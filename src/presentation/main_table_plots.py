import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QMessageBox
from seebeck_prime.presentation.plot_window import PlotWindow

from seebeck_prime.application.table_schema import (
    COL_TEMP,
    COL_EC,
    COL_SEEBECK,
    COL_PF,
    COL_K_TOTAL,
    COL_K_E,
    COL_K_L,
    COL_ZT,
)
from seebeck_prime.application.use_cases import (
    calculate_weighted_mobility_use_case as calculate_weighted_mobility,
    convert_resistivity_to_mohm_cm,
)
from seebeck_prime.application.unit_conversion import from_base_values
from .table_plot_data import get_table_data
from .table_plot_data import PlotDataContext


def resolve_plot_context(main_window):
    """Build explicit plot inputs from the active main window's state."""
    return PlotDataContext(
        frame=main_window.data,
        error_mode=main_window.error_mode,
        header_label=lambda column_index: main_window.table
        .horizontalHeaderItem(column_index)
        .text()
        .replace("\n", " "),
    )


def create_plot(main_window, y_col_index):
    """Creates a plot of the specified column vs. Temperature."""
    context = resolve_plot_context(main_window)
    x_data, y_data, x_err, y_err = get_table_data(
        context.frame, y_col_index, context.error_mode
    )

    if x_data is None:
        return

    # Get labels
    if context.error_mode:
        x_h_idx = 0
        h_idx = y_col_index * 2 - 1 if y_col_index > 0 else 0
    else:
        x_h_idx = COL_TEMP
        h_idx = y_col_index

    x_label = context.header_label(x_h_idx)
    y_label = context.header_label(h_idx)
    title = f"{y_label} vs. {x_label}"

    # Create and show the plot window
    plot_win = PlotWindow(main_window)

    # We pass the data in a trace-like structure to support error bars
    trace = {
        "x": x_data,
        "y": y_data,
        "xerr": x_err if any(x_err) else None,
        "yerr": y_err if any(y_err) else None,
        "label": y_label,
    }

    plot_win.subplots = [
        {"traces": [trace], "title": title, "xlabel": x_label, "ylabel": y_label}
    ]
    plot_win.draw_plot()

    main_window.plot_windows.append(plot_win)
    plot_win.show()


def plot_all_properties(main_window):
    """Plots all relevant properties vs Temperature."""
    properties_to_plot = [
        COL_SEEBECK,
        COL_EC,
        COL_PF,
        COL_K_TOTAL,
        COL_K_L,
        COL_K_E,
        COL_ZT,
    ]

    context = resolve_plot_context(main_window)

    # Check if we have any data
    has_any_data = False
    for col in properties_to_plot:
        x_data, _, _, _ = get_table_data(context.frame, col, context.error_mode)
        if x_data:
            has_any_data = True
            create_plot(main_window, col)

    if not has_any_data:
        QMessageBox.warning(main_window, "No Data", "No valid data to plot.")


def plot_custom_layout(main_window, selection):
    """Plots selected properties in a custom grid layout."""
    selected_props = selection["selected_properties"]
    rows = selection["rows"]
    cols = selection["cols"]

    if not selected_props:
        return

    PROP_MAP = {
        "Seebeck Coeff.": COL_SEEBECK,
        "Electrical Conductivity": COL_EC,
        "Power Factor": COL_PF,
        "Thermal Cond.": COL_K_TOTAL,
        "Electronic TC": COL_K_E,
        "Lattice TC": COL_K_L,
        "ZT": COL_ZT,
        "Weighted Mobility": -1,  # Special flag
    }

    context = resolve_plot_context(main_window)
    subplots_data = []
    x_label = context.header_label(COL_TEMP)

    for prop_name in selected_props:
        col_idx = PROP_MAP.get(prop_name)
        if col_idx is None:
            continue

        if prop_name == "Weighted Mobility":
            # Special handling for on-the-fly calculation
            t_data, _, _, _ = get_table_data(context.frame, COL_TEMP, context.error_mode)
            s_data, _, _, _ = get_table_data(context.frame, COL_SEEBECK, context.error_mode)
            sigma_data, _, _, _ = get_table_data(context.frame, COL_EC, context.error_mode)

            if t_data and s_data and sigma_data:
                # We need to ensure we have aligned data (get_table_data sorts by T, so if all rows present, should be fine)
                # But get_table_data skips rows with missing Y. If S or Sigma is missing but T is there...
                # This might be tricky if data is sparse.
                # Ideally we use main_window.data directly which is easier.

                try:
                    df = context.frame.copy()
                    df = df.apply(pd.to_numeric, errors="coerce")

                    # Filter valid rows
                    mask = (
                        (df["Temperature"].notna())
                        & (df["Electrical Conductivity"].notna())
                        & (df["Seebeck Coeff."].notna())
                    )
                    valid_df = df[mask].sort_values("Temperature")

                    if not valid_df.empty:
                        # Base units are K, S/m, V/K
                        # Target for formula: K, mOhm.cm, absolute uV/K
                        # (conversions delegated to the application layer)

                        T_K = valid_df["Temperature"].values
                        # Sigma S/m -> Rho mOhm.cm
                        Rho_mOhm_cm = convert_resistivity_to_mohm_cm(
                            valid_df["Electrical Conductivity"].values, "S/m"
                        )

                        # Seebeck V/K -> uV/K
                        S_uVK = from_base_values(
                            valid_df["Seebeck Coeff."].values, "uV/K", "seebeck"
                        )

                        mu_w = calculate_weighted_mobility(
                            T_K, Rho_mOhm_cm, np.abs(S_uVK)
                        )

                        title = "Weighted Mobility vs. Temperature"
                        y_label = "Weighted Mobility (cm²/Vs)"

                        trace = {
                            "x": T_K.tolist(),
                            "y": mu_w.tolist(),
                            "xerr": None,
                            "yerr": None,
                            "label": y_label,
                        }

                        subplots_data.append(
                            {
                                "traces": [trace],
                                "title": title,
                                "xlabel": "Temperature (K)",
                                "ylabel": y_label,
                                "x": T_K.tolist(),
                                "y": mu_w.tolist(),
                            }
                        )
                        continue  # Done with this prop
                except Exception as e:
                    print(f"Error calculating Weighted Mobility for plot: {e}")

            continue  # Skip if failed or no data, or if it was Weighted Mobility handled above

        col_idx = PROP_MAP.get(prop_name)
        if col_idx is None or col_idx == -1:  # -1 Handled above already
            continue

        x_data, y_data, x_err, y_err = get_table_data(
            context.frame, col_idx, context.error_mode
        )

        if x_data:
            if context.error_mode:
                h_idx = col_idx * 2 - 1 if col_idx > 0 else 0
            else:
                h_idx = col_idx

            y_label = context.header_label(h_idx)
            title = f"{y_label} vs. {x_label}"

            trace = {
                "x": x_data,
                "y": y_data,
                "xerr": x_err if any(x_err) else None,
                "yerr": y_err if any(y_err) else None,
                "label": y_label,
            }

            subplots_data.append(
                {
                    "traces": [trace],
                    "title": title,
                    "xlabel": x_label,
                    "ylabel": y_label,
                    "x": x_data,  # For backward compat in export if needed
                    "y": y_data,
                }
            )

    if not subplots_data:
        QMessageBox.warning(main_window, "No Data", "No valid data to plot.")
        return

    plot_win = PlotWindow(main_window)
    plot_win.plot_multi(subplots_data, rows, cols)
    main_window.plot_windows.append(plot_win)
    plot_win.show()
