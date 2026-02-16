def on_unit_changed(app):
    """A generic slot to handle unit changes and recalculate."""
    # 1. Update headers
    app.update_headers()

    # 2. Refresh the display (convert internal base units -> new display units)
    # Internal `app.data` is ALWAYS in base units.
    app.load_data_into_table(app.data, is_base_units=True)

    # 3. Recalculate
    app.recalculate_all_properties()


def _get_current_unit(app, key, default):
    """Safely retrieves the current text from a combo box if it exists."""
    if key in app.unit_combos:
        combo = app.unit_combos[key]
        if combo is not None:
            return combo.currentText()
    return default


def _convert_to_base_unit(app, value, column_index):
    """Converts a value from its display unit to its base unit for storage."""
    # Mapping columns to unit types
    # 0: Temp (K)
    # 1: Sigma (S/m) or (S/cm)
    # 2: Seebeck (V/K) or (uV/K)
    # 4: Kappa (W/mK)

    if value is None:
        return None

    try:
        val = float(value)
    except:
        return None

    if column_index == 0:  # Temperature
        # Default Base: K
        unit = _get_current_unit(app, "Temperature", "K")
        if unit == "°C":
            return val + 273.15
        return val  # K

    elif column_index == 1:  # Conductivity
        # Default Base: S/m
        unit = _get_current_unit(app, "Electrical Conductivity", "S/m")
        if unit == "S/cm":
            return val * 100
        elif unit == "Ohm-cm":
            return 100 / val if val != 0 else 0
        return val  # S/m

    elif column_index == 2:  # Seebeck
        # Default Base: V/K
        # If no combo, we assume standard input uV/K if that was legacy behavior,
        # OR we assume V/K?
        # Legacy code: `return value * 1e-6` implies input is uV/K.
        # So default should be uV/K.
        unit = _get_current_unit(app, "Seebeck Coeff.", "μV/K")

        if unit == "μV/K":
            return val * 1e-6
        elif unit == "mV/K":
            return val * 1e-3
        return val  # V/K, or if unit="V/K"

    elif column_index == 4:  # Thermal Cond
        # Base: W/mK
        return val  # Usually only one unit supported or standard

    return val


def _convert_from_base_unit(app, value, column_index):
    """Converts a value from its base unit to its display unit for the table."""
    if value is None:
        return ""

    try:
        val = float(value)
    except:
        return ""

    if column_index == 0:  # Temperature
        unit = _get_current_unit(app, "Temperature", "K")
        if unit == "°C":
            return val - 273.15
        return val

    elif column_index == 1:  # Sigma
        unit = _get_current_unit(app, "Electrical Conductivity", "S/m")
        if unit == "S/cm":
            return val / 100
        elif unit == "Ohm-cm":
            return 100 / val if val != 0 else float("inf")
        return val

    elif column_index == 2:  # Seebeck
        unit = _get_current_unit(app, "Seebeck Coeff.", "μV/K")

        if unit == "μV/K":
            return val * 1e6
        elif unit == "mV/K":
            return val * 1e3
        return val

    elif column_index == 3:  # Power Factor
        # Legacy code checked app.units["pf"]
        unit = _get_current_unit(app, "Power Factor", "μW/mK²")
        if unit == "μW/mK²":
            return val * 1e6
        elif unit == "mW/mK²":
            return val * 1e3
        return val

    return val


def _get_display_value(app, value, column_index):
    """Converts a base unit value to a formatted display string/float."""
    converted = _convert_from_base_unit(app, value, column_index)
    if isinstance(converted, (int, float)):
        # Check for infinity
        import math

        if math.isinf(converted):
            return "Inf"
        return round(converted, 5)  # Reasonable precision
    return converted
