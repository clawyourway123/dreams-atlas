# Demo Pre-Call Checklist

**Do this 5 minutes before every sales call.**
Render free tier spins down after inactivity. The first request takes ~60 s. Do not let the buyer see a blank screen.

---

## 1 — Warm up the URL (2 min before call)

Open this in a browser tab and wait for it to load fully:

```
https://dreams-atlas.onrender.com
```

You'll know it's ready when the search bar appears and the atlas tiles are visible.
If the page is blank after 30 s, refresh once — Render is waking up. Wait another 30 s.

Verify health:

```
https://dreams-atlas.onrender.com/healthz
```

Expected response: `{"status":"alive","vectors":...,"faiss":true}`

---

## 2 — Test one search

In the search bar, type a compound ID (e.g. `Henkel-001` or any ID from `atlas_data.json`).
Confirm results appear within 2 s.

---

## 3 — Verify CSV export

From the search results, click **Export CSV** (or hit the export button).
Confirm a `.csv` file downloads with `id` and `rank` columns.

---

## 4 — Open the Henkel demo page

Navigate to:

```
https://dreams-atlas.onrender.com/examples/branded-demos/henkel_demo.html
```

Confirm the Henkel-branded atlas loads and the sidebar shows compound details.

---

## 5 — Sanity-check the API status

```
https://dreams-atlas.onrender.com/api/status
```

Expected: `{"status":"ok","vectors":...}`

---

## If anything fails

1. Hard-refresh the page (`Cmd+Shift+R` / `Ctrl+Shift+R`)
2. Run the keep-alive script locally: `bash scripts/keepalive.sh`
3. Check Render dashboard for deploy errors
4. If still broken, delay the call — do not demo a broken product

---

## Quick manual smoke test (CLI)

```bash
DEMO_URL=https://dreams-atlas.onrender.com pytest backend/tests/test_live.py -v
```
