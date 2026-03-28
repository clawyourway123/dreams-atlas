const modalities = [
  {
    name: 'Infrared (IR)',
    range: '4000–400 cm⁻¹',
    description:
      'Probes molecular vibrations through absorption of infrared radiation. Excellent for identifying functional groups — carbonyl, hydroxyl, amine — that distinguish adhesive chemistries.',
  },
  {
    name: 'Fourier-Transform IR (FTIR)',
    range: '4000–400 cm⁻¹',
    description:
      'High-resolution interferometric IR providing rapid, quantitative spectra. The workhorse for polymer and adhesive characterization in industrial QC environments.',
  },
  {
    name: 'Raman Spectroscopy',
    range: '100–3500 cm⁻¹',
    description:
      'Measures inelastic light scattering to reveal molecular structure. Complementary to IR — strong where IR is weak — and non-destructive with minimal sample preparation.',
  },
];

const adhesiveClasses = [
  { name: 'Acrylic / PSA', count: 216, color: 'bg-blue-500' },
  { name: 'Cyanoacrylate', count: 101, color: 'bg-purple-500' },
  { name: 'Epoxy', count: 140, color: 'bg-amber-500' },
  { name: 'Hot-melt', count: 128, color: 'bg-red-500' },
  { name: 'Polyurethane', count: 96, color: 'bg-green-500' },
  { name: 'Rubber-based', count: 140, color: 'bg-orange-500' },
  { name: 'Silicone', count: 134, color: 'bg-teal-500' },
];

const pipeline = [
  {
    step: '01',
    title: 'Sample Acquisition',
    description: 'Collect spectral measurements across IR, FTIR, and Raman modalities from adhesive samples.',
  },
  {
    step: '02',
    title: 'Feature Engineering',
    description: 'Extract wavenumber intensity features and normalize across modalities for consistent input representation.',
  },
  {
    step: '03',
    title: 'Compound-Grouped CV',
    description: '5-fold cross-validation grouped by compound identity ensures the model generalizes to novel formulations.',
  },
  {
    step: '04',
    title: 'Classification',
    description: 'CNN-1D architecture processes spectral vectors to predict one of 7 adhesive families with per-class confidence scores.',
  },
];

export default function TechnologyPage() {
  return (
    <>
      {/* Header */}
      <section className="bg-gradient-to-b from-gray-50 to-white py-20 sm:py-28">
        <div className="section-container">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-primary-600">
              Our Approach
            </p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">
              Spectral Classification{' '}
              <span className="gradient-text">Technology</span>
            </h1>
            <p className="mt-5 text-base leading-relaxed text-gray-600">
              DREAMS Atlas uses dual-modality vibrational spectroscopy — infrared
              absorption and Raman scattering — combined with deep learning to
              classify adhesive materials at the molecular level.
            </p>
          </div>
        </div>
      </section>

      {/* Modalities */}
      <section className="py-16">
        <div className="section-container">
          <h2 className="text-2xl font-bold tracking-tight">
            Spectral Modalities
          </h2>
          <div className="mt-8 grid gap-6 md:grid-cols-3">
            {modalities.map((m) => (
              <div
                key={m.name}
                className="rounded-xl border border-gray-100 p-6 shadow-sm"
              >
                <h3 className="text-lg font-semibold text-primary-700">
                  {m.name}
                </h3>
                <p className="mt-1 font-mono text-xs text-gray-400">
                  {m.range}
                </p>
                <p className="mt-3 text-sm leading-relaxed text-gray-600">
                  {m.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Adhesive Classes */}
      <section className="bg-gray-50 py-16">
        <div className="section-container">
          <h2 className="text-2xl font-bold tracking-tight">
            7 Adhesive Families
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            955 samples spanning 43 unique compounds across the adhesive
            landscape.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {adhesiveClasses.map((ac) => (
              <div
                key={ac.name}
                className="flex items-center gap-3 rounded-lg bg-white p-4 shadow-sm"
              >
                <div className={`h-3 w-3 rounded-full ${ac.color}`} />
                <div>
                  <p className="text-sm font-semibold">{ac.name}</p>
                  <p className="text-xs text-gray-400">{ac.count} samples</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pipeline */}
      <section className="py-16">
        <div className="section-container">
          <h2 className="text-2xl font-bold tracking-tight">
            Classification Pipeline
          </h2>
          <div className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {pipeline.map((p) => (
              <div key={p.step} className="relative rounded-xl border border-gray-100 p-6 shadow-sm">
                <span className="text-4xl font-extrabold text-primary-100">
                  {p.step}
                </span>
                <h3 className="mt-2 text-base font-semibold">{p.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">
                  {p.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Spectral Visualization Placeholder */}
      <section className="bg-gray-50 py-16">
        <div className="section-container text-center">
          <h2 className="text-2xl font-bold tracking-tight">
            Interactive Spectral Explorer
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Coming soon — explore real IR and Raman spectra for each adhesive
            class.
          </p>
          <div className="mx-auto mt-8 flex h-64 max-w-3xl items-center justify-center rounded-xl border-2 border-dashed border-gray-300 bg-white">
            <div className="text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-300"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6"
                />
              </svg>
              <p className="mt-2 text-sm text-gray-400">
                Spectral visualization placeholder
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
