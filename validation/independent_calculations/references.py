"""Independent reference calculations for the Seebeck Prime validation.

These implementations are written **from the governing equations**, not from
the application source, and they deliberately **do not import any
``seebeck_prime`` calculation function** (see
``validation/INDEPENDENT_REFERENCE_METHODS.md`` for the derivation and
normalisation conventions used here).

Conventions
-----------
* SI base units are used everywhere: V, A, K, m, kg, s.
* The complete Fermi-Dirac integral is evaluated in **Blatt's normalised**
  convention ``F_j(eta) = (1/Gamma(j+1)) * int_0^inf x^j/(1+exp(x-eta)) dx``
  by direct quadrature with ``scipy.integrate.quad``; the application's
  unnormalised convention is checked against it in the test suite.
* Uncertainties are first-order (linearised) Gaussian propagations, except
  where a Monte-Carlo reference is used explicitly.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import gamma as gamma_fn

#: Exact SI constants (CODATA 2018).
K_B = 1.380649e-23            # J/K
E_CHARGE = 1.602176634e-19     # C
N_A = 6.02214076e23            # 1/mol
PLANCK_H = 6.62607015e-34      # J*s
M_E = 9.1093837015e-31         # kg
K_B_OVER_E = K_B / E_CHARGE    # V/K
K_B_OVER_E_UV = K_B_OVER_E * 1e6  # uV/K


# =====================================================================
# Fermi-Dirac integrals and the single parabolic band model
# =====================================================================

def fermi_integral_blatt(j: float, eta: float) -> float:
    """Blatt-normalised complete Fermi-Dirac integral F_j(eta).

    F_j(eta) = (1/Gamma(j+1)) * int_0^inf x^j / (1 + exp(x - eta)) dx

    Evaluated by adaptive quadrature (no asymptotic shortcuts), so the result is
    independent of the application's branch structure.
    """
    upper = max(eta + 80.0, 90.0)
    value, _ = quad(
        lambda x: (x**j) / (1.0 + math.exp(min(x - eta, 700.0))),
        0.0,
        upper,
        limit=400,
        epsrel=1e-11,
        epsabs=1e-18,
    )
    return value / gamma_fn(j + 1.0)


def fermi_integral_unnormalised(j: float, eta: float) -> float:
    """Unnormalised complete Fermi-Dirac integral (Gamma-scaled Blatt form)."""
    return gamma_fn(j + 1.0) * fermi_integral_blatt(j, eta)


def spb_seebeck(eta: float, lambda_scat: float = 0.0) -> float:
    """Seebeck coefficient from the reduced Fermi level [uV/K].

    With Blatt-normalised integrals and the scattering exponent
    r = lambda - 1/2 (lambda = 0 -> acoustic deformation potential):

        S(eta) = (k_B/e) [ (5/2 + r) F_{r+3/2}(eta) / F_{r+1/2}(eta) - eta ]
                = (k_B/e) [ (lambda + 2) F_{lambda+1}(eta) / F_{lambda}(eta) - eta ]

    Limits (checked in the test suite):
      * non-degenerate: F_j ~ exp(eta) -> S -> (k_B/e)(lambda + 2 - eta)
      * degenerate:      F_j ~ eta^(j+1) -> S -> 0
    """
    f_low = fermi_integral_blatt(lambda_scat, eta)
    f_high = fermi_integral_blatt(lambda_scat + 1.0, eta)
    bracket = (lambda_scat + 2.0) * f_high / f_low - eta
    return K_B_OVER_E_UV * bracket


def spb_eta_from_seebeck(seebeck_uv_k: float, lambda_scat: float = 0.0) -> float:
    """Invert S(eta) for eta by bisection on a bracketed interval.

    S(eta) decreases monotonically with eta, so the bracket is valid when
    S(low) >= target >= S(high).
    """
    target = abs(seebeck_uv_k)

    def objective(eta: float) -> float:
        return spb_seebeck(eta, lambda_scat) - target

    low, high = -60.0, 80.0
    if objective(low) < 0.0 or objective(high) > 0.0:
        raise ValueError(f"|S| = {target} uV/K is outside the bracketed range")
    return brentq(objective, low, high, xtol=1e-12, rtol=1e-14)


def spb_lorenz_number(eta: float, lambda_scat: float = 0.0) -> float:
    """Rigorous SPB Lorenz number [W*Ohm/K^2] from the transport integrals.

    With Blatt-normalised integrals and r = lambda - 1/2:

        L = (k_B/e)^2 [ (lambda+3)(lambda+2) F_{lambda+2}/F_{lambda}
                          - ( (lambda+2) F_{lambda+1}/F_{lambda} )^2 ]

    Limits (checked in the test suite):
      * non-degenerate: L -> (5/2 + r)(k_B/e)^2 = (lambda + 2)(k_B/e)^2
      * degenerate:      L -> (pi^2/3)(k_B/e)^2
    """
    f0 = fermi_integral_blatt(lambda_scat, eta)
    f1 = fermi_integral_blatt(lambda_scat + 1.0, eta)
    f2 = fermi_integral_blatt(lambda_scat + 2.0, eta)
    ratio_1 = (lambda_scat + 2.0) * f1 / f0
    term1 = (lambda_scat + 3.0) * (lambda_scat + 2.0) * f2 / f0
    return K_B_OVER_E**2 * (term1 - ratio_1**2)


def spb_effective_density_of_states(mass_ratio: float, temperature_k: float) -> float:
    """Effective density of states N_c [m^-3] for m*/m_e = 1 at T [K].

        N_c = 2 (2 pi m_e k_B T / h^2)^{3/2}

    (the textbook convention, paired with Blatt-normalised integrals)
    """
    return 2.0 * (2.0 * math.pi * M_E * K_B * temperature_k / PLANCK_H**2) ** 1.5


def spb_carrier_density(
    eta: float, mass_ratio: float, temperature_k: float
) -> float:
    """Carrier concentration [cm^-3] from the SPB model.

        n = N_c (m*/m_e)^{3/2} F_{1/2}(eta) / 1e6      (N_c in m^-3, F normalised)
    """
    n_c = spb_effective_density_of_states(1.0, temperature_k)
    n_m3 = n_c * mass_ratio**1.5 * fermi_integral_blatt(0.5, eta)
    return n_m3 * 1e-6


def spb_effective_mass(
    seebeck_uv_k: float, carrier_density_cm3: float, temperature_k: float,
    lambda_scat: float = 0.0,
) -> float:
    """Density-of-states effective mass ratio m*/m_e from (S, n, T)."""
    eta = spb_eta_from_seebeck(seebeck_uv_k, lambda_scat)
    n_m3 = carrier_density_cm3 * 1e6
    n_c = spb_effective_density_of_states(1.0, temperature_k)
    f_half = fermi_integral_blatt(0.5, eta)
    return (n_m3 / (n_c * f_half)) ** (2.0 / 3.0)


# =====================================================================
# Transport properties
# =====================================================================

def power_factor(seebeck_v_per_k, sigma_s_per_m):
    """PF = S^2 * sigma  [W/(m*K^2)]."""
    return np.asarray(seebeck_v_per_k) ** 2 * np.asarray(sigma_s_per_m)


def resistivity_from_geometry(length_m, area_m2, resistance_ohm):
    """rho = L / (R * A)  [Ohm*m]."""
    return np.asarray(length_m) / (np.asarray(resistance_ohm) * np.asarray(area_m2))


def conductivity_from_resistivity(resistivity_ohm_m):
    """sigma = 1 / rho  [S/m]."""
    return 1.0 / np.asarray(resistivity_ohm_m)


def kappa_electronic(sigma_s_per_m, temperature_k, lorenz):
    """kappa_e = L * sigma * T  [W/(m*K)]."""
    return lorenz * np.asarray(sigma_s_per_m) * np.asarray(temperature_k)


def kappa_lattice(kappa_total, kappa_electronic_value):
    """kappa_L = kappa_total - kappa_e  [W/(m*K)]."""
    return np.asarray(kappa_total) - np.asarray(kappa_electronic_value)


def figure_of_merit(pf, temperature_k, kappa_total):
    """ZT = PF * T / kappa_total  [dimensionless]."""
    pf = np.asarray(pf)
    temperature_k = np.asarray(temperature_k)
    kappa_total = np.asarray(kappa_total)
    out = np.zeros_like(pf, dtype=float)
    np.divide(pf * temperature_k, kappa_total, out=out, where=kappa_total != 0)
    return out


def kappa_from_laser_flash_si(diffusivity_m2_s, cp_j_kg_k, density_kg_m3):
    """kappa = alpha * Cp * rho  [W/(m*K)]."""
    return (
        np.asarray(diffusivity_m2_s)
        * np.asarray(cp_j_kg_k)
        * np.asarray(density_kg_m3)
    )


def kappa_from_laser_flash_lab(diffusivity_mm2_s, cp_j_g_k, density_g_cm3):
    """Laboratory-unit laser flash: alpha [mm^2/s], Cp [J/(g*K)], rho [g/cm^3]."""
    return (
        np.asarray(diffusivity_mm2_s) * 1e-6
        * np.asarray(cp_j_g_k) * 1e3
        * np.asarray(density_g_cm3) * 1e3
    )


def lorenz_sommerfeld() -> float:
    """L0 = (pi^2/3) (k_B/e)^2  [W*Ohm/K^2]."""
    return (math.pi**2 / 3.0) * K_B_OVER_E**2


def lorenz_kim(seebeck_uv_k) -> float:
    """Empirical Kim et al. (2015) Lorenz estimate [W*Ohm/K^2]."""
    return (1.5 + np.exp(-np.abs(np.asarray(seebeck_uv_k)) / 116.0)) * 1e-8


def weighted_mobility_snyder(temperature_k, resistivity_mohm_cm, seebeck_uv_k):
    """Independent transcription of Snyder et al. (2020), Eq. 1.

    Returns weighted mobility in cm^2/(V*s), with rho in mOhm*cm,
    temperature in K and Seebeck coefficient in uV/K.
    """
    temperature, resistivity, seebeck = np.broadcast_arrays(
        np.asarray(temperature_k, dtype=float),
        np.asarray(resistivity_mohm_cm, dtype=float),
        np.asarray(seebeck_uv_k, dtype=float),
    )
    s = np.abs(seebeck) / K_B_OVER_E_UV
    logistic_1 = np.exp(-np.logaddexp(0.0, -5.0 * (s - 1.0)))
    logistic_2 = np.exp(-np.logaddexp(0.0, 5.0 * (s - 1.0)))
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        shape = np.exp(s - 2.0) * logistic_1 + (3.0 / math.pi**2) * s * logistic_2
        result = 331.0 * (1.0 / resistivity) * (temperature / 300.0) ** (-1.5) * shape
    valid = (
        np.isfinite(temperature) & np.isfinite(resistivity) & np.isfinite(seebeck)
        & (temperature > 0.0) & (resistivity > 0.0)
    )
    return np.where(valid, result, np.nan)


def seebeck_from_regression(delta_t_k, delta_v_v):
    """Ordinary least-squares slope of dV against dT [V/K] and its standard error.

    The slope standard error uses the classical residual estimate
    s^2 = SS_res/(n-2) and s_e = s / sqrt(SS_xx).
    """
    x = np.asarray(delta_t_k, dtype=float)
    y = np.asarray(delta_v_v, dtype=float)
    n = x.size
    if n < 3:
        return np.nan, np.nan
    x_mean, y_mean = x.mean(), y.mean()
    sxx = ((x - x_mean) ** 2).sum()
    sxy = ((x - x_mean) * (y - y_mean)).sum()
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    residuals = y - (slope * x + intercept)
    ss_res = (residuals**2).sum()
    slope_stderr = math.sqrt(ss_res / (n - 2) / sxx) if sxx > 0 else np.nan
    return slope, slope_stderr


def hall_coefficient(hall_voltage_v, thickness_m, current_a, magnetic_field_t):
    """R_H = V_H * t / (I * B)  [m^3/C]."""
    return (
        np.asarray(hall_voltage_v) * thickness_m
        / (current_a * magnetic_field_t)
    )


def hall_carrier_density(hall_coefficient_m3_c, hall_factor=1.0):
    """n_H = r_H / (e |R_H|)  [m^-3]."""
    return hall_factor / (E_CHARGE * np.abs(np.asarray(hall_coefficient_m3_c)))


def hall_mobility(hall_coefficient_m3_c, sigma_s_per_m):
    """mu_H = |R_H| * sigma  [m^2/(V*s)]."""
    return np.abs(np.asarray(hall_coefficient_m3_c)) * np.asarray(sigma_s_per_m)


def scattering_exponent_from_power_law(temperature_k, mobility_cm2_vs):
    """Least-squares fit of ln(mu) = p ln(T) + ln(mu_0) -> (p, mu_0, r^2)."""
    x = np.log(np.asarray(temperature_k, dtype=float))
    y = np.log(np.asarray(mobility_cm2_vs, dtype=float))
    slope, intercept = np.polyfit(x, y, 1)
    fitted = slope * x + intercept
    ss_res = float(((y - fitted) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return float(slope), float(math.exp(intercept)), r2


def dulong_petit_molar(n_atoms: int) -> float:
    """C_V = 3 n R  [J/(mol*K)]."""
    return 3.0 * n_atoms * N_A * K_B


def dulong_petit_specific(n_atoms: int, molar_mass_g_mol: float) -> float:
    """C_V = 3 n R / M  [J/(kg*K)] with M in kg/mol."""
    return dulong_petit_molar(n_atoms) / (molar_mass_g_mol * 1e-3)


def device_efficiencies(
    temps_k, seebecks_v_k, sigmas_s_m, kappas_w_mk, tc_k, th_k
):
    """Independent device-efficiency reference (Simpson integration).

    Returns the average-ZT, the engineering figure of merit, the Carnot limit
    and both efficiencies.
    """
    order = np.argsort(np.asarray(temps_k, dtype=float))
    t = np.asarray(temps_k, dtype=float)[order]
    s = np.asarray(seebecks_v_k, dtype=float)[order]
    sigma = np.asarray(sigmas_s_m, dtype=float)[order]
    kappa = np.asarray(kappas_w_mk, dtype=float)[order]

    mask = (t >= tc_k) & (t <= th_k)
    if mask.sum() >= 2:
        t_range, s_range = t[mask], s[mask]
        sigma_range, kappa_range = sigma[mask], kappa[mask]
    else:
        t_range = np.linspace(tc_k, th_k, 101)
        s_range = np.interp(t_range, t, s)
        sigma_range = np.interp(t_range, t, sigma)
        kappa_range = np.interp(t_range, t, kappa)

    delta_t = th_k - tc_k
    zt_range = (s_range**2) * sigma_range * t_range / kappa_range
    # Simpson quadrature is used on both sides so that the comparison isolates
    # the *formulas* (the quadrature rule itself is validated separately).
    from scipy.integrate import simpson

    zt_avg = float(simpson(y=zt_range, x=t_range) / delta_t)
    carnot = delta_t / th_k

    s_avg = float(simpson(y=s_range, x=t_range) / delta_t)
    rho_avg = float(simpson(y=1.0 / sigma_range, x=t_range) / delta_t)
    kappa_avg = float(simpson(y=kappa_range, x=t_range) / delta_t)
    t_avg = 0.5 * (tc_k + th_k)
    zt_eng = s_avg**2 * t_avg / (rho_avg * kappa_avg)

    def ioffe(zt_value):
        factor = math.sqrt(1.0 + zt_value)
        return carnot * (factor - 1.0) / (factor + tc_k / th_k)

    return {
        "ZT_avg": zt_avg,
        "ZT_eng": zt_eng,
        "Carnot": carnot,
        "Efficiency_Max": ioffe(zt_avg),
        "Efficiency_Eng": ioffe(zt_eng),
    }


# =====================================================================
# Uncertainty propagation (first-order, independent inputs)
# =====================================================================

def u_pf(seebeck, u_seebeck, sigma, u_sigma):
    """u(PF) = sqrt((2 S sigma u_S)^2 + (S^2 u_sigma)^2)."""
    return np.sqrt(
        ((2.0 * seebeck * sigma * u_seebeck) ** 2)
        + ((seebeck**2 * u_sigma) ** 2)
    )


def u_kappa_electronic(sigma, u_sigma, temperature, u_temperature, lorenz, u_lorenz):
    """u(kappa_e) = sqrt((L T u_sigma)^2 + (L sigma u_T)^2 + (sigma T u_L)^2)."""
    return np.sqrt(
        ((lorenz * temperature * u_sigma) ** 2)
        + ((lorenz * sigma * u_temperature) ** 2)
        + ((sigma * temperature * u_lorenz) ** 2)
    )


def u_kappa_lattice(u_kappa_total, u_kappa_electronic_value):
    """u(kappa_L) = sqrt(u_kappa_total^2 + u_kappa_e^2)."""
    return np.sqrt(u_kappa_total**2 + u_kappa_electronic_value**2)


def u_zt(pf, u_pf_value, temperature, u_temperature, kappa_total, u_kappa_total):
    """u(ZT) = |ZT| sqrt((u_PF/PF)^2 + (u_T/T)^2 + (u_kappa/kappa)^2)."""
    zt = figure_of_merit(pf, temperature, kappa_total)
    with np.errstate(divide="ignore", invalid="ignore"):
        relative = np.sqrt(
            (u_pf_value / pf) ** 2
            + (u_temperature / temperature) ** 2
            + (u_kappa_total / kappa_total) ** 2
        )
    return np.abs(zt) * relative


def u_conductivity_from_geometry(area, u_area, length, u_length, resistance, u_resistance):
    """u(sigma)/sigma = sqrt((u_L/L)^2 + (u_R/R)^2 + (u_A/A)^2)."""
    sigma = length / (resistance * area)
    relative = np.sqrt(
        (u_length / length) ** 2
        + (u_resistance / resistance) ** 2
        + (u_area / area) ** 2
    )
    return np.abs(sigma) * relative


def u_kappa_from_laser_flash(diffusivity, u_diffusivity, cp, u_cp, density, u_density):
    """u(kappa)/kappa = sqrt((u_alpha/alpha)^2 + (u_Cp/Cp)^2 + (u_rho/rho)^2)."""
    kappa = diffusivity * cp * density
    relative = np.sqrt(
        (u_diffusivity / diffusivity) ** 2
        + (u_cp / cp) ** 2
        + (u_density / density) ** 2
    )
    return np.abs(kappa) * relative


def u_density(weight, u_weight, area, u_area, thickness, u_thickness):
    """u(rho)/rho = sqrt((u_m/m)^2 + (u_A/A)^2 + (u_t/t)^2)."""
    density = weight / (area * thickness)
    relative = np.sqrt(
        (u_weight / weight) ** 2
        + (u_area / area) ** 2
        + (u_thickness / thickness) ** 2
    )
    return np.abs(density) * relative


def monte_carlo_uncertainty(evaluator, inputs, uncertainties, n_samples=200_000, seed=20261112):
    """Independent Monte-Carlo uncertainty reference.

    ``evaluator`` maps a tuple of sampled inputs to the quantity of interest;
    ``inputs`` and ``uncertainties`` are matching sequences. The result is the
    standard deviation of the sampled distribution.
    """
    rng = np.random.default_rng(seed)
    samples = [
        rng.normal(np.asarray(value, dtype=float), np.asarray(sigma, dtype=float),
                   size=(n_samples,) + np.shape(value))
        for value, sigma in zip(inputs, uncertainties)
    ]
    values = np.array([evaluator(*sample) for sample in zip(*samples)], dtype=float)
    return float(np.nanstd(values)), values
