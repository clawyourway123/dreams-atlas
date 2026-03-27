# DreaMS Atlas

Interactive 3D chemical space explorer powered by FAISS similarity search.

---

## Running a demo

**Option A — Docker (recommended, no Python required):**

```bash
docker compose up
```

Open **http://localhost:8000** when you see the server log line. That's it.

**Option B — Python (no Docker required):**

```bash
./demo-start.sh
```

Open **http://localhost:8000** when the script prints the URL.

> Requires Python 3.10+. Dependencies are installed automatically on first run.

---

## What's included

- 10,000 synthetic spectra loaded from `atlas_data.json`
- FAISS-powered similarity search (`faiss-cpu` with numpy fallback)
- FastAPI backend serving the 3D explorer frontend on port 8000

## Deploying to production

See [DEPLOYMENT.md](./DEPLOYMENT.md) and [render.yaml](./render.yaml) for cloud deployment.
