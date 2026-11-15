from types import SimpleNamespace

import pandas as pd

from seebeck_prime.application.table_schema import COL_EC, COL_ZT
from seebeck_prime.presentation.table_plot_data import get_table_data


def test_table_plot_data_sorts_and_keeps_error_values_aligned():
    app = SimpleNamespace(
        data=pd.DataFrame(
            {
                "Temperature": [400.0, 300.0, 350.0],
                "Electrical Conductivity": [4.0, 2.0, float("nan")],
                "±σ": [0.4, 0.2, 0.3],
                "ZT": [0.4, 0.2, float("nan")],
                "±ZT": [0.04, 0.02, 0.03],
            }
        ),
        error_mode=True,
    )

    x, y, x_error, y_error = get_table_data(app, COL_EC)

    assert x == [300.0, 400.0]
    assert y == [2.0, 4.0]
    assert x_error == [0.0, 0.0]
    assert y_error == [0.2, 0.4]


def test_table_plot_data_returns_empty_for_missing_or_empty_plot_values():
    app = SimpleNamespace(
        data=pd.DataFrame({"Temperature": [300.0], "ZT": [float("nan")]}),
        error_mode=False,
    )

    assert get_table_data(app, COL_EC) == (None, None, None, None)
    assert get_table_data(app, COL_ZT) == (None, None, None, None)


def test_table_plot_data_accepts_explicit_frame_and_error_mode():
    frame = pd.DataFrame(
        {
            "Temperature": [400.0, 300.0],
            "Electrical Conductivity": [4.0, 2.0],
            "±σ": [0.4, 0.2],
        }
    )

    x, y, x_error, y_error = get_table_data(frame, COL_EC, error_mode=True)

    assert x == [300.0, 400.0]
    assert y == [2.0, 4.0]
    assert y_error == [0.2, 0.4]

    x, y, _, y_error = get_table_data(frame, COL_EC, error_mode=False)
    assert y_error == [0.0, 0.0]
