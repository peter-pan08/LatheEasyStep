# Developer Notes – Lathe EasyStep

## Projektziel
Lathe EasyStep soll ein **shop-floor-taugliches Drehpanel** sein, kein vollwertiges CAM.
Ziel ist:
- deterministische Bewegungen
- nachvollziehbare Geometrie
- minimale Überraschungen an der Maschine

## Release-Stand

- `v0.7.0` ist die lauffaehige Basis auf `main`.
- `dev` ist der Entwicklungsstand fuer `v0.8.0` und liegt am 24. Juli 2026
  acht Commits vor `main`.
- Aktueller Teststand: `331 passed, 3 skipped`.
- Der Stand umfasst Freistich-/Hinterschnitt-Backend, harte XRI-Grenzen,
  Dirty-State, Preview-Docking, explizite Toolchange-/Park-Koordinatensysteme,
  Rechts-/Linksgewinde, `rough_finish`, Realtest-Fixes und die geteilte UI.
- `lathe_easystep.ui` ist die Shell; die acht Bearbeitungsreiter liegen unter
  `lathe_easystep/ui_parts/` und werden durch `ui_split.py` geladen.
- `de.lng`, `en.lng` und `es.lng` besitzen jeweils 1.020 identische,
  nichtleere und eindeutige Schluessel.
- Offene Arbeiten und Release-Zuordnung werden verbindlich in
  `TODO.md` und `ROADMAP.md` gepflegt.

---

## Architektur-Überblick

- `lathe_easystep_handler.py`
  - QtVCP-`HandlerClass`, Widget-Bootstrapping und verbleibende Klebelogik
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
- `slicer.py`
  - veraltete Parallelimplementierung; von der produktiven Anwendung nicht
    importiert, aber noch von `regenerate_ngc.py` und Legacy-Tests verwendet
  - soll nach Migration dieser Verbraucher entfernt werden

UI und Toolpath-Logik sind bewusst getrennt.

## UI-/Spracharchitektur

- Fachliche Logik arbeitet mit technischen IDs und `currentData()`, nicht mit
  lokalisierten Anzeigetexten.
- Die aktiven Kataloge liegen unter `lathe_easystep/languages/*.lng`.
- Deutsch, Englisch und Spanisch besitzen aktuell jeweils 1.020 identische,
  nichtleere und eindeutige Schluessel.
- Sprachumschaltung und Tooltips wurden im eingebetteten Panel praktisch
  bestaetigt.
- Noch offen sind sichtbare Defaulttexte in Python, `lathe_easystep.ui` und
  `ui_parts/*.ui`. Diese werden zur Laufzeit ueberschrieben, verletzen aber
  noch den angestrebten reinen Key-/ID-Zustand.
- `lathe_easystep/i18n/*.json` wird vom aktiven `.lng`-Loader nicht
  verwendet; verbleibende Verwendungen muessen vor einer Entfernung auditiert
  werden.

## Test-Hinweise
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

Lokale Kopien dieser Helfer sollen nicht erneut in UI- oder G-Code-Modulen
angelegt werden. Das fruehere Paket `lathe_easystep/contour/` war ungenutzt
und intern unvollstaendig und wurde entfernt; produktive Konturpfade laufen
ueber `contour_logic.py` und `contour_features.py`.

Weitere Handler-Methoden mit substanzieller Eigenlogik (statt reinem
Delegieren), die sich als naechstes ausgliedern liessen: `_collect_program_header`,
`_collect_contour_segments`, `_apply_thread_preset`/`_populate_thread_standard_options`,
`_get_widget_by_name`/`_resolve_core_widgets_strict`/`_register_known_widgets`
(Widget-Bootstrapping), `_set_tooltip_deep`/`_fallback_tooltip_text` (Tooltip-
Erzwingung). Nicht in dieser Runde gemacht, um das Risiko in einem Durchgang
begrenzt zu halten - jede Extraktion wurde einzeln mit vollem Testlauf und
echtem PyQt5 (`uic.loadUi`) gegengeprueft.

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
- Endparklogik ist jetzt als eigene Funktion gekapselt und unterstuetzt:
  - Werkzeugwechselpunkt
  - freie Parkposition
  - sequentielle Endbewegung
- Werkzeugwechsel- und Parkpositionen koennen explizit als Werkstueck- oder Maschinenkoordinaten erzeugt werden; fuer Maschinenkoordinaten wird `G53` direkt an der Bewegung ausgegeben
- Vor jedem expliziten `T.. M6` wird derselbe Werkzeugwechselpfad erzwungen; der erste reale Wechsel faehrt den Wechselpunkt jetzt nicht mehr aus Versehen aus
- Spindelmodus kann generatorseitig zwischen `G97` und `G96` unterscheiden; fuer `G96` ist ein Max-RPM-Wert vorgesehen.
- Werkzeugwechsel kann jetzt optional einen `M1` vor dem Wechsel ausgeben; Gewinde und separater Hinterschnitt koennen ebenfalls optional gestoppt werden.
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
- Aktueller Gesamtstand: `331 passed, 3 skipped`.
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
- fehlender harter Abbruch bei vollstaendig leeren Schruppoperationen
- weitere Verifikation von Innen-Schruppen und Innen-Schlichten
- lokale DIN-Freistiche innerhalb laengerer Konturen
- Primitive-/Arc-Erhalt in verbleibenden move-based Pfaden
- produktiv ungenutzte Parallelimplementierung in `slicer.py`
- sichtbare Defaulttexte in UI-/Python-Quellen trotz vollstaendiger Kataloge
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
