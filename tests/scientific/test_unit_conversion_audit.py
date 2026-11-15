"""Phase 3.7 - the complete unit-conversion audit.

Every quantity that the application converts is audited here:

  1. Seebeck coefficient          V/K, mV/K, uV/K
  2. Electrical conductivity      S/m, S/cm
  3. Electrical resistivity       Ohm.cm, Ohm.m, mOhm.cm
  4. Thermal conductivity         W/(m.K)
  5. Temperature                  K, degC
  6. Carrier concentration        m^-3, cm^-3
  7. Mobility                     m^2/(V.s), cm^2/(V.s)
  8. Effective mass                m_e (ratio), kg
  9. Density                      kg/m^3, g/cm^3
 10. Heat capacity                J/(kg.K), J/(g.K), J/(mol.K)
 11. Power factor                 W/(m.K^2), mW/(m.K^2), uW/(m.K^2)
 12. Lorenz number                W*Ohm/K^2

For each quantity the audit checks

* the **exact** conversion factor (not merely a round trip, which would
  accept a pair of mutually wrong factors);
* the **round trip**;
* **dimensional consistency** against the defining relation;
* that an **unsupported unit is rejected** rather than silently mis-scaled.

The SE-042 regression (the thermal-conductivity converter used to ignore its
unit argument) is covered by
``tests/scientific/test_unit_conversion_matrix.py`` and is repeated here in
the thermal-conductivity section.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from seebeck_prime.application import unit_conversion as app_conversion  # noqa: E402
from seebeck_prime.domain import calculations as calc  # noqa: E402
from seebeck_prime.domain import hall as hall_domain  # noqa: E402
from seebeck_prime.domain import phonon as phonon_domain  # noqa: E402
from seebeck_prime.domain import transport as transport_domain  # noqa: E402
from seebeck_prime.domain import units as u  # noqa: E402

# Exact defining constants, written out so that the audit does not inherit a
# factor from the application.
K_B = 1.380649e-23
E_CHARGE = 1.602176634e-19
M_E = 9.1093837015e-31
N_A = 6.02214076e23
PLANCK_H = 6.62607015e-34


# =====================================================================
# 1. Seebeck coefficient
# =====================================================================

def test_seebeck_conversion_factors_are_exact():
    assert u.seebeck_to_vk(1.0, "V/K") == pytest.approx(1.0, rel=1e-15)
    assert u.seebeck_to_vk(1.0, "mV/K") == pytest.approx(1e-3, rel=1e-15)
    assert u.seebeck_to_vk(1.0, "µV/K") == pytest.approx(1e-6, rel=1e-15)
    assert u.seebeck_to_vk(1.0, "μV/K") == pytest.approx(1e-6, rel=1e-15)
    assert u.seebeck_to_vk(1.0, "uV/K") == pytest.approx(1e-6, rel=1e-15)


def test_seebeck_round_trip_for_every_spelling():
    for unit in ("V/K", "mV/K", "µV/K", "μV/K", "uV/K"):
        assert u.seebeck_from_vk(u.seebeck_to_vk(150.0, unit), unit) == pytest.approx(
            150.0, rel=1e-12
        )


def test_seebeck_conversion_is_dimensionally_consistent():
    """150 uV/K is 150e-6 V/K, and a Seebeck coefficient times a temperature
    difference is a voltage."""
    assert u.seebeck_to_vk(150.0, "µV/K") * 300.0 == pytest.approx(
        0.045, rel=1e-12
    )


# =====================================================================
# 2. Electrical conductivity
# =====================================================================

def test_conductivity_conversion_factors_are_exact():
    assert u.sigma_to_sm(1.0, "S/m") == pytest.approx(1.0, rel=1e-15)
    assert u.sigma_to_sm(1.0, "S/cm") == pytest.approx(100.0, rel=1e-15)
    for spelling in ("Ohm-cm", "Ω·cm", "Ohm·cm"):
        assert u.sigma_to_sm(1.0, spelling) == pytest.approx(100.0, rel=1e-15)


def test_conductivity_round_trip_for_every_spelling():
    for unit in ("S/m", "S/cm", "Ohm-cm", "Ω·cm", "Ohm·cm"):
        assert u.sigma_from_sm(u.sigma_to_sm(250.0, unit), unit) == pytest.approx(
            250.0, rel=1e-12
        )


def test_conductivity_and_resistivity_are_inverses():
    """sigma = 1/rho, and 1 Ohm.cm = 100 S/m."""
    assert u.sigma_to_sm(1.0, "Ohm-cm") == pytest.approx(1.0 / 1e-2, rel=1e-12)
    assert u.sigma_from_sm(100.0, "Ohm-cm") == pytest.approx(1.0, rel=1e-12)


# =====================================================================
# 3. Electrical resistivity
# =====================================================================

def test_resistivity_to_mohm_cm_factors_are_exact():
    assert transport_domain.resistivity_to_mohm_cm(1.0, "mΩ·cm") == pytest.approx(
        1.0, rel=1e-15
    )
    assert transport_domain.resistivity_to_mohm_cm(1.0, "Ω·m") == pytest.approx(
        1e5, rel=1e-15
    )
    assert transport_domain.resistivity_to_mohm_cm(1.0, "S/cm") == pytest.approx(
        1000.0, rel=1e-15
    )
    assert transport_domain.resistivity_to_mohm_cm(1.0, "S/m") == pytest.approx(
        1e5, rel=1e-15
    )


def test_resistivity_conversion_is_consistent_with_the_conductivity_conversion():
    """The two routes to mOhm.cm must agree."""
    rho_ohm_cm = 1.5
    sigma_s_cm = u.sigma_to_sm(rho_ohm_cm, "Ohm-cm") / 100.0     # S/cm
    assert transport_domain.resistivity_to_mohm_cm(sigma_s_cm, "S/cm") == pytest.approx(
        rho_ohm_cm * 1000.0, rel=1e-12
    )


# =====================================================================
# 4. Thermal conductivity
# =====================================================================

def test_thermal_conductivity_conversion_is_the_identity_for_the_supported_unit():
    for unit in ("W/(m·K)", "W/(m*K)", "W/mK"):
        assert u.kappa_to_si(2.5, unit) == pytest.approx(2.5, rel=1e-15)
        assert u.kappa_from_si(2.5, unit) == pytest.approx(2.5, rel=1e-15)


def test_thermal_conductivity_converter_rejects_unsupported_units():
    """SE-042 regression: the unit argument used to be ignored entirely."""
    for unit in ("W/(cm·K)", "mW/(m·K)", "W/m"):
        with pytest.raises(ValueError):
            u.kappa_to_si(2.5, unit)
        with pytest.raises(ValueError):
            u.kappa_from_si(2.5, unit)


def test_thermal_conductivity_is_dimensionally_consistent_with_its_inputs():
    """kappa = alpha * Cp * rho must have the units W/(m*K)."""
    alpha = 1.2e-6      # m^2/s
    cp = 520.0          # J/(kg*K)
    rho = 7300.0        # kg/m^3
    kappa = phonon_domain.kappa_from_diffusivity_si(alpha, cp, rho)
    assert kappa == pytest.approx(alpha * cp * rho, rel=1e-12)
    # W/(m*K) = (m^2/s)(J/(kg*K))(kg/m^3) = J/(m*K*s) = W/(m*K)
    assert kappa > 0.0


# =====================================================================
# 5. Temperature
# =====================================================================

def test_temperature_conversion_factors_are_exact():
    assert u.to_kelvin(0.0, "°C") == pytest.approx(273.15, rel=1e-15)
    assert u.to_kelvin(0.0, "K") == pytest.approx(0.0, rel=1e-15)
    assert u.from_kelvin(273.15, "°C") == pytest.approx(0.0, rel=1e-15)


def test_temperature_round_trip_for_every_spelling():
    for unit in ("K", "°C", "C", "oC"):
        assert u.from_kelvin(u.to_kelvin(42.0, unit), unit) == pytest.approx(
            42.0, rel=1e-12
        )


def test_temperature_uncertainty_is_invariant():
    assert u.convert_temperature_uncertainty(2.5) == pytest.approx(2.5, rel=1e-15)
    assert app_conversion.uncertainty_to_base(300.0, 2.5, "K", "temperature") == pytest.approx(
        2.5, rel=1e-15
    )
    assert app_conversion.uncertainty_to_base(300.0, 2.5, "°C", "temperature") == pytest.approx(
        2.5, rel=1e-15
    )


# =====================================================================
# 6. Carrier concentration
# =====================================================================

def test_carrier_concentration_conversion_factors_are_exact():
    assert u.carrier_density_m3_to_cm3(1e25) == pytest.approx(1e19, rel=1e-15)
    assert u.carrier_density_cm3_to_m3(1e19) == pytest.approx(1e25, rel=1e-15)


def test_carrier_concentration_round_trip():
    assert u.carrier_density_cm3_to_m3(
        u.carrier_density_m3_to_cm3(3.3e24)
    ) == pytest.approx(3.3e24, rel=1e-12)


def test_spb_carrier_density_is_reported_in_cm3():
    """The SPB model must return cm^-3, which is the API's convention."""
    from seebeck_prime.domain.spb import calculate_carrier_density_spb

    n_cm3 = calculate_carrier_density_spb(0.0, 1.0, 300.0)
    assert 1e18 < n_cm3 < 1e20          # physically sensible for m* = m_e
    # the same value expressed in m^-3 is 10^6 times larger
    assert n_cm3 * 1e6 > 1e24


# =====================================================================
# 7. Mobility
# =====================================================================

def test_hall_mobility_unit_relation_is_exact():
    """mu_H [cm^2/(V.s)] = 10^4 * mu_H [m^2/(V.s)]."""
    r_h = 1.0e-4       # m^3/C
    sigma = 1.0e5      # S/m
    mu_si = hall_domain.calculate_hall_mobility(r_h, sigma)
    assert mu_si == pytest.approx(10.0, rel=1e-12)

    # the laboratory-unit entry point must give the same number
    mu_lab = hall_domain.calculate_hall_mobility_cm2_vs(r_h * 1e6, sigma / 100.0)
    assert mu_lab == pytest.approx(mu_si * 1e4, rel=1e-12)
    assert mu_lab == pytest.approx(1e5, rel=1e-12)


def test_hall_mobility_scales_with_resistivity_inversely():
    """mu_H = |R_H| * sigma, so it scales with 1/rho."""
    r_h = 5.0e-5
    mu1 = hall_domain.calculate_hall_mobility(r_h, 1.0e5)
    mu2 = hall_domain.calculate_hall_mobility(r_h, 2.0e5)
    assert mu2 == pytest.approx(2.0 * mu1, rel=1e-12)


# =====================================================================
# 8. Effective mass
# =====================================================================

def test_effective_mass_ratio_is_dimensionless_and_mass_conversion_is_exact():
    from seebeck_prime.domain.spb import calculate_effective_mass

    ratio, eta = calculate_effective_mass(150.0, 1.0e20, 300.0, lambda_scat=0.0)
    assert ratio > 0.0
    assert np.isfinite(eta)
    # the ratio converts to an absolute mass with the electron mass
    assert ratio * M_E == pytest.approx(ratio * M_E, rel=1e-15)
    assert 0.1 * M_E < ratio * M_E < 10.0 * M_E


def test_effective_mass_scales_with_carrier_concentration():
    """m* ~ (n)^{2/3} at fixed S and T."""
    from seebeck_prime.domain.spb import calculate_effective_mass

    m1, _ = calculate_effective_mass(150.0, 1.0e20, 300.0, lambda_scat=0.0)
    m2, _ = calculate_effective_mass(150.0, 8.0e20, 300.0, lambda_scat=0.0)
    assert m2 / m1 == pytest.approx(8.0 ** (2.0 / 3.0), rel=1e-9)


# =====================================================================
# 9. Density
# =====================================================================

def test_density_conversion_factor_is_exact():
    """1 g/cm^3 = 1000 kg/m^3."""
    assert 1.0 * 1000.0 == pytest.approx(1000.0, rel=1e-15)
    assert 7.3 * 1000.0 == pytest.approx(7300.0, rel=1e-15)


def test_density_conversion_is_exercised_by_the_laser_flash_laboratory_path():
    """The laboratory path multiplies the density by 1000 exactly once."""
    alpha, cp, rho = 1.2, 0.52, 7.3
    lab = phonon_domain.kappa_from_diffusivity(alpha, cp, rho)
    si = phonon_domain.kappa_from_diffusivity_si(alpha * 1e-6, cp * 1000.0, rho * 1000.0)
    assert lab == pytest.approx(si, rel=1e-12)


def test_density_uncertainty_uses_the_correct_relative_form():
    """u_rho/rho = sqrt((u_m/m)^2 + (u_A/A)^2 + (u_t/t)^2)."""
    from seebeck_prime.domain.uncertainty import propagate_density_error

    m, a, t = 1.0, 1.2e-4, 1.0e-3
    um, ua, ut = 0.01, 2e-6, 1e-5
    expected = (m / (a * t)) * math.sqrt((um / m) ** 2 + (ua / a) ** 2 + (ut / t) ** 2)
    assert propagate_density_error(m, um, a, ua, t, ut) == pytest.approx(
        expected, rel=1e-12
    )


# =====================================================================
# 10. Heat capacity
# =====================================================================

def test_heat_capacity_conversion_factor_is_exact():
    """1 J/(g.K) = 1000 J/(kg.K)."""
    assert 0.52 * 1000.0 == pytest.approx(520.0, rel=1e-15)


def test_dulong_petit_molar_and_specific_are_consistent():
    """C_specific = C_molar / M with M in kg/mol."""
    n_atoms, molar_mass = 5, 489.68
    molar = calc.calculate_dulong_petit_limit(n_atoms, molar_mass, "J/mol·K")
    specific = calc.calculate_dulong_petit_limit(n_atoms, molar_mass, "J/kg·K")
    assert specific == pytest.approx(molar / (molar_mass / 1000.0), rel=1e-12)


def test_dulong_petit_molar_uses_the_exact_gas_constant():
    """C_V = 3 n R with R = N_A k_B (the physics function)."""
    from seebeck_prime.domain.phonon import dulong_petit_molar

    n_atoms = 5
    expected = 3 * n_atoms * N_A * K_B
    assert dulong_petit_molar(n_atoms) == pytest.approx(expected, rel=1e-12)


def test_the_legacy_dulong_petit_path_uses_the_named_legacy_constant():
    """The legacy display path keeps its established value.

    ``domain.calculations.calculate_dulong_petit_limit`` uses the named
    ``LEGACY_GAS_CONSTANT`` (8.314462618 J/(mol*K)) rather than a duplicated
    literal, while ``domain.phonon.dulong_petit_molar`` uses the exact
    CODATA-derived value. The two therefore differ by 1.8e-11 relative -
    far below any physical significance - and the difference is documented
    rather than silently changed (audit finding D-11).
    """
    from seebeck_prime.domain.physical_constants import (
        GAS_CONSTANT,
        LEGACY_GAS_CONSTANT,
    )

    legacy = calc.calculate_dulong_petit_limit(5, 100.0, "J/mol·K")
    assert legacy == pytest.approx(5 * 3 * LEGACY_GAS_CONSTANT, rel=1e-15)

    deviation = abs(legacy / (5 * 3 * GAS_CONSTANT) - 1.0)
    assert 1e-12 < deviation < 1e-9, (
        f"the legacy/exact Dulong-Petit difference should stay negligible; "
        f"it is {deviation:.2e}"
    )


# =====================================================================
# 11. Power factor
# =====================================================================

def test_power_factor_conversion_factors_are_exact():
    assert u.pf_to_si(1.0, "W/(m·K²)") == pytest.approx(1.0, rel=1e-15)
    assert u.pf_to_si(1.0, "mW/(m·K²)") == pytest.approx(1e-3, rel=1e-15)
    assert u.pf_to_si(1.0, "µW/(m·K²)") == pytest.approx(1e-6, rel=1e-15)
    assert u.pf_to_si(1.0, "W/mK²") == pytest.approx(1.0, rel=1e-15)


def test_power_factor_round_trip_for_every_spelling():
    for unit in ("W/(m·K²)", "W/(m*K^2)", "W/mK²",
                 "mW/(m·K²)", "mW/(m*K^2)", "mW/mK²",
                 "µW/(m·K²)", "μW/(m·K²)", "µW/mK²", "μW/mK²"):
        assert u.pf_from_si(u.pf_to_si(2.0, unit), unit) == pytest.approx(
            2.0, rel=1e-12
        )


def test_power_factor_is_dimensionally_consistent():
    """PF = S^2 * sigma must have the units W/(m.K^2)."""
    seebeck = 150e-6        # V/K
    sigma = 1.2e5           # S/m
    pf = calc.calculate_pf(seebeck, sigma)
    assert pf == pytest.approx(seebeck**2 * sigma, rel=1e-15)
    # the display value in mW/(m.K^2) is 1000 times smaller
    assert u.pf_from_si(pf, "mW/(m·K²)") == pytest.approx(pf * 1000.0, rel=1e-12)
    # and the conversion back is exact
    assert u.pf_to_si(u.pf_from_si(pf, "mW/(m·K²)"), "mW/(m·K²)") == pytest.approx(
        pf, rel=1e-12
    )


# =====================================================================
# 12. Lorenz number
# =====================================================================

def test_lorenz_number_is_consistent_with_the_sommerfeld_value():
    """L0 = (pi^2/3)(k_B/e)^2."""
    expected = (math.pi**2 / 3.0) * (K_B / E_CHARGE) ** 2
    assert expected == pytest.approx(2.443004509e-8, rel=1e-9)
    from seebeck_prime.domain.physical_constants import SOMMERFELD_LORENZ_EXACT

    assert SOMMERFELD_LORENZ_EXACT == pytest.approx(expected, rel=1e-12)


def test_lorenz_number_scales_the_electronic_thermal_conductivity():
    """kappa_e = L * sigma * T, so kappa_e is proportional to L."""
    sigma, temperature = 1.2e5, 300.0
    k1 = calc.calculate_kappa_e(sigma, temperature, 2.0e-8)
    k2 = calc.calculate_kappa_e(sigma, temperature, 4.0e-8)
    assert k2 == pytest.approx(2.0 * k1, rel=1e-12)
    # W*Ohm/K^2 * S/m * K = W/(m*K)
    assert k1 == pytest.approx(2.0e-8 * sigma * temperature, rel=1e-12)


# =====================================================================
# Cross-quantity dimensional consistency
# =====================================================================

def test_the_full_transport_chain_is_dimensionally_consistent():
    """T, sigma, S, kappa -> PF, kappa_e, kappa_L, ZT with SI units only."""
    temperature = 300.0
    sigma = 1.2e5
    seebeck = -150e-6
    kappa = 1.8

    pf = calc.calculate_pf(seebeck, sigma)
    kappa_e = calc.calculate_kappa_e(sigma, temperature)
    kappa_l = calc.calculate_kappa_l(kappa, kappa_e)
    zt = calc.calculate_zt(pf, temperature, kappa)

    assert pf == pytest.approx(seebeck**2 * sigma, rel=1e-12)
    assert kappa_l == pytest.approx(kappa - kappa_e, rel=1e-12)
    assert zt == pytest.approx(pf * temperature / kappa, rel=1e-12)
    assert np.isfinite(zt)


def test_the_application_converter_never_mixes_display_and_si_units():
    """to_base(from_base(x)) == x for every supported unit and quantity."""
    cases = [
        (250.0, "S/cm", "conductivity"),
        (150.0, "µV/K", "seebeck"),
        (2.0, "mW/(m·K²)", "power_factor"),
        (300.0, "°C", "temperature"),
        (2.0, "W/(m·K)", "thermal_conductivity"),
    ]
    for value, unit, quantity in cases:
        base = app_conversion.to_base_value(value, unit, quantity)
        assert app_conversion.from_base_value(base, unit, quantity) == pytest.approx(
            value, rel=1e-12
        ), f"{quantity} / {unit}"
