"use client";

import React, { useEffect, useState } from "react";
import SpectralPlotViewer from "./SpectralPlotViewer";
import ModelPerformanceDashboard from "./ModelPerformanceDashboard";
import ClassificationDemo from "./ClassificationDemo";
import { fetchSpectra } from "./loadSpectra";
import type { SpectrumRow } from "./SpectralPlotViewer";
import type { EvaluationReport } from "./ModelPerformanceDashboard";

/**
 * Full-page component that loads data and renders all three DREAMS visualizations.
 * Drop this into a Next.js page:
 *
 *   // app/visualizations/page.tsx
 *   import DreamsVisualizationPage from "@/components/visualizations/DreamsVisualizationPage";
 *   export default function Page() { return <DreamsVisualizationPage />; }
 *
 * Prerequisites:
 *   - Place adhesive_spectra_ir_raman_intensities.csv at /public/data/
 *   - Place evaluation_report.json at /public/data/
 *   - Install: npm install react-plotly.js plotly.js-dist-min
 */
export default function DreamsVisualizationPage() {
  const [spectra, setSpectra] = useState<SpectrumRow[] | null>(null);
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetchSpectra("/data/adhesive_spectra_ir_raman_intensities.csv"),
      fetch("/data/evaluation_report.json").then((r) => r.json()),
    ])
      .then(([spectraData, reportData]) => {
        setSpectra(spectraData);
        setReport(reportData);
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <p className="text-red-600">Failed to load data: {error}</p>
      </div>
    );
  }

  if (!spectra || !report) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
          <p className="text-sm text-gray-500">Loading spectral data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">
          DREAMS Atlas — Spectral Analysis Dashboard
        </h1>
        <p className="mt-2 text-gray-600">
          Interactive visualization of adhesive spectral classification data and
          model performance
        </p>
      </div>

      <SpectralPlotViewer spectra={spectra} />
      <ModelPerformanceDashboard report={report} />
      <ClassificationDemo spectra={spectra} classes={report.dataset.classes} />
    </div>
  );
}
