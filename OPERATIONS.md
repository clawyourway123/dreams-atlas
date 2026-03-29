# DreaMS Atlas Operations Runbook

## Deployment

### Production (Render)

The API backend deploys automatically on push to `main` via `render.yaml`.

- **Service:** `dreams-atlas-api` (Python web service, Oregon region, free plan)
- **Build:** `pip install -r backend/requirements.txt`
- **Start:** `uvicorn backend.server:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 75`
- **Health check:** `GET /healthz` (Docker: every 30s, 5s timeout, 3 retries)

The Next.js frontend deploys as a separate service (`dreams-atlas`) from the `dreams-atlas/` subdirectory.

### Local (Docker)

```bash
docker compose up
# Open http://localhost:8000
```

### Local (Python)

```bash
./demo-start.sh
# Open http://localhost:8000
```

## Rollback

### Render

1. Go to the Render dashboard for `dreams-atlas-api`.
2. Navigate to **Deploys** and click **Rollback** on the last known-good deploy.
3. Verify health: `curl https://dreams-atlas.onrender.com/healthz`

### Git-based rollback

```bash
# Identify the last good commit
git log --oneline -10

# Revert the bad commit (creates a new commit, safe for shared branches)
git revert <bad-commit-sha>
git push origin main
```

## Health Monitoring

### Health endpoint

```bash
curl https://dreams-atlas.onrender.com/healthz
# Expected: {"status":"alive","vectors":24593,"faiss":true}
```

Key indicators:
- `status: "alive"` -- server is running
- `vectors > 0` -- data loaded successfully
- `faiss: true` -- FAISS index built (false = numpy fallback, slower but functional)

### Logs endpoint

```bash
curl https://dreams-atlas.onrender.com/api/logs
```

Returns the last 100 in-memory log entries. Useful for quick debugging without Render log access.

### Status endpoint

```bash
curl https://dreams-atlas.onrender.com/api/status
# Expected: {"status":"ok","vectors":24593,"cache":42}
```

- `cache` shows current LRU cache size (max 512).

## Data Recovery

### Embeddings

The embedding checkpoint is stored at `embeddings_checkpoint.npy` (binary numpy array). To regenerate:

1. Ensure `atlas_data.json` is present in the project root.
2. Re-run the embedding generation pipeline (upstream from this repo).
3. Place the new `.npy` file in the project root and redeploy.

### Training data

Source data is `adhesive_spectra_ir_raman_intensities.csv`. To retrain models:

```bash
python train_ir_raman_models.py
# Outputs: model_output/rf_ir_raman_production.joblib
#          model_output/cnn1d_ir_raman.pth
#          model_output/evaluation_report.json
```

### Tenant vault data

Per-tenant data lives in `vault/<tenant_id>/`. Each tenant directory contains:
- `embeddings.npy` -- Tenant-specific embedding vectors
- `atlas_data.json` -- Tenant-specific spectrum metadata

To restore: copy the tenant directory from backup and restart the service.

## Common Issues

### FAISS not available (numpy fallback)

**Symptom:** `/healthz` returns `"faiss": false`; search latency ~50ms instead of <10ms.

**Cause:** `faiss-cpu` failed to install (common on some ARM/Alpine builds).

**Fix:** Ensure the Dockerfile uses `python:3.11.9-slim-bookworm` and `libgomp1` is installed. The service will still function with numpy fallback.

### Data not loaded (503 on search)

**Symptom:** `/api/search` returns 503 "Search data not loaded".

**Cause:** `embeddings_checkpoint.npy` missing or corrupt, or `atlas_data.json` not found.

**Fix:**
1. Check Render logs for `Load error:` messages.
2. Verify the files exist and are not empty.
3. Redeploy or restart the service.

### Rate limit hit (429)

**Symptom:** Clients receive 429 responses.

**Cause:** More than 60 requests/minute from a single IP.

**Fix:** This is expected behavior. Clients should implement exponential backoff. The rate limiter is in-memory and resets on service restart.

### High memory usage

**Symptom:** Service OOM on Render free tier.

**Cause:** Large embedding files or many cached search results.

**Fix:**
1. Reduce LRU cache size in `server.py` (`LRUCache(capacity=256)` instead of 512).
2. Consider downsampling embeddings or upgrading the Render plan.

## Runbook Checklist

### Pre-deployment

- [ ] All tests pass: `pytest backend/tests/ -v`
- [ ] Backend lint clean: `flake8 backend/ --max-line-length=100`
- [ ] Frontend lint clean: `npx eslint atlas-viewer-lab.js`
- [ ] HTML validation: `npx html-validate index.html`
- [ ] Health check responds after local startup

### Post-deployment

- [ ] `/healthz` returns `status: alive` with correct vector count
- [ ] `/api/search?id=ADHESIVE_0001&k=5` returns results
- [ ] `/api/cluster/list` returns cluster data
- [ ] Branded demo pages load at new paths (`/examples/branded-demos/`)
- [ ] Check Render deploy logs for errors
