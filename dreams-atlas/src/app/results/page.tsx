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
    <div className="rounded-lg bg-gray-50 p-4 text-center">
      <p className="text-2xl font-bold text-primary-700">{value}</p>
      <p className="mt-1 text-xs font-medium uppercase tracking-wider text-gray-500">
        {label}
      </p>
    </div>
  );
}

export default function ResultsPage() {
  return (
    <>
      {/* Header */}
      <section className="bg-gradient-to-b from-gray-50 to-white py-20 sm:py-28">
        <div className="section-container">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-primary-600">
              Model Performance
            </p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">
              Evaluation{' '}
              <span className="gradient-text">Results</span>
            </h1>
            <p className="mt-5 text-base leading-relaxed text-gray-600">
              Models evaluated with compound-grouped 5-fold cross-validation on
              955 samples across 43 unique compounds. This rigorous protocol
              ensures no compound leakage between train and test sets.
            </p>
          </div>
        </div>
      </section>

      {/* Models */}
      <section className="py-16">
        <div className="section-container space-y-12">
          {models.map((model) => (
            <div
              key={model.name}
              className="overflow-hidden rounded-2xl border border-gray-100 shadow-sm"
            >
              <div className="flex items-center justify-between border-b border-gray-100 bg-white px-6 py-4">
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-bold">{model.name}</h2>
                  {model.recommended && (
                    <span className="rounded-full bg-accent-100 px-3 py-0.5 text-xs font-semibold text-accent-700">
                      Recommended
                    </span>
                  )}
                </div>
              </div>
              <div className="bg-white p-6">
                <p className="text-sm text-gray-600">{model.description}</p>

                {/* Metrics */}
                <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <MetricCard label="Accuracy" value={model.metrics.accuracy} />
                  <MetricCard label="F1 (Macro)" value={model.metrics.f1Macro} />
                  <MetricCard label="F1 (Weighted)" value={model.metrics.f1Weighted} />
                  <MetricCard label="AUC (Macro)" value={model.metrics.aucMacro} />
                </div>

                {/* Fold breakdown */}
                <div className="mt-6">
                  <h3 className="text-sm font-semibold text-gray-700">
                    Per-Fold Performance
                  </h3>
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100 text-left text-xs uppercase tracking-wider text-gray-500">
                          <th className="pb-2 pr-4">Fold</th>
                          <th className="pb-2 pr-4">Accuracy</th>
                          <th className="pb-2">F1 (Macro)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {model.folds.map((f) => (
                          <tr
                            key={f.fold}
                            className="border-b border-gray-50"
                          >
                            <td className="py-2 pr-4 font-medium">
                              Fold {f.fold}
                            </td>
                            <td className="py-2 pr-4">
                              <div className="flex items-center gap-2">
                                <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-100">
                                  <div
                                    className="h-full rounded-full bg-primary-500"
                                    style={{ width: `${Math.min(f.accuracy * 3, 100)}%` }}
                                  />
                                </div>
                                <span className="font-mono text-xs">
                                  {f.accuracy.toFixed(1)}%
                                </span>
                              </div>
                            </td>
                            <td className="py-2">
                              <span className="font-mono text-xs">
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
      <section className="bg-amber-50 py-12">
        <div className="section-container">
          <div className="mx-auto max-w-2xl text-center">
            <h3 className="text-lg font-semibold text-amber-800">
              Early-Stage Models
            </h3>
            <p className="mt-2 text-sm text-amber-700">
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
      <section className="py-16">
        <div className="section-container">
          <div className="text-center">
            <h2 className="text-2xl font-bold tracking-tight">
              Confusion Matrix &amp; ROC Curves
            </h2>
            <p className="mt-2 text-sm text-gray-600">
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
