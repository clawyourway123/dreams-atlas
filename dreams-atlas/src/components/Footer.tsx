import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="border-t border-white/5 bg-navy-950">
      <div className="section-container py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-teal-500 to-teal-400">
                <span className="text-sm font-bold text-navy-950">D</span>
              </div>
              <span className="text-lg font-bold tracking-tight text-white">
                DREAMS <span className="text-teal-400">Atlas</span>
              </span>
            </Link>
            <p className="mt-3 max-w-md text-sm text-navy-400">
              Dual-modality Recognition and Evaluation of Adhesive Materials via
              Spectroscopy. Advancing adhesive identification through IR and Raman
              spectral classification.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Platform</h3>
            <ul className="mt-3 space-y-2">
              <li><Link href="/technology" className="text-sm text-navy-400 hover:text-teal-400 transition-colors">Technology</Link></li>
              <li><Link href="/results" className="text-sm text-navy-400 hover:text-teal-400 transition-colors">Results</Link></li>
              <li><a href="../index.html" className="text-sm text-navy-400 hover:text-teal-400 transition-colors">Enterprise Gallery</a></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Company</h3>
            <ul className="mt-3 space-y-2">
              <li><Link href="/team" className="text-sm text-navy-400 hover:text-teal-400 transition-colors">Team</Link></li>
              <li><Link href="/contact" className="text-sm text-navy-400 hover:text-teal-400 transition-colors">Contact</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-8 border-t border-white/5 pt-8 text-center text-xs text-navy-500">
          &copy; {new Date().getFullYear()} K-Dense Science Lab. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
