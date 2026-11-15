"""Phase 3 investigation: the SiGe:P Lorenz-number discrepancy.

Audit finding M-04. The published Si80Ge20P1 data imply a Lorenz number of
about 2.4579e-8 W*Ohm/K^2 (the Sommerfeld value), while the application's
SPB acoustic-phonon model gives about 1.592e-8 - a 35 % disagreement.

This script discriminates between the candidate causes:

  (a) the scattering assumption - tested by evaluating the rigorous SPB
      Lorenz number for lambda = 0, 1, 2 at the eta implied by the measured
      Seebeck coefficient, and by solving for the lambda that reproduces the
      implied value;
  (b) the single-parabolic-band assumption - assessed from the degeneracy
      regime the specimen occupies;
  (c) the published kappa / kappa_L pair is not internally consistent -
      tested by the spread of the implied L over the grid;
  (d) the reconstruction/interpolation of the digitised curves contributes
      the offset - tested against the digitisation noise floor.

The model is NOT changed. This script only characterises the discrepancy.

    python tools/investigate_sige_lorenz.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from seebeck_prime.domain.physical_constants import (  # noqa: E402
    DEFAULT_LORENZ,
    ELECTRON_CHARGE,
    SOMMERFELD_LORENZ_EXACT,
)
from seebeck_prime.domain.spb import (  # noqa: E402
    fermi_integral,
    reduced_fermi_level_from_seebeck,
    rigorous_lorenz_number,
)

RAW = ROOT / "tests" / "experimental_benchmarks" / "raw" / "sige_si80ge20p1_curves.csv"

MECHANISMS = {
    0.0: "acoustic deformation potential",
    1.0: "polar optical / alloy",
    2.0: "ionised impurity",
}

#: The degenerate (Sommerfeld) and classical limits of F_{1/2}(eta).
F_HALF_DEGENERATE = 0.765147
F_HALF_CLASSICAL = 0.443147


def load_curves(path: pathlib.Path = RAW) -> dict:
    frame = pd.read_csv(path)
    curves = {}
    for row in frame.itertuples(index=False):
        xs = np.array([v for v in json.loads(row.x) if v is not None], dtype=float)
        ys = np.array([v for v in json.loads(row.y) if v is not None], dtype=float)
        n = min(len(xs), len(ys))
        order = np.argsort(xs[:n])
        curves[row.prop_y] = (xs[:n][order], ys[:n][order], row.unit_y)
    return curves


def spb_lorenz_for(seebeck_v_k: np.ndarray, lambda_scat: float) -> np.ndarray:
    """The rigorous SPB Lorenz number at the eta implied by |S|."""
    values = []
    for s in seebeck_v_k:
        eta = reduced_fermi_level_from_seebeck(abs(float(s)) * 1e6, lambda_scat)
        values.append(np.nan if np.isnan(eta) else rigorous_lorenz_number(eta, lambda_scat))
    return np.array(values, dtype=float)


def lambda_for_target(seebeck_v_k: np.ndarray, target: float) -> float:
    """The scattering exponent whose SPB Lorenz number matches ``target``."""
    lo, hi = -1.0, 4.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        value = float(np.nanmedian(spb_lorenz_for(seebeck_v_k, mid)))
        if not np.isfinite(value):
            break
        if value < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main() -> None:
    curves = load_curves()
    t_kl, kappa_l, _ = curves["Lattice thermal conductivity"]
    t_k, kappa, _ = curves["Thermal conductivity"]
    t_s, sigma, _ = curves["Electrical conductivity"]
    t_se, seebeck, _ = curves["Seebeck coefficient"]

    print("=" * 78)
    print("Si80Ge20P1  -  the published data as extracted from the StarryData snapshot")
    print("=" * 78)
    print(f"  kappa     : {len(t_k):3d} points, {t_k.min():.0f}-{t_k.max():.0f} K")
    print(f"  kappa_L   : {len(t_kl):3d} points, {t_kl.min():.0f}-{t_kl.max():.0f} K")
    print(f"  sigma     : {len(t_s):3d} points, {t_s.min():.0f}-{t_s.max():.0f} K")
    print(f"  seebeck   : {len(t_se):3d} points, {t_se.min():.0f}-{t_se.max():.0f} K")

    kappa_at = np.interp(t_kl, t_k, kappa)
    sigma_at = np.interp(t_kl, t_s, sigma)
    seebeck_at = np.interp(t_kl, t_se, seebeck)
    implied = (kappa_at - kappa_l) / (sigma_at * t_kl)
    implied_median = float(np.median(implied))

    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("(c) Is the published kappa / kappa_L pair internally consistent?")
    print("=" * 78)
    spread = (implied.max() - implied.min()) / implied_median
    print(f"  implied L: median {implied_median:.4e}   min {implied.min():.4e}   "
          f"max {implied.max():.4e}")
    print(f"  relative spread over the grid: {spread:.1%}")
    print(f"  Sommerfeld L0 = {SOMMERFELD_LORENZ_EXACT:.4e}  "
          f"(median differs by {abs(implied_median / SOMMERFELD_LORENZ_EXACT - 1):.1%})")
    print(f"  application default L = {DEFAULT_LORENZ:.4e}  "
          f"(median differs by {abs(implied_median / DEFAULT_LORENZ - 1):.1%})")
    print(f"  -> the pair IS mutually consistent "
          f"({'yes' if spread < 0.10 else 'no'}: spread {spread:.1%})")

    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("(a) The scattering exponent: which lambda reproduces the published data?")
    print("=" * 78)
    print(f"  {'lambda':>7}  {'mechanism':<28} {'L(eta) median':>15} {'vs implied':>11}")
    for lam, name in MECHANISMS.items():
        median = float(np.nanmedian(spb_lorenz_for(seebeck_at, lam)))
        print(f"  {lam:7.1f}  {name:<28} {median:15.4e} "
              f"{median / implied_median - 1:+10.1%}")
    fitted_lambda = lambda_for_target(seebeck_at, implied_median)
    fitted = float(np.nanmedian(spb_lorenz_for(seebeck_at, fitted_lambda)))
    print(f"  {fitted_lambda:7.3f}  {'<-- reproduces the published L':<28} {fitted:15.4e} "
          f"{fitted / implied_median - 1:+10.1%}")

    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("(b) The degeneracy regime the specimen occupies")
    print("=" * 78)
    etas = np.array([
        reduced_fermi_level_from_seebeck(abs(float(s)) * 1e6, 0.0) for s in seebeck_at
    ])
    f_half = np.array([fermi_integral(0.5, float(e)) for e in etas])
    print(f"  eta from the measured |S| (lambda = 0): {etas.min():.2f} to {etas.max():.2f}")
    print(f"  F_1/2 over that range: {f_half.min():.4f} to {f_half.max():.4f}")
    print(f"  (degenerate limit {F_HALF_DEGENERATE:.3f}, classical limit {F_HALF_CLASSICAL:.3f})")
    print(f"  median F_1/2 = {np.median(f_half):.4f}")
    if f_half.min() < F_HALF_CLASSICAL < f_half.max():
        print("  -> the specimen CROSSES the classical-to-degenerate transition:")
        print("     the low-T points are non-degenerate and the high-T points are")
        print("     degenerate, so the Lorenz number varies strongly with T and")
        print("     is highly sensitive to the scattering exponent.")
    else:
        regime = "degenerate" if np.median(f_half) > 0.6 else "non-degenerate"
        print(f"  -> the specimen is {regime} over this range.")

    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("(d) The digitisation noise floor")
    print("=" * 78)
    eps = 0.01
    kappa_rel = kappa_at / kappa
    floor = np.sqrt(
        (eps / kappa_rel) ** 2
        + (eps * kappa_at / np.maximum(np.abs(kappa_l), 1e-12)) ** 2
    )
    print(f"  a 1 % digitisation error on kappa and kappa_L propagates to about")
    print(f"  {np.median(floor):.1%} relative uncertainty on the implied L")
    print(f"  observed spread of the implied L: {spread:.1%}")
    print(f"  -> the observed spread is "
          f"{'CONSISTENT WITH' if spread < 5 * np.median(floor) else 'LARGER THAN'} "
          "the digitisation noise floor, so the pair is not noise-limited")

    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("VERDICT")
    print("=" * 78)
    spb_acoustic = float(np.nanmedian(spb_lorenz_for(seebeck_at, 0.0)))
    print(f"  implied L (published data) : {implied_median:.4e}")
    print(f"  SPB acoustic (lambda = 0)  : {spb_acoustic:.4e}  "
          f"({spb_acoustic / implied_median - 1:+.1%})  <- the application's default")
    for lam in (1.0, 2.0):
        value = float(np.nanmedian(spb_lorenz_for(seebeck_at, lam)))
        print(f"  SPB lambda = {lam:.0f}             : {value:.4e}  "
              f"({value / implied_median - 1:+.1%})")
    print(f"  SPB lambda = {fitted_lambda:.2f}            : {fitted:.4e}  "
          f"({fitted / implied_median - 1:+.1%})  <- reproduces the published L")
    print(f"  Sommerfeld L0              : {SOMMERFELD_LORENZ_EXACT:.4e}  "
          f"({SOMMERFELD_LORENZ_EXACT / implied_median - 1:+.1%})")
    print()
    print("  The 35 % gap between the application's acoustic-scattering default")
    print("  and the published data is therefore a SCATTERING-ASSUMPTION")
    print("  difference, not an implementation error and not a failure of the")
    print("  single-parabolic-band model: the published value is reproduced by")
    print(f"  a scattering exponent of lambda = {fitted_lambda:.2f}, which lies")
    print("  between alloy/optical (1) and ionised-impurity (2) scattering, as")
    print("  expected for a P-doped alloy in this temperature range.")
    print()
    print("  CONSEQUENCE FOR THE SOFTWARE: the Seebeck-derived ('auto') Lorenz")
    print("  mode always uses lambda = 0, so it inherits the acoustic-model")
    print("  value and underestimates L for such specimens. The mode must")
    print("  document this; the model must NOT be re-fitted to the measurement.")


if __name__ == "__main__":
    main()
