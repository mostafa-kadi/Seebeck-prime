# SCIENTIFIC_FUNCTION_MAP.md
## Seebeck Prime Scientific Function Inventory

**Date:** 2026-08-24
**Status:** Complete

This document inventories all scientific calculations, their locations, dependencies, and migration plans to the target architecture.

---

## 1. Core Transport Calculations

| Function | Current Location | Formula | Scientific Reference | Target Location | Migration Risk |
|----------|-----------------|---------|---------------------|-----------------|----------------|
| `calculate_pf()` | `src/core/calculations.py` | PF = S² * σ | Standard thermoelectric theory | `src/seebeck_prime/domain/calculations/transport.py` | Low |
| `calculate_kappa_e()` | `src/core/calculations.py` | κₑ = L * σ * T (Wiedemann-Franz law) | Wiedemann, G. & Franz, R. (1853) | `src/seebeck_prime/domain/calculations/thermal.py` | Low |
| `calculate_kappa_l()` | `src/core/calculations.py` | κₗ = κ_total - κₑ | Standard decomposition | `src/seebeck_prime/domain/calculations/thermal.py` | Low |
| `calculate_zt()` | `src/core/calculations.py` | ZT = PF * T / κ_total | Goldsmid, H.J. (2016) - Applications of Thermoelectricity | `src/seebeck_prime/domain/calculations/transport.py` | Low |
| `estimate_lorenz())` | `src.code.calculations.py` | L = (1.5 + exp(-|S|/116.0)) * 1e-8 | Single Parabolic Band (SPB) model | `src/seebeck_prime/domain/models/spb.py` | Low |

---

## 2. Error Propagation Functions

| Function | Current Location | Formula | Reference | Target Location | Migration Risk |
|----------|-----------------|---------|-----------|-----------------|----------------|
| `calculate_pf_error()` | `src/core/error_propagation.py` | Gaussian propagation for PF | Taylor, J.R. (1997) - Introduction to Error Analysis | `src/seebeck_prime/domain/uncertainty/gaussian.py` | Medium |
| `calculate_kappa_e_error()` | `src/core/error_propagation.py` | Gaussian propagation for κₑ | Taylor, J.R. (1997) | `src/seebeck_prime/domain/uncertainty/gaussian.py` | Medium |
| `calculate_kappa_l_error()` | `src/core/error_propagation.py` | Gaussian propagation for κₗ | Taylor, J.R. (1997) | `src/seebeck_prime/domain/uncertainty/gaussian.py` | Medium |
| `calculate_zt_error()` | `src/core/error_propagation.py` | Gaussian propagation for ZT | Taylor, J.R. (1997) | `src/seebeck_prime/domain/uncertainty/gaussian.py` | Medium |
| `mad_filter()` | `src/core/error_propagation.py` | Median Absolute Deviation outlier filtering | Leys, C. et al. (2013) - Journal of Experimental Social Psychology | `src/seebeck_prime/domain/uncertainty/filtering.py` | Medium |

---

## 3. Analysis Engine Functions

| Function | Current Location | Purpose | Target Location | Migration Risk |
|----------|-----------------|---------|-----------------|----------------|
| `process_sample_data()` | `src/core/analyzer.py` | Process single sample dataframe, calculate all properties | `src/seebeck_prime/application/analysis/single_sample.py` | Medium |
| `run_multi_sample_analysis()` | `src/core/analyzer.py` | Process and compare multiple samples | `src/seebeck_prime/application/analysis/multi_sample.py` | Medium |
| `plot_comparisons()` | `src/core/analyzer.py` | Generate overlaid comparison plots | `src/seebeck_prime/visualization/plots/multi_sample.py` | High (currently imports matplotlib in core) |

---

## 4. Materials Calculations

| Function | Current Location | Purpose | Reference | Target Location | Migration Risk |
|----------|-----------------|---------|-----------|-----------------|----------------|
| `calculate_molecular_weight()` | `src/core/calculations.py` | Parse chemical formula, calculate molecular weight | IUPAC atomic weights | `src/seebeck_prime/domain/materials/composition.py` | Low |

---

## 5. Tool-Specific Scientific Logic

### Weighted Mobility Module
| Function | Current Location | Purpose | Reference | Target Location | Migration Risk |
|----------|-----------------|---------|-----------|-----------------|----------------|
| Weighted mobility calculations | `src/ui/logic/weighted_mobility_logic.py` | Calculate μw from Snyder et al. | Snyder, G.J. et al. (2016) - Weighted mobility | `src/seebeck_prime/domain/transport/carrier.py` | High (currently in UI logic, needs to move to domain) |

### Device Efficiency Module
| Function | Current Location | Purpose | Reference | Target Location | Migration Risk |
|----------|-----------------|---------|-----------|-----------------|----------------|
| Engineering ZT calculations | `src/ui/logic/device_efficiency_logic.py` | Calculate ZT_eng, device efficiency | Snyder, G.J. (2014) - Energy efficiency of thermoelectric devices | **Note: Deprioritized per plan - this device-focused module will be moved to an optional plugin** | N/A |

### Thermal Conductivity (Kappa) Module
| Function | Current Location | Purpose | Reference | Target Location | Migration Risk |
|----------|-----------------|---------|-----------|-----------------|----------------|
| LFA data processing | `src/ui/logic/kappa_logic.py` | Process laser flash data, κ = α*Cp*ρ | Parker, W.J. et al. (1961) - Flash method for thermal diffusivity | `src/seebeck_prime/domain/thermal/lfa.py` | High (currently in UI logic) |

---

## 6. Unit Conversion Functions

| Unit Type | Current Location | Conversions Handled | Target Location | Migration Risk |
|-----------|-----------------|---------------------|-----------------|----------------|
| Temperature | `src/ui/logic/unit_converter.py` | K ↔ °C | `src/seebeck_prime/domain/units/temperature.py` | High (UI-only currently) |
| Electrical Conductivity | `src/ui/logic/unit_converter.py` | S/cm ↔ S/m ↔ Ω·cm | `src/seebeck_prime/domain/units/transport.py` | High (UI-only currently) |
| Power Factor | `src/ui/logic/unit_converter.py` | mW/mK² ↔ μW/mK² ↔ W/mK² | `src/seebeck_prime/domain/units/transport.py` | High (UI-only currently) |
| Thermal Conductivity | (hardcoded) | W/mK base only | `src/seebeck_prime/domain/units/thermal.py` | Medium |
| Seebeck Coefficient | (hardcoded) | μV/K ↔ V/K | `src/seebeck_prime/domain/units/transport.py` | Medium |

---

## 7. File Processing Functions

| Function | Current Location | Purpose | Target Location | Migration Risk |
|----------|-----------------|---------|-----------------|----------------|
| `process_four_probe()` | `src/core/error_propagation.py` | Process four-probe resistivity data | Standard measurement protocol | `src/seebeck_prime/infrastructure/io/four_probe.py` | Medium |
| `process_raw_seebeck()` | `src/core/error_propagation.py` | Process raw Seebeck ΔV/ΔT data | Standard measurement protocol | `src/seebeck_prime/infrastructure/io/seebeck.py` | Medium |
| `_read_file()` | `src/core/error_propagation.py` | Generic Excel/CSV reader | `src/seebeck_prime/infrastructure/io/common.py` | Low |

---

## 8. All Duplicated Scientific Code

### Inline Duplicates Found
1. **kappa_e calculation** - `src/core/error_propagation.py` line 496
   - Current: `df["kappa_e"] = L_vals * df["sigma"] * df["T_K"]`
   - Should use: `calculate_kappa_e()` from core
   - Fix: **Immediate** - affects scientific consistency

2. **ZT calculation** - `src/core/error_propagation.py` line 506
   - Current: `df["ZT"] = df["PF"] * df["T_K"] / df["kappa"]`
   - Should use: `calculate_zt()` from core
   - Fix: **Immediate** - affects scientific consistency

3. **PF error calculation duplication** - None found, but error functions are not centralized
   - Plan: Move all error calculations to unified uncertainty module

---

## 9. Missing Scientific Functions (Required for Target Modules)

### Module 1 - Carrier Transport & Materials Optimization (P0)
- [ ] `calculate_spb_parameters()` - SPB model effective mass calculation
- [ ] `calculate_pisarenko_relationship()` - α-lnσ transport relation
- [ ] `estimate_optimal_carrier_concentration()` - Predict optimal n for maximum PF
- [ ] `calculate_weighted_mobility()` - μw calculation (currently in UI logic)

### Module 2 - Lattice Thermal Transport (P0)
- [ ] `calculate_slack_model()` - Slack's κL estimation
- [ ] `calculate_debye_callaway()` - Debye-Callaway phonon scattering
- **Requires**: Separate scattering contribution functions (boundary, point-defect, Umklapp, alloy)

### Module 3 - Materials Maps (P0)
- [ ] Generic composition-property mapping functions
- [ ] Trend analysis and peak detection algorithms

### Module 4 - Composition and Doping Analysis (P1)
- [ ] Doping trend analysis
- [ ] Experimental optimum identification

### Module 5 - Literature Benchmark (P1)
- [ ] Data consistency checking (recalculate ZT from literature values)
- [ ] Cross-sample comparison statistics

---

## 10. Implementation Priorities for Scientific Functions

| Priority | Task | Timeline |
|----------|------|----------|
| **CRITICAL** | Fix duplicated calculations in error_propagation.py | Immediate |
| HIGH | Move weighted mobility logic from UI to domain layer | Week 1 |
| HIGH | Move kappa/LFA logic from UI to domain/thermal | Week 1 |
| HIGH | Create unit module in domain, move all unit conversions | Week 2 |
| MEDIUM | Implement SPB/Pisarenko calculations for carrier transport | Week 3 |
| MEDIUM | Implement Slack/Debye-Callaway for lattice thermal transport | Week 4 |
| MEDIUM | Create uncertainty module with Gaussian + Monte Carlo | Week 5 |
| LOW | Add literature benchmark database functions | Future |

---

## 11. Scientific References to Track

All scientific calculations must include proper citations. The following references need to be embedded in the code documentation:

1. **Goldsmid, H.J.** - Applications of Thermoelectricity (2016) - foundational ZT theory
2. **Snyder, G.J. & Toberer, E.S.** - Complex thermoelectric materials (2008) - SPB model
5. **Taylor, J.R.** - Introduction to Error Analysis (1997) - uncertainty propagation
4. **Parker, W.J. et al.** - Flash method for thermal diffusivity measurements (1961) - LFA theory
3. **Snyder, G.J. et al.** - Weighted mobility (2016) - μw calculations
6. **Leys, C. et al.** - Detecting outliers: Do not use standard deviation around the mean, use absolute deviation around the median (2013) - MAD filtering