'use client';

import Link from 'next/link';
import { useState } from 'react';

const navigation = [
  { name: 'Explore', href: '/explore' },
  { name: 'Technology', href: '/technology' },
  { name: 'Results', href: '/results' },
  { name: 'Team', href: '/team' },
  { name: 'Contact', href: '/contact' },
];

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed top-0 z-50 w-full border-b border-white/5 bg-navy-950/80 backdrop-blur-lg">
      <div className="section-container flex h-16 items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-teal-500 to-teal-400">
              <span className="text-sm font-bold text-navy-950">D</span>
            </div>
            <span className="text-lg font-bold tracking-tight text-white">
              DREAMS <span className="text-teal-400">Atlas</span>
            </span>
          </Link>
          {/* Cross-nav link to vanilla gallery */}
          <a
            href="../index.html"
            className="hidden text-xs font-medium text-navy-400 transition-colors hover:text-teal-400 sm:inline-flex items-center gap-1"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
            </svg>
            Enterprise Gallery
          </a>
        </div>

        {/* Desktop nav */}
        <div className="hidden items-center gap-8 md:flex">
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className="text-sm font-medium text-navy-300 transition-colors hover:text-white"
            >
              {item.name}
            </Link>
          ))}
          <Link href="/contact" className="btn-primary text-xs">
            Get in Touch
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden text-white"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            {mobileOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile nav */}
      {mobileOpen && (
        <div className="border-t border-white/5 bg-navy-950/95 backdrop-blur-lg md:hidden">
          <div className="space-y-1 px-4 py-4">
            <a
              href="../index.html"
              className="block rounded-lg px-3 py-2 text-sm font-medium text-teal-400 hover:bg-white/5"
              onClick={() => setMobileOpen(false)}
            >
              Enterprise Gallery
            </a>
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="block rounded-lg px-3 py-2 text-sm font-medium text-navy-300 hover:bg-white/5 hover:text-white"
                onClick={() => setMobileOpen(false)}
              >
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
