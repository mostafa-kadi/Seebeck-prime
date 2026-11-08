"""
Unit definitions and conversions for thermoelectric quantities.

All conversion functions are pure (no side effects, no GUI/IO dependencies).
The SI base unit is always used internally; these functions convert to/from
display units.

Conventions
-----------
* Temperature  : SI base = Kelvin [K]
* Conductivity : SI base = S/m
* Resistivity  : SI base = Ω·m
* Seebeck      : SI base = V/K
* Thermal cond.: SI base = W/(m·K)
* Power Factor : SI base = W/(m·K²)
"""

from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
# Temperature
# ─────────────────────────────────────────────────────────────────────────────

def celsius_to_kelvin(celsius: float) -> float:
    """T[K] = T[°C] + 273.15"""
    return celsius + 273.15


def kelvin_to_celsius(kelvin: float) -> float:
    """T[°C] = T[K] − 273.15"""
    return kelvin - 273.15


def to_kelvin(value: float, unit: str) -> float:
    """
    Convert a temperature value from any supported unit to Kelvin.

    Supported units: ``"K"``, ``"°C"``, ``"C"``

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit == "K":
        return float(value)
    if unit in ("°C", "C", "oC"):
        return celsius_to_kelvin(float(value))
    raise ValueError(f"Unknown temperature unit: '{unit}'. Supported: 'K', '°C'.")


def from_kelvin(value: float, unit: str) -> float:
    """
    Convert a temperature from Kelvin to any supported display unit.

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit == "K":
        return float(value)
    if unit in ("°C", "C", "oC"):
        return kelvin_to_celsius(float(value))
    raise ValueError(f"Unknown temperature unit: '{unit}'. Supported: 'K', '°C'.")


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature between any two supported units via Kelvin."""
    return from_kelvin(to_kelvin(value, from_unit), to_unit)


def convert_temperature_uncertainty(u: float) -> float:
    """
    Temperature uncertainty is invariant under °C ↔ K conversion
    (it is a difference/offset, not an absolute value).

    This function is a no-op included for documentation clarity.
    """
    return u


# ─────────────────────────────────────────────────────────────────────────────
# Electrical Conductivity / Resistivity
# ─────────────────────────────────────────────────────────────────────────────

def sigma_to_sm(value: float, unit: str) -> float:
    """Convert electrical conductivity to SI base [S/m]."""
    unit = unit.strip()
    if unit == "S/m":
        return float(value)
    if unit == "S/cm":
        return float(value) * 100.0
    if unit in ("Ohm-cm", "Ω·cm", "Ohm·cm"):
        return 100.0 / float(value) if value != 0 else 0.0
    raise ValueError(f"Unknown conductivity unit: '{unit}'.")


def sigma_from_sm(value: float, unit: str) -> float:
    """Convert electrical conductivity from SI base [S/m] to display unit."""
    unit = unit.strip()
    if unit == "S/m":
        return float(value)
    if unit == "S/cm":
        return float(value) / 100.0
    if unit in ("Ohm-cm", "Ω·cm", "Ohm·cm"):
        return 100.0 / float(value) if value != 0 else float("inf")
    raise ValueError(f"Unknown conductivity unit: '{unit}'.")


# ─────────────────────────────────────────────────────────────────────────────
# Seebeck Coefficient
# ─────────────────────────────────────────────────────────────────────────────

def seebeck_to_vk(value: float, unit: str) -> float:
    """Convert Seebeck coefficient to SI base [V/K]."""
    unit = unit.strip()
    if unit == "V/K":
        return float(value)
    if unit in ("µV/K", "μV/K", "uV/K"):
        return float(value) * 1e-6
    if unit == "mV/K":
        return float(value) * 1e-3
    raise ValueError(f"Unknown Seebeck unit: '{unit}'.")


def seebeck_from_vk(value: float, unit: str) -> float:
    """Convert Seebeck coefficient from SI base [V/K] to display unit."""
    unit = unit.strip()
    if unit == "V/K":
        return float(value)
    if unit in ("µV/K", "μV/K", "uV/K"):
        return float(value) * 1e6
    if unit == "mV/K":
        return float(value) * 1e3
    raise ValueError(f"Unknown Seebeck unit: '{unit}'.")


# ─────────────────────────────────────────────────────────────────────────────
# Power Factor
# ─────────────────────────────────────────────────────────────────────────────

def pf_to_si(value: float, unit: str) -> float:
    """Convert Power Factor to SI base [W/(m·K²)]."""
    unit = unit.strip()
    if unit == "W/(m·K²)":
        return float(value)
    if unit in ("mW/(m·K²)", "mW/mK²"):
        return float(value) * 1e-3
    if unit in ("µW/(m·K²)", "μW/(m·K²)", "μW/mK²", "µW/mK²"):
        return float(value) * 1e-6
    raise ValueError(f"Unknown PF unit: '{unit}'.")


def pf_from_si(value: float, unit: str) -> float:
    """Convert Power Factor from SI base [W/(m·K²)] to display unit."""
    unit = unit.strip()
    if unit == "W/(m·K²)":
        return float(value)
    if unit in ("mW/(m·K²)", "mW/mK²"):
        return float(value) * 1e3
    if unit in ("µW/(m·K²)", "μW/(m·K²)", "μW/mK²", "µW/mK²"):
        return float(value) * 1e6
    raise ValueError(f"Unknown PF unit: '{unit}'.")


# ─────────────────────────────────────────────────────────────────────────────
# Thermal Conductivity (display = SI here, just pass-through)
# ─────────────────────────────────────────────────────────────────────────────

def kappa_to_si(value: float, unit: str = "W/(m·K)") -> float:
    """Convert thermal conductivity to SI base [W/(m·K)].  Currently only W/(m·K) supported."""
    return float(value)


def kappa_from_si(value: float, unit: str = "W/(m·K)") -> float:
    """Convert thermal conductivity from SI base [W/(m·K)]. Currently only W/(m·K) supported."""
    return float(value)


# ─────────────────────────────────────────────────────────────────────────────
# Carrier Concentration
# ─────────────────────────────────────────────────────────────────────────────

def carrier_density_m3_to_cm3(value: float) -> float:
    """Convert carrier concentration from SI [m⁻³] to [cm⁻³]."""
    return float(value) * 1e-6


def carrier_density_cm3_to_m3(value: float) -> float:
    """Convert carrier concentration from [cm⁻³] to SI [m⁻³]."""
    return float(value) * 1e6
