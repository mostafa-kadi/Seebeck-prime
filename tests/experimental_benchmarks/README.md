# Experimental Benchmark Framework

This directory contains **published experimental benchmarks** for Seebeck Prime:
real measurements taken from peer-reviewed papers, digitised by the
[StarryData](https://starrydata.nims.go.jp/) project (NIMS), used to verify
that the software reproduces independently reported thermoelectric properties.

The benchmarks are deliberately kept **outside** the synthetic-data test suite:
`tests/test_scientific_equations_audit.py` verifies that the code implements the
governing equations; this framework verifies that the code produces the right
answers **for real materials**.

## Layout

```text
tests/experimental_benchmarks/
├── README.md                 this file
├── extract_benchmarks.py     reproducible extraction (download → verify → extract)
├── raw/                      verbatim curve rows from the source database
├── references/               provenance cards (one per benchmark) + source snapshot
├── processed/                temperature-matched, unit-checked tables
├── expected_results/         results from an INDEPENDENT equation implementation
└── test_benchmarks.py        the automated benchmark tests
```

## Ground rules

* **Raw data are never modified.** `raw/` contains the original CSV rows of the
  source database, including the JSON-encoded x/y value lists and every
  metadata column (DOI, SID, sample_id, figure_id, unit_x, unit_y, …).
* **Every processed value is traceable.** `references/<benchmark>.md` records
  the paper, its DOI, the journal, the source snapshot and its checksums, the
  measurement conditions recorded by the database, the original units, and the
  extraction method.
* **Expected results are computed independently.** `extract_benchmarks.py`
  implements PF = S²σ, κₑ = LσT, κ_L = κ − κₑ and ZT = PF·T/κ **without
  importing Seebeck-Prime**, so the comparison in `test_benchmarks.py` is
  software-versus-independent-implementation, not software-versus-itself.
* **No simulated data are used as experimental references.** The example data in
  `examples/` are synthetic and are clearly labelled as such; they are not part
  of this framework.

## The benchmarks

| Benchmark | Material family | Publication | DOI | Grids |
|---|---|---|---|---|
| `b2te3_bi2te2_4se0_6cu0_006` | Bi2Te3-based | *Effect of Cu electroless plating on thermoelectric properties of n-type Bi2Te2.4Se0.6 alloy* | 10.1007/s10854-019-01874-0 | PF, ZT, κ_L |
| `pbte_pbte0_95pbs0_05` | PbTe-based | *Thermoelectric performance in pseudo-ternary (PbTe)0.95-x(Sb2Se3)x(PbS)0.05 system…* | 10.1016/j.cap.2020.06.028 | PF, ZT, κ_L |
| `sige_si80ge18sb2` | SiGe-based | *Thermoelectric performance of Si80Ge20−xSbx based multiphase alloys…* | 10.1016/j.enconman.2015.01.082 | PF, ZT |

All three datasets are published in SI units (S·K⁻¹, S·m⁻¹, W·m⁻¹·K⁻¹), and the
unit strings are validated in the test suite rather than assumed.

## Comparison classes

| Class | What is compared | Tolerance | Rationale |
|---|---|---|---|
| A | Software vs. the independent implementation | 1e-9 relative | identical algebra; only float round-off may differ |
| B | Software vs. the **published** power factor | 5 % relative | digitisation (~1 %) + interpolation of S, σ, κ onto the published grid (1–2 %) + the paper's own rounding |
| C | Software vs. the **published** ZT | 10 % relative | ZT accumulates the PF and κ contributions |
| D | Lattice κ vs. the **published** lattice κ, using the Lorenz number implied by the published data | 5 % relative | isolates the arithmetic from the authors' Lorenz assumption |
| E | Quantities the paper does not publish | — | reported as **UNVERIFIED**, never silently skipped |

The tolerances are derived from the measurement chain (section 5 of
`docs/EXPERIMENTAL_BENCHMARK_VALIDATION.md`); they are not chosen to make the
tests pass. A unit error, a sign error or a wrong equation would exceed them
by orders of magnitude.

## Extended validation (Part II of the report)

| Module | Scope |
|---|---|
| `test_auto_lorenz.py` | The Seebeck-derived ("auto") Lorenz mode: S <-> eta relation, Fermi-Dirac integral conventions, scattering assumptions, the rigorous SPB Lorenz number, integration accuracy, inversion convergence and failure handling, kappa_e / kappa_L / ZT, and the **conditional validity** of the empirical fit (quantified against independent transport-integral references) |
| `test_instrument_importers.py` | The four-probe, raw-Seebeck and laser-flash importers: temperature association, unit conversions, sign conventions, regression behaviour, grouping, invalid/missing measurements and the geometry-uncertainty combination |
| `test_workflow_validation.py` | Multi-sample processing (vs published PF/ZT), weighted mobility (vs an independent implementation) and the SPB inversion (vs the published carrier concentration) |
| `test_gui_end_to_end.py` + `gui_workflow_driver.py` | The desktop workflow end-to-end: file -> column mapper -> spreadsheet -> recalculation, display-unit vs base-unit paths, and the rendered values |
| `raw/instrument/` | Instrument-format reconstructions of the published Bi2Te3 curves that exercise the importers (derivation documented in `raw/instrument/README.md`) |

The GUI test drives the workflow in a **separate process**: a `QApplication`
must exist before any widget is constructed and Qt aborts the interpreter
natively otherwise. Where the Qt runtime is broken, the module is skipped with
an explicit reason.

## Reproducing the extraction

```bash
python tests/experimental_benchmarks/extract_benchmarks.py            # core benchmarks
python tests/experimental_benchmarks/extract_workflow_benchmarks.py  # + carrier data, 4th dataset, instrument files
```

The script downloads the three StarryData source files (~29 MB), verifies
their SHA-256 checksums against the published daily manifest, and regenerates
`raw/`, `processed/`, `expected_results/` and `references/`. The committed
datasets were produced with the snapshot

```
db_snapshot  2026-11-11 02:00:02 UTC+0900 (JST)
```

## Running the benchmarks

```bash
python -m pytest tests/experimental_benchmarks -v -s
```

`-s` shows the per-benchmark PASS / FAIL / UNVERIFIED summary and the error
metrics.

## Attribution and licence

* The **measurements** belong to the publications listed in `references/` (© the
  respective authors).
* The **digitised data** are provided by the Starrydata project under
  **CC BY 4.0** (<https://creativecommons.org/licenses/by/4.0/>).
* When reusing these benchmark data, please cite the source publication *and*
  the Starrydata project.
