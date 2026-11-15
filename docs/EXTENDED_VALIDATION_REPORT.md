# Extended Validation Report — Seebeck Prime

**Date:** 2026-11-11 (final scientific validation audit)
**Scope:** the extended validation phase — the Seebeck-derived ("auto") Lorenz mode, the three instrument importers, the multi-sample workflow, the weighted mobility, the SPB inversion and the desktop workflow.
**Companion document:** `EXPERIMENTAL_BENCHMARK_VALIDATION.md` (Part I — the calculation engine).
**Canonical dataset list:** `tests/experimental_benchmarks/registry.py` (single source of truth; a test verifies that the registry, the on-disk datasets and both reports agree).

### Datasets used in this report

| Benchmark id | Family | Composition | DOI | Comparison kinds |
|---|---|---|---|---|
| `b2te3_bi2te2_4se0_6cu0_006` | Bi2Te3-based | Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | 10.1007/s10854-019-01874-0 | pf, zt (experimental); kappa_l (consistency) |
| `pbte_pbte0_95pbs0_05` | PbTe-based | (PbTe)₀.₉₅(PbS)₀.₀₅ | 10.1016/j.cap.2020.06.028 | pf, zt (experimental); kappa_l (consistency, noise-limited) |
| `sige_si80ge18sb2` | SiGe-based | Si₈₀Ge₁₈Sb₂ | 10.1016/j.enconman.2015.01.082 | pf, zt (experimental) |
| `sige_si80ge20p1` | SiGe-based | Si₈₀Ge₂₀P₁ | 10.1021/acsami.9b20090 | pf, zt, kappa_l, kappa_e, n, μ (experimental) |

---

## 1. Purpose and method

This report was written under peer-review conditions: every claim was
re-checked against the repository, and claims that did not survive the
re-check were corrected rather than defended. Three corrections of substance
were made in the process and are recorded below:

1. The **lattice-thermal-conductivity comparison is circular** and has been
   re-labelled an *arithmetic consistency check* (§5).
2. The **Seebeck-derived ("auto") Lorenz mode is not experimentally
   validated** by the available data; the published measurements actually
   *contradict* the single-parabolic-band acoustic-phonon model for the
   available SiGe sample by ≈35 % (§4.3).
3. The **weighted mobility is not experimentally validated** at all, because
   the only published reference curve in the datasets is unusable (§7.2).

The numerical agreement of the software with an independent implementation is
reported throughout as *independent numerical verification*, never as
experimental validation.

---

## 2. Classification of every result

The seven categories below are used consistently in both reports.

| Category | Definition | What it may and may not claim |
|---|---|---|
| **M** — mathematical verification | The expression is checked against a closed-form identity or an analytic limit (e.g. F₀(η) = ln(1+e^η); C_V = 3nR; μ = σ/(n·e)). | Establishes that the *formula* is right. Says nothing about the software or the physics of a sample. |
| **N** — independent numerical verification | The software is compared with an implementation of the *same* equation written independently (different code, different quadrature, different inversion bracket). | Establishes that the software computes what the equation says. **Is not experimental validation.** |
| **E** — experimental benchmark validation | The software is compared with an independently published *measurement* that was not used to derive anything in the comparison. | The strongest evidence available here. Applies to the power factor, the figure of merit, the lattice conductivity computed with an a-priori constant, and the carrier-data unit cross-check. |
| **P** — instrument-file parsing validation | An importer is exercised with a file in an instrument export *format*. | Establishes that the parser extracts, converts, groups and regresses correctly. **Is not a measurement-chain validation** and not an experimental validation. |
| **M-chain** — measurement-chain validation | The full chain from a raw instrument signal to a transport property (raw V/I → R → ρ → σ). | **Not applicable: the application does not implement this chain** (§6.2). |
| **G** — GUI integration validation | The application stack is driven headlessly (file → mapper → spreadsheet → recalculation → rendering). | Establishes that the desktop workflow is wired correctly. **Is not interactive-GUI validation** (§8). |
| **P-model** — physical model validation | Whether the *underlying model* (single parabolic band, Wiedemann–Franz, the Kim fit) describes the real material. | The strongest and least comfortable category: it is where the published data disagree with the model (§4.3, §7.1). |

### 2.1 Classification of the individual results

| # | Result | Category | Verdict |
|---|---|---|---|
| R1 | PF = S²σ, κₑ = LσT, κ_L = κ−κₑ, ZT = PF·T/κ reproduced by an independent implementation (≤1e-9) | N | pass |
| R2 | F_j(η) equals Γ(j+1)×Blatt integral; F₀(η) = ln(1+e^η) | M | pass |
| R3 | Seebeck ↔ η inversion round trip; classical limit S = (k_B/e)(2−η) | M | pass |
| R4 | Rigorous SPB L(η) matches an independent transport-integral evaluation; limits L₀ (degenerate) and 2(k_B/e)² (non-degenerate) | M, N | pass |
| R5 | Empirical Kim fit vs. rigorous SPB value for λ = 0, 1, 2 | M, N | pass (agreement and its breakdown quantified) |
| R6 | Fermi–Dirac quadrature accuracy after the SE-039 fix | N | pass |
| R7 | Published **power factor** vs computed, four datasets | **E** | pass, 1.3–3.8 % |
| R8 | Published **figure of merit** vs computed, four datasets | **E** | pass, 1.3–5.9 % |
| R9 | Published **lattice κ** vs computed with the a-priori constant L = 2.44e-8 (SiGe) | **E** | pass, ≤0.7 % |
| R10 | Published **σ, n, μ** mutual consistency (μ = σ/(n·e)) | **E**, M | pass (median ratio 1.08) → confirms the carrier-density units |
| R11 | Published **ZT** of the single-phase SiGe:P reference vs the paper's composite value | **E** | context only |
| R12 | κ_L recomputed with an L *derived from* the published κ_L | **arithmetic consistency** (not E) | pass, but circular by construction |
| R13 | SPB inversion vs an independent implementation; round trip n→m*→n | N | pass (≤1e-6, exact round trip) |
| R14 | SPB-inverted m\* = 1.70 m_e for P-doped SiGe | P-model | plausible; **not cross-checked against a value stated in the publication** (§7.1) |
| R15 | Weighted mobility vs an independent implementation | N | pass (≤1e-9) |
| R16 | Weighted mobility vs the published carrier mobility | **none** | **UNVERIFIED** — the published curve is negative (§7.2) |
| R17 | Importers on reconstructed instrument-format files (T association, unit conversion, sign, regression, grouping, invalid rows, geometry uncertainty) | P | pass |
| R18 | Raw V/I → R → ρ → σ chain | M-chain | **UNVERIFIED** — not implemented (§6.2) |
| R19 | Multi-sample workflow vs published PF/ZT | **E** | pass, 1.3–5.9 % |
| R20 | Desktop workflow headless (file → mapper → table → recalculation → rendering) | G | pass (4 tests) |
| R21 | Interactive dialogs (error bars, Kappa, SPB, Hall, weighted mobility, multi-sample) | — | **UNVERIFIED** — modal, no automated coverage (§8) |
| R22 | SPB single-band model vs the published SiGe Lorenz number | P-model | **fails by ≈35 %** (§4.3) |
| R23 | Published carrier-mobility curve of the Bi₂Te₃ sample | — | **unusable** (negative values) |

---

## 3. Reconciling the reports

| Discrepancy | Resolution |
|---|---|
| Part I listed **three** datasets, Part II used **four** | Both reports now list the same **four** datasets from `registry.py`; the registry is the single source of truth and a test enforces that the on-disk data and both reports match it |
| The first version of the extended suite reported "100 passed" | The measured counts are now stated per module and in total, and a test re-measures them and compares them with the text of both reports |
| The "27 passed, 3 skipped" figure referred only to the core benchmark module | Both figures are now given: the core module and the whole benchmark directory |
| The lattice-κ comparison was described as an experimental validation | Re-labelled an **arithmetic consistency check** (§5) and removed from the experimental list |
| The SPB effective mass was described as "experimentally consistent" | Re-described as a **physical-model plausibility check**; the publication's own effective mass could not be retrieved, so it is not claimed (§7.1) |

---

## 4. Review of the Lorenz validation

### 4.1 Two different quantities must not be conflated

| | Empirical ("auto") estimate | Rigorous SPB value |
|---|---|---|
| Formula | L(S) = (1.5 + e^(−\|S\|/116))·10⁻⁸ | L(η) = (k_B/e)²[((λ+3)F_{λ+2})/((λ+1)F_λ) − (((λ+2)F_{λ+1})/((λ+1)F_λ))²] |
| Nature | Empirical fit in the measured Seebeck coefficient | First-principles transport-integral expression in the single-parabolic-band model |
| Inputs | \|S\| only | η, i.e. the reduced Fermi level, and the scattering exponent λ |
| Status in this report | N/M verified | M/N verified |

The two are **not** interchangeable and are never mixed in a single claim.

### 4.2 Scattering assumptions

The application's default λ = 0 corresponds to acoustic-deformation-potential
scattering (r = −1/2); λ = 1 (optical/alloy) and λ = 2 (ionised impurity,
r = +3/2) are selectable. The verification shows the empirical fit tracks the
rigorous value only in the regime it was fitted for:

| Scattering | Deviation of the empirical fit from the rigorous SPB value (at \|S\| = 150 µV/K) |
|---|---|
| λ = 0 (acoustic) | **+2.8 %** |
| λ = 1 (optical/alloy) | **−21.7 %** |
| λ = 2 (ionised impurity) | **−31.8 %** |

The auto mode therefore inherits the *scattering* assumption of the fit; it
cannot detect that the material is not phonon-limited. This is a **model
limitation**, not an implementation defect.

### 4.3 Which comparisons are theoretical and which are experimental?

* Everything in §4.1–4.2 is **theoretical / mathematical** (categories M
  and N): the relations are checked against independent implementations and
  analytic limits. No measurement enters.
* The only experimental statement that touches the Lorenz number is R9/R22:
  the published thermal conductivity, lattice thermal conductivity and
  conductivity of the Si₈₀Ge₂₀P₁ sample imply

      L_implied = 2.458e-8 W·Ω/K²

  which coincides with the **Sommerfeld value** (2.443e-8, within 0.6 %),
  whereas the rigorous SPB value for the same sample is

      L_SPB = 1.592e-8 W·Ω/K²   (≈ −35 % away)

  **Interpretation.** The published measurements are consistent with the
  authors having used the Sommerfeld constant, and are *inconsistent* with
  the single-parabolic-band acoustic-phonon model for this material. The
  published data therefore **do not validate the auto-Lorenz estimate**; on
  the contrary, if the SPB model described this sample, the auto estimate
  would miss the published lattice conductivity by about 35 % in L. The
  application's default constant (L = 2.44e-8) is the one that agrees with
  these measurements (≤0.7 % on κ_L, R9).

**Corrected statement.** The auto-Lorenz mode is *empirically fitted* and
*conditional on acoustic-phonon transport*; it is **not** universally
appropriate, and this work provides **no experimental validation** of it. The
strongest statement the data support is: for a strongly degenerate,
phonon-limited material such as the SiGe:P reference, the auto estimate is
about 35 % below the Lorenz number implied by the published transport data.

### 4.4 Consequences for the software and the paper

1. The auto-Lorenz output must be labelled *model-derived* in the GUI and in
   any exported table (recommended change, not implemented here).
2. A publication must state the scattering assumption whenever an auto-Lorenz
   value is used.
3. The **recommended** default for degenerate materials remains the
   constant L₀ (as the authors of the SiGe paper did), with the auto mode
   offered as an alternative for non-degenerate, phonon-limited samples.

---

## 5. Review of the thermal-conductivity validation

### 5.1 The implied-Lorenz comparison is circular

The comparison "compute κ_L with the Lorenz number implied by the published
κ_L and compare with the published κ_L" uses the published κ_L to *define* the
constant it then reproduces. It is therefore an **arithmetic consistency
check**: it verifies that the application's subtraction and propagation are
internally consistent, and it says nothing about the correctness of the model
or of the data.

It is retained (it does test the application's arithmetic on real values) but
it is:

* re-labelled **"arithmetic consistency test"** in both reports and in the
  registry (`CONSISTENCY_GRIDS`);
* excluded from the experimental list of every dataset;
* **not** counted as evidence for any scientific claim.

The two lattice-conductivity results are therefore distinct:

| Comparison | Category | Circular? | Verdict |
|---|---|---|---|
| κ_L computed with the a-priori constant L = 2.44e-8 vs the published κ_L (SiGe) | **E** | no | pass, ≤0.7 % |
| κ_L recomputed with L derived from the published κ_L | arithmetic consistency | yes | pass by construction |

### 5.2 Why the PbTe lattice comparison is UNVERIFIED

For the PbTe sample the implied Lorenz number scatters by 25 % between
temperatures (1.15–1.46e-8), i.e. the published total and lattice thermal
conductivities do not describe a single constant L. No constant-L comparison
against them is meaningful at the 5 % level, so the comparison is reported as
UNVERIFIED with the measured numbers rather than tuned to pass.

---

## 6. Review of the instrument validation

### 6.1 The input files are reconstructions

The three instrument files in `raw/instrument/` are **reconstructions**: the
published Bi₂Te₃ values re-expressed in the instrument export formats. No
instrument was operated, no raw export was obtained, and no new measurement
exists. A test (`test_instrument_reconstructions_derive_from_published_data`)
verifies that the files contain exactly the published values, so the
reconstruction can never drift into "new data".

Consequently the importer results are **instrument-file parsing validation**
(category P), not measurement-chain validation and not experimental
validation.

### 6.2 The raw V/I → R → ρ → σ chain is not implemented

The application consumes the conductivity and the Seebeck coefficient **as
computed by the instrument**. The chain from a raw voltage/current dataset to
a resistivity and a conductivity is *not* implemented in the application
(only its uncertainty propagation is). Nothing in this work validates that
chain, and no such claim is made: the corresponding component is listed as
**UNVERIFIED — not implemented**.

What *is* validated about the four-probe path: temperature association, the
S/cm → S/m and µV/K → V/K conversions, the grouping and the MAD-based
outlier rejection, the standard error of the mean, the invalid/missing-row
handling, and the geometry-uncertainty combination (which is verified against
an independent formula, category N).

---

## 7. Review of the SPB inversion and the weighted mobility

### 7.1 SPB inversion

* **Numerical inversion consistency (N):** the inverted effective mass equals
  an independent evaluation to 1e-6, and the round trip n → m\* → n
  reproduces the published carrier concentration exactly (0.00 %).
* **Experimental unit cross-check (E/M):** the published σ, n and μ are
  mutually consistent through μ = σ/(n·e) with a median ratio of 1.08 — a
  factor of 1e6 or 1e-6 would have exposed a unit error. The carrier
  concentration is therefore confirmed to be in m⁻³ as published, and the
  conversion the application requires (to cm⁻³) is verified.
* **Physical-model plausibility (P-model):** the inverted m\* = 1.49–2.23 m_e
  (median 1.70 m_e) is physically reasonable for P-doped SiGe. **It was not
  cross-checked against a value stated in the source publication**: the
  abstract of DOI 10.1021/acsami.9b20090 (an SrTiO₃/SiGe composite study)
  does not state an effective mass, and the full text is not openly available.
  The benchmarked sample is the single-phase P-doped SiGe reference of that
  study (Starrydata sample name "0 wt% SrTiO₃"), whose published ZT reaches
  0.87 at ≈1007 K (the composite of the same paper reaches 0.91). The
  plausibility statement therefore rests on the general literature range, not
  on the publication, and is classified as P-model only.

### 7.2 Weighted mobility

* The implementation matches an independent implementation to 1e-9 (N) and
  scales exactly as 1/ρ.
* **It is not experimentally validated.** The only published carrier-mobility
  reference in the datasets is the Bi₂Te₃ sample's curve, which is
  *negative* (−0.0096 m²/(V·s)) — physically impossible and therefore
  unusable. The SiGe sample's mobility curve is usable and internally
  consistent, but μ_w (a weighted mobility) is **not** the same quantity as
  the published carrier mobility μ; they coincide only in the non-degenerate
  limit with m\* ≈ m_e. A like-for-like experimental reference for μ_w does
  not exist in the available data.
* **Status: PARTIALLY VALIDATED** — the arithmetic is verified, the physics
  is not, and the comparison that would be needed (a published weighted
  mobility, or a Hall-based μ plus an independent m\*) is not available here.

---

## 8. Review of the GUI testing

### 8.1 What the automated GUI tests actually cover

| Component | Automated coverage | Category |
|---|---|---|
| Main window construction and composition root (injected file service) | yes (4 tests) | G |
| File → column mapper → spreadsheet → recalculation | yes | G |
| Display-unit path vs. `is_base_units=True` path | yes | G |
| Rendered cell values vs. the model (through the app's own conversion path) | yes | G |
| Error-mode column contract (schema level) | yes | G |
| Unit switch must not change the computed values | yes | G |

### 8.2 What has **no** automated coverage

| Component | Why |
|---|---|
| Error-bar dialog (modal `ErrorBarDialog`) | interactive: `dialog.exec()` blocks a headless run |
| Kappa / laser-flash dialog | modal |
| SPB modelling dialog | modal |
| Hall mobility dialog | modal |
| Weighted-mobility dialog | modal |
| Multi-sample comparison dialog | modal (its *processing* is covered, not the dialog) |
| Plot window rendering and export | interactive |
| Clipboard paste path | interactive |
| Menus, toolbars, unit selectors (visual) | interactive |

### 8.3 The honest characterisation

The GUI testing performed here is **headless integration testing of the
non-interactive paths**, not full interactive GUI testing. The application is
exercised through its own services and widget API, and the dialogs are
validated only in their *processing* logic (through the import and use-case
layers). A peer reviewer should read the GUI validation as "the main window
loads a published dataset and computes the right numbers", not as "the user
interface has been exhaustively tested".

A `QTest`-based harness would be the natural next step; it is out of scope
here.

---

## 9. Defects found and corrected during the extended phase

| ID | Severity | Location | Description | Status |
|---|---|---|---|---|
| SE-039 | LOW | `domain/spb.py` | The Fermi–Dirac quadrature ran without `epsabs`; scipy's absolute tolerance limited the *relative* accuracy of small integrals (6.9e-4 for F₁/₂(−20)) | **fixed** (≤1e-8) |
| SE-040 | MEDIUM | `application/measurement_processing.py` | A raw-Seebeck group with a single ΔT made scipy raise `ValueError`, aborting the whole import | **fixed** (group skipped) |
| SE-041 | MEDIUM | `application/measurement_processing.py` | The four-probe fixed-layout fallback assigned four column names to a shorter frame, raising `ValueError` | **fixed** (returns "no data") |
| SE-042 | MEDIUM | `domain/units.py` | `kappa_to_si` / `kappa_from_si` **ignored the unit argument entirely** and returned the value unchanged, so `kappa_to_si(1.0, "W/(cm·K)")` returned 1.0 instead of rejecting the unit — a silently wrong κ that propagates into κ_L and ZT. The three sibling converters (`sigma_to_sm`, `seebeck_to_vk`, `pf_to_si`) all raise `ValueError` for an unknown unit | **fixed** (the unit is validated; the application layer's documented pass-through for unknown units is unchanged) |

No scientific equation was modified; every change is numerical robustness or
error handling.

---

## 10. Final validation status

### VALIDATED
| Component | Evidence |
|---|---|
| Core transport equations (PF, κₑ, κ_L, ZT) | N (independent implementations, ≤1e-9) + E (published PF/ZT, four materials, 1.3–5.9 %) |
| Lattice thermal conductivity with an a-priori constant L | E (published κ_L, ≤0.7 %) |
| Carrier-density unit interpretation of published data | E + M (μ = σ/(n·e), median ratio 1.08) |
| Multi-sample workflow | E (published PF/ZT) + N |
| Seebeck ↔ η relation, inversion, analytic limits | M + N |
| Rigorous SPB Lorenz number | M + N (independent transport integrals, both limits) |
| Empirical auto-Lorenz formula and its range of validity | M + N (+2.8 % acoustic, −21.7 % optical, −31.8 % ionised impurity) |
| Fermi–Dirac quadrature accuracy | N (after SE-039) |
| SPB inversion arithmetic | N (independent implementation + exact round trip) |
| Weighted-mobility arithmetic | N (≤1e-9) |
| Instrument importers (parsing, units, grouping, sign, robustness) | P |
| Desktop workflow (non-interactive paths) | G |

### PARTIALLY VALIDATED
| Component | What is validated | What is not |
|---|---|---|
| Weighted mobility | arithmetic and scaling (N) | the physics — no usable published μ_w reference (R16) |
| SPB effective mass | inversion consistency and unit handling (N, E) | the physical value against the publication's own statement (P-model, not retrieved) |
| Auto-Lorenz mode | formula, limits, conditional range (M, N) | experimental validation — the available data contradict the SPB model it embeds (R22) |

### UNVERIFIED
| Component | Reason |
|---|---|
| Raw V/I → R → ρ → σ chain | not implemented in the application (M-chain) |
| Interactive dialogs (error bars, Kappa, SPB, Hall, weighted mobility, multi-sample UI) | modal; no automated coverage |
| Plot rendering and export | interactive |
| Clipboard paste path | interactive |
| Weighted mobility vs a published reference | no usable published μ_w or comparable reference |
| Lattice-κ comparison for the PbTe sample | published data are not consistent with a single Lorenz number |
| Lattice-κ comparison for the Bi₂Te₃ sample | same, for the κ_L grid of that dataset |
| SPB m\* against the publication's own value | the publication's abstract does not state one and the full text is not openly available |
| Certified reference-material accuracy | no certified specimen exists in the project |

---

## 11. Reproducibility

```bash
# 1. the source snapshot (checksums verified against the published manifest)
python tests/experimental_benchmarks/extract_benchmarks.py
python tests/experimental_benchmarks/extract_workflow_benchmarks.py

# 2. the benchmark suite
python -m pytest tests/experimental_benchmarks -q

# 3. the full project suite
python -m pytest -q
```

The regeneration of `raw/`, `processed/` and `expected_results/` is
**byte-identical** to the committed files (verified by hashing before and
after a regeneration). The counts quoted in §12 are re-measured by
`tests/experimental_benchmarks/test_report_consistency.py`, which fails if
this report and the companion report disagree with the actual pytest output
or with the dataset registry.

---

## 12. Measured test counts

| Module | Result |
|---|---|
| `test_benchmarks.py` (core engine, four datasets) | 27 passed, 3 skipped |
| `test_auto_lorenz.py` (Phase 2) | 38 passed |
| `test_instrument_importers.py` (Phase 3) | 16 passed |
| `test_workflow_validation.py` (multi-sample, weighted mobility, SPB) | 19 passed, 1 skipped |
| `test_benchmark_data_integrity.py` (dataset unit and provenance guards) | 10 passed, 2 skipped |
| `test_report_consistency.py` (report/registry guards) | 9 passed |
| **benchmark directory total (environment-independent part)** | **119 passed, 6 skipped** |
| `test_gui_end_to_end.py` (environment-dependent, reported separately) | 4 passed in a Qt-capable environment; 1 module-level skip in the primary environment |

The benchmark-directory total deliberately **excludes** `test_gui_end_to_end.py`:
that module's availability depends on whether the local Qt installation can be
loaded, so including it would make the quoted count environment-dependent.
The six skips that remain are the documented UNVERIFIED comparisons (no
usable published reference) plus the two benchmark specimens whose published
carrier data are physically impossible; they are skipped in *every*
environment. `test_report_consistency.py::test_reports_state_the_actual_test_counts`
re-measures these numbers and fails if a report drifts from them.

Full project suite (primary environment): **682 passed, 10 skipped** (1 warning:
a third-party `pytz` deprecation).

The skipped tests are listed with their reasons in the test output
(`pytest -rs`): four are documented UNVERIFIED comparisons and one is the
GUI module in an environment whose Qt runtime is broken.
