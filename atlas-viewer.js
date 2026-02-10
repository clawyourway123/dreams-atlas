
// DreaMS Atlas Viewer Logic
// Shared across all client demos

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
    uirevision: 'atlas-1'
};

let atlasData = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initDetailsPanel();
    generateData();
    window.addEventListener('resize', () => {
        try { Plotly.Plots.resize('scatter3d'); } catch(e){}
    });
});

function initDetailsPanel() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    // Create Details Panel if not exists
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
        // Insert before the "What you're seeing" section (usually the last div or close to it)
        // Or just append after the specific controls
        const similaritySection = Array.from(sidebar.querySelectorAll('h2')).find(h => h.textContent.includes('Similarity'));
        if (similaritySection && similaritySection.nextElementSibling) {
             // Insert after the similarity container (stat-card)
             similaritySection.nextElementSibling.insertAdjacentElement('afterend', div);
        } else {
             sidebar.appendChild(div);
        }
    }
}

function populateSpectrumDropdown(json) {
    const select = document.getElementById('specSelect');
    if (!select || json.length === 0) return;
    select.innerHTML = '';
    
    const placeholder = document.createElement('option');
    placeholder.text = "Select a compound...";
    placeholder.value = "";
    select.appendChild(placeholder);

    // Sort alphabetically
    const sorted = [...json].sort((a, b) => a.id.localeCompare(b.id));
    
    for (let i = 0; i < sorted.length; i++) {
        const opt = document.createElement('option');
        opt.value = sorted[i].id;
        opt.textContent = sorted[i].id;
        select.appendChild(opt);
    }
}

function generateData() {
    fetch('atlas_data.json')
        .then(res => {
            if (!res.ok) throw new Error("Network response was not ok");
            return res.json();
        })
        .then(json => {
            atlasData = json;
            populateSpectrumDropdown(json);

            const x = json.map(d => d.x);
            const y = json.map(d => d.y);
            const z = json.map(d => d.z);
            const colors = json.map(d => d.cluster);
            const ids = json.map(d => d.id);

            window.baseColors = colors.slice();
            window.baseSizes = new Array(json.length).fill(2);
            window.baseIds = ids.slice();

            window.currentColors = colors.slice();
            window.currentSizes = new Array(json.length).fill(2);
            window.lastHighlightedIdx = [];

            const baseTrace = {
                x: x, y: y, z: z,
                mode: 'markers',
                text: ids,
                hoverinfo: 'text',
                marker: { size: window.baseSizes, color: window.baseColors, colorscale: 'Viridis', opacity: 0.6 },
                type: 'scatter3d',
                name: 'All spectra'
            };
            
            Plotly.newPlot('scatter3d', [baseTrace], layout).then(() => {
                // Fix for black screen on some loads: force a resize/redraw
                setTimeout(() => Plotly.Plots.resize('scatter3d'), 100);
            });

            // Index for clicks
            const idToFullIndex = new Map();
            json.forEach((d, idx) => {
                idToFullIndex.set(d.id, idx);
            });

            const plotEl = document.getElementById('scatter3d');
            plotEl.on('plotly_click', function(data){
                if(!data || !data.points) return;
                const pointIndex = data.points[0].pointNumber;
                
                // Map from rendered point to full atlas id
                const selectedId = ids[pointIndex];
                const fullIdx = idToFullIndex.get(selectedId);
                if (fullIdx == null) return;

                console.log("Clicked:", selectedId);
                
                // Update Dropdown
                const select = document.getElementById('specSelect');
                if(select) {
                    select.value = selectedId;
                    // Trigger update
                    highlightSimilar();
                }
            });
        })
        .catch(err => {
            console.error("Data load failed:", err);
            const msg = {
                showlegend: false,
                annotations: [{
                    text: "Data Load Failed<br>" + err.message,
                    font: { size: 14, color: '#ff4444' },
                    showarrow: false,
                    align: 'center',
                    x: 0.5, y: 0.5
                }]
            };
            Plotly.newPlot('scatter3d', [], {...layout, ...msg});
        });
}

function uploadDataset() {
    const fileInput = document.getElementById('fileUpload');
    if(fileInput) fileInput.click();
}

function handleFile(input) {
    if (input.files && input.files[0]) {
        alert("Live uploads are disabled for this demo.\n\nTo add spectra, process the MGF file offline with DreaMS and re-run generate_atlas_real.py.");
        input.value = "";
    }
}

function highlightSimilar() {
    if (!atlasData || atlasData.length === 0) return;
    
    const select = document.getElementById('specSelect');
    if (!select || !select.value) return;
    
    const anchorId = select.value;
    const anchor = atlasData.find(d => d.id === anchorId);
    if (!anchor) return;

    // update details panel
    const pPanel = document.getElementById('details-panel');
    if(pPanel) {
        pPanel.style.display = 'block';
        document.getElementById('detail-id').textContent = anchor.id;
        document.getElementById('detail-cluster').textContent = anchor.cluster;
        document.getElementById('detail-xyz').textContent = 
            `${anchor.x.toFixed(1)}, ${anchor.y.toFixed(1)}, ${anchor.z.toFixed(1)}`;
    }

    // Compute distances
    const distances = atlasData.map((d, idx) => {
        const dx = d.x - anchor.x;
        const dy = d.y - anchor.y;
        const dz = d.z - anchor.z;
        return { idx, dist: Math.sqrt(dx*dx + dy*dy + dz*dz) };
    });
    distances.sort((a, b) => a.dist - b.dist);

    const k = 50; // Increased context
    const neighbourIdx = distances.slice(0, k).map(d => d.idx);

    // Reset old highlights
    if (window.lastHighlightedIdx && window.lastHighlightedIdx.length > 0) {
        window.lastHighlightedIdx.forEach(i => {
            window.currentColors[i] = window.baseColors[i];
            window.currentSizes[i] = window.baseSizes[i];
        });
    }

    // Apply new highlights (Red for anchor, Orange for neighbors)
    neighbourIdx.forEach((i, rank) => {
        if (rank === 0) {
            window.currentColors[i] = '#ffffff'; // Anchor white
            window.currentSizes[i] = 10;
        } else {
            window.currentColors[i] = '#ff4b5c'; // Neighbors red
            window.currentSizes[i] = 6;
        }
    });

    window.lastHighlightedIdx = neighbourIdx;

    // Update Plot
    Plotly.restyle('scatter3d', {
        'marker.color': [window.currentColors],
        'marker.size': [window.currentSizes]
    }, [0]);

    // ANIMATE CAMERA to focus on the cluster
    // Target the anchor, pull back along the normal vector towards origin slightly
    const target = { x: anchor.x, y: anchor.y, z: anchor.z };
    
    // Simple zoom: maintain current viewing angle but move closer? 
    // Or just move camera eye to a fixed offset?
    // Let's try to keep the camera "orbiting" but center the target.
    
    const currentLayout = document.getElementById('scatter3d').layout;
    let currentEye = currentLayout.scene.camera.eye;
    
    // Normalize eye vector to keep distance reasonable
    // (This is a naive zoom impl; ideally we'd calculate a vector based on cluster spread)
    
    Plotly.relayout('scatter3d', {
        'scene.camera.center': target,
        // Optional: Zoom in slightly if we are far away, but for now just centering is huge improvement
        // 'scene.camera.eye': {x: currentEye.x * 0.8, y: currentEye.y * 0.8, z: currentEye.z * 0.8} 
    });
}
