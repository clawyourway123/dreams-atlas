import ContactForm from '../../components/ContactForm';

export default function ContactPage() {
  return (
    <>
      {/* Header */}
      <section className="bg-gradient-to-b from-navy-900 to-navy-950 py-20 sm:py-28">
        <div className="section-container">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-teal-400">
              Get in Touch
            </p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Contact{' '}
              <span className="gradient-text">Us</span>
            </h1>
            <p className="mt-5 text-base leading-relaxed text-navy-300">
              Interested in DREAMS Atlas for your adhesive identification needs?
              Reach out to discuss partnerships, licensing, or custom solutions.
            </p>
          </div>
        </div>
      </section>

      {/* Contact Form + Info */}
      <section className="py-16 bg-navy-950">
        <div className="section-container">
          <div className="mx-auto grid max-w-5xl gap-12 lg:grid-cols-2">
            {/* Form */}
            <ContactForm />

            {/* Info */}
            <div className="space-y-8">
              <div>
                <h2 className="text-xl font-bold text-white">For Investors</h2>
                <p className="mt-2 text-sm leading-relaxed text-navy-300">
                  DREAMS Atlas addresses a growing market need for rapid,
                  non-destructive adhesive identification in manufacturing QC,
                  forensic science, and materials R&amp;D. We&apos;re building a
                  vertically integrated platform combining proprietary spectral
                  datasets with state-of-the-art classification models.
                </p>
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">For Researchers</h2>
                <p className="mt-2 text-sm leading-relaxed text-navy-300">
                  We welcome academic collaborations on spectral classification,
                  adhesive chemistry, and machine learning for materials science.
                  Our dataset of 955 multi-modal spectra across 43 compounds is
                  available for collaborative research.
                </p>
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">For Industry</h2>
                <p className="mt-2 text-sm leading-relaxed text-navy-300">
                  Need adhesive identification integrated into your quality
                  control workflow? We offer API access and custom model training
                  on your proprietary adhesive formulations.
                </p>
              </div>

              <div className="rounded-panel bg-surface/60 border border-white/5 p-6">
                <h3 className="text-base font-semibold text-white">
                  K-Dense Science Lab
                </h3>
                <div className="mt-3 space-y-2 text-sm text-teal-400">
                  <p>contact@kdense.science</p>
                  <p className="text-navy-300">San Francisco, CA</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
