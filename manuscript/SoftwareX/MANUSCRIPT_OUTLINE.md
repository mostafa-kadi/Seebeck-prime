# Seebeck-Prime Manuscript Outline — SoftwareX Stage 1

**Document type:** Stage 1 deliverable of the SoftwareX manuscript preparation.
**Date:** 2026-11-12
**Companion documents:** `manuscript/SoftwareX/SOFTWARE_CAPABILITY_MATRIX.md`,
`manuscript/SoftwareX/RESEARCH_POSITIONING.md`,
`manuscript/SoftwareX/AUTHOR_INPUT_REQUIRED.md`.

---

## 1. Proposed titles (choose one; author to confirm)

1. **Seebeck-Prime: An integrated desktop application for thermoelectric
   transport-property analysis and modelling** *(working title)*
2. **Seebeck-Prime: Reproducible thermoelectric transport-property calculations
   with rigorous Lorenz-number modelling and experimental benchmarking**
3. **From measured Seebeck coefficient, conductivity and thermal conductivity to
   thermoelectric figure of merit: an integrated software implementation**

## 2. Central contribution statement (Stage 1 wording, subject to author
confirmation)

> Seebeck-Prime provides an integrated desktop environment that (i) ingests
> thermoelectric transport measurements, (ii) computes power factor, ZT,
> Lorenz-number-conditioned electronic and lattice thermal conductivities, SPB
> carrier and Seebeck inversion, and device efficiency, and (iii) propagates
> uncertainties — under a single unit convention, against independently verified
> numerical implementations and, where published data permit, published measurements.

The *scientific* contribution is the **validated implementation and the honest
boundary conditions** of those models; the *software* contribution is the
**integration** of the chain into a reproducible desktop workflow.

## 3. Section-by-section outline (SoftwareX-oriented)

### 3.1 Title, authors, abstract

- Abstract must state: problem, software, capabilities, methods, validation
  evidence, users, and non-claims.
- Avoid generic statements; no "thermoelectric materials are important".

### 3.2 1. Motivation and significance

- Interdependence of S, σ, κ → PF, ZT; κL = κ − κe as a difference of close numbers;
  Lorenz-number choice propagation.
- Practical difficulty of assembling the chain by hand; reproducibility need.

### 3.3 2. Software description

- Desktop GUI (`src/gui`), headless Python API (`src/application`,
  `src/domain`), presentation layer, exporters, importers, multi-sample.
- Layering: GUI → application → domain; presentation helpers; infrastructure.
- Architecture boundary tests (no domain→GUI; no infrastructure→GUI).

### 3.4 3. Software functionality

- 3.1 Transport calculations: S, σ, ρ, PF, κe, κL, ZT, Lorenz modes (constant /
  Kim / SPB).
- 3.2 Thermal conductivity analysis: laser flash κ = α·Cp·ρ; decomposition.
- 3.3 Lorenz-number models: constant, Kim, SPB; conditional validity.
- 3.4 SPB modelling: Fermi integrals, inversion, carrier density, effective mass,
  round trips.
- 3.5 Weighted mobility and Hall: distinction μ_W vs μ_H; weighted-mobility
  physics unverified (D-12).
- 3.6 Uncertainty: first-order Taylor; independence assumption; JΣJᵀ absent.
- 3.7 Data management, visualization, exports, importers.

### 3.5 4. Illustrative application and validation

- Numerical verification vs independent references (1e-14…1e-6).
- Experimental benchmarking: four specimens; PF/ZT 1.26–5.93 %; κL SiGe:P ≤0.7 %.
- SiGe:P Lorenz contradiction: resolved as scattering assumption (λ≈1.41); −35 %.
- PbTe: Lorenz comparison **UNVERIFIED** (source-data inconsistency, 24.9 % spread).
- Limitations.

### 3.6 5. Impact and reuse potential

- Integration, reproducibility, unit consistency, multi-sample; expected vs
  demonstrated impact (no invented statistics).

### 3.7 6. Limitations and future development

- GUI coverage incomplete; V/I chain not implemented; covariance propagation
  absent; Kane/Dingle absent; weighted mobility physically unverified.

### 3.8 7. Conclusions

### 3.9 Software metadata (to be completed from actual project information)

## 4. Figures and tables plan (max six)

1. Software architecture diagram — GUI / data / calculation / modelling / validation / export.
2. Application interface — genuine screenshot only (author to supply).
3. Workflow diagram: measurement → transport properties → ZT.
4. SPB modelling workflow: Fermi integrals → inversion → carrier density.
5. Numerical validation: independent reference vs application (regeneration
   script available).
6. Experimental benchmark: calculated vs published (PF/ZT; κL).

No figure may be fabricated.

## 5. References plan

- `manuscript/SoftwareX/references.bib` to be created; `REFERENCE_VERIFICATION.md`
  to be created. Existing anchors: Sommerfeld/Lorenz, Wiedemann–Franz, Kim 2015,
  Snyder & Toberer 2008, Snyder et al. 2020, May & Snyder 2012, Goldsmid 2016,
  Putley 1960. All must be verified; DOIs must not be invented.

## 6. Compliance checklist inputs

- SoftwareX 3000-word limit (verify against current guide); structure mapping;
  software availability (local-only ≠ compliant); licensing (D-04 open);
  metadata (version reconciliation D-03 open); packaging (D-05/D-06 open).

## 7. Stage 1 completion statement

The outline above is **drafted from repository evidence only**. It is not the final
manuscript text and must not be cited as such. Section content must be filled in
only after the capability matrix and research positioning are approved and after
the author supplies required inputs.
