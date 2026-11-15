"""Generate validation/remediation/EQUATION_STATUS_MAPPING.csv.

The CSV is the deliverable; this generator exists so that the file is
reproducible and so that the mapping is reviewable in one place.

    python tools/generate_equation_status_mapping.py

The mapping is checked by
``tests/scientific/test_equation_status_mapping.py``, which verifies that

* the mapping covers exactly the registry's E-01..E-62 (no gaps, no extras);
* every implementation path and every test path exists on disk;
* every named independent-reference function exists in the reference module;
* the category counts match those declared in
  ``validation/remediation/VALIDATION_STATUS.md``.
"""

from __future__ import annotations

import csv
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "remediation" / "EQUATION_STATUS_MAPPING.csv"

COLUMNS = [
    "equation_id",
    "equation_name",
    "registry_section",
    "implementation_file",
    "implementation_function",
    "test_files",
    "independent_reference",
    "numerical_validation_status",
    "physical_applicability_status",
    "experimental_validation_status",
    "validation_category",
    "remaining_limitation",
]

C1 = "1 - Numerically verified"
C2 = "2 - Numerically verified but physically conditional"
C3 = "3 - Experimentally benchmarked within a defined scope"
C4 = "4 - Not yet validated"

SCI = "tests/scientific/test_independent_references.py"
EDGE = "tests/scientific/test_numerical_edge_cases.py"
PHYS = "tests/scientific/test_physical_constraints.py"
UNIT = "tests/scientific/test_unit_conversion_matrix.py"
BM = "tests/experimental_benchmarks/test_benchmarks.py"
WF = "tests/experimental_benchmarks/test_workflow_validation.py"
AL = "tests/experimental_benchmarks/test_auto_lorenz.py"
IMP = "tests/experimental_benchmarks/test_instrument_importers.py"
GDE = "tests/experimental_benchmarks/test_gui_end_to_end.py"

R: list[dict[str, str]] = []


def row(**kw):
    R.append({c: kw.get(c, "") for c in COLUMNS})


# ── 1. Core transport ──────────────────────────────────────────────────────
row(equation_id="E-01", equation_name="Power factor",
    registry_section="1 Core transport",
    implementation_file="src/domain/calculations.py",
    implementation_function="calculate_pf",
    test_files=f"{SCI}; tests/test_calculations.py; {BM}",
    independent_reference="references.power_factor",
    numerical_validation_status="VERIFIED - independent reference, rel <= 1e-12",
    physical_applicability_status="UNCONDITIONAL - PF = S^2*sigma is sign-independent",
    experimental_validation_status="BENCHMARKED - published PF, 4 specimens, max dev 1.26-3.79 %",
    validation_category=C3,
    remaining_limitation="None for the formula itself; the experimental scope is limited to the four benchmark specimens.")

row(equation_id="E-02", equation_name="Electronic thermal conductivity",
    registry_section="1 Core transport",
    implementation_file="src/domain/calculations.py",
    implementation_function="calculate_kappa_e",
    test_files=f"{SCI}; tests/test_calculations.py; {BM}",
    independent_reference="references.kappa_electronic",
    numerical_validation_status="VERIFIED - independent reference, rel <= 1e-12",
    physical_applicability_status="CONDITIONAL - Wiedemann-Franz law: constant L, elastic scattering, single band",
    experimental_validation_status="BENCHMARKED - published kappa_e, Si80Ge20P1 only",
    validation_category=C3,
    remaining_limitation="Inherits the Lorenz-number error. The kappa_L sensitivity to the constant L is 26.5 % (Bi2Te3) and 130.6 % (PbTe); the SPB acoustic deviation from the implied value is -3.6 % (Bi2Te3), +10 % .. +46 % (PbTe, implied value itself unreliable) and -25 % .. -38 % (Si80Ge20P1, scattering exponent ~1.41 - see validation/remediation/SIGE_LORENZ_INVESTIGATION.md).")

row(equation_id="E-03", equation_name="Lattice thermal conductivity",
    registry_section="1 Core transport",
    implementation_file="src/domain/calculations.py",
    implementation_function="calculate_kappa_l",
    test_files=f"{SCI}; tests/test_calculations.py; {PHYS}; {BM}",
    independent_reference="references.kappa_lattice",
    numerical_validation_status="VERIFIED - independent reference, rel <= 1e-12",
    physical_applicability_status="CONDITIONAL - valid only below the bipolar onset and with a correct L",
    experimental_validation_status="BENCHMARKED - published kappa_L, Si80Ge20P1, <= 0.7 % with the a-priori constant",
    validation_category=C3,
    remaining_limitation="The negative-kappa_L diagnostic exists in domain/validation.py but has NO production caller - it never reaches the user (audit D-01). The registry previously claimed 'negative-result flagging VERIFIED'; that claim is withdrawn.")

row(equation_id="E-04", equation_name="Figure of merit",
    registry_section="1 Core transport",
    implementation_file="src/domain/calculations.py",
    implementation_function="calculate_zt",
    test_files=f"{SCI}; tests/test_calculations.py; {BM}",
    independent_reference="references.figure_of_merit",
    numerical_validation_status="VERIFIED - independent reference, rel <= 1e-12; ZT = 0 where kappa = 0 (guarded division)",
    physical_applicability_status="CONDITIONAL - requires coincident T and a correct kappa_total",
    experimental_validation_status="BENCHMARKED - published ZT, 4 specimens, max dev 1.26-5.93 %",
    validation_category=C3,
    remaining_limitation="ZT = 0 for kappa_total = 0 is a defensive convention, not the physical limit (ZT -> infinity).")

row(equation_id="E-05", equation_name="Empirical (Kim) Lorenz number",
    registry_section="1 Core transport",
    implementation_file="src/domain/calculations.py",
    implementation_function="estimate_lorenz",
    test_files=f"{AL}; {SCI}; tests/test_calculations.py",
    independent_reference="references.lorenz_kim",
    numerical_validation_status="VERIFIED - independent reference, rel <= 1e-12; even in S; limits 2.5e-8 and 1.5e-8",
    physical_applicability_status="CONDITIONAL - acoustic-phonon scattering only (+2.8 % at |S|=150 uV/K); -21.7 % optical/alloy, -31.8 % ionised impurity",
    experimental_validation_status="NONE - the published data contradict the acoustic model it approximates (see E-06)",
    validation_category=C2,
    remaining_limitation="Must not be described as a universal Lorenz number; the input unit must be uV/K.")

row(equation_id="E-06", equation_name="Rigorous SPB Lorenz number",
    registry_section="1 Core transport",
    implementation_file="src/domain/spb.py",
    implementation_function="rigorous_lorenz_number",
    test_files=f"{AL}; {SCI}; {EDGE}; tests/test_spb_models.py",
    independent_reference="references.spb_lorenz_number",
    numerical_validation_status="VERIFIED - independent Blatt-normalised quadrature, worst rel 1.4e-14 over lambda = 0,1,2; analytic limits L0 and (lambda+2)(k_B/e)^2",
    physical_applicability_status="CONDITIONAL - single parabolic band, scattering exponent lambda",
    experimental_validation_status="CONTRADICTED for Si80Ge20P1 - the published data imply 2.4579e-8 (Sommerfeld) against 1.592e-8 from this model (-35 %)",
    validation_category=C2,
    remaining_limitation="Open negative result (audit M-04): the cause is not yet discriminated between scattering assumption, single-band failure and published-pair inconsistency. The model must NOT be changed to match the measurement.")

row(equation_id="E-07", equation_name="Chemical formula mass and Dulong-Petit limit",
    registry_section="1 Core transport",
    implementation_file="src/domain/calculations.py; src/domain/phonon.py",
    implementation_function="calculate_molecular_weight; calculate_legacy_molecular_weight; calculate_dulong_petit_limit; dulong_petit_molar; dulong_petit_specific",
    test_files=f"{SCI}; tests/test_calculations.py; tests/test_phonon_lfa.py",
    independent_reference="references.dulong_petit_molar; references.dulong_petit_specific",
    numerical_validation_status="VERIFIED - independent reference, rel <= 1e-12; unsupported formula syntax is rejected (SE-002)",
    physical_applicability_status="CONDITIONAL - the Dulong-Petit limit is a high-temperature classical limit",
    experimental_validation_status="NONE - no published Dulong-Petit reference used",
    validation_category=C2,
    remaining_limitation="The formula parser accepts only unbracketed Element[Count] syntax; fractional stoichiometry and parentheses are rejected, not mis-parsed.")

# ── 2. Uncertainty propagation ──────────────────────────────────────────────
for eid, name, fn, ref_fn, extra in (
    ("E-08", "Power-factor uncertainty", "propagate_pf_error", "references.u_pf",
     "cross-checked against a 200k-sample Monte-Carlo reference (rel <= 5e-3)"),
    ("E-09", "Electronic thermal-conductivity uncertainty", "propagate_kappa_e_error", "references.u_kappa_electronic",
     "includes the Lorenz term; cross-checked against Monte-Carlo where applicable"),
    ("E-10", "Lattice thermal-conductivity uncertainty", "propagate_kappa_l_error", "references.u_kappa_lattice", ""),
    ("E-11", "Figure-of-merit uncertainty", "propagate_zt_error", "references.u_zt", ""),
    ("E-13", "Laser-flash thermal-conductivity uncertainty", "propagate_kappa_error", "references.u_kappa_from_laser_flash",
     "cross-checked against a 200k-sample Monte-Carlo reference (rel <= 5e-3)"),
    ("E-14", "Density uncertainty", "propagate_density_error", "references.u_density", ""),
):
    row(equation_id=eid, equation_name=name,
        registry_section="2 Uncertainty propagation",
        implementation_file="src/domain/uncertainty.py",
        implementation_function=fn,
        test_files=f"{SCI}; tests/test_uncertainty.py; {EDGE}",
        independent_reference=ref_fn,
        numerical_validation_status="VERIFIED - independent reference, rel <= 1e-12" + (f"; {extra}" if extra else ""),
        physical_applicability_status="UNCONDITIONAL - the propagation rule does not depend on the material; the independence of inputs is a statistical assumption recorded in remaining_limitation",
        experimental_validation_status="NONE - no published uncertainty comparison",
        validation_category=C1,
        remaining_limitation="Independence assumption is undocumented in the UI; no covariance input is supported (audit Phase 4 item).")

row(equation_id="E-12", equation_name="Conductivity uncertainty from geometry",
    registry_section="2 Uncertainty propagation",
    implementation_file="src/domain/uncertainty.py",
    implementation_function="propagate_sigma_error",
    test_files=f"{SCI}; tests/test_uncertainty.py",
    independent_reference="references.u_conductivity_from_geometry",
    numerical_validation_status="VERIFIED - independent reference, rel <= 1e-12",
    physical_applicability_status="CONDITIONAL - the propagator presupposes sigma = L/(R*A) for a rectangular specimen with uniform current",
    experimental_validation_status="NONE",
    validation_category=C2,
    remaining_limitation="NOT called by any production path (audit D-09). The live application uses application/measurement_processing.py::combine_sigma_uncertainty, a second implementation of the same physics.")

row(equation_id="E-15", equation_name="Relative-uncertainty combiner",
    registry_section="2 Uncertainty propagation",
    implementation_file="src/domain/uncertainty.py",
    implementation_function="propagate_relative_uncertainty",
    test_files="tests/test_scientific_equations_audit.py",
    independent_reference="(covered by references.u_pf and references.u_zt, which use the same root-sum-square form)",
    numerical_validation_status="VERIFIED - root-sum-square form asserted explicitly in tests/scientific",
    physical_applicability_status="CONDITIONAL - independent contributions only",
    experimental_validation_status="NONE",
    validation_category=C1,
    remaining_limitation="No independent reference function is dedicated to it; covered indirectly through the propagators above.")

# ── 3. Units ────────────────────────────────────────────────────────────────
UNITS = [
    ("E-16", "Temperature conversion", "to_kelvin; from_kelvin",
     "(no dedicated function; covered by the temperature round trips asserted in tests/scientific/test_unit_conversion_matrix.py)",
     "VERIFIED - round trip rel <= 1e-12; offset 273.15 exact; uncertainty invariant under the offset",
     "UNCONDITIONAL", "NONE", C1,
     "None."),
    ("E-17", "Electrical-conductivity conversion", "sigma_to_sm; sigma_from_sm",
     "references.conductivity_from_resistivity (relation 1 S/cm = 100 S/m)",
     "VERIFIED - round trip rel <= 1e-12; exact factors 100 and 100/rho",
     "UNCONDITIONAL", "NONE", C1,
     "None."),
    ("E-18", "Seebeck-coefficient conversion", "seebeck_to_vk; seebeck_from_vk",
     "references (S[V/K] = S[uV/K]*1e-6)",
     "VERIFIED - round trip rel <= 1e-12 for all spellings (V/K, uV/K, mV/K, micro variants)",
     "UNCONDITIONAL", "NONE", C1,
     "None."),
    ("E-19", "Power-factor conversion", "pf_to_si; pf_from_si",
     "references.power_factor",
     "VERIFIED - round trip rel <= 1e-12 for all spellings (W/(m*K^2), mW, uW variants)",
     "UNCONDITIONAL", "NONE", C1,
     "None."),
    ("E-20", "Carrier-concentration conversion", "carrier_density_m3_to_cm3; carrier_density_cm3_to_m3",
     "references.spb_carrier_density (cm^-3 output)",
     "VERIFIED - exact 1e-6/1e6 factors, rel <= 1e-12",
     "UNCONDITIONAL", "BENCHMARKED (unit interpretation) - published n in m^-3 confirmed via mu = sigma/(n e), median ratio 1.08",
     C1, "None."),
    ("E-21", "Uncertainty conversions", "uncertainty_to_base; uncertainty_from_base (application/unit_conversion.py)",
     "references (inverse-of-value-conversion assertion)",
     "VERIFIED - linear for S and PF; u_sigma = u_rho*100/rho^2 for Ohm-cm; inverse of the value conversion",
     "UNCONDITIONAL", "NONE", C1,
     "The thermal-conductivity branch falls through to the identity, which is correct because only W/(m*K) is supported."),
]
for eid, name, fn, ref_fn, num, phys, exp, cat, lim in UNITS:
    row(equation_id=eid, equation_name=name,
        registry_section="3 Units",
        implementation_file="src/domain/units.py; src/application/unit_conversion.py",
        implementation_function=fn,
        test_files=f"{UNIT}; tests/test_units.py; tests/test_unit_converter.py",
        independent_reference=ref_fn,
        numerical_validation_status=num,
        physical_applicability_status=phys,
        experimental_validation_status=exp,
        validation_category=cat,
        remaining_limitation=lim)

row(equation_id="E-22", equation_name="Thermal-conductivity conversion",
    registry_section="3 Units",
    implementation_file="src/domain/units.py",
    implementation_function="kappa_to_si; kappa_from_si",
    test_files=f"{UNIT}; tests/test_units.py",
    independent_reference="references.kappa_from_laser_flash_si (SI normalisation)",
    numerical_validation_status="VERIFIED - identity for the supported spellings; unsupported units raise ValueError (SE-042 regression test)",
    physical_applicability_status="SCOPE-LIMITED - only W/(m*K) is supported",
    experimental_validation_status="NONE",
    validation_category=C2,
    remaining_limitation="W/(cm*K) is not implemented (audit SE-021). The converter now rejects it rather than silently mis-scaling it.")

# ── 4. SPB model ────────────────────────────────────────────────────────────
SPB = [
    ("E-23", "Fermi-Dirac integral", "fermi_integral", "references.fermi_integral_unnormalised; references.fermi_integral_blatt",
     "VERIFIED - independent quadrature rel <= 1e-8; F_0 = ln(1+e^eta) analytic identity to 1e-12; branch switches continuous to 5e-3",
     "UNCONDITIONAL - a mathematical function", "NONE", C1,
     "The eta < -30 Boltzmann and eta > 50 Sommerfeld branches are documented approximations, not machine precision."),
    ("E-24", "Seebeck coefficient versus reduced Fermi level", "seebeck_from_reduced_fermi_level", "references.spb_seebeck",
     "VERIFIED - independent reference rel <= 1.5e-14; Boltzmann limit (k_B/e)(lambda+2-eta) to 4.7e-11; degenerate limit S -> 0",
     "CONDITIONAL - single parabolic band, scattering exponent lambda = r + 1/2", "NONE", C2,
     "The unnormalised-integral convention is correct but is not stated in the function docstring; see audit item 3.6."),
    ("E-25", "Reduced Fermi level from Seebeck coefficient", "reduced_fermi_level_from_seebeck", "references.spb_eta_from_seebeck",
     "VERIFIED - independent inversion rel <= 2.7e-6; bracket-independent; unbracketable input returns NaN; metallic limit saturates at eta = 50",
     "CONDITIONAL - inherits the single-band assumption", "NONE", C2,
     "The metallic-limit saturation value (eta = 50) is a documented convention, not a computed result."),
    ("E-26", "SPB carrier concentration", "calculate_carrier_density_spb", "references.spb_carrier_density",
     "VERIFIED - textbook n to 1.5e-14; the internal constant carries the 1/Gamma(3/2) factor required by the unnormalised convention",
     "CONDITIONAL - single parabolic band; N_c proportional to T^(3/2)", "NONE - the benchmark uses the published n to invert m* and then recovers n, which is a self-consistency round trip, not an independent comparison",
     C2, "No independent experimental comparison of the application's n against a published n for the same specimen."),
    ("E-27", "SPB effective mass", "calculate_effective_mass", "references.spb_effective_mass",
     "VERIFIED - independent reference rel <= 1.6e-8; units cm^-3 / K handled explicitly",
     "CONDITIONAL - inherits the assumed scattering exponent", "NONE - plausibility only: 1.49-2.23 m_e (median 1.70 m_e) for P-doped SiGe",
     C2, "No publication states an effective mass that can be cross-checked (DOI 10.1021/acsami.9b20090 abstract gives none; full text not openly available). Do not claim experimental verification."),
    ("E-28", "Pisarenko curve and optimal transport", "generate_pisarenko_curve; predict_optimal_transport", "(no dedicated reference; structure and monotonicity asserted)",
     "VERIFIED - structure, monotonicity and range assertions only",
     "CONDITIONAL - single parabolic band with an acoustic-phonon mobility parameter mu_0", "NONE", C2,
     "No independent reference implementation exists for these two functions; coverage is structural only."),
    ("E-29", "Empirical carrier-concentration estimator", "calculate_carrier_concentration", "(no dedicated reference; the published expression is asserted in tests)",
     "VERIFIED - the published Snyder-Toberer fit is reproduced exactly",
     "CONDITIONAL - empirical fit in |S| only, no temperature dependence", "NONE", C2,
     "A fast estimator kept for compatibility; it is not an SPB result and must not be confused with E-26."),
]
for eid, name, fn, ref_fn, num, phys, exp, cat, lim in SPB:
    row(equation_id=eid, equation_name=name,
        registry_section="4 SPB model",
        implementation_file="src/domain/spb.py",
        implementation_function=fn,
        test_files=f"{SCI}; tests/test_spb_models.py; {AL}",
        independent_reference=ref_fn,
        numerical_validation_status=num,
        physical_applicability_status=phys,
        experimental_validation_status=exp,
        validation_category=cat,
        remaining_limitation=lim)

# ── 5. Hall ─────────────────────────────────────────────────────────────────
HALL = [
    ("E-30", "Hall coefficient", "calculate_hall_coefficient_from_raw", "references.hall_coefficient",
     "VERIFIED - independent reference rel <= 1e-12", "CONDITIONAL - single-carrier, flat sample, uniform current",
     "NONE", C2, "No experimental benchmark for the application's Hall path."),
    ("E-31", "Hall carrier density", "calculate_hall_carrier_density", "references.hall_carrier_density",
     "VERIFIED - independent reference rel <= 1e-12", "CONDITIONAL - Hall factor r_H = 1 assumed unless supplied",
     "NONE", C2, "The published carrier-concentration unit interpretation was confirmed independently, but the application's own n_H has no experimental comparison."),
    ("E-32", "Carrier type from the Hall sign", "determine_carrier_type", "references (sign convention asserted directly)",
     "VERIFIED - explicit sign convention test", "UNCONDITIONAL - a definition", "NONE", C1, "None."),
    ("E-33", "Hall mobility", "calculate_hall_mobility", "references.hall_mobility",
     "VERIFIED - independent reference rel <= 1e-12, including the 1e4 m^2/(V s) -> cm^2/(V s) relation",
     "CONDITIONAL - single-carrier, r_H = 1", "NONE", C2,
     "Must not be presented as the weighted mobility (E-39); the two are different physical quantities."),
    ("E-34", "Scattering-exponent fit", "fit_scattering_exponent", "references.scattering_exponent_from_power_law",
     "VERIFIED - independent reference rel <= 1e-9", "CONDITIONAL - assumes a single power law mu ~ T^p over the fitted range",
     "NONE", C2, "The fit quality (r^2) is returned but no goodness-of-fit threshold is enforced."),
]
for eid, name, fn, ref_fn, num, phys, exp, cat, lim in HALL:
    row(equation_id=eid, equation_name=name,
        registry_section="5 Hall",
        implementation_file="src/domain/hall.py",
        implementation_function=fn,
        test_files=f"{SCI}; tests/test_hall_models.py; {PHYS}",
        independent_reference=ref_fn,
        numerical_validation_status=num,
        physical_applicability_status=phys,
        experimental_validation_status=exp,
        validation_category=cat,
        remaining_limitation=lim)

# ── 6. Phonon ───────────────────────────────────────────────────────────────
row(equation_id="E-35", equation_name="Thermal conductivity from laser flash",
    registry_section="6 Phonon / laser flash",
    implementation_file="src/domain/phonon.py",
    implementation_function="kappa_from_diffusivity_si; kappa_from_diffusivity",
    test_files=f"{SCI}; tests/test_phonon_lfa.py; {IMP}",
    independent_reference="references.kappa_from_laser_flash_si; references.kappa_from_laser_flash_lab",
    numerical_validation_status="VERIFIED - independent reference rel <= 1e-12; the SI and laboratory-unit paths agree",
    physical_applicability_status="CONDITIONAL - assumes one-dimensional heat flow and a homogeneous specimen",
    experimental_validation_status="NONE - no published laser-flash result is used as a reference",
    validation_category=C2,
    remaining_limitation="The instrument file is a reconstruction from published curves, so this validates the parsing and the arithmetic, not the measurement.")

# ── 7. Device efficiency ────────────────────────────────────────────────────
DE = [
    ("E-36", "Average figure of merit", "ZT_avg = (1/dT) int ZT dT", "references.device_efficiencies",
     "VERIFIED - independent reference rel <= 1e-12 (Simpson on both sides)", "CONDITIONAL - interpolates the property grid onto [Tc, Th]",
     "NONE", C2, "A constant-property approximation over the active leg."),
    ("E-37", "Maximum (Ioffe) efficiency", "eta_max = (dT/Th)(sqrt(1+ZT)-1)/(sqrt(1+ZT)+Tc/Th)", "references.device_efficiencies",
     "VERIFIED - independent reference rel <= 1e-12", "CONDITIONAL - constant-property average ZT", "NONE", C2,
     "Same constant-property assumption as E-36."),
    ("E-38", "Engineering figure of merit", "ZT_eng = Sbar^2 Tbar / (rhobar kappabar)", "references.device_efficiencies",
     "VERIFIED - independent reference rel <= 1e-12, after the SE-001 dimensional correction", "CONDITIONAL - constant-property average", "NONE", C2,
     "The pre-correction implementation was dimensionally invalid; the current form is verified but still a constant-property approximation."),
]
for eid, name, fn, ref_fn, num, phys, exp, cat, lim in DE:
    row(equation_id=eid, equation_name=name,
        registry_section="7 Device efficiency",
        implementation_file="src/domain/device_efficiency.py",
        implementation_function="calculate_efficiencies",
        test_files=f"{SCI}; tests/test_device_efficiency_models.py; tests/test_transport_models.py",
        independent_reference=ref_fn,
        numerical_validation_status=num,
        physical_applicability_status=phys,
        experimental_validation_status=exp,
        validation_category=cat,
        remaining_limitation=lim)

# ── 8. Transport / analysis / validation ────────────────────────────────────
row(equation_id="E-39", equation_name="Weighted mobility",
    registry_section="8 Transport / analysis / validation",
    implementation_file="src/domain/transport.py",
    implementation_function="calculate_weighted_mobility",
    test_files=f"{SCI}; {WF}; {PHYS}; tests/test_transport_models.py",
    independent_reference="references.weighted_mobility_snyder",
    numerical_validation_status="VERIFIED - independent implementation rel <= 1e-9; scaling mu_w ~ 1/rho and mu_w ~ T^(-3/2) asserted",
    physical_applicability_status="CONDITIONAL - assumes acoustic-phonon transport and an effective mobility, NOT the Hall mobility",
    experimental_validation_status="NONE - the only published carrier-mobility curve in the benchmark set is negative and unusable",
    validation_category=C2,
    remaining_limitation="The formula is verified; the physics has no experimental reference. Never label weighted mobility as Hall mobility (E-33).")

row(equation_id="E-40", equation_name="Resistivity conversion to mohm.cm",
    registry_section="8 Transport / analysis / validation",
    implementation_file="src/domain/transport.py",
    implementation_function="resistivity_to_mohm_cm",
    test_files="tests/test_transport_models.py",
    independent_reference="(covered by references.resistivity_from_geometry and the unit-matrix conversions)",
    numerical_validation_status="VERIFIED - exact factors asserted in tests/test_transport_models.py",
    physical_applicability_status="UNCONDITIONAL",
    experimental_validation_status="NONE",
    validation_category=C1,
    remaining_limitation="An unknown unit falls through unchanged; unlike the domain converters this does not raise.")

row(equation_id="E-41", equation_name="Analysis helpers (MAD filter, OLS, interpolation, alignment)",
    registry_section="8 Transport / analysis / validation",
    implementation_file="src/domain/analysis.py",
    implementation_function="mad_filter; linear_regression; interpolate_onto; round_temperature; align_datasets",
    test_files="tests/test_analysis_tools.py; tests/test_scientific_equations_audit.py",
    independent_reference="references.seebeck_from_regression (OLS slope and standard error)",
    numerical_validation_status="VERIFIED - OLS slope and stderr against a closed form to 1e-12",
    physical_applicability_status="UNCONDITIONAL - numerical helpers",
    experimental_validation_status="NONE", validation_category=C1,
    remaining_limitation="MAD filtering and temperature rounding are analysis conventions, not physical models.")

row(equation_id="E-42", equation_name="Physical-constraint validators",
    registry_section="8 Transport / analysis / validation",
    implementation_file="src/domain/validation.py",
    implementation_function="validate_temperature_array; validate_conductivity_array; validate_seebeck_array; validate_kappa_array; validate_kappa_l_array; validate_dataset",
    test_files=f"{PHYS}; tests/test_validation_rules.py",
    independent_reference="(not applicable - the reference module asserts the same physical bounds directly)",
    numerical_validation_status="VERIFIED - messages, severities and field names asserted",
    physical_applicability_status="UNCONDITIONAL - the bounds are physical, not model-dependent",
    experimental_validation_status="NONE",
    validation_category=C1,
    remaining_limitation="REACHABILITY DEFECT: no production code calls validate_measurement_data/validate_dataset, so the negative-kappa_L warning never reaches the user (audit D-01). The registry previously claimed 'reachability VERIFIED'; that claim is withdrawn.")

# ── 9. Data-processing workflows ────────────────────────────────────────────
WORK = [
    ("E-43", "Property suite from measured inputs", "calculate_thermoelectric_properties",
     "src/application/use_cases.py", f"{SCI}; tests/test_use_cases.py; {AL}",
     "references.power_factor; references.kappa_electronic; references.kappa_lattice; references.figure_of_merit",
     "VERIFIED - every derived quantity matches the independent reference to 1e-12",
     "CONDITIONAL - inherits the Lorenz-number assumption of E-02", "NONE", C1,
     "Uncertainty outputs appear only when their inputs are supplied; see SE-035."),
    ("E-44", "Multi-sample preparation", "process_multi_sample_data; process_multi_sample_batch",
     "src/application/use_cases.py", f"{WF}; tests/test_batch_workflows.py; tests/test_author_decisions.py",
     "(delegates to the same domain references)",
     "VERIFIED - every derived quantity matches the independent reference to 1e-12",
     "CONDITIONAL - as E-43", "BENCHMARKED - published PF and ZT, 4 specimens, max dev 1.26-5.93 %",
     C3, "The report units are S/cm, uV/K and mW/(m*K^2) on both paths (author decision)."),
    ("E-45", "Four-probe import", "process_four_probe_table",
     "src/application/measurement_processing.py", f"{IMP}; tests/test_measurement_processing.py",
     "(not applicable - parsing, not a scientific relation)",
     "VERIFIED - column mapping, unit conversion, grouping, standard error of the mean, invalid rows",
     "CONDITIONAL - the temperature unit comes from the column header, with magnitude inference only as a fallback",
     "NONE - the instrument file is a RECONSTRUCTION from published curves, not a real instrument export",
     C1, "There is no raw V/I -> R -> rho -> sigma path (see E-58)."),
    ("E-46", "Raw Seebeck import", "process_raw_seebeck_table",
     "src/application/measurement_processing.py", f"{IMP}; tests/test_measurement_processing.py",
     "references.seebeck_from_regression (OLS slope and standard error)",
     "VERIFIED - regression slope and stderr to 1e-12; sign convention; grouping; invalid and duplicate rows",
     "CONDITIONAL - assumes a linear dV/dT response over the fitted range",
     "NONE - reconstruction, not an instrument export", C1,
     "A single-difference group is skipped rather than raising (SE-040)."),
    ("E-47", "Laser-flash import", "process_laser_flash_table",
     "src/application/measurement_processing.py", f"{IMP}; tests/test_measurement_processing.py",
     "references.kappa_from_laser_flash_si; references.kappa_from_laser_flash_lab",
     "VERIFIED - unit handling, missing and invalid fields",
     "CONDITIONAL - the temperature unit comes from the column header (SE-026/028 resolved)",
     "NONE - reconstruction, not an instrument export", C1,
     "Both the application and the presentation path now derive the unit from the header."),
    ("E-48", "Geometry uncertainty combination", "combine_sigma_uncertainty",
     "src/application/measurement_processing.py", f"{IMP}; tests/test_measurement_processing.py",
     "references.u_conductivity_from_geometry",
     "VERIFIED - independent formula, rel <= 1e-12",
     "CONDITIONAL - assumes independent geometry and resistance errors", "NONE", C1,
     "A second, live implementation of the geometry uncertainty (see E-12)."),
    ("E-49", "Reference-Seebeck uncertainty combination", "combine_seebeck_uncertainty",
     "src/application/measurement_processing.py", f"{IMP}; tests/test_measurement_processing.py",
     "(covered by references.seebeck_from_regression for the regression part)",
     "VERIFIED - independent formula", "CONDITIONAL - assumes independent reference and sample errors", "NONE", C1,
     "None."),
    ("E-50", "Column mapping with physical-plausibility guards", "find_column (and the alias matcher)",
     "src/application/data_mapping.py", "tests/test_application_layer_audit.py; tests/test_measurement_processing.py",
     "(not applicable - matching logic)",
     "VERIFIED - alias matching and the guards that reject 'Thermal Conductivity (W/mK)' for the conductivity slot (SE-031)",
     "UNCONDITIONAL", "NONE", C1, "None."),
    ("E-51", "SPB batch rows and mean parameters", "process_spb_batch (module spb_batch.py)",
     "src/application/spb_batch.py", "tests/test_batch_workflows.py",
     "(delegates to the same domain references)",
     "VERIFIED - per-row arithmetic matches the domain references to 1e-12",
     "CONDITIONAL - inherits the SPB single-band assumption", "NONE", C1,
     "The mean mass is taken over rows with a valid mass while the mean temperature covers all submitted rows (SE-034). Documented legacy rule, preserved and pinned by a test."),
    ("E-52", "Arrhenius activation-energy fits", "arrhenius_ln_sigma; arrhenius_ln_sigma_T; arrhenius_log10_sigma",
     "src/plugins/arrhenius.py", "tests/test_arrhenius_plugin.py",
     "references.seebeck_from_regression (linear-regression core)",
     "VERIFIED - the activation energy is recovered exactly from synthetic data with a known slope",
     "CONDITIONAL - assumes ln(sigma) or ln(sigma*T) is linear in 1/T over the fitted range", "NONE", C1,
     "The log10 variant applies the ln(10) factor explicitly; both are covered."),
]
for eid, name, fn, impl, tests, ref_fn, num, phys, exp, cat, lim in WORK:
    row(equation_id=eid, equation_name=name,
        registry_section="9 Data-processing workflows",
        implementation_file=impl,
        implementation_function=fn,
        test_files=tests,
        independent_reference=ref_fn,
        numerical_validation_status=num,
        physical_applicability_status=phys,
        experimental_validation_status=exp,
        validation_category=cat,
        remaining_limitation=lim)

# ── 10. GUI / presentation ──────────────────────────────────────────────────
GUI = [
    ("E-53", "Spreadsheet recalculation (file -> mapper -> table -> properties)", "recalculate_all_properties; load_data_into_table",
     "src/gui/main_window.py; src/presentation/table_handler.py",
     f"{GDE}; tests/experimental_benchmarks/gui_workflow_driver.py",
     "references (the derived quantities are the domain references)",
     "VERIFIED - headless end-to-end run reproduces the property table",
     "CONDITIONAL - inherits E-43", "NONE", C1,
     "Driven through a subprocess driver; the GUI subset is skipped in the conda base environment (Qt DLL) and passes in the Qt-capable venv."),
    ("E-54", "Display-unit rendering versus internal SI values", "to_base_value; from_base_value; _convert_to_base_unit; _convert_from_base_unit",
     "src/application/unit_conversion.py; src/presentation/unit_converter.py",
     f"{UNIT}; {GDE}", "references (the unit-matrix round trips)",
     "VERIFIED - for every supported unit, to_base(from_base(x)) == x to 1e-12",
     "UNCONDITIONAL", "NONE", C1,
     "The presentation column map uses the key 'Thermal Conductivity' while the combo registry uses 'Thermal Cond.'; the default is therefore always used for kappa. Harmless today because there is no kappa unit selector."),
    ("E-55", "Plot-data preparation (sorting, error alignment)", "get_plot_data / table_plot_data helpers",
     "src/presentation/table_plot_data.py; src/presentation/main_table_plots.py",
     "tests/test_plot_data.py; tests/test_architecture_dependencies.py",
     "(not applicable - data shaping)",
     "VERIFIED - ordering and error-bar alignment asserted", "UNCONDITIONAL", "NONE", C1,
     "The interactive plot window itself is covered only by the headless driver."),
]
for eid, name, fn, impl, tests, ref_fn, num, phys, exp, cat, lim in GUI:
    row(equation_id=eid, equation_name=name,
        registry_section="10 GUI / presentation",
        implementation_file=impl,
        implementation_function=fn,
        test_files=tests,
        independent_reference=ref_fn,
        numerical_validation_status=num,
        physical_applicability_status=phys,
        experimental_validation_status=exp,
        validation_category=cat,
        remaining_limitation=lim)

row(equation_id="E-56", equation_name="Interactive calculation dialogs",
    registry_section="10 GUI / presentation",
    implementation_file="src/presentation/dialogs/ (6 tools); src/gui/main_window.py (open_* methods)",
    implementation_function="KappaToolDialog; SPBModelingDialog; HallMobilityDialog; WeightedMobilityDialog; MultiSampleDialog; ErrorBarDialog",
    test_files="(none)",
    independent_reference="(not applicable - no calculation is exercised through the dialogs)",
    numerical_validation_status="NOT VERIFIED - no automated coverage of any dialog",
    physical_applicability_status="NOT APPLICABLE",
    experimental_validation_status="NONE",
    validation_category=C4,
    remaining_limitation="CORRECTED REASON: five of the six are opened with .show() (non-modal) and are therefore already QTest-driveable; only ErrorBarDialog (main_window.py:292) and PlotDataDialog (:779) use modal .exec(). The registry previously said 'modal' for all six.")

row(equation_id="E-57", equation_name="Clipboard paste, menus and plot export",
    registry_section="10 GUI / presentation",
    implementation_file="src/gui/main_window.py; src/gui/file_commands.py; src/presentation/plot_window.py",
    implementation_function="(interactive handlers)",
    test_files="(none)",
    independent_reference="(not applicable)",
    numerical_validation_status="NOT VERIFIED - no automated coverage",
    physical_applicability_status="NOT APPLICABLE",
    experimental_validation_status="NONE",
    validation_category=C4,
    remaining_limitation="Interactive-only paths; the headless export path is covered by the subprocess driver but the GUI actions themselves are not.")

row(equation_id="E-58", equation_name="Raw V/I -> R -> rho -> sigma measurement chain",
    registry_section="10 GUI / presentation",
    implementation_file="(does not exist)",
    implementation_function="(none - process_four_probe_table requires a conductivity column)",
    test_files="(none)",
    independent_reference="references.resistivity_from_geometry; references.conductivity_from_resistivity (available, unused by the application)",
    numerical_validation_status="NOT IMPLEMENTED - confirmed absent in audit M-01",
    physical_applicability_status="NOT APPLICABLE",
    experimental_validation_status="NONE",
    validation_category=C4,
    remaining_limitation="Geometry (width, thickness, probe_length) is used only for the sigma UNCERTAINTY of an already measured sigma. The chain itself must be built as a separate module in Phase 4; reconstructed example data must never be presented as instrument validation.")

# ── 11. Retired legacy / compatibility surfaces ─────────────────────────────
# The compatibility shims (src/legacy/) were deleted in the architecture
# migration on 2026-11-13. The four entries below record what was verified
# about them while they existed; the parenthesised fields mark the surfaces
# as retired instead of naming paths that no longer exist. No validation
# status, category or count was changed by the retirement.
LEG = [
    ("E-59", "Legacy calculation wrappers (RETIRED)",
     "(retired 2026-11-13 - was src/legacy/core/calculations.py, every numerical assertion preserved verbatim in tests/test_canonical_calculations_surface.py)",
     "(the verified delegation surface: calculate_pf, calculate_kappa_e, calculate_kappa_l, calculate_zt, estimate_lorenz)",
     "(retired with the shim, active test files: tests/test_canonical_calculations_surface.py and tests/test_architecture_dependencies.py)",
     "references (the delegated domain functions)",
     "VERIFIED (historical) - the compatibility shim was verified to be pure delegation before its deletion; the canonical domain surface passes the same numerical assertions",
     "CONDITIONAL - inherits the delegated relations", "NONE", C1,
     "Compatibility surface deleted in the architecture migration (2026-11-13); no independent scientific content."),
    ("E-60", "Legacy constant aliases (RETIRED)",
     "(retired 2026-11-13 - was src/legacy/core/constants.py, the application-wide constants live on in src/domain/physical_constants.py)",
     "(the verified alias surface: DEFAULT_LORENZ, LEGACY_DEFAULT_LORENZ)",
     "(retired with the shim, active test files: tests/test_canonical_calculations_surface.py and tests/test_scientific_equations_audit.py)",
     "references.lorenz_sommerfeld",
     "VERIFIED (historical) - the legacy Lorenz alias was verified to equal the application-wide 2.44e-8 (SE-015 author decision) before its deletion",
     "CONDITIONAL - 2.44e-8 is a rounded value; the exact Sommerfeld value is 2.443004509e-8",
     "NONE", C1,
     "The alias module was deleted in the architecture migration (2026-11-13); the application-wide constants remain in src/domain/physical_constants.py."),
    ("E-61", "Legacy multi-sample orchestration (RETIRED)",
     "(retired 2026-11-13 - was src/legacy/core/analyzer.py, the orchestration lives on in src/application/use_cases.py (process_multi_sample_data, process_multi_sample_batch) and src/presentation/multi_sample_plots.py)",
     "(the verified delegation surface: process_sample_data, run_multi_sample_analysis, plot_comparisons)",
     "tests/test_batch_workflows.py (now drives the canonical application workflows)",
     "references (the delegated use cases)",
     "VERIFIED (historical) - the compatibility wrapper was verified to be pure delegation to the application use cases before its deletion",
     "CONDITIONAL - inherits E-44", "NONE", C1,
     "A sample error aborts the batch (established behaviour); the compatibility wrapper was deleted in the architecture migration (2026-11-13)."),
    ("E-62", "Legacy presentation logic aliases (RETIRED)",
     "(retired 2026-11-13 - was src/legacy/ui/logic/ with 4 alias modules, the canonical modules are src/presentation/kappa_logic.py, table_handler.py, ui_builder.py and unit_converter.py)",
     "(the verified re-export surface: kappa_logic, table_handler, ui_builder, unit_converter)",
     "(retired with the shim, the presentation modules are covered by tests/test_architecture_dependencies.py)",
     "references (the delegated functions)",
     "VERIFIED (historical) - the alias modules were verified to be pure delegation before their deletion",
     "CONDITIONAL - inherits the delegated relations", "NONE", C1,
     "The alias modules were deleted in the architecture migration (2026-11-13)."),
]
for eid, name, impl, fn, tests, ref_fn, num, phys, exp, cat, lim in LEG:
    row(equation_id=eid, equation_name=name,
        registry_section="11 Retired legacy / compatibility surfaces",
        implementation_file=impl,
        implementation_function=fn,
        test_files=tests,
        independent_reference=ref_fn,
        numerical_validation_status=num,
        physical_applicability_status=phys,
        experimental_validation_status=exp,
        validation_category=cat,
        remaining_limitation=lim)


# ── classification overrides ────────────────────────────────────────────────
# The physical-applicability axis states the conditions under which the
# *validated claim* holds:
#
#   * a workflow whose validated claim is the PARSING / unit handling
#     (E-45, E-47, E-50, E-54, E-55, E-59..E-62) is unconditional - the
#     scientific relations it carries are validated under their own entries;
#   * a workflow whose validated claim IS the derived property
#     (E-43, E-51, E-53) inherits that property's model conditions;
#   * a propagator validates a COMBINATION RULE, which is unconditional; the
#     independence of inputs is a statistical assumption and is recorded in
#     remaining_limitation;
#   * a relation that presupposes a specimen model (rectangular geometry,
#     1-D heat flow, a linear fit, a single band) is conditional.
#
# The table below is the single, reviewable place where those decisions are
# applied.
OVERRIDES: dict[str, dict[str, str]] = {
    "E-12": {
        "physical_applicability_status": (
            "CONDITIONAL - the propagator presupposes sigma = L/(R*A) for a "
            "rectangular specimen with uniform current"
        ),
        "validation_category": C2,
    },
    "E-15": {
        "physical_applicability_status": (
            "UNCONDITIONAL - the combination rule does not depend on the material; "
            "the independence of the contributions is a statistical assumption"
        ),
    },
    "E-35": {
        "physical_applicability_status": (
            "CONDITIONAL - assumes one-dimensional heat flow and a homogeneous specimen"
        ),
        "validation_category": C2,
    },
    "E-43": {
        "physical_applicability_status": (
            "CONDITIONAL - inherits the Lorenz-number assumption of E-02"
        ),
        "validation_category": C2,
    },
    "E-45": {
        "physical_applicability_status": (
            "UNCONDITIONAL for the parsing and unit handling; the imported sigma "
            "is taken as measured and is not re-derived here"
        ),
    },
    "E-46": {
        "physical_applicability_status": (
            "UNCONDITIONAL for the parsing; the fitted slope presupposes a linear "
            "dV/dT response over the fitted range"
        ),
    },
    "E-47": {
        "physical_applicability_status": (
            "UNCONDITIONAL for the parsing and unit handling; the temperature unit "
            "comes from the column header (SE-026/028 resolved)"
        ),
    },
    "E-48": {
        "physical_applicability_status": (
            "UNCONDITIONAL - the combination rule does not depend on the material; "
            "the independence of inputs is a statistical assumption"
        ),
    },
    "E-49": {
        "physical_applicability_status": (
            "UNCONDITIONAL - the combination rule does not depend on the material; "
            "the independence of inputs is a statistical assumption"
        ),
    },
    "E-51": {
        "physical_applicability_status": (
            "CONDITIONAL - inherits the SPB single-band assumption"
        ),
        "validation_category": C2,
    },
    "E-52": {
        "physical_applicability_status": (
            "UNCONDITIONAL for the fit arithmetic; the activation-energy "
            "interpretation presupposes ln(sigma) or ln(sigma*T) linear in 1/T "
            "over the fitted range"
        ),
    },
    "E-53": {
        "physical_applicability_status": "CONDITIONAL - inherits E-43",
        "validation_category": C2,
    },
    "E-59": {
        "physical_applicability_status": (
            "UNCONDITIONAL - pure delegation (historical verification of the "
            "retired shim); the scientific content and its physical conditions "
            "are those of the delegated function (E-01..E-04)"
        ),
    },
    "E-60": {
        "physical_applicability_status": (
            "UNCONDITIONAL - an alias of the application-wide constant "
            "(historical verification of the retired alias); the value "
            "2.44e-8 is a rounded value, the exact Sommerfeld value being "
            "2.443004509e-8"
        ),
    },
    "E-61": {
        "physical_applicability_status": (
            "UNCONDITIONAL - pure delegation (historical verification of the "
            "retired wrapper); the physical conditions are those of E-44"
        ),
    },
    "E-62": {
        "physical_applicability_status": (
            "UNCONDITIONAL - pure delegation (historical verification of the "
            "retired alias modules); the scientific content and its physical "
            "conditions are those of the delegated function"
        ),
    },
}

for _row in R:
    _override = OVERRIDES.get(_row["equation_id"])
    if _override:
        _row.update(_override)


# ── write ───────────────────────────────────────────────────────────────────
# the rows are written in equation-id order regardless of how they were built
R.sort(key=lambda r: r["equation_id"])

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=COLUMNS, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    writer.writerows(R)

ids = [r["equation_id"] for r in R]
assert len(ids) == len(set(ids)) == 62, f"expected 62 unique ids, got {len(ids)}"
assert ids == [f"E-{i:02d}" for i in range(1, 63)], "equation ids must be E-01..E-62"

counts: dict[str, int] = {}
for r in R:
    counts[r["validation_category"]] = counts.get(r["validation_category"], 0) + 1
print(f"wrote {OUT.relative_to(ROOT)}  ({len(R)} rows)")
for cat in (C1, C2, C3, C4):
    print(f"  {cat:<52} {counts.get(cat, 0)}")
