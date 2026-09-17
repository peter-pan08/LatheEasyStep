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

**Gekapselt seit 2026-09-17 (fuenfte Zustandskategorie, `view_state.py`).**
Zoom/Pan/Slice-Position/aktiver Ansichtsmodus/Legenden-Auf-Zu-Zustand lebten
als neun einzelne Attribute direkt auf `LathePreviewWidget`
(`preview_widget.py::__init__`): `_view_zoom`, `_view_pan`, `slice_z`,
`slice_enabled`, `view_mode`, `active_index`, `_legend_collapsed`,
`show_legend`, `status_messages`. Anders als bei `DirtyState`/
`ToolTableState`/`RuntimeState` (deren Aufrufstellen ueber viele Module
verteilt waren, deshalb per Umbenennung auf `handler._<name>.<feld>`
umgestellt) liegt die gesamte Nutzung dieser neun Felder innerhalb einer
einzigen Klasse (62 Fundstellen in `preview_widget.py` allein). Deshalb ein
anderer Adapter-Mechanismus: `LathePreviewWidget` haelt fuer jedes Feld
eine gleichnamige `@property`, die transparent an `self._view.<feld>`
delegiert - keine der 62 internen Nutzungsstellen musste angefasst werden,
und extern lesender/schreibender Code (mehrere Tests lesen/setzen
`widget.slice_z`/`widget.active_index`/`widget._view_zoom`/`widget.
_view_pan` direkt) funktioniert unveraendert weiter. `_view_pan` (vormals
ein `QtCore.QPointF`) wird in `ViewState` bewusst als zwei reine `float`-
Felder (`pan_x`/`pan_y`) gehalten, nicht als `QPointF` - damit `view_state.py`
komplett ohne Qt-Import auskommt und wie die anderen vier Zustandsklassen
ohne laufende Qt-Anwendung testbar bleibt; die `_view_pan`-Property baut
das `QPointF` erst an der Grenze zu Qt (die einzige echte Logik dieser
Kapselung, direkt per `test_view_zoom_and_pan_properties_delegate_to_
view_state` in `tests/test_preview_navigation.py` abgesichert).
5 bare `LathePreviewWidget.__new__(LathePreviewWidget)`-Testfixturen (4
Aufrufstellen in `tests/test_front_slice_profile.py`,
`tests/test_preview_widget_error_boundaries.py`,
`tests/test_slice_view_sync.py`) mussten um `widget._view = ViewState()`
ergaenzt werden - kleinere Testflaeche als bei `RuntimeState`, da nur diese
eine Widget-Klasse betroffen ist. 4 neue eigenstaendige Tests
(`tests/test_view_state.py`, Qt-frei) plus 1 neuer Property-Rundlauf-Test
in `tests/test_preview_navigation.py`.
Zusaetzlich existiert weiterhin impliziter Qt-Zustand ausserhalb jeder
eigenen Klasse: aktiver Reiter (`QTabWidget.currentIndex()`) und
ausgewaehlte Step-Zeile (`list_ops.currentRow()`, gekapselt hinter
`StepListView.selected_row()` in `ui_step_list_view.py` - das ist bereits
ein brauchbarer Adapter-Ansatz, bewusst nicht Teil dieser Kapselung).
Regressionsverifikation bestaetigt: eine absichtliche Verstuemmelung der
`_view_pan`-Setter-Property (Y-Komponente faelschlich aus `value.x()` statt
`value.y()`) wurde von mehreren Tests korrekt erkannt, darunter zwei
bereits vorher bestehende Navigationstests. 912 Stub-/109 Real-Qt-Tests
bestanden, Standalone-Panel sauber gestartet.

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

**Erste Handler-Kleber-Extraktion auf dieser Basis (2026-09-17):**
`_handle_add_operation()`/`_handle_delete_operation()` (Handler-Methoden,
~95/~54 Zeilen) nach `handle_add_operation(handler)`/
`handle_delete_operation(handler)` in `ui_flow.py` verschoben, Handler-
Methoden auf duenne einzeilige Delegations-Wrapper reduziert - gleiches
Muster wie zuvor bei `handle_move_up`/`handle_move_down`. Beim Lesen des
Methodenkoerpers fielen zwei weitere, bei der urspruenglichen
`RuntimeState`-Bestandsaufnahme uebersehene lose Reentranz-/Debounce-
Attribute auf (`_adding_operation`, `_last_add_operation_ts`) und wurden
direkt als `adding_operation`/`last_add_operation_ts` in `RuntimeState`
aufgenommen, statt sie als weitere lose Handler-Attribute stehen zu lassen.
`last_add_operation_ts` ist kein Reentranz-Flag, sondern ein 0,8s-Debounce-
Zeitstempel gegen sehr schnell aufeinanderfolgende, aber nicht ueberlappende
Klicks. Regressionsverifikation deckte eine echte Testluecke auf: der
bestehende Test `test_handle_add_operation_refreshes_stale_numbered_
comment_via_helper` (`tests/test_auto_comment_on_creation.py`) pruefte trotz
seines Namens nur den reinen `_looks_like_generated_step_comment()`-Helfer,
nie `handle_add_operation()` end-to-end - die absichtliche `if False:`-
Verstuemmelung der Kommentar-Auffrisch-Zeile wurde dadurch von keinem Test
erkannt. Behoben durch zwei neue End-zu-Ende-Tests
(`test_handle_add_operation_refreshes_stale_numbered_comment`,
`test_handle_add_operation_keeps_individual_comment`), die `handle_add_
operation()` tatsaechlich aufrufen; die Luecke war danach nachweislich
geschlossen (Korruption fuehrte zu einem Testfehlschlag, Ruecknahme wieder
zu 900/108 gruen). 900 Stub-/108 Real-Qt-Tests bestanden, Standalone-Panel
sauber gestartet.

**Zweite Handler-Kleber-Extraktion (2026-09-17):**
`_refresh_operation_list()` (~74 Zeilen) nach `refresh_operation_list
(handler, select_index=None)` in `ui_flow.py` verschoben, Handler-Methode
auf einen einzeiligen Delegations-Wrapper reduziert. Mehrere Tests
ueberschreiben `handler._refresh_operation_list` bereits als Instanz-Lambda
(`test_dirty_and_messages.py` u. a.) - das bleibt unveraendert moeglich, da
nur der Methodenkoerper, nicht die Aufruf-Signatur verschoben wurde.
Regressionsverifikation deckte einen zweiten, aber andersartigen Befund auf:
der `select_index is None`-Zweig (Zeile `target_idx = current`, "vorherige
Auswahl beibehalten") ist toter Code - jeder einzelne Aufrufer im gesamten
Projekt uebergibt einen expliziten `select_index`, nie `None`. Eine
Verstuemmelung genau dieser Zeile wurde folgerichtig von keinem Test
erkannt, weil kein Aufrufpfad sie je erreicht (anders als bei
`handle_add_operation()` oben, wo eine reale, erreichbare Regel ungetestet
war). Bewusst NICHT behoben - Entfernen des toten Zweigs waere eine
Verhaltensaenderung ueber reine Code-Verschiebung hinaus und gehoert nicht
in diese Extraktion; als moeglicher spaeterer Aufraeumpunkt vermerkt. Eine
zweite Korruption am tatsaechlich erreichten `select_index`-Zweig (`target_
idx = 0` statt `target_idx = select_index`) wurde dagegen korrekt von
`test_delete_last_step_selects_previous` (`tests/test_step_double_click.py`)
erkannt - das bestaetigt echte Regressionsabdeckung fuer den produktiv
genutzten Pfad. 900 Stub-/108 Real-Qt-Tests bestanden, Standalone-Panel
sauber gestartet.

**Dritte Handler-Kleber-Extraktion (2026-09-17):**
`_handle_param_change()` (~73 Zeilen, generischer Signal-Handler fuer alle
Parameter-Widgets: Spinbox/Combo/Checkbox/Lineedit) nach `handle_param_
change(handler)` in `ui_flow.py` verschoben, Handler-Methode auf einen
einzeiligen Delegations-Wrapper reduziert. In `ui_signals.py` per
`widget.valueChanged.connect(handler._handle_param_change)` u. ae. als
Qt-Slot verbunden - bleibt unveraendert funktionsfaehig, da nur der
Methodenkoerper, nicht die Bindung (weiterhin eine gebundene Methode auf
`handler`) verschoben wurde. Ein Audit-Test
(`test_current_text_occurrences_are_limited_to_audited_fallbacks`,
`tests/test_ui_visibility_guards.py`) fuehrt eine Positivliste erlaubter
`currentText()`-Fallback-Vorkommen je Datei; die beiden verschobenen Zeilen
wurden dort von `lathe_easystep_handler.py` nach `ui_flow.py` umgehaengt
(reine Ortsangabe, keine inhaltliche Aenderung der Pruefung).
Bestandsaufnahme vor der Extraktion ergab: kein einziger Test rief
`_handle_param_change()`/`handle_param_change()` bisher end-zu-end auf -
die vorhandenen zwei Tests pruefen nur, dass die Methode als Signal-Slot
verbunden wird, bzw. dass das *Befuellen* der Formularfelder keine Signale
ausloest (LES-025), nie die eigentliche Wert-Lese-/Dirty-Markier-Logik der
Methode selbst. Geschlossen durch drei neue End-zu-Ende-Tests in
`tests/test_dirty_and_messages.py`
(`test_handle_param_change_marks_operation_dirty_for_spinbox`,
`test_handle_param_change_marks_program_dirty_for_header`,
`test_handle_param_change_ignores_unnamed_widget`). Regressionsverifikation
bestaetigt: eine absichtliche Verstuemmelung der PROGRAM_HEADER-vs-Step-
Unterscheidung (`_mark_dirty(program=True)` vs. `_mark_dirty(operation_
index=idx)`) wurde vom neuen `test_handle_param_change_marks_program_dirty_
for_header` korrekt erkannt. 903 Stub-/108 Real-Qt-Tests bestanden,
Standalone-Panel sauber gestartet.

**Vierte Handler-Kleber-Extraktion (2026-09-17), anderes Ziel als bisher:**
`_populate_thread_standard_options()` (~46 Zeilen) nach
`populate_thread_standard_options(self)` verschoben - diesmal nicht nach
`ui_flow.py`, sondern in das bereits existierende `ui_thread.py`, das
bereits `apply_thread_preset(self, ...)` nach demselben Delegations-Muster
enthielt (Parametername dort bewusst `self` statt `handler`, um dem
bestehenden Dateistil zu folgen statt `ui_flow.py`s Konvention zu
uebernehmen). Die beiden ausschliesslich fuer diese Methode gebrauchten
Imports (`metric_thread_presets`, `trapezoidal_thread_presets`) aus
`lathe_easystep_handler.py` entfernt, da dort ungenutzt. Zur Einordnung:
`_ensure_contour_widgets()`/`_ensure_thread_widgets()` (reine Widget-Lookup-
Bootstrap-Methoden, aehnliche Groessenordnung) wurden bewusst NICHT
extrahiert - sie sind genau die Art "Bootstrap, Controller-Verbindungen"-
Code, die laut LES-052 Abschnitt 1 auf dem Handler bleiben soll; ihre
eigentliche offene Aufgabe ist der separate "einheitlicher Ladevertrag"-
Punkt, keine reine Verschiebung.
Bestandsaufnahme ergab wieder eine echte Testluecke: der vorhandene Test
`test_apply_thread_preset_applies_real_metric_preset`
(`tests/test_preview_safety_and_language.py`) baut das erwartete Combo-
itemData nur von Hand nach, ruft `_populate_thread_standard_options()`
selbst nie auf. Geschlossen durch zwei neue Tests
(`test_populate_thread_standard_options_builds_valid_preset_itemdata`,
`test_populate_thread_standard_options_is_idempotent`). Regressions-
verifikation reproduzierte gezielt den realen, im Nachbartest bereits
dokumentierten historischen Bug (Metric-Presets ohne `"label"`-Schluessel im
itemData) und wurde vom neuen Test korrekt erkannt. 905 Stub-/108 Real-Qt-
Tests bestanden, Standalone-Panel sauber gestartet (ein erster Lauf brach
ohne erkennbaren Fehler/Traceback beim Timeout von 20s knapp vor der
`DONE`-Zeile ab - reproduzierbar sauber bei 25s, keine Aenderung am Code
noetig, als Umgebungs-/Lastschwankung eingeordnet).

**Fuenfte Handler-Kleber-Extraktion (2026-09-17), kein Fall von "Kleber"
mehr:** `_tool_change_position_lines()` (~35 Zeilen, baut G-Code zum
Anfahren der Werkzeugwechselposition aus `header["xt"/"zt"/
"toolchange_coords"/"xt_absolute"/"zt_absolute"]`) griff ueberhaupt nicht
auf `self` zu - reine Funktion, die nur zufaellig als Handler-Methode
lebte. Nach `tool_change_position_lines(header)` in `ui_flow.py`
verschoben, ganz ohne Handler-Parameter. Einziger Aufrufer war bereits
`build_gcode_lines()` (selbst schon in `ui_flow.py`) - dessen zwei
Aufrufstellen rufen die Funktion jetzt direkt auf, nicht mehr ueber
`handler._tool_change_position_lines(...)`. `HandlerClass.
_tool_change_position_lines()` bleibt als duenner Delegations-Wrapper
bestehen (gleiche Vorsicht wie bei den bisherigen vier Extraktionen, falls
irgendwo ausserhalb dieses Moduls noch darauf zugegriffen wird - aktuell
nirgends der Fall).
Bestandsaufnahme deckte eine besonders bemerkenswerte Luecke auf: diese
G-Code-Pfad-Logik (Werkzeugwechsel-Anfahrposition, sicherheitsrelevant im
Sinne von CLAUDE.md) hatte ueberhaupt keine Tests - weder end-zu-end noch
direkt. `generate_program_gcode()` (`gcode_program.py`) implementiert die
gleiche work/machine/mixed-Logik ein zweites Mal, unabhaengig, fuer die
inline `"(Toolchange move)"`-Zeilen im Hauptprogramm - dessen Tests
(`test_toolchange_uses_work_or_machine_coords_explicitly` u. a.,
`tests/test_regression_contracts.py`) deckten nur diese zweite, separate
Implementierung ab, nie `_tool_change_position_lines()` selbst (das
`header_lines`/`footer_lines` in `program_settings` fuellt). Geschlossen
durch drei neue Tests in derselben Datei
(`test_tool_change_position_lines_work_and_machine_modes`,
`test_tool_change_position_lines_mixed_mode_moves_each_axis_separately`,
`test_tool_change_position_lines_defaults_without_explicit_coord_mode`).
Da es sich um eine reine Verschiebung ohne Verhaltensaenderung handelt, war
keine `rs274`-Nachverifikation noetig (CLAUDE.md verlangt sie fuer
Aenderungen an G-Code-Ausgabe/Fahrwegen, nicht fuer reine Code-Bewegung);
die neue Testabdeckung selbst schliesst aber eine bisher unbeaufsichtigte
Luecke in genau diesem Bereich. Regressionsverifikation bestaetigt: eine
absichtliche Verstuemmelung des mixed-Zweigs (fehlendes `G53`-Praefix fuer
die nicht-absolute X-Achse) wurde korrekt erkannt. 908 Stub-/108 Real-Qt-
Tests bestanden, Standalone-Panel sauber gestartet.

### Zusammenfassung fuer die eigentliche Umsetzung

Stand 2026-09-17: Alle sechs Zustandskategorien sind jetzt gekapselt -
LES-052 Abschnitt 1s erster Punkt ist damit vollstaendig abgeschlossen.
Vier Kategorien lebten urspruenglich als unbenannte Attribute direkt auf
Handler oder Widget, gelesen/geschrieben von freien Funktionen oder Code in
mehreren Modulen - genau das "heimlicher Zustandsbesitzer"-Muster, das
LES-052 beenden soll: `DirtyState`, `ToolTableState`, `RuntimeState`
(zweiter bis vierter LES-052-Baustein, alle drei auf dem Handler) und
zuletzt `ViewState` (fuenfter Baustein, auf `LathePreviewWidget`). Die
ersten drei nach demselben Muster: Qt-freie Klasse (Methoden bei
`DirtyState`/`ToolTableState`, bei `RuntimeState` reine Felder, da die
Reentranz-Logik bewusst an den Aufrufstellen blieb statt in einer neuen
`guard()`-Abstraktion), duenne `ui_*.py`-Adapter mit unveraenderter
Signatur, damit bestehende Aufrufstellen nur den Attributzugriff, nicht
ihre Struktur, aendern mussten. `ViewState` weicht davon bewusst ab: da
alle 62 Nutzungsstellen innerhalb einer einzigen Klasse liegen (statt ueber
viele Module verteilt), delegieren `@property`-Deskriptoren transparent an
`self._view.<feld>` - keine einzige interne Nutzungsstelle musste
umbenannt werden. Bei mehreren Umsetzungen kamen zusaetzliche, bei der
ersten Bestandsaufnahme uebersehene lose Attribute zum Vorschein
(`_loaded_tools`/`_missing_iso_tools` bei `ToolTableState`; die
tatsaechliche Groesse von `RuntimeState` selbst kam erst bei der
`DirtyState`-Kapselung ans Licht) - ein Hinweis, dass die Bestandsaufnahme
selbst nur der erste, nicht der letzte Blick auf den tatsaechlichen Code
sein sollte. `ProgramState`/`OperationState` und `MotionState`/
`SpindleState` waren schon vorher sauber gekapselt und dienten durchgehend
als Vorbild. Auf der jetzt vollstaendigen Zustandstrennung aufbauend wurden
bereits sechs Handler-Kleber-Methoden (fuenf Extraktionsschritte) nach
`ui_flow.py`/`ui_thread.py` verschoben (`handle_add_operation`,
`handle_delete_operation`,
`refresh_operation_list`, `handle_param_change`,
`populate_thread_standard_options`, `tool_change_position_lines`); reine
Widget-Lookup-Bootstrap-Methoden (`_ensure_contour_widgets()`,
`_ensure_thread_widgets()`) blieben bewusst auf dem Handler. Die naechsten
LES-052-Schritte (Abschnitt 1s verbleibende Punkte: einheitlicher
Ladevertrag, Views ohne eigenen Fachzustand) bauen auf dieser Trennung auf.
