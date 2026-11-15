import pytest
import numpy as np
import pandas as pd
from seebeck_prime.domain.calculations import (
    calculate_pf,
    calculate_kappa_e,
    calculate_kappa_l,
    calculate_zt,
    estimate_lorenz,
    calculate_molecular_weight,
    calculate_legacy_molecular_weight,
    calculate_dulong_petit_limit,
)
from seebeck_prime.domain.physical_constants import (
    ATOMIC_WEIGHTS,
    DEFAULT_LORENZ,
    LEGACY_GAS_CONSTANT,
)


# --- Fixtures for common test data ---
@pytest.fixture
def sample_data_scalar():
    return {
        "seebeck": 100e-6,  # V/K
        "conductivity": 1e5,  # S/m
        "temperature": 300,  # K
        "kappa_total": 2.0,  # W/(mK)
    }


@pytest.fixture
def sample_data_array():
    return {
        "seebeck": np.array([100e-6, 50e-6]),
        "conductivity": np.array([1e5, 0.5e5]),
        "temperature": np.array([300, 400]),
        "kappa_total": np.array([2.0, 1.5]),
    }


# --- Test calculate_pf ---
def test_calculate_pf_scalar(sample_data_scalar):
    s = sample_data_scalar["seebeck"]
    sigma = sample_data_scalar["conductivity"]
    expected_pf = (s**2) * sigma
    assert calculate_pf(s, sigma) == pytest.approx(expected_pf)


def test_calculate_pf_array(sample_data_array):
    s = sample_data_array["seebeck"]
    sigma = sample_data_array["conductivity"]
    expected_pf = (s**2) * sigma
    assert np.allclose(calculate_pf(s, sigma), expected_pf)


def test_calculate_pf_zero_inputs():
    assert calculate_pf(0, 100) == 0
    assert calculate_pf(100, 0) == 0
    assert calculate_pf(0, 0) == 0


def test_calculate_pf_negative_seebeck():
    assert calculate_pf(-100e-6, 1e5) == pytest.approx(((-100e-6) ** 2) * 1e5)


# --- Test calculate_kappa_e ---
def test_calculate_kappa_e_scalar(sample_data_scalar):
    sigma = sample_data_scalar["conductivity"]
    temp = sample_data_scalar["temperature"]
    expected_kappa_e = DEFAULT_LORENZ * sigma * temp
    assert calculate_kappa_e(sigma, temp) == pytest.approx(expected_kappa_e)


def test_calculate_kappa_e_array(sample_data_array):
    sigma = sample_data_array["conductivity"]
    temp = sample_data_array["temperature"]
    expected_kappa_e = DEFAULT_LORENZ * sigma * temp
    assert np.allclose(calculate_kappa_e(sigma, temp), expected_kappa_e)


def test_calculate_kappa_e_custom_lorenz():
    assert calculate_kappa_e(1e5, 300, lorenz=2.0e-8) == pytest.approx(
        2.0e-8 * 1e5 * 300
    )


def test_calculate_kappa_e_zero_inputs():
    assert calculate_kappa_e(0, 300) == 0
    assert calculate_kappa_e(1e5, 0) == 0
    assert calculate_kappa_e(0, 0) == 0


# --- Test calculate_kappa_l ---
def test_calculate_kappa_l_scalar():
    assert calculate_kappa_l(2.0, 0.5) == pytest.approx(1.5)


def test_calculate_kappa_l_array():
    assert np.allclose(
        calculate_kappa_l(np.array([2.0, 1.5]), np.array([0.5, 0.3])),
        np.array([1.5, 1.2]),
    )


def test_calculate_kappa_l_zero_inputs():
    assert calculate_kappa_l(0, 0) == 0
    assert calculate_kappa_l(1.0, 1.0) == 0


def test_calculate_kappa_l_negative_result():
    assert calculate_kappa_l(0.5, 2.0) == pytest.approx(-1.5)


# --- Test calculate_zt ---
def test_calculate_zt_scalar(sample_data_scalar):
    pf = calculate_pf(sample_data_scalar["seebeck"], sample_data_scalar["conductivity"])
    temp = sample_data_scalar["temperature"]
    kappa = sample_data_scalar["kappa_total"]
    expected_zt = (pf * temp) / kappa
    assert calculate_zt(pf, temp, kappa) == pytest.approx(expected_zt)


def test_calculate_zt_array(sample_data_array):
    pf = calculate_pf(sample_data_array["seebeck"], sample_data_array["conductivity"])
    temp = sample_data_array["temperature"]
    kappa = sample_data_array["kappa_total"]
    expected_zt = (pf * temp) / kappa
    assert np.allclose(calculate_zt(pf, temp, kappa), expected_zt)


def test_calculate_zt_kappa_zero():
    assert calculate_zt(1.0, 300, 0) == 0.0
    assert np.allclose(
        calculate_zt(np.array([1.0, 1.0]), np.array([300, 300]), np.array([2.0, 0])),
        np.array([150.0, 0.0]),
    )


def test_calculate_zt_zero_pf_temp():
    assert calculate_zt(0, 300, 2.0) == 0.0
    assert calculate_zt(1.0, 0, 2.0) == 0.0


def test_calculate_zt_mixed_scalar_and_array():
    """CR-01: scalars and vectors may be combined; NumPy broadcasting applies."""
    result = calculate_zt(1.0, 300.0, np.array([2.0, 0.0]))
    assert isinstance(result, np.ndarray)
    assert np.allclose(result, np.array([150.0, 0.0]))

    result = calculate_zt(np.array([1.0, 2.0]), 300.0, 2.0)
    assert isinstance(result, np.ndarray)
    assert np.allclose(result, np.array([150.0, 300.0]))


def test_calculate_zt_series_zero_kappa_is_zero():
    """CR-02: ZT = 0 wherever kappa == 0, also for pandas Series inputs."""
    index = ["a", "b", "c"]
    pf = pd.Series([1.0, 1.0, 1.0], index=index)
    temperature = pd.Series([300.0, 300.0, 300.0], index=index)
    kappa = pd.Series([2.0, 0.0, 1.0], index=index)

    result = calculate_zt(pf, temperature, kappa)

    assert isinstance(result, pd.Series)
    assert result.index.tolist() == index
    assert result.tolist() == pytest.approx([150.0, 0.0, 300.0])
    assert np.isfinite(result.to_numpy()).all()


def test_calculate_zt_series_mixed_with_scalar():
    """CR-01 + CR-02 together: a Series denominator with zero entries."""
    result = calculate_zt(1.0, 300.0, pd.Series([2.0, 0.0]))

    assert isinstance(result, pd.Series)
    assert result.tolist() == pytest.approx([150.0, 0.0])


def test_calculate_zt_series_nan_kappa_stays_nan():
    result = calculate_zt(pd.Series([1.0]), pd.Series([300.0]), pd.Series([np.nan]))

    assert np.isnan(result.iloc[0])


# --- Test estimate_lorenz ---
def test_estimate_lorenz_scalar():
    s_uvk = 100
    expected_l = (1.5 + np.exp(-np.abs(s_uvk) / 116.0)) * 1e-8
    assert estimate_lorenz(s_uvk) == pytest.approx(expected_l)


def test_estimate_lorenz_array():
    s_uvk_array = np.array([100, 200, -50])
    expected_l_array = (1.5 + np.exp(-np.abs(s_uvk_array) / 116.0)) * 1e-8
    assert np.allclose(estimate_lorenz(s_uvk_array), expected_l_array)


def test_estimate_lorenz_zero_seebeck():
    assert estimate_lorenz(0) == pytest.approx((1.5 + np.exp(0)) * 1e-8)


# --- Test calculate_molecular_weight ---
def test_calculate_molecular_weight_valid_formula():
    assert calculate_molecular_weight("Bi2Te3") == pytest.approx(
        (2 * ATOMIC_WEIGHTS["Bi"] + 3 * ATOMIC_WEIGHTS["Te"], 5)
    )
    assert calculate_molecular_weight("Al2O3") == pytest.approx(
        (2 * ATOMIC_WEIGHTS["Al"] + 3 * ATOMIC_WEIGHTS["O"], 5)
    )
    assert calculate_molecular_weight("H2O") == pytest.approx(
        (2 * ATOMIC_WEIGHTS["H"] + ATOMIC_WEIGHTS["O"], 3)
    )
    assert calculate_molecular_weight("C") == pytest.approx((ATOMIC_WEIGHTS["C"], 1))
    assert calculate_molecular_weight("Bi2Te") == pytest.approx(
        (2 * ATOMIC_WEIGHTS["Bi"] + ATOMIC_WEIGHTS["Te"], 3)
    )


def test_calculate_molecular_weight_invalid_formula():

    assert calculate_molecular_weight("UnknownElement") == (None, 0)
    assert calculate_molecular_weight("Bi2X3") == (None, 0)


def test_calculate_molecular_weight_empty_formula():
    assert calculate_molecular_weight("") == (None, 0)


def test_calculate_molecular_weight_formula_with_spaces():
    assert calculate_molecular_weight(" Bi2 Te3 ") == pytest.approx(
        (2 * ATOMIC_WEIGHTS["Bi"] + 3 * ATOMIC_WEIGHTS["Te"], 5)
    )


# --- Test calculate_legacy_molecular_weight ---
def test_calculate_legacy_molecular_weight_valid():
    mass, atoms = calculate_legacy_molecular_weight("NaCl")
    assert mass == pytest.approx(58.44)
    assert atoms == 2


# --- Test calculate_dulong_petit_limit ---
def test_calculate_dulong_petit_limit_molar():
    value = calculate_dulong_petit_limit(5, 800.0, "J/mol·K")
    assert value == pytest.approx(5 * 3 * LEGACY_GAS_CONSTANT)


def test_calculate_dulong_petit_limit_specific():
    value = calculate_dulong_petit_limit(5, 800.0, "J/kg·K")
    assert value == pytest.approx((5 * 3 * LEGACY_GAS_CONSTANT) / (800.0 / 1000.0))
