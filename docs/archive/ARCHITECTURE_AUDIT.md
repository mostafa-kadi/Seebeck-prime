# ARCHITECTURE_AUDIT.md
## Seebeck Prime Repository Audit - Phase 0

**Date:** 2026-08-24
**Status:** Complete

---

## Executive Summary
The current codebase has a solid foundation with good separation of concerns, but has several areas that need refactoring to meet the target architecture requirements. The core scientific calculations are mostly centralized, but there is critical code duplication in error propagation, and the domain layer is not yet fully GUI-independent.

---

## 1. Current Architecture Map

### Existing Directory Structure
```
Seebeck-Prime/
├── main.py                          # Application entry point
├── requirements.txt                 # Dependencies
├── README.md                        # Documentation
└── src/
    ├── __init__.py
    ├── core/                        # Scientific calculation engine
    │   ├── __init__.py
    │   ├── calculations.py          # Basic thermoelectric formulas
    │   ├── analyzer.py              # Multi-sample analysis engine
    │   ├── constants.py             # Physical constants, atomic weights
    │   └── error_propagation.py     # Gaussian error propagation system
    ├── ui/                          # Complete UI layer
    │   ├── __init__.py
    │   ├── main_window.py           # Main application window
    │   ├── widgets/                 # Reusable custom widgets
    │   ├── dialogs/                 # All modal dialogs/tools
    │   └── logic/                   # UI business logic
```

---

## 2. Scientific Calculations - Inventory

### Centralized Core Calculations (GOOD)
All base calculations are defined in `src/core/calculations.py`:
- `calculate_pf()` - Power Factor (S² * σ)
- `calculate_kappa_e()` - Electronic thermal conductivity (L*σ*T)
- `calculate_kappa_l()` - Lattice thermal conductivity
- `calculate_zt()` - Figure of Merit (PF*T/κ)
- `estimate_lorenz()` - Seebeck-derived Lorenz number (SPB model)
- `calculate_molecular_weight()` - Parse chemical formulas

These are imported and used correctly in:
- `src/ui/main_window.py` - ✅ Uses `calc.calculate_*()` functions
- `src/core/analyzer.py` - ✅ Imports and uses core calculations

### Duplicated Calculations (CRITICAL - needs fixing)
**Found in `src/core/error_propagation.py` lines 496, 506:**
```python
# Line 496: Duplicate kappa_e calculation
df["kappa_e"] = L_vals * df["sigma"] * df["T_K"]  # Should use calculate_kappa_e()

# Line 506: Duplicate ZT calculation  
df["ZT"] = df["PF"] * df["T_K"] / df["kappa"]     # Should use calculate_zt()
```

These inline calculations duplicate the core functions, creating maintenance risk. If the core formulas are updated, the error propagation calculations would become inconsistent.

### Additional Standalone Calculations
Error calculation functions exist in the same file:
- `calculate_pf_error()`
- `calculate_kappa_e_error()`
- `calculate_kappa_l_error()`
- `calculate_zt_error()`

These are scientifically sound but should be moved into the domain/uncertainty module.

---

## 3. UI/Business-Logic Coupling Analysis

### Good Separation (Mostly Compliant)
- **Core layer is GUI-independent**: `src/core/` does not import PyQt6 - ✅
- **UI logic is separated**: `src/ui/logic/` contains orchestration code
- **Widgets are decoupled**: Custom widgets in `src/ui/widgets/` are reusable

### Coupling Issues Found

1. **Main window contains calculation orchestration**:
   - `src/ui/main_window.py` line 284-310: `recalculate_all_properties()` directly calls core calculations. This is acceptable for now but should eventually move to an application service.

2. **Unit conversion is UI-only**:
   - Unit conversion logic exists only in `src/ui/logic/unit_converter.py`
   - Violates requirement: "Unit system must move to domain layer"
   - Currently, you cannot use the unit conversion system without importing UI modules

3. **Error propagation has incomplete imports**:
   - In `error_propagation.py` line 491, it imports `estimate_lorenz` inline only when needed:
     ```python
     from .calculations import estimate_lorenz
     ```
   - This is a code smell - should be at the top of the file

---

## 4. Data Flow Analysis

### Single Source of Truth Pattern (Working Correctly)
✅ **The pandas DataFrame pattern is implemented correctly in main_window.py**:
- `self.data` is the only source of truth for all sample data
- User input → convert to base units → update DataFrame → recalculate → update display
- Unit conversions are handled transparently between storage (base SI) and display

### Data Flow Issues
1. **Error propagation creates separate DataFrames**:
   - The `ThermoelectricAnalyzer` class creates its own DataFrames that are not integrated with the main application's data model
   - Creates data duplication and synchronization challenges

2. **Multi-sample analysis creates independent data structures**:
   - `run_multi_sample_analysis()` in analyzer.py operates on dictionary of DataFrames
   - Not integrated with the proposed Project/Sample domain model

---

## 5. Dependencies Analysis

### Current Dependencies (requirements.txt)
```
PyQt6                    # GUI framework - only in UI layer, correct
pandas                   # Data manipulation - used throughout, acceptable
numpy                    # Numerical calculations - domain layer, correct
matplotlib               # Plotting - visualization layer, correct
qtawesome                # Icons - UI only, correct
scienceplots             # Plot styles - visualization layer, correct
openpyxl                 # Excel I/O - infrastructure layer, correct
```

### Dependency Issues Found
1. **matplotlib imported in core files**:
   - `src/core/analyzer.py` imports `matplotlib.pyplot` - violates domain layer purity
   - Plotting should only happen in visualization layer, not core domain

2. **No dependency organization**:
   - Dependencies are not split into: core, UI, development, testing
   - Missing test dependencies: pytest, pytest-cov, etc.

---

## 6. State Management Analysis

### Good State Management
✅ Main application state is centralized in `ThermoelectricApp`:
- `self.data` - main DataFrame
- `self.units` - current display units
- `self.error_mode` - error bar toggle
- `self.uncertainties` - uncertainty configuration
- `self.current_file_path` - currently open file
- `self.plot_windows` - tracks open plot windows

### State Management Issues
1. **Dialogs manage their own state independently**:
   - Each dialog (kappa_dialog, multi_sample_dialog, etc.) maintains its own state
   - No centralized state management for analysis sessions

2. **No session persistence**:
   - Cannot save an analysis session and reproduce it later
   - Missing provenance tracking as required by the plan

---

## 7. Current Tests Status

🚨 **CRITICAL: No test files exist in the repository**
- No unit tests
- No scientific validation tests
- No integration tests
- No regression tests
- This is the highest priority item to address

---

## 8. File I/O Analysis

### Good File Handling
- `src/ui/logic/file_handler.py` abstracts file I/O operations
- Supports Excel and CSV import/export
- Error handling for file operations is basic but functional

### I/O Issues
1. **File I/O is trapped in UI logic**:
   - Cannot use file handling functions without importing UI modules
   - Should move to infrastructure/io layer

2. **No project file format**:
   - Cannot save a complete project with all metadata, only data tables
   - Missing the reproducible project structure defined in the plan

---

## 9. Plotting Analysis

### Good Plotting Architecture
- `src/ui/widgets/plot_window.py` embeds matplotlib correctly
- `src/ui/logic/plot_handler.py` contains plot creation logic
- `scienceplots` used for publication-quality figures

### Plotting Issues
1. **Plotting logic split between multiple files**:
   - Plot creation in `main_window.py.create_plot()`
   - Plot logic in `plot_handler.py`
   - Multi-sample plotting in `analyzer.py.plot_comparisons()`
   - Creates code duplication in plotting logic

2. **Core layer imports matplotlib**:
   - As mentioned earlier, `analyzer.py` imports pyplot, violating separation

---

## 10. Uncertainty/Error Propagation Analysis

### Good Foundation
✅ The uncertainty engine has strong fundamentals:
- MAD (Median Absolute Deviation) outlier filtering
- Gaussian error propagation
- Handles both simple percentage errors and file-based rigorous errors
- Processes raw measurement files (four-probe, LFA, Seebeck)

### Uncertainty Engine Issues
1. **Code duplication in calculations** (as documented earlier)
2. **Error functions are standalone**: Should be part of a unified uncertainty module
3. **Only supports Gaussian propagation**: Plan requires adding Monte Carlo propagation
4. **Cannot track model uncertainty**

---

## 11. Summary of Critical Issues to Address

| Issue | Severity | Location | Impact |
|-------|----------|----------|--------|
| No tests exist | CRITICAL | Entire codebase | Cannot validate scientific correctness |
| Duplicated calculations | HIGH | error_propagation.py | Risk of inconsistent calculations |
| matplotlib in core | HIGH | analyzer.py | Violates domain layer GUI-independence |
| Unit conversion only in UI | MEDIUM | unit_converter.py | Cannot use units outside GUI |
| File I/O in UI logic | MEDIUM | file_handler.py | Cannot use I/O outside GUI |
| Plotting logic duplicated | MEDIUM | Multiple files | Maintenance overhead |
| No project persistence | MEDIUM | N/A | Cannot implement reproducibility |

---

## 12. Recommendations for Next Steps

1. **Immediate (Phase 1)**:
   - Fix duplicated calculations in error_propagation.py to use core functions
   - Remove matplotlib import from analyzer.py, move plotting to visualization layer
   - Create tests directory and add first unit tests for core calculations
   - Add pytest and other test dependencies to requirements

2. **Short-term**:
   - Move unit_converter.py to domain/units/
   - Move file_handler.py to infrastructure/io/
   - Create the domain model classes (Project, Sample, Material, etc.)
   - Start implementing ARCHITECTURE_MIGRATION_MAP.md

3. **Long-term**:
   - Implement the project persistence format
   - Add Monte Carlo uncertainty propagation
   - Create the plugin architecture for the 5 core modules