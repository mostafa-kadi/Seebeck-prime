"""
Core thermoelectric calculations.

All functions are pure, unit-agnostic, and free of GUI/plotting/IO dependencies.
Internal units follow SI conventions (see individual docstrings).

Scientific equations implemented:
    PF  = S² · σ
    κe  = L · σ · T       (Wiedemann–Franz)
    κL  = κ − κe
    ZT  = S² · σ · T / κ  = PF · T / κ
    L   ≈ (1.5 + exp(−|S|/116)) × 10⁻⁸   (Kim et al. 2015 empirical)
    MW  = Σ n_i · atomic_weight_i          (formula unit molar mass)
"""

from __future__ import annotations

import re
import numpy as np
from .physical_constants import ATOMIC_WEIGHTS, DEFAULT_LORENZ

# ─── Power Factor ─────────────────────────────────────────────────────────────


def calculate_pf(
    seebeck: float | np.ndarray,
    electrical_conductivity: float | np.ndarray,
) -> float | np.ndarray:
    """
    Calculate Power Factor.

    Formula:
        PF = S² · σ  [W/(m·K²)]

    Args:
        seebeck: Seebeck coefficient S [V/K].
        electrical_conductivity: Electrical conductivity σ [S/m].

    Returns:
        Power Factor PF [W/(m·K²)].
    """
    return (seebeck**2) * electrical_conductivity


# ─── Thermal Conductivity Components ──────────────────────────────────────────


def calculate_kappa_e(
    electrical_conductivity: float | np.ndarray,
    temperature: float | np.ndarray,
    lorenz: float | np.ndarray = DEFAULT_LORENZ,
) -> float | np.ndarray:
    """
    Calculate the electronic contribution to thermal conductivity (Wiedemann–Franz law).

    Formula:
        κe = L · σ · T  [W/(m·K)]

    Args:
        electrical_conductivity: σ [S/m].
        temperature: T [K].
        lorenz: Lorenz number L [W·Ω/K²]. Defaults to Sommerfeld value.

    Returns:
        Electronic thermal conductivity κe [W/(m·K)].
    """
    return lorenz * electrical_conductivity * temperature


def calculate_kappa_l(
    kappa_total: float | np.ndarray,
    kappa_e: float | np.ndarray,
) -> float | np.ndarray:
    """
    Calculate the lattice (phonon) contribution to thermal conductivity.

    Formula:
        κL = κtotal − κe  [W/(m·K)]

    Args:
        kappa_total: Total measured thermal conductivity κtotal [W/(m·K)].
        kappa_e: Electronic thermal conductivity κe [W/(m·K)].

    Returns:
        Lattice thermal conductivity κL [W/(m·K)].
    """
    return kappa_total - kappa_e


# ─── Figure of Merit ──────────────────────────────────────────────────────────


def calculate_zt(
    pf: float | np.ndarray,
    temperature: float | np.ndarray,
    kappa_total: float | np.ndarray,
) -> float | np.ndarray:
    """
    Calculate the dimensionless thermoelectric figure of merit ZT.

    Formula:
        ZT = PF · T / κtotal = S² · σ · T / κtotal  [dimensionless]

    Division-by-zero is handled: ZT = 0 wherever κtotal = 0.

    Args:
        pf: Power Factor PF [W/(m·K²)].
        temperature: T [K].
        kappa_total: Total thermal conductivity κtotal [W/(m·K)].

    Returns:
        Dimensionless figure of merit ZT.
    """
    if isinstance(kappa_total, np.ndarray):
        result = np.zeros_like(kappa_total, dtype=float)
        mask = kappa_total != 0
        result[mask] = (pf[mask] * temperature[mask]) / kappa_total[mask]
        return result

    if isinstance(kappa_total, (int, float, np.number)):
        if kappa_total == 0:
            return 0.0
        return (pf * temperature) / kappa_total

    # Pandas Series or array-like
    return (pf * temperature) / kappa_total


# ─── Lorenz Number Estimation ─────────────────────────────────────────────────


def estimate_lorenz(seebeck_uv_k: float | np.ndarray) -> float | np.ndarray:
    """
    Empirical Lorenz number approximation (Kim et al. 2015).

    Formula:
        L ≈ (1.5 + exp(−|S| / 116)) × 10⁻⁸  [W·Ω/K²]

    This fast estimator is accurate to within ~5 % for most thermoelectrics
    but is NOT a substitute for the rigorous SPB Lorenz number for precision work.

    Args:
        seebeck_uv_k: Seebeck coefficient |S| [µV/K].

    Returns:
        Estimated Lorenz number L [W·Ω/K²].

    Reference:
        Kim, H.S. et al. (2015). APL Materials, 3, 041506.
    """
    return (1.5 + np.exp(-np.abs(seebeck_uv_k) / 116.0)) * 1e-8


# ─── Molecular Weight ─────────────────────────────────────────────────────────


def calculate_molecular_weight(formula: str) -> tuple[float | None, int]:
    """
    Calculate molar mass and atom count from a chemical formula string.

    Args:
        formula: Chemical formula, e.g. ``"Bi2Te3"`` or ``"Al2O3"``.

    Returns:
        Tuple ``(total_mw, num_atoms)`` where ``total_mw`` is in [g/mol]
        and ``num_atoms`` is atoms per formula unit.
        Returns ``(None, 0)`` if the formula is invalid or contains an
        unknown element.
    """
    formula = formula.strip()
    if not formula:
        return None, 0

    total_mw = 0.0
    num_atoms = 0
    elements = re.findall(r"([A-Z][a-z]*)(\d*)", formula)
    if not elements:
        return None, 0

    try:
        for element, count_str in elements:
            count = int(count_str) if count_str else 1
            if element not in ATOMIC_WEIGHTS:
                raise KeyError(element)
            total_mw += ATOMIC_WEIGHTS[element] * count
            num_atoms += count
        return total_mw, num_atoms
    except KeyError:
        return None, 0
