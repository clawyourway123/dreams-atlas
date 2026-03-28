import Link from 'next/link';

const stats = [
  { label: 'Adhesive Classes', value: '7' },
  { label: 'Spectral Samples', value: '955' },
  { label: 'Unique Compounds', value: '43' },
  { label: 'Spectral Modalities', value: '3' },
];

const features = [
  {
    title: 'Multi-Modal Spectroscopy',
    description:
      'Combines IR, FTIR, and Raman spectral data for comprehensive adhesive fingerprinting across multiple modalities.',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
      </svg>
    ),
  },
  {
    title: 'Deep Learning Classification',
    description:
      'CNN-1D architecture trained with compound-grouped cross-validation ensures robust generalization to unseen adhesive formulations.',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
      </svg>
    ),
  },
  {
    title: 'Industrial Applications',
    description:
      'Rapid, non-destructive identification of adhesive types for quality control, forensics, and materials science research.',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
      </svg>
    ),
  },
];

export default function Home() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-950 via-primary-900 to-primary-800">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
        <div className="section-container relative py-24 sm:py-32 lg:py-40">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-primary-300">
              K-Dense Science Lab
            </p>
            <h1 className="mt-4 text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl">
              DREAMS{' '}
              <span className="bg-gradient-to-r from-primary-300 to-accent-400 bg-clip-text text-transparent">
                Atlas
              </span>
            </h1>
            <p className="mt-2 text-lg font-medium text-primary-200">
              Dual-modality Recognition &amp; Evaluation of Adhesive Materials
              via Spectroscopy
            </p>
            <p className="mt-6 text-base leading-relaxed text-primary-100/80">
              Combining infrared and Raman spectroscopy with deep learning to
              classify adhesive materials at molecular resolution. Identify 7
              adhesive families across 43 unique compounds &mdash; rapidly and
              non-destructively.
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link href="/technology" className="btn-primary">
                Explore the Science
              </Link>
              <Link href="/results" className="btn-secondary !border-primary-400/30 !text-primary-100 hover:!bg-primary-800">
                View Results
              </Link>
            </div>
          </div>

          {/* Stats bar */}
          <div className="mx-auto mt-16 grid max-w-2xl grid-cols-2 gap-6 sm:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-3xl font-bold text-white">{stat.value}</p>
                <p className="mt-1 text-xs font-medium uppercase tracking-wider text-primary-300">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 sm:py-28">
        <div className="section-container">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Spectral Intelligence for{' '}
              <span className="gradient-text">Adhesive Science</span>
            </h2>
            <p className="mt-4 text-base text-gray-600">
              DREAMS Atlas brings together advanced spectroscopy and machine
              learning to solve the challenge of rapid adhesive identification.
            </p>
          </div>
          <div className="mx-auto mt-14 grid max-w-5xl gap-8 md:grid-cols-3">
            {features.map((f) => (
              <div
                key={f.title}
                className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
                  {f.icon}
                </div>
                <h3 className="mt-4 text-lg font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">
                  {f.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-primary-50 py-16">
        <div className="section-container text-center">
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Interested in DREAMS Atlas?
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-gray-600">
            Whether you&apos;re in quality control, forensic science, or
            materials R&amp;D, we&apos;d love to discuss how spectral adhesive
            classification can support your work.
          </p>
          <Link href="/contact" className="btn-primary mt-8">
            Contact Us
          </Link>
        </div>
      </section>
    </>
  );
}
