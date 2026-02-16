import sys
import os
import logging
import matplotlib

# Set the Qt API for Matplotlib and specify the backend early for PyQt6
os.environ["QT_API"] = "pyqt6"
os.environ["MPLBACKEND"] = "QtAgg"

# Suppress Matplotlib's informative/warning messages about backends
logging.getLogger("matplotlib").setLevel(logging.ERROR)

# Set the backend to QtAgg and disable interactive mode
matplotlib.use("QtAgg")
matplotlib.interactive(False)

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import ThermoelectricApp

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Ensure the app style works well with icons
    app.setStyle("Fusion")

    ex = ThermoelectricApp()

    # Center on screen
    screen = app.primaryScreen().geometry()
    size = ex.geometry()
    ex.move(
        (screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2
    )

    ex.show()
    ex.raise_()
    ex.activateWindow()

    sys.exit(app.exec())
