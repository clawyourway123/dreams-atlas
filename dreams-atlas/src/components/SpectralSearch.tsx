'use client';

import { useState, useMemo, useRef, useEffect } from 'react';

interface Compound {
  id: number;
  name: string;
  family: string;
  modality: string;
  peakSignature: string;
  similarity: number;
  color: string;
}

const FAMILY_COLORS: Record<string, string> = {
  'Acrylic/PSA': '#3b82f6',
  Cyanoacrylate: '#8b5cf6',
  Epoxy: '#f59e0b',
  'Hot-melt': '#ef4444',
  Polyurethane: '#22c55e',
  'Rubber-based': '#f97316',
  Silicone: '#14b8a6',
};

const compounds: Compound[] = [
  { id: 1, name: 'Loctite 3090 PSA', family: 'Acrylic/PSA', modality: 'IR', peakSignature: 'C=O 1730, C-O-C 1160', similarity: 0.95, color: FAMILY_COLORS['Acrylic/PSA'] },
  { id: 2, name: '3M VHB 4910', family: 'Acrylic/PSA', modality: 'FTIR', peakSignature: 'C=O 1730, C-H 2950', similarity: 0.92, color: FAMILY_COLORS['Acrylic/PSA'] },
  { id: 3, name: 'tesa ACXplus 7074', family: 'Acrylic/PSA', modality: 'Raman', peakSignature: 'C=O 1730, C-O-C 1160', similarity: 0.89, color: FAMILY_COLORS['Acrylic/PSA'] },
  { id: 4, name: 'Avery Dennison S8000', family: 'Acrylic/PSA', modality: 'IR', peakSignature: 'C-H 2950, C=O 1730', similarity: 0.87, color: FAMILY_COLORS['Acrylic/PSA'] },
  { id: 5, name: 'Loctite 401', family: 'Cyanoacrylate', modality: 'FTIR', peakSignature: 'C≡N 2240, C=O 1740', similarity: 0.96, color: FAMILY_COLORS.Cyanoacrylate },
  { id: 6, name: 'Permabond 910', family: 'Cyanoacrylate', modality: 'IR', peakSignature: 'C≡N 2240, C=C 1620', similarity: 0.94, color: FAMILY_COLORS.Cyanoacrylate },
  { id: 7, name: 'Infinity CA+ Bond', family: 'Cyanoacrylate', modality: 'Raman', peakSignature: 'C≡N 2240, C=O 1740', similarity: 0.91, color: FAMILY_COLORS.Cyanoacrylate },
  { id: 8, name: 'Araldite AW 106', family: 'Epoxy', modality: 'FTIR', peakSignature: 'Epoxide 915, Aromatic 1610', similarity: 0.93, color: FAMILY_COLORS.Epoxy },
  { id: 9, name: '3M Scotch-Weld DP420', family: 'Epoxy', modality: 'IR', peakSignature: 'O-H 3400, Epoxide 915', similarity: 0.90, color: FAMILY_COLORS.Epoxy },
  { id: 10, name: 'Henkel EA 9395', family: 'Epoxy', modality: 'Raman', peakSignature: 'Aromatic 1610, C-O 1250', similarity: 0.88, color: FAMILY_COLORS.Epoxy },
  { id: 11, name: 'Henkel Technomelt PA 646', family: 'Hot-melt', modality: 'FTIR', peakSignature: 'C-H 2920, C-H 2850', similarity: 0.94, color: FAMILY_COLORS['Hot-melt'] },
  { id: 12, name: 'Bostik Thermogrip 4232', family: 'Hot-melt', modality: 'IR', peakSignature: 'C-H 2920, CH₂ 720', similarity: 0.91, color: FAMILY_COLORS['Hot-melt'] },
  { id: 13, name: 'H.B. Fuller HL 6444', family: 'Hot-melt', modality: 'Raman', peakSignature: 'C-H 2920, C=O 1740', similarity: 0.86, color: FAMILY_COLORS['Hot-melt'] },
  { id: 14, name: 'Sikaflex 252', family: 'Polyurethane', modality: 'FTIR', peakSignature: 'N-H 3330, C=O 1730', similarity: 0.93, color: FAMILY_COLORS.Polyurethane },
  { id: 15, name: 'Loctite PL Premium', family: 'Polyurethane', modality: 'IR', peakSignature: 'N-H 3330, N-H 1540', similarity: 0.90, color: FAMILY_COLORS.Polyurethane },
  { id: 16, name: '3M 550 Fast Cure', family: 'Polyurethane', modality: 'Raman', peakSignature: 'NCO 2270, C=O 1730', similarity: 0.85, color: FAMILY_COLORS.Polyurethane },
  { id: 17, name: '3M Super 77 Spray', family: 'Rubber-based', modality: 'FTIR', peakSignature: 'C-H 2920, C=C 1660', similarity: 0.92, color: FAMILY_COLORS['Rubber-based'] },
  { id: 18, name: 'Bostik Grip N Grab', family: 'Rubber-based', modality: 'IR', peakSignature: 'C=C 1660, =C-H 840', similarity: 0.89, color: FAMILY_COLORS['Rubber-based'] },
  { id: 19, name: 'DAP Weldwood Contact', family: 'Rubber-based', modality: 'Raman', peakSignature: 'C-H 2920, C-H 1450', similarity: 0.87, color: FAMILY_COLORS['Rubber-based'] },
  { id: 20, name: 'Dow Corning 732', family: 'Silicone', modality: 'FTIR', peakSignature: 'Si-O-Si 1020, Si-CH₃ 1260', similarity: 0.97, color: FAMILY_COLORS.Silicone },
  { id: 21, name: 'GE Silicone II', family: 'Silicone', modality: 'IR', peakSignature: 'Si-O-Si 1020, Si-C 800', similarity: 0.94, color: FAMILY_COLORS.Silicone },
  { id: 22, name: 'Permatex Ultra Grey', family: 'Silicone', modality: 'Raman', peakSignature: 'Si-CH₃ 1260, Si-O-Si 490', similarity: 0.91, color: FAMILY_COLORS.Silicone },
];

const families = Object.keys(FAMILY_COLORS);
const modalities = ['IR', 'FTIR', 'Raman'];

export default function SpectralSearch() {
  const [query, setQuery] = useState('');
  const [familyFilter, setFamilyFilter] = useState<string | null>(null);
  const [modalityFilter, setModalityFilter] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'similarity'>('similarity');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    let results = compounds;
    if (query) {
      const q = query.toLowerCase();
      results = results.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.family.toLowerCase().includes(q) ||
          c.peakSignature.toLowerCase().includes(q),
      );
    }
    if (familyFilter) results = results.filter((c) => c.family === familyFilter);
    if (modalityFilter) results = results.filter((c) => c.modality === modalityFilter);
    return [...results].sort((a, b) =>
      sortBy === 'similarity' ? b.similarity - a.similarity : a.name.localeCompare(b.name),
    );
  }, [query, familyFilter, modalityFilter, sortBy]);

  const suggestions = useMemo(() => {
    if (!query || query.length < 2) return [];
    const q = query.toLowerCase();
    const names = compounds.filter((c) => c.name.toLowerCase().includes(q)).map((c) => c.name);
    const peaks = Array.from(new Set(
      compounds
        .flatMap((c) => c.peakSignature.split(', '))
        .filter((p) => p.toLowerCase().includes(q)),
    ));
    return [...names.slice(0, 3), ...peaks.slice(0, 2)];
  }, [query]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (inputRef.current && !inputRef.current.parentElement?.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div>
      {/* Search bar */}
      <div className="relative">
        <div className="relative">
          <svg
            className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-navy-400"
            fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setShowSuggestions(true); }}
            onFocus={() => setShowSuggestions(true)}
            placeholder="Search compounds, families, or spectral peaks (e.g. C=O 1730)..."
            className="w-full rounded-panel border border-white/10 bg-surface/60 py-3 pl-11 pr-4 text-sm text-white placeholder-navy-500 backdrop-blur-sm transition-colors focus:border-teal-400/40 focus:outline-none focus:ring-1 focus:ring-teal-400/20"
            aria-label="Search spectral database"
          />
        </div>

        {/* Autocomplete suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-20 mt-1 w-full rounded-card border border-white/10 bg-navy-900/95 py-1 shadow-card backdrop-blur-lg">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => { setQuery(s); setShowSuggestions(false); }}
                className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-navy-300 transition-colors hover:bg-white/5 hover:text-white"
              >
                <svg className="h-3.5 w-3.5 text-navy-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <span className="text-xs font-medium text-navy-400">Family:</span>
        <div className="flex flex-wrap gap-1.5">
          {families.map((f) => (
            <button
              key={f}
              onClick={() => setFamilyFilter(familyFilter === f ? null : f)}
              className={`rounded-pill px-2.5 py-1 text-[11px] font-medium transition-all ${
                familyFilter === f
                  ? 'text-white shadow-sm'
                  : 'border border-white/5 text-navy-400 hover:text-navy-200'
              }`}
              style={familyFilter === f ? { backgroundColor: FAMILY_COLORS[f] } : undefined}
            >
              {f}
            </button>
          ))}
        </div>

        <div className="mx-2 h-4 w-px bg-white/10" />

        <span className="text-xs font-medium text-navy-400">Modality:</span>
        <div className="flex gap-1.5">
          {modalities.map((m) => (
            <button
              key={m}
              onClick={() => setModalityFilter(modalityFilter === m ? null : m)}
              className={`rounded-pill px-2.5 py-1 text-[11px] font-medium transition-all ${
                modalityFilter === m
                  ? 'bg-teal-500 text-navy-950'
                  : 'border border-white/5 text-navy-400 hover:text-navy-200'
              }`}
            >
              {m}
            </button>
          ))}
        </div>

        <div className="mx-2 h-4 w-px bg-white/10" />

        <button
          onClick={() => setSortBy(sortBy === 'similarity' ? 'name' : 'similarity')}
          className="flex items-center gap-1 rounded-pill border border-white/5 px-2.5 py-1 text-[11px] font-medium text-navy-400 transition-colors hover:text-navy-200"
        >
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 7.5L7.5 3m0 0L12 7.5M7.5 3v13.5m13.5-4.5L16.5 16.5m0 0L12 12m4.5 4.5V3" />
          </svg>
          Sort: {sortBy === 'similarity' ? 'Match Score' : 'Name'}
        </button>
      </div>

      {/* Results */}
      <div className="mt-5 space-y-2">
        <div className="mb-2 text-xs text-navy-400">
          {filtered.length} result{filtered.length !== 1 ? 's' : ''}
        </div>
        {filtered.map((c) => (
          <div
            key={c.id}
            className="group flex items-center gap-4 rounded-card border border-white/5 bg-surface/40 p-4 transition-all hover:border-white/10 hover:bg-surface/60"
          >
            {/* Color indicator */}
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg" style={{ backgroundColor: c.color + '20' }}>
              <div className="h-3 w-3 rounded-full" style={{ backgroundColor: c.color }} />
            </div>

            {/* Info */}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-white">{c.name}</span>
                <span className="rounded-pill bg-white/5 px-2 py-0.5 text-[10px] font-medium text-navy-400">
                  {c.modality}
                </span>
              </div>
              <div className="mt-1 flex items-center gap-2 text-xs text-navy-400">
                <span style={{ color: c.color }}>{c.family}</span>
                <span className="text-navy-600">|</span>
                <span className="font-mono">{c.peakSignature}</span>
              </div>
            </div>

            {/* Similarity score */}
            <div className="flex-shrink-0 text-right">
              <div className="text-sm font-bold" style={{ color: c.color }}>
                {(c.similarity * 100).toFixed(0)}%
              </div>
              <div className="mt-0.5 h-1.5 w-16 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${c.similarity * 100}%`, backgroundColor: c.color }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
