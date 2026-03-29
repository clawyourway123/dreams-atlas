'use client';

import { useState, useRef } from 'react';

interface ClusterPoint {
  x: number;
  y: number;
  family: string;
  compound: string;
  color: string;
}

const FAMILY_COLORS: Record<string, string> = {
  'Acrylic/PSA': '#3b82f6',
  Cyanoacrylate: '#8b5cf6',
  Epoxy: '#f59e0b',
  'Hot-melt': '#ef4444',
  Polyurethane: '#22c55e',
  'Rubber-based': '#f97316',
  Silicone: '#14b8a6',
};

function generateTSNEData(): ClusterPoint[] {
  const rng = (seed: number) => {
    let s = seed;
    return () => {
      s = (s * 16807 + 0) % 2147483647;
      return s / 2147483647;
    };
  };
  const rand = rng(123);

  const clusters: { family: string; cx: number; cy: number; spread: number; compounds: string[] }[] = [
    { family: 'Acrylic/PSA', cx: 0.18, cy: 0.72, spread: 0.08, compounds: ['Loctite 3090', '3M VHB 4910', 'tesa ACXplus', 'Avery S8000', 'Nitto SPV-224'] },
    { family: 'Cyanoacrylate', cx: 0.78, cy: 0.82, spread: 0.06, compounds: ['Loctite 401', 'Permabond 910', 'Infinity CA+'] },
    { family: 'Epoxy', cx: 0.25, cy: 0.28, spread: 0.09, compounds: ['Araldite AW 106', '3M DP420', 'Henkel EA 9395', 'West System 105'] },
    { family: 'Hot-melt', cx: 0.72, cy: 0.22, spread: 0.07, compounds: ['Technomelt PA 646', 'Thermogrip 4232', 'Fuller HL 6444'] },
    { family: 'Polyurethane', cx: 0.5, cy: 0.5, spread: 0.1, compounds: ['Sikaflex 252', 'Loctite PL Premium', '3M 550'] },
    { family: 'Rubber-based', cx: 0.82, cy: 0.52, spread: 0.07, compounds: ['3M Super 77', 'Grip N Grab', 'DAP Weldwood', 'Elmer\'s Rubber'] },
    { family: 'Silicone', cx: 0.35, cy: 0.85, spread: 0.06, compounds: ['Dow 732', 'GE Silicone II', 'Permatex Ultra'] },
  ];

  const points: ClusterPoint[] = [];
  for (const cl of clusters) {
    const n = 8 + Math.floor(rand() * 10);
    for (let i = 0; i < n; i++) {
      const angle = rand() * Math.PI * 2;
      const radius = rand() * cl.spread;
      points.push({
        x: cl.cx + Math.cos(angle) * radius,
        y: cl.cy + Math.sin(angle) * radius,
        family: cl.family,
        compound: cl.compounds[Math.floor(rand() * cl.compounds.length)],
        color: FAMILY_COLORS[cl.family],
      });
    }
  }
  return points;
}

export default function ClusteringViz() {
  const data = useRef(generateTSNEData()).current;
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [selectedFamily, setSelectedFamily] = useState<string | null>(null);

  const width = 640;
  const height = 480;
  const padding = 40;
  const plotW = width - padding * 2;
  const plotH = height - padding * 2;

  const toX = (v: number) => padding + v * plotW;
  const toY = (v: number) => padding + (1 - v) * plotH;

  // Compute cluster centroids for labels
  const centroids = Object.keys(FAMILY_COLORS).map((family) => {
    const pts = data.filter((d) => d.family === family);
    const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
    const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length;
    return { family, cx: toX(cx), cy: toY(cy), color: FAMILY_COLORS[family] };
  });

  // Compute convex hull approximation (bounding ellipse)
  const ellipses = Object.keys(FAMILY_COLORS).map((family) => {
    const pts = data.filter((d) => d.family === family);
    const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
    const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length;
    const rx = Math.max(...pts.map((p) => Math.abs(p.x - cx))) * 1.3;
    const ry = Math.max(...pts.map((p) => Math.abs(p.y - cy))) * 1.3;
    return {
      family,
      cx: toX(cx),
      cy: toY(cy),
      rx: rx * plotW,
      ry: ry * plotH,
      color: FAMILY_COLORS[family],
    };
  });

  return (
    <div>
      {/* Method toggle */}
      <div className="mb-4 flex items-center justify-center gap-3">
        <span className="text-xs font-medium text-navy-400">Dimensionality Reduction:</span>
        <div className="flex rounded-card border border-white/10 bg-surface/40 p-0.5">
          <button className="rounded-lg bg-teal-500/20 px-3 py-1.5 text-xs font-medium text-teal-400">
            t-SNE
          </button>
          <button className="rounded-lg px-3 py-1.5 text-xs font-medium text-navy-400 hover:text-navy-200">
            UMAP
          </button>
        </div>
      </div>

      {/* Visualization */}
      <div className="mx-auto overflow-hidden rounded-panel border border-white/5 bg-navy-950/80 shadow-card">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full"
          aria-label="t-SNE clustering visualization of spectral similarity"
        >
          <defs>
            <radialGradient id="clusterBg" cx="50%" cy="50%">
              <stop offset="0%" stopColor="#1a2d43" />
              <stop offset="100%" stopColor="#171f2e" />
            </radialGradient>
          </defs>
          <rect width={width} height={height} fill="url(#clusterBg)" />

          {/* Grid */}
          {[0.2, 0.4, 0.6, 0.8].map((v) => (
            <g key={v} opacity={0.08}>
              <line x1={toX(v)} y1={padding} x2={toX(v)} y2={height - padding} stroke="#9fb3c8" strokeDasharray="4 4" />
              <line x1={padding} y1={toY(v)} x2={width - padding} y2={toY(v)} stroke="#9fb3c8" strokeDasharray="4 4" />
            </g>
          ))}

          {/* Cluster ellipses */}
          {ellipses.map((e) => (
            <ellipse
              key={e.family}
              cx={e.cx} cy={e.cy} rx={e.rx} ry={e.ry}
              fill={e.color}
              opacity={selectedFamily === null || selectedFamily === e.family ? 0.06 : 0.01}
              stroke={e.color}
              strokeWidth={1}
              strokeOpacity={selectedFamily === null || selectedFamily === e.family ? 0.2 : 0.05}
              strokeDasharray="4 4"
              className="transition-opacity duration-200"
            />
          ))}

          {/* Data points */}
          {data.map((p, i) => {
            const dimmed = selectedFamily !== null && p.family !== selectedFamily;
            const isHovered = hoveredIdx === i;
            return (
              <g key={i}>
                {isHovered && (
                  <circle cx={toX(p.x)} cy={toY(p.y)} r={12} fill={p.color} opacity={0.15} />
                )}
                <circle
                  cx={toX(p.x)}
                  cy={toY(p.y)}
                  r={isHovered ? 6 : 4}
                  fill={p.color}
                  opacity={dimmed ? 0.1 : isHovered ? 1 : 0.7}
                  stroke={isHovered ? '#fff' : 'none'}
                  strokeWidth={1.5}
                  className="transition-opacity duration-150"
                  onPointerEnter={() => setHoveredIdx(i)}
                  onPointerLeave={() => setHoveredIdx(null)}
                />
              </g>
            );
          })}

          {/* Cluster labels */}
          {centroids.map((c) => (
            <text
              key={c.family}
              x={c.cx} y={c.cy - 18}
              textAnchor="middle"
              fill={c.color}
              fontSize="10"
              fontWeight={600}
              fontFamily="Inter, system-ui, sans-serif"
              opacity={selectedFamily === null || selectedFamily === c.family ? 0.8 : 0.15}
              className="transition-opacity duration-200"
            >
              {c.family}
            </text>
          ))}

          {/* Axes labels */}
          <text x={width / 2} y={height - 8} textAnchor="middle" fill="#829ab1" fontSize="10" fontFamily="JetBrains Mono, monospace">
            t-SNE Dimension 1
          </text>
          <text x={14} y={height / 2} textAnchor="middle" fill="#829ab1" fontSize="10" fontFamily="JetBrains Mono, monospace" transform={`rotate(-90 14 ${height / 2})`}>
            t-SNE Dimension 2
          </text>

          {/* Tooltip */}
          {hoveredIdx !== null && (() => {
            const p = data[hoveredIdx];
            const tx = Math.min(toX(p.x) + 12, width - 155);
            const ty = Math.max(toY(p.y) - 40, 16);
            return (
              <g>
                <rect x={tx} y={ty} width={145} height={48} rx={8} fill="#1a2d43" stroke={p.color} strokeWidth={1} opacity={0.95} />
                <text x={tx + 8} y={ty + 18} fill="#fff" fontSize="11" fontWeight={600}>{p.compound}</text>
                <text x={tx + 8} y={ty + 34} fill="#9fb3c8" fontSize="10" fontFamily="JetBrains Mono, monospace">{p.family}</text>
              </g>
            );
          })()}
        </svg>
      </div>

      {/* Family filter */}
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {Object.entries(FAMILY_COLORS).map(([family, color]) => {
          const count = data.filter((d) => d.family === family).length;
          return (
            <button
              key={family}
              onClick={() => setSelectedFamily(selectedFamily === family ? null : family)}
              className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-all ${
                selectedFamily === null || selectedFamily === family
                  ? 'border-white/10 text-white'
                  : 'border-white/5 text-navy-500'
              }`}
            >
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
              {family}
              <span className="text-navy-500">{count}</span>
            </button>
          );
        })}
      </div>

      {/* Stats */}
      <div className="mt-3 flex items-center justify-center gap-6 text-xs text-navy-400">
        <span><span className="font-semibold text-white">{data.length}</span> embeddings</span>
        <span><span className="font-semibold text-white">7</span> clusters</span>
        <span className="font-mono">perplexity=30</span>
      </div>
    </div>
  );
}
