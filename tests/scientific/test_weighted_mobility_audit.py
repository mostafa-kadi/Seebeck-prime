"""Scientific regression tests for Snyder et al. weighted mobility.

The reference expression is transcribed independently from the publisher's
2020 paper (DOI: 10.1002/adma.202001537). These tests verify implementation
parity and numerical robustness; they do not substitute for experimental
validation against a specimen with independently reported mobility data.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from seebeck_prime.domain.transport import calculate_weighted_mobility  # noqa: E402

# CODATA-derived k_B/e expressed in µV/K. The paper rounds this to 86.3.
K_B_OVER_E_UV_K = 86.17333262145


def _published_reference(temperature_k: float, resistivity_mohm_cm: float,
                         seebeck_uv_k: float) -> float:
    """Independent scalar transcription of Snyder et al. (2020), Eq. 1."""
    s = abs(seebeck_uv_k) / K_B_OVER_E_UV_K
    first = math.exp(s - 2.0) / (1.0 + math.exp(-5.0 * (s - 1.0)))
    second = ((3.0 / math.pi**2) * s) / (
        1.0 + math.exp(5.0 * (s - 1.0))
    )
    return (
        331.0
        * (1.0 / resistivity_mohm_cm)
        * (temperature_k / 300.0) ** (-1.5)
        * (first + second)
    )


@pytest.mark.parametrize("seebeck", [50.0, 100.0, 150.0, 200.0, 250.0])
def test_matches_published_snyder_expression_across_seebeck_range(seebeck):
    actual = float(calculate_weighted_mobility(300.0, 1.0, seebeck))
    expected = _published_reference(300.0, 1.0, seebeck)
    assert actual == pytest.approx(expected, rel=2e-12)


@pytest.mark.parametrize("seebeck", [50.0, 100.0, 150.0, 200.0, 250.0])
def test_seebeck_sign_does_not_change_weighted_mobility(seebeck):
    positive = calculate_weighted_mobility(300.0, 1.0, seebeck)
    negative = calculate_weighted_mobility(300.0, 1.0, -seebeck)
    assert positive == pytest.approx(negative, rel=1e-13)


def test_resistivity_scaling_is_inverse():
    base = calculate_weighted_mobility(300.0, 1.0, 150.0)
    doubled = calculate_weighted_mobility(300.0, 2.0, 150.0)
    assert doubled == pytest.approx(base / 2.0, rel=1e-13)


def test_temperature_scaling_is_acoustic_phonon_t_to_minus_three_halves():
    base = calculate_weighted_mobility(300.0, 1.0, 150.0)
    for factor in (0.5, 2.0):
        scaled = calculate_weighted_mobility(300.0 * factor, 1.0, 150.0)
        assert scaled == pytest.approx(base * factor ** (-1.5), rel=1e-13)


def test_zero_seebeck_is_finite_and_does_not_diverge():
    actual = calculate_weighted_mobility(300.0, 1.0, 0.0)
    expected = _published_reference(300.0, 1.0, 0.0)
    assert np.isfinite(actual)
    assert actual == pytest.approx(expected, rel=1e-13)


def test_inputs_broadcast_and_preserve_array_shape():
    actual = calculate_weighted_mobility(
        np.array([300.0, 600.0]), 1.0, np.array([100.0, 200.0])
    )
    expected = np.array([
        _published_reference(300.0, 1.0, 100.0),
        _published_reference(600.0, 1.0, 200.0),
    ])
    np.testing.assert_allclose(actual, expected, rtol=2e-12)


@pytest.mark.parametrize(
    "temperature,resistivity,seebeck",
    [
        (0.0, 1.0, 150.0),
        (-1.0, 1.0, 150.0),
        (300.0, 0.0, 150.0),
        (300.0, -1.0, 150.0),
        (np.nan, 1.0, 150.0),
        (300.0, np.inf, 150.0),
        (300.0, 1.0, np.nan),
    ],
)
def test_invalid_or_non_finite_inputs_return_nan(temperature, resistivity, seebeck):
    assert np.isnan(calculate_weighted_mobility(temperature, resistivity, seebeck))


def test_non_finite_array_elements_are_marked_nan_without_invalidating_valid_rows():
    actual = calculate_weighted_mobility(
        np.array([300.0, 0.0, 600.0]),
        np.array([1.0, 1.0, 2.0]),
        np.array([150.0, 150.0, np.nan]),
    )
    assert np.isfinite(actual[0])
    assert np.isnan(actual[1])
    assert np.isnan(actual[2])


def test_weighted_mobility_is_not_hall_mobility():
    from seebeck_prime.domain.hall import calculate_hall_mobility

    mu_w = float(calculate_weighted_mobility(300.0, 1.0, 150.0))
    mu_h_si = float(calculate_hall_mobility(1.0e-4, 1.0e5))
    mu_h_cm2 = mu_h_si * 1e4
    assert mu_w != pytest.approx(mu_h_cm2, rel=1e-3)
    assert mu_w > 0.0 and mu_h_cm2 > 0.0
