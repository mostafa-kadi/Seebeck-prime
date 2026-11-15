import ast
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

from seebeck_prime.application.unit_conversion import (
    convert_temperature_to_kelvin,
    seebeck_to_uvk,
)
from seebeck_prime.application.use_cases import (
    process_multi_sample_batch,
    process_multi_sample_data,
)
from seebeck_prime.application.table_files import MultiSampleFileError, TableFileService
from seebeck_prime.infrastructure.io import PandasTabularDataStore
from seebeck_prime.application.data_mapping import get_robust_mapped_dataframe
from seebeck_prime.presentation.multi_sample_plots import plot_comparisons
from seebeck_prime.application.spb_batch import (
    SPBBatchRowResult,
    calculate_spb_batch_mean_parameters,
    calculate_spb_batch_rows,
)
from seebeck_prime.domain import spb as spb_domain_model


def _sample_frame():
    return pd.DataFrame(
        {
            "Temperature": [300.0, 400.0],
            "Seebeck": [100e-6, -200e-6],
            "Sigma": [1e5, 8e4],
            "Kappa_total": [2.0, 1.5],
        }
    )


def test_multi_sample_calculation_preserves_input_and_output_contract():
    source = _sample_frame()
    original = source.copy(deep=True)

    result = process_multi_sample_data(source)

    pd.testing.assert_frame_equal(source, original)
    assert result["Power Factor"].tolist() == pytest.approx([1e-3, 3.2e-3])
    assert result["PF_mW"].tolist() == pytest.approx([1.0, 3.2])
    assert result["Sigma_Scm"].tolist() == pytest.approx([1e3, 800.0])
    assert result["S_uVK"].tolist() == pytest.approx([100.0, -200.0])
    assert result["Electronic TC"].tolist() == pytest.approx([0.732, 0.7808])
    assert result["Lattice TC"].tolist() == pytest.approx([1.268, 0.7192])
    assert result["ZT"].tolist() == pytest.approx([0.15, 0.8533333333333334])


def test_multi_sample_batch_and_workbook_export_preserve_names_and_sheets(
    tmp_path,
):
    source = _sample_frame()
    workbook = tmp_path / "Comparison_Results.xlsx"

    results = process_multi_sample_batch(
        {"Sample A": source, "Sample B": source.copy()}
    )
    TableFileService(PandasTabularDataStore()).save_workbook(
        [(name, frame) for name, frame in results.items()], str(workbook)
    )

    assert list(results) == ["Sample A", "Sample B"]
    assert workbook.exists()
    excel = pd.ExcelFile(workbook)
    assert excel.sheet_names == ["Sample A", "Sample B"]
    for sheet in excel.sheet_names:
        exported = pd.read_excel(workbook, sheet_name=sheet)
        assert {"Power Factor", "Electronic TC", "Lattice TC", "ZT"}.issubset(
            exported.columns
        )


def test_multi_sample_application_batch_use_case_preserves_names_and_order():
    source_a = _sample_frame()
    source_b = _sample_frame().iloc[:1].copy()
    original_a = source_a.copy(deep=True)

    results = process_multi_sample_batch({"A": source_a, "B": source_b})

    assert list(results) == ["A", "B"]
    assert len(results["A"]) == 2
    assert len(results["B"]) == 1
    assert "ZT" in results["A"] and "ZT" in results["B"]
    assert results["A"]["Electronic TC"].tolist() == pytest.approx([0.732, 0.7808])
    pd.testing.assert_frame_equal(source_a, original_a)


def test_multi_sample_presentation_plot_preserves_selected_property_and_styles():
    processed = process_multi_sample_data(_sample_frame())
    settings = {
        "selected_props": [("ZT", "Dimensionless ZT")],
        "multi_panel": False,
        "sample_styles": {
            "Sample A": {"label": "Display A", "color": "#123456", "marker": "s"}
        },
    }

    figures = plot_comparisons({"Sample A": processed}, settings=settings, show=False)

    try:
        assert len(figures) == 1
        axes = figures[0].axes
        assert len(axes) == 1
        assert axes[0].get_ylabel() == "Dimensionless ZT"
        assert axes[0].get_title() == "ZT vs. Temperature"
        line = axes[0].lines[0]
        assert line.get_label() == "Display A"
        assert line.get_marker() == "s"
        assert line.get_color() == "#123456"
        np.testing.assert_allclose(line.get_ydata(), processed["ZT"].to_numpy())
    finally:
        for figure in figures:
            matplotlib.pyplot.close(figure)


class _Cell:
    def __init__(self, value):
        self.value = value

    def text(self):
        return self.value


class _Table:
    def __init__(self, rows):
        self.rows = rows

    def rowCount(self):
        return len(self.rows)

    def item(self, row, column):
        value = self.rows[row][column]
        return None if value is None else _Cell(value)


class _Combo:
    def __init__(self, value):
        self.value = value

    def currentText(self):
        return self.value


class _BatchForm:
    table = _Table(
        [
            ["27", "-0.2", "1e19", None, None, None],
            ["bad", "100", "1e19", None, None, None],
            ["100", None, "2e19", None, None, None],
            ["300", "200", "0", None, None, None],
        ]
    )
    temp_unit_combo = _Combo("C")
    seebeck_unit_combo = _Combo("mV/K")


def _spb_batch_extractor_from_source():
    dialog_path = (
        Path(__file__).resolve().parents[1] / "src" / "presentation" / "dialogs" / "spb_dialog.py"
    )
    tree = ast.parse(dialog_path.read_text(encoding="utf-8"), filename=str(dialog_path))
    dialog_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SPBModelingDialog"
    )
    method = next(
        node
        for node in dialog_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "_extract_table_data"
    )
    namespace = {
        "np": np,
        "convert_temperature_to_kelvin": convert_temperature_to_kelvin,
        "seebeck_to_uvk": seebeck_to_uvk,
    }
    isolated_module = ast.Module(body=[method], type_ignores=[])
    exec(compile(isolated_module, str(dialog_path), "exec"), namespace)
    return namespace["_extract_table_data"]


def test_spb_batch_parser_converts_units_and_skips_invalid_rows():
    extractor = _spb_batch_extractor_from_source()
    temperatures, seebecks, concentrations, rows = extractor(_BatchForm())

    np.testing.assert_allclose(temperatures, [300.15])
    np.testing.assert_allclose(seebecks, [200.0])
    np.testing.assert_allclose(concentrations, [1e19])
    assert rows == [0]


def test_spb_batch_calculation_maps_results_to_original_rows_and_scales_lorenz():
    batch_call = {}

    class FakeItem:
        def __init__(self, text):
            self._text = text
            self._flags = 1
            self.background = None

        def flags(self):
            return self._flags

        def setFlags(self, flags):
            self._flags = flags

        def setBackground(self, color):
            self.background = color

        def text(self):
            return self._text

    class FakeTable(_Table):
        def __init__(self):
            super().__init__(
                [
                    ["27", "-0.2", "1e19", None, None, None],
                    ["bad", "100", "1e19", None, None, None],
                    ["100", None, "2e19", None, None, None],
                    ["300", "200", "0", None, None, None],
                    ["50", "0.1", "2e19", None, None, None],
                ]
            )
            self.outputs = {}

        def setItem(self, row, column, item):
            self.outputs[(row, column)] = item

    table = FakeTable()
    batch_form = SimpleNamespace(
        table=table,
        temp_unit_combo=_Combo("C"),
        seebeck_unit_combo=_Combo("mV/K"),
    )

    class MessageBox:
        @staticmethod
        def warning(*args):
            pytest.fail("valid rows should be calculated")

        @staticmethod
        def information(*args):
            pass

        @staticmethod
        def critical(*args):
            pytest.fail(args[-1])

    class ItemFactory(FakeItem):
        pass

    class FakeQt:
        class ItemFlag:
            ItemIsEditable = 1

        class GlobalColor:
            lightGray = "lightGray"

    namespace = {
        "QMessageBox": MessageBox,
        "QTableWidgetItem": ItemFactory,
        "Qt": FakeQt,
        "calculate_spb_batch_rows": lambda temps, seebecks, ns, rows, scattering: (
            batch_call.update(
                inputs=(list(temps), list(seebecks), list(ns), list(rows), scattering)
            )
            or [
                SPBBatchRowResult(row, eta, mass, 2.0)
                for row, eta, mass in zip(rows, (-1.5, -2.5), (3.0, 4.0))
            ],
            3.5,
        ),
    }
    calculate_table = _spb_batch_method_from_source("calculate_table", namespace)
    dialog = SimpleNamespace(
        _extract_table_data=lambda: _spb_batch_extractor_from_source()(batch_form),
        scat_combo=SimpleNamespace(currentData=lambda: 1),
        table=table,
        table_status=SimpleNamespace(setText=lambda text: setattr(dialog, "status", text)),
    )

    calculate_table(dialog)

    assert batch_call["inputs"] == (
        [300.15, 323.15],
        [200.0, 100.0],
        [1e19, 2e19],
        [0, 4],
        1,
    )
    assert set(table.outputs) == {(0, 3), (0, 4), (0, 5), (4, 3), (4, 4), (4, 5)}
    assert [table.outputs[(0, col)].text() for col in (3, 4, 5)] == [
        "-1.500",
        "3.000",
        "2.000",
    ]
    assert [table.outputs[(4, col)].text() for col in (3, 4, 5)] == [
        "-2.500",
        "4.000",
        "2.000",
    ]
    assert dialog.status.startswith("Calculated 2 data points.")


def _spb_batch_method_from_source(method_name, namespace):
    dialog_path = (
        Path(__file__).resolve().parents[1] / "src" / "presentation" / "dialogs" / "spb_dialog.py"
    )
    tree = ast.parse(dialog_path.read_text(encoding="utf-8"), filename=str(dialog_path))
    dialog_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SPBModelingDialog"
    )
    method = next(
        node
        for node in dialog_class.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )
    isolated_module = ast.Module(body=[method], type_ignores=[])
    exec(compile(isolated_module, str(dialog_path), "exec"), namespace)
    return namespace[method_name]


def test_spb_batch_mean_mass_action_uses_valid_masses_and_mean_temperature():
    updates = {}
    messages = []

    class MessageBox:
        @staticmethod
        def warning(*args):
            pytest.fail("valid batch rows should be available")

        @staticmethod
        def information(*args):
            messages.append(args[-1])

    call = {}
    method = _spb_batch_method_from_source(
        "load_mean_mass_from_table",
        {
            "QMessageBox": MessageBox,
            "calculate_spb_batch_mean_parameters": lambda *args: (
                call.update(args=args) or (1.25, 350.0)
            ),
        },
    )
    dialog = SimpleNamespace(
        _extract_table_data=lambda: (
            np.array([300.0, 400.0]),
            np.array([100.0, 200.0]),
            np.array([1e19, 2e19]),
            [0, 1],
        ),
        scat_combo=SimpleNamespace(currentData=lambda: 2),
        pis_mass_spin=SimpleNamespace(setValue=lambda value: updates.update(mass=value)),
        pis_temp_spin=SimpleNamespace(setValue=lambda value: updates.update(temp=value)),
    )

    method(dialog)

    np.testing.assert_allclose(call["args"][0], [300.0, 400.0])
    np.testing.assert_allclose(call["args"][1], [100.0, 200.0])
    np.testing.assert_allclose(call["args"][2], [1e19, 2e19])
    assert call["args"][3] == 2
    assert updates == {"mass": 1.25, "temp": 350.0}
    assert len(messages) == 1


def test_spb_batch_application_use_case_calculates_in_order_and_excludes_nan_mean(
    monkeypatch,
):
    calls = []

    def calculate_mass(seebeck, concentration, temperature, lambda_scat):
        calls.append((seebeck, concentration, temperature, lambda_scat))
        if temperature == 323.15:
            return np.nan, -2.5
        return 3.0, -1.5

    monkeypatch.setattr(spb_domain_model, "calculate_effective_mass", calculate_mass)
    monkeypatch.setattr(
        spb_domain_model,
        "rigorous_lorenz_number",
        lambda eta, lambda_scat: 2.0e-8,
    )

    results, mean_mass = calculate_spb_batch_rows(
        [300.15, 323.15], [200.0, 100.0], [1e19, 2e19], [0, 4], 1
    )

    assert calls == [(200.0, 1e19, 300.15, 1), (100.0, 2e19, 323.15, 1)]
    assert [result.row_index for result in results] == [0, 4]
    assert [result.reduced_fermi_level for result in results] == [-1.5, -2.5]
    assert results[0].effective_mass == 3.0
    assert np.isnan(results[1].effective_mass)
    assert [result.lorenz_display_value for result in results] == [2.0, 2.0]
    assert mean_mass == 3.0


def test_spb_batch_application_mean_parameters_preserve_legacy_mean_rules(monkeypatch):
    masses = iter([1.0, np.nan])
    monkeypatch.setattr(
        spb_domain_model,
        "calculate_effective_mass",
        lambda *args, **kwargs: (next(masses), 0.0),
    )

    result = calculate_spb_batch_mean_parameters(
        [300.0, 400.0], [100.0, 200.0], [1e19, 2e19], 2
    )

    assert result == (1.0, 350.0)


def test_multi_sample_analysis_processes_only_checked_samples():
    processed_names = []
    plotted = {}
    windows = []
    data = {"checked": _sample_frame(), "unchecked": _sample_frame()}

    class Item:
        def __init__(self, name, checked):
            self.name = name
            self.checked = checked

        def checkState(self):
            return 2 if self.checked else 0

        def text(self):
            return self.name

    class SettingsDialog:
        Accepted = 1

        def __init__(self, names, parent=None):
            self.names = names

        def exec(self):
            return 1

        def get_settings(self):
            return {"selected": True}

    class FakeWindow:
        def __init__(self, parent):
            self.figure = None
            windows.append(self)

        def set_figure(self, figure):
            self.figure = figure

        def show(self):
            pass

    class MessageBox:
        @staticmethod
        def critical(*args):
            pytest.fail(args[-1])

        @staticmethod
        def information(*args):
            pytest.fail(args[-1])

        @staticmethod
        def warning(*args):
            # A scientific validation notice during this orchestration test
            # would mean an unexpected condition; fail loudly.
            pytest.fail(args[-1])

    def process(frame):
        processed_names.append("checked" if frame is data["checked"] else "other")
        return frame

    def process_batch(samples):
        return {name: process(frame) for name, frame in samples.items()}

    def plot(samples, settings, show):
        plotted.update(samples=samples, settings=settings, show=show)
        return ["figure"]

    run_analysis = _multi_sample_method_from_source(
        "run_analysis",
        {
            "Qt": SimpleNamespace(CheckState=SimpleNamespace(Checked=2)),
            "QMessageBox": MessageBox,
            "QDialog": SimpleNamespace(Accepted=1),
            "PlotSettingsDialog": SettingsDialog,
            "PlotWindow": FakeWindow,
            "process_multi_sample_batch": process_batch,
            "plot_comparisons": plot,
            # The scientific validation step of the workflow (audit D-01).
            # The stub frames carry no derived columns, so no notice is
            # expected and the warning branch must not be taken.
            "validate_multi_sample_properties": lambda processed: [],
            "validation_notices": SimpleNamespace(
                format_detail=lambda notices: ""
            ),
        },
    )
    parent = SimpleNamespace(plot_windows=[])
    dialog = SimpleNamespace(
        samples=data,
        sample_list_widget=SimpleNamespace(
            count=lambda: 2,
            item=lambda index: [Item("checked", True), Item("unchecked", False)][index],
        ),
        parent=lambda: parent,
    )

    run_analysis(dialog)

    assert processed_names == ["checked"]
    assert list(plotted["samples"]) == ["checked"]
    assert plotted["settings"] == {"selected": True}
    assert plotted["show"] is False
    assert len(windows) == 1 and windows[0].figure == "figure"
    assert parent.plot_windows == windows


def _multi_sample_method_from_source(method_name, namespace):
    dialog_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "presentation"
        / "dialogs"
        / "multi_sample_dialog.py"
    )
    tree = ast.parse(dialog_path.read_text(encoding="utf-8"), filename=str(dialog_path))
    dialog_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "MultiSampleDialog"
    )
    method = next(
        node
        for node in dialog_class.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )
    isolated_module = ast.Module(body=[method], type_ignores=[])
    exec(compile(isolated_module, str(dialog_path), "exec"), namespace)
    return namespace[method_name]


def test_multi_sample_import_reads_csv_and_each_excel_sheet(tmp_path):
    calls = {"samples": [], "warnings": []}
    csv_path = tmp_path / "one.csv"
    workbook_path = tmp_path / "book.xlsx"
    pd.DataFrame({"temperature": [300.0], "source": ["csv"]}).to_csv(
        csv_path, index=False
    )
    with pd.ExcelWriter(workbook_path) as writer:
        pd.DataFrame({"temperature": [310.0], "source": ["A"]}).to_excel(
            writer, sheet_name="Run A", index=False
        )
        pd.DataFrame({"temperature": [320.0], "source": ["B"]}).to_excel(
            writer, sheet_name="Run B", index=False
        )

    class FileDialog:
        @staticmethod
        def getOpenFileNames(*args):
            return ([str(csv_path), str(workbook_path)], "")

    class MessageBox:
        @staticmethod
        def warning(*args):
            calls["warnings"].append(args[-1])

    method = _multi_sample_method_from_source(
        "add_samples",
        {
            "QFileDialog": FileDialog,
            "QMessageBox": MessageBox,
            "MultiSampleFileError": MultiSampleFileError,
        },
    )
    dialog = SimpleNamespace(
        table_file_service=TableFileService(PandasTabularDataStore()),
        _add_to_dict_and_list=lambda name, frame: calls["samples"].append(
            (name, frame.copy())
        )
    )

    method(dialog)

    assert [name for name, _ in calls["samples"]] == [
        "one.csv",
        "book.xlsx [Run A]",
        "book.xlsx [Run B]",
    ]
    assert calls["samples"][0][1].loc[0, "source"] == "csv"
    assert calls["samples"][1][1].loc[0, "source"] == "A"
    assert calls["samples"][2][1].loc[0, "source"] == "B"
    assert calls["warnings"] == []


def test_multi_sample_dialog_export_writes_every_sample_to_workbook(tmp_path):
    export_path = tmp_path / "dialog_export.xlsx"
    messages = []

    class FileDialog:
        @staticmethod
        def getSaveFileName(*args):
            return (str(export_path), "Excel Files (*.xlsx)")

    class MessageBox:
        @staticmethod
        def information(*args):
            messages.append(("info", args[-1]))

        @staticmethod
        def critical(*args):
            messages.append(("critical", args[-1]))

    method = _multi_sample_method_from_source(
        "export_excel",
        {
            "process_sample_data": process_multi_sample_data,
            "QFileDialog": FileDialog,
            "QMessageBox": MessageBox,
        },
    )
    long_name = "Sample name that exceeds thirty one characters"
    dialog = SimpleNamespace(
        table_file_service=TableFileService(PandasTabularDataStore()),
        samples={long_name: _sample_frame(), "Sample B": _sample_frame()},
    )

    method(dialog)

    assert export_path.exists()
    excel = pd.ExcelFile(export_path)
    assert excel.sheet_names == [long_name[:31], "Sample B"]
    assert all(message[0] == "info" for message in messages)


def test_multi_sample_dialog_export_uses_injected_file_service(tmp_path):
    saved = {}

    class FileDialog:
        @staticmethod
        def getSaveFileName(*args):
            return (str(tmp_path / "results.xlsx"), "Excel Files (*.xlsx)")

    class MessageBox:
        @staticmethod
        def information(*args):
            saved["message"] = args[-1]

        @staticmethod
        def critical(*args):
            pytest.fail(args[-1])

    service = SimpleNamespace(save_workbook=lambda tables, path: saved.update(tables=tables, path=path))
    method = _multi_sample_method_from_source(
        "export_excel",
        {
            "process_sample_data": process_multi_sample_data,
            "QFileDialog": FileDialog,
            "QMessageBox": MessageBox,
        },
    )
    long_name = "Sample name that exceeds thirty one characters"
    dialog = SimpleNamespace(
        samples={long_name: _sample_frame(), "Sample B": _sample_frame()},
        table_file_service=service,
    )

    method(dialog)

    assert saved["path"].endswith("results.xlsx")
    assert [name for name, _ in saved["tables"]] == [long_name[:31], "Sample B"]
    assert all("ZT" in frame for _, frame in saved["tables"])


def test_multi_sample_header_mapper_maps_required_scientific_columns():
    source = pd.DataFrame(
        {
            "Temperature (K)": [300.0],
            "Seebeck Coefficient (uV/K)": [100.0],
            "Electrical Conductivity (S/cm)": [1000.0],
            "Thermal Conductivity (W/mK)": [2.0],
        }
    )
    groups = [
        ("Temperature", ["temperature", "temp", "t"]),
        ("Seebeck", ["seebeck", "alpha", "α", "coeff", "coefficient", "s"]),
        ("Sigma", ["sigma", "conductivity", "electrical", "ec", "resistivity", "rho"]),
        ("Kappa_total", ["kappa", "thermal", "k", "kappa_total"]),
    ]

    mapped = get_robust_mapped_dataframe(source, groups)

    assert list(mapped.columns) == ["Temperature", "Seebeck", "Sigma", "Kappa_total"]
    assert mapped.iloc[0].tolist() == [300.0, 100.0, 1000.0, 2.0]


