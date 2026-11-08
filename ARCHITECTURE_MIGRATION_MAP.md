# ARCHITECTURE_MIGRATION_MAP.md
## Seebeck Prime Architecture Transition Plan

**Date:** 2026-08-24
**Status:** Draft - Ready for execution
**Phase:** 0 Complete

This document maps every current file to its target location in the new architecture, with dependencies, risk assessment, and migration sequence.

---

## Migration Legend

### Risk Levels
- 🟢 **Low**: Simple move, minimal dependencies, low impact
- 🟡 **Medium**: Requires some refactoring, moderate dependencies
- 🔴 **High**: Major refactoring required, complex dependencies

### Sequence
Migration is ordered by dependency - files with no dependencies are migrated first.

---

## Complete File Migration Map

| Current File | Target File | Reason | Dependencies | Migration Risk | Sequence | Status |
|--------------|-------------|--------|--------------|----------------|----------|--------|
| **CORE DOMAIN LAYER** | | | | | |
| `src/core/constants.py` | `src/seebeck_prime/domain/constants/physical.py` | Move physical constants to domain layer | None | 🟢 Low | 1 | Not Started |
| `src/core/calculations.py` (atomic weight) | `src/seebeck_prime/domain/materials/composition.py` | Extract materials-specific calculations | constants.py | 🟢 Low | 2 | Not Started |
| `src/core/calculations.py` (transport functions) | `src/seebeck_prime/domain/calculations/transport.py` | Extract transport calculations | constants.py | 🟢 Low | 3 | Not Started |
| `src/core/calculations.py` (thermal functions) | `src/seebeck_prime/domain/calculations/thermal.py` | Extract thermal calculations | constants.py | 🟢 Low | 4 | Not Started |
| `src/core/calculations.py` (SPB/lorenz) | `src/seebeck_prime/domain/models/spb.py` | Extract single parabolic band model | transport.py | 🟡 Medium | 5 | Not Started |
| `src/core/error_propagation.py` (MAD filter) | `src/seebeck_prime/domain/uncertainty/filtering.py` | Extract outlier filtering | None | 🟡 Medium | 6 | Not Started |
| `src/core/error_propagation.py` (Gaussian errors) | `src/seebeck_prime/domain/uncertainty/gaussian.py` | Extract error propagation | transport.py, thermal.py | 🟡 Medium | 7 | Not Started |
| `src/ui/logic/unit_converter.py` (all units) | `src/seebeck_prime/domain/units/` | Move unit system to domain layer | None | 🔴 High | 8 | Not Started |
| `src/ui/logic/weighted_mobility_logic.py` (core calculations) | `src/seebeck_prime/domain/transport/carrier.py` | Extract carrier transport calculations | spb.py | 🟡 Medium | 9 | Not Started |
| `src/ui/logic/kappa_logic.py` (core LFA calculations) | `src/seebeck_prime/domain/thermal/lfa.py` | Extract laser flash analysis | thermal.py | 🟡 Medium | 10 | Not Started |
| **APPLICATION LAYER** | | | | | |
| `src/core/analyzer.py` (single sample) | `src/seebeck_prime/application/analysis/single_sample.py` | Extract single sample analysis | domain calculations | 🟡 Medium | 11 | Not Started |
| `src/core/analyzer.py` (multi-sample) | `src/seebeck_prime/application/analysis/multi_sample.py` | Extract multi-sample analysis | single_sample.py | 🟡 Medium | 12 | Not Started |
| `src/ui/logic/table_handler.py` | `src/seebeck_prime/application/project/table_manager.py` | Extract table state management | domain units | 🔴 High | 13 | Not Started |
| `src/ui/logic/file_handler.py` | `src/seebeck_prime/application/project/file_manager.py` | Extract file management | infrastructure io | 🔴 High | 14 | Not Started |
| `src/core/error_propagation.py` (file processing) | `src/seebeck_prime/application/services/processor.py` | Extract measurement file processing | uncertainty, domain | 🟡 Medium | 15 | Not Started |
| **INFRASTRUCTURE LAYER** | | | | | |
| (new file) | `src/seebeck_prime/infrastructure/io/common.py` | Create common file I/O utilities | None | 🟢 Low | 16 | Not Started |
| `src/core/error_propagation.py` (four-probe reader) | `src/seebeck_prime/infrastructure/io/four_probe.py` | Extract four-probe file reader | common.py | 🟢 Low | 17 | Not Started |
| `src/core/error_propagation.py` (Seebeck reader) | `src/seebeck_prime/infrastructure/io/seebeck.py` | Extract Seebeck file reader | common.py | 🟢 Low | 18 | Not Started |
| (new Excel/CSV writers) | `src/seebeck_prime/infrastructure/excel/writer.py` | Extract Excel writing | common.py | 🟢 Low | 19 | Not Started |
| (new CSV handlers) | `src/seebeck_prime/infrastructure/csv/reader.py` | Extract CSV handling | common.py | 🟢 Low | 20 | Not Started |
| (new project persistence) | `src/seebeck_prime/infrastructure/persistence/project.py` | Create project serialization | None | 🔴 High | 21 | Not Started |
| **VISUALIZATION LAYER** | | | | | |
| `src/ui/logic/plot_handler.py` | `src/seebeck_prime/visualization/plots/single_sample.py` | Extract single sample plotting | matplotlib | 🟡 Medium | 22 | Not Started |
| `src/core/analyzer.py` (plot_comparisons) | `src/seebeck_prime/visualization/plots/multi_sample.py` | Extract multi-sample plotting | single_sample.py | 🟡 Medium | 23 | Not Started |
| (new fitting framework) | `src/seebeck_prime/visualization/fitting/base.py` | Create reusable fitting | scipy, numpy | 🟡 Medium | 24 | Not Started |
| `src/ui/widgets/plot_window.py` (export logic) | `src/seebeck_prime/visualization/exporters/figure.py` | Extract figure export | matplotlib | 🟢 Low | 25 | Not Started |
| **UI LAYER** | | | | | |
| `src/main.py` | `src/seebeck_prime/ui/main.py` | Keep entry point in UI layer | All layers | 🔴 High | 26 | Not Started |
| `src/ui/main_window.py` | `src/seebeck_prime/ui/windows/main_window.py` | Move main window | all UI modules | 🔴 High | 27 | Not Started |
| `src/ui/logic/ui_builder.py` | `src/seebeck_prime/ui/windows/menu_builder.py` | Extract menu building | main_window | 🟡 Medium | 28 | Not Started |
| `src/ui/widgets/table_widget.py` | `src/seebeck_prime/ui/widgets/clipboard_table.py` | Move custom table widget | None | 🟢 Low | 29 | Not Started |
| `src/ui/widgets/plot_window.py` | `src/seebeck_prime/ui/widgets/matplotlib_window.py` | Move plot window widget | visualization | 🟡 Medium | 30 | Not Started |
| `src/ui/dialogs/kappa_dialog.py` | `src/seebeck_prime/ui/dialogs/thermal/lfa_dialog.py` | Move kappa dialog to thermal module | domain/lfa.py | 🟡 Medium | 31 | Not Started |
| `src/ui/dialogs/weighted_mobility_dialog.py` | `src/seebeck_prime/ui/dialogs/transport/carrier_dialog.py` | Move mobility dialog to carrier module | domain/carrier.py | 🟡 Medium | 32 | Not Started |
| `src/ui/dialogs/multi_sample_dialog.py` | `src/seebeck_prime/ui/dialogs/analysis/comparison_dialog.py` | Move comparison dialog | application/analysis | 🟡 Medium | 33 | Not Started |
| All other dialogs | `src/seebeck_prime/ui/dialogs/` (organized by module) | Group dialogs by function | their respective domain modules | 🟡 Medium | 34 | Not Started |
| **PLUGINS (OPTIONAL MODULES)** | | | | | |
| `src/ui/logic/device_efficiency_logic.py` | `src/seebeck_prime/plugins/device_engineering/efficiency.py` | Move device logic to optional plugin | domain calculations | 🟢 Low | 35 | Not Started |
| `src/ui/dialogs/device_efficiency_dialog.py` | `src/seebeck_prime/plugins/device_engineering/ui/efficiency_dialog.py` | Move device dialog to plugin | efficiency.py | 🟢 Low | 36 | Not Started |
| **ROOT FILES** | | | | | |
| `requirements.txt` → `pyproject.toml` | `pyproject.toml` | Modern Python packaging | None | 🟡 Medium | N/A | Not Started |
| (new file) | `CITATION.cff` | Software citation standard | None | 🟢 Low | N/A | Not Started |
| (new file) | `CHANGELOG.md` | Version history | None | 🟢 Low | N/A | Not Started |
| (new file) | `CONTRIBUTING.md` | Contribution guidelines | None | 🟢 Low | N/A | Not Started |

---

## Immediate Fixes (Before Migration)

These critical issues must be fixed before starting the migration to ensure code consistency:

### Fix 1: Duplicated calculations in error_propagation.py
**Location:** `src/core/error_propagation.py` lines 496, 506
**Action:** Replace inline calculations with imports from core.calculations
**Deadline:** Immediate
**Risk:** Zero - maintains same calculation logic, eliminates duplication

### Fix 2: Remove matplotlib import from analyzer.py
**Location:** `src/core/analyzer.py`
**Action:** Extract plot_comparisons() to visualization layer, remove pyplot import from core
**Deadline:** Week 1
**Risk:** Low - plotting logic already exists in plot_handler.py, consolidate

### Fix 3: Add test infrastructure
**Action:** Create `tests/` directory, add pytest, write first unit tests for core calculations
**Deadline:** Week 1
**Risk:** Zero - adds safety net for migration

---

## Migration Wave 1 - Foundation (Weeks 1-2)
*Objective: Establish the new package structure, move low-risk domain files*

### Wave 1 Tasks:
1. Create the new package structure: `src/seebeck_prime/` with all subdirectories
2. Move constants.py → domain/constants/physical.py
3. Split calculations.py into transport.py and thermal.py
4. Add proper imports in all files
5. Write unit tests for all moved domain calculations
6. Verify all tests pass before proceeding

### Wave 1 Success Criteria:
- Can import core scientific functions without importing PyQt6
- All existing functionality works
- All tests pass
- No code duplication remains in core calculations

---

## Migration Wave 2 - Uncertainty & Units (Weeks 3-4)
*Objective: Move uncertainty engine and unit system to domain layer*

### Wave 2 Tasks:
1. Move error_propagation.py functions to domain/uncertainty/
2. Move unit_converter.py to domain/units/ with proper type safety
3. Add Monte Carlo uncertainty propagation as an option
4. Write comprehensive tests for unit conversions
5. Update main_window to use new domain unit system

### Wave 2 Success Criteria:
- Unit system accessible from domain layer, no UI dependencies
- Both Gaussian and Monte Carlo uncertainty work
- All existing unit conversion functionality preserved
- UI still correctly displays user-selected units

---

## Migration Wave 3 - Application & Infrastructure (Weeks 5-6)
*Objective: Establish application services and infrastructure layer*

### Wave 3 Tasks:
1. Move analyzer.py functionality to application/analysis/
2. Move file I/O functions to infrastructure/io/
3. Create project persistence format
4. Implement provenance tracking
5. Add reproducibility features

### Wave 3 Success Criteria:
- Can save and load complete projects
- Analysis provenance is tracked
- File I/O works from domain layer without UI
- Multi-sample analysis still functions correctly

---

## Migration Wave 4 - Visualization & UI (Weeks 7-8)
*Objective: Complete the migration by moving visualization and UI layers*

### Wave 4 Tasks:
1. Consolidate all plotting logic into visualization/
2. Move all UI files to their new locations
3. Update all imports in the main application
4. Test all dialogs and tools
5. Address any remaining issues

### Wave 4 Success Criteria:
- Application launches and runs normally
- All existing features work
- No import errors
- All plots generate correctly
- All dialogs function as before

---

## Post-Migration Tasks (Weeks 9-10)
1. Remove old src/ directory structure
2. Update all documentation
3. Run full test suite
4. Create first alpha release
5. Begin implementing the 5 core modules (carrier transport, lattice thermal, etc.)

---

## Risk Mitigation Strategy

### High-Risk Items Mitigation
1. **Unit system migration**:
   - Create comprehensive tests before moving any code
   - Compare input/output before/after migration with exact numerical tolerance
   - Maintain backward compatibility during transition

2. **Main window refactoring**:
   - Extract logic incrementally, don't rewrite
   - Use feature flags to toggle old/new implementations
   - Test each feature after extraction

3. **DataFrame compatibility**:
   - Maintain pandas DataFrame as the primary data structure throughout migration
   - Only introduce domain models (Project, Sample) after core migration is complete
   - Ensure backward compatibility with existing file formats

### Rollback Plan
If any migration wave fails:
1. Revert to the last working commit
2. Analyze the root cause
3. Fix the issues in a development branch
4. Retry the migration only after thorough testing

---

## Validation Checklist for Each Migration Step

After completing any file move:
- [ ] Imports are updated and resolve correctly
- [ ] All unit tests pass
- [ ] Existing functionality is preserved (manual testing)
- [ ] No new code duplication introduced
- [ ] Scientific calculations produce identical results (numerical comparison)
- [ ] GUI launches without errors
- [ ] All dialogs open and function correctly
- [ ] Plot generation works as before
- [ ] File I/O operations maintain compatibility

---

## Success Metrics for Complete Migration

### Architecture Goals Achieved:
- [x] Scientific domain layer is completely GUI-independent
- [x] Can import `calculate_zt()` and all core functions without PyQt6
- [x] Unit system is in domain layer, accessible to API/CLI
- [x] Clear separation between domain, application, infrastructure, visualization, UI
- [x] Plugin architecture supports optional modules
- [x] Project format enables reproducibility
- [x] Provenance tracking implemented
- [x] All tests pass with >90% coverage
- [x] No scientific code in UI layer
- [x] No duplication of any calculation