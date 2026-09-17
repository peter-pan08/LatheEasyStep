# Changelog

## Dokumentation 2026-09-15

- `TODO.md` auf die tatsaechlich offenen Arbeiten konsolidiert. Historische
  Abschlussberichte und bereits erledigte IDs bleiben im Changelog; LES-022
  wurde als bisher fehlende offene Restarbeit wieder aufgenommen.
- Neue offene Architekturaufgabe LES-051 aufgenommen: Das Panel-Grundgeruest
  soll Zustand, Fachlogik, Views und externe Darstellungsressourcen strikt
  trennen. Austauschbare Schneidplatten-Grafiken oder komplette Darstellungs-
  Sets duerfen dadurch weder Programm-/Werkzeugdaten noch G-Code oder Dirty-
  State beeinflussen.
- Der Umsetzungsplan fuer diese Architektur ist als LES-052 in `TODO.md`
  festgehalten: Ladevertrag, Zustandsmodell, Darstellungsadapter, atomare
  Fehlergrenzen, Undo/Redo, Autosave, Werkzeugdaten-Domaene und technischer
  Pruefbericht.

## [Unreleased]

### LES-052: Abschnitt 5 - unbekannte Tool-Tabellen-Felder werden erhalten 2026-09-17

- Kleinsten offenen Teil von Abschnitt 5 ("Werkzeugtabelle als eigene
  Domaene kapseln ... unbekannte Felder") umgesetzt, nach Nutzer-
  Entscheidung bewusst ohne das Zurueckschreiben in die `tool.tbl`-Datei
  selbst (separater, groesserer Schritt mit Schreibzugriff auf eine
  externe Maschinenkonfigurationsdatei).
- `parse_tool_table()` (`tools.py`) las Tool-Tabellen-Token wie X/Y/Z/A/B/
  C/U/V/W/I/J/R (alles ausser T/P/D/Q, aus dem Standard-LinuxCNC-
  Tooltable-Layout) bisher in ein lokales `token_map`, verwarf sie danach
  aber stillschweigend - nie an das `Tool`-Objekt weitergegeben. Neues
  Feld `Tool.unknown_fields: Dict[str, str]` (mit Default `{}`, daher
  keine bestehende `Tool(...)`-Konstruktion betroffen) erhaelt diese Werte
  jetzt. Rein additive Datenerhaltung, noch keine Fachlogik liest das Feld.
- `parse_tool_table()` hatte bislang ueberhaupt keine eigene Testdatei -
  nur `Tool`-Konstruktion und darauf aufbauende Pruefungen waren getestet,
  nie der Parser selbst. Neue Datei `tests/test_tool_table_parsing.py` (4
  Tests) deckt jetzt auch den Grundfall (bekannte Felder korrekt geparst)
  ab. Regressionsbewiesen: ein Test schlug vor dem Fix nachweislich fehl.
- 921 Stub-/110 Real-Qt-Tests bestanden (917 vorher + 4 neue),
  Standalone-Panel sauber gestartet (echter `tool.tbl`-Ladepfad
  durchlaufen).

### LES-052: Abschnitt 3 - Rollback-Luecke gefunden und behoben 2026-09-17

- Abschnitt 3 ("Atomare Zustandsaenderungen und Fehlergrenzen") gegen den
  Code geprueft - anders als Abschnitt 1/2 ist das hier NICHT ueberwiegend
  bereits erledigt. Details: `doc/PANEL_ARCHITECTURE.md` → "Atomare
  Zustandsaenderungen und Fehlergrenzen".
- **Konkreter, sicherheitsrelevanter Fund und behoben:**
  `sync_form_to_operation()` (`ui_program.py`) ueberschrieb `op.params` mit
  den neu gesammelten Formularwerten, BEVOR `update_geometry()`
  validierte. `validate_finite_data()` (`model.py`/`numeric.py`) wirft bei
  NaN/Inf oder nicht-numerischen Eingaben eine echte, erreichbare
  Exception - schlug diese Validierung fehl, blieb `op.params` auf dem
  halb angewendeten, ungueltigen Stand stehen, ohne jede sichtbare
  Meldung (der einzige Aufrufer `handle_param_change()` schluckt die
  Exception komplett). Jetzt wird bei einem Fehlschlag von
  `update_geometry()` auf die vorherigen Parameter zurueckgesetzt, bevor
  die Exception weitergereicht wird. Regressionsbewiesen: ein neuer Test
  schlug vor dem Fix nachweislich fehl.
- Die anderen drei Punkte des Abschnitts (projektweite `except Exception`-
  Haertung: ~400 Vorkommen in 40+ Dateien, deutlich groesser als der
  bereits laufende, engere LES-044-Umfang; zentrale Fehlerdiagnose-
  Sammlung; einheitliche Fehlerklassen `INFO`/`WARNING`/`BLOCKING_ERROR`/
  `INTERNAL_ERROR`) sind vollstaendig unimplementiert und bewusst NICHT in
  dieser Session angegangen - eigenstaendige, projektweite
  Entwurfsentscheidungen, die vor der Umsetzung eigene Klaerung
  verdienen.
- 917 Stub-/110 Real-Qt-Tests bestanden, Standalone-Panel sauber
  gestartet.

### LES-052: Abschnitt 2 vollstaendig - vierter Punkt war ebenfalls schon erledigt 2026-09-17

- Vierten und letzten offenen Punkt aus Abschnitt 2 ("Preview-Canvas,
  Werkzeugbild, Legende, Status-/Warnungsbox ... ueber stabile
  Datenvertraege austauschbar machen") gegen den Code geprueft: bereits
  seit LES-044/LES-051 vollstaendig umgesetzt. `preview_geometry.py`
  enthaelt fuer jeden dieser Bereiche einen dedizierten, Qt-freien
  Datenvertrag (`PREVIEW_DRAW_STYLES`, `FRONT_VIEW_RING_STYLES`,
  `FRONT_VIEW_FILL_COLORS`, `PREVIEW_CHROME_STYLES`, `PREVIEW_CHROME_
  FILLS`, `LEGEND_ENTRIES`/`legend_layout()`, `STATUS_BOX_STYLE`/
  `status_message_layout()`), `preview_scene.py` die zugehoerigen
  Zeichenplaene (`build_preview_draw_plan()` u. a.) - `paintEvent()`
  (`preview_widget.py`) liest nur noch daraus, konstruiert keine `QPen`/
  `QColor`-Werte mehr direkt. Jeder Vertrag hat einen eigenen "ist ein
  reiner Vertrag"-Test in `tests/test_preview_legend_and_status_layout.py`
  (bereits vorhanden, nicht neu geschrieben).
- Reine Dokumentationskorrektur, kein Code veraendert - TODO.md Abschnitt 2
  ist damit komplett geschlossen (alle vier Punkte), `doc/PANEL_
  ARCHITECTURE.md`s "Werkzeugdarstellung"-Abschnitt entsprechend ergaenzt.
  916 Stub-/110 Real-Qt-Tests weiterhin bestanden (keine Aenderung).

### LES-052: Korrektur einer Testduplizierung + Section-2-Bestandsaufnahme 2026-09-17

- Beim Umsetzen von TODO.md-Abschnitt 2 ("Darstellungs- und
  Ressourcenadapter") festgestellt: `ToolVisualProvider`/
  `ToolVisualRequest`/`ToolVisual` (`tool_visuals.py`) waren bereits aus
  LES-051 vollstaendig implementiert, getestet und ueber
  `resolve_tool_visual()`/`handler._tool_visual_provider`
  (`tool_logic.py`) live verdrahtet - TODO.md war hier veraltet (drei der
  vier Punkte in Abschnitt 2 waren faktisch schon erledigt), analog zum
  frueheren `ViewState`-Befund.
- **Eigener Fehler korrigiert:** der im vorigen Commit hinzugefuegte Test
  `test_gcode_identical_across_different_tool_visual_resource_sets`
  (`tests/test_regression_contracts.py`) erwies sich als redundant mit der
  bereits bestehenden `test_switching_tool_visual_resource_never_affects_
  generated_gcode` (`tests/test_tool_preview_layout.py`, LES-051) - die
  urspruengliche Bestandsaufnahme hatte diese Abdeckung uebersehen (die
  Grep-Suche war zu eng auf `resource_set`-artige Substrings fokussiert,
  der bestehende Test heisst anders). Entfernt; stattdessen den
  bestehenden Test echt verbessert (laeuft jetzt gegen alle
  `example_programs()` statt nur "Bohren.ngc").
- Fehlenden Teil des LES-052-Abnahmekriteriums ergaenzt: "Dirty-/Save-
  State" war bisher nirgends explizit geprueft. Neuer Test
  `test_render_tool_preview_never_marks_program_dirty`
  (`tests/test_tool_preview_layout.py`) macht das explizit
  (`_mark_dirty`-Spion bleibt beim Rendern ungenutzt). Regressionsbewiesen.
- TODO.md Abschnitt 2 entsprechend aktualisiert: drei der vier Punkte als
  erledigt markiert, der vierte (stabile Datenvertraege fuer Preview-
  Canvas/Werkzeugbild/Legende/Status-Box) noch nicht im Detail geprueft -
  bleibt offen. Ebenfalls festgehalten: `handler._tool_visual_provider`
  wird in der laufenden Anwendung nirgends auf ein echtes Theme-Verzeichnis
  gesetzt (nur prozeduraler Fallback) - kein Bug, aber ein offener
  Produktentscheid.
- 916 Stub-/110 Real-Qt-Tests bestanden.

### LES-052: Ladevertrag- und Views-Bestandsaufnahme umgesetzt 2026-09-17

- Alle vier Punkte aus der vorangegangenen Ladevertrag-/Views-
  Bestandsaufnahme umgesetzt (Details: `doc/PANEL_ARCHITECTURE.md`).
- **Bugfix:** `connect_mode_visibility_signals()` (`ui_signals.py`) hat
  jetzt denselben Dedup-Schutz wie die anderen fuenf Signal-Connectoren
  (ein Bool-Flag pro Widget). Regressionsbewiesen: ein neuer Test schlug
  vor dem Fix nachweislich fehl (3 statt 1 Verbindung nach drei Aufrufen).
- **Toter Code entfernt:** `process_deferred_lookups()` (`ui_widget_
  lookup.py`) hatte nachweislich keine Aufrufstelle im gesamten Projekt -
  entfernt, zusammen mit der nie geleerten `_deferred_lookup_queue`
  (Initialisierung im Handler-`__init__`, Befuellungslogik in
  `resolve_core_widgets_strict()` und `bootstrap_widget_refs()`). Reine
  Aufraeumarbeit, keine Verhaltensaenderung.
- **Toter Code entfernt, aber differenzierter als gedacht:**
  `HandlerClass._connect_signals()` war tatsaechlich toter Code (nirgends
  aufgerufen) und wurde entfernt, ebenso die davon exklusiv aufgerufenen
  `_connect_live_update_signals()`/`_connect_live_update()`/
  `_on_param_changed()` (nachweislich redundant mit dem laengst laufenden
  `connect_param_change_signals()`-Pfad) und `prepare_signal_connection_
  context()` (alle vier Einzelaktionen bereits anderweitig abgedeckt).
  `connect_resolver_fallbacks()` dagegen war NICHT redundant - ein
  einzigartiger 5s-Polling-Rueckfall speziell fuer `listOperations` (eines
  der vier `_ui_finalized`-kritischen Widgets). Statt entfernt: sauber in
  `finalize_ui_ready()` eingebunden, mit neuem
  `_list_ops_resolver_fallback_started`-Schutz gegen mehrfach gestartete
  Polling-Ketten ueber die drei Durchlaeufe. Zwei neue Tests decken das ab,
  regressionsbewiesen.
- **Zwei neue Regressionstests** fuer die LES-052-Abnahmekriterien zu
  "Views ohne eigenen Fachzustand" (`tests/test_regression_contracts.py`):
  identischer G-Code bei unterschiedlichen `ToolVisualProvider`-
  Ressourcensaetzen; `LathePreviewWidget`s Rendering-Cache-Felder
  (`paths`/`primitives`/`front_program`/`front_operation`/
  `preview_scene`) fliessen nachweislich nie in G-Code zurueck. Beide per
  absichtlicher Mutation der verglichenen Werte sanity-geprueft.
- Kein struktureller Umbau des Drei-Durchlaeufe-Ladeablaufs, wie in der
  Bestandsaufnahme vorgeschlagen - nur die konkreten Befunde behoben.
- 917 Stub-/109 Real-Qt-Tests bestanden (912 Stub-Tests vorher + 5 neue,
  alle Stub-only), Standalone-Panel sauber gestartet.

### LES-052: Ladevertrag + Views-Bestandsaufnahme 2026-09-17

- Die beiden verbleibenden Punkte aus LES-052 Abschnitt 1 ("einheitlicher
  Ladevertrag" und "Views ohne eigenen Fachzustand") gegen den
  tatsaechlichen Code geprueft und in `doc/PANEL_ARCHITECTURE.md`
  dokumentiert - reine Bestandsaufnahme, kein Code veraendert.
- **Ladevertrag:** kein expliziter Standalone-/Embedded-Modus im Code -
  Unterscheidung ist rein strukturell (`_looks_like_panel_widget()`). Der
  bestehende Drei-Durchlaeufe-Timer (`_finalize_ui_ready`, 0/500/2000ms)
  ist idempotent gut abgesichert (`_ui_finalized`-Riegel,
  `_finalize_ui_ready_running`-Reentranzschutz, pro Schicht konsistente,
  aber unterschiedliche Dedup-Muster). Zwei konkrete Befunde: (1)
  `connect_mode_visibility_signals()` fehlt als einzigem von sechs
  Signal-Connectoren ein Dedup-Schutz - echtes Mehrfachverbindungsrisiko
  ueber die drei Durchlaeufe, besonders embedded; (2) toter Code
  `HandlerClass._connect_signals()` wird laut projektweiter Suche nirgends
  aufgerufen, divergiert von der tatsaechlich laufenden Signalbindung in
  `finalize_ui_ready()`; (3) unklar, ob `process_deferred_lookups()`
  ueberhaupt eine Aufrufstelle hat. Vorschlag: die drei Punkte beheben/
  klaeren, den bestehenden Ablauf selbst NICHT strukturell umbauen.
- **Views ohne eigenen Fachzustand:** Stichprobe der View-Klassen
  (`StepListView`, `PreviewView`, `LathePreviewWidget`, `ToolVisualProvider`,
  Kontur-Tabelle) fand keine tatsaechliche "zweite Wahrheit" - das in
  LES-051 bereits dokumentierte Prinzip wird eingehalten. Der eigentliche
  Befund: keines der beiden LES-052-Abnahmekriterien dazu (identischer
  G-Code bei unterschiedlichen Darstellungs-/Ressourcensaetzen; fehlende
  Ressource aendert G-Code nicht) hat heute eine automatisierte
  Absicherung. Vorschlag: zwei neue Regressionstests statt eines
  strukturellen Umbaus.
- Details und vollstaendige Fundstellen: `doc/PANEL_ARCHITECTURE.md`
  (neue Abschnitte "Ladevertrag: Standalone und Embedded" und "Views ohne
  eigenen Fachzustand"), `TODO.md` (LES-052 Abschnitt 1).
- 912 Stub-/109 Real-Qt-Tests weiterhin bestanden (reine
  Dokumentationsaenderung, kein Code betroffen).

### LES-052: toten Code in `refresh_operation_list()` entfernt 2026-09-17

- Der bei der `refresh_operation_list()`-Handler-Kleber-Extraktion
  gefundene tote `select_index is None`-Zweig ("vorherige Auswahl
  beibehalten") entfernt - jeder Aufrufer im Projekt (neun Stueck, ueber
  `ui_flow.py`/`ui_persistence.py`/`lathe_easystep_handler.py`) uebergibt
  bereits einen expliziten `select_index`. `select_index` ist jetzt ein
  regulaerer Pflichtparameter statt `int | None = None` - sowohl auf der
  freien Funktion (`ui_flow.py`) als auch auf dem duennen Handler-Wrapper.
  Die damit ebenfalls unbenutzt gewordene `current = lst.currentRow()`-
  Zeile mit entfernt.
- Reine Aufraeumarbeit ohne Verhaltensaenderung (der entfernte Zweig war
  beweisbar unerreichbar); keine neuen Tests noetig, volle Suite bestaetigt
  unveraendertes Verhalten.
- 912 Stub-/109 Real-Qt-Tests weiterhin bestanden, Standalone-Panel sauber
  gestartet.

### LES-052: `ViewState` gekapselt - fuenfte Zustandskategorie 2026-09-17

- `view_state.py` neu: fasst die neun bisher losen Attribute auf
  `LathePreviewWidget` (`_view_zoom`, `_view_pan`, `slice_z`,
  `slice_enabled`, `view_mode`, `active_index`, `_legend_collapsed`,
  `show_legend`, `status_messages`) in einer einzigen, Qt-freien Klasse
  zusammen (`widget._view`). `_view_pan` (vormals `QtCore.QPointF`) wird
  als zwei reine `float`-Felder (`pan_x`/`pan_y`) gehalten, damit das Modul
  komplett ohne Qt-Import auskommt.
- Anders als bei `DirtyState`/`ToolTableState`/`RuntimeState` (deren
  Aufrufstellen ueber viele Module verteilt waren, deshalb per Umbenennung
  auf `handler._<name>.<feld>` umgestellt) liegt die gesamte Nutzung dieser
  neun Felder innerhalb einer einzigen Klasse (62 Fundstellen in
  `preview_widget.py`). Deshalb ein anderer Adapter-Mechanismus:
  `LathePreviewWidget` haelt fuer jedes Feld eine gleichnamige `@property`,
  die transparent an `self._view.<feld>` delegiert - keine der 62 internen
  Nutzungsstellen musste angefasst werden, und externer Code (mehrere
  Tests lesen/setzen `widget.slice_z`/`widget.active_index`/`widget.
  _view_zoom`/`widget._view_pan` direkt) funktioniert unveraendert weiter.
- 4 Testfixturen (`LathePreviewWidget.__new__(LathePreviewWidget)`,
  `__init__` uebersprungen) in `tests/test_front_slice_profile.py`,
  `tests/test_preview_widget_error_boundaries.py`,
  `tests/test_slice_view_sync.py` mussten um `widget._view = ViewState()`
  ergaenzt werden.
- 4 neue eigenstaendige Tests (`tests/test_view_state.py`, Qt-frei) plus 1
  neuer Property-Rundlauf-Test in `tests/test_preview_navigation.py`
  (`test_view_zoom_and_pan_properties_delegate_to_view_state`), der
  gezielt die `_view_pan`-QPointF-Rueckuebersetzung absichert - die
  einzige echte Logik dieser Kapselung.
- Regressionsverifikation bestaetigt: eine absichtliche Verstuemmelung der
  `_view_pan`-Setter-Property (Y-Komponente faelschlich aus `value.x()`
  statt `value.y()`) wurde von mehreren Tests korrekt erkannt, darunter
  zwei bereits vorher bestehende Navigationstests.
- Damit sind jetzt alle sechs in LES-052 genannten Zustandskategorien
  tatsaechlich gekapselt (`ProgramState`, `OperationState`, `ToolTableState`,
  `ViewState`, `DirtyState`, `RuntimeState`) - siehe auch die fruehere
  Korrektur weiter unten, die diese Aussage vorschnell fuer `ViewState`
  behauptet hatte, bevor die Arbeit tatsaechlich erledigt war.
- 912 Stub-/109 Real-Qt-Tests bestanden (908 vorher + 4 neue Stub- und 1
  neuer Real-Qt-Test), Standalone-Panel sauber gestartet.

### LES-052: fuenfte Handler-Kleber-Extraktion (`tool_change_position_lines`) 2026-09-17

- `_tool_change_position_lines()` (~35 Zeilen, baut G-Code zum Anfahren der
  Werkzeugwechselposition aus XT/ZT/Koordinatenmodus) griff ueberhaupt
  nicht auf `self` zu - reine Funktion, die nur zufaellig als Handler-
  Methode lebte. Nach `tool_change_position_lines(header)` in `ui_flow.py`
  verschoben, ganz ohne Handler-Parameter. Einziger Aufrufer war bereits
  `build_gcode_lines()` (selbst schon in `ui_flow.py`); dessen zwei
  Aufrufstellen rufen die Funktion jetzt direkt auf.
  `HandlerClass._tool_change_position_lines()` bleibt als duenner
  Delegations-Wrapper bestehen, falls extern noch darauf zugegriffen wird.
- Bestandsaufnahme deckte eine bemerkenswerte Luecke auf: diese G-Code-
  Pfad-Logik (Werkzeugwechsel-Anfahrposition) hatte ueberhaupt keine Tests.
  `generate_program_gcode()` (`gcode_program.py`) implementiert dieselbe
  work/machine/mixed-Logik ein zweites Mal, unabhaengig, fuer die inline
  `"(Toolchange move)"`-Zeilen im Hauptprogramm - deren vorhandene Tests
  (`tests/test_regression_contracts.py`) deckten nur diese zweite,
  separate Implementierung ab, nie `_tool_change_position_lines()` selbst.
  Geschlossen durch drei neue Tests in derselben Datei.
- Reine Verschiebung ohne Verhaltensaenderung, daher keine `rs274`-
  Nachverifikation noetig (CLAUDE.md verlangt sie fuer Aenderungen an
  G-Code-Ausgabe/Fahrwegen, nicht fuer reine Code-Bewegung); die neue
  Testabdeckung schliesst trotzdem eine bisher unbeaufsichtigte Luecke in
  diesem sicherheitsrelevanten Bereich.
- Regressionsverifikation bestaetigt: eine absichtliche Verstuemmelung des
  mixed-Zweigs (fehlendes `G53`-Praefix fuer die nicht-absolute X-Achse)
  wurde korrekt erkannt.
- 908 Stub-/108 Real-Qt-Tests bestanden (905 vorher + 3 neue), Standalone-
  Panel sauber gestartet.

### LES-052: vierte Handler-Kleber-Extraktion (`populate_thread_standard_options`) 2026-09-17

- `_populate_thread_standard_options()` (Handler-Methode, ~46 Zeilen) nach
  `populate_thread_standard_options(self)` in `ui_thread.py` verschoben -
  diesmal nicht nach `ui_flow.py`, sondern in das bereits existierende
  `ui_thread.py`, das mit `apply_thread_preset(self, ...)` bereits dasselbe
  Delegations-Muster fuer Gewinde-Logik enthielt. Die beiden nur dafuer
  gebrauchten Imports (`metric_thread_presets`, `trapezoidal_thread_
  presets`) aus `lathe_easystep_handler.py` entfernt (dort ungenutzt).
- Bewusst NICHT extrahiert: `_ensure_contour_widgets()`/
  `_ensure_thread_widgets()` (reine Widget-Lookup-Bootstrap-Methoden,
  aehnliche Groessenordnung) - das ist Bootstrap-Code, der laut LES-052
  Abschnitt 1 auf dem Handler bleiben soll; ihre eigentliche offene Aufgabe
  ist der separate "einheitlicher Ladevertrag"-Punkt, keine reine
  Verschiebung.
- Bestandsaufnahme ergab wieder eine echte Testluecke:
  `test_apply_thread_preset_applies_real_metric_preset`
  (`tests/test_preview_safety_and_language.py`) baut das erwartete Combo-
  itemData nur von Hand nach, ruft `_populate_thread_standard_options()`
  selbst nie auf. Geschlossen durch zwei neue Tests
  (`test_populate_thread_standard_options_builds_valid_preset_itemdata`,
  `test_populate_thread_standard_options_is_idempotent`).
- Regressionsverifikation reproduzierte gezielt den im Nachbartest bereits
  dokumentierten historischen Bug (Metric-Presets ohne `"label"`-Schluessel
  im itemData) und wurde vom neuen Test korrekt erkannt.
- 905 Stub-/108 Real-Qt-Tests bestanden (903 vorher + 2 neue), Standalone-
  Panel sauber gestartet (ein erster Lauf brach ohne Fehler/Traceback beim
  20s-Timeout knapp vor der `DONE`-Zeile ab, bei 25s reproduzierbar sauber -
  als Umgebungs-/Lastschwankung eingeordnet, keine Codeaenderung noetig).

### LES-052: dritte Handler-Kleber-Extraktion (`handle_param_change`) 2026-09-17

- `_handle_param_change()` (Handler-Methode, ~73 Zeilen; generischer
  Signal-Handler fuer alle Parameter-Widgets - Spinbox/Combo/Checkbox/
  Lineedit) nach `handle_param_change(handler)` in `ui_flow.py` verschoben;
  Handler-Methode auf einen einzeiligen Delegations-Wrapper reduziert. Bleibt
  als Qt-Slot in `ui_signals.py` (`widget.valueChanged.connect(handler.
  _handle_param_change)` u. ae.) unveraendert funktionsfaehig, da weiterhin
  eine gebundene Methode auf `handler` verbunden wird.
- `test_current_text_occurrences_are_limited_to_audited_fallbacks`
  (`tests/test_ui_visibility_guards.py`, eine Positivliste erlaubter
  `currentText()`-Fallback-Vorkommen je Datei) musste um die verschobene
  Datei ergaenzt werden - reine Ortsangabe, keine inhaltliche Aenderung der
  Pruefung selbst.
- Bestandsaufnahme vor der Extraktion ergab eine echte Testluecke: kein
  Test rief `_handle_param_change()`/`handle_param_change()` bisher
  end-zu-end auf. Die beiden vorhandenen Tests pruefen nur die Signal-
  Verbindung bzw. dass das Befuellen der Formularfelder keine Signale
  ausloest (LES-025), nie die eigentliche Wert-Lese-/Dirty-Markier-Logik.
  Geschlossen durch drei neue Tests in `tests/test_dirty_and_messages.py`
  (`test_handle_param_change_marks_operation_dirty_for_spinbox`,
  `test_handle_param_change_marks_program_dirty_for_header`,
  `test_handle_param_change_ignores_unnamed_widget`).
- Regressionsverifikation bestaetigt: eine absichtliche Verstuemmelung der
  PROGRAM_HEADER-vs-Step-Unterscheidung beim Dirty-Markieren wurde vom
  neuen `test_handle_param_change_marks_program_dirty_for_header` korrekt
  erkannt.
- 903 Stub-/108 Real-Qt-Tests bestanden (900 vorher + 3 neue), Standalone-
  Panel sauber gestartet.

### LES-052: zweite Handler-Kleber-Extraktion (`refresh_operation_list`) 2026-09-17

- `_refresh_operation_list()` (Handler-Methode, ~74 Zeilen) nach
  `refresh_operation_list(handler, select_index=None)` in `ui_flow.py`
  verschoben; Handler-Methode auf einen einzeiligen Delegations-Wrapper
  reduziert - gleiches Muster wie zuvor `handle_add_operation`/
  `handle_delete_operation`. Bestehende Tests, die `handler.
  _refresh_operation_list` als Instanz-Lambda ueberschreiben (u. a.
  `test_dirty_and_messages.py`), bleiben unveraendert funktionsfaehig, da
  nur der Methodenkoerper und nicht die Aufruf-Signatur verschoben wurde.
- Regressionsverifikation deckte einen zweiten, andersartigen Befund auf:
  der `select_index is None`-Zweig ("vorherige Auswahl beibehalten") ist
  toter Code - jeder Aufrufer im Projekt uebergibt bereits einen expliziten
  `select_index`, nie `None`. Eine Verstuemmelung dieser Zeile wurde
  folgerichtig von keinem Test erkannt, weil kein Aufrufpfad sie erreicht.
  Bewusst NICHT behoben (waere eine Verhaltensaenderung ueber reine
  Code-Verschiebung hinaus); als eigener Aufraeumpunkt in `TODO.md`
  vermerkt. Eine zweite Korruption am tatsaechlich erreichten
  `select_index`-Zweig wurde dagegen korrekt von
  `test_delete_last_step_selects_previous`
  (`tests/test_step_double_click.py`) erkannt - bestaetigt echte
  Regressionsabdeckung fuer den produktiv genutzten Pfad.
- 900 Stub-/108 Real-Qt-Tests bestanden, Standalone-Panel sauber gestartet.

### Korrektur: `ViewState` in LES-052 faelschlich als abgeschlossen gefuehrt 2026-09-17

- Die Formulierung "alle sechs Zustandskategorien ... sind jetzt fachlich
  getrennte, Qt-freie Verantwortungen" im Commit "LES-052: RuntimeState
  gekapselt - Zustandsmodell abgeschlossen" (2026-09-17) und in der davon
  abgeleiteten `TODO.md`-Zusammenfassung war fuer `ViewState` sachlich
  falsch: der Baustein selbst hat nur `ProgramState`, `OperationState`,
  `ToolTableState`, `DirtyState` und `RuntimeState` gekapselt.
  `doc/PANEL_ARCHITECTURE.md`s eigener, detaillierterer `ViewState`-
  Abschnitt hatte den tatsaechlichen Stand die ganze Zeit korrekt als
  "teilweise gekapselt, aber ungetypt" beschrieben - dieser Widerspruch
  wurde beim Schreiben nicht bemerkt.
- `TODO.md` korrigiert: `ViewState` aus der "Umgesetzt"-Liste entfernt, ein
  neuer offener Punkt fuer einen benannten `ViewState`-Typ (Zoom/Pan/Slice/
  Ansichtsmodus/Legende, aktuell lose Attribute auf `LathePreviewWidget`)
  ergaenzt. Reine Dokumentationskorrektur, kein Code betroffen - der
  fehlerhafte Commit selbst wird nicht nachtraeglich umgeschrieben, da er
  bereits nach `origin/dev` gepusht war.

### LES-052: erste Handler-Kleber-Extraktion (`handle_add_operation`/`handle_delete_operation`) 2026-09-17

- `_handle_add_operation()`/`_handle_delete_operation()` (Handler-Methoden in
  `lathe_easystep_handler.py`, ~95/~54 Zeilen) nach `handle_add_operation
  (handler)`/`handle_delete_operation(handler)` in `ui_flow.py` verschoben;
  Handler-Methoden auf einzeilige Delegations-Wrapper reduziert - gleiches
  Muster wie zuvor `handle_move_up`/`handle_move_down`.
- Zwei bei der urspruenglichen `RuntimeState`-Bestandsaufnahme uebersehene
  lose Reentranz-/Debounce-Attribute (`_adding_operation`,
  `_last_add_operation_ts`) beim Lesen des Methodenkoerpers entdeckt und
  direkt als `adding_operation`/`last_add_operation_ts` in `RuntimeState`
  aufgenommen statt als weitere lose Handler-Attribute stehen zu lassen.
  `last_add_operation_ts` ist ein 0,8s-Debounce-Zeitstempel gegen sehr
  schnell aufeinanderfolgende, aber nicht ueberlappende Klicks - kein
  Reentranz-Flag wie die anderen zehn `RuntimeState`-Felder.
- Regressionsverifikation (absichtliche `if False:`-Verstuemmelung der
  Kommentar-Auffrisch-Zeile in `handle_add_operation()`) deckte eine echte
  Testluecke auf: `test_handle_add_operation_refreshes_stale_numbered_
  comment_via_helper` (`tests/test_auto_comment_on_creation.py`) pruefte
  trotz seines Namens nur den reinen `_looks_like_generated_step_comment()`-
  Helfer, nie `handle_add_operation()` end-to-end - die Korruption blieb
  dadurch unbemerkt. Behoben: der irrefuehrend benannte Test in
  `test_looks_like_generated_step_comment_helper` umbenannt (unveraenderter
  Inhalt) und zwei neue End-zu-Ende-Tests ergaenzt
  (`test_handle_add_operation_refreshes_stale_numbered_comment`,
  `test_handle_add_operation_keeps_individual_comment`), die
  `handle_add_operation()` tatsaechlich aufrufen. Luecke danach nachweislich
  geschlossen: Korruption fuehrte zu einem Testfehlschlag, Ruecknahme wieder
  zu gruen.
- 900 Stub-/108 Real-Qt-Tests bestanden, Standalone-Panel sauber gestartet
  (kein `AttributeError`, `_finalize_ui_ready DONE`).

### Dokumentation: TODO.md auf offene Aufgaben reduziert 2026-09-17

- `TODO.md` war entgegen der eigenen Einleitung ("enthaelt ausschliesslich
  offene Aufgaben") wieder zu einem Entwicklungsprotokoll angewachsen: 6
  abgehakte (`[x]`) Punkte mit mehrseitigen Umsetzungsnarrativen sowie lange,
  in offene (`[ ]`) Punkte eingebettete Baustein-Historien (u. a. teilweise
  veraltete Zwischen-Teststaende wie "877 Stub-/107 Real-Qt-Tests" neben
  einer bereits auf 898/108 aktualisierten "Verifizierte Basis" oben).
  Von 560 auf 323 Zeilen reduziert: alle 6 `[x]`-Punkte entfernt (jeder
  bereits mit eigenem, vollstaendigem Changelog-Eintrag dokumentiert -
  ueberprueft vor dem Entfernen), Baustein-Historien in den verbleibenden
  offenen Punkten auf kurze "umgesetzt, Details im Changelog"-Absaetze
  gekuerzt. Alle 57 zuvor offenen Teilaufgaben inhaltlich unveraendert
  erhalten (per Zeilenvergleich verifiziert) - nur die Umsetzungsnarrative
  entfernt, keine Aufgabe geaendert oder gestrichen.
- Drei neue offene Punkte ergaenzt (neuer Abschnitt "Release-Prozess"): der
  am 17.09.2026 eingefuehrte `scripts/create_release.py`-Release-Pfad wurde
  bisher nur mit `--check` (rein lesend) getestet, nicht der tatsaechlich
  schreibende Pfad; Manifest-Vollstaendigkeit (neue Laufzeitpfade ausserhalb
  `release_manifest.txt`) muss vor jedem Release explizit geprueft werden,
  da das Skript das nicht selbst erkennen kann; die Agenten-
  Instruktionsdateien sollen auf `RELEASE_POLICY.md` als verbindliche Quelle
  verweisen, statt deren Regeln zu duplizieren.
- Ausserdem in "Verifizierte Basis" nachgezogen: `main` enthaelt seit dem
  17.09.2026 nur noch kompakte Release-Commits nach der neu eingefuehrten
  `RELEASE_POLICY.md` (`release_manifest.txt`), nicht mehr den vollstaendigen
  `dev`-Baum per Fast-Forward wie beim 0.8.0-Release. `main`s Historie sowie
  die Tags `v0.7.0`/`v0.8.0` wurden dafuer einmalig neu aufgebaut.
- 898 Stub-/108 Real-Qt-Tests weiterhin bestanden (reine Dokumentations-
  aenderung, kein Code betroffen).

### LES-052: RuntimeState gekapselt - Zustandsmodell abgeschlossen 2026-09-17

- Vierter und letzter LES-052-Baustein: neun lose Reentranz-/Ladezustands-
  Flags (`_loading_step`, `_deleting`, `_saving_step`, `_saving_changes`,
  `_moving_up`, `_moving_down`, `_generating_gcode`,
  `_creating_new_program`, `_ui_loading`) durch eine einzelne Qt-freie
  Klasse `RuntimeState` (`runtime_state.py`) ersetzt, jetzt als
  `handler._runtime` gehalten. Damit sind alle sechs in LES-052 genannten
  Zustandskategorien (`ProgramState`, `OperationState`, `ToolTableState`,
  `ViewState`, `DirtyState`, `RuntimeState`) fachlich getrennte, Qt-freie
  Verantwortungen mit dokumentierten Besitzverhaeltnissen.
- Acht der neun Felder folgen an neun praktisch identischen Aufrufstellen
  (`ui_flow.py`, `ui_persistence.py`, `lathe_easystep_handler.py`)
  demselben Reentranz-Muster (`if state.x: return` / `state.x = True` /
  im `finally` `state.x = False`) - bewusst NICHT zu einer
  `guard()`-Kontextmanager-Abstraktion zusammengefasst, da das eine echte
  Struktur-/Verhaltensaenderung an den Aufrufstellen gewesen waere, nicht
  nur eine Verschiebung des Speicherorts.
- `ui_loading` ist semantisch anders (unterdrueckt Signal-Reaktionen
  waehrend programmatischen Zurueckschreibens ins Formular) und war zuvor
  NIE explizit initialisiert - nur per `getattr(handler, "_ui_loading",
  False)` defensiv gelesen. Jetzt wie die anderen acht ein regulaeres
  `RuntimeState`-Feld mit Default `False`.
- Groesste Testflaeche der vier LES-052-Bausteine: 12 Testdateien mit
  minimalen/bare Test-Handlern (`object.__new__(HandlerClass)`,
  `SimpleNamespace`) mussten um `handler._runtime = RuntimeState()`
  ergaenzt werden - mehr als bei `DirtyState`/`ToolTableState`, weil
  `_ui_loading` bisher ueberall defensiv gelesen wurde und dadurch auf
  fehlenden Testattributen nie sichtbar auffiel.
- 3 neue eigenstaendige Tests (`tests/test_runtime_state.py`) - anders als
  bei `DirtyState`/`ToolTableState` ohne Regressionsverifikation per
  absichtlich entfernter Logik, da die Klasse selbst keine Methoden
  enthaelt (alles reentranz-relevante Verhalten blieb unveraendert an den
  Aufrufstellen, durch den vollen Testlauf ueber alle betroffenen Module
  abgedeckt).
- 898 Stub-/108 Real-Qt-Tests bestanden (895 vorher + 3 neue). Standalone-
  Panel offscreen sauber gestartet, kein `AttributeError` im Log. Details:
  TODO.md/`doc/PANEL_ARCHITECTURE.md` (LES-052).

### LES-052: ToolTableState gekapselt 2026-09-17

- Dritter LES-052-Baustein: `handler.tools` (ein rohes `Dict[int, Tool]`)
  plus zwei bei der ersten Bestandsaufnahme uebersehene lose Attribute
  (`_loaded_tools`, `_missing_iso_tools`) durch eine einzelne Qt-freie
  Klasse `ToolTableState` (`tool_table_state.py`) ersetzt, jetzt als
  `handler._tool_table` gehalten.
- `_loaded_tools` ist der Cache der zuletzt geladenen NICHT-leeren Tabelle
  fuer das Nachbefuellen von erst spaeter (lazy) auftauchenden Werkzeug-
  Combo-Widgets; `set_tools()` kapselt exakt die bisherige "leere Tabelle
  ueberschreibt den Cache nicht"-Logik aus
  `ui_tools.py::populate_tool_combos()`. `_missing_iso_tools` (die von
  `parse_tool_table()` gelieferten ISO-Warnungen) war schon vor der
  Kapselung ein reines Schreib-Attribut ohne Leser - hier bewusst nicht
  "repariert", nur unveraendert mituebernommen.
- `handler.tool_table_path` (der angezeigte Dateipfad-Text) bleibt bewusst
  aussen vor - das ist Qt-View-Zustand, keine Fachdaten.
- Alle neun betroffenen Aufrufstellen (`tool_logic.py`, `ui_flow.py`,
  `ui_persistence.py`, `ui_preview.py`, `ui_tools.py`,
  `lathe_easystep_handler.py`) mussten nur ihren direkten Attributzugriff
  von `handler.tools`/`handler._loaded_tools` auf
  `handler._tool_table.tools`/`handler._tool_table.loaded_tools`
  umstellen, keine strukturellen Aenderungen.
- 4 neue eigenstaendige Tests (`tests/test_tool_table_state.py`), per
  absichtlich entferntem Leer-Dict-Schutz als echte Regression
  verifiziert (die "leere Tabelle ueberschreibt den Cache nicht"-Logik
  schlug korrekt fehl, als der Schutz entfernt wurde).
- 895 Stub-/108 Real-Qt-Tests bestanden (891 vorher + 4 neue).
  Standalone-Panel-Log bestaetigt den echten Ladepfad: `tool.tbl`
  automatisch geladen, Combos befuellt, kein `AttributeError`. Details:
  TODO.md (LES-052).

### LES-052: DirtyState gekapselt 2026-09-16

- Zweiter LES-052-Baustein: die fuenf bisherigen Handler-Attribute
  (`_dirty_operation_indices`, `_program_dirty`, `_dirty_program_header`,
  `_dirty_program_structure`, `_dirty_warning_suppressed`) durch eine
  einzelne Qt-freie Klasse `DirtyState` (`dirty_state.py`) ersetzt, jetzt
  als `handler._dirty` gehalten.
- `ui_dirty.py`s freie Funktionen bleiben mit unveraenderter Signatur als
  duenne Adapter bestehen (Koerper delegiert an Methoden auf `DirtyState`)
  - alle Aufrufstellen ausserhalb von `ui_dirty.py` (`ui_flow.py`,
  `ui_persistence.py`, `ui_selection.py`, `lathe_easystep_handler.py`)
  mussten deshalb nicht umgebaut werden; nur der direkte Attributzugriff
  wurde von `handler._dirty_xxx` auf `handler._dirty.xxx` umgestellt.
- 14 neue eigenstaendige Tests (`tests/test_dirty_state.py`) decken die
  Klasse Qt-frei und unabhaengig von der Handler-Integration ab. Per
  absichtlich entfernter Nachzieh-Arithmetik zweimal als echte Regression
  verifiziert: einmal fuer `reindex_after_removal()` (die Methode hinter
  dem SICHERHEITSFUND 2026-09-13), einmal fuer die abgeleitete
  `program_dirty`-Logik in `clear_program()`.
- Dabei nebenbei entdeckt: `RuntimeState` hat tatsaechlich neun statt der
  in der ersten Bestandsaufnahme notierten zwei Flags -
  `lathe_easystep_handler.py`s `__init__` setzt zusaetzlich zu
  `_ui_loading` noch `_loading_step`, `_deleting`, `_saving_step`,
  `_saving_changes`, `_moving_up`, `_moving_down`, `_generating_gcode`
  und `_creating_new_program` direkt auf `self`. `doc/PANEL_ARCHITECTURE.md`
  entsprechend korrigiert.
- 891 Stub-/108 Real-Qt-Tests bestanden (877 vorher + 14 neue). Standalone-
  Panel offscreen sauber gestartet, kein `AttributeError` im Log. Details:
  TODO.md (LES-052).

### LES-052: Zustandsmodell-Bestandsaufnahme 2026-09-16

- Erster LES-052-Baustein ("Architektur und Ladevertrag"): die sechs
  genannten Zustandskategorien (`ProgramState`, `OperationState`,
  `ToolTableState`, `ViewState`, `DirtyState`, `RuntimeState`) gegen den
  tatsaechlichen Code geprueft und in `doc/PANEL_ARCHITECTURE.md`
  dokumentiert - reine Bestandsaufnahme, kein Code veraendert.
- `ProgramState`/`OperationState` (`model.py`) und `MotionState`/
  `SpindleState` (`motion_state.py`) sind bereits sauber gekapselt. Drei
  Kategorien sind es nicht: `ToolTableState` (`handler.tools`-Dict, direkt
  von `ui_tools.py` gesetzt), `DirtyState` (fuenf Attribute direkt auf dem
  Handler, von neun Modulen gelesen/geschrieben) und `RuntimeState`
  (`_generating_gcode`/`_ui_loading`, ebenfalls lose Handler-Attribute).
- `DirtyState` hat dabei nachweislich die groesste Dringlichkeit: die
  Index-Nachzieh-Logik in `ui_dirty.py` traegt an zwei Stellen den
  Kommentar "SICHERHEITSFUND 2026-09-13" fuer bereits real aufgetretene
  Bugs durch genau dieses Streuungsmuster (ein dirty-Flag "wanderte" beim
  Verschieben einer Operation auf den falschen Nachbar-Step).
  `ViewState` (Zoom/Pan/Slice/Ansichtsmodus) ist auf `LathePreviewWidget`
  immerhin lokal gebuendelt, aber ungetypt.
- Details: TODO.md (LES-052).

## [0.8.0] - 2026-09-16

### Realtest 17: Innenbearbeitung-Richtungsvergleich in der LinuxCNC-SIM 2026-09-16

- Letzter offener 0.8.0-Blocker: der LinuxCNC-Backplot-Nachweis, dass die
  Punktreihenfolge einer Innenkontur (steigend vs. fallend in Z) keinen
  Einfluss auf den erzeugten G-Code/Materialabtrag hat. Die algorithmische
  Richtungsunabhaengigkeit war seit 2026-08-22 bereits automatisiert
  getestet (`is_monotonic_z()`, `test_internal_roughing_never_uses_g71_
  g72_cycle`); offen war nur noch der reale SIM-/Backplot-Nachweis.
- Testpaar aus der bestehenden 43-Matrix regeneriert:
  `inside_step_forward_rough_finish.ngc`/`inside_step_reverse_rough_
  finish.ngc` (identisches Stufenprofil `[(12,-30),(12,-15),(18,-15),
  (18,0)]`, einmal in Original- und einmal in umgekehrter Punktreihenfolge,
  Schruppen+Schlichten kombiniert). G-Code-Diff ausserhalb des
  Programmnamens: nur die Schlichtbahn durchlaeuft dieselbe Kontur in
  umgekehrter Richtung, alle Schrupppaesse sind byte-identisch.
- Beide Programme in der nativen QtDragon-SIM (`linuxcnc lathe.ini`)
  vollstaendig im AUTO-Modus bis `M30` ausgefuehrt: 187,1 s (vorwaerts)
  bzw. 186,2 s (rueckwaerts), je leerer NML-Fehlerkanal, identische
  Endposition (X150.000/Z300.000 Werkzeugwechselpunkt), Backplot beider
  Richtungen visuell deckungsgleich. XRI (X9.000) kommt in beiden
  Programmen ausschliesslich als `G0`-Rueckzug vor, nie als Schnittbahn.
  Gesteuert ueber das `linuxcnc`-Python-Modul (NML-Status-/Kommando-API)
  statt GUI-Dateibrowser, nachdem sich dessen "User"-Panel trotz "All (*)"-
  Filter und deaktiviertem "Restricted" als reiner Verzeichnis- statt
  Datei-Browser erwies - robuster und fuer den zweiten Lauf per Skript
  sofort als echter Regressionsfund nutzbar (siehe naechster Punkt).
- Dabei zwei reale Fehler ausserhalb des LatheEasyStep-Codes gefunden und
  behoben:
  - `lathe_postgui.hal` der SIM-Konfiguration (ausserhalb dieses Repos,
    `/home/adm1n/linuxcnc/configs/sim.qtdragon_lathe.basic_xz_lathe-1/`)
    verband zwei rein kosmetische Achslast-/Drehzahl-Anzeigen
    (`joint.N.vel-cmd`/`spindle-speed-limited`, beide `float`) mit
    `qtdragon.axis-*-load`/`qtdragon.spindle-rpm`, die in der installierten
    QtDragon-Version jetzt `s32` sind - liess den SIM-Start hart mit
    `Signal ... of type 'float' cannot add pin ... of type 's32'`
    abbrechen. Beide Netze auskommentiert (Backup unter
    `/tmp/lathe_postgui.hal.orig.bak`), keine Bewegungs-/Koordinatenlogik
    betroffen.
  - Eigenes Steuerskript: der zweite (Rueckwaerts-)Lauf meldete zunaechst
    faelschlich "fertig nach 1,0 s" ohne echte Bewegung - `c.mode(MODE_
    AUTO)` griff nach dem ersten `M30` nicht mehr zuverlaessig, `c.auto(
    AUTO_RUN, ...)` wurde im noch aktiven MANUAL-Modus stillschweigend
    ignoriert. Behoben durch expliziten Moduswechsel unmittelbar vor
    `AUTO_RUN` mit Ruecklesepruefung (`task_mode == MODE_AUTO`) sowie eine
    Abschlusspruefung, die eine tatsaechliche Positionsaenderung
    voraussetzt, bevor "fertig" gemeldet wird - Wiederholung lief korrekt
    186,2 s mit echter Bewegung.
- Realtest-17-Eintrag aus `doc/REALTEST_FRAGEN_2026-07-15.md` entfernt
  (Datei-eigene Konvention: beantwortete/umgesetzte Punkte werden hier
  dokumentiert statt dort offengehalten).
- Damit ist der letzte 0.8.0-Blocker geschlossen. Alle Abnahmekriterien aus
  `ROADMAP.md` gegengeprueft (Referenzfaelle, gemeinsame Primitive,
  Freistich-in-Kontur, kein ungenutzter Generator-Pfad, CSS-Position,
  Planen-Radius, Parserannahme, SIM-/Backplot-Nachweise) - Details dort
  unter "Aktueller Release-Gate-Status". `0.8.0-dev` ist damit inhaltlich
  freigabefertig; der Release-Schritt selbst (Merge nach `main`,
  Versionsbump, Tag) steht noch aus.
- 877 Stub-/108 Real-Qt-Tests weiterhin bestanden (unveraendert durch diese
  reine Verifikationsarbeit).

### 0.8.0 Release-Gate gegen vorhandene Realnachweise korrigiert 2026-09-16

- Die neu angelegte Gate-Liste hatte zwei bereits abgeschlossene SIM-Abnahmen
  irrtuemlich wieder geoeffnet. Planen-Radius ist seit 2026-09-14 mit 272,6 s
  AUTO-Lauf bis `M30`, leerem NML-Fehlerkanal und lesbarem Backplot belegt.
  DIN-76-Aussen/-Innengewinde sind seit 2026-09-12 mit 103 s/122 s echten
  QtDragon-SIM-Laeufen bis Programmende und geprueftem Backplot belegt.
- Diese Punkte aus den offenen Realtest-Fragen entfernt und TODO/Roadmap auf
  den tatsaechlichen verbleibenden Blocker reduziert: Richtungsvergleich der
  Innenkontur in der LinuxCNC-SIM, danach abschliessender Gate-Audit.
- Release-Pruefungen frisch wiederholt: alle zwoelf Referenzen deterministisch
  ohne Git-Diff regeneriert, 96 statische NGC-Pruefungen, zwoelf Referenzen und
  43 Matrixfaelle mit `/usr/bin/rs274`, 877 Stub-Qt- und 108 Real-Qt-Tests ohne
  Skips bestanden.

### LES-044: verbleibende `except Exception`-Fallbacks in ui_preview.py begrenzt 2026-09-16

- Dritter und letzter Baustein: vier der sechs zuvor bewusst offen
  gelassenen Fachlogik-Vorkommen in `collect_preview_state()`/
  `_detect_preview_collision()` nach genauerer Einzelpruefung doch
  begrenzt - `_current_op_type()`/`_collect_params()` auf
  `(RuntimeError, AttributeError)` (beide lesen ein Handler-Attribut
  ohne `getattr()`-Fallback: `self.tab_params` bzw.
  `self.param_widgets`), die sechs Vorschau-Builder-Aufrufe (`build_
  face_path` u. a.) auf `(TypeError, ValueError, IndexError)` (rechnen
  mit `params`-Werten, die `collect_params()` bei nicht als Zahl
  parsbarem Text roh als String ablegt), `_detect_preview_collision()`
  auf `(TypeError, ValueError, IndexError, AttributeError)` (liest
  primitive-Dicts per `.get()`/Indexzugriff, entpackt p1/p2/points als
  (x, z)-Paare).
- Jede der vier Begrenzungen per Monkeypatch in beide Richtungen
  verifiziert: eine synthetische `KeyError` propagiert korrekt statt
  geschluckt zu werden, die tatsaechlich erwartete Ausnahme (zu kurzes
  `p1`, ein `None`-Punkt, ein fehlendes `tab_params`-Attribut auf einem
  minimalen Test-Handler) wird weiterhin sauber abgefangen - diesmal im
  ersten Anlauf gruen, ohne den Fehltritt wie beim zweiten Baustein.
- Die verbleibenden zwei Vorkommen (Warnungs-Aggregation aus drei
  unabhaengigen Funktionen; Rohteil-/Rueckzugs-/Worklimit-/Sperrzonen-
  Builder-Aufrufe) bleiben bewusst breit und sind entsprechend
  kommentiert - sie aggregieren mehrere unabhaengige Funktionen mit
  Fehlerursachen, die sich ohne tiefere Einzelpruefung jeder einzelnen
  nicht verlaesslich eingrenzen lassen, und betreffen ohnehin nur die
  Vorschau-/Warnungsanzeige, nie die G-Code-Erzeugung.
- Damit ist diese Aufgabe fuer `preview_widget.py`/`ui_preview.py`
  abgeschlossen: 36 von 40 urspruenglichen `except Exception`-Vorkommen
  begrenzt, 4 bewusst breit mit dokumentierter Begruendung. Andere Module
  (`ui_header.py`, `ui_params.py` usw.) wurden nicht durchsucht - ausserhalb
  des LES-044-Vorschau-Umfangs.
- 877 Stub-/108 Real-Qt-Tests bestanden. Standalone-Panel offscreen bis
  `_finalize_ui_ready DONE` sauber gestartet. Details: TODO.md (LES-044).

### LES-044: `except Exception`-Fallbacks in ui_preview.py einzeln bewertet 2026-09-16

- Zweiter Baustein derselben Aufraeumung: `ui_preview.py` (32 Vorkommen).
  26 davon liessen sich begrenzen - durchgaengig Qt-Widget-Methodenaufrufe
  auf `handler.preview`/`preview_slice`/`btn_slice_view`/`btn_reset_view`
  oder auf per `_get_widget_by_name()` ermittelte Objekte:
  `(RuntimeError, AttributeError)` (RuntimeError bei einem zwischen Lookup
  und Aufruf zerstoerten C++-Qt-Objekt, AttributeError bei fehlender
  Methode/fehlendem Attribut), bei `.connect()`-Aufrufen zusaetzlich
  `TypeError`.
- Dabei zwei echte Fehleinschaetzungen gemacht und durch den vollen
  Testlauf sofort gefunden, nicht nur durch Ueberlegung: `update_slice_
  view_button()`s `button.setText()`/`setToolTip()` zunaechst nur auf
  `RuntimeError` begrenzt - ein minimaler Test-Stub ohne `setToolTip()`
  (uebliches Testmuster in diesem Projekt) loeste tatsaechlich ein
  `AttributeError` aus und liess `test_keyway_preview.py::test_toggle_
  slice_view_switches_main_preview_mode` fehlschlagen. Ebenso `_current_
  language_code()`s eigener `get_widget_by_name()`-Aufruf: liest
  `self.root_widget` ohne `getattr()`-Fallback - auf einem
  `object.__new__(HandlerClass)`-Test-Handler ohne dieses Attribut
  ebenfalls ein `AttributeError`, kein `RuntimeError`. Beide Male die
  Ausnahmeliste korrigiert, erneut den vollen Testlauf geprueft (877
  Stub-/108 Real-Qt-Tests gruen). Lehre: bei diesem Muster IMMER
  `AttributeError` mitfangen, nie nur `RuntimeError` allein - Test-Stubs
  in diesem Projekt implementieren durchgehend nur die Methoden, die der
  jeweilige Test braucht.
- Zusaetzlich per Monkeypatch (wie beim ersten Baustein) fuer
  `setup_slice_view()`/`on_toggle_slice_view()` verifiziert: eine
  synthetische `KeyError` propagiert korrekt (statt geschluckt zu
  werden), eine echte `RuntimeError` wird weiterhin sauber abgefangen.
- Die restlichen sechs Vorkommen (`_current_op_type()`/`_collect_params()`/
  die Vorschau-Builder-Aufrufe/die Warnungs-Aggregation/die Rohteil-/
  Rueckzugs-/Sperrzonen-Builder in `collect_preview_state()` sowie
  `_detect_preview_collision()`) bleiben bewusst offen - Fachlogik mit
  vielfaeltigen, nicht auf den ersten Blick eingrenzbaren Fehlerursachen
  ueber viele verschiedene Operationstypen hinweg, anders als die
  mechanisch gleichfoermigen Qt-Widget-Aufrufe dieses Schritts.
- 877 Stub-/108 Real-Qt-Tests bestanden. Standalone-Panel offscreen bis
  `_finalize_ui_ready DONE` sauber gestartet, kein Verbindungsfehler im
  Log (`slice toggle connect failed` u. ae. traten nicht auf). Details:
  TODO.md (LES-044).

### LES-044: `except Exception`-Fallbacks in preview_widget.py einzeln bewertet 2026-09-16

- Alle acht Vorkommen in `preview_widget.py` einzeln bewertet (erster
  Baustein - `ui_preview.py` mit 32 weiteren Vorkommen folgt separat).
- Zwei sicher begrenzt: `_debug_slice()` (nur `print()`, jetzt
  `(OSError, UnicodeError)`) und `set_primitives()` (liest primitive-Dicts
  per `tuple()`/Indexzugriff, jetzt `(TypeError, ValueError, IndexError)`).
  Per Monkeypatch verifiziert: eine synthetische `AttributeError` wird
  korrekt NICHT mehr geschluckt, sondern propagiert - die Begrenzung ist
  nicht nur enger, sondern tatsaechlich praezise. Neuer Stub-unabhaengiger
  Real-Qt-Test `test_set_primitives_with_malformed_line_ignores_it_
  without_crash` (`tests/test_preview_widget_paint_no_crash.py`).
- Zwei bleiben bewusst breit und sind jetzt entsprechend kommentiert:
  `sliceChanged.emit()`/`_slice_change_callback()` in `set_slice_z()` rufen
  synchron beliebigen verbundenen Fremdcode auf, dessen Ausnahmeklassen
  ausserhalb der Kontrolle dieser Methode liegen.
- Die restlichen vier (`paintEvent()`-interne QPainter-Bloecke) bleiben
  ebenfalls bewusst breit, aber aus einem waehrenddessen entdeckten,
  wichtigeren Grund: eine unbehandelte Ausnahme in `paintEvent()` beendet
  unter echtem PyQt5 nicht nur den Zeichenvorgang, sondern den gesamten
  Prozess (empirisch reproduziert - ein absichtlich entfernter Datenvertrag-
  Schluessel liess den Real-Qt-Testlauf hart abstuerzen statt einen Test
  fehlschlagen zu lassen).
- Dabei eine echte Luecke gefunden und geschlossen: die "slice"/"front"-
  Zweige in `paintEvent()` hatten bislang GAR kein Exception-Netz (nur
  `finally: painter.end()`) - jetzt wie der "side"-Zweig mit
  `except Exception` abgesichert, damit ein kuenftiger Regressionsfund dort
  nicht das ganze Panel abstuerzen laesst.
- Damit dieses neue Sicherheitsnetz einen echten Bug nicht nur noch still
  verschluckt (statt ihn wie zuvor als Absturz sichtbar zu machen), pruefen
  die bestehenden Real-Qt-Paint-Tests jetzt zusaetzlich per `caplog`, dass
  `paintEvent()` keine unterdrueckte Ausnahme geloggt hat.
- Per entferntem Datenvertrag-Schluessel als echte Regression verifiziert:
  vor der Aenderung Prozessabsturz, danach sauberer, `caplog`-basierter
  Testfehlschlag.
- 877 Stub-/108 Real-Qt-Tests bestanden. Standalone-Panel offscreen bis
  `_finalize_ui_ready DONE` sauber gestartet. Details: TODO.md (LES-044).

### LES-044: verbleibende "Chrome"-Farben des Preview-Widgets als Datenvertrag 2026-09-16

- Letzter Schritt derselben Aufraeumung: alle noch direkt in
  `preview_widget.py` hartkodierten `QColor`/`QtCore.Qt.<Style>`/
  `QtCore.Qt.white`-Werte, die keiner semantischen Rolle zugeordnet sind
  (Achsen, Gitterticks/-beschriftung, Schnittlinie/-label der Seiten-
  ansicht, Legenden-Rahmen/-Hintergrund/-Text, Vorderansichts-Achsen/-
  Infotext, Keilnut-Overlay-Umriss/-Fuellung, Kreis/Text der
  Schnittansicht) in `PREVIEW_CHROME_STYLES`/`PREVIEW_CHROME_FILLS`
  (`preview_geometry.py`) verschoben.
- Zwei neue Hilfsmethoden `_chrome_pen()`/`_chrome_fill()` auf
  `LathePreviewWidget` buendeln die Qt-Adaption (Stil-Mapping weiterhin
  lokal im Methodenkoerper, nicht Modulebene - siehe fruehere Eintraege
  in diesem Abschnitt).
- Dabei eine echte Testluecke geschlossen: `_paint_slice_view()` (die
  Schnittansicht mit rundem Werkstueckquerschnitt) hatte bislang keinen
  Real-Qt-Test. Neuer Test `test_slice_view_paints_without_crash`
  (`tests/test_preview_widget_paint_no_crash.py`) deckt sie jetzt ab.
- Per entferntem Schluessel als echte Regression verifiziert: im Stub-Test
  ein sauberer `AssertionError`, im Real-Qt-Test dagegen ein harter
  Prozessabsturz - PyQt5 kann eine unbehandelte Python-`KeyError` aus
  `paintEvent()` nicht sauber propagieren. Beide Male wie erwartet
  fehlgeschlagen, danach beide Male gruen nach Wiederherstellung.
- Einzig verbliebenes Farbliteral in `preview_widget.py`: der schwarze
  Canvas-Hintergrund (`QtCore.Qt.black`, dreimal identisch verwendet) -
  bewusst nicht extrahiert, da eine einzelne, ueberall gleiche Konstante
  kein Duplizierungsrisiko traegt.
- 877 Stub-/107 Real-Qt-Tests bestanden. Standalone-Panel offscreen bis
  `_finalize_ui_ready DONE` sauber gestartet. Details: TODO.md (LES-044).

### LES-044/LES-051: Vorderansicht-Ringe/-Fuellungen als austauschbarer Datenvertrag 2026-09-16

- Gleiche Aufraeumung wie beim Haupt-Vorschau-Canvas, jetzt fuer
  `_paint_front_view()`: `FRONT_VIEW_RING_STYLES` (Rohteil-Aussen-/
  Innendurchmesser, sichtbare Aussen-/Innen-Durchmesserringe, aktiver Ring)
  und `FRONT_VIEW_FILL_COLORS` (Endkontur-Fuellung/-Loch, RGBA wegen
  Transparenz) in `preview_geometry.py` decken alle sieben `style_key`-
  Werte ab, die `build_front_view_draw_plan()` (`preview_scene.py`)
  erzeugen kann - vorher direkt als `QColor`/`QtCore.Qt.<Style>`/
  `QtCore.Qt.black` in `preview_widget.py` hartkodiert.
- Zwei weitere Stub-Tests pruefen, dass beide Datenvertraege genau die von
  `build_front_view_draw_plan()` moeglichen Schluessel abdecken (ein
  fehlender wuerde `_paint_front_view()` mit `KeyError` abstuerzen lassen) -
  per entferntem Schluessel als echte Regression verifiziert.
- Kein separater Standalone-Klicktest fuer die Vorderansicht noetig: die
  bereits bestehenden, weiterhin gruenen Real-Qt-Tests
  `test_front_view_paints_external_abspanen_without_crash`,
  `test_front_view_paints_internal_abspanen_without_crash` und
  `test_front_view_paints_keyway_without_crash`
  (`tests/test_preview_widget_paint_no_crash.py`) durchlaufen
  `_paint_front_view()` bereits mit echtem PyQt5 und decken damit den
  neuen Ring-/Fuellungs-Code ab. Standalone-Panel offscreen bis
  `_finalize_ui_ready DONE` sauber gestartet.
- 875 Stub-/106 Real-Qt-Tests bestanden. Die uebrigen Qt-Farbliterale in
  `preview_widget.py` (Achsen/Gitterticks, Legende-/Status-Box-Rahmen,
  Keilnut-Overlay, Schnittlinie) sind Chrome/Struktur statt semantischer
  Rollen-Stile und bleiben bewusst offen - siehe TODO.md (LES-044).

### LES-051: Haupt-Vorschau-Canvas als austauschbarer Datenvertrag 2026-09-15

- Dritter Baustein derselben Aufraeumung: der Haupt-Vorschau-Canvas
  (Seitenansicht) selbst. `PREVIEW_DRAW_STYLES` (`preview_geometry.py`)
  deckt alle elf `style_key`-Werte ab, die `build_preview_draw_plan()`
  erzeugen kann (Werkstueck, Werkzeugweg, Rohteil, Rueckzug, Futter-
  Sperrzone, Schruppkontur, Freistich, aktiv, Hilfsgeometrie und zwei
  weitere Feature-Varianten) - vorher direkt als `QColor`- und
  Linienstil-Werte in `paintEvent()` hartkodiert.
- Zwei der Eintraege waren zuvor als Qt-Farbnamen ("gray"/"red"/"lime")
  statt RGB-Tripel hinterlegt; fuer Konsistenz mit `LEGEND_ENTRIES`/
  `STATUS_BOX_STYLE` auf die per Laufzeitpruefung bestaetigten RGB-
  Aequivalente umgestellt (`gray=(128,128,128)`, `red=(255,0,0)`,
  `lime=(0,255,0)`) - keine sichtbare Aenderung.
- Ein weiterer Stub-Test prueft, dass der Datenvertrag genau die von
  `build_preview_draw_plan()` moeglichen Schluessel abdeckt (ein
  fehlender wuerde `paintEvent()` mit `KeyError` abstuerzen lassen) - per
  entferntem Schluessel als echte Regression verifiziert.
- Kein separater Standalone-Klicktest: das Hinzufuegen eines Schritts per
  synthetischem X11-Klick liess sich in dieser Sitzung wiederholt nicht
  zuverlaessig ausloesen. Stattdessen den bereits bestehenden, erneut
  gruenen Real-Qt-Test `test_side_view_paints_expanded_legend_and_status_
  messages_without_crash` als staerkeren Nachweis herangezogen - er
  durchlaeuft denselben `styles`-Dict/`draw_plan`-Code mit echten
  synthetischen Pfaden.
- 873 Stub-/106 Real-Qt-Tests bestanden. Details: TODO.md (LES-051).

### LES-051: Status-/Warnungsbox als austauschbarer Datenvertrag 2026-09-15

- Zweiter Baustein derselben Aufraeumung (nach der Legende unmittelbar
  zuvor): Rand-, Fuell- und Textfarbe sowie die Kopfzeile "Warnungen" der
  Status-/Warnungsbox waren direkt als `QColor`-Konstruktion in
  `paintEvent()` hartkodiert. Neuer, reiner Datenvertrag
  `STATUS_BOX_STYLE` (`preview_geometry.py`); `paintEvent()` konstruiert
  daraus nur noch die Qt-Objekte. Keine sichtbare Aenderung.
- Ein weiterer Stub-Test (`tests/test_preview_legend_and_status_layout.py`):
  der Datenvertrag ist Qt-frei mit genau den erwarteten Schluesseln. Per
  eingefuegtem unerwartetem Schluessel als echte Regression verifiziert.
- 872 Stub-/106 Real-Qt-Tests bestanden. Kein separater Standalone-Check -
  identisches, bereits live bestaetigtes Extraktionsmuster wie die Legende,
  keine neue Risikoflaeche. Details: TODO.md (LES-051).

### LES-051: Vorschau-Legende als austauschbarer Datenvertrag 2026-09-15

- Erster Baustein fuer "weitere austauschbare Panelbereiche identifizieren"
  (Preview-Canvas, Legende, Status-/Warnungsbox, optionale Bedienelemente):
  die 10 Legenden-Eintraege (Label, RGB-Farbe, Linienbreite, Stilname) waren
  bisher direkt als `QPen`/`QColor`-Konstruktion in `paintEvent()`
  hartkodiert. Neuer, reiner Datenvertrag `LEGEND_ENTRIES`
  (`preview_geometry.py`); `paintEvent()` (`preview_widget.py`) baut daraus
  nur noch die Qt-Objekte (derselbe Qt-Adapter-Zuschnitt wie beim
  `ToolVisualProvider`). Keine sichtbare Aenderung - exakt dieselben Werte,
  nur umgezogen. Bewusst nicht gleichzeitig uebersetzt (die Legende war
  schon vorher ungebunden an `_tr()`, siehe LES-044 - eigenes Thema).
- Echter Regressionsfund waehrend der Umsetzung: ein Modulebenen-Dict fuer
  das Stil-Mapping (`QtCore.Qt.SolidLine` usw.) haette den Import von
  `preview_widget.py` in der Stub-Qt-Suite gebrochen (`QtCore.Qt` ist dort
  ein leeres Fake-Namespace-Objekt ohne diese Attribute) - 28
  Testdateien haetten beim Sammeln fehlgeschlagen. Sofort behoben, indem
  das Mapping lokal in `paintEvent()` bleibt (genau wie vorher).
- Zwei neue Stub-Tests (`tests/test_preview_legend_and_status_layout.py`):
  der Datenvertrag ist Qt-frei und hat eindeutige Label,
  `legend_layout()`-Zeilenzahl passt zur Eintragsanzahl. Per absichtlich
  dupliziertem Label als echte Regression verifiziert. Live im Standalone-
  Panel bestaetigt: Legende sieht unveraendert aus, kein Fehler im Log.
  871 Stub-/106 Real-Qt-Tests bestanden. Details: TODO.md (LES-051).

### LES-051: G-Code-Unabhaengigkeit des Ressourcenwechsels end-to-end belegt 2026-09-15

- Letzter Satz des LES-051-Abnahmekriteriums ("Austauschen einer
  Schneidplatten-Grafik darf weder Operationen, Werkzeugdaten, G-Code,
  Preview-Geometrie noch Dirty-/Save-State veraendern") war fuer
  Werkzeugdaten bereits per `asdict(tool)`-Vergleich getestet, fuer G-Code
  aber nur architekturell (kein Import von `tool_visuals`/`render_tool_
  preview` in `gcode_*.py`/`checks.py`) belegt, nicht als expliziter Test.
- Neuer Test `test_switching_tool_visual_resource_never_affects_generated_
  gcode` (`tests/test_tool_preview_layout.py`): erzeugt dasselbe
  Beispielprogramm zweimal, mit einer voellig unabhaengigen
  `render_tool_preview()`-Ausfuehrung samt externer PNG-Ressource
  dazwischen - identischer G-Code-Output.
- Per absichtlich veraendertem Operationsparameter (statt der Ressource) als
  echte Regression verifiziert: der Test schlaegt korrekt fehl, sobald sich
  der erzeugte G-Code tatsaechlich unterscheidet (Diff exakt an der
  erwarteten Stelle: `F99.000` statt `F0.100`).
- 869 Stub-/106 Real-Qt-Tests bestanden. Details: TODO.md (LES-051).

### LES-051: Werkzeugressourcen an Qt-Vorschau angebunden 2026-09-15

- `render_tool_preview()` fragt nun vor der bisherigen prozeduralen Zeichnung
  den neutralen `ToolVisualProvider` ab. Gueltige PNG-/SVG-Ressourcen werden
  seitenverhaeltnistreu in die unveraenderte 140-x-140-Ausgabe eingepasst.
- Fehlende oder nicht dekodierbare konfigurierte Dateien fallen auf die
  prozedurale Darstellung zurueck, werden geloggt und erhalten als sichtbare
  Diagnose ein orangefarbenes Ausrufezeichen. Ohne konfiguriertes Theme bleibt
  die bisherige Darstellung unveraendert.
- Drei neue Real-Qt-Tests sichern externe PNG-Ausgabe, fehlende Ressource,
  Dekodierfehler und unveraenderte Werkzeugdaten. Nebenbei einen bereits
  vorhandenen unausgeglichenen `QPainter.save()`-Zustand korrigiert.
- Gesamtstand: 869 Stub-Qt- und 105 Real-Qt-Tests, keine Skips. Standalone-Panel
  bis `critical done` nach 2,337 s gestartet und sauber beendet; G-Code und
  Fahrwege sind unveraendert, daher kein LinuxCNC-Lauf erforderlich.

### LES-051: neutraler Providervertrag fuer Werkzeugdarstellungen 2026-09-15

- Neues Qt-freies Modul `tool_visuals.py`: `ToolVisualRequest` beschreibt eine
  Darstellung ohne Abhaengigkeit von `Tool`, Operation oder Widget;
  `ToolVisualProvider` loest logische Manifest-Schluessel innerhalb eines
  getrennten Theme-Verzeichnisses auf.
- ISO-spezifische, Form-/Seiten-, Familien- und Default-Eintraege besitzen eine
  definierte Prioritaet. PNG und SVG sind zugelassen; absolute Pfade,
  Verzeichnisausbrueche, unbekannte Formate und fehlende Dateien fuehren zum
  prozeduralen Fallback mit Diagnose.
- Besitz- und Abhaengigkeitsgrenzen sind in `doc/PANEL_ARCHITECTURE.md`
  festgehalten. Fuenf Tests sichern alternative Ressourcensaetze, fehlende und
  ungueltige Ressourcen sowie unveraenderte Werkzeugdaten.
- Gesamtstand: 869 Stub-Qt- und 102 Real-Qt-Tests, keine Skips. Noch keine
  Qt-Anbindung und damit keine Aenderung am sichtbaren Panel, G-Code oder
  Maschinenverhalten; ein Standalone-/LinuxCNC-Start war nicht erforderlich.

### LES-044/LES-052: numerische Vorschau-Fehlergrenzen verengt 2026-09-15

- Fuenf reine Zahlenkonvertierungen in `preview_widget.py` fangen nur noch
  erwartete ungueltige Eingaben (`TypeError`, `ValueError`, `OverflowError`)
  ab. Unerwartete Programmierfehler werden nicht mehr still als Nullwert oder
  ausgelassener Punkt verborgen.
- Vier Regressionstests sichern beide Seiten der Fehlergrenze: ungueltige
  Benutzerwerte behalten die bisherigen sicheren Fallbacks, waehrend eine
  unerwartete `RuntimeError` sichtbar bleibt.
- Gesamtstand: 864 Stub-Qt- und 102 Real-Qt-Tests, keine Skips. Standalone-Panel
  bis `critical done` nach 2,202 s gestartet und sauber beendet; kein
  LinuxCNC-Start erforderlich.

### LES-044: Vorderansichts-Kreise als fertiger Bildschirmplan 2026-09-15

- Neue Qt-freie Funktion `build_front_view_screen_plan()` wandelt die
  semantischen Durchmesserkreise in Mittelpunkt und Pixelradius um und teilt
  sie zugleich in die drei bestehenden Zeichenphasen Rohteil, Fuellung und
  Ringe. Die Keilnut bleibt unveraendert zwischen Fuellung und Ringen.
- `preview_widget.py` berechnet keine Kreisradien und filtert keine
  Vorderansichtsphasen mehr; es weist nur noch Qt-Stifte/-Pinsel zu und zeichnet
  den Plan. Ein neuer Stub-Test sichert Pixelradien, Mittelpunkt und Reihenfolge.
- Gesamtstand: 860 Stub-Qt- und 102 Real-Qt-Tests, keine Skips. Standalone-Panel
  bis `critical done` nach 2,187 s gestartet und sauber beendet; kein
  LinuxCNC-Start erforderlich.

### LES-044: Pfad-/Primitive-Abbildung aus Paint-Code geloest 2026-09-15

- `side_points_to_screen()` und `side_strokes_to_screen()` bilden normale
  Polylinien sowie getrennte Primitive Qt-frei auf Bildschirmkoordinaten ab;
  die Trennung einzelner Strokes bleibt dabei explizit erhalten, sodass keine
  erfundenen Verbindungslinien entstehen.
- `point_cross_lines()` liefert die beiden Linien fuer die Markierung eines
  einzelnen Punkts. Auch die gefuellte Futter-Sperrzone verwendet nun dieselbe
  gemeinsame Punktabbildung. `paintEvent()` erzeugt fuer diese Faelle nur noch
  Qt-Punkte und zeichnet sie.
- Zwei neue Stub-Tests sichern Durchmesserabbildung, getrennte Strokes,
  unveraenderte Eingaben und Punktkreuz. Vollstaendige Suite real gezaehlt:
  859 Stub-Qt- und 102 Real-Qt-Tests, keine Skips. Dabei eine rein
  dokumentarische Alt-Abweichung gefunden: Die beiden vorigen LES-032-Eintraege
  hatten jeweils zwei Tests zu viel fortgeschrieben (korrekt waren 850 statt
  852 und danach 857 statt 859); die zwei neuen Tests ergeben nun tatsaechlich
  859. Standalone-Panel bis `critical done` nach 2,329 s gestartet und sauber
  beendet; kein LinuxCNC-Start erforderlich.

### LES-032: Werkzeugbreite gegen die Futter-Sperrzone geprueft 2026-09-15

- Erster konkreter Baustein fuer Erreichbarkeits-/Werkzeughuellenpruefung
  mit Tooltable-Daten. Bisher wurde die Futter-Sperrzone
  (`chuck_no_go_x_min/x_max/z_limit`) nur fuer die SEPARATEN Rueckzugswege
  vor/nach einer Operation geprueft (`emit_safe_retract_for_op()`) - die
  eigentliche Stechbewegung selbst hatte NIE eine Pruefung, und selbst die
  Rueckzugspruefung behandelt das Werkzeug als punktfoermig. Ein
  Stechwerkzeug hat aber eine reale Schneidenbreite (`Tool.insert_width_mm`,
  siehe voriger Eintrag) - die dem Futter zugewandte Kante kann in die
  Sperrzone reichen, auch wenn die programmierte Z-Mitte selbst noch
  ausserhalb liegt.
- Neue `_check_groove_reaches_chuck_no_go_zone()` (`checks.py`) prueft die
  tiefste Stechposition (Nutgrund) an beiden Kanten der bekannten
  Werkzeugbreite gegen dieselbe, bereits produktiv genutzte Sperrzonen-
  Logik wie die Rueckzugswege (`gcode_safety.py::validate_chuck_segment()`,
  direkt wiederverwendet statt dupliziert). Nur aktiv, wenn ueberhaupt eine
  Sperrzone konfiguriert ist.
- Sieben neue Tests (`tests/test_groove_chuck_reachability_check.py`), per
  entferntem Verdrahtungsaufruf als echte Regression verifiziert;
  zusaetzlich end-to-end gegen die echte `Drehbank/tool.tbl` bestaetigt (T4
  "Einstechen MGMN200", 2,0 mm Einsatzbreite: eine fuer sich allein 0,6 mm
  von der Sperrzonengrenze entfernte Z-Position wird durch die
  Werkzeugbreite korrekt als Verletzung erkannt - ein rein punktbasierter
  Check haette das uebersehen). Alle zwoelf Referenzen neu generiert (keine
  Abweichung), `rs274` sowie 43 Matrixfaelle weiterhin fehlerfrei. 857
  Stub-/102 Real-Qt-Tests bestanden.
- Weitergehende Werkzeughuellenpruefung (z. B. fuer Dreh-/Bohrwerkzeuge,
  Haltergeometrie) bleibt offen - dafuer fehlt bislang die Datengrundlage
  im echten `tool.tbl`. Details: TODO.md (LES-032).

### LES-032: Entscheidung gegen eine Q-basierte Innen/Aussen-Pruefung 2026-09-15

- Ueberpruefung ergab per echtem Gegenbeispiel im realen `Drehbank/tool.tbl`:
  Q6 steht dort gleichzeitig fuer T3/T4 ("Außendrehen"/"Einstechen",
  AUSSEN) und T7/T9/T11 ("Innen*", INNEN) - eine Plausibilisierung anhand
  des Q-Werts allein wuerde also Falschmeldungen erzeugen. Q kodiert die
  Schneidenausrichtung fuer die Radiuskompensation, nicht die Werkstueck-
  seite.
- Nutzerbestaetigung: dasselbe physische Werkzeug kann durch Drehrichtungs-
  wechsel der Spindel sowohl aussen als auch innen schneiden - Q kann
  grundsaetzlich keine alleinige, zuverlaessige Innen/Aussen-Quelle sein.
  Eine umfassendere, sprachunabhaengige Kommentaranalyse waere
  unverhaeltnismaessig aufwendig; ein gewisses Mass an Verantwortung beim
  Anwender (korrekte Kommentare/Parameter) wird bewusst akzeptiert.
- Kein Codeeingriff - die bestehende, bereits aktive Kommentartext-Pruefung
  in `checks.py::validate_program_setup()` bleibt unveraendert und ist die
  verlaesslichere Quelle. Details: TODO.md (LES-032).

### LES-032: Werkzeugbreite aus ISO-Einsatzcode fuer Vorschau UND Pruefung 2026-09-15

- Das real genutzte `tool.tbl` (`Drehbank/tool.tbl`) belegt D bereits fuer
  Radius (Dreh-/Gewinde-/Stechwerkzeuge, Werte <= 5 mm) bzw. Durchmesser
  (Bohrer, Werte > 5 mm) und Q fuer die Orientierung; I/J sind durchgehend
  0 und ungenutzt - der LinuxCNC-Standard-Tooltable-Aufbau hat keine eigene
  Spalte fuer die Stechwerkzeug-Schneidenbreite. Die tatsaechlich
  vorhandene Quelle ist der ISO-Einstich-Einsatzcode im Kommentar (z. B.
  "MGMN200" -> 2,00 mm), bisher nur redundant in
  `tool_logic.py::infer_insert_profile()` fuer die Werkzeugvorschau
  implementiert.
- Neue gemeinsame, Qt-freie Quelle: `Tool.insert_width_mm`-Property
  (`tools.py`, basiert auf neuer `extract_insert_width_from_comment()`).
  `infer_insert_profile()` liest jetzt von dort statt selbst zu parsen.
- Neue `_check_tool_width_matches_operation()` (`checks.py`): warnt, wenn
  die manuell eingetragene Werkzeugbreite einer Stech-Operation (nur wenn
  `use_tool_width` aktiv ist) vom kommentarbasierten Wert abweicht - analog
  zum kuerzlich ergaenzten Gewinde-Preset-Vergleich.
- Sieben neue Tests (`tests/test_tool_width_mismatch_check.py`), per
  entferntem Verdrahtungsaufruf als echte Regression verifiziert. Die
  `tool_logic.py`-Umstellung zusaetzlich end-to-end gegen die echte
  `Drehbank/tool.tbl`-Datei bestaetigt (T4 "Einstechen MGMN200" ->
  unveraendert `groove_width_mm: 2.0`). Alle zwoelf Referenzen neu
  generiert (keine Abweichung), `rs274` sowie 43 Matrixfaelle weiterhin
  fehlerfrei. 850 Stub-/102 Real-Qt-Tests bestanden.
- Schneidenlaenge und Haltergeometrie (die anderen beiden in LES-032
  genannten Datenpunkte) bleiben offen - im echten `tool.tbl` gibt es
  dafuer aktuell keine erkennbare Datenquelle (weder Spalte noch
  Kommentarkonvention). Details: TODO.md (LES-032).

### LES-044: Seitenansicht-Raster als Qt-freier Darstellungsplan 2026-09-15

- Neue Funktion `side_view_grid_layout()` buendelt Achsen, X-/Z-Ticks samt
  Markierungslinien und Textpositionen, Achsbeschriftungen sowie die optionale
  Schnittlinie mit Beschriftungsposition. `paintEvent()` berechnet diese
  Koordinaten nicht mehr selbst, sondern zeichnet den fertigen Plan.
- Ein neuer Stub-Test prueft den Plan gegen die bestehenden elementaren
  Transformationsfunktionen. Gesamtstand: 843 Stub-Qt- und 102 Real-Qt-Tests,
  keine Skips. Standalone-Panel bis `critical done` nach 2,143 s gestartet und
  sauber beendet; kein LinuxCNC-Start erforderlich.

### LES-044: Kreis-/Vorderansichts-Layout Qt-frei berechnet 2026-09-15

- `circular_view_layout()` berechnet fuer Schnitt- und Vorderansicht jetzt
  Mittelpunkt, Massstab, Kreisradius und Achslinien ausserhalb des Paint-Codes;
  Pan/Zoom und unterschiedliche Einpassfaktoren bleiben erhalten.
- `offset_polygons_to_screen()` verschiebt und skaliert die Keilnut-Polygone
  Qt-frei. `_draw_front_keyway_overlay()` ist damit auf Stil und QPainter-
  Ausgabe reduziert. Eine nach dem vorherigen Paket ungenutzte Qt-Wrapper-
  Methode wurde entfernt.
- Zwei neue Stub-Tests sichern Layout/Navigation und unveraenderte Eingabe-
  Polygone. Gesamtstand: 842 Stub-Qt- und 102 Real-Qt-Tests, keine Skips.
  Standalone-Panel bis `critical done` nach 2,060 s gestartet und sauber
  beendet; kein LinuxCNC-Start erforderlich.

### LES-044: Pan-/Zoom-Transformation aus dem Qt-Widget geloest 2026-09-15

- `navigated_center_scale()`, `apply_side_navigation()` und
  `zoom_navigation_state()` nach `preview_geometry.py` ausgelagert. Die
  Berechnung von verschobenem Mittelpunkt, skaliertem Seiten-Viewport,
  Zoomgrenzen und festem Mausanker ist damit Qt-freie Darstellungsgeometrie;
  `preview_widget.py` uebersetzt nur noch zwischen Tupeln und Qt-Punkten.
- Zwei neue Stub-Tests pruefen Mausanker, Mittelpunkt/Skalierung, halbierte
  Sichtspanne bei Faktor 2 und dass der eingepasste Ausgangs-Viewport nicht
  veraendert wird. Bestehende Real-Qt-Navigationstests bleiben gruen.
- Gesamtstand: 840 Stub-Qt- und 102 Real-Qt-Tests, keine Skips. Standalone mit
  `LATHEEASYSTEP_DEBUG=1 qtvcp ...` bis `_finalize_ui_ready critical done`
  nach 2,346 s gestartet und sauber beendet; kein LinuxCNC-Start erforderlich.

### LES-028: Preset-/Manuell-Normalisierung abgeschlossen 2026-09-15

- Echter Verdrahtungsfehler behoben: Beim Wechsel eines Gewinde-Presets setzte
  `_apply_standard_thread_selection()` Durchmesser und Steigung, aktivierte
  dann aber den Rekursionsschutz, bevor `apply_thread_preset()` die uebrigen
  leeren Felder fuellen konnte. Der vorgesehene Soft-Fill lief dadurch nie.
- Neue Qt-freie Funktion `thread_preset_values()` liefert alle aus einem
  gueltigen Preset abgeleiteten Werte. UI und Plausibilitaetspruefung verwenden
  damit dieselbe Berechnung fuer Gewindetiefe, erste Zustellung, Spitzenversatz,
  Ruecklauf, Zustellwinkel, Federschnitte und Auslaufparameter.
- Presetwechsel setzen die identitaetsbildenden Werte Durchmesser/Steigung und
  fuellen sonst nur leere Felder; "Preset uebernehmen" ersetzt weiterhin
  bewusst alle Presetwerte. Manuelle Abweichungen bleiben erlaubt, werden aber
  nun ueber alle abgeleiteten Felder als eine zusammengefasste Warnung sichtbar.
- Maschinen-/Futterprofile erzeugen keinen parallelen Presetdatensatz: Sie
  werden sofort in die konkreten Programmkopfwerte aufgeloest. Dort gibt es
  daher keinen spaeteren Preset-/Manuell-Widerspruch zu vergleichen.
- Vier neue Stub-Tests fuer Normalisierung, Soft-Fill, erzwungenes Anwenden und
  zusammengefasste Konfliktmeldung. Gesamtstand: 838 Stub-Qt- und 102
  Real-Qt-Tests, keine Skips. Das eingebettete Panel erreichte in der
  QtDragon-SIM `_finalize_ui_ready critical done` nach 10,946 s und wurde
  sauber beendet. LES-028 ist damit abgeschlossen.

### LES-028: Tool.kind gegen den Operationstyp geprueft 2026-09-15

- Recherche zu "Werkzeugwechsel nur aus einem normalisierten
  Werkzeugdatensatz erzeugen" ergab: `T{tool_num:02d} M6` wird bereits
  heute nur mit einer per `validate_tool_table_completeness()` vorab
  gegen die Tabelle geprueften Nummer erzeugt. Stattdessen einen echten,
  bisher komplett ungenutzten Datenpunkt aktiviert: `Tool.kind` (aus der
  Q-Orientierung der Werkzeugtabelle geparst) wurde nirgends gegen den
  tatsaechlich verwendeten Operationstyp geprueft - ein Werkzeug, dessen
  Q-Wert laut Tabelle z. B. auf ein Bohrwerkzeug hindeutet, konnte
  unbemerkt einer Stech- oder Gewinde-Operation zugewiesen werden.
- Neue `_check_tool_kind_matches_operation()` (`checks.py`), in die
  bereits aktive `validate_program_setup()`-Warnungs-Pipeline verdrahtet
  (landet in `prog["__warnings"]` im Preview UND als `(WARN: ...)`-
  Kommentar im erzeugten G-Code-Kopf). Bewusst konservativ, um
  Falschmeldungen bei unklassifizierten Werkzeugen zu vermeiden: nur bei
  tatsaechlich gesetzter Q-Orientierung geprueft (fehlende Orientierung
  liefert nur den Fallback "turning", keine echte Klassifikation) und
  `kind == "parting"` (Fallback fuer jeden nicht zugeordneten Q-Wert) wird
  nie als Widerspruch gewertet.
- Bei der Recherche bestaetigt (bereits dokumentiert in
  `tests/test_tool_warning_wiring.py`): die aehnliche Pruefung
  `tool_logic.py::collect_tool_orientation_warnings()` ist bewusst tote,
  redundante Zweitimplementierung eines in `checks.py` bereits aktiven
  Innen-/Aussen-Checks - kein neuer Fund, nur zur Einordnung bestaetigt.
- Neun neue Tests (`tests/test_tool_kind_mismatch_check.py`), per
  entferntem Verdrahtungsaufruf als echte Regression verifiziert. Alle
  zwoelf Referenzen neu generiert (keine Abweichung), `rs274` sowie 43
  Matrixfaelle weiterhin fehlerfrei. 834 Stub-/102 Real-Qt-Tests
  bestanden. Details: TODO.md (LES-028).

### LES-044: stille except Exception-Fallbacks in den Vorschau-Modulen loggen 2026-09-15

- 72 von 82 `except Exception`-Fundstellen in `preview_geometry.py`,
  `preview_widget.py`, `preview_scene.py` und `ui_preview.py` fingen
  Ausnahmen bisher vollstaendig still ab - kein Log, kein Hinweis. Ein
  echter Bug haette sich dadurch als leise falsches Verhalten getarnt
  statt als sichtbarer Fehler.
- Entscheidung mit dem Nutzer geklaert: kleinster Schritt zuerst - nur
  Logging ergaenzen, Ausnahmetypen nicht einschraenken und Verhalten nicht
  aendern. Jede zuvor stille Stelle bekommt jetzt
  `_LOGGER.debug("[LatheEasyStep] <Funktion>: unexpected exception
  suppressed: %s", exc)` als ersten Befehl im except-Block; wo noch kein
  `as exc` vorhanden war, wurde das ergaenzt.
- `preview_geometry.py`/`preview_scene.py` bleiben bewusst Qt-frei -
  `logging` ist Standardbibliothek, keine neue Qt-Abhaengigkeit.
- Per Skript erzeugt (AST-basiert, damit garantiert nur innerhalb
  bestehender except-Bloecke eingefuegt wird) und manuell gegengeprueft:
  Syntax aller vier Dateien, Importplatzierung korrigiert, ein direkter
  Spotcheck mit `logging.basicConfig` bestaetigt die Meldung erscheint mit
  korrekter Funktion und Fehlertext, Verhalten unveraendert (gleicher
  Rueckgabewert wie zuvor). Volle Stub- und Real-Qt-Suite unveraendert
  gruen (825/102) - reine Zusatzausgabe, keine neuen Tests noetig.
- Die vollstaendige Einzelbewertung (Ausnahmetypen je Fundstelle gezielt
  auf den erwarteten Fehlertyp einschraenken) bleibt bewusst offen fuer
  eine spaetere, groessere Iteration - siehe TODO.md (LES-044).

### LES-024: verbleibende QMessageBox-Klick-Validierungen bewertet (LES-024 vollstaendig abgeschlossen) 2026-09-15

- Letzter offener LES-024-Punkt: alle 21 verbliebenen `QMessageBox`-
  Fundstellen (`ui_flow.py`, `ui_dirty.py`, `ui_persistence.py`,
  `ui_tools.py`, `lathe_easystep_handler.py`) einzeln durchgesehen und
  bewertet, ob sie sich - wie "Step speichern", die Listenaktionen und
  "Aenderungen speichern" zuvor - durch einen Buttonzustand ersetzen
  liessen.
- Ergebnis: drei sind bereits die bewusst beibehaltene "letzte Sicherung"
  neben einem vorhandenen Buttonzustand (Step speichern ohne Auswahl,
  Loeschen des Programmkopfs, Aenderungen speichern ohne offene
  Aenderungen). Alle uebrigen sind Ergebnis-/Fehlermeldungen NACH einem
  Versuch (Datei nicht ladbar/speicherbar, G-Code-Erzeugung fehlgeschlagen,
  Werkzeugtabellen-Probleme) - deren Ursache (z. B. Dateisystemfehler,
  kaputte Datei) laesst sich nicht vorab per Buttonzustand ausschliessen,
  ohne die bereits in `checks.py` vorhandene Validierung zu duplizieren.
- Kein Codeeingriff noetig - reine Bewertung/Dokumentation. LES-024 ist
  damit vollstaendig abgeschlossen (alle vier Pakete: View-Schnittstellen,
  Step speichern, Listenaktionen, Aenderungen speichern) und aus TODO.md
  entfernt.

### LES-024: "Aenderungen speichern" per Buttonzustand gesperrt (drittes Paket) 2026-09-15

- "Aenderungen speichern" (`btn_save_changes`) ohne offene Aenderungen war
  bisher jederzeit klickbar und zeigte erst danach eine "nichts zu
  speichern"-Meldung (`handle_save_changes()`). Wie bei "Step speichern"
  und den Listenaktionen (Loeschen/Hoch/Runter) wird die ungueltige Aktion
  jetzt per Buttonzustand von vornherein verhindert: `update_dirty_status()`
  (`ui_dirty.py`) sperrt den Button zusaetzlich zum bisherigen Text-
  Sternchen (" *"), solange `has_unsaved_changes()` falsch ist.
- Zentral in `update_dirty_status()` verdrahtet, das bereits von jeder
  dirty-zustandsaendernden Funktion aufgerufen wird (mark_dirty,
  mark_program_structure_dirty, clear_dirty_state, clear_program_dirty,
  clear_dirty_operation, die drei Reindex-Funktionen,
  mark_all_operations_dirty) - keine einzelne Aktion musste separat
  verdrahtet werden. Die bestehende Klick-Meldung bleibt als letzte
  Sicherung bestehen (z. B. falls alle dirty Steps ohne verknuepfte Datei
  sind).
- Zwei neue Tests (`tests/test_dirty_and_messages.py`): Button gesperrt
  ohne offene Aenderungen, entsperrt nach `mark_dirty()`, wieder gesperrt
  nach `clear_dirty_state()`; sowie eine Bestaetigung, dass das Text-
  Sternchen weiterhin funktioniert. Per entferntem `setEnabled()`-Aufruf
  als echte Regression verifiziert. Live im Standalone-Panel bestaetigt:
  Button startet sichtbar gesperrt ohne offene Aenderungen, kein Fehler im
  Log. 825 Stub-/102 Real-Qt-Tests bestanden. Details: TODO.md (LES-024).

### LES-050: REGRESSIONSFUND im eingebetteten QtDragon-Panel behoben (LES-050 vollstaendig abgeschlossen) 2026-09-15

- Praktischer Check im eingebetteten QtDragon-Panel (letzter offener
  LES-050-Punkt) foerderte einen echten Fund zutage: bei dessen gemerkter
  Standardfenstergroesse (1364x768, aus `qtdragon.pref`) ist die Tab-Flaeche
  fuer LatheEasyStep nur rund 590-640px breit - schmaler als unsere
  Mindestbreite von 750px. Die zweite Button-Spalte (Schritt loeschen/
  Nach unten/Programm erzeugen) wurde dadurch ohne Scrollbar abgeschnitten -
  nicht nur gequetscht wie beim fruehreren REGRESSIONSFUND, sondern
  vollstaendig unsichtbar und nicht klickbar, da die QtDragon-Tab-Seite
  selbst keine Scrollmoeglichkeit bietet.
- Ursache per Live-Debug-Dump (temporaere Logausgaben im laufenden
  Standalone- und eingebetteten SIM-Panel) gefunden: `root.setMinimumWidth(...)`
  (`_install_workspace_splitter`) zwang `root` dazu, breiter zu sein als
  sein eigener Elterncontainer innerhalb der QtDragon-Tab-Flaeche (live
  beobachtet: root auf 750px erzwungen, Elterncontainer aber nur 592px
  breit) - und genau an dieser root-zu-Elter-Grenze (nicht innerhalb
  unseres eigenen Splitters) wurde abgeschnitten.
- Zwei Teile behoben: (1) `root` selbst in eine neue `QScrollArea`
  (`workspaceScrollArea`, horizontal bei Bedarf, vertikal nie,
  `widgetResizable`) gepackt, damit Inhalt unabhaengig von der
  tatsaechlichen Host-Breite ueber eine Scrollleiste erreichbar bleibt,
  statt bei zu wenig Platz verloren zu gehen; (2) die Mindestbreite wird
  jetzt auf `root.window()` statt auf `root` selbst gesetzt - im
  Standalone-Fall weiterhin `root` selbst (unveraendertes Verhalten, WM
  erzwingt weiterhin ein sinnvolles Minimum), im eingebetteten Fall dagegen
  QtDragons eigenes, ohnehin schon breiteres Hauptfenster (dort wirkungslos,
  root darf auf die tatsaechlich verfuegbare Host-Breite schrumpfen).
- Vier neue Tests (`tests/test_preview_panel_ui_loader.py`): Mindestbreite
  landet auf dem Fenster statt auf root im eingebetteten Fall, bleibt im
  Standalone-Fall unveraendert auf root, QScrollArea-Konfiguration
  strukturell abgesichert. Eine vollstaendige automatisierte Nachbildung
  des QtDragon-eigenen Einbettungsmechanismus war nicht praktikabel - `root`
  hat bewusst kein eigenes Qt-Layout (`root.layout() is None`), die
  Groessenkaskade zu seinem Inhalt laeuft ueber einen QtVCP-eigenen,
  projektexternen Mechanismus außerhalb dieses Repos. Live-Verifikation im
  eingebetteten SIM-Panel als massgebliche Bestaetigung: Scrollleiste
  erscheint bei der gemerkten Standardgroesse, und Scrollen ans Ende (per
  direktem Setzen des Scrollbar-Werts, da synthetische X11-Mausereignisse
  den genauen Scrollbar-Griff nicht zuverlaessig trafen) macht
  "Schnittansicht", "Schritt loeschen", "Nach unten", "Programm erzeugen"
  sowie die weiteren Reiter (Kontur/Abspanen/Gewinde/...) wieder
  vollstaendig lesbar.
- 823 Stub-/102 Real-Qt-Tests bestanden. LES-050 ist damit vollstaendig
  abgeschlossen (alle Punkte umgesetzt, inklusive des eingebetteten
  Panels) und aus TODO.md entfernt - Details siehe oben und in den
  vorherigen LES-050-Eintraegen dieser Datei.

### LES-050: Splitterpositionen sitzungsuebergreifend gemerkt (abgeschlossen) 2026-09-15

- Letzter offener LES-050-Punkt umgesetzt: `workspaceSplitter` (Step-Spalte/
  rechte Spalte) und `previewParamsSplitter` (Vorschau/Parameter) merken
  sich ihre Groesse jetzt ueber `QSettings`
  (`LatheEasyStep/WorkspaceSplitterSizes`,
  `LatheEasyStep/PreviewParamsSplitterSizes`) und stellen sie beim naechsten
  Start wieder her, statt stets bei der festen Standardaufteilung
  (340/700 bzw. 180/520) zu bleiben. Neue Hilfsfunktionen
  `_restore_splitter_sizes()`/`_persist_splitter_sizes()` in
  `ui_lifecycle.py`, an beiden Splittern verdrahtet.
- Entscheidung (2026-09-15) mit dem Nutzer geklaert: nur Persistenz mit
  sicherem Fallback, keine zusaetzliche sichtbare Ruecksetzen-Aktion (anders
  als beim vorherigen "Ansicht zuruecksetzen"-Button, siehe Eintrag unten).
- "Robuste Standardaufteilung" ergibt sich daraus, dass ein gemerkter Wert
  nur uebernommen wird, wenn er nach dem Parsen (korrekte Anzahl,
  ausschliesslich positive Werte) mindestens so gross ist wie die jeweils
  bekannten Mindestgroessen (330/380 fuer den Arbeitsflaechen-Splitter,
  siehe REGRESSIONSFUND weiter unten) - eine zu schmale, fremde oder
  beschaedigte Einstellung faellt automatisch auf die bisherige feste
  Standardaufteilung zurueck, statt Buttons erneut zu quetschen.
  `QSettings()`-Fehlschlaege (z. B. kein Schreibzugriff auf das
  Konfigverzeichnis) werden abgefangen und wirken sich nicht auf die
  Splitter-Funktion aus.
- 15 neue Tests: neun isolierte Tests fuer die Parse-/Restore-/Persist-
  Hilfsfunktionen inkl. kaputtem Settings-Backend
  (`tests/test_splitter_size_persistence.py`), vier Real-Qt-
  Integrationstests je Splitter fuer Wiederherstellung, Mindestgroessen-
  Fallback und Speichern beim Ziehen (`tests/test_preview_panel_ui_loader.py`).
  `moveSplitter()` statt `setSizes()` verwendet, um das Speichern-beim-Ziehen
  zu testen - `setSizes()` loest das `splitterMoved`-Signal nicht aus, an das
  die Persistenz gebunden ist (empirisch per Testskript geprueft, bevor die
  Tests geschrieben wurden). Alle Fixes per entfernter Verdrahtung als echte
  Regression bestaetigt. 823 Stub-/99 Real-Qt-Tests bestanden. LES-050 ist
  damit vollstaendig abgeschlossen (offen bleibt nur noch ein praktischer
  Check im eingebetteten QtDragon-Panel bei verschiedenen Panelgroessen,
  siehe TODO.md).

### LES-050: Sichtbare Aktion "Ansicht zuruecksetzen" 2026-09-15

- Letzter offener Punkt aus LES-050 umgesetzt: Doppelklick setzte die
  Vorschau bereits zurueck, aber ohne sichtbare, gut erreichbare
  Alternative dazu. Neuer `btn_reset_view` (QToolButton, "Ansicht
  zuruecksetzen") links neben "Schnittansicht" in `previewPanel.ui`,
  verdrahtet in `setup_slice_view()` (`ui_preview.py`) auf
  `handler._reset_preview_view()` -> neue Funktion `reset_preview_view()`,
  die `reset_view()` auf beiden Vorschau-Widgets (`preview`,
  `preview_slice`) aufruft und dabei tolerant gegenueber fehlenden oder
  kaputten Widgets bleibt.
- Uebersetzung laeuft ueber die generische `.ui`-Scan-Schiene
  (`ui_static.py`, Schluessel `ui.btn_reset_view.text` /
  `ui.btn_reset_view.toolTip`), nicht ueber die Widget-Registry
  (`UI_TEXT_KEYS`/`UI_TOOLTIP_KEYS`) - beim ersten Versuch faelschlich die
  Registry verwendet, per fehlgeschlagenem Test korrigiert.
- Echter Regressionsfund beim Docking: `_dock_preview_above_scroll()`
  reparentete urspruenglich nur `btn_slice_view` in den neuen
  Controls-Bereich. `btn_reset_view` blieb dadurch als letztes Kind im
  alten `previewPanel`-Geruest zuruck, wodurch dessen `findChildren()`
  nicht mehr leer war und die "leere Huelle entfernen"-Pruefung
  fehlschlug - die leere Huelle blieb sichtbar im Baum und beanspruchte
  wieder Platz. Behoben, indem beide Buttons gemeinsam in den neuen
  Controls-Bereich umgehaengt werden.
- Sechs neue/erweiterte Tests: Signalverdrahtung und Toleranz ohne Button
  (`tests/test_slice_view_sync.py`), `reset_preview_view()` isoliert fuer
  beide Widgets sowie mit fehlenden/kaputten Widgets
  (`tests/test_slice_view_sync.py`), Docking nimmt Reset-Button mit und
  die leere Huelle bleibt entfernbar (`tests/test_preview_panel_ui_loader.py`).
  Jeder Fix per zurueckgesetzter Verdrahtung/zurueckgesetztem Docking-Fix
  als echte Regression verifiziert.
- Live im Standalone-Panel (`qtvcp -c easystep -u
  ./lathe_easystep_handler.py ./lathe_easystep.ui`) bestaetigt: Button
  rendert lesbar links von "Schnittansicht", Log zeigt fehlerfreie
  Verbindung ("reset view button connected"), Mausrad-Zoom und Klick auf
  den Button loesen ohne Fehler/Traceback aus. Ein visueller
  Vorher-Nachher-Screenshotvergleich war bei leerem Vorschau-Canvas (kein
  Programm geladen) nicht aussagekraeftig - die eigentliche Wirkung ist
  durch die automatisierten Tests direkt abgesichert, nicht nur durch den
  fehlerfreien Start. 812 Stub-/94 Real-Qt-Tests bestanden. Details:
  TODO.md (LES-050).

### LES-050: Regressionsfund "Buttontext gequetscht" behoben, Standalone-Panel als schnellerer UI-Testweg 2026-09-15

- Beim praktischen Test des neuen `workspaceSplitter` (siehe vorheriger
  Eintrag) gefunden: `stepListPanel.ui` (4 Buttons: Step/Programm speichern/
  laden) und `stepActionsPanel.ui` (7 Buttons: hinzufuegen/loeschen/
  verschieben/Programm erzeugen/Aenderungen speichern) standen je in einer
  einzigen QHBoxLayout-Reihe ohne Mindestbreiten-Absicherung - bei
  schmaler Splitterstellung wurden die Buttons unter ihre Textbreite
  gequetscht, nur noch Fragmente lesbar (in praktisch jedem SIM-
  Screenshot dieser gesamten Sitzung sichtbar, ohne dass es als Fund
  erkannt wurde).
- Beide Reihen auf zweispaltiges `QGridLayout` umgestellt (`stepListPanel`:
  2x2, `stepActionsPanel`: 2x4 mit "Aenderungen speichern" ueber beide
  Spalten). Die Splitter-Mindestbreiten (`_install_workspace_splitter`,
  `ui_lifecycle.py`) waren mit 190/360 zu knapp fuer die neuen Grids
  bemessen - per echtem `sizeHint()`-Messlauf auf 330/380 korrigiert. Das
  Gesamtfenster bekommt zusaetzlich `root.setMinimumWidth(330+380+40)`,
  damit der Fenstermanager selbst gar nicht erst kleiner zulaesst, als der
  Splitter zum Vermeiden von Quetschungen braucht.
- Echter Zweitfund beim Standalone-Test (siehe unten):
  `_ensure_status_widgets()` (`ui_advanced.py`) rief `layout.insertWidget()`
  auf, um das "Keine offenen Aenderungen"-Label neben "Aenderungen
  speichern" einzufuegen - eine QBoxLayout-Methode, die das neue
  QGridLayout nicht hat. Brach beim echten Panelstart mit `AttributeError`
  ab; kein bestehender Test deckte das ab (Stub-Suite nutzt keine echten
  Qt-Layouts, der einzige Real-Qt-Test setzte `label_dirty_status` direkt
  als Fake statt die Funktion echt aufzurufen). Auf `getItemPosition()`/
  `addWidget(row+1, ...)` umgestellt.
- **Workflow-Verbesserung:** fuer reine UI-/Layout-Verifikation muss nicht
  jedes Mal die volle QtDragon-SIM (`linuxcnc lathe.ini`, ~8-10s Boot,
  Screensaver, X11-Klicknavigation durchs UTILS-Panel) gestartet werden -
  das Panel laesst sich standalone starten
  (`qtvcp -c easystep -u ./lathe_easystep_handler.py ./lathe_easystep.ui`,
  ~1,5-2s Boot, echtes eigenstaendiges Top-Level-Fenster, direkt
  groessenveraenderbar). Genau darueber wurde der zweite Fund
  (QGridLayout-Crash) live entdeckt und die Fenstermindestbreite per
  echter Fenstergroessenaenderung verifiziert (Anforderung auf 400px
  fuehrte zu einer vom Fenstermanager korrekt durchgesetzten Groesse von
  750px). Die volle SIM bleibt fuer G-Code-/Bewegungspruefung reserviert.
- 12 neue Tests: neun fuer die Button-Lesbarkeit
  (`tests/test_step_action_buttons_stay_readable.py`, minimale/normale/
  breite Fenstergroesse plus beide Splittergrenzen, per zurueckgesetztem
  Layout als echte Regression verifiziert - Original: "Schritt hinzufuegen"
  77px statt benoetigter 155px, selbst bei 1600px Fensterbreite), drei fuer
  das Dirty-Status-Label im neuen Grid
  (`tests/test_dirty_status_label_grid_layout.py`, per zurueckgesetztem Fix
  als echte Regression verifiziert). Ein bestehender Test
  (`test_preview_panel_ui_loader.py`) fehlte die reale Aufrufreihenfolge
  (`_install_workspace_splitter()` vor dem Preview-Docking, wie der echte
  Start es immer tut) und wurde entsprechend ergaenzt - ohne den Splitter
  teilten sich Step-Spalte und rechte Spalte noch dieselbe Zeile, wodurch
  die jetzt zweizeilige Button-Gruppe der Vorschau faelschlich Hoehe
  weggenommen haette (reines Testaufbau-Artefakt, im echten Start nicht
  vorhanden).
- Live im Standalone-Panel bestaetigt: alle elf Buttons bei 900px
  (Standardgroesse), 650px sowie an der erzwungenen Fenstermindestbreite
  (750px) vollstaendig lesbar; das Dirty-Status-Label sitzt sichtbar
  korrekt unter "Aenderungen speichern". 809 Stub-/93 Real-Qt-Tests
  bestanden, keine Skips. Details: TODO.md (LES-050).

### LES-050: Arbeitsbereiche per Splitter, Vorschau mit Pan und Zoom 2026-09-15

- Vorschau/Parameter erhalten einen vertikalen, Step-Liste/Editor einen
  horizontalen `QSplitter`. Beide Seiten besitzen Mindestgroessen und koennen
  nicht vollstaendig zusammengeklappt werden.
- Seiten- und Schnittansicht lassen sich mit dem Mausrad um den Mauszeiger
  zoomen (begrenzt auf Faktor 0,2 bis 20) und per Maus verschieben. Die linke
  Maustaste behaelt bei aktiver Schnittlinie Vorrang fuer deren Z-Position;
  Mittel-/Rechtsziehen verschiebt die Ansicht weiterhin. Ein Doppelklick passt
  die Darstellung wieder ein.
- Die Navigation veraendert nur die Bildschirmtransformation, niemals Modell-
  oder Bearbeitungsdaten. Fuenf neue Real-Qt-Tests sichern Splitterrichtung,
  Mindestgroessen, Groessenaenderung, Zoomanker/-grenzen, Pan, Reset und den
  Vorrang der Schnittlinie. Gesamtstand: 809 Stub-Qt- und 81 Real-Qt-Tests,
  keine Skips. Das eingebettete Panel erreichte in der QtDragon-SIM
  `_finalize_ui_ready critical done` nach 13,885 s und wurde sauber beendet.
  Offen bleiben persistente Splitterpositionen und eine sichtbar beschriftete
  Reset-Aktion.

### LES-024: Vorschau wieder oben und Schnittansicht nach Lazy-Load verbunden 2026-09-15

- Die angedockte Vorschau steht wieder an erster Stelle im rechten
  Inhaltsbereich statt unter den Parametern.
- Die Schnittansicht wurde beim fruehen Handler-Start faelschlich als fertig
  eingerichtet markiert, obwohl ihr ausgelagertes UI-Fragment noch nicht
  geladen war. Der Aufbau wird nun erst nach vorhandener Vorschau, Vorderansicht
  und Umschaltbutton abgeschlossen und nach dem Lazy-Load gezielt wiederholt.
- Regressionstests sichern Position, unveraenderte Vorschauhoehe, entfernte
  Leerhuelle und den einmaligen Signalanschluss nach dem verzögerten Laden ab.
  Vollstaendige Suite: 809 Stub-Qt- und 76 Real-Qt-Tests, keine Skips. In der
  QtDragon-SIM wurde der fruehe Aufschub und anschliessend der erfolgreiche
  Anschluss beider Slice-Signale protokolliert; Embedded-Start bis
  `critical done` nach 8,866 s, danach sauber beendet.

### LES-024: Loeschen und Verschieben per Buttonzustand begrenzt 2026-09-15

- Neue zentrale Funktion `update_operation_action_button_states()` steuert
  "Loeschen", "hoch" und "runter" anhand der aktuellen Auswahl, des
  Programmkopfs und der Listengrenzen. Sie wird bei Auswahlaenderungen, nach
  jedem Neuaufbau der Step-Liste und nach dem verzögerten Laden der Buttons
  aufgerufen.
- Der Programmkopf bleibt unveraenderlich: alle drei Aktionen sind dort
  gesperrt; der erste Bearbeitungsschritt kann nicht ueber ihn verschoben
  werden, der letzte nicht weiter nach unten. Die Move-Handler besitzen
  dieselben Grenzen als zweite Sicherung fuer direkte Aufrufe.
- Sieben neue Tests sichern Auswahlgrenzen, Programmkopf, ersten/mittleren/
  letzten Step, Lazy-UI und den fruehen Auswahl-Rueckgabepfad ab. Vollstaendige
  Suite: 808 Stub-Qt- und 76 Real-Qt-Tests, keine Skips. Das eingebettete
  Panel erreichte in der QtDragon-SIM `_finalize_ui_ready critical done` nach
  9,025 s und wurde anschliessend sauber beendet. Details: TODO.md (LES-024).

### LES-024: "Step speichern" per Buttonzustand gesperrt (erstes Muster-Paket) 2026-09-14

- Nutzerentscheidung in Umsetzung: ungueltige Aktionen sollen kuenftig
  per Buttonzustand verhindert werden statt nur beim Klick eine
  Fehlermeldung zu zeigen. Klarster Fall zuerst umgesetzt: "Step
  speichern" ist jetzt nur aktiv, wenn eine Operation in der Step-Liste
  ausgewaehlt ist. Neue Funktion `update_save_step_button_state()`
  (`ui_persistence.py`), aufgerufen bei jeder Auswahlaenderung
  (`handle_selection_change()` in `ui_selection.py`, inklusive des
  fruehen Rueckgabepfads fuer eine ungueltige Zeile - sonst waere der
  Button nach dem Loeschen der letzten Operation faelschlich aktiv
  geblieben) sowie zentral am Ende von `_refresh_operation_list()`
  (`lathe_easystep_handler.py`). Letzteres deckt Hinzufuegen/Loeschen/
  Verschieben/Laden automatisch mit ab, ohne jede einzelne Aktion in
  `ui_flow.py`/`ui_operations.py` separat verdrahten zu muessen. Die
  bestehende Klick-Meldung ("message.step.select_operation_first")
  bleibt unveraendert als letzte Sicherung bestehen.
- Sechs neue Tests (`tests/test_save_step_button_state.py`): die reine
  Funktion isoliert (Button gesperrt/aktiv, fehlender Button, Ausnahme
  beim Lesen der Auswahl wird geschluckt) sowie die Verdrahtung in
  `handle_selection_change()` fuer eine gueltige und eine ungueltige
  Zeile. Per zwei unabhaengig entfernten Aufrufen als echte Regression
  verifiziert, danach zurueckgesetzt.
- Real in der SIM verifiziert: Embedded-Start fehlerfrei (`critical done`
  nach 8,233 s), "Step speichern" startet sichtbar gesperrt (kein Programm
  geladen, keine Auswahl) - deutlich erkennbar am gedimmten Button
  gegenueber den anderen, aktiven Buttons in derselben Reihe.
- 801 Stub-/76 Real-Qt-Tests bestanden, keine Skips. Noch offen: die
  uebrigen zehn+ QMessageBox-Klick-Validierungen in `ui_flow.py`/
  `ui_persistence.py` nach demselben Muster umstellen. Details: TODO.md
  (LES-024).

### LES-044: G-Code-Werkstattkommentare sind jetzt sprachabhaengig 2026-09-14

- Nutzerentscheidung umgesetzt: G-Code-Kommentare folgen jetzt der
  UI-Sprache. Die Step-Beschreibung (`(STEP: ...)`) war bereits ueber
  `_tr()` sprachabhaengig - der eigentliche Fund bei der Umsetzung war,
  dass die sieben `gcode_*.py`-Generatormodule selbst rund 70 weitere,
  hart-deutsche Kommentare direkt in den G-Code schreiben (Anfahrhinweise,
  Programmkopf-Sicherheitsblock, Gewinde- und Schrupp-Parameter),
  vollkommen unabhaengig von der UI-Uebersetzung.
- Neue Funktion `gcode_comment()` (`gcode_utils.py`) mit eigenem, minimalem
  `.lng`-Parser - bewusst NICHT an `translations.TranslationStore`
  gekoppelt. Ein erster Versuch, direkt `TRANSLATIONS` zu importieren,
  brach `regenerate_all_ngc.py` und jeden Generator-Aufruf ohne PyQt5, weil
  `translations.py` ueber `ui_registry.py` an `qtpy` haengt - der Generator
  ist bewusst von Qt getrennt (siehe TODO.md "Verifizierte Basis"). Per
  echtem Subprozess-Regressionstest (ohne pytest-Qt-Stub) dauerhaft
  abgesichert.
- 64 neue Uebersetzungsschluessel in `de.lng`/`en.lng`/`es.lng`, alle sieben
  betroffenen Dateien umgestellt (`gcode_drill.py`, `gcode_face.py`,
  `gcode_groove.py`, `gcode_thread.py`, `gcode_program.py`,
  `gcode_safety.py`, `gcode_roughing.py` - letztere mit den meisten
  Kommentaren: Strategie-/Aufmass-/Fallback-Gruende beim Schruppen).
  Bewusst NICHT angefasst: Validierungs-/Warnmeldungstexte aus
  `checks.py`/`get_machine_limit_warnings()` (eigenes, deutlich groesseres
  Thema - naeher an "Fehlertexte" als an "Werkstattkommentare", im TODO als
  offen dokumentiert) sowie eine Handvoll bereits-englische Struktur-/
  Diagnosemarker (Subroutine-Grenzen, "Pass N: X-band/Z-band"-Debugspur).
- Echter kleiner Nebenfund: "Schlichtaufmaß" war die einzige Kommentar-
  Stelle im ganzen Generator ohne `sanitize_comment_text()` - ein rohes
  scharfes S kam dort unsanitisiert durch. `gcode_comment()` sanitisiert
  jetzt konsequent wie jeder andere Kommentar; drei Referenzen zeigen
  dadurch "Schlichtaufmass" statt "Schlichtaufmaß" (reine Transliteration,
  keine Bedeutungsaenderung), ein bestehender Test entsprechend angepasst.
- 14+8 neue Tests (reine `gcode_comment()`-Funktion inkl. Subprozess-Import-
  Regressionstest, End-to-End durch `generate_program_gcode()` fuer DE/EN/
  ES ueber alle sieben Dateien, Default-Sprache bleibt exakt der bisherige
  Text). Mehrere gezielt injizierte Bugs (u. a. deaktivierte Pruefungen,
  vertauschte Uebersetzungsaufrufe) als echte Regression verifiziert.
- Alle zwoelf Referenzen neu generiert und mit `rs274` bestaetigt, 43
  Matrixfaelle weiterhin fehlerfrei. 795 Stub-/76 Real-Qt-Tests bestanden,
  keine Skips. Details: TODO.md (LES-044).

### LES-028: fehlende Werkzeugnummer in der Werkzeugtabelle blockiert jetzt die Programmerzeugung 2026-09-14

- Nutzerentscheidung umgesetzt: jede in einer Operation verwendete
  Werkzeugnummer muss einen Eintrag in der geladenen Werkzeugtabelle haben,
  sobald ueberhaupt eine geladen wurde. Vorher wurde eine fehlende Nummer
  weder als Fehler noch als Warnung gemeldet - der Werkzeugwechsel wurde
  stillschweigend mit einer unbekannten Werkzeugnummer erzeugt.
- Neue Funktion `validate_tool_table_completeness()` (`checks.py`), direkt
  aus `generate_program_gcode()` nach den bestehenden Pflichtfeld-Checks
  aufgerufen. Bewusst nur aktiv, wenn `settings["tools"]` nicht leer ist:
  reine Generatortests und die Referenzregeneration rufen
  `generate_program_gcode()` ueberwiegend ohne echtes `tool.tbl` auf - ohne
  diese Absicherung waeren 35+ bestehende Testdateien betroffen gewesen.
  Die bereits bestehende "ISO/Radius fehlt bei: ..."-Meldung in `tools.py`
  ist ein separates Thema (fehlende Metadaten bei vorhandenem Eintrag) und
  bleibt unveraendert eine Warnung.
- Sieben neue Tests (`tests/test_tool_table_completeness_check.py`): die
  Prueffunktion isoliert (fehlende/vorhandene Nummer, leere Tabelle,
  PROGRAM_HEADER/Tool-0 werden ignoriert, mehrere fehlende Nummern in einer
  Meldung) sowie zwei End-to-End-Tests durch den echten Generatorpfad. Per
  deaktiviertem Check als echte Regression verifiziert, danach
  zurueckgesetzt.
- Alle zwoelf Referenzprogramme neu generiert: keine Abweichung (reine
  Validierungsaenderung, keine Bewegungs-/Kommentaraenderung). Statische
  NGC-Pruefung, nativer `rs274`-Lauf und alle 43 Matrixfaelle weiterhin
  fehlerfrei. 779 Stub-/76 Real-Qt-Tests bestanden, keine Skips. Details:
  TODO.md (LES-028).

### LES-024/LES-034 abgeschlossen: Legende und Statusmeldungsbox aus preview_widget.py extrahiert 2026-09-14

- Letztes (zehntes) Verkleinerungspaket: die Legende (Box-/Klick-Rechteck,
  Kopf- und Zeilenpositionen) und die Statusmeldungsbox (Kuerzung auf vier
  Eintraege je 80 Zeichen, Box-/Zeilenpositionen) waren die letzten
  verbliebenen Stellen in `paintEvent()` mit echter Layoutberechnung statt
  reinem Zeichnen. Jetzt als `legend_layout()`/`status_message_layout()`
  (`preview_geometry.py`) ausgelagert. Farben/Stifte der Legendeneintraege
  bleiben bewusst im Widget (Qt-Stildaten, keine Fachlogik, die eine
  Qt-freie Abstraktion braucht).
- Acht neue Tests: sieben direkt gegen die beiden reinen Funktionen (Zeilen-
  reihenfolge, eingeklappter vs. ausgeklappter Zustand, stabiler Klick-Rect
  unabhaengig vom Klappzustand, Kuerzung auf vier Nachrichten/80 Zeichen,
  Box-Breite an beiden Seiten begrenzt) sowie ein echter PyQt5-Painttest,
  der Legende-Header-Klick (Ein-/Ausklappen) und sichtbare Statusmeldungen
  ueber den tatsaechlichen Widget-Zeichenpfad ausuebt. Per zwei unabhaengig
  injizierten Bugs (klappzustandsabhaengiger Klick-Rect, falsche
  Nachrichten-Obergrenze) als echte Regression verifiziert, danach
  zurueckgesetzt.
- Real in der SIM verifiziert: Embedded-Start fehlerfrei (`critical done`
  nach 9,679 s), Legende im UTILS-Panel per Klick auf den Kopf sichtbar
  korrekt eingeklappt (nur noch die Kopfzeile, keine Eintraege). Kein
  Fehler im Log.
- `preview_widget.py`: 689 -> 671 Zeilen. Damit ist die Verkleinerung
  entlang der `PreviewScene`-Ebenen abgeschlossen: 1049 -> 671 Zeilen
  ueber zehn Pakete (-36%); die verbliebenen `_paint_*`-Routinen sind
  reines QPainter-Zeichnen ohne eigene Fachlogik mehr. 772 Stub-/76
  Real-Qt-Tests bestanden, keine Skips. Details: TODO.md (LES-024,
  LES-034).

### LES-024/LES-034: Vorderansicht - Rohteilkreise, Endkonturfuellung und Durchmesserringe als Darstellungsplan 2026-09-14

- Neuntes Verkleinerungspaket: `_paint_front_view()` entschied bisher inline,
  welche Kreise (Rohteil-Aussen-/Innendurchmesser, gefuellte Endkontur,
  Aussen-/Innen-/aktive Durchmesserringe) in welcher Reihenfolge und Farbe
  gezeichnet werden. `build_front_view_draw_plan()` (`preview_scene.py`)
  loest das jetzt Qt-frei als Liste von `FrontViewCircle`-Eintraegen
  (Durchmesser + semantischer Stilschluessel) auf; `front_view_scale()`
  (`preview_geometry.py`) berechnet den Skalierungsfaktor. Die Zeichenroutine
  ruft nur noch `painter.drawEllipse()` mit den fertigen Werten auf.
- Reihenfolge bewusst unveraendert: Rohteil -> gefuellte Endkontur ->
  Keilnut-Overlay -> Durchmesserringe. Die Keilnut bleibt ein separater
  Aufruf (`_draw_front_keyway_overlay`), da sie aus der Operationsliste statt
  aus diesem Plan stammt - der Plan ruft sie nicht auf, das Widget haelt die
  Reihenfolge weiterhin per zwei getrennten Durchlaeufen ein.
- Sieben neue Tests: vier fuer `build_front_view_draw_plan()`
  (Reihenfolge, ausgelassene Rohteil-Innenkontur bei gleichem Durchmesser,
  ausgelassenes Endkontur-Loch ohne kleinere Bohrung, komplett leerer Plan
  ohne Geometrie) und drei fuer `front_view_scale()` (Skalierung an beiden
  Seiten, entarteter Nulldurchmesser). Per zwei unabhaengig injizierten Bugs
  (vertauschte Ring-Rolle, vertauschtes min/max bei der Skalierung) als echte
  Regression verifiziert, danach zurueckgesetzt.
- Real in der SIM verifiziert: Embedded-Start fehlerfrei (`critical done`
  nach 8,493 s), Schnittansicht im UTILS-Panel live umgeschaltet, kein Fehler
  im Log. `preview_widget.py`: 679 -> 689 Zeilen (die duennen Qt-Adapter
  wachsen leicht, die Fachlogik ist aber vollstaendig entfernt).
- 764 Stub-/75 Real-Qt-Tests bestanden, keine Skips. Details: TODO.md
  (LES-024, LES-034).

### LES-024/LES-034: Sperrzonen-Fuellgeometrie aus Paint-Code entfernt 2026-09-14

- `stroke_bounding_rectangle()` berechnet jetzt Qt-frei das Modellrechteck
  um alle Primitive-Striche der Futter-Sperrzone. Das Widget transformiert
  nur noch dessen vier Eckpunkte und zeichnet die Fuellung.
- Primitive werden pro Pfad nur einmal in Striche zerlegt und anschliessend
  sowohl fuer Fuellung als auch Kontur verwendet; die bisherige doppelte
  Bogenzerlegung entfaellt.
- Zwei direkte Tests sichern getrennte Striche und leere Eingaben ab.
  `preview_widget.py` schrumpft von 681 auf 679 Zeilen. Vollstaendige Suite:
  757 Stub-Qt- und 75 Real-Qt-Tests, keine Skips. Das eingebettete Panel
  erreichte in der QtDragon-SIM `_finalize_ui_ready critical done` nach
  8,505 s und wurde anschliessend sauber beendet. Details: TODO.md (LES-024,
  LES-034).

### LES-024/LES-034: Zeichenreihenfolge und semantische Stile ausgelagert 2026-09-14

- `build_preview_draw_plan()` in `preview_scene.py` bestimmt jetzt Qt-frei
  Reihenfolge, erste Primitive-Rolle, Szenenebene und semantischen Stil jedes
  Pfads. Das Widget ordnet dem Stil nur noch konkrete Qt-Farbe, Breite und
  Strichart zu.
- Zwei direkte Tests sichern, dass der aktive Pfad zuletzt gezeichnet wird,
  Werkstueck-/Hilfs-/Werkzeugwege ihre Ebenenstile behalten und Sonderrollen
  wie `chuck_nogo` auch beim aktiven Pfad Vorrang besitzen.
- `preview_widget.py` schrumpft von 739 auf 681 Zeilen. Vollstaendige Suite:
  755 Stub-Qt- und 75 Real-Qt-Tests, keine Skips. Das eingebettete Panel
  erreichte in der QtDragon-SIM `_finalize_ui_ready critical done` nach
  8,294 s und wurde anschliessend sauber beendet. Details: TODO.md (LES-024,
  LES-034).

### LES-024/LES-034: Tickwerte und Positionen aus Paint-Code entfernt 2026-09-14

- `side_view_ticks()` berechnet jetzt Qt-frei die 1/2/5-Tickwerte, deren
  Bildschirmpositionen und die Durchmesserbeschriftung der X-Achse. Der
  Paint-Code iteriert nur noch ueber fertige Werte und zeichnet sie.
- Ein direkter Test sichert beide Achsen inklusive negativer Werte,
  Ursprung, Bildschirmpositionen und X-Durchmesserlabels ab. Ein dadurch
  unbenutzter Transformationsadapter wurde entfernt; `preview_widget.py`
  schrumpft von 748 auf 739 Zeilen.
- Vollstaendige Suite bestanden: 753 Stub-Qt- und 75 Real-Qt-Tests, keine
  Skips. Das eingebettete Panel erreichte in der QtDragon-SIM
  `_finalize_ui_ready critical done` nach 8,364 s und wurde anschliessend
  sauber beendet. Details: TODO.md (LES-024, LES-034).

### LES-024/LES-034: Bildschirmtransformation und Achsen ausgelagert 2026-09-14

- Modellkoordinaten-Transformation, Achsenlage und Schnittlinie der
  Seitenansicht als `side_view_to_screen()`, `side_view_axis_lines()` und
  `side_view_slice_line()` Qt-frei nach `preview_geometry.py` verschoben.
  Das Widget wandelt die gelieferten Tupel nur noch in `QPointF` um.
- Drei direkte Tests sichern Durchmesserhalbierung, Bildschirmorientierung,
  Maschinenursprung und Schnittlinienausdehnung ab. Die duennen Qt-Adapter
  lassen `preview_widget.py` gegenueber dem vorigen Paket leicht von 741 auf
  748 Zeilen wachsen, entfernen jedoch die Koordinatenfachlogik aus dem
  Widget.
- Vollstaendige Suite bestanden: 752 Stub-Qt- und 75 Real-Qt-Tests, keine
  Skips. Das eingebettete Panel erreichte in der QtDragon-SIM
  `_finalize_ui_ready critical done` nach 8,141 s und wurde anschliessend
  sauber beendet. Details: TODO.md (LES-024, LES-034).

### LES-024/LES-034: Seitenansicht-Viewport und Ticks Qt-frei berechnet 2026-09-14

- Grenzenermittlung, Durchmesser-/Radiusumrechnung, Mindestspanne, Rand und
  Skalierung aus `paintEvent()` als `compute_side_viewport()` nach
  `preview_geometry.py` verschoben. Auch die 1/2/5-Auswahl der Achsenticks
  liegt jetzt in der reinen Funktion `nice_tick_step()`.
- Vier direkte Tests sichern leere Ansichten, Durchmesserkoordinaten,
  Bogenprimitive und Tickabstaende ab. Die bestehenden echten Painttests
  bleiben unveraendert gruen; `preview_widget.py` schrumpft von 808 auf 741
  Zeilen.
- Vollstaendige Suite bestanden: 749 Stub-Qt- und 75 Real-Qt-Tests, keine
  Skips. Embedded-Start in der QtDragon-SIM ebenfalls fehlerfrei;
  `_finalize_ui_ready critical done` nach 7,769 s, anschliessend sauber
  beendet. Details: TODO.md (LES-024, LES-034).

### LES-024/LES-034: Keilnut-Polygonberechnung aus Zeichenroutine extrahiert 2026-09-14

- Die Berechnung der radialen Keilnut-Polygone aus
  `_draw_front_keyway_overlay()` als Qt-freie Funktion
  `build_keyway_front_polygons()` nach `preview_geometry.py` verschoben. Die
  Zeichenroutine skaliert und zeichnet nur noch die fertigen Punkte;
  `preview_widget.py` schrumpft von 856 auf 808 Zeilen.
- Zwei direkte Tests sichern Anzahl, Punktzahl, Innen-/Aussenradius und den
  gueltigen axialen Schnittbereich ab. Der bestehende Real-Qt-Painttest wurde
  auf einen tatsaechlich gueltigen Keilnutdatensatz korrigiert; zuvor lief er
  ohne Absturz, erreichte aber wegen fehlender Parameter keinen Polygonpfad.
- Vollstaendige Suite bestanden: 745 Stub-Qt- und 75 Real-Qt-Tests, keine
  Skips. Embedded-Start in der QtDragon-SIM ebenfalls fehlerfrei;
  `_finalize_ui_ready critical done` nach 8,075 s, anschliessend sauber
  beendet. Details: TODO.md (LES-024, LES-034).

### LES-024/LES-034: Primitive-Konvertierung aus dem Preview-Widget extrahiert 2026-09-14

- `_sample_arc` und `primitives_to_points` aus `preview_widget.py` als reine,
  Qt-freie Funktionen `sample_preview_arc()` und
  `preview_primitives_to_points()` nach `preview_geometry.py` verschoben. Die
  Widget-Methoden bleiben als schmale Kompatibilitaetsdelegierungen erhalten;
  `preview_widget.py` schrumpft dadurch von 909 auf 856 Zeilen.
- Drei direkte Regressionstests fuer degenerierte Boegen, verbundene
  Linienprimitive und ungueltige Altdaten ergaenzt. Die bestehenden
  Bogentests pruefen jetzt die echte Produktionsfunktion statt eine Kopie
  ihres Algorithmus im Test zu unterhalten.
- Vollstaendige Suite bestanden: 743 Stub-Qt- und 75 Real-Qt-Tests, keine
  Skips. Embedded-Start in der QtDragon-SIM ebenfalls fehlerfrei;
  `_finalize_ui_ready critical done` nach 8,409 s, anschliessend sauber
  beendet. Noch offen ist die schrittweise Verkleinerung der an QPainter
  gebundenen `_paint_*`-Routinen. Details: TODO.md (LES-024, LES-034).

### LES-024/LES-034: Schnittansicht-Diagrammberechnung aus preview_widget.py extrahiert 2026-09-14

- Erstes Verkleinerungspaket fuer `preview_widget.py` (LES-024/LES-044:
  "reine Vorschaugeometrie von Qt-Zeichenbefehlen trennen", Muster
  `compute_tool_preview_layout()`): die komplette Schnittansicht-
  Diagrammberechnung (`_interp_x_hits_at_z`, `_interp_x_at_z`,
  `_path_hits_at_slice`, `_front_operation_side`, `_front_slice_profile`,
  `_front_active_diameters`, `_front_reference_diameter`) als reine,
  Qt-freie Funktionen nach `preview_geometry.py` gezogen. Die
  Widget-Methoden sind jetzt einzeilige Delegierungen; Verhalten
  unveraendert. `preview_widget.py`: 1049 -> 909 Zeilen.
- Acht neue Tests (`tests/test_preview_front_slice_geometry.py`) laufen
  jetzt direkt gegen die reinen Funktionen, ohne echtes PyQt5 - vorher nur
  indirekt ueber das Widget erreichbar und ungetestet
  (`_front_operation_side`, `_front_slice_profile`,
  `_front_reference_diameter` hatten bisher keinen eigenen Test). Per zwei
  unabhaengig injizierten Bugs (Klassifikations- und Kandidatenfehler) als
  echte Regression verifiziert, danach zurueckgesetzt.
- Real in der SIM verifiziert: Embedded-Start fehlerfrei (9,2 s), Reiter
  UTILS/LatheEasyStep geoeffnet und "Schnittansicht" live umgeschaltet -
  kein Fehler im Log, kein Absturz.
- 740 Stub-/75 Real-Qt-Tests bestanden, keine Skips. Noch offen:
  `_sample_arc`/`primitives_to_points` (ebenfalls reine Geometrie, aber
  noch Widget-Methoden) sowie die `_paint_*`-Zeichenroutinen selbst.
  Details: TODO.md (LES-024, LES-034).

### LES-034 abgeschlossen: Schnittansicht-Interpolation fuer GROOVE/THREAD/ABSPANEN abgesichert 2026-09-14

- Letzter offener LES-034-Punkt ("komplexe Endgeometrien in Seiten- und
  Schnittansicht vergleichen"): GROOVE/THREAD/ABSPANEN haben - anders als
  die radiale Keilnut - keine separat kodierte Schnittansicht-Formel. Die
  Schnittansicht interpoliert den Durchmesser bei `slice_z` direkt aus
  demselben `op.path`, das die Seitenansicht zeichnet
  (`LathePreviewWidget._interp_x_hits_at_z()`); beide Ansichten koennen
  fuer diese Operationstypen strukturell nicht auseinanderlaufen.
- Diese gemeinsame Interpolation war bisher ohne eigenen Test. Vier neue
  Tests (`tests/test_preview_slice_interpolation.py`, real PyQt5): linearer
  Verlauf liefert den exakt interpolierten Wert, eine Nutflanke liefert
  beide Durchmesser (nicht nur einen), der kleinste Treffer wird als
  Durchmesser gewaehlt, ausserhalb des Pfad-Z-Bereichs kommt kein Treffer.
  Per zwei unabhaengig injizierten Abweichungen (fehlender zweiter Treffer
  an einer vertikalen Flanke; verfaelschter Interpolationswert) als echte
  Regression verifiziert, danach zurueckgesetzt.
- Damit ist LES-034 vollstaendig abgeschlossen: alle Checklistenpunkte der
  Preview-Pipeline sind entweder umgesetzt oder als Bestandsaufnahme ohne
  Fund dokumentiert. 732 Stub-/75 Real-Qt-Tests bestanden, keine Skips.
  Details: TODO.md (LES-034).

### LES-034 Radiale Keilnut: Schnittansicht-Overlay gegen Seitenansicht abgesichert 2026-09-14

- Bisher inline in `preview_widget.py._draw_front_keyway_overlay()`
  verborgene Radius-Berechnung des Schnittansicht-Overlays als eigene,
  reine Funktion `keyway_radial_slot_radii()` nach `preview_geometry.py`
  gezogen (analog zu `build_keyway_path`, `keyway_slice_bounds`,
  `build_keyway_slot_angles`, die dort bereits lagen).
- Direkt verglichen: fuer die radiale Keilnut (mode 0) liefert
  `keyway_radial_slot_radii()` (Schnittansicht, Radius bei festem Z) fuer
  beide `radial_side`-Werte exakt dieselbe Nuttiefe wie `build_keyway_path()`
  (Seitenansicht, Durchmesser entlang der Nutlaenge) - keine Abweichung
  gefunden, jetzt aber strukturell garantiert statt zufaellig konsistent,
  da beide Ansichten dieselbe Funktion nutzen.
- Zwei neue Tests (`tests/test_keyway_preview.py`), per gezielt injizierter
  Abweichung (`* 0.5` auf einen der beiden Radien) als echte Regression
  verifiziert, danach zurueckgesetzt. 732 Stub-/71 Real-Qt-Tests bestanden.
- Noch offen (LES-034): axiale Keilnut (mode != 0 - wird in der
  Schnittansicht aktuell gar nicht gezeichnet, daher kein Fund aber auch
  kein Vergleich moeglich) sowie GROOVE-/THREAD-Endgeometrien. Details:
  TODO.md (LES-034).

### LES-034 Anfahrt/Rueckzug/Werkzeugwechsel/Parken: Bestandsaufnahme, kein Fund 2026-09-14

- Geprueft, ob die Vorschau Anfahrt-, Rueckzug-, Werkzeugwechsel- oder
  Park-Bewegungen synthetisch erfindet, statt sie aus dem echten
  Bewegungsplan (G-Code) zu uebernehmen: kein Fund. Keine Preview-Quelle
  baut solche Segmente; die "retract"-Rolle in `preview_geometry.py`
  zeichnet nur die konfigurierten Rueckzugsebenen (XRA/XRI/ZRA/ZRI) als
  statische Referenzlinien, keine Werkzeugbewegung.
- Diese Garantie ist strukturell bereits vorhanden: `paintEvent()`
  (`preview_widget.py`) zeichnet jeden Operationspfad ueber einen eigenen
  `drawPolyline()`-Aufruf statt mehrere unabhaengige Pfade zu einer
  gemeinsamen Polylinie zu verketten - eine erfundene Verbindungslinie
  zwischen zwei Operationen war also bereits vor diesem Durchgang
  strukturell ausgeschlossen, nur bisher nicht dauerhaft geprueft.
- Neuer Regressionstest (`tests/test_preview_no_synthetic_links_between_operations.py`,
  real PyQt5): zwei weit auseinanderliegende Operationspfade duerfen nur als
  zwei getrennte 2-Punkt-Polylinien gezeichnet werden, nie als eine
  4-Punkt-Polylinie. Per gezielt injizierter Verkettung (`drawPolyline` ueber
  beide Pfade hinweg) als echte Regression verifiziert, danach zurueckgesetzt.
  730 Stub-/71 Real-Qt-Tests bestanden, keine Skips. Details: TODO.md
  (LES-034).

### LES-034 Preview-Szenenmodell mit getrennten Fachebenen 2026-09-14

- Neues Qt-freies `PreviewScene`-Modell mit expliziten Ebenen fuer
  Werkstueckgeometrie, verifizierte Werkzeugwege und Hilfsgeometrie.
  `PreviewPath` behaelt dabei optional den Bezug zur erzeugenden Operation.
- Bestehende flache Pfadreihenfolge und aktiver Index bleiben als
  Kompatibilitaetsansicht exakt erhalten. Kontur/Nut/Keilnut und Features
  werden als Werkstueck, Planen/Gewinde/Abspanen als Werkzeugweg sowie
  Rohteil/Rueckzug/Grenzen/Futter/Schrupphilfe als Hilfsgeometrie klassifiziert.
  Die nur nominale Bohrer-Silhouette bleibt bewusst Hilfsgeometrie.
- `refresh_preview()` erzeugt und uebergibt jetzt eine `PreviewScene`;
  `LathePreviewWidget` bewahrt die Ebeneninformation fuer die folgende
  getrennte Darstellung auf. Die Seitenansicht zeichnet Werkstueck blau,
  Werkzeugwege gruen beziehungsweise aktiv rot und allgemeine Hilfsgeometrie
  grau strichpunktiert; Spezialrollen und Legende wurden entsprechend
  beibehalten beziehungsweise erweitert.
- `primitive_strokes()` zerlegt alle Line-/Arc-/Polyline-Primitive in
  unabhaengige Zeichenstriche. Damit entstehen auch bei Feature- oder
  sonstigen Rollen keine erfundenen diagonalen Verbindungen mehr; zuvor war
  dies nur fuer einige fest verdrahtete Hilfsrollen verhindert.
- Fuenf neue Szenen-/Integrationsregressionen. 730 Stub-/70 Real-Qt-Tests
  bestanden. Embedded-Start in QtDragon fehlerfrei, ein Durchlauf und
  `critical done` nach 8,465 s. Nach der getrennten Strichdarstellung erneut
  real gestartet: fehlerfrei, ein Durchlauf, `critical done` nach 10,496 s
  (normale Laufzeitschwankung derselben SIM).

### LES-024 Zweites Migrationspaket: Vorschauausgabe gekapselt 2026-09-14

- `PreviewView` als schmale, zustandslose Ausgabeschnittstelle fuer Haupt-,
  Schnitt- und Konturvorschau eingefuehrt. `ui_preview.apply_preview_paths()`
  kennt damit keine konkreten Zeichenwidgets und deren Legacy-Signaturen mehr.
- Kollisionsstatus, Warntexte, aktive Bahn, Frontkontext, sichtbare
  Schnittansicht und optionales Konturpreview behalten ihr bisheriges
  Verhalten; Geometrieaufbau und Kollisionsberechnung wurden bewusst nicht
  veraendert.
- Vier neue Schnittstellentests; kompletter Stand 725 Stub-/70 Real-Qt-Tests,
  keine Skips.
- Embedded-Smoke-Test in der echten QtDragon-SIM bestanden: ein
  Finalisierungsdurchlauf, `critical done` nach 8,567 s, Preview-Initialisierung
  und kontrolliertes Beenden ohne neue Python-Ausnahme.

### LES-024 Erstes Migrationspaket: Step-Liste hinter schmaler View-Schnittstelle 2026-09-14

- Schmale View-Klasse `StepListView` (`ui_step_list_view.py`) eingefuehrt:
  buendelt die bisher verstreuten direkten `handler.list_ops`-Zugriffe
  (currentRow/count/item/row/blockSignals+setCurrentRow/hasFocus) hinter
  benannten Methoden (`selected_row()`, `count()`, `row_of()`,
  `set_item_text()`, `select_row()`, `has_focus()`, `is_bound()`).
  Zustandslos - liest `handler.list_ops` bei jedem Aufruf frisch, damit
  spaeteres (Neu-)Binden ohne Cache-Invalidierung funktioniert.
- Die zwoelf bereits in der vorherigen Bestandsaufnahme (2026-09-14,
  "LES-024 Restliche zwei Punkte konkretisiert") ermittelten Dateien mit
  `list_ops`-Zugriff zerfallen in zwei klar getrennte Gruppen: sechs
  Fachlogik-Dateien (ui_dirty/ui_flow/ui_persistence/ui_preview/
  ui_program/ui_selection) und sechs Bindungs-/Such-Dateien
  (ui_lifecycle/ui_split/ui_signals/ui_widget_lookup/ui_widgets/
  lathe_easystep_handler.py). Bewusste Entscheidung: nur die sechs
  Fachlogik-Dateien migrieren, die Bindungs-/Such-Dateien bleiben
  unveraendert - dort WIRD `handler.list_ops` erst gesucht/gebunden/
  validiert, das ist keine Fachlogik, die eine View-Abstraktion braucht.
- Acht neue Tests (`tests/test_step_list_view.py`) fuer die neue Klasse
  selbst (inkl. Exception-Schlucken bei kaputtem Widget, kein Caching
  von `handler.list_ops`). Per Wegverschieben der Implementierungsdatei
  verifiziert (Tests schlagen ohne sie mit `ModuleNotFoundError` fehl).
  721 Stub-/70 Real-Qt-Tests bestanden, keine Skips.
- Real in der SIM verifiziert: vollstaendiger Embedded-Start fehlerfrei,
  anschliessend mehrere Reiterwechsel (Programm/Planen/Kontur/Abspanen)
  ausgeloest - `handle_tab_changed`/`handle_selection_change` liefen ueber
  den neuen `StepListView`-Pfad ohne Fehler im Log. Der "Schritt
  hinzufuegen"-Button wurde bewusst nicht geklickt (oeffnet einen echten
  Speichern-Dialog, LES-047), da der zugrundeliegende Codepfad bereits
  ueber Reiterwechsel/Tests abgedeckt ist.
- Naechstes Paket (nicht Teil dieses Durchgangs): Vorschau-Geometrieaufbau
  in `ui_preview.py` sowie die LES-034-Ebenentrennung. Details: TODO.md
  (LES-024).

### LES-027 abgeschlossen: erster Reiterwechsel 4,682s -> 0,000s 2026-09-14

- Letzter offener LES-027-Punkt real in der SIM gemessen: erster
  Reiterwechsel (historisch 4,682s berichtet) ist jetzt 0,000s, ebenso
  alle folgenden Reiterwechsel - Nebeneffekt der Scope-Root-Memoisierung.
  Stepwechsel/Preview-Refresh nicht separat live gemessen (der
  Step-Anlage-Dialog fuer neue Operationen liesse sich nur mit einer
  echten Datei im Nutzerverzeichnis automatisiert durchklicken - bewusst
  nicht gemacht), nutzen aber denselben, bereits gefixten Codepfad.
  Timing-Log fuer `_handle_selection_change` (Stepwechsel) ergaenzt,
  analog zum bestehenden fuer Tab-Wechsel/Preview-Refresh.
- "Embedded und Standalone mit identischem Messpunkt vergleichen" und
  "Zeit bis sichtbares und bedienbares Panel messen": bereits durch
  LES-035 abgedeckt (Standalone ~1,7s, embedded ~8,8s bis "critical
  done").
- **Zusammenfassung der gesamten LES-027-Arbeit dieser Sitzung:** Start
  69,1s (zwei Durchlaeufe, mit Absturzrisiko durch den verwaisten
  `_schedule_post_start_init()`-Aufruf) -> ein Durchlauf ~18s -> Scope-
  Root-Cache ~10,8s -> verallgemeinerte Cache-Bedingung ~8,8s. Rund 87%
  Reduktion, jeder Schritt real in der SIM gemessen und funktional
  gegengeprueft, jede Aenderung testabgesichert.
- 713 Stub-/70 Qt-Tests bestanden, zwoelf Referenzen unveraendert. Alle
  LES-027-Punkte abgeschlossen, aus der Prioritaetstabelle entfernt.

### LES-035 Embedded-/Standalone-Paritaet abgeschlossen 2026-09-14

- Real verglichen: Standalone (`qtvcp -c easystep -u ./lathe_easystep_handler.py
  ./lathe_easystep.ui`) gegen den eingebetteten SIM-Lauf (QtDragon,
  UTILS-Tab). Beide schliessen `_finalize_ui_ready` nach EINEM Durchlauf
  ab, loesen dieselben 167/169 Tooltip-Namen auf (dieselben zwei
  fehlenden: `program_spindle_mode`, `program_preview_warnings` - bekannt,
  kein neuer Fund), laden dieselbe Werkzeugtabelle vom selben Pfad.
- Standalone ist deutlich schneller (~1,7s vs. ~8,8s) - der Unterschied
  liegt an `_auto_load_tool_table()`/`QSettings()` (embedded teilt sich
  QtDragons groessere Settings-Datei), kein Bug, bewusst nicht weiter
  verfolgt (das waere LES-027s Zustaendigkeit, nicht diese
  Paritaets-Frage).
- "Keine globalen Host-Widgets binden": bereits durch den fruehreren
  LES-024-Fund/-Fix (`_looks_like_panel_widget()`) abgesichert. Drei neue,
  gezielte Tests ergaenzt (`tests/test_embedded_vs_standalone_root_resolution.py`):
  Standalone-Root ist das Panel selbst; eingebettet unter einem generisch
  benannten Host-Fenster mit einem NAMENSKOLLIDIERENDEN Geschwister-Widget
  (eigenes `listOperations`, gehoert nicht zu uns) liefert
  `_pick_best_root()` weiterhin exakt unser Panel, nie das Host-Fenster
  oder den Geschwister-Zweig. Erkennungsfaehigkeit direkt nachgewiesen:
  mit einer simulierten Regression (Root-Erkennung faellt auf das
  Host-`QMainWindow` zurueck statt beim benannten Panel zu stoppen)
  schlaegt der Test zuverlaessig fehl.
- 713 Stub-/70 Qt-Tests bestanden, zwoelf Referenzen unveraendert (reine
  UI-Verifikation, kein G-Code-Bezug). Alle fuenf LES-035-Punkte
  abgeschlossen.

### LES-027 Memoisierungs-Bedingung verallgemeinert: ensure_advanced_widgets 2,7s -> 1,09s 2026-09-14

- Die Scope-Root-Memoisierung aus dem vorherigen LES-027-Fix half
  `ensure_advanced_widgets` noch nicht - dieser Aufruf (ueber `_ensure_row()`
  in `ui_advanced.py`, ~28 `get_widget_by_name()`-Aufrufe) laeuft VOR
  `_widget_name_cache_authoritative`, an das die Memoisierung bisher
  gekoppelt war.
- `tab_params`/`list_ops` sind aber schon durch das noch frueher laufende
  `ensure_core_widgets()` stabil gebunden und werden danach nicht mehr
  umgehaengt. Memoisierungs-Bedingung deshalb verallgemeinert: nutzt jetzt
  direkt deren Praesenz statt auf das spaetere Flag zu warten.
- Real in der SIM nachgemessen: `ensure_advanced_widgets` sank von
  ~2,5-2,7s auf ~1,09s. Gesamtzeit bis "critical done": ~8,8s (vorher
  ~10,8s, urspruenglich 69,1s fuer zwei Durchlaeufe). Panel funktional
  gegengeprueft (Tab-Wechsel, dynamische Felder zeigen korrekte Werte).
- Vier Tests (drei angepasst, einer neu), per `git stash` verifiziert.
  713 Stub-/67 Qt-Tests bestanden, zwoelf Referenzen unveraendert.
  Details: TODO.md (LES-027).

### Projektbereinigung, LES-036-SIM-Abnahme und Resolver-Fix 2026-09-14

- `TODO.md` von 2.849 Zeilen historischem Sitzungsprotokoll auf eine kurze,
  ausschliesslich offene Aufgabenliste reduziert. Abgeschlossene Befunde
  bleiben in diesem Changelog und den Berichten unter `doc/` erhalten.
  Aktuelle Teststaende in README, DEV, ROADMAP und TODO synchronisiert.
- `Planen_Radius.ngc` in der nativen QtDragon-SIM vollstaendig im AUTO-Modus
  bis `M30` ausgefuehrt: 272,6 s, leerer NML-Fehlerkanal, T1 und definierte
  Endposition. Zusaetzlicher Backplot mit rein temporaer nahem
  Werkzeugwechselpunkt macht die Radiuskante lesbar. LES-036 abgeschlossen.
- Beim kontrollierten Beenden der SIM einen bisher ungetesteten realen Fehler
  gefunden: `WidgetResolver._log()` referenzierte ohne injizierten Logger den
  nie definierten Namen `_LOGGER`. Modul-Logger ergaenzt und der konkrete
  Fallbackpfad regressionstestet.
- Der anschliessende echte Embedded-Start deckte einen zweiten Rueckfall auf:
  Der ausgelagerte UI-Lifecycle rief noch den bereits entfernten, wirkungslosen
  `_schedule_post_start_init()`-Callback auf. Verwaisten Aufruf entfernt und
  einen AST-basierten Vertragstest fuer alle direkten privaten Handler-Aufrufe
  des Lifecycle-Moduls ergaenzt. Der korrigierte Embedded-Start schloss ohne
  Ausnahme nach 69,1 s ab. Ursache des teuren zweiten Durchlaufs ist das im
  ersten Durchlauf nicht gebundene `listOperations`; als aktueller
  LES-027-Befund dokumentiert.
- Aktueller Stand: 713 Stub-/63 Real-Qt-Tests; zwoelf Referenzen bestehen
  statische Pruefung und nativen `rs274`.

### LES-027 Scope-Root-Memoisierung: connect_param_change_signals von 6,77s auf 0,02s 2026-09-14

- Nachdem der erste LES-027-Fix (ein Finalisierungsdurchlauf statt zwei)
  real in der SIM bestaetigt war, war `connect_remaining_signals` (~6,6s)
  der neue groesste Einzelposten. Profiliert: fast die gesamte Zeit steckte
  in `connect_param_change_signals`.
- Root Cause: `get_widget_by_name()` (`ui_widget_lookup.py`) berechnete
  seinen internen "Panel-Scope-Root" (mehrstufiger `parentWidget()`-Walk,
  pro Stufe zwei volle rekursive `findChild()`-Scans) bei JEDEM Aufruf neu
  - `setup_param_maps()` ruft die Funktion ca. 100x pro Start auf. Behoben:
  der Scope-Root wird jetzt einmalig berechnet und gecacht, sobald der
  Widget-Baum vollstaendig ist (`_widget_name_cache_authoritative`).
- Real in der SIM nachgemessen: `connect_param_change_signals` sank von
  6,77s auf 0,02s. Gesamtzeit bis "critical done": ~10,8s (vorher ~18s,
  urspruenglich 69,1s fuer zwei Durchlaeufe). Panel funktional
  gegengeprueft (Tab-Wechsel, Parameterfelder reagieren korrekt).
- Drei neue Tests, per `git stash` verifiziert. 713 Stub-/66 Qt-Tests
  bestanden, zwoelf Referenzen unveraendert. Details: TODO.md (LES-027).

### LES-027 Fix real in der SIM bestaetigt: nur noch ein Finalisierungsdurchlauf 2026-09-14

- Nutzerhinweis, dass die SIM zur Verifikation zur Verfuegung steht -
  vorherige Aussage, das koenne nicht selbst geprueft werden, war falsch.
- SIM real gestartet (Embedded-Panel, UTILS-Tab angeklickt), Debug-Log
  ausgewertet: `_finalize_ui_ready` schliesst jetzt nach EINEM Durchlauf ab
  (log-bestaetigt: `"DONE after pass 1 — all critical widgets found,
  skipping further passes"`), `listOperations` ist bereits im ersten
  Durchlauf real gebunden, kein Absturz durch den vormals verwaisten
  `_schedule_post_start_init()`-Aufruf.
- Gesamtzeit bis "critical done": ~18 s (vorher 69,1 s fuer zwei
  Durchlaeufe). `ensure_core_widgets` selbst jetzt nur noch ~0,11 s
  (vorher 23,5 s). Neuer groesster Einzelposten: `connect_remaining_signals`
  mit ~6,6 s - noch nicht einzeln profiliert, als neuer LES-027-Punkt
  dokumentiert. Details: TODO.md (LES-027).

### LES-034 Nut-Vorschaugeometrie erstmals getestet (kein Fund) 2026-09-14

- Nachuntersuchung der bewusst ausgeklammerten Operationstypen: `build_drill_path()`
  ist bereits umfassend getestet; Seiten- und Schnittansicht teilen sich
  dieselbe Interpolationsfunktion (strukturell konsistent, kein Fund).
- `build_groove_preview_path()` hatte dagegen KEINE Testabdeckung, obwohl
  es die Vorschau fuer jede GROOVE-Operation liefert. Acht neue Unit-Tests
  sichern die interne Korrektheit ab: Uebereinstimmung mit dem
  handgepflegten Referenz-Fixture, alle Bezugskanten, radiale/axiale Nut,
  und das sicherheitsrelevante Vorzeichen Innen-/Aussenbearbeitung
  (Innen-Nut vergroessert den Durchmesser am Nutgrund).
- Kein Bug gefunden - die bestehende Logik war bereits korrekt, jetzt
  aber gegen eine Regression abgesichert (Test-Wirksamkeit direkt per
  vertauschtem Vorzeichen nachgewiesen). 711 Stub-/59 Qt-Tests bestanden,
  zwoelf Referenzen unveraendert. Details: TODO.md (LES-034).

### LES-034 Vorschau-Pfad gegen tatsaechliche G-Code-Ausgabe verifiziert (kein Fund) 2026-09-14

- Nutzerauftrag: dargestellten Werkzeugweg der zwoelf Referenzprogramme
  gegen die tatsaechliche G-Code-Ausgabe vergleichen. **Ergebnis: keine
  Abweichung gefunden** - alle neun vergleichbaren ABSPANEN-/FACE-Faelle
  mit explizitem Schlichtpfad stimmen exakt (< 0.01mm) ueberein.
- Zwei eigene Script-Fehler beim ersten Anlauf zunaechst faelschlich als
  Bugs interpretiert (falsche Vergleichsrichtung bei tessellierten
  Boegen; ein Text-Marker traf zuerst auf einen unrelatierten Kommentar)
  - erst durch genaues Nachschauen im rohen G-Code widerlegt, bevor eine
  unnoetige Codeaenderung gemacht wurde.
- Neuer dauerhafter Regressionstest (`tests/test_preview_matches_gcode_output.py`,
  9 Faelle), Erkennungsfaehigkeit per injizierter 1mm-Abweichung
  nachgewiesen. 703 Stub-/59 Qt-Tests bestanden, zwoelf Referenzen
  unveraendert (reine Verifikation). DRILL/GROOVE brauchen eine andere
  Methodik (Vorschau zeigt dort die Werkzeugform, nicht den Weg) - nicht
  Teil dieses Durchgangs. Details: TODO.md (LES-034).

### LES-024 Restliche zwei Punkte konkretisiert (Bestandsaufnahme, kein Umbau) 2026-09-14

- Tooltips/Sprach-IDs fuer die drei neuen Panel-Module bereits
  vollstaendig erfuellt (der generische `ui_parts/*.ui`-Scan von
  `ui_static.py` deckt sie automatisch ab) - real stichprobenartig
  verifiziert (`ui.btn_slice_view.toolTip` in allen drei Sprachen).
- "Controller"-Zuordnung bereits pro fachlichem Anliegen erfuellt (nicht
  1:1 pro UI-Container) - bewusst nicht aufgebrochen.
- "Validierung": kein Code-Mangel gefunden, sondern eine offene
  Design-Frage (Buttons vorab sperren vs. beim Klick validieren) - nicht
  ohne Nutzerentscheidung umgesetzt.
- "Direkte Widgetzugriffe durch definierte Schnittstellen ersetzen":
  Umfang ermittelt (zwoelf betroffene Dateien) - bewusst nicht blind als
  invasiver Mehrdateien-Umbau umgesetzt, bleibt offen fuer einen separat
  freizugebenden Schritt. Details: TODO.md (LES-024).

### LES-024 SICHERHEITSFUND: Embedded-Panel-Erkennung nach Step-Liste-Auslagerung repariert 2026-09-13

- Beim gezielten Nachpruefen des letzten offenen LES-024-Punkts
  ("Embedded- und Standalone-Laden testen") gefunden: `_looks_like_panel_widget()`
  (`ui_registry.py`) - zentral fuer die Panel-Root-Erkennung im
  eingebetteten Betrieb unter generisch benannten Host-Fenstern
  ("MainWindow"/"VCPWindow") - prueft SYNCHRON in `bootstrap_widget_refs()`,
  also bevor die asynchron nachgeladenen Panel-Module (Step-Liste,
  Aktionsleiste, Vorschau) ueberhaupt existieren.
- Der Check verliess sich bisher auf `listOperations`, das durch die
  vorherige LES-024-Aenderung dieser Sitzung (Step-Liste als eigenes
  Panel-Modul) in diesem fruehen Zeitfenster nicht mehr existiert -
  eigenes Nebenprodukt der eigenen Umbauten, ohne dieses Nachpruefen
  unentdeckt geblieben.
- Behoben: zusaetzlich auf `stepListPanel` pruefen (der Container-
  Widget, das sofort nach `uic.loadUi()` existiert, unabhaengig vom
  Ladezustand).
- Drei neue Tests, per direkter Code-Entfernung der Korrektur verifiziert.
  694 Stub-/59 Qt-Tests bestanden, zwoelf Referenzen unveraendert.
  Details: TODO.md (LES-024).

### LES-024 SICHERHEITSRELEVANTER LAYOUT-FIX: Vorschau als eigenes Panel-Modul ausgelagert 2026-09-13

- Vorschau/Schnittansicht (`previewWidget`/`previewSliceWidget`/
  `btn_slice_view`) liegen jetzt in `ui_parts/previewPanel.ui`, analog
  zum Step-Liste/Aktionsleiste-Split.
- **Echter Fund beim vorgeschriebenen Screenshot-Vergleich:** die
  bestehende Laufzeit-Verschiebung der Vorschau (`_dock_preview_below_scroll()`)
  liess den nach dem Verschieben leeren neuen Container im Scroll-Bereich
  zurueck - blosses Verstecken reichte nicht, der Platzanspruch im
  Eltern-Layout blieb bestehen und machte die angedockte Vorschau sichtbar
  zu gross (220px statt 140px Hoehe, 170.129 von 700.000 Pixeln des
  Vergleichs-Screenshots unterschiedlich). Behoben: der leere Container
  wird jetzt vollstaendig aus seinem Layout entfernt statt nur versteckt.
  Nach dem Fix: 37 von 700.000 Pixeln (reine Anti-Aliasing-Groessenordnung).
- Ohne den vom Nutzer angeordneten Screenshot-Vergleich waere dieser
  Fehler nicht durch die automatisierte Testsuite erkannt worden.
- Vier neue Tests (`tests/test_preview_panel_ui_loader.py`, inkl. gezieltem
  Regressionstest fuer den gefundenen Layout-Bug), per `git stash`
  verifiziert. 694 Stub-/56 Qt-Tests bestanden, zwoelf Referenzen unter
  rs274 bestanden. Details: TODO.md (LES-024).

### LES-024 Step-Liste/Programmverwaltung als eigenes Panel-Modul ausgelagert 2026-09-13

- Nach dem im Architekturdokument (LES-044) festgelegten Muster: Step-Liste
  (`listOperations` + Step/Programm speichern/laden) und Aktionsleiste
  (hinzufuegen/loeschen/verschieben/erzeugen/Aenderungen speichern) liegen
  jetzt in eigenen `.ui`-Dateien (`ui_parts/stepListPanel.ui`,
  `ui_parts/stepActionsPanel.ui`), analog zum bestehenden Reiter-Split.
  Alle objectNames blieben unveraendert, kein anderer Code musste
  angepasst werden.
- Erste Sitzungs-Aenderung, die die Haupt-`.ui`-Datei selbst umstrukturiert.
  Zusaetzlich zur automatisierten Pruefung per Nutzerentscheidung mit
  einem echten Screenshot-Vergleich abgesichert (offscreen-Rendering vor/
  nach der Aenderung, Pixel-fuer-Pixel verglichen): 25 von 700.000 Pixeln
  unterschiedlich, alle auf einer einzelnen Anti-Aliasing-Trennlinie -
  keine strukturelle Abweichung.
- Drei neue Tests, per `git stash` verifiziert. 694 Stub-/53 Qt-Tests
  bestanden, zwoelf Referenzen unveraendert. Details: TODO.md (LES-024).

### LES-020 Radius-Warnung an die Vorschau-Warnungspipeline angebunden 2026-09-13

- Nutzerrueckfrage zum LES-020-Fund (Werkzeug-Orientierung/-Radius-
  Warnsystem implementiert, aber nie angezeigt): Nutzerentscheidung
  "anbinden", da eine real gepflegte Werkzeugtabelle Radius und
  Orientierung grundsaetzlich enthaelt.
- Bei der Umsetzung zeigte sich: der Orientierungs-Abgleich
  (`tool_logic.py::collect_tool_orientation_warnings`) ist eine bereits
  vollstaendig redundante Zweitimplementierung - `checks.py::validate_program_setup()`
  hat laengst einen eigenen, bereits aktiven Orientierungs-Check in
  `prog["__warnings"]`. Eine Anbindung haette dieselbe Warnung doppelt
  ausgegeben, deshalb NICHT verdrahtet.
- Nur `radius_warning_details()` ist tatsaechlich neu: jetzt in
  `ui_preview.py::collect_preview_state()` eingehaengt. Werkzeuge ohne
  bekannten Radius (Kompensation wird dadurch stillschweigend
  deaktiviert) erscheinen jetzt als Warnung im Panel.
- Drei neue Tests (`tests/test_tool_warning_wiring.py`), per `git stash`
  verifiziert. 694 Stub-/50 Qt-Tests bestanden, zwoelf Referenzen
  unveraendert. Details: TODO.md (LES-020).

### LES-020 187 Zeilen toten Code aus dem Handler entfernt 2026-09-13

- Systematischer Scan aller privaten Handler-Methoden auf Null-Referenzen
  (kein Aufrufer irgendwo im Repo) im Rahmen der LES-024/LES-044-Arbeit
  fand 17 bestaetigt tote Methoden, darunter eine komplette, nie
  aufgerufene Zweit-Implementierung der Kern-Widget-Suche
  (`_find_all_core_widgets_comprehensive()`, parallel zur tatsaechlich
  genutzten `ensure_core_widgets()`-Familie) und ein komplett
  deaktivierter Init-Queue-Mechanismus (`_schedule_post_start_init()`/
  `_post_start_init()` plus sechs nie aufgerufene Step-Methoden).
- Vor jeder Entfernung einzeln geprueft, dass die zugrunde liegende
  Funktionalitaet entweder anderswo direkt genutzt wird oder tatsaechlich
  folgenlos tot ist (kein String-Dispatch, keine Tests, kein indirekter
  Aufruf uebersehen). Details: TODO.md (LES-020).
- **Separater Fund, bewusst NICHT geloescht:** drei zusammengehoerige
  Methoden (`_tool_orientation_mismatch`, `_collect_tool_orientation_warnings`,
  `_radius_warning_details`) bilden ein vollstaendig implementiertes, aber
  nie an die tatsaechliche Warnungs-Pipeline angebundenes Warnsystem fuer
  Werkzeug-Orientierung/-Radius. Ob das absichtlich inaktiv ist oder
  unvollendet blieb, ist eine fachliche Entscheidung - siehe TODO.md.
- 691 Stub-/50 Qt-Tests bestanden, `lathe_easystep_handler.py` importiert
  weiterhin fehlerfrei mit echtem PyQt5, zwoelf Referenzen unveraendert.

### LES-044 Architekturdokument fuer die Panel-Modularisierung 2026-09-13

- Nutzerauftrag "eines der grossen Architektur-Themen anfangen": LES-044
  fordert selbst, die Zielarchitektur (Geruest/Panel-Module/Text/
  Darstellung/Generator) als kurzes Dokument festzuhalten, BEVOR weitere
  LES-020/024/034-Extraktionen vorgenommen werden - das ist jetzt erste
  Voraussetzung fuer die weitere LES-024-Arbeit.
- Neu: [doc/ARCHITECTURE_MODULES.md](doc/ARCHITECTURE_MODULES.md)
  beschreibt Ist-Stand je Schicht (Geruest/`ui_split.py` und Text/
  `TRANSLATIONS` erfuellen die Vorgabe bereits, Generator ist bereits
  vollstaendig Qt-unabhaengig), definierte Schnittstellen zwischen den
  Schichten und eine begruendete Reihenfolge fuer die naechsten
  Schritte (zuerst `render_tool_preview()` als kleinster konkreter
  Umbaukandidat, dann Step-Liste/Programmverwaltung, dann Vorschau/
  Schnittansicht als eigene Panel-Module).
- Reine Dokumentation, keine Codeaenderung.

### LES-044 render_tool_preview() entkoppelt (erster konkreter Umbau) 2026-09-13

- Neue reine Funktion `compute_tool_preview_layout()` (`tool_logic.py`)
  uebernimmt die komplette Geometrieberechnung fuer die Werkzeug-Vorschau
  (Einsatz-Polygon, Schaft, Winkel, Nasenradius-Position); `render_tool_preview()`
  enthaelt jetzt nur noch `QPainter`-Zeichenaufrufe. Reine Verschiebung,
  kein beabsichtigter Verhaltensunterschied.
- Diese Funktion hatte bisher KEINE Testabdeckung. Sechs neue Tests
  (`tests/test_tool_preview_layout.py`, echtes PyQt5) decken alle vier
  Werkzeugfamilien und die Innen-/Aussenlage der Nasenradius-Position ab,
  per `git stash` gegen den alten Code verifiziert.
- 691 Stub-/50 Qt-Tests bestanden, zwoelf Referenzen unveraendert (reine
  UI-Aenderung). Details: TODO.md (LES-044).

### LES-022 abgeschlossen: zentraler Bewegungs- und Modalzustand 2026-09-13

- Alle Checklistenpunkte erledigt (Positions-Tracking in allen sechs
  Operations-Generatoren, G90/G91/G94/G95/G96/G97/G18/G40-42-Verwaltung,
  M3/M4/M5/M7/M8/M9 und Werkstuecknullpunkt-Pruefung). Aus der
  Prioritaetstabelle entfernt.
- Ein Punkt bleibt bewusst dauerhaft offen (Design-Entscheidung, kein
  TODO): die Nutbreiten-Nachverfolgung im `gcode_groove.py`-`o220`-Zyklus
  wird nicht in Python nachgerechnet, um keine Duplizierung der
  Zustelllogik des Makros einzugehen - Details: TODO.md.

### LES-049 geloeschte/umbenannte Kontur bei Abspanen-Step wird jetzt sofort gewarnt 2026-09-13

- Fund waehrend der LES-047/LES-048-Nachuntersuchung: eine ABSPANEN-
  Operation, deren `contour_name` auf eine spaeter geloeschte oder
  umbenannte CONTOUR-Operation verweist, blieb in `validate_program_setup()`
  bisher stumm - keine Warnung waehrend der Bearbeitung, erst ein harter
  Fehler beim naechsten Speicherversuch.
- Kein Sicherheitsrisiko wie LES-046/047/048 (bereits ein lauter Abbruch,
  keine still falsche Ausgabe), aber eine vermeidbare Ueberraschung.
  Warnung ergaenzt, sobald `contour_name` gesetzt aber nicht aufloesbar
  ist (leerer Name bleibt bewusst unbemerkt - ueber die UI beim Anlegen
  bereits ausgeschlossen).
- Drei neue Tests, per `git stash` verifiziert. 691 Stub-/44 Qt-Tests,
  zwoelf Referenzen und 43 Matrixfaelle unter rs274 bestanden, keine
  Referenzaenderung. Details: TODO.md.

### LES-048 SICHERHEITSKRITISCHER FIX: Loeschen/Verschieben eines Steps verschob dessen dirty-Markierung nicht mit 2026-09-13

- Gefunden als direkte Folgeuntersuchung von LES-047: `_dirty_operation_indices`
  ist eine reine Menge von Listenpositionen. Loeschen einer Operation
  verschiebt alle nachfolgenden Operationen um eine Position nach vorn,
  Verschieben nach oben/unten vertauscht zwei Positionen - in beiden
  Faellen wurde die dirty-Menge bisher nie nachgezogen.
- Ergebnis: eine zuvor als geaendert markierte Operation "wanderte"
  stillschweigend auf eine ANDERE, tatsaechlich unveraenderte Operation,
  waehrend die wirklich geaenderte Operation ihre Markierung komplett
  verlor. "Aenderungen speichern" haette dadurch die falsche Step-Datei
  mit fremdem Inhalt ueberschrieben und die echte Aenderung
  stillschweigend verloren - in einem sehr gewoehnlichen Workflow (Steps
  umsortieren oder loeschen).
- Real reproduziert (direkter Aufruf der echten Handler-Methoden) und
  behoben: drei neue Hilfsfunktionen in `ui_dirty.py`
  (`reindex_dirty_operations_after_removal()`, `swap_dirty_operation_indices()`,
  `reindex_dirty_operations_after_insert()`), eingebunden in Loeschen,
  Verschieben nach oben/unten und den Sonderfall "Programmkopf
  nachtraeglich an Position 0 einfuegen".
- Fuenf neue Regressionstests, alle fuenf per `git stash` gegen den alten
  Code verifiziert. 688 Stub-/44 Qt-Tests, zwoelf Referenzen und 43
  Matrixfaelle unter rs274 bestanden, keine Referenzaenderung. Details:
  TODO.md.

### LES-047 (Teil 1): "Aenderungen speichern" liess fehlende Step-Datei-Verknuepfung unbemerkt 2026-09-13

- Nutzerbericht: nach dem Laden eines Programms mit urspruenglich einzeln
  gespeicherten Steps wurden Aenderungen ueber "Aenderungen speichern"
  scheinbar nicht in die Step-Dateien uebernommen.
- Der Kern-Mechanismus selbst ist korrekt (direkt getestet: die Step-
  Datei-Verknuepfung uebersteht einen vollstaendigen Speichern/Laden-
  Rundlauf, und die Formular-Sync-Logik ist bereits gezielt dagegen
  abgesichert, sie beim Bearbeiten zu verlieren).
- Aber ein echter, real reproduzierter Fehler in `handle_save_changes()`
  gefunden: ein geaenderter Step OHNE Verknuepfung wurde bisher VOELLIG
  STILL uebersprungen - die Abschlussmeldung zeigte trotzdem "Erfolg" (nur
  die Anzahl der TATSAECHLICH gespeicherten Steps), ohne zu erwaehnen,
  dass ein anderer geaenderter Step dabei komplett uebersprungen wurde.
  Genau das erklaert den Bericht.
- Behoben: eine explizite Warnung mit der Anzahl betroffener Steps wird
  jetzt angehaengt. Neuer Regressionstest, per `git stash` gegen den alten
  Code verifiziert (reproduziert exakt die alte, irrefuehrende Meldung).

### LES-047 (Teil 2): "Aenderungen speichern" fordert fehlende Step-Datei-Verknuepfung jetzt automatisch ein 2026-09-13

- Nutzervorgabe ("Das soll automatisch funktionieren"): der bereits beim
  Anlegen eines neuen Steps geltende Zwang (Step-Datei anlegen ODER eine
  bestehende laden, geloest erst durch Loeschen des Steps im Panel) galt
  bisher nicht fuer "Aenderungen speichern" - ein unverknuepfter Step
  wurde dort nur noch gewarnt.
- Jetzt konsistent: `handle_save_changes()` ruft fuer jeden geaenderten,
  unverknuepften Step denselben Verknuepfungs-Dialog auf wie "Programm
  speichern". Akzeptiert der Nutzer, wird der Step automatisch verknuepft
  und sein aktueller Inhalt sofort gespeichert - keine separate manuelle
  Aktion mehr noetig. Bricht der Nutzer ab, bleibt es bei der Warnung aus
  Teil 1 (kein harter Abbruch der gesamten Aktion).
- Zwei neue Regressionstests, je per `git stash` gegen den alten Code
  verifiziert. 683 Stub-/44 Qt-Tests, zwoelf Referenzen und 43 Matrixfaelle
  unter rs274 bestanden, keine Referenzaenderung. Details: TODO.md.

### LES-042 abgeschlossen: TURN/BORE-Kuehlmittelfehler behoben (reale Belege statt Vermutung) 2026-09-13

- Die Kernfrage ("muessen alte gespeicherte TURN/BORE-Programme weiter
  ladbar sein?") liess sich mit realen Belegen beantworten: das
  Speicherformat hat seit Projektbeginn nur eine einzige Version, keine
  op-typ-spezifische Ablehnung oder Migration existiert. Ein alt
  gespeichertes Programm mit TURN/BORE-Step laedt deshalb heute
  unveraendert und wird vom Dispatcher weiterhin an `gcode_for_turn`/
  `gcode_for_bore` gereicht - kein toter Code.
- Damit war der urspruengliche Fund ein echter, ueber alte Dateien
  erreichbarer Bug: beide Funktionen gaben Kuehlmittel per direktem `M8`
  aus, ohne je `M9` auszugeben - eine Operation mit `coolant=False` liess
  zuvor aktiviertes Kuehlmittel einfach weiterlaufen. Behoben: beide
  nutzen jetzt `emit_coolant()` wie alle anderen Operationstypen.
- Neuer Regressionstest, per `git stash` gegen den alten Code verifiziert
  (beide Faelle schlagen ohne den Fix fehl). 681 Stub-/44 Qt-Tests, zwoelf
  Referenzen und 43 Matrixfaelle unter rs274 bestanden, keine
  Referenzaenderung. Details: TODO.md.

### LES-022 (vierte Etappe): Positions-Nachverfolgung durch die Schrupp-Baender 2026-09-13

- Die zuvor als "deutlich groessere Etappe" zurueckgestellte Positions-
  Nachverfolgung durch `rough_turn_parallel_x()`/`rough_turn_parallel_z()`
  ist jetzt umgesetzt: beide Funktionen tragen ihre tatsaechlich erreichte
  Endposition selbst in den zentralen Bewegungszustand ein, statt dass der
  Aufrufer danach bedingungslos `clear()` setzen muss.
- Nutzen: ein kombinierter Schruppen+Schlichten-Step (ein Funktionsaufruf)
  kann den Rueckzug vor dem Schlichtschnitt jetzt korrekt ueberspringen,
  wenn das Schruppen bereits nachweislich exakt dort endete - vorher wurde
  dieser ungefaehrliche, aber unnoetige Rueckzug immer zusaetzlich
  ausgegeben. Drei neue Tests, per `git stash` gegen den alten Code
  verifiziert (schlagen ohne die Aenderung fehl).
- Ausserdem zwei bereits durch Codeaudit abgesicherte Punkte formal
  abgeschlossen: die uebrigen modalen G-Codes (G90/91, G94/95, G18,
  G40/41/42) und M-Codes/Werkstuecknullpunkt (M3/4/5, M7/8/9, G54) haben
  keinen dynamisch umgeschalteten Zustand, der ueberhaupt "verwaltet"
  werden muesste - strukturell dasselbe Argument wie bei G40/41/42
  (Aktivierung und Ausgabe im selben Funktionsaufruf zwingend gepaart).
- Keine der zwoelf Referenzen oder 43 Matrixfaelle nutzt die absolute
  Rueckzugskonfiguration, die den konkreten Optimierungsfall ausloest -
  keine Referenzaenderung. 679 Stub-/44 Qt-Tests bestanden. Details:
  TODO.md.

### LES-046 SICHERHEITSKRITISCHER FIX: Vorschub-Unterbrechung (Spanbruch) schnitt kein Material 2026-09-13

- Gefunden waehrend der LES-022-Codeaudit-Arbeit: die "Vorschub-
  Unterbrechung"/"Spanbruch"-Checkbox (`pause_enabled`/`pause_distance`)
  hat seit ihrer Einfuehrung (Juli 2026) NIE tatsaechlich Material
  geschnitten, wenn sie aktiv war. ABSPANEN gab statt einer G1-Schnittzeile
  einen Subroutinenaufruf aus, dessen Definition NUR eine Verweilzeit
  (`G4`) enthielt - keine Bewegung. Die gesamte Schnittstrecke (oft
  10-20mm) wurde durch einen kurzen Halt ersetzt; das Programm lief danach
  unveraendert weiter, als sei das Material entfernt worden - der naechste
  Pass bzw. Schlichtschnitt haette auf praktisch unbearbeitetes Rohmass
  statt auf das erwartete Restaufmass getroffen. Per rs274-Bewegungsspur
  (STRAIGHT_FEED/DWELL) zweifelsfrei bestaetigt. PLANEN war noch
  weitergehender wirkungslos: die Subroutine wurde dort nie aufgerufen.
- **Warum das nie auffiel:** alle bestehenden Tests pruefen nur, ob der
  Subroutinenaufruf mit den richtigen Zahlen im Text auftaucht - nie, ob
  die Subroutine diese Zahlen tatsaechlich anfaehrt. Betrifft auch direkt
  die urspruengliche Anfrage ganz am Anfang dieser Sitzung zur Verifikation
  von Zyklus-/ISO-Pfad mit Vorschub-Unterbrechung - die damalige
  "erledigt"-Einschaetzung beruhte auf demselben blinden Fleck.
- **Fix:** `_emit_segment_with_pauses()` zerlegt die Schnittstrecke jetzt
  selbst in `pause_distance`-lange Teilschnitte mit echten `G1`-Zeilen,
  gefolgt von `G4`-Pausen zum Spanbrechen - als explizite, direkt lesbare
  Folge statt einer Laufzeit-Subroutine. PLANEN wirft jetzt einen klaren
  `ValueError` statt die Checkbox still zu ignorieren (kein
  bewegungsbasierter Ersatzpfad fuer den dortigen G72-Zyklus vorhanden -
  eigener, groesserer Folgeschritt).
- Alle betroffenen Bestandstests repariert (pruefen jetzt echte G1/G4-
  Bewegung statt Makro-Textparameter), per `git stash` gegen den alten Code
  verifiziert (3 von 6 aktualisierten/neuen Tests schlagen ohne den Fix
  fehl). Per rs274-Bewegungsspur UND echtem SIM-Maschinenlauf bestaetigt
  (fehlerfrei, korrekte Endposition). Keine der zwoelf Referenzen oder 43
  Matrixfaelle nutzt `pause_enabled=True` - keine Referenzaenderung. 676
  Stub-/44 Qt-Tests bestanden. Details: TODO.md (LES-046).

### LES-033 abgeschlossen: Gewindevorschau-Geometrie numerisch gegen echten G76-Befehl verifiziert 2026-09-13

- `build_thread_path()` war bereits die einzige, reale (nicht symbolische)
  Vorschau-Geometriefunktion fuer Gewindeoperationen - abgeleitet aus
  Steigung, Tiefe, Start-Z und Laenge, inklusive Vorlauf/Auslauf-Taper und
  Rechts-/Linksgewinde. Bisher aber nie numerisch gegen den tatsaechlich
  erzeugten G76-Befehl verifiziert, nur strukturell getestet.
- Neuer Regressionstest vergleicht Z-Endwert, Kronen-/Kerndurchmesser und
  Vorlauf-Taperlaenge der Vorschau direkt gegen den geparsten G76-Befehl,
  fuer alle vier Kombinationen Aussen/Innen x Rechts/Links, mit und ohne
  Vorlauf - alle stimmen exakt ueberein.
- Eine kleine, bewusst nicht geratene Detailfrage bleibt offen: der
  Innen-Vorlaufpunkt liegt auf dem Kerndurchmesser statt dem Major-
  Durchmesser (konsistent zur eigenen Kronen-/Kerndurchmesser-Definition
  der Funktion) - ob das die anschaulichste Darstellung ist, wurde nicht
  gegen einen realen Backplot fuer diesen speziellen Fall geprueft (betrifft
  nur die Vorschau-Optik, LinuxCNCs eigene G76-Zyklusimplementierung fuehrt
  den tatsaechlichen Taper aus). 676 Stub-/44 Qt-Tests bestanden. Details:
  TODO.md.

### Dokumentationspflege: drei laengst abgeschlossene Punkte hatten noch eine Prioritaetszeile 2026-09-13

- LES-018 (G70-Wiederverwendung fuer separaten Schlichtstep), LES-020
  (Handler-Verkleinerung) und LES-031 (redundante Ausgabe bereinigen)
  waren laut ihrer eigenen Detail-Abschnitte (alle Checkboxen abgehakt,
  mit Umsetzungsnotiz) bereits vollstaendig abgeschlossen, standen aber
  noch in der Prioritaetstabelle. Keine Code-/Testaenderung, reine
  Nachpflege gemaess der projekteigenen Regel ("Erledigte Punkte werden
  entfernt").

### LES-015 abgeschlossen: Innenkontur-Testmatrix war bereits vollstaendig abgedeckt 2026-09-12

- Bei genauerer Pruefung deckt die bestehende, bei jeder Sitzung real
  gegen rs274 verifizierte 43-Matrix bereits alle neun offenen Punkte ab -
  nur ohne dass es in dieser TODO-Sektion nachvollzogen war.
- Vier Profilformen (Zylinder, Stufe, Konus, Radius mit I != 0) x zwei
  Konturrichtungen x drei Modi (Schruppen/Schlichten/beides) = 24
  Matrixfaelle, plus zwei Werkzeugradiuskorrektur-Faelle, alle unter
  rs274 bestanden und zusaetzlich pytest-seitig geometrisch geprueft
  (XRI-Grenze, Bogenerhalt, Materialgrenze).
- Reale SIM-Backplot-Bestaetigung ist bewusst repraesentativ (ein Fall je
  Profilform, inkl. dem neuen LES-005-Freistichfall), nicht alle 26
  Matrixfaelle einzeln - Begruendung: dieselbe geteilte Generatorlogik,
  nur variierende Koordinaten/Flags, kein eigener Codepfad je
  Kombination (Praezedenzfall LES-012). Details: TODO.md.

### LES-030 Futter-Sperrzone mit realem Beispiel verifiziert 2026-09-12

- Bisher war die Futter-Sperrzone (`chuck_no_go_x_min/x_max/z_limit`) nur
  in isolierten Unit-Tests geprueft, nicht in einem vollstaendigen
  Programm gegen einen echten Interpreter/Maschine.
- Neuer Verifikationsfall `chuck_nogo_case()` (basierend auf `Einstich.ngc`)
  setzt eine Sperrzone, deren X-Bereich den tatsaechlichen
  Rueckzugsdurchmesser bewusst einschliesst - sicher umgangen wird sie nur
  ueber die Z-Seite, nicht trivial durch einen ausserhalb liegenden X-Wert.
  Neuer Regressionstest bestaetigt sowohl den sicheren Fall (generiert
  fehlerfrei) als auch die Gegenprobe (engere Sperrgrenze blockiert korrekt).
- Real auf der SIM-Maschine gefahren (925s, fehlerfrei, korrekte
  Endposition, Backplot bestaetigt). 675 Stub-/44 Qt-Tests, zwoelf
  Referenzen und 43 Matrixfaelle unter rs274 bestanden.
- Bewusst NICHT geprueft: unterschiedliche physische Maschinenprofile
  (fehlen mangels realer Vergleichsdaten) - dafuer neue, separate
  Checkbox in TODO.md ergaenzt statt den Punkt stillschweigend
  mitzuschliessen. Details: TODO.md.

### LES-030 Teilabschluss: letzte zwei Referenzen (Abdrehen.ngc, Einstich.ngc) real bis M30 gefahren 2026-09-12

- Beide seit 2026-09-10 offen gebliebenen Referenzen mit grosszuegigem
  Zeitbudget real auf der SIM-Maschine zu Ende gefahren: `Abdrehen.ngc`
  (769s, materialintensivste Referenz mit vielen feinen Schrupppaessen) und
  `Einstich.ngc` (928s) - beide fehlerfrei, beide mit Endposition exakt am
  konfigurierten Werkzeugwechselpunkt.
- Damit haben jetzt alle zwoelf Referenzen einen dokumentierten nativen
  LinuxCNC-Trockenlauf bis M30 (mit einer bewussten Ausnahme: `CSS_Wechsel.ngc`
  selbst nutzt eine fuer eine reale Abnahme unpraktikabel feine 0.05mm-
  Zustellung - der zugrunde liegende Mechanismus ist stattdessen ueber
  LES-013s `css_switch_case()` verifiziert).
- Eigener Messfehler gefunden und korrigiert: ein Hilfsskript uebergab sein
  Zeitbudget-Argument nicht an die Laufzeitfunktion (fixer 180s-Default
  wurde stillschweigend verwendet) - dadurch wurde der erste `Abdrehen.ngc`-
  Lauf faelschlich als Timeout gemeldet, obwohl die Maschine nachweislich
  fehlerfrei weiterlief (Queue-Tiefe wuchs kontinuierlich). Keine
  Code-/Testaenderung in LatheEasyStep selbst noetig.
- Drei weitere Checkboxen per Dokumentation geschlossen (kein neuer Code,
  nur bereits vorhandene Belege zusammengefuehrt): Nichtnull-I-Boegen unter
  G7 in Schlichtweg UND G71-Subroutine sind bereits durch
  `Kontur_Radius_Fase.ngc` (Teil der zwoelf rs274-/SIM-Referenzen) und
  `tests/test_g71_arc_profile.py` abgedeckt; "Innen-G71" ist keine
  offene Testluecke, sondern eine per Design nie eintretende Situation
  (G71/G72 werden fuer Innenbearbeitung wegen eines bestaetigten
  Interpreter-Fehlers grundsaetzlich nie verwendet, der bewegungsbasierte
  Ersatzpfad deckt Z-Monotonie und Bohrung-als-Materialgrenze bereits ab).
  Details: TODO.md.

### LES-013 abgeschlossen: CSS/G96-Sicherheit fuer Zyklen und Groove-Makro analysiert und real verifiziert 2026-09-12

- Codeaudit fuer die drei verbleibenden Bewertungspunkte: `css_start_diameter`
  (`stock_x` bei ABSPANEN) wird NUR fuer die einmalige, begrenzte G97-Anfahr-/
  Freifahrtdrehzahl verwendet - jeder tatsaechliche Schnitt aktiviert vorher
  echtes G96, das LinuxCNC selbst live anhand der tatsaechlichen X-Position
  nachfuehrt. "stock_x ist nicht jeder einzelne Passdurchmesser" ist deshalb
  kein Bug.
- G71/G72/G76 und das Groove-Makro (`o220 call`) lassen G96 fuer ihre gesamte
  interne Bewegung aktiv, was sicher ist, weil die EINZIGE Stelle im
  gesamten Generator, die je "G96" ausgibt, IMMER ein D-Wort (harte
  Maximaldrehzahl) mitgibt (per Grep verifiziert) - eine interne
  Zyklusbewegung nahe X=0 kann die Drehzahl nie ueber das Limit treiben.
  Bereits automatisiert abgedeckt durch einen bestehenden Test fuer alle
  vier Schnittarten.
- Neuer Verifikationsfall (`verification_cases.css_switch_case()`, grobe
  1mm-Zustellung statt der 400-Pass-Produktionsreferenz) real auf der
  SIM-Maschine gefahren (53s, fehlerfrei): Live-Protokoll der Spindeldreh-
  zahl bestaetigt quantitativ, dass die Drehzahl waehrend des Zyklus korrekt
  bis exakt auf die D-Wort-Grenze steigt und nie darueber, und nach dem
  Zyklus korrekt auf die begrenzte Freifahrtdrehzahl zurueckfaellt (nicht
  auf dem CSS-Wert stehen bleibt). 674 Stub-/44 Qt-Tests, zwoelf Referenzen
  und 43 Matrixfaelle unter rs274 bestanden, keine Referenzaenderung.
  Details: TODO.md.

### LES-005 abgeschlossen: eigenstaendiger Innenfreistich (nicht THREAD-abgeleitet) mitten in Innenkontur verifiziert 2026-09-12

- Letzter offener Punkt von LES-005: der eigenstaendige `din_relief`-
  Kontur-Feature (nicht das automatisch aus einer THREAD-Operation
  abgeleitete, siehe LES-037) hatte fuer die Innenseite mitten in einer
  Bohrungskontur bisher keine Testabdeckung, nur die Aussenseite war
  automatisiert geprueft.
- Neuer Regressionstest bestaetigt: die Geometriefunktion war bereits
  generisch (`x_relief = x_anchor + 2*depth` fuer Innen statt `-2*depth`
  fuer Aussen), produziert fuer eine M12-Innenbohrung korrekt einen zu
  GROESSEREM X wachsenden Freistich (mehr Material aus der Bohrungswand
  entfernt) an der richtigen Position - kein Bug, reine fehlende
  Testabdeckung.
- Neuer Verifikationsfall (`verification_cases.internal_relief_case()`)
  real auf der SIM-Maschine gefahren: rs274 fehlerfrei, 412s AUTO-
  Trockenlauf ohne Eintrag im NML-Fehlerkanal, Endposition exakt am
  Werkzeugwechselpunkt. Die 0,25mm tiefe Freistichnut ist gegenueber dem
  4mm-Stufensprung im Backplot bei praktikablem Zoom nicht pixelgenau
  sichtbar (physikalische Eigenschaft eines flachen DIN-76-Innenfreistichs
  bei kleinem Gewindedurchmesser, bereits durch den Geometrietest
  algebraisch nachgewiesen). 674 Stub-/44 Qt-Tests, zwoelf Referenzen und
  43 Matrixfaelle unter rs274 bestanden, keine Referenzaenderung. Details:
  TODO.md.

### LES-037 abgeschlossen: reale Aussen-/Innengewinde-Freistichfaelle auf SIM-Maschine gefahren und Backplot geprueft 2026-09-12

- Letzter offener Punkt von LES-037 (reale Backplot-/Trockenlauf-Abnahme,
  nicht nur automatisierte rs274-Parserpruefung) auf der nativen SIM-Maschine
  `sim.qtdragon_lathe.basic_xz_lathe-1` nachgeholt: beide mit
  `lathe_easystep.verification_cases.thread_relief_case()` erzeugten Faelle
  (Aussen- und Innengewinde, je mit automatischem DIN-Freistich) headless
  ueber das `linuxcnc`-Python-Modul im echten AUTO-Modus gefahren.
- Aussengewinde 103s, Innengewinde 122s Laufzeit, beide mit leerem
  Fehlerkanal und Endposition exakt am konfigurierten Werkzeugwechselpunkt.
  Backplot per Screenshot visuell bestaetigt (inkl. sichtbarer
  Freistich-Absetzung).
- Eigener Messfehler im ersten Anlauf gefunden und behoben: die
  Ueberwachungslogik wertete beide Laeufe zunaechst faelschlich nach ~2s als
  "sauber abgeschlossen", weil die Statusabfrage begann, bevor die Bewegung
  ueberhaupt gestartet war. Durch staerkere Synchronisation
  (`wait_complete()` je Kommando, Bestaetigung von `queue>0`/
  `interp_state=READING` vor jeder "fertig"-Pruefung) korrigiert und beide
  Faelle danach mit nachweislich echter Bewegung neu gefahren.
- Keine Code-/Testaenderung in diesem Schritt (reine Maschinenabnahme). 673
  Stub-/44 Qt-Tests, zwoelf Referenzen und 43 Matrixfaelle unter rs274
  weiterhin unveraendert bestanden. Details: TODO.md.

### LES-028 G76-Parametervalidierung abgeschlossen: peak_offset konnte lautlos verschwinden 2026-09-12

- Ein explizit gesetzter, aber winziger `peak_offset` (z. B. 0.00001)
  verschwand lautlos im vierstellig gerundeten G76-`I`-Wort
  (`I-0.0000`/`I0.0000`) - weder der bestehende Fallback (nur fuer exakt
  `0.0`) noch eine "rundet auf Null"-Pruefung (wie bei Steigung/
  Gewindetiefe/Zustellwinkel bereits vorhanden) griff.
- Behoben konsistent mit dem bestehenden Verhalten: ein auf Null
  rundender Wert wird jetzt wie ein fehlender behandelt und durch den
  Standardwert ersetzt, statt eine neue, inkonsistente Fehlerablehnung
  nur fuer diesen einen Parameter einzufuehren. Neuer Regressionstest,
  gegen den alten Code verifiziert (reproduziert `I-0.0000` exakt). 673
  Stub-/44 Qt-Tests, zwoelf Referenzen und 43 Matrixfaelle unter rs274
  bestanden, keine Referenzaenderung. LES-028 ("G76-Parameter vollstaendig
  normalisieren") damit abgeschlossen; zwei bewusst offen gebliebene
  Punkte sind zu unpraezise spezifiziert fuer eine Entscheidung ohne
  Rueckfrage. Details: TODO.md.

### LES-010 abgeschlossen: komplette DIN-76-Tabelle verifiziert, ein Datenfehler und eine falsche Herleitung gefunden 2026-09-12

- Alle 19 Groessen in `DIN76_THREAD_DATA` (M2-M30) systematisch gegen die
  verifizierte DIN 76-1:2016-08-Tabelle geprueft (Steigung, dg, Radius,
  g2/short_g2 fuer alle vier Formen).
- **Datenfehler gefunden und behoben:** M12 Innengewinde `short_g2` (Form
  D Kurz) stand auf `6.4`, korrekt sind `6.1` (die drei anderen M12-Werte
  stimmten bereits exakt).
- **Eigene g1-Herleitungsformel als fuer die Innenseite falsch entlarvt:**
  `g1 = g2 - Tiefe*tan(60°)` trifft die Aussenseite bei allen 19 Groessen
  auf 0.01-0.1mm genau, weicht bei der Innenseite aber systematisch und
  mit der Groesse wachsend ab (M3: 0.44mm daneben, M30: 3.27mm daneben) -
  kein Rundungsfehler. Die damit berechneten Innen-g1-Werte fuer M2/M2.5/
  M3.5 (LES-019) wurden deshalb wieder entfernt statt eine falsche Zahl zu
  behalten.
- Nebenwirkung (bewusst akzeptiert): die automatische Innen-Freistich-
  Vorschlagsfunktion blockiert fuer M2/M2.5/M3.5 jetzt korrekt mit klarer
  Fehlermeldung statt stillschweigend falscher Geometrie (`short_g1` wird
  als `thread_overlap` streng auf `>0` geprueft). Aussengewinde dieser
  Groessen bleiben vollstaendig funktionsfaehig. Neuer Regressionstest (3
  parametrisierte Faelle) haelt das sichere Blockieren fest. 672 Stub-/44
  Qt-Tests, zwoelf Referenzen und 43 Matrixfaelle unter rs274 bestanden
  (keine Referenzaenderung). Details: TODO.md LES-010/LES-019.

### LES-012 abgeschlossen: Vorschau nutzt jetzt dieselbe Bogenzerlegung wie der Generator 2026-09-12

- `LathePreviewWidget._sample_arc()` hatte eine eigene, unabhaengige
  Bogenzerlegung (fest 48 Schritte, naive lineare Winkelinterpolation)
  statt der vom Generator bereits genutzten `contour_features._tessellate_arc()`
  (adaptiv, Sehnenabweichung <0.0005mm). Delegiert die eigentliche
  Zerlegung jetzt dorthin - Vorschau und erzeugter G-Code teilen sich
  damit dieselbe Primitive-Quelle statt zweier parallel gepflegter
  Implementierungen. Die Degenerations-/Plausibilitaetspruefung fuer
  inkonsistente Radien (kann waehrend der Live-Konturbearbeitung
  kurzzeitig auftreten) bleibt lokal in der Vorschau erhalten.
- Die beiden anderen verbliebenen LES-012-Punkte ("Linien/Boegen bis zur
  Ausgabe als Primitive fuehren", "Radien nicht in reine G1-Punktlisten
  umwandeln") wurden erneut geprueft und als fuer den bandbasierten
  Schrupp-Pfad (`rough_turn_parallel_x/z`) nicht sinnvoll umsetzbar
  eingeordnet: jeder Einzelschnitt ist durch die Band-Strategie selbst
  eine achsparallele Gerade, ein Bogen kann dort grundsaetzlich nicht als
  G2/G3-Bewegung auftreten. Die numerische Genauigkeit der Materialreich-
  weiten-Berechnung (wo ein Band beginnt/endet) ist bereits seit dem
  Sehnen-Fix vom 2026-09-10 sichergestellt.
- Bestehende Tests (`tests/test_preview_arcs.py`) pruefen weiterhin
  dieselben geometrischen Eigenschaften; eine auf die alte feste
  Schrittzahl hartkodierte Assertion wurde auf eine Mindestanzahl
  umgestellt (adaptive Zerlegung liefert fuer die Testgeometrie 80 statt
  49 Punkte). 669 Stub-/44 Qt-Tests bestanden; reine Vorschau-Aenderung
  ohne Einfluss auf die G-Code-Generierung. LES-012 damit vollstaendig
  abgeschlossen. Details: TODO.md.

### LES-019 M3.5 DIN-76-Freistichpreset ergaenzt, Luecke vollstaendig geschlossen 2026-09-12

- Zwei vom Nutzer gefundene, per KI-Suchtool erzeugte Tabellen fuer M3.5
  beim Gegenpruefen als unzuverlaessig verworfen (eine kehrte das bei allen
  anderen Groessen geltende Muster "Innenmass > Aussenmass" um; die andere
  behauptete fuer das bereits zweifach verifizierte M3 beim Innengewinde
  Werte, die um mehr als das Doppelte von den echten abweichen).
- Stattdessen die P=0.6-Zeile (zwischen M3 und M4) aus derselben, fuer
  M2/M2.5 bereits genutzten 1983er-Tabelle (DIN 76 T1 12.83) verwendet -
  per Tabellen-Fussnote fuer jedes Gewinde dieser Steigung gueltig, und
  M3.5 hat genau P=0.6. g1/short_g1 wieder geometrisch hergeleitet.
  Dokumentierter Vorbehalt: die Aussenwerte dieser 1983er-Ausgabe lagen bei
  M3 ca. 0.05mm ueber der 2016er-Ausgabe - fuer eine Freistichnut ohne
  Passmass-Funktion praktisch bedeutungslos.
- Die urspruengliche Luecke (M2, M2.5, M3.5 ohne DIN-76-Freistichdaten)
  ist damit vollstaendig geschlossen. Neuer Regressionstest, End-to-End
  verifiziert. 669 Stub-/44 Qt-Tests, zwoelf Referenzen und 43 Matrixfaelle
  unter rs274 bestanden (keine Referenzaenderung). Details: TODO.md
  LES-019.

### LES-019 M2/M2.5 DIN-76-Freistichpresets ergaenzt 2026-09-11

- Nutzer stellte zwei unabhaengige, sich exakt deckende Quellenfotos bereit
  (DIN 76 T1 12.83, "Tabellenbuch Metall" Europa-Lehrmittel, sowie DIN
  76-1:2016-08, "Technische Kommunikation" K54 handwerk-technik.de). M2 und
  M2.5 in `DIN76_THREAD_DATA`/`DIN_RELIEF_TABLE` ergaenzt (Steigung,
  Freistichdurchmesser-Differenz, Breite g2 Form A/B/C/D, Radius - alles
  direkt aus den Quellen).
- Keine der beiden Quellen weist einen separaten `g1`-Wert aus (nur `g2`) -
  `g1`/`short_g1` daher geometrisch hergeleitet (`g1 = g2 - Tiefe *
  tan(60°)`, aus dem 30°-Mindestflankenwinkel der Norm), gegen alle
  vorhandenen M3-M30-Eintraege verifiziert (trifft durchgehend auf
  0.01-0.1mm genau).
- M3.5 bleibt offen - fehlt in beiden Quellen (kein eigener
  Tabelleneintrag), explizit dokumentiert statt geschaetzt.
- Neuer Regressionstest (4 parametrisierte Faelle), End-to-End ueber
  `thread_relief_spec()` verifiziert. 667 Stub-/44 Qt-Tests, zwoelf
  Referenzen und 43 Matrixfaelle unter rs274 bestanden (keine
  Referenzaenderung). Details: TODO.md LES-019.

### LES-027 Fix: tatsaechliche Ursache der restlichen 6.7s gefunden 2026-09-10

- Diagnose-Log zeigte 168/168 aufgeloeste Eintraege gleichmaessig > 20ms
  (~45-88ms, auch bei trivialen Buttons) - kein Ausreisser, sondern
  konstanter Zusatzaufwand pro Widget. `set_tooltip_deep()` loeste fuer
  JEDES Zielwidget zusaetzlich dessen `label_<name>`-Gegenstueck ueber den
  ungecachten `_get_widget_by_name()` auf - denselben teuren Pfad, den die
  vorige Runde in `apply_registered_tooltips()` bereits ersetzt hatte,
  hier aber uebersehen. Die meisten Widgets haben gar kein Label-Widget -
  der teuerste Fall fuer den ungecachten Lookup (kompletter Baum-/
  Panel-Scope-Walk, findet trotzdem nichts). 168 x ~45ms ≈ 7.5s - passt
  exakt zur gemessenen Restlaufzeit.
- Behoben: nutzt jetzt `_widgets_by_name()` (Cache mit automatischem
  Fallback). Neuer Regressionstest, gegen den alten Code verifiziert
  (`git stash`). 663 Stub-/44 Qt-Tests bestanden.
- **Nutzerentscheidung:** LES-027 damit vorerst zurueckgestellt. Die
  eigentliche Krankheit ist die such-basierte Widget-Aufloesung selbst,
  nicht nur diese zwei Fundstellen - die echte Loesung ist LES-044
  (modulare Panel-Architektur mit festen IDs statt Laufzeitsuche). Die
  beiden bereits gemachten Fixes bleiben bestehen (real 59% schneller,
  28.4s -> 11.7s), weitere Performance-Jagd in der aktuellen Architektur
  wird bewusst nicht fortgesetzt. Details: TODO.md
  LES-027.

### LES-027 Bestaetigt: -59% Startzeit, Restbefund bei apply_registered_tooltips 2026-09-10

- Realer Testlauf bestaetigt den vorherigen Fix: Gesamtstartzeit sank von
  28.4s auf **11.7s (-59%)**. `_apply_widget_property_translations` fiel
  wie erwartet auf 17ms. `apply_registered_tooltips` sank von 16.63s auf
  6.70s fuer dieselben 169 Eintraege - besser, aber immer noch deutlich
  ueber den aus `_apply_combo_translations` erwarteten <0.5s.
- Naheliegende Hypothese: die intrinsischen Kosten von `_set_tooltip_deep()`
  selbst (eigener `findChildren()`-Aufruf PRO Zielwidget, bis zu sechs
  Qt-Property-Aufrufe und ein neu erzeugter/installierter
  `_TooltipRelay`-Eventfilter), nicht mehr der Widget-Lookup. Zaehler und
  ein sortiertes "> 20ms"-Log der zehn langsamsten Eintraege ergaenzt, um
  das beim naechsten Testlauf zu bestaetigen. 662 Stub-/44 Qt-Tests
  weiterhin bestanden. Details: TODO.md LES-027.

### LES-027 Fix: Startzeit-Root-Cause gefunden - doppelte Tooltip-Anwendung ueber 169 Widgets 2026-09-10

- **Root Cause gefunden** (dritter Testlauf mit dem erweiterten Logging):
  `apply_registered_tooltips()` und `_apply_widget_property_translations()`
  zusammen 21.7s von 28.4s Gesamtstartzeit.
- `apply_registered_tooltips()` (`ui_tooltips.py`) nutzte fuer alle 169
  Eintraege in `UI_TOOLTIP_KEYS` den ungecachten `_get_widget_by_name()`
  statt des Caches (`_widgets_by_name()`), den `_apply_combo_translations()`
  fuer denselben Zweck bereits nutzt (39 Eintraege dort: ~0.1s). Behoben -
  behandelt dabei jetzt zusaetzlich korrekt ALLE Treffer eines Namens statt
  nur einen (echte Korrektur bei mehrfach vorkommenden Feldnamen in
  eingebetteten Teil-UIs, nicht nur schneller).
- `_apply_widget_property_translations()` durchlief danach nochmal den
  GESAMTEN Widget-Baum und wandte fuer jedes Widget mit `tooltip_key`
  erneut `_set_tooltip_deep()` an - dieselben bis zu 169 Widgets, die
  `apply_registered_tooltips()` (immer direkt davor aufgerufen) bereits
  behandelt hatte. Behoben: ueberspringt jetzt bereits registrierte
  Widgets (`tooltip_fallback_auto=False`-Marker).
- Zwei neue Regressionstests, gegen den alten Code verifiziert (`git
  stash`). 662 Stub-/44 Qt-Tests bestanden. Reine UI-Performance-Aenderung
  ohne Einfluss auf die G-Code-Generierung. Hypothese (noch nicht durch
  einen realen Testlauf bestaetigt): Startzeit sinkt von ~28s auf ~7s.
  Details: TODO.md LES-027.

### LES-027 Startzeit erstmals reproduziert, feingranulare Messung ergaenzt 2026-09-10

- Ein realer `LATHEEASYSTEP_DEBUG=1 qtvcp`-Lauf (Standalone, native
  Maschine) zeigte `_finalize_ui_ready` von +0.240s bis +25.166s - die
  erste echte Reproduktion der seit Tagen gemeldeten, zuvor unter Windows/
  WSL nicht nachvollziehbaren >20s-Startzeit.
- `ui_lifecycle.py` (`finalize_ui_ready()`) protokolliert jetzt vor/nach
  jedem groesseren Teilschritt einen `_startup_mark()` (Split-UI-Laden,
  Widget-Registrierung, Core-/Advanced-/Contour-/Preview-Widgets,
  Signalverbindungen, Sprach-/Tab-Titel-Praesentation), statt nur am
  Anfang und Ende der gesamten Funktion zu messen. Reine
  Logging-Ergaenzung ohne Verhaltensaenderung.
- Wiederholter Testlauf mit dem erweiterten Logging grenzt den
  Hauptverursacher ein: **18.26s (84% der 21.856s Gesamtzeit) entfallen
  auf den "presentation"-Block** (`_apply_tab_titles`/
  `_handle_global_change`/`_apply_language_texts`); die uebrigen
  Signalverbindungen (`connect_remaining_signals`) trugen 1.84s bei.
  `_apply_language_texts()` selbst buendelt ~10 weitere Teilschritte
  (u. a. `_apply_combo_translations`, das ueber alle 39 Eintraege von
  `COMBO_ITEM_REGISTRY` iteriert) - jetzt ebenfalls mit `_startup_mark()`
  instrumentiert, um den tatsaechlichen Ort beim naechsten Testlauf zu
  bestaetigen. Details: TODO.md LES-027.

### LES-040 fachliche Wertebereiche an Generatorgrenzen geschlossen 2026-09-10

- GROOVE lehnt negative Breiten, Tiefen, Zustellungen, Ueberdeckung,
  Rueckzug, Vorschuebe, Aufmass und Spanbruchamplitude ab, statt sie ueber
  `abs()` unbemerkt in andere Eingaben umzudeuten.
- ABSPANEN lehnt negative Schlichtaufmasse und Spanbruchdistanzen ab. FACE,
  ABSPANEN sowie die erreichbaren Legacy-Pfade TURN/BORE verhindern Werte,
  die bei der G-Code-Formatierung auf `0.000` gerundet wuerden; THREAD prueft
  Steigung und Gewindetiefe entsprechend mit vier Nachkommastellen.
- Direkte GROOVE-/ABSPANEN-/TURN-/BORE-Aufrufe validieren Parameter und Pfade
  nun ebenfalls auf Endlichkeit. 21 neue beziehungsweise angepasste
  Regressionen; 660 Stub-/44 Real-Qt-Tests, zwoelf Referenzen und 43
  Matrixprogramme unter nativem `rs274` bestanden.

### LES-039 erster Werkzeugwechsel mit LinuxCNC-Laufzeitpruefung 2026-09-10

- Der Bedienablauf ist verbindlich festgelegt: Nach Antasten oder Rohteilwechsel
  wird vor Programmstart manuell frei vom Werkstueck gefahren. Der Generator
  leitet aus der unbekannten Startposition keinen vermeintlich sicheren
  Rueckzugsweg mehr ab.
- Das erste Programmwerkzeug wird zur Laufzeit mit LinuxCNCs
  `#<_current_tool>` verglichen. Nur bei Abweichung faehrt das Programm zum
  definierten XT/ZT-Wechselpunkt und fuehrt `T.. M6` aus. Ein bereits korrekt
  eingelegtes Werkzeug verursacht keinen unnoetigen ersten Wechsel.
- Der Bewegungszustand bleibt nach dem Laufzeitzweig bewusst unbekannt, damit
  die erste Operation ihre sichere Anfahrt unabhaengig vom ausgefuehrten Zweig
  vollstaendig ausgibt. Folgewechsel und Programmendposition bleiben wie bisher
  deterministisch geplant.
- Verifiziert mit 639 Stub-/44 Real-Qt-Tests, statischer Pruefung aller zwoelf
  Referenzen sowie nativem `rs274` fuer alle zwoelf Referenzen und 43
  Matrixprogramme. In der QtDragon-SIM wurde der Abweichungszweig real im
  AUTO-Modus ausgefuehrt: Start mit T0, Fahrt zum Wechselpunkt, `T01 M6`,
  anschliessend meldete LinuxCNC T1; der weitere lange Planen-Testlauf wurde
  nach dem fuer LES-039 relevanten Startabschnitt kontrolliert abgebrochen.

### LES-022 dritte Etappe: Positions-Tracking in allen sechs Operations-Generatoren 2026-09-10

- Jede Operation mit deterministisch bekannter Endposition aktualisiert
  jetzt den gemeinsamen Bewegungszustand (`_motion_state`), statt ihn
  stillschweigend veraltet stehen zu lassen: `gcode_drill.py` (G81-Familie
  endet immer auf `(x_start, safe_z)`), `gcode_thread.py` (G76 endet immer
  auf `(approach_x, end_z)`), `gcode_face.py` und `gcode_roughing.py`
  (G70 endet immer exakt am letzten Punkt der referenzierten Kontur -
  alle vier per `rs274`-Trace empirisch verifiziert). `gcode_keyway.py`
  bricht immer ab, keine Bewegung.
- **Echter, zuvor unbemerkter Bug gefunden:** `gcode_thread.py`
  aktualisierte den Bewegungszustand nach G76 bisher ueberhaupt nicht - er
  blieb faelschlich auf der Anfahrposition VOR dem Gewindeschneiden stehen
  (Z blieb insbesondere auf `start_z` statt dem real erreichten `end_z` -
  bei einem 20mm-Gewinde ein Versatz von 20mm). Ein direkt folgender
  Schritt haette einen tatsaechlich noetigen Rueckzug potenziell
  faelschlich als bereits erledigt ansehen koennen. Neuer Regressionstest,
  gegen den alten Code verifiziert (`git stash`).
- Zwei Faelle bleiben bewusst auf `clear()` (Endposition unbekannt) statt
  eines geratenen Werts: der `o220`-Nutzyklus in `gcode_groove.py`
  (Breitenachsen-Endposition haengt datenabhaengig von Werkzeugbreite/
  Nutbreite/Ueberdeckung ab - Nachrechnen in Python wuerde die
  Makro-Zustelllogik duplizieren) und die eigentlichen Schrupp-Baender in
  `gcode_roughing.py` (`rough_turn_parallel_x/z` - reine Effizienzfrage,
  keine Sicherheitsluecke, da die bestehende `clear()`-Invalidierung
  bereits sicher ist). Details: TODO.md LES-022.
- 639 Stub-/44 Qt-Tests, zwoelf Referenzen und 43 Matrixfaelle unter rs274
  bestanden; keine Ausgabeaenderung ausser den bereits bekannten Diffs von
  heute (keine der zwoelf Referenzen hat einen Schritt direkt nach einem
  Gewinde-Step, daher wird der Thread-Bugfix dort nicht sichtbar).

### LES-045 Ergaenzung: G71/G72-Ruecklaufabstand (R) bewusst gesetzt 2026-09-10

- Per `rs274`-Trace verifiziert: `R` ist wie `D`/`I` ein reiner, nicht
  konvertierter Radius-/Z-Abstand (`R5.0` erzeugte einen exakt diagonalen
  5mm-Ruecklauf in X und Z zwischen den Schruppgaengen). Bisher war `R`
  nie gesetzt (Interpreter-Default 0.5mm) - nicht sicherheitskritisch
  falsch, aber unbewusst knapp. Jetzt `R{LEADOUT_LENGTH_DEFAULT}` (2.0mm)
  in beiden G71/G72-Zeilen ergaenzt, passend zur bereits etablierten
  Freifahrtlaenge des bewegungsbasierten Pfads. `Kontur_Radius_Fase.ngc`
  neu erzeugt (`R2.000` ergaenzt). 638 Stub-/44 Qt-Tests, zwoelf
  Referenzen und 43 Matrixfaelle unter rs274 bestanden. Details: TODO.md
  LES-045.

### LES-045 Fix: G71/G72 sendeten Zustelltiefe und Aufmass an vertauschte Parameter 2026-09-10

- **Sicherheitsrelevanter Fix, real gegen den LinuxCNC-Interpreter
  verifiziert:** der G7x-Dreh-Zyklus (`gcode_roughing.py`) sendete bisher
  nur `D{depth_per_pass}` - kein `I`. Laut Interpreter-Quelltext
  (`interp_g7x.cc`) ist `D` aber das AUFMASS ("final distance to
  profile", radial) und `I` die ZUSTELLTIEFE ("increment of cutting",
  radial, Default 1.0mm). Folge: die konfigurierte Zustelltiefe wurde bei
  Zyklus-Ausgabe komplett ignoriert (immer 1.0mm Default, empirisch per
  `rs274`-Trace bestaetigt: `depth_per_pass=1.0` und `=0.3` erzeugten
  identische Schnittfolgen), und das konfigurierte Schlichtaufmass kam nie
  an - stattdessen wirkte `depth_per_pass` zufaellig als Aufmass
  (`Kontur_Radius_Fase.ngc` liess trotz konfiguriertem Aufmass 0 bisher
  0.75mm Radius unbeabsichtigtes Restmaterial stehen).
- **Fix:** `I{depth_per_pass/2}` ergaenzt, `D{finish_allow_x/2}` statt
  `D{depth_per_pass}` (beide UI-Werte sind Durchmesserwerte, der Zyklus
  rechnet radial). Der bisherige `stock_x_adj`-Hack im G72-Zweig (Versuch,
  Aufmass ueber eine verkleinerte Startgrenze nachzubilden) entfernt.
  `U`/`W` (getrennter X/Z-Versatz) sind vom installierten Interpreter-Build
  nicht nutzbar ("Bad character 'u' used") - deshalb erzwingt
  `finish_allow_z > finish_allow_x` jetzt den bewegungsbasierten Pfad
  (nur EIN Aufmass ueber `D` darstellbar). Vorbild fuer den korrekten
  Parameter-Einsatz war der bereits laenger richtige Facing-Zyklus-Pfad
  (`gcode_face.py`).
- D/I-Semantik empirisch per `rs274`-Trace an gerader Zylinderwand UND an
  einer Bogenkontur bestaetigt (Restaufmass ueberall >= Konfiguration).
  `Kontur_Radius_Fase.ngc` (einzige Referenz mit echtem Dreh-G71) neu
  erzeugt; elf weitere Referenzen unveraendert. 638 Stub-/44 Qt-Tests,
  zwoelf Referenzen und 43 Matrixfaelle unter rs274 bestanden. Details:
  TODO.md LES-045.

### LES-003 Test: Innenbearbeitung mit Spanbruch an der Bogenkontur abgesichert 2026-09-10

- **Nutzerauftrag:** Roheitentest muss alle drei praxisrelevanten Faelle
  an derselben Bogenkontur abdecken - Zyklus (erledigt), expliziter
  ("ISO") Code, und explizit MIT aktiver Vorschub-Unterbrechung
  (Spanbruch). Der dritte Fall fehlte bisher fuer Innenbearbeitung, wo
  die urspruengliche Sehne-statt-Bogen-Regression gefunden wurde und wo
  ausschliesslich der explizite Pfad existiert (G71/G72 fuer
  Innenkonturen in dieser LinuxCNC-Version generell nicht nutzbar,
  LES-003-Hauptbefund). Neuer Test
  `test_internal_rough_passes_never_undercut_allowance_through_arc_with_chip_breaking`
  (`tests/test_internal_profile_matrix.py`): `Innen_Radius.ngc`-Bogenkontur
  mit `pause_enabled=True`, prueft jeden Schrupp-Punkt (aus `G1`- und aus
  `o<step_line_pause> call [...]`-Zeilen) gegen die wahre Fertigkontur.
  Gegen den alten Sehnen-Code verifiziert (`git stash`): schlaegt real mit
  einer Aufmass-Verletzung fehl (0.04mm statt 0.2mm Restaufmass bei
  X12.0 Z-15.8). 637 Stub-/44 Qt-Tests, elf Referenzen und 43
  Matrixfaelle unter rs274 bestanden, keine Referenzaenderung. Details:
  TODO.md LES-003.

### LES-003 Fix: Zyklus-vs-explizit-Paritaet, zwei Bugs im Aussen-Schrupp-Pfad 2026-09-10

- **Nutzerfrage:** liefert eine Kontur mit G71/G72-Zyklus dasselbe
  Ergebnis wie mit explizit erzeugtem ("ISO") G-Code? Neue
  `tests/test_cycle_vs_explicit_parity.py` prueft genau das fuer eine
  Aussenkontur mit Bogen, einmal per `prefer_cycle`, einmal per
  `prefer_explicit`, gegen die wahre (nicht linearisierte) Fertigkontur.
  Zwei echte Bugs im bewegungsbasierten Aussen-Schrupp-Pfad gefunden:
  1. **Schlichtaufmass-Asymmetrie** (`gcode_roughing.py`): der
     Aufmass-Versatz wurde nur fuer Innenbearbeitung angewendet -
     Aussenkonturen im expliziten Pfad schrubbten bis zur Fertigkontur
     OHNE jedes Aufmass, sobald der explizite statt der Zyklus-Pfad
     genutzt wurde. Behoben: Versatz jetzt fuer beide Seiten mit
     passendem Vorzeichen.
  2. **Spanbruch ignoriert bei zyklustauglicher Kontur** (`gcode_roughing.py`
     `can_use_cycles`): das selbst gebaute Vorschub-Unterbrechungsfeature
     (`pause_enabled`/`pause_distance`, Ersatz fuer einen LinuxCNC
     unbekannten Siemens-Zyklus, nutzerbestaetigt real haeufig verwendet)
     wurde stillschweigend uebergangen, wenn die Kontur sonst
     zyklustauglich war - G71/G72 kann diese Unterbrechung grundsaetzlich
     nicht ausfuehren. Behoben: aktiver Spanbruch erzwingt jetzt immer
     den expliziten Pfad.
- Beide Fixes gegen den alten Code verifiziert (`git stash`, 3 der 5
  neuen Tests schlagen vorher mit spezifischen Aufmass-Verletzungen fehl).
  636 Stub-/44 Qt-Tests, elf Referenzen und 43 Matrixfaelle unter rs274
  bestanden; nur `Innen_Radius.ngc` aendert sich (bereits dokumentierter
  Sehnen-Fix), keine neue Referenzaenderung durch diese beiden Fixes.
  Details: TODO.md LES-003.

### LES-005 abgeschlossen: Innen_Konus.ngc als zwoelfte Referenz 2026-09-10

- `Innen_Konus.ngc` war bisher nur ein Profil-Fall in der generischen
  Testmatrix, keine eingecheckte Referenz. Neu in `examples.py` ergaenzt
  (Kegelkontur, sonst identischer Aufbau wie `Innen_Stufe.ngc`) und als
  zwoelfte Referenz regeneriert - besteht statische Pruefung und `rs274`.
  In der SIM (Zoom-Testvariante) bis `M30` gefahren, Backplot zeigt die
  Kegelform klar erkennbar. Damit haben jetzt alle drei LES-005-
  Innenkonturformen (Stufe, Konus, Radius) automatisierte Regressionen
  UND einen dokumentierten nativen LinuxCNC-Nachweis. 631 Stub-/44
  Qt-Tests bestanden. Details: `doc/NATIVE_VERIFICATION_2026-09-09.md`.

### LES-040 Fix: Aussen-Rueckzugsebene konnte im Rohteil liegen 2026-09-10

- **Sicherheitsrelevanter Fix, Nutzerentscheidung:** "Ausser bei
  Innenbearbeitung kann die Rueckzugsebene niemals im Rohteil sein."
  Neue Funktion `validate_external_retract_clearance()` (`gcode_safety.py`)
  prueft die aufgeloeste AUSSEN-Rueckzugsebene (XRA/ZRA) einmalig ganz am
  Anfang der Programmerzeugung gegen die Rohteil-Huellkurve (X- und
  Z-Bereich gleichzeitig) und blockiert die Ausgabe, wenn sie tatsaechlich
  innerhalb liegt. Innenbearbeitung (XRI/ZRI) ist bewusst unberuehrt - dort
  ist "innerhalb der Huellkurve" der Normalfall (eigene Pruefung von
  heute frueh, `validate_internal_material_clearance()`).
- Bewusst NICHT geloest: die generelle sichere Achsreihenfolge/
  -sequenzierung einzelner Bewegungen (separat verfolgt unter LES-001/
  LES-039) - diese Pruefung sichert nur die konfigurierte Rueckzugsebene
  selbst ab, nicht jede Einzelbewegung dorthin.
- Drei neue Tests (Unit- und zwei Integrationstests), gegen den alten
  Code verifiziert. 630 Stub-/44 Qt-Tests, 88 statische Checks, elf
  Referenzen und 43 Matrixfaelle unter rs274 bestanden; keine Referenz
  geaendert. Details: TODO.md LES-040.

### LES-040 Fix: Abspanen akzeptierte Vorschub 0 oder negativ 2026-09-10

- **Fix:** `REQUIRED_KEYS[OpType.ABSPANEN]` fehlte `"feed"` - anders als
  bei FACE/DRILL wurde der Vorschub fuer Abspanen (die mit Abstand
  meistgenutzte Operation) nie auf Positivitaet geprueft. `feed=0` erzeugte
  `G1 ... F0.000`, `feed=-0.15` sogar `G1 ... F-0.150`. Behoben durch
  Ergaenzen von `"feed"` in der Liste; dieselbe zentrale Pruefung greift
  automatisch. Neuer Regressionstest, gegen den alten Code verifiziert.
  627 Stub-/44 Qt-Tests bestanden, keine Referenz geaendert.
- **Noch offen, bewusst nicht ad hoc gefixt:** `zra`/`zri` (globale
  Z-Rueckzugsebenen) werden nirgends auf einen plausiblen Wertebereich
  geprueft - eine Ebene innerhalb der Rohteil-Huellkurve erzeugt nur eine
  informative Kommentarzeile, keinen Fehler. Braucht eine fachliche
  Entscheidung vor einer Aenderung. Details: TODO.md LES-040.

### LES-003 abgeschlossen: Backplot-Nachweis fuer Innen_Stufe.ngc 2026-09-10

- Letzter offener LES-003-Punkt nachgeholt: lesbarer SIM-Backplot-
  Screenshot fuer `Innen_Stufe.ngc` (Parser/`rs274` und echter
  AUTO-Trockenlauf bis `M30` waren bereits vorher erbracht). Stufenkontur
  im Backplot klar erkennbar, leerer NML-Fehlerkanal. LES-003 damit
  vollstaendig abgehakt. Details: `doc/NATIVE_VERIFICATION_2026-09-09.md`.

### LES-003 Aussen-Richtungsmatrix ergaenzt, zwei Checkboxen nachtraeglich bestaetigt 2026-09-10

- Audit ergab: "XRI nur als Einfahr-/Rueckzugsebene" und "monoton
  steigende/fallende Z-Konturen" waren inhaltlich bereits durch
  bestehende Tests erledigt (24 Kombinationen fuer Innenbearbeitung), nur
  nicht abgehakt.
- Fuer Aussenbearbeitung fehlte die analoge Richtungs-/Modus-Matrix (nutzt
  einen grundsaetzlich anderen Ausgabepfad: G71/G72-Zyklus statt der
  bewegungsbasierten Innen-Ersatzloesung) - neu ergaenzt in
  `tests/test_external_profile_matrix.py` (18 Kombinationen, prueft dass
  kein Schnitt die XA-Rohteilgrenze ueberschreitet). Reiner Testzuwachs,
  keine Referenz geaendert. 625 Stub-/44 Qt-Tests bestanden.

### LES-005 "zuerst auf nachweislich freien Innendurchmesser fahren" 2026-09-10

- **Sicherheitsrelevanter Fix:** Die axiale Eilgangebene (`XRI`) bei
  Innenbearbeitung wurde bisher nie gegen bekanntes, bereits offenes
  Material geprueft - ein zu gross gewaehltes XRI (groesser als eine
  vorangehende Bohrung oder das im Programmkopf gesetzte XI) haette den
  Eilgang durch stehengebliebenes Vollmaterial fahren lassen koennen.
- Neue Pruefung `validate_internal_material_clearance()`
  (`gcode_utils.py`): blockiert die Ausgabe, sobald XRI nachweislich groesser
  ist als das per Programmkopf-`XI` (deckt die gesamte Werkstuecklaenge ab)
  oder per vorangehender Bohren-Operation (Durchmesser UND Tiefe, neu in
  `gcode_program.py` mitverfolgt) bekannte offene Material. Fehlen beide
  Angaben, bleibt die Pruefung bewusst stumm - dafuer existiert weiterhin
  die separate Reihenfolge-Warnung in `checks.py::validate_program_setup`.
- Neue Testdatei `tests/test_internal_material_clearance.py` (11 Faelle).
  Zwei bestehende Testfixtures mit unplausiblen XRI/XI- bzw.
  XRI/Bohrdurchmesser-Kombinationen korrigiert. 607 Stub-/44 Qt-Tests, 88
  statische Checks, elf Referenzen und 43 Matrixfaelle unter rs274
  bestanden; keine Referenz geaendert (alle bestehenden Kombinationen
  waren bereits konsistent). Details: TODO.md LES-005.

### LES-043 Gegenspindel-Checkbox vorerst deaktiviert 2026-09-10

- **Sicherheitsrelevanter Befund (Nutzerverdacht bestaetigt):** Die
  Checkbox "Gegenspindel vorhanden" und das Feld "max. Drehzahl S3" wurden
  nirgends im Generator ausgewertet - kein Operationstyp fuer
  Werkstueckuebergabe/Spindelsynchronisation existiert, die S3-Grenze
  wurde nie geprueft, nicht einmal als Kommentar ausgegeben. Eine
  irrefuehrende Bedienoberflaeche: Setzen der Checkbox konnte Unterstuetzung
  suggerieren, die es nicht gibt.
- Checkbox und S3-Feld bleiben sichtbar (Transparenz fuer bestehende
  gespeicherte Programme), sind aber jetzt gesperrt (`setEnabled(False)`)
  mit erklaerendem Tooltip, bis eine echte Umsetzung existiert. Kein
  Generatorverhalten geaendert. Details: TODO.md LES-043.

### Fix: Innen-Schruppen schnitt an Rundungen ins Fertigteil 2026-09-10

- **Sicherheitsrelevanter Fix:** Beim Betrachten der SIM-Backplot-
  Screenshots fiel auf, dass Schrupp-Paesse an der kleinen R1-Rundung
  zwischen Bohrung und Schulter (`Innen_Radius.ngc`) ins Fertigteil
  schnitten - bis zu 0.43mm Durchmesser-Uebermass bei 0.2mm
  konfiguriertem Schlichtaufmass. Ursache: `primitive_to_points()`
  reduzierte Bogen-Primitive fuer die Schrupp-Materialreichweiten-
  Berechnung (`intersect_segment_with_x_band`) auf ihre Sehne statt den
  wahren Kreis abzutasten; bei kleinen Radien baucht die echte Kontur
  gegenueber der Sehne nach innen aus, wodurch die Schrupp-Zustellung zu
  tief fuhr.
- Behoben: `primitive_to_points()` tastet Bogen-Primitive jetzt entlang
  des wahren Kreises ab (adaptive Segmentzahl, Sehnenabweichung
  <0.0005mm) - betrifft nur die interne Materialreichweiten-Berechnung,
  die FERTIGKONTUR-Ausgabe (G2/G3) war bereits vorher korrekt und bleibt
  unveraendert.
- Neuer Regressionstest
  `test_internal_rough_passes_never_undercut_allowance_through_arc`
  (`tests/test_internal_profile_matrix.py`) - reproduziert nachweislich
  den alten Fehler ohne den Fix und prueft dauerhaft, dass kein
  Schrupp-Schnitt entlang eines Bogens das Aufmass unterschreitet.
  Einzige geaenderte Referenz: `Innen_Radius.ngc` (vier Zeilen, Pass 4-7
  jetzt flacher/sicherer). 596 Stub-/44 Qt-Tests, 88 statische Checks,
  elf Referenzen und 43 Matrixfaelle unter rs274 bestanden.

### SIM: 9/11 Referenzen abgeschlossen, lesbarer Backplot-Screenshot 2026-09-10

- Mit mehr Zeitbudget (400s) liefen vier weitere Referenzen fehlerfrei
  durch: `Innen_Radius.ngc`, `Innen_Stufe.ngc`, `Planen.ngc`,
  `Planen_Radius.ngc`. Damit 9 von 11 Referenzen in dieser Sitzung
  automatisiert bis `M30` verifiziert.
- `Abdrehen.ngc` gezielt mit Live-Tracking geprueft: kein Haenger,
  sondern kontinuierlich viele feine Schrupppaesse - schlicht das
  materialintensivste Referenzbeispiel, braucht mehr Zeitbudget als
  bisher getestet.
- Zoom-Testvariante (naher Werkzeugwechselpunkt) fuer `Innen_Radius.ngc`
  liefert jetzt einen klar lesbaren Backplot-Screenshot: Schrupppaesse
  und Schlichtkontur sauber getrennt erkennbar, inkl. der axialen
  Einfahrt vor dem radialen Zustellen. Damit ist der zuvor offene Punkt
  "gezoomter, lesbarer Backplot" erledigt. Details:
  `doc/NATIVE_VERIFICATION_2026-09-09.md`.

### SIM: alle elf Referenzen automatisiert durchlaufen lassen 2026-09-09

- `MAX_ACCELERATION` in `lathe.ini` (SIM, ausserhalb dieses Projekts) von
  20.0 auf 2000.0 mm/s^2 erhoeht - reine Tuning-Massnahme fuer schnellere
  Trockenlaeufe ohne reale Maschinenentsprechung, kommentiert und
  reversibel. Vorschub-Override half kaum (dominiert von
  Beschleunigungsrampen vieler kurzer Paesse, nicht Reisegeschwindigkeit).
- Sechs von elf Referenzen liefen automatisiert (inkl. automatischem
  Werkzeugwechsel-Loopback, ohne manuellen Klick) fehlerfrei bis `M30`
  durch (1-100s). Die restlichen fuenf liefen nachweislich weiter (Position/
  Drehzahl aendern sich kontinuierlich), ueberschritten aber das
  150s-Testzeitbudget dieser Sitzung - kein Generatorbefund.
- Nebenbefund: mehrfache harte Prozess-Neustarts hinterliessen ein
  verwaistes NML-Shared-Memory-Segment (`ipcs -m`, Key `0x64`), das
  `linuxcnc.error_channel()` brechen liess (`Error buffer invalid`);
  behoben mit `ipcrm -M 0x64` nach vollstaendigem Prozessstop. Details:
  `doc/NATIVE_VERIFICATION_2026-09-09.md`.

### SIM: doppelte Werkzeugwechsel-Komponente behoben, Zoom-Tipp bestaetigt 2026-09-09

- `basic_sim.tcl` lud zusaetzlich zu QtDragons eigenem Werkzeugwechsel-
  Dialog noch `hal_manualtoolchange` mit (Startlog: "Detected
  hal_manualtoolchange component already loaded"). Fix: `[HAL] HALFILE`
  in `lathe.ini` um die dafuer vorgesehene Option
  `-no_use_hal_manualtoolchange` ergaenzt - kein zweites, ungemapptes
  Werkzeugwechsel-Fenster mehr.
- Nutzertipp bestaetigt: Mit einem testweise nahen Werkzeugwechselpunkt
  (`xt=30`/`zt=10` statt Default 150/300, nur als Scratch-Variante ohne
  Aenderung der Referenzen) wird die QtDragon-Vorschaugrafik erstmals
  lesbar - Rohteil, Schrupppaesse und Konturzug sind klar erkennbar statt
  von der Eilgang-Linie zum weit entfernten Wechselpunkt dominiert zu
  werden. Details: `doc/NATIVE_VERIFICATION_2026-09-09.md`.

### SIM-Konfiguration korrigiert: echter Trockenlauf jetzt moeglich 2026-09-09

- `sim.qtdragon_lathe.basic_xz_lathe-1/lathe.ini` (ausserhalb dieses
  Projekts, lokale Testmaschine) verhinderte bisher jeden echten
  Trockenlauf: `emcTrajInit failed` beim Start liess die Maschine nie aus
  dem Not-Aus. Ursache war ein unnoetiger 50us-Base-Thread
  (`BASE_PERIOD = 50000`) fuer eine reine Simulation ohne
  Schrittmotor-Ausgabe. Nach Entfernen von `BASE_PERIOD`, Ergaenzen von
  `HOME = 0.0` in `[JOINT_0]`/`[JOINT_1]` und absolutem `SUBROUTINE_PATH`
  liess sich die Maschine referenzieren und `Innen_Radius.ngc` sowie
  `Innen_Stufe.ngc` liefen je einmal vollstaendig im AUTO-Modus bis `M30`
  durch, ohne Eintrag im NML-Fehlerkanal. Original-INI gesichert als
  `lathe.ini.bak-2026-09-09`. Details: `doc/NATIVE_VERIFICATION_2026-09-09.md`.

### SIM-Nachtrag zur Innen-Schlichtanfahrt 2026-09-09

- `Innen_Radius.ngc` und `Innen_Stufe.ngc` (neue Anfahrt XRI axial vor
  radialem Zustellen) in der QtDragon-Simulation ueber
  `linuxcnc.command().program_open()` geladen; die im GUI angezeigte
  Programmquelle bestaetigt Zeile fuer Zeile den erwarteten Text
  (`G0 Z2.000` / `G0 X9.000` / `G0 Z-30.000` / `G1 ...`). Damit
  akzeptiert auch der reale Task, nicht nur das eigenstaendige `rs274`,
  den geaenderten Fahrweg.
- Ein grafisch gezoomter, kollisionsfrei gepruefter Backplot war
  weiterhin nicht erreichbar (Vorschaugrafik zeigt nur eine
  Eilgang-Linie zum Werkzeugwechselpunkt); dieselben Startbefunde
  (`USRMOT`-Timeout, `emcTrajInit failed`, ungueltiger relativer
  `SUBROUTINE_PATH`) wie zuvor. Simulationskonfigurations-Einschraenkung,
  keine Generator-Regression. Details:
  `doc/NATIVE_VERIFICATION_2026-09-09.md`.

### LES-005 Sichere Innen-Schlichtanfahrt 2026-09-09

- Innen-Schlichten faehrt jetzt auf XRI axial bis zum Konturstart und stellt
  erst dort radial im Vorschub auf den Schnittdurchmesser zu. Damit entfaellt
  die bisherige radiale G0-Anfahrt an der Stirnseite mit anschliessendem
  diagonalen Einfahrweg zum tiefen Konturstart.
- Die Reihenfolge gilt auch ohne Werkzeugradiuskorrektur. Mit G41.1 muss der
  gerundete radiale Einfahrweg laenger als der Werkzeugdurchmesser sein;
  unzureichender Raum blockiert die Ausgabe.
- Vorne/hinten und Rundungsgrenzen getestet: 595 Stub-/44 Real-Qt-Tests,
  elf Referenzen und 43 native rs274-Matrixfaelle bestanden. Geaendert:
  `Innen_Stufe.ngc`, `Innen_Radius.ngc`.

### Native Nachpruefung nach Unterbrechung 2026-09-09

- Stand `11ee8b0` auf dem LinuxCNC-Rechner erneut geprueft: 590 Stub-/44
  echte Qt-Tests, elf Referenzen und 43 Matrixfaelle mit nativem rs274
  bestanden. Regeneration ohne NGC-Diff.
- Alle elf Referenzen in der vorhandenen QtDragon-Simulation im Not-Aus
  geladen. Startprobleme und Grenzen dokumentiert; kein Bewegungs- oder
  Backplotnachweis. Details: `doc/NATIVE_VERIFICATION_2026-09-09.md`.

### LES-022 CSS/G96-Modalzustand ausgelagert 2026-09-09

- Zweite Etappe von LES-022: neue Klasse `SpindleState`
  (`lathe_easystep/motion_state.py`) ersetzt die bisherigen ad-hoc
  settings-Keys `_pending_css`/`_active_css`/`_css_fixed_rpm` in
  `activate_pending_css()`, `suspend_css()` und `append_tool_and_spindle()`
  (`gcode_safety.py`). Alle anderen Operations-Generatoren (Abspanen,
  Bohren, Gewinde, Face, Groove) rufen bereits ausschliesslich die
  oeffentlichen Funktionen auf und waren nicht direkt betroffen.
- Im Gegensatz zur ersten Etappe (Positions-Tracking) war die CSS-Suspend/
  Resume-Logik bereits durchgehend konsistent - gezielt auf ein analoges
  Stale-State-Risiko geprueft, keines gefunden. Reine Architektur-
  bereinigung ohne Ausgabeaenderung: elf Referenzen und 43 rs274-
  Matrixfaelle (inkl. der `css_clearance_*`-Faelle) bestehen identisch.
- Ein Testfall mit direkter `_pending_css`-Dict-Konstruktion auf
  `SpindleState` umgestellt. 590 Stub-/44 echte Qt-Tests weiterhin
  bestanden.

### LES-022 Zentraler Bewegungszustand: Sicherheitsfehler bei Innen-Schruppen+Schlichten behoben 2026-09-09

- **Sicherheitsfehler gefunden und behoben:** Eine Innenbearbeitung im
  kombinierten Schruppen+Schlichten-Modus (Move-based Fallback, betrifft
  jede Innenbearbeitung, da G71/G72 dafuer nicht zuverlaessig ist, siehe
  LES-003), die NICHT die erste Operation im Programm ist, konnte den
  Rueckzug auf die sichere Z-Ebene vor dem Schlichtschnitt faelschlich
  ueberspringen und stattdessen im Eilgang (G0) diagonal direkt durch das
  noch stehengebliebene Restmaterial fahren. Ursache: das bisherige
  `_is_at_safe`-Flag blieb nach dem Schruppen unveraendert auf dem Wert
  einer vorherigen (typischerweise AUSSEN-)Operation stehen, obwohl die
  reale Position laengst eine andere war - `emit_approach()` vertraute
  diesem Flag, ohne die tatsaechlich hinterlegte Position gegenzupruefen.
  Real reproduziert und verifiziert: ohne den Fix erzeugt ein Programm mit
  vorangehender Aussen-Operation gefolgt von einer kombinierten Innen-
  Bohrung einen `G0 X12.000`-Eilgang bei Z=-29.900, mitten durch 0.2mm
  unbearbeitetes Schlicht-Aufmass.
- Neue Klasse `MotionState` (`lathe_easystep/motion_state.py`, LES-022,
  erste Etappe: Positions-Tracking) ersetzt die bisherigen ad-hoc
  settings-Keys `_is_at_safe`/`_safe_x`/`_safe_z` durch ein typisiertes
  Objekt mit `record()`/`update()`/`clear()`/`at()`. `gcode_safety.py`
  (`emit_safe_retract_for_op`, `emit_approach`, `append_tool_and_spindle`)
  und `gcode_groove.py` nutzen es jetzt statt der rohen Dict-Keys;
  `emit_approach()` vergleicht die Zielposition jetzt exakt gegen die
  zuletzt real erreichte Position statt nur ein Flag zu lesen.
  `gcode_roughing.py` invalidiert den Zustand nach jedem Schruppdurchlauf
  (G71/G72-Zyklus wie auch Move-based Fallback) explizit, da dessen reale
  Endposition hier bewusst nicht feingranular mitgefuehrt wird - ein
  nachfolgender `emit_approach()`-Aufruf fuer den Schlichtschritt muss sich
  dadurch immer neu auf eine tatsaechlich bekannte Position stuetzen statt
  auf eine veraltete Annahme.
  Zwei bestehende Referenzprogramme (`Innen_Radius.ngc`, `Innen_Stufe.ngc`)
  waren vom Fehler betroffen und wurden neu generiert; beide fuegen jetzt
  den zuvor fehlenden Rueckzug vor Schrupp- und Schlichteinstieg ein. Alle
  neun uebrigen Referenzen unveraendert.
- Fuenf Testdateien (`gcode_safety.py`-, `gcode_groove.py`- und
  `gcode_roughing.py`-Konsumenten sowie drei Testdateien mit direkten
  `_is_at_safe`/`_safe_x`/`_safe_z`-Dict-Konstruktionen) auf `MotionState`
  umgestellt; neuer gezielter Regressionstest fuer das gefundene Szenario
  (`test_combined_internal_rough_finish_after_external_op_retracts_before_finish_entry`).
  590 Stub-/44 echte Qt-Tests, elf NGC-Referenzen und 43 rs274-Matrixfaelle
  (WSL/Debian) bestanden.
- Weiterhin offen fuer LES-022: modale G/M-Codes (G90/G91, G94/G95, G18,
  G40/G41/G42, M3/M4/M5, M7/M8/M9) zentral verwalten sowie Positions-
  Tracking auf Schnittbewegungen (G1/G2/G3) innerhalb der Operations-
  Generatoren ausweiten.

### LES-020 Widget-Bootstrapping ausgelagert 2026-09-09

- Letzte verbleibende Teilaufgabe von LES-020: 19 Widget-Suche/-Auflösungs-
  Methoden (`_register_known_widgets`, `_resolve_core_widgets_strict`,
  `_get_widget_by_name`, `_find_root_widget`, `_poll_for_widget` u.a.) aus
  `lathe_easystep_handler.py` nach `lathe_easystep/ui_widget_lookup.py`
  verschoben; der Handler ruft sie nur noch ueber duenne, gleichnamige
  Wrapper-Methoden auf, Aufrufstellen unveraendert.
- `TAB_TRANSLATIONS` und `_looks_like_panel_widget` dafuer nach
  `lathe_easystep/ui_registry.py` verschoben, um einen Zirkelimport zu
  vermeiden. Dabei einen bestehenden `NameError`-Bug in
  `lathe_easystep/widget_resolver.py` gefunden und behoben:
  `_pick_best_root()` rief `_looks_like_panel_widget()` auf, ohne dass es
  importiert war - der Fehler wurde bislang von einem umgebenden
  `except Exception: pass` stumm verschluckt, wodurch der Fallback
  "sieht strukturell wie unser Panel aus" nie tatsaechlich griff.
- 589 Stub-/44 echte Qt-Tests (mit `uic.loadUi`) bestanden, elf
  NGC-Referenzen statisch unveraendert (reiner UI-Refactor ohne
  G-Code-Auswirkung).

### LES-028/032 Werkzeugdatenvalidierung 2026-09-09

- Explizite Werkzeugorientierung fuer Radiuskorrektur ganzzahlig in 0..9
  pruefen; defekte Werte nicht mehr abschneiden oder still ignorieren.
- Negative Radien, Ueberlauf des Schneidendurchmessers und auf D0 gerundete
  Korrekturwerte blockieren. Fehlende optionale Daten behalten ihr Verhalten.
- Neun Fehlerfaelle reproduziert, elf Regressionen ergaenzt. 589 Stub-/44
  Qt-Tests, 88 statische Checks, elf Referenzen und 43 rs274-Matrixfaelle
  bestanden. Referenzausgabe unveraendert; keine Werkzeughuellenabnahme.

### LES-027 Startzeitmessung 2026-09-09

- Reproduzierbarer Benchmark fuer den isolierten Aufbau mit echtem Qt:
  je fuenf frische Prozesse unter Windows und WSL, Rohdaten gespeichert.
- Neun nachgelagerte Startaufgaben des echten Panels erhalten Begin/Ende-
  Zeitmarken, einschliesslich Werkzeugtabelle und erster Konturvorschau.
- Gemessener UI-Ausschnitt: Median 0.368 s Windows, 1.362 s WSL.
  Kein vollstaendiger Panelstart; Ursache der >20 s bleibt unbekannt.
  Keine Beschleunigung behauptet, keine Generatoraenderung.
- 578 Stub-/44 Qt-Tests bestanden, keine Skips.
  [Messbericht](doc/STARTUP_2026-09-09.md).

### LES-040/028 Einstich-Ausgabegrenzen 2026-09-09

- Positive Vorschuebe/Zustellungen duerfen bei der o220-Ausgabe nicht
  auf null runden. Breiten-/Ueberdeckungspruefung verwendet gerundete
  Makrowerte; Start und Ende muessen unterscheidbar bleiben.
- Spanbruchanzahl wird ganzzahlig und nichtnegativ validiert statt gerundet.
- Fuenf Fehlerfaelle vor Korrektur reproduziert. 578 Stub-/44 Qt-Tests,
  elf Referenzen und 43 LinuxCNC-Matrixfaelle sowie 88 statische Checks bestanden.
  Referenzprogramme unveraendert; keine Maschinenabnahme.
- Bestehende harte Keilnut-Generatorsperre als verbleibende Funktionsluecke
  dokumentiert; in diesem Schritt nicht aufgehoben.

### LES-037 und Operationsfolgen: Matrix erweitert 2026-09-09

- Vier automatische M12-Gewindefreistichprogramme (innen/aussen,
  rechts/links) und zwei CSS-Schruppen-/Schlichten-Folgen mit identischem
  Werkzeug in gemeinsame Regression-/Interpreterfaelle aufgenommen.
- Fehlender Platz erhaelt bestehende Exportdateien; Konturverlaengerung
  verschiebt weder Freistichboegen noch Gewindeende. Kein Generatorfix
  fuer diese Faelle erforderlich.
- 573 Stub-/44 Qt-Tests, keine Skips; 88 statische Checks und 43
  Matrixprogramme im echten rs274 bestanden. Elf Referenzen unveraendert.
- WSLg/AXIS verfuegbar, verborgener GUI-Test erfolgreich. Grafischer
  Backplot und reale Maschinenabnahme wurden damit nicht durchgefuehrt.
  [Nachweise und Grenzen](doc/linuxcnc_2026-09-09/README.md).

### Review und Fortsetzung nach Unterbrechung 2026-09-09

- Zwischenstand mit 559 Stub-/44 Qt-Tests geprueft und weitgehend behalten.
- LES-018: `prefer_explicit` verhindert jetzt auch beim separaten Schlichten
  eine automatische G70-Wiederverwendung; auto/G70 bleibt erhalten.
- LES-028/040: G76 Q darf nach Ausgaberundung nicht 90 erreichen;
  CSS-Schnittgeschwindigkeit und Startdurchmesser duerfen nicht auf null runden.
  Vier zuvor fehlschlagende Regressionen sichern die Korrekturen ab.
- Fuenf CSS-Faelle und zwei G70-/explizite Schlichtfolgen in die
  reproduzierbare LinuxCNC-Matrix aufgenommen: elf Referenzen und
  37 Matrixfaelle bestanden. 563 Stub-/44 Qt-Tests, 88 statische Checks.
- Zu weitgehende LES-013-Abschlussaussage korrigiert: stock_x entspricht
  nicht jedem Passdurchmesser; explizite Freifahrten und zyklusinterne
  Bewegungen sind getrennt zu bewerten. Backplot/Maschinenabnahme offen.
  [Review und Interpreter-Nachweise](doc/linuxcnc_2026-09-09/README.md).

### Dokumentations-Nachtrag 2026-09-09 (LES-012/027/037)

- LES-012: `Kontur_Radius_Fase.ngc` (`G3 ... I-3.000`) und die daraus
  abgeleiteten Matrixfaelle sind Teil der bei jeder Sitzung gegen echten
  rs274 verifizierten Referenzen - der Nichtnull-I-Parser-Punkt ist damit
  abgedeckt (Backplot grafisch weiterhin offen).
- LES-027: neues `measure_startup.py` misst Shell-UI, acht Teil-UIs,
  Zusatzwidgets und statische Uebersetzungsstruktur separat, mit
  Handler-Instrumentierung fuer die neun nachgelagerten Startaufgaben. Die
  gemeldeten >20s liessen sich unter Windows (0.587s) und WSL/Debian
  (1.565s) NICHT reproduzieren - kein Root Cause, keine unbelegte
  Optimierung. Siehe [doc/STARTUP_2026-09-09.md](doc/STARTUP_2026-09-09.md).
- LES-037: neue automatisierte Matrix (`test_thread_relief_matrix.py`)
  beweist die Kernaussage - eine Konturverlaengerung hinter dem Gewinde
  verschiebt den Freistich nicht - fuer Aussen/Innen x Rechts/Links, alle
  vier real gegen rs274 verifiziert. Reale Backplot-/Trockenlauf-Abnahme
  bleibt der einzige noch offene Punkt.

### LES-028 G76-Zustellwinkel begrenzt 2026-09-09

- `infeed_q` (G76-Zustellwinkel `Q`) floss bisher vollstaendig ungeprueft
  in die Ausgabe ein - ein negativer oder unplausibel grosser Wert
  (>=90 Grad) waere unveraendert als `Q`-Wort ausgegeben worden. Jetzt auf
  den physikalisch gueltigen Bereich 0..<90 Grad geprueft (0 = radiale
  Zustellung, z. B. Quadratgewinde, bleibt explizit gueltig).
- "G7-Massystem nicht erneut als offenen Fachfehler behandeln": keine
  verbleibende Stelle gefunden, die das bereits per Realtest bestaetigte
  G76-Massystem noch als offen fuehrt - kein Codegap.
- Bewusst nicht umgesetzt: "Werkzeugwechsel nur aus normalisiertem
  Werkzeugdatensatz erzeugen" und "Preset-/manuelle Werte nachvollziehbar
  vergleichen" sind im TODO nicht praezise genug spezifiziert fuer eine
  sichere Entscheidung, ohne moeglicherweise viele bestehende Testfixtures
  oder reale Programme ohne vollstaendig gepflegte Werkzeugtabelle zu
  brechen (aehnliches Risiko wie beim Drehzahl-Fund in LES-040) - bleibt
  offen fuer eine Sitzung mit Klaerung der genauen Anforderung.
- Unter WSL/Debian mit echtem rs274 verifiziert, keine Ausgabeaenderung.
  559 Stub-Tests, 44 Real-Qt-Tests, keine Skips.

### LES-018 G70-Wiederverwendung fuer separaten Schlichtstep 2026-09-09

- Ein reiner Schlichtstep (eigene Operation, typischerweise eigenes
  Werkzeug) nutzt jetzt `G70 Q<sub>`, um den Kontur-Sub eines frueheren,
  separaten Schruppschritts wiederzuverwenden, statt die Fertigkontur
  nochmal explizit als G1/G2/G3-Liste auszugeben - aber nur, wenn dieser
  exakte Sub nachweislich per G71/G72 zyklisch definiert wurde (neue
  `_cycle_defined_subs`-Zustandsverfolgung) und keine Werkzeugradius-
  korrektur noetig ist.
- Fallback auf den bestehenden expliziten Schlichtweg bleibt fuer alle
  anderen Faelle unveraendert (keine benannte Kontur, kein vorheriger
  Zyklus, Innenbearbeitung - nutzt G71/G72 ohnehin nie -, Werkzeug-
  korrektur). Reiner Schlichtstep schruppt dabei nie erneut: G70 fuehrt
  ausschliesslich den bereits vorhandenen Fertigkontur-Sub aus.
- Real mit einem separaten Zwei-Werkzeug-Rough/Finish-Programm gegen
  echten rs274 verifiziert: der Schlichtschritt fuehrt nur die zwei
  tatsaechlichen Konturbewegungen aus, keine erneute Schruppbewegung,
  keine zweite Subroutine-Definition.
- Alle 11 Referenzen und 30 Matrixfaelle bestehen unveraendert (keine
  nutzt den neuen Pfad). 555 Stub-Tests, 44 Real-Qt-Tests, keine Skips.

### LES-013 CSS-Aktivierungsposition verifiziert 2026-09-09

- Codepruefung: jeder Aufrufer von `append_tool_and_spindle()` mit CSS-
  Parametern (`gcode_face.py`, `gcode_roughing.py` - Schrupp-Zyklus,
  Move-based-Schruppen je Pass, separater Hinterschnitt, Schlichtschnitt,
  `gcode_thread.py`, `gcode_groove.py`) uebergibt als `css_start_diameter`
  konsistent den Durchmesser, an dem `emit_approach()` unmittelbar danach
  tatsaechlich ankommt, bevor G96 aktiviert wird - keine Diskrepanz
  gefunden. Move-based-Schruppen aktiviert/suspendiert CSS sogar je Pass.
- Modalsequenz frisch gegen echten rs274 verifiziert (kanonische
  `SET_SPINDLE_MODE`/`SET_SPINDLE_SPEED`-Ausgabe eines CSS-Wechsel-
  Programms geprueft).
- Kein Codegap gefunden, keine Aenderung noetig - alle offenen
  Checklistenpunkte in TODO.md abgehakt. Grafischer Backplot und reale
  Maschinenabnahme bleiben separate, unveraenderte Grenzen (LES-030).

### LES-031 Redundante Nullbewegungen entfernt 2026-09-09

- `gcode_drill.py` gab nach jedem Bohrzyklus unbedingt ein `G0 Z<safe_z>`
  aus. Empirisch gegen echten `rs274` verifiziert: LinuxCNC-Zyklen kehren
  im Default-Modus G99 auf die Rueckzugsebene R zurueck, nicht auf die
  Z-Position vor dem Zyklus - da `retract` ohne Angabe auf `safe_z`
  faellt, stand das Werkzeug nach `G80` im Standardfall bereits auf
  `safe_z`. Die zusaetzliche Bewegung wird jetzt nur noch ausgegeben, wenn
  `retract` explizit hoeher als `safe_z` gesetzt ist (dann echt noetig).
- `append_tool_and_spindle()` gab vor jedem Werkzeugwechsel unbedingt
  einen Rueckzug auf die Aussen-Sicherheitsposition aus, auch wenn die
  vorherige Operation dort bereits exakt stand. Eng begrenzte
  Zustandsverfolgung (`_safe_x`/`_safe_z`, nur an Stellen gesetzt, wo die
  Position unmittelbar zuvor sicher bekannt ist) erkennt und ueberspringt
  diesen Fall jetzt.
- Bewusst nicht angefasst: eine dritte Redundanz in den Innen-Schrupp-
  zyklen (`rough_turn_parallel_x/z`) - ein Fix dafuer bräuchte echte
  zentrale Positionsverfolgung (LES-022), sonst Risiko veralteten, im
  `rough_finish`-Kombimodus falsch als sicher angenommenen Zustands.
- Unter WSL/Debian mit echtem rs274 verifiziert (11 Referenzen, 30
  Matrixfaelle). 553 Stub-Tests, 44 Real-Qt-Tests, keine Skips.

### LES-001 Warnung und Fahrweg abgeglichen 2026-09-09

- `get_approach_warnings()` meldete "Rueckzugsebene schneidet den
  Futterbereich" bisher allein anhand des Z-Grenzwerts der Futter-
  Sperrzone, ohne wie `validate_chuck_segment()` auch das X-Intervall zu
  pruefen. Eine sichere Position mit X ausserhalb der Sperrzone wurde
  dadurch faelschlich als gefaehrdet gemeldet, obwohl der tatsaechliche,
  bereits abgesicherte Fahrweg dort nie hinfuehrt - Warnungstext und
  echtes Verhalten widersprachen sich. Beide pruefen jetzt dieselbe
  Bedingung.
- Damit ist LES-001 vollstaendig durchgegangen bis auf die bewusst nicht
  umgesetzte "dynamische" Achsreihenfolge-Wahl je Eilgang: das wuerde den
  Projektzielen (deterministische, nachvollziehbare Bewegungen)
  zuwiderlaufen und ist auch im ausgewerteten Inventor-Post (LES-006)
  nicht vorgesehen - der nutzt ebenfalls eine feste, global konfigurierte
  Reihenfolge statt einer Fall-zu-Fall-Entscheidung.
- Unter WSL/Debian mit echtem rs274 verifiziert (11 Referenzen, 30
  Matrixfaelle), keine Ausgabeaenderung. 550 Stub-Tests, 44 Real-Qt-Tests,
  keine Skips.

### LES-006 Inventor-Post als Referenz ausgewertet 2026-09-09

- `doc/linuxcnc turning.cps` (Autodesk generischer LinuxCNC-Drehpost)
  ausgewertet: der Post hat keine Matrix je Operationstyp - Rueckzugs- und
  Anfahrreihenfolge sind je eine globale Post-Eigenschaft fuer das gesamte
  Programm, unabhaengig vom Operationstyp. Unser Generator unterscheidet
  bereits feiner (Bohren/Gewinde Z-vor-X, Einstich/Keilnut X-vor-Z).
- Gepruefter, bewusst nicht umgesetzter Vorschlag: Rueckzug bei
  unbekanntem Ausgangszustand auf eine feste G53-Maschinenposition
  umstellen (wie in der Referenz). Geometrisch widerlegt: ein fester
  Punkt macht eine Diagonalbewegung von unbekannter Startposition nicht
  automatisch kollisionsfrei (Gegenbeispiel dokumentiert in TODO.md) und
  entzieht sich vollstaendig der LES-001-Segmentpruefung. Keine
  Codeaenderung; Ergebnis in TODO.md/DEV.md festgehalten.

### LES-040 Spindel-Start darf nicht stillschweigend ausbleiben 2026-09-09

- `append_tool_and_spindle()` - die zentrale Funktion, die fuer JEDE
  Operation (Abspanen, Einstich, Bohren, Gewinde, Planen) die Drehzahl
  ausgibt - schluckte `spindle=0`, negative Werte, fehlende Werte sowie
  eine auf 0 U/min gerundete positive Drehzahl bisher vollstaendig
  stillschweigend: kein Fehler, kein `M3`/`S..` irgendwo im Programm. Real
  reproduziert: eine komplette Abspanen-Operation mit `spindle=0` erzeugte
  ein vollstaendig "gueltiges" Programm, in dem die Spindel nie gestartet
  wird.
- Blockiert jetzt die Ausgabe, mit einer bewussten Ausnahme fuer die reine
  Werkzeugwechsel-Positionierung (`require_spindle=False` an den zwei
  Stellen in `gcode_program.py`, deren Aufgabe nur das Anfahren des
  Wechselpunkts ist - die eigentliche Drehzahl inkl. CSS setzt danach
  immer der jeweilige Operations-Generator selbst).
- Aendert 22 Testfixtures quer durchs Projekt (Innenkontur-Matrix,
  Subroutinen, Rueckzugslogik, CSS, Parting), die bisher nie eine
  Drehzahl gesetzt hatten, um eine sinnvolle Drehzahl - keine Aufweichung
  der neuen Pruefung.
- Unter WSL/Debian mit echtem rs274 verifiziert (11 Referenzen, 30
  Matrixfaelle), keine Ausgabeaenderung fuer bestehende Programme. 549
  Stub-Tests, 44 Real-Qt-Tests, keine Skips. "Koordinaten, Vorschuebe,
  Zustellungen und Sicherheitswerte" ausserhalb der Drehzahl sind weiterhin
  nicht vollstaendig auf fachlich passende Wertebereiche durchgegangen.

### LES-039 M1 vor dem ersten Werkzeugwechsel 2026-09-09

- `optional_stop_toolchange` ("Fuegt vor JEDEM Werkzeugwechsel ein
  optionales M1 ein") schloss den allerersten Werkzeugwechsel bisher
  stillschweigend aus - genau dort, wo Werkzeug und Ausgangsposition am
  wenigsten bekannt sind, weil keine vorherige Operation existiert. M1
  gilt jetzt fuer jeden Werkzeugwechsel einschliesslich des ersten.
- M1 steht jetzt VOR der angenommenen sicheren Z-vor-X-Rueckzugsbewegung,
  nicht mehr danach - der Bediener kann den tatsaechlichen Maschinen-
  zustand pruefen, bevor irgendeine Bewegung ausgefuehrt wird.
- Das ist eine prozedurale Absicherung fuer LES-039 ("unbekannten Zustand
  nicht als sicher annehmen"), keine geometrische: die pauschale
  Z-vor-X-Reihenfolge bei unbekanntem Ausgangszustand bleibt bestehen, da
  eine Textgenerierung den realen Maschinenzustand nicht kennen kann.
- Unter WSL/Debian mit echtem rs274 verifiziert (11 Referenzen, 30
  Matrixfaelle, Sonderfall mit M1 vor dem ersten Wechsel), keine
  Ausgabeaenderung fuer bestehende Programme. 543 Stub-Tests, 44
  Real-Qt-Tests, keine Skips.

### LES-001 Zweiter Rueckzugsschritt gegen Rohteil/Futterzone 2026-09-09

- Der zweite Teilschritt jeder Rueckzugsreihenfolge (die zuerst erreichte
  sichere Achse bleibt dabei konstant, nur die andere Achse bewegt sich)
  wird jetzt in `emit_safe_retract_for_op()` (Einstich/Keilnut, Bohren/
  Gewinde, X-vor-Z-Fallback bei Start im Rohteil/in der Futterzone) UND in
  `emit_approach()` (Aussen-Modus) gegen Futter-Sperrzone und - ausser im
  Innen-Modus, der eine Bohrung nicht als Rechteck abbilden kann - gegen
  die Rohteil-Huellkurve geprueft. Der erste Teilschritt (Flucht aus der
  aktuellen Position) bleibt bewusst ungeprueft, da er dort legitim
  beginnen darf.
- Dabei einen echten, bis dahin unentdeckten Fall gefunden und behoben:
  ein bestehender Test konfigurierte eine "sichere" XRA=60, die selbst noch
  innerhalb der Futter-Sperrzone (X20..80) lag - der zweite Rueckzugsschritt
  haette die gesamte restliche Z-Strecke ungeprueft mitten durch die Sperr-
  zone gefuehrt. Testfixture auf eine tatsaechlich sichere XRA=90 korrigiert.
- Unter WSL/Debian mit echtem rs274 verifiziert: alle 11 Referenzen und
  30 Matrixfaelle bis PROGRAM_END bestanden, keine Ausgabeaenderung.
  542 Stub-Tests, 44 Real-Qt-Tests, keine Skips. Die eigentliche
  Achsreihenfolge-Entscheidung nach Rohteil-/Futterzone (LES-001,
  Kernpunkt: Reihenfolge dynamisch statt fest je Operationstyp) bleibt
  offen - fixe Konventionen, die im Einzelfall nicht sicher sind, werden
  jetzt aber blockiert statt stillschweigend ausgefuehrt.

### LES-001 Achsreihenfolge und Werkzeugwechsel-Regressionen 2026-09-09

- Regressionstest fixiert die op-spezifische Rueckzugs-Achsreihenfolge:
  Einstich/Keilnut zieht X vor Z zurueck, Bohren/Gewinde immer Z vor X -
  unabhaengig vom Startpunkt, damit ein im Einstich/Gewindegang stehendes
  Werkzeug nicht zuerst radial bewegt wird.
- Aussen- UND Innen-Schruppen->Schlichten mit identischem Werkzeug erzeugen
  nachweislich nur einen Werkzeugwechsel; die Anfahrt der zweiten Operation
  lief in beiden Faellen fehlerfrei durch (bei Innenarbeit bleibt die
  sichere Position innerhalb der bereits gebohrten/hohlen Zone - kein neuer
  Fehler gefunden, bestehendes Verhalten jetzt regressionsgesichert).
- 539 Stub-Tests, 44 Real-Qt-Tests, keine Skips; Referenzprogramme
  unveraendert. Die eigentliche Achsreihenfolge-Entscheidung nach Rohteil-/
  Futterzone (LES-001, Kernpunkt) und der Abgleich Warnung/tatsaechlicher
  Fahrweg bleiben offen.

### LES-001 Diagonal-Eilgaenge gegen Rohteil 2026-09-09

- `validate_stock_segment()` prueft reine Diagonal-Eilgaenge (`G0 X.. Z..`
  in einer Zeile) gegen die Rohteil-Huellkurve als vollstaendiges Rechteck -
  auch wenn Start- und Zielpunkt jeweils fuer sich ausserhalb liegen, die
  Strecke dazwischen aber mitten durchs Rohteil fuehrt. Betrifft den
  Diagonal-Rueckzug in `emit_safe_retract_for_op` und die Anfahrt der
  Werkzeugwechselposition in `move_to_toolchange_pos`.
- Bewusst ausgenommen: die achsweise Anfahrt-/Rueckzugsfolge in
  `emit_approach` (dort landet der Zielpunkt bei Folgeoperationen wie
  Schlichten nach Schruppen absichtlich innerhalb der Rohteil-Huellkurve)
  sowie jede Sicherheitsposition im Innen-Modus - die Huellkurve ist ein
  reines Aussenmass-Rechteck und kann eine Bohrung nicht abbilden.
- Regressionsfaelle fuer Rohteil-Diagonalkreuzung ergaenzt, analog zur
  bestehenden Futter-Sperrzonen-Pruefung. 533 Stub-Tests, 44 Real-Qt-Tests,
  keine Skips; Referenzprogramme unveraendert (reine Zusatzpruefung ohne
  Ausgabeaenderung). Die eigentliche "sichere Achsreihenfolge je nach
  Rohteil-/Futterzone" (LES-001, erster Punkt) bleibt offen.

### LES-005 Innen-Schlichtrueckzug 2026-09-09

- Innen-Schlichten zieht zuerst radial nach XRI und erst danach axial nach
  ZRI zurueck. Programmierte Segmente werden gegen Futter-Sperrzonen geprueft.
- Bei aktiver Radiuskorrektur G40 vor der radialen G1-Freifahrt; physischer
  Weg im G7-Masssystem nach Ausgaberundung muss laenger als der Schneiden-
  durchmesser sein. Bei zu wenig Freiraum wird die Ausgabe blockiert.
- Richtungs-, Korrektur- und Rundungsregressionen ergaenzt. Vier weitere
  LinuxCNC-Matrixfaelle mit Radiuskorrektur an Innenzylinder/-konus.
- 524 Stub-Tests, 44 Qt-Tests, 88 statische Checks; elf Referenzen und
  30 Matrixprogramme im echten Interpreter bestanden. Werkzeughuellen,
  weitere kompensierte Konturformen und reale Abnahme bleiben offen.
  [Pruefbericht](doc/LES005_INNEN_RUECKZUG_2026-09-09.md).

### WSL-/LinuxCNC-Fortsetzung 2026-09-09

- Echter rs274-Lauf deckt nichtmonotonen Bogen in `Kontur_Radius_Fase` auf.
  G71/G72-Pruefung beruecksichtigt jetzt analytische Bogenextrema und weist
  solche Konturen ab; urspruenglicher Fehler fuer beide Achsstrategien getestet.
- Positives Referenzbeispiel auf monotonen Viertelkreis umgestellt; Nutzer-
  konturen werden nicht automatisch veraendert. Expliziter Schlichtweg erhaelt
  jetzt auch bei rein primitiven Konturen G2/G3 statt gerader Verbindungen.
- Elf Referenzen und 26 Matrixprogramme bestehen LinuxCNC 2.10.0~pre1 unter
  WSL/Debian bis PROGRAM_END. Kanonische Ausgaben und SHA256-Manifeste
  archiviert; Matrixgenerator und Report-/Eingabeordneroptionen hinzugefuegt.
- 516 Stub-Tests, 44 Real-Qt-Tests, keine Skips; 88 statische NGC-Checks.
  Grafischer Backplot, Trockenlauf und verbleibende Sicherheitsaufgaben offen.
  [Interpreterbericht](doc/linuxcnc_2026-09-09/README.md).

### Fortsetzung 2026-09-09 (LinuxCNC-Abnahme offen)

- LES-013: gesicherten CSS-Zwischenstand geprueft; veraltete vorbereitete
  Aktivierung beim G97-Fallback entfernt, Maximaldrehzahl ohne Ueberschreitung
  durch Ganzzahlrundung. Gemischtes CSS/G97/CSS-Referenzprogramm und echter
  Qt-Programmdatei-/Formular-Roundtrip ergaenzt.
- LES-040/028: Bohrmodi werden nicht mehr still zu G81 umgedeutet;
  endliche Bohrwerte, positive ausgegebene Vorschuebe/Zustelltiefen und
  nichtnegative Verweilzeiten vor Bewegungsplanung geprueft. Zahlenleser
  ersetzen defekte explizite Werte nicht durch andere Aliase oder Defaults.
  Fehler beim G-Code-Export erhalten bestehende Dateien.
- LES-003/012/015: Innenradius in beiden Konturrichtungen und drei Modi,
  Schnittgrenzen und erhaltene Boegen getestet. Ausgabe von Schlichtweg und
  Kontur-Subroutine sowie G7-Bogenradien verglichen.
- Elf Referenzen regeneriert; neu `CSS_Wechsel.ngc` und `Innen_Radius.ngc`.
  Die bisherigen neun Dateien bleiben unveraendert. 513 Stub-Tests,
  44 Real-Qt-Tests und 88 statische NGC-Checks bestanden, keine Skips.
- Testabhaengigkeiten festgehalten und veraltete README-Einschraenkungen
  korrigiert. WSL und rs274 fehlen auf diesem Rechner; offene P0-Punkte,
  komplette CSS-Modalsequenz und reale Abnahmen bleiben offen.
  [Verifikationsbericht](doc/VERIFICATION_2026-09-09.md).

### Lokale Umsetzung 2026-09-08 (noch keine Maschinenabnahme)

- LES-041 abgeschlossen: Generierung auf tief kopiertem Programmsnapshot;
  Konturen/Freistiche frisch aufloesen, keine alten Ableitungen wiederverwenden.
  Fehlende oder doppelte Konturnamen und unbekannte Operationen brechen ab.
- LES-042 abgeschlossen: Programm-JSON ueber temporaere Datei und atomaren
  Ersatz schreiben; bei Fehler bleiben Datei und bisheriger Programmpfad erhalten.
- LES-043 abgeschlossen: Step-Dateien ebenfalls atomar, Verknuepfung erst
  nach erfolgreichem Schreiben; Teilfehler melden bereits gespeicherte Steps,
  ungespeicherte/verknuepfungslose Steps bleiben dirty.
- LES-038 abgeschlossen: Stub-/Real-Qt in getrennten Prozessen, gemeinsamer
  `run_tests.py`; 472 Stub-Tests und 43 echte Qt-Tests bestanden, keine Skips.
- LES-023 abgeschlossen: automatische Kommentare ohne gespeicherte Nummer;
  manuelle Kommentare bleiben erhalten. Konturen zaehlen in der Step-Liste
  als Geometrieschritte mit, erzeugen aber keine eigene Bearbeitung.
- LES-011 abgeschlossen: gemeinsame Freistich-Primitive fuer Vorschau,
  Kontur-Sub und explizites Schlichten auf identische Ausgabe getestet;
  Segment-Features ueberstehen Save/Load.
- LES-016 abgeschlossen: Freistichnorm nur bei Vorschlagsmodus sichtbar;
  alte IDs normalisiert, beide Zweige und Sprach-/Save-/Load-Wechsel mit
  echtem Qt geprueft. Kontur-Kantenfelder bleiben sichtbar/deaktivierbar;
  Innen/Aussen bekommt ohne fachlichen Bedarf keine zusaetzliche Ausblendung.
- LES-001/039 teilweise: gemeinsame Anfahrt achsweise; Futter-Sperrzone
  blockiert Ziel- und Segmentverletzungen. XT/ZT auch bei Einzelwerkzeug
  zwingend. Unbekannte Startposition und vollstaendige Kollisionsplanung offen.
- LES-040/028 teilweise: endliche Zahlen an Daten-/Geometriegrenzen,
  ganzzahlige Werkzeugnummern und G76-Eingaben; defekte Pfadpunkte abweisen.
  Ungueltige Gewindesteigung wird nicht mehr still ersetzt, H=0 bleibt H=0.
- LES-003/015 teilweise: vorhandenes XI als Bohrungsgrenze erhalten,
  Innenaufmass richtig ausrichten; 18 Profil-/Richtungs-/Moduskombinationen.
- LES-036 implementiert: Planradius aus gemeinsamen Geometrieprimitiven,
  G2 mit radialem I im Durchmessermodus, G91.1 im Programmkopf;
  analytische Bogen- und echte Qt-Roundtrip-Tests. LinuxCNC-Abnahme offen.
- LES-020 teilweise: Kopf-, Kontur-, Gewinde-Preset- und Tooltip-Funktionen
  aus Handler in eigene Module extrahiert; Widget-Bootstrapping bleibt offen.
- Neun NGC-Referenzen regeneriert, darunter Innenstufe, mittiger Freistich
  und Planradius; statischer Validator korrigiert, rs274-Batchpruefung
  vorbereitet. Fuer diesen Stand keine reale Parser-/Backplot-Verifikation.

- Fix: Die neue sichere Innenanfahrt in `emit_approach()` (axial auf XRI,
  erst danach radial zustellen, kein diagonaler Schnellgang durch die
  Bohrung) erzeugte einen bedeutungslosen zusaetzlichen `G0 Z...` auf
  denselben Z-Wert, sobald der Konturstart bereits auf der sicheren
  Z-Ebene lag (haeufiger Fall, z. B. bei einem reinen Innen-Schlichtstep).
  Die Zeile wird jetzt nur noch ausgegeben, wenn sich der Z-Wert tatsaechlich
  aendert. Verifiziert mit `rs274` (keine Diagonalbewegung, keine
  Nullbewegung) und gegen den alten Code per manuellem Revert bestaetigt
  fehlgeschlagen; `tests/test_parting_slice.py::test_internal_finish_with_nose_comp_gets_nonzero_entry_move`
  auf die korrigierte Sequenz umgestellt
- Fix: Die axiale Lage der 30°-Flanke wurde faelschlich von Innen/Aussen
  abgeleitet. Sie folgt jetzt ausschliesslich der Gewinderichtung: Die Flanke
  liegt immer an der Seite, an der das Gewinde in den Freistich einlaeuft.
  Das gilt fuer Aussen- und Innengewinde sowie Rechts- und Linksgewinde.
- Gewinde: Der Reiter hat jetzt die getrennten Eingaben "Gewinde-Vorlauf"
  und "Gewinde-Auslauf". Sie erzeugen einen G76-Taper vor bzw. nach dem
  programmierten Gewinde und werden in der Vorschau als schräge An-/Ausläufe
  dargestellt. LinuxCNC G76 kann technisch nur eine gemeinsame E-Laenge:
  ein einzelner Wert wird mit `L1` oder `L2` ausgegeben, zwei gleiche Werte
  mit `L3`; zwei unterschiedliche Werte brechen mit einer klaren Meldung ab,
  statt einen falschen Taper zu erzeugen.
- Fix (P0): Ein Innen-Freistich mit dynamischer Werkzeugradiuskorrektur
  `G41.1` fuehrte LinuxCNC an der konkaven Schulter zu einem Interpreterabbruch
  ("Straight feed in concave corner ..."). Der nachfolgende Innen-G76-Zyklus
  wurde dadurch nie erreicht und erschien weder im Backplot noch beim Lauf.
  Bei integrierten Innenfreistichen wird diese fuer die Form unzulaessige
  Kompensation jetzt gezielt deaktiviert; der Kontur- und Gewindeschritt wird
  vollstaendig verarbeitet.
- Freistich (P0): Automatische DIN-76-Freistiche fuer Aussen- und
  Innengewinde werden nicht mehr als rechteckige Tasche erzeugt. Die Kontur
  besteht jetzt aus Ein-/Auslaufflanken, tangentialen G2/G3-Boegen und dem
  Freistichgrund; dieselbe Primitive-Geometrie wird fuer Schlichten,
  Kontur-Subroutine und Vorschau verwendet.
- Korrektur Freistichprofil: `g1` und `g2` werden jetzt entsprechend der
  DIN-Skizze von der Schulter aus ausgewertet. Die Form ist asymmetrisch:
  eine 30°-Flanke auf der Gewindeseite, gerader Grund, Schulterradius und
  radiale Schulter. Die vorherige beidseitig schraege Trapezform war keine
  DIN-76-Form.
- Presets: Die automatische DIN-76-1-Auswahl verwendet jetzt je Gewindeseite
  die Tabellenmasse `dg`, `g1`, `g2`, Kurzform und `r`. Die frueher
  geschaetzten Tiefen und die fuer Innengewinde faelschlich wiederverwendeten
  Aussenwerte sind entfernt. M30x3,5 hat damit aussen `dg=d-5`, innen
  `dg=D+0,5`; M12 innen verwendet Form C/D mit `g2=9,1 mm`.
- Vorschau: Automatische Gewindefreistiche werden als Bauteilgeometrie aller
  verknuepften Aussen-/Innenkonturen dargestellt, auch wenn gerade der
  Gewinde-Step oder ein anderer Reiter aktiv ist. Die Anzeige haengt nicht
  mehr von der Auswahl eines Abspanen-Steps ab.
- Verifikation: `doc/Test_Dateien/test.ngc` aus `Test.lse` neu erzeugt;
  LinuxCNC `rs274 -g` akzeptiert die neuen Freistichboegen bis `M30`.
- Innenbearbeitung: Move-based-Innen-Schruppen vermeidet jetzt diagonale
  Schnellgaenge innerhalb der Bohrung und redundante Safe-Moves. Jeder Pass
  faehrt axial ausschliesslich auf `XRI`, stellt erst dort auf den
  Schnittdurchmesser zu und zieht danach nur radial auf `XRI` zurueck.
- Innen-Schlichten und Innengewinde verwenden fuer die Einfahrt ebenfalls
  immer `Z` auf der freien `XRI`-Ebene, danach `X`; der bisherige direkte
  diagonale Schnellgang vom Rueckzugspunkt in die Kontur ist entfernt.
- Referenzprogramm: Das M12-Innengewinde nutzt jetzt ebenfalls den
  automatischen DIN-76-Freistich; der Innen-Schlichtstep verarbeitet ihn
  vollstaendig statt ihn zu ignorieren.
- Fix (P0): Ein Generatorfehler wurde bisher still in ein dreizeiliges
  Fallback-Programm umgesetzt und anschliessend als erfolgreicher Export
  gemeldet. Fehler werden jetzt an die UI weitergegeben; die NC-Datei wird
  nur nach einer vollstaendigen Erzeugung atomar ersetzt. Eine vorhandene
  Programmdatei bleibt bei einem Fehlschlag unveraendert.
- Freistich: Reicht die lange DIN-76-Form bis zur folgenden Kontur-Schulter
  nicht aus, waehlt der Generator jetzt die hinterlegte Kurzform nur dann,
  wenn sie vollstaendig in die zylindrische Gewindestrecke passt; anderenfalls
  bleibt der sichere Generierungsabbruch bestehen. Das Referenzprogramm
  verwendet fuer das M30-Gewinde damit die Kurzform von `Z=-25,3` bis `-34,3`
  statt eines alten manuellen Freistichs bei `Z=-35`.
- Fix: Beim Ausblenden eines Freistichs fuer G71/G72 werden die getrennten
  zylindrischen Teilsegmente wieder zu einer Schruppkontur zusammengefasst.
  LinuxCNC erhaelt damit keine nicht schneidbare Parallel-Linienfolge mehr
  (`G7X error: Cannot intersect parallel lines`).
- Fix (P0): Abspanen verwendet fuer Konturen mit Freistich keine ungeeignete
  globale Fertigkontur mehr als `G71/G72`-Subroutine. Relief-freie
  Schruppvarianten erhalten eine eigene Subroutine; bei "voll in Kontur" wird
  wegen der axial nichtmonotonen U-Geometrie sicher auf Move-based-Ausgabe
  gewechselt. Damit entsteht kein LinuxCNC-Fehler `G7X error: Not monotonic`.
- Verifikation: `doc/Test_Dateien/test.ngc` aus `Test.lse` regeneriert und mit
  `/home/adm1n/linuxcnc/configs/Drehbank/tool.tbl` ueber den lokalen
  LinuxCNC-Interpreter `rs274 -g` vollstaendig bis `M30` geparst.
- Freistich (LES-037): Ein aktivierter DIN-76-Gewindefreistich wird jetzt aus
  Gewindeende, Hand, Durchmesser und der normierten Ueberdeckung `f`
  abgeleitet. Er wird nur in eine passende zylindrische Aussen-/Innenkontur
  eingespleisst und dadurch identisch in Vorschau, Kontur-Subroutine,
  Schruppen und Schlichten verwendet. Fehlt die Konturstrecke, bricht die
  G-Code-Erzeugung ab statt einen Freistich am Konturende oder im Vollmaterial
  zu erzeugen. Regressionen decken Aussen- und Innengeometrie sowie den
  sicheren Abbruch ab.
- Docs: README und DEV-Dokumentation beschreiben die verbindliche
  Gewinde-zu-Kontur-Zuordnung; der Realtest-Fragenkatalog enthaelt die
  LinuxCNC-Abnahme fuer automatischen Aussen- und Innenfreistich.
- Presets: DIN-76-1-Regelgewinde bis M30 enthalten jetzt Steigung, Freistichbreite fuer Aussen/Innen, Kurzformbreite, normierte Gewindeueberdeckung und Radius. Die bisherige rein groessenbasierte Breiten-Schaetzung wird dadurch fuer vorhandene Regelgewinde ersetzt; M30x3,5 verwendet beispielsweise `g2=12,0 mm`, `f=4,7 mm`, `r=1,6 mm` aussen und `g2=17,7 mm` innen.
- Performance: Die vollstaendige Sprach-/Widget-Praesentation bleibt Teil der synchronen Startbereitschaft. Ihre statische Uebersetzung indexiert den Widgetbaum jetzt einmal nach `objectName`, statt fuer jeden Schluessel erneut eine rekursive `findChild()`-Suche auszufuehren; das beseitigt die quadratische Startzeit nach der UI-Aufteilung.
- Safety/Audit (LES-037): Ein Kontur-Freistich ist derzeit nur an ein Kontursegment gebunden, nicht an eine konkrete Gewindeoperation. Im Referenzprogramm liegt das Feature bei `Z=-35`, das Gewinde endet aber bei `Z=-30`; Vorschau und Ausgabe duerfen diese fehlende Zuordnung nicht als korrekt behandeln.
- Fix (LES-037, P0): Der Gewinde-Generator bricht jetzt vor der Ausgabe mit einer klaren Fehlermeldung ab, wenn die vorgeschlagene DIN-Freistichbreite laenger als das Gewinde ist. Damit wird kein ungueltiger Freistich-Vorschlag erzeugt; die tatsaechliche Freistichgeometrie bleibt weiterhin eine Kontur-Funktion und ist noch unter LES-037 zu vervollstaendigen.
- Fix: Das Sperren des Programmkopf-Loeschens funktioniert auch ohne Qt-Elternwidget robust. Statt in einem Headless-/Testpfad beim Oeffnen eines Dialogs fehlzuschlagen, wird der Vorgang nachvollziehbar geloggt.
- Test-Audit: Der kombinierte Gesamtlauf mischt echte Qt- und Stub-Tests im selben Python-Prozess. Die aktuelle globale Import-Umschaltung kann dabei `qtpy`-Rekursionen ausloesen; die Testarten muessen in getrennte, reproduzierbare Laeufe aufgeteilt werden (LES-038).
- Dokumentation: Nullbytes aus `TODO.md` und `CHANGELOG.md` entfernt. Beide Dateien sind wieder normale Textdateien, so dass Suche, Diff und Changelog-Pruefungen sie vollstaendig verarbeiten.
- Audit/Plan (P0, real reproduzierbar): Freistich/Relief am Gewindeende muss am Ende der Gewindelaenge und nicht am Ende der Gesamtkontur verankert werden. Der derzeitige Fehlerpfad kann zu einem LinuxCNC-Fehler `not monotonic` fuehren, weil der letzte Freistich-Schritt nach der Gesamtkontur statt hinter dem Gewindeschritt liegt; der Generator muss hier sofort mit einer klaren Fehlermeldung abbrechen, wenn der verbleibende Platz nicht ausreicht
- Fix (LES-003, P0, schwerwiegend, real bestaetigt - Nutzerhinweis: "es wird keine wirkliche abspahnaufgabe generiert"): Die bewegungsbasierte Ersatzloesung `rough_turn_parallel_x()` (`gcode_roughing.py`, siehe unten fuer den Grund, warum G71/G72 fuer Innenbearbeitung nicht genutzt werden) suchte pro Zustelltiefe nur in einem hauchduennen Fenster (`x_cut +/- 1e-3`) nach Material - bei den meisten X-Baendern einer realen Innenkontur (Anfahrt, Radien, senkrechte Bohrungswand, Uebergaenge) traf dieses Fenster kein Kontursegment ("no cut region"), waehrend ein einzelnes Band zufaellig die GESAMTE lange Bohrungswand in einem einzigen ~33mm-Schnitt erfasste - exakt das gemeldete Symptom. Ersetzt durch eine "Materialreichweite"-Baenderung: pro Zustelltiefe `x_cut` wird jetzt ueberall dort geschnitten, wo die Zielkontur ueber `x_cut` hinausgeht (intern: Kontur-X >= x_cut bis zum Kontur-Maximum; extern: Kontur-X <= x_cut bis zum Kontur-Minimum) - fuer die reale Nutzerkontur ("ausdrehen") ergeben sich jetzt 9 gleichmaessige Einzelzustellungen statt eines Riesenschnitts, die letzten 3 Baender (steiler, kurzer Uebergang zur Bohrungsoeffnung) melden konsistent "no cut region" statt einer irrefuehrenden leeren "X-band"-Kopfzeile (zusaetzlicher Konsistenz-Fix: ein Band, dessen gefundene Intervalle alle entartet/zu flach sind, meldet jetzt ebenfalls "no cut region" statt einer Kopfzeile ohne folgenden Schnitt)
- Verifikation: der generierte G-Code fuer die reale Bohrungskontur (inkl. vorangehendem Bohren-Step) wurde mit dem echten LinuxCNC-Interpreter `rs274` geparst und ausgefuehrt - fehlerfrei, mit der erwarteten Treppenstufen-Bewegungssequenz (`STRAIGHT_TRAVERSE`/`STRAIGHT_FEED` je Zustellung)
- Tests: `tests/test_internal_roughing_uses_g71_cycle.py::test_internal_roughing_with_real_bore_contour_produces_even_stepped_passes` (vormals `..._still_produces_uneven_passes`, dokumentierte bewusst den alten Bug) auf das jetzt korrekte Verhalten umgeschrieben; `tests/test_gcode_motion_regressions.py::test_parallel_x_roughing_merges_touching_wall_and_transition_segments` an den jetzt vollstaendigeren zusammenhaengenden Schnitt angepasst (Z-10.0 statt Z-10.5, da die Baenderung ein kurzes Uebergangssegment korrekt mit erfasst); zwei `test_slicer_extra.py`-Tests zum `allow_undercut`-Verhalten neu geschrieben (das alte schmale Fenster lieferte dort nur hauchduenne ~0.001mm-Splitter, die faelschlich als Testerfolg gewertet wurden); alle geaenderten Tests gegen den alten Code per `git stash` auf `gcode_roughing.py` bestaetigt fehlgeschlagen; Stand `368 passed, 7 skipped`
- Fix (LES-010/LES-011, P1, real bestaetigt - Nutzerhinweis: "Freistich muss funktionieren, sonst kann es zu Problemen beim Gewinde drehen kommen"): DIN-Freistiche wurden bisher nur erzeugt, wenn das Feature am absolut ERSTEN oder LETZTEN Segment der GESAMTEN Kontur lag - ein Freistich mitten in einer laengeren Wellenkontur (z. B. Gewinde-Freistich, gefolgt von weiterem Profil bis zur naechsten Stufe) blieb komplett ohne Geometrie, nur mit einer unauffaelligen Warnung im G-Code-Kopf. `build_contour_variants()` (`contour_logic.py`) verfolgt jetzt waehrend der Haupt-Konturschleife fuer jedes Segment den zugehoerigen Primitiv-Indexbereich (`segment_prim_bounds`) und spleisst die Freistich-Primitive an der GENAU RICHTIGEN Stelle ein (vor dem Segment bei `orientation="start"`, danach bei `orientation="end"`) - die zugrundeliegende Geometrieformel war bereits generisch (haengt nur vom lokalen Segment-Punktpaar ab), die Anfang/Ende-Beschraenkung war eine rein kuenstliche `idx`-Pruefung. Mehrere Freistiche in einer Kontur werden in absteigender Segmentreihenfolge eingefuegt, damit sich Primitiv-Indizes nicht gegenseitig verschieben. Die jetzt veraltete Warnfunktion `_check_din_relief_feature_position()` (`checks.py`) wurde entfernt
- Verifikation: der reale, betroffene G-Code (M30-Aussengewinde-Freistich der Nutzerkontur "abdrehen", mitten in der Kontur) wurde mit dem echten LinuxCNC-Interpreter `rs274` geparst - fehlerfrei, mit der erwarteten Zustellsequenz (radial rein, axial durch die Freistichbreite, radial raus, zurueck auf die Hauptkontur, dann Fortsetzung des Wellenprofils). Aussen- UND Innenfreistich mitten in der Kontur beide bestaetigt
- Tests: `tests/test_din_relief_position_check.py` von "Warnung" auf "erzeugt korrekte Geometrie" umgestellt (Segment-1/mittleres Segment/letztes Segment als Faelle, inkl. Reihenfolge- und Rough-Pfad-Pruefung); `tests/test_relief_and_safety.py::test_validation_warning_comment_sanitizes_parentheses` auf eine andere, weiterhin bestehende Warnung mit Klammern umgestellt (die bisherige Freistich-Warnung existiert nicht mehr); Stand `368 passed, 7 skipped`
- Fix (LES-003, P0, sehr schwerwiegend, empirisch gegen den echten LinuxCNC-Interpreter verifiziert): `G71`/`G72` erzeugen bei Innenkonturen entgegen der Erwartung nur EINEN durchgehenden Schnitt statt echter Treppenstufen-Schrupppaesse. Verifiziert durch direktes Ausfuehren von generiertem G-Code (echte und minimale Testkonturen) mit dem eigenstaendigen LinuxCNC-Interpreter `rs274` gegen den auf dieser Maschine vorhandenen LinuxCNC-Quellcode (`/home/adm1n/linuxcnc-src`, Version 2.10.0~pre1 - identisch zur installierten Version): identisch aufgebaute Aussenkonturen zeigen im selben Test den korrekten, mehrfach zustellenden Treppenstufen-Zyklus (`interp_g7x.cc::pocket()`), Innenkonturen dagegen nur einen einzigen Schnitt von Anfahrpunkt bis Zielkontur - unabhaengig von Konturrichtung, -komplexitaet oder dem verwendeten `stock_x`-Wert. Kein Fehler dieses Generators, sondern eine Einschraenkung von G71/G72 fuer Innenbearbeitung in dieser LinuxCNC-Version. `G71`/`G72` werden in `generate_abspanen_gcode()` (`gcode_roughing.py`) jetzt nur noch fuer Aussenbearbeitung (`external=True`) gewaehlt; Innenbearbeitung nutzt immer die bewegungsbasierte Ersatzloesung, mit neuem, erklaerendem Fallback-Kommentar im generierten Code
- Erkenntnis (noch NICHT behoben, LES-003 bleibt offen): dieser Fix behebt die falsche Zyklus-Wahl, loest aber NICHT den urspruenglich gemeldeten Fehler ("keine wirkliche Abspanaufgabe generiert") vollstaendig - dieser liegt in der bewegungsbasierten Ersatzloesung `rough_turn_parallel_x()` selbst: ihre schmale Fenster-Intersection (`x_cut +/- 1e-3`) findet fuer mehrere X-Baender keinen Treffer ("no cut region"), waehrend ein anderes Band eine lange senkrechte Bohrungswand komplett in einem einzigen ~33mm-Schnitt zusammenfasst statt das Material ueber mehrere Zustellungen zu verteilen. Bewusst NICHT als schnelle Aenderung an sicherheitsrelevanter Fahrweg-Geometrie umgesetzt - braucht eine echte Neuentwicklung der Zustelllogik; als offener Punkt in TODO.md LES-003 dokumentiert, real-verifiziertes Verhalten in `tests/test_internal_roughing_uses_g71_cycle.py` festgehalten
- Tests: `tests/test_internal_roughing_uses_g71_cycle.py` ueberarbeitet - bestaetigt, dass G71/G72 fuer Innenbearbeitung nie mehr gewaehlt werden (Aussenbearbeitung bleibt unveraendert per G71 bestaetigt), dass die Bohrdurchmesser-basierte Materialgrenze (siehe unten) weiterhin korrekt berechnet wird, und dokumentiert per Test den noch unregelmaessigen Zustellverlauf der Ersatzloesung fuer die reale Nutzerkontur; drei bestehende Tests in `test_parting_slice.py`/`test_regression_contracts.py` an das neue (korrekte) Verhalten angepasst; Stand `367 passed, 7 skipped`
- Fix (LES-003, P0, real bestaetigt): Innen-Abspanen mit Vollzylinder-Rohteil (kein `XI` im Programmkopf gesetzt, da die Bohrung erst durch einen vorangehenden Bohren-Step entsteht) rechnete faelschlich mit dem kleinsten X-Wert der ZIELKONTUR selbst als Materialgrenze fuer den `G71`-Zyklus - der Zyklus "startete" damit praktisch schon auf der Fertigkontur, ohne echten Zustellweg zum Abfahren (Symptom: "die Kontur wird nur einmal quasi wie eine Aussenkontur nachgefahren, keine richtige Abspanstrategie"). `gcode_program.py` fuehrt jetzt den zuletzt gebohrten Durchmesser (`op.params["diameter"]` der letzten `DRILL`-Operation vor dem Abspanen-Step) als `_last_drill_diameter` mit; `_resolve_roughing_stock_x()` (`gcode_roughing.py`) nutzt diesen Wert als Materialgrenze, sobald kein plausibles `XI` gesetzt ist und der gebohrte Durchmesser kleiner als die Zielkontur ist - andernfalls bleibt der bisherige sichere Fallback (kleinster Konturwert) erhalten
- Tests: Neue Datei-Ergaenzung in `tests/test_internal_roughing_uses_g71_cycle.py` (zwei neue Faelle: gebohrter Durchmesser wird uebernommen; ein zu grosser gebohrter Durchmesser wird sicher ignoriert) - beide gegen den alten Code bestaetigt; Stand `366 passed, 7 skipped`
- Docs: `TODO.md`, `ROADMAP.md` und `doc/REALTEST_FRAGEN_2026-07-15.md` auf den aktuellen Entwicklungsstand synchronisiert. Die bereits vorhandenen Nutzerantworten zu Realtest 9 (Innen-Zustellrichtung bestaetigt), 11 (Innenstufe/-konus/-radius plausibel, Freistich offen) und 13 (Duplikate erlaubt, aber mit Warnung) werden nicht mehr faelschlich als unbeantwortete Blocker gefuehrt; TODO.md und die Realtest-Datei zeigen anschliessend wieder nur noch aktuell offene Aufgaben (erledigte Erlaeuterungstexte stehen bereits hier im Changelog)
- Planung: LES-013 auf die tatsaechlich noch offene sichere CSS-Aktivierungssequenz reduziert, LES-016 an die entfernte globale Spindelmodus-Combo angepasst und LES-036 als sichtbare, aber noch nicht implementierte P1-Funktion dem Ziel 0.8.0 zugeordnet
- Testprozess: Verbindliche Abnahmeanforderungen fuer G7-Boegen mit `I != 0`, direkten Schlichtweg und G71/G72-Subroutine, Innen-G71 mit beiden Z-Richtungen, gemischte G96/G97-Operationsfolgen sowie Planen-Radius ergaenzt. Neue/geaenderte Skips muessen begruendet werden; sicherheitsrelevante Fahrwege erfordern LinuxCNC-Backplot und dokumentierten Trockenlauf
- Verifikation: reine Dokumentationsaenderung; produktiver Code unveraendert, daher kein neuer Testlauf. Dokumentierter Stand bleibt `364 passed, 7 skipped`
- Fix (P0, schwerwiegend, real bestaetigt durch LinuxCNC-Fehlermeldung): Generierte Programme mit Bogenkontur (G2/G3 aus Kontur-Primitiven) wurden von LinuxCNC mit "Radius to end of arc differs from radius to start" abgelehnt. Ursache: `I` (X-Achsen-Offset zum Bogenzentrum) wurde als rohe Durchmesser-Differenz zum Zentrum berechnet (`cx - cur_x`) - `I` ist in LinuxCNC/Fanuc-Drehmaschinen-Dialekten aber IMMER ein Radiuswert, auch im Durchmessermodus `G7`, in dem die X-Koordinaten selbst Durchmesser sind. Betraf `_emit_finish_primitives()` (Schlichtschnitt/direkter Bogen) und `contour_sub_from_primitives()` (G71/G72-Zyklus-Subroutine) gleichermassen; unbemerkt bisher nur, weil alle Bogen in den Referenzbeispielen zufaellig `I0.000` hatten (Zentrum exakt auf der Startachse) - der Fehler trat erst bei einem Bogen mit echtem X-Versatz zutage (reale Innenkontur des Nutzers)
- Fix: Das Referenzbeispiel `Kontur_Radius_Fase.ngc` (`examples.py`) enthielt selbst einen handgeschriebenen, geometrisch ungueltigen Bogenmittelpunkt (Radius zum Start und zum Ende waren nie gleich, unabhaengig vom obigen Fix) - korrigiert auf einen tatsaechlich gueltigen Mittelpunkt (gleicher Radius zu beiden Endpunkten, per Mittelsenkrechte nachgerechnet)
- Tests: `tests/test_contour_arc_gcode.py` um drei neue Faelle ergaenzt (reale Nutzerkontur, G71-Subroutine-Pfad, Kontrollfall mit dem bereits validen Fillet-Algorithmus) - alle drei bestaetigt gegen den alten Code; `regenerate_all_ngc.py` zeigt den korrigierten `I`-Wert in `Kontur_Radius_Fase.ngc`; Stand `364 passed, 7 skipped`
- Fix (LES-003, P0, schwerwiegend, real bestaetigt): Innen-Abspanen nutzte bei vielen realen Innenkonturen keinen `G71`-Zyklus, sondern eine grobe bewegungsbasierte Ersatzloesung (sichtbar am Kommentar "Fallback-Grund: automatische Entscheidung -> Move-based" und ungleichmaessigen, teils winzigen Zustellungen). Root Cause: `is_monotonic_z_decreasing()` (`gcode_utils.py`) akzeptierte fuer die G71-Eignungspruefung (`parallel_z`-Strategie) nur FALLENDE Z-Werte - anders als bei X (`is_monotonic_x()` prueft beide Richtungen) fehlte eine "Z steigend"-Variante. Innenkonturen werden aber haeufig vom tiefsten Punkt zur Bohrungsoeffnung definiert (Z steigt monoton) - eine geometrisch einwandfreie, aber bisher faelschlich als "nicht zyklustauglich" abgelehnte Richtung. Neue Funktion `is_monotonic_z()` (faellt ODER steigt) ergaenzt und in der G71-Pruefung verwendet
- Tests: Neue Datei `tests/test_internal_roughing_uses_g71_cycle.py` (bestaetigt gegen den alten Code: Import-Fehler, da die neue Funktion vorher nicht existierte; mit dem realen "ausdrehen"-Konturbeispiel des Nutzers manuell nachvollzogen: G71-Aufruf statt 10 ungleichmaessiger Move-based-Passes); Referenz-`.ngc` unveraendert (kein Innen-Abspanen-Beispiel in `examples.py` vorhanden - als neuer TODO-Punkt unter LES-003 vermerkt); Stand `361 passed, 7 skipped`
- Fix (LES-013, P1, real bestaetigt): Innengewinde-Anfahrt fuhr eine sichere Position an und entfernte sich danach nochmal in Z vom Material, bevor eingefahren wurde. Ursache: `gcode_thread.py` routete fuer Innengewinde zusaetzlich ueber das eigene "Sicherheits-Z"-Feld des Gewinde-Steps (`safe_z`), obwohl bereits `XRI` (radial bei JEDER Z-Position sicher) erreicht war - wich `safe_z` vom Gewindestart (`start_z`) ab, entstand ein unnoetiger Zwischenstopp. Anfahrt geht jetzt direkt auf `(XRI, start_z)`
- Tests: `tests/test_thread_internal.py` - bestehenden Test auf das korrigierte Verhalten angepasst, neuen Regressionstest ergaenzt (beide gegen den alten Code bestaetigt); Referenz-`.ngc` unveraendert (kein Fall mit abweichendem `safe_z` darin)
- Fix (real bestaetigt, physikalisch falsche Einheit): `G96` (CSS) sendete unter `S` bisher denselben Zahlenwert wie die Drehzahl (`spindle`, U/min) - `G96` erwartet dort aber die Schnittgeschwindigkeit Vc in m/min. `append_tool_and_spindle()` (`gcode_safety.py`) nutzt jetzt einen eigenen `cutting_speed`-Parameter fuer `G96 S`; ohne gueltigen Wert faellt der Generator sicher auf `G97` mit der Drehzahl zurueck (Warnkommentar), statt eine falsche Zahl als Vc zu senden
- Feature (LES-013, P1): G96/G97 ist jetzt pro Operation waehlbar (Planen, Abspanen, Einstich/Abstich, Gewinde - Bohren bewusst ausgenommen, da sich der Werkzeugdurchmesser beim Bohren nicht aendert). Neue Felder `<prefix>_spindle_mode`/`<prefix>_cutting_speed` je Reiter; kontextabhaengige Anzeige (Drehzahl bei G97, Schnittgeschwindigkeit Vc bei G96) ueber neu gefasste `update_spindle_mode_visibility()`. Die globale `program_spindle_mode`-Combo im Programmkopf entfaellt (gehoerte fachlich nicht dorthin); `program_spindle_max_rpm` bleibt als programmweite CSS-Sicherheitsobergrenze erhalten und ist jetzt immer sichtbar
- Docs (LES-013): "bei CSS sicher mit G97 anfahren, G96 erst an der Bearbeitungsposition aktivieren" bewusst NICHT umgesetzt - erfordert eine verifizierte Vc-zu-Drehzahl-Umrechnung fuer die Anfahrt, die noch keine etablierte Konvention im Projekt hat; als offener Punkt in `TODO.md` LES-013 dokumentiert statt geraten
- Tests: Neue Datei `tests/test_per_operation_spindle_mode_ui.py` (echtes PyQt5: Widget-Erzeugung, Sichtbarkeit, Entfernen der globalen Combo); `tests/test_regression_contracts.py` und `tests/test_advanced_options.py` auf die korrigierte G96-Semantik (Vc statt Drehzahl) angepasst, ein neuer Test fuer den sicheren G97-Fallback ohne Vc ergaenzt; Stand `358 passed, 7 skipped`
- Analyse (kein Codeaenderung, auf Nutzerwunsch zurueckgestellt): Innen-Abspanen faellt bei vielen real vorkommenden Innenkonturen auf eine grobe bewegungsbasierte Ersatzloesung zurueck statt `G71` zu nutzen (sichtbar am Kommentar "Fallback-Grund: automatische Entscheidung -> Move-based"). Root Cause identifiziert: `is_monotonic_z_decreasing()` in `gcode_utils.py` akzeptiert nur FALLENDE Z-Werte fuer die G71-Eignungspruefung (`gcode_roughing.py`, `parallel_z`-Strategie) - anders als bei X existiert keine "Z steigend"-Variante und kein ODER-Fall. Innenkonturen werden aber haeufig vom tiefsten Punkt zur Bohrungsoeffnung definiert (Z steigt monoton) - eine geometrisch einwandfreie, aber bisher abgelehnte Konturrichtung. Vor einer Umsetzung noch zu klaeren: ob die `G71`-Startkoordinate (aktuell `X{stock_x} Z{safe_z}`) bei umgekehrter Konturrichtung weiterhin zum tatsaechlichen ersten Konturpunkt passt; Fix erfordert Backplot-/Trockenlauf-Verifikation vor Praxiseinsatz (siehe LES-003)
- Fix (schwerwiegend, real bestaetigt): Planen mit Kantenform "Fase" schlug im Generator fehl (`Invalid float for 'edge_type': 'chamfer'`) und brach die Programmerzeugung ab. Ursache: `gcode_face.py` las `edge_type` weiterhin ueber `int(float(...))`, obwohl die Combo seit der ID-only-Umstellung ueber `currentData()` die String-IDs `"none"/"chamfer"/"radius"` liefert (wie bereits bei `mode` ueber `resolve_enum_index()` korrekt gehandhabt) - eine der beiden Stellen wurde bei dieser Umstellung nicht mitgezogen. Nutzt jetzt ebenfalls `resolve_enum_index()` (neue `FACE_EDGE_TYPE_INDEX`-Tabelle), inklusive Rueckwaertskompatibilitaet zu alten numerischen Werten (siehe `examples.py`-Referenzprogramm)
- Fix: Kantenform "Radius" beim Planen ist im Generator noch nicht umgesetzt (nur "Fase" erzeugt eine Geometrie) - waere nach obigem Fix sonst still wie "Keine" behandelt worden (Nutzerwahl wortlos ignoriert). Erzeugt jetzt einen klaren Fehler statt eines unbemerkt falschen Ergebnisses (neuer Punkt LES-036 fuer die eigentliche Umsetzung)
- Tests: Neue Datei `tests/test_face_edge_type.py` (bestaetigt gegen den alten Code); Stand `352 passed, 5 skipped`
- Fix (schwerwiegend, real bestaetigt): Nach "Programm laden" fehlte bei einigen Operationen das Werkzeug in der Combo, obwohl beim Programmstart eine Werkzeugtabelle geladen wurde - erst ein manuelles Neuladen der Werkzeugtabelle stellte die Auswahl wieder her. Zwei Ursachen: (1) `handle_load_program()` rief nur `_auto_load_tool_table()` auf, das nach dem ersten (automatischen) Aufruf beim Programmstart dauerhaft gesperrt ist und beim Laden eines Programms nichts mehr tut; die im Speicher bereits vorhandene Werkzeugtabelle (`handler.tools`) wurde dadurch nie erneut auf (ggf. erst jetzt vorhandene) Werkzeug-Combos angewendet. (2) `load_operation_params_to_form()` interpretierte eine nicht in der Combo gefundene Werkzeugnummer (`findData()` ohne Treffer) ueber den generischen Fallback als Positions-Index in der Combo - je nach Combo-Inhalt wurde dadurch ein voellig falsches Werkzeug angezeigt, ohne dass dies auffiel, statt korrekt "kein Werkzeug ausgewaehlt" zu zeigen
- Fix: "Neues Programm" wendet die bereits geladene Werkzeugtabelle jetzt ebenfalls erneut auf alle Werkzeug-Combos an (vorher gar nicht, unabhaengig vom obigen Auto-Load-Zustand)
- Tests: Neue Dateien `tests/test_tool_table_persists_across_program_actions.py` und `tests/test_tool_combo_selection.py` (beide gegen den alten Code bestaetigt, letztere benoetigt echtes PyQt5); Stand `355 passed, 6 skipped`
- Fix (LES-023, P2, real reproduzierbarer Bug): `_insert_loaded_operation()` ("Step laden") und `_handle_add_operation()` frischten den in `params["comment"]` gespeicherten, nummerierten Steptext nur auf, wenn er komplett LEER war. Eine per "Step speichern" gesicherte Datei enthaelt aber ihren zum Speicherzeitpunkt gueltigen, bereits nummerierten Kommentar (z. B. "5. Innenabspanen ..."); wird dieselbe Datei spaeter per "Step laden" an anderer Position eingefuegt, blieb die alte, jetzt falsche Nummer im gespeicherten Kommentar (und damit im generierten `(STEP: ...)`-G-Code-Kommentar) stehen, obwohl die Operationsliste bereits die korrekte neue Nummer anzeigte - derselbe Widerspruch, der frueher schon fuer Verschieben/Loeschen behoben wurde (`renumber_operations()`). Neue Hilfsfunktion `_looks_like_generated_step_comment()` (`ui_flow.py`) erkennt maschinell nummerierte Kommentare (`^\d+\.\s`) und lässt nur diese neu erzeugen; ein bewusst individueller Kommentar ohne Nummern-Vorsilbe bleibt wie bisher unangetastet
- Tests: `tests/test_auto_comment_on_creation.py` um zwei Faelle ergaenzt (bestaetigt gegen den alten Code per manuellem Revert: veraltete Nummer wird jetzt aufgefrischt, Helper-Funktion unterscheidet generiert/individuell korrekt); `regenerate_all_ngc.py` unveraendert (Fix betrifft nur die UI-Einfuegepfade, nicht die Referenzbeispiele); Stand `347 passed, 5 skipped`
- Docs (LES-023): grössere architekturelle Restfrage bewusst offen gelassen und in `TODO.md` praezisiert - die Nummer dauerhaft dem laufenden `params["comment"]` einzuschreiben bleibt fehleranfaellig; die sauberere Loesung (Nummer ausschliesslich beim Programmexport erzeugen) sowie die Frage, ob Konturen in der Step-Nummerierung mitzaehlen sollen, sind eigene, noch offene Entscheidungen
- Docs/Tests (LES-025): Audit aller `_mark_dirty()`/`_mark_program_structure_dirty()`-Aufrufstellen (`ui_visibility.handle_global_change`, `ui_flow.handle_move_up/down`, `_handle_add_operation`, `_handle_delete_operation`, `_handle_param_change`) ergab, dass Sprachumschaltung (expliziter `program_language`-Ausschluss in `handle_global_change`), Step-/Operationswechsel (`load_operation_params_to_form`/`apply_program_header_to_handler` befuellen alle Widgets ausschliesslich unter `blockSignals(True)`) und Programm laden (`handle_load_program` ruft `_clear_dirty_state()` nach dem Laden explizit auf) bereits korrekt NICHT als Aenderung gewertet werden, waehrend echte Struktur-/Parameteraenderungen (Step verschieben/hinzufuegen/loeschen, echte Formulareingabe) korrekt markieren. Diese Pfade waren bisher unentdeckt, aber ungetestet
- Tests: Neue Datei `tests/test_dirty_state_signal_blocking.py` (echtes PyQt5) bestaetigt, dass `load_operation_params_to_form()` beim Befuellen aus gespeicherten Werten keine Widget-Signale ausloest; `tests/test_ui_visibility_guards.py` um drei Faelle fuer `handle_global_change()` ergaenzt (Sprachumschaltung markiert nicht, `_ui_loading` markiert nicht, echte Nutzeraenderung markiert); Stand `345 passed, 5 skipped`
- Fix (LES-021, P2, real gefundener Bug): `lathe_easystep/ui_static.py::load_ui_static_map()` scannte fuer die automatische Sprachumschaltung von "statischen" (nicht per `ui_advanced.py` dynamisch erzeugten) Widgets ausschliesslich die Shell-Datei `lathe_easystep.ui`. Beim fruehreren UI-Refactor (Aufteilung aller acht Bearbeitungsreiter in `lathe_easystep/ui_parts/*.ui`) wurde diese Funktion nicht mitgezogen - seither wurden Labels, Tooltips und Combo-Eintraege aus ALLEN acht Reiter-Dateien (u. a. Bohren, Gewinde, Einstich/Abstich, Kontur, Programm) bei einer Sprachumschaltung nie aktualisiert, obwohl fuer praktisch alle betroffenen Strings (z. B. `label_drill_dwell`, `groove_lage`-Comboeintraege, `btn_slice_view`-Tooltip, diverse `program_*_absolute`-Checkboxen) bereits vollstaendige de/en/es-Uebersetzungen im `.lng`-Katalog vorhanden waren - sie wurden schlicht nie angewendet. `load_ui_static_map()` scannt jetzt zusaetzlich alle Dateien unter `lathe_easystep/ui_parts/*.ui`
- Tests: Neue Datei `tests/test_ui_static_translation_split_tabs.py` (echtes PyQt5): bestaetigt gegen den alten Code per manuellem Revert (`git stash` auf `ui_static.py`), dass betroffene Labels/Tooltips/Combo-Eintraege aus Reiter-Dateien vor dem Fix bei Sprachumschaltung eingefroren blieben, und nach dem Fix korrekt zwischen de/en/es wechseln
- Feature/Fix (LES-016, P1): `program_spindle_max_rpm`/"CSS Max-RPM" (Programm-Reiter) war unabhaengig vom gewaehlten Spindelmodus (`program_spindle_mode`, G97/Festdrehzahl vs. G96/CSS) immer sichtbar - ein fuer G97 irrelevantes Feld stand dauerhaft im Formular. Neue Funktion `update_spindle_mode_visibility()` in `lathe_easystep/ui_visibility.py` blendet Feld und Label jetzt nur bei G96/CSS ein, analog zu den bestehenden Regeln fuer Bohrmodus (Dwell/Peck) und Planen (Kantentyp); an allen bestehenden Aufrufstellen der uebrigen Sichtbarkeitsfunktionen ergaenzt (`handle_global_change`, `_force_visibility_updates`, `_check_unit_change`, `_update_ui_after_widget_found`, `sync_form_to_operation`)
- Tests: `tests/test_ui_visibility_guards.py` um zwei neue Faelle fuer `update_spindle_mode_visibility()` ergaenzt; ausserdem drei bisher ungetestete, bereits bestehende Sichtbarkeitsregeln nachtraeglich abgesichert: Abspanen-Freistich "separat" (`parting_undercut_mode == "separate"` zeigt Werkzeug/Spindel/Vorschub-Felder fuer den Freistich), sowie am Einstich/Abstich-Reiter sowohl `groove_use_tool_width` (Schnittbreite-Feld) als auch der bisher ungetestete "kein Abstich"-Zweig von `groove_process_type`; Stand `342 passed, 3 skipped`
- Docs (LES-016): TODO.md praezisiert - Kontur, Gewinde und Innen/Aussen haben nach Audit aktuell KEINE Sichtbarkeitsregel im Code (kein Testluecken-, sondern ein Funktionsluecken-Befund); as solche als eigene, klar begruendete Punkte belassen statt als "erledigt" markiert
- Docs (LES-026): Verhalten bei doppelten geladenen Steps entschieden - Duplikate werden weiterhin zugelassen, aber (bereits ueber `_check_duplicate_operations()` implementiert und in `tests/test_duplicate_operation_check.py` abgesichert) bei gleichem Operationstyp und identischen Bearbeitungsparametern als Warnung gemeldet, ohne automatisch zu loeschen oder zu veraendern. Realtest-Frage 13 blieb ohne Nutzerantwort; die bereits im Code umgesetzte, in `TODO.md` dokumentierte Empfehlung deckt den Fall ab und wurde in `doc/REALTEST_FRAGEN_2026-07-15.md` entsprechend vermerkt
- Cleanup (LES-017): `slicer.py` (2496 Zeilen, Top-Level-Modul) entfernt. Es duplizierte weite Teile von `gcode_roughing.py`/`gcode_safety.py`/`gcode_utils.py`/`gcode_program.py`, reassignte an seinem Ende (Zeilen ~2410-2495) aber fast alle eigenen Top-Level-Namen auf die echten Funktionen aus diesen Modulen zurueck - der grosse Teil des Datei-Inhalts war damit toter, nie ausgefuehrter Code. Produktivcode hat `slicer.py` nie importiert; genutzt wurde es ausschliesslich noch von sechs Testdateien und dem alten `regenerate_ngc.py`. `regenerate_ngc.py` (einzelnes Referenzprogramm, importierte aus `slicer.py`) war bereits durch `regenerate_all_ngc.py` (alle sechs Referenzprogramme, importiert aus den echten `lathe_easystep`-Modulen) ersetzt und wurde ebenfalls entfernt
- Tests: `tests/test_abspanen_finish_allow.py`, `tests/test_contour_arc_gcode.py`, `tests/test_drill_modes.py`, `tests/test_thread_internal.py`, `tests/test_slicer.py` und `tests/test_slicer_extra.py` importieren jetzt aus den echten Modulen (`lathe_easystep.gcode_roughing`, `.gcode_program`, `.gcode_drill`, `.contour_logic`, `.model`) statt aus `slicer.py`; `regenerate_all_ngc.py` erzeugt nach der Entfernung weiterhin byte-identische Referenzdateien (`git diff` auf `ngc/*.ngc` leer)
- Cleanup (LES-029): `lathe_easystep/i18n/de.json`/`en.json` waren vom aktiven `.lng`-Loader (`translations.py`, laedt ausschliesslich aus `languages/*.lng`) nie verwendet worden. Nach Audit (keine Referenzen in Python-Code, Tests, `.ui`-Dateien oder Packaging-Konfiguration) entfernt; `DEV.md` entsprechend aktualisiert
- Fix/Feature (LES-002, P0): Ein Schruppstep (`mode=rough` oder `rough_finish`), der keinen einzigen echten Schnittbefehl erzeugt (fehlende Bearbeitungsrichtung, nicht zyklustaugliche Kontur ohne Schnittbereich, o. ae.), erzeugte bisher bestenfalls eine Kommentar-/Warnzeile im G-Code - ein leicht zu uebersehendes, scheinbar gueltiges, aber leeres Programm. `generate_abspanen_gcode()` bricht jetzt mit `ValueError` ab, sobald fuer den Schrupp-Anteil kein `G1`/`G71`/`G72` erzeugt wurde. Die alte, jetzt unerreichbare Warnzeile fuer den Fall "keine Strategie gewaehlt" wurde entfernt (der neue Fehler deckt diesen Fall vollstaendig ab, inklusive `mode=rough_finish`, das vorher gar keine Meldung bekam)
- Tests: Neue Datei `tests/test_empty_roughing_aborts.py`; mehrere bestehende Tests, die versehentlich ohne `slice_strategy` schruppten (aber etwas anderes pruefen wollten), um eine gueltige Strategie ergaenzt; Stand `336 passed, 3 skipped`
- Docs: `TODO.md`, `ROADMAP.md`, `README.md` und `DEV.md` auf den Stand 24.07.2026 synchronisiert: erledigte ZRA/ZRI- und G76-Pruefpunkte aus dem offenen Plan entfernt, UI-Teilung und vollstaendige de/en/es-Kataloge dokumentiert, `slicer.py`-Bereinigung und alle verbleibenden Sicherheits-, Kontur-, UI-, Preview-, Werkzeug- und Architekturaufgaben eindeutig priorisiert
- Docs: `doc/REALTEST_FRAGEN_2026-07-15.md` ausgewertet (Nutzerantworten zu 15 Realtest-Fragen) und `TODO.md` entsprechend bereinigt:
  - Erledigt/durch Antwort geschlossen: G53-Werkzeugwechsel (F1: "funktioniert"), Bewegung nach M6 (F2: "nein, alles korrekt"), Tooltips (F4: "scheinen alle zu funktionieren"), Sprachumschaltung (F5: "gerade alle ok"), Vorschau/Slice/Frontview (F6: "sieht alles ok aus" - nach den Absturz-/Freeze-Fixes dieser Session), G76-Masssystem (F12: "generierte Werte scheinen zu passen")
  - `safe_z`/`ZRA`/`ZRI` absolut vs. relativ bei ABSPANEN (F10): Nutzer bestaetigt, dass die Regel in der Praxis beachtet wird und Abweichungen bereits beim Generieren gemeldet werden - aus der bereits dokumentierten "Blockiert"-Liste entfernt, da ohne konkretes Gegenbeispiel kein Aenderungsbedarf ersichtlich ist
  - Durch Antwort ausgeloeste Fixes/Features: siehe die eigenen Eintraege weiter unten (erster Werkzeugwechsel, Bohr-Anfahrt, drittes Combo-Item "Schruppen + Schlichten", Innen-Schruppen-Bug)
  - Weiterhin offen (unbeantwortet): Startzeit/Reaktionszeit (F7), Materialmodell-Richtung fuer Innen-Schruppen Parallel-Z (F9), Innenkonturformen-Verifikation (F11), Verhalten bei doppelten Operationen beim Step-Laden (F13)
- Fix (schwerwiegend, real bestaetigt via Realtest-Antwort Q15: "innenabspanen ... das ist Blödsinn, was da generiert wird"): `rough_turn_parallel_x()` (Move-based-Fallback fuer die Strategie "parallel_z") baute pro X-Band ungemergte Z-Intervalle aus allen schneidenden Kontursegmenten. Beruehren/ueberlappen sich zwei Segmente am selben X (z. B. eine senkrechte Bohrungswand, die exakt dort endet, wo eine Fase/ein Radius beginnt - genau die reale "ausdrehen"-Innenkontur), entstanden fuer dasselbe Band mehrere sich ueberschneidende Schnitt-Intervalle: das Werkzeug fuhr denselben Tiefenbereich mehrfach anstatt in einem zusammenhaengenden Zug an (sichtbar als naeherungsweise identische, aber leicht abweichende Z-Werte in aufeinanderfolgenden Zeilen). Das Pendant `rough_turn_parallel_z()` mergt seine Intervalle bereits ueber die vorhandene `merge_intervals()`-Funktion - der Aufruf fehlte hier
- Tests: Neue Regression `test_parallel_x_roughing_merges_touching_wall_and_transition_segments` (bestaetigt gegen den alten Code per manuellem Revert); Stand `331 passed, 3 skipped`
- Feature (Realtest-Antwort Q14: "drittes Combo-Item Schruppen + Schlichten? - ja"): `parting_mode` (Abspanen-Reiter) hatte in `lathe_easystep/ui_parts/tabParting.ui` nur zwei `<item>`-Eintraege (Schruppen/Schlichten), obwohl Registry/Uebersetzungen (`ui_registry.py`, alle drei `.lng`-Dateien) den dritten Wert "rough_finish" bereits vorbereitet hatten - im echten Panel war die kombinierte Option nicht auswaehlbar. Drittes `<item>` "Schruppen + Schlichten" ergaenzt, analog zum bereits vollstaendigen `face_mode`
- Fix: `PARTING_MODE_INDEX` in `gcode_roughing.py` kannte nur `"rough"`/`"finish"`, nicht `"rough_finish"` - `resolve_enum_index()` waere fuer die String-ID des neuen dritten Combo-Items auf den Default (0/Schruppen) zurueckgefallen und haette den Schlichtschnitt stillschweigend uebersprungen. Ergaenzt (analog zu `FACE_MODE_INDEX`, das den Eintrag bereits korrekt hatte)
- Tests: Neue Datei-Ergaenzungen `tests/test_finish_mode_never_reroughs.py` (String-ID-Aufloesung) und `tests/test_split_ui_loader.py` (echtes PyQt5, drei sichtbare Combo-Eintraege); Stand `330 passed, 3 skipped`
- Fix (real bestaetigt via Realtest-Antwort Q8: "Anfahrt sollte so sein wie die Abfahrt, Abfahrt ist gut"): Bohren nutzte eine eigene, bespoke Anfahrlogik (`emit_drill_approach` in `gcode_drill.py`) statt des projektweiten `emit_approach()`-Helfers - mit teils redundanten Bewegungen (generische sichere Position, danach nochmal separat auf Startpunkt) und einer anderen Struktur als die bereits als korrekt bestaetigte Rueckzugssequenz. Bohren verwendet jetzt `emit_approach()`, denselben Helfer wie Abspanen/Einstich
- Tests: `test_drill_approach_uses_shared_safety_helper_like_other_operations` (ersetzt einen Test, der die alte bespoke Struktur festschrieb); Referenzdatei `ngc/Bohren.ngc` angepasst; Stand `329 passed, 3 skipped`
- Fix (schwerwiegend, real bestaetigt via Realtest-Antwort): Der ERSTE Werkzeugwechsel eines Programms fuhr nicht zum definierten Werkzeugwechselpunkt. Ursache: `generate_program_gcode()` ruft `gcode_for_operation()` zuerst nur zur Vorab-Validierung auf, mutiert dabei aber denselben `settings`-Dict (u. a. `_current_tool` ueber `append_tool_and_spindle()`). Verwenden alle Operationen dasselbe Werkzeug, stand `_current_tool` nach der Validierung bereits auf dem ERSTEN echten Werkzeug - der Vergleich "tool_num != last_tool" im echten Erzeugungsdurchlauf wurde dadurch faelschlich `False`, und der Werkzeugwechselpunkt wurde beim ersten (und einzigen) Wechsel nicht angefahren. Die Werkzeug-/Positions-Laufzeittracker (`_current_tool`, `_is_at_safe`, `_active_retract_mode`) werden nach der Validierungsschleife jetzt zurueckgesetzt; die `needs_step_*_pause_sub`-Flags bleiben davon unberuehrt erhalten (werden fuer die Subroutinen-Definitionen gebraucht)
- Tests: Neue Regression `test_first_toolchange_moves_to_toolchange_point_when_only_one_tool_used` (bestehender Test mit zwei unterschiedlichen Werkzeugen uebersah den Fehler zufaellig); mehrere Tests mit unspezifischen `in lines`/`.index()`-Pruefungen auf Retract-Zeilen praezisiert, die durch die jetzt korrekt erscheinende erste Werkzeugwechsel-Sequenz auf denselben Text (z. B. `G0 X45.000 Z5.000`) trafen; alle sechs Referenzdateien in `ngc/` an die jetzt korrekte erste Werkzeugwechsel-Sequenz angepasst; Stand `329 passed, 3 skipped`
- UI: Vorschau-Dock kompakter aufgebaut; Seitenvorschau und Schnittansicht liegen jetzt nebeneinander und belegen deutlich weniger Hoehe im rechten Bereich
- UI: Fehlende Tooltips in `Abspanen`, `Gewinde` und `Einstich/Abstich` ueber das Sprachsystem fuer `de`, `en` und `es` vervollstaendigt
- UI-Refactor: `lathe_easystep.ui` ist jetzt die Start-Shell; die Reiter `Program`, `Face`, `Contour`, `Parting`, `Thread`, `Groove`, `Drill` und `Keyway` liegen als einzelne Dateien unter `lathe_easystep/ui_parts/*.ui` und werden zur Laufzeit ueber `lathe_easystep/ui_split.py` in die bestehenden Tab-Container geladen
- Tests: Zusätzliche UI-Sichtbarkeits-Regressionen für Rohteilform (`tube`/`polygon`) und Rueckzugsmodus (`simple`/`all`) ergaenzt; offene Sichtbarkeitsarbeit in der `TODO` auf die fachlichen Restbereiche Kontur/Abspanen/Gewinde reduziert
- Drill: Die Bohr-Einfahrt nutzt jetzt eine eigene sichere Sequenz statt des generischen Diagonal-Endzugs von `emit_approach()`. Aus der Safe-Position wird erst auf die Bohr-Rueckzugsebene in `Z`, dann auf die Bohr-Achse in `X` gefahren; das spiegelt die bereits als korrekt bestaetigte Abfahrt sauber
- Fix: Validierungs- und Sicherheitswarnungen werden vor der Ausgabe als LinuxCNC-Kommentar jetzt konsequent geklammert-sicher bereinigt; Texte wie `Segment 3 (z. B. ...)` erzeugen damit keinen `nested comment`-Fehler mehr im generierten `.ngc`
- Toolchange: Der erste echte Werkzeugwechsel im Programm nutzt jetzt denselben definierten Werkzeugwechselpfad wie Folgewechsel; vor jedem expliziten `T.. M6` wird der konfigurierte Wechselpunkt sauber angefahren
- UI: `rough_finish` ist im Abspanen-/Einstich-Modus jetzt auch im Panel als drittes Strategie-Combo-Item sichtbar und an die bestehende Sichtbarkeitslogik angebunden
- Safety: `XRI` ist jetzt fuer Innenbearbeitung eine harte Sicherheitsgrenze. Innengewinde, Inneneinstich und Innen-Abspanen werden abgewiesen, sobald irgendein angeforderter X-Wert kleiner als `XRI` waere
- Safety: Innen-Gewindeanfahrt haelt `XRI` jetzt bis zur Start-Z-Position ein; der Generator faehrt erst dort auf den eigentlichen Gewinde-Anfahrdurchmesser
- Safety: Werkzeugwechsel rueckziehen vor `M6` immer ueber die aeusseren Safe-Planes; die naechste Innenoperation schaltet den Rueckzug nicht mehr schon vor dem Wechsel auf `XRI/ZRI` um
- Motion: Schlichtwege fuer Konturen mit Radius erhalten Boegen jetzt im expliziten Finish-Pfad als `G2/G3` statt sie zu `G1`-Fasen zu linearisieren
- Motion: Groove-/Einstich-Anfahrten nutzen fuer sichere Anfahrt jetzt die hinterlegten Rueckzugsebenen statt direkt vor der Bearbeitungsposition am Material zu starten
- Motion: Innen-Schruppen mit `parallel_z` verwendet `XRI` nicht mehr als Ersatz fuer den Schrupp-Startstock; bei fehlendem/untauglichem `XI` wird der Kontur-Mindestdurchmesser als Start fuer reale Innen-Schruppbahnen verwendet
- Workflow: neue Datei `doc/REALTEST_FRAGEN_2026-07-15.md` als ausfuellbare Sammelstelle fuer reale LinuxCNC-/QtVCP-Tests und offene Nutzerentscheidungen
- Repo: `.cps`-Postprozessor-Dateien sind jetzt in `.gitignore`, damit lokale LinuxCNC-/Inventor-Postprozessoren nicht versehentlich committed werden
- Docs: README und DEV-Dokumentation um die harte `XRI`-Sicherheitsregel und den neuen Realtest-Workflow ergaenzt
- Fix: Die Schnittansicht (Frontview) wirkte nach dem Ziehen an der Schnittkante eingefroren - die dargestellte Z-Position aktualisierte sich visuell nicht. Ursache: `_ensure_slice_z_matches_operation()` wird bei JEDEM `_refresh_preview()`-Durchlauf aufgerufen (nicht nur beim Wechsel des ausgewaehlten Steps) und setzte `slice_z` fuer jede Nicht-Nut-Operation bedingungslos auf den vorgeschlagenen Standardwert zurueck. Jeder beliebige Refresh waehrend des Ziehens (Tab-Wechsel, Parameteraenderung, periodische Aktualisierung) machte die manuelle Positionierung dadurch unsichtbar rueckgaengig, noch bevor sie sichtbar wurde. Der Vorschlag greift jetzt nur noch, wenn sich die aktive Operation seit dem letzten Aufruf tatsaechlich geaendert hat
- Tests: Neue Datei `tests/test_slice_view_z_not_reset_on_refresh.py`; bestaetigt gegen den alten Code (verifiziert per `git stash`); Stand `309 passed, 2 skipped`
- Fix (kritisch, Absturz): `lathe_easystep/preview_widget.py` (bei der Extraktion aus dem Handler in einer frueheren Session ausgelagert) verwendete vier Namen ohne Import: `is_internal_side` (Aussen-/Innenerkennung fuer die Schnittansicht) sowie `build_keyway_slot_angles`/`front_view_polar_to_cartesian`/`keyway_slice_bounds` (Nutkontur in der Frontansicht). Sobald die Schnittansicht (Slice-/Frontview-Toggle) tatsaechlich gemalt wurde, stuerzte PyQt5 mit `NameError` beim `paintEvent` hart ab (Panel-Absturz, exakt wie gemeldet). Alle vier Imports ergaenzt (aus `gcode_utils.py` bzw. `preview_geometry.py`, wo die Funktionen tatsaechlich definiert sind)
- Tests: Neue Datei `tests/test_preview_widget_paint_no_crash.py` (echtes PyQt5, da der qtpy-Stub `paintEvent()` nie wirklich aufruft und den fehlenden Import nicht gefunden haette) - malt die Frontansicht fuer Aussen-/Innen-Abspanen und Nut und bestaetigt gegen den alten Code einen echten Prozessabsturz (`Fatal Python error: Aborted`), gegen den neuen Code sauberes Bestehen. Ausfuehren mit `/usr/bin/python3 -m pytest tests/test_preview_widget_paint_no_crash.py`
- Docs: `TODO.md` erneut bereinigt und gestrafft; erledigter `currentText()`-Audit entfernt, Sichtbarkeits-Tests auf den tatsaechlich noch offenen Rest reduziert und die strikte UI-/Sprachtrennung als eigener Architekturblock explizit dokumentiert
- Tests: Neue Datei `tests/test_ui_visibility_guards.py` ergaenzt Regressionen fuer Sichtbarkeitslogik in Planen, Bohren und Subspindel, fuer `chuck_size_mm()` sowie einen Guard, der verbleibende `currentText()`-Verwendungen auf bewusst auditierten Fallback-/Debug-Stellen einfriert
- Tests: Test-Infrastruktur fuer Real-Qt- und Stub-basierte Laeufe entkoppelt (`tests/conftest.py`, `tests/test_slice_strategy_ui_roundtrip.py`, `tests/test_dirty_and_messages.py`), damit echte PyQt5-Tests die uebrige Suite nicht mehr durch entfernte `qtpy.QtCore`/`qtpy.QtWidgets`-Aliase destabilisieren
- Verifikation: Neue und betroffene fokussierte Testbloecke erfolgreich geprueft:
  - `tests/test_ui_visibility_guards.py`
  - `tests/test_parting_visibility.py`
  - `tests/test_dirty_and_messages.py`
  - `tests/test_slice_strategy_ui_roundtrip.py`
  - `tests/test_step_path_persistence.py`
- Refactor: Gemeinsame UI-Helfer fuer Sprachcode, Uebersetzung, ComboBox-Befuellen und Tab-Bezeichnungen in `lathe_easystep/ui_helpers.py` zentralisiert
- Refactor: Doppelte Safe-X-Berechnung fuer Innen-Abspanen und Innengewinde nach `gcode_utils.py` verschoben
- Refactor: Generische `get_param_int()`-/`get_param_float()`-Lookups aus dem Groove-Generator nach `gcode_utils.py` verschoben; Werkzeugnummern verwenden dieselbe zentrale Konvertierung
- Cleanup: Ungenutztes und durch fehlende interne Module nicht importierbares Alt-Paket `lathe_easystep/contour/` entfernt; aktive Konturpfade ueber `contour_logic.py`/`contour_features.py` bleiben unveraendert
- Verifikation: Python-Syntaxpruefung, Diff-Pruefung und fokussierte dependency-freie Tests der zentralisierten G-Code-Helfer erfolgreich; vollstaendiger Testlauf lokal wegen fehlendem `pytest`/`qtpy` nicht moeglich
- Architektur: Strikte Trennung von UI und Sprache eingefuehrt: sichtbare Texte werden nicht mehr aus Python-/UI-Fallbacks hergeleitet, fehlende Eintraege zeigen den jeweiligen Schluessel/ID
- Architektur: Tooltip-Fallback-Ableitung aus Label-/Widget-Texten deaktiviert; Tooltips kommen nur noch aus expliziten Uebersetzungskeys
- UI-Logik: Kritische Auswahl-/Sichtbarkeitslogik auf technische IDs (`currentData`) umgestellt statt auf lokalisierte Anzeige-Texte (`currentText`)
- Kontur-Editor: Segment-Combos (Kante, Bogen-Seite, Feature, Innen/Aussen, Start/Ende) nutzen nun stabile interne IDs in `itemData`
- Programmkopf: Relevante Combo-Werte werden beim Sammeln/Laden als technische Werte gespeichert/verarbeitet (sprachunabhaengig)
- Tests: Sprach-/Tooltip-Regressionen an den strikten ID-only Modus angepasst; fokussierte Regressionen laufen gruen (`22 passed`)
- Safety: Innen-Gewinde und Innen-Abspanen erzwingen jetzt ein plausibles `XRI`; ohne gueltige Innen-Rueckzugsebene bricht die G-Code-Erzeugung mit einer klaren Fehlermeldung ab
- Safety: Innen-Gewinde und Innen-Abspanen verwenden jetzt op-spezifische sichere Anfahr- und Rueckzugsebenen ueber `XRI/ZRI` statt pauschal `XRA/ZRA`
- Abspanen: Interner `G71`-Startdurchmesser wird jetzt aus Kontur und Innen-Rueckzug fachlich korrekt abgeleitet; unplausible `X0/Z0`-Zyklusstarts fuer Innenkonturen werden nicht mehr erzeugt
- Abspanen: Innen-Schlichtschnitt mit aktiver Schneidenradiuskorrektur bekommt jetzt einen echten Einfahrweg, damit LinuxCNC keine Fehler wegen zu kurzer Kompensations-Einfahrt meldet
- Tests: Regressionen fuer `XRI`-Pflicht, Innen-Anfahrlogik, `M30`-Programmende und Subroutinen-Reihenfolge erweitert
- Tests: Referenz- und Regressionsstand auf `202 passed` angehoben
- Gewinde: Gewinde-Reiter um `Gewindestart Z` sowie separate Rechts-/Linksgewinde-Auswahl erweitert; Werte laufen jetzt durch UI, Save/Load, Vorschau und Generator
- Gewinde: Vorschau und G-Code unterscheiden jetzt alle vier Kombinationen aus Innen/Aussen und Rechts/Links; Start-Z und Gewinderichtung steuern Anfahrpunkt, Endpunkt und Z-Laufrichtung
- Gewinde: Zusaetzliche Plausibilitaetswarnungen fuer identische Start-/Endpunkte sowie Start-/Endlagen ausserhalb des Werkstueck-Z-Bereichs
- Kontur: Step-Liste benennt Konturen jetzt fachlich neutral als `Kontur: <Name>`
- UI: Tooltip-Anzeige um einen erzwungenen Hover-/ToolTip-Relay erweitert, damit Tooltips auch im eingebetteten QtVCP-Pfad robuster erscheinen
- Tests: Gewinde-Regressionen fuer Rechts-/Linksgewinde, Innen-/Aussengewinde und variable Start-Z-Positionen ergaenzt
- G-Code: Hauptprogrammfluss wird jetzt vor den O-Subroutinen ausgegeben, damit LinuxCNC nicht mehr in die Einstich-/Abstich-Bibliothek hineinfaellt und Groove-Zyklen nicht endlos neu starten
- Toolchange: Werkzeugwechsel- und Parkposition haben jetzt eine explizite Auswahl fuer `Werkstueckkoordinaten` oder `Maschinenkoordinaten (G53)` statt der fachlich missverstaendlichen Altlogik ueber `absolut / inkrementell`
- Toolchange: Legacy-Dateien mit gemischter XT/ZT-Logik bleiben kompatibel; neue Programme erzeugen koordinatensystemsauberen Werkzeugwechsel- und Park-G-Code
- Toolchange: Regressionspruefung gegen reales Testprogramm `Test.ngc` nachgezogen; der Generator emittiert nach `T.. M6` kein zusaetzliches `G0 X0 Z0`, der anschliessende manuelle Wechselpfad kommt aus der LinuxCNC-Konfiguration (`TOOL_CHANGE_MODE = MANUAL`, `hal_manualtoolchange`)
- UI: Tooltips werden jetzt tief auf Ziel-Widget, Label, Editor und Combo-View propagiert und fuer Embedded-/Standalone-Betrieb explizit aktiviert
- Validierung: Fehlermeldungs-Mapping ist jetzt pro Operationstyp gehaertet und verweist nur noch auf tatsaechlich vorhandene UI-Felder
- Presets: Gewinde- und DIN-Freistich-Presets in `lathe_easystep/presets/` zentralisiert und fuer metrische Groessen bis `M30` erweitert
- Gewinde: DIN-Freistich-Helfer und Gewindevorschlaege greifen jetzt ueber zentrale Preset-Helper zu statt auf verstreute Tabellen
- Tests: Neue Regressionen fuer Groove-Subroutine-Reihenfolge, explizite Toolchange-/Park-Koordinatensysteme, Keyway-Validierung und generatorseitig fehlende `X0/Z0`-Zusatzfahrt
- Workflow: Sichtbarer Dirty-State fuer Programm und Steps eingebaut; `Aenderungen speichern` markiert offene Aenderungen jetzt direkt im UI
- Workflow: Reiter- und Stepwechsel warnen jetzt bei ungespeicherten Aenderungen und speichern weiterhin keine Dateien automatisch
- UI: Groove-Reiter um klare Betriebsart `Einstich` / `Abstich` erweitert; partingspezifische Reduktionsfelder werden kontextabhaengig ein-/ausgeblendet
- UI: Vorschau wird beim finalen Layout jetzt ausserhalb des Scrollbereichs angedockt und bleibt als fester Kontrollbereich sichtbar
- UI: Zentrale Tooltips fuer Rueckzugsebenen, Futtergrenzen, CSS/G96, Parklogik, Freistich-/Hinterschnitt-Optionen und Groove/Abstich komplettiert
- UX: Generator- und Speichermeldungen werden fuer Anwender jetzt auf Reiter/Feld-Ebene benutzerverstaendlicher formatiert
- Uebersetzungen: Restliche Mischtexte in Drill-/Groove-/Advanced-Widgets und relevanten Groove-Makrokommentaren bereinigt
- Kontur: Datenmodell fuer Konturfeatures um DIN-Freistich/Hinterschnitt erweitert; Segment-Features koennen jetzt als Teil der Konturgeometrie beschrieben werden
- Kontur: Neue DIN-Freistich-Tabelle `M3` bis `M30` mit Aussen-/Innen-Varianten sowie Breite, Tiefe und Uebergangsform angelegt
- Kontur: Generator leitet jetzt drei Geometrievarianten aus derselben Kontur ab: Fertigkontur, Schruppkontur ohne Hinterschnitt und Feature-Teilkontur
- Abspanen: Bearbeitungsmodi fuer Hinterschnitt/Freistich umgesetzt (`ignore`, `finish_only`, `separate`, `full`)
- Abspanen: Generator dokumentiert Strategie, Ausgabe-Praeferenz, Aufmass und Hinterschnitt-Modus jetzt explizit im G-Code
- Abspanen: Fallback-Gruende fuer Move-based Roughing werden systematisch ausgegeben statt nur punktuell
- Abspanen: Expertenoption fuer Ausgabeart (`auto`, Zyklus bevorzugen, ausgeschriebener Code bevorzugen) in der Generatorlogik verdrahtet
- UI: Expertenoptionen fuer Hinterschnitt-Modus, Ausgabe-Praeferenz, CSS/G97, Parklogik und optionale Stops in das Panel eingebunden
- UI: Kontursegment-Editor um DIN-Freistich-Felder fuer Feature, Gewindegroesse, Norm, Innen/Aussen und Start/Ende erweitert
- Workflow: Save/Load und Formularbindung fuer die neuen Experten- und Konturfeature-Parameter vervollstaendigt
- Safety: Vor jedem `T.. M6` wird jetzt `M5` erzwungen; Werkzeugwechsel fahren weiterhin mit Sicherheitsrueckzug und Toolchange-Position
- Safety: Anfahrt und Rueckzug pruefen jetzt Startpunkt im Rohteil, Startpunkt in der Futter-Sperrzone und kritische Rueckzugsebenen und markieren diese als Warnung
- Safety: Plausibilitaetswarnungen fuer `XT/ZT`, `XRA/XRI`, `ZRA/ZRI` ausserhalb sinnvoller Rohteil-/Maschinenbereiche ergaenzt
- Safety: Optionale Haltepunkte vor separatem Hinterschnitt sowie CSS/Festdrehzahl-Ausgabe (`G96`/`G97`) mit Max-RPM-Fallback eingebaut
- Workflow: Endparklogik um konfigurierbare Parkposition und sequentielle Endbewegung erweitert
- Validierung: Zusaetzliche Pruefungen fuer `G76`, DIN-Freistich-Parameter, separates Hinterschnitt-Schruppen und Werkzeugbreite eingebaut
- Validierung: Werkzeug-/Operations-Plausibilitaet um Innen/Aussen-Hinweise und Spezialwerkzeug-Checks erweitert
- Gewinde: DIN-Freistich kann fuer Gewinde jetzt als Vorschlag kommentiert werden, ohne blind erzeugt zu werden
- Preview: Roughing- und Freistich-Geometrie werden fuer `ABSPANEN` unterscheidbar ueberlagert; Warnungen koennen im Preview eingeblendet werden
- Tests: Neue Regressionen fuer Freistich-Varianten, Sicherheitswarnungen und `M5` vor jedem Werkzeugwechsel hinzugefuegt
- Tests: Save/Load, CSS/Parklogik, Gewinde-Freistich-Vorschlag und optionale Stops zusaetzlich abgesichert
- Tests: Dirty-State, Groove/Abstich-Sichtbarkeit, benutzerfreundliche Fehlermeldungen und Snapshot-Normalisierung zusaetzlich abgesichert
- Tests: Referenzprogramme regeneriert; aktueller Stand mit `202 passed` verifiziert
- Safety: Einstich-/Abstich-Zyklus (`o220` in `gcode_groove.py`) bricht bei ungueltigen Parametern (Werkzeugbreite/Nutbreite/Zustellung <= 0, Werkzeug breiter als Nut) jetzt ueber echtes `M99` ab statt wirkungslose Kommentare zu haben; Schrupp-Schleife hat eine harte Iterationsobergrenze gegen Endlosschleifen bei Nullbewegung
- Safety: Innen-Nut-Einstich (`GROOVE lage=1`) verwendet jetzt ebenfalls `XRI`/`ZRI` statt `XRA`/`ZRA` fuer Anfahrt/Rueckzug, analog zu Innengewinde und Innen-Abspanen
- Safety: Sichere Z-Rueckzugsebene bei Innenbearbeitung korrigiert - `gcode_safety._safe_axis_value()` nutzte faelschlich `ZI` (hinteres Endmass, nahe Futter) statt `ZA` (vorderes, zugaengliches Mass) als Bezug; dadurch fuhr der Rueckzug teils mitten ins bzw. durchs Rohteil (der Generator warnte selbst davor, fuhr aber trotzdem)
- Fix: G-Code-Kommentare werden nicht mehr zeilenuebergreifend erzeugt (LinuxCNC schliesst `(...)`-Kommentare nicht ueber Zeilenumbrueche hinweg)
- Fix: Fuenf `QFormLayout`-Zellenkollisionen (Face-/Parting-/Thread-/Groove-/Drill-Reiter: Werkzeug-Combo + Tool-Preview-Bild in ungueltiger dritter Spalte, von Qt als `SpanningRole` fehlinterpretiert) behoben; mit echtem PyQt5 warnungsfrei verifiziert
- Fix: Systemisches String- vs. Int-Problem bei ID-only-Combo-Werten (Gewinderichtung/-hand, Innen/Aussen-Seite, Bohr-/Abspan-/Planmodus) behoben - fuehrte teils zu Abstuerzen, teils zu stillem Fehlverhalten (z. B. Innengewinde wurde als Aussengewinde erzeugt, G82/G83/G73/G84-Bohrzyklen liefen heimlich als G81); neue Helfer `is_internal_side()`/`is_left_hand()`/`resolve_enum_index()` in `gcode_utils.py`
- Fix: Innenkontur-Vorschau leerte sich faelschlich bei Konturelementen, die nur eine Achse setzen (`x_empty`/`z_empty`-Markierung wurde von der Validierung ignoriert)
- Fix: `setup_param_maps()` baute die komplette Widget-Zuordnung bisher bei jedem Step-/Tabwechsel und jeder Feldaenderung komplett neu auf (100+ Widget-Suchen ohne Zwischenspeicherung); jetzt einmalig und selbstheilend gecacht
- Fix: Fehlermeldung bei fehlgeschlagener G-Code-Erzeugung zeigt jetzt zuverlaessig Reiter und Feldname; das Panel springt bei einem Generierungsfehler automatisch zum betroffenen Step/Reiter und hebt das Feld farblich hervor
- Fix: Preset-Button im Gewinde-Reiter kollidierte im Formular-Grid mit der Standard-Auswahl, jetzt eigene Zeile
- Fix: Zahlreiche fehlende Uebersetzungsschluessel ergaenzt (Gewinde-Presets, Groove-Diagramm-Labels, Kontur-Laufzeitwerte, Drill-/Parting-Beschreibung); `ui_static.py` verlangt keinen Schluessel mehr fuer leere Platzhalter-Labels (z. B. Diagramm-Vorschaubilder)
- Feature: Aktivierbarer Debug-Modus (`LATHEEASYSTEP_DEBUG=1` vor dem Start setzen) fuer ausfuehrliche Laufzeit-Logs: Feldaenderungen, Step-/Tabwechsel inkl. Zeitmessung, Vorschau-Refresh inkl. Zeitmessung, Dirty-State-Aenderungen, G-Code-Generierung inkl. Zeitmessung, Fehler-Navigation
- Feature: Tooltips fuer alle Bedienelemente in Planen, Bohren, Kontur und Keilnut ergaenzt (vorher dort keine registriert) in Deutsch/Englisch/Spanisch
- Validierung: DIN-Freistich-Presets bekommen jetzt Plausibilitaetspruefungen wie Gewinde-Presets (`validate_din_relief_preset_data()`)
- Tests: umfangreiche neue Regressionen fuer alle oben genannten Fixes, u. a. mit echtem PyQt5 (Systempaket `python3-pyqt5`) statt nur Test-Stubs verifiziert; Stand `260 passed`
- Refactor: `lathe_easystep_handler.py` deutlich verkleinert (7501 -> 4965 Zeilen), damit der Handler wieder naeher an "nur Kleber zwischen den Modulen" ist:
  - Ueber 1100 Zeilen totes, laengst durch `preview_geometry.py`/`contour_logic.py` ersetztes Code entfernt (u. a. Duplikate von `build_face_path`, `build_contour_path`, `validate_contour_segments_for_profile`, `gcode_for_operation` - alle durch spaetere Imports bereits ueberschattet und nie erreicht)
  - `LathePreviewWidget` (2D-Vorschau-Canvas) nach `lathe_easystep/preview_widget.py` ausgegliedert; als promoted Widget in `lathe_easystep.ui` unveraendert ueber den bestehenden `<header>lathe_easystep_handler</header>` erreichbar, da der Handler die Klasse re-exportiert
  - `WidgetResolver`/`WidgetResolveError` (Widget-Suche fuer Standalone-/eingebettetes Panel) nach `lathe_easystep/widget_resolver.py` ausgegliedert
  - `_collect_params()` nach `lathe_easystep/ui_params.py` (`collect_params()`) ausgegliedert, neben dem bereits dort lebenden `setup_param_maps()`
  - `PANEL_WIDGET_NAMES` nach `lathe_easystep/ui_registry.py` verschoben (gemeinsam von Handler und `widget_resolver.py` genutzt)
  - Vier lebende, bisher nur im Handler vorhandene Vorschau-Hilfsfunktionen (`build_stock_outline`, `build_retract_primitives`, `build_worklimit_primitives`, `build_chuck_nogo_primitives`) nach `preview_geometry.py` verschoben statt geloescht
  - Jede Extraktion einzeln mit vollem Testlauf und echtem PyQt5 (`uic.loadUi` gegen `lathe_easystep.ui`) verifiziert
- Docs: `TODO.md` bereinigt - enthaelt nur noch offene Punkte, erledigte Punkte stehen ausschliesslich hier im Changelog
- Fix: Futter-Sperrzone in der Vorschau begann bisher nicht bei `ZB` (Bearbeitungsmass - die tatsaechliche Grenze, ab der das Rohteil aus dem Futter herausschaut), sondern wurde komplett aus `chuck_no_go_z_limit` plus einem geschaetzten Abstand konstruiert. Die Zone beginnt jetzt korrekt bei `ZB` und reicht von dort Richtung Futter (weiter negativ)
- Fix: Gewinde-Presets wurden nie uebernommen (`thread preset skipped: missing label` bei jedem Klick auf "Preset uebernehmen"). Ursache: `_populate_thread_standard_options()` baute das Combo-itemData ohne den von `validate_thread_preset_data()` zwingend verlangten Schluessel `label` (nur `label_key` war vorhanden)
- Fix (schwerwiegend): Kontur-Punkte mit einem absoluten Ziel von exakt `X0`/`Z0` wurden in `contour_logic.py` stillschweigend durch die vorherige Koordinate ersetzt (`s.get(key, last) or last` - `0.0` ist in Python falsy). Betraf sowohl die Vorschau als auch den generierten G-Code: eine Kontur, die z. B. bis `X19.2`/`Z0` laufen sollte, brach vorher bei einem Zwischenpunkt ab, sobald ein Segment exakt auf `0` zielte
- Fix: `Programm laden` sprang bisher immer auf den ersten fachlichen Schritt (Zeile 1) statt auf den Programmkopf (Zeile 0), sobald das geladene Programm mehr als eine Operation enthielt - praktisch immer der Fall. Ausgangspunkt nach dem Laden ist jetzt immer der Programmkopf
- Tests: Regressionen fuer alle vier Fixes ergaenzt, u. a. mit den exakten Werten aus einem real geladenen Testprogramm; Stand `264 passed`
- Fix (schwerwiegend): Innen-Schruppen (`Abspanen`, Modus Schruppen) erzeugte bei einem realen Testprogramm keinerlei Schnittbewegung, nur eine WARN-Zeile ("ohne Bearbeitungsrichtung deaktiviert"). Ursache war ein UI/Generator-Widerspruch bei `slice_strategy`:
  - `_select_slice_strategy_index()` suchte per `combo.findData(<int>, ...)`, obwohl das itemData der Combo immer die Strings `"parallel_x"`/`"parallel_z"` enthaelt - der Treffer konnte nie gelingen, gueltige gespeicherte Werte (`1`/`2`) wurden beim Laden nie korrekt auf die Combo angewandt
  - `load_operation_params_to_form()` liess `slice_strategy` danach in den generischen `setCurrentIndex(int(val))`-Fallback durchfallen; ein ungueltiger gespeicherter Wert wie `0` landete dadurch auf einem echten Combo-Eintrag ("Parallel X") - die Anzeige log also eine Auswahl vor, die nie getroffen wurde, waehrend `gcode_roughing.py` denselben Wert `0` korrekt als "keine Strategie gewaehlt" behandelte und nur warnte
  - `collect_params()` erzeugte fuer eine Combo ganz ohne Auswahl (`currentIndex() == -1`) ueber den Fallback `idx + 1` den ungueltigen Wert `0` und schrieb ihn in die Operation - exakt der Wert, der spaeter die widerspruechliche Anzeige verursachte
  - Alle drei Stellen korrigiert: numerische Legacy-Codes werden jetzt korrekt auf die String-itemData abgebildet, eine nicht aufloesbare/fehlende Auswahl zeigt die Combo jetzt ehrlich als "nicht ausgewaehlt" (`currentIndex() == -1`) statt eine falsche Strategie vorzutaeuschen, und `collect_params()` fabriziert keinen ungueltigen Platzhalterwert mehr
  - Klarstellung: Die Erzeugung verweigert weiterhin bewusst einen Schruppschnitt ohne explizit gewaehlte Bearbeitungsrichtung (kein automatisches Raten) - das ist beabsichtigt; der Fix beseitigt nur den Widerspruch zwischen UI-Anzeige und tatsaechlichem Generatorverhalten, so dass die Warnung jetzt tatsaechlich handlungsleitend ist
- Tests: Neue Datei `tests/test_slice_strategy_ui_roundtrip.py` (mit echtem PyQt5 statt Stub, da der projektweite qtpy-Stub isinstance-Unterscheidungen zwischen Widget-Typen nicht abbilden kann); `6 passed`. Ausfuehren mit `/usr/bin/python3 -m pytest tests/test_slice_strategy_ui_roundtrip.py`
- Feature: Neue Plausibilitaetspruefung `_check_drill_before_internal_machining()` in `checks.py` - warnt (ohne selbst umzusortieren), sobald eine Innenbearbeitung (Innen-Abspanen, Innen-Einstich, Innengewinde) in der Ablaufreihenfolge vor der ersten Bohrung steht oder gar keine Bohrung vorhanden ist. Das Werkzeug haette sonst keinen Zugang zum noch vollen Material
- Tests: Neue Datei `tests/test_drill_before_internal_check.py` deckt Innen-vor-Bohrung, Bohrung-vor-Innen, fehlende Bohrung, gemischte Groove/Gewinde-Faelle und reine Aussenbearbeitung ab; Stand `269 passed, 1 skipped`
- Fix (schwerwiegend, Datenintegritaet): `ProgramModel.update_geometry()` fror bei bestimmten Operationstypen (u. a. Einstich/Abstich, Planen) den jeweils aktuellen `op.path` als Snapshot in `op.params["path"]` ein (write-once: nur solange der Key noch fehlte). Dieser Snapshot wurde bei spaeteren Parameteraenderungen (z. B. Aussen-Einstich zu Innen-Einstich mit anderem Werkzeug/Durchmesser umgebaut) nie aktualisiert und driftete stillschweigend von der tatsaechlichen Geometrie weg - mit in der gespeicherten Step-Datei sichtbaren, in sich widerspruechlichen Angaben (Werkzeug/Lage/Durchmesser in den Parametern vs. eingefrorener alter Pfad). Geometrie wird jetzt ausschliesslich ueber `op.path` gefuehrt, `params["path"]` wird nicht mehr geschrieben
- Tests: Neue Datei `tests/test_geometry_cache_staleness.py` reproduziert exakt das reale Fehlerbild (Aussen- zu Innen-Einstich-Umbau) und schlaegt gegen den alten Code fehl (verifiziert per `git stash`); Stand `270 passed, 1 skipped`
- Fix (Sicherheit): Die Einfahrt vor dem Schlichtschnitt bei Abspanen (`generate_abspanen_gcode`, Innen- und Aussenbearbeitung) war ein einzelner diagonaler `G0` (X und Z gleichzeitig) direkt aus der vorherigen Position - ohne die Rohteil-/Futter-Sperrzonen-Pruefung und ohne die sichere Zwei-Schritt-Sequenz (erst Z, dann X), die dieselbe Funktion fuer die Schrupp-Zustellung bereits verwendet (`emit_approach()`). Die Schlicht-Einfahrt nutzt jetzt denselben, bereits vorhandenen Sicherheits-Helfer; ein realer Testfall (Innen-Schlichten, Einfahrpunkt X10/Z0 mit ZA=1/ZI=-80) erzeugt jetzt korrekt `(WARN: Startpunkt X10.000 Z0.000 liegt im Rohteil)` statt stillschweigend zu verfahren
- Untersucht, NICHT geaendert (zu riskant ohne Fachbestaetigung): `safe_z` in `generate_abspanen_gcode` wird weiterhin aus dem rohen `ZRA`/`ZRI`-Wert gebildet und ignoriert dabei das `*_absolute`-Flag - bei relativem `ZRI`/`ZRA` (z. B. `0.0`, `absolute=False`) muesste der sicherheitsrelevante Wert eigentlich `ZA + ZRI` sein (siehe bereits vorhandene, korrekte Logik in `gcode_safety._safe_axis_value()`, dort exakt so kommentiert). Ein Versuch, `generate_abspanen_gcode` auf diese bereits vorhandene Funktion umzustellen, brach 21 bestehende Tests, die alle den rohen Wert als korrekt voraussetzen - die Aenderung wurde verworfen und stattdessen als offener, mit Fachwissen zu klaerender Punkt in `TODO.md` dokumentiert (gleiche Kategorie wie die bereits dokumentierte G71/G72-Materialmodell-Unsicherheit)
- Tests: `tests/test_parting_slice.py` um `test_internal_finish_entry_uses_checked_approach_not_raw_diagonal_move` erweitert; Referenzdatei `ngc/Kontur_Radius_Fase.ngc` an die jetzt sicherere Schlicht-Einfahrt angepasst; Stand `271 passed, 1 skipped`
- Fix (Datenintegritaet, Vorschau): `build_program_data()` (vor jedem Speichern aufgerufen) hat abgeleitete Geometrie bisher nicht aufgefrischt - nur `handle_load_program()` tat das ueber `_rebuild_all_operation_geometry()`. Wurde eine Kontur bearbeitet, ohne dass ein davon abhaengiger Abspanen-Step zwischenzeitlich erneut ausgewaehlt wurde, landete die veraltete Kontur-Geometrie (`params["source_path"]`) im gespeicherten Programm. Die G-Code-Erzeugung selbst war davon nicht betroffen (loest die Kontur beim Generieren immer frisch ueber `contour_name` auf), wohl aber die Vorschau in der "alle Steps"-Uebersicht. `build_program_data()` ruft jetzt vor dem Schreiben ebenfalls `_rebuild_all_operation_geometry()` auf
- Fix (Datenintegritaet, Vorschau): `build_abspanen_path()` (Vorschau-Geometrie fuer Abspanen-Operationen) akzeptierte nur eine flache Liste aus `(x, z)`-Punkten in `params["source_path"]`. Die tatsaechliche Quelle (`resolve_contour_path()`) liefert aber IMMER das primitiven-foermige `op.path` der referenzierten Kontur-Operation (`{"type": "line"/"arc", "p1": ..., "p2": ...}`) - der Tupel-Zweig griff dadurch bei keiner echten Kontur-Referenz und jede Abspanen-Vorschau in der "alle Steps"-Uebersicht war leer. `build_abspanen_path()` erkennt jetzt beide Formen (wiederverwendet `contour_features.primitive_to_points()`)
- Tests: Neue Datei `tests/test_contour_source_path_refresh.py`; `tests/test_geometry_cache_staleness.py` um zwei Tests fuer `build_abspanen_path()` (primitiven-foermig und flach) erweitert; Stand `274 passed, 1 skipped`
- Fix: Neu hinzugefuegte oder per "Step laden" eingefuegte Operationen bekamen `params["comment"]` bisher nur beim NAECHSTEN Stepwechsel/Speichern gesetzt (`sync_form_to_operation()`). Wurde ein Step danach nie erneut ausgewaehlt, blieb der Kommentar dauerhaft leer (reale Test.lse: Innen-Einstich-Step ohne jeden Kommentar). `_handle_add_operation()` und `_insert_loaded_operation()` setzen jetzt sofort einen automatischen Kommentar, falls noch keiner vorhanden ist - ein bereits vorhandener (z. B. aus der geladenen Step-Datei uebernommener) Kommentar wird nicht ueberschrieben
- Feature: Neue Plausibilitaetspruefung `_check_duplicate_operations()` in `checks.py` - meldet Operationen mit identischem Typ und identischen Bearbeitungsparametern (Kommentar/Cache-Felder wie `source_path`/`_contour_params`/`path` werden beim Vergleich ignoriert) als Hinweis. Loescht oder aendert nichts automatisch - der Nutzer entscheidet, ob eine Mehrfachverwendung beabsichtigt ist (z. B. dieselbe Nut an zwei Stellen)
- Tests: Neue Dateien `tests/test_auto_comment_on_creation.py` und `tests/test_duplicate_operation_check.py`; Stand `280 passed, 1 skipped`
- Fix: Kontur-Subroutinen (`o<n> sub ... endsub`) wurden fuer JEDE benannte Kontur unbedingt definiert, unabhaengig davon, ob ein Abspanen-Schritt sie tatsaechlich per `G71`/`G72` (`Q<num>`) referenziert. Faellt die Bearbeitung auf Move-based-Code zurueck (nicht zyklustaugliche Kontur oder `Ausgabe bevorzugen: explizit`), blieb die Definition als toter Code im Programm stehen (real reproduziert: `o101` fuer die Innenkontur "ausdrehen", nie aufgerufen). Kontur-Subroutinen werden jetzt erst NACH der Haupt-Ablauferzeugung eingehaengt und nur dann, wenn ihre Nummer tatsaechlich als `Q<num>` im generierten Code vorkommt
- Tests: Neue Datei `tests/test_unused_contour_subroutine_suppressed.py`; Referenzdatei `ngc/Abdrehen.ngc` an die jetzt fehlende (weil ungenutzte) Subroutine-Definition angepasst; Stand `282 passed, 1 skipped`
- Fix: Verschieben (`handle_move_up`/`handle_move_down`) und Loeschen (`_handle_delete_operation`) einer Operation aktualisierte bisher nur den Anzeigetext der Step-Liste, nicht den in `op.params["comment"]` gespeicherten - und in der G-Code-Ausgabe als `(STEP: ...)` verwendeten - Kommentar. Nach einer Umsortierung driftete die gespeicherte Stepnummer im Kommentar von der tatsaechlichen Position auseinander (real reproduziert: `(Step 4: ...)` direkt gefolgt von `(STEP: 5. ...)`). `renumber_operations()` (bisher definiert, aber nie aufgerufen) aktualisiert jetzt auch den gespeicherten Kommentar und wird nach Verschieben/Loeschen aufgerufen
- Fix: `sanitize_gcode_text()` transliterierte Umlaute (ä/ö/ü/ß) explizit, aber keinen Pfeil (→, U+2192). Ein gespeicherter Kommentar mit Pfeil (z. B. aus einer vor der Umstellung auf `->` gespeicherten Planen-Operation) fiel dadurch auf den generischen ASCII-Fallback zurueck, der jedes verbleibende Nicht-ASCII-Zeichen durch ein bedeutungsloses `?` ersetzt (real reproduziert: `Z 0.0→0.0` wurde zu `Z 0.0?0.0`). Pfeil wird jetzt zu `->` transliteriert, konsistent mit der bereits in den `.lng`-Dateien verwendeten Schreibweise
- Tests: Neue Datei `tests/test_comment_encoding_and_renumbering.py`; `tests/test_dirty_and_messages.py` um Stub fuer `_renumber_operations` ergaenzt; Stand `285 passed, 1 skipped`
- Fix (schwerwiegend): `emit_coolant()` verstand nur Strings (`"on"`/`"flood"`/...) und echte `bool`-Werte. Anders als bei Planen (das vorher `opt_bool()` anwendet) reichen Bohren/Einstich/Gewinde `params["coolant"]` unveraendert durch - ein gespeicherter Zahlenwert `1.0` traf dadurch weder den str- noch den bool-Zweig und fiel stillschweigend auf `M9` (AUS) zurueck, obwohl `1.0` "an" bedeuten sollte. Real reproduziert: Innen-Einstich (Op 11), Innengewinde (Op 12) und Bohren (Op 8) mit `coolant=1.0` blieben ohne Kuehlung. `emit_coolant()` behandelt numerische Werte jetzt wie `opt_bool()` (ungleich 0 = an)
- Tests: Neue Datei `tests/test_coolant_normalization.py`; Stand `288 passed, 1 skipped`
- Feature: Neue Plausibilitaetspruefung fuer Gewinde-Presets in `validate_program_setup()` - meldet, wenn die in `params["standard"]` gespeicherten Preset-Metadaten (Steigung/Nenndurchmesser) vom tatsaechlich fuer die G76-Erzeugung verwendeten `pitch`/`major_diameter` abweichen (real reproduziert: Preset "M30x3.5" mit `standard.pitch=3.5`, tatsaechlich verwendet `pitch=1.75` - vermutlich Preset gewaehlt, dann Steigung manuell ueberschrieben, ohne dass die Preset-Metadaten nachgezogen wurden). Meldet nur, aendert nichts automatisch - unklar, welcher Wert gewollt ist
- Tests: Neue Datei `tests/test_thread_preset_consistency_check.py`; Stand `292 passed, 1 skipped`
- Untersucht, NICHT vollstaendig behoben (Geometrie-Splicing zu riskant ohne Backplot-Verifikation): DIN-Freistich-Features in Kontur-Segmenten (`din_relief`) erzeugen nur dann tatsaechlich Geometrie, wenn das betroffene Segment das ABSOLUT ERSTE oder LETZTE Segment der GESAMTEN Kontur ist (`contour_logic.py`, Zeilen ~244-247: `if anchor_mode == "end" and idx != len(segments) - 1: continue`). Bei einem Gewinde-Freistich MITTEN in einer laengeren Kontur (z. B. M30-Aussengewinde mit Freistich bei Z=-35, gefolgt von weiterem Wellenprofil bis Z=-60 - genau der reale Testfall) wird die Pruefung nie erfuellt und `feature_points`/`feature_primitives` bleiben leer. Eine korrekte Behebung muss die Freistich-Primitiven an der Position des EIGENEN Segment-Index in die Kontur einfuegen (nicht nur an den Gesamtkontur-Rand an-/vorhaengen) - das erfordert eine Segment-zu-Primitive-Indexzuordnung (Kantenbehandlungen wie Fase/Radius erzeugen mehrere Primitiven pro Segment) und sollte gegen eine reale DIN-76-Referenzgeometrie verifiziert werden, bevor daran etwas geaendert wird
- Feature: Neue Plausibilitaetspruefung `_check_din_relief_feature_position()` - meldet, sobald ein `din_relief`-Feature wegen der obigen Einschraenkung keine Geometrie erzeugen kann (statt wie bisher stillschweigend leer zu bleiben), inkl. Kontur-Name und betroffenem Segment
- Tests: Neue Datei `tests/test_din_relief_position_check.py`; Stand `295 passed, 1 skipped`
- Fix (schwerwiegend): Ein dedizierter Schlichtstep (`mode=finish`) mit gueltiger Bearbeitungsrichtung (`slice_strategy`) fuehrte trotzdem einen vollen `G71`/`G72`-Schruppzyklus aus, bevor der eigentliche Schlichtschnitt kam - das Material war durch einen fruaheren, separaten Schruppstep bereits abgetragen (z. B. mit eigenem Schruppwerkzeug). Die Wiederholung war unnoetig und potenziell riskant (Schlichtwerkzeug schruppt unbemerkt erneut). `mode=finish` (reiner Schlichtstep) ueberspringt den Schruppzyklus jetzt vollstaendig; `mode=rough` und `mode=rough_finish` sind unveraendert
- Tests: Neue Datei `tests/test_finish_mode_never_reroughs.py`; Stand `298 passed, 1 skipped`
- Fix: Endete die Schlichtkontur bereits genau auf `safe_z` (z. B. Konturende an der Stirnflaeche bei Z0, `ZRA`/`ZRI` ebenfalls 0), wurde trotzdem ein zusaetzliches `G0 Z{safe_z}` angehaengt - eine bedeutungslose Nullbewegung auf eine bereits erreichte Position (real reproduziert in Test.lse's Innen-Schlichten). Wird jetzt uebersprungen, wenn der letzte Konturpunkt bereits auf `safe_z` liegt
- Tests: Neue Datei `tests/test_no_redundant_zero_move_after_finish.py`; Stand `300 passed, 1 skipped`

## [0.7.0] - 2026-07-08

- Refactor: Vorschau-Geometrie-Helfer in `lathe_easystep/preview_geometry.py` gebuendelt und fuer Model/UI als neue Einstiegsschicht verdrahtet
- Refactor: Kontur-Geometrie und Kontur-Validierung in `lathe_easystep/contour_logic.py` aus dem Handler herausgeloest
- Refactor: Neue G-Code-Einstiegsmodule `gcode_program.py`, `gcode_roughing.py`, `gcode_safety.py` und `gcode_utils.py` als kompatible Zerlegung von `slicer.py` angelegt
- Tests: Referenzprogramme und Vertrags-Regressionen fuer Snapshot-G-Code, Save/Load, `G20`, FACE/G72-Profil und Sicherheitsrueckzuege aufgebaut
- Tests: `regenerate_all_ngc.py` regeneriert jetzt sechs Beispielprogramme als Smoke-Basis (`python3 regenerate_all_ngc.py`)
- Tests: Gemeinsamer Smoke-Run in `smoke_test.py` ergaenzt; aktueller Stand validiert mit `171 passed`

## [0.6.1] - 2026-07-08
- Refactor: `Operation`, `ProgramModel` and `OpType` moved out of `lathe_easystep_handler.py` into `lathe_easystep/model.py`
- Refactor: Werkzeugtabellen- und ISO-Helfer in `lathe_easystep/tools.py` ausgelagert
- Refactor: Step-/Programm-Payload-Helfer in `lathe_easystep/persistence.py` ausgelagert
- Refactor: Dateiverknüpfung und Programm-Metadaten in `lathe_easystep/storage.py` ausgelagert
- Refactor: Program-Header-UI-Logik in `lathe_easystep/ui_program.py` ausgelagert
- Refactor: Formularbefüllung für Operationen in `lathe_easystep/ui_operations.py` ausgelagert
- Refactor: Preview-Aufbereitung und Preview-Widget-Ansteuerung in `lathe_easystep/ui_preview.py` ausgelagert
- Refactor: Parameter-, Auswahl-, Persistenz-, Werkzeug-, Sichtbarkeits- und Ablauf-Logik in weitere UI-Module unter `lathe_easystep/` aufgeteilt (`ui_params.py`, `ui_selection.py`, `ui_persistence.py`, `ui_tools.py`, `ui_visibility.py`, `ui_flow.py`, `ui_widgets.py`, `ui_signals.py`, `ui_lifecycle.py`)
- Refactor: Kontur- und Einstich-spezifische UI-Logik in `ui_contour.py` und `ui_groove.py` ausgelagert
- Refactor: Werkzeugnahe Fachlogik in `lathe_easystep/tool_logic.py` ausgelagert
- Refactor: Bohr-, Plan-, Gewinde-, Einstich- und Keyway-G-Code in eigene Module unter `lathe_easystep/` aufgeteilt
- Verifikation: Refactor-Stand mit `pytest -q` erfolgreich getestet (`165 passed`)
- Docs: README neu strukturiert, Versionsstand am Anfang sichtbar gemacht und um englische Betriebs-/Workflow-Informationen erweitert

## [0.6.0] - 2026-07-08
- Branching: Neue Änderungen werden zuerst auf `DEV` gesammelt und müssen dort getestet werden, bevor sie nach `main` migriert werden
- Release-Policy: `main` bleibt als lauffähige Basis; neue Arbeit wird erst nach Test auf `DEV` übernommen
- Preview: Aktive Kontur wird in der Seitenvorschau immer im Vordergrund gezeichnet
- Preview: Seitenvorschau bildet X aus Durchmesserprogrammierung korrekt als Radius ab
- Preview: Zusatzvorschau als Vorderansicht für den aktuellen Z-Schnitt eingebaut
- Preview: Seitenansicht und Schnittansicht bleiben gleichzeitig sichtbar; die Seitenansicht zeigt die aktive Schnittlage als markierte Linie
- Preview: Schnittlage kann direkt in der Seitenansicht verschoben werden; die Vorderansicht aktualisiert sich auf die gewählte Z-Position
- Preview: Vorderansicht wertet jetzt das gesamte Programm statt nur den aktuell markierten Step aus
- Preview: Vorderansicht nutzt eine feste Referenz auf den maximalen Werkstückdurchmesser, damit Konen und Durchmesserwechsel optisch klar kleiner oder größer werden
- Preview: Aktuelle Endgeometrie der Schnittansicht wird zusätzlich flächig hervorgehoben, nicht nur numerisch angegeben
- Preview: Einstich-/Nutgeometrie folgt in der Vorschau jetzt den Maskenwerten für OD, ID und Stirnlagen
- Keyway: Reiter um Werkzeugauswahl, Winkelversatz für Wiederholungen und zusätzliche Bearbeitungsparameter erweitert
- Keyway: Winkelfelder korrekt auf Grad umgestellt; irreführende mm-Einheit entfernt
- Keyway: Nutenstossen ohne unnötige Drehzahl-Eingabe bereinigt, da das Werkstück zwischen den Positionen stillsteht
- Keyway: Winkelversatz der Nutmitten wird jetzt konsistent in Vorschau und Step-Daten verwendet
- Keyway: Reiterwechsel selektiert jetzt den zugehörigen Keilnut-Step in der Liste, damit Laden, Bearbeiten und Speichern auf dieselbe Operation wirken
- Keyway: Parametereingaben werden nach dem UI-Aufbau jetzt zuverlässig mit dem Handler verdrahtet; Änderungen wirken dadurch auf Vorschau, Step-Liste und Dateispeicherung
- Workflow: Dateidialoge merken sich den zuletzt verwendeten Ordner für Step-, Programm-, G-Code- und Werkzeugdateien
- Workflow: Zuletzt geladene Werkzeugtabelle wird beim Start des Panels automatisch wieder geladen
- Workflow: Neuer Button `Änderungen speichern` aktualisiert verknüpfte Steps, Programme und vorhandene G-Code-Dateien direkt aus der aktuellen Maske
- Workflow: Programme speichern jetzt Metadaten zu verknüpften Step- und Programmdateien, damit Änderungen später gezielt zurückgeschrieben werden können
- Workflow: Jeder neue Bearbeitungsschritt erhält eine eigene Step-Datei; Programmspeichern stellt diese Verknüpfung ebenfalls sicher
- Workflow: Programmkopf wird beim Laden und beim Wechsel auf den Program-Tab jetzt konsistent in die Eingabemaske zurückgeschrieben
- Fix: Interne Dateimetadaten (`__step_file_path`, `__program_file_path`, `__gcode_file_path`) bleiben bei Parameteränderungen erhalten
- Fix: Startfehler in der Initialisierung durch fehlende Preview-/Combo-Attribute behoben
- Fix: Auto-Load der Werkzeugtabelle scheitert nicht mehr an fehlenden `tool_table_path`-Referenzen im Frühstart
- Performance-Fix: LinuxCNC-Embedded-Start massiv verkürzt; GUI und Panel sind wieder nach rund 11 Sekunden benutzbar
- Refactor: Widget-Auflösung strikt auf den Panel-Baum begrenzt, keine globalen `allWidgets()`-Scans mehr
- Refactor: Root-Erkennung für Embedded-Panel stabilisiert, Host-`MainWindow` wird nicht mehr fälschlich als Panel benutzt
- Fix: Initialisierung und Signalverdrahtung so umgebaut, dass Embedded-Start wieder funktional bleibt
- Cleanup: aufwendige Startup-Debug- und Refresh-Schleifen entfernt bzw. stark reduziert
- Cleanup: `widget_ids.json` auf echte Panel-Widgets reduziert, um unnötige Persistenz- und Lookup-Kosten zu vermeiden
- Echte Radius-Geometrie (Fillet-Berechnung)
- Innen/Außen-Auswahl pro Radius
- Verbesserte Konturvorschau
- Überarbeitung der Abspan- und Retract-Logik
- README / DEV.md / Changelog neu strukturiert
- Fix: Im Embedded-Betrieb wird die Step-Liste jetzt strikt an `listOperations`/`list_ops` gebunden (kein Fallback mehr auf `gcode_list`)
- Fix: Laden von Einzel-Step und komplettem Programm aktualisiert die sichtbare Step-Liste zuverlässig
- Fix: Parameter-Änderungen greifen auf die aktive Operationsliste (`self.list_ops`) zu
- Verifikation: Save/Load-Regressionstests (`test_save_load_roundtrip.py`, `test_step_double_click.py`) wurden aufgebaut und zuletzt zur Absicherung der Embedded-Step-Logik verwendet
- Safety-Fix: Sichere Rückzugspunkte berücksichtigen jetzt `xra_absolute`/`zra_absolute` korrekt (inkrementell vs. absolut)
- Safety-Fix: Globale Rückzüge und Toolchange-Anfahrten fahren jetzt mit Z-vor-X
- Safety-Fix: `FACE`-Profil-Subroutinen für G72 verwenden nur Schnittbewegungen (`G1`), kein `G0` im Zyklusprofil
- Fix: Programme mit Einheit `inch` emittieren jetzt `G20` (statt immer `G21`)
- Safety-Fix (Drehbank-Freifahrt kontextabhängig): Standard simultan `G0 X.. Z..`, bei Einstich/Keyway erst `X`, bei Bohren/Gewinde erst `Z`
- Safety-Fix (Materialbezug): Simultane Freifahrt wird nur verwendet, wenn die Startposition außerhalb der Rohteil-Hüllzone liegt; innerhalb wird konservativ sequenziell freigefahren
- Feature: Program-Tab erweitert um Spannfutter-Auswahl (80/100/125/160/200/250), Werkstücktyp und Spannart mit automatischer Vorbelegung von No-Go-Sicherheitsmaßen
- Safety-Fix: Freifahrt berücksichtigt zusätzlich eine konfigurierbare Chuck-No-Go-Zone (`chuck_no_go_x_min/x_max/z_limit`) und erzwingt dort sequenzielles Freifahren
- Feature: Spannfutter-Profile ergänzt (`3-Backen Standard`, `Softjaws`, `Innenausdrehen`) mit profilabhängiger Anpassung der No-Go-Geometrie
- Feature: Program-Tab um `Maschinenprofil` ergänzt (schnelle Werkstatt-Presets für Futtergröße/Spannart/Profil)
- Feature: Vorschau zeigt die Futter-Sperrzone als eigene farbige Fläche inkl. Legenden-Eintrag (`Futter-Sperrzone`)
- Preview: aktive Kontur wird beim Schrittwechsel farblich hervorgehoben; Doppelklick auf Steps oeffnet wieder den passenden Reiter
- Preview: Vorschaugeometrie geladener Programme wird nach dem Laden aus den Parametern neu aufgebaut statt aus veralteten Pfad-Caches
- Hinweis: als offene Restpunkte bleiben Programmkopf-Vorschau ohne Vorselektion und fachlich genauere Gewindegeometrie

---

## [0.1.0] – Initial Development
- Erste Version des Lathe EasyStep Panels
- Grundlegende Konturdefinition
- Abspanen parallel Z
- Vorschau und G-Code-Erzeugung
- STEP/Projektdateien

---

Hinweis:
Dieses Projekt befindet sich in aktiver Entwicklung.
Änderungen an Verhalten und Dateiformaten sind möglich.
