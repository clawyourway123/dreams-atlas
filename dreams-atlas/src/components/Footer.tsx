import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="border-t border-gray-100 bg-gray-50">
      <div className="section-container py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
                <span className="text-sm font-bold text-white">D</span>
              </div>
              <span className="text-lg font-bold tracking-tight">
                DREAMS <span className="text-primary-600">Atlas</span>
              </span>
            </Link>
            <p className="mt-3 max-w-md text-sm text-gray-500">
              Dual-modality Recognition and Evaluation of Adhesive Materials via
              Spectroscopy. Advancing adhesive identification through IR and Raman
              spectral classification.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Platform</h3>
            <ul className="mt-3 space-y-2">
              <li><Link href="/technology" className="text-sm text-gray-500 hover:text-primary-600">Technology</Link></li>
              <li><Link href="/results" className="text-sm text-gray-500 hover:text-primary-600">Results</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Company</h3>
            <ul className="mt-3 space-y-2">
              <li><Link href="/team" className="text-sm text-gray-500 hover:text-primary-600">Team</Link></li>
              <li><Link href="/contact" className="text-sm text-gray-500 hover:text-primary-600">Contact</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-8 border-t border-gray-200 pt-8 text-center text-xs text-gray-400">
          &copy; {new Date().getFullYear()} K-Dense Science Lab. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
