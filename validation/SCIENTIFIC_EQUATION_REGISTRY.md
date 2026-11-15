# Scientific Equation Registry — Seebeck Prime

**Audit date:** 2026-11-12
**Scope:** every scientific calculation, numerical method, unit conversion and
calculation workflow implemented in the repository (read-only Phase I inventory,
extended by a second pass over the application, presentation, GUI and legacy
layers).

**How to read the columns**

| Column | Meaning |
|---|---|
| Equation | The mathematical relation as implemented |
| Source | File and function |
| I/O units | Input units → output units (SI base unless stated) |
| Conversions | Unit conversions the caller must apply |
| Assumptions | Physical assumptions carried by the relation |
| Validity | Where the relation applies |
| Numerics | Numerical method used |
| Tests | Existing test coverage, and what is still missing |

Status vocabulary: **VERIFIED** (independently re-derived and numerically
confirmed) · **PARTIALLY VERIFIED** · **NOT IMPLEMENTED** (the calculation does
not exist) · **UNVERIFIED** (insufficient evidence).

---

## 1. Core transport — `src/domain/calculations.py`

### E-01 · Power factor
- **Equation:** PF = S²·σ
- **Source:** `domain/calculations.py::calculate_pf`
- **I/O units:** S [V/K], σ [S/m] → PF [W/(m·K²)]
- **Conversions:** the caller must convert display units (µV/K, S/cm) to SI
- **Assumptions:** isotropic transport; PF is a material property at a given T
- **Validity:** any T; sign-independent (S²)
- **Numerics:** direct arithmetic, array-broadcasting
- **Tests:** `tests/scientific/test_independent_references.py::test_power_factor_matches_the_independent_reference` (VERIFIED, ≤1e-12); golden baseline; experimental comparison vs published PF for 4 materials (1.3–3.8 %)

### E-02 · Electronic thermal conductivity
- **Equation:** κₑ = L·σ·T
- **Source:** `domain/calculations.py::calculate_kappa_e`
- **I/O units:** σ [S/m], T [K], L [W·Ω/K²] → κₑ [W/(m·K)]
- **Conversions:** T must be Kelvin; σ must be S/m
- **Assumptions:** Wiedemann–Franz law — elastic scattering, single band, constant L
- **Validity:** fails when L varies strongly (degenerate semiconductors,
  ionised-impurity scattering, multi-band); see E-05/E-06
- **Numerics:** direct arithmetic
- **Tests:** independent reference (VERIFIED); scaling laws; L-mode comparison (VERIFIED)

### E-03 · Lattice thermal conductivity
- **Equation:** κ_L = κ_total − κₑ
- **Source:** `domain/calculations.py::calculate_kappa_l`
- **I/O units:** κ [W/(m·K)] → κ_L [W/(m·K)]
- **Assumptions:** total κ is the sum of electronic and lattice contributions
- **Validity:** breaks above the bipolar onset (minority-carrier contribution
  inflates κ_total) and whenever L is mis-estimated; a negative result
  indicates an inconsistent input combination
- **Tests:** independent reference (VERIFIED); the negative-result
  validator is verified (`domain/validation.py` +
  `application/use_cases.py`) **but is not surfaced to the user** — no
  production path calls it (audit finding D-01, see
  `validation/SCIENTIFIC_CALCULATION_TEST_RESULTS.md` §3.3). The
  **flagging** is therefore NOT verified; the **validator** is.

### E-04 · Figure of merit
- **Equation:** ZT = PF·T/κ_total = S²σT/κ_total
- **Source:** `domain/calculations.py::calculate_zt`
- **I/O units:** PF [W/(m·K²)], T [K], κ [W/(m·K)] → ZT [dimensionless]
- **Assumptions:** single-band; properties measured at the same T
- **Validity:** requires coincident T; a ZT assembled from mismatched
  temperatures is meaningless (the application never does this)
- **Numerics:** guarded division (ZT = 0 where κ = 0)
- **Tests:** independent reference (VERIFIED); consistency PF/κ/T (VERIFIED);
  experimental comparison vs published ZT for 4 materials (1.3–5.9 %)

### E-05 · Empirical (Kim) Lorenz number
- **Equation:** L(S) = (1.5 + exp(−|S|/116))·10⁻⁸ [W·Ω/K²], S in µV/K
- **Source:** `domain/calculations.py::estimate_lorenz`
- **Assumptions:** single parabolic band, **acoustic-phonon scattering**
  (r = −1/2); empirical fit in |S|
- **Validity:** measured against the rigorous SPB value it tracks the
  acoustic-phonon model to ≈±4 % (|S| = 20–300 µV/K) but departs by
  −22 % (optical/alloy) and −32 % (ionised impurity) — **not universal**.
  Quantified against published data: for a P-doped SiGe alloy the
  acoustic default underestimates the published Lorenz number by
  **35 %**, because that alloy's effective scattering exponent is
  λ ≈ 1.41, not 0 (see
  `validation/remediation/SIGE_LORENZ_INVESTIGATION.md`)
- **Tests:** independent reference (VERIFIED); deviation from the rigorous SPB
  value quantified per scattering parameter (VERIFIED)

### E-06 · Rigorous SPB Lorenz number
- **Equation:** L(η) = (k_B/e)²[ ((λ+3)(λ+2) F̂_{λ+2}/F̂_λ) − ((λ+2)F̂_{λ+1}/F̂_λ)² ]
  (equivalently written with the unnormalised complete integrals, which is how
  the application evaluates it)
- **Source:** `domain/spb.py::rigorous_lorenz_number`
- **Assumptions:** single parabolic band; scattering exponent λ (r = λ − ½)
- **Validity:** model-dependent; requires the η from the measured Seebeck
  coefficient under the *same* scattering assumption. The λ = 0
  acoustic default is **not** appropriate for alloys whose transport is
  dominated by alloy or ionised-impurity scattering: for P-doped
  Si80Ge20P1 the published data require λ ≈ 1.41, and the acoustic
  value is 35 % low. The model implementation is correct; the
  *assumption* is what fails. See
  `validation/remediation/SIGE_LORENZ_INVESTIGATION.md`.
- **Numerics:** Fermi–Dirac integrals by adaptive quadrature with
  Boltzmann / Sommerfeld asymptotic branches; see SE-039 in the audit
- **Tests:** independent Blatt-normalised quadrature (VERIFIED for λ = 0, 1, 2);
  analytic limits L₀ and (5/2+r)(k_B/e)² (VERIFIED); positive over the whole
  η range (VERIFIED)

### E-07 · Chemical formula mass and Dulong–Petit limit
- **Equations:** M = Σ nᵢAᵢ [g/mol]; C_V = 3nR [J/(mol·K)]; C = C_V/M [J/(kg·K)]
- **Source:** `domain/calculations.py::calculate_molecular_weight`,
  `calculate_dulong_petit_limit`, `domain/phonon.py::dulong_petit_*`
- **Assumptions:** classical Dulong–Petit limit (valid at high T)
- **Tests:** independent reference (VERIFIED); formula parser rejects
  unsupported syntax (VERIFIED — issue SE-002)

---

## 2. Uncertainty propagation — `src/domain/uncertainty.py`

| ID | Relation | Source | Notes | Status |
|---|---|---|---|---|
| E-08 | u_PF = √((2Sσu_S)² + (S²u_σ)²) | `propagate_pf_error` | independent inputs | VERIFIED (≤1e-12) + Monte-Carlo (≤5e-3) |
| E-09 | u_κₑ = √((LTu_σ)² + (Lσu_T)² + (σTu_L)²) | `propagate_kappa_e_error` | includes the L term | VERIFIED + MC |
| E-10 | u_κL = √(u_κ² + u_κₑ²) | `propagate_kappa_l_error` | | VERIFIED |
| E-11 | u_ZT = \|ZT\|√((u_PF/PF)² + (u_T/T)² + (u_κ/κ)²) | `propagate_zt_error` | | VERIFIED |
| E-12 | u_σ/σ = √((u_L/L)²+(u_R/R)²+(u_A/A)²) | `propagate_sigma_error` | **not called by the application**; the live geometry-uncertainty path is `combine_sigma_uncertainty` (E-48) | VERIFIED (reference only; presupposes σ = L/(R·A) for a rectangular specimen) |
| E-13 | u_κ/κ = √((u_α/α)²+(u_Cp/Cp)²+(u_ρ/ρ)²) | `propagate_kappa_error` | | VERIFIED + MC |
| E-14 | u_ρ/ρ = √((u_m/m)²+(u_A/A)²+(u_t/t)²) | `propagate_density_error` | | VERIFIED |
| E-15 | u = \|v\|√(Σrel²) | `propagate_relative_uncertainty` | | VERIFIED |

**Documented assumption:** all propagations assume **independent**
contributions; no covariance is modelled anywhere (stated in §7 of the
limitations report).

---

## 3. Units — `src/domain/units.py`, `src/application/unit_conversion.py`

| ID | Relation | Status |
|---|---|---|
| E-16 | T[K] = T[°C] + 273.15; uncertainty invariant | VERIFIED |
| E-17 | σ[S/m] = 100·σ[S/cm]; σ[S/m] = 100/ρ[Ω·cm] | VERIFIED |
| E-18 | S[V/K] = S[µV/K]·10⁻⁶; = S[mV/K]·10⁻³ | VERIFIED |
| E-19 | PF[W/(m·K²)] = PF[mW/(m·K²)]·10⁻³ = PF[µW/(m·K²)]·10⁻⁶ | VERIFIED (all spellings) |
| E-20 | n[cm⁻³] = n[m⁻³]·10⁻⁶ | VERIFIED |
| E-21 | Uncertainty conversions (linear for S/PF; 100/ρ² for Ω·cm) | VERIFIED |
| E-22 | κ: only W/(m·K) supported | PARTIALLY VERIFIED (the unit is not supported; the converter now **rejects** it rather than silently mis-scaling — SE-042) |

---

## 4. SPB model — `src/domain/spb.py`

| ID | Relation | Source | Notes | Status |
|---|---|---|---|---|
| E-23 | F_j(η) = ∫₀^∞ x^j/(1+e^{x−η})dx (unnormalised) | `fermi_integral` | asymptotic branches for η<−30 and η>50; quadrature otherwise | VERIFIED (independent quadrature, ≤1e-8) |
| E-24 | S(η) = (k_B/e)[(λ+2)F_{λ+1}/((λ+1)F_λ) − η] (unnormalised convention) | `seebeck_from_reduced_fermi_level` | λ = r + ½ | VERIFIED (classical + degenerate limits, all λ) |
| E-25 | η from S (Brent) | `reduced_fermi_level_from_seebeck` | metallic limit | VERIFIED; unbracketed → NaN (VERIFIED) |
| E-26 | n = N_c m*^{3/2} F_{1/2}(η) | `calculate_carrier_density_spb` | N_c carries 1/Γ(3/2) | VERIFIED (textbook n to 1e-15) |
| E-27 | m* = [n/(N_c F_{1/2})]^{2/3} | `calculate_effective_mass` | | VERIFIED vs independent reference (≤1e-6) |
| E-28 | Pisarenko curve, optimal n/PF | `generate_pisarenko_curve`, `predict_optimal_transport` | | VERIFIED (structure, monotonicity) |
| E-29 | n_empirical = 10²¹·exp(−\|S\|/43.4) | `calculate_carrier_concentration` | | empirical fit (documented) |

---

## 5. Hall — `src/domain/hall.py`

| ID | Relation | Status |
|---|---|---|
| E-30 | R_H = V_H·t/(I·B) | VERIFIED |
| E-31 | n_H = r_H/(e·\|R_H\|) | VERIFIED |
| E-32 | carrier type from sign(R_H) | VERIFIED |
| E-33 | μ_H = \|R_H\|·σ [m²/(V·s)] and the cm²/(V·s) variant | VERIFIED (incl. the 10⁴ relation) |
| E-34 | μ ∝ T^p fit (scattering exponent) | VERIFIED |

---

## 6. Phonon / laser flash — `src/domain/phonon.py`

| ID | Relation | Status |
|---|---|---|
| E-35 | κ = α·C_p·ρ [W/(m·K)] (SI and laboratory-unit forms) | VERIFIED (the two paths agree to 1e-12) |

---

## 7. Device efficiency — `src/domain/device_efficiency.py`

| ID | Relation | Status |
|---|---|---|
| E-36 | ZT̄ = (1/ΔT)∫ZT dT | VERIFIED (Simpson, independent reference) |
| E-37 | η_max = (ΔT/Th)(√(1+ZT̄)−1)/(√(1+ZT̄)+Tc/Th) | VERIFIED |
| E-38 | ZT_eng = S̄²·T̄/(ρ̄·κ̄) | VERIFIED **after the SE-001 correction** (was dimensionally invalid) |

---

## 8. Transport / analysis / validation — `src/domain/transport.py`, `analysis.py`, `validation.py`

| ID | Relation | Status |
|---|---|---|
| E-39 | Snyder et al. (2020): μ_w = 331·(mΩ·cm/ρ)·(T/300 K)^{−3/2}·[exp(s−2)/(1+exp(−5(s−1))) + (3/π²)s/(1+exp(5(s−1)))], s=|S|/(k_B/e) | VERIFIED against independent published-equation transcription; **not experimentally validated** |
| E-40 | ρ conversions to mΩ·cm | VERIFIED |
| E-41 | MAD filter, OLS regression, linear interpolation, temperature rounding/alignment | VERIFIED |
| E-42 | Physical-constraint validators (T, σ, S, κ, κ_L) | VERIFIED (messages, severities) — **reachability is NOT verified**: no production path calls `validate_measurement_data`/`validate_dataset` (audit D-01) |

---

## 9. Data-processing workflows

| ID | Workflow | Source | Status |
|---|---|---|---|
| E-43 | Property suite from measured inputs (with uncertainties) | `application/use_cases.py::calculate_thermoelectric_properties` | VERIFIED |
| E-44 | Multi-sample preparation (display columns, ordering, row dropping) | `process_multi_sample_data`, `process_multi_sample_batch` | VERIFIED (published PF/ZT, 1.3–5.9 %) |
| E-45 | Four-probe import (T association, unit conversion, grouping, SEM, invalid rows) | `application/measurement_processing.py::process_four_probe_table` | VERIFIED (parsing) |
| E-46 | Raw Seebeck import (ΔV/ΔT regression, sign, grouping) | `process_raw_seebeck_table` | VERIFIED (parsing) |
| E-47 | Laser-flash import (T, κ, α, C_p) | `process_laser_flash_table` | VERIFIED (parsing) |
| E-48 | Geometry uncertainty combination | `combine_sigma_uncertainty` | VERIFIED (independent formula) |
| E-49 | Reference Seebeck uncertainty combination | `combine_seebeck_uncertainty` | VERIFIED |
| E-50 | Column mapping (aliases + physical-plausibility guards) | `application/data_mapping.py` | VERIFIED (guards) |
| E-51 | SPB batch rows and mean parameters | `application/spb_batch.py` | VERIFIED (arithmetic); the mean-pairing rule is **documented, not changed** (legacy) |
| E-52 | Arrhenius fits (ln σ, ln σT, log10 σ) | `plugins/arrhenius.py` | VERIFIED (activation energy recovered exactly) |

---

## 10. GUI / presentation calculations

| ID | Workflow | Status |
|---|---|---|
| E-53 | Spreadsheet recalculation (file → mapper → table → properties) | VERIFIED (headless integration) |
| E-54 | Display-unit rendering vs internal SI values | VERIFIED |
| E-55 | Plot data preparation (sorting, error alignment) | VERIFIED |
| E-56 | Interactive dialogs (error bars, Kappa, SPB, Hall, weighted mobility, multi-sample) | **UNVERIFIED** — no automated coverage. **Corrected reason:** five of the six are opened with `.show()` (non-modal) and are already `QTest`-driveable; only `ErrorBarDialog` (`gui/main_window.py:292`) and `PlotDataDialog` (`:779`) use modal `exec()` |
| E-57 | Clipboard paste, menus, plot export | **UNVERIFIED** — interactive |
| E-58 | Raw V/I → R → ρ → σ chain | **NOT IMPLEMENTED** — confirmed absent in the Phase 1 audit (finding M-01): the instrument file is assumed to contain σ, and geometry is used only for the σ *uncertainty* |

---

## 11. Retired legacy / compatibility surfaces (deleted 2026-11-13)

| ID | Module | Status |
|---|---|---|
| E-59 | `legacy/core/calculations.py` (5 wrappers) — **retired**; the numerical assertions run unchanged against `domain/calculations.py` via `tests/test_canonical_calculations_surface.py` | VERIFIED (pure delegation, historical) |
| E-60 | `legacy/core/constants.py` (aliases; legacy Lorenz 2.44e-8) — **retired**; the application-wide constants remain in `domain/physical_constants.py` | VERIFIED (historical) |
| E-61 | `legacy/core/analyzer.py` (multi-sample orchestration) — **retired**; the orchestration lives on in `application/use_cases.py` and `presentation/multi_sample_plots.py` | VERIFIED (historical) |
| E-62 | `legacy/ui/logic/*` (4 alias modules) — **retired**; the canonical modules are `presentation/{kappa_logic,table_handler,ui_builder,unit_converter}.py` | VERIFIED (pure delegation, historical) |

---

## 12. Register summary

62 entries, E-01 … E-62, with no gaps.

**The per-equation validation status is maintained in the remediation
package**, which is the canonical, machine-checked source:

| Artefact | Content |
|---|---|
| [`remediation/EQUATION_STATUS_MAPPING.csv`](remediation/EQUATION_STATUS_MAPPING.csv) | One row per equation: implementation file and function, test files, independent reference, **numerical** / **physical** / **experimental** status, validation category and remaining limitation |
| [`remediation/VALIDATION_STATUS.md`](remediation/VALIDATION_STATUS.md) | The four evidence categories, the scope of every experimental claim, the reproduced test accounting, and the explanation of the 62-vs-49 difference |
| `tests/scientific/test_equation_status_mapping.py` | The guard: the registry, the mapping and the status document are verified against each other on every run |

**Status summary (62 equations):**

| Status | Count |
|---|---|
| 1 — Numerically verified | 31 |
| 2 — Numerically verified but physically conditional | 23 |
| 3 — Experimentally benchmarked within a defined scope | 5 |
| 4 — Not yet validated | 3 |

**Two sub-items of otherwise-verified entries are explicitly not verified:**

- **E-27 (SPB effective mass)** — the inversion is verified; the *physical
  value* is not, because no publication states an effective mass that can be
  cross-checked.
- **E-39 (weighted mobility)** — the formula is verified; the *physics* is
  not, because the only published carrier-mobility curve in the benchmark
  set is negative and therefore unusable.

**One confirmed defect was found and fixed during the validation programme**
(SE-042, `domain/units.py`): the thermal-conductivity converter ignored its
unit argument. See `SCIENTIFIC_CALCULATION_TEST_RESULTS.md` §3.2.

**One open high-severity defect was found by the Phase 1 remediation audit**
(D-01): the negative-lattice-conductivity diagnostic has no production
caller, so it never reaches the user. See
`SCIENTIFIC_CALCULATION_TEST_RESULTS.md` §3.3 and the audit's Phase 3 plan.
