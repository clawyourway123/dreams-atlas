'use client';

import { useState } from 'react';

const classes = [
  'Acrylic/PSA',
  'Cyano.',
  'Epoxy',
  'Hot-melt',
  'PU',
  'Rubber',
  'Silicone',
];

const classColors = [
  '#3b82f6',
  '#8b5cf6',
  '#f59e0b',
  '#ef4444',
  '#22c55e',
  '#f97316',
  '#14b8a6',
];

// Representative confusion data from CNN-1D compound-grouped CV
// Rows = true, Cols = predicted. Values are approximate proportions.
const cnnMatrix = [
  [0.18, 0.12, 0.14, 0.16, 0.10, 0.15, 0.15],
  [0.10, 0.16, 0.13, 0.12, 0.15, 0.18, 0.16],
  [0.14, 0.11, 0.15, 0.13, 0.14, 0.17, 0.16],
  [0.15, 0.13, 0.12, 0.14, 0.16, 0.14, 0.16],
  [0.12, 0.15, 0.16, 0.14, 0.12, 0.15, 0.16],
  [0.16, 0.14, 0.13, 0.15, 0.13, 0.15, 0.14],
  [0.13, 0.12, 0.15, 0.14, 0.16, 0.13, 0.17],
];

const rfMatrix = [
  [0.14, 0.14, 0.15, 0.15, 0.13, 0.14, 0.15],
  [0.15, 0.12, 0.14, 0.14, 0.16, 0.15, 0.14],
  [0.14, 0.15, 0.11, 0.14, 0.15, 0.16, 0.15],
  [0.13, 0.14, 0.16, 0.13, 0.14, 0.15, 0.15],
  [0.16, 0.15, 0.14, 0.13, 0.10, 0.16, 0.16],
  [0.14, 0.14, 0.15, 0.16, 0.14, 0.13, 0.14],
  [0.14, 0.16, 0.15, 0.15, 0.14, 0.13, 0.13],
];

function cellColor(value: number, isDiagonal: boolean): string {
  if (isDiagonal) {
    const alpha = Math.min(value / 0.25, 1);
    return `rgba(26, 110, 245, ${0.15 + alpha * 0.6})`;
  }
  const alpha = Math.min(value / 0.2, 1);
  return `rgba(239, 68, 68, ${alpha * 0.25})`;
}

export default function ConfusionMatrix() {
  const [model, setModel] = useState<'cnn' | 'rf'>('cnn');
  const matrix = model === 'cnn' ? cnnMatrix : rfMatrix;
  const [hoveredCell, setHoveredCell] = useState<[number, number] | null>(null);

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Confusion Matrix</h3>
        <div className="flex gap-1 rounded-lg bg-gray-100 p-0.5">
          <button
            onClick={() => setModel('cnn')}
            className={`rounded-md px-3 py-1 text-xs font-medium transition-all ${
              model === 'cnn'
                ? 'bg-white text-primary-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            CNN-1D
          </button>
          <button
            onClick={() => setModel('rf')}
            className={`rounded-md px-3 py-1 text-xs font-medium transition-all ${
              model === 'rf'
                ? 'bg-white text-primary-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Random Forest
          </button>
        </div>
      </div>

      <div className="mt-4 overflow-x-auto">
        <div className="min-w-[320px]">
          {/* Column headers */}
          <div className="ml-16 flex">
            {classes.map((c, i) => (
              <div
                key={c}
                className="flex-1 text-center"
                style={{ minWidth: 36 }}
              >
                <span
                  className="inline-block text-[9px] font-medium leading-tight"
                  style={{ color: classColors[i] }}
                >
                  {c}
                </span>
              </div>
            ))}
          </div>

          {/* Matrix rows */}
          {matrix.map((row, i) => (
            <div key={i} className="flex items-center">
              <div className="w-16 pr-2 text-right">
                <span
                  className="text-[9px] font-medium"
                  style={{ color: classColors[i] }}
                >
                  {classes[i]}
                </span>
              </div>
              {row.map((val, j) => {
                const isHovered =
                  hoveredCell !== null &&
                  (hoveredCell[0] === i || hoveredCell[1] === j);
                return (
                  <div
                    key={j}
                    className="flex-1 p-0.5"
                    style={{ minWidth: 36 }}
                    onMouseEnter={() => setHoveredCell([i, j])}
                    onMouseLeave={() => setHoveredCell(null)}
                  >
                    <div
                      className={`flex items-center justify-center rounded transition-all ${
                        isHovered ? 'ring-1 ring-primary-400' : ''
                      }`}
                      style={{
                        backgroundColor: cellColor(val, i === j),
                        height: 32,
                      }}
                    >
                      <span
                        className={`font-mono text-[10px] ${
                          i === j ? 'font-bold text-primary-900' : 'text-gray-600'
                        }`}
                      >
                        {(val * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between text-[10px] text-gray-400">
        <span>Rows: True class | Columns: Predicted class</span>
        <span>Compound-grouped 5-fold CV</span>
      </div>
    </div>
  );
}
