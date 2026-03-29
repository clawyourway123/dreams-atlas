"""atlas_schema.py — Pydantic validation schemas for atlas data.

Validates atlas_data.json entries on load, rejecting NaN/Inf embeddings
and enforcing required field structure.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator, model_validator

logger = logging.getLogger("dreams-atlas")


class AtlasProperties(BaseModel):
    tack: float
    shear: float
    viscosity: float

    @field_validator("tack", "shear", "viscosity")
    @classmethod
    def must_be_finite(cls, v: float, info) -> float:
        if not math.isfinite(v):
            raise ValueError(f"{info.field_name} must be finite, got {v}")
        return v


class AtlasEntry(BaseModel):
    id: str
    x: float
    y: float
    z: float
    cluster: int
    properties: AtlasProperties

    @field_validator("x", "y", "z")
    @classmethod
    def coords_must_be_finite(cls, v: float, info) -> float:
        if not math.isfinite(v):
            raise ValueError(f"{info.field_name} must be finite, got {v}")
        return v

    @field_validator("cluster")
    @classmethod
    def cluster_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"cluster must be >= 0, got {v}")
        return v


def validate_atlas_data(items: list[dict[str, Any]]) -> list[AtlasEntry]:
    """Validate a list of raw atlas data dicts, returning parsed entries.

    Raises ValueError with details on first invalid entry.
    """
    validated = []
    errors = []
    for i, item in enumerate(items):
        try:
            entry = AtlasEntry.model_validate(item)
            validated.append(entry)
        except Exception as e:
            errors.append(f"Entry {i}: {e}")
            if len(errors) >= 10:
                break

    if errors:
        error_summary = "; ".join(errors[:5])
        raise ValueError(
            f"Atlas data validation failed ({len(errors)} errors): {error_summary}"
        )

    logger.info("Atlas data validated: %d entries OK", len(validated))
    return validated
