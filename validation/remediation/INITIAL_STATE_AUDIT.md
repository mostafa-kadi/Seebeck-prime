# Initial State Audit — Seebeck Prime

**Phase:** 1 (read-only)
**Date:** 2026-11-12
**Auditor scope:** local working tree only — no network, no GitHub, no push/pull/publish
**Method:** direct inspection of the source tree, the test suite, the validation
package, the packaging configuration and the documentation; reproduction of the
test run in the local environment; targeted runtime probes for the GUI and the
Qt runtime.
**No source, test, configuration or documentation file was modified during this
phase.** The only file created is this audit and its directory.

---

## 0. Summary of the audit

| Question | Answer |
|---|---|
| Does the previous report's headline ("592 passed, 6 skipped") still hold? | **Yes — reproduced exactly.** |
| Is the report's "41 of 50 status entries VERIFIED" correct? | **No.** The status table has **49** rows; the §8.1 summary claims 50 and over-counts PARTIALLY VERIFIED by one (5 vs 4). |
| Is the equation registry complete? | **Yes for what it claims** — E-01…E-62, no gaps. But it counts *equations*; the status table counts *calculations*, and the two are not in one-to-one correspondence. |
| Is SE-042 really fixed? | **Yes** — `src/domain/units.py` now validates the thermal-conductivity unit and a regression test exists. |
| Are the physical models validated? | **No.** The SPB *implementation* is correct (re-derived independently in §4.1); the SPB *model* is contradicted by the one specimen whose published data can arbitrate. |
| Are the six "untested" GUI dialogs really untestable? | **Partly false.** Five of the six are opened with `.show()` (non-modal) and are `QTest`-driveable; only `ErrorBarDialog` and `PlotDataDialog` use modal `exec()`. |
| Is the raw V/I → R → ρ → σ chain missing? | **Yes — confirmed absent.** Geometry is used only for σ *uncertainties*, never to derive ρ from a measured R. |
| Is the negative-κ_L warning surfaced to the user? | **No — this is the most serious finding.** The validator exists and is unit-tested, but **no production code path calls it**. |
| Is the project installable and releasable today? | **No.** No `LICENSE`, no `CITATION.cff`, version inconsistency, an unsupported MIT claim, a placeholder repository URL and a machine-specific path in `pyproject.toml`. |

---

## 1. Repository inventory

```
Seebeck-Prime/
├── main.py                     entry point (PyQt6 GUI)
├── setup.py                    packaging (flat-layout package mapping)
├── pyproject.toml              build-system only + a machine-specific tool path
├── requirements.txt            unpinned dependencies
├── README.md  CHANGELOG.md  CONTRIBUTING.md
├── src/
│   ├── domain/        (13 files)  calculation core  — 1 958 lines
│   ├── application/   (11 files)  use cases, importers, services
│   ├── presentation/  (12 files)  table/plot/label logic
│   ├── gui/           ( 4 files)  main window, file commands
│   ├── infrastructure/( 2 files)  pandas I/O adapter
│   ├── plugins/       ( 6 files)  Arrhenius + 4 backward-compat shims
│   ├── legacy/        (24 files)  compatibility dialogs and wrappers
│   └── seebeck_prime/__init__.py  import-root path-extension shim
├── tests/                       34 test modules + benchmark datasets
├── validation/                  the scientific validation package (§6)
├── tools/                       2 reproducible generators
├── scripts/generate_golden_baseline.py
├── examples/                    synthetic dataset + headless analysis
└── docs/                        architecture, model register, SoftwareX prep
```

`git status` (read-only): 15 modified, 171 deleted, 60 untracked — the tree
carries the whole migration/validation programme **uncommitted**. Nothing is
committed, pushed, merged or released.

### 1.1 Architecture (as implemented)

Layered and enforced by `tests/test_architecture_dependencies.py` (24 tests):

```
gui ──► presentation ──► application ──► domain
              │                │
              └── infrastructure (pandas I/O adapter)
```

`src/seebeck_prime/__init__.py` extends `__path__` so the flat `src/<layer>`
directories resolve as `seebeck_prime.<layer>`. `setup.py` maps each layer to
its own package directory so a built wheel contains only `seebeck_prime/...`.

---

## 2. What exists and is already implemented

Verified by inspection *and* by a passing test suite.

| Area | Implementation | Files |
|---|---|---|
| Core transport | PF, κₑ, κ_L, ZT, Kim L, formula mass, Dulong–Petit | `src/domain/calculations.py` |
| SPB model | Fermi–Dirac integrals (3 branches), S(η), η-inversion, rigorous L(η), n(η,m*,T), m*(S,n,T), Pisarenko curve, optimal transport, empirical estimators | `src/domain/spb.py` (404 lines) |
| Hall | R_H, n_H, carrier type, μ_H, scattering-exponent fit | `src/domain/hall.py` |
| Phonon / laser flash | κ = αC_pρ (SI and laboratory units), Dulong–Petit | `src/domain/phonon.py` |
| Device efficiency | ZT̄, ZT_eng, Carnot, η_max, η_eng | `src/domain/device_efficiency.py` |
| Uncertainty | 7 first-order propagators + 1 relative combiner | `src/domain/uncertainty.py` |
| Units | 12 conversion functions across 6 quantities | `src/domain/units.py` |
| Physical validation | T / σ / S / κ / κ_L validators with severities | `src/domain/validation.py` |
| Importers | four-probe, raw-Seebeck, laser-flash | `src/application/measurement_processing.py` |
| Column mapping | alias matcher with physical-plausibility guards | `src/application/data_mapping.py` |
| SPB batch | per-row results + legacy mean parameters | `src/application/spb_batch.py` |
| Arrhenius | ln σ, ln σT, log₁₀ σ activation energies | `src/plugins/arrhenius.py` |
| GUI | main window + 10 QDialog tools | `src/gui/`, `src/legacy/ui/dialogs/` |
| I/O adapter | CSV / TSV / TXT (delimiter sniffing) / Excel / multi-sheet workbooks | `src/infrastructure/io.py` |
| Independent references | 36 functions, no application imports (AST-enforced) | `validation/independent_calculations/references.py` |
| Published benchmarks | 4 specimens, 3 publications, DOI-level provenance, byte-reproducible extraction | `tests/experimental_benchmarks/` |

---

## 3. Test accounting (reproduced locally, 2026-11-12)

### 3.1 Totals

| Metric | Value |
|---|---|
| Collected items (`pytest --collect-only -q`) | **597** |
| Module-level skip (whole module unimportable) | +1 |
| Total items reported by the run | **598** |
| **Passed** | **592** |
| **Failed** | **0** |
| **Skipped** | **6** |

### 3.2 By group

| Group | Collected | Passed | Skipped |
|---|---|---|---|
| `tests/scientific/` — new independent-reference, physical-constraint, unit-matrix, edge-case | 141 | **141** | 0 |
| `tests/experimental_benchmarks/` — published measurement, importers, workflows, GUI e2e, report consistency | 113 (+1 module skip) | 109 | 5 |
| `tests/test_*.py` — root engineering / unit / audit suites | 343 | 342 | 1 |
| **Total** | **597 (+1)** | **592** | **6** |

### 3.3 Overlap

The three groups **do not overlap** — they are disjoint file sets:

- `tests/scientific/` exercises the *domain* against independently written
  reference implementations (`validation/independent_calculations/`).
- `tests/experimental_benchmarks/` exercises the *workflow* against published
  measurements and against the committed provenance.
- `tests/test_*.py` covers engineering invariants (architecture, import roots,
  legacy compatibility), the golden regression snapshot, and a 63-test audit
  suite (`tests/test_scientific_equations_audit.py`).

**One file is counted in two groups by nature:**
`tests/experimental_benchmarks/test_report_consistency.py` (9 tests) both
validates the benchmark data *and* re-measures the test counts of the
benchmark directory, so it must exclude itself from its own subprocess
measurement. It is counted once in the totals above.

### 3.4 Every skip, with its reason

| # | Test | Reason | Class |
|---|---|---|---|
| 1 | `tests/experimental_benchmarks/test_gui_end_to_end.py` (whole module, 4 tests) | `ImportError: DLL load failed while importing QtWidgets: The specified procedure could not be found` — the conda base environment's Qt is broken (§5.1). **The same 4 tests pass in the Qt-capable venv.** | **environmental** |
| 2 | `tests/test_startup_smoke.py::test_import_main_smoke_when_qt_available` | Same Qt DLL failure. **The same test passes in the venv.** | **environmental** |
| 3 | `test_benchmarks.py:275` | `sige_si80ge18sb2`: the source paper publishes no lattice thermal conductivity | **missing reference data** |
| 4 | `test_benchmarks.py:326` | `sige_si80ge18sb2`: no published lattice thermal conductivity | **missing reference data** |
| 5 | `test_benchmarks.py:292` | `pbte_pbte0_95pbs0_05`: the published κ and κ_L imply a Lorenz number with a 25 % spread — the comparison is limited by the source data, not by the calculation | **missing reference data / noise-limited** |
| 6 | `test_workflow_validation.py:204` | The published carrier-mobility curve is negative (physically impossible) and unusable as a reference | **unusable reference data** |

**Summary:** 2 of the 6 skips are environmental and are *covered* by the venv
run (7 GUI tests pass there). The other 4 are **scientific gaps** that no
amount of software testing can close — they must stay open and reported.

### 3.5 The GUI-capable environment

| Property | Value |
|---|---|
| Interpreter | `%LOCALAPPDATA%\Temp\opencode\seebeck-gui\Scripts\python.exe` |
| Base interpreter | `C:\Users\Elkady\anaconda3\python.exe` (a **plain venv**, `include-system-site-packages = false`) |
| PyQt6 / Qt | 6.9.1 / 6.9.0 |
| Result | `test_gui_end_to_end.py` → 4 passed; `test_startup_smoke.py` → 3 passed |

---

## 4. Genuinely defective (confirmed by inspection and/or runtime probe)

### D-01 · HIGH · A negative lattice thermal conductivity is never reported to the user

**Files**
- `src/domain/validation.py:90` — `validate_kappa_l_array()` (emits the WARNING)
- `src/application/use_cases.py:205` — `validate_measurement_data()` (forwards it)
- `src/gui/main_window.py:291-301` — `recalculate_all_properties()` (**never calls it**)
- `src/presentation/kappa_logic.py` — the Kappa tool (**never calls it**)

**Evidence.** `validate_measurement_data` has **no production caller**. A
repository-wide search for `validate_measurement_data|validate_dataset|
validate_kappa_l_array` finds only the definitions, the re-export in
`src/domain/__init__.py`, and the tests. The GUI computes κ_L and writes it
straight into the table:

```python
calculated = calculate_thermoelectric_properties(...)
df["Lattice TC"] = calculated["kappa_L"]      # no validation, no warning
df["ZT"]        = calculated["ZT"]
```

So a physically impossible κ_L < 0 — the classic symptom of a wrong Lorenz
number or a unit error — is displayed and plotted as an ordinary value, and is
exported to the spreadsheet, with **no diagnostic at all**.

**Why this matters.** This directly contradicts two shipped claims:
`validation/SCIENTIFIC_EQUATION_REGISTRY.md` (E-03: *"negative-result flagging
(VERIFIED)"*) and `validation/SCIENTIFIC_CALCULATION_TEST_RESULTS.md` (§8:
*"negative result flagged → VERIFIED"*). What is verified is the *validator*,
not the *flagging*. The task brief's requirement — *"a negative calculated
lattice thermal conductivity must not silently appear as a physically valid
result"* — is **not met in the shipped application**.

**Remediation direction (Phase 3).** Surface the existing validation result in
the recalculation and Kappa workflows. **Do not clip the value to zero** — the
negative number must remain in the data for diagnosis, with a warning attached.

### D-02 · MEDIUM · The committed benchmark provenance cards mis-state the carrier units

**Files**
- `tests/experimental_benchmarks/references/sige_si80ge20p1.md:25-26`
- `tests/experimental_benchmarks/references/b2te3_bi2te2_4se0_6cu0_006.md:24-25`
- generator: `tests/experimental_benchmarks/extract_benchmarks.py:83` (`EXPECTED_UNITS`)

**Evidence.** The cards state

```
- Carrier concentration (cm^(-3))
- Carrier mobility (cm^2*V^(-1)*s^(-1))
```

but the committed raw extracts say otherwise:

| Dataset | `prop_y` | `unit_y` (actual) |
|---|---|---|
| `sige_si80ge20p1` | Carrier concentration | **`m^(-3)`** |
| `sige_si80ge20p1` | Carrier mobility | **`m^2*V^(-1)*s^(-1)`** |
| `b2te3_bi2te2_4se0_6cu0_006` | Carrier concentration | **`m^(-3)`** |
| `b2te3_bi2te2_4se0_6cu0_006` | Carrier mobility | **`m^2*V^(-1)*s^(-1)`** |

The generator's `EXPECTED_UNITS` does not list the carrier properties at all,
so their units are **neither validated at extraction time nor recorded
correctly**. The application and the benchmark test both correctly use m⁻³
(`test_report_consistency.py:198` asserts `n_unit == "m^(-3)"`), so the
*data* is right and the *card* is wrong.

**Secondary observation.** The committed cards are also **stale relative to
the current generator**: `extract_benchmarks.py:262-301` now emits a richer
card with "Measurement conditions", authors, journal, year and a
"Units (as published in the StarryData release)" section, while the committed
cards still carry the old "Published properties in this dataset" format. The
cards were never regenerated.

### D-03 · MEDIUM · Version is declared inconsistently in three places

| File | Value |
|---|---|
| `setup.py:58` | `version="0.1.0"` |
| `src/seebeck_prime/__init__.py:5,21` | `Version: 1.0.0-dev` / `__version__ = "1.0.0-dev"` |
| `docs/softwarex/CITATION.cff.template:11` | `version: "0.1.0"` |
| `docs/softwarex/software_metadata.md:8` | "0.1.0 (from `setup.py`; confirm release tag)" |
| `CHANGELOG.md` | 0.1.0, marked Unreleased |

A reader of the installed package sees `1.0.0-dev`; a reader of the PyPI
metadata sees `0.1.0`. `docs/SUPPORTED_PYTHON.md` already flags the release
tag as an author action.

### D-04 · MEDIUM · The project claims an MIT licence it has not chosen

**Files**
- `setup.py:69` — classifier `"License :: OSI Approved :: MIT License",  # Or your chosen license`
- `src/seebeck_prime/__init__.py:23` — `__license__ = "MIT"`
- `docs/softwarex/software_metadata.md:9` — "License: **Not finalized** (author approval required)"
- `docs/ARCHITECTURE_DECISION_RECORD.md:53` — "ADR-008 — No license change without author approval"
- `CHANGELOG.md:245` — "No license file yet (`setup.py` claims MIT — pending author decision)"

There is **no `LICENSE` file**. The packaging metadata therefore advertises a
licence that the project has explicitly deferred, and the package's own
`__license__` attribute asserts it. For a SoftwareX submission this is a
blocking inconsistency: the published licence and the deposited licence must
match.

### D-05 · LOW · Placeholder repository URL in packaging metadata

`setup.py:66` — `url="https://github.com/user/seebeck-prime",  # Replace with your repo URL`.
The real repository is recorded in `docs/softwarex/software_metadata.md:10` and
`docs/softwarex/CITATION.cff.template:10` as
`https://github.com/mostafa-kadi/Seebeck-prime`.

### D-06 · LOW · `pyproject.toml` hard-codes a machine-specific interpreter path

`pyproject.toml:6` — `[tool.pyrefly] python-interpreter-path = "C:/Users/Elkady/anaconda3/python.exe"`.
This makes the build configuration non-portable; any other checkout on any
other machine inherits a path that does not exist.

### D-07 · LOW · The results report's own counts do not match its table

`validation/SCIENTIFIC_CALCULATION_TEST_RESULTS.md` §8 contains **49** rows
(41 VERIFIED + 4 PARTIALLY VERIFIED + 3 NOT IMPLEMENTED + 1 UNVERIFIED), but the
§8.1 summary immediately below states **PARTIALLY VERIFIED 5** and a total of
**50**. Verified by re-counting the table rows with a status parser.

### D-08 · LOW · Stale statements in the SoftwareX preparation documents

| File | Stale statement | Actual |
|---|---|---|
| `docs/softwarex/starrydata_snapshot.md:84` | "The **three** selected benchmarks" | four |
| `docs/softwarex/author_guideline_compliance.md` | "Source distribution under `src/` … `src/seebeck_prime/` canonical package" | `src/seebeck_prime/` is only the **path-extension shim**; the implementation is in the sibling layer directories |
| `docs/softwarex/author_guideline_compliance.md` | "no changelog" | `CHANGELOG.md` exists |
| `docs/softwarex/author_guideline_compliance.md` | "177 passed, 1 conditional skip" | 592 passed, 6 skipped |
| `docs/softwarex/software_metadata.md:17` | "pytest (147 passing baseline)" | 592 passed, 6 skipped |
| `docs/SUPPORTED_PYTHON.md:39` | references `docs/softwarex/compliance_checklist.md` | the file is `author_guideline_compliance.md` |

### D-09 · LOW · `propagate_sigma_error` is implemented, exported and never used

`src/domain/uncertainty.py:167` defines the geometry-based σ propagator; it is
re-exported by `src/domain/__init__.py:40,77` and consumed only by
`tests/scientific/`. No production path calls it — the application's σ
uncertainty comes from `application/measurement_processing.py:304`
(`combine_sigma_uncertainty`), a *separate* formula. Two implementations of
the same physics coexist; only one is live.

---

## 5. Missing, incomplete, or not verifiable

### 5.1 The PyQt6 environment failure — root cause now identified

**Symptom.** In the conda base environment,
`import PyQt6.QtWidgets` raises
`ImportError: DLL load failed while importing QtWidgets: The specified procedure
could not be found` (Windows status `0xc0000139`, `STATUS_ENTRYPOINT_NOT_FOUND`).

**Root cause (measured, not guessed).**

| Evidence | Value |
|---|---|
| `anaconda3\Library\bin\Qt6Core.dll` | 5 790 024 bytes (conda-forge Qt 6.x) |
| `anaconda3\Lib\site-packages\PyQt6\Qt6\bin\Qt6Core.dll` | 10 480 440 bytes (pip `PyQt6-Qt6` **6.11.1**) |
| conda packages | `pyqt6 6.11.0`, `pyqt6-qt6 6.11.1` (both **pypi**, not conda-forge) |
| `ctypes.CDLL("Qt6Core.dll")` in the conda env | **succeeds** → the conda copy is the one that resolves |
| `import PyQt6.QtCore` | **fails** → the PyQt6 6.11.0 bindings need symbols that the shadowing conda Qt6Core does not export |

The conda prefix's `Library\bin` is registered in the interpreter's DLL search
path **ahead of** the pip package's own `PyQt6\Qt6\bin`, so the older
conda-forge Qt6 runtime shadows the PyQt6 runtime it belongs to. The two are
ABI-incompatible → the entry point is missing.

**Fix candidates tested (all four failed in the conda base env):**

| Candidate | Result |
|---|---|
| A. baseline | FAIL |
| B. `os.add_dll_directory(<pip PyQt6 Qt6\bin>)` before the import | FAIL |
| C. preload the pip `Qt6Core.dll`/`Qt6Gui.dll` by absolute path via `ctypes` | FAIL (`WinError 127`) |
| D. B + prepend the pip Qt bin to `PATH` | FAIL |

Removing `anaconda3\Library\bin` from `PATH` alone also does **not** fix it,
because the conda prefix directories are registered by the interpreter, not
only by `PATH`.

**The working solution (verified).** A **plain virtual environment** isolates
the Qt runtime, because a venv does not inherit the conda prefix's DLL
directory registration — and it keeps working even with
`anaconda3\Library\bin` on `PATH`:

```
venv\Scripts\python.exe -c "import PyQt6.QtWidgets"   →  OK (Qt 6.9.0 / PyQt 6.9.1)
```

That is exactly the environment in which the 7 GUI tests pass.

**Conclusion.** This is **not** an application defect and **not** a PyQt6
defect. It is an environment-construction problem: the conda base environment
mixes a pip PyQt6 stack with a conda-forge Qt runtime. The reproducible remedy
is to build the application environment as a **venv**, not a conda base
environment, and to document it. No package pinning or upgrading is required
or advisable.

### 5.2 The six "untested" GUI dialogs are mostly *testable* — the prior report overstates the obstacle

`src/gui/main_window.py` opens the tools as follows:

| Dialog | How it is opened | Modal? | QTest-driveable? |
|---|---|---|---|
| `KappaToolDialog` | `self.kappa_tool_dialog.show()` (`main_window.py:549`) | no | **yes** |
| `MultiSampleDialog` | `.show()` (`:556`) | no | **yes** |
| `WeightedMobilityDialog` | `.show()` (`:593`) | no | **yes** |
| `HallMobilityDialog` | `.show()` (`:615`) | no | **yes** |
| `SPBModelingDialog` | `.show()` (`:637`) | no | **yes** |
| `DeviceEfficiencyDialog` | `.show()` (`:667`) | no | **yes** |
| `ErrorBarDialog` | `dialog.exec()` (`:225`) | **yes** | only with a refactor |
| `PlotDataDialog` | `dialog.exec()` (`:688`) | **yes** | only with a refactor |

Only **two** dialogs block the event loop. All ten dialog classes are
`QDialog` subclasses (`src/legacy/ui/dialogs/*.py`) and none calls
`setModal(True)`. The prior report's claim that *"each of these dialogs is
opened with a modal `dialog.exec()`"* is therefore **inaccurate for five of
the six**, and the estimated remediation effort is materially smaller than
stated. The four dialogs that the task brief names (error bar, κ, SPB, Hall,
weighted mobility, multi-sample) are: 5 non-modal + 1 modal.

### 5.3 The raw V/I → R → ρ → σ chain is genuinely absent — confirmed

- `src/application/measurement_processing.py:102` `process_four_probe_table()`
  requires a **conductivity** column (`"conductivity", "sigma", "σ", "s/cm"`,
  line 109) — there is no voltage/current input path anywhere.
- `src/domain/uncertainty.py:167` `propagate_sigma_error()` computes
  σ = L/(R·A) as an *uncertainty* helper only; it is never called (D-09).
- Geometry (`width`, `thickness`, `probe_length`) collected by
  `src/legacy/ui/dialogs/error_bar_dialog.py:95-111` is consumed **only** by
  `application/measurement_processing.py:304` `combine_sigma_uncertainty()`,
  which combines *relative* geometry errors for an **already measured** σ.

So: no resistance is computed from a measured V/I, no resistivity is derived
from geometry, and the application assumes the instrument file already
contains σ. The task brief's §6 capability list is therefore genuinely
unimplemented.

### 5.4 The physical models are not validated, and one is contradicted

**The SPB implementation is correct.** This was re-derived independently for
this audit (Phase 1 is read-only, so no code changed):

With the **unnormalised** complete Fermi–Dirac integral
F_j(η) = ∫₀^∞ x^j/(1+e^{x−η})dx and the transport exponent r = λ − ½, the
Seebeck coefficient is

S(η) = (k_B/e)·[ ((λ+2)/(λ+1))·F_{λ+1}(η)/F_λ(η) − η ]

which is **exactly** what `src/domain/spb.py:136` implements, and is
identical to the Blatt-normalised textbook form
(k_B/e)·[(λ+2)·F̂_{λ+1}/F̂_λ − η] because the Γ factors reduce the prefactor
to (λ+2)/(λ+1) and not to 1. The same reduction holds for
`rigorous_lorenz_number()` (`spb.py:204-205`), and `_CONST_N0_SI`
(`spb.py:49`) carries the 1/Γ(3/2) factor that the unnormalised convention
requires for `calculate_carrier_density_spb()`. **No SPB defect was found.**

*Numerical confirmation* (independent quadrature, this audit):

| Check | Worst relative difference |
|---|---|
| app `S(η)` vs Blatt textbook form (λ = 0, 1, 2; η = −8…8) | **7.1e-15** |
| app `S(η)` vs the unnormalised form with the reduced prefactor | **7.1e-15** |
| app `S(η)` vs the *wrong* unnormalised form (prefactor 1) | factor 2.00 (λ=0), 1.33 (λ=2) — the app is **not** this one |
| app `S(η)` vs the Boltzmann limit (k_B/e)(λ+2−η) | **4.7e-11** |
| app `L(η)` vs the Blatt transport-integral form | **1.4e-14** |

**But the model is contradicted by the published SiGe data.** For
Si₈₀Ge₂₀P₁ (`10.1021/acsami.9b20090`) the published κ, κ_L and σ imply
L ≈ 2.4579e-8 W·Ω/K² — the Sommerfeld value — while the SPB acoustic-phonon
model (λ = 0) gives ≈1.592e-8, i.e. **−35 %**. The application's *default*
2.44e-8 is the value that agrees with the data (≤0.7 % on κ_L).

**Open hypotheses to discriminate in Phase 3** (none acted on yet):
(a) the specimen is not acoustic-scattering dominated at 300–1000 K
(P-doped SiGe has significant alloy + ionised-impurity scattering);
(b) the SPB single-band assumption fails for that alloy;
(c) the published κ_L and κ are not mutually consistent (unlike the PbTe
dataset, where the 25 % spread was already detected);
(d) the reconstruction/interpolation of the digitised curves introduces the
offset.
**The SPB model must not be modified to reproduce the experimental value
unless one of these is demonstrated.**

### 5.5 Missing release artefacts

| Artefact | Status |
|---|---|
| `LICENSE` | **absent** (D-04) |
| `CITATION.cff` | **absent** — only `docs/softwarex/CITATION.cff.template` with `REQUIRES AUTHOR INPUT` placeholders |
| Author-controlled metadata | `docs/softwarex/author_controlled_information.md` lists 12 items the authors must supply: names, affiliations, corresponding author, ORCID, funding, COI, contributions, acknowledgements, licence choice, Zenodo DOI, release tag, publication status. **These must not be invented.** |
| Release tag / archive DOI | not created — must not be claimed |
| User manual | none (in-app dialogs only) |
| Dependency pins | `requirements.txt` has no version specifiers |

### 5.6 What cannot be verified from the available files

| Item | Why |
|---|---|
| Whether the published benchmark values belong to one specimen | **Verified for all four**: each raw extract has a single `composition` and a single `sample_id`, so the compared curves come from one `(SID, sample_id)`. |
| **Measurement direction** (in-plane / c-axis) | **Not recorded** in the source. StarryData's `sample_info` fields (`ThermalMeasurement`, `ElectricalMeasurement`, `Other`) are empty strings for these samples. The direction therefore **cannot be asserted** for any benchmark — which matters for SnSe (strongly anisotropic) and is an argument against promoting SnSe to an active benchmark. |
| **Scattering assumptions** | **Not recorded** in the source, and not stated in the papers' aggregated metadata. The benchmarks therefore cannot support any SPB-based claim. |
| Raw tables vs digitised figures | **Digitised figures** for all four (`tests/experimental_benchmarks/references/starrydata_snapshot.md`), with a documented internal-consistency screen (501 → 238 candidates) before selection. |
| Published measurement uncertainties | **Not available** in the aggregated source; the ~1 % digitisation floor is the practical limit. |
| Whether the CI matrix (3.12/3.13) passes | `.github/workflows/tests.yml` has **never executed** (no push is permitted). |
| True support for Python 3.9 | `setup.py` declares `>=3.9`; only 3.13.9 has been exercised (`docs/SUPPORTED_PYTHON.md` already flags this). |

---

## 6. The validation package as it stands on disk

| Path | Size | State |
|---|---|---|
| `validation/SCIENTIFIC_EQUATION_REGISTRY.md` | 13 733 B | E-01…E-62, no gaps; 62 entries = 35 equation + 7 unit + 10 workflow + 6 GUI + 4 legacy |
| `validation/SCIENTIFIC_CALCULATION_TEST_PLAN.md` | 30 348 B | per-phase scope, tolerance derivation, existing-vs-new test map |
| `validation/SCIENTIFIC_CALCULATION_TEST_RESULTS.md` | 32 714 B | environment, commands, counts, skip reasons, 31-row comparison table, 49-row status table |
| `validation/SCIENTIFIC_VALIDATION_LIMITATIONS.md` | 19 604 B | negative findings |
| `validation/INDEPENDENT_REFERENCE_METHODS.md` | 20 360 B | derivations, conventions, the two reference-side discrepancies |
| `validation/SCIENTIFIC_BENCHMARK_MATERIAL_FAMILIES.md` | 14 583 B | seven families surveyed with real DOIs |
| `validation/reference_comparison_table.md` | 3 136 B | generated, 31 comparisons, 0 outside tolerance |
| `validation/independent_calculations/references.py` | 16 243 B | 36 functions, independence AST-enforced |
| `validation/README.md` | 3 833 B | index |

**The 62 ↔ 49 discrepancy, explained.** The two artefacts count different
things:

- The **registry** counts *equations*: 35 equation entries (E-01…E-07, E-08…
  E-15, E-23…E-42), 7 unit-conversion entries (E-16…E-22), 10 workflow
  entries (E-43…E-52), 6 GUI/presentation entries (E-53…E-58) and 4
  legacy-compatibility entries (E-59…E-62).
- The **status table** counts *calculations with a scientific status*: it
  **groups** related equations into one row (e.g. one "Uncertainty — PF" row
  covers E-08 and its Monte-Carlo check; "Unit conversions (all quantities)"
  collapses E-16…E-22), it **omits** entries that carry no independent
  physical status (the 4 legacy wrappers, the 6 GUI entries other than the
  interactive-gap row), and it **adds** 4 rows that have no registry entry at
  all (the missing uncertainty propagation for weighted mobility / SPB, and
  the missing Mg₂Sn / SnSe / CaMnO₃ experimental comparisons).

The counts are therefore not reconcilable by arithmetic alone; an explicit
per-equation mapping is required — this is exactly the Phase 2 deliverable
`EQUATION_STATUS_MAPPING.csv`.

---

## 7. Recommended remediation order

### Phase 2 — Validation reconciliation (no production code)

1. **2.1** Build `validation/remediation/EQUATION_STATUS_MAPPING.csv` — all 62
   registry entries → implementation file/function → test files → independent
   reference → numerical / physical / experimental status → remaining
   limitation. Explains the 62 ↔ 49 difference explicitly.
2. **2.2** Correct the §8.1 count in the results report (5 → 4 PARTIALLY
   VERIFIED; total 50 → 49) — **D-07**.
3. **2.3** Produce `validation/remediation/VALIDATION_STATUS.md` with the four
   required categories, replacing the current five-status vocabulary where it
   is ambiguous, and stating explicitly that *"fully validated"* is not used
   for model-conditional or experimentally unverified calculations.
4. **2.4** Publish the reproduced test accounting (§3 of this audit) with the
   per-group breakdown and the 6 reasoned skips.

### Phase 3 — Critical scientific corrections

5. **3.1 (D-01, highest priority)** Wire the existing negative-κ_L validation
   into the GUI recalculation and the Kappa workflow. **Preserve the negative
   value**; attach a warning. Add GUI-level regression tests.
6. **3.2 (D-02)** Correct the carrier units in the committed provenance cards
   and regenerate the cards with the current generator; add
   "Carrier concentration" and "Carrier mobility" to `EXPECTED_UNITS` so
   their units are validated at extraction time.
7. **3.3** Resolve the SiGe Lorenz discrepancy **as an investigation**, not as
   a code change: quantify the implied L per temperature point, test the
   scattering-exponent hypothesis (λ = 0/1/2) against the published data, and
   test hypothesis (c) — the internal consistency of the published κ/κ_L pair.
   Record the outcome as a documented negative result if no hypothesis
   survives. **Do not modify the SPB model to match the measurement.**
8. **3.4** Assess the degenerate-PbTe case (SPB L deviating by up to 130.6 %)
   as a *model* question: state the mathematical requirements for a
   Kane/Dingle correction, the literature basis, the inputs needed and the
   validation data available. **Implement nothing** unless the assessment
   shows it can be validated.
9. **3.5** Audit and document the weighted-mobility definition and unit
   convention against its source; keep the numerical result, the physical
   interpretation and the experimental status strictly separate (§4C).
10. **3.6** Add the derivation references and explicit unit tests for the SPB
    conventions (Blatt vs unnormalised, the Γ factors, the prefactors, the
    T^{3/2} in N_c) so that the convention cannot silently drift.
11. **3.7** Complete the unit-conversion audit across all 12 quantities,
    including the density, heat-capacity, mobility and effective-mass
    conversions, with round-trip tests. Keep the SE-042 regression test.

### Phase 4 — Uncertainty and measurement workflow

12. **4.1** Implement covariance-aware propagation
    (u²(y) = J Σ Jᵀ) **on top of** the existing independent default: validate
    the matrix dimensions, symmetry and positive-semidefiniteness; reject
    invalid input with informative errors; test against Monte-Carlo with both
    correlated and uncorrelated cases; document the assumptions.
13. **4.2** Implement the raw measurement chain as a **separate, modular**
    workflow (not inside the existing importers): V/I → R (with an explicit
    two- vs four-terminal distinction) → ρ (with an explicit geometry model
    and a documented assumption set) → σ, with geometry and measurement
    uncertainty propagation, raw-value preservation, a calculation history and
    export. Independent references and tests **before** any GUI integration.
    The task brief is explicit that reconstructed example data must not be
    presented as instrument validation.

### Phase 5 — GUI testing

14. **5.1** Build the QTest strategy on the **five non-modal** dialogs first
    (§5.2) — no production refactor required for them.
15. **5.2** Refactor `ErrorBarDialog` and `PlotDataDialog` to injectable,
    non-modal-friendly forms so the modal paths become testable.
16. **5.3** Cover input validation, calculation invocation, output values,
    error handling, cancel/close behaviour, data persistence and "no
    unintended change to other samples".
17. **5.4** Publish the Qt environment remedy as a documented, reproducible
    procedure (§5.1): build the application environment as a **venv**, never
    as a conda base environment; document the exact commands.

### Phase 6 — Release readiness

18. **6.1** Resolve the licence (D-04) with the authors, then add the
    `LICENSE` file and make `setup.py` + `__license__` + `CITATION.cff` agree.
19. **6.2** Add `CITATION.cff` from the template, filling only the
    author-controlled fields with **author-supplied** values; leave the rest
    as explicit `REQUIRES AUTHOR INPUT` placeholders (D-05 URL, D-03 version).
20. **6.3** Reconcile the version across `setup.py`, `__init__.py`, the
    changelog and the citation metadata (D-03).
21. **6.4** Fix the packaging metadata: real repository URL (D-05), remove the
    machine-specific interpreter path from `pyproject.toml` (D-06).
22. **6.5** Rewrite `README.md` for installation, usage, scientific scope and
    limitations; add the user-facing quick start.
23. **6.6** Update `validation/README.md` with the reproduced commands and
    environment; add `validation/remediation/RELEASE_READINESS.md`.
24. **6.7** Correct the stale SoftwareX preparation documents (D-08).
25. **6.8** Test a **clean-venv installation** end to end: install the wheel,
    start the application, and run a representative calculation without
    relying on the development checkout.

---

## 8. Findings index

| ID | Severity | Area | One-line description | Primary file |
|---|---|---|---|---|
| D-01 | **HIGH** | science / GUI | Negative lattice κ is never reported to the user; the validator has no production caller | `src/gui/main_window.py:291` |
| D-02 | MEDIUM | benchmarks | Provenance cards mis-state the carrier units (cm⁻³ → m⁻³) and are stale vs the generator | `tests/experimental_benchmarks/references/*.md` |
| D-03 | MEDIUM | packaging | Version declared as 0.1.0 and 1.0.0-dev in different places | `setup.py:58`, `src/seebeck_prime/__init__.py:21` |
| D-04 | MEDIUM | packaging | MIT claimed in metadata while the licence is undecided and no LICENSE file exists | `setup.py:69`, `src/seebeck_prime/__init__.py:23` |
| D-05 | LOW | packaging | Placeholder repository URL | `setup.py:66` |
| D-06 | LOW | packaging | Machine-specific interpreter path in the build config | `pyproject.toml:6` |
| D-07 | LOW | validation docs | Results-report §8.1 counts (5 / 50) do not match its own 49-row table | `validation/SCIENTIFIC_CALCULATION_TEST_RESULTS.md` §8.1 |
| D-08 | LOW | docs | Six stale statements in the SoftwareX preparation documents | `docs/softwarex/`, `docs/SUPPORTED_PYTHON.md` |
| D-09 | LOW | science | `propagate_sigma_error` implemented, exported and never used (duplicate of a live formula) | `src/domain/uncertainty.py:167` |
| M-01 | HIGH | feature | The raw V/I → R → ρ → σ chain is absent (confirmed) | `src/application/measurement_processing.py:102` |
| M-02 | MEDIUM | environment | The conda base environment mixes pip PyQt6 with conda-forge Qt → `0xc0000139`; remedy = build a venv | `anaconda3\Library\bin\Qt6Core.dll` |
| M-03 | MEDIUM | test coverage | Five of the six "untested" dialogs are non-modal and already `QTest`-driveable | `src/gui/main_window.py:549-667` |
| M-04 | MEDIUM | science | SPB acoustic model contradicts the published SiGe Lorenz number by −35 %; unresolved | `src/domain/spb.py` vs `tests/experimental_benchmarks/raw/sige_si80ge20p1_curves.csv` |
| M-05 | MEDIUM | release | No `LICENSE`, no `CITATION.cff`, 12 author-controlled metadata items outstanding | `docs/softwarex/author_controlled_information.md` |
| M-06 | LOW | benchmarks | Measurement direction and scattering assumptions are absent from the source and cannot be asserted | `tests/experimental_benchmarks/references/*.md` |
| M-07 | LOW | reproducibility | `requirements.txt` unpinned; declared Python floor 3.9 never exercised | `requirements.txt`, `setup.py:72` |
| M-08 | LOW | CI | `.github/workflows/tests.yml` has never executed | `.github/workflows/tests.yml` |

---

## 9. Verification commands used in this audit

```powershell
cd C:\Users\Elkady\Documents\seebeck_new\Seebeck-Prime
$env:PYTHONDONTWRITEBYTECODE='1'

# totals
C:\Users\Elkady\anaconda3\python.exe -m pytest -q -p no:cacheprovider --tb=no -rs
#   → 592 passed, 6 skipped

# per-directory
C:\Users\Elkady\anaconda3\python.exe -m pytest tests\scientific            -q -p no:cacheprovider   # 141 passed
C:\Users\Elkady\anaconda3\python.exe -m pytest tests\experimental_benchmarks -q -p no:cacheprovider   # 109 passed, 5 skipped
C:\Users\Elkady\anaconda3\python.exe -m pytest tests --ignore=tests\scientific --ignore=tests\experimental_benchmarks -q -p no:cacheprovider   # 342 passed, 1 skipped

# GUI subset (Qt-capable venv)
C:\Users\Elkady\AppData\Local\Temp\opencode\seebeck-gui\Scripts\python.exe -m pytest `
    tests\experimental_benchmarks\test_gui_end_to_end.py tests\test_startup_smoke.py -q -p no:cacheprovider
#   → 7 passed

# collection inventory
C:\Users\Elkady\anaconda3\python.exe -m pytest --collect-only -q -p no:cacheprovider tests
#   → 597 collected

# Qt root-cause probes
C:\Users\Elkady\anaconda3\python.exe -c "import ctypes; ctypes.CDLL('Qt6Core.dll'); print('conda Qt resolves')"
C:\Users\Elkady\anaconda3\python.exe -c "import PyQt6.QtWidgets"   # → ImportError 0xc0000139
C:\Users\Elkady\AppData\Local\Temp\opencode\seebeck-gui\Scripts\python.exe -c "import PyQt6.QtWidgets"   # → OK
```

---

## 10. Audit conclusion

The **calculation engine is in good shape**: the SPB conventions were
re-derived from scratch in this audit and the implementation is correct; the
core transport relations, the unit handling and the uncertainty propagators
are covered by independent references; the published-measurement evidence is
traceable to DOI level with a documented internal-consistency screen.

Three things stand between the current tree and a defensible SoftwareX
submission, and none of them is a scientific-equation defect:

1. **A physics diagnostic that never reaches the user** (D-01) — the
   application computes a physically impossible lattice thermal conductivity
   and presents it as a normal result.
2. **A documentation and packaging layer that contradicts itself** (D-02,
   D-03, D-04, D-05, D-06, D-07, D-08) — wrong units in provenance cards,
   two version numbers, an unchosen licence that is nonetheless advertised, a
   placeholder URL and a machine-specific path in the build config.
3. **A release gate that has never been run** — no `LICENSE`, no
   `CITATION.cff`, unpinned dependencies, an unexercised CI matrix and a
   conda environment in which the application cannot start.

The two largest *opportunities* — GUI coverage and the raw measurement chain —
are both more tractable than the previous report suggested: five of the six
dialogs are already non-modal, and the measurement chain is a genuinely new
module that can be built and tested against independent references before any
GUI integration.
