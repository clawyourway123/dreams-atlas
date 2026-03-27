"""vault_manager.py — Multi-tenant data path resolution and index caching.

Maps tenant_id to per-tenant atlas_data.json / embeddings.npy paths.
Falls back to the project-level defaults when tenant-specific files are
absent, so existing single-tenant deployments continue to work unchanged.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np

logger = logging.getLogger("dreams-atlas")

# Expected per-tenant file names under vault/<tenant_id>/
_TENANT_ATLAS = "atlas_data.json"
_TENANT_EMBEDDINGS = "embeddings.npy"

# Default project-level file names
_DEFAULT_ATLAS = "atlas_data.json"
_DEFAULT_EMBEDDINGS = "embeddings_checkpoint.npy"


def get_data_paths(
    tenant_id: str, project_root: Path
) -> tuple[Path, Path]:
    """Return (atlas_data_path, embeddings_path) for *tenant_id*.

    Looks for tenant-specific files under ``vault/<tenant_id>/``.
    Falls back to the project-level defaults when not found.

    Args:
        tenant_id: Identifier for the tenant (e.g. ``"client_alpha"``).
        project_root: Absolute path to the project root directory.

    Returns:
        A tuple of ``(atlas_data_path, embeddings_path)`` Paths.
    """
    tenant_dir = project_root / "vault" / tenant_id
    tenant_atlas = tenant_dir / _TENANT_ATLAS
    tenant_embeddings = tenant_dir / _TENANT_EMBEDDINGS

    atlas_path = tenant_atlas if tenant_atlas.exists() else project_root / _DEFAULT_ATLAS
    embeddings_path = (
        tenant_embeddings
        if tenant_embeddings.exists()
        else project_root / _DEFAULT_EMBEDDINGS
    )

    return atlas_path, embeddings_path


class VaultManager:
    """Lazily loads and caches per-tenant search indexes.

    Thread-safety: a module-level lock prevents duplicate loads when two
    requests for the same new tenant arrive simultaneously.
    """

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def get_tenant_data(self, tenant_id: str) -> dict[str, Any]:
        """Return cached index data for *tenant_id*, loading on first call.

        The returned dict has keys: ``vectors``, ``id_map``, ``reverse_map``,
        ``index`` (may be ``None`` if FAISS is unavailable).
        """
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        with self._lock:
            # Double-checked locking — another thread may have loaded while we waited
            if tenant_id in self._cache:
                return self._cache[tenant_id]

            data = self._load(tenant_id)
            self._cache[tenant_id] = data
            return data

    def _load(self, tenant_id: str) -> dict[str, Any]:
        atlas_path, embeddings_path = get_data_paths(tenant_id, self._project_root)

        id_map: dict[int, str] = {}
        reverse_map: dict[str, int] = {}

        if atlas_path.exists():
            with open(atlas_path) as f:
                items = json.load(f)
            for i, item in enumerate(items):
                str_id = item.get("id", f"ID_{i}")
                id_map[i] = str_id
                reverse_map[str_id] = i
            logger.info(
                "VaultManager: loaded %d IDs for tenant '%s'",
                len(id_map),
                tenant_id,
            )

        if embeddings_path.exists():
            vectors = np.load(str(embeddings_path)).astype("float32")
        else:
            logger.warning(
                "VaultManager: no embeddings for tenant '%s', generating mock vectors",
                tenant_id,
            )
            n = max(len(id_map), 100)
            rng = np.random.default_rng(42)
            vectors = rng.random((n, 512), dtype=np.float32)
            if not id_map:
                for i in range(n):
                    id_map[i] = f"ID_{i}"
                    reverse_map[f"ID_{i}"] = i

        # Try FAISS; fall back gracefully if not installed
        faiss_index = None
        try:
            import faiss as _faiss  # noqa: PLC0415

            d = vectors.shape[1]
            faiss_index = _faiss.IndexFlatL2(d)
            faiss_index.add(vectors)
            logger.info(
                "VaultManager: FAISS index built for tenant '%s' (%d vectors)",
                tenant_id,
                vectors.shape[0],
            )
        except Exception:
            logger.info(
                "VaultManager: FAISS unavailable for tenant '%s', numpy fallback active",
                tenant_id,
            )

        return {
            "vectors": vectors,
            "id_map": id_map,
            "reverse_map": reverse_map,
            "index": faiss_index,
        }

    def has_vault(self, tenant_id: str) -> bool:
        """Return True if tenant-specific data files exist under vault/<tenant_id>/."""
        tenant_dir = self._project_root / "vault" / tenant_id
        return (tenant_dir / _TENANT_ATLAS).exists() or (
            tenant_dir / _TENANT_EMBEDDINGS
        ).exists()

    def invalidate(self, tenant_id: str) -> None:
        """Remove cached data for *tenant_id* (e.g. after re-ingestion)."""
        with self._lock:
            self._cache.pop(tenant_id, None)
