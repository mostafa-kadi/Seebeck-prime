"""Application-facing unit conversion workflows for tabular measurements."""

from __future__ import annotations

from typing import Callable, Literal

import numpy as np

from seebeck_prime.domain.units import (
    carrier_density_cm3_to_m3 as _carrier_density_cm3_to_m3,
    carrier_density_m3_to_cm3 as _carrier_density_m3_to_cm3,
    conductivity_to_scm as _conductivity_to_scm,
    current_from_ampere,
    current_to_ampere,
    density_from_si,
    density_to_si,
    from_kelvin,
    hall_coefficient_from_si,
    hall_coefficient_to_cm3 as _hall_coefficient_to_cm3,
    hall_coefficient_to_si,
    kappa_from_si,
    kappa_to_si,
    length_from_meter,
    length_to_meter,
    magnetic_flux_density_from_tesla,
    magnetic_flux_density_to_tesla,
    pf_from_si,
    pf_to_si,
    seebeck_from_vk,
    seebeck_to_vk,
    sigma_from_sm,
    sigma_to_sm,
    seebeck_to_uvk as _seebeck_to_uvk,
    specific_heat_from_si,
    specific_heat_to_si,
    thermal_diffusivity_from_si,
    thermal_diffusivity_to_si,
    to_kelvin,
    voltage_from_volt,
    voltage_to_volt,
)

QuantityKind = Literal[
    "temperature",
    "conductivity",
    "seebeck",
    "power_factor",
    "thermal_conductivity",
    "density",
    "thermal_diffusivity",
    "specific_heat_capacity",
    "voltage",
    "length",
    "current",
    "magnetic_flux_density",
    "hall_coefficient",
]


def convert_temperature_to_kelvin(value: float, unit: str) -> float:
    return to_base_value(value, unit, "temperature")


def to_base_value(value: float, unit: str, quantity: QuantityKind) -> float:
    try:
        if quantity == "temperature":
            return to_kelvin(value, unit)
        if quantity == "conductivity":
            return sigma_to_sm(value, unit)
        if quantity == "seebeck":
            return seebeck_to_vk(value, unit)
        if quantity == "power_factor":
            return pf_to_si(value, unit)
        if quantity == "density":
            return density_to_si(value, unit)
        if quantity == "thermal_diffusivity":
            return thermal_diffusivity_to_si(value, unit)
        if quantity == "specific_heat_capacity":
            return specific_heat_to_si(value, unit)
        if quantity == "voltage":
            return voltage_to_volt(value, unit)
        if quantity == "length":
            return length_to_meter(value, unit)
        if quantity == "current":
            return current_to_ampere(value, unit)
        if quantity == "magnetic_flux_density":
            return magnetic_flux_density_to_tesla(value, unit)
        if quantity == "hall_coefficient":
            return hall_coefficient_to_si(value, unit)
        return kappa_to_si(value, unit)
    except ValueError:
        # Retain the legacy converter's pass-through for an unrecognized unit.
        return float(value)


def from_base_value(value: float, unit: str, quantity: QuantityKind) -> float:
    try:
        if quantity == "temperature":
            return from_kelvin(value, unit)
        if quantity == "conductivity":
            return sigma_from_sm(value, unit)
        if quantity == "seebeck":
            return seebeck_from_vk(value, unit)
        if quantity == "power_factor":
            return pf_from_si(value, unit)
        if quantity == "density":
            return density_from_si(value, unit)
        if quantity == "thermal_diffusivity":
            return thermal_diffusivity_from_si(value, unit)
        if quantity == "specific_heat_capacity":
            return specific_heat_from_si(value, unit)
        if quantity == "voltage":
            return voltage_from_volt(value, unit)
        if quantity == "length":
            return length_from_meter(value, unit)
        if quantity == "current":
            return current_from_ampere(value, unit)
        if quantity == "magnetic_flux_density":
            return magnetic_flux_density_from_tesla(value, unit)
        if quantity == "hall_coefficient":
            return hall_coefficient_from_si(value, unit)
        return kappa_from_si(value, unit)
    except ValueError:
        return float(value)


def _convert_values(
    values,
    unit: str,
    quantity: QuantityKind,
    converter: Callable[[float, str, QuantityKind], float],
) -> np.ndarray:
    """Apply a scalar application converter element-wise to an array."""
    array = np.asarray(values, dtype=float)
    converted = np.fromiter(
        (converter(float(v), unit, quantity) for v in array.ravel()),
        dtype=float,
        count=array.size,
    )
    return converted.reshape(array.shape)


def to_base_values(values, unit: str, quantity: QuantityKind) -> np.ndarray:
    """Convert an array of display-unit measurements to SI base units.

    Element-wise delegation to :func:`to_base_value`: the pass-through for
    unrecognized units and the NaN behaviour are identical to the scalar
    workflow. Accepts any array-like input and returns a float64
    :class:`numpy.ndarray` with the input's shape.
    """
    return _convert_values(values, unit, quantity, to_base_value)


def from_base_values(values, unit: str, quantity: QuantityKind) -> np.ndarray:
    """Convert an array of SI base values to display units.

    Element-wise delegation to :func:`from_base_value` (the conversion
    definitions live in :mod:`seebeck_prime.domain.units` only); accepts any
    array-like input and returns a float64 :class:`numpy.ndarray`.

    Note: for conductivity in ``S/cm`` the domain converter divides by
    100.0, where the retired inline GUI expression multiplied by 0.01. The
    two agree to within one double-precision ulp (measured maximum relative
    difference 2.22e-16), far below measurement precision.
    """
    return _convert_values(values, unit, quantity, from_base_value)


def uncertainty_to_base(value: float, uncertainty: float | None, unit: str, quantity: QuantityKind):
    if uncertainty is None:
        return None
    if quantity == "conductivity":
        if unit == "S/cm":
            return uncertainty * 100.0
        if unit in ("Ohm-cm", "Ω·cm", "Ohm·cm"):
            return uncertainty * (100.0 / value**2) if value != 0 else None
    if quantity == "seebeck":
        if unit in ("µV/K", "μV/K", "uV/K"):
            return uncertainty * 1e-6
        if unit == "mV/K":
            return uncertainty * 1e-3
    if quantity == "power_factor":
        if unit in ("μW/(m·K²)", "µW/(m·K²)", "μW/mK²", "µW/mK²"):
            return uncertainty * 1e-6
        if unit in ("mW/(m·K²)", "mW/mK²"):
            return uncertainty * 1e-3
    if quantity in (
        "density",
        "thermal_diffusivity",
        "specific_heat_capacity",
        "voltage",
        "length",
        "current",
        "magnetic_flux_density",
        "hall_coefficient",
    ):
        # Linear scale conversions: an uncertainty transforms exactly like
        # the value itself.
        return to_base_value(uncertainty, unit, quantity)
    return uncertainty


def uncertainty_from_base(value: float, uncertainty: float | None, unit: str, quantity: QuantityKind):
    if uncertainty is None:
        return None
    if quantity == "conductivity":
        if unit == "S/cm":
            return uncertainty / 100.0
        if unit in ("Ohm-cm", "Ω·cm", "Ohm·cm"):
            return uncertainty * (100.0 / value**2) if value != 0 else None
    if quantity == "seebeck":
        if unit in ("µV/K", "μV/K", "uV/K"):
            return uncertainty * 1e6
        if unit == "mV/K":
            return uncertainty * 1e3
    if quantity == "power_factor":
        if unit in ("μW/(m·K²)", "µW/(m·K²)", "μW/mK²", "µW/mK²"):
            return uncertainty * 1e6
        if unit in ("mW/(m·K²)", "mW/mK²"):
            return uncertainty * 1e3
    if quantity in (
        "density",
        "thermal_diffusivity",
        "specific_heat_capacity",
        "voltage",
        "length",
        "current",
        "magnetic_flux_density",
        "hall_coefficient",
    ):
        # Linear scale conversions: an uncertainty transforms exactly like
        # the value itself.
        return from_base_value(uncertainty, unit, quantity)
    return uncertainty


def conductivity_to_scm(value: float, unit: str) -> float:
    """Standardize a transport measurement (σ or ρ) to σ in [S/cm].

    This is the input contract of the Hall workflow's application models.
    As in :func:`to_base_value`, an unrecognized unit passes through
    unchanged (legacy behaviour of the presentation layer).
    """
    try:
        return _conductivity_to_scm(value, unit)
    except ValueError:
        return float(value)


def hall_coefficient_to_cm3(value: float, unit: str) -> float:
    """Standardize a Hall coefficient to [cm³/C].

    This is the input contract of the Hall workflow's application models.
    As in :func:`to_base_value`, an unrecognized unit passes through
    unchanged (legacy behaviour of the presentation layer).
    """
    try:
        return _hall_coefficient_to_cm3(value, unit)
    except ValueError:
        return float(value)


def carrier_density_m3_to_cm3(value: float) -> float:
    """Convert carrier concentration from SI [m⁻³] to [cm⁻³]."""
    return _carrier_density_m3_to_cm3(value)


def carrier_density_cm3_to_m3(value: float) -> float:
    """Convert carrier concentration from [cm⁻³] to SI [m⁻³]."""
    return _carrier_density_cm3_to_m3(value)


def seebeck_to_uvk(value: float, unit: str) -> float:
    """Standardize a Seebeck coefficient to [µV/K].

    This is the input contract of the SPB workflow's application models.
    As in :func:`to_base_value`, an unrecognized unit passes through
    unchanged (legacy behaviour of the presentation layer).
    """
    try:
        return _seebeck_to_uvk(value, unit)
    except ValueError:
        return float(value)
