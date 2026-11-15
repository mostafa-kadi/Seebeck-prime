"""Independent reference calculations used to validate Seebeck Prime.

The implementations in :mod:`references` are written from the governing
equations and deliberately do **not** import any ``seebeck_prime``
calculation function; the test suite asserts this.
"""

from __future__ import annotations

from . import references  # noqa: F401

__all__ = ["references"]
