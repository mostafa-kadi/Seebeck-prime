"""Physical-constraint tests: invalid physical results must be flagged.

Phase VIII of the validation plan: the software must not silently accept a
physically impossible result (for example a negative lattice thermal
conductivity) without reporting it.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from seebeck_prime.domain import calculations as calc  # noqa: E402
from seebeck_prime.domain import validation as domain_validation  # noqa: E402
from seebeck_prime.application.use_cases import (  # noqa: E402
    calculate_thermoelectric_properties,
    validate_measurement_data,
)


def test_negative_lattice_thermal_conductivity_is_reported_by_the_validator():
    """kappa_L < 0 signals a too-large Lorenz number or a unit error."""
    messages = domain_validation.validate_kappa_l_array(np.array([-0.5]))

    assert len(messages) == 1
    assert messages[0].severity is domain_validation.Severity.WARNING
    assert messages[0].field == "kappa_L"


def test_negative_lattice_conductivity_is_reachable_from_the_application_layer():
    """The application must be able to surface the negative-kappa_L warning."""
    messages = validate_measurement_data(
        T=np.array([300.0]),
        sigma=np.array([1.0e5]),
        S=np.array([-1.0e-4]),
        kappa=np.array([2.0]),
        kappa_L=np.array([-0.5]),
    )

    assert any(m.field == "kappa_L" for m in messages)


def test_non_positive_temperature_is_an_error():
    messages = domain_validation.validate_temperature_array(np.array([300.0, -1.0]))

    assert any(
        m.severity is domain_validation.Severity.ERROR and m.field == "T"
        for m in messages
    )


def test_duplicate_temperatures_are_reported():
    messages = domain_validation.validate_temperature_array(np.array([300.0, 300.0]))

    assert any("Duplicate" in m.message for m in messages)


def test_extreme_but_possible_seebeck_is_reported_as_a_warning():
    """3 mV/K is far outside the thermoelectric range and must be flagged."""
    messages = domain_validation.validate_seebeck_array(np.array([3.0e-3]))

    assert messages and messages[0].severity is domain_validation.Severity.WARNING


def test_power_factor_is_never_negative():
    """PF is a non-negative quantity for any real Seebeck coefficient."""
    for seebeck in (-1.0e-3, -1.0e-6, 0.0, 1.0e-6, 1.0e-3):
        for sigma in (0.0, 1.0e3, 1.0e5):
            assert calc.calculate_pf(seebeck, sigma) >= 0.0


def test_figure_of_merit_is_negative_only_when_thermal_conductivity_is_negative():
    """ZT inherits the sign of 1/kappa; a negative kappa is a physical error."""
    assert calc.calculate_zt(1e-3, 300.0, 2.0) > 0.0
    assert calc.calculate_zt(1e-3, 300.0, -2.0) < 0.0


def test_electronic_thermal_conductivity_cannot_exceed_total_for_valid_input():
    """A kappa_e above kappa_total means the input combination is impossible."""
    sigma, temperature, kappa_total = 1.0e6, 500.0, 1.0
    kappa_e = calc.calculate_kappa_e(sigma, temperature)
    assert kappa_e > kappa_total          # an impossible combination
    kappa_l = calc.calculate_kappa_l(kappa_total, kappa_e)
    assert kappa_l < 0.0                  # and the validator flags it
    assert domain_validation.validate_kappa_l_array(np.array([kappa_l]))


def test_carrier_concentration_and_mobility_stay_positive_for_valid_input():
    """The SPB outputs must be positive for physical inputs."""
    from seebeck_prime.domain.spb import (
        calculate_carrier_density_spb,
        calculate_effective_mass,
    )

    n = calculate_carrier_density_spb(0.0, 1.0, 300.0)
    mass, _ = calculate_effective_mass(150.0, 1.0e20, 300.0)
    assert n > 0.0
    assert mass > 0.0


def test_weighted_mobility_is_positive_for_positive_resistivity():
    from seebeck_prime.domain.transport import calculate_weighted_mobility

    assert calculate_weighted_mobility(300.0, 1.0, -150.0) > 0.0
    # Zero resistivity carries no information and must not yield a number.
    assert np.isnan(calculate_weighted_mobility(300.0, 0.0, -150.0))


def test_hall_carrier_type_follows_the_sign_of_the_hall_coefficient():
    from seebeck_prime.domain.hall import determine_carrier_type

    assert determine_carrier_type(1.0e-4) == "p-type"
    assert determine_carrier_type(-1.0e-4) == "n-type"
    assert determine_carrier_type(0.0) == "undetermined"


def test_temperature_dependent_properties_are_consistent_along_a_series():
    """PF, kappa_e, kappa_L and ZT must stay mutually consistent row-wise."""
    temperature = np.array([300.0, 350.0, 400.0])
    sigma = np.array([1.2e5, 1.1e5, 1.0e5])
    seebeck = np.array([-1.5e-4, -1.4e-4, -1.3e-4])
    kappa = np.array([1.8, 1.9, 2.0])

    result = calculate_thermoelectric_properties(temperature, sigma, seebeck, kappa)

    assert result["PF"] == pytest.approx(
        (seebeck**2) * sigma, rel=1e-12
    )
    assert result["kappa_L"] == pytest.approx(
        kappa - result["kappa_e"], rel=1e-12
    )
    assert result["ZT"] == pytest.approx(
        result["PF"] * temperature / kappa, rel=1e-12
    )
