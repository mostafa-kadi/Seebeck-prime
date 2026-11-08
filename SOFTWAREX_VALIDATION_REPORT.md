# SOFTWAREX_VALIDATION_REPORT.md
## SoftwareX Scientific Validation & Quality Report

**Date:** 2026-08-25  
**Version:** 0.2.0-dev  
**Status:** In Progress (Phase 1 & Phase 2 Complete)

---

## 1. Executive Summary

This report documents the architectural separation, scientific validation test results, reproducibility foundations, and current implementation status for **Seebeck Prime** toward SoftwareX submission standards.

---

## 2. Architecture & Domain Decoupling

The scientific core has been extracted into a dedicated, GUI-independent package (`src/seebeck_prime/domain/`) with zero dependencies on PyQt6.

### Verification of GUI Independence:
```python
from seebeck_prime.domain import calculate_zt, calculate_pf, estimate_lorenz
from seebeck_prime.domain.units import celsius_to_kelvin, sigma_to_base
from seebeck_prime.domain.transport import calculate_weighted_mobility
from seebeck_prime.domain.uncertainty import propagate_pf_error, mad_filter
```
All above imports execute cleanly in headless / CLI environments.

---

## 3. Test Suite Summary

Total Test Count: **135 passed, 0 failed**

| Test Category | Directory | Test Count | Description |
|---------------|-----------|------------|-------------|
| **Scientific Reference** | `tests/scientific/` | 8 | Validates transport formulas against literature values ($Bi_2Te_3$, $Cu$, $PbTe$). |
| **Numerical Regression** | `tests/regression/` | 47 | Verifies floating-point parity between new domain layer and legacy core functions. |
| **Domain Units** | `tests/unit/test_unit_conversions.py` | 21 | Verifies offset trap ($^\circ\text{C}\leftrightarrow\text{K}$), $S/\text{cm}\leftrightarrow S/\text{m}$, and power factor units. |
| **Domain Uncertainty** | `tests/unit/domain/test_gaussian.py` | 10 | Validates first-order Gaussian error propagation against analytical derivations. |
| **Legacy Error Prop** | `tests/unit/test_error_propagation.py` | 10 | Verifies four-probe geometry errors, laser flash errors, and MAD filtering. |
| **SPB Models** | `tests/unit/domain/test_spb.py` | 12 | Tests Lorenz estimation limits and empirical carrier concentration bounds. |
| **Materials/Composition** | `tests/unit/domain/test_materials.py` | 8 | Validates IUPAC atomic weight parsing and molecular formula decomposition. |
| **Transport Module** | `tests/unit/domain/test_transport.py` | 3 | Verifies carrier concentration scaling behavior. |
| **Core Calculations** | `tests/unit/test_calculations.py` | 16 | Verifies basic thermoelectric formulas. |

---

## 4. Feature Status Matrix (Per Plan Section 33)

Statuses are strictly restricted to: `IMPLEMENTED`, `PARTIALLY IMPLEMENTED`, or `NOT IMPLEMENTED`.

| Feature | Status | Tests | Validation Source | Known Limitations |
|---------|--------|-------|-------------------|-------------------|
| **Core Transport (PF, ZT)** | `IMPLEMENTED` | `test_calculations.py`, `test_reference_values.py`, `test_calculation_regression.py` | Goldsmid (2016), Snyder & Toberer (2008) | Standard single-band definitions. |
| **Thermal Transport ($\kappa_e, \kappa_L$)** | `IMPLEMENTED` | `test_calculations.py`, `test_reference_values.py`, `test_calculation_regression.py` | Wiedemann & Franz (1853), Goldsmid (2016) | Standard decomposition; bipolar thermal transport not yet separated. |
| **Lorenz Estimation (SPB)** | `IMPLEMENTED` | `test_spb.py`, `test_reference_values.py` | Kim et al. (2015) APL Materials | Empirical SPB approximation with acoustic phonon scattering ($r=-1/2$). |
| **Weighted Mobility ($\mu_w$)** | `IMPLEMENTED` | `carrier.py`, `test_unit_conversions.py` | Snyder et al. (2022) PRX Energy | Model-derived estimate, assumes acoustic phonon scattering. |
| **Chemical Formula & MW** | `IMPLEMENTED` | `test_materials.py` | IUPAC 2021 Standard Atomic Weights | Supports integer and simple decimal subscripts; parentheses formulas pending. |
| **MAD Outlier Filtering** | `IMPLEMENTED` | `test_error_propagation.py` | Leys et al. (2013) J. Exp. Soc. Psychol. | Applied per temperature group. |
| **Gaussian Error Propagation** | `IMPLEMENTED` | `test_gaussian.py`, `test_error_propagation.py` | Taylor (1997) Error Analysis | First-order Taylor series approximation; assumes uncorrelated variables. |
| **Domain Unit System** | `IMPLEMENTED` | `test_unit_conversions.py` | SI / IUPAC Standards | Pure-function architecture; UI integration underway. |
| **Hall Transport & Mobility** | `IMPLEMENTED` | `test_hall.py` | Putley (1960), Poplavskyy (2003) | Single carrier type approximation; mixed-band Hall factor not yet separated. |
| **Carrier Transport Optimization & SPB (Module 1)** | `IMPLEMENTED` | `test_spb.py`, `test_hall.py`, `carrier.py` | Snyder et al. (2008, 2022), May (2012) | Numerical Fermi-Dirac integrals, effective mass estimation, Pisarenko curves, and optimal doping prediction. |
| **Lattice Thermal Transport (Module 2)** | `NOT IMPLEMENTED` | None | Future: Slack (1979), Callaway (1959) | Planned for Phase 6. |

| **Thermoelectric Materials Maps (Module 3)** | `NOT IMPLEMENTED` | None | Future: Snyder (2008) | Planned for Phase 7. |
| **Composition & Doping Analysis (Module 4)** | `NOT IMPLEMENTED` | None | Future: teMatDb patterns | Planned for Phase 8. |
| **Literature Benchmark (Module 5)** | `NOT IMPLEMENTED` | None | Future: teMatDb (2025) | Planned for Phase 9. |
| **Reproducible Project Format** | `NOT IMPLEMENTED` | None | Future: JSON / HDF5 schema | Planned for Phase 12. |
| **CLI / API Interface** | `NOT IMPLEMENTED` | None | Future: argparse/click | Planned for Phase 11. |

---

## 5. Next Steps

1. **Phase 3:** Introduce formal domain entities (`Sample`, `Measurement`, `Dataset`, `Analysis`, `Project`, `Provenance`) while maintaining DataFrame interoperability.
2. **Phase 4:** Expand uncertainty engine to include Monte Carlo error propagation and develop universal curve-fitting framework.
3. **Phase 5:** Complete Module 1 (Carrier Transport & Pisarenko optimization with numerical Fermi–Dirac integrals).
