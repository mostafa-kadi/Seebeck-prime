import numpy as np
import re
from .constants import ATOMIC_WEIGHTS, DEFAULT_LORENZ


def calculate_pf(seebeck, electrical_conductivity):
    """Calculates Power Factor (PF = S^2 * sigma)."""
    return (seebeck**2) * electrical_conductivity


def calculate_kappa_e(electrical_conductivity, temperature, lorenz=DEFAULT_LORENZ):
    """Calculates Electronic Thermal Conductivity (kappa_e = L * sigma * T)."""
    return lorenz * electrical_conductivity * temperature


def calculate_kappa_l(kappa_total, kappa_e):
    """Calculates Lattice Thermal Conductivity (kappa_l = kappa_total - kappa_e)."""
    return kappa_total - kappa_e


def calculate_zt(pf, temperature, kappa_total):
    """Calculates Figure of Merit (ZT = PF * T / kappa_total)."""
    # Avoid division by zero
    if isinstance(kappa_total, (int, float, np.float64)):
        if kappa_total == 0:
            return 0.0
    elif isinstance(kappa_total, np.ndarray):
        results = np.zeros_like(kappa_total)
        mask = kappa_total != 0
        results[mask] = (pf[mask] * temperature[mask]) / kappa_total[mask]
        return results

    return (pf * temperature) / kappa_total


def estimate_lorenz(seebeck_uv_k):
    """
    Estimates Lorenz number based on Seebeck coefficient (simplified model).
    L = (1.5 + exp(-|S| / 116.0)) * 1e-8 W-Ohm/K^2
    """
    return (1.5 + np.exp(-np.abs(seebeck_uv_k) / 116.0)) * 1e-8


def calculate_molecular_weight(formula):
    """
    Calculates molecular weight and atoms per formula unit from a chemical formula.

    Args:
        formula (str): Chemical formula (e.g., "Al2O3").

    Returns:
        tuple: (total_mw, num_atoms) or (None, 0) if invalid.
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
