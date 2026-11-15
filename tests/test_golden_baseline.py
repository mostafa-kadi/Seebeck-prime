"""Stage 7 golden-output regression harness.

Recomputes every entry in ``tests/golden/baseline_outputs.json`` from the
current Domain/Application scientific code and compares against the committed
snapshot.

The baseline is a self-generated characterization snapshot (see
``scripts/generate_golden_baseline.py``). It detects unintended changes in
calculations during refactoring; it is NOT scientific validation of the
equations themselves.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[0]
GENERATOR = REPO_ROOT / "scripts" / "generate_golden_baseline.py"
BASELINE = TESTS_DIR / "golden" / "baseline_outputs.json"


def _load_builder():
    spec = importlib.util.spec_from_file_location(
        "generate_golden_baseline", GENERATOR
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_golden_baseline"] = module
    spec.loader.exec_module(module)
    return module


def _flatten(node, path=()):
    """Yield (path, leaf) pairs for numeric comparison."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _flatten(value, path + (key,))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _flatten(value, path + (index,))
    else:
        yield path, node


def _numeric(value):
    if value == "NaN":
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return value  # Non-numeric leaf (e.g. "p-type") compared directly


def _compare(actual, expected, path=()):
    if isinstance(actual, dict) and isinstance(expected, dict):
        assert set(actual) == set(expected), (
            f"Baseline structure changed at {'/'.join(map(str, path))}: "
            f"actual={sorted(actual)}, expected={sorted(expected)}"
        )
        for key in expected:
            _compare(actual[key], expected[key], path + (key,))
    elif isinstance(actual, list) and isinstance(expected, list):
        assert len(actual) == len(expected), (
            f"Baseline list length changed at {'/'.join(map(str, path))}: "
            f"{len(actual)} != {len(expected)}"
        )
        for index in range(len(expected)):
            _compare(actual[index], expected[index], path + (index,))
    else:
        location = "/".join(map(str, path))
        a = _numeric(actual)
        e = _numeric(expected)
        if isinstance(a, float) and isinstance(e, float):
            if math.isnan(a) or math.isnan(e):
                assert math.isnan(a) and math.isnan(e), f"NaN mismatch at {location}"
            else:
                assert a == pytest.approx(e, rel=1e-12, abs=1e-15), (
                    f"Golden output changed at {location}: {a!r} != {e!r}"
                )
        else:
            assert a == e, f"Golden output changed at {location}: {a!r} != {e!r}"


def test_golden_baseline_file_exists_and_matches_regenerated_outputs():
    builder = _load_builder()
    expected = json.loads(BASELINE.read_text(encoding="utf-8"))
    actual = builder.build_baseline()

    _compare(actual, expected)
