import faiss
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import json
import os
from pathlib import Path

# Resolve the project root (one level up from backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

app = FastAPI()

# Enable CORS for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# FAISS / Search Backend
# ---------------------------------------------------------------------------
index = None
vectors = None
id_map = {}  # map internal index to string ID
reverse_map = {}  # map string ID to internal index (fast lookup)


def load_data():
    global index, vectors, id_map, reverse_map

    print("Loading embeddings...")
    try:
        embeddings_path = PROJECT_ROOT / "embeddings_checkpoint.npy"
        atlas_path = PROJECT_ROOT / "atlas_data.json"

        # Load high-dim vectors
        if embeddings_path.exists():
            vectors = np.load(str(embeddings_path)).astype("float32")
            print(f"Loaded {vectors.shape[0]} vectors with {vectors.shape[1]} dimensions.")
        else:
            print("Warning: embeddings_checkpoint.npy not found. Using mock data.")
            vectors = np.random.rand(5000, 1024).astype("float32")

        # Load ID mapping from atlas_data.json
        if atlas_path.exists():
            with open(atlas_path, "r") as f:
                atlas_json = json.load(f)
                for i, item in enumerate(atlas_json):
                    str_id = item.get("id", f"ID_{i}")
                    id_map[i] = str_id
                    reverse_map[str_id] = i
        else:
            print("Warning: atlas_data.json not found. Using numeric IDs.")
            for i in range(vectors.shape[0]):
                id_map[i] = f"ID_{i}"
                reverse_map[f"ID_{i}"] = i

        # Build FAISS Index (FlatL2 is fast & exact for <100k vectors)
        d = vectors.shape[1]
        index = faiss.IndexFlatL2(d)
        index.add(vectors)
        print(f"FAISS Index built with {index.ntotal} vectors.")

    except Exception as e:
        print(f"Error loading data: {e}")


# Initialize on startup
load_data()


# ---------------------------------------------------------------------------
# API Routes (under /api/)
# ---------------------------------------------------------------------------
@app.get("/api/status")
def api_status():
    return {"status": "ok", "vectors": index.ntotal if index else 0}


@app.get("/api/search")
def api_search(id: str, k: int = 20):
    global index, vectors, id_map, reverse_map

    query_idx = reverse_map.get(id, -1)
    if query_idx == -1:
        raise HTTPException(status_code=404, detail="ID not found")

    query_vec = vectors[query_idx].reshape(1, -1)
    D, I = index.search(query_vec, k)

    results = []
    for rank, idx in enumerate(I[0]):
        dist = float(D[0][rank])
        neighbor_id = id_map.get(int(idx), f"Unknown_{idx}")
        results.append(
            {
                "id": neighbor_id,
                "score": 1.0 / (1.0 + dist),
                "rank": rank,
            }
        )
    return {"query": id, "results": results}


# Keep legacy /search endpoint for backward compat
@app.get("/search")
def search_legacy(id: str, k: int = 20):
    return api_search(id=id, k=k)


# ---------------------------------------------------------------------------
# Static File Serving
# ---------------------------------------------------------------------------
# Serve known static assets (CSS, JS, JSON, images) from project root
# We mount this AFTER API routes so /api/* takes priority.
# For HTML files (demo pages), we use a catch-all.

@app.get("/")
async def serve_index():
    """Serve the landing page."""
    index_path = PROJECT_ROOT / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return HTMLResponse("<h1>DreaMS Atlas</h1><p>index.html not found</p>", status_code=404)


@app.get("/{path:path}")
async def serve_static(path: str):
    """Catch-all: serve static files from project root."""
    file_path = (PROJECT_ROOT / path).resolve()

    # Security: prevent path traversal outside project root
    if not str(file_path).startswith(str(PROJECT_ROOT)):
        raise HTTPException(status_code=403, detail="Forbidden")

    if file_path.is_file():
        # Determine media type
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
            ".npy": "application/octet-stream",
        }
        media_type = media_types.get(suffix, "application/octet-stream")
        return FileResponse(str(file_path), media_type=media_type)

    raise HTTPException(status_code=404, detail=f"Not found: {path}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
