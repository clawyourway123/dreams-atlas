"use client";

import React, { useState, useMemo, useCallback } from "react";
import dynamic from "next/dynamic";
import type { SpectrumRow } from "./SpectralPlotViewer";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface ClassificationDemoProps {
  spectra: SpectrumRow[];
  classes: string[];
  height?: number;
}

const CLASS_COLORS: Record<string, string> = {
  "Acrylic/PSA": "#1f77b4",
  Cyanoacrylate: "#ff7f0e",
  Epoxy: "#2ca02c",
  "Hot-melt": "#d62728",
  Polyurethane: "#9467bd",
  "Rubber-based": "#8c564b",
  Silicone: "#e377c2",
};

function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0,
    magA = 0,
    magB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }
  return magA && magB ? dot / (Math.sqrt(magA) * Math.sqrt(magB)) : 0;
}

function classifySpectrum(
  target: SpectrumRow,
  library: SpectrumRow[],
  classes: string[],
): { scores: Record<string, number>; predicted: string; topMatches: { compound: string; cls: string; score: number }[] } {
  const classSims: Record<string, number[]> = {};
  const allMatches: { compound: string; cls: string; score: number }[] = [];

  for (const ref of library) {
    if (ref.spectrum_id === target.spectrum_id) continue;
    if (ref.spectral_type !== target.spectral_type) continue;
    const sim = cosineSimilarity(target.intensities, ref.intensities);
    (classSims[ref.adhesive_class] ??= []).push(sim);
    allMatches.push({ compound: ref.compound_name, cls: ref.adhesive_class, score: sim });
  }

  const scores: Record<string, number> = {};
  let maxScore = -1;
  let predicted = classes[0];

  for (const cls of classes) {
    const sims = classSims[cls] || [];
    // Use top-5 mean similarity as class score
    const top = sims.sort((a, b) => b - a).slice(0, 5);
    const avg = top.length ? top.reduce((s, v) => s + v, 0) / top.length : 0;
    scores[cls] = avg;
    if (avg > maxScore) {
      maxScore = avg;
      predicted = cls;
    }
  }

  const topMatches = allMatches.sort((a, b) => b.score - a.score).slice(0, 5);
  return { scores, predicted, topMatches };
}

export default function ClassificationDemo({
  spectra,
  classes,
  height = 420,
}: ClassificationDemoProps) {
  const compounds = useMemo(() => {
    const seen = new Map<string, SpectrumRow>();
    for (const s of spectra) {
      if (!seen.has(s.compound_name)) seen.set(s.compound_name, s);
    }
    return [...seen.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [spectra]);

  const [selectedCompound, setSelectedCompound] = useState(
    compounds[0]?.[0] || "",
  );

  const selected = useMemo(
    () => spectra.find((s) => s.compound_name === selectedCompound) || null,
    [spectra, selectedCompound],
  );

  const result = useMemo(() => {
    if (!selected) return null;
    return classifySpectrum(selected, spectra, classes);
  }, [selected, spectra, classes]);

  const handleRandom = useCallback(() => {
    const idx = Math.floor(Math.random() * compounds.length);
    setSelectedCompound(compounds[idx][0]);
  }, [compounds]);

  if (!selected || !result) return null;

  const isCorrect = result.predicted === selected.adhesive_class;

  // Confidence bar chart
  const sortedClasses = [...classes].sort(
    (a, b) => (result.scores[b] || 0) - (result.scores[a] || 0),
  );
  const barTrace: Plotly.Data = {
    y: sortedClasses,
    x: sortedClasses.map((c) => (result.scores[c] || 0) * 100),
    type: "bar" as const,
    orientation: "h" as const,
    marker: {
      color: sortedClasses.map((c) =>
        c === result.predicted ? CLASS_COLORS[c] : "#d1d5db",
      ),
    },
    hovertemplate: "<b>%{y}</b><br>Score: %{x:.1f}%<extra></extra>",
  };

  // Spectrum trace
  const spectrumTrace: Plotly.Data = {
    x: selected.wavenumbers,
    y: selected.intensities,
    type: "scatter" as const,
    mode: "lines" as const,
    line: { color: CLASS_COLORS[selected.adhesive_class], width: 2 },
    hovertemplate: "%{x:.0f} cm\u207b\u00b9<br>Intensity: %{y:.3f}<extra></extra>",
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold text-gray-900">
        Classification Demo
      </h2>

      {/* Compound selector */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <select
          value={selectedCompound}
          onChange={(e) => setSelectedCompound(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
        >
          {compounds.map(([name]) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
        <button
          onClick={handleRandom}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700"
        >
          Random Sample
        </button>
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-semibold ${
              isCorrect
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            {isCorrect ? "\u2713" : "\u2717"}{" "}
            {isCorrect ? "Correct" : "Incorrect"}
          </span>
        </div>
      </div>

      {/* Info row */}
      <div className="mb-4 flex flex-wrap gap-4 text-sm">
        <span>
          <span className="text-gray-500">True class:</span>{" "}
          <span
            className="font-semibold"
            style={{ color: CLASS_COLORS[selected.adhesive_class] }}
          >
            {selected.adhesive_class}
          </span>
        </span>
        <span>
          <span className="text-gray-500">Predicted:</span>{" "}
          <span
            className="font-semibold"
            style={{ color: CLASS_COLORS[result.predicted] }}
          >
            {result.predicted}
          </span>
        </span>
        <span>
          <span className="text-gray-500">Type:</span>{" "}
          <span className="font-medium">{selected.spectral_type}</span>
        </span>
      </div>

      {/* Two-column layout: spectrum + confidence */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-100 bg-gray-50 p-2">
          <Plot
            data={[spectrumTrace]}
            layout={{
              height: height,
              margin: { t: 30, r: 15, b: 55, l: 60 },
              title: {
                text: `${selected.compound_name} (${selected.spectral_type})`,
                font: { size: 12 },
                y: 0.98,
              },
              xaxis: {
                title: { text: "Wavenumber (cm\u207b\u00b9)", font: { size: 11 } },
                autorange: "reversed" as const,
                gridcolor: "#f0f0f0",
              },
              yaxis: {
                title: { text: "Intensity", font: { size: 11 } },
                gridcolor: "#f0f0f0",
              },
              plot_bgcolor: "white",
              paper_bgcolor: "transparent",
              showlegend: false,
              font: { family: "Inter, system-ui, sans-serif" },
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: "100%" }}
          />
        </div>

        <div className="rounded-lg border border-gray-100 bg-gray-50 p-2">
          <Plot
            data={[barTrace]}
            layout={{
              height: height,
              margin: { t: 30, r: 25, b: 40, l: 120 },
              title: {
                text: "Classification Confidence",
                font: { size: 12 },
                y: 0.98,
              },
              xaxis: {
                title: { text: "Similarity Score (%)", font: { size: 11 } },
                range: [0, 100],
              },
              plot_bgcolor: "white",
              paper_bgcolor: "transparent",
              showlegend: false,
              font: { family: "Inter, system-ui, sans-serif" },
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: "100%" }}
          />
        </div>
      </div>

      {/* Top matches table */}
      <div className="mt-4">
        <h3 className="mb-2 text-sm font-semibold text-gray-700">
          Top 5 Nearest Spectra
        </h3>
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-2">Rank</th>
                <th className="px-4 py-2">Compound</th>
                <th className="px-4 py-2">Class</th>
                <th className="px-4 py-2">Similarity</th>
              </tr>
            </thead>
            <tbody>
              {result.topMatches.map((m, i) => (
                <tr key={i} className="border-t border-gray-100">
                  <td className="px-4 py-2 text-gray-600">{i + 1}</td>
                  <td className="px-4 py-2 font-medium text-gray-800">
                    {m.compound}
                  </td>
                  <td className="px-4 py-2">
                    <span
                      className="rounded-full px-2 py-0.5 text-xs font-medium text-white"
                      style={{ backgroundColor: CLASS_COLORS[m.cls] }}
                    >
                      {m.cls}
                    </span>
                  </td>
                  <td className="px-4 py-2 font-mono text-gray-700">
                    {(m.score * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
