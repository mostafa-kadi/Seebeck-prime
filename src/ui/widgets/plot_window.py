import matplotlib.pyplot as plt
import numpy as np
import scienceplots
from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QToolBar,
    QApplication,
    QDockWidget,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QPushButton,
    QLabel,
    QFrame,
    QInputDialog,
    QLineEdit,
    QFileDialog,
    QHBoxLayout,
    QColorDialog,
    QMenu,
    QDialog,
    QDialogButtonBox,
)
from PyQt6.QtGui import QAction, QGuiApplication, QImage, QIcon, QColor, QCursor
from PyQt6.QtCore import Qt, QPoint
import qtawesome as qta
import pandas as pd
import io
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar


class PlotWindow(QMainWindow):
    """
    A professional Matplotlib GUI Wrapper with a feature-rich sidebar for
    real-time scientific plot customization, crosshair tracking, and data export.
    Supports OriginLab-like interactivity: click to edit traces, axes, and titles.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scientific Plotting Wrapper")
        self.resize(1100, 850)
        self.setWindowIcon(qta.icon("fa5s.chart-area", color="#2980b9"))

        # Data & State
        self.subplots = []
        self.layout_rows = 1
        self.layout_cols = 1
        self.current_style = ["science", "notebook", "no-latex"]
        self.plot_type = "Line + Scatter"
        self.line_style = "Solid"
        self.line_width = 2
        self.marker_style = "Circle"
        self.marker_size = 6
        self.line_color = "#1f77b4"
        self.marker_color = "#1f77b4"
        self.show_grid = False
        self.show_legend = False
        self.crosshair_enabled = True
        self.xlim = None
        self.ylim = None

        self.crosshair_lines = []

        self.init_ui()

    def init_ui(self, figure=None):
        if self.centralWidget():
            self.centralWidget().deleteLater()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.figure = figure if figure else plt.figure(tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.create_sidebar()
        self.statusBar().showMessage("Publication Quality Plotting Active")

        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas.mpl_connect("button_press_event", self.on_click)

    def create_sidebar(self):
        for d in self.findChildren(QDockWidget):
            d.deleteLater()

        self.dock = QDockWidget("Scientific Controls", self)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        form = QFormLayout()

        # --- Theme & Global ---
        self.side_theme = QComboBox()
        self.side_theme.addItems(
            [
                "Science",
                "Science (Notebook)",
                "IEEE",
                "Nature",
                "High-Vis",
                "Vibrant",
                "Muted",
            ]
        )
        self.side_theme.setCurrentText("Science (Notebook)")
        self.side_theme.currentTextChanged.connect(self.sync_and_draw)
        form.addRow("Theme:", self.side_theme)

        self.side_type = QComboBox()
        self.side_type.addItems(["Line + Scatter", "Line Plot", "Scatter Plot"])
        self.side_type.setCurrentText(self.plot_type)
        self.side_type.currentTextChanged.connect(self.sync_and_draw)
        form.addRow("Mode:", self.side_type)

        container_layout.addLayout(form)
        container_layout.addWidget(self.create_sep())

        # --- Individual Properties ---
        prop_form = QFormLayout()

        self.side_marker = QComboBox()
        self.side_marker.addItems(
            ["Circle", "Square", "Triangle", "Diamond", "Star", "None"]
        )
        self.side_marker.setCurrentText(self.marker_style)
        self.side_marker.currentTextChanged.connect(self.sync_and_draw)
        prop_form.addRow("Marker:", self.side_marker)

        self.side_lstyle = QComboBox()
        self.side_lstyle.addItems(["Solid", "Dashed", "Dotted", "Dash-Dot"])
        self.side_lstyle.setCurrentText(self.line_style)
        self.side_lstyle.currentTextChanged.connect(self.sync_and_draw)
        prop_form.addRow("Line St.:", self.side_lstyle)

        # Colors
        color_layout = QHBoxLayout()
        self.line_color_btn = QPushButton()
        self.line_color_btn.setFixedSize(25, 25)
        self.line_color_btn.setStyleSheet(
            f"background-color: {self.line_color}; border: 1px solid gray;"
        )
        self.line_color_btn.clicked.connect(lambda: self.pick_color("line"))

        self.mark_color_btn = QPushButton()
        self.mark_color_btn.setFixedSize(25, 25)
        self.mark_color_btn.setStyleSheet(
            f"background-color: {self.marker_color}; border: 1px solid gray;"
        )
        self.mark_color_btn.clicked.connect(lambda: self.pick_color("marker"))

        color_layout.addWidget(QLabel("Line:"))
        color_layout.addWidget(self.line_color_btn)
        color_layout.addWidget(QLabel(" Mark:"))
        color_layout.addWidget(self.mark_color_btn)
        color_layout.addStretch()
        prop_form.addRow("Colors:", color_layout)

        container_layout.addLayout(prop_form)
        container_layout.addWidget(self.create_sep())

        # --- Toggles ---
        self.side_grid = QCheckBox("Show Grid")
        self.side_grid.setChecked(self.show_grid)
        self.side_legend = QCheckBox("Show Legend")
        self.side_legend.setChecked(self.show_legend)
        self.side_crosshair = QCheckBox("Interactive Crosshairs")
        self.side_crosshair.setChecked(self.crosshair_enabled)

        for cb in [self.side_grid, self.side_legend, self.side_crosshair]:
            cb.toggled.connect(self.sync_and_draw)
            container_layout.addWidget(cb)

        container_layout.addWidget(self.create_sep())

        # --- Limits ---
        limit_form = QFormLayout()
        self.side_xmin = QLineEdit()
        self.side_xmax = QLineEdit()
        self.side_ymin = QLineEdit()
        self.side_ymax = QLineEdit()
        for le in [self.side_xmin, self.side_xmax, self.side_ymin, self.side_ymax]:
            le.setPlaceholderText("Auto")
            le.editingFinished.connect(self.sync_and_draw)
        limit_form.addRow("X Range:", self.wrap_limits(self.side_xmin, self.side_xmax))
        limit_form.addRow("Y Range:", self.wrap_limits(self.side_ymin, self.side_ymax))
        container_layout.addLayout(limit_form)

        container_layout.addStretch()

        # --- Footer Actions ---
        copy_btn = QPushButton(" Copy Image")
        copy_btn.setIcon(qta.icon("fa5s.copy"))
        copy_btn.clicked.connect(self.copy_to_clipboard)
        container_layout.addWidget(copy_btn)

        excel_btn = QPushButton(" Export Data (XLSX)")
        excel_btn.setIcon(qta.icon("fa5s.file-excel"))
        excel_btn.clicked.connect(self.export_data_to_excel)
        container_layout.addWidget(excel_btn)

        container_layout.addWidget(
            QLabel(
                "<i>Click trace/labels to edit properties.<br>Right-click for options.</i>"
            )
        )

        self.dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)

    def create_sep(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def wrap_limits(self, min_le, max_le):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(min_le)
        l.addWidget(max_le)
        return w

    def pick_color(self, target):
        initial = self.line_color if target == "line" else self.marker_color
        color = QColorDialog.getColor(QColor(initial), self, "Pick Color")
        if color.isValid():
            hex_c = color.name()
            if target == "line":
                self.line_color = hex_c
                self.line_color_btn.setStyleSheet(
                    f"background-color: {hex_c}; border: 1px solid gray;"
                )
            else:
                self.marker_color = hex_c
                self.mark_color_btn.setStyleSheet(
                    f"background-color: {hex_c}; border: 1px solid gray;"
                )
            self.draw_plot()

    def sync_and_draw(self):
        style_map = {
            "Science": ["science", "no-latex"],
            "Science (Notebook)": ["science", "notebook", "no-latex"],
            "IEEE": ["science", "ieee", "no-latex"],
            "Nature": ["science", "nature", "no-latex"],
            "High-Vis": ["science", "high-vis", "no-latex"],
            "Vibrant": ["science", "vibrant", "no-latex"],
            "Muted": ["science", "muted", "no-latex"],
        }
        self.current_style = style_map.get(
            self.side_theme.currentText(), ["science", "notebook", "no-latex"]
        )
        self.plot_type = self.side_type.currentText()
        self.marker_style = self.side_marker.currentText()
        self.line_style = self.side_lstyle.currentText()
        self.show_grid = self.side_grid.isChecked()
        self.show_legend = self.side_legend.isChecked()
        self.crosshair_enabled = self.side_crosshair.isChecked()
        try:
            self.xlim = (
                (float(self.side_xmin.text()), float(self.side_xmax.text()))
                if self.side_xmin.text() and self.side_xmax.text()
                else None
            )
            self.ylim = (
                (float(self.side_ymin.text()), float(self.side_ymax.text()))
                if self.side_ymin.text() and self.side_ymax.text()
                else None
            )
        except:
            pass
        self.draw_plot()

    def on_mouse_move(self, event):
        if not event.inaxes or not self.crosshair_enabled:
            for l in self.crosshair_lines:
                l.set_visible(False)
            self.canvas.draw_idle()
            return
        self.statusBar().showMessage(
            f"Coordinates - T: {event.xdata:.2f} K, Y: {event.ydata:.4f}"
        )
        for l in self.crosshair_lines:
            if l.get_label() == "v":
                l.set_xdata([event.xdata, event.xdata])
            else:
                l.set_ydata([event.ydata, event.ydata])
            l.set_visible(True)
        self.canvas.draw_idle()

    def on_click(self, event):
        """Interact with plot elements (OriginLab style)."""
        if event.inaxes:
            # Right Click -> Context Menu
            if event.button == 3:
                self.show_context_menu(event)
                return

            if event.dblclick:
                ax = event.inaxes

                # Check Text Hits
                if hasattr(ax, "title_obj") and ax.title_obj.contains(event)[0]:
                    self.edit_text(ax.title_obj, ax, "title")
                    return
                if hasattr(ax, "xlabel_obj") and ax.xlabel_obj.contains(event)[0]:
                    self.edit_text(ax.xlabel_obj, ax, "xlabel")
                    return
                if hasattr(ax, "ylabel_obj") and ax.ylabel_obj.contains(event)[0]:
                    self.edit_text(ax.ylabel_obj, ax, "ylabel")
                    return

                # Check Line Hits
                for line in ax.get_lines():
                    if line.contains(event)[0] and hasattr(line, "trace_data"):
                        self.edit_trace_props(line.trace_data)
                        return

                # Fallback: prompt label edit for the subplot
                for i, axis in enumerate(self.figure.axes):
                    if axis == ax and i < len(self.subplots):
                        self.prompt_label_edit(i)
                        break

    def show_context_menu(self, event):
        menu = QMenu(self)
        toggle_grid = menu.addAction("Toggle Grid")
        toggle_grid.setCheckable(True)
        toggle_grid.setChecked(self.show_grid)
        toggle_grid.triggered.connect(
            lambda: self.side_grid.click()
        )  # Click sidebox to trigger sync

        toggle_leg = menu.addAction("Toggle Legend")
        toggle_leg.setCheckable(True)
        toggle_leg.setChecked(self.show_legend)
        toggle_leg.triggered.connect(lambda: self.side_legend.click())

        menu.addSeparator()
        menu.addAction("Auto-Scale Axis").triggered.connect(self.autoscale)
        menu.exec(QCursor.pos())

    def autoscale(self):
        for le in [self.side_xmin, self.side_xmax, self.side_ymin, self.side_ymax]:
            le.clear()
        self.xlim, self.ylim = None, None
        self.draw_plot()

    def edit_text(self, text_obj, ax, key):
        # Find data
        data = next(
            (
                d
                for i, d in enumerate(self.subplots)
                if i < len(self.figure.axes) and self.figure.axes[i] == ax
            ),
            None,
        )
        if data:
            txt, ok = QInputDialog.getText(
                self,
                "Edit Text",
                f"New {key}:",
                QLineEdit.EchoMode.Normal,
                text_obj.get_text(),
            )
            if ok:
                data[key] = txt
                self.draw_plot()

    def edit_trace_props(self, trace_data):
        d = TraceStyleDialog(trace_data, self)
        if d.exec():
            trace_data.update(d.get_properties())
            self.draw_plot()

    def prompt_label_edit(self, index):
        data = self.subplots[index]
        t, ok1 = QInputDialog.getText(
            self,
            "Edit Labels",
            "Title:",
            QLineEdit.EchoMode.Normal,
            data.get("title", ""),
        )
        if ok1:
            xl, ok2 = QInputDialog.getText(
                self,
                "Edit Labels",
                "X-Axis:",
                QLineEdit.EchoMode.Normal,
                data.get("xlabel", ""),
            )
            if ok2:
                yl, ok3 = QInputDialog.getText(
                    self,
                    "Edit Labels",
                    "Y-Axis:",
                    QLineEdit.EchoMode.Normal,
                    data.get("ylabel", ""),
                )
                if ok3:
                    data["title"], data["xlabel"], data["ylabel"] = t, xl, yl
                    self.draw_plot()

    def plot(self, x, y, title=None, xlabel=None, ylabel=None):
        self.subplots = [
            {"x": x, "y": y, "title": title, "xlabel": xlabel, "ylabel": ylabel}
        ]
        self.draw_plot()

    def plot_multi(self, subplots, rows=1, cols=1):
        self.subplots = subplots
        self.layout_rows = rows
        self.layout_cols = cols
        self.draw_plot()

    def set_figure(self, figure):
        self.figure = figure
        self.init_ui(figure)
        self.canvas.draw()

    def draw_plot(self):
        if not self.subplots:
            return
        self.figure.clear()
        self.crosshair_lines = []
        with plt.style.context(self.current_style):
            ls_map = {"Solid": "-", "Dashed": "--", "Dotted": ":", "Dash-Dot": "-."}
            mk_map = {
                "Circle": "o",
                "Square": "s",
                "Triangle": "^",
                "Diamond": "D",
                "Star": "*",
                "None": "",
            }
            ls = ls_map.get(self.line_style, "-")
            mk = mk_map.get(self.marker_style, "o")
            if self.plot_type == "Scatter Plot":
                ls = "None"
            elif self.plot_type == "Line Plot":
                mk = ""
            rows, cols = self.layout_rows, self.layout_cols
            if len(self.subplots) > rows * cols:
                cols = (len(self.subplots) + rows - 1) // rows
            for i, data in enumerate(self.subplots):
                ax = self.figure.add_subplot(rows, cols, i + 1)

                if self.crosshair_enabled:
                    v = ax.axvline(
                        x=0, color="red", ls=":", lw=0.5, visible=False, label="v"
                    )
                    h = ax.axhline(
                        y=0, color="red", ls=":", lw=0.5, visible=False, label="h"
                    )
                    self.crosshair_lines.extend([v, h])

                traces = data.get("traces", [])
                if not traces and "x" in data:
                    traces = [
                        {
                            "x": data["x"],
                            "y": data["y"],
                            "xerr": data.get("xerr"),
                            "yerr": data.get("yerr"),
                            "label": data.get("label", "Data"),
                            "color": data.get("color"),
                        }
                    ]
                for t in traces:
                    x = np.array(t["x"])
                    y = np.array(t["y"])
                    xerr = (
                        np.array(t.get("xerr")) if t.get("xerr") is not None else None
                    )
                    yerr = (
                        np.array(t.get("yerr")) if t.get("yerr") is not None else None
                    )

                    # If scatter plot, line style is None. If line plot, marker is None.
                    # For errorbar, fmt controls both.
                    fmt = ""
                    if self.plot_type == "Scatter Plot":
                        fmt = mk if mk else "o"
                    elif self.plot_type == "Line Plot":
                        fmt = ls if ls else "-"
                    else:
                        fmt = (mk if mk else "o") + (ls if ls else "-")

                    eb = ax.errorbar(
                        x,
                        y,
                        xerr=xerr,
                        yerr=yerr,
                        fmt=fmt,
                        capsize=3,
                        lw=self.line_width,
                        markersize=self.marker_size,
                        color=t.get("color", self.line_color),
                        label=t.get("label", "Data"),
                        alpha=0.8,
                        picker=5,
                    )
                    # For errorbar, the line is eb[0]
                    # We link the trace data to the main line/scatter container
                    eb[0].trace_data = t

                # Save refs for picking
                if data.get("title"):
                    ax.title_obj = ax.set_title(data["title"], picker=True)
                if data.get("xlabel"):
                    ax.xlabel_obj = ax.set_xlabel(data["xlabel"], picker=True)
                if data.get("ylabel"):
                    ax.ylabel_obj = ax.set_ylabel(data["ylabel"], picker=True)

                if self.show_grid:
                    ax.grid(True)
                if self.show_legend:
                    ax.legend()
                if self.xlim:
                    ax.set_xlim(self.xlim)
                if self.ylim:
                    ax.set_ylim(self.ylim)
        self.figure.tight_layout()
        self.canvas.draw()

    def copy_to_clipboard(self):
        buf = io.BytesIO()
        self.figure.savefig(buf, format="png", dpi=300)
        QGuiApplication.clipboard().setImage(QImage.fromData(buf.getvalue()))
        self.statusBar().showMessage("Image copied to clipboard", 2000)

    def export_data_to_excel(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export", "Plot_Data.xlsx", "Excel Files (*.xlsx)"
        )
        if not path:
            return
        try:
            with pd.ExcelWriter(path) as writer:
                for i, data in enumerate(self.subplots):
                    name = data.get("title", f"Plot_{i}")[:30].replace("/", "")
                    pd.DataFrame({"X": data["x"], "Y": data["y"]}).to_excel(
                        writer, sheet_name=name, index=False
                    )
            self.statusBar().showMessage(f"Exported to {path}", 5000)
        except Exception as e:
            self.statusBar().showMessage(f"Error: {str(e)}", 5000)


class TraceStyleDialog(QDialog):
    def __init__(self, trace_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customize Curve")
        self.data = trace_data
        self.init_ui()

    def init_ui(self):
        l = QVBoxLayout(self)
        f = QFormLayout()
        self.lbl = QLineEdit(self.data.get("label", "Data"))
        f.addRow("Label:", self.lbl)
        self.col_btn = QPushButton()
        self.col = self.data.get("color", "#1f77b4")
        self.col_btn.setStyleSheet(f"background-color: {self.col}; min-width: 40px;")
        self.col_btn.clicked.connect(self.pick)
        f.addRow("Color:", self.col_btn)
        self.mk = QComboBox()
        self.mk.addItems(["Circle", "Square", "Triangle", "Diamond", "Star", "None"])
        rev = {
            "o": "Circle",
            "s": "Square",
            "^": "Triangle",
            "D": "Diamond",
            "*": "Star",
            "": "None",
        }
        self.mk.setCurrentText(rev.get(self.data.get("marker", "o"), "Circle"))
        f.addRow("Marker:", self.mk)
        l.addLayout(f)
        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        l.addWidget(bb)

    def pick(self):
        c = QColorDialog.getColor(QColor(self.col), self)
        if c.isValid():
            self.col = c.name()
            self.col_btn.setStyleSheet(
                f"background-color: {self.col}; min-width: 40px;"
            )

    def get_properties(self):
        m = {
            "Circle": "o",
            "Square": "s",
            "Triangle": "^",
            "Diamond": "D",
            "Star": "*",
            "None": "",
        }
        return {
            "label": self.lbl.text(),
            "color": self.col,
            "marker": m.get(self.mk.currentText(), "o"),
        }
