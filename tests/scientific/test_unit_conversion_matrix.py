"""Phase VII: unit-conversion validation matrix.

Covers every supported unit, the round-trip identity, the conversion of
*uncertainties*, and the central invariant: **no calculation may mix display
units with internal SI units**.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from seebeck_prime.application import unit_conversion as app_conversion  # noqa: E402
from seebeck_prime.application.use_cases import (  # noqa: E402
    convert_resistivity_to_mohm_cm,
)
from seebeck_prime.domain import units as domain_units  # noqa: E402

CONDUCTIVITY_UNITS = ("S/m", "S/cm", "Ohm-cm", "\u03a9\u00b7cm", "Ohm\u00b7cm")
SEEBECK_UNITS = ("V/K", "\u00b5V/K", "\u03bcV/K", "uV/K", "mV/K")
PF_UNITS = ("W/(m\u00b7K\u00b2)", "mW/(m\u00b7K\u00b2)", "mW/mK\u00b2",
            "\u00b5W/(m\u00b7K\u00b2)", "\u03bcW/mK\u00b2", "W/mK\u00b2")
TEMPERATURE_UNITS = ("K", "\u00b0C", "C", "oC")


@pytest.mark.parametrize("unit", CONDUCTIVITY_UNITS)
def test_conductivity_round_trip_for_every_supported_unit(unit):
    original = 1234.5
    base = domain_units.sigma_to_sm(original, unit)
    assert domain_units.sigma_from_sm(base, unit) == pytest.approx(original, rel=1e-12)


@pytest.mark.parametrize("unit", SEEBECK_UNITS)
def test_seebeck_round_trip_for_every_supported_unit(unit):
    original = 150.0
    base = domain_units.seebeck_to_vk(original, unit)
    assert domain_units.seebeck_from_vk(base, unit) == pytest.approx(original, rel=1e-12)


@pytest.mark.parametrize("unit", PF_UNITS)
def test_power_factor_round_trip_for_every_supported_unit(unit):
    original = 2.5e-3
    base = domain_units.pf_to_si(original, unit)
    assert domain_units.pf_from_si(base, unit) == pytest.approx(original, rel=1e-12)


@pytest.mark.parametrize("unit", TEMPERATURE_UNITS)
def test_temperature_round_trip_for_every_supported_unit(unit):
    original = 42.0
    base = domain_units.to_kelvin(original, unit)
    assert domain_units.from_kelvin(base, unit) == pytest.approx(original, rel=1e-12)


def test_exact_conversion_factors_are_used():
    """The factors are fixed by definition, not by convention."""
    assert domain_units.sigma_to_sm(1.0, "S/cm") == pytest.approx(100.0, rel=1e-12)
    assert domain_units.sigma_to_sm(1.0, "Ohm-cm") == pytest.approx(100.0, rel=1e-12)
    assert domain_units.seebeck_to_vk(1.0, "\u00b5V/K") == pytest.approx(1e-6, rel=1e-12)
    assert domain_units.seebeck_to_vk(1.0, "mV/K") == pytest.approx(1e-3, rel=1e-12)
    assert domain_units.pf_to_si(1.0, "mW/mK\u00b2") == pytest.approx(1e-3, rel=1e-12)
    assert domain_units.pf_to_si(1.0, "\u00b5W/mK\u00b2") == pytest.approx(1e-6, rel=1e-12)
    assert domain_units.carrier_density_m3_to_cm3(1e25) == pytest.approx(1e19, rel=1e-12)
    assert domain_units.carrier_density_cm3_to_m3(1e19) == pytest.approx(1e25, rel=1e-12)
    assert domain_units.to_kelvin(0.0, "\u00b0C") == pytest.approx(273.15, rel=1e-12)


def test_unknown_units_are_rejected_rather_than_guessed():
    for converter, unit in (
        (domain_units.sigma_to_sm, "S/fortnight"),
        (domain_units.seebeck_to_vk, "V/degree"),
        (domain_units.pf_to_si, "W/(m*K)"),
        (domain_units.to_kelvin, "Kelvin"),
    ):
        with pytest.raises(ValueError):
            converter(1.0, unit)


def test_thermal_conductivity_converter_validates_its_unit():
    """Regression test for defect SE-046: the kappa converter used to ignore
    the unit argument entirely.

    ``kappa_to_si(1.0, "W/(cm·K)")`` returned 1.0, i.e. the value was taken
    to be W/(m·K) although W/(cm·K) is a factor of 100 smaller.  A silently
    wrong thermal conductivity propagates into kappa_L and ZT, so the
    converter must reject the unsupported unit instead.
    """
    # the supported spellings are accepted
    for unit in ("W/(m·K)", "W/(m*K)", "W/mK"):
        assert domain_units.kappa_to_si(2.5, unit) == pytest.approx(2.5, rel=1e-12)
        assert domain_units.kappa_from_si(2.5, unit) == pytest.approx(2.5, rel=1e-12)

    # an unsupported unit must be rejected, not silently mis-scaled
    for unit in ("W/(cm·K)", "mW/(m·K)", "W/m"):
        with pytest.raises(ValueError):
            domain_units.kappa_to_si(2.5, unit)
        with pytest.raises(ValueError):
            domain_units.kappa_from_si(2.5, unit)


def test_application_layer_keeps_its_legacy_passthrough_for_unknown_units():
    """The application-level converter deliberately passes unknown units
    through unchanged; raising in the domain converter must not change that
    observable behaviour."""
    assert app_conversion.to_base_value(
        2.5, "W/(cm·K)", "thermal_conductivity"
    ) == pytest.approx(2.5, rel=1e-12)
    assert app_conversion.from_base_value(
        2.5, "W/(cm·K)", "thermal_conductivity"
    ) == pytest.approx(2.5, rel=1e-12)


def test_temperature_uncertainty_is_invariant_under_the_offset_conversion():
    """A difference is unchanged by an offset."""
    assert domain_units.convert_temperature_uncertainty(2.5) == 2.5
    assert app_conversion.uncertainty_to_base(300.0, 2.5, "K", "temperature") == 2.5
    assert app_conversion.uncertainty_to_base(300.0, 2.5, "\u00b0C", "temperature") == 2.5


def test_conductivity_uncertainty_conversion_is_correct():
    """S/cm: u scales like the value; Ohm-cm: u_sigma = u_rho * 100/rho^2."""
    assert app_conversion.uncertainty_to_base(
        100.0, 5.0, "S/cm", "conductivity") == pytest.approx(500.0, rel=1e-12)
    # rho = 2 Ohm.cm -> sigma = 50 S/m; u_sigma = u_rho * 100 / rho^2 = 5*100/4
    assert app_conversion.uncertainty_to_base(
        2.0, 5.0, "Ohm-cm", "conductivity") == pytest.approx(125.0, rel=1e-12)


def test_seebeck_and_power_factor_uncertainty_conversion_is_linear():
    assert app_conversion.uncertainty_to_base(
        150.0, 3.0, "\u00b5V/K", "seebeck") == pytest.approx(3e-6, rel=1e-12)
    assert app_conversion.uncertainty_to_base(
        2.0, 0.1, "mW/mK\u00b2", "power_factor") == pytest.approx(1e-4, rel=1e-12)


def test_uncertainty_conversion_is_the_inverse_of_the_value_conversion():
    for unit, quantity, value in (
        ("S/cm", "conductivity", 250.0),
        ("\u00b5V/K", "seebeck", 150.0),
        ("mW/mK\u00b2", "power_factor", 2.0),
    ):
        base = app_conversion.to_base_value(value, unit, quantity)
        assert app_conversion.from_base_value(base, unit, quantity) == pytest.approx(
            value, rel=1e-12
        )


def test_display_units_and_internal_si_values_are_never_mixed():
    """The invariant: converting a base value to display and back is lossless,
    and the base value is unchanged by the display round trip."""
    base = 2.0e-3
    for unit in PF_UNITS:
        display = app_conversion.from_base_value(base, unit, "power_factor")
        assert app_conversion.to_base_value(display, unit, "power_factor") == pytest.approx(
            base, rel=1e-12
        )


def test_a_single_si_value_converts_to_consistent_display_values():
    """1 W/(m*K^2) is 1000 mW/(m*K^2) and 1e6 uW/(m*K^2)."""
    assert app_conversion.from_base_value(1.0, "mW/mK\u00b2", "power_factor") == pytest.approx(
        1000.0, rel=1e-12
    )
    assert app_conversion.from_base_value(1.0, "\u00b5W/mK\u00b2", "power_factor") == pytest.approx(
        1.0e6, rel=1e-12
    )


def test_conductivity_display_units_are_consistent_with_each_other():
    """1 S/cm equals 100 S/m equals 0.01 Ohm.cm."""
    si = app_conversion.to_base_value(1.0, "S/cm", "conductivity")
    assert si == pytest.approx(100.0, rel=1e-12)
    # rho = 0.01 Ohm.cm = 1e-4 Ohm.m -> sigma = 1e4 S/m
    assert app_conversion.to_base_value(0.01, "Ohm-cm", "conductivity") == pytest.approx(
        1.0e4, rel=1e-12
    )
    # and 100 S/m = 1 S/cm = 1 Ohm.cm  (rho = 100/sigma in Ohm.cm)
    assert app_conversion.from_base_value(100.0, "Ohm-cm", "conductivity") == pytest.approx(
        1.0, rel=1e-12
    )


# ─────────────────────────────────────────────────────────────────────────────
# Vector conversion helpers (Phase 3 architecture migration, migration-map
# step 3b): the GUI auto-populate paths must delegate their unit conversion
# to the application layer instead of multiplying inline factors.
# ─────────────────────────────────────────────────────────────────────────────

VECTOR_SAMPLE = np.array([0.0, 1.0, 250.0, 8e4, 1.234567e5])
VECTOR_SAMPLE_WITH_NAN = np.array([0.0, 250.0, np.nan, 1.234567e5])


def test_vector_to_base_conversion_matches_the_scalar_converter_element_for_element():
    converted = app_conversion.to_base_values(
        VECTOR_SAMPLE_WITH_NAN, "S/cm", "conductivity"
    )
    expected = np.array(
        [
            app_conversion.to_base_value(v, "S/cm", "conductivity")
            for v in VECTOR_SAMPLE_WITH_NAN
        ]
    )
    finite = np.isfinite(VECTOR_SAMPLE_WITH_NAN)
    np.testing.assert_array_equal(converted[finite], expected[finite])
    # NaN must stay NaN in the same position
    assert np.array_equal(np.isnan(converted), np.isnan(expected))
    assert converted.shape == VECTOR_SAMPLE_WITH_NAN.shape


def test_vector_from_base_conversion_matches_the_scalar_converter_element_for_element():
    converted = app_conversion.from_base_values(
        VECTOR_SAMPLE_WITH_NAN, "\u00b5V/K", "seebeck"
    )
    expected = np.array(
        [
            app_conversion.from_base_value(v, "\u00b5V/K", "seebeck")
            for v in VECTOR_SAMPLE_WITH_NAN
        ]
    )
    finite = np.isfinite(VECTOR_SAMPLE_WITH_NAN)
    np.testing.assert_array_equal(converted[finite], expected[finite])
    # NaN must stay NaN in the same position
    assert np.array_equal(np.isnan(converted), np.isnan(expected))
    assert converted.shape == VECTOR_SAMPLE_WITH_NAN.shape


def test_vector_conversion_keeps_the_legacy_passthrough_for_unknown_units():
    """Same observable behaviour as the scalar workflow (see
    test_application_layer_keeps_its_legacy_passthrough_for_unknown_units)."""
    converted = app_conversion.from_base_values(
        VECTOR_SAMPLE, "S/fortnight", "conductivity"
    )
    np.testing.assert_array_equal(converted, VECTOR_SAMPLE)


def test_vector_seebeck_conversion_is_bit_identical_to_the_retired_inline_factor():
    """The GUI auto-populate used ``values * 1e6`` (V/K -> uV/K); the delegated
    domain converter performs the same operation, so the results must be
    bit-for-bit identical."""
    converted = app_conversion.from_base_values(VECTOR_SAMPLE, "uV/K", "seebeck")
    np.testing.assert_array_equal(converted, VECTOR_SAMPLE * 1e6)


def test_vector_conductivity_conversion_agrees_with_the_retired_inline_factor():
    """The GUI auto-populate used ``values * 0.01`` (S/m -> S/cm); the
    delegated domain converter divides by 100.0. Measured worst-case
    relative difference over 2e5 sampled magnitudes: 2.22e-16 — under one
    double-precision ulp. Zero must still convert to exact +0.0."""
    converted = app_conversion.from_base_values(VECTOR_SAMPLE, "S/cm", "conductivity")
    historical = VECTOR_SAMPLE * 0.01
    np.testing.assert_array_almost_equal_nulp(converted, historical, nulp=4)
    assert converted[0] == 0.0


def test_vector_conversion_round_trip_stays_far_below_measurement_precision():
    """The display round trip may differ by a few ulps from double rounding;
    that remains orders of magnitude below any measured-data precision."""
    for unit, quantity in (("S/cm", "conductivity"), ("\u00b5V/K", "seebeck")):
        display = app_conversion.from_base_values(VECTOR_SAMPLE, unit, quantity)
        round_trip = app_conversion.to_base_values(display, unit, quantity)
        np.testing.assert_array_almost_equal_nulp(round_trip, VECTOR_SAMPLE, nulp=8)


# ─────────────────────────────────────────────────────────────────────────────
# Sample physical properties (Phase 3 architecture migration, migration-map
# step 3d): density, thermal diffusivity and specific heat capacity as used by
# the LFA κ workflow.
# ─────────────────────────────────────────────────────────────────────────────

DENSITY_UNITS = ("g/cm\u00b3", "kg/m\u00b3")
DIFFUSIVITY_UNITS = ("mm\u00b2/s", "m\u00b2/s")
CP_UNITS = ("J/(g\u00b7K)", "J/g\u00b7K", "J/(g*K)")


@pytest.mark.parametrize("unit", DENSITY_UNITS)
def test_density_round_trip_for_every_supported_unit(unit):
    original = 5.32
    base = domain_units.density_to_si(original, unit)
    assert domain_units.density_from_si(base, unit) == pytest.approx(original, rel=1e-12)


@pytest.mark.parametrize("unit", DIFFUSIVITY_UNITS)
def test_thermal_diffusivity_round_trip_for_every_supported_unit(unit):
    original = 1.5
    base = domain_units.thermal_diffusivity_to_si(original, unit)
    assert domain_units.thermal_diffusivity_from_si(base, unit) == pytest.approx(
        original, rel=1e-12
    )


@pytest.mark.parametrize("unit", CP_UNITS)
def test_specific_heat_round_trip_for_every_supported_unit(unit):
    original = 0.7
    base = domain_units.specific_heat_to_si(original, unit)
    assert domain_units.specific_heat_from_si(base, unit) == pytest.approx(
        original, rel=1e-12
    )


def test_sample_property_conversion_factors_are_exact():
    assert domain_units.density_to_si(1.0, "g/cm\u00b3") == pytest.approx(1000.0, rel=1e-12)
    assert domain_units.density_to_si(42.0, "kg/m\u00b3") == 42.0
    assert domain_units.thermal_diffusivity_to_si(1.0, "mm\u00b2/s") == pytest.approx(
        1e-6, rel=1e-12
    )
    assert domain_units.thermal_diffusivity_to_si(2.5, "m\u00b2/s") == 2.5
    assert domain_units.specific_heat_to_si(1.0, "J/g\u00b7K") == pytest.approx(
        1000.0, rel=1e-12
    )
    assert domain_units.specific_heat_to_si(300.0, "J/(kg\u00b7K)") == 300.0


def test_sample_property_units_are_rejected_rather_than_guessed():
    for converter, unit in (
        (domain_units.density_to_si, "g/mL"),
        (domain_units.thermal_diffusivity_to_si, "cm\u00b2/s"),
        (domain_units.specific_heat_to_si, "kJ/(kg\u00b7K)"),
    ):
        with pytest.raises(ValueError):
            converter(1.0, unit)


def test_lfa_workflow_inline_factors_are_reproduced_by_the_converters():
    """Phase 3 step 3d: presentation/kappa_logic.py previously multiplied these
    factors inline (g/cm\u00b3 \u00d71000, mm\u00b2/s \u00d71e-6, J/g\u00b7K \u00d71000). The
    application converters must reproduce the identical numbers so the golden
    \u03ba values stay unchanged."""
    assert app_conversion.to_base_value(7.31, "g/cm\u00b3", "density") == 7.31 * 1000
    assert app_conversion.to_base_value(
        1.234, "mm\u00b2/s", "thermal_diffusivity"
    ) == 1.234 * 1e-6
    assert app_conversion.to_base_value(
        0.567, "J/g\u00b7K", "specific_heat_capacity"
    ) == 0.567 * 1000


def test_lfa_uncertainty_inline_factors_are_reproduced_by_the_uncertainty_converters():
    """The error mode propagated uncertainties with the same inline factors;
    for linear scale conversions an uncertainty transforms exactly like the
    value."""
    assert app_conversion.uncertainty_to_base(
        1.234, 0.05, "mm\u00b2/s", "thermal_diffusivity"
    ) == 0.05 * 1e-6
    assert app_conversion.uncertainty_to_base(
        0.567, 0.01, "J/g\u00b7K", "specific_heat_capacity"
    ) == 0.01 * 1000
    assert app_conversion.uncertainty_from_base(
        7.31, 12.0, "g/cm\u00b3", "density"
    ) == pytest.approx(12.0 / 1000.0, rel=1e-12)


def test_lfa_end_to_end_kappa_is_unchanged_by_the_converter_delegation():
    """Golden check: \u03ba = \u03b1\u00b7cp\u00b7\u03c1 with SI values converted from the
    dialog's display units must equal the value produced by the retired
    inline multiplication."""
    alpha_mm2s, cp_JgK, density_gcm3 = 0.5, 0.3, 6.0
    si_alpha = app_conversion.to_base_value(
        alpha_mm2s, "mm\u00b2/s", "thermal_diffusivity"
    )
    si_cp = app_conversion.to_base_value(cp_JgK, "J/g\u00b7K", "specific_heat_capacity")
    si_density = app_conversion.to_base_value(density_gcm3, "g/cm\u00b3", "density")
    assert si_alpha * si_cp * si_density == pytest.approx(
        (alpha_mm2s * 1e-6) * (cp_JgK * 1000) * (density_gcm3 * 1000), rel=1e-15
    )
    # and the plain golden number: 0.5e-6 \u00b7 300 \u00b7 6000 = 0.9 W/(m\u00b7K)
    assert si_alpha * si_cp * si_density == pytest.approx(0.9, rel=1e-12)


def test_vector_helpers_support_the_sample_property_quantities():
    densities = np.array([1.0, 5.32, np.nan])
    converted = app_conversion.to_base_values(densities, "g/cm\u00b3", "density")
    np.testing.assert_array_equal(converted[:2], densities[:2] * 1000)
    assert np.isnan(converted[2])


# ─────────────────────────────────────────────────────────────────────────────
# SI prefix quantities and working-unit standardizers (Phase 3 Step C+): the
# hall / SPB / device-efficiency dialogs and the weighted-mobility plot block
# delegate every unit conversion to the application layer.
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("unit", ("V", "mV", "\u00b5V", "\u03bcV", "uV"))
def test_voltage_round_trip_for_every_supported_unit(unit):
    original = 0.12
    base = domain_units.voltage_to_volt(original, unit)
    assert domain_units.voltage_from_volt(base, unit) == pytest.approx(original, rel=1e-12)


@pytest.mark.parametrize("unit", ("m", "cm", "mm", "\u00b5m", "\u03bcm", "um"))
def test_length_round_trip_for_every_supported_unit(unit):
    original = 0.25
    base = domain_units.length_to_meter(original, unit)
    assert domain_units.length_from_meter(base, unit) == pytest.approx(original, rel=1e-12)


@pytest.mark.parametrize("unit", ("A", "mA", "\u00b5A", "\u03bcA", "uA"))
def test_current_round_trip_for_every_supported_unit(unit):
    original = 0.01
    base = domain_units.current_to_ampere(original, unit)
    assert domain_units.current_from_ampere(base, unit) == pytest.approx(original, rel=1e-12)


@pytest.mark.parametrize("unit", ("T", "Tesla", "Tesla (T)", "G", "Gauss", "Gauss (G)"))
def test_magnetic_flux_density_round_trip_for_every_supported_unit(unit):
    original = 0.5
    base = domain_units.magnetic_flux_density_to_tesla(original, unit)
    assert domain_units.magnetic_flux_density_from_tesla(base, unit) == pytest.approx(
        original, rel=1e-12
    )


@pytest.mark.parametrize("unit", ("m\u00b3/C", "cm\u00b3/C"))
def test_hall_coefficient_round_trip_for_every_supported_unit(unit):
    original = 2.5e-3
    base = domain_units.hall_coefficient_to_si(original, unit)
    assert domain_units.hall_coefficient_from_si(base, unit) == pytest.approx(
        original, rel=1e-12
    )


def test_prefix_conversion_factors_are_exact():
    assert domain_units.voltage_to_volt(1.0, "mV") == pytest.approx(1e-3, rel=1e-12)
    assert domain_units.voltage_to_volt(120.0, "\u03bcV") == pytest.approx(1.2e-4, rel=1e-12)
    assert domain_units.length_to_meter(1.0, "mm") == pytest.approx(1e-3, rel=1e-12)
    assert domain_units.length_to_meter(1.0, "\u03bcm") == pytest.approx(1e-6, rel=1e-12)
    assert domain_units.length_to_meter(1.0, "cm") == pytest.approx(1e-2, rel=1e-12)
    assert domain_units.current_to_ampere(10.0, "mA") == pytest.approx(1e-2, rel=1e-12)
    assert domain_units.magnetic_flux_density_to_tesla(
        1.0, "Gauss (G)"
    ) == pytest.approx(1e-4, rel=1e-12)


def test_prefix_units_are_rejected_rather_than_guessed():
    for converter, unit in (
        (domain_units.voltage_to_volt, "kV"),
        (domain_units.length_to_meter, "inch"),
        (domain_units.current_to_ampere, "Ab"),
        (domain_units.magnetic_flux_density_to_tesla, "mT"),
        (domain_units.hall_coefficient_to_si, "mm\u00b3/C"),
    ):
        with pytest.raises(ValueError):
            converter(1.0, unit)


def test_hall_raw_mode_si_chain_matches_the_retired_inline_factors():
    """The raw-mode dialog multiplied SI prefixes inline (mV ×1e-3, mm ×1e-3,
    mA ×1e-3, Gauss ×1e-4). The converter chain must reproduce the identical
    numbers bit-for-bit."""
    vh_mV, t_mm, i_mA, b_G = 0.12, 1.0, 10.0, 1.0
    assert (
        app_conversion.to_base_value(vh_mV, "mV", "voltage"),
        app_conversion.to_base_value(t_mm, "mm", "length"),
        app_conversion.to_base_value(i_mA, "mA", "current"),
        app_conversion.to_base_value(b_G, "Gauss (G)", "magnetic_flux_density"),
    ) == (vh_mV * 1e-3, t_mm * 1e-3, i_mA * 1e-3, b_G * 1e-4)


def test_hall_coefficient_standardization_matches_the_dialog_contract():
    assert app_conversion.hall_coefficient_to_cm3(2.5e-3, "m\u00b3/C") == 2.5e-3 * 1e6
    assert app_conversion.hall_coefficient_to_cm3(1500.0, "cm\u00b3/C") == 1500.0
    # SI direction used by the density workflow (cm³/C -> m³/C)
    assert app_conversion.to_base_value(1500.0, "cm\u00b3/C", "hall_coefficient") == (
        1500.0 * 1e-6
    )


def test_carrier_density_helpers_are_exposed_through_the_application_layer():
    assert app_conversion.carrier_density_m3_to_cm3(1e22) == pytest.approx(1e16, rel=1e-12)
    assert app_conversion.carrier_density_cm3_to_m3(1e16) == pytest.approx(1e22, rel=1e-12)


def test_transport_standardization_to_scm_matches_the_retired_dialog_branches():
    """The hall dialog standardized its transport input to S/cm inline.
    Except for S/m (÷100 vs the retired ×0.01 — ≤1 ulp), every branch must be
    bit-identical; zero resistivity yields NaN as before."""
    assert app_conversion.conductivity_to_scm(250.0, "S/cm") == 250.0
    assert app_conversion.conductivity_to_scm(1.234e5, "S/m") == pytest.approx(
        1.234e5 * 0.01, rel=1e-15
    )
    assert app_conversion.conductivity_to_scm(0.004, "\u03a9\u00b7cm") == 1.0 / 0.004
    assert app_conversion.conductivity_to_scm(4.0, "m\u03a9\u00b7cm") == 1000.0 / 4.0
    assert np.isnan(app_conversion.conductivity_to_scm(0.0, "\u03a9\u00b7cm"))
    assert np.isnan(app_conversion.conductivity_to_scm(0.0, "m\u03a9\u00b7cm"))
    # unknown unit passes through (legacy behaviour)
    assert app_conversion.conductivity_to_scm(7.0, "S/fortnight") == 7.0


def test_seebeck_standardization_to_uvk_matches_the_retired_spb_dialog_branches():
    assert app_conversion.seebeck_to_uvk(150.0, "\u00b5V/K") == 150.0
    assert app_conversion.seebeck_to_uvk(150.0, "\u03bcV/K") == 150.0
    assert app_conversion.seebeck_to_uvk(0.15, "mV/K") == 0.15 * 1e3
    assert app_conversion.seebeck_to_uvk(150e-6, "V/K") == 150e-6 * 1e6
    # unknown unit passes through (legacy behaviour)
    assert app_conversion.seebeck_to_uvk(5.0, "V/fortnight") == 5.0


def test_device_efficiency_and_weighted_mobility_readbacks_match_retired_factors():
    # device_efficiency_dialog table readback (µV/K -> V/K, S/cm -> S/m)
    assert app_conversion.to_base_value(120.0, "uV/K", "seebeck") == 120.0 * 1e-6
    assert app_conversion.to_base_value(850.0, "S/cm", "conductivity") == 850.0 * 100.0
    # main_table_plots weighted-mobility block (S/m -> mΩ·cm, V/K -> µV/K)
    assert convert_resistivity_to_mohm_cm(1.0e4, "S/m") == 1e5 / 1.0e4
    assert app_conversion.from_base_value(120e-6, "uV/K", "seebeck") == 120e-6 * 1e6


def test_uncertainty_linear_rule_covers_the_new_kinds():
    assert app_conversion.uncertainty_to_base(1.0, 0.01, "mV", "voltage") == 0.01 * 1e-3
    assert app_conversion.uncertainty_from_base(1.0, 10.0, "\u00b5V", "voltage") == 10.0 * 1e6
