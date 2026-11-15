# Examples

## Contents

- `example_dataset.csv` — a small, **synthetic**, Bi2Te3-like n-type dataset
  (11 temperature points from 300 K to 500 K) with the four primary input
  columns in SI base units. The values are generated from simple smooth
  temperature trends purely to exercise the software; they are **not
  experimental data and not reference data**.
- `example_dataset.txt` — the same dataset as tab-separated plain text, for
  testing the text import path (File → Open).
- `headless_analysis.py` — a GUI-independent usage example that loads the
  dataset, computes Power Factor, electronic and lattice thermal
  conductivity, and ZT with the domain layer, prints a summary table, and
  can write the results to a CSV file.

## Running

From the repository root:

```bash
python examples/headless_analysis.py                # print a summary table
python examples/headless_analysis.py out/results.csv  # also write results CSV
```

## Expected input columns

| Column | Unit |
| --- | --- |
| `Temperature (K)` | K |
| `Seebeck (V/K)` | V/K |
| `Electrical Conductivity (S/m)` | S/m |
| `Thermal Conductivity (W/(m*K))` | W/(m·K) |

The desktop application additionally accepts display units (°C, µV/K, S/cm)
and converts internally; see the main `README.md`.
