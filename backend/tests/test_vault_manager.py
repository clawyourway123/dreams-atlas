"""Tests for backend.vault_manager — tenant path resolution and index caching."""

import json
from pathlib import Path

import numpy as np
import pytest

from backend.vault_manager import VaultManager, get_data_paths


# ---------------------------------------------------------------------------
# get_data_paths
# ---------------------------------------------------------------------------


def test_get_data_paths_returns_defaults_when_no_tenant_files(tmp_path):
    """Falls back to project-level atlas/embeddings when vault dir is absent."""
    atlas_path, embeddings_path = get_data_paths("acme", tmp_path)

    assert atlas_path == tmp_path / "atlas_data.json"
    assert embeddings_path == tmp_path / "embeddings_checkpoint.npy"


def test_get_data_paths_returns_tenant_files_when_present(tmp_path):
    """Returns tenant-specific paths when vault/<tenant_id>/ files exist."""
    tenant_dir = tmp_path / "vault" / "acme"
    tenant_dir.mkdir(parents=True)
    (tenant_dir / "atlas_data.json").write_text("[]")
    (tenant_dir / "embeddings.npy").write_bytes(b"")

    atlas_path, embeddings_path = get_data_paths("acme", tmp_path)

    assert atlas_path == tenant_dir / "atlas_data.json"
    assert embeddings_path == tenant_dir / "embeddings.npy"


def test_get_data_paths_mixed_fallback(tmp_path):
    """Tenant atlas present but embeddings absent → use tenant atlas, default embeddings."""
    tenant_dir = tmp_path / "vault" / "beta"
    tenant_dir.mkdir(parents=True)
    (tenant_dir / "atlas_data.json").write_text("[]")
    # No embeddings file in tenant dir

    atlas_path, embeddings_path = get_data_paths("beta", tmp_path)

    assert atlas_path == tenant_dir / "atlas_data.json"
    assert embeddings_path == tmp_path / "embeddings_checkpoint.npy"


# ---------------------------------------------------------------------------
# VaultManager.get_tenant_data
# ---------------------------------------------------------------------------


def test_vault_manager_returns_dict_with_required_keys(tmp_path):
    """get_tenant_data must return vectors, id_map, reverse_map, and index."""
    vm = VaultManager(tmp_path)
    data = vm.get_tenant_data("default")

    assert "vectors" in data
    assert "id_map" in data
    assert "reverse_map" in data
    assert "index" in data


def test_vault_manager_loads_tenant_specific_atlas(tmp_path):
    """VaultManager reads per-tenant atlas_data.json and builds correct id_map."""
    items = [{"id": f"MOL_{i}"} for i in range(10)]
    tenant_dir = tmp_path / "vault" / "client_alpha"
    tenant_dir.mkdir(parents=True)
    (tenant_dir / "atlas_data.json").write_text(json.dumps(items))

    vm = VaultManager(tmp_path)
    data = vm.get_tenant_data("client_alpha")

    assert data["id_map"][0] == "MOL_0"
    assert data["id_map"][9] == "MOL_9"
    assert data["reverse_map"]["MOL_0"] == 0


def test_vault_manager_caches_second_call(tmp_path):
    """Calling get_tenant_data twice returns the same dict object (cached)."""
    vm = VaultManager(tmp_path)
    first = vm.get_tenant_data("default")
    second = vm.get_tenant_data("default")

    assert first is second


def test_vault_manager_invalidate_clears_cache(tmp_path):
    """invalidate() removes tenant from cache so next call reloads."""
    vm = VaultManager(tmp_path)
    first = vm.get_tenant_data("default")
    vm.invalidate("default")
    reloaded = vm.get_tenant_data("default")

    # After invalidation, a fresh dict is returned (different object)
    assert first is not reloaded


def test_vault_manager_vectors_are_float32(tmp_path):
    """Loaded (or generated) vectors must be float32 for FAISS/numpy compatibility."""
    vm = VaultManager(tmp_path)
    data = vm.get_tenant_data("default")

    assert data["vectors"].dtype == np.float32


def test_vault_manager_loads_embeddings_npy(tmp_path):
    """VaultManager loads real .npy embeddings when present in vault dir."""
    rng = np.random.default_rng(0)
    vecs = rng.random((5, 16), dtype=np.float32)

    tenant_dir = tmp_path / "vault" / "lab"
    tenant_dir.mkdir(parents=True)
    np.save(str(tenant_dir / "embeddings.npy"), vecs)

    # Minimal atlas so id_map is populated
    items = [{"id": f"X_{i}"} for i in range(5)]
    (tenant_dir / "atlas_data.json").write_text(json.dumps(items))

    vm = VaultManager(tmp_path)
    data = vm.get_tenant_data("lab")

    assert data["vectors"].shape == (5, 16)
    np.testing.assert_array_equal(data["vectors"], vecs)
