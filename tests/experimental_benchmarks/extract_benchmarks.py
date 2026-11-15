"""Build the experimental benchmark datasets from the StarryData snapshot.

Pipeline
--------
1. Download (or reuse) the StarryData ``ThermoelectricMaterials`` snapshot and
   verify its SHA-256 against the published daily manifest.
2. Extract the selected samples' curve rows **verbatim** into ``raw/`` (the
   original CSV fields, including the JSON-encoded x/y value lists).
3. Build the temperature-matched, unit-checked tables in ``processed/``.
4. Compute the *expected* results with an INDEPENDENT implementation of the
   governing equations (this file deliberately does **not** import
   Seebeck-Prime) and store them in ``expected_results/``.

Run:  python tests/experimental_benchmarks/extract_benchmarks.py
"""

from __future__ import annotations

import gzip
import hashlib
import json
import pathlib
import shutil
import sys
import urllib.request

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CACHE = pathlib.Path.home() / ".cache" / "starrydata" / "seebeck_prime"

BASE_URL = (
    "https://github.com/starrydata/starrydata_datasets/releases/latest/download"
)
MANIFEST_URL = "https://starrydata.github.io/starrydata_datasets/manifest.json"

# --- Provenance of the source snapshot ---------------------------------------
# The StarryData daily manifest (db_snapshot 2026-11-11 02:00:02 UTC+0900 JST)
# publishes these sizes and checksums for the ThermoelectricMaterials project.
SOURCE_FILES = {
    "papers": (
        "ThermoelectricMaterials_papers.csv.gz",
        1479311,
        "bc2ce54dcf85b15eff165b477c6dfa63693221021751c138eb35ce2622471e8b",
    ),
    "samples": (
        "ThermoelectricMaterials_samples.csv.gz",
        2085998,
        "8d93b72e3b32101b19a04242e1b2fefe8d3cf5b404d4b85178adb659fb714453",
    ),
    "curves": (
        "ThermoelectricMaterials_curves.csv.gz",
        25532288,
        "dc4d9eaad2b90a20b27e35e1b74533bafe704ba1a6962ae5aa27739823914734",
    ),
}

# --- Selected benchmarks -----------------------------------------------------
BENCHMARKS = {
    "b2te3_bi2te2_4se0_6cu0_006": {
        "SID": 24609,
        "sample_id": 27694,
        "family": "Bi2Te3-based",
        "composition": "Bi2Te2.4Se0.6Cu0.006",
    },
    "pbte_pbte0_95pbs0_05": {
        "SID": 29429,
        "sample_id": 37034,
        "family": "PbTe-based",
        "composition": "(PbTe)0.95(PbS)0.05",
    },
    "sige_si80ge18sb2": {
        "SID": 900,
        "sample_id": 1338,
        "family": "SiGe-based",
        "composition": "Si80Ge18Sb2",
    },
}

# Units used by the StarryData thermoelectric field (all SI).
#
# Every property that the benchmark framework relies on is listed here so
# that its unit is **validated** at extraction time rather than assumed.
# The carrier properties were added in the Phase 3 remediation: an earlier
# version of the provenance cards recorded them as cm^-3 and
# cm^2/(V.s), whereas the source data are m^-3 and m^2/(V.s) - a factor of
# 10^6 (audit finding D-02).
EXPECTED_UNITS = {
    "Seebeck coefficient": "V*K^(-1)",
    "Electrical conductivity": "ohm^(-1)*m^(-1)",
    "Thermal conductivity": "W*m^(-1)*K^(-1)",
    "Power factor": "W*m^(-1)*K^(-2)",
    "ZT": "-",
    "Lattice thermal conductivity": "W*m^(-1)*K^(-1)",
    "Carrier concentration": "m^(-3)",
    "Carrier mobility": "m^2*V^(-1)*s^(-1)",
}

LORENZ_APPLICATION = 2.44e-8   # Seebeck-Prime application-wide constant


# =============================================================================
# 1. Source snapshot
# =============================================================================
def fetch_snapshot() -> dict[str, pathlib.Path]:
    """Download the source snapshot (cached) and verify the published checksums."""
    CACHE.mkdir(parents=True, exist_ok=True)
    paths = {}
    for kind, (filename, size, sha) in SOURCE_FILES.items():
        target = CACHE / filename
        if not (target.exists() and target.stat().st_size == size):
            print(f"downloading {filename} ...", flush=True)
            url = f"{BASE_URL}/{filename}"
            request = urllib.request.Request(
                url, headers={"User-Agent": "seebeck-prime-benchmark"}
            )
            with urllib.request.urlopen(request, timeout=300) as response:
                with open(target, "wb") as handle:
                    shutil.copyfileobj(response, handle)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != sha or target.stat().st_size != size:
            raise SystemExit(f"checksum mismatch for {filename}")
        print(f"verified {filename} ({size} bytes, sha256 {sha[:16]}...)")
        paths[kind] = target
    return paths


# =============================================================================
# 2. Independent physics (deliberately NOT importing Seebeck-Prime)
# =============================================================================
def independent_pf(seebeck_v_per_k: np.ndarray, sigma_s_per_m: np.ndarray) -> np.ndarray:
    """PF = S^2 * sigma  [W/(m*K^2)]."""
    return (seebeck_v_per_k ** 2) * sigma_s_per_m


def independent_kappa_e(
    sigma_s_per_m: np.ndarray, temperature_k: np.ndarray, lorenz: float
) -> np.ndarray:
    """kappa_e = L * sigma * T  [W/(m*K)] (Wiedemann-Franz)."""
    return lorenz * sigma_s_per_m * temperature_k


def independent_kappa_l(kappa_total: np.ndarray, kappa_e: np.ndarray) -> np.ndarray:
    """kappa_L = kappa_total - kappa_e  [W/(m*K)]."""
    return kappa_total - kappa_e


def independent_zt(
    pf: np.ndarray, temperature_k: np.ndarray, kappa_total: np.ndarray
) -> np.ndarray:
    """ZT = PF * T / kappa_total  [dimensionless]."""
    return (pf * temperature_k) / kappa_total


def parse_curve(row) -> tuple[np.ndarray, np.ndarray]:
    """Decode a StarryData curve row into sorted (x, y) arrays."""
    xs = np.array([v for v in json.loads(row.x) if v is not None], dtype=float)
    ys = np.array([v for v in json.loads(row.y) if v is not None], dtype=float)
    n = min(len(xs), len(ys))
    order = np.argsort(xs[:n])
    return xs[:n][order], ys[:n][order]


# =============================================================================
# 3. Extraction
# =============================================================================
def build_benchmark(name: str, spec: dict, curves: pd.DataFrame,
                    samples: pd.DataFrame, papers: pd.DataFrame) -> dict:
    sid, sample_id = spec["SID"], spec["sample_id"]

    sub = curves[
        (curves.SID == sid)
        & (curves.sample_id == sample_id)
        & (curves.prop_x == "Temperature")
    ].copy()
    if sub.empty:
        raise SystemExit(f"{name}: no temperature-dependent curves found")

    # -- unit validation (never silently assume) -----------------------------
    for prop, unit in EXPECTED_UNITS.items():
        present = sub[sub.prop_y == prop]
        if present.empty:
            continue
        found = set(present.unit_y.unique())
        if found != {unit}:
            raise SystemExit(f"{name}: unexpected unit for '{prop}': {found} != {unit}")

    # -- raw: verbatim rows ----------------------------------------------------
    raw_dir = HERE / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{name}_curves.csv"
    sub.to_csv(raw_path, index=False)

    paper_row = papers[papers.SID == sid].iloc[0]
    sample_row = samples[(samples.SID == sid) & (samples.sample_id == sample_id)].iloc[0]

    props = {row.prop_y: row for row in sub.itertuples(index=False)}
    curves_by_prop = {prop: parse_curve(row) for prop, row in props.items()}

    # -- processed: temperature-matched tables ---------------------------------
    processed = []

    def add_grid(grid: str, source_prop: str, column: str):
        """Build one temperature-matched grid.

        The grid is the temperature grid of the published curve named by
        ``source_prop``; the measured S, sigma and kappa curves are linearly
        interpolated onto it, and the published values are written into the
        column that matches the quantity.
        """
        if source_prop not in curves_by_prop:
            return
        tx, published = curves_by_prop[source_prop]
        s_grid = np.interp(tx, *curves_by_prop["Seebeck coefficient"])
        sigma_grid = np.interp(tx, *curves_by_prop["Electrical conductivity"])
        kappa_grid = np.interp(tx, *curves_by_prop["Thermal conductivity"])
        for i in range(len(tx)):
            row = {
                "grid": grid,
                "T_K": tx[i],
                "seebeck_V_per_K": s_grid[i],
                "sigma_S_per_m": sigma_grid[i],
                "kappa_W_per_mK": kappa_grid[i],
                "published_PF_W_per_mK2": np.nan,
                "published_ZT": np.nan,
                "published_kappa_L_W_per_mK": np.nan,
            }
            row[column] = published[i]
            processed.append(row)

    add_grid("pf", "Power factor", "published_PF_W_per_mK2")
    add_grid("zt", "ZT", "published_ZT")
    add_grid("kappa_l", "Lattice thermal conductivity", "published_kappa_L_W_per_mK")

    processed_df = pd.DataFrame(processed)

    # -- expected results (independent implementation) -------------------------
    expected = []
    for grid, block in processed_df.groupby("grid", sort=False):
        t = block["T_K"].to_numpy()
        s = block["seebeck_V_per_K"].to_numpy()
        sigma = block["sigma_S_per_m"].to_numpy()
        kappa = block["kappa_W_per_mK"].to_numpy()

        pf = independent_pf(s, sigma)
        kappa_e = independent_kappa_e(sigma, t, LORENZ_APPLICATION)
        kappa_l = independent_kappa_l(kappa, kappa_e)
        zt = independent_zt(pf, t, kappa)

        for i in range(len(t)):
            expected.append({
                "grid": grid,
                "T_K": t[i],
                "pf_W_per_mK2": pf[i],
                "kappa_e_W_per_mK": kappa_e[i],
                "kappa_L_W_per_mK": kappa_l[i],
                "zt": zt[i],
                "lorenz_used_W_ohm_per_K2": LORENZ_APPLICATION,
            })
    expected_df = pd.DataFrame(expected)

    # -- reference card --------------------------------------------------------
    issued = json.loads(paper_row["issued"])["date_parts"][0]
    authors = json.loads(paper_row["author"])
    author_text = ", ".join(
        f"{a.get('given','')} {a.get('family','')}".strip() for a in authors
    )
    lines = [
        f"# {spec['composition']} ({spec['family']})",
        "",
        "## Provenance",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Benchmark id | `{name}` |",
        f"| StarryData SID / sample_id | {sid} / {sample_id} |",
        f"| Composition | {spec['composition']} |",
        f"| Sample name (paper) | {sample_row['sample_name']} |",
        f"| Publication title | {paper_row['title']} |",
        f"| Journal | {paper_row['container_title']} |",
        f"| Publication year | {issued[0]} |",
        f"| DOI | https://doi.org/{paper_row['DOI']} |",
        f"| Authors | {author_text} |",
        f"| Data source | StarryData (NIMS), project `ThermoelectricMaterials` |",
        f"| Source snapshot | db_snapshot 2026-11-11 02:00:02 UTC+0900 (JST) |",
        f"| Raw extract | `raw/{name}_curves.csv` |",
        f"| Processed data | `processed/{name}.csv` |",
        f"| Expected results | `expected_results/{name}.csv` |",
        "",
        "## Measurement conditions",
        "",
        f"- `sample_info` as recorded by StarryData: `{str(sample_row['sample_info'])[:900]}`",
        f"- Curves digitized by the Starrydata project from the figures of the",
        f"  publication (figure identifiers are stored in the raw extract:",
        f"  `figure_id`, `figure_name`).",
        "- Data type recorded by StarryData: *Experiment* (calculated datasets are",
        "  excluded from the Starrydata release).",
        "",
        "## Units (as published in the StarryData release)",
        "",
    ]
    for prop, unit in EXPECTED_UNITS.items():
        if prop in props:
            lines.append(f"- `{prop}`: `{unit}`")
    lines += [
        "",
        "## Data extraction method",
        "",
        "1. The three selected curves (Seebeck coefficient, electrical",
        "   conductivity, thermal conductivity) plus the published power factor,",
        "   ZT and lattice thermal conductivity curves are extracted verbatim from",
        "   `ThermoelectricMaterials_curves.csv.gz` (rows are copied without",
        "   modification, including the JSON-encoded value lists).",
        "2. The x/y JSON arrays are decoded into numeric columns.",
        "3. For each comparison grid (the temperature grid of the published power",
        "   factor, of the published ZT, or of the published lattice thermal",
        "   conductivity) the measured Seebeck coefficient, electrical",
        "   conductivity and thermal conductivity are linearly interpolated onto",
        "   that grid (`numpy.interp`). The published curve is therefore compared",
        "   at exactly its own temperatures - no result is interpolated.",
        "4. Expected results are computed by an independent implementation of the",
        "   governing equations inside `extract_benchmarks.py`, which does not",
        "   import Seebeck-Prime.",
        "",
        "## Attribution and licence",
        "",
        "- Underlying measurements: the publication above (© the authors).",
        "- Digitised data: StarryData project, licensed **CC BY 4.0**",
        "  (https://creativecommons.org/licenses/by/4.0/).",
        "- Please cite the publication and the Starrydata project paper when",
        "  reusing these benchmark data.",
        "",
    ]

    ref_dir = HERE / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / f"{name}.md").write_text("\n".join(lines), encoding="utf-8")

    processed_dir = HERE / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_df.to_csv(processed_dir / f"{name}.csv", index=False)

    expected_dir = HERE / "expected_results"
    expected_dir.mkdir(parents=True, exist_ok=True)
    expected_df.to_csv(expected_dir / f"{name}.csv", index=False)

    print(f"{name}: {len(sub)} curves, {len(processed_df)} processed rows, "
          f"{len(expected_df)} expected rows")
    return {
        "name": name,
        "doi": paper_row["DOI"],
        "title": paper_row["title"],
        "composition": spec["composition"],
        "grids": {g: int((processed_df.grid == g).sum()) for g in processed_df.grid.unique()},
        "properties": sorted(props),
    }


def main() -> int:
    paths = fetch_snapshot()
    curves = pd.read_csv(paths["curves"], compression="gzip")
    samples = pd.read_csv(paths["samples"], compression="gzip")
    papers = pd.read_csv(paths["papers"], compression="gzip")

    summary = []
    for name, spec in BENCHMARKS.items():
        summary.append(build_benchmark(name, spec, curves, samples, papers))

    print()
    for entry in summary:
        safe = entry["title"][:70].encode("ascii", "replace").decode("ascii")
        print(f"{entry['name']}: {entry['doi']}")
        print(f"   {entry['composition']} - {safe}")
        print(f"   grids: {entry['grids']}  properties: {len(entry['properties'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
