"use client";

import React, { useState, useMemo, useCallback } from "react";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export interface SpectrumRow {
  spectrum_id: string;
  compound_name: string;
  adhesive_class: string;
  spectral_type: "IR" | "FTIR" | "Raman";
  wavenumbers: number[];
  intensities: number[];
}

interface SpectralPlotViewerProps {
  spectra: SpectrumRow[];
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

export default function SpectralPlotViewer({
  spectra,
  height = 520,
}: SpectralPlotViewerProps) {
  const allClasses = useMemo(
    () => [...new Set(spectra.map((s) => s.adhesive_class))].sort(),
    [spectra],
  );
  const allTypes = useMemo(
    () => [...new Set(spectra.map((s) => s.spectral_type))].sort(),
    [spectra],
  );

  const [selectedClasses, setSelectedClasses] = useState<Set<string>>(
    new Set(allClasses),
  );
  const [selectedType, setSelectedType] = useState<string>(allTypes[0] || "IR");
  const [showMean, setShowMean] = useState(true);
  const [showIndividual, setShowIndividual] = useState(false);

  const toggleClass = useCallback((cls: string) => {
    setSelectedClasses((prev) => {
      const next = new Set(prev);
      if (next.has(cls)) next.delete(cls);
      else next.add(cls);
      return next;
    });
  }, []);

  const filtered = useMemo(
    () =>
      spectra.filter(
        (s) =>
          selectedClasses.has(s.adhesive_class) &&
          s.spectral_type === selectedType,
      ),
    [spectra, selectedClasses, selectedType],
  );

  const meanByClass = useMemo(() => {
    const groups: Record<string, SpectrumRow[]> = {};
    for (const s of filtered) {
      (groups[s.adhesive_class] ??= []).push(s);
    }
    return Object.entries(groups).map(([cls, rows]) => {
      const wn = rows[0].wavenumbers;
      const mean = wn.map((_, i) => {
        const sum = rows.reduce((acc, r) => acc + r.intensities[i], 0);
        return sum / rows.length;
      });
      return { cls, wn, mean, count: rows.length };
    });
  }, [filtered]);

  const traces: Plotly.Data[] = [];

  if (showIndividual) {
    for (const s of filtered) {
      traces.push({
        x: s.wavenumbers,
        y: s.intensities,
        type: "scatter" as const,
        mode: "lines" as const,
        name: s.compound_name,
        line: { color: CLASS_COLORS[s.adhesive_class], width: 0.5 },
        opacity: 0.25,
        legendgroup: s.adhesive_class,
        showlegend: false,
        hovertemplate: `<b>${s.compound_name}</b><br>%{x:.0f} cm⁻¹<br>Intensity: %{y:.3f}<extra>${s.adhesive_class}</extra>`,
      });
    }
  }

  if (showMean) {
    for (const { cls, wn, mean, count } of meanByClass) {
      traces.push({
        x: wn,
        y: mean,
        type: "scatter" as const,
        mode: "lines" as const,
        name: `${cls} (n=${count})`,
        line: { color: CLASS_COLORS[cls], width: 2.5 },
        legendgroup: cls,
        hovertemplate: `<b>${cls}</b><br>%{x:.0f} cm⁻¹<br>Mean intensity: %{y:.3f}<extra></extra>`,
      });
    }
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold text-gray-900">
        Spectral Plot Viewer
      </h2>

      {/* Controls */}
      <div className="mb-4 flex flex-wrap items-center gap-4">
        {/* Spectral type selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-600">Mode:</span>
          {allTypes.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`rounded-full px-3 py-1 text-sm font-medium transition ${
                selectedType === t
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="h-6 w-px bg-gray-300" />

        {/* Display toggles */}
        <label className="flex items-center gap-1.5 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={showMean}
            onChange={() => setShowMean(!showMean)}
            className="accent-indigo-600"
          />
          Mean spectra
        </label>
        <label className="flex items-center gap-1.5 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={showIndividual}
            onChange={() => setShowIndividual(!showIndividual)}
            className="accent-indigo-600"
          />
          Individual spectra
        </label>
      </div>

      {/* Class filter chips */}
      <div className="mb-4 flex flex-wrap gap-2">
        {allClasses.map((cls) => (
          <button
            key={cls}
            onClick={() => toggleClass(cls)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
              selectedClasses.has(cls)
                ? "border-transparent text-white"
                : "border-gray-300 bg-white text-gray-400"
            }`}
            style={
              selectedClasses.has(cls)
                ? { backgroundColor: CLASS_COLORS[cls] }
                : undefined
            }
          >
            {cls}
          </button>
        ))}
      </div>

      {/* Plot */}
      <Plot
        data={traces}
        layout={{
          height,
          margin: { t: 30, r: 30, b: 60, l: 70 },
          xaxis: {
            title: { text: "Wavenumber (cm⁻¹)", font: { size: 13 } },
            autorange: "reversed" as const,
            gridcolor: "#f0f0f0",
          },
          yaxis: {
            title: { text: "Normalized Intensity", font: { size: 13 } },
            gridcolor: "#f0f0f0",
          },
          legend: {
            orientation: "h" as const,
            y: -0.18,
            x: 0.5,
            xanchor: "center" as const,
          },
          plot_bgcolor: "#fafafa",
          paper_bgcolor: "white",
          hovermode: "x unified" as const,
          font: { family: "Inter, system-ui, sans-serif" },
        }}
        config={{
          responsive: true,
          displayModeBar: true,
          modeBarButtonsToRemove: ["lasso2d", "select2d"],
          toImageButtonOptions: {
            format: "svg",
            filename: `spectra_${selectedType}`,
          },
        }}
        style={{ width: "100%" }}
      />
    </div>
  );
}
