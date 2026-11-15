"""Application use cases for tabular data import and export."""

from __future__ import annotations

import os
from os import PathLike
from dataclasses import dataclass
from typing import Iterator, Sequence

import pandas as pd

from .ports import TabularDataStore


@dataclass(frozen=True)
class MultiSampleFileError:
    """A per-file read failure yielded in the same order as selected files."""

    path: str
    message: str


class TableFileService:
    """Coordinate table persistence through an injected storage port."""

    def __init__(self, store: TabularDataStore) -> None:
        self._store = store

    def load(self, path: str | PathLike[str]) -> pd.DataFrame:
        return self._store.read(path)

    def load_multi_sample_files(
        self, paths: Sequence[str | PathLike[str]]
    ) -> Iterator[tuple[str, pd.DataFrame] | MultiSampleFileError]:
        """Load files for Multi-Sample batch processing, continuing per file.

        XLSX sheets become independently named samples, in workbook order.
        CSV and delimited text files (``.txt``/``.tsv``) are loaded as a
        single sample each, using the store's format detection.
        Load results and errors are yielded in order so Presentation can
        retain the established per-file and per-sheet behavior.
        """
        for path in paths:
            file_path = str(path)
            try:
                base_name = os.path.basename(file_path)
                if file_path.lower().endswith(".xlsx"):
                    for sheet_name, frame in self._store.read_workbook(path):
                        yield (f"{base_name} [{sheet_name}]", frame)
                elif file_path.lower().endswith((".txt", ".tsv")):
                    yield (base_name, self._store.read(path))
                else:
                    yield (base_name, self._store.read_csv(path))
            except Exception as exc:
                yield MultiSampleFileError(file_path, str(exc))

    def save(self, data: pd.DataFrame, path: str | PathLike[str]) -> None:
        self._store.write(data, path)

    def save_workbook(
        self, tables: Sequence[tuple[str, pd.DataFrame]], path: str | PathLike[str]
    ) -> None:
        self._store.write_workbook(tables, path)
