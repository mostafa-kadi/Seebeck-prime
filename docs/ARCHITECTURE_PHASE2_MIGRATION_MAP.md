# Seebeck-Prime — Phase 2: Migration Map

**Date:** 2026-11-13
**Basis:** `docs/ARCHITECTURE_PHASE1_AUDIT.md` (measured).
**Target architecture:** Layered Modular Monolith (agreed, frozen).
**Rule for this programme:** incremental; no rewrite; no scientific change;
tests never weakened; nothing deleted while a dependent exists.

---

## 1. Migration map — legacy tree (`src/legacy/`, 25 files)

Legend for risk: **L** = mechanical (file move / import update),
**M** = needs equivalence verification,
**—** = deletion of a confirmed-orphan.

### 1.1 Live dialogs → Presentation layer

| # | Current file | Responsibility | Target layer | Target file | Dependencies (unchanged except path) | Tests required | Risk |
|---|---|---|---|---|---|---|---|
| 1 | `legacy/ui/dialogs/kappa_dialog.py` (394) | κ tool dialog: LFA data mapping, DP display, κ table/plot | Presentation | `src/presentation/dialogs/kappa_dialog.py` | `presentation.{table_widget,plot_window,plot_data_dialog,kappa_logic}`, `application.unit_conversion` | import smoke test; existing suite | L |
| 2 | `legacy/ui/dialogs/spb_dialog.py` (428) | SPB modelling dialog: batch table, Pisarenko/Lorenz plots | Presentation | `src/presentation/dialogs/spb_dialog.py` | `presentation.{table_widget,plot_window}`, `application.{models,unit_conversion,spb_batch}`, `domain.physical_constants` | import smoke test; existing suite | L |
| 3 | `legacy/ui/dialogs/hall_mobility_dialog.py` (399) | Hall mobility dialog: raw + table modes, mobility/n plots, λ fit | Presentation | `src/presentation/dialogs/hall_mobility_dialog.py` | `presentation.{table_widget,plot_window}`, `application.{models,unit_conversion}` | import smoke test; existing suite | L |
| 4 | `legacy/ui/dialogs/weighted_mobility_dialog.py` (139) | Weighted-mobility calculator dialog | Presentation | `src/presentation/dialogs/weighted_mobility_dialog.py` | `presentation.table_widget`, `application.use_cases` | import smoke test; existing suite | L |
| 5 | `legacy/ui/dialogs/device_efficiency_dialog.py` (173) | Device efficiency dialog (Γ-leg, ZT → η) | Presentation | `src/presentation/dialogs/device_efficiency_dialog.py` | `presentation.table_widget`, `application.use_cases` | import smoke test; existing suite | L |
| 6 | `legacy/ui/dialogs/multi_sample_dialog.py` (205) | Multi-sample batch dialog + Excel export | Presentation | `src/presentation/dialogs/multi_sample_dialog.py` | `presentation.{multi_sample_plots,validation_notices,plot_window}`, `application.{use_cases,data_mapping,table_files}`, **`plot_settings_dialog` (path update)** | import smoke test; existing suite | L |
| 7 | `legacy/ui/dialogs/error_bar_dialog.py` (230) | Uncertainty source file dialog (4-probe/LF/Seebeck) | Presentation | `src/presentation/dialogs/error_bar_dialog.py` | `application.services`, **`processed_data_dialog` (path update)** | import smoke test; existing suite | L |
| 8 | `legacy/ui/dialogs/plot_settings_dialog.py` (162) | Plot-style settings sub-dialog | Presentation | `src/presentation/dialogs/plot_settings_dialog.py` | `presentation.ui_utils` | import smoke test | L |
| 9 | `legacy/ui/dialogs/processed_data_dialog.py` (45) | Processed-data viewer sub-dialog | Presentation | `src/presentation/dialogs/processed_data_dialog.py` | (none internal) | import smoke test | L |

### 1.2 Orphan → delete

| # | Current file | Responsibility | Target | Tests required | Risk |
|---|---|---|---|---|---|
| 10 | `legacy/ui/dialogs/plot_options_dialog.py` (146) | unused plot-options dialog | **DELETE** (after zero-reference re-grep in Phase 3) | none (no test references it) | — |

### 1.3 Compatibility shims → delete (dependents updated first)

| # | Current file | Responsibility | Target | Depends on it (measured) | Action & tests | Risk |
|---|---|---|---|---|---|---|
| 11 | `legacy/ui/logic/unit_converter.py` (9) | shim → `presentation.unit_converter` | **DELETE** | `tests/test_unit_converter.py:4` | update test import to `presentation.unit_converter`; assertions unchanged | L |
| 12 | `legacy/ui/logic/kappa_logic.py` (10) | shim → `presentation.kappa_logic` | **DELETE** | none | delete | — |
| 13 | `legacy/ui/logic/table_handler.py` (49) | shim → `presentation.table_handler` | **DELETE** | none | delete | — |
| 14 | `legacy/ui/logic/ui_builder.py` (5) | shim → `presentation.ui_builder` | **DELETE** | none | delete | — |
| 15 | `legacy/ui/widgets/plot_window.py` (3) | shim → `presentation.plot_window` | **DELETE** | none | delete | — |
| 16 | `legacy/ui/widgets/table_widget.py` (3) | shim → `presentation.table_widget` | **DELETE** | none | delete | — |
| 17 | `legacy/core/calculations.py` (27) | shim → `domain.calculations` | **DELETE** | `tests/test_legacy_calculations_compatibility.py` | rewrite that test against `seebeck_prime.domain.calculations` (same assertions) **or** retire it with user approval — compatibility surface it guards no longer exists | L |
| 18 | `legacy/core/constants.py` (16) | legacy constants re-export | **DELETE** | `tests/test_legacy_calculations_compatibility.py` | same as #17 | L |
| 19 | `legacy/core/analyzer.py` (49) | adapter → `application.use_cases` + `presentation.multi_sample_plots` | **DELETE** | `tests/test_batch_workflows.py:12` | update test imports to `application.use_cases` / `presentation.multi_sample_plots`; assertions identical | L |
| 20 | `legacy/**/__init__.py` ×5, `legacy/__init__.py` | package markers | **DELETE whole `src/legacy/` tree** | (only rows above) | after 1–19 | — |

## 2. Migration map — non-legacy files touched by the programme

| # | Current file | Change | Target | Tests required | Risk |
|---|---|---|---|---|---|
| 21 | `src/gui/main_window.py:32-38,53` | 7 imports → `seebeck_prime.presentation.dialogs.*` | GUI | startup smoke test; full Qt suite | L |
| 22 | `src/gui/main_window.py:663-738` (G-2) | replace `*0.01` / `*1e6` with `application.unit_conversion` helpers (new small helpers in application if missing) | GUI (logic moves to Application) | existing suite; add equivalence assertions (values identical) | L |
| 23 | `src/presentation/kappa_logic.py:119-218` (G-3) | replace inline `×1000 / ×1e-6` with converter calls from `application.unit_conversion` (extend converter units for diffusivity/cp if absent) | Presentation (conversion moves to Application) | existing suite incl. golden batch values; **new numeric-equivalence test**; benchmark suite re-run | **M** |
| 24 | `tests/test_architecture_dependencies.py` (G-5) | forbid **every** `seebeck_prime.legacy` import from any layer; presentation.dialogs covered by presentation rule; gui rule tightened | Architecture tests | run the file | L |
| 25 | `setup.py` | verify package walk auto-includes `presentation.dialogs` (it walks nested packages — confirm, adjust only if needed) | packaging | `pip install -e .` smoke / import-root test | L |

## 3. Execution order (Phase 3, smallest independent first)

| Step | Content | Rows | Stop condition |
|---|---|---|---|
| 3a | Confirm-orphan greps; delete orphan + 5 unused shims (#10,12,13,14,15,16) | — | suite green |
| 3b | Move 9 dialogs to `src/presentation/dialogs/`; update 2 internal + 7 gui imports (#1–9, 21) | — | full suites green (conda + Qt) |
| 3c | G-2 gui conversion helpers (#22) | — | suite green, values identical |
| 3d | G-3 presentation conversion (#23) + equivalence test | — | suite + benchmark suite green |
| 3e | Update dependent tests (#11, 17, 19) | — | suite green |
| 4 | Delete `src/legacy/` entirely (#17–20 leftovers); tighten architecture tests (#24); packaging check (#25) | — | all 30+ architecture tests green |
| 5 | Full scientific + application + GUI suites, both environments | — | report |
| 6 | Update `docs/ARCHITECTURE.md`, `docs/CODE_SKELETON.md`, register; final diagram | — | report |

**Rollback at any step:** restore from
`Seebeck-Prime_backup_2026-11-13.zip` (working tree) and
`Seebeck-Prime_history_2026-11-13.bundle` (history). Nothing is committed
during the programme without explicit approval.

## 4. Explicit non-goals (per instruction)

- No microservices, no rewrite, no new frameworks.
- No change to equations, numerical methods, validation records, or the
  Lorenz-constant decisions.
- No feature removal — the 9 dialogs keep every behaviour; only their
  address changes.
- No remote services; all work local.
