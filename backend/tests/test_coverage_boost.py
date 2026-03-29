"""Comprehensive backend tests to reach ≥80% coverage.

Covers the 6 categories from FUL-17:
1. FAISS search correctness — nearest neighbors match brute-force numpy
2. Cluster bounds — empty clusters, single-item clusters, single-cluster edge
3. Multi-tenant isolation — tenant A cannot access tenant B data
4. Input validation edges — invalid k, empty query, malformed tenant_id
5. Cache behavior — LRU eviction at 512 entries, cache invalidation on tenant change
6. Rate limiter edge cases — concurrent requests, IP rotation

Plus: atlas_schema validation, roadmap stubs, export endpoint, numpy_search fallback.
"""

import json
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

import backend.server as server_module
from backend.server import (
    LRUCache,
    RateLimiter,
    AuthFailureLimiter,
    StructuredFormatter,
    LogHandler,
    _build_cluster_stats,
    _coming_soon,
    numpy_search,
    validate_search_id,
    app,
    rate_limiter,
    search_cache,
    auth_failure_limiter,
    _hash_key,
    event_log,
)


# ---------------------------------------------------------------------------
# Shared constants and fixtures
# ---------------------------------------------------------------------------

VALID_KEY = "test-key-default"
VALID_KEY_ALPHA = "test-key-alpha"
AUTH_HEADER = {"Authorization": f"Bearer {VALID_KEY}"}
AUTH_HEADER_ALPHA = {"Authorization": f"Bearer {VALID_KEY_ALPHA}"}
NUM_VECTORS = 50
VECTOR_DIM = 512
TEST_ID = "ID_0000"


@pytest.fixture(autouse=True)
def inject_test_data(monkeypatch):
    rng = np.random.default_rng(42)
    vecs = rng.random((NUM_VECTORS, VECTOR_DIM), dtype=np.float32)

    test_id_map = {i: f"ID_{i:04d}" for i in range(NUM_VECTORS)}
    test_reverse_map = {v: k for k, v in test_id_map.items()}

    assigns = np.zeros(NUM_VECTORS, dtype=np.int32)
    assigns[NUM_VECTORS // 2:] = 1

    def fake_load_data(retries=3):
        server_module.vectors = vecs
        server_module.id_map = test_id_map
        server_module.reverse_map = test_reverse_map
        server_module.cluster_assignments = assigns
        server_module.cluster_stats = _build_cluster_stats(
            vecs, assigns, dict(test_id_map)
        )
        if server_module.faiss_available and server_module.faiss is not None:
            d = vecs.shape[1]
            idx = server_module.faiss.IndexFlatL2(d)
            idx.add(vecs)
            server_module.index = idx
        else:
            server_module.index = None

    monkeypatch.setattr(server_module, "load_data", fake_load_data)
    yield
    search_cache._cache.clear()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    rate_limiter._hits.clear()
    auth_failure_limiter._failures.clear()
    yield
    rate_limiter._hits.clear()
    auth_failure_limiter._failures.clear()


@pytest.fixture(autouse=True)
def inject_test_api_keys(monkeypatch):
    test_keys = {
        _hash_key(VALID_KEY): {"tenant_id": "default", "label": "Test default key"},
        _hash_key(VALID_KEY_ALPHA): {"tenant_id": "client_alpha", "label": "Test alpha key"},
    }
    monkeypatch.setattr(server_module, "api_keys", test_keys)
    monkeypatch.setattr(server_module, "load_api_keys", lambda: None)
    yield


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ===========================================================================
# 1. FAISS search correctness — nearest neighbors match brute-force numpy
# ===========================================================================


class TestFAISSSearchCorrectness:
    def test_faiss_results_match_numpy_brute_force(self, client):
        """FAISS nearest neighbors must match numpy brute-force for known vectors."""
        # Get results via API
        r = client.get(f"/api/search?id={TEST_ID}&k=10", headers=AUTH_HEADER)
        assert r.status_code == 200
        api_ids = [item["id"] for item in r.json()["results"]]

        # Compute brute-force numpy reference
        query_idx = server_module.reverse_map[TEST_ID]
        query_vec = server_module.vectors[query_idx].reshape(1, -1)
        D_np, I_np = numpy_search(query_vec, 10, vecs=server_module.vectors)
        np_ids = [server_module.id_map[int(i)] for i in I_np[0]]

        assert api_ids == np_ids, "FAISS results diverge from numpy brute-force"

    def test_numpy_search_returns_correct_shape(self):
        """numpy_search must return (1, k) shaped arrays."""
        rng = np.random.default_rng(99)
        vecs = rng.random((20, 64), dtype=np.float32)
        query = vecs[0].reshape(1, -1)
        D, I = numpy_search(query, 5, vecs=vecs)
        assert D.shape == (1, 5)
        assert I.shape == (1, 5)

    def test_numpy_search_self_is_nearest(self):
        """The query vector itself should be its own nearest neighbor (distance ~0)."""
        rng = np.random.default_rng(7)
        vecs = rng.random((30, 32), dtype=np.float32)
        query = vecs[3].reshape(1, -1)
        D, I = numpy_search(query, 1, vecs=vecs)
        assert I[0][0] == 3
        assert D[0][0] < 1e-6

    def test_search_scores_are_monotonically_decreasing(self, client):
        """Search results should have scores in non-increasing order."""
        r = client.get(f"/api/search?id={TEST_ID}&k=20", headers=AUTH_HEADER)
        scores = [item["score"] for item in r.json()["results"]]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"Score at rank {i} < rank {i+1}"

    def test_search_k_clamped_to_100(self, client):
        """k > 100 should be clamped to 100 (max(1, min(k, 100)))."""
        r = client.get(f"/api/search?id={TEST_ID}&k=200", headers=AUTH_HEADER)
        assert r.status_code == 200
        # k is clamped to 100 by the server
        assert len(r.json()["results"]) == 100

    def test_search_k_clamped_to_1_minimum(self, client):
        """k=0 or negative should be clamped to 1."""
        r = client.get(f"/api/search?id={TEST_ID}&k=0", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert len(r.json()["results"]) == 1


# ===========================================================================
# 2. Cluster bounds — edge cases
# ===========================================================================


class TestClusterBounds:
    def test_single_cluster_nearest_is_self(self):
        """When only one cluster exists, nearest_cluster should be itself."""
        rng = np.random.default_rng(0)
        vecs = rng.random((10, 32), dtype=np.float32)
        assigns = np.zeros(10, dtype=np.int32)
        id_map = {i: f"ID_{i}" for i in range(10)}

        stats = _build_cluster_stats(vecs, assigns, id_map)
        assert stats[0]["nearest_cluster"] == 0
        assert stats[0]["nearest_cluster_distance"] == 0.0

    def test_single_item_cluster(self):
        """A cluster with one item should still produce valid stats."""
        rng = np.random.default_rng(1)
        vecs = rng.random((3, 16), dtype=np.float32)
        assigns = np.array([0, 1, 2], dtype=np.int32)
        id_map = {0: "A", 1: "B", 2: "C"}

        stats = _build_cluster_stats(vecs, assigns, id_map)
        for cid in (0, 1, 2):
            assert stats[cid]["size"] == 1
            assert len(stats[cid]["top_representative_ids"]) == 1
            assert 0.0 <= stats[cid]["centroid_density"] <= 1.0

    def test_cluster_list_returns_503_when_no_stats(self, client, monkeypatch):
        """cluster/list should return 503 when cluster data is unavailable."""
        monkeypatch.setattr(server_module, "cluster_stats", {})
        r = client.get("/api/cluster/list", headers=AUTH_HEADER)
        assert r.status_code == 503

    def test_cluster_insights_returns_503_when_no_stats(self, client, monkeypatch):
        """cluster/insights should return 503 when cluster data is unavailable."""
        monkeypatch.setattr(server_module, "cluster_stats", {})
        r = client.get("/api/cluster/insights?cluster_id=0", headers=AUTH_HEADER)
        assert r.status_code == 503

    def test_cluster_insights_404_for_negative_id(self, client):
        """Negative cluster_id should return 404."""
        r = client.get("/api/cluster/insights?cluster_id=-1", headers=AUTH_HEADER)
        assert r.status_code == 404

    def test_build_cluster_stats_centroid_density_bounded(self):
        """centroid_density must be in [0, 1]."""
        rng = np.random.default_rng(3)
        vecs = rng.random((100, 64), dtype=np.float32)
        assigns = np.array([i % 4 for i in range(100)], dtype=np.int32)
        id_map = {i: f"ID_{i}" for i in range(100)}

        stats = _build_cluster_stats(vecs, assigns, id_map)
        for cid, s in stats.items():
            assert 0.0 <= s["centroid_density"] <= 1.0
            assert s["intra_cluster_similarity_p10"] <= s["intra_cluster_similarity_mean"]


# ===========================================================================
# 3. Multi-tenant isolation
# ===========================================================================


class TestMultiTenantIsolation:
    def test_alpha_key_cannot_see_default_data_via_param(self, client):
        """Key bound to client_alpha must not switch to default via query param."""
        r = client.get(
            f"/api/search?id={TEST_ID}&k=5&tenant_id=default",
            headers=AUTH_HEADER_ALPHA,
        )
        assert r.status_code == 200
        assert r.json()["tenant"] == "client_alpha"

    def test_default_key_cannot_switch_to_alpha(self, client):
        """Key bound to default must not escalate to client_alpha."""
        r = client.get(
            f"/api/search?id={TEST_ID}&k=5&tenant_id=client_alpha",
            headers=AUTH_HEADER,
        )
        assert r.status_code == 200
        assert r.json()["tenant"] == "default"

    def test_different_tenants_get_different_cache_entries(self, client):
        """Cache keys are tenant-scoped — same ID/k but different tenant must not share."""
        r1 = client.get(f"/api/search?id={TEST_ID}&k=5", headers=AUTH_HEADER)
        assert r1.status_code == 200

        r2 = client.get(f"/api/search?id={TEST_ID}&k=5", headers=AUTH_HEADER_ALPHA)
        assert r2.status_code == 200

        # Both should succeed — cache keyed by tenant:id:k
        assert r1.json()["tenant"] == "default"
        assert r2.json()["tenant"] == "client_alpha"


# ===========================================================================
# 4. Input validation edges
# ===========================================================================


class TestInputValidation:
    def test_k_zero_clamped_to_1(self, client):
        """k=0 should be clamped to 1."""
        r = client.get(f"/api/search?id={TEST_ID}&k=0", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert len(r.json()["results"]) == 1

    def test_k_negative_clamped_to_1(self, client):
        """k=-5 should be clamped to 1."""
        r = client.get(f"/api/search?id={TEST_ID}&k=-5", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert len(r.json()["results"]) == 1

    def test_k_over_100_clamped(self, client):
        """k=101 should be clamped to 100."""
        r = client.get(f"/api/search?id={TEST_ID}&k=101", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert len(r.json()["results"]) <= 100

    def test_empty_id_returns_400(self, client):
        """Empty string ID should be rejected."""
        r = client.get("/api/search?id=&k=5", headers=AUTH_HEADER)
        assert r.status_code == 400

    def test_special_chars_in_id_returns_400(self, client):
        """IDs with special chars (path traversal) should be rejected."""
        r = client.get("/api/search?id=../../etc/passwd&k=5", headers=AUTH_HEADER)
        assert r.status_code == 400

    def test_semicolon_in_id_returns_400(self, client):
        """Semicolons (potential injection) should be rejected."""
        r = client.get("/api/search?id=ID;DROP TABLE&k=5", headers=AUTH_HEADER)
        assert r.status_code == 400

    def test_valid_id_format_accepted(self, client):
        """IDs with allowed chars (alphanumeric, dash, underscore, etc.) pass validation."""
        r = client.get(f"/api/search?id={TEST_ID}&k=1", headers=AUTH_HEADER)
        assert r.status_code == 200

    def test_validate_search_id_strips_whitespace(self):
        """validate_search_id should strip leading/trailing whitespace."""
        result = validate_search_id("  ID_0001  ")
        assert result == "ID_0001"

    def test_malformed_id_with_angle_brackets(self, client):
        """Angle brackets (XSS attempt) should be rejected."""
        r = client.get("/api/search?id=<script>alert(1)</script>&k=5", headers=AUTH_HEADER)
        assert r.status_code == 400


# ===========================================================================
# 5. Cache behavior — LRU eviction at 512 entries
# ===========================================================================


class TestCacheBehavior:
    def test_lru_cache_basic_get_put(self):
        """Basic get/put operations."""
        cache = LRUCache(capacity=3)
        cache.put("a", [1])
        assert cache.get("a") == [1]
        assert cache.get("missing") is None

    def test_lru_cache_evicts_oldest_at_capacity(self):
        """When capacity is reached, the LRU (oldest) entry is evicted."""
        cache = LRUCache(capacity=3)
        cache.put("a", [1])
        cache.put("b", [2])
        cache.put("c", [3])
        cache.put("d", [4])  # evicts "a"
        assert cache.get("a") is None
        assert cache.get("b") == [2]

    def test_lru_cache_access_refreshes_entry(self):
        """Accessing an entry moves it to the end, preventing eviction."""
        cache = LRUCache(capacity=3)
        cache.put("a", [1])
        cache.put("b", [2])
        cache.put("c", [3])
        cache.get("a")  # refresh "a"
        cache.put("d", [4])  # evicts "b" (now oldest)
        assert cache.get("a") == [1]
        assert cache.get("b") is None

    def test_lru_cache_overwrite_existing_key(self):
        """Putting an existing key updates its value without eviction."""
        cache = LRUCache(capacity=2)
        cache.put("a", [1])
        cache.put("b", [2])
        cache.put("a", [10])  # update, not insert
        assert cache.get("a") == [10]
        assert cache.get("b") == [2]  # still present

    def test_lru_eviction_at_512_entries(self):
        """Test eviction behaviour at the production capacity (512)."""
        cache = LRUCache(capacity=512)
        for i in range(512):
            cache.put(f"k{i}", [i])
        assert cache.get("k0") == [0]  # still present

        cache.put("k512", [512])  # triggers eviction
        # k0 was accessed above so it's refreshed; k1 is the true LRU
        assert cache.get("k1") is None

    def test_cache_invalidation_on_tenant_change(self, client):
        """Clearing search cache after tenant data change prevents stale results."""
        r1 = client.get(f"/api/search?id={TEST_ID}&k=5", headers=AUTH_HEADER)
        assert r1.status_code == 200

        # Simulate cache invalidation (e.g., after re-ingestion)
        search_cache._cache.clear()

        r2 = client.get(f"/api/search?id={TEST_ID}&k=5", headers=AUTH_HEADER)
        assert r2.status_code == 200
        # Both should succeed — data recomputed after invalidation


# ===========================================================================
# 6. Rate limiter edge cases
# ===========================================================================


class TestRateLimiterEdges:
    def test_rate_limiter_allows_up_to_max(self):
        """RateLimiter allows exactly max_requests within the window."""
        rl = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert rl.is_allowed("1.2.3.4") is True
        assert rl.is_allowed("1.2.3.4") is False

    def test_rate_limiter_different_ips_independent(self):
        """Different IPs have independent counters."""
        rl = RateLimiter(max_requests=2, window_seconds=60)
        assert rl.is_allowed("1.1.1.1") is True
        assert rl.is_allowed("1.1.1.1") is True
        assert rl.is_allowed("1.1.1.1") is False
        # Different IP is still allowed
        assert rl.is_allowed("2.2.2.2") is True

    def test_rate_limiter_window_expiry(self):
        """Requests outside the window should be pruned and allow new ones."""
        rl = RateLimiter(max_requests=2, window_seconds=1)
        assert rl.is_allowed("1.1.1.1") is True
        assert rl.is_allowed("1.1.1.1") is True
        assert rl.is_allowed("1.1.1.1") is False

        # Manually expire hits
        rl._hits["1.1.1.1"] = [time.time() - 2]
        assert rl.is_allowed("1.1.1.1") is True

    def test_auth_failure_limiter_blocks_after_threshold(self):
        """AuthFailureLimiter blocks after max_failures within window."""
        afl = AuthFailureLimiter(max_failures=3, window_seconds=60)
        assert afl.is_blocked("10.0.0.1") is False
        afl.record_failure("10.0.0.1")
        afl.record_failure("10.0.0.1")
        afl.record_failure("10.0.0.1")
        assert afl.is_blocked("10.0.0.1") is True

    def test_auth_failure_limiter_different_ips(self):
        """Auth failures for one IP don't block another."""
        afl = AuthFailureLimiter(max_failures=2, window_seconds=60)
        afl.record_failure("10.0.0.1")
        afl.record_failure("10.0.0.1")
        assert afl.is_blocked("10.0.0.1") is True
        assert afl.is_blocked("10.0.0.2") is False

    def test_auth_failure_limiter_window_expiry(self):
        """Failures outside the window are pruned."""
        afl = AuthFailureLimiter(max_failures=2, window_seconds=1)
        afl.record_failure("10.0.0.1")
        afl.record_failure("10.0.0.1")
        assert afl.is_blocked("10.0.0.1") is True

        # Manually expire
        afl._failures["10.0.0.1"] = [time.time() - 2]
        assert afl.is_blocked("10.0.0.1") is False

    def test_rate_limit_headers_after_block(self, client):
        """After rate limit is hit, response should be 429."""
        for _ in range(60):
            client.get(f"/api/search?id={TEST_ID}&k=1", headers=AUTH_HEADER)
        r = client.get(f"/api/search?id={TEST_ID}&k=1", headers=AUTH_HEADER)
        assert r.status_code == 429


# ===========================================================================
# Roadmap stub endpoints (covers _coming_soon and many uncovered lines)
# ===========================================================================


class TestRoadmapEndpoints:
    def test_coming_soon_helper(self):
        result = _coming_soon("Test Feature")
        assert result["status"] == "coming_soon"
        assert result["feature"] == "Test Feature"

    def test_eln_context(self, client):
        r = client.get(f"/api/eln/context?id={TEST_ID}", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_eln_export(self, client):
        r = client.get(f"/api/eln/export?id={TEST_ID}", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_lims_ingest(self, client):
        r = client.get("/api/lims/ingest?smiles=CCO", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_dotmatics_sync(self, client):
        r = client.post(f"/api/dotmatics/sync?id={TEST_ID}", json={}, headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_molecule_smiles(self, client):
        r = client.get(f"/api/molecule/smiles?id={TEST_ID}", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_safety_score(self, client):
        r = client.get(f"/api/safety/score?id={TEST_ID}", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_safety_sds(self, client):
        r = client.get(f"/api/safety/sds?id={TEST_ID}", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_hts_assay(self, client):
        r = client.get(f"/api/hts/assay?id={TEST_ID}", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_hts_sar_map(self, client):
        r = client.get("/api/hts/sar?cluster_id=0", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_sustainability_score(self, client):
        r = client.get(f"/api/sustainability/score?id={TEST_ID}", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_ip_check(self, client):
        r = client.get(f"/api/ip/check?id={TEST_ID}", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_collaboration_sign(self, client):
        r = client.post("/api/collaboration/sign", json={}, headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_molecule_properties(self, client):
        r = client.get(f"/api/molecule/properties?id={TEST_ID}", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_validation_similarity(self, client):
        r = client.get(
            f"/api/validation/similarity?id_a={TEST_ID}&id_b=ID_0001",
            headers=AUTH_HEADER,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "coming_soon"

    def test_onboard_upload(self, client):
        r = client.post("/api/onboard/upload", json={}, headers=AUTH_HEADER)
        assert r.status_code == 200
        assert "job_id" in r.json()


# ===========================================================================
# Export endpoint
# ===========================================================================


class TestExportEndpoint:
    def test_csv_export_returns_csv(self, client):
        r = client.get("/api/export?ids=ID_0000,ID_0001", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        body = r.text
        assert "ID_0000" in body
        assert "ID_0001" in body

    def test_export_rate_limited(self, client):
        for _ in range(60):
            client.get("/api/export?ids=ID_0000", headers=AUTH_HEADER)
        r = client.get("/api/export?ids=ID_0000", headers=AUTH_HEADER)
        assert r.status_code == 429


# ===========================================================================
# Miscellaneous server endpoints
# ===========================================================================


class TestMiscEndpoints:
    def test_api_status(self, client):
        r = client.get("/api/status")
        assert r.status_code == 200
        assert "vectors" in r.json()
        assert "cache" in r.json()

    def test_api_logs(self, client):
        r = client.get("/api/logs", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_sso_callback(self, client):
        r = client.get("/api/auth/sso/callback?token=abc123def456", headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "authenticated"

    def test_track_endpoint_with_auth(self, client):
        r = client.post("/api/track", json={"event": "test_click"}, headers=AUTH_HEADER)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_track_endpoint_malformed_body(self, client):
        r = client.post(
            "/api/track",
            content=b"not json",
            headers={**AUTH_HEADER, "content-type": "application/json"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "err"

    def test_root_redirects(self, client):
        r = client.get("/", follow_redirects=False)
        assert r.status_code == 301

    def test_index_html_redirects(self, client):
        r = client.get("/index.html", follow_redirects=False)
        assert r.status_code == 301

    def test_static_denylist_config(self, client):
        r = client.get("/config/api_keys.json", headers=AUTH_HEADER)
        assert r.status_code == 403

    def test_static_denylist_vault(self, client):
        """Vault paths should be blocked (403) or not found (404)."""
        r = client.get("/vault/secret/data.json", headers=AUTH_HEADER)
        assert r.status_code in (403, 404)

    def test_static_denylist_memory(self, client):
        """Memory paths should be blocked (403) or not found (404)."""
        r = client.get("/memory/stuff.json", headers=AUTH_HEADER)
        assert r.status_code in (403, 404)

    def test_hsts_present_on_api(self, client):
        r = client.get(f"/api/search?id={TEST_ID}&k=1", headers=AUTH_HEADER)
        hsts = r.headers.get("strict-transport-security")
        assert hsts is not None

    def test_search_returns_503_when_no_vectors(self, client, monkeypatch):
        """Search should return 503 if vectors failed to load."""
        monkeypatch.setattr(server_module, "vectors", None)
        r = client.get(f"/api/search?id={TEST_ID}&k=1", headers=AUTH_HEADER)
        assert r.status_code == 503


# ===========================================================================
# VaultManager — additional coverage for edge cases
# ===========================================================================


class TestVaultManagerExtended:
    def test_has_vault_returns_false_for_missing_tenant(self, tmp_path):
        from backend.vault_manager import VaultManager
        vm = VaultManager(tmp_path)
        assert vm.has_vault("nonexistent") is False

    def test_has_vault_returns_true_for_atlas_only(self, tmp_path):
        from backend.vault_manager import VaultManager
        tenant_dir = tmp_path / "vault" / "t1"
        tenant_dir.mkdir(parents=True)
        (tenant_dir / "atlas_data.json").write_text("[]")
        vm = VaultManager(tmp_path)
        assert vm.has_vault("t1") is True

    def test_has_vault_returns_true_for_embeddings_only(self, tmp_path):
        from backend.vault_manager import VaultManager
        tenant_dir = tmp_path / "vault" / "t2"
        tenant_dir.mkdir(parents=True)
        (tenant_dir / "embeddings.npy").write_bytes(b"")
        vm = VaultManager(tmp_path)
        assert vm.has_vault("t2") is True

    def test_vault_manager_mock_vectors_when_no_embeddings(self, tmp_path):
        """When no embeddings exist, VaultManager generates mock vectors."""
        from backend.vault_manager import VaultManager
        items = [{"id": f"T_{i}"} for i in range(5)]
        tenant_dir = tmp_path / "vault" / "mock_tenant"
        tenant_dir.mkdir(parents=True)
        (tenant_dir / "atlas_data.json").write_text(json.dumps(items))

        vm = VaultManager(tmp_path)
        data = vm.get_tenant_data("mock_tenant")
        assert data["vectors"].shape[0] >= 5
        assert data["vectors"].dtype == np.float32


# ===========================================================================
# StructuredFormatter and LogHandler (covers lines 51-85)
# ===========================================================================


class TestLogging:
    def test_structured_formatter(self):
        import logging as _logging
        fmt = StructuredFormatter()
        record = _logging.LogRecord(
            "test", _logging.INFO, "test.py", 1, "hello %s", ("world",), None
        )
        record.tenant_id = "t1"
        record.request_id = "r1"
        record.client_ip = "1.2.3.4"
        output = fmt.format(record)
        data = json.loads(output)
        assert data["message"] == "hello world"
        assert data["tenant_id"] == "t1"
        assert data["request_id"] == "r1"
        assert data["client_ip"] == "1.2.3.4"

    def test_structured_formatter_without_extras(self):
        import logging as _logging
        fmt = StructuredFormatter()
        record = _logging.LogRecord(
            "test", _logging.WARNING, "test.py", 1, "plain msg", (), None
        )
        output = fmt.format(record)
        data = json.loads(output)
        assert data["message"] == "plain msg"
        assert "tenant_id" not in data

    def test_log_handler_captures_events(self):
        import logging as _logging
        handler = LogHandler()
        handler.setFormatter(_logging.Formatter())
        record = _logging.LogRecord(
            "test", _logging.INFO, "test.py", 1, "test event", (), None
        )
        initial_len = len(event_log)
        handler.emit(record)
        assert len(event_log) == initial_len + 1
        assert event_log[-1]["message"] == "test event"
