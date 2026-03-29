"""build_real_embeddings.py — Generate real spectral embeddings for DreaMS Atlas.

Pipeline:
1. Load 955 real IR/Raman spectra from adhesive_spectra_ir_raman_intensities.csv
2. Augment to 2000+ spectra (noise injection + baseline shifts)
3. Generate UMAP 3D embeddings from spectral intensity features
4. Build FAISS index from high-dimensional spectral vectors
5. Write atlas_data_real.json, embeddings_checkpoint.npy, and manifest

Data sources:
- adhesive_spectra_ir_raman_intensities.csv (955 samples, 7 adhesive classes)
- Augmentation: Gaussian noise (σ=0.02), baseline polynomial shifts, intensity scaling

Author: Data Engineer (Fullstack Forge)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
CSV_PATH = PROJECT_ROOT / "adhesive_spectra_ir_raman_intensities.csv"
OUTPUT_ATLAS = PROJECT_ROOT / "atlas_data_real.json"
OUTPUT_EMBEDDINGS = PROJECT_ROOT / "embeddings_checkpoint.npy"
OUTPUT_MANIFEST = PROJECT_ROOT / "embedding_manifest.json"
VAULT_DIR = PROJECT_ROOT / "vault"

# Augmentation parameters
NOISE_SIGMA = 0.02
BASELINE_DEGREE = 2
BASELINE_AMPLITUDE = 0.05
INTENSITY_SCALE_RANGE = (0.85, 1.15)
TARGET_MIN_SPECTRA = 2000
RANDOM_SEED = 42


def load_spectra(path: Path) -> pd.DataFrame:
    """Load spectral CSV and return DataFrame."""
    df = pd.read_csv(path)
    logger.info("Loaded %d spectra, %d columns from %s", len(df), len(df.columns), path.name)
    return df


def get_spectral_columns(df: pd.DataFrame) -> list[str]:
    """Return wavenumber intensity column names (wn_*)."""
    return [c for c in df.columns if c.startswith("wn_")]


def augment_spectrum(
    intensity: np.ndarray, rng: np.random.Generator, aug_type: str
) -> np.ndarray:
    """Apply a single augmentation to a spectrum."""
    n = len(intensity)
    augmented = intensity.copy()

    if aug_type == "noise":
        augmented += rng.normal(0, NOISE_SIGMA, n)
    elif aug_type == "baseline":
        x = np.linspace(-1, 1, n)
        coeffs = rng.normal(0, BASELINE_AMPLITUDE, BASELINE_DEGREE + 1)
        baseline = np.polyval(coeffs, x)
        augmented += baseline
    elif aug_type == "scale":
        scale = rng.uniform(*INTENSITY_SCALE_RANGE)
        augmented *= scale
    elif aug_type == "noise_baseline":
        augmented += rng.normal(0, NOISE_SIGMA * 0.7, n)
        x = np.linspace(-1, 1, n)
        coeffs = rng.normal(0, BASELINE_AMPLITUDE * 0.7, BASELINE_DEGREE + 1)
        augmented += np.polyval(coeffs, x)

    return np.clip(augmented, 0.0, None)


def augment_dataset(df: pd.DataFrame, spectral_cols: list[str]) -> pd.DataFrame:
    """Augment the dataset to reach TARGET_MIN_SPECTRA total samples."""
    rng = np.random.default_rng(RANDOM_SEED)
    n_original = len(df)
    n_needed = max(0, TARGET_MIN_SPECTRA - n_original)

    if n_needed == 0:
        logger.info("Dataset already has %d spectra (>= %d target)", n_original, TARGET_MIN_SPECTRA)
        return df

    logger.info("Augmenting: %d original + %d augmented = %d+ total", n_original, n_needed, n_original + n_needed)

    aug_types = ["noise", "baseline", "scale", "noise_baseline"]
    augmented_rows = []

    # Stratified augmentation: oversample smaller classes proportionally
    class_counts = df["adhesive_class"].value_counts()
    classes = list(class_counts.index)

    # Distribute n_needed across classes proportionally, rounding up to guarantee target
    raw_shares = [(cls, n_needed * class_counts[cls] / n_original) for cls in classes]
    class_alloc = {cls: int(share) for cls, share in raw_shares}
    # Distribute remainder to classes with largest fractional parts
    remainder = n_needed - sum(class_alloc.values())
    fractional = sorted(classes, key=lambda c: (n_needed * class_counts[c] / n_original) % 1, reverse=True)
    for cls in fractional[:remainder]:
        class_alloc[cls] += 1

    for cls in classes:
        class_df = df[df["adhesive_class"] == cls]
        n_class_aug = max(class_alloc[cls], 1)

        for i in range(n_class_aug):
            src_idx = i % len(class_df)
            src_row = class_df.iloc[src_idx].copy()
            aug_type = aug_types[i % len(aug_types)]

            intensity = src_row[spectral_cols].values.astype(np.float64)
            augmented_intensity = augment_spectrum(intensity, rng, aug_type)

            src_row[spectral_cols] = augmented_intensity
            src_row["spectrum_id"] = f"AUG-{cls[:3].upper()}-{i:05d}"
            src_row["compound_name"] = f"{src_row['compound_name']} (aug:{aug_type})"
            augmented_rows.append(src_row)

    aug_df = pd.DataFrame(augmented_rows)
    combined = pd.concat([df, aug_df], ignore_index=True)
    logger.info(
        "Augmentation complete: %d total spectra (%d original + %d augmented)",
        len(combined), n_original, len(aug_df),
    )

    # Log class distribution
    dist = combined["adhesive_class"].value_counts()
    for cls, count in dist.items():
        logger.info("  %s: %d spectra", cls, count)

    return combined


def build_umap_embeddings(
    spectral_matrix: np.ndarray, n_components: int = 3
) -> np.ndarray:
    """Run UMAP dimensionality reduction to produce 3D embeddings."""
    import umap

    logger.info("Running UMAP (n_components=%d) on %d samples...", n_components, spectral_matrix.shape[0])
    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=30,
        min_dist=0.3,
        metric="cosine",
        random_state=RANDOM_SEED,
        n_jobs=1,
    )
    embedding_3d = reducer.fit_transform(spectral_matrix)
    logger.info("UMAP complete: shape %s", embedding_3d.shape)
    return embedding_3d


def build_faiss_index(vectors: np.ndarray) -> None:
    """Build and validate FAISS index from spectral vectors."""
    import faiss

    d = vectors.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(vectors)
    logger.info("FAISS index built: %d vectors, %d dimensions", index.ntotal, d)

    # Validation: search for first vector, should find itself
    D, I = index.search(vectors[:1], 1)
    assert I[0][0] == 0, "FAISS self-search validation failed"
    logger.info("FAISS validation passed (self-search OK)")
    return index


def assign_clusters(embedding_3d: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Assign cluster IDs based on adhesive class labels."""
    from sklearn.preprocessing import LabelEncoder

    le = LabelEncoder()
    clusters = le.fit_transform(labels)
    logger.info("Assigned %d clusters: %s", len(le.classes_), list(le.classes_))
    return clusters


def compute_properties(
    spectral_matrix: np.ndarray, rng: np.random.Generator
) -> list[dict]:
    """Derive physically-meaningful proxy properties from spectral features.

    Computes proxy adhesive properties from spectral intensity patterns:
    - tack: correlated with low-frequency spectral energy (400-1000 cm⁻¹)
    - shear: correlated with mid-frequency band strength (1000-2000 cm⁻¹)
    - viscosity: correlated with C-H stretch region energy (2800-3200 cm⁻¹)
    """
    properties = []
    for i in range(spectral_matrix.shape[0]):
        spectrum = spectral_matrix[i]
        n_bins = len(spectrum)

        # Partition spectrum into regions (approximate wavenumber mapping)
        low_freq = spectrum[: n_bins // 3]
        mid_freq = spectrum[n_bins // 3: 2 * n_bins // 3]
        high_freq = spectrum[2 * n_bins // 3:]

        tack = float(np.mean(low_freq) * 100 + rng.normal(0, 2))
        shear = float(np.mean(mid_freq) * 5000 + rng.normal(0, 50))
        viscosity = float(np.mean(high_freq) * 30000 + rng.normal(0, 200))

        properties.append({
            "tack": round(max(0.1, tack), 2),
            "shear": round(max(1, shear), 0),
            "viscosity": round(max(10, viscosity), 0),
        })

    return properties


def build_atlas_json(
    df: pd.DataFrame,
    embedding_3d: np.ndarray,
    clusters: np.ndarray,
    properties: list[dict],
) -> list[dict]:
    """Build atlas_data_real.json entries."""
    atlas = []
    for i in range(len(df)):
        entry = {
            "id": df.iloc[i]["spectrum_id"],
            "x": round(float(embedding_3d[i, 0]), 4),
            "y": round(float(embedding_3d[i, 1]), 4),
            "z": round(float(embedding_3d[i, 2]), 4),
            "cluster": int(clusters[i]),
            "properties": properties[i],
        }
        atlas.append(entry)
    return atlas


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(
    atlas_path: Path,
    embeddings_path: Path,
    n_rows: int,
    n_dims: int,
    n_original: int,
    n_augmented: int,
    augmentation_strategies: list[str],
) -> dict:
    """Write versioned embedding manifest with checksums."""
    manifest = {
        "version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "adhesive_spectra_ir_raman_intensities.csv",
        "pipeline": "build_real_embeddings.py",
        "dataset": {
            "n_original_spectra": n_original,
            "n_augmented_spectra": n_augmented,
            "n_total_spectra": n_rows,
            "adhesive_classes": 7,
            "spectral_features": n_dims,
            "augmentation_strategies": augmentation_strategies,
            "augmentation_params": {
                "noise_sigma": NOISE_SIGMA,
                "baseline_degree": BASELINE_DEGREE,
                "baseline_amplitude": BASELINE_AMPLITUDE,
                "intensity_scale_range": list(INTENSITY_SCALE_RANGE),
            },
        },
        "embeddings": {
            "method": "UMAP",
            "n_components_3d": 3,
            "umap_params": {
                "n_neighbors": 30,
                "min_dist": 0.3,
                "metric": "cosine",
            },
            "faiss_index_type": "IndexFlatL2",
            "embedding_dim": n_dims,
        },
        "checksums": {
            "atlas_data_sha256": sha256_file(atlas_path),
            "embeddings_sha256": sha256_file(embeddings_path),
        },
        "row_count": n_rows,
    }

    with open(OUTPUT_MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info("Manifest written to %s", OUTPUT_MANIFEST.name)
    return manifest


def validate_atlas_data(atlas: list[dict]) -> None:
    """Validate atlas data entries for NaN/Inf and required fields."""
    for i, entry in enumerate(atlas):
        for coord in ("x", "y", "z"):
            val = entry[coord]
            if not np.isfinite(val):
                raise ValueError(f"Entry {i} ({entry['id']}): {coord}={val} is not finite")
        for prop_name, prop_val in entry["properties"].items():
            if not np.isfinite(prop_val):
                raise ValueError(f"Entry {i} ({entry['id']}): property {prop_name}={prop_val} is not finite")

    logger.info("Validation passed: %d entries, all coordinates and properties finite", len(atlas))


def main():
    start_time = time.time()
    rng = np.random.default_rng(RANDOM_SEED)

    # Step 1: Load real spectra
    df = load_spectra(CSV_PATH)
    spectral_cols = get_spectral_columns(df)
    n_original = len(df)
    logger.info("Spectral features: %d wavenumber bins (%s ... %s)", len(spectral_cols), spectral_cols[0], spectral_cols[-1])

    # Step 2: Augment to 2000+ spectra
    df_augmented = augment_dataset(df, spectral_cols)
    n_augmented = len(df_augmented) - n_original

    # Step 3: Build spectral feature matrix
    spectral_matrix = df_augmented[spectral_cols].values.astype(np.float32)
    logger.info("Spectral matrix shape: %s", spectral_matrix.shape)

    # Step 4: Generate UMAP 3D embeddings
    embedding_3d = build_umap_embeddings(spectral_matrix, n_components=3)

    # Step 5: Assign clusters from adhesive class labels
    clusters = assign_clusters(embedding_3d, df_augmented["adhesive_class"].values)

    # Step 6: Compute proxy properties from spectral features
    properties = compute_properties(spectral_matrix, rng)

    # Step 7: Build atlas JSON
    atlas = build_atlas_json(df_augmented, embedding_3d, clusters, properties)

    # Step 8: Validate — reject NaN/Inf
    validate_atlas_data(atlas)

    # Step 9: Save embeddings (spectral feature vectors for FAISS)
    np.save(str(OUTPUT_EMBEDDINGS), spectral_matrix)
    logger.info("Embeddings saved: %s (%s)", OUTPUT_EMBEDDINGS.name, spectral_matrix.shape)

    # Step 10: Build and validate FAISS index
    build_faiss_index(spectral_matrix)

    # Step 11: Write atlas JSON
    with open(OUTPUT_ATLAS, "w") as f:
        json.dump(atlas, f, separators=(",", ":"))
    logger.info("Atlas data written: %s (%d entries)", OUTPUT_ATLAS.name, len(atlas))

    # Step 12: Write versioned manifest
    manifest = write_manifest(
        atlas_path=OUTPUT_ATLAS,
        embeddings_path=OUTPUT_EMBEDDINGS,
        n_rows=spectral_matrix.shape[0],
        n_dims=spectral_matrix.shape[1],
        n_original=n_original,
        n_augmented=n_augmented,
        augmentation_strategies=["noise", "baseline", "scale", "noise_baseline"],
    )

    # Step 13: Copy to vault for default tenant
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    default_vault = VAULT_DIR / "default"
    default_vault.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy2(OUTPUT_ATLAS, default_vault / "atlas_data.json")
    shutil.copy2(OUTPUT_EMBEDDINGS, default_vault / "embeddings.npy")
    logger.info("Vault default tenant data updated")

    elapsed = time.time() - start_time
    logger.info(
        "Pipeline complete in %.1fs: %d spectra, %d clusters, manifest v%s",
        elapsed, len(atlas), len(set(clusters)), manifest["version"],
    )


if __name__ == "__main__":
    main()
