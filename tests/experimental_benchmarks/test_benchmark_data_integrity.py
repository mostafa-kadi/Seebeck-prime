"""Guard for the integrity of the benchmark datasets (audit finding D-02).

The committed processed dataset declares its carrier columns as
``published_carrier_concentration_cm3`` and
``published_carrier_mobility_cm2_Vs``, but the values written into them
were the **unconverted SI** values (m^-3 and m^2/(V.s)) - a factor of 10^6
and 10^4 respectively. The provenance cards repeated the same wrong units.

The defect escaped the existing tests because the round-trip check that
consumes those columns is **scale-invariant**: feeding n in the wrong unit
and recovering it with the same wrong unit cancels the error exactly.

These tests are therefore stated in **physical** terms - a semiconductor
cannot have a carrier concentration of 10^26 cm^-3 or a mobility of
5e-3 cm^2/(V.s) - so that the error cannot hide again.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
BENCH = REPO_ROOT / "tests" / "experimental_benchmarks"

#: The units in which the StarryData release publishes each quantity.
PUBLISHED_UNITS = {
    "Seebeck coefficient": "V*K^(-1)",
    "Electrical conductivity": "ohm^(-1)*m^(-1)",
    "Thermal conductivity": "W*m^(-1)*K^(-1)",
    "Power factor": "W*m^(-1)*K^(-2)",
    "ZT": "-",
    "Lattice thermal conductivity": "W*m^(-1)*K^(-1)",
    "Electronic thermal conductivity": "W*m^(-1)*K^(-1)",
    "Carrier concentration": "m^(-3)",
    "Carrier mobility": "m^2*V^(-1)*s^(-1)",
}

#: The benchmarks that publish carrier data.
CARRIER_BENCHMARKS = ("b2te3_bi2te2_4se0_6cu0_006", "sige_si80ge20p1")


def _raw(name: str) -> pd.DataFrame:
    return pd.read_csv(BENCH / "raw" / f"{name}_curves.csv")


def _processed(name: str) -> pd.DataFrame:
    return pd.read_csv(BENCH / "processed" / f"{name}.csv")


def _published_curve(raw: pd.DataFrame, prop: str) -> tuple[np.ndarray, np.ndarray]:
    """The published (x, y) pairs of one property, with the nulls removed.

    The StarryData curves occasionally carry ``null`` entries for points that
    could not be digitised; the extraction drops them, and so does this.
    """
    row = raw[raw.prop_y == prop].iloc[0]
    xs = [v for v in json.loads(row.x) if v is not None]
    ys = [v for v in json.loads(row.y) if v is not None]
    n = min(len(xs), len(ys))
    return np.array(xs[:n], dtype=float), np.array(ys[:n], dtype=float)


def _published_carrier_values_are_positive(name: str, prop: str) -> bool:
    raw = _raw(name)
    _, ys = _published_curve(raw, prop)
    return bool(np.all(ys > 0.0))


@pytest.mark.parametrize("name", CARRIER_BENCHMARKS)
def test_the_raw_extract_carries_the_published_units(name):
    """The raw extract must record the units the source published."""
    raw = _raw(name)
    for prop, expected in PUBLISHED_UNITS.items():
        present = raw[raw.prop_y == prop]
        if present.empty:
            continue
        found = set(present.unit_y.unique())
        assert found == {expected}, (
            f"{name}: the published unit of '{prop}' is {found}, not {expected}"
        )


@pytest.mark.parametrize("name", CARRIER_BENCHMARKS)
def test_the_processed_carrier_concentration_is_in_cm3(name):
    """A semiconductor's carrier concentration is 1e16 - 1e23 cm^-3.

    The defect this guards against stored the published m^-3 values
    (about 1e26) under a cm^-3 column name.

    The Bi2Te3 specimen is exempt: its published carrier concentration is
    *negative* (physically impossible), which the benchmark already reports
    as an unusable reference. Its unit consistency is covered by the
    conversion test below.
    """
    if not _published_carrier_values_are_positive(name, "Carrier concentration"):
        pytest.skip(f"{name}: the published carrier concentration is not physical")

    frame = _processed(name)
    block = frame[frame.grid == "carrier_concentration"]
    assert not block.empty, f"{name}: no carrier-concentration grid"

    values = block["published_carrier_concentration_cm3"].to_numpy()
    assert np.all(values > 0.0)
    assert values.min() > 1e16, (
        f"{name}: the carrier concentration looks like m^-3 rather than cm^-3 "
        f"(minimum {values.min():.3e})"
    )
    assert values.max() < 1e23, (
        f"{name}: implausible carrier concentration {values.max():.3e} cm^-3"
    )


@pytest.mark.parametrize("name", CARRIER_BENCHMARKS)
def test_the_processed_carrier_mobility_is_in_cm2_per_volt_second(name):
    """A real carrier mobility is 0.1 - 1e4 cm^2/(V.s).

    The defect this guards against stored the published m^2/(V.s) values
    (about 5e-3) under a cm^2/(V.s) column name.
    """
    if not _published_carrier_values_are_positive(name, "Carrier mobility"):
        pytest.skip(f"{name}: the published carrier mobility is not physical")

    frame = _processed(name)
    block = frame[frame.grid == "carrier_mobility"]
    assert not block.empty, f"{name}: no carrier-mobility grid"

    values = block["published_carrier_mobility_cm2_Vs"].to_numpy()
    assert np.all(values > 0.0)
    assert values.min() > 0.1, (
        f"{name}: the carrier mobility looks like m^2/(V.s) rather than "
        f"cm^2/(V.s) (minimum {values.min():.3e})"
    )
    assert values.max() < 1e4, (
        f"{name}: implausible carrier mobility {values.max():.3e} cm^2/(V.s)"
    )


@pytest.mark.parametrize("name", CARRIER_BENCHMARKS)
def test_the_processed_carrier_values_are_the_published_values_converted(name):
    """The processed carrier values must be the published SI values scaled.

    The comparison is **positional**, not an interpolation: the extraction
    copies the published values verbatim onto the published temperature
    grid, so the invariant is an identity. (Interpolation would in fact be
    invalid here - the published SiGe:P carrier curve contains a duplicated
    temperature point, 764.0777 K with two different concentrations, so its
    x list is not strictly increasing.)
    """
    raw = _raw(name)
    frame = _processed(name)

    concentration_x, concentration_y = _published_curve(raw, "Carrier concentration")
    block = frame[frame.grid == "carrier_concentration"]
    assert block["T_K"].to_numpy() == pytest.approx(concentration_x, rel=1e-12)
    assert block["published_carrier_concentration_cm3"].to_numpy() == pytest.approx(
        concentration_y * 1e-6, rel=1e-12
    )

    mobility_x, mobility_y = _published_curve(raw, "Carrier mobility")
    block = frame[frame.grid == "carrier_mobility"]
    assert block["T_K"].to_numpy() == pytest.approx(mobility_x, rel=1e-12)
    assert block["published_carrier_mobility_cm2_Vs"].to_numpy() == pytest.approx(
        mobility_y * 1e4, rel=1e-12
    )


def test_the_published_curves_are_copied_verbatim_into_the_processed_data():
    """A source-data observation, recorded so that it is not mistaken for a
    processing artefact.

    The published SiGe:P carrier-concentration curve contains one duplicated
    temperature point (764.0777 K) carrying two different concentrations.
    The extraction preserves both points verbatim, which is correct - the
    raw data are the published data - but it means the curve is not
    strictly monotonic in temperature and must not be interpolated.
    """
    raw = _raw("sige_si80ge20p1")
    concentration_x, _ = _published_curve(raw, "Carrier concentration")
    assert len(set(concentration_x)) != len(concentration_x), (
        "the duplicated published temperature point is expected; if this "
        "assertion fails the upstream data have changed and the extraction "
        "notes must be revisited"
    )


@pytest.mark.parametrize("name", CARRIER_BENCHMARKS)
def test_the_provenance_card_states_the_published_units(name):
    """The card must not claim a unit the source does not use."""
    card = (BENCH / "references" / f"{name}.md").read_text(encoding="utf-8")
    assert "Carrier concentration" in card
    assert "Carrier mobility" in card
    # the published SI units must appear ...
    assert "m^(-3)" in card
    assert "m^2*V^(-1)*s^(-1)" in card
    # ... and the previously recorded (wrong) ones must not
    assert "Carrier concentration (cm^(-3))" not in card
    assert "Carrier mobility (cm^2*V^(-1)*s^(-1))" not in card


def test_the_raw_extract_keeps_the_published_values_verbatim():
    """The raw extract must never be converted - it is the published data."""
    raw = _raw("sige_si80ge20p1")
    concentration = raw[raw.prop_y == "Carrier concentration"]
    xs = json.loads(concentration.iloc[0].x)
    ys = json.loads(concentration.iloc[0].y)
    assert max(ys) > 1e25, (
        "the raw carrier concentration should still be in m^-3, i.e. of order "
        "1e26"
    )
    assert len(xs) == len(ys)
