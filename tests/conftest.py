import sys
import types
import os
import pytest
from pathlib import Path

REAL_QT_TESTS = {
    "test_program_save_real_qt.py",
    "test_dirty_state_signal_blocking.py", "test_per_operation_spindle_mode_ui.py",
    "test_preview_widget_paint_no_crash.py", "test_slice_strategy_ui_roundtrip.py",
    "test_split_ui_loader.py", "test_tool_combo_selection.py",
    "test_ui_static_translation_split_tabs.py",
}


def pytest_addoption(parser):
    parser.addoption("--qt-mode", choices=("stub", "real"), default="stub",
                     help="Isolate stub tests from real PyQt5 tests (default: stub).")


def pytest_ignore_collect(collection_path, config):
    if collection_path.suffix != ".py" or not collection_path.name.startswith("test_"):
        return None
    is_real = collection_path.name in REAL_QT_TESTS
    return is_real != (config.getoption("--qt-mode") == "real")

def _clear_stale_qt_modules():
    for name in list(sys.modules):
        if name in {"qtpy", "qtvcp", "qtvcp.core"} or name.startswith("qtpy.") or name.startswith("qtvcp.") or name.startswith("lathe_easystep"):
            sys.modules.pop(name, None)


def _install_qt_stubs():
    if "qtpy" in sys.modules and "qtvcp.core" in sys.modules:
        qtpy = sys.modules["qtpy"]
        if hasattr(qtpy, "QtCore"):
            sys.modules.setdefault("qtpy.QtCore", qtpy.QtCore)
        if hasattr(qtpy, "QtGui"):
            sys.modules.setdefault("qtpy.QtGui", qtpy.QtGui)
        if hasattr(qtpy, "QtWidgets"):
            sys.modules.setdefault("qtpy.QtWidgets", qtpy.QtWidgets)
        return

    # Qt Enum-Ersatz
    qt_enum = types.SimpleNamespace(
        UserRole=0,
        MatchFixedString=0,
        FindChildrenRecursively=0,
        ItemIsSelectable=1,
        ItemIsEnabled=2,
        ItemIsEditable=4,
    )

    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            return None

        def __getattr__(self, _name):
            return _Dummy()

    class _DummyTimer(_Dummy):
        @staticmethod
        def singleShot(*args, **kwargs):
            return None

    class _DummyDir(_Dummy):
        @staticmethod
        def homePath():
            return "/tmp"

    class _DummySettings:
        def __init__(self, *args, **kwargs):
            self._values = {}

        def value(self, key, default=None, type=None):
            value = self._values.get(key, default)
            return type(value) if type is not None and value is not None else value

        def setValue(self, key, value):
            self._values[key] = value

    QtCore = types.SimpleNamespace(
        QSettings=_DummySettings,
        Qt=qt_enum,
        QObject=_Dummy,
        QTimer=_DummyTimer,
        QPointF=_Dummy,
        QLineF=_Dummy,
        QDir=_DummyDir,
        Signal=_Dummy,  # Add Signal mock
    )

    class _DummyPainter(_Dummy):
        def setPen(self, *args, **kwargs):
            pass

        def setFont(self, *args, **kwargs):
            pass

    QtGui = types.SimpleNamespace(
        QColor=_Dummy,
        QPainter=_DummyPainter,
        QPen=_Dummy,
        QFont=lambda *args, **kwargs: None,
        QPolygonF=list,
    )

    class _DummyWidget(_Dummy):
        def setVisible(self, *args, **kwargs):
            pass

        def setEnabled(self, *args, **kwargs):
            pass

        def blockSignals(self, *args, **kwargs):
            pass

        def setCurrentIndex(self, *args, **kwargs):
            pass

        def currentIndex(self, *args, **kwargs):
            return 0

        def currentText(self, *args, **kwargs):
            return ""

        def setText(self, *args, **kwargs):
            pass

        def text(self, *args, **kwargs):
            return ""

        def value(self, *args, **kwargs):
            return 0

        def setValue(self, *args, **kwargs):
            pass

        def isChecked(self, *args, **kwargs):
            return False

        def setChecked(self, *args, **kwargs):
            pass

        def itemData(self, *args, **kwargs):
            return None

        def findText(self, *args, **kwargs):
            return 0

        def addItem(self, *args, **kwargs):
            pass

        def insertRow(self, *args, **kwargs):
            pass

        def rowCount(self, *args, **kwargs):
            return 0

        def setRowCount(self, *args, **kwargs):
            pass

        def setItem(self, *args, **kwargs):
            pass

        def item(self, *args, **kwargs):
            return None

        def setCurrentRow(self, *args, **kwargs):
            pass

        def addItems(self, *args, **kwargs):
            pass

        def clear(self, *args, **kwargs):
            pass

        def count(self, *args, **kwargs):
            return 0

        def setCurrentText(self, *args, **kwargs):
            pass

        def findChild(self, *args, **kwargs):
            return None

    class _DummyMessageBox:
        @staticmethod
        def information(*args, **kwargs):
            return None

        @staticmethod
        def critical(*args, **kwargs):
            return None

        @staticmethod
        def warning(*args, **kwargs):
            return None

    QtWidgets = types.SimpleNamespace(
        QWidget=_DummyWidget,
        QMessageBox=_DummyMessageBox,
        QTableWidgetItem=_DummyWidget,
        QAbstractButton=_DummyWidget,
        QComboBox=_DummyWidget,
        QSpinBox=_DummyWidget,
        QDoubleSpinBox=_DummyWidget,
        QListWidget=_DummyWidget,
        QTableWidget=_DummyWidget,
        QTabWidget=_DummyWidget,
    )

    qtpy = types.SimpleNamespace(QtCore=QtCore, QtGui=QtGui, QtWidgets=QtWidgets)
    sys.modules["qtpy"] = qtpy
    sys.modules["qtpy.QtCore"] = QtCore
    sys.modules["qtpy.QtGui"] = QtGui
    sys.modules["qtpy.QtWidgets"] = QtWidgets

    # qtvcp-Stub
    qtvcp = types.ModuleType("qtvcp")
    core = types.ModuleType("qtvcp.core")

    class _DummyAction:
        CALLBACK_OPEN_PROGRAM = None

    core.Action = _DummyAction
    sys.modules["qtvcp"] = qtvcp
    sys.modules["qtvcp.core"] = core


def pytest_configure(config):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    if config.getoption("--qt-mode") == "real":
        import pytest
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PyQt5 import QtWidgets
            import qtpy
        except ImportError as exc:
            raise pytest.UsageError("Real-Qt tests require PyQt5 and qtpy.") from exc
        # Real widgets, but no machine connection in UI regression tests.
        qtvcp = types.ModuleType("qtvcp")
        core = types.ModuleType("qtvcp.core")
        core.Action = type("Action", (), {"CALLBACK_OPEN_PROGRAM": None})
        sys.modules["qtvcp"] = qtvcp
        sys.modules["qtvcp.core"] = core
        config._lathe_qapplication = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    else:
        _install_qt_stubs()


@pytest.fixture(autouse=True)
def restore_qt_namespaces(request):
    """Legacy tests assign attributes directly; contain those changes per test."""
    names = ("qtpy", "qtpy.QtCore", "qtpy.QtGui", "qtpy.QtWidgets", "qtvcp", "qtvcp.core")
    modules = {name: sys.modules[name] for name in names if name in sys.modules}
    snapshots = {name: dict(vars(module)) for name, module in modules.items()}
    yield
    for name, module in modules.items():
        sys.modules[name] = module
        namespace = vars(module)
        for key in set(namespace) - snapshots[name].keys():
            del namespace[key]
        namespace.update(snapshots[name])
