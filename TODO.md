# TODO LatheEasyStep

Stand: 2026-09-21

Diese Datei enthaelt ausschliesslich offene Aufgaben. Abgeschlossene Arbeiten,
Befunde und historische Teststaende stehen im [CHANGELOG.md](CHANGELOG.md) und
in den Berichten unter `doc/`. Release-Ziele stehen in [ROADMAP.md](ROADMAP.md).

## Verifizierte Basis

- Branch `dev` ist der vollstaendige Entwicklungsstand (Quelltext, Tests,
  Entwicklungsdokumentation). `main` enthaelt seit dem 17.09.2026 nur noch
  kompakte Release-Commits nach `RELEASE_POLICY.md`
  (`release_manifest.txt` definiert die veroeffentlichten Pfade); die
  Historie von `main` sowie die Tags `v0.7.0`/`v0.8.0` wurden dafuer einmalig
  neu aufgebaut (siehe README.md-Hinweis fuer bestehende Klone).
- 968 Stub-Qt-Tests und 131 Tests mit echtem PyQt5, keine Skips.
- Zwoelf Referenzprogramme bestehen statische NGC-Pruefung und den nativen
  LinuxCNC-Interpreter (`rs274`); zusaetzlich bestehen 43 Matrixprogramme.
- Alle zwoelf Referenzen wurden in der QtDragon-SIM bis `M30` ausgefuehrt.
- Der Generator ist von Qt getrennt. Reiter, Step-Verwaltung und Vorschau
  liegen in eigenen UI-/Fachmodulen.

## 0.9.0-Scope-Status (Audit 2026-09-21, veroeffentlicht 2026-09-21)

**Fuer 0.9.0 war kein bekannter funktionaler Codefehler mehr offen.** Der
0.9.0-Scope-Audit 2026-09-21 hat alle bis dahin als "Ziel 0.9.0"
gefuehrten Architekturpunkte (LES-022, LES-044, LES-051-Rest,
LES-052-Handler-Kleber/`except Exception`/Fehlerklassen/Undo-Redo/Autosave/
Pruefbericht) einzeln gegen den Code- und Teststand geprueft: keiner davon
behebt einen bekannten Fehler, verursacht falschen G-Code/falsche
Fahrwege oder blockiert ein bestehendes 0.9.0-Abnahmekriterium - Details
und Einzelbegruendung je Punkt in den jeweiligen Abschnitten unten sowie
im Changelog. Der damals verbleibende technische Schritt, der regulaere
Release-Vorgang selbst einschliesslich des erstmaligen schreibenden
Laufs von `scripts/create_release.py`, wurde am 2026-09-21 durchgefuehrt:
`v0.9.0` (lightweight Tag, konsistent zu `v0.7.0`/`v0.8.0`) zeigt auf den
Release-Commit `33d5db3` auf `main` (Quelle: `dev`-Commit `dc6b6fe`,
Vorgaenger-`main` `e16728a`). Details siehe ROADMAP.md → "Release-Gate-
Status 0.9.0: freigegeben".

## Priorisierter Arbeitsindex

| ID | Prio | Aufgabe | Aufwand | Ziel |
|---|---|---|---|---|
| LES-051 | - | Panel-Grundgeruest/Darstellungsadapter: 0.9.0-Kernumfang abgeschlossen, zwei Restpunkte verschoben (siehe Abschnitt) | - | 0.9.0 abgeschlossen |
| LES-052 | - | Panel-Architektur/Zustandsmodell: 0.9.0-Kernumfang abgeschlossen, Restpunkte verschoben/optional (siehe Abschnitt) | - | 0.9.0 abgeschlossen |
| LES-022 | P3 | vier verstreute Settings-Zustaende typisieren (kein bekannter Fehler, Audit 2026-09-21: reine Typisierung) | S | 1.0.0/spaeter |
| LES-044 | P3 | drei kleine Qt-freie Restauslagerungen (kein bekannter Fehler, reine Codeverschiebung); ID-only-Vollaudit 2026-09-21 abgeschlossen, keine bekannte sichtbare UI-Prosa mehr ausserhalb `.lng` | S | 1.0.0/spaeter |
| LES-043 | P2 | Gegenspindelfunktion als separates Projekt spezifizieren | XL | separat |
| LES-030 | extern | weitere reale Maschinenprofile verifizieren | extern | offen |
| Release-Prozess | P3 | Standing-Checkliste fuer jedes zukuenftige Release pflegen (siehe Abschnitt) | S | laufend |

## Release-Prozess

`RELEASE_POLICY.md` und `scripts/create_release.py` (mit `release_manifest.txt`)
wurden am 17.09.2026 eingefuehrt. Der zuvor nur lesend (`--check`)
gegengepruefte schreibende Release-Pfad wurde am 2026-09-21 beim
tatsaechlichen 0.9.0-Release erstmals real durchgespielt
(`scripts/create_release.py 0.9.0`, Release-Commit `33d5db3` auf `main`,
Tag `v0.9.0`) und vollstaendig verifiziert (Manifest-Deckungsgleichheit,
Blob-Identitaet zu `dev`, korrekter Autor/Committer aus bestehender
Git-Konfiguration, keine KI-/Co-Author-Trailer, kein Leck von Test- oder
Entwicklungsdateien in den Release-Commit). Die dabei im Skript gefundene
Abweichung (empfohlener Tag-Befehl `git tag -a ...` widersprach der
tatsaechlichen Projektpraxis mit lightweight Tags bei `v0.7.0`/`v0.8.0`)
wurde in `scripts/create_release.py` auf `git tag <tag> <commit>`
korrigiert.

- [x] den tatsaechlich schreibenden Release-Pfad einmal vollstaendig
  durchspielen - geschehen als echter 0.9.0-Release (kein Wegwerf-/Test-
  Release mehr noetig).

Fuer jedes zukuenftige Release weiterhin als Standing-Checkliste offen
(nicht an eine bestimmte naechste Version gebunden):

- [ ] vor jedem Release explizit pruefen, ob seit dem letzten Release neue
  Laufzeitabhaengigkeiten ausserhalb der `release_manifest.txt`-Pfade
  hinzugekommen sind. Das Skript erkennt fehlende/veraenderte Manifest-
  Eintraege, aber nicht, dass ein neuer Laufzeitpfad ueberhaupt ins Manifest
  gehoert.
- [ ] die vorhandenen Agenten-Instruktionsdateien (`CLAUDE.md` u. Ae.) um
  einen kurzen Verweis ergaenzen: fuer Release-Arbeiten ist
  `RELEASE_POLICY.md` verbindlich. Keine Kopie der Regeln, sonst laufen
  beide Texte auseinander.

## LES-022 Bewegungs- und Modalzustand

Audit 2026-09-18 gegen den aktuellen `dev`-Stand: `MotionState` und
`SpindleState` sind fuer alle tatsaechlich dynamisch umgeschalteten
Modalgruppen abgeschlossen.

- G96/G97 (CSS) vollstaendig zentral ueber `SpindleState`
  (`request()`/`activate()`/`suspend()`, `gcode_safety.py`).
- Reale Endposition wird nach jeder Operation mit deterministisch bekanntem
  Ergebnis in `MotionState` nachgefuehrt: Bohren (`gcode_drill.py`),
  Gewinde (`gcode_thread.py`), G70-Fertigzyklus und move-basiertes
  Schruppen (`rough_turn_parallel_x/z`, `gcode_roughing.py`, seit "vierte
  Etappe" 2026-09-13 inkl. Bandendposition, nicht mehr nur bedingungslos
  invalidiert).
- G90/G91, G7/G8, G94/G95, G18, G80 werden einmalig im Programmkopf
  gesetzt (`gcode_program.py`) und im gesamten Repo nie dynamisch
  umgeschaltet - dafuer ist aktuell kein zentraler Zustand erforderlich,
  es gibt keinen Codepfad, der das aendern wuerde.
- G40/G41/G42 (Werkzeugradiuskorrektur) wird ausschliesslich in
  `generate_abspanen_gcode()` (`gcode_roughing.py`) genutzt und dort in
  jedem Pfad, der sie aktiviert, im selben Funktionsdurchlauf auch wieder
  per G40 abgewaehlt (inkl. harter Weglaengen-Validierung) - lokal
  korrekt, kein zentraler Zustand noetig.
- Zustandsuebergaenge sind regressionsgesichert
  (`tests/test_gcode_motion_regressions.py`,
  `tests/test_no_redundant_zero_move_after_finish.py`,
  `tests/test_css_and_drill_validation.py`, `tests/test_css_clearance.py`).

**Bewusste, abgeschlossene Designentscheidung (kein offener Punkt):**
`MotionState.clear()` bleibt endgueltig fuer zwei Faelle bestehen, in denen
die reale Endposition strukturell nicht von aussen bekannt ist, ohne
LinuxCNC-/Makro-interne Zustellogik in Python zu duplizieren:

- G71/G72-Roughing-Zyklus ohne abschliessendes G70
  (`generate_abspanen_gcode()`, `gcode_roughing.py`) - die Einzelpaesse
  laufen interpreterintern, ihre Endposition ist von aussen nicht bekannt.
- Nut-Zyklus `o220` (`gcode_groove.py`) - die Breitenachsen-Endposition
  haengt datenabhaengig von Werkzeugbreite/Nutbreite/Ueberdeckung ab.

In beiden Faellen ist das Fallback-Verhalten sicher-konservativ:
`MotionState.at()` liefert bei unbekannter Position immer `False`, jede
nachfolgende Anfahrt (`emit_approach()`/`append_tool_and_spindle()`,
`gcode_safety.py`) faehrt deshalb immer die volle sichere Rueckzugs-/
Anfahrtsroute, statt eine noetige Bewegung faelschlich zu uebergehen. Eine
"granulare" Nachfuehrung waere hier keine Fehlerbehebung, sondern haette
zur Folge, LinuxCNC-Zykluscode bzw. Makro-Zustellogik in Python
nachzubilden - bewusst nicht vorgesehen.

**Technische Restarbeit, verschoben auf 1.0.0/spaeter (kein nachgewiesener
funktionaler Fehler, daher keine hohe Prioritaet):** vier Zustaende leben
weiterhin als rohe `settings["_..."]`-Schluessel statt in einem
typisierten Objekt wie `MotionState`/`SpindleState`. Jeder Wert wird
konsistent gelesen/geschrieben, keiner der vier zeigt einen aktuell
nachweisbaren funktionalen Fehler - eine Typisierung waere
Architekturaufraeumen, keine Fehlerbehebung. 0.9.0-Scope-Audit 2026-09-21
gegen den Code bestaetigt: alle vier sind reine, in sich konsistente
Buchfuehrung innerhalb eines einzelnen Generatorlaufs (exakt dasselbe
Muster wie das bereits typisierte `MotionState`), durch die volle
Referenz-/Matrix-`rs274`-Suite mitgeprueft - kein 0.9.0-Blocker, LES-022
ist damit fuer 0.9.0 abgeschlossen:

- [ ] `_current_tool` (aktuell geladenes Werkzeug, `gcode_safety.py`)
- [ ] `_active_retract_mode` (Innen-/Aussen-Rueckzugsebene je Operation,
  gesetzt in `gcode_program.py`, gelesen in `gcode_safety.py`)
- [ ] `_cycle_defined_subs` (bereits per G71/G72 definierte
  Zyklus-Subroutinen fuer G70-Wiederverwendung, `gcode_roughing.py`)
- [ ] `_last_drill_diameter`/`_last_drill_depth` (Gedaechtnis fuer
  nachfolgende Innenbearbeitungs-Sicherheitspruefungen, `gcode_program.py`/
  `gcode_utils.py`/`gcode_roughing.py`)

## LES-051 Panel-Grundgeruest, Ressourcen und Darstellungsadapter

Die bestehende Shell-/Fragment-Struktur ist die richtige Basis, aber noch
keine vollstaendige Trennung von Zustand, Fachlogik und optischer Darstellung.
Das Panel soll ueber ein stabiles Grundgeruest geladen werden, waehrend
Darstellungen und Ressourcen austauschbare Adapter bleiben.

Umgesetzt (Details im Changelog): Besitzgrenzen sind in
`doc/PANEL_ARCHITECTURE.md` dokumentiert; der Qt-freie `ToolVisualProvider`
loest Werkzeug-/Schneidplatten-Darstellungen aus einem Theme-Manifest auf
(diagnostizierter Fallback bei fehlenden/ungueltigen Ressourcen, Pfade nicht
in Fachobjekten verankert, per Test belegt dass ein Ressourcenwechsel weder
Operationen/Werkzeugdaten noch G-Code veraendert); Vorschau-Legende,
Status-/Warnungsbox, Haupt-Vorschau-Canvas, Vorderansicht-Ringe/-Fuellungen
und die uebrigen "Chrome"-Farben (Achsen, Gitterticks, Legenden-/Status-Box-
Rahmen, Keilnut-Overlay, Schnittlinie) sind vollstaendig als Qt-freie
Datenvertraege in `preview_geometry.py` ausgelagert.

Audit 2026-09-20 gegen `dev`: der Standalone-/Embedded-Ladevertrag
(Reihenfolge, Widget-Registrierung, Signalbindung, Wiederholung) ist
bereits vollstaendig untersucht und abgesichert - Details unter LES-052
Abschnitt 1 (`doc/PANEL_ARCHITECTURE.md` → "Ladevertrag: Standalone und
Embedded"), kein erneuter allgemeiner Punkt hier. Die
Handler-Kleber-Reduzierung ist mit dem gleichlautenden LES-052-Abschnitt-1-
Punkt zusammengefuehrt, Details dort. Konfigurierbare Theme-Auswahl, Cache
und Lebensdauer fuer `ToolVisualProvider`: Produktentscheidung, keine
Architekturfrage - einmalig unter LES-052 Abschnitt 2 gefuehrt, nicht hier
dupliziert.

0.9.0-Scope-Audit 2026-09-21: die beiden verbleibenden Punkte behandeln
keinen bekannten Fehler und blockieren kein bestehendes
0.9.0-Abnahmekriterium - LES-051 ist damit fuer 0.9.0 abgeschlossen,
beide Punkte verschoben:

- [ ] **(1.0.0/spaeter, spaetere Robustheitsverbesserung)** Fehlerbehandlung
  bei einem dauerhaft (nicht nur verzoegert) fehlenden Fragment/Widget -
  bisher nicht untersucht. Die bestehende Ladevertrag-Bestandsaufnahme
  deckt Reihenfolge/Registrierung/Signalbindung/Wiederholung ab, aber
  nicht den Fall, dass ein Lookup auch nach allen drei Durchlaeufen
  endgueltig fehlschlaegt. Code-Pruefung 2026-09-21
  (`ui_lifecycle.py::finalize_ui_ready()`): nach dem dritten Durchlauf
  (2000ms) wird bei weiterhin fehlenden kritischen Widgets nur geloggt
  ("will retry on next timer"), obwohl kein vierter Timer existiert - in
  der Praxis nie beobachtet (alle 131 Real-Qt-Tests und die QtDragon-SIM
  finden alle Widgets zuverlaessig), rein hypothetisches Risiko fuer eine
  kuenftige inkompatible Einbettungsumgebung.
- [ ] **(optionales zukuenftiges Architekturfeature, kein Versionsziel)**
  optionale Bedienelemente (z. B. Schnittansicht-/Ansicht-zuruecksetzen-
  Buttons) als austauschbare Komponenten ueber einen eigenen Datenvertrag,
  analog zu den bereits ausgelagerten Farb-/Stil-Vertraegen. Reine
  Architekturidee ohne aktuell bekannten funktionalen Fehler -
  `ui_preview.py` verdrahtet diese Buttons weiterhin direkt
  (`_get_widget_by_name()` + inline `TRANSLATIONS.tr()`), aber kein Bug,
  kein bekannter Bedarf fuer ein zweites Skin. Nur relevant, falls je ein
  zweites Skin gebraucht wird.

## LES-052 Panel-Architektur, Zustandsmodell und Wiederherstellung

Diese Aufgabe beschreibt den groesseren Ausbauplan auf Basis von LES-051. Vor
der Umsetzung muessen die Grenzen zwischen fachlichem Zustand, Controller,
Views, Ressourcen und Persistenz festgelegt werden. Kein einzelner Umbau darf
die G-Code-Erzeugung oder bestehende Maschinenlogik nur wegen einer optischen
Aenderung veraendern.

### 1. Architektur und Ladevertrag

Umgesetzt (Details im Changelog und `doc/PANEL_ARCHITECTURE.md`): fuenf der
sechs Zustandskategorien (`ProgramState`, `OperationState`, `ToolTableState`,
`DirtyState`, `RuntimeState`) sind fachlich getrennte, Qt-freie
Verantwortungen mit dokumentierten Besitzverhaeltnissen -
`ProgramState`/`OperationState` (`model.py`) und `MotionState`/`SpindleState`
(`motion_state.py`) waren es schon vorher; `DirtyState` (`dirty_state.py`),
`ToolTableState` (`tool_table_state.py`) und `RuntimeState`
(`runtime_state.py`) wurden neu gekapselt, jeweils als duenner `handler.
_<name>`-Adapter ueber den bestehenden Aufrufstellen. Handler-Kleber-
Extraktionen auf dieser Basis: `_handle_add_operation()`/
`_handle_delete_operation()`, `_refresh_operation_list()` und
`_handle_param_change()` und `_tool_change_position_lines()` nach
`ui_flow.py`, `_populate_thread_standard_options()` nach `ui_thread.py`
verschoben, Details im Changelog und `doc/PANEL_ARCHITECTURE.md`. Reine
Widget-Lookup-Bootstrap-Methoden
(`_ensure_contour_widgets()`, `_ensure_thread_widgets()`) bewusst NICHT
extrahiert - das ist Bootstrap-Code, der laut diesem Punkt auf dem Handler
bleiben soll; ihre eigentliche offene Aufgabe ist der Ladevertrag-Punkt
unten. `ViewState` (Zoom/Pan/Slice/Ansichtsmodus, vormals lose Attribute
auf `LathePreviewWidget`) ist jetzt ebenfalls gekapselt (`view_state.py`,
fuenfte Zustandskategorie) - Details im Changelog und
`doc/PANEL_ARCHITECTURE.md`. Der bei der `refresh_operation_list()`-
Extraktion gefundene tote `select_index is None`-Zweig ist entfernt,
`select_index` ist jetzt ein regulaerer Pflichtparameter (kein Aufrufer
liess ihn je weg).

Handler-Kleber-Reduzierung (Audit 2026-09-20, zusammengefuehrt mit dem
gleichlautenden LES-051-Punkt - kein zweiter Punkt mehr dort): AST-Analyse
aller 205 Handler-Methoden zeigt, dass der ganz ueberwiegende Teil bereits
als bewusst gehaltener Bootstrap-/Widget-Lookup-/Uebersetzungscode
identifiziert ist (`__init__`, `initialized__`, `_ensure_contour_widgets()`,
`_ensure_thread_widgets()`, `_apply_*_translations`/`_apply_*_tooltips`
u. Ae. - siehe oben "bewusst NICHT extrahiert"). Kein bekannter Fehler,
reine Architekturarbeit.

- [ ] **(1.0.0/spaeter)** `_select_operation_for_current_tab()`,
  `_ensure_slice_z_matches_operation()`/`_suggest_slice_z_for_preview()`,
  `_write_contour_row()`, `_select_slice_strategy_index()`,
  `_setup_thread_helpers()`/`_apply_standard_thread_selection()`/
  `_apply_thread_preset_force()`, `_insert_loaded_operation()` (alle
  `lathe_easystep_handler.py`) - echte, nicht rein UI-mechanische Logik,
  die in testbare Module unter `lathe_easystep/` gehoert. 0.9.0-Scope-Audit
  2026-09-21: kein bekannter Fehler in einer dieser sieben Funktionen (alle
  in dieser Session real gefundenen Fehler darin - Kontur-Rollback,
  Reentranz, Programmkopf-Dirty - sind bereits behoben); Stichprobe zeigt
  zudem, dass die Thread-Preset-Funktionen bereits duenne Wrapper um die
  laengst extrahierte, getestete Kernlogik (`ui_thread.py::
  apply_thread_preset()`, `tests/test_thread_preset_application.py`) sind
  - die urspruengliche Begruendung ist fuer diese drei teilweise ueberholt.
  Kein 0.9.0-Blocker.

Ladevertrag und Views ohne eigenen Fachzustand: Bestandsaufnahme +
Umsetzung abgeschlossen (Details: `doc/PANEL_ARCHITECTURE.md` →
"Ladevertrag: Standalone und Embedded" / "Views ohne eigenen Fachzustand").
`connect_mode_visibility_signals()` hat jetzt denselben Dedup-Schutz wie
die anderen fuenf Connectoren; der tote `process_deferred_lookups()`-Code
und die nie geleerte `_deferred_lookup_queue` wurden entfernt; der eigentlich
tote `_connect_signals()` wurde entfernt, aber `connect_resolver_fallbacks()`
(bisher nur ueber diesen toten Pfad erreichbar, aber als einziger echter
5s-Polling-Rueckfall fuer `listOperations` NICHT redundant) wurde stattdessen
sauber in `finalize_ui_ready()` eingebunden. Fuer "Views ohne eigenen
Fachzustand" fand die Stichprobe keine strukturelle Verletzung. Das
LES-052-Abnahmekriterium "identischer G-Code bei unterschiedlichen
Ressourcensaetzen" war entgegen der ersten (zu eng gesuchten)
Bestandsaufnahme bereits seit LES-051 abgedeckt
(`test_switching_tool_visual_resource_never_affects_generated_gcode`,
`tests/test_tool_preview_layout.py`) - jetzt auf alle Beispielprogramme
erweitert statt nur eines; der zunaechst neu geschriebene, redundante Test
wurde wieder entfernt. `LathePreviewWidget`s Rendering-Cache-Felder fliessen
nachweislich nie in G-Code zurueck (neuer Test).

### 2. Darstellungs- und Ressourcenadapter

Vollstaendig bereits umgesetzt (aus LES-044/LES-051, bei der Bestandsaufnahme
oben entdeckt - TODO.md war hier durchgehend veraltet, analog zum
`ViewState`-Befund). `ToolVisualProvider`/`ToolVisualRequest`/`ToolVisual`
(`tool_visuals.py`) existieren, sind Qt-frei, getestet
(`tests/test_tool_visual_provider.py`) und ueber `resolve_tool_visual()`/
`handler._tool_visual_provider` (`tool_logic.py`) live verdrahtet - Pfade/
Cache/Fallbacks landen nachweislich nie in `Tool`-Objekten oder
Programmdaten. Preview-Canvas, Legende und Status-/Warnungsbox sind
ebenfalls bereits als reine Qt-freie Datenvertraege ausgelagert
(`PREVIEW_DRAW_STYLES`/`LEGEND_ENTRIES`/`legend_layout()`/
`STATUS_BOX_STYLE`/`status_message_layout()` u. a. in `preview_geometry.py`,
Zeichenplaene in `preview_scene.py`), jeweils mit eigenem "ist ein reiner
Vertrag"-Test in `tests/test_preview_legend_and_status_layout.py`. Details:
`doc/PANEL_ARCHITECTURE.md` → "Werkzeugdarstellung". Offener Produktentscheid
(keine Architekturfrage, hier einmalig gefuehrt - nicht mehr zusaetzlich
unter LES-051): `handler._tool_visual_provider` wird in der laufenden
Anwendung nirgends auf ein echtes Theme-Verzeichnis gesetzt - es greift
also immer nur der prozedurale Fallback; lohnt sich ein echtes grafisches
Theme mit konfigurierbarer Auswahl, Cache und Lebensdauer, oder ist das
bewusst ausreichend?

### 3. Atomare Zustandsaenderungen und Fehlergrenzen

Anders als Abschnitt 1/2: hier gibt es echte, teils sicherheitsrelevante
Luecken (Bestandsaufnahme + erster Fix 2026-09-17, Details:
`doc/PANEL_ARCHITECTURE.md` → "Atomare Zustandsaenderungen und
Fehlergrenzen"). Konkreter Fund und behoben: `sync_form_to_operation()`
(`ui_program.py`) ueberschrieb `op.params` mit den neu gesammelten Werten,
BEVOR `update_geometry()` validierte (`validate_finite_data()` in
`model.py`, ein echter, erreichbarer Fehlerfall bei NaN/Inf/nicht-
numerischen Eingaben) - schlug die Validierung fehl, blieb das Modell ohne
jede sichtbare Meldung auf dem halb angewendeten, ungueltigen Stand stehen
(der Aufrufer `handle_param_change()` schluckt die Exception). Jetzt wird
bei einem Fehlschlag auf die vorherigen Parameter zurueckgesetzt.
Regressionsbewiesen.

Systematischer Audit 2026-09-20 (Eingabe -> Normalisierung -> Validierung ->
Modelluebernahme -> Dirty-State -> Preview/Warnungen, geprueft gegen Save/
Load, Step hinzufuegen/laden/loeschen/verschieben, Parameter-/Header-
Aenderungen, Werkzeugauswahl/-tabelle) fand drei weitere echte Stellen mit
demselben oder einem verwandten Muster - alle drei noch am selben Tag
behoben, regressionsbewiesen (zuerst rot, dann durch den jeweiligen Fix
gruen):

- `handle_load_program()` (`ui_persistence.py`) leerte `handler.model.
  operations` bereits, WAEHREND die einzelnen Operationen noch geparst
  wurden - ein Fehler in einer spaeteren Operation (`_step_data_to_
  operation()` wirft z. B. bei einem strukturell ungueltigen `path`-
  Eintrag, was die vorgelagerte Zahlen-Endlichkeitspruefung nicht abdeckt)
  ersetzte das noch offene, ggf. ungespeicherte Programm durch einen
  kaputten Teilimport. Fix: das neue Programm wird jetzt komplett in einer
  lokalen Liste aufgebaut/validiert, bevor `handler.model.operations`
  ueberhaupt angefasst wird. Tests:
  `test_load_program_failure_in_later_operation_leaves_clean_program_untouched`,
  `..._leaves_dirty_program_untouched` (`tests/test_dirty_state_load_save_contract.py`).
- `handle_param_change()` (`ui_flow.py`) verschluckte eine von `sync_form_
  to_operation()` korrekt zurueckgerollte, aber weitergeworfene Exception
  lautlos und markierte den Step/Header trotzdem als dirty - ohne das
  Formular auf den (bereits zurueckgerollten) gueltigen Modellzustand
  zurueckzusetzen. Fix: bei einem Fehlschlag wird jetzt ausschliesslich das
  Formular ueber die bereits vorhandene `_load_params_to_form()` mit dem
  Modell resynchronisiert, kein dirty gesetzt, bestehender Dirty-Zustand
  unangetastet gelassen. Tests:
  `test_handle_param_change_does_not_mark_dirty_and_resyncs_widget_when_update_is_rejected`,
  `test_handle_param_change_does_not_mark_program_dirty_when_header_update_is_rejected`
  (`tests/test_dirty_and_messages.py`).
- `handle_add_operation()`s Programmkopf-Zweig (`ui_flow.py`, der einzige
  Weg, wie ein neues Programm ueberhaupt seinen ersten Kopf bekommt): beide
  Unterfaelle (neu einfuegen, bestehenden ersetzen) markierten nie dirty;
  der "ersetzen"-Unterfall validierte zusaetzlich gar nicht (anders als der
  "einfuegen"-Unterfall, der `update_geometry()` vor dem Insert aufruft).
  Fix: neuer Kopf -> `_mark_program_structure_dirty()`; Kopf ersetzen ->
  erst auf einem noch nicht uebernommenen Kandidaten validieren (wie beim
  Einfuegen), dann `_mark_dirty(program=True)` - bei ungueltigen Werten
  bleibt der bestehende Kopf unveraendert. Tests: alle vier Faelle in
  `tests/test_program_header_add_operation.py` (neu).

- Kontur-Tabellen-Verdacht untersucht, bestaetigt und behoben (2026-09-20):
  `handle_contour_delete_segment()` (`ui_contour.py`) konnte die letzte
  verbleibende Segmentzeile eines bestehenden, ausgewaehlten Kontur-Steps
  entfernen, obwohl `contour_logic.build_contour_variants()` bei
  `len(pts) < 2` seinen eigenen Rueckgabetyp verletzte (blanke Liste `[]`
  statt des sonst ueblichen Dicts mit `finish_primitives`/...) -
  `build_contour_path()`s `variants["finish_primitives"]` warf dadurch
  einen unbehandelten `TypeError` statt einer fachlichen Fehlermeldung.
  `sync_form_to_operation()` rollte `op.params` zwar bereits korrekt
  zurueck, liess die TABELLE aber auf dem abgelehnten (leeren) Zustand
  stehen - Modell und sichtbare Tabelle zeigten danach unterschiedliche
  Konturen. Fixes: (1) `build_contour_variants()` wirft jetzt konsistent
  mit `validate_contour_segments_for_profile()`s bereits etablierter
  Bedeutung ("zu wenige Segmente = ungueltig, nicht legitim leer") einen
  `ValueError`, kein neuer Rueckgabetyp-Bruch mehr; (2)
  `handle_contour_delete_segment()` faengt einen Fehlschlag ab und stellt
  die Tabelle ueber die vorhandene `_load_params_to_form()`
  (dispatcht fuer CONTOUR an `_load_contour_operation_to_form()`) aus dem
  unveraenderten `op.params` wieder her, ohne dirty zu markieren; (3)
  `add`/`delete`/`move up`/`move down` sowie `contour_start_x`/
  `contour_start_z` (dabei mitgefunden: waren bisher nur an die
  Live-Vorschau angebunden, nie zuverlaessig an Modell/Dirty-State)
  markieren einen bestehenden, ausgewaehlten Kontur-Step jetzt bei Erfolg
  korrekt dirty. Tests: `tests/test_contour_segment_change_dirty_and_
  rollback.py` (Real-Qt, zuerst rot). G-Code-Referenzen (`ngc/`)
  unveraendert (`regenerate_all_ngc.py` liefert Null-Diff), alle 12
  Referenzen + 43 Matrixfaelle bestehen `rs274`.
- Kontur-State-/Preview-Block vollstaendig abgeschlossen (2026-09-21):
  - **Teil A**: `ui_preview.py::collect_preview_state()` rief fuer eine
    noch leere/unvollstaendige, gerade erst begonnene Kontur (nur
    erreichbar, solange `handler.model.operations` komplett leer ist,
    z. B. direkt nach "Neues Programm" mit aktivem Kontur-Tab)
    `build_contour_path()` unbedingt auf - seit dem `contour_logic.py`-Fix
    ein `ValueError` statt eines `TypeError`, aber weiterhin unbehandelt.
    Fix: dieselbe bereits vorhandene `validate_contour_segments_for_
    profile()`-Pruefung wie die Kontur-Tab-eigene Live-Vorschau
    (`update_contour_preview_temp()`) davor geschaltet - bei
    unvollstaendigen Daten wird einfach keine Konturgeometrie erzeugt
    (auch <2 Segmente werden so konsistent mit dieser bereits etablierten
    Live-Vorschau behandelt statt nur >=1). Nichts wird ins Modell
    uebernommen (dieser Zweig baut nur ein lokales `Operation`-Objekt fuer
    die Vorschau, nie `handler.model`). Tests:
    `tests/test_contour_preview_incomplete_draft.py` (neu, 2 Faelle,
    Stub-Qt, zuerst rot).
  - **Teil B**: die drei noch offenen Pfade real (nicht nur vermutet)
    geprueft. `handle_contour_table_change()` (Zellen-/Combo-Edits) und
    `handle_contour_edge_change()` (Kantentyp-Vorlage anwenden) hatten
    beide denselben bestaetigten Doppelbefund wie `delete_segment` vor dem
    letzten Fix: ein direkter, nicht-numerischer Zellen-Text (z. B. X/Z)
    laesst `finite_float()` ueber `_collect_contour_segments()` mit einem
    `ValueError` scheitern (reproduziert: `"Kontur Zeile 1: ungueltige
    Zahl 'abc'."`) - vorher unbehandelt, Tabelle blieb auf dem
    abgelehnten Text stehen, nie dirty auch im Erfolgsfall. Fix: beide
    nutzen jetzt denselben (aus `delete_segment` extrahierten,
    wiederverwendeten) Sync-mit-Wiederherstellung-Helfer - bei Erfolg
    dirty, bei Fehlschlag Tabelle aus `op.params` wiederhergestellt,
    bestehender Dirty-Zustand unangetastet. `contour_name` erwies sich
    NICHT als reine Anzeige-/Metadatenangabe, sondern als fachlicher
    Bestandteil (`op.params["name"]`, von ABSPANEN-Operationen ueber
    `contour_name` referenziert) - hatte denselben Fund wie Start-X/Z
    (nur an Vorschau/Auswahlliste angebunden, nie zuverlaessig an Modell/
    Dirty-State). Fix: neue `handle_contour_name_change()`, analog zu
    `handle_contour_start_change()`, zusaetzlich verdrahtet (leichte
    Variante ohne eigene Fehlerbehandlung, da eine Umbenennung selbst
    keine ungueltigen Zahlen erzeugen kann). Tests: 8 neue Faelle in
    `tests/test_contour_segment_change_dirty_and_rollback.py` (Real-Qt,
    zuerst rot).
  - **Reentranz-Fund behoben (2026-09-21):** der Kantentyp-Combo einer
    Tabellenzeile ist an `handle_contour_table_change()` angebunden;
    `_write_contour_row()`s `setCurrentIndex()`
    (`lathe_easystep_handler.py`) loeste dieses Signal REENTRANT aus,
    waehrend die Zeile noch programmgesteuert befuellt/wiederhergestellt
    wurde. Bestaetigt: ein rein programmatischer `_write_contour_row()`-
    Aufruf loeste dadurch selbststaendig einen Sync/Dirty-Zyklus aus (keine
    Benutzeraenderung, trotzdem dirty); enthielt eine ANDERE Zeile zu
    diesem Zeitpunkt bereits ungueltigen Text, fuehrte das sogar zu einem
    *nativen Prozessabsturz* (`Fatal Python error: Aborted`). Fix: die
    zwei `setCurrentIndex()`-Aufrufe in `_write_contour_row()` blocken
    jetzt kurz nur das Signal des betroffenen Combo-Widgets selbst
    (dieselbe bereits im Projekt etablierte Technik wie in
    `_load_contour_operation_to_form()`/`sync_contour_edge_controls()` -
    keine globale Signalsperre, keine neue Architektur). Damit ist der
    Sync-/Dirty-Ablauf nach einer Kantentyp-Aenderung jetzt vollstaendig
    deterministisch (nicht mehr zeitpunktabhaengig): programmatisches
    Schreiben allein erzeugt keine fachliche Aenderung/kein Dirty;
    Benutzeraenderung funktioniert weiterhin und markiert korrekt dirty;
    Restore nach einer abgelehnten Aenderung endet exakt mit
    Tabelle == unveraendertem `op.params`, bestehender Dirty-Zustand
    bleibt dabei unangetastet. Tests (zuerst rot):
    `test_write_contour_row_alone_does_not_sync_or_mark_dirty`,
    `test_edge_change_restore_after_invalid_change_ends_deterministically_with_table_matching_model`,
    `test_edge_change_restore_after_invalid_change_does_not_alter_existing_dirty_state`
    (`tests/test_contour_segment_change_dirty_and_rollback.py`).
  - `ui_preview.py` und `ui_contour.py`/`lathe_easystep_handler.py`
    enthalten keine Generator-/Konturgeometrielogik (nur Vorschau-Guard
    bzw. Zustands-/Dirty-Fluss) - `regenerate_all_ngc.py`/`rs274` deshalb
    in diesem Durchgang nicht erneut ausgefuehrt (letzter Stand:
    Null-Diff, siehe oben).
**Breite `except Exception`-Fallbacks: kein eigener 0.9.0-Meilenstein mehr
(Entscheidung 0.9.0-Scope-Audit 2026-09-21).** Projektweite Zaehlung ergab
weiterhin ~400/486 Vorkommen in 40+/43 Dateien; die reine Anzahl ist aber
kein Fehlerbeleg. Stichprobe in bisher ungeprueften Dateien (`ui_header.py`)
zeigt dieselbe Kategorie wie die bereits einzeln bewerteten LES-044-Stellen:
defensive Absicherung gegen PyQt5-Widget-Zugriffsfehler mit sauberem
Fallback, kein verschluckter Fachfehler. Alle in dieser Session tatsaechlich
gefundenen, funktional wirksamen verschluckten Fehler (Kontur-Rollback,
`handle_param_change()`s Dirty-Fehlmarkierung, `handle_load_program()`s
Teilimport, `handle_load_step()`s Dirty-Loeschung) wurden einzeln, gezielt
und mit Regressionstest behoben - **dieses Vorgehen bleibt die Praxis**:
konkrete, einzeln bestaetigte Faelle weiterhin gezielt mit Regressionstest
beheben, statt eine pauschale Bereinigung als eigenen Meilenstein zu fuehren.
`preview_widget.py`/`ui_preview.py` bleiben als bereits abgeschlossenes
Beispiel bestehen (siehe LES-044).

- [ ] **(1.0.0/spaeter)** Fehlerdiagnosen zentral sammeln und fuer Log,
  UI-Warnung und Tests strukturiert nutzbar machen - vollstaendig
  unimplementiert, eigene Entwurfsarbeit. 0.9.0-Scope-Audit 2026-09-21:
  `ui_messages.py::format_user_error()`/`parse_error_location()` bieten
  bereits einen funktionierenden Mechanismus (Exception -> lokalisierte
  Nutzermeldung -> automatischer Sprung zu Tab/Feld); alle in dieser
  Session behobenen Fehler wurden darueber sauber gemeldet, ohne eine
  zentrale Sammlung zu benoetigen. Kein 0.9.0-Blocker.
- [ ] **(1.0.0/spaeter)** Fehlerklassen vereinheitlichen: `INFO`, `WARNING`,
  `BLOCKING_ERROR` und `INTERNAL_ERROR`; insbesondere muss klar sein, wann
  kein G-Code entstehen darf. Vollstaendig unimplementiert (`checks.py`s
  `ValidationError` ist nur ein `Tuple[int, str]`-Typalias, keine
  Klassenhierarchie) - eigenstaendige Entwurfsentscheidung mit
  projektweiter Auswirkung, verdient eigene Klaerung vor der Umsetzung.
  0.9.0-Scope-Audit 2026-09-21: heute wird "kein G-Code bei ungueltigen
  Daten" bereits fallweise durch harte `ValueError`s durchgesetzt
  (`contour_logic.py`, `validate_finite_data()`) - keine Funktionsluecke
  bis zur spaeteren Taxonomie-Einfuehrung. Kein 0.9.0-Blocker.

### 4. Bedienbarkeit und Wiederherstellung

0.9.0-Scope-Audit 2026-09-21 (folgt auf die Bestandsaufnahme 2026-09-20):
Undo/Redo und Autosave sind beide vollstaendig unimplementiert und beide
**kein 0.9.0-Blocker** - Entscheidung getroffen, keines von beiden ist
Teil des 0.9.0-Umfangs. Beide bleiben eigenstaendige, optionale
zukuenftige Features ohne festes Versionsziel; Autosave mit deutlich
staerkerer sachlicher Begruendung als Undo/Redo (siehe jeweils unten).

**Exit-Schutz bei ungespeicherten Aenderungen: umgesetzt 2026-09-21**
(nachgeholter Befund aus der Code-Pruefung 2026-09-21, bewusst getrennt von
Autosave behandelt - siehe unten). `warn_if_dirty()` lief bis dahin
ausschliesslich bei Tab-/Step-Wechsel (`ui_selection.py:46,110`), nie beim
Beenden. Geprueft wurde der tatsaechliche QtVCP-Lifecycle gegen den
installierten Quelltext (`/usr/bin/qtvcp`, `qtvcp/qt_makegui.py`):
`closing_cleanup__()` laeuft nachweislich erst NACH `QApplication.exec()`
und kann das Schliessen nicht mehr verhindern. `class_patch__()` dagegen
laeuft vor `APP.exec()` mit bereits vorhandenem `self.w` (dem echten
QtVCP-Fenster) und wird fuer Standalone (`qtvcp -c easystep`) und Embedded
(`EMBED_TAB_COMMAND=qtvcp -x {XID} -c easystep ...`) identisch aufgerufen,
da beide Modi denselben `/usr/bin/qtvcp`-Startpfad und dieselbe
QMainWindow-Klasse (`VCPWindow`/`MainPage`) durchlaufen - Embedded startet
laut `Drehbank.ini` als eigener `qtvcp`-Prozess mit `-x`, nicht als
Python-Kindwidget von QtDragon. Umgesetzt: `HandlerClass.class_patch__()`
ersetzt `self.w.closeEvent` durch `_handle_window_close_event()`
(`lathe_easystep_handler.py`), delegiert an
`ui_dirty.py::handle_window_close_event()`/
`confirm_discard_or_save_on_exit()`. Bei ungespeicherten Aenderungen
erscheint ein Speichern-/Verwerfen-/Abbrechen-Dialog (eigene Buttons statt
Qt-Standardbuttons, da deren Text nicht aus `.lng` kaeme): Speichern nutzt
den bestehenden `handle_save_changes()`-Pfad und schliesst nur, wenn
danach kein Dirty-State mehr besteht; Verwerfen laesst schliessen zu;
Abbrechen verhindert das Schliessen tatsaechlich; ohne Dirty-State
erscheint kein Dialog. Tests: `tests/test_class_patch_close_event.py`
(Stub, `class_patch__()`-Verdrahtung), `tests/test_unsaved_changes_on_exit_real_qt.py`
(Real-Qt, sieben Faelle inkl. echter `handle_save_changes()`-Integration).

**Autosave/Absturzwiederherstellung - weiterhin optionales zukuenftiges
Feature mit dokumentiertem Recovery-Nutzen, aber kein 0.9.0-Blocker:** der
Exit-Schutz oben deckt ausschliesslich den regulaeren Beendigungsvorgang
ab. Ein Panel-Absturz oder Stromausfall in der Werkstattumgebung verliert
ungespeicherte Aenderungen weiterhin vollstaendig und ohne jeden Hinweis -
dafuer waere eine getrennte, atomare Wiederherstellungsdatei noetig, keine
Erweiterung des Exit-Schutzes. Betrifft ausschliesslich ungespeicherte, im
Speicher gehaltene Aenderungen - bereits gespeicherte Programmdateien sind
durch LES-053/LES-054 bereits korrekt/deterministisch. Neues Feature,
nichts Bestehendes haengt davon ab; keine 0.9.0-Abnahmekriterien verlangen
es unabhaengig von der Feature-Entscheidung selbst.

- [ ] Autosave und Absturzwiederherstellung als getrennte, atomare
  Wiederherstellungsdatei vorsehen. Originaldateien duerfen niemals ungefragt
  ueberschrieben werden.
- [ ] Wiederherstellung, Versionskennung, unvollstaendige Autosaves und die
  Entscheidung des Anwenders im UI nachvollziehbar behandeln.
- [ ] Autosave-Roundtrips erhalten alle fachlichen Daten und den korrekten
  Dirty-State (vormals als 0.9.0-Abnahmekriterium unter LES-052 gefuehrt -
  hierher verschoben, da abhaengig von dieser Feature-Entscheidung).

**Undo/Redo - optionales zukuenftiges Feature, Ziel 1.0.0 oder spaeter:**
schwaecher begruendet als Autosave - der bestehende Workflow erzwingt
bereits explizites Speichern (`handle_save_changes()`/LES-047-
Verknuepfungszwang fuer Step-Dateien), eine nicht gespeicherte Fehleingabe
wird durch Nicht-Speichern/Neuladen faktisch bereits "rueckgaengig
gemacht". Kein bekannter Datenverlust-Vorfall, der Undo/Redo erzwingt.

- [ ] Undo/Redo auf Modell- oder Command-Ebene entwerfen; Widget-Zustaende
  duerfen nicht die Undo-Historie bilden.
- [ ] Undo/Redo fuer Parameter-, Segment-, Step-, Werkzeug- und Preset-
  Aenderungen mit klarer Dirty-State-Behandlung testen.
- [ ] Undo-Roundtrips erhalten alle fachlichen Daten und den korrekten
  Dirty-State (vormals als 0.9.0-Abnahmekriterium unter LES-052 gefuehrt -
  hierher verschoben, da abhaengig von dieser Feature-Entscheidung).

### 5. Werkzeugdaten und technische Pruefung

Bestandsaufnahme 2026-09-17: `parse_tool_table()`/`Tool`/`ToolTableState`
existieren bereits (Parser, normalisierte Werkzeuge, Parse-Warnungen ueber
`missing_iso`/Duplikat-Log). Kleinste offene Teilluecke geschlossen:
unbekannte Tool-Tabellen-Token (alles ausser T/P/D/Q, z. B. X/Y/Z/R) wurden
bisher beim Parsen stillschweigend verworfen - jetzt in `Tool.
unknown_fields` erhalten (reine Datenerhaltung, noch keine Fachlogik liest
das Feld). `parse_tool_table()` hatte bislang ueberhaupt keine eigene
Testdatei (`tests/test_tool_table_parsing.py` neu).

**Dauerhaft ausgeschlossen (Sicherheitsregel, nutzerbestaetigt
2026-09-17):** Zurueckschreiben in die `tool.tbl`-Datei (oder wie auch
immer der Anwender seine Werkzeugtabelle nennt) selbst. Das Panel darf
LinuxCNC-Konfigurationsdateien ausschliesslich LESEN, niemals schreiben -
geschrieben wird ausschliesslich, was zum Programm/G-Code gehoert. Das ist
keine offene Scoping-Frage fuer spaeter, sondern eine feste Grenze. `Tool.
unknown_fields` bleibt bewusst reine Datenerhaltung ohne jeden
Schreibpfad.

Audit 2026-09-20: die ersten drei Punkte sind bereits erfuellt, keine
offenen Punkte mehr.

- Werkzeugtabelle als eigene Domaene gekapselt: `parse_tool_table()`/
  `Tool`/`ToolTableState` (`tools.py`, `tool_table_state.py`) - Parser,
  Normalisierung, Warnungen, ausschliesslich lesend (siehe
  Sicherheitsregel oben).
- Werkzeugdaten (`tools.py`), Werkzeuggeometrie-Pruefung (`checks.py`) und
  Werkzeugdarstellung (`tool_logic.py`/`tool_visuals.py`) sind bereits
  strukturell getrennte Module. Die urspruengliche Begruendung ("Grundlage
  fuer die offenen LES-032-Pruefungen") ist zudem ueberholt, seit LES-032
  Abschnitt 1 als mit der offiziellen `tool.tbl` nicht loesbar geschlossen
  wurde.
- Pruefung gespeicherter erwarteter Werkzeugmerkmale gegen die aktuelle
  Werkzeugtabelle: bereits umgesetzt, siehe LES-032 Abschnitt 2
  (`tools.py::build_tool_snapshot()`,
  `checks.py::_check_tool_matches_snapshot()`) - kein eigener Punkt mehr
  hier, um die Aufgabe nicht doppelt zu fuehren.

- [ ] **(optionales zukuenftiges Feature, Ziel 1.0.0 oder spaeter)** einen
  technischen Pruefbericht pro Programm vorsehen: Werkzeuge, Grenzen,
  Futter-Sperrzone, XRI/XRA, Vorschub/Drehzahl, Warnungen und verwendete
  G-Code-Strategien. Neues Feature, existiert bisher nicht. 0.9.0-Scope-
  Audit 2026-09-21: projektweite Suche findet keine einzige bestehende
  Referenz auf einen solchen Bericht - vollstaendig gruenes Feld, nichts
  Bestehendes haengt davon ab. Kein 0.9.0-Blocker.

### Abnahme fuer LES-052

Audit 2026-09-20 bereits erfuellt, kein offener Punkt mehr:

- gleicher Programmzustand und identischer G-Code bei mindestens zwei
  Darstellungs-/Ressourcensaetzen
  (`test_switching_tool_visual_resource_never_affects_generated_gcode`,
  `tests/test_tool_preview_layout.py`, alle Beispielprogramme).
- fehlende optionale Ressource fuehrt zu sichtbarer Diagnose, aber nicht zu
  geaendertem G-Code oder verlorenen Daten
  (`test_missing_resource_has_visible_diagnostic_and_safe_fallback`,
  `test_changing_visual_set_cannot_mutate_tool_data`,
  `tests/test_tool_visual_provider.py`).
- Save/Load-Anteil der Roundtrip-Anforderung: durch LES-053/LES-054
  abgedeckt (`tests/test_save_load_roundtrip.py`,
  `tests/test_deterministic_generation.py`,
  `tests/test_format_versioning.py`).
- Stub-Qt- und Real-Qt-Suite sowie Embedded-/Standalone-Start bestehen:
  Dauerbedingung, aktuell erfuellt (968 Stub-/131 Real-Qt-Tests gruen) -
  kein einmalig abhakbarer Punkt, sondern Standard-Gate fuer jede Aenderung.
- Dedizierter Test, dass der Dirty-State nach `handle_load_program()`/
  `handle_save_program()` korrekt geleert wird bzw. bei einem Fehlschlag
  NICHT faelschlich sauber wird: `tests/test_dirty_state_load_save_contract.py`
  (Audit/Ergaenzung 2026-09-20). Vier Faelle: erfolgreiches "Programm
  laden" leert Programm- UND Step-Dirty vollstaendig; ein ungueltiges
  Programm (fehlende Version) laesst einen vorher bestehenden Dirty-Zustand
  unveraendert; erfolgreiches "Programm speichern" macht `has_unsaved_
  changes()` sauber; ein fehlschlagendes "Programm speichern" (Exception
  beim Schreiben) laesst den Dirty-Zustand unveraendert (kein falsches
  "sauber").
- Beim selben Audit gefundener Fehler behoben (2026-09-20): "Step laden"
  (`handle_load_step()`, `lathe_easystep/ui_persistence.py`) rief nach
  erfolgreichem Einfuegen faelschlich `handler._clear_dirty_state()` auf
  und loeschte damit JEDEN bestehenden Dirty-Zustand statt nur die neue
  Strukturaenderung zu markieren. Fix: derselbe Aufruf markiert jetzt
  `handler._mark_program_structure_dirty()` - analog zur bereits korrekten
  "Operation hinzufuegen" (`handle_add_operation()`). `_insert_loaded_
  operation()` selbst war bereits korrekt (markiert den neu geladenen Step
  zu Recht als sauber relativ zu SEINER EIGENEN Datei) und blieb
  unveraendert. Regressionsabgesichert durch
  `test_load_step_into_dirty_program_preserves_preexisting_dirty_state`
  und `test_load_step_into_clean_program_marks_program_dirty`
  (`tests/test_dirty_state_load_save_contract.py`), beide vor dem Fix rot.

0.9.0-Scope-Audit 2026-09-21: die vormals hier gefuehrten Undo-/Autosave-
Roundtrip-Kriterien sind zu Abschnitt 4 verschoben (sie haengen an der
dortigen, noch offenen Feature-Entscheidung, nicht an bestehendem 0.9.0-
Umfang - siehe dort). Damit ist "Abnahme fuer LES-052" fuer 0.9.0
vollstaendig erfuellt, kein offener Punkt mehr.

(Die frueher hier zusaetzlich gefuehrte Regel "bei Generator-/
Fahrwegaenderungen Referenzen/NGC/rs274/SIM ausfuehren" ist entfernt - sie
duplizierte die bereits bestehenden globalen "Abschlussregeln fuer
Aenderungen" am Ende dieser Datei.)

## LES-053 Programm-/Step-Dateiformat versionieren

Umgesetzt 2026-09-18 (Details im Changelog). Zentrale Versionierung/Migration
in `storage.py`: `CURRENT_FORMAT_VERSION = 2` (der JSON-Schluessel heisst
weiterhin `"version"`, wie schon vor LES-053 - keine Umbenennung, um
bestehende `.lse`-Dateien nicht anzufassen), `_migrate_v1_to_v2()`,
`_MIGRATIONS` (Versionsnummer -> Migrationsfunktion) und der einzige
Einstiegspunkt `_migrate_to_current()`. Programmdateien (`parse_program_
payload()`) und Step-Dateien (`parse_step_payload()`, neu - Step-Dateien
hatten vorher ueberhaupt kein Versionsfeld) laufen beide durch dieselbe
Migrationskette.

- [x] Versionsfeld in Programm- **und** Step-Dateien - Step-Dateien hatten
  vorher gar keins (Audit-Fund 2026-09-18). `write_step_file()` und der
  Step-Resave in `handle_save_changes()` schreiben jetzt `version: 2`.
- [x] Migration zentral definiert: `v1 -> v2` real umgesetzt (siehe LES-032
  unten - der Werkzeug-Snapshot ist ihr erster echter Anwendungsfall). Eine
  `v2 -> v3`-Migration existiert NICHT, da aktuell keine v3-relevante
  Formataenderung ansteht - der Mechanismus (`_MIGRATIONS`-Dict) traegt eine
  weitere Migration bei Bedarf ohne Strukturaenderung.
- [x] kein Format-Raten: `_migrate_to_current()` ist der einzige
  Einstiegspunkt fuer beide Dateiarten; Ausnahme bewusst dokumentiert (siehe
  unten).
- [x] Roundtrip-Tests fuer die unterstuetzte Altversion (v1) ergaenzt
  (`tests/test_format_versioning.py`), inkl. Save-\>Load-\>Save fuer v2.
- [x] unbekannte neuere Versionen sauber abgelehnt, mit eigener,
  unterscheidbarer Fehlermeldung (nicht mehr derselbe generische Text wie
  fuer jeden anderen Fehlerfall).
- [x] Migrationen ueberschreiben die Quelldatei nicht ungefragt - jeder
  Migrationsschritt arbeitet auf `deepcopy()`, getestet dass Laden einer
  alten Datei nichts auf die Platte zurueckschreibt.

**Bewusste Ausnahme vom "kein Format-Raten"-Grundsatz, nicht versehentlich:**
eine fehlende Version wird nur bei Step-Dateien (nicht bei Programmdateien)
stillschweigend als historisches Step-v1 behandelt - das ist das einzige
Step-Dateiformat, das je geschrieben wurde (vor LES-053 gab es dort gar kein
Versionsfeld), keine Erkennung anhand mehrerer moeglicher Formen. Fehlt die
Version in einer Programmdatei, wird das weiterhin abgelehnt - gueltige
`.lse`-Programme hatten schon vor Format v2 immer eine Version.

Der beim Audit gefundene Fehlerpfad in `handle_load_step()` (ungueltige
Step-Daten propagierten dort bisher ungefangen) ist mitbehoben: der neue
Ladeweg ueber `parse_step_payload()` ist jetzt in dasselbe `except
ValueError` eingefasst wie `_step_data_to_operation()`.

Ziel 0.9.0 erreicht (veroeffentlicht 2026-09-21); bleibt verpflichtendes
1.0.0-Gate.

## LES-054 Deterministische Programmerzeugung

Umgesetzt 2026-09-20 (Details im Changelog). Aus denselben normalisierten
Programmdaten entsteht nachweislich unabhaengig von Eingabeweg, Sprache,
Vorschau, Theme sowie Embedded-/Standalone-Betrieb derselbe fachlich
identische G-Code.

- [x] deterministische Erzeugung als expliziter Vertrag dokumentiert - als
  Moduldocstring in `tests/test_deterministic_generation.py`, direkt an
  den Nachweisen statt als separates, driftendes Prosadokument.
- [x] Eingabe -> Speichern -> Laden -> Erzeugen als Regression getestet -
  auf tatsaechlicher G-Code-Ebene (nicht nur Datenaequivalenz wie im
  schon vorhandenen `test_example_programs_roundtrip_through_program_payload`),
  zusaetzlich fuer Format-v1-Migration gegen nativen v2-Zustand (LES-053).
- [x] Erzeugen -> Vorschau/Theme-/Sprachwechsel -> Erzeugen als Regression
  getestet - Vorschau und Theme/Ressourcen waren bereits abgedeckt
  (`test_gcode_unaffected_by_preview_widget_rendering_cache`,
  `test_switching_tool_visual_resource_never_affects_generated_gcode`);
  Sprachwechsel war bisher nur als "Kommentare unterscheiden sich"
  getestet, nicht als "nur Kommentare unterscheiden sich" - ergaenzt.
- [x] Embedded und Standalone gegen dieselben normalisierten Daten
  geprueft - `build_gcode_lines()` liest nachweislich nirgends
  `root_widget`, einzige strukturelle Embedded-/Standalone-Differenz.
- [x] G-Code-Vergleiche auf fachlicher Ebene: alle neuen/bestehenden
  Nachweise vergleichen generierten G-Code (bzw. dessen technischen Anteil
  ohne Kommentartext), nicht UI-/Widget-Zustaende.

Keine Abweichung gefunden - alle vier neuen Regressionen bestanden bereits
beim ersten Lauf. Geprueft und als unproblematisch bestaetigt: `id()`-
basierte interne Korrelation in `gcode_program.py` wird nur fuer
Mitgliedschafts-/Lookup-Pruefungen innerhalb eines Generatorlaufs
verwendet, nie fuer eine die Ausgabe beeinflussende Iterationsreihenfolge.

Ziel 0.9.0 erreicht (veroeffentlicht 2026-09-21); bleibt Gate fuer die
1.0.0-Abnahme.

## LES-055 Maschinenprofil-Identitaet und Kompatibilitaet

Ein gespeichertes Programm muss erkennen lassen, fuer welches Maschinenprofil
es erstellt wurde. Das Profil umfasst mindestens Achsgrenzen,
Werkzeugwechselpunkt, Futter-/Sperrzonen, X/Z-Konvention und
Drehzahlgrenzen.

- [ ] stabile Identitaet und Version fuer Maschinenprofile definieren.
- [ ] verwendetes Profil in Programm- oder Laufmetadaten speichern.
- [ ] Abweichung zwischen gespeichertem und aktuellem Profil erkennen und
  nachvollziehbar melden.
- [ ] Kompatibilitaetspruefung fuer sicherheitsrelevante Profilparameter
  spezifizieren; eine harte Sperre ist gesondert zu entscheiden.
- [ ] positive, inkompatible und fehlende Profilfaelle testen.

Ziel: 1.0.0.

## LES-044 Vorschau und Darstellung

Audit 2026-09-18 gegen den aktuellen `dev`-Stand: die Qt-freie
Geometrieplanung ist fuer Navigation, Raster, Pfade, Sperrzonen und
Vorderansicht weitgehend umgesetzt. Farb-/Stil-Datenvertraege fuer das
Preview-Widget sind vollstaendig ausgelagert (siehe LES-051). Bereits als
duenne Qt-Adapter auf Qt-freie Funktionen delegiert (`preview_geometry.py`/
`contour_logic.py`, alle in `preview_widget.py`): `_sample_arc` →
`sample_preview_arc`, `primitives_to_points` →
`preview_primitives_to_points`, `_interp_x_at_z`/`_interp_x_hits_at_z`,
`_path_hits_at_slice`, `_front_operation_side`, `_front_slice_profile`,
`_front_reference_diameter`, `_apply_side_navigation` →
`apply_side_navigation`, das Kreis-Layout in `_paint_slice_view()` →
`circular_view_layout`.

Die `except Exception`-Fallbacks in `preview_widget.py`/`ui_preview.py`
wurden einzeln bewertet und, wo fachlich moeglich, auf erwartete
Ausnahmetypen begrenzt (Details im Changelog). Aktueller Codebestand
(Audit 2026-09-18, per Vorkommenszaehlung statt der Changelog-Prosa
mehrerer Teilschritte vom selben Tag): 10 `except Exception` verbleiben
bewusst breit, jede mit `# LES-044:`-Begruendungskommentar -
`preview_widget.py:277,287` (`set_slice_z`: `sliceChanged.emit()`/
Fallback-Callback rufen beliebigen Fremdcode auf), `preview_widget.py:
676,689,742,895,913,917` (`paintEvent`-Sicherheitsnetz je Zeichenzweig -
eine unbehandelte Ausnahme dort stuerzt unter echtem PyQt5 den gesamten
Prozess ab, empirisch verifiziert), `ui_preview.py:349,376`
(`collect_preview_state`: Warnungs-Aggregation aus drei bzw. Rohteil-/
Rueckzugs-/Worklimit-/Sperrzonen-Vorschau aus vier unabhaengigen
Funktionen). Dieser Teil von LES-044 ist damit abgeschlossen; die frueher
hier genannte absolute Zahl ("36 von 40") war nicht mehr aktuell und wurde
entfernt.

`except Exception` ausserhalb von `preview_widget.py`/`ui_preview.py`
(z. B. `ui_header.py`, `ui_params.py`) betrifft keine Preview-Geometrie
und gehoert inhaltlich nicht zu "Vorschau und Darstellung" - dieser Punkt
wird jetzt ausschliesslich unter LES-052 Abschnitt 3 (projektweites
Fehlergrenzen-Aufraeumen) gefuehrt, nicht mehr hier.

**Technische Restbereinigung, verschoben auf 1.0.0/spaeter (kein
funktionaler Blocker fuer 0.9.0)** (kein daraus bekannter Fehler in
falscher/fehlender Preview-Geometrie). 0.9.0-Scope-Audit 2026-09-21
bestaetigt per Code-Pruefung: alle drei sind bereits reine, in sich
geschlossene Funktionen ohne Qt-/Handler-Kopplung - die Aufgabe ist
ausschliesslich Verschieben in eine andere Datei, keine
Verhaltensaenderung. LES-044 ist damit fuer 0.9.0 abgeschlossen:

- [ ] `_pixel_to_z()` (`preview_widget.py`) als Qt-freie Funktion nach
  `preview_geometry.py` auslagern (Pixel->Z-Ruecktransformation, reine
  Arithmetik, analog zum bereits extrahierten `apply_side_navigation`).
- [ ] die Eingabe-Normalisierung in `set_paths()` (`preview_widget.py`:
  Primitive-Dicts vs. Punktlisten, Float-Koerzion) als eigene Qt-freie
  Funktion auslagern statt sie direkt in der Widget-Methode zu halten.
- [ ] `_detect_preview_collision()` (`ui_preview.py`) nach
  `preview_geometry.py` verschieben - ist bereits eine reine Funktion ohne
  Qt-/Handler-Bezug, liegt aber noch am falschen Ort.

Jeden dieser Schritte weiterhin mit einem kleinen Stub-Test und einem
Real-Qt-Start pruefen (etablierte Praxis, siehe Changelog); bereits
abgeschlossene Vorschau-Pakete nicht erneut als offene Aufgaben
dokumentieren.

**ID-only-Vollaudit 2026-09-21, erster Durchgang: behoben.** Die
Vorschau-Canvas-Beschriftung war Qt-frei-sprachunwissend und dauerhaft
Deutsch (`preview_widget.py` importierte `TRANSLATIONS` an keiner Stelle).
Umgesetzt: `ViewState.language` (`view_state.py`) plus `language`-Property
auf `LathePreviewWidget`, gesetzt ueber `PreviewView.apply_paths()`
(`ui_preview_view.py`) und bei Sprachumschaltung ueber
`_apply_language_texts()` -> `_refresh_preview()`
(`lathe_easystep_handler.py`). `LEGEND_ENTRIES`/`STATUS_BOX_STYLE`
(`preview_geometry.py`) halten jetzt `label_key`/`header_key` statt
Literaltext (Modul bleibt Qt-frei, Aufloesung erst in
`preview_widget.py`); die gezeichneten Labels ("Schnitt bei Z = ...",
"Vorderansicht bei Z = ...", "D final:", "D max:", "Schnitt Z ...",
"Legende") sowie `get_machine_limit_warnings()` (`gcode_safety.py`, auch
in G-Code-`(WARN: ...)`-Kommentaren, siehe `gcode_program.py:361`) nutzen
jetzt `TRANSLATIONS.tr()`/`gcode_comment()` mit neuen `runtime.preview.*`/
`gcode.comment.limit_warning_*`-Schluesseln in allen drei Sprachdateien.
Ebenfalls behoben: `ui_persistence.py:220,330` (roher `str(exc)` bei
ungueltigen Step-/Programm-Dateien) nutzen jetzt `format_user_error()` mit
neuem `fallback_title` (`message.step.load_failed`/bereits vorhandenem
`message.program.load_failed`); `format_user_error()`s letzter Fallback
ohne `fallback_title`/`op_number` gibt nicht mehr rohen `detail` zurueck,
sondern `TRANSLATIONS.tr("message.generic_error", lang).format(detail=...)`
(`ui_messages.py`). Nicht betroffen/kein Verstoss: die Achsbeschriftungen
"X"/"Z"/"XZ" (`preview_widget.py`, `ui_contour.py:387`,
`ui_operations.py:178`) sind technische, sprachunabhaengige
Achs-/Bewegungscodes, keine Uebersetzungsfaelle.

**ID-only-Vollaudit 2026-09-21, zweiter Durchgang: weiterer Befund,
inzwischen ebenfalls behoben.** Die Vorschau-Statusbox zeigte laut
`ui_preview.py:361-364` zwei weitere, unabhaengige Warnungsquellen mit
hartkodiertem Text, die im ersten Durchgang nicht mitverfolgt wurden:
`checks.py::validate_program_setup()` (ca. 24 Stellen ueber
`_check_drill_before_internal_machining()`, `_check_duplicate_operations()`,
`_check_tool_kind_matches_operation()`, `_check_tool_width_matches_operation()`,
`_check_tool_matches_snapshot()`, `_check_groove_reaches_chuck_no_go_zone()`
sowie mehrere Inline-Pruefungen fuer Gewinde/DIN-Freistich/Einstich, auch
in G-Code-`(WARN: ...)`-Kommentaren via `gcode_program.py:231,363`) und
`tool_logic.py::radius_warning_details()` (eine Stelle, nur UI-Statusbox).

Umgesetzt: **stabile Meldungs-IDs plus Parameter statt fertiger Saetze**,
da dieselben Ergebnisse technisch weiterverarbeitet werden (rund ein
Dutzend Tests filtern/vergleichen Warnungen inhaltlich, z. B.
`tests/test_tool_kind_mismatch_check.py`). `checks.py::CheckWarning`
(`{"key": str, "params": dict}`) plus `checks.py::format_warning()` als
zentrale Uebersetzungsgrenze (nutzt `gcode_comment()` - dieselbe Qt-freie
`.lng`-Mechanik wie der Rest der Generatorpipeline, `checks.py` bleibt
Qt-frei). `radius_warning_details()` liefert dieselbe Struktur.
`gcode_program.py`/`ui_preview.py` uebersetzen erst beim Einbetten
(G-Code-Kommentar bzw. Vorschau-Statusbox, mit `current_language(handler)`).
Alle betroffenen Tests (9 Dateien) von Substring- auf Key-/Parameter-
Vergleiche umgestellt. 47 neue `.lng`-Schluessel (`warning.*`, `optype.*`,
`tool.kind.*`, `field.*`) in allen drei Sprachen, Regressionstests in
`tests/test_checks_warning_translation.py` und
`tests/test_gcode_comments_are_language_dependent.py`.

**Dritter Durchgang (repo-weiter Vollaudit, nicht nur die bekannten
Funktionen): zwei weitere, kleinere Funde, ebenfalls behoben.**
`gcode_drill.py` (Retract-unter-safe_z-Warnung, `"... verwende safe_z"`)
und `gcode_safety.py::get_approach_warnings()` (drei Meldungen: Startpunkt
im Rohteil/in der Futter-Sperrzone, Rueckzugsebene schneidet Futterbereich,
nur in G-Code-Kommentare eingebettet, keine UI-Statusbox) nutzten
hartkodiertes Deutsch ohne jeden `.lng`-Bezug. Keine Weiterverarbeitung
durch Tests (nur Substring-Pruefung des unveraenderten Default-Texts),
daher direkt via `gcode_comment()` uebersetzt (analog zu
`get_machine_limit_warnings()`), keine Teststruktur-Aenderung noetig.
`ui_groove.py::render_groove_diagrams()` zeichnete das Label "Stirn"
(Einstich-/Abstich-Lagediagramm) fest Deutsch - neuer Schluessel
`runtime.groove.label_face`. Referenzregeneration (kein Diff) und
12+43-rs274-Lauf danach wiederholt, da G-Code-Kommentartext betroffen war.

Als Nicht-Verstoss geprueft und bewusst ausgenommen (kein Fix noetig):
`checks.py::validate_contour()` und `tool_logic.py::
collect_tool_orientation_warnings()` enthalten ebenfalls hartkodiertes
Deutsch, sind aber toter Code - projektweit nicht aufgerufen (verifiziert
per Grep ueber `lathe_easystep/`, `lathe_easystep_handler.py`, `tests/`),
erreichen also nie einen Nutzer. `contour_logic.py::
validate_contour_segments_for_profile()`s Fehlertexte gehen ausschliesslich
in `handler._log(...)` (interne Logs, per Definition von der ID-only-Regel
ausgenommen). Technische Bezeichner wie "X"/"Z"/"XZ", "ID"/"OD", "mm"/
"inch", Werkzeugnummern/-radien/ISO-Codes und "WARN"/"Step" als feste
G-Code-Kommentarpraefixe bleiben unveraendert sprachinvariant - keine
UI-Prosa.

**Ergebnis: keine bekannte sichtbare UI-Prosa mehr ausserhalb der
`.lng`-Dateien.** Details zum tatsaechlichen repo-weiten Pruefumfang siehe
CHANGELOG.md.

**Sprach-Verdrahtungsluecke (separater, nicht ID-only-bezogener
Nebenbefund derselben Pruefung): behoben 2026-09-22.**
`settings["lang"]` wurde im echten, Handler-getriebenen
"Programm erzeugen"-Pfad nirgends gesetzt (`ui_header.py::
collect_program_header()` liefert keinen `lang`-Schluessel) -
`gcode_comment()` fiel dadurch in der laufenden UI immer auf Deutsch
zurueck, unabhaengig von der gewaehlten UI-Sprache, obwohl LES-044
(2026-09-14) genau das als Ziel dokumentiert und auf Funktionsebene bereits
korrekt testete. War keine ID-only-Regelverletzung (der Text kam korrekt
aus `.lng`, nur die Sprachauswahl selbst erreichte den Aufrufer nicht).

Datenfluss geprueft: `ui_flow.py::build_gcode_lines()` ist der alleinige
reale Aufrufpfad (`write_gcode_file()` -> `handler._build_gcode_lines()`
-> `build_gcode_lines()` -> `handler.model.generate_gcode()`) - hier und
nur hier wird `handler.model.program_settings` aus
`_collect_program_header()` aufgebaut. Kleinste Korrektur: eine Zeile,
`handler.model.program_settings["lang"] = current_language(handler)`
(bestehender `ui_helpers.py`-Wrapper um `_current_language_code()`, kein
neuer Sprachzustand). `current_language()` faengt fehlendes Handler-Setup
bereits ab (Fallback "de"), dadurch auch fuer synthetische Test-Handler
ohne Widget-Baum sicher.

Bewusst NICHT persistiert: `build_program_data()`
(Speicherpfad fuer `.lse`) ruft `_collect_program_header()` unabhaengig
und ohne "lang" erneut auf, statt `handler.model.program_settings`
wiederzuverwenden - gespeicherte Programme werden dadurch nicht
sprachabhaengig, die jeweils aktuelle UI-Sprache gilt beim Erzeugen.
`numeric.py::_TEXT_KEYS` um `"lang"` ergaenzt (rein deklarativ - ein
Sprachcode wird nie als Zahl fehlinterpretiert, aber explizit statt
zufaellig ueber den String-Parse-Fallback abgesichert).

Regressionstests: `tests/test_gcode_language_wiring.py` (6 Faelle) treibt
den echten `build_gcode_lines()`-Pfad direkt an - DE/EN/ES-Kommentare,
Sprachwechsel ohne Programmneuladen zwischen zwei Aufrufen desselben
Handlers, technische G-Code-Struktur (Zeilen ohne `(...)`-Kommentare)
bleibt zwischen den Sprachen byte-identisch, sowie der explizite
Nicht-Persistenz-Nachweis gegen `build_program_data()`.

## LES-032 Werkzeuggeometrie

Werkzeugnummer, Radius, ISO-Code, Orientierung und Stechbreite werden bereits
aus dem normalisierten `Tool`-Datensatz verwendet. Die Q-basierte Innen-/
Aussenableitung ist bewusst verworfen; Details stehen im Changelog.

### 1. Werkzeughuelle / Bohrstangengeometrie

**Dauerhaft abgeschlossen - mit der offiziellen LinuxCNC-`tool.tbl` nicht
loesbar (Audit 2026-09-18/2026-09-20 gegen `dev`, kein offener Punkt mehr,
kein spaeter erneut zu pruefender Punkt):**

LatheEasyStep verwendet ausschliesslich die offizielle LinuxCNC-`tool.tbl`
als Werkzeugdatenquelle. Die dort verfuegbaren Drehwerkzeug-Felder D, I, J
und Q enthalten laut offizieller LinuxCNC-Dokumentation nachweislich keine
Information ueber Schaftdurchmesser, Schaftlaenge oder Halterausladung: D
ist der Kompensationsradius (bereits fuer die Schneidennase vergeben,
groessenordnungsmaessig ohnehin die falsche Groesse fuer einen
Bohrstangenschaft), I/J ("front angle"/"back angle") sind reine
Winkelangaben zur Schneidkantenform ohne Laengeninformation und laut
LinuxCNC-Doku nicht einmal in die eigene Kompensations-/Gouge-Pruefung des
Interpreters einbezogen, Q ist ein diskreter Orientierungscode. Die
uebrigen offiziellen Tabellenfelder (X/Y/Z/A/B/C/U/V/W) sind
Werkzeug-/TCP-Offsets und duerfen dafuer nicht zweckentfremdet werden. In
der real genutzten `Drehbank/tool.tbl` sind I und J bei allen Eintraegen
zusaetzlich durchgehend 0.

Da keine proprietaeren Zusatzdateien, Kommentarkonventionen oder
erfundenen Defaultwerte eingefuehrt werden, ist eine belastbare
Werkzeughuellen-/Bohrstangen-Kollisionspruefung mit der verfuegbaren
Datenquelle nicht moeglich - nicht als Zwischenstand, sondern als
strukturelle Grenze des offiziellen Tabellenformats selbst.

Unveraendert bestehen bleiben: die punktfoermige Rueckzugs-/
Sperrzonenpruefung fuer alle Operationstypen (`validate_chuck_segment()`,
`gcode_safety.py` - das Werkzeug wird dabei ausdruecklich als Punkt
behandelt) sowie die echte, geometriebasierte Kollisionspruefung mit
realer Werkzeugbreite fuer Einstich-/Abstechwerkzeuge
(`_check_groove_reaches_chuck_no_go_zone()`, `checks.py`, nutzt
`Tool.insert_width_mm` - dieser Wert kommt aus dem ISO-Einsatzcode im
Kommentar, nicht aus D/I/J/Q). Die innen liegende Rueckzugsebene XRI
(`resolve_internal_safe_x()`, `gcode_utils.py`) bleibt dauerhaft eine reine
Anwenderangabe ohne Gegenpruefung gegen die tatsaechliche
Bohrstangenschaftgeometrie.

`I`/`J` landen weiterhin unveraendert in `Tool.unknown_fields`
(`tools.py:229`) und werden von keiner Fachfunktion gelesen - das ist
korrekt und erfordert keine Codeaenderung, solange diese Felder fuer keine
Fachfunktion benoetigt werden.

### 2. Aenderung von Werkzeugmerkmalen seit Programmerstellung

Umgesetzt 2026-09-18, zusammen mit LES-053 als deren erster realer
`v1 -> v2`-Anwendungsfall (Details im Changelog). Genau wie im Audit
vorgeschlagen: `tools.py::build_tool_snapshot()` erzeugt einen minimalen,
abgeleiteten Schnappschuss (nur `radius_mm`, `orientation`/Q,
`insert_width_mm` - NICHT die volle Tooltable-Zeile) fuer jede Operation
mit Werkzeugbezug, geschrieben beim Speichern
(`persistence.py::operation_to_step_data()`, ueber alle drei Speicherpfade
Gesamtprogramm, einzelne Step-Datei und Step-Resave bei "Aenderungen
speichern") aus der dann aktuell geladenen Tabelle in
`op.params["tool_snapshot"]`. `checks.py::_check_tool_matches_snapshot()`
(neu, aus `validate_program_setup()` aufgerufen) vergleicht das gegen die
beim Laden/Erzeugen aktuell geladene Tabelle - nur Warnung, nie eine
Sperre. Erkennt geaenderten Radius, geaenderte Orientierung und geaenderte
Einstichbreite je einzeln.

- Operationen ohne Snapshot (aus Format v1 migrierte Altprogramme) werden
  bewusst uebersprungen - kein historischer Vergleichswert vorhanden, siehe
  `storage.py::_migrate_v1_to_v2()` (erzeugt ausdruecklich KEINEN
  nachtraeglichen Snapshot aus der aktuellen Tabelle).
- Fehlt das Werkzeug in der aktuellen Tabelle komplett, meldet weiterhin
  ausschliesslich `validate_tool_table_completeness()` (LES-028) - keine
  Dopplung.
- Tests: `tests/test_tool_snapshot_check.py` (unveraendert/Radius/
  Orientierung/Breite geaendert, kein Snapshot, fehlendes Werkzeug).

Kein offener Punkt mehr fuer diesen Unterabschnitt.

## LES-043 Gegenspindel

Die nicht implementierten Bedienelemente bleiben sichtbar, aber gesperrt.

- [ ] separate Spezifikation erstellen: Operationen, Spindelsynchronisation,
  S3-Grenzen, Koordinatensysteme und Kollisionsmodell.
- [ ] LinuxCNC-SIM- und Maschinenkonzept fuer diese Spezifikation festlegen,
  bevor irgendeine Generatorimplementierung in LatheEasyStep beginnt.

## LES-030 Externe Maschinenverifikation

- [ ] unterschiedliche reale Drehmaschinen mit Achsgrenzen,
  Werkzeugwechselpositionen und Futterbauformen verifizieren.
- [ ] Referenzprogramme als formale Schnittstelle dokumentieren: Quelldatei,
  normalisierte Operationen, G-Code-Eigenschaften, `rs274`-, SIM- und
  Backplot-Ergebnis sowie gegebenenfalls Maschinenlauf.

Dieser Punkt ist mit der vorhandenen einzelnen QtDragon-SIM nicht abschliessbar
und blockiert die 0.8.0-Softwarebasis nicht.

## Spaetere Funktionen

- Keilnut ohne verbotene Makrovariablen neu implementieren.
- weitergehende Verzahnungs- und Gegenspindelfunktionen.
- weitere Maschinen-, Futter- und Werkzeugprofile.
- automatisierte LinuxCNC-SIM-Laeufe als dauerhafte Testinfrastruktur.

## Abschlussregeln fuer Aenderungen

1. Regression, die den alten Fehler oder die neue Grenze konkret abdeckt.
2. Voller Lauf von `python3 run_tests.py`, ohne unbegruendete Skips.
3. Bei Generatoraenderungen Referenzen regenerieren und Diff pruefen.
4. Statische NGC-Pruefung sowie nativer `rs274`-Lauf.
5. Bei UI-Aenderungen echtes PyQt5 sowie Embedded/Standalone pruefen.
6. Bei Fahrweg-/Modal-Aenderungen LinuxCNC-Backplot und AUTO-Trockenlauf.
7. Dokumentation und aktuelle Testzahlen synchron halten.
