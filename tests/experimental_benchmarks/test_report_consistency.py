"""Consistency and classification guards for the experimental validation reports.

These tests make the *claims of the reports* checkable against the
repository:

* the benchmark registry, the on-disk datasets and the validation reports
  agree (no dataset is claimed that is not present, none is present that is
  not documented);
* the distinction between an **experimental benchmark comparison** and an
  **arithmetic consistency check** is enforced by the data, not by prose;
* the carrier-concentration units of the published data are confirmed by an
  independent relation (mu = sigma/(n e)) rather than assumed;
* the Lorenz number implied by the published data is compared with the
  rigorous SPB model, which is the only way to decide whether the published
  measurements support the Seebeck-derived ("auto") estimate.
"""

from __future__ import annotations

import json
import math
import pathlib

import numpy as np
import pandas as pd
import pytest

from registry import COMPARISON_KINDS, REGISTRY

from seebeck_prime.domain.physical_constants import (
    BOLTZMANN, DEFAULT_LORENZ, ELECTRON_CHARGE, SOMMERFELD_LORENZ_EXACT,
)
from seebeck_prime.domain.spb import (
    reduced_fermi_level_from_seebeck,
    rigorous_lorenz_number,
)

HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE / "raw"
PROCESSED = HERE / "processed"
REPORTS = [
    HERE.parents[1] / "docs" / "EXPERIMENTAL_BENCHMARK_VALIDATION.md",
    HERE.parents[1] / "docs" / "EXTENDED_VALIDATION_REPORT.md",
]


def _curves(benchmark: str) -> dict:
    frame = pd.read_csv(RAW / f"{benchmark}_curves.csv")
    curves = {}
    for row in frame.itertuples(index=False):
        xs = np.array([v for v in json.loads(row.x) if v is not None], dtype=float)
        ys = np.array([v for v in json.loads(row.y) if v is not None], dtype=float)
        n = min(len(xs), len(ys))
        order = np.argsort(xs[:n])
        curves[row.prop_y] = (xs[:n][order], ys[:n][order], row.unit_y)
    return curves


# =============================================================================
# Registry / repository / report consistency
# =============================================================================

def test_every_registered_benchmark_has_its_dataset_on_disk():
    for name in REGISTRY:
        assert (RAW / f"{name}_curves.csv").is_file(), f"missing raw data: {name}"
        assert (PROCESSED / f"{name}.csv").is_file(), f"missing processed data: {name}"


def test_no_dataset_on_disk_is_missing_from_the_registry():
    on_disk = {path.name.replace("_curves.csv", "")
               for path in RAW.glob("*_curves.csv")}
    assert on_disk == set(REGISTRY), (
        f"datasets on disk {sorted(on_disk)} do not match the registry "
        f"{sorted(REGISTRY)}"
    )


def test_both_validation_reports_exist_and_mention_every_benchmark():
    for report in REPORTS:
        assert report.is_file(), f"missing report: {report.name}"
        text = report.read_text(encoding="utf-8")
        for name, spec in REGISTRY.items():
            assert name in text, f"{report.name} does not mention {name}"
            assert spec["doi"] in text, f"{report.name} does not cite {spec['doi']}"


def test_reports_state_the_actual_test_counts():
    """The counts quoted in the reports must match the measured ones.

    The subprocess cannot include this module (it would spawn itself), and it
    also excludes the GUI end-to-end module, whose availability depends on
    whether the local Qt installation can be loaded. The remaining benchmark
    suite is environment-independent, so the reported counts are valid both
    in the primary environment (where the GUI module cannot be imported) and
    in a Qt-capable environment (where its four tests pass).
    """
    import ast
    import subprocess
    import sys

    this_file = pathlib.Path(__file__).resolve()
    gui_module = HERE / "test_gui_end_to_end.py"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(HERE), "-q",
         "-p", "no:cacheprovider",
         "--ignore", str(this_file),
         "--ignore", str(gui_module)],
        capture_output=True, text=True, cwd=str(HERE.parents[1]),
    )
    line = [ln for ln in result.stdout.splitlines() if "passed" in ln]
    assert line, result.stdout[-2000:]
    summary = line[-1]
    numbers = [int(part.split()[0]) for part in summary.split(",")
               if part.strip().split()[0].isdigit()]
    passed = numbers[0]
    skipped = numbers[1] if len(numbers) > 1 else 0

    # The tests of this module are excluded from the subprocess but they do
    # run in the full suite, so they are added back in full.
    tree = ast.parse(this_file.read_text(encoding="utf-8"))
    module_tests = sum(
        1 for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    )
    passed += module_tests

    for report in REPORTS:
        text = report.read_text(encoding="utf-8")
        assert f"{passed} passed" in text, (
            f"{report.name} does not state the measured count '{passed} passed'"
        )
        assert f"{skipped} skipped" in text, (
            f"{report.name} does not state the measured count '{skipped} skipped'"
        )


# =============================================================================
# Classification guards
# =============================================================================

def test_lattice_conductivity_comparisons_are_classified_correctly():
    """The lattice-kappa comparison is a consistency check whenever the
    Lorenz number is derived from the published kappa_L; for the SiGe sample
    the application uses its own a-priori constant, so that comparison is a
    genuine experimental one."""
    for name, spec in REGISTRY.items():
        for grid, kind in spec["comparisons"].items():
            assert kind in COMPARISON_KINDS, f"{name}: unknown comparison kind {kind!r}"
            assert grid in spec["grids"], (
                f"{name}: the '{grid}' comparison refers to a grid that the "
                "dataset does not publish"
            )
        # The classification must follow the outcome of the validation audit.
        kind = spec["comparisons"].get("kappa_l")
        if name == "sige_si80ge20p1":
            assert kind == "experimental"
        elif "kappa_l" in spec["grids"]:
            assert kind == "consistency", (
                f"{name}: the lattice-kappa comparison derives the Lorenz "
                "number from the published kappa_L and must be classified as "
                "an arithmetic consistency check"
            )


def test_instrument_reconstructions_derive_from_published_data():
    """The instrument files must contain the published values, not new data."""
    curves = _curves("b2te3_bi2te2_4se0_6cu0_006")
    temperature, seebeck = curves["Seebeck coefficient"][0], curves["Seebeck coefficient"][1]
    _, sigma = curves["Electrical conductivity"][0], curves["Electrical conductivity"][1]

    four_probe = pd.read_csv(HERE / "raw" / "instrument" / "four_probe_instrument.csv")
    assert four_probe["Temperature (K)"].tolist() == pytest.approx(
        temperature.tolist(), rel=1e-12
    )
    assert four_probe["Seebeck (uV/K)"].tolist() == pytest.approx(
        (seebeck * 1e6).tolist(), rel=1e-12
    )
    assert four_probe["Conductivity (S/cm)"].tolist() == pytest.approx(
        (
            np.interp(
                temperature,
                curves["Electrical conductivity"][0],
                curves["Electrical conductivity"][1],
            )
            / 100.0
        ).tolist(),
        rel=1e-12,
    )


# =============================================================================
# Experimental checks on the carrier data
# =============================================================================

def test_published_carrier_concentration_units_are_confirmed_by_the_published_mobility():
    """mu = sigma/(n e) is an independent relation: it confirms that the
    published carrier concentration (m^-3) and conductivity (S/m) are mutually
    consistent, i.e. that the unit interpretation is correct."""
    curves = _curves("sige_si80ge20p1")
    t_n, n_m3, n_unit = curves["Carrier concentration"]
    t_mu, mu_pub, mu_unit = curves["Carrier mobility"]
    t_s, sigma, _ = curves["Electrical conductivity"]

    assert n_unit == "m^(-3)"
    assert mu_unit == "m^2*V^(-1)*s^(-1)"

    mu_from_n = np.interp(t_n, t_s, sigma) / (n_m3 * ELECTRON_CHARGE)
    ratio = np.interp(t_n, t_mu, mu_pub) / mu_from_n

    # A unit error would show up as a factor of 1e6 or 1e-6 here.
    assert 0.85 < np.median(ratio) < 1.15, (
        f"the published sigma, n and mu are not mutually consistent "
        f"(median ratio {np.median(ratio):.3f}); the carrier-concentration "
        "unit interpretation would be wrong"
    )


def test_published_lorenz_number_matches_the_sommerfeld_value_not_the_spb_model():
    """The decisive check for the Seebeck-derived ("auto") Lorenz mode.

    The published thermal conductivity, lattice thermal conductivity and
    conductivity imply a Lorenz number. For this sample that number is the
    Sommerfeld value, and it is ~35 % away from the rigorous single-parabolic-
    band value for acoustic-phonon scattering. The published measurements
    therefore do **not** support the SPB acoustic model, and consequently they
    do not validate the "auto" estimate; the application's default constant
    (2.44e-8) is the one that agrees with these data.
    """
    curves = _curves("sige_si80ge20p1")
    t_kl, kappa_l, _ = curves["Lattice thermal conductivity"]
    t_k, kappa, _ = curves["Thermal conductivity"]
    t_s, sigma, _ = curves["Electrical conductivity"]
    t_se, seebeck, _ = curves["Seebeck coefficient"]

    kappa_at = np.interp(t_kl, t_k, kappa)
    sigma_at = np.interp(t_kl, t_s, sigma)
    seebeck_at = np.interp(t_kl, t_se, seebeck)

    implied = (kappa_at - kappa_l) / (sigma_at * t_kl)
    implied_lorenz = float(np.median(implied))
    rigorous = float(np.median([
        rigorous_lorenz_number(
            reduced_fermi_level_from_seebeck(abs(s) * 1e6, 0.0), 0.0)
        for s in seebeck_at
    ]))

    print(f"\n[Lorenz] implied by the published data : {implied_lorenz:.4e}")
    print(f"[Lorenz] rigorous SPB L(eta) (lambda=0): {rigorous:.4e}")
    print(f"[Lorenz] Sommerfeld L0                : {SOMMERFELD_LORENZ_EXACT:.4e}")

    # The published data agree with the Sommerfeld value ...
    assert implied_lorenz == pytest.approx(SOMMERFELD_LORENZ_EXACT, rel=0.05)
    # ... and disagree with the SPB acoustic-phonon model.
    assert abs(rigorous / implied_lorenz - 1.0) > 0.25, (
        "the SPB acoustic-phonon value is expected to disagree with the "
        "published SiGe data by more than 25 %; if this changes the "
        "documentation of the auto-Lorenz limitation must be revised"
    )


def test_application_default_lorenz_reproduces_the_published_lattice_conductivity():
    """With its own (a priori) constant the application reproduces the
    published lattice conductivity of this sample - an experimental
    comparison that does not derive anything from the published kappa_L."""
    curves = _curves("sige_si80ge20p1")
    t_kl, kappa_l, _ = curves["Lattice thermal conductivity"]
    t_k, kappa, _ = curves["Thermal conductivity"]
    t_s, sigma, _ = curves["Electrical conductivity"]

    kappa_at = np.interp(t_kl, t_k, kappa)
    sigma_at = np.interp(t_kl, t_s, sigma)

    kappa_e_app = DEFAULT_LORENZ * sigma_at * t_kl
    kappa_l_app = kappa_at - kappa_e_app
    deviation = np.max(np.abs(kappa_l_app / kappa_l - 1.0))

    print(f"\n[kappa_L] application L={DEFAULT_LORENZ:.3e}: max deviation from the "
          f"published lattice conductivity {deviation:.1%}")
    assert deviation <= 0.05, (
        f"with its own Lorenz constant the application must reproduce the "
        f"published lattice conductivity (deviation {deviation:.1%})"
    )
