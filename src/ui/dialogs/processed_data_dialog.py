from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QHBoxLayout,
    QLabel,
)
from PyQt6.QtCore import Qt


class ProcessedDataDialog(QDialog):
    def __init__(self, df, title="Processed Data", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)
        self.df = df
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        if self.df is None or self.df.empty:
            layout.addWidget(QLabel("No data to display."))
        else:
            self.table = QTableWidget()
            self.table.setColumnCount(len(self.df.columns))
            self.table.setRowCount(len(self.df))
            self.table.setHorizontalHeaderLabels(self.df.columns)

            for i in range(len(self.df)):
                for j in range(len(self.df.columns)):
                    val = self.df.iloc[i, j]
                    item = QTableWidgetItem(
                        f"{val:.6g}" if isinstance(val, (float, int)) else str(val)
                    )
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(i, j, item)

            self.table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch
            )
            layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
