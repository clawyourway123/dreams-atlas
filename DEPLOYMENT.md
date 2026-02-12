# DreaMS Atlas — Deployment Guide

Complete guide for deploying DreaMS Atlas to production, staging, and local development.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub (Source)                      │
│              clawyourway123/dreams-atlas                 │
└──────────────────────────┬──────────────────────────────┘
                           │
                    push to main
                           │
┌──────────────────────────▼──────────────────────────────┐
│              GitHub Actions (CI/CD)                      │
│  • Lint backend (flake8)                                │
│  • Run tests (pytest)                                   │
│  • Security scan (Trivy)                                │
│  • Trigger Render deployment                            │
└──────────────────────────┬──────────────────────────────┘
                           │
                  if all checks pass
                           │
┌──────────────────────────▼──────────────────────────────┐
│           Render (Production Hosting)                   │
│  • Python 3.10, uvicorn, FastAPI                        │
│  • URL: https://dreams-atlas.onrender.com              │
│  • Auto-restart on config change                        │
│  • Free tier (can upgrade to paid)                      │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### **Local Development**

```bash
# Required
- Python 3.10+
- Node.js 18+
- Git
- Render CLI (optional): brew install render

# Optional
- Docker (for containerized deployment)
- AWS/Azure CLI (for advanced deployments)
```

### **Credentials & Keys**

| Credential | Where to Find | Used For |
|-----------|---------------|----------|
| `RENDER_API_KEY` | Render dashboard → Account Settings → API Keys | Triggering deployments |
| `GITHUB_TOKEN` | GitHub → Settings → Personal access tokens | CI/CD GitHub API calls |
| `SLACK_WEBHOOK_URL` | Slack workspace → Apps → Incoming Webhooks | Deployment notifications |

---

## Local Development Setup

### **1. Clone & Install**

```bash
git clone https://github.com/clawyourway123/dreams-atlas.git
cd dreams-atlas

# Python backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

pip install -r backend/requirements.txt
pip install pytest flake8  # Dev tools
```

### **2. Load Data**

```bash
# Option A: Use existing atlas_data.json (included)
# The server will auto-generate mock embeddings if needed

# Option B: Use your own spectra data
# Place atlas_data.json in project root, following this format:
cat > sample_data.json << 'EOF'
[
  {"id": "SPECTRUM_001", "x": 0.1, "y": 0.2, "z": 0.3, "cluster": 1},
  {"id": "SPECTRUM_002", "x": 0.15, "y": 0.25, "z": 0.35, "cluster": 1}
]
EOF
```

### **3. Run Locally**

```bash
# Start backend
cd backend
export PORT=8000
python -m uvicorn server:app --reload --host 0.0.0.0 --port $PORT

# In another terminal, open browser
open http://localhost:8000
```

---

## Render Deployment

### **First-Time Setup**

```bash
# 1. Create Render account (free tier available)
# 2. Connect GitHub: Dashboard → GitHub → Authorize

# 3. Create new Web Service
# Via dashboard:
#   - Repository: clawyourway123/dreams-atlas
#   - Branch: main
#   - Runtime: Python 3.10
#   - Build command: pip install -r backend/requirements.txt
#   - Start command: uvicorn backend.server:app --host 0.0.0.0 --port $PORT
#   - Plan: Free (or Starter for production)

# 4. Add environment variables (if needed)
# Environment: select "Production"
# Add any secrets here (API keys, etc.)

# 5. Deploy
# Push to main: git push origin main
# Render auto-deploys (watch dashboard for status)
```

### **Via Render CLI** (Advanced)

```bash
# Install
brew install render  # macOS
# or: npm install -g @render/cli

# Login
render login

# Create service
render service create \
  --name dreams-atlas \
  --github-repo clawyourway123/dreams-atlas \
  --github-branch main \
  --runtime python-3-10 \
  --build-cmd "pip install -r backend/requirements.txt" \
  --start-cmd "uvicorn backend.server:app --host 0.0.0.0 --port \$PORT" \
  --plan free

# Deploy
git push origin main  # Auto-deploys on Render
```

### **Monitor Deployments**

```bash
# Check status via API
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv-d65lbihr0fns73d5j0kg

# View recent deploys
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv-d65lbihr0fns73d5j0kg/deploys?limit=5

# Tail logs
render logs --service dreams-atlas
```

### **Troubleshooting**

| Error | Cause | Fix |
|-------|-------|-----|
| **502 Bad Gateway** | Backend not starting | Check logs; verify Python version, dependencies |
| **Build timeout** | Takes >30 min to install deps | Remove heavy deps (e.g., `faiss-cpu`); use numpy fallback |
| **Out of memory** | Free tier limit (512 MB) | Upgrade to Starter plan or optimize code |
| **Static files 404** | Path traversal issue | Ensure `PROJECT_ROOT` is set correctly in `server.py` |

---

## GitHub Actions CI/CD

### **Workflow Triggers**

- **Push to main/develop:** Run tests, deploy to Render (if main)
- **Pull request:** Run tests, security scan, but don't deploy
- **Manual trigger:** Via GitHub Actions UI (future enhancement)

### **Workflow Jobs**

1. **test** — Lint & unit tests
   - Flake8 (Python linting)
   - Pytest (unit tests)
   - ESLint (JavaScript linting)
   - HTML validation

2. **security-scan** — Trivy container & config scan
   - Detects vulnerabilities in dependencies
   - Uploads to GitHub Security tab

3. **deploy** — Trigger Render deployment
   - Only runs if tests pass & branch is main
   - Waits for Render to report deployment
   - Health check: curl `/healthz` endpoint

4. **notify** — Slack notification on success/failure
   - Sends message to `#deployments` channel
   - Includes commit hash and author

### **Setup GitHub Secrets**

```bash
# In GitHub repo → Settings → Secrets and variables → Actions

# Add these:
RENDER_API_KEY = rnd_gzPPiowyKUUS7HJg7JFFaOwH0cp9
SLACK_WEBHOOK_URL = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### **View Workflow Status**

```bash
# GitHub CLI
gh run list --repo clawyourway123/dreams-atlas
gh run view <run-id> --log

# Or: https://github.com/clawyourway123/dreams-atlas/actions
```

---

## Docker Deployment (Optional)

### **Build Docker Image**

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Build & Run**

```bash
# Build
docker build -t dreams-atlas:latest .

# Run locally
docker run -p 8000:8000 dreams-atlas:latest

# Push to Docker Hub (if needed)
docker tag dreams-atlas:latest yourusername/dreams-atlas:latest
docker push yourusername/dreams-atlas:latest
```

---

## Staging Environment

### **Option A: Render (Separate Service)**

```bash
# Create staging service
# Via dashboard: New Web Service → same repo, branch=develop

# Result: https://dreams-atlas-staging.onrender.com
# Push to develop → auto-deploys to staging
```

### **Option B: Local Staging**

```bash
# Use Docker locally
docker run -e ENVIRONMENT=staging \
  -e PORT=8001 \
  -p 8001:8001 \
  dreams-atlas:latest

# Access: http://localhost:8001
```

---

## Data Backups

### **Backup Strategy**

Since DreaMS is stateless (data is read-only), backups focus on:
- `atlas_data.json` (spectra metadata)
- Deployment config (render.yaml)
- Source code (GitHub auto-backs up)

### **Backup Automation**

```bash
# Backup script (run daily via cron)
#!/bin/bash

BACKUP_DIR="$HOME/dreams-atlas-backups"
DATE=$(date +%Y-%m-%d)

mkdir -p $BACKUP_DIR

# Backup config
cp render.yaml $BACKUP_DIR/render.yaml.$DATE

# Backup data
cp atlas_data.json $BACKUP_DIR/atlas_data.json.$DATE

# Compress
tar -czf $BACKUP_DIR/backup-$DATE.tar.gz \
  backend/requirements.txt \
  render.yaml \
  atlas_data.json

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup-$DATE.tar.gz s3://your-bucket/

# Cleanup (keep last 30 days)
find $BACKUP_DIR -type f -mtime +30 -delete

echo "✅ Backup completed: $BACKUP_DIR/backup-$DATE.tar.gz"
```

### **Cron Schedule**

```bash
# Run backup daily at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/dreams-atlas-backup.log 2>&1
```

---

## Monitoring & Alerts

### **Health Checks**

```bash
# Render auto-performs health checks
# Endpoint: GET /healthz
# Expected response: {"status": "alive", "vectors": 24593, ...}

# Manual check
curl https://dreams-atlas.onrender.com/healthz
```

### **Uptime Monitoring** (Optional)

```bash
# Using UptimeRobot (free tier)
# 1. Create monitor: https://dreams-atlas.onrender.com/healthz
# 2. Alert on failure (email/Slack)

# Or: Use Render's built-in monitoring
# Dashboard → Service → Metrics
```

### **Alerts Setup**

```bash
# Create Slack alert for deployment failures
# In GitHub Actions workflow, already configured in notify job

# View alerts: Slack #deployments channel
```

---

## Rollback Procedure

### **If Deployment Fails**

```bash
# Option 1: Render UI
# Dashboard → Service → Deployments → Select previous version → Redeploy

# Option 2: Via API
curl -X POST https://api.render.com/v1/services/srv-d65lbihr0fns73d5j0kg/deploys \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -d '{}' \
  # This triggers a new deployment of current main branch

# Option 3: Revert commit & push
git revert <bad-commit>
git push origin main  # GitHub Actions auto-deploys
```

---

## Security Checklist

- [x] API validates input (regex-based ID sanitization)
- [x] Rate limiting: 30 req/min per IP
- [x] CORS enabled (all origins for MVP; restrict later)
- [x] Static files: no `.git` or `.env` exposure
- [x] Logging: all API requests logged for audit
- [x] HTTPS: Render provides free SSL
- [ ] Authentication: Consider adding for production (future)
- [ ] Secrets: Never commit API keys (use .env or GitHub Secrets)

---

## Production Readiness Checklist

- [x] Backend tests passing
- [x] Security scan passing
- [x] Health endpoint responding
- [x] Static files serving correctly
- [x] CORS configured
- [x] Rate limiting active
- [x] Logging enabled
- [ ] Custom domain configured (optional)
- [ ] CDN enabled (optional)
- [ ] Dedicated database (only if scaling beyond MVP)

---

## Scaling for Production

### **If Load Increases**

1. **Upgrade Render plan** (Free → Starter → Standard)
2. **Add caching** (Redis for FAISS results)
3. **Use CDN** (Cloudflare for static assets)
4. **Distribute searches** (multiple workers)

### **If Data Grows**

1. **Sharding:** Partition spectra by cluster
2. **Indexing:** Pre-compute similarities for hot queries
3. **Database:** Move from JSON to PostgreSQL if needed

---

## Support & Questions

- **Render issues:** Render dashboard → Help → Open support ticket
- **GitHub Actions:** Consult official docs
- **Code questions:** Open GitHub issue
- **Email:** [support@specbridge.com]

---

**Last Updated:** 2026-02-12 12:40 AM MST
