"""Normalize externally supplied column labels into application contracts."""

from __future__ import annotations

import re

import pandas as pd


def _alias_is_plausible(alias: str, src_col: str) -> bool:
    """Reject matches between physically different quantities.

    Guards (audit issues SE-031 / SE-032):

    * ``"conductivity"`` must not capture a *thermal* conductivity column
      ("Thermal Conductivity (W/mK)"), which would otherwise feed kappa
      values into the electrical-conductivity slot and leave the
      thermal-conductivity target unmapped.
    * ``"k"`` must not capture a temperature column ("T (K)").
    * ``"s"`` must not capture an S/cm conductivity column.
    """
    if alias == "conductivity" and (
        "thermal" in src_col or "kappa" in src_col or "\u03ba" in src_col
    ):
        return False
    if alias == "k" and ("temp" in src_col or src_col.endswith("(k)")):
        return False
    if alias == "s" and (
        re.search(r"s/[mc]", src_col) or "conductivity" in src_col
    ):
        return False
    return True


def find_column_index(source_columns, aliases, used_indices=None) -> int | None:
    """Return the index of the first source column matching any alias.

    Matching rules (shared by every import path so that they cannot diverge):

    * source column names are lower-cased and stripped;
    * aliases are lower-cased as well, so "uV/K" matches "Seebeck (uV/K)";
    * longer aliases are tried first (longest, most specific match wins);
    * aliases of three characters or more match as a substring, shorter ones
      match on word boundaries;
    * physically implausible matches are rejected (see
      :func:`_alias_is_plausible`).
    """
    normalized = [str(column).lower().strip() for column in source_columns]
    used = used_indices if used_indices is not None else set()

    for alias in sorted(aliases, key=len, reverse=True):
        alias = str(alias).lower()
        for index, src_col in enumerate(normalized):
            if index in used:
                continue
            if len(alias) > 2:
                matched = alias in src_col
            else:
                matched = bool(re.search(rf"\b{re.escape(alias)}\b", src_col))
            if matched and _alias_is_plausible(alias, src_col):
                return index
    return None


def get_robust_mapped_dataframe(source_df: pd.DataFrame, search_groups):
    """Map source columns to requested targets using the legacy alias rules.

    Alias ordering, whole-word handling for short aliases, and special cases
    are intentionally preserved for compatibility with existing imports.
    """
    mapped_df = pd.DataFrame()
    used_indices = set()

    for target, aliases in search_groups:
        index = find_column_index(source_df.columns, aliases, used_indices)
        if index is None:
            continue
        mapped_df[target] = source_df.iloc[:, index]
        used_indices.add(index)
    return mapped_df
