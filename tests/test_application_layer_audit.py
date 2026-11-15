"""Regression tests for the application-layer defects found by the audit.

Covers the issues that were silently corrupting results:
- SE-029 the Seebeck uncertainty was dropped by the four-probe/raw-Seebeck merge
- SE-030 u(kappa_e) diverged between the two application entry points
- SE-031 the electrical-conductivity alias captured thermal conductivity
- SE-032 the "k" alias captured a temperature column
- SE-033 group means were reported with the sample spread instead of the
  standard error of the mean
- SE-035 u(kappa) was dropped unless both u(sigma) and u(S) were supplied
- SE-036 the Lorenz uncertainty was not propagated in the S-derived mode
- SE-037 the reporting statement did not describe the implemented method
- SE-038 the negative-kappa_L diagnostic was unreachable
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from seebeck_prime.application.data_mapping import (
    find_column_index,
    get_robust_mapped_dataframe,
)
from seebeck_prime.application.measurement_processing import (
    find_column,
    process_four_probe_table,
    process_laser_flash_table,
)
from seebeck_prime.application.services import ThermoelectricAnalyzer
from seebeck_prime.application.use_cases import (
    calculate_thermoelectric_properties,
    validate_measurement_data,
)
from seebeck_prime.domain.uncertainty import propagate_kappa_e_error


# ── SE-031 / SE-032: column alias matching ─────────────────────────────────

def test_electrical_conductivity_alias_does_not_capture_thermal_conductivity():
    search_groups = [
        ("Temperature", ["temperature", "temp", "t"]),
        ("Sigma", ["sigma", "conductivity", "electrical", "ec"]),
        ("Kappa_total", ["kappa", "thermal", "k", "kappa_total"]),
    ]
    frame = pd.DataFrame(
        {
            "Temperature (K)": [300.0],
            "Sigma (S/cm)": [1000.0],
            "Thermal Conductivity (W/mK)": [2.0],
        }
    )

    mapped = get_robust_mapped_dataframe(frame, search_groups)

    assert mapped["Sigma"].tolist() == [1000.0]      # not the kappa value
    assert mapped["Kappa_total"].tolist() == [2.0]   # now mapped


def test_short_k_alias_does_not_capture_a_temperature_column():
    hit = find_column(
        pd.DataFrame(columns=["T (K)", "Cp (J/gK)"]),
        ["thermal conductivity", "thermal cond", "kappa", "\u03ba", "k"],
    )

    assert hit != "T (K)"


def test_alias_matching_is_case_insensitive():
    hit = find_column(pd.DataFrame(columns=["Seebeck (uV/K)"]), ["uV/K", "\u00b5V/K"])

    assert hit == "Seebeck (uV/K)"


def test_shared_matcher_is_used_by_both_import_paths():
    assert find_column_index(
        ["Thermal Conductivity (W/mK)"], ["conductivity"]
    ) is None


# ── SE-033: standard error of the mean ────────────────────────────────────

def test_group_uncertainty_is_the_standard_error_of_the_mean():
    raw = pd.DataFrame(
        {
            "Temperature (K)": [300.0, 300.0, 300.0, 300.0, 300.0],
            "Conductivity (S/cm)": [1000.0, 1002.0, 998.0, 1001.0, 999.0],
            "Seebeck (uV/K)": [150.0, 150.0, 150.0, 150.0, 150.0],
        }
    )

    result = process_four_probe_table(raw)

    # The values are converted from S/cm to S/m (x100) before the statistics,
    # so the reported uncertainty is the SEM of the converted values.
    values = np.array([1000.0, 1002.0, 998.0, 1001.0, 999.0]) * 100.0
    expected_sem = values.std(ddof=1) / np.sqrt(values.size)
    assert result["\u00b1\u03c3"].iloc[0] == pytest.approx(expected_sem, rel=1e-12)
    assert result["\u00b1\u03c3"].iloc[0] < values.std(ddof=1)


def test_laser_flash_group_uncertainty_is_the_standard_error_of_the_mean():
    raw = pd.DataFrame(
        {
            "Temperature (K)": [300.0, 300.0, 300.0, 300.0],
            "Thermal Conductivity (W/mK)": [2.0, 2.1, 1.9, 2.0],
        }
    )

    result = process_laser_flash_table(raw)

    values = np.array([2.0, 2.1, 1.9, 2.0])
    expected_sem = values.std(ddof=1) / np.sqrt(values.size)
    assert result["\u00b1\u03ba"].iloc[0] == pytest.approx(expected_sem, rel=1e-12)


# ── SE-029: the Seebeck uncertainty must survive the merge ─────────────────

def test_raw_seebeck_uncertainty_survives_the_four_probe_merge():
    analyzer = ThermoelectricAnalyzer()
    fp = pd.DataFrame(
        {
            "T_K": [300.0, 350.0],
            "sigma": [1e5, 9e4],
            "S": [100e-6, 110e-6],
            "\u00b1\u03c3": [1e3, 1e3],
            "\u00b1S": [5e-6, 5e-6],
        }
    )
    seebeck_raw = pd.DataFrame(
        {
            "T_K": [300.0, 350.0],
            "S": [100e-6, 110e-6],
            "\u00b1S": [8.485e-6, 8.485e-6],
        }
    )

    result = analyzer.calculate_transport(
        fp_df=fp, lf_df=None, seebeck_raw_df=seebeck_raw
    )

    assert "\u00b1S" in result.columns
    assert "\u00b1S_x" not in result.columns
    assert "\u00b1S_y" not in result.columns
    # The regression uncertainty must not be silently discarded.
    assert result["\u00b1S"].iloc[0] == pytest.approx(8.485e-6, rel=1e-9)


# ── SE-030: one implementation of u(kappa_e) ────────────────────────────────

def test_file_and_manual_workflows_agree_on_kappa_e_uncertainty():
    sigma = np.array([1e5, 9e4])
    u_sigma = np.array([1e3, 900.0])
    T = np.array([300.0, 350.0])
    u_T = np.array([0.5, 0.5])
    L = 2.44e-8

    analyzer = ThermoelectricAnalyzer()
    fp = pd.DataFrame(
        {
            "T_K": T,
            "sigma": sigma,
            "S": np.array([100e-6, 110e-6]),
            "\u00b1\u03c3": u_sigma,
            "\u00b1S": np.array([5e-6, 5e-6]),
        }
    )
    result = analyzer.calculate_transport(fp_df=fp, lf_df=None, seebeck_raw_df=None)

    expected = propagate_kappa_e_error(
        sigma, u_sigma, T, np.zeros(len(T)), L, np.zeros(len(T))
    )
    assert result["\u00b1\u03ba\u2091"].tolist() == pytest.approx(expected.tolist(), rel=1e-9)


# ── SE-035 / SE-036: uncertainty inputs are used as supplied ───────────────

def test_kappa_uncertainty_is_used_even_without_sigma_and_seebeck_errors():
    T = np.array([300.0])
    sigma = np.array([1e5])
    S = np.array([100e-6])
    kappa = np.array([2.0])

    result = calculate_thermoelectric_properties(
        T, sigma, S, kappa, u_kappa=np.array([0.02])
    )

    assert result["u_kappa"].tolist() == pytest.approx([0.02])


def test_auto_lorenz_mode_propagates_the_seebeck_uncertainty_into_kappa_e():
    T = np.array([300.0])
    sigma = np.array([1e5])
    S = np.array([100e-6])
    u_S = np.array([5e-6])

    auto = calculate_thermoelectric_properties(
        T, sigma, S, None, lorenz="auto", u_sigma=np.array([1e3]), u_S=u_S
    )
    fixed = calculate_thermoelectric_properties(
        T, sigma, S, None, lorenz=2.44e-8, u_sigma=np.array([1e3]), u_S=u_S
    )

    # The S-derived Lorenz number carries an extra uncertainty contribution.
    assert auto["u_kappa_e"][0] > fixed["u_kappa_e"][0]


# ── SE-037 / SE-038 ────────────────────────────────────────────────────────

def test_reporting_statement_describes_the_implemented_method():
    statement = ThermoelectricAnalyzer.get_reporting_statement()

    assert "standard error" in statement.lower()
    assert "ΔV versus ΔT" in statement


def test_validation_reaches_the_negative_lattice_conductivity_diagnostic():
    messages = validate_measurement_data(
        T=np.array([300.0]),
        sigma=np.array([1e5]),
        S=np.array([100e-6]),
        kappa=np.array([2.0]),
        kappa_L=np.array([-0.5]),
    )

    assert any(m.field == "kappa_L" for m in messages)
