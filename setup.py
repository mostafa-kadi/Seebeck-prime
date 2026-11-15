"""Packaging configuration for Seebeck Prime.

The source tree is flat: the implementation packages live in ``src/`` as
siblings (``src/domain``, ``src/application``, ``src/presentation``,
``src/gui``, ``src/infrastructure``, ``src/plugins``), and
``src/seebeck_prime/__init__.py`` is the import-root shim.

To publish a conventional wheel (where everything sits inside the
``seebeck_prime`` package directory), each package is mapped explicitly to its
own source directory instead of relying on ``find_packages(where="src")``,
which would otherwise install the layers as top-level packages.
"""

import os

from setuptools import setup

HERE = os.path.abspath(os.path.dirname(__file__))
SRC_DIR = os.path.join(HERE, "src")
PACKAGE_NAME = "seebeck_prime"


def _discover_flat_packages():
    """Return (packages, package_dir) for the flat source layout."""
    packages = []
    package_dir = {}

    for entry in sorted(os.listdir(SRC_DIR)):
        directory = os.path.join(SRC_DIR, entry)
        if not os.path.isdir(directory):
            continue
        if entry == PACKAGE_NAME:
            # The import-root shim (src/seebeck_prime/__init__.py).
            package_dir[PACKAGE_NAME] = os.path.join("src", PACKAGE_NAME)
            packages.append(PACKAGE_NAME)
            continue
        if not os.path.isfile(os.path.join(directory, "__init__.py")):
            continue

        # Walk nested packages (e.g. presentation.dialogs).
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            if "__init__.py" not in files:
                continue
            relative = os.path.relpath(root, SRC_DIR).replace(os.sep, ".")
            packages.append(f"{PACKAGE_NAME}.{relative}")
            package_dir[f"{PACKAGE_NAME}.{relative}"] = os.path.join(
                "src", *relative.split(".")
            )

    return packages, package_dir


PACKAGES, PACKAGE_DIR = _discover_flat_packages()

setup(
    name="seebeck-prime",
    version="0.1.0",
    license="MIT",
    packages=PACKAGES,
    package_dir=PACKAGE_DIR,
    # NOTE (release, D-04/D-03): the author list is pending final confirmation
    # for the SoftwareX submission, so author/author_email are deliberately
    # omitted here rather than filled with placeholder contact details.
    # Author identity is declared in src/seebeck_prime/__init__.py and the
    # CITATION.cff (see RELEASE_READINESS.md).
    description="Open-source desktop application and headless Python API for "
    "experimental thermoelectric transport-property analysis.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mostafa-kadi/Seebeck-prime",
    project_urls={
        "Documentation": "https://github.com/mostafa-kadi/Seebeck-prime#readme",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    # Verified supported versions per docs/SUPPORTED_PYTHON.md (3.12/3.13 are
    # the CI targets); 3.9 was a stale claim from the original template.
    python_requires=">=3.12",
    # Runtime dependency closure measured from the actual imports:
    # qtawesome/scienceplots are hard imports of the GUI/plot modules,
    # openpyxl is the Excel engine used by infrastructure/io.py. pytz was
    # removed (nothing in src/ imports it; pandas manages its own deps).
    install_requires=[
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "pyqt6",
        "scienceplots",
        "openpyxl",
        "qtawesome",
    ],
    extras_require={"dev": ["pytest", "pytest-cov", "black", "ruff", "mypy"]},
)
