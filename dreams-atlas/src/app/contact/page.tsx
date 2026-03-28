export default function ContactPage() {
  return (
    <>
      {/* Header */}
      <section className="bg-gradient-to-b from-gray-50 to-white py-20 sm:py-28">
        <div className="section-container">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-primary-600">
              Get in Touch
            </p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">
              Contact{' '}
              <span className="gradient-text">Us</span>
            </h1>
            <p className="mt-5 text-base leading-relaxed text-gray-600">
              Interested in DREAMS Atlas for your adhesive identification needs?
              Reach out to discuss partnerships, licensing, or custom solutions.
            </p>
          </div>
        </div>
      </section>

      {/* Contact Form + Info */}
      <section className="py-16">
        <div className="section-container">
          <div className="mx-auto grid max-w-5xl gap-12 lg:grid-cols-2">
            {/* Form */}
            <div className="rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
              <h2 className="text-xl font-bold">Send a Message</h2>
              <form className="mt-6 space-y-5">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    placeholder="Your name"
                  />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                    Email
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    placeholder="you@company.com"
                  />
                </div>
                <div>
                  <label htmlFor="interest" className="block text-sm font-medium text-gray-700">
                    Interest
                  </label>
                  <select
                    id="interest"
                    name="interest"
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  >
                    <option>Partnership / Collaboration</option>
                    <option>Licensing</option>
                    <option>Investment</option>
                    <option>Technical Inquiry</option>
                    <option>Other</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-gray-700">
                    Message
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    rows={4}
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    placeholder="Tell us about your project..."
                  />
                </div>
                <button type="submit" className="btn-primary w-full justify-center">
                  Send Message
                </button>
              </form>
            </div>

            {/* Info */}
            <div className="space-y-8">
              <div>
                <h2 className="text-xl font-bold">For Investors</h2>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">
                  DREAMS Atlas addresses a growing market need for rapid,
                  non-destructive adhesive identification in manufacturing QC,
                  forensic science, and materials R&amp;D. We&apos;re building a
                  vertically integrated platform combining proprietary spectral
                  datasets with state-of-the-art classification models.
                </p>
              </div>
              <div>
                <h2 className="text-xl font-bold">For Researchers</h2>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">
                  We welcome academic collaborations on spectral classification,
                  adhesive chemistry, and machine learning for materials science.
                  Our dataset of 955 multi-modal spectra across 43 compounds is
                  available for collaborative research.
                </p>
              </div>
              <div>
                <h2 className="text-xl font-bold">For Industry</h2>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">
                  Need adhesive identification integrated into your quality
                  control workflow? We offer API access and custom model training
                  on your proprietary adhesive formulations.
                </p>
              </div>

              <div className="rounded-xl bg-primary-50 p-6">
                <h3 className="text-base font-semibold text-primary-900">
                  K-Dense Science Lab
                </h3>
                <div className="mt-3 space-y-2 text-sm text-primary-800">
                  <p>contact@kdense.science</p>
                  <p>San Francisco, CA</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
