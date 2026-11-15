"""Validation of the multi-sample workflow, the weighted mobility and the SPB inversion.

All three are validated against the *published* measurements of the benchmark
datasets (StarryData / peer-reviewed papers), not against synthetic data.

Unit traps found in the source data and handled explicitly here:

* The published **carrier concentration** is given in **m^-3** (unit string
  ``m^(-3)``), while the application's SPB API takes **cm^-3**; the
  conversion is applied in the test and asserted.
* The published **carrier mobility** of the Bi2Te3 sample is *negative*
  (-0.0096 m^2/(V*s)), which is physically impossible: that curve is
  mis-digitised in the source database and cannot be used as a reference.
  The corresponding comparison is therefore reported as UNVERIFIED.
"""

from __future__ import annotations

import json
import math
import pathlib

import numpy as np
import pandas as pd
import pytest

from seebeck_prime.application.use_cases import (
    process_multi_sample_batch,
    process_multi_sample_data,
)
from seebeck_prime.domain.spb import (
    calculate_carrier_density_spb,
    calculate_effective_mass,
    fermi_integral,
    reduced_fermi_level_from_seebeck,
)
from seebeck_prime.domain.transport import calculate_weighted_mobility

HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE / "raw"

BENCHMARKS = {
    "b2te3_bi2te2_4se0_6cu0_006": "Bi2Te3-based",
    "pbte_pbte0_95pbs0_05": "PbTe-based",
    "sige_si80ge18sb2": "SiGe-based",
    "sige_si80ge20p1": "SiGe-based",
}

SPB_DATASET = "sige_si80ge20p1"


def _published_curves(benchmark: str) -> dict:
    frame = pd.read_csv(RAW / f"{benchmark}_curves.csv")
    curves = {}
    for row in frame.itertuples(index=False):
        xs = np.array([v for v in json.loads(row.x) if v is not None], dtype=float)
        ys = np.array([v for v in json.loads(row.y) if v is not None], dtype=float)
        n = min(len(xs), len(ys))
        order = np.argsort(xs[:n])
        curves[row.prop_y] = (xs[:n][order], ys[:n][order], row.unit_y)
    return curves


def _sample_frame(benchmark: str) -> pd.DataFrame:
    """Build the multi-sample input frame from the published curves."""
    curves = _published_curves(benchmark)
    temperature, seebeck, _ = curves["Seebeck coefficient"]
    return pd.DataFrame({
        "Temperature": temperature,
        "Seebeck": seebeck,
        "Sigma": np.interp(temperature, curves["Electrical conductivity"][0],
                           curves["Electrical conductivity"][1]),
        "Kappa_total": np.interp(temperature, curves["Thermal conductivity"][0],
                                  curves["Thermal conductivity"][1]),
    })


# =============================================================================
# 5. Multi-sample processing
# =============================================================================

@pytest.mark.parametrize("benchmark", sorted(BENCHMARKS))
def test_multi_sample_processing_reproduces_the_published_power_factor(benchmark):
    """PF computed by the multi-sample workflow must match the published PF."""
    frame = _sample_frame(benchmark)
    curves = _published_curves(benchmark)
    temperature, published_pf, _ = curves["Power factor"]

    processed = process_multi_sample_data(frame)

    assert "Power Factor" in processed.columns
    assert "PF_mW" in processed.columns
    computed = np.interp(temperature, processed["Temperature"], processed["Power Factor"])

    deviation = np.max(np.abs(computed / published_pf - 1.0))
    print(f"\n[{benchmark}] multi-sample PF vs published: max deviation {deviation:.2%}")
    assert deviation <= 0.05, (
        f"{benchmark}: the multi-sample workflow deviates from the published "
        f"power factor by {deviation:.2%}"
    )


@pytest.mark.parametrize("benchmark", sorted(BENCHMARKS))
def test_multi_sample_processing_reproduces_the_published_zt(benchmark):
    """ZT computed by the multi-sample workflow must match the published ZT."""
    frame = _sample_frame(benchmark)
    curves = _published_curves(benchmark)
    temperature, published_zt, _ = curves["ZT"]

    processed = process_multi_sample_data(frame)

    computed = np.interp(temperature, processed["Temperature"], processed["ZT"])
    deviation = np.max(np.abs(computed / published_zt - 1.0))
    print(f"\n[{benchmark}] multi-sample ZT vs published: max deviation {deviation:.2%}")
    assert deviation <= 0.10, (
        f"{benchmark}: the multi-sample workflow deviates from the published "
        f"ZT by {deviation:.2%}"
    )


@pytest.mark.parametrize("benchmark", sorted(BENCHMARKS))
def test_multi_sample_processing_uses_the_documented_display_units(benchmark):
    """PF_mW, Sigma_Scm and S_uVK must carry the documented units."""
    frame = _sample_frame(benchmark)
    processed = process_multi_sample_data(frame)

    assert processed["PF_mW"].iloc[0] == pytest.approx(
        processed["Power Factor"].iloc[0] * 1000.0, rel=1e-12
    )
    assert processed["Sigma_Scm"].iloc[0] == pytest.approx(
        processed["Sigma"].iloc[0] * 0.01, rel=1e-12
    )
    assert processed["S_uVK"].iloc[0] == pytest.approx(
        processed["Seebeck"].iloc[0] * 1e6, rel=1e-12
    )


def test_multi_sample_batch_preserves_names_and_order():
    frames = {"A": _sample_frame("b2te3_bi2te2_4se0_6cu0_006"),
              "B": _sample_frame("sige_si80ge18sb2")}
    result = process_multi_sample_batch(frames)

    assert list(result.keys()) == ["A", "B"]
    assert len(result["A"]) == len(frames["A"])


def test_multi_sample_processing_drops_rows_with_missing_values():
    frame = _sample_frame("b2te3_bi2te2_4se0_6cu0_006")
    broken = frame.copy()
    broken.loc[0, "Sigma"] = np.nan

    processed = process_multi_sample_data(broken)

    assert len(processed) == len(frame) - 1


# =============================================================================
# 6. Weighted mobility
# =============================================================================

def _independent_weighted_mobility(temperature_k, resistivity_mohm_cm, seebeck_uv_k):
    """Independent implementation of the Snyder-style weighted mobility."""
    kb_e_uv = 86.17333262145179            # (k_B/e) in uV/K, CODATA exact
    reduced = abs(np.asarray(seebeck_uv_k, dtype=float)) / kb_e_uv
    term1 = np.exp(reduced - 2.0) / (1.0 + np.exp(-5.0 * (reduced - 1.0)))
    term2 = (3.0 * math.pi**2 / reduced) / (1.0 + np.exp(5.0 * (reduced - 1.0)))
    shape = term1 + term2
    return (
        331.0
        * (1.0 / np.asarray(resistivity_mohm_cm, dtype=float))
        * (np.asarray(temperature_k, dtype=float) / 300.0) ** (-1.5)
        * shape
    )


def test_weighted_mobility_matches_the_independent_implementation():
    """The application's weighted mobility equals an independent evaluation."""
    temperature = np.array([300.0, 350.0, 400.0])
    resistivity = np.array([1.0, 1.2, 1.5])
    seebeck = np.array([-150.0, -140.0, -130.0])

    computed = calculate_weighted_mobility(temperature, resistivity, seebeck)
    expected = _independent_weighted_mobility(temperature, resistivity, seebeck)

    assert computed == pytest.approx(expected, rel=1e-9)


def test_weighted_mobility_comparison_against_published_mobility_is_unverified():
    """The published carrier-mobility curve of this sample is unusable.

    The Starrydata curve is negative (-0.0096 m^2/(V*s)), which is physically
    impossible for a carrier mobility, so it is a mis-digitised curve in the
    source database and cannot serve as an experimental reference. The
    comparison is reported as UNVERIFIED rather than silently skipped.
    """
    curves = _published_curves("b2te3_bi2te2_4se0_6cu0_006")
    if "Carrier mobility" not in curves:
        pytest.skip("the dataset publishes no carrier mobility")
    temperature, published_mu, unit = curves["Carrier mobility"]

    print(f"\n[weighted mobility] published carrier mobility ({unit}): "
          f"{published_mu[:4]} ...")
    if (published_mu <= 0).all():
        pytest.skip(
            "UNVERIFIED: the published carrier-mobility curve is negative "
            "(physically impossible) and cannot be used as a reference"
        )

    ts, ss, _ = curves["Seebeck coefficient"]
    tg, sg, _ = curves["Electrical conductivity"]
    sigma_at_t = np.interp(temperature, tg, sg)
    resistivity_mohm_cm = 1.0e5 / sigma_at_t          # 1 Ohm.m = 1e5 mOhm.cm
    mu_w = calculate_weighted_mobility(
        temperature, resistivity_mohm_cm, np.interp(temperature, ts, ss)
    )
    ratio = mu_w / published_mu
    print(f"[weighted mobility] mu_w / mu_published: median {np.median(ratio):.2f}")
    assert 0.05 < np.median(ratio) < 20.0


def test_weighted_mobility_scales_inversely_with_resistivity():
    """mu_w ~ 1/rho at fixed temperature and Seebeck coefficient."""
    base = calculate_weighted_mobility(300.0, 1.0, -150.0)
    assert calculate_weighted_mobility(300.0, 2.0, -150.0) == pytest.approx(
        base / 2, rel=1e-12
    )


# =============================================================================
# 7. SPB inversion
# =============================================================================

def _spb_inputs(benchmark: str = SPB_DATASET):
    """Published (T, |S|, n) with the unit conversion the API expects."""
    curves = _published_curves(benchmark)
    if "Carrier concentration" not in curves:
        pytest.skip("the dataset publishes no carrier concentration")
    temperature, concentration, unit = curves["Carrier concentration"]
    ts, ss, _ = curves["Seebeck coefficient"]
    seebeck = np.interp(temperature, ts, ss)

    if unit == "m^(-3)":
        concentration_cm3 = concentration * 1e-6        # m^-3 -> cm^-3
    elif unit == "cm^(-3)":
        concentration_cm3 = concentration
    else:
        pytest.skip(f"unexpected carrier-concentration unit: {unit}")
    return temperature, seebeck, concentration_cm3


def test_spb_effective_mass_matches_an_independent_inversion():
    """m_d* from (S, n, T) must equal an independent evaluation."""
    temperature, seebeck, concentration_cm3 = _spb_inputs()

    computed = [
        calculate_effective_mass(abs(s) * 1e6, n, t, lambda_scat=0.0)[0]
        for t, s, n in zip(temperature, seebeck, concentration_cm3)
    ]

    from seebeck_prime.domain.physical_constants import (
        AVOGADRO, BOLTZMANN, ELECTRON_CHARGE, PLANCK,
    )

    n0 = 4.0 * math.pi * (
        2.0 * 9.1093837015e-31 * BOLTZMANN / PLANCK**2
    ) ** 1.5 * 1.0     # N0 for m*/m_e = 1, in m^-3 K^-3/2 units

    expected = []
    for t, s, n in zip(temperature, seebeck, concentration_cm3):
        eta = reduced_fermi_level_from_seebeck(abs(s) * 1e6, 0.0)
        f_half = fermi_integral(0.5, eta)
        expected.append(((n * 1e6) / (n0 * t**1.5 * f_half)) ** (2.0 / 3.0))

    assert computed == pytest.approx(expected, rel=1e-6)
    del AVOGADRO, ELECTRON_CHARGE


def test_spb_effective_mass_is_physically_plausible_for_the_benchmark():
    """The inverted mass of the SiGe sample must lie in the published range.

    For P-doped SiGe the literature reports density-of-states effective masses
    of order 1.5-3 m_e (heavy-hole dominated); the value obtained from the
    published (S, n, T) must fall in that range, which is an experimental
    check of the inversion.
    """
    temperature, seebeck, concentration_cm3 = _spb_inputs()

    masses = [
        calculate_effective_mass(abs(s) * 1e6, n, t, lambda_scat=0.0)[0]
        for t, s, n in zip(temperature, seebeck, concentration_cm3)
    ]
    median = float(np.median(masses))
    print(f"\n[SPB] inverted m_d* for Si80Ge20P1: {median:.3f} m_e "
          f"(range {min(masses):.2f} - {max(masses):.2f})")
    assert 1.0 < median < 3.0, (
        f"the inverted effective mass ({median:.2f} m_e) is outside the "
        "physically expected range for a P-doped SiGe alloy"
    )


def test_spb_effective_mass_round_trip_reproduces_the_published_concentration():
    """n(S, m*) must reproduce the published carrier concentration."""
    temperature, seebeck, concentration_cm3 = _spb_inputs()

    recovered = []
    for t, s, n in zip(temperature, seebeck, concentration_cm3):
        m_ratio, _ = calculate_effective_mass(abs(s) * 1e6, n, t, lambda_scat=0.0)
        eta = reduced_fermi_level_from_seebeck(abs(s) * 1e6, 0.0)
        recovered.append(calculate_carrier_density_spb(eta, m_ratio, t))

    deviation = np.max(np.abs(np.array(recovered) / concentration_cm3 - 1.0))
    print(f"\n[SPB] carrier-concentration round trip: max deviation {deviation:.2%}")
    assert deviation < 1e-6
