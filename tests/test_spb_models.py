"""Tests for the single-parabolic-band (SPB) model surface (``seebeck_prime.domain.spb``).

Assertions use mathematical identities and monotonicity properties of the
documented model — plus closed-form degenerate asymptotes — rather than
invented reference data.
"""

from __future__ import annotations

import numpy as np
import pytest

from seebeck_prime.domain.spb import (
    calculate_carrier_concentration,
    calculate_carrier_density_spb,
    calculate_effective_mass,
    estimate_lorenz,
    fermi_integral,
    generate_pisarenko_curve,
    predict_optimal_transport,
    reduced_fermi_level_from_seebeck,
    rigorous_lorenz_number,
    seebeck_from_reduced_fermi_level,
)


def test_fermi_integral_f0_matches_closed_form():
    # F_0(eta) = ln(1 + exp(eta)) exactly (Gamma(1) = 1).
    eta = 3.0
    expected = np.log(1.0 + np.exp(eta))

    assert fermi_integral(0.0, eta) == pytest.approx(expected, rel=1e-9)


def test_fermi_integral_boltzmann_and_sommerfeld_limits():
    # Unnormalized complete FD integral: F_j(eta) = int x^j/(1+exp(x-eta)) dx.
    # Boltzmann branch (eta < -30): F_j = Gamma(j+1) * exp(eta).
    from scipy.special import gamma

    assert fermi_integral(0.5, -40.0) == pytest.approx(gamma(1.5) * np.exp(-40.0), rel=1e-12)
    # Sommerfeld branch (eta > 50): the expansion with its correction terms
    #   F_j = eta^(j+1)/(j+1) + (pi^2/6) j eta^(j-1) + (7 pi^4/360) j(j-1)(j-2) eta^(j-3)
    # The correction terms are mandatory: the Lorenz combination is a
    # near-cancellation and the leading term alone returned L = 0 in the
    # degenerate limit (see docs/SCIENTIFIC_EQUATION_AUDIT.md, issue SE-008).
    j, eta = 0.5, 60.0
    expected = (
        eta ** (j + 1) / (j + 1)
        + (np.pi**2 / 6) * j * eta ** (j - 1)
        + (7 * np.pi**4 / 360) * j * (j - 1) * (j - 2) * eta ** (j - 3)
    )
    assert fermi_integral(j, eta) == pytest.approx(expected, rel=1e-12)


def test_fermi_integral_degenerate_regime_tracks_sommerfeld_asymptote():
    # In the degenerate regime (eta=10, numerical branch) the value is close
    # to eta^(j+1)/(j+1) with small finite-temperature corrections.
    assert fermi_integral(0.5, 10.0) == pytest.approx(10.0 ** 1.5 / 1.5, rel=2e-2)


def test_fermi_integral_is_positive_and_increasing_in_eta():
    values = [fermi_integral(0.5, eta) for eta in (-2.0, 0.0, 2.0, 5.0)]

    assert all(v > 0 for v in values)
    assert values == sorted(values)


def test_seebeck_eta_round_trip():
    for seebeck in (50.0, 150.0, 250.0):
        eta = reduced_fermi_level_from_seebeck(seebeck, 0.0)
        recovered = seebeck_from_reduced_fermi_level(eta, 0.0)

        assert recovered == pytest.approx(seebeck, rel=1e-6)  # numeric inversion tolerance


def test_seebeck_decreases_with_reduced_fermi_level():
    eta = np.linspace(-4.0, 8.0, 25)
    seebeck = [seebeck_from_reduced_fermi_level(e, 0.0) for e in eta]

    assert seebeck == sorted(seebeck, reverse=True)


def test_carrier_density_spb_is_monotonic_in_eta_and_mass():
    n_low_mass = [calculate_carrier_density_spb(e, 1.0, 300.0) for e in (-2.0, 0.0, 4.0)]
    assert n_low_mass == sorted(n_low_mass)

    n_light = calculate_carrier_density_spb(0.0, 1.0, 300.0)
    n_heavy = calculate_carrier_density_spb(0.0, 3.0, 300.0)

    assert n_heavy == pytest.approx(n_light * 3.0 ** 1.5, rel=1e-9)  # n ~ m*^(3/2)


def test_effective_mass_recovers_mass_from_constructed_data():
    # Build (S, n, T) from m* = 1.0, then invert: m* must be recovered.
    temperature = 300.0
    eta = reduced_fermi_level_from_seebeck(150.0, 0.0)
    n_cm3 = calculate_carrier_density_spb(eta, 1.0, temperature)

    m_ratio, eta_recovered = calculate_effective_mass(150.0, n_cm3, temperature)

    assert m_ratio == pytest.approx(1.0, rel=1e-9)
    assert eta_recovered == pytest.approx(eta, rel=1e-9)


def test_pisarenko_curve_sorted_and_seebeck_decreasing_with_density():
    n, seebeck = generate_pisarenko_curve(1.5, 300.0)

    assert n.ndim == 1 and seebeck.ndim == 1
    assert n.size == seebeck.size > 0
    assert list(n) == sorted(n)
    magnitudes = [abs(s) for s in seebeck]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_predict_optimal_transport_structure_and_consistency():
    n_opt, pf_max, eta_opt, n_curve, pf_curve = predict_optimal_transport(
        1.5, 300.0, 100.0
    )

    assert n_opt > 0 and pf_max > 0
    assert -6.0 <= eta_opt <= 10.0
    assert n_curve.shape == pf_curve.shape
    assert pf_max == pytest.approx(pf_curve.max(), rel=1e-12)
    assert n_opt == pytest.approx(n_curve[int(np.argmax(pf_curve))], rel=1e-12)


def test_estimate_lorenz_matches_documented_formula():
    # L = (1.5 + exp(-|S|/116)) * 1e-8
    assert estimate_lorenz(116.0) == pytest.approx((1.5 + np.exp(-1.0)) * 1e-8, rel=1e-12)
    assert estimate_lorenz(0.0) == pytest.approx(2.5e-8, rel=1e-12)


def test_empirical_carrier_concentration_formula():
    # n = 1e21 * exp(-|S|/43.4)
    assert calculate_carrier_concentration(43.4) == pytest.approx(1e21 * np.exp(-1.0), rel=1e-12)
    assert calculate_carrier_concentration(0.0) == pytest.approx(1e21, rel=1e-12)


def test_rigorous_lorenz_is_finite_and_positive():
    value = rigorous_lorenz_number(1.0, 0.5)

    assert np.isfinite(value) and value > 0
