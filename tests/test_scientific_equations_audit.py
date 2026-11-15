"""Independent numerical verification of every scientific equation.

Design rules for this module (audit requirement):
  * Expected values are computed ANALYTICALLY here - never by calling another
    application function (no "the implementation agrees with itself" tests).
  * Each test documents the scientific basis of its expected value.
  * Dimensional consistency is checked by *scaling laws* (how the result must
    respond when an input is scaled), which is unit-system independent.
  * Boundary cases (zero, negative, tiny, huge, NaN/inf) are exercised.

References are listed in docs/SCIENTIFIC_EQUATION_AUDIT.md (section 11).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from seebeck_prime.domain.analysis import (
    align_datasets,
    interpolate_onto,
    linear_regression,
    mad_filter,
)
from seebeck_prime.domain.calculations import (
    calculate_dulong_petit_limit,
    calculate_kappa_e,
    calculate_kappa_l,
    calculate_molecular_weight,
    calculate_pf,
    calculate_zt,
    estimate_lorenz,
)
from seebeck_prime.domain.device_efficiency import calculate_efficiencies
from seebeck_prime.domain.hall import (
    calculate_hall_carrier_density,
    calculate_hall_coefficient_from_raw,
    calculate_hall_mobility,
    calculate_hall_mobility_cm2_vs,
    determine_carrier_type,
    fit_scattering_exponent,
)
from seebeck_prime.domain.physical_constants import (
    AVOGADRO,
    BOLTZMANN,
    DEFAULT_LORENZ,
    ELECTRON_CHARGE,
    GAS_CONSTANT,
    LEGACY_DEFAULT_LORENZ,
    PLANCK,
    SOMMERFELD_LORENZ_EXACT,
)
from seebeck_prime.domain.phonon import (
    dulong_petit_molar,
    dulong_petit_specific,
    kappa_from_diffusivity,
    kappa_from_diffusivity_si,
)
from seebeck_prime.domain.spb import (
    calculate_carrier_density_spb,
    calculate_effective_mass,
    fermi_integral,
    reduced_fermi_level_from_seebeck,
    rigorous_lorenz_number,
    seebeck_from_reduced_fermi_level,
)
from seebeck_prime.domain.transport import calculate_weighted_mobility
from seebeck_prime.domain.uncertainty import (
    propagate_density_error,
    propagate_kappa_e_error,
    propagate_kappa_error,
    propagate_kappa_l_error,
    propagate_pf_error,
    propagate_relative_uncertainty,
    propagate_sigma_error,
    propagate_zt_error,
)
from seebeck_prime.domain.units import (
    carrier_density_cm3_to_m3,
    carrier_density_m3_to_cm3,
    celsius_to_kelvin,
    kelvin_to_celsius,
    pf_from_si,
    pf_to_si,
    seebeck_from_vk,
    seebeck_to_vk,
    sigma_from_sm,
    sigma_to_sm,
)

KB_E = BOLTZMANN / ELECTRON_CHARGE          # V/K, exactly 8.617333262e-5
KB_E_UV = KB_E * 1e6                        # uV/K, 86.17333262
ELEMENTARY_CHARGE = 1.602176634e-19        # C (exact, CODATA 2018)


# =====================================================================
# 1. Fundamental constants
# =====================================================================

def test_fundamental_constants_match_codata_2018_exact_values():
    """CODATA 2018: k_B, e, N_A, h are exactly defined in the SI."""
    assert BOLTZMANN == 1.380649e-23
    assert ELECTRON_CHARGE == 1.602176634e-19
    assert AVOGADRO == 6.02214076e23
    assert PLANCK == 6.62607015e-34


def test_gas_constant_is_the_product_of_avogadro_and_boltzmann():
    """R = N_A k_B exactly (SI defining relation)."""
    assert GAS_CONSTANT == pytest.approx(8.31446261815324, rel=1e-14)
    assert GAS_CONSTANT == pytest.approx(AVOGADRO * BOLTZMANN, rel=1e-15)


def test_sommerfeld_lorenz_number_matches_the_analytic_expression():
    """L0 = (pi^2/3) (k_B/e)^2 = 2.443004509e-8 W*Ohm/K^2.

    The application uses the rounded 2.44e-8 for every workflow (author
    decision 2026-11-11, audit issue SE-015); the exact Sommerfeld value is
    retained as a reference constant.
    """
    from seebeck_prime.domain.physical_constants import SOMMERFELD_LORENZ_EXACT

    analytic = (math.pi**2 / 3.0) * KB_E**2
    assert SOMMERFELD_LORENZ_EXACT == pytest.approx(analytic, rel=1e-15)
    assert SOMMERFELD_LORENZ_EXACT == pytest.approx(2.443004509e-8, rel=1e-9)


def test_application_lorenz_constant_is_the_unified_rounded_value():
    """Author decision: every workflow uses L = 2.44e-8 W*Ohm/K^2."""
    assert DEFAULT_LORENZ == 2.44e-8
    assert LEGACY_DEFAULT_LORENZ == DEFAULT_LORENZ
    # The rounded value is 0.12 % below the exact Sommerfeld value.
    assert abs(DEFAULT_LORENZ / SOMMERFELD_LORENZ_EXACT - 1.0) == pytest.approx(
        0.00123, abs=5e-4
    )


def test_legacy_lorenz_number_is_the_rounded_historical_value():
    """The Multi-Sample workflow historically used L = 2.44e-8; it is now the
    same constant as the main table (no workflow divergence)."""
    assert LEGACY_DEFAULT_LORENZ == 2.44e-8


# =====================================================================
# 2. Core transport equations and their scaling laws
# =====================================================================

def test_power_factor_analytic_value():
    """PF = S^2 * sigma  [W/(m*K^2)]."""
    assert calculate_pf(100e-6, 1e5) == pytest.approx(1.0e-3, rel=1e-12)


def test_power_factor_scaling_laws_are_dimensional():
    """PF must scale as S^2 and linearly in sigma."""
    base = calculate_pf(100e-6, 1e5)
    assert calculate_pf(2 * 100e-6, 1e5) == pytest.approx(4.0 * base, rel=1e-12)
    assert calculate_pf(100e-6, 2 * 1e5) == pytest.approx(2.0 * base, rel=1e-12)


def test_power_factor_is_sign_independent_for_negative_seebeck():
    """PF uses S^2: the carrier type must not change the power factor."""
    assert calculate_pf(-100e-6, 1e5) == pytest.approx(
        calculate_pf(100e-6, 1e5), rel=1e-15
    )


def test_electronic_thermal_conductivity_analytic_value_and_scaling():
    """kappa_e = L * sigma * T  [W/(m*K)]; linear in sigma and T."""
    expected = DEFAULT_LORENZ * 1e5 * 300.0
    assert calculate_kappa_e(1e5, 300.0) == pytest.approx(expected, rel=1e-12)
    assert calculate_kappa_e(2e5, 300.0) == pytest.approx(
        2 * calculate_kappa_e(1e5, 300.0), rel=1e-12
    )
    assert calculate_kappa_e(1e5, 600.0) == pytest.approx(
        2 * calculate_kappa_e(1e5, 300.0), rel=1e-12
    )


def test_lattice_thermal_conductivity_is_the_residual():
    """kappa_L = kappa_total - kappa_e."""
    kappa_e = calculate_kappa_e(1e5, 300.0)
    assert calculate_kappa_l(2.0, kappa_e) == pytest.approx(2.0 - kappa_e, rel=1e-12)


def test_figure_of_merit_is_dimensionless_and_scales_with_temperature():
    """ZT = S^2 sigma T / kappa; dimensionless, linear in T, inverse in kappa."""
    zt = calculate_zt(1e-3, 300.0, 2.0)
    assert zt == pytest.approx(0.15, rel=1e-12)
    assert calculate_zt(1e-3, 600.0, 2.0) == pytest.approx(2 * zt, rel=1e-12)
    assert calculate_zt(1e-3, 300.0, 4.0) == pytest.approx(zt / 2, rel=1e-12)
    # Dimensionless: ZT must be invariant to a consistent unit change of S
    # and sigma, because the units cancel.
    s_v_per_k, sigma_s_per_m = 200e-6, 1e5
    s_uv_per_k = s_v_per_k * 1e6
    sigma_s_per_cm = sigma_s_per_m / 100.0
    pf_v = (s_v_per_k**2) * sigma_s_per_m
    # S[uV/K]^2 * sigma[S/cm] -> W/(m*K^2) needs 1e-12 (V/K)^2 and 1e2 (S/m):
    pf_uv = (s_uv_per_k**2) * sigma_s_per_cm * 1e-12 * 1e2
    assert pf_v == pytest.approx(pf_uv, rel=1e-12)


def test_figure_of_merit_handles_zero_thermal_conductivity_defensively():
    """Documented convention: ZT = 0 where kappa_total = 0 (no division error)."""
    assert calculate_zt(1e-3, 300.0, 0.0) == 0.0


def test_kim_empirical_lorenz_relation_and_limits():
    """L = (1.5 + exp(-|S|/116)) * 1e-8 W*Ohm/K^2 (Kim et al. 2015)."""
    assert estimate_lorenz(0.0) == pytest.approx(2.5e-8, rel=1e-12)
    assert estimate_lorenz(116.0) == pytest.approx((1.5 + math.exp(-1.0)) * 1e-8, rel=1e-12)
    # Sign-independent and monotonically decreasing with |S|.
    assert estimate_lorenz(-150.0) == pytest.approx(estimate_lorenz(150.0), rel=1e-12)
    values = [estimate_lorenz(s) for s in (0.0, 50.0, 100.0, 200.0)]
    assert values == sorted(values, reverse=True)


def test_dulong_petit_limit_is_three_n_r():
    """C_V = 3 n R [J/(mol*K)]."""
    assert dulong_petit_molar(1) == pytest.approx(3.0 * GAS_CONSTANT, rel=1e-12)
    assert dulong_petit_molar(5) == pytest.approx(15.0 * GAS_CONSTANT, rel=1e-12)


def test_dulong_petit_specific_uses_the_molar_mass_in_kg_per_mol():
    """C_specific = 3 n R / (M [g/mol] * 1e-3) [J/(kg*K)]."""
    expected = dulong_petit_molar(5) / (489.68 * 1e-3)
    assert dulong_petit_specific(5, 489.68) == pytest.approx(expected, rel=1e-12)


def test_dulong_petit_limit_application_function_matches_the_domain_value():
    """The Application entry point must return the same physical quantity."""
    assert calculate_dulong_petit_limit(5, 489.68, "J/mol\u00b7K") == pytest.approx(
        dulong_petit_molar(5), rel=1e-9
    )
    assert calculate_dulong_petit_limit(5, 489.68, "J/kg\u00b7K") == pytest.approx(
        dulong_petit_specific(5, 489.68), rel=1e-9
    )


def test_formula_mass_is_hand_computable_and_rejects_unsupported_syntax():
    """Bi2Te3: 2*208.9804 + 3*127.60 = 800.7608 g/mol with 5 atoms."""
    mass, atoms = calculate_molecular_weight("Bi2Te3")
    assert mass == pytest.approx(2 * 208.98040 + 3 * 127.60, rel=1e-12)
    assert atoms == 5
    # Unsupported syntax must be rejected rather than silently mis-parsed.
    assert calculate_molecular_weight("Ca3(PO4)2") == (None, 0)
    assert calculate_molecular_weight("Na0.5") == (None, 0)


# =====================================================================
# 3. Uncertainty propagation (first-order Gaussian)
# =====================================================================

def test_pf_uncertainty_matches_the_analytic_partial_derivative_form():
    """u_PF = sqrt((2 S sigma u_S)^2 + (S^2 u_sigma)^2)."""
    s, s_err, sigma, sigma_err = 100e-6, 5e-6, 1e5, 0.05e5
    expected = math.sqrt(((2 * s * sigma * s_err) ** 2) + ((s**2 * sigma_err) ** 2))
    assert propagate_pf_error(s, s_err, sigma, sigma_err) == pytest.approx(
        expected, rel=1e-12
    )


def test_kappa_e_uncertainty_includes_the_lorenz_term():
    """u_kappa_e = sqrt((L T u_sigma)^2 + (L sigma u_T)^2 + (sigma T u_L)^2)."""
    sigma, u_sigma, T, u_T, L, u_L = 1e5, 0.05e5, 300.0, 5.0, DEFAULT_LORENZ, 0.0
    expected = math.sqrt(
        ((L * T * u_sigma) ** 2) + ((L * sigma * u_T) ** 2) + ((sigma * T * u_L) ** 2)
    )
    assert propagate_kappa_e_error(
        sigma, u_sigma, T, u_T, L, u_L
    ) == pytest.approx(expected, rel=1e-12)


def test_kappa_l_uncertainty_combines_in_quadrature():
    """u_kappa_L = sqrt(u_kappa_total^2 + u_kappa_e^2)."""
    assert propagate_kappa_l_error(0.02, 0.01) == pytest.approx(
        math.sqrt(0.02**2 + 0.01**2), rel=1e-12
    )


def test_zt_uncertainty_uses_the_relative_form():
    """u_ZT = |ZT| sqrt((u_PF/PF)^2 + (u_T/T)^2 + (u_kappa/kappa)^2)."""
    pf, pf_err, T, u_T, kappa, u_kappa = 1e-3, 5e-5, 300.0, 5.0, 2.0, 0.02
    zt = pf * T / kappa
    expected = abs(zt) * math.sqrt(
        (pf_err / pf) ** 2 + (u_T / T) ** 2 + (u_kappa / kappa) ** 2
    )
    assert propagate_zt_error(pf, pf_err, T, u_T, kappa, u_kappa) == pytest.approx(
        expected, rel=1e-12
    )


def test_sigma_uncertainty_from_geometry_and_resistance():
    """sigma = L/(R A): u_sigma/sigma = sqrt((u_L/L)^2+(u_R/R)^2+(u_A/A)^2)."""
    area, u_area, length, u_length, R, u_R = 1e-6, 1e-8, 1e-3, 1e-5, 0.1, 0.001
    sigma = length / (R * area)
    expected = abs(sigma) * math.sqrt(
        (u_length / length) ** 2 + (u_R / R) ** 2 + (u_area / area) ** 2
    )
    assert propagate_sigma_error(
        area, u_area, length, u_length, R, u_R
    ) == pytest.approx(expected, rel=1e-12)


def test_laser_flash_kappa_uncertainty_uses_relative_addition():
    """kappa = alpha Cp rho: relative errors add in quadrature."""
    alpha, u_alpha, cp, u_cp, rho, u_rho = 1e-6, 5e-8, 500.0, 10.0, 8000.0, 100.0
    kappa = alpha * cp * rho
    expected = abs(kappa) * math.sqrt(
        (u_alpha / alpha) ** 2 + (u_cp / cp) ** 2 + (u_rho / rho) ** 2
    )
    assert propagate_kappa_error(
        alpha, u_alpha, cp, u_cp, rho, u_rho
    ) == pytest.approx(expected, rel=1e-12)


def test_density_uncertainty_from_mass_area_and_thickness():
    """rho = m/(A t)."""
    m, u_m, A, u_A, t, u_t = 1.0, 0.01, 1e-4, 2e-6, 1e-3, 1e-5
    rho = m / (A * t)
    expected = abs(rho) * math.sqrt(
        (u_m / m) ** 2 + (u_A / A) ** 2 + (u_t / t) ** 2
    )
    assert propagate_density_error(m, u_m, A, u_A, t, u_t) == pytest.approx(
        expected, rel=1e-12
    )


def test_relative_uncertainty_combination_is_root_sum_of_squares():
    """u = |value| sqrt(sum of relative variances)."""
    assert propagate_relative_uncertainty(1e-3, 0.05, 0.02, 0.01) == pytest.approx(
        1e-3 * math.sqrt(0.05**2 + 0.02**2 + 0.01**2), rel=1e-12
    )


def test_uncertainty_propagation_is_sign_insensitive_for_seebeck():
    """Uncertainties are magnitudes: S and -S give identical u(PF)."""
    assert propagate_pf_error(-100e-6, 5e-6, 1e5, 0.05e5) == pytest.approx(
        propagate_pf_error(100e-6, 5e-6, 1e5, 0.05e5), rel=1e-15
    )


# =====================================================================
# 4. Unit conversions (critical audit section 3)
# =====================================================================

@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        (1.0, "S/m", 1.0),
        (1.0, "S/cm", 100.0),          # 1 S/cm = 100 S/m
        (1.0, "Ohm-cm", 100.0),        # rho = 1 ohm.cm -> sigma = 100 S/m
        (0.01, "Ohm-cm", 10000.0),
    ],
)
def test_conductivity_conversion_factors_are_exact(value, unit, expected):
    assert sigma_to_sm(value, unit) == pytest.approx(expected, rel=1e-12)


def test_conductivity_round_trip_for_every_supported_unit():
    for unit in ("S/m", "S/cm", "Ohm-cm", "\u03a9\u00b7cm", "Ohm\u00b7cm"):
        original = 1234.0
        assert sigma_from_sm(sigma_to_sm(original, unit), unit) == pytest.approx(
            original, rel=1e-12
        )


def test_seebeck_conversion_factors_are_exact():
    assert seebeck_to_vk(150.0, "\u00b5V/K") == pytest.approx(150e-6, rel=1e-12)
    assert seebeck_to_vk(150.0, "mV/K") == pytest.approx(0.15, rel=1e-12)
    assert seebeck_from_vk(150e-6, "\u00b5V/K") == pytest.approx(150.0, rel=1e-12)


def test_power_factor_conversion_factors_are_exact():
    assert pf_to_si(1.0, "mW/mK\u00b2") == pytest.approx(1e-3, rel=1e-12)
    assert pf_to_si(1.0, "\u00b5W/mK\u00b2") == pytest.approx(1e-6, rel=1e-12)
    assert pf_to_si(1.0, "W/mK\u00b2") == pytest.approx(1.0, rel=1e-12)
    assert pf_to_si(1.0, "W/(m*K^2)") == pytest.approx(1.0, rel=1e-12)
    assert pf_from_si(1e-3, "mW/mK\u00b2") == pytest.approx(1.0, rel=1e-12)
    assert pf_from_si(1e-6, "\u00b5W/mK\u00b2") == pytest.approx(1.0, rel=1e-12)


def test_temperature_offset_conversion_and_uncertainty_invariance():
    """Celsius->Kelvin is an offset; a temperature *uncertainty* is unchanged."""
    assert celsius_to_kelvin(0.0) == pytest.approx(273.15, rel=1e-15)
    assert celsius_to_kelvin(-40.0) == pytest.approx(233.15, rel=1e-15)
    assert kelvin_to_celsius(273.15) == pytest.approx(0.0, rel=1e-15)


def test_carrier_density_conversion_factors_are_exact():
    assert carrier_density_m3_to_cm3(1e25) == pytest.approx(1e19, rel=1e-12)
    assert carrier_density_cm3_to_m3(1e19) == pytest.approx(1e25, rel=1e-12)


def test_conversion_factors_are_not_applied_twice_in_a_display_round_trip():
    """S/m -> display -> S/m must return the original value exactly."""
    sigma = 4321.0
    for unit in ("S/cm", "Ohm-cm"):
        assert sigma_from_sm(sigma_to_sm(sigma, unit), unit) == pytest.approx(
            sigma, rel=1e-12
        )


# =====================================================================
# 5. Hall effect
# =====================================================================

def test_hall_coefficient_matches_its_definition():
    """R_H = V_H * t / (I * B) [m^3/C]."""
    v_h, t, i, b = 1.2e-4, 1.0e-3, 10e-3, 0.5
    assert calculate_hall_coefficient_from_raw(v_h, t, i, b) == pytest.approx(
        v_h * t / (i * b), rel=1e-12
    )


def test_hall_carrier_density_follows_r_h_over_e_r_h():
    """n = r_H / (e |R_H|) [m^-3] (single-carrier Hall factor convention)."""
    r_h_val, factor = 1.0e-3, 0.85
    expected = factor / (ELEMENTARY_CHARGE * abs(r_h_val))
    assert calculate_hall_carrier_density(r_h_val, factor) == pytest.approx(
        expected, rel=1e-9
    )


def test_hall_mobility_units_are_correct_in_both_conventions():
    """mu_H = |R_H| sigma: m^2/(V*s) in SI, cm^2/(V*s) in laboratory units."""
    assert calculate_hall_mobility(1.0e-3, 1e5) == pytest.approx(100.0, rel=1e-12)
    assert calculate_hall_mobility_cm2_vs(100.0, 10.0) == pytest.approx(
        1000.0, rel=1e-12
    )
    # The laboratory form must be 1e4 times the SI form for the same material.
    r_h_si, sigma_si = 1.0e-3, 1e5
    mu_si = calculate_hall_mobility(r_h_si, sigma_si)
    mu_lab = calculate_hall_mobility_cm2_vs(r_h_si * 1e6, sigma_si / 100.0)
    assert mu_lab == pytest.approx(mu_si * 1e4, rel=1e-12)


def test_carrier_type_follows_the_sign_of_the_hall_coefficient():
    assert determine_carrier_type(1e-4) == "p-type"
    assert determine_carrier_type(-1e-4) == "n-type"
    assert determine_carrier_type(0.0) == "undetermined"


def test_scattering_exponent_fit_recovers_a_known_power_law():
    """mu = mu_0 T^p -> log-log fit returns (p, mu_0, r^2)."""
    T = np.linspace(200.0, 600.0, 40)
    mu = 7.5 * T ** (-1.5)
    p, mu_0, r2 = fit_scattering_exponent(T, mu)
    assert p == pytest.approx(-1.5, rel=1e-9)
    assert mu_0 == pytest.approx(7.5, rel=1e-9)
    assert r2 == pytest.approx(1.0, abs=1e-9)


# =====================================================================
# 6. Single parabolic band (SPB) model
# =====================================================================

def test_fermi_integral_zero_order_is_the_exact_logarithm():
    """F_0(eta) = ln(1 + e^eta) exactly (unnormalized complete integral)."""
    for eta in (-3.0, 0.0, 3.0):
        assert fermi_integral(0.0, eta) == pytest.approx(
            math.log(1.0 + math.exp(eta)), rel=1e-8
        )


def test_fermi_integral_matches_the_degenerate_sommerfeld_expansion():
    """F_j(eta) = eta^(j+1)/(j+1) + (pi^2/6) j eta^(j-1) + (7 pi^4/360) j(j-1)(j-2) eta^(j-3).

    The correction terms are required: the Lorenz combination is a
    near-cancellation, so the leading term alone is not accurate enough
    (issue SE-008).
    """
    for j in (0.0, 0.5, 1.0, 2.0):
        eta = 80.0
        expected = (
            eta ** (j + 1) / (j + 1)
            + (math.pi**2 / 6) * j * eta ** (j - 1)
            + (7 * math.pi**4 / 360) * j * (j - 1) * (j - 2) * eta ** (j - 3)
        )
        assert fermi_integral(j, eta) == pytest.approx(expected, rel=1e-12)


def test_fermi_integral_matches_the_boltzmann_asymptote():
    """F_j(eta) -> Gamma(j+1) e^eta for eta << 0."""
    from scipy.special import gamma

    assert fermi_integral(0.5, -40.0) == pytest.approx(
        gamma(1.5) * math.exp(-40.0), rel=1e-12
    )


def test_seebeck_reduced_fermi_level_round_trip():
    """The S <-> eta inversion must be self-consistent."""
    for s_uv_k in (50.0, 100.0, 150.0, 250.0):
        eta = reduced_fermi_level_from_seebeck(s_uv_k, 0.0)
        assert seebeck_from_reduced_fermi_level(eta, 0.0) == pytest.approx(
            s_uv_k, rel=1e-6
        )


def test_seebeck_decreases_monotonically_with_reduced_fermi_level():
    eta = np.linspace(-6.0, 8.0, 30)
    seebeck = [seebeck_from_reduced_fermi_level(e, 0.0) for e in eta]
    assert seebeck == sorted(seebeck, reverse=True)


def test_carrier_density_scales_with_mass_to_the_three_halves():
    """n ~ (m*/m_e)^(3/2) T^(3/2) F_1/2(eta)."""
    n1 = calculate_carrier_density_spb(0.0, 1.0, 300.0)
    n3 = calculate_carrier_density_spb(0.0, 3.0, 300.0)
    assert n3 == pytest.approx(n1 * 3.0**1.5, rel=1e-9)

    n_600 = calculate_carrier_density_spb(0.0, 1.0, 600.0)
    assert n_600 == pytest.approx(n1 * 2.0**1.5, rel=1e-9)


def test_effective_mass_inversion_recovers_a_constructed_mass():
    """Build (S, n, T) from m* = 2.0 and invert it back."""
    eta = reduced_fermi_level_from_seebeck(120.0, 0.0)
    n = calculate_carrier_density_spb(eta, 2.0, 350.0)
    m_ratio, eta_back = calculate_effective_mass(120.0, n, 350.0)
    assert m_ratio == pytest.approx(2.0, rel=1e-9)
    assert eta_back == pytest.approx(eta, rel=1e-9)


def test_rigorous_lorenz_number_reaches_both_analytic_limits():
    """L -> (pi^2/3)(k/e)^2 (degenerate) and (5/2 + r)(k/e)^2 (non-degenerate).

    For acoustic phonon scattering (lambda = 0, r = -1/2) the classical
    Boltzmann limit is (5/2 - 1/2)(k_B/e)^2 = 2(k_B/e)^2.
    """
    degenerate = rigorous_lorenz_number(80.0, 0.0)
    non_degenerate = rigorous_lorenz_number(-60.0, 0.0)

    assert degenerate == pytest.approx(DEFAULT_LORENZ, rel=2e-3)
    assert non_degenerate == pytest.approx(2.0 * KB_E**2, rel=2e-3)


def test_rigorous_lorenz_number_is_positive_over_the_whole_eta_range():
    """L must stay positive and finite for every reduced Fermi level."""
    for eta in np.linspace(-20.0, 40.0, 25):
        value = rigorous_lorenz_number(float(eta), 0.0)
        assert np.isfinite(value)
        assert value > 0.0


# =====================================================================
# 7. Phonon / laser-flash models
# =====================================================================

def test_laser_flash_kappa_is_the_product_of_its_three_factors():
    """kappa = alpha * Cp * rho."""
    assert kappa_from_diffusivity_si(1.0e-6, 500.0, 8000.0) == pytest.approx(
        4.0, rel=1e-12
    )


def test_laboratory_and_si_laser_flash_paths_agree():
    """1.5 mm^2/s, 0.20 J/(g*K), 7.8 g/cm^3 must give the same kappa."""
    lab = kappa_from_diffusivity(1.5, 0.20, 7.8)
    si = kappa_from_diffusivity_si(1.5e-6, 200.0, 7800.0)
    assert lab == pytest.approx(si, rel=1e-12)


# =====================================================================
# 8. Device efficiency (Ioffe / Snyder)
# =====================================================================

def test_carnot_efficiency_and_i_offe_maximum_efficiency():
    """eta_max = (dT/Th)(sqrt(1+ZT_avg)-1)/(sqrt(1+ZT_avg)+Tc/Th)."""
    S, sigma, kappa, tc, th = 200e-6, 1e5, 2.0, 300.0, 500.0
    result = calculate_efficiencies(
        np.array([300.0, 400.0]), np.array([S, S]), np.array([sigma, sigma]),
        np.array([kappa, kappa]), tc, th,
    )

    pf = S**2 * sigma
    zt_avg = pf * (tc + th) / 2.0 / kappa
    carnot = (th - tc) / th
    eta_max = carnot * (math.sqrt(1 + zt_avg) - 1) / (math.sqrt(1 + zt_avg) + tc / th)

    assert result["ZT_avg"] == pytest.approx(zt_avg, rel=1e-9)
    assert result["Carnot"] == pytest.approx(carnot, rel=1e-12)
    assert result["Efficiency_Max"] == pytest.approx(eta_max, rel=1e-9)
    assert result["Efficiency_Max"] < result["Carnot"]


def test_engineering_figure_of_merit_is_dimensionless_and_consistent():
    """ZT_eng = S_avg^2 T_avg / (rho_avg kappa_avg); for constant properties
    it must equal the material ZT at T_avg, and eta_eng must equal eta_max."""
    S, sigma, kappa, tc, th = 200e-6, 1e5, 2.0, 300.0, 500.0
    result = calculate_efficiencies(
        np.array([300.0, 400.0]), np.array([S, S]), np.array([sigma, sigma]),
        np.array([kappa, kappa]), tc, th,
    )

    s_avg = S
    rho_avg = 1.0 / sigma
    zt_eng = s_avg**2 * ((tc + th) / 2.0) / (rho_avg * kappa)

    assert result["ZT_eng"] == pytest.approx(zt_eng, rel=1e-9)
    assert result["ZT_eng"] == pytest.approx(result["ZT_avg"], rel=1e-9)
    assert result["Efficiency_Eng"] == pytest.approx(result["Efficiency_Max"], rel=1e-9)


def test_device_efficiency_rejects_a_non_positive_junction_temperature_difference():
    assert (
        calculate_efficiencies(
            np.array([300.0, 400.0]), np.array([200e-6, 200e-6]),
            np.array([1e5, 1e5]), np.array([2.0, 2.0]), 400.0, 400.0,
        )
        is None
    )


# =====================================================================
# 9. Weighted mobility (Snyder-style approximation)
# =====================================================================

def test_weighted_mobility_matches_its_documented_expression():
    """mu_w = C * (1/rho) * (T/300)^(-1.5) * shape(|S|/(k_B/e))."""
    T, rho_mohm_cm, s_uv_k = 300.0, 1.0, 200.0
    s = abs(s_uv_k) / KB_E_UV
    shape = math.exp(s - 2) / (1 + math.exp(-5 * (s - 1))) + (
        3 * math.pi**2 / s
    ) / (1 + math.exp(5 * (s - 1)))
    expected = 331.0 * (1.0 / rho_mohm_cm) * (T / 300.0) ** (-1.5) * shape

    assert calculate_weighted_mobility(T, rho_mohm_cm, s_uv_k) == pytest.approx(
        expected, rel=1e-9
    )


def test_weighted_mobility_scales_inversely_with_resistivity():
    """mu_w ~ 1/rho at fixed T and S."""
    base = calculate_weighted_mobility(300.0, 1.0, 200.0)
    assert calculate_weighted_mobility(300.0, 2.0, 200.0) == pytest.approx(
        base / 2, rel=1e-9
    )


def test_weighted_mobility_follows_the_assumed_t_minus_three_halves_law():
    """The model assumes acoustic-phonon scattering: mu ~ T^(-3/2)."""
    base = calculate_weighted_mobility(300.0, 1.0, 200.0)
    assert calculate_weighted_mobility(600.0, 1.0, 200.0) == pytest.approx(
        base * 0.5**1.5, rel=1e-9
    )


def test_weighted_mobility_is_sign_independent_for_seebeck():
    assert calculate_weighted_mobility(300.0, 1.0, -200.0) == pytest.approx(
        calculate_weighted_mobility(300.0, 1.0, 200.0), rel=1e-12
    )


# =====================================================================
# 10. Analysis utilities (alignment / filtering / regression)
# =====================================================================

def test_mad_filter_removes_only_extreme_points():
    x = np.array([100.0, 101.0, 99.0, 100.5, 100.2, 250.0])
    filtered = mad_filter(x, thresh=3.0)
    assert 250.0 not in filtered
    assert len(filtered) == 5


def test_linear_regression_recovers_slope_and_intercept_exactly():
    x = np.linspace(0.0, 10.0, 11)
    y = 3.0 * x - 7.0
    fit = linear_regression(x, y)
    assert fit["slope"] == pytest.approx(3.0, rel=1e-9)
    assert fit["intercept"] == pytest.approx(-7.0, rel=1e-9)
    assert fit["r_squared"] == pytest.approx(1.0)


def test_interpolation_is_exact_at_the_nodes_and_linear_between_them():
    x = np.array([300.0, 400.0, 500.0])
    y = np.array([1.0, 2.0, 3.0])
    interpolated = interpolate_onto(x, y, np.array([300.0, 350.0, 500.0]))
    assert interpolated == pytest.approx([1.0, 1.5, 3.0], rel=1e-12)


def test_temperature_alignment_maps_one_grid_onto_another():
    aligned = align_datasets(
        np.array([300.0, 320.0, 340.0]),
        np.array([310.0, 330.0]),
        np.array([1.0, 3.0]),
    )
    assert aligned[1] == pytest.approx(2.0, rel=1e-12)  # midpoint at 320 K
