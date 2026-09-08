# Lokaler Umsetzungs- und Pruefstand 2026-09-08

Arbeitszweig: `dev`. Diese Aenderungen sind Entwicklungsarbeit, keine
Freigabe fuer den Maschinenlauf. Historische LinuxCNC-/Panelbestaetigungen
im Changelog beziehen sich auf ihre damaligen Staende.

## Abgeschlossene Aufgaben

| TODO | Ergebnis | Nachweis |
|---|---|---|
| LES-041 | Tief kopierter Generierungssnapshot, frisch aufgeloeste Konturen/Features; keine Modellmutation | `test_generation_boundaries.py`: wiederholte Ausgabe aller neun Beispiele, Konturaenderung/Save/Load, veralteter Cache, Fehlerfall |
| LES-042 | Atomarer Ersatz der Programmdatei, bisheriger Pfad bei Fehler wiederhergestellt | Serialisierung, Dateiersatz, abgebrochene Step-Verknuepfung und echter Qt-Save/Load |
| LES-043 | Atomare Step-Dateien, Verknuepfung erst nach Erfolg, Teilfehler sichtbar, Dirty-State erhalten | Fehler beim Serialisieren/Ersetzen und Teilfehler-/unverknuepfte-Step-Tests |
| LES-038 | Stub und echtes Qt in frischen Prozessen; Qt-Namespace-Aenderungen isoliert | `run_tests.py`, `tests/conftest.py` |
| LES-023 | Automatische Step-Kommentare ohne dauerhaft gespeicherte Nummer; eigene Texte erhalten | Kommentar-/Renummerierungsregressionen |
| LES-011 | Gleiche Freistichprimitive fuer Preview-Quelle, Kontur-Sub und explizites Schlichten | Koordinatenvergleich und Feature-Save/Load in `test_internal_profile_matrix.py` |
| LES-016 | Freistichnorm bedingt sichtbar; technische IDs und alte Speicherwerte stabil | Echter Qt-Test beider Zweige, de/en/es und Save/Load |

Konturen bleiben nummerierte Geometrieschritte in der Liste, ohne eigene
Bearbeitungsbewegung. Kontur-Kantengroessen bleiben sichtbar und werden
wie bisher deaktiviert. Fuer Innen/Aussen wurde keine pauschale neue
Ausblendung eingefuehrt: Die Lage aendert die fachliche Interpretation;
alle weiterhin benoetigten Eingaben bleiben erreichbar.

## Teilumsetzungen und Grenzen

- LES-001/039: Gemeinsame Anfahrt gibt achsweise Bewegungen aus und blockiert
  Futter-Sperrzonenverletzungen, auch wenn eine Strecke die Zone nur kreuzt.
  XT/ZT werden bei jedem Werkzeugwechsel verlangt, auch beim Einzelwerkzeug.
  **Nicht geloest:** erste Freifahrt bei unbekannter Ausgangsposition/aktivem
  Werkzeug, G53-Transformation, alle direkten Moves/Zyklen und Werkzeughuelle.
  `_is_at_safe` bzw. errechnete Safe-Positionen sind kein gemessener Zustand.
- LES-040/028: NaN/Inf an Import-, Modell- und Gesamtgeneratorgrenzen blockiert,
  Werkzeugnummern ganzzahlig, defekte X/Z-Punkte nicht still entfernt.
  G76 prueft positive Steigung/Laenge/Durchmesser, Tiefen, R/H/L und Taper.
  Zahlenstrings sind gleichwertig; H=0 ist explizit null. Automatische
  Schnitttiefen bei leer/0 bleiben kompatibel. Fachliche Grenzen aller
  anderen Generatoren und ein einheitlicher Werkzeugdatensatz bleiben offen.
- LES-003/015: Vorhandenes XI unterhalb der Zielkontur wird nicht durch den
  Zieldurchmesser ersetzt. Innenaufmass laesst Material fuer das Schlichten.
  Zylinder/Stufe/Konus x beide Konturrichtungen x drei Modi sind abgedeckt.
  Innenradius, vollstaendige Ein-/Ausfahrt und reale Abnahme bleiben offen.
- LES-036: Planradius als G2 aus gemeinsamer Geometrie, analytischer Vergleich
  von Start-/Endradius und radialem I sowie echter Qt-Roundtrip. Kein
  LinuxCNC-Parser-/Backplot- oder Panelnachweis fuer diese neue Funktion.
- LES-020: Kopf-, Kontur-, Gewinde-Preset- und Tooltip-Sammlung extrahiert.
  Bootstrapping und die weitergehenden Controllergrenzen bleiben offen.
- LES-010/030: Innenstufe, mittiger Freistich und Planradius als neue
  Referenzen. Statischer Validator repariert; rs274-Batchwerkzeug vorbereitet.

Atomar ist jeweils der Ersatz einer einzelnen Programm- oder Step-Datei,
keine Transaktion ueber alle verknuepften Dateien. Bei einem Teilfehler
bleiben schon erfolgreich gespeicherte Dateien erhalten; die Fehlermeldung
nennt gespeicherte Steps und der Dirty-State erlaubt erneutes Speichern.
Vorschau und komplette Maschinenbewegungen sind noch nicht dieselbe Pipeline
(LES-022/034). DIN-Werte wurden nicht geschaetzt oder als normverifiziert erklaert.

## Ausgefuehrte Pruefungen

Windows, Python aus Projekt-`.venv`, Qt offscreen:

```text
python run_tests.py -p no:cacheprovider --tb=short
472 passed (Stub-Qt)
43 passed (echtes PyQt5)
0 skipped

python -X utf8 regenerate_all_ngc.py
9 Dateien, 1223 Zeilen

python validate_ngc.py
72 statische Checks bestanden, 0 Probleme
```

Die Real-Qt-Suite nutzt echtes PyQt5/qtpy, aber eine isolierte qtvcp.Action;
sie prueft UI-Verhalten und verbindet sich nicht mit HAL oder einer Maschine.
Bestehende Referenz-Diffs: G91.1 im Kopf und Wegfall redundanter Z-Werte
auf gemeinsamer Safe-Ebene; neue Referenzen wurden zusaetzlich gelesen.
`git diff --check` nach Bereinigung ohne Befund.

## Noch auszufuehren

Im Windows-Pfad ist kein `rs274` verfuegbar. Der erneute WSL-Aufruf
brach beim VM-Start mit Timeout `0x800705b4` ab. `check_linuxcnc.py` meldet den fehlenden
Interpreter als Fehler; ein erfolgreicher realer Lauf wird nicht behauptet.
Auf einem LinuxCNC-System:

```text
python3 check_linuxcnc.py --interpreter /pfad/zu/rs274
```

Der Runner verwendet eigene temporaere Parameter und eine synthetische
Werkzeugtabelle. Er ersetzt weder Backplot mit realen Offsets noch Trockenlauf.
Vor Release bleiben insbesondere LES-001/003/005/037/039/040 sowie
LinuxCNC- und Panelabnahme der geaenderten Fahrwege offen. Fuer die
weitergehende Bewegungsplanung werden definierte Startbedingungen,
Maschinenoffsets, Eingriff und Werkzeuggeometrie benoetigt.

## Technische Referenzen

- [LinuxCNC G-Codes: G7, G18, G76 und G91.1](https://linuxcnc.org/docs/stable/html/gcode/g-code.html):
  relative Bogenmittelpunkte ausdruecklich im Programmkopf; G76-Grenzen
  fuer R und Taperlaenge als Grundlage der Eingabepruefung.
- [LinuxCNC rs274 CLI](https://linuxcnc.org/docs/stable/html/code/rs274.html):
  Batchlauf, Fehlerbehandlung und separate Werkzeug-/Parameterdateien.
