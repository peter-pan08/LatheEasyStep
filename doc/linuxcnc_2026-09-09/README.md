# LinuxCNC-Interpreterpruefung 2026-09-09

WSL2, Distribution Debian, `/usr/bin/rs274`, Paket `linuxcnc-uspace`
`2:2.10.0~pre1+git20260908.0211.64efb28cd77a-1`.

**Ergebnis: 11 Referenzen und 43 Matrixprogramme bis PROGRAM_END erfolgreich.**
Jede `.txt`-Datei enthaelt die echte kanonische Interpreterausgabe.
`references/manifest.json` und `matrix/manifest.json` enthalten SHA256-Hashes
der geprueften Programme und den Abschlussstatus. Keine HAL-Verbindung;
eigene temporaere Parameterdateien und synthetische Werkzeugtabelle.

## Gefundener und behobener Fehler

Der erste Lauf scheiterte bei `Kontur_Radius_Fase.ngc` mit
`G7X error: Not monotonic`. Die alte Bogenprimitive lief von X32/Z-8 nach
X26/Z-16 um das Zentrum X26/Z-11.4375 mit G2. Die Endpunkte sind monoton,
der lange Bogen dazwischen ist es nicht. Eine reine Endpunktpruefung hat
den unzulaessigen G71-Zyklus trotzdem freigegeben.

Die Zykluspruefung beruecksichtigt jetzt analytische Bogenextrema in der
jeweiligen Zyklusachse. Eine nichtmonotone Bogenkontur wird vor der
G71/G72-Ausgabe abgewiesen. Ein Rueckfall auf gerade Endpunktverbindungen
waere kein geometrisch korrekter Ersatz. Die urspruengliche Fehlerkontur
bleibt in `tests/test_cycle_arc_monotonicity.py` fuer beide Strategien erhalten.

Das positive Referenzbeispiel verwendet jetzt einen monotonen Viertelkreis:
X32/Z-8 nach X26/Z-11 um X26/Z-8, G3 mit I=-3 und K=0 (Radius 3 mm).
Das ist eine bewusste Aenderung der Beispielgeometrie, keine automatische
Aenderung von Nutzerkonturen. Ausserdem bleibt die Bogenprimitive jetzt
auch beim expliziten Schlichten primitiver Konturen erhalten; vorher wurde
sie dort als Gerade ausgegeben. LinuxCNC fuehrt den Bogen in der
Zyklusbearbeitung und beim expliziten Schlichten als ARC_FEED aus.

## Matrix und Grenzen

- Innenzylinder, Innenstufe, Innenkonus, Innenradius: jeweils beide
  Konturrichtungen und rough/finish/rough_finish, insgesamt 24 Faelle.
- Zusaetzlich vier Innenzylinder/-konus-Faelle mit Radiuskorrektur 0.4/L3,
  jeweils beide Konturrichtungen und reines Schlichten.
- Aussenbogen: parallel_x (G72) und parallel_z (G71), zwei Faelle.
- CSS-Referenz: kanonische Ausgabe bestaetigt Festdrehzahlen 955/900/1432,
  CSS-Schnittgeschwindigkeiten 120/180 und Begrenzung 2500.
- Windows-Regressionen: **573 Stub-Tests, 44 echte Qt-Tests, keine Skips**.
- Elf NGC-Referenzen: **88 statische Checks, keine Probleme**.

Parsererfolg ist keine Kollisions-, Materialabtrags- oder Maschinenfreigabe.
Ein grafischer LinuxCNC-Backplot mit realer Konfiguration und ein Trockenlauf
wurden nicht ausgefuehrt. Erste Freifahrt und vollstaendige Werkzeughuellen und die vollstaendige CSS-Rueckzugs-/Wechselsequenz bleiben
offen. Ausgeschriebene Schrupppfade verwenden teilweise weiterhin Sehnen;
die neue Pruefung ersetzt keine allgemeine Bogen-Schnittplanung (LES-012).

## Wiederholen

Im Windows-Projektverzeichnis:

```text
.venv/Scripts/python -X utf8 regenerate_all_ngc.py
.venv/Scripts/python regenerate_linuxcnc_matrix.py
```

In WSL im Projektverzeichnis `/mnt/c/Users/matth/Downloads/git/LatheEasyStep`:

```text
python3 check_linuxcnc.py --report-dir doc/linuxcnc_2026-09-09/references
python3 check_linuxcnc.py --input-dir tests/_local/linuxcnc_matrix --report-dir doc/linuxcnc_2026-09-09/matrix
```

Die Matrixeingaben sind reproduzierbar und liegen im ignorierten Testordner.
Die Referenzdateien unter `ngc/` und die Interpreterberichte werden versioniert.

Technische Grundlage: [LinuxCNC interp_g7x.cc, Monotoniepruefung](https://github.com/LinuxCNC/linuxcnc/blob/64efb28cd77a/src/emc/rs274ngc/interp_g7x.cc).

Nachtrag LES-005: Der axiale Rueckzug auf Schnittdurchmesser ist korrigiert.
Berichte und Manifeste wurden mit dem neuen Stand erneuert.
[Umfang und Grenzen](../LES005_INNEN_RUECKZUG_2026-09-09.md).

## Review nach Unterbrechung, 2026-09-09

Der vorgefundene Zwischenstand bestand 559 Stub- und 44 Qt-Tests.
Drehzahlvalidierung, Sicherheitspositionsverfolgung, zusaetzliche
Streckenpruefungen, CSS-Freifahrt und G70-Wiederverwendung wurden beibehalten.
Das ist keine vollstaendige Sicherheitsfreigabe aller dieser Aenderungen.

Vier neue Regressionen scheiterten zunaechst und bestehen nach Korrektur:
- G70-Wiederverwendung respektiert jetzt `prefer_explicit`.
- G76 Q darf auch nach Rundung auf vier Nachkommastellen nicht 90 erreichen.
- CSS-Schnittgeschwindigkeit darf in der Ausgabe nicht auf S0.0 runden.
- Der CSS-Startdurchmesser darf in der Ausgabe nicht auf X0.000 runden.

Aktuell: 573 Stub-Tests, 44 echte Qt-Tests, keine Skips; elf Referenzen
und 43 Matrixprogramme bis PROGRAM_END bestanden, 88 statische Checks.
Die Matrix enthaelt jetzt fuenf CSS-Freifahrtfaelle sowie zwei separate
Schlichtprogramme mit auto/G70 bzw. prefer_explicit. Berichte und Hashes
wurden erneuert. Die Referenzen enthalten insgesamt 1483 Zeilen.

Die pauschale LES-013-Abschlussaussage wurde korrigiert: Die feste
Anfahrdrehzahl beim ausgeschriebenen Schruppen wird einmal aus stock_x
berechnet, waehrend G96 an wechselnden Passdurchmessern aktiviert wird.
Das ist eine begrenzte Festdrehzahlstrategie, kein Nachweis identischer
Durchmesser. Ausserdem laufen interne Rueckzuege von Zyklen und Makros
weiterhin in deren aktivem Spindelmodus; die G97-Pruefung betrifft explizite
Freifahrten. Grafischer Backplot und reale Maschinenabnahme bleiben offen.

## Gewindefreistiche und Operationsfolgen, 2026-09-09

Vier neue Programme pruefen automatische M12-Freistiche: innen/aussen,
rechts/links. Jeder Fall enthaelt einen expliziten Kontur-Schlichtschritt
und anschliessend G76. Alle laufen mit echtem rs274 bis PROGRAM_END.
Zwei weitere Programme pruefen ausgeschriebenes Schruppen und separates
Schlichten mit identischer Werkzeugnummer, innen bzw. aussen, mit CSS.
Es erfolgt genau ein Werkzeugwechsel; der Schlichtschritt faehrt mit
Festdrehzahl an und aktiviert anschliessend seine eigene Schnittgeschwindigkeit.

Zehn neue Regressionen bestaetigen Gewindeendkoordinaten, erhaltene
Freistichboegen, unveraenderte Eingabedaten, lagefeste Freistiche bei
Konturverlaengerung und Dateierhalt bei zu wenig Konturstrecke. Die vier
Negativfaelle brechen mit einem Freistichfehler ab, bevor eine vorhandene
G-Code-Datei ersetzt wird. Es war fuer diese Faelle kein Generatorfix noetig.

Aktuell: 573 Stub-Tests, 44 echte Qt-Tests, keine Skips; 88 statische Checks.
Die Interpreter-Matrix umfasst jetzt 43 erfolgreiche Faelle, zusaetzlich
zu den elf Referenzen. Eingaben aus `lathe_easystep/verification_cases.py`
werden von Regressionen und Matrixgenerator gemeinsam verwendet.

WSLg ist verfuegbar (DISPLAY=:0, Wayland, AXIS installiert); ein verborgenes
Tk-Testfenster konnte den Bildschirm mit 1920x1080 ansprechen. Dies ist
nur ein GUI-Verfuegbarkeitsnachweis, kein ausgefuehrter LinuxCNC-Backplot.

LES-037 bleibt fuer Backplot mit realen Werkzeugdaten und Trockenlauf
offen. Die Matrix prueft vorhandene M12-Daten, keine Normverifikation oder
alle Groessen. Die Operationsfolgen belegen keine allgemeine Kollisions-
freiheit oder physische Eignung eines konkreten Werkzeugs. LES-001/006
bleiben fuer weitere Folgen, Werkzeughuellen und Maschinenabnahme offen.

## Einstichvalidierung

LES-040/028, Einstichvalidierung 2026-09-09: Vorschuebe, Zustellung,
Werkzeug-/Nutbreite und Ueberdeckung werden mit den tatsaechlich an o220
uebergebenen drei Nachkommastellen geprueft. Start/Ende duerfen nach
Rundung nicht zusammenfallen. Spanbruchanzahl muss ganzzahlig und
nichtnegativ sein. Fuenf zuvor fehlschlagende Regressionen bestanden.
Aktuell 578 Stub-/44 Qt-Tests, keine Skips; elf Referenzen und 43
Matrixfaelle unter rs274 sowie 88 statische Checks bestanden.
Referenzausgabe unveraendert. Dies ist keine vollstaendige Abnahme aller
Einstich-/Abstichvarianten. Keilnut erzeugt derzeit wegen der expliziten
Makro-Sperre in gcode_keyway.py keinen G-Code; eine eigenstaendige
Implementierung und LinuxCNC-Abnahme bleiben offen.

## Werkzeugdatenvalidierung

LES-028/032 Teilstand 2026-09-09: Radiuskorrektur lehnt negative Radien,
nicht darstellbare Schneidendurchmesser sowie explizit ungueltige
Werkzeugorientierungen ab. Q/L wird ganzzahlig in 0..9 validiert, statt
Dezimalwerte abzuschneiden oder bei defekten Angaben still ohne Korrektur
weiterzulaufen. G41.1/G42.1 darf keinen auf null gerundeten D-Wert ausgeben.
Gueltige Zahlenstrings bleiben kompatibel. Fehlende Werkzeugdaten bzw.
fehlendes Q und Radius null behalten das bisherige Verhalten ohne Korrektur;
eine allgemeine Pflicht fuer vollstaendige Werkzeugtabellen ist nicht umgesetzt.
Neun Fehlerfaelle vorher reproduziert, elf neue Regressionen bestanden.
Aktuell 589 Stub-/44 Qt-Tests, 88 statische Checks sowie elf Referenzen und
43 Matrixfaelle unter rs274 bestanden; Referenzausgabe unveraendert.
Werkzeughuellen, Schneidenlaenge, physische Eignung und reale Abnahme bleiben offen.
