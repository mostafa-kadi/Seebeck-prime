# Validation Status — Seebeck Prime

**Version:** 1.0
**Date:** 2026-11-12
**Phase:** 2 (validation reconciliation)
**Machine-readable mapping:**
[`EQUATION_STATUS_MAPPING.csv`](EQUATION_STATUS_MAPPING.csv) (62 rows, one per
registry equation)
**Guard:** `tests/scientific/test_equation_status_mapping.py` — the counts in
this document, the mapping and the equation registry are verified against each
other on every test run.

---

## 0. How to read this document

Every implemented calculation is placed in **exactly one** of four categories.

The categories are assigned by a fixed rule, so the classification is
mechanical rather than editorial:

| Category | Rule |
|---|---|
| **1 — Numerically verified** | The relation is confirmed against an independent reference implementation and/or an analytic limit, **and** it carries no material-model assumption that can fail for some specimen, **and** no experimental claim is made. |
| **2 — Numerically verified but physically conditional** | The relation is confirmed numerically, but the *result* depends on a physical/model assumption (single band, single carrier, acoustic scattering, constant Lorenz number, isotropic transport, high-temperature limit) or is restricted to a narrow validated scope. |
| **3 — Experimentally benchmarked within a defined scope** | The calculation is compared with an independently published measurement of the **same specimen**, and the scope of that comparison is stated. |
| **4 — Not yet validated** | The calculation does not exist, has no automated coverage, or the available evidence is insufficient. |

**The term "fully validated" is not used anywhere in this document**, because
no calculation in this project currently satisfies every requirement of its
physical applicability *and* has an experimental confirmation across its
stated domain. A green test run is not validation.

### 0.1 The three status axes

Each equation carries three *independent* status axes, because a single
status cannot express the actual state:

| Axis | Question it answers |
|---|---|
| **Numerical validation** | Does the software compute what the equation says? |
| **Physical applicability** | Does the equation describe the material/regime it is applied to? |
| **Experimental validation** | Does the software reproduce an independently published measurement? |

The category is derived from the three axes; the axes are what the CSV
records.

---

## 1. Summary

| Category | Count |
|---|---|
| 1 - Numerically verified | 31 |
| 2 - Numerically verified but physically conditional | 23 |
| 3 - Experimentally benchmarked within a defined scope | 5 |
| 4 - Not yet validated | 3 |
| **Total** | **62** |

| Registry section | Equations | Cat 1 | Cat 2 | Cat 3 | Cat 4 |
|---|---|---|---|---|---|
| 1 Core transport | E-01…E-07 | 0 | 3 | 4 | 0 |
| 2 Uncertainty propagation | E-08…E-15 | 7 | 1 | 0 | 0 |
| 3 Units | E-16…E-22 | 6 | 1 | 0 | 0 |
| 4 SPB model | E-23…E-29 | 1 | 6 | 0 | 0 |
| 5 Hall | E-30…E-34 | 1 | 4 | 0 | 0 |
| 6 Phonon / laser flash | E-35 | 0 | 1 | 0 | 0 |
| 7 Device efficiency | E-36…E-38 | 0 | 3 | 0 | 0 |
| 8 Transport / analysis / validation | E-39…E-42 | 3 | 1 | 0 | 0 |
| 9 Data-processing workflows | E-43…E-52 | 7 | 2 | 1 | 0 |
| 10 GUI / presentation | E-53…E-58 | 2 | 1 | 0 | 3 |
| 11 Retired legacy / compatibility | E-59…E-62 | 4 | 0 | 0 | 0 |
| **Total** | **62** | **31** | **23** | **5** | **3** |

---

## 2. Category 3 — Experimentally benchmarked within a defined scope

**5 equations.** These are the only ones for which an independently published
measurement exists. **The scope is stated in every case and is narrow.**

| ID | Calculation | Published reference | Scope of the comparison |
|---|---|---|---|
| **E-01** | Power factor | 4 specimens, 3 DOIs | PF compared with the published PF curve for the same `(SID, sample_id)`. Max deviation **1.26 %** (Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆), **3.18 %** ((PbTe)₀.₉₅(PbS)₀.₀₅), **2.37 %** (Si₈₀Ge₁₈Sb₂), **3.79 %** (Si₈₀Ge₂₀P₁). Tolerance 5 %. |
| **E-02** | Electronic thermal conductivity | Si₈₀Ge₂₀P₁ only (`10.1021/acsami.9b20090`) | κₑ compared with the published electronic thermal conductivity. **One specimen.** |
| **E-03** | Lattice thermal conductivity | Si₈₀Ge₂₀P₁ only | κ_L computed with the application's **a-priori** L = 2.44e-8 (not derived from the published κ_L) → **≤ 0.7 %**. For the Bi₂Te₃ and PbTe datasets the Lorenz number *is* derived from the same publication's κ_L, so those comparisons are **arithmetic consistency checks, not experimental validation**. |
| **E-04** | Figure of merit | 4 specimens, 3 DOIs | ZT compared with the published ZT curve. Max deviation **1.26 % / 4.62 % / 2.74 % / 5.93 %**. Tolerance 10 %. |
| **E-44** | Multi-sample preparation | 4 specimens | The multi-sample workflow reproduces the published PF and ZT (1.26–5.93 %) with no mixing of sample identities. |

### 2.1 What the experimental evidence does **not** cover

- **No measurement direction.** StarryData's `sample_info` does not record the
  measurement direction for any benchmark sample (the `ThermalMeasurement`,
  `ElectricalMeasurement` and `Other` fields are empty strings). The direction
  therefore **cannot be asserted** for any benchmark.
- **No scattering assumptions.** Likewise absent from the source and from the
  aggregated publication metadata. No benchmark can support an SPB-based
  claim.
- **No published measurement uncertainties.** The practical accuracy floor is
  the ≈1 % digitisation uncertainty of the source figures.
- **Four specimens, three publications.** Not a material survey. The other
  requested families (Mg₂Sn, SnSe, CaMnO₃) are surveyed with real DOIs in
  `SCIENTIFIC_BENCHMARK_MATERIAL_FAMILIES.md` but are **not** active
  benchmarks, for reasons given in §5.3 of that document.

### 2.2 The negative result inside this category

**E-02 / E-03 / E-06 share one unresolved finding.** For Si₈₀Ge₂₀P₁ the
published κ, κ_L and σ imply **L = 2.4579e-8 W·Ω/K²** — the Sommerfeld value.
The application's SPB acoustic-phonon model gives **1.592e-8**, i.e. **−35 %**.
The application's *default* constant 2.44e-8 is the value that agrees with the
published data.

This is **not** a coding defect — the SPB implementation was independently
re-derived and agrees with the textbook transport-integral form to 1.4e-14
(`validation/remediation/INITIAL_STATE_AUDIT.md` §5.4).

**The cause was identified in Phase 3**
(`remediation/SIGE_LORENZ_INVESTIGATION.md`): the **scattering
assumption**. The published κ/κ_L pair is internally consistent (3.0 %
spread, at the digitisation noise floor), and **λ ≈ 1.41** — between
alloy/optical and ionised-impurity scattering, as expected for a P-doped
alloy — reproduces the published value exactly. The model was **not**
refitted; the negative result is locked in by
`tests/scientific/test_sige_lorenz_finding.py`.

---

## 3. Category 2 — Numerically verified but physically conditional

**23 equations.** Every one of these is confirmed numerically to ≤1e-6
relative error (usually ≤1e-12). The qualifier concerns the *physics*, not the
arithmetic.

| ID | Calculation | The condition that can fail |
|---|---|---|
| E-05 | Kim empirical Lorenz number | **Acoustic-phonon scattering only.** +2.8 % vs the rigorous SPB value at \|S\| = 150 µV/K; **−21.7 %** (optical/alloy), **−31.8 %** (ionised impurity). |
| E-06 | Rigorous SPB Lorenz number | Single parabolic band; λ = r + ½. Contradicted by the SiGe:P published data (see §2.2). |
| E-07 | Formula mass / Dulong–Petit limit | The Dulong–Petit limit is a **high-temperature** classical limit; the formula parser accepts only unbracketed `Element[Count]` syntax. |
| E-12 | σ uncertainty from geometry | Presupposes **σ = L/(R·A)** for a rectangular specimen with uniform current. Also not exercised by any production path (audit D-09). |
| E-22 | Thermal-conductivity conversion | **Scope-limited:** only W/(m·K) is supported. The converter now *rejects* other units rather than mis-scaling them (SE-042). |
| E-24 | S(η) | Single parabolic band. |
| E-25 | η from S | Inherits E-24; the metallic-limit saturation at η = 50 is a convention. |
| E-26 | SPB carrier concentration | Single band; N_c ∝ T^{3/2}. **No independent experimental comparison** of the application's n against a published n. |
| E-27 | SPB effective mass | Inherits the assumed λ. **Plausibility only** (1.49–2.23 mₑ, median 1.70 mₑ) — no publication states an m\* to check against. |
| E-28 | Pisarenko curve / optimal transport | Single band + an acoustic-phonon mobility parameter μ₀. |
| E-29 | Empirical carrier-concentration estimator | Empirical fit in \|S\|; no temperature dependence. |
| E-30 | Hall coefficient | Single carrier, flat sample, uniform current. |
| E-31 | Hall carrier density | **Hall factor r_H = 1** assumed unless supplied. |
| E-33 | Hall mobility | Single carrier, r_H = 1. **Must not be presented as the weighted mobility (E-39).** |
| E-34 | Scattering-exponent fit | Assumes a single power law µ ∝ T^p over the fitted range; no goodness-of-fit threshold. |
| E-35 | Thermal conductivity from laser flash | Presupposes **one-dimensional heat flow in a homogeneous specimen**. |
| E-36 | Average figure of merit | Constant-property interpolation onto [T_c, T_h]. |
| E-37 | Maximum (Ioffe) efficiency | Constant-property average ZT. |
| E-38 | Engineering figure of merit | Constant-property average; dimensionally corrected after SE-001. |
| E-39 | Weighted mobility | Assumes acoustic-phonon transport; the formula is verified, the **physics has no experimental reference** (the only published mobility curve is negative and unusable). |
| E-43 | Property suite from measured inputs | The derived κₑ / κ_L / ZT **inherit the Lorenz-number assumption** (E-02). |
| E-51 | SPB batch rows and mean parameters | Inherits the SPB single-band assumption; the mean-pairing rule is legacy (SE-034). |
| E-53 | Spreadsheet recalculation | Inherits E-43, and therefore the Lorenz-number assumption. |

---

## 4. Category 1 — Numerically verified

**31 equations.** Confirmed against an independent reference implementation
and/or an analytic limit, with no material-model assumption that can fail for
some specimen, and no experimental claim made.

| ID | Calculation | Evidence |
|---|---|---|
| E-08 | PF uncertainty | independent reference ≤1e-12; Monte-Carlo ≤5e-3 |
| E-09 | κₑ uncertainty | independent reference ≤1e-12 |
| E-10 | κ_L uncertainty | independent reference ≤1e-12 |
| E-11 | ZT uncertainty | independent reference ≤1e-12 |
| E-13 | Laser-flash κ uncertainty | independent reference ≤1e-12; Monte-Carlo ≤5e-3 |
| E-14 | Density uncertainty | independent reference ≤1e-12 |
| E-15 | Relative-uncertainty combiner | root-sum-square asserted explicitly |
| E-16 | Temperature conversion | round trip ≤1e-12; offset 273.15 exact |
| E-17 | Conductivity conversion | round trip ≤1e-12; exact factors 100, 100/ρ |
| E-18 | Seebeck conversion | round trip ≤1e-12 for all spellings |
| E-19 | Power-factor conversion | round trip ≤1e-12 for all spellings |
| E-20 | Carrier-concentration conversion | exact 1e-6/1e6; the published m⁻³ interpretation was independently confirmed via µ = σ/(n·e) |
| E-21 | Uncertainty conversions | linear for S/PF; u_σ = u_ρ·100/ρ² for Ω·cm |
| E-23 | Fermi–Dirac integral | independent quadrature ≤1e-8; F₀ = ln(1+e^η) to 1e-12 |
| E-32 | Carrier type from the Hall sign | explicit sign convention |
| E-40 | Resistivity conversion to mΩ·cm | exact factors |
| E-41 | Analysis helpers | OLS slope/stderr vs a closed form ≤1e-12 |
| E-42 | Physical-constraint validators | messages, severities and field names |
| E-45 | Four-probe import | parsing, units, grouping, SEM, invalid rows |
| E-46 | Raw Seebeck import | regression ≤1e-12, sign, grouping, invalid/duplicate rows |
| E-47 | Laser-flash import | unit handling, missing/invalid fields |
| E-48 | Geometry uncertainty combination | independent formula ≤1e-12 |
| E-49 | Reference-Seebeck uncertainty combination | independent formula |
| E-50 | Column mapping with plausibility guards | alias matching and guards (SE-031) |
| E-52 | Arrhenius activation energies | recovered exactly from synthetic data |
| E-54 | Display-unit rendering vs internal SI | to_base(from_base(x)) ≡ x for every supported unit |
| E-55 | Plot-data preparation | ordering and error-bar alignment |
| E-59 | Legacy calculation wrappers (retired 2026-11-13) | the shim was verified pure delegation before deletion; its numerical assertions run unchanged against the canonical surface |
| E-60 | Legacy constant aliases (retired 2026-11-13) | the legacy Lorenz alias was verified to equal the application-wide 2.44e-8 before deletion; the constants live on in `domain/physical_constants.py` |
| E-61 | Legacy multi-sample orchestration (retired 2026-11-13) | the wrapper was verified pure delegation before deletion; the canonical workflows are covered by `test_batch_workflows.py` |
| E-62 | Legacy presentation logic aliases (retired 2026-11-13) | the alias modules were verified pure delegation before deletion; the canonical presentation modules are covered by `test_architecture_dependencies.py` |

### 4.1 Three important qualifications inside category 1

**E-42 (physical-constraint validators) — the validator is verified, its
*reach* is not.** `validate_kappa_l_array()` correctly emits a `WARNING` for a
negative lattice thermal conductivity, and `validate_measurement_data()`
forwards it — but **no production code path calls either function**
(`src/gui/main_window.py:363-368` writes κ_L straight into the table). The
negative-κ_L diagnostic therefore never reaches the user. This is audit
finding **D-01** and is scheduled for Phase 3. The registry's earlier claim
that reachability was VERIFIED is **withdrawn**.

**E-45 / E-46 / E-47 (importers) — parsing validation only.** The instrument
files used in the importer tests are **reconstructions** derived from the
published benchmark curves; they reproduce a real instrument *format* and are
checked for that by
`test_report_consistency.py::test_instrument_reconstructions_derive_from_published_data`.
They are **not** real instrument exports and must never be presented as
instrument validation. The raw V/I → R → ρ → σ chain (E-58) does not exist.

**E-59 … E-62 (legacy surfaces) — delegation only, now retired.** These entries
verified that the compatibility wrappers return the domain results unchanged;
the wrappers were deleted in the architecture migration (2026-11-13) and every
numerical assertion of their test now runs against the canonical surfaces
(`tests/test_canonical_calculations_surface.py`, `tests/test_batch_workflows.py`).
Their scientific content, and its physical conditions, belong to the entries
they delegated to (E-01…E-04, E-44).

---

## 5. Category 4 — Not yet validated

**3 equations.**

| ID | Item | Why it is not validated | What is needed |
|---|---|---|---|
| **E-56** | Interactive calculation dialogs (error bar, Kappa, SPB, Hall, weighted mobility, multi-sample) | **No automated coverage of any dialog.** | QTest coverage. **Corrected note:** five of the six are opened with `.show()` (non-modal) and are already `QTest`-driveable; only `ErrorBarDialog` (`main_window.py:292`) and `PlotDataDialog` (`:779`) use modal `exec()` and need a refactor. The registry previously attributed the gap to modality for all six - that was inaccurate. |
| **E-57** | Clipboard paste, menus, plot export | Interactive-only paths; no automated coverage. | QTest coverage for the non-modal actions; the modal export path needs the same refactor as E-56. |
| **E-58** | Raw V/I → R → ρ → σ measurement chain | **Not implemented.** `process_four_probe_table()` requires a conductivity column; geometry is used only for the *uncertainty* of an already-measured σ. | A separate, modular measurement workflow with an explicit two- vs four-terminal distinction, an explicit geometry model, uncertainty propagation, raw-value preservation, a calculation history and export — built with independent references and tests **before** any GUI integration. |

---

## 6. Why the registry lists 62 equations and this document classifies 62 entries

They are the same 62 — the counts are not in conflict. The apparent
62-vs-49 discrepancy in the earlier report came from comparing **two different
artefacts that counted different things**:

| Artefact | What it counts | Number |
|---|---|---|
| `SCIENTIFIC_EQUATION_REGISTRY.md` | **Equations** — 35 equation entries, 7 unit-conversion entries, 10 workflow entries, 6 GUI/presentation entries, 4 legacy-compatibility entries | **62** |
| `SCIENTIFIC_CALCULATION_TEST_RESULTS.md` §8 | **Calculations with a scientific status** — related equations *grouped* into one row; legacy and GUI entries without an independent physical status *omitted*; four rows *added* that have no registry entry (the missing weighted-mobility/SPB uncertainties and the three inactive material families) | **49** |

The earlier §8.1 summary table additionally claimed **5** PARTIALLY VERIFIED
entries against its own table's **4**, and a total of **50** against **49**.
That arithmetic error is corrected in the results report (audit finding D-07).

**The mapping CSV is now the single bridge between the two**, and the guard
test verifies that the registry, the mapping and this document agree.

---

## 7. Test accounting (reproduced locally, 2026-11-12)

| Group | Collected | Passed | Skipped |
|---|---|---|---|
| `tests/scientific/` — independent references, physical constraints, unit matrix, edge cases, **mapping guard** | 156 | 156 | 0 |
| `tests/experimental_benchmarks/` — published measurement, importers, workflows, GUI e2e, report consistency | 113 (+1 module skip) | 109 | 5 |
| `tests/test_*.py` — root engineering / unit / audit suites | 343 | 342 | 1 |
| **Total** | **612 (+1)** | **607** | **6** |

### 7.1 Every skip, and whether it is environmental or scientific

| # | Test | Reason | Class |
|---|---|---|---|
| 1 | `test_gui_end_to_end.py` (module, 4 tests) | conda base environment: `ImportError: DLL load failed while importing QtWidgets` (Windows `0xc0000139`). Root cause identified in `INITIAL_STATE_AUDIT.md` §5.1: conda-forge's `anaconda3\Library\bin\Qt6Core.dll` shadows the pip `PyQt6-Qt6 6.11.1` runtime. **The same 4 tests pass in the Qt-capable venv.** | **environmental** |
| 2 | `test_startup_smoke.py::test_import_main_smoke_when_qt_available` | Same cause. **Passes in the venv.** | **environmental** |
| 3 | `test_benchmarks.py:275` | `sige_si80ge18sb2`: no published lattice thermal conductivity | **missing reference data** |
| 4 | `test_benchmarks.py:326` | `sige_si80ge18sb2`: no published lattice thermal conductivity | **missing reference data** |
| 5 | `test_benchmarks.py:292` | `pbte_pbte0_95pbs0_05`: the published κ and κ_L imply a Lorenz number with a 25 % spread — limited by the source data, not by the calculation | **missing reference data** |
| 6 | `test_workflow_validation.py:204` | the published carrier-mobility curve is negative (physically impossible) and unusable | **unusable reference data** |

**2 of 6 skips are environmental and are covered by the venv run (7 GUI tests
pass there). 4 of 6 are scientific gaps** that no software testing can close;
they correspond directly to the "NONE — no usable published reference"
entries in the mapping.

### 7.2 Environment

| Item | Primary | Qt-capable venv |
|---|---|---|
| Python | 3.13.9 (Anaconda, Win10 19045) | 3.13.9 (venv) |
| NumPy / SciPy / pandas / matplotlib | 2.3.5 / 1.17.1 / 3.0.2 / 3.10.9 | — |
| PyQt6 / Qt | 6.11.0 / 6.11.1 — **QtWidgets fails to load** | 6.9.1 / 6.9.0 — **works** |
| Command | `C:\Users\Elkady\anaconda3\python.exe -m pytest -q -p no:cacheprovider` | `…\seebeck-gui\Scripts\python.exe -m pytest …` |

The two environments differ only in the Qt build. The reproducible remedy for
the broken environment is to build the application environment as a **venv**,
not a conda base environment.

---

## 8. Changes made to the shipped validation records in this phase

| # | Record | Change |
|---|---|---|
| 1 | `validation/SCIENTIFIC_CALCULATION_TEST_RESULTS.md` §8.1 | Corrected the counts: PARTIALLY VERIFIED **5 → 4**, total **50 → 49** (audit D-07). |
| 2 | `validation/SCIENTIFIC_CALCULATION_TEST_RESULTS.md` §8 | The row for E-03/E-42 no longer claims that the negative-κ_L diagnostic reaches the user; it now states that it does not (audit D-01). |
| 3 | `validation/SCIENTIFIC_EQUATION_REGISTRY.md` E-03 | "negative-result flagging (VERIFIED)" → the claim is corrected: the validator is verified, its **reach** is not. |
| 4 | `validation/SCIENTIFIC_EQUATION_REGISTRY.md` E-42 | "reachability" removed from the verified list. |
| 5 | `validation/SCIENTIFIC_EQUATION_REGISTRY.md` E-56 | The reason is corrected: five of the six dialogs are non-modal and `QTest`-driveable; only two are modal. |
| 6 | `validation/SCIENTIFIC_EQUATION_REGISTRY.md` E-12 | The cross-reference "(see E-24)" is corrected to point at E-39/E-48 (the weighted-mobility and geometry-uncertainty entries). |
| 7 | `validation/SCIENTIFIC_EQUATION_REGISTRY.md` §12 | The register summary is replaced by a pointer to this document and the mapping CSV. |
| 8 | `validation/SCIENTIFIC_EQUATION_REGISTRY.md` E-03/E-42 | The negative-κ_L reachability defect (D-01) is recorded as an open defect, not as a verification. |

**No production code was changed in this phase.**
