"""Tests for the phonon / LFA thermal-conductivity feature (``seebeck_prime.domain.phonon``).

Expected values are derived from the documented formulas and unit
conversions — not from invented reference data.
"""

from __future__ import annotations

import numpy as np
import pytest

from seebeck_prime.domain.phonon import (
    dulong_petit_molar,
    dulong_petit_specific,
    kappa_from_diffusivity,
    kappa_from_diffusivity_si,
)
from seebeck_prime.domain.physical_constants import GAS_CONSTANT


def test_dulong_petit_molar_is_three_n_r():
    assert dulong_petit_molar(1) == pytest.approx(3.0 * GAS_CONSTANT, rel=1e-12)
    assert dulong_petit_molar(3) == pytest.approx(9.0 * GAS_CONSTANT, rel=1e-12)


def test_dulong_petit_specific_divides_molar_by_molar_mass_in_kg():
    # specific = 3 n R / (M [g/mol] * 1e-3)  -> J/(kg*K)
    expected = dulong_petit_molar(3) / (100.0 * 1e-3)
    assert dulong_petit_specific(3, 100.0) == pytest.approx(expected, rel=1e-12)


def test_kappa_from_lab_units_matches_si_conversion():
    alpha_mm2s = 1.5      # mm^2/s
    cp_J_gK = 0.20        # J/(g*K)
    rho_g_cm3 = 7.8       # g/cm^3

    lab = kappa_from_diffusivity(alpha_mm2s, cp_J_gK, rho_g_cm3)
    si = kappa_from_diffusivity_si(
        alpha_mm2s * 1e-6,        # mm^2/s -> m^2/s
        cp_J_gK * 1000.0,         # J/(g*K) -> J/(kg*K)
        rho_g_cm3 * 1000.0,       # g/cm^3 -> kg/m^3
    )

    assert lab == pytest.approx(si, rel=1e-12)


def test_kappa_formula_is_product_of_si_inputs():
    value = kappa_from_diffusivity_si(1.0e-6, 500.0, 8000.0)

    assert value == pytest.approx(1.0e-6 * 500.0 * 8000.0, rel=1e-12)


def test_kappa_from_diffusivity_accepts_arrays():
    values = kappa_from_diffusivity(
        np.array([1.0, 2.0]), np.array([0.2, 0.3]), np.array([7.0, 8.0])
    )

    assert values.shape == (2,)
    assert values[0] == pytest.approx(1.0e-6 * 200.0 * 7000.0, rel=1e-12)
    assert values[1] == pytest.approx(2.0e-6 * 300.0 * 8000.0, rel=1e-12)
