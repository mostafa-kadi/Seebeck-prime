"""Tests for Hall-effect models (``seebeck_prime.domain.hall``).

Expected values come from the documented formulas (R_H = V_H·t/(I·B),
n = 1/(e·|R_H|·r_H), mu_H = |R_H|·sigma) — not from invented reference data.
"""

from __future__ import annotations

import numpy as np
import pytest

from seebeck_prime.domain.hall import (
    calculate_hall_carrier_density,
    calculate_hall_coefficient_from_raw,
    calculate_hall_mobility,
    calculate_hall_mobility_cm2_vs,
    determine_carrier_type,
    fit_scattering_exponent,
)


def test_hall_coefficient_from_raw_matches_formula():
    # R_H = V_H * t / (I * B)
    r_h = calculate_hall_coefficient_from_raw(1e-3, 1e-3, 1e-2, 0.5)

    assert r_h == pytest.approx(1e-3 * 1e-3 / (1e-2 * 0.5), rel=1e-12)


def test_hall_coefficient_keeps_the_sign_of_the_hall_voltage():
    assert calculate_hall_coefficient_from_raw(-1e-3, 1e-3, 1e-2, 0.5) < 0


def test_hall_carrier_density_from_coefficient():
    r_h = 0.001
    n = calculate_hall_carrier_density(r_h, 1.0)

    assert n == pytest.approx(1.0 / (1.602176634e-19 * abs(r_h) * 1.0), rel=1e-6)


def test_hall_carrier_density_follows_documented_hall_concentration_formula():
    # Documented model: n_H = r_H / (e * |R_H|)  (Hall carrier concentration).
    n_full = calculate_hall_carrier_density(0.001, 1.0)
    n_factored = calculate_hall_carrier_density(0.001, 0.85)

    assert n_factored == pytest.approx(n_full * 0.85, rel=1e-9)
    assert n_factored == pytest.approx(0.85 / (1.602176634e-19 * 0.001), rel=1e-6)


def test_hall_mobility_is_abs_rh_times_sigma():
    assert calculate_hall_mobility(0.001, 1e5) == pytest.approx(100.0, rel=1e-12)
    assert calculate_hall_mobility(-0.001, 1e5) == pytest.approx(100.0, rel=1e-12)


def test_hall_mobility_cm2_vs_uses_lab_units():
    assert calculate_hall_mobility_cm2_vs(100.0, 10.0) == pytest.approx(1000.0, rel=1e-12)


def test_carrier_type_from_sign():
    assert determine_carrier_type(1e-4) == "p-type"
    assert determine_carrier_type(-1e-4) == "n-type"
    assert determine_carrier_type(0.0) == "undetermined"


def test_fit_scattering_exponent_recovers_power_law():
    # mu = 4.0 * T^-1.5 -> exponent p = -1.5, prefactor 4.0, perfect fit
    T = np.linspace(200.0, 500.0, 25)
    mu = 4.0 * T ** (-1.5)

    p, mu_0, r2 = fit_scattering_exponent(T, mu)

    assert p == pytest.approx(-1.5, rel=1e-9)
    assert mu_0 == pytest.approx(4.0, rel=1e-9)
    assert r2 == pytest.approx(1.0)


def test_fit_scattering_exponent_needs_two_valid_points():
    p, mu_0, r2 = fit_scattering_exponent([300.0], [100.0])

    assert np.isnan(p) and np.isnan(mu_0) and np.isnan(r2)
