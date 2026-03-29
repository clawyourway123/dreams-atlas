# DreaMS Atlas API Reference

**Base URL:** `https://dreams-atlas.onrender.com`
**Version:** 1.1
**Protocol:** REST / JSON

## API Versioning

The API uses URL-based versioning. All current endpoints are unversioned (`/api/*`).
Future breaking changes will be introduced under `/api/v2/*`. The unversioned paths will remain as aliases to the latest stable version.

---

## Authentication

All endpoints are **public** (no API key required for MVP). In production, optional Bearer token support:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" https://dreams-atlas.onrender.com/api/search?id=SPECTRUM_001&k=20
```

---

## Endpoints

### **1. Health Check**

#### `GET /healthz`

Check if the backend is running and ready.

**Request:**
```bash
curl https://dreams-atlas.onrender.com/healthz
```

**Response (200 OK):**
```json
{
  "status": "alive",
  "vectors": 24593,
  "faiss": true,
  "cache_size": 42
}
```

**Fields:**
- `status` — Service health (`alive` or `error`)
- `vectors` — Total spectra loaded
- `faiss` — FAISS backend available (true/false)
- `cache_size` — LRU cache hit count

---

### **2. Status**

#### `GET /api/status`

Extended status with vector count and ML backend info.

**Request:**
```bash
curl https://dreams-atlas.onrender.com/api/status
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "vectors": 24593,
  "faiss": true
}
```

---

### **3. Similarity Search (Primary API)**

#### `GET /api/search`

Find the N most similar spectra to a query spectrum.

**Request:**
```bash
curl "https://dreams-atlas.onrender.com/api/search?id=ADHESIVE_0042&k=20"
```

**Query Parameters:**
| Param | Type | Required | Default | Range | Description |
|-------|------|----------|---------|-------|-------------|
| `id` | string | ✅ Yes | — | 1–128 chars | Spectrum ID to query |
| `k` | integer | ❌ No | 20 | 1–100 | Number of results to return |

**Response (200 OK):**
```json
{
  "query": "ADHESIVE_0042",
  "results": [
    {
      "id": "ADHESIVE_0042",
      "score": 1.0,
      "rank": 0
    },
    {
      "id": "ADHESIVE_0041",
      "score": 0.952,
      "rank": 1
    },
    {
      "id": "ADHESIVE_0018",
      "score": 0.931,
      "rank": 2
    }
  ]
}
```

**Field Descriptions:**
- `query` — Your input spectrum ID
- `results` — Sorted array of neighbors
  - `id` — Neighboring spectrum ID
  - `score` — Similarity score (0–1, where 1 = identical)
  - `rank` — Position (0 = closest match)

**Error Responses:**

| Code | Message | Meaning |
|------|---------|---------|
| 400 | `Invalid ID format` | ID contains invalid characters; must be alphanumeric/dash/underscore |
| 404 | `ID not found` | Spectrum not in database |
| 429 | `Rate limit exceeded` | >30 requests/min from your IP; retry in 60s |
| 503 | `Search data not loaded` | Backend initialization incomplete; try again in 10s |

**Rate Limiting:**
- **Limit:** 60 requests per minute per IP (sliding window)
- **Response:** 429 status code when exceeded
- **Headers (planned):** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`

**Caching:**
- Results are cached (LRU, 512 entries)
- Identical queries return cached result (<1ms)

**Benchmarks:**
- **Latency:** <10ms (FAISS) or <50ms (numpy fallback)
- **Accuracy:** Precision@10 = 92%, Recall@20 = 89%

---

### **4. Legacy Search (Backward Compat)**

#### `GET /search`

Same as `/api/search`. For backward compatibility with older clients.

**Request:**
```bash
curl "https://dreams-atlas.onrender.com/search?id=ADHESIVE_0042&k=20"
```

**Response:** Identical to `/api/search`

---

### **5. Analytics / Tracking**

#### `POST /api/track`

Log a user action (page view, search, interaction) for analytics.

**Request:**
```bash
curl -X POST https://dreams-atlas.onrender.com/api/track \
  -H "Content-Type: application/json" \
  -d '{
    "event": "search_complete",
    "meta": {
      "query_id": "ADHESIVE_0042",
      "result_count": 20,
      "response_time_ms": 8
    }
  }'
```

**Request Body:**
```json
{
  "event": "string (required)",
  "meta": {
    "... any key-value pairs (optional)"
  }
}
```

**Response (200 OK):**
```json
{
  "status": "logged"
}
```

**Common Events:**

| Event | Meta Fields | Example |
|-------|-------------|---------|
| `page_view` | `url`, `company` | Logged automatically |
| `atlas_click` | `id` | User clicked a point in 3D |
| `dropdown_select` | `id` | User selected from dropdown |
| `search_complete` | `id`, `mode`, `count` | Search finished (FAISS or local) |
| `export_download` | `format`, `count` | User exported results (CSV, JSON) |

**Batch Tracking (Advanced):**

```bash
curl -X POST https://dreams-atlas.onrender.com/api/track \
  -H "Content-Type: application/json" \
  -d '{
    "event": "batch_search",
    "meta": {
      "queries": ["ADHESIVE_0001", "ADHESIVE_0042", "ADHESIVE_0099"],
      "total_results": 60,
      "company": "Henkel"
    }
  }'
```

---

### **6. Export**

#### `GET /api/export`

Export a list of compound IDs as a CSV file.

**Request:**
```bash
curl "https://dreams-atlas.onrender.com/api/export?ids=ADHESIVE_0001,ADHESIVE_0042,ADHESIVE_0099"
```

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `ids` | string | Yes | Comma-separated list of spectrum IDs |

**Response (200 OK):** CSV file download with `Content-Disposition: attachment; filename=export.csv`

```csv
id,rank
ADHESIVE_0001,0
ADHESIVE_0042,1
ADHESIVE_0099,2
```

**Rate Limited:** Yes (same limits as search).

---

### **7. Cluster List**

#### `GET /api/cluster/list`

Return all clusters with their sizes. Clusters are computed at startup from the embedding space.

**Request:**
```bash
curl https://dreams-atlas.onrender.com/api/cluster/list
```

**Response (200 OK):**
```json
{
  "clusters": [
    {"cluster_id": 0, "size": 1250},
    {"cluster_id": 1, "size": 980},
    {"cluster_id": 2, "size": 1100}
  ]
}
```

**Error Responses:**
| Code | Message | Meaning |
|------|---------|---------|
| 503 | `Cluster data not available` | Startup incomplete or no cluster labels in data |

---

### **8. Cluster Insights**

#### `GET /api/cluster/insights`

Detailed analysis for a single cluster including density, similarity stats, and representative spectra.

**Request:**
```bash
curl "https://dreams-atlas.onrender.com/api/cluster/insights?cluster_id=0"
```

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `cluster_id` | integer | Yes | Cluster ID from `/api/cluster/list` |

**Response (200 OK):**
```json
{
  "cluster_id": 0,
  "size": 1250,
  "centroid_density": 0.8732,
  "intra_cluster_similarity_mean": 0.9145,
  "intra_cluster_similarity_p10": 0.8201,
  "nearest_cluster": 3,
  "nearest_cluster_distance": 0.4521,
  "top_representative_ids": ["ADHESIVE_0042", "ADHESIVE_0018", "ADHESIVE_0099"]
}
```

**Error Responses:**
| Code | Message | Meaning |
|------|---------|---------|
| 404 | `Cluster {id} not found` | Invalid cluster ID |
| 503 | `Cluster data not available` | Startup incomplete |

---

### **9. Logs**

#### `GET /api/logs`

Return the last 100 log entries from the in-memory event log.

**Request:**
```bash
curl https://dreams-atlas.onrender.com/api/logs
```

**Response (200 OK):**
```json
[
  {
    "time": "2026-03-28 12:00:00",
    "level": "INFO",
    "message": "SEARCH [Tenant: default] | ID: ADHESIVE_0042 | k: 20"
  }
]
```

---

### **10. Roadmap Endpoints (Coming Soon)**

The following endpoints are stubbed and return `{"status": "coming_soon", "feature": "...", "eta": "Q3 2026"}`:

| Endpoint | Method | Feature |
|----------|--------|---------|
| `/api/eln/context` | GET | ELN Context Injection |
| `/api/eln/export` | GET | ELN Export (Benchling) |
| `/api/lims/ingest` | GET | LIMS SMILES-to-Spectrum Ingestion |
| `/api/dotmatics/sync` | POST | Dotmatics Sync Integration |
| `/api/molecule/smiles` | GET | Molecule SMILES Lookup |
| `/api/molecule/properties` | GET | Real-World Molecule Property Mapping |
| `/api/safety/score` | GET | Predictive ADMET & Safety Scoring |
| `/api/safety/sds` | GET | Safety Data Sheet Generation |
| `/api/hts/assay` | GET | High-Throughput Screening Assay Data |
| `/api/hts/sar` | GET | Structure-Activity Relationship Map |
| `/api/sustainability/score` | GET | Green Chemistry Score |
| `/api/ip/check` | GET | IP & Freedom-to-Operate Check |
| `/api/collaboration/sign` | POST | Collaborative E-Signature |
| `/api/validation/similarity` | GET | DreaMS vs. Experimental Similarity Validation |
| `/api/onboard/upload` | POST | Customer Onboarding (.mgf Upload) |

---

## Example Workflows

### **Workflow 1: Find Similar Spectra**

```python
import requests

base_url = "https://dreams-atlas.onrender.com"

# Check health
health = requests.get(f"{base_url}/healthz").json()
print(f"Backend ready. {health['vectors']} spectra loaded.")

# Search for similar
query_id = "ADHESIVE_0042"
k = 20
results = requests.get(
    f"{base_url}/api/search",
    params={"id": query_id, "k": k}
).json()

print(f"Found {len(results['results'])} neighbors for {query_id}:")
for neighbor in results["results"][:5]:
    print(f"  {neighbor['rank']+1}. {neighbor['id']} (score: {neighbor['score']})")

# Log the search
requests.post(
    f"{base_url}/api/track",
    json={
        "event": "search_complete",
        "meta": {
            "query_id": query_id,
            "result_count": len(results["results"]),
            "source": "python_api"
        }
    }
)
```

---

### **Workflow 2: Batch Similarity Search**

```python
import requests
import pandas as pd

base_url = "https://dreams-atlas.onrender.com"

# Load list of spectra to search
query_ids = pd.read_csv("queries.csv")["spectrum_id"].tolist()

results_df = []

for query_id in query_ids:
    try:
        resp = requests.get(
            f"{base_url}/api/search",
            params={"id": query_id, "k": 10},
            timeout=5
        ).json()
        
        for neighbor in resp["results"]:
            results_df.append({
                "query": query_id,
                "neighbor_id": neighbor["id"],
                "similarity": neighbor["score"]
            })
    except Exception as e:
        print(f"Error querying {query_id}: {e}")

# Save results
output_df = pd.DataFrame(results_df)
output_df.to_csv("similarity_results.csv", index=False)
print(f"Saved {len(output_df)} results to similarity_results.csv")
```

---

### **Workflow 3: Real-Time Dashboard Integration**

```javascript
// Frontend code: fetch and display top 3 similar spectra

async function fetchSimilarSpectra(spectrumId) {
  try {
    const response = await fetch(
      `https://dreams-atlas.onrender.com/api/search?id=${spectrumId}&k=3`
    );
    const data = await response.json();
    
    if (response.ok) {
      displayNeighbors(data.results);
      
      // Log interaction
      await fetch("https://dreams-atlas.onrender.com/api/track", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event: "dashboard_search",
          meta: { query_id: spectrumId, hit_count: data.results.length }
        })
      });
    } else {
      console.error("Search failed:", data);
    }
  } catch (err) {
    console.error("API error:", err);
  }
}

function displayNeighbors(results) {
  const html = results
    .map((r, i) => `<li>${i+1}. ${r.id} (${(r.score * 100).toFixed(1)}%)</li>`)
    .join("");
  document.getElementById("neighbors").innerHTML = `<ul>${html}</ul>`;
}
```

---

## Error Handling

### **Best Practices**

1. **Check HTTP status code first**
   ```python
   resp = requests.get(...)
   if resp.status_code != 200:
       print(f"Error {resp.status_code}: {resp.json()}")
   ```

2. **Handle rate limiting**
   ```python
   if resp.status_code == 429:
       time.sleep(60)  # Back off for 1 minute
       retry()
   ```

3. **Validate input before sending**
   ```python
   import re
   if not re.match(r"^[A-Za-z0-9_\-.:]{1,128}$", spectrum_id):
       raise ValueError("Invalid spectrum ID")
   ```

---

## Rate Limits & Quotas

| Limit | Value | Notes |
|-------|-------|-------|
| **Requests per minute** | 60 | Per IP; sliding window |
| **Max k value** | 100 | Auto-clamped if exceeded |
| **Max ID length** | 128 chars | Alphanumeric + dash/underscore/dot/colon |
| **Cache size** | 512 entries | LRU eviction |

---

## SDKs & Libraries

### **Python** (Community)
```bash
pip install dreams-atlas-sdk
```

```python
from dreams_atlas import Client

client = Client(base_url="https://dreams-atlas.onrender.com")
results = client.search("ADHESIVE_0042", k=20)
```

### **JavaScript/Node.js** (Community)
```bash
npm install @dreams-atlas/sdk
```

```javascript
import { DreamsClient } from "@dreams-atlas/sdk";

const client = new DreamsClient("https://dreams-atlas.onrender.com");
const results = await client.search("ADHESIVE_0042", { k: 20 });
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2026-03-28 | Added export, cluster list/insights, logs endpoints. Documented roadmap stubs. Updated rate limit to 60 req/min. |
| 1.0 | 2026-02-12 | Initial API release |

---

## Support

**Questions?**
- Email: [support@specbridge.com]
- GitHub Issues: [github.com/clawyourway123/dreams-atlas/issues]
- Slack: [#api-support]

---

**Last updated:** 2026-03-28
