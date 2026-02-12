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
        "atlas_neighborhood": "Cluster_0", # Mock
        "recommended_action": "Verify spectrum similarity with Scytonemin reference.",
        "log_entry": f"DREAM-CONTEXT: [{clean_id}] Analysis in DreaMS Atlas. Part of neighborhood Cluster_0. Recommended for further spectral deconvolution."
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
    return {"id": clean_id, "smiles": mock_smiles.get(clean_id, "CN1C=NC2=C1C(=O)N(C(=O)N2C)C")} # Caffeine fallback

# ---------------------------------------------------------------------------
# Phase 20: Predictive ADMET & Safety Intelligence
# ---------------------------------------------------------------------------
@app.get("/api/safety/score")
def safety_score(id: str):
    """Predictive ADMET and safety scoring (Mock - Tox21/ClinTox integration)."""
    clean_id = validate_search_id(id)
    
    # Deterministic mock scoring based on ID hash
    h = hash(clean_id)
    tox21_score = round(0.5 + (h % 50) / 100.0, 2) # 0.5 - 0.99
    clintox_pass = (h % 10) > 1 # 80% pass rate
    
    # CYP450 Liabilities (Red Flags)
    liabilities = []
    if h % 7 == 0: liabilities.append("CYP3A4 Inhibition")
    if h % 11 == 0: liabilities.append("hERG Channel Blockade")
    if h % 13 == 0: liabilities.append("Hepatotoxicity Risk")
    
    # BBB Penetration
    bbb_prob = round((h % 100) / 100.0, 2)
    
    return {
        "id": clean_id,
        "tox21_safety_score": tox21_score,
        "clintox_status": "PASS" if clintox_pass else "FAIL",
        "red_flags": liabilities,
        "admet": {
            "logP": round(1.0 + (h % 40) / 10.0, 2),
            "molecular_weight": 200 + (h % 500),
            "bbb_penetration": bbb_prob,
            "h_bond_donors": h % 5,
            "h_bond_acceptors": h % 10
        },
        "mpo_score": round((tox21_score + bbb_prob + (1 if clintox_pass else 0)) / 3.0, 2)
    }

@app.get("/api/safety/sds")
def safety_sds(id: str):
    """Generate a mock Safety Data Sheet (SDS) for a molecule."""
    clean_id = validate_search_id(id)
    return {
        "id": clean_id,
        "document_type": "Safety Data Sheet (Draft)",
        "version": "2026.1",
        "sections": {
            "1_identification": f"Product: {clean_id} (DreaMS De Novo Candidate)",
            "2_hazard_identification": "GHS Category 4: Harmful if swallowed. Potential skin irritant.",
            "3_composition": f"Pure substance: {clean_id} (>98% purity target)",
            "4_first_aid": "In case of contact, flush with water. Seek medical attention if symptoms persist.",
            "8_exposure_controls": "Wear appropriate PPE (gloves, safety glasses, lab coat). Handle in a well-ventilated fume hood."
        },
        "disclaimer": "This is a predicted SDS based on ML models and has not been verified by physical testing."
    }

# ---------------------------------------------------------------------------
# Phase 21: High-Throughput Screening (HTS) & Assay Data Fusion
# ---------------------------------------------------------------------------
@app.get("/api/hts/assay")
def hts_assay(id: str):
    """Mock HTS Assay data (Dose-response, IC50)."""
    clean_id = validate_search_id(id)
    h = hash(clean_id)
    
    # Generate mock dose-response points
    doses = [0.01, 0.1, 1.0, 10.0, 100.0]
    # Simple sigmoid: 100 / (1 + (dose/IC50)^slope)
    ic50 = 0.5 + (h % 50) / 10.0
    slope = 1.0
    responses = [round(100 / (1 + (d/ic50)**slope), 2) for d in doses]
    
    return {
        "id": clean_id,
        "assay_type": "Kinase Inhibition (Mock)",
        "ic50_um": ic50,
        "unit": "uM",
        "dose_response": {
            "doses": doses,
            "responses": responses
        },
        "outlier_status": "NORMAL" if (h % 20) > 0 else "FLAGGED_OUTLIER"
    }

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
        patents.append({"id": f"US-{h % 10000000}-B2", "assignee": "Competitor Pharma", "status": "Active"})
    
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
    except: return {"status": "error"}

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
            "glass_transition_temp": round(-60 + (h % 40), 1), # °C
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

@app.get("/{path:path}")
async def serve_static(path: str):
    file_path = (PROJECT_ROOT / path).resolve()
    if not str(file_path).startswith(str(PROJECT_ROOT)): raise HTTPException(status_code=403)
    if file_path.is_file(): return FileResponse(str(file_path))
    raise HTTPException(status_code=404, detail=f"Not found: {path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
