'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { apiFetch } from '@/lib/api';

interface AtlasPoint {
  id: string;
  x: number;
  y: number;
  z: number;
  cluster: number;
  properties: { tack: number; shear: number; viscosity: number };
}

interface ClusterInfo {
  cluster_id: number;
  size: number;
}

interface DataPoint {
  x: number;
  y: number;
  z: number;
  family: string;
  compound: string;
  color: string;
}

const CLUSTER_COLORS: string[] = [
  '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444',
  '#22c55e', '#f97316', '#14b8a6', '#ec4899',
  '#a855f7', '#06b6d4',
];

// Fallback: procedurally generated data when API is unavailable
function generateFallbackData(): DataPoint[] {
  const rng = (seed: number) => {
    let s = seed;
    return () => { s = (s * 16807 + 0) % 2147483647; return s / 2147483647; };
  };
  const rand = rng(42);
  const clusters: { family: string; cx: number; cy: number; cz: number; compounds: string[]; spread: number }[] = [
    { family: 'Acrylic/PSA', cx: -2.5, cy: 1.8, cz: 0.5, compounds: ['Loctite 3090 PSA', '3M VHB 4910', 'tesa ACXplus', 'Avery S8000'], spread: 1.2 },
    { family: 'Cyanoacrylate', cx: 3.0, cy: 2.5, cz: -1.0, compounds: ['Loctite 401', 'Permabond 910', 'Infinity CA+'], spread: 0.9 },
    { family: 'Epoxy', cx: -1.0, cy: -2.5, cz: 2.0, compounds: ['Araldite AW 106', '3M DP420', 'Henkel EA 9395'], spread: 1.1 },
    { family: 'Hot-melt', cx: 2.0, cy: -1.5, cz: -2.0, compounds: ['Henkel Technomelt', 'Bostik Thermogrip', 'H.B. Fuller HL 6444'], spread: 1.0 },
    { family: 'Polyurethane', cx: -3.0, cy: -0.5, cz: -1.5, compounds: ['Sikaflex 252', 'Loctite PL Premium', '3M 550'], spread: 1.1 },
    { family: 'Rubber-based', cx: 1.5, cy: 0.5, cz: 2.5, compounds: ['3M 77 Spray', 'Bostik Grip N Grab', 'DAP Weldwood'], spread: 1.0 },
    { family: 'Silicone', cx: 0, cy: 3.0, cz: 0, compounds: ['Dow Corning 732', 'GE Silicone II', 'Permatex Ultra'], spread: 0.8 },
  ];
  const points: DataPoint[] = [];
  for (const cl of clusters) {
    const n = 12 + Math.floor(rand() * 8);
    for (let i = 0; i < n; i++) {
      points.push({
        x: cl.cx + (rand() - 0.5) * cl.spread * 2,
        y: cl.cy + (rand() - 0.5) * cl.spread * 2,
        z: cl.cz + (rand() - 0.5) * cl.spread * 2,
        family: cl.family,
        compound: cl.compounds[Math.floor(rand() * cl.compounds.length)],
        color: CLUSTER_COLORS[clusters.indexOf(cl) % CLUSTER_COLORS.length],
      });
    }
  }
  return points;
}

function project(
  x: number, y: number, z: number,
  rotX: number, rotY: number,
  scale: number, cx: number, cy: number,
): { px: number; py: number; depth: number } {
  const cosY = Math.cos(rotY), sinY = Math.sin(rotY);
  const x1 = x * cosY + z * sinY;
  const z1 = -x * sinY + z * cosY;
  const cosX = Math.cos(rotX), sinX = Math.sin(rotX);
  const y1 = y * cosX - z1 * sinX;
  const z2 = y * sinX + z1 * cosX;
  return { px: cx + x1 * scale, py: cy - y1 * scale, depth: z2 };
}

export default function MolecularViewer3D() {
  const [data, setData] = useState<DataPoint[]>(() => generateFallbackData());
  const [clusterNames, setClusterNames] = useState<Map<number, string>>(new Map());
  const [loading, setLoading] = useState(true);
  const [usingFallback, setUsingFallback] = useState(false);
  const [rotX, setRotX] = useState(-0.4);
  const [rotY, setRotY] = useState(0.6);
  const [dragging, setDragging] = useState(false);
  const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 });
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [activeFamily, setActiveFamily] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  const width = 720;
  const height = 480;
  const scale = 45;
  const cx = width / 2;
  const cy = height / 2;

  // Fetch real atlas data + cluster list
  useEffect(() => {
    let cancelled = false;

    async function loadAtlasData() {
      try {
        const [atlasRes, clusterRes] = await Promise.all([
          fetch('/atlas_data.json').then((r) => {
            if (!r.ok) throw new Error('Atlas data not found');
            return r.json() as Promise<AtlasPoint[]>;
          }),
          apiFetch<{ clusters: ClusterInfo[] }>('/api/cluster/list').catch(() => null),
        ]);

        if (cancelled) return;

        // Build cluster name map from cluster list
        const nameMap = new Map<number, string>();
        if (clusterRes) {
          clusterRes.clusters.forEach((c) => nameMap.set(c.cluster_id, `Cluster ${c.cluster_id}`));
        }
        setClusterNames(nameMap);

        // Subsample for performance (max 500 points for SVG rendering)
        const sampled = atlasRes.length > 500
          ? atlasRes.filter((_, i) => i % Math.ceil(atlasRes.length / 500) === 0)
          : atlasRes;

        // Normalize coordinates to fit in view
        const xs = sampled.map((p) => p.x);
        const ys = sampled.map((p) => p.y);
        const zs = sampled.map((p) => p.z);
        const maxRange = Math.max(
          Math.max(...xs) - Math.min(...xs),
          Math.max(...ys) - Math.min(...ys),
          Math.max(...zs) - Math.min(...zs),
        ) || 1;
        const normFactor = 6 / maxRange;

        const points: DataPoint[] = sampled.map((p) => ({
          x: p.x * normFactor,
          y: p.y * normFactor,
          z: p.z * normFactor,
          family: nameMap.get(p.cluster) ?? `Cluster ${p.cluster}`,
          compound: p.id.split('_')[0],
          color: CLUSTER_COLORS[p.cluster % CLUSTER_COLORS.length],
        }));

        setData(points);
        setUsingFallback(false);
      } catch {
        if (!cancelled) setUsingFallback(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadAtlasData();
    return () => { cancelled = true; };
  }, []);

  // Auto-rotate when not interacting
  useEffect(() => {
    if (dragging) return;
    const id = setInterval(() => setRotY((r) => r + 0.003), 30);
    return () => clearInterval(id);
  }, [dragging]);

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    setDragging(true);
    setLastMouse({ x: e.clientX, y: e.clientY });
    (e.target as Element).setPointerCapture?.(e.pointerId);
  }, []);

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!dragging) return;
      const dx = e.clientX - lastMouse.x;
      const dy = e.clientY - lastMouse.y;
      setRotY((r) => r + dx * 0.005);
      setRotX((r) => Math.max(-Math.PI / 2, Math.min(Math.PI / 2, r - dy * 0.005)));
      setLastMouse({ x: e.clientX, y: e.clientY });
    },
    [dragging, lastMouse],
  );

  const handlePointerUp = useCallback(() => setDragging(false), []);

  const projected = data.map((d, i) => {
    const p = project(d.x, d.y, d.z, rotX, rotY, scale, cx, cy);
    return { ...d, ...p, idx: i };
  });

  const sorted = [...projected].sort((a, b) => a.depth - b.depth);

  const axisLen = 4;
  const axes = [
    { label: 'PC1', end: project(axisLen, 0, 0, rotX, rotY, scale, cx, cy), color: '#4ade80' },
    { label: 'PC2', end: project(0, axisLen, 0, rotX, rotY, scale, cx, cy), color: '#60a5fa' },
    { label: 'PC3', end: project(0, 0, axisLen, rotX, rotY, scale, cx, cy), color: '#f472b6' },
  ];
  const origin = project(0, 0, 0, rotX, rotY, scale, cx, cy);

  const families = Array.from(new Set(data.map((d) => d.family)));

  return (
    <div>
      {/* Legend */}
      <div className="mb-4 flex flex-wrap justify-center gap-2">
        {families.map((f) => {
          const color = data.find((d) => d.family === f)?.color ?? '#6b7280';
          return (
            <button
              key={f}
              onClick={() => setActiveFamily(activeFamily === f ? null : f)}
              className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-all ${
                activeFamily === null || activeFamily === f
                  ? 'border-white/10 text-white'
                  : 'border-white/5 text-navy-500'
              }`}
            >
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
              {f}
            </button>
          );
        })}
        {usingFallback && (
          <span className="flex items-center rounded-full bg-amber-500/10 px-2.5 py-1 text-[10px] text-amber-400">
            demo data
          </span>
        )}
      </div>

      {/* 3D Viewer */}
      <div className="relative mx-auto overflow-hidden rounded-panel border border-white/5 bg-navy-950/80 shadow-card">
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-navy-950/60 backdrop-blur-sm">
            <div className="flex flex-col items-center gap-3">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-400/30 border-t-teal-400" />
              <span className="text-xs text-navy-400">Loading atlas data...</span>
            </div>
          </div>
        )}
        <svg
          ref={svgRef}
          viewBox={`0 0 ${width} ${height}`}
          className="w-full cursor-grab active:cursor-grabbing select-none"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          aria-label="3D PCA projection of spectral data clusters"
        >
          <defs>
            <radialGradient id="bgGrad" cx="50%" cy="50%">
              <stop offset="0%" stopColor="#1a2d43" />
              <stop offset="100%" stopColor="#171f2e" />
            </radialGradient>
          </defs>
          <rect width={width} height={height} fill="url(#bgGrad)" />

          {/* Grid plane at y=0 */}
          {[-3, -2, -1, 0, 1, 2, 3].map((v) => {
            const a = project(v, 0, -3, rotX, rotY, scale, cx, cy);
            const b = project(v, 0, 3, rotX, rotY, scale, cx, cy);
            const c = project(-3, 0, v, rotX, rotY, scale, cx, cy);
            const d = project(3, 0, v, rotX, rotY, scale, cx, cy);
            return (
              <g key={v} opacity={0.15}>
                <line x1={a.px} y1={a.py} x2={b.px} y2={b.py} stroke="#9fb3c8" strokeWidth={0.5} />
                <line x1={c.px} y1={c.py} x2={d.px} y2={d.py} stroke="#9fb3c8" strokeWidth={0.5} />
              </g>
            );
          })}

          {/* Axes */}
          {axes.map((ax) => (
            <g key={ax.label}>
              <line
                x1={origin.px} y1={origin.py}
                x2={ax.end.px} y2={ax.end.py}
                stroke={ax.color} strokeWidth={1.5} opacity={0.6}
              />
              <text
                x={ax.end.px + 4} y={ax.end.py - 4}
                fill={ax.color} fontSize="11" fontFamily="JetBrains Mono, monospace" fontWeight={500}
              >
                {ax.label}
              </text>
            </g>
          ))}

          {/* Data points */}
          {sorted.map((p) => {
            const dimmed = activeFamily !== null && p.family !== activeFamily;
            const isHovered = hoveredIdx === p.idx;
            const depthScale = 0.6 + (p.depth + 4) / 8 * 0.6;
            const r = isHovered ? 7 : 4 * Math.max(0.5, depthScale);

            return (
              <g key={p.idx}>
                {isHovered && (
                  <circle cx={p.px} cy={p.py} r={14} fill={p.color} opacity={0.15} />
                )}
                <circle
                  cx={p.px} cy={p.py} r={r}
                  fill={p.color}
                  opacity={dimmed ? 0.1 : isHovered ? 1 : 0.7 * depthScale}
                  stroke={isHovered ? '#fff' : 'none'}
                  strokeWidth={isHovered ? 1.5 : 0}
                  className="transition-opacity duration-150"
                  onPointerEnter={() => setHoveredIdx(p.idx)}
                  onPointerLeave={() => setHoveredIdx(null)}
                />
              </g>
            );
          })}

          {/* Tooltip */}
          {hoveredIdx !== null && (() => {
            const p = projected[hoveredIdx];
            const tx = Math.min(p.px + 12, width - 160);
            const ty = Math.max(p.py - 40, 16);
            return (
              <g>
                <rect
                  x={tx} y={ty} width={150} height={48} rx={8}
                  fill="#1a2d43" stroke={p.color} strokeWidth={1} opacity={0.95}
                />
                <text x={tx + 8} y={ty + 18} fill="#fff" fontSize="11" fontWeight={600}>
                  {p.compound}
                </text>
                <text x={tx + 8} y={ty + 34} fill="#9fb3c8" fontSize="10" fontFamily="JetBrains Mono, monospace">
                  {p.family}
                </text>
              </g>
            );
          })()}
        </svg>

        {/* Interaction hint */}
        <div className="absolute bottom-3 right-3 flex items-center gap-1.5 rounded-pill bg-navy-900/80 px-3 py-1.5 text-[10px] text-navy-400 backdrop-blur-sm">
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.042 21.672L13.684 16.6m0 0l-2.51 2.225.569-9.47 5.227 7.917-3.286-.672zM12 2.25V4.5m5.834.166l-1.591 1.591M20.25 10.5H18M7.757 14.743l-1.59 1.59M6 10.5H3.75m4.007-4.243l-1.59-1.59" />
          </svg>
          Drag to rotate
        </div>
      </div>

      {/* Stats */}
      <div className="mt-4 flex items-center justify-center gap-6 text-xs text-navy-400">
        <span>
          <span className="font-semibold text-white">{data.length}</span> spectral embeddings
        </span>
        <span>
          <span className="font-semibold text-white">{families.length}</span> clusters
        </span>
        <span className="font-mono">PCA projection</span>
      </div>
    </div>
  );
}
