import numpy as np
import pytest

from seebeck_prime.application.use_cases import (
    calculate_dulong_petit_limit_use_case,
    calculate_formula_mass_use_case,
    combine_relative_uncertainties_use_case,
    calculate_kappa_from_lfa_si_use_case,
    calculate_thermoelectric_properties,
    propagate_lfa_kappa_uncertainty_use_case,
)
from seebeck_prime.domain.physical_constants import DEFAULT_LORENZ, LEGACY_GAS_CONSTANT
from seebeck_prime.domain.uncertainty import propagate_kappa_e_error, propagate_zt_error


def test_transport_use_case_calculates_base_properties():
    result = calculate_thermoelectric_properties(
        np.array([300.0]),
        np.array([1e5]),
        np.array([100e-6]),
        np.array([2.0]),
    )

    assert result["PF"][0] == pytest.approx(1e-3)
    assert result["ZT"][0] == pytest.approx(0.15)


def test_laser_flash_kappa_use_case_accepts_si_values():
    assert calculate_kappa_from_lfa_si_use_case(1e-6, 1000.0, 6000.0) == pytest.approx(6.0)


def test_lfa_uncertainty_use_cases_combine_independent_errors():
    assert combine_relative_uncertainties_use_case(10.0, 0.03, 0.04) == pytest.approx(0.5)
    assert propagate_lfa_kappa_uncertainty_use_case(
        1e-6, 0.1e-6, 1000.0, 50.0, 6000.0, 300.0
    ) == pytest.approx(6.0 * np.sqrt(0.1**2 + 0.05**2 + 0.05**2))


def test_formula_mass_use_case_preserves_legacy_element_values():
    assert calculate_formula_mass_use_case("NaCl") == pytest.approx((58.44, 2))
    assert calculate_formula_mass_use_case("Og") == pytest.approx((294.0, 1))


def test_dulong_petit_use_case_preserves_legacy_units_and_constant():
    molar = calculate_dulong_petit_limit_use_case(5, 800.0, "J/mol·K")
    specific = calculate_dulong_petit_limit_use_case(5, 800.0, "J/kg·K")

    assert molar == pytest.approx(5 * 3 * LEGACY_GAS_CONSTANT)
    assert specific == pytest.approx(molar / 0.8)


def test_transport_use_case_propagates_temperature_uncertainty():
    temperature = np.array([300.0])
    conductivity = np.array([1e5])
    seebeck = np.array([100e-6])
    kappa = np.array([2.0])
    u_temperature = np.array([3.0])
    u_conductivity = np.array([5e3])
    u_seebeck = np.array([5e-6])
    u_kappa = np.array([0.1])

    result = calculate_thermoelectric_properties(
        temperature,
        conductivity,
        seebeck,
        kappa,
        u_sigma=u_conductivity,
        u_S=u_seebeck,
        u_kappa=u_kappa,
        u_T=u_temperature,
    )

    expected_kappa_e_error = propagate_kappa_e_error(
        conductivity,
        u_conductivity,
        temperature,
        u_temperature,
        DEFAULT_LORENZ,
        0.0,
    )
    expected_zt_error = propagate_zt_error(
        result["PF"],
        result["u_PF"],
        temperature,
        u_temperature,
        kappa,
        u_kappa,
    )

    assert result["u_kappa_e"][0] == pytest.approx(expected_kappa_e_error[0])
    assert result["u_ZT"][0] == pytest.approx(expected_zt_error[0])
