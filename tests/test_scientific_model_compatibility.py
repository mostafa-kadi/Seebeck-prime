import pytest

from seebeck_prime.domain import hall, phonon, spb
from seebeck_prime.plugins import electronic, hall as legacy_hall, phonon as legacy_phonon


def test_hall_plugin_import_surface_delegates_to_domain():
    assert legacy_hall.calculate_hall_coefficient_from_raw is hall.calculate_hall_coefficient_from_raw
    assert legacy_hall.calculate_hall_carrier_density is hall.calculate_hall_carrier_density

    result = hall.calculate_hall_coefficient_from_raw(1e-3, 1e-3, 1e-2, 0.5)
    assert result == pytest.approx(2e-4)


def test_electronic_plugin_import_surface_delegates_to_domain():
    assert electronic.rigorous_lorenz_number is spb.rigorous_lorenz_number
    assert electronic.calculate_effective_mass is spb.calculate_effective_mass
    assert spb.fermi_integral(0.5, 0.0) == pytest.approx(0.6780938952, rel=1e-8)


def test_phonon_plugin_import_surface_delegates_to_domain():
    assert legacy_phonon.kappa_from_diffusivity_si is phonon.kappa_from_diffusivity_si
    assert legacy_phonon.kappa_from_diffusivity(1.0, 1.0, 5.0) == pytest.approx(5.0)


def test_thermal_plugin_import_surface_delegates_to_domain():
    from seebeck_prime.plugins import thermal as legacy_thermal
    from seebeck_prime.domain import calculations as domain_calculations

    assert legacy_thermal.calculate_kappa_e is domain_calculations.calculate_kappa_e
    assert legacy_thermal.calculate_kappa_l is domain_calculations.calculate_kappa_l
    assert legacy_thermal.calculate_kappa_e(1e5, 300.0) == pytest.approx(
        domain_calculations.calculate_kappa_e(1e5, 300.0)
    )
