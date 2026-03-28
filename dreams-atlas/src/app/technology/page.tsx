import SpectralExplorer from '../../components/SpectralExplorer';

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

      {/* Interactive Spectral Explorer */}
      <section className="bg-gray-50 py-16">
        <div className="section-container">
          <div className="text-center">
            <h2 className="text-2xl font-bold tracking-tight">
              Interactive Spectral Explorer
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Explore representative IR and Raman spectral signatures for each
              adhesive class. Select a class to view characteristic peaks.
            </p>
          </div>
          <div className="mx-auto mt-8 max-w-3xl">
            <SpectralExplorer />
          </div>
        </div>
      </section>
    </>
  );
}
