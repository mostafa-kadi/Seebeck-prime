"""
Application use cases for Seebeck Prime.

Each use case represents one user/application workflow, coordinating
domain calculations and (optionally) infrastructure through the services layer.

Use cases must NOT depend on GUI or plot code.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from seebeck_prime.domain.calculations import (
    calculate_pf,
    calculate_kappa_e,
    calculate_kappa_l,
    calculate_zt,
    estimate_lorenz,
)
from seebeck_prime.domain.uncertainty import (
    propagate_pf_error,
    propagate_kappa_e_error,
    propagate_kappa_l_error,
    propagate_zt_error,
)
from seebeck_prime.domain.constants import DEFAULT_LORENZ
from seebeck_prime.domain.validation import validate_dataset


def calculate_thermoelectric_properties(
    T: np.ndarray,
    sigma: np.ndarray,
    S: np.ndarray,
    kappa: np.ndarray | None = None,
    lorenz: float | str = DEFAULT_LORENZ,
    u_sigma: np.ndarray | None = None,
    u_S: np.ndarray | None = None,
    u_kappa: np.ndarray | None = None,
) -> dict:
    """
    Calculate all thermoelectric properties from measured inputs.

    Args:
        T: Temperature [K].
        sigma: Electrical conductivity [S/m].
        S: Seebeck coefficient [V/K].
        kappa: Total thermal conductivity [W/(m·K)]. Optional.
        lorenz: Lorenz number [W·Ω/K²], or ``"auto"`` for Seebeck-derived estimate.
        u_sigma: Absolute uncertainty in sigma [S/m]. Optional.
        u_S: Absolute uncertainty in S [V/K]. Optional.
        u_kappa: Absolute uncertainty in kappa [W/(m·K)]. Optional.

    Returns:
        Dict with keys: T, sigma, S, kappa, PF, kappa_e, kappa_L, ZT
        and corresponding u_* uncertainty keys if inputs were provided.
    """
    T = np.asarray(T, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    S = np.asarray(S, dtype=float)

    # Lorenz number
    if isinstance(lorenz, str) and lorenz == "auto":
        L = estimate_lorenz(S * 1e6)
    else:
        L = float(lorenz)

    result = {
        "T": T,
        "sigma": sigma,
        "S": S,
        "PF": calculate_pf(S, sigma),
        "kappa_e": calculate_kappa_e(sigma, T, L),
    }

    result["kappa_L"] = None
    result["ZT"] = None

    if kappa is not None:
        kappa = np.asarray(kappa, dtype=float)
        result["kappa"] = kappa
        result["kappa_L"] = calculate_kappa_l(kappa, result["kappa_e"])
        result["ZT"] = calculate_zt(result["PF"], T, kappa)

    # Uncertainties
    if u_sigma is not None and u_S is not None:
        u_sigma = np.asarray(u_sigma, dtype=float)
        u_S = np.asarray(u_S, dtype=float)
        result["u_PF"] = propagate_pf_error(S, u_S, sigma, u_sigma)
        result["u_kappa_e"] = propagate_kappa_e_error(sigma, u_sigma, T, np.zeros_like(T), L, 0.0)

        if kappa is not None and u_kappa is not None:
            u_kappa = np.asarray(u_kappa, dtype=float)
            result["u_kappa"] = u_kappa
            result["u_kappa_L"] = propagate_kappa_l_error(u_kappa, result["u_kappa_e"])
            result["u_ZT"] = propagate_zt_error(
                result["PF"], result["u_PF"],
                T, np.zeros_like(T),
                kappa, u_kappa,
            )

    return result


def calculate_zt_use_case(
    T: np.ndarray,
    sigma: np.ndarray,
    S: np.ndarray,
    kappa: np.ndarray,
    lorenz: float | str = DEFAULT_LORENZ,
) -> np.ndarray:
    """Calculate ZT only, without full property suite."""
    result = calculate_thermoelectric_properties(T, sigma, S, kappa, lorenz)
    return result["ZT"]


def validate_measurement_data(T, sigma=None, S=None, kappa=None):
    """
    Validate measurement inputs and return a list of validation messages.

    Returns:
        List of ValidationMessage objects.
    """
    return validate_dataset(T, sigma=sigma, S=S, kappa=kappa)
