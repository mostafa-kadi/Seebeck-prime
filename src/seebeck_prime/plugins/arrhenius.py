"""
Arrhenius-type analysis for thermoelectric transport.

Supports:
    - log(sigma) vs 1/T  (standard Arrhenius)
    - log(sigma*T) vs 1/T  (polaronic / small-polaron transport)

Activation energy is derived from the slope of the linear fit.
"""

from __future__ import annotations

import numpy as np
from seebeck_prime.domain.analysis import linear_regression
from seebeck_prime.domain.constants import GAS_CONSTANT, BOLTZMANN, ELECTRON_CHARGE


def arrhenius_ln_sigma(
    temperature_k: np.ndarray,
    sigma: np.ndarray,
) -> dict:
    """
    Standard Arrhenius analysis: ln(sigma) vs 1/T.

    Model:
        ln(sigma) = ln(sigma_0) - E_a / (k_B * T)
        => slope = -E_a / k_B  (when x = 1/T in K^-1)

    Activation energy:
        E_a [eV] = -slope * k_B / e
        E_a [J/mol] = -slope * R

    Args:
        temperature_k: Temperature array [K].
        sigma: Electrical conductivity array [S/m] (must be > 0).

    Returns:
        Dict with keys:
            x (1/T), y (ln sigma),
            slope, intercept, r_squared, stderr,
            E_a_eV, E_a_J_per_mol,
            sigma_0 (pre-exponential factor)
    """
    T = np.asarray(temperature_k, dtype=float)
    s = np.asarray(sigma, dtype=float)
    mask = (T > 0) & (s > 0) & np.isfinite(T) & np.isfinite(s)
    x = 1.0 / T[mask]
    y = np.log(s[mask])  # natural logarithm

    reg = linear_regression(x, y)
    slope = reg["slope"]

    E_a_eV = -slope * BOLTZMANN / ELECTRON_CHARGE if np.isfinite(slope) else np.nan
    E_a_J_per_mol = -slope * GAS_CONSTANT if np.isfinite(slope) else np.nan
    sigma_0 = float(np.exp(reg["intercept"])) if np.isfinite(reg["intercept"]) else np.nan

    return dict(
        x=x,
        y=y,
        **reg,
        E_a_eV=E_a_eV,
        E_a_J_per_mol=E_a_J_per_mol,
        sigma_0=sigma_0,
        log_type="ln",
        model="ln(sigma) vs 1/T",
    )


def arrhenius_ln_sigma_T(
    temperature_k: np.ndarray,
    sigma: np.ndarray,
) -> dict:
    """
    Polaronic Arrhenius analysis: ln(sigma*T) vs 1/T.

    Model:
        ln(sigma*T) = ln(A) - E_a / (k_B * T)
        => slope = -E_a / k_B

    Args:
        temperature_k: Temperature array [K].
        sigma: Electrical conductivity array [S/m] (must be > 0).

    Returns:
        Dict with the same keys as ``arrhenius_ln_sigma``.
    """
    T = np.asarray(temperature_k, dtype=float)
    s = np.asarray(sigma, dtype=float)
    mask = (T > 0) & (s > 0) & np.isfinite(T) & np.isfinite(s)
    x = 1.0 / T[mask]
    y = np.log(s[mask] * T[mask])  # natural logarithm

    reg = linear_regression(x, y)
    slope = reg["slope"]

    E_a_eV = -slope * BOLTZMANN / ELECTRON_CHARGE if np.isfinite(slope) else np.nan
    E_a_J_per_mol = -slope * GAS_CONSTANT if np.isfinite(slope) else np.nan
    A = float(np.exp(reg["intercept"])) if np.isfinite(reg["intercept"]) else np.nan

    return dict(
        x=x,
        y=y,
        **reg,
        E_a_eV=E_a_eV,
        E_a_J_per_mol=E_a_J_per_mol,
        sigma_0=A,
        log_type="ln",
        model="ln(sigma*T) vs 1/T",
    )


def arrhenius_log10_sigma(
    temperature_k: np.ndarray,
    sigma: np.ndarray,
) -> dict:
    """
    Arrhenius analysis using log10: log10(sigma) vs 1/T.

    Model:
        log10(sigma) = log10(sigma_0) - E_a / (ln(10) * k_B * T)
        => E_a [eV] = -slope * ln(10) * k_B / e

    Note: Using log10 instead of ln changes the activation energy formula.
    This function explicitly applies the correct conversion.
    """
    T = np.asarray(temperature_k, dtype=float)
    s = np.asarray(sigma, dtype=float)
    mask = (T > 0) & (s > 0) & np.isfinite(T) & np.isfinite(s)
    x = 1.0 / T[mask]
    y = np.log10(s[mask])

    reg = linear_regression(x, y)
    slope = reg["slope"]

    # Corrected: multiply by ln(10) to account for base-10 log
    E_a_eV = -slope * np.log(10.0) * BOLTZMANN / ELECTRON_CHARGE if np.isfinite(slope) else np.nan
    E_a_J_per_mol = -slope * np.log(10.0) * GAS_CONSTANT if np.isfinite(slope) else np.nan
    sigma_0 = float(10.0 ** reg["intercept"]) if np.isfinite(reg["intercept"]) else np.nan

    return dict(
        x=x,
        y=y,
        **reg,
        E_a_eV=E_a_eV,
        E_a_J_per_mol=E_a_J_per_mol,
        sigma_0=sigma_0,
        log_type="log10",
        model="log10(sigma) vs 1/T",
    )
