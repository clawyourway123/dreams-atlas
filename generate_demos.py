
import os

template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company} Chemical Space Atlas (Enterprise Lab)</title>
    <script>
        // Prevent flash of wrong theme on load
        (function() {
            var saved = localStorage.getItem('dreams-theme');
            if (!saved) saved = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', saved);
        })();
    </script>
    <script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
    <script src="https://unpkg.com/@rdkit/rdkit/dist/RDKit_minimal.js"></script>
    <link rel="stylesheet" href="atlas.css">
    <style>
      .sidebar.collapsed {
        transform: translateX(-320px);
      }
      .sidebar.collapsed ~ .main-view {
        margin-left: 0 !important;
      }
      .details-overlay {
        position: fixed;
        top: 80px;
        right: 20px;
        max-width: 260px;
        z-index: 10;
      }
      #sidebar-toggle.mobile-toggle {
        display: block !important;
      }
      .btn-group {
        display: flex;
        gap: 8px;
        margin-top: 20px;
      }
      .btn-group .btn {
        margin-top: 0;
        flex: 1;
      }
    </style>
</head>
<body>
<div id="loading-overlay">
    <div class="loader" style="display:block"></div>
    <div style="margin-top:10px;color:var(--text-dim);font-size:12px;font-family:'Inter',sans-serif">Loading {company} Atlas (Lab / FAISS)...</div>
</div>

<button class="theme-toggle" aria-label="Toggle dark/light mode" title="Toggle theme">
    <span class="icon-moon">🌙</span>
    <span class="icon-sun">☀️</span>
</button>

<button id="sidebar-toggle" class="mobile-toggle">☰</button>

<div class="sidebar">
    <h1>{company} / Atlas (Lab)</h1>

    <div class="stat-card">
        <div class="stat-val">{spectra_count}</div>
        <div class="stat-label">Proprietary {industry} Mapped</div>
    </div>
    <div class="stat-card">
        <div class="stat-val tooltip" data-tooltip="Facebook AI Similarity Search - an industry-standard library for efficient similarity search of dense vectors.">FAISS</div>
        <div class="stat-label">Backend: dreams-atlas.onrender.com</div>
    </div>

    <h2>Controls</h2>
    <div class="stat-card">
        <label style="font-size: 12px; color: var(--text-dim); display: block; margin-bottom: 5px;">Filter by Property</label>
        <select>
            <option>Viscosity</option>
            <option>Cure Speed</option>
            <option>Shear Strength</option>
            <option>Molecular Weight</option>
        </select>
    </div>

    <h2>Similarity (Lab)</h2>
    <div class="stat-card">
        <label style="font-size: 12px; color: var(--text-dim); display: block; margin-bottom: 5px;">Anchor <span class="tooltip" data-tooltip="Mass spectra represent the 'fingerprint' of a molecule, showing the distribution of ions by mass-to-charge ratio.">Spectrum</span></label>
        <select id="specSelect">
            <option>Loading spectra...</option>
        </select>
        <p style="margin-top:8px; font-size:11px; color:var(--text-dim); line-height:1.4;">
            <span class="tooltip" data-tooltip="High-fidelity mode using the DreaMS foundation model for real-time similarity search.">Lab mode</span>: clicking a point or changing this dropdown will hit the FAISS backend first,
            then fall back to local 3D similarity if needed.
        </p>
    </div>

    <div class="btn-group">
        <button class="btn" onclick="exportResultsAsCSV()">Export CSV</button>
        <button class="btn" id="compareBtn" onclick="toggleCompareMode()" style="background: var(--panel-bg); border: 1px solid var(--border-color); color: var(--text-main);">Compare</button>
        <button class="btn" style="background: var(--panel-bg); border: 1px solid var(--border-color); color: var(--text-main);" onclick="shareView()">Share View</button>
    </div>

    <div class="btn-group" style="margin-top: 8px;">
        <button class="btn" onclick="calculateCoverage()" style="background: #1a1a1a; border-color: #333;">Coverage Map</button>
        <button class="btn" onclick="exportReportPDF()" style="background: #1a1a1a; border-color: #333;">Generate Report</button>
    </div>

    <div style="margin-top: 30px; border-top: 1px solid var(--border-color); padding-top: 20px;">
        <h2>What you're seeing</h2>
        <ul style="font-size: 12px; color: var(--text-dim); padding-left: 15px; line-height: 1.6;">
            <li style="margin-bottom: 8px;"><strong style="color:var(--header-text)">DreaMS Atlas (Lab):</strong> High-fidelity manifold of {company}'s proprietary chemical space.</li>
            <li style="margin-bottom: 8px;"><strong style="color:var(--header-text)">FAISS Similarity:</strong> Real-time neighborhood ranking via the DreaMS foundation model.</li>
            <li style="margin-bottom: 8px;"><strong style="color:var(--header-text)">Strategic Insight:</strong> Built for R&D leaders to identify "<span class="tooltip" data-tooltip="Unexplored regions of chemical space where new, patentable molecules may exist.">white space</span>" for IP protection.</li>
        </ul>
    </div>
</div>

<div class="main-view" id="scatter3d"></div>

<div class="details-overlay">
  <div id="details-panel" class="stat-card" style="display:none; border-top: 1px solid var(--border-color);">
      <label style="font-size: 12px; color: var(--text-dim); display: block; margin-bottom: 5px;">Selected Spectrum</label>
      <div id="detail-id" style="font-weight:bold; color:var(--header-text); word-break:break-all; margin-bottom:5px;"></div>
      <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--text-dim);">
          <span>Cluster: <span id="detail-cluster" style="color:var(--header-text);"></span></span>
      </div>
      <div style="margin-top:5px; font-size:11px; font-family:monospace; color:var(--text-dim);">
          XYZ: <span id="detail-xyz"></span>
      </div>
      <div id="structure-container" style="margin-top:10px; height: 140px; background: white; border-radius: 8px; display: none; align-items: center; justify-content: center; overflow: hidden; border: 1px solid var(--border-color);">
          <div id="molecule-canvas-container" style="width: 100%; height: 100%;"></div>
      </div>
      <div style="margin-top:8px; font-size:11px; color:var(--text-dim);">
          Most similar (top 10):
          <ol id="detail-neighbors" style="margin:4px 0 0; padding-left:16px; max-height:160px; overflow-y:auto; color:var(--text-main)"></ol>
      </div>

      <div id="safety-panel" class="stat-card" style="margin-top:10px; border-top: 1px solid var(--border-color);"></div>
      <div id="hts-panel" class="stat-card" style="margin-top:10px; border-top: 1px solid var(--border-color);"></div>
      <div id="sustainability-panel" class="stat-card" style="margin-top:10px; border-top: 1px solid var(--border-color);"></div>
      <div id="ip-panel" class="stat-card" style="margin-top:10px; border-top: 1px solid var(--border-color);"></div>

      <div style="margin-top: 16px; border-top: 1px solid var(--border-color); padding-top: 12px;">
          <label style="font-size: 11px; color: var(--text-dim); display: block; margin-bottom: 5px;">R&D Annotation</label>
          <textarea id="annotationBox" style="width: 100%; background: var(--bg-body); border: 1px solid var(--border-color); color: var(--text-main); font-size: 11px; border-radius: 4px; padding: 6px; height: 40px; resize: none;" placeholder="Add team note..."></textarea>
          <button class="btn" onclick="saveAnnotation()" style="margin-top: 5px; width: 100%; font-size: 10px; padding: 6px;">Save Note</button>
      </div>
  </div>
</div>

<script src="atlas-viewer-lab.js"></script>
<script>
    // Theme Toggle logic for demo pages
    (function() {
        const toggle = document.querySelector('.theme-toggle');
        const html = document.documentElement;
        
        function setTheme(theme) {
            html.setAttribute('data-theme', theme);
            localStorage.setItem('dreams-theme', theme);
        }

        toggle.addEventListener('click', () => {
            const current = html.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            setTheme(next);
        });
    })();
</script>

</body>
</html>
"""

companies = [
    {"name": "3M", "industry": "Materials", "count": "24,593", "file": "examples/branded-demos/3m_demo.html"},
    {"name": "BASF", "industry": "Chemicals", "count": "18,201", "file": "examples/branded-demos/basf_demo.html"},
    {"name": "Dow", "industry": "Polymers", "count": "15,440", "file": "examples/branded-demos/dow_demo.html"},
    {"name": "DuPont", "industry": "Specialties", "count": "12,982", "file": "examples/branded-demos/dupont_demo.html"},
    {"name": "Evonik", "industry": "Specialties", "count": "9,451", "file": "examples/branded-demos/evonik_demo.html"},
    {"name": "Arkema", "industry": "Advanced Materials", "count": "7,112", "file": "examples/branded-demos/arkema_demo.html"},
    {"name": "Avery Dennison", "industry": "Labels", "count": "5,890", "file": "examples/branded-demos/avery_dennison_demo.html"},
    {"name": "Covestro", "industry": "Polyurethanes", "count": "8,231", "file": "examples/branded-demos/covestro_demo.html"},
    {"name": "PPG", "industry": "Coatings", "count": "14,556", "file": "examples/branded-demos/ppg_demo.html"},
    {"name": "Syensqo", "industry": "Specialty Polymers", "count": "11,023", "file": "examples/branded-demos/syensqo_demo.html"},
    {"name": "AkzoNobel", "industry": "Performance Coatings", "count": "13,445", "file": "examples/branded-demos/akzonobel_demo.html"},
    {"name": "Clariant", "industry": "Care Chemicals", "count": "6,778", "file": "examples/branded-demos/clariant_demo.html"},
    {"name": "Henkel", "industry": "Adhesives", "count": "24,593", "file": "examples/branded-demos/henkel_lab_demo.html"},
]

v = "2.6.5"

for c in companies:
    content = template.replace("{company}", c["name"]).replace("{industry}", c["industry"]).replace("{spectra_count}", c["count"])
    content = content.replace("atlas-viewer-lab.js", f"atlas-viewer-lab.js?v={v}")
    content = content.replace("atlas.css", f"atlas.css?v={v}")
    content = content.replace("RDKit_minimal.js", "RDKit_minimal.js\" async=\"true")
    with open(f"/Users/clawdy/.openclaw/workspace/dreams-atlas/{c['file']}", "w") as f:
        f.write(content)
    print(f"Generated {c['file']}")
