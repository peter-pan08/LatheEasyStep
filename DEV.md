# Developer Notes – Lathe EasyStep

## Projektziel
Lathe EasyStep soll ein **shop-floor-taugliches Drehpanel** sein, kein vollwertiges CAM.
Ziel ist:
- deterministische Bewegungen
- nachvollziehbare Geometrie
- minimale Überraschungen an der Maschine

## Release-Stand

- `v0.7.0` ist die lauffaehige Basis auf `main`.
- `dev` ist der aktuelle Entwicklungsstand fuer `v0.8.0`; `main` bleibt
  die stabile, lauffaehige Basis.
- Aktueller Teststand: `673 passed (Stub-Qt), 44 passed (Real-Qt), 0 skipped`.
- Der Stand umfasst Freistich-/Hinterschnitt-Backend, harte XRI-Grenzen,
  Dirty-State, Preview-Docking, explizite Toolchange-/Park-Koordinatensysteme,
  Rechts-/Linksgewinde, `rough_finish`, Realtest-Fixes und die geteilte UI.
- `lathe_easystep.ui` ist die Shell; die acht Bearbeitungsreiter liegen unter
  `lathe_easystep/ui_parts/` und werden durch `ui_split.py` geladen.
- `de.lng`, `en.lng` und `es.lng` besitzen jeweils 1.022 identische,
  nichtleere und eindeutige Schluessel.
- Offene Arbeiten und Release-Zuordnung werden verbindlich in
  `TODO.md` und `ROADMAP.md` gepflegt.

---

## Architektur-Überblick

- `lathe_easystep_handler.py`
  - QtVCP-`HandlerClass` und verbleibende Klebelogik
  - neue substanzielle Fachlogik gehoert in Module unter `lathe_easystep/`
- `lathe_easystep.ui`
  - Shell fuer Step-Liste, Tab-Container und Vorschau
- `lathe_easystep/ui_parts/*.ui`
  - getrennte Bearbeitungsreiter fuer Program, Face, Contour, Parting, Thread,
    Groove, Drill und Keyway
- `lathe_easystep/ui_split.py`
  - laedt die Teil-UIs beim Start in die Shell
- `lathe_easystep/gcode_*.py`, `contour_logic.py`, `contour_features.py`
  - produktive Generator- und Geometrielogik
UI und Toolpath-Logik sind bewusst getrennt.

## UI-/Spracharchitektur

- Fachliche Logik arbeitet mit technischen IDs und `currentData()`, nicht mit
  lokalisierten Anzeigetexten.
- Die aktiven Kataloge liegen unter `lathe_easystep/languages/*.lng`.
- Deutsch, Englisch und Spanisch besitzen aktuell jeweils 1.022 identische,
  nichtleere und eindeutige Schluessel.
- Sprachumschaltung und Tooltips wurden im eingebetteten Panel praktisch
  bestaetigt.
- `lathe_easystep/ui_static.py::load_ui_static_map()` scannte fuer die
  automatische Sprachumschaltung von "statischen" Widgets nur die
  Shell-Datei `lathe_easystep.ui`; seit der Aufteilung der acht Reiter in
  `ui_parts/*.ui` wurden deren Labels/Tooltips/Combo-Eintraege trotz
  vollstaendiger `.lng`-Uebersetzungen nie mehr angewendet. Behoben (LES-021):
  die Funktion scannt jetzt zusaetzlich alle `ui_parts/*.ui`-Dateien.
- `lathe_easystep/i18n/*.json` war vom aktiven `.lng`-Loader nie verwendet
  worden; nach Audit (keine verbleibenden Referenzen in Code, Tests oder
  `.ui`-Dateien) entfernt (LES-029).

## Test-Hinweise

- Auf dem nativen LinuxCNC-Rechner `/usr/bin/python3 run_tests.py` nutzen:
  System-Python besitzt PyQt5/qtpy, die lokale `.venv` derzeit nicht.
  Native rs274- und Simulationsbefunde fuer `11ee8b0`:
  `doc/NATIVE_VERIFICATION_2026-09-09.md`.

- LES-005: Der explizite innere Schlichtweg beginnt geometrisch bei
  `(XRI, Konturstart-Z)`. `_emit_finish_primitives(..., initial_pos=...)`
  kennt diesen realen Ausgangspunkt, sodass die erste Profilbewegung radial
  im Vorschub erfolgt und nicht als redundanter Punkt oder G0 ausgegeben
  wird. Kompensierte Einfahrwege werden im G7-Durchmessermass berechnet:
  `(Profilstart-X - XRI) / 2 > Werkzeugdurchmesser`, jeweils nach Rundung
  der ausgegebenen X-Koordinaten.
- Es gibt zwei Testwelten:
  - stub-basierte Suite ueber `tests/conftest.py`
  - echte PyQt5-Roundtrip-Tests wie `tests/test_slice_strategy_ui_roundtrip.py`
- Die Test-Infrastruktur wurde darauf gehaertet, dass Real-Qt-Tests die
  `qtpy`-Alias-Module in `sys.modules` temporaer ersetzen duerfen, ohne danach
  die restliche Stub-Suite zu zerlegen.
- Bei neuen Real-Qt-Tests darauf achten:
  - echte Module (`qtpy`, `qtpy.QtCore`, `qtpy.QtWidgets`, ggf. betroffene
    Projektmodule) vor dem Import gezielt aus `sys.modules` entfernen
  - danach keine stillschweigende Abhaengigkeit darauf einbauen, dass die
    Stub-Aliase unveraendert geblieben sind

Ausgegliederte Handler-Bestandteile (frueher direkt im Handler definiert):
- `lathe_easystep/preview_widget.py`
  - `LathePreviewWidget` (2D-Vorschau-Canvas, reines Qt-Paint-Widget ohne
    fachliche Logik). Als promoted Widget in `lathe_easystep.ui` weiterhin
    ueber `<header>lathe_easystep_handler</header>` referenziert - der Handler
    re-exportiert die Klasse per Import, das `.ui`-Customwidget muss dafuer
    nicht geaendert werden.
- `lathe_easystep/widget_resolver.py`
  - `WidgetResolver`/`WidgetResolveError`: robuste, rein Qt-baumbasierte
    Widget-Suche fuer Standalone- vs. eingebettetes Panel.
- `lathe_easystep/ui_params.py`
  - `setup_param_maps()` (mit Cache, siehe Performance-Hinweis unten) und
    `collect_params()` fuer die generische Feld-Sammlung pro Operationstyp.
- `lathe_easystep/ui_split.py`
  - Laufzeit-Lader fuer die ausgelagerten Reiter-UIs aus
    `lathe_easystep/ui_parts/`
- `lathe_easystep/ui_widget_lookup.py`
  - Widget-Bootstrapping: `register_known_widgets()`, `resolve_core_widgets_strict()`,
    `get_widget_by_name()`, `find_root_widget()`, `poll_for_widget()` u.a. -
    reine Widget-Lookup-Mechanik ohne fachliche Logik, vom Handler nur ueber
    gleichnamige, duenne Wrapper-Methoden aufgerufen

Gemeinsame Querschnittslogik:
- `lathe_easystep/ui_helpers.py`
  - robuster Sprachcode-Fallback
  - Uebersetzung mit Formatparametern
  - ID-stabile ComboBox-Befuellung
  - zentrale Zuordnung von Operationstypen zu Tab-Bezeichnungen
- `lathe_easystep/gcode_utils.py`
  - generische Float-/Integer-Parameter-Lookups
  - Werkzeugnummern-Lookup
  - gemeinsame Aufloesung der internen Safe-X-Position
  - zentrale Validierung harter Innen-X-Grenzen ueber `validate_internal_x_limit()`
  - `is_internal_side()`/`is_left_hand()`/`resolve_enum_index()`: robuste
    Interpretation von Combo-Werten, die seit der ID-only-Umstellung sowohl
    als String-ID als auch (Altdaten) als Zahl vorliegen koennen
- `lathe_easystep/ui_registry.py`
  - `PANEL_WIDGET_NAMES` (moegliche Root-Objektnamen je nach Embedding), neben
    den bestehenden Text-/Tooltip-/Combo-Item-Registries
- `lathe_easystep/motion_state.py` (LES-022)
  - `MotionState` (erste Etappe): zentraler, typisierter Bewegungszustand
    (zuletzt real erreichte X/Z-Position). Ersetzt die fruehere ad-hoc
    Ablage ueber `settings["_is_at_safe"/"_safe_x"/"_safe_z"]` in
    `gcode_safety.py` und `gcode_groove.py`. `gcode_safety._motion_state(settings)`
    liefert/legt die Instanz unter `settings["_motion"]` an (lazy, auch fuer
    Tests mit handgebauten Dicts ohne vorherige Initialisierung). Wird nach
    jedem Schruppdurchlauf in `gcode_roughing.py` explizit invalidiert
    (`clear()`), da Schnittbewegungen (G1/G2/G3) dort noch nicht
    feingranular mitgefuehrt werden.
  - `SpindleState` (zweite Etappe): CSS(G96)-Modalzustand (`pending`/
    `active`/`fixed_rpm`). Ersetzt `settings["_pending_css"/"_active_css"/
    "_css_fixed_rpm"]` in `activate_pending_css()`/`suspend_css()`/
    `append_tool_and_spindle()` (`gcode_safety.py`), analog ueber
    `gcode_safety._spindle_state(settings)` unter `settings["_spindle"]`.
  - Siehe TODO.md fuer die verbleibenden LES-022-Punkte (uebrige modale
    G/M-Codes, vollstaendiges Move-Tracking ueber Schnittbewegungen).

Lokale Kopien dieser Helfer sollen nicht erneut in UI- oder G-Code-Modulen
angelegt werden. Das fruehere Paket `lathe_easystep/contour/` war ungenutzt
und intern unvollstaendig und wurde entfernt; produktive Konturpfade laufen
ueber `contour_logic.py` und `contour_features.py`.

Die zuvor als naechste Kandidaten identifizierten Handler-Methoden mit
substanzieller Eigenlogik (`_collect_program_header`, `_collect_contour_segments`,
`_apply_thread_preset`/`_populate_thread_standard_options`,
`_get_widget_by_name`/`_resolve_core_widgets_strict`/`_register_known_widgets`,
`_set_tooltip_deep`/`_fallback_tooltip_text`) sind inzwischen alle ausgegliedert
(LES-020 abgeschlossen). Jede Extraktion wurde einzeln mit vollem Testlauf und
echtem PyQt5 (`uic.loadUi`) gegengeprueft. Weitere Kandidaten fuer zukuenftige
Pakete sind derzeit nicht konkret identifiziert (LES-020 bleibt als
Aufwandskategorie in `TODO.md`, falls neue Klebelogik im Handler entsteht).

---

## Kontur-Datenmodell
Konturen bestehen aus Segmenten mit:
- Punkt (X/Z)
- Kantentyp: none / chamfer / radius
- Kantenmaß
- bei Radius zusätzlich:
  - `arc_side`: auto / inner / outer
- optionalem Konturfeature:
  - `feature_type`: none / din_relief
  - `thread_size`
  - `orientation`: start / end
  - `internal` bzw. side

Die Kontur ist die **Quelle der Wahrheit** für:
- Vorschau
- Abspanlogik
- spätere G2/G3-Ausgabe
- Freistich-/Hinterschnitt-Ableitungen fuer Finish, Roughing und Feature-only

- `start_x`/`start_z` werden jetzt als erster Punkt übernommen, sodass die erste Segmentzeile tatsächlich eine Ecke erzeugt.
- `validate_contour_segments_for_profile` überprüft jede Zeile auf Nullsegmente, Winkel und erreichbare Kantenlängen; bei Fehlern wird die Vorschau geleert und der Benutzer sieht die Details im Log (die Funktion ist der Eingang zu G71/G70).
- `build_contour_variants()` liefert jetzt getrennt:
  - `finish_primitives`
  - `rough_primitives`
  - `feature_primitives`
  - passende Punktlisten fuer Generator und Tests

## DIN-Freistich / Hinterschnitt
- Standarddaten liegen zentral in `lathe_easystep/presets/din_relief_presets.py`.
- Ausbaustufe Stand `2026-07-09`: `M3` bis `M30`.
- Die Logik behandelt Freistich als Konturfeature der Fertiggeometrie, nicht als eigene Nut-Operation.
- Ein aktivierter automatischer Gewinde-Freistich wird aus der Gewindeoperation
  abgeleitet. `thread_overlap` positioniert das G76-Ende innerhalb des
  Freistichs; nur eine zylindrische Konturstrecke mit passendem Durchmesser
  darf die Geometrie aufnehmen. Ohne diese Zuordnung wird kein G-Code erzeugt.
- Bearbeitungsstrategie in `ABSPANEN` ist davon getrennt.
- Der Kontur-Editor speichert diese Daten jetzt direkt in den Segmentparametern und fuehrt sie durch Save/Load wieder in die UI zurueck.

## Preset-Architektur
- Gewinde-Presets liegen zentral in `lathe_easystep/presets/thread_presets.py`.
- DIN-Freistich-/Hinterschnitt-Presets liegen zentral in `lathe_easystep/presets/din_relief_presets.py`.
- UI, Generator und Validierung greifen nur noch ueber Helper zu, z. B.:
  - `get_thread_preset("M20")`
  - `get_din_relief_preset("M20", internal=False)`
  - `get_thread_with_relief("M20", internal=False)`

---

## Radien (Wichtiger Punkt)
Radien werden **nicht** als einfache Polylines verstanden, sondern als:
- echte Fillet-Geometrie zwischen zwei Geraden
- mit berechneten Tangentialpunkten
- und eindeutigem Kreismittelpunkt

Der aktuelle Stand erzeugt intern echte Arc-Geometrie. Der explizite
Schlichtweg erhaelt Radien bereits als G2/G3 in der G18-Ebene. Offen bleiben
move-based Roughing-/Fallback-Pfade, die Geometrie teilweise noch
linearisieren, sowie vollstaendige Arc-Intersections.

---

## Planen / FACE
- `build_face_primitives()` repräsentiert die OD-Ecke als echte Primitive (Linien + Arc), sodass the preview die Kante am Außendurchmesser direkt zeigt.
- Die Parameter `edge_type`, `edge_size` und das neue `edge_in_roughing` bestimmen, ob die Kante als Linie, Fase oder Radius modelliert wird und ob sie schon im letzten Roughing-Pass vorgearbeitet wird.
- In `gcode_for_face()` wird bei aktivierter Vorform im Schruppen konkret eine diagonal abgesprungene Fase (G1) bzw. ein Viertelkreis (G2/G3) erzeugt; ohne Platz oder Edge-Inhalte bleibt es beim bewährten geraden Abziehen.

---

## Abspanlogik
- Unterstuetzte Strategien: zyklusbasiert oder move-based, parallel zur jeweils gewaehlten Achsrichtung
- Kontur wird entlang X-Linien ausgewertet
- Sichere Anfahrt, Lead-in, Lead-out und Retract werden explizit erzeugt
- Rückzug X/Z erfolgt simultan (kein sequentielles „hochziehen“)
- Generator unterstuetzt jetzt fuer Hinterschnitt/Freistich:
  - `ignore`
  - `finish_only`
  - `separate`
  - `full`
- Generator dokumentiert jetzt explizit:
  - Strategie
  - Ausgabe-Praeferenz
  - Aufmass X/Z
  - Hinterschnitt-Modus
  - Fallback-Gruende
- `output_preference` wird generatorseitig ausgewertet als:
  - `auto`
  - `prefer_cycle`
  - `prefer_explicit`
- Die zugehoerigen UI-Felder existieren jetzt direkt im Panel, zusammen mit separatem Hinterschnitt-Werkzeug, Vorschub, Drehzahl und Optionalstop.

## Sicherheitslogik
- Vor jedem Werkzeugwechsel wird `M5` vor `M9` und `T.. M6` ausgegeben.
- `emit_approach()` schreibt Warnungen in den G-Code, wenn:
  - der Startpunkt im Rohteil liegt
  - der Startpunkt in der Chuck-No-Go-Zone liegt
  - die Rueckzugsebene den Futterbereich schneidet
- `get_machine_limit_warnings()` meldet unplausible Werte fuer `XT/ZT`, `XRA/XRI`, `ZRA/ZRI`.
- `validate_chuck_segment()` blockiert jeden Eilgang, der die Futter-Sperrzone
  schneidet, auch wenn Start- und Zielpunkt jeweils fuer sich ausserhalb
  liegen. `validate_stock_segment()` macht dasselbe fuer reine Diagonal-
  Eilgaenge (`G0 X.. Z..` in einer Zeile) gegen die Rohteil-Huellkurve
  (Diagonal-Rueckzug in `emit_safe_retract_for_op`, Anfahrt der
  Werkzeugwechselposition). Bewusst ausgenommen: die achsweise Anfahrt-
  /Rueckzugsfolge in `emit_approach` (Zielpunkt liegt bei Folgeoperationen
  wie Schlichten nach Schruppen absichtlich innerhalb der Huellkurve) und
  jede Sicherheitsposition im Innen-Modus (die Huellkurve ist ein reines
  Aussenmass-Rechteck und kann eine Bohrung nicht abbilden). Dieselbe
  Prüfung deckt inzwischen den zweiten Teilschritt jeder achsweisen
  Rückzugsreihenfolge ab (Einstich/Keilnut, Bohren/Gewinde, X-vor-Z-
  Fallback bei Start im Rohteil/in der Futterzone, sowie den Aussen-Modus
  von `emit_approach()`) - eine konfigurierte "sichere" Position (XRA/ZRA),
  die selbst noch in einer Sperrzone liegt, wird dadurch erkannt statt
  stillschweigend durchfahren.
- `append_tool_and_spindle()` blockiert seit LES-040, wenn fuer eine
  Operation keine gueltige Drehzahl (fest oder vollstaendiges CSS) zustande
  kommt - vorher wurde `spindle=0`/negativ/fehlend/auf 0 U/min gerundet
  stillschweigend ignoriert, ohne jedes `M3` im Programm. Ausnahme
  `require_spindle=False` fuer die reine Werkzeugwechsel-Positionierung
  (zwei Stellen in `gcode_program.py`), deren Aufgabe nur das Anfahren des
  Wechselpunkts ist.
- Endparklogik ist jetzt als eigene Funktion gekapselt und unterstuetzt:
  - Werkzeugwechselpunkt
  - freie Parkposition
  - sequentielle Endbewegung
- Werkzeugwechsel- und Parkpositionen koennen explizit als Werkstueck- oder Maschinenkoordinaten erzeugt werden; fuer Maschinenkoordinaten wird `G53` direkt an der Bewegung ausgegeben
- Vor jedem expliziten `T.. M6` wird derselbe Werkzeugwechselpfad erzwungen; der erste reale Wechsel faehrt den Wechselpunkt jetzt nicht mehr aus Versehen aus
- Spindelmodus (`G97`/`G96`) ist pro Operation waehlbar (Planen, Abspanen, Einstich/Abstich, Gewinde - Bohren bewusst ausgenommen, da sich der Werkzeugdurchmesser dort nicht aendert); `G96` nutzt eine eigene Schnittgeschwindigkeit Vc (m/min) statt der Drehzahl unter `S`, `program_spindle_max_rpm` bleibt als programmweite Sicherheitsobergrenze im Programmkopf erhalten.
- Werkzeugwechsel kann jetzt optional einen `M1` vor dem Wechsel ausgeben - gilt seit LES-039 auch fuer den allerersten Wechsel (vorher stillschweigend ausgenommen) und steht vor jeder angenommenen sicheren Rueckzugsbewegung, nicht danach. Gewinde und separater Hinterschnitt koennen ebenfalls optional gestoppt werden.
- Legacy-Dateien mit gemischter XT-/ZT-Altlogik bleiben weiterhin les- und generierbar.

## Gewindelogik
- Gewinde unterstuetzen jetzt getrennt:
  - Innen/Aussen
  - Rechts/Links
  - expliziten `thread_start_z`
- Vorschau und Generator leiten daraus konsistent Anfahrpunkt, Startpunkt, Endpunkt und Z-Laufrichtung ab.
- Die Step-Beschreibung zeigt Gewindetyp, Hand und den tatsaechlichen Z-Verlauf jetzt korrekt an.

## Validierung und Tests
- `validate_program_setup()` prueft jetzt zusaetzlich:
  - `G76` ohne sinnvolle Werte
  - DIN-Freistich ohne Gewindegroesse
  - DIN-Freistich ohne Innen/Aussen-Angabe
  - separates Hinterschnitt-Schruppen ohne Werkzeug
  - Werkzeugbreite groesser als Freistichbreite
- Neue Tests:
  - Gewinde fuer Innen/Aussen + Rechts/Links + variable Start-Z
  - Groove-Subroutinen liegen hinter dem Hauptprogrammfluss
  - explizite Toolchange-/Park-Koordinatensysteme
  - generatorseitig keine zusaetzliche `X0/Z0`-Fahrt nach `T.. M6`
  - Keyway-Validierung ohne irrefuehrendes `safe_z`-Pflichtfeld
  - Freistich-Geometrievarianten
  - separater Hinterschnitt-Pfad
  - `M5` vor jedem `M6`
  - Startwarnung im Rohteil
- Zusaetzlich abgesichert:
  - CSS + Parkposition
  - Gewinde-Freistich-Vorschlag
  - Optionalstop vor Werkzeugwechsel
  - Persistenz der neuen Expertenoptionen
- Referenzprogramme wurden nach Regenerierung erneut an den Snapshot gebunden.
- Aktueller Gesamtstand: `673 passed (Stub-Qt), 44 passed (Real-Qt), 0 skipped`.
- Tooltip-Ausgabe wird nicht mehr nur ueber `setToolTip()` gesetzt, sondern ueber einen zusaetzlichen Hover-/ToolTip-Relay fuer Embedded-/QTVCP-Kontexte stabilisiert.
- Reales Testprogramm `/home/adm1n/linuxcnc/nc_files/Test.ngc` wurde gegen die Generatorannahmen geprueft; die beobachtete manuelle Zusatzfahrt stammt aus der LinuxCNC-Konfiguration (`[EMCIO] TOOL_CHANGE_MODE = MANUAL`, `hal_manualtoolchange` in `lc10e_spindle_postgui.hal`), nicht aus dem generierten G-Code.

---

## UI-Design-Entscheidungen
- Dropdowns pro Kontursegment statt globaler Optionen
- Deutsch als Primärsprache
- qtpy als Abstraktionsschicht (Fallback möglich)
- Vorschau zeichnet X weiterhin als Durchmesser (für die Beschriftung), nutzt intern aber immer halbierte X-Werte, damit Kreise wirklich rund und in Radiusmaßstab dargestellt werden.
- Unsaved-State wird bewusst nicht ueber Dateisystem-Events, sondern ueber Form-/Struktur-Aenderungen im Handler gefuehrt; Warnungen beim Reiter-/Stepwechsel sind nur Hinweis, kein implizites Speichern.

## Verbindliche i18n-Regel (ID-only)
- Keine sichtbaren Texte aus Python-Strings oder `.ui`-Fallbacks verwenden.
- Sichtbare Texte, Tooltips, Tabellenkoepfe und Dialogtexte muessen aus Sprachkeys (`.lng`) kommen.
- Fehlende Keys duerfen nicht kaschiert werden: sichtbar bleibt der Key/ID.
- Programmlogik darf nicht auf `currentText()` basieren; nur technische Werte via `currentData()`.
- Neue UI-Elemente zuerst mit stabiler ID/Key einfuehren, danach Sprachdateien erweitern.
- Generatorwarnungen, die als `(...)`-Kommentare ins `.ngc` gehen, muessen vor der Ausgabe geklammert-sicher sanitisiert werden, damit LinuxCNC keine `nested comment`-Fehler bekommt.

---

## Embedded-Widget-Binding (2026-02 Fix)
- Im eingebetteten QTvcp-Modus dürfen Operations-Updates ausschließlich gegen `listOperations`/`list_ops` laufen.
- Der frühere Fallback auf beliebige `QListWidget`-Instanzen (insb. `gcode_list`) wurde entfernt, da dadurch Save/Load-Aktionen gegen die falsche Liste liefen.
- `_refresh_operation_list()` verwirft jetzt aktiv falsch gebundene Listen (`objectName` nicht `listOperations`/`list_ops`) und resolved neu.
- `_on_param_changed()` nutzt konsistent `self.list_ops`; damit bleiben Param-Änderungen und Selektion synchron.
- Relevante Regressionstests: `tests/test_save_load_roundtrip.py`, `tests/test_step_double_click.py`.

---

## Bekannte technische Baustellen

Die vollstaendige und priorisierte Liste steht in `TODO.md`. Technisch
besonders relevant sind derzeit:

- unsichere direkte Diagonalanfahrt bei gesetztem `_is_at_safe`
- weitere Verifikation von Innen-Schruppen und Innen-Schlichten
- lokale DIN-Freistiche innerhalb laengerer Konturen
- Primitive-/Arc-Erhalt in verbleibenden move-based Pfaden
- Werkzeuggeometrie und tiefere Tooltable-Plausibilitaet
- noch symbolische Gewindevorschau
- fachliche Trennung der Preview-Pipeline

---

## Mitwirken
Das Projekt ist experimentell, aber strukturiert.
Beiträge sind willkommen, insbesondere:
- Geometrie / Arc-Berechnungen
- zusätzliche Abspanstrategien
- Tests mit realen Maschinen


## Reproduzierbarer Check seit 2026-09-08

Testabhaengigkeiten: `python -m pip install pytest PyQt5 qtpy`.
`python run_tests.py -p no:cacheprovider` startet Stub- und Real-Qt-Suite
in frischen Prozessen. Einzellauf: `python -m pytest -q --qt-mode=stub`
oder `python -m pytest -q --qt-mode=real`. Real-Qt laeuft offscreen mit
echtem PyQt5; nur die qtvcp-Maschinenaktion ist isoliert. Fehlendes PyQt5
ist ein Fehler und wird nicht als erfolgreicher Skip gewertet.

Danach `python -X utf8 regenerate_all_ngc.py` und
`python validate_ngc.py`. Unter Linux mit installiertem LinuxCNC:
`python3 check_linuxcnc.py --interpreter /pfad/zu/rs274`.
Dieser letzte Lauf wurde hier mangels Interpreter NICHT ausgefuehrt.
Er verwendet temporaere Parameter und eine synthetische Werkzeugtabelle.
Backplot, reale Werkzeugoffsets und Trockenlauf sind gesonderte Pruefungen.
Details: [Verifikation](doc/VERIFICATION_2026-09-08.md).

Fortsetzung 2026-09-09: CSS-Zwischenstand abgesichert, Bohr- und zentrale
Zahlenvalidierung erweitert, Innenradiusmatrix und zwei Referenzen ergaenzt.
LES-013/040/028/003/012/015 bleiben mit den dokumentierten Restarbeiten offen.
[Pruefstand und Grenzen](doc/VERIFICATION_2026-09-09.md).

Testumgebung auf einem neuen Rechner:

```text
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-test.txt
.venv/Scripts/python run_tests.py -p no:cacheprovider --tb=short
```

Unter Linux `.venv/bin/python` verwenden. Die direkte Abhaengigkeitsliste
enthaelt die hier getesteten Versionen; LinuxCNC wird separat benoetigt.

WSL-Fortsetzung 2026-09-09: LinuxCNC-Interpreterpruefung erfolgreich fuer
elf Referenzen und 30 Matrixprogramme. Nichtmonotone Boegen vor G71/G72
abweisen; primitive Konturboegen auch beim expliziten Schlichten erhalten.
[Interpreterbericht und Nachweise](doc/linuxcnc_2026-09-09/README.md).

LES-005 Teilabschluss: Innen-Schlichtrueckzug radial vor axial, G40-Abwahl
mit geprueftem Freiraum. 524 Stub-/44 Qt-Tests und 11 Referenzen/30 Matrixfaelle
im Interpreter bestanden. [Details und Grenzen](doc/LES005_INNEN_RUECKZUG_2026-09-09.md).

LES-001 Teilabschluss 2026-09-09: reine Diagonal-Eilgaenge werden jetzt
zusaetzlich per `validate_stock_segment()` gegen die Rohteil-Huellkurve
geprueft, auch wenn Start- und Zielpunkt jeweils fuer sich ausserhalb
liegen. Bewusst ausgenommen bleiben die achsweise Anfahrt/Rueckzugsfolge
und jede Sicherheitsposition im Innen-Modus (Bohrung nicht als Rechteck
abbildbar). 533 Stub-/44 Qt-Tests bestanden, Referenzprogramme unveraendert.
Die sichere Achsreihenfolge je nach Rohteil-/Futterzone (LES-001,
Kernpunkt) bleibt offen.

LES-001 Fortsetzung 2026-09-09: op-spezifische Rueckzugs-Achsreihenfolge
(Einstich/Keilnut X vor Z, Bohren/Gewinde Z vor X) sowie Aussen- UND
Innen-Schruppen->Schlichten mit identischem Werkzeug regressionsgesichert -
in beiden Faellen nur ein Werkzeugwechsel, Anfahrt der zweiten Operation
fehlerfrei. Kein neuer Fehler gefunden, bestehendes Verhalten bestaetigt.
539 Stub-/44 Qt-Tests bestanden. Die Achsreihenfolge-Entscheidung selbst
(LES-001, Kernpunkt) und der Abgleich Warnung/tatsaechlicher Fahrweg
bleiben offen.

LES-001 WSL-Fortsetzung 2026-09-09: der zweite Teilschritt jeder
Rueckzugsreihenfolge (die zuerst erreichte sichere Achse bleibt konstant)
wird jetzt in `emit_safe_retract_for_op()` (alle vier Zweige) und
`emit_approach()` (Aussen-Modus) gegen Futter-Sperrzone und - ausser im
Innen-Modus - Rohteil-Huellkurve geprueft; der erste (Flucht-)Teilschritt
bleibt bewusst ungeprueft. Dabei einen echten, bis dahin unentdeckten Fall
gefunden: ein bestehender Test konfigurierte XRA=60 als "sicher", obwohl
selbst noch in der Futter-Sperrzone (X20..80) liegend - korrigiert auf
XRA=90. Alle 11 Referenzen und 30 Matrixfaelle unter WSL/Debian mit
echtem rs274 erneut bestanden, keine Ausgabeaenderung. 542 Stub-/44
Qt-Tests bestanden. Die eigentliche Achsreihenfolge-Entscheidung (LES-001,
Kernpunkt: dynamisch statt fest je Operationstyp) bleibt offen.

LES-039 Fortsetzung 2026-09-09: `optional_stop_toolchange` schloss den
allerersten Werkzeugwechsel bisher stillschweigend aus (Tooltip verspricht
aber "vor JEDEM Werkzeugwechsel") - genau dort, wo Werkzeug und Position
am wenigsten bekannt sind. M1 gilt jetzt fuer jeden Wechsel einschliesslich
des ersten und steht vor der angenommenen sicheren Rueckzugsbewegung, nicht
mehr danach. Das ist eine PROZEDURALE Absicherung (Bediener kann vor der
ersten Bewegung pruefen); die pauschale Z-vor-X-Reihenfolge bei unbekanntem
Ausgangszustand selbst bleibt unveraendert - eine Textgenerierung kann den
realen Maschinenzustand grundsaetzlich nicht kennen. Unter WSL/Debian mit
echtem rs274 verifiziert, keine Ausgabeaenderung fuer bestehende Programme.
543 Stub-/44 Qt-Tests bestanden.

LES-040 Drehzahl-Luecke 2026-09-09: `append_tool_and_spindle()` schluckte
`spindle=0`/negativ/fehlend/auf 0 U/min gerundet bisher stillschweigend -
kein Fehler, kein `M3` irgendwo im Programm. Real reproduziert: eine
komplette Abspanen-Operation mit `spindle=0` erzeugte ein vollstaendig
"gueltiges" Programm ohne Spindelstart. Blockiert jetzt, mit bewusster
Ausnahme fuer die reine Werkzeugwechsel-Positionierung
(`require_spindle=False`), deren Aufgabe nur das Anfahren des
Wechselpunkts ist. Erster Anlauf brach 148 Tests, weil viele Fixtures nie
eine Drehzahl gesetzt hatten - auf Rueckfrage vollstaendig gefixt statt
die Pruefung aufzuweichen. Unter WSL/Debian mit echtem rs274 verifiziert,
keine Ausgabeaenderung fuer bestehende Programme. 549 Stub-/44 Qt-Tests
bestanden. "Koordinaten, Vorschuebe, Zustellungen und Sicherheitswerte"
ausserhalb der Drehzahl bleiben fachlich nicht vollstaendig durchgegangen.

LES-006 Inventor-Post ausgewertet 2026-09-09: `doc/linuxcnc turning.cps`
hat KEINE Matrix je Operationstyp - Rueckzugs-/Anfahrreihenfolge sind
global per Post-Eigenschaft (Default X-dann-Z Rueckzug, Diagonale
Anfahrt), unabhaengig vom Operationstyp; Rueckzug erfolgt zudem nur bei
Werkzeug-/Spindel-/WCS-Wechsel und geht auf eine feste Maschinenposition
(G28/G53), nicht auf eine werkstueckrelative Position. Unser Generator
unterscheidet bereits feiner. Vorschlag "Rueckzug bei unbekanntem Zustand
auf festes G53 umstellen" gepruefte und geometrisch widerlegt (fester
Punkt macht Diagonalbewegung von unbekannter Startposition nicht
automatisch kollisionsfrei, siehe TODO.md-Gegenbeispiel) - keine
Codeaenderung, aktueller werkstueckrelativer Ansatz bleibt robuster.

LES-001 Abschluss (bis auf dynamische Wahl) 2026-09-09:
`get_approach_warnings()` prueft die Rueckzugsebene-Warnung jetzt wie
`validate_chuck_segment()` gegen X-Intervall UND Z-Grenzwert der Futter-
Sperrzone, nicht mehr nur gegen Z allein - eine sichere Position mit X
ausserhalb der Zone wurde vorher faelschlich als gefaehrdet gemeldet,
obwohl der tatsaechliche, bereits abgesicherte Fahrweg dort nie hinfuehrt.
Damit ist LES-001 bis auf die bewusst NICHT umgesetzte dynamische
Achsreihenfolge-Wahl je Eilgang durchgegangen: eine Fall-zu-Fall-
Entscheidung widerspraeche den Projektzielen (deterministische,
nachvollziehbare Bewegungen) und ist auch im Inventor-Post (LES-006)
nicht vorgesehen. 550 Stub-/44 Qt-Tests bestanden, unter WSL/Debian mit
echtem rs274 verifiziert.

LES-031 Redundante Nullbewegungen 2026-09-09: zwei echte, reproduzierbare
Faelle behoben. `gcode_drill.py` gab nach jedem Bohrzyklus unbedingt ein
`G0 Z<safe_z>` aus - empirisch gegen echten rs274 verifiziert, dass
LinuxCNC nach G80 im Default-Modus G99 auf die Rueckzugsebene R
zurueckkehrt (nicht auf die Z-Position vor dem Zyklus); da `retract` ohne
Angabe auf `safe_z` faellt, war die Bewegung im Standardfall ueberfluessig.
`append_tool_and_spindle()` gab vor jedem Werkzeugwechsel unbedingt einen
Rueckzug aus, auch wenn die vorherige Operation bereits exakt dort stand -
neue eng begrenzte `_safe_x`/`_safe_z`-Zustandsverfolgung (nur an Stellen
gesetzt, wo die Position unmittelbar zuvor sicher bekannt ist) erkennt
das. Bewusst NICHT angefasst: eine dritte Redundanz in den Innen-
Schruppzyklen - haengt an echter zentraler Positionsverfolgung (LES-022),
sonst Risiko veralteten Zustands im rough_finish-Kombimodus. 553 Stub-/44
Qt-Tests bestanden, unter WSL/Debian mit echtem rs274 verifiziert.

LES-013 verifiziert 2026-09-09 (keine Codeaenderung): jeder CSS-Aufrufer
uebergibt `css_start_diameter` konsistent passend zur tatsaechlichen
`emit_approach()`-Zielposition, an der `activate_pending_css()` direkt
danach G96 aktiviert - Move-based-Schruppen sogar je Pass. Modalsequenz
frisch gegen echten rs274 bestaetigt (kanonische SET_SPINDLE_MODE/
SET_SPINDLE_SPEED-Ausgabe). Alle Checklistenpunkte in TODO.md abgehakt.

LES-018 G70-Wiederverwendung 2026-09-09: ein reiner Schlichtstep (eigene
Operation, eigenes Werkzeug) nutzt jetzt `G70 Q<sub>` fuer den Kontur-Sub
eines frueheren, separaten Schruppschritts statt die Fertigkontur erneut
explizit auszugeben - neue `_cycle_defined_subs`-Zustandsverfolgung
bestaetigt, dass der Sub tatsaechlich per G71/G72 definiert wurde;
Werkzeugkorrektur und Innenbearbeitung (nutzt G71/G72 nie) fallen
automatisch auf den bestehenden expliziten Weg zurueck. Real mit einem
Zwei-Werkzeug-Rough/Finish-Programm gegen echten rs274 verifiziert. 555
Stub-/44 Qt-Tests bestanden, alle 41 Referenzen/Matrixfaelle unveraendert.

LES-028 G76-Zustellwinkel 2026-09-09: `infeed_q` (G76 `Q`) floss bisher
ungeprueft in die Ausgabe - jetzt auf den physikalisch gueltigen Bereich
0..<90 Grad geprueft (0 = radiale Zustellung bleibt gueltig). Zwei
Checklistenpunkte ("Werkzeugwechsel nur aus normalisiertem
Werkzeugdatensatz", "Preset-/manuelle Werte vergleichen") bewusst NICHT
umgesetzt - im TODO nicht praezise genug spezifiziert, Risiko eines
grossen Blast-Radius wie beim Drehzahl-Fund in LES-040 ohne vorherige
Klaerung der genauen Anforderung. 559 Stub-/44 Qt-Tests bestanden, unter
WSL/Debian mit echtem rs274 verifiziert.

Review nach Unterbrechung 2026-09-09: Zwischenzeitliche Erweiterungen
beibehalten; explizite Schlichtpraeferenz und CSS-/G76-Ausgaberundung
korrigiert. Aktuell 563 Stub-/44 Qt-Tests und elf Referenzen/37 Matrixfaelle
im Interpreter bestanden. LES-013 bleibt fuer Durchmesserbewertung,
zyklusinterne Bewegungen und reale Abnahmen offen; fruehere pauschale
Abschlussaussagen sind damit ersetzt.
[Details und Nachweise](doc/linuxcnc_2026-09-09/README.md).

Fortsetzung LES-037/001/006: vier Gewindefreistichfaelle (innen/aussen,
rechts/links) und zwei Schruppen-/Schlichten-Folgen mit identischem Werkzeug
unter rs274 bestanden. Zu wenig Konturstrecke blockiert in allen vier
Freistichvarianten den Export; Konturverlaengerung verschiebt den Freistich
nicht. Aktuell 573 Stub-/44 Qt-Tests, elf Referenzen und 43 Matrixfaelle.
WSLg/AXIS sind erreichbar; grafischer Backplot und reale Abnahme bleiben offen.
[Pruefbericht](doc/linuxcnc_2026-09-09/README.md).


LES-040/028, Einstichvalidierung 2026-09-09: Vorschuebe, Zustellung,
Werkzeug-/Nutbreite und Ueberdeckung werden mit den tatsaechlich an o220
uebergebenen drei Nachkommastellen geprueft. Start/Ende duerfen nach
Rundung nicht zusammenfallen. Spanbruchanzahl muss ganzzahlig und
nichtnegativ sein. Fuenf zuvor fehlschlagende Regressionen bestanden.
Aktuell 578 Stub-/44 Qt-Tests, keine Skips; elf Referenzen und 43
Matrixfaelle unter rs274 sowie 88 statische Checks bestanden.
Referenzausgabe unveraendert. Dies ist keine vollstaendige Abnahme aller
Einstich-/Abstichvarianten. Keilnut erzeugt derzeit wegen der expliziten
Makro-Sperre in gcode_keyway.py keinen G-Code; eine eigenstaendige
Implementierung und LinuxCNC-Abnahme bleiben offen.

LES-027 Teilstand 2026-09-09: isolierter Qt-Startbenchmark mit frischen
Prozessen vorhanden. UI-Ausschnitt im Median 0.368 s unter Windows und
1.362 s unter WSL, keine Reproduktion der gemeldeten >20 s. Neun
nachgelagerte Panel-Startaufgaben erhalten eigene Zeitmarken. Reale
Ursache, Bedienbereitschaft und Embedded-/Standalone-Vergleich bleiben offen.
[Messumfang, Rohdaten und naechster Nachweis](doc/STARTUP_2026-09-09.md).


LES-028/032 Teilstand 2026-09-09: Radiuskorrektur lehnt negative Radien,
nicht darstellbare Schneidendurchmesser sowie explizit ungueltige
Werkzeugorientierungen ab. Q/L wird ganzzahlig in 0..9 validiert, statt
Dezimalwerte abzuschneiden oder bei defekten Angaben still ohne Korrektur
weiterzulaufen. G41.1/G42.1 darf keinen auf null gerundeten D-Wert ausgeben.
Gueltige Zahlenstrings bleiben kompatibel. Fehlende Werkzeugdaten bzw.
fehlendes Q und Radius null behalten das bisherige Verhalten ohne Korrektur;
eine allgemeine Pflicht fuer vollstaendige Werkzeugtabellen ist nicht umgesetzt.
Neun Fehlerfaelle vorher reproduziert, elf neue Regressionen bestanden.
Aktuell 589 Stub-/44 Qt-Tests, 88 statische Checks sowie elf Referenzen und
43 Matrixfaelle unter rs274 bestanden; Referenzausgabe unveraendert.
Werkzeughuellen, Schneidenlaenge, physische Eignung und reale Abnahme bleiben offen.
