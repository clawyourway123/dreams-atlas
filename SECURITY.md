# DreaMS Atlas Security

## Threat Model

### Assets
- **Spectral embeddings** -- Proprietary chemical fingerprints stored in `embeddings_checkpoint.npy` and `atlas_data.json`.
- **Tenant data** -- Per-customer vault directories containing isolated embeddings and indices.
- **API keys** -- Stored in `config/api_keys.json` (not committed to version control).
- **ML models** -- Trained classifiers in `model_output/` (trade-secret IP).

### Trust Boundaries
1. **Internet -> FastAPI**: All external traffic enters through the FastAPI application. Rate limiting and input validation are applied at this boundary.
2. **Default tenant -> Tenant-specific data**: API key authentication determines tenant routing. Without a valid key, requests fall through to the default (public) dataset.
3. **Static file serving -> Filesystem**: The catch-all route serves files from the project root. A denylist blocks `config/`, `vault/`, and `memory/` directories.

### Threat Categories

| Threat | Mitigation | Status |
|--------|-----------|--------|
| **Brute-force search enumeration** | Rate limiter: 60 req/min per IP, sliding window | Active |
| **Input injection via spectrum IDs** | Regex validation (`_SAFE_ID_RE`), max 256 chars | Active |
| **Path traversal via static file serving** | `resolve()` + `startswith(PROJECT_ROOT)` check; denylist for sensitive dirs | Active |
| **Tenant data leakage** | API key middleware binds tenant; key-bound tenant overrides query param | Active |
| **API key exposure** | Keys loaded from `config/api_keys.json` (gitignored); Bearer token or query param auth | Active |
| **Denial of service** | Rate limiting + GZip minimum size threshold (1000 bytes) | Partial |
| **CORS abuse** | Currently `allow_origins=["*"]` for MVP -- should be restricted in production | Known risk |
| **Missing HTTPS enforcement** | Handled at Render infrastructure level (automatic TLS) | Active |
| **Session/auth token exposure** | SSO callback is a mock endpoint -- no real tokens issued | N/A (roadmap) |

## Security Assumptions

1. **Render provides TLS termination** -- The application does not handle HTTPS itself.
2. **Single-worker uvicorn** -- The LRU cache and rate limiter are not thread-safe across workers. This is acceptable for the current single-process deployment.
3. **No secrets in repository** -- API keys, vault data, and configuration are loaded at runtime from paths outside version control.
4. **FAISS indices are read-only** -- No write path exists from the API to modify embeddings or indices.

## Sensitive Directories

These directories must never be served as static files or committed to version control:

| Directory | Contents | Protection |
|-----------|---------|------------|
| `config/` | API keys JSON | Static file denylist |
| `vault/` | Per-tenant embeddings and data | Static file denylist |
| `memory/` | Application memory/state | Static file denylist |
| `model_output/` | Trained ML models | Not denied (consider adding) |

## Incident Response

### Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| **P1 Critical** | Data breach, tenant isolation failure | Immediate | Vault data served via static route |
| **P2 High** | Authentication bypass, unauthorized access | < 1 hour | API key validation bypassed |
| **P3 Medium** | Rate limit bypass, cache poisoning | < 4 hours | IP spoofing to bypass rate limiter |
| **P4 Low** | Information disclosure via error messages | < 24 hours | Stack trace in 500 response |

### Response Procedures

1. **Detection**: Monitor `event_log` (in-memory, last 100 entries) and Render deployment logs.
2. **Containment**: Rotate compromised API keys by updating `config/api_keys.json` and restarting the service.
3. **Eradication**: For path traversal or static file exposure -- add the offending path to `_STATIC_DENYLIST` and redeploy.
4. **Recovery**: Verify tenant isolation by running search queries with different API keys and confirming result sets are disjoint.
5. **Post-incident**: Document findings, update this threat model, and add regression tests to `backend/tests/`.

### Key Contacts

- Engineering: hello@gstack.ai
- Security issues: file via GitHub Issues (private disclosure preferred)

## Recommendations

1. **Restrict CORS origins** to the production frontend domain instead of `allow_origins=["*"]`.
2. **Add `model_output/` to the static file denylist** to prevent serving trained models.
3. **Implement structured logging** with log levels and correlation IDs for audit trails.
4. **Add rate limit response headers** (`X-RateLimit-Remaining`, `Retry-After`) for client visibility.
5. **Consider API key hashing** -- store hashed keys in `api_keys.json` instead of plaintext.
