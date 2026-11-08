# Seebeck Prime — Authoritative Migration Plan

**Document Version:** 1.0.0  
**Status:** Authoritative Implementation Roadmap  
**Last Updated:** October 2026  

---

## 1. Executive Summary & Strategy

This document provides the definitive, evidence-based migration plan for transitioning **Seebeck Prime** from its legacy transitional state into a clean, modular, and scientifically rigorous architecture. 

### 1.1 Guiding Principles
1. **Incremental Transitions:** Follow the strict sequence: **Inspect $\rightarrow$ Test $\rightarrow$ Refactor $\rightarrow$ Retest $\rightarrow$ Document**.
2. **Preserve User Workflows:** Do not disrupt working desktop workflows (spreadsheet data entry, clipboard pasting from Origin/Excel, automated multi-window plotting).
3. **No Hidden Breakers:** Never delete or alter legacy functions until drop-in domain replacements are verified and callers updated.
4. **Single Source of Scientific Truth:** Every equation must exist in exactly one location in the domain layer.

---

## 2. Verified Current Issues Inventory

Every issue listed below has been verified against actual filesystem contents and source code.

| Issue ID | Description | Actual File Path | Supporting Evidence & Impact | Risk | Proposed Fix | Status |
|---|---|---|---|---|---|---|
| **ISS-01** | Live entry point imports missing source file | `main.py` | Line 33 imports `from src.ui.main_window import ThermoelectricApp`. Source file `src/ui/main_window.py` is deleted; runtime relies on stale `.pyc`. High breakage risk. | 🔴 High | Point `main.py` to the consolidated GUI entry point in `seebeck_prime.gui.main_window` once boundary issues are resolved. | **VERIFIED** |
| **ISS-02** | Active source files deleted in working directory | `src/ui/widgets/table_widget.py`, `src/core/constants.py`, `src/core/error_propagation.py` | Git status flags `D` on these files. Python only executes them if `.pyc` exists in `__pycache__`. If bytecode is purged, application crashes immediately. | 🔴 High | Restore working source versions or verify complete replacement in `seebeck_prime/domain/` and `seebeck_prime/gui/`. | **VERIFIED** |
| **ISS-03** | Parallel disconnected architectures with boundary violations | `src/seebeck_prime/gui/main_window.py`, `dialogs.py`, `plotter.py` | `src/seebeck_prime/gui/main_window.py` lines 30-38 import legacy `src.ui.widgets.*` and `src.ui.dialogs.*`. The parallel package cannot run independently. | 🔴 High | Decouple `seebeck_prime.gui` from legacy `src.ui`, redirecting all internal dependencies to domain and local widgets. | **VERIFIED** |
| **ISS-04** | Complete absence of test suite on disk | Repository root (`tests/`) | Documentation claimed 135 passed tests across 9 categories. Inspection proves `tests/` directory is entirely absent. No automated regression protection exists. | 🔴 High | Author foundational test suite in `tests/` covering unit conversions, core calculations, SPB approximations, and error propagation. | **VERIFIED** |
| **ISS-05** | Duplicate implementations of core transport equations | `src/core/error_propagation.py`, `src/seebeck_prime/plugins/thermal.py` | Inline duplicate equations: $\kappa_e = L \sigma T$ and $ZT = PF \cdot T / \kappa$ are re-coded inline in error propagation and plugin thermal, bypassing `calculate_kappa_e` and `calculate_zt`. | 🟡 Medium | Refactor all error and plugin modules to import and invoke `seebeck_prime.domain.calculations` exclusively. | **VERIFIED** |
| **ISS-06** | Unit conversion coupled to PyQt6 GUI | `src/ui/logic/unit_converter.py` | Unit conversions are wrapped in GUI-dependent helper functions. Headless domain code cannot use them without Qt. Pure conversions already exist in `seebeck_prime/domain/units.py`. | 🟡 Medium | Migrate all application and UI code to call `seebeck_prime.domain.units` directly, deprecating `src/ui/logic/unit_converter.py`. | **VERIFIED** |
| **ISS-07** | Temperature alignment uses crude binning | `src/core/error_propagation.py` | Alignment between four-probe resistivity and laser flash thermal data uses `round(1)` or $T/20$ bins, discarding valid data and introducing scatter. | 🟡 Medium | Implement continuous interpolation (linear / Akima spline) with explicit temperature boundary checking in `domain.analysis`. | **VERIFIED** |
| **ISS-08** | Unvalidated empirical carrier concentration approximation | `src/seebeck_prime/domain/models/spb.py` / `plugins/electronic.py` | Formula $n \approx 10^{21} \exp(-|S| / 43.4)$ is an empirical approximation for non-degenerate acoustic phonon scattering, but is presented without regime warnings. | 🟡 Medium | Add explicit warning labels `(Empirical SPB Estimate)` and implement numerical Fermi-Dirac integral inversion. | **VERIFIED** |
| **ISS-09** | Bipolar thermal conductivity omission | `src/seebeck_prime/domain/calculations.py` | Lattice thermal conductivity is computed as $\kappa_L = \kappa - \kappa_e$. High-temperature bipolar conduction ($\kappa_{bp}$) is omitted, causing artificial $\kappa_L$ upturns. | 🟡 Medium | Document limitation in model register, flag high-temperature upturns, and prepare bipolar separation model. | **VERIFIED** |

---

## 3. Prioritized Migration Tasks

Tasks are ordered strictly by engineering dependency and scientific risk:

```text
Phase 1: Test Suite & Baseline Regression Protection
    ↓
Phase 2: Source File Integrity & Entry Point Stabilization
    ↓
Phase 3: Scientific Calculation Deduplication
    ↓
Phase 4: Unit Conversion & Validation Consolidation
    ↓
Phase 5: Data Registry & UI Coupling Refactor
    ↓
Phase 6: Multi-Instrument Alignment & Scientific Modeling Enhancements
```

### Phase 1: Test Suite & Baseline Regression Protection
- **TASK-01 (Regression Baseline):**  
  *Target:* Create `tests/unit/` and author comprehensive unit tests for `seebeck_prime.domain.calculations` (PF, $\kappa_e$, $\kappa_L$, $ZT$, Kim Lorenz, molecular weight). Validate against published reference materials ($Bi_2Te_3$, $PbTe$, $Cu$).  
  *Risk:* 🟢 Low (Additive only).  
  *Status:* PROPOSED.
- **TASK-02 (Unit Conversion Test Harness):**  
  *Target:* Author tests for `seebeck_prime.domain.units` covering temperature offset traps ($^\circ\text{C} \leftrightarrow \text{K}$), electrical conductivity ($S/\text{cm} \leftrightarrow S/\text{m}$), and power factor scalings.  
  *Risk:* 🟢 Low.  
  *Status:* PROPOSED.
- **TASK-03 (Gaussian Uncertainty Tests):**  
  *Target:* Author tests in `tests/unit/test_uncertainty.py` verifying first-order Taylor series error propagation against analytical derivations.  
  *Risk:* 🟢 Low.  
  *Status:* PROPOSED.

### Phase 2: Source File Integrity & Runtime Stabilization
- **TASK-04 (Source File Restoration & Verification):**  
  *Target:* Re-establish tracked source files for critical deleted modules (`table_widget.py`, `main_window.py`) by either restoring from git history or validating that their implementations in `seebeck_prime.gui` are fully functional and complete.  
  *Risk:* 🔴 High. Requires careful validation against live GUI execution.  
  *Status:* PROPOSED.
- **TASK-05 (Boundary Violation Elimination):**  
  *Target:* Clean all reverse imports in `src/seebeck_prime/gui/main_window.py`, `dialogs.py`, and `plotter.py` so they reference local `seebeck_prime.*` modules rather than legacy `src.ui.*`.  
  *Risk:* 🟡 Medium.  
  *Status:* PROPOSED.
- **TASK-06 (Unified Entry Point Rewiring):**  
  *Target:* Update `main.py` to import `ThermoelectricApp` directly from `seebeck_prime.gui.main_window`. Verify clean launch and UI functionality.  
  *Risk:* 🟡 Medium. Depends on TASK-04 and TASK-05.  
  *Status:* PROPOSED.

### Phase 3: Scientific Calculation Deduplication
- **TASK-07 (Deduplicate Error Propagation Calculations):**  
  *Target:* Replace duplicate inline calculations of $\kappa_e$ and $ZT$ in `src/core/error_propagation.py` with calls to `seebeck_prime.domain.calculations`.  
  *Risk:* 🟢 Low. Validated by TASK-01 and TASK-03.  
  *Status:* PROPOSED.
- **TASK-08 (Consolidate Thermal Plugins):**  
  *Target:* Consolidate `src/seebeck_prime/plugins/thermal.py` into `seebeck_prime.domain.calculations` to eliminate duplicate Wiedemann-Franz definitions.  
  *Risk:* 🟢 Low.  
  *Status:* PROPOSED.

### Phase 4: Unit Conversion & Validation Consolidation
- **TASK-09 (Migrate UI to Domain Units):**  
  *Target:* Refactor `src/ui/logic/table_handler.py` and GUI dialogs to import and execute conversions from `seebeck_prime.domain.units`.  
  *Risk:* 🟡 Medium. Must verify table column display units and clipboard paste formatting.  
  *Status:* PROPOSED.
- **TASK-10 (Input Domain Validation):**  
  *Target:* Integrate `seebeck_prime.domain.validation` into data loading pipelines to detect physical impossibilities ($T \le 0\text{ K}$, $\kappa \le 0$, negative absolute conductivity) before calculations run.  
  *Risk:* 🟢 Low.  
  *Status:* PROPOSED.

### Phase 5: Data Registry & UI Decoupling
- **TASK-11 (Dataset Abstraction Wiring):**  
  *Target:* Connect `seebeck_prime.domain.dataset.ThermoelectricDataset` as the backing store for tabular application state, maintaining bidirectional synchronization with pandas DataFrame.  
  *Risk:* 🟡 Medium.  
  *Status:* PROPOSED.
- **TASK-12 (Centralize Plotting Service):**  
  *Target:* Connect `seebeck_prime.plot.plotter` to `PlotWindow`, ensuring standard Matplotlib figure export (PDF, PNG, SVG) operates consistently across all analysis dialogs.  
  *Risk:* 🟢 Low.  
  *Status:* PROPOSED.

### Phase 6: Multi-Instrument Alignment & Scientific Modeling
- **TASK-13 (Interpolation-Based Temperature Grid Alignment):**  
  *Target:* Replace discrete rounding/binning in multi-instrument merging with continuous interpolation (Akima/linear) and explicit extrapolation warnings.  
  *Risk:* 🟡 Medium.  
  *Status:* PROPOSED.
- **TASK-14 (Fermi-Dirac Numerical Inversion):**  
  *Target:* Implement complete Fermi-Dirac integral solver $F_j(\eta)$ with root-finding to compute reduced Fermi level $\eta$ from Seebeck coefficient, providing a rigorous alternative to the empirical SPB carrier concentration approximation.  
  *Risk:* 🟡 Medium.  
  *Status:* PROPOSED.
- **TASK-15 (Bipolar Thermal Conduction Flagging):**  
  *Target:* Add automated detection in `domain.calculations.calculate_kappa_l` to flag anomalous high-temperature upturns as suspected bipolar conduction ($\kappa_{bp}$).  
  *Risk:* 🟢 Low.  
  *Status:* PROPOSED.

---

## 4. Explicitly Out-of-Scope Tasks

To maintain focus and avoid scope creep, the following items are formally declared **out of scope**:

1. **Density Functional Theory (DFT) Implementation:** No electronic structure codes, pseudopotentials, or plane-wave solvers will be built.
2. **Automated Literature Scraping / Web Search:** No web crawlers or external database search plugins will be embedded.
3. **GPU / Distributed Computing Architecture:** No CUDA, OpenCL, MPI, or Celery task queues. The platform must run on consumer PC hardware.
4. **Cloud / Client-Server Backend:** The application is a standalone desktop application; no client-server databases (SQL servers, REST microservices) are permitted.
5. **GUI Framework Migration:** Do not attempt migration away from PyQt6 (e.g., to web frameworks, Electron, or alternative GUI toolkits).
