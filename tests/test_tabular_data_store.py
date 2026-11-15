import pandas as pd
import pytest

from seebeck_prime.application.table_files import TableFileService
from seebeck_prime.application.table_files import MultiSampleFileError
from seebeck_prime.application.services import ThermoelectricAnalyzer
from seebeck_prime.infrastructure.io import PandasTabularDataStore


def test_csv_store_round_trip(tmp_path):
    path = tmp_path / "measurements.csv"
    expected = pd.DataFrame({"temperature": [300.0, 400.0], "seebeck": [1e-4, 2e-4]})
    store = PandasTabularDataStore()

    TableFileService(store).save(expected, path)
    actual = TableFileService(store).load(path)

    pd.testing.assert_frame_equal(actual, expected)


def test_store_uses_excel_reader_for_xlsx(monkeypatch, tmp_path):
    expected = pd.DataFrame({"temperature": [300.0]})
    seen = {}

    def fake_read_excel(path):
        seen["path"] = path
        return expected

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)
    result = PandasTabularDataStore().read(tmp_path / "measurements.xlsx")

    assert result is expected
    assert seen["path"].endswith("measurements.xlsx")


def test_store_writes_excel_for_non_csv_path(monkeypatch, tmp_path):
    data = pd.DataFrame({"temperature": [300.0]})
    seen = {}

    def fake_to_excel(frame, path, index):
        seen.update(path=path, index=index, frame=frame)

    monkeypatch.setattr(pd.DataFrame, "to_excel", fake_to_excel)
    PandasTabularDataStore().write(data, tmp_path / "measurements.xlsx")

    assert seen["path"].endswith("measurements.xlsx")
    assert seen["index"] is False
    assert seen["frame"] is data


def test_workbook_export_preserves_named_table_sequence(monkeypatch, tmp_path):
    frame = pd.DataFrame({"X": [1], "Y": [2]})
    seen = {"sheets": []}

    class Writer:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_excel_writer(path):
        seen["path"] = path
        return Writer()

    def fake_to_excel(data, writer, sheet_name, index):
        seen["sheets"].append((sheet_name, data, index))

    monkeypatch.setattr(pd, "ExcelWriter", fake_excel_writer)
    monkeypatch.setattr(pd.DataFrame, "to_excel", fake_to_excel)
    PandasTabularDataStore().write_workbook(
        [("Plot", frame), ("Plot", frame)], tmp_path / "plots.xlsx"
    )

    assert str(seen["path"]).endswith("plots.xlsx")
    assert [sheet[0] for sheet in seen["sheets"]] == ["Plot", "Plot"]
    assert all(sheet[1] is frame and sheet[2] is False for sheet in seen["sheets"])


class InMemoryTableStore:
    def __init__(self):
        self.data = None
        self.path = None

    def read(self, path):
        self.path = path
        return self.data

    def write(self, data, path):
        self.data = data
        self.path = path

    def write_workbook(self, tables, path):
        self.tables = tables
        self.path = path


def test_application_file_service_uses_injected_store(tmp_path):
    store = InMemoryTableStore()
    service = TableFileService(store)
    frame = pd.DataFrame({"temperature": [300.0]})
    path = tmp_path / "data.csv"

    service.save(frame, path)
    loaded = service.load(path)

    assert loaded is frame
    assert store.path == path


def test_application_file_service_delegates_workbook_exports(tmp_path):
    store = InMemoryTableStore()
    service = TableFileService(store)
    tables = [("Processed", pd.DataFrame({"value": [1.0]}))]
    path = tmp_path / "processed.xlsx"

    service.save_workbook(tables, path)

    assert store.tables is tables
    assert store.path == path


def test_multi_sample_file_service_loads_csv_and_each_workbook_sheet(tmp_path):
    csv_path = tmp_path / "sample.csv"
    workbook_path = tmp_path / "runs.xlsx"
    pd.DataFrame({"value": [1]}).to_csv(csv_path, index=False)
    with pd.ExcelWriter(workbook_path) as writer:
        pd.DataFrame({"value": [2]}).to_excel(writer, sheet_name="Run 1", index=False)
        pd.DataFrame({"value": [3]}).to_excel(writer, sheet_name="Run 2", index=False)

    events = list(
        TableFileService(PandasTabularDataStore()).load_multi_sample_files(
            [csv_path, workbook_path]
        )
    )
    samples = [event for event in events if not isinstance(event, MultiSampleFileError)]

    assert [name for name, _ in samples] == [
        "sample.csv",
        "runs.xlsx [Run 1]",
        "runs.xlsx [Run 2]",
    ]
    assert [frame.iloc[0, 0] for _, frame in samples] == [1, 2, 3]
    assert len(events) == 3


def test_multi_sample_file_service_continues_after_a_file_error(tmp_path):
    class PartiallyFailingStore(InMemoryTableStore):
        def read_csv(self, path):
            if str(path).endswith("bad.csv"):
                raise ValueError("bad input")
            return pd.DataFrame({"value": [1]})

        def read_workbook(self, path):
            return []

    good = tmp_path / "good.csv"
    bad = tmp_path / "bad.csv"
    events = list(
        TableFileService(PartiallyFailingStore()).load_multi_sample_files([good, bad])
    )

    assert events[0][0] == "good.csv"
    assert events[1] == MultiSampleFileError(str(bad), "bad input")


def test_multi_sample_file_service_keeps_prior_sheets_if_a_later_sheet_fails(
    tmp_path,
):
    class PartiallyFailingWorkbookStore(InMemoryTableStore):
        def read_csv(self, path):
            return pd.DataFrame()

        def read_workbook(self, path):
            yield "Good Sheet", pd.DataFrame({"value": [1]})
            raise ValueError("second sheet unreadable")

    path = tmp_path / "partial.xlsx"
    events = list(
        TableFileService(PartiallyFailingWorkbookStore()).load_multi_sample_files(
            [path]
        )
    )

    assert events[0][0] == "partial.xlsx [Good Sheet]"
    assert events[1] == MultiSampleFileError(str(path), "second sheet unreadable")


def test_measurement_analyzer_reads_paths_through_injected_store(tmp_path):
    store = InMemoryTableStore()
    store.data = pd.DataFrame({"temperature": [300.0]})

    analyzer = ThermoelectricAnalyzer(
        four_probe_file=tmp_path / "four_probe.csv",
        data_store=store,
    )

    assert analyzer.fp_raw is store.data
    assert store.path == tmp_path / "four_probe.csv"


def test_measurement_analyzer_requires_a_store_for_file_paths(tmp_path):
    with pytest.raises(ValueError, match="TabularDataStore"):
        ThermoelectricAnalyzer(four_probe_file=tmp_path / "four_probe.csv")


def test_xlsx_store_round_trip(tmp_path):
    path = tmp_path / "measurements.xlsx"
    expected = pd.DataFrame(
        {"temperature": [300.0, 400.0], "seebeck": [1e-4, 2e-4], "label": ["a", "b"]}
    )
    store = PandasTabularDataStore()

    TableFileService(store).save(expected, path)
    actual = TableFileService(store).load(path)

    # Excel stores numbers natively; integer-valued floats may be read back as int64.
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False)


def test_workbook_round_trip_preserves_named_sheet_order(tmp_path):
    path = tmp_path / "exports.xlsx"
    tables = [
        ("Run 1", pd.DataFrame({"temperature": [300.0], "value": [1.0]})),
        ("Run 2", pd.DataFrame({"temperature": [310.0], "value": [2.0]})),
    ]
    store = PandasTabularDataStore()

    TableFileService(store).save_workbook(tables, path)
    loaded = list(store.read_workbook(path))

    assert [name for name, _ in loaded] == ["Run 1", "Run 2"]
    pd.testing.assert_frame_equal(loaded[0][1], tables[0][1], check_dtype=False)
    pd.testing.assert_frame_equal(loaded[1][1], tables[1][1], check_dtype=False)


def test_store_write_omits_dataframe_index_in_csv(tmp_path):
    path = tmp_path / "table.csv"
    data = pd.DataFrame({"a": [1, 2]}, index=["x", "y"])

    PandasTabularDataStore().write(data, path)
    text = path.read_text(encoding="utf-8")

    assert not text.startswith(",")  # no unnamed index column
