
// DreaMS Atlas Viewer Logic - Ultra-Stable Dual Trace
// Architecture: 
// Trace 0: Base Dataset (Static, 25k points)
// Trace 1: Highlights (Dynamic, 20 points)
// Trace 2+: Comparison Overlays

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
    uirevision: 'atlas-persistent', 
    hovermode: 'closest',
    showlegend: false
};

let atlasData = [];
let idToIdx = new Map();

// PRE-ALLOCATED BUFFERS (Stop GC crashes)
let distsBuffer = null;
let indicesBuffer = null;

document.addEventListener('DOMContentLoaded', () => {
    initDetailsPanel();
    initComparisonPanel();
    generateData();
    
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            try { Plotly.Plots.resize('scatter3d'); } catch(e){}
        }, 200);
    });

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
    if (!select) return;
    select.innerHTML = '';
    const placeholder = document.createElement('option');
    placeholder.text = "Select a compound...";
    placeholder.value = "";
    select.appendChild(placeholder);
    
    // Performance optimization: only show top items
    const limited = json.slice(0, 1000).sort((a,b) => a.id.localeCompare(b.id));
    const fragment = document.createDocumentFragment();
    for (let i = 0; i < limited.length; i++) {
        const opt = document.createElement('option');
        opt.value = limited[i].id;
        opt.textContent = limited[i].id;
        fragment.appendChild(opt);
    }
    select.appendChild(fragment);
    select.onchange = (e) => { if(e.target.value) highlightSimilar(e.target.value); };
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
            
            // Allocate buffers once
            distsBuffer = new Float32Array(json.length);
            indicesBuffer = new Int32Array(json.length);

            const x = new Float32Array(json.length);
            const y = new Float32Array(json.length);
            const z = new Float32Array(json.length);
            const colors = new Array(json.length);
            const ids = new Array(json.length);

            for(let i=0; i<json.length; i++) {
                const d = json[i];
                idToIdx.set(d.id, i);
                x[i] = d.x; y[i] = d.y; z[i] = d.z;
                colors[i] = d.cluster; ids[i] = d.id;
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
                if(selectedId) highlightSimilar(selectedId);
            });

            populateSpectrumDropdown(json);
        })
        .catch(err => { console.error(err); hideLoadingOverlay(); });
}

async function highlightSimilar(specificId) {
    if (!atlasData.length) return;
    const anchorIdx = idToIdx.get(specificId);
    if (anchorIdx === undefined) return;
    const anchor = atlasData[anchorIdx];

    // Details Update
    const p = document.getElementById('details-panel');
    if(p) {
        p.style.display = 'block';
        document.getElementById('detail-id').textContent = anchor.id;
        document.getElementById('detail-cluster').textContent = anchor.cluster;
        document.getElementById('detail-xyz').textContent = `${anchor.x.toFixed(1)}, ${anchor.y.toFixed(1)}, ${anchor.z.toFixed(1)}`;
    }

    // SIMILARITY CALC (Optimized Client-side using buffers)
    const ax = anchor.x, ay = anchor.y, az = anchor.z;
    for (let i = 0; i < atlasData.length; i++) {
        const d = atlasData[i];
        const dx = d.x - ax, dy = d.y - ay, dz = d.z - az;
        distsBuffer[i] = dx*dx + dy*dy + dz*dz;
        indicesBuffer[i] = i;
    }
    indicesBuffer.sort((a, b) => distsBuffer[a] - distsBuffer[b]);

    const k = 20;
    const hX = [], hY = [], hZ = [], hText = [], hColor = [], hSize = [];
    for(let i=0; i<k; i++) {
        const idx = indicesBuffer[i];
        const d = atlasData[idx];
        hX.push(d.x); hY.push(d.y); hZ.push(d.z); hText.push(d.id);
        if(i===0) { hColor.push('#ffffff'); hSize.push(12); } 
        else { hColor.push('#ff4b5c'); hSize.push(6); }
    }

    // RESTYLE TRACE 1 ONLY (The Dynamic Layer)
    Plotly.restyle('scatter3d', { x: [hX], y: [hY], z: [hZ], text: [hText], 'marker.color': [hColor], 'marker.size': [hSize] }, [1]);
    
    // Smooth Camera (Relayout is stable here because Trace 0 is static)
    Plotly.relayout('scatter3d', {
        'scene.camera.center': { x: ax, y: ay, z: az },
        'scene.camera.eye': { x: 0.5, y: 0.5, z: 0.5 }
    });
}

function loadComparison(targetName) {
    const colors = { '3M': '#ff0000', 'BASF': '#004a96' };
    fetch('atlas_data.json').then(res => res.json()).then(json => {
        const x = json.map(d => d.x + 1.5), y = json.map(d => d.y - 0.8), z = json.map(d => d.z + 0.3);
        const ids = json.map(d => `[${targetName}] ` + d.id);
        Plotly.addTraces('scatter3d', [{
            x: x, y: y, z: z, mode: 'markers', text: ids, hoverinfo: 'text',
            marker: { size: 2, color: colors[targetName] || '#fff', opacity: 0.3 },
            type: 'scatter3d', name: targetName
        }]);
    });
}
window.loadComparison = loadComparison;
