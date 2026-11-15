import sys
import os
import logging

import matplotlib

# Configure Python module search paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_DIR, "src")

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Fix PyQt6 DLL loading on Windows
if sys.platform == "win32":
    QT_BIN = os.path.join(
        sys.prefix,
        "Lib",
        "site-packages",
        "PyQt6",
        "Qt6",
        "bin",
    )

    if os.path.isdir(QT_BIN):
        try:
            os.add_dll_directory(QT_BIN)
        except (OSError, AttributeError):
            pass

# Configure Matplotlib for PyQt6
os.environ["QT_API"] = "pyqt6"
os.environ["MPLBACKEND"] = "QtAgg"

logging.getLogger("matplotlib").setLevel(logging.ERROR)

matplotlib.use("QtAgg")
matplotlib.interactive(False)

from PyQt6.QtWidgets import QApplication

# Import the main application window from its canonical package location
from seebeck_prime.gui.main_window import ThermoelectricApp
from seebeck_prime.application.table_files import TableFileService
from seebeck_prime.infrastructure.io import PandasTabularDataStore


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Composition root: keep concrete persistence adapters outside the GUI.
    tabular_data_store = PandasTabularDataStore()
    table_file_service = TableFileService(tabular_data_store)
    window = ThermoelectricApp(
        table_file_service=table_file_service,
        measurement_data_store=tabular_data_store,
    )

    # Center the window on the primary screen
    screen = app.primaryScreen()

    if screen is not None:
        screen_geometry = screen.availableGeometry()
        window_geometry = window.frameGeometry()

        window_geometry.moveCenter(screen_geometry.center())
        window.move(window_geometry.topLeft())

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
