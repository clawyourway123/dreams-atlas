import type { SpectrumRow } from "./SpectralPlotViewer";

/**
 * Parse the adhesive_spectra_ir_raman_intensities.csv file into typed rows.
 * Works both server-side (fs read) and client-side (fetch).
 */
export function parseSpectraCSV(csvText: string): SpectrumRow[] {
  const lines = csvText.trim().split("\n");
  const header = lines[0].split(",");

  // Extract wavenumber values from column names (wn_400 -> 400)
  const wnCols = header.slice(4);
  const wavenumbers = wnCols.map((col) => parseFloat(col.replace("wn_", "")));

  const rows: SpectrumRow[] = [];

  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(",");
    if (cols.length < 5) continue;

    rows.push({
      spectrum_id: cols[0],
      compound_name: cols[1],
      adhesive_class: cols[2],
      spectral_type: cols[3] as "IR" | "FTIR" | "Raman",
      wavenumbers,
      intensities: cols.slice(4).map(Number),
    });
  }

  return rows;
}

/**
 * Fetch and parse the spectra CSV from the public directory.
 * Place adhesive_spectra_ir_raman_intensities.csv in /public/data/
 */
export async function fetchSpectra(
  url = "/data/adhesive_spectra_ir_raman_intensities.csv",
): Promise<SpectrumRow[]> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch spectra: ${res.status}`);
  const text = await res.text();
  return parseSpectraCSV(text);
}
