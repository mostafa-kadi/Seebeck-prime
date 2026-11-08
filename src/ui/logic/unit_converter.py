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


def _convert_to_base_unit(app, value, uncertainty, column_index):
    """Converts a value and its uncertainty from display units to base units for storage."""
    # Mapping columns to unit types
    # 0: Temp (K)
    # 1: Sigma (S/m) or (S/cm)
    # 2: Seebeck (V/K) or (uV/K)
    # 4: Kappa (W/mK)

    if value is None:
        return None, None

    try:
        val = float(value)
        unc = float(uncertainty) if uncertainty is not None else None
    except (ValueError, TypeError):
        return None, None

    converted_val = val
    converted_unc = unc

    if column_index == 0:  # Temperature
        # Default Base: K
        unit = _get_current_unit(app, "Temperature", "K")
        if unit == "°C":
            converted_val = val + 273.15
            # Uncertainty in Celsius is the same in Kelvin
            converted_unc = unc
        # else: K, no change
    elif column_index == 1:  # Conductivity
        # Default Base: S/m
        unit = _get_current_unit(app, "Electrical Conductivity", "S/m")
        if unit == "S/cm":
            converted_val = val * 100
            if unc is not None:
                converted_unc = unc * 100
        elif unit == "Ohm-cm":
            if val != 0:
                converted_val = 100 / val
                if unc is not None:
                    # Error propagation for y = C/x: dy = |C/x^2| * dx
                    converted_unc = unc * (100 / val**2)
            else:
                converted_val = 0
                converted_unc = (
                    None  # Cannot propagate uncertainty for division by zero
                )
        # else: S/m, no change
    elif column_index == 2:  # Seebeck
        # Default Base: V/K
        unit = _get_current_unit(app, "Seebeck Coeff.", "μV/K")
        if unit == "μV/K":
            converted_val = val * 1e-6
            if unc is not None:
                converted_unc = unc * 1e-6
        elif unit == "mV/K":
            converted_val = val * 1e-3
            if unc is not None:
                converted_unc = unc * 1e-3
        # else: V/K, no change
    elif column_index == 3:  # Power Factor
        # Default Base: W/(m·K²)
        unit = _get_current_unit(app, "Power Factor", "μW/(m·K²)")
        if unit == "μW/(m·K²)":
            converted_val = val * 1e-6
            if unc is not None:
                converted_unc = unc * 1e-6
        elif unit == "mW/(m·K²)":
            converted_val = val * 1e-3
            if unc is not None:
                converted_unc = unc * 1e-3
        # else: W/(m·K²), no change
    elif column_index == 4:  # Thermal Cond
        # Base: W/mK, no change
        pass

    return converted_val, converted_unc


def _convert_from_base_unit(app, value, uncertainty, column_index):
    """Converts a value and its uncertainty from base units to display units for the table."""
    if value is None:
        return "", ""  # Return empty strings for display

    try:
        val = float(value)
        unc = float(uncertainty) if uncertainty is not None else None
    except (ValueError, TypeError):
        return "", ""

    converted_val = val
    converted_unc = unc

    if column_index == 0:  # Temperature
        unit = _get_current_unit(app, "Temperature", "K")
        if unit == "°C":
            converted_val = val - 273.15
            # Uncertainty in Kelvin is the same in Celsius
            converted_unc = unc
        # else: K, no change
    elif column_index == 1:  # Sigma
        unit = _get_current_unit(app, "Electrical Conductivity", "S/m")
        if unit == "S/cm":
            converted_val = val / 100
            if unc is not None:
                converted_unc = unc / 100
        elif unit == "Ohm-cm":
            if val != 0:
                converted_val = 100 / val
                if unc is not None:
                    # Error propagation for y = C/x: dy = |C/x^2| * dx
                    converted_unc = unc * (100 / val**2)
            else:
                converted_val = float("inf")
                converted_unc = (
                    None  # Cannot propagate uncertainty for division by zero
                )
        # else: S/m, no change
    elif column_index == 2:  # Seebeck
        unit = _get_current_unit(app, "Seebeck Coeff.", "μV/K")
        if unit == "μV/K":
            converted_val = val * 1e6
            if unc is not None:
                converted_unc = unc * 1e6
        elif unit == "mV/K":
            converted_val = val * 1e3
            if unc is not None:
                converted_unc = unc * 1e3
        # else: V/K, no change
    elif column_index == 3:  # Power Factor (assuming base is W/mK^2)
        unit = _get_current_unit(app, "Power Factor", "μW/(m·K²)")
        if unit == "μW/(m·K²)":
            converted_val = val * 1e6
            if unc is not None:
                converted_unc = unc * 1e6
        elif unit == "mW/(m·K²)":
            converted_val = val * 1e3
            if unc is not None:
                converted_unc = unc * 1e3
        # else: W/mK^2, no change
    # elif column_index == 4: Thermal Cond, no change

    return converted_val, converted_unc


def _get_display_value(app, value, uncertainty, column_index):
    """Converts a base unit value and its uncertainty to a formatted display string/float."""
    converted_val, converted_unc = _convert_from_base_unit(
        app, value, uncertainty, column_index
    )
    if isinstance(converted_val, (int, float)):
        import math

        if math.isinf(converted_val):
            return "Inf"
        # Format value and uncertainty
        if converted_unc is not None and not math.isinf(converted_unc):
            return (
                f"{converted_val:.5g} ± {converted_unc:.5g}"  # Display with uncertainty
            )
        return f"{converted_val:.5g}"  # Display without uncertainty
    return converted_val
