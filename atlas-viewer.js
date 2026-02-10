
// DreaMS Atlas Viewer Logic - RESTORED TO STABLE SINGLE-TRACE
// This reverts the Dual-Trace experiment to fix rendering freezes and visual fidelity.

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
    showlegend: false,
    hoverlabel: {
        bgcolor: "#1a1d24",
        bordercolor: "#333",
        font: { family: "Inter, sans-serif", color: "#fff" }
    }
};

let atlasData = [];
let idToIdx = new Map();
let baseColors = []; // Cache for reset
let baseSizes = []; // Cache for reset

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
    
    if(select.options.length > 1) return;

    select.innerHTML = '';
    const placeholder = document.createElement('option');
    placeholder.text = "Select a compound...";
    placeholder.value = "";
    select.appendChild(placeholder);

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

            // Cache for reset
            baseColors = colors.slice();
            baseSizes = new Array(len).fill(3);

            // SINGLE TRACE: High Fidelity
            const trace = {
                x: x, y: y, z: z,
                mode: 'markers',
                text: ids,
                hoverinfo: 'text',
                marker: { 
                    size: baseSizes, 
                    color: baseColors, 
                    colorscale: 'Viridis', 
                    opacity: 0.6, // Transparent for depth
                    line: { width: 0.5, color: 'rgba(255,255,255,0.2)' } // Subtle border for definition
                },
                type: 'scatter3d',
                name: 'Spectra'
            };

            Plotly.newPlot('scatter3d', [trace], layout, {responsive: true})
                .then(() => {
                    hideLoadingOverlay();
                    setTimeout(() => Plotly.Plots.resize('scatter3d'), 100);
                });

            // Click Handler
            document.getElementById('scatter3d').on('plotly_click', function(data){
                if(!data || !data.points) return;
                
                const pt = data.points[0];
                const selectedId = ids[pt.pointNumber];
                
                if(selectedId) {
                    const select = document.getElementById('specSelect');
                    if(select) select.value = selectedId;
                    
                    highlightSimilar(selectedId);

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
    let anchorId = specificId;
    if (!anchorId) {
        const select = document.getElementById('specSelect');
        if (select) anchorId = select.value;
    }
    if (!anchorId) return;

    const anchorIdx = idToIdx.get(anchorId);
    if (anchorIdx === undefined) return;
    const anchor = atlasData[anchorIdx];

    const pPanel = document.getElementById('details-panel');
    if(pPanel) {
        pPanel.style.display = 'block';
        document.getElementById('detail-id').textContent = anchor.id;
        document.getElementById('detail-cluster').textContent = anchor.cluster;
        document.getElementById('detail-xyz').textContent = 
            `${anchor.x.toFixed(1)}, ${anchor.y.toFixed(1)}, ${anchor.z.toFixed(1)}`;
    }

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

    const k = 20; 
    const topIdx = indices.subarray(0, k);

    // RESTORE SINGLE TRACE RESTYLE LOGIC
    const newColors = [...baseColors]; 
    const newSizes = [...baseSizes];   
    
    for(let i=0; i<k; i++) {
        const idx = topIdx[i];
        if(i===0) { // Anchor
            newColors[idx] = '#ffffff'; 
            newSizes[idx] = 10;
        } else { // Neighbor
            newColors[idx] = '#ff4b5c'; 
            newSizes[idx] = 6;
        }
    }

    Plotly.restyle('scatter3d', {
        'marker.color': [newColors],
        'marker.size': [newSizes]
    }, [0]);

    // Cinematic Camera Move
    Plotly.relayout('scatter3d', {
        'scene.camera.center': { x: ax, y: ay, z: az }
    }, {
        transition: {
            duration: 1200,
            easing: 'cubic-in-out'
        }
    });
}
