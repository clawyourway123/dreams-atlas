import dynamic from 'next/dynamic';
import SpectralSearch from '../../components/SpectralSearch';
import ClusteringViz from '../../components/ClusteringViz';

const MolecularViewer3D = dynamic(
  () => import('../../components/MolecularViewer3D'),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[480px] items-center justify-center rounded-panel border border-white/5 bg-navy-950/80">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-400/30 border-t-teal-400" />
          <span className="text-xs text-navy-400">Loading 3D viewer...</span>
        </div>
      </div>
    ),
  },
);

export const metadata = {
  title: 'Explore | DREAMS Atlas',
  description: 'Interactive spectral data exploration with 3D molecular views, intelligent search, and ML-powered similarity clustering.',
};

export default function ExplorePage() {
  return (
    <>
      {/* Header */}
      <section className="bg-gradient-to-b from-navy-900 to-navy-950 py-20 sm:py-28">
        <div className="section-container">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-teal-400">
              ML-Powered Exploration
            </p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Spectral <span className="gradient-text">Explorer</span>
            </h1>
            <p className="mt-5 text-base leading-relaxed text-navy-300">
              Navigate the adhesive spectral landscape through interactive 3D
              projections, intelligent compound search, and similarity
              clustering. Every visualization is driven by ML embeddings from
              our classification pipeline.
            </p>
          </div>
        </div>
      </section>

      {/* 3D Molecular Viewer */}
      <section className="py-16 bg-navy-950">
        <div className="section-container">
          <div className="mx-auto max-w-4xl">
            <div className="mb-8 text-center">
              <h2 className="text-2xl font-bold tracking-tight text-white">
                3D Spectral Embedding Space
              </h2>
              <p className="mt-2 text-sm text-navy-300">
                Principal component analysis projects high-dimensional spectral
                features into an interactive 3D scatter plot. Compounds within
                the same adhesive family naturally cluster together.
              </p>
            </div>
            <MolecularViewer3D />
          </div>
        </div>
      </section>

      {/* Intelligent Search */}
      <section className="bg-navy-900/50 py-16">
        <div className="section-container">
          <div className="mx-auto max-w-3xl">
            <div className="mb-8 text-center">
              <h2 className="text-2xl font-bold tracking-tight text-white">
                Intelligent Compound Search
              </h2>
              <p className="mt-2 text-sm text-navy-300">
                Search across 43 unique compounds by name, adhesive family, or
                characteristic spectral peaks. Results are ranked by ML
                classification confidence.
              </p>
            </div>
            <SpectralSearch />
          </div>
        </div>
      </section>

      {/* Similarity Clustering */}
      <section className="py-16 bg-navy-950">
        <div className="section-container">
          <div className="mx-auto max-w-3xl">
            <div className="mb-8 text-center">
              <h2 className="text-2xl font-bold tracking-tight text-white">
                Similarity Clustering
              </h2>
              <p className="mt-2 text-sm text-navy-300">
                t-SNE dimensionality reduction reveals how spectral fingerprints
                group by chemical similarity. Hover over points to inspect
                individual compounds and their family assignments.
              </p>
            </div>
            <ClusteringViz />
          </div>
        </div>
      </section>

      {/* Methodology callout */}
      <section className="bg-navy-900/50 py-16">
        <div className="section-container">
          <div className="mx-auto max-w-3xl">
            <div className="rounded-panel border border-teal-400/10 bg-surface/40 p-8">
              <h3 className="text-lg font-semibold text-teal-400">
                How It Works
              </h3>
              <div className="mt-4 grid gap-6 sm:grid-cols-3">
                <div>
                  <div className="text-3xl font-extrabold text-navy-700">01</div>
                  <h4 className="mt-1 text-sm font-semibold text-white">Feature Extraction</h4>
                  <p className="mt-1 text-xs leading-relaxed text-navy-400">
                    Raw IR and Raman spectra are transformed into
                    high-dimensional feature vectors capturing peak positions,
                    intensities, and shapes.
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-extrabold text-navy-700">02</div>
                  <h4 className="mt-1 text-sm font-semibold text-white">Embedding &amp; Projection</h4>
                  <p className="mt-1 text-xs leading-relaxed text-navy-400">
                    PCA and t-SNE project the feature space into 2D/3D for
                    visualization while preserving local structure and cluster
                    separation.
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-extrabold text-navy-700">03</div>
                  <h4 className="mt-1 text-sm font-semibold text-white">Classification</h4>
                  <p className="mt-1 text-xs leading-relaxed text-navy-400">
                    CNN-1D classifiers trained on compound-grouped
                    cross-validation assign family labels with per-class
                    confidence scores.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
