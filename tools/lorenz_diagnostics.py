"""Lorenz-number diagnostics for every benchmark specimen that publishes kappa_L.

Two DIFFERENT quantities were conflated in the earlier validation
documents. This tool computes both, separately and correctly:

1. the **kappa_L sensitivity** - how much the computed lattice thermal
   conductivity changes if the application-wide constant L = 2.44e-8 is used
   instead of the Lorenz number implied by the published data;
2. the **SPB deviation** - how far the rigorous single-parabolic-band
   acoustic-scattering value (lambda = 0), evaluated at the measured
   Seebeck coefficient, sits from that implied Lorenz number.

Quantity (1) is what the benchmark report tabulated as "26.5 %" and
"130.6 %"; those numbers are correct *for the kappa_L sensitivity*. The
later validation tables reused them under the header "SPB deviation", which
is a mislabel. This tool prints both so the documents can be corrected.

    python tools/lorenz_diagnostics.py
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
    SOMMERFELD_LORENZ_EXACT,
)
from seebeck_prime.domain.spb import (  # noqa: E402
    reduced_fermi_level_from_seebeck,
    rigorous_lorenz_number,
)

RAW = ROOT / "tests" / "experimental_benchmarks" / "raw"

SPECIMENS = {
    "Bi2Te2.4Se0.6Cu0.006": "b2te3_bi2te2_4se0_6cu0_006",
    "(PbTe)0.95(PbS)0.05": "pbte_pbte0_95pbs0_05",
    "Si80Ge18Sb2": "sige_si80ge18sb2",
    "Si80Ge20P1": "sige_si80ge20p1",
}


def load_curves(name: str) -> dict:
    frame = pd.read_csv(RAW / f"{name}_curves.csv")
    curves = {}
    for row in frame.itertuples(index=False):
        xs = np.array([v for v in json.loads(row.x) if v is not None], dtype=float)
        ys = np.array([v for v in json.loads(row.y) if v is not None], dtype=float)
        n = min(len(xs), len(ys))
        order = np.argsort(xs[:n])
        curves[row.prop_y] = (xs[:n][order], ys[:n][order])
    return curves


def analyse(label: str, name: str) -> dict | None:
    curves = load_curves(name)
    if "Lattice thermal conductivity" not in curves:
        print(f"{label}: no published kappa_L -> nothing to analyse")
        return None

    t_kl, kappa_l = curves["Lattice thermal conductivity"]
    t_k, kappa = curves["Thermal conductivity"]
    t_s, sigma = curves["Electrical conductivity"]
    t_se, seebeck = curves["Seebeck coefficient"]

    kappa_at = np.interp(t_kl, t_k, kappa)
    sigma_at = np.interp(t_kl, t_s, sigma)
    seebeck_at = np.interp(t_kl, t_se, seebeck)

    implied = (kappa_at - kappa_l) / (sigma_at * t_kl)
    implied_median = float(np.median(implied))

    # (1) the kappa_L sensitivity to the application-wide constant
    kappa_l_with_default = kappa_at - DEFAULT_LORENZ * sigma_at * t_kl
    sensitivity = np.abs(kappa_l_with_default / kappa_l - 1.0)

    # (2) the SPB acoustic deviation
    spb = np.array([
        rigorous_lorenz_number(
            reduced_fermi_level_from_seebeck(abs(float(s)) * 1e6, 0.0), 0.0
        )
        for s in seebeck_at
    ])
    spb_deviation = spb / implied - 1.0

    return {
        "label": label,
        "implied": implied_median,
        "spread": float((implied.max() - implied.min()) / implied_median),
        "kappa_l_sensitivity": float(sensitivity.max()),
        "spb_median": float(np.median(spb)),
        "spb_deviation_min": float(spb_deviation.min()),
        "spb_deviation_max": float(spb_deviation.max()),
        "sommerfeld_deviation": float(SOMMERFELD_LORENZ_EXACT / implied_median - 1.0),
    }


def main() -> None:
    results = []
    for label, name in SPECIMENS.items():
        result = analyse(label, name)
        if result:
            results.append(result)

    print("=" * 92)
    print("LORENZ DIAGNOSTICS - two different quantities, reported separately")
    print("=" * 92)
    print()
    header = (
        f"{'specimen':<24} {'L implied':>12} {'spread':>8} "
        f"{'kappa_L sens.':>14} {'SPB L':>12} {'SPB deviation':>20}"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['label']:<24} {r['implied']:12.4e} {r['spread']:7.1%} "
            f"{r['kappa_l_sensitivity']:13.1%} {r['spb_median']:12.4e} "
            f"{r['spb_deviation_min']:+9.1%} .. {r['spb_deviation_max']:+7.1%}"
        )
    print()
    print(f"{'specimen':<24} {'Sommerfeld L0 vs implied':>26}")
    print("-" * 52)
    for r in results:
        print(f"{r['label']:<24} {r['sommerfeld_deviation']:+25.1%}")
    print()
    print("Reading:")
    print("  * 'kappa_L sens.' is the change in the computed lattice thermal")
    print("    conductivity when the application-wide constant L = 2.44e-8 is used")
    print("    instead of the implied value. It is the quantity the benchmark")
    print("    report tabulated as 26.5 % and 130.6 %.")
    print("  * 'SPB deviation' is the gap between the rigorous acoustic-scattering")
    print("    SPB value and the implied Lorenz number. It is a different (and")
    print("    smaller) quantity, and it is what the validation documents must")
    print("    quote.")
    print("  * 'spread' is the internal consistency of the published kappa/kappa_L")
    print("    pair; where it is large the implied Lorenz number is itself")
    print("    unreliable, which is why the PbTe comparison is UNVERIFIED.")


if __name__ == "__main__":
    main()
