"""Verify the shipped example workflow (synthetic dataset + headless script)."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / "examples" / "headless_analysis.py"


def _load_example():
    spec = importlib.util.spec_from_file_location("headless_analysis", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["headless_analysis"] = module
    spec.loader.exec_module(module)
    return module


def test_example_dataset_is_present_and_well_formed():
    dataset = REPO_ROOT / "examples" / "example_dataset.csv"
    with open(dataset, newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == [
        "Temperature (K)",
        "Seebeck (V/K)",
        "Electrical Conductivity (S/m)",
        "Thermal Conductivity (W/(m*K))",
    ]
    assert len(rows) == 12  # header + 11 temperature points
    assert float(rows[1][0]) == 300.0
    assert float(rows[-1][0]) == 500.0


def test_example_computes_domain_properties_consistently():
    example = _load_example()
    data = example.read_dataset()
    results = example.compute_properties(data)

    temperature = data["Temperature (K)"]
    seebeck = data["Seebeck (V/K)"]
    conductivity = data["Electrical Conductivity (S/m)"]
    kappa = data["Thermal Conductivity (W/(m*K))"]

    for index in (0, 5, 10):
        expected_zt = (seebeck[index] ** 2) * conductivity[index] * temperature[index] / kappa[index]
        assert results["ZT"][index] == pytest.approx(expected_zt, rel=1e-12)
        assert results["PF (W/(m*K^2))"][index] == pytest.approx(
            seebeck[index] ** 2 * conductivity[index], rel=1e-12
        )
        assert (
            results["kappa_e (W/(m*K))"][index]
            + results["kappa_l (W/(m*K))"][index]
            == pytest.approx(kappa[index], rel=1e-12)
        )


def test_example_main_writes_results_csv(tmp_path, capsys):
    example = _load_example()
    output = tmp_path / "out" / "results.csv"

    exit_code = example.main([str(output)])

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "ZT" in captured

    with open(output, newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0][-1] == "ZT"
    assert len(rows) == 12

    data = example.read_dataset()
    expected = (data["Seebeck (V/K)"][0] ** 2) * data["Electrical Conductivity (S/m)"][0]
    assert float(rows[1][-1]) == pytest.approx(
        expected * 300.0 / data["Thermal Conductivity (W/(m*K))"][0], rel=1e-12
    )
