
import os

template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company} Chemical Space Atlas (Enterprise Lab)</title>
    <script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
    <link rel="stylesheet" href="atlas.css">
    <style>
      .sidebar.collapsed {{
        transform: translateX(-320px);
      }}
      .sidebar.collapsed ~ .main-view {{
        margin-left: 0 !important;
      }}
      .details-overlay {{
        position: fixed;
        top: 70px;
        right: 20px;
        max-width: 260px;
        z-index: 10;
      }}
      #sidebar-toggle.mobile-toggle {{
        display: block !important;
      }}
    </style>
</head>
<body>
<div id="loading-overlay">
    <div class="loader" style="display:block"></div>
    <div style="margin-top:10px;color:#888;font-size:12px;font-family:'Inter',sans-serif">Loading {company} Atlas (Lab / FAISS)...</div>
</div>

<button id="sidebar-toggle" class="mobile-toggle">☰</button>

<div class="sidebar">
    <h1>{company} / Atlas (Lab)</h1>

    <div class="stat-card">
        <div class="stat-val">{spectra_count}</div>
        <div class="stat-label">Proprietary {industry} Mapped</div>
    </div>
    <div class="stat-card">
        <div class="stat-val">FAISS</div>
        <div class="stat-label">Backend: dreams-atlas.onrender.com</div>
    </div>

    <h2>Controls</h2>
    <div class="stat-card">
        <label style="font-size: 12px; color: #aaa; display: block; margin-bottom: 5px;">Filter by Property</label>
        <select style="width: 100%; background: #111; color: #fff; border: 1px solid #444; padding: 5px; border-radius: 4px;">
            <option>Viscosity</option>
            <option>Cure Speed</option>
            <option>Shear Strength</option>
            <option>Molecular Weight</option>
        </select>
    </div>

    <h2>Similarity (Lab)</h2>
    <div class="stat-card">
        <label style="font-size: 12px; color: #aaa; display: block; margin-bottom: 5px;">Anchor Spectrum</label>
        <select id="specSelect" style="width: 100%; background: #111; color: #fff; border: 1px solid #444; padding: 5px; border-radius: 4px;">
            <option>Loading spectra...</option>
        </select>
        <p style="margin-top:8px; font-size:11px; color:#888; line-height:1.4;">
            Lab mode: clicking a point or changing this dropdown will hit the FAISS backend first,
            then fall back to local 3D similarity if needed.
        </p>
    </div>

    <div style="margin-top: 30px; border-top: 1px solid #333; padding-top: 20px;">
        <h2>What you're seeing</h2>
        <ul style="font-size: 12px; color: #aaa; padding-left: 15px; line-height: 1.6;">
            <li style="margin-bottom: 8px;"><strong>DreaMS Atlas (Lab):</strong> High-fidelity manifold of {company}'s proprietary chemical space.</li>
            <li style="margin-bottom: 8px;"><strong>FAISS Similarity:</strong> Real-time neighborhood ranking via the DreaMS foundation model.</li>
            <li style="margin-bottom: 8px;"><strong>Strategic Insight:</strong> Built for R&D leaders to identify "white space" for IP protection.</li>
        </ul>
    </div>
</div>

<div class="main-view" id="scatter3d"></div>

<div class="details-overlay">
  <div id="details-panel" class="stat-card" style="display:none; border-top: 1px solid #333;">
      <label style="font-size: 12px; color: #aaa; display: block; margin-bottom: 5px;">Selected Spectrum</label>
      <div id="detail-id" style="font-weight:bold; color:#fff; word-break:break-all; margin-bottom:5px;"></div>
      <div style="display:flex; justify-content:space-between; font-size:12px; color:#aaa;">
          <span>Cluster: <span id="detail-cluster" style="color:#fff;"></span></span>
      </div>
      <div style="margin-top:5px; font-size:11px; font-family:monospace; color:#666;">
          XYZ: <span id="detail-xyz"></span>
      </div>
      <div style="margin-top:8px; font-size:11px; color:#aaa;">
          Most similar (top 10):
          <ol id="detail-neighbors" style="margin:4px 0 0; padding-left:16px; max-height:160px; overflow-y:auto;"></ol>
      </div>
  </div>
</div>

<script src="atlas-viewer-lab.js"></script>

</body>
</html>
"""

companies = [
    {"name": "3M", "industry": "Materials", "count": "24,593", "file": "3m_demo.html"},
    {"name": "BASF", "industry": "Chemicals", "count": "18,201", "file": "basf_demo.html"},
    {"name": "Dow", "industry": "Polymers", "count": "15,440", "file": "dow_demo.html"},
    {"name": "DuPont", "industry": "Specialties", "count": "12,982", "file": "dupont_demo.html"},
    {"name": "Evonik", "industry": "Specialties", "count": "9,451", "file": "evonik_demo.html"},
    {"name": "Arkema", "industry": "Advanced Materials", "count": "7,112", "file": "arkema_demo.html"},
    {"name": "Avery Dennison", "industry": "Labels", "count": "5,890", "file": "avery_dennison_demo.html"},
    {"name": "Covestro", "industry": "Polyurethanes", "count": "8,231", "file": "covestro_demo.html"},
    {"name": "PPG", "industry": "Coatings", "count": "14,556", "file": "ppg_demo.html"},
    {"name": "Syensqo", "industry": "Specialty Polymers", "count": "11,023", "file": "syensqo_demo.html"},
    {"name": "AkzoNobel", "industry": "Performance Coatings", "count": "13,445", "file": "akzonobel_demo.html"},
    {"name": "Clariant", "industry": "Care Chemicals", "count": "6,778", "file": "clariant_demo.html"},
    {"name": "Henkel", "industry": "Adhesives", "count": "24,593", "file": "henkel_lab_demo.html"},
]

for c in companies:
    content = template.format(company=c["name"], industry=c["industry"], spectra_count=c["count"])
    with open(f"/Users/clawdy/.openclaw/workspace/dreams-atlas/{c['file']}", "w") as f:
        f.write(content)
    print(f"Generated {c['file']}")
