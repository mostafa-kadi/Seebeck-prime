"""Tests for plain-text (``.txt``/``.tsv``) import and export support."""

from __future__ import annotations

import pandas as pd
import pytest

from seebeck_prime.application.table_files import TableFileService
from seebeck_prime.infrastructure.io import PandasTabularDataStore


def _service():
    return TableFileService(PandasTabularDataStore())


def test_txt_export_is_tab_separated_with_a_header_and_no_index(tmp_path):
    path = tmp_path / "measurements.txt"
    data = pd.DataFrame({"Temperature": [300.0, 400.0], "Seebeck": [1e-4, 2e-4]})

    PandasTabularDataStore().write(data, path)

    text = path.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "Temperature\tSeebeck"
    assert "\t" in text.splitlines()[1]
    assert not text.startswith(",")


def test_txt_round_trip_preserves_values(tmp_path):
    path = tmp_path / "measurements.txt"
    expected = pd.DataFrame(
        {"temperature": [300.0, 400.0], "seebeck": [1e-4, 2e-4], "label": ["a", "b"]}
    )
    store = PandasTabularDataStore()

    TableFileService(store).save(expected, path)
    actual = TableFileService(store).load(path)

    pd.testing.assert_frame_equal(actual, expected, check_dtype=False)


@pytest.mark.parametrize(
    ("content", "separator"),
    [
        ("temperature,seebeck\n300.0,0.0001\n", ","),
        ("temperature\tseebeck\n300.0\t0.0001\n", "\t"),
        ("temperature;seebeck\n300.0;0.0001\n", ";"),
        ("temperature seebeck\n300.0 0.0001\n", " "),
    ],
)
def test_txt_read_detects_the_separator(tmp_path, content, separator):
    path = tmp_path / "instrument.txt"
    path.write_text(content, encoding="utf-8")

    frame = PandasTabularDataStore().read(path)

    assert list(frame.columns) == ["temperature", "seebeck"]
    assert frame["temperature"].tolist() == [300.0]
    assert frame["seebeck"].tolist() == pytest.approx([0.0001])


def test_txt_read_skips_comment_lines(tmp_path):
    path = tmp_path / "instrument.txt"
    path.write_text(
        "# Instrument export 2026-11-11\n"
        "temperature\tseebeck\n"
        "300.0\t0.0001\n",
        encoding="utf-8",
    )

    frame = PandasTabularDataStore().read(path)

    assert list(frame.columns) == ["temperature", "seebeck"]
    assert len(frame) == 1


def test_txt_files_are_not_routed_to_the_excel_reader(monkeypatch, tmp_path):
    path = tmp_path / "measurements.txt"
    path.write_text("temperature,seebeck\n300.0,0.0001\n", encoding="utf-8")

    def fail(*args, **kwargs):
        raise AssertionError("read_excel must not be used for .txt files")

    monkeypatch.setattr(pd, "read_excel", fail)
    monkeypatch.setattr(pd, "ExcelFile", fail)

    frame = PandasTabularDataStore().read(path)

    assert list(frame.columns) == ["temperature", "seebeck"]


def test_tsv_is_read_as_tab_separated(tmp_path):
    path = tmp_path / "measurements.tsv"
    path.write_text("temperature\tseebeck\n300.0\t0.0001\n", encoding="utf-8")

    frame = PandasTabularDataStore().read(path)

    assert frame["seebeck"].tolist() == pytest.approx([0.0001])


def test_multi_sample_service_loads_text_files_as_single_samples(tmp_path):
    first = tmp_path / "sample_a.txt"
    second = tmp_path / "sample_b.txt"
    first.write_text("temperature,seebeck\n300.0,0.0001\n", encoding="utf-8")
    second.write_text("temperature\tseebeck\n400.0\t0.0002\n", encoding="utf-8")

    events = list(_service().load_multi_sample_files([first, second]))
    samples = [event for event in events if not hasattr(event, "path")]

    assert [name for name, _ in samples] == ["sample_a.txt", "sample_b.txt"]
    assert samples[0][1]["temperature"].tolist() == [300.0]
    assert samples[1][1]["seebeck"].tolist() == pytest.approx([0.0002])


def test_multi_sample_service_reports_text_file_errors_per_file(tmp_path):
    bad = tmp_path / "broken.txt"
    bad.write_text("", encoding="utf-8")

    events = list(_service().load_multi_sample_files([bad]))

    assert len(events) == 1
    assert events[0].path == str(bad)


def test_file_dialog_filters_include_text_files():
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    commands = (repo_root / "src" / "gui" / "file_commands.py").read_text(
        encoding="utf-8"
    )
    dialog = (
        repo_root / "src" / "presentation" / "dialogs" / "multi_sample_dialog.py"
    ).read_text(encoding="utf-8")

    assert "*.txt" in commands
    assert "Text Files (*.txt" in commands
    assert "*.txt" in dialog
