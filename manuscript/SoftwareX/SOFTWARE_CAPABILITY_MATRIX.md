# Seebeck-Prime Software Capability Matrix — SoftwareX Stage 1

**Document type:** Stage 1 deliverable of the SoftwareX manuscript preparation.
**Project:** Seebeck Prime (thermoelectric transport-property software).
**Date:** 2026-11-12
**Companion documents:** `manuscript/SoftwareX/RESEARCH_POSITIONING.md`,
`manuscript/SoftwareX/MANUSCRIPT_OUTLINE.md`,
`manuscript/SoftwareX/AUTHOR_INPUT_REQUIRED.md`.

---

## 1. Purpose and scope

This matrix is the **single authoritative capability table** for the SoftwareX
manuscript. It decides, for every capability that the manuscript may mention,
whether the capability:

1. exists in the shipped source code,
2. is covered by automated tests,
3. has validation evidence (numerical / experimental / physical / unit), and
4. may legitimately be described in the manuscript.

It is produced from **three independent sources** that are cross-checked:

- the source tree (`src/`, `src/domain`, `src/application`, `src/presentation`,
  `src/gui`, `src/legacy`, `src/infrastructure`, `src/plugins`, `src/core`);
- the automated test suites (`tests/scientific`, `tests/experimental_benchmarks`,
  `tests/`, including architecture-boundary and golden-regression tests);
- the scientific validation package (`validation/`: equation registry E-01…E-62,
  test plan, independent reference implementations, test results, validation
  limitations, benchmark material families) and its remediation trail
  (`validation/remediation/`).

A capability is **never** taken from documentation alone. Where documentation and
code disagree, the code and the test evidence govern, and the disagreement is
recorded as a finding.

---

## 2. Status vocabulary

### 2.1 Implementation status (as used by `docs/SCIENTIFIC_MODEL_REGISTER.md` "Actual Implementation Status" fields)

| Status | Meaning |
|---|---|
| `IMPLEMENTED` | Source code is fully written, functional, and verified. |
| `PARTIALLY IMPLEMENTED` | Implementation exists but has boundary issues, duplicates, or missing UI integration. |
| `NOT IMPLEMENTED` | Planned capability with no code currently written. |

### 2.2 Scientific validation status (the five-value vocabulary required by the
validation programme)

| Status | Meaning |
|---|---|
| **VERIFIED** | Independently re-derived implementation agrees with an independent reference or with a published measurement within the stated scope; no defect found. |
| **PARTIALLY VERIFIED** | Numerical implementation verified; the physical claim is conditional, or only part of the claim is verifiable with the available data. |
| **UNVERIFIED** | No suitable independent or published reference is available; a comparison is correctly withheld (skipped with a reason). |
| **NOT IMPLEMENTED** | The capability or chain of calculation is absent from the source. |
| **FAILED** | A defect was found (e.g. SE-042) and is outstanding. |

No outstanding **FAILED** status remains at the time of writing: every defect
identified in the Phase 1 audit and the Phase 3 investigations has been
remediated (SE-042, D-01…D-13) or documented (D-12, D-13 resolution), and no
tolerance was weakened to obtain a passing result.

---

## 3. Reading protocol

1. **Implementation** is verified by the test suites (architecture-boundary tests
   in `tests/test_architecture_dependencies.py`, golden regression in
   `tests/golden/baseline_outputs.json`, calculation tests in
   `tests/test_calculations.py`, model tests in `tests/test_transport_models.py`,
   etc.).
2. **Numerics** are verified against `validation/independent_calculations/`
   (machine-checked independence; no application imports).
3. **Physics** is verified against published measurements in
   `tests/experimental_benchmarks/` (four StarryData datasets, checksum-verified,
   byte-identical regeneration).
4. **Units** are verified by the conversion audit and unit matrices.
5. **Limitations** are taken from `validation/SCIENTIFIC_VALIDATION_LIMITATIONS.md`
   and are authoritative for anything the manuscript states.

---

## 4. Capability matrix

The table below lists the capabilities the manuscript is permitted to discuss,
with the state of each. "Location" cites the module that implements the
capability; the reader should confirm the exact dotted path against
`docs/ARCHITECTURE.md` and `docs/SCIENTIFIC_MODEL_REGISTER.md` before citation.

### 4.1 Core transport-property calculations

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| Power factor | PF = S²·σ | `seebeck_prime.domain.calculations.calculate_pf` | `tests/test_calculations.py`; independent reference | Independent OLS: 1e-12 rel; benchmark PF vs published: 1.26–3.79 % | **VERIFIED** (numerics) / benchmarked | Scalar-band PF; unit conventions | **May be described** as numerically verified; benchmark error is reported honestly. |
| Electronic thermal conductivity | κe = L·σ·T | `seebeck_prime.domain.calculations.calculate_kappa_e` | independent reference, Wiedemann–Franz | Independent: 1e-12; SPB limit check | **VERIFIED** (numerics, conditionally physical) | Sommerfeld-default overestimates non-degenerate κe | **May be described** with the conditional. |
| Lattice thermal conductivity | κL = κtot − κe | `seebeck_prime.domain.calculations.calculate_kappa_l` | independent reference, arithmetic consistency | Independent: 1e-12 | **VERIFIED** (arithmetic, not experimental) | Negative-κL diagnostic was previously un-surfaced (D-01, now fixed) | **May be described**; negative results are now surfaced. |
| Figure of merit | ZT = PF·T / κtot | `seebeck_prime.domain.calculations.calculate_zt` | independent reference, 1e-12; benchmarks 1.26–5.93 % | Independent: 1e-12; benchmark | **VERIFIED** (numerics) / benchmarked | κtot composition | **May be described**. |

### 4.2 Lorenz-number models

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| Constant Lorenz number | L0 = (π²/3)(kB/e)² = 2.443004509e-8 W·Ω/K² | `seebeck_prime.domain.physical_constants`, `domain.calculations` | independent reference, 3e-11 vs Sommerfeld; regression | Independent: 3e-11 | **VERIFIED** | Rounded to 2.44e-8 in app (agrees with published SiGe:P data to ≤0.7 %) | **May be described**. |
| Kim empirical Lorenz | L(S) = (1.5 + e^(−|S|/116))·10⁻⁸ | `seebeck_prime.domain.calculations.calculate_lorenz_kim` | independent reference, 1e-12 | Independent: 1e-12 | **VERIFIED** (conditionally physical; acoustic approximation only) | Empirical; acoustic-scattering assumption | **May be described** with the conditional. |
| Rigorous SPB Lorenz | L(η) via transport integrals | `seebeck_prime.domain.spb.rigorous_lorenz_number` | independent transport-integral reference, 2e-14; Fermi-integral checks | Independent: 2e-14; analytic limits | **VERIFIED** (numerically) / conditionally physical | Single parabolic band; acoustic default λ=0 not appropriate for P-doped SiGe (D-13) | **May be described**; the SiGe:P contradiction is resolved as a scattering-assumption matter, model not refitted. |

### 4.3 Single parabolic band / Fermi-integral model

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| Fermi-Dirac integrals F_j | F_j(η) = ∫x^j/(1+e^(x−η))dx | `seebeck_prime.domain.spb.fermi_integral` | independent reference, 1e-8; Sommerfeld / classical limits | Independent: 1e-8 | **VERIFIED** | Single band | **May be described**. |
| Seebeck from reduced Fermi level | S(η) | `seebeck_prime.domain.spb.seebeck_from_reduced_fermi_level` | independent, 1.5e-14 vs Blatt-normalised form | Independent: 1.5e-14 | **VERIFIED** (single band) | Band structure | **May be described**. |
| Carrier density | n = Nc·(m*/m_e)^1.5·F1/2 | `seebeck_prime.domain.spb.calculate_carrier_density_spb` | independent, 5.8e-14; round trips | Independent: 5.8e-14 | **VERIFIED** (numerics) / no published m* reference for benchmarks | Effective-mass inversion unbenchmared | **May be described**; effective-mass benchmark marked UNVERIFIED where no reference exists. |
| SPB inversion (n ↔ S ↔ m*) | monotone root find | `seebeck_prime.domain.spb` | independent, 2.7e-6 | Independent: 2.7e-6 | **VERIFIED** (round trips) | Unbracketed → NaN | **May be described**. |

### 4.4 Hall analysis

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| Hall coefficient R_H = V_H·t/(IB) | `seebeck_prime.domain.hall.calculate_hall_coefficient_from_raw` | independent: 1e-12 | Independent: 1e-12 | **VERIFIED** | Single-carrier approximation | Multiband not modelled | **May be described** as single-carrier. |
| Hall carrier density n_H = r_H/(e·|R_H|) | `seebeck_prime.domain.hall.calculate_hall_carrier_density` | independent: 1e-12 | **VERIFIED** | **VERIFIED** | Single-carrier | — | **May be described**. |
| Hall mobility μ_H = |R_H|·σ | `seebeck_prime.domain.hall.calculate_hall_mobility` | independent: 1e-12 | **VERIFIED** | Single-carrier | — | **May be described**. |
| Scattering-exponent fit μ(T) ∝ T^p | `seebeck_prime.domain.hall.fit_scattering_exponent` | independent: 1e-9 | **VERIFIED** | **VERIFIED** | — | Fit range | **May be described**. |

### 4.5 Weighted mobility

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| Weighted mobility μ_W | Snyder-style expression as implemented | `seebeck_prime.domain.transport.calculate_weighted_mobility` | `tests/scientific/test_weighted_mobility_audit.py` (8 tests); independent reference 8.3e-10 | Independent: 8.3e-10; self-consistent with unit convention | **PARTIALLY VERIFIED** (numerics self-consistent; physics UNVERIFIED) | Implementation ≠ earlier-registered equation (1.49–8.25×); shape divergence at small \|S\| (D-12); no experimental reference | **May be described** only as numerically characterised, not validated; must not claim experimental validation. |

### 4.6 Phonon / laser-flash thermal conductivity

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| Laser-flash κ = α·Cp·ρ | `seebeck_prime.domain.phonon.kappa_from_diffusivity*` | independent: 2e-16 | **VERIFIED** | **VERIFIED** | κe/κL decomposition uses the same physics | H/T correction not modelled | **May be described**. |

### 4.7 Device efficiency

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| η_max, η_eng, ZT_eng (Ioffe / Snyder) | `seebeck_prime.domain.device_efficiency` | independent: 1e-12 | **VERIFIED** | **VERIFIED** (conditionally physical; constant-property assumption) | **VERIFIED** (numerics) / conditional | Constant-property assumption | **May be described** with the assumption stated. |

### 4.8 Uncertainty propagation

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| First-order Taylor propagation of PF, κ, κe, ZT | `seebeck_prime.domain.uncertainty` | independent: 1e-12; Monte Carlo 5e-3 | **VERIFIED** | **VERIFIED** (independent; independence assumption) | **VERIFIED** (numerics) | Independence of inputs assumed; covariance-aware `J·Σ·Jᵀ` **not implemented** (future work, Phase 4) | **May be described** for the implemented first-order scheme; covariance propagation must not be claimed as implemented. |

### 4.9 Units and conversions

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| Unit conversions + SE-042 fix | `seebeck_prime.domain.units`, `seebeck_prime.application.unit_conversion` | `tests/scientific/test_unit_conversion_audit.py` (34 tests), `test_unit_conversion_matrix.py` | Independent audit tests | Independent: exact factors checked; unsupported units rejected | **VERIFIED** (post-SE-042 remediation) | Density/CP performed inline in one presentation function (noted, out of scope) | **May be described**. |

### 4.10 Workflows

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| Headless calculation of transport properties | `calculate_thermoelectric_properties` | `seebeck_prime.application.use_cases` | `tests/scientific/`, `tests/test_use_cases.py` | Independent references | **VERIFIED** | — | **May be described**. |
| Measurement-derived calculation (manual entry → calc) | main-table workflow | `seebeck_prime.gui.main_window`, `application` | headless via use cases; GUI not covered | Independent references | **VERIFIED** (headless) | GUI path unautomated | **May be described** as headless; GUI behaviour as not yet automated. |
| Laser-flash workflow | κ = α·Cp·ρ | `seebeck_prime.application.use_cases.calculate_kappa_from_lfa_si_use_case`, `domain.phonon` | `tests/experimental_benchmarks/test_instrument_importers.py`, workflow tests | Independent references | **VERIFIED** | — | **May be described**. |
| Seebeck/V–I workflow | S, σ from V/I | `seebeck_prime.application`, instrument importers | importers tested; **V/I → R → ρ → σ chain NOT IMPLEMENTED** (E-58) | — | **NOT IMPLEMENTED** | Raw V/I chain absent | **Must not be claimed as implemented**. |
| Multi-sample workflow | batch over samples | `application`, `legacy.ui.dialogs.multi_sample_dialog` | `tests/test_batch_workflows.py`, workflow tests | Independent references | **VERIFIED** (headless/batch) | GUI coverage pending | **May be described** as implemented and validated headlessly; GUI not yet automated. |
| Batch processing | `process_*_batch` | `seebeck_prime.application.use_cases` | `tests/test_batch_workflows.py` | — | **VERIFIED** (headless) | — | **May be described**. |

### 4.11 GUI

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| Main-window calculation, export, units, plots | `seebeck_prime.gui.main_window` | `tests/scientific/test_negative_kappa_l_diagnostic.py` (GUI subset, Qt-capable env) | **Partial**: only the negative-κL presentation path has GUI-level tests this phase; other dialogs via `.show()` | — | n/a (UI not a scientific claim) | QTest coverage of the five non-modal dialogs not yet written; two modal dialogs use `exec()` | **Not claim automated GUI validation**; describe headless paths only. |

### 4.12 Experimental benchmarks

| Capability | Equation / method | Implementation location | Tests | Validation evidence | Scientific status | Known limitations | Manuscript allowability |
|---|---|---|---|---|---|---|---|
| PF / ZT vs published (4 specimens) | application vs independent recomputation of published curves | `tests/experimental_benchmarks/test_benchmarks.py`, `test_auto_lorenz.py` | 119 passed, 6 skipped (env-independent part of benchmark dir) | Published-data comparison | **VERIFIED** (PF/ZT within scope: 1.26–5.93 %) | Digitisation, three-source figures for PbTe | **May be described** within the stated error bars. |
| κL vs published | SiGe:P: ≤0.7 % with app constant; Bi₂Te₃ sensitivity 26.5 % | `tests/experimental_benchmarks/*` | same | Published-data comparison | **VERIFIED** (SiGe:P) / **PARTIALLY VERIFIED** (Bi₂Te₃ κL sensitivity) | κL is a difference of comparable numbers | **May be described** with the sensitivity noted. |
| PbTe κ/κL Lorenz spread | implied L spread 24.9 % | `tests/experimental_benchmarks/*` | skipped: UNVERIFIED (source data inconsistent) | **UNVERIFIED** | **UNVERIFIED** — source data limit the comparison | Pair not internally consistent | **Must not claim experimental verification**. |
| SiGe:P Lorenz contradiction | implied L = 2.4579e-8 vs acoustic SPB 1.592e-8 (−35 %) | `tests/scientific/test_sige_lorenz_finding.py`, `tools/investigate_sige_lorenz.py` | 5 tests | Investigation | **RESOLVED** as scattering-assumption matter; model not refitted | — | **May describe** as identified, quantified, not fixed by re-fitting. |

---

## 5. Consolidated final validation-status table for the manuscript

The table below is the **final status table** the validation programme commits for
the implemented calculation set. It uses the five-value vocabulary and is
reproducible from the registry and the status mapping.

| Eq. / capability | Validation status | Evidence | Notes |
|---|---|---|---|
| E-01…E-04 (PF, κe, κL, ZT) | **VERIFIED** (numerics) / benchmarked | independent refs 1e-12…1e-14; published PF/ZT 1.26–5.93 % | κL arithmetic verified; SiGe:P κL via constant ≤0.7 % |
| E-05 Kim Lorenz | **VERIFIED** (conditionally physical) | independent 1e-12 | acoustic approximation |
| E-06 SPB Lorenz | **VERIFIED** (numerics) / conditionally physical | independent 2e-14 | SiGe:P: published data contradict acoustic default (−35 %); cause = scattering (λ≈1.41), model not refitted |
| E-07 Dulong–Petit | **VERIFIED** | independent 2.3e-16 | legacy constant retained |
| Hall / mobility / scattering fit | **VERIFIED** | independent 1e-9…1e-12 | single-carrier |
| Weighted mobility | **PARTIALLY VERIFIED** (physics UNVERIFIED) | independent 8.3e-10; D-12 | implementation vs register divergence; small-│S│ divergence |
| Phonon κ | **VERIFIED** | independent 2e-16 | — |
| Device efficiency | **VERIFIED** (conditionally physical) | independent 1e-12 | constant-property assumption |
| Uncertainty (first-order) | **VERIFIED** | independent 1e-12 + MC | independence assumed; JΣJᵀ absent |
| Units / conversions | **VERIFIED** (post-SE-042) | independent audit 34 tests | SE-042 remediated |
| Raw V/I → R → ρ → σ | **NOT IMPLEMENTED** | — | E-58 |
| PbTe Lorenz comparison | **UNVERIFIED** | source data inconsistent | spread 24.9 % |
| SiGe:P Lorenz | **RESOLVED** (scattering) | investigation + tests | model not refitted |

**Headline:** the calculation engine is **VERIFIED** against independent
references and, where published data exist and are internally consistent, against
published measurements; the *physical models* remain conditional, and the
weighted mobility remains **UNVERIFIED** physically; the raw V/I chain is
**NOT IMPLEMENTED**.

---

## 6. How to use this matrix during manuscript drafting

- Any claim of the form "X is calculated by the software" must map to a row here.
- Any claim of the form "X was validated" must cite the evidence column and the
  status, and must not exceed it.
- Any claim of the form "X is implemented" must map to an implementation location
  and must not be inferred from a planned feature.
- A manuscript statement that cannot be mapped to a row here requires the author
  to add evidence or to use an explicit placeholder.

## 7. Open items that affect manuscript wording (Stage 1 finding)

1. GUI automated coverage is incomplete (Phase 5 backlog) — do not claim GUI
   validation.
2. Covariance-aware uncertainty propagation is not implemented (Phase 4 backlog).
3. Kane / Dingle / multiband Lorenz models are **not** implemented (see
   `validation/remediation/DEGENERATE_LORENZ_ASSESSMENT.md`) — must not be
   described as implemented.
4. The weighted-mobility equation implemented differs from the equation
   previously printed in the model register — must not be described as the
   registered expression without qualification.
