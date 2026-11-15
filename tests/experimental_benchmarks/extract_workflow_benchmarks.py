"""Extend the benchmark extraction: carrier data, a kappa_e dataset, instrument files.

Adds
----
* Benchmark ``sige_si80ge20p1`` (SID 24041 / sample 35339) which publishes
  electronic and lattice thermal conductivity, carrier concentration and
  carrier mobility - the only candidate with published electronic kappa.
* ``carrier_concentration`` and ``carrier_mobility`` grids for every
  benchmark that publishes them.
* Instrument-format reconstructions (four-probe, raw Seebeck, laser flash)
  built from the published Bi2Te3 curves, used to exercise the importers.
  The reconstructions are *derived* from published data and are labelled as
  such; they are not raw instrument files.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from extract_benchmarks import (  # noqa: E402
    BENCHMARKS,
    CACHE,
    EXPECTED_UNITS,
    HERE,
    LORENZ_APPLICATION,
    independent_kappa_e,
    independent_kappa_l,
    independent_pf,
    independent_zt,
    parse_curve,
)

NEW_BENCHMARK = {
    "sige_si80ge20p1": {
        "SID": 24041,
        "sample_id": 35339,
        "family": "SiGe-based",
        "composition": "Si80Ge20P1",
        "doi": "10.1021/acsami.9b20090",
    },
}

EXTRA_UNITS = {
    # The StarryData release publishes the carrier quantities in SI:
    # m^(-3) and m^2*V^(-1)*s^(-1). The processed dataset converts them to
    # the conventional experimental units that its column names declare
    # (cm^-3 and cm^2/(V.s)). Audit finding D-02: the units were previously
    # recorded as cm^-3 / cm^2/(V.s) while the values written into the
    # processed dataset were the unconverted SI values, so the column names
    # understated the stored magnitudes by 10^6 and 10^4.
    "Carrier concentration": "m^(-3)",
    "Carrier mobility": "m^2*V^(-1)*s^(-1)",
    "Electronic thermal conductivity": "W*m^(-1)*K^(-1)",
}

#: The unit of each property as published in the StarryData release. The
#: extraction validates every property it uses against this table instead of
#: assuming it.
EXPECTED_UNITS_PUBLISHED = {
    "Seebeck coefficient": "V*K^(-1)",
    "Electrical conductivity": "ohm^(-1)*m^(-1)",
    "Thermal conductivity": "W*m^(-1)*K^(-1)",
    "Power factor": "W*m^(-1)*K^(-2)",
    "ZT": "-",
    "Lattice thermal conductivity": "W*m^(-1)*K^(-1)",
    "Electronic thermal conductivity": "W*m^(-1)*K^(-1)",
    "Carrier concentration": "m^(-3)",
    "Carrier mobility": "m^2*V^(-1)*s^(-1)",
}

#: Conversion of a published SI carrier quantity into the unit that the
#: processed-dataset column names declare.
CARRIER_CONCENTRATION_TO_CM3 = 1e-6
CARRIER_MOBILITY_TO_CM2_VS = 1e4


def load_sources():
    curves = pd.read_csv(CACHE / "ThermoelectricMaterials_curves.csv.gz", compression="gzip")
    samples = pd.read_csv(CACHE / "ThermoelectricMaterials_samples.csv.gz", compression="gzip")
    papers = pd.read_csv(CACHE / "ThermoelectricMaterials_papers.csv.gz", compression="gzip")
    return curves, samples, papers


def build(name, spec, curves, samples, papers):
    sid, sample_id = spec["SID"], spec["sample_id"]
    sub = curves[(curves.SID == sid) & (curves.sample_id == sample_id)
                 & (curves.prop_x == "Temperature")].copy()
    if sub.empty:
        raise SystemExit(f"{name}: no curves")

    raw_dir = HERE / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    sub.to_csv(raw_dir / f"{name}_curves.csv", index=False)

    props = {row.prop_y: row for row in sub.itertuples(index=False)}
    curves_by_prop = {prop: parse_curve(row) for prop, row in props.items()}

    # -- unit validation (never silently assume) -----------------------------
    for prop, expected in EXPECTED_UNITS_PUBLISHED.items():
        present = sub[sub.prop_y == prop]
        if present.empty:
            continue
        found = set(present.unit_y.unique())
        if found != {expected}:
            raise SystemExit(
                f"{name}: unexpected published unit for '{prop}': "
                f"{found} != {expected}"
            )

    processed = []
    grid_specs = [
        ("pf", "Power factor", "published_PF_W_per_mK2"),
        ("zt", "ZT", "published_ZT"),
        ("kappa_l", "Lattice thermal conductivity", "published_kappa_L_W_per_mK"),
        ("kappa_e", "Electronic thermal conductivity", "published_kappa_e_W_per_mK"),
        ("carrier_concentration", "Carrier concentration", "published_carrier_concentration_cm3"),
        ("carrier_mobility", "Carrier mobility", "published_carrier_mobility_cm2_Vs"),
    ]
    for grid, prop, column in grid_specs:
        if prop not in curves_by_prop:
            continue
        tx, published = curves_by_prop[prop]
        # The carrier quantities are published in SI but the processed
        # dataset's columns declare the conventional experimental units, so
        # they are converted here. The raw extract keeps the published SI
        # values verbatim (audit finding D-02).
        if prop == "Carrier concentration":
            published = published * CARRIER_CONCENTRATION_TO_CM3
        elif prop == "Carrier mobility":
            published = published * CARRIER_MOBILITY_TO_CM2_VS
        s_grid = np.interp(tx, *curves_by_prop["Seebeck coefficient"])
        sigma_grid = np.interp(tx, *curves_by_prop["Electrical conductivity"])
        kappa_grid = np.interp(tx, *curves_by_prop["Thermal conductivity"])
        for i in range(len(tx)):
            row = {
                "grid": grid, "T_K": tx[i],
                "seebeck_V_per_K": s_grid[i],
                "sigma_S_per_m": sigma_grid[i],
                "kappa_W_per_mK": kappa_grid[i],
                "published_PF_W_per_mK2": np.nan,
                "published_ZT": np.nan,
                "published_kappa_L_W_per_mK": np.nan,
                "published_kappa_e_W_per_mK": np.nan,
                "published_carrier_concentration_cm3": np.nan,
                "published_carrier_mobility_cm2_Vs": np.nan,
            }
            row[column] = published[i]
            processed.append(row)

    processed_df = pd.DataFrame(processed)

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
                "grid": grid, "T_K": t[i], "pf_W_per_mK2": pf[i],
                "kappa_e_W_per_mK": kappa_e[i], "kappa_L_W_per_mK": kappa_l[i],
                "zt": zt[i], "lorenz_used_W_ohm_per_K2": LORENZ_APPLICATION,
            })
    expected_df = pd.DataFrame(expected)

    (HERE / "processed").mkdir(exist_ok=True)
    (HERE / "expected_results").mkdir(exist_ok=True)
    processed_df.to_csv(HERE / "processed" / f"{name}.csv", index=False)
    expected_df.to_csv(HERE / "expected_results" / f"{name}.csv", index=False)

    paper_row = papers[papers.SID == sid].iloc[0]
    (HERE / "references" / f"{name}.md").write_text(
        f"# {spec['composition']} ({spec['family']})\n\n"
        f"## Provenance\n\n"
        f"| Item | Value |\n|---|---|\n"
        f"| Benchmark id | `{name}` |\n"
        f"| StarryData SID / sample_id | {sid} / {sample_id} |\n"
        f"| Composition | {spec['composition']} |\n"
        f"| DOI | https://doi.org/{paper_row['DOI']} |\n"
        f"| Publication title | {paper_row['title']} |\n"
        f"| Journal | {paper_row['container_title']} |\n"
        f"| Data source | StarryData (NIMS), project `ThermoelectricMaterials` |\n"
        f"| Source snapshot | db_snapshot 2026-11-11 02:00:02 UTC+0900 (JST) |\n"
        f"| Raw extract | `raw/{name}_curves.csv` |\n\n"
        f"## Published properties in this dataset\n\n"
        + "".join(f"- {p} (`{units}`)\n" for p, units in
                  {**EXPECTED_UNITS, **EXTRA_UNITS}.items() if p in props)
        + "\nThe units above are the units **as published** in the StarryData\n"
          "release and are the units of the raw extract. The processed dataset\n"
          "converts the two carrier quantities into the conventional\n"
          "experimental units that its column names declare:\n\n"
          "- `published_carrier_concentration_cm3`: published m^-3 divided by 10^6\n"
          "- `published_carrier_mobility_cm2_Vs`: published m^2/(V.s) multiplied by 10^4\n\n"
          "## Licence and attribution\n\n"
          "- Digitised data: StarryData project, licensed **CC BY 4.0**.\n"
          "- The measurements belong to the publication above (© the authors).\n",
        encoding="utf-8",
    )
    print(f"{name}: {len(sub)} curves, grids {sorted(processed_df.grid.unique())}")


def build_instrument_reconstructions(curves):
    """Rebuild instrument-format files from the published Bi2Te3 curves.

    These files are **reconstructions**, not raw instrument records: they are
    derived from the published Seebeck/conductivity/thermal-conductivity
    curves of the Bi2Te3 benchmark so that the importers can be exercised
    end-to-end against published values. The reconstruction is documented in
    `raw/instrument/README.md`.
    """
    spec = {"SID": 24609, "sample_id": 27694}
    sub = curves[(curves.SID == spec["SID"]) & (curves.sample_id == spec["sample_id"])
                 & (curves.prop_x == "Temperature")]
    props = {row.prop_y: parse_curve(row) for row in sub.itertuples(index=False)}
    ts, ss = props["Seebeck coefficient"]
    tg, sg = props["Electrical conductivity"]
    tk, kk = props["Thermal conductivity"]

    out_dir = HERE / "raw" / "instrument"
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- four-probe instrument export: T, sigma [S/cm], S [uV/K] ---------------
    fp = pd.DataFrame({
        "Temperature (K)": ts,
        "Conductivity (S/cm)": np.interp(ts, tg, sg) / 100.0,
        "Seebeck (uV/K)": ss * 1e6,
    })
    fp.to_csv(out_dir / "four_probe_instrument.csv", index=False)

    # --- raw Seebeck export: grouped dT/dV pairs (mV), signed ---------------
    # Several temperature differences per nominal temperature are required:
    # the importer fits dV against dT within each temperature group, so a
    # group with a single dT carries no slope. dV carries the sign of the
    # measured Seebeck coefficient, so the sign convention is exercised.
    rows = []
    for t, s in zip(ts, ss):
        for d_t in (5.0, 10.0, 20.0):
            rows.append({
                "Temperature (K)": t,
                "delta_k": d_t,
                "delta_mv": s * 1e6 * d_t / 1000.0,
            })
    raw_sb = pd.DataFrame(rows).sort_values("Temperature (K)")
    raw_sb.to_csv(out_dir / "raw_seebeck_instrument.csv", index=False)

    # --- laser-flash export: T, kappa, alpha [mm^2/s], Cp [J/(g*K)] ---------
    # alpha and Cp are reconstructed from the published kappa using the
    # documented density assumption (5.6 g/cm^3 for a Bi2Te3-based alloy):
    #     kappa = alpha * Cp * rho  =>  alpha[mm^2/s] = kappa / (Cp * rho)
    density_g_cm3 = 5.6
    cp_j_g_k = 0.20
    alpha_mm2s = kk / (cp_j_g_k * density_g_cm3)
    lf = pd.DataFrame({
        "Temperature (K)": tk,
        "Thermal Conductivity (W/mK)": kk,
        "Diffusivity (mm2/s)": alpha_mm2s,
        "Specific Heat (J/g.K)": cp_j_g_k,
    })
    lf.to_csv(out_dir / "laser_flash_instrument.csv", index=False)

    readme = """# Instrument-format reconstructions

These files are **reconstructions**, not raw instrument records. They were
generated by `extract_workflow_benchmarks.py` from the *published* curves of
the Bi2Te3 benchmark (DOI 10.1007/s10854-019-01874-0) so that the
application's instrument importers can be exercised end-to-end and their
output compared with the published values.

| File | Format consumed by | Reconstruction |
|---|---|---|
| `four_probe_instrument.csv` | `process_four_probe_table` | Temperature [K], Conductivity [S/cm], Seebeck [uV/K] taken directly from the published curves and converted to the instrument's display units |
| `raw_seebeck_instrument.csv` | `process_raw_seebeck_table` | Groups of three (dT = 5, 10, 20 K, dV) pairs per temperature; dV = S * dT carries the **sign** of the published Seebeck coefficient, so the sign convention is exercised. Several dT values per temperature are required because the importer fits dV against dT within each group. |
| `laser_flash_instrument.csv` | `process_laser_flash_table` | Temperature [K] and Thermal Conductivity [W/mK] from the published curve, plus Diffusivity [mm^2/s] and Specific Heat [J/(g*K)] reconstructed from the published kappa with the documented density assumption rho = 5.6 g/cm^3 and Cp = 0.20 J/(g*K): alpha = kappa / (Cp * rho) |

**No new measurements are introduced.** The reconstructions only change the
*format* in which the published values are presented, never their values.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")
    return out_dir


def main():
    curves, samples, papers = load_sources()
    for name, spec in {**BENCHMARKS, **NEW_BENCHMARK}.items():
        build(name, spec, curves, samples, papers)
    build_instrument_reconstructions(curves)
    return 0


if __name__ == "__main__":
    sys.exit(main())
