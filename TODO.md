# TODO LatheEasyStep

Stand: 2026-09-17

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
- 948 Stub-Qt-Tests und 115 Tests mit echtem PyQt5, keine Skips.
- Zwoelf Referenzprogramme bestehen statische NGC-Pruefung und den nativen
  LinuxCNC-Interpreter (`rs274`); zusaetzlich bestehen 43 Matrixprogramme.
- Alle zwoelf Referenzen wurden in der QtDragon-SIM bis `M30` ausgefuehrt.
- Der Generator ist von Qt getrennt. Reiter, Step-Verwaltung und Vorschau
  liegen in eigenen UI-/Fachmodulen.

## Priorisierter Arbeitsindex

| ID | Prio | Aufgabe | Aufwand | Ziel |
|---|---|---|---|---|
| Release-Prozess | P1 | echten Release-Pfad testen, Manifest-Vollstaendigkeit absichern | S | vor 0.9.0 |
| LES-022 | P2 | vier verstreute Settings-Zustaende typisieren (kein bekannter Fehler, Rest laut Audit 2026-09-18 bereits umgesetzt/bewusst abgeschlossen) | S | 0.9.0 |
| LES-051 | P1 | Panel-Grundgeruest und Darstellungsadapter weiter entkoppeln | XL | 0.9.0 |
| LES-052 | P1 | Panel-Architektur, Zustandsmodell und Wiederherstellung planen/umsetzen | XL | 0.9.0 |
| LES-044 | P2 | drei kleine Qt-freie Restauslagerungen (kein bekannter Fehler, Rest laut Audit 2026-09-18 bereits umgesetzt) | S | 0.9.0 |
| LES-043 | P2 | Gegenspindelfunktion als separates Projekt spezifizieren | XL | separat |
| LES-030 | extern | weitere reale Maschinenprofile verifizieren | extern | offen |

## Release-Prozess

`RELEASE_POLICY.md` und `scripts/create_release.py` (mit `release_manifest.txt`)
wurden am 17.09.2026 eingefuehrt und bislang nur mit `--check` gegengeprueft
(reine Validierung, kein Schreibvorgang). Vor 0.9.0 noch offen:

- [ ] den tatsaechlich schreibenden Release-Pfad einmal vollstaendig
  durchspielen: `scripts/create_release.py` ohne `--check` fuer einen
  Wegwerf-/Test-Release ausfuehren, den erzeugten `main`-Commit und den
  Manifestvergleich pruefen, danach lokal zuruecksetzen (`git branch -f
  main <vorheriger main-Commit>`, temporaeren Worktree/Tag entfernen).
  Bisher wurde nur der lesende `--check`-Pfad unter Windows und Debian
  getestet.
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

**Technische Restarbeit (kein nachgewiesener funktionaler Fehler, daher
keine hohe Prioritaet):** vier Zustaende leben weiterhin als rohe
`settings["_..."]`-Schluessel statt in einem typisierten Objekt wie
`MotionState`/`SpindleState`. Jeder Wert wird konsistent gelesen/
geschrieben, keiner der vier zeigt einen aktuell nachweisbaren
funktionalen Fehler - eine Typisierung waere Architekturaufraeumen, keine
Fehlerbehebung:

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
Datenvertraege in `preview_geometry.py` ausgelagert. Offen bleiben
konfigurierbare Theme-Auswahl, Cache und Lebensdauer fuer `ToolVisualProvider`.

- [ ] den verbleibenden Handler-Kleber weiter reduzieren. Neue Fachlogik darf
  nicht in `lathe_easystep_handler.py` entstehen; UI-Fragmente sollen nur
  definieren, welche Views geladen werden, nicht deren Zustand selbst besitzen.
- [ ] weitere austauschbare Panelbereiche identifizieren. Preview-Canvas,
  Legende und Status-/Warnungsdarstellung sind als Farb-/Stil-Datenvertraege
  bereits umgesetzt (siehe oben); offen bleiben optionale Bedienelemente
  (z. B. Schnittansicht-/Ansicht-zuruecksetzen-Buttons) als austauschbare
  Komponenten ueber einen eigenen Datenvertrag.
- [ ] Shell- und Fragment-Laden fuer Standalone und Embedded mit einem
  definierten Ladevertrag absichern: Reihenfolge, Widget-Registrierung,
  Signalbindung, Fehlerbehandlung und Wiederholung duerfen nicht vom
  konkreten Skin oder Ressourcenpaket abhaengen.

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

- [ ] den Handler auf Bootstrap, Controller-Verbindungen und Kompatibilitaets-
  Wrapper begrenzen; neue Fachlogik gehoert in testbare Module unter
  `lathe_easystep/`.

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
(keine Architekturfrage): `handler._tool_visual_provider` wird in der
laufenden Anwendung nirgends auf ein echtes Theme-Verzeichnis gesetzt - es
greift also immer nur der prozedurale Fallback; lohnt sich ein echtes
grafisches Theme, oder ist das bewusst ausreichend?

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

- [ ] Aenderungen nach dem Ablauf Eingabe -> Normalisierung -> Validierung ->
  Modelluebernahme -> Dirty-State -> Preview/Warnungen ordnen - der obige
  Fund/Fix deckt nur den Rollback-Teil ab, nicht die vollstaendige
  Reihenfolge-Pruefung ueber alle Aenderungspfade.
- [ ] weitere Stellen mit demselben Muster (Modelluebernahme vor
  Validierung, kein Rollback bei Fehlschlag) suchen - `sync_form_to_
  operation()` war nur die eine gefundene, gezielt untersuchte Stelle.
- [ ] breite `except Exception`-Fallbacks in den betroffenen UI-Modulen
  durch definierte Fehlerklassen oder engere Fehlergrenzen ersetzen, ohne
  erwartete optionale Ressourcenfehler zu verschlucken. `preview_widget.py`/
  `ui_preview.py` sind dieser Aufgabe entwachsen - dort ist das bereits
  abgeschlossen (siehe LES-044). Projektweite Zaehlung (Audit 2026-09-18)
  ergab weiterhin ~400 Vorkommen in 40+ Dateien, u. a. `ui_header.py` (6)
  und `ui_params.py` (4) - deutlich groesser als der bisherige LES-044-
  Umfang, nicht in einem Rutsch angehen, sondern inkrementell oder
  explizit in Etappen zerlegen.
- [ ] Fehlerdiagnosen zentral sammeln und fuer Log, UI-Warnung und Tests
  strukturiert nutzbar machen - vollstaendig unimplementiert, eigene
  Entwurfsarbeit.
- [ ] Fehlerklassen vereinheitlichen: `INFO`, `WARNING`, `BLOCKING_ERROR` und
  `INTERNAL_ERROR`; insbesondere muss klar sein, wann kein G-Code entstehen
  darf. Vollstaendig unimplementiert (`checks.py`s `ValidationError` ist nur
  ein `Tuple[int, str]`-Typalias, keine Klassenhierarchie) - eigenstaendige
  Entwurfsentscheidung mit projektweiter Auswirkung, verdient eigene
  Klaerung vor der Umsetzung.

### 4. Bedienbarkeit und Wiederherstellung

- [ ] Undo/Redo auf Modell- oder Command-Ebene entwerfen; Widget-Zustaende
  duerfen nicht die Undo-Historie bilden.
- [ ] Undo/Redo fuer Parameter-, Segment-, Step-, Werkzeug- und Preset-
  Aenderungen mit klarer Dirty-State-Behandlung testen.
- [ ] Autosave und Absturzwiederherstellung als getrennte, atomare
  Wiederherstellungsdatei vorsehen. Originaldateien duerfen niemals ungefragt
  ueberschrieben werden.
- [ ] Wiederherstellung, Versionskennung, unvollstaendige Autosaves und die
  Entscheidung des Anwenders im UI nachvollziehbar behandeln.

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

- [ ] Werkzeugtabelle als eigene Domaene kapseln (Parser/Normalisierung/
  Warnungen sind vorhanden) - ausschliesslich lesend, kein
  Zurueckschreiben in die Datei (siehe Sicherheitsregel oben).
- [ ] Werkzeugdaten, Werkzeuggeometrie und Werkzeugdarstellung getrennt
  halten; dies bildet die Grundlage fuer die offenen LES-032-Pruefungen.
- [ ] beim Laden oder Erzeugen gespeicherte erwartete Werkzeugmerkmale gegen
  die aktuelle Werkzeugtabelle pruefen und erkennbare Abweichungen melden.
- [ ] einen technischen Pruefbericht pro Programm vorsehen: Werkzeuge,
  Grenzen, Futter-Sperrzone, XRI/XRA, Vorschub/Drehzahl, Warnungen und
  verwendete G-Code-Strategien.

### Abnahme fuer LES-052

- [ ] gleicher Programmzustand und identischer G-Code bei mindestens zwei
  Darstellungs-/Ressourcensaetzen.
- [ ] fehlende optionale Ressource fuehrt zu sichtbarer Diagnose, aber nicht
  zu geaendertem G-Code oder verlorenen Daten.
- [ ] Save/Load-, Undo/Redo- und Autosave-Roundtrips erhalten alle fachlichen
  Daten und den korrekten Dirty-State.
- [ ] Stub-Qt- und Real-Qt-Suite sowie Embedded-/Standalone-Start bestehen.
- [ ] bei Generator- oder Fahrwegaenderungen zusaetzlich Referenzen, statische
  NGC-Pruefung, `rs274` und erforderliche SIM-/Backplot-Nachweise aus den
  Abschlussregeln ausfuehren.

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

Ziel: 0.9.0, verpflichtendes 1.0.0-Gate.

## LES-054 Deterministische Programmerzeugung

Aus denselben normalisierten Programmdaten muss unabhaengig von Eingabeweg,
Sprache, Vorschau, Theme sowie Embedded-/Standalone-Betrieb derselbe fachlich
identische G-Code entstehen.

- [ ] deterministische Erzeugung als expliziten Vertrag dokumentieren.
- [ ] Eingabe -> Speichern -> Laden -> Erzeugen als Regression testen.
- [ ] Erzeugen -> Vorschau/Theme-/Sprachwechsel -> Erzeugen als Regression
  testen.
- [ ] Embedded und Standalone gegen dieselben normalisierten Daten pruefen.
- [ ] G-Code-Vergleiche auf fachlicher Ebene statt auf UI-Zustaenden aufbauen.

Ziel: 0.9.0, Gate fuer die 1.0.0-Abnahme.

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

**Technische Restbereinigung, kein funktionaler Blocker fuer 0.9.0** (kein
daraus bekannter Fehler in falscher/fehlender Preview-Geometrie):

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
