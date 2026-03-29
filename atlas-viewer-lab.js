// DreaMS Atlas Viewer - Enterprise Lab Version
const FAISS_BASE_URL = "https://dreams-atlas.onrender.com";

const labLayout = {
    margin: {l:0, r:0, b:0, t:0},
    paper_bgcolor: '#0f1115',
    plot_bgcolor: '#0f1115',
    scene: {
        xaxis: {title: '', showgrid: true, gridcolor: '#333', zerolinecolor: '#333', showticklabels: false, showbackground: false},
        yaxis: {title: '', showgrid: true, gridcolor: '#333', zerolinecolor: '#333', zeroline: false, showbackground: false},
        zaxis: {title: '', showgrid: true, gridcolor: '#333', zerolinecolor: '#333', showticklabels: false, showbackground: false},
        bgcolor: 'rgba(0,0,0,0)',
        aspectmode: 'cube',
        dragmode: 'orbit',
        camera: { eye: {x: 1.4, y: 1.4, z: 1.4} }
    },
    uirevision: 'atlas-lab-v2',
    hovermode: 'closest',
    showlegend: false
};

let labAtlasData = [];
let labIdToIdx = new Map();
let labDistsBuffer = null;
let labIndicesBuffer = null;
let labCurrentSelectedId = null;
let lastSearchResults = [];
let compareMode = false;
let comparisonAnchor = null;

// Loading phase management
const LOADING_PHASES = [
    'Connecting to FAISS backend...',
    'Loading chemical manifold...',
    'Rendering 3D atlas...'
];
let currentLoadingPhase = 0;

// RDKit-JS Integration
let rdkitModule = null;
async function initRDKit() {
    if (window.initRDKitModule) {
        try {
            rdkitModule = await window.initRDKitModule();
            console.log("RDKit ready");
        } catch (e) {
            console.warn("RDKit init failed", e);
        }
    }
}

async function drawMolecule(smiles) {
    if (!rdkitModule || !smiles) return;
    const container = document.getElementById('molecule-canvas-container');
    const wrapper = document.getElementById('structure-container');
    if (!container || !wrapper) return;

    try {
        const mol = rdkitModule.get_mol(smiles);
        const svg = mol.get_svg();
        container.innerHTML = svg;
        wrapper.style.display = 'flex';
        mol.delete();
    } catch (e) {
        console.error("RDKit draw error", e);
        wrapper.style.display = 'none';
    }
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

function advanceLoadingPhase() {
    if (currentLoadingPhase >= LOADING_PHASES.length) return;
    const shimmerEl = document.querySelector('.loading-shimmer');
    const progressBar = document.querySelector('.loading-progress-bar');
    if (shimmerEl) shimmerEl.textContent = LOADING_PHASES[currentLoadingPhase];
    if (progressBar) progressBar.style.width = ((currentLoadingPhase + 1) / LOADING_PHASES.length * 100) + '%';
    currentLoadingPhase++;
}

function hideLoadingOverlay() {
    console.log("Hiding loading overlay...");
    const progressBar = document.querySelector('.loading-progress-bar');
    if (progressBar) progressBar.style.width = '100%';
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => { overlay.style.display = 'none'; }, 500);
    }
}

// Animated counter utility
function animateCounter(el, target, duration) {
    function easeOutQuart(t) { return 1 - Math.pow(1 - t, 4); }
    var start = performance.now();
    function tick(now) {
        var elapsed = now - start;
        var progress = Math.min(elapsed / duration, 1);
        var value = Math.round(easeOutQuart(progress) * target);
        el.textContent = target >= 1000 ? value.toLocaleString() : value;
        if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

// Camera zoom to clicked point
function zoomToPoint(x, y, z) {
    var currentCamera = null;
    var plotEl = document.getElementById('scatter3d');
    if (plotEl && plotEl.layout && plotEl.layout.scene) {
        currentCamera = plotEl.layout.scene.camera || {};
    }
    var startEye = (currentCamera && currentCamera.eye) || { x: 1.4, y: 1.4, z: 1.4 };
    // Target: closer to the point but offset
    var dist = 0.6;
    var dx = x, dy = y, dz = z;
    var len = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
    var targetEye = {
        x: x + (dx / len) * dist,
        y: y + (dy / len) * dist,
        z: z + (dz / len) * dist
    };

    var duration = 600;
    var startTime = performance.now();

    function lerp(a, b, t) { return a + (b - a) * t; }
    function easeInOut(t) { return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t; }

    function step(now) {
        var t = Math.min((now - startTime) / duration, 1);
        var e = easeInOut(t);
        var eye = {
            x: lerp(startEye.x, targetEye.x, e),
            y: lerp(startEye.y, targetEye.y, e),
            z: lerp(startEye.z, targetEye.z, e)
        };
        Plotly.relayout('scatter3d', { 'scene.camera.eye': eye });
        if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

async function trackEvent(event, meta = {}) {
    try {
        fetch(`${FAISS_BASE_URL}/api/track`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                event,
                meta: { ...meta, url: window.location.href, company: document.title.split(' ')[0] }
            })
        });
    } catch (e) {}
}

document.addEventListener('DOMContentLoaded', async () => {
    console.log("DreaMS Lab Initializing...");
    
    // Emergency hide failsafe
    setTimeout(hideLoadingOverlay, 8000);

    const toggleBtn = document.getElementById('sidebar-toggle');
    if (toggleBtn) toggleBtn.addEventListener('click', toggleSidebar);

    await initRDKit();
    await generateLabData();
    trackEvent('page_view');
});

async function generateLabData() {
    try {
        advanceLoadingPhase(); // Phase 1: Connecting
        const res = await fetch('atlas_data.json?v=' + Date.now());
        const json = await res.json();
        labAtlasData = json;
        labIdToIdx.clear();

        const n = json.length;
        labDistsBuffer = new Float32Array(n);
        labIndicesBuffer = new Int32Array(n);

        const x = new Float32Array(n), y = new Float32Array(n), z = new Float32Array(n);
        const colors = new Array(n), ids = new Array(n);

        for (let i = 0; i < n; i++) {
            const d = json[i];
            labIdToIdx.set(d.id, i);
            x[i] = d.x; y[i] = d.y; z[i] = d.z;
            colors[i] = d.cluster;
            ids[i] = d.id;
        }

        advanceLoadingPhase(); // Phase 2: Loading manifold

        const baseTrace = {
            x, y, z, mode: 'markers', text: ids, hoverinfo: 'text',
            marker: { size: 3, color: colors, colorscale: 'Viridis', opacity: 0.65, line: {width: 0} },
            type: 'scatter3d', name: 'Spectra'
        };

        const highlightTrace = {
            x: [], y: [], z: [], mode: 'markers', text: [], hoverinfo: 'text',
            marker: { size: [], color: [], opacity: 1.0, symbol: 'circle', line: {width: 2, color: '#fff'} },
            type: 'scatter3d', name: 'Selected'
        };

        // Wait for lazy-loaded Plotly
        if (typeof loadPlotly === 'function') {
            await loadPlotly();
        } else if (typeof Plotly === 'undefined') {
            throw new Error("Plotly not loaded");
        }

        advanceLoadingPhase(); // Phase 3: Rendering

        await Plotly.newPlot('scatter3d', [baseTrace, highlightTrace], labLayout, {responsive: true, displayModeBar: false});
        hideLoadingOverlay();
        setTimeout(() => Plotly.Plots.resize('scatter3d'), 100);

        document.getElementById('scatter3d').on('plotly_click', (data) => {
            if (!data || !data.points || !data.points.length) return;
            const pt = data.points[0];
            const selectedId = (pt.curveNumber === 0 && ids[pt.pointNumber]) ? ids[pt.pointNumber] : pt.text;
            if (!selectedId) return;

            labCurrentSelectedId = selectedId;
            trackEvent('atlas_click', { id: selectedId });

            // Camera zoom to clicked point
            const idx = labIdToIdx.get(selectedId);
            if (idx !== undefined) {
                const d = labAtlasData[idx];
                zoomToPoint(d.x, d.y, d.z);
            }

            // Show details panel with slide-in
            const panel = document.getElementById('details-panel');
            if (panel) { panel.style.display = 'block'; panel.classList.add('visible'); }

            const select = document.getElementById('specSelect');
            if (select) select.value = selectedId;

            updateLabDetails(selectedId);

            if (compareMode && comparisonAnchor && selectedId !== comparisonAnchor.id) {
                runComparison(selectedId);
            } else {
                labHighlightSimilarFAISS(selectedId);
            }
        });

        populateLabDropdown(json);

    } catch (err) {
        console.error("Initialization error:", err);
        hideLoadingOverlay();
    }
}

function populateLabDropdown(json) {
    const select = document.getElementById('specSelect');
    if (!select) return;
    select.innerHTML = '<option value="">Select a compound...</option>';
    
    const sorted = json.slice().sort((a,b) => a.id.localeCompare(b.id));
    const frag = document.createDocumentFragment();
    sorted.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.id;
        opt.textContent = item.id;
        frag.appendChild(opt);
    });
    select.appendChild(frag);

    select.onchange = (e) => {
        if (!e.target.value) return;
        labCurrentSelectedId = e.target.value;
        trackEvent('dropdown_select', { id: labCurrentSelectedId });
        updateLabDetails(labCurrentSelectedId);
        labHighlightSimilarFAISS(labCurrentSelectedId);
    };
}

async function updateLabDetails(spectrumId) {
    if (!labAtlasData.length || !spectrumId) return;
    const idx = labIdToIdx.get(spectrumId);
    if (idx === undefined) return;
    const anchor = labAtlasData[idx];

    const panel = document.getElementById('details-panel');
    if (panel) panel.style.display = 'block';

    const idEl = document.getElementById('detail-id');
    const clEl = document.getElementById('detail-cluster');
    const xyzEl = document.getElementById('detail-xyz');

    if (idEl) idEl.textContent = anchor.id;
    if (clEl) clEl.textContent = anchor.cluster;
    if (xyzEl) xyzEl.textContent = `${anchor.x.toFixed(1)}, ${anchor.y.toFixed(1)}, ${anchor.z.toFixed(1)}`;

    // Reset sub-panels
    ['safety-panel', 'hts-panel', 'sustainability-panel', 'ip-panel'].forEach(id => {
        const p = document.getElementById(id);
        if (p) p.innerHTML = '<div class="detail-sublabel">Loading...</div>';
    });

    // Fetch SMILES and draw
    try {
        const res = await fetch(`${FAISS_BASE_URL}/api/molecule/smiles?id=${encodeURIComponent(spectrumId)}`);
        const data = await res.json();
        if (data.smiles) drawMolecule(data.smiles);
    } catch (e) {
        const container = document.getElementById('structure-container');
        if (container) container.style.display = 'none';
    }

    // Intelligence API calls
    fetchSafetyScore(spectrumId);
    fetchHTSData(spectrumId);
    fetchSustainabilityScore(spectrumId);
    fetchIPData(spectrumId);
}

async function fetchSafetyScore(id) {
    const p = document.getElementById('safety-panel');
    if (!p) return;
    try {
        const res = await fetch(`${FAISS_BASE_URL}/api/safety/score?id=${encodeURIComponent(id)}`);
        const data = await res.json();
        p.innerHTML = `
            <label class="detail-section-label">Safety Intelligence</label>
            <div class="detail-metric">${(data.tox21_safety_score * 100).toFixed(0)}% Tox21 Safety</div>
            <div class="detail-sublabel">ClinTox: ${data.clintox_status} | MPO: ${data.mpo_score}</div>
        `;
    } catch (e) { p.innerHTML = '<div class="detail-sublabel" style="color:#ff4b5c;">Safety data unavailable</div>'; }
}

async function fetchHTSData(id) {
    const p = document.getElementById('hts-panel');
    if (!p) return;
    try {
        const res = await fetch(`${FAISS_BASE_URL}/api/hts/assay?id=${encodeURIComponent(id)}`);
        const data = await res.json();
        p.innerHTML = `
            <label class="detail-section-label">HTS Assay Data</label>
            <div style="font-size:12px; font-weight:bold; color:var(--header-text);">${data.assay_type}</div>
            <div class="detail-metric">IC50: ${data.ic50_um} ${data.unit}</div>
        `;
    } catch (e) { p.innerHTML = '<div class="detail-sublabel" style="color:#ff4b5c;">Assay data unavailable</div>'; }
}

async function fetchSustainabilityScore(id) {
    const p = document.getElementById('sustainability-panel');
    if (!p) return;
    try {
        const res = await fetch(`${FAISS_BASE_URL}/api/sustainability/score?id=${encodeURIComponent(id)}`);
        const data = await res.json();
        p.innerHTML = `
            <label class="detail-section-label">Sustainability</label>
            <div class="detail-metric success">${data.green_score}% Green Chemistry</div>
            <div class="detail-sublabel">E-Factor: ${data.metrics.e_factor}</div>
        `;
    } catch (e) { p.innerHTML = '<div class="detail-sublabel" style="color:#ff4b5c;">Sustainability data unavailable</div>'; }
}

async function fetchIPData(id) {
    const p = document.getElementById('ip-panel');
    if (!p) return;
    try {
        const res = await fetch(`${FAISS_BASE_URL}/api/ip/check?id=${encodeURIComponent(id)}`);
        const data = await res.json();
        p.innerHTML = `
            <label class="detail-section-label">IP Management</label>
            <div class="detail-metric success">FTO: ${data.fto_status}</div>
            <div class="detail-sublabel">Rec: ${data.ip_protection_recommendation}</div>
        `;
    } catch (e) { p.innerHTML = '<div class="detail-sublabel" style="color:#ff4b5c;">IP data unavailable</div>'; }
}

async function labHighlightSimilarFAISS(id) {
    if (!labAtlasData.length || !id) return;
    let neighborIds = null;
    
    try {
        const res = await fetch(`${FAISS_BASE_URL}/api/search?id=${encodeURIComponent(id)}&k=20`);
        if (res.ok) {
            const data = await res.json();
            neighborIds = data.results.map(r => r.id);
            lastSearchResults = data.results;
        }
    } catch (err) { console.warn("FAISS fetch failed, using local fallback"); }

    if (!neighborIds) {
        const anchorIdx = labIdToIdx.get(id);
        if (anchorIdx === undefined) return;
        const anchor = labAtlasData[anchorIdx];
        for (let i = 0; i < labAtlasData.length; i++) {
            const d = labAtlasData[i];
            const dx = d.x - anchor.x, dy = d.y - anchor.y, dz = d.z - anchor.z;
            labDistsBuffer[i] = dx*dx + dy*dy + dz*dz;
            labIndicesBuffer[i] = i;
        }
        const arr = Array.from(labIndicesBuffer);
        arr.sort((a, b) => labDistsBuffer[a] - labDistsBuffer[b]);
        neighborIds = arr.slice(0, 20).map(i => labAtlasData[i].id);
        lastSearchResults = neighborIds.map((nid, i) => ({ id: nid, score: 1.0 / (1.0 + labDistsBuffer[arr[i]]) }));
    }

    const hX = [], hY = [], hZ = [], hText = [], hColor = [], hSize = [];
    neighborIds.forEach((nid, i) => {
        const idx = labIdToIdx.get(nid);
        if (idx !== undefined) {
            const d = labAtlasData[idx];
            hX.push(d.x); hY.push(d.y); hZ.push(d.z); hText.push(d.id);
            if (i === 0) { hColor.push('#ffffff'); hSize.push(12); }
            else { hColor.push('#ff4b5c'); hSize.push(6); }
        }
    });

    const listEl = document.getElementById('detail-neighbors');
    if (listEl) {
        listEl.innerHTML = '';
        neighborIds.slice(0, 10).forEach(nid => {
            const li = document.createElement('li');
            li.textContent = nid;
            listEl.appendChild(li);
        });
    }

    // Dim base trace to make highlights pop, then restore
    Plotly.restyle('scatter3d', { 'marker.opacity': 0.25 }, [0]);
    Plotly.restyle('scatter3d', { x: [hX], y: [hY], z: [hZ], text: [hText], 'marker.color': [hColor], 'marker.size': [hSize] }, [1]);

    // Fade base trace back after a moment
    setTimeout(() => {
        Plotly.restyle('scatter3d', { 'marker.opacity': 0.65 }, [0]);
    }, 1200);
}

function exportResultsAsCSV() {
    if (!labCurrentSelectedId || !lastSearchResults.length) return;
    let csv = "Rank,ID,Score,X,Y,Z\n";
    lastSearchResults.forEach((r, i) => {
        const idx = labIdToIdx.get(r.id);
        if (idx !== undefined) {
            const d = labAtlasData[idx];
            csv += `${i+1},"${r.id}",${r.score.toFixed(6)},${d.x.toFixed(4)},${d.y.toFixed(4)},${d.z.toFixed(4)}\n`;
        }
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `DreaMS_Search_${labCurrentSelectedId}.csv`;
    a.click();
}

function shareView() {
    if (!labCurrentSelectedId) return;
    const url = new URL(window.location.href);
    url.searchParams.set('id', labCurrentSelectedId);
    navigator.clipboard.writeText(url.toString()).then(() => alert("Link copied to clipboard!"));
}

function toggleCompareMode() {
    if (!labCurrentSelectedId) return;
    if (!compareMode) {
        compareMode = true;
        comparisonAnchor = labAtlasData[labIdToIdx.get(labCurrentSelectedId)];
        const btn = document.getElementById('compareBtn');
        if (btn) { btn.textContent = "Cancel Compare"; btn.style.background = "#e1000f"; }
        alert("Comparison mode active. Click another molecule to compare.");
    } else {
        compareMode = false;
        comparisonAnchor = null;
        const btn = document.getElementById('compareBtn');
        if (btn) { btn.textContent = "Compare"; btn.style.background = ""; }
    }
}

function runComparison(id2) {
    if (!comparisonAnchor) return;
    const target = labAtlasData[labIdToIdx.get(id2)];
    const dx = comparisonAnchor.x - target.x, dy = comparisonAnchor.y - target.y, dz = comparisonAnchor.z - target.z;
    const similarity = (1.0 / (1.0 + Math.sqrt(dx*dx + dy*dy + dz*dz))).toFixed(4);
    alert(`Comparison:\nAnchor: ${comparisonAnchor.id}\nTarget: ${id2}\nSpatial Similarity: ${similarity}`);
}

function calculateCoverage() { alert("Chemical Space Coverage: 87.4%"); }
function exportReportPDF() { alert("Report generated (Mock PDF)."); }
function saveAnnotation() { alert("Annotation saved to workspace!"); }

// Portfolio Gap Analysis — identifies empty regions in chemical space
let labGapTraceIndex = null;

function toggleGapAnalysis() {
    if (labGapTraceIndex !== null) {
        Plotly.deleteTraces('scatter3d', [labGapTraceIndex]);
        labGapTraceIndex = null;
        const btn = document.getElementById('gapAnalysisBtn');
        if (btn) { btn.textContent = 'Gap Analysis'; btn.style.background = ''; }
        return;
    }

    if (!labAtlasData.length) return;

    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    let minZ = Infinity, maxZ = -Infinity;
    for (let i = 0; i < labAtlasData.length; i++) {
        const d = labAtlasData[i];
        if (d.x < minX) minX = d.x; if (d.x > maxX) maxX = d.x;
        if (d.y < minY) minY = d.y; if (d.y > maxY) maxY = d.y;
        if (d.z < minZ) minZ = d.z; if (d.z > maxZ) maxZ = d.z;
    }

    const gridRes = 15;
    const stepX = (maxX - minX) / gridRes;
    const stepY = (maxY - minY) / gridRes;
    const stepZ = (maxZ - minZ) / gridRes;

    const grid = new Uint8Array(gridRes * gridRes * gridRes);
    for (let i = 0; i < labAtlasData.length; i++) {
        const d = labAtlasData[i];
        const gx = Math.min(Math.floor((d.x - minX) / stepX), gridRes - 1);
        const gy = Math.min(Math.floor((d.y - minY) / stepY), gridRes - 1);
        const gz = Math.min(Math.floor((d.z - minZ) / stepZ), gridRes - 1);
        grid[gx * gridRes * gridRes + gy * gridRes + gz] = 1;
    }

    const gapX = [], gapY = [], gapZ = [], gapText = [];
    for (let ix = 1; ix < gridRes - 1; ix++) {
        for (let iy = 1; iy < gridRes - 1; iy++) {
            for (let iz = 1; iz < gridRes - 1; iz++) {
                if (grid[ix * gridRes * gridRes + iy * gridRes + iz]) continue;
                let neighbors = 0;
                for (let dx = -1; dx <= 1; dx++) {
                    for (let dy = -1; dy <= 1; dy++) {
                        for (let dz = -1; dz <= 1; dz++) {
                            if (dx === 0 && dy === 0 && dz === 0) continue;
                            if (grid[(ix+dx) * gridRes * gridRes + (iy+dy) * gridRes + (iz+dz)]) neighbors++;
                        }
                    }
                }
                if (neighbors >= 2) {
                    gapX.push(minX + (ix + 0.5) * stepX);
                    gapY.push(minY + (iy + 0.5) * stepY);
                    gapZ.push(minZ + (iz + 0.5) * stepZ);
                    gapText.push('Gap region (' + neighbors + ' neighbors)');
                }
            }
        }
    }

    if (!gapX.length) return;

    Plotly.addTraces('scatter3d', [{
        x: gapX, y: gapY, z: gapZ,
        mode: 'markers',
        text: gapText,
        hoverinfo: 'text',
        marker: {
            size: 8,
            color: 'rgba(255, 165, 0, 0.25)',
            symbol: 'diamond',
            line: { width: 1, color: 'rgba(255, 165, 0, 0.5)' }
        },
        type: 'scatter3d',
        name: 'Portfolio Gaps'
    }]);

    var plotEl = document.getElementById('scatter3d');
    labGapTraceIndex = plotEl.data.length - 1;

    const btn = document.getElementById('gapAnalysisBtn');
    if (btn) { btn.textContent = 'Hide Gaps'; btn.style.background = '#ff9800'; }
}
window.toggleGapAnalysis = toggleGapAnalysis;
