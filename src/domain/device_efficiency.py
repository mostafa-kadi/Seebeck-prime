"""Temperature-dependent thermoelectric device efficiency estimates."""

from __future__ import annotations

import numpy as np
from scipy.integrate import simpson


def calculate_efficiencies(
    temps_k, seebecks_v_k, sigmas_s_m, kappas_w_mk, tc_k, th_k
):
    """Calculate average-ZT and engineering efficiency estimates.

    Inputs use temperature [K], Seebeck [V/K], conductivity [S/m], and
    thermal conductivity [W/(m·K)]. The implementation preserves the existing
    integration and endpoint interpolation behavior.
    """
    idx = np.argsort(temps_k)
    t = temps_k[idx]
    s = seebecks_v_k[idx]
    sigma = sigmas_s_m[idx]
    kappa = kappas_w_mk[idx]

    mask = (t >= tc_k) & (t <= th_k)
    if np.sum(mask) < 2:
        if len(t) < 2:
            return None
        s_tc = np.interp(tc_k, t, s)
        s_th = np.interp(th_k, t, s)
        sigma_tc = np.interp(tc_k, t, sigma)
        sigma_th = np.interp(th_k, t, sigma)
        kappa_tc = np.interp(tc_k, t, kappa)
        kappa_th = np.interp(th_k, t, kappa)
        t_range = np.linspace(tc_k, th_k, 100)
        s_range = np.interp(t_range, [tc_k, th_k], [s_tc, s_th])
        sigma_range = np.interp(t_range, [tc_k, th_k], [sigma_tc, sigma_th])
        kappa_range = np.interp(t_range, [tc_k, th_k], [kappa_tc, kappa_th])
    else:
        t_range = t[mask]
        s_range = s[mask]
        sigma_range = sigma[mask]
        kappa_range = kappa[mask]
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

    pf_range = (s_range**2) * sigma_range
    zt_range = (pf_range * t_range) / kappa_range
    delta_t = th_k - tc_k
    if delta_t <= 0:
        return None

    zt_avg = simpson(y=zt_range, x=t_range) / delta_t
    carnot = delta_t / th_k
    material_factor = np.sqrt(1 + zt_avg)
    eta_max = carnot * (material_factor - 1) / (material_factor + tc_k / th_k)

    int_s = simpson(y=s_range, x=t_range)
    rho_range = 1.0 / sigma_range
    int_rho = simpson(y=rho_range, x=t_range)
    int_kappa = simpson(y=kappa_range, x=t_range)

    # Engineering figure of merit (Snyder's ZT_eng):
    #
    #     ZT_eng = S_avg^2 * T_avg / (rho_avg * kappa_avg)
    #
    # with the averages taken over the junction interval dT = Th - Tc:
    #     S_avg    = (1/dT) * int S dT
    #     rho_avg  = (1/dT) * int rho dT      (rho = 1/sigma)
    #     kappa_avg= (1/dT) * int kappa dT
    #     T_avg    = (Tc + Th) / 2
    #
    # The earlier expression (int_s^2/int_rho)/(int_kappa/dT)/Th was NOT
    # dimensionless (it carried units of 1/K) and was 1e3-1e4 times too small:
    # for constant properties it returned ZT_eng = 8e-4 instead of the correct
    # ZT = 0.8, which drove Efficiency_Eng to ~1e-4 instead of the correct
    # Efficiency_Max. See docs/SCIENTIFIC_EQUATION_AUDIT.md (issue SE-001).
    s_avg = int_s / delta_t
    rho_avg = int_rho / delta_t
    kappa_avg = int_kappa / delta_t
    t_avg = 0.5 * (tc_k + th_k)
    zt_eng = (s_avg**2) * t_avg / (rho_avg * kappa_avg)

    engineering_factor = np.sqrt(1 + zt_eng)
    eta_eng = carnot * (engineering_factor - 1) / (
        engineering_factor + tc_k / th_k
    )

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
