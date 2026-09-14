# TODO LatheEasyStep

Stand: 2026-09-14

Diese Datei enthaelt ausschliesslich offene Aufgaben. Abgeschlossene Arbeiten,
Befunde und historische Teststaende stehen im [CHANGELOG.md](CHANGELOG.md) und
in den Berichten unter `doc/`. Release-Ziele stehen in [ROADMAP.md](ROADMAP.md).

## Verifizierte Basis

- Branch `dev`, Entwicklungsstand fuer 0.8.0; `main` bleibt stabile 0.7.0-Basis.
- 772 Stub-Qt-Tests und 76 Tests mit echtem PyQt5, keine Skips.
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
| LES-024 | P2 | direkte moduluebergreifende Widgetzugriffe durch Schnittstellen ersetzen | L | 0.9.0 |
| LES-044 | P2 | Darstellungs- und Textschichten weiter entkoppeln | L-XL | 0.9.0 |
| LES-028 | P2 | Werkzeugdatensatz und Preset-/Manuell-Normalisierung festlegen | M | 0.9.0 |
| LES-032 | P2 | reale Werkzeuggeometrie fuer Plausibilitaet/Kollision auswerten | L | 0.9.0 |
| LES-043 | P2 | Gegenspindelfunktion als eigenes Projekt spezifizieren (UI bleibt gesperrt sichtbar) | XL | separat |
| LES-030 | extern | weitere physische Maschinenprofile verifizieren | extern | offen |

## LES-024 Modulschnittstellen

- [x] fuer Step-Verwaltung und Vorschau schmale View-Schnittstellen definiert:
  `StepListView` kapselt die Step-Liste; `PreviewView` kapselt die Ausgabe an
  Seiten-, Schnitt- und Konturvorschau.
- [x] die zwoelf `list_ops`-Zugriffsstellen bestehen aus zwei Gruppen:
  sechs Fachlogik-Dateien (ui_dirty/ui_flow/ui_persistence/ui_preview/
  ui_program/ui_selection) und sechs Bindungs-/Such-Dateien
  (ui_lifecycle/ui_split/ui_signals/ui_widget_lookup/ui_widgets/
  lathe_easystep_handler.py), die `handler.list_ops` ueberhaupt erst
  herstellen und bewusst nicht ueber `StepListView` laufen. Die sechs
  Fachlogik-Dateien sind auf `StepListView` migriert, die Vorschau-Ausgabe
  auf `PreviewView`/`PreviewScene`. `preview_widget.py` ist ueber zehn
  Pakete von 1049 auf 671 Zeilen geschrumpft (Diagrammberechnung, Primitive-
  Konvertierung, Keilnut-Polygone, Viewport/Ticks, Zeichenreihenfolge,
  Vorderansicht-Darstellungsplan, Legende/Statusbox als Qt-freie Funktionen
  in `preview_geometry.py`/`preview_scene.py`) - Details je Paket in
  CHANGELOG.md.
- [x] nach jedem der zehn Verkleinerungspakete Stub- und Real-Qt-Suite sowie
  Embedded-Start in der QtDragon-SIM verifiziert (durchgehend fehlerfrei,
  721/70 bis zuletzt 772/76 Tests); je nach Paket zusaetzlich Tab-Wechsel,
  Schnittansicht-Toggle und Legende-Klick live im UTILS-Panel geprueft.
  Einzelergebnisse je Paket in CHANGELOG.md.
- [ ] Entscheidung (2026-09-14): ungueltige Aktionen kuenftig per Buttonzustand
  verhindern statt nur beim Klick zu melden. Umsetzung: pro Button, der heute
  eine QMessageBox-Fehlermeldung ausloest (u. a. `ui_flow.py`/
  `ui_persistence.py`, zehn+ Stellen), den zugrundeliegenden Gueltigkeits-
  check als eigene, wiederverwendbare Funktion herausziehen und sowohl beim
  Klick (bestehende Meldung bleibt als letzte Sicherung) als auch bei
  Zustandsaenderungen (Signal-Handler) zum Enable/Disable des Buttons
  aufrufen. Reihenfolge klaeren, welcher Button zuerst (kleinster, klarster
  Fall zum Muster-Etablieren, dann die uebrigen paketweise).

## LES-044 Darstellung und Texte

- [ ] reine Vorschaugeometrie von Qt-Zeichenbefehlen weiter trennen; das Muster
  von `compute_tool_preview_layout()` verwenden.
- [ ] Entscheidung (2026-09-14): G-Code-Kommentare (Werkstattkommentare im
  erzeugten `.ngc`) werden sprachabhaengig wie die UI-Texte. Umsetzung:
  `comments.py`/`update_auto_comment()` und die `_describe_operation()`-
  Textbausteine auf `TRANSLATIONS`/Sprachdateien umstellen (analog zu
  `runtime.*`-Schluesseln); Referenzprogramme betroffen, da Kommentare Teil
  der `.ngc`-Ausgabe sind - nach der Umstellung alle Referenzen neu
  generieren, Diff pruefen (nur Kommentartext, keine Bewegungsaenderung)
  und mit `rs274` bestaetigen (Abschlussregeln Punkt 3/4).
- [ ] breite `except Exception`-Fallbacks pro migriertem Modul pruefen: erwartete
  Qt-/Host-Ausnahmen gezielt behandeln, unerwartete Fehler mindestens loggen.

## LES-028 Eingaben normalisieren

- [ ] Entscheidung (2026-09-14): jede verwendete Werkzeugnummer muss zwingend
  einen Eintrag in der geladenen Werkzeugtabelle haben. Umsetzung: den
  bisherigen Hinweis ("ISO/Radius fehlt bei: ...", optional) fuer fehlende
  Eintraege durch eine harte Fehlermeldung ersetzen, die den Werkzeugwechsel/
  die Programmerzeugung blockiert statt nur zu warnen - Fundstelle:
  `_auto_load_tool_table()`/Tool-Validierung in `lathe_easystep_handler.py`
  bzw. `tools.py`. Bestehende Referenzprogramme/Matrixfaelle muessen weiter
  fehlerfrei durchlaufen (alle nutzen bereits vollstaendige Tooltables).
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

- [x] Entscheidung (2026-09-14): keine UI-Entfernung - Gegenspindelfunktion
  wird als eigenes, separates Projekt geplant statt jetzt in LatheEasyStep
  umgesetzt. Bedienelemente bleiben bis dahin sichtbar, aber gesperrt.
- [ ] Spezifikation fuer das separate Projekt erstellen, bevor irgendeine
  Generatorimplementierung beginnt: Operationen, Spindelsynchronisation,
  S3-Grenzen und Kollisionsmodell. Kein LatheEasyStep-Codepaket ohne
  LinuxCNC-SIM-/Maschinenkonzept fuer diese Spezifikation.

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
