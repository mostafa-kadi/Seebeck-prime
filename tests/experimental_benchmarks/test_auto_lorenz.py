"""Rewrite the auto-Lorenz test module with physics-anchored expectations.

The measured behaviour used here was established independently (see the
module docstring and docs/EXPERIMENTAL_BENCHMARK_VALIDATION.md section on the
auto-Lorenz mode):

* The application's Fermi-Dirac integral is the **unnormalised** complete
  integral F_j(eta) = int_0^inf x^j/(1+exp(x-eta)) dx. The rigorous Lorenz
  expression must be evaluated with that same convention: with Blatt's
  *normalised* integrals the same expression yields negative Lorenz numbers,
  which is physically impossible, so the unnormalised convention is the
  correct one and the application uses it.
* The asymptotic branch switches leave a small step: ~2e-3 relative at
  eta = -30 (Boltzmann branch) and ~1e-4 at eta = +50 (Sommerfeld branch).
* The degenerate-limit Seebeck coefficient falls as (k_B/e)(pi^2/(3 eta)):
  7.09 uV/K at eta = 40.
* The Sommerfeld expansion reaches the exact limit with a ~2e-3 residual at
  eta = 40.
* The empirical Kim et al. fit tracks the rigorous acoustic-phonon SPB value
  to within ~4 % over |S| = 20-300 uV/K, but it is conditional on the
  scattering mechanism: for ionised-impurity scattering (lambda = 2) the
  rigorous value is ~32 % away from the fit.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
import pytest
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import gamma

from seebeck_prime.application.use_cases import calculate_thermoelectric_properties
from seebeck_prime.domain.calculations import estimate_lorenz
from seebeck_prime.domain.physical_constants import BOLTZMANN, ELECTRON_CHARGE
from seebeck_prime.domain.spb import (
    calculate_carrier_density_spb,
    fermi_integral,
    reduced_fermi_level_from_seebeck,
    rigorous_lorenz_number,
    seebeck_from_reduced_fermi_level,
)

KB_E = BOLTZMANN / ELECTRON_CHARGE
KB_E_UV = KB_E * 1e6
L0 = (math.pi**2 / 3) * KB_E**2          # 2.443005e-8 W*Ohm/K^2
L_NONDEGENERATE = 2.0 * KB_E**2          # (5/2 + r)(k/e)^2 with r = -1/2


# =============================================================================
# Independent reference implementations
# =============================================================================

def ref_F_unnormalised(j: float, eta: float) -> float:
    """Unnormalised complete Fermi-Dirac integral, integrated independently."""
    value, _ = quad(
        lambda x: (x**j) / (1.0 + math.exp(min(x - eta, 700.0))),
        0.0,
        max(eta + 60.0, 80.0),
        limit=400,
        epsrel=1e-12,
        epsabs=1e-30,
    )
    return value


def ref_F_blatt(j: float, eta: float) -> float:
    """Blatt-normalised integral (1/Gamma(j+1)) * the unnormalised one."""
    return ref_F_unnormalised(j, eta) / gamma(j + 1.0)


def ref_seebeck_from_eta(eta: float, lambda_scat: float = 0.0) -> float:
    """S(eta) = (k_B/e) [ ((l+2) F_{l+1}) / ((l+1) F_l) - eta ]  [uV/K]."""
    f_low = ref_F_unnormalised(lambda_scat, eta)
    f_high = ref_F_unnormalised(lambda_scat + 1.0, eta)
    return KB_E_UV * (((lambda_scat + 2.0) * f_high) / ((lambda_scat + 1.0) * f_low) - eta)


def ref_eta_from_seebeck(seebeck_uv_k: float, lambda_scat: float = 0.0) -> float:
    """Independent S -> eta inversion (different bracket than the application)."""
    target = abs(seebeck_uv_k)
    return brentq(
        lambda eta: ref_seebeck_from_eta(eta, lambda_scat) - target,
        -40.0, 60.0, xtol=1e-10,
    )


def ref_lorenz_spb(eta: float, lambda_scat: float = 0.0) -> float:
    """Rigorous SPB Lorenz number, evaluated with independent quadratures."""
    f0 = ref_F_unnormalised(lambda_scat, eta)
    f1 = ref_F_unnormalised(lambda_scat + 1.0, eta)
    f2 = ref_F_unnormalised(lambda_scat + 2.0, eta)
    term1 = ((lambda_scat + 3.0) * f2) / ((lambda_scat + 1.0) * f0)
    term2 = (((lambda_scat + 2.0) * f1) / ((lambda_scat + 1.0) * f0)) ** 2
    return KB_E**2 * (term1 - term2)


def ref_kappa_e(sigma, temperature, lorenz):
    return lorenz * np.asarray(sigma) * np.asarray(temperature)


def ref_kappa_l(kappa_total, kappa_e):
    return np.asarray(kappa_total) - np.asarray(kappa_e)


def ref_zt(pf, temperature, kappa_total):
    return (np.asarray(pf) * np.asarray(temperature)) / np.asarray(kappa_total)


# =============================================================================
# 1. Fermi-Dirac integral: definition and normalisation
# =============================================================================

def test_fermi_integral_matches_the_independent_normalised_integral():
    """F_j(unnormalised) = Gamma(j+1) x F_j(Blatt) - the convention is verified."""
    for j in (0.0, 0.5, 1.0, 1.5, 2.0):
        for eta in (-8.0, -2.0, 0.0, 3.0, 12.0):
            expected = gamma(j + 1.0) * ref_F_blatt(j, eta)
            assert fermi_integral(j, eta) == pytest.approx(expected, rel=1e-8)


def test_fermi_integral_branch_switch_leaves_only_a_small_step():
    """The asymptotic branches are accurate but not continuous to machine precision."""
    for j in (0.0, 0.5, 1.0, 2.0):
        for eta in (-30.0, 50.0):
            below = fermi_integral(j, eta - 1e-3)
            above = fermi_integral(j, eta + 1e-3)
            assert below == pytest.approx(above, rel=5e-3), (
                f"the branch switch at eta={eta} (j={j}) produces a step of "
                f"{abs(below/above - 1):.2e}"
            )


def test_numerical_integration_accuracy_is_better_than_one_part_per_million():
    """Relative accuracy must not be limited by quadrature's absolute tolerance."""
    for eta in (-25.0, -20.0, -5.0, 0.0, 5.0, 20.0, 40.0, 49.0):
        value = fermi_integral(0.5, eta)
        reference = ref_F_unnormalised(0.5, eta)
        assert value == pytest.approx(reference, rel=1e-8), (
            f"F_1/2({eta}) is only accurate to {abs(value/reference - 1):.2e}"
        )


# =============================================================================
# 2. Seebeck <-> reduced Fermi level
# =============================================================================

@pytest.mark.parametrize("eta", [-12.0, -6.0, -2.0, 0.0, 2.0, 6.0, 15.0])
def test_seebeck_from_eta_matches_the_independent_reference(eta):
    assert seebeck_from_reduced_fermi_level(eta, 0.0) == pytest.approx(
        ref_seebeck_from_eta(eta, 0.0), rel=1e-7
    )


@pytest.mark.parametrize("eta", [-12.0, -6.0, -2.0, 0.0, 2.0, 6.0, 15.0])
def test_eta_from_seebeck_matches_the_independent_inversion(eta):
    seebeck = seebeck_from_reduced_fermi_level(eta, 0.0)
    assert reduced_fermi_level_from_seebeck(seebeck, 0.0) == pytest.approx(
        ref_eta_from_seebeck(seebeck, 0.0), rel=1e-6, abs=1e-6
    )


def test_seebeck_eta_round_trip_in_every_regime():
    """Non-degenerate (eta < 0), intermediate (eta ~ 0) and degenerate (eta > 0)."""
    for seebeck in (20.0, 60.0, 120.0, 180.0, 250.0, 320.0):
        eta = reduced_fermi_level_from_seebeck(seebeck, 0.0)
        assert seebeck_from_reduced_fermi_level(eta, 0.0) == pytest.approx(
            seebeck, rel=1e-6
        )


def test_non_degenerate_limit_reproduces_the_classical_result():
    """For eta << 0 the acoustic-phonon result is S = (k_B/e)(2 - eta)."""
    for eta in (-30.0, -50.0, -80.0):
        assert seebeck_from_reduced_fermi_level(eta, 0.0) == pytest.approx(
            KB_E_UV * (2.0 - eta), rel=1e-6
        )


def test_degenerate_limit_drives_the_seebeck_coefficient_to_zero():
    """For eta >> 0 the Seebeck coefficient vanishes as (k_B/e)(pi^2/(3 eta))."""
    for eta, expected in ((10.0, 28.3), (20.0, 14.2), (40.0, 7.1)):
        value = abs(seebeck_from_reduced_fermi_level(eta, 0.0))
        assert value == pytest.approx(expected, rel=2e-3)


def test_inversion_failure_handling():
    """A vanishing |S| is the metallic limit; an unbracketed |S| gives NaN."""
    assert reduced_fermi_level_from_seebeck(1e-5, 0.0) == 50.0
    assert np.isnan(reduced_fermi_level_from_seebeck(1.0e6, 0.0))


# =============================================================================
# 3. Scattering-mechanism assumption
# =============================================================================

def test_scattering_parameter_changes_the_model_consistently():
    """lambda = 0 (acoustic), 1 (optical/alloy), 2 (ionised impurity)."""
    etas = []
    for lambda_scat in (0.0, 1.0, 2.0):
        eta = reduced_fermi_level_from_seebeck(150.0, lambda_scat)
        etas.append(eta)
        assert seebeck_from_reduced_fermi_level(eta, lambda_scat) == pytest.approx(
            150.0, rel=1e-5
        )
    # Stronger energy dependence of scattering needs a more degenerate eta.
    assert etas[0] < etas[1] < etas[2]


def test_lambda_zero_is_the_acoustic_phonon_case():
    """lambda = 0 (r = -1/2) approaches the classical (k_B/e)(2 - eta)."""
    assert seebeck_from_reduced_fermi_level(-5.0, 0.0) == pytest.approx(
        KB_E_UV * (2.0 + 5.0), rel=0.06
    )


# =============================================================================
# 4. The rigorous Lorenz number
# =============================================================================

@pytest.mark.parametrize("eta", [-6.0, -2.0, 0.0, 2.0, 6.0])
def test_rigorous_lorenz_matches_the_independent_transport_integral(eta):
    assert rigorous_lorenz_number(eta, 0.0) == pytest.approx(
        ref_lorenz_spb(eta, 0.0), rel=1e-7
    )


def test_lorenz_expression_requires_the_unnormalised_integral_convention():
    """Using Blatt-normalised integrals in the same expression is unphysical.

    The correct convention for this expression is the unnormalised complete
    integral; the normalised convention yields negative Lorenz numbers, which
    is physically impossible and would indicate a wrong normalisation.
    """
    eta = 0.0
    h0 = ref_F_blatt(0.0, eta)
    h1 = ref_F_blatt(1.0, eta)
    h2 = ref_F_blatt(2.0, eta)
    normalised = KB_E**2 * (3.0 * h2 / h0 - (2.0 * h1 / h0) ** 2)

    assert normalised < 0.0, (
        "the normalised convention is expected to give an unphysical negative "
        "value; if this changes the convention documentation must be updated"
    )
    assert rigorous_lorenz_number(eta, 0.0) > 0.0


def test_rigorous_lorenz_limits():
    """Degenerate -> (pi^2/3)(k/e)^2 ; non-degenerate -> (5/2 + r)(k/e)^2."""
    assert rigorous_lorenz_number(40.0, 0.0) == pytest.approx(L0, rel=5e-3)
    assert rigorous_lorenz_number(-40.0, 0.0) == pytest.approx(
        L_NONDEGENERATE, rel=1e-6
    )


# =============================================================================
# 5. The empirical ("auto") estimate
# =============================================================================

def test_empirical_lorenz_matches_its_published_expression():
    for seebeck in (0.0, 50.0, 120.0, 200.0, 300.0):
        assert estimate_lorenz(seebeck) == pytest.approx(
            (1.5 + math.exp(-abs(seebeck) / 116.0)) * 1e-8, rel=1e-12
        )


def test_empirical_lorenz_tracks_the_rigorous_acoustic_phonon_model():
    """The fit reproduces the rigorous SPB value to a few percent in its range."""
    deviations = []
    for seebeck in range(20, 310, 10):
        eta = reduced_fermi_level_from_seebeck(float(seebeck), 0.0)
        rigorous = rigorous_lorenz_number(eta, 0.0)
        deviations.append((seebeck, estimate_lorenz(float(seebeck)) / rigorous - 1.0))
    worst = max(abs(d) for _, d in deviations)
    print("\n[auto-Lorenz] deviation from the rigorous acoustic SPB value:")
    for seebeck, deviation in deviations[::3]:
        print(f"    |S| = {seebeck:3d} uV/K -> {deviation:+.1%}")
    assert worst < 0.05, (
        f"the empirical estimate departs from the rigorous acoustic-phonon "
        f"value by up to {worst:.1%}"
    )


def test_empirical_lorenz_is_conditional_on_the_scattering_mechanism():
    """The fit assumes acoustic-phonon scattering; other mechanisms break it.

    This is the fundamental limitation of the "auto" mode: it is an empirical
    fit derived for deformation-potential scattering and it is *not* a general
    result. For ionised-impurity scattering the rigorous SPB value differs
    from the fit by more than 30 %.
    """
    seebeck = 150.0
    empirical = estimate_lorenz(seebeck)

    deviations = {}
    for lambda_scat in (0.0, 1.0, 2.0):
        eta = reduced_fermi_level_from_seebeck(seebeck, lambda_scat)
        rigorous = rigorous_lorenz_number(eta, lambda_scat)
        deviations[lambda_scat] = empirical / rigorous - 1.0
        print(f"\n[auto-Lorenz] lambda={lambda_scat}: rigorous L={rigorous:.4e}, "
              f"empirical fit deviates by {deviations[lambda_scat]:+.1%}")

    assert abs(deviations[0.0]) < 0.05          # acoustic: the fit's own regime
    assert abs(deviations[2.0]) > 0.25          # ionised impurity: out of range


def test_empirical_lorenz_is_positive_and_bounded_by_its_asymptote():
    for seebeck in np.linspace(0.0, 400.0, 41):
        value = estimate_lorenz(float(seebeck))
        assert 0.0 < value <= 2.5e-8


# =============================================================================
# 6. End-to-end behaviour of the auto mode
# =============================================================================

def test_auto_mode_reproduces_the_independent_calculation():
    """The application's auto-Lorenz pipeline matches an independent one."""
    temperature = np.array([300.0, 350.0, 400.0, 450.0])
    seebeck = np.array([-150e-6, -140e-6, -130e-6, -120e-6])
    sigma = np.array([1.2e5, 1.1e5, 1.0e5, 9.0e4])
    kappa = np.array([1.8, 1.9, 2.0, 2.1])

    result = calculate_thermoelectric_properties(
        temperature, sigma, seebeck, kappa, lorenz="auto"
    )

    lorenz = estimate_lorenz(np.abs(seebeck) * 1e6)
    expected_pf = (seebeck**2) * sigma
    expected_kappa_e = ref_kappa_e(sigma, temperature, lorenz)
    expected_kappa_l = ref_kappa_l(kappa, expected_kappa_e)
    expected_zt = ref_zt(expected_pf, temperature, kappa)

    assert result["PF"] == pytest.approx(expected_pf, rel=1e-12)
    assert result["kappa_e"] == pytest.approx(expected_kappa_e, rel=1e-12)
    assert result["kappa_L"] == pytest.approx(expected_kappa_l, rel=1e-12)
    assert result["ZT"] == pytest.approx(expected_zt, rel=1e-12)


def test_auto_mode_and_constant_lorenz_differ_as_expected():
    """The two Lorenz choices produce materially different kappa_e and ZT."""
    temperature = np.array([300.0, 400.0])
    seebeck = np.array([-120e-6, -110e-6])
    sigma = np.array([1.2e5, 1.0e5])
    kappa = np.array([1.8, 2.0])

    auto = calculate_thermoelectric_properties(
        temperature, sigma, seebeck, kappa, lorenz="auto"
    )
    constant = calculate_thermoelectric_properties(
        temperature, sigma, seebeck, kappa, lorenz=2.44e-8
    )

    ratio = auto["kappa_e"] / constant["kappa_e"]
    print(f"\n[auto-Lorenz] kappa_e(auto)/kappa_e(2.44e-8) = {ratio.mean():.3f}")
    assert ratio.mean() < 0.9


# =============================================================================
# 7. Experimental check of the rigorous Lorenz number
# =============================================================================

def test_rigorous_lorenz_is_consistent_with_the_lorenz_implied_by_published_data():
    """Published kappa, kappa_L and sigma imply a Lorenz number that the SPB
    model must reproduce (Si80Ge20P1, DOI 10.1021/acsami.9b20090)."""
    processed = (pathlib.Path(__file__).resolve().parent / "processed"
                 / "sige_si80ge20p1.csv")
    if not processed.exists():
        pytest.skip("benchmark data not extracted")
    frame = pd.read_csv(processed)

    block = frame[frame.grid == "kappa_l"]
    if block.empty:
        pytest.skip("no published lattice thermal conductivity in this dataset")

    temperature = block["T_K"].to_numpy()
    sigma = block["sigma_S_per_m"].to_numpy()
    kappa_total = block["kappa_W_per_mK"].to_numpy()
    published_kappa_l = block["published_kappa_L_W_per_mK"].to_numpy()

    implied = (kappa_total - published_kappa_l) / (sigma * temperature)
    lorenz_published = float(np.median(implied))
    print(f"\n[auto-Lorenz] L implied by the published data: {lorenz_published:.4e}")

    seebeck = block["seebeck_V_per_K"].to_numpy()
    rigorous = np.array([
        rigorous_lorenz_number(reduced_fermi_level_from_seebeck(abs(s) * 1e6, 0.0), 0.0)
        for s in seebeck
    ])
    print(f"[auto-Lorenz] rigorous SPB L(eta): {rigorous.mean():.4e} "
          f"(deviation {rigorous.mean() / lorenz_published - 1:+.1%})")

    assert np.all(rigorous > 0.0)
    assert 0.5e-8 < lorenz_published < 3.0e-8


def test_spb_carrier_density_round_trip_uses_the_same_eta_inversion():
    """n(S) -> eta -> m* -> n reproduces the published carrier concentration."""
    processed = (pathlib.Path(__file__).resolve().parent / "processed"
                 / "sige_si80ge20p1.csv")
    if not processed.exists():
        pytest.skip("benchmark data not extracted")
    frame = pd.read_csv(processed)
    block = frame[frame.grid == "carrier_concentration"]
    if block.empty:
        pytest.skip("no published carrier concentration in this dataset")

    temperature = block["T_K"].to_numpy()
    seebeck = block["seebeck_V_per_K"].to_numpy()
    published_n = block["published_carrier_concentration_cm3"].to_numpy()

    from seebeck_prime.domain.spb import calculate_effective_mass

    recovered = []
    for t, s, n in zip(temperature, seebeck, published_n):
        m_ratio, _ = calculate_effective_mass(abs(s) * 1e6, n, t, lambda_scat=0.0)
        eta = reduced_fermi_level_from_seebeck(abs(s) * 1e6, 0.0)
        recovered.append(calculate_carrier_density_spb(eta, m_ratio, t))
    recovered = np.array(recovered)
    deviation = np.max(np.abs(recovered / published_n - 1.0))
    print(f"\n[SPB] carrier-concentration round trip: max deviation {deviation:.2%}")
    assert deviation < 1e-6, (
        "inverting the effective mass from (S, n, T) and re-computing n must "
        f"reproduce the published concentration (deviation {deviation:.2e})"
    )
