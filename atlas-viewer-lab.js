// DreaMS Atlas Viewer - LAB Version (FAISS-powered)
// This is an experimental viewer wired to the FAISS backend on Render.
// It is allowed to be more aggressive than the stable demo, but must not affect henkel_demo.html.

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

// Buffers for client-side fallback
let labDistsBuffer = null;
let labIndicesBuffer = null;

// Track current selection
let labCurrentSelectedId = null;

document.addEventListener('DOMContentLoaded', () => {
    initDetailsPanel(); // reuse from atlas-viewer.js if present; otherwise no-op
    generateLabData();

    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            try { Plotly.Plots.resize('scatter3d'); } catch(e){}
        }, 150);
    });

    const toggleBtn = document.getElementById('sidebar-toggle');
    if (toggleBtn) toggleBtn.addEventListener('click', toggleSidebar);
});

function generateLabData() {
    fetch('atlas_data.json')
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
                x, y, z,
                mode: 'markers',
                text: ids,
                hoverinfo: 'text',
                marker: {
                    size: 3,
                    color: colors,
                    colorscale: 'Viridis',
                    opacity: 0.65,
                    line: {width: 0}
                },
                type: 'scatter3d',
                name: 'Spectra'
            };

            const highlightTrace = {
                x: [], y: [], z: [],
                mode: 'markers', text: [], hoverinfo: 'text',
                marker: {
                    size: [],
                    color: [],
                    opacity: 1.0,
                    symbol: 'circle',
                    line: {width: 2, color: '#fff'}
                },
                type: 'scatter3d',
                name: 'Selected'
            };

            Plotly.newPlot('scatter3d', [baseTrace, highlightTrace], labLayout, {responsive: true, displayModeBar: false})
                .then(() => {
                    hideLoadingOverlay && hideLoadingOverlay();
                    setTimeout(() => Plotly.Plots.resize('scatter3d'), 100);
                });

            // LAB behavior: click selects + immediately runs FAISS search (with fallback)
            document.getElementById('scatter3d').on('plotly_click', function(data){
                if (!data || !data.points || !data.points.length) return;
                const pt = data.points[0];
                const selectedId = (pt.curveNumber === 0 && ids[pt.pointNumber]) ? ids[pt.pointNumber] : pt.text;
                if (!selectedId) return;
                labCurrentSelectedId = selectedId;

                const select = document.getElementById('specSelect');
                if (select) select.value = selectedId;

                updateLabDetails(selectedId);
                labHighlightSimilarFAISS(selectedId);
            });

            populateLabDropdown(json);
        })
        .catch(err => {
            console.error('Lab viewer data load error', err);
            hideLoadingOverlay && hideLoadingOverlay();
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

    const limited = json.slice(0, 1000).sort((a,b) => a.id.localeCompare(b.id));
    const frag = document.createDocumentFragment();
    for (let i = 0; i < limited.length; i++) {
        const opt = document.createElement('option');
        opt.value = limited[i].id;
        opt.textContent = limited[i].id;
        frag.appendChild(opt);
    }
    select.appendChild(frag);

    select.onchange = function(e) {
        if (!e.target.value) return;
        labCurrentSelectedId = e.target.value;
        updateLabDetails(labCurrentSelectedId);
        // In lab mode, changing dropdown can also trigger FAISS search
        labHighlightSimilarFAISS(labCurrentSelectedId);
    };
}

function updateLabDetails(spectrumId) {
    if (!labAtlasData.length || !spectrumId) return;
    const idx = labIdToIdx.get(spectrumId);
    if (idx === undefined) return;
    const anchor = labAtlasData[idx];

    const panel = document.getElementById('details-panel');
    if (!panel) return;
    panel.style.display = 'block';

    const idEl = document.getElementById('detail-id');
    const clEl = document.getElementById('detail-cluster');
    const xyzEl = document.getElementById('detail-xyz');

    if (idEl) idEl.textContent = anchor.id;
    if (clEl) clEl.textContent = anchor.cluster;
    if (xyzEl) xyzEl.textContent = `${anchor.x.toFixed(1)}, ${anchor.y.toFixed(1)}, ${anchor.z.toFixed(1)}`;
}

async function labHighlightSimilarFAISS(id) {
    if (!labAtlasData.length || !id) return;

    let neighborIds = null;

    // 1) Try FAISS backend
    try {
        const res = await fetch(`${FAISS_BASE_URL}/search?id=${encodeURIComponent(id)}&k=20`);
        if (!res.ok) throw new Error('FAISS HTTP ' + res.status);
        const data = await res.json();
        if (data && Array.isArray(data.results) && data.results.length) {
            neighborIds = data.results.map(r => r.id);
        }
    } catch (err) {
        console.warn('FAISS backend failed, falling back to local similarity:', err);
    }

    // 2) Fallback: local 3D distance if backend absent or failed
    if (!neighborIds) {
        const anchorIdx = labIdToIdx.get(id);
        if (anchorIdx === undefined) return;
        const anchor = labAtlasData[anchorIdx];
        const ax = anchor.x, ay = anchor.y, az = anchor.z;

        for (let i = 0; i < labAtlasData.length; i++) {
            const d = labAtlasData[i];
            const dx = d.x - ax, dy = d.y - ay, dz = d.z - az;
            labDistsBuffer[i] = dx*dx + dy*dy + dz*dz;
            labIndicesBuffer[i] = i;
        }
        const arr = Array.from(labIndicesBuffer);
        arr.sort((a, b) => labDistsBuffer[a] - labDistsBuffer[b]);
        neighborIds = arr.slice(0, 20).map(i => labAtlasData[i].id);
    }

    // 3) Build highlight trace data
    const hX = [], hY = [], hZ = [], hText = [], hColor = [], hSize = [];
    for (let i = 0; i < neighborIds.length; i++) {
        const nid = neighborIds[i];
        const idx = labIdToIdx.get(nid);
        if (idx === undefined) continue;
        const d = labAtlasData[idx];
        hX.push(d.x); hY.push(d.y); hZ.push(d.z); hText.push(d.id);
        if (i === 0) { hColor.push('#ffffff'); hSize.push(12); }
        else { hColor.push('#ff4b5c'); hSize.push(6); }
    }

    Plotly.restyle('scatter3d', {
        x: [hX],
        y: [hY],
        z: [hZ],
        text: [hText],
        'marker.color': [hColor],
        'marker.size': [hSize]
    }, [1]);
}
