"""Stage 7 startup and core-workflow smoke tests.

These verify that the application starts importing cleanly and that the
composition-root wiring (Application service + Infrastructure store) works
end-to-end without a GUI session.

The full ``import main`` smoke test is conditional on PyQt6 being importable
in the local environment; on machines where the Qt DLLs cannot load, the
static no-side-effect check still guarantees that importing ``main`` performs
no GUI initialization at module level.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for candidate in (REPO_ROOT, REPO_ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def _qt_available() -> bool:
    try:
        import PyQt6.QtWidgets  # noqa: F401

        return True
    except (ImportError, OSError):
        return False


def test_main_module_has_no_gui_side_effects_at_import():
    """Importing main.py must not create QApplication or windows at module level."""
    source = (REPO_ROOT / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="main.py")

    module_level_calls = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for sub_node in ast.walk(node):
            if sub_node is not node and isinstance(sub_node, ast.Call):
                module_level_calls.append(sub_node)

    # Only the sys.path/environment setup calls and os.add_dll_directory are
    # allowed at module level; QApplication/window construction must stay in main().
    for call in module_level_calls:
        name = None
        if isinstance(call.func, ast.Name):
            name = call.func.id
        elif isinstance(call.func, ast.Attribute):
            name = call.func.attr
        assert name not in {"QApplication", "ThermoelectricApp", "show", "exec"}, (
            f"GUI side effect at module level: {name}"
        )

    assert (REPO_ROOT / "main.py").read_text(encoding="utf-8").rstrip().endswith(
        'main()'
    ) or "__main__" in source


def test_import_main_smoke_when_qt_available():
    if not _qt_available():
        pytest.skip(
            "PyQt6 QtWidgets cannot load in this environment (Qt DLL issue); "
            "run on a machine with working Qt bindings"
        )

    main_module = importlib.import_module("main")

    assert callable(main_module.main)
    assert main_module.ThermoelectricApp.__name__ == "ThermoelectricApp"
    # Composition root classes resolve through the canonical layer locations.
    assert main_module.TableFileService is not None
    assert main_module.PandasTabularDataStore is not None


def test_composition_root_wiring_import_export_analyze_round_trip(tmp_path):
    """Core workflow without a GUI: save -> load -> analyze measurement data."""
    from seebeck_prime.application.table_files import TableFileService
    from seebeck_prime.application.use_cases import (
        calculate_thermoelectric_properties,
    )
    from seebeck_prime.infrastructure.io import PandasTabularDataStore

    service = TableFileService(PandasTabularDataStore())

    source = pd.DataFrame(
        {
            "Temperature": [300.0, 400.0, 500.0],
            "Seebeck": [100e-6, 150e-6, 180e-6],
            "Sigma": [1e5, 8e4, 6e4],
            "Kappa": [2.0, 1.8, 1.6],
        }
    )

    for suffix in (".csv", ".xlsx"):
        path = tmp_path / f"measurement{suffix}"
        service.save(source, path)
        loaded = service.load(path)
        assert list(loaded.columns) == list(source.columns)
        for column in ("Temperature", "Seebeck", "Sigma", "Kappa"):
            assert loaded[column].tolist() == pytest.approx(
                source[column].tolist(), rel=1e-9
            )

        result = calculate_thermoelectric_properties(
            loaded["Temperature"].to_numpy(),
            loaded["Sigma"].to_numpy(),
            loaded["Seebeck"].to_numpy(),
            loaded["Kappa"].to_numpy(),
        )
        assert set(result) == {
            "T", "sigma", "S", "PF", "kappa_e", "kappa_L", "ZT", "kappa",
        }
        assert result["ZT"][0] == pytest.approx(
            (source["Seebeck"][0] ** 2) * source["Sigma"][0]
            * source["Temperature"][0]
            / source["Kappa"][0],
            rel=1e-9,
        )
