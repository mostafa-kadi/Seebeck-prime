"""Prepare main-table columns for presentation plots without Qt dependencies.

The helper consumes explicit inputs: a pandas DataFrame and an error-bar flag.
Main-window-like objects are still accepted for backward compatibility, but the
canonical call passes data and configuration explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from seebeck_prime.application.table_schema import (
    COL_TEMP,
    COL_EC,
    COL_SEEBECK,
    COL_PF,
    COL_K_TOTAL,
    COL_K_E,
    COL_K_L,
    COL_ZT,
)

_COL_MAP = {
    COL_TEMP: ("Temperature", None),
    COL_EC: ("Electrical Conductivity", "±σ"),
    COL_SEEBECK: ("Seebeck Coeff.", "±S"),
    COL_PF: ("Power Factor", "±PF"),
    COL_K_TOTAL: ("Thermal Cond.", "±κ"),
    COL_K_E: ("Electronic TC", "±κₑ"),
    COL_K_L: ("Lattice TC", "±κₗ"),
    COL_ZT: ("ZT", "±ZT"),
}


@dataclass(frozen=True)
class PlotDataContext:
    """Explicit inputs for main-table plotting.

    ``frame`` holds base-unit data; ``error_mode`` selects uncertainty columns;
    ``header_label`` maps a column index to its displayed header text.
    """

    frame: pd.DataFrame
    error_mode: bool
    header_label: Callable[[int], str]


def get_table_data(frame: pd.DataFrame, y_col_index: int, error_mode: bool = False):
    """Return aligned, x-sorted plot arrays with the legacy missing-data rules.

    Backward compatibility: if ``frame`` exposes ``.data`` and ``.error_mode``
    (a main-window-like object), it is unwrapped to the established behavior.
    """
    if hasattr(frame, "data") and hasattr(frame, "error_mode"):
        error_mode = frame.error_mode
        frame = frame.data

    x_col = _COL_MAP[COL_TEMP][0]
    y_col, y_uncertainty_col = _COL_MAP[y_col_index]

    if x_col not in frame.columns or y_col not in frame.columns:
        return None, None, None, None

    x_raw = frame[x_col]
    y_raw = frame[y_col]
    x_error_raw = pd.Series([0.0] * len(frame))
    y_error_raw = (
        frame[y_uncertainty_col]
        if error_mode and y_uncertainty_col and y_uncertainty_col in frame.columns
        else pd.Series([0.0] * len(frame))
    )

    combined = pd.DataFrame(
        {"x": x_raw, "y": y_raw, "x_err": x_error_raw, "y_err": y_error_raw}
    ).dropna(subset=["x", "y"])
    if combined.empty:
        return None, None, None, None

    combined = combined.sort_values(by="x")
    return (
        combined["x"].tolist(),
        combined["y"].tolist(),
        combined["x_err"].tolist(),
        combined["y_err"].tolist(),
    )
