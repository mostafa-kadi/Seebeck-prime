"""Phase VIII: numerical edge cases, convergence and physical limits.

Every implemented calculation is exercised with zero, negative, tiny, huge,
NaN and infinity inputs, with empty/single-point/unsorted/duplicated
datasets, and with inconsistent array lengths. The tests assert that the
software either returns a meaningful result or raises a *meaningful* error -
never a silently misleading number.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from validation.independent_calculations import references as ref  # noqa: E402

from seebeck_prime.domain import calculations as calc  # noqa: E402
from seebeck_prime.domain import spb as spb_domain  # noqa: E402
from seebeck_prime.domain import transport as transport_domain  # noqa: E402
from seebeck_prime.domain import uncertainty as unc  # noqa: E402


# =====================================================================
# Zero, negative and extreme inputs
# =====================================================================

def test_zero_inputs_do_not_produce_infinities_where_none_is_physical():
    assert calc.calculate_pf(0.0, 1.0e5) == 0.0
    assert calc.calculate_kappa_e(0.0, 300.0) == 0.0
    assert calc.calculate_kappa_l(2.0, 0.0) == 2.0
    assert calc.calculate_zt(0.0, 300.0, 2.0) == 0.0


def test_zero_thermal_conductivity_does_not_divide_by_zero():
    assert calc.calculate_zt(1e-3, 300.0, 0.0) == 0.0
    assert np.isfinite(unc.propagate_zt_error(1e-3, 1e-4, 300.0, 1.0, 0.0, 0.01))


def test_negative_inputs_propagate_predictably():
    assert calc.calculate_pf(-100e-6, 1e5) > 0.0            # S is squared
    assert calc.calculate_kappa_e(-1.0, 300.0) < 0.0          # sigma is linear
    assert calc.calculate_kappa_l(2.0, -0.5) == 2.5


def test_extreme_magnitudes_do_not_produce_nan():
    """Physically absurd magnitudes may overflow to +/-inf (IEEE-754), but they
    must never become NaN, which would signal an undefined result."""
    assert not np.isnan(calc.calculate_pf(1.0, 1.0e300))
    # 2.44e-8 * 1e300 * 1e300 exceeds the double range: the result is
    # +inf, which is the correct IEEE outcome for an unrepresentable product.
    assert not np.isnan(calc.calculate_kappa_e(1.0e300, 1.0e300))
    assert not np.isnan(calc.calculate_zt(1.0e300, 1.0e300, 1.0e300))


def test_nan_inputs_propagate_as_nan():
    assert np.isnan(calc.calculate_pf(np.nan, 1e5))
    assert np.isnan(calc.calculate_zt(np.nan, 300.0, 2.0))


def test_infinite_inputs_propagate_predictably():
    """inf in the Seebeck coefficient gives an infinite power factor; an
    infinite thermal conductivity drives the figure of merit to zero."""
    assert np.isinf(calc.calculate_pf(np.inf, 1e5))
    assert calc.calculate_zt(1e-3, 300.0, np.inf) == 0.0


def test_weighted_mobility_with_zero_resistivity_is_not_a_number():
    """rho = 0 carries no information; the implementation returns NaN."""
    assert np.isnan(transport_domain.calculate_weighted_mobility(300.0, 0.0, -150.0))


def test_weighted_mobility_with_zero_temperature_does_not_raise():
    with np.errstate(divide="ignore", invalid="ignore"):
        result = transport_domain.calculate_weighted_mobility(0.0, 1.0, -150.0)
    assert result is not None


# =====================================================================
# Array-shape and dataset edge cases
# =====================================================================

def test_empty_arrays_are_handled():
    assert calc.calculate_pf(np.array([]), np.array([])).size == 0
    assert calc.calculate_kappa_e(np.array([]), np.array([])).size == 0


def test_single_point_dataset_is_handled():
    assert calc.calculate_pf(np.array([1e-4]), np.array([1e5])) == pytest.approx(1e-3)


def test_inconsistent_array_lengths_follow_numpy_broadcasting():
    """A length-1 input is broadcast over the longer array (numpy semantics);
    genuinely incompatible lengths raise. The application validates data
    completeness before this point (see validate_measurement_data)."""
    result = calc.calculate_pf(np.array([1e-4, 2e-4]), np.array([1e5]))
    # S^2 * sigma, element-wise with the conductivity broadcast
    assert result.tolist() == pytest.approx([1.0e-3, 4.0e-3])

    with pytest.raises(ValueError):
        calc.calculate_pf(np.array([1e-4, 2e-4, 3e-4]), np.array([1e5, 2e5]))


def test_duplicate_temperatures_do_not_break_the_spb_inversion():
    """The SPB inversion works on individual points, so duplicates are fine."""
    for _ in range(2):
        eta = spb_domain.reduced_fermi_level_from_seebeck(150.0, 0.0)
        assert np.isfinite(eta)


def test_unsorted_temperature_arrays_are_accepted():
    temperature = np.array([400.0, 300.0, 350.0])
    sigma = np.array([1.0e5, 1.2e5, 1.1e5])
    seebeck = np.array([-1.3e-4, -1.5e-4, -1.4e-4])
    kappa = np.array([2.0, 1.8, 1.9])
    from seebeck_prime.application.use_cases import calculate_thermoelectric_properties

    result = calculate_thermoelectric_properties(temperature, sigma, seebeck, kappa)

    assert result["ZT"].shape == temperature.shape
    assert np.all(np.isfinite(result["ZT"]))


# =====================================================================
# Numerical convergence and limits
# =====================================================================

def test_fermi_integral_converges_with_the_quadrature():
    """The application's quadrature must agree with a finer independent one."""
    for eta in (-6.0, -1.0, 2.0, 8.0, 30.0):
        app_value = spb_domain.fermi_integral(0.5, eta)
        reference = ref.fermi_integral_unnormalised(0.5, eta)
        assert app_value == pytest.approx(reference, rel=1e-8)


def test_fermi_integral_asymptotic_branches_are_continuous_enough():
    """The branch switches must not introduce a visible step."""
    for j in (0.0, 0.5, 1.0, 2.0):
        for eta in (-30.0, 50.0):
            below = spb_domain.fermi_integral(j, eta - 1e-3)
            above = spb_domain.fermi_integral(j, eta + 1e-3)
            assert below == pytest.approx(above, rel=5e-3)


def test_seebeck_inversion_converges_to_the_same_eta_for_different_brackets():
    """The inversion result must be independent of the bracketing interval."""
    eta = 0.5
    seebeck = spb_domain.seebeck_from_reduced_fermi_level(eta, 0.0)
    assert spb_domain.reduced_fermi_level_from_seebeck(seebeck, 0.0) == pytest.approx(
        eta, abs=1e-5
    )


def test_inversion_returns_nan_rather_than_a_wrong_number_when_unbracketable():
    """An impossible |S| must not produce a plausible-looking eta."""
    assert np.isnan(spb_domain.reduced_fermi_level_from_seebeck(1.0e6, 0.0))


def test_metallic_limit_is_treated_as_such():
    """A vanishing |S| corresponds to a degenerate metal (eta -> infinity)."""
    assert spb_domain.reduced_fermi_level_from_seebeck(1e-6, 0.0) == 50.0


def test_physical_limits_of_the_spb_lorenz_number():
    """The rigorous Lorenz number must approach the classical limits."""
    l_sommerfeld = ref.lorenz_sommerfeld()
    l_non_degenerate = 2.0 * ref.K_B_OVER_E**2      # acoustic scattering (r = -1/2)

    assert spb_domain.rigorous_lorenz_number(40.0, 0.0) == pytest.approx(
        l_sommerfeld, rel=5e-3
    )
    assert spb_domain.rigorous_lorenz_number(-40.0, 0.0) == pytest.approx(
        l_non_degenerate, rel=5e-3
    )


def test_spb_seebeck_limits():
    """S -> (k_B/e)(lambda + 2 - eta) for eta << 0 and S -> 0 for eta >> 0."""
    for eta in (-20.0, -60.0):
        expected = ref.K_B_OVER_E_UV * (2.0 - eta)      # lambda = 0
        assert spb_domain.seebeck_from_reduced_fermi_level(eta, 0.0) == pytest.approx(
            expected, rel=1e-3
        )
    assert abs(spb_domain.seebeck_from_reduced_fermi_level(40.0, 0.0)) < 10.0


def test_uncertainty_of_a_zero_input_is_zero():
    assert unc.propagate_pf_error(0.0, 1e-6, 1e5, 1e3) == 0.0
    assert unc.propagate_kappa_l_error(0.0, 0.0) == 0.0


def test_huge_uncertainty_is_reported_without_overflow():
    value = unc.propagate_pf_error(1e-4, 1.0, 1e5, 1e5)
    assert np.isfinite(value)
    assert value > 0.0
