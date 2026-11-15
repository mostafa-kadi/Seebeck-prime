# Seebeck Prime — Code Skeleton (Layered Modular Monolith)

**Status:** refreshed **2026-11-13 (post-migration revision)** against the
**live** source tree. Method: AST extraction of every public symbol per
module (60 files, 8,359 non-blank/non-comment LOC in `src/`) + import-graph
resolution to a file per import. Every count, class name and dependency edge
below is measured, not remembered. This revision reflects the **completed**
architecture migration (Phases 3–5, see `docs/ARCHITECTURE_PHASE*_REPORT.md`):
the 9 dialogs moved to `presentation/dialogs/`, the whole `src/legacy/` tree
deleted, and the unit-conversion vocabulary consolidated in `domain/units.py`
+ `application/unit_conversion.py`. The same-morning revision still counted
the legacy layer (75 files, 8,259 LOC).

This document is **descriptive of the current layout**, not a change proposal.

---

## 1. Layering model (as designed)

```text
┌─────────────────────────────────────────────────────────────┐
│ gui/            composition root (Qt main window, wiring)   │
└───────────────┬─────────────────────────────────────────────┘
                │ imports
┌───────────────▼─────────────────────────────────────────────┐
│ presentation/  (plot windows, table widget, κ logic,        │
│                table handler, notices, dialogs/ ×9)         │
└───────────────┬─────────────────────────────────────────────┘
                │ imports
┌───────────────▼─────────────────────────────────────────────┐
│ application/   (use cases, measurement processing, schema,  │
│                unit conversion, SPB batch, ports, services)  │
└───────────────┬─────────────────────────────────────────────┘
                │ imports
┌───────────────▼─────────────────────────────────────────────┐
│ domain/        (pure science: calculations, uncertainty,    │
│                units, SPB, Hall, phonon, transport, device  │
│                efficiency, analysis, validation, constants) │
└─────────────────────────────────────────────────────────────┘
                ▲
┌───────────────┴───────────────┐
│ infrastructure/  pandas tabular data store (I/O adapter)    │
└───────────────────────────────┘

┌──────────────┐
│   plugins/   │  domain re-exports only
└──────────────┘
```

### 1.1 Measured dependency graph (imports resolved to files)

| Source | → Target | Edges | Rule |
|---|---|---:|---|
| `domain` | *(no internal imports)* | 0 | pure science: numpy/scipy only |
| `application` | `domain` | 17 | inward only |
| `presentation` | `application` | 27 | inward only; **no** domain, no infrastructure |
| `gui` | `presentation` | 17 | composition |
| `gui` | `application` | 4 | composition |
| `plugins` | `domain` | 9 | re-exports only |
| `infrastructure` | *(none)* | 0 | depends on nothing internal |
| `main.py` (root) | `gui`, `application`, `infrastructure` | — | the only place adapters are wired |

**Reading:** the inward rule `domain ← application ← presentation ← gui` holds
with **no deviations** — the measured graph is acyclic and every edge points
inward. The former `gui → legacy.ui.dialogs` exception and the whole `legacy`
compatibility package were removed on 2026-11-13 (Phase 4; see §5.2).

---

## 2. Domain layer — `seebeck_prime.domain` (13 modules, 2,012 LOC)

```python
# domain/physical_constants.py
BOLTZMANN, ELECTRON_CHARGE, AVOGADRO, GAS_CONSTANT, LEGACY_GAS_CONSTANT,
PLANCK, ELECTRON_MASS, KB_OVER_E_UV_K, FARADAY,
SILICON_DEFAULT_DEBYE_T, SILICON_DEFAULT_SOUND_VELOCITY,
ATOMIC_WEIGHTS, LEGACY_ATOMIC_WEIGHTS,
DEFAULT_LORENZ, SOMMERFELD_LORENZ_EXACT, LEGACY_DEFAULT_LORENZ
# DEFAULT_LORENZ = 2.44e-8 W·Ω·K⁻²  (rounded; exact 2.443004509e-8 retained as
# SOMMERFELD_LORENZ_EXACT). LEGACY_DEFAULT_LORENZ = DEFAULT_LORENZ — kept only
# as a backward-compatibility alias after the Lorenz-number unification.

# domain/calculations.py
def calculate_pf(seebeck, electrical_conductivity)                      # PF = S²·σ
def calculate_kappa_e(electrical_conductivity, temperature, lorenz)     # κe = L·σ·T
def calculate_kappa_l(kappa_total, kappa_e)                            # κL = κ − κe
def calculate_zt(pf, temperature, kappa_total)                         # ZT = PF·T/κ
def estimate_lorenz(seebeck_uv_k)                                      # Kim 2015 empirical
def calculate_molecular_weight(formula, atomic_weights)
def calculate_legacy_molecular_weight(formula)
def calculate_dulong_petit_limit(atom_count, molar_mass_g_mol, unit)

# domain/uncertainty.py
def propagate_relative_uncertainty(value)
def propagate_pf_error(seebeck, seebeck_err, conductivity, conductivity_err)
def propagate_kappa_e_error(conductivity, conductivity_err, temperature, temp_err, lorenz, lorenz_err)
def propagate_kappa_l_error(kappa_total_err, kappa_e_err)
def propagate_zt_error(pf, pf_err, temperature, temp_err, kappa_total, kappa_total_err)
def propagate_sigma_error(area, area_err, length, length_err, resistance, resistance_err)
def propagate_kappa_error(diffusivity, diffusivity_err, cp, cp_err, density, density_err)
def propagate_density_error(weight, weight_err, area, area_err, thickness, thickness_err)

# domain/transport.py
def calculate_weighted_mobility(temperature_k, resistivity_mohm_cm, seebeck_uv_k)
def resistivity_to_mohm_cm(value, unit)

# domain/device_efficiency.py
def calculate_efficiencies(temps_k, seebecks_v_k, sigmas_s_m, kappas_w_mk, tc_k, th_k) -> dict

# domain/spb.py
def fermi_integral(j, eta)
def seebeck_from_reduced_fermi_level(eta, lambda_scat)
def reduced_fermi_level_from_seebeck(seebeck_uv_k, lambda_scat)
def rigorous_lorenz_number(eta, lambda_scat)
def calculate_carrier_density_spb(eta, effective_mass_ratio, temperature_k)
def calculate_effective_mass(seebeck_uv_k, carrier_density_cm3, temperature_k, lambda_scat)
def generate_pisarenko_curve(effective_mass_ratio, temperature_k, n_min_cm3, n_max_cm3, num_points, lambda_scat)
def predict_optimal_transport(effective_mass_ratio, temperature_k, mu_0_cm2_vs, lambda_scat)
def estimate_lorenz(seebeck_uv_k)
def calculate_carrier_concentration(seebeck_uv_k)

# domain/hall.py
def calculate_hall_coefficient_from_raw(hall_voltage_v, thickness_m, current_a, magnetic_field_t)
def calculate_hall_carrier_density(hall_coefficient_m3_c, hall_factor)
def determine_carrier_type(hall_coefficient) -> str
def calculate_hall_mobility(hall_coefficient_m3_c, electrical_conductivity_s_m)
def calculate_hall_mobility_cm2_vs(hall_coefficient_cm3_c, electrical_conductivity_s_cm)
def fit_scattering_exponent(temperature_k, mobility_cm2_vs)

# domain/phonon.py
def dulong_petit_molar(n_atoms)
def dulong_petit_specific(n_atoms, molar_mass_g_mol)
def kappa_from_diffusivity(diffusivity_mm2s, cp_J_gK, density_g_cm3)
def kappa_from_diffusivity_si(diffusivity_m2s, cp_J_kgK, density_kg_m3)

# domain/analysis.py
def mad_filter(x, thresh) -> np.ndarray
def linear_regression(x, y) -> dict          # slope, intercept, r_squared, stderr, n
def interpolate_onto(source_x, source_y, target_x) -> np.ndarray
def round_temperature(T, step) -> np.ndarray
def align_datasets(T_ref, T_other, y_other) -> np.ndarray

# domain/validation.py
class Severity(Enum); class ValidationMessage
def validate_temperature_array(T) / validate_conductivity_array(sigma)
def validate_seebeck_array(S) / validate_kappa_array(kappa) / validate_kappa_l_array(kappa_L)
def validate_dataset(T, sigma, S, kappa, kappa_L)

# domain/units.py    (single physical-unit vocabulary for the whole app)
def celsius_to_kelvin(celsius) / kelvin_to_celsius(kelvin)
def to_kelvin(value, unit) / from_kelvin(value, unit)
def convert_temperature(value, from_unit, to_unit) / convert_temperature_uncertainty(u)
def sigma_to_sm(value, unit) / sigma_from_sm(value, unit)
def conductivity_to_scm(value, unit)
def seebeck_to_vk(value, unit) / seebeck_from_vk(value, unit)
def seebeck_to_uvk(value, unit)
def pf_to_si(value, unit) / pf_from_si(value, unit)
def kappa_to_si(value, unit) / kappa_from_si(value, unit)
def carrier_density_m3_to_cm3(value) / carrier_density_cm3_to_m3(value)
def density_to_si(value, unit) / density_from_si(value, unit)
def thermal_diffusivity_to_si(value, unit) / thermal_diffusivity_from_si(value, unit)
def specific_heat_to_si(value, unit) / specific_heat_from_si(value, unit)
def voltage_to_volt(value, unit) / voltage_from_volt(value, unit)
def length_to_meter(value, unit) / length_from_meter(value, unit)
def current_to_ampere(value, unit) / current_from_ampere(value, unit)
def magnetic_flux_density_to_tesla(value, unit) / magnetic_flux_density_from_tesla(value, unit)
def hall_coefficient_to_si(value, unit) / hall_coefficient_from_si(value, unit)
def hall_coefficient_to_cm3(value, unit)

# domain/dataset.py
class ThermoelectricDataset    # is_empty, has_uncertainty, clear_calculated
```

## 3. Application layer — `seebeck_prime.application` (11 modules, 1,262 LOC)

```python
# application/table_schema.py
COL_TEMP=0; COL_EC=1; COL_SEEBECK=2; COL_PF=3
COL_K_TOTAL=4; COL_K_E=5; COL_K_L=6; COL_ZT=7
BASE_COLUMN_COUNT=8; INPUT_COLUMNS_BASE=(COL_TEMP, COL_EC, COL_SEEBECK, COL_K_TOTAL)
COLUMN_HEADERS; ERROR_COLUMN_HEADERS

# application/ports.py
class TabularDataStore(Protocol):   # read, read_csv, read_workbook, write, write_workbook

# application/services.py
class ThermoelectricAnalyzer        # 13 parameters in __init__
    process_four_probe / process_raw_seebeck / process_laser_flash
    calculate_combined_sigma_error / calculate_combined_seebeck_error
    calculate_transport / get_reporting_statement

# application/use_cases.py
def calculate_thermoelectric_properties(T, sigma, S, kappa, lorenz, u_sigma, u_S, u_kappa, u_T)
def calculate_zt_use_case(T, sigma, S, kappa, lorenz)
def process_multi_sample_data(df, lorenz) / process_multi_sample_batch(samples, lorenz)
def validate_measurement_data(...) / validate_calculated_properties(...) / validate_multi_sample_properties(...)
def calculate_weighted_mobility_use_case(...) / calculate_efficiencies_use_case(...)
def calculate_kappa_from_lfa_si_use_case(...) / propagate_lfa_kappa_uncertainty_use_case(...)
def convert_resistivity_to_mohm_cm(value, unit)
def combine_relative_uncertainties_use_case(value)
def calculate_formula_mass_use_case(formula) / calculate_dulong_petit_limit_use_case(...)
# use_cases re-exports DEFAULT_LORENZ and LEGACY_DEFAULT_LORENZ from
# domain.physical_constants (import-path compatibility after the unification;
# both names now hold 2.44e-8 W·Ω·K⁻²)

# application/measurement_processing.py   (pure table transforms)
def find_column(df, aliases)
def process_four_probe_table(raw_df) / process_raw_seebeck_table(raw_df) / process_laser_flash_table(raw_df)
def combine_sigma_uncertainty(sigma_vals, sigma_stat_err_vals, width, width_err, thickness, thickness_err, probe_length, probe_length_err)
def combine_seebeck_uncertainty(s_stat_err_vals, seebeck_ref_err_uv_k)

# application/unit_conversion.py    (table-facing conversion front end)
QuantityKind = Literal[...]         # 13 kinds: temperature, conductivity, seebeck,
                                    # power_factor, thermal_conductivity, density,
                                    # thermal_diffusivity, specific_heat_capacity,
                                    # voltage, length, current, magnetic_flux_density,
                                    # hall_coefficient
def convert_temperature_to_kelvin(value, unit)
def to_base_value(value, unit, quantity) / from_base_value(value, unit, quantity)
def to_base_values(values, unit, quantity) -> np.ndarray     # vectorised
def from_base_values(values, unit, quantity) -> np.ndarray   # vectorised
def uncertainty_to_base(value, uncertainty, unit, quantity) / uncertainty_from_base(...)
                                    # uncertainty scaling is linear in the factor
def conductivity_to_scm(value, unit) / hall_coefficient_to_cm3(value, unit)   # dialog wrappers
def carrier_density_m3_to_cm3 / carrier_density_cm3_to_m3 / seebeck_to_uvk   # domain re-exports

# application/spb_batch.py
class SPBBatchRowResult
def calculate_spb_batch_rows(temperatures_k, seebecks_uv_k, concentrations_cm3, row_indices, scattering_parameter)
def calculate_spb_batch_mean_parameters(temperatures_k, seebecks_uv_k, concentrations_cm3, scattering_parameter)

# application/table_files.py
class MultiSampleFileError; class TableFileService   # load, load_multi_sample_files, save, save_workbook

# application/data_mapping.py
def find_column_index(source_columns, aliases, used_indices)
def get_robust_mapped_dataframe(source_df, search_groups)

# application/models.py    (dataclasses / value objects)
```

## 4. Presentation layer — `seebeck_prime.presentation` (23 modules, 4,192 LOC)

```python
# presentation/table_plot_data.py    (Qt-free, explicit inputs)
class PlotDataContext
def get_table_data(frame, y_col_index, error_mode) -> tuple   # (x, y, x_err, y_err)

# presentation/main_table_plots.py
def resolve_plot_context(main_window)
def create_plot(main_window, y_col_index) / plot_all_properties(main_window) / plot_custom_layout(main_window, selection)

# presentation/plot_window.py
class PlotWindow(QMainWindow)     # create_sidebar, create_sep, wrap_limits, pick_color, sync_and_draw,
                                   # on_mouse_move, on_click, show_context_menu, autoscale, edit_text,
                                   # edit_trace_props, prompt_label_edit, plot, plot_multi, set_figure,
                                   # draw_plot, copy_to_clipboard, export_data_to_excel
class TraceStyleDialog(QDialog)   # pick, get_properties

# presentation/table_handler.py
def get_column_headers(error_mode) / get_input_columns(error_mode)
def setup_table_properties(app) / reset_and_create_new_sheet(app, rows) / update_headers(app)
def load_data_into_table(app, df, is_base_units)
def get_robust_mapped_dataframe(source_df, search_groups)
def on_paste_recalculate(app) / interpolate_k_values(app, temps, k_values, unit, k_errs)

# presentation/kappa_logic.py
def smart_map_lf_data(df) / process_grouped_lf_data(df) / update_dp_display(dialog)
def calculate_properties(dialog) / read_source_data(dialog) / draw_custom_plot(dialog, selection)

# presentation/table_widget.py
class ClipboardAwareTableWidget(QTableWidget)  # show_context_menu, keyPressEvent, copy/paste/cut/delete_selection

# presentation/validation_notices.py
def split_by_severity(notices) / has_blocking_notices(notices) / summarise(notices)
def format_detail(notices) / negative_lattice_count(notices) / notice_signature(notices)

# presentation/multi_sample_plots.py     def plot_comparisons(processed_samples, settings, show)
# presentation/plot_data_dialog.py        class PlotDataDialog(QDialog)  # get_selection
# presentation/ui_builder.py               def create_menu_bar(mw) / create_toolbar(mw)
# presentation/ui_utils.py                 def pick_color(initial_color, parent) / add_unit_selector(...)
# presentation/unit_converter.py           def on_unit_changed(app)

# presentation/dialogs/    (9 dialogs + package __init__ — migrated 2026-11-13
#                          from the retired src/legacy/ui/dialogs/ tree)
class KappaToolDialog          kappa_dialog.py               κ single-sample tool
class MultiSampleDialog        multi_sample_dialog.py        multi-sample comparison
class WeightedMobilityDialog   weighted_mobility_dialog.py   weighted mobility (D-12: physics unverified)
class HallMobilityDialog       hall_mobility_dialog.py       Hall mobility / carrier density
class SPBModelingDialog        spb_dialog.py                 SPB modeling (Pisarenko, m*)
class DeviceEfficiencyDialog   device_efficiency_dialog.py   TE device efficiency
class ErrorBarDialog           error_bar_dialog.py           global error-bar percentages (documented-only: %→fraction)
class PlotSettingsDialog       plot_settings_dialog.py       per-trace plot settings (used by MultiSampleDialog)
class ProcessedDataDialog      processed_data_dialog.py      processed-data viewer (used by ErrorBarDialog)
```

## 5. GUI / composition root

```python
# gui/main_window.py
class ThermoelectricApp(QMainWindow)
    init_ui, setup_table_properties, create_status_bar, present_validation_notices,
    on_cell_changed, on_paste_recalculate, toggle_error_bars, recalculate_all_properties,
    on_unit_changed, update_headers, reset_and_create_new_sheet, new_file, open_file,
    save_file, save_as_file, load_data_into_table, confirm_action,
    open_kappa_tool_dialog, open_multi_sample_tool, open_weighted_mobility_tool,
    open_hall_mobility_tool, open_spb_tool, open_device_efficiency_tool,
    interpolate_k_values, create_plot, plot_all_properties, open_plot_selection_dialog, about_app

# gui/file_commands.py   new_file / open_file / save_file / save_as_file
# gui/table.py           (6-LOC back-compat re-export of presentation.table_widget;
#                         single-implementation rule enforced by
#                         test_clipboard_table_widget_has_one_presentation_implementation)
# gui/__init__.py        layer package marker
```

### 5.1 Composition root — `main.py` (repo root)

```python
app          = QApplication(sys.argv); app.setStyle("Fusion")
store        = PandasTabularDataStore()          # infrastructure adapter
file_service = TableFileService(store)           # application port impl
window       = ThermoelectricApp(table_file_service=file_service,
                                  measurement_data_store=store)
```

`main.py` is the **only** place a concrete persistence adapter is instantiated.

### 5.2 The `legacy/` package — retired 2026-11-13

`src/legacy/` **no longer exists**. It was deleted in Phase 4 of the
architecture migration (`docs/ARCHITECTURE_PHASE4_REPORT.md`). At deletion it
measured 25 modules / 2,499 LOC:

- the **7 live dialogs** had already moved to `presentation/dialogs/` in
  Phase 3 (Step C+); `gui/main_window.py:32-54` now imports them from
  `seebeck_prime.presentation.dialogs.*` (see §4);
- `legacy/core/*` and `legacy/ui/logic|widgets/*` were thin delegation shims
  to domain / application / presentation and were dropped with the tree;
- `plot_options_dialog.py`, the only fully orphaned module, was deleted unused.

Two guard tests prevent the package from returning:

| Guard | Test |
|---|---|
| no file under `src/` may reference the retired tree | `test_no_package_imports_the_retired_legacy_tree` |
| importing `seebeck_prime.legacy` must raise ImportError | `test_the_retired_legacy_tree_is_no_longer_importable` |

Historical measurements of the legacy package are preserved in the phase
reports and in `docs/CODE_PROBLEMS_REGISTER.md` (**CR-08**, resolved
2026-11-13).

---

## 6. Layer summary (measured)

| Layer | Modules | LOC | Governing contract |
|---|---:|---:|---|
| domain | 13 | 2,012 | no internal imports; numpy/scipy only; no I/O |
| application | 11 | 1,262 | depends on domain only; *defines* the `TabularDataStore` port |
| presentation | 23 | 4,192 | depends on application only; Qt widgets, no science; incl. `dialogs/` ×9 |
| gui | 4 | 652 | composition root; wiring only |
| infrastructure | 2 | 84 | `PandasTabularDataStore` implements the port structurally; 0 internal imports |
| plugins | 6 | 136 | domain re-exports only |
| import shim | 1 | 21 | `src/seebeck_prime/__init__.py` |
| **total** | **60** | **8,359** | |

## 7. Source layout (single direction)

```text
src/                                  ← packaging root (editable install points here)
├── seebeck_prime/__init__.py         ← import-root shim (extends __path__ to src/)
├── domain/          (13 modules)     ← pure science
├── application/     (11 modules)     ← use cases, ports, services
├── infrastructure/  ( 2 modules)     ← pandas persistence adapter
├── presentation/    (23 modules)     ← Qt plot windows / table / notices + dialogs/ ×9
├── gui/              ( 4 modules)     ← main-window composition
└── plugins/          ( 6 modules)     ← domain re-exports
```

The physical tree is flat: every layer is a direct child of `src/`.
`src/seebeck_prime/__init__.py` extends the package search path to `src/`, so

```python
from seebeck_prime.domain.calculations import calculate_pf   # -> src/domain/calculations.py
```

In a built wheel the packages are laid out conventionally inside
`site-packages/seebeck_prime/` (see `setup.py`), so the shim is a no-op there.

## 8. Where the skeleton is enforced

`tests/test_architecture_dependencies.py` (25 tests) enforces the layering;
`tests/test_import_root.py` (7 tests) enforces the import-root contract:

| Rule | Test |
|---|---|
| domain imports no outer layer or gui | `test_domain_has_no_outer_layer_or_gui_imports` |
| no package references the retired legacy tree | `test_no_package_imports_the_retired_legacy_tree` |
| application imports neither presentation nor infrastructure | `test_application_does_not_import_presentation_or_concrete_infrastructure` |
| presentation imports neither domain nor infrastructure | `test_presentation_does_not_import_domain_or_infrastructure` |
| infrastructure has no GUI toolkit / file-dialog dependency | `test_infrastructure_has_no_file_dialog_or_gui_imports` / `test_infrastructure_has_no_gui_toolkit_dependency` |
| gui owns no science and no infrastructure | `test_gui_composition_does_not_own_science_or_infrastructure` |
| measured import graph has no cycles | `test_internal_package_import_graph_has_no_cycles` |
| dialogs delegate science to application | `test_device_efficiency_dialog_delegates_thermoelectric_properties` / `test_weighted_mobility_dialog_calls_application_use_cases_directly` / `test_multi_sample_dialog_uses_application_without_legacy_core_import` / `test_kappa_presentation_uses_application_formula_services` |
| presentation components use the canonical adapters | `test_main_window_uses_canonical_unit_conversion_presentation_adapter` / `test_plot_dialogs_use_canonical_presentation_utilities` / `test_main_window_uses_presentation_menu_and_toolbar_builder` / `test_table_presentation_uses_application_column_contract` / `test_clipboard_table_widget_has_one_presentation_implementation` / `test_plot_data_helper_consumes_explicit_inputs` |
| main window routes formulas / exports through application | `test_main_window_uses_application_layer_instead_of_domain_formulas` / `test_main_window_exports_processed_tables_through_file_service` / `test_plot_window_exports_through_application_file_service` / `test_application_services_does_not_read_or_write_files_directly` / `test_hall_and_spb_application_models_depend_on_domain` |
| domain performs no filesystem operations; application avoids direct filesystem access | `test_domain_performs_no_filesystem_operations` / `test_application_avoids_direct_filesystem_operations` |
| import root exposes one canonical module object per source file | `tests/test_import_root.py` (7 tests) |

**No sanctioned exceptions remain.** The former `gui → legacy.ui.dialogs`
exception was closed by Phase 4: every enforced rule now holds uniformly, and
the whole `src/` tree is scanned for retired-path references.

## 9. What this skeleton deliberately does NOT contain

Documented capability boundaries, not oversights:

- **Raw V/I → R → ρ → σ measurement chain** — not implemented (E-58). Geometry
  currently feeds only the σ *uncertainty*.
- **Covariance-aware uncertainty propagation** (J Σ Jᵀ) — not implemented;
  inputs are treated as independent.
- **Kane / Dingle / multiband Lorenz models** — not implemented.
- **Two-band models** for Mg₂Sn / SnSe / CaMnO₃-type comparisons.
- **Weighted-mobility physics** is implemented but its physical validity is
  unverified (D-12) — see `docs/SCIENTIFIC_MODEL_REGISTER.md`.
- **PbTe κ/κ_L benchmark comparison** — unverified (internally inconsistent
  published pair).

Sources: `validation/SCIENTIFIC_EQUATION_REGISTRY.md`,
`validation/SCIENTIFIC_VALIDATION_LIMITATIONS.md`,
`validation/remediation/PHASE3_FINDINGS.md`.
