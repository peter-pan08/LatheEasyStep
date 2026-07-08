# Changelog

## [Unreleased]
- Refactor: Vorschau-Geometrie-Helfer in `lathe_easystep/preview_geometry.py` gebuendelt und fuer Model/UI als neue Einstiegsschicht verdrahtet
- Refactor: Kontur-Geometrie und Kontur-Validierung in `lathe_easystep/contour_logic.py` aus dem Handler herausgeloest
- Refactor: Neue G-Code-Einstiegsmodule `gcode_program.py`, `gcode_roughing.py`, `gcode_safety.py` und `gcode_utils.py` als kompatible Zerlegung von `slicer.py` angelegt
- Tests: Referenzprogramme und Vertrags-Regressionen fuer Snapshot-G-Code, Save/Load, `G20`, FACE/G72-Profil und Sicherheitsrueckzuege aufgebaut
- Tests: `regenerate_all_ngc.py` regeneriert jetzt sechs Beispielprogramme als Smoke-Basis (`python3 regenerate_all_ngc.py`)
- Tests: Gemeinsamer Smoke-Run in `smoke_test.py` ergaenzt; aktueller Stand validiert mit `171 passed`

## [0.6.1] - 2026-07-08
- Refactor: `Operation`, `ProgramModel` and `OpType` moved out of `lathe_easystep_handler.py` into `lathe_easystep/model.py`
- Refactor: Werkzeugtabellen- und ISO-Helfer in `lathe_easystep/tools.py` ausgelagert
- Refactor: Step-/Programm-Payload-Helfer in `lathe_easystep/persistence.py` ausgelagert
- Refactor: Dateiverknüpfung und Programm-Metadaten in `lathe_easystep/storage.py` ausgelagert
- Refactor: Program-Header-UI-Logik in `lathe_easystep/ui_program.py` ausgelagert
- Refactor: Formularbefüllung für Operationen in `lathe_easystep/ui_operations.py` ausgelagert
- Refactor: Preview-Aufbereitung und Preview-Widget-Ansteuerung in `lathe_easystep/ui_preview.py` ausgelagert
- Refactor: Parameter-, Auswahl-, Persistenz-, Werkzeug-, Sichtbarkeits- und Ablauf-Logik in weitere UI-Module unter `lathe_easystep/` aufgeteilt (`ui_params.py`, `ui_selection.py`, `ui_persistence.py`, `ui_tools.py`, `ui_visibility.py`, `ui_flow.py`, `ui_widgets.py`, `ui_signals.py`, `ui_lifecycle.py`)
- Refactor: Kontur- und Einstich-spezifische UI-Logik in `ui_contour.py` und `ui_groove.py` ausgelagert
- Refactor: Werkzeugnahe Fachlogik in `lathe_easystep/tool_logic.py` ausgelagert
- Refactor: Bohr-, Plan-, Gewinde-, Einstich- und Keyway-G-Code in eigene Module unter `lathe_easystep/` aufgeteilt
- Verifikation: Refactor-Stand mit `pytest -q` erfolgreich getestet (`165 passed`)
- Docs: README neu strukturiert, Versionsstand am Anfang sichtbar gemacht und um englische Betriebs-/Workflow-Informationen erweitert

## [0.6.0] - 2026-07-08
- Branching: Neue Änderungen werden zuerst auf `DEV` gesammelt und müssen dort getestet werden, bevor sie nach `main` migriert werden
- Release-Policy: `main` bleibt als lauffähige Basis; neue Arbeit wird erst nach Test auf `DEV` übernommen
- Preview: Aktive Kontur wird in der Seitenvorschau immer im Vordergrund gezeichnet
- Preview: Seitenvorschau bildet X aus Durchmesserprogrammierung korrekt als Radius ab
- Preview: Zusatzvorschau als Vorderansicht für den aktuellen Z-Schnitt eingebaut
- Preview: Seitenansicht und Schnittansicht bleiben gleichzeitig sichtbar; die Seitenansicht zeigt die aktive Schnittlage als markierte Linie
- Preview: Schnittlage kann direkt in der Seitenansicht verschoben werden; die Vorderansicht aktualisiert sich auf die gewählte Z-Position
- Preview: Vorderansicht wertet jetzt das gesamte Programm statt nur den aktuell markierten Step aus
- Preview: Vorderansicht nutzt eine feste Referenz auf den maximalen Werkstückdurchmesser, damit Konen und Durchmesserwechsel optisch klar kleiner oder größer werden
- Preview: Aktuelle Endgeometrie der Schnittansicht wird zusätzlich flächig hervorgehoben, nicht nur numerisch angegeben
- Preview: Einstich-/Nutgeometrie folgt in der Vorschau jetzt den Maskenwerten für OD, ID und Stirnlagen
- Keyway: Reiter um Werkzeugauswahl, Winkelversatz für Wiederholungen und zusätzliche Bearbeitungsparameter erweitert
- Keyway: Winkelfelder korrekt auf Grad umgestellt; irreführende mm-Einheit entfernt
- Keyway: Nutenstossen ohne unnötige Drehzahl-Eingabe bereinigt, da das Werkstück zwischen den Positionen stillsteht
- Keyway: Winkelversatz der Nutmitten wird jetzt konsistent in Vorschau und Step-Daten verwendet
- Keyway: Reiterwechsel selektiert jetzt den zugehörigen Keilnut-Step in der Liste, damit Laden, Bearbeiten und Speichern auf dieselbe Operation wirken
- Keyway: Parametereingaben werden nach dem UI-Aufbau jetzt zuverlässig mit dem Handler verdrahtet; Änderungen wirken dadurch auf Vorschau, Step-Liste und Dateispeicherung
- Workflow: Dateidialoge merken sich den zuletzt verwendeten Ordner für Step-, Programm-, G-Code- und Werkzeugdateien
- Workflow: Zuletzt geladene Werkzeugtabelle wird beim Start des Panels automatisch wieder geladen
- Workflow: Neuer Button `Änderungen speichern` aktualisiert verknüpfte Steps, Programme und vorhandene G-Code-Dateien direkt aus der aktuellen Maske
- Workflow: Programme speichern jetzt Metadaten zu verknüpften Step- und Programmdateien, damit Änderungen später gezielt zurückgeschrieben werden können
- Workflow: Jeder neue Bearbeitungsschritt erhält eine eigene Step-Datei; Programmspeichern stellt diese Verknüpfung ebenfalls sicher
- Workflow: Programmkopf wird beim Laden und beim Wechsel auf den Program-Tab jetzt konsistent in die Eingabemaske zurückgeschrieben
- Fix: Interne Dateimetadaten (`__step_file_path`, `__program_file_path`, `__gcode_file_path`) bleiben bei Parameteränderungen erhalten
- Fix: Startfehler in der Initialisierung durch fehlende Preview-/Combo-Attribute behoben
- Fix: Auto-Load der Werkzeugtabelle scheitert nicht mehr an fehlenden `tool_table_path`-Referenzen im Frühstart
- Performance-Fix: LinuxCNC-Embedded-Start massiv verkürzt; GUI und Panel sind wieder nach rund 11 Sekunden benutzbar
- Refactor: Widget-Auflösung strikt auf den Panel-Baum begrenzt, keine globalen `allWidgets()`-Scans mehr
- Refactor: Root-Erkennung für Embedded-Panel stabilisiert, Host-`MainWindow` wird nicht mehr fälschlich als Panel benutzt
- Fix: Initialisierung und Signalverdrahtung so umgebaut, dass Embedded-Start wieder funktional bleibt
- Cleanup: aufwendige Startup-Debug- und Refresh-Schleifen entfernt bzw. stark reduziert
- Cleanup: `widget_ids.json` auf echte Panel-Widgets reduziert, um unnötige Persistenz- und Lookup-Kosten zu vermeiden
- Echte Radius-Geometrie (Fillet-Berechnung)
- Innen/Außen-Auswahl pro Radius
- Verbesserte Konturvorschau
- Überarbeitung der Abspan- und Retract-Logik
- README / DEV.md / Changelog neu strukturiert
- Fix: Im Embedded-Betrieb wird die Step-Liste jetzt strikt an `listOperations`/`list_ops` gebunden (kein Fallback mehr auf `gcode_list`)
- Fix: Laden von Einzel-Step und komplettem Programm aktualisiert die sichtbare Step-Liste zuverlässig
- Fix: Parameter-Änderungen greifen auf die aktive Operationsliste (`self.list_ops`) zu
- Verifikation: Save/Load-Regressionstests (`test_save_load_roundtrip.py`, `test_step_double_click.py`) wurden aufgebaut und zuletzt zur Absicherung der Embedded-Step-Logik verwendet
- Safety-Fix: Sichere Rückzugspunkte berücksichtigen jetzt `xra_absolute`/`zra_absolute` korrekt (inkrementell vs. absolut)
- Safety-Fix: Globale Rückzüge und Toolchange-Anfahrten fahren jetzt mit Z-vor-X
- Safety-Fix: `FACE`-Profil-Subroutinen für G72 verwenden nur Schnittbewegungen (`G1`), kein `G0` im Zyklusprofil
- Fix: Programme mit Einheit `inch` emittieren jetzt `G20` (statt immer `G21`)
- Safety-Fix (Drehbank-Freifahrt kontextabhängig): Standard simultan `G0 X.. Z..`, bei Einstich/Keyway erst `X`, bei Bohren/Gewinde erst `Z`
- Safety-Fix (Materialbezug): Simultane Freifahrt wird nur verwendet, wenn die Startposition außerhalb der Rohteil-Hüllzone liegt; innerhalb wird konservativ sequenziell freigefahren
- Feature: Program-Tab erweitert um Spannfutter-Auswahl (80/100/125/160/200/250), Werkstücktyp und Spannart mit automatischer Vorbelegung von No-Go-Sicherheitsmaßen
- Safety-Fix: Freifahrt berücksichtigt zusätzlich eine konfigurierbare Chuck-No-Go-Zone (`chuck_no_go_x_min/x_max/z_limit`) und erzwingt dort sequenzielles Freifahren
- Feature: Spannfutter-Profile ergänzt (`3-Backen Standard`, `Softjaws`, `Innenausdrehen`) mit profilabhängiger Anpassung der No-Go-Geometrie
- Feature: Program-Tab um `Maschinenprofil` ergänzt (schnelle Werkstatt-Presets für Futtergröße/Spannart/Profil)
- Feature: Vorschau zeigt die Futter-Sperrzone als eigene farbige Fläche inkl. Legenden-Eintrag (`Futter-Sperrzone`)
- Preview: aktive Kontur wird beim Schrittwechsel farblich hervorgehoben; Doppelklick auf Steps oeffnet wieder den passenden Reiter
- Preview: Vorschaugeometrie geladener Programme wird nach dem Laden aus den Parametern neu aufgebaut statt aus veralteten Pfad-Caches
- Hinweis: als offene Restpunkte bleiben Programmkopf-Vorschau ohne Vorselektion und fachlich genauere Gewindegeometrie

---

## [0.1.0] – Initial Development
- Erste Version des Lathe EasyStep Panels
- Grundlegende Konturdefinition
- Abspanen parallel Z
- Vorschau und G-Code-Erzeugung
- STEP/Projektdateien

---

Hinweis:
Dieses Projekt befindet sich in aktiver Entwicklung.
Änderungen an Verhalten und Dateiformaten sind möglich.
