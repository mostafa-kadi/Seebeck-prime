"""Generate the application-vs-independent-reference comparison table.

The numbers in the results report are produced by this script, not written
by hand.  Run from the repository root:

    python tools/generate_reference_comparison.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.independent_calculations import references as ref  # noqa: E402

from seebeck_prime.domain import calculations as calc  # noqa: E402
from seebeck_prime.domain import hall as hall_domain  # noqa: E402
from seebeck_prime.domain import phonon as phonon_domain  # noqa: E402
from seebeck_prime.domain import spb as spb_domain  # noqa: E402
from seebeck_prime.domain import transport as transport_domain  # noqa: E402
from seebeck_prime.domain import uncertainty as unc  # noqa: E402

ROWS: list[tuple[str, float, float, float, float, str]] = []


def record(name: str, app: float, reference: float, tol: float, kind: str = "rel") -> None:
    app = float(app)
    reference = float(reference)
    abs_err = abs(app - reference)
    denom = abs(reference) if reference != 0.0 else 1.0
    rel_err = abs_err / denom
    if kind == "rel":
        passed = rel_err <= tol
    else:
        passed = abs_err <= tol
    ROWS.append((name, app, reference, abs_err, rel_err, tol, passed))


def worst(name: str, pairs, tol: float, kind: str = "rel") -> None:
    """Record the worst case over a parameter grid."""
    worst_pair = None
    worst_value = -1.0
    for app_value, ref_value in pairs:
        app_f, ref_f = float(app_value), float(ref_value)
        abs_err = abs(app_f - ref_f)
        denom = abs(ref_f) if ref_f != 0.0 else 1.0
        metric = abs_err / denom if kind == "rel" else abs_err
        if metric > worst_value:
            worst_value = metric
            worst_pair = (app_f, ref_f)
    record(name, worst_pair[0], worst_pair[1], tol, kind)


# --- PF ---------------------------------------------------------------
worst(
    "PF = S^2*sigma",
    [(calc.calculate_pf(s, g), ref.power_factor(s, g))
     for s in (-3.0e-4, -1.5e-4, -1e-6, 0.0, 1e-6, 1.5e-4, 3.0e-4)
     for g in (1.0, 1e3, 1e5, 1e7)],
    1e-12,
)

# --- kappa_e ----------------------------------------------------------
worst(
    "kappa_e = L*sigma*T",
    [(calc.calculate_kappa_e(g, t, l), ref.kappa_electronic(g, t, l))
     for l in (2.44e-8, 1.5e-8, 3.0e-8)
     for g in (1.0, 1e3, 1e5, 1e7)
     for t in (77.0, 300.0, 1000.0)],
    1e-12,
)

# --- kappa_L ----------------------------------------------------------
worst(
    "kappa_L = kappa_total - kappa_e",
    [(calc.calculate_kappa_l(k, calc.calculate_kappa_e(g, t)), ref.kappa_lattice(k, ref.kappa_electronic(g, t, 2.44e-8)))
     for k in (0.5, 2.0, 5.0)
     for g in (1e3, 1e5, 1e6)
     for t in (300.0, 600.0)],
    1e-12,
)

# --- ZT ---------------------------------------------------------------
worst(
    "ZT = PF*T/kappa",
    [(calc.calculate_zt(p, t, k), ref.figure_of_merit(p, t, k))
     for p in (1e-6, 1e-3, 5e-3)
     for t in (300.0, 600.0)
     for k in (0.5, 2.0, 4.0)],
    1e-12,
)

# --- laser flash ------------------------------------------------------
worst(
    "kappa = alpha*Cp*rho (SI)",
    [(phonon_domain.kappa_from_diffusivity_si(a, c, r),
      ref.kappa_from_laser_flash_si(a, c, r))
     for a in (1e-7, 1.2e-6, 1e-5)
     for c in (120.0, 520.0, 900.0)
     for r in (1600.0, 7300.0, 19300.0)],
    1e-12,
)
worst(
    "kappa = alpha*Cp*rho (laboratory units)",
    [(phonon_domain.kappa_from_diffusivity(a, c, r),
      ref.kappa_from_laser_flash_lab(a, c, r))
     for a in (0.12, 1.2, 8.0)
     for c in (0.12, 0.52, 0.9)
     for r in (1.6, 7.3, 19.3)],
    1e-12,
)

# --- Lorenz -----------------------------------------------------------
worst(
    "Kim empirical Lorenz L(S)",
    [(calc.estimate_lorenz(s), ref.lorenz_kim(s))
     for s in (-400.0, -250.0, -120.0, -50.0, 0.0, 50.0, 120.0, 250.0, 400.0)],
    1e-12,
)
record(
    "Sommerfeld L0 = (pi^2/3)(k_B/e)^2",
    ref.lorenz_sommerfeld(),
    2.443004509e-8,
    1e-9,
)

# --- SPB --------------------------------------------------------------
worst(
    "SPB S(eta)",
    [(spb_domain.seebeck_from_reduced_fermi_level(e, lam), ref.spb_seebeck(e, lam))
     for lam in (0.0, 1.0, 2.0)
     for e in (-12.0, -6.0, -3.0, 0.0, 2.0, 5.0, 9.0)],
    1e-6,
)
worst(
    "SPB L(eta)",
    [(spb_domain.rigorous_lorenz_number(e, lam), ref.spb_lorenz_number(e, lam))
     for lam in (0.0, 1.0, 2.0)
     for e in (-12.0, -6.0, -3.0, 0.0, 2.0, 5.0, 9.0)],
    1e-6,
)
worst(
    "SPB eta inversion from S",
    [(spb_domain.reduced_fermi_level_from_seebeck(s, lam),
      ref.spb_eta_from_seebeck(s, lam))
     for lam in (0.0, 1.0, 2.0)
     for s in (60.0, 100.0, 150.0, 200.0, 250.0)],
    1e-5,
)
worst(
    "SPB carrier density n(eta, m*, T)",
    [(spb_domain.calculate_carrier_density_spb(e, m, t), ref.spb_carrier_density(e, m, t))
     for m in (0.5, 1.0, 1.7, 2.5)
     for t in (300.0, 600.0, 900.0)
     for e in (-4.0, 0.0, 3.0)],
    1e-6,
)
worst(
    "SPB effective mass m*(S, n, T)",
    [(spb_domain.calculate_effective_mass(s, n, t, lambda_scat=0.0)[0],
      ref.spb_effective_mass(s, n, t, lambda_scat=0.0))
     for s in (100.0, 150.0, 200.0)
     for n in (1e19, 1e20, 1e21)
     for t in (300.0, 700.0)],
    1e-6,
)

# --- weighted mobility ------------------------------------------------
worst(
    "Weighted mobility mu_w",
    [(transport_domain.calculate_weighted_mobility(t, r, s),
      ref.weighted_mobility_snyder(t, r, s))
     for t in (200.0, 300.0, 600.0, 1000.0)
     for r in (0.1, 1.0, 10.0)
     for s in (-300.0, -150.0, 100.0)],
    1e-9,
)

# --- Hall -------------------------------------------------------------
worst(
    "Hall coefficient R_H",
    [(hall_domain.calculate_hall_coefficient_from_raw(v, th, i, b),
      ref.hall_coefficient(v, th, i, b))
     for v in (1e-5, 1.2e-4, 1e-3)
     for th in (1e-4, 1e-3)
     for i in (1e-3, 1e-2)
     for b in (0.2, 0.5, 1.0)],
    1e-12,
)
worst(
    "Hall carrier density n_H",
    [(hall_domain.calculate_hall_carrier_density(r, 1.0), ref.hall_carrier_density(r, 1.0))
     for r in (1e-5, 1e-4, 1e-3)],
    1e-9,
)
worst(
    "Hall mobility mu_H",
    [(hall_domain.calculate_hall_mobility(r, g), ref.hall_mobility(r, g))
     for r in (1e-5, 1e-4, 1e-3)
     for g in (1e4, 1e5, 1e6)],
    1e-12,
)

# --- uncertainties ----------------------------------------------------
worst(
    "u(PF)",
    [(unc.propagate_pf_error(s, us, g, ug), ref.u_pf(s, us, g, ug))
     for s in (5e-5, 1.5e-4, 3e-4)
     for us in (1e-6, 6e-6, 2e-5)
     for g in (1e4, 1e5, 1e6)
     for ug in (1e2, 6e3, 5e4)],
    1e-12,
)
worst(
    "u(kappa_e)",
    [(unc.propagate_kappa_e_error(g, ug, t, ut, l, ul),
      ref.u_kappa_electronic(g, ug, t, ut, l, ul))
     for g in (1e4, 1e5, 1e6)
     for ug in (1e2, 6e3)
     for t in (200.0, 300.0, 900.0)
     for ut in (0.5, 2.0)
     for l in (2.44e-8,)
     for ul in (1e-9, 5e-9)],
    1e-12,
)
worst(
    "u(kappa_L)",
    [(unc.propagate_kappa_l_error(a, b), ref.u_kappa_lattice(a, b))
     for a in (0.01, 0.05, 0.2)
     for b in (0.005, 0.02, 0.1)],
    1e-12,
)
worst(
    "u(ZT)",
    [(unc.propagate_zt_error(p, up, t, ut, k, uk), ref.u_zt(p, up, t, ut, k, uk))
     for p in (5e-4, 2e-3, 8e-3)
     for up in (1e-5, 1e-4)
     for t in (300.0, 800.0)
     for ut in (1.0, 5.0)
     for k in (1.0, 2.0, 4.0)
     for uk in (0.01, 0.05)],
    1e-12,
)
worst(
    "u(sigma) from geometry",
    [(unc.propagate_sigma_error(a, ua, l, ul, r, ur),
      ref.u_conductivity_from_geometry(a, ua, l, ul, r, ur))
     for a in (1e-6, 1.2e-6)
     for ua in (1e-8, 2e-8)
     for l in (1e-3, 5e-3)
     for ul in (1e-5, 5e-5)
     for r in (0.01, 0.045)
     for ur in (1e-5, 1e-4)],
    1e-12,
)
worst(
    "u(kappa) laser flash",
    [(unc.propagate_kappa_error(a, ua, c, uc, r, ur),
      ref.u_kappa_from_laser_flash(a, ua, c, uc, r, ur))
     for a in (1.2e-6,)
     for ua in (5e-8, 1e-7)
     for c in (520.0, 900.0)
     for uc in (5.0, 20.0)
     for r in (7300.0, 19300.0)
     for ur in (50.0, 200.0)],
    1e-12,
)
worst(
    "u(rho) density",
    [(unc.propagate_density_error(m, um, a, ua, t, ut),
      ref.u_density(m, um, a, ua, t, ut))
     for m in (0.5, 1.0, 5.0)
     for um in (0.005, 0.05)
     for a in (1.2e-4,)
     for ua in (1e-6, 2e-6)
     for t in (1e-3,)
     for ut in (1e-5, 5e-5)],
    1e-12,
)

# --- Dulong-Petit and device efficiency --------------------------------
worst(
    "Dulong-Petit molar heat capacity",
    [(phonon_domain.dulong_petit_molar(n), ref.dulong_petit_molar(n))
     for n in (1, 2, 5, 9)],
    1e-12,
)
worst(
    "Dulong-Petit specific heat capacity",
    [(phonon_domain.dulong_petit_specific(n, m), ref.dulong_petit_specific(n, m))
     for n in (1, 5) for m in (58.93, 489.68, 727.65)],
    1e-12,
)

from seebeck_prime.domain.device_efficiency import calculate_efficiencies  # noqa: E402

# per-key worst case over a synthetic 7-point temperature grid
for _key in ("ZT_avg", "ZT_eng", "Carnot", "Efficiency_Max", "Efficiency_Eng"):
    _pairs = []
    for _t in (np.linspace(300, 900, 7),):
        for _s in (np.linspace(2.2e-4, 1.6e-4, 7),):
            for _g in (np.linspace(1.4e5, 6e4, 7),):
                for _k in (np.linspace(1.9, 2.6, 7),):
                    _app = calculate_efficiencies(_t, _s, _g, _k, 300.0, 900.0)
                    _rfr = ref.device_efficiencies(_t, _s, _g, _k, 300.0, 900.0)
                    _pairs.append((_app[_key], _rfr[_key]))
    worst(f"Device efficiency: {_key}", _pairs, 2e-3)


# --- emit -------------------------------------------------------------
HEADER = (
    "| Calculation | Application result | Independent reference | Absolute error | "
    "Relative error | Tolerance | Result |\n"
    "|---|---|---|---|---|---|---|\n"
)

print(HEADER, end="")
failures = 0
for name, app, reference, abs_err, rel_err, tol, passed in ROWS:
    if not passed:
        failures += 1
    print(
        f"| {name} | {app:.10g} | {reference:.10g} | {abs_err:.3e} | "
        f"{rel_err:.3e} | {tol:.0e} | {'PASS' if passed else 'FAIL'} |"
    )
print(f"\n{len(ROWS)} comparisons, {failures} outside tolerance.")
sys.exit(1 if failures else 0)
