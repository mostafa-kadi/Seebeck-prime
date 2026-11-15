"""Phase 3 assessment: the degenerate-semiconductor (PbTe) Lorenz number.

Audit finding M-04b / limitation 3.2.1. The shipped validation documents
tabulated a "130.6 %" figure for this specimen under the header *SPB
deviation*. That figure is in fact the **kappa_L sensitivity** - how much
the computed lattice thermal conductivity changes when the application-wide
constant L = 2.44e-8 is used instead of the implied value. The two quantities
are different, and this tool measures both (see also
``tools/lorenz_diagnostics.py``).

The validation brief is explicit: *"Do not implement Kane, Dingle, or
multiband models merely to improve agreement. First assess the mathematical
requirements, literature basis, required inputs, and validation data."*

This script therefore only **characterises** the problem: it measures the
degeneracy regime, the size of the deviation, and what a corrected model
would require. It changes nothing.

    python tools/assess_degenerate_lorenz.py
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

RAW = ROOT / "tests" / "experimental_benchmarks" / "raw" / "pbte_pbte0_95pbs0_05_curves.csv"

K_B_OVER_E = 1.380649e-23 / ELECTRON_CHARGE


def load_curves(path: pathlib.Path = RAW) -> dict:
    frame = pd.read_csv(path)
    curves = {}
    for row in frame.itertuples(index=False):
        xs = np.array([v for v in json.loads(row.x) if v is not None], dtype=float)
        ys = np.array([v for v in json.loads(row.y) if v is not None], dtype=float)
        n = min(len(xs), len(ys))
        order = np.argsort(xs[:n])
        curves[row.prop_y] = (xs[:n][order], ys[:n][order])
    return curves


def main() -> None:
    curves = load_curves()
    t_kl, kappa_l = curves["Lattice thermal conductivity"]
    t_k, kappa = curves["Thermal conductivity"]
    t_s, sigma = curves["Electrical conductivity"]
    t_se, seebeck = curves["Seebeck coefficient"]

    kappa_at = np.interp(t_kl, t_k, kappa)
    sigma_at = np.interp(t_kl, t_s, sigma)
    seebeck_at = np.interp(t_kl, t_se, seebeck)
    implied = (kappa_at - kappa_l) / (sigma_at * t_kl)

    print("=" * 78)
    print("PbTe (PbTe)0.95(PbS)0.05  -  degenerate-semiconductor regime")
    print("=" * 78)
    print(f"  kappa   : {len(t_k):3d} points, {t_k.min():.0f}-{t_k.max():.0f} K")
    print(f"  kappa_L : {len(t_kl):3d} points, {t_kl.min():.0f}-{t_kl.max():.0f} K")
    print(f"  seebeck : {len(t_se):3d} points, {t_se.min():.0f}-{t_se.max():.0f} K")

    print()
    print("--- 1. The published pair is NOT internally consistent ---")
    spread = (implied.max() - implied.min()) / np.median(implied)
    print(f"  implied L: median {np.median(implied):.4e}  "
          f"range {implied.min():.4e} - {implied.max():.4e}")
    print(f"  relative spread: {spread:.1%}")
    print(f"  Sommerfeld L0 = {SOMMERFELD_LORENZ_EXACT:.4e}")
    print("  -> a single Lorenz number cannot reproduce both published curves;")
    print("     the source data, not the calculation, limit this comparison.")
    print("     This is why the benchmark comparison is reported UNVERIFIED.")

    print()
    print("--- 2. The degeneracy regime ---")
    etas = np.array([
        reduced_fermi_level_from_seebeck(abs(float(s)) * 1e6, 0.0) for s in seebeck_at
    ])
    f_half = np.array([fermi_integral(0.5, float(e)) for e in etas])
    print(f"  eta from the measured |S|: {etas.min():.2f} to {etas.max():.2f}")
    print(f"  F_1/2: {f_half.min():.4f} to {f_half.max():.4f} "
          f"(degenerate limit 0.765, classical limit 0.443)")
    print(f"  median eta = {np.median(etas):.2f}")
    if etas.min() > 2.0:
        print("  -> the specimen is STRONGLY degenerate over the whole range:")
        print("     the parabolic-band dispersion is the approximation in doubt.")

    print()
    print("--- 3. Size of the deviations ---")
    acoustic = np.array([
        rigorous_lorenz_number(reduced_fermi_level_from_seebeck(abs(float(s)) * 1e6, 0.0), 0.0)
        for s in seebeck_at
    ])
    deviation = acoustic / implied - 1.0
    kappa_l_with_default = kappa_at - DEFAULT_LORENZ * sigma_at * t_kl
    sensitivity = np.abs(kappa_l_with_default / kappa_l - 1.0)
    print(f"  SPB acoustic L: {acoustic.min():.4e} to {acoustic.max():.4e}")
    print(f"  SPB deviation from the implied L : {deviation.min():+.1%} to {deviation.max():+.1%}")
    print(f"  kappa_L sensitivity to L = 2.44e-8: up to {sensitivity.max():.1%}")
    print(f"  Sommerfeld L0 vs the implied L   : "
          f"{SOMMERFELD_LORENZ_EXACT / np.median(implied) - 1:+.1%}")
    print("  (the 130.6 % quoted in the earlier documents is the kappa_L")
    print("   sensitivity, not the SPB deviation - the two were conflated)")

    print()
    print("--- 4. What a corrected model would require ---")
    print("  A Kane (non-parabolic) dispersion or a Dingle (band-narrowing)")
    print("  correction needs, at minimum:")
    print("    (i)   the band-edge effective mass m_d* AND the band-edge")
    print("          Seebeck coefficient S_0 of the material - neither is")
    print("          published in the benchmark datasets;")
    print("    (ii)  a band-gap parameter Eg(T) - not published;")
    print("    (iii) a justified constant for the band-narrowing factor;")
    print("    (iv)  an independent validation reference for the corrected L.")
    print()
    print("  Availability in the benchmark data:")
    available = {
        "Seebeck coefficient": "yes (temperature dependent)",
        "Electrical conductivity": "yes",
        "Thermal conductivity": "yes",
        "Lattice thermal conductivity": "yes",
        "Hall carrier concentration": "no",
        "Hall mobility": "no",
        "Effective mass": "no",
        "Band gap": "no",
    }
    for item, status in available.items():
        print(f"    {item:<32} {status}")
    print()
    print("  Conclusion: the inputs required to evaluate a Kane/Dingle model")
    print("  are NOT available in the benchmark data, and no independent")
    print("  reference exists against which such a model could be validated.")
    print("  Implementing one would therefore be an unvalidated model change,")
    print("  which the validation brief forbids. The honest action is to")
    print("  document the limit and to keep the benchmark comparison marked")
    print("  UNVERIFIED.")
    print()
    print("  What WOULD make it possible, in order of cost:")
    print("    1. a published Hall carrier concentration and mobility for the")
    print("       specimen, which fixes m_d* empirically;")
    print("    2. an independent measurement of L (not derived by differencing")
    print("       published kappa and kappa_L, which is what makes the present")
    print("       pair inconsistent);")
    print("    3. the material's band gap over the measured range.")


if __name__ == "__main__":
    main()
