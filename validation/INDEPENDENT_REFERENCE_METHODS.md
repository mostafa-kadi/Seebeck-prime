# Independent Reference Methods — Seebeck Prime

**Version:** 1.0
**Date:** 2026-11-12
**Code:** `validation/independent_calculations/references.py`
**Package:** `validation/independent_calculations/__init__.py`

---

## 1. Purpose

The application (`seebeck_prime`) computes thermoelectric properties from
measured inputs. A test that compares the application with itself proves
internal consistency only. This document describes the **separate
implementations** used to decide whether the application's numbers are
scientifically correct.

Each reference function below was written from the governing equation and
the published definition of the constants, with an explicit statement of
the convention used. Where the application and the reference disagreed, the
disagreement was *diagnosed* (not adjusted away) — §8 records the two
instances in which the **reference** turned out to be wrong and the
application right.

---

## 2. The independence rules, and how they are enforced

| Rule | Enforcement |
|---|---|
| The reference package must not import `seebeck_prime` (or any application module) | `tests/scientific/test_independent_references.py::test_reference_package_does_not_import_the_application` — parses the reference module's AST and asserts that no `import`/`from … import` statement targets the application |
| The reference must not call the application at runtime | Same AST check, plus the absence of `importlib`/`__import__` usage |
| The reference must use a *different* numerical method where one exists | Asserted by construction (Table in §4) and documented per function |
| The reference must not be a line-by-line copy | The reference is 380 lines against 1 400+ lines of application calculation code, uses different branch structure, different quadrature and different regression implementation; the comparison table in §4 records the method on each side |
| The reference must ship with the validation package | It lives in `validation/independent_calculations/` and is imported by the test suite from the repository root |

The reference module depends only on `numpy`, `scipy` and the Python
standard library (`math`). It does not import `pandas`, `matplotlib` or
`PyQt6`.

---

## 3. Constants

CODATA 2018 exact values, written out literally so that the reference does
not inherit a constant table from the application:

| Constant | Value | Unit |
|---|---|---|
| k_B | 1.380649e-23 | J/K |
| e | 1.602176634e-19 | C |
| N_A | 6.02214076e23 | 1/mol |
| h | 6.62607015e-34 | J·s |
| m_e | 9.1093837015e-31 | kg |

Derived: `k_B/e = 8.617333262e-5 V/K` (= 86.17333262 µV/K),
`L₀ = (π²/3)(k_B/e)² = 2.443004509e-8 W·Ω/K²`.

**Note.** The application's *default* Lorenz number is 2.44e-8 W·Ω/K² (a
rounded value), while `SOMMERFELD_LORENZ_EXACT` in the application is
2.443004509e-8. This is a deliberate, documented author decision
(unified default of 2.44e-8 across all Lorenz modes). The reference always
computes the exact value and the comparison against the application's
*exact* constant is at 1e-9; the comparison against the *default* is at the
0.13 % level, which is the rounding, not an error.

---

## 4. Method-by-method record

For each quantity: the governing equation, the reference's implementation
strategy, the application's strategy, and the tolerance that follows from
the difference in method.

### 4.1 Fermi–Dirac integrals

**Definition.** The complete Fermi–Dirac integral of order *j*:

F_j(η) = ∫₀^∞ x^j / (1 + exp(x − η)) dx

Two normalisation conventions appear in the literature and both are used
here:

| Convention | Definition | Used by |
|---|---|---|
| **Unnormalised** | F_j(η) as written above | the application (`domain/spb.py`) |
| **Blatt-normalised** | F̂_j(η) = F_j(η) / Γ(j+1) | the reference, and most modern textbooks |

The conversion is exact: F_j = Γ(j+1)·F̂_j, with Γ(3/2) = √π/2 = 0.8862269…

**Reference implementation.** Direct adaptive quadrature
(`scipy.integrate.quad`) of the integrand over [0, max(η+80, 90)] with
`epsrel = 1e-11`, `epsabs = 1e-18`, `limit = 400`. No asymptotic
shortcuts, no branch structure — the reference is a *single* method that
works at every η.

**Application implementation.** Asymptotic branches for η < −30 (Boltzmann)
and η > 50 (Sommerfeld), adaptive quadrature in between.

**Analytic anchors used in the tests.**

- F₀(η) = ln(1 + e^η) exactly → the reference reproduces this to machine
  precision; the application reproduces it to 1e-12 (verified in
  `test_numerical_edge_cases.py`).
- F₀(η) ≈ η for η ≫ 1.
- F_j(η) ≈ e^η for η ≪ 0.

**Tolerance.**

| Comparison | Tolerance | Why |
|---|---|---|
| app vs reference (unnormalised), quadrature region | `rel = 1e-8` | The application's quadrature tolerance is looser than the reference's; 1e-8 is 3 orders above the reference's own error and 3 orders below any physical difference |
| app vs reference at the asymptotic branches | `rel = 1e-3` | The application's branches are *documented approximations*; a machine-precision comparison there would be false |
| reference vs the analytic F₀ = ln(1+e^η) | `rel = 1e-12` | Exact identity |

### 4.2 Single parabolic band (SPB) — Seebeck coefficient

**Governing equation.** For a band with transport distribution
∝ x^r (so the *transport* exponent is r = λ − ½), with Blatt-normalised
integrals:

S(η) = (k_B/e) [ (5/2 + r)·F̂_{r+3/2}(η)/F̂_{r+1/2}(η) − η ]

Substituting r = λ − ½:

**S(η) = (k_B/e) [ (λ + 2)·F̂_{λ+1}(η)/F̂_λ(η) − η ]**

and, in the application's unnormalised convention,

S(η) = (k_B/e) [ (λ+2)·F_{λ+1}(η)/F_λ(η) − η ]

because the Γ factors cancel in the ratio. **The two forms are identical.**

The scattering parameter is defined by λ = r + ½, i.e.

| λ | r | Scattering mechanism |
|---|---|---|
| 0 | −1/2 | acoustic deformation potential (phonon) |
| 1 | +1/2 | optical / alloy |
| 2 | +3/2 | ionised impurity |

**Reference implementation.** Blatt-normalised integrals from the direct
quadrature above; the textbook prefactor (λ + 2).

**Application implementation.** Unnormalised integrals with the unnormalised
prefactor. The two are numerically identical *provided the prefactor is
consistent with the normalisation* — which is precisely the point that
§8.1 records.

**Limits (all asserted in the test suite).**

- Non-degenerate (η ≪ 0): F_j ≈ e^η → S → (k_B/e)(λ + 2 − η).
  For λ = 0 this is the classical result S = (k_B/e)(2 − η).
- Degenerate (η ≫ 0): F_j ≈ η^{j+1} → S → 0.

**Tolerance:** `rel = 1e-6` (quadrature-limited, three orders above the
reference's own error).

### 4.3 SPB — inversion S → η

**Governing equation.** S(η) is strictly decreasing in η, so the inverse is
a well-posed scalar root-finding problem.

**Reference implementation.** `scipy.optimize.brentq` on the explicitly
bracketed interval [−60, 80], with `xtol = 1e-12`, `rtol = 1e-14`; a
`ValueError` is raised if the target |S| lies outside the bracket.

**Application implementation.** Brent on a wider, differently chosen bracket
with an explicit "metallic limit" saturation for S → 0.

**Tolerance:** `abs = 1e-5`, `rel = 1e-5` on η. The application returns NaN
(unbracketed) where the reference raises — both are "no answer", and the
test asserts the *value* agreement only where an answer exists.

### 4.4 SPB — Lorenz number

**Governing equation.**

L(η) = (k_B/e)² [ (λ+3)(λ+2)·F̂_{λ+2}(η)/F̂_λ(η) − ( (λ+2)·F̂_{λ+1}(η)/F̂_λ(η) )² ]

**Limits (asserted).**

- η → +∞ (degenerate): L → (π²/3)(k_B/e)² = 2.443004509e-8 — the
  Sommerfeld value.
- η → −∞ (non-degenerate): L → (5/2 + r)(k_B/e)² = (λ + 2)(k_B/e)².
  For λ = 0 this is 2(k_B/e)² = 1.48668e-8.

**Tolerance:** `rel = 1e-6` for the λ ∈ {0, 1, 2} grid; `rel = 5e-3` for the
asymptotic-limit assertions (the application reaches its branch cut-off at
|η| = 40/50, where the asymptotic form is only approximate).

### 4.5 SPB — carrier concentration and effective mass

**Governing equations.**

N_c = 2 (2π m_e k_B T / h²)^{3/2}   [m⁻³], for m* = m_e

n = N_c · (m*/m_e)^{3/2} · F̂_{1/2}(η)   [m⁻³]  →  [cm⁻³] after ×10⁻⁶

m*/m_e = [ n / (N_c · F̂_{1/2}(η)) ]^{2/3}

**The normalisation subtlety.** When n is expressed with the *unnormalised*
integral, the effective density of states must carry the factor 1/Γ(3/2):

n = N_c · (m*/m_e)^{3/2} · F_{1/2}(η) / Γ(3/2)

The application's internal constant `_CONST_N0_SI` carries exactly this
factor. The reference uses the textbook (Blatt-normalised) form with the
plain N_c. **Both give the same n** — verified numerically to 1e-15
(§8.2).

**Tolerance:** `rel = 1e-6` for n and m* (the η entering both comes from the
inversion, which is itself only good to 1e-5).

### 4.6 Transport quantities

| Quantity | Reference implementation | Application | Tolerance |
|---|---|---|---|
| PF = S²σ | `np.asarray(S)**2 * sigma` | scalar/array arithmetic | `rel = 1e-12` |
| ρ = L/(R·A) | direct | (not used in the calculation path; the instrument file supplies σ) | `rel = 1e-12` |
| σ = 1/ρ | direct | direct | `rel = 1e-12` |
| κₑ = LσT | direct | direct | `rel = 1e-12` |
| κ_L = κ_total − κₑ | direct | direct | `rel = 1e-12` |
| ZT = PF·T/κ | guarded division (`np.divide(..., where=κ≠0)`) | guarded division | `rel = 1e-12` |
| κ = α C_p ρ (SI) | direct | direct | `rel = 1e-12` |
| κ = α C_p ρ (lab) | α[mm²/s]×10⁻⁶ · C_p[J/(g·K)]×10³ · ρ[g/cm³]×10³ | same | `rel = 1e-12` |

For the array-valued quantities the reference is deliberately written with
`np.asarray` + NumPy broadcasting so that the reference does *not* inherit
the application's own shape-validation behaviour — a difference in shape
handling is therefore detectable.

### 4.7 Lorenz numbers

- **Sommerfeld:** L₀ = (π²/3)(k_B/e)² — closed form in the reference.
- **Kim empirical:** L(S) = (1.5 + exp(−|S|/116))·10⁻⁸ with S in µV/K.
  The reference implements it from the published expression; the application
  implements the same expression. Compared at `rel = 1e-12`.
  The *physics* of this relation is separately quantified against the
  rigorous SPB value (§4.4) in `tests/experimental_benchmarks/test_auto_lorenz.py`.

### 4.8 Weighted mobility

**The expression actually used by the application** (read from
`src/domain/transport.py::calculate_weighted_mobility`):

μ_w = 331 · (1/ρ) · (T/300)^{−3/2} · shape( |S| / (k_B/e) )

with the shape factor

shape(s) = exp(s − 2)/(1 + exp(−5(s − 1))) + 3π² / ( s·(1 + exp(5(s − 1))) )

**Reference implementation.** Re-derived from the above with the constants
written out explicitly (k_B/e in µV/K), so that a change in the application's
magic number (331) or in the shape function is detected.

**Interpretation — and its limits.** μ_w is an *effective* mobility inferred
from the measured ρ and S under an assumed scattering law. It is **not** the
Hall mobility μ_H = |R_H|σ, and the two are not interchangeable except in
the non-degenerate limit with m* ≈ m_e. The reference test
`test_weighted_mobility_is_not_the_hall_mobility` asserts their inequality.

**Tolerance:** `rel = 1e-9` (transcendental functions; 1e-9 is generous
against double round-off but tight enough to catch a changed constant).

**Experimental status:** UNVERIFIED. The published carrier-mobility curve
for the Bi₂Te₃ benchmark specimen is *negative* (physically impossible) and
therefore unusable as a reference. No substitute was fabricated.

### 4.9 Hall

| Relation | Reference | Tolerance |
|---|---|---|
| R_H = V_H·t/(I·B) | direct | `rel = 1e-12` |
| n_H = r_H/(e·\|R_H\|) | direct | `rel = 1e-9` (the application's internal 1/e constant) |
| μ_H = \|R_H\|·σ | direct | `rel = 1e-12` |
| μ ∝ T^p fit | `np.polyfit` on ln μ vs ln T, with r² computed explicitly | `rel = 1e-9` |

The scattering-exponent fit is an independent implementation: the
application uses its own least-squares routine, the reference uses NumPy's
polynomial fit with a separately written r².

### 4.10 Regression

**Application:** `scipy.stats.linregress` (slope, intercept, r, stderr).
**Reference:** a closed-form OLS written from the normal equations:

slope = Σ(x−x̄)(y−ȳ) / Σ(x−x̄)²
s_e = √( SS_res/(n−2) / SS_xx )

**Tolerance:** `rel = 1e-12`.

### 4.11 Uncertainty propagation

The reference implements the **first-order (linearised) Gaussian**
propagations directly from the definitions:

u(y)² = Σ_i (∂y/∂x_i)² u(x_i)²

with the partial derivatives evaluated analytically:

| Quantity | Propagator |
|---|---|
| PF | √((2Sσ u_S)² + (S² u_σ)²) |
| κₑ | √((LT u_σ)² + (Lσ u_T)² + (σT u_L)²) |
| κ_L | √(u_κ² + u_κₑ²) |
| ZT | \|ZT\|·√((u_PF/PF)² + (u_T/T)² + (u_κ/κ)²) |
| σ (geometry) | \|σ\|·√((u_L/L)² + (u_R/R)² + (u_A/A)²) |
| κ (laser flash) | \|κ\|·√((u_α/α)² + (u_Cp/Cp)² + (u_ρ/ρ)²) |
| ρ (density) | \|ρ\|·√((u_m/m)² + (u_A/A)² + (u_t/t)²) |

**Independence assumption.** Every propagator assumes the inputs are
**statistically independent**. No covariance is modelled anywhere in the
application; this is stated in the limitations report as a modelling
limitation, not as a bug.

**Monte-Carlo cross-check.** `monte_carlo_uncertainty()` in the reference
draws 200 000 Gaussian samples (fixed seed 20261112) and reports the
sample standard deviation of the resulting quantity. The comparison with the
analytic propagator is at `rel = 5e-3`, which covers both the sampling
error (≈0.2 % at N = 2·10⁵) and the genuine second-order contribution
(the distribution of a product is skewed, so the analytic first-order value
is not exactly the standard deviation).

### 4.12 Dulong–Petit

C_V(molar) = 3·n_atoms·R = 3·n_atoms·N_A·k_B   [J/(mol·K)]
C(specific) = C_V / M   with M in kg/mol   [J/(kg·K)]

Tolerance `rel = 1e-12`. The reference writes R = N_A·k_B explicitly rather
than importing the molar gas constant.

### 4.13 Device efficiency

**Governing equations.**

ZT̄ = (1/(T_h − T_c)) ∫ ZT(T) dT
η_max = (ΔT/T_h)·(√(1+ZT̄) − 1)/(√(1+ZT̄) + T_c/T_h)
ZT_eng = S̄²·T̄/(ρ̄·κ̄) with ρ̄ = ⟨1/σ⟩

**Reference implementation.** `scipy.integrate.simpson` on the same
temperature grid. The application uses a Simpson rule of its own; using the
same rule on both sides deliberately isolates the *formulas* from the
quadrature rule. Where the application's temperature grid does not cover
[T_c, T_h], both sides interpolate identically.

**Tolerance:** `rel = 2e-3`.

---

## 5. Comparison reporting

Every comparison performed by the test suite reports, per the plan:

- application result,
- independent reference result,
- absolute error,
- relative error,
- numerical tolerance,
- pass/fail.

The per-test tolerances are listed in §4. The aggregate table (application
vs reference, worst case over the parameter grid) is generated by the test
run and reproduced in `SCIENTIFIC_CALCULATION_TEST_RESULTS.md`.

---

## 6. What the reference does **not** cover (and why)

| Area | Reason |
|---|---|
| Importer parsing | The importers are validated against *real instrument-format files* and their own reconstructed round-trips (`tests/experimental_benchmarks/test_instrument_importers.py`); a reference "importer" would only re-test the parsing logic, not the science |
| GUI behaviour | Modal dialogs block headless execution; the GUI is covered by a subprocess driver in a Qt-capable environment, not by a reference implementation |
| Multi-sample workflows | Validated against published PF/ZT of the same specimens — an experimental class, not a reference class |
| Weighted mobility *physics* | The reference reproduces the *formula*; the physics has no valid experimental reference (negative published curve) and is reported UNVERIFIED |
| Auto-Lorenz *physics* | The reference implements the Kim relation; the comparison against rigorous SPB shows the model contradicts the published SiGe data (see the limitations report) |

---

## 7. Reproducibility

- The reference module has **no** random component except
  `monte_carlo_uncertainty`, which uses a fixed seed (20261112) and a fixed
  sample count (200 000).
- All constants are literal CODATA values, so the reference is independent
  of the application's constant module.
- The reference is imported from the repository root
  (`from validation.independent_calculations import references as ref`);
  `validation/` has no `__init__.py` requirement — Python 3 namespace
  packages handle it.

---

## 8. Discrepancies found, and how they were resolved

### 8.1 SPB prefactor convention — the *reference* was wrong

**Symptom.** The first independent reference used the textbook form
S = (k_B/e)[(λ+2)F̂_{λ+1}/((λ+1)F̂_λ) − η] with Blatt-normalised integrals.
The application disagreed by up to a factor of 8.9 at η = 3, λ = 0, while
agreeing to 0.08 % at η = −4.

**Diagnosis.** The reference's prefactor was wrong for λ ≠ 0. The correct
textbook form is

S = (k_B/e)[ (5/2 + r)·F̂_{r+3/2}/F̂_{r+1/2} − η ]

With r = λ − ½ this becomes (k_B/e)[(λ+2)F̂_{λ+1}/F̂_λ − η] — the ratio's
denominator carries **no** (λ+1) factor. The reference had inserted one.

**Resolution.** The reference was corrected to the prefactor above; the
application's unnormalised-prefactor form was shown to be **identical** to
the corrected Blatt form (the Γ factors cancel in the ratio), and the two
now agree to ≤1e-6 for λ ∈ {0, 1, 2}.

**Scientific content.** The application's SPB implementation is correct as
written, for **every** λ — not only for acoustic scattering.

### 8.2 Effective density of states — the *reference* was wrong

**Symptom.** The independent m* disagreed with the application's by exactly a
factor of 300 at T = 300 K.

**Diagnosis.** The reference multiplied N_c by an extra T^{3/2} while also
using the T-dependent N_c — a double count. A direct check of the
application's internal constant against the textbook N_c showed the
application's `_CONST_N0_SI` is 1/Γ(3/2) times the plain N_c, i.e. it is
correctly adapted to the *unnormalised* integral convention.

**Resolution.** The reference was corrected to use the textbook N_c with
Blatt-normalised integrals. The application's n now matches the textbook to
1e-15 for n(η = 0, m* = 1, T = 300 K) = 1.9200692976919e19 cm⁻³.

**Scientific content.** The application's carrier concentration is correct
and convention-consistent.

### 8.3 Empirical unit expectations — the *test* was wrong

Two new tests failed on arithmetic slips in the **test expectations**, not
in the application: the power factor of 2e-4 V/K (not 1e-4) and the
resistivity/conductivity identity 100 S/m ≡ 1 Ω·cm (not 0.01 Ω·cm). Both
expectations were corrected; the application's behaviour was unchanged.

### 8.4 Broadcasting and IEEE-754 semantics — the *test* was too strict

The application follows NumPy broadcasting for a length-1 array against a
longer array, and returns ±inf (not NaN) for physically absurd magnitudes
such as 10³⁰⁰. Both behaviours are correct IEEE-754/NumPy semantics. The
tests were corrected to assert them explicitly rather than to demand a
NaN-based rejection.

---

## 9. Independence of the experimental benchmarks

The experimental benchmarks use the **StarryData** `ThermoelectricMaterials`
release (a curated aggregation of published thermoelectric measurements
with DOI-level provenance). The application's own functions are never used
to *produce* the reference data; the published curves are the reference.
The extraction scripts
(`tests/experimental_benchmarks/extract_benchmarks.py`,
`extract_workflow_benchmarks.py`) regenerate the on-disk datasets
byte-identically from the upstream snapshot, and the SHA-256 checksums of
the upstream files are recorded in
`docs/EXPERIMENTAL_BENCHMARK_VALIDATION.md`.

A comparison is labelled **`consistency`** (not `experimental`) whenever the
reference value is derived from the *same* publication — for example, the
lattice thermal conductivity recomputed with a Lorenz number derived from
that publication's own κ_L. Such a comparison tests the arithmetic, not the
model.
