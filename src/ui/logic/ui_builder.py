from PyQt6.QtWidgets import QMenu, QLabel, QComboBox, QPushButton, QToolButton, QToolBar
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
import qtawesome as qta
from .ui_utils import add_unit_selector

# Import column constants for lambda connections if needed
from src.ui.logic.table_handler import (
    COL_EC,
    COL_SEEBECK,
    COL_PF,
    COL_K_TOTAL,
    COL_K_E,
    COL_K_L,
    COL_ZT,
)


def create_menu_bar(mw):
    """Create the main menu bar with File, Edit, and Tools menus."""
    menu_bar = mw.menuBar()
    file_menu = menu_bar.addMenu("&File")

    file_menu.addAction(
        QAction(
            qta.icon("fa5s.file-alt"),
            "&New",
            mw,
            shortcut="Ctrl+N",
            triggered=mw.new_file,
        )
    )
    file_menu.addAction(
        QAction(
            qta.icon("fa5s.folder-open"),
            "&Open...",
            mw,
            shortcut="Ctrl+O",
            triggered=mw.open_file,
        )
    )
    file_menu.addAction(
        QAction(
            qta.icon("fa5s.save"),
            "&Save",
            mw,
            shortcut="Ctrl+S",
            triggered=mw.save_file,
        )
    )
    file_menu.addAction(
        QAction(
            qta.icon("fa5s.save"),
            "Save &As...",
            mw,
            shortcut="Ctrl+Shift+S",
            triggered=mw.save_as_file,
        )
    )
    file_menu.addSeparator()
    file_menu.addAction(
        QAction(
            qta.icon("fa5s.sign-out-alt"),
            "&Exit",
            mw,
            shortcut="Ctrl+Q",
            triggered=mw.close,
        )
    )

    tools_menu = menu_bar.addMenu("&Tools")
    kappa_tool_action = QAction(
        qta.icon("fa5s.exchange-alt"), "Thermal Conductivity...", mw
    )
    kappa_tool_action.setStatusTip(
        "Calculate, interpolate or extrapolate thermal conductivity"
    )
    kappa_tool_action.triggered.connect(mw.open_kappa_tool_dialog)
    tools_menu.addAction(kappa_tool_action)

    multi_sample_action = QAction(
        qta.icon("fa5s.layer-group"), "Multi-Sample Comparison...", mw
    )
    multi_sample_action.setStatusTip(
        "Compare thermoelectric data across multiple samples/sheets"
    )
    multi_sample_action.triggered.connect(mw.open_multi_sample_tool)
    tools_menu.addAction(multi_sample_action)

    weighted_mobility_action = QAction(
        qta.icon("fa5s.microchip"), "Weighted Mobility...", mw
    )
    weighted_mobility_action.setStatusTip(
        "Calculate weighted mobility (μ_w) based on Snyder et al."
    )
    weighted_mobility_action.triggered.connect(mw.open_weighted_mobility_tool)
    tools_menu.addAction(weighted_mobility_action)

    hall_mobility_action = QAction(
        qta.icon("fa5s.magnet"), "Hall Mobility & Carrier Transport...", mw
    )
    hall_mobility_action.setStatusTip(
        "Calculate Hall mobility (μ_H), carrier density (n_H), and scattering exponents"
    )
    hall_mobility_action.triggered.connect(mw.open_hall_mobility_tool)
    tools_menu.addAction(hall_mobility_action)

    spb_tool_action = QAction(
        qta.icon("fa5s.atom"), "SPB Modeling & Transport Optimization...", mw
    )
    spb_tool_action.setStatusTip(
        "Single Parabolic Band model, effective mass estimation, Pisarenko curves, and optimal doping"
    )
    spb_tool_action.triggered.connect(mw.open_spb_tool)
    tools_menu.addAction(spb_tool_action)



    help_menu = menu_bar.addMenu("&Help")
    about_action = QAction(qta.icon("fa5s.info-circle"), "&About", mw)
    about_action.triggered.connect(mw.about_app)
    help_menu.addAction(about_action)


def create_toolbar(mw):
    """Create the toolbar for unit selection and calculations."""
    toolbar = mw.addToolBar("Controls")

    mw.temp_combo = add_unit_selector(
        toolbar, "Temp Unit:", ["K", "°C"], mw.on_unit_changed
    )
    mw.ec_combo = add_unit_selector(
        toolbar, "EC Unit:", ["S/cm", "S/m", "Ohm-cm"], mw.on_unit_changed
    )
    mw.pf_combo = add_unit_selector(
        toolbar, "PF Unit:", ["mW/mK²", "μW/mK²", "W/mK²"], mw.on_unit_changed
    )

    toolbar.addSeparator()
    toolbar.addWidget(QLabel("κₑ Method:"))
    mw.kappa_method_combo = QComboBox()
    mw.kappa_method_combo.addItems(["Standard Lorenz", "Seebeck-Derived"])
    mw.kappa_method_combo.currentIndexChanged.connect(mw.recalculate_all_properties)
    toolbar.addWidget(mw.kappa_method_combo)

    calc_button = QPushButton("Calculate All")
    calc_button.setIcon(qta.icon("fa5s.calculator"))
    calc_button.setToolTip("Recalculate all derived values in the table")
    calc_button.clicked.connect(mw.recalculate_all_properties)
    toolbar.addWidget(calc_button)

    toolbar.addSeparator()
    error_button = QPushButton(" Add Error Bars")
    error_button.setIcon(qta.icon("fa5s.balance-scale"))
    error_button.setToolTip("Toggle Gaussian error propagation (error bars)")
    error_button.setCheckable(True)
    error_button.clicked.connect(mw.toggle_error_bars)
    toolbar.addWidget(error_button)

    toolbar.addSeparator()
    mw.plot_tool_btn = QToolButton()
    mw.plot_tool_btn.setText(" Plot Data")
    mw.plot_tool_btn.setIcon(qta.icon("fa5s.chart-area", color="#2c3e50"))
    mw.plot_tool_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    mw.plot_tool_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
    mw.plot_tool_btn.clicked.connect(mw.open_plot_selection_dialog)

    plot_menu = QMenu(mw)
    plot_menu.addAction(qta.icon("fa5s.chart-line"), "Seebeck vs. T").triggered.connect(
        lambda: mw.create_plot(COL_SEEBECK)
    )
    plot_menu.addAction(
        qta.icon("fa5s.chart-line"), "Elec. Cond. vs. T"
    ).triggered.connect(lambda: mw.create_plot(COL_EC))
    plot_menu.addAction(
        qta.icon("fa5s.chart-line"), "Power Factor vs. T"
    ).triggered.connect(lambda: mw.create_plot(COL_PF))
    plot_menu.addSeparator()
    plot_menu.addAction(
        qta.icon("fa5s.chart-line"), "Total Thermal Cond. vs. T"
    ).triggered.connect(lambda: mw.create_plot(COL_K_TOTAL))
    plot_menu.addAction(
        qta.icon("fa5s.chart-line"), "Lattice Thermal Cond. vs. T"
    ).triggered.connect(lambda: mw.create_plot(COL_K_L))
    plot_menu.addAction(
        qta.icon("fa5s.chart-line"), "Electronic Thermal Cond. vs. T"
    ).triggered.connect(lambda: mw.create_plot(COL_K_E))
    plot_menu.addSeparator()
    plot_menu.addAction(qta.icon("fa5s.chart-line"), "ZT vs. T").triggered.connect(
        lambda: mw.create_plot(COL_ZT)
    )
    plot_menu.addSeparator()
    plot_menu.addAction(
        qta.icon("fa5s.layer-group"), "Plot All Properties"
    ).triggered.connect(mw.plot_all_properties)
    plot_menu.addAction(
        qta.icon("fa5s.th-large"), "Custom Plot Layout..."
    ).triggered.connect(mw.open_plot_selection_dialog)

    mw.plot_tool_btn.setMenu(plot_menu)
    toolbar.addWidget(mw.plot_tool_btn)
