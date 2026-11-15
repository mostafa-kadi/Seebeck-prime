"""Tests for the general analysis utilities in ``seebeck_prime.domain.analysis``.

These cover the temperature-alignment, regression, interpolation, and
outlier-filtering feature set used by the alignment workflows.
"""

from __future__ import annotations

import numpy as np
import pytest

from seebeck_prime.domain.analysis import (
    align_datasets,
    interpolate_onto,
    linear_regression,
    mad_filter,
    round_temperature,
)


# --- MAD outlier filtering ---

def test_mad_filter_keeps_normal_data_and_removes_gross_outlier():
    x = np.array([10.0, 10.1, 9.9, 10.2, 10.0, 10.1, 100.0])

    filtered = mad_filter(x, thresh=3.0)

    assert 100.0 not in filtered
    assert np.allclose(filtered, x[:6])


def test_mad_filter_ignores_non_finite_values():
    x = np.array([1.0, 2.0, np.nan, np.inf, 1.5, 1000.0])

    filtered = mad_filter(x)

    assert np.all(np.isfinite(filtered))
    assert 1000.0 not in filtered


def test_mad_filter_returns_everything_when_mad_is_zero():
    x = np.array([5.0, 5.0, 5.0, 5.0])

    assert np.array_equal(mad_filter(x), x)


def test_mad_filter_empty_array_returns_empty():
    assert mad_filter(np.array([])).size == 0


# --- Linear regression ---

def test_linear_regression_recovers_exact_line():
    x = np.linspace(1.0, 10.0, 10)
    y = 2.0 * x + 1.0

    result = linear_regression(x, y)

    assert result["slope"] == pytest.approx(2.0, rel=1e-9)
    assert result["intercept"] == pytest.approx(1.0, rel=1e-9)
    assert result["r_squared"] == pytest.approx(1.0)
    assert result["n"] == 10


def test_linear_regression_excludes_non_finite_pairs():
    x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
    y = np.array([3.0, 5.0, 9.0, np.inf, 11.0])  # y = 2x + 1 on finite pairs

    result = linear_regression(x, y)

    assert result["n"] == 3
    assert result["slope"] == pytest.approx(2.0, rel=1e-9)


def test_linear_regression_fewer_than_two_points_returns_nan():
    result = linear_regression([1.0], [2.0])

    for key in ("slope", "intercept", "r_squared", "stderr"):
        assert np.isnan(result[key])
    assert result["n"] == 1


# --- Interpolation ---

def test_interpolate_onto_passes_through_source_points():
    source_x = np.array([300.0, 350.0, 400.0])
    source_y = np.array([2.0, 4.0, 6.0])

    interpolated = interpolate_onto(source_x, source_y, np.array([300.0, 350.0, 400.0]))

    assert np.allclose(interpolated, source_y)


def test_interpolate_onto_linear_midpoint():
    value = interpolate_onto(
        np.array([300.0, 400.0]), np.array([2.0, 6.0]), np.array([350.0])
    )

    assert value[0] == pytest.approx(4.0)


def test_interpolate_onto_handles_unsorted_source():
    interpolated = interpolate_onto(
        np.array([400.0, 300.0]), np.array([6.0, 2.0]), np.array([300.0, 350.0, 400.0])
    )

    assert np.allclose(interpolated, [2.0, 4.0, 6.0])


def test_interpolate_onto_clamps_outside_source_range():
    interpolated = interpolate_onto(
        np.array([300.0, 400.0]), np.array([2.0, 6.0]), np.array([100.0, 500.0])
    )

    assert interpolated[0] == pytest.approx(2.0)   # left clamp
    assert interpolated[1] == pytest.approx(6.0)   # right clamp


# --- Temperature rounding / alignment ---

def test_round_temperature_snaps_to_step_multiples():
    T = np.array([297.0, 313.0, 441.0])

    rounded = round_temperature(T, step=20.0)

    assert np.allclose(rounded, [300.0, 320.0, 440.0])


def test_align_datasets_matches_interpolation_of_other_dataset():
    T_ref = np.array([300.0, 320.0, 340.0])
    T_other = np.array([310.0, 330.0])
    y_other = np.array([1.0, 3.0])

    aligned = align_datasets(T_ref, T_other, y_other)

    expected = interpolate_onto(T_other, y_other, T_ref)
    assert np.allclose(aligned, expected)
    assert aligned[0] == pytest.approx(1.0)  # below source range -> clamped to first value
    assert aligned[1] == pytest.approx(2.0)  # midpoint between 1.0 @310 and 3.0 @330
