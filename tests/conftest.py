import sys
import types


def _install_qt_stubs():
    if "qtpy" in sys.modules and "qtvcp.core" in sys.modules:
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

    QtCore = types.SimpleNamespace(
        Qt=qt_enum,
        QObject=_Dummy,
        QTimer=_DummyTimer,
        QPointF=_Dummy,
        QLineF=_Dummy,
        QDir=_DummyDir,
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
    _install_qt_stubs()
