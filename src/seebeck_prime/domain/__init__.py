"""
seebeck_prime.domain
====================
Core scientific logic for thermoelectric data analysis.

This package is intentionally free of GUI, plotting, and infrastructure
dependencies. All quantities are in SI base units unless explicitly noted.
"""

from .physical_constants import (
    BOLTZMANN,
    ELECTRON_CHARGE,
    AVOGADRO,
    GAS_CONSTANT,
    PLANCK,
    ELECTRON_MASS,
    FARADAY,
    DEFAULT_LORENZ,
    ATOMIC_WEIGHTS,
)
from .calculations import (
    calculate_pf,
    calculate_kappa_e,
    calculate_kappa_l,
    calculate_zt,
    estimate_lorenz,
    calculate_molecular_weight,
)
from .uncertainty import (
    propagate_pf_error,
    propagate_kappa_e_error,
    propagate_kappa_l_error,
    propagate_zt_error,
    propagate_sigma_error,
    propagate_kappa_error,
    propagate_density_error,
)
from .units import celsius_to_kelvin, kelvin_to_celsius, to_kelvin, from_kelvin

__all__ = [
    # constants
    "BOLTZMANN",
    "ELECTRON_CHARGE",
    "AVOGADRO",
    "GAS_CONSTANT",
    "PLANCK",
    "ELECTRON_MASS",
    "FARADAY",
    "DEFAULT_LORENZ",
    "ATOMIC_WEIGHTS",
    # calculations
    "calculate_pf",
    "calculate_kappa_e",
    "calculate_kappa_l",
    "calculate_zt",
    "estimate_lorenz",
    "calculate_molecular_weight",
    # uncertainty
    "propagate_pf_error",
    "propagate_kappa_e_error",
    "propagate_kappa_l_error",
    "propagate_zt_error",
    "propagate_sigma_error",
    "propagate_kappa_error",
    "propagate_density_error",
    # units
    "celsius_to_kelvin",
    "kelvin_to_celsius",
    "to_kelvin",
    "from_kelvin",
]
