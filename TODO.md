# TODO LatheEasyStep

Stand: 2026-09-14

Diese Datei enthaelt ausschliesslich offene Aufgaben. Abgeschlossene Arbeiten,
Befunde und historische Teststaende stehen im [CHANGELOG.md](CHANGELOG.md) und
in den Berichten unter `doc/`. Release-Ziele stehen in [ROADMAP.md](ROADMAP.md).

## Verifizierte Basis

- Branch `dev`, Entwicklungsstand fuer 0.8.0; `main` bleibt stabile 0.7.0-Basis.
- 740 Stub-Qt-Tests und 75 Tests mit echtem PyQt5, keine Skips.
- Zwoelf Referenzprogramme bestehen statische NGC-Pruefung und nativen
  LinuxCNC-Interpreter (`rs274`); zusaetzlich bestehen 43 Matrixprogramme.
- Alle zwoelf Referenzen wurden in der QtDragon-SIM bis `M30` ausgefuehrt.
- `Planen_Radius.ngc` wurde am 2026-09-14 erneut vollstaendig in der SIM
  ausgefuehrt: 272,6 s, leerer Fehlerkanal, Endposition am definierten
  Werkzeugwechselpunkt. Ein Backplot mit nahem Test-Wechselpunkt bestaetigt
  die gerundete Planenkante. LES-036 ist damit abgeschlossen.
- Der Generator ist von Qt getrennt. Reiter, Step-Verwaltung und Vorschau
  liegen in eigenen UI-Fragmenten.

## Priorisierter Arbeitsindex

| ID | Prio | Aufgabe | Aufwand | Ziel |
|---|---|---|---|---|
| LES-034 | P2 | Vorschau fachlich in Endkontur, Werkzeugweg und Hilfsgeometrie trennen | L | 0.9.0 |
| LES-024 | P2 | direkte moduluebergreifende Widgetzugriffe durch Schnittstellen ersetzen | L | 0.9.0 |
| LES-044 | P2 | Darstellungs- und Textschichten weiter entkoppeln | L-XL | 0.9.0 |
| LES-028 | P2 | Werkzeugdatensatz und Preset-/Manuell-Normalisierung festlegen | M | 0.9.0 |
| LES-032 | P2 | reale Werkzeuggeometrie fuer Plausibilitaet/Kollision auswerten | L | 0.9.0 |
| LES-043 | P2 | Gegenspindel-UI entfernen oder Funktion als eigenes Projekt spezifizieren | S/XL | 0.9.0 |
| LES-030 | extern | weitere physische Maschinenprofile verifizieren | extern | offen |

## LES-034 Preview-Pipeline

ABSPANEN/FACE-Pfade, THREAD-Geometrie sowie DRILL/GROOVE-Grundgeometrie sind
bereits gegen Generator beziehungsweise Referenzdaten getestet.

- [x] Werkstueckgeometrie, verifizierter Werkzeugweg und Hilfsgeometrie im
  `PreviewScene`-Modell als getrennte Ebenen abbilden. Bohrer-Silhouette und
  unbekannte Altdaten bleiben bewusst Hilfsgeometrie statt faelschlich als
  verifizierter Werkzeugweg bezeichnet zu werden.
- [x] die drei `PreviewScene`-Ebenen in der Seitenansicht mit eigener
  Darstellungsart und passender Legende zeichnen; aktiver Pfad sowie vorhandene
  Spezialrollen behalten Vorrang.
- [x] Primitive grundsaetzlich als einzelne Striche zeichnen; unabhaengige
  Linien, Boegen und Polylinien werden nicht mehr ueber synthetische
  Diagonalen miteinander verbunden.
- [x] Anfahrt, Rueckzug, Werkzeugwechsel und Parken nur darstellen, wenn sie
  aus demselben Bewegungsplan wie der G-Code stammen: Bestandsaufnahme ergab
  keinen Fund. Keine Preview-Quelle (`preview_geometry.py`, `preview_scene.py`,
  `ui_preview.py`) baut Anfahrt-/Werkzeugwechsel-/Park-Segmente; die
  "retract"-Rolle zeichnet nur die konfigurierten Rueckzugsebenen als
  statische Referenzlinien, keine Bewegung. Strukturell abgesichert, weil
  `paintEvent()` jeden Operationspfad ueber einen eigenen
  `drawPolyline()`-Aufruf zeichnet statt mehrere Pfade zu verketten - jetzt
  dauerhaft mit `tests/test_preview_no_synthetic_links_between_operations.py`
  geprueft (per gezielt injizierter Verkettung als echte Regression
  verifiziert, danach zurueckgesetzt).
- [x] komplexe Endgeometrien in Seiten- und Schnittansicht vergleichen. Zwei
  strukturell verschiedene Faelle gefunden und beide abgesichert: (1) die
  radiale Keilnut (mode 0) hatte zwei unabhaengig kodierte Formeln (Seite:
  `build_keyway_path()`; Schnitt: bisher inline in `preview_widget.py`) -
  als `keyway_radial_slot_radii()` nach `preview_geometry.py` extrahiert und
  direkt gegen die Seitenansicht verglichen (stimmte exakt ueberein), jetzt
  mit zwei Tests dauerhaft geprueft. (2) GROOVE/THREAD/ABSPANEN nutzen keine
  eigene Formel: die Schnittansicht interpoliert den Durchmesser bei
  `slice_z` direkt aus demselben `op.path`, das die Seitenansicht zeichnet
  (`_interp_x_hits_at_z()`) - koennen also strukturell nicht auseinander-
  laufen. Diese bisher ungetestete Interpolation (linearer Verlauf,
  Nutflanke mit zwei Treffern, Bereich ausserhalb des Pfads) jetzt mit vier
  Tests abgesichert. Alle sechs neuen Tests per injizierter Abweichung als
  echte Regression verifiziert, danach zurueckgesetzt. Bewusst nicht
  weiterverfolgt: axiale Keilnut (mode != 0) wird in der Schnittansicht gar
  nicht gezeichnet - kein Fund, aber auch kein Vergleich noetig.
- [ ] `preview_widget.py` entlang dieser Ebenen verkleinern. Erstes Paket:
  die komplette Schnittansicht-Diagrammberechnung (`_interp_x_hits_at_z`,
  `_interp_x_at_z`, `_path_hits_at_slice`, `_front_operation_side`,
  `_front_slice_profile`, `_front_active_diameters`,
  `_front_reference_diameter`) als reine, Qt-freie Funktionen nach
  `preview_geometry.py` gezogen; die Widget-Methoden sind jetzt duenne
  Delegierungen. `preview_widget.py` von 1049 auf 909 Zeilen geschrumpft.
  Acht neue Tests laufen jetzt ohne echtes PyQt5 direkt gegen die reinen
  Funktionen (vorher nur indirekt ueber das Widget erreichbar), per zwei
  unabhaengig injizierten Bugs als echte Regression verifiziert. Noch
  offen: `_sample_arc`/`primitives_to_points` (pure Geometrie, aber noch
  Widget-Methoden) sowie die eigentlichen `_paint_*`-Zeichenroutinen
  (bleiben an QPainter gebunden, koennen aber schlanker werden, wenn sie
  nur noch die bereits extrahierte Geometrie abrufen statt sie selbst
  aufzubauen).

## LES-024 Modulschnittstellen

- [x] fuer Step-Verwaltung und Vorschau schmale View-Schnittstellen definiert:
  `StepListView` kapselt die Step-Liste; `PreviewView` kapselt die Ausgabe an
  Seiten-, Schnitt- und Konturvorschau.
- [ ] die zwoelf `list_ops`-Zugriffsstellen bestehen aus zwei Gruppen:
  sechs Fachlogik-Dateien (ui_dirty/ui_flow/ui_persistence/ui_preview/
  ui_program/ui_selection) und sechs Bindungs-/Such-Dateien
  (ui_lifecycle/ui_split/ui_signals/ui_widget_lookup/ui_widgets/
  lathe_easystep_handler.py), die `handler.list_ops` ueberhaupt erst
  herstellen und bewusst nicht ueber `StepListView` laufen. Die sechs
  Fachlogik-Dateien sind auf `StepListView` migriert. Die Widget-Ausgabe der
  Vorschau ist auf `PreviewView` migriert und der Geometrieaufbau liefert
  `PreviewScene`-Ebenen. Die Schnittansicht-Diagrammberechnung ist als reine
  Funktionen nach `preview_geometry.py` gezogen (siehe LES-034). Weiter offen
  ist die Verkleinerung der eigentlichen `_paint_*`-Zeichenroutinen sowie von
  `_sample_arc`/`primitives_to_points`.
- [x] nach dem ersten Paket Stub- und Real-Qt-Suite ausgefuehrt (721/70,
  keine Skips) sowie Tab-Wechsel embedded live in der SIM verifiziert
  (fehlerfrei, `handle_tab_changed`/`handle_selection_change` liefen ueber
  den neuen Pfad). Das zweite Paket ist mit 725/70 sowie Embedded-Start bis
  `critical done` nach 8,567 s ebenfalls verifiziert. Das Szenenmodell-Paket
  besteht mit 730/70 und Embedded-Start nach 8,465 s. Die Schnittansicht-
  Extraktion besteht mit 740/75 sowie Embedded-Start (9,2 s, fehlerfrei) und
  Live-Toggle der Schnittansicht im UTILS-Panel ohne Absturz. Bei jedem
  weiteren Paket erneut so pruefen.
- [ ] entscheiden, ob ungueltige Aktionen bereits per Buttonzustand verhindert
  oder weiterhin erst beim Klick mit konkreter Fehlermeldung blockiert werden.

## LES-044 Darstellung und Texte

- [ ] reine Vorschaugeometrie von Qt-Zeichenbefehlen weiter trennen; das Muster
  von `compute_tool_preview_layout()` verwenden.
- [ ] entscheiden, ob G-Code-Kommentare sprachabhaengig sein sollen. Fehlertexte
  der UI sollen langfristig ueber die Sprachdateien laufen; Werkstattkommentare
  koennen bewusst sprachstabil bleiben.
- [ ] breite `except Exception`-Fallbacks pro migriertem Modul pruefen: erwartete
  Qt-/Host-Ausnahmen gezielt behandeln, unerwartete Fehler mindestens loggen.

## LES-028 Eingaben normalisieren

- [ ] fachlich festlegen, ob jede verwendete Werkzeugnummer zwingend einen
  Eintrag in der geladenen Werkzeugtabelle benoetigt.
- [ ] Werkzeugwechsel nur aus einem normalisierten Werkzeugdatensatz erzeugen.
- [ ] Preset- und manuelle Werte nachvollziehbar vergleichen und Konflikte
  sichtbar machen.

## LES-032 Werkzeuggeometrie

- [ ] verifizierte Zuordnung der real genutzten Tooltable-Spalten fuer
  Schneidenlaenge, Haltergeometrie und Werkzeugbreite festlegen.
- [ ] Innen-/Aussenwerkzeuge anhand dieser Daten plausibilisieren.
- [ ] Tooltable-Daten fuer Erreichbarkeits- und Werkzeughuellenpruefungen nutzen.
- [ ] Werkzeugvorschau und Generator auf denselben normalisierten Datensatz
  stuetzen.

## LES-043 Gegenspindel

Die nicht implementierten Bedienelemente sind derzeit sichtbar, aber gesperrt.

- [ ] entscheiden: Checkbox/S3-Feld samt Settings entfernen oder eine echte
  Gegenspindelfunktion als separates Projekt planen.
- [ ] bei Umsetzung zuerst Operationen, Spindelsynchronisation, S3-Grenzen und
  Kollisionsmodell spezifizieren; keine Generatorimplementierung ohne
  LinuxCNC-SIM-/Maschinenkonzept.

## LES-030 Externe Maschinenverifikation

- [ ] unterschiedliche reale Drehmaschinen mit ihren Achsgrenzen,
  Werkzeugwechselpositionen und Futterbauformen verifizieren.

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
