"""
Seebeck Prime — Open-source platform for experimental
thermoelectric-material transport analysis and materials optimization.

Version: 0.1.0

The implementation lives in the sibling directories of this package
(``src/domain``, ``src/application``, ``src/presentation``, ``src/gui``,
``src/infrastructure``, ``src/plugins``) so the repository
keeps a single, flat source direction. This module extends the package search
path to that parent directory, so the public import path is unchanged::

    from seebeck_prime.domain.calculations import calculate_pf

When the project is installed as a wheel, the packages are laid out normally
inside ``site-packages/seebeck_prime/`` and the extension below is a no-op.
"""

import os

__version__ = "0.1.0"
__author__ = "Mostafa M. Elkady"
__license__ = "MIT"

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.dirname(_PACKAGE_DIR)

# Source checkout: the layer packages are siblings of this package directory.
if os.path.isdir(os.path.join(_SOURCE_DIR, "domain")) and _SOURCE_DIR not in __path__:
    __path__.append(_SOURCE_DIR)
