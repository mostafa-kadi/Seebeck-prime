"""Headless example: compute transport properties from a CSV dataset.

This demonstrates the GUI-independent scientific API without launching the
desktop application. It reads ``example_dataset.csv`` (a synthetic,
Bi2Te3-like dataset — see ``README.md`` in this directory), computes the
derived transport properties with the domain layer, prints a summary table,
and optionally writes the results to a CSV file.

Usage (from the repository root):

    python examples/headless_analysis.py                 # print only
    python examples/headless_analysis.py results.csv     # print + write CSV
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
for candidate in (REPO_ROOT, REPO_ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from seebeck_prime.domain import (
    calculate_kappa_e,
    calculate_kappa_l,
    calculate_pf,
    calculate_zt,
)

DATASET = Path(__file__).resolve().parent / "example_dataset.csv"

COLUMNS = [
    "Temperature (K)",
    "Seebeck (V/K)",
    "Electrical Conductivity (S/m)",
    "Thermal Conductivity (W/(m*K))",
]


def read_dataset(path: Path = DATASET):
    """Read the example dataset into column lists (SI base units)."""
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        data = {name: [] for name in reader.fieldnames or COLUMNS}
        for row in reader:
            for name, value in row.items():
                data[name].append(float(value))
    return data


def compute_properties(data):
    """Compute PF, kappa_e, kappa_l, and ZT with the domain layer."""
    import numpy as np

    temperature = np.asarray(data[COLUMNS[0]], dtype=float)
    seebeck = np.asarray(data[COLUMNS[1]], dtype=float)
    conductivity = np.asarray(data[COLUMNS[2]], dtype=float)
    kappa_total = np.asarray(data[COLUMNS[3]], dtype=float)

    pf = calculate_pf(seebeck, conductivity)
    kappa_e = calculate_kappa_e(conductivity, temperature)
    kappa_l = calculate_kappa_l(kappa_total, kappa_e)
    zt = calculate_zt(pf, temperature, kappa_total)
    return {
        "PF (W/(m*K^2))": [float(v) for v in pf],
        "kappa_e (W/(m*K))": [float(v) for v in kappa_e],
        "kappa_l (W/(m*K))": [float(v) for v in kappa_l],
        "ZT": [float(v) for v in zt],
    }


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    data = read_dataset()
    results = compute_properties(data)

    header = list(data) + list(results)
    print("\t".join(header))
    for index in range(len(data[COLUMNS[0]])):
        row = [data[name][index] for name in data] + [
            results[name][index] for name in results
        ]
        print("\t".join(f"{value:.6g}" for value in row))

    if argv:
        output_path = Path(argv[0])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            for index in range(len(data[COLUMNS[0]])):
                writer.writerow(
                    [data[name][index] for name in data]
                    + [results[name][index] for name in results]
                )
        print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
