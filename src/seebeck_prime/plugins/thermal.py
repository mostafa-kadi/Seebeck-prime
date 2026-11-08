"""
Thermoelectric thermal transport calculations.

All quantities are in SI base units unless stated otherwise in the docstring.

Scientific references:
    - Wiedemann, G. & Franz, R. (1853). Über die Wärme-Leitungsfähigkeit der Metalle.
      Ann. Phys., 165(8), 497–531.  → κe = L·σ·T (Wiedemann–Franz law)
    - Goldsmid, H.J. (2016). Introduction to Thermoelectricity. Springer.
      → κL = κtotal − κe
"""

import numpy as np
from seebeck_prime.domain.constants import DEFAULT_LORENZ


def calculate_kappa_e(electrical_conductivity: float | np.ndarray,
                      temperature: float | np.ndarray,
                      lorenz: float | np.ndarray = DEFAULT_LORENZ) -> float | np.ndarray:
    """
    Calculate the electronic contribution to thermal conductivity via the
    Wiedemann–Franz law.

    Formula:
        κe = L · σ · T

    where L is the Lorenz number. The standard (Sommerfeld) value
    L₀ = 2.44 × 10⁻⁸ W·Ω/K² is used by default. For semiconductors and
    thermoelectrics with large Seebeck coefficients, use `estimate_lorenz()`
    from `seebeck_prime.domain.models.spb` instead.

    Args:
        electrical_conductivity: σ [S/m].
        temperature: T [K].
        lorenz: Lorenz number L [W·Ω/K²]. Defaults to Sommerfeld value.

    Returns:
        Electronic thermal conductivity κe [W/(m·K)].

    Scientific reference:
        Wiedemann, G. & Franz, R. (1853). Ann. Phys., 165(8), 497–531.
    """
    return lorenz * electrical_conductivity * temperature


def calculate_kappa_l(kappa_total: float | np.ndarray,
                      kappa_e: float | np.ndarray) -> float | np.ndarray:
    """
    Calculate the lattice (phonon) contribution to thermal conductivity.

    Formula:
        κL = κtotal − κe

    This is the standard bipolar/decomposition approach. Note that κL can
    be negative if κe is overestimated (e.g., wrong Lorenz number or units).
    The application's quality-control engine should flag negative κL values.

    Args:
        kappa_total: Total measured thermal conductivity κtotal [W/(m·K)].
        kappa_e: Electronic thermal conductivity κe [W/(m·K)].

    Returns:
        Lattice thermal conductivity κL [W/(m·K)].

    Scientific reference:
        Goldsmid, H.J. (2016). Introduction to Thermoelectricity, Ch. 2.
    """
    return kappa_total - kappa_e
