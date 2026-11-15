# Seebeck-Prime — Figure Plan (Stage 4)

**Document type:** Stage 4 deliverable of the SoftwareX manuscript preparation.
**Date:** 2026-11-12
**Status:** Plan draft — figures requiring author input are marked.

---

## 1. Scope

Maximum of six figures, subject to the current official SoftwareX figure policy.
No figure may be fabricated; every figure requires source data and a generation
method.

## 2. Proposed figures

### Figure 1 — Software architecture

- **Caption:** Layered architecture of Seebeck-Prime: presentation, application,
  domain, infrastructure, with the enforced dependency boundaries.
- **Scientific / technical purpose:** show the software contribution and the
  decoupling of the scientific core.
- **Source data:** source tree (`src/`).
- **Generation method:** diagram from the architecture documentation
  (`docs/ARCHITECTURE.md`) and `tests/test_architecture_dependencies.py`.
- **Ready / author input needed:** **Ready** (documentation-based diagram).

### Figure 2 — Application interface

- **Caption:** Screenshot of the Seebeck-Prime desktop application.
- **Scientific / technical purpose:** illustrate the user-facing workflow.
- **Source data:** genuine screenshot of the running application.
- **Generation method:** capture from the GUI.
- **Ready / author input needed:** **Author input required** — no screenshot may be
  fabricated; GUI capture pending.

### Figure 3 — Thermoelectric analysis workflow

- **Caption:** From measured Seebeck coefficient, conductivity and thermal
  conductivity to power factor, Lorenz-conditioned thermal conductivities and ZT.
- **Scientific / technical purpose:** show the integrated chain.
- **Source data:** equations + workflow inventory.
- **Generation method:** diagram.
- **Ready / author input needed:** **Ready**.

### Figure 4 — SPB modelling workflow

- **Caption:** Fermi-Dirac integrals, Seebeck inversion, carrier density,
  effective mass, round trips.
- **Scientific / technical purpose:** show rigorous model pipeline.
- **Source data:** `src/domain/spb`, independent references.
- **Generation method:** diagram.
- **Ready / author input needed:** **Ready**.

### Figure 5 — Numerical validation

- **Caption:** Independent reference implementations vs application outputs.
- **Scientific / technical purpose:** numerical verification evidence.
- **Source data:** `validation/independent_calculations/`, test results.
- **Generation method:** generated from the independent-reference computations.
- **Ready / author input needed:** **Ready** (generated output).

### Figure 6 — Experimental benchmark

- **Caption:** Calculated vs published power factor and ZT (and κL) for benchmark
  specimens.
- **Scientific / technical purpose:** empirical validation evidence.
- **Source data:** `tests/experimental_benchmarks/` processed/expected data.
- **Generation method:** generated from benchmark comparison code.
- **Ready / author input needed:** **Ready** (generated output; PbTe marked
  unverified).

## 3. Figures explicitly deferred (do not fabricate)

- GUI screenshot: author input required.
- Bipolar κ_bp separation, lattice transport (Slack/Callaway), Monte Carlo,
  HDF5: **not implemented** — must not appear as figures.

## 4. Figure policy

- Maximum of six figures.
- Each figure must state source data and generation method.
- No fabricated screenshots or data.
