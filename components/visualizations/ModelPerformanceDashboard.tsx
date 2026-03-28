"use client";

import React, { useState, useMemo } from "react";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export interface FoldMetrics {
  fold: number;
  accuracy: number;
  f1_macro: number;
  f1_weighted: number;
  train_size?: number;
  test_size?: number;
  test_compounds?: string[];
}

export interface ModelResult {
  overall_accuracy: number;
  f1_macro: number;
  f1_weighted: number;
  auc_macro: number;
  targets_met: boolean;
  fold_metrics: FoldMetrics[];
  model_file: string;
}

export interface EvaluationReport {
  dataset: {
    file: string;
    total_samples: number;
    modalities: string[];
    classes: string[];
    class_distribution: Record<string, number>;
    unique_compounds: number;
    cv_method: string;
  };
  random_forest: ModelResult;
  cnn_1d: ModelResult;
  recommendation: string;
}

interface ModelPerformanceDashboardProps {
  report: EvaluationReport;
  height?: number;
}

type ModelKey = "random_forest" | "cnn_1d";

const MODEL_LABELS: Record<ModelKey, string> = {
  random_forest: "Random Forest",
  cnn_1d: "CNN-1D",
};

const MODEL_COLORS: Record<ModelKey, string> = {
  random_forest: "#1f77b4",
  cnn_1d: "#ff7f0e",
};

function MetricCard({
  label,
  value,
  format = "pct",
}: {
  label: string;
  value: number;
  format?: "pct" | "num";
}) {
  const display =
    format === "pct" ? `${(value * 100).toFixed(1)}%` : value.toFixed(3);
  return (
    <div className="rounded-lg border border-gray-100 bg-gray-50 px-4 py-3 text-center">
      <div className="text-2xl font-bold text-gray-900">{display}</div>
      <div className="mt-0.5 text-xs font-medium uppercase tracking-wide text-gray-500">
        {label}
      </div>
    </div>
  );
}

export default function ModelPerformanceDashboard({
  report,
  height = 380,
}: ModelPerformanceDashboardProps) {
  const [selectedModel, setSelectedModel] = useState<ModelKey>("cnn_1d");
  const model = report[selectedModel];
  const classes = report.dataset.classes;

  // Class distribution bar chart
  const distTrace: Plotly.Data = {
    x: classes,
    y: classes.map((c) => report.dataset.class_distribution[c]),
    type: "bar" as const,
    marker: {
      color: classes.map(
        (_, i) =>
          [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
          ][i],
      ),
    },
    hovertemplate: "<b>%{x}</b><br>%{y} samples<extra></extra>",
  };

  // Fold performance comparison (grouped bar)
  const foldTraces: Plotly.Data[] = (
    ["random_forest", "cnn_1d"] as ModelKey[]
  ).map((mk) => ({
    x: report[mk].fold_metrics.map((f) => `Fold ${f.fold}`),
    y: report[mk].fold_metrics.map((f) => f.accuracy * 100),
    type: "bar" as const,
    name: MODEL_LABELS[mk],
    marker: { color: MODEL_COLORS[mk] },
    hovertemplate: `<b>${MODEL_LABELS[mk]}</b><br>Fold %{x}<br>Accuracy: %{y:.1f}%<extra></extra>`,
  }));

  // Metrics comparison radar
  const metricNames = ["Accuracy", "F1 Macro", "F1 Weighted", "AUC Macro"];
  const radarTraces: Plotly.Data[] = (
    ["random_forest", "cnn_1d"] as ModelKey[]
  ).map((mk) => ({
    type: "scatterpolar" as const,
    r: [
      report[mk].overall_accuracy * 100,
      report[mk].f1_macro * 100,
      report[mk].f1_weighted * 100,
      report[mk].auc_macro * 100,
    ],
    theta: metricNames,
    fill: "toself" as const,
    name: MODEL_LABELS[mk],
    line: { color: MODEL_COLORS[mk] },
    opacity: 0.7,
  }));

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          Model Performance Dashboard
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Recommended:</span>
          <span className="rounded-full bg-green-100 px-3 py-1 text-sm font-semibold text-green-800">
            {report.recommendation}
          </span>
        </div>
      </div>

      {/* Model selector and summary metrics */}
      <div className="mb-6 flex items-center gap-4">
        {(["random_forest", "cnn_1d"] as ModelKey[]).map((mk) => (
          <button
            key={mk}
            onClick={() => setSelectedModel(mk)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              selectedModel === mk
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {MODEL_LABELS[mk]}
          </button>
        ))}
      </div>

      {/* Summary metric cards */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricCard label="Accuracy" value={model.overall_accuracy} />
        <MetricCard label="F1 Macro" value={model.f1_macro} />
        <MetricCard label="F1 Weighted" value={model.f1_weighted} />
        <MetricCard label="AUC Macro" value={model.auc_macro} />
      </div>

      {/* Charts grid */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Class distribution */}
        <div className="rounded-lg border border-gray-100 bg-gray-50 p-2">
          <Plot
            data={[distTrace]}
            layout={{
              height: height,
              margin: { t: 35, r: 15, b: 90, l: 45 },
              title: {
                text: "Class Distribution",
                font: { size: 13 },
                y: 0.98,
              },
              xaxis: { tickangle: -35, tickfont: { size: 10 } },
              yaxis: { title: { text: "Samples", font: { size: 11 } } },
              plot_bgcolor: "white",
              paper_bgcolor: "transparent",
              showlegend: false,
              font: { family: "Inter, system-ui, sans-serif" },
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: "100%" }}
          />
        </div>

        {/* Fold accuracy comparison */}
        <div className="rounded-lg border border-gray-100 bg-gray-50 p-2">
          <Plot
            data={foldTraces}
            layout={{
              height: height,
              margin: { t: 35, r: 15, b: 50, l: 45 },
              title: {
                text: "Fold Accuracy (%)",
                font: { size: 13 },
                y: 0.98,
              },
              barmode: "group" as const,
              yaxis: {
                title: { text: "Accuracy %", font: { size: 11 } },
                range: [0, 25],
              },
              legend: { orientation: "h" as const, y: -0.22, x: 0.5, xanchor: "center" as const },
              plot_bgcolor: "white",
              paper_bgcolor: "transparent",
              font: { family: "Inter, system-ui, sans-serif" },
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: "100%" }}
          />
        </div>

        {/* Radar comparison */}
        <div className="rounded-lg border border-gray-100 bg-gray-50 p-2">
          <Plot
            data={radarTraces}
            layout={{
              height: height,
              margin: { t: 35, r: 30, b: 30, l: 30 },
              title: {
                text: "Model Comparison",
                font: { size: 13 },
                y: 0.98,
              },
              polar: {
                radialaxis: { visible: true, range: [0, 50] },
              },
              legend: { orientation: "h" as const, y: -0.12, x: 0.5, xanchor: "center" as const },
              paper_bgcolor: "transparent",
              font: { family: "Inter, system-ui, sans-serif" },
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: "100%" }}
          />
        </div>
      </div>

      {/* Dataset info footer */}
      <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-500">
        <span>
          <strong>{report.dataset.total_samples}</strong> samples
        </span>
        <span>
          <strong>{report.dataset.unique_compounds}</strong> compounds
        </span>
        <span>
          <strong>{report.dataset.classes.length}</strong> classes
        </span>
        <span>CV: {report.dataset.cv_method}</span>
        <span>Modalities: {report.dataset.modalities.join(", ")}</span>
      </div>
    </div>
  );
}
