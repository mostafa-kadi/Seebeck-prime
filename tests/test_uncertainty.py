import pytest
import numpy as np
from src.seebeck_prime.domain.uncertainty import (
    propagate_pf_error,
    propagate_kappa_e_error,
    propagate_kappa_l_error,
    propagate_zt_error,
    propagate_sigma_error,
    propagate_kappa_error,
    propagate_density_error,
)
from src.seebeck_prime.domain.physical_constants import DEFAULT_LORENZ


# --- Test propagate_pf_error ---
def test_propagate_pf_error_scalar():
    s = 100e-6  # V/K
    s_err = 5e-6
    sigma = 1e5  # S/m
    sigma_err = 0.05e5

    # PF = S^2 * sigma
    # u_PF = sqrt( (dPF/dS * u_S)^2 + (dPF/dsigma * u_sigma)^2 )
    # dPF/dS = 2 * S * sigma
    # dPF/dsigma = S^2
    expected_pf_err = np.sqrt(
        ((2 * s * sigma) * s_err) ** 2 + ((s**2) * sigma_err) ** 2
    )
    assert propagate_pf_error(s, s_err, sigma, sigma_err) == pytest.approx(
        expected_pf_err
    )


def test_propagate_pf_error_array():
    s = np.array([100e-6, 50e-6])
    s_err = np.array([5e-6, 2e-6])
    sigma = np.array([1e5, 0.5e5])
    sigma_err = np.array([0.05e5, 0.02e5])

    expected_pf_err = np.sqrt(
        ((2 * s * sigma) * s_err) ** 2 + ((s**2) * sigma_err) ** 2
    )
    assert np.allclose(propagate_pf_error(s, s_err, sigma, sigma_err), expected_pf_err)


def test_propagate_pf_error_zero_uncertainties():
    assert propagate_pf_error(100e-6, 0, 1e5, 0) == 0


# --- Test propagate_kappa_e_error ---
def test_propagate_kappa_e_error_scalar():
    sigma = 1e5  # S/m
    sigma_err = 0.05e5
    temp = 300  # K
    temp_err = 5
    lorenz = DEFAULT_LORENZ
    lorenz_err = 0  # Assuming Lorenz is constant for this test

    # kappa_e = L * sigma * T
    # u_kappa_e = sqrt( (dK/dL * u_L)^2 + (dK/dsigma * u_sigma)^2 + (dK/dT * u_T)^2 )
    # dK/dL = sigma * T
    # dK/dsigma = L * T
    # dK/dT = L * sigma
    expected_kappa_e_err = np.sqrt(
        ((sigma * temp) * lorenz_err) ** 2
        + ((lorenz * temp) * sigma_err) ** 2
        + ((lorenz * sigma) * temp_err) ** 2
    )
    assert propagate_kappa_e_error(
        sigma, sigma_err, temp, temp_err, lorenz, lorenz_err
    ) == pytest.approx(expected_kappa_e_err)


def test_propagate_kappa_e_error_array():
    sigma = np.array([1e5, 0.5e5])
    sigma_err = np.array([0.05e5, 0.02e5])
    temp = np.array([300, 400])
    temp_err = np.array([5, 10])
    lorenz = DEFAULT_LORENZ
    lorenz_err = 0

    expected_kappa_e_err = np.sqrt(
        ((sigma * temp) * lorenz_err) ** 2
        + ((lorenz * temp) * sigma_err) ** 2
        + ((lorenz * sigma) * temp_err) ** 2
    )
    assert np.allclose(
        propagate_kappa_e_error(sigma, sigma_err, temp, temp_err, lorenz, lorenz_err),
        expected_kappa_e_err,
    )


def test_propagate_kappa_e_error_zero_uncertainties():
    assert propagate_kappa_e_error(1e5, 0, 300, 0, DEFAULT_LORENZ, 0) == 0


# --- Test propagate_kappa_l_error ---
def test_propagate_kappa_l_error_scalar():
    kappa_total = 2.0
    kappa_total_err = 0.1
    kappa_e = 0.5
    kappa_e_err = 0.02

    # kappa_l = kappa_total - kappa_e
    # u_kappa_l = sqrt( u_kappa_total^2 + u_kappa_e^2 )
    expected_kappa_l_err = np.sqrt(kappa_total_err**2 + kappa_e_err**2)
    assert propagate_kappa_l_error(kappa_total_err, kappa_e_err) == pytest.approx(
        expected_kappa_l_err
    )


def test_propagate_kappa_l_error_array():
    kappa_total_err = np.array([0.1, 0.05])
    kappa_e_err = np.array([0.02, 0.01])

    expected_kappa_l_err = np.sqrt(kappa_total_err**2 + kappa_e_err**2)
    assert np.allclose(
        propagate_kappa_l_error(kappa_total_err, kappa_e_err), expected_kappa_l_err
    )


def test_propagate_kappa_l_error_zero_uncertainties():
    assert propagate_kappa_l_error(0, 0) == 0


# --- Test propagate_zt_error ---
def test_propagate_zt_error_scalar():
    pf = 1e-3
    pf_err = 0.05e-3
    temp = 300
    temp_err = 5
    kappa_total = 2.0
    kappa_total_err = 0.1

    # ZT = (PF * T) / kappa_total
    # Relative error propagation: (u_ZT/ZT)^2 = (u_PF/PF)^2 + (u_T/T)^2 + (u_kappa_total/kappa_total)^2
    # u_ZT = ZT * sqrt( (u_PF/PF)^2 + (u_T/T)^2 + (u_kappa_total/kappa_total)^2 )
    zt_val = (pf * temp) / kappa_total
    expected_zt_err = zt_val * np.sqrt(
        (pf_err / pf) ** 2
        + (temp_err / temp) ** 2
        + (kappa_total_err / kappa_total) ** 2
    )
    assert propagate_zt_error(
        pf, pf_err, temp, temp_err, kappa_total, kappa_total_err
    ) == pytest.approx(expected_zt_err)


def test_propagate_zt_error_array():
    pf = np.array([1e-3, 0.5e-3])
    pf_err = np.array([0.05e-3, 0.02e-3])
    temp = np.array([300, 400])
    temp_err = np.array([5, 10])
    kappa_total = np.array([2.0, 1.5])
    kappa_total_err = np.array([0.1, 0.05])

    zt_val = (pf * temp) / kappa_total
    expected_zt_err = zt_val * np.sqrt(
        (pf_err / pf) ** 2
        + (temp_err / temp) ** 2
        + (kappa_total_err / kappa_total) ** 2
    )
    assert np.allclose(
        propagate_zt_error(pf, pf_err, temp, temp_err, kappa_total, kappa_total_err),
        expected_zt_err,
    )


def test_propagate_zt_error_zero_uncertainties():
    assert propagate_zt_error(1e-3, 0, 300, 0, 2.0, 0) == 0


def test_propagate_zt_error_zero_denominator_value():
    # If kappa_total is zero, ZT is effectively infinite, so uncertainty should be 0 (or NaN depending on implementation)
    # Current implementation returns 0 if any value is 0, which is a simplification.
    assert propagate_zt_error(1e-3, 0.05e-3, 300, 5, 0, 0.1) == 0
    zt_errors = propagate_zt_error(
        np.array([1e-3, 1e-3]),
        np.array([0.05e-3, 0.05e-3]),
        np.array([300, 300]),
        np.array([5, 5]),
        np.array([2.0, 0]),
        np.array([0.1, 0.1]),
    )
    expected_errors = np.array([0.025000000000000005, 0.0])
    for i in range(len(zt_errors)):
        assert zt_errors[i] == pytest.approx(expected_errors[i])


# --- Test propagate_sigma_error ---
def test_propagate_sigma_error_scalar():
    area = 1e-4
    area_err = 0.01e-4
    length = 1e-2
    length_err = 0.001e-2
    resistance = 100
    resistance_err = 5

    # sigma = length / (resistance * area)
    # Relative error propagation: (u_sigma/sigma)^2 = (u_L/L)^2 + (u_R/R)^2 + (u_A/A)^2
    # u_sigma = sigma * sqrt( (u_L/L)^2 + (u_R/R)^2 + (u_A/A)^2 )
    sigma_val = length / (resistance * area)
    expected_sigma_err = sigma_val * np.sqrt(
        (length_err / length) ** 2
        + (resistance_err / resistance) ** 2
        + (area_err / area) ** 2
    )
    assert propagate_sigma_error(
        area, area_err, length, length_err, resistance, resistance_err
    ) == pytest.approx(expected_sigma_err)


def test_propagate_sigma_error_zero_uncertainties():
    assert propagate_sigma_error(1e-4, 0, 1e-2, 0, 100, 0) == 0


# --- Test propagate_kappa_error ---
def test_propagate_kappa_error_scalar():
    diffusivity = 1e-6
    diffusivity_err = 0.05e-6
    cp = 1e6
    cp_err = 0.05e6
    density = 5000
    density_err = 200

    # kappa = diffusivity * cp * density
    # Relative error propagation: (u_kappa/kappa)^2 = (u_D/D)^2 + (u_Cp/Cp)^2 + (u_rho/rho)^2
    # u_kappa = kappa * sqrt( (u_D/D)^2 + (u_Cp/Cp)^2 + (u_rho/rho)^2 )
    kappa_val = diffusivity * cp * density
    expected_kappa_err = kappa_val * np.sqrt(
        (diffusivity_err / diffusivity) ** 2
        + (cp_err / cp) ** 2
        + (density_err / density) ** 2
    )
    assert propagate_kappa_error(
        diffusivity, diffusivity_err, cp, cp_err, density, density_err
    ) == pytest.approx(expected_kappa_err)


def test_propagate_kappa_error_zero_uncertainties():
    assert propagate_kappa_error(1e-6, 0, 1e6, 0, 5000, 0) == 0


# --- Test propagate_density_error ---
def test_propagate_density_error_scalar():
    weight = 1e-3
    weight_err = 0.01e-3
    area = 1e-4
    area_err = 0.01e-4
    thickness = 1e-3
    thickness_err = 0.01e-3

    # density = weight / (area * thickness)
    # Relative error propagation: (u_rho/rho)^2 = (u_W/W)^2 + (u_A/A)^2 + (u_T/T)^2
    # u_rho = rho * sqrt( (u_W/W)^2 + (u_A/A)^2 + (u_T/T)^2 )
    density_val = weight / (area * thickness)
    expected_density_err = density_val * np.sqrt(
        (weight_err / weight) ** 2
        + (area_err / area) ** 2
        + (thickness_err / thickness) ** 2
    )
    assert propagate_density_error(
        weight, weight_err, area, area_err, thickness, thickness_err
    ) == pytest.approx(expected_density_err)


def test_propagate_density_error_zero_uncertainties():
    assert propagate_density_error(1e-3, 0, 1e-4, 0, 1e-3, 0) == 0
