"""
Single Parabolic Band (SPB) transport model and Fermi-Dirac integration.

This module provides rigorous numerical calculations for the Single Parabolic
Band (SPB) model across arbitrary degeneracy:
- Numerical Fermi-Dirac integrals F_j(η)
- Reduced Fermi level inversion η from Seebeck coefficient S
- Rigorous Lorenz number L(η) as a function of reduced Fermi level
- Density-of-states effective mass m_d* estimation from experimental (S, n, T)
- Pisarenko curve generation S(n) for benchmarking doping series
- Optimal carrier concentration (n_opt) and maximum power factor (PF_max) prediction
- Empirical fast estimators (Kim et al. 2015, Snyder & Toberer 2008)

Scattering parameter conventions (λ or r):
    - λ = 0 (r = -1/2): Acoustic phonon scattering (deformation potential) - default
    - λ = 1 (r = 1/2) : Polar optical / alloy scattering
    - λ = 2 (r = 3/2) : Ionized impurity scattering (Brooks-Herring)

Scientific references:
    - Snyder, G.J. & Toberer, E.S. (2008). Complex thermoelectric materials.
      Nature Materials, 7, 105–114.
    - May, A.F. & Snyder, G.J. (2012). Introduction to modeling thermoelectric
      properties of semiconductors. In CRC Handbook of Thermoelectrics.
    - Kim, H.S. et al. (2015). Characterization of Lorenz number with Seebeck
      coefficient measurement. APL Materials, 3, 041506.
    - Goldsmid, H.J. (2016). Introduction to Thermoelectricity. Springer.
"""

import numpy as np
import scipy.integrate as integrate
import scipy.optimize as optimize
from typing import Tuple, Union, Optional

from seebeck_prime.domain.constants import (
    BOLTZMANN,
    ELECTRON_CHARGE,
    PLANCK,
    ELECTRON_MASS,
    KB_OVER_E_UV_K,
)

# Pre-factor for carrier concentration in SI: 4 * pi * (2 * m_e * k_B / h^2)^(3/2)
# n = CONST_N0 * (m_d* / m_e)^(3/2) * T^(3/2) * F_1/2(η)  [m^-3]
_CONST_N0_SI = 4.0 * np.pi * ((2.0 * ELECTRON_MASS * BOLTZMANN) / (PLANCK ** 2)) ** 1.5


def fermi_integral(j: float, eta: float) -> float:
    """
    Compute the complete Fermi-Dirac integral of order j:

        F_j(η) = ∫₀^∞ (x^j / (1 + exp(x - η))) dx

    Args:
        j: Order of the Fermi integral (e.g., 0, 0.5, 1, 1.5, 2, 3).
        eta: Reduced Fermi energy η = E_F / (k_B · T) (dimensionless).

    Returns:
        Value of the Fermi-Dirac integral F_j(η).
    """
    if eta < -30.0:
        # Non-degenerate Boltzmann asymptotic limit: F_j(η) ≈ Γ(j + 1) * exp(η)
        import scipy.special as sp
        return float(sp.gamma(j + 1.0) * np.exp(eta))

    if eta > 50.0:
        # Heavily degenerate Sommerfeld asymptotic limit: F_j(η) ≈ η^(j+1) / (j+1)
        return float((eta ** (j + 1.0)) / (j + 1.0))

    # Numerical integration with transformed variable to avoid overflow
    def integrand(x):
        # 1 / (1 + exp(x - eta))
        arg = x - eta
        if arg > 100.0:
            return 0.0
        return (x ** j) / (1.0 + np.exp(arg))

    # Split integration around eta for high accuracy
    upper_bound = max(eta + 40.0, 50.0)
    val, _ = integrate.quad(integrand, 0.0, upper_bound, limit=150, epsrel=1e-8)
    return float(val)


def seebeck_from_reduced_fermi_level(
    eta: Union[float, np.ndarray],
    lambda_scat: float = 0.0,
) -> Union[float, np.ndarray]:
    """
    Calculate the Seebeck coefficient S(η) from the reduced Fermi level η.

    Formula (SPB model):
        S(η) = (k_B / e) · [ ((λ + 2) · F_{λ+1}(η)) / ((λ + 1) · F_λ(η)) − η ]

    For acoustic phonon scattering (λ = 0, r = -1/2):
        S(η) = (k_B / e) · [ (2 · F_1(η)) / F_0(η) − η ]

    Args:
        eta: Reduced Fermi level η = E_F / (k_B · T).
        lambda_scat: Scattering parameter λ. Default 0 (acoustic phonon scattering).

    Returns:
        Seebeck coefficient |S| [µV/K].
    """
    if np.ndim(eta) > 0:
        return np.array([seebeck_from_reduced_fermi_level(e, lambda_scat) for e in eta])

    eta_val = float(eta)
    f_top = fermi_integral(lambda_scat + 1.0, eta_val)
    f_bot = fermi_integral(lambda_scat, eta_val)

    term = ((lambda_scat + 2.0) * f_top) / ((lambda_scat + 1.0) * f_bot) - eta_val
    return float(KB_OVER_E_UV_K * term)


def reduced_fermi_level_from_seebeck(
    seebeck_uv_k: Union[float, np.ndarray],
    lambda_scat: float = 0.0,
) -> Union[float, np.ndarray]:
    """
    Invert Seebeck coefficient S [µV/K] to obtain the reduced Fermi level η.

    Uses robust root finding (Brent's method) against seebeck_from_reduced_fermi_level.

    Args:
        seebeck_uv_k: Absolute Seebeck coefficient |S| [µV/K] (> 0).
        lambda_scat: Scattering parameter λ (default 0.0).

    Returns:
        Reduced Fermi level η = E_F / (k_B · T).
    """
    if np.ndim(seebeck_uv_k) > 0:
        return np.array([reduced_fermi_level_from_seebeck(s, lambda_scat) for s in seebeck_uv_k])

    s_target = abs(float(seebeck_uv_k))
    if s_target < 1e-4:
        return 50.0  # Metal limit

    def objective(eta_guess):
        return seebeck_from_reduced_fermi_level(eta_guess, lambda_scat) - s_target

    # Bracket search between non-degenerate (eta = -20) and degenerate (eta = 40)
    try:
        sol = optimize.brentq(objective, -25.0, 45.0, xtol=1e-5)
        return float(sol)
    except Exception:
        # Fallback to wider bracket
        try:
            sol = optimize.brentq(objective, -50.0, 100.0, xtol=1e-4)
            return float(sol)
        except Exception:
            return np.nan


def rigorous_lorenz_number(
    eta: Union[float, np.ndarray],
    lambda_scat: float = 0.0,
) -> Union[float, np.ndarray]:
    """
    Calculate the rigorous Lorenz number L(η) from the SPB model.

    Formula:
        L(η) = (k_B/e)² · [ ((λ+3)·F_{λ+2}(η)) / ((λ+1)·F_λ(η)) − (((λ+2)·F_{λ+1}(η)) / ((λ+1)·F_λ(η)))² ]

    Args:
        eta: Reduced Fermi level η.
        lambda_scat: Scattering parameter λ (default 0.0).

    Returns:
        Lorenz number L [W·Ω/K²].
    """
    if np.ndim(eta) > 0:
        return np.array([rigorous_lorenz_number(e, lambda_scat) for e in eta])

    eta_val = float(eta)
    f0 = fermi_integral(lambda_scat, eta_val)
    f1 = fermi_integral(lambda_scat + 1.0, eta_val)
    f2 = fermi_integral(lambda_scat + 2.0, eta_val)

    term1 = ((lambda_scat + 3.0) * f2) / ((lambda_scat + 1.0) * f0)
    term2 = (((lambda_scat + 2.0) * f1) / ((lambda_scat + 1.0) * f0)) ** 2

    # (k_B / e)^2 in SI (W·Ω/K^2)
    kb_e_si = BOLTZMANN / ELECTRON_CHARGE
    return float((kb_e_si ** 2) * (term1 - term2))


def calculate_carrier_density_spb(
    eta: Union[float, np.ndarray],
    effective_mass_ratio: float,
    temperature_k: float,
) -> Union[float, np.ndarray]:
    """
    Calculate carrier concentration n [cm⁻³] from SPB model.

    Formula:
        n = 4π · (2 m_d* k_B T / h²)^(3/2) · F_{1/2}(η)  [converted to cm⁻³]

    Args:
        eta: Reduced Fermi level η.
        effective_mass_ratio: Density-of-states effective mass ratio m_d* / m_e [-].
        temperature_k: Absolute temperature T [K].

    Returns:
        Carrier concentration n [cm⁻³].
    """
    if np.ndim(eta) > 0:
        return np.array([calculate_carrier_density_spb(e, effective_mass_ratio, temperature_k) for e in eta])

    f_half = fermi_integral(0.5, float(eta))
    n_m3 = _CONST_N0_SI * (effective_mass_ratio ** 1.5) * (temperature_k ** 1.5) * f_half
    return float(n_m3 * 1e-6)  # to cm^-3


def calculate_effective_mass(
    seebeck_uv_k: float,
    carrier_density_cm3: float,
    temperature_k: float,
    lambda_scat: float = 0.0,
) -> Tuple[float, float]:
    """
    Calculate the density-of-states effective mass m_d* / m_e from experimental (S, n, T).

    Algorithm:
        1. Invert experimental S to find reduced Fermi level η.
        2. Calculate F_{1/2}(η).
        3. Invert n = N₀ (m_d*/m_e)^(3/2) T^(3/2) F_{1/2}(η) to solve for m_d*/m_e.

    Args:
        seebeck_uv_k: Measured Seebeck coefficient |S| [µV/K].
        carrier_density_cm3: Measured carrier concentration n [cm⁻³].
        temperature_k: Measurement temperature T [K].
        lambda_scat: Scattering parameter λ (default 0.0).

    Returns:
        Tuple (effective_mass_ratio, eta):
            - effective_mass_ratio: m_d* / m_e (dimensionless)
            - eta: Inverted reduced Fermi level η
    """
    eta = reduced_fermi_level_from_seebeck(seebeck_uv_k, lambda_scat)
    if np.isnan(eta):
        return np.nan, np.nan

    f_half = fermi_integral(0.5, eta)
    if f_half <= 0 or temperature_k <= 0 or carrier_density_cm3 <= 0:
        return np.nan, eta

    n_m3 = carrier_density_cm3 * 1e6
    # m_d* / m_e = [ n / (CONST_N0 * T^(3/2) * F_1/2(η)) ]^(2/3)
    denom = _CONST_N0_SI * (temperature_k ** 1.5) * f_half
    m_ratio = (n_m3 / denom) ** (2.0 / 3.0)

    return float(m_ratio), float(eta)


def generate_pisarenko_curve(
    effective_mass_ratio: float,
    temperature_k: float,
    n_min_cm3: float = 1e17,
    n_max_cm3: float = 1e21,
    num_points: int = 100,
    lambda_scat: float = 0.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate theoretical Pisarenko curve S vs n for a given effective mass and temperature.

    Args:
        effective_mass_ratio: m_d* / m_e.
        temperature_k: Temperature T [K].
        n_min_cm3: Minimum carrier density [cm⁻³]. Default 1e17.
        n_max_cm3: Maximum carrier density [cm⁻³]. Default 1e21.
        num_points: Number of curve points.
        lambda_scat: Scattering parameter (default 0.0).

    Returns:
        Tuple (n_array_cm3, seebeck_array_uv_k)
    """
    # Span reduced Fermi level from non-degenerate to degenerate
    eta_min = -15.0
    eta_max = 20.0
    eta_grid = np.linspace(eta_min, eta_max, num_points * 2)

    n_grid = np.array([
        calculate_carrier_density_spb(e, effective_mass_ratio, temperature_k)
        for e in eta_grid
    ])
    s_grid = np.array([
        seebeck_from_reduced_fermi_level(e, lambda_scat)
        for e in eta_grid
    ])

    # Filter within user range and sort by n
    mask = (n_grid >= n_min_cm3) & (n_grid <= n_max_cm3)
    if not np.any(mask):
        mask = np.ones_like(n_grid, dtype=bool)

    n_sel = n_grid[mask]
    s_sel = s_grid[mask]

    sort_idx = np.argsort(n_sel)
    return n_sel[sort_idx], s_sel[sort_idx]


def predict_optimal_transport(
    effective_mass_ratio: float,
    temperature_k: float,
    mu_0_cm2_vs: float,
    lambda_scat: float = 0.0,
) -> Tuple[float, float, float, np.ndarray, np.ndarray]:
    """
    Predict optimal carrier concentration n_opt for maximum Power Factor (PF_max)
    within the SPB acoustic-phonon model.

    Formula:
        μ(η) = μ₀ · (F_0(η) / (2 · F_{1/2}(η)))  [acoustic phonon scattering]
        σ(η) = n(η) · e · μ(η)
        PF(η) = S(η)² · σ(η)

    Args:
        effective_mass_ratio: m_d* / m_e.
        temperature_k: T [K].
        mu_0_cm2_vs: Non-degenerate intrinsic mobility parameter μ₀ [cm²/(V·s)].
        lambda_scat: Scattering parameter (default 0.0).

    Returns:
        Tuple (n_opt_cm3, pf_max_mW_mK2, eta_opt, n_curve_cm3, pf_curve_mW_mK2)
    """
    eta_grid = np.linspace(-6.0, 10.0, 150)
    n_list = []
    pf_list = []

    for eta in eta_grid:
        s_uvk = seebeck_from_reduced_fermi_level(eta, lambda_scat)
        s_vk = s_uvk * 1e-6

        n_cm3 = calculate_carrier_density_spb(eta, effective_mass_ratio, temperature_k)
        n_m3 = n_cm3 * 1e6

        # Mobility in SPB acoustic phonon scattering
        f0 = fermi_integral(0.0, eta)
        f_half = fermi_integral(0.5, eta)
        if f_half > 0:
            mu_cm2_vs = mu_0_cm2_vs * (f0 / (2.0 * f_half))
        else:
            mu_cm2_vs = mu_0_cm2_vs

        mu_m2_vs = mu_cm2_vs * 1e-4
        sigma_s_m = n_m3 * ELECTRON_CHARGE * mu_m2_vs

        # PF in W/(m·K^2) -> mW/(m·K^2)
        pf_w = (s_vk ** 2) * sigma_s_m
        pf_mw = pf_w * 1000.0

        n_list.append(n_cm3)
        pf_list.append(pf_mw)

    n_arr = np.array(n_list)
    pf_arr = np.array(pf_list)

    max_idx = np.argmax(pf_arr)
    n_opt = float(n_arr[max_idx])
    pf_max = float(pf_arr[max_idx])
    eta_opt = float(eta_grid[max_idx])

    return n_opt, pf_max, eta_opt, n_arr, pf_arr


# --- Legacy / Fast Empirical Functions (Preserved for compatibility) ---

def estimate_lorenz(seebeck_uv_k: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Fast empirical Lorenz number approximation (Kim et al., 2015)."""
    return (1.5 + np.exp(-np.abs(seebeck_uv_k) / 116.0)) * 1e-8


def calculate_carrier_concentration(seebeck_uv_k: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Fast empirical carrier concentration estimation (Snyder & Toberer, 2008)."""
    A = 1e21
    B = 43.4
    seebeck_uv_k = np.asarray(seebeck_uv_k, dtype=float)
    return A * np.exp(-np.abs(seebeck_uv_k) / B)
