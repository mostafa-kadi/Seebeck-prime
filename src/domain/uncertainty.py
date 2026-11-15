"""
Gaussian error propagation for thermoelectric quantities.

All propagation formulas follow first-order Gaussian error propagation for
independent (uncorrelated) variables:

    u_y = sqrt( Σ (∂f/∂x_i · u_x_i)² )

This module is pure (no GUI, no IO, no pandas dependency).
All inputs and outputs are floats or numpy arrays.
"""

from __future__ import annotations
import numpy as np


def propagate_relative_uncertainty(
    value: float | np.ndarray,
    *relative_uncertainties: float | np.ndarray,
) -> float | np.ndarray:
    """Combine independent relative standard uncertainties for a value."""
    variance = sum(np.asarray(relative, dtype=float) ** 2 for relative in relative_uncertainties)
    result = np.abs(value) * np.sqrt(variance)
    if np.ndim(result) == 0:
        return float(result)
    return result


def propagate_pf_error(
    seebeck: float | np.ndarray,
    seebeck_err: float | np.ndarray,
    conductivity: float | np.ndarray,
    conductivity_err: float | np.ndarray,
) -> float | np.ndarray:
    """
    Gaussian uncertainty for Power Factor PF = S² · σ.

    Partial derivatives:
        ∂PF/∂S = 2 · S · σ
        ∂PF/∂σ = S²

    Formula:
        u_PF = sqrt( (2·S·σ·u_S)² + (S²·u_σ)² )

    Args:
        seebeck: S [V/K].
        seebeck_err: u(S) [V/K].
        conductivity: σ [S/m].
        conductivity_err: u(σ) [S/m].

    Returns:
        u(PF) [W/(m·K²)].
    """
    return np.sqrt(
        (2.0 * seebeck * conductivity * seebeck_err) ** 2
        + (seebeck ** 2 * conductivity_err) ** 2
    )


def propagate_kappa_e_error(
    conductivity: float | np.ndarray,
    conductivity_err: float | np.ndarray,
    temperature: float | np.ndarray,
    temp_err: float | np.ndarray,
    lorenz: float | np.ndarray,
    lorenz_err: float | np.ndarray,
) -> float | np.ndarray:
    """
    Gaussian uncertainty for electronic thermal conductivity κe = L · σ · T.

    Partial derivatives:
        ∂κe/∂σ = L · T
        ∂κe/∂T = L · σ
        ∂κe/∂L = σ · T

    Formula:
        u_κe = sqrt( (L·T·u_σ)² + (L·σ·u_T)² + (σ·T·u_L)² )

    Args:
        conductivity: σ [S/m].
        conductivity_err: u(σ) [S/m].
        temperature: T [K].
        temp_err: u(T) [K].
        lorenz: Lorenz number L [W·Ω/K²].
        lorenz_err: u(L) [W·Ω/K²]. Use 0.0 if L is treated as exact.

    Returns:
        u(κe) [W/(m·K)].
    """
    return np.sqrt(
        (lorenz * temperature * conductivity_err) ** 2
        + (lorenz * conductivity * temp_err) ** 2
        + (conductivity * temperature * lorenz_err) ** 2
    )


def propagate_kappa_l_error(
    kappa_total_err: float | np.ndarray,
    kappa_e_err: float | np.ndarray,
) -> float | np.ndarray:
    """
    Gaussian uncertainty for lattice thermal conductivity κL = κtotal − κe.

    Formula:
        u_κL = sqrt( u_κtotal² + u_κe² )

    Args:
        kappa_total_err: u(κtotal) [W/(m·K)].
        kappa_e_err: u(κe) [W/(m·K)].

    Returns:
        u(κL) [W/(m·K)].
    """
    return np.sqrt(kappa_total_err ** 2 + kappa_e_err ** 2)


def propagate_zt_error(
    pf: float | np.ndarray,
    pf_err: float | np.ndarray,
    temperature: float | np.ndarray,
    temp_err: float | np.ndarray,
    kappa_total: float | np.ndarray,
    kappa_total_err: float | np.ndarray,
) -> float | np.ndarray:
    """
    Gaussian uncertainty for figure of merit ZT = PF · T / κtotal.

    Relative form:
        u_ZT / ZT = sqrt( (u_PF/PF)² + (u_T/T)² + (u_κ/κ)² )

    Division-by-zero handled: u_ZT = 0 wherever PF, T, or κ is zero.

    Args:
        pf: Power Factor PF [W/(m·K²)].
        pf_err: u(PF) [W/(m·K²)].
        temperature: T [K].
        temp_err: u(T) [K].
        kappa_total: κtotal [W/(m·K)].
        kappa_total_err: u(κtotal) [W/(m·K)].

    Returns:
        u(ZT) [dimensionless].
    """
    pf = np.asarray(pf, dtype=float)
    pf_err = np.asarray(pf_err, dtype=float)
    temperature = np.asarray(temperature, dtype=float)
    temp_err = np.asarray(temp_err, dtype=float)
    kappa_total = np.asarray(kappa_total, dtype=float)
    kappa_total_err = np.asarray(kappa_total_err, dtype=float)

    zt_numerator, kappa_values = np.broadcast_arrays(pf * temperature, kappa_total)
    zt = np.zeros_like(zt_numerator, dtype=float)
    np.divide(zt_numerator, kappa_values, out=zt, where=kappa_values != 0)
    mask = (pf != 0) & (temperature != 0) & (kappa_total != 0)
    zt_err = np.zeros_like(zt)
    zt_err[mask] = np.abs(zt[mask]) * np.sqrt(
        (pf_err[mask] / pf[mask]) ** 2
        + (temp_err[mask] / temperature[mask]) ** 2
        + (kappa_total_err[mask] / kappa_total[mask]) ** 2
    )
    # Return scalar if inputs were scalar-like
    if zt_err.ndim == 0:
        return float(zt_err)
    return zt_err


def propagate_sigma_error(
    area: float | np.ndarray,
    area_err: float | np.ndarray,
    length: float | np.ndarray,
    length_err: float | np.ndarray,
    resistance: float | np.ndarray,
    resistance_err: float | np.ndarray,
) -> float | np.ndarray:
    """
    Gaussian uncertainty for conductivity from geometry + resistance:
    σ = L / (R · A).

    Relative form:
        u_σ / σ = sqrt( (u_L/L)² + (u_R/R)² + (u_A/A)² )

    Args:
        area: Cross-sectional area A [m²].
        area_err: u(A) [m²].
        length: Probe/contact length L [m].
        length_err: u(L) [m].
        resistance: Electrical resistance R [Ω].
        resistance_err: u(R) [Ω].

    Returns:
        u(σ) [S/m].
    """
    sigma = length / (resistance * area)
    return np.abs(sigma) * np.sqrt(
        (length_err / length) ** 2
        + (resistance_err / resistance) ** 2
        + (area_err / area) ** 2
    )


def propagate_kappa_error(
    diffusivity: float | np.ndarray,
    diffusivity_err: float | np.ndarray,
    cp: float | np.ndarray,
    cp_err: float | np.ndarray,
    density: float | np.ndarray,
    density_err: float | np.ndarray,
) -> float | np.ndarray:
    """
    Gaussian uncertainty for thermal conductivity from laser flash:
    κ = α · Cp · ρ.

    Relative form:
        u_κ / κ = sqrt( (u_α/α)² + (u_Cp/Cp)² + (u_ρ/ρ)² )

    Args:
        diffusivity: Thermal diffusivity α [m²/s].
        diffusivity_err: u(α) [m²/s].
        cp: Specific heat Cp [J/(kg·K)].
        cp_err: u(Cp) [J/(kg·K)].
        density: Mass density ρ [kg/m³].
        density_err: u(ρ) [kg/m³].

    Returns:
        u(κ) [W/(m·K)].
    """
    kappa = diffusivity * cp * density
    return np.abs(kappa) * np.sqrt(
        (diffusivity_err / diffusivity) ** 2
        + (cp_err / cp) ** 2
        + (density_err / density) ** 2
    )


def propagate_density_error(
    weight: float | np.ndarray,
    weight_err: float | np.ndarray,
    area: float | np.ndarray,
    area_err: float | np.ndarray,
    thickness: float | np.ndarray,
    thickness_err: float | np.ndarray,
) -> float | np.ndarray:
    """
    Gaussian uncertainty for sample density ρ = m / (A · t).

    Relative form:
        u_ρ / ρ = sqrt( (u_m/m)² + (u_A/A)² + (u_t/t)² )

    Args:
        weight: Sample mass m [kg].
        weight_err: u(m) [kg].
        area: Area A [m²].
        area_err: u(A) [m²].
        thickness: Thickness t [m].
        thickness_err: u(t) [m].

    Returns:
        u(ρ) [kg/m³].
    """
    density = weight / (area * thickness)
    return np.abs(density) * np.sqrt(
        (weight_err / weight) ** 2
        + (area_err / area) ** 2
        + (thickness_err / thickness) ** 2
    )


# Backward compatibility aliases for legacy naming
calculate_pf_error = propagate_pf_error
calculate_kappa_e_error = propagate_kappa_e_error
calculate_kappa_l_error = propagate_kappa_l_error
calculate_zt_error = propagate_zt_error
calculate_measurement_sigma_error = propagate_sigma_error
calculate_measurement_kappa_error = propagate_kappa_error
calculate_density_error = propagate_density_error

