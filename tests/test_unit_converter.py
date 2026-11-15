import pytest
from unittest.mock import Mock
import numpy as np
from seebeck_prime.presentation.unit_converter import (
    _convert_to_base_unit,
    _convert_from_base_unit,
    _get_display_value,
)
from seebeck_prime.application.table_schema import (
    COL_TEMP,
    COL_EC,
    COL_SEEBECK,
    COL_PF,
    COL_K_TOTAL,
    COL_ZT,
)


# Mock the app object for unit_converter functions
@pytest.fixture
def mock_app():
    app = Mock()
    app.unit_combos = {
        "Temperature": Mock(),
        "Seebeck Coeff.": Mock(),
        "Electrical Conductivity": Mock(),
        "Power Factor": Mock(),
        "Thermal Cond.": Mock(),
        "ZT": Mock(),
    }
    # Set default return values
    app.unit_combos["Temperature"].currentText.return_value = "K"
    app.unit_combos["Seebeck Coeff."].currentText.return_value = "μV/K"
    app.unit_combos["Electrical Conductivity"].currentText.return_value = "S/cm"
    app.unit_combos["Power Factor"].currentText.return_value = "μW/(m·K²)"
    app.unit_combos["Thermal Cond."].currentText.return_value = "W/(m·K)"
    app.unit_combos["ZT"].currentText.return_value = ""
    return app


# --- Test _convert_to_base_unit ---
def test_convert_to_base_unit_temp(mock_app):
    # K to K
    val, unc = _convert_to_base_unit(mock_app, 300, 5, COL_TEMP)
    assert val == pytest.approx(300)
    assert unc == pytest.approx(5)

    # C to K
    mock_app.unit_combos["Temperature"].currentText.return_value = "°C"
    val, unc = _convert_to_base_unit(mock_app, 27, 2, COL_TEMP)
    assert val == pytest.approx(300.15)
    assert unc == pytest.approx(2)  # Uncertainty in C is same as K


def test_convert_to_base_unit_seebeck(mock_app):
    # µV/K to V/K
    val, unc = _convert_to_base_unit(mock_app, 100, 5, COL_SEEBECK)
    assert val == pytest.approx(100e-6)
    assert unc == pytest.approx(5e-6)


def test_convert_to_base_unit_conductivity(mock_app):
    # S/cm to S/m
    val, unc = _convert_to_base_unit(mock_app, 100, 5, COL_EC)
    assert val == pytest.approx(100 * 100)  # S/cm * 100 = S/m
    assert unc == pytest.approx(5 * 100)  # Uncertainty scales linearly

    # Ohm-cm to S/m
    mock_app.unit_combos["Electrical Conductivity"].currentText.return_value = "Ohm-cm"
    val, unc = _convert_to_base_unit(mock_app, 1, 0.1, COL_EC)
    assert val == pytest.approx(100)  # 1 / (1 Ohm-cm) = 1 S/cm = 100 S/m
    # Uncertainty for 1/x: u_y = |y/x| * u_x
    # Here, y = 1/x, so u_y = |1/x^2| * u_x
    # sigma_sm = 1 / (rho_ocm * 1e-2) = 100 / rho_ocm
    # d(sigma_sm)/d(rho_ocm) = -100 / rho_ocm^2
    # u_sigma_sm = |-100 / rho_ocm^2| * u_rho_ocm
    expected_unc = (100 / (1**2)) * 0.1
    assert unc == pytest.approx(expected_unc)


def test_convert_to_base_unit_power_factor(mock_app):
    # µW/(m·K²) to W/(m·K²)
    val, unc = _convert_to_base_unit(mock_app, 100, 5, COL_PF)
    assert val == pytest.approx(100e-6)
    assert unc == pytest.approx(5e-6)


def test_convert_to_base_unit_thermal_conductivity(mock_app):
    # W/(m·K) to W/(m·K) (no change)
    val, unc = _convert_to_base_unit(mock_app, 10, 1, COL_K_TOTAL)
    assert val == pytest.approx(10)
    assert unc == pytest.approx(1)


def test_convert_to_base_unit_zt(mock_app):
    # ZT has no units, should return value and uncertainty unchanged
    val, unc = _convert_to_base_unit(mock_app, 1.5, 0.1, COL_ZT)
    assert val == pytest.approx(1.5)
    assert unc == pytest.approx(0.1)


def test_convert_to_base_unit_none_uncertainty(mock_app):
    val, unc = _convert_to_base_unit(mock_app, 300, None, COL_TEMP)
    assert val == pytest.approx(300)
    assert unc is None


# --- Test _convert_from_base_unit ---
def test_convert_from_base_unit_temp(mock_app):
    # K to K
    val, unc = _convert_from_base_unit(mock_app, 300, 5, COL_TEMP)
    assert val == pytest.approx(300)
    assert unc == pytest.approx(5)

    # K to C
    mock_app.unit_combos["Temperature"].currentText.return_value = "°C"
    val, unc = _convert_from_base_unit(mock_app, 300.15, 2, COL_TEMP)
    assert val == pytest.approx(27)
    assert unc == pytest.approx(2)


def test_convert_from_base_unit_seebeck(mock_app):
    # V/K to µV/K
    val, unc = _convert_from_base_unit(mock_app, 100e-6, 5e-6, COL_SEEBECK)
    assert val == pytest.approx(100)
    assert unc == pytest.approx(5)


def test_convert_from_base_unit_conductivity(mock_app):
    # S/m to S/cm
    val, unc = _convert_from_base_unit(mock_app, 10000, 500, COL_EC)
    assert val == pytest.approx(100)
    assert unc == pytest.approx(5)

    # S/m to Ohm-cm
    mock_app.unit_combos["Electrical Conductivity"].currentText.return_value = "Ohm-cm"
    val, unc = _convert_from_base_unit(mock_app, 100, 10, COL_EC)
    assert val == pytest.approx(1)  # 1 / (100 S/m) = 0.01 m/S = 1 Ohm-cm
    # Uncertainty for 1/x: u_y = |y/x| * u_x
    # Here, y = 1/x, so u_y = |1/x^2| * u_x
    # rho_ocm = 100 / sigma_sm
    # d(rho_ocm)/d(sigma_sm) = -100 / sigma_sm^2
    # u_rho_ocm = |-100 / sigma_sm^2| * u_sigma_sm
    expected_unc = (100 / (100**2)) * 10
    assert unc == pytest.approx(expected_unc)


def test_convert_from_base_unit_power_factor(mock_app):
    # W/(m·K²) to µW/(m·K²)
    val, unc = _convert_from_base_unit(mock_app, 100e-6, 5e-6, COL_PF)
    assert val == pytest.approx(100)
    assert unc == pytest.approx(5)


def test_convert_from_base_unit_thermal_conductivity(mock_app):
    # W/(m·K) to W/(m·K) (no change)
    val, unc = _convert_from_base_unit(mock_app, 10, 1, COL_K_TOTAL)
    assert val == pytest.approx(10)
    assert unc == pytest.approx(1)


def test_convert_from_base_unit_zt(mock_app):
    # ZT has no units, should return value and uncertainty unchanged
    val, unc = _convert_from_base_unit(mock_app, 1.5, 0.1, COL_ZT)
    assert val == pytest.approx(1.5)
    assert unc == pytest.approx(0.1)


def test_convert_from_base_unit_none_uncertainty(mock_app):
    val, unc = _convert_from_base_unit(mock_app, 300, None, COL_TEMP)
    assert val == pytest.approx(300)
    assert unc is None


# --- Test _get_display_value ---
def test_get_display_value_with_uncertainty(mock_app):
    mock_app.unit_combos["Temperature"].currentText.return_value = "K"
    display_str = _get_display_value(mock_app, 300.123, 5.456, COL_TEMP)
    assert display_str == "300.12 ± 5.456"


def test_get_display_value_without_uncertainty(mock_app):
    mock_app.unit_combos["Temperature"].currentText.return_value = "K"
    display_str = _get_display_value(mock_app, 300.123, None, COL_TEMP)
    assert display_str == "300.12"


def test_get_display_value_zero_uncertainty(mock_app):
    mock_app.unit_combos["Temperature"].currentText.return_value = "K"
    display_str = _get_display_value(mock_app, 300.123, 0, COL_TEMP)
    assert display_str == "300.12 ± 0"


def test_get_display_value_small_uncertainty(mock_app):
    mock_app.unit_combos["Temperature"].currentText.return_value = "K"
    display_str = _get_display_value(mock_app, 300.12345, 0.00001, COL_TEMP)
    assert display_str == "300.12 ± 1e-05"


def test_get_display_value_large_uncertainty(mock_app):
    mock_app.unit_combos["Temperature"].currentText.return_value = "K"
    display_str = _get_display_value(mock_app, 12345.67, 1234.56, COL_TEMP)
    assert display_str == "12346 ± 1234.6"


def test_get_display_value_zt_no_units(mock_app):
    mock_app.unit_combos["ZT"].currentText.return_value = ""
    display_str = _get_display_value(mock_app, 1.567, 0.012, COL_ZT)
    assert display_str == "1.567 ± 0.012"


def test_get_display_value_nan_values(mock_app):
    mock_app.unit_combos["Temperature"].currentText.return_value = "K"
    display_str = _get_display_value(mock_app, np.nan, np.nan, COL_TEMP)
    assert display_str == "nan ± nan"


def test_get_display_value_inf_values(mock_app):
    mock_app.unit_combos["Temperature"].currentText.return_value = "K"
    display_str = _get_display_value(mock_app, np.inf, np.inf, COL_TEMP)
    assert display_str == "Inf"


def test_get_display_value_negative_values(mock_app):
    mock_app.unit_combos["Temperature"].currentText.return_value = "K"
    display_str = _get_display_value(mock_app, -300.123, 5.456, COL_TEMP)
    assert display_str == "-300.12 ± 5.456"
