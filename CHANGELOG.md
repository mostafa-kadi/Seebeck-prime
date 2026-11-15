# Changelog

All notable changes to **Seebeck Prime** are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the version numbers follow the repository's `setup.py` version.

## [0.1.0] — 2026-11-13

First public release accompanying the SoftwareX submission.

### Architecture migration (Phases 3–6)

- **Dialogs migrated to Presentation.** All 9 live dialogs moved from the
  legacy tree to `src/presentation/dialogs/` (Step C+ included new quantity
  kinds for the device-efficiency / main-table / Hall-mobility dialogs and the
  SPB-dialog convention fix; the error-bar %-vs-fraction behaviour is
  documented-only, see the validation register §9).
- **Legacy layer deleted.** The whole `src/legacy/` tree (25 modules / 2,499
  LOC) was removed with its compatibility test; two guard tests now prevent
  reintroduction (`test_no_package_imports_the_retired_legacy_tree`,
  `test_the_retired_legacy_tree_is_no_longer_importable`). The enforced inward
  rule holds without exceptions.
- **Unit-conversion vocabulary consolidated.** `domain/units.py` is the single
  physical-unit vocabulary (34 converters incl. density, thermal diffusivity,
  specific heat, voltage, length, current, magnetic flux density, Hall
  coefficient); `application/unit_conversion.py` is the table-facing front end
  with `QuantityKind` (13 kinds) and vectorised batch conversion.
- **Validation-record consistency.** The equation-status mapping was
  regenerated after the migration (62 rows, byte-reproducible; counts unchanged
  31/23/5/3); E-56 references updated; E-59…E-62 marked RETIRED.
- **Documentation refreshed to the as-built state** (`ARCHITECTURE.md`,
  `CODE_SKELETON.md`, problem register) and the D-01 line references corrected.
- **Release hygiene:** MIT licence (`LICENSE` + `Licence.txt`), reconciled
  version 0.1.0 across the changelog, package metadata and `__version__`,
  `CITATION.cff`, corrected packaging metadata (complete runtime dependency
  closure, Python 3.12+, no placeholder contact details).

### Validation reconciliation (Phase 2)

- **Added `validation/remediation/EQUATION_STATUS_MAPPING.csv`** — one row per
  registry equation (E-01 … E-62) carrying the implementation file and
  function, the test files, the independent reference, the **numerical** /
  **physical** / **experimental** status, a validation category and the
  remaining limitation. The 62 equations are now mapped explicitly to the
  49 status rows of the results report, which resolves the long-standing
  62-vs-49 discrepancy.
- **Added `validation/remediation/VALIDATION_STATUS.md`** — the canonical
  per-equation status in the four evidence categories required by the
  validation brief (numerically verified / numerically verified but physically
  conditional / experimentally benchmarked within a defined scope / not yet
  validated): **31 / 23 / 5 / 3**. The term *fully validated* is not used for
  any calculation whose physical applicability or experimental accuracy
  remains unverified.
- **Added `validation/remediation/INITIAL_STATE_AUDIT.md`** — a read-only
  audit of the working tree recording nine confirmed defects (D-01 … D-09),
  eight missing or unverifiable items (M-01 … M-08), and the recommended
  remediation order.
- **Added `tests/scientific/test_equation_status_mapping.py`** (15 tests) — the
  guard that keeps the registry, the mapping and the status document
  consistent with each other and with the files on disk, and that checks the
  mapping is byte-identical to its generator's output.
- **Withdrawn an overstated verification claim.** The negative-lattice-
  conductivity diagnostic was reported as VERIFIED ("negative-result
  flagging"), but `validate_measurement_data`/`validate_dataset` have **no
  production caller**, so the warning never reaches the user. The lattice-
  conductivity and physical-validator rows are now **PARTIALLY VERIFIED** and
  the defect is recorded as D-01 for Phase 3.
- **Corrected the results-report counts** (audit D-07): the §8.1 summary
  claimed 50 entries with 5 partially verified, while its own table has 49
  rows with 4. Both the summary and the two reclassified rows are now
  consistent.
- **Corrected the reason given for the untested GUI dialogs.** Five of the six
  are opened with `.show()` (non-modal) and are already `QTest`-driveable;
  only `ErrorBarDialog` and `PlotDataDialog` use modal `exec()`. The previous
  claim that all six were modal was inaccurate.
- **Corrected the E-12 cross-reference** in the equation registry, which
  pointed at the SPB Seebeck equation instead of the geometry-uncertainty
  entries.
- Test suite: **607 passed, 6 skipped** (the 15 new mapping-guard tests are
  the only additions; no production code changed in this phase).

### Architecture (modular monolith, layered)

- Consolidated the scientific core into a layered package
  (`src/`): `domain` → `application` → `presentation`/`gui`,
  with `infrastructure` providing persistence adapters injected through the
  composition root (`main.py`).
- Enforced layer boundaries with automated architecture tests
  (Domain independence and filesystem-freedom, Application isolation,
  Infrastructure Qt-freedom, explicit plot-data inputs).
- Kept legacy modules (`src/legacy/core`, `src/legacy/ui`, `seebeck_prime.plot`, plugins)
  as backward-compatible adapters or domain re-exports; no legacy public
  function signatures were broken.
- Documented decisions in `docs/ARCHITECTURE_DECISION_RECORD.md` (ADRs 001–010)
  and the live dependency map in `docs/architecture/DEPENDENCY_MAP.md`.
  (Note: both files were later consolidated into `docs/ARCHITECTURE.md` in the
  2026-11-15 documentation cleanup — see that document for the dependency map
  (§3) and the design-decision classification (§6).)

### Scientific core

- Single source of truth for PF, κ_e, κ_L, ZT, Lorenz estimation,
  uncertainty propagation, SPB, Hall, weighted mobility, and device
  efficiency calculations in `seebeck_prime.domain`; duplicate inline
  implementations were replaced with domain calls after equivalence checks.
- Preserved the established Multi-Sample convention of the rounded legacy
  Lorenz constant (2.44e-8) while other workflows use the full-precision
  constant (documented in ADR-005); the two are not silently unified.
- Added a committed golden-output baseline
  (`tests/golden/baseline_outputs.json`, generated by
  `scripts/generate_golden_baseline.py`) as a regression characterization
  snapshot of the scientific core. It is self-generated, not scientific
  validation.

### Application / GUI

- Extracted pure measurement-table transforms to
  `application/measurement_processing.py`; `ThermoelectricAnalyzer` remains a
  façade with an identical public API.
- Main-table plot data preparation is now a Qt-free, explicit-input helper
  (`presentation/table_plot_data.py`); window state is adapted in
  `presentation/main_table_plots.py`.

- **Flattened the source tree under `src/`.** The layer packages are now direct
  children of `src/` (`src/domain`, `src/application`, `src/presentation`,
  `src/gui`, `src/infrastructure`, `src/plugins`, `src/legacy`), and
  `src/seebeck_prime/__init__.py` is an import-root shim that extends the
  package search path to `src/`. The public import path is unchanged
  (`from seebeck_prime.domain.calculations import ...`), so the README,
  examples, and API are unaffected. `setup.py` now maps every package
  explicitly, so a built wheel still installs the conventional
  `site-packages/seebeck_prime/…` layout without leaking top-level
  `domain`/`application` packages.

### Changed

- **Consolidated the source tree under a single import root.** The legacy
  packages were moved into the canonical package and now live under
  `src/legacy/` (`legacy/core`, `legacy/ui`), so every module
  is imported as `seebeck_prime.*` and the former duplicate
  `src.seebeck_prime.*` import path (which loaded the same files twice as two
  distinct module objects) was removed. `src/__init__.py` is no longer
  needed. The 20 empty scaffolding directories and the stale bytecode-only
  `__pycache__` folders from the earlier target layout were deleted.

### Added

- **Extended experimental validation of the complete workflow**
  (`docs/EXPERIMENTAL_BENCHMARK_VALIDATION.md`, Part II). The Seebeck-derived
  ("auto") Lorenz mode is verified against independent Fermi-Dirac and
  transport-integral references, with its conditional validity quantified
  (+2.8 % against the rigorous acoustic-phonon value, -21.7 % for optical and
  -31.8 % for ionised-impurity scattering); the four-probe, raw-Seebeck and
  laser-flash importers reproduce published properties from instrument-format
  files; the multi-sample workflow reproduces the published power factor and
  figure of merit of four materials to 1.3-5.9 %; the SPB inversion returns a
  physically correct effective mass (1.70 m_e for P-doped SiGe) and round-trips
  exactly; and the desktop workflow is validated end-to-end (file -> mapper ->
  spreadsheet -> recalculation) against published data.
- A fourth published dataset (Si80Ge20P1, DOI 10.1021/acsami.9b20090) that
  publishes electronic and lattice thermal conductivity, carrier concentration
  and carrier mobility.
- Instrument-format reconstructions of the published Bi2Te3 curves
  (`tests/experimental_benchmarks/raw/instrument/`) that exercise the
  importers end-to-end, with their derivation documented.

### Fixed

- **Fermi-Dirac integration accuracy** (SE-039): the quadrature ran without
  `epsabs`, so scipy's absolute tolerance limited the *relative* accuracy of
  small integrals (6.9e-4 for F_1/2(-20)); it is now better than 1e-8
  everywhere.
- **Raw-Seebeck import no longer aborts** on a temperature group with a single
  temperature difference (SE-040) and the **four-probe importer no longer
  raises** on a short or unrelated file (SE-041).
- **Thermal-conductivity unit conversion no longer ignores its unit argument**
  (SE-042): `kappa_to_si` / `kappa_from_si` returned the value unchanged for
  *any* unit string, so a value labelled `W/(cm·K)` was silently treated as
  `W/(m·K)` — a factor of 100 that propagates into the lattice thermal
  conductivity and the figure of merit. The unit is now validated, exactly as
  the conductivity, Seebeck and power-factor converters already did. The
  application layer's documented pass-through for an unrecognised unit is
  unchanged.

### Changed

- **Final scientific validation audit** (`docs/EXTENDED_VALIDATION_REPORT.md`):
  every result is now classified as mathematical verification, independent
  numerical verification, experimental benchmark validation, instrument-file
  parsing validation, measurement-chain validation, GUI integration validation
  or physical-model validation; the lattice-thermal-conductivity comparison is
  re-labelled an **arithmetic consistency check** where the Lorenz number is
  derived from the same published lattice conductivity; the **auto-Lorenz mode
  is explicitly not experimentally validated** (the published SiGe data imply
  the Sommerfeld value and contradict the single-parabolic-band acoustic
  model by ~35 %); the instrument files are documented as **reconstructions**
  of published curves; the raw V/I -> R -> rho -> sigma chain is recorded as
  **not implemented**; and the SPB effective mass is re-classified as a
  physical-model plausibility check because the source publication does not
  state a value that could be cross-checked.
- Added `tests/experimental_benchmarks/registry.py` (single source of truth for
  the benchmark set) and `test_report_consistency.py`, which re-measures the
  test counts and verifies that the registry, the on-disk datasets and both
  validation reports agree.

### Added

- **Experimental benchmark validation framework** (`tests/experimental_benchmarks/`,
  `docs/EXPERIMENTAL_BENCHMARK_VALIDATION.md`). Three published experimental
  datasets - Bi2Te3-based (DOI 10.1007/s10854-019-01874-0), PbTe-based
  (DOI 10.1016/j.cap.2020.06.028) and SiGe-based
  (DOI 10.1016/j.enconman.2015.01.082) - digitised from peer-reviewed papers
  by the StarryData project (CC BY 4.0). The framework keeps verbatim raw
  extracts, unit-checked temperature-matched tables, independently calculated
  expected results, and per-dataset provenance cards, and reports a
  PASS / FAIL / UNVERIFIED status for every comparison. The computed power
  factor and figure of merit reproduce the published values with maximum
  relative deviations of 1.3-4.6 % across the three materials, and the
  software matches an independent implementation of the governing equations to
  better than 1e-9 relative.

- **Scientific equation audit** (`docs/SCIENTIFIC_EQUATION_AUDIT.md`) with an
  independent analytical verification suite
  (`tests/test_scientific_equations_audit.py`, 62 tests) covering every
  transport, uncertainty, unit-conversion, Hall, SPB, phonon, device-
  efficiency and Arrhenius relation, their dimensional consistency, and
  their boundary behaviour.

### Fixed (scientific, second pass — application layer)

- **The Seebeck uncertainty was silently discarded (CRITICAL).** The
  four-probe `±S` column survived the merge with the raw-Seebeck frame, so
  pandas renamed the colliding columns and the regression uncertainty was lost;
  u(PF) was understated by up to 17x. The superseded four-probe `±S` is now
  dropped before the merge.
- **u(κₑ) now uses the domain propagator** in the file workflow, so the file
  and manual workflows no longer report different uncertainties for the same
  inputs (the previous inline expression omitted the temperature and Lorenz
  terms).
- **Column mapping no longer feeds thermal conductivity into the electrical
  conductivity slot** ("Thermal Conductivity (W/mK)" matched the
  "conductivity" alias), and the short "k" alias no longer captures a
  temperature column. Both import paths now share one case-insensitive
  matcher with physical-plausibility guards.
- **Group means are reported with the standard error of the mean** (s/√N)
  instead of the sample spread, which overstated the uncertainty of the mean
  by a factor √N.
- `u(κ)` is no longer dropped unless both `u(σ)` and `u(S)` are supplied; the
  Lorenz uncertainty is now propagated in the Seebeck-derived mode; the
  measurement-validation entry point can forward `κ_L`; the workbook branch of
  the file service is case-insensitive; and the reporting statement now
  describes the method that is actually used.

### Changed (author decisions, 2026-11-11)

- **One application-wide Lorenz number: L = 2.44e-8 W·Ω/K²** (audit issue
  SE-015). The main table and the Multi-Sample workflow previously used
  different constants (2.443004509e-8 and 2.44e-8) and now agree exactly; the
  exact Sommerfeld value remains available as
  `physical_constants.SOMMERFELD_LORENZ_EXACT` for reference.
- **Raw temperature units are taken from the file header** (audit issues
  SE-026/SE-027/SE-028). The laser-flash import no longer applies an
  unconditional +273.15 K offset — it now matches the Kappa dialog's own
  import path — and the four-probe import no longer shifts Kelvin data below
  250 K. Magnitude inference remains only as a fallback for files whose
  header declares no unit.
- **Multi-Sample reports S/cm, µV/K and mW/(m·K²) on both plotting paths**
  (audit issue SE-016), so the reported numbers no longer depend on which
  path the user takes.

### Fixed (scientific)

- **Device-efficiency engineering figure of merit (CRITICAL).** `ZT_eng` was
  computed from a mis-scaled expression with units of 1/K and returned
  8.0e-4 instead of 0.8 for constant properties, which drove the reported
  engineering efficiency to ~1e-4 instead of 7.04e-2. It now uses the
  standard Snyder form `ZT_eng = S_avg^2 * T_avg / (rho_avg * kappa_avg)`
  and the engineering and maximum efficiencies coincide for constant
  properties, as physics requires.
- **Rigorous SPB Lorenz number (CRITICAL).** The Fermi-Dirac integral used
  only the leading Sommerfeld term in the degenerate regime; because the
  Lorenz combination is a near-cancellation, this returned `L = 0` for
  eta > 50 instead of the Sommerfeld value. The expansion now includes its
  correction terms (`L(eta=80) = 2.4417e-8` vs. `2.4430e-8` exact).
- **Molar heat capacity in the Kappa tool (HIGH).** `Cp * M / 1000` produced
  values 1000x too small (kJ/(mol*K) labelled J/(mol*K)) and placed the
  Dulong-Petit overlay ~1000x off the curve.
- **Kappa dialog temperature handling (HIGH).** A magnitude heuristic
  corrupted genuine sub-273 K measurements and double-converted Kelvin
  values; the mapped source column is now treated as Kelvin, with display
  conversion only.
- Percentage uncertainties now yield non-negative "±" columns for n-type
  samples, the power-factor unit table recognises every spelling used by the
  toolbar, chemical formulas with unsupported syntax are rejected instead of
  silently mis-parsed, and the SPB Lorenz reference lines use the domain
  constants.

### Added

- Plain-text import/export support (`.txt`, `.tsv`) for the main table and
  Multi-Sample batch loading: the separator (comma, tab, semicolon, or
  whitespace) is detected on import, `#` comment lines are ignored, and
  exports are written tab-separated for direct Origin/Excel import. File
  dialog filters now list the text formats.

### Quality infrastructure

- Test suite: 241 passing tests, including architecture, golden-baseline,
  startup smoke, import/export round-trip (CSV and real XLSX), and
  dedicated headless tests for every scientific feature area (transport,
  uncertainty, units, weighted mobility, device efficiency, SPB, Hall,
  phonon/LFA, Arrhenius, analysis/alignment, validation, examples).
- CI workflow (`.github/workflows/tests.yml`) for Python 3.12 and 3.13.
- Supported-Python status documented in `docs/SUPPORTED_PYTHON.md`.
- SoftwareX preparation area: `manuscript/SoftwareX/` (compliance checklist,
  manuscript, references, citation metadata, author-controlled information;
  formerly `docs/softwarex/`).

### Known limitations

- No license file yet (`setup.py` claims MIT — pending author decision).
- CI workflow not yet executed (repository not pushed).
- Interactive GUI behavior verified by code inspection and conditional smoke
  tests only in environments where PyQt6 cannot load.
