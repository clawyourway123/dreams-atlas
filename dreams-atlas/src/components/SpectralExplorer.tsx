'use client';

import { useState } from 'react';

const adhesiveClasses = [
  {
    name: 'Acrylic/PSA',
    color: '#3b82f6',
    samples: 216,
    peaks: [
      { x: 1730, label: 'C=O stretch', intensity: 0.92 },
      { x: 1160, label: 'C-O-C', intensity: 0.78 },
      { x: 2950, label: 'C-H stretch', intensity: 0.65 },
      { x: 1450, label: 'C-H bend', intensity: 0.55 },
      { x: 1380, label: 'CH₃ sym', intensity: 0.42 },
    ],
  },
  {
    name: 'Cyanoacrylate',
    color: '#8b5cf6',
    samples: 101,
    peaks: [
      { x: 2240, label: 'C≡N stretch', intensity: 0.95 },
      { x: 1740, label: 'C=O stretch', intensity: 0.88 },
      { x: 1620, label: 'C=C stretch', intensity: 0.72 },
      { x: 1280, label: 'C-O stretch', intensity: 0.58 },
      { x: 1060, label: 'C-O-C', intensity: 0.45 },
    ],
  },
  {
    name: 'Epoxy',
    color: '#f59e0b',
    samples: 140,
    peaks: [
      { x: 915, label: 'Epoxide ring', intensity: 0.90 },
      { x: 3400, label: 'O-H stretch', intensity: 0.75 },
      { x: 1610, label: 'Aromatic C=C', intensity: 0.82 },
      { x: 1250, label: 'C-O stretch', intensity: 0.68 },
      { x: 830, label: 'Aromatic C-H', intensity: 0.55 },
    ],
  },
  {
    name: 'Hot-melt',
    color: '#ef4444',
    samples: 128,
    peaks: [
      { x: 2920, label: 'C-H asym', intensity: 0.94 },
      { x: 2850, label: 'C-H sym', intensity: 0.88 },
      { x: 1470, label: 'C-H deform', intensity: 0.72 },
      { x: 720, label: 'CH₂ rock', intensity: 0.62 },
      { x: 1740, label: 'C=O (EVA)', intensity: 0.50 },
    ],
  },
  {
    name: 'Polyurethane',
    color: '#22c55e',
    samples: 96,
    peaks: [
      { x: 3330, label: 'N-H stretch', intensity: 0.85 },
      { x: 1730, label: 'C=O stretch', intensity: 0.92 },
      { x: 1540, label: 'N-H bend', intensity: 0.78 },
      { x: 1220, label: 'C-N stretch', intensity: 0.65 },
      { x: 2270, label: 'NCO (free)', intensity: 0.35 },
    ],
  },
  {
    name: 'Rubber-based',
    color: '#f97316',
    samples: 140,
    peaks: [
      { x: 2920, label: 'C-H stretch', intensity: 0.88 },
      { x: 1660, label: 'C=C stretch', intensity: 0.82 },
      { x: 1450, label: 'C-H bend', intensity: 0.70 },
      { x: 840, label: '=C-H wag', intensity: 0.75 },
      { x: 1380, label: 'CH₃ deform', intensity: 0.52 },
    ],
  },
  {
    name: 'Silicone',
    color: '#14b8a6',
    samples: 134,
    peaks: [
      { x: 1020, label: 'Si-O-Si asym', intensity: 0.96 },
      { x: 1260, label: 'Si-CH₃', intensity: 0.88 },
      { x: 800, label: 'Si-C stretch', intensity: 0.82 },
      { x: 2960, label: 'C-H stretch', intensity: 0.55 },
      { x: 490, label: 'Si-O-Si bend', intensity: 0.65 },
    ],
  },
];

function generateSpectrumPath(
  peaks: { x: number; intensity: number }[],
  width: number,
  height: number,
): string {
  const xMin = 400;
  const xMax = 4000;
  const padding = 40;
  const plotW = width - padding * 2;
  const plotH = height - padding * 2;
  const toX = (wn: number) => padding + ((xMax - wn) / (xMax - xMin)) * plotW;
  const toY = (i: number) => padding + plotH - i * plotH;

  const points: [number, number][] = [];
  const numPoints = 200;

  for (let j = 0; j <= numPoints; j++) {
    const wn = xMin + (j / numPoints) * (xMax - xMin);
    let intensity = 0.03 + Math.random() * 0.02; // baseline noise
    for (const peak of peaks) {
      const sigma = 30 + Math.random() * 15;
      const dist = (wn - peak.x) / sigma;
      intensity += peak.intensity * Math.exp(-0.5 * dist * dist);
    }
    points.push([toX(wn), toY(Math.min(intensity, 1))]);
  }

  return (
    `M ${points[0][0]} ${points[0][1]} ` +
    points
      .slice(1)
      .map(([x, y]) => `L ${x} ${y}`)
      .join(' ')
  );
}

export default function SpectralExplorer() {
  const [selected, setSelected] = useState(0);
  const cls = adhesiveClasses[selected];
  const width = 700;
  const height = 300;
  const path = generateSpectrumPath(cls.peaks, width, height);

  const padding = 40;
  const plotW = width - padding * 2;
  const plotH = height - padding * 2;
  const xMin = 400;
  const xMax = 4000;
  const toX = (wn: number) => padding + ((xMax - wn) / (xMax - xMin)) * plotW;
  const toY = (i: number) => padding + plotH - i * plotH;

  return (
    <div>
      {/* Class selector pills */}
      <div className="flex flex-wrap justify-center gap-2">
        {adhesiveClasses.map((ac, i) => (
          <button
            key={ac.name}
            onClick={() => setSelected(i)}
            className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-all ${
              i === selected
                ? 'border-transparent shadow-sm text-white'
                : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
            }`}
            style={i === selected ? { backgroundColor: ac.color } : undefined}
          >
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: ac.color }}
            />
            {ac.name}
          </button>
        ))}
      </div>

      {/* Spectrum plot */}
      <div className="mx-auto mt-6 overflow-hidden rounded-xl border border-gray-200 bg-white">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full"
          aria-label={`Representative spectrum for ${cls.name} adhesive class`}
        >
          {/* Grid lines */}
          {[0.2, 0.4, 0.6, 0.8].map((v) => (
            <line
              key={v}
              x1={padding}
              x2={width - padding}
              y1={toY(v)}
              y2={toY(v)}
              stroke="#e5e7eb"
              strokeDasharray="4 4"
            />
          ))}
          {[1000, 1500, 2000, 2500, 3000, 3500].map((wn) => (
            <line
              key={wn}
              x1={toX(wn)}
              x2={toX(wn)}
              y1={padding}
              y2={height - padding}
              stroke="#e5e7eb"
              strokeDasharray="4 4"
            />
          ))}

          {/* Axes */}
          <line
            x1={padding}
            x2={width - padding}
            y1={height - padding}
            y2={height - padding}
            stroke="#9ca3af"
          />
          <line
            x1={padding}
            x2={padding}
            y1={padding}
            y2={height - padding}
            stroke="#9ca3af"
          />

          {/* Axis labels */}
          {[500, 1000, 1500, 2000, 2500, 3000, 3500, 4000].map((wn) => (
            <text
              key={wn}
              x={toX(wn)}
              y={height - padding + 16}
              textAnchor="middle"
              className="fill-gray-400"
              fontSize="9"
              fontFamily="JetBrains Mono, monospace"
            >
              {wn}
            </text>
          ))}
          <text
            x={width / 2}
            y={height - 4}
            textAnchor="middle"
            className="fill-gray-500"
            fontSize="10"
          >
            Wavenumber (cm⁻¹)
          </text>
          <text
            x={12}
            y={height / 2}
            textAnchor="middle"
            className="fill-gray-500"
            fontSize="10"
            transform={`rotate(-90 12 ${height / 2})`}
          >
            Intensity
          </text>

          {/* Spectrum path */}
          <path
            d={path}
            fill="none"
            stroke={cls.color}
            strokeWidth={2}
            opacity={0.9}
          />

          {/* Peak annotations */}
          {cls.peaks
            .filter((p) => p.intensity > 0.5)
            .map((p) => (
              <g key={p.x}>
                <circle
                  cx={toX(p.x)}
                  cy={toY(p.intensity)}
                  r={3}
                  fill={cls.color}
                />
                <text
                  x={toX(p.x)}
                  y={toY(p.intensity) - 8}
                  textAnchor="middle"
                  fontSize="8"
                  className="fill-gray-500"
                  fontFamily="JetBrains Mono, monospace"
                >
                  {p.label}
                </text>
              </g>
            ))}
        </svg>
      </div>

      {/* Info bar */}
      <div className="mt-4 flex items-center justify-center gap-6 text-xs text-gray-500">
        <span>
          <span className="font-semibold text-gray-700">{cls.samples}</span>{' '}
          samples
        </span>
        <span>
          <span className="font-semibold text-gray-700">{cls.peaks.length}</span>{' '}
          characteristic peaks
        </span>
        <span className="font-mono">400–4000 cm⁻¹</span>
      </div>
    </div>
  );
}
