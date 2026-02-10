
import faiss
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# Enable CORS for frontend access (localhost:8000 -> localhost:3000/github.io)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global FAISS Index
index = None
vectors = None
id_map = {} # map internal index to string ID

def load_data():
    global index, vectors, id_map
    
    print("Loading embeddings...")
    try:
        # Load high-dim vectors
        if os.path.exists("embeddings_checkpoint.npy"):
            vectors = np.load("embeddings_checkpoint.npy").astype('float32')
            print(f"Loaded {vectors.shape[0]} vectors with {vectors.shape[1]} dimensions.")
        else:
            print("Warning: embeddings_checkpoint.npy not found. Using mock data.")
            vectors = np.random.rand(5000, 1024).astype('float32')

        # Load ID mapping from atlas_data.json (assuming order matches)
        if os.path.exists("atlas_data.json"):
            with open("atlas_data.json", "r") as f:
                atlas_json = json.load(f)
                # Map index i -> id string
                for i, item in enumerate(atlas_json):
                    id_map[i] = item.get("id", f"ID_{i}")
        else:
            print("Warning: atlas_data.json not found. Using numeric IDs.")
            for i in range(vectors.shape[0]):
                id_map[i] = f"ID_{i}"

        # Build FAISS Index
        d = vectors.shape[1]
        # Using HNSW for fast approximate search, or FlatL2 for exact (slow but fine for <1M)
        # For <100k, FlatL2 is instant and exact.
        index = faiss.IndexFlatL2(d) 
        index.add(vectors)
        print(f"FAISS Index built with {index.ntotal} vectors.")
        
    except Exception as e:
        print(f"Error loading data: {e}")

# Initialize on startup
load_data()

@app.get("/")
def read_root():
    return {"status": "ok", "vectors": index.ntotal if index else 0}

@app.get("/search")
def search(id: str, k: int = 20):
    global index, vectors, id_map
    
    # 1. Find vector for the given ID
    query_vec = None
    query_idx = -1
    
    # Reverse lookup ID -> Index (naive O(N) but fine for demo size)
    # Ideally build a reverse map on load
    for i, mapped_id in id_map.items():
        if mapped_id == id:
            query_idx = i
            break
            
    if query_idx == -1:
        raise HTTPException(status_code=404, detail="ID not found")
        
    query_vec = vectors[query_idx].reshape(1, -1)
    
    # 2. Search FAISS
    D, I = index.search(query_vec, k)
    
    # 3. Format results
    results = []
    for rank, idx in enumerate(I[0]):
        dist = float(D[0][rank])
        neighbor_id = id_map.get(idx, f"Unknown_{idx}")
        results.append({
            "id": neighbor_id,
            "score": 1.0 / (1.0 + dist), # convert L2 distance to similarity score
            "rank": rank
        })
        
    return {"query": id, "results": results}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
