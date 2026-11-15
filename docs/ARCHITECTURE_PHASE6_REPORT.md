# Architecture Migration — Phase 6 Report

**Status:** COMPLETE — documentation refreshed to the as-built state, the final
architecture diagram recorded, CR-08 closed in the problem register, and the
D-01 line-reference drift corrected. All suites green.
**Authorization:** User approved Phase 6 ("continue") after the Phase 5 report
(map row 26 of `docs/ARCHITECTURE_PHASE2_MIGRATION_MAP.md` — documentation
refresh and final as-built diagram).
**Rollback:** local backups at
`C:\Users\Elkady\Documents\seebeck_new\Seebeck-Prime_backup_2026-11-13.zip`
(working tree) and `Seebeck-Prime_history_2026-11-13.bundle` (git history);
nothing has been committed.

---

## 1. What was executed

Phase 6 changed **documentation only** — no source file, no test file, no
validation-record status/category/count.

| File | Work | Result |
|------|------|--------|
| `docs/CODE_SKELETON.md` | Re-measured against the live tree and rewritten: header (60 modules / 8,359 LOC, post-migration revision note), §1 diagram (gui-only composition root; `dialogs/ ×9`), §1.1 dependency table (new edge counts, legacy rows removed, "no deviations" reading), §2 domain (13 modules / 2,012 LOC; `physical_constants` constants list incl. `DEFAULT_LORENZ` / `SOMMERFELD_LORENZ_EXACT` / `LEGACY_DEFAULT_LORENZ`; `units.py` full 34-function vocabulary), §3 application (11 / 1,262; `unit_conversion.py` `QuantityKind` 13 kinds + vectorised batch + dialog wrappers; Lorenz re-export note in `use_cases`), §4 presentation (23 / 4,192; 9-dialog listing with roles), §5 gui (title, `reset_and_create_new_sheet` typo fix, `gui/table.py` documented as the test-enforced re-export shim, `__init__.py` marker), §5.2 legacy section replaced by the retired-package record (with both guard tests), §6 layer table (new counts; port direction corrected: application *defines* `TabularDataStore`, infrastructure implements it structurally with 0 internal imports), §7 layout tree (no legacy), §8 enforcement (25 + 7 tests, full rule→test table, "no sanctioned exceptions remain") | DONE |
| `docs/ARCHITECTURE.md` | Header (version 1.1.0, "as-built" status, 2026-11-13); §2 rewritten as-built (§2.1 tree: 6 layer packages + shim, measured module/LOC counts, `dialogs/` enumerated; §2.2: 25+7 enforcement tests, presentation consolidation complete, Lorenz unified, Phase 5 verification numbers 738/745/119 + 35 + mypy/ruff baselines); §3 rewritten "As-Built Architecture (final diagram)" (mermaid: `main.py → gui → presentation → application → domain`, infrastructure dashed implements-port arrow, plugins re-export arrow); new §3.1 as-built components; new §3.2 "Remaining Target Components (not yet implemented)" — Central Data Registry, Dependency-Aware Calculation Engine, standalone visualization package; §6.1 updated with the completed consolidation/conversion/composition-root achievements; §6.2 reduced to the two genuinely remaining target items | DONE |
| `docs/CODE_PROBLEMS_REGISTER.md` | Post-review status addendum after the header (tree now 60 modules / 8,359 LOC; legacy deleted; suites 738/745/119; CR-08 resolved; remaining items still open); **CR-08 section marked RESOLVED 2026-11-13** with a resolution record (original review text retained verbatim as the historical record); §10 priority row 6 struck through as DONE | DONE |
| `validation/remediation/VALIDATION_STATUS.md` | **D-01 line reference corrected**: `main_window.py:291-301` → `:363-368` (the κ_L write moved when the dialog imports changed in Phase 3). Same correction applied to the E-56 row: `ErrorBarDialog` `main_window.py:225` → `:292`, `PlotDataDialog` `:688` → `:779`. Prose only — no status, category, or count changed | DONE |

## 2. Measured facts recorded in the refreshed documents

All numbers below were measured 2026-11-13 (AST-based LOC counting of
non-blank/non-comment lines; import edges resolved per import statement):

| Layer | Modules | LOC | Import edges out |
|---|---:|---:|---|
| domain | 13 | 2,012 | 0 internal |
| application | 11 | 1,262 | → domain 17 |
| presentation (incl. `dialogs/` ×10 files) | 23 | 4,192 | → application 27 |
| gui | 4 | 652 | → presentation 17, → application 4 |
| infrastructure | 2 | 84 | 0 |
| plugins | 6 | 136 | → domain 9 (re-exports) |
| import shim (`seebeck_prime/__init__.py`) | 1 | 21 | — |
| **total** | **60** | **8,359** | **no legacy edges; graph acyclic** |

`presentation/dialogs/` holds 9 dialogs (2,165 LOC incl. `__init__.py`):
`KappaToolDialog`, `SPBModelingDialog`, `HallMobilityDialog`,
`WeightedMobilityDialog`, `DeviceEfficiencyDialog`, `ErrorBarDialog`,
`MultiSampleDialog`, `PlotSettingsDialog`, `ProcessedDataDialog`.

Line-number truth table (used for the VALIDATION_STATUS correction):
κ_L table write `src/gui/main_window.py:363-368`; `ErrorBarDialog(...)` at
`:292`; `PlotDataDialog(...)` at `:779`.

## 3. Documents deliberately NOT changed

These are dated snapshot records whose value depends on remaining unchanged
(the same principle the Phase 3 findings register states for the Phase 1
audit):

- `docs/ARCHITECTURE_PHASE1_AUDIT.md`, `docs/ARCHITECTURE_PHASE2_MIGRATION_MAP.md`
  (historical audit / migration plan; explicitly excluded by earlier phases),
- `validation/remediation/INITIAL_STATE_AUDIT.md`,
- `validation/remediation/PHASE3_FINDINGS.md` (records what Phase 3 found *at
  the time*; its `main_window.py:291-301` citation was correct then),
- `validation/SCIENTIFIC_CALCULATION_TEST_RESULTS.md` (dated 2026-11-12,
  version 1.0 — a point-in-time validation record),
- `docs/ARCHITECTURE_PHASE4_REPORT.md` / `docs/ARCHITECTURE_PHASE5_REPORT.md`
  (their references to the then-stale line numbers document the plan items
  that Phase 6 has now executed).

No doc-consistency test reads any of these files (verified by grep), so the
edits cannot affect the suites.

## 4. Verification

| Check | Result |
|---|---|
| `pytest tests/scientific/test_equation_status_mapping.py tests/test_architecture_dependencies.py tests/test_import_root.py tests/test_canonical_calculations_surface.py -q` | **50 passed** |
| Full conda suite `pytest -q` | **738 passed, 10 skipped** — identical to the Phase 5 baseline; `pytest` exit code **0** (the `0xc0000139` traces on stderr are the documented conda-PyQt6 6.11.0 DLL load failure behind the 10 documented skips, not failures) |
| Consistency greps | No stale counts (`8,259 / 1,773 / 1,105 / 2,004 / 637 / 75 files`) remain outside the explicitly historical revision notes; no `src/core|src/ui|src/plot|src.ui` layout references remain in the living architecture docs; remaining `main_window.py:` citations are in dated snapshot records only |

## 5. Architecture migration — final state

All rows of `docs/ARCHITECTURE_PHASE2_MIGRATION_MAP.md` are now executed.
The tree is the frozen target: **Domain ← Application ← Presentation ← GUI**
with `main.py` as the sole composition root, Infrastructure implementing the
`TabularDataStore` port structurally, `plugins/` re-exporting domain, the
retired legacy tree deleted and guarded, and the enforced inward rule holding
without exceptions. The documentation now states the same thing the tests
enforce and the tree contains.

## 6. Open items (next steps, pending user approval)

- **Release queue:** licence file (D-04), `CITATION.cff`, version
  reconciliation (D-03), packaging (D-05/D-06 incl. a clean-venv install
  check), README, `RELEASE_READINESS.md`, CI execution (M-08, ENV-04).
- **Open register items:** CR-03…CR-07, CR-09…CR-14 and ENV-01…ENV-06 (see
  `docs/CODE_PROBLEMS_REGISTER.md` §10).
- **Author-dependent manuscript inputs:** as listed in
  `MANUSCRIPT.tex` placeholders and the validation programme records.
