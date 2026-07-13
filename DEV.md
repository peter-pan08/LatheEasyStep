# Developer Notes – Lathe EasyStep

## Projektziel
Lathe EasyStep soll ein **shop-floor-taugliches Drehpanel** sein, kein vollwertiges CAM.
Ziel ist:
- deterministische Bewegungen
- nachvollziehbare Geometrie
- minimale Überraschungen an der Maschine

## Release-Stand
- `v0.7.0` markiert den abgeschlossenen Refactor-Stand fuer Vorschau-Geometrie,
  Kontur-Logik, G-Code-Einstiegsmodule und die aktuelle Regressionstest-Basis.
- Neue Umbauten werden wieder unter `Unreleased` im Changelog gesammelt und
  zuerst auf `dev` verifiziert.
- Stand `2026-07-13` auf `dev`: Freistich-/Hinterschnitt-Backend, Generator-Transparenz,
  Dirty-State/Warnlogik, Preview-Docking, Groove/Abstich-Split, explizite
  Toolchange-/Park-Koordinatensysteme, erweiterte Gewinde-UI/-Generatorlogik,
  robustere Tooltip-Erzwingung, erweiterte Sicherheitslogik und
  zusaetzliche Validierungen sind implementiert und mit `194 passed`
  abgesichert.

---

## Architektur-Überblick
- `lathe_easystep_handler.py`
  - UI-Logik
  - Konturverwaltung
  - Benutzerparameter
- `slicer.py`
  - Geometrische Auswertung
  - Abspanstrategien
  - G-Code-Erzeugung

UI und Toolpath-Logik sind bewusst getrennt.

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

Lokale Kopien dieser Helfer sollen nicht erneut in UI- oder G-Code-Modulen
angelegt werden. Das fruehere Paket `lathe_easystep/contour/` war ungenutzt
und intern unvollstaendig und wurde entfernt; produktive Konturpfade laufen
ueber `contour_logic.py` und `contour_features.py`.

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

Der aktuelle Stand erzeugt intern echte Arc-Geometrie, die Ausgabe erfolgt derzeit noch linearisiert.
Geplante Erweiterung:
- echte Arc-Primitiven
- G2/G3-Ausgabe (G18-Ebene)

---

## Planen / FACE
- `build_face_primitives()` repräsentiert die OD-Ecke als echte Primitive (Linien + Arc), sodass the preview die Kante am Außendurchmesser direkt zeigt.
- Die Parameter `edge_type`, `edge_size` und das neue `edge_in_roughing` bestimmen, ob die Kante als Linie, Fase oder Radius modelliert wird und ob sie schon im letzten Roughing-Pass vorgearbeitet wird.
- In `gcode_for_face()` wird bei aktivierter Vorform im Schruppen konkret eine diagonal abgesprungene Fase (G1) bzw. ein Viertelkreis (G2/G3) erzeugt; ohne Platz oder Edge-Inhalte bleibt es beim bewährten geraden Abziehen.

---

## Abspanlogik
- Aktuell: Schruppen parallel Z
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

---

## Embedded-Widget-Binding (2026-02 Fix)
- Im eingebetteten QTvcp-Modus dürfen Operations-Updates ausschließlich gegen `listOperations`/`list_ops` laufen.
- Der frühere Fallback auf beliebige `QListWidget`-Instanzen (insb. `gcode_list`) wurde entfernt, da dadurch Save/Load-Aktionen gegen die falsche Liste liefen.
- `_refresh_operation_list()` verwirft jetzt aktiv falsch gebundene Listen (`objectName` nicht `listOperations`/`list_ops`) und resolved neu.
- `_on_param_changed()` nutzt konsistent `self.list_ops`; damit bleiben Param-Änderungen und Selektion synchron.
- Relevante Regressionstests: `tests/test_save_load_roundtrip.py`, `tests/test_step_double_click.py`.

---

## Bekannte technische Baustellen
- Preview-Pipeline trennt aktuell Werkstueckkontur, Bearbeitungsbild und Hilfsgeometrie nicht strikt genug
- Preview soll im Zweifel zu wenig statt zu viel zeigen; keine impliziten Verbindungen oder Fantasie-Hilfslinien
- Gewinde-Vorschau ist derzeit nur symbolisch und muss spaeter aus den realen Gewindeparametern geometrisch abgeleitet werden
- Native Arc-Intersections in Move-based Roughing sind noch nicht vollstaendig fachlich ausgereizt
- G2/G3-Ausgabe kann fuer weitere Roughing-/Preview-Pfade noch vertieft werden
- Werkzeuggeometrie (Nasenradius, Lage, Schneidenlaenge)
- Tooltable-Integration mit tieferen Plausibilitaetspruefungen fuer Innen/Aussen-Werkzeuge

---

## Mitwirken
Das Projekt ist experimentell, aber strukturiert.
Beiträge sind willkommen, insbesondere:
- Geometrie / Arc-Berechnungen
- zusätzliche Abspanstrategien
- Tests mit realen Maschinen
