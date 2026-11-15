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
from .physical_constants import (
    ATOMIC_WEIGHTS,
    DEFAULT_LORENZ,
    LEGACY_ATOMIC_WEIGHTS,
    LEGACY_GAS_CONSTANT,
)

# A chemical formula supported by this parser: repeated Element[Count] groups
# separated by optional whitespace, e.g. "Bi2Te3", "Bi2 Te3", "Al2O3", "Cu".
# Parentheses, brackets, dots and fractional stoichiometry are intentionally
# not supported (they are rejected, not silently mis-parsed).
_SIMPLE_FORMULA_RE = re.compile(r"(?:[A-Z][a-z]?\d*\s*)+")

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

    Scalars, NumPy arrays and pandas Series may be mixed freely; the result
    keeps the container semantics of the inputs (pandas Series stay
    index-aligned Series, arrays stay arrays, scalars stay scalars).

    Args:
        pf: Power Factor PF [W/(m·K²)].
        temperature: T [K].
        kappa_total: Total thermal conductivity κtotal [W/(m·K)].

    Returns:
        Dimensionless figure of merit ZT.
    """
    if np.ndim(kappa_total) == 0 and np.ndim(pf) == 0 and np.ndim(temperature) == 0:
        if kappa_total == 0:
            return 0.0
        return (pf * temperature) / kappa_total

    # Arithmetic is performed on the original objects so that pandas Series
    # keep their index alignment; broadcasting handles scalar/array mixes.
    with np.errstate(divide="ignore", invalid="ignore"):
        result = (pf * temperature) / kappa_total

    zero_mask = kappa_total == 0
    if np.any(zero_mask):
        mask_method = getattr(result, "mask", None)
        if callable(mask_method):  # pandas Series/DataFrame
            result = mask_method(zero_mask, 0.0)
        else:
            result = np.where(zero_mask, 0.0, result)
    return result


# ─── Lorenz Number Estimation ─────────────────────────────────────────────────


def estimate_lorenz(seebeck_uv_k: float | np.ndarray) -> float | np.ndarray:
    """
    Empirical Lorenz number approximation (Kim et al. 2015).

    Formula:
        L ≈ (1.5 + exp(−|S| / 116)) × 10⁻⁸  [W·Ω/K²]

    This fast estimator is accurate to within ~5 % for most thermoelectrics
    but is NOT a substitute for the rigorous SPB Lorenz number for precision work.

    Applicability (see validation/remediation/SIGE_LORENZ_INVESTIGATION.md):
    the relation is fitted to the **acoustic-phonon** single-parabolic-band
    model, so it inherits that model's assumptions. Measured against a
    published P-doped SiGe alloy it underestimates the published Lorenz number
    by **35 %**, because that alloy's effective scattering exponent is
    λ ≈ 1.41 (alloy/optical to ionised-impurity) rather than the acoustic
    λ = 0. Do not use this estimator for alloys whose transport is dominated
    by alloy or ionised-impurity scattering.

    Args:
        seebeck_uv_k: Seebeck coefficient |S| [µV/K].

    Returns:
        Estimated Lorenz number L [W·Ω/K²].

    Reference:
        Kim, H.S. et al. (2015). APL Materials, 3, 041506.
    """
    return (1.5 + np.exp(-np.abs(seebeck_uv_k) / 116.0)) * 1e-8


# ─── Molecular Weight ─────────────────────────────────────────────────────────


def calculate_molecular_weight(
    formula: str, atomic_weights: dict[str, float] = ATOMIC_WEIGHTS
) -> tuple[float | None, int]:
    """
    Calculate molar mass and atom count from a chemical formula string.

    Only simple (unbracketed) formulas are supported, e.g. ``"Bi2Te3"`` or
    ``"Al2O3"``. Formulas using parentheses/brackets or fractional stoichiometry
    (e.g. ``"Ca3(PO4)2"``, ``"Na0.5"``) are rejected and return ``(None, 0)``:
    the previous parser silently returned a *wrong* molar mass for them
    (e.g. 184.2 g/mol instead of 310.17 g/mol for Ca3(PO4)2).
    See docs/SCIENTIFIC_EQUATION_AUDIT.md (issue SE-002).

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

    # Validate the whole string: sequences of Element[Count] only.
    if not _SIMPLE_FORMULA_RE.fullmatch(formula):
        return None, 0

    total_mw = 0.0
    num_atoms = 0
    elements = re.findall(r"([A-Z][a-z]*)(\d*)", formula)
    if not elements:
        return None, 0

    try:
        for element, count_str in elements:
            count = int(count_str) if count_str else 1
            if element not in atomic_weights:
                raise KeyError(element)
            total_mw += atomic_weights[element] * count
            num_atoms += count
        return total_mw, num_atoms
    except KeyError:
        return None, 0


def calculate_legacy_molecular_weight(formula: str) -> tuple[float | None, int]:
    """Formula mass using the complete legacy element table and values."""
    return calculate_molecular_weight(formula, LEGACY_ATOMIC_WEIGHTS)


def calculate_dulong_petit_limit(
    atom_count: int, molar_mass_g_mol: float, unit: str = "J/mol·K"
) -> float:
    """Return the Dulong-Petit heat-capacity limit in the requested legacy unit.

    C_V = 3 n R. The named ``LEGACY_GAS_CONSTANT`` is used, so that the
    literal is no longer duplicated in this module.

    Known, deliberate difference: ``domain.phonon.dulong_petit_molar`` uses
    the exact CODATA-derived ``GAS_CONSTANT``, so this legacy path is lower
    by 1.8e-11 relative (8.314462618 J/(mol*K) versus 8.31446261815324).
    The difference is far below any physical significance and the legacy
    value is kept so that the established display behaviour is unchanged;
    aligning the two is an open item (audit finding D-11).
    """
    molar_limit = atom_count * 3 * LEGACY_GAS_CONSTANT
    if unit == "J/mol·K":
        return molar_limit
    return molar_limit / (molar_mass_g_mol / 1000)
