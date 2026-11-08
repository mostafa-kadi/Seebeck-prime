# Seebeck Prime — AI Agent Master Plan

## 1. Mission

You are working on **Seebeck Prime**, an existing PyQt6 desktop application for thermoelectric-material analysis.

Your mission is to evolve the existing application into a **reliable, reproducible, extensible scientific software platform focused on thermoelectric materials research**, suitable for a future SoftwareX submission.

The current architecture already separates:

* `src/core/` for scientific calculations
* `src/ui/logic/` for application logic
* `src/ui/widgets/`
* `src/ui/dialogs/`
* file handling
* plotting
* unit conversion
* uncertainty/error propagation
* multi-sample analysis

The current architecture also uses a pandas DataFrame as the main application data source and follows an MVC-like separation of model, logic, and UI.

## 2. Most Important Rule

**Do not rewrite the application from scratch.**

First understand the existing implementation.

Refactor incrementally.

Preserve existing functionality unless there is a documented scientific, architectural, or reliability reason to change it.

Before changing any public function, class, data structure, calculation, or file format:

1. Find all callers.
2. Understand current behavior.
3. Add or update tests.
4. Make the smallest safe change.
5. Run the relevant test suite.
6. Only then continue.

Do not optimize architecture at the expense of scientific correctness or existing user workflows.

---

# 3. Scientific Positioning

The final software should NOT be positioned primarily as:

> A calculator for PF and ZT.

It should become:

> **An open-source, reproducible platform for experimental thermoelectric-material transport analysis and materials optimization.**

The scientific center of the software should be:

```text
Experimental measurements
        ↓
Data validation
        ↓
Electronic transport
        ↓
Lattice thermal transport
        ↓
Materials-property relationships
        ↓
Composition / doping trends
        ↓
Optimization
        ↓
Literature benchmarking
        ↓
Reproducible results
```

The application should remain primarily **materials-focused**, not device-focused.

Do not prioritize TEG engineering, segmented generators, device efficiency, or device optimization during this development phase.

---

# 4. Target Architecture

Gradually evolve the current architecture toward:

```text
Seebeck-Prime/
│
├── pyproject.toml
├── README.md
├── LICENSE
├── CITATION.cff
├── CHANGELOG.md
├── CONTRIBUTING.md
│
├── docs/
│   ├── theory/
│   ├── tutorials/
│   ├── validation/
│   └── developer/
│
├── examples/
│   ├── basic/
│   ├── transport/
│   ├── thermal/
│   ├── optimization/
│   └── literature/
│
├── tests/
│   ├── unit/
│   ├── scientific/
│   ├── integration/
│   └── regression/
│
├── benchmarks/
│
└── src/
    └── seebeck_prime/
        │
        ├── domain/
        │   ├── calculations/
        │   ├── transport/
        │   ├── thermal/
        │   ├── models/
        │   ├── uncertainty/
        │   ├── units/
        │   ├── materials/
        │   └── constants/
        │
        ├── application/
        │   ├── analysis/
        │   ├── workflows/
        │   ├── project/
        │   └── services/
        │
        ├── infrastructure/
        │   ├── io/
        │   ├── excel/
        │   ├── csv/
        │   └── persistence/
        │
        ├── visualization/
        │   ├── plots/
        │   ├── fitting/
        │   └── exporters/
        │
        ├── plugins/
        │
        └── ui/
            ├── windows/
            ├── dialogs/
            ├── widgets/
            └── models/
```

Do not perform this restructuring all at once.

First map the current architecture to the proposed architecture.

Produce:

```text
ARCHITECTURE_MIGRATION_MAP.md
```

showing:

```text
current file
→ target location
→ reason
→ dependencies
→ migration risk
```

---

# 5. Scientific Domain Must Be GUI-Independent

Scientific calculations must not depend on PyQt6.

This must work:

```python
from seebeck_prime.domain import calculate_zt
```

without importing the GUI.

The same scientific engine must eventually serve:

```text
GUI
CLI
Python API
Plugins
Tests
```

There must be only one implementation of each scientific calculation.

Do not duplicate equations in dialogs, CLI commands, or plugins.

---

# 6. Scientific Data Model

The current DataFrame workflow should remain supported, but introduce explicit domain concepts.

Create models conceptually equivalent to:

```text
Project
 ├── Sample
 │    ├── Material
 │    ├── Composition
 │    ├── Geometry
 │    ├── Metadata
 │    └── Measurements
 │
 ├── Dataset
 ├── Analysis
 ├── Uncertainty
 └── Provenance
```

A sample should be capable of storing optional metadata such as:

```text
sample ID
material
composition
dopant concentration
mass
density
dimensions
thickness
electrode geometry
measurement method
temperature range
atmosphere
instrument
notes
```

Do not require every field for every experiment.

---

# 7. Unit System

Move unit conversion from being purely a UI concern into the scientific/domain layer.

The current application already stores data internally using base units and converts values between display and storage units.

Preserve this principle.

The domain must explicitly distinguish:

```text
Temperature
Seebeck coefficient
Electrical conductivity
Electrical resistivity
Thermal conductivity
Power factor
Carrier concentration
Mobility
Geometry
Energy
```

Pay particular attention to dangerous conversions such as:

```text
°C ↔ K
μV/K ↔ V/K
S/cm ↔ S/m
Ω·cm ↔ Ω·m
cm⁻³ ↔ m⁻³
```

Never silently guess a unit.

---

# 8. Provenance and Reproducibility

Every analysis should record enough information to answer:

> Where did this result come from?

and:

> Can the result be reproduced?

Record:

```text
software version
dataset
sample ID
input file
units
calculation model
constants
parameters
fit model
fit range
uncertainty model
filtering method
analysis date
```

Implement a reproducible project format, for example:

```text
Project/
├── project.json
├── raw/
├── processed/
├── results/
├── figures/
└── metadata/
```

The user should eventually be able to perform:

```text
Open Project
→ Reproduce Analysis
```

and regenerate the analysis.

---

# 9. Scientific Validation Comes Before Major Feature Expansion

Before introducing advanced plugins, create a strong scientific test framework.

Use:

```text
tests/
├── unit/
├── scientific/
├── integration/
└── regression/
```

Test:

```text
PF
κe
κL
ZT
Lorenz number
unit conversions
molecular weight
uncertainty propagation
fitting
transport models
```

Every scientific equation added later must have:

```text
formula
definition of variables
units
assumptions
scientific reference
test case
```

Never claim validation without a documented reference.

---

# 10. Materials-Focused Plugin Strategy

Do NOT implement a large number of unrelated plugins.

The initial materials roadmap should contain **only five major scientific modules**.

They are intentionally broad so that each module contains meaningful functionality rather than becoming a collection of small calculators.

---

# 11. Module 1 — Carrier Transport & Materials Optimization

## Priority: P0 — highest priority

This should become one of the defining capabilities of Seebeck Prime.

Current workflow:

```text
S + σ + κ
      ↓
PF + ZT
```

Target workflow:

```text
S
σ
n
μ
      ↓
Carrier Transport Analysis
      ↓
effective mass
Fermi level parameter
Lorenz number
weighted mobility
optimal carrier concentration
maximum PF
```

Implement a validated **single-parabolic-band/Pisarenko workflow**.

Potential analyses:

```text
S vs n
S vs σ
α-ln(σ)
weighted mobility
effective mass
optimal carrier concentration
maximum PF
Lorenz number
```

The 2025 Pisarenko study specifically demonstrated effective-mass estimation, an α–lnσ transport relation, and maximum-power-factor prediction from weighted mobility, making this a highly relevant materials-analysis direction.

## Important restrictions

Do not pretend SPB is universally valid.

The UI must clearly report:

```text
Model
Assumptions
Input requirements
Validity limitations
```

Allow the researcher to compare experimental values with model predictions.

Example:

```text
Experimental data
       +
SPB/Pisarenko model
       ↓
Transport map
       ↓
estimated optimum
```

The module must never automatically replace experimental data with model predictions.

---

# 12. Module 2 — Lattice Thermal Transport and Phonon Scattering

## Priority: P0

Current functionality calculates:

```text
κL = κtotal − κe
```

Extend this into analysis of the physical origin of κL.

Implement an architecture capable of supporting:

```text
Debye model
Slack model
Debye–Callaway model
```

Do not implement every model blindly.

Begin with:

1. Experimental κL(T)
2. Slack estimation
3. Debye–Callaway fitting framework

The goal is:

```text
Experimental κL(T)
        ↓
Phonon scattering model
        ↓
Fit
        ↓
Scattering parameters
        ↓
Contribution analysis
```

The reason this is a high priority is that a February 2026 npj Computational Materials paper introduced a dedicated Debye–Callaway simulator specifically for fitting experimental κL and deconvoluting phonon-scattering mechanisms. Therefore, implementing merely another basic Debye–Callaway calculator would not be sufficiently differentiated.

Our implementation should instead emphasize integration with Seebeck Prime's broader thermoelectric materials workflow:

```text
σ/S data
+
κtotal
+
κe
+
κL
+
composition
+
microstructure
        ↓
integrated material analysis
```

## Required features

Support, where scientifically justified:

```text
boundary scattering
point-defect scattering
Umklapp scattering
alloy scattering
grain-boundary effects
```

Provide:

```text
experimental vs calculated κL
fit quality
residuals
parameter confidence/uncertainty
active scattering mechanisms
```

Never infer a scattering mechanism merely because a fitted curve looks visually reasonable.

---

# 13. Module 3 — Thermoelectric Materials Maps

## Priority: P0

Create one unified **Materials Maps** module instead of many small plotting plugins.

It should support:

```text
S vs σ
S vs n
PF vs σ
PF vs T
κL vs T
ZT vs T
σ vs composition
S vs composition
κL vs composition
PF vs composition
ZT vs composition
```

Include:

```text
multi-sample comparison
error bars
fit curves
temperature filtering
composition filtering
```

The purpose is not simply plotting.

The module should allow researchers to identify:

```text
transport trade-offs
optimum regions
sample families
doping trends
temperature-dependent behavior
```

Provide publication-quality export while retaining a machine-readable plot configuration.

---

# 14. Module 4 — Composition and Doping Analysis

## Priority: P1

Treat composition as a first-class materials variable.

Example:

```text
Material A-x
x = 0
x = 0.02
x = 0.04
x = 0.06
...
```

The software should associate composition with:

```text
S
σ
n
μ
κ
κL
PF
ZT
```

Then provide:

```text
property vs composition
property vs temperature
composition-temperature maps
```

Support identification of experimental optima:

```text
maximum PF
maximum ZT
minimum κL
target conductivity
target Seebeck coefficient
```

Clearly distinguish:

```text
Experimental optimum
```

from:

```text
Model-predicted optimum
```

Do not create an "AI optimization" feature yet.

First establish trustworthy experimental and physics-based optimization.

---

# 15. Module 5 — Literature Materials Benchmark

## Priority: P1

Do not build a giant uncontrolled web scraper.

Create a **curated literature comparison system**.

A literature record should contain:

```text
material
composition
sample condition
temperature
S
σ/ρ
κ
ZT
source
DOI
year
notes
```

Allow:

```text
My material
vs.
Literature materials
```

with comparisons of:

```text
S
σ
κ
PF
ZT
```

Use source metadata for every literature point.

A 2025 thermoelectric database, teMatDb, demonstrates the value of temperature-dependent literature data and self-consistency checking by recalculating ZT from reported transport properties.

Use that idea carefully:

```text
reported ZT
      vs
recalculated ZT from S, σ, κ
```

Flag inconsistencies.

Do not reproduce copyrighted database contents without appropriate permission.

---

# 16. Optional Module — Electronic Structure Inference

## Priority: P2

Do not turn Seebeck Prime into a DFT package.

Instead provide experimental inference tools such as:

```text
effective mass
bipolar-transport indicators
band-gap estimates from approved models
transport-regime diagnostics
```

Any model must report assumptions and limitations.

For example, a Goldsmid–Sharp estimate must be presented as a model estimate rather than a definitive band gap.

This module should only be implemented after the P0/P1 modules are scientifically stable.

---

# 17. What NOT to Build During This Project

Do not prioritize:

```text
TEG device optimization
segmented TEG design
device geometry optimization
device efficiency calculators
generic machine-learning material discovery
large external web scraping systems
DFT calculations
full band-structure software
```

These are outside the core objective of the first SoftwareX version.

The application should first become an excellent **experimental thermoelectric-material analysis platform**.

---

# 18. Plugin Architecture

Each major module must have:

```text
Scientific model
Application service
Plugin interface
GUI interface
Python API
Tests
Documentation
References
```

Conceptually:

```text
Plugin
  │
  ├── Domain model
  ├── Calculator
  ├── Validation
  ├── Application service
  ├── GUI
  ├── CLI/API
  └── Tests
```

The GUI must never contain the primary scientific implementation.

---

# 19. Quality-Control Engine

Before producing final results, automatically check:

```text
missing values
duplicate temperatures
invalid units
nonphysical values
negative uncertainty
inconsistent geometry
κe > κtotal
insufficient points
poor fit quality
large uncertainty
invalid model range
```

Return:

```text
PASS
WARNING
ERROR
```

The application should tell the researcher why something is suspicious.

Example:

```text
WARNING:
κe exceeds κtotal in 4 data points.
Possible causes:
- conductivity unit conversion
- Lorenz number assumption
- thermal conductivity data
```

Never silently "fix" scientific data.

---

# 20. Fitting Framework

Create one reusable fitting subsystem instead of implementing independent fitting code inside every plugin.

Support:

```text
linear
polynomial
Arrhenius
power-law
exponential
custom models
```

Every fit must return:

```text
parameters
uncertainties
R² where applicable
residuals
fit range
number of points
confidence interval where supported
```

For Arrhenius analysis, support:

```text
log(σ) vs 1/T
log(σT) vs 1/T
```

with explicit model selection.

Do not automatically select a "best" fitting interval without exposing the selected region to the user.

---

# 21. Uncertainty Framework

Keep the existing uncertainty engine but move it toward the domain layer.

The current implementation already includes MAD outlier filtering and Gaussian error propagation.

Expand it to support:

```text
analytical propagation
Monte Carlo propagation
measurement uncertainty
geometry uncertainty
fit uncertainty
model uncertainty where appropriate
```

Every advanced materials plugin must be able to request uncertainty propagation rather than implementing its own inconsistent method.

---

# 22. Reproducible Analysis Workflow

The final researcher workflow should be:

```text
Import data
      ↓
Map columns
      ↓
Assign units
      ↓
Validate
      ↓
Process
      ↓
Calculate transport properties
      ↓
Uncertainty analysis
      ↓
Materials model
      ↓
Compare samples
      ↓
Plot
      ↓
Export
      ↓
Save reproducible project
```

This workflow should be accessible through GUI and eventually through CLI/API.

---

# 23. CLI and Python API

Do this only after the scientific domain layer is stable.

Target:

```bash
seebeck-prime validate
```

```bash
seebeck-prime analyze sample.csv
```

```bash
seebeck-prime transport sample.csv
```

```bash
seebeck-prime thermal sample.csv
```

```bash
seebeck-prime reproduce project.spj
```

All commands must call the same internal scientific services used by the GUI.

---

# 24. Testing Requirements

No scientific feature is complete until it has tests.

For every module provide:

```text
unit tests
scientific/reference tests
integration tests
regression tests
```

For each model:

```text
known input
expected result
tolerance
reference
```

For numerical methods:

```text
edge cases
invalid inputs
unit conversions
extreme values
```

For plugins:

```text
input validation
calculation
uncertainty
output
serialization
```

---

# 25. Scientific Validation Datasets

Create small, version-controlled validation datasets.

Do not depend on internet access during normal tests.

Each dataset must record:

```text
source
DOI
material
property
units
expected result
acceptable tolerance
```

Use published/reference values wherever licensing permits.

---

# 26. Benchmarking

Benchmark only after correctness is established.

Measure:

```text
single sample
multi-sample
large dataset
Monte Carlo uncertainty
thermal-model fitting
plot generation
```

Do not make performance claims in the paper until benchmarks are reproducible.

---

# 27. Documentation

For every scientific module provide:

```text
Purpose
Scientific theory
Equations
Definitions
Assumptions
Input requirements
Units
Examples
References
Limitations
Validation results
```

The user should be able to understand not only **how** to use the tool, but **what the result means scientifically**.

---

# 28. Release Engineering

Add:

```text
pyproject.toml
CITATION.cff
CHANGELOG.md
CONTRIBUTING.md
```

Set up automated checks for:

```text
tests
linting
formatting
type checking
package build
```

Every release must have a version identifier.

Every reproducible project must store the Seebeck Prime version.

---

# 29. Development Phases

## Phase 0 — Repository Audit

Do not modify code.

Produce:

```text
ARCHITECTURE_AUDIT.md
```

Identify:

```text
scientific calculations
UI/business-logic coupling
data flow
dependencies
duplicated calculations
state management
current tests
missing tests
file I/O
plotting
uncertainty
```

Also produce:

```text
SCIENTIFIC_FUNCTION_MAP.md
```

mapping every scientific equation/function to its current source file.

---

## Phase 1 — Freeze Current Scientific Behavior

Create regression tests for the existing application.

The objective is:

```text
Current result
=
Refactored result
```

within explicitly defined numerical tolerances.

Do this BEFORE substantial refactoring.

---

## Phase 2 — Extract Scientific Domain

Move pure calculations from UI/application code into the new domain architecture.

Do not change equations unless necessary.

If an equation appears ambiguous or scientifically questionable:

```text
DO NOT silently change it.
```

Document it in:

```text
SCIENTIFIC_REVIEW_NEEDED.md
```

with:

```text
current implementation
question
reference required
possible alternatives
```

---

## Phase 3 — Scientific Data Model

Introduce:

```text
Sample
Measurement
Dataset
Analysis
Project
Provenance
```

Maintain compatibility with current DataFrame-based workflows.

---

## Phase 4 — Validation and Uncertainty

Implement:

```text
unit validation
physical validation
quality control
uncertainty framework
fitting framework
```

---

## Phase 5 — Materials Module P0

Implement:

```text
Carrier Transport & Optimization
```

First.

Validate it thoroughly.

Do not begin another major scientific module until this passes its tests.

---

## Phase 6 — Materials Module P0

Implement:

```text
Lattice Thermal Transport
```

Begin with robust experimental κL handling and carefully validated models.

Do not copy the architecture of an existing Debye–Callaway application blindly. Build it as an integrated part of Seebeck Prime.

---

## Phase 7 — Materials Maps

Implement:

```text
S–σ
S–n
PF
κL
ZT
temperature maps
multi-sample maps
```

---

## Phase 8 — Composition/Doping

Implement composition-aware datasets and property-versus-composition analysis.

---

## Phase 9 — Literature Benchmark

Implement curated literature comparison and consistency checking.

---

## Phase 10 — Optional Electronic Inference

Only begin this after P0/P1 modules are stable.

---

## Phase 11 — CLI/API

Expose the mature scientific engine.

---

## Phase 12 — Reproducibility

Implement:

```text
project saving
provenance
analysis configuration
reproduction
```

---

## Phase 13 — SoftwareX Validation

Produce:

```text
SOFTWAREX_VALIDATION_REPORT.md
```

covering:

```text
architecture
scientific correctness
testing
reference validation
reproducibility
performance
documentation
installation
examples
known limitations
```

---

# 30. Definition of Done

The agent must NOT declare the project "SoftwareX ready" merely because:

```text
the program opens
```

or:

```text
the plugins work manually
```

It is ready only when:

```text
✓ Existing functionality preserved
✓ Scientific equations documented
✓ Scientific domain independent of GUI
✓ Unit handling validated
✓ Reference tests implemented
✓ Regression tests implemented
✓ Uncertainty tested
✓ Materials modules tested
✓ Reproducible projects implemented
✓ Provenance implemented
✓ Documentation complete
✓ Example datasets included
✓ Package install tested
✓ CLI/API validated where implemented
✓ Citation metadata prepared
✓ Known limitations documented
```

---

# 31. Final Materials-Focused Feature Set

The mature application should conceptually look like:

```text
                    SEEBECK PRIME
                         │
            THERMOELECTRIC MATERIALS
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
 ELECTRONIC          LATTICE          MATERIAL
 TRANSPORT           TRANSPORT       OPTIMIZATION
       │                 │                 │
       │                 │                 │
   S, σ, n, μ        κtotal, κe, κL    Composition
   SPB               Slack             Doping
   Pisarenko         Callaway          Trends
   m*                Scattering        Optimum
   Lorenz            Defects
   PF
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                  MATERIALS MAPS
                         │
                         ▼
              LITERATURE BENCHMARK
                         │
                         ▼
                  REPRODUCIBLE
                    ANALYSIS
```

The main scientific story should therefore be:

```text
Measure
  ↓
Understand electronic transport
  ↓
Understand lattice transport
  ↓
Understand composition/doping effects
  ↓
Compare materials
  ↓
Find experimentally/model-supported optimum
  ↓
Reproduce the analysis
```

---

# 32. Important Scientific Boundary

The agent must never present a calculated model parameter as an experimentally measured quantity.

Clearly distinguish:

```text
Measured
Calculated
Fitted
Estimated
Model-predicted
Literature-derived
```

For every result.

This is especially important for:

```text
effective mass
carrier concentration inferred from models
Lorenz number
band-gap estimates
scattering parameters
optimal carrier concentration
```

---

# 33. Final AI-Agent Deliverables

At completion, produce:

```text
ARCHITECTURE_AUDIT.md
ARCHITECTURE_MIGRATION_MAP.md
SCIENTIFIC_FUNCTION_MAP.md
SCIENTIFIC_REVIEW_NEEDED.md
SOFTWAREX_VALIDATION_REPORT.md
```

and the working software with:

```text
domain architecture
transport analysis
lattice thermal analysis
materials maps
composition/doping analysis
literature benchmarking
uncertainty
validation
provenance
reproducibility
tests
documentation
packaging
```

The agent must provide a final table:

```text
Feature
Status
Tests
Validation source
Known limitations
```

with statuses restricted to:

```text
IMPLEMENTED
PARTIALLY IMPLEMENTED
NOT IMPLEMENTED
```

Never mark a planned feature as implemented.

---

# 34. Absolute Priorities

When choosing between adding a new feature and improving reliability, always choose:

```text
Scientific correctness
        >
Reproducibility
        >
Validation
        >
Architecture
        >
Materials analysis depth
        >
New features
        >
UI cosmetics
```

The goal is not to make Seebeck Prime the software with the largest number of tools.

The goal is to make it a **credible, reproducible, materials-focused thermoelectric research platform**.

The strongest first release should therefore contain a small number of deep capabilities:

```text
1. Carrier Transport & Optimization
2. Lattice Thermal Transport
3. Materials Property Maps
4. Composition/Doping Analysis
5. Literature Benchmarking
```

Everything else is secondary.
