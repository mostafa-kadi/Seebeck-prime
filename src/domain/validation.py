"""
Scientific data validation for thermoelectric datasets.

All validation functions are pure (no GUI, no IO).
They return lists of ValidationMessage objects so the caller
can decide how to display warnings/errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import numpy as np


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationMessage:
    severity: Severity
    field: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.field}: {self.message}"


def validate_temperature_array(T: np.ndarray) -> List[ValidationMessage]:
    """Check temperature array for physical validity."""
    msgs: List[ValidationMessage] = []
    T = np.asarray(T, dtype=float)
    if len(T) == 0:
        msgs.append(ValidationMessage(Severity.ERROR, "T", "Temperature array is empty."))
        return msgs
    if np.any(T <= 0):
        msgs.append(ValidationMessage(Severity.ERROR, "T", "Temperature must be positive (K). Found T ≤ 0."))
    if np.any(T < 1.0):
        msgs.append(ValidationMessage(Severity.WARNING, "T", "Very low temperature (< 1 K). Verify units."))
    if np.any(T > 5000.0):
        msgs.append(ValidationMessage(Severity.WARNING, "T", "Very high temperature (> 5000 K). Verify units."))
    # Duplicate temperatures
    unique_T, counts = np.unique(np.round(T, 1), return_counts=True)
    dups = unique_T[counts > 1]
    if len(dups) > 0:
        msgs.append(ValidationMessage(Severity.WARNING, "T", f"Duplicate temperature points detected: {dups[:5]}"))
    return msgs


def validate_conductivity_array(sigma: np.ndarray) -> List[ValidationMessage]:
    """Check electrical conductivity array."""
    msgs: List[ValidationMessage] = []
    sigma = np.asarray(sigma, dtype=float)
    if len(sigma) == 0:
        return msgs
    if np.any(sigma < 0):
        msgs.append(ValidationMessage(Severity.ERROR, "sigma", "Electrical conductivity must be ≥ 0."))
    if np.any(sigma > 1e8):
        msgs.append(ValidationMessage(Severity.WARNING, "sigma", "Very high conductivity (> 10⁸ S/m). Verify units."))
    return msgs


def validate_seebeck_array(S: np.ndarray) -> List[ValidationMessage]:
    """Check Seebeck coefficient array (in V/K)."""
    msgs: List[ValidationMessage] = []
    S = np.asarray(S, dtype=float)
    if len(S) == 0:
        return msgs
    S_uvk = np.abs(S) * 1e6
    if np.any(S_uvk > 2000.0):
        msgs.append(ValidationMessage(Severity.WARNING, "S", "Seebeck |S| > 2000 µV/K is unusual. Verify units (expected V/K in SI base)."))
    return msgs


def validate_kappa_array(kappa: np.ndarray) -> List[ValidationMessage]:
    """Check thermal conductivity array."""
    msgs: List[ValidationMessage] = []
    kappa = np.asarray(kappa, dtype=float)
    if len(kappa) == 0:
        return msgs
    if np.any(kappa < 0):
        msgs.append(ValidationMessage(Severity.ERROR, "kappa", "Total thermal conductivity must be ≥ 0."))
    return msgs


def validate_kappa_l_array(kappa_L: np.ndarray) -> List[ValidationMessage]:
    """Check lattice thermal conductivity for non-physical negative values."""
    msgs: List[ValidationMessage] = []
    kappa_L = np.asarray(kappa_L, dtype=float)
    if len(kappa_L) == 0:
        return msgs
    if np.any(kappa_L < 0):
        msgs.append(ValidationMessage(
            Severity.WARNING, "kappa_L",
            "Lattice thermal conductivity κL < 0. This may indicate a wrong Lorenz number or unit error."
        ))
    return msgs


def validate_dataset(T, sigma=None, S=None, kappa=None, kappa_L=None) -> List[ValidationMessage]:
    """Run all applicable validators and return combined message list."""
    msgs: List[ValidationMessage] = []
    msgs.extend(validate_temperature_array(np.asarray(T, dtype=float)))
    if sigma is not None:
        msgs.extend(validate_conductivity_array(np.asarray(sigma, dtype=float)))
    if S is not None:
        msgs.extend(validate_seebeck_array(np.asarray(S, dtype=float)))
    if kappa is not None:
        msgs.extend(validate_kappa_array(np.asarray(kappa, dtype=float)))
    if kappa_L is not None:
        msgs.extend(validate_kappa_l_array(np.asarray(kappa_L, dtype=float)))
    return msgs
