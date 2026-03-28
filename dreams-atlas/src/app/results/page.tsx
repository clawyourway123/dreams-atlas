import ConfusionMatrix from '../../components/ConfusionMatrix';
import ROCCurves from '../../components/ROCCurves';

const models = [
  {
    name: 'CNN-1D',
    recommended: true,
    metrics: {
      accuracy: '14.0%',
      f1Macro: '13.9%',
      f1Weighted: '13.9%',
      aucMacro: '0.460',
    },
    folds: [
      { fold: 1, accuracy: 15.7, f1: 11.5 },
      { fold: 2, accuracy: 13.2, f1: 9.8 },
      { fold: 3, accuracy: 9.2, f1: 5.1 },
      { fold: 4, accuracy: 15.8, f1: 10.4 },
      { fold: 5, accuracy: 16.1, f1: 12.7 },
    ],
    description:
      'One-dimensional convolutional neural network operating on raw spectral intensity vectors. Shows stronger generalization on compound-grouped folds.',
  },
  {
    name: 'Random Forest',
    recommended: false,
    metrics: {
      accuracy: '11.2%',
      f1Macro: '9.4%',
      f1Weighted: '10.8%',
      aucMacro: '0.417',
    },
    folds: [
      { fold: 1, accuracy: 10.8, f1: 7.4 },
      { fold: 2, accuracy: 12.7, f1: 10.7 },
      { fold: 3, accuracy: 7.0, f1: 4.8 },
      { fold: 4, accuracy: 13.3, f1: 9.9 },
      { fold: 5, accuracy: 12.0, f1: 11.2 },
    ],
    description:
      'Ensemble of decision trees on engineered spectral features. Baseline model for comparison with deep learning approaches.',
  },
];

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-card bg-surface/40 border border-white/5 p-4 text-center">
      <p className="text-2xl font-bold text-teal-400">{value}</p>
      <p className="mt-1 text-xs font-medium uppercase tracking-wider text-navy-400">
        {label}
      </p>
    </div>
  );
}

export default function ResultsPage() {
  return (
    <>
      {/* Header */}
      <section className="bg-gradient-to-b from-navy-900 to-navy-950 py-20 sm:py-28">
        <div className="section-container">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-teal-400">
              Model Performance
            </p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Evaluation{' '}
              <span className="gradient-text">Results</span>
            </h1>
            <p className="mt-5 text-base leading-relaxed text-navy-300">
              Models evaluated with compound-grouped 5-fold cross-validation on
              955 samples across 43 unique compounds. This rigorous protocol
              ensures no compound leakage between train and test sets.
            </p>
          </div>
        </div>
      </section>

      {/* Models */}
      <section className="py-16 bg-navy-950">
        <div className="section-container space-y-12">
          {models.map((model) => (
            <div
              key={model.name}
              className="overflow-hidden rounded-panel border border-white/5 shadow-card"
            >
              <div className="flex items-center justify-between border-b border-white/5 bg-surface/60 px-6 py-4">
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-bold text-white">{model.name}</h2>
                  {model.recommended && (
                    <span className="rounded-pill bg-teal-400/10 px-3 py-0.5 text-xs font-semibold text-teal-400 border border-teal-400/20">
                      Recommended
                    </span>
                  )}
                </div>
              </div>
              <div className="bg-surface/30 p-6">
                <p className="text-sm text-navy-300">{model.description}</p>

                {/* Metrics */}
                <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <MetricCard label="Accuracy" value={model.metrics.accuracy} />
                  <MetricCard label="F1 (Macro)" value={model.metrics.f1Macro} />
                  <MetricCard label="F1 (Weighted)" value={model.metrics.f1Weighted} />
                  <MetricCard label="AUC (Macro)" value={model.metrics.aucMacro} />
                </div>

                {/* Fold breakdown */}
                <div className="mt-6">
                  <h3 className="text-sm font-semibold text-navy-200">
                    Per-Fold Performance
                  </h3>
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-white/5 text-left text-xs uppercase tracking-wider text-navy-400">
                          <th className="pb-2 pr-4">Fold</th>
                          <th className="pb-2 pr-4">Accuracy</th>
                          <th className="pb-2">F1 (Macro)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {model.folds.map((f) => (
                          <tr
                            key={f.fold}
                            className="border-b border-white/5"
                          >
                            <td className="py-2 pr-4 font-medium text-white">
                              Fold {f.fold}
                            </td>
                            <td className="py-2 pr-4">
                              <div className="flex items-center gap-2">
                                <div className="h-2 w-24 overflow-hidden rounded-full bg-navy-700">
                                  <div
                                    className="h-full rounded-full bg-teal-500"
                                    style={{ width: `${Math.min(f.accuracy * 3, 100)}%` }}
                                  />
                                </div>
                                <span className="font-mono text-xs text-navy-200">
                                  {f.accuracy.toFixed(1)}%
                                </span>
                              </div>
                            </td>
                            <td className="py-2">
                              <span className="font-mono text-xs text-navy-200">
                                {f.f1.toFixed(1)}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Note */}
      <section className="bg-amber-900/20 border-y border-amber-500/10 py-12">
        <div className="section-container">
          <div className="mx-auto max-w-2xl text-center">
            <h3 className="text-lg font-semibold text-amber-400">
              Early-Stage Models
            </h3>
            <p className="mt-2 text-sm text-amber-300/80">
              Current metrics reflect our initial dataset and compound-grouped
              validation. Active work on feature engineering, data augmentation,
              and architecture tuning targets production-grade accuracy. The
              compound-grouped protocol deliberately prevents data leakage,
              resulting in conservative but realistic performance estimates.
            </p>
          </div>
        </div>
      </section>

      {/* Performance Visualizations */}
      <section className="py-16 bg-navy-950">
        <div className="section-container">
          <div className="text-center">
            <h2 className="text-2xl font-bold tracking-tight text-white">
              Confusion Matrix &amp; ROC Curves
            </h2>
            <p className="mt-2 text-sm text-navy-300">
              Per-class performance breakdown from compound-grouped
              cross-validation.
            </p>
          </div>
          <div className="mx-auto mt-8 grid max-w-5xl gap-6 md:grid-cols-2">
            <ConfusionMatrix />
            <ROCCurves />
          </div>
        </div>
      </section>
    </>
  );
}
