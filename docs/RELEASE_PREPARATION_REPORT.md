# Release Preparation Report — Seebeck Prime 0.1.0 (SoftwareX)

**Status:** COMPLETE — local release preparation finished; all three test
suites green; the public release (GitHub push, tag, DOI) remains an
author-side action recorded in `RELEASE_READINESS.md`.
**Authorization:** User approved the release work ("release anything
consistent with SoftwareX journal") and chose **MIT** for the licence and
**0.1.0** for the release version.
**Rollback:** local backups at
`C:\Users\Elkady\Documents\seebeck_new\Seebeck-Prime_backup_2026-11-13.zip`
(working tree) and `Seebeck-Prime_history_2026-11-13.bundle` (git history);
nothing has been committed.

---

## 1. Author decisions (2026-11-13)

| Decision | Choice | Rationale |
|---|---|---|
| Licence (audit D-04) | **MIT** | User-selected; OSI-approved as SoftwareX requires; consistent with `src/seebeck_prime/__init__.py`, which already declared `__license__ = "MIT"` |
| Release version (audit D-03) | **0.1.0** | Minimal-change reconciliation: `CHANGELOG.md`, `setup.py` and manuscript metadata C1 already said 0.1.0; only `__version__` ("1.0.0-dev") changed |

## 2. What was created / changed

| File | Change |
|---|---|
| `LICENSE` (new) + `Licence.txt` (new) | MIT text; copyright line `Copyright (c) 2026 Mostafa M. Elkady` mirrors the identity declared in the source tree (`__author__`); `Licence.txt` satisfies the SoftwareX OSP requirement (paper returned if missing) |
| `setup.py` | `license="MIT"`; **invented contact details removed** (`author="Seebeck Prime Development Team"`, `author_email="development@seebeck-prime.com"` — fields omitted pending the confirmed author list, with an explanatory comment); repository URL set to the README's URL (was the template placeholder); `python_requires>=3.12` (was stale `>=3.9`, contradicting `docs/SUPPORTED_PYTHON.md`); **runtime dependency closure completed** (`scienceplots`, `openpyxl`, `qtawesome` added — measured hard imports; `pytz` removed — no import in `src/`); README read with explicit UTF-8; Windows-specific classifier (only Windows verified) |
| `src/seebeck_prime/__init__.py` | Docstring version and `__version__` → `0.1.0` |
| `CHANGELOG.md` | `[0.1.0] — Unreleased` → `[0.1.0] — 2026-11-13` with a first-release note and a new "Architecture migration (Phases 3–6)" subsection (dialogs migrated, legacy tree deleted, unit vocabulary consolidated, validation-record consistency, docs refresh, release hygiene) |
| `CITATION.cff` (new) | cff 1.2.0: title, version 0.1.0, date-released 2026-11-13, MIT, repository URL, keywords, abstract; author entry mirrors `__author__` with an explicit TODO to confirm the author list before DOI minting |
| `pyproject.toml` | Machine-specific `[tool.pyrefly]` interpreter path removed (audit D-06); build-system table unchanged — package metadata remains in `setup.py` (the established single source) |
| `README.md` | Stale suite counts (592/6) → current (738/10, 745/6, 119/7); installation section (wheel install + from source + PyQt6 6.9.1 pin note); new sections: **Architecture** (measured layer table, inward rule), **Scientific Status & Capability Boundaries** (numerically-verified ≠ experimentally-validated, four-specimen benchmark scope, not-implemented list, D-12 disclosure, golden-baseline caveat), **Licence**, **Citation**, **Support** |
| `.github/workflows/tests.yml` | Static-checks job added (register CR-07/ENV-04): ruff security-rule gate (baseline 2) and mypy gate (baseline 9, CR-14) beside the existing pytest matrix; **execution requires the push** (M-08 open) |
| `manuscript/SoftwareX/MANUSCRIPT.tex` | C1 → "0.1.0 (released 2026-11-13…)"; C2 → repository URL (still flagged: repo must be made public); C3 → MIT with licence-file note; "Current executable software version" table filled (permanent link, MIT, 0.1.0, 2026-11-13, repository) |
| `manuscript/SoftwareX/SOFTWARE_METADATA.md` | Version/licence/packaging/citation marked RESOLVED with evidence; availability step precise (public GitHub + tag + Zenodo remain); PyQt6 6.12 note added; completeness checklist updated (2 of 6 boxes ticked) |
| `manuscript/SoftwareX/SOFTWAREX_COMPLIANCE_CHECKLIST.md` | Item 3 "substantially filled"; item 4 updated (local preparation complete, public release pending); item 5 RESOLVED (MIT); T2 updated; T4 "Met locally" |
| `docs/CODE_PROBLEMS_REGISTER.md` | ENV-04 partially addressed (CI authored, execution pending push); ENV-06 RESOLVED (version/licence/URL/pyrefly path); §10 rows 5 and 9 updated |
| `RELEASE_READINESS.md` (new) | Master release-status document: completed items with evidence, the 8 remaining author actions in order, honest caveats, version statement |

## 3. Distribution build & install verification (D-05/D-06)

- `python -m build` → `dist/seebeck_prime-0.1.0-py3-none-any.whl` and
  `dist/seebeck_prime-0.1.0.tar.gz` (rebuilt after the final README/pyproject
  edits; both licence files and the final README are embedded).
- Wheel contents verified: **60 `.py` files** — exactly matching the 60-module
  source tree, all inside the conventional `seebeck_prime/` package directory
  (the import-root shim is a no-op there); `Requires-Python: >=3.12`; the
  complete 8-package runtime dependency closure declared.
- **Clean-venv install (fresh venv, no system site-packages):** the wheel
  resolved its full dependency set from PyPI (PyQt6 6.12.0, numpy 2.5.4,
  pandas 3.1.1, scipy 1.18.1, matplotlib 3.11.2, scienceplots, openpyxl,
  qtawesome) and installed cleanly.
- **Import closure in the clean venv:** domain, application,
  presentation + all dialogs, infrastructure, gui, plugins all import;
  `seebeck_prime.__version__` = 0.1.0 from `site-packages`.
- **Physics-valued smoke from the wheel:** T = 300 K, σ = 1e5 S/m,
  S = 150 µV/K, κ = 2.5 W/mK, L = 2.44e-8 → PF = 2.25e-3 W/K²m, κe = 0.732,
  κL = 1.768, ZT = 0.27 — every value exact against hand calculation.
- **PyQt6 6.12.0 caveat:** pip's newest binding fails `QtWidgets` on the
  development machine's Windows build (DLL entry-point error, `0xc0000139` —
  same class as the documented conda 6.11.0 issue); installing **PyQt6
  6.9.1** in the clean venv fixed it and completed the verification. The
  wheel deliberately does not pin PyQt6; the README documents the fallback
  pin. The clean-venv check used the newer numpy/pandas/scipy stack
  successfully, but the **full test suites were not re-run against that
  stack** — the documented development environments remain the authoritative
  verification.

## 4. Verification

| Suite | Result |
|---|---|
| conda environment (full suite) | **738 passed, 10 skipped**, exit 0 |
| Qt-capable environment (`%TEMP%\opencode\seebeck-gui2`, rebuilt from the documented recipe after temp-cleanup wiped it) | **745 passed, 6 skipped**, exit 0 |
| Benchmark suite (`tests/experimental_benchmarks`) | **119 passed, 7 skipped**, exit 0 |
| Editable-install metadata refresh | `pip show seebeck-prime` → Version 0.1.0, License: MIT |
| Sdist spot-check | `pyproject.toml` inside the sdist has no machine-specific path; `LICENSE`, `Licence.txt`, `README.md` bundled |

All suite numbers are identical to the Phase 5/6 baselines — the release work
changed no scientific code paths (the only source change is the version
string in the import-root shim).

## 5. Honest boundary of this release

- The repository is **not yet public** and nothing has been committed/pushed —
  both require explicit user approval (register ENV-05 stands).
- The software-availability requirement of SoftwareX is therefore **not yet
  satisfied**; `RELEASE_READINESS.md` §2 lists the exact author-side steps
  (push, public repo, commit, tag `v0.1.0`, GitHub release, Zenodo DOI, CI
  execution, support email, Figure 2, TeX compile).
- Author metadata (author list, ORCIDs, affiliation, funding, competing
  interests, support email C8, AI-tool disclosure names) remain
  `[AUTHOR TO CONFIRM]` placeholders by policy — nothing was invented.
