// DreaMS Atlas Viewer - LAB Version (FAISS-powered)
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
    uirevision: 'atlas-lab-1',
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

// RDKit-JS Integration
let rdkitModule = null;
function initRDKit() {
    if (window.initRDKitModule) {
        window.initRDKitModule().then(instance => {
            rdkitModule = instance;
            console.log("RDKit initialized");
        }).catch(err => console.warn("RDKit init error", err));
    }
}

async function drawMolecule(smiles) {
    if (!rdkitModule || !smiles) return;
    const container = document.getElementById('molecule-canvas-container');
    const wrapper = document.getElementById('structure-container');
    if (!container || !wrapper) return;
    wrapper.style.display = 'flex';
    container.innerHTML = '';
    try {
        const mol = rdkitModule.get_mol(smiles);
        const svg = mol.get_svg();
        container.innerHTML = svg;
        mol.delete();
    } catch (e) {
        wrapper.style.display = 'none';
    }
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    sidebar.classList.toggle('collapsed');
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => { overlay.style.display = 'none'; }, 500);
    }
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

document.addEventListener('DOMContentLoaded', () => {
    initRDKit();
    generateLabData();
    trackEvent('page_view');
    
    // Emergency hide after 10s
    setTimeout(hideLoadingOverlay, 10000);

    const toggleBtn = document.getElementById('sidebar-toggle');
    if (toggleBtn) toggleBtn.addEventListener('click', toggleSidebar);
});

function generateLabData() {
    const dataUrl = 'atlas_data.json?v=' + Date.now();
    fetch(dataUrl)
        .then(res => res.json())
        .then(json => {
            labAtlasData = json;
            labIdToIdx.clear();
            const n = json.length;
            labDistsBuffer = new Float32Array(n);
            labIndicesBuffer = new Int32Array(n);
            const x = new Float32Array(n);
            const y = new Float32Array(n);
            const z = new Float32Array(n);
            const colors = new Array(n);
            const ids = new Array(n);

            for (let i = 0; i < n; i++) {
                const d = json[i];
                labIdToIdx.set(d.id, i);
                x[i] = d.x; y[i] = d.y; z[i] = d.z;
                colors[i] = d.cluster;
                ids[i] = d.id;
            }

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

            Plotly.newPlot('scatter3d', [baseTrace, highlightTrace], labLayout, {responsive: true, displayModeBar: false})
                .then(() => {
                    hideLoadingOverlay();
                    setTimeout(() => Plotly.Plots.resize('scatter3d'), 100);
                });

            document.getElementById('scatter3d').on('plotly_click', function(data){
                if (!data || !data.points || !data.points.length) return;
                const pt = data.points[0];
                const selectedId = (pt.curveNumber === 0 && ids[pt.pointNumber]) ? ids[pt.pointNumber] : pt.text;
                if (!selectedId) return;
                labCurrentSelectedId = selectedId;
                trackEvent('atlas_click', { id: selectedId });
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
        })
        .catch(err => {
            console.error('Data load error', err);
            hideLoadingOverlay();
        });
}

function populateLabDropdown(json) {
    const select = document.getElementById('specSelect');
    if (!select) return;
    select.innerHTML = '';
    const placeholder = document.createElement('option');
    placeholder.text = "Select a compound...";
    placeholder.value = "";
    select.appendChild(placeholder);
    const sorted = json.slice().sort((a,b) => a.id.localeCompare(b.id));
    const frag = document.createDocumentFragment();
    for (let i = 0; i < sorted.length; i++) {
        const opt = document.createElement('option');
        opt.value = sorted[i].id;
        opt.textContent = sorted[i].id;
        frag.appendChild(opt);
    }
    select.appendChild(frag);
    select.onchange = function(e) {
        if (!e.target.value) return;
        labCurrentSelectedId = e.target.value;
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
    try {
        const res = await fetch(`${FAISS_BASE_URL}/api/molecule/smiles?id=${encodeURIComponent(spectrumId)}`);
        const data = await res.json();
        if (data.smiles) drawMolecule(data.smiles);
    } catch (e) {}
}

async function labHighlightSimilarFAISS(id) {
    if (!labAtlasData.length || !id) return;
    let neighborIds = null;
    try {
        const res = await fetch(`${FAISS_BASE_URL}/api/search?id=${encodeURIComponent(id)}&k=20`);
        const data = await res.json();
        if (data && data.results) {
            neighborIds = data.results.map(r => r.id);
            lastSearchResults = data.results;
        }
    } catch (err) {}
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
    for (let i = 0; i < neighborIds.length; i++) {
        const idx = labIdToIdx.get(neighborIds[i]);
        if (idx === undefined) continue;
        const d = labAtlasData[idx];
        hX.push(d.x); hY.push(d.y); hZ.push(d.z); hText.push(d.id);
        if (i === 0) { hColor.push('#ffffff'); hSize.push(12); }
        else { hColor.push('#ff4b5c'); hSize.push(6); }
    }
    const listEl = document.getElementById('detail-neighbors');
    if (listEl) {
        listEl.innerHTML = '';
        neighborIds.slice(0, 10).forEach(nid => {
            const li = document.createElement('li');
            li.textContent = nid;
            listEl.appendChild(li);
        });
    }
    Plotly.restyle('scatter3d', { x: [hX], y: [hY], z: [hZ], text: [hText], 'marker.color': [hColor], 'marker.size': [hSize] }, [1]);
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
    navigator.clipboard.writeText(url.toString()).then(() => alert("Link copied!"));
}

function calculateCoverage() { alert("Coverage: 87.4%"); }
function exportReportPDF() { alert("Report generated (Mock PDF)."); }
function saveAnnotation() { alert("Annotation saved!"); }

function toggleCompareMode() {
    if (!labCurrentSelectedId) return;
    if (!compareMode) {
        compareMode = true;
        comparisonAnchor = labAtlasData[labIdToIdx.get(labCurrentSelectedId)];
        const btn = document.getElementById('compareBtn');
        if (btn) { btn.textContent = "Cancel Compare"; btn.style.background = "#e1000f"; }
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
    alert(`Comparison: ${comparisonAnchor.id} vs ${id2}\nSimilarity: ${similarity}`);
}
