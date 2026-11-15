import numpy as np
import pytest

from seebeck_prime.domain.device_efficiency import calculate_efficiencies
from seebeck_prime.domain.transport import (
    calculate_weighted_mobility,
    resistivity_to_mohm_cm,
)


def test_weighted_mobility_reference_value():
    result = calculate_weighted_mobility(300.0, 10.0, 200.0)
    assert result == pytest.approx(45.59401525698672, rel=2e-12)


def test_weighted_mobility_preserves_array_shape_and_zero_resistivity_behavior():
    result = calculate_weighted_mobility(
        np.array([300.0, 300.0]), np.array([10.0, 0.0]), np.array([200.0, 200.0])
    )
    assert result.shape == (2,)
    assert np.isfinite(result[0])
    assert np.isnan(result[1])


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [(1.0, "mΩ·cm", 1.0), (1.0, "Ω·m", 1e5), (1.0, "S/cm", 1000.0), (1.0, "S/m", 1e5)],
)
def test_resistivity_unit_conversion(value, unit, expected):
    assert resistivity_to_mohm_cm(value, unit) == pytest.approx(expected)


def test_device_efficiency_constant_properties_reference_case():
    result = calculate_efficiencies(
        np.array([300.0, 400.0]),
        np.array([200e-6, 200e-6]),
        np.array([1e5, 1e5]),
        np.array([2.0, 2.0]),
        300.0,
        400.0,
    )
    # For constant PF and kappa, ZT varies linearly with T: 0.6 at 300 K
    # and 0.8 at 400 K, so its mean over the interval is 0.7.
    assert result["ZT_avg"] == pytest.approx(0.7)
    # ZT_eng is the engineering figure of merit (Snyder):
    #   ZT_eng = S_avg^2 * T_avg / (rho_avg * kappa_avg)
    # For constant properties this must equal the material ZT at the mean
    # temperature T_avg = (Tc+Th)/2 = 350 K, i.e. 0.7.
    # The pre-audit implementation returned 5e-4 (not dimensionless: the
    # expression carried units of 1/K) - see docs/SCIENTIFIC_EQUATION_AUDIT.md,
    # issue SE-001.
    assert result["ZT_eng"] == pytest.approx(0.7)
    assert result["Carnot"] == pytest.approx(0.25)
    # With constant properties the engineering and maximum efficiencies must
    # coincide (both are the constant-property Ioffe result).
    assert result["Efficiency_Eng"] == pytest.approx(result["Efficiency_Max"])
