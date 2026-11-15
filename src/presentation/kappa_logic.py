"""Presentation orchestration for the Kappa analysis dialog."""

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from seebeck_prime.application.use_cases import (
    calculate_formula_mass_use_case,
    calculate_dulong_petit_limit_use_case,
    calculate_kappa_from_lfa_si_use_case,
    combine_relative_uncertainties_use_case,
    propagate_lfa_kappa_uncertainty_use_case,
)
from seebeck_prime.application.unit_conversion import (
    convert_temperature_to_kelvin,
    to_base_value,
    uncertainty_to_base,
)
from seebeck_prime.presentation.plot_window import PlotWindow


import re
from seebeck_prime.application.data_mapping import get_robust_mapped_dataframe


def smart_map_lf_data(df):
    """
    Robustly maps Laser Flash DataFrame columns to logical properties.
    """
    SEARCH_GROUPS = [
        ("T_K", ["temperature", "temp", "t"]),
        ("alpha", ["thermal diffusivity", "alpha", "α", "diffusivity"]),
        ("cp", ["specific heat", "cp", "heat capacity", "specific"]),
        ("kappa", ["thermal conductivity", "thermal cond.", "kappa", "κ", "k"]),
    ]

    # We use the generic mapper from table_handler if available or similar logic
    mapped_df = get_robust_mapped_dataframe(df, SEARCH_GROUPS)

    # Check if we got the absolute minimum (T)
    if "T_K" not in mapped_df.columns:
        return None

    return mapped_df


def process_grouped_lf_data(df):
    """
    Groups data by temperature (rounding to nearest 20 K) and calculates mean and std.
    """
    if df is None:
        return None

    # Round T_K to nearest 20 to group points like 95, 100, 105 (buffer for ±5)
    df = df.copy()
    df["T_Group"] = (df["T_K"] / 20).round() * 20

    grouped = df.groupby("T_Group")
    out = []

    for T, g in grouped:
        row = {"T_K": T}
        for col in ["alpha", "cp", "kappa"]:
            if col in g.columns:
                vals = pd.to_numeric(g[col], errors="coerce").dropna()
                if len(vals) > 0:
                    row[col] = vals.mean()
                    row[f"d{col}"] = vals.std(ddof=1) if len(vals) > 1 else 0.0
        out.append(row)

    return pd.DataFrame(out)


def update_dp_display(dialog):
    """Updates the DP limit label based on the selected unit."""
    if dialog.molecular_weight is None:
        dialog.dp_val_label.setText("Limit: N/A")
        return

    unit = dialog.dp_unit_combo.currentText()
    val = calculate_dulong_petit_limit_use_case(
        dialog.atoms_per_formula_unit, dialog.molecular_weight, unit
    )

    dialog.dp_val_label.setText(f"Limit: {val:.2f} {unit}")


def _calculate_molecular_weight(dialog):
    """Calculates molecular weight and atoms per formula unit."""
    formula = dialog.formula_edit.text().strip()
    if not formula:
        QMessageBox.warning(dialog, "Input Error", "Please enter a chemical formula.")
        return

    total_mw, num_atoms = calculate_formula_mass_use_case(formula)

    if total_mw is None:
        dialog.molecular_weight = None
        dialog.atoms_per_formula_unit = 0
        dialog.plot_dp_check.setEnabled(False)
        dialog.mw_result_label.setText("MW: N/A, Atoms: N/A")
        update_dp_display(dialog)
        QMessageBox.warning(
            dialog, "Calculation Error", f"Invalid formula or unknown element."
        )
        return

    dialog.molecular_weight = total_mw
    dialog.atoms_per_formula_unit = num_atoms
    dialog.plot_dp_check.setEnabled(True)

    # Reset checkbox text to generic
    dialog.plot_dp_check.setText("Overlay Dulong-Petit Limit on Cp Plot")

    dialog.mw_result_label.setText(f"MW: {total_mw:.3f} g/mol, Atoms: {num_atoms}")
    update_dp_display(dialog)


def calculate_properties(dialog):
    """Core calculation logic for thermal conductivity."""
    try:
        density_val = float(dialog.density_edit.text())
        # Display units (g/cm³ or kg/m³) -> SI [kg/m³], application-layer
        # conversion; unrecognized units pass through as before.
        density_kg_m3 = to_base_value(density_val, dialog.units["density"], "density")

        # Density Error
        rho_err_kg_m3 = 0.0
        if dialog.calc_errors_check.isChecked():
            try:
                w_val = float(dialog.weight_edit.text())
                w_err = float(dialog.weight_err_edit.text())
                t_val = float(dialog.thickness_edit.text())
                t_err = float(dialog.thickness_err_edit.text())
                area_val = float(dialog.area_edit.text())
                area_err = float(dialog.area_err_edit.text())

                if w_val > 0 and t_val > 0 and area_val > 0:
                    rel_dm = w_err / w_val
                    rel_dt = t_err / t_val
                    rel_dA = area_err / area_val
                    rho_err_kg_m3 = combine_relative_uncertainties_use_case(
                        density_kg_m3, rel_dm, rel_dt, rel_dA
                    )
            except ValueError:
                pass

    except ValueError:
        return

    is_manual_mode = dialog.kappa_mode_combo.currentIndex() == 0
    is_error_mode = dialog.calc_errors_check.isChecked()

    if is_manual_mode:
        return  # No calculation needed

    dialog.source_table.blockSignals(True)
    for row in range(dialog.source_table.rowCount()):
        item_t = dialog.source_table.item(row, 0)

        if not is_error_mode:
            # Mode: Fixed columns [T, alpha, cp, kappa]
            item_a = dialog.source_table.item(row, 1)
            item_c = dialog.source_table.item(row, 2)
            if (
                item_t
                and item_a
                and item_c
                and item_t.text()
                and item_a.text()
                and item_c.text()
            ):
                try:
                    alpha_mm2s = float(item_a.text())
                    cp_JgK = float(item_c.text())

                    # Display units (mm²/s, J/g·K) -> SI, application-layer
                    # conversion (no inline unit factors in the presentation
                    # layer).
                    alpha_m2s = to_base_value(
                        alpha_mm2s, "mm²/s", "thermal_diffusivity"
                    )
                    cp_JkgK = to_base_value(
                        cp_JgK, "J/g·K", "specific_heat_capacity"
                    )

                    kappa = calculate_kappa_from_lfa_si_use_case(
                        alpha_m2s, cp_JkgK, density_kg_m3
                    )

                    if np.isnan(kappa):
                        continue

                    dialog.source_table.setItem(
                        row, 3, QTableWidgetItem(f"{kappa:.6g}")
                    )
                except ValueError:
                    pass
        else:
            # Mode: Error columns [T, alpha, da, cp, dcp, kappa, dkappa]
            item_a = dialog.source_table.item(row, 1)
            item_da = dialog.source_table.item(row, 2)
            item_c = dialog.source_table.item(row, 3)
            item_dc = dialog.source_table.item(row, 4)

            if (
                item_t
                and item_a
                and item_c
                and item_t.text()
                and item_a.text()
                and item_c.text()
            ):
                try:
                    alpha = float(item_a.text())
                    cp = float(item_c.text())
                    da = float(item_da.text()) if (item_da and item_da.text()) else 0.0
                    dcp = float(item_dc.text()) if (item_dc and item_dc.text()) else 0.0

                    alpha_m2s = to_base_value(
                        alpha, "mm²/s", "thermal_diffusivity"
                    )
                    cp_JkgK = to_base_value(cp, "J/g·K", "specific_heat_capacity")

                    kappa = calculate_kappa_from_lfa_si_use_case(
                        alpha_m2s, cp_JkgK, density_kg_m3
                    )

                    if np.isnan(kappa):
                        continue

                    # Linear scale units: the uncertainties transform exactly
                    # like their values (see application.unit_conversion).
                    da_m2s = uncertainty_to_base(
                        alpha, da, "mm²/s", "thermal_diffusivity"
                    )
                    dcp_JkgK = uncertainty_to_base(
                        cp, dcp, "J/g·K", "specific_heat_capacity"
                    )

                    dk = propagate_lfa_kappa_uncertainty_use_case(
                        alpha_m2s,
                        da_m2s,
                        cp_JkgK,
                        dcp_JkgK,
                        density_kg_m3,
                        rho_err_kg_m3,
                    )

                    dialog.source_table.setItem(
                        row, 5, QTableWidgetItem(f"{kappa:.6g}")
                    )
                    dialog.source_table.setItem(row, 6, QTableWidgetItem(f"{dk:.6g}"))
                except ValueError:
                    pass

    dialog.source_table.blockSignals(False)


def read_source_data(dialog):
    """Reads and validates the data from the source table, returning a dict."""
    temps = []
    alphas = []
    cps = []
    ks = []
    # Error counterparts
    da_list = []
    dcp_list = []
    dk_list = []

    is_error_mode = dialog.calc_errors_check.isChecked()
    rows = dialog.source_table.rowCount()

    for r in range(rows):
        i_t = dialog.source_table.item(r, 0)

        if not i_t or not i_t.text().strip():
            continue

        try:
            # The table displays temperatures in the dialog's selected unit;
            # convert to Kelvin (the internal unit used by every downstream
            # calculation and by the main-window interpolation).
            # See docs/SCIENTIFIC_EQUATION_AUDIT.md, issue SE-004.
            t_val = convert_temperature_to_kelvin(
                float(i_t.text()), dialog.units["temp"]
            )

            if not is_error_mode:
                i_a = dialog.source_table.item(r, 1)
                i_c = dialog.source_table.item(r, 2)
                i_k = dialog.source_table.item(r, 3)

                a_val = float(i_a.text()) if (i_a and i_a.text().strip()) else np.nan
                c_val = float(i_c.text()) if (i_c and i_c.text().strip()) else np.nan
                k_val = float(i_k.text()) if (i_k and i_k.text().strip()) else np.nan

                da_val, dcp_val, dk_val = 0.0, 0.0, 0.0
            else:
                i_a = dialog.source_table.item(r, 1)
                i_da = dialog.source_table.item(r, 2)
                i_c = dialog.source_table.item(r, 3)
                i_dc = dialog.source_table.item(r, 4)
                i_k = dialog.source_table.item(r, 5)
                i_dk = dialog.source_table.item(r, 6)

                a_val = float(i_a.text()) if (i_a and i_a.text().strip()) else np.nan
                da_val = float(i_da.text()) if (i_da and i_da.text().strip()) else 0.0
                c_val = float(i_c.text()) if (i_c and i_c.text().strip()) else np.nan
                dcp_val = float(i_dc.text()) if (i_dc and i_dc.text().strip()) else 0.0
                k_val = float(i_k.text()) if (i_k and i_k.text().strip()) else np.nan
                dk_val = float(i_dk.text()) if (i_dk and i_dk.text().strip()) else 0.0

            temps.append(t_val)
            alphas.append(a_val)
            da_list.append(da_val)
            cps.append(c_val)
            dcp_list.append(dcp_val)
            ks.append(k_val)
            dk_list.append(dk_val)

        except ValueError:
            continue

    return {
        "temps": temps,
        "alphas": alphas,
        "da": da_list,
        "cps": cps,
        "dcp": dcp_list,
        "ks": ks,
        "dk": dk_list,
    }


def draw_custom_plot(dialog, selection):
    """Renders the selected plots in a separate PlotWindow."""
    data = read_source_data(dialog)
    if not data["temps"]:
        QMessageBox.warning(dialog, "No Data", "No valid data to plot.")
        return

    selected_props = selection["selected_properties"]
    rows = selection["rows"]
    cols = selection["cols"]

    subplots_data = []
    temp_label = f"Temperature ({dialog.units['temp']})"

    PROP_MAP = {
        "Thermal Diffusivity (α)": ("alphas", "da", "α (mm²/s)", "blue"),
        "Specific Heat (Cp)": ("cps", "dcp", "Cp (J/g·K)", "green"),
        "Thermal Conductivity (κ)": ("ks", "dk", "κ (W/mK)", "red"),
    }

    for prop_name in selected_props:
        if prop_name in PROP_MAP:
            key, err_key, ylabel, color = PROP_MAP[prop_name]
            y_data = data[key]
            y_err = data[err_key]
            valid_x = []
            valid_y = []
            valid_yerr = []
            for x, y, dy in zip(data["temps"], y_data, y_err):
                if not np.isnan(x) and not np.isnan(y):
                    valid_x.append(x)
                    valid_y.append(y)
                    valid_yerr.append(dy if not np.isnan(dy) else 0.0)

            if valid_x:
                subplots_data.append(
                    {
                        "x": valid_x,
                        "y": valid_y,
                        "yerr": valid_yerr if any(v > 0 for v in valid_yerr) else None,
                        "title": f"{prop_name} vs. T",
                        "xlabel": temp_label,
                        "ylabel": ylabel,
                        "color": color,
                    }
                )
        elif prop_name == "Molar Specific Heat (Molar Cp)":
            # Molar heat capacity: Cp [J/(g*K)] * M [g/mol] = J/(mol*K).
            # The gram factors cancel, so no extra 1/1000 factor applies.
            # (The previous "/1000" produced values 1000x too small - i.e. in
            # kJ/(mol*K) - while the axis was labelled J/(mol*K), which also
            # placed the Dulong-Petit overlay ~1000x off the curve.
            # See docs/SCIENTIFIC_EQUATION_AUDIT.md, issue SE-003.)
            molar_cp_data = [
                (cp * dialog.molecular_weight) if not np.isnan(cp) else np.nan
                for cp in data["cps"]
            ]
            valid_x, valid_y = [], []
            for x, y in zip(data["temps"], molar_cp_data):
                if not np.isnan(x) and not np.isnan(y):
                    valid_x.append(x)
                    valid_y.append(y)
            if valid_x:
                subplots_data.append(
                    {
                        "x": valid_x,
                        "y": valid_y,
                        "title": "Molar Specific Heat vs. T",
                        "xlabel": temp_label,
                        "ylabel": "Molar Cp (J/mol·K)",
                    }
                )

    if not subplots_data:
        QMessageBox.warning(
            dialog, "No Plot Data", "Could not generate any of the selected plots."
        )
        return

    # Add DP Limit overlay
    if dialog.plot_dp_check.isChecked() and dialog.molecular_weight:
        dp_limit = calculate_dulong_petit_limit_use_case(
            dialog.atoms_per_formula_unit, dialog.molecular_weight, "J/mol·K"
        )
        found_molar = False
        for plot_data in subplots_data:
            if plot_data.get("title") == "Molar Specific Heat vs. T":
                plot_data["hlines"] = [
                    {
                        "y": dp_limit,
                        "color": "purple",
                        "linestyle": "--",
                        "label": f"D-P Limit ({dp_limit:.1f} J/mol·K)",
                    }
                ]
                found_molar = True
                break
        if not found_molar:
            dp_specific = calculate_dulong_petit_limit_use_case(
                dialog.atoms_per_formula_unit, dialog.molecular_weight, "J/kg·K"
            )
            for plot_data in subplots_data:
                if "Specific Heat (Cp)" in plot_data.get("title", ""):
                    plot_data["hlines"] = [
                        {
                            "y": dp_specific,
                            "color": "purple",
                            "linestyle": "--",
                            "label": f"D-P Limit ({dp_specific:.1f} J/kg·K)",
                        }
                    ]
                    break

    plot_win = PlotWindow(dialog)
    plot_win.setWindowTitle("Thermal Properties Plots")
    plot_win.plot_multi(subplots_data, rows, cols)
    plot_win.show()
    if not hasattr(dialog, "plot_windows"):
        dialog.plot_windows = []
    dialog.plot_windows.append(plot_win)
