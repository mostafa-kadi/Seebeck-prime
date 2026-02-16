from PyQt6.QtWidgets import QColorDialog


def pick_color(initial_color="blue", parent=None):
    """
    Opens a QColorDialog and returns the hex color string if valid,
    otherwise returns None.
    """
    color = QColorDialog.getColor(initial=initial_color, parent=parent)
    if color.isValid():
        return color.name()
    return None


def add_unit_selector(toolbar, label_text, items, callback):
    """
    Shared helper to add a labeled QComboBox to a toolbar.
    """
    from PyQt6.QtWidgets import QLabel, QComboBox

    toolbar.addWidget(QLabel(label_text))
    combo = QComboBox()
    combo.addItems(items)
    combo.currentTextChanged.connect(callback)
    toolbar.addWidget(combo)
    return combo
