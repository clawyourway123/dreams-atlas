"""Pytest test suite for the DreaMS Atlas FastAPI backend.

Tests cover:
1. GET /healthz returns 200 with expected shape
2. GET /api/search returns k results with correct schema
3. Rate limiter returns 429 after 60 requests from the same IP
4. Cache: second identical search is served from cache
5. Index (FAISS or numpy) loaded at startup — vectors must be non-empty
6. Invalid ?id= returns 404 with error detail
7. API key auth: 401 for missing/invalid key, pass with valid key
8. /healthz is excluded from auth check
9. Key-bound tenant_id overrides query param
"""

import numpy as np
import pytest

import backend.server as server_module
from backend.server import app, rate_limiter, search_cache
from fastapi.testclient import TestClient

# Demo key that matches the fixture injected by inject_test_api_keys
VALID_KEY = "test-key-default"
VALID_KEY_ALPHA = "test-key-alpha"
AUTH_HEADER = {"Authorization": f"Bearer {VALID_KEY}"}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NUM_VECTORS = 50
VECTOR_DIM = 512
TEST_ID = "ID_0000"


@pytest.fixture(autouse=True)
def inject_test_data(monkeypatch):
    """Populate module-level globals with deterministic test data.

    We replace load_data() so the lifespan hook injects known test vectors
    instead of reading production files (atlas_data.json / embeddings_checkpoint.npy).
    """
    rng = np.random.default_rng(42)
    vecs = rng.random((NUM_VECTORS, VECTOR_DIM), dtype=np.float32)

    test_id_map = {i: f"ID_{i:04d}" for i in range(NUM_VECTORS)}
    test_reverse_map = {v: k for k, v in test_id_map.items()}

    def fake_load_data(retries=3):
        server_module.vectors = vecs
        server_module.id_map = test_id_map
        server_module.reverse_map = test_reverse_map
        if server_module.faiss_available and server_module.faiss is not None:
            d = vecs.shape[1]
            idx = server_module.faiss.IndexFlatL2(d)
            idx.add(vecs)
            server_module.index = idx
        else:
            server_module.index = None  # numpy fallback

    monkeypatch.setattr(server_module, "load_data", fake_load_data)

    yield

    # Clear caches between tests so state doesn't bleed
    search_cache._cache.clear()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear the in-process rate limiter between tests."""
    rate_limiter._hits.clear()
    yield
    rate_limiter._hits.clear()


@pytest.fixture(autouse=True)
def inject_test_api_keys(monkeypatch):
    """Inject deterministic test API keys so auth tests don't depend on the
    real config/api_keys.json file.

    load_api_keys is stubbed out as a no-op so the TestClient lifespan cannot
    overwrite the test keys when it runs at startup.
    """
    test_keys = {
        VALID_KEY: {"tenant_id": "default", "label": "Test default key"},
        VALID_KEY_ALPHA: {"tenant_id": "client_alpha", "label": "Test alpha key"},
    }
    monkeypatch.setattr(server_module, "api_keys", test_keys)
    monkeypatch.setattr(server_module, "load_api_keys", lambda: None)
    yield


@pytest.fixture
def client():
    # Disable the lifespan (data already injected by inject_test_data)
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# 1. Health check
# ---------------------------------------------------------------------------

def test_healthz_returns_200(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "alive"
    assert isinstance(body["vectors"], int)
    assert body["vectors"] > 0
    assert "faiss" in body


# ---------------------------------------------------------------------------
# 2. Search returns correct number of results with correct schema
# ---------------------------------------------------------------------------

def test_search_returns_k_results(client):
    response = client.get(f"/api/search?id={TEST_ID}&k=20", headers=AUTH_HEADER)
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == TEST_ID
    results = body["results"]
    assert len(results) == 20
    for item in results:
        assert "id" in item, "result missing 'id' field"
        assert "score" in item, "result missing 'score' field"
        assert "rank" in item, "result missing 'rank' field"
        assert isinstance(item["score"], float)
        assert 0.0 <= item["score"] <= 1.0


def test_search_respects_k_parameter(client):
    for k in (1, 5, 10):
        response = client.get(f"/api/search?id={TEST_ID}&k={k}", headers=AUTH_HEADER)
        assert response.status_code == 200
        assert len(response.json()["results"]) == k


# ---------------------------------------------------------------------------
# 3. Rate limiter returns 429 after 60 requests from the same IP
# ---------------------------------------------------------------------------

def test_rate_limiter_blocks_after_60_requests(client):
    # 60 requests should all succeed
    for _ in range(60):
        r = client.get(f"/api/search?id={TEST_ID}&k=1", headers=AUTH_HEADER)
        assert r.status_code == 200, f"Expected 200 before limit, got {r.status_code}"

    # The 61st request from the same IP must be rate-limited
    r = client.get(f"/api/search?id={TEST_ID}&k=1", headers=AUTH_HEADER)
    assert r.status_code == 429, (
        f"Expected 429 after 60 requests, got {r.status_code}"
    )


# ---------------------------------------------------------------------------
# 4. Cache: second identical search is served from LRU cache
# ---------------------------------------------------------------------------

def test_cache_serves_second_request(monkeypatch, client):
    """The second search with the same parameters must hit the cache.

    We spy on LRUCache.put to count how many times a new result is stored.
    If caching works, the result is stored only on the first call; the second
    call returns the cached value without calling put again.
    """
    put_calls = []
    original_put = search_cache.put

    def spy_put(key, value):
        put_calls.append(key)
        original_put(key, value)

    monkeypatch.setattr(search_cache, "put", spy_put)

    r1 = client.get(f"/api/search?id={TEST_ID}&k=20", headers=AUTH_HEADER)
    assert r1.status_code == 200
    assert len(put_calls) == 1, "First request should populate the cache"

    r2 = client.get(f"/api/search?id={TEST_ID}&k=20", headers=AUTH_HEADER)
    assert r2.status_code == 200
    assert len(put_calls) == 1, "Second identical request must not call cache.put again"

    # Both responses must be identical
    assert r1.json()["results"] == r2.json()["results"]


# ---------------------------------------------------------------------------
# 5. Index loaded at startup — vectors must be present and non-empty
# ---------------------------------------------------------------------------

def test_index_loaded_at_startup():
    """Verify that some vector index is operational at startup.

    In CI the numpy fallback is used (faiss-cpu is not installed).
    Production deployments should have FAISS installed; add faiss-cpu to
    requirements.txt and the healthz endpoint will report faiss=true.
    """
    assert server_module.vectors is not None, "vectors not loaded"
    assert server_module.vectors.shape[0] > 0, "vectors array is empty"
    assert len(server_module.id_map) > 0, "id_map not populated"
    assert len(server_module.reverse_map) > 0, "reverse_map not populated"


@pytest.mark.skipif(
    not server_module.faiss_available,
    reason="faiss-cpu not installed — add it to requirements.txt for this check",
)
def test_faiss_index_used_when_available(client):
    """When faiss-cpu is installed the FAISS index must be non-None."""
    assert server_module.index is not None, (
        "FAISS is available but index was not built — check load_data()"
    )
    response = client.get("/healthz")
    assert response.json()["faiss"] is True


# ---------------------------------------------------------------------------
# 6. Invalid ?id= returns 404 with an error message
# ---------------------------------------------------------------------------

def test_invalid_id_returns_404(client):
    response = client.get("/api/search?id=DOES_NOT_EXIST_XYZ&k=5", headers=AUTH_HEADER)
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body, "404 response must include a 'detail' field"


def test_malformed_id_returns_400(client):
    # Characters outside the safe regex should be rejected
    response = client.get("/api/search?id=../../../etc/passwd&k=5", headers=AUTH_HEADER)
    assert response.status_code == 400
    body = response.json()
    assert "detail" in body


# ---------------------------------------------------------------------------
# 7. API key authentication
# ---------------------------------------------------------------------------

def test_missing_key_returns_401(client):
    response = client.get(f"/api/search?id={TEST_ID}&k=1")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_invalid_key_returns_401(client):
    response = client.get(
        f"/api/search?id={TEST_ID}&k=1",
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert response.status_code == 401


def test_valid_key_in_header_returns_200(client):
    response = client.get(
        f"/api/search?id={TEST_ID}&k=5",
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200


def test_valid_key_as_query_param_returns_200(client):
    response = client.get(f"/api/search?id={TEST_ID}&k=5&api_key={VALID_KEY}")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 8. /healthz is excluded from auth
# ---------------------------------------------------------------------------

def test_healthz_no_auth_required(client):
    """Health endpoint must respond 200 with no API key."""
    response = client.get("/healthz")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 9. Key-bound tenant_id overrides query param
# ---------------------------------------------------------------------------

def test_key_tenant_overrides_query_param(client):
    """API key for 'default' tenant must not let caller switch to another tenant
    by supplying ?tenant_id=client_alpha."""
    response = client.get(
        f"/api/search?id={TEST_ID}&k=5&tenant_id=client_alpha",
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200
    # The response tenant must reflect the key's tenant, not the query param.
    assert response.json()["tenant"] == "default"


def test_alpha_key_sets_correct_tenant(client):
    """An enterprise key bound to 'client_alpha' must scope results to that tenant."""
    response = client.get(
        f"/api/search?id={TEST_ID}&k=5",
        headers={"Authorization": f"Bearer {VALID_KEY_ALPHA}"},
    )
    assert response.status_code == 200
    assert response.json()["tenant"] == "client_alpha"
