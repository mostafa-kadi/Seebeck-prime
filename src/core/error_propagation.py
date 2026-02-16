import numpy as np
import pandas as pd
import re


class ThermoelectricAnalyzer:
    def _read_file(self, path):
        if not path:
            return None
        try:
            if str(path).lower().endswith((".xlsx", ".xls")):
                return pd.read_excel(path)
            else:
                # Try CSV, then fallback to tab-separated if needed
                try:
                    return pd.read_csv(path)
                except:
                    return pd.read_csv(path, sep="\t")
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            return None

    def __init__(
        self,
        four_probe_file=None,
        lf_file=None,
        seebeck_raw_file=None,
        lorenz=2.44e-8,
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

        # Geometry parameters
        self.width = width
        self.width_err = width_err
        self.thickness = thickness
        self.thickness_err = thickness_err
        self.probe_length = probe_length
        self.probe_length_err = probe_length_err

        # Reference Seebeck Uncertainty (absolute in uV/K)
        self.seebeck_ref_err = seebeck_ref_err

    @staticmethod
    def mad_filter(x, thresh=3.0):
        x = np.asarray(x, dtype=float)
        x = x[~np.isnan(x)]  # Handle NaNs
        if len(x) == 0:
            return x
        med = np.median(x)
        mad = np.median(np.abs(x - med))
        if mad == 0:
            return x
        return x[np.abs(x - med) < thresh * mad]

    def process_four_probe(self):
        if self.fp_raw is None:
            return None
        df = self.fp_raw.copy()

        # Try robust mapping first
        FP_GROUPS = {
            "T_C": ["temperature", "temp", "t"],
            "sigma_Scm": ["conductivity", "sigma", "σ", "s/cm"],
            "S_uVK": ["seebeck", "alpha", "α", "uV/K", "µV/K"],
        }

        normalized_cols = {}
        source_cols = [str(c).lower().strip() for c in df.columns]

        for target, aliases in FP_GROUPS.items():
            for alias in sorted(aliases, key=len, reverse=True):
                found = False
                for idx, src_col in enumerate(source_cols):
                    if len(alias) > 2:
                        if alias in src_col:
                            normalized_cols[target] = df.columns[idx]
                            found = True
                            break
                    else:
                        pattern = rf"\b{re.escape(alias)}\b"
                        if re.search(pattern, src_col):
                            normalized_cols[target] = df.columns[idx]
                            found = True
                            break
                if found:
                    break

        if all(k in normalized_cols for k in ["T_C", "sigma_Scm", "S_uVK"]):
            t_col = normalized_cols["T_C"]
            sig_col = normalized_cols["sigma_Scm"]
            s_col = normalized_cols["S_uVK"]
            df = df[[t_col, sig_col, s_col]].copy()
            df.columns = ["T_C", "sigma_Scm", "S_uVK"]
        else:
            # Fallback to hardcoded positional indexing for legacy SBA files if mapping fails
            # Data usually starts at row 5 (index 4)
            df = self.fp_raw.iloc[4:, 0:4].copy()
            df.columns = ["T_C", "sigma_Scm", "S_uVK", "PF_raw"]

        df = df.apply(pd.to_numeric, errors="coerce").dropna()

        # Check if T is Kelvin or Celsius
        t_vals = df["T_C"].values
        if np.mean(t_vals) > 250:
            df["T_K"] = t_vals
        else:
            df["T_K"] = t_vals + 273.15

        df["sigma"] = df["sigma_Scm"] * 100.0
        df["S"] = df["S_uVK"] * 1e-6

        grouped = df.groupby("T_K")
        out = []

        for T, g in grouped:
            sigma = self.mad_filter(g["sigma"])
            S = self.mad_filter(g["S"])

            if len(sigma) > 0 and len(S) > 0:
                out.append(
                    {
                        "T_K": T,
                        "sigma": sigma.mean(),
                        "sigma_err": sigma.std(ddof=1) if len(sigma) > 1 else 0.0,
                        "S": S.mean(),
                        "S_err": S.std(ddof=1) if len(S) > 1 else 0.0,
                    }
                )

        return pd.DataFrame(out)

    def process_raw_seebeck(self):
        """
        Processes raw Seebeck data (dT, dV, S_ref) and performs linear regression.
        Headers: T, delta_K, delta_mV, Spt
        Formula: dV = S * dT
        Uncertainty: sigma_S = sigma_y / sqrt(N * sigma_x^2)
        Output Columns: T_K, S, Spt, Ssmp, S_err
        """
        if self.seebeck_raw is None:
            return None

        from scipy.stats import linregress

        df = self.seebeck_raw.copy()
        # Robust Header mapping using search groups
        SEARCH_GROUPS = {
            "T": ["temperature", "temp", "t"],
            "deltaT": ["delta_k", "deltat", "delta_t", "⊿t", "dt", "delta t"],
            "deltaV": ["delta_mv", "deltav", "delta_v", "⊿v", "dv", "delta v"],
            "Spt": ["spt", "ref", "r_s", "reference"],
        }

        # Helper to find valid header row
        def find_header_row(dataframe, search_groups, max_scan=50):
            # 1. Quick check on existing columns
            def check_row(cols):
                normalized = {}
                src_cols = [str(c).lower().strip() for c in cols]
                match_count = 0
                required = ["T", "deltaT", "deltaV"]

                for target, aliases in search_groups.items():
                    for alias in sorted(aliases, key=len, reverse=True):
                        found_alias = False
                        for idx, src_col in enumerate(src_cols):
                            if len(alias) > 2:
                                if alias in src_col:
                                    normalized[target] = cols[idx]
                                    found_alias = True
                                    break
                            else:
                                pattern = rf"\b{re.escape(alias)}\b"
                                if re.search(pattern, src_col):
                                    normalized[target] = cols[idx]
                                    found_alias = True
                                    break
                        if found_alias:
                            break

                # Check if all required are found
                if all(req in normalized for req in required):
                    return True, normalized
                return False, normalized

            # Check top columns first
            ok, mapping = check_row(dataframe.columns)
            if ok:
                return 0, mapping, dataframe

            # Scan rows
            for i in range(min(max_scan, len(dataframe))):
                row_vals = dataframe.iloc[i].astype(str).tolist()
                ok, mapping = check_row(row_vals)
                if ok:
                    # Reload or slice to make this the header
                    # Slice df from i+1
                    new_df = dataframe.iloc[i + 1 :].copy()
                    new_df.columns = row_vals
                    return i + 1, mapping, new_df

            return -1, {}, dataframe

        # Attempt to find the header
        start_idx, normalized_cols, df = find_header_row(df, SEARCH_GROUPS)

        required = ["T", "deltaT", "deltaV"]
        if not all(k in normalized_cols for k in required):
            missing = [k for k in required if k not in normalized_cols]
            print(
                f"Missing required columns in Seebeck file: {missing}. Found: {list(normalized_cols.keys())}"
            )
            print(f"Available columns in file: {list(df.columns)}")
            # Fallback: use first three columns if they exist
            if len(df.columns) >= 3:
                normalized_cols["T"] = df.columns[0]
                normalized_cols["deltaT"] = df.columns[1]
                normalized_cols["deltaV"] = df.columns[2]
                print("Fallback to first three columns as T, deltaT, deltaV.")
            else:
                return None

        # Extract data
        t_col = normalized_cols["T"]
        dt_col = normalized_cols["deltaT"]
        dv_col = normalized_cols["deltaV"]
        spt_col = normalized_cols.get("Spt")

        cols_to_use = [t_col, dt_col, dv_col]
        if spt_col:
            cols_to_use.append(spt_col)

        df = df[cols_to_use].apply(pd.to_numeric, errors="coerce").dropna()

        # Group by Temperature
        df["T_group"] = df[t_col].round(1)
        grouped = df.groupby("T_group")
        out = []

        for T, g in grouped:
            if len(g) < 1:  # Warn if < 1 as requested, though linreg needs >= 2
                continue

            if len(g) < 2:
                # Cannot regress with < 2 points
                continue

            # Linear regression: dV [mV] * 1000 = S_meas [uV/K] * dT [K]
            x = g[dt_col].values
            y = g[dv_col].values * 1000.0  # to uV

            res = linregress(x, y)
            s_meas = res.slope  # uV/K

            # Gaussian uncertainty: sigma_S = sigma_y / sqrt(N * sigma_x^2)
            # res.stderr is already the standard error of the slope in scipy
            # which is s_res / sqrt(sum((x - x_mean)^2))
            # sum((x - x_mean)^2) = N * variance(x)
            s_err_uVK = res.stderr if len(g) >= 3 else 0.0

            spt = g[spt_col].mean() if spt_col else 0.0
            ssmp = s_meas + spt

            out.append(
                {
                    "T_K": T,
                    "S": s_meas,  # uV/K (slope)
                    "Spt": spt,  # uV/K (ref)
                    "Ssmp": ssmp,  # uV/K (total)
                    "S_err": s_err_uVK,  # uV/K
                }
            )

        res_df = pd.DataFrame(out)
        if res_df.empty:
            return None

        # For the internal transport calculation, we need Seebeck in V/K
        res_df["S_base"] = res_df["Ssmp"] * 1e-6
        res_df["S_err_base"] = res_df["S_err"] * 1e-6

        return res_df

    def get_reporting_statement(self):
        """Mandatory scientific statement for reports."""
        return "The Seebeck coefficient uncertainty was determined from the standard error of the linear regression of ΔV versus ΔT using Gaussian error propagation."

    def process_laser_flash(self):
        if self.lf_raw is None:
            return None
        df = self.lf_raw.copy()

        # Robust mapping for Laser Flash columns
        LF_GROUPS = {
            "T_K": ["temperature", "temp", "t"],
            "kappa": ["thermal conductivity", "thermal cond", "kappa", "κ", "k"],
            "alpha": ["diffusivity", "alpha", "α"],
            "cp": ["specific heat", "cp", "heat capacity"],
        }

        normalized_cols = {}
        source_cols = [str(c).lower().strip() for c in df.columns]

        for target, aliases in LF_GROUPS.items():
            for alias in sorted(aliases, key=len, reverse=True):
                found = False
                for idx, src_col in enumerate(source_cols):
                    if len(alias) > 2:
                        if alias in src_col:
                            normalized_cols[target] = df.columns[idx]
                            found = True
                            break
                    else:
                        pattern = rf"\b{re.escape(alias)}\b"
                        if re.search(pattern, src_col):
                            normalized_cols[target] = df.columns[idx]
                            found = True
                            break
                if found:
                    break

        if "T_K" not in normalized_cols or "kappa" not in normalized_cols:
            print(f"Brittle LF mapping failed. Found: {list(normalized_cols.keys())}")
            return None

        t_col = normalized_cols["T_K"]
        k_col = normalized_cols["kappa"]
        alpha_col = normalized_cols.get("alpha")
        cp_col = normalized_cols.get("cp")

        # Convert T to Kelvin if it looks like Celsius
        # We'll check the values later during grouping

        df["T_K"] = df[t_col] + 273.15

        grouped = df.groupby("T_K")
        out = []

        for T, g in grouped:
            k = self.mad_filter(g[k_col])
            alpha = self.mad_filter(g[alpha_col]) if alpha_col else np.array([])
            cp = self.mad_filter(g[cp_col]) if cp_col else np.array([])

            row = {
                "T_K": T,
                "kappa": k.mean(),
                "kappa_err": k.std(ddof=1) if len(k) > 1 else 0.0,
            }
            if alpha_col and len(alpha) > 0:
                row["diffusivity"] = alpha.mean()
                row["diffusivity_err"] = alpha.std(ddof=1) if len(alpha) > 1 else 0.0
            if cp_col and len(cp) > 0:
                row["Cp"] = cp.mean()
                row["Cp_err"] = cp.std(ddof=1) if len(cp) > 1 else 0.0

            if len(k) > 0:
                out.append(row)

        return pd.DataFrame(out)

    def calculate_combined_sigma_error(self, sigma_vals, sigma_stat_err_vals):
        """
        Calculates total conductivity uncertainty by combining statistical measurement error
        with systematic geometric errors.
        dsigma/sigma = sqrt( (dStat/sigma)^2 + (dL/L)^2 + (dw/w)^2 + (dt/t)^2 )
        """
        if (
            self.width is None
            or self.thickness is None
            or self.probe_length is None
            or self.width == 0
            or self.thickness == 0
            or self.probe_length == 0
        ):
            # Fallback if geometry not provided: return statistical error only
            return sigma_stat_err_vals

        # Relative errors
        rel_stat = sigma_stat_err_vals / (sigma_vals + 1e-20)
        rel_L = (self.probe_length_err or 0) / self.probe_length
        rel_w = (self.width_err or 0) / self.width
        rel_t = (self.thickness_err or 0) / self.thickness

        rel_total = np.sqrt(rel_stat**2 + rel_L**2 + rel_w**2 + rel_t**2)

        return sigma_vals * rel_total

    def calculate_combined_seebeck_error(self, s_stat_err_vals):
        """
        Calculates total Seebeck uncertainty by combining statistical measurement error
        with systematic reference uncertainty.
        dS_total = sqrt( dS_stat^2 + dS_ref^2 )
        """
        # Convert uV/K to V/K if input is V/K, or ensure units match.
        # Self.S is usually stored in V/K in the dataframe (processed_four_probe does *1e-6)
        # s_stat_err_vals is in V/K.
        # self.seebeck_ref_err is likely provided in uV/K, need to check inputs.
        # Assuming seebeck_ref_err passed to init is in uV/K, we convert to V/K here.

        ref_err_V_K = self.seebeck_ref_err * 1e-6

        return np.sqrt(s_stat_err_vals**2 + ref_err_V_K**2)

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

        # Determine base DataFrame logic
        df = None

        # 1. Start with Four-Probe if available
        if fp_df is not None:
            df = fp_df.copy()
            # If Raw Seebeck is also available, use it to override/augment S
            if seebeck_raw_df is not None and not seebeck_raw_df.empty:
                df = pd.merge(
                    df.drop(columns=["S", "S_err"], errors="ignore"),
                    seebeck_raw_df,
                    on="T_K",
                    how="left",
                )
        elif seebeck_raw_df is not None:
            # 2. Fallback to Seebeck Raw as base if no Four-Probe
            df = seebeck_raw_df.copy()
            # Ensure S column exists for consistency (process_raw_seebeck provides S, Ssmp)
            if "S" not in df.columns and "Ssmp" in df.columns:
                # Ensure we have the slope (S) or the sample S (Ssmp = S + Spt).
                # Usually 'S' in process_raw_seebeck is the slope. 'Ssmp' is the corrected one.
                # The Analyzer logic uses 'S' as the value for transport.
                # For consistency with 'process_four_probe' (where S is the sample Seebeck),
                # we probably want Ssmp as the main 'S' if coming from raw seebeck?
                # Wait, process_raw_seebeck output: S (slope), Ssmp (total).
                # process_four_probe output: S.
                pass

        # 3. Merge with Laser Flash if available
        if lf_df is not None:
            if df is None:
                df = lf_df.copy()
            else:
                # Merge inner to find common temperatures
                df = pd.merge(df, lf_df, on="T_K", how="inner")

        if df is None or df.empty:
            return None

        # Transport Calculations (conditionally)
        has_sigma = "sigma" in df.columns
        has_S = "S" in df.columns
        has_kappa = "kappa" in df.columns

        # Error Propagation
        if has_sigma:
            df["sigma_err"] = self.calculate_combined_sigma_error(
                df["sigma"], df.get("sigma_err", 0)
            )

        if has_S:
            df["S_err"] = self.calculate_combined_seebeck_error(df.get("S_err", 0))

        # Derived Properties
        if has_sigma and has_S:
            df["PF"] = df["S"] ** 2 * df["sigma"]

            # PF Error
            df["PF_err"] = df["PF"] * np.sqrt(
                (2 * df["S_err"] / (df["S"] + 1e-20)) ** 2
                + (df["sigma_err"] / (df["sigma"] + 1e-20)) ** 2
            )

        # Kappa Electronic and Lattice
        if has_sigma and has_S:  # Lorenz requires S for auto, and sigma for Ke
            # Handle variable Lorenz number
            if isinstance(self.L, str) and self.L == "auto":
                from .calculations import estimate_lorenz

                # Use Seebeck in uV/K for estimation
                L_vals = estimate_lorenz(df["S"] * 1e6)
            else:
                L_vals = self.L

            df["kappa_e"] = L_vals * df["sigma"] * df["T_K"]

            # Kappa e Error
            df["kappa_e_err"] = df["kappa_e"] * (
                df["sigma_err"] / (df["sigma"] + 1e-20)
            )

            if has_kappa:
                df["kappa_L"] = df["kappa"] - df["kappa_e"]
                df["kappa_L_err"] = np.sqrt(
                    df["kappa_err"] ** 2 + df["kappa_e_err"] ** 2
                )

                # ZT
                df["ZT"] = df["PF"] * df["T_K"] / df["kappa"]
                df["ZT_err"] = df["ZT"] * np.sqrt(
                    (2 * df["S_err"] / (df["S"] + 1e-20)) ** 2
                    + (df["sigma_err"] / (df["sigma"] + 1e-20)) ** 2
                    + (df["kappa_err"] / (df["kappa"] + 1e-20)) ** 2
                )

        return df


def calculate_pf_error(seebeck, seebeck_err, conductivity, conductivity_err):
    """
    Calculates error for Power Factor (PF = S^2 * sigma).
    dPF = sqrt((2 * S * sigma * dS)^2 + (S^2 * dsigma)^2)
    """
    return np.sqrt(
        (2 * seebeck * conductivity * seebeck_err) ** 2
        + (seebeck**2 * conductivity_err) ** 2
    )


def calculate_kappa_e_error(
    conductivity, conductivity_err, temperature, temp_err, lorenz, lorenz_err
):
    """
    Calculates error for Electronic Thermal Conductivity (kappa_e = L * sigma * T).
    dk_e = sqrt((L * T * dsigma)^2 + (L * sigma * dT)^2 + (sigma * T * dL)^2)
    """
    return np.sqrt(
        (lorenz * temperature * conductivity_err) ** 2
        + (lorenz * conductivity * temp_err) ** 2
        + (conductivity * temperature * lorenz_err) ** 2
    )


def calculate_kappa_l_error(kappa_total_err, kappa_e_err):
    """
    Calculates error for Lattice Thermal Conductivity (kappa_l = kappa_total - kappa_e).
    dk_l = sqrt(dk_total^2 + dk_e^2)
    """
    return np.sqrt(kappa_total_err**2 + kappa_e_err**2)


def calculate_zt_error(pf, pf_err, temperature, temp_err, kappa_total, kappa_total_err):
    """
    Calculates error for Figure of Merit (ZT = PF * T / kappa_total).
    dZT = ZT * sqrt((dPF/PF)^2 + (dT/T)^2 + (dk_total/k_total)^2)
    """
    zt = (pf * temperature) / kappa_total
    # Avoid division by zero
    mask = (pf != 0) & (temperature != 0) & (kappa_total != 0)
    zt_err = np.zeros_like(zt)

    if np.any(mask):
        zt_err[mask] = zt[mask] * np.sqrt(
            (pf_err[mask] / pf[mask]) ** 2
            + (temp_err[mask] / temperature[mask]) ** 2
            + (kappa_total_err[mask] / kappa_total[mask]) ** 2
        )
    return zt_err


def calculate_measurement_sigma_error(
    area, area_err, length, length_err, resistance, resistance_err
):
    """
    Calculates sigma error from sample geometry and resistance (sigma = L / (R * A)).
    dsigma = sigma * sqrt((dL/L)^2 + (dR/R)^2 + (dA/A)^2)
    """
    sigma = length / (resistance * area)
    return sigma * np.sqrt(
        (length_err / length) ** 2
        + (resistance_err / resistance) ** 2
        + (area_err / area) ** 2
    )


def calculate_measurement_kappa_error(
    diffusivity, diffusivity_err, cp, cp_err, density, density_err
):
    """
    Calculates kappa error from laser flash measurements (kappa = alpha * Cp * rho).
    dkappa = kappa * sqrt((dalpha/alpha)^2 + (dCp/Cp)^2 + (drho/rho)^2)
    """
    kappa = diffusivity * cp * density
    return kappa * np.sqrt(
        (diffusivity_err / diffusivity) ** 2
        + (cp_err / cp) ** 2
        + (density_err / density) ** 2
    )


def calculate_density_error(
    weight, weight_err, area, area_err, thickness, thickness_err
):
    """
    Calculates density error (rho = m / (A * t)).
    drho = rho * sqrt((dm/m)^2 + (dA/A)^2 + (dt/t)^2)
    """
    density = weight / (area * thickness)
    return density * np.sqrt(
        (weight_err / weight) ** 2
        + (area_err / area) ** 2
        + (thickness_err / thickness) ** 2
    )
