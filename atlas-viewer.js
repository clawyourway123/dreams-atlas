
// DreaMS Atlas Viewer Logic - Balanced for Performance & Visuals
// Architecture: Dual Trace (Static Background + Dynamic Overlay)

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
        dragmode: 'orbit',
        camera: { eye: {x: 1.5, y: 1.5, z: 1.5} }
    },
    uirevision: 'atlas-1', 
    hovermode: 'closest',
    showlegend: false
};

let atlasData = [];
let idToIdx = new Map();

document.addEventListener('DOMContentLoaded', () => {
    initDetailsPanel();
    generateData();
    
    // Resize handler
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            try { Plotly.Plots.resize('scatter3d'); } catch(e){}
        }, 150);
    });

    // Sidebar Toggle (Mobile)
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
        div.innerHTML = `
            <label style="font-size: 12px; color: #aaa; display: block; margin-bottom: 5px;">Selected Spectrum</label>
            <div id="detail-id" style="font-weight:bold; color:#fff; word-break:break-all; margin-bottom:5px;"></div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#aaa;">
                <span>Cluster: <span id="detail-cluster" style="color:#fff;"></span></span>
            </div>
            <div style="margin-top:5px; font-size:11px; font-family:monospace; color:#666;">
                XYZ: <span id="detail-xyz"></span>
            </div>
        `;
        const similaritySection = Array.from(sidebar.querySelectorAll('h2')).find(h => h.textContent.includes('Similarity'));
        if (similaritySection && similaritySection.nextElementSibling) {
             similaritySection.nextElementSibling.insertAdjacentElement('afterend', div);
        } else {
             sidebar.appendChild(div);
        }
    }
}

function populateSpectrumDropdown(json) {
    const select = document.getElementById('specSelect');
    if (!select || json.length === 0) return;
    
    // Use a simplified approach to avoid blocking UI
    // Only populate if empty
    if(select.options.length > 1) return;

    select.innerHTML = '';
    const placeholder = document.createElement('option');
    placeholder.text = "Select a compound...";
    placeholder.value = "";
    select.appendChild(placeholder);

    // Limit to top 2000 for dropdown performance? 
    // Or use a virtual list? For now, full list but deferred.
    // Actually, filling 25k options IS slow.
    // Let's use requestIdleCallback or setTimeout chunks if we really need it.
    // For now, standard blocking but optimized via Fragment.
    
    const fragment = document.createDocumentFragment();
    const sorted = json.map(d => d.id).sort();
    
    for (let i = 0; i < sorted.length; i++) {
        const opt = document.createElement('option');
        opt.value = sorted[i];
        opt.textContent = sorted[i];
        fragment.appendChild(opt);
    }
    select.appendChild(fragment);
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

            // Async populate dropdown to not block render
            setTimeout(() => populateSpectrumDropdown(json), 10);

            const len = json.length;
            const x = new Float32Array(len);
            const y = new Float32Array(len);
            const z = new Float32Array(len);
            const colors = new Array(len);
            const ids = new Array(len);

            for(let i=0; i<len; i++) {
                x[i] = json[i].x;
                y[i] = json[i].y;
                z[i] = json[i].z;
                colors[i] = json[i].cluster;
                ids[i] = json[i].id;
            }

            // Trace 0: Background (High Fidelity)
            // Using marker.line.width > 0 adds cost, but user wants "looks".
            // Let's try 0.5px line for definition without killing it.
            const baseTrace = {
                x: x, y: y, z: z,
                mode: 'markers',
                text: ids,
                hoverinfo: 'text',
                marker: { 
                    size: 3, 
                    color: colors, 
                    colorscale: 'Viridis', 
                    opacity: 0.7, // Higher opacity for "pop"
                    line: { width: 0 } // Keep 0 for perf, rely on opacity/color
                },
                type: 'scatter3d',
                name: 'Spectra'
            };

            // Trace 1: Highlights (Overlay)
            const highlightTrace = {
                x: [], y: [], z: [],
                mode: 'markers',
                text: [],
                hoverinfo: 'text',
                marker: { 
                    size: [], 
                    color: [], 
                    opacity: 1.0,
                    symbol: 'circle',
                    line: { width: 2, color: '#fff' } // Distinct highlight
                },
                type: 'scatter3d',
                name: 'Selected'
            };

            Plotly.newPlot('scatter3d', [baseTrace, highlightTrace], layout, {responsive: true})
                .then(() => {
                    hideLoadingOverlay();
                    // Force a resize to fix black screen issues
                    setTimeout(() => Plotly.Plots.resize('scatter3d'), 100);
                });

            // Click Handler
            document.getElementById('scatter3d').on('plotly_click', function(data){
                if(!data || !data.points) return;
                
                const pt = data.points[0];
                let selectedId;
                
                if (pt.curveNumber === 0) {
                    selectedId = ids[pt.pointNumber];
                } else if (pt.curveNumber === 1) {
                    selectedId = pt.text;
                }
                
                if(selectedId) {
                    // Update Dropdown UI (Silent)
                    const select = document.getElementById('specSelect');
                    if(select) select.value = selectedId;
                    
                    // Trigger Logic
                    highlightSimilar(selectedId);

                    // Mobile UX
                    if (window.innerWidth <= 768) {
                        document.querySelector('.sidebar').classList.remove('open');
                    }
                }
            });
        })
        .catch(err => {
            console.error(err);
            hideLoadingOverlay();
        });
}

function highlightSimilar(specificId) {
    // 1. Resolve Anchor
    let anchorId = specificId;
    if (!anchorId) {
        const select = document.getElementById('specSelect');
        if (select) anchorId = select.value;
    }
    if (!anchorId) return;

    const anchorIdx = idToIdx.get(anchorId);
    if (anchorIdx === undefined) return;
    const anchor = atlasData[anchorIdx];

    // 2. Update Details Panel
    const pPanel = document.getElementById('details-panel');
    if(pPanel) {
        pPanel.style.display = 'block';
        document.getElementById('detail-id').textContent = anchor.id;
        document.getElementById('detail-cluster').textContent = anchor.cluster;
        document.getElementById('detail-xyz').textContent = 
            `${anchor.x.toFixed(1)}, ${anchor.y.toFixed(1)}, ${anchor.z.toFixed(1)}`;
    }

    // 3. Calc Neighbors (Optimized Loop)
    const dists = new Float32Array(atlasData.length);
    const indices = new Int32Array(atlasData.length);
    const ax = anchor.x, ay = anchor.y, az = anchor.z;
    
    for (let i = 0; i < atlasData.length; i++) {
        const d = atlasData[i];
        const dx = d.x - ax, dy = d.y - ay, dz = d.z - az;
        dists[i] = dx*dx + dy*dy + dz*dz;
        indices[i] = i;
    }
    
    // Sort top K only? No, partial sort is hard in JS. Full sort is fast enough for 25k.
    indices.sort((a, b) => dists[a] - dists[b]);

    // 4. Update Highlight Trace
    const k = 20; 
    const topIdx = indices.subarray(0, k);

    const hX = [], hY = [], hZ = [], hText = [], hColor = [], hSize = [];
    
    for(let i=0; i<k; i++) {
        const idx = topIdx[i];
        const d = atlasData[idx];
        hX.push(d.x); hY.push(d.y); hZ.push(d.z);
        hText.push(d.id);
        
        if(i===0) { // Anchor
            hColor.push('#ffffff'); hSize.push(10);
        } else { // Neighbor
            hColor.push('#ff4b5c'); hSize.push(6);
        }
    }

    // RESTYLE TRACE 1 ONLY
    Plotly.restyle('scatter3d', {
        x: [hX], y: [hY], z: [hZ],
        text: [hText],
        'marker.color': [hColor],
        'marker.size': [hSize]
    }, [1]);

    // 5. Animate Camera (Optional - does this cause lag?)
    // Let's keep it but make it smooth.
    Plotly.relayout('scatter3d', {
        'scene.camera.center': { x: ax, y: ay, z: az }
    });
}

function uploadDataset() {
    document.getElementById('fileUpload').click();
}
function handleFile(input) {
    if (input.files && input.files[0]) {
        alert("Live uploads disabled in demo.");
        input.value = "";
    }
}
