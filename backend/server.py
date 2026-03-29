"""DreaMS Atlas — FastAPI backend with FAISS similarity search.

Phase 6/12 hardening: rate limiting, input validation, request logging,
LRU caching, graceful degradation, and GZip.

v2.2 — 2026-02-12: Added Phase 12 hardening (GZip, Logs API, Resilience).
v2.3 — 2026-03-28: Security hardening (CORS, hashed auth, HSTS, path traversal,
                    auth rate limiting, structured audit logging).
v2.4 — 2026-03-28: API completeness (versioning, rate limit headers, predict,
                    export formats, track validation, modality filter).
"""

import csv
import hashlib
import hmac
import io
import json
import logging
import logging.handlers
import math
import os
import re
import time
import uuid
from collections import deque, OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

from backend.vault_manager import VaultManager

# ---------------------------------------------------------------------------
# Logging & Event Tracking (structured JSON)
# ---------------------------------------------------------------------------


class StructuredFormatter(logging.Formatter):
    """Emit log records as single-line JSON with audit fields."""

    def format(self, record):
        entry = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        for field in ("tenant_id", "request_id", "client_ip"):
            val = getattr(record, field, None)
            if val is not None:
                entry[field] = val
        return json.dumps(entry)


_handler = logging.StreamHandler()
_handler.setFormatter(StructuredFormatter())
logging.basicConfig(level=logging.INFO, handlers=[_handler])
logger = logging.getLogger("dreams-atlas")

# Keep last 100 log messages in memory for /api/logs
event_log = deque(maxlen=100)


class LogHandler(logging.Handler):
    def emit(self, record):
        try:
            self.format(record)
            event_log.append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(record.created)),
                "level": record.levelname,
                "message": record.getMessage()
            })
        except Exception:
            pass


logger.addHandler(LogHandler())

# Resolve the project root (one level up from backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Vault manager — per-tenant data path resolution and index caching
vault_manager = VaultManager(PROJECT_ROOT)

# ---------------------------------------------------------------------------
# API Key Auth (SHA-256 hashed keys with timing-safe comparison)
# ---------------------------------------------------------------------------
# Maps sha256_hex(key) -> {"tenant_id": str, "label": str}
# Populated at startup from config/api_keys.json.
# If the file is absent, auth is disabled (warn-only) so local dev still works.
api_keys: dict[str, dict] = {}

# Paths that bypass authentication entirely.
SKIP_AUTH_PATHS: frozenset[str] = frozenset({"/healthz", "/api/status"})

# Mutation endpoints that ALWAYS require auth when keys are loaded.
AUTH_REQUIRED_PATHS: frozenset[str] = frozenset({
    "/api/search",
    "/api/track",
    "/api/predict",
    "/api/onboard/upload",
    "/api/dotmatics/sync",
    "/api/collaboration/sign",
})

# Same set but under the /v1 prefix — built dynamically.
AUTH_REQUIRED_V1_PATHS: frozenset[str] = frozenset(
    f"/v1{p}" for p in AUTH_REQUIRED_PATHS
)


def _hash_key(raw_key: str) -> str:
    """Return the SHA-256 hex digest of a raw API key."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def load_api_keys() -> None:
    global api_keys
    keys_path = PROJECT_ROOT / "config" / "api_keys.json"
    if not keys_path.exists():
        logger.warning("config/api_keys.json not found — API authentication disabled")
        api_keys = {}
        return
    with open(keys_path) as f:
        data = json.load(f)
    api_keys = data.get("keys", {})
    logger.info(f"Loaded {len(api_keys)} API key(s) from config/api_keys.json")


# ---------------------------------------------------------------------------
# FAISS / Search Backend
# ---------------------------------------------------------------------------
index = None
vectors = None
id_map: dict[int, str] = {}
reverse_map: dict[str, int] = {}
faiss_available = False

# Atlas metadata — populated at startup from atlas_data.json
atlas_metadata: list[dict] = []

# Cluster analysis — populated once at startup in load_data()
cluster_assignments: np.ndarray | None = None  # shape (n,), dtype int
cluster_stats: dict[int, dict] = {}  # cluster_id -> stats dict

try:
    import faiss
    faiss_available = True
except Exception:
    faiss = None  # type: ignore[assignment]
    logger.warning("faiss-cpu not available — search will use numpy fallback")

# ---------------------------------------------------------------------------
# ML Model for /api/predict (optional — graceful if missing)
# ---------------------------------------------------------------------------
predict_model = None
predict_label_encoder = None
predict_available = False

try:
    import joblib
    _joblib_available = True
except ImportError:
    joblib = None  # type: ignore[assignment]
    _joblib_available = False
    logger.warning("joblib not available — /api/predict will be disabled")


def load_predict_model() -> None:
    global predict_model, predict_label_encoder, predict_available
    if not _joblib_available:
        return
    model_path = PROJECT_ROOT / "model_output" / "rf_ir_raman_production.joblib"
    encoder_path = PROJECT_ROOT / "model_output" / "label_encoder.joblib"
    if not model_path.exists() or not encoder_path.exists():
        logger.warning("Prediction model files not found — /api/predict disabled")
        return
    try:
        predict_model = joblib.load(model_path)
        predict_label_encoder = joblib.load(encoder_path)
        predict_available = True
        logger.info(
            f"Prediction model loaded: {len(predict_label_encoder.classes_)} classes"
        )
    except Exception as e:
        logger.error(f"Failed to load prediction model: {e}")


# ---------------------------------------------------------------------------
# LRU Cache for search results
# ---------------------------------------------------------------------------
class LRUCache:
    """Simple thread-safe-ish LRU cache (fine for single-worker uvicorn)."""

    def __init__(self, capacity: int = 256):
        self._cache: OrderedDict[str, list] = OrderedDict()
        self._capacity = capacity

    def get(self, key: str):
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: str, value: list):
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._capacity:
                self._cache.popitem(last=False)
        self._cache[key] = value


search_cache = LRUCache(capacity=512)


# ---------------------------------------------------------------------------
# Rate Limiter (in-memory, per-IP) — enhanced with remaining/reset tracking
# ---------------------------------------------------------------------------
class RateLimiter:
    """Sliding-window rate limiter per IP address with header support."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = {}

    def check(self, ip: str) -> tuple[bool, int, int]:
        """Check rate limit and return (allowed, remaining, reset_epoch).

        *reset_epoch* is the Unix timestamp when the oldest hit in the current
        window expires (i.e., when one slot frees up).
        """
        now = time.time()
        cutoff = now - self.window
        hits = [t for t in self._hits.get(ip, []) if t > cutoff]

        if len(hits) >= self.max_requests:
            self._hits[ip] = hits
            reset_at = int(math.ceil(hits[0] + self.window))
            return False, 0, reset_at

        hits.append(now)
        self._hits[ip] = hits
        remaining = self.max_requests - len(hits)
        reset_at = int(math.ceil(hits[0] + self.window)) if hits else int(now + self.window)
        return True, remaining, reset_at

    def is_allowed(self, ip: str) -> bool:
        allowed, _, _ = self.check(ip)
        return allowed


# Global rate limiter: 60 req/min for general API endpoints
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)

# Tighter rate limiter for /api/track: 10 req/min per IP
track_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


# ---------------------------------------------------------------------------
# Auth Failure Rate Limiter (per IP, 5 failures / 5-min window)
# ---------------------------------------------------------------------------
class AuthFailureLimiter:
    """Tracks authentication failures per IP to throttle brute-force attempts."""

    def __init__(self, max_failures: int = 5, window_seconds: int = 300):
        self.max_failures = max_failures
        self.window = window_seconds
        self._failures: dict[str, list[float]] = {}

    def record_failure(self, ip: str) -> None:
        now = time.time()
        hits = self._failures.get(ip, [])
        hits.append(now)
        self._failures[ip] = hits

    def is_blocked(self, ip: str) -> bool:
        now = time.time()
        cutoff = now - self.window
        hits = self._failures.get(ip, [])
        hits = [t for t in hits if t > cutoff]
        self._failures[ip] = hits
        return len(hits) >= self.max_failures


auth_failure_limiter = AuthFailureLimiter(max_failures=5, window_seconds=300)


# ---------------------------------------------------------------------------
# Pydantic models for request validation
# ---------------------------------------------------------------------------
class TrackEvent(BaseModel):
    event: str = Field(..., max_length=64)
    meta: Optional[dict] = Field(default=None)


class PredictRequest(BaseModel):
    spectrum: list[float] = Field(..., min_length=1, max_length=10000)


# ---------------------------------------------------------------------------
# Cluster statistics (computed once at startup, no extra dependencies)
# ---------------------------------------------------------------------------

def _build_cluster_stats(
    vecs: np.ndarray,
    assignments: np.ndarray,
    local_id_map: dict,
) -> dict:
    """Compute per-cluster statistics from embedding vectors.

    Returns a dict keyed by cluster_id containing pre-computed stats so
    the API endpoints can serve responses in O(1) without holding the GIL.
    """
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    unit_vecs = (vecs / norms).astype("float32")

    cluster_ids = sorted(set(int(c) for c in assignments))

    # Pass 1 — centroids and centroid density
    centroids: dict[int, np.ndarray] = {}
    densities: dict[int, float] = {}
    for cid in cluster_ids:
        members = unit_vecs[assignments == cid]
        raw = members.mean(axis=0)
        raw_norm = float(np.linalg.norm(raw))
        densities[cid] = round(min(raw_norm, 1.0), 4)
        centroids[cid] = raw / raw_norm if raw_norm > 0 else raw

    # Pass 2 — per-member similarity stats and representative IDs
    stats: dict[int, dict] = {}
    for cid in cluster_ids:
        mask = assignments == cid
        member_indices = np.where(mask)[0]
        members = unit_vecs[mask]
        sims = (members @ centroids[cid]).astype("float64")

        top_k = min(3, len(member_indices))
        top_local = np.argsort(-sims)[:top_k]
        top_ids = [local_id_map[int(member_indices[i])] for i in top_local]

        stats[cid] = {
            "size": int(mask.sum()),
            "centroid_density": densities[cid],
            "intra_cluster_similarity_mean": round(float(sims.mean()), 4),
            "intra_cluster_similarity_p10": round(float(np.percentile(sims, 10)), 4),
            "top_representative_ids": top_ids,
            "_centroid": centroids[cid],
        }

    # Pass 3 — nearest cluster (centroid-to-centroid L2)
    if len(cluster_ids) > 1:
        centroid_matrix = np.stack([centroids[cid] for cid in cluster_ids])
        for i, cid in enumerate(cluster_ids):
            dists = np.linalg.norm(centroid_matrix - centroids[cid], axis=1)
            dists[i] = np.inf
            nearest_idx = int(np.argmin(dists))
            stats[cid]["nearest_cluster"] = cluster_ids[nearest_idx]
            stats[cid]["nearest_cluster_distance"] = round(float(dists[nearest_idx]), 4)
    else:
        cid = cluster_ids[0]
        stats[cid]["nearest_cluster"] = cid
        stats[cid]["nearest_cluster_distance"] = 0.0

    return stats


# ---------------------------------------------------------------------------
# Roadmap stub helper
# ---------------------------------------------------------------------------
def _coming_soon(feature: str) -> dict:
    return {
        "status": "coming_soon",
        "feature": feature,
        "eta": "Q3 2026",
        "contact": "hello@gstack.ai",
    }


# ---------------------------------------------------------------------------
# Input Validation
# ---------------------------------------------------------------------------
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_\-.:, +()'\[\]]{1,256}$")


def validate_search_id(raw: str) -> str:
    """Sanitise and validate a search ID parameter."""
    raw = raw.strip()
    if not _SAFE_ID_RE.match(raw):
        raise HTTPException(
            status_code=400,
            detail="Invalid ID format.",
        )
    return raw


# ---------------------------------------------------------------------------
# Numpy fallback for similarity search (no FAISS)
# ---------------------------------------------------------------------------
def numpy_search(
    query_vec: np.ndarray,
    k: int,
    vecs: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Brute-force L2 search using numpy — fallback when faiss is unavailable.

    *vecs* defaults to the module-level ``vectors`` when not supplied so callers
    using the global default index require no change.
    """
    arr = vecs if vecs is not None else vectors
    diffs = arr - query_vec
    dists = np.sum(diffs ** 2, axis=1)
    top_k = np.argpartition(dists, k)[:k]
    top_k_sorted = top_k[np.argsort(dists[top_k])]
    return dists[top_k_sorted].reshape(1, -1), top_k_sorted.reshape(1, -1)


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
def load_data(retries=3):
    global index, vectors, cluster_assignments, cluster_stats, atlas_metadata

    for attempt in range(retries):
        logger.info(f"Loading data (attempt {attempt + 1}/{retries})...")
        try:
            embeddings_path = PROJECT_ROOT / "embeddings_checkpoint.npy"
            atlas_path = PROJECT_ROOT / "atlas_data.json"

            id_map.clear()
            reverse_map.clear()

            atlas_json = None
            n_items = 1000
            if atlas_path.exists():
                with open(atlas_path, "r") as f:
                    atlas_json = json.load(f)
                for i, item in enumerate(atlas_json):
                    str_id = item.get("id", f"ID_{i}")
                    id_map[i] = str_id
                    reverse_map[str_id] = i
                n_items = len(atlas_json)
                atlas_metadata = atlas_json
                logger.info(f"Loaded {len(id_map)} ID mappings")

            if embeddings_path.exists():
                vectors = np.load(str(embeddings_path)).astype("float32")
                logger.info(f"Loaded {vectors.shape[0]} vectors")
            else:
                logger.warning("Generating mock vectors")
                np.random.seed(42)
                vectors = np.random.rand(n_items, 512).astype("float32")

            if not id_map:
                for i in range(vectors.shape[0]):
                    id_map[i] = f"ID_{i}"
                    reverse_map[f"ID_{i}"] = i

            if faiss_available and faiss is not None:
                try:
                    d = vectors.shape[1]
                    index = faiss.IndexFlatL2(d)
                    index.add(vectors)
                    logger.info(f"FAISS index built: {index.ntotal}")
                except Exception as faiss_err:
                    index = None
                    logger.warning(f"FAISS index build failed ({faiss_err}) — using numpy fallback")
            if index is None:
                logger.info("Using numpy search")

            # Build cluster stats if atlas_data provided cluster labels
            if atlas_json is not None:
                raw_assigns = [item.get("cluster", 0) for item in atlas_json]
                if len(raw_assigns) == vectors.shape[0]:
                    cluster_assignments = np.array(raw_assigns, dtype=np.int32)
                    cluster_stats = _build_cluster_stats(
                        vectors, cluster_assignments, dict(id_map)
                    )
                    logger.info(
                        f"Cluster stats built: {len(cluster_stats)} clusters"
                    )

            return

        except Exception as e:
            logger.error(f"Load error: {e}")
            if attempt < retries - 1:
                time.sleep(1)

# ---------------------------------------------------------------------------
# App Lifecycle
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_api_keys()
    load_data()
    load_predict_model()
    yield


app = FastAPI(title="DreaMS Atlas", lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=1000)

_allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ---------------------------------------------------------------------------
# Middleware: Logging, Cache, Version Header & Rate Limit Headers
# ---------------------------------------------------------------------------


@app.middleware("http")
async def process_request(request: Request, call_next):
    start = time.time()
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    request.state.request_id = request_id

    response = await call_next(request)
    elapsed = (time.time() - start) * 1000
    path = request.url.path

    # API version header on all versioned and API responses
    if path.startswith("/v1/") or path.startswith("/api/"):
        response.headers["X-API-Version"] = "1"

    # HSTS header on all responses
    response.headers["Strict-Transport-Security"] = (
        "max-age=63072000; includeSubDomains"
    )

    # Rate limit headers — populated by endpoint handlers via request.state
    rl_limit = getattr(request.state, "ratelimit_limit", None)
    if rl_limit is not None:
        response.headers["X-RateLimit-Limit"] = str(rl_limit)
        response.headers["X-RateLimit-Remaining"] = str(
            getattr(request.state, "ratelimit_remaining", 0)
        )
        response.headers["X-RateLimit-Reset"] = str(
            getattr(request.state, "ratelimit_reset", 0)
        )

    if any(path.endswith(ext) for ext in [".js", ".css", ".png", ".jpg", ".json"]):
        max_age = 3600 if path.endswith(".json") else 86400
        response.headers["Cache-Control"] = f"public, max-age={max_age}"

    if path.startswith("/api/") or path.startswith("/v1/api/") or path in ("/healthz", "/search"):
        client_ip = request.client.host if request.client else "unknown"
        tenant_id = getattr(request.state, "tenant_id", None)
        logger.info(
            f"{request.method} {path} -> {response.status_code} ({elapsed:.1f}ms)",
            extra={
                "request_id": request_id,
                "client_ip": client_ip,
                "tenant_id": tenant_id,
            },
        )

    return response


def _is_auth_required_path(path: str) -> bool:
    """Check if a path requires auth, handling both /api/ and /v1/api/ prefixes."""
    return path in AUTH_REQUIRED_PATHS or path in AUTH_REQUIRED_V1_PATHS


# Added after process_request so Starlette registers it as the outermost
# wrapper — meaning it runs first on every inbound request.
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    path = request.url.path

    # Health check is always public.
    if path in SKIP_AUTH_PATHS:
        return await call_next(request)

    # Auth is disabled when no keys are configured (e.g. local dev without config).
    # But mutation endpoints still require auth when keys ARE configured.
    if not api_keys:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"

    # Check if this IP is blocked due to too many auth failures.
    if auth_failure_limiter.is_blocked(client_ip):
        return JSONResponse(
            {"detail": "Too many authentication failures"},
            status_code=429,
        )

    # Extract key from Authorization header (Bearer) or ?api_key= query param.
    key: str | None = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        key = auth_header[7:]
    if not key:
        key = request.query_params.get("api_key") or None

    if key is None:
        # Mutation endpoints always require auth.
        if _is_auth_required_path(path) or path.startswith("/api/onboard/") or path.startswith("/v1/api/onboard/"):
            return JSONResponse({"detail": "Missing API key"}, status_code=401)
        return await call_next(request)

    # Hash incoming key and do timing-safe comparison against stored hashes.
    incoming_hash = _hash_key(key)
    meta = None
    for stored_hash, stored_meta in api_keys.items():
        if hmac.compare_digest(incoming_hash, stored_hash):
            meta = stored_meta
            break

    if meta is None:
        auth_failure_limiter.record_failure(client_ip)
        logger.warning(
            f"AUTH: rejected invalid key for {request.method} {path}",
            extra={"client_ip": client_ip},
        )
        return JSONResponse({"detail": "Invalid API key"}, status_code=401)

    # Bind the key's tenant to the request so downstream handlers use it.
    request.state.tenant_id = meta.get("tenant_id", "default")
    return await call_next(request)


# ---------------------------------------------------------------------------
# Helper: apply rate limit check and store headers on request.state
# ---------------------------------------------------------------------------
def _apply_rate_limit(request: Request, limiter: RateLimiter) -> None:
    """Check rate limit for request IP. Raises 429 if exceeded.
    Stores limit/remaining/reset on request.state for header middleware.
    """
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining, reset_at = limiter.check(client_ip)
    request.state.ratelimit_limit = limiter.max_requests
    request.state.ratelimit_remaining = remaining
    request.state.ratelimit_reset = reset_at
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


# ---------------------------------------------------------------------------
# API Router — all /api/* endpoints live here, mounted at both
# /api (unversioned alias) and /v1/api (versioned canonical).
# ---------------------------------------------------------------------------
api_router = APIRouter()


@api_router.get("/status")
def api_status():
    return {"status": "ok", "vectors": len(id_map), "cache": len(search_cache._cache)}


@api_router.get("/logs")
def get_logs():
    return list(event_log)


@api_router.get("/search")
def api_search(
    request: Request,
    id: str,
    k: int = 20,
    tenant_id: str = "default",
    modality: Optional[str] = Query(
        default=None,
        description="Filter by spectral modality (IR, FTIR, Raman). "
        "Requires modality metadata in atlas data.",
    ),
):
    _apply_rate_limit(request, rate_limiter)

    clean_id = validate_search_id(id)
    k = max(1, min(k, 100))

    # Key-bound tenant takes precedence over the query param so callers
    # cannot escalate to another tenant by changing ?tenant_id=.
    effective_tenant = getattr(request.state, "tenant_id", tenant_id)

    logger.info(f"SEARCH [Tenant: {effective_tenant}] | ID: {clean_id} | k: {k} | modality: {modality}")

    cache_key = f"{effective_tenant}:{clean_id}:{k}:{modality or 'all'}"
    cached = search_cache.get(cache_key)
    if cached:
        return {"query": clean_id, "tenant": effective_tenant, "results": cached}

    # Route to tenant-specific index when vault files exist; otherwise use the
    # module-level defaults (preserves single-tenant / dev behaviour unchanged).
    if effective_tenant != "default" and vault_manager.has_vault(effective_tenant):
        t_data = vault_manager.get_tenant_data(effective_tenant)
        t_vectors = t_data["vectors"]
        t_id_map = t_data["id_map"]
        t_reverse_map = t_data["reverse_map"]
        t_index = t_data["index"]
    else:
        t_vectors = vectors
        t_id_map = id_map
        t_reverse_map = reverse_map
        t_index = index

    query_idx = t_reverse_map.get(clean_id, -1)
    if query_idx == -1:
        raise HTTPException(status_code=404)
    if t_vectors is None:
        raise HTTPException(status_code=503)

    # Over-fetch when modality filter is active so we can filter down to k.
    fetch_k = k * 3 if modality else k

    query_vec = t_vectors[query_idx].reshape(1, -1)
    if t_index:
        D, indices = t_index.search(query_vec, min(fetch_k, t_vectors.shape[0]))
    else:
        D, indices = numpy_search(query_vec, min(fetch_k, t_vectors.shape[0]), vecs=t_vectors)

    results = []
    for rank_idx, idx in enumerate(indices[0]):
        int_idx = int(idx)
        result_id = t_id_map.get(int_idx)
        dist = float(D[0][rank_idx])

        # Apply modality filter if requested and metadata is available
        if modality and atlas_metadata:
            item_meta = atlas_metadata[int_idx] if int_idx < len(atlas_metadata) else {}
            item_modality = item_meta.get("modality")
            if item_modality and item_modality.upper() != modality.upper():
                continue

        results.append({
            "id": result_id,
            "score": round(1.0 / (1.0 + dist), 6),
            "rank": len(results),
        })
        if len(results) >= k:
            break

    search_cache.put(cache_key, results)
    return {"query": clean_id, "tenant": effective_tenant, "results": results}


@api_router.get("/auth/sso/callback")
def sso_callback(token: str):
    """Mock SAML/SSO callback for enterprise authentication."""
    logger.info(f"SSO: Authenticated user with token {token[:10]}...")
    return {
        "status": "authenticated",
        "user": "enterprise_user@client.com",
        "tenant_id": "client_alpha",
        "role": "admin",
        "expires_in": 3600
    }


@api_router.get("/export")
def api_export(
    request: Request,
    ids: Optional[str] = Query(default=None, description="Comma-separated compound IDs"),
    query: Optional[str] = Query(default=None, description="Search query ID — runs search then exports results"),
    k: int = Query(default=20, ge=1, le=100, description="Number of results when using query param"),
    format: str = Query(default="csv", regex="^(csv|json)$", description="Export format: csv or json"),
):
    """Export compound data as CSV or JSON.

    Provide either `ids` (comma-separated) or `query` (search ID) — not both.
    """
    _apply_rate_limit(request, rate_limiter)

    if ids and query:
        raise HTTPException(status_code=400, detail="Provide either 'ids' or 'query', not both")
    if not ids and not query:
        raise HTTPException(status_code=400, detail="Provide 'ids' or 'query' parameter")

    # Build the result list
    export_rows: list[dict] = []

    if query:
        # Search-then-export: run similarity search and export results
        clean_id = validate_search_id(query)
        effective_tenant = getattr(request.state, "tenant_id", "default")

        if effective_tenant != "default" and vault_manager.has_vault(effective_tenant):
            t_data = vault_manager.get_tenant_data(effective_tenant)
            t_vectors = t_data["vectors"]
            t_id_map = t_data["id_map"]
            t_reverse_map = t_data["reverse_map"]
            t_index = t_data["index"]
        else:
            t_vectors = vectors
            t_id_map = id_map
            t_reverse_map = reverse_map
            t_index = index

        query_idx = t_reverse_map.get(clean_id, -1)
        if query_idx == -1:
            raise HTTPException(status_code=404, detail=f"Query ID not found: {clean_id}")
        if t_vectors is None:
            raise HTTPException(status_code=503)

        query_vec = t_vectors[query_idx].reshape(1, -1)
        if t_index:
            D, indices_arr = t_index.search(query_vec, k)
        else:
            D, indices_arr = numpy_search(query_vec, k, vecs=t_vectors)

        for rank, idx in enumerate(indices_arr[0]):
            dist = float(D[0][rank])
            export_rows.append({
                "id": t_id_map.get(int(idx), f"ID_{idx}"),
                "rank": rank,
                "score": round(1.0 / (1.0 + dist), 6),
            })
    else:
        # Direct ID export
        id_list = [i.strip() for i in ids.split(",") if i.strip()]
        for rank, compound_id in enumerate(id_list):
            clean_id = validate_search_id(compound_id)
            export_rows.append({"id": clean_id, "rank": rank})

    # Format response
    if format == "json":
        return JSONResponse(
            content={"results": export_rows},
            headers={"Content-Disposition": "attachment; filename=export.json"},
        )

    # CSV format
    output = io.StringIO()
    if export_rows:
        writer = csv.DictWriter(output, fieldnames=list(export_rows[0].keys()))
        writer.writeheader()
        writer.writerows(export_rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"},
    )


@api_router.post("/track")
async def api_track(request: Request):
    """Track analytics events with rate limiting and schema validation."""
    _apply_rate_limit(request, track_rate_limiter)

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Validate with Pydantic
    try:
        event = TrackEvent(**data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {e}")

    # Enforce meta size limit (1KB serialized)
    if event.meta is not None:
        meta_size = len(json.dumps(event.meta))
        if meta_size > 1024:
            raise HTTPException(
                status_code=422,
                detail=f"meta field exceeds 1KB limit ({meta_size} bytes)",
            )

    logger.info(f"TRACK: {event.event} | {event.meta}")
    return {"status": "ok"}


@api_router.post("/predict")
async def api_predict(request: Request, body: PredictRequest):
    """Run spectrum classification. Returns predicted class, confidence, and top-3 probabilities.

    Requires authentication.
    """
    if not predict_available:
        raise HTTPException(
            status_code=503,
            detail="Prediction model not available. Ensure model files are present in model_output/.",
        )

    spectrum = np.array(body.spectrum, dtype=np.float64).reshape(1, -1)

    try:
        probabilities = predict_model.predict_proba(spectrum)[0]
        predicted_idx = int(np.argmax(probabilities))
        predicted_class = predict_label_encoder.inverse_transform([predicted_idx])[0]
        confidence = float(probabilities[predicted_idx])

        # Top-3 predictions
        top3_indices = np.argsort(-probabilities)[:3]
        top3 = [
            {
                "class": str(predict_label_encoder.inverse_transform([int(i)])[0]),
                "probability": round(float(probabilities[int(i)]), 6),
            }
            for i in top3_indices
        ]
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")

    return {
        "predicted_class": str(predicted_class),
        "confidence": round(confidence, 6),
        "top_3": top3,
    }


# ---------------------------------------------------------------------------
# Phase 16: Interoperability logic
# ---------------------------------------------------------------------------


@api_router.get("/eln/context")
def eln_context(id: str, experiment_type: str = "similarity_review"):
    """ELN context injection — roadmap feature."""
    validate_search_id(id)
    return _coming_soon("ELN Context Injection")


@api_router.get("/eln/export")
def eln_export(id: str, format: str = "benchling"):
    """ELN export — roadmap feature."""
    validate_search_id(id)
    return _coming_soon("ELN Export (Benchling, etc.)")

# ---------------------------------------------------------------------------
# Phase 16.5: LIMS Ingestion
# ---------------------------------------------------------------------------


@api_router.get("/lims/ingest")
def lims_ingest(smiles: str):
    """LIMS ingestion — roadmap feature."""
    return _coming_soon("LIMS SMILES-to-Spectrum Ingestion")


@api_router.post("/dotmatics/sync")
def dotmatics_sync(id: str, payload: dict = None):
    """Dotmatics integration — roadmap feature."""
    validate_search_id(id)
    return _coming_soon("Dotmatics Sync Integration")


@api_router.get("/molecule/smiles")
def get_smiles(id: str):
    """SMILES lookup — roadmap feature."""
    validate_search_id(id)
    return _coming_soon("Molecule SMILES Lookup")

# ---------------------------------------------------------------------------
# Phase 20: Predictive ADMET & Safety Intelligence
# ---------------------------------------------------------------------------


@api_router.get("/safety/score")
def safety_score(id: str):
    """ADMET and safety scoring — roadmap feature."""
    validate_search_id(id)
    return _coming_soon("Predictive ADMET & Safety Scoring")


@api_router.get("/safety/sds")
def safety_sds(id: str):
    """Safety Data Sheet generation — roadmap feature."""
    validate_search_id(id)
    return _coming_soon("Safety Data Sheet Generation")

# ---------------------------------------------------------------------------
# Phase 21: High-Throughput Screening (HTS) & Assay Data Fusion
# ---------------------------------------------------------------------------


@api_router.get("/hts/assay")
def hts_assay(id: str):
    """HTS assay data fusion — roadmap feature."""
    validate_search_id(id)
    return _coming_soon("High-Throughput Screening Assay Data")


@api_router.get("/hts/sar")
def hts_sar_map(cluster_id: int = 0):
    """SAR heatmap — roadmap feature."""
    return _coming_soon("Structure-Activity Relationship Map")

# ---------------------------------------------------------------------------
# Phase 22: Sustainable Chemistry & Green Synthesis Score
# ---------------------------------------------------------------------------


@api_router.get("/sustainability/score")
def sustainability_score(id: str):
    """Green chemistry scoring — roadmap feature."""
    validate_search_id(id)
    return _coming_soon("Sustainable Chemistry & Green Synthesis Score")

# ---------------------------------------------------------------------------
# Phase 23: Global R&D Collaboration & IP Management
# ---------------------------------------------------------------------------


@api_router.get("/ip/check")
def ip_check(id: str):
    """IP/Patent FTO check — roadmap feature."""
    validate_search_id(id)
    return _coming_soon("IP & Freedom-to-Operate Check")


@api_router.post("/collaboration/sign")
async def collaboration_sign(request: Request):
    """E-signature for experimental sign-off — roadmap feature."""
    return _coming_soon("Collaborative E-Signature")

# ---------------------------------------------------------------------------
# Phase 25: Real-World Data Integration & Property Mapping
# ---------------------------------------------------------------------------


@api_router.get("/molecule/properties")
def get_molecule_properties(id: str):
    """Molecule property overlays — roadmap feature."""
    validate_search_id(id)
    return _coming_soon("Real-World Molecule Property Mapping")


@api_router.post("/onboard/upload")
async def onboard_upload(request: Request):
    """Mock Customer Onboarding: Upload .mgf for private Atlas creation."""
    # In a real app, we'd process the file and generate embeddings
    logger.info("ONBOARD: Received proprietary .mgf file upload.")
    return {
        "status": "success",
        "job_id": f"JOB-{int(time.time())}",
        "message": "Spectra received. DreaMS transformer embedding generation started.",
        "estimated_completion": "5 minutes"
    }


@api_router.get("/validation/similarity")
def validation_similarity(id_a: str, id_b: str):
    """Cross-validation against experimental data — roadmap feature."""
    validate_search_id(id_a)
    validate_search_id(id_b)
    return _coming_soon("DreaMS vs. Experimental Similarity Validation")

# ---------------------------------------------------------------------------
# Cluster Analysis (real, computed at startup from existing embeddings)
# ---------------------------------------------------------------------------


@api_router.get("/cluster/list")
def cluster_list():
    """Return all clusters with their sizes."""
    if not cluster_stats:
        raise HTTPException(status_code=503, detail="Cluster data not available")
    return {
        "clusters": [
            {"cluster_id": cid, "size": stats["size"]}
            for cid, stats in sorted(cluster_stats.items())
        ]
    }


@api_router.get("/cluster/insights")
def cluster_insights(cluster_id: int):
    """Return detailed analysis for a single cluster."""
    if not cluster_stats:
        raise HTTPException(status_code=503, detail="Cluster data not available")
    stats = cluster_stats.get(cluster_id)
    if stats is None:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    return {
        "cluster_id": cluster_id,
        "size": stats["size"],
        "centroid_density": stats["centroid_density"],
        "intra_cluster_similarity_mean": stats["intra_cluster_similarity_mean"],
        "intra_cluster_similarity_p10": stats["intra_cluster_similarity_p10"],
        "nearest_cluster": stats["nearest_cluster"],
        "nearest_cluster_distance": stats["nearest_cluster_distance"],
        "top_representative_ids": stats["top_representative_ids"],
    }


# ---------------------------------------------------------------------------
# Mount API router at both /api (unversioned alias) and /v1/api (canonical)
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/v1/api")


# ---------------------------------------------------------------------------
# Non-API routes (healthz, static files, root redirect)
# ---------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"status": "alive", "vectors": len(id_map), "faiss": index is not None}


# ---------------------------------------------------------------------------
# Static Files & Root Redirect
# ---------------------------------------------------------------------------

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://dreams-atlas.onrender.com")


@app.get("/")
async def redirect_root():
    return RedirectResponse(url=FRONTEND_URL, status_code=301)


@app.get("/index.html")
async def redirect_index_html():
    return RedirectResponse(url=FRONTEND_URL, status_code=301)


_STATIC_DENYLIST: frozenset[str] = frozenset({
    "config", "vault", "memory", "backend", ".git", ".env",
})


@app.get("/{path:path}")
async def serve_static(path: str):
    try:
        file_path = (PROJECT_ROOT / path).resolve(strict=True)
    except (OSError, ValueError):
        raise HTTPException(status_code=404)
    if not str(file_path).startswith(str(PROJECT_ROOT)):
        raise HTTPException(status_code=403)
    # Block sensitive server-side directories from being served as static files.
    top_dir = Path(path).parts[0] if Path(path).parts else ""
    if top_dir in _STATIC_DENYLIST:
        raise HTTPException(status_code=403)
    if file_path.is_file():
        return FileResponse(str(file_path))
    raise HTTPException(status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
