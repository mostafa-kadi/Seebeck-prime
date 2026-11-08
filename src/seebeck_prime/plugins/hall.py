"""
Hall effect and carrier transport calculations.

This module provides GUI-independent scientific functions for analyzing
Hall effect measurements: Hall coefficient (R_H), Hall carrier concentration (n_H),
carrier type determination (n-type vs p-type), Hall mobility (mu_H), and
temperature-dependent scattering exponent analysis (mu_H ~ T^p).

Scientific references:
    - Putley, E. H. (1960). The Hall Effect and Related Phenomena. Butterworths.
    - Goldsmid, H. J. (2016). Introduction to Thermoelectricity. Springer.
    - Snyder, G. J. & Toberer, E. S. (2008). Complex thermoelectric materials.
      Nature Materials, 7, 105–114.
    - Poplavskyy, D. & Nelson, J. (2003). Nondestructive Hall effect measurements.
      J. Appl. Phys.
"""

import numpy as np
from typing import Tuple, Union, Literal
from seebeck_prime.domain.constants import ELECTRON_CHARGE


def calculate_hall_coefficient_from_raw(
    hall_voltage_v: Union[float, np.ndarray],
    thickness_m: float,
    current_a: float,
    magnetic_field_t: float,
) -> Union[float, np.ndarray]:
    """
    Calculate the Hall coefficient R_H from raw experimental measurements.

    Formula:
        R_H = (V_H · t) / (I · B)  [m³/C]

    Args:
        hall_voltage_v: Measured Hall voltage V_H [V].
        thickness_m: Sample thickness t [m].
        current_a: Applied excitation current I [A].
        magnetic_field_t: Applied perpendicular magnetic field B [T].

    Returns:
        Hall coefficient R_H [m³/C]. Positive for p-type, negative for n-type.

    Raises:
        ZeroDivisionError: If current_a or magnetic_field_t is zero.
    """
    if current_a == 0 or magnetic_field_t == 0:
        raise ZeroDivisionError("Current and magnetic field must be non-zero.")
    return (np.asarray(hall_voltage_v) * thickness_m) / (current_a * magnetic_field_t)


def calculate_hall_carrier_density(
    hall_coefficient_m3_c: Union[float, np.ndarray],
    hall_factor: float = 1.0,
) -> Union[float, np.ndarray]:
    """
    Calculate the Hall carrier concentration n_H (or p_H).

    Formula:
        n_H = r_H / (e · |R_H|)  [m⁻³]

    where e is elementary charge (1.602176634e-19 C) and r_H is the Hall factor
    (r_H = 1.0 for degenerate / standard single band assumption;
     r_H = 1.18 for acoustic phonon scattering in non-degenerate SPB).

    Args:
        hall_coefficient_m3_c: Hall coefficient R_H [m³/C].
        hall_factor: Dimensionless Hall scattering factor r_H [-]. Default is 1.0.

    Returns:
        Hall carrier concentration in SI base units [m⁻³].
        Divide by 1e6 to obtain [cm⁻³].
    """
    R_H = np.asarray(hall_coefficient_m3_c, dtype=float)
    R_H_abs = np.abs(R_H)
    
    # Avoid division by zero
    if isinstance(R_H_abs, np.ndarray):
        result = np.zeros_like(R_H_abs, dtype=float)
        mask = R_H_abs > 0
        result[mask] = hall_factor / (ELECTRON_CHARGE * R_H_abs[mask])
        return result
    else:
        if R_H_abs == 0:
            return 0.0
        return hall_factor / (ELECTRON_CHARGE * R_H_abs)


def determine_carrier_type(
    hall_coefficient: Union[float, np.ndarray]
) -> Union[str, np.ndarray]:
    """
    Determine majority carrier type from the sign of the Hall coefficient.

    Sign convention:
        - R_H > 0 -> p-type (holes)
        - R_H < 0 -> n-type (electrons)
        - R_H == 0 -> Undetermined / Intrinsic

    Args:
        hall_coefficient: R_H in any consistent unit.

    Returns:
        'p-type', 'n-type', or 'undetermined' (or an array of strings).
    """
    R_H = np.asarray(hall_coefficient)
    if R_H.ndim == 0:
        val = float(R_H)
        if val > 0:
            return "p-type"
        elif val < 0:
            return "n-type"
        return "undetermined"

    types = np.full(R_H.shape, "undetermined", dtype="<U12")
    types[R_H > 0] = "p-type"
    types[R_H < 0] = "n-type"
    return types


def calculate_hall_mobility(
    hall_coefficient_m3_c: Union[float, np.ndarray],
    electrical_conductivity_s_m: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """
    Calculate the Hall mobility mu_H.

    Formula:
        mu_H = |R_H| · sigma  [m²/(V·s)]

    Multiply by 10,000 (1e4) to convert to standard experimental units [cm²/(V·s)].

    Args:
        hall_coefficient_m3_c: Hall coefficient R_H [m³/C].
        electrical_conductivity_s_m: Electrical conductivity sigma [S/m].

    Returns:
        Hall mobility mu_H [m²/(V·s)].

    Scientific reference:
        Putley, E. H. (1960). The Hall Effect and Related Phenomena.
    """
    R_H = np.abs(np.asarray(hall_coefficient_m3_c, dtype=float))
    sigma = np.asarray(electrical_conductivity_s_m, dtype=float)
    return R_H * sigma


def calculate_hall_mobility_cm2_vs(
    hall_coefficient_cm3_c: Union[float, np.ndarray],
    electrical_conductivity_s_cm: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """
    Calculate Hall mobility directly using experimental laboratory units:
    R_H in [cm³/C] and sigma in [S/cm].

    Formula:
        mu_H = |R_H| · sigma  [cm²/(V·s)]

    Args:
        hall_coefficient_cm3_c: R_H in [cm³/C].
        electrical_conductivity_s_cm: sigma in [S/cm].

    Returns:
        Hall mobility in [cm²/(V·s)].
    """
    R_H = np.abs(np.asarray(hall_coefficient_cm3_c, dtype=float))
    sigma = np.asarray(electrical_conductivity_s_cm, dtype=float)
    return R_H * sigma


def fit_scattering_exponent(
    temperature_k: np.ndarray,
    mobility_cm2_vs: np.ndarray,
) -> Tuple[float, float, float]:
    """
    Fit temperature-dependent Hall mobility to a power law mu_H ~ T^p to identify
    the dominant carrier scattering mechanism.

    Formula:
        ln(mu_H) = p · ln(T) + ln(mu_0)

    Scattering regime guide:
        - p ≈ -1.5 : Acoustic phonon scattering (deformation potential)
        - p ≈ -0.5 to -1.0 : Optical / mixed polar phonon scattering
        - p ≈ +1.5 : Ionized impurity scattering (Brooks-Herring)
        - p ≈ 0 : Neutral impurity / grain boundary barrier dominated

    Args:
        temperature_k: 1D array of temperatures [K] (> 0).
        mobility_cm2_vs: 1D array of Hall mobilities [cm²/(V·s)] (> 0).

    Returns:
        Tuple (p_exponent, mu_0_prefactor, r_squared):
            - p_exponent: Temperature power law exponent p
            - mu_0_prefactor: Prefactor mu_0 in mu = mu_0 * T^p
            - r_squared: Coefficient of determination R² of the log-log fit.
    """
    T = np.asarray(temperature_k, dtype=float)
    mu = np.asarray(mobility_cm2_vs, dtype=float)

    # Filter positive and finite values for log
    valid_mask = (T > 0) & (mu > 0) & np.isfinite(T) & np.isfinite(mu)
    T_clean = T[valid_mask]
    mu_clean = mu[valid_mask]

    if len(T_clean) < 2:
        return np.nan, np.nan, np.nan

    log_T = np.log(T_clean)
    log_mu = np.log(mu_clean)

    # Linear regression on log-log
    p, intercept = np.polyfit(log_T, log_mu, 1)
    mu_0 = float(np.exp(intercept))

    # Calculate R^2
    fitted_log_mu = p * log_T + intercept
    ss_res = np.sum((log_mu - fitted_log_mu) ** 2)
    ss_tot = np.sum((log_mu - np.mean(log_mu)) ** 2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

    return float(p), mu_0, float(r2)
