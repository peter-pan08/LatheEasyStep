# Changelog

## [Unreleased]
- Architektur: Strikte Trennung von UI und Sprache eingefuehrt: sichtbare Texte werden nicht mehr aus Python-/UI-Fallbacks hergeleitet, fehlende Eintraege zeigen den jeweiligen Schluessel/ID
- Architektur: Tooltip-Fallback-Ableitung aus Label-/Widget-Texten deaktiviert; Tooltips kommen nur noch aus expliziten Uebersetzungskeys
- UI-Logik: Kritische Auswahl-/Sichtbarkeitslogik auf technische IDs (`currentData`) umgestellt statt auf lokalisierte Anzeige-Texte (`currentText`)
- Kontur-Editor: Segment-Combos (Kante, Bogen-Seite, Feature, Innen/Aussen, Start/Ende) nutzen nun stabile interne IDs in `itemData`
- Programmkopf: Relevante Combo-Werte werden beim Sammeln/Laden als technische Werte gespeichert/verarbeitet (sprachunabhaengig)
- Tests: Sprach-/Tooltip-Regressionen an den strikten ID-only Modus angepasst; fokussierte Regressionen laufen gruen (`22 passed`)
- Safety: Innen-Gewinde und Innen-Abspanen erzwingen jetzt ein plausibles `XRI`; ohne gueltige Innen-Rueckzugsebene bricht die G-Code-Erzeugung mit einer klaren Fehlermeldung ab
- Safety: Innen-Gewinde und Innen-Abspanen verwenden jetzt op-spezifische sichere Anfahr- und Rueckzugsebenen ueber `XRI/ZRI` statt pauschal `XRA/ZRA`
- Abspanen: Interner `G71`-Startdurchmesser wird jetzt aus Kontur und Innen-Rueckzug fachlich korrekt abgeleitet; unplausible `X0/Z0`-Zyklusstarts fuer Innenkonturen werden nicht mehr erzeugt
- Abspanen: Innen-Schlichtschnitt mit aktiver Schneidenradiuskorrektur bekommt jetzt einen echten Einfahrweg, damit LinuxCNC keine Fehler wegen zu kurzer Kompensations-Einfahrt meldet
- Tests: Regressionen fuer `XRI`-Pflicht, Innen-Anfahrlogik, `M30`-Programmende und Subroutinen-Reihenfolge erweitert
- Tests: Referenz- und Regressionsstand auf `202 passed` angehoben
- Gewinde: Gewinde-Reiter um `Gewindestart Z` sowie separate Rechts-/Linksgewinde-Auswahl erweitert; Werte laufen jetzt durch UI, Save/Load, Vorschau und Generator
- Gewinde: Vorschau und G-Code unterscheiden jetzt alle vier Kombinationen aus Innen/Aussen und Rechts/Links; Start-Z und Gewinderichtung steuern Anfahrpunkt, Endpunkt und Z-Laufrichtung
- Gewinde: Zusaetzliche Plausibilitaetswarnungen fuer identische Start-/Endpunkte sowie Start-/Endlagen ausserhalb des Werkstueck-Z-Bereichs
- Kontur: Step-Liste benennt Konturen jetzt fachlich neutral als `Kontur: <Name>`
- UI: Tooltip-Anzeige um einen erzwungenen Hover-/ToolTip-Relay erweitert, damit Tooltips auch im eingebetteten QtVCP-Pfad robuster erscheinen
- Tests: Gewinde-Regressionen fuer Rechts-/Linksgewinde, Innen-/Aussengewinde und variable Start-Z-Positionen ergaenzt
- G-Code: Hauptprogrammfluss wird jetzt vor den O-Subroutinen ausgegeben, damit LinuxCNC nicht mehr in die Einstich-/Abstich-Bibliothek hineinfaellt und Groove-Zyklen nicht endlos neu starten
- Toolchange: Werkzeugwechsel- und Parkposition haben jetzt eine explizite Auswahl fuer `Werkstueckkoordinaten` oder `Maschinenkoordinaten (G53)` statt der fachlich missverstaendlichen Altlogik ueber `absolut / inkrementell`
- Toolchange: Legacy-Dateien mit gemischter XT/ZT-Logik bleiben kompatibel; neue Programme erzeugen koordinatensystemsauberen Werkzeugwechsel- und Park-G-Code
- Toolchange: Regressionspruefung gegen reales Testprogramm `Test.ngc` nachgezogen; der Generator emittiert nach `T.. M6` kein zusaetzliches `G0 X0 Z0`, der anschliessende manuelle Wechselpfad kommt aus der LinuxCNC-Konfiguration (`TOOL_CHANGE_MODE = MANUAL`, `hal_manualtoolchange`)
- UI: Tooltips werden jetzt tief auf Ziel-Widget, Label, Editor und Combo-View propagiert und fuer Embedded-/Standalone-Betrieb explizit aktiviert
- Validierung: Fehlermeldungs-Mapping ist jetzt pro Operationstyp gehaertet und verweist nur noch auf tatsaechlich vorhandene UI-Felder
- Presets: Gewinde- und DIN-Freistich-Presets in `lathe_easystep/presets/` zentralisiert und fuer metrische Groessen bis `M30` erweitert
- Gewinde: DIN-Freistich-Helfer und Gewindevorschlaege greifen jetzt ueber zentrale Preset-Helper zu statt auf verstreute Tabellen
- Tests: Neue Regressionen fuer Groove-Subroutine-Reihenfolge, explizite Toolchange-/Park-Koordinatensysteme, Keyway-Validierung und generatorseitig fehlende `X0/Z0`-Zusatzfahrt
- Workflow: Sichtbarer Dirty-State fuer Programm und Steps eingebaut; `Aenderungen speichern` markiert offene Aenderungen jetzt direkt im UI
- Workflow: Reiter- und Stepwechsel warnen jetzt bei ungespeicherten Aenderungen und speichern weiterhin keine Dateien automatisch
- UI: Groove-Reiter um klare Betriebsart `Einstich` / `Abstich` erweitert; partingspezifische Reduktionsfelder werden kontextabhaengig ein-/ausgeblendet
- UI: Vorschau wird beim finalen Layout jetzt ausserhalb des Scrollbereichs angedockt und bleibt als fester Kontrollbereich sichtbar
- UI: Zentrale Tooltips fuer Rueckzugsebenen, Futtergrenzen, CSS/G96, Parklogik, Freistich-/Hinterschnitt-Optionen und Groove/Abstich komplettiert
- UX: Generator- und Speichermeldungen werden fuer Anwender jetzt auf Reiter/Feld-Ebene benutzerverstaendlicher formatiert
- Uebersetzungen: Restliche Mischtexte in Drill-/Groove-/Advanced-Widgets und relevanten Groove-Makrokommentaren bereinigt
- Kontur: Datenmodell fuer Konturfeatures um DIN-Freistich/Hinterschnitt erweitert; Segment-Features koennen jetzt als Teil der Konturgeometrie beschrieben werden
- Kontur: Neue DIN-Freistich-Tabelle `M3` bis `M30` mit Aussen-/Innen-Varianten sowie Breite, Tiefe und Uebergangsform angelegt
- Kontur: Generator leitet jetzt drei Geometrievarianten aus derselben Kontur ab: Fertigkontur, Schruppkontur ohne Hinterschnitt und Feature-Teilkontur
- Abspanen: Bearbeitungsmodi fuer Hinterschnitt/Freistich umgesetzt (`ignore`, `finish_only`, `separate`, `full`)
- Abspanen: Generator dokumentiert Strategie, Ausgabe-Praeferenz, Aufmass und Hinterschnitt-Modus jetzt explizit im G-Code
- Abspanen: Fallback-Gruende fuer Move-based Roughing werden systematisch ausgegeben statt nur punktuell
- Abspanen: Expertenoption fuer Ausgabeart (`auto`, Zyklus bevorzugen, ausgeschriebener Code bevorzugen) in der Generatorlogik verdrahtet
- UI: Expertenoptionen fuer Hinterschnitt-Modus, Ausgabe-Praeferenz, CSS/G97, Parklogik und optionale Stops in das Panel eingebunden
- UI: Kontursegment-Editor um DIN-Freistich-Felder fuer Feature, Gewindegroesse, Norm, Innen/Aussen und Start/Ende erweitert
- Workflow: Save/Load und Formularbindung fuer die neuen Experten- und Konturfeature-Parameter vervollstaendigt
- Safety: Vor jedem `T.. M6` wird jetzt `M5` erzwungen; Werkzeugwechsel fahren weiterhin mit Sicherheitsrueckzug und Toolchange-Position
- Safety: Anfahrt und Rueckzug pruefen jetzt Startpunkt im Rohteil, Startpunkt in der Futter-Sperrzone und kritische Rueckzugsebenen und markieren diese als Warnung
- Safety: Plausibilitaetswarnungen fuer `XT/ZT`, `XRA/XRI`, `ZRA/ZRI` ausserhalb sinnvoller Rohteil-/Maschinenbereiche ergaenzt
- Safety: Optionale Haltepunkte vor separatem Hinterschnitt sowie CSS/Festdrehzahl-Ausgabe (`G96`/`G97`) mit Max-RPM-Fallback eingebaut
- Workflow: Endparklogik um konfigurierbare Parkposition und sequentielle Endbewegung erweitert
- Validierung: Zusaetzliche Pruefungen fuer `G76`, DIN-Freistich-Parameter, separates Hinterschnitt-Schruppen und Werkzeugbreite eingebaut
- Validierung: Werkzeug-/Operations-Plausibilitaet um Innen/Aussen-Hinweise und Spezialwerkzeug-Checks erweitert
- Gewinde: DIN-Freistich kann fuer Gewinde jetzt als Vorschlag kommentiert werden, ohne blind erzeugt zu werden
- Preview: Roughing- und Freistich-Geometrie werden fuer `ABSPANEN` unterscheidbar ueberlagert; Warnungen koennen im Preview eingeblendet werden
- Tests: Neue Regressionen fuer Freistich-Varianten, Sicherheitswarnungen und `M5` vor jedem Werkzeugwechsel hinzugefuegt
- Tests: Save/Load, CSS/Parklogik, Gewinde-Freistich-Vorschlag und optionale Stops zusaetzlich abgesichert
- Tests: Dirty-State, Groove/Abstich-Sichtbarkeit, benutzerfreundliche Fehlermeldungen und Snapshot-Normalisierung zusaetzlich abgesichert
- Tests: Referenzprogramme regeneriert; aktueller Stand mit `202 passed` verifiziert

## [0.7.0] - 2026-07-08

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
