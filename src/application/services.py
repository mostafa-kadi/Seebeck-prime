"""
Application services for Seebeck Prime.

This module contains the ``ThermoelectricAnalyzer`` service, which coordinates
domain logic (calculations, uncertainty propagation, and measurement processing)
into higher-level workflows. Raw tables enter through an injected data-store port.

The application layer:
- May depend on domain
- May depend on infrastructure (via passed-in data, not direct import)
- Must NOT depend on GUI or plot code
"""

from __future__ import annotations

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
from seebeck_prime.domain.physical_constants import DEFAULT_LORENZ
from seebeck_prime.application.ports import TabularDataStore
from seebeck_prime.application.measurement_processing import (
    combine_seebeck_uncertainty,
    combine_sigma_uncertainty,
    find_column,
    process_four_probe_table,
    process_laser_flash_table,
    process_raw_seebeck_table,
)


class ThermoelectricAnalyzer:
    """
    High-level service that receives raw measurement files through a data-store
    port, applies error propagation, and produces a combined processed DataFrame.

    Table transformations live in ``application.measurement_processing``; this
    class remains the public façade and owns file access through the port.
    """

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
        data_store: TabularDataStore | None = None,
    ):
        self.fp_raw = self._read_input(four_probe_file, data_store)
        self.lf_raw = self._read_input(lf_file, data_store)
        self.seebeck_raw = self._read_input(seebeck_raw_file, data_store)
        self.L = DEFAULT_LORENZ if lorenz is None else lorenz

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

    @staticmethod
    def _read_input(path, data_store: TabularDataStore | None):
        if not path:
            return None
        if data_store is None:
            raise ValueError("A TabularDataStore must be provided when measurement file paths are used.")
        try:
            return data_store.read(path)
        except Exception as exc:
            raise ValueError(f"Could not read measurement file {path}: {exc}") from exc

    # ── Column Mapping Utility ───────────────────────────────────────────────

    @staticmethod
    def _find_column(df, aliases):
        """Backward-compatible delegate for the shared alias matcher."""
        return find_column(df, aliases)

    # ── Four-Probe Processing ────────────────────────────────────────────────

    def process_four_probe(self):
        return process_four_probe_table(self.fp_raw)

    # ── Raw Seebeck Processing ───────────────────────────────────────────────

    def process_raw_seebeck(self):
        return process_raw_seebeck_table(self.seebeck_raw)

    # ── Laser Flash Processing ───────────────────────────────────────────────

    def process_laser_flash(self):
        return process_laser_flash_table(self.lf_raw)

    # ── Combined Sigma Error ─────────────────────────────────────────────────

    def calculate_combined_sigma_error(self, sigma_vals, sigma_stat_err_vals):
        return combine_sigma_uncertainty(
            sigma_vals,
            sigma_stat_err_vals,
            self.width,
            self.width_err,
            self.thickness,
            self.thickness_err,
            self.probe_length,
            self.probe_length_err,
        )

    def calculate_combined_seebeck_error(self, s_stat_err_vals):
        return combine_seebeck_uncertainty(s_stat_err_vals, self.seebeck_ref_err)

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
                # Drop the four-probe Seebeck value AND its uncertainty before
                # merging: the raw-Seebeck regression supersedes both. Keeping
                # the four-probe "±S" would make pandas rename the colliding
                # columns to "±S_x"/"±S_y", after which the regression
                # uncertainty was silently lost and u(PF)/u(ZT) were
                # understated (audit issue SE-029).
                df = pd.merge(
                    df.drop(columns=["S", "S_err", "\u00b1S"], errors="ignore"),
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
            df["PF"] = calculate_pf(df["S"], df["sigma"])
            df["±PF"] = propagate_pf_error(df["S"], df["±S"], df["sigma"], df["±σ"])

            L_vals = estimate_lorenz(df["S"] * 1e6) if (isinstance(self.L, str) and self.L == "auto") else self.L
            df["kappa_e"] = calculate_kappa_e(df["sigma"], df["T_K"], L_vals)
            # Use the domain propagator so that the file workflow and the
            # manual workflow report the same u(kappa_e); the previous inline
            # expression (kappa_e * u_sigma/sigma) omitted the temperature and
            # Lorenz terms (audit issue SE-030).
            u_kappa_e = propagate_kappa_e_error(
                df["sigma"].to_numpy(),
                df["±σ"].to_numpy(),
                df["T_K"].to_numpy(),
                np.zeros(len(df)),
                np.asarray(L_vals, dtype=float),
                np.zeros(len(df)),
            )
            df["±κₑ"] = u_kappa_e

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
        """Describe how the reported uncertainties were obtained.

        The statement must reflect what the code actually does: the raw
        Seebeck file contributes the standard error of the linear regression
        of ΔV versus ΔT (combined in quadrature with the reference Seebeck
        uncertainty), while a four-probe file contributes the standard error
        of the mean of the repeated readings (audit issue SE-037).
        """
        return (
            "Seebeck uncertainty: from the standard error of the linear regression of "
            "ΔV versus ΔT when a raw Seebeck file is supplied (combined in quadrature "
            "with the reference Seebeck uncertainty), otherwise from the standard error "
            "of the mean of the repeated four-probe readings; all contributions are "
            "combined by Gaussian (independent) error propagation."
        )
