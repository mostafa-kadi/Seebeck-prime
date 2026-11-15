"""Driver for the GUI end-to-end workflow (run as a separate process).

The desktop stack is driven here rather than inside the pytest process: a
QApplication must exist before any widget is constructed, and Qt aborts the
interpreter natively when it does not - a failure mode that cannot be caught
by pytest. Running the workflow in a subprocess keeps the test suite stable
and mirrors how the application is actually used.

Usage:
    python gui_workflow_driver.py <benchmark_raw_dir> <output_json>

The driver prints a JSON summary of the recalculated properties.
"""

from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for candidate in (REPO_ROOT, os.path.join(REPO_ROOT, "src")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


def main() -> int:
    raw_dir, output_path = sys.argv[1], sys.argv[2]

    import numpy as np
    import pandas as pd
    from PyQt6.QtWidgets import QApplication

    from seebeck_prime.application.table_files import TableFileService
    from seebeck_prime.gui.main_window import ThermoelectricApp
    from seebeck_prime.infrastructure.io import PandasTabularDataStore

    qapplication = QApplication.instance() or QApplication([])
    print("driver: QApplication ready", flush=True)

    def published_curves(name: str) -> dict:
        frame = pd.read_csv(os.path.join(raw_dir, f"{name}_curves.csv"))
        curves = {}
        for row in frame.itertuples(index=False):
            xs = np.array([v for v in json.loads(row.x) if v is not None], dtype=float)
            ys = np.array([v for v in json.loads(row.y) if v is not None], dtype=float)
            n = min(len(xs), len(ys))
            order = np.argsort(xs[:n])
            curves[row.prop_y] = (xs[:n][order], ys[:n][order])
        return curves

    name = "b2te3_bi2te2_4se0_6cu0_006"
    curves = published_curves(name)
    temperature, seebeck = curves["Seebeck coefficient"]
    sigma = np.interp(temperature, *curves["Electrical conductivity"])
    kappa = np.interp(temperature, *curves["Thermal conductivity"])

    display_frame = pd.DataFrame({
        "Temperature (K)": temperature,
        "Conductivity (S/cm)": sigma / 100.0,
        "Seebeck (uV/K)": seebeck * 1e6,
        "Thermal Conductivity (W/mK)": kappa,
    })
    base_frame = pd.DataFrame({
        "Temperature": temperature,
        "Electrical Conductivity": sigma,
        "Seebeck Coeff.": seebeck,
        "Thermal Cond.": kappa,
    })

    store = PandasTabularDataStore()
    window = ThermoelectricApp(
        table_file_service=TableFileService(store), measurement_data_store=store
    )
    print("driver: window ready", flush=True)

    # --- path 1: the user workflow (display units, via the file service) ----
    csv_path = os.path.join(output_path + ".csv")
    display_frame.to_csv(csv_path, index=False)
    loaded = window.table_file_service.load(csv_path)
    print("driver: file loaded", flush=True)
    mapped = window._get_mapped_dataframe(loaded)
    print("driver: mapped", flush=True)
    window.load_data_into_table(mapped)
    print("driver: loaded into table", flush=True)
    window.recalculate_all_properties()
    print("driver: recalculated (display path)", flush=True)
    display_result = {
        "columns": list(window.data.columns),
        "power_factor": window.data["Power Factor"].tolist(),
        "zt": window.data["ZT"].tolist(),
        "electronic_tc": window.data["Electronic TC"].tolist(),
        "lattice_tc": window.data["Lattice TC"].tolist(),
        "temperature": window.data["Temperature"].tolist(),
    }

    # --- path 2: base units through the is_base_units flag ------------------
    window.reset_and_create_new_sheet()
    window.load_data_into_table(
        window._get_mapped_dataframe(base_frame), is_base_units=True
    )
    window.recalculate_all_properties()
    base_result = {
        "power_factor": window.data["Power Factor"].tolist(),
        "zt": window.data["ZT"].tolist(),
    }

    # --- the displayed spreadsheet must agree with the model ----------------
    # The table renders the values in the *display* units (the power factor is
    # shown in mW/(m*K^2) by default), while app.data holds the base units
    # (W/(m*K^2)). The application's own conversion path is used to obtain the
    # value that must appear in the cell.
    from seebeck_prime.application.table_schema import COL_PF, COL_ZT

    headers = [
        window.table.horizontalHeaderItem(c).text()
        for c in range(window.table.columnCount())
    ]
    pf_column = next(c for c, h in enumerate(headers) if "Power Factor" in h)
    zt_column = next(c for c, h in enumerate(headers) if h.strip() == "ZT")

    expected_display_pf, _ = window._convert_from_base_unit(
        window.data["Power Factor"].iloc[0], None, COL_PF
    )
    expected_display_zt, _ = window._convert_from_base_unit(
        window.data["ZT"].iloc[0], None, COL_ZT
    )
    displayed = {
        "power_factor": float(window.table.item(0, pf_column).text()),
        "zt": float(window.table.item(0, zt_column).text()),
        "expected_power_factor": float(expected_display_pf),
        "expected_zt": float(expected_display_zt),
        "pf_display_unit": window.units.get("pf"),
        "headers": headers,
    }

    # --- error-bar column contract -------------------------------------------
    # The error-bar workflow itself is interactive: enabling it opens the
    # modal ErrorBarDialog (main_window.toggle_error_bars -> dialog.exec()),
    # which cannot be driven without a user. The *column contract* it applies
    # is therefore verified here at the schema level; the uncertainty
    # arithmetic behind it is covered by the equation audit and by the
    # importer tests.
    from seebeck_prime.presentation.table_handler import get_column_headers

    error_headers = get_column_headers(True)

    summary = {
        "display_path": display_result,
        "base_path": base_result,
        "displayed": displayed,
        "error_mode_headers": error_headers,
        "error_mode_interactive": True,
        "expected_power_factor": ((seebeck**2) * sigma).tolist(),
        "expected_zt": (((seebeck**2) * sigma) * temperature / kappa).tolist(),
        "rows": len(temperature),
    }
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle)

    os.remove(csv_path)
    print("driver: closing", flush=True)
    window.close()
    del qapplication
    return 0


if __name__ == "__main__":
    sys.exit(main())
