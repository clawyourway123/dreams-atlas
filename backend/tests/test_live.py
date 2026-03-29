"""Live smoke tests for the deployed Dreams Atlas demo.

These tests run against a real deployed URL and are SKIPPED by default
so they never block CI. Run them manually before sales calls:

    DEMO_URL=https://dreams-atlas.onrender.com pytest backend/tests/test_live.py -v

Set DEMO_URL to any running instance (local or remote).
"""

import os

import pytest
import requests

DEMO_URL = os.environ.get("DEMO_URL", "").rstrip("/")

# Skip the entire module if DEMO_URL is not set
pytestmark = pytest.mark.skipif(
    not DEMO_URL,
    reason="Set DEMO_URL env var to run live smoke tests (e.g. DEMO_URL=https://dreams-atlas.onrender.com)",
)


def _get(path: str, **kwargs) -> requests.Response:
    url = f"{DEMO_URL}{path}"
    return requests.get(url, timeout=90, **kwargs)


# ---------------------------------------------------------------------------
# 1. Health check
# ---------------------------------------------------------------------------

def test_healthz_returns_200():
    r = _get("/healthz")
    assert r.status_code == 200, f"/healthz returned {r.status_code}"


def test_healthz_body():
    r = _get("/healthz")
    body = r.json()
    assert body.get("status") == "alive"
    assert body.get("faiss") is True, "FAISS index not loaded"
    assert isinstance(body.get("vectors"), int) and body["vectors"] > 0, "No vectors loaded"


# ---------------------------------------------------------------------------
# 2. API status
# ---------------------------------------------------------------------------

def test_api_status():
    r = _get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"


# ---------------------------------------------------------------------------
# 3. Homepage loads
# ---------------------------------------------------------------------------

def test_homepage_loads():
    r = _get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# 4. Henkel demo page loads
# ---------------------------------------------------------------------------

def test_henkel_demo_page():
    r = _get("/examples/branded-demos/henkel_demo.html")
    assert r.status_code == 200, f"Henkel demo page returned {r.status_code}"
    assert "text/html" in r.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# 5. Search returns results
# ---------------------------------------------------------------------------

def test_search_returns_results():
    r = _get("/api/search", params={"id": "Henkel-001", "k": 5})
    # 200 expected; 401 means no API key needed check
    assert r.status_code in (200, 401), f"Unexpected status {r.status_code}"
    if r.status_code == 200:
        body = r.json()
        assert isinstance(body, (list, dict)), "Search did not return JSON"


# ---------------------------------------------------------------------------
# 6. CSV export endpoint reachable
# ---------------------------------------------------------------------------

def test_export_endpoint_reachable():
    r = _get("/api/export", params={"ids": "Henkel-001,Henkel-002"})
    # 200 = CSV returned; 401 = auth required (still reachable); 429 = rate limit (site alive)
    assert r.status_code in (200, 401, 429), f"Unexpected status {r.status_code}"
    if r.status_code == 200:
        assert "text/csv" in r.headers.get("content-type", "") or len(r.content) > 0
