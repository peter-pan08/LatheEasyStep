# Roadmap LatheEasyStep

Stand: 2026-09-16

LatheEasyStep soll ein werkstattnahes, konversationelles Drehpanel fuer
LinuxCNC werden. Die Roadmap beschreibt Release-Ziele und Abhaengigkeiten.
Die vollstaendige Aufgabenliste steht in der [TODO.md](TODO.md), reale
Verifikation in
[doc/REALTEST_FRAGEN_2026-07-15.md](doc/REALTEST_FRAGEN_2026-07-15.md).

## Ausgangsstand

- `main`: Version 0.8.0 als lauffaehige Basis (freigegeben 2026-09-16)
- `dev`: aktueller Entwicklungsstand fuer die naechste Version; `main`
  bleibt die stabile Basis
- aktueller Teststand: `877 passed (Stub-Qt), 108 passed (Real-Qt), 0 skipped`
- UI-Shell, acht Reiter, Step-Verwaltung und Vorschau sind bereits in Teil-UIs
  und Fachmodule getrennt
- Deutsch, Englisch und Spanisch besitzen jeweils 1.022 identische,
  nichtleere Sprachschluessel
- G53-Werkzeugwechsel, erster Werkzeugwechsel, Tooltips, Sprachumschaltung,
  Slice-/Frontview, Bohren-Anfahrt, G76-Plausibilitaet und `rough_finish`
  wurden praktisch bestaetigt oder umgesetzt

Der Umfang auf `dev` ist als Entwicklung zu Version 0.8.0 einzuordnen, nicht
als kleine Patchversion 0.7.1.

## 0.8.0 - Generator- und Sicherheitsrelease

Ziel: Die angebotenen Konturfaelle sind innen und aussen nachvollziehbar
nutzbar und verwenden in Vorschau und G-Code dieselbe Geometrie.

Verbindliche Aufgaben:

- LES-001/039 sichere Anfahrten, Freifahrten und Werkzeugwechsel
- LES-003/005 belastbare Innen-Schrupp- und Schlichtfahrwege
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
- Referenzprogramme bestehen die dokumentierten SIM-/Backplot-Nachweise

### Release-Gate-Status: freigegeben

`v0.8.0` wurde am 2026-09-16 freigegeben (Merge `dev` -> `main`, Tag
`v0.8.0`). Alle Abnahmekriterien oben waren zu diesem Zeitpunkt erfuellt
und gegengeprueft:

- zylindrische Innenkontur/-stufe/-konus/-radius: `ngc/Innen_Stufe.ngc`,
  `ngc/Innen_Konus.ngc`, `ngc/Innen_Radius.ngc` sowie die Matrixfaelle
  `inside_cylinder_*`; Innenfreistich: Matrixfaelle
  `thread_relief_inside_left/right.ngc`.
- Vorschau/Subroutine/Schlichtweg: gemeinsame Primitive ueber
  `preview_scene.py`/`gcode_*.py`, durch die bestehende Testsuite gedeckt.
- lokale Freistiche mitten in einer Kontur: `ngc/Freistich_Mitte.ngc`.
- keine ungenutzte Generator-Kopie: ein einziger Einstiegspunkt
  (`generate_program_gcode()`, `gcode_program.py`) und je eine
  `rough_turn_parallel_x/z()`-Implementierung (`gcode_roughing.py`).
- G96/G97/CSS-Positionierung: `ngc/CSS_Wechsel.ngc`,
  `tests/test_css_and_drill_validation.py`,
  `tests/test_css_clearance.py`.
- Planen-Kantenform "Radius": LES-036, `ngc/Planen_Radius.ngc`,
  272,6 s AUTO-Lauf bis `M30`, Backplot.
- Parserannahme: zwoelf Referenzen und 43 Matrixfaelle bestehen `rs274`
  ohne Fehler.
- SIM-/Backplot-Nachweise: Planen-Radius (272,6 s bis `M30`), DIN-76-
  Aussen-/Innenfall (103 s/122 s bis Programmende) und die Innenbearbeitungs-
  Richtungsvarianten (187,1 s/186,2 s bis `M30`, identische Endposition,
  deckungsgleicher Backplot, je leerer NML-Fehlerkanal) besitzen
  dokumentierte QtDragon-SIM-Nachweise. Die allgemeine Testbasis (877
  Stub-/108 Real-Qt-Tests) ist erfolgreich; alle zwoelf Referenzen liefen
  in QtDragon-SIM bis `M30`.

Der reale Maschinenlauf mit tatsaechlich geschnittenem Gewinde ist kein
0.8.0-Kriterium. Er bleibt zusammen mit den weiteren realen Maschinen-
Trockenlaeufen dem 1.0.0-Gate vorbehalten.

Eine 0.8.1 oder 0.8.2 wird vorab nicht verplant. Patchversionen bleiben
spaeter tatsaechlichen Fehlerkorrekturen des 0.8.0-Releases vorbehalten.

## 0.9.0 - Panel-, Zustands- und Datenarchitektur

Ziel: Die in 0.8.0 verifizierte Generatorbasis wird in eine dauerhaft
wartbare Panelarchitektur eingebettet. Aenderungen an Darstellung und
Bedienung duerfen Bearbeitungsdaten und G-Code nicht beeinflussen.

Verbindliche Aufgaben:

- LES-022 zentraler Bewegungs- und Modalzustand
- LES-044 vollstaendige Trennung von Vorschaugeometrie und Qt-Darstellung
- LES-051 Panel-Grundgeruest und Darstellungsadapter
- LES-052 Zustandsmodell, Controller und Wiederherstellung
- LES-053 Programm-/Step-Dateiformat versionieren
- LES-054 deterministische Programmerzeugung
- LES-032 normalisierte Werkzeuggeometrie und Tooltable-Auswertung

Abnahmekriterien:

- Generator bleibt vollstaendig Qt-unabhaengig
- UI-Fragmente besitzen keinen fachlichen Zustand
- `ProgramState`, `OperationState`, `ToolTableState`, `ViewState`,
  `DirtyState` und `RuntimeState` besitzen definierte Eigentuemer
- Embedded und Standalone verwenden denselben Ladevertrag
- optische Ressourcen-Aenderungen veraendern weder Programmdaten noch G-Code
- Bewegungs- und Modalzustaende werden zentral gefuehrt
- Save/Load stellt fachlichen Zustand reproduzierbar wieder her
- unterstuetzte Dateiformate werden zentral migriert; unbekannte neuere
  Versionen werden sauber abgelehnt
- gleiche normalisierte Programmdaten erzeugen unabhaengig von UI, Sprache,
  Theme und Ladeweg identischen G-Code

Die bereits erledigte Trennung der Bearbeitungsreiter wird nicht erneut
geplant. LES-055 beschreibt eine sicherheitsrelevante Erweiterung fuer die
Maschinenprofil-Kompatibilitaet und ist fuer 1.0.0 verpflichtend.

## 1.0.0 - Werkstattgeeigneter dokumentierter Stand

Version 1.0 bedeutet nicht, dass jede denkbare Drehoperation vorhanden ist.
Sie bedeutet, dass der dokumentierte Funktionsumfang reproduzierbar und
fachlich verifiziert ist.

Voraussetzungen:

- keine offenen P0- oder P1-Aufgaben
- jede angebotene Bearbeitungsart besitzt mindestens ein Referenzprogramm
- Innen- und Aussenvarianten sind getrennt getestet
- Save/Load-Roundtrips fuer aktuelle und unterstuetzte aeltere Dateien
- versioniertes Dateiformat mit getesteten Migrationen; unbekannte neuere
  Versionen werden nicht stillschweigend geladen
- deterministische G-Code-Erzeugung aus normalisierten Programmdaten
- Maschinenprofil-Identitaet und erkennbare Kompatibilitaetspruefung
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
