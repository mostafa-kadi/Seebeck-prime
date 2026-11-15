"""Presentation adapter for unit display and conversion interactions."""

"""Presentation adapter for the application's unit-conversion use cases."""

import math

from seebeck_prime.application.unit_conversion import (
    from_base_value,
    to_base_value,
    uncertainty_from_base,
    uncertainty_to_base,
)


_COLUMN_UNITS = {
    0: ("Temperature", "K", "temperature"),
    1: ("Electrical Conductivity", "S/m", "conductivity"),
    2: ("Seebeck Coeff.", "μV/K", "seebeck"),
    3: ("Power Factor", "μW/(m·K²)", "power_factor"),
    4: ("Thermal Conductivity", "W/(m·K)", "thermal_conductivity"),
}


def on_unit_changed(app):
    """Refresh table headings and values after a display-unit selection."""
    app.update_headers()
    app.load_data_into_table(app.data, is_base_units=True)
    app.recalculate_all_properties()


def _get_current_unit(app, key, default):
    """Read the selected unit while supporting the established UI mapping."""
    if key in app.unit_combos:
        combo = app.unit_combos[key]
        if combo is not None:
            return combo.currentText()
    return default


def _convert_to_base_unit(app, value, uncertainty, column_index):
    if value is None:
        return None, None
    try:
        numeric_value = float(value)
        numeric_uncertainty = float(uncertainty) if uncertainty is not None else None
    except (ValueError, TypeError):
        return None, None

    column = _COLUMN_UNITS.get(column_index)
    if column is None:
        return numeric_value, numeric_uncertainty
    key, default, quantity = column
    unit = _get_current_unit(app, key, default)
    converted_value = to_base_value(numeric_value, unit, quantity)
    converted_uncertainty = uncertainty_to_base(
        numeric_value, numeric_uncertainty, unit, quantity
    )
    return converted_value, converted_uncertainty


def _convert_from_base_unit(app, value, uncertainty, column_index):
    if value is None:
        return "", ""
    try:
        numeric_value = float(value)
        numeric_uncertainty = float(uncertainty) if uncertainty is not None else None
    except (ValueError, TypeError):
        return "", ""

    column = _COLUMN_UNITS.get(column_index)
    if column is None:
        return numeric_value, numeric_uncertainty
    key, default, quantity = column
    unit = _get_current_unit(app, key, default)
    converted_value = from_base_value(numeric_value, unit, quantity)
    converted_uncertainty = uncertainty_from_base(
        numeric_value, numeric_uncertainty, unit, quantity
    )
    return converted_value, converted_uncertainty


def _get_display_value(app, value, uncertainty, column_index):
    converted_value, converted_uncertainty = _convert_from_base_unit(
        app, value, uncertainty, column_index
    )
    if isinstance(converted_value, (int, float)):
        if math.isinf(converted_value):
            return "Inf"
        if converted_uncertainty is not None and not math.isinf(converted_uncertainty):
            return f"{converted_value:.5g} ± {converted_uncertainty:.5g}"
        return f"{converted_value:.5g}"
    return converted_value
