"""Tests for the Arrhenius analysis feature (``seebeck_prime.plugins.arrhenius``).

Activation energies are recovered from synthetic data constructed from the
documented models, so expected values are exact by construction.
"""

from __future__ import annotations

import numpy as np
import pytest

from seebeck_prime.domain.physical_constants import BOLTZMANN, ELECTRON_CHARGE, GAS_CONSTANT
from seebeck_prime.plugins.arrhenius import (
    arrhenius_ln_sigma,
    arrhenius_ln_sigma_T,
    arrhenius_log10_sigma,
)


def _synthetic_arrhenius_data(e_a_ev=0.5, sigma_0=1e4):
    """sigma(T) = sigma_0 * exp(-Ea / (kB T)) over a 300-500 K grid."""
    T = np.linspace(300.0, 500.0, 21)
    e_a_j = e_a_ev * ELECTRON_CHARGE
    sigma = sigma_0 * np.exp(-e_a_j / (BOLTZMANN * T))
    return T, sigma


def _synthetic_polaronic_data(e_a_ev=0.4, a_const=5e6):
    """Small-polaron model: sigma(T) = A/T * exp(-Ea / (kB T))."""
    T = np.linspace(300.0, 500.0, 21)
    e_a_j = e_a_ev * ELECTRON_CHARGE
    sigma = a_const / T * np.exp(-e_a_j / (BOLTZMANN * T))
    return T, sigma


def test_arrhenius_ln_sigma_recovers_activation_energy():
    T, sigma = _synthetic_arrhenius_data(e_a_ev=0.5, sigma_0=1e4)

    result = arrhenius_ln_sigma(T, sigma)

    assert result["E_a_eV"] == pytest.approx(0.5, rel=1e-9)
    assert result["E_a_J_per_mol"] == pytest.approx(0.5 * ELECTRON_CHARGE * 6.02214076e23, rel=1e-6)
    assert result["sigma_0"] == pytest.approx(1e4, rel=1e-9)
    assert result["r_squared"] == pytest.approx(1.0)
    assert result["model"] == "ln(sigma) vs 1/T"


def test_arrhenius_activation_energy_units_consistency():
    T, sigma = _synthetic_arrhenius_data(e_a_ev=0.3)

    result = arrhenius_ln_sigma(T, sigma)

    # E_a [J/mol] = E_a [eV] * e * N_A ; N_A * e = F (Faraday) ~ 96485 C/mol.
    assert result["E_a_J_per_mol"] == pytest.approx(
        result["E_a_eV"] * 96485.3321233100184, rel=1e-6
    )
    # Alternative identity via the gas constant and the slope in kelvin units:
    assert result["E_a_J_per_mol"] == pytest.approx(
        -result["slope"] * GAS_CONSTANT, rel=1e-9
    )


def test_log10_variant_recovers_same_activation_energy():
    T, sigma = _synthetic_arrhenius_data(e_a_ev=0.5)

    ln_result = arrhenius_ln_sigma(T, sigma)
    log10_result = arrhenius_log10_sigma(T, sigma)

    assert log10_result["E_a_eV"] == pytest.approx(ln_result["E_a_eV"], rel=1e-9)
    assert log10_result["sigma_0"] == pytest.approx(1e4, rel=1e-9)
    assert log10_result["log_type"] == "log10"


def test_polaronic_variant_recovers_activation_energy():
    T, sigma = _synthetic_polaronic_data(e_a_ev=0.4, a_const=5e6)

    result = arrhenius_ln_sigma_T(T, sigma)

    assert result["E_a_eV"] == pytest.approx(0.4, rel=1e-9)
    assert result["sigma_0"] == pytest.approx(5e6, rel=1e-9)  # A from sigma*T = A exp(...)
    assert result["model"] == "ln(sigma*T) vs 1/T"


def test_invalid_rows_are_masked_out():
    T, sigma = _synthetic_arrhenius_data()
    T = np.append(T, [0.0, -10.0])          # invalid temperatures
    sigma = np.append(sigma, [0.0, 1.0])    # invalid conductivity

    result = arrhenius_ln_sigma(T, sigma)

    assert result["n"] == 21
    assert result["E_a_eV"] == pytest.approx(0.5, rel=1e-9)
