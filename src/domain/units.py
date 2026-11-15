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
* Density      : SI base = kg/m³
* Thermal diff.: SI base = m²/s
* Spec. heat   : SI base = J/(kg·K)
* Voltage      : SI base = V
* Length       : SI base = m
* Current      : SI base = A
* Mag. flux d. : SI base = T
* Hall coeff.  : SI base = m³/C
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


def conductivity_to_scm(value: float, unit: str) -> float:
    """Standardize a transport measurement (σ or ρ) to σ in [S/cm].

    The Hall workflow's application models work in cm-based units; this
    converts any supported transport unit to that σ contract.

    Supported units: ``"S/cm"`` (pass-through), ``"S/m"`` (÷100),
    ``"Ω·cm"``/``"Ohm-cm"`` (ρ → σ), ``"mΩ·cm"``/``"mOhm-cm"`` (ρ → σ).

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit == "S/cm":
        return float(value)
    if unit == "S/m":
        return float(value) / 100.0
    if unit in ("Ohm-cm", "Ω·cm", "Ohm·cm"):
        return 1.0 / float(value) if value != 0 else float("nan")
    if unit in ("mΩ·cm", "mOhm-cm", "mOhm·cm"):
        return 1000.0 / float(value) if value != 0 else float("nan")
    raise ValueError(f"Unknown transport unit: '{unit}'.")


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


def seebeck_to_uvk(value: float, unit: str) -> float:
    """Standardize a Seebeck coefficient to [µV/K].

    The SPB workflow's application models work in µV/K; this converts any
    supported Seebeck unit to that contract.

    Supported units: ``"µV/K"``/``"μV/K"``/``"uV/K"`` (pass-through),
    ``"mV/K"`` (×1e3), ``"V/K"`` (×1e6).

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit in ("µV/K", "μV/K", "uV/K"):
        return float(value)
    if unit == "mV/K":
        return float(value) * 1e3
    if unit == "V/K":
        return float(value) * 1e6
    raise ValueError(f"Unknown Seebeck unit: '{unit}'.")


# ─────────────────────────────────────────────────────────────────────────────
# Power Factor
# ─────────────────────────────────────────────────────────────────────────────

def pf_to_si(value: float, unit: str) -> float:
    """Convert Power Factor to SI base [W/(m·K²)].

    Accepted spellings (all equivalent):
      SI base : "W/(m·K²)", "W/(m*K^2)", "W/mK²"
      milli  : "mW/(m·K²)", "mW/(m*K^2)", "mW/mK²"
      micro  : "µW/(m·K²)", "μW/(m·K²)", "µW/(m*K^2)", "μW/(m*K^2)", "µW/mK²", "μW/mK²"
    """
    unit = unit.strip()
    if unit in ("W/(m·K²)", "W/(m*K^2)", "W/mK²"):
        return float(value)
    if unit in ("mW/(m·K²)", "mW/(m*K^2)", "mW/mK²"):
        return float(value) * 1e-3
    if unit in ("µW/(m·K²)", "μW/(m·K²)", "µW/(m*K^2)", "μW/(m*K^2)", "µW/mK²", "μW/mK²"):
        return float(value) * 1e-6
    raise ValueError(f"Unknown PF unit: '{unit}'.")


def pf_from_si(value: float, unit: str) -> float:
    """Convert Power Factor from SI base [W/(m·K²)] to display unit."""
    unit = unit.strip()
    if unit in ("W/(m·K²)", "W/(m*K^2)", "W/mK²"):
        return float(value)
    if unit in ("mW/(m·K²)", "mW/(m*K^2)", "mW/mK²"):
        return float(value) * 1e3
    if unit in ("µW/(m·K²)", "μW/(m·K²)", "µW/(m*K^2)", "μW/(m*K^2)", "µW/mK²", "μW/mK²"):
        return float(value) * 1e6
    raise ValueError(f"Unknown PF unit: '{unit}'.")


def kappa_to_si(value: float, unit: str = "W/(m·K)") -> float:
    """Convert thermal conductivity to SI base [W/(m·K)].

    Only the SI base unit is supported.  The unit argument is *validated*
    rather than ignored: silently accepting an unsupported unit (for example
    "W/(cm·K)", which differs by a factor of 100) would produce a silently
    wrong thermal conductivity.  An unsupported unit raises ``ValueError``,
    exactly as the other converters do.

    Accepted spellings (all equivalent):
      SI base : "W/(m·K)", "W/(m*K)", "W/mK"
    """
    unit = unit.strip()
    if unit in ("W/(m·K)", "W/(m*K)", "W/mK"):
        return float(value)
    raise ValueError(f"Unknown thermal conductivity unit: '{unit}'.")


def kappa_from_si(value: float, unit: str = "W/(m·K)") -> float:
    """Convert thermal conductivity from SI base [W/(m·K)] to display unit.

    Only the SI base unit is supported; see :func:`kappa_to_si`.
    """
    unit = unit.strip()
    if unit in ("W/(m·K)", "W/(m*K)", "W/mK"):
        return float(value)
    raise ValueError(f"Unknown thermal conductivity unit: '{unit}'.")


# ─────────────────────────────────────────────────────────────────────────────
# Carrier Concentration
# ─────────────────────────────────────────────────────────────────────────────

def carrier_density_m3_to_cm3(value: float) -> float:
    """Convert carrier concentration from SI [m⁻³] to [cm⁻³]."""
    return float(value) * 1e-6


def carrier_density_cm3_to_m3(value: float) -> float:
    """Convert carrier concentration from [cm⁻³] to SI [m⁻³]."""
    return float(value) * 1e6


# ─────────────────────────────────────────────────────────────────────────────
# Sample Physical Properties (LFA workflow)
# ─────────────────────────────────────────────────────────────────────────────

def density_to_si(value: float, unit: str) -> float:
    """Convert density to SI base [kg/m³].

    Supported units: ``"g/cm³"`` (×1000), ``"kg/m³"`` (pass-through).

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit in ("kg/m³", "kg/m^3"):
        return float(value)
    if unit in ("g/cm³", "g/cm^3"):
        return float(value) * 1000.0
    raise ValueError(f"Unknown density unit: '{unit}'.")


def density_from_si(value: float, unit: str) -> float:
    """Convert density from SI base [kg/m³] to display unit."""
    unit = unit.strip()
    if unit in ("kg/m³", "kg/m^3"):
        return float(value)
    if unit in ("g/cm³", "g/cm^3"):
        return float(value) / 1000.0
    raise ValueError(f"Unknown density unit: '{unit}'.")


def thermal_diffusivity_to_si(value: float, unit: str) -> float:
    """Convert thermal diffusivity to SI base [m²/s].

    Supported units: ``"mm²/s"`` (×1e-6), ``"m²/s"`` (pass-through).

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit in ("m²/s", "m2/s"):
        return float(value)
    if unit in ("mm²/s", "mm2/s"):
        return float(value) * 1e-6
    raise ValueError(f"Unknown thermal diffusivity unit: '{unit}'.")


def thermal_diffusivity_from_si(value: float, unit: str) -> float:
    """Convert thermal diffusivity from SI base [m²/s] to display unit."""
    unit = unit.strip()
    if unit in ("m²/s", "m2/s"):
        return float(value)
    if unit in ("mm²/s", "mm2/s"):
        return float(value) * 1e6
    raise ValueError(f"Unknown thermal diffusivity unit: '{unit}'.")


def specific_heat_to_si(value: float, unit: str) -> float:
    """Convert specific heat capacity to SI base [J/(kg·K)].

    Supported units: ``"J/(g·K)"`` and equivalent spellings (×1000),
    ``"J/(kg·K)"`` and equivalent spellings (pass-through).

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit in ("J/(kg·K)", "J/kg·K", "J/(kg*K)"):
        return float(value)
    if unit in ("J/(g·K)", "J/g·K", "J/(g*K)"):
        return float(value) * 1000.0
    raise ValueError(f"Unknown specific heat unit: '{unit}'.")


def specific_heat_from_si(value: float, unit: str) -> float:
    """Convert specific heat capacity from SI base [J/(kg·K)] to display unit."""
    unit = unit.strip()
    if unit in ("J/(kg·K)", "J/kg·K", "J/(kg*K)"):
        return float(value)
    if unit in ("J/(g·K)", "J/g·K", "J/(g*K)"):
        return float(value) / 1000.0
    raise ValueError(f"Unknown specific heat unit: '{unit}'.")


# ─────────────────────────────────────────────────────────────────────────────
# Hall Measurement Quantities
# ─────────────────────────────────────────────────────────────────────────────

def voltage_to_volt(value: float, unit: str) -> float:
    """Convert a voltage to SI base [V].

    Supported units: ``"V"`` (pass-through), ``"mV"`` (×1e-3),
    ``"µV"``/``"μV"``/``"uV"`` (×1e-6).

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit == "V":
        return float(value)
    if unit == "mV":
        return float(value) * 1e-3
    if unit in ("µV", "μV", "uV"):
        return float(value) * 1e-6
    raise ValueError(f"Unknown voltage unit: '{unit}'.")


def voltage_from_volt(value: float, unit: str) -> float:
    """Convert a voltage from SI base [V] to display unit."""
    unit = unit.strip()
    if unit == "V":
        return float(value)
    if unit == "mV":
        return float(value) * 1e3
    if unit in ("µV", "μV", "uV"):
        return float(value) * 1e6
    raise ValueError(f"Unknown voltage unit: '{unit}'.")


def length_to_meter(value: float, unit: str) -> float:
    """Convert a length to SI base [m].

    Supported units: ``"m"`` (pass-through), ``"cm"`` (×1e-2),
    ``"mm"`` (×1e-3), ``"µm"``/``"μm"``/``"um"`` (×1e-6).

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit == "m":
        return float(value)
    if unit == "cm":
        return float(value) * 1e-2
    if unit == "mm":
        return float(value) * 1e-3
    if unit in ("µm", "μm", "um"):
        return float(value) * 1e-6
    raise ValueError(f"Unknown length unit: '{unit}'.")


def length_from_meter(value: float, unit: str) -> float:
    """Convert a length from SI base [m] to display unit."""
    unit = unit.strip()
    if unit == "m":
        return float(value)
    if unit == "cm":
        return float(value) * 1e2
    if unit == "mm":
        return float(value) * 1e3
    if unit in ("µm", "μm", "um"):
        return float(value) * 1e6
    raise ValueError(f"Unknown length unit: '{unit}'.")


def current_to_ampere(value: float, unit: str) -> float:
    """Convert a current to SI base [A].

    Supported units: ``"A"`` (pass-through), ``"mA"`` (×1e-3),
    ``"µA"``/``"μA"``/``"uA"`` (×1e-6).

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit == "A":
        return float(value)
    if unit == "mA":
        return float(value) * 1e-3
    if unit in ("µA", "μA", "uA"):
        return float(value) * 1e-6
    raise ValueError(f"Unknown current unit: '{unit}'.")


def current_from_ampere(value: float, unit: str) -> float:
    """Convert a current from SI base [A] to display unit."""
    unit = unit.strip()
    if unit == "A":
        return float(value)
    if unit == "mA":
        return float(value) * 1e3
    if unit in ("µA", "μA", "uA"):
        return float(value) * 1e6
    raise ValueError(f"Unknown current unit: '{unit}'.")


def magnetic_flux_density_to_tesla(value: float, unit: str) -> float:
    """Convert a magnetic flux density to SI base [T].

    Supported units: ``"T"``, ``"Tesla"``, ``"Tesla (T)"`` (pass-through),
    ``"G"``, ``"Gauss"``, ``"Gauss (G)"`` (×1e-4).

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit in ("T", "Tesla", "Tesla (T)"):
        return float(value)
    if unit in ("G", "Gauss", "Gauss (G)"):
        return float(value) * 1e-4
    raise ValueError(f"Unknown magnetic flux density unit: '{unit}'.")


def magnetic_flux_density_from_tesla(value: float, unit: str) -> float:
    """Convert a magnetic flux density from SI base [T] to display unit."""
    unit = unit.strip()
    if unit in ("T", "Tesla", "Tesla (T)"):
        return float(value)
    if unit in ("G", "Gauss", "Gauss (G)"):
        return float(value) * 1e4
    raise ValueError(f"Unknown magnetic flux density unit: '{unit}'.")


def hall_coefficient_to_si(value: float, unit: str) -> float:
    """Convert a Hall coefficient to SI base [m³/C].

    Supported units: ``"m³/C"`` (pass-through), ``"cm³/C"`` (×1e-6).

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit == "m³/C":
        return float(value)
    if unit == "cm³/C":
        return float(value) * 1e-6
    raise ValueError(f"Unknown Hall coefficient unit: '{unit}'.")


def hall_coefficient_from_si(value: float, unit: str) -> float:
    """Convert a Hall coefficient from SI base [m³/C] to display unit."""
    unit = unit.strip()
    if unit == "m³/C":
        return float(value)
    if unit == "cm³/C":
        return float(value) * 1e6
    raise ValueError(f"Unknown Hall coefficient unit: '{unit}'.")


def hall_coefficient_to_cm3(value: float, unit: str) -> float:
    """Standardize a Hall coefficient to [cm³/C].

    The Hall workflow's application models work in cm-based units; this
    converts any supported Hall-coefficient unit to that contract.

    Supported units: ``"cm³/C"`` (pass-through), ``"m³/C"`` (×1e6).

    Raises:
        ValueError: If the unit is not recognised.
    """
    unit = unit.strip()
    if unit == "cm³/C":
        return float(value)
    if unit == "m³/C":
        return float(value) * 1e6
    raise ValueError(f"Unknown Hall coefficient unit: '{unit}'.")
