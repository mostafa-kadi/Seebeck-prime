"""Unit tests for pure measurement-table processing workflows."""

import numpy as np
import pandas as pd
import pytest

from seebeck_prime.application.measurement_processing import (
    combine_seebeck_uncertainty,
    combine_sigma_uncertainty,
    find_column,
    process_four_probe_table,
    process_laser_flash_table,
    process_raw_seebeck_table,
)


def test_find_column_matches_longest_alias():
    df = pd.DataFrame(columns=["Temperature (K)", "Seebeck (uV/K)", "Sigma (S/cm)"])
    assert find_column(df, ["seebeck", "alpha"]) == "Seebeck (uV/K)"
    assert find_column(df, ["unknown"]) is None


def test_process_four_probe_table_converts_and_groups():
    raw = pd.DataFrame(
        {
            "Temperature (K)": [300.0, 300.0, 350.0],
            "Conductivity (S/cm)": [100.0, 100.0, 90.0],
            "Seebeck (uV/K)": [100.0, 100.0, 120.0],
        }
    )
    result = process_four_probe_table(raw)

    assert list(result.columns) == ["T_K", "sigma", "±σ", "S", "±S"]
    assert list(result["T_K"]) == [300.0, 350.0]
    assert result.loc[result["T_K"] == 300.0, "sigma"].iloc[0] == pytest.approx(10000.0)
    assert result.loc[result["T_K"] == 300.0, "S"].iloc[0] == pytest.approx(100e-6)
    assert result.loc[result["T_K"] == 300.0, "±σ"].iloc[0] == pytest.approx(0.0)
    assert result.loc[result["T_K"] == 350.0, "sigma"].iloc[0] == pytest.approx(9000.0)


def test_process_four_probe_table_honours_the_declared_kelvin_header():
    # The header declares Kelvin, so the values are taken as Kelvin - even
    # for a cryogenic mean below the legacy 250 K inference threshold.
    raw = pd.DataFrame(
        {
            "Temperature (K)": [25.0, 25.0],
            "Conductivity (S/cm)": [100.0, 100.0],
            "Seebeck (uV/K)": [100.0, 100.0],
        }
    )
    result = process_four_probe_table(raw)
    assert list(result["T_K"]) == [25.0]


def test_process_four_probe_table_converts_a_declared_celsius_header():
    raw = pd.DataFrame(
        {
            "Temperature (degC)": [25.0, 25.0],
            "Conductivity (S/cm)": [100.0, 100.0],
            "Seebeck (uV/K)": [100.0, 100.0],
        }
    )
    result = process_four_probe_table(raw)
    assert list(result["T_K"]) == [298.15]


def test_process_four_probe_table_none_input():
    assert process_four_probe_table(None) is None


def test_process_laser_flash_table_groups_by_temperature_in_kelvin():
    # The header declares Kelvin: the values are used as they are, which
    # matches the Kappa dialog's laser-flash import path (SE-026).
    raw = pd.DataFrame(
        {
            "Temperature (K)": [300.0, 300.0, 350.0],
            "Thermal Conductivity (W/mK)": [2.0, 2.0, 1.5],
        }
    )
    result = process_laser_flash_table(raw)

    assert list(result.columns) == ["T_K", "kappa", "±κ"]
    assert list(result["T_K"]) == [300.0, 350.0]
    assert result["kappa"].tolist() == pytest.approx([2.0, 1.5])
    assert result["±κ"].tolist() == pytest.approx([0.0, 0.0])


def test_process_laser_flash_table_requires_temperature_and_kappa():
    raw = pd.DataFrame({"Diffusivity": [1.0, 2.0]})
    assert process_laser_flash_table(raw) is None
    assert process_laser_flash_table(None) is None


def test_process_raw_seebeck_table_regression_slope():
    raw = pd.DataFrame(
        {
            "T (K)": [300, 300, 300],
            "Delta T (K)": [1.0, 2.0, 3.0],
            "Delta V (mV)": [0.1, 0.2, 0.3],
        }
    )
    result = process_raw_seebeck_table(raw)

    assert list(result["T_K"]) == [300.0]
    assert result["S_uVK"].iloc[0] == pytest.approx(100.0)
    assert result["S"].iloc[0] == pytest.approx(100e-6)
    assert result["±S"].iloc[0] == pytest.approx(0.0)


def test_process_raw_seebeck_table_none_input():
    assert process_raw_seebeck_table(None) is None


def test_combine_sigma_uncertainty_without_geometry_returns_statistical_error():
    sigma = np.array([1e5, 1e5])
    stat = np.array([100.0, 200.0])
    result = combine_sigma_uncertainty(sigma, stat, None, None, None, None, None, None)
    np.testing.assert_allclose(result, stat)


def test_combine_sigma_uncertainty_combines_geometric_relative_errors():
    sigma = np.array([1e5])
    stat = np.array([100.0])
    result = combine_sigma_uncertainty(
        sigma,
        stat,
        width=0.004,
        width_err=0.00004,
        thickness=0.001,
        thickness_err=0.00001,
        probe_length=0.008,
        probe_length_err=0.00008,
    )
    expected = 1e5 * np.sqrt(0.001 ** 2 + 3 * 0.01 ** 2)
    assert result[0] == pytest.approx(expected)


def test_combine_seebeck_uncertainty_adds_reference_error_in_quadrature():
    stat = np.array([2e-6])
    result = combine_seebeck_uncertainty(stat, 1.0)
    assert result[0] == pytest.approx(np.sqrt(4e-12 + 1e-12))


def test_services_facade_delegates_to_pure_functions():
    from seebeck_prime.application.services import ThermoelectricAnalyzer
    from seebeck_prime.application import measurement_processing

    raw = pd.DataFrame(
        {
            "Temperature (K)": [300.0],
            "Thermal Conductivity (W/mK)": [2.0],
        }
    )

    class SingleStore:
        def __init__(self, data):
            self.data = data

        def read(self, path):
            return self.data

    analyzer = ThermoelectricAnalyzer(lf_file="unused.csv", data_store=SingleStore(raw))
    assert analyzer.lf_raw is raw
    np.testing.assert_allclose(
        analyzer.process_laser_flash()["kappa"].values,
        process_laser_flash_table(raw)["kappa"].values,
    )
