# Phase 3 Findings Register — critical scientific corrections

**Phase:** 3
**Date:** 2026-11-12
**Scope:** the items of the Phase 1 audit's remediation order §7 items 3.1–3.7.

The Phase 1 audit (`INITIAL_STATE_AUDIT.md`) is left unchanged: it is a
snapshot of the tree as it was found, and rewriting it would destroy its
value as a record. This file records what Phase 3 **found** and **changed**.

---

## Summary

| ID | Severity | Area | Finding | Outcome |
|---|---|---|---|---|
| **D-01** | HIGH | science / GUI | The negative-lattice-conductivity diagnostic had **no production caller**, so a physically impossible κ_L was displayed, plotted and exported without any warning | **FIXED** — the validator is now wired into the main-table recalculation and the multi-sample workflow; the negative value is preserved, never clipped |
| **D-02** | MEDIUM | benchmark data | The processed dataset's carrier columns were named `_cm3` / `_cm2_Vs` but stored the **unconverted SI** values (10⁶ and 10⁴ too large); the provenance cards repeated the wrong units | **FIXED** — the values are converted, the units are validated at extraction, the cards are regenerated, and a physical-plausibility guard was added |
| **D-10** | MEDIUM | validation docs | Two different quantities were conflated under the header *"SPB deviation"*: the **κ_L sensitivity** (26.5 % / 130.6 %) and the **SPB deviation** (≤3.6 % / +10…46 % / −25…38 %) | **FIXED** — both are now tabulated separately, everywhere |
| **D-11** | LOW | code hygiene | `calculate_dulong_petit_limit` duplicated the rounded gas-constant literal `8.314462618` instead of using the named `LEGACY_GAS_CONSTANT` | **FIXED** — the named constant is used; the 1.8e-11 difference from the exact `GAS_CONSTANT` is documented rather than silently changed |
| **D-12** | MEDIUM | model | The weighted-mobility **implementation does not evaluate the equation printed in the scientific model register** (they differ by 1.49–8.25×), and the implemented shape factor **diverges for small \|S\|** (≈10¹² cm²/(V·s) at S = 0) | **DOCUMENTED** — the register was corrected to describe the implementation; the implementation was **not** changed (no primary source, no experimental reference) |
| **D-13** | — | model | The SiGe:P Lorenz discrepancy was reported as an unresolved contradiction | **RESOLVED** — the cause is the **scattering assumption** (λ ≈ 1.41 reproduces the published value exactly); the model was **not** refitted |

---

## D-01 — the negative-κ_L diagnostic now reaches the user

### What was wrong

`domain/validation.py::validate_kappa_l_array()` produced a correct
`WARNING`, and `application/use_cases.py::validate_measurement_data()`
forwarded it — but **no production code called either**. The GUI wrote
`df["Lattice TC"] = calculated["kappa_L"]` straight into the table
(`gui/main_window.py:291-301`), so a physically impossible κ_L was
displayed, plotted and exported with no diagnostic.

### What was changed

| File | Change |
|---|---|
| `src/application/use_cases.py` | New `validate_calculated_properties()` — validates a **computed** suite and returns **plain records** (`severity`/`field`/`message`) so the presentation layer never imports the domain types. New `validate_multi_sample_properties()` — the same for processed multi-sample frames, with the sample name prefixed to each message. |
| `src/presentation/validation_notices.py` | **New.** Pure helpers: `split_by_severity`, `has_blocking_notices`, `summarise`, `format_detail`, `negative_lattice_count`, `notice_signature`. No Qt, no domain import (both enforced by tests). |
| `src/gui/main_window.py` | `recalculate_all_properties()` now calls the validator and passes the notices to a new `present_validation_notices()` method. A **persistent status-bar indicator** shows the condition for as long as it exists; a **modal notice** appears when the set of messages *changes* (so it cannot be missed but does not reappear on every cell edit); an ERROR-level notice always shows a modal notice. |
| `src/legacy/ui/dialogs/multi_sample_dialog.py` | The multi-sample workflow validates the processed samples and warns before plotting or exporting. |
| `tests/scientific/test_negative_kappa_l_diagnostic.py` | **New, 16 tests.** |

### The value is preserved

The calculated κ_L is **never clipped**. The negative number stays in the
table, in the plot and in the export, so it remains available for
diagnosis; what changes is that the user is told.

### Tests

`tests/scientific/test_negative_kappa_l_diagnostic.py` (14 headless + 2 GUI).
The two GUI tests are **skipped** in the primary environment (Qt DLL) and
**pass** in the Qt-capable virtual environment.

---

## D-02 — the processed benchmark carrier data were 10⁶ too large

### What was wrong

The processed dataset declares

```
published_carrier_concentration_cm3   ->  1.289e+26   (but that is m^-3)
published_carrier_mobility_cm2_Vs     ->  5.07e-03   (but that is m^2/(V.s))
```

The **raw** extract correctly held the published SI values; the *processed*
copied them unchanged into columns whose names promised cm⁻³ and
cm²/(V·s). The provenance cards also recorded the wrong units.

**Why it escaped:** the only test that consumed those columns is a
*round trip* (n → m\* → n), which is **scale-invariant** — feeding n in the
wrong unit and recovering it with the same wrong unit cancels the error
exactly.

### What was changed

| File | Change |
|---|---|
| `tests/experimental_benchmarks/extract_workflow_benchmarks.py` | The published SI carrier quantities are **converted** into the units the processed column names declare (×10⁻⁶ and ×10⁴). A `EXPECTED_UNITS_PUBLISHED` table **validates** every property's published unit at extraction time — the script previously validated no unit at all. |
| `tests/experimental_benchmarks/extract_benchmarks.py` | "Carrier concentration" and "Carrier mobility" added to `EXPECTED_UNITS`, so their units are validated rather than assumed. |
| `tests/experimental_benchmarks/references/*.md` | **Regenerated** with the current generator: correct units, plus the measurement conditions, authors, journal and year that the current generator emits. |
| `tests/experimental_benchmarks/processed/sige_si80ge20p1.csv` | Regenerated: n = 1.289e+20 cm⁻³, μ = 50.7 cm²/(V·s) — both physically sensible. |
| `tests/experimental_benchmarks/test_benchmark_data_integrity.py` | **New, 11 tests**, stated in **physical** terms so the error cannot hide again (a semiconductor cannot have 10²⁶ cm⁻³ or 5e-3 cm²/(V·s)). |

### A source-data observation, recorded

The published SiGe:P carrier-concentration curve contains a **duplicated
temperature point** (764.0777 K) with two different concentrations. The
extraction preserves both points verbatim — correct, since the raw data are
the published data — but the curve is therefore **not strictly monotonic in
temperature and must not be interpolated**. This is now asserted explicitly
so that it is not later mistaken for a processing artefact.

---

## D-10 — two different quantities were tabulated as "SPB deviation"

The shipped validation documents listed **26.5 %** (Bi₂Te₃) and **130.6 %**
(PbTe) under the header *"SPB deviation"*. Those numbers are real, but they
measure the **κ_L sensitivity** — how much the computed lattice thermal
conductivity changes when the application-wide constant L = 2.44e-8 is used
instead of the implied value. The **SPB deviation** is a different and
smaller quantity:

| Specimen | L implied | pair spread | **κ_L sensitivity** | **SPB deviation** (acoustic, λ = 0) |
|---|---|---|---|---|
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | 1.6525e-8 | 3.4 % | 26.5 % | **−3.6 % … −1.5 %** |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | 1.2765e-8 | 24.9 % | 130.6 % | **+10.0 % … +46.0 %** |
| Si₈₀Ge₂₀P₁ | 2.4579e-8 | 3.0 % | 0.7 % | **−37.7 % … −25.2 %** (median −35 %) |

**This materially changes the scientific picture:** the SPB acoustic model
performs **well** on the Bi₂Te₃ specimen (≤3.6 %), is 15–38 % low on
P-doped SiGe (cause identified, D-13), and is 10–46 % high on PbTe — where
the implied value is itself unreliable (24.9 % spread), so no model
conclusion can be drawn there.

**Changed:** `validation/SCIENTIFIC_CALCULATION_TEST_RESULTS.md`,
`validation/SCIENTIFIC_VALIDATION_LIMITATIONS.md`, the equation-status
mapping and its generator, and the Phase 3 assessment. Reproduce with
`python tools/lorenz_diagnostics.py`.

---

## D-11 — the Dulong–Petit gas constant

`domain/calculations.py::calculate_dulong_petit_limit` used the literal
`8.314462618` instead of the named `LEGACY_GAS_CONSTANT`, while
`domain/phonon.py::dulong_petit_molar` used the exact CODATA-derived
`GAS_CONSTANT`. The two therefore differed by **1.8e-11** relative.

**Decision.** The named `LEGACY_GAS_CONSTANT` is now used, so the **value is
unchanged** (the golden regression snapshot stays valid and no behaviour
changes), the magic literal is gone, and the residual difference from the
exact constant is documented in the function's docstring and asserted by
`tests/scientific/test_unit_conversion_audit.py`.

The alternative — switching to the exact constant — was considered and
**rejected**: it is scientifically irrelevant at 1.8e-11 and would have
invalidated the regression snapshot for no scientific gain. Aligning the two
functions is left as an open item.

---

## D-12 — the weighted-mobility implementation versus the model register

Full detail in `WEIGHTED_MOBILITY_AUDIT.md`. Summary:

* `docs/SCIENTIFIC_MODEL_REGISTER.md` §3.4 printed an expression the
  implementation does not evaluate; the two differ by **1.49 to 8.25×** over
  a representative grid, because their second shape terms and their
  prefactors differ.
* The implemented shape factor **diverges as |S| → 0**, reaching
  ≈9.7e12 cm²/(V·s) — four to ten orders of magnitude above any physical
  mobility.

**Decision.** The implementation was **not** changed: the primary source is
not available in the repository, there is **no experimental reference**
(the only published mobility curve is negative and unusable), and the change
would be a physics change rather than a bug fix. The register was corrected
to describe the implementation, the divergence was documented, and
`tests/scientific/test_weighted_mobility_audit.py` (8 tests) characterises
both findings so that any future change to the physics is deliberate and
visible.

---

## D-13 — the SiGe:P Lorenz discrepancy: cause identified, model not refitted

Full detail in `SIGE_LORENZ_INVESTIGATION.md`. The four candidate causes
were discriminated:

| Candidate | Result |
|---|---|
| (c) the published κ/κ_L pair is internally inconsistent | **rejected** — 3.0 % spread, at the 1.7 % digitisation noise floor |
| (d) the digitisation contributes the offset | **rejected** — the noise floor is below the observed spread |
| (b) the single-parabolic-band model fails | **rejected** — the specimen is in the *transitional* degeneracy regime, where the single-band model is most applicable |
| (a) the **scattering assumption** | **CONFIRMED** — **λ = 1.41** reproduces the published value exactly; 1.41 lies between alloy/optical (1) and ionised-impurity (2), as expected for a P-doped alloy |

**The model was not refitted.** The finding is preserved as a negative
result and locked in by `tests/scientific/test_sige_lorenz_finding.py`
(5 tests), which **fails** if the acoustic value is ever made to agree with
the measurement.

The documentation now states the acoustic-scattering approximation wherever
it is used: the `estimate_lorenz` docstring, the `rigorous_lorenz_number`
docstring, the `seebeck_from_reduced_fermi_level` docstring (including the
Γ-factor reduction that was previously unstated), the
`calculate_carrier_density_spb` docstring (including the 1/Γ(3/2) factor),
the equation registry (E-05, E-06), the results report and the limitations
report.

---

## Additional Phase 3 work

### The complete unit-conversion audit (audit item 3.7)

`tests/scientific/test_unit_conversion_audit.py` — **34 tests** covering all
twelve quantities the brief names: Seebeck coefficient, electrical
conductivity, electrical resistivity, thermal conductivity, temperature,
carrier concentration, mobility, effective mass, density, heat capacity,
power factor and Lorenz number. For each: the **exact** factor (not merely
a round trip, which would accept a pair of mutually wrong factors), the
round trip, dimensional consistency against the defining relation, and the
rejection of unsupported units. The SE-042 regression is repeated in the
thermal-conductivity section.

**Residual observation (not a defect).** The **density** and **heat
capacity** conversions are performed inline in
`presentation/kappa_logic.py` rather than in a centralised domain
converter, and appear three times in that one function. The factors are
correct (g/cm³ × 1000 → kg/m³; J/(g·K) × 1000 → J/(kg·K)) and are now
tested, but centralising them would be an architecture change outside the
scope of this phase.

### The environment-dependent report guard

`tests/experimental_benchmarks/test_report_consistency.py::test_reports_state_the_actual_test_counts`
compared the report's quoted counts against a measurement that included the
GUI end-to-end module — so it **failed in any environment where Qt loads**
(the counts differ by the four GUI tests). The measurement now excludes the
environment-dependent module, so the quoted benchmark counts
(**109 passed, 4 skipped**) are valid in every environment, and the report
states the GUI module's result separately. Both validation reports were
updated accordingly.

### A SciPy-version-dependent regression test

`tests/scientific/test_independent_references.py::test_seebeck_regression_matches_an_independent_ols`
compared the *standard error* of two implementations on **perfectly
collinear** data, where the true standard error is exactly zero. SciPy
1.17 returns 0.0 and SciPy 1.18 returns 1.8e-12 for the same data, so the
test compared two floating-point noise residues and failed in the
Qt-capable environment (SciPy 1.18.1) while passing in the primary one
(SciPy 1.17.1).

**This was not a tolerance weakening.** The meaningless comparison was
replaced by two meaningful ones: on collinear data the standard error must
be **physically negligible** (< 1e-9 V/K, i.e. a relative standard
uncertainty of 7e-6 on a 150 µV/K coefficient — four orders below the 1–5 %
experimental uncertainty), and on data with genuine scatter the standard
error must agree with SciPy to 1e-10 (the observed difference between the
two formulations is 3.9e-12 / 1.1e-12). The slope comparison is unchanged
at 1e-12, where it is exact.

---

## What was deliberately **not** changed

| Item | Reason |
|---|---|
| The SPB model | The SiGe discrepancy is explained by the scattering assumption; refitting the model to a measurement is forbidden and would not generalise |
| The weighted-mobility expression | No primary source and no experimental reference; changing it would be an unvalidated physics change |
| A Kane/Dingle/multiband Lorenz number | The required inputs (Hall n and μ, effective mass, band gap) are **absent** from the benchmark data and no independent reference exists — see `DEGENERATE_LORENZ_ASSESSMENT.md` |
| The Dulong–Petit constant value | 1.8e-11 is irrelevant; the golden snapshot stays valid |
| The published data | Never altered; the defect was in how they were *recorded*, and the recording is now faithful |
| Any tolerance | No tolerance was loosened to make a test pass; two were made *stricter* and one meaningless comparison was replaced |
