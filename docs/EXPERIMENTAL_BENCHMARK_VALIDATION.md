# Experimental Benchmark Validation — Seebeck Prime

**Date:** 2026-11-11
**Purpose:** independent experimental validation of the Seebeck Prime calculation engine against published measurements.
**Structure:** Part I validates the calculation engine; **Part II** (the extended validation phase: auto-Lorenz mode, instrument importers, multi-sample workflow, weighted mobility, SPB inversion, desktop workflow) is reported separately in `EXTENDED_VALIDATION_REPORT.md`.
**Canonical dataset list:** `tests/experimental_benchmarks/registry.py` — the single source of truth; a test verifies that the registry, the on-disk datasets and both reports agree.

> **Scope limit, stated up front:** this validates the *calculation engine* and the
> file-based workflow against real, published measurements. The **interactive**
> dialogs (error bars, Kappa, SPB, Hall) require a user and are therefore
> **UNVERIFIED**; see `EXTENDED_VALIDATION_REPORT.md` §8 for the exact coverage.

---

## 1. Selected materials and publications

Four published datasets were selected — one per requested material family, plus
a fourth (Si₈₀Ge₂₀P₁) that publishes electronic/lattice thermal conductivity
and carrier data, which is what makes the κₑ, lattice-κ, weighted-mobility and
SPB comparisons possible at all.

| Benchmark id | Family | Composition | Publication | DOI |
|---|---|---|---|---|
| `b2te3_bi2te2_4se0_6cu0_006` | Bi2Te3-based | Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | *Effect of Cu electroless plating on thermoelectric properties of n-type Bi₂Te₂.₄Se₀.₆ alloy*, J. Mater. Sci.: Mater. Electron. (2019) | [10.1007/s10854-019-01874-0](https://doi.org/10.1007/s10854-019-01874-0) |
| `pbte_pbte0_95pbs0_05` | PbTe-based | (PbTe)₀.₉₅(PbS)₀.₀₅ | *Thermoelectric performance in pseudo-ternary (PbTe)₀.₉₅₋ₓ(Sb₂Se₃)ₓ(PbS)₀.₀₅ system with ultra-low thermal conductivity*, Current Applied Physics (2020) | [10.1016/j.cap.2020.06.028](https://doi.org/10.1016/j.cap.2020.06.028) |
| `sige_si80ge18sb2` | SiGe-based | Si₈₀Ge₁₈Sb₂ | *Thermoelectric performance of Si₈₀Ge₂₀₋ₓSbₓ based multiphase alloys with inhomogeneous dopant distribution*, Energy Conversion and Management (2015) | [10.1016/j.enconman.2015.01.082](https://doi.org/10.1016/j.enconman.2015.01.082) |
| `sige_si80ge20p1` | SiGe-based | Si₈₀Ge₂₀P₁ (single-phase reference of an SrTiO₃/SiGe composite study) | *Enhanced Thermoelectric Performance in n-Type SrTiO₃/SiGe Composite*, ACS Appl. Mater. Interfaces 12, 2687 (2020) | [10.1021/acsami.9b20090](https://doi.org/10.1021/acsami.9b20090) |

**Selection was evidence-based, not opportunistic.** From 501 candidate samples
that publish temperature-dependent Seebeck coefficient, electrical
conductivity, thermal conductivity, power factor **and** ZT, only **238**
passed an internal-consistency screen of the published data (§4.3): 207
Bi₂Te₃-based, 25 PbTe-based and 6 SiGe-based. The benchmarks used here are
drawn from those 238.

---

## 2. Dataset provenance

| Item | Value |
|---|---|
| Data source | StarryData (NIMS), project `ThermoelectricMaterials` |
| Database snapshot | `2026-11-11 02:00:02 UTC+0900 (JST)` |
| Manifest | <https://starrydata.github.io/starrydata_datasets/manifest.json> |
| Download base | `https://github.com/starrydata/starrydata_datasets/releases/latest/download` |
| Source files | `ThermoelectricMaterials_{papers,samples,curves}.csv.gz` |
| Checksums | SHA-256 of all three files verified by `extract_benchmarks.py` against the published manifest (values in `references/starrydata_snapshot.md`) |
| Raw extract | `raw/<benchmark>_curves.csv` — **verbatim** rows of the source table, including the JSON-encoded x/y lists and all metadata columns |
| Provenance cards | `references/<benchmark>.md` — composition, title, DOI, journal, year, snapshot, units, extraction method, licence |
| Licence | Digitised data: **CC BY 4.0**. The measurements belong to the original publications (© their authors). |

The join key is `(SID, sample_id)` — the database's own changelog warns that
`sample_id` alone is not unique across papers in some releases.

**Raw data are preserved unmodified.** `raw/` contains the source rows exactly
as published; all transformation happens in `processed/`, which is regenerated
by the extraction scripts (verified **byte-identical** on regeneration).

---

## 3. Experimental conditions

| Benchmark | Temperature range | Published properties available | Notes |
|---|---|---|---|
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | 305–477 K (9 points per grid) | S, σ, κ, PF, ZT, κ_L, n, μ | n-type; electrical transport and laser flash on the same specimen |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | 299–862 K (12 points per grid) | S, σ, κ, PF, ZT, κ_L | degenerate n-type; three separate source figures |
| Si₈₀Ge₁₈Sb₂ | 321–1070 K (9 points per grid) | S, σ, κ, PF, ZT | Sb-doped SiGe multiphase alloy; high-temperature range |
| Si₈₀Ge₂₀P₁ | 302–1007 K (9–20 points per grid) | S, σ, κ, PF, ZT, κₑ, κ_L, n, μ | single-phase P-doped SiGe reference; published ZT reaches 0.87 (the composite of the same paper reaches 0.91) |

Measurement-condition metadata recorded by the database (measurement
technique, data type, form, …) is preserved verbatim in the per-benchmark
provenance cards; StarryData classifies the selected datasets as
**experimental** (calculated datasets are excluded from the release).

All properties are published in **SI units** (S·K⁻¹, S·m⁻¹, W·m⁻¹·K⁻¹,
W·m⁻¹·K⁻²); the unit strings are validated by the test suite rather than
assumed. One trap was found and handled explicitly: the **carrier
concentration is published in m⁻³** (unit string `m^(-3)`), not cm⁻³.

---

## 4. Data preprocessing

### 4.1 Pipeline
1. Download the three source files; verify SHA-256 against the published
   manifest.
2. Copy the selected samples' curve rows **verbatim** into `raw/`.
3. Decode the JSON `x`/`y` lists into numeric columns.
4. Build one **temperature-matched grid** per published quantity. The grid is
   the temperature grid of the published curve; the measured S, σ and κ curves
   are linearly interpolated onto it with `numpy.interp`.
5. Compute the expected results with an **independent** implementation
   (`extract_benchmarks.py`, which does not import Seebeck-Prime).

### 4.2 Interpolation policy
Only the **inputs** are interpolated (S, σ, κ onto the published grid). The
**published value is never re-sampled**, and the **computed result is never
interpolated**: every comparison is made at exactly the temperatures of the
published curve.

### 4.3 Internal-consistency screen of the source data
Before any benchmark was accepted, the published data of each candidate were
checked against each other:

* the published power factor must agree with S²σ computed from the published S
  and σ (≤5 % over the grid);
* the published ZT must agree with PF·T/κ computed from the published PF and
  published κ (≤5 % over the grid).

**263 of 501 candidates failed this screen** and were excluded; in several
cases the published ZT curve contradicted the paper's own S, σ and κ by a
factor of ~100 (e.g. DOI 10.1002/aenm.201500411 and DOI 10.1063/1.4796148),
which indicates curves assigned to the wrong specimen in the source database
rather than anything about Seebeck Prime. Excluding them keeps a benchmark
failure interpretable.

---

## 5. Independent reference calculations

The expected values were produced by an implementation that is deliberately
**independent of Seebeck Prime** (it lives in `extract_benchmarks.py` and
imports only numpy/pandas):

| Quantity | Expression | Units |
|---|---|---|
| Electrical conductivity | σ (measured, taken as published) | S·m⁻¹ |
| Power factor | PF = S²·σ | W·(m·K²)⁻¹ |
| Electronic thermal conductivity | κₑ = L·σ·T | W·(m·K)⁻¹ |
| Lattice thermal conductivity | κ_L = κ_total − κₑ | W·(m·K)⁻¹ |
| Figure of merit | ZT = PF·T/κ_total | dimensionless |

The Lorenz number used for the expected results is the application-wide
constant **L = 2.44e-8 W·Ω·K⁻²** (author decision of 2026-11-11). The
comparison in §6 therefore also checks that the software and the independent
implementation agree exactly, and §7 compares against the *published* values.

---

## 6. Comparison methodology

| Class | Comparison | Tolerance | Justification |
|---|---|---|---|
| **A** | Software vs. independent calculation | 1e-9 relative | Identical algebra; only floating-point round-off may differ |
| **B** | Software vs. published **power factor** | 5 % relative | Digitisation of the source figures (~1 %), linear interpolation of S, σ and κ onto the published grid (1–2 % for these curved properties), and the paper's own rounding |
| **C** | Software vs. published **ZT** | 10 % relative | ZT accumulates the power-factor and thermal-conductivity contributions |
| **D** | Software vs. published **lattice κ** | 5 % relative | Isolates the arithmetic from the authors' (unknown) Lorenz assumption — **only where the application uses its own a-priori constant** (the Si₈₀Ge₂₀P₁ dataset). Where the Lorenz number is *derived from the published κ_L*, the comparison is an **arithmetic consistency check**, not an experimental validation (see §9) |
| **E** | Quantities the paper does not publish | — | Reported as **UNVERIFIED** with the reason; never silently skipped |

Metrics reported for every comparison: absolute error, relative error, mean
absolute error (MAE), root mean square error (RMSE) and maximum relative
error.

**Tolerances are derived from the measurement chain, not fitted to the
results.** A unit error (10²–10⁶), a sign error (2×) or a wrong equation
would exceed them by orders of magnitude; a 1–5 % deviation is what
digitised, independently plotted data can legitimately produce.

---

## 7. Quantitative results

### 7.1 Power factor — software vs. published (Class B)

| Benchmark | MAE [W/(m·K²)] | RMSE [W/(m·K²)] | Max relative error | Status |
|---|---|---|---|---|
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | 1.171e-05 | 1.297e-05 | **1.26 %** | **PASS** |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | 1.846e-05 | 2.662e-05 | **3.18 %** | **PASS** |
| Si₈₀Ge₁₈Sb₂ | 2.666e-05 | 3.236e-05 | **2.37 %** | **PASS** |
| Si₈₀Ge₂₀P₁ | — | — | **3.79 %**¹ | **PASS** |

¹ measured in the extended phase through the multi-sample workflow
(`EXTENDED_VALIDATION_REPORT.md` §14.1).

### 7.2 Figure of merit — software vs. published (Class C)

| Benchmark | MAE | RMSE | Max relative error | Status |
|---|---|---|---|---|
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | 3.131e-03 | 4.272e-03 | **1.26 %** | **PASS** |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | 1.610e-02 | 2.168e-02 | **4.62 %** | **PASS** |
| Si₈₀Ge₁₈Sb₂ | 3.999e-03 | 6.006e-03 | **2.74 %** | **PASS** |
| Si₈₀Ge₂₀P₁ | — | — | **5.93 %**¹ | **PASS** |

### 7.3 Lattice thermal conductivity

| Benchmark | Comparison | MAE [W/(m·K)] | Max relative error | Implied Lorenz number | Status |
|---|---|---|---|---|---|
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | **arithmetic consistency check** (L derived from the published κ_L) | 3.411e-03 | **1.25 %** | 1.6525e-08 W·Ω·K⁻² | PASS (consistency only) |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | consistency check | — | 9.8 % | 1.276e-08 W·Ω·K⁻² (spread 25 %) | **UNVERIFIED** — noise-limited (§9) |
| Si₈₀Ge₁₈Sb₂ | — | — | — | — | **UNVERIFIED** — no published κ_L |
| Si₈₀Ge₂₀P₁ | **experimental** (application constant L = 2.44e-8) | — | **≤0.7 %** | 2.4579e-08 W·Ω·K⁻² (published) | **PASS** |

### 7.4 Software vs. independent calculation (Class A)

All datasets × all grids: **max relative error < 1e-9** (identical algebra,
floating-point round-off only).

---

## 8. Error analysis

### 8.1 Observed deviations
The 1.3–4.6 % deviations between the computed and published power factors and
figures of merit are consistent with the error budget of the comparison chain:

1. **Digitisation of the source figures** — the published curves were traced
   from printed graphs; the tracing precision is ≈1 % of the axis range.
2. **Interpolation onto the published grid** — the measured S, σ and κ curves
   are sampled at 9–20 points per curve and are curved; linear interpolation
   between them contributes ≈1–2 %.
3. **Independent digitisation of different figures** — the published power
   factor and the published ZT come from *different figures* of the same
   paper at slightly different temperatures, so the comparison is never a
   point-by-point identity.
4. **The papers' own rounding** of the tabulated/digitised values.

The Bi₂Te₃ dataset shows the smallest deviation (1.26 %); the PbTe dataset
the largest (4.62 % for ZT), consistent with its 300–860 K span (curvature
between widely spaced points) and its three separate source figures.

### 8.2 A physically important finding: the Lorenz assumption dominates κ_L
The Lorenz number implied by the published data differs from the
application-wide constant by a factor that matters:

| Benchmark | L implied by the published data | κ_L difference with L = 2.44e-8 |
|---|---|---|
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | 1.6525e-08 | up to **26.5 %** |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | 1.276e-08 | up to **130.6 %** |
| Si₈₀Ge₂₀P₁ | 2.4579e-08 | up to **0.7 %** |

Both implied values are physically expected (degenerate semiconductors have
L < L₀), but the magnitude of the effect is large — **the choice of Lorenz
number, not the arithmetic, determines the reported lattice thermal
conductivity for degenerate materials**. This is exactly why the application
offers the Seebeck-derived ("auto") Lorenz mode, and it is a first-class
limitation that must be stated in any publication using κ_L.

---

## 9. Limitations

1. **The lattice-κ comparison is circular whenever the Lorenz number is
   derived from the published κ_L.** Recomputing κ_L with that L reproduces
   the published κ_L by construction. It is retained as an **arithmetic
   consistency check** (it does test the application's subtraction on real
   values) and is excluded from the experimental claims. The genuine
   experimental comparison is the Si₈₀Ge₂₀P₁ dataset, where the application
   uses its own a-priori constant (≤0.7 %).
2. **The PbTe lattice comparison is noise-limited.** The published total and
   lattice thermal conductivities imply a Lorenz number that scatters 25 %
   (1.15–1.46e-8) between temperatures, i.e. no single constant L describes
   them; the deviation (9.8 %) is a property of the source data, not of the
   calculation, and the comparison is reported **UNVERIFIED**.
3. **No certified reference material.** The repository contains no certified
   reference specimen; the reference values are *digitised published figures*.
   The validation establishes that the software reproduces published values,
   not that it reproduces measurements of a certified standard.
4. **Digitisation and interpolation dominate the error budget** (§8.1).
5. **The auto-Lorenz mode is not experimentally validated** — the available
   published data contradict the single-parabolic-band acoustic-phonon model
   by ≈35 % for the SiGe sample. See `EXTENDED_VALIDATION_REPORT.md` §4.3.
6. **Interactive dialogs are unvalidated** (error bars, Kappa, SPB, Hall):
   they open modal windows and cannot be driven headlessly.
7. **Single-source dependence.** All datasets come from one digitisation
   pipeline (StarryData); a benchmark from a different source would
   cross-check the *source data* as well.
8. **Averaging and model conventions.** ZT_avg is a temperature-weighted
   average over the junction interval; ZT_eng uses arithmetic averages and
   T̄ = (T_c+T_h)/2. Different conventions shift ZT_eng by a few percent, and
   the convention must be stated when comparing with the literature.

---

## 10. Failed and incomplete tests

Nothing was hidden; the complete status of every comparison:

| Benchmark | Comparison | Status | Reason |
|---|---|---|---|
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | PF vs published | **PASS** | 1.26 % ≤ 5 % |
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | ZT vs published | **PASS** | 1.26 % ≤ 10 % |
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | κ_L vs published | PASS (consistency) | 1.25 % ≤ 5 % — arithmetic consistency, not experimental |
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | electronic κ, n, μ | UNVERIFIED | not published (the published μ curve is negative → unusable) |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | PF vs published | **PASS** | 3.18 % ≤ 5 % |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | ZT vs published | **PASS** | 4.62 % ≤ 10 % |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | κ_L vs published | **UNVERIFIED** | published κ and κ_L are not consistent with one Lorenz number (25 % spread) |
| Si₈₀Ge₁₈Sb₂ | PF vs published | **PASS** | 2.37 % ≤ 5 % |
| Si₈₀Ge₁₈Sb₂ | ZT vs published | **PASS** | 2.74 % ≤ 10 % |
| Si₈₀Ge₁₈Sb₂ | κ_L vs published | **UNVERIFIED** | the paper publishes no lattice thermal conductivity |
| Si₈₀Ge₂₀P₁ | PF vs published | **PASS** | 3.79 % ≤ 5 % |
| Si₈₀Ge₂₀P₁ | ZT vs published | **PASS** | 5.93 % ≤ 10 % |
| Si₈₀Ge₂₀P₁ | κ_L vs published | **PASS** | ≤0.7 % with the application's own constant |
| Si₈₀Ge₂₀P₁ | n, μ cross-check | **PASS** | μ = σ/(n·e) consistent to a median ratio of 1.08 |
| all | software vs independent calculation | **PASS** | <1e-9 relative on every grid |

**Benchmark-suite result: 119 passed, 6 skipped.** The six skips are the
documented UNVERIFIED comparisons — no usable published reference exists for
them — together with the two benchmark specimens whose published carrier data
are physically impossible (a negative carrier concentration and mobility). The
count excludes `test_gui_end_to_end.py`, whose availability depends on the
local Qt runtime: its four tests pass in a Qt-capable environment and the
module is skipped in the primary environment. No comparison was silently
dropped, and no failing comparison was hidden or re-tuned.

Excluded from the benchmark set (not failures of the software): the 263
candidate samples whose *published* data failed the internal-consistency
screen of §4.3.

---

## 11. Overall validation status

**Status: VALIDATED (for the tested scope).**

Seebeck Prime reproduces the **published** power factor and figure of merit of
three real thermoelectric materials — n-type Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ (1.26 %),
degenerate n-type (PbTe)₀.₉₅(PbS)₀.₀₅ (3.18 % / 4.62 %) and Sb-doped
Si₈₀Ge₁₈Sb₂ (2.37 % / 2.74 %) — with maximum relative deviations of
1.3–4.6 %, consistent with the digitisation and interpolation error of the
comparison chain and comfortably inside the justified tolerances. Its
arithmetic matches an independent implementation of the governing equations to
better than 1e-9 relative.

**What this does and does not establish**

* It establishes that the calculation engine, fed with published measurements
  in SI units, returns the thermoelectric figures of merit that the source
  papers report — across three material families, two carrier types and a
  300–1070 K temperature span, plus a fourth dataset in the extended phase.
* It does **not** establish experimental accuracy of the *measurements* the
  software takes from the user, nor validate the interactive dialogs, nor
  validate the material models; and the lattice-κ comparison is an arithmetic
  consistency check unless the application supplies the constant itself.
* The largest quantitative sensitivity identified is the **Lorenz number**:
  with the application-wide L = 2.44e-8 the extracted lattice thermal
  conductivity of degenerate PbTe differs from the published value by up to
  130 %. The benchmark quantifies this and the report must state it.

### Recommended next steps

1. Add a benchmark from a **second digitisation source** (e.g. published
   supplementary data tables) so that the *source data* are cross-checked too.
2. Validate the **interactive dialogs** with a scripted `QTest` harness.
3. Cross-check the **SPB effective mass** against the value stated in the
   source publication (the abstract of DOI 10.1021/acsami.9b20090 does not
   state one and the full text is not openly available).
4. Label the **auto-Lorenz** output as model-derived in the GUI, and state the
   scattering assumption in any publication that uses it.
5. Validate the **raw instrument files** end-to-end against genuine
   instrument exports, which would additionally close the
   V/I → R → ρ → σ chain.
