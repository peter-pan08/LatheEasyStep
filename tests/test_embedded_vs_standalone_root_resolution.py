"""LES-035: Real-Qt-Smoke-Test fuer Standalone- und Embedded-Start.

Realer Vergleich 2026-09-14 (Standalone `qtvcp -c easystep -u ...` vs.
QtDragon-SIM mit eingebettetem Panel unter dem UTILS-Tab): beide Startarten
schliessen `_finalize_ui_ready` nach einem Durchlauf ab, loesen dieselben
167/169 Tooltip-Namen auf (dieselben zwei fehlenden: `program_spindle_mode`,
`program_preview_warnings`), laden dieselbe Werkzeugtabelle vom selben
Pfad. Standalone ist deutlich schneller (~1,7s vs. ~8,8s) - dieser
Unterschied liegt an `_auto_load_tool_table()`/`QSettings()` (embedded
teilt sich QtDragons groessere Settings-Datei), nicht an einem Bug, und
ist bewusst nicht Teil dieses Tests (das ist LES-027s Zustaendigkeit,
nicht LES-035s Paritaets-Frage).

Dieser Test deckt strukturell ab, was der reale Vergleich fuer die
Panel-Root-Erkennung zeigte: `_pick_best_root()` (`widget_resolver.py`)
muss im eingebetteten Fall (unser "easystep"-Panel haengt unter einem
generisch benannten Host-Fenster mit unrelatierten Geschwister-Widgets)
GENAU unser Panel liefern - weder das Host-Fenster selbst noch einen
Geschwister-Widget des Hosts (LES-035-Punkt "keine globalen Host-Widgets
binden")."""

from PyQt5 import QtWidgets

from lathe_easystep.widget_resolver import _pick_best_root

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _build_panel_subtree(parent=None):
    panel = QtWidgets.QWidget(parent)
    panel.setObjectName("easystep")
    tab_params = QtWidgets.QWidget(panel)
    tab_params.setObjectName("tabParams")
    list_ops = QtWidgets.QListWidget(panel)
    list_ops.setObjectName("listOperations")
    return panel


def test_standalone_root_is_the_panel_itself():
    """Standalone: `easystep` ist das oberste Fenster, kein Host drumherum."""
    panel = _build_panel_subtree(parent=None)
    assert _pick_best_root([panel]) is panel


def test_embedded_root_is_our_panel_not_the_host_window():
    """Embedded: `easystep` haengt unter einem generisch benannten
    Host-Fenster ("MainWindow", wie QtDragon) neben einem unrelatierten
    Geschwister-Widget. _pick_best_root() muss trotzdem GENAU unser Panel
    liefern, nicht das Host-Fenster (das waere zu breit - jede
    Widget-Suche wuerde dann potenziell im ganzen Host-Baum landen)."""
    main_window = QtWidgets.QMainWindow()
    main_window.setObjectName("MainWindow")
    host_sidebar = QtWidgets.QWidget(main_window)
    host_sidebar.setObjectName("host_sidebar_unrelated")
    QtWidgets.QListWidget(host_sidebar).setObjectName("listOperations")  # Namenskollision, gehoert NICHT zu uns
    panel = _build_panel_subtree(parent=main_window)

    root = _pick_best_root([panel])
    assert root is panel
    assert root is not main_window
    assert root is not host_sidebar


def test_embedded_root_resolution_does_not_return_unrelated_host_sibling():
    """Wird nur der unrelatierte Geschwister-Zweig als Kandidat uebergeben
    (z.B. weil ein anderer Lookup-Pfad zufaellig dort zuerst sucht), darf
    das NICHT als unser Panel durchgehen, obwohl er zufaellig ebenfalls
    ein "listOperations"-Widget enthaelt (Namenskollision) - ihm fehlt
    "tabParams", die zweite Bedingung von `_looks_like_panel_widget()`."""
    main_window = QtWidgets.QMainWindow()
    main_window.setObjectName("MainWindow")
    host_sidebar = QtWidgets.QWidget(main_window)
    host_sidebar.setObjectName("host_sidebar_unrelated")
    QtWidgets.QListWidget(host_sidebar).setObjectName("listOperations")
    _build_panel_subtree(parent=main_window)

    root = _pick_best_root([host_sidebar])
    assert root is not host_sidebar
