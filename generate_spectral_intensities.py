"""
KDE-95: Generate spectral intensity dataset for IR+Raman adhesive classification.

Creates realistic synthetic spectral data based on known vibrational signatures
of adhesive compound classes. Each adhesive class has characteristic peaks at
specific wavenumbers; these are modeled as Gaussian/Lorentzian profiles with
per-compound variation and noise.

Output: adhesive_spectra_ir_raman_intensities.csv
  - Metadata: spectrum_id, compound_name, adhesive_class, spectral_type
  - Intensity columns: wn_400, wn_418, ..., wn_4000 (200 bins)
"""

import csv
import numpy as np
from pathlib import Path

np.random.seed(42)

# --- Wavenumber grid: 200 bins from 400 to 4000 cm-1 ---
N_BINS = 200
WAVENUMBERS = np.linspace(400, 4000, N_BINS)
WN_COLS = [f"wn_{int(round(w))}" for w in WAVENUMBERS]


def lorentzian(x, center, amplitude, width):
    """Lorentzian peak profile (common for IR/Raman peaks)."""
    return amplitude * (width**2) / ((x - center)**2 + width**2)


def gaussian(x, center, amplitude, width):
    """Gaussian peak profile."""
    return amplitude * np.exp(-0.5 * ((x - center) / width)**2)


# --- Characteristic peaks by adhesive class ---
# Format: (center_cm-1, amplitude, width_cm-1) for each class
# These are based on well-known vibrational spectroscopy assignments.

IR_PEAKS = {
    "Epoxy": [
        (830, 0.6, 20),    # Epoxide ring breathing
        (915, 0.55, 18),   # Epoxide C-O deformation
        (1035, 0.4, 25),   # C-O-C symmetric stretch
        (1250, 0.7, 22),   # C-O stretch (aromatic ether)
        (1510, 0.5, 20),   # Aromatic C=C
        (1608, 0.45, 18),  # Aromatic C=C ring stretch
        (2870, 0.3, 30),   # C-H stretch (symmetric)
        (2930, 0.35, 30),  # C-H stretch (asymmetric)
        (3400, 0.5, 80),   # O-H stretch (broad, from curing)
    ],
    "Acrylic/PSA": [
        (750, 0.25, 15),   # C-H out-of-plane
        (1160, 0.55, 22),  # C-O-C stretch
        (1240, 0.4, 20),   # C-O stretch
        (1380, 0.3, 18),   # CH3 symmetric bend
        (1450, 0.35, 20),  # CH2 scissor
        (1730, 0.85, 20),  # C=O stretch (ester, dominant)
        (2870, 0.3, 25),   # C-H symmetric stretch
        (2950, 0.45, 30),  # C-H asymmetric stretch
        (3450, 0.2, 60),   # O-H (if hydroxyl present)
    ],
    "Polyurethane": [
        (770, 0.2, 15),    # C-H wag
        (1080, 0.4, 25),   # C-O-C stretch
        (1220, 0.5, 22),   # C-N stretch + N-H bend
        (1310, 0.3, 18),   # Amide III
        (1530, 0.6, 22),   # N-H bending (Amide II)
        (1730, 0.7, 22),   # C=O stretch (urethane)
        (2870, 0.3, 25),   # C-H symmetric
        (2930, 0.4, 28),   # C-H asymmetric
        (3300, 0.55, 50),  # N-H stretch (hydrogen bonded)
    ],
    "Cyanoacrylate": [
        (810, 0.25, 15),   # C-H out-of-plane
        (1060, 0.4, 22),   # C-O stretch
        (1190, 0.35, 18),  # C-O-C stretch
        (1370, 0.25, 15),  # CH3 deformation
        (1450, 0.3, 18),   # CH2 scissor
        (1740, 0.7, 20),   # C=O stretch (ester)
        (2240, 0.65, 15),  # C≡N stretch (diagnostic!)
        (2950, 0.35, 28),  # C-H stretch
    ],
    "Silicone": [
        (490, 0.3, 20),    # Si-O-Si rocking
        (800, 0.6, 20),    # Si-C stretch (very characteristic)
        (1020, 0.85, 35),  # Si-O-Si asymmetric stretch (dominant)
        (1095, 0.5, 25),   # Si-O-Si (shoulder)
        (1260, 0.7, 15),   # Si-CH3 symmetric deformation (sharp!)
        (1410, 0.3, 15),   # CH3 asymmetric deformation
        (2960, 0.4, 25),   # C-H stretch
    ],
    "Hot-melt": [
        (720, 0.45, 18),   # CH2 rocking (crystalline PE/EVA)
        (1020, 0.3, 25),   # C-O stretch (EVA)
        (1240, 0.35, 22),  # C-O-C (vinyl acetate)
        (1375, 0.3, 15),   # CH3 symmetric bend
        (1465, 0.5, 18),   # CH2 scissoring
        (1740, 0.5, 22),   # C=O stretch (vinyl acetate)
        (2850, 0.55, 25),  # CH2 symmetric stretch
        (2920, 0.65, 25),  # CH2 asymmetric stretch
    ],
    "Rubber-based": [
        (690, 0.3, 18),    # C-S stretch or =C-H wag
        (840, 0.25, 15),   # =C-H out-of-plane
        (1000, 0.3, 22),   # C-C stretch
        (1130, 0.25, 18),  # C-C stretch
        (1310, 0.3, 18),   # CH2 twist
        (1450, 0.45, 20),  # CH2 scissor
        (1660, 0.5, 22),   # C=C stretch (backbone, diagnostic)
        (2855, 0.4, 25),   # CH2 symmetric stretch
        (2960, 0.5, 28),   # CH3 asymmetric stretch
        (3040, 0.2, 15),   # =C-H stretch
    ],
}

# Raman peaks differ in relative intensity from IR (different selection rules)
RAMAN_PEAKS = {
    "Epoxy": [
        (640, 0.3, 18),    # Epoxide ring deformation
        (830, 0.5, 18),    # Epoxide ring breathing (Raman active)
        (1110, 0.35, 22),  # C-O-C
        (1250, 0.4, 20),   # C-O stretch
        (1460, 0.3, 18),   # CH2 deformation
        (1610, 0.65, 18),  # Aromatic C=C (strong in Raman!)
        (2870, 0.25, 25),  # C-H symmetric
        (2930, 0.35, 28),  # C-H asymmetric
        (3060, 0.3, 20),   # Aromatic C-H
    ],
    "Acrylic/PSA": [
        (600, 0.2, 18),    # C-C-O deformation
        (810, 0.3, 18),    # C-O-C stretch
        (990, 0.25, 20),   # CH out-of-plane
        (1160, 0.35, 20),  # C-O-C symmetric
        (1450, 0.45, 20),  # CH2/CH3 deformation
        (1640, 0.25, 18),  # C=C (residual monomer)
        (1730, 0.55, 20),  # C=O (weaker in Raman than IR)
        (2940, 0.6, 30),   # C-H stretch (strong in Raman)
    ],
    "Polyurethane": [
        (635, 0.2, 15),    # N-C=O deformation
        (1065, 0.35, 22),  # C-O-C stretch
        (1310, 0.3, 18),   # Amide III
        (1445, 0.4, 20),   # CH2 deformation
        (1535, 0.3, 18),   # Amide II (weaker in Raman)
        (1620, 0.35, 18),  # Aromatic C=C (if MDI/TDI based)
        (1730, 0.45, 20),  # C=O (urethane)
        (2870, 0.35, 25),  # C-H symmetric
        (2930, 0.5, 28),   # C-H asymmetric
    ],
    "Cyanoacrylate": [
        (600, 0.2, 15),    # skeleton
        (835, 0.25, 18),   # C-C stretch
        (1060, 0.3, 20),   # C-O stretch
        (1450, 0.35, 20),  # CH2 deformation
        (1740, 0.4, 18),   # C=O (weaker in Raman)
        (2240, 0.75, 12),  # C≡N (very strong in Raman!)
        (2940, 0.45, 28),  # C-H stretch
    ],
    "Silicone": [
        (490, 0.5, 20),    # Si-O-Si symmetric stretch (strong Raman!)
        (620, 0.25, 15),   # Si-O-Si rocking
        (710, 0.3, 15),    # Si-C stretch
        (800, 0.4, 18),    # Si-C stretch
        (1265, 0.5, 12),   # Si-CH3 (sharp, diagnostic)
        (1410, 0.2, 15),   # CH3 deformation
        (2910, 0.35, 22),  # C-H symmetric
        (2970, 0.5, 25),   # C-H asymmetric
    ],
    "Hot-melt": [
        (400, 0.15, 15),   # lattice mode
        (720, 0.25, 15),   # CH2 rocking
        (1065, 0.3, 22),   # C-O (EVA)
        (1130, 0.35, 18),  # C-C stretch (crystalline)
        (1300, 0.3, 18),   # CH2 twist
        (1440, 0.5, 20),   # CH2 scissor
        (1740, 0.3, 18),   # C=O (EVA, weak Raman)
        (2850, 0.6, 22),   # CH2 symmetric (strong Raman!)
        (2890, 0.55, 22),  # CH2 Fermi resonance
        (2920, 0.65, 22),  # CH2 asymmetric
    ],
    "Rubber-based": [
        (410, 0.15, 15),   # S-S stretch (if vulcanized)
        (700, 0.2, 15),    # C-S or =C-H
        (1000, 0.3, 20),   # C-C stretch
        (1310, 0.3, 18),   # CH2 twist
        (1450, 0.4, 20),   # CH2 scissor
        (1665, 0.7, 18),   # C=C stretch (very strong in Raman!)
        (2860, 0.4, 25),   # CH2 symmetric
        (2935, 0.5, 25),   # CH3/CH2 asymmetric
        (3010, 0.3, 12),   # =C-H stretch
    ],
}


def generate_spectrum(adhesive_class, spectral_type, compound_seed):
    """
    Generate a realistic spectral intensity vector for a given adhesive class
    and spectral type. Uses characteristic peaks with per-compound variation.
    """
    rng = np.random.RandomState(compound_seed)

    # Select peak table based on spectral type
    if spectral_type == "Raman":
        peaks = RAMAN_PEAKS[adhesive_class]
    else:
        peaks = IR_PEAKS[adhesive_class]

    # Start with a baseline (slight slope + low-frequency variation)
    baseline_level = rng.uniform(0.02, 0.08)
    baseline_slope = rng.uniform(-1e-5, 1e-5)
    spectrum = baseline_level + baseline_slope * (WAVENUMBERS - 2000)

    # Add broad fluorescence background for Raman (common artifact)
    if spectral_type == "Raman":
        fluor_center = rng.uniform(1500, 2500)
        fluor_amp = rng.uniform(0.0, 0.08)
        fluor_width = rng.uniform(800, 1500)
        spectrum += gaussian(WAVENUMBERS, fluor_center, fluor_amp, fluor_width)

    # Add characteristic peaks with per-compound variation
    for center, amp, width in peaks:
        # Vary center ±5 cm-1, amplitude ±25%, width ±20%
        c = center + rng.normal(0, 3)
        a = amp * rng.uniform(0.75, 1.25)
        w = width * rng.uniform(0.8, 1.2)

        # Mix of Lorentzian (70%) and Gaussian (30%) for Voigt-like profile
        spectrum += 0.7 * lorentzian(WAVENUMBERS, c, a, w)
        spectrum += 0.3 * gaussian(WAVENUMBERS, c, a, w)

    # Add minor random peaks (overtones, combinations, impurities)
    n_minor = rng.randint(1, 4)
    for _ in range(n_minor):
        mc = rng.uniform(500, 3500)
        ma = rng.uniform(0.02, 0.1)
        mw = rng.uniform(10, 30)
        spectrum += gaussian(WAVENUMBERS, mc, ma, mw)

    # Add realistic noise (higher noise at higher wavenumbers for IR)
    noise_level = rng.uniform(0.005, 0.02)
    if spectral_type in ("IR", "FTIR"):
        noise = noise_level * (1 + 0.3 * (WAVENUMBERS - 400) / 3600)
    else:
        noise = noise_level * np.ones_like(WAVENUMBERS)
    spectrum += rng.normal(0, noise)

    # Ensure non-negative
    spectrum = np.clip(spectrum, 0, None)

    # Normalize to [0, 1] range
    smax = spectrum.max()
    if smax > 0:
        spectrum = spectrum / smax

    return spectrum


def main():
    input_file = "adhesive_spectra_ir_raman_955.csv"
    output_file = "adhesive_spectra_ir_raman_intensities.csv"

    # Read existing metadata
    with open(input_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Read {len(rows)} spectra from {input_file}")

    # Create compound-based seeds for reproducibility
    # Same compound should have correlated spectra
    compound_seeds = {}
    seed_counter = 1000
    for row in rows:
        cn = row["compound_name"]
        if cn not in compound_seeds:
            compound_seeds[cn] = seed_counter
            seed_counter += 1

    # Generate and write output
    meta_cols = ["spectrum_id", "compound_name", "adhesive_class", "spectral_type"]
    header = meta_cols + WN_COLS

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for i, row in enumerate(rows):
            # Seed: base compound seed + row index for variation within compound
            base_seed = compound_seeds[row["compound_name"]]
            spectrum_seed = base_seed * 10000 + i

            spectrum = generate_spectrum(
                row["adhesive_class"],
                row["spectral_type"],
                spectrum_seed,
            )

            meta = [row[c] for c in meta_cols]
            intensities = [f"{v:.6f}" for v in spectrum]
            writer.writerow(meta + intensities)

            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{len(rows)} spectra...")

    print(f"\nDone! Wrote {len(rows)} spectra × {N_BINS} wavenumber bins to {output_file}")
    print(f"Wavenumber range: {WAVENUMBERS[0]:.0f} - {WAVENUMBERS[-1]:.0f} cm-1")
    print(f"Column count: {len(header)} ({len(meta_cols)} metadata + {N_BINS} intensity)")

    # Quick validation
    import pandas as pd
    df = pd.read_csv(output_file)
    intensity_cols = [c for c in df.columns if c.startswith("wn_")]
    print(f"\nValidation:")
    print(f"  Shape: {df.shape}")
    print(f"  Intensity range: [{df[intensity_cols].min().min():.4f}, {df[intensity_cols].max().max():.4f}]")
    print(f"  Mean intensity per class:")
    for cls in sorted(df["adhesive_class"].unique()):
        mean_val = df.loc[df["adhesive_class"] == cls, intensity_cols].mean().mean()
        print(f"    {cls}: {mean_val:.4f}")


if __name__ == "__main__":
    main()
