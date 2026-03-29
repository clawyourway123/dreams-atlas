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

// Confusion data reflecting 100% accuracy from compound-grouped CV
// Perfect classification: all predictions on the diagonal
const cnnMatrix = [
  [1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
  [0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00],
  [0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00],
  [0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00],
  [0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00],
  [0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00],
  [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00],
];

const rfMatrix = [
  [1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
  [0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00],
  [0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00],
  [0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00],
  [0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00],
  [0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00],
  [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00],
];

function cellColor(value: number, isDiagonal: boolean): string {
  if (isDiagonal) {
    const alpha = Math.min(value, 1);
    return `rgba(45, 212, 191, ${0.1 + alpha * 0.5})`;
  }
  if (value === 0) return 'rgba(255, 255, 255, 0.02)';
  const alpha = Math.min(value / 0.2, 1);
  return `rgba(239, 68, 68, ${alpha * 0.25})`;
}

export default function ConfusionMatrix() {
  const [model, setModel] = useState<'cnn' | 'rf'>('cnn');
  const matrix = model === 'cnn' ? cnnMatrix : rfMatrix;
  const [hoveredCell, setHoveredCell] = useState<[number, number] | null>(null);

  return (
    <div className="rounded-panel border border-white/5 bg-surface/60 p-5 backdrop-blur-sm shadow-card">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">Confusion Matrix</h3>
        <div className="flex gap-1 rounded-lg bg-navy-900/60 p-0.5">
          <button
            onClick={() => setModel('cnn')}
            className={`rounded-md px-3 py-1 text-xs font-medium transition-all ${
              model === 'cnn'
                ? 'bg-teal-500/20 text-teal-400 shadow-sm'
                : 'text-navy-400 hover:text-navy-200'
            }`}
          >
            CNN-1D
          </button>
          <button
            onClick={() => setModel('rf')}
            className={`rounded-md px-3 py-1 text-xs font-medium transition-all ${
              model === 'rf'
                ? 'bg-teal-500/20 text-teal-400 shadow-sm'
                : 'text-navy-400 hover:text-navy-200'
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
                        isHovered ? 'ring-1 ring-teal-400/50' : ''
                      }`}
                      style={{
                        backgroundColor: cellColor(val, i === j),
                        height: 32,
                      }}
                    >
                      <span
                        className={`font-mono text-[10px] ${
                          i === j ? 'font-bold text-teal-300' : 'text-navy-500'
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

      <div className="mt-3 flex items-center justify-between text-[10px] text-navy-500">
        <span>Rows: True class | Columns: Predicted class</span>
        <span>Compound-grouped 5-fold CV</span>
      </div>
    </div>
  );
}
