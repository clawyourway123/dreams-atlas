
# DreaMS FAISS Backend

Scalable similarity search service for the Chemical Space Atlas.
Decouples the search logic from the browser, allowing the atlas to scale to millions of points.

## Setup

1. Install dependencies:
   ```bash
   pip install fastapi uvicorn faiss-cpu numpy
   ```

2. Place data files in root:
   - `embeddings_checkpoint.npy` (High-dimensional vectors)
   - `atlas_data.json` (ID mapping)

3. Run server:
   ```bash
   python3 backend/server.py
   ```

4. API Endpoints:
   - `GET /`: Health check + vector count.
   - `GET /search?id=CompoundName&k=20`: Returns top 20 nearest neighbors.

## Integration

Update `atlas-viewer.js` to fetch from this API instead of calculating Euclidean distance client-side.
