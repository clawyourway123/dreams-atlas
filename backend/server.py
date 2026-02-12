"""DreaMS Atlas — FastAPI backend with FAISS similarity search.

Phase 6 hardening: rate limiting, input validation, request logging,
LRU caching, and graceful degradation.
"""

import json
import logging
import os
import re
import time
from collections import OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("dreams-atlas")

# Resolve the project root (one level up from backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# FAISS / Search Backend
# ---------------------------------------------------------------------------
index = None
vectors = None
id_map: dict[int, str] = {}
reverse_map: dict[str, int] = {}
faiss_available = True

try:
    import faiss
except ImportError:
    faiss = None  # type: ignore[assignment]
    faiss_available = False
    logger.warning("faiss-cpu not available — search will use numpy fallback")


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
# Rate Limiter (in-memory, per-IP)
# ---------------------------------------------------------------------------
class RateLimiter:
    """Sliding-window rate limiter per IP address."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = {}

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        cutoff = now - self.window
        hits = self._hits.get(ip, [])
        # Prune old entries
        hits = [t for t in hits if t > cutoff]
        if len(hits) >= self.max_requests:
            self._hits[ip] = hits
            return False
        hits.append(now)
        self._hits[ip] = hits
        return True

    def cleanup(self):
        """Remove stale IPs (call occasionally)."""
        now = time.time()
        cutoff = now - self.window * 2
        stale = [ip for ip, hits in self._hits.items() if not hits or hits[-1] < cutoff]
        for ip in stale:
            del self._hits[ip]


rate_limiter = RateLimiter(max_requests=30, window_seconds=60)


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
            detail="Invalid ID format. Must be 1-128 alphanumeric/dash/underscore characters.",
        )
    return raw


# ---------------------------------------------------------------------------
# Numpy fallback for similarity search (no FAISS)
# ---------------------------------------------------------------------------
def numpy_search(query_vec: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Brute-force L2 search using numpy — fallback when faiss is unavailable."""
    diffs = vectors - query_vec  # type: ignore[operator]
    dists = np.sum(diffs ** 2, axis=1)
    top_k = np.argpartition(dists, k)[:k]
    top_k_sorted = top_k[np.argsort(dists[top_k])]
    return dists[top_k_sorted].reshape(1, -1), top_k_sorted.reshape(1, -1)


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
def load_data():
    global index, vectors, id_map, reverse_map

    logger.info("Loading embeddings...")
    try:
        embeddings_path = PROJECT_ROOT / "embeddings_checkpoint.npy"
        atlas_path = PROJECT_ROOT / "atlas_data.json"

        # Load ID mapping first so we know how many vectors to generate
        n_items = 1000  # default fallback
        if atlas_path.exists():
            with open(atlas_path, "r") as f:
                atlas_json = json.load(f)
                for i, item in enumerate(atlas_json):
                    str_id = item.get("id", f"ID_{i}")
                    id_map[i] = str_id
                    reverse_map[str_id] = i
                n_items = len(atlas_json)
            logger.info(f"Loaded {len(id_map)} ID mappings from atlas_data.json")
        else:
            logger.warning("atlas_data.json not found — using numeric IDs")

        # Load vectors
        if embeddings_path.exists():
            vectors = np.load(str(embeddings_path)).astype("float32")
            logger.info(f"Loaded {vectors.shape[0]} vectors ({vectors.shape[1]}D)")
        else:
            logger.warning(
                "embeddings_checkpoint.npy not found — generating %d mock vectors", n_items
            )
            np.random.seed(42)
            vectors = np.random.rand(n_items, 512).astype("float32")

        # If atlas wasn't loaded yet, build numeric IDs matching vector count
        if not id_map:
            for i in range(vectors.shape[0]):
                id_map[i] = f"ID_{i}"
                reverse_map[f"ID_{i}"] = i

        # Build FAISS index (or skip if unavailable)
        if faiss_available and faiss is not None:
            d = vectors.shape[1]
            index = faiss.IndexFlatL2(d)
            index.add(vectors)
            logger.info(f"FAISS index built: {index.ntotal} vectors")
        else:
            logger.info("Using numpy fallback for similarity search")

    except Exception as e:
        logger.error(f"Error loading data: {e}", exc_info=True)


# ---------------------------------------------------------------------------
# App Lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_data()
    yield


app = FastAPI(title="DreaMS Atlas", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request Logging & Cache Headers Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def process_request(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = (time.time() - start) * 1000
    
    path = request.url.path
    
    # Add Cache-Control for static assets
    if any(path.endswith(ext) for ext in [".js", ".css", ".png", ".jpg", ".svg", ".woff2", ".json"]):
        # 1 day cache for assets, 1 hour for json
        max_age = 3600 if path.endswith(".json") else 86400
        response.headers["Cache-Control"] = f"public, max-age={max_age}"
    
    # Log API requests (skip static assets to reduce noise)
    if path.startswith("/api/") or path in ("/healthz", "/search"):
        logger.info(
            f"{request.method} {path} → {response.status_code} ({elapsed:.1f}ms) "
            f"[{request.client.host if request.client else '?'}]"
        )
    return response


# ---------------------------------------------------------------------------
# Health & Status
# ---------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    vec_count = 0
    if index is not None:
        vec_count = index.ntotal
    elif vectors is not None:
        vec_count = vectors.shape[0]
    return {
        "status": "alive",
        "vectors": vec_count,
        "faiss": faiss_available,
        "cache_size": len(search_cache._cache),
    }


@app.get("/api/status")
def api_status():
    vec_count = 0
    if index is not None:
        vec_count = index.ntotal
    elif vectors is not None:
        vec_count = vectors.shape[0]
    return {"status": "ok", "vectors": vec_count, "faiss": faiss_available}


# ---------------------------------------------------------------------------
# Search API (rate-limited, validated, cached)
# ---------------------------------------------------------------------------
def _do_search(query_id: str, k: int) -> list[dict]:
    """Core search logic — uses cache, FAISS or numpy fallback."""
    cache_key = f"{query_id}:{k}"
    cached = search_cache.get(cache_key)
    if cached is not None:
        return cached

    query_idx = reverse_map.get(query_id, -1)
    if query_idx == -1:
        raise HTTPException(status_code=404, detail="ID not found")

    if vectors is None:
        raise HTTPException(status_code=503, detail="Search data not loaded")

    query_vec = vectors[query_idx].reshape(1, -1)

    if index is not None:
        D, I = index.search(query_vec, k)
    else:
        D, I = numpy_search(query_vec, k)

    results = []
    for rank, idx in enumerate(I[0]):
        dist = float(D[0][rank])
        neighbor_id = id_map.get(int(idx), f"Unknown_{idx}")
        results.append(
            {"id": neighbor_id, "score": round(1.0 / (1.0 + dist), 6), "rank": rank}
        )

    search_cache.put(cache_key, results)
    return results


@app.get("/api/search")
def api_search(request: Request, id: str, k: int = 20):
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    # Input validation
    clean_id = validate_search_id(id)
    k = max(1, min(k, 100))  # Clamp k to [1, 100]

    results = _do_search(clean_id, k)
    return {"query": clean_id, "results": results}


@app.get("/search")
def search_legacy(request: Request, id: str, k: int = 20):
    """Legacy endpoint — same as /api/search."""
    return api_search(request=request, id=id, k=k)


# ---------------------------------------------------------------------------
# Analytics API
# ---------------------------------------------------------------------------
@app.post("/api/track")
async def api_track(request: Request):
    """Log an analytics event."""
    try:
        data = await request.json()
        event = data.get("event", "unknown")
        meta = data.get("meta", {})
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"TRACK: {event} | {json.dumps(meta)} | IP: {client_ip}")
        return {"status": "logged"}
    except Exception as e:
        logger.error(f"Track error: {e}")
        return {"status": "error"}


# ---------------------------------------------------------------------------
# Static File Serving
# ---------------------------------------------------------------------------
@app.get("/")
async def serve_index():
    index_path = PROJECT_ROOT / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return HTMLResponse("<h1>DreaMS Atlas</h1><p>index.html not found</p>", status_code=404)


@app.get("/{path:path}")
async def serve_static(path: str):
    """Catch-all: serve static files from project root."""
    file_path = (PROJECT_ROOT / path).resolve()

    # Security: prevent path traversal
    if not str(file_path).startswith(str(PROJECT_ROOT)):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Block sensitive files
    if file_path.name in (".env", ".git", ".gitignore") or ".git/" in str(file_path):
        raise HTTPException(status_code=403, detail="Forbidden")

    if file_path.is_file():
        suffix = file_path.suffix.lower()
        media_types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".woff": "font/woff",
            ".woff2": "font/woff2",
            ".ttf": "font/ttf",
        }
        media_type = media_types.get(suffix, "application/octet-stream")
        return FileResponse(str(file_path), media_type=media_type)

    raise HTTPException(status_code=404, detail=f"Not found: {path}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
