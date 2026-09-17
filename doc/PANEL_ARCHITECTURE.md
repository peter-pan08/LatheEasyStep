# Panel-Architektur und Besitzgrenzen

Stand: 2026-09-15, erster LES-051-Baustein.

## Abhaengigkeitsrichtung

1. Fachobjekte (`ProgramModel`, `Operation`, `Tool`) besitzen ausschliesslich
   Bearbeitungs- und Werkzeugdaten. Sie kennen weder Qt-Widgets noch Dateien
   eines Darstellungs-Sets.
2. Qt-freie Zeichenplaene und Darstellungsanfragen leiten aus Fachwerten nur
   die fuer eine View notwendigen Werte ab. Sie duerfen das Fachmodell nicht
   veraendern.
3. Ressourcen-Provider loesen logische Darstellungsanfragen innerhalb eines
   Theme-Verzeichnisses auf. Pfad, Format und Fallback bleiben Eigentum dieser
   Schicht und werden nicht gespeichert.
4. Qt-Views weisen Farben, Stifte, Bilder und Interaktion zu. Sie melden
   Benutzeraktionen an Controllerfunktionen, sind aber keine zweite Wahrheit
   fuer Programm- oder Werkzeugdaten.
5. Der Handler verbindet Bootstrap, LinuxCNC/QTVCP und die Controllergrenzen.
   Neue Fachregeln oder Ressourcenauflosung gehoeren nicht in den Handler.

Damit gilt die Richtung `Fachmodell -> Zeichenplan/Anfrage -> Provider -> View`.
Rueckwaerts duerfen nur definierte Benutzerereignisse laufen, niemals Qt- oder
Ressourcenobjekte in das Fachmodell.

## Werkzeugdarstellung

`ToolVisualRequest` beschreibt Familie, Seite, Plattenform und optionalen
ISO-Code ohne Bezug zum `Tool`-Objekt. `ToolVisualProvider` sucht dazu einen
logischen Eintrag in einem austauschbaren Manifest. Unterstuetzt werden derzeit
PNG und SVG. Absolute Pfade und Pfade ausserhalb des Theme-Verzeichnisses sind
untersagt.

Ohne passenden Eintrag bleibt die vorhandene prozedurale Darstellung aktiv.
Ist ein konfigurierter Eintrag ungueltig oder fehlt die Datei, liefert der
Provider denselben Fallback plus strukturierte Diagnose. Der Qt-Adapter zeigt
diese Diagnose als Warnmarkierung und im Log, ohne Operation, Werkzeug, G-Code
oder Dirty-State zu veraendern. Die Wahl und Lebensdauer eines konkreten Themes
bleibt ausserhalb des Fachmodells und wird in einem weiteren Paket ergaenzt.

## Zustandsmodell (LES-052, Bestandsaufnahme)

Stand: 2026-09-16. Diese Bestandsaufnahme beschreibt, wo die sechs in
LES-052 genannten Zustandskategorien HEUTE tatsaechlich leben, und ist die
Voraussetzung fuer die eigentliche Umsetzung - LES-052 selbst verlangt
ausdruecklich, die Grenzen vor dem Umbau festzulegen. Kein Code wurde fuer
diese Bestandsaufnahme veraendert.

### `ProgramState` / `OperationState`

Bereits das best-eingegrenzte Beispiel im Projekt. `ProgramModel` und
`Operation` (`model.py`) kapseln Operationsliste, Programmkopf-Settings und
Geometrie-/G-Code-Erzeugung hinter Methoden (`add_operation()`,
`update_geometry()`, `generate_gcode()`); Aufrufer mutieren keine internen
Felder direkt. Einziger Schoenheitsfehler: `program_settings` ist ein
untypisiertes `Dict[str, object]`, kein eigener Typ - fuer die anstehende
Dateiformat-Versionierung (LES-053) relevant, aber kein Ownership-Problem.

### `ToolTableState`

**Gekapselt seit 2026-09-17 (dritter LES-052-Baustein).** War ein rohes
`handler.tools: Dict[int, Tool]` (`Tool` selbst war schon ein sauberes
`frozen`-Dataclass in `tools.py`, nur der Container drumherum fehlte) plus
zwei WEITERE lose Attribute, die bei der Bestandsaufnahme zunaechst
uebersehen wurden: `handler._loaded_tools` (Cache der zuletzt geladenen,
NICHT-leeren Tabelle - fuer das Nachbefuellen von erst spaeter/lazy
auftauchenden Werkzeug-Combo-Widgets) und `handler._missing_iso_tools`
(die von `parse_tool_table()` gelieferten ISO-Warnungen, geschrieben, aber
nirgends gelesen - schon vor der Kapselung totes Feld, hier bewusst nicht
"repariert", nur mituebernommen). `ToolTableState` (`tool_table_state.py`,
Qt-frei) buendelt alle drei in `handler._tool_table`; `set_tools()`
kapselt exakt die bisherige "leere Tabelle ueberschreibt den Cache nicht"-
Logik aus `ui_tools.py::populate_tool_combos()`. Der Widget-Text
`handler.tool_table_path` bleibt bewusst aussen vor - das ist Qt-View-
Zustand (der angezeigte Dateipfad), keine Fachdaten. 4 neue eigenstaendige
Tests (`tests/test_tool_table_state.py`), per absichtlich entferntem
Leer-Dict-Schutz als echte Regression verifiziert. 895 Stub-/108 Real-Qt-
Tests bestanden; Standalone-Panel-Log bestaetigt den echten Ladepfad
(`tool.tbl` automatisch geladen, Combos befuellt).

### `ViewState`

**Teilweise gekapselt, aber ungetypt.** Zoom/Pan/Slice-Position/aktiver
Ansichtsmodus/Legenden-Auf-Zu-Zustand leben als einzelne Attribute direkt
auf `LathePreviewWidget` (`preview_widget.py::__init__`): `_view_zoom`,
`_view_pan`, `slice_z`, `slice_enabled`, `view_mode`, `active_index`,
`_legend_collapsed`, `show_legend`, `status_messages`. Das ist insofern
unproblematisch, als es reiner Anzeigezustand ist, der nachweislich nie in
Operationsdaten oder G-Code zurueckfliesst (mehrfach per Test belegt, siehe
LES-051-Eintraege). Zusaetzlich existiert impliziter Qt-Zustand ausserhalb
jeder eigenen Klasse: aktiver Reiter (`QTabWidget.currentIndex()`) und
ausgewaehlte Step-Zeile (`list_ops.currentRow()`, gekapselt hinter
`StepListView.selected_row()` in `ui_step_list_view.py` - das ist bereits
ein brauchbarer Adapter-Ansatz). Fehlt: ein benannter `ViewState`-Typ, der
diese Werte buendelt, statt sie als Attributliste auf einem Qt-Widget zu
fuehren.

### `DirtyState`

**Gekapselt seit 2026-09-16 (zweiter LES-052-Baustein).** War der
komplexeste und riskanteste Fall: fuenf einzelne Attribute direkt auf dem
Handler, gelesen und geschrieben von freien Funktionen in acht Modulen.
`DirtyState` (`dirty_state.py`, Qt-frei) buendelt jetzt `operation_indices`,
`program_dirty`, `program_header_dirty`, `program_structure_dirty` und
`warning_suppressed` in einem Objekt (`handler._dirty`); `ui_dirty.py`s
freie Funktionen bleiben als duenne Adapter bestehen (Signatur unveraendert,
Koerper delegiert an Methoden auf `DirtyState`), damit alle Aufrufstellen
in `ui_flow.py`/`ui_persistence.py`/`ui_selection.py`/`lathe_easystep_
handler.py` unveraendert bleiben konnten - nur der direkte Attributzugriff
wurde auf `handler._dirty.<feld>` umgestellt. Die Index-Nachzieh-Methoden
(`reindex_after_removal()`/`reindex_after_insert()`/`swap_indices()`) tragen
weiterhin den Hinweis auf den SICHERHEITSFUND 2026-09-13 (ein dirty-Flag
"wanderte" beim Verschieben auf den falschen Nachbar-Step) - sie leben jetzt
in einer eigenstaendig testbaren Klasse (`tests/test_dirty_state.py`, 14
neue Tests) statt in acht Aufrufstellen. Per absichtlich entfernter
Nachzieh-Arithmetik als echte Regression verifiziert (zweimal: einmal fuer
`reindex_after_removal()`, einmal fuer die abgeleitete `program_dirty`-Logik
in `clear_program()`). 891 Stub-/108 Real-Qt-Tests bestanden, Standalone-
Panel sauber gestartet.

### `RuntimeState`

**Gekapselt seit 2026-09-17 (vierter LES-052-Baustein, letzte der sechs
Kategorien).** Neun lose Reentranz-/Ladezustands-Flags direkt auf dem
Handler (`_loading_step`, `_deleting`, `_saving_step`, `_saving_changes`,
`_moving_up`, `_moving_down`, `_generating_gcode`, `_creating_new_program`,
`_ui_loading`) sind jetzt `RuntimeState` (`runtime_state.py`, Qt-frei),
gehalten als `handler._runtime`. Acht der neun Felder folgen demselben
Reentranz-Muster (`if state.x: return` / `state.x = True` / im `finally`
`state.x = False`) an neun praktisch identischen Aufrufstellen in
`ui_flow.py`/`ui_persistence.py`/`lathe_easystep_handler.py` - bewusst
NICHT zu einer `guard()`-Kontextmanager-Abstraktion zusammengefasst, da das
eine echte Struktur-/Verhaltensaenderung an den Aufrufstellen waere, nicht
nur eine Verschiebung des Speicherorts (siehe `runtime_state.py`-Docstring).
`ui_loading` ist semantisch anders (unterdrueckt Signal-Reaktionen waehrend
programmatischen Zurueckschreibens ins Formular, gelesen in
`ui_selection.py`/`ui_visibility.py`/Handler) und war zuvor NIE explizit
initialisiert (nur ueber `getattr(handler, "_ui_loading", False)` defensiv
gelesen) - jetzt wie die anderen acht ein regulaeres `RuntimeState`-Feld
mit Default `False`. Grosse Testflaeche: 12 Testdateien mit minimalen/
bare Test-Handlern (`object.__new__(HandlerClass)`, `SimpleNamespace`)
mussten um `handler._runtime = RuntimeState()` ergaenzt werden - deutlich
mehr als bei `DirtyState`/`ToolTableState`, weil `_ui_loading` bisher
ueberall defensiv gelesen wurde und dadurch auf fehlenden Testattributen
nie sichtbar auffiel. Bewusst NICHT in dieser Kategorie: `MotionState`/
`SpindleState` (`motion_state.py`, LES-022) - das sind reine, lokale
Parameter innerhalb eines einzelnen `generate_program_gcode()`-Laufs
(Werkzeug-Rueckzugsposition/CSS-Modalzustand waehrend der Erzeugung),
nicht panelweiter Laufzeitzustand; sie werden nicht auf dem Handler
gehalten und waren bereits vorher ein brauchbares Vorbild. 3 neue
eigenstaendige Tests (`tests/test_runtime_state.py`) - anders als bei
`DirtyState`/`ToolTableState` ohne Regressionsverifikation per absichtlich
entfernter Logik, da die Klasse selbst keine Methoden/Ableitungslogik
enthaelt (alles reentranz-relevante Verhalten bleibt an den Aufrufstellen,
unveraendert durch diese Kapselung). 898 Stub-/108 Real-Qt-Tests bestanden,
Standalone-Panel sauber gestartet.

### Zusammenfassung fuer die eigentliche Umsetzung

Stand 2026-09-17: Alle sechs Zustandskategorien sind jetzt gekapselt -
LES-052 Abschnitt 1s erster Punkt ist damit vollstaendig abgeschlossen.
Drei Kategorien lebten urspruenglich ausschliesslich als unbenannte
Attribute auf dem Handler, direkt gelesen/geschrieben von freien Funktionen
in mehreren Modulen - genau das "Handler als heimlicher Zustandsbesitzer"-
Muster, das LES-052 beenden soll: `DirtyState`, `ToolTableState` und
zuletzt `RuntimeState` (zweiter bis vierter LES-052-Baustein). Alle drei
nach demselben Muster: Qt-freie Klasse (Methoden bei `DirtyState`/
`ToolTableState`, bei `RuntimeState` reine Felder, da die Reentranz-Logik
bewusst an den Aufrufstellen blieb statt in einer neuen `guard()`-
Abstraktion), duenne `ui_*.py`-Adapter mit unveraenderter Signatur, damit
bestehende Aufrufstellen nur den Attributzugriff, nicht ihre Struktur,
aendern mussten. Bei allen drei Umsetzungen kamen zusaetzliche, bei der
ersten Bestandsaufnahme uebersehene lose Attribute zum Vorschein
(`_loaded_tools`/`_missing_iso_tools` bei `ToolTableState`; die
tatsaechliche Groesse von `RuntimeState` selbst kam erst bei der
`DirtyState`-Kapselung ans Licht) - ein Hinweis, dass die Bestandsaufnahme
selbst nur der erste, nicht der letzte Blick auf den tatsaechlichen Code
sein sollte. `ProgramState`/`OperationState` und `MotionState`/
`SpindleState` waren schon vorher sauber gekapselt und dienten durchgehend
als Vorbild fuer die drei Umsetzungen. Die naechsten LES-052-Schritte
(Abschnitt 1s verbleibende Punkte: Handler auf Bootstrap begrenzen,
einheitlicher Ladevertrag, Views ohne eigenen Fachzustand) bauen auf dieser
jetzt vollstaendigen Zustandstrennung auf.
