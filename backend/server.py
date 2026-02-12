"""DreaMS Atlas — FastAPI backend with FAISS similarity search.

Phase 6/12 hardening: rate limiting, input validation, request logging,
LRU caching, graceful degradation, and GZip.

v2.2 — 2026-02-12: Added Phase 12 hardening (GZip, Logs API, Resilience).
"""

import json
import logging
import os
import re
import time
from collections import deque, OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse

# ---------------------------------------------------------------------------
# Logging & Event Tracking
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("dreams-atlas")

# Keep last 100 log messages in memory for /api/logs
event_log = deque(maxlen=100)

class LogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
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

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
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

rate_limiter = RateLimiter(max_requests=60, window_seconds=60)


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
def numpy_search(query_vec: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Brute-force L2 search using numpy — fallback when faiss is unavailable."""
    diffs = vectors - query_vec
    dists = np.sum(diffs ** 2, axis=1)
    top_k = np.argpartition(dists, k)[:k]
    top_k_sorted = top_k[np.argsort(dists[top_k])]
    return dists[top_k_sorted].reshape(1, -1), top_k_sorted.reshape(1, -1)


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
def load_data(retries=3):
    global index, vectors, id_map, reverse_map

    for attempt in range(retries):
        logger.info(f"Loading data (attempt {attempt + 1}/{retries})...")
        try:
            embeddings_path = PROJECT_ROOT / "embeddings_checkpoint.npy"
            atlas_path = PROJECT_ROOT / "atlas_data.json"

            id_map.clear()
            reverse_map.clear()

            n_items = 1000
            if atlas_path.exists():
                with open(atlas_path, "r") as f:
                    atlas_json = json.load(f)
                    for i, item in enumerate(atlas_json):
                        str_id = item.get("id", f"ID_{i}")
                        id_map[i] = str_id
                        reverse_map[str_id] = i
                    n_items = len(atlas_json)
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
                d = vectors.shape[1]
                index = faiss.IndexFlatL2(d)
                index.add(vectors)
                logger.info(f"FAISS index built: {index.ntotal}")
            else:
                logger.info("Using numpy search")
            
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
    load_data()
    yield


app = FastAPI(title="DreaMS Atlas", lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Middleware: Logging & Cache
# ---------------------------------------------------------------------------
@app.middleware("http")
async def process_request(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = (time.time() - start) * 1000
    path = request.url.path
    
    if any(path.endswith(ext) for ext in [".js", ".css", ".png", ".jpg", ".json"]):
        max_age = 3600 if path.endswith(".json") else 86400
        response.headers["Cache-Control"] = f"public, max-age={max_age}"
    
    if path.startswith("/api/") or path in ("/healthz", "/search"):
        logger.info(f"{request.method} {path} -> {response.status_code} ({elapsed:.1f}ms)")
    
    return response

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"status": "alive", "vectors": len(id_map), "faiss": faiss_available}

@app.get("/api/status")
def api_status():
    return {"status": "ok", "vectors": len(id_map), "cache": len(search_cache._cache)}

@app.get("/api/logs")
def get_logs():
    return list(event_log)

@app.get("/api/search")
def api_search(request: Request, id: str, k: int = 20, tenant_id: str = "default"):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit")

    clean_id = validate_search_id(id)
    k = max(1, min(k, 100))

    # Mock data isolation: filter results based on tenant_id
    # In a real app, this would filter the FAISS index or lookup table.
    logger.info(f"SEARCH [Tenant: {tenant_id}] | ID: {clean_id} | k: {k}")

    cache_key = f"{tenant_id}:{clean_id}:{k}"
    cached = search_cache.get(cache_key)
    if cached: return {"query": clean_id, "tenant": tenant_id, "results": cached}

    query_idx = reverse_map.get(clean_id, -1)
    if query_idx == -1: raise HTTPException(status_code=404)
    if vectors is None: raise HTTPException(status_code=503)

    query_vec = vectors[query_idx].reshape(1, -1)
    if index: D, I = index.search(query_vec, k)
    else: D, I = numpy_search(query_vec, k)

    results = []
    for rank, idx in enumerate(I[0]):
        dist = float(D[0][rank])
        results.append({"id": id_map.get(int(idx)), "score": round(1.0/(1.0+dist), 6), "rank": rank})

    # Mock tenant-specific filtering (simulated)
    if tenant_id != "default":
        # Simulate that some tenants only see a subset (e.g., even IDs)
        results = [r for r in results if hash(f"{tenant_id}{r['id']}") % 2 == 0]

    search_cache.put(cache_key, results)
    return {"query": clean_id, "tenant": tenant_id, "results": results}

@app.post("/api/track")
async def api_track(request: Request):
    try:
        data = await request.json()
        logger.info(f"TRACK: {data.get('event')} | {data.get('meta')}")
        return {"status": "ok"}
    except: return {"status": "err"}

# ---------------------------------------------------------------------------
# Phase 16.5: Interoperability logic
# ---------------------------------------------------------------------------
@app.get("/api/eln/export")
def eln_export(id: str, format: str = "benchling"):
    """Export compound metadata in ELN-friendly formats."""
    clean_id = validate_search_id(id)
    if clean_id not in reverse_map:
        raise HTTPException(status_code=404, detail="Compound not found")
    
    # Mock metadata retrieval
    metadata = {
        "id": clean_id,
        "source": "DreaMS Atlas v2.5",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "eln_target": format
    }
    
    if format == "benchling":
        return {
            "schema": "benchling:entity:v1",
            "entity": {
                "name": clean_id,
                "type": "molecule",
                "custom_fields": {
                    "DreaMS_ID": clean_id,
                    "Atlas_Link": f"https://dreams-atlas.onrender.com/search?id={clean_id}"
                }
            }
        }
    
    return metadata

# ---------------------------------------------------------------------------
# Phase 16.5: LIMS Ingestion
# ---------------------------------------------------------------------------
@app.get("/api/lims/ingest")
def lims_ingest(smiles: str):
    """SMILES-to-Spectrum mapping for LIMS ingestion (Mock)."""
    # Simple hash-based mapping for demo
    mock_id = f"MOL_{abs(hash(smiles)) % 5000}"
    query_idx = reverse_map.get(mock_id, 0)
    str_id = id_map.get(query_idx, "Unknown")
    
    return {
        "smiles": smiles,
        "matched_spectrum_id": str_id,
        "confidence": 0.89,
        "status": "LIMS_READY"
    }

# ---------------------------------------------------------------------------
# Static Files
# ---------------------------------------------------------------------------
@app.get("/")
async def serve_index():
    return FileResponse(str(PROJECT_ROOT / "index.html"))

@app.get("/{path:path}")
async def serve_static(path: str):
    file_path = (PROJECT_ROOT / path).resolve()
    if not str(file_path).startswith(str(PROJECT_ROOT)): raise HTTPException(status_code=403)
    if file_path.is_file(): return FileResponse(str(file_path))
    raise HTTPException(status_code=404, detail=f"Not found: {path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
