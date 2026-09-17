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

**Nicht gekapselt.** Der Zustand ist ein rohes `handler.tools: Dict[int,
Tool]` (`Tool` selbst ist ein sauberes `frozen`-Dataclass in `tools.py`,
nur der Container drumherum fehlt) plus der lose Widget-Text
`handler.tool_table_path`. Beides wird direkt von freien Funktionen in
`ui_tools.py` gesetzt (`handler.tools = tools` an mindestens drei Stellen).
`parse_tool_table()` (`tools.py`) liefert Parse-Warnungen (fehlendes ISO,
Duplikate) bereits zurueck, aber nichts haelt sie ueber den Ladevorgang
hinaus fest - sie werden geloggt, nicht als Teil des Zustands gefuehrt.
Deckt sich mit LES-052 Abschnitt 5 ("Werkzeugtabelle als eigene Domaene
kapseln").

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

**Nicht gekapselt - groesserer Umfang als zunaechst erfasst.** Bei der
DirtyState-Kapselung faellt auf, dass `lathe_easystep_handler.py`s
`__init__` allein acht weitere Reentranz-/Ladezustands-Flags direkt auf
`self` setzt: `_loading_step`, `_deleting`, `_saving_step`,
`_saving_changes`, `_moving_up`, `_moving_down`, `_generating_gcode`,
`_creating_new_program` - zusaetzlich zu `_ui_loading` (unterdrueckt
Signal-Reaktionen waehrend ein Step/Programm in die Maske geschrieben wird,
damit das Zurueckschreiben nicht selbst als Nutzeraenderung/Dirty-
Markierung gewertet wird - gesetzt in `ui_selection.py`, gelesen
zusaetzlich in `ui_visibility.py` und im
Handler). Bewusst NICHT in dieser Kategorie: `MotionState`/`SpindleState`
(`motion_state.py`, LES-022) - das sind reine, lokale Parameter innerhalb
eines einzelnen `generate_program_gcode()`-Laufs (Werkzeug-Rueckzugs-
position/CSS-Modalzustand waehrend der Erzeugung), nicht panelweiter
Laufzeitzustand; sie werden nicht auf dem Handler gehalten und sind bereits
ein brauchbares Vorbild fuer sauber gekapselten Zustand.

### Zusammenfassung fuer die eigentliche Umsetzung

Stand 2026-09-16: Drei der sechs Kategorien lebten urspruenglich
ausschliesslich als unbenannte Attribute auf dem Handler, direkt gelesen/
geschrieben von freien Funktionen in mehreren Modulen - genau das "Handler
als heimlicher Zustandsbesitzer"-Muster, das LES-052 Abschnitt 1 beenden
soll. `DirtyState` ist davon jetzt gekapselt (siehe oben, zweiter
LES-052-Baustein) - die dringendste der drei, wegen der real aufgetretenen
Bugs durch Index-Drift. `ToolTableState` und `RuntimeState` (jetzt mit
neun statt zwei bekannten Flags) sind es noch nicht. `ProgramState`/
`OperationState` (bereits Klassen mit Methoden) und `MotionState`/
`SpindleState` (bereits lokale, nicht handler-gebundene Werte) zeigen,
dass das Projekt das Zielmuster an mehreren Stellen schon beherrscht - die
Umsetzung fuer die beiden verbleibenden Kategorien kann sich daran
orientieren, insbesondere am `DirtyState`-Muster: Qt-freie Klasse mit
Methoden statt loser Attribute, duenne `ui_*.py`-Adapter mit unveraenderter
Signatur, damit bestehende Aufrufstellen nicht angefasst werden muessen.
