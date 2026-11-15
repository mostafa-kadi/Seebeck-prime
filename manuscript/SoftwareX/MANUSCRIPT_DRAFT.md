# Seebeck-Prime: An integrated desktop application for thermoelectric transport-property analysis and modelling

**Draft version:** 0.1 (Stage 6 assembly — first full draft)
**Date:** 2026-11-12
**Status:** Draft for review — pending author confirmation and editorial compliance check
**Assembly disposition:** Critical review dispositions incorporated (see
`CRITICAL_REVIEW.md`); mandatory information and evidence remain open (author
inputs, licence, distribution, references verification, GUI capture, compliance
verification). The draft is **not submission-ready**.

---

## Abstract

Thermoelectric transport-property analysis normally requires the researcher to
combine measured Seebeck coefficients, electrical conductivities and thermal
conductivities into power factors, figures of merit, Lorenz-number-conditioned
thermal conductivities and device efficiencies, while keeping unit conventions
and modelling assumptions consistent. Seebeck-Prime is an open-source desktop
application that provides this chain as an integrated, reproducible workflow,
together with a headless Python API for programmatic use.

The software implements the thermoelectric transport equations directly: power
factor \(PF = S^2 \sigma\), electronic thermal conductivity \(\kappa_e = L \sigma T\),
lattice thermal conductivity \(\kappa_L = \kappa - \kappa_e\), figure of merit
\(ZT = PF\,T / \kappa\), Lorenz-number models (constant Sommerfeld value,
Kim empirical relation, rigorous single-parabolic-band transport-integral
Lorenz number), Fermi-Dirac integral evaluation and Seebeck-from-reduced-Fermi-level
inversion, carrier concentration and effective-mass estimation, Hall analysis,
weighted mobility, laser-flash thermal conductivity, device efficiency, and
first-order uncertainty propagation.

The implementation was verified against independently written reference
implementations to relative errors of approximately \(10^{-14}\) to \(10^{-6}\)
across the transport equations, and the full suite contains **680 passing tests**
with **10 documented skips** in the primary environment (629 passing, 4 skipped, in
the Qt-capable GUI environment). Against published experimental data for four
benchmark specimens, the calculation engine reproduces published power factors and
figures of merit within approximately \(1.3\%\) to \(5.9\%\), and the published
Seebeck-doped germanium data imply a Lorenz number of approximately \(2.46 \times
10^{-8}\ \mathrm{W\,\Omega\,K^{-2}}\), consistent with the application constant of
\(2.44 \times 10^{-8}\ \mathrm{W\,\Omega\,K^{-2}}\).

The software deliberately distinguishes numerical verification from physical
validation and does not overclaim: the physical models are conditional, the
weighted-mobility model is not experimentally validated, the PbTe Lorenz-number
comparison is unverified because of source-data inconsistency, the raw
voltage-and-current-to-conductivity chain is not implemented, and covariance-aware
uncertainty propagation is not yet implemented.

**Purpose:** integrated, reproducible thermoelectric transport-property analysis.
**Audience:** thermoelectric materials researchers, computational materials
scientists, and developers of scientific thermoelectric software.

**Keywords:** thermoelectric materials; Seebeck coefficient; power factor; figure
of merit; single parabolic band; Fermi-Dirac integrals; Lorenz number; scientific
software; numerical analysis; materials characterisation.

---

## 1. Motivation and Significance

Thermoelectric transport-property analysis is, at its core, a chain of
interdependent quantities. The measured Seebeck coefficient \(S\), electrical
conductivity \(\sigma\), and thermal conductivity \(\kappa\) must be combined into
the power factor \(PF = S^2\sigma\) and the figure of merit \(ZT = PF\,T/\kappa\).
The total thermal conductivity is then decomposed into an electronic and a lattice
contribution, \(\kappa = \kappa_e + \kappa_L\), which requires a Lorenz number
choice.

This chain is where preventable error accumulates. The lattice contribution is a
*difference of two comparable numbers*, so an error in the Lorenz number
propagates directly and substantially into \(\kappa_L\) and hence into \(ZT\). The
choice of Lorenz number is also where the physics becomes subtle: the constant
Sommerfeld value, an empirical relation, and a transport-integral model each embed
different assumptions about scattering and band structure.

In practice, researchers assembling these steps from separate programs,
spreadsheets, or custom scripts face inconsistent unit conventions and implicit
model choices. Seebeck-Prime was developed so that the chain — from input, through
calculation, to derived properties, plots and exports — is executed, unit-normalised
and traceable within one application.

## 2. Software Description

### 2.1 Architecture

Seebeck-Prime follows a layered architecture:

- **Presentation:** Qt desktop user interface (`src/gui`), plotting layers
  (`src/presentation`), reusable UI helpers.
- **Application:** use cases and orchestration
  (`src/application`): calculation workflows, validation workflows, file-handling
  orchestration.
- **Domain:** scientific models and pure calculation functions
  (`src/domain`): transport equations, SPB/Fermi-integral model, Hall, phonon,
  device efficiency, uncertainty, units, physical constants, validation rules.
- **Infrastructure:** storage and I/O adapters.

Architectural boundary tests enforce the direction of dependencies (no domain →
GUI, no infrastructure → GUI), keeping the scientific core free of UI concerns.

### 2.2 Implementation coverage relevant to the manuscript

The implemented capability set includes, at the headless level:

- transport-property calculations (\(PF\), \(\kappa_e\), \(\kappa_L\), \(ZT\));
- Lorenz-number models: constant, Kim empirical, rigorous SPB;
- SPB Fermi-Dirac integrals, Seebeck inversion, carrier density, effective mass,
  round trips;
- Hall coefficient/density/mobility and scattering-exponent fit;
- weighted mobility;
- laser-flash thermal conductivity \(\kappa = \alpha C_p \rho\);
- device efficiency;
- first-order uncertainty propagation;
- unit conversion;
- manual and instrument-derived workflows, batch and multi-sample processing;
- GUI, plotting, export.

## 3. Software Functionality

### 3.1 Thermoelectric transport calculations

The core headless entry point computes, from temperature, electrical conductivity
and Seebeck coefficient (and total thermal conductivity):

\[
PF = S^2\sigma,\qquad \kappa_e = L\,\sigma\,T,\qquad \kappa_L = \kappa - \kappa_e,\qquad
ZT = \frac{PF\,T}{\kappa}.
\]

All quantities are handled internally in SI base units and converted for display,
with unit validation on conversion (a thermal-conductivity unit-convention defect,
severity SE-042, was identified and remediated during the validation programme).

### 3.2 Thermal conductivity analysis

Laser-flash analysis uses

\[
\kappa = \alpha\,C_p\,\rho,
\]

with laboratory inputs converted to SI before evaluation.

### 3.3 Lorenz-number models

Three modes are implemented:

- **Constant:** \(L_0 = (\pi^2/3)(k_B/e)^2 = 2.443004509\times10^{-8}\ \mathrm{W\,\Omega\,K^{-2}}\).
- **Kim empirical:** \(L(S) = (1.5 + e^{-|S|/116})\times10^{-8}\ \mathrm{W\,\Omega\,K^{-2}}\).
- **Rigorous SPB:** \(L(\eta)\) via Fermi-Dirac transport integrals.

### 3.4 SPB modelling

Fermi-Dirac integrals, Seebeck-from-η inversion, carrier concentration, effective
mass, and round trips are implemented; the unnormalised integral convention is
explicitly reconciled with the Blatt-normalised textbook form.

### 3.5 Weighted mobility and Hall

The weighted mobility and Hall mobility are distinct quantities; their definitions
and units are handled separately.

### 3.6 Uncertainty

First-order propagation of power factor, thermal conductivity components and ZT is
implemented; input independence is assumed.

### 3.7 Data management, visualisation, export

Manual entry, instrument importers, batch processing, multi-sample comparison,
plotting, and export are implemented.

## 4. Illustrative Application and Validation

### 4.1 Numerical verification

Independent reference implementations (written without application imports,
machine-checked for independence) reproduce the application results to
approximately \(10^{-14}\) to \(10^{-6}\) relative error across the transport
equations.

### 4.2 Experimental benchmarking

Benchmarks against four published datasets (power factor and ZT; SiGe:P and
Bi₂Te₃ thermal conductivity):

- Published power factors and ZT reproduced within approximately \(1.3\%\)–\(5.9\%\).
- Published SiGe:P lattice thermal conductivity reproduced within \(0.7\%\) using
  the application constant.
- The Lorenz number implied by the published SiGe:P data (\(2.46\times10^{-8}\)) is
  consistent with the constant (\(2.44\times10^{-8}\)).
- The acoustic-scattering SPB Lorenz value (\(1.59\times10^{-8}\)) disagrees by
  approximately \(35\%\); investigation showed this to be a scattering-assumption
  matter (effective exponent \(\lambda \approx 1.41\)), not an implementation error.
- The PbTe comparison is **unverified** because the published \(\kappa/\kappa_L\) pair
  is internally inconsistent (spread \(>20\%\)).

### 4.3 Honest boundaries

The manuscript states plainly: tests passing is not validation; numerical agreement
is not experimental validation; conditional physical models are not universal.

## 5. Impact and Reuse Potential

Integrated desktop workflow, reproducible headless API, traceable units,
multi-sample comparison, reusable equations.

## 6. Limitations and Future Development

- GUI automated coverage incomplete.
- Raw V/I → R → ρ → σ chain **not implemented**.
- Covariance-aware uncertainty propagation **not implemented**.
- Kane / Dingle / multiband models **not implemented**.
- Weighted mobility physically **unverified** (and implementation differed from an
  earlier internal formulation; divergence documented).
- PbTe and weighted-mobility benchmarks **unverified**.

## 7. Conclusions

Seebeck-Prime implements an integrated thermoelectric transport chain with
numerically verified equations and honest, conditional validation claims.

---

## 8. Final assembly disposition (Stage 6)

This draft was assembled from the Stage 1–5 artefacts and the Stage 5 critical
review. Dispositions applied:

- all substantive scientific claims carry traceable evidence (see
  `SCIENTIFIC_CLAIMS_AUDIT.md`);
- honest boundaries retained (PbTe unverified; weighted mobility unverified;
  V/I chain not implemented; covariance propagation not implemented);
- author-input placeholders retained where information is missing
  (`AUTHOR_INPUT_REQUIRED.md`, `AUTHOR_INFORMATION.md`);
- compliance items open (`SOFTWAREX_COMPLIANCE_CHECKLIST.md`);
- references pending verification (`REFERENCE_VERIFICATION.md`,
  `references.bib`);
- figures pending author input for Figure 2 (`FIGURE_PLAN.md`).

**Final disposition:** submission-ready **not** declared; submission-facing
assembly continues only after author confirmation of the open items.

**Stage 6b (2026-11-12):** the official SoftwareX OSP template was downloaded
and inspected (`templates/softwarex-osp-template.tex`), and the template-based
manuscript `MANUSCRIPT.tex` was produced from this draft, with all references
re-verified against Crossref/OpenAlex (three wrong draft DOIs corrected; see
`REFERENCE_VERIFICATION.md`). This markdown draft remains the working master;
`MANUSCRIPT.tex` is the submission-format source.

*End of Stage 6 final assembly.*
