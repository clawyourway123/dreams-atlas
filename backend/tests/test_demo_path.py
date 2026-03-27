"""E2E smoke test for the DreaMS Atlas demo path.

Verifies the exact flow a buyer will see:
1. Server starts and 3D visualization loads (GET / → 200 with non-empty HTML)
2. Search returns results with correct schema (id, similarity score, rank)
3. Similarity scores are plausible (0.0–1.0, top result > 0.9)
4. CSV export works (GET /api/export → valid CSV with headers)
5. Rate limiter is active (61 rapid requests → 429 on request 61)

Run with: pytest backend/tests/test_demo_path.py -v
"""

import csv
import io

import numpy as np
import pytest

import backend.server as server_module
from backend.server import app, rate_limiter, search_cache
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NUM_VECTORS = 50
VECTOR_DIM = 512
TEST_ID = "ID_0000"
TEST_ID_1 = "ID_0001"
VALID_KEY = "demo-smoke-key"
AUTH_HEADER = {"Authorization": f"Bearer {VALID_KEY}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def inject_test_data(monkeypatch):
    """Inject deterministic test vectors so no production files are needed."""
    rng = np.random.default_rng(0)
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
    monkeypatch.setattr(server_module, "load_api_keys", lambda: None)
    monkeypatch.setattr(
        server_module,
        "api_keys",
        {VALID_KEY: {"tenant_id": "default", "label": "Demo smoke key"}},
    )
    yield

    search_cache._cache.clear()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    rate_limiter._hits.clear()
    yield
    rate_limiter._hits.clear()


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# 1. Server starts and 3D visualization loads
# ---------------------------------------------------------------------------


def test_homepage_returns_200_with_html(client):
    """GET / must return 200 and serve non-empty HTML content."""
    response = client.get("/", headers=AUTH_HEADER)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    body = response.text
    assert len(body) > 0, "Response body must not be empty"
    assert "<html" in body.lower() or "<!doctype" in body.lower(), (
        "Response must contain HTML markup"
    )


# ---------------------------------------------------------------------------
# 2 & 3. Search returns results with correct schema and plausible scores
# ---------------------------------------------------------------------------


def test_search_returns_20_results_with_required_fields(client):
    """GET /api/search?id=ID_0000&k=20 must return exactly 20 results
    each containing 'id', 'score' (similarity), and 'rank' fields."""
    response = client.get(f"/api/search?id={TEST_ID}&k=20", headers=AUTH_HEADER)
    assert response.status_code == 200, f"Search failed: {response.status_code}"

    body = response.json()
    results = body["results"]
    assert len(results) == 20, f"Expected 20 results, got {len(results)}"

    for item in results:
        assert "id" in item, f"Result missing 'id' field: {item}"
        assert "score" in item, f"Result missing 'score' (similarity) field: {item}"
        assert "rank" in item, f"Result missing 'rank' (metadata) field: {item}"


def test_similarity_scores_are_plausible(client):
    """All similarity scores must be between 0.0 and 1.0.
    The top result (self-match) must have similarity > 0.9."""
    response = client.get(f"/api/search?id={TEST_ID}&k=20", headers=AUTH_HEADER)
    assert response.status_code == 200

    results = response.json()["results"]
    for item in results:
        score = item["score"]
        assert 0.0 <= score <= 1.0, (
            f"Score {score} out of range [0.0, 1.0] for id={item['id']}"
        )

    top_score = results[0]["score"]
    assert top_score > 0.9, (
        f"Top result similarity {top_score} must be > 0.9 (self-match expected)"
    )


# ---------------------------------------------------------------------------
# 4. CSV export works
# ---------------------------------------------------------------------------


def test_csv_export_returns_valid_csv_with_headers(client):
    """GET /api/export?ids=ID_0000,ID_0001 must return valid CSV with a header row."""
    response = client.get(
        f"/api/export?ids={TEST_ID},{TEST_ID_1}", headers=AUTH_HEADER
    )
    assert response.status_code == 200, f"Export failed: {response.status_code}"

    content_type = response.headers.get("content-type", "")
    assert "text/csv" in content_type, (
        f"Expected text/csv content-type, got {content_type}"
    )

    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) >= 1, "CSV must have at least a header row"

    headers = rows[0]
    assert len(headers) >= 1, "CSV header row must have at least one column"
    assert "id" in [h.lower() for h in headers], (
        f"CSV must have an 'id' column; got headers: {headers}"
    )

    # The two requested IDs must appear in the data rows
    data_ids = [row[0] for row in rows[1:] if row]
    assert TEST_ID in data_ids, f"{TEST_ID} not found in export rows"
    assert TEST_ID_1 in data_ids, f"{TEST_ID_1} not found in export rows"


# ---------------------------------------------------------------------------
# 5. Rate limiter is active
# ---------------------------------------------------------------------------


def test_rate_limiter_returns_429_on_61st_request(client):
    """60 rapid requests must succeed; the 61st must be rate-limited (429)."""
    for i in range(60):
        r = client.get(f"/api/search?id={TEST_ID}&k=1", headers=AUTH_HEADER)
        assert r.status_code == 200, (
            f"Request {i + 1} failed before limit with {r.status_code}"
        )

    r = client.get(f"/api/search?id={TEST_ID}&k=1", headers=AUTH_HEADER)
    assert r.status_code == 429, (
        f"Expected 429 on request 61, got {r.status_code}"
    )
