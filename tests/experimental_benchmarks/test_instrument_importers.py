"""Phase 3 - validation of the instrument importers against published data.

The application consumes three instrument export formats:

* four-probe    -> ``process_four_probe_table``
* raw Seebeck   -> ``process_raw_seebeck_table``
* laser flash   -> ``process_laser_flash_table``

The input files in ``raw/instrument/`` are *reconstructions* of the published
Bi2Te3 curves in those formats (see ``raw/instrument/README.md``). They carry
the published values, so a correct importer must return the published
quantities after its own unit conversions, grouping and statistics.

The expected values are read directly from the published curve rows
(``raw/<benchmark>_curves.csv``), because the reconstructions follow the
temperature grid of the corresponding published curve:

* the four-probe and raw-Seebeck files follow the *Seebeck coefficient* curve,
* the laser-flash file follows the *thermal conductivity* curve.

Scope note: the application reads the electrical conductivity and the
Seebeck coefficient **as computed by the instrument**; the raw V/I -> R ->
rho -> sigma chain is not implemented in the application (only its uncertainty
propagation is). The corresponding validation is therefore limited to the
geometry-uncertainty combination, and this is stated rather than glossed over.
"""

from __future__ import annotations

import json
import math
import pathlib

import numpy as np
import pandas as pd
import pytest

from seebeck_prime.application.measurement_processing import (
    combine_seebeck_uncertainty,
    combine_sigma_uncertainty,
    process_four_probe_table,
    process_laser_flash_table,
    process_raw_seebeck_table,
)
from seebeck_prime.domain.phonon import (
    kappa_from_diffusivity,
    kappa_from_diffusivity_si,
)

HERE = pathlib.Path(__file__).resolve().parent
INSTRUMENT = HERE / "raw" / "instrument"
RAW = HERE / "raw"
BENCH = "b2te3_bi2te2_4se0_6cu0_006"


def _published_curves(benchmark: str = BENCH) -> dict:
    """Decode the published curves of a benchmark (x/y JSON -> arrays)."""
    frame = pd.read_csv(RAW / f"{benchmark}_curves.csv")
    curves = {}
    for row in frame.itertuples(index=False):
        xs = np.array([v for v in json.loads(row.x) if v is not None], dtype=float)
        ys = np.array([v for v in json.loads(row.y) if v is not None], dtype=float)
        n = min(len(xs), len(ys))
        order = np.argsort(xs[:n])
        curves[row.prop_y] = (xs[:n][order], ys[:n][order])
    return curves


# =============================================================================
# A. Four-probe importer
# =============================================================================

def test_four_probe_importer_recovers_the_published_properties():
    """Temperature, conductivity and Seebeck coefficient must round-trip."""
    raw = pd.read_csv(INSTRUMENT / "four_probe_instrument.csv")
    curves = _published_curves()
    temperature, seebeck = curves["Seebeck coefficient"]
    _, sigma = curves["Electrical conductivity"]
    sigma_at_t = np.interp(temperature, *curves["Electrical conductivity"])

    result = process_four_probe_table(raw)

    assert set(result.columns) == {"T_K", "sigma", "\u00b1\u03c3", "S", "\u00b1S"}
    assert len(result) == len(temperature)
    assert result["T_K"].tolist() == pytest.approx(temperature.tolist(), rel=1e-12)
    assert result["sigma"].tolist() == pytest.approx(sigma_at_t.tolist(), rel=1e-9)
    assert result["S"].tolist() == pytest.approx(seebeck.tolist(), rel=1e-9)


def test_four_probe_importer_applies_the_instrument_unit_conversions():
    """S/cm -> S/m (x100) and uV/K -> V/K (x1e-6)."""
    raw = pd.read_csv(INSTRUMENT / "four_probe_instrument.csv")
    result = process_four_probe_table(raw)

    assert result["sigma"].iloc[0] == pytest.approx(
        raw["Conductivity (S/cm)"].iloc[0] * 100.0, rel=1e-12
    )
    assert result["S"].iloc[0] == pytest.approx(
        raw["Seebeck (uV/K)"].iloc[0] * 1e-6, rel=1e-12
    )


def test_four_probe_importer_associates_each_row_with_its_temperature():
    """Every measured row keeps its own temperature (no rounding or shifting)."""
    raw = pd.read_csv(INSTRUMENT / "four_probe_instrument.csv")
    result = process_four_probe_table(raw)

    assert sorted(result["T_K"].tolist()) == pytest.approx(
        sorted(raw["Temperature (K)"].tolist()), rel=1e-12
    )


def test_four_probe_importer_drops_invalid_rows_and_reports_missing_columns():
    """Non-numeric cells are discarded; a file without the required columns
    yields no result at all."""
    raw = pd.read_csv(INSTRUMENT / "four_probe_instrument.csv")
    broken = raw.copy()
    # an invalid (non-numeric) measurement
    broken["Conductivity (S/cm)"] = broken["Conductivity (S/cm)"].astype(object)
    broken.loc[0, "Conductivity (S/cm)"] = "not-a-number"
    # and a missing one
    broken.loc[2, "Seebeck (uV/K)"] = np.nan

    result = process_four_probe_table(broken)
    assert len(result) == len(raw) - 2

    # A file without the expected columns yields no usable result. The
    # importer returns an empty frame (not None) in this case; the caller
    # treats both identically.
    unrelated = process_four_probe_table(pd.DataFrame({"Unrelated": [1.0, 2.0]}))
    assert unrelated is None or len(unrelated) == 0


def test_four_probe_geometry_uncertainty_combination_matches_the_independent_formula():
    """u_sigma/sigma = sqrt((u_stat/sigma)^2 + (u_L/L)^2 + (u_w/w)^2 + (u_t/t)^2)."""
    sigma = np.array([1.0e5, 9.0e4])
    u_stat = np.array([1.0e3, 900.0])
    width, u_width = 2.0e-3, 1.0e-4
    thickness, u_thickness = 1.0e-3, 5.0e-5
    probe_length, u_probe_length = 5.0e-3, 2.0e-4

    combined = combine_sigma_uncertainty(
        sigma, u_stat, width, u_width, thickness, u_thickness,
        probe_length, u_probe_length,
    )

    expected = sigma * np.sqrt(
        (u_stat / sigma) ** 2
        + (u_probe_length / probe_length) ** 2
        + (u_width / width) ** 2
        + (u_thickness / thickness) ** 2
    )
    assert combined == pytest.approx(expected, rel=1e-12)


def test_four_probe_geometry_uncertainty_falls_back_to_the_statistical_error():
    """Without geometry information only the statistical error remains."""
    sigma = np.array([1.0e5])
    u_stat = np.array([1.0e3])
    combined = combine_sigma_uncertainty(sigma, u_stat, None, None, None, None, None, None)
    assert combined == pytest.approx(u_stat, rel=1e-12)


# =============================================================================
# B. Raw Seebeck importer
# =============================================================================

def test_raw_seebeck_importer_recovers_the_published_seebeck_coefficient():
    """The dV/dT regression must reproduce the published Seebeck coefficient."""
    raw = pd.read_csv(INSTRUMENT / "raw_seebeck_instrument.csv")
    temperature, seebeck = _published_curves()["Seebeck coefficient"]

    result = process_raw_seebeck_table(raw)

    assert result is not None
    assert len(result) == len(temperature)
    # The importer groups measurements to 0.1 K, so the returned temperature
    # is the rounded group key.
    assert result["T_K"].tolist() == pytest.approx(
        np.round(temperature, 1).tolist(), rel=1e-12
    )
    assert result["S"].tolist() == pytest.approx(seebeck.tolist(), rel=1e-6)


def test_raw_seebeck_importer_preserves_the_sign_convention():
    """An n-type sample (negative published Seebeck) must stay negative."""
    raw = pd.read_csv(INSTRUMENT / "raw_seebeck_instrument.csv")
    _, seebeck = _published_curves()["Seebeck coefficient"]
    assert (seebeck < 0).all()

    result = process_raw_seebeck_table(raw)

    assert (result["S"] < 0).all(), "the sign of the Seebeck coefficient was lost"


def test_raw_seebeck_importer_handles_the_voltage_unit():
    """dV is exported in mV and must be scaled to uV before the fit."""
    raw = pd.read_csv(INSTRUMENT / "raw_seebeck_instrument.csv")
    _, seebeck = _published_curves()["Seebeck coefficient"]

    result = process_raw_seebeck_table(raw)

    assert result["S_uVK"].tolist() == pytest.approx(
        (seebeck * 1e6).tolist(), rel=1e-9
    )


def test_raw_seebeck_importer_skips_invalid_measurements():
    """Rows without a usable voltage or temperature difference are skipped."""
    raw = pd.read_csv(INSTRUMENT / "raw_seebeck_instrument.csv")
    broken = raw.copy()
    broken.loc[0, "delta_mv"] = np.nan
    broken.loc[1, "delta_k"] = np.nan

    result = process_raw_seebeck_table(broken)

    assert result is not None
    # Two of the three measurements of the first temperature are unusable, so
    # that temperature group is dropped entirely.
    assert len(result) == len(raw) // 3 - 1


def test_raw_seebeck_importer_requires_at_least_two_points_per_temperature():
    """A single pair per temperature carries no slope information."""
    raw = pd.read_csv(INSTRUMENT / "raw_seebeck_instrument.csv")
    one_per_group = raw.groupby("Temperature (K)", as_index=False).head(1)

    result = process_raw_seebeck_table(one_per_group)

    assert result is None or len(result) == 0


def test_seebeck_reference_uncertainty_is_combined_in_quadrature():
    """u_S = sqrt(u_stat^2 + u_ref^2), with u_ref entered in uV/K."""
    u_stat = np.array([8.485e-6])
    u_ref_uv_k = 1.0

    combined = combine_seebeck_uncertainty(u_stat, u_ref_uv_k)

    assert combined[0] == pytest.approx(
        math.sqrt(8.485e-6**2 + 1.0e-6**2), rel=1e-12
    )


# =============================================================================
# C. Laser-flash importer
# =============================================================================

def test_laser_flash_importer_recovers_the_published_thermal_conductivity():
    """Temperature and kappa must be recovered from the instrument file."""
    raw = pd.read_csv(INSTRUMENT / "laser_flash_instrument.csv")
    temperature, kappa = _published_curves()["Thermal conductivity"]

    result = process_laser_flash_table(raw)

    assert result is not None
    assert set(result.columns) >= {"T_K", "kappa", "\u00b1\u03ba"}
    assert len(result) == len(temperature)
    assert result["T_K"].tolist() == pytest.approx(temperature.tolist(), rel=1e-12)
    assert result["kappa"].tolist() == pytest.approx(kappa.tolist(), rel=1e-9)


def test_laser_flash_importer_carries_the_diffusivity_and_heat_capacity():
    """alpha and Cp are optional but must be carried through when present."""
    raw = pd.read_csv(INSTRUMENT / "laser_flash_instrument.csv")
    result = process_laser_flash_table(raw)

    assert "diffusivity" in result.columns
    assert "Cp" in result.columns
    assert result["diffusivity"].iloc[0] == pytest.approx(
        raw["Diffusivity (mm2/s)"].iloc[0], rel=1e-9
    )


def test_laser_flash_thermal_conductivity_uses_consistent_unit_conversions():
    """kappa = alpha * Cp * rho must be identical in laboratory and SI units."""
    alpha_mm2s = 0.85
    cp_j_g_k = 0.20
    density_g_cm3 = 5.6

    laboratory = kappa_from_diffusivity(alpha_mm2s, cp_j_g_k, density_g_cm3)
    si = kappa_from_diffusivity_si(
        alpha_mm2s * 1e-6, cp_j_g_k * 1000.0, density_g_cm3 * 1000.0
    )

    assert laboratory == pytest.approx(si, rel=1e-12)
    assert laboratory == pytest.approx(
        alpha_mm2s * 1e-6 * cp_j_g_k * 1000.0 * density_g_cm3 * 1000.0, rel=1e-12
    )


def test_laser_flash_importer_requires_temperature_and_thermal_conductivity():
    raw = pd.read_csv(INSTRUMENT / "laser_flash_instrument.csv")
    assert process_laser_flash_table(pd.DataFrame({"Unrelated": [1.0]})) is None
    assert process_laser_flash_table(None) is None
