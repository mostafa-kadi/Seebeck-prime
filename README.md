# Seebeck Prime

**Seebeck Prime** is an open-source, reproducible scientific analysis platform designed for thermoelectric materials research. It automates the calculation of transport properties, performs rigorous analytical and statistical error propagation, provides advanced interactive plotting, and models electronic and thermal transport mechanisms.

---

## Authoritative Project Documentation

For architecture decisions, verified migration tasks, physical equations, and publication validation, consult the authoritative documentation in [`docs/`](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs):

1. **[System Architecture (`docs/ARCHITECTURE.md`)](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/ARCHITECTURE.md)**  
   System boundary definitions, live codebase layout, target architecture, Central Data Registry design, and strict architectural constraints (no DFT, no web scrapers, PC-practical).
2. **[Migration Plan (`docs/MIGRATION_PLAN.md`)](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/MIGRATION_PLAN.md)**  
   Comprehensive inventory of verified codebase issues, prioritized 6-phase engineering roadmap, and out-of-scope boundaries.
3. **[Scientific Model Register (`docs/SCIENTIFIC_MODEL_REGISTER.md`)](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/SCIENTIFIC_MODEL_REGISTER.md)**  
   Definitive scientific catalog covering governing formulas, input/output units, physical assumptions, limitations, and literature citations for core transport ($PF, \kappa_e, \kappa_L, ZT$), carrier models (Hall, weighted mobility, SPB, Pisarenko), and uncertainty propagation.
4. **[SoftwareX Scientific Validation Report (`docs/SOFTWAREX_VALIDATION_REPORT.md`)](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/SOFTWAREX_VALIDATION_REPORT.md)**  
   Empirical audit of headless domain decoupling, reconciliation of previous test claims, feature status matrix, and submission readiness roadmap.
5. **[Documentation Archive (`docs/archive/README.md`)](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/archive/README.md)**  
   Historical planning drafts, Phase 0 audits, and migration maps preserved for traceability.

---

## Table of Contents
- [Getting Started](#getting-started)
- [Headless Python API](#headless-python-api)
- [Data Entry & Processing](#data-entry--processing)
- [Error Propagation & Uncertainty Analysis](#error-propagation--uncertainty-analysis)
- [Analysis Tools](#analysis-tools)
    - [Thermal Conductivity (Kappa) Tool](#thermal-conductivity-kappa-tool)
    - [Device Efficiency Calculator](#device-efficiency-calculator)
    - [Weighted Mobility](#weighted-mobility)
- [Plotting & Visualization](#plotting--visualization)

---

## Getting Started

### Prerequisites & Installation
Ensure Python 3.10+ is installed. Clone the repository and install dependencies:
```bash
git clone https://github.com/mostafa-kadi/Seebeck-prime.git
cd Seebeck-prime
pip install -r requirements.txt
```

### Launch Desktop Application
To launch the PyQt6 interactive graphical interface:
```bash
python main.py
```

---

## Headless Python API

The scientific domain layer in `seebeck_prime.domain` is strictly GUI-independent and can be imported directly into Python scripts, Jupyter notebooks, or batch workflows without launching Qt:

```python
import numpy as np
from seebeck_prime.domain import calculate_pf, calculate_kappa_e, calculate_kappa_l, calculate_zt
from seebeck_prime.domain.units import celsius_to_kelvin
from seebeck_prime.plugins.electronic import invert_seebeck_to_eta, pisarenko_curve

# Temperature array in Celsius converted to Kelvin
T_C = np.array([100.0, 200.0, 300.0])
T_K = np.array([celsius_to_kelvin(t) for t in T_C])

# Transport properties (in SI base units: S in V/K, sigma in S/m, kappa in W/mK)
S = np.array([-180e-6, -210e-6, -230e-6])
sigma = np.array([1200e2, 850e2, 600e2])
kappa = np.array([1.6, 1.4, 1.25])

# Calculate derived properties
PF = calculate_pf(S, sigma)
kappa_e = calculate_kappa_e(sigma, T_K)
kappa_l = calculate_kappa_l(kappa, kappa_e)
ZT = calculate_zt(PF, T_K, kappa)

print("ZT values:", ZT)
```

---

## Data Entry & Processing

The main application features a spreadsheet-like interface for managing experimental thermoelectric datasets.

### Primary Input Columns
1. **Temperature ($T$)**: Independent experimental variable (Units: $\text{K}$ or $^\circ\text{C}$).
2. **Electrical Conductivity ($\sigma$)**: (Units: $\text{S/cm}$ or $\text{S/m}$).
3. **Seebeck Coefficient ($S$)**: (Units: $\mu\text{V/K}$ or $\text{V/K}$).
4. **Thermal Conductivity ($\kappa$)**: (Units: $\text{W}/(\text{m}\cdot\text{K})$). *Can be entered directly or imported via the Kappa Tool.*

### Automatic Calculations
Once primary data is entered, the application automatically computes:
* **Power Factor ($PF$)**: $S^2 \sigma$
* **Electronic Thermal Conductivity ($\kappa_e$)**: Wiedemann–Franz law ($\kappa_e = L \sigma T$).
  * *Default:* Standard Sommerfeld value ($2.443 \times 10^{-8}\ \text{W}\cdot\Omega/\text{K}^2$).
  * *Dynamic:* "Seebeck-Derived" Kim et al. SPB empirical estimate.
* **Lattice Thermal Conductivity ($\kappa_L$)**: $\kappa_{\text{total}} - \kappa_e$
* **Figure of Merit ($ZT$)**: $S^2 \sigma T / \kappa_{\text{total}}$

### Unit Management & Clipboard
- Select raw measurement units via toolbar dropdowns. The application manages internal conversions to base SI units for all calculations and transforms values back to display units.
- **Clipboard Support:** Paste experimental columns directly from Excel, OriginLab, or CSV files.

---

## Error Propagation & Uncertainty Analysis

Seebeck Prime implements first-order **Multivariate Gaussian Error Propagation** to calculate formal measurement uncertainties.

Activate uncertainty analysis by clicking **"Toggle Error Bars"** in the toolbar:

### 1. Percentage Mode (Manual)
Specify uniform percentage uncertainties (e.g., $5\%$ for Seebeck, $7\%$ for conductivity, $8\%$ for thermal conductivity). The system propagates standard errors to derived quantities ($PF$, $\kappa_e$, $\kappa_L$, $ZT$).

### 2. File-Based Rigorous Mode
Processes raw instrument data directly:
* **Specimen Geometry:** Length, width, thickness, and caliper uncertainties ($\delta l, \delta w, \delta t$).
* **Raw Files:**
  * **Four-Probe / Resistivity File:** Computes geometric error and voltage scatter.
  * **Laser Flash (LFA) File:** Propagates diffusivity ($\alpha$), heat capacity ($C_p$), and density ($\rho$) errors.
  * **Raw Seebeck File:** Determines $\delta S$ from the standard linear regression error of $\Delta V$ vs $\Delta T$.

---

## Analysis Tools

### Thermal Conductivity (Kappa) Tool
Located under the **Analyze** menu:
* Computes $\kappa = \alpha \cdot C_p \cdot \rho$ from raw LFA flash data.
* Temperature interpolation allows matching laser flash temperatures to electrical transport setpoints.
* High-temperature **Dulong-Petit** limit calculation based on chemical formula unit stoichiometry.

### Device Efficiency Calculator
Estimates theoretical maximum conversion efficiency $\eta_{\max}$ and cumulative engineering figure of merit $ZT_{\text{eng}}$ across specified cold ($T_c$) and hot ($T_h$) junction temperatures using Snyder et al. integration methods.

### Weighted Mobility ($\mu_W$)
Evaluates electronic transport quality independent of carrier concentration using the Snyder relation, allowing direct comparison of intrinsic electronic performance across different doping series.

---

## Plotting & Visualization

* **Multi-Property Plotting:** Automatically generates coordinated Matplotlib windows for all key thermoelectric properties vs temperature.
* **Publication Formatting:** Styled with `scienceplots` for submission-ready vector outputs (PDF, SVG, EPS, PNG).
* **Error Visualization:** Error bars corresponding to standard uncertainties are automatically overlaid when error mode is active.
