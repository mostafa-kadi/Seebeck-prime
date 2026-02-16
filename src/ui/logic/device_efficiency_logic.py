import numpy as np
from scipy.integrate import simpson


def calculate_efficiencies(temps_k, seebecks_v_k, sigmas_s_m, kappas_w_mk, tc_k, th_k):
    """
    Calculates device-level efficiency based on temperature-dependent properties.

    Args:
        temps_k: Array of temperatures in Kelvin
        seebecks_v_k: Array of Seebeck coefficients in V/K
        sigmas_s_m: Array of electrical conductivities in S/m
        kappas_w_mk: Array of thermal conductivities in W/mK
        tc_k: Cold side temperature in Kelvin
        th_k: Hot side temperature in Kelvin

    Returns:
        dict: Containing ZT_avg, max_efficiency, power_output_factor, etc.
    """
    # Sort data by temperature
    idx = np.argsort(temps_k)
    t = temps_k[idx]
    s = seebecks_v_k[idx]
    sigma = sigmas_s_m[idx]
    kappa = kappas_w_mk[idx]

    # Filter for data within [Tc, Th]
    mask = (t >= tc_k) & (t <= th_k)
    if np.sum(mask) < 2:
        # If we don't have enough data in the range, we might need to interpolate/extrapolate
        # For now, let's just use what we have or return None
        if len(t) < 2:
            return None

        # Interpolate properties at Tc and Th if possible
        s_tc = np.interp(tc_k, t, s)
        s_th = np.interp(th_k, t, s)
        sigma_tc = np.interp(tc_k, t, sigma)
        sigma_th = np.interp(th_k, t, sigma)
        kappa_tc = np.interp(tc_k, t, kappa)
        kappa_th = np.interp(th_k, t, kappa)

        # Create a mini-range
        t_range = np.linspace(tc_k, th_k, 100)
        s_range = np.interp(t_range, [tc_k, th_k], [s_tc, s_th])
        sigma_range = np.interp(t_range, [tc_k, th_k], [sigma_tc, sigma_th])
        kappa_range = np.interp(t_range, [tc_k, th_k], [kappa_tc, kappa_th])
    else:
        t_range = t[mask]
        s_range = s[mask]
        sigma_range = sigma[mask]
        kappa_range = kappa[mask]

        # Optionally add endpoints if not exact
        if t_range[0] > tc_k:
            t_range = np.insert(t_range, 0, tc_k)
            s_range = np.insert(s_range, 0, np.interp(tc_k, t, s))
            sigma_range = np.insert(sigma_range, 0, np.interp(tc_k, t, sigma))
            kappa_range = np.insert(kappa_range, 0, np.interp(tc_k, t, kappa))

        if t_range[-1] < th_k:
            t_range = np.append(t_range, th_k)
            s_range = np.append(s_range, np.interp(th_k, t, s))
            sigma_range = np.append(sigma_range, np.interp(th_k, t, sigma))
            kappa_range = np.append(kappa_range, np.interp(th_k, t, kappa))

    # Calculate ZT at each point
    pf_range = (s_range**2) * sigma_range
    zt_range = (pf_range * t_range) / kappa_range

    # 1. Classical ZT_avg approach
    # ZT_avg = 1/(Th-Tc) * integral(ZT dT)
    delta_t = th_k - tc_k
    if delta_t <= 0:
        return None

    zt_avg = simpson(y=zt_range, x=t_range) / delta_t

    # Carnot efficiency
    carnot = delta_t / th_k

    # Max material efficiency (Constant property model)
    M = np.sqrt(1 + zt_avg)
    eta_max = carnot * (M - 1) / (M + tc_k / th_k)

    # 2. Engineering Figure of Merit (Snyder et al.)
    # (ZT)_eng = (integral(S dT))^2 / (integral(rho dT) * integral(kappa dT) / (Th-Tc)) * 1/Th
    # Note: this is a more advanced metric
    int_s = simpson(y=s_range, x=t_range)
    rho_range = 1.0 / sigma_range
    int_rho = simpson(y=rho_range, x=t_range)
    int_kappa = simpson(y=kappa_range, x=t_range)

    zt_eng = (int_s**2 / int_rho) / (int_kappa / delta_t) / th_k

    # Engineering Efficiency
    M_eng = np.sqrt(1 + zt_eng)
    eta_eng = carnot * (M_eng - 1) / (M_eng + tc_k / th_k)

    return {
        "ZT_avg": zt_avg,
        "ZT_eng": zt_eng,
        "Carnot": carnot,
        "Efficiency_Max": eta_max,
        "Efficiency_Eng": eta_eng,
        "DeltaT": delta_t,
        "Th": th_k,
        "Tc": tc_k,
    }
