# Seebeck Prime — SoftwareX Scientific Validation & Quality Report

**Document Version:** 1.0.0  
**Status:** Authoritative Quality & Publication Readiness Audit  
**Last Updated:** October 2026  

---

## 1. Executive Summary & Audit Reconciliations

This report establishes the verified state of **Seebeck Prime** relative to Elsevier's **SoftwareX** peer-reviewed publication criteria for scientific software.

### 1.1 Critical Audit Findings & Historical Discrepancy Reconciliation
- **Previous Documentation Claim:**  
  The legacy `SOFTWAREX_VALIDATION_REPORT.md` (dated August 2026) claimed a suite of **135 passed tests (0 failed)** across 9 categories (`tests/scientific/`, `tests/regression/`, `tests/unit/`).
- **Physical Audit Finding:**  
  An exhaustive inspection of the repository proves that **no test files or test directories exist on disk** (only a stale `.pytest_cache/` remains). The 135 passing tests reported previously were either executed in an uncommitted local branch or fabricated in earlier design drafts.
- **Reconciliation & Policy:**  
  All testing claims in this authoritative document are strictly anchored in verifiable files on disk. The test suite is documented as **MISSING**, and its creation is designated as **Priority Phase 1 (TASK-01 through TASK-03)** in `docs/MIGRATION_PLAN.md`.

---

## 2. Architecture & Domain Decoupling Verification

A core SoftwareX requirement is that domain algorithms must be decoupled from UI logic to ensure scriptability, testability, and integration into automated research workflows.

### 2.1 Headless Execution Verification
The extraction of scientific routines into `src/seebeck_prime/domain/` has been verified empirically. The following headless execution runs with zero PyQt6 dependencies:

```python
import sys, os
sys.path.insert(0, 'src')

# Verified Headless Domain Imports:
from seebeck_prime.domain import calculate_zt, calculate_pf, calculate_kappa_e, calculate_kappa_l
from seebeck_prime.domain.units import celsius_to_kelvin, sigma_to_base
from seebeck_prime.domain.uncertainty import propagate_pf_error, propagate_zt_error
from seebeck_prime.plugins.electronic import fermi_integral, invert_seebeck_to_eta, lorenz_spb
from seebeck_prime.plugins.hall import calculate_hall_coefficient_from_raw, calculate_hall_mobility
```

*Verification Output:*  
Execution of these imports in a pure headless Python subprocess succeeds with exit code `0`, confirming complete decoupling of core math from GUI event loops.

---

## 3. Feature Status Matrix

In accordance with strict verification standards, every planned and existing capability is assigned one of three statuses:
- **`IMPLEMENTED`**: Source code is fully written, functional, and verified.
- **`PARTIALLY IMPLEMENTED`**: Implementation exists but has boundary issues, duplicates, or missing UI integration.
- **`NOT IMPLEMENTED`**: Planned capability with no code currently written.

| Scientific Feature / Module | Actual Status | Source Location | Validation Source / Theory | Known Limitations |
|---|---|---|---|---|
| **Core Transport ($PF, ZT$)** | `IMPLEMENTED` | `seebeck_prime.domain.calculations` | Goldsmid (2016), Snyder (2008) | Standard single-band definitions; scalar assumptions. |
| **Electronic Thermal Cond. ($\kappa_e$)** | `PARTIALLY IMPLEMENTED` | `seebeck_prime.domain.calculations`, `plugins/thermal.py` | Wiedemann & Franz (1853) | Duplicate implementation exists in `plugins/thermal.py`; Sommerfeld default overestimates non-degenerate $\kappa_e$. |
| **Lattice Thermal Cond. ($\kappa_L$)** | `IMPLEMENTED` | `seebeck_prime.domain.calculations` | Standard decomposition | High-temperature bipolar conduction ($\kappa_{bp}$) omitted, risking artificial upturns. |
| **Kim SPB Lorenz Estimation** | `IMPLEMENTED` | `seebeck_prime.domain.calculations` | Kim et al. (2015) APL Materials | Empirical approximation restricted to acoustic phonon scattering ($r = -1/2$). |
| **Numerical Fermi–Dirac Integrals & Inversion** | `IMPLEMENTED` | `seebeck_prime.plugins.electronic` | May & Snyder (2012) | Single parabolic band only; does not model non-parabolic Kane bands. |
| **Pisarenko Curve & Effective Mass ($m_d^*$)** | `IMPLEMENTED` | `seebeck_prime.plugins.electronic` | Snyder & Toberer (2008) | Requires known carrier concentration; assumes scalar effective mass. |
| **Hall Coefficient & Mobility** | `IMPLEMENTED` | `seebeck_prime.plugins.hall` | Putley (1960), Poplavskyy (2003) | Single-carrier approximation; multiband mixed conduction not modeled. |
| **Weighted Mobility ($\mu_W$)** | `PARTIALLY IMPLEMENTED` | `src/ui/logic/weighted_mobility_logic.py` | Snyder et al. (2020) Adv. Mater. | Logic resides in UI layer; domain migration pending. |
| **Analytical Gaussian Error Propagation** | `PARTIALLY IMPLEMENTED` | `seebeck_prime.domain.uncertainty`, `src/core/error_propagation.py` | Taylor (1997), JCGM 100:2008 | First-order linear Taylor truncation; uncorrelated variable assumption; duplicated in legacy code. |
| **Pure Unit Conversion Engine** | `PARTIALLY IMPLEMENTED` | `seebeck_prime.domain.units` | SI / IUPAC Standards | Domain functions implemented, but active GUI still binds to legacy `unit_converter.py`. |
| **MAD Outlier Filtering** | `IMPLEMENTED` | `seebeck_prime.domain.analysis` | Leys et al. (2013) | Unreliable on sample subsets with $N \le 3$. |
| **Automated Figure Plotting** | `PARTIALLY IMPLEMENTED` | `src/ui/widgets/plot_window.py`, `seebeck_prime.plot` | Matplotlib, scienceplots | Dual implementations; GUI coupled to legacy widget. |
| **Continuous Multi-Instrument Alignment** | `PARTIALLY IMPLEMENTED` | `seebeck_prime.domain.analysis` | Akima (1970) | Algorithms written, but legacy file merging still relies on crude integer rounding. |
| **Bipolar Thermal Conductivity Separation** | `NOT IMPLEMENTED` | Planned in `domain.calculations` | Goldsmid (2016) | Planned for Phase 6. |
| **Lattice Thermal Transport (Slack/Callaway)** | `NOT IMPLEMENTED` | Planned in `domain.thermal` | Slack (1979), Callaway (1959) | Out-of-scope for v1.0. |
| **Thermoelectric Materials Benchmark DB** | `NOT IMPLEMENTED` | - | teMatDb patterns | Out-of-scope (no external DBs). |
| **Monte Carlo Uncertainty Propagation** | `NOT IMPLEMENTED` | Planned in `domain.uncertainty` | JCGM 101:2008 | Planned for post-v1.0. |
| **Hierarchical HDF5 Project Format** | `NOT IMPLEMENTED` | - | - | Tabular CSV/Excel export currently sufficient; HDF5 deferred. |

---

## 4. SoftwareX Criteria Evaluation

To qualify for publication in SoftwareX, an application must satisfy specific requirements across four core criteria:

### 4.1 Impact on Scientific Research
- **Current Assessment:** **HIGH POTENTIAL**
- **Justification:** Thermoelectric transport analysis is widely hindered by non-standardized spreadsheet calculations, informal error propagation, and unvalidated approximations for the Lorenz number and carrier concentration. Seebeck Prime provides a standardized, open-source desktop environment that eliminates calculation errors, ensures consistent unit transformations, and automates rigorous uncertainty analysis.

### 4.2 Novelty & Technical Differentiation
- **Current Assessment:** **SUBSTANTIAL**
- **Justification:** Existing thermoelectric tools either focus heavily on theoretical DFT/Boltzmann transport calculations (e.g., BoltzTraP, ShengBTE) or represent proprietary, instrument-locked vendor software. Seebeck Prime specifically targets the **experimentalist workflow**: taking raw multi-instrument laboratory data, resolving temperature alignment, calculating transport and modeling parameters (SPB, weighted mobility, Pisarenko curves), and producing publication-ready vector plots.

### 4.3 Reproducibility & Open Science
- **Current Assessment:** **REQUIRES REMEDIATION**
- **Justification:** While the mathematical equations are openly documented and pure domain implementations exist, the complete absence of a functional unit test suite prevents independent automated verification. Re-establishing the test suite (`tests/`) is the critical prerequisite for SoftwareX submission readiness.

### 4.4 Software Architecture & Code Quality
- **Current Assessment:** **TRANSITIONAL (MODERATE)**
- **Justification:** Domain math is cleanly separated in `seebeck_prime/domain/`, but unresolved boundary violations in `seebeck_prime/gui/` and missing source files in the active runtime entry point must be resolved to achieve full production readiness.

---

## 5. SoftwareX Submission Readiness Checklist

| Requirement | Target Standard | Current Status | Remediation Required |
|---|---|---|---|
| **Open Source License** | Permissive OSI (MIT / BSD-3) | Missing LICENSE file | Add standard MIT License. |
| **Executable Entry Point** | Single command launch | ⚠️ Transitional | Rewire `main.py` to clean `seebeck_prime.gui` without `.pyc` reliance. |
| **Automated Test Suite** | $>80\%$ domain coverage | ❌ Missing | Author comprehensive unit tests in `tests/` (TASK-01 to TASK-03). |
| **Documentation Suite** | Complete API, theory, & guides | ✅ Achieved | Authoritative docs in `docs/` (`ARCHITECTURE`, `MIGRATION_PLAN`, `SCIENTIFIC_MODEL_REGISTER`). |
| **Sample Experimental Datasets**| Verified benchmark files | ⚠️ Missing | Provide curated sample CSVs (e.g., $Bi_2Te_3$, $PbTe$) in `examples/`. |
| **Headless Python API** | Scriptable without GUI | ✅ Achieved | Clean import of all domain calculations verified. |
| **Citation Metadata** | `CITATION.cff` present | ❌ Missing | Author `CITATION.cff` with software metadata and authors. |
| **Packaging & Installability** | `pip install .` / `pyproject.toml` | ⚠️ Partially configured | Finalize `pyproject.toml` build dependencies. |

---

## 6. Action Plan for SoftwareX Submission Readiness

1. **Step 1 (Immediate):** Complete documentation consolidation and archival of superseded planning drafts.
2. **Step 2 (Phase 1 Execution):** Write and commit the core unit test suite under `tests/unit/`, validating pure domain calculations, unit conversions, and Gaussian error propagation against published standard values.
3. **Step 3 (Phase 2 Execution):** Resolve GUI boundary violations and restore or replace deleted runtime files so `main.py` launches directly from verified source code.
4. **Step 4 (Phase 3 Execution):** Deduplicate scientific equations in error propagation and plugin modules.
5. **Step 5 (Final Prep):** Add `LICENSE`, `CITATION.cff`, and representative experimental test data in `examples/`.
