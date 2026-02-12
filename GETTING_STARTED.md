# Getting Started with DreaMS Atlas

Welcome! This guide walks you through exploring your chemical spectra in 3D chemical space—from first login to advanced search.

---

## 1. Access the Platform

### **Option A: Cloud (Managed)**
- Email sent to your team: `https://dreams-atlas.onrender.com`
- Login with your company credentials
- Your spectra data is already imported

### **Option B: Local/On-Premises**
- IT team has deployed DreaMS on your infrastructure
- Access via your internal URL (e.g., `https://dreams.yourcompany.com`)
- Your team is the only user; no shared authentication needed

### **Option C: GitHub (Open-Source)**
- Clone: `git clone https://github.com/clawyourway123/dreams-atlas`
- Follow README for local setup (Python 3.10+, Node.js)
- Load your own spectra data

---

## 2. Your First 5 Minutes

### **Step 1: Open the 3D Explorer**

Navigate to the homepage. You'll see:

```
DreaMS ATLAS: Interactive Chemical Space Explorer

[Loading visualization...]
```

**What you're looking at:**
- **3D Point Cloud:** Each dot = one spectrum from your library
- **Color gradient:** Different chemical clusters (red=one family, blue=another)
- **Mouse controls:** Drag to rotate, scroll to zoom

### **Step 2: Click a Dot**

Click any point in the 3D space. A sidebar appears:

```
━━━━━━━━━━━━━━━━━━━
SPECTRUM DETAILS
━━━━━━━━━━━━━━━━━━━
ID:      ADHESIVE_0042
Cluster: 7 (epoxy-based)
Position: (3.21, -1.45, 0.89)

🔍 SIMILAR SPECTRA (Top 10):
1. ADHESIVE_0041    [score: 0.95]
2. ADHESIVE_0018    [score: 0.93]
3. ADHESIVE_0099    [score: 0.91]
...
```

**What this means:**
- Your clicked spectrum is `ADHESIVE_0042`
- It's in the "epoxy-based" cluster
- The 10 most similar spectra are listed (FAISS similarity search)

### **Step 3: Explore Similar Compounds**

Click any similar spectrum to see *its* neighbors. Watch the 3D view update in real-time:
- **White dot:** Your query (e.g., ADHESIVE_0042)
- **Red dots:** Top 20 similar neighbors
- **Gray dots:** Everything else (background)

---

## 3. Search by ID

### **Find a Specific Spectrum**

Use the **dropdown menu** to search by ID:

```
📋 Select Spectrum:
[Type or search...]

↓ Autocomplete shows:
  • ADHESIVE_0001
  • ADHESIVE_0042  ← (Your previous selection)
  • ADHESIVE_0099
```

Or **paste an ID** directly:

```
🔍 Search:
[ADHESIVE_0042]  [SEARCH]
```

---

## 4. Filter & Refine

### **By Cluster**

**Sidebar dropdown:**
```
Filter by Cluster:
☐ All (showing all 24,593 spectra)
☐ Cluster 0 (polyurethane)  — 2,341 spectra
☐ Cluster 1 (silane-based)  — 1,923 spectra
☑ Cluster 2 (epoxy)         — 3,201 spectra  ← Selected
☐ Cluster 3 (acrylic)       — 2,891 spectra
```

When you select a cluster, the 3D view highlights only those points.

### **By Performance Metrics** (if available)

```
Filters:
  Cure Time: [Min: 0] — [Max: 60] minutes
  Temp Range: [Min: -20] — [Max: 120] °C
  Cost: [Min: $0] — [Max: $100] per liter
  
[APPLY FILTERS]
```

---

## 5. Export & Report

### **Download Results**

Click **"Export Neighbors"** to download a CSV:

```
ID,Similarity_Score,Cluster,Cost,Cure_Time
ADHESIVE_0042,1.00,2,45.50,30
ADHESIVE_0041,0.95,2,42.10,32
ADHESIVE_0018,0.93,2,46.80,28
...
```

Use in Excel, Python, or your LIMS.

### **Share a Link**

Copy the URL:
```
https://dreams-atlas.onrender.com?query=ADHESIVE_0042&k=20
```

Send to a colleague. They'll see the same results (if they have access).

---

## 6. Common Use Cases

### **Use Case 1: Find a Baseline**

*Goal:* Find existing formulations similar to a target spec.

**Steps:**
1. Search for spec ID (e.g., `TARGET_SPEC_001`)
2. View top 10 neighbors
3. Click each to compare formulation details
4. Download CSV of top 20 → send to lab

**Time:** 5 minutes

---

### **Use Case 2: Explore a Cluster**

*Goal:* Understand all "fast-cure epoxy" formulations.

**Steps:**
1. Filter by cluster: "epoxy"
2. Sort by cure time (fastest first)
3. Visually scan the 3D cloud for gaps
4. Click on edge cases (unusual points)
5. Generate report: "Underexplored fast-cure epoxy space"

**Time:** 15 minutes

---

### **Use Case 3: Portfolio Gap Analysis**

*Goal:* Find where to invest R&D effort.

**Steps:**
1. View all spectra (unfiltered 3D cloud)
2. Identify sparse regions (empty 3D space)
3. Click nearby formulations to understand the gap
4. Ask: "What chemistry could fill this gap?"
5. Export neighboring formulations as research starting points

**Time:** 30 minutes

---

## 7. Tips & Tricks

### **Keyboard Shortcuts**

| Key | Action |
|-----|--------|
| `R` | Reset 3D view (home position) |
| `S` | Save screenshot of current view |
| `E` | Export visible spectra as CSV |
| `/` | Open search bar |
| `?` | Show help menu |

### **Mouse Controls**

| Control | Action |
|---------|--------|
| **Drag (left)** | Rotate 3D view |
| **Drag (right)** | Pan (move view) |
| **Scroll** | Zoom in/out |
| **Double-click** | Focus on a point; center it |
| **Hover** | Show tooltip (spectrum ID, cluster) |

### **Performance Tips**

- **Large datasets (100K+)?** Use cluster filters to reduce visual clutter
- **Slow search?** Check your internet; FAISS backend is <10ms, so lag is likely browser
- **Many points overlapping?** Increase point size in settings, or filter by cluster

---

## 8. Advanced: API Access

If you're a developer or data scientist, DreaMS exposes a REST API:

### **Search Endpoint**

```bash
curl "https://dreams-atlas.onrender.com/api/search?id=ADHESIVE_0042&k=20"
```

**Response:**
```json
{
  "query": "ADHESIVE_0042",
  "results": [
    {"id": "ADHESIVE_0041", "score": 0.95, "rank": 1},
    {"id": "ADHESIVE_0018", "score": 0.93", "rank": 2},
    ...
  ]
}
```

### **Analytics Endpoint**

```bash
curl -X POST https://dreams-atlas.onrender.com/api/track \
  -H "Content-Type: application/json" \
  -d '{"event": "custom_search", "meta": {"query_type": "fast_cure"}}'
```

**Use case:** Track which spectra your team searches most often; inform R&D priorities.

---

## 9. Troubleshooting

### **"I clicked a point but nothing happened"**

- Try clicking again (sometimes the 3D renderer is slow)
- Check browser console: `F12` → Console tab → any error messages?
- If persistent, refresh page: `Ctrl+R` or `Cmd+R`

### **"Search is very slow"**

- Likely browser latency, not backend (FAISS is <10ms)
- Try a different browser (Chrome typically fastest)
- If you have 100K+ spectra, filter by cluster first

### **"I don't see my spectra in the 3D view"**

- Confirm your spectra were imported (ask IT/SpecBridge team)
- Check that your login has access to the right dataset
- If using on-premises, verify the data file is present at deployment time

### **"Can I download all spectra as a file?"**

- Yes, but only the similarity results (not raw embeddings)
- Click "Export Neighbors" and repeat for different queries
- For bulk exports, contact SpecBridge team

---

## 10. Next Steps

### **After Your First Week**

- ✅ You've explored the 3D visualization
- ✅ You've searched for similar spectra
- ✅ You've identified useful neighbors

### **Advanced Skills to Learn**

1. **Cluster interpretation:** What does each color group represent chemically?
2. **Gap analysis:** Use 3D view to find whitespace in your portfolio
3. **API integration:** Automate searches from your Python scripts
4. **Custom dashboards:** Work with SpecBridge to build reports for your team

---

## 11. Support & Feedback

### **Got a question?**

- **Quick issue?** Check [FAQ.md](./FAQ.md)
- **Bug report?** Email: [support@specbridge.com]
- **Feature request?** Slack: [#dreams-feedback]
- **Training needed?** Schedule 1-on-1: [calendar link]

### **Want to suggest improvements?**

Open an issue on GitHub: [github.com/clawyourway123/dreams-atlas/issues](https://github.com/clawyourway123/dreams-atlas/issues)

---

*Happy exploring! 🧪✨*

**Generated:** 2026-02-12 12:20 AM MST
