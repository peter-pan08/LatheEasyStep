# TODO LatheEasyStep

Stand: 2026-09-15

Diese Datei enthaelt ausschliesslich offene Aufgaben. Abgeschlossene Arbeiten,
Befunde und historische Teststaende stehen im [CHANGELOG.md](CHANGELOG.md) und
in den Berichten unter `doc/`. Release-Ziele stehen in [ROADMAP.md](ROADMAP.md).

## Verifizierte Basis

- Branch `dev`, Entwicklungsstand fuer 0.8.0; `main` bleibt stabile 0.7.0-Basis.
- 838 Stub-Qt-Tests und 102 Tests mit echtem PyQt5, keine Skips.
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
| LES-044 | P2 | Darstellungs- und Textschichten weiter entkoppeln | L-XL | 0.9.0 |
| LES-032 | P2 | reale Werkzeuggeometrie fuer Plausibilitaet/Kollision auswerten | L | 0.9.0 |
| LES-043 | P2 | Gegenspindelfunktion als eigenes Projekt spezifizieren (UI bleibt gesperrt sichtbar) | XL | separat |
| LES-030 | extern | weitere physische Maschinenprofile verifizieren | extern | offen |

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
- [x] Entscheidung (2026-09-15) umgesetzt: breite `except Exception`-
  Fallbacks in den vier Vorschau-Modulen (`preview_geometry.py`,
  `preview_widget.py`, `preview_scene.py`, `ui_preview.py`) durchgesehen -
  72 von 82 Fundstellen fingen Ausnahmen bisher vollstaendig still ab
  (kein Log, kein Hinweis), obwohl ein echter Bug dahinter unbemerkt
  bliebe. Entscheidung mit dem Nutzer geklaert: kleinster Schritt zuerst -
  nur Logging ergaenzen, Ausnahmetypen NICHT einschraenken und Verhalten
  NICHT aendern (die vollstaendige Einzelbewertung je Fundstelle auf
  "welcher Fehlertyp ist hier eigentlich erwartet" bleibt ein separates,
  groesseres Thema). Jede zuvor stille Stelle bekommt jetzt
  `_LOGGER.debug("[LatheEasyStep] <Funktion>: unexpected exception
  suppressed: %s", exc)` als ersten Befehl im except-Block; wo noch kein
  `as exc` vorhanden war, wurde das ergaenzt. `preview_geometry.py`/
  `preview_scene.py` bleiben bewusst Qt-frei - `logging` ist Standard-
  bibliothek, keine neue Qt-Abhaengigkeit. Per Skript erzeugt und manuell
  gegengeprueft (Syntax, Importplatzierung, ein direkter Spotcheck mit
  `logging.basicConfig` bestaetigt: die Meldung erscheint mit korrekter
  Funktion und Fehlertext, Verhalten unveraendert). Volle Stub- und
  Real-Qt-Suite unveraendert gruen (825/102) - reine Zusatzausgabe, keine
  neuen Tests noetig (die bestehende Suite deckt bereits ab, dass sich am
  Verhalten nichts geaendert hat). Die vollstaendige Einzelbewertung
  (Ausnahmetypen gezielt einschraenken) bleibt bewusst offen fuer eine
  spaetere, groessere Iteration.

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
- [x] Entscheidung (2026-09-15) umgesetzt: `T{tool_num:02d} M6` wird bereits
  heute nur mit einer per `validate_tool_table_completeness()` vorab gegen
  die Tabelle geprueften Nummer erzeugt - ein woertlicher Umbau auf
  "Nummer aus dem `Tool`-Objekt statt aus den rohen Operationsparametern
  lesen" waere in diesem Datenmodell folgenlos gewesen (der Dict-Schluessel
  in `tools` IST bereits `Tool.t`, keine zweite unabhaengige Ableitung).
  Stattdessen einen echten, bisher komplett ungenutzten Datenpunkt aus dem
  normalisierten Datensatz aktiviert: `Tool.kind` (aus der Q-Orientierung
  der Werkzeugtabelle geparst, `tools.py::tool_kind_from_orientation()`)
  wurde nirgends gegen den tatsaechlich verwendeten Operationstyp geprueft
  - ein Werkzeug, dessen Q-Wert laut Tabelle z. B. auf ein Bohrwerkzeug
  hindeutet, konnte unbemerkt einer Stech- oder Gewinde-Operation
  zugewiesen werden. Neue `_check_tool_kind_matches_operation()`
  (`checks.py`), in `validate_program_setup()` verdrahtet (bereits aktive
  Warnungs-Pipeline, landet in `prog["__warnings"]` im Preview UND als
  `(WARN: ...)`-Kommentar im erzeugten G-Code-Kopf). Bewusst konservativ:
  nur bei tatsaechlich gesetzter Q-Orientierung geprueft (`tool.orientation
  is None` liefert nur den Fallback "turning", keine echte Klassifikation)
  und `kind == "parting"` (Fallback fuer JEDEN nicht zugeordneten Q-Wert)
  wird nie als Widerspruch gewertet - beides haette sonst zu
  Falschmeldungen bei unklassifizierten Werkzeugen gefuehrt. Bei der
  Recherche zusaetzlich bestaetigt (und durch einen bereits vorhandenen
  Testkommentar in `tests/test_tool_warning_wiring.py` gedeckt): die
  parallele, aehnliche Pruefung `tool_logic.py::collect_tool_orientation_warnings()`
  ist bewusst tote, redundante Zweitimplementierung eines in `checks.py`
  bereits aktiven Innen-/Aussen-Checks - kein neuer Fund, nur zur
  Einordnung bestaetigt. Neun neue Tests
  (`tests/test_tool_kind_mismatch_check.py`), per entferntem Verdrahtungs-
  Aufruf als echte Regression verifiziert. Alle zwoelf Referenzen neu
  generiert (keine Abweichung - die Referenzbeispiele verwenden durchweg
  passende Werkzeuge), `rs274` sowie 43 Matrixfaelle weiterhin fehlerfrei.
  834 Stub-/102 Real-Qt-Tests bestanden.
- [x] Preset- und manuelle Werte nachvollziehbar verglichen: Der einzige
  dauerhaft doppelte Datensatz ist das Gewinde-Preset (`standard`) neben den
  editierbaren G76-Werten. `thread_preset_values()` ist nun die gemeinsame,
  Qt-freie Sollwertberechnung fuer UI und Pruefung. Presetwechsel setzen
  Durchmesser/Steigung und fuellen die uebrigen leeren Felder weich; der
  explizite Preset-Button ueberschreibt weiterhin bewusst alle Presetwerte.
  Manuelle Abweichungen bei Durchmesser, Steigung sowie allen sieben
  abgeleiteten Bearbeitungswerten bleiben erlaubt, erscheinen aber gesammelt
  als Warnung in Vorschau und G-Code-Kopf. Dabei einen echten Fehler behoben:
  der Rekursionsschutz verhinderte zuvor den gesamten Soft-Fill nach einem
  Presetwechsel. Maschinen-/Futterprofile werden dagegen sofort in konkrete
  Programmkopfwerte aufgeloest und speichern keinen konkurrierenden
  Presetdatensatz. Vier neue Tests, Gesamtstand 838/102. LES-028 abgeschlossen.

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
