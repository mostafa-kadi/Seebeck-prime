# Architecture Migration — Phase 3 Report (Steps A–D)

**Status:** COMPLETE — both test suites and the benchmark suite green.
**Authorization:** User approved Phase 3 continuation (map rows 21–23 of
`docs/ARCHITECTURE_PHASE2_MIGRATION_MAP.md`; rows 20 and 24 are Phase 4 items
and were **not** executed).
**Rollback:** local backups at
`C:\Users\Elkady\Documents\seebeck_new\Seebeck-Prime_backup_2026-11-13.zip`
(working tree) and `Seebeck-Prime_history_2026-11-13.bundle` (git history);
nothing has been committed.

---

## 1. Execution summary

| Step | Map row | Work | Result |
|------|---------|------|--------|
| A (3a/3b) | 21 (+ move/delete rows 1–9, 11–19 partial) | 9 dialogs moved to `presentation/dialogs/`; 7 shim/orphan files deleted; imports and 5 test files re-pointed; new canonical-surface test | DONE, suites green |
| B (3c) | 22 (G-2) | 6 inline GUI factors → `application.unit_conversion` vector helpers; 6 equivalence tests | DONE, suites green |
| C (3d) | 23 (G-3) | 3 new quantity kinds (domain + application); 8 inline `kappa_logic` factors replaced; 13 new tests | DONE, suites + benchmark suite green |
| D (3e) | (verification) | Legacy compatibility shim test re-run against intact shim | DONE, 6 passed |
| — | 25 | `setup.py` nested-package walk verified (packaging auto-includes `presentation.dialogs`) | DONE (editable-install smoke remains queued under D-05/D-06) |

## 2. Step A — dialog migration (map row 21)

**Moved** `src/legacy/ui/dialogs/` → `src/presentation/dialogs/` (9 files):
`kappa_dialog`, `spb_dialog`, `hall_mobility_dialog`, `weighted_mobility_dialog`,
`device_efficiency_dialog`, `multi_sample_dialog`, `error_bar_dialog`,
`plot_settings_dialog`, `processed_data_dialog` (new package `__init__.py` added).

**Deleted** (7 files, dependents verified before deletion):
- orphan `legacy/ui/dialogs/plot_options_dialog.py`
- shims `legacy/ui/logic/{kappa_logic, table_handler, ui_builder, unit_converter}.py`
- shims `legacy/ui/widgets/{plot_window, table_widget}.py`

Why one coherent batch: 10 tests in `test_architecture_dependencies.py` read the
legacy file paths directly, so move + delete + test update had to land
atomically (stale `__pycache__` cleared as well).

**Import re-pointing:**
- `gui/main_window.py` — 7 imports → `seebeck_prime.presentation.dialogs.*`
- `presentation/dialogs/multi_sample_dialog.py` → `presentation.dialogs.plot_settings_dialog`
- `presentation/dialogs/error_bar_dialog.py` → `presentation.dialogs.processed_data_dialog`
- `presentation/dialogs/spb_dialog.py` — `LEGACY_DEFAULT_LORENZ` re-pointed from
  `domain.physical_constants` to the `application.use_cases` re-export
  (**identical value**, 2.44e-8 W·Ω·K⁻²; keeps the presentation→application rule).

**Test updates:** `test_architecture_dependencies.py` (10 tests re-pointed to the
new paths; shim-existence assertions removed, delegation assertions kept),
`test_batch_workflows.py` (canonical `process_multi_sample_data` /
`process_multi_sample_batch` + `TableFileService.save_workbook`; spb/multi-sample
dialog paths), `test_author_decisions.py`, `test_text_file_support.py`,
`test_unit_converter.py` → `presentation.unit_converter`.
**New:** `tests/test_canonical_calculations_surface.py` (3 tests) — identical
numeric assertions to the legacy compatibility file; shim-vs-domain identity
assertions intentionally not carried (their subject disappears in Phase 4).

## 3. Step B — GUI inline unit factors (map row 22, gap G-2)

Added vector-capable helpers to `src/application/unit_conversion.py`:
`to_base_values` / `from_base_values` — element-wise delegation to the existing
scalar workflows, so conversion definitions remain single-sourced in
`domain/units.py`; NaN and unknown-unit pass-through behaviour are identical to
the scalar API.

Replaced the 6 inline factors in `gui/main_window.py`
(`open_weighted_mobility_tool`, `open_hall_mobility_tool`, `open_spb_tool`,
`open_device_efficiency_tool`): S/m→S/cm and V/K→µV/K now route through
`from_base_values`. Temperature (K) and thermal conductivity (W/mK) pass
through unchanged, as before.

**Numerical equivalence (measured, not assumed):** the retired GUI expression
multiplied by `0.01`, the domain converter divides by `100.0`. A 200,000-value
sweep measured a worst-case relative difference of **2.22e-16 — under one
double-precision ulp**; zero converts to exact +0.0 on both paths. The Seebeck
conversion is bit-identical (`*1e6` on both paths). 6 equivalence tests pin
this, including the ≤1-ulp parity assertion and NaN propagation.

## 4. Step C — presentation inline unit factors (map row 23, gap G-3)

**Domain** (`src/domain/units.py`) — new "Sample Physical Properties (LFA
workflow)" section, matching the file's existing style (ValueError on unknown
units, pass-through for the SI base unit, equivalent spellings accepted):

| Quantity | SI base | Display → SI |
|----------|---------|--------------|
| density | kg/m³ | `g/cm³` ×1000 (`kg/m³` pass-through) |
| thermal_diffusivity | m²/s | `mm²/s` ×1e-6 (`m²/s` pass-through) |
| specific_heat_capacity | J/(kg·K) | `J/(g·K)` ×1000 (`J/(kg·K)` pass-through) |

**Application** (`src/application/unit_conversion.py`) — `QuantityKind`
extended with the three kinds; value dispatch, and
`uncertainty_to_base` / `uncertainty_from_base` extended with the linear-scale
rule (an uncertainty transforms exactly like its value — these conversions are
pure scale factors, unlike the nonlinear Ω·cm case).

**Presentation** (`src/presentation/kappa_logic.py`) — all **8** inline factor
sites replaced with application-layer calls (matches G-3's count):
1. density `g/cm³ ×1000` (line 119)
2. fixed-mode α `mm²/s ×1e-6` (line 172)
3. fixed-mode cp `J/g·K ×1000` (line 173)
4. error-mode α `×1e-6` in the κ call
5. error-mode cp `×1000` in the κ call
6. error-mode dα `×1e-6` in the propagation call
7. error-mode dcp `×1000` in the propagation call
(the κ-call α/cp factors and propagation-call factors are 4 sites in the error
branch; total 8 arithmetic sites)

**Regression evidence:** 13 new tests in
`tests/scientific/test_unit_conversion_matrix.py` (round trips for every
supported spelling, exact factors, unknown-unit rejection, the inline-factor
equivalence assertions, uncertainty equivalence, and an end-to-end golden
κ = α·cp·ρ check producing 0.9 W/(m·K)). Golden κ/ZT values in
`test_batch_workflows.py` unchanged and green. The LFA use-case golden in
`test_use_cases.py` unchanged and green.

## 5. Step D — legacy shim verification (kept until Phase 4)

`tests/test_legacy_calculations_compatibility.py` still passes against the
intact `legacy/core` shim (6 passed together with the canonical-surface file).
Per the migration map, the shim and its test are retired **together in
Phase 4** (row 20: delete the whole `src/legacy/` tree; row 24: forbid every
`seebeck_prime.legacy` import).

## 6. Verification matrix

| Suite | Pre-Phase 3 | after A | after B | after C/D |
|-------|-------------|---------|---------|-----------|
| conda (`anaconda3\python.exe -m pytest -q`) | 684 passed / 10 skipped | 687 / 10 | 693 / 10 | **706 / 10, exit 0** |
| Qt venv (`seebeck-gui2`) | 691 passed / 6 skipped | 694 / 6 | 700 / 6 | **713 / 6, exit 0** |
| benchmark suite (`pytest tests/experimental_benchmarks -q`) | — | — | — | **119 passed / 7 skipped, exit 0** |

Delta arithmetic: +3 (Step A canonical-surface tests) +6 (Step B) +13 (Step C)
= +22 in both environments — matches exactly.

## 7. Tree state after Phase 3

- `src/` now holds **69 `.py` files** (was 75: −7 shim/orphan deletions,
  +1 `presentation/dialogs/__init__.py`).
- Current LOC measurement (non-blank lines, `Get-Content | Measure-Object -Line`):
  8,743. The earlier `CODE_SKELETON.md` figure (8,259) was produced by a
  different counter; treat the LOC delta qualitatively, the file count is exact.
- `src/legacy/` retains only: `__init__.py`, `core/{__init__, analyzer,
  calculations, constants}.py`, and empty `ui/{,dialogs,logic,widgets}/
  __init__.py` — the entire Phase 4 deletion target.

## 8. NEW FINDING — inline unit factors outside the audited gaps (resolved by decision)

While verifying Step C with a project-wide factor sweep, additional inline
factors were found in presentation files that **neither G-2/G-3 nor any
migration-map row covers** (rows 3, 5, 7 moved these dialogs without a
factor-fix requirement). The user approved a focused **Step C+** (2026-11-13):
fix the existing-vocabulary sites now, add the hall vocabulary as part of the
same step, and document the percentage-arithmetic sites as a deliberate
exclusion.

| File | Sites | Disposition |
|------|-------|-------------|
| `presentation/dialogs/device_efficiency_dialog.py:138-139` | 2 | **FIXED** — `to_base_value` (seebeck, conductivity); both operations bit-identical to the retired inline factors |
| `presentation/main_table_plots.py:165-168` | 2 | **FIXED** — σ→mΩ·cm via `convert_resistivity_to_mohm_cm` (existing application wrapper, bit-identical `1e5/σ`), V/K→µV/K via `from_base_values` |
| `presentation/dialogs/hall_mobility_dialog.py` | ~13 | **FIXED** — new vocabulary (see below); every replaced operation bit-identical except S/m→S/cm (÷100 vs ×0.01, ≤1 ulp, same documented class as Step B) |
| `presentation/dialogs/spb_dialog.py:313-315` | 2 | **FIXED** — discovered during implementation (omitted from the first sweep summary); new `seebeck_to_uvk` working-unit standardizer; bit-identical (µV/K pass-through, mV/K ×1e3, V/K ×1e6) |
| `presentation/dialogs/error_bar_dialog.py:264-279` | 4 | **DOCUMENTED, NOT CHANGED** — relative-error **% → fraction** arithmetic, not a measurement unit; recorded in `docs/CODE_PROBLEMS_REGISTER.md` §9 as a deliberate exclusion (2026-11-13) |

**New vocabulary added (Step C+):**

*Domain* (`src/domain/units.py`): `voltage_to_volt`/`voltage_from_volt` (V/mV/µV),
`length_to_meter`/`length_from_meter` (m/cm/mm/µm), `current_to_ampere`/
`current_from_ampere` (A/mA/µA), `magnetic_flux_density_to_tesla`/
`magnetic_flux_density_from_tesla` (T/Gauss), `hall_coefficient_to_si`/
`hall_coefficient_from_si` (m³/C ↔ cm³/C), `hall_coefficient_to_cm3`
(input standardizer for the Hall application-model contract),
`conductivity_to_scm` (transport-input → σ[S/cm] standardizer, incl. Ω·cm and
mΩ·cm resistivity forms), `seebeck_to_uvk` (input standardizer for the SPB
contract). All follow the file's conventions (ValueError on unknown units,
pass-through for SI base, equivalent spellings).

*Application* (`src/application/unit_conversion.py`): `QuantityKind` extended
with `voltage`, `length`, `current`, `magnetic_flux_density`, `hall_coefficient`
(value dispatch + linear-rule uncertainty branches); working-unit wrappers
`conductivity_to_scm`, `hall_coefficient_to_cm3`, `seebeck_to_uvk` (unknown
unit → legacy pass-through, matching the retired dialog `else` branches); and
`carrier_density_m3_to_cm3` / `carrier_density_cm3_to_m3` exposing the existing
domain helpers.

*Presentation*: `hall_mobility_dialog` (raw mode: 4 SI-prefix conversions + R_H
display conversion + carrier density; table mode: transport and R_H
standardization; density readback ×2), `spb_dialog` (Seebeck standardization),
`device_efficiency_dialog` (table readback), `main_table_plots`
(weighted-mobility block). Carrier-density arithmetic now routes through the
named domain helpers instead of raw `*1e-6`/`*1e6`.

**Regression evidence:** 33 new tests in
`tests/scientific/test_unit_conversion_matrix.py` (round trips for every
prefix spelling, exact factors, unknown-unit rejection, retired-branch
equivalence for every replaced site, the raw-mode SI chain bit-identity, and
the linear-rule uncertainty coverage). The synthetic execution namespace for
the SPB dialog source in `test_batch_workflows.py` gained `seebeck_to_uvk`
(the tests execute the extracted dialog method in a controlled namespace).

**Step C+ verification:** conda full suite **739 passed / 10 skipped (exit 0)**;
Qt suite **746 passed / 6 skipped (exit 0)**; benchmark suite **119 passed /
7 skipped (exit 0)**. Delta arithmetic: +33 tests in both environments —
matches exactly.

## 9. Notes

- CR-08 (gui→legacy.ui.dialogs exception) is resolved by this migration; the
  register entry update is scheduled for Phase 6 as planned.
- `tests/test_import_root.py:62` still lists `"legacy"` — correct until the
  Phase 4 tree deletion (then removed per row 24's tightening).
- Qt venv rebuilt once this session (temp-dir wipe); recipe unchanged.
- No application source, test results, scientific assumptions, or validation
  records were modified to strengthen any result; all numerical behaviour
  changes are the documented ≤1-ulp rounding differences, verified by tests.
