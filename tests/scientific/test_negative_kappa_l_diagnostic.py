"""Phase 3 regression tests for the negative-lattice-conductivity diagnostic.

Audit finding D-01: the domain validators produced a correct warning for a
physically impossible lattice thermal conductivity, but **no production path
called them**, so the warning never reached the user. These tests lock in
the fix:

* the application layer produces the notices (plain records);
* the presentation layer formats them without importing Qt or the domain;
* the GUI presents them, and the **calculated value is preserved** - a
  negative kappa_L is never clipped to zero.

The GUI-level assertions run only where Qt is available; they are skipped
(otherwise) with the reason recorded, and they are executed in the
Qt-capable virtual environment.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from seebeck_prime.application.use_cases import (  # noqa: E402
    calculate_thermoelectric_properties,
    validate_calculated_properties,
    validate_multi_sample_properties,
)
from seebeck_prime.domain import calculations as calc  # noqa: E402
from seebeck_prime.presentation import validation_notices  # noqa: E402


# =====================================================================
# Application layer: the notices are actually produced
# =====================================================================

def test_a_negative_lattice_conductivity_produces_a_notice():
    """kappa_total < kappa_e is physically impossible and must be reported."""
    notices = validate_calculated_properties(
        T=np.array([300.0, 350.0]),
        sigma=np.array([1.0e6, 1.0e6]),
        S=np.array([-1.0e-4, -1.0e-4]),
        kappa=np.array([1.0, 1.0]),
        kappa_L=np.array([-0.5, -0.4]),
    )

    kappa_l_notices = [n for n in notices if n["field"] == "kappa_L"]
    assert kappa_l_notices, f"no kappa_L notice was produced: {notices}"
    assert kappa_l_notices[0]["severity"] == "warning"
    assert "Lattice thermal conductivity" in kappa_l_notices[0]["message"]


def test_a_positive_lattice_conductivity_produces_no_kappa_notice():
    notices = validate_calculated_properties(
        T=np.array([300.0]),
        sigma=np.array([1.0e5]),
        S=np.array([-1.0e-4]),
        kappa=np.array([2.0]),
        kappa_L=np.array([1.6]),
    )
    assert [n for n in notices if n["field"] == "kappa_L"] == []


def test_an_empty_table_produces_no_notices():
    """An empty table is the normal initial state, not a data error."""
    assert validate_calculated_properties(
        T=np.array([]), sigma=np.array([]), S=np.array([])
    ) == []
    assert validate_calculated_properties(
        T=np.array([np.nan, np.nan]), sigma=np.array([np.nan]), S=np.array([np.nan])
    ) == []


def test_a_non_positive_temperature_is_an_error_notice():
    notices = validate_calculated_properties(
        T=np.array([300.0, -5.0]),
        sigma=np.array([1.0e5, 1.0e5]),
        S=np.array([-1.0e-4, -1.0e-4]),
    )
    errors = [n for n in notices if n["severity"] == "error"]
    assert errors, f"no error notice for a negative temperature: {notices}"
    assert errors[0]["field"] == "T"


def test_notices_are_plain_records_with_the_expected_keys():
    """The presentation layer must not have to import the domain types."""
    notices = validate_calculated_properties(
        T=np.array([300.0]), sigma=np.array([1.0e6]), S=np.array([-1.0e-4]),
        kappa=np.array([1.0]), kappa_L=np.array([-0.5]),
    )
    for notice in notices:
        assert set(notice) == {"severity", "field", "message"}
        assert isinstance(notice["severity"], str)
        assert isinstance(notice["field"], str)
        assert isinstance(notice["message"], str)


# =====================================================================
# The calculated value is preserved - never clipped
# =====================================================================

def test_a_negative_lattice_conductivity_is_not_clipped_to_zero():
    """The diagnostic value must survive into the data."""
    result = calculate_thermoelectric_properties(
        T=np.array([300.0]),
        sigma=np.array([1.0e6]),
        S=np.array([-1.0e-4]),
        kappa=np.array([1.0]),
    )
    assert result["kappa_L"][0] < 0.0
    assert result["kappa_L"][0] == pytest.approx(
        calc.calculate_kappa_l(1.0, calc.calculate_kappa_e(1.0e6, 300.0)),
        rel=1e-12,
    )
    # the domain function itself is untouched by the presentation change
    assert calc.calculate_kappa_l(1.0, 1.5) == pytest.approx(-0.5, rel=1e-12)


def test_the_presentation_layer_does_not_modify_values():
    """Formatting a notice must not alter the data it describes."""
    notices = validate_calculated_properties(
        T=np.array([300.0]), sigma=np.array([1.0e6]), S=np.array([-1.0e-4]),
        kappa=np.array([1.0]), kappa_L=np.array([-0.5]),
    )
    before = list(notices)
    validation_notices.format_detail(notices)
    validation_notices.summarise(notices)
    validation_notices.notice_signature(notices)
    assert notices == before


# =====================================================================
# Presentation layer
# =====================================================================

def test_the_presentation_module_has_no_qt_or_domain_dependency():
    """Layer boundary: the presentation layer stays free of Qt and domain."""
    import ast

    tree = ast.parse(
        pathlib.Path(validation_notices.__file__).read_text(encoding="utf-8")
    )
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                imported.add(node.module.split(".")[0])

    assert "PyQt6" not in imported
    assert not any(name.startswith("seebeck_prime") for name in imported)


def test_summary_and_detail_name_the_offending_field():
    notices = validate_calculated_properties(
        T=np.array([300.0]), sigma=np.array([1.0e6]), S=np.array([-1.0e-4]),
        kappa=np.array([1.0]), kappa_L=np.array([-0.5]),
    )

    summary = validation_notices.summarise(notices)
    assert "warning" in summary
    assert "kappa_L" in summary

    detail = validation_notices.format_detail(notices)
    assert "Warning" in detail
    assert "kappa_L" in detail
    assert "Lattice thermal conductivity" in detail


def test_an_empty_notice_set_summarises_to_nothing():
    assert validation_notices.summarise([]) == ""
    assert validation_notices.format_detail([]) == ""
    assert validation_notices.has_blocking_notices([]) is False


def test_errors_are_reported_before_warnings():
    notices = [
        {"severity": "warning", "field": "kappa_L", "message": "w"},
        {"severity": "error", "field": "T", "message": "e"},
    ]
    detail = validation_notices.format_detail(notices)
    assert detail.index("Error") < detail.index("Warning")
    assert validation_notices.has_blocking_notices(notices) is True


def test_the_notice_signature_changes_with_the_content():
    a = [{"severity": "warning", "field": "kappa_L", "message": "m"}]
    b = [{"severity": "warning", "field": "kappa_L", "message": "different"}]
    assert validation_notices.notice_signature(a) != validation_notices.notice_signature(b)
    assert validation_notices.notice_signature(a) == validation_notices.notice_signature(list(a))


# =====================================================================
# Multi-sample workflow
# =====================================================================

def test_multi_sample_validation_names_the_offending_sample():
    import pandas as pd

    frame = pd.DataFrame(
        {
            "Temperature": [300.0, 350.0],
            "Seebeck": [-1.0e-4, -1.0e-4],
            "Sigma": [1.0e6, 1.0e6],
            "Kappa_total": [1.0, 1.0],
            "Electronic TC": [1.5, 1.8],
            "Lattice TC": [-0.5, -0.8],
            "ZT": [0.5, 0.6],
        }
    )
    notices = validate_multi_sample_properties({"Sample A": frame})

    assert notices
    assert "Sample A" in notices[0]["message"]
    assert notices[0]["field"] == "kappa_L"


def test_multi_sample_validation_of_a_good_sample_is_silent():
    import pandas as pd

    frame = pd.DataFrame(
        {
            "Temperature": [300.0, 350.0],
            "Seebeck": [-1.0e-4, -1.0e-4],
            "Sigma": [1.0e5, 1.0e5],
            "Kappa_total": [2.0, 2.0],
            "Electronic TC": [0.7, 0.8],
            "Lattice TC": [1.3, 1.2],
            "ZT": [0.5, 0.6],
        }
    )
    assert validate_multi_sample_properties({"Sample A": frame}) == []


# =====================================================================
# GUI level - runs where Qt is available
# =====================================================================

def _qt_available() -> bool:
    try:
        import PyQt6.QtWidgets  # noqa: F401
    except Exception:
        return False
    return True


def _single_row_window_data(temperature, sigma, seebeck, kappa):
    """A one-row table frame matching the application's column contract."""
    import pandas as pd

    from seebeck_prime.application.table_schema import COLUMN_HEADERS

    frame = pd.DataFrame({column: [float("nan")] for column in COLUMN_HEADERS})
    frame.loc[0, "Temperature"] = temperature
    frame.loc[0, "Electrical Conductivity"] = sigma
    frame.loc[0, "Seebeck Coeff."] = seebeck
    frame.loc[0, "Thermal Cond."] = kappa
    return frame


@pytest.mark.skipif(not _qt_available(), reason="PyQt6 QtWidgets is not available")
def test_the_main_window_reports_a_negative_lattice_conductivity(monkeypatch):
    """The GUI must surface the warning and keep the negative value."""
    from PyQt6.QtWidgets import QApplication, QMessageBox

    from seebeck_prime.gui.main_window import ThermoelectricApp

    app = QApplication.instance() or QApplication([])

    shown: list[str] = []

    def _capture(parent, title, text, *args, **kwargs):
        shown.append(f"{title}\n{text}")
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "warning", staticmethod(_capture))

    window = ThermoelectricApp()
    try:
        # a physically impossible combination: kappa_total < kappa_e
        window.data = _single_row_window_data(
            temperature=300.0, sigma=1.0e6, seebeck=-1.0e-4, kappa=1.0
        )
        window.recalculate_all_properties()

        assert shown, "no warning was presented for a negative kappa_L"
        assert "kappa_L" in shown[0]
        assert "Lattice thermal conductivity" in shown[0]

        # the persistent indicator is switched on.  ``isVisible()`` cannot be
        # used headlessly because the parent window is never shown, so the
        # check is that the widget is not explicitly hidden and that it
        # carries the expected text.
        assert not window.validation_notice_label.isHidden()
        assert "kappa_L" in window.validation_notice_label.text()

        # and the value itself is preserved, not clipped
        assert float(window.data["Lattice TC"].iloc[0]) < 0.0
    finally:
        window.close()
        app.processEvents()


@pytest.mark.skipif(not _qt_available(), reason="PyQt6 QtWidgets is not available")
def test_the_main_window_does_not_warn_for_a_physical_dataset(monkeypatch):
    from PyQt6.QtWidgets import QApplication, QMessageBox

    from seebeck_prime.gui.main_window import ThermoelectricApp

    app = QApplication.instance() or QApplication([])

    shown: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "warning",
        staticmethod(lambda *a, **k: shown.append(str(a)) or QMessageBox.StandardButton.Ok),
    )

    window = ThermoelectricApp()
    try:
        window.data = _single_row_window_data(
            temperature=300.0, sigma=1.0e5, seebeck=-1.0e-4, kappa=2.0
        )
        window.recalculate_all_properties()

        assert shown == [], f"an unexpected warning was shown: {shown}"
        assert window.validation_notice_label.isHidden()
        assert float(window.data["Lattice TC"].iloc[0]) > 0.0
    finally:
        window.close()
        app.processEvents()
