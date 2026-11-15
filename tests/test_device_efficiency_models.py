"""Tests for the device-efficiency model (``seebeck_prime.domain.device_efficiency``).

Assertions use thermodynamic identities (Carnot = ΔT/Th, η_max < Carnot,
ZT_avg from constant properties) and the committed golden-baseline case —
not invented reference data.
"""

from __future__ import annotations

import numpy as np
import pytest

from seebeck_prime.domain.device_efficiency import calculate_efficiencies


def _constant_properties_case(tc=300.0, th=500.0):
    return calculate_efficiencies(
        np.array([300.0, 400.0]),
        np.array([200e-6, 200e-6]),
        np.array([1e5, 1e5]),
        np.array([2.0, 2.0]),
        tc,
        th,
    )


def test_matches_golden_baseline_reference_case():
    result = _constant_properties_case()

    assert result["Carnot"] == pytest.approx(0.4, rel=1e-12)
    assert result["ZT_avg"] == pytest.approx(0.8000000000000002, rel=1e-12)
    assert result["Efficiency_Max"] == pytest.approx(0.07038187266672276, rel=1e-12)


def test_carnot_and_delta_t_identities():
    result = _constant_properties_case(tc=300.0, th=600.0)

    assert result["DeltaT"] == pytest.approx(300.0, rel=1e-12)
    assert result["Carnot"] == pytest.approx(300.0 / 600.0, rel=1e-12)


def test_zt_avg_equals_material_zt_for_constant_properties():
    # ZT = S^2 * sigma * T / kappa; with constant properties the Simpson
    # average over [Tc, Th] reproduces ZT at the midpoint temperature.
    result = _constant_properties_case(tc=300.0, th=500.0)

    zt = (200e-6 ** 2) * 1e5 * 400.0 / 2.0
    assert result["ZT_avg"] == pytest.approx(zt, rel=1e-12)


def test_max_efficiency_is_below_carnot():
    result = _constant_properties_case()

    assert 0.0 < result["Efficiency_Max"] < result["Carnot"]


def test_constant_properties_reproduce_eta_max_formula():
    result = _constant_properties_case(tc=300.0, th=500.0)

    zt_avg = result["ZT_avg"]
    carnot = result["Carnot"]
    factor = np.sqrt(1.0 + zt_avg)
    expected = carnot * (factor - 1.0) / (factor + 300.0 / 500.0)
    assert result["Efficiency_Max"] == pytest.approx(expected, rel=1e-12)


def test_returns_none_for_zero_or_negative_delta_t():
    assert calculate_efficiencies(
        np.array([300.0, 400.0]),
        np.array([200e-6, 200e-6]),
        np.array([1e5, 1e5]),
        np.array([2.0, 2.0]),
        400.0,
        400.0,
    ) is None
    assert calculate_efficiencies(
        np.array([300.0, 400.0]),
        np.array([200e-6, 200e-6]),
        np.array([1e5, 1e5]),
        np.array([2.0, 2.0]),
        500.0,
        300.0,
    ) is None


def test_returns_none_for_fewer_than_two_points():
    assert calculate_efficiencies(
        np.array([300.0]),
        np.array([200e-6]),
        np.array([1e5]),
        np.array([2.0]),
        300.0,
        500.0,
    ) is None


def test_interpolates_endpoints_when_data_lies_outside_the_operating_range():
    # Measurement grid 200-250 K lies entirely outside [300, 500]; the
    # interpolation branch must build the range from endpoint interpolation.
    result = calculate_efficiencies(
        np.array([200.0, 250.0]),
        np.array([100e-6, 150e-6]),
        np.array([1e5, 1e5]),
        np.array([2.0, 2.0]),
        300.0,
        500.0,
    )

    assert result is not None
    assert result["DeltaT"] == pytest.approx(200.0, rel=1e-12)
    assert np.isfinite(result["Efficiency_Max"])


def test_higher_zt_material_gives_higher_efficiency():
    weaker = _constant_properties_case()
    stronger = calculate_efficiencies(
        np.array([300.0, 400.0]),
        np.array([400e-6, 400e-6]),   # doubled Seebeck -> 4x PF/ZT
        np.array([1e5, 1e5]),
        np.array([2.0, 2.0]),
        300.0,
        500.0,
    )

    assert stronger["Efficiency_Max"] > weaker["Efficiency_Max"]
    assert stronger["ZT_avg"] == pytest.approx(weaker["ZT_avg"] * 4.0, rel=1e-9)
