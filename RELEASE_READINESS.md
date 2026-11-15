# Seebeck Prime — Release Readiness

**Status:** Release preparation **complete locally** (2026-11-13); the public
release itself (GitHub push, tag, Zenodo DOI) is an author-side action.
**Target venue:** SoftwareX (Elsevier) — Open Source Process ("OSP").
**Scope of this document:** everything needed to make the repository
submission-ready, with the exact remaining author actions.

---

## 1. Completed (2026-11-13)

| Item | State | Evidence |
|---|---|---|
| Licence (audit D-04) | **MIT**, chosen by the author | `LICENSE` + `Licence.txt` (SoftwareX-required filename, identical MIT text); `setup.py` `license="MIT"` + classifier; `CITATION.cff` license field |
| Version reconciliation (audit D-03) | **0.1.0 everywhere** | `CHANGELOG.md` `[0.1.0] — 2026-11-13` (released heading + Phases 3–6 entry); `setup.py` `version="0.1.0"`; `src/seebeck_prime/__init__.py` `__version__ = "0.1.0"` (was `1.0.0-dev`); manuscript C1 updated |
| Packaging metadata (audit D-05 / ENV-06) | **Corrected** | Placeholder repository URL replaced with the README URL; **invented contact details removed** (`author`/`author_email` omitted pending the confirmed author list, commented in `setup.py`); `python_requires>=3.12` (was the stale `>=3.9`); runtime dependency closure completed (`scienceplots`, `openpyxl`, `qtawesome` added — they are hard imports; `pytz` removed — nothing imports it); machine-specific `[tool.pyrefly]` interpreter path removed from `pyproject.toml` (audit D-06) |
| Distribution build (audit D-05) | **Built and verified** | `dist/seebeck_prime-0.1.0-py3-none-any.whl` + `dist/seebeck_prime-0.1.0.tar.gz` via `python -m build`; wheel contains exactly **60 `.py` files** in the conventional `seebeck_prime/` layout (matches the source tree 1:1, incl. `presentation/dialogs`); `Requires-Python: >=3.12`; both licence files bundled as `License-File` |
| Clean-venv install (audit D-06 follow-through) | **PASSED** | Fresh venv (`%TEMP%\opencode\seebeck-clean`, no system site-packages) + `pip install` of the wheel resolved the full dependency set from PyPI; full layer closure imports (domain, application, presentation+dialogs, infrastructure, gui, plugins); physics-valued smoke: T=300 K, σ=1e5 S/m, S=150 µV/K, κ=2.5 W/mK, L=2.44e-8 → PF=2.25e-3 W/K²m, κe=0.732, κL=1.768, ZT=0.27 — all exact; `__version__` = 0.1.0 from site-packages (shim is a no-op in the wheel layout) |
| PyQt6 binding note | **Documented** | On the development machine, pip's **PyQt6 6.12.0** fails `QtWidgets` with a DLL entry-point error (`0xc0000139`); the verified combination is **PyQt6 6.9.1** (used by the Qt test environment). README documents the fallback pin `pip install PyQt6==6.9.1` |
| `CITATION.cff` | **Created** | cff 1.2.0; title, version 0.1.0, date-released 2026-11-13, MIT, repository URL, keywords, abstract; author entry mirrors the identity declared in `src/seebeck_prime/__init__.py` (`__author__ = "Mostafa M. Elkady"`) with an explicit TODO to confirm the full author list |
| README (SoftwareX T4) | **Refreshed** | Installation (wheel + from source + PyQt6 pin note), architecture section (measured layer counts, inward rule), scientific status & capability boundaries (numerically-verified ≠ experimentally-validated; not-implemented list; D-12 disclosure), licence, citation, support sections; current suite numbers (738/10, 745/6, 119/7) replace the stale 592/6 |
| CI definition (register CR-07 / ENV-04 / M-08) | **Authored** | `.github/workflows/tests.yml`: existing pytest matrix (3.12/3.13, offscreen Qt) + new `static` job with ruff security-rule gate (baseline 2) and mypy gate (baseline 9, CR-14) — **execution requires the repository push** |

## 2. Remaining author actions (in order)

| # | Action | Why it blocks |
|---|---|---|
| 1 | Push the repository to <https://github.com/mostafa-kadi/Seebeck-prime> and make it **public** | SoftwareX accepts GitHub-only repositories; the paper is returned if `README.md` / `Licence.txt` are missing there |
| 2 | Commit the working tree and tag `v0.1.0` (release date 2026-11-13) | The tag anchors the "current code version" C1 and the Zenodo release; version control hygiene (register ENV-05) is still a single commit — nothing has been committed without your approval |
| 3 | Confirm the author list / legal copyright holder, ORCIDs, affiliation, funding, competing interests, support e-mail (C8) | Title page, `CITATION.cff` authors, `setup.py` maintainer fields, and the manuscript declarations all await this input (`[AUTHOR TO CONFIRM]` placeholders) |
| 4 | Create the GitHub release `v0.1.0` with the built wheel attached (optional but recommended) | Makes the "current code version" concrete; feeds step 5 |
| 5 | Mint the Zenodo DOI for the `v0.1.0` release and fill it into `CITATION.cff` (`doi:` field), the README Citation section, and the manuscript C2 | SoftwareX prefers a permanent DOI for the archived code version |
| 6 | Execute CI: let the pushed workflow run (M-08) | First execution of the test + static gates; report any platform failures |
| 7 | Capture the GUI screenshot (manuscript Figure 2) | Figure 2 is author-side |
| 8 | Compile `MANUSCRIPT.tex` on Overleaf or a local TeX installation (with `references.bib`) | No LaTeX toolchain locally; template-structure verification (checklist item T9) |

## 3. Known, honest caveats recorded at release time

- **PyQt6 6.12.0** fails on the development machine's Windows build (DLL
  entry-point error); the wheel does **not** pin PyQt6 — other systems may use
  the newest binding. The verified combination is documented in the README.
- The clean-venv verification pulled **numpy 2.5.4 / pandas 3.1.1 / scipy
  1.18.1** from PyPI — newer than the development environment's pinned
  conda versions (numpy 2.3.5). Imports and the smoke run passed with the
  newer stack; the full test suites were **not** re-run against it (the
  development suites remain the authoritative verification, run with the
  documented environment).
- The release-year copyright line in `LICENSE` uses the name declared in the
  source tree (`__author__`); if the confirmed legal copyright holder differs,
  that is a one-line edit in both `LICENSE` and `Licence.txt`.

## 4. Version statement

Current code version: **0.1.0** (released 2026-11-13).
Code versioning system: git.
Declared consistently in: `CHANGELOG.md`, `setup.py`,
`src/seebeck_prime/__init__.py`, `CITATION.cff`, manuscript metadata table C1
and the "Current executable software version" table.
