"""
General numerical / data analysis utilities.

This module contains:
- Regression (linear regression on raw or log-log data)
- Interpolation helpers
- MAD-based outlier filtering
- Temperature alignment across datasets

All functions are pure (no GUI, no IO, no pandas dependency).
"""

from __future__ import annotations

import numpy as np
from typing import Optional


# ─── Outlier Filtering ────────────────────────────────────────────────────────

def mad_filter(x: np.ndarray, thresh: float = 3.0) -> np.ndarray:
    """
    Remove outliers using the Median Absolute Deviation (MAD) criterion.

    A point x_i is kept if:
        |x_i − median(x)| < thresh × MAD

    Args:
        x: 1-D array of values.
        thresh: Rejection threshold in units of MAD (default 3.0).

    Returns:
        Filtered array with outliers removed.
    """
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return x
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    if mad == 0:
        return x
    return x[np.abs(x - med) < thresh * mad]


# ─── Linear Regression ────────────────────────────────────────────────────────

def linear_regression(x: np.ndarray, y: np.ndarray) -> dict:
    """
    Ordinary least-squares linear regression y = m*x + b.

    Args:
        x: Independent variable array (1-D, finite).
        y: Dependent variable array (1-D, same length as x).

    Returns:
        Dict with keys:
            slope, intercept, r_squared, stderr (standard error of slope),
            n (number of points used).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 2:
        return dict(slope=np.nan, intercept=np.nan, r_squared=np.nan, stderr=np.nan, n=n)

    from scipy.stats import linregress
    res = linregress(x, y)
    return dict(
        slope=float(res.slope),
        intercept=float(res.intercept),
        r_squared=float(res.rvalue ** 2),
        stderr=float(res.stderr),
        n=n,
    )


# ─── Interpolation ────────────────────────────────────────────────────────────

def interpolate_onto(
    source_x: np.ndarray,
    source_y: np.ndarray,
    target_x: np.ndarray,
) -> np.ndarray:
    """
    Linear interpolation of (source_x, source_y) evaluated at target_x.

    Args:
        source_x: Source x-coordinates (1-D, monotonically sorted recommended).
        source_y: Source y-values (1-D, same length as source_x).
        target_x: Target x-coordinates at which to interpolate.

    Returns:
        Interpolated y-values at each target_x point.
    """
    sx = np.asarray(source_x, dtype=float)
    sy = np.asarray(source_y, dtype=float)
    tx = np.asarray(target_x, dtype=float)
    sort_idx = np.argsort(sx)
    return np.interp(tx, sx[sort_idx], sy[sort_idx])


# ─── Temperature Grouping / Alignment ────────────────────────────────────────

def round_temperature(T: np.ndarray, step: float = 20.0) -> np.ndarray:
    """
    Round temperature values to the nearest multiple of step for grouping.

    Args:
        T: Temperature array [K].
        step: Rounding step in K (default 20 K).

    Returns:
        Rounded array.
    """
    return (np.asarray(T, dtype=float) / step).round() * step


def align_datasets(
    T_ref: np.ndarray,
    T_other: np.ndarray,
    y_other: np.ndarray,
) -> np.ndarray:
    """
    Interpolate (T_other, y_other) onto the reference temperature grid T_ref.

    Args:
        T_ref: Reference temperature grid [K].
        T_other: Temperature grid of the other dataset [K].
        y_other: Values of the other dataset at T_other.

    Returns:
        y_other interpolated at T_ref.
    """
    return interpolate_onto(T_other, y_other, T_ref)
