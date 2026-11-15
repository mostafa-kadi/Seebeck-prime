"""Independent thermoelectric transport models."""

from __future__ import annotations

import numpy as np

from seebeck_prime.domain.physical_constants import KB_OVER_E_UV_K

_WEIGHTED_MOBILITY_COEFFICIENT = 331.0


def calculate_weighted_mobility(temperature_k, resistivity_mohm_cm, seebeck_uv_k):
    """Calculate Snyder et al. weighted mobility.

    Implements the empirical expression reported by Snyder et al.,
    Advanced Materials 32 (2020), 2001537, DOI: 10.1002/adma.202001537.

    Parameters
    ----------
    temperature_k:
        Absolute temperature in K.
    resistivity_mohm_cm:
        Electrical resistivity in mΩ·cm.
    seebeck_uv_k:
        Seebeck coefficient in µV/K. Its sign is removed as specified by
        the published expression.

    Returns
    -------
    float or numpy.ndarray
        Weighted mobility in cm²/(V·s). Inputs are broadcast together.
        Non-finite inputs, non-positive temperatures, and non-positive
        resistivities produce NaN at the corresponding output positions.

    Notes
    -----
    With s = |S|/(k_B/e), the shape factor is

        exp(s - 2) / (1 + exp(-5(s - 1)))
        + (3/pi²) s / (1 + exp(5(s - 1))).

    The logistic factors are evaluated in log space to avoid overflow.
    The T^(-3/2) factor reflects the acoustic-phonon-scattering
    approximation used by the empirical expression. Weighted mobility is
    not Hall mobility and is not an experimentally validated output for
    the benchmark set currently shipped with this application.
    """
    temperature, resistivity, seebeck = np.broadcast_arrays(
        np.asarray(temperature_k, dtype=float),
        np.asarray(resistivity_mohm_cm, dtype=float),
        np.asarray(seebeck_uv_k, dtype=float),
    )

    valid = (
        np.isfinite(temperature)
        & np.isfinite(resistivity)
        & np.isfinite(seebeck)
        & (temperature > 0.0)
        & (resistivity > 0.0)
    )
    reduced_seebeck = np.abs(seebeck) / _KB_OVER_E_UV_K

    # Stable evaluation of 1/(1 + exp(-x)) and 1/(1 + exp(x)).
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        logistic_positive = np.exp(
            -np.logaddexp(0.0, -5.0 * (reduced_seebeck - 1.0))
        )
        logistic_negative = np.exp(
            -np.logaddexp(0.0, 5.0 * (reduced_seebeck - 1.0))
        )
        term1 = np.exp(reduced_seebeck - 2.0) * logistic_positive
        term2 = (
            (3.0 / np.pi**2)
            * reduced_seebeck
            * logistic_negative
        )
        shape_factor = term1 + term2
        temperature_factor = (temperature / 300.0) ** (-1.5)
        result = (
            _WEIGHTED_MOBILITY_COEFFICIENT
            * (1.0 / resistivity)
            * temperature_factor
            * shape_factor
        )

    return np.where(valid, result, np.nan)


def resistivity_to_mohm_cm(value, unit):
    """Convert the supported UI transport units to mΩ·cm."""
    if unit == "mΩ·cm":
        return value
    if unit == "Ω·m":
        return value * 1e5
    if unit == "S/cm":
        return 1000.0 / value
    if unit == "S/m":
        return 1e5 / value
    return value
