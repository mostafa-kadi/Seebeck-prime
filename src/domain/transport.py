"""Independent thermoelectric transport models."""

from __future__ import annotations

import numpy as np

from seebeck_prime.domain.physical_constants import KB_OVER_E_UV_K

# Retained to preserve the established weighted-mobility implementation.
# The reduced Seebeck uses the exact CODATA value k_B/e = 86.173332621... uV/K
# (previously a rounded 86.1733 literal; the difference is 3.8e-7 relative).
_KB_E_UV_K = KB_OVER_E_UV_K
_WEIGHTED_MOBILITY_COEFFICIENT = 331.0


def calculate_weighted_mobility(temperature_k, resistivity_mohm_cm, seebeck_uv_k):
    """Calculate the application's Snyder-style weighted mobility estimate.

    Units: temperature [K], resistivity [mΩ·cm], Seebeck [µV/K], output
    [cm²/(V·s)]. This preserves the prior UI-logic algorithm and defaults.

    The implemented expression is

        mu_w = 331 * (1/rho) * (T/300)^(-1.5) * shape(|S|/(k_B/e))
        shape(s) = exp(s-2)/(1+exp(-5(s-1)))
                   + 3*pi^2/(s*(1+exp(5(s-1))))

    Assumptions of the underlying approximation (see
    docs/SCIENTIFIC_EQUATION_AUDIT.md, issue SE-020):

    * The temperature factor (T/300)^(-1.5) assumes acoustic-phonon
      (deformation-potential) scattering, i.e. mu ~ T^(-3/2).
    * The shape factor is a closed-form approximation of the SPB transport
      integrals expressed through the reduced Seebeck coefficient.
    * The prefactor 331.0 is an empirical constant that also carries the
      unit conversion between mOhm*cm and cm^2/(V*s).

    Known limitations (see validation/remediation/WEIGHTED_MOBILITY_AUDIT.md):

    * The shape factor **diverges as |S| -> 0** because of its 3*pi^2/s
      term, so the estimator returns values far above any physical mobility
      (1-1000 cm^2/(V*s)) for Seebeck coefficients below ~1 uV/K.
    * This is **not** the Hall mobility: mu_H = |R_H|*sigma is a different
      physical quantity, and the two coincide only in the non-degenerate
      limit with an effective mass near the electron mass.
    * The model has **no experimental validation** - the only published
      carrier-mobility curve in the benchmark set is negative and unusable.
    * An earlier revision of the scientific model register printed a
      different expression, which this implementation does not evaluate;
      the two differ by a factor of 1.5 to 8.2. The implementation was not
      changed, because the primary source and an experimental reference are
      both unavailable.
    """
    temperature = np.array(temperature_k, dtype=float)
    resistivity = np.array(resistivity_mohm_cm, dtype=float)
    seebeck = np.abs(np.array(seebeck_uv_k, dtype=float))

    reduced_seebeck = seebeck / _KB_E_UV_K
    term1 = np.exp(reduced_seebeck - 2) / (
        1 + np.exp(-5 * (reduced_seebeck - 1))
    )
    term2 = (3 * (np.pi**2) / (reduced_seebeck + 1e-9)) / (
        1 + np.exp(5 * (reduced_seebeck - 1))
    )
    shape_factor = term1 + term2
    temperature_factor = (temperature / 300.0) ** (-1.5)
    resistivity = np.where(resistivity == 0, np.nan, resistivity)
    return _WEIGHTED_MOBILITY_COEFFICIENT * (1 / resistivity) * temperature_factor * shape_factor


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
