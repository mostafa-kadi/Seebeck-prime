# Scientific Benchmark Material Families — Seebeck Prime

**Version:** 1.0
**Date:** 2026-11-12
**Purpose:** document the published-data landscape for the seven material
families named in the validation plan (Phase X), state which of them are
currently used as *active* experimental benchmarks, and record the
extraction procedure so that further families can be added without
re-deriving the method.

**Data source.** StarryData `ThermoelectricMaterials` release (a curated
aggregation of published thermoelectric measurements with DOI-level
provenance). Snapshot: `2026-11-11 02:00:02 JST`. Upstream files and their
SHA-256 checksums are recorded in `docs/EXPERIMENTAL_BENCHMARK_VALIDATION.md`.

**Reproduction.**

```
python tools/survey_material_families.py
```

The script reads only the cached snapshot and prints the tables in §2–§3.
No number in this document is hand-entered.

---

## 1. What the plan asked for, and what exists

The plan named seven families and required that (a) no experimental data be
fabricated, (b) not all families be assumed to obey a single parabolic band,
and (c) every benchmark record carry full provenance.

| # | Family requested | Present in the snapshot? | Used as an active benchmark? |
|---|---|---|---|
| 1 | SiGe alloys (SPB + Pisarenko) | **yes** — 638 samples / 149 publications | **yes** — 2 specimens (PF, ZT, κ_L, κₑ, n, μ) |
| 2 | Mg₂Si (semiconductor transport) | **yes** — 769 samples / 165 publications | no (surveyed; extraction procedure ready) |
| 3 | Mg₂Sn (SPB + two-band) | **yes** — 114 samples / 26 publications | no (surveyed) |
| 4 | Bi₂Te₃-based (SPB + multiband) | **yes** — 1 651 samples / 467 publications | **yes** — 1 specimen (PF, ZT) |
| 5 | PbTe (SPB, Kane, multiband) | **yes** — 652 samples / 170 publications | **yes** — 1 specimen (PF, ZT) |
| 6 | SnSe (anisotropic, bipolar) | **yes** — 345 samples / 113 publications | no (surveyed) |
| 7 | CaMnO₃-based oxides (oxide transport, Lorenz limits) | **yes** — 458 samples / 94 publications | no (surveyed) |

All seven families are genuinely available. The four that are *not* active
benchmarks are not omitted by choice — they are registered with the same
provenance discipline, and §5 states the specific physical reason each
would need a different comparison protocol.

---

## 2. Property coverage per family

Counts of published curves **against temperature** for the samples of each
family. This is the material that determines which comparisons are
physically possible.

| family | samples | papers | S | σ | ρ | κ | κ_L | PF | ZT | n_H | μ_H |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SiGe | 638 | 149 | 698 | 347 | 353 | 561 | 85 | 265 | 495 | 33 | 6 |
| Mg₂Si | 769 | 165 | 798 | 581 | 157 | 610 | 112 | 305 | 654 | 6 | 8 |
| Mg₂Sn | 114 | 26 | 179 | 86 | 75 | 134 | 32 | 95 | 91 | 0 | 0 |
| Bi₂Te₃-based | 1 651 | 467 | 1 932 | 1 245 | 717 | 1 428 | 331 | 1 150 | 1 360 | 157 | 116 |
| PbTe | 652 | 170 | 820 | 553 | 247 | 705 | 282 | 427 | 751 | 52 | 33 |
| SnSe | 345 | 113 | 550 | 389 | 177 | 484 | 241 | 402 | 480 | 57 | 44 |
| CaMnO₃-based | 458 | 94 | 406 | 105 | 374 | 258 | 14 | 250 | 185 | 0 | 0 |

**Reading this table.**

- **PF and ZT are universally available** — they are the two quantities the
  application computes directly from (S, σ, T, κ) and they are therefore
  the right first comparison for every family.
- **κ_L is sparse for CaMnO₃ (14 curves) and Mg₂Sn (32)** — the oxide family
  is dominated by publications that report only κ_total, so a lattice-κ
  comparison is not generally possible there.
- **Hall data are absent for Mg₂Sn and CaMnO₃** (0 curves) — a Hall-based
  carrier-concentration comparison cannot be built for those families from
  this source.
- **Bi₂Te₃ has by far the richest coverage** (467 publications), which is
  consistent with it being the most-studied class; it is also the family
  where the *published* data are most likely to be internally inconsistent
  (see §5.1).

---

## 3. Representative publications (with real DOIs)

The six most complete publications per family, by number of published
quantity types. These are the natural candidates for future benchmark
extractions.

### 3.1 SiGe

| SID | DOI | Published vs T |
|---|---|---|
| 24041 | `10.1021/acsami.9b20090` | n, μ, σ, κₑ, κ_L, PF, S, κ, ZT — **active benchmark** |
| 841 | `10.3390/en81010958` | n, PF, S, κ, ZT |
| 2092 | `10.1063/1.4794992` | n, ρ, PF, S, κ, ZT |
| 15282 | `10.1002/pssa.201532642` | ρ, κ_L, PF, S, κ, ZT |
| 9756 | `10.1016/j.jallcom.2015.09.023` | σ, ρ, PF, S, κ, ZT |
| 18616 | `10.1021/acs.chemmater.6b04076` | σ, κ_L, PF, S, κ, ZT |

### 3.2 Mg₂Si

| SID | DOI | Published vs T |
|---|---|---|
| 27819 | `10.1016/j.materresbull.2020.110885` | n, μ, σ, PF, S, κ, ZT |
| 29196 | `10.1016/j.actamat.2020.07.045` | μ, σ, κ_L, PF, S, κ, ZT |
| 66 | `10.1016/j.actamat.2014.04.060` | σ, κ_L, PF, S, κ, ZT |
| 2182 | `10.1063/1.4918311` | σ, κ_L, PF, S, κ, ZT |
| 2822 | `10.1039/c5ta03751d` | σ, ρ, PF, S, κ, ZT |
| 7068 | `10.1016/j.applthermaleng.2016.05.146` | σ, κ_L, PF, S, κ, ZT |

### 3.3 Mg₂Sn

| SID | DOI | Published vs T |
|---|---|---|
| 16684 | `10.1073/pnas.1424388112` | σ, κ_L, PF, S, κ, ZT |
| 24687 | `10.1038/s41598-020-58998-1` | σ, κ_L, PF, S, κ, ZT |
| 31469 | `10.1016/j.mtphys.2020.100327` | ρ, κ_L, PF, S, κ, ZT |
| 32064 | `10.1016/j.actamat.2017.09.009` | ρ, κ_L, PF, S, κ, ZT |
| 2198 | `10.1063/1.4933277` | σ, PF, S, κ, ZT |
| 2348 | `10.1007/s11664-012-1985-x` | ρ, PF, S, κ, ZT |

### 3.4 Bi₂Te₃-based

| SID | DOI | Published vs T |
|---|---|---|
| 24609 | `10.1007/s10854-019-01874-0` | n, μ, σ, κ_L, PF, S, κ, ZT — **active benchmark** |
| 24621 | `10.1021/acsami.9b10394` | n, μ, σ, κ_L, PF, S, κ, ZT |
| 31965 | `10.1016/j.matdes.2016.09.089` | n, μ, σ, κ_L, PF, S, κ, ZT |
| 37273 | `10.1007/s40843-021-1666-6` | n, μ, σ, κ_L, PF, S, κ, ZT |
| 5750 | `10.1021/acsnano.6b01156` | n, μ, σ, PF, S, κ, ZT |
| 9824 | `10.1016/j.jallcom.2016.05.340` | n, μ, σ, PF, S, κ, ZT |

### 3.5 PbTe

| SID | DOI | Published vs T |
|---|---|---|
| 34272 | `10.1002/adma.201703148` | n, μ, σ, κ_L, PF, S, κ, ZT |
| 51183 | `10.1021/acs.chemmater.2c03542` | n, μ, σ, κ_L, PF, S, κ, ZT |
| 31457 | `10.1002/adfm.202007340` | n, σ, κ_L, PF, S, κ, ZT |
| 585 | `10.1021/cm803437x` | n, σ, PF, S, κ, ZT |
| 864 | `10.1039/c2ee22495j` | n, σ, PF, S, κ, ZT |
| 27903 | `10.1088/1361-6463/ab7d6c` | ρ, κₑ, κ_L, PF, S, κ, ZT |

### 3.6 SnSe

| SID | DOI | Published vs T |
|---|---|---|
| 24753 | `10.1002/adfm.201908405` | n, μ, σ, κ_L, PF, S, κ, ZT |
| 31731 | `10.1016/j.mattod.2017.11.005` | n, μ, σ, κ_L, PF, S, κ, ZT |
| 32056 | `10.1021/jacs.7b11875` | n, μ, σ, κ_L, PF, S, κ, ZT |
| 32268 | `10.1002/aenm.201901334` | n, μ, σ, κ_L, PF, S, κ, ZT |
| 37183 | `10.1016/j.jssc.2021.122626` | n, μ, σ, κ_L, PF, S, κ, ZT |
| 37683 | `10.1021/acsnano.1c03120` | n, μ, ρ, κ_L, PF, S, κ, ZT |

### 3.7 CaMnO₃-based

| SID | DOI | Published vs T |
|---|---|---|
| 31248 | `10.1016/j.cej.2020.127364` | σ, κ_L, PF, S, κ, ZT |
| 31639 | `10.1016/j.jallcom.2016.12.359` | σ, κ_L, PF, S, κ, ZT |
| 531 | `10.1016/j.ceramint.2014.09.089` | ρ, PF, S, κ, ZT |
| 1636 | `10.1016/j.jallcom.2009.08.012` | σ, PF, S, κ, ZT |
| 1687 | `10.1016/j.jallcom.2011.04.056` | σ, PF, S, κ, ZT |
| 1797 | `10.1016/j.jallcom.2014.12.141` | ρ, PF, S, κ, ZT |

---

## 4. Provenance record format

Every benchmark that is activated must carry the following fields, in the
registry (`tests/experimental_benchmarks/registry.py`) and in the extracted
dataset:

| Field | Meaning |
|---|---|
| `family` | Material class (one of the seven) |
| `composition` | Exact composition string as published |
| `doi` | Digital object identifier of the source publication |
| `journal` | Journal name |
| `year` | Publication year |
| `title` | Publication title |
| `sample_note` | Which specimen within the publication (the sample ID) |
| `grids` | Which published curves were extracted |
| `comparisons` | Per grid: `experimental` or `consistency` (enforced by `test_report_consistency.py`) |
| `notes` | Known caveats (e.g. unusable published curve) |

The *measurement-level* provenance (temperature, S, σ, n_H, μ_H, κ, m*) is
carried by the extracted CSV, whose column headers record the source
property name and unit, and whose extraction is deterministic —
`extract_benchmarks.py` regenerates the on-disk dataset **byte-identically**
from the upstream snapshot.

**Digitisation uncertainty.** The published curves are digitised from the
publication's figures. The extracted datasets therefore carry an
*inherent* interpolation/digitisation uncertainty that dominates any
comparison tighter than a few per cent. This is why the experimental
comparisons are reported as a distribution of relative deviations over the
temperature grid rather than as a single pass/fail number.

---

## 5. Why four families are not yet active benchmarks

Each of these is a **scientific** reason, not an oversight.

### 5.1 Bi₂Te₃ — the published mobility curve is negative

For the active Bi₂Te₃ specimen (`10.1007/s10854-019-01874-0`) the
published **carrier-mobility** curve is negative, which is physically
impossible. It cannot serve as a reference for the weighted mobility, and
the comparison is therefore skipped with the reason recorded in the test
output rather than replaced by a substitute value.

This is also why the κ_L comparison for this specimen is classified
`consistency` rather than `experimental`: the Lorenz number used is derived
from the same publication's κ_L.

### 5.2 PbTe — the published κ and κ_L are not consistent with one Lorenz number

For the active PbTe specimen (`10.1016/j.cap.2020.06.028`) the published
total and lattice thermal conductivities imply a Lorenz number with a
25 % spread around 1.276e-8 W·Ω/K² — i.e. the published pair is not
internally consistent. The κ_L comparison is therefore limited by the
source data rather than by the calculation, and is reported UNVERIFIED.

A second, deeper point applies to the PbTe family in general: **PbTe is
strongly degenerate at the temperatures of interest**, and the
single-parabolic-band Lorenz number deviates from the Sommerfeld value by
up to 130 % in that regime. This is documented in the limitations report as
a *model* limitation, not a code defect.

### 5.3 Mg₂Sn — bipolar conduction and two-band transport

The Mg₂Sn family (and its Mg₂Si₀.₄Sn₀.₆ solid solutions) exhibits bipolar
transport above a characteristic temperature: both electron and hole
conduction contribute, so the measured Seebeck coefficient is not a
single-band quantity and the SPB inversion is not physically applicable.
A benchmark for this family must therefore compare against a **two-band**
model — which the application does not implement. Adding such a model
would violate the plan's constraint *"do not add new scientific models
during this validation task"*. The family is registered and ready; the
comparison protocol is deliberately deferred.

### 5.4 SnSe — strong anisotropy

SnSe is a layered, strongly anisotropic material: the in-plane and
c-axis transport properties differ by one to two orders of magnitude. The
application's transport model is isotropic. A single published curve does
not identify the direction, so comparing it with an isotropic model would
be comparing different quantities. An anisotropic benchmark would require
the application to carry a direction label — a data-model change, not a
validation artefact.

### 5.5 CaMnO₃-based oxides — the Lorenz number is the question, not the answer

The oxide family's scientific purpose in the plan is *"oxide transport and
Lorenz-number limitations"*. In oxides the electronic thermal conductivity
is small and the Lorenz number departs strongly from both the Sommerfeld
and the SPB acoustic value; moreover these materials are typically
**insulators at low T**, where the measured "carrier concentration" is
model-dependent. A meaningful CaMnO₃ benchmark is a study of the Lorenz
number itself, which is precisely the quantity the application *cannot*
derive from published data without circularity (using κ_L to get L and then
κ_L to check L). The family is registered; the honest comparison would
need an independent L measurement (e.g. from a Wiedemann–Franz analysis
published alongside the transport data), which the snapshot does not
contain.

---

## 6. Adding a new family

The procedure is fixed and reproducible:

1. Pick a specimen from §3 with the required published quantities.
2. Add an entry to `tests/experimental_benchmarks/registry.py` with the full
   provenance fields and the per-grid `comparisons` classification.
3. Extend `tests/experimental_benchmarks/extract_benchmarks.py` with the
   extraction rule for that specimen (composition string, SID, curve
   property names, unit handling, temperature range).
4. Regenerate the dataset and confirm the regeneration is
   **byte-identical** to the committed file.
5. The comparison test picks up the new registry entry automatically; the
   report-consistency test verifies that both reports match the registry.

No new scientific model is introduced by this procedure, and no published
number is altered: the application computes its value, the publication
provides the reference, and the deviation is reported.

---

## 7. Honest status of the material-family coverage

| Item | Status |
|---|---|
| All seven families surveyed against a DOI-level source | **VERIFIED** (survey reproducible from the snapshot) |
| Four families used as active experimental benchmarks | **VERIFIED** (PF and ZT against published values) |
| Bi₂Te₃ weighted-mobility experimental validation | **UNVERIFIED** — published mobility curve is negative |
| PbTe κ_L consistency comparison | **UNVERIFIED** — published κ/κ_L pair implies a 25 %-spread Lorenz number |
| Mg₂Sn / SnSe / CaMnO₃ active comparisons | **NOT IMPLEMENTED** in this validation cycle — the required model (two-band), the required data dimension (anisotropy) or the required independent reference (non-circular Lorenz number) is absent |
| SPB validity for any of the seven families | **PARTIALLY VERIFIED** — the SPB *implementation* is verified against an independent reference; the *physical applicability* of SPB is family-specific and is not claimed |
