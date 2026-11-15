"""Pure measurement-table processing workflows.

These functions transform raw instrument tables (four-probe, raw Seebeck,
laser flash) into the application's normalized per-temperature DataFrames.
They are file-format agnostic: raw tables are provided by the caller
(normally through the ``TabularDataStore`` port in ``services.py``).

Scientific behavior is intentionally preserved from the previous
``ThermoelectricAnalyzer`` methods; equations delegate to Domain.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
from scipy.stats import linregress as _linregress

from seebeck_prime.domain.analysis import mad_filter
from seebeck_prime.application.data_mapping import find_column_index


# ── Column-mapping helper ────────────────────────────────────────────────

def find_column(df: pd.DataFrame, aliases: list[str]) -> object | None:
    """Return the first source column matching one of the aliases.

    The matching rules are shared with the Application data mapper so that the
    two cannot diverge (audit issues SE-031 / SE-032): aliases are matched
    case-insensitively and physically implausible matches - a thermal
    conductivity column for the electrical-conductivity slot, a temperature
    column for "k" - are rejected.
    """
    index = find_column_index(df.columns, aliases)
    if index is None:
        return None
    return df.columns[index]


def _standard_error(values: np.ndarray) -> float:
    """Standard uncertainty of the *mean* of a set of repeated readings.

    The group statistic reported by this module is the arithmetic mean of N
    repeats, so its standard uncertainty is the sample standard deviation
    divided by sqrt(N) - not the spread of the individual readings.
    Reporting s instead of s/sqrt(N) overstates the uncertainty of the mean
    by a factor sqrt(N) (audit issue SE-033). For a single reading there is no
    information about the mean's uncertainty, so 0.0 is returned (the
    pre-existing convention) and the caller is expected to supply a
    measurement-level uncertainty.
    """
    values = np.asarray(values, dtype=float)
    if values.size < 2:
        return 0.0
    return float(values.std(ddof=1) / np.sqrt(values.size))


# ── Temperature unit handling ───────────────────────────────────────────────

def _temperature_source_unit(source_header: str | None) -> str | None:
    """Return the temperature unit declared by a raw-file column header.

    Returns "K" or "degC" when the header declares the unit, otherwise None
    (the unit has to be inferred from the data).
    """
    if not source_header:
        return None
    header = str(source_header).strip().lower()
    if "(k)" in header or "[k]" in header or header.endswith(" k"):
        return "K"
    if "°c" in header or "(c)" in header or "[c]" in header or "degc" in header:
        return "degC"
    return None


def _to_kelvin(values: np.ndarray, source_header: str | None) -> np.ndarray:
    """Convert a raw temperature column to Kelvin.

    The unit declared by the source header takes precedence; only when the
    header does not declare one is the unit inferred from the magnitude of the
    data (legacy behaviour). The declared-unit rule removes the ambiguity for
    files exported by this application, whose temperature column is always
    written in Kelvin.

    Audit references: docs/SCIENTIFIC_EQUATION_AUDIT.md, issues SE-026 / SE-027.
    """
    values = np.asarray(values, dtype=float)
    declared = _temperature_source_unit(source_header)
    if declared == "K":
        return values
    if declared == "degC":
        return values + 273.15
    # No declared unit: fall back to the magnitude heuristic.
    if values.size == 0:
        return values
    return values if np.mean(values) > 250 else values + 273.15


# ── Four-probe processing ────────────────────────────────────────────────

def process_four_probe_table(raw_df: pd.DataFrame | None) -> pd.DataFrame | None:
    """Normalize a raw four-probe table into per-temperature properties."""
    if raw_df is None:
        return None
    df = raw_df.copy()
    FP_GROUPS = {
        "T_C":      ["temperature", "temp", "t"],
        "sigma_Scm": ["conductivity", "sigma", "σ", "s/cm"],
        "S_uVK":    ["seebeck", "alpha", "α", "uV/K", "µV/K"],
    }
    normalized_cols = {}
    for target, aliases in FP_GROUPS.items():
        col = find_column(df, aliases)
        if col is not None:
            normalized_cols[target] = col

    if all(k in normalized_cols for k in ["T_C", "sigma_Scm", "S_uVK"]):
        source_header = normalized_cols["T_C"]
        df = df[[normalized_cols["T_C"], normalized_cols["sigma_Scm"], normalized_cols["S_uVK"]]].copy()
        df.columns = ["T_C", "sigma_Scm", "S_uVK"]
    else:
        # Fixed-layout instrument export: the header row is row 3.
        source_header = str(raw_df.iloc[3, 0]) if raw_df.shape[0] > 3 else None
        # The fixed layout needs four columns; a shorter file carries no
        # usable data and must not raise (audit issue SE-041).
        if raw_df.shape[1] < 4:
            return None
        df = raw_df.iloc[4:, 0:4].copy()
        df.columns = ["T_C", "sigma_Scm", "S_uVK", "PF_raw"]

    df = df.apply(pd.to_numeric, errors="coerce").dropna()
    t_vals = df["T_C"].values
    df["T_K"] = _to_kelvin(t_vals, source_header)
    df["sigma"] = df["sigma_Scm"] * 100.0
    df["S"] = df["S_uVK"] * 1e-6

    grouped = df.groupby("T_K")
    out = []
    for T, g in grouped:
        sigma_vals = mad_filter(g["sigma"].values)
        S_vals = mad_filter(g["S"].values)
        if len(sigma_vals) > 0 and len(S_vals) > 0:
            out.append({
                "T_K": T,
                "sigma": sigma_vals.mean(),
                "±σ": _standard_error(sigma_vals),
                "S": S_vals.mean(),
                "±S": _standard_error(S_vals),
            })
    return pd.DataFrame(out)


# ── Raw Seebeck processing ───────────────────────────────────────────────

def process_raw_seebeck_table(raw_df: pd.DataFrame | None) -> pd.DataFrame | None:
    """Derive sample Seebeck values from raw ΔV/ΔT regression groups."""
    if raw_df is None:
        return None

    df = raw_df.copy()
    SEARCH_GROUPS = {
        "T":      ["temperature", "temp", "t"],
        "deltaT": ["delta_k", "deltat", "delta_t", "⊿t", "dt", "delta t"],
        "deltaV": ["delta_mv", "deltav", "delta_v", "⊿v", "dv", "delta v"],
        "Spt":    ["spt", "ref", "r_s", "reference"],
    }

    def check_row(cols):
        normalized = {}
        src_cols = [str(c).lower().strip() for c in cols]
        for target, aliases in SEARCH_GROUPS.items():
            col = find_column(
                pd.DataFrame(columns=cols),
                aliases,
            )
            # simplified: direct alias search on src_cols
            for alias in sorted(aliases, key=len, reverse=True):
                for idx, src_col in enumerate(src_cols):
                    match = (alias in src_col) if len(alias) > 2 else bool(re.search(rf"\b{re.escape(alias)}\b", src_col))
                    if match:
                        normalized[target] = cols[idx] if hasattr(cols[0], '__len__') else cols[idx]
                        break
                if target in normalized:
                    break
        ok = all(k in normalized for k in ["T", "deltaT", "deltaV"])
        return ok, normalized

    ok, normalized_cols = check_row(list(df.columns))
    if not ok:
        for i in range(min(50, len(df))):
            row_vals = df.iloc[i].astype(str).tolist()
            ok, normalized_cols = check_row(row_vals)
            if ok:
                new_df = df.iloc[i + 1:].copy()
                new_df.columns = row_vals
                df = new_df
                break

    if not all(k in normalized_cols for k in ["T", "deltaT", "deltaV"]):
        if len(df.columns) >= 3:
            normalized_cols["T"] = df.columns[0]
            normalized_cols["deltaT"] = df.columns[1]
            normalized_cols["deltaV"] = df.columns[2]
        else:
            return None

    t_col = normalized_cols["T"]
    dt_col = normalized_cols["deltaT"]
    dv_col = normalized_cols["deltaV"]
    spt_col = normalized_cols.get("Spt")

    cols_to_use = [t_col, dt_col, dv_col]
    if spt_col:
        cols_to_use.append(spt_col)
    df = df[cols_to_use].apply(pd.to_numeric, errors="coerce").dropna()
    df["T_group"] = df[t_col].round(1)
    grouped = df.groupby("T_group")
    out = []

    for T, g in grouped:
        if len(g) < 2:
            continue
        x = g[dt_col].values
        y = g[dv_col].values * 1000.0  # to µV
        # A group in which every measurement used the same temperature
        # difference carries no slope information; scipy raises for that
        # case, so the group is skipped instead of aborting the import
        # (audit issue SE-040).
        if np.all(x == x[0]):
            continue
        res = _linregress(x, y)
        s_meas = res.slope
        s_err_uVK = res.stderr if len(g) >= 3 else 0.0
        spt = g[spt_col].mean() if spt_col else 0.0
        ssmp = s_meas + spt
        out.append({
            "T_K": T,
            "S_slope_uVK": s_meas,
            "Spt_uVK": spt,
            "S_uVK": ssmp,
            "±S_uVK": s_err_uVK,
            "S": ssmp * 1e-6,
            "±S": s_err_uVK * 1e-6,
        })

    res_df = pd.DataFrame(out)
    return None if res_df.empty else res_df


# ── Laser-flash processing ───────────────────────────────────────────────

def process_laser_flash_table(raw_df: pd.DataFrame | None) -> pd.DataFrame | None:
    """Normalize a raw laser-flash table into per-temperature properties."""
    if raw_df is None:
        return None
    df = raw_df.copy()
    LF_GROUPS = {
        "T_K":  ["temperature", "temp", "t"],
        "kappa": ["thermal conductivity", "thermal cond", "kappa", "κ", "k"],
        "alpha": ["diffusivity", "alpha", "α"],
        "cp":    ["specific heat", "cp", "heat capacity"],
    }
    normalized_cols = {}
    for target, aliases in LF_GROUPS.items():
        col = find_column(df, aliases)
        if col is not None:
            normalized_cols[target] = col

    if "T_K" not in normalized_cols or "kappa" not in normalized_cols:
        return None

    # The raw temperature column is converted to Kelvin using the unit
    # declared by its header (this application always exports laser-flash
    # temperatures in Kelvin), falling back to magnitude inference when the
    # header declares nothing. This matches the Kappa dialog's own laser-flash
    # import path, which treats the same column as Kelvin.
    # Audit reference: docs/SCIENTIFIC_EQUATION_AUDIT.md, issue SE-026.
    df["T_K"] = _to_kelvin(
        df[normalized_cols["T_K"]].values, normalized_cols["T_K"]
    )
    grouped = df.groupby("T_K")
    out = []
    for T, g in grouped:
        k = mad_filter(g[normalized_cols["kappa"]].values.astype(float))
        row = {"T_K": T, "kappa": k.mean(), "±κ": _standard_error(k)}
        if "alpha" in normalized_cols:
            a = mad_filter(g[normalized_cols["alpha"]].values.astype(float))
            if len(a) > 0:
                row["diffusivity"] = a.mean()
                row["±α"] = _standard_error(a)
        if "cp" in normalized_cols:
            c = mad_filter(g[normalized_cols["cp"]].values.astype(float))
            if len(c) > 0:
                row["Cp"] = c.mean()
                row["±Cp"] = _standard_error(c)
        if len(k) > 0:
            out.append(row)
    return pd.DataFrame(out)


# ── Combined measurement uncertainties ───────────────────────────────────

def combine_sigma_uncertainty(
    sigma_vals,
    sigma_stat_err_vals,
    width,
    width_err,
    thickness,
    thickness_err,
    probe_length,
    probe_length_err,
):
    """Combine statistical and geometric relative errors for conductivity."""
    if (width is None or thickness is None or probe_length is None
            or width == 0 or thickness == 0 or probe_length == 0):
        return sigma_stat_err_vals
    rel_stat = sigma_stat_err_vals / (sigma_vals + 1e-20)
    rel_L = (probe_length_err or 0) / probe_length
    rel_w = (width_err or 0) / width
    rel_t = (thickness_err or 0) / thickness
    return sigma_vals * np.sqrt(rel_stat ** 2 + rel_L ** 2 + rel_w ** 2 + rel_t ** 2)


def combine_seebeck_uncertainty(s_stat_err_vals, seebeck_ref_err_uv_k):
    """Combine statistical and reference Seebeck uncertainties."""
    ref_err_V_K = seebeck_ref_err_uv_k * 1e-6
    return np.sqrt(s_stat_err_vals ** 2 + ref_err_V_K ** 2)
