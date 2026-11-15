"""Phase 3: the SiGe:P Lorenz-number finding is locked in as a regression.

The published Si80Ge20P1 data imply L = 2.4579e-8 W*Ohm/K^2, while the
application's acoustic-scattering SPB default (lambda = 0) gives 1.592e-8 - a
35 % disagreement. The Phase 3 investigation
(``validation/remediation/SIGE_LORENZ_INVESTIGATION.md``) established that the
cause is the **scattering assumption**, not the implementation:

* the published kappa / kappa_L pair is internally consistent (3.0 % spread,
  at the 1.7 % digitisation noise floor);
* a scattering exponent of lambda = 1.41 - between alloy/optical and
  ionised-impurity scattering, as expected for a P-doped alloy - reproduces
  the published value exactly.

These tests are **characterisation tests of a negative result**: they assert
that the model is NOT refitted to the measurement. If a future change made
the acoustic model agree with the published data, these tests would fail and
the change would have to be justified as a *model* change rather than a
fitting.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from seebeck_prime.domain.physical_constants import (  # noqa: E402
    DEFAULT_LORENZ,
    SOMMERFELD_LORENZ_EXACT,
)
from seebeck_prime.domain.spb import (  # noqa: E402
    reduced_fermi_level_from_seebeck,
    rigorous_lorenz_number,
)

RAW = (
    REPO_ROOT / "tests" / "experimental_benchmarks" / "raw"
    / "sige_si80ge20p1_curves.csv"
)


def _curves():
    import pandas as pd

    frame = pd.read_csv(RAW)
    out = {}
    for row in frame.itertuples(index=False):
        xs = np.array([v for v in json.loads(row.x) if v is not None], dtype=float)
        ys = np.array([v for v in json.loads(row.y) if v is not None], dtype=float)
        n = min(len(xs), len(ys))
        order = np.argsort(xs[:n])
        out[row.prop_y] = (xs[:n][order], ys[:n][order])
    return out


@pytest.fixture(scope="module")
def implied():
    """The Lorenz number implied by the published kappa, kappa_L and sigma."""
    curves = _curves()
    t_kl, kappa_l = curves["Lattice thermal conductivity"]
    t_k, kappa = curves["Thermal conductivity"]
    t_s, sigma = curves["Electrical conductivity"]
    t_se, seebeck = curves["Seebeck coefficient"]

    kappa_at = np.interp(t_kl, t_k, kappa)
    sigma_at = np.interp(t_kl, t_s, sigma)
    seebeck_at = np.interp(t_kl, t_se, seebeck)
    values = (kappa_at - kappa_l) / (sigma_at * t_kl)
    return float(np.median(values)), seebeck_at


def test_the_published_pair_is_internally_consistent(implied):
    """Rejects the hypothesis that the published kappa / kappa_L pair is the
    source of the discrepancy (as it is for the PbTe dataset)."""
    median, _ = implied
    curves = _curves()
    t_kl, kappa_l = curves["Lattice thermal conductivity"]
    t_k, kappa = curves["Thermal conductivity"]
    t_s, sigma = curves["Electrical conductivity"]

    kappa_at = np.interp(t_kl, t_k, kappa)
    sigma_at = np.interp(t_kl, t_s, sigma)
    values = (kappa_at - kappa_l) / (sigma_at * t_kl)
    spread = (values.max() - values.min()) / np.median(values)

    assert spread < 0.10, (
        f"the published SiGe:P pair should be internally consistent; spread "
        f"{spread:.1%}"
    )
    assert median == pytest.approx(2.4579e-8, rel=1e-3)


def test_the_acoustic_default_disagrees_with_the_published_data(implied):
    """The negative result itself: the acoustic SPB value is 35 % low.

    This assertion is what stops the model from being quietly re-fitted.
    """
    median, seebeck_at = implied

    acoustic = float(np.median([
        rigorous_lorenz_number(
            reduced_fermi_level_from_seebeck(abs(float(s)) * 1e6, 0.0), 0.0
        )
        for s in seebeck_at
    ]))

    assert acoustic == pytest.approx(1.592e-8, rel=2e-3)
    assert abs(acoustic / median - 1.0) > 0.25, (
        "the SPB acoustic value is expected to disagree with the published "
        "SiGe:P data by more than 25 %; if this changes, the documentation "
        "of the finding must be revised"
    )


def test_an_alloy_scattering_exponent_reproduces_the_published_value(implied):
    """lambda = 1.41 reproduces the published Lorenz number exactly.

    That value lies between alloy/optical (1) and ionised-impurity (2)
    scattering, which is what is expected for a P-doped SiGe alloy.
    """
    median, seebeck_at = implied

    value = float(np.median([
        rigorous_lorenz_number(
            reduced_fermi_level_from_seebeck(abs(float(s)) * 1e6, 1.41), 1.41
        )
        for s in seebeck_at
    ]))

    assert value == pytest.approx(median, rel=2e-3), (
        "the scattering exponent identified by the investigation should still "
        "reproduce the published Lorenz number"
    )

    # the ordering that gives the finding its meaning
    l0 = float(np.median([
        rigorous_lorenz_number(
            reduced_fermi_level_from_seebeck(abs(float(s)) * 1e6, 0.0), 0.0
        )
        for s in seebeck_at
    ]))
    l1 = float(np.median([
        rigorous_lorenz_number(
            reduced_fermi_level_from_seebeck(abs(float(s)) * 1e6, 1.0), 1.0
        )
        for s in seebeck_at
    ]))
    l2 = float(np.median([
        rigorous_lorenz_number(
            reduced_fermi_level_from_seebeck(abs(float(s)) * 1e6, 2.0), 2.0
        )
        for s in seebeck_at
    ]))
    assert l0 < l1 < median < l2


def test_the_application_constant_agrees_with_the_published_data(implied):
    """The constant the application uses by default is the one that matches."""
    median, _ = implied
    assert abs(DEFAULT_LORENZ / median - 1.0) < 0.01
    assert abs(SOMMERFELD_LORENZ_EXACT / median - 1.0) < 0.01


def test_the_specimen_crosses_the_classical_to_degenerate_transition():
    """Why the scattering exponent matters so much for this specimen."""
    from seebeck_prime.domain.spb import fermi_integral

    curves = _curves()
    t_se, seebeck = curves["Seebeck coefficient"]
    etas = [
        reduced_fermi_level_from_seebeck(abs(float(s)) * 1e6, 0.0) for s in seebeck
    ]
    f_half = [fermi_integral(0.5, float(e)) for e in etas]

    assert min(f_half) < 0.443 < max(f_half), (
        "the specimen is expected to span the classical-to-degenerate "
        f"transition; F_1/2 range {min(f_half):.3f}-{max(f_half):.3f}"
    )
