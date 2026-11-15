"""Regression tests for the three author decisions taken after the audit.

1. SE-015 - one application-wide Lorenz number (2.44e-8 W*Ohm/K^2).
2. SE-026 / SE-027 - raw temperature columns are converted using the unit
   declared by the file header; the laser-flash path matches the Kappa
   dialog's import path.
3. SE-016 - the Multi-Sample tool reports S/cm, uV/K and mW/(m*K^2) on both
   of its plotting paths.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
import pytest

from seebeck_prime.application.measurement_processing import (
    process_four_probe_table,
    process_laser_flash_table,
)
from seebeck_prime.domain.physical_constants import (
    DEFAULT_LORENZ,
    LEGACY_DEFAULT_LORENZ,
    SOMMERFELD_LORENZ_EXACT,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


# ── 1. one Lorenz number ────────────────────────────────────────────────────

def test_all_workflows_share_the_same_lorenz_constant():
    assert DEFAULT_LORENZ == LEGACY_DEFAULT_LORENZ == 2.44e-8
    # The exact Sommerfeld value remains available for reference.
    assert SOMMERFELD_LORENZ_EXACT == pytest.approx(2.443004509e-8, rel=1e-9)


def test_multi_sample_and_main_table_agree_on_kappa_e():
    """The same material data must give the same kappa_e in both workflows."""
    from seebeck_prime.application.use_cases import process_multi_sample_data
    from seebeck_prime.domain.calculations import calculate_kappa_e

    frame = pd.DataFrame(
        {
            "Temperature": [300.0, 400.0],
            "Seebeck": [100e-6, -200e-6],
            "Sigma": [1e5, 8e4],
            "Kappa_total": [2.0, 1.5],
        }
    )
    processed = process_multi_sample_data(frame)
    main_table_kappa_e = calculate_kappa_e(1e5, 300.0)

    assert processed["Electronic TC"].iloc[0] == pytest.approx(
        main_table_kappa_e, rel=1e-12
    )


# ── 2. temperature unit handling ────────────────────────────────────────────

def test_declared_kelvin_header_is_not_offset():
    raw = pd.DataFrame(
        {
            "Temperature (K)": [300.0, 300.0, 350.0],
            "Thermal Conductivity (W/mK)": [2.0, 2.0, 1.5],
        }
    )
    result = process_laser_flash_table(raw)

    assert list(result["T_K"]) == [300.0, 350.0]


def test_declared_celsius_header_is_converted():
    raw = pd.DataFrame(
        {
            "Temperature (degC)": [300.0, 300.0, 350.0],
            "Thermal Conductivity (W/mK)": [2.0, 2.0, 1.5],
        }
    )
    result = process_laser_flash_table(raw)

    assert list(result["T_K"]) == [573.15, 623.15]


def test_laser_flash_and_kappa_dialog_use_the_same_temperature_convention():
    """The application path and the Kappa dialog path must not disagree by
    273.15 K for the same file (audit issue SE-026)."""
    kappa_logic = (REPO_ROOT / "src" / "presentation" / "kappa_logic.py").read_text(
        encoding="utf-8"
    )
    measurement = (
        REPO_ROOT / "src" / "application" / "measurement_processing.py"
    ).read_text(encoding="utf-8")

    # Neither path may apply a hard-coded Celsius offset any more.
    assert "+ 273.15" not in kappa_logic
    assert "df[\"T_K\"] = df[normalized_cols[\"T_K\"]] + 273.15" not in measurement
    assert "_to_kelvin(" in measurement


def test_four_probe_cryogenic_kelvin_data_is_not_shifted():
    """A Kelvin-labelled file with a mean below 250 K must not be offset."""
    raw = pd.DataFrame(
        {
            "Temperature (K)": [20.0, 20.0, 40.0],
            "Conductivity (S/cm)": [100.0, 100.0, 90.0],
            "Seebeck (uV/K)": [100.0, 100.0, 110.0],
        }
    )
    result = process_four_probe_table(raw)

    assert sorted(set(result["T_K"])) == [20.0, 40.0]


# ── 3. Multi-Sample units ───────────────────────────────────────────────────

def _property_list(source: str, attribute: str):
    """Extract the (column, label) pairs of a property list from source."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                name = None
                if isinstance(target, ast.Name):
                    name = target.id
                elif isinstance(target, ast.Attribute):
                    name = target.attr
                if name == attribute and isinstance(node.value, ast.List):
                    return [
                        (elt.elts[0].value, elt.elts[1].value)
                        for elt in node.value.elts
                        if isinstance(elt, ast.Tuple)
                    ]
    return []


def test_multi_sample_paths_use_identical_columns_and_units():
    default_properties = _property_list(
        (REPO_ROOT / "src" / "presentation" / "multi_sample_plots.py").read_text(
            encoding="utf-8"
        ),
        "properties",
    )
    settings_properties = _property_list(
        (
            REPO_ROOT / "src" / "presentation" / "dialogs" / "plot_settings_dialog.py"
        ).read_text(encoding="utf-8"),
        "properties",
    )

    assert default_properties, "default Multi-Sample property list not found"
    assert settings_properties, "Multi-Sample settings property list not found"
    assert settings_properties == default_properties
    # Conductivity is reported in S/cm on both paths.
    assert ("Sigma_Scm", "Electrical Conductivity (S/cm)") in default_properties
    assert ("S_uVK", "Seebeck Coefficient (\u03bcV/K)") in default_properties
    assert ("PF_mW", "Power Factor (mW/mK\u00b2)") in default_properties
