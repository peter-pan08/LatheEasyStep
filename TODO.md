# TODO LatheEasyStep

Stand: 2026-09-14

Diese Datei enthaelt ausschliesslich offene Aufgaben. Abgeschlossene Arbeiten,
Befunde und historische Teststaende stehen im [CHANGELOG.md](CHANGELOG.md) und
in den Berichten unter `doc/`. Release-Ziele stehen in [ROADMAP.md](ROADMAP.md).

## Verifizierte Basis

- Branch `dev`, Entwicklungsstand fuer 0.8.0; `main` bleibt stabile 0.7.0-Basis.
- 713 Stub-Qt-Tests und 63 Tests mit echtem PyQt5, keine Skips.
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
| LES-035 | P1 | Embedded-/Standalone-Paritaet nach UI-Auslagerungen absichern | M | 0.8.0 |
| LES-027 | P1 | reale Startzeit nach Tooltip-/Modulumbauten erneut messen | S | 0.8.0 |
| LES-034 | P2 | Vorschau fachlich in Endkontur, Werkzeugweg und Hilfsgeometrie trennen | L | 0.9.0 |
| LES-024 | P2 | direkte moduluebergreifende Widgetzugriffe durch Schnittstellen ersetzen | L | 0.9.0 |
| LES-044 | P2 | Darstellungs- und Textschichten weiter entkoppeln | L-XL | 0.9.0 |
| LES-028 | P2 | Werkzeugdatensatz und Preset-/Manuell-Normalisierung festlegen | M | 0.9.0 |
| LES-032 | P2 | reale Werkzeuggeometrie fuer Plausibilitaet/Kollision auswerten | L | 0.9.0 |
| LES-043 | P2 | Gegenspindel-UI entfernen oder Funktion als eigenes Projekt spezifizieren | S/XL | 0.9.0 |
| LES-030 | extern | weitere physische Maschinenprofile verifizieren | extern | offen |

## LES-035 Embedded-/Standalone-Paritaet

- [ ] Widget-Binding beider Startarten gezielt vergleichen.
- [ ] Tooltips, Dialoge und Dateipfade vergleichen.
- [ ] sicherstellen, dass Embedded-Betrieb keine globalen Host-Widgets bindet.
- [ ] Real-Qt-Smoke-Test fuer beide Startarten pflegen.
- [ ] Resolver-Warn-/Fehlerpfade nach `ui_ready` testen; der am 2026-09-14
  real gefundene fehlende Modul-Logger ist behoben und regressionstestet.

## LES-027 Performance

Eine bestaetigte Messung in der echten QtDragon-SIM am 2026-09-14 benoetigte
69,1 s bis zum Abschluss des zweiten Finalisierungsdurchlaufs. Darin entfielen
23,5 s auf dessen `ensure_core_widgets`; auch Signalbindung und Tooltips kosten
mehrere Sekunden. `listOperations` blieb im ersten Durchlauf trotz bereits
geladener Step-UI ungebunden und erzwang den zweiten Durchlauf. Der erste Lauf
deckte zudem einen verwaisten Aufruf des bereits
entfernten No-op-Callbacks `_schedule_post_start_init()` auf; dieser ist nun
entfernt und die Handler/Lifecycle-Schnittstelle wird automatisch geprueft.

**Nachmessung 2026-09-14 (nach dem Fix), real in der QtDragon-SIM (Embedded,
UTILS-Tab angeklickt):** `_finalize_ui_ready` schliesst jetzt nach EINEM
Durchlauf ab (`"DONE after pass 1 — all critical widgets found, skipping
further passes"`, log-bestaetigt); die zwei spaeteren `QTimer`-Aufrufe
(500 ms/2 s) kehren beide innerhalb von 6 ms sofort ueber die
`_ui_finalized`-Guard-Klausel zurueck, ohne erneut zu arbeiten. `listOperations`
ist im ersten Durchlauf bereits real gebunden (log: `list=<QListWidget ...>`,
nicht mehr `None`). Kein Absturz durch den vormals verwaisten
`_schedule_post_start_init()`-Aufruf. Gesamtzeit bis "critical done": **rund
18 s** (vorher 69,1 s fuer zwei Durchlaeufe) - `ensure_core_widgets` selbst
jetzt nur noch ~0,11 s (vorher 23,5 s allein dafuer). Neuer, jetzt groesster
Einzelposten: `connect_remaining_signals` mit ~6,6 s (9,6 s -> 16,2 s),
gefolgt von `ensure_advanced_widgets` mit ~2,5 s - beide bisher nicht
einzeln geprueft.

- [ ] Embedded und Standalone mit identischem Messpunkt vergleichen.
- [ ] Zeit bis sichtbares und bedienbares Panel messen.
- [x] klaeren, warum `listOperations` nach `load_step_management_uis()` im
  ersten Durchlauf nicht gebunden wird, und den zweiten Durchlauf vermeiden -
  real in der SIM bestaetigt (siehe Nachmessung oben): nur noch ein
  Durchlauf, `listOperations` korrekt gebunden.
- [x] teure Widget-Suchen in `ensure_core_widgets` profilieren und reduzieren;
  Zielwert unter 10 s - erreicht (~0,11 s). Neuer Flaschenhals ist jetzt
  `connect_remaining_signals` (~6,6 s), noch nicht einzeln profiliert.
- [ ] `connect_remaining_signals` (~6,6 s) und `ensure_advanced_widgets`
  (~2,5 s) einzeln profilieren - neue groesste Zeitanteile nach dem
  `listOperations`-Fix.
- [ ] ersten Reiterwechsel, Stepwechsel und Preview-Refresh messen.
- [ ] nur nach gemessenem Befund optimieren.

## LES-034 Preview-Pipeline

ABSPANEN/FACE-Pfade, THREAD-Geometrie sowie DRILL/GROOVE-Grundgeometrie sind
bereits gegen Generator beziehungsweise Referenzdaten getestet.

- [ ] Werkstueck-Endkontur, Werkzeugweg und Sicherheits-/Hilfsgeometrie als
  getrennte Datenebenen modellieren und getrennt zeichnen.
- [ ] keine impliziten Verbindungen zwischen unabhaengigen Pfaden erzeugen.
- [ ] Anfahrt, Rueckzug, Werkzeugwechsel und Parken nur darstellen, wenn sie
  aus demselben Bewegungsplan wie der G-Code stammen.
- [ ] komplexe Endgeometrien in Seiten- und Schnittansicht vergleichen.
- [ ] `preview_widget.py` entlang dieser Ebenen verkleinern.

## LES-024 Modulschnittstellen

- [ ] fuer Step-Verwaltung und Vorschau schmale Controller-/View-Schnittstellen
  definieren, bevor direkte Widgetzugriffe ersetzt werden.
- [ ] die dokumentierten zwoelf direkten Zugriffsstellen paketweise migrieren.
- [ ] nach jedem Paket Stub-, Real-Qt-, Embedded- und Standalone-Test ausfuehren.
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
