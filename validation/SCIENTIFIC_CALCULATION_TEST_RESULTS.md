# Scientific Calculation Test Results — Seebeck Prime

**Version:** 1.0
**Date:** 2026-11-12
**Companion documents:** `SCIENTIFIC_EQUATION_REGISTRY.md` ·
`SCIENTIFIC_CALCULATION_TEST_PLAN.md` · `INDEPENDENT_REFERENCE_METHODS.md` ·
`SCIENTIFIC_VALIDATION_LIMITATIONS.md` ·
`SCIENTIFIC_BENCHMARK_MATERIAL_FAMILIES.md`

---

## 0. Headline

**The test suite passes; that is not the same as "the software is validated".**

607 automated tests pass and 6 are skipped. Of those, **156 are new
scientific tests** written for this programme against **independently
written reference implementations** (`validation/independent_calculations/`,
which is machine-checked for independence).

The evidence supports a **differentiated** assessment:

- The **calculation engine** is verified to a high standard: every
  implemented equation has been re-derived independently and agrees to
  between 1e-14 and 1e-6 relative error, far inside every physical
  uncertainty.
- The **published-measurement** evidence exists for **four specimens** and
  covers the power factor and the figure of merit (1.3–5.9 %).
- The **physical models** are verified as *implementations* but are **not**
  validated as *models*: for the one specimen where the published data can
  decide the question (SiGe:P), the published measurements **contradict**
  the embedded single-parabolic-band acoustic-phonon model by ≈35 %.
- Six interactive GUI paths and the raw-V/I → σ chain have **no** automated
  coverage or do not exist.

---

## 1. Environment

### 1.1 Primary environment (all non-GUI tests)

| Item | Value |
|---|---|
| OS | Windows 10 Pro, 10.0.19045 (build 19045) |
| Python | 3.13.9 (Anaconda, 64-bit MSC v.1944) |
| NumPy | 2.3.5 |
| SciPy | 1.17.1 |
| pandas | 3.0.2 |
| Matplotlib | 3.10.9 |
| pytest | 9.1.1 |
| pytest-cov | 7.1.0 |
| PyQt6 (installed) | 6.11.0 / Qt 6.11.1 — **QtWidgets fails to load** in this environment (DLL error `0xc0000139`) |

### 1.2 Qt-capable environment (GUI subset only)

| Item | Value |
|---|---|
| Interpreter | `%LOCALAPPDATA%\Temp\opencode\seebeck-gui\Scripts\python.exe` (venv) |
| Python | 3.13.9 |
| PyQt6 | 6.9.1 |
| Qt | 6.9.0 |
| Launcher | `%LOCALAPPDATA%\Temp\opencode\run_seebeck_gui.ps1` (strips `anaconda3\Library\bin` from `PATH`) |

**The difference is documented rather than hidden:** the primary environment
is the one in which the project is developed and in which 590 of the 596
tests run. The Qt-capable venv differs only in the PyQt6/Qt build
(6.9.1/6.9.0 vs 6.11.0/6.11.1) and is used solely for the 7 GUI tests. The
GUI code path is identical; the GUI tests pass in the venv and are skipped
(not failed) in the primary environment.

### 1.3 Commands

```powershell
# full suite (primary environment)
$env:PYTHONDONTWRITEBYTECODE='1'
C:\Users\Elkady\anaconda3\python.exe -m pytest -q -p no:cacheprovider

# per-directory breakdown
C:\Users\Elkady\anaconda3\python.exe -m pytest tests\scientific            -q -p no:cacheprovider
C:\Users\Elkady\anaconda3\python.exe -m pytest tests\experimental_benchmarks -q -p no:cacheprovider
C:\Users\Elkady\anaconda3\python.exe -m pytest tests --ignore=tests\scientific --ignore=tests\experimental_benchmarks -q -p no:cacheprovider

# GUI subset (Qt-capable venv)
C:\Users\Elkady\AppData\Local\Temp\opencode\seebeck-gui\Scripts\python.exe -m pytest tests\experimental_benchmarks\test_gui_end_to_end.py -q -p no:cacheprovider
C:\Users\Elkady\AppData\Local\Temp\opencode\seebeck-gui\Scripts\python.exe -m pytest tests\test_startup_smoke.py -q -p no:cacheprovider

# reference-comparison table (regenerates validation/reference_comparison_table.md)
C:\Users\Elkady\anaconda3\python.exe tools\generate_reference_comparison.py

# Phase X material-family survey
C:\Users\Elkady\anaconda3\python.exe tools\survey_material_families.py
```

---

## 2. Test counts

### 2.1 Full suite — primary environment

```
607 passed, 6 skipped, 1 warning in 22.71s
```

| Directory | Passed | Skipped | Content |
|---|---|---|---|
| `tests/` (root suites, 26 files) | 342 | 1 | pre-existing engineering, unit and audit suites |
| `tests/scientific/` (**new**) | **156** | 0 | independent-reference, physical-constraint, unit-matrix, edge-case and equation-mapping-guard suites |
| `tests/experimental_benchmarks/` | 109 | 5 | published-measurement validation, importers, GUI e2e, report consistency |
| **Total** | **607** | **6** | |

### 2.2 GUI subset — Qt-capable venv

```
tests\experimental_benchmarks\test_gui_end_to_end.py    4 passed
tests\test_startup_smoke.py                              3 passed
```

### 2.3 Skips — every one with its reason

A skipped test is **not** a passed test.

| # | Test | Reason | Classification |
|---|---|---|---|
| 1 | `test_gui_end_to_end.py::test_*` (module-level) | `ImportError: DLL load failed while importing QtWidgets: The specified procedure could not be found` — the conda environment's PyQt6 6.11.0 cannot load QtWidgets | **Skipped: Qt unavailable.** The same 4 tests **pass** in the Qt-capable venv |
| 2 | `test_startup_smoke.py::test_import_main_smoke_when_qt_available` | Same Qt DLL failure | **Skipped: Qt unavailable.** The same test **passes** in the venv |
| 3 | `test_benchmarks.py:275` | `sige_si80ge18sb2`: the source paper publishes no lattice thermal conductivity for this sample | **Skipped: reference data absent** (not a failure) |
| 4 | `test_benchmarks.py:326` | `sige_si80ge18sb2`: no published lattice thermal conductivity | **Skipped: reference data absent** |
| 5 | `test_benchmarks.py:292` | `pbte_pbte0_95pbs0_05`: the published κ and κ_L are not consistent with a single Lorenz number (implied L = 1.276e-8 W·Ω/K², spread 25 %) | **Skipped: UNVERIFIED — noise-limited by the source data, not by the calculation** |
| 6 | `test_workflow_validation.py:204` | The published carrier-mobility curve is negative (physically impossible) and cannot be used as a reference | **Skipped: reference data unusable** — the weighted mobility therefore has **no** experimental validation |

**Net effect:** skips 1–2 are environmental (and are covered by the venv
run); skips 3–6 are *scientific gaps* that no amount of testing can close
with the available data. They are reported as UNVERIFIED, not as passes.

---

## 3. Independent-reference comparison (Phase IX)

Generated by `tools/generate_reference_comparison.py` → also stored verbatim
in `validation/reference_comparison_table.md`.

**31 comparisons, 0 outside tolerance.** Worst case over each parameter
grid:

| Calculation | Application result | Independent reference | Absolute error | Relative error | Tolerance | Result |
|---|---|---|---|---|---|---|
| PF = S²σ | 9e-08 | 9e-08 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| κₑ = LσT | 1.8788e-06 | 1.8788e-06 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| κ_L = κ_total − κₑ | 0.49268 | 0.49268 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| ZT = PF·T/κ | 0.0006 | 0.0006 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| κ = αC_pρ (SI) | 0.0192 | 0.0192 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| κ = αC_pρ (lab units) | 2.0844 | 2.0844 | 4.441e-16 | 2.131e-16 | 1e-12 | PASS |
| Kim empirical Lorenz L(S) | 1.531800417e-08 | 1.531800417e-08 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| Sommerfeld L₀ = (π²/3)(k_B/e)² | 2.443004509e-08 | 2.443004509e-08 | 7.367e-19 | 3.015e-11 | 1e-09 | PASS |
| SPB S(η) | 31.48644901 | 31.48644901 | 4.619e-13 | 1.467e-14 | 1e-06 | PASS |
| SPB L(η) | 1.494188406e-08 | 1.494188406e-08 | 3.375e-22 | 2.259e-14 | 1e-06 | PASS |
| SPB η inversion from S | 0.5294447553 | 0.5294461941 | 1.439e-06 | 2.718e-06 | 1e-05 | PASS |
| SPB carrier density n(η,m*,T) | 2.496056677e+20 | 2.496056677e+20 | 1.439e+07 | 5.763e-14 | 1e-06 | PASS |
| SPB effective mass m*(S,n,T) | 1.238702872 | 1.238702891 | 1.958e-08 | 1.581e-08 | 1e-06 | PASS |
| Weighted mobility μ_w | 9591.650591 | 9591.650599 | 7.965e-06 | 8.304e-10 | 1e-09 | PASS |
| Hall coefficient R_H | 5e-06 | 5e-06 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| Hall carrier density n_H | 6.241509074e+23 | 6.241509074e+23 | 0.000e+00 | 0.000e+00 | 1e-09 | PASS |
| Hall mobility μ_H | 0.1 | 0.1 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| u(PF) | 1.030776406e-06 | 1.030776406e-06 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| u(κₑ) | 0.00206228708 | 0.00206228708 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| u(κ_L) | 0.01118033989 | 0.01118033989 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| u(ZT) | 0.003391164992 | 0.003391164992 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| u(σ) from geometry | 1417.744688 | 1417.744688 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| u(κ) laser flash | 0.1972711839 | 0.1972711839 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| u(ρ) density | 68394.84585 | 68394.84585 | 0.000e+00 | 0.000e+00 | 1e-12 | PASS |
| Dulong–Petit molar C_V | 124.7169393 | 124.7169393 | 2.842e-14 | 2.279e-16 | 1e-12 | PASS |
| Dulong–Petit specific C_V | 171.3968794 | 171.3968794 | 5.684e-14 | 3.316e-16 | 1e-12 | PASS |
| Device efficiency: ZT_avg | 0.9111747179 | 0.9111747179 | 0.000e+00 | 0.000e+00 | 2e-03 | PASS |
| Device efficiency: ZT_eng | 0.9088529406 | 0.9088529406 | 0.000e+00 | 0.000e+00 | 2e-03 | PASS |
| Device efficiency: Carnot | 0.6666666667 | 0.6666666667 | 0.000e+00 | 0.000e+00 | 2e-03 | PASS |
| Device efficiency: η_max | 0.1486014697 | 0.1486014697 | 0.000e+00 | 0.000e+00 | 2e-03 | PASS |
| Device efficiency: η_eng | 0.1483477195 | 0.1483477195 | 0.000e+00 | 0.000e+00 | 2e-03 | PASS |

**Interpretation.** The agreement is at the level of double-precision
round-off for the closed-form relations (identical results, zero error),
and at 1e-14 – 1e-6 for the numerically integrated relations. These errors
are **6 to 12 orders of magnitude smaller** than the physical uncertainties
in the inputs (typically 1–5 %), so the implementation is not the limiting
factor in any application of the software.

### 3.1 The two discrepancies found — and how they were resolved

Two comparisons initially **failed**. In both cases the diagnosis showed
that the *independent reference* was wrong, not the application:

| # | Discrepancy | Root cause | Resolution |
|---|---|---|---|
| D1 | SPB S(η) disagreed by up to a factor **8.9** at η = 3, λ = 0 | the reference's textbook prefactor carried a spurious (λ+1) factor in the denominator | The reference was corrected to S = (k_B/e)[(λ+2)F̂_{λ+1}/F̂_λ − η] (the identity follows from r = λ − ½). The application's unnormalised-prefactor form is then **identical** to the corrected Blatt form, and agrees to ≤1e-6 for λ ∈ {0,1,2}. **The application's SPB implementation is correct for every λ.** |
| D2 | SPB m\* disagreed by exactly a factor **300** at T = 300 K | the reference multiplied N_c by an extra T^{3/2} while already using the T-dependent N_c — a double count | The reference was corrected to the textbook N_c. The application's internal constant `_CONST_N0_SI` carries the 1/Γ(3/2) factor required by the unnormalised-integral convention; its n(η=0, m*=1, 300 K) = 1.9200692976919e19 cm⁻³ now matches the textbook to **1e-15**. |

Full derivation in `INDEPENDENT_REFERENCE_METHODS.md` §8.

**Two further "failures" were arithmetic slips in the new *test
expectations*** (a power factor of 2e-4 rather than 1e-4, and 100 S/m ≡
1 Ω·cm rather than 0.01 Ω·cm). The application was **not** changed.

### 3.2 A confirmed application defect found by this programme (SE-042)

While writing the unit-conversion matrix, the thermal-conductivity
converter was found to **ignore its unit argument entirely**.

**Location.** `src/domain/units.py::kappa_to_si` and
`src/domain/units.py::kappa_from_si`.

**The problem.** Both functions returned `float(value)` for *any* unit
string:

```python
def kappa_to_si(value: float, unit: str = "W/(m·K)") -> float:
    """Convert thermal conductivity to SI base [W/(m·K)].  Currently only W/(m·K) supported."""
    return float(value)
```

so `kappa_to_si(1.0, "W/(cm·K)")` returned `1.0` — a value that is **100×
wrong** (1 W/(cm·K) = 0.01 W/(m·K)) — with no error and no warning. A
silently mis-scaled κ propagates directly into κ_L = κ_total − κₑ and
therefore into ZT. The three sibling converters (`sigma_to_sm`,
`seebeck_to_vk`, `pf_to_si`) all raise `ValueError` for an unknown unit;
the κ converter was the odd one out.

**Classification.** Unit-related. Not mathematical, not physical-model, not
numerical.

**Reachability.** Latent in the current GUI — there is no thermal-conductivity
unit selector (`gui/main_window.py` sets `unit_combos["Thermal Cond."] = None`),
so the value is always W/(m·K) in the interactive path. It **is** reachable
through the public application API `to_base_value(value, unit,
"thermal_conductivity")`, which is the surface an importer or a plug-in
would use.

**The smallest safe correction.** Validate the unit and raise `ValueError`
for unsupported spellings, matching the pattern of the other three
converters. This adds **no** new unit support and changes **no** scientific
equation. The application layer (`application/unit_conversion.py`) already
catches `ValueError` and passes the value through — the documented legacy
behaviour for an unrecognised unit — so the **observable application
behaviour is unchanged**; only the domain-level function becomes honest and
testable.

**Regression test.**
`tests/scientific/test_unit_conversion_matrix.py::test_thermal_conductivity_converter_validates_its_unit`
asserts that the supported spellings convert, that `"W/(cm·K)"`,
`"mW/(m·K)"` and `"W/m"` raise `ValueError`, and that the application
layer's pass-through behaviour is preserved.

**Effect on the results.** The full suite was re-run after the fix:
**607 passed, 6 skipped** — no existing test changed behaviour. (The count
grew from 592 because of the 15 equation-mapping guard tests added in the
Phase 2 reconciliation, not because of the SE-042 fix.)

### 3.3 A verification that was overstated — the negative-κ_L diagnostic never reaches the user

**Found during the Phase 1 remediation audit (finding D-01), 2026-11-12.**

This report previously stated that a negative lattice thermal conductivity
must be *"reported"*, with the evidence
`domain/validation.py` + `application/use_cases.py`, and marked the lattice
conductivity **VERIFIED**.

**What the code actually does.**

- `src/domain/validation.py:90` — `validate_kappa_l_array()` correctly emits
  a `WARNING` on field `kappa_L` for κ_L < 0. ✔
- `src/application/use_cases.py:205` — `validate_measurement_data()` forwards
  it. ✔
- **But no production code calls either function.** A repository-wide search
  for `validate_measurement_data|validate_dataset|validate_kappa_l_array`
  returns only the definitions, the re-export in `src/domain/__init__.py`, and
  the tests.
- `src/gui/main_window.py:291-301` — `recalculate_all_properties()` computes
  the property suite and writes the result straight into the table:

  ```python
  calculated = calculate_thermoelectric_properties(...)
  df["Lattice TC"] = calculated["kappa_L"]      # no validation, no warning
  df["ZT"]        = calculated["ZT"]
  ```

**Consequence.** A physically impossible κ_L < 0 — the classic symptom of a
wrong Lorenz number or a unit error — is displayed, plotted and exported as an
ordinary value, with **no diagnostic at all**. The user is not told; the
number is simply wrong.

**What was and was not verified.** The *validator* is verified: its messages,
severities and field names are asserted in
`tests/test_validation_rules.py` and `tests/scientific/test_physical_constraints.py`.
The *flagging* is not, because there is no wiring.

**Reclassification.** The lattice-conductivity row and the
physical-validators row of §8 are therefore reclassified from **VERIFIED** to
**PARTIALLY VERIFIED** (§8.1). The registry entries E-03 and E-42 are
corrected to match.

**Not fixed in this phase.** This is a production-code change and belongs to
Phase 3. The planned correction is to surface the existing validation result
in the recalculation and Kappa workflows **while preserving the negative
value** in the data (never clipping it to zero), so that the user is warned
and the diagnostic number remains available.

---

## 4. Physical-constraint results (Phase VIII)

| Constraint | Result |
|---|---|
| A negative lattice thermal conductivity must be **reported** | **PARTIAL — the validator works, the wiring does not.** `domain/validation.py` emits a `WARNING` on field `kappa_L` and `application/use_cases.py` forwards it, but **no production path calls either**, so the message never reaches the user (audit D-01, §3.3). Fixed in Phase 3. |
| A non-positive temperature is an error | PASS — `Severity.ERROR` on field `T` |
| Duplicate temperatures are reported | PASS |
| An extreme Seebeck coefficient (>3 mV/K) is a warning | PASS |
| PF ≥ 0 for any real S and any σ ≥ 0 | PASS |
| ZT > 0 for κ > 0; ZT < 0 signals a negative κ | PASS |
| κₑ > κ_total is detected as physically impossible | PASS (produces a negative κ_L which is then flagged) |
| SPB outputs (n, m*) are positive for physical inputs | PASS |
| Weighted mobility is positive for positive ρ; NaN for ρ = 0 | PASS |
| Carrier type follows sign(R_H) | PASS |
| PF, κₑ, κ_L and ZT are mutually consistent row-wise | PASS (≤1e-12) |

### 4.1 Numerical edge cases — every implemented calculation

Zero · negative · very small · very large · NaN · Inf · missing input ·
duplicate temperatures · unsorted temperatures · empty dataset ·
single-point dataset · inconsistent array lengths · invalid numerical type ·
extreme temperatures · unbracketable inversion — all exercised.

| Behaviour | Convention verified |
|---|---|
| κ_total = 0 | ZT = 0 (no ZeroDivisionError, no NaN) |
| ρ = 0 in the weighted mobility | NaN (the value carries no information) |
| length-1 array vs longer array | NumPy broadcasting; the application validates completeness before this point |
| magnitudes ~10³⁰⁰ | ±inf is the correct IEEE-754 outcome; **NaN is not** produced |
| unbracketable \|S\| in the SPB inversion | NaN, not a plausible-looking η |
| S → 0 in the SPB inversion | saturates at the metallic-limit η = 50 (documented) |
| Fermi-integral asymptotic branch switches | continuous to within 5e-3 (no visible step) |
| SPB Lorenz limits | L(η=+40) → 2.443e-8; L(η=−40) → 1.487e-8, both to <5e-3 |

---

## 5. Unit-conversion results (Phase VII)

| Check | Result |
|---|---|
| Round trip for every supported conductivity unit (S/m, S/cm, Ω·cm, Ohm-cm) | PASS, ≤1e-12 |
| Round trip for every supported Seebeck unit (V/K, µV/K, μV/K, uV/K, mV/K) | PASS, ≤1e-12 |
| Round trip for every supported PF unit (W/(m·K²), mW/(m·K²), mW/mK², µW/(m·K²), μW/mK², W/mK²) | PASS, ≤1e-12 |
| Round trip for every supported temperature unit (K, °C, C, oC) | PASS, ≤1e-12 |
| Exact factors: 1 S/cm ≡ 100 S/m; 1 Ω·cm ≡ 100 S/m; 1 µV/K = 1e-6 V/K; 1 mV/K = 1e-3 V/K; 1 mW/(m·K²) = 1e-3 W/(m·K²); 1 m⁻³ = 1e-6 cm⁻³; 0 °C = 273.15 K | PASS, ≤1e-12 |
| Unknown units are rejected, not guessed | PASS — `ValueError` raised |
| Temperature uncertainty invariant under the offset conversion | PASS |
| Conductivity uncertainty in Ω·cm: u_σ = u_ρ·100/ρ² | PASS |
| Seebeck / PF uncertainty conversions are linear | PASS |
| Uncertainty conversion is the inverse of the value conversion | PASS |
| **Display units and internal SI values are never mixed** | PASS — for every supported unit, `to_base(from_base(x)) ≡ x` |

---

## 6. Published-measurement results (Phase X)

**Four specimens**, from three real publications, with DOI-level provenance.
Deviations are the **maximum relative deviation over the published
temperature grid**; the tolerance is justified in §6.3.

### 6.1 Experimental comparisons

| Specimen | DOI | Quantity | Max deviation | Tolerance | Result |
|---|---|---|---|---|---|
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | `10.1007/s10854-019-01874-0` | power factor | **1.26 %** | 5 % | PASS |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | `10.1016/j.cap.2020.06.028` | power factor | **3.18 %** | 5 % | PASS |
| Si₈₀Ge₁₈Sb₂ | `10.1016/j.enconman.2015.01.082` | power factor | **2.37 %** | 5 % | PASS |
| Si₈₀Ge₂₀P₁ | `10.1021/acsami.9b20090` | power factor | **3.79 %** | 5 % | PASS |
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | `10.1007/s10854-019-01874-0` | figure of merit | **1.26 %** | 10 % | PASS |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | `10.1016/j.cap.2020.06.028` | figure of merit | **4.62 %** | 10 % | PASS |
| Si₈₀Ge₁₈Sb₂ | `10.1016/j.enconman.2015.01.082` | figure of merit | **2.74 %** | 10 % | PASS |
| Si₈₀Ge₂₀P₁ | `10.1021/acsami.9b20090` | figure of merit | **5.93 %** | 10 % | PASS |
| Si₈₀Ge₂₀P₁ | `10.1021/acsami.9b20090` | lattice κ (with the application's a-priori L = 2.44e-8) | **≤0.7 %** | 5 % | PASS |
| Si₈₀Ge₂₀P₁ | `10.1021/acsami.9b20090` | κₑ | — | 5 % | PASS |
| Si₈₀Ge₂₀P₁ | `10.1021/acsami.9b20090` | carrier concentration, carrier mobility | — | unit cross-check | PASS |

### 6.2 Arithmetic-consistency comparisons (explicitly **not** experimental)

| Specimen | Quantity | Deviation | Implied L | Classification |
|---|---|---|---|---|
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | lattice κ recomputed with L derived from the *same* publication's κ_L | 1.25 % | 1.6525e-8 | **consistency only** |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | lattice κ, same construction | 9.8 % | 1.276e-8 (spread **25 %**) | **UNVERIFIED** — the published κ/κ_L pair is not internally consistent |

### 6.3 Why these tolerances

| Comparison | Tolerance | Justification |
|---|---|---|
| power factor | 5 % | digitisation of the source figures ≈1 %; linear interpolation of S, σ and κ onto the published grid 1–2 % (these are curved properties); the publication's own rounding |
| figure of merit | 10 % | ZT accumulates the power-factor and thermal-conductivity contributions |
| lattice κ (a-priori L) | 5 % | isolates the arithmetic from the authors' unknown Lorenz assumption |
| lattice κ (derived L) | — | circular by construction; reported as a consistency check |

**This is the distinction the plan demanded:** a comparison in which the
reference value is derived from the same publication is an *arithmetic*
check of the published data and says nothing about the model. The registry
(`tests/experimental_benchmarks/registry.py`) encodes the classification
per grid, and `test_report_consistency.py` enforces it — a mis-classified
grid fails the suite.

### 6.4 The decisive model check — and its negative outcome

For the SiGe:P specimen the published κ, κ_L and σ imply a Lorenz number:

| Quantity | Value |
|---|---|
| L implied by the published data | **2.4579e-8 W·Ω/K²** |
| Sommerfeld L₀ | 2.4430e-8 W·Ω/K² — **agrees (within 0.6 %)** |
| Rigorous SPB L(η), acoustic scattering (λ = 0) | **1.592e-8 W·Ω/K²** — **disagrees by ≈35 %** |
| Kim empirical L(S) | tracks the acoustic model to +2.8 % |

**Consequence, stated plainly.** The published measurements of this specimen
do **not** support the embedded single-parabolic-band *acoustic-phonon*
model; they support the Sommerfeld value. The application's *default*
constant (2.44e-8) is the one that agrees with the data (≤0.7 % on κ_L).
The Seebeck-derived ("auto") Lorenz mode therefore inherits the acoustic
assumption's −35 % bias for this material and **must not** be described as
physically validated.

**The cause was identified in Phase 3** (see
`validation/remediation/SIGE_LORENZ_INVESTIGATION.md`): it is the
**scattering assumption**, not the implementation and not a failure of the
single-parabolic-band model. The published κ/κ_L pair is internally
consistent (3.0 % spread, at the 1.7 % digitisation noise floor — unlike
the PbTe pair, whose 25 % spread is the reason *that* comparison is
UNVERIFIED), and a scattering exponent **λ ≈ 1.41** — between
alloy/optical (1) and ionised-impurity (2) scattering, as expected for a
P-doped alloy — reproduces the published value **exactly**. The specimen
crosses the classical-to-degenerate transition (F₁⁄₂ from 0.29 to 2.24),
where the Lorenz number is strongly scattering-dependent.

**The model was not refitted.** The finding is preserved as a negative
result and is locked in by
`tests/scientific/test_sige_lorenz_finding.py`, which fails if the
acoustic value is ever made to agree with the measurement.

Lorenz-number sensitivity across the benchmark specimens (the deviation of
the SPB value from the value implied by the published data):

| Specimen | L implied by the data | pair spread | **κ_L sensitivity** to L = 2.44e-8 | **SPB deviation** (acoustic, λ = 0) |
|---|---|---|---|---|
| Si₈₀Ge₂₀P₁ | 2.4579e-8 | 3.0 % | 0.7 % | **−37.7 % … −25.2 %** (median −35 %) |
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | 1.6525e-8 | 3.4 % | 26.5 % | **−3.6 % … −1.5 %** |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | 1.2765e-8 | 24.9 % | 130.6 % | **+10.0 % … +46.0 %** |

The two right-hand columns are **different quantities** and were previously
conflated under a single "SPB deviation" header:

* the **κ_L sensitivity** is how much the *computed lattice thermal
  conductivity* changes when the application-wide constant is used instead of
  the implied Lorenz number. It is large because κ_L is a small difference
  of two comparable numbers;
* the **SPB deviation** is how far the rigorous acoustic-scattering SPB
  Lorenz number sits from the implied value.

Reproduce with `python tools/lorenz_diagnostics.py`.

**Consequence.** The SPB model performs **well** on the Bi₂Te₃ specimen
(≤3.6 %), is **15–38 % low** on P-doped SiGe (the case explained in §6.4),
and is **10–46 % high** on PbTe — where the implied Lorenz number is itself
unreliable (24.9 % spread), so no model conclusion can be drawn from that
specimen.

### 6.5 Physical-model plausibility of the SPB effective mass

The SPB inversion for P-doped SiGe yields **m\* = 1.49 – 2.23 mₑ (median
1.70 mₑ)**. This is physically reasonable for doped SiGe. It was **not**
cross-checked against a value stated in the publication: the abstract of
`10.1021/acsami.9b20090` does not report m\*, and the full text is not
openly available. This is therefore a *plausibility* statement, not a
validation.

---

## 7. Importer and GUI integration results (Phase XI)

### 7.1 Importers

| Importer | Coverage | Result |
|---|---|---|
| Four-probe | file parsing, column mapping, conductivity units, Seebeck units, invalid rows, temperature association, grouping, SEM, the calculation pipeline | PASS (16 tests) |
| Raw Seebeck | ΔV/ΔT regression, sign convention, unit conversion, temperature grouping, invalid and duplicate rows | PASS |
| Laser flash | thermal diffusivity, density, specific heat, thermal conductivity, missing/invalid fields | PASS |

**A distinction that matters.** The instrument files used are
*reconstructions* from the published benchmark curves — they reproduce a
real instrument **format**, and their contents are derived from published
data (checked by `test_instrument_reconstructions_derive_from_published_data`).
They are therefore **format/parsing** validation, not an independent
measurement-chain validation.

### 7.2 Multi-sample workflow

Multiple datasets, different compositions, independent calculations,
temperature alignment, comparison against published PF/ZT — **PASS**
(1.3–5.9 % against the published values of the same specimens; no mixing
of sample identities).

### 7.3 GUI

| Path | Coverage | Result |
|---|---|---|
| Spreadsheet recalculation (file → mapper → table → properties) | headless, full stack | PASS |
| Display units vs internal SI values | headless | PASS |
| Plot data preparation (sorting, error alignment) | headless | PASS |
| End-to-end desktop workflow (subprocess driver) | file → import → recalculation → render | PASS (4 tests, Qt venv) |
| Application startup smoke test | import + main-window construction | PASS (3 tests, Qt venv) |
| **Error-bar dialog** | interactive | **NOT IMPLEMENTED** — no automated coverage |
| **Kappa dialog** | interactive | **NOT IMPLEMENTED** |
| **SPB dialog** | interactive | **NOT IMPLEMENTED** |
| **Hall dialog** | interactive | **NOT IMPLEMENTED** |
| **Weighted-mobility dialog** | interactive | **NOT IMPLEMENTED** |
| **Multi-sample dialog** | interactive | **NOT IMPLEMENTED** |
| **Modal-dialog behaviour** | interactive | **NOT IMPLEMENTED** |
| **Clipboard paste** | interactive | **NOT IMPLEMENTED** |
| **Menus** | interactive | **NOT IMPLEMENTED** |
| **Plot export** | interactive | **NOT IMPLEMENTED** |

**Reason.** Each of these dialogs is opened with a modal `dialog.exec()`,
which blocks the event loop and cannot be driven headlessly by `QTest`
without refactoring the dialogs into a non-modal form. No such refactoring
was performed: it would change production code for testability alone,
outside the scope of this validation task.

---

## 8. Final status table

Legend for the evidence columns:
**A** = analytical (closed form / physical limit) · **N** = independent
numerical reference · **X** = published-measurement comparison ·
**—** = not applicable.

| Calculation | Equation verified | Independent reference | Unit tests | Physical validity | Status |
|---|---|---|---|---|---|
| Seebeck coefficient (regression) | S = ΔV/ΔT | A + N · 1e-12 | ✓ | sign preserved n/p | **VERIFIED** |
| Seebeck coefficient (single difference) | S = ΔV/ΔT | A | ✓ | — | **VERIFIED** |
| Seebeck slope standard error | s_e = √(SS_res/(n−2)/SS_xx) | A | — | — | **VERIFIED** |
| Resistivity from geometry | ρ = L/(R·A) | A + N · 1e-12 | ✓ | — | **VERIFIED** |
| Conductivity | σ = 1/ρ | A + N · 1e-12 | ✓ | — | **VERIFIED** |
| **Raw V/I → R → ρ → σ** | — | — | — | — | **NOT IMPLEMENTED** |
| Power factor | PF = S²σ | A + N · 1e-12 + X (1.26–3.79 %) | ✓ | PF ≥ 0 | **VERIFIED** |
| Electronic thermal conductivity | κₑ = LσT | A + N · 1e-12 | ✓ | W–F law; L-dependent | **VERIFIED** (conditionally physical) |
| Lattice thermal conductivity | κ_L = κ_total − κₑ | A + N · 1e-12 | ✓ | negative result **detected but not surfaced to the user** — see §3.3 | **PARTIALLY VERIFIED** — the validator exists and is tested, but no production path calls it (audit D-01) |
| Figure of merit | ZT = PF·T/κ_total | A + N · 1e-12 + X (1.26–5.93 %) | ✓ | ZT>0 for κ>0 | **VERIFIED** |
| Constant Lorenz number | L₀ = (π²/3)(k_B/e)² | A + N · 3e-11 | ✓ | — | **VERIFIED** |
| Kim empirical Lorenz | L(S) = (1.5+e^(−\|S\|/116))·10⁻⁸ | A + N · 1e-12 | ✓ | acoustic-scattering approximation only | **VERIFIED** (conditionally physical) |
| Rigorous SPB Lorenz | L(η) transport integrals | A + N · 2e-14 + limits | ✓ | model-dependent | **VERIFIED** (conditionally physical) |
| Fermi–Dirac integrals | F_j(η) | A + N · 1e-8 | — | branches documented | **VERIFIED** |
| SPB Seebeck vs η | S(η) | A + N · 1.5e-14 | ✓ | single band | **VERIFIED** (conditionally physical) |
| SPB inversion η from S | monotone root-find | A + N · 2.7e-6 | — | NaN when unbracketed | **VERIFIED** |
| SPB carrier concentration | n = N_c m*^{3/2} F_{1/2} | A + N · 5.8e-14 | ✓ | n>0 | **VERIFIED** |
| SPB effective mass | m* = [n/(N_c F_{1/2})]^{2/3} | A + N · 1.6e-8 | ✓ | 1.49–2.23 mₑ (plausibility only) | **PARTIALLY VERIFIED** (no published m* to check) |
| SPB round trips (n→S→n, m*→S→m*) | — | A + N · 1e-6 | — | — | **VERIFIED** (not experimental) |
| Weighted mobility | μ_w (Snyder form) | A + N · 8.3e-10 | ✓ | ≠ Hall mobility | **PARTIALLY VERIFIED** — physics UNVERIFIED |
| Hall coefficient | R_H = V_H t/(IB) | A + N · 1e-12 | ✓ | — | **VERIFIED** |
| Hall carrier density | n_H = r_H/(e\|R_H\|) | A + N · 1e-12 | ✓ | — | **VERIFIED** |
| Hall mobility | μ_H = \|R_H\|σ | A + N · 1e-12 | ✓ | — | **VERIFIED** |
| Scattering-exponent fit | μ ∝ T^p | A + N · 1e-9 | ✓ | — | **VERIFIED** |
| Laser flash thermal conductivity | κ = αC_pρ | A + N · 2e-16 | ✓ | — | **VERIFIED** |
| Dulong–Petit limit | C_V = 3nR | A + N · 2.3e-16 | ✓ | high-T only | **VERIFIED** |
| Device efficiency (η_max, η_eng, ZT̄, ZT_eng) | Ioffe / average-ZT | A + N · 1e-12 | ✓ | constant-property assumption | **VERIFIED** (conditionally physical) |
| Uncertainty — PF | u_PF = √((2Sσu_S)²+(S²u_σ)²) | A + N · 1e-12 + MC 5e-3 | ✓ | independence assumed | **VERIFIED** |
| Uncertainty — κₑ | u_κₑ (3 terms) | A + N · 1e-12 | ✓ | independence assumed | **VERIFIED** |
| Uncertainty — κ_L | u_κL = √(u_κ²+u_κₑ²) | A + N · 1e-12 | ✓ | independence assumed | **VERIFIED** |
| Uncertainty — ZT | u_ZT (relative form) | A + N · 1e-12 | ✓ | independence assumed | **VERIFIED** |
| Uncertainty — σ (geometry) | u_σ/σ | A + N · 1e-12 | ✓ | independence assumed | **VERIFIED** (not called by the app) |
| Uncertainty — κ (laser flash) | u_κ/κ | A + N · 1e-12 + MC 5e-3 | ✓ | independence assumed | **VERIFIED** |
| Uncertainty — ρ (density) | u_ρ/ρ | A + N · 1e-12 | ✓ | independence assumed | **VERIFIED** |
| Uncertainty — weighted mobility, SPB outputs | — | — | — | — | **NOT IMPLEMENTED** |
| Unit conversions (all quantities) | see §5 | A · 1e-12 | ✓ | unsupported units rejected (after SE-042) | **VERIFIED** |
| Physical-constraint validators | — | A | — | ✓ | **PARTIALLY VERIFIED** — the messages, severities and field names are verified, but the validators have **no production caller** (audit D-01) |
| Arrhenius fits | ln σ vs 1/T | A + N | — | — | **VERIFIED** |
| Multi-sample workflow | — | X (1.3–5.9 %) | ✓ | — | **VERIFIED** |
| Four-probe importer | — | format validation | ✓ | — | **VERIFIED** (parsing only) |
| Raw Seebeck importer | — | format validation | ✓ | — | **VERIFIED** (parsing only) |
| Laser-flash importer | — | format validation | ✓ | — | **VERIFIED** (parsing only) |
| Spreadsheet recalculation | — | G | ✓ | — | **VERIFIED** (integration) |
| Plot data preparation | — | G | ✓ | — | **VERIFIED** |
| GUI end-to-end (subprocess driver) | — | G | — | — | **VERIFIED** (integration) |
| Interactive dialogs (6), clipboard, menus, plot export | — | — | — | — | **UNVERIFIED** — no automated coverage. **Corrected:** five of the six dialogs are opened with `.show()` (non-modal) and are already `QTest`-driveable; only `ErrorBarDialog` and `PlotDataDialog` use modal `exec()` |
| Auto-Lorenz mode (physics) | L from S via SPB | — | — | contradicts published SiGe data by 35 % | **PARTIALLY VERIFIED** — implementation verified, physics contradicted |
| PbTe / degenerate-semiconductor regime | — | — | — | SPB L deviates by +10 % … +46 % from the implied value, but that implied value has a 24.9 % spread and is itself unreliable | **PARTIALLY VERIFIED** |
| Mg₂Sn, SnSe, CaMnO₃ experimental comparisons | — | — | — | — | **NOT IMPLEMENTED** — no protocol in this cycle |

### 8.1 Counts by status

| Status | Entries |
|---|---|
| VERIFIED | 39 |
| PARTIALLY VERIFIED (model-conditional, missing reference, or **not surfaced to the user**) | 6 |
| NOT IMPLEMENTED | 3 |
| UNVERIFIED | 1 (grouped: the 6 interactive dialogs + clipboard/menus/export) |
| **Total rows in the table above** | **49** |

> **Corrected 2026-11-12 (audit finding D-07).** This summary previously
> stated 5 PARTIALLY VERIFIED and a total of 50, while the table above
> contains 49 rows with 4 PARTIALLY VERIFIED. Two rows were then reclassified
> after the Phase 1 audit found that the negative-lattice-conductivity
> diagnostic is never surfaced to the user (§3.3), giving 39 / 6 / 3 / 1.
>
> **Scope note.** This table is a *per-calculation* view. The canonical
> classification is **per equation** (62 entries) in
> [`remediation/EQUATION_STATUS_MAPPING.csv`](remediation/EQUATION_STATUS_MAPPING.csv)
> and [`remediation/VALIDATION_STATUS.md`](remediation/VALIDATION_STATUS.md),
> which use the four evidence categories required by the validation brief
> (numerically verified / numerically verified but physically conditional /
> experimentally benchmarked within a defined scope / not yet validated).
> The 62-vs-49 difference is explained in `VALIDATION_STATUS.md` §6 and is
> guarded by `tests/scientific/test_equation_status_mapping.py`.

---

## 9. Reproducibility

- Every number above is regenerable with the commands in §1.3.
- The benchmark datasets regenerate **byte-identically** from the upstream
  StarryData snapshot (SHA-256 of the upstream files recorded in
  `docs/EXPERIMENTAL_BENCHMARK_VALIDATION.md`).
- The reference-comparison table regenerates with
  `tools/generate_reference_comparison.py`; the material-family survey with
  `tools/survey_material_families.py`.
- `tests/experimental_benchmarks/test_report_consistency.py` re-measures the
  test counts and verifies that the registry, the on-disk datasets and **both**
  validation reports agree — a report that drifts from the code fails the
  suite.
- The Monte-Carlo reference uses a fixed seed (20261112) and a fixed sample
  count (200 000).
- **Not reproduced by CI:** the GitHub Actions workflow
  (`.github/workflows/tests.yml`) has never been executed, because no push
  has been performed. The results in this document come from local runs.

---

## 10. What this does **not** establish

Stated explicitly, because a green suite is easy to over-read:

1. **It does not establish that the physical models are right.** The SPB
   implementation is verified; the SPB *model* is contradicted by the one
   specimen whose published data can decide the question.
2. **It does not establish experimental validity for every material family.**
   Four specimens were used; three families have no active comparison.
3. **It does not cover the interactive GUI.** Six dialogs, the clipboard,
   the menus and the plot export have no automated coverage.
4. **It does not cover a raw measurement chain.** The application does not
   implement V/I → R → ρ → σ; the instrument files are format reconstructions
   derived from published curves.
5. **It does not establish that the uncertainty model is complete.**
   Independence is assumed everywhere; no covariance is modelled.
6. **It says nothing about the provenance of the published data themselves.**
   The benchmarks inherit the digitisation uncertainty of the source
   figures (≈1 %), and the publications' own uncertainties are unknown.
