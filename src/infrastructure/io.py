"""Pandas-backed CSV/Excel/text adapter for the application tabular-data port.

Supported formats (preserved from the established main-table workflow):
- CSV read/write (comma-separated; tab-separated fallback on comma-parse failure).
- Plain-text read/write (``.txt``): the delimiter is detected on read
  (comma, tab, semicolon, or arbitrary whitespace) and tab-separated on
  write, which is the convention used by Origin/Excel imports.
- Tab-separated text (``.tsv``).
- Excel read/write for spreadsheet extensions (``.xlsx`` via openpyxl; ``.xls``
  only when a pandas-supported legacy engine is installed).
- Named multi-sheet workbook export/import via ``write_workbook``/``read_workbook``.

Files with an unknown extension are treated as Excel workbooks.
"""

from __future__ import annotations

from os import PathLike
from typing import Iterable, Sequence

import pandas as pd

_TEXT_SUFFIXES = (".txt", ".tsv")
_TAB_SUFFIXES = (".tsv",)


def _read_delimited_text(file_path: str) -> pd.DataFrame:
    """Read a delimited plain-text file, detecting the separator.

    Tries, in order: delimiter sniffing (comma/tab/semicolon), whitespace
    separation, tab, then comma. Comment lines starting with ``#`` are
    ignored.
    """
    attempts = (
        {"sep": None, "engine": "python"},
        {"sep": r"\s+", "engine": "python"},
        {"sep": "\t"},
        {"sep": ","},
    )
    last_error: Exception | None = None
    for options in attempts:
        try:
            return pd.read_csv(file_path, comment="#", **options)
        except Exception as exc:  # try the next separator convention
            last_error = exc
    raise last_error if last_error else ValueError(f"Cannot parse text file: {file_path}")



class PandasTabularDataStore:
    """Infrastructure adapter for the application's tabular-data operations.

    CSV and Excel behavior matches the established main-table workflow. The
    adapter intentionally has no Qt dependency; file selection and user
    messaging belong to the presentation layer.
    """

    def read(self, path: str | PathLike[str]) -> pd.DataFrame:
        file_path = str(path)
        lowered = file_path.lower()
        if lowered.endswith(".csv"):
            try:
                return pd.read_csv(file_path)
            except Exception:
                return pd.read_csv(file_path, sep="\t")
        if lowered.endswith(_TAB_SUFFIXES):
            return pd.read_csv(file_path, sep="\t", comment="#")
        if lowered.endswith(_TEXT_SUFFIXES):
            return _read_delimited_text(file_path)
        return pd.read_excel(file_path)

    def read_csv(self, path: str | PathLike[str]) -> pd.DataFrame:
        return pd.read_csv(path)

    def read_workbook(
        self, path: str | PathLike[str]
    ) -> Iterable[tuple[str, pd.DataFrame]]:
        workbook = pd.ExcelFile(path)
        for sheet_name in workbook.sheet_names:
            yield sheet_name, pd.read_excel(path, sheet_name=sheet_name)

    def write(self, data: pd.DataFrame, path: str | PathLike[str]) -> None:
        file_path = str(path)
        lowered = file_path.lower()
        if lowered.endswith(".csv"):
            data.to_csv(file_path, index=False)
        elif lowered.endswith(_TEXT_SUFFIXES):
            data.to_csv(file_path, sep="\t", index=False)
        else:
            data.to_excel(file_path, index=False)

    def write_workbook(
        self, tables: Sequence[tuple[str, pd.DataFrame]], path: str | PathLike[str]
    ) -> None:
        with pd.ExcelWriter(path) as writer:
            for sheet_name, data in tables:
                data.to_excel(writer, sheet_name=sheet_name, index=False)
