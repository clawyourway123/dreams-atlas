# DreaMS Atlas Architecture

## Overview

DreaMS Atlas is an interactive 3D chemical space explorer that uses FAISS-powered similarity search over spectral embeddings. It consists of a FastAPI backend, a static HTML/JS frontend, and offline ML training pipelines.

## System Diagram

```
                      +---------------------+
                      |   Browser Client    |
                      | (index.html + JS)   |
                      +----------+----------+
                                 |
                          HTTPS / REST
                                 |
                      +----------v----------+
                      |   FastAPI Backend   |
                      |   (backend/server.py)|
                      +----+-----+-----+----+
                           |     |     |
               +-----------+     |     +-----------+
               |                 |                 |
      +--------v------+  +------v------+  +-------v-------+
      | FAISS Index   |  | Vault Mgr   |  | Rate Limiter  |
      | (in-memory)   |  | (per-tenant)|  | + LRU Cache   |
      +--------+------+  +------+------+  +---------------+
               |                 |
      +--------v------+  +------v------+
      | embeddings_   |  | vault/      |
      | checkpoint.npy|  | <tenant>/   |
      +---------------+  +-------------+

      +----------------------------------------------+
      | Offline ML Pipeline (train_ir_raman_models.py)|
      | RandomForest (primary) + CNN-1D (secondary)   |
      | Input: adhesive_spectra_ir_raman_intensities.csv|
      | Output: model_output/*.joblib, *.pth           |
      +----------------------------------------------+
```

## Components

### Frontend

- **index.html** -- Main landing page with 3D atlas viewer, pilot program gallery, and extended gallery.
- **atlas-viewer.js / atlas-viewer-lab.js** -- Three.js-based 3D visualization of the chemical embedding space. The lab variant adds interactive controls.
- **atlas.css / mobile-responsive.css / brand-themes.css** -- Styling including responsive breakpoints and per-brand theming.
- **plotly-loader.js** -- Lazy Plotly.js loader for chart overlays.
- **brand-config.js** -- Per-company brand colors and configuration.
- **examples/branded-demos/** -- Company-specific demo pages (Henkel, 3M, BASF, etc.).

### Backend (`backend/`)

- **server.py** -- FastAPI application with:
  - **FAISS similarity search** (`/api/search`) with numpy fallback.
  - **Multi-tenant isolation** via `VaultManager` -- per-tenant embeddings and indices.
  - **API key authentication** middleware (optional, disabled when no keys configured).
  - **Rate limiting** -- sliding-window, 60 req/min per IP.
  - **LRU cache** -- 512-entry cache for search results.
  - **Cluster analysis** endpoints (`/api/cluster/list`, `/api/cluster/insights`).
  - **Export** endpoint (`/api/export`) for CSV download.
  - **Tracking** endpoint (`/api/track`) for analytics events.
  - **Roadmap stubs** -- ELN, LIMS, Dotmatics, ADMET, HTS, sustainability, IP check endpoints returning `coming_soon`.
  - **GZip middleware** and **CORS** configured for all origins.
- **vault_manager.py** -- Resolves per-tenant data paths and caches FAISS indices.
- **benchmark_search.py** -- Performance benchmarking for the search backend.
- **tests/** -- Integration tests for live deployment validation.

### ML Pipeline

- **train_ir_raman_models.py** -- Trains two classifiers on IR/Raman spectral intensity data:
  - **RandomForest** (primary production model) -- 500 trees, balanced class weights, compound-grouped 5-fold CV.
  - **CNN-1D** (secondary) -- PyTorch 1D convolutional network, 300 epochs with cosine annealing.
  - Outputs saved to `model_output/`.
- **generate_spectral_intensities.py** -- Generates synthetic spectral intensity data.
- **generate_demos.py** -- Generates branded demo HTML pages from a template.

### Data Files

- **atlas_data.json** -- 10,000+ spectra with embedding coordinates and cluster assignments.
- **embeddings_checkpoint.npy** -- Pre-computed 512-dim embedding vectors for FAISS indexing.
- **adhesive_spectra_ir_raman_intensities.csv** -- Training data with wavenumber intensity features.

## Data Flow

1. **Startup**: `server.py` loads `embeddings_checkpoint.npy` and `atlas_data.json`, builds a FAISS `IndexFlatL2` index, and computes cluster statistics.
2. **Search request**: Client sends `GET /api/search?id=SPECTRUM_ID&k=20`. Backend resolves the tenant, looks up the query vector, runs FAISS (or numpy) nearest-neighbor search, and returns ranked results with similarity scores.
3. **Multi-tenant**: When `config/api_keys.json` is present, requests are routed to tenant-specific indices via `VaultManager`. Without keys, all requests use the default global index.
4. **Caching**: Search results are cached in an LRU cache keyed by `tenant:id:k`. Identical queries return cached results in <1ms.

## Deployment

- **Render** -- Production deployment via `render.yaml` and `Dockerfile`.
- **Docker Compose** -- Local development via `docker-compose.yml`.
- **demo-start.sh** -- Quick local startup script (installs deps, starts uvicorn).
- Frontend is served as static files by the FastAPI catch-all route. The root `/` redirects to `FRONTEND_URL`.

## Key Design Decisions

- **FAISS with numpy fallback**: Ensures the system works even when `faiss-cpu` cannot be installed, at the cost of slower search (<50ms vs <10ms).
- **In-memory everything**: Embeddings, indices, and caches are all in-memory for sub-10ms latency. Trade-off: higher memory usage (~150MB for 10K 512-dim vectors).
- **Compound-grouped CV**: Training pipeline uses `GroupKFold` on compound names to prevent data leakage between chemically related samples.
- **Static file serving from FastAPI**: Simplifies deployment to a single process. Sensitive directories (`config`, `vault`, `memory`) are denied via a static denylist.
