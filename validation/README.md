# Scientific Validation Package — Seebeck Prime

This directory contains the **scientific validation** of Seebeck Prime: an
inventory of every implemented calculation, a plan for validating it,
independently written reference implementations, the measured results, and
an explicit statement of what remains unverified.

| Document | Purpose |
|---|---|
| [`SCIENTIFIC_EQUATION_REGISTRY.md`](SCIENTIFIC_EQUATION_REGISTRY.md) | **The inventory.** Every implemented calculation (E-01 … E-62) with its equation, source, units, assumptions, validity conditions, numerical method, tests and known limitations. |
| [`SCIENTIFIC_CALCULATION_TEST_PLAN.md`](SCIENTIFIC_CALCULATION_TEST_PLAN.md) | **The plan.** What has to be demonstrated for each calculation, the evidence classes (analytical / independent numerical / experimental), and the derivation of every tolerance. |
| [`INDEPENDENT_REFERENCE_METHODS.md`](INDEPENDENT_REFERENCE_METHODS.md) | **The method.** The derivations, conventions (Blatt vs unnormalised Fermi integrals, Γ factors, scattering exponent), quadrature strategies, and the two occasions on which the *reference* — not the application — was wrong. |
| [`SCIENTIFIC_CALCULATION_TEST_RESULTS.md`](SCIENTIFIC_CALCULATION_TEST_RESULTS.md) | **The result.** Environment, commands, test counts, skip reasons, the application-vs-reference comparison table, the published-measurement comparisons, and the final status table. |
| [`SCIENTIFIC_VALIDATION_LIMITATIONS.md`](SCIENTIFIC_VALIDATION_LIMITATIONS.md) | **The honest boundary.** Everything the validation cannot establish, written as negative findings. |
| [`SCIENTIFIC_BENCHMARK_MATERIAL_FAMILIES.md`](SCIENTIFIC_BENCHMARK_MATERIAL_FAMILIES.md) | **Phase X.** The published-data landscape for the seven material families, which are active benchmarks and which are not, and why. |
| [`reference_comparison_table.md`](reference_comparison_table.md) | The generated application-vs-reference comparison table (regenerate with `tools/generate_reference_comparison.py`). |

### Remediation package (Phase 2 onwards)

| Document | Purpose |
|---|---|
| [`remediation/INITIAL_STATE_AUDIT.md`](remediation/INITIAL_STATE_AUDIT.md) | **The read-only audit** of the current working tree: what exists, what is missing, what is genuinely defective (D-01 … D-09, M-01 … M-08), what cannot be verified from the files, and the recommended remediation order. |
| [`remediation/EQUATION_STATUS_MAPPING.csv`](remediation/EQUATION_STATUS_MAPPING.csv) | **The bridge.** One row per equation (E-01 … E-62): implementation file and function, test files, independent reference, numerical / physical / experimental status, validation category and remaining limitation. Regenerate with `tools/generate_equation_status_mapping.py`. |
| [`remediation/VALIDATION_STATUS.md`](remediation/VALIDATION_STATUS.md) | **The canonical status.** The four evidence categories, the scope of every experimental claim, the reproduced test accounting, and the explanation of the 62-vs-49 difference between the registry and the results report. |

The registry, the mapping and `VALIDATION_STATUS.md` are kept consistent by
`tests/scientific/test_equation_status_mapping.py`, which also checks that the
mapping is byte-identical to the generator's output.

## Code

| Path | Purpose |
|---|---|
| [`independent_calculations/`](independent_calculations/) | The independent reference implementations. They **never** import the application; the test suite proves it by parsing their AST. |

## How to reproduce

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'

# the full suite
C:\Users\Elkady\anaconda3\python.exe -m pytest -q -p no:cacheprovider

# the new scientific suites
C:\Users\Elkady\anaconda3\python.exe -m pytest tests\scientific -q -p no:cacheprovider

# the GUI subset (needs a working Qt; see the results report §1.2)
C:\Users\Elkady\AppData\Local\Temp\opencode\seebeck-gui\Scripts\python.exe -m pytest tests\experimental_benchmarks\test_gui_end_to_end.py tests\test_startup_smoke.py -q -p no:cacheprovider

# regenerate the comparison table and the material-family survey
C:\Users\Elkady\anaconda3\python.exe tools\generate_reference_comparison.py
C:\Users\Elkady\anaconda3\python.exe tools\survey_material_families.py
```

## Reading order

1. The **limitations** document first — it states what the evidence does
   and does not support.
2. Then the **results** document, which gives the evidence.
3. Then the **registry** for the per-calculation detail.
4. The **plan** and the **reference methods** for how the evidence was
   obtained.

## One-sentence summary

> Seebeck Prime's implemented scientific calculations have been
> independently re-derived and verified numerically (agreement at 1e-14 to
> 1e-6), its unit handling and physical constraints have been systematically
> tested, and its core transport outputs reproduce four published
> specimens' power factors and figures of merit to within 1.3–5.9 %. Its
> physical models, its interactive GUI paths and its raw measurement chain
> remain outside the verified set.
