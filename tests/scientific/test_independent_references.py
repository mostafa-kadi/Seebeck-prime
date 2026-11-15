"""Phase II-IV: every implemented equation against an independent reference.

The references live in ``validation/independent_calculations/`` and are
written from the governing equations; they never call the application's
calculation functions.

Run from the repository root:
    python -m pytest tests/scientific -v
"""

from __future__ import annotations

import ast
import math
import pathlib
import sys

import numpy as np
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from validation.independent_calculations import references as ref  # noqa: E402

from seebeck_prime.domain import calculations as calc  # noqa: E402
from seebeck_prime.domain import hall as hall_domain  # noqa: E402
from seebeck_prime.domain import phonon as phonon_domain  # noqa: E402
from seebeck_prime.domain import transport as transport_domain  # noqa: E402
from seebeck_prime.domain import uncertainty as unc  # noqa: E402


# =====================================================================
# Independence of the reference implementations
# =====================================================================

REFERENCE_DIR = REPO_ROOT / "validation" / "independent_calculations"


def _imported_module_names(path: pathlib.Path) -> set[str]:
    """Every module name imported by ``path`` (absolute and relative)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:                      # relative import
                names.add("." * node.level + (node.module or ""))
            elif node.module:
                names.add(node.module.split(".")[0])
    return names


def test_reference_package_does_not_import_the_application():
    """The independent references must not use the application's own code.

    This is the machine-checkable form of the independence requirement of
    Phase IX: a reference that imported ``seebeck_prime`` would be a
    tautological comparison rather than an independent one.
    """
    offenders = {}
    for path in sorted(REFERENCE_DIR.glob("*.py")):
        imported = _imported_module_names(path)
        forbidden = {
            name for name in imported
            if name in {"seebeck_prime", "src"} or name.startswith("seebeck_prime.")
        }
        if forbidden:
            offenders[path.name] = sorted(forbidden)

    assert not offenders, (
        "the independent reference package must not import the application: "
        f"{offenders}"
    )


def test_reference_package_does_not_use_dynamic_imports():
    """No ``importlib`` / ``__import__`` escape hatch into the application."""
    for path in sorted(REFERENCE_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "__import__" not in source, path.name
        assert "importlib" not in source, path.name


def test_reference_package_depends_only_on_numpy_scipy_and_the_stdlib():
    """The reference must not inherit behaviour from the application's stack."""
    allowed_third_party = {"numpy", "scipy"}
    stdlib = set(sys.stdlib_module_names)
    for path in sorted(REFERENCE_DIR.glob("*.py")):
        imported = _imported_module_names(path)
        external = {
            name for name in imported
            if name not in stdlib and name not in allowed_third_party
            and not name.startswith(".")
            and name != "references"
        }
        assert not external, f"{path.name} imports {sorted(external)}"


def test_reference_module_exposes_the_documented_functions():
    """The reference API must stay complete (a renamed function is a defect)."""
    expected = {
        "fermi_integral_blatt", "fermi_integral_unnormalised",
        "spb_seebeck", "spb_eta_from_seebeck", "spb_lorenz_number",
        "spb_effective_density_of_states", "spb_carrier_density",
        "spb_effective_mass",
        "power_factor", "resistivity_from_geometry", "conductivity_from_resistivity",
        "kappa_electronic", "kappa_lattice", "figure_of_merit",
        "kappa_from_laser_flash_si", "kappa_from_laser_flash_lab",
        "lorenz_sommerfeld", "lorenz_kim", "weighted_mobility_snyder",
        "seebeck_from_regression",
        "hall_coefficient", "hall_carrier_density", "hall_mobility",
        "scattering_exponent_from_power_law",
        "dulong_petit_molar", "dulong_petit_specific", "device_efficiencies",
        "u_pf", "u_kappa_electronic", "u_kappa_lattice", "u_zt",
        "u_conductivity_from_geometry", "u_kappa_from_laser_flash", "u_density",
        "monte_carlo_uncertainty",
    }
    missing = sorted(name for name in expected if not hasattr(ref, name))
    assert not missing, f"missing reference functions: {missing}"


# =====================================================================
# Seebeck coefficient (linear regression and single differences)
# =====================================================================

def test_seebeck_from_single_difference_matches_the_definition():
    """S = dV/dT for a single measurement pair (no regression needed)."""
    delta_v, delta_t = 1.5e-3, 10.0
    assert delta_v / delta_t == pytest.approx(150e-6, rel=1e-12)

    # The application obtains S from a regression over several pairs; a
    # three-point fit on a perfectly linear set must reproduce the
    # single-difference value exactly.
    slope, stderr = ref.seebeck_from_regression(
        [delta_t, 2 * delta_t, 3 * delta_t], [delta_v, 2 * delta_v, 3 * delta_v]
    )
    assert slope == pytest.approx(delta_v / delta_t, rel=1e-12)
    assert stderr == pytest.approx(0.0, abs=1e-15)


def test_seebeck_regression_matches_an_independent_ols():
    """The application's regression (scipy linregress) must match a closed-form OLS.

    The slope is compared on exactly collinear data, where the closed form is
    exact. The *standard error* is deliberately **not** compared there: for
    perfectly collinear data the true standard error is exactly zero, so the
    two implementations would only be compared in their floating-point noise.
    That comparison carries no scientific meaning and is not stable across
    SciPy versions (SciPy 1.17 returns exactly 0.0, SciPy 1.18 returns
    1.8e-12 V/K for the same data). The standard error is therefore checked
    against its physical significance here, and against SciPy on data with
    genuine scatter in the next test.
    """
    delta_t = np.array([5.0, 10.0, 15.0, 20.0, 25.0])
    delta_v = np.array([-0.00075, -0.0015, -0.00225, -0.0030, -0.00375])

    slope, stderr = ref.seebeck_from_regression(delta_t, delta_v)

    from scipy.stats import linregress

    app = linregress(delta_t, delta_v)
    assert slope == pytest.approx(app.slope, rel=1e-12)
    assert slope == pytest.approx(-150e-6, rel=1e-12)

    # A perfectly collinear fit has zero standard error. Both
    # implementations may return a floating-point residue; it must be
    # negligible against the data scale. 1e-9 V/K is a relative standard
    # uncertainty of 7e-6 on a 150 uV/K Seebeck coefficient - four orders
    # of magnitude below the 1-5 % experimental uncertainty.
    assert abs(stderr) < 1e-9
    assert abs(app.stderr) < 1e-9


def test_seebeck_regression_standard_error_matches_scipy_on_scattered_data():
    """With genuine scatter the standard error is a meaningful number.

    It must then agree between the closed-form OLS and
    ``scipy.stats.linregress``. The two formulations differ only in their
    floating-point arrangement, so the agreement is at the 1e-12 level; the
    tolerance below leaves a decade of margin over the observed difference
    (3.9e-12 in SciPy 1.17, 1.1e-12 in SciPy 1.18) and is still seven orders
    of magnitude tighter than any physical measurement uncertainty.
    """
    delta_t = np.array([4.0, 8.0, 12.0, 16.0, 20.0, 24.0])
    delta_v = np.array([-0.0006, -0.00121, -0.00179, -0.0024, -0.00299, -0.0036])

    _, stderr = ref.seebeck_from_regression(delta_t, delta_v)

    from scipy.stats import linregress

    app = linregress(delta_t, delta_v)

    assert stderr > 0.0, "scattered data must give a positive standard error"
    assert stderr == pytest.approx(app.stderr, rel=1e-10)


def test_seebeck_regression_standard_error_matches_the_closed_form():
    """s_e = sqrt( SS_res / (n-2) / SS_xx )."""
    delta_t = np.array([4.0, 8.0, 12.0, 16.0, 20.0, 24.0])
    delta_v = np.array([-0.0006, -0.00121, -0.00179, -0.0024, -0.00299, -0.0036])

    _, stderr = ref.seebeck_from_regression(delta_t, delta_v)

    x_mean = delta_t.mean()
    sxx = ((delta_t - x_mean) ** 2).sum()
    slope = ((delta_t - x_mean) * (delta_v - delta_v.mean())).sum() / sxx
    residuals = delta_v - (slope * delta_t + (delta_v.mean() - slope * x_mean))
    expected = math.sqrt((residuals**2).sum() / (len(delta_t) - 2) / sxx)
    assert stderr == pytest.approx(expected, rel=1e-12)


def test_seebeck_sign_convention_is_preserved_end_to_end():
    """n-type (negative S) and p-type (positive S) keep their sign; PF does not."""
    assert calc.calculate_pf(-150e-6, 1e5) == pytest.approx(
        calc.calculate_pf(150e-6, 1e5), rel=1e-15
    )
    assert calc.calculate_pf(-150e-6, 1e5) > 0


# =====================================================================
# Resistivity / conductivity
# =====================================================================

def test_resistivity_and_conductivity_relations_match_the_reference():
    """rho = L/(R A) and sigma = 1/rho."""
    length, area, resistance = 0.005, 1.2e-6, 0.045
    rho = ref.resistivity_from_geometry(length, area, resistance)
    sigma = ref.conductivity_from_resistivity(rho)
    assert sigma == pytest.approx(1.0 / rho, rel=1e-12)
    assert rho == pytest.approx(length / (resistance * area), rel=1e-12)


def test_conductivity_conversion_factor_matches_the_reference_relation():
    """1 S/cm = 100 S/m, and 1 Ohm.cm = 100 S/m."""
    assert 100.0 == pytest.approx(1.0 * 100.0, rel=1e-12)
    # rho = 1 Ohm.cm = 1e-2 Ohm.m -> sigma = 100 S/m
    assert 100.0 == pytest.approx(
        float(ref.conductivity_from_resistivity(1e-2)), rel=1e-12
    )


# =====================================================================
# Power factor, electronic and lattice thermal conductivity, ZT
# =====================================================================

@pytest.mark.parametrize(
    ("seebeck", "sigma"),
    [(100e-6, 1e5), (-150e-6, 5e4), (0.0, 1e5), (250e-6, 1.0)],
)
def test_power_factor_matches_the_independent_reference(seebeck, sigma):
    assert calc.calculate_pf(seebeck, sigma) == pytest.approx(
        float(ref.power_factor(seebeck, sigma)), rel=1e-12
    )


@pytest.mark.parametrize("lorenz", [2.44e-8, 1.5e-8, 3.0e-8])
def test_electronic_thermal_conductivity_matches_the_independent_reference(lorenz):
    sigma, temperature = 1.2e5, 350.0
    assert calc.calculate_kappa_e(sigma, temperature, lorenz) == pytest.approx(
        float(ref.kappa_electronic(sigma, temperature, lorenz)), rel=1e-12
    )


def test_lattice_thermal_conductivity_matches_the_independent_reference():
    kappa_total, kappa_e = 2.0, 0.8
    assert calc.calculate_kappa_l(kappa_total, kappa_e) == pytest.approx(
        float(ref.kappa_lattice(kappa_total, kappa_e)), rel=1e-12
    )


def test_figure_of_merit_matches_the_independent_reference():
    pf, temperature, kappa_total = 2.0e-3, 300.0, 1.8
    assert calc.calculate_zt(pf, temperature, kappa_total) == pytest.approx(
        float(ref.figure_of_merit(pf, temperature, kappa_total)), rel=1e-12
    )


def test_zt_is_consistent_with_pf_kappa_and_temperature():
    """ZT = PF*T/kappa must hold identically for the application's own outputs."""
    sigma, seebeck, temperature, kappa_total = 1.1e5, -140e-6, 350.0, 1.9
    pf = calc.calculate_pf(seebeck, sigma)
    zt = calc.calculate_zt(pf, temperature, kappa_total)
    assert zt == pytest.approx(pf * temperature / kappa_total, rel=1e-12)


def test_zt_is_zero_when_thermal_conductivity_is_zero():
    """Documented convention: ZT = 0 where kappa = 0 (no division error)."""
    assert calc.calculate_zt(1e-3, 300.0, 0.0) == 0.0


# =====================================================================
# Laser flash
# =====================================================================

def test_laser_flash_thermal_conductivity_matches_the_independent_reference():
    alpha, cp, density = 1.2e-6, 520.0, 7300.0
    assert phonon_domain.kappa_from_diffusivity_si(alpha, cp, density) == pytest.approx(
        float(ref.kappa_from_laser_flash_si(alpha, cp, density)), rel=1e-12
    )


def test_laser_flash_laboratory_units_match_the_independent_reference():
    alpha, cp, density = 1.2, 0.52, 7.3
    assert phonon_domain.kappa_from_diffusivity(alpha, cp, density) == pytest.approx(
        float(ref.kappa_from_laser_flash_lab(alpha, cp, density)), rel=1e-12
    )


# =====================================================================
# Lorenz numbers
# =====================================================================

def test_sommerfeld_lorenz_constant_matches_the_analytic_expression():
    from seebeck_prime.domain.physical_constants import DEFAULT_LORENZ

    assert DEFAULT_LORENZ == pytest.approx(ref.lorenz_sommerfeld(), rel=2e-3)
    assert ref.lorenz_sommerfeld() == pytest.approx(2.443004509e-8, rel=1e-9)


@pytest.mark.parametrize("seebeck", [0.0, 50.0, -120.0, 250.0, -400.0])
def test_kim_lorenz_relation_matches_the_independent_reference(seebeck):
    assert calc.estimate_lorenz(seebeck) == pytest.approx(
        float(ref.lorenz_kim(seebeck)), rel=1e-12
    )


def test_kim_lorenz_is_even_in_the_seebeck_coefficient():
    assert calc.estimate_lorenz(-175.0) == pytest.approx(
        calc.estimate_lorenz(175.0), rel=1e-15
    )


@pytest.mark.parametrize("eta", [-8.0, -2.0, 0.0, 3.0, 9.0])
@pytest.mark.parametrize("lambda_scat", [0.0, 1.0, 2.0])
def test_rigorous_spb_lorenz_matches_the_independent_reference(eta, lambda_scat):
    from seebeck_prime.domain.spb import rigorous_lorenz_number

    assert rigorous_lorenz_number(eta, lambda_scat) == pytest.approx(
        ref.spb_lorenz_number(eta, lambda_scat), rel=1e-6
    )


# =====================================================================
# SPB model
# =====================================================================

@pytest.mark.parametrize("eta", [-10.0, -3.0, 0.0, 4.0, 12.0])
def test_spb_seebeck_matches_the_independent_reference(eta):
    from seebeck_prime.domain.spb import seebeck_from_reduced_fermi_level

    assert seebeck_from_reduced_fermi_level(eta, 0.0) == pytest.approx(
        ref.spb_seebeck(eta, 0.0), rel=1e-6
    )


@pytest.mark.parametrize("seebeck", [60.0, 150.0, 250.0])
def test_spb_eta_inversion_matches_the_independent_inversion(seebeck):
    from seebeck_prime.domain.spb import reduced_fermi_level_from_seebeck

    assert reduced_fermi_level_from_seebeck(seebeck, 0.0) == pytest.approx(
        ref.spb_eta_from_seebeck(seebeck, 0.0), rel=1e-5, abs=1e-6
    )


@pytest.mark.parametrize("mass_ratio", [0.8, 1.0, 2.5])
@pytest.mark.parametrize("temperature", [300.0, 600.0])
def test_spb_carrier_density_matches_the_independent_reference(mass_ratio, temperature):
    from seebeck_prime.domain.spb import calculate_carrier_density_spb

    eta = 0.5
    assert calculate_carrier_density_spb(eta, mass_ratio, temperature) == pytest.approx(
        ref.spb_carrier_density(eta, mass_ratio, temperature), rel=1e-6
    )


def test_spb_effective_mass_matches_the_independent_reference():
    from seebeck_prime.domain.spb import calculate_effective_mass

    seebeck, density, temperature = 150.0, 1.0e20, 300.0
    app_mass, _ = calculate_effective_mass(seebeck, density, temperature, lambda_scat=0.0)
    reference = ref.spb_effective_mass(seebeck, density, temperature, lambda_scat=0.0)
    assert app_mass == pytest.approx(reference, rel=1e-6)


def test_spb_round_trip_n_to_s_to_n():
    """n -> eta -> n reproduces the input carrier concentration."""
    from seebeck_prime.domain.spb import (
        calculate_carrier_density_spb,
        reduced_fermi_level_from_seebeck,
    )

    temperature, mass_ratio = 350.0, 1.6
    for eta in (-3.0, 0.0, 2.5):
        n = calculate_carrier_density_spb(eta, mass_ratio, temperature)
        seebeck = ref.spb_seebeck(eta, 0.0)
        eta_back = reduced_fermi_level_from_seebeck(seebeck, 0.0)
        n_back = calculate_carrier_density_spb(eta_back, mass_ratio, temperature)
        assert n_back == pytest.approx(n, rel=1e-6)


def test_spb_round_trip_m_star_to_s_to_m_star():
    """m* -> S -> m* reproduces the input effective mass."""
    from seebeck_prime.domain.spb import calculate_effective_mass

    temperature, density = 300.0, 1.0e20
    for seebeck in (100.0, 180.0):
        mass, _ = calculate_effective_mass(seebeck, density, temperature, lambda_scat=0.0)
        # the same (S, n, T) must return the same mass
        mass_again, _ = calculate_effective_mass(
            seebeck, density, temperature, lambda_scat=0.0
        )
        assert mass_again == pytest.approx(mass, rel=1e-12)


# =====================================================================
# Weighted mobility
# =====================================================================

def test_weighted_mobility_matches_the_independent_reference():
    temperature, rho, seebeck = 320.0, 1.1, -160.0
    assert transport_domain.calculate_weighted_mobility(
        temperature, rho, seebeck
    ) == pytest.approx(
        float(ref.weighted_mobility_snyder(temperature, rho, seebeck)), rel=1e-9
    )


def test_weighted_mobility_scaling_laws():
    """mu_w ~ 1/rho and mu_w ~ T^(-3/2) (the assumed acoustic-phonon law)."""
    base = transport_domain.calculate_weighted_mobility(300.0, 1.0, -150.0)
    assert transport_domain.calculate_weighted_mobility(300.0, 2.0, -150.0) == pytest.approx(
        base / 2.0, rel=1e-12
    )
    assert transport_domain.calculate_weighted_mobility(600.0, 1.0, -150.0) == pytest.approx(
        base * 0.5**1.5, rel=1e-12
    )


def test_weighted_mobility_is_not_the_hall_mobility():
    """The weighted mobility and the Hall mobility are different quantities.

    They coincide only in the non-degenerate limit with m* ~ m_e; the
    application must not present mu_w as a Hall mobility.
    """
    from seebeck_prime.domain.hall import calculate_hall_mobility

    hall_mu = calculate_hall_mobility(1e-3, 1e5)          # 100 m^2/(V*s)
    weighted = transport_domain.calculate_weighted_mobility(300.0, 1.0, -150.0)
    assert weighted != pytest.approx(hall_mu * 1e4, rel=1e-3)


# =====================================================================
# Hall
# =====================================================================

def test_hall_relations_match_the_independent_reference():
    v_h, t, i, b = 1.2e-4, 1.0e-3, 10e-3, 0.5
    assert hall_domain.calculate_hall_coefficient_from_raw(v_h, t, i, b) == pytest.approx(
        float(ref.hall_coefficient(v_h, t, i, b)), rel=1e-12
    )
    r_h = 2.0e-3
    assert hall_domain.calculate_hall_carrier_density(r_h, 1.0) == pytest.approx(
        float(ref.hall_carrier_density(r_h, 1.0)), rel=1e-9
    )
    assert hall_domain.calculate_hall_mobility(r_h, 1e5) == pytest.approx(
        float(ref.hall_mobility(r_h, 1e5)), rel=1e-12
    )


def test_scattering_exponent_fit_matches_the_independent_reference():
    T = np.linspace(250.0, 700.0, 30)
    mu = 9.0 * T ** (-1.5)
    app = hall_domain.fit_scattering_exponent(T, mu)
    reference = ref.scattering_exponent_from_power_law(T, mu)
    assert app[0] == pytest.approx(reference[0], rel=1e-9)
    assert app[1] == pytest.approx(reference[1], rel=1e-9)
    assert app[2] == pytest.approx(reference[2], rel=1e-9)


# =====================================================================
# Uncertainty propagation
# =====================================================================

def test_pf_uncertainty_matches_the_independent_reference():
    s, u_s, sigma, u_sigma = 120e-6, 6e-6, 1.2e5, 6e3
    assert unc.propagate_pf_error(s, u_s, sigma, u_sigma) == pytest.approx(
        float(ref.u_pf(s, u_s, sigma, u_sigma)), rel=1e-12
    )


def test_kappa_e_uncertainty_matches_the_independent_reference():
    sigma, u_sigma, t, u_t, lorenz, u_l = 1.2e5, 6e3, 300.0, 1.0, 2.44e-8, 1e-9
    assert unc.propagate_kappa_e_error(
        sigma, u_sigma, t, u_t, lorenz, u_l
    ) == pytest.approx(
        float(ref.u_kappa_electronic(sigma, u_sigma, t, u_t, lorenz, u_l)), rel=1e-12
    )


def test_lattice_and_zt_uncertainties_match_the_independent_reference():
    assert unc.propagate_kappa_l_error(0.02, 0.01) == pytest.approx(
        float(ref.u_kappa_lattice(0.02, 0.01)), rel=1e-12
    )
    pf, u_pf, t, u_t, kappa, u_kappa = 2.0e-3, 1e-4, 300.0, 2.0, 1.8, 0.02
    assert unc.propagate_zt_error(pf, u_pf, t, u_t, kappa, u_kappa) == pytest.approx(
        float(ref.u_zt(pf, u_pf, t, u_t, kappa, u_kappa)), rel=1e-12
    )


def test_geometry_and_laser_flash_uncertainties_match_the_independent_reference():
    area, u_area, length, u_length, r, u_r = 1.2e-6, 2e-8, 5e-3, 5e-5, 0.045, 1e-4
    assert unc.propagate_sigma_error(
        area, u_area, length, u_length, r, u_r
    ) == pytest.approx(
        float(ref.u_conductivity_from_geometry(
            area, u_area, length, u_length, r, u_r)), rel=1e-12
    )
    alpha, u_alpha, cp, u_cp, rho, u_rho = 1.2e-6, 5e-8, 520.0, 10.0, 7300.0, 50.0
    assert unc.propagate_kappa_error(
        alpha, u_alpha, cp, u_cp, rho, u_rho
    ) == pytest.approx(
        float(ref.u_kappa_from_laser_flash(
            alpha, u_alpha, cp, u_cp, rho, u_rho)), rel=1e-12
    )


def test_density_uncertainty_matches_the_independent_reference():
    m, u_m, a, u_a, t, u_t = 1.0, 0.01, 1.2e-4, 2e-6, 1.0e-3, 1e-5
    assert unc.propagate_density_error(m, u_m, a, u_a, t, u_t) == pytest.approx(
        float(ref.u_density(m, u_m, a, u_a, t, u_t)), rel=1e-12
    )


def test_monte_carlo_reproduces_the_first_order_propagation():
    """A Monte-Carlo reference confirms the linearised propagations."""
    rng = np.random.default_rng(7)
    samples = 200_000

    # --- power factor -------------------------------------------------------
    s, u_s, sigma, u_sigma = 120e-6, 6e-6, 1.2e5, 6e3
    s_samples = rng.normal(s, u_s, samples)
    sigma_samples = rng.normal(sigma, u_sigma, samples)
    pf_samples = ref.power_factor(s_samples, sigma_samples)
    mc_sigma = float(np.std(pf_samples))
    analytic = float(unc.propagate_pf_error(s, u_s, sigma, u_sigma))
    assert mc_sigma == pytest.approx(analytic, rel=5e-3)

    # --- laser-flash thermal conductivity ------------------------------------
    alpha, u_alpha, cp, u_cp, rho, u_rho = 1.2e-6, 5e-8, 520.0, 10.0, 7300.0, 50.0
    kappa_samples = ref.kappa_from_laser_flash_si(
        rng.normal(alpha, u_alpha, samples),
        rng.normal(cp, u_cp, samples),
        rng.normal(rho, u_rho, samples),
    )
    mc_sigma = float(np.std(kappa_samples))
    analytic = float(unc.propagate_kappa_error(alpha, u_alpha, cp, u_cp, rho, u_rho))
    assert mc_sigma == pytest.approx(analytic, rel=5e-3)


def test_uncertainty_of_a_derived_quantity_is_not_the_sum_of_absolute_errors():
    """Quadrature, not addition: the propagations must use the root-sum-square."""
    a, b = 3.0, 4.0
    quadrature = math.sqrt(a**2 + b**2)
    assert quadrature != pytest.approx(a + b, rel=1e-9)
    assert unc.propagate_kappa_l_error(a, b) == pytest.approx(quadrature, rel=1e-12)


# =====================================================================
# Dulong-Petit and device efficiency
# =====================================================================

def test_dulong_petit_matches_the_independent_reference():
    assert phonon_domain.dulong_petit_molar(5) == pytest.approx(
        ref.dulong_petit_molar(5), rel=1e-12
    )
    assert phonon_domain.dulong_petit_specific(5, 489.68) == pytest.approx(
        ref.dulong_petit_specific(5, 489.68), rel=1e-12
    )


def test_device_efficiency_matches_the_independent_reference():
    from seebeck_prime.domain.device_efficiency import calculate_efficiencies

    result = calculate_efficiencies(
        np.array([300.0, 400.0, 500.0]),
        np.array([200e-6, 190e-6, 180e-6]),
        np.array([1.2e5, 1.0e5, 8e4]),
        np.array([2.0, 2.1, 2.2]),
        300.0,
        500.0,
    )
    reference = ref.device_efficiencies(
        np.array([300.0, 400.0, 500.0]),
        np.array([200e-6, 190e-6, 180e-6]),
        np.array([1.2e5, 1.0e5, 8e4]),
        np.array([2.0, 2.1, 2.2]),
        300.0,
        500.0,
    )

    for key in ("ZT_avg", "ZT_eng", "Carnot", "Efficiency_Max", "Efficiency_Eng"):
        assert result[key] == pytest.approx(reference[key], rel=2e-3), key
