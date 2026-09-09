# LES-005: Innen-Schlichtrueckzug, 2026-09-09

## Aenderung

Der explizite Innen-Schlichtweg fuhr nach dem letzten Konturpunkt zuerst
axial nach ZRI, noch auf Schnittdurchmesser. Jetzt faehrt er zuerst auf
XRI und danach axial auf ZRI. Beide programmierten Strecken werden gegen
die konfigurierte Futter-Sperrzone geprueft.

Ohne Radiuskorrektur ist die erste Bewegung ein rein radialer G0. Bei
aktiver Korrektur wird G40 ausgegeben und die Freifahrt nach XRI mit G1
und dem Bearbeitungsvorschub ausgefuehrt. Die radiale programmierte
Weglaenge muss groesser als der Schneidendurchmesser sein; in G7 ist sie
(End-X minus XRI) / 2. Geprueft werden die gerundeten Ausgabekoordinaten.
Ein unzureichender Abwahlweg blockiert die Erzeugung, statt XRI zu verletzen
oder auf einen axialen Abwahlweg auszuweichen.

Die Vorgabe fuer die erste Bewegung nach G40 folgt der
[LinuxCNC-Dokumentation](https://linuxcnc.org/docs/stable/html/gcode/g-code.html#gcode:g40).

## Nachweise

- Fuenf neue Faelle reproduzierten vor der Korrektur die falsche
  Rueckzugsreihenfolge bzw. die fehlende Abwahlwegpruefung.
- Tests fuer beide Konturrichtungen mit und ohne Radiuskorrektur sowie
  Grenzfaelle unterhalb, auf und oberhalb der geforderten Weglaenge,
  einschliesslich Ausgaberundung.
- Ein bestehender Einfahrtest verwendet jetzt XRI=8 statt 9: Bei seinem
  Enddurchmesser 10 und Schneidenradius 0.4 ist erst damit ausreichend
  radialer Weg fuer die Abwahl vorhanden. Der neue Negativtest deckt
  unzureichenden Freiraum separat ab.
- **524 Stub-Tests und 44 Real-Qt-Tests bestanden, keine Skips.**
- Elf Referenzen regeneriert (1487 Zeilen), 88 statische Checks bestanden.
- **Elf Referenzen und 30 Matrixprogramme bestehen den echten rs274-Lauf.**
  Die Matrix enthaelt zusaetzlich vier Faelle fuer Innenzylinder/Innenkonus
  mit Radius 0.4 und Orientierung L3 in beiden Konturrichtungen.
- Geaenderte Referenzen dieses Schritts: `Innen_Stufe.ngc` und
  `Innen_Radius.ngc`, jeweils radialer Rueckzug vor dem bisherigen Z-Move.

Die kanonische Ausgabe von `inside_cone_reverse_finish_comp` zeigt nach
G40 eine Vorschubbewegung auf physisch X4.5/Z-30 (G7: X9), danach den
axialen Eilgang bei unveraendertem X4.5 auf Z2. Der bisherige axiale
Eilgang auf Schnittdurchmesser ist damit entfernt.

[Interpreterausgaben und aktuelle Hash-Manifeste](linuxcnc_2026-09-09/README.md).

## Verbleibende Grenzen

Durch die G40-Abwahl hat die tatsaechliche lineare Freifahrt auch einen
Z-Anteil aus dem wegfallenden Werkzeugkorrekturversatz. Die Pruefung der
programmierten Strecken ist keine vollstaendige Pruefung des korrigierten
Werkzeugweges oder der Werkzeughuelle.

LES-005 bleibt fuer vollstaendige Einfahrt, alle Werkzeugorientierungen,
kompensierte Innenstufen/-radien/-freistiche, grafischen Backplot und
Trockenlauf offen. Die vollstaendige CSS-Rueckzugs-/Werkzeugwechselsequenz
(LES-013) wurde in diesem Schritt nicht veraendert. Der gemeinsame
Programmabschluss gibt teilweise weiterhin Nullbewegungen auf bereits
erreichte Rueckzugskoordinaten aus (LES-031).
