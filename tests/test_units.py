import pytest
from seebeck_prime.domain.units import (
    celsius_to_kelvin,
    kelvin_to_celsius,
    to_kelvin,
    from_kelvin,
    convert_temperature,
    convert_temperature_uncertainty,
    sigma_to_sm,
    sigma_from_sm,
    seebeck_to_vk,
    seebeck_from_vk,
    pf_to_si,
    pf_from_si,
    kappa_to_si,
    kappa_from_si,
    carrier_density_m3_to_cm3,
    carrier_density_cm3_to_m3,
)


# --- Temperature Conversions ---
def test_celsius_to_kelvin():
    assert celsius_to_kelvin(0) == pytest.approx(273.15)
    assert celsius_to_kelvin(100) == pytest.approx(373.15)
    assert celsius_to_kelvin(-273.15) == pytest.approx(0)


def test_kelvin_to_celsius():
    assert kelvin_to_celsius(273.15) == pytest.approx(0)
    assert kelvin_to_celsius(373.15) == pytest.approx(100)
    assert kelvin_to_celsius(0) == pytest.approx(-273.15)


def test_to_kelvin():
    assert to_kelvin(100, "K") == pytest.approx(100)
    assert to_kelvin(0, "°C") == pytest.approx(273.15)
    assert to_kelvin(0, "C") == pytest.approx(273.15)
    assert to_kelvin(0, "oC") == pytest.approx(273.15)
    with pytest.raises(ValueError):
        to_kelvin(0, "F")


def test_from_kelvin():
    assert from_kelvin(100, "K") == pytest.approx(100)
    assert from_kelvin(273.15, "°C") == pytest.approx(0)
    assert from_kelvin(273.15, "C") == pytest.approx(0)
    assert from_kelvin(273.15, "oC") == pytest.approx(0)
    with pytest.raises(ValueError):
        from_kelvin(0, "F")


def test_convert_temperature():
    assert convert_temperature(0, "°C", "K") == pytest.approx(273.15)
    assert convert_temperature(273.15, "K", "°C") == pytest.approx(0)
    assert convert_temperature(25, "C", "K") == pytest.approx(298.15)


def test_convert_temperature_uncertainty():
    assert convert_temperature_uncertainty(1.0) == 1.0
    assert convert_temperature_uncertainty(0.5) == 0.5


# --- Electrical Conductivity / Resistivity Conversions ---
def test_sigma_to_sm():
    assert sigma_to_sm(1, "S/m") == pytest.approx(1)
    assert sigma_to_sm(1, "S/cm") == pytest.approx(100)
    assert sigma_to_sm(1, "Ohm-cm") == pytest.approx(100)
    assert sigma_to_sm(0.5, "Ohm-cm") == pytest.approx(200)
    assert sigma_to_sm(0, "Ohm-cm") == pytest.approx(0)  # Division by zero handled
    with pytest.raises(ValueError):
        sigma_to_sm(1, "mS/m")


def test_sigma_from_sm():
    assert sigma_from_sm(1, "S/m") == pytest.approx(1)
    assert sigma_from_sm(100, "S/cm") == pytest.approx(1)
    assert sigma_from_sm(100, "Ohm-cm") == pytest.approx(1)
    assert sigma_from_sm(200, "Ohm-cm") == pytest.approx(0.5)
    assert sigma_from_sm(0, "Ohm-cm") == pytest.approx(
        float("inf")
    )  # Division by zero handled
    with pytest.raises(ValueError):
        sigma_from_sm(1, "mS/m")


# --- Seebeck Coefficient Conversions ---
def test_seebeck_to_vk():
    assert seebeck_to_vk(1, "V/K") == pytest.approx(1)
    assert seebeck_to_vk(1, "µV/K") == pytest.approx(1e-6)
    assert seebeck_to_vk(1, "μV/K") == pytest.approx(1e-6)
    assert seebeck_to_vk(1, "uV/K") == pytest.approx(1e-6)
    assert seebeck_to_vk(1, "mV/K") == pytest.approx(1e-3)
    with pytest.raises(ValueError):
        seebeck_to_vk(1, "nV/K")


def test_seebeck_from_vk():
    assert seebeck_from_vk(1, "V/K") == pytest.approx(1)
    assert seebeck_from_vk(1e-6, "µV/K") == pytest.approx(1)
    assert seebeck_from_vk(1e-6, "μV/K") == pytest.approx(1)
    assert seebeck_from_vk(1e-6, "uV/K") == pytest.approx(1)
    assert seebeck_from_vk(1e-3, "mV/K") == pytest.approx(1)
    with pytest.raises(ValueError):
        seebeck_from_vk(1, "nV/K")


# --- Power Factor Conversions ---
def test_pf_to_si():
    assert pf_to_si(1, "W/(m·K²)") == pytest.approx(1)
    assert pf_to_si(1, "mW/(m·K²)") == pytest.approx(1e-3)
    assert pf_to_si(1, "mW/mK²") == pytest.approx(1e-3)
    assert pf_to_si(1, "µW/(m·K²)") == pytest.approx(1e-6)
    assert pf_to_si(1, "μW/(m·K²)") == pytest.approx(1e-6)
    assert pf_to_si(1, "μW/mK²") == pytest.approx(1e-6)
    assert pf_to_si(1, "µW/mK²") == pytest.approx(1e-6)
    with pytest.raises(ValueError):
        pf_to_si(1, "nW/(m·K²)")


def test_pf_from_si():
    assert pf_from_si(1, "W/(m·K²)") == pytest.approx(1)
    assert pf_from_si(1e-3, "mW/(m·K²)") == pytest.approx(1)
    assert pf_from_si(1e-3, "mW/mK²") == pytest.approx(1)
    assert pf_from_si(1e-6, "µW/(m·K²)") == pytest.approx(1)
    assert pf_from_si(1e-6, "μW/(m·K²)") == pytest.approx(1)
    assert pf_from_si(1e-6, "μW/mK²") == pytest.approx(1)
    assert pf_from_si(1e-6, "µW/mK²") == pytest.approx(1)
    with pytest.raises(ValueError):
        pf_from_si(1, "nW/(m·K²)")


# --- Thermal Conductivity Conversions ---
def test_kappa_to_si():
    assert kappa_to_si(1, "W/(m·K)") == pytest.approx(1)
    # Test with default unit
    assert kappa_to_si(1) == pytest.approx(1)


def test_kappa_from_si():
    assert kappa_from_si(1, "W/(m·K)") == pytest.approx(1)
    # Test with default unit
    assert kappa_from_si(1) == pytest.approx(1)


# --- Carrier Concentration Conversions ---
def test_carrier_density_m3_to_cm3():
    assert carrier_density_m3_to_cm3(1e20) == pytest.approx(1e14)
    assert carrier_density_m3_to_cm3(1e26) == pytest.approx(1e20)


def test_carrier_density_cm3_to_m3():
    assert carrier_density_cm3_to_m3(1e14) == pytest.approx(1e20)
    assert carrier_density_cm3_to_m3(1e20) == pytest.approx(1e26)
