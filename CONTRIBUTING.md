# Contributing to Seebeck Prime

Thank you for considering a contribution. This document summarizes the
practical rules that keep the project scientifically reliable and
architecturally consistent.

## Getting set up

```bash
git clone https://github.com/mostafa-kadi/Seebeck-prime.git
cd Seebeck-prime
pip install -r requirements.txt
python -m pytest -q
```

See `docs/SUPPORTED_PYTHON.md` for verified Python versions.

## Rules that apply to every change

1. **Scientific equations are protected.** The authoritative equations live in
   `src/domain/` (see `docs/SCIENTIFIC_MODEL_REGISTER.md`).
   Do not modify formulas, default constants, or unit conventions without an
   explicit, reviewed scientific rationale. Never re-implement an equation
   that already exists in the domain layer — import it.
2. **Deduplication requires proof of equivalence.** Before removing any
   duplicate implementation, confirm the two implementations produce
   equivalent results (the golden baseline helps here) and document the
   equivalence.
3. **Layer boundaries are enforced by tests.** The architecture tests in
   `tests/test_architecture_dependencies.py` enforce:
   - Domain must not import Application/Presentation/GUI/Infrastructure or
     perform filesystem operations.
   - Application must not import Presentation/GUI/concrete Infrastructure or
     perform direct filesystem operations.
   - Infrastructure must not import PyQt6 or GUI modules.
   - Presentation plot-data helpers must consume explicit inputs.
   If your change fails these tests, the architecture is wrong, not the test —
   unless you have a reviewed reason to amend the boundary.
4. **Behavior-preserving refactors only, unless specified.** Keep public APIs
   backward compatible; legacy modules (`src/legacy/core`, `src/legacy/ui`, `src/legacy/ui/logic`,
   `seebeck_prime.plot`) are compatibility surfaces and must keep working.

## Regenerating the golden baseline

If a change deliberately alters scientific outputs (approved equation fix,
constant update), regenerate the snapshot and review the diff:

```bash
python scripts/generate_golden_baseline.py
git diff tests/golden/baseline_outputs.json
```

A baseline diff must be explainable item by item in the pull-request
description. The baseline is a characterization snapshot, not scientific
validation — do not cite it as evidence of correctness in publications.

## Testing expectations

- Every bug fix and behavior change needs a test that fails without the
  change.
- GUI-dependent code: prefer extracting logic into Qt-free modules so it can
  be tested headlessly.
- Known environment issue: on some Windows machines the PyQt6 `QtWidgets`
  DLL fails to load; GUI-dependent tests skip automatically in that case.
  Headless tests must still pass everywhere.

## Pull requests

- Describe what changed, why, and which tests cover it.
- Include the full pytest output (`python -m pytest -q`).
- Do not push to `main` directly; feature branches and pull requests are
  preferred.
