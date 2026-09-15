# TODO LatheEasyStep

Stand: 2026-09-15

Diese Datei enthaelt ausschliesslich offene Aufgaben. Abgeschlossene Arbeiten,
Befunde und historische Teststaende stehen im [CHANGELOG.md](CHANGELOG.md) und
in den Berichten unter `doc/`. Release-Ziele stehen in [ROADMAP.md](ROADMAP.md).

## Verifizierte Basis

- Branch `dev`, Entwicklungsstand fuer 0.8.0; `main` bleibt stabile 0.7.0-Basis.
- 823 Stub-Qt-Tests und 102 Tests mit echtem PyQt5, keine Skips.
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
- [ ] Entscheidung (2026-09-14) in Umsetzung: ungueltige Aktionen kuenftig per
  Buttonzustand verhindern statt nur beim Klick zu melden. Muster mit dem
  klarsten Fall etabliert: `update_save_step_button_state()`
  (`ui_persistence.py`) sperrt "Step speichern", solange keine Operation
  ausgewaehlt ist (vorher: Klick jederzeit moeglich, dann eine Warnung).
  Aufgerufen bei jeder Auswahlaenderung (`handle_selection_change()`,
  inkl. des fruehen Rueckgabepfads fuer eine ungueltige Zeile - sonst
  bliebe der Button nach dem Loeschen der letzten Operation faelschlich
  aktiv) sowie zentral am Ende von `_refresh_operation_list()`
  (`lathe_easystep_handler.py`) - das deckt Hinzufuegen/Loeschen/
  Verschieben/Laden automatisch mit ab, ohne jede einzelne Aktion
  separat verdrahten zu muessen. Die bestehende Klick-Meldung bleibt als
  letzte Sicherung bestehen. Sechs neue Tests, per zwei unabhaengig
  entfernten Aufrufen als echte Regression verifiziert; live in der SIM
  bestaetigt (Button startet sichtbar gesperrt ohne Auswahl, kein Fehler
  im Log). Zweites Paket: `update_operation_action_button_states()` steuert
  Loeschen/Hoch/Runter aus Auswahl, Programmkopf und Listengrenzen. Der
  Programmkopf ist auch in den Handlern gegen Verschieben abgesichert; der
  erste Bearbeitungsschritt kann nicht ueber ihn geschoben werden. Sieben
  neue Tests, 808/76 bestanden; Embedded-Start bis `critical done` nach
  9,025 s. Noch offen: "Aenderungen speichern" am Dirty-State ausrichten und
  die verbleibenden QMessageBox-Klick-Validierungen einzeln bewerten.
  Aktueller Regressionfix: Vorschau wieder an erster Stelle oberhalb der
  Parameter; Schnittansicht wird nach dem verzögerten Laden des Preview-Panels
  erneut eingerichtet statt durch einen zu fruehen Done-Marker dauerhaft
  uebersprungen. Gesamtstand danach 809/76 Tests.

## LES-044 Darstellung und Texte

- [ ] reine Vorschaugeometrie von Qt-Zeichenbefehlen weiter trennen; das Muster
  von `compute_tool_preview_layout()` verwenden.
- [x] Entscheidung (2026-09-14) umgesetzt: G-Code-Kommentare (Werkstatt-
  kommentare im erzeugten `.ngc`) sind jetzt sprachabhaengig wie die
  UI-Texte. Die Step-Beschreibung selbst (`_describe_operation()`, landet
  ueber `update_auto_comment()` im `(STEP: ...)`-Kommentar) war bereits
  ueber `_tr()` sprachabhaengig - der eigentliche Fund war, dass die
  gcode_*.py-Generatormodule selbst rund 70 weitere, hart-deutsche
  Kommentare direkt in den G-Code schreiben (Anfahrhinweise, Sicherheits-
  block, Gewinde-/Schrupp-Parameter), voellig unabhaengig von `_tr()`.
  Neue, bewusst von `translations.py`/qtpy entkoppelte Funktion
  `gcode_comment()` (`gcode_utils.py`) mit eigenem `.lng`-Parser - der
  Generator darf keine Qt-Abhaengigkeit bekommen ("Der Generator ist von
  Qt getrennt"), sonst waere `regenerate_all_ngc.py` ohne PyQt5 kaputt
  gegangen (echter Fund waehrend der Umsetzung, per Regressionstest
  abgesichert). 64 neue Uebersetzungsschluessel in de/en/es.lng, alle
  sieben betroffenen gcode_*.py-Dateien umgestellt. Bewusst NICHT
  angefasst: Validierungs-/Warnmeldungstexte aus `checks.py`/
  `get_machine_limit_warnings()` (eigenes, groesseres Thema - naeher an
  "Fehlertexte" als an "Werkstattkommentare") sowie eine Handvoll bereits-
  englische Struktur-/Diagnosemarker (Subroutine-Grenzen, "Pass N:
  X-band/Z-band"-Debugspur). Alle zwoelf Referenzen neu generiert und mit
  `rs274` bestaetigt (drei Referenzen minimal geaendert: ein rohes "ß" in
  einem bisher nicht sanitisierten Kommentar wurde beim Umbau konsistent
  wie alle anderen Kommentare zu "ss" transliteriert - reiner
  Zeichensatz-Fund, keine Bedeutungsaenderung), 43 Matrixfaelle weiterhin
  fehlerfrei. 795 Stub-/76 Real-Qt-Tests bestanden.
- [ ] breite `except Exception`-Fallbacks pro migriertem Modul pruefen: erwartete
  Qt-/Host-Ausnahmen gezielt behandeln, unerwartete Fehler mindestens loggen.

## LES-028 Eingaben normalisieren

- [x] Entscheidung (2026-09-14) umgesetzt: `validate_tool_table_completeness()`
  (`checks.py`) blockiert die Programmerzeugung jetzt hart, wenn eine
  verwendete Werkzeugnummer in der geladenen Werkzeugtabelle fehlt -
  aufgerufen aus `generate_program_gcode()` direkt nach den bestehenden
  Pflichtfeld-Checks. Bewusst nur aktiv, wenn ueberhaupt eine (nicht-leere)
  Tabelle vorliegt: reine Generatortests/die Referenzregeneration ohne
  echtes `tool.tbl` bleiben unveraendert ungeprueft, sonst waeren alle
  35+ bestehenden Generator-Testdateien betroffen gewesen. Die urspruengliche
  "ISO/Radius fehlt"-Meldung in `tools.py` (separates Thema: fehlende
  Metadaten bei vorhandenem Eintrag) bleibt unveraendert eine Warnung.
  Sieben neue Tests (`tests/test_tool_table_completeness_check.py`,
  isoliert und End-to-End durch `generate_program_gcode()`), per
  deaktiviertem Check als echte Regression verifiziert. Alle zwoelf
  Referenzen neu generiert (keine Abweichung), `rs274` sowie 43
  Matrixfaelle weiterhin fehlerfrei. 779 Stub-/76 Real-Qt-Tests bestanden.
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
