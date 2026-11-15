"""Phase 3.5 audit: the weighted-mobility implementation versus the
equation published in the project's own scientific model register.

``docs/SCIENTIFIC_MODEL_REGISTER.md`` section 3.4 documents

    mu_W = 3 h^3 sigma / (8 pi e (2 m_e k_B T)^{3/2}) * [ Breg(s) ]^{-1}
    Breg(s) = exp(s-2)/(1+exp(-5(s-1))) + (3/pi^2) * s
    s = |S| / (k_B/e)

while ``src/domain/transport.py`` implements

    mu_W = 331 * (1/rho) * (T/300)^{-3/2} * shape(s)
    shape(s) = exp(s-2)/(1+exp(-5(s-1))) + 3 pi^2 / (s (1+exp(5(s-1))))
    with rho in mohm.cm

This script quantifies the relationship between the two forms. It changes
nothing.

    python tools/audit_weighted_mobility.py
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from seebeck_prime.domain.physical_constants import (  # noqa: E402
    AVOGADRO,
    BOLTZMANN,
    ELECTRON_CHARGE,
    ELECTRON_MASS,
    PLANCK,
)
from seebeck_prime.domain.transport import calculate_weighted_mobility  # noqa: E402

K_B_OVER_E = BOLTZMANN / ELECTRON_CHARGE


def register_bracket(s: np.ndarray) -> np.ndarray:
    """The shape bracket of the documented equation (used inverted)."""
    first = np.exp(s - 2.0) / (1.0 + np.exp(-5.0 * (s - 1.0)))
    second = (3.0 / math.pi**2) * s
    return first + second


def implemented_shape(s: np.ndarray) -> np.ndarray:
    """The shape factor of the implemented equation."""
    first = np.exp(s - 2.0) / (1.0 + np.exp(-5.0 * (s - 1.0)))
    second = (3.0 * math.pi**2) / (s + 1e-9) / (1.0 + np.exp(5.0 * (s - 1.0)))
    return first + second


def register_mu_w(sigma_s_m: float, temperature_k: float, seebeck_v_k: float) -> float:
    """mu_W from the documented equation, in m^2/(V.s)."""
    s = abs(seebeck_v_k) / K_B_OVER_E
    prefactor = (
        3.0 * PLANCK**3 * sigma_s_m
        / (8.0 * math.pi * ELECTRON_CHARGE * (2.0 * ELECTRON_MASS * BOLTZMANN * temperature_k) ** 1.5)
    )
    return prefactor / register_bracket(np.array([s]))[0]


def implemented_mu_w(rho_mohm_cm: float, temperature_k: float, seebeck_v_k: float) -> float:
    """mu_W from the implementation, in cm^2/(V.s)."""
    value = calculate_weighted_mobility(temperature_k, rho_mohm_cm, seebeck_v_k * 1e6)
    return float(value)


def main() -> None:
    print("=" * 78)
    print("WEIGHTED MOBILITY - the implemented equation versus the register")
    print("=" * 78)

    print()
    print("--- 1. Do the two shape factors coincide? ---")
    print(f"  {'s':>6} {'register bracket':>18} {'implemented shape':>19} {'ratio':>9}")
    for s in (0.5, 1.0, 1.5, 1.7405, 2.0, 3.0, 5.0):
        a = register_bracket(np.array([s]))[0]
        b = implemented_shape(np.array([s]))[0]
        print(f"  {s:6.3f} {a:18.6f} {b:19.6f} {b / a:9.4f}")
    print("  -> the two shape factors are NOT the same function.")

    print()
    print("--- 2. Is the prefactor relation 331 = 1e4 x (register prefactor)? ---")
    # the register form expressed with (1/rho) in (mohm.cm)^-1 and T scaled
    sigma = 1.0e5
    rho_mohm_cm = 1.0
    temperature = 300.0
    # sigma[S/m] that corresponds to rho = 1 mohm.cm
    sigma_for_rho = 1.0 / (rho_mohm_cm * 1e-5)
    register_pref = (
        3.0 * PLANCK**3
        / (8.0 * math.pi * ELECTRON_CHARGE * (2.0 * ELECTRON_MASS * BOLTZMANN * temperature) ** 1.5)
    )
    # expressed per (mohm.cm)^-1 with (T/300)^-3/2
    scaled = register_pref * sigma_for_rho * temperature**1.5
    print(f"  register prefactor (per (mohm.cm)^-1, with (T/300)^-3/2): {scaled:.6f} m^2/(V.s)")
    print(f"  scaled to cm^2/(V.s) by 1e4                       : {scaled * 1e4:.4f}")
    print(f"  the implementation uses                              : 331.0")
    print(f"  -> the prefactors differ by a factor {331.0 / (scaled * 1e4):.6f}")

    print()
    print("--- 3. The resulting mobilities, side by side ---")
    print(f"  {'T [K]':>7} {'rho [mohm.cm]':>14} {'|S| [uV/K]':>11} "
          f"{'register [cm2/Vs]':>19} {'implemented [cm2/Vs]':>21} {'ratio':>8}")
    rows = []
    for temperature in (300.0, 600.0, 900.0):
        for rho in (0.5, 1.0, 2.0):
            for seebeck in (-250e-6, -150e-6, -80e-6):
                sigma = 1.0 / (rho * 1e-5)
                reg = register_mu_w(sigma, temperature, seebeck) * 1e4
                imp = implemented_mu_w(rho, temperature, seebeck)
                rows.append((reg, imp))
                print(f"  {temperature:7.0f} {rho:14.2f} {seebeck * 1e6:11.0f} "
                      f"{reg:19.2f} {imp:21.2f} {imp / reg:8.4f}")

    ratios = np.array([imp / reg for reg, imp in rows])
    print()
    print(f"  implemented / register over the grid: {ratios.min():.4f} .. {ratios.max():.4f}")

    print()
    print("--- 4. What the implementation is internally consistent with ---")
    print("  * the independent reference implementation (validation/independent_calculations),")
    print("    agreement <= 1e-9 relative - so the FORM is reproducible;")
    print("  * the golden regression snapshot;")
    print("  * the unit convention: rho in mohm.cm, |S| in uV/K, output in cm^2/(V.s).")
    print()
    print("  The implementation is therefore *self-consistent* but it is NOT the")
    print("  equation printed in docs/SCIENTIFIC_MODEL_REGISTER.md section 3.4.")
    print()
    print("  Resolving the divergence requires one of:")
    print("    (a) the primary source (Snyder et al. (2020), Advanced Materials 32,")
    print("        2001537) to establish which form is the published one;")
    print("    (b) an experimental reference for mu_w - none exists in the benchmark")
    print("        set (the published carrier-mobility curve is negative and unusable).")
    print("  Without one of those, the implementation must NOT be changed, and the")
    print("  register must be corrected to describe what the code actually does,")
    print("  with the divergence recorded as an open item.")


if __name__ == "__main__":
    main()
