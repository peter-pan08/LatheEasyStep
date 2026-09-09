# Roadmap LatheEasyStep

Stand: 2026-09-09

LatheEasyStep soll ein werkstattnahes, konversationelles Drehpanel fuer
LinuxCNC werden. Die Roadmap beschreibt Release-Ziele und Abhaengigkeiten.
Die vollstaendige Aufgabenliste steht in der [TODO.md](TODO.md), reale
Verifikation in
[doc/REALTEST_FRAGEN_2026-07-15.md](doc/REALTEST_FRAGEN_2026-07-15.md).

## Ausgangsstand

- `main`: Version 0.7.0 als lauffaehige Basis
- `dev`: aktueller Entwicklungsstand fuer 0.8.0; `main` bleibt die stabile Basis
- aktueller Teststand: `589 passed (Stub-Qt), 44 passed (Real-Qt), 0 skipped`
- UI-Shell und acht Reiter sind bereits in Teil-UIs getrennt
- Deutsch, Englisch und Spanisch besitzen jeweils 1.022 identische,
  nichtleere Sprachschluessel
- G53-Werkzeugwechsel, erster Werkzeugwechsel, Tooltips, Sprachumschaltung,
  Slice-/Frontview, Bohren-Anfahrt, G76-Plausibilitaet und `rough_finish`
  wurden praktisch bestaetigt oder umgesetzt

Der Umfang auf `dev` ist als Entwicklung zu Version 0.8.0 einzuordnen, nicht
als kleine Patchversion 0.7.1.

## 0.8.0-alpha - Sicherheits- und Realtest-Gate

Ziel: Keine bekannte Operation darf unsichere, leere oder widerspruechlich
gewarnte Fahrwege erzeugen.

Verbindliche Aufgaben:

- LES-001 sichere Anfahrt zwischen Operationen
- LES-039 sichere erste Freifahrt und Werkzeugwechsel
- LES-040 vollstaendige Zahlen- und Wertebereichspruefung
- LES-003 Innen-Schruppen Parallel-Z abschliessend verifizieren
- LES-005 Innen-Schlichtanfahrt und Rueckzug absichern

Abnahmekriterien:

- kein offener P0-Punkt
- kein diagonaler Eilgang allein aufgrund von `_is_at_safe`
- kein erfolgreicher Roughing-Step ohne reale Schnittbewegung
- Innen-Schruppen besitzt einen bestaetigten Referenz-, Backplot- und
  Trockenlauffall fuer monoton steigende und fallende Z-Konturen
- mindestens ein G7-Bogen mit `I != 0` wird sowohl im direkten Schlichtweg
  als auch in der G71/G72-Subroutine vom LinuxCNC-Parser akzeptiert
- Warnung und ausgegebener Fahrweg widersprechen sich nicht
- komplette Testsuite, Referenzprogramme und LinuxCNC-Parser laufen erfolgreich

## 0.8.0 - Belastbare Kontur- und Innenbearbeitung

Ziel: Die angebotenen Konturfaelle sind innen und aussen nachvollziehbar
nutzbar und verwenden in Vorschau und G-Code dieselbe Geometrie.

Verbindliche Aufgaben:

- LES-006 Rueckzugsstrategie je Bearbeitungsart
- LES-010 lokale DIN-Freistichgeometrie
- LES-012 G1/G2/G3-Primitive durchgaengig erhalten
- LES-013 sichere CSS-Umschaltung nach per-Operation-G96/G97
- LES-015 automatisierte Innenkontur-Testmatrix
- LES-019 fehlende DIN-76-Presets
- LES-030 LinuxCNC-Simulationsmatrix
- LES-036 Kantenform "Radius" beim Planen

Abnahmekriterien:

- zylindrische Innenkontur, Innenstufe, Innenkonus, Innenradius und
  Innenfreistich besitzen Referenzfaelle
- Vorschau, Subroutine und Schlichtweg verwenden dieselben Primitive
- lokale Freistiche funktionieren auch mitten in einer laengeren Kontur
- keine produktiv ungenutzte Generator-Kopie wird von Tests als Referenz benutzt
- G96/G97-Wechsel zwischen Operationen verwechseln weder Vc noch Drehzahl;
  CSS wird erst an der fachlich festgelegten Position aktiviert
- die im UI angebotene Planen-Kantenform "Radius" besitzt Generator-,
  Preview-, Save/Load- und LinuxCNC-Referenztests
- alle angebotenen 0.8.0-Faelle werden von LinuxCNC ohne Parserfehler angenommen

## 0.9.0 - Bedienung und technische Konsolidierung

Ziel: Die funktionale Basis wird leichter wartbar, besser testbar und im
Werkstattalltag eindeutiger.

Aufgabenbereiche:

- LES-018 optionale G70-Wiederverwendung
- LES-020 weitere Handler-Extraktionen
- LES-022 zentraler Bewegungs- und Modalzustand
- LES-024 Vorschau-/Step-UI und Controllergrenzen
- LES-027 Embedded-/Standalone-Performance
- LES-028 normalisierte Werkzeug- und G76-Daten
- LES-031 redundante Bewegungen und Modals
- LES-032 Werkzeuggeometrie und Tooltable-Plausibilitaet
- LES-033 reale Gewindevorschau
- LES-034 fachlich getrennte Preview-Pipeline
- LES-035 Embedded-/Standalone-Paritaet

Die bereits erledigte Trennung der acht Bearbeitungsreiter wird nicht erneut
geplant. Offen bleiben Vorschau, Step-Verwaltung und saubere Schnittstellen
zwischen den Modulen.

## 1.0.0 - Werkstattgeeigneter dokumentierter Stand

Version 1.0 bedeutet nicht, dass jede denkbare Drehoperation vorhanden ist.
Sie bedeutet, dass der dokumentierte Funktionsumfang reproduzierbar und
fachlich verifiziert ist.

Voraussetzungen:

- keine offenen P0- oder P1-Aufgaben
- jede angebotene Bearbeitungsart besitzt mindestens ein Referenzprogramm
- Innen- und Aussenvarianten sind getrennt getestet
- Save/Load-Roundtrips fuer aktuelle und unterstuetzte aeltere Dateien
- LinuxCNC-Parsing und Backplot aller Referenzprogramme
- dokumentierte Trockenlaeufe an der realen Maschine
- konsistente Vorschau- und G-Code-Geometrie
- definierte Maschinenprofile, Rueckzugsebenen und Futter-Sperrzonen
- verstaendliche Fehlermeldungen statt fragwuerdiger G-Code-Ausgabe
- reproduzierbarer Teststand; jeder Skip ist begruendet und kein
  sicherheitsrelevanter Generatorfall wird im regulaeren Lauf uebersprungen
- Release-Tag, Changelog und Bedienhinweise

## Nach 1.0

- weitergehende Keilnut- und Verzahnungsfunktionen
- weitere Maschinen-, Futter- und Werkzeugprofile
- automatisierte LinuxCNC-Simulationslaeufe
- zusaetzliche Abspanstrategien

Entwicklungsstand 2026-09-08: Snapshot-Generierung, atomare Programmdateien,
getrennte Qt-Testlaeufe, normierte Step-Kommentare und Freistich-Koordinaten-
regressionen sind umgesetzt. Planradius, Innenaufmass, Eingabevalidierung
und gemeinsame Anfahrt wurden erweitert. Die neuen Fahrwege sind noch
nicht mit LinuxCNC-Parser, Backplot und Maschine abgenommen; offene P0-
Punkte bleiben Releaseblocker. [Details und Grenzen](doc/VERIFICATION_2026-09-08.md).

Fortsetzung 2026-09-09: CSS-Zwischenstand abgesichert, Bohr- und zentrale
Zahlenvalidierung erweitert, Innenradiusmatrix und zwei Referenzen ergaenzt.
LES-013/040/028/003/012/015 bleiben mit den dokumentierten Restarbeiten offen.
[Pruefstand und Grenzen](doc/VERIFICATION_2026-09-09.md).

WSL-Fortsetzung 2026-09-09: LinuxCNC-Interpreterpruefung erfolgreich fuer
elf Referenzen und 30 Matrixprogramme. Nichtmonotone Boegen vor G71/G72
abweisen; primitive Konturboegen auch beim expliziten Schlichten erhalten.
[Interpreterbericht und Nachweise](doc/linuxcnc_2026-09-09/README.md).

LES-005 Teilabschluss: Innen-Schlichtrueckzug radial vor axial, G40-Abwahl
mit geprueftem Freiraum. 524 Stub-/44 Qt-Tests und 11 Referenzen/30 Matrixfaelle
im Interpreter bestanden. [Details und Grenzen](doc/LES005_INNEN_RUECKZUG_2026-09-09.md).

Review nach Unterbrechung 2026-09-09: Zwischenzeitliche Erweiterungen
beibehalten; explizite Schlichtpraeferenz und CSS-/G76-Ausgaberundung
korrigiert. Aktuell 563 Stub-/44 Qt-Tests und elf Referenzen/37 Matrixfaelle
im Interpreter bestanden. LES-013 bleibt fuer Durchmesserbewertung,
zyklusinterne Bewegungen und reale Abnahmen offen; fruehere pauschale
Abschlussaussagen sind damit ersetzt.
[Details und Nachweise](doc/linuxcnc_2026-09-09/README.md).

Fortsetzung LES-037/001/006: vier Gewindefreistichfaelle (innen/aussen,
rechts/links) und zwei Schruppen-/Schlichten-Folgen mit identischem Werkzeug
unter rs274 bestanden. Zu wenig Konturstrecke blockiert in allen vier
Freistichvarianten den Export; Konturverlaengerung verschiebt den Freistich
nicht. Aktuell 573 Stub-/44 Qt-Tests, elf Referenzen und 43 Matrixfaelle.
WSLg/AXIS sind erreichbar; grafischer Backplot und reale Abnahme bleiben offen.
[Pruefbericht](doc/linuxcnc_2026-09-09/README.md).


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

LES-027 Teilstand 2026-09-09: isolierter Qt-Startbenchmark mit frischen
Prozessen vorhanden. UI-Ausschnitt im Median 0.368 s unter Windows und
1.362 s unter WSL, keine Reproduktion der gemeldeten >20 s. Neun
nachgelagerte Panel-Startaufgaben erhalten eigene Zeitmarken. Reale
Ursache, Bedienbereitschaft und Embedded-/Standalone-Vergleich bleiben offen.
[Messumfang, Rohdaten und naechster Nachweis](doc/STARTUP_2026-09-09.md).


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
