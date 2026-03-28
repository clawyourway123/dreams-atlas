const team = [
  {
    name: 'Dr. Elena Vasquez',
    role: 'Chief Executive Officer',
    bio: 'Leads K-Dense Science Lab\'s mission to bring spectral intelligence to materials science. Oversees company strategy and investor relations.',
    initials: 'EV',
  },
  {
    name: 'Dr. Marcus Chen',
    role: 'Chief Science Officer',
    bio: 'Directs the scientific vision behind DREAMS Atlas. Expert in vibrational spectroscopy and machine learning for chemical analysis.',
    initials: 'MC',
  },
  {
    name: 'Dr. Catherine Moreau',
    role: 'Director of Laboratory Operations',
    bio: 'Manages laboratory workflows, LIMS integration, and data quality assurance for all spectral acquisition campaigns.',
    initials: 'CM',
  },
  {
    name: 'Dr. Elise Bergstrom',
    role: 'Lab Informatics Specialist',
    bio: 'Builds the data infrastructure powering DREAMS Atlas — from LIMS integration and data lineage to cloud compute pipelines for model training.',
    initials: 'EB',
  },
];

export default function TeamPage() {
  return (
    <>
      {/* Header */}
      <section className="bg-gradient-to-b from-gray-50 to-white py-20 sm:py-28">
        <div className="section-container">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-primary-600">
              Our People
            </p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">
              The K-Dense{' '}
              <span className="gradient-text">Team</span>
            </h1>
            <p className="mt-5 text-base leading-relaxed text-gray-600">
              A multidisciplinary team of scientists and engineers building the
              future of spectral adhesive classification.
            </p>
          </div>
        </div>
      </section>

      {/* Team Grid */}
      <section className="py-16">
        <div className="section-container">
          <div className="mx-auto grid max-w-4xl gap-8 sm:grid-cols-2">
            {team.map((member) => (
              <div
                key={member.name}
                className="rounded-xl border border-gray-100 p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-100 text-lg font-bold text-primary-700">
                    {member.initials}
                  </div>
                  <div>
                    <h3 className="text-base font-semibold">{member.name}</h3>
                    <p className="text-sm text-primary-600">{member.role}</p>
                  </div>
                </div>
                <p className="mt-4 text-sm leading-relaxed text-gray-600">
                  {member.bio}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Lab */}
      <section className="bg-gray-50 py-16">
        <div className="section-container text-center">
          <h2 className="text-2xl font-bold tracking-tight">
            K-Dense Science Lab
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-gray-600">
            We combine deep domain expertise in spectroscopy, polymer chemistry,
            and machine learning to advance the state of the art in materials
            identification. Our lab infrastructure supports high-throughput
            spectral acquisition and GPU-accelerated model development.
          </p>
        </div>
      </section>
    </>
  );
}
