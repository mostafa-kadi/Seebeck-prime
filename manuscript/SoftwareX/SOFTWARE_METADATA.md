# Seebeck-Prime — Software Metadata (Stage 4)

**Document type:** Stage 4 deliverable of the SoftwareX manuscript preparation.
**Date:** 2026-11-12
**Status:** Metadata draft — author confirmation required for unresolved fields.

---

## 1. Completed fields (from repository evidence)

| Field | Value |
|---|---|
| Software name | Seebeck-Prime |
| Software type | Open-source desktop application + headless Python API for thermoelectric transport-property analysis |
| Programming language | Python |
| Operating system | Windows (primary); Linux/macOS intended per `docs/SUPPORTED_PYTHON.md` (Python 3.12+/3.13) |
| Dependencies | NumPy, SciPy, pandas, Matplotlib, scienceplots, PyQt6, qtawesome; see `requirements.txt` |
| Software functionality | Transport calculations, Lorenz models, SPB, Hall, weighted mobility, phonon, device efficiency, uncertainty, units, workflows, GUI, plotting, export |
| Documentation | `README.md`, `docs/`, `validation/` |
| Test suite | **738 passed, 10 skipped** (primary conda); **745 passed, 6 skipped** (Qt-capable); **119 passed, 7 skipped** (benchmark suite) — all exit 0 (2026-11-13, Phase 5/6) |
| Official SoftwareX template | **Obtained 2026-11-12** (unmodified) in `manuscript/SoftwareX/templates/` (`.tex` + `.docx`); `MANUSCRIPT.tex` produced from the official OSP template |

## 2. Resolved and remaining fields (updated 2026-11-13)

| Field | Status |
|---|---|
| Current version | **RESOLVED 2026-11-13:** `0.1.0` released — reconciled across `CHANGELOG.md` (released heading), `setup.py` and `src/seebeck_prime/__init__.py` (`__version__ = "0.1.0"`); audit item D-03 closed |
| License | **RESOLVED 2026-11-13:** MIT — `LICENSE` + `Licence.txt` (SoftwareX-required filename) in the repository; `setup.py` license/classifier aligned; audit item D-04 closed |
| Packaging metadata | **RESOLVED 2026-11-13:** wheel/sdist build verified; runtime dependency closure completed in `setup.py` (`scienceplots`, `openpyxl`, `qtawesome` added; `pytz` removed — unimported); invented contact details removed; `python_requires>=3.12`; clean-venv install of the wheel verified with a physics-valued smoke run (audit items D-05/D-06 verified locally) |
| Citation metadata | **RESOLVED 2026-11-13:** `CITATION.cff` (cff 1.2.0, v0.1.0, MIT, repository URL; author entry mirrors `__author__` — confirm at submission) |
| Public repository / distribution URL | **Open (author action):** candidate URL `https://github.com/mostafa-kadi/Seebeck-prime` (taken from the existing README); the repository must be pushed **public** and tagged `v0.1.0` before submission |
| Developer / affiliation | **Open (author input)** — required for the title page and CFF/ORCID completeness |
| User support (support email, C8) | **Open (author input)** |
| Release / archiving step | **Partially open:** public GitHub release + Zenodo DOI minting remain author-side actions |
| PyQt6 pin note | **Documented:** PyQt6 6.9.1 verified on the development machine; pip's 6.12.0 failed there with a `QtWidgets` DLL entry-point error (`0xc0000139`); README documents the fallback pin |

## 3. Software availability

Local release preparation is complete (licence, version, citation metadata,
packaging verification). The software-availability requirement itself is
satisfied only once the repository is **public** (GitHub-only per the OSP
template) and the accepted version is archived with the journal; both remain
author-side steps.

## 4. Metadata completeness checklist for the final submission

- [x] Version reconciled (D-03 closed 2026-11-13)
- [x] License confirmed (D-04 closed 2026-11-13 — MIT)
- [ ] Distribution / repository URL confirmed (candidate URL present; repository must be made public + tagged `v0.1.0`)
- [ ] Author information confirmed (CFF entry, title page, ORCIDs)
- [ ] Release archived (public GitHub release + Zenodo DOI)
- [ ] Compliance checklist completed (`SOFTWAREX_COMPLIANCE_CHECKLIST.md`)
