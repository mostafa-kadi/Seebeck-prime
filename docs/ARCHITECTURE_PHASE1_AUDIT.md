# Seebeck-Prime — Phase 1: Architecture Audit

**Date:** 2026-11-13
**Target architecture (agreed, frozen):** Layered Modular Monolith.
**Scope of this phase:** audit only — no code changes.
**Backup taken before this programme:**
`C:\Users\Elkady\Documents\seebeck_new\Seebeck-Prime_backup_2026-11-13.zip`
(full working tree, 4.1 MB) and
`C:\Users\Elkady\Documents\seebeck_new\Seebeck-Prime_history_2026-11-13.bundle`
(git history, 2.26 MB).

**Method:** every import in `src/` resolved to a file (75 modules, 8,259 LOC);
per-module AST extraction of public symbols; targeted reads of every file
flagged by the scan; architecture/import-root test suite re-run
(30 passed). No claim below is from memory.

---

## 1. Conformance matrix — target rules vs measured reality

| # | Target requirement | Status | Evidence |
|---|---|---|---|
| A1 | Domain must not depend on Application, Presentation, GUI, Infrastructure | **COMPLIANT** | resolved import graph: `domain → (none)` — 0 internal edges; numpy/scipy only |
| A2 | Application depends on Domain and abstractions, not concrete GUI/storage | **COMPLIANT** | `application → domain` ×17; `application/ports.py` defines `TabularDataStore(Protocol)`; `ThermoelectricAnalyzer(..., data_store: TabularDataStore)`; no infrastructure import (test-enforced) |
| A3 | Presentation must not contain scientific calculation implementations | **MOSTLY COMPLIANT** — 1 gap (G-3) | all κ/LFA physics delegated to application use cases (`calculate_kappa_from_lfa_si_use_case`, `combine_relative_uncertainties_use_case`, `calculate_formula_mass_use_case`, `calculate_dulong_petit_limit_use_case`); **but 8 inline unit-conversion factors** in `presentation/kappa_logic.py:119-218` |
| A4 | GUI must orchestrate components rather than implement scientific logic | **MOSTLY COMPLIANT** — 1 gap (G-2) | `recalculate_all_properties` delegates to `calculate_thermoelectric_properties` + `ThermoelectricAnalyzer`; **but 6 inline conversion factors** in `gui/main_window.py:663,665,690,712,735,738` (`*0.01`, `*1e6`) |
| A5 | Infrastructure must implement the required persistence interfaces | **COMPLIANT** | `infrastructure/io.py::PandasTabularDataStore implements TabularDataStore`; no GUI imports; instantiated only in `main.py` |
| A6 | `main.py` is the composition root | **COMPLIANT** | `main.py:55-60` — the only place concrete adapters are constructed |
| A7 | All application dialogs live in Presentation | **NON-COMPLIANT** (G-1) | 7 production dialogs live in `legacy/ui/dialogs/` and are imported by `gui/main_window.py:32-38,53` |
| A8 | No duplicate implementations | **COMPLIANT** | suspected duplicate `get_robust_mapped_dataframe` in `presentation/table_handler.py:161` verified as a **delegation wrapper** to `application/data_mapping.py`, not a copy |

**Enforcement today:** `tests/test_architecture_dependencies.py` + `tests/test_import_root.py` (30 tests, re-run 2026-11-13: all pass). The gui rule currently permits `legacy.ui.dialogs` — the exact hole behind G-1.

---

## 2. Legacy inventory — "legacy" is NOT obsolete (measured)

Classified by *who imports it*, not by directory name.

### 2.1 Live production code (reached from the running application)

| Module | LOC | Reached via | Internal legacy imports | Science content |
|---|---:|---|---|---|
| `legacy/ui/dialogs/kappa_dialog.py` | 394 | `gui/main_window.py:32` | none | none — delegates to `presentation.kappa_logic`, `application.unit_conversion` |
| `legacy/ui/dialogs/spb_dialog.py` | 428 | `gui/main_window.py:37` | none | none — delegates to `application.spb_batch`, `models`, `unit_conversion`, `domain.physical_constants`; `np` used only for input arrays + plot grid |
| `legacy/ui/dialogs/hall_mobility_dialog.py` | 399 | `gui/main_window.py:36` | none | none — delegates to `application.models`, `unit_conversion`; `np` = arrays + plot grid |
| `legacy/ui/dialogs/weighted_mobility_dialog.py` | 139 | `gui/main_window.py:35` | none | none — delegates to `application.use_cases` |
| `legacy/ui/dialogs/device_efficiency_dialog.py` | 173 | `gui/main_window.py:38` | none | none — delegates to `application.use_cases` |
| `legacy/ui/dialogs/multi_sample_dialog.py` | 205 | `gui/main_window.py:33` | `plot_settings_dialog` | none — delegates to `application.use_cases`, `data_mapping`, `table_files` |
| `legacy/ui/dialogs/error_bar_dialog.py` | 230 | `gui/main_window.py:53` | `processed_data_dialog` | none — delegates to `application.services.ThermoelectricAnalyzer` |

**Verdict:** all seven dialogs are presentation-layer components that already
follow the target dependency direction. Their migration is a **file move +
import update**, not a rewrite.

### 2.2 Reached only from inside the legacy layer

| Module | Used by |
|---|---|
| `legacy/ui/dialogs/plot_settings_dialog.py` (162) | `multi_sample_dialog.py:25` |
| `legacy/ui/dialogs/processed_data_dialog.py` (45) | `error_bar_dialog.py:217` |

### 2.3 Orphaned (defined, referenced from nowhere)

| Module | Confirmation |
|---|---|
| `legacy/ui/dialogs/plot_options_dialog.py` (146) | grep of all `*.py`: only its own definition |

### 2.4 Pure compatibility shims (delegate inward; no science)

| Module | Delegates to | External importers |
|---|---|---|
| `legacy/core/calculations.py` (27) | `domain.calculations` | `tests/test_legacy_calculations_compatibility.py` |
| `legacy/core/constants.py` (16) | `domain.physical_constants` | same test |
| `legacy/core/analyzer.py` (49) | `application.use_cases` + `presentation.multi_sample_plots` | `tests/test_batch_workflows.py:12` |
| `legacy/ui/logic/kappa_logic.py` (10) | `presentation.kappa_logic` | **none** |
| `legacy/ui/logic/table_handler.py` (49) | `presentation.table_handler` | **none** |
| `legacy/ui/logic/ui_builder.py` (5) | `presentation.ui_builder` | **none** |
| `legacy/ui/logic/unit_converter.py` (9) | `presentation.unit_converter` | `tests/test_unit_converter.py:4` |
| `legacy/ui/widgets/plot_window.py` (3) | `presentation.plot_window` | **none** |
| `legacy/ui/widgets/table_widget.py` (3) | `presentation.table_widget` | **none** |

**Verdict:** the legacy *logic/widgets* migration announced in
`docs/CODE_SKELETON.md` already happened; what remains is 9 shims with 171 LOC
total, of which only 3 have any importer at all (all in `tests/`).

### 2.5 Everything else that mentions "legacy"

`setup.py` (packaging walk comment), `docs/*` and `manuscript/*` (narrative
text only), `tests/test_architecture_dependencies.py` (enforcement rules).
No further code dependency exists anywhere in the repository.

---

## 3. Gap list (what blocks full conformance)

| ID | Gap | Target rule violated | Evidence | Fix class |
|---|---|---|---|---|
| **G-1** | 7 production dialogs physically live in `legacy/ui/dialogs/`; GUI imports them directly | A7 + "legacy dir must not hold production code" | `gui/main_window.py:32-38,53` | move to `src/presentation/dialogs/`, update 9 imports (7 gui + 2 intra-legacy), delete orphan |
| **G-2** | Inline unit factors in GUI (`σ[S/cm]×0.01→S/m`, `S[V/K]×1e6→µV/K`) — GUI implements application-level conversion | A4 | `gui/main_window.py:663,665,690,712,735,738` | route through `application.unit_conversion` helpers |
| **G-3** | Inline unit factors in presentation (`g/cm³→kg/m³ ×1000`, `mm²/s→m²/s ×1e-6`, `J/g·K→J/kg·K ×1000`) | A3 (and A2 in spirit) | `presentation/kappa_logic.py:119-120,172-174,210-218` | route through `application.unit_conversion`; **highest numerical-risk item** — golden values must be unchanged |
| **G-4** | Compatibility shims retained after their purpose expired | "Remove obsolete compatibility modules after confirming no dependents" | §2.4 | delete 9 shims after updating the 2 test files that import 3 of them |
| **G-5** | Architecture tests permit `gui → legacy.ui.dialogs` | A7 | `test_architecture_dependencies.py:279` | Phase 4: forbid every `seebeck_prime.legacy` import anywhere |
| **G-6** | Orphan `plot_options_dialog.py` | dead code | §2.3 | delete (after zero-reference re-confirmation in Phase 3) |

**Explicitly reviewed and accepted as compliant (no action):**

- `presentation/main_table_plots.py:169` (`×1e6` for the µV/K axis label) —
  display-unit *formatting* for a plot is presentation logic by the agreed
  definition ("Presentation logic"). The authoritative conversion stays in
  `application/unit_conversion`.
- `plugins/` (6 modules, 136 LOC) — all import domain only (9 edges);
  `arrhenius.py` holds real science but sits in a domain-only package, which
  satisfies the layering rule. Keeping the plugin façade as-is; no rewrite.
- Wildcard imports in `plugins/{electronic,hall,phonon}.py` — style debt,
  already CR-12 in `docs/CODE_PROBLEMS_REGISTER.md`; optional cleanup, not an
  architecture violation.

---

## 4. Measured dependency graph (baseline for Phase 4)

| Source | → Target | Edges |
|---|---|---:|
| domain | — | 0 |
| application | domain | 17 |
| presentation | application | 11 |
| gui | presentation / application / legacy | 10 / 3 / 7 |
| legacy | presentation / application / domain | 23 / 14 / 3 |
| plugins | domain | 9 |
| infrastructure | — | 0 |
| main.py | gui, application, infrastructure | — |

Post-migration target graph: identical, minus every row containing `legacy`,
plus `gui → presentation.dialogs` (inside presentation).

## 5. Risks carried into Phase 2/3

1. **G-3 numerical risk (highest):** replacing literal factors with converter
   calls must not shift any computed value. Mitigation: golden-value tests
   (`tests/test_batch_workflows.py` asserts exact κ/ZT values), a new
   equivalence test, and re-running the benchmark suite.
2. **Test semantics:** `tests/test_legacy_calculations_compatibility.py`
   exists *to test the shim*. When the shim is deleted, that test is deleted
   with it — that is removal of a compatibility guarantee the user no longer
   has, not a weakening of coverage of the canonical functions (which keep
   their own tests). This will be stated explicitly in Phase 4 for approval.
3. **GUI regression:** dialogs are exercised manually today; automated GUI
   coverage is partial (known). Mitigation: startup smoke test + import tests
   for every moved dialog + full Qt-venv suite.

## 6. Verdict

The codebase is **already structurally close** to the agreed architecture.
The scientific core is clean; the deviations are concentrated in one place
(the legacy dialog layer) plus two small unit-conversion hygiene gaps.
No rewrite is needed — Phase 2 maps a contained, mostly mechanical migration.
