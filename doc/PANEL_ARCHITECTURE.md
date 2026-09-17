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

**Nachtrag (2026-09-17, nach der `ViewState`-Kapselung):** der oben als
"moeglicher spaeterer Aufraeumpunkt" vermerkte tote Zweig ist jetzt
entfernt - `select_index` ist ein regulaerer Pflichtparameter (keine
`int | None = None`-Signatur mehr) auf der freien Funktion und dem
Handler-Wrapper, die ebenfalls unbenutzt gewordene `current = lst.
currentRow()`-Zeile mit entfernt. Reine Aufraeumarbeit ohne
Verhaltensaenderung, volle Suite (912/109) bestaetigt das.

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

## Ladevertrag: Standalone und Embedded (LES-052, Bestandsaufnahme 2026-09-17)

Reine Bestandsaufnahme, kein Code veraendert. Bestaetigt den tatsaechlichen
Ladeablauf gegen den Code (`lathe_easystep_handler.py`, `ui_lifecycle.py`,
`ui_split.py`, `ui_widget_lookup.py`, `ui_signals.py`), als Grundlage fuer
den noch offenen Punkt "einheitlicher Ladevertrag ... Laden muss idempotent
und in einer nachvollziehbaren Reihenfolge erfolgen" (`TODO.md`).

### Kein expliziter Standalone-/Embedded-Modus

Es gibt keine einzige `if standalone:`/`if embedded:`-Weiche im Code.
QtVCP ruft in beiden Faellen identisch `get_handlers()` ->
`HandlerClass(halcomp, widgets, paths)` auf. Die Unterscheidung ist rein
strukturell: `__init__` (`lathe_easystep_handler.py:874-981`) sucht den
Panel-Root per Eltern-Kette und `findChild()` nach bekannten Namen
(`PANEL_WIDGET_NAMES`, `ui_registry.py`) bzw. `_looks_like_panel_widget()`.
Letztere prueft bewusst `listOperations` ODER `stepListPanel` UND
`tabParams`, weil `listOperations` selbst erst nach dem Laden der
UI-Fragmente existiert - ein Check nur auf `listOperations` wuerde den
Panel-Root waehrend des fruehen Embedded-Host-Suchfensters verfehlen. Der
einzige praktische Unterschied ist Timing: Standalone laedt die `.ui`-Datei
synchron vor `initialized__()`, alles ist meist schon in Durchlauf 1 (0ms)
auffindbar; im QtDragon-Embed-Host kann die Widget-Realisierung noch
laufen, wenn `initialized__()` feuert.

### Drei-Durchlaeufe-Timer (`_finalize_ui_ready`)

`initialized__()` (`lathe_easystep_handler.py:1337-1599`) plant nach eigener
Vorarbeit (Widget-IDs vergeben, einzelne Combos direkt verbinden, acht
`singleShot(0, ...)`-Startaufgaben) drei Durchlaeufe dergleichen Funktion:

```python
QtCore.QTimer.singleShot(0, self._finalize_ui_ready)
QtCore.QTimer.singleShot(500, self._finalize_ui_ready)
QtCore.QTimer.singleShot(2000, self._finalize_ui_ready)
```

Kommentar direkt darueber (`:1589-1596`) benennt den Grund: im Embed-Fall
kann die Widget-Realisierung des Host-GUI noch nicht abgeschlossen sein,
wenn der erste Durchlauf laeuft - statt Event-basiert zu warten, wird
einfach bei 0/500/2000ms erneut versucht. `finalize_ui_ready()`
(`ui_lifecycle.py:202-405`) fuehrt **denselben** Ablauf bei jedem Durchlauf
aus (kein "Durchlauf 1 macht X, Durchlauf 2 macht Y") - jeder Einzelschritt
ist fuer sich genommen idempotent (siehe naechster Abschnitt), sodass
Wiederholung guenstig ist. Drei Waechter am Funktionsanfang:

1. `if not handler.w: return` - noch keine Widgets.
2. `if handler._ui_finalized: return` - der eigentliche "fertig"-Riegel;
   macht alle spaeteren Durchlaeufe (500ms/2000ms, oder jeden versehentlichen
   erneuten Aufruf) zu einem reinen No-Op.
3. `if handler._finalize_ui_ready_running: return` - Reentranz-Schutz
   waehrend EINES Durchlaufs (z. B. gegen eine verschachtelte Qt-
   Ereignisschleife waehrend `findChild`/Dialogen).

Fertig ist ein Durchlauf, wenn `list_ops`, `btn_add`, `btn_generate` und
`tab_params` alle gefunden wurden - dann `_ui_finalized = True`,
`_startup_complete = True`, Log `"DONE after pass N"` (das ist exakt die
Zeile, die alle Standalone-Panel-Smoke-Checks in diesem Projekt seit
Session-Beginn abfragen).

### Idempotenz pro Schicht - drei verschiedene, aber konsistente Muster

- **UI-Fragmente** (`ui_split.py`, `load_split_tab_uis`/
  `load_step_management_uis`/`load_preview_uis`, bei jedem Durchlauf
  unbedingt aufgerufen): doppelt abgesichert - ein grober Bool-Flag pro
  Fragmentgruppe (`_split_tabs_loaded` etc.) UND eine Pruefung pro
  Container (`findChild(..., f"{container_name}_content")`) - macht den
  Loader sicher aufrufbar, selbst wenn der grobe Flag je zurueckgesetzt
  wuerde. Vorbildlich robust.
- **Widget-Registrierung** (`ui_widget_lookup.py`): mehrschichtige, jeweils
  fuer sich idempotente Kaskade - `register_known_widgets()` (setzt nur,
  was gerade aufloesbar ist), `resolve_core_widgets_strict()`
  (`if getattr(self, attr, None) is not None: continue`),
  `force_attach_core_widgets()` (`or`-verkettete Zuweisung). Eine
  "authoritative Cache"-Umschaltung (`_widget_name_cache_authoritative`,
  nach Durchlauf-Schritt "rebuild widget name cache") verhindert nach
  Abschluss teure wiederholte volle Baum-Scans - mit Messwert im Code
  belegt (LES-027: `connect_param_change_signals()` allein kostete vorher
  ~6,7s von ~18s Startzeit).
- **Signalbindung** (`ui_signals.py`): fuenf real existierende
  `connect_*`-Funktionen, **kein** `connect_remaining_signals` (das ist nur
  ein Log-Label in `ui_lifecycle.py`, keine echte Funktion). Vier
  verschiedene, aber jeweils konsistente Schutzmuster: `WeakSet` fuer
  Param-/Global-Form-Widgets, `set()` von `id(widget)` fuer Sprach-Combos,
  einzelne Bool-Flags fuer Tool-Preview-Combos, sowie fuer Buttons ein
  bewusst anderes Muster (`_connect_button_once()`: **immer** erst
  `disconnect()`, dann `connect()` - Docstring begruendet das explizit mit
  "Buttons werden an mehreren Stellen initialisiert").

### Zwei konkrete Befunde (kein Code veraendert, nur festgestellt)

- **Fehlender Schutz:** `connect_mode_visibility_signals()`
  (`ui_signals.py:170-182`) verbindet `face_mode`/`face_edge_type`/
  `drill_mode` OHNE jeden Dedup-Schutz - anders als alle fuenf anderen
  Connectoren. Da `finalize_ui_ready()` das bei jedem der drei Durchlaeufe
  erneut aufruft, bis `_ui_finalized` greift, ist eine Mehrfachverbindung
  ueber die drei Durchlaeufe hinweg ein echtes Risiko, wenn der Widget
  bereits in Durchlauf 1 gefunden wird, `_ui_finalized` aber aus anderem
  Grund (ein anderes der vier kritischen Widgets fehlt noch) erst in
  Durchlauf 2 oder 3 gesetzt wird - genau der Fall, den Embedded typischer-
  weise auslöst.
- **Toter Code:** `HandlerClass._connect_signals()`
  (`lathe_easystep_handler.py:1926-1935`) ist eine vollstaendige "alles
  verbinden"-Sammelmethode, die neun Einzelfunktionen in einer bestimmten
  Reihenfolge aufruft - wird aber laut projektweiter Suche NIRGENDS
  aufgerufen (nur einmal in einem Docstring-Kommentar erwaehnt). Der
  tatsaechlich laufende Ablauf lebt ausschliesslich in
  `finalize_ui_ready()`, mit anderer Zusammensetzung/Reihenfolge als diese
  ungenutzte Methode nahelegt - zwei divergierende "verbinde alles"-
  Erzaehlungen im Code, von denen nur eine wirklich laeuft. Direkt relevant
  fuer "nachvollziehbare Reihenfolge".
- **Zu verifizieren:** `process_deferred_lookups()`
  (`ui_widget_lookup.py:146-176`) leert eine Warteschlange fuer Widget-
  Lookups, die vor `ui_ready = True` deferred wurden - im gesamten
  `finalize_ui_ready()`-Ablauf wurde keine Aufrufstelle dafuer gefunden.
  Entweder wird sie an anderer Stelle getriggert (noch zu pruefen) oder die
  Warteschlange leert sich nie - muss vor jeder Aenderung an diesem Bereich
  geklaert werden.

### Bisherige Dokumentation

Bisher undokumentiert ausserhalb von Code-Kommentaren. `doc/
PANEL_ARCHITECTURE.md` hatte bislang nur einen Vorwaertsverweis (LES-052 §1
verschiebe das hierher), `DEV.md` dokumentiert nur einen engeren, bereits
behobenen Einzelfall ("Embedded-Widget-Binding (2026-02 Fix)"). Die
eigentliche Begruendung fuer idempotentes, mehrfach laufendes Laden steckt
ausschliesslich in Code-Kommentaren, v. a. drei Bloecke mit realen
Regressionsfunden: der `initialized__`-Kommentar ueber den drei Timern
(oben zitiert), `_dock_preview_above_scroll()` (LES-024: eine leer
gebliebene Fragment-Huelle verschob sichtbar die Preview-Groesse, deshalb
`removeWidget()` + `deleteLater()` statt blossem `hide()`), und
`_install_workspace_splitter()` (mehrere REGRESSIONSFUND-Kommentare zu
QtDragon-Embed-spezifischen Breiten-/Scroll-Problemen, z. B. gemessene
638px verfuegbar vs. 710px benoetigt ohne `QScrollArea`).

### Umsetzungsvorschlag (noch nicht umgesetzt)

1. **Bugfix:** `connect_mode_visibility_signals()` einen Dedup-Schutz nach
   demselben Muster wie die anderen Connectoren geben (Bool-Flags pro
   Widget) - mit dem in dieser Session etablierten Verfahren (Test vorher
   schreiben, der eine Mehrfachverbindung erkennt; Fix; Regressionsbeweis
   per absichtlichem Rueckbau).
2. **Klaeren, dann entscheiden:** `process_deferred_lookups()`-Aufrufstelle
   suchen. Falls keine existiert: entweder sauber einbinden (in
   `finalize_ui_ready()`, nach dem Setzen von `ui_ready = True`) oder als
   toten Code entfernen - Entscheidung erst nach Klaerung, ob die
   Warteschlange in der Praxis je etwas enthaelt.
3. **Toten Code entfernen oder beleben:** `_connect_signals()` - entweder
   nachweisen, dass sie wirklich nirgends gebraucht wird und entfernen, oder
   falls sie mal als sauberer Alternativeinstieg gedacht war, klaeren ob
   `finalize_ui_ready()` sie stattdessen nutzen sollte (staerkere Aenderung,
   nur falls die beiden Ablaeufe sich als aequivalent erweisen).
4. **Dokumentieren, nicht umbauen:** diesen Abschnitt als dauerhafte
   Doku-Grundlage belassen (bereits geschrieben) - der bestehende Ablauf
   selbst (drei-Durchlaeufe-Timer mit Idempotenz-Waechtern) ist funktional
   und gut, ein struktureller Umbau ist NICHT vorgeschlagen. Der TODO-Punkt
   "einheitlicher Ladevertrag ... nachvollziehbare Reihenfolge" ist damit
   im Kern durch Dokumentation plus die zwei kleinen Fixes oben erfuellbar,
   nicht durch eine groessere Umstrukturierung.

## Views ohne eigenen Fachzustand (LES-052, Bestandsaufnahme 2026-09-17)

Reine Bestandsaufnahme, kein Code veraendert. Das leitende Prinzip ist
bereits dokumentiert (siehe "Abhaengigkeitsrichtung" oben, aus LES-051:
"Qt-Views ... sind aber keine zweite Wahrheit fuer Programm- oder
Werkzeugdaten") - dieser Abschnitt prueft es gegen den tatsaechlichen Code.

### Stichprobe der View-Klassen

Im gesamten Paket existieren nur ~15 echte Klassen; die View-relevanten
wurden einzeln geprueft:

- **`StepListView`** (`ui_step_list_view.py`): vollstaendig zustandslos -
  liest `handler.list_ops` bei jedem Aufruf frisch, haelt selbst keine
  Kopie irgendeiner Operationsliste. Vorbildlich, im eigenen Docstring
  bereits so benannt.
- **`PreviewView`** (`ui_preview_view.py`): reiner Durchreiche-Adapter -
  nimmt `paths`/`scene`/Kontext als Methodenparameter entgegen und schreibt
  sie in die Preview-Widgets, haelt selbst nichts.
- **`LathePreviewWidget`** (`preview_widget.py`): haelt `paths`,
  `primitives`, `front_program`, `front_operation`, `preview_scene` als
  Instanzattribute - eine Rendering-Kopie von Programmdaten. Grep ueber das
  gesamte Projekt zeigt: nirgends ausserhalb von Tests und dem eigenen
  Sync-Code (`sync_slice_widget()` in `ui_preview.py`, das lediglich diese
  Werte auf ein zweites Preview-Widget uebertraegt) liest irgendein
  Fachlogik-Code diese Felder zurueck. Reine Schreib-Senke vom Controller,
  nie Quelle - dasselbe Verhalten, das fuer `ViewState` bereits per Test
  belegt ist ("mehrfach per Test belegt, siehe LES-051-Eintraege"), hier
  aber bisher nicht explizit fuer genau diese fuenf Felder abgesichert.
- **`ToolVisualProvider`** (`tool_visuals.py`): vollstaendig zustandslos
  (nur feste Konfiguration `_root`/`_manifest`), loest pro Aufruf frisch
  auf, cached kein Ergebnis. Docstring nennt das Ziel bereits explizit
  ("without leaking resource paths into models").
- **Kontur-Tabelle** (`ui_contour.py`, `QTableWidget`): folgt demselben
  Muster wie jedes andere Formularfeld im Projekt - jede Aenderung
  (`handle_contour_add_segment`, `-delete_segment`, `-table_change`) ruft
  sofort `handler._update_selected_operation()` auf, das die Tabelle in
  `Operation.params` zurueckschreibt. Kein Sonderfall, keine laenger
  lebende Divergenz zwischen Tabelle und Modell als bei jedem Spinbox-Feld
  auch.

### Befund: keine strukturelle Verletzung gefunden - aber keine Absicherung

Die Stichprobe findet keine tatsaechliche "zweite Wahrheit" im Sinne von
Code, der Programmdaten aus einer View zurueckliest. Der eigentliche Befund
ist ein anderer: **keines** der beiden in LES-052s "Abnahme"-Abschnitt
genannten Kriterien hat heute eine automatisierte Absicherung:

- "gleicher Programmzustand und identischer G-Code bei mindestens zwei
  Darstellungs-/Ressourcensaetzen" - keine Testdatei prueft das.
- "fehlende optionale Ressource fuehrt zu sichtbarer Diagnose, aber nicht zu
  geaendertem G-Code" - ebenfalls keine direkte Testabdeckung gefunden
  (grep nach `resource_set`/vergleichbaren Mustern in `tests/` ohne
  Treffer).

Das Prinzip steht also schon in `doc/PANEL_ARCHITECTURE.md`, ist bislang
aber unbewiesen statt durchgesetzt.

### Umsetzungsvorschlag (noch nicht umgesetzt)

1. Einen Regressionstest ergaenzen, der `generate_program_gcode()` (oder
   die hoehere `build_gcode_lines()`-Ebene) einmal mit vollstaendigen und
   einmal mit fehlenden/alternativen Darstellungsressourcen (z. B.
   `ToolVisualProvider` ohne Manifest-Eintrag) aufruft und byteidentisches
   G-Code-Ergebnis erwartet - schliesst direkt die erste Abnahme-Luecke.
2. Einen zweiten, kleineren Test ergaenzen, der gezielt `LathePreviewWidget`
   mit Test-Operationsdaten befuellt und danach prueft, dass
   `handler.model.operations`/erzeugter G-Code unveraendert bleiben -
   macht die bisher nur "beobachtete" Eigenschaft der fuenf
   Rendering-Cache-Felder (`paths`/`primitives`/`front_program`/
   `front_operation`/`preview_scene`) genauso beweisbar wie bei
   `ViewState`.
3. Kein struktureller Umbau vorgeschlagen: Die Stichprobe findet die
   Architektur bereits konform; der offene TODO-Punkt sollte durch die
   beiden neuen Tests plus eine kurze Doku-Ergaenzung ("gepruefte
   Konformitaet, siehe Tests X/Y") geschlossen werden, nicht durch neue
   Abstraktionen.
