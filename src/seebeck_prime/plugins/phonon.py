"""
Phonon / lattice thermal conductivity models.

Only models actually used in Seebeck Prime are included here.
Currently supported:
    - Dulong–Petit heat capacity limit
    - Debye heat capacity model (numerical)
    - Thermal diffusivity → thermal conductivity conversion

References:
    - Callaway, J. (1959). Model for Lattice Thermal Conductivity at Low Temperatures.
      Physical Review, 113(4), 1046.
    - Debye, P. (1912). Zur Theorie der spezifischen Waerme. Annalen der Physik, 344(14).
"""

from __future__ import annotations

import numpy as np
from seebeck_prime.domain.constants import GAS_CONSTANT, BOLTZMANN


# ─── Dulong–Petit Limit ───────────────────────────────────────────────────────

def dulong_petit_molar(n_atoms: int) -> float:
    """
    Dulong–Petit (classical) molar heat capacity limit.

    Formula:
        C_v = 3 * n * R  [J/(mol*K)]

    Args:
        n_atoms: Number of atoms per formula unit.

    Returns:
        Molar heat capacity [J/(mol*K)].
    """
    return 3.0 * n_atoms * GAS_CONSTANT


def dulong_petit_specific(n_atoms: int, molar_mass_g_mol: float) -> float:
    """
    Dulong–Petit specific heat capacity.

    Args:
        n_atoms: Number of atoms per formula unit.
        molar_mass_g_mol: Molar mass M [g/mol].

    Returns:
        Specific heat capacity [J/(kg*K)].
    """
    molar_J_molK = dulong_petit_molar(n_atoms)
    return molar_J_molK / (molar_mass_g_mol * 1e-3)


# ─── Thermal Conductivity from Laser Flash ────────────────────────────────────

def kappa_from_diffusivity(
    diffusivity_mm2s: float | np.ndarray,
    cp_J_gK: float | np.ndarray,
    density_g_cm3: float | np.ndarray,
) -> float | np.ndarray:
    """
    Calculate thermal conductivity from laser flash analysis results.

    Formula:
        kappa = alpha * Cp * rho  [W/(m*K)]

    Units are converted from typical laboratory inputs to SI internally.

    Args:
        diffusivity_mm2s: Thermal diffusivity alpha [mm²/s].
        cp_J_gK: Specific heat capacity Cp [J/(g*K)].
        density_g_cm3: Mass density rho [g/cm³].

    Returns:
        Thermal conductivity kappa [W/(m*K)].
    """
    alpha_m2s = np.asarray(diffusivity_mm2s, dtype=float) * 1e-6
    cp_J_kgK = np.asarray(cp_J_gK, dtype=float) * 1000.0
    rho_kg_m3 = np.asarray(density_g_cm3, dtype=float) * 1000.0
    return alpha_m2s * cp_J_kgK * rho_kg_m3


def kappa_from_diffusivity_si(
    diffusivity_m2s: float | np.ndarray,
    cp_J_kgK: float | np.ndarray,
    density_kg_m3: float | np.ndarray,
) -> float | np.ndarray:
    """
    Calculate thermal conductivity using SI units throughout.

    Formula:
        kappa = alpha * Cp * rho  [W/(m*K)]

    Args:
        diffusivity_m2s: Thermal diffusivity [m²/s].
        cp_J_kgK: Specific heat capacity [J/(kg*K)].
        density_kg_m3: Mass density [kg/m³].

    Returns:
        Thermal conductivity [W/(m*K)].
    """
    return (
        np.asarray(diffusivity_m2s, dtype=float)
        * np.asarray(cp_J_kgK, dtype=float)
        * np.asarray(density_kg_m3, dtype=float)
    )
