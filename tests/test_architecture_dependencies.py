import ast
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src"


def _imports_in(package_name):
    package_path = PACKAGE_ROOT / package_name
    found = []
    for source_path in package_path.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.append(node.module)
    return found


def test_domain_has_no_outer_layer_or_gui_imports():
    forbidden = (
        "PyQt6",
        "seebeck_prime.application",
        "seebeck_prime.gui",
        "seebeck_prime.infrastructure",
        "seebeck_prime.plugins",
        "seebeck_prime.legacy",
    )
    imports = _imports_in("domain")

    assert not [name for name in imports if name.startswith(forbidden)]


def test_no_package_imports_the_retired_legacy_tree():
    """The ``src/legacy`` tree was deleted in Phase 4; no layer may import it.

    Migration-map row 24 tightens the earlier per-layer exceptions
    (``legacy.ui`` for the GUI, ``legacy.core`` for the dialogs) into a single
    prohibition covering the whole source tree.
    """
    offenders = []
    for source_path in PACKAGE_ROOT.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                if name == "seebeck_prime.legacy" or name.startswith("seebeck_prime.legacy."):
                    offenders.append(
                        f"{source_path.relative_to(PACKAGE_ROOT)}: {name}"
                    )

    assert offenders == []


def test_application_does_not_import_presentation_or_concrete_infrastructure():
    imports = _imports_in("application")

    assert not [
        name
        for name in imports
        if name == "PyQt6"
        or name.startswith("seebeck_prime.gui")
        or name.startswith("seebeck_prime.infrastructure")
        or name.startswith("seebeck_prime.plugins")
        or name.startswith("seebeck_prime.legacy")
    ]


def test_infrastructure_has_no_gui_toolkit_dependency():
    imports = _imports_in("infrastructure")

    forbidden = ("seebeck_prime.gui", "seebeck_prime.presentation", "seebeck_prime.legacy")
    assert not [
        name for name in imports
        if name == "PyQt6" or name.startswith(forbidden) or name.startswith("PyQt6.")
    ]


def test_main_window_uses_application_layer_instead_of_domain_formulas():
    source = (PACKAGE_ROOT / "gui" / "main_window.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)

    assert not [name for name in imported_modules if name.startswith("seebeck_prime.domain")]


def test_application_services_does_not_read_or_write_files_directly():
    source = (PACKAGE_ROOT / "application" / "services.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    file_io_methods = {"read_csv", "read_excel", "to_csv", "to_excel"}
    calls = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]

    assert not file_io_methods.intersection(calls)


def test_main_window_exports_processed_tables_through_file_service():
    source = (PACKAGE_ROOT / "gui" / "main_window.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    direct_io_methods = {"read_csv", "read_excel", "to_csv", "to_excel", "ExcelWriter"}
    calls = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    ]

    assert not direct_io_methods.intersection(calls)
    assert "table_file_service" in source


def test_plot_window_exports_through_application_file_service():
    source = (PACKAGE_ROOT / "presentation" / "plot_window.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    direct_io_methods = {"ExcelWriter", "to_excel", "to_csv"}
    calls = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    ]

    assert not direct_io_methods.intersection(calls)
    assert "save_workbook" in source


def test_table_presentation_uses_application_column_contract():
    source = (PACKAGE_ROOT / "presentation" / "table_handler.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]

    assert "seebeck_prime.application.table_schema" in imports
    assert not [name for name in imports if name.startswith("seebeck_prime.domain")]


def test_device_efficiency_dialog_delegates_thermoelectric_properties():
    source = (PACKAGE_ROOT / "presentation" / "dialogs" / "device_efficiency_dialog.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imported_modules = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]

    assert "seebeck_prime.application.use_cases" in imported_modules
    assert "seebeck_prime.domain.calculations" not in imported_modules
    assert not any(module.startswith("seebeck_prime.legacy.ui.logic") for module in imported_modules)


def test_kappa_presentation_uses_application_formula_services():
    source = (PACKAGE_ROOT / "presentation" / "kappa_logic.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = [
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]
    assert "seebeck_prime.application.use_cases" in imported_modules
    assert not [name for name in imported_modules if name.startswith("seebeck_prime.legacy.core")]
    assert "calculate_formula_mass_use_case" in source
    assert "calculate_dulong_petit_limit_use_case" in source

    dialog = (PACKAGE_ROOT / "presentation" / "dialogs" / "kappa_dialog.py").read_text(encoding="utf-8")
    assert "seebeck_prime.presentation.kappa_logic" in dialog


def test_hall_and_spb_application_models_depend_on_domain():
    imports = _imports_in("application")
    assert not [name for name in imports if name.startswith("seebeck_prime.plugins")]


def test_main_window_uses_presentation_menu_and_toolbar_builder():
    source = (PACKAGE_ROOT / "gui" / "main_window.py").read_text(encoding="utf-8")
    assert "import seebeck_prime.presentation.ui_builder as ui_builder" in source

    canonical = (PACKAGE_ROOT / "presentation" / "ui_builder.py").read_text(encoding="utf-8")
    assert "from seebeck_prime.presentation.ui_utils import add_unit_selector" in canonical


def test_main_window_uses_canonical_unit_conversion_presentation_adapter():
    source = (PACKAGE_ROOT / "gui" / "main_window.py").read_text(encoding="utf-8")
    assert "import seebeck_prime.presentation.unit_converter as unit_converter" in source

    canonical = (PACKAGE_ROOT / "presentation" / "unit_converter.py").read_text(encoding="utf-8")
    assert "seebeck_prime.application.unit_conversion" in canonical

    for name in ("on_unit_changed", "_convert_to_base_unit", "_convert_from_base_unit", "_get_display_value"):
        assert name in canonical


def test_weighted_mobility_dialog_calls_application_use_cases_directly():
    source = (PACKAGE_ROOT / "presentation" / "dialogs" / "weighted_mobility_dialog.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = [
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]

    assert "seebeck_prime.application.use_cases" in imported_modules
    assert "seebeck_prime.legacy.ui.logic.weighted_mobility_logic" not in source


def test_plot_dialogs_use_canonical_presentation_utilities():
    source = (PACKAGE_ROOT / "presentation" / "dialogs" / "plot_settings_dialog.py").read_text(encoding="utf-8")
    assert "import seebeck_prime.presentation.ui_utils as ui_utils" in source
    assert "seebeck_prime.legacy.ui.logic.ui_utils" not in source


def test_presentation_does_not_import_domain_or_infrastructure():
    imports = _imports_in("presentation")
    forbidden = ("seebeck_prime.domain", "seebeck_prime.infrastructure", "seebeck_prime.legacy")
    assert not [name for name in imports if name.startswith(forbidden)]


def test_internal_package_import_graph_has_no_cycles():
    package_modules = {}
    for path in PACKAGE_ROOT.rglob("*.py"):
        relative = path.relative_to(PACKAGE_ROOT).with_suffix("")
        parts = relative.parts[:-1] if relative.name == "__init__" else relative.parts
        if parts == ("seebeck_prime",):  # the import-root shim itself
            module_name = "seebeck_prime"
        else:
            module_name = ".".join(("seebeck_prime", *parts))
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names if alias.name.startswith("seebeck_prime."))
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("seebeck_prime."):
                imported.add(node.module)
        package_modules[module_name] = imported

    graph = {name: set() for name in package_modules}
    for name, imports in package_modules.items():
        for imported in imports:
            candidate = imported
            while candidate not in package_modules and candidate.startswith("seebeck_prime."):
                candidate = candidate.rpartition(".")[0]
            if candidate in package_modules:
                graph[name].add(candidate)

    visiting = []
    visited = set()
    cycles = []

    def visit(name):
        if name in visiting:
            cycles.append(visiting[visiting.index(name):] + [name])
            return
        if name in visited:
            return
        visiting.append(name)
        for dependency in graph[name]:
            visit(dependency)
        visiting.pop()
        visited.add(name)

    for module_name in graph:
        visit(module_name)

    assert cycles == []


def test_gui_composition_does_not_own_science_or_infrastructure():
    imports = _imports_in("gui")
    forbidden = ("seebeck_prime.domain", "seebeck_prime.infrastructure", "seebeck_prime.legacy")
    assert not [name for name in imports if name.startswith(forbidden)]


def test_multi_sample_dialog_uses_application_without_legacy_core_import():
    source = (PACKAGE_ROOT / "presentation" / "dialogs" / "multi_sample_dialog.py").read_text(encoding="utf-8")
    assert "process_multi_sample_batch" in source
    assert "load_multi_sample_files(files)" in source
    assert "save_workbook(tables, path)" in source
    assert "seebeck_prime.legacy.core" not in source
    tree = ast.parse(source)
    direct_io = {"read_csv", "read_excel", "to_csv", "to_excel", "ExcelWriter"}
    calls = [
        node.func.attr for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert not direct_io.intersection(calls)
    assert "import pandas as pd" not in source


def test_clipboard_table_widget_has_one_presentation_implementation():
    canonical = (PACKAGE_ROOT / "presentation" / "table_widget.py").read_text(encoding="utf-8")
    assert "class ClipboardAwareTableWidget" in canonical

    for relative_path in ("gui/table.py",):
        adapter = (PACKAGE_ROOT / relative_path).read_text(encoding="utf-8")
        assert "seebeck_prime.presentation.table_widget" in adapter
        assert "class ClipboardAwareTableWidget" not in adapter

    main_window = (PACKAGE_ROOT / "gui" / "main_window.py").read_text(encoding="utf-8")
    assert "from seebeck_prime.presentation.table_widget import ClipboardAwareTableWidget" in main_window


def test_plot_data_helper_consumes_explicit_inputs():
    source = (PACKAGE_ROOT / "presentation" / "table_plot_data.py").read_text(encoding="utf-8")
    assert "def get_table_data(frame" in source
    assert "main_window.data" not in source
    assert "main_window.error_mode" not in source
    assert "main_window.table" not in source

    plot_source = (PACKAGE_ROOT / "presentation" / "main_table_plots.py").read_text(encoding="utf-8")
    assert "resolve_plot_context" in plot_source


def _calls_in(package_name, forbidden_names, forbidden_attributes):
    package_path = PACKAGE_ROOT / package_name
    offenders = []
    for source_path in package_path.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_names:
                offenders.append(f"{source_path.name}:open-style {node.func.id}")
            elif isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_attributes:
                offenders.append(f"{source_path.name}:{node.func.attr}")
    return offenders


def test_domain_performs_no_filesystem_operations():
    fs_calls = _calls_in(
        "domain",
        {"open"},
        {
            "read_text", "write_text", "read_bytes", "write_bytes",
            "open", "remove", "unlink", "mkdir", "rmdir", "rename",
            "listdir", "scandir", "walk", "getcwd", "makedirs",
        },
    )
    imports = _imports_in("domain")
    fs_modules = [name for name in imports if name.split(".")[0] in {"os", "pathlib", "shutil", "io"}]

    assert fs_calls == []
    assert fs_modules == []


def test_application_avoids_direct_filesystem_operations():
    fs_calls = _calls_in(
        "application",
        {"open"},
        {
            "read_text", "write_text", "read_bytes", "write_bytes",
            "open", "remove", "unlink", "mkdir", "rmdir", "rename",
            "listdir", "scandir", "walk", "getcwd", "makedirs",
        },
    )

    assert fs_calls == []


def test_infrastructure_has_no_file_dialog_or_gui_imports():
    imports = _imports_in("infrastructure")
    forbidden = ("PyQt6", "seebeck_prime.gui", "seebeck_prime.presentation", "seebeck_prime.legacy")
    assert not [name for name in imports if name.startswith(forbidden)]
