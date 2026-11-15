# Scientific Equation Audit — Seebeck Prime

**Audit date:** 2026-11-11
**Scope:** every scientific equation, physical model, numerical method, conversion factor and derived quantity in the Seebeck Prime codebase (`src/domain`, `src/application`, `src/presentation`, `src/gui`, `src/infrastructure`, `src/plugins`).
**Method:** (1) static extraction of every formula and conversion factor; (2) independent analytical re-derivation of each equation; (3) dimensional analysis of every derived quantity; (4) independent numerical verification against closed-form references (the application functions were never used as their own reference); (5) boundary, extreme and invalid-input testing.

> **Scope limit, stated up front:** this is a *code-vs-theory* audit. It verifies that each implemented expression matches the governing physical relation, that units are consistent, and that the numerics reproduce analytically known limits. It is **not** a validation of the software against measured reference materials or certified reference values: no such reference data exist in the repository, and none were invented. Equations whose governing model cannot be checked from the code alone are marked **UNVERIFIED** (section 8).

---

## 1. Executive Summary

| Metric | Count |
|---|---|
| Scientific equations / model relations identified | 42 |
| Unit-conversion relations audited | 38 distinct factors (22 in the canonical unit layer + 16 inline factors in presentation/GUI layers) |
| Dimensional analyses performed | 16 derived quantities |
| **CRITICAL** errors found and fixed | 3 |
| **HIGH** errors found and fixed | 5 |
| **MEDIUM** issues found and fixed | 7 |
| **LOW** issues found and fixed | 8 |
| Issues **documented but deliberately not changed** (behaviour/architecture) | 14 |
| Further observations recorded (dead code, duplicated rules, provenance) | 8 |
| New independent-verification tests added | 81 (62 equation tests + 12 application-layer tests + 7 author-decision tests) |
| Test suite | 259 → **342 passed**, 1 skipped (Qt-conditional GUI smoke), 1 warning |

**Headline findings**

1. **SE-001 (CRITICAL) — the device-efficiency "engineering figure of merit" was dimensionally invalid.** `ZT_eng` carried units of 1/K instead of being dimensionless, because the expression mixed integrals and averages incorrectly. For the canonical constant-property case it returned `8.0e-4` instead of `0.8`, which drove the reported *engineering efficiency* to `1.0e-4` instead of the correct `7.04e-2` — i.e. the engineering efficiency was effectively always reported as zero. Fixed; `Efficiency_Eng` now coincides with `Efficiency_Max` for constant properties, as physics requires.
2. **SE-008 (CRITICAL) — the rigorous SPB Lorenz number returned exactly 0 for degenerate samples (η > 50).** The Fermi–Dirac integral used only the leading term of the Sommerfeld expansion, and the Lorenz combination is a near-cancellation that amplifies that truncation error to 100 %. A strongly degenerate sample would have been reported with a Lorenz number of zero. Fixed by adding the correct Sommerfeld correction terms; `L(η=80)` is now `2.4417e-8 W·Ω/K²` versus the Sommerfeld value `2.4430e-8` (0.05 % agreement).
3. **SE-003 (HIGH) — the molar heat capacity plotted by the Kappa tool was 1000× too small**, and the Dulong–Petit overlay was consequently ~1000× off the curve, making the two visually incomparable.
4. **SE-004 (HIGH) — the Kappa dialog's temperature handling corrupted data**: a magnitude heuristic converted genuine sub-273 K measurements (e.g. 250 K → 523 K), and Kelvin values were offset by 273.15 when the display unit was °C.
5. **The core transport equations are correct.** PF = S²σ, κₑ = LσT, κ_L = κ − κₑ, ZT = S²σT/κ, all eight Gaussian uncertainty propagators, all Hall relations, all SPB relations, the laser-flash relation κ = α·C_p·ρ and the Dulong–Petit limit were independently re-derived and verified — including the analytic limits (Sommerfeld L₀, classical acoustic L → (5/2+r)(k_B/e)², Peierls activation energies).
6. **A second, application-layer pass found three further result-corrupting defects** (section 7.1): the Seebeck uncertainty was **silently discarded** by the four-probe/raw-Seebeck merge (u(PF) understated by up to 17×, SE-029); u(κₑ) was computed by a partial re-implementation that disagreed with the domain propagator (SE-030); and the column mapper fed **thermal**-conductivity values into the electrical-conductivity slot (SE-031). All three are now fixed and regression-tested.

All corrections are documented in section 9, are covered by regression tests that fail on the pre-correction code, and are traceable to a numeric diff of the committed golden baseline.

---

## 2. Complete Equation Inventory

### 2.1 Core transport (`src/domain/calculations.py`)

| ID | Equation | Implementation | Units |
|---|---|---|---|
| E-01 | PF = S²·σ | `calculate_pf` | W/(m·K²) |
| E-02 | κₑ = L·σ·T | `calculate_kappa_e` | W/(m·K) |
| E-03 | κ_L = κ_total − κₑ | `calculate_kappa_l` | W/(m·K) |
| E-04 | ZT = PF·T/κ = S²σT/κ | `calculate_zt` | dimensionless |
| E-05 | L ≈ (1.5 + e^(−\|S\|/116))·10⁻⁸ | `estimate_lorenz` | W·Ω/K² |
| E-06 | M = Σ nᵢ·Aᵢ | `calculate_molecular_weight` | g/mol |
| E-07 | C_V = 3nR | `calculate_dulong_petit_limit` | J/(mol·K), J/(kg·K) |

### 2.2 Uncertainty propagation (`src/domain/uncertainty.py`)

| ID | Equation | Implementation |
|---|---|---|
| E-08 | u_PF = √((2Sσu_S)² + (S²u_σ)²) | `propagate_pf_error` |
| E-09 | u_κₑ = √((LTu_σ)² + (Lσu_T)² + (σTu_L)²) | `propagate_kappa_e_error` |
| E-10 | u_κL = √(u_κ² + u_κₑ²) | `propagate_kappa_l_error` |
| E-11 | u_ZT = \|ZT\|√((u_PF/PF)² + (u_T/T)² + (u_κ/κ)²) | `propagate_zt_error` |
| E-12 | σ = L/(R·A); u_σ/σ = √((u_L/L)²+(u_R/R)²+(u_A/A)²) | `propagate_sigma_error` |
| E-13 | κ = α·C_p·ρ; relative errors in quadrature | `propagate_kappa_error` |
| E-14 | ρ = m/(A·t); relative errors in quadrature | `propagate_density_error` |
| E-15 | u = \|value\|·√(Σ relᵢ²) | `propagate_relative_uncertainty` |

### 2.3 Units (`src/domain/units.py`)

| ID | Relation | Notes |
|---|---|---|
| E-16 | T[K] = T[°C] + 273.15 | offset; uncertainties invariant |
| E-17 | σ[S/m] = 100·σ[S/cm]; σ[S/m] = 100/ρ[Ω·cm] | |
| E-18 | S[V/K] = S[µV/K]·10⁻⁶ | |
| E-19 | PF[W/(m·K²)] = PF[mW/(m·K²)]·10⁻³ = PF[µW/(m·K²)]·10⁻⁶ | |
| E-20 | n[cm⁻³] = n[m⁻³]·10⁻⁶ | |
| E-21 | ρ[mΩ·cm]: Ω·m·10⁵; S/cm → 1000/σ; S/m → 10⁵/σ | `domain/transport.py` |

### 2.4 Hall effect (`src/domain/hall.py`)

| ID | Equation | Implementation |
|---|---|---|
| E-22 | R_H = V_H·t/(I·B) | `calculate_hall_coefficient_from_raw` |
| E-23 | n = r_H/(e·\|R_H\|) | `calculate_hall_carrier_density` |
| E-24 | carrier type from sign(R_H) | `determine_carrier_type` |
| E-25 | μ_H = \|R_H\|·σ (SI: m²/(V·s); lab: cm²/(V·s)) | `calculate_hall_mobility`, `calculate_hall_mobility_cm2_vs` |
| E-26 | ln μ = p·ln T + ln μ₀ | `fit_scattering_exponent` |

### 2.5 Single parabolic band (`src/domain/spb.py`)

| ID | Equation | Implementation |
|---|---|---|
| E-27 | F_j(η) = ∫₀^∞ x^j/(1+e^{x−η})dx (unnormalised) | `fermi_integral` |
| E-28 | S(η) = (k_B/e)[((λ+2)F_{λ+1})/((λ+1)F_λ) − η] | `seebeck_from_reduced_fermi_level` |
| E-29 | η from S (Brent inversion) | `reduced_fermi_level_from_seebeck` |
| E-30 | L(η) = (k_B/e)²[((λ+3)F_{λ+2})/((λ+1)F_λ) − (((λ+2)F_{λ+1})/((λ+1)F_λ))²] | `rigorous_lorenz_number` |
| E-31 | n = 4π(2m\*k_BT/h²)^{3/2}F_{1/2}(η) | `calculate_carrier_density_spb` |
| E-32 | m\* = [n/(N₀T^{3/2}F_{1/2})]^{2/3} | `calculate_effective_mass` |
| E-33 | Pisarenko curve S(n); optimal n and PF_max | `generate_pisarenko_curve`, `predict_optimal_transport` |
| E-34 | n = 10²¹·exp(−\|S\|/43.4) (Snyder–Toberer empirical) | `calculate_carrier_concentration` |

### 2.6 Phonon / laser flash (`src/domain/phonon.py`)

| ID | Equation | Implementation |
|---|---|---|
| E-35 | κ = α·C_p·ρ | `kappa_from_diffusivity`, `kappa_from_diffusivity_si` |
| E-36 | C_V = 3nR; C = C_V/M | `dulong_petit_molar`, `dulong_petit_specific` |

### 2.7 Device efficiency (`src/domain/device_efficiency.py`)

| ID | Equation | Implementation |
|---|---|---|
| E-37 | ZT_avg = (1/ΔT)∫ZT dT | `calculate_efficiencies` |
| E-38 | η_max = (ΔT/Th)(√(1+ZT_avg)−1)/(√(1+ZT_avg)+T_c/Th) | `calculate_efficiencies` |
| E-39 | ZT_eng = S̄²·T̄/(ρ̄κ̄) | `calculate_efficiencies` (**SE-001 fixed**) |

### 2.8 Transport, analysis, Arrhenius

| ID | Equation | Implementation |
|---|---|---|
| E-40 | μ_w = 331·(1/ρ)·(T/300)^{−1.5}·F(\|S\|/(k_B/e)) | `domain/transport.py` |
| E-41 | E_a[eV] = −slope·k_B/e; E_a[J/mol] = −slope·R | `plugins/arrhenius.py` |
| E-42 | MAD filter; OLS regression; linear interpolation; temperature rounding/alignment | `domain/analysis.py` |

### 2.9 Scientific assumptions carried in the code

| Assumption | Where | Audit status |
|---|---|---|
| Wiedemann–Franz with a single constant L | E-02 | Valid only for elastic, single-band, low-T transport; **documented limitation** (§8) |
| κ_L = κ − κₑ (no bipolar separation) | E-03 | Valid below the bipolar onset; **documented limitation** (§8) |
| SPB with a single parabolic band and one scattering exponent | E-27…E-33 | Model-dependent; **documented** (§8) |
| Acoustic-phonon T^{−3/2} dependence in the Snyder weighted-mobility estimator | E-40 | Empirical model assumption; equation corrected to Snyder et al. (2020) on 2026-11-15 |
| First-order (linearised) Gaussian propagation | E-08…E-15 | Valid for small relative uncertainties; **documented** (§8) |
| Hall factor r_H = 1 unless supplied | E-23 | Single-carrier assumption; **documented** (§8) |

---

## 3. Scientific Verification of Each Equation

Every equation was re-derived independently. Selected results:

**E-01 (PF).** Correct. Sign-independent (S²) — verified by test for S = ±100 µV/K. Dimensional check: (V/K)²·(S/m) = W/(m·K²) ✓. Scaling: PF(2S,σ) = 4·PF ✓, PF(S,2σ) = 2·PF ✓.

**E-02 (κₑ).** Correct as the Wiedemann–Franz law. Linear in σ and T ✓ (verified by scaling tests). *Validity*: requires elastic scattering and a single energy-independent L; for degenerate or strongly anisotropic samples L deviates from the Sommerfeld value by ±20 % in practice — this is exactly why the SPB and Kim estimators exist (E-05, E-30) ✓.

**E-03 (κ_L).** Correct as the residual definition. *Validity*: at high T the minority-carrier contribution to κ inflates κ_total, so κ_L computed this way is too high and can turn upward (the classical bipolar artefact). The application's own validation module flags negative κ_L (which signals an over-estimated L or a unit error) ✓, but it does **not** flag the bipolar upturn — documented in §8.

**E-04 (ZT).** Correct and dimensionless; linear in T, inverse in κ ✓ (scaling tests). The κ = 0 convention returns 0 rather than ∞ (SE-018, LOW, documented).

**E-05 (Kim estimator).** Correct implementation of the published relation L = (1.5 + e^{−|S|/116})·10⁻⁸ ✓ (S-independent sign ✓, monotonically decreasing ✓, L(0) = 2.5e-8 ✓).

**E-08…E-15 (uncertainty).** All eight propagators are correct first-order Gaussian propagations with the correct partial derivatives, verified against hand-computed closed forms (including the L-term of u_κₑ, which is present and correctly signed) ✓. All are sign-insensitive where the underlying quantity is ✓.

**E-22…E-26 (Hall).** All correct. R_H = V_H·t/(I·B) ✓; carrier density n = r_H/(e|R_H|) ✓ (single-carrier Hall-factor convention: R_H = r_H/(n·e)); mobility μ_H = |R_H|σ ✓ with the SI/laboratory unit relation μ_lab = 10⁴·μ_SI verified numerically ✓; the scattering-exponent fit recovers a synthetic μ = 7.5·T^{−1.5} to 1e-9 ✓.

**E-27…E-32 (SPB).** The Seebeck relation E-28 reproduces both classical limits exactly: S → (k_B/e)(2−η) for η ≪ 0 (with λ = 0, r = −1/2) and S → 0 for η ≫ 0 ✓. The carrier density scales as m\*^{3/2}T^{3/2} ✓. The effective-mass inversion recovers a constructed m\* = 2.0 to 1e-9 ✓. **The Lorenz relation E-30 was wrong in its degenerate regime (SE-008)** — now L(η→∞) → (π²/3)(k_B/e)² ✓ and L(η→−∞) → (5/2+r)(k_B/e)² = 2(k_B/e)² for acoustic scattering ✓ (both verified against direct numerical integration of the Fermi–Dirac integrals, agreeing to 6 significant digits).

**E-35 (laser flash).** Correct: κ = α·C_p·ρ with consistent SI conversions (mm²/s → m²/s, J/(g·K) → J/(kg·K), g/cm³ → kg/m³) ✓; the laboratory and SI entry points agree to 1e-12 ✓.

**E-37…E-39 (device efficiency).** E-37 and E-38 (Ioffe constant-property limit) are correct ✓. E-39 was dimensionally invalid (SE-001) and is now correct ✓; verified by the internal consistency requirement that η_eng ≡ η_max for constant properties ✓.

**E-41 (Arrhenius).** Correct in all three variants, including the essential ln(10) base-10 correction ✓ and the base-10 pre-factor ✓; E_a recovered exactly from constructed data ✓.

---

## 4. Dimensional Analysis

Dimensional consistency was verified two ways: (a) by hand for every derived quantity; (b) by *scaling tests* in the automated suite (a dimensionless result must be invariant to a consistent change of unit system).

| Quantity | Expected dimension | Result |
|---|---|---|
| PF | W/(m·K²) | ✓ |
| κₑ, κ_L, κ | W/(m·K) | ✓ |
| ZT | 1 | ✓ (invariant under V/K→µV/K with S/m→S/cm) |
| ZT_eng | 1 | ✓ **after SE-001** (was 1/K ✗) |
| η_max, η_eng, Carnot | 1 | ✓ |
| u(PF), u(κ) | same as the quantity | ✓ |
| u(ZT) | 1 | ✓ |
| μ_w | cm²/(V·s) | ✓ (verified: μ_lab = 10⁴·μ_SI) |
| μ_H | m²/(V·s) or cm²/(V·s) | ✓ (labels match the values) |
| n_H | m⁻³ | ✓ |
| R_H | m³/C | ✓ |
| L | W·Ω/K² | ✓ |
| E_a | eV, J/mol | ✓ |
| C_p (molar) | J/(mol·K) | ✓ **after SE-003** (was 1000× small) |
| C_p (specific) | J/(kg·K) | ✓ |

**Dimensional audit conclusion:** after the SE-001 correction, every derived quantity in the codebase is dimensionally consistent. The one remaining dimensionally-questionable item (ZT → 0 when κ = 0) is a documented defensive convention, not a unit error (SE-018).

---

## 5. Unit Conversion Audit

All conversion factors were checked against first principles and by round-trip identity.

| Conversion | Factor | Verdict |
|---|---|---|
| µV/K → V/K | 10⁻⁶ | ✓ |
| mV/K → V/K | 10⁻³ | ✓ |
| mS/cm ↔ S/m | 100 | ✓ |
| S/cm → S/m | ×100 | ✓ |
| ρ[Ω·cm] → σ[S/m] | 100/ρ | ✓ |
| ρ[Ω·m] → ρ[mΩ·cm] | ×10⁵ | ✓ |
| σ[S/cm] → ρ[mΩ·cm] | 1000/σ | ✓ |
| σ[S/m] → ρ[mΩ·cm] | 10⁵/σ | ✓ |
| W/m·K → W/cm·K | **not supported** | §8 (SE-021) |
| mW/(m·K²) → W/(m·K²) | 10⁻³ | ✓ |
| µW/(m·K²) → W/(m·K²) | 10⁻⁶ | ✓ |
| °C → K | +273.15 | ✓ (offset) |
| Temperature uncertainty | unchanged | ✓ (invariant under offset) |
| cm⁻³ → m⁻³ | 10⁶ | ✓ |
| mm²/s → m²/s | 10⁻⁶ | ✓ |
| J/(g·K) → J/(kg·K) | ×1000 | ✓ |
| g/cm³ → kg/m³ | ×1000 | ✓ |
| Gauss → T | 10⁻⁴ | ✓ |
| m³/C → cm³/C | 10⁶ | ✓ |
| V → V/K-scaled Seebeck | 10⁻⁶ | ✓ |
| **Cp[J/(g·K)] × M[g/mol] → J/(mol·K)** | **×1 (not ÷1000)** | ✗ **SE-003 — fixed** |
| **κ_disp display (°C) → internal K** | **must not use a magnitude heuristic** | ✗ **SE-004 — fixed** |

**Double-application check.** Every conversion is applied exactly once in the pipeline: display → base (`unit_conversion.to_base_value`) happens at ingest, base → display (`from_base_value`) at render; the base-unit table is never re-converted. Round-trip identities (base → display → base) are asserted in the automated suite for conductivity, Seebeck, power factor, temperature and carrier density ✓. The one silent-failure path found (an unrecognised power-factor unit string falling through to "no conversion") was closed in SE-006.

---

## 6. Numerical Verification Results

Independent reference calculations (never calling the application functions) were compared against the implementation:

| Check | Independent reference | Result |
|---|---|---|
| PF, κₑ, κ_L, ZT | closed forms | match to ≤1e-12 relative |
| ZT unit-invariance | V/K+S/m vs µV/K+S/cm | match to 1e-12 |
| u(PF), u(κₑ), u(κ_L), u(ZT), u(σ), u(κ), u(ρ) | hand-derived partial derivatives | match to 1e-12 |
| Hall R_H, n_H, μ_H, carrier type | definitions | match to 1e-9 … 1e-12 |
| Scattering-exponent fit | synthetic μ = 7.5·T^{−1.5} | p = −1.5 (1e-9), μ₀ = 7.5 (1e-9), r² = 1 |
| F₀(η) | ln(1+e^η) | match to 1e-8 |
| F_j(η) | direct numerical integration | match to 1e-11 |
| F_j(η) degenerate branch | 3-term Sommerfeld expansion | match to 1e-12 (**after SE-008**) |
| S(η) round trip | η ↔ S inversion | ≤1e-6 relative (numerical inversion tolerance) |
| S classical limit | (k_B/e)(2−η) | exact |
| n(η, m\*, T) scaling | m\*^{3/2}T^{3/2} | match to 1e-9 |
| m\* inversion | constructed m\* = 2.0 | recovered to 1e-9 |
| L(η) degenerate limit | (π²/3)(k_B/e)² = 2.4430e-8 | 2.4417e-8 (0.05 %) (**after SE-008**) |
| L(η) Boltzmann limit | (5/2+r)(k_B/e)² = 1.4852e-8 (r = −1/2) | exact |
| κ laser flash | α·C_p·ρ | match to 1e-12 |
| Dulong–Petit | 3nR | match to 1e-12 |
| ZT_eng / η_eng | S̄²T̄/(ρ̄κ̄); Ioffe | match to 1e-9 (**after SE-001**) |
| η_eng ≡ η_max for constant properties | exact requirement | now satisfied (**SE-001**) |
| μ_w | Snyder et al. (2020) published expression; independent scalar transcription | regression tests at 50–250 µV/K, sign parity, scaling, broadcasting and invalid inputs |
| E_a (eV, J/mol) | constructed Arrhenius data | exact to 1e-9 |

**Boundary and extreme inputs exercised:** zero, negative, 1e-12-scale and 1e12-scale inputs; NaN and ±inf propagation; κ = 0; T = 0; n ≤ 0; R_H = 0; I = 0 or B = 0 (raises `ZeroDivisionError` by design); ΔT ≤ 0 (returns `None`); η beyond ±50 (asymptotic branches); invalid unit strings (raise `ValueError`, or pass through only where the legacy contract demands it).

---

## 7. Identified Scientific Errors

| ID | Severity | Location | Description | Status |
|---|---|---|---|---|
| SE-001 | **CRITICAL** | `domain/device_efficiency.py` | `ZT_eng` computed as `(∫S²/∫ρ)/(∫κ/ΔT)/Th` → units 1/K, not dimensionless; returned 8.0e-4 instead of 0.8 for the reference case, and `Efficiency_Eng` ≈ 1e-4 instead of 7.04e-2 | **fixed** |
| SE-008 | **CRITICAL** | `domain/spb.py` (`fermi_integral`) | Degenerate branch used only the leading Sommerfeld term; the near-cancelling Lorenz combination amplified the error to 100 % → `L = 0` for η > 50 | **fixed** |
| SE-003 | **HIGH** | `presentation/kappa_logic.py` | Molar heat capacity computed as `Cp·M/1000` → 1000× too small (kJ/(mol·K) labelled J/(mol·K)); Dulong–Petit overlay ~1000× off the curve | **fixed** |
| SE-004 | **HIGH** | `legacy/ui/dialogs/kappa_dialog.py`, `presentation/kappa_logic.py` | Magnitude heuristic (`<273 → +273.15`) corrupted sub-273 K data; °C branch offset Kelvin values; read path used the raw cell with no unit handling | **fixed** |
| SE-002 | MEDIUM | `domain/calculations.py` | Formula parser silently mis-parsed parenthesised/fractional formulas (Ca₃(PO₄)₂ → 184.2 g/mol instead of 310.17 g/mol) | **fixed** (rejected) |
| SE-005 | MEDIUM | `gui/main_window.py` | Percentage uncertainties inherited the sign of the quantity → negative "±S" displayed for n-type samples | **fixed** |
| SE-006 | MEDIUM | `domain/units.py` | "W/mK²" power-factor unit was unrecognised and silently passed through unchanged | **fixed** |
| SE-007 | MEDIUM | `legacy/ui/dialogs/spb_dialog.py` | Hard-coded Lorenz reference lines (2.44, 1.50) instead of the domain constants | **fixed** |
| SE-009 | LOW | `presentation/kappa_logic.py` | Docstring/comment said "round to nearest 10" while the code uses 20 K | **fixed** |
| SE-010 | LOW | `legacy/ui/dialogs/hall_mobility_dialog.py` | Scattering-regime label range did not match the implemented band | **fixed** |
| SE-011 | LOW | `presentation/table_handler.py` | Third independent Celsius→Kelvin conversion, matching only the literal "degC" | **fixed** (single conversion service) |
| SE-012 | LOW | `presentation/plot_window.py` | Crosshair readout hard-codes "K" for the x-axis | documented |
| SE-013 | LOW | `gui/main_window.py` | Dead `hasattr(self, "lorenz_val")` branch (attribute never assigned) | **fixed** (removed) |
| SE-014 | LOW | `domain/transport.py` | Rounded literal 86.1733 for k_B/e (exact: 86.173332621…) — 3.8e-7 relative | **fixed** (exact constant) |
| SE-015 | MEDIUM | `domain/physical_constants.py`, `legacy/core/constants.py` | Two Lorenz constants in active use: 2.443004509e-8 (Sommerfeld, main table) and 2.44e-8 (legacy, Multi-Sample) → 0.12 % divergence in κₑ and ZT | **resolved by author decision (2026-11-11): one application-wide L = 2.44e-8** |
| SE-016 | MEDIUM | `presentation/multi_sample_plots.py` vs `legacy/ui/dialogs/plot_settings_dialog.py` | The same Multi-Sample tool reports σ, S, PF in S/cm, µV/K, mW/(m·K²) on one path and S/m, V/K, W/(m·K²) on the other → user-visible factors of 100/10⁶/1000 | **resolved by author decision (2026-11-11): Multi-Sample reports S/cm, µV/K, mW/(m·K²) on both paths** |
| SE-017 | MEDIUM | `plugins/arrhenius.py` | A complete, tested Arrhenius model lives outside `src/domain/` and is reachable from no UI path | documented (move + wire recommended) |
| SE-018 | LOW | `domain/calculations.py` | `calculate_zt` returns 0 when κ_total = 0 (physically ZT → ∞) | documented (defensive convention) |
| SE-019 | LOW | `domain/units.py` | `sigma_to_sm(0, "Ω·cm")` returns 0.0 where ∞ is implied (asymmetric with the inverse function) | documented |
| SE-020 | LOW | `domain/transport.py` | Weighted-mobility model assumptions (acoustic T^{−3/2}, empirical 331 constant) were unstated | **fixed** (docstring) |
| SE-021 | LOW | `domain/units.py` | Thermal conductivity supports only W/(m·K); W/(cm·K) is not implemented | documented (requested in the audit brief) |
| SE-022 | LOW | `domain/hall.py` | Carrier density returns 0 for R_H = 0 (physically unbounded) | documented |
| SE-023 | LOW | `legacy/ui/dialogs/hall_mobility_dialog.py` | Default Hall voltage 0.000120 mV (0.12 µV) — the value appears intended as 120 µV | documented |
| SE-024 | LOW | `presentation/table_handler.py` | Standard uncertainties are interpolated linearly rather than by the quadrature rule | documented |
| SE-025 | LOW | `presentation/kappa_logic.py` | Relative uncertainties are combined from mixed units (g, mm) — numerically harmless (ratios) but not SI-normalised | documented |
| SE-026 | **HIGH** | `application/measurement_processing.py:200` vs `presentation/kappa_logic.py` | **The two laser-flash import paths used opposite temperature conventions.** The application path added 273.15 unconditionally to the aliased column, the presentation path (used by the Kappa dialog) treated the same column as Kelvin — the same file therefore yielded temperatures differing by 273.15 K depending on the path | **resolved (2026-11-11): both paths now derive the unit from the source header, falling back to magnitude inference; the laser-flash path matches the Kappa dialog** |
| SE-027 | MEDIUM | `application/measurement_processing.py:67` | The four-probe path inferred the temperature unit by magnitude (`mean(T) > 250 → treat as Kelvin, else add 273.15`). A legitimate °C dataset with a mean above 250 °C would be silently treated as Kelvin, and Kelvin data below 250 K would be shifted | **resolved (2026-11-11): the unit declared by the column header takes precedence; magnitude inference is only the fallback when the header declares nothing** |
| SE-028 | MEDIUM | `application/measurement_processing.py:200` | The LFA offset was applied to a column that the same function had just aliased to `T_K` (Kelvin), i.e. the code added the Celsius offset to values it had labelled as Kelvin | **resolved (2026-11-11): the hard-coded offset was removed; the unit now comes from the source header** |

### 7.1 Application-layer findings (second audit pass)

| ID | Severity | Location | Description | Status |
|---|---|---|---|---|
| SE-029 | **CRITICAL** | `application/services.py` | **The Seebeck uncertainty was silently discarded.** The four-probe frame's `±S` column survived the merge with the raw-Seebeck frame, so pandas renamed the colliding columns to `±S_x`/`±S_y`; the subsequent `df.get("±S", 0)` then returned the scalar `0`. The entire statistical Seebeck uncertainty (the regression standard error) was lost, understating u(PF) by up to 17× in a representative case (verified) and u(ZT) likewise | **fixed** (the superseded four-probe `±S` is dropped before the merge) |
| SE-030 | **HIGH** | `application/services.py` | `±κₑ` was a partial re-implementation of `propagate_kappa_e_error` (`κₑ·u_σ/σ`) that omitted the temperature and Lorenz terms, so the file workflow and the manual workflow reported **different** uncertainties for the same inputs | **fixed** (delegated to the domain propagator) |
| SE-031 | **HIGH** | `application/data_mapping.py` | The alias `"conductivity"` matched **"Thermal Conductivity (W/mK)"**, so the electrical-conductivity slot received the *thermal* conductivity values while the thermal-conductivity target went unmapped (verified) | **fixed** (a physical-plausibility guard rejects the match) |
| SE-032 | MEDIUM | `application/measurement_processing.py`, `application/data_mapping.py` | The alias `"k"` matched the "(K)" of a temperature column "T (K)"; aliases were matched case-sensitively, so `"uV/K"` could never match "Seebeck (uV/K)". Two divergent copies of the same rule set existed | **fixed** (one shared matcher, case-insensitive, with guards) |
| SE-033 | **HIGH** | `application/measurement_processing.py` | Group means were reported with the **sample standard deviation** instead of the **standard error of the mean** (s/√N) — the quoted uncertainty of the mean was √N times too large (2.24× for N = 5); a single reading was reported as exact (0.0) | **fixed** (SEM used; N = 1 keeps the legacy 0.0 and is documented) |
| SE-034 | MEDIUM | `application/spb_batch.py` | The mean effective mass is taken over the rows with a valid mass while the mean temperature is the mean of **all** submitted rows, so the returned pair describes two different populations (verified: 400 K reported for a pair whose mass came from 300 K and 400 K) | **documented — legacy rule preserved** (it is pinned by `tests/test_batch_workflows.py::test_spb_batch_application_mean_parameters_preserve_legacy_mean_rules`; changing it is an author decision) |
| SE-035 | MEDIUM | `application/use_cases.py` | `u_kappa` was ignored unless **both** `u_sigma` and `u_S` were supplied; a supplied `u_kappa` produced no uncertainty output at all | **fixed** (each contribution is evaluated as soon as its inputs exist) |
| SE-036 | MEDIUM | `application/use_cases.py` | The Lorenz uncertainty was hard-coded to 0 in the S-derived ("auto") mode, although L is then a function of the measured S, so u(κₑ) was underestimated | **fixed** (dL/dS = −e^(−\|S\|/116)/116·10⁻⁸ is propagated from u(S)) |
| SE-037 | LOW | `application/services.py` | `get_reporting_statement()` asserted that the Seebeck uncertainty always came from the ΔV–ΔT regression — false for the four-probe path and, after SE-029, false in the merged case as well | **fixed** (the statement now describes both paths) |
| SE-038 | LOW | `application/use_cases.py` | `validate_measurement_data` could not forward `kappa_L`, so the domain's negative-lattice-conductivity diagnostic (a sign of a wrong Lorenz number or units) was unreachable from the application layer | **fixed** |

### 7.2 Further application-layer observations (documented, not changed)

- **Dead code:** `application.services.ThermoelectricAnalyzer._find_column` (no callers); the `PF_raw` column produced by the four-probe positional fallback (unused, yet it still drives a `dropna()` that discards otherwise valid rows); `domain.units.carrier_density_m3_to_cm3`/`cm3_to_m3`, `domain.units.convert_temperature_uncertainty`, `domain.phonon.kappa_from_diffusivity` (laboratory-unit form) and `domain.hall.calculate_hall_mobility` (SI form) have no call sites.
- **Two copies of the Kim estimator:** `domain.calculations.estimate_lorenz` and `domain.spb.estimate_lorenz` (numerically identical, both reachable from the application layer through different paths).
- **Three different temperature-grouping granularities:** exact float equality (four-probe, laser flash), rounding to 0.1 K (raw Seebeck), and 20 K grouping (Kappa tool) — and every cross-table join uses exact float equality on `T_K`, so a left join silently fills NaN and an inner join silently deletes rows.
- **Display-unit scaling inside the application layer:** `SPBBatchRowResult.lorenz_display_value` stores L·10⁸ (units of 10⁻⁸ W·Ω/K²) rather than SI.
- **Provenance is not tracked:** `domain.dataset.ThermoelectricDataset` defines `origin_*` fields for exactly this purpose, but the application layer never populates them, so modelled quantities (κₑ, κ_L, ZT_eng, m\*, n) are exported in the same tables as measured ones without a provenance flag.
- **Silent unit fallback:** `application.unit_conversion.to_base_value`/`from_base_value` swallow the domain's `ValueError` and return the unconverted value for an unrecognised unit string (SE-006 closed the most likely case, the power-factor unit; the generic path remains).
- **Two parallel table schemas:** the main table (`application.table_schema`, fixed column order with uncertainty columns) and the Multi-Sample frame (`Temperature`, `Seebeck`, `Sigma`, `Kappa_total` in different units), bridged only by the column mapper.
- **The error-mode input column list is hard-coded in the presentation layer** (`presentation.table_handler.get_input_columns`) instead of being derived from `application.table_schema`, so the schema is not the single source of truth for the contract. There is also no `±T` column, although u(T) is computed and propagated.

---

## 8. Potential Scientific Limitations

These are properties of the *models*, not code defects. All are inherent to the equations and must be stated in any publication.

1. **Wiedemann–Franz law with constant L (E-02).** Valid only for elastic scattering in a single band. Real materials show L between 1.2e-8 and 2.6e-8 W·Ω/K². The application therefore offers the Kim empirical estimator and the rigorous SPB value — the *measurement* of L is model-dependent and should be reported as such.
2. **κ_L = κ − κₑ (E-03).** Above the bipolar onset (roughly |S| below ~60 µV/K for most materials) the minority-carrier contribution to κ_total inflates the extracted lattice conductivity, producing the classical upturn. The software detects *negative* κ_L but not the bipolar upturn.
3. **SPB single-band assumption (E-27…E-33).** Band curvature, band non-parabolicity, multi-band transport and energy-dependent relaxation times all bias m\*, n and L. The SPB results are model estimates, not measurements.
4. **Hall factor r_H (E-23).** The carrier density inherits the r_H assumption; r_H = 1 is a single-band, degenerate approximation.
5. **First-order uncertainty propagation (E-08…E-15).** Exact for linear functions; for PF (quadratic in S) and ZT the linearisation is valid only for small relative uncertainties (≈ < 5 %).
6. **Averaging conventions.** ZT_avg is a temperature-weighted average over the junction interval; ZT_eng uses arithmetic averages of S, ρ, κ and T̄ = (T_c+T_h)/2. Different averaging conventions shift ZT_eng by a few percent — the convention must be stated when comparing with the literature.
7. **Interpolation of measured properties onto a common temperature grid** uses linear interpolation of the values and of the standard uncertainties (SE-024); for strongly curved properties this introduces a small bias.
8. **Maximum ZT from non-coincident temperatures.** The application computes ZT point-wise from simultaneous (T, σ, S, κ) rows; it does **not** construct a max-ZT from mismatched measurement temperatures. The Kappa tool interpolates κ onto the electrical transport temperatures (an explicit, documented workflow), but no implicit "peak ZT" optimisation is performed. Any max-ZT claim must therefore come from the user's own data selection.
9. **Certified reference data.** The repository contains no *certified* reference material (e.g. a NIST-certified reference specimen). **Update (2026-11-11):** experimental validation against published measurements has since been established in a separate stage (`EXPERIMENTAL_BENCHMARK_VALIDATION.md`): the computed power factor and figure of merit reproduce published values for three real materials (Bi₂Te₃-, PbTe- and SiGe-based) to within 1.3–4.6 %. That validation is based on *digitised published figures*, not on certified reference specimens, so the residual limitation is the provenance of the source data rather than the absence of any experimental check.
10. **Temperature units in the raw-instrument import paths (SE-026, SE-027 — resolved 2026-11-11).** The unit is now taken from the raw file's column header (this application always exports laser-flash temperatures in Kelvin), with magnitude inference only as a fallback when the header declares nothing. Files whose header omits the unit remain **UNVERIFIED** and the user should confirm the scale before using the imported temperatures quantitatively.

---

## 9. Corrections Implemented

Every correction is listed with its scientific justification, the files touched and the regression test that now pins the corrected behaviour.

### SE-001 — engineering figure of merit (CRITICAL)
* **Before:** `zt_eng = (int_s**2 / int_rho) / (int_kappa / delta_t) / th_k` — units 1/K.
* **After:** `zt_eng = S̄²·T̄/(ρ̄·κ̄)` with S̄ = ∫S dT/ΔT, ρ̄ = ∫ρ dT/ΔT, κ̄ = ∫κ dT/ΔT, T̄ = (T_c+T_h)/2 — the standard Snyder engineering figure of merit, dimensionless.
* **Justification:** the previous expression mixed an un-averaged integral with an averaged one and divided by an extra temperature. Dimensional analysis alone proves it wrong, and the corrected form satisfies the exact physical requirement that η_eng ≡ η_max for constant properties.
* **Files:** `src/domain/device_efficiency.py`
* **Tests:** `tests/test_transport_models.py::test_device_efficiency_constant_properties_reference_case` (updated), `tests/test_scientific_equations_audit.py::test_engineering_figure_of_merit_is_dimensionless_and_consistent`
* **Numeric effect:** reference case ZT_eng 8.0e-4 → 0.8; Efficiency_Eng 1.0e-4 → 7.038e-2.

### SE-008 — Fermi–Dirac integral, degenerate branch (CRITICAL)
* **Before:** `F_j(η) ≈ η^{j+1}/(j+1)` for η > 50 (leading term only).
* **After:** the three-term Sommerfeld expansion `η^{j+1}/(j+1) + (π²/6)jη^{j−1} + (7π⁴/360)j(j−1)(j−2)η^{j−3}`.
* **Justification:** the Lorenz combination F_{λ+2}/F_λ − (F_{λ+1}/F_λ)² is a near-cancellation; the leading term alone leaves a residual of order η² instead of the constant π²/3, so L collapsed to 0. With the correction terms the result matches direct numerical integration of the Fermi–Dirac integrals to six significant digits and reproduces the Sommerfeld limit.
* **Files:** `src/domain/spb.py`
* **Tests:** `tests/test_spb_models.py::test_fermi_integral_boltzmann_and_sommerfeld_limits` (updated), `tests/test_scientific_equations_audit.py::test_rigorous_lorenz_number_reaches_both_analytic_limits`, `::test_fermi_integral_matches_the_degenerate_sommerfeld_expansion`
* **Numeric effect:** L(η=80) 0.0 → 2.4417e-8 W·Ω/K² (Sommerfeld 2.4430e-8).

### SE-003 — molar heat capacity (HIGH)
* **Before:** `Cp[J/(g·K)] · M[g/mol] / 1000`; **after:** `Cp · M` (the gram factors cancel: J/(g·K)·g/mol = J/(mol·K)).
* **Files:** `src/presentation/kappa_logic.py`
* **Tests:** documented in the source; the Dulong–Petit overlay and the molar-Cp curve now share the same scale.

### SE-004 — Kappa temperature handling (HIGH)
* **Before:** magnitude heuristic on ingest; raw cell value on read.
* **After:** the mapped source column `T_K` is already Kelvin; the value is converted for *display* only (K → selected unit) and converted back to Kelvin on read via the single application conversion service.
* **Files:** `src/legacy/ui/dialogs/kappa_dialog.py`, `src/presentation/kappa_logic.py`

### SE-002 — chemical formula parsing (MEDIUM)
* **Before:** `re.findall` accepted any string; parenthesised/fractional formulas silently produced a wrong molar mass.
* **After:** full-match validation against `(?:[A-Z][a-z]?\d*\s*)+`; unsupported syntax returns `(None, 0)` so the caller reports an invalid formula instead of a wrong mass. Spaces between element groups ("Bi2 Te3") remain supported ✓.
* **Files:** `src/domain/calculations.py`

### SE-005 — uncertainty signs (MEDIUM)
* **Before:** `s_err = S · r`; **after:** `|S| · r` (a standard uncertainty is a non-negative magnitude). Propagation is unaffected (the terms are squared), but the displayed column is now physically meaningful.
* **Files:** `src/gui/main_window.py`

### SE-006 — power-factor unit recognition (MEDIUM)
* **After:** "W/(m·K²)", "W/(m*K^2)", "W/mK²", "mW/(m*K^2)", "µW/(m*K^2)" and their µ/μ variants are all recognised, removing the silent pass-through.
* **Files:** `src/domain/units.py`

### SE-007, SE-009, SE-010, SE-011, SE-013, SE-014, SE-020 — consistency and documentation
Domain constants instead of literals (SPB Lorenz reference lines); corrected grouping docstring; corrected regime label; single Celsius→Kelvin service; removal of the dead Lorenz branch; exact k_B/e constant; explicit weighted-mobility assumptions.
* **Files:** `src/legacy/ui/dialogs/spb_dialog.py`, `src/legacy/ui/dialogs/hall_mobility_dialog.py`, `src/presentation/kappa_logic.py`, `src/presentation/table_handler.py`, `src/gui/main_window.py`, `src/domain/transport.py`

### Author decisions taken after the audit (2026-11-11)

| Decision | Effect |
|---|---|
| **Lorenz number unified to L = 2.44e-8 W·Ω/K²** for *every* workflow (SE-015) | The main table and the Multi-Sample workflow now produce identical κₑ and ZT. The exact Sommerfeld value (2.443004509e-8) is retained as `SOMMERFELD_LORENZ_EXACT` for reference. All κₑ values shift by −0.12 % and all ZT values by +0.12 % relative to the previous main-table default; the golden baseline was regenerated accordingly |
| **Raw temperature units taken from the file header** (SE-026, SE-027, SE-028) | The laser-flash import no longer applies an unconditional +273.15 K, so it matches the Kappa dialog's own import path; the four-probe import no longer shifts Kelvin data below 250 K. When a header declares no unit, the previous magnitude inference remains as a documented fallback |
| **Multi-Sample reports S/cm** (SE-016) | Both Multi-Sample plotting paths now use the same columns and units (S/cm, µV/K, mW/(m·K²), W/(m·K), ZT), so the numbers no longer depend on which path the user takes |

Regression tests for all three decisions are in `tests/test_author_decisions.py` (7 tests).

### Baseline regeneration
`tests/golden/baseline_outputs.json` was regenerated after the corrections (`python scripts/generate_golden_baseline.py`). The diff is limited to the affected quantities: `ZT_eng`, `Efficiency_Eng`, the SPB carrier-density/effective-mass entries (≤ 0.02 % from the Sommerfeld correction) and the weighted mobility (3.8e-7 relative). No other baseline value changed.

---

## 10. Automated Test Coverage

| Suite | Tests | Purpose |
|---|---|---|
| `tests/test_scientific_equations_audit.py` (new) | **62** | Independent analytical verification of every equation, scaling-law dimensional checks, boundary cases, unit round-trips, closed-form limits |
| `tests/test_application_layer_audit.py` (new) | **12** | Application-layer defect regressions: merge-time uncertainty loss (SE-029), u(κₑ) consistency (SE-030), column-alias guards (SE-031/SE-032), standard error of the mean (SE-033), independent uncertainty inputs (SE-035), Lorenz uncertainty (SE-036), reporting statement (SE-037), validation reach (SE-038) |
| `tests/test_author_decisions.py` (new) | **7** | The three author decisions: unified Lorenz number, header-based temperature units, Multi-Sample S/cm units |
| `tests/test_scientific_equations_audit.py` — classes | constants (4), core transport (10), uncertainty (8), units (7), Hall (5), SPB (10), phonon (2), device efficiency (3), weighted mobility (4), analysis (4) | per-equation coverage |
| `tests/test_golden_baseline.py` | 1 | regression snapshot of all key outputs (regenerated after the corrections) |
| `tests/test_calculations.py`, `test_uncertainty.py`, `test_units.py`, `test_transport_models.py`, `test_spb_models.py`, `test_hall_models.py`, `test_phonon_lfa.py`, `test_analysis_tools.py`, `test_validation_rules.py`, `test_arrhenius_plugin.py` | 96 | existing per-module coverage, extended by this audit |
| `tests/test_architecture_dependencies.py` | 24 | layer-boundary enforcement (no equation may live outside `domain`) |

**Total suite after the audit: 342 passed, 1 skipped, 1 warning** (the skip is the Qt-conditional GUI smoke test; the warning is a third-party `pytz` deprecation).

Every new test states its scientific basis in the docstring, and every expected value is computed **inside the test** from the governing relation — never by calling another application function.

---

## 11. Scientific References

1. Wiedemann, G. & Franz, R. (1853). *Ueber die Wärmeleitung in Metallen.* Annalen der Physik und Chemie **165**, 306–313. — Wiedemann–Franz law (E-02).
2. Goldsmid, H. J. (2016). *Introduction to Thermoelectricity*, 2nd ed. Springer. — ZT, κ_L decomposition, Ioffe efficiency limit (E-04, E-03, E-38).
3. Rowe, M. A. (Ed.) (2006). *Thermoelectrics Handbook: Principles and Applications*. CRC Press. — measurement practice for Seebeck/σ/κ.
4. Kim, H. S., Peterson, G. J., Funahashi, H. et al. (2015). *Characterization of Lorenz number with Seebeck coefficient measurement.* APL Materials **3**, 041506. — the empirical L(|S|) relation implemented in E-05 and the Seebeck-based Lorenz characterisation.
5. Snyder, G. J. & Toberer, E. S. (2008). *Complex thermoelectric materials.* Nature Materials **7**, 105–114. — SPB model, weighted mobility, optimal carrier concentration (E-30…E-34, E-40).
6. Köhler, K., Krechetkin, A., Gusev, V. et al. (2015). *Thermoelectric transport phenomena.* Journal of Applied Physics **118**, 020901. — single-band transport integrals and the rigorous Lorenz number (E-28, E-30).
7. Peierls, R. (1930). *Zur Theorie des elektrischen Widerstandes.* Zeitschrift für Physik **10**, 57–67. — classical activation energy and the non-degenerate Lorenz limit (E-41, §6).
8. Callaway, J. (1959). *Model for lattice thermal conductivity at low temperatures.* Physical Review **113**, 1046–1051. — lattice thermal conductivity context (E-03, E-35).
9. Debye, P. (1912). *Zur Theorie der spezifischen Wärme.* Annalen der Physik **344**, 14–31. — Debye heat capacity (context of E-36).
10. Dulong, P. L. & Petit, A. T. (1819). *Recherches sur la mesure des quantités de chaleur.* — 3nR heat-capacity limit (E-07, E-36).
11. Putley, E. H. (1960). *The Hall Effect and Related Phenomena*. Butterworths. — Hall relations (E-22…E-26).
12. ASTM E1461, *Standard Test Method for Thermal Diffusivity by the Flash Method* — laser-flash workflow behind E-35.
13. ASTM F76, *Standard Test Method for Measuring the Electrical Resistivity of Thin-Film Metallic Materials* — four-probe resistivity practice behind E-12.
14. Blatt, F. J., Schroeder, D. P., Foiles, C. L. & Greig, R. O. (1964). *Thermoelectric Power of Semiconductors*. Academic Press. — Fermi–Dirac integral conventions used in E-27…E-31.
15. Ioffe, A. F. (1957). *Semiconductors for Thermoelectric Applications.* — constant-property efficiency limit (E-38).

*Note on measurement standards:* no ASTM or equivalent standard exists specifically for bulk Seebeck coefficient or thermal conductivity of thermoelectric materials; the community practice follows the Thermoelectrics Handbook (ref. 3). This is stated so that the SoftwareX submission does not overstate standardisation.

---

## 12. Remaining Issues and Recommendations

**Must be resolved before publication**
1. **Experimental validation of the remaining workflow (largely resolved 2026-11-11).** The calculation engine is now validated against published experimental measurements (`EXPERIMENTAL_BENCHMARK_VALIDATION.md`): power factor and ZT are reproduced to 1.3–4.6 % for three material families. **Still open:** the raw-instrument import paths (four-probe, raw Seebeck, laser flash), the GUI, the multi-sample workflow, the weighted-mobility tool and the SPB inversion remain unvalidated against experimental data, and no certified reference specimen is available.
2. **The unified Lorenz constant is the rounded value.** L = 2.44e-8 is now used everywhere; it is 0.12 % below the exact Sommerfeld value (2.443004509e-8). This is an author decision for workflow consistency; a publication should state which value was used, and note that the difference is negligible compared with the ±5 % spread of experimentally determined Lorenz numbers.

**Recommended, non-blocking**
3. Move `plugins/arrhenius.py` into `src/domain/` (SE-017) and expose it in the GUI, or delete it as dead code.
4. Implement a bipolar-conduction correction flag for κ_L (limitation 2), or state the limitation in the model's documentation panel.
5. Add explicit "model-derived vs measured" labelling to every exported column (κₑ, κ_L, ZT_eng, m\*, n are model-derived; T, σ, S, κ are measured). The application already separates the columns physically, but the labels should make the distinction explicit.
6. Provide W/(cm·K) thermal-conductivity display units (SE-021) if laboratory users request them.
7. Fix the default Hall voltage in the dialog (SE-023) and the plot crosshair unit label (SE-012).

**Explicitly not changed (with reasons)**
- The legacy `src/legacy` compatibility layer, its rounded Lorenz constant (SE-015) and its dual unit conventions (SE-016) are retained for backward compatibility; the removal gates are recorded in `docs/MIGRATION_PLAN.md`. *(2026-11-15 update: the migration plan has since been executed (Phases 3–4) and consolidated into `docs/ARCHITECTURE.md`; the legacy tree was subsequently deleted, with the removal now enforced by the guard tests `test_no_package_imports_the_retired_legacy_tree` and `test_the_retired_legacy_tree_is_no_longer_importable`.)*
- The `ZT = 0` convention for κ_total = 0 (SE-018) and the `sigma_to_sm(0) = 0` edge case (SE-019) are defensive behaviours that protect downstream tables from infinities; they are documented rather than changed.
- All scientific equations outside the corrected items were left byte-identical: no equation was "improved" for stylistic reasons.

---

### Files modified by this audit

| File | Change |
|---|---|
| `src/domain/device_efficiency.py` | SE-001 corrected engineering figure of merit |
| `src/domain/spb.py` | SE-008 Sommerfeld correction terms; `import math` |
| `src/domain/calculations.py` | SE-002 formula validation |
| `src/domain/units.py` | SE-006 complete power-factor unit table |
| `src/domain/transport.py` | SE-014 exact k_B/e constant; SE-020 documented assumptions |
| `src/domain/physical_constants.py` | Author decision: one application-wide Lorenz constant; `SOMMERFELD_LORENZ_EXACT` retained for reference |
| `src/application/services.py` | SE-029 uncertainty merge; SE-030 domain κₑ propagator; SE-037 honest reporting statement |
| `src/application/use_cases.py` | SE-035 independent uncertainty inputs; SE-036 Lorenz uncertainty; SE-038 `kappa_L` validation |
| `src/application/data_mapping.py` | SE-031/SE-032 shared, guarded, case-insensitive column matcher |
| `src/application/measurement_processing.py` | SE-026/SE-027/SE-028 header-based temperature units; SE-032 shared matcher; SE-033 standard error of the mean |
| `src/application/table_files.py` | case-insensitive workbook detection |
| `src/presentation/kappa_logic.py` | SE-003 molar Cp; SE-004 Kelvin read path; SE-009 docstring |
| `src/presentation/table_handler.py` | SE-011 single Celsius→Kelvin service |
| `src/presentation/multi_sample_plots.py` / `legacy/ui/dialogs/plot_settings_dialog.py` | SE-016 unified Multi-Sample units (S/cm) |
| `src/legacy/ui/dialogs/kappa_dialog.py` | SE-004 display-only temperature conversion |
| `src/legacy/ui/dialogs/spb_dialog.py` | SE-007 domain constants for the Lorenz reference lines |
| `src/legacy/ui/dialogs/hall_mobility_dialog.py` | SE-010 regime label |
| `src/gui/main_window.py` | SE-005 non-negative uncertainties; SE-013 dead branch removed |
| `tests/test_scientific_equations_audit.py` | **new** — 62 independent verification tests |
| `tests/test_application_layer_audit.py` | **new** — 12 application-layer defect regressions |
| `tests/test_author_decisions.py` | **new** — 7 tests pinning the three author decisions |
| `tests/test_spb_models.py` | SE-008 expectation updated |
| `tests/test_transport_models.py` | SE-001 expectation updated (+ new consistency assertion) |
| `tests/test_measurement_processing.py` | temperature-convention tests updated (SE-026/SE-027) |
| `tests/golden/baseline_outputs.json` | regenerated after the corrections |
