# Changelog

## [Unreleased]
- Branching: Neue Änderungen werden zuerst auf `DEV` gesammelt und müssen dort getestet werden, bevor sie nach `main` migriert werden
- Release-Policy: `main` bleibt als lauffähige Basis; neue Arbeit wird erst nach Test auf `DEV` übernommen
- Preview: Aktive Kontur wird in der Seitenvorschau immer im Vordergrund gezeichnet
- Preview: Seitenvorschau bildet X aus Durchmesserprogrammierung korrekt als Radius ab
- Preview: Zusatzvorschau als Vorderansicht für den aktuellen Z-Schnitt eingebaut
- Preview: Einstich-/Nutgeometrie folgt in der Vorschau jetzt den Maskenwerten für OD, ID und Stirnlagen
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
