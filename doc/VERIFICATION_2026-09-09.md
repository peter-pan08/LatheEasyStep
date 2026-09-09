# Fortsetzung und Pruefstand 2026-09-09

Nachtrag: WSL/LinuxCNC wurde anschliessend installiert. Der folgende Bericht
beschreibt den Stand davor; den aktuellen Parsernachweis, die anschliessenden
Korrekturen und 516 + 44 Tests dokumentiert der
[WSL-Interpreterbericht](linuxcnc_2026-09-09/README.md).

Basis: Branch `DEV`, Sicherungscommit `9e85644`. Dieser enthielt bereits
die erste LES-013-Umsetzung. Vor weiteren Aenderungen bestanden hier
478 Stub-Tests und 43 Real-Qt-Tests. Der Bericht vom 08.09. bleibt historisch.

## Umgesetzt

- LES-013: vorbereitete CSS-Aktivierung wird bei jedem neuen Spindelauftrag
  verworfen, auch bei G97-Fallback. Ganzzahlige CSS-Drehzahlgrenzen werden
  abgerundet; Anfahrdrehzahl ueberschreitet sie nicht. Grenzen unter 1 U/min
  werden abgewiesen. Bestehende Berechnung und Aktivierung nach der
  Operationsanfahrt durch Regressionen abgesichert.
- Gemischtes Referenzprogramm `CSS_Wechsel.ngc`: Planen mit Vc 120,
  Bohren mit 900 U/min, Planen mit Vc 180. Echtes PyQt5, Programmdatei-
  Roundtrip, Formularbindung und identische G-Code-Ausgabe getestet.
- LES-040/028: Bohrmodus darf weder abgeschnitten noch durch einen anderen
  Zyklus ersetzt werden. Vorschub und Zustelltiefe muessen auch nach
  Ausgabe mit drei Nachkommastellen positiv sein, Verweilzeit nichtnegativ.
  Direkter Bohrgenerator prueft Zahlen vor Spindel-/Bewegungsplanung.
  Bohren fordert ausdruecklich G97 an. Fehler beim Export lassen eine
  vorhandene G-Code-Datei unveraendert.
- Gemeinsame Zahlenleser lehnen defekte explizite Werte ab, statt eine
  andere Alias-Dimension oder einen Standardwert einzusetzen. Ganzzahlige
  Parameter werden mit `whole_number` validiert; leere optionale Felder
  und gueltige alte Zahlenstrings bleiben kompatibel.
- LES-003/012/015: Innenradius in beiden Konturrichtungen und drei Modi
  getestet. Mehrere Schrupppaesse, keine Innen-G71/G72-Ausgabe, Schnitt-X
  oberhalb XRI, erhaltene Schlichtboegen und identische Primitive-Ausgabe
  fuer direkten Schlichtweg und Kontur-Subroutine geprueft. Bogenradien
  werden aus ausgegebenen X/Z/I/K-Werten im G7-Masssystem verglichen.
  `Innen_Radius.ngc` enthaelt `G3 ... I1.000 K0.000` als neue Referenz.
- Testumgebung lokal eingerichtet; direkte Abhaengigkeiten in
  `requirements-test.txt` festgehalten. README-Widersprueche bereinigt.

Vor den Korrekturen scheiterten zehn neue CSS-/Bohrfaelle und sieben
Zahlenleser-Faelle am alten Verhalten. Ein alter Test, der unbekannte
Bohrmodi absichtlich als G81 akzeptierte, fordert jetzt den Fehler.

## Verifikation

Windows, Python 3.14.7, Projekt-`.venv`, Qt offscreen:

```text
.venv/Scripts/python run_tests.py -p no:cacheprovider --tb=short
513 passed (Stub-Qt)
44 passed (echtes PyQt5)
0 skipped

.venv/Scripts/python -X utf8 regenerate_all_ngc.py
11 Dateien, 1485 Zeilen

.venv/Scripts/python validate_ngc.py
88 statische Checks, 0 Probleme
```

Die bisherigen neun NGC-Dateien bleiben nach Regeneration unveraendert.
Die beiden neuen Referenzen wurden gelesen: CSS-Reihenfolge und Einheiten,
Innenradius mit I=1, Schrupppaesse und Schlichtbogen nachvollzogen.
Qt testet mit isolierter qtvcp.Action, ohne HAL-/Maschinenverbindung.

## Offene Grenzen

`check_linuxcnc.py` meldet fehlendes `rs274`. `wsl --list --quiet` meldet,
dass WSL auf diesem Rechner nicht installiert ist. Keine neue LinuxCNC-,
Backplot-, Panel- oder Trockenlaufabnahme.

LES-013 bleibt offen fuer die vollstaendige Freifahrt-/Werkzeugwechsel-
Modalsequenz, die fachliche Pruefung aller Aktivierungsdurchmesser und die
LinuxCNC-Abnahme. Der Zustand von G96 bei Rueckzuegen und vor der naechsten
Operationsanfahrt ist damit noch nicht zentral geplant.

LES-005 bleibt offen: Der explizite Innen-Schlichtweg faehrt am Ende noch
axial auf safe_z, bevor der gemeinsame radiale Rueckzug folgt. Die neue
Radiusmatrix belegt Geometrie und Schnittgrenzen, keine kollisionsfreie
Ein-/Ausfahrt oder Werkzeughuelle. LES-001/039 benoetigen weiterhin
Startzustand, Werkzeugdaten und Maschinenoffsets.

LES-040/028 sind Teilumsetzungen: Wertebereiche aller Generatoren,
normalisierte Werkzeugdaten und Ausgabegrenzen aller Zahlen fehlen noch.
DIN-Normwerte wurden nicht geschaetzt; Architektur- und Performance-
Aufgaben bleiben im TODO. Kein P0-Blocker wird durch diesen Bericht als
maschinenfreigegeben erklaert.

Technische Referenz fuer G96/G97 und D/S-Einheiten:
[LinuxCNC G-Codes](https://linuxcnc.org/docs/stable/html/gcode/g-code.html#gcode:g96-g97).
