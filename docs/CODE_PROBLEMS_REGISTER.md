# Seebeck-Prime — Code Review: Problem Register

**Type:** Full static + runtime code review of the Python source tree.
**Date:** 2026-11-12
**Scope:** all 83 Python files — 75 in `src/`, 7 in `tools/`, 1 in `scripts/`
(~8,250 non-blank/non-comment LOC in `src`)
**Commit:** `326e929` (working tree: 247 modified/untracked files, uncommitted)
**Method:** `compileall`, **ruff 0.15.20**, **mypy 2.3.1**, a purpose-built AST
defect scanner, targeted runtime probes, and re-execution of the full test
suite in both environments.

> **Post-review status (2026-11-13).** This register records the review of
> commit `326e929` as inspected on 2026-11-12; the counts and file lists below
> are historical. Since then the architecture migration (Phases 3–5) completed:
> the whole `src/legacy/` tree (25 files / 2,499 LOC) was **deleted** and the
> 9 dialogs moved to `src/presentation/dialogs/`, so `src/` now holds
> **60 modules / 8,359 non-blank LOC** across 6 layer packages. The suite grew
> accordingly: conda **738 passed / 10 skipped**, Qt **745 / 6**, benchmarks
> **119 / 7** (all exit 0). **CR-08 is resolved** (see its section for the
> resolution record); CR-01/CR-02 remain fixed as noted inline. All other open
> items (CR-03…CR-07, CR-09…CR-14, ENV-01…ENV-06) still apply to the current
> tree and remain open.

---

## 1. Executive summary

| Metric | Result |
|---|---|
| Syntax errors (`compileall`) | **0** |
| Test suite, primary conda env | **680 passed, 10 skipped** (21.7 s) → **684 / 10** after the CR-01/CR-02 fix |
| Test suite, Qt-capable env | **687 passed, 6 skipped** (25.1 s) → **691 / 6** after the fix |
| Ruff diagnostics (E,F,W,B,SIM,C4,PIE,RUF,PL) | **481** (mostly style) |
| Ruff security rules (S) | **2** (`try/except/pass`) |
| Mypy | **10 errors in 4 files** (checked 75 files) → **9 errors in 3 files** after the fix |
| AST scan findings | **314**, of which ~6 categories are substantive |

**Verdict:** the numerical core is in good shape — no new scientific
discrepancy was found by this review, and the suite is green. The problems are
concentrated in **robustness, dead code, GUI architecture and release
hygiene**, not in the transport equations. One genuine API-level crash and one
data-correctness inconsistency were found and reproduced (`CR-01`, `CR-02`).

### Severity counts

| Severity | Meaning | Count |
|---|---|---|
| **S1** | Crash / silently wrong result on a legal public call | **2 — both FIXED (see §2)** |
| **S2** | Major robustness / architecture / invisible failure | **6** |
| **S3** | Maintainability: complexity, dead code, import hygiene | **6 groups** |
| **S4** | Style / lint noise | **~430** |
| **ENV** | Environment & release blockers (not code logic) | **6** |

> **Changes since first publication of this register (2026-11-12, same day):**
> `CR-01` and `CR-02` have been **fixed** in `src/domain/calculations.py`, with
> regression tests. No other finding has been addressed. Post-fix evidence:
> **684 passed, 10 skipped** (conda env) and **691 passed, 6 skipped**
> (rebuilt Qt env); ruff and mypy clean on the changed module.

---

## 2. S1 — Verified behavioural defects (both fixed)

### CR-01 · `calculate_zt` crashes on mixed scalar/array inputs

- **File:** `src/domain/calculations.py:125-129`
- **Type:** `TypeError` at runtime
- **Evidence (reproduced):**

```
calculate_zt(1.0, 300.0, np.array([1.0, 2.0]))
-> TypeError: 'float' object is not subscriptable
```

- **Cause:** the array branch indexes `pf[mask]` and `temperature[mask]` but
  only `kappa_total` is checked for being an array. The documented signature
  (`float | np.ndarray` for *each* argument) explicitly permits the crashing
  combination.
- **Impact:** any caller mixing a scalar with a vector crashes. The GUI is
  believed to pass consistent shapes, which is why tests never caught it — the
  mixed-shape case is **untested**.
- **Fix direction:** `np.broadcast_arrays` / `np.asarray` all three inputs
  before the mask.
- **Status: FIXED (2026-11-12).** The function now performs its arithmetic on
  the original operands (broadcasting scalars/vectors) and applies an explicit
  zero mask afterwards; no input is indexed. Verified:
  `calculate_zt(1.0, 300.0, np.array([1.0, 2.0])) -> [300.0, 150.0]`.
  Regression tests: `tests/test_calculations.py::test_calculate_zt_mixed_scalar_and_array`
  and `::test_calculate_zt_series_mixed_with_scalar`.

### CR-02 · `calculate_zt` zero-handling is inconsistent and contradicts its docstring

- **File:** `src/domain/calculations.py:104-137`
- **Docstring:** *"Division-by-zero is handled: ZT = 0 wherever κtotal = 0."*
- **Actual (reproduced):**

| Input type | κ = 0 result |
|---|---|
| `np.ndarray` | `0.0` (correct) |
| Python scalar | `0.0` (correct) |
| **`pandas.Series`** | **`inf`** (docstring violated) |

```
calculate_zt(pd.Series([1.0,1.0]), pd.Series([300.0,300.0]), pd.Series([1.0,0.0]))
-> [300.0, inf]
```

- **Impact:** `inf` propagates into exported tables, plots and downstream
  statistics. Same public function, three behaviours.
- **Fix direction:** convert to NumPy at entry (single code path), or apply the
  mask for Series.
- **Status: FIXED (2026-11-12).** Zero entries in `kappa_total` are now masked
  to `0.0` for every container. Verified:
  `calculate_zt(pd.Series([1.0,1.0]), pd.Series([300.0,300.0]), pd.Series([1.0,0.0])).tolist() -> [300.0, 0.0]`.
  pandas index alignment is preserved (the mask is built from the Series, not
  from a positional ndarray). Regression tests:
  `tests/test_calculations.py::test_calculate_zt_series_zero_kappa_is_zero`
  and `::test_calculate_zt_series_nan_kappa_stays_nan`.

---

## 3. S2 — Major robustness / architecture findings

### CR-03 · GUI errors are reported with `print()` — invisible to the user

- **Files:** `src/gui/main_window.py:673`, `:695`, `:717` (+2 more; 5 total in `src/gui`)
- **Pattern:** `except Exception as e: print(f"Error auto-populating ...: {e}")`
- **Impact:** in a windowed/packaged application there is no console; failed
  auto-population is silent, the dialog opens empty and the user cannot tell
  why. Failures are undiagnosable.
- **Fix direction:** `logging` + a non-blocking UI notice.

### CR-04 · Bare `except: pass` swallows all exceptions

- **File:** `src/presentation/plot_window.py:297`
- **Code:** axis-limit parsing wrapped in `except: pass`
- **Impact:** catches `KeyboardInterrupt`/`SystemExit` too; invalid axis input
  is silently ignored instead of reported. (Flagged by ruff **S110/E722**.)

### CR-05 · Swallowed exceptions (12 sites) — mixed severity

| File:line | Assessment |
|---|---|
| `src/presentation/plot_window.py:297` | **Problem** (see CR-04) |
| `src/presentation/kappa_logic.py:139,185,228,296` | **Problem** — user input parse failures disappear silently |
| `src/presentation/table_widget.py:112` | **Problem** — silent failure on cell handling |
| `src/presentation/table_handler.py:240` | **Problem** — silent failure |
| `src/application/use_cases.py:72` | **Acceptable** — `except KeyError: continue`, documented rationale |
| `src/presentation/dialogs/{device_efficiency,hall_mobility,spb,weighted_mobility}_dialog.py` | **Borderline** — deliberate UI guards, but unlogged |

### CR-06 · `zip()` without `strict=` (12 sites) — silent truncation risk

- **Files:** `application/spb_batch.py:38,79`; `presentation/kappa_logic.py:338,368`;
  `presentation/dialogs/device_efficiency_dialog.py:204`, `hall_mobility_dialog.py:377`,
  `kappa_dialog.py:469,470,472,473`, `weighted_mobility_dialog.py:147,172`
- **Impact:** unequal-length inputs are silently truncated (e.g. a batch result
  list shorter than the sample list is paired with the wrong samples).
- **Fix:** `strict=True` (or explicit length validation).

### CR-07 · Dead code: 64 unused imports (22 in one file)

- `src/gui/main_window.py` **×22**, `presentation/table_handler.py` ×8,
  `presentation/plot_window.py` ×7, `presentation/dialogs/plot_settings_dialog.py` ×4, others ×1–2.
- **Impact:** signal of organic drift/dead code; slows review; risks importing
  broken optional dependencies at startup.
- **Fix:** ruff `--fix` (all 64 are auto-fixable).

### CR-08 · The "legacy" layer is actually the production GUI — **RESOLVED 2026-11-13**

**Resolution (Phase 3 Step C + Phase 4, 2026-11-13):** the "migrate to
`presentation/` and delete" option was executed. The 9 dialogs moved to
`src/presentation/dialogs/` in Phase 3 (Step C+, including the 4 new quantity
kinds and the `spb_dialog` convention fix); `gui/main_window.py:32-54` now
imports them from `seebeck_prime.presentation.dialogs.*`; the whole
`src/legacy/` tree (25 files / 2,499 LOC) was deleted in Phase 4 together with
its compatibility test. Two guard tests prevent reintroduction:
`test_no_package_imports_the_retired_legacy_tree` (whole-`src/` scan) and
`test_the_retired_legacy_tree_is_no_longer_importable`. Verified by the Phase 5
full suites (738 / 745 / 119 passed, all exit 0). The text below is retained as
the historical review record.

- **File:** `src/gui/main_window.py:32-38,53` imports **7 dialogs** from
  `seebeck_prime.legacy.ui.dialogs` (`KappaToolDialog`, `MultiSampleDialog`,
  `WeightedMobilityDialog`, `HallMobilityDialog`, `SPBModelingDialog`,
  `DeviceEfficiencyDialog`, `ErrorBarDialog`).
- **Reality:** `src/legacy/` holds 25 files / 2,499 LOC that are **live**, are
  labelled "legacy", have **no automated GUI coverage**, and duplicate patterns
  already re-implemented in `src/presentation/`.
- **Impact:** ambiguous ownership; a reader cannot tell what is deprecated;
  double-maintenance risk; security/quality fixes must be applied twice.
- **Fix direction:** either rename (`ui/dialogs/`) and test them, or migrate to
  `presentation/` and delete. This is the single largest architectural problem.

---

## 4. S3 — Maintainability

| ID | Problem | Evidence |
|---|---|---|
| CR-09 | **21 functions > 80 lines**; worst: `main_window.recalculate_all_properties` **214 lines** (72 statements), `spb_dialog.init_ui` 220, `hall_mobility_dialog.init_ui` 183, `kappa_dialog.init_ui` 144, `plot_custom_layout` 141, `error_bar_dialog.init_ui` 134 | AST scan |
| CR-10 | **Oversized interfaces:** `ThermoelectricAnalyzer.__init__` **13 parameters** (`src/application/services.py:53`; ruff PLR0913 counts 12, excluding `self`), `calculate_thermoelectric_properties` 9 args, 8 more functions with 6 args | ruff PLR0913 |
| CR-11 | **9 imports inside functions** — including `domain/spb.py:67` and `domain/analysis.py:69`; hides dependencies and can mask circular imports | ruff PLC0415 |
| CR-12 | **3 wildcard imports** (`plugins/{electronic,hall,phonon}.py:3` `from ... import *`) — namespace pollution, silent shadowing | AST scan |
| CR-13 | **32 `except Exception` handlers.** Many are legitimate (wrap-and-re-raise, e.g. `application/services.py:93`), but 6 in `main_window`, 10 in legacy dialogs and 2 in `domain/spb.py` deserve individual review | AST scan |
| CR-14 | **Mypy: 10 errors / 4 files** at review time. After the CR-01 fix: **9 errors / 3 files** — all scalar-vs-array union warnings guarded at runtime by `np.ndim()` checks (`domain/spb.py`) plus 1 missing annotation (`application/data_mapping.py:72`). No other type errors in 75 files. | mypy 2.3.1 |

---

## 5. S4 — Style / lint noise (not defects)

| Rule | Count | Note |
|---|---|---|
| E501 line-too-long | 165 | formatting only |
| RUF002/RUF003/RUF001 ambiguous unicode | 106 | `×`, `µ`, `⁻²` in docstrings — intentional scientific notation |
| PLR2004 magic value | 35 | mostly physical constants in tests/fixtures |
| RUF022 unsorted `__all__` | 7 | cosmetic |
| SIM108 ternary | 6 | cosmetic |
| E741 ambiguous name `l` | 4 | `plot_window.py:244,303,310,591` |
| C408 `dict()` call | 2 | cosmetic |
| F841 unused variable | 2 | dead locals |
| RUF100 unused noqa | 3 | stale suppressions |
| W293 whitespace | 2 | cosmetic |
| E402 module import not at top | 2 | deliberate (`scripts/`) |

**`print()` count:** 224 total, but **217 are in `tools/`/`scripts/`** (CLI
programs — expected). Only **6 are in `src/`** (5 GUI, 1 presentation) — these
are CR-03.

---

## 6. ENV — Environment & release blockers (not code logic)

| ID | Problem | Evidence |
|---|---|---|
| ENV-01 | **PyQt6 6.11.0 in the conda base env is broken** (DLL load failure `0xc0000139`) — the GUI does not start there | documented in task log |
| ENV-02 | The only working GUI environment is a **temporary venv** under `%TEMP%\opencode\seebeck-gui` — volatile; OS cleanup **did delete its interpreter on 2026-11-12**, breaking GUI testing. It was rebuilt as `%TEMP%\opencode\seebeck-gui2` (PyQt6 6.9.1, `--system-site-packages`), which is equally volatile | reproduced this session |
| ENV-03 | `python` on PATH resolves to **C:\Python314 without project dependencies** (no pytest); conda must be called explicitly | reproduced this session |
| ENV-04 | **CI workflow never executed** (M-08) — **partially addressed 2026-11-13:** the workflow now includes a static job (ruff S-rules gate, mypy baseline gate, CR-07/ENV-04); execution still requires the repository push | `.github/workflows/tests.yml` |
| ENV-05 | **Version control hygiene:** 247 changed/untracked files, single commit `326e929`; all Phase 3–6 and release work is uncommitted | `git status` |
| ~~ENV-06~~ | **RESOLVED 2026-11-13 (release):** version reconciled to 0.1.0 everywhere (CHANGELOG, `setup.py`, `__version__`); MIT licence files added (`LICENSE` + `Licence.txt`); placeholder repository URL replaced; machine-specific `[tool.pyrefly]` path removed from `pyproject.toml` (D-03/D-04/D-05/D-06) — see `RELEASE_READINESS.md` | verified |

---

## 7. Test-coverage gaps (known)

- No automated GUI coverage for: error-bar, kappa, SPB, Hall, weighted-mobility,
  multi-sample dialogs, modal behaviour, clipboard paste, menus, plot export.
- 10 skipped tests in the primary env (documented reasons: source papers
  publishing no PF/ZT; GUI-dependent tests).
- ~~The two `calculate_zt` defects above are **not covered by any test**~~ —
  **closed 2026-11-12:** four regression tests now cover mixed scalar/array
  inputs, Series-with-zero, Series/scalar mix, and Series NaN κ
  (`tests/test_calculations.py`).

## 8. Functional gaps already recorded in the validation programme

Not new findings; listed for completeness (see `validation/`):
raw V/I → R → ρ → σ chain (E-58), covariance-aware propagation, Kane/Dingle/
multiband Lorenz models, weighted-mobility physical validation (D-12), PbTe
comparison (unverified). These are **documented capability boundaries**, not
code defects.

## 9. Deliberately excluded (verified not to be problems)

- **Duplicate `__init__`/`init_ui` in `plot_window.py`** — false positive: two
  different classes (`PlotWindow`, `TraceStyleDialog`).
- **`services.py:93` broad except** — wraps and re-raises with context; correct.
- **`use_cases.py:72` swallowed `KeyError`** — deliberate, documented.
- **`spb.py` mypy union errors** — runtime-guarded by `np.ndim()` checks;
  a typing limitation, not a bug.
- **Lorenz constant 2.44e-8 vs exact 2.443004509e-8** — documented 0.12 %
  rounding decision (D-11/SE-015), not a defect.
- **`error_bar_dialog.py:264-279` relative-error `/100.0` (4 sites)** —
  percent-to-fraction arithmetic on user-entered relative uncertainties (%),
  **not** a measurement-unit conversion. Left inline by decision (2026-11-13,
  Phase 3 Step C+ review): routing it through the unit-converter vocabulary
  would misrepresent its semantics. Revisit only if a dedicated
  relative-uncertainty workflow is added.

## 10. Remediation priority

| Priority | Item | Effort |
|---|---|---|
| 1 | ~~Fix `calculate_zt` (CR-01 + CR-02); add mixed-input and Series tests~~ — **DONE 2026-11-12** | S |
| 2 | Replace GUI `print()` with logging + UI notice (CR-03) | S |
| 3 | `zip(..., strict=True)` or explicit length checks (CR-06) | S |
| 4 | Fix `except: pass` sites with specific exceptions + logging (CR-04/05) | S |
| 5 | `ruff --fix` unused imports; add ruff+mypy to CI (CR-07, ENV-04) — **CI static job authored 2026-11-13; execution pending push** | S |
| 6 | ~~Decide the legacy layer: rename+test or migrate (CR-08)~~ — **DONE 2026-11-13** (migrated to `presentation/dialogs/` + legacy tree deleted, Phase 3/4) | L |
| 7 | Split `recalculate_all_properties` and the `init_ui` giants (CR-09) | M |
| 8 | Introduce a settings/dataclass object for the 13-arg constructor (CR-10) | M |
| 9 | Release hygiene: version, licence, commit, CI, packaging (ENV-05/06) — **version/licence/packaging DONE 2026-11-13** (`RELEASE_READINESS.md`); commit + CI execution pending approval | M |

## 11. Reproduction commands

```powershell
# tests (primary env)
& C:\Users\Elkady\anaconda3\python.exe -m pytest -q

# lint / types
& C:\Users\Elkady\anaconda3\python.exe -m ruff check src --select E,F,W,B,SIM,C4,PIE,RUF,PL
& C:\Users\Elkady\anaconda3\python.exe -m ruff check src --select S
& C:\Users\Elkady\anaconda3\python.exe -m mypy src --ignore-missing-imports --show-error-codes

# the two defects, post-fix (both now succeed)
$env:PYTHONPATH="src"
& C:\Users\Elkady\anaconda3\python.exe -c "import numpy as np; from seebeck_prime.domain.calculations import calculate_zt; print(calculate_zt(1.0, 300.0, np.array([1.0,2.0])))"
& C:\Users\Elkady\anaconda3\python.exe -c "import pandas as pd; from seebeck_prime.domain.calculations import calculate_zt; print(calculate_zt(pd.Series([1.0,1.0]), pd.Series([300.0,300.0]), pd.Series([1.0,0.0])).tolist())"

# regression tests for CR-01 / CR-02
& C:\Users\Elkady\anaconda3\python.exe -m pytest tests/test_calculations.py -q -k calculate_zt
```

---

*End of code-problem register.*
