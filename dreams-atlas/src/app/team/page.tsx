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
      <section className="bg-gradient-to-b from-navy-900 to-navy-950 py-20 sm:py-28">
        <div className="section-container">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-teal-400">
              Our People
            </p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight text-white sm:text-5xl">
              The K-Dense{' '}
              <span className="gradient-text">Team</span>
            </h1>
            <p className="mt-5 text-base leading-relaxed text-navy-300">
              A multidisciplinary team of scientists and engineers building the
              future of spectral adhesive classification.
            </p>
          </div>
        </div>
      </section>

      {/* Team Grid */}
      <section className="py-16 bg-navy-950">
        <div className="section-container">
          <div className="mx-auto grid max-w-4xl gap-8 sm:grid-cols-2">
            {team.map((member) => (
              <div
                key={member.name}
                className="rounded-panel border border-white/5 bg-surface/60 p-6 shadow-card transition-all hover:shadow-card-hover hover:border-teal-400/20"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-teal-400/20 to-navy-700 border-2 border-teal-400/30 text-lg font-bold text-teal-400">
                    {member.initials}
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white">{member.name}</h3>
                    <p className="text-sm text-teal-400">{member.role}</p>
                  </div>
                </div>
                <p className="mt-4 text-sm leading-relaxed text-navy-300">
                  {member.bio}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Lab */}
      <section className="bg-navy-900/50 py-16">
        <div className="section-container text-center">
          <h2 className="text-2xl font-bold tracking-tight text-white">
            K-Dense Science Lab
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-navy-300">
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
