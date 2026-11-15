"""Phase X: build the scientific benchmark material-family registry.

Surveys the StarryData ``ThermoelectricMaterials`` snapshot for the seven
material families requested by the validation plan and records what is
actually available (sample counts, paper counts, DOIs, published curve
types).  Nothing is fabricated: every entry is derived from the snapshot.

    python tools/survey_material_families.py
"""
from __future__ import annotations

import collections
import pathlib
import re
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

CACHE = pathlib.Path.home() / ".cache" / "starrydata" / "seebeck_prime"

samples = pd.read_csv(CACHE / "ThermoelectricMaterials_samples.csv.gz", compression="gzip")
papers = pd.read_csv(CACHE / "ThermoelectricMaterials_papers.csv.gz", compression="gzip")
curves = pd.read_csv(CACHE / "ThermoelectricMaterials_curves.csv.gz", compression="gzip")

doi_of = papers.set_index("SID")["DOI"]
title_of = papers.set_index("SID")["title"]

FAMILIES = {
    "SiGe": r"Si\d*\.?\d*Ge|SiGe",
    "Mg2Si": r"Mg2Si|Mg2?Si",
    "Mg2Sn": r"Mg2Sn|Mg2?Sn",
    "Bi2Te3-based": r"Bi2Te|Bi2?Te",
    "PbTe": r"PbTe|Pb2?Te",
    "SnSe": r"SnSe|Sn1?Se",
    "CaMnO3-based": r"CaMnO|CaMn",
}

CURVE_TYPES_OF_INTEREST = [
    "Seebeck coefficient",
    "Electrical conductivity",
    "Electrical resistivity",
    "Thermal conductivity",
    "Lattice thermal conductivity",
    "Power factor",
    "ZT",
    "Carrier concentration",
    "Carrier mobility",
    "Hall coefficient",
]

print("=" * 96)
print("PHASE X - SCIENTIFIC BENCHMARK MATERIAL FAMILIES")
print("=" * 96)
print(f"Snapshot: ThermoelectricMaterials (StarryData), samples={len(samples)}, "
      f"papers={len(papers)}, curves={len(curves)}")
print()

summary_rows = []
detail_blocks = []

for family, pattern in FAMILIES.items():
    rx = re.compile(pattern)
    hits = samples[samples["composition"].astype(str).str.contains(rx, na=False, regex=True)]
    sids = sorted(hits["SID"].unique())

    sub = curves[curves["SID"].isin(sids) & (curves["prop_x"] == "Temperature")]
    counts = collections.Counter(sub["prop_y"])

    print("-" * 96)
    print(f"{family}: {len(hits)} samples, {len(sids)} distinct publications")
    print("-" * 96)
    for prop in CURVE_TYPES_OF_INTEREST:
        n = counts.get(prop, 0)
        if n:
            print(f"    {prop:<32s} {n:5d} published curves")

    # pick the publications that publish the most of the needed quantities
    per_paper = collections.defaultdict(set)
    for sid, prop in zip(sub["SID"], sub["prop_y"]):
        per_paper[sid].add(prop)

    def score(sid):
        have = per_paper.get(sid, set())
        return (
            sum(1 for p in ("Seebeck coefficient", "Thermal conductivity",
                            "Power factor", "ZT") if p in have),
            sum(1 for p in ("Carrier concentration", "Carrier mobility") if p in have),
            len(have),
        )

    best = sorted(sids, key=score, reverse=True)[:8]
    detail_blocks.append((family, best, per_paper, len(hits), len(sids)))

    summary_rows.append(
        {
            "family": family,
            "samples": len(hits),
            "papers": len(sids),
            "seebeck": counts.get("Seebeck coefficient", 0),
            "conductivity": counts.get("Electrical conductivity", 0),
            "resistivity": counts.get("Electrical resistivity", 0),
            "kappa": counts.get("Thermal conductivity", 0),
            "kappa_l": counts.get("Lattice thermal conductivity", 0),
            "pf": counts.get("Power factor", 0),
            "zt": counts.get("ZT", 0),
            "carrier_n": counts.get("Carrier concentration", 0),
            "carrier_mu": counts.get("Carrier mobility", 0),
        }
    )

print()
print("=" * 96)
print("SUMMARY")
print("=" * 96)
header = ["family", "samples", "papers", "S", "sigma", "rho", "kappa", "kappa_L",
          "PF", "ZT", "n_H", "mu_H"]
keys = ["family", "samples", "papers", "seebeck", "conductivity", "resistivity",
        "kappa", "kappa_l", "pf", "zt", "carrier_n", "carrier_mu"]
print("| " + " | ".join(header) + " |")
print("|" + "|".join(["---"] * len(header)) + "|")
for row in summary_rows:
    print("| " + " | ".join(str(row[k]) for k in keys) + " |")

print()
print("=" * 96)
print("REPRESENTATIVE PUBLICATIONS (most complete coverage per family)")
print("=" * 96)
for family, best, per_paper, n_samples, n_papers in detail_blocks:
    print()
    print(f"### {family}  ({n_samples} samples / {n_papers} publications)")
    for sid in best[:6]:
        have = sorted(per_paper.get(sid, set()))
        print(f"  SID {sid:<8} DOI {doi_of.get(sid, '')}")
        print(f"      title: {str(title_of.get(sid, ''))[:100]}")
        print(f"      published vs T: {', '.join(have) if have else '(none vs T)'}")
