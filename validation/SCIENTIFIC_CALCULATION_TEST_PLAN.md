# Scientific Calculation Test Plan — Seebeck Prime

**Version:** 1.0
**Date:** 2026-11-12
**Companion documents:**
`SCIENTIFIC_EQUATION_REGISTRY.md` (what exists) · `INDEPENDENT_REFERENCE_METHODS.md`
(how it is checked) · `SCIENTIFIC_CALCULATION_TEST_RESULTS.md` (what passed) ·
`SCIENTIFIC_VALIDATION_LIMITATIONS.md` (what remains open)

---

## 0. Purpose and scope

This plan defines **what has to be demonstrated** before a calculation in
Seebeck Prime may be called scientifically verified, **how** it is
demonstrated, and **what tolerance** is acceptable for each numerical
method.

The plan is deliberately organised around *evidence classes*, not around
files. A test that exercises the application's own function against another
of the application's own functions proves only internal consistency; it is
never counted as scientific verification.

### 0.1 The three evidence classes

| Class | Code | What it establishes | What it cannot establish |
|---|---|---|---|
| **Analytical** | `A` | The formula reproduces a closed-form limit, a textbook value or a physical bound | Behaviour outside the limit; model validity |
| **Independent numerical** | `N` | The application agrees with a **separately written** implementation of the same governing equations | Whether the governing equation is the right physical model |
| **Experimental** | `X` | The application reproduces an independently published measurement of the *same specimen* under *compatible* conditions | That the model is universally valid; that other specimens behave likewise |

A calculation may be VERIFIED at one class and UNVERIFIED at another. The
status table in the results report states the class explicitly for every row.

### 0.2 Rules binding this plan

1. **No self-reference.** A test that compares the application with itself
   (including with a differently-named wrapper) is an *internal consistency*
   test, not a scientific test, and is labelled as such.
2. **No fabricated references.** Experimental reference values must come from
   a citable publication with a DOI. Where the only available data are
   unusable (e.g. a negative mobility curve), the comparison is reported as
   UNVERIFIED rather than substituted.
3. **No tolerance inflation.** Tolerances are derived from the numerical
   method (see §3) and may only be changed with a written justification that
   does not appeal to "the test needs to pass".
4. **No equation edits to satisfy a test.** Where the application and the
   independent reference disagree, one of them is wrong; the discrepancy is
   diagnosed, and the *scientific* choice is made explicitly — not by
   editing whichever side is convenient.
5. **A skip is not a pass.** Skipped tests are reported separately with a
   reason and are excluded from the verified set.
6. **Absent calculations are reported as absent.** A calculation that the
   application does not implement is `NOT IMPLEMENTED`; no surrogate test may
   be written to imply otherwise.

---

## 1. Phase map

| Phase | Subject | Plan section | Primary class |
|---|---|---|---|
| I | Equation inventory (read-only) | §2 | — |
| II | Core thermoelectric equations | §4 | A + N |
| III | Lorenz number methods | §5 | A + N |
| IV | SPB model | §6 | A + N |
| V | Weighted mobility | §7 | A + N (physics: no X) |
| VI | Uncertainty propagation | §8 | A + N (Monte-Carlo) |
| VII | Unit conversions | §9 | A |
| VIII | Numerical / physical edge cases | §10 | A |
| IX | Independent reference implementations | §3, §11 | — (infrastructure) |
| X | Scientific benchmark materials | §12 | X |
| XI | Importers and GUI integration | §13 | N + integration |
| XII | Test architecture | §14 | — (infrastructure) |
| XIII | Execution and reporting | §15 | — |

---

## 2. Phase I — Equation inventory

**Requirement.** Every calculation that can influence a displayed or exported
number must appear in `SCIENTIFIC_EQUATION_REGISTRY.md` with: equation,
source file and function, inputs, outputs, input and output units, required
conversions, physical assumptions, validity conditions, numerical method,
existing tests, missing tests and known limitations.

**Search surfaces (all inspected):**

- `src/domain/` — `calculations.py`, `uncertainty.py`, `units.py`, `spb.py`,
  `hall.py`, `phonon.py`, `transport.py`, `device_efficiency.py`,
  `analysis.py`, `validation.py`, `physical_constants.py`
- `src/application/` — `use_cases.py`, `measurement_processing.py`,
  `unit_conversion.py`, `spb_batch.py`, `services.py`, `data_mapping.py`
- `src/presentation/` — `kappa_logic.py`, `table_handler.py`,
  `unit_converter.py`, `table_plot_data.py`
- `src/gui/` — dialog controllers, menu actions, spreadsheet recalculation
- `src/legacy/` — compatibility wrappers
- `src/plugins/` — `arrhenius.py`
- `src/infrastructure/` — importers and exporters

**Completion criterion.** The registry contains one row per implemented
calculation, each traceable from user input to displayed/exported output, and
each cross-referenced to at least one test (existing or planned).

**Result.** 62 entries (E-01 … E-62). Delivered.

---

## 3. Numerical methods, and how tolerances are derived

A single blanket tolerance is scientifically meaningless. The tolerance for a
comparison is a function of the error sources of the *method being compared*.

| Method | Dominant error sources | Tolerance basis | Value used |
|---|---|---|---|
| Closed-form arithmetic (PF, κₑ, κ_L, ZT, unit conversions) | Floating-point rounding only | IEEE-754 double round-off, ≪ any physical error | `rel = 1e-12` |
| OLS regression | Summation round-off | Same | `rel = 1e-12` |
| Adaptive quadrature (Fermi integrals) vs adaptive quadrature | Independent quadrature tolerance (`epsrel = 1e-11`) | Quadrature error is the *larger* of the two; 1e-8 leaves a 3-order margin | `rel = 1e-8` |
| Fermi integral vs *analytic* limit (Boltzmann, Sommerfeld, F₀ = ln(1+e^η)) | Asymptotic truncation of the application | Application branches are documented approximations; agreement is required at the 1e-3 level, not machine precision | `rel = 1e-3` |
| Application SPB vs independent SPB (same convention) | Quadrature + normalisation convention | 1e-6 leaves three orders over the quadrature tolerance | `rel = 1e-6` |
| Root-finding (η from S) | Bracket tolerance + Brent `xtol` | 1e-5 absolute on η, which corresponds to ≪1 µV/K on S | `abs = 1e-5`, `rel = 1e-5` |
| Device efficiency (Simpson quadrature) | Quadrature rule | Same rule on both sides isolates the *formulas*; 2e-3 covers grid-dependent differences | `rel = 2e-3` |
| First-order uncertainty vs Monte-Carlo (2·10⁵ samples) | Sampling error O(N⁻¹ᐟ²) ≈ 0.2 % plus the second-order (skew) term | 5e-3 covers sampling noise and the genuine non-linearity | `rel = 5e-3` |
| Experimental comparison (published grid) | Digitisation + sample-to-sample + interpolation | *Not* a tight tolerance: agreement is reported as a distribution of relative deviations | reported, see §12 |
| Physical-constraint assertions | Exact | Boolean | exact |
| Unit conversion round-trip | Round-off | `rel = 1e-12` |

**Rule.** Where the application uses an *asymptotic* branch (Boltzmann for
η < −30, Sommerfeld for η > 50), the comparison against the exact integral is
a **documented-approximation** test with a 1e-3 tolerance, and the asymptotic
error is reported separately. It is never presented as a machine-precision
result.

---

## 4. Phase II — Core thermoelectric equations

### 4.1 Seebeck coefficient — S = ΔV/ΔT

| ID | Check | Class | Evidence required |
|---|---|---|---|
| 4.1.1 | Positive and negative S preserved end to end | A | n-type S < 0, p-type S > 0; sign not altered by import, conversion or display |
| 4.1.2 | Regression slope equals a closed-form OLS | N | ≤1e-12 against an independently written OLS |
| 4.1.3 | Slope standard error = √(SS_res/(n−2)/SS_xx) | A | closed form, ≤1e-12 |
| 4.1.4 | A perfectly linear set reproduces ΔV/ΔT exactly | A | ≤1e-12 |
| 4.1.5 | Zero temperature difference | A | handled without division by zero; documented behaviour |
| 4.1.6 | Duplicate / invalid measurement rows | N | rejected or reported, never silently averaged |
| 4.1.7 | Temperature grouping and averaging | N | group mean equals the arithmetic mean of the group |
| 4.1.8 | Unit conversions V/K ↔ mV/K ↔ µV/K | A | §9 |

### 4.2 Resistivity / conductivity

| ID | Check | Class | Evidence required |
|---|---|---|---|
| 4.2.1 | σ = 1/ρ, ρ = L/(R·A) | A + N | ≤1e-12 vs independent reference |
| 4.2.2 | Ω·cm ↔ Ω·m ↔ S/m ↔ S/cm | A | §9; 1 S/cm ≡ 100 S/m ≡ 1 Ω·cm |
| 4.2.3 | Zero, negative, infinite, missing | A | §10 |
| 4.2.4 | Numerical stability over realistic and extreme ranges | A | no NaN; overflow to ±inf is the correct IEEE outcome |
| 4.2.5 | **Raw V/I → R → ρ → σ chain** | — | **NOT IMPLEMENTED** — recorded as such; no surrogate test |

### 4.3 Power factor — PF = S²σ

| ID | Check | Class | Evidence required |
|---|---|---|---|
| 4.3.1 | SI conversion **before** the formula | N | input in SI, compare ≤1e-12 |
| 4.3.2 | Sign independence (S²) | A | PF(S) = PF(−S); PF ≥ 0 always |
| 4.3.3 | Temperature-dependent dataset | N | row-wise |
| 4.3.4 | Output units W/(m·K²) and mW/(m·K²) | A | §9 |
| 4.3.5 | Zero / invalid inputs | A | §10 |
| 4.3.6 | Experimental: published PF | X | §12 |

### 4.4 Electronic thermal conductivity — κₑ = LσT

| ID | Check | Class | Evidence required |
|---|---|---|---|
| 4.4.1 | Lorenz number in W·Ω/K² | A | unit-aware |
| 4.4.2 | Temperature in Kelvin (K vs °C) | A | a °C input produces a detectably different κₑ; the application must take K |
| 4.4.3 | Conductivity in S/m | A | S/cm input would be wrong by 100×; the conversion is applied by the caller |
| 4.4.4 | All Lorenz modes | N | constant, Kim, rigorous SPB — each compared with the independent reference |
| 4.4.5 | Scaling across input scales | A | κₑ ∝ σ, ∝ T, ∝ L |
| 4.4.6 | Experimental: κₑ from published κ and κ_L | X | §12 |

### 4.5 Lattice thermal conductivity — κ_L = κ_total − κₑ

| ID | Check | Class | Evidence required |
|---|---|---|---|
| 4.5.1 | Correct subtraction and units | N | ≤1e-12 |
| 4.5.2 | Negative result is **reported**, not silently accepted | A | a `WARNING` on field `kappa_L` is produced **and reaches the user**. **Status 2026-11-12: the validator exists and is tested, but no production path calls it — the requirement is NOT met (audit D-01).** Phase 3 |
| 4.5.3 | Near-zero result | A | treated as a warning, not an error |
| 4.5.4 | Missing κ_total or missing L | A | meaningful message |
| 4.5.5 | Physically inconsistent combination (κₑ > κ_total) | A | negative κ_L produced **and** flagged. **Status 2026-11-12: the value is produced; the flag does not reach the user (audit D-01).** Phase 3 |

### 4.6 Figure of merit — ZT = S²σT/κ_total

| ID | Check | Class | Evidence required |
|---|---|---|---|
| 4.6.1 | Independent recomputation from raw inputs | N | ≤1e-12 |
| 4.6.2 | Internal consistency PF ↔ κ ↔ T ↔ ZT | A | ZT ≡ PF·T/κ exactly |
| 4.6.3 | Zero κ handling | A | ZT = 0, no ZeroDivisionError, no NaN |
| 4.6.4 | Sign behaviour | A | ZT > 0 for κ > 0; ZT < 0 signals a negative κ |
| 4.6.5 | Numerical stability | A | no NaN for extreme magnitudes |
| 4.6.6 | Experimental: published ZT | X | §12 |

### 4.7 Laser flash — κ = α·C_p·ρ

| ID | Check | Class | Evidence required |
|---|---|---|---|
| 4.7.1 | SI path | N | ≤1e-12 |
| 4.7.2 | Laboratory-unit path (mm²/s, J/(g·K), g/cm³) | N | ≤1e-12; and the two paths agree |
| 4.7.3 | Missing fields | A | meaningful message |
| 4.7.4 | Zero and negative values | A | §10 |
| 4.7.5 | Manual verification example | A | hand-computed value reproduced |

---

## 5. Phase III — Lorenz numbers

The three methods are treated as **independent scientific implementations**;
each is verified separately and none is assumed correct because another is.

### 5.1 Constant (Sommerfeld)

| ID | Check | Class | Evidence |
|---|---|---|---|
| 5.1.1 | L₀ = (π²/3)(k_B/e)² | A | analytical, and equal to the application's default to <0.2 % (the application default is 2.44e-8, the exact value 2.443004509e-8) |
| 5.1.2 | Units W·Ω/K² | A | dimensional check through κₑ |
| 5.1.3 | Propagation into κₑ, κ_L, ZT | N | the effect of L on the three derived quantities is reproduced by the independent reference |
| 5.1.4 | User-selected vs default | A | a user value is used verbatim |

### 5.2 Empirical Kim relation

L(S) = (1.5 + exp(−|S|/116))·10⁻⁸ [W·Ω/K²], S in µV/K

| ID | Check | Class | Evidence |
|---|---|---|---|
| 5.2.1 | Formula reproduction | N | ≤1e-12 |
| 5.2.2 | Evenness in S | A | L(−S) = L(S) |
| 5.2.3 | Boundary and extreme values (S → 0, S → ±1000) | A | limits 2.5e-8 and 1.5e-8 |
| 5.2.4 | Input-unit handling | A | the relation takes µV/K; a V/K input would be off by 10⁶ |
| 5.2.5 | Comparison against rigorous SPB | A | deviation quantified per scattering parameter; **the Kim relation is documented as an acoustic-scattering approximation, never as universal** |

### 5.3 Rigorous SPB Lorenz

| ID | Check | Class | Evidence |
|---|---|---|---|
| 5.3.1 | Fermi–Dirac integral implementation | N | ≤1e-8 against independent quadrature; F₀ vs ln(1+e^η) analytic check |
| 5.3.2 | Normalisation convention | A | the Γ factors are stated and checked; the application's unnormalised convention is reconciled with the Blatt-normalised reference analytically |
| 5.3.3 | Scattering-parameter definition | A | λ = r + ½ is asserted and shown to reproduce the correct limits |
| 5.3.4 | Quadrature convergence | A | asymptotic branch continuity (no step) across the switch points |
| 5.3.5 | Limiting behaviour | A | η → +∞ gives (π²/3)(k_B/e)²; η → −∞ gives (5/2 + r)(k_B/e)² |
| 5.3.6 | Root finding | N | §6.2 |
| 5.3.7 | Scattering mechanisms (acoustic, optical/alloy, ionised impurity) | N | each λ compared with the independent reference |

---

## 6. Phase IV — SPB model

### 6.1 S(η)

| ID | Check | Class | Evidence |
|---|---|---|---|
| 6.1.1 | Fermi integral and scattering convention | N | ≤1e-6 for λ ∈ {0, 1, 2} |
| 6.1.2 | Sign: S > 0 for η < 0 (p-type), S → 0⁺ for η ≫ 0 | A | monotonicity |
| 6.1.3 | Non-degenerate limit | A | S → (k_B/e)(λ + 2 − η) |
| 6.1.4 | Degenerate limit | A | S → 0 |
| 6.1.5 | Temperature dependence (through η) | N | row-wise consistency |
| 6.1.6 | Numerical convergence | A | §5.3.4 |

### 6.2 Inversion S → η

| ID | Check | Class | Evidence |
|---|---|---|---|
| 6.2.1 | Root finding converges | N | ≤1e-5 vs an independent Brent/bisection inversion |
| 6.2.2 | Bracket independence | A | the same η from a different bracket |
| 6.2.3 | Initial guess irrelevance | A | the result does not depend on the seed |
| 6.2.4 | Unbracketable input | A | NaN (not a plausible-looking number) |
| 6.2.5 | Metallic limit | A | S → 0 maps to the saturated η |
| 6.2.6 | Round-trip S(η) → η' → S(η') | A | ≤1e-5 |

### 6.3 Effective mass, 6.4 carrier concentration

| ID | Check | Class | Evidence |
|---|---|---|---|
| 6.3.1 | m* from (S, n, T) | N | ≤1e-6 vs independent reference |
| 6.3.2 | n in cm⁻³ vs m⁻³ | A | 10⁶ factor |
| 6.3.3 | Temperature dependence of N_c | A | N_c ∝ T^{3/2} |
| 6.3.4 | Electron/hole convention | A | |S| used; sign carried by the carrier type, not by m* |
| 6.3.5 | Sensitivity to the scattering assumption | A | the implied m* changes with λ; the dependency is documented |
| 6.4.1 | n = N_c m*^{3/2} F_{1/2}(η) | N | ≤1e-6 |
| 6.4.2 | Effective density of states | A | N_c = 2(2πm_e k_B T/h²)^{3/2}, checked against the application's internal constant including the 1/Γ(3/2) factor |
| 6.4.3 | Physical limits | A | n > 0, m* > 0 |

### 6.5 Round trips

| ID | Check | Class | Evidence |
|---|---|---|---|
| 6.5.1 | n → S → n | N | ≤1e-6 |
| 6.5.2 | m* → S → m* | N | ≤1e-12 |
| 6.5.3 | **Round-trip agreement is not experimental validation** | — | explicitly recorded as such in the results report |

---

## 7. Phase V — Weighted mobility

The exact expression used by the application is read from the source and
re-implemented independently.

| ID | Check | Class | Evidence |
|---|---|---|---|
| 7.1 | Expression reproduction | N | ≤1e-9 vs an independent implementation of the same formula |
| 7.2 | Dimensional consistency | A | cm²/(V·s) |
| 7.3 | Scaling with resistivity | A | μ_w ∝ 1/ρ |
| 7.4 | Scaling with temperature | A | μ_w ∝ T^{−3/2} (the assumed acoustic law) |
| 7.5 | Effective-mass dependence | A | as assumed by the model |
| 7.6 | Unit conversions (mΩ·cm, µV/K) | A | §9 |
| 7.7 | Relation to conventional carrier mobility | A | μ_w ≠ μ_H in general; they are **not** compared as identical quantities |
| 7.8 | Negative / zero mobility in the input data | A | flagged |
| 7.9 | **Experimental validation** | X | **UNVERIFIED** — the published carrier-mobility curve for the Bi₂Te₃ benchmark is negative and therefore unusable; no substitute reference is fabricated |

---

## 8. Phase VI — Uncertainty and error propagation

| ID | Check | Class | Evidence |
|---|---|---|---|
| 8.1 | Analytical form for every implemented propagator | N | ≤1e-12 vs the independent implementation |
| 8.2 | Monte-Carlo cross-check | N | ≤5e-3 (2·10⁵ samples) for PF and κ(laser flash) |
| 8.3 | Independent vs correlated inputs | A | the **assumption of independence is documented**; no covariance matrix is modelled anywhere, and the report states this explicitly |
| 8.4 | Relative and absolute uncertainty | A | both forms supported and distinguished |
| 8.5 | Zero uncertainty | A | propagated uncertainty = 0 |
| 8.6 | Missing uncertainty | A | meaningful message / documented default |
| 8.7 | Very large uncertainty | A | finite result, no overflow to NaN |
| 8.8 | Quadrature, not addition | A | explicitly asserted (u = √(Σu²), not Σu) |
| 8.9 | Covered quantities | — | PF, κₑ, κ_L, ZT, σ(geometry), κ(laser flash), ρ(density). Weighted mobility and SPB outputs have **no** implemented uncertainty propagation and are reported as such |

---

## 9. Phase VII — Unit conversions

| ID | Check | Class | Evidence |
|---|---|---|---|
| 9.1 | Forward conversion correctness | A | exact factors, ≤1e-12 |
| 9.2 | Round trip | A | ≤1e-12, for every supported spelling (incl. `µ` vs `μ`, `Ω·cm` vs `Ohm-cm`) |
| 9.3 | Conversion **before** calculation | N | §4 |
| 9.4 | Conversion **after** calculation | N | the same physical result is reached either way |
| 9.5 | Display units vs internal SI | A | the invariant of §9.1 below |
| 9.6 | Imported vs manually entered data | N | §13 |
| 9.7 | Spreadsheet vs exported values | N | §13 |
| 9.8 | Uncertainty conversions | A | linear for S and PF; u_σ = u_ρ·100/ρ² for Ω·cm; temperature uncertainty invariant under the offset |
| 9.9 | Unknown unit handling | A | `ValueError`, never a silent default |

**The central invariant (9.5):** *no calculation may mix display units and
internal SI units.* It is enforced by requiring that, for every supported
unit, `to_base(from_base(x)) ≡ x` and by checking that the internal value
stored for a table row equals the independently recomputed SI value.

---

## 10. Phase VIII — Numerical and physical edge cases

Every implemented calculation is exercised with:

zero · negative · very small · very large · NaN · Inf · missing input ·
duplicate temperatures · unsorted temperatures · empty dataset ·
single-point dataset · inconsistent array lengths · invalid numerical type ·
extreme temperatures · non-convergent numerical algorithm.

For each case the test asserts one of two outcomes:

1. a **meaningful result** (documented convention), or
2. a **meaningful validation message** / exception with a human-readable
   text.

Never: a silently misleading number, a silent NaN where a value is
expected, an unhandled exception, or a `ZeroDivisionError`.

Special cases with an explicit documented convention:

| Case | Convention |
|---|---|
| κ_total = 0 | ZT = 0 (not NaN, not an exception) |
| ρ = 0 in weighted mobility | NaN (the value carries no information) |
| Length-1 array vs longer array | numpy broadcasting (the application validates completeness before this point) |
| Physically absurd magnitudes (10³⁰⁰) | ±inf is acceptable (IEEE-754); **NaN is not** |
| Unbracketable \|S\| in the SPB inversion | NaN |

---

## 11. Phase IX — Independent reference implementations

**Location:** `validation/independent_calculations/`

**Requirements (all enforced):**

1. **No import of `seebeck_prime`** — enforced by an automated test that
   parses the reference modules' AST and asserts the absence of any
   application import.
2. **Not a line-by-line copy** — the references are written from the
   governing equations and use a *different* numerical strategy where one is
   available (e.g. adaptive quadrature + Blatt normalisation vs the
   application's branch structure; closed-form OLS vs `scipy.stats.linregress`;
   Monte-Carlo vs analytic propagation).
3. **Assumptions documented** — in the module docstring and in
   `INDEPENDENT_REFERENCE_METHODS.md`.
4. **Analytically known values used where available** — ln(1+e^η) for F₀,
   the Sommerfeld and Boltzmann limits, the exact 1 S/cm ≡ 100 S/m relation.
5. **Reference code shipped in the validation package** — the directory is
   part of the repository and is imported by the test suite.
6. **Transparent fixtures** — the expected numbers are either computed by the
   reference in the test (preferred) or stored as literals with the
   derivation in a comment.

**Reporting.** For every comparison the results report states: application
result, reference result, absolute error, relative error, tolerance and
pass/fail. The comparison table is generated from the test run, not written
by hand.

---

## 12. Phase X — Scientific benchmark materials

**Goal:** support published datasets for SiGe, Mg₂Si, Mg₂Sn, Bi₂Te₃-based,
PbTe, SnSe and CaMnO₃-based oxides — **without fabricating data and without
assuming that any of them obeys a single parabolic band**.

**Provenance requirements for every benchmark:**

material composition · sample ID · DOI · source publication · data source ·
temperature · Seebeck coefficient · electrical conductivity · Hall carrier
concentration · Hall mobility · thermal conductivity · effective mass (if
independently reported) · scattering assumptions · digitisation uncertainty ·
data provenance.

**Rules.**

- Only measurements of the **same specimen** under **compatible conditions**
  are compared.
- A grid is compared only if the published curve supplies the inputs the
  software needs (e.g. κ_L requires κ_total and σ at the same T).
- Where the comparison uses a Lorenz number **derived from the same
  publication's κ_L**, the comparison is labelled `consistency`
  (arithmetic self-consistency of the published data) — **not** experimental
  validation of the model.
- Where a published curve is physically unusable (negative mobility), the
  comparison is dropped and the reason recorded.
- The material-family survey records what the source database actually
  contains (sample counts, paper counts, DOIs) — it does not invent
  benchmarks.

**Outcome.** Four datasets are used as full experimental benchmarks (see
`tests/experimental_benchmarks/registry.py`); the remaining families are
registered as surveyed material families with a documented extraction
procedure, so the framework is demonstrably capable of hosting them.

---

## 13. Phase XI — Importers and GUI integration

### 13.1 Four-probe importer
File parsing · column mapping · conductivity units · Seebeck units ·
invalid rows · geometry-related calculation (if implemented) · the complete
calculation pipeline.

### 13.2 Raw Seebeck importer
ΔV and ΔT · regression · sign convention · unit conversion · temperature
grouping · invalid and duplicate rows.

### 13.3 Laser-flash importer
Thermal diffusivity · density · specific heat · thermal conductivity ·
missing and invalid fields.

### 13.4 Multi-sample workflow
Multiple datasets · different compositions · independent calculations ·
temperature alignment · comparison results · **no mixing of sample
identities**.

### 13.5 GUI (PyQt6 `QTest` where possible)

All calculation dialogs (error bar, Kappa, SPB, Hall, weighted mobility,
multi-sample) · user input validation · modal dialog behaviour · plotting
and error bars · clipboard paste · menus · export · spreadsheet
recalculation · display units vs base SI values.

**The end-to-end path** `Input → Import → Unit Conversion → Calculation →
GUI Display → Plot → Export` must be value-preserving at every stage.

**Constraint.** Modal dialogs block headless execution. The GUI tests
therefore have three distinct outcomes, which the results report states
separately:

| Outcome | Meaning |
|---|---|
| passed | the assertion held in a Qt-capable environment |
| skipped (Qt unavailable) | the environment lacks a working Qt; **not** a pass |
| not implemented | no automated coverage exists for this path |

---

## 14. Phase XII — Test architecture

The requested tree is adapted to the actual project layout (which is flat
rather than `unit/ numerical/ integration/ gui/`):

```
tests/
├── test_*.py                     # 26 legacy/engineering suites (≈300 tests)
├── scientific/                   # NEW: independent scientific validation
│   ├── test_independent_references.py
│   ├── test_physical_constraints.py
│   ├── test_unit_conversion_matrix.py
│   └── test_numerical_edge_cases.py
├── experimental_benchmarks/      # published-measurement validation
│   ├── registry.py               # single source of truth
│   ├── extract_benchmarks.py
│   ├── extract_workflow_benchmarks.py
│   ├── gui_workflow_driver.py
│   ├── test_benchmarks.py
│   ├── test_auto_lorenz.py
│   ├── test_instrument_importers.py
│   ├── test_workflow_validation.py
│   ├── test_gui_end_to_end.py
│   └── test_report_consistency.py
└── golden/
    ├── baseline_outputs.json     # self-generated regression snapshot
    └── test_previous_benchmarks.py
```

**Deliberate deviations from the requested tree, and why:**

- The requested `unit/`, `numerical/`, `integration/`, `gui/` and
  `regression/` sub-trees would have **duplicated** the existing
  `tests/test_*.py` suites (which already cover the same functions) and
  required moving files, breaking the existing golden baseline. The new
  `tests/scientific/` tree was therefore added *alongside* the existing
  layout instead of replacing it.
- The requested `test_analytical_references.py` is realised as
  `test_independent_references.py` (it contains both the analytical-limit and
  the independent-numerical comparisons).
- No separate `tests/gui/` directory exists because the GUI can only be
  driven through the subprocess driver in
  `tests/experimental_benchmarks/`, and the existing
  `tests/test_plot_data.py` covers the headless plotting logic.

**Consistency guard.** `tests/experimental_benchmarks/test_report_consistency.py`
re-measures the test counts on disk and verifies that the registry, the
on-disk datasets and **both** validation reports agree. A report that
disagrees with the code fails the suite.

---

## 15. Phase XIII — Execution and reporting

### 15.1 Environment to be recorded
Python version · operating system · PyQt6 version · NumPy · SciPy · Pandas ·
Matplotlib · the exact test command · total / passed / failed / skipped
counts · the reason for every skip.

The suite must be run in the **supported** environment. Where the primary
conda environment cannot load Qt (a DLL-load failure on this machine), the
GUI subset is run in a **documented** Qt-capable virtual environment and the
difference is stated explicitly, together with the versions in each.

### 15.2 Status vocabulary (used in every report)

| Status | Definition |
|---|---|
| **VERIFIED** | Every requirement defined in this plan for that calculation was met, with the evidence class stated |
| **PARTIALLY VERIFIED** | Some requirements were met; named requirements remain |
| **FAILED** | One or more confirmed tests failed (a defect, not an absence of evidence) |
| **UNVERIFIED** | Insufficient evidence — the calculation exists but no qualifying test exists, or the available reference is unusable |
| **NOT IMPLEMENTED** | The calculation does not exist in the application |

### 15.3 Reporting rules

- The summary table has the columns
  `Calculation | Equation verified | Independent reference | Unit tests |
  Physical validity | Status`.
- The word "VALIDATED" is never used without stating **what** was validated
  and **at which evidence class**.
- A green test run is **never** reported as "100 % validated".
- Every confirmed defect is either fixed (with a regression test) or listed
  as unresolved, with its scientific consequence.

---

## 16. Completion criteria

| # | Criterion | Met by |
|---|---|---|
| 1 | Every implemented calculation inventoried | `SCIENTIFIC_EQUATION_REGISTRY.md` (62 entries) |
| 2 | Every equation has an independent reference test | `tests/scientific/test_independent_references.py` |
| 3 | Unit conversions tested | `tests/scientific/test_unit_conversion_matrix.py` |
| 4 | Numerical methods tested | `tests/scientific/test_numerical_edge_cases.py` |
| 5 | Physical constraints checked | `tests/scientific/test_physical_constraints.py` |
| 6 | Model assumptions and limits documented | registry + limitations report |
| 7 | Importer workflows tested | `tests/experimental_benchmarks/test_instrument_importers.py` |
| 8 | GUI coverage and skips reported separately | results report §GUI |
| 9 | Experimental validation distinguished from mathematical validation | registry comparison kinds + results report |
| 10 | Every confirmed defect documented and fixed or explicitly open | `docs/SCIENTIFIC_EQUATION_AUDIT.md` + limitations report |
| 11 | All results reproducible | commands, environment and checksums in the results report |
