# Supported Python Versions

Status as of 2026-11-11 (Stage 7 regression/compatibility review).

## Declared support

- `setup.py` metadata declares `python_requires=">=3.9"`.
- The test/CI workflow (`.github/workflows/tests.yml`) targets **Python 3.12 and 3.13** on `ubuntu-latest`.

## Verified environments

| Version | Where | Result |
| --- | --- | --- |
| **3.13.9** (Anaconda, Windows) | Local machine — the only environment with all dependencies installed | Full test suite passes (pytest, incl. architecture, golden-baseline, and smoke tests) |
| 3.12 | CI workflow matrix only | **Not executed** — the workflow file exists but has not been pushed/triggered yet |
| 3.14 | Present locally | **Unverified** — environment has no project dependencies installed |

## Caveats

1. The declared floor of **3.9** in `setup.py` is metadata inherited from the
   original packaging and has **not** been verified against a 3.9–3.11
   interpreter. Some syntax used in the codebase (PEP 604 `X | Y` unions are
   fine on 3.10+; `from __future__ import annotations` covers annotations) may
   not run on 3.9 as-is. Do not advertise 3.9 support until it is tested on a
   3.9 environment or the floor is raised deliberately.
2. Interactive GUI startup (`import main` + window creation) was verified only
   by code inspection and conditional smoke tests: the local Windows Anaconda
   environment cannot load the PyQt6 `QtWidgets` DLL, so the smoke test skips
   there and runs in CI/other environments with working Qt bindings.
3. Dependency floor versions are not pinned (`requirements.txt` has no
   version specifiers); reproducibility depends on the authors' chosen
   environment.

## Recommendation for the SoftwareX paper

State the supported range as **Python 3.12+ (tested on 3.13)** once CI has
actually executed, and either verify or drop the 3.9 claim from `setup.py`
before submission. Both actions are author decisions and are tracked in
`manuscript/SoftwareX/SOFTWAREX_COMPLIANCE_CHECKLIST.md`.
