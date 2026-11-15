"""Ports used by application use cases to reach external data stores."""

from __future__ import annotations

from os import PathLike
from typing import Iterable, Protocol, Sequence

import pandas as pd


class TabularDataStore(Protocol):
    """Read and write tabular scientific data without prescribing storage."""

    def read(self, path: str | PathLike[str]) -> pd.DataFrame:
        """Load a table from a supported path."""

    def read_csv(self, path: str | PathLike[str]) -> pd.DataFrame:
        """Read a CSV using the established default pandas parsing behavior."""

    def read_workbook(
        self, path: str | PathLike[str]
    ) -> Iterable[tuple[str, pd.DataFrame]]:
        """Iterate sheets in stored order, preserving names and partial reads."""

    def write(self, data: pd.DataFrame, path: str | PathLike[str]) -> None:
        """Persist a table to a supported path."""

    def write_workbook(
        self, tables: Sequence[tuple[str, pd.DataFrame]], path: str | PathLike[str]
    ) -> None:
        """Persist named tables as worksheets in a workbook."""
