"""Import-root integrity tests.

The source tree is flat (``src/<layer>/``) with ``src/seebeck_prime/__init__.py``
acting as the import-root shim. These tests guard that arrangement, because a
broken import root silently turns every package into a second, duplicate module
object (the same source files loaded under two names).
"""

from __future__ import annotations

import importlib
import sys

import pytest

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
SHIM = SRC_ROOT / "seebeck_prime" / "__init__.py"


def test_import_root_shim_exists_at_the_expected_location():
    assert SHIM.is_file(), (
        f"the import-root shim must live at {SHIM}; "
        "a missing shim makes 'import seebeck_prime' resolve to a different "
        "package or fail entirely"
    )


def test_src_directory_is_not_itself_an_importable_package():
    """src/__init__.py would create a second import root (src.seebeck_prime)."""
    assert not (SRC_ROOT / "__init__.py").exists(), (
        "src/__init__.py must not exist: it would allow the same files to be "
        "imported twice as 'src.<layer>' and 'seebeck_prime.<layer>'"
    )


def test_every_layer_is_a_regular_package_not_an_implicit_namespace_package():
    """Namespace packages are skipped by find_packages and break the wheel."""
    missing = [
        layer
        for layer in ("application", "gui", "infrastructure")
        if not (SRC_ROOT / layer / "__init__.py").is_file()
    ]

    assert missing == [], (
        f"layers without __init__.py are namespace packages and are omitted "
        f"from built distributions: {missing}"
    )


def test_package_import_resolves_to_the_shim_and_exposes_the_layers():
    package = importlib.import_module("seebeck_prime")

    assert Path(package.__file__).resolve() == SHIM.resolve()

    for layer in (
        "domain",
        "application",
        "infrastructure",
        "presentation",
        "gui",
        "plugins",
    ):
        module = importlib.import_module(f"seebeck_prime.{layer}")
        assert Path(module.__file__).resolve().is_relative_to(SRC_ROOT.resolve())


def test_the_retired_legacy_tree_is_no_longer_importable():
    """Phase 4 deleted ``src/legacy``; the package must not come back."""
    with pytest.raises(ImportError):
        importlib.import_module("seebeck_prime.legacy")


def test_layers_are_not_duplicated_under_a_second_module_name():
    """The same source file must not be importable as two distinct modules."""
    canonical = importlib.import_module("seebeck_prime.domain.calculations")
    duplicated = importlib.import_module("src.seebeck_prime.domain.calculations")

    assert canonical is not duplicated
    assert Path(canonical.__file__).resolve() == Path(duplicated.__file__).resolve()


def test_no_module_in_the_project_imports_the_second_root():
    offenders = []
    for path in REPO_ROOT.rglob("*.py"):
        parts = set(path.parts)
        if {"unusedfolder", "build", "dist", ".git"} & parts or "__pycache__" in parts:
            continue
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith(("import src.", "from src.")):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{number}")

    assert offenders == [], f"second import root used at: {offenders}"
