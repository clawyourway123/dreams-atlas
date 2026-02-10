
// DreaMS Atlas Viewer Logic - Scalable & Cinematic
// Architecture: 
// Trace 0: Base Dataset (Static)
// Trace 1: Highlights (Dynamic Selection)
// Trace 2+: Comparison Datasets (Overlays)

const layout = {
    margin: {l:0, r:0, b:0, t:0},
    paper_bgcolor: '#0f1115',
    plot_bgcolor: '#0f1115',
    scene: {
        xaxis: {title: '', showgrid: true, gridcolor: '#333', zerolinecolor: '#333', showticklabels: false, showbackground: false},
        yaxis: {title: '', showgrid: true, gridcolor: '#333', zerolinecolor: '#333', showticklabels: false, showbackground: false},
        zaxis: {title: '', showgrid: true, gridcolor: '#333', zerolinecolor: '#333', showticklabels: false, showbackground: false},
        bgcolor: 'rgba(0,0,0,0)',
        aspectmode: 'cube',
        dragmode: 'orbit'
    },
    uirevision: 'atlas-1', 
    hovermode: 'closest',
    showlegend: false
};

let atlasData = [];
let idToIdx = new Map();

document.addEventListener('DOMContentLoaded', () => {
    initDetailsPanel();
    initComparisonPanel();
    generateData();
    
    let resizeTimeout;\n    window.addEventListener('resize', () => {\n        clearTimeout(resizeTimeout);\n        resizeTimeout = setTimeout(() => {\n            try { Plotly.Plots.resize('scatter3d'); } catch(e){}\n        }, 150);\n    });

    const toggleBtn = document.getElementById('sidebar-toggle');
    if (toggleBtn) toggleBtn.addEventListener('click', toggleSidebar);
});

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) sidebar.classList.toggle('open');
}
window.toggleSidebar = toggleSidebar; 

function initDetailsPanel() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    if (!document.getElementById('details-panel')) {
        const div = document.createElement('div');
        div.id = 'details-panel';
        div.className = 'stat-card';
        div.style.display = 'none';
        div.style.marginTop = '20px';
        div.style.borderTop = '1px solid #333';
        div.innerHTML = `\n            <label style=\"font-size: 12px; color: #aaa; display: block; margin-bottom: 5px;\">Selected Spectrum</label>\n            <div id=\"detail-id\" style=\"font-weight:bold; color:#fff; word-break:break-all; margin-bottom:5px;\"></div>\n            <div style=\"display:flex; justify-content:space-between; font-size:12px; color:#aaa;\">\n                <span>Cluster: <span id=\"detail-cluster\" style=\"color:#fff;\"></span></span>\n            </div>\n            <div style=\"margin-top:5px; font-size:11px; font-family:monospace; color:#666;\">\n                XYZ: <span id=\"detail-xyz\"></span>\n            </div>\n        `;
        const simSection = Array.from(sidebar.querySelectorAll('h2')).find(h => h.textContent.includes('Similarity'));
        if (simSection && simSection.nextElementSibling) {
             simSection.nextElementSibling.insertAdjacentElement('afterend', div);
        } else {
             sidebar.appendChild(div);
        }
    }
}

function initComparisonPanel() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    const div = document.createElement('div');
    div.innerHTML = `\n        <h2>Infiltration / Compare</h2>\n        <div class=\"stat-card\">\n            <label style=\"font-size: 12px; color: #aaa; display: block; margin-bottom: 5px;\">Overlay Target Map</label>\n            <div style=\"display: flex; gap: 5px;\">\n                <button class=\"btn\" style=\"margin-top:0; padding: 8px; font-size: 11px;\" onclick=\"loadComparison('3M')\">3M</button>\n                <button class=\"btn\" style=\"margin-top:0; padding: 8px; font-size: 11px; background: #004a96;\" onclick=\"loadComparison('BASF')\">BASF</button>\n            </div>\n        </div>\n    `;
    sidebar.appendChild(div);
}

function populateSpectrumDropdown(json) {
    const select = document.getElementById('specSelect');
    if (!select || json.length === 0) return;
    if(select.options.length > 1) return;
    select.innerHTML = '';
    const placeholder = document.createElement('option');
    placeholder.text = "Select a compound...";
    placeholder.value = "";
    select.appendChild(placeholder);
    const fragment = document.createDocumentFragment();
    const sorted = json.slice(0, 1000).map(d => d.id).sort();
    for (let i = 0; i < sorted.length; i++) {
        const opt = document.createElement('option');
        opt.value = sorted[i];
        opt.textContent = sorted[i];
        fragment.appendChild(opt);
    }
    select.appendChild(fragment);
    select.addEventListener('change', (e) => { if(e.target.value) highlightSimilar(e.target.value); });
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.style.display = 'none', 500);
    }
}

function generateData() {
    fetch('atlas_data.json')
        .then(res => res.json())
        .then(json => {
            atlasData = json;
            idToIdx.clear();
            json.forEach((d, i) => idToIdx.set(d.id, i));
            setTimeout(() => populateSpectrumDropdown(json), 10);
            const len = json.length;
            const x = new Float32Array(len), y = new Float32Array(len), z = new Float32Array(len);
            const colors = new Array(len), ids = new Array(len);
            for(let i=0; i<len; i++) {
                x[i] = json[i].x; y[i] = json[i].y; z[i] = json[i].z;
                colors[i] = json[i].cluster; ids[i] = json[i].id;
            }
            const baseTrace = {
                x: x, y: y, z: z, mode: 'markers', text: ids, hoverinfo: 'text',
                marker: { size: 3, color: colors, colorscale: 'Viridis', opacity: 0.6, line: { width: 0 } },
                type: 'scatter3d', name: 'Spectra'
            };
            const highlightTrace = {
                x: [], y: [], z: [], mode: 'markers', text: [], hoverinfo: 'text',
                marker: { size: [], color: [], opacity: 1.0, symbol: 'circle', line: { width: 2, color: '#fff' } },
                type: 'scatter3d', name: 'Selected'
            };
            Plotly.newPlot('scatter3d', [baseTrace, highlightTrace], layout, {responsive: true, displayModeBar: false})
                .then(() => {
                    hideLoadingOverlay();
                    setTimeout(() => Plotly.Plots.resize('scatter3d'), 100);
                });
            document.getElementById('scatter3d').on('plotly_click', function(data){
                if(!data || !data.points) return;
                const pt = data.points[0];
                let selectedId = (pt.curveNumber === 0) ? ids[pt.pointNumber] : pt.text;
                if(selectedId) {
                    const select = document.getElementById('specSelect');
                    if(select) select.value = selectedId;
                    highlightSimilar(selectedId);
                }
            });
        })
        .catch(err => { console.error(err); hideLoadingOverlay(); });
}

async function highlightSimilar(specificId) {
    if (!atlasData.length) return;
    const anchorIdx = idToIdx.get(specificId);
    if (anchorIdx === undefined) return;
    const anchor = atlasData[anchorIdx];

    const pPanel = document.getElementById('details-panel');
    if(pPanel) {
        pPanel.style.display = 'block';
        document.getElementById('detail-id').textContent = anchor.id;
        document.getElementById('detail-cluster').textContent = anchor.cluster;
        document.getElementById('detail-xyz').textContent = `${anchor.x.toFixed(1)}, ${anchor.y.toFixed(1)}, ${anchor.z.toFixed(1)}`;
    }

    // Try Backend First (FAISS)
    let topIdx = [];
    try {
        const res = await fetch(`http://localhost:8000/search?id=${encodeURIComponent(specificId)}&k=20`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        topIdx = data.results.map(r => idToIdx.get(r.id)).filter(i => i !== undefined);
    } catch (e) {
        // Fallback to client-side
        const dists = new Float32Array(atlasData.length);
        const indices = new Int32Array(atlasData.length);
        const ax = anchor.x, ay = anchor.y, az = anchor.z;
        for (let i = 0; i < atlasData.length; i++) {
            const d = atlasData[i];
            const dx = d.x - ax, dy = d.y - ay, dz = d.z - az;
            dists[i] = dx*dx + dy*dy + dz*dz;
            indices[i] = i;
        }
        indices.sort((a, b) => dists[a] - dists[b]);
        topIdx = Array.from(indices.subarray(0, 20));
    }

    const hX = [], hY = [], hZ = [], hText = [], hColor = [], hSize = [];
    for(let i=0; i<topIdx.length; i++) {
        const d = atlasData[topIdx[i]];
        hX.push(d.x); hY.push(d.y); hZ.push(d.z); hText.push(d.id);
        if(i===0) { hColor.push('#ffffff'); hSize.push(12); } 
        else { hColor.push('#ff4b5c'); hSize.push(6); }
    }

    Plotly.restyle('scatter3d', { x: [hX], y: [hY], z: [hZ], text: [hText], 'marker.color': [hColor], 'marker.size': [hSize] }, [1]);
    Plotly.relayout('scatter3d', { 'scene.camera.center': { x: anchor.x, y: anchor.y, z: anchor.z } });
}

function loadComparison(targetName) {
    const colors = { '3M': '#ff0000', 'BASF': '#004a96' };
    fetch('atlas_data.json').then(res => res.json()).then(json => {
        const x = json.map(d => d.x + 1.5), y = json.map(d => d.y - 0.8), z = json.map(d => d.z + 0.3);
        const ids = json.map(d => `[${targetName}] ` + d.id);
        const comparisonTrace = {
            x: x, y: y, z: z, mode: 'markers', text: ids, hoverinfo: 'text',
            marker: { size: 2, color: colors[targetName] || '#fff', opacity: 0.3 },
            type: 'scatter3d', name: targetName
        };
        Plotly.addTraces('scatter3d', [comparisonTrace]);
    });
}
window.loadComparison = loadComparison;
