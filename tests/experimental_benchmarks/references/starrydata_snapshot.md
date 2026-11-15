# Source snapshot — StarryData (NIMS)

## What this data is

The benchmark datasets in this directory are derived from the
[Starrydata](https://starrydata.nims.go.jp/) project (National Institute for
Materials Science, Japan), which digitises experimental plots from published
papers into structured, machine-readable data.

* Project: **ThermoelectricMaterials**
* Database snapshot: **2026-11-11 02:00:02 UTC+0900 (JST)**
* Manifest: <https://starrydata.github.io/starrydata_datasets/manifest.json>
* Release (download base):
  `https://github.com/starrydata/starrydata_datasets/releases/latest/download`

## Files used and their published checksums

| File | Rows | Bytes | SHA-256 |
|---|---|---|---|
| `ThermoelectricMaterials_papers.csv.gz` | 9 562 | 1 479 311 | `bc2ce54dcf85b15eff165b477c6dfa63693221021751c138eb35ce2622471e8b` |
| `ThermoelectricMaterials_samples.csv.gz` | 55 780 | 2 085 998 | `8d93b72e3b32101b19a04242e1b2fefe8d3cf5b404d4b85178adb659fb714453` |
| `ThermoelectricMaterials_curves.csv.gz` | 158 531 | 25 532 288 | `dc4d9eaad2b90a20b27e35e1b74533bafe704ba1a6962ae5aa27739823914734` |

`extract_benchmarks.py` re-downloads these files and verifies the checksums
before using them, so the committed extracts can always be re-derived.

## Data model

| Table | Key columns |
|---|---|
| `papers` | `SID`, `DOI`, `URL`, `issued`, `author`, `title`, `container_title`, `project_names` |
| `samples` | `sample_name`, `sample_id`, `composition`, `composition_details`, `SID`, `DOI`, `sample_info` (measurement conditions) |
| `curves` | `SID`, `DOI`, `composition`, `sample_id`, `figure_id`, `figure_name`, `prop_x`, `prop_y`, `unit_x`, `unit_y`, `x` (JSON list), `y` (JSON list), `comments` |

Each **curve** is one property-versus-temperature dataset digitised from one
figure of one paper, with the property names and units as published.

### Joining rule

`(SID, sample_id)` is the unique key. The daily changelog of the dataset warns
that datasets published between 2026-04-01 and 2026-09-04 contain duplicated
`sample_id` values across papers; the snapshot used here (2026-11-11) is after
the announced fix, and the benchmark extraction always joins on `(SID,
sample_id)` regardless.

### Units in the thermoelectric field (all SI)

| Property | Unit string |
|---|---|
| Seebeck coefficient | `V*K^(-1)` |
| Electrical conductivity | `ohm^(-1)*m^(-1)` |
| Electrical resistivity | `ohm*m` |
| Thermal conductivity | `W*m^(-1)*K^(-1)` |
| Lattice / electronic thermal conductivity | `W*m^(-1)*K^(-1)` |
| Power factor | `W*m^(-1)*K^(-2)` |
| ZT | `-` |

The unit strings are validated in `test_benchmarks.py`; nothing is assumed.

## Licence and attribution

* Digitised data: **CC BY 4.0** (<https://creativecommons.org/licenses/by/4.0/>).
* The measurements themselves belong to the original publications (see the
  per-benchmark provenance cards).
* Please cite the source publication and the Starrydata project when reusing
  these data.

## Selection procedure used for the benchmarks

The candidate pool was screened for **internal consistency of the published
data** before any benchmark was chosen, so that a comparison failure would
indicate a software problem rather than a mis-assigned curve:

1. candidates must provide temperature-dependent Seebeck coefficient, electrical
   conductivity **and** thermal conductivity curves for the same
   `(SID, sample_id)`, plus a published power factor and a published ZT;
2. the published power factor must agree with S²σ computed from the published
   S and σ (within 5 % over the published temperature grid);
3. the published ZT must agree with PF·T/κ computed from the published PF and
   the published κ (within 5 % over the published temperature grid).

Of 501 candidates that satisfied criterion 1, **238 passed criteria 2 and 3**
(207 Bi2Te3-based, 25 PbTe-based, 6 SiGe-based). The three selected benchmarks
are among those, and were chosen for one per requested material family and for
the richness of their published property set.

Candidates that failed the consistency screen are **not** used as benchmarks;
they indicate mis-assigned or mis-digitised curves in the source database
rather than anything about Seebeck Prime.
