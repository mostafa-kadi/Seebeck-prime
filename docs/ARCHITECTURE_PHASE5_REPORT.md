# Architecture Migration — Phase 5 Report (Complete Verification)

**Status:** COMPLETE — the full scientific + application + GUI verification
required by map step 5 passed in both environments, and the static checks are
at their documented baselines. The migration programme's code work is
therefore verified end-to-end.
**Scope:** map step 5 of `docs/ARCHITECTURE_PHASE2_MIGRATION_MAP.md`
("Full scientific + application + GUI suites, both environments — stop
condition: report").
**Rollback:** local backups at
`C:\Users\Elkady\Documents\seebeck_new\Seebeck-Prime_backup_2026-11-13.zip`
and `Seebeck-Prime_history_2026-11-13.bundle`; nothing has been committed.

---

## 1. Test suites (fresh runs, both environments)

| Suite | Command | Result |
|-------|---------|--------|
| Primary (conda) | `anaconda3\python.exe -m pytest -q` | **738 passed / 10 skipped, exit 0** (16.9 s) |
| GUI-capable (Qt venv `seebeck-gui2`) | `seebeck-gui2\Scripts\python.exe -m pytest -q` | **745 passed / 6 skipped, exit 0** (22.4 s) |
| Benchmark suite | `pytest tests/experimental_benchmarks -q` | **119 passed / 7 skipped, exit 0** (13.4 s) |

- Identical to the Phase 4 closing numbers (no source changed since), now
  re-run from clean as the final gate.
- Skip counts are unchanged from the documented baselines
  (`docs/CODE_PROBLEMS_REGISTER.md` §7: 10 skips in the primary env with
  documented reasons; 6 in the Qt env).

## 2. What the suites cover (why this constitutes "scientific + application + GUI")

- **Scientific:** the conversion matrix (`tests/scientific/…` — every
  supported unit, round trips, retired-inline-factor equivalence, golden
  batch/κ/ZT values), independent-reference tests, physical-constraint tests,
  SPB/Hall/LFA use cases.
- **Application:** batch workflows, file services, table schema, import-root
  integrity (including the two Phase 4 guard tests).
- **GUI:** the Qt env runs the PyQt6-dependent tests; the benchmark suite
  drives the **real main window** headlessly through
  `gui_workflow_driver.py` (window constructed with the real composition
  root, published benchmark dataset loaded through the application's own
  file service); `tests/test_startup_smoke.py` imports the actual
  `main.py` composition root in the Qt env (conda skips it with the
  documented Qt-DLL reason) and verifies the no-side-effect-at-import rule.
- **Architecture:** `test_architecture_dependencies.py` +
  `test_import_root.py` + `test_canonical_calculations_surface.py` =
  **35 tests, all passing** — including the Phase 4 whole-tree ban on
  `seebeck_prime.legacy`.

## 3. Static checks vs the code-review baseline

Reproduction commands are exactly those recorded in
`docs/CODE_PROBLEMS_REGISTER.md` §11 (tool versions unchanged: ruff 0.15.20,
mypy 2.3.1).

| Check | Register baseline | Now | Verdict |
|-------|-------------------|-----|---------|
| `compileall -q src main.py` | 0 syntax errors | **0 (exit 0)** | no regression |
| `mypy src --ignore-missing-imports --show-error-codes` | 9 errors / 3 files (CR-14) | **9 errors / 3 files** (`domain/spb.py` runtime-guarded unions ×6, `application/data_mapping.py:72` annotation ×1, `application/measurement_processing.py` ×2) | **exactly at baseline** |
| `ruff check src --select S` | 2 (`try/except pass`) | **2 (`S110` ×2)** | **exactly at baseline** |
| `ruff check src --select E,F,W,B,SIM,C4,PIE,RUF,PL` | 481 diagnostics (style) | **499 diagnostics (style)** | style-only drift, attributed below |

**Style-drift attribution (+18 net on 15 fewer files):** the two
unit-converter files (`src/domain/units.py`,
`src/application/unit_conversion.py`) — where the Phase 3/C+ vocabulary was
documented — carry **37 diagnostics, 27 of them `RUF002`
ambiguous-unicode-docstring** from the deliberate scientific spellings
(`µV`, `Ω·cm`, `m²/s`, `³`) in the new docstrings. That is exactly the
register's documented "intentional scientific notation" class (S4).
`E501` moved 165 → 163. No defect-class rule grew; the security-class `S`
count is unchanged.

**Mypy invocation note (environment, not code):** a bare `mypy src` reports
142 noisy `import-untyped` errors because mypy cannot follow the editable
install's path injection for `seebeck_prime.*` (and, without site-packages,
216 `import-not-found` errors because mypy names the flat-src modules
`domain.*`, not `seebeck_prime.domain.*`). The register's documented command
(with `--ignore-missing-imports`) is the correct invocation and reproduces
the clean 9/3 baseline. Nothing in the migration changed type behaviour.

## 4. Environment observations (release-queue relevance)

- `pip list` shows **`seebeck-prime 0.1.0` installed editable**, resolving
  live to `src\seebeck_prime\__init__.py` — verified **not** a stale copy
  (imports resolve to the working tree, and `test_import_root.py` proves the
  shim identity in both environments). Relevant to release items D-05/D-06
  (packaging): a clean-venv install test remains queued there.
- The Qt venv (`%TEMP%\opencode\seebeck-gui2`, PyQt6 6.9.1) was alive for all
  Phase 5 runs; conda PyQt6 6.11.0 remains broken (ENV-01, unchanged).

## 5. Conclusion

Map steps 1–5 are executed and verified: the legacy tree is gone, every layer
satisfies the tightened dependency rules, packaging discovery is correct, and
both environments plus the benchmark suite are green with the static checks
at their baselines.

**Next:** Phase 6 — documentation refresh (`docs/ARCHITECTURE.md`,
`docs/CODE_SKELETON.md`, `docs/CODE_PROBLEMS_REGISTER.md` incl. CR-08
resolution) and the final architecture diagram.
