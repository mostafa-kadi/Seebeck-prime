"""
Dataset: central scientific data model.

The ThermoelectricDataset is the single source of truth for all measured
and calculated thermoelectric properties at each temperature point.
All properties are stored in SI base units.

The GUI table and plots are views of the dataset, not independent data stores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class ThermoelectricDataset:
    """
    Container for a single thermoelectric sample's data.

    All array fields are parallel arrays (same length).
    All values are in SI base units:
        T        → K
        sigma    → S/m
        S        → V/K
        kappa    → W/(m·K)
        PF       → W/(m·K²)
        ZT       → dimensionless
        kappa_e  → W/(m·K)
        kappa_L  → W/(m·K)
        n        → m⁻³
        mu       → m²/(V·s)

    Uncertainty fields (prefix ``u_``) are absolute uncertainties in the same SI unit.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    name: str = "Unnamed Sample"
    description: str = ""

    # ── Primary measured / imported data ─────────────────────────────────────
    T: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    sigma: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    S: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    kappa: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))

    # ── Calculated properties ─────────────────────────────────────────────────
    PF: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    ZT: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    kappa_e: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    kappa_L: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))

    # ── Hall / carrier transport ──────────────────────────────────────────────
    n: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    mu: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    R_H: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))

    # ── Uncertainties (absolute, same SI unit) ────────────────────────────────
    u_T: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    u_sigma: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    u_S: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    u_kappa: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    u_PF: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    u_ZT: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    u_kappa_e: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    u_kappa_L: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))

    # ── Data origin tags (one per T-point, e.g. "measured", "calculated") ────
    origin_sigma: list[str] = field(default_factory=list)
    origin_S: list[str] = field(default_factory=list)
    origin_kappa: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.T)

    def is_empty(self) -> bool:
        return len(self.T) == 0

    def has_uncertainty(self) -> bool:
        """Return True if at least one uncertainty array has been set."""
        return (
            len(self.u_sigma) > 0
            or len(self.u_S) > 0
            or len(self.u_kappa) > 0
        )

    def clear_calculated(self) -> None:
        """Reset all calculated fields so they can be recomputed."""
        empty = np.array([], dtype=float)
        self.PF = empty.copy()
        self.ZT = empty.copy()
        self.kappa_e = empty.copy()
        self.kappa_L = empty.copy()
        self.u_PF = empty.copy()
        self.u_ZT = empty.copy()
        self.u_kappa_e = empty.copy()
        self.u_kappa_L = empty.copy()
