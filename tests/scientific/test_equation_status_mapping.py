"""Guard for the equation-status mapping (Phase 2).

The mapping ``validation/remediation/EQUATION_STATUS_MAPPING.csv`` is the
explicit bridge between the equation registry (E-01..E-62) and the
per-calculation validation status.  This module makes the bridge
*checkable* rather than a narrative claim:

* the mapping covers exactly the registry's E-01..E-62 - no gaps, no extras;
* every implementation path and every test path it names exists on disk;
* every independent-reference function it names exists in the reference
  module and that module still does not import the application;
* the category counts it implies match the counts published in
  ``validation/remediation/VALIDATION_STATUS.md``;
* the three status axes are populated consistently with the category, so a
  row cannot claim a category its own fields contradict.
"""

from __future__ import annotations

import csv
import pathlib
import re
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REMEDIATION = REPO_ROOT / "validation" / "remediation"
MAPPING_CSV = REMEDIATION / "EQUATION_STATUS_MAPPING.csv"
STATUS_MD = REMEDIATION / "VALIDATION_STATUS.md"
REGISTRY_MD = REPO_ROOT / "validation" / "SCIENTIFIC_EQUATION_REGISTRY.md"

CATEGORIES = (
    "1 - Numerically verified",
    "2 - Numerically verified but physically conditional",
    "3 - Experimentally benchmarked within a defined scope",
    "4 - Not yet validated",
)


def _load_rows() -> list[dict[str, str]]:
    assert MAPPING_CSV.is_file(), f"missing mapping file: {MAPPING_CSV}"
    with MAPPING_CSV.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


ROWS = _load_rows()


# =====================================================================
# Coverage
# =====================================================================

def test_mapping_covers_exactly_the_registry_equations():
    ids = [row["equation_id"] for row in ROWS]
    expected = [f"E-{i:02d}" for i in range(1, 63)]

    assert len(ids) == len(set(ids)), "duplicate equation ids in the mapping"
    assert ids == expected, (
        "the mapping must cover E-01..E-62 in order; "
        f"missing={sorted(set(expected) - set(ids))} "
        f"extra={sorted(set(ids) - set(expected))}"
    )


def test_mapping_ids_match_the_equation_registry():
    """The registry and the mapping must describe the same set of equations."""
    text = REGISTRY_MD.read_text(encoding="utf-8")
    registry_ids = {
        f"E-{int(m):02d}"
        for m in re.findall(r"\bE-(\d{2})\b", text)
        if int(m) >= 1
    }
    mapping_ids = {row["equation_id"] for row in ROWS}

    assert registry_ids == mapping_ids, (
        f"registry-only: {sorted(registry_ids - mapping_ids)}; "
        f"mapping-only: {sorted(mapping_ids - registry_ids)}"
    )


def test_every_row_has_the_required_fields():
    required = [
        "equation_id", "equation_name", "implementation_file",
        "implementation_function", "test_files", "independent_reference",
        "numerical_validation_status", "physical_applicability_status",
        "experimental_validation_status", "validation_category",
        "remaining_limitation",
    ]
    for row in ROWS:
        for field in required:
            assert row.get(field, "").strip(), (
                f"{row['equation_id']}: field '{field}' is empty"
            )
        assert row["validation_category"] in CATEGORIES, (
            f"{row['equation_id']}: unknown category {row['validation_category']!r}"
        )


# =====================================================================
# The paths and symbols the mapping names must exist
# =====================================================================

def _split_paths(value: str) -> list[str]:
    out = []
    for chunk in value.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        # a path may carry a trailing "(N alias modules)" note
        chunk = re.sub(r"\s*\(.*\)\s*$", "", chunk).strip()
        if not chunk or chunk.startswith("("):
            continue
        out.append(chunk)
    return out


def test_every_named_implementation_path_exists():
    missing = []
    for row in ROWS:
        for path in _split_paths(row["implementation_file"]):
            if not (REPO_ROOT / path).exists():
                missing.append((row["equation_id"], path))
    assert not missing, f"implementation paths that do not exist: {missing}"


def test_every_named_test_path_exists():
    missing = []
    for row in ROWS:
        for path in _split_paths(row["test_files"]):
            if not (REPO_ROOT / path).exists():
                missing.append((row["equation_id"], path))
    assert not missing, f"test paths that do not exist: {missing}"


def test_every_named_independent_reference_function_exists():
    """A named reference must exist in the reference module."""
    from validation.independent_calculations import references as ref

    missing = []
    for row in ROWS:
        for name in re.findall(r"references\.([A-Za-z_][A-Za-z0-9_]*)",
                               row["independent_reference"]):
            if not hasattr(ref, name):
                missing.append((row["equation_id"], name))
    assert not missing, f"independent-reference functions that do not exist: {missing}"


def test_the_reference_module_still_does_not_import_the_application():
    """The mapping's 'independent reference' column is only meaningful while
    the reference module stays independent of the application.

    The check is an AST inspection, not a substring search: the module's
    docstring legitimately *mentions* ``seebeck_prime`` when it explains that
    it must not import it.
    """
    import ast

    from validation.independent_calculations import references as ref

    tree = ast.parse(pathlib.Path(ref.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                imported.add(node.module.split(".")[0])

    offenders = sorted(
        name for name in imported
        if name == "seebeck_prime" or name.startswith("seebeck_prime.")
    )
    assert not offenders, (
        f"the independent reference module must not import the application: "
        f"{offenders}"
    )


# =====================================================================
# Category consistency
# =====================================================================

def test_status_axes_agree_with_the_category():
    """No row may claim a category its own status fields contradict."""
    for row in ROWS:
        eid = row["equation_id"]
        category = row["validation_category"]
        numerical = row["numerical_validation_status"].upper()
        physical = row["physical_applicability_status"].upper()
        experimental = row["experimental_validation_status"].upper()

        if category.startswith("1"):
            assert numerical.startswith("VERIFIED"), (
                f"{eid}: category 1 requires a VERIFIED numerical status"
            )
            # NOTE: "UNCONDITIONAL" contains "CONDITIONAL" as a substring, so
            # the test must look at the leading token, not at containment.
            assert physical.startswith("UNCONDITIONAL"), (
                f"{eid}: category 1 requires an unconditional physical status, "
                f"got {row['physical_applicability_status']!r}"
            )
        elif category.startswith("2"):
            assert numerical.startswith("VERIFIED"), (
                f"{eid}: category 2 requires a VERIFIED numerical status"
            )
            assert (
                physical.startswith("CONDITIONAL")
                or physical.startswith("SCOPE-LIMITED")
            ), (
                f"{eid}: category 2 requires a conditional or scope-limited "
                f"physical status, got {row['physical_applicability_status']!r}"
            )
        elif category.startswith("3"):
            assert numerical.startswith("VERIFIED"), (
                f"{eid}: category 3 requires a VERIFIED numerical status"
            )
            assert "BENCHMARKED" in experimental, (
                f"{eid}: category 3 requires an experimental benchmark"
            )
        else:                                   # category 4
            assert numerical.startswith("NOT"), (
                f"{eid}: category 4 requires a NOT-VERIFIED / NOT-IMPLEMENTED "
                "numerical status"
            )


def test_no_row_claims_the_term_fully_validated():
    """The brief forbids 'fully validated' for calculations whose physical
    applicability or experimental accuracy remains unverified."""
    for row in ROWS:
        blob = " ".join(row.values()).lower()
        assert "fully validated" not in blob, row["equation_id"]
        assert "completely validated" not in blob, row["equation_id"]


# =====================================================================
# The published status document must agree with the mapping
# =====================================================================

def test_validation_status_document_exists_and_lists_every_equation():
    assert STATUS_MD.is_file(), f"missing {STATUS_MD}"
    text = STATUS_MD.read_text(encoding="utf-8")
    for row in ROWS:
        assert row["equation_id"] in text, (
            f"VALIDATION_STATUS.md does not mention {row['equation_id']}"
        )


def test_validation_status_document_publishes_the_matching_counts():
    """The counts in VALIDATION_STATUS.md must equal the mapping's counts."""
    assert STATUS_MD.is_file(), f"missing {STATUS_MD}"
    text = STATUS_MD.read_text(encoding="utf-8")

    actual: dict[str, int] = {}
    for row in ROWS:
        actual[row["validation_category"]] = actual.get(row["validation_category"], 0) + 1

    for category in CATEGORIES:
        count = actual.get(category, 0)
        assert re.search(rf"\|\s*{re.escape(category)}\s*\|\s*\*?\*?{count}\*?\*?\s*\|", text), (
            f"VALIDATION_STATUS.md must report {count} entries for "
            f"'{category}'"
        )

    total = sum(actual.values())
    assert total == 62
    assert re.search(rf"\b{total}\b", text), (
        f"VALIDATION_STATUS.md must state the total ({total})"
    )


@pytest.mark.parametrize("category", CATEGORIES)
def test_the_mapping_is_reproducible_from_the_generator(category):
    """``tools/generate_equation_status_mapping.py`` must reproduce the
    committed CSV byte-for-byte, so the mapping cannot silently drift."""
    import subprocess

    generator = REPO_ROOT / "tools" / "generate_equation_status_mapping.py"
    assert generator.is_file(), f"missing generator {generator}"

    before = MAPPING_CSV.read_bytes()
    result = subprocess.run(
        [sys.executable, str(generator)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    after = MAPPING_CSV.read_bytes()

    assert before == after, (
        "the committed mapping does not match the generator output; "
        "re-run tools/generate_equation_status_mapping.py"
    )
