"""Backward-compatible import surface for thermal transport calculations.

The authoritative implementations live in ``seebeck_prime.domain.calculations``.
This module re-exports them to preserve the historical import path.
"""

from seebeck_prime.domain.calculations import calculate_kappa_e, calculate_kappa_l

__all__ = ["calculate_kappa_e", "calculate_kappa_l"]
