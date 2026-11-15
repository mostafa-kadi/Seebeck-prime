# Seebeck Prime

**Seebeck Prime** is an open-source, reproducible scientific analysis platform designed for thermoelectric materials research. It automates the calculation of transport properties, performs rigorous analytical and statistical error propagation, provides advanced interactive plotting, and models electronic and thermal transport mechanisms.

---

## Authoritative Project Documentation

For architecture decisions, verified migration tasks, physical equations, and publication validation, consult the authoritative documentation in [`docs/`](docs/) and [`validation/`](validation/):

1. **[System Architecture (`docs/ARCHITECTURE.md`)](docs/ARCHITECTURE.md)**  
   As-built system boundary definitions, codebase layout, architectural constraints (no DFT, no web scrapers, PC-practical), and the remaining target components.
2. **[Scientific Model Register (`docs/SCIENTIFIC_MODEL_REGISTER.md`)](docs/SCIENTIFIC_MODEL_REGISTER.md)**  
   Definitive scientific catalog covering governing formulas, input/output units, physical assumptions, limitations, and literature citations for core transport ($PF, \kappa_e, \kappa_L, ZT$), carrier models (Hall, weighted mobility, SPB, Pisarenko), and uncertainty propagation.
3. **[Experimental Benchmark Validation (`docs/EXPERIMENTAL_BENCHMARK_VALIDATION.md`)](docs/EXPERIMENTAL_BENCHMARK_VALIDATION.md)**
   Validation of selected calculation-engine and file-workflow components against published experimental measurements (Bi₂Te₃-, PbTe- and SiGe-based, digitised from peer-reviewed papers by the StarryData project): power factor and figure of merit for four materials, selected Lorenz-number checks, instrument-import and multi-sample checks, and SPB numerical comparisons. Weighted mobility has equation-level regression tests but no usable experimental mobility reference in the current benchmark set; interactive GUI paths remain partly unverified. The benchmark framework is in [`tests/experimental_benchmarks/`](tests/experimental_benchmarks/).
4. **[Scientific Equation Audit (`docs/SCIENTIFIC_EQUATION_AUDIT.md`)](docs/SCIENTIFIC_EQUATION_AUDIT.md)**
   Equation-by-equation verification of the physical models, dimensional analysis, unit-conversion audit, independent numerical verification, identified errors with severities, and the corrections implemented.
5. **[Comprehensive Scientific Validation Package (`validation/README.md`)](validation/README.md)**
   Independent scientific validation of **every** implemented calculation: the equation registry (E-01…E-62), the test plan with justified tolerances, the independently written reference implementations, the measured results (**738 passed / 10 skipped** in the primary environment, **745 / 6** in the Qt-capable environment, **119 / 7** in the benchmark suite, with every skip reasoned), the published-material benchmark landscape, and an explicit statement of what remains unverified. Read `validation/SCIENTIFIC_VALIDATION_LIMITATIONS.md` first.

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
- [Architecture](#architecture)
- [Scientific Status & Capability Boundaries](#scientific-status--capability-boundaries)
- [Licence](#licence)
- [Citation](#citation)
- [Support](#support)

---

## Getting Started

### Prerequisites & Installation
See [`docs/SUPPORTED_PYTHON.md`](docs/SUPPORTED_PYTHON.md) for the verified Python-version status. In short: **Python 3.12 or 3.13** (verified locally on 3.13; 3.12/3.13 are the CI targets).

**Option A — install from the public source repository:**
```bash
git clone https://github.com/mostafa-kadi/Seebeck-prime.git
cd Seebeck-prime
python -m pip install -r requirements.txt
python -m pip install .
```

**Option B — editable development install:**
```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

A PyPI distribution is not documented as a verified release in this repository; use the source-install commands above unless a published PyPI release is confirmed.

> **Windows note:** the PyQt6 combination verified on the development machine is **PyQt6 6.9.1**; the newest PyQt6 (6.12) failed to load `QtWidgets` on that machine's Windows build with a DLL entry-point error (`0xc0000139`). If you see the same error, pin the binding: `pip install PyQt6==6.9.1`.

### Launch Desktop Application
To launch the PyQt6 interactive graphical interface:
```bash
python main.py
```

### Running the Test Suite
Run the full test suite (unit tests, architecture-boundary tests, golden-output regression baseline, and startup smoke tests):
```bash
python -m pytest -q
```

Notes:
- The golden-output baseline (`tests/golden/baseline_outputs.json`) characterizes the current scientific outputs of the domain/application layers. It is a self-generated regression snapshot — **not** scientific validation. Regenerate it deliberately (after an approved scientific change) with:
  ```bash
  python scripts/generate_golden_baseline.py
  ```
  and review the resulting JSON diff in git.
- One test (`import main` GUI smoke) is skipped automatically on machines where the PyQt6 widgets library cannot load; it runs in CI and normal environments.
- A synthetic example dataset and a headless usage script are provided in [`examples/`](examples/README.md) (`example_dataset.csv`, `example_dataset.txt`, `headless_analysis.py`).

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

### File Formats (Import / Export)
- **CSV** (`.csv`) — comma-separated (tab-separated files are also accepted on import).
- **Plain text** (`.txt`, `.tsv`) — the separator is detected automatically on import (comma, tab, semicolon, or whitespace) and `#` comment lines are ignored; exports are written tab-separated, which imports directly into Origin/Excel.
- **Excel** (`.xlsx`) — workbooks, including named multi-sheet exports for plots and Multi-Sample batches.
- Use **File → Open** / **File → Save As** to select the format; the dialog filters list all supported types.

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
Calculates the Snyder et al. (2020) empirical weighted mobility from Seebeck coefficient, electrical resistivity and temperature. It is a density-of-states-weighted transport descriptor, not Hall mobility. The implementation is regression-tested against the published equation, but material-specific experimental validation is unavailable in the current benchmark set.

---

## Plotting & Visualization

* **Multi-Property Plotting:** Automatically generates coordinated Matplotlib windows for all key thermoelectric properties vs temperature.
* **Publication Formatting:** Styled with `scienceplots` for submission-ready vector outputs (PDF, SVG, EPS, PNG).
* **Error Visualization:** Error bars corresponding to standard uncertainties are automatically overlaid when error mode is active.

---

## Architecture

Seebeck Prime is a **layered modular monolith** with a strictly one-directional dependency rule, enforced by automated architecture tests:

```
main.py (composition root)
   └─ gui  →  presentation  →  application  →  domain
                                     ▲
infrastructure (pandas adapter) ─────┘   implements the TabularDataStore port
plugins/  re-exports domain only
```

- **`domain/`** (13 modules, 2,012 LOC) — pure science: transport calculations, uncertainty propagation, unit vocabulary, SPB / Hall / phonon / device-efficiency models, validation. No GUI, no filesystem access.
- **`application/`** (11 modules, 1,262 LOC) — use cases, measurement-table processing, table schema, the `TabularDataStore` port, the table-facing unit-conversion front end.
- **`presentation/`** (23 modules, 4,192 LOC) — table/plot orchestration, notices, and the 9 dialogs (`dialogs/`); owns no scientific calculations (enforced by test).
- **`gui/`** (4 modules, 652 LOC) — main-window composition only; `main.py` is the single place a concrete persistence adapter is wired.
- **`infrastructure/`** (2 modules, 84 LOC) — pandas-backed tabular data store.
- **`plugins/`** (6 modules, 136 LOC) — domain re-exports.

Measured 2026-11-13: **60 modules / 8,359 non-blank LOC**; the import graph is acyclic and every edge points inward (`tests/test_architecture_dependencies.py`, 25 tests; `tests/test_import_root.py`, 7 tests). Details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/CODE_SKELETON.md`](docs/CODE_SKELETON.md).

---

## Scientific Status & Capability Boundaries

Honesty boundaries, stated up front (full detail in the validation package):

- **Every implemented equation has an independently re-derived reference** (`validation/independent_calculations/`, machine-checked for independence) and agrees inside stated tolerances; the per-equation status lives in `validation/SCIENTIFIC_EQUATION_REGISTRY.md` and `validation/remediation/VALIDATION_STATUS.md`.
- **Numerically verified is not the same as experimentally validated.** The published-measurement benchmark evidence covers **power factor and figure of merit for four specimens** (Bi₂Te₃-, PbTe- and SiGe-based, digitised from peer-reviewed papers via the StarryData project); other quantities are verified as implementations but are **not** validated against independent experiments.
- **Not implemented** (documented boundaries, not oversights): raw V/I → σ measurement chain, covariance-aware uncertainty propagation, Kane/Dingle/multiband Lorenz models, two-band models.
- **Weighted mobility** now implements the published Snyder et al. (2020) expression and is covered by independent equation-level regression tests. It remains experimentally unvalidated because the current benchmark set contains no usable matched mobility curve.
- The golden-output regression baseline is a self-generated snapshot, **not** scientific validation.

---

## Licence

Seebeck Prime is released under the **MIT Licence** — see [`LICENSE`](LICENSE) (also provided as `Licence.txt` for the SoftwareX repository requirement).

---

## Citation

If you use Seebeck Prime in your research, please cite it using the metadata in [`CITATION.cff`](CITATION.cff) (version 0.1.0, 2026-11-13) or the accompanying SoftwareX article. A permanent DOI (Zenodo) will be minted with the public release; until then the repository URL is the canonical reference.

---

## Support

Questions, bug reports and feature requests: please open a GitHub issue at <https://github.com/mostafa-kadi/Seebeck-prime> or contact the corresponding author. Support e-mail to be confirmed at the SoftwareX submission (see `manuscript/SoftwareX/SOFTWARE_METADATA.md`).
