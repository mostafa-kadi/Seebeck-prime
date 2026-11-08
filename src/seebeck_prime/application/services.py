"""
Application services for Seebeck Prime.

This module contains the ThermoelectricAnalyzer service, which coordinates
domain logic (calculations, uncertainty propagation, file parsing) into
higher-level workflows.

The application layer:
- May depend on domain
- May depend on infrastructure (via passed-in data, not direct import)
- Must NOT depend on GUI or plot code
"""

from __future__ import annotations

import re
import numpy as np
import pandas as pd

from seebeck_prime.domain.calculations import (
    calculate_pf,
    calculate_kappa_e,
    calculate_kappa_l,
    calculate_zt,
    estimate_lorenz,
)
from seebeck_prime.domain.uncertainty import (
    propagate_pf_error,
    propagate_kappa_e_error,
    propagate_kappa_l_error,
    propagate_zt_error,
)
from seebeck_prime.domain.analysis import mad_filter, linear_regression
from seebeck_prime.domain.constants import DEFAULT_LORENZ


class ThermoelectricAnalyzer:
    """
    High-level service that reads raw measurement files, applies error
    propagation, and produces a combined processed DataFrame.

    This class is the authoritative replacement for the old
    ``src.core.error_propagation.ThermoelectricAnalyzer``.
    """

    def _read_file(self, path):
        if not path:
            return None
        try:
            if str(path).lower().endswith((".xlsx", ".xls")):
                return pd.read_excel(path)
            try:
                return pd.read_csv(path)
            except Exception:
                return pd.read_csv(path, sep="\t")
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            return None

    def __init__(
        self,
        four_probe_file=None,
        lf_file=None,
        seebeck_raw_file=None,
        lorenz=DEFAULT_LORENZ,
        width=None,
        width_err=None,
        thickness=None,
        thickness_err=None,
        probe_length=None,
        probe_length_err=None,
        seebeck_ref_err=0.0,
    ):
        self.fp_raw = self._read_file(four_probe_file)
        self.lf_raw = self._read_file(lf_file)
        self.seebeck_raw = self._read_file(seebeck_raw_file)
        self.L = lorenz

        self.width = width
        self.width_err = width_err
        self.thickness = thickness
        self.thickness_err = thickness_err
        self.probe_length = probe_length
        self.probe_length_err = probe_length_err
        self.seebeck_ref_err = seebeck_ref_err

        self.fp_processed = None
        self.lf_processed = None
        self.seebeck_raw_processed = None

    # ── Column Mapping Utility ───────────────────────────────────────────────

    @staticmethod
    def _find_column(df, aliases):
        source_cols = [str(c).lower().strip() for c in df.columns]
        for alias in sorted(aliases, key=len, reverse=True):
            for idx, src_col in enumerate(source_cols):
                if len(alias) > 2:
                    if alias in src_col:
                        return df.columns[idx]
                else:
                    pattern = rf"\b{re.escape(alias)}\b"
                    if re.search(pattern, src_col):
                        return df.columns[idx]
        return None

    # ── Four-Probe Processing ────────────────────────────────────────────────

    def process_four_probe(self):
        if self.fp_raw is None:
            return None
        df = self.fp_raw.copy()
        FP_GROUPS = {
            "T_C":      ["temperature", "temp", "t"],
            "sigma_Scm": ["conductivity", "sigma", "σ", "s/cm"],
            "S_uVK":    ["seebeck", "alpha", "α", "uV/K", "µV/K"],
        }
        normalized_cols = {}
        for target, aliases in FP_GROUPS.items():
            col = self._find_column(df, aliases)
            if col is not None:
                normalized_cols[target] = col

        if all(k in normalized_cols for k in ["T_C", "sigma_Scm", "S_uVK"]):
            df = df[[normalized_cols["T_C"], normalized_cols["sigma_Scm"], normalized_cols["S_uVK"]]].copy()
            df.columns = ["T_C", "sigma_Scm", "S_uVK"]
        else:
            df = self.fp_raw.iloc[4:, 0:4].copy()
            df.columns = ["T_C", "sigma_Scm", "S_uVK", "PF_raw"]

        df = df.apply(pd.to_numeric, errors="coerce").dropna()
        t_vals = df["T_C"].values
        df["T_K"] = t_vals if np.mean(t_vals) > 250 else t_vals + 273.15
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
                    "±σ": sigma_vals.std(ddof=1) if len(sigma_vals) > 1 else 0.0,
                    "S": S_vals.mean(),
                    "±S": S_vals.std(ddof=1) if len(S_vals) > 1 else 0.0,
                })
        return pd.DataFrame(out)

    # ── Raw Seebeck Processing ───────────────────────────────────────────────

    def process_raw_seebeck(self):
        if self.seebeck_raw is None:
            return None
        from scipy.stats import linregress as _linregress

        df = self.seebeck_raw.copy()
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
                col = self._find_column(
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

    # ── Laser Flash Processing ───────────────────────────────────────────────

    def process_laser_flash(self):
        if self.lf_raw is None:
            return None
        df = self.lf_raw.copy()
        LF_GROUPS = {
            "T_K":  ["temperature", "temp", "t"],
            "kappa": ["thermal conductivity", "thermal cond", "kappa", "κ", "k"],
            "alpha": ["diffusivity", "alpha", "α"],
            "cp":    ["specific heat", "cp", "heat capacity"],
        }
        normalized_cols = {}
        for target, aliases in LF_GROUPS.items():
            col = self._find_column(df, aliases)
            if col is not None:
                normalized_cols[target] = col

        if "T_K" not in normalized_cols or "kappa" not in normalized_cols:
            return None

        df["T_K"] = df[normalized_cols["T_K"]] + 273.15
        grouped = df.groupby("T_K")
        out = []
        for T, g in grouped:
            k = mad_filter(g[normalized_cols["kappa"]].values.astype(float))
            row = {"T_K": T, "kappa": k.mean(), "±κ": k.std(ddof=1) if len(k) > 1 else 0.0}
            if "alpha" in normalized_cols:
                a = mad_filter(g[normalized_cols["alpha"]].values.astype(float))
                if len(a) > 0:
                    row["diffusivity"] = a.mean()
                    row["±α"] = a.std(ddof=1) if len(a) > 1 else 0.0
            if "cp" in normalized_cols:
                c = mad_filter(g[normalized_cols["cp"]].values.astype(float))
                if len(c) > 0:
                    row["Cp"] = c.mean()
                    row["±Cp"] = c.std(ddof=1) if len(c) > 1 else 0.0
            if len(k) > 0:
                out.append(row)
        return pd.DataFrame(out)

    # ── Combined Sigma Error ─────────────────────────────────────────────────

    def calculate_combined_sigma_error(self, sigma_vals, sigma_stat_err_vals):
        if (self.width is None or self.thickness is None or self.probe_length is None
                or self.width == 0 or self.thickness == 0 or self.probe_length == 0):
            return sigma_stat_err_vals
        rel_stat = sigma_stat_err_vals / (sigma_vals + 1e-20)
        rel_L = (self.probe_length_err or 0) / self.probe_length
        rel_w = (self.width_err or 0) / self.width
        rel_t = (self.thickness_err or 0) / self.thickness
        return sigma_vals * np.sqrt(rel_stat ** 2 + rel_L ** 2 + rel_w ** 2 + rel_t ** 2)

    def calculate_combined_seebeck_error(self, s_stat_err_vals):
        ref_err_V_K = self.seebeck_ref_err * 1e-6
        return np.sqrt(s_stat_err_vals ** 2 + ref_err_V_K ** 2)

    # ── Main Transport Calculation ───────────────────────────────────────────

    def calculate_transport(self, fp_df=None, lf_df=None, seebeck_raw_df=None):
        if fp_df is None:
            fp_df = self.process_four_probe()
        if lf_df is None:
            lf_df = self.process_laser_flash()
        if seebeck_raw_df is None:
            seebeck_raw_df = self.process_raw_seebeck()

        self.fp_processed = fp_df
        self.lf_processed = lf_df
        self.seebeck_raw_processed = seebeck_raw_df

        df = None
        if fp_df is not None:
            df = fp_df.copy()
            if seebeck_raw_df is not None and not seebeck_raw_df.empty:
                df = pd.merge(
                    df.drop(columns=["S", "S_err"], errors="ignore"),
                    seebeck_raw_df,
                    on="T_K",
                    how="left",
                )
        elif seebeck_raw_df is not None:
            df = seebeck_raw_df.copy()

        if lf_df is not None:
            df = lf_df.copy() if df is None else pd.merge(df, lf_df, on="T_K", how="inner")

        if df is None or df.empty:
            return None

        has_sigma = "sigma" in df.columns
        has_S = "S" in df.columns
        has_kappa = "kappa" in df.columns

        if has_sigma:
            df["±σ"] = self.calculate_combined_sigma_error(df["sigma"], df.get("±σ", 0))
        if has_S:
            df["±S"] = self.calculate_combined_seebeck_error(df.get("±S", 0))

        if has_sigma and has_S:
            df["PF"] = df["S"] ** 2 * df["sigma"]
            df["±PF"] = propagate_pf_error(df["S"], df["±S"], df["sigma"], df["±σ"])

            L_vals = estimate_lorenz(df["S"] * 1e6) if (isinstance(self.L, str) and self.L == "auto") else self.L
            df["kappa_e"] = calculate_kappa_e(df["sigma"], df["T_K"], L_vals)
            df["±κₑ"] = df["kappa_e"] * (df["±σ"] / (df["sigma"] + 1e-20))

            if has_kappa:
                df["kappa_L"] = calculate_kappa_l(df["kappa"], df["kappa_e"])
                df["±κₗ"] = propagate_kappa_l_error(df["±κ"], df["±κₑ"])
                df["ZT"] = calculate_zt(df["PF"], df["T_K"], df["kappa"])
                df["±ZT"] = propagate_zt_error(
                    df["PF"], df["±PF"],
                    df["T_K"], pd.Series(np.zeros(len(df))),
                    df["kappa"], df["±κ"],
                )

        return df

    @staticmethod
    def get_reporting_statement() -> str:
        return (
            "The Seebeck coefficient uncertainty was determined from the standard error of "
            "the linear regression of ΔV versus ΔT using Gaussian error propagation."
        )
