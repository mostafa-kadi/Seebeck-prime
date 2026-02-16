from PyQt6.QtWidgets import (
    QTableWidget,
    QMenu,
    QApplication,
    QTableWidgetItem,
)
from PyQt6.QtGui import QKeySequence, QAction
from PyQt6.QtCore import Qt, pyqtSignal


class ClipboardAwareTableWidget(QTableWidget):
    """
    A QTableWidget subclass that implements copy, cut, paste, and delete
    functionality via a context menu and keyboard shortcuts.
    """

    bulkDataChanged = pyqtSignal()

    def __init__(self, rows, columns, parent=None):
        super().__init__(parent)
        self.setRowCount(rows)
        self.setColumnCount(columns)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        """Creates and displays the right-click context menu."""
        menu = QMenu(self)
        copy_action = menu.addAction("Copy")
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        paste_action = menu.addAction("Paste")
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        cut_action = menu.addAction("Cut")
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        delete_action = menu.addAction("Delete")
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)

        copy_action.triggered.connect(self.copy_selection)
        paste_action.triggered.connect(self.paste_selection)
        cut_action.triggered.connect(self.cut_selection)
        delete_action.triggered.connect(self.delete_selection)

        menu.exec(self.viewport().mapToGlobal(pos))

    def keyPressEvent(self, event):
        """Handles keyboard shortcuts for clipboard operations."""
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selection()
        elif event.matches(QKeySequence.StandardKey.Paste):
            self.paste_selection()
        elif event.matches(QKeySequence.StandardKey.Cut):
            self.cut_selection()
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selection()
        else:
            super().keyPressEvent(event)

    def copy_selection(self):
        """Copies the selected cells' text to the clipboard."""
        selection = self.selectedRanges()
        if not selection:
            return

        rows = []
        for r in range(selection[0].topRow(), selection[0].bottomRow() + 1):
            row_data = []
            for c in range(selection[0].leftColumn(), selection[0].rightColumn() + 1):
                item = self.item(r, c)
                row_data.append(item.text() if item else "")
            rows.append("\t".join(row_data))

        clipboard_text = "\n".join(rows)
        QApplication.clipboard().setText(clipboard_text)

    def paste_selection(self):
        """Pastes text from the clipboard into the selected area."""
        selection = self.selectedRanges()
        if not selection:
            return

        start_row, start_col = selection[0].topRow(), selection[0].leftColumn()
        clipboard_text = QApplication.clipboard().text()
        rows = clipboard_text.strip("\n").split("\n")

        self.blockSignals(True)
        for r, row_text in enumerate(rows):
            values = row_text.split("\t")
            for c, value in enumerate(values):
                if (
                    start_row + r < self.rowCount()
                    and start_col + c < self.columnCount()
                ):
                    self.setItem(start_row + r, start_col + c, QTableWidgetItem(value))
        self.blockSignals(False)
        self.bulkDataChanged.emit()

    def cut_selection(self):
        self.copy_selection()
        self.delete_selection()

    def delete_selection(self):
        items = self.selectedItems()
        if not items:
            return

        self.blockSignals(True)
        for item in items:
            try:
                item.setText("")
            except RuntimeError:
                # In case it was already deleted somehow
                pass
        self.blockSignals(False)
        self.bulkDataChanged.emit()
