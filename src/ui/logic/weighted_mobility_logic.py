import numpy as np

# Constants
KB_E = 86.1733  # Boltzmann constant / electron charge in uV/K
COEFF_MU_W = 331.0  # Coefficient for weighted mobility in cm^2/Vs


def calculate_weighted_mobility(T, rho, S):
    """
    Calculates weighted mobility using the exact Drude-Sommerfeld approximation
    from Snyder et al.

    Parameters:
    -----------
    T : float or np.ndarray
        Temperature in Kelvin.
    rho : float or np.ndarray
        Electrical resistivity in mOhm*cm.
    S : float or np.ndarray
        Seebeck coefficient in uV/K (absolute value is used).

    Returns:
    --------
    mu_w : float or np.ndarray
        Weighted mobility in cm^2/(V*s).
    """

    # Ensure inputs are floats or arrays
    T = np.array(T, dtype=float)
    rho = np.array(rho, dtype=float)
    S = np.abs(np.array(S, dtype=float))  # Use absolute Seebeck

    # Reduced Seebeck (eta_S)
    # S is in uV/K, KB_E is in uV/K  -> dimensionless
    eta_S = S / KB_E

    # Analytic approximation for the function F(S)
    # F(S) term
    # exp term 1: exp(eta_S - 2)
    # denom 1: 1 + exp(-5 * (eta_S - 1))

    # To prevent overflow with exp, we can clip eta_S if needed,
    # but typical S values (0-500 uV/K) give eta_S ~ 0-6.
    # eta_S - 2 ~ -2 to 4. exp(4) is fine.

    term1_num = np.exp(eta_S - 2)
    term1_den = 1 + np.exp(-5 * (eta_S - 1))

    term2_num = 3 * (np.pi**2) / (eta_S + 1e-9)  # Avoid div by zero
    term2_den = 1 + np.exp(5 * (eta_S - 1))

    f_sep = (term1_num / term1_den) + (term2_num / term2_den)

    # Temperature normalization (T / 300)^-1.5
    t_norm = (T / 300.0) ** (-1.5)

    # Final calculation
    # mu_w = 331 * (mOhm cm / rho) * (T/300)^-1.5 * F(sep)
    # Note: rho input is mOhm*cm. Formula essentially has "1 mOhm*cm" in numerator if we consider units.
    # The paper says: mu_w = 331 [cm2/Vs] * (mOhm cm / rho) ...
    # So if rho is 1 mOhm cm, the term is 1.

    # Avoid division by zero for rho
    rho = np.where(rho == 0, np.nan, rho)

    mu_w = COEFF_MU_W * (1 / rho) * t_norm * f_sep

    return mu_w


def convert_to_mOhm_cm(value, unit):
    """
    Converts resistivity/conductivity to mOhm*cm.
    """
    if unit == "mΩ·cm":
        return value
    elif unit == "Ω·m":
        # 1 Ohm m = 100 Ohm cm = 100,000 mOhm cm.
        return value * 1e5
    elif unit == "S/cm":
        # rho = 1/sigma.
        # 1 S/cm = 1 Ohm^-1 cm^-1
        # rho = 1 Ohm cm = 1000 mOhm cm
        return 1000.0 / value
    elif unit == "S/m":
        # 1 S/m = 0.01 S/cm
        # rho = 1 / (0.01 * value) Ohm cm = 100 / value Ohm cm = 100,000 / value mOhm cm
        return 1e5 / value
    return value
