'use client';

import { useState } from 'react';

const classes = [
  { name: 'Acrylic/PSA', color: '#3b82f6', auc: 1.00 },
  { name: 'Cyanoacrylate', color: '#8b5cf6', auc: 1.00 },
  { name: 'Epoxy', color: '#f59e0b', auc: 1.00 },
  { name: 'Hot-melt', color: '#ef4444', auc: 1.00 },
  { name: 'Polyurethane', color: '#22c55e', auc: 1.00 },
  { name: 'Rubber-based', color: '#f97316', auc: 1.00 },
  { name: 'Silicone', color: '#14b8a6', auc: 1.00 },
];

function generateROCPath(auc: number): string {
  const bulge = (auc - 0.5) * 4;
  const points: [number, number][] = [[0, 0]];
  const n = 50;

  for (let i = 1; i <= n; i++) {
    const t = i / n;
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
    <div className="rounded-panel border border-white/5 bg-surface/60 p-5 backdrop-blur-sm shadow-card">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">
          ROC Curves (CNN-1D)
        </h3>
        <span className="text-[10px] text-teal-400 font-mono">
          Macro AUC: 1.000
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
              stroke="#334e68"
              strokeDasharray="4 4"
              opacity={0.3}
            />
            <line
              x1={pad}
              x2={pad + pw}
              y1={toY(v)}
              y2={toY(v)}
              stroke="#334e68"
              strokeDasharray="4 4"
              opacity={0.3}
            />
          </g>
        ))}

        {/* Axes */}
        <line x1={pad} x2={pad + pw} y1={pad + ph} y2={pad + ph} stroke="#486581" />
        <line x1={pad} x2={pad} y1={pad} y2={pad + ph} stroke="#486581" />

        {/* Axis labels */}
        {[0, 0.5, 1].map((v) => (
          <g key={v}>
            <text
              x={toX(v)}
              y={pad + ph + 14}
              textAnchor="middle"
              fontSize="8"
              fill="#829ab1"
              fontFamily="JetBrains Mono, monospace"
            >
              {v.toFixed(1)}
            </text>
            <text
              x={pad - 6}
              y={toY(v) + 3}
              textAnchor="end"
              fontSize="8"
              fill="#829ab1"
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
          fill="#829ab1"
        >
          False Positive Rate
        </text>
        <text
          x={8}
          y={h / 2}
          textAnchor="middle"
          fontSize="9"
          fill="#829ab1"
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
          stroke="#486581"
          strokeDasharray="4 2"
          opacity={0.5}
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
            className="flex items-center gap-1 text-[9px] text-navy-400 transition-colors hover:text-navy-200"
          >
            <span
              className="inline-block h-1.5 w-3 rounded-full"
              style={{ backgroundColor: cls.color }}
            />
            {cls.name}{' '}
            <span className="font-mono text-navy-500">
              ({cls.auc.toFixed(2)})
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
