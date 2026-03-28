'use client';

import { useState } from 'react';

const classes = [
  { name: 'Acrylic/PSA', color: '#3b82f6', auc: 0.52 },
  { name: 'Cyanoacrylate', color: '#8b5cf6', auc: 0.48 },
  { name: 'Epoxy', color: '#f59e0b', auc: 0.45 },
  { name: 'Hot-melt', color: '#ef4444', auc: 0.43 },
  { name: 'Polyurethane', color: '#22c55e', auc: 0.41 },
  { name: 'Rubber-based', color: '#f97316', auc: 0.47 },
  { name: 'Silicone', color: '#14b8a6', auc: 0.46 },
];

function generateROCPath(auc: number): string {
  // Generate a plausible ROC curve given an AUC
  const bulge = (auc - 0.5) * 4; // how far above diagonal
  const points: [number, number][] = [[0, 0]];
  const n = 50;

  for (let i = 1; i <= n; i++) {
    const t = i / n;
    // Parametric curve above diagonal, scaled by AUC
    const fpr = t;
    const tpr = Math.min(
      1,
      t + bulge * Math.sin(Math.PI * t) * (0.5 + 0.5 * t),
    );
    points.push([fpr, tpr]);
  }

  const w = 260;
  const h = 260;
  const pad = 35;
  const pw = w - pad * 2;
  const ph = h - pad * 2;
  const toX = (v: number) => pad + v * pw;
  const toY = (v: number) => pad + ph - v * ph;

  return (
    `M ${toX(points[0][0])} ${toY(points[0][1])} ` +
    points
      .slice(1)
      .map(([x, y]) => `L ${toX(x)} ${toY(y)}`)
      .join(' ')
  );
}

export default function ROCCurves() {
  const [highlighted, setHighlighted] = useState<number | null>(null);
  const w = 260;
  const h = 260;
  const pad = 35;
  const pw = w - pad * 2;
  const ph = h - pad * 2;
  const toX = (v: number) => pad + v * pw;
  const toY = (v: number) => pad + ph - v * ph;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">
          ROC Curves (CNN-1D)
        </h3>
        <span className="text-[10px] text-gray-400">
          Macro AUC: 0.460
        </span>
      </div>

      <svg viewBox={`0 0 ${w} ${h}`} className="mt-3 w-full">
        {/* Grid */}
        {[0.25, 0.5, 0.75].map((v) => (
          <g key={v}>
            <line
              x1={toX(v)}
              x2={toX(v)}
              y1={pad}
              y2={pad + ph}
              stroke="#f3f4f6"
            />
            <line
              x1={pad}
              x2={pad + pw}
              y1={toY(v)}
              y2={toY(v)}
              stroke="#f3f4f6"
            />
          </g>
        ))}

        {/* Axes */}
        <line x1={pad} x2={pad + pw} y1={pad + ph} y2={pad + ph} stroke="#d1d5db" />
        <line x1={pad} x2={pad} y1={pad} y2={pad + ph} stroke="#d1d5db" />

        {/* Axis labels */}
        {[0, 0.5, 1].map((v) => (
          <g key={v}>
            <text
              x={toX(v)}
              y={pad + ph + 14}
              textAnchor="middle"
              fontSize="8"
              className="fill-gray-400"
              fontFamily="JetBrains Mono, monospace"
            >
              {v.toFixed(1)}
            </text>
            <text
              x={pad - 6}
              y={toY(v) + 3}
              textAnchor="end"
              fontSize="8"
              className="fill-gray-400"
              fontFamily="JetBrains Mono, monospace"
            >
              {v.toFixed(1)}
            </text>
          </g>
        ))}
        <text
          x={w / 2}
          y={h - 2}
          textAnchor="middle"
          fontSize="9"
          className="fill-gray-500"
        >
          False Positive Rate
        </text>
        <text
          x={8}
          y={h / 2}
          textAnchor="middle"
          fontSize="9"
          className="fill-gray-500"
          transform={`rotate(-90 8 ${h / 2})`}
        >
          True Positive Rate
        </text>

        {/* Diagonal (random) */}
        <line
          x1={toX(0)}
          y1={toY(0)}
          x2={toX(1)}
          y2={toY(1)}
          stroke="#e5e7eb"
          strokeDasharray="4 2"
        />

        {/* ROC curves */}
        {classes.map((cls, i) => (
          <path
            key={cls.name}
            d={generateROCPath(cls.auc)}
            fill="none"
            stroke={cls.color}
            strokeWidth={highlighted === i ? 2.5 : 1.5}
            opacity={
              highlighted === null || highlighted === i ? 0.85 : 0.2
            }
            onMouseEnter={() => setHighlighted(i)}
            onMouseLeave={() => setHighlighted(null)}
            style={{ cursor: 'pointer', transition: 'opacity 0.15s' }}
          />
        ))}
      </svg>

      {/* Legend */}
      <div className="mt-2 flex flex-wrap justify-center gap-x-3 gap-y-1">
        {classes.map((cls, i) => (
          <button
            key={cls.name}
            onMouseEnter={() => setHighlighted(i)}
            onMouseLeave={() => setHighlighted(null)}
            className="flex items-center gap-1 text-[9px] text-gray-500 transition-colors hover:text-gray-700"
          >
            <span
              className="inline-block h-1.5 w-3 rounded-full"
              style={{ backgroundColor: cls.color }}
            />
            {cls.name}{' '}
            <span className="font-mono text-gray-400">
              ({cls.auc.toFixed(2)})
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
