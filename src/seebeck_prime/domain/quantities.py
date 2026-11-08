"""
Scientific quantities: typed data classes for thermoelectric properties.

These classes carry a value, unit string, and optional uncertainty.
They are intentionally lightweight (no GUI, no IO).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScalarQuantity:
    """
    A single measured or calculated scalar quantity.

    Attributes:
        value: Numeric value.
        unit: Unit string (e.g. ``"K"``, ``"S/m"``, ``"µV/K"``).
        uncertainty: Absolute uncertainty u(value) in the same unit. ``None`` if unknown.
        label: Human-readable name for display (e.g. ``"Seebeck Coefficient"``).
        origin: Data origin tag (e.g. ``"measured"``, ``"calculated"``, ``"imported"``).
    """
    value: float
    unit: str
    uncertainty: Optional[float] = None
    label: str = ""
    origin: str = "measured"

    def __repr__(self) -> str:  # pragma: no cover
        unc = f" ± {self.uncertainty}" if self.uncertainty is not None else ""
        return f"{self.label or 'Quantity'}({self.value}{unc} {self.unit})"


# ─── Origin Tags ──────────────────────────────────────────────────────────────

class DataOrigin:
    """Canonical data-origin tag strings."""
    MEASURED = "measured"
    CALCULATED = "calculated"
    IMPORTED = "imported"
    INTERPOLATED = "interpolated"
    EXTRAPOLATED = "extrapolated"
    ESTIMATED = "estimated"
    FITTED = "fitted"
