"""Phase 3.5 - the weighted-mobility audit, characterised as tests.

The weighted mobility has **no experimental reference** (the only published
carrier-mobility curve in the benchmark set is negative and unusable), so
these tests cannot validate the physics. What they do is

* pin the **unit convention** and the **scaling laws**, so that a future
  change to the model is a deliberate, visible act;
* **characterise** the two open findings from
  ``validation/remediation/WEIGHTED_MOBILITY_AUDIT.md``:
  - the divergence of the shape factor for small |S|;
  - the difference between the implemented expression and the one that an
    earlier revision of the scientific model register printed.

They are deliberately written so that they FAIL if somebody changes the
physics silently, and so that the failure message says what to do.
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

from seebeck_prime.domain.physical_constants import (  # noqa: E402
    BOLTZMANN,
    ELECTRON_CHARGE,
    ELECTRON_MASS,
    PLANCK,
)
from seebeck_prime.domain.transport import calculate_weighted_mobility  # noqa: E402

K_B_OVER_E = BOLTZMANN / ELECTRON_CHARGE


# =====================================================================
# The unit convention
# =====================================================================

def test_the_unit_convention_is_the_documented_one():
    """rho [mOhm.cm], |S| [uV/K], T [K] -> mu_w [cm^2/(V.s)].

    The convention is pinned by an explicit hand-computed value, not by a
    round trip, so that a change of units in either direction is detected.
    """
    value = float(calculate_weighted_mobility(300.0, 1.0, -150.0))

    s = 150.0 / (K_B_OVER_E * 1e6)
    term1 = math.exp(s - 2.0) / (1.0 + math.exp(-5.0 * (s - 1.0)))
    # the +1e-9 is the implementation's divide-by-zero guard and is part of
    # the expression being characterised
    term2 = (3.0 * math.pi**2 / (s + 1e-9)) / (1.0 + math.exp(5.0 * (s - 1.0)))
    expected = 331.0 * 1.0 * 1.0 * (term1 + term2)

    assert value == pytest.approx(expected, rel=1e-12)


def test_the_input_scale_is_resistivity_in_mohm_cm():
    """Doubling rho in mOhm.cm must halve the mobility."""
    base = float(calculate_weighted_mobility(300.0, 1.0, -150.0))
    doubled = float(calculate_weighted_mobility(300.0, 2.0, -150.0))
    assert doubled == pytest.approx(base / 2.0, rel=1e-12)


def test_the_input_scale_is_seebeck_in_microvolt_per_kelvin():
    """A Seebeck coefficient given in uV/K must use the uV/K scale."""
    value_uvk = float(calculate_weighted_mobility(300.0, 1.0, -150.0))
    # the same physical coefficient expressed in V/K
    value_vk = float(calculate_weighted_mobility(300.0, 1.0, -150e-6))
    assert value_vk != pytest.approx(value_uvk, rel=1e-6)
    assert value_uvk == pytest.approx(
        float(calculate_weighted_mobility(300.0, 1.0, -150.0)), rel=1e-15
    )


def test_the_temperature_law_is_the_assumed_acoustic_one():
    """mu_w ~ T^(-3/2)."""
    base = float(calculate_weighted_mobility(300.0, 1.0, -150.0))
    for factor in (0.5, 2.0):
        scaled = float(calculate_weighted_mobility(300.0 * factor, 1.0, -150.0))
        assert scaled == pytest.approx(base * factor ** (-1.5), rel=1e-12)


# =====================================================================
# It is not the Hall mobility
# =====================================================================

def test_the_weighted_mobility_is_not_the_hall_mobility():
    """mu_w and mu_H are different physical quantities."""
    from seebeck_prime.domain.hall import calculate_hall_mobility

    mu_w = float(calculate_weighted_mobility(300.0, 1.0, -150.0))
    mu_h_si = float(calculate_hall_mobility(1.0e-4, 1.0e5))       # m^2/(V.s)
    mu_h_cm2 = mu_h_si * 1e4

    assert mu_w != pytest.approx(mu_h_cm2, rel=1e-3)
    assert mu_w > 0.0 and mu_h_cm2 > 0.0


def test_zero_resistivity_yields_not_a_number():
    assert np.isnan(float(calculate_weighted_mobility(300.0, 0.0, -150.0)))


# =====================================================================
# Finding 1: the divergence for small |S|
# =====================================================================

def test_the_shape_factor_diverges_for_small_seebeck_coefficients():
    """CHARACTERISATION of an open finding, not an endorsement.

    The implemented shape factor contains a 3*pi^2/s term, so mu_w grows
    without bound as |S| -> 0 and reaches ~1e13 cm^2/(V.s) at S = 0, which
    is four to ten orders of magnitude above any physical mobility
    (1-1000 cm^2/(V.s)). Whether the expression should be regularised there
    is a physics question that needs the primary source; this test exists
    so that a change to the behaviour is a deliberate, visible act.
    """
    at_zero = float(calculate_weighted_mobility(300.0, 1.0, 0.0))
    at_small = float(calculate_weighted_mobility(300.0, 1.0, -1.0))     # 1 uV/K
    at_typical = float(calculate_weighted_mobility(300.0, 1.0, -150.0))

    assert at_zero > 1e12
    assert at_small > at_typical
    assert at_zero > at_small

    # the value at a typical Seebeck coefficient is physically plausible
    assert 100.0 < at_typical < 1000.0


# =====================================================================
# Finding 2: the difference from the previously-registered expression
# =====================================================================

def _register_bracket(s: float) -> float:
    return (
        math.exp(s - 2.0) / (1.0 + math.exp(-5.0 * (s - 1.0)))
        + (3.0 / math.pi**2) * s
    )


def _register_mu_w(sigma_s_m: float, temperature_k: float, seebeck_v_k: float) -> float:
    """The expression an earlier revision of the model register printed."""
    s = abs(seebeck_v_k) / K_B_OVER_E
    prefactor = (
        3.0 * PLANCK**3 * sigma_s_m
        / (
            8.0 * math.pi * ELECTRON_CHARGE
            * (2.0 * ELECTRON_MASS * BOLTZMANN * temperature_k) ** 1.5
        )
    )
    return prefactor / _register_bracket(s)


def test_the_implementation_differs_from_the_previously_registered_expression():
    """CHARACTERISATION of an open finding.

    The scientific model register previously printed an expression that the
    implementation does not evaluate; the two differ by a factor of 1.5 to
    8.2 over a representative grid. The register has been corrected to
    describe the implementation, and the implementation was NOT changed,
    because the primary source and an experimental reference are both
    unavailable.

    If this test fails, the model's physics has changed: the register, the
    limitations report and validation/remediation/WEIGHTED_MOBILITY_AUDIT.md
    must then be updated in the same change.
    """
    ratios = []
    for temperature in (300.0, 600.0, 900.0):
        for rho_mohm_cm in (0.5, 1.0, 2.0):
            for seebeck in (-250e-6, -150e-6, -80e-6):
                sigma_s_m = 1.0 / (rho_mohm_cm * 1e-5)
                register = _register_mu_w(sigma_s_m, temperature, seebeck) * 1e4
                implemented = float(
                    calculate_weighted_mobility(temperature, rho_mohm_cm, seebeck * 1e6)
                )
                ratios.append(implemented / register)

    assert min(ratios) == pytest.approx(1.4915, rel=1e-3)
    assert max(ratios) == pytest.approx(8.2452, rel=1e-3)
    # the ratio is a function of |S| alone, not of T or rho
    assert all(r == pytest.approx(ratios[0], rel=1e-9) for r in ratios[0::3])
