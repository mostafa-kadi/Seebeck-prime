# Seebeck Prime

**Seebeck Prime** is a comprehensive analysis tool designed for thermoelectric materials research. It automates the calculation of transport properties, performs rigorous error propagation, and provides advanced plotting and device-level efficiency estimations.

## Table of Contents
- [Getting Started](#getting-started)
- [Data Entry & Processing](#data-entry--processing)
- [Error Propagation & Uncertainty Analysis](#error-propagation--uncertainty-analysis)
- [Analysis Tools](#analysis-tools)
    - [Thermal Conductivity (Kappa) Tool](#thermal-conductivity-kappa-tool)
    - [Device Efficiency Calculator](#device-efficiency-calculator)
    - [Weighted Mobility](#weighted-mobility)
- [Plotting](#plotting)

---

## Getting Started

To launch the application, run the main script from your terminal:
```bash
python main.py
```

## Data Entry & Processing

The main window features a spreadsheet-like interface for managing your thermoelectric data.

### Input Columns
You are required to provide the following primary data:
1.  **Temperature**: The independent variable (Units: K or °C).
2.  **Electrical Conductivity (σ)**: (Units: S/cm or S/m).
3.  **Seebeck Coefficient (S)**: (Units: μV/K or V/K).
4.  **Thermal Conductivity (κ)**: (Units: W/mK). *Note: This can also be imported via the Kappa Tool.*

### Automatic Calculations
Once the primary data is entered, the application automatically calculates:
*   **Power Factor (PF)**: $S^2 \sigma$
*   **Electronic Thermal Conductivity (κ_e)**: Calculated using the Wiedemann-Franz law ($\kappa_e = L \sigma T$).
    *   *Default*: Uses a standard Lorenz number ($2.44 \times 10^{-8} \, W\Omega K^{-2}$).
    *   *Dynamic*: Can be set to "Seebeck-Derived" to estimate $L$ based on the Seebeck coefficient (SPB model).
*   **Lattice Thermal Conductivity (κ_L)**: $\kappa_{total} - \kappa_e$
*   **Figure of Merit (ZT)**: $S^2 \sigma T / \kappa$

### Unit Management
Use the dropdown menus in the toolbar to match the units of your raw data. The application handles all internal conversions to base SI units for calculation and back to your preferred units for display.
*   **Clipboard Support**: You can copy and paste rows directly from Excel or Origin.

---

## Error Propagation & Uncertainty Analysis

Seebeck Prime includes a robust engine for calculating measurement uncertainties using **Gaussian Error Propagation**.

To activate, click the **"Toggle Error Bars"** button in the toolbar. You will be presented with two modes:

### 1. Simple Percentage Mode (Manual)
Use this if you only have estimated relative errors for your equipment.
*   Enter fixed percentage errors for Temperature, Conductivity, Seebeck, and Thermal Conductivity (e.g., 5%).
*   The app will calculate absolute error bars for all derived properties (PF, ZT, etc.).

### 2. File-Based Rigorous Mode
Use this for detailed analysis starting from raw measurement files. The application calculates systematic errors based on sample geometry and statistical errors from measurement scatter.

**Required Inputs:**
*   **Geometry**: Sample Width, Thickness, probe distance, and their respective uncertainties (e.g., caliper precision).
*   **Raw Data Files**:
    *   **Four-Probe / Resistivity File**: Should contain Temperature, Resistance/Conductivity data.
    *   **Laser Flash (LFA) File**: For Thermal Diffusivity and Cp.
    *   **Raw Seebeck File**: Contains $\Delta V$ vs $\Delta T$ raw gradients.

**Methodology:**
*   **Conductivity Error**: Combines geometric factors ($\delta l/l, \delta w/w, \delta t/t$) with resistance scatter.
*   **Seebeck Error**: derived from the standard error of the linear regression slope ($\Delta V / \Delta T$).
*   **Thermal Conductivity Error**: propagates errors from Diffusivity, Cp, and Density.

*When using File-Based mode, the application will generate and save new Excel files in your source directory containing the fully processed data with calculated uncertainty columns.*

---

## Analysis Tools

### Thermal Conductivity (Kappa) Tool
*Located under the "Tools" or "Analyze" menu.*

This tool helps process raw Laser Flash Analysis (LFA) data.
*   **Calculation Mode**: Calculate $\kappa = \alpha \cdot C_p \cdot \rho$.
*   **Inputs**:
    *   **Diffusivity ($\alpha$)**: Raw data from LFA.
    *   **Specific Heat ($C_p$)**: measured or generic.
    *   **Density ($\rho$)**: Manually entered or calculated from weight/dimensions.
*   **Interpolation**: The tool can interpolate calculated $\kappa$ values to specific temperatures to match your main electrical data (e.g., matching LFA temperatures to ZEM temperatures).
*   **Dulong-Petit Limit**: Can calculate and overlay the theoretical high-temperature $C_p$ limit based on chemical formula.

### Device Efficiency Calculator
*Located under the "Tools" menu.*

Estimates the theoretical conversion efficiency of a thermoelectric generator leg made from your material.
*   **Inputs**: Cold Side ($T_c$) and Hot Side ($T_h$) temperatures.
*   **Outputs**:
    *   **Engineering ZT ($ZT_{eng}$)**: Cumulative ZT over the temperature range (Snyder et al. method).
    *   **Standard Efficiency**: Based on average ZT.
    *   **Engineering Efficiency**: More accurate estimation accounting for temperature-dependent properties.

### Weighted Mobility
Calculates and plots the weighted mobility ($\mu_W$) to assess electronic transport quality independent of carrier concentration.

---

## Plotting

*   **Plot All**: Instantly generates individual windows for every key property (Seebeck, Conductivity, Power Factor, ZT, Kappa, etc.) vs Temperature.
*   **Custom Plot**: Allows you to select specific X and Y axes and arrange multiple plots in a grid layout.
*   **Error Bars**: If Error Mode is active, plots will automatically include error bars representing the calculated standard deviation.
