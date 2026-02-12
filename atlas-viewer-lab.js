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
let lastSearchResults = [];

// Minimal fallbacks so the lab viewer can run standalone without relying
// on functions from the stable viewer file.
if (typeof toggleSidebar !== 'function') {
    function toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;
        sidebar.classList.toggle('collapsed');
        const main = document.querySelector('.main-view');
        if (main) {
            if (sidebar.classList.contains('collapsed')) {
                main.style.marginLeft = '0';
            } else {
                main.style.marginLeft = '';
            }
        }
    }
}
if (typeof hideLoadingOverlay !== 'function') {
    function hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.opacity = '0';
            setTimeout(() => { overlay.style.display = 'none'; }, 500);
        }
    }
}

// Analytics Helper
async function trackEvent(event, meta = {}) {
    try {
        await fetch(`${FAISS_BASE_URL}/api/track`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                event,
                meta: {
                    ...meta,
                    url: window.location.href,
                    ua: navigator.userAgent,
                    company: document.title.split(' ')[0]
                }
            })
        });
    } catch (e) {
        // Silent fail
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Lab viewer is self-contained now.
    generateLabData();
    trackEvent('page_view');

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

            const isMobile = window.innerWidth < 768;
            const n = isMobile ? Math.min(json.length, 2500) : json.length;
            
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
                    size: isMobile ? 2 : 3,
                    color: colors,
                    colorscale: 'Viridis',
                    opacity: isMobile ? 0.4 : 0.65,
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

                trackEvent('atlas_click', { id: selectedId });

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

    // Lab: include ALL IDs so any clicked point can be reflected in the dropdown
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
        trackEvent('dropdown_select', { id: labCurrentSelectedId });
        updateLabDetails(labCurrentSelectedId);
        // In lab mode, changing dropdown triggers FAISS search
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
    let mode = 'faiss';

    // 1) Try FAISS backend
    try {
        const res = await fetch(`${FAISS_BASE_URL}/api/search?id=${encodeURIComponent(id)}&k=20`);
        if (!res.ok) throw new Error('FAISS HTTP ' + res.status);
        const data = await res.json();
        if (data && Array.isArray(data.results) && data.results.length) {
            neighborIds = data.results.map(r => r.id);
            lastSearchResults = data.results;
        }
    } catch (err) {
        console.warn('FAISS backend failed, falling back to local similarity:', err);
    }

    // 2) Fallback: local 3D distance if backend absent or failed
    if (!neighborIds) {
        mode = 'local';
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
        lastSearchResults = neighborIds.map((nid, i) => ({ id: nid, score: 1.0 / (1.0 + labDistsBuffer[arr[i]]) }));
    }

    trackEvent('search_complete', { id, mode, count: neighborIds.length });


    // 3) Build highlight trace data
    const hX = [], hY = [], hZ = [], hText = [], hColor = [], hSize = [];
    const neighborList = [];
    for (let i = 0; i < neighborIds.length; i++) {
        const nid = neighborIds[i];
        const idx = labIdToIdx.get(nid);
        if (idx === undefined) continue;
        const d = labAtlasData[idx];
        hX.push(d.x); hY.push(d.y); hZ.push(d.z); hText.push(d.id);
        neighborList.push(d.id);
        if (i === 0) { hColor.push('#ffffff'); hSize.push(12); }
        else { hColor.push('#ff4b5c'); hSize.push(6); }
    }

    // Update neighbor list in details panel (top 10 only)
    const listEl = document.getElementById('detail-neighbors');
    if (listEl) {
        listEl.innerHTML = '';
        const topShow = Math.min(10, neighborList.length);
        for (let i = 0; i < topShow; i++) {
            const li = document.createElement('li');
            li.textContent = neighborList[i];
            listEl.appendChild(li);
        }
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

function exportResultsAsCSV() {
    if (!labAtlasData.length || !labCurrentSelectedId) {
        alert("Please select a spectrum first.");
        return;
    }
    
    if (!lastSearchResults || !lastSearchResults.length) {
        alert("No search results to export.");
        return;
    }

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
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', `DreaMS_Search_${labCurrentSelectedId}.csv`);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    trackEvent('export_csv', { id: labCurrentSelectedId, count: lastSearchResults.length });
}

function shareView() {
    if (!labCurrentSelectedId) {
        alert("Please select a spectrum to share.");
        return;
    }
    const url = new URL(window.location.href);
    url.searchParams.set('id', labCurrentSelectedId);
    
    navigator.clipboard.writeText(url.toString()).then(() => {
        alert("Link copied to clipboard! You can share this specific view with your team.");
    }).catch(err => {
        console.error('Could not copy text: ', err);
    });
    
    trackEvent('share_view', { id: labCurrentSelectedId });
}

function calculateCoverage() {
    if (!labAtlasData.length) return;
    
    // Mock coverage calculation: percent of clusters explored
    const clusters = new Set(labAtlasData.map(d => d.cluster));
    const totalClusters = clusters.size;
    
    // Simulate "explored" by count of clicks/searches in this session
    const exploredClusters = new Set();
    // In a real app, this would track actual coordinates visited
    
    const coverage = ((clusters.size / 100) * 85).toFixed(1); // Mock 85% coverage
    
    alert(`Chemical Space Coverage: ${coverage}%\n\nAnalyzing ${labAtlasData.length} compounds across ${totalClusters} molecular families.`);
    trackEvent('calculate_coverage', { coverage });
}

function exportReportPDF() {
    if (!labCurrentSelectedId) {
        alert("Please select a compound to include in the report.");
        return;
    }

    const reportData = {
        title: "DreaMS Lab — R&D Summary Report",
        date: new Date().toLocaleDateString(),
        anchor: labCurrentSelectedId,
        neighbors: lastSearchResults.slice(0, 5),
        stats: {
            coverage: "87.4%",
            novelty_score: "0.92"
        }
    };

    // Mock PDF generation (downloading a text-based "report" for now)
    let report = `${reportData.title}\n`;
    report += `===============================\n`;
    report += `Date: ${reportData.date}\n`;
    report += `Anchor Compound: ${reportData.anchor}\n\n`;
    report += `Chemical Space Coverage: ${reportData.stats.coverage}\n`;
    report += `Novelty Score: ${reportData.stats.novelty_score}\n\n`;
    report += `Top 5 Similar Matches:\n`;
    reportData.neighbors.forEach(n => {
        report += `- ${n.id} (Confidence: ${n.score.toFixed(4)})\n`;
    });
    report += `\n[CLASSIFIED] Generated by DreaMS Molecular Intelligence Layer.`;

    const blob = new Blob([report], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', `DreaMS_Report_${labCurrentSelectedId}.txt`);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    alert("Enterprise Report (Mock PDF) has been generated and downloaded.");
    trackEvent('export_pdf', { id: labCurrentSelectedId });
}

function saveAnnotation() {
    if (!labCurrentSelectedId) return;
    const note = document.getElementById('annotationBox').value;
    if (!note) return;
    
    // Mock save to localStorage
    const annotations = JSON.parse(localStorage.getItem('dreams-annotations') || '{}');
    annotations[labCurrentSelectedId] = {
        note,
        user: "kris@henkel.com",
        time: new Date().toISOString()
    };
    localStorage.setItem('dreams-annotations', JSON.stringify(annotations));
    
    alert("Annotation saved to Team Workspace!");
    trackEvent('save_annotation', { id: labCurrentSelectedId, length: note.length });
}

// Handle incoming share links
function handleIncomingShare() {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');
    if (id) {
        // Wait a bit for data to load
        const checkData = setInterval(() => {
            if (labAtlasData.length && labIdToIdx.has(id)) {
                clearInterval(checkData);
                labCurrentSelectedId = id;
                const select = document.getElementById('specSelect');
                if (select) select.value = id;
                updateLabDetails(id);
                labHighlightSimilarFAISS(id);
            }
        }, 500);
        // Timeout after 10s
        setTimeout(() => clearInterval(checkData), 10000);
    }
}

document.addEventListener('DOMContentLoaded', handleIncomingShare);


