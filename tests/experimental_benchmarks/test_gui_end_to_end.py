"""End-to-end validation of the desktop workflow (item 8 of the extended phase).

The real GUI stack is exercised: the main window, its column mapper, the
spreadsheet widget and the recalculation path, with a published benchmark
dataset loaded from a file through the application's own file service.

The workflow runs in a **separate process** (`gui_workflow_driver.py`): a
QApplication must exist before any widget is constructed, and Qt aborts the
interpreter natively when it does not - a failure pytest cannot report. The
driver returns a JSON summary that the test asserts on, so the behaviour is
verified without destabilising the test session.

Two unit paths are exercised, because they are genuinely different and easy to
confuse:

* **display units** (the application default, and what its own export
  produces): conductivity in S/cm and the Seebeck coefficient in uV/K. This is
  the user workflow: file -> mapper -> spreadsheet -> recalculation.
* **base units** through the ``is_base_units=True`` flag: conductivity in S/m
  and the Seebeck coefficient in V/K.

Both must yield the same physics. Feeding base-unit values through the
display-unit path silently scales the conductivity by 100 and the Seebeck
coefficient by 1e-6 - a trap this test makes explicit.

The module is skipped when the Qt widget library cannot be loaded (for
example on a machine whose PyQt6 runtime is broken).
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE / "raw"
DRIVER = HERE / "gui_workflow_driver.py"

try:
    import PyQt6.QtWidgets  # noqa: F401
except ImportError as exc:  # pragma: no cover - environment dependent
    pytest.skip(
        f"the PyQt6 widget library is not available in this environment: {exc}",
        allow_module_level=True,
    )


@pytest.fixture(scope="module")
def workflow(tmp_path_factory):
    """Run the GUI workflow in a separate process and return its summary."""
    output = tmp_path_factory.mktemp("gui") / "summary.json"
    environment = dict(os.environ)
    environment.setdefault("QT_QPA_PLATFORM", "offscreen")

    result = subprocess.run(
        [sys.executable, str(DRIVER), str(RAW), str(output)],
        capture_output=True,
        text=True,
        timeout=300,
        env=environment,
        cwd=str(HERE.parents[1]),
    )
    if result.returncode != 0:
        pytest.fail(
            "the GUI workflow driver failed "
            f"(exit {result.returncode}):\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
        )
    return json.loads(output.read_text(encoding="utf-8"))


def test_gui_workflow_reproduces_the_published_physics(workflow):
    """File -> mapper -> spreadsheet -> recalculation must reproduce the physics."""
    display = workflow["display_path"]

    assert workflow["rows"] == len(display["zt"])
    assert {"Power Factor", "Electronic TC", "Lattice TC", "ZT"} <= set(display["columns"])

    expected_pf = workflow["expected_power_factor"]
    expected_zt = workflow["expected_zt"]
    for computed, expected in zip(display["power_factor"], expected_pf):
        assert computed == pytest.approx(expected, rel=1e-9)
    for computed, expected in zip(display["zt"], expected_zt):
        assert computed == pytest.approx(expected, rel=1e-9)


def test_gui_display_and_base_unit_paths_agree(workflow):
    """The is_base_units flag must reproduce the display-unit result."""
    display = workflow["display_path"]
    base = workflow["base_path"]

    assert base["power_factor"] == pytest.approx(
        display["power_factor"], rel=1e-9
    )
    assert base["zt"] == pytest.approx(display["zt"], rel=1e-9)


def test_gui_spreadsheet_displays_the_recalculated_values(workflow):
    """The rendered table must show the recalculated power factor and ZT.

    The table renders in the *display* units (the power factor is shown in
    mW/(m*K^2) by default) while the model holds base units, so the
    comparison uses the application's own conversion path.
    """
    display = workflow["display_path"]
    displayed = workflow["displayed"]

    assert displayed["power_factor"] == pytest.approx(
        displayed["expected_power_factor"], rel=1e-3
    )
    assert displayed["zt"] == pytest.approx(displayed["expected_zt"], rel=1e-3)
    # the base-unit model value and the rendered value differ by the display
    # conversion (1000 for mW/(m*K^2)) - the table must not show base units
    assert displayed["power_factor"] == pytest.approx(
        display["power_factor"][0] * 1000.0, rel=1e-3
    )
    # the table renders with five significant digits, so the agreement with
    # the model cannot be tighter than that formatting precision
    assert displayed["pf_display_unit"] == "mW/mK\u00b2"


def test_gui_error_bar_mode_extends_the_column_contract(workflow):
    """The error-bar mode must extend the table with +/- columns.

    The workflow itself is *interactive* - enabling error bars opens the modal
    ErrorBarDialog - so the headless validation covers the column contract it
    applies rather than the dialog interaction.
    """
    headers = workflow["error_mode_headers"]

    assert any("\u00b1" in header for header in headers)
    assert len(headers) > len(workflow["displayed"]["headers"])
    assert workflow["error_mode_interactive"] is True
