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
from fastapi.responses import FileResponse, JSONResponse

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

# ---------------------------------------------------------------------------
# API Key Auth
# ---------------------------------------------------------------------------
# Maps raw key string -> {"tenant_id": str, "label": str}
# Populated at startup from config/api_keys.json.
# If the file is absent, auth is disabled (warn-only) so local dev still works.
api_keys: dict[str, dict] = {}

# Paths that bypass authentication entirely.
SKIP_AUTH_PATHS: frozenset[str] = frozenset({"/healthz"})


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

try:
    import faiss
    faiss_available = True
except Exception:
    faiss = None  # type: ignore[assignment]
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
    global index, vectors

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


# Added after process_request so Starlette registers it as the outermost
# wrapper — meaning it runs first on every inbound request.
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    path = request.url.path

    # Health check is always public.
    if path in SKIP_AUTH_PATHS:
        return await call_next(request)

    # Auth is disabled when no keys are configured (e.g. local dev without config).
    if not api_keys:
        return await call_next(request)

    # Extract key from Authorization header (Bearer) or ?api_key= query param.
    key: str | None = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        key = auth_header[7:]
    if not key:
        key = request.query_params.get("api_key") or None

    if key is None:
        return JSONResponse({"detail": "Missing API key"}, status_code=401)

    # Dict lookup is hash-based (O(1), no character-by-character timing leak).
    meta = api_keys.get(key)
    if meta is None:
        logger.warning(f"AUTH: rejected invalid key for {request.method} {path}")
        return JSONResponse({"detail": "Invalid API key"}, status_code=401)

    # Bind the key's tenant to the request so downstream handlers use it.
    request.state.tenant_id = meta.get("tenant_id", "default")
    return await call_next(request)


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"status": "alive", "vectors": len(id_map), "faiss": index is not None}


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

    # Key-bound tenant takes precedence over the query param so callers
    # cannot escalate to another tenant by changing ?tenant_id=.
    effective_tenant = getattr(request.state, "tenant_id", tenant_id)

    # Mock data isolation: filter results based on effective_tenant
    # In a real app, this would filter the FAISS index or lookup table.
    logger.info(f"SEARCH [Tenant: {effective_tenant}] | ID: {clean_id} | k: {k}")

    cache_key = f"{effective_tenant}:{clean_id}:{k}"
    cached = search_cache.get(cache_key)
    if cached:
        return {"query": clean_id, "tenant": effective_tenant, "results": cached}

    query_idx = reverse_map.get(clean_id, -1)
    if query_idx == -1:
        raise HTTPException(status_code=404)
    if vectors is None:
        raise HTTPException(status_code=503)

    query_vec = vectors[query_idx].reshape(1, -1)
    if index:
        D, indices = index.search(query_vec, k)
    else:
        D, indices = numpy_search(query_vec, k)

    results = []
    for rank, idx in enumerate(indices[0]):
        dist = float(D[0][rank])
        results.append({"id": id_map.get(int(idx)),
                       "score": round(1.0/(1.0+dist), 6), "rank": rank})

    # Mock tenant-specific filtering (simulated)
    if effective_tenant != "default":
        # Role-Based Access Control (RBAC) Logic
        # Admin can see everything, Viewer only sees even IDs
        user_role = request.headers.get("X-User-Role", "viewer")
        if user_role == "viewer":
            results = [r for r in results if hash(f"{effective_tenant}{r['id']}") % 2 == 0]
        logger.info(f"RBAC: Filtered results for role {user_role} (Tenant: {effective_tenant})")

    search_cache.put(cache_key, results)
    return {"query": clean_id, "tenant": effective_tenant, "results": results}


@app.get("/api/auth/sso/callback")
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


@app.get("/api/export")
def api_export(ids: str, request: Request):
    """Export compound IDs as CSV."""
    import csv
    import io
    from fastapi.responses import StreamingResponse

    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit")

    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "rank"])
    for rank, compound_id in enumerate(id_list):
        clean_id = validate_search_id(compound_id)
        writer.writerow([clean_id, rank])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"},
    )


@app.post("/api/track")
async def api_track(request: Request):
    try:
        data = await request.json()
        logger.info(f"TRACK: {data.get('event')} | {data.get('meta')}")
        return {"status": "ok"}
    except Exception:
        return {"status": "err"}

# ---------------------------------------------------------------------------
# Phase 16: Interoperability logic
# ---------------------------------------------------------------------------


@app.get("/api/eln/context")
def eln_context(id: str, experiment_type: str = "similarity_review"):
    """Generate 'Chemical Context' injection for automated experiment log metadata."""
    clean_id = validate_search_id(id)
    if clean_id not in reverse_map:
        raise HTTPException(status_code=404, detail="Compound not found")

    # In a real app, we'd fetch actual metadata and neighborhood stats
    context = {
        "molecule_id": clean_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "experiment": experiment_type,
        "atlas_neighborhood": "Cluster_0",  # Mock
        "recommended_action": "Verify spectrum similarity with Scytonemin reference.",
        "log_entry": (
            f"DREAM-CONTEXT: [{clean_id}] Analysis in DreaMS Atlas. "
            "Part of neighborhood Cluster_0. Recommended for further spectral deconvolution."
        )
    }
    return context


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


@app.post("/api/dotmatics/sync")
def dotmatics_sync(id: str, payload: dict = None):
    """Mock Dotmatics integration hook."""
    clean_id = validate_search_id(id)
    # Simulate pushing data to Dotmatics
    logger.info(f"DOTMATICS SYNC: Pushing {clean_id} to Dotmatics gateway.")
    return {
        "status": "success",
        "molecule_id": clean_id,
        "dotmatics_record_id": f"DX-{int(time.time())}",
        "synced_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


@app.get("/api/molecule/smiles")
def get_smiles(id: str):
    """Return mock SMILES for a given compound ID."""
    clean_id = validate_search_id(id)
    # Mock SMILES mapping
    mock_smiles = {
        "Scytonemin M+H": "C1=CC=C2C(=C1)C3=C(N2)C(=O)C(=C3)C4=CC5=C(C=C4)NC6=CC=CC=C56",
        "Salinisporamide A M+H": "CC1C(C(=O)N1C(CC2=CC=CC=C2)C(=O)O)C(C)O",
        "Hectochlorin M+H": "CCCCCCCCCCC(C(CC(=O)NC(C(C)OC(=O)C)C(=O)O)O)Cl"
    }
    # Caffeine fallback
    return {"id": clean_id, "smiles": mock_smiles.get(clean_id, "CN1C=NC2=C1C(=O)N(C(=O)N2C)C")}

# ---------------------------------------------------------------------------
# Phase 20: Predictive ADMET & Safety Intelligence
# ---------------------------------------------------------------------------


@app.get("/api/safety/score")
def safety_score(id: str):
    """ADMET and safety scoring — roadmap feature."""
    validate_search_id(id)
    return {"status": "coming_soon", "feature": "Predictive ADMET & Safety Scoring", "eta": "Q3 2026", "contact": "hello@gstack.ai"}


@app.get("/api/safety/sds")
def safety_sds(id: str):
    """Safety Data Sheet generation — roadmap feature."""
    validate_search_id(id)
    return {"status": "coming_soon", "feature": "Safety Data Sheet Generation", "eta": "Q3 2026", "contact": "hello@gstack.ai"}

# ---------------------------------------------------------------------------
# Phase 21: High-Throughput Screening (HTS) & Assay Data Fusion
# ---------------------------------------------------------------------------


@app.get("/api/hts/assay")
def hts_assay(id: str):
    """HTS assay data fusion — roadmap feature."""
    validate_search_id(id)
    return {"status": "coming_soon", "feature": "High-Throughput Screening Assay Data", "eta": "Q3 2026", "contact": "hello@gstack.ai"}


@app.get("/api/hts/sar")
def hts_sar_map(cluster_id: int = 0):
    """Mock SAR heatmap data for a chemical cluster."""
    # Return mock IDs and their assay activities
    results = []
    for i in range(10):
        mock_id = f"MOL_{cluster_id}_{i}"
        results.append({
            "id": mock_id,
            "activity": round(10 + (hash(mock_id) % 90), 2),
            "status": "active" if (hash(mock_id) % 100) > 70 else "inactive"
        })
    return {"cluster": cluster_id, "data": results}

# ---------------------------------------------------------------------------
# Phase 22: Sustainable Chemistry & Green Synthesis Score
# ---------------------------------------------------------------------------


@app.get("/api/sustainability/score")
def sustainability_score(id: str):
    """Sustainability and Green Chemistry scoring (Mock)."""
    clean_id = validate_search_id(id)
    h = hash(clean_id)

    atom_economy = round(70 + (h % 30), 2)
    e_factor = round(5 + (h % 95), 1)

    # Inventory check
    inventory = ["Acetone", "Ethanol"] if (h % 2) == 0 else ["DCM", "THF", "Toluene"]

    return {
        "id": clean_id,
        "green_score": round((atom_economy / 100.0) * (1.0 - (e_factor / 200.0)) * 100, 1),
        "metrics": {
            "atom_economy": f"{atom_economy}%",
            "e_factor": e_factor,
            "solvent_safety": "High" if e_factor < 20 else "Moderate",
            "carbon_footprint": f"{round(e_factor * 0.5, 2)} kg CO2/kg"
        },
        "inventory_reagents": inventory,
        "status": "GREEN" if atom_economy > 85 and e_factor < 15 else "STANDARD"
    }

# ---------------------------------------------------------------------------
# Phase 23: Global R&D Collaboration & IP Management
# ---------------------------------------------------------------------------


@app.get("/api/ip/check")
def ip_check(id: str):
    """Mock IP/Patent check and Freedom to Operate (FTO)."""
    clean_id = validate_search_id(id)
    h = hash(clean_id)

    # Simulate patent matches
    patents = []
    if h % 5 == 0:
        patents.append({"id": f"US-{h % 10000000}-B2",
                       "assignee": "Competitor Pharma", "status": "Active"})

    return {
        "id": clean_id,
        "fto_status": "CLEAR" if not patents else "POTENTIAL_CONFLICT",
        "matches": patents,
        "novelty_score": round(0.7 + (h % 30) / 100.0, 2),
        "ip_protection_recommendation": "File Provisional" if not patents else "Redesign Scaffold"
    }


@app.post("/api/collaboration/sign")
async def collaboration_sign(request: Request):
    """Mock E-signature for experimental sign-off."""
    try:
        data = await request.json()
        logger.info(f"COLLAB SIGN: {data.get('user')} signed off on {data.get('id')}")
        return {
            "status": "success",
            "signature_id": f"SIG-{int(time.time())}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception:
        return {"status": "error"}

# ---------------------------------------------------------------------------
# Phase 25: Real-World Data Integration & Property Mapping
# ---------------------------------------------------------------------------


@app.get("/api/molecule/properties")
def get_molecule_properties(id: str):
    """Return high-fidelity adhesive property overlays (Tack, Shear, Viscosity)."""
    clean_id = validate_search_id(id)
    h = hash(clean_id)

    # Deterministic mock property mapping
    return {
        "id": clean_id,
        "properties": {
            "tack": round(2.0 + (h % 80) / 10.0, 2),        # N/25mm
            "shear": round(100 + (h % 900), 0),           # minutes
            "viscosity": round(500 + (h % 4500), 0),      # mPa·s
            "glass_transition_temp": round(-60 + (h % 40), 1),  # °C
            "solids_content": round(30 + (h % 40), 1)      # %
        },
        "confidence_score": round(0.85 + (h % 15) / 100.0, 2)
    }


@app.post("/api/onboard/upload")
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


@app.get("/api/validation/similarity")
def validation_similarity(id_a: str, id_b: str):
    """Compare DreaMS similarity vs. experimental chemical relatedness."""
    clean_a = validate_search_id(id_a)
    clean_b = validate_search_id(id_b)

    # Mock validation score
    dreams_score = round(0.4 + (hash(clean_a + clean_b) % 60) / 100.0, 2)
    experimental_score = round(dreams_score + (hash(clean_a) % 10 - 5) / 100.0, 2)

    return {
        "comparison": [clean_a, clean_b],
        "dreams_similarity": dreams_score,
        "experimental_relatedness": experimental_score,
        "delta": round(abs(dreams_score - experimental_score), 3),
        "status": "VALIDATED" if abs(dreams_score - experimental_score) < 0.1 else "OUTLIER"
    }

# ---------------------------------------------------------------------------
# Static Files
# ---------------------------------------------------------------------------


@app.get("/")
async def serve_index():
    return FileResponse(str(PROJECT_ROOT / "index.html"))

_STATIC_DENYLIST: frozenset[str] = frozenset({"config", "vault", "memory"})


@app.get("/{path:path}")
async def serve_static(path: str):
    file_path = (PROJECT_ROOT / path).resolve()
    if not str(file_path).startswith(str(PROJECT_ROOT)):
        raise HTTPException(status_code=403)
    # Block sensitive server-side directories from being served as static files.
    top_dir = Path(path).parts[0] if Path(path).parts else ""
    if top_dir in _STATIC_DENYLIST:
        raise HTTPException(status_code=403)
    if file_path.is_file():
        return FileResponse(str(file_path))
    raise HTTPException(status_code=404, detail=f"Not found: {path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
