# TODO LatheEasyStep

Stand: 2026-09-09

Diese Datei ist die verbindliche Liste aller offenen Aufgaben. Erledigte Punkte
werden entfernt und im `CHANGELOG.md` dokumentiert. Release-Ziele und
Abhaengigkeiten stehen in der [ROADMAP.md](ROADMAP.md), reale Tests in
[doc/REALTEST_FRAGEN_2026-07-15.md](doc/REALTEST_FRAGEN_2026-07-15.md).

## Aktuell verifizierte Basis

- Native Nachpruefung: SIM-Konfiguration korrigiert (siehe LES-005-
  Teilstand "SIM-Konfiguration korrigiert, echter Trockenlauf"), damit
  erstmals echte AUTO-Trockenlaeufe bis `M30` moeglich. Grafischer,
  lesbarer Backplot-Screenshot und realer Trockenlauf liegen jetzt fuer
  `Innen_Radius.ngc`, `Innen_Stufe.ngc` und `Innen_Konus.ngc` vor
  (Naeheres: [nativer Bericht](doc/NATIVE_VERIFICATION_2026-09-09.md)).
  `Abdrehen.ngc`/`Einstich.ngc` liefen nachweislich weiter (kein Haenger),
  aber ohne ausreichendes Zeitbudget bis zum Ende beobachtet.

- `main`: Version 0.7.0 als lauffaehige Basis
- `dev`: aktueller Entwicklungsstand fuer 0.8.0; `main` bleibt die stabile Basis
- Teststand: `639 passed` (Stub-Qt) und `44 passed` (echtes PyQt5),
  getrennte Prozesse ueber `python run_tests.py`, keine Skips.
- Zwoelf Referenzprogramme (inkl. neu `Innen_Konus.ngc`) regeneriert;
  statische NGC-Pruefung und LinuxCNC-Parser (`rs274`, alle zwoelf) sowie
  43 Matrixfaelle bestanden.
- Umfang, Testbefehle und verbleibende Grenzen:
  [Verifikationsbericht 2026-09-09](doc/VERIFICATION_2026-09-09.md).
- UI-Shell und acht Reiter-Teil-UIs sind getrennt und werden ueber
  `lathe_easystep/ui_split.py` geladen
- `de.lng`, `en.lng` und `es.lng` enthalten jeweils 1.022 identische,
  nichtleere und eindeutige Sprachschluessel
- derzeit keine offenen GitHub-Issues; diese Datei ist der Aufgabenbestand
- Real am Panel bestaetigt (Nutzertest 2026-08-22): DIN-Freistich mitten in
  der Kontur (Vorschau UND generierter G-Code) sowie Innen-Schruppen
  erzeugen jetzt beide sinnvolle, tatsaechlich abtragende Ergebnisse -
  siehe LES-003/LES-010/LES-011

Aufwand:

- `S`: wenige Stunden bis etwa ein Tag
- `M`: ein bis drei Entwicklungstage
- `L`: mehrere Tage mit Tests und Simulation
- `XL`: groessere Architekturarbeit in mehreren Etappen

Prioritaeten:

- `P0`: Sicherheit, falsche Fahrwege oder ungueltige Programmausgabe
- `P1`: fachliche Vollstaendigkeit und hoher praktischer Nutzen
- `P2`: Bedienkomfort, Wartbarkeit und langfristige Architektur

## Priorisierter Arbeitsindex

| ID | Prio | Aufgabe | Nutzen | Aufwand | Ziel |
|---|---|---|---|---|---|
| LES-001 | P0 | Sichere Anfahrt zwischen aufeinanderfolgenden Operationen | sehr hoch | M | 0.8.0-alpha |
| LES-039 | P0 | Werkzeugwechselposition und sichere erste Freifahrt verbindlich pruefen | sehr hoch | M-L | 0.8.0-alpha |
| LES-040 | P0 | Nicht endliche Zahlen vor Geometrie und Ausgabe ablehnen | hoch | M | 0.8.0-alpha |
| LES-003 | P0 | Innen-Schruppen Parallel-Z abschliessend verifizieren | sehr hoch | L | 0.8.0-alpha |
| LES-045 | P0 | G71/G72: D/I-Parameter vertauscht, Zustelltiefe und Aufmass falsch | sehr hoch | M | 0.8.0-alpha |
| LES-005 | P0 | Innen-Schlichtanfahrt und Rueckzug fuer weitere Konturformen absichern | sehr hoch | M-L | 0.8.0-alpha |
| LES-006 | P1 | Rueckzugsstrategie und Achsreihenfolge je Bearbeitungsart festlegen | hoch | M | 0.8.0 |
| LES-010 | P1 | Lokale DIN-Freistichgeometrie am markierten Segment erzeugen | hoch | L | 0.8.0 |
| LES-012 | P1 | Konturprimitive bis zur finalen G1/G2/G3-Ausgabe erhalten | hoch | L | 0.8.0 |
| LES-013 | P1 | Sichere CSS-Umschaltung nach per-Operation-G96/G97 | mittel-hoch | S-M | 0.8.0 |
| LES-015 | P1 | Innenkontur-Testmatrix automatisieren und in LinuxCNC verifizieren | hoch | M-L | 0.8.0 |
| LES-019 | P1 | Verifizierte DIN-76-Presets fuer M2, M2.5 und M3.5 ergaenzen | mittel | S-M | 0.8.0 |
| LES-030 | P1 | Neue Generatorfunktionen systematisch in LinuxCNC simulieren | hoch | M-L | 0.8.0 |
| LES-037 | P0 | Freistich/Relief am Gewindeende verankern, nicht am Konturende; bei zu wenig Platz klar fehlern | sehr hoch | M | 0.8.0-alpha |
| LES-018 | P2 | G70-Wiederverwendung fuer separaten Schlichtstep pruefen | mittel | M-L | 0.9.0 |
| LES-020 | P2 | Handler in kleinen Paketen weiter verkleinern | mittel | M je Paket | 0.9.0 |
| LES-022 | P2 | Zentralen Bewegungs- und Modalzustand einfuehren | langfristig hoch | XL | 0.9.0 |
| LES-024 | P2 | Restliche UI-Modularisierung und Controllergrenzen abschliessen | mittel | L | 0.9.0 |
| LES-027 | P2 | Start- und Reaktionszeit im Embedded-Betrieb messen | mittel | S | 0.9.0 |
| LES-028 | P2 | Werkzeug- und G76-Parameter vor Ausgabe zentral normalisieren | mittel-hoch | M | 0.9.0 |
| LES-031 | P2 | Redundante Bewegungen und Modalbefehle systematisch bereinigen | mittel | M-L | 0.9.0 |
| LES-032 | P2 | Werkzeuggeometrie und Tooltable-Plausibilitaet vertiefen | hoch | L | 0.9.0 |
| LES-033 | P2 | Gewindevorschau aus realen Gewindeparametern ableiten | mittel | M-L | 0.9.0 |
| LES-034 | P2 | Preview-Pipeline fachlich in Werkstueck, Werkzeugweg und Hilfsgeometrie trennen | mittel | L | 0.9.0 |
| LES-035 | P2 | Embedded- und Standalone-Verhalten weiter angleichen | mittel | M | 0.9.0 |
| LES-036 | P1 | Kantenform "Radius" beim Planen umsetzen | mittel | M | 0.8.0 |
| LES-042 | P2 | Legacy-Operationstypen TURN/BORE bereinigen oder korrigieren | gering | S | 0.9.0 |
| LES-043 | P0 | Gegenspindel-Checkbox taeuscht nicht vorhandene Generatorunterstuetzung vor | sehr hoch | XL | 0.8.0-alpha |
| LES-044 | P2 | Modulare Panel-Architektur: Geruest, Text, Darstellung und Generator strikt trennen | langfristig hoch | XL | 0.9.0 |

## P0 - Sicherheits- und Generatorblocker

### LES-001 Sichere Anfahrt zwischen Operationen

Ausgangsbefund (in der gemeinsamen Anfahrt inzwischen behoben):
`emit_approach()` gab bei gesetztem `_is_at_safe` einen
direkten diagonalen Zielmove aus. Der Status sagt nur, dass die vorherige
Operation an einer sicheren Position endete; er beweist nicht, dass der neue
Zielpunkt von dort direkt kollisionsfrei erreichbar ist.

- [x] direkten Zielmove nicht allein aus dem Boolean `_is_at_safe` ableiten
- [ ] sichere Achsreihenfolge anhand Start-, Ziel-, Rohteil- und Futterzone waehlen
- [x] gleiches Werkzeug ohne dazwischenliegenden Werkzeugwechsel testen
- [x] Aussen-Schruppen -> Schlichten und Innen-Schruppen -> Schlichten testen
- [x] Bohren und Gewinde als Z-vor-X-Sonderfaelle pruefen
- [x] Warnung und tatsaechlicher Fahrweg duerfen sich nicht widersprechen
- [x] Regressionen fuer Rohteil- und Chuck-No-Go-Faelle ergaenzen

Ergaenzung aus Codepruefung 2026-09-08: `gcode_safety.emit_approach()`
erzeugt trotz erkannter Futter-Sperrzone weiterhin einen Eilgang. Lokal auf
Funktionsebene reproduziert: Rohteil XA=50, XI=0, ZA=0, ZI=-50;
relative Rueckzuege XRA=5/ZRA=5; Sperrzone X=0..100, Z<=-40;
Ziel X30/Z-45 ergibt Warnkommentare und danach `G0 X30.000 Z-45.000`.

- [x] Verletzungen der Futter-Sperrzone in `emit_approach` als blockierenden Fehler behandeln;
  ein WARN-Kommentar darf die Bewegung nicht freigeben
- [x] gesamte Eilgangstrecke gegen Rohteil und Futterzone pruefen, auch wenn
  Start und Ziel jeweils ausserhalb liegen; beabsichtigte Schnittbewegungen
  gesondert behandeln
- [x] obigen Fall sowohl direkt als auch ueber Gesamtgenerator und Export
  testen: keine ausfuehrbare Ausgabe, bestehende G-Code-Datei bleibt erhalten

Teilstand 2026-09-08: gemeinsame Anfahrt achsweise; Futterpruefung
auch fuer kreuzende Segmente und Werkzeugwechsel in Werkstueckkoordinaten.
Noch keine vollstaendige Rohteil-/Werkzeughuellenpruefung aller direkten
Moves oder Zyklen; angenommene Safe-Position ersetzt keinen Positionsnachweis.

Teilstand 2026-09-09: reine Diagonal-Eilgaenge (kombiniertes `G0 X.. Z..`
in einer Zeile) werden jetzt zusaetzlich per `validate_stock_segment()`
gegen die Rohteil-Huellkurve geprueft - auch wenn Start- und Zielpunkt
jeweils fuer sich ausserhalb liegen, die Strecke dazwischen aber mitten
durchs Rohteil fuehrt (`emit_safe_retract_for_op`-Diagonale,
`move_to_toolchange_pos`). Bewusst NICHT geprueft: die achsweise
Anfahrt-/Rueckzugsfolge in `emit_approach` (ihr Zielpunkt liegt bei
Folgeoperationen wie dem Schlichten nach dem Schruppen absichtlich
innerhalb der Rohteil-Huellkurve) sowie jede Sicherheitsposition im
Innen-Modus (`_active_retract_mode == "internal"`): die Huellkurve ist ein
reines Aussenmass-Rechteck und kann eine Bohrung nicht abbilden, eine
gueltige interne XRI-Position liegt deshalb oft geometrisch "im Rechteck".
Die eigentliche "sichere Achsreihenfolge je nach Rohteil-/Futterzone"
(erster Punkt oben) bleibt unveraendert offen.

Teilstand 2026-09-09 (Fortsetzung): drei weitere Teststand-Punkte
geschlossen. Direkter Regressionstest belegt die op-spezifische
Rueckzugs-Achsreihenfolge (Einstich/Keilnut: X vor Z; Bohren/Gewinde:
Z vor X, unabhaengig vom Startpunkt). Aussen- UND Innen-Schruppen->
Schlichten mit identischem Werkzeug erzeugen nachweislich nur einen
Werkzeugwechsel; die Anfahrt der zweiten Operation lief in beiden Faellen
fehlerfrei durch (bei Innenarbeit bleibt die sichere Position innerhalb
der bereits gebohrten/hohlen Zone - kein neuer Fehler gefunden). Verbleibt
offen: die eigentliche Achsreihenfolge-Entscheidung (erster Punkt) und der
Abgleich Warnung/tatsaechlicher Fahrweg.

Teilstand 2026-09-09 (WSL-Fortsetzung, echter rs274 verfuegbar): der
zweite Teilschritt jeder Rueckzugsreihenfolge (die Achse, die zuerst auf
ihren sicheren Wert gebracht wurde, bleibt dabei konstant) wird jetzt in
`emit_safe_retract_for_op()` (Einstich/Keilnut, Bohren/Gewinde, sowie der
bisherige X-vor-Z-Fallback bei Start im Rohteil/in der Futterzone) UND in
`emit_approach()` (Aussen-Modus) gegen Futter-Sperrzone und - ausser im
Innen-Modus - Rohteil-Huellkurve geprueft. Der ERSTE Teilschritt (Flucht
aus der aktuellen, ggf. gefaehrlichen Position) bleibt bewusst ungeprueft,
da er dort legitim beginnen darf.

Dabei einen echten, bis dahin unentdeckten Fall gefunden: ein bestehender
Test (`test_turn_in_chuck_nogo_falls_back_to_x_then_z_retract`) konfigurierte
XRA=60 als "sichere" Rueckzugsposition, obwohl diese SELBST noch innerhalb
der konfigurierten Futter-Sperrzone (X20..80) lag - der zweite Rueckzugs-
schritt haette die gesamte restliche Z-Strecke MITTEN DURCH die Sperrzone
gefuehrt, ohne Warnung oder Fehler. Testfixture auf eine tatsaechlich
sichere XRA=90 korrigiert; die bisherige Kernaussage des Tests (X vor Z,
keine Diagonale) bleibt erhalten. Alle 11 Referenzen und 30 Matrixfaelle
unter WSL/Debian mit echtem rs274 bis PROGRAM_END erneut bestanden, keine
Ausgabeaenderung. 542 Stub-/44 Qt-Tests bestanden.

Die eigentliche Achsreihenfolge-Entscheidung (erster Punkt: Reihenfolge
dynamisch aus Start/Ziel/Rohteil/Futterzone ableiten statt fixer Konvention
je Operationstyp) bleibt offen - jetzt wird aber zumindest jede fixe
Konvention, die im Einzelfall nicht wirklich sicher ist, blockiert statt
stillschweigend ausgefuehrt.

Teilstand 2026-09-09 (nach LES-006-Referenzpruefung): "Warnung und
tatsaechlicher Fahrweg duerfen sich nicht widersprechen" geschlossen -
`get_approach_warnings()` meldete "Rueckzugsebene schneidet den
Futterbereich" bisher allein anhand des Z-Grenzwerts, ohne wie
`validate_chuck_segment()` auch das X-Intervall der Sperrzone zu pruefen.
Eine sichere Position mit X ausserhalb der Sperrzone wurde dadurch faelschlich
als gefaehrdet gemeldet, obwohl der tatsaechliche (bereits abgesicherte)
Fahrweg dort nie hinfuehrt - ein Widerspruch zwischen Warnungstext und
echtem Verhalten. Jetzt pruefen beide dieselbe Bedingung. Unter WSL/Debian
mit echtem rs274 verifiziert (11 Referenzen, 30 Matrixfaelle), keine
Ausgabeaenderung. 550 Stub-/44 Qt-Tests bestanden.

Zur eigentlichen Achsreihenfolge-Entscheidung (erster Punkt, weiterhin
offen): eine echte dynamische Auswahl (bei jedem Eilgang neu aus Start/
Ziel/Rohteil/Futterzone ableiten, welche Achse zuerst bewegt wird) wuerde
den drei erklaerten Projektzielen zuwiderlaufen ("deterministische
Bewegungen, nachvollziehbare Geometrie, minimale Ueberraschungen" -
DEV.md). Auch der ausgewertete Inventor-Post (LES-006) macht das nicht -
er nutzt eine feste, global konfigurierte Reihenfolge. Die vorhandene,
jetzt vollstaendig gepruefte Loesung (feste Konvention je Operationstyp,
mit hartem Fehler statt stillem Fehlverhalten, wenn diese Konvention im
Einzelfall nicht sicher waere) ist der bewusst gewaehlte Kompromiss.
Ein echter naechster Schritt waere nicht "klueger waehlen", sondern echte
Werkzeug-Eingriffsverfolgung (LES-022, zentraler Bewegungs-/Modalzustand)
statt der aktuellen Naeherung ueber Rohteil-/Futter-Rechtecke.

### LES-039 Werkzeugwechselposition und erste Freifahrt absichern

Codepruefung 2026-09-08: `gcode_safety.append_tool_and_spindle()` gibt bei
fehlendem XT/ZT nach einer Warnung trotzdem `T01 M6` aus (lokal reproduziert).
`ui_flow.build_gcode_lines()` verlangt XT/ZT erst bei mindestens zwei
unterschiedlichen Werkzeugen. Vor dem ersten Wechsel wird zudem pauschal
Z vor X freigefahren, ohne Ausgangsposition und aktuell eingesetztes Werkzeug
zu kennen. Ein noch im Einstich stehendes Werkzeug ist ein Kollisionsrisiko;
dieses Szenario wurde nicht an der Maschine getestet.

- [x] XT/ZT fuer jedes ausgegebene T/M6 verlangen,
  auch bei nur einem Werkzeug; fehlende notwendige XT/ZT blockieren die Ausgabe
- [ ] Startbedingungen fuer Position, aktives Werkzeug und freien Eingriff
  explizit festlegen und pruefen; unbekannten Zustand nicht als sicher annehmen
- [ ] erste Freifahrt passend zu Werkzeug und Eingriff planen; kein pauschales
  Z-vor-X bei einem im Einstich stehenden Werkzeug
- [ ] Wechselposition und Hin-/Rueckweg im ausgewaehlten Koordinatensystem
  pruefen; mit LES-001, LES-006 und LES-022 abstimmen
- [ ] Einzelwerkzeug ohne XT/ZT, mehrere Werkzeuge, Innenwerkzeug und
  Stechwerkzeug im Eingriff als Regressionen plus LinuxCNC-Simulation abdecken

Teilstand: fehlendes XT/ZT blockiert auch Einzelwerkzeugprogramme.
G53-Hin-/Rueckwege koennen ohne Maschinenoffsets nicht gegen die
Werkstueck-Sperrzone geprueft werden. Erste Freifahrt bleibt offen.

Teilstand 2026-09-09: `optional_stop_toolchange` (Tooltip: "Fuegt vor
JEDEM Werkzeugwechsel ein optionales M1 ein") schloss bisher explizit den
allerersten Werkzeugwechsel aus (`last_tool > 0`-Bedingung) - genau dort,
wo Werkzeug und Position am wenigsten bekannt sind. Ausserdem stand das
bestehende M1 NACH der angenommenen sicheren Z-vor-X-Rueckzugsbewegung,
nicht davor. Beides behoben: M1 gilt jetzt fuer jeden Werkzeugwechsel
einschliesslich des ersten und steht vor jeder Bewegung. Das loest den
zweiten Punkt oben nur als PROZEDURALE Absicherung (Bediener kann vor dem
ersten Move pruefen) - die GEOMETRISCHE Frage (pauschales Z-vor-X bleibt
bei unbekanntem Zustand unveraendert bestehen, dritter Punkt oben) ist
damit nicht geloest, da eine Textgenerierung den tatsaechlichen
Maschinenzustand grundsaetzlich nicht kennen kann. Unter WSL/Debian mit
echtem rs274 verifiziert (11 Referenzen, 30 Matrixfaelle, Sonderfall mit
aktiviertem M1 vor dem ersten Wechsel), keine Ausgabeaenderung fuer
bestehende Programme (kein Referenzbeispiel aktiviert die Option). 543
Stub-/44 Qt-Tests bestanden.

### LES-040 Nicht endliche Zahlen zentral ablehnen

Codepruefung 2026-09-08: `gcode_utils.require_positive()` akzeptiert
`"nan"` und `"inf"` (lokal reproduziert). `float()` und reine
Groessenvergleiche sichern die Geometrie und Ausgabe daher nicht ausreichend.

- [x] gemeinsame Zahlenvalidierung mit `math.isfinite()` vor Berechnung und
  Ausgabe einsetzen, einschliesslich geladener Programm-/Step-Daten
- [ ] Koordinaten, Vorschuebe, Drehzahlen, Zustellungen und Sicherheitswerte
  auf Endlichkeit und fachlich passende Wertebereiche pruefen
- [x] Werkzeugnummern als gueltige ganze Zahlen validieren statt Dezimalwerte
  still mit `int(float(...))` abzuschneiden; mit LES-028 abstimmen
- [x] NaN, positive/negative Unendlichkeit, ungueltige Texte und Grenzwerte
  testen; Fehler muss vor Bewegungsplanung und Dateiersetzung auftreten

Teilstand: NaN/Inf an Import-, Modell- und Gesamtgeneratorgrenzen
blockiert; defekte X/Z-Punkte werden nicht mehr still uebersprungen.
Regressionsfaelle fuer Zahlen, Werkzeugnummern und Dateierhalt vorhanden.
Fachliche Wertebereiche aller Operationen und direkter Generatoraufrufe
bleiben vollstaendig durchzugehen (LES-028).

Ergaenzung 2026-09-09: Bohrmodus, Vorschub, Zustelltiefe und Verweilzeit
werden auch im direkten Bohrgenerator vor Planung validiert. Zahlenleser
verwerfen defekte explizite Werte statt Alias-/Standardwerte einzusetzen.
Positive Bohrwerte duerfen in der Ausgabe nicht auf null runden.

Ergaenzung 2026-09-09 (Drehzahl-Luecke): `append_tool_and_spindle()` -
die zentrale Funktion, die fuer JEDE Operation (Abspanen, Einstich,
Bohren, Gewinde, Planen) die Drehzahl ausgibt - schluckte `spindle=0`,
negative Werte, fehlende Werte sowie eine auf 0 U/min gerundete positive
Drehzahl bisher vollstaendig stillschweigend: kein Fehler, keine Warnung,
kein `M3`/`S..` irgendwo im Programm. Real reproduziert: eine komplette
40-Schnitt-Abspanen-Operation mit `spindle=0` erzeugte ein vollstaendig
"gueltiges" Programm, in dem die Spindel nie gestartet wird. Jetzt
blockiert die Ausgabe in diesem Fall, mit einer bewussten Ausnahme fuer
die reine Werkzeugwechsel-Positionierung (zwei Stellen in
`gcode_program.py`, `require_spindle=False`), deren Aufgabe nur das
Anfahren des Wechselpunkts ist - die eigentliche, operationsspezifische
Drehzahl (inkl. CSS) setzt danach immer der jeweilige Operations-
Generator selbst.

Blast-Radius beim ersten Anlauf: 148 von 543 Tests schlugen fehl, weil
viele Testfixtures quer durchs Projekt (Innenkontur-Matrix, Subroutinen,
Rueckzugslogik, CSS, Parting) nie eine Drehzahl gesetzt hatten, da es
bisher folgenlos war. Auf Rueckfrage vollstaendig gefixt: alle
betroffenen Fixtures um eine Drehzahl ergaenzt statt die Pruefung
aufzuweichen. Unter WSL/Debian mit echtem rs274 verifiziert (11
Referenzen, 30 Matrixfaelle), keine Ausgabeaenderung fuer bestehende
Programme. 549 Stub-/44 Qt-Tests bestanden.

Ergaenzung 2026-09-10 (Vorschub-Luecke bei ABSPANEN): Realer Bugreport -
`REQUIRED_KEYS[OpType.ABSPANEN]` (`gcode_utils.py`) fehlte `"feed"`. FACE
und DRILL nutzen dieselbe `require_positive()`-Maschinerie korrekt fuer
`feed`; ABSPANEN - die mit Abstand am haeufigsten genutzte Operation -
hatte die einzige Luecke. Reproduziert: `feed=0` erzeugte anstandslos
`G1 ... F0.000` (Werkzeug bewegt sich effektiv nicht); `feed=-0.15`
erzeugte `G1 ... F-0.150` (von LinuxCNC vermutlich ohnehin abgelehnt,
aber unentdeckt bis zur Maschine). Behoben durch Ergaenzen von `"feed"`
in der Liste; kein weiterer Codepfad noetig, dieselbe zentrale Pruefung
greift automatisch. GROOVE und THREAD haben bereits eigene, vollstaendige
Vorschub-/Parameter-Pruefungen (gegengeprueft, kein Bug gefunden). Neuer
Regressionstest `test_abspanen_with_non_positive_feed_blocks_generation`
(`tests/test_css_and_drill_validation.py`, per `git stash` gegen den
alten Code verifiziert). "Fehler vor Dateiersetzung" war bereits vorher
korrekt geloest: `ui_persistence.write_gcode_file()` generiert den
G-Code vollstaendig im Speicher, bevor ueberhaupt eine Datei angefasst
wird, und schreibt selbst dann nur atomar (`tempfile` + `os.replace`) -
ein Fehler kann nie eine bestehende Datei teilweise ueberschreiben
(bereits getestet in `test_invalid_drill_export_preserves_existing_file`).
627 Stub-/44 Qt-Tests, 88 statische Checks, elf Referenzen und 43
Matrixfaelle unter rs274 bestanden; keine Referenz geaendert (alle
nutzten bereits gueltige Vorschuebe).

Befund (dieselbe Sitzung): `zra`/`zri` (globale Rueckzugsebenen Aussen/
Innen Z) wurden nirgends auf einen plausiblen Wertebereich geprueft.
Reproduziert: `zra=-50.0` bei einem Rohteil mit Z-Bereich 0 bis -55
(Rueckzugsebene damit INNERHALB des Rohteils, kombiniert mit einem
ebenfalls unplausiblen `xra`) erzeugte anstandslos Eilgaenge in Richtung
Rohteil, inklusive einer vom Generator selbst ausgegebenen, aber nur
informativen Kommentarzeile `(WARN: Startpunkt ... liegt im Rohteil)` -
`get_approach_warnings()` (`gcode_safety.py`) sammelte das nur als
Text-Warnung, `validate_stock_segment()` prueft diesen Fall laut eigenem
Docstring bewusst NICHT (dafuer gedacht, dass Anfahr-/Rueckzugsziele
haeufig ABSICHTLICH innerhalb der Huellkurve liegen, z. B. Schlichten auf
bereits abgetragenem Durchmesser).

Nutzerentscheidung 2026-09-10: "Ausser bei Innenbearbeitung kann die
Rueckzugsebene niemals im Rohteil sein." Damit klargestellt und behoben:
neue Funktion `validate_external_retract_clearance()` (`gcode_safety.py`)
loest die AUSSEN-Rueckzugsebene (XRA/ZRA, `internal=False`) auf und
prueft sie GENAU EINMAL, ganz am Anfang von `generate_program_gcode()`
(`gcode_program.py`), gegen die volle Rohteil-Huellkurve (X- UND
Z-Bereich gleichzeitig - liegt der Punkt in mindestens einer Achse
ausserhalb, ist er real ausserhalb des Werkstuecks und damit sicher,
selbst wenn die andere Achse einen unauffaelligen Wert haette). XRI/ZRI
(Innenbearbeitung) sind davon bewusst unberuehrt - dort bleibt "innerhalb
der Huellkurve" per Definition der Normalfall, dafuer sorgt weiterhin
die eigene, bereits vorhandene `validate_internal_material_clearance()`.
Bewusst NICHT geloest (deutlich groesserer, separat verfolgter Umfang):
die generelle sichere Achsreihenfolge/-sequenzierung einzelner Bewegungen
(z. B. ob eine Z-Bewegung VOR Erreichen einer sicheren X-Position
stattfinden darf) - das ist LES-001/LES-039, nicht dieser Punkt. Diese
Pruefung stellt sicher, dass die KONFIGURIERTE Rueckzugsebene selbst
plausibel ist, nicht dass jede Einzelbewegung dorthin kollisionsfrei ist.

Neuer Unit-Test `test_validate_external_retract_clearance_unit` sowie
zwei Integrationstests (`test_external_retract_plane_inside_stock_blocks_generation`,
`test_external_retract_plane_outside_stock_in_either_axis_is_accepted`,
`tests/test_relief_and_safety.py`) - gegen den alten Code verifiziert
(direkter Unit-Test schlaegt mit `ImportError` fehl, Integrationstest mit
einer anderen, weniger spezifischen Fehlermeldung ueber die
Werkzeugwechsel-Diagonale). 630 Stub-/44 Qt-Tests, 88 statische Checks,
elf Referenzen und 43 Matrixfaelle unter rs274 bestanden; keine Referenz
geaendert (alle nutzten bereits plausible Rueckzugsebenen).

Damit ist die "Drehzahlen"- UND "Sicherheitswerte (Rueckzugsebenen)"-
Teilmenge des zweiten Punktes oben geschlossen. "Koordinaten, Vorschuebe
und Zustellungen" sind weiterhin nicht vollstaendig auf fachlich passende
Wertebereiche durchgegangen (z. B. GROOVE/THREAD ausserhalb der
zentralen `require_positive()`-Liste bei anderen Feldern als Vorschub/
Drehzahl) - bleibt offen.

### LES-003 Innen-Schruppen Parallel-Z abschliessend verifizieren

WICHTIGER BEFUND (real gegen den LinuxCNC-Interpreter verifiziert, Quelle
`/home/adm1n/linuxcnc-src/src/emc/rs274ngc/interp_g7x.cc`, Version
2.10.0~pre1 - identisch zur installierten Version): `G71`/`G72` erzeugen bei
Innenkonturen nur EINEN durchgehenden Schnitt statt echter Treppenstufen-
Schrupppaesse (empirisch mit `rs274` bestaetigt, sowohl fuer die reale
Nutzerkontur als auch fuer einen trivialen linearen Innenkegel), waehrend
identisch aufgebaute Aussenkonturen korrekt mehrfach zustellen. Kein Fehler
dieses Generators, sondern eine Einschraenkung dieser LinuxCNC-Version fuer
Innenbearbeitung. `G71`/`G72` werden deshalb jetzt AUSSCHLIESSLICH fuer
Aussenbearbeitung gewaehlt; Innenbearbeitung nutzt immer die
bewegungsbasierte Ersatzloesung (`rough_turn_parallel_x()`).

Der urspruenglich gemeldete Fehler ("keine wirkliche Abspanaufgabe
generiert") ist jetzt ebenfalls behoben: `rough_turn_parallel_x()` nutzte
eine viel zu schmale Fenster-Intersection (`x_cut +/- 1e-3`), die pro
X-Band meist gar kein Kontursegment traf ("no cut region"), waehrend ein
anderes Band zufaellig eine lange senkrechte Bohrungswand komplett in
einem einzigen Schnitt zusammenfasste. Ersetzt durch eine
"Materialreichweite"-Baenderung (pro `x_cut` wird der volle Z-Bereich
gesucht, in dem die Zielkontur ueber diese Tiefe hinausgeht) - real fuer die
Nutzerkontur "ausdrehen" verifiziert (9 gleichmaessige Einzelzustellungen
statt eines Riesenschnitts) und mit `rs274` fehlerfrei ausgefuehrt. Test:
`tests/test_internal_roughing_uses_g71_cycle.py::test_internal_roughing_with_real_bore_contour_produces_even_stepped_passes`.

- [x] `XRI` nur als sichere Einfahr-/Rueckzugsebene verwenden, niemals als
  Schnittbahn; Regression muss jeden G1-Profilwert gegen diese Grenze pruefen
- [x] Schlichtaufmass X/Z fuer Innenkonturen korrekt ausrichten
- [x] automatisierte Faelle fuer monoton steigende UND fallende Z-Konturen
  sowie Innen-/Aussenbearbeitung pflegen
- [x] `examples.py` um Innen-Abspanen (`Innen_Stufe.ngc`, `side=inside`)
  ergaenzen; automatisiert getestet und regeneriert, reale Abnahme unten offen
- [x] LinuxCNC-Parser, Backplot und Trockenlauf mit diesem Referenzteil
  dokumentieren (P0 - vor Praxiseinsatz zwingend)

Teilstand: positive vorhandene Bohrung XI bleibt Materialgrenze;
Zylinder, Stufe und Konus jeweils in beiden Konturrichtungen und drei
Bearbeitungsmodi automatisiert getestet (18 Kombinationen). XRI-Grenze,
mehrere Zustellungen und reines Schlichten ohne erneutes Schruppen geprueft.
Innenradius ist seit 09.09. in beiden Richtungen und drei Modi getestet;
Werkzeughuelle, sichere Ein-/Ausfahrt und reale Abnahme bleiben offen.

Teilstand 2026-09-10 (Audit der ersten beiden Checkbox-Punkte): Beide waren
inhaltlich bereits erledigt, nur nicht abgehakt.
`test_internal_profiles_preserve_xri_and_cut_in_both_contour_directions`
und `test_internal_radius_preserves_arcs_and_material_limits`
(`tests/test_internal_profile_matrix.py`) pruefen bereits jeden G1-Wert
aus 24 Kombinationen (Zylinder/Stufe/Konus/Radius-Bogen, beide Richtungen,
alle drei Modi) gegen XRI. Fuer die Aussenbearbeitung (grundsaetzlich
anderer Ausgabepfad: G71/G72-Zyklus statt bewegungsbasierter
Innen-Ersatzloesung, siehe Hauptbefund oben) fehlte die analoge
Richtungs-/Modus-Matrix - neu ergaenzt in
`tests/test_external_profile_matrix.py` (18 Kombinationen, prueft
Aussen-Analog: kein Schnitt ueberschreitet XA). 625 Stub-/44 Qt-Tests
bestanden, keine Referenz geaendert (reiner Testzuwachs).

Teilstand 2026-09-10 (LinuxCNC-Parser/Backplot/Trockenlauf fuer
`Innen_Stufe.ngc`): Parser (`rs274`) und echter AUTO-Trockenlauf bis `M30`
waren bereits am selben Tag erbracht (SIM-Sitzung, siehe
`doc/NATIVE_VERIFICATION_2026-09-09.md`); nachgeholt wurde ein lesbarer
Backplot-Screenshot (Testvariante mit nahem Werkzeugwechselpunkt
`xt=30`/`zt=10`, wie bei `Innen_Radius.ngc` etabliert). Lief in der SIM
fehlerfrei bis `M30` (leerer NML-Fehlerkanal); Vorschaugrafik zeigt die
Stufenkontur mit Schrupppaessen klar erkennbar getrennt von der
Schlichtkontur. Damit ist dieser Punkt fuer `Innen_Stufe.ngc` erledigt -
`Innen_Radius.ngc` war es bereits.

Teilstand 2026-09-10 (Nutzerfrage: liefert Zyklus (G71/G72) dieselbe
Kontur wie der explizite/"ISO"-Pfad?): neue
`tests/test_cycle_vs_explicit_parity.py` fuehrt dieselbe Aussenkontur
(Bogen an der Ecke, siehe Sehnen-Fix oben) einmal per `prefer_cycle` und
einmal per `prefer_explicit` aus und prueft jeden erzeugten Schrupp-Punkt
gegen die wahre (nicht linearisierte) Fertigkontur. Dabei zwei echte,
unabhaengig voneinander reproduzierte Bugs im bewegungsbasierten
("ISO") Aussen-Schrupp-Pfad gefunden und behoben (`gcode_roughing.py`):

1. Schlichtaufmass-Asymmetrie: der Aufmass-Versatz des Schrupp-Pfads
   (`if side_idx == 1 and mode_idx in (0, 2): rough_path = [...]`) wurde
   NUR fuer Innenbearbeitung (`side_idx == 1`) angewendet - Aussenkonturen
   im bewegungsbasierten Pfad bekamen ueberhaupt keinen Versatz und
   schrubbten exakt bis zur Fertigkontur, ohne jedes Schlichtaufmass.
   Fuer G71/G72-Zyklen unsichtbar (der Zyklus regelt das Aufmass selbst
   ueber den `D`-Parameter), aber jeder Grund, der den expliziten Pfad
   erzwingt (siehe Punkt 2, oder allgemein `output_preference=
   prefer_explicit`), hat das Aufmass komplett entfernt. Behoben: Versatz
   jetzt fuer beide Seiten, mit entgegengesetztem Vorzeichen (aussen
   groesserer Durchmesser/Versatz nach aussen, innen kleinerer
   Durchmesser/Versatz nach innen).
2. Spanbruch (`pause_enabled`/`pause_distance`, das selbst gebaute,
   an einen Siemens-Zyklus angelehnte Vorschub-Unterbrechungs-Feature)
   wurde von `can_use_cycles` nicht beruecksichtigt: eine sonst
   zyklustaugliche Kontur mit aktivem Spanbruch bekam trotzdem G71/G72 -
   dabei kann ein LinuxCNC-Zyklus diese Unterbrechung grundsaetzlich
   nicht ausfuehren (LinuxCNC kennt diesen Zyklus nicht, daher wurde der
   Pausen-Sub ja ueberhaupt erst gebaut). Das Feature wurde also je nach
   Kontur STILLSCHWEIGEND ignoriert, obwohl die Checkbox aktiv war.
   Nutzerbestaetigt real haeufig genutzt ("Diese Funktion nutze ich auf
   der Siemens fast immer"). Behoben: `pause_enabled and pause_distance
   > 0.0` erzwingt jetzt immer den expliziten Pfad, unabhaengig davon,
   ob die Kontur sonst zyklustauglich waere.

Beide Fixes ueber `git stash` gegen den alten Code verifiziert (3 der 5
neuen Paritaetstests schlagen ohne die Aenderungen fehl, mit spezifischen
Aufmass-Verletzungsmeldungen). 636 Stub-/44 Qt-Tests, elf Referenzen und
43 Matrixfaelle unter rs274 bestanden (nur `Innen_Radius.ngc` aendert sich
minimal durch den bereits dokumentierten Sehnen-Fix, keine neue
Aenderung durch diese beiden Fixes). Nutzerwunsch, die Paritaetspruefung
auf weitere Konturformen (Zylinder/Stufe/Konus, nicht nur den Bogenfall)
auszuweiten, bleibt offen ("eigentlich muesste jeder Kontur Test das
durchlaufen").

Ergaenzung 2026-09-10 (Innenbearbeitung, dieselbe Bogenkontur, mit
Spanbruch): der obige Paritaetstest deckte nur Aussenbearbeitung ab.
Innenbearbeitung nutzt aber IMMER den bewegungsbasierten Pfad (G71/G72
ist fuer Innenkonturen in dieser LinuxCNC-Version grundsaetzlich nicht
nutzbar, siehe Hauptbefund oben) - genau der Pfad, an dem sowohl der
Sehnen-Fix als auch das Spanbruch-Feature ansetzen, und genau dort, wo
der Sehnen-Fehler urspruenglich gefunden wurde. Neuer Test
`test_internal_rough_passes_never_undercut_allowance_through_arc_with_chip_breaking`
(`tests/test_internal_profile_matrix.py`) kombiniert die
`Innen_Radius.ngc`-Bogenkontur mit aktivem Spanbruch (`pause_enabled`)
und prueft jeden Schrupp-Schnittpunkt (aus `G1`- UND aus
`o<step_line_pause> call [...]`-Zeilen) gegen die wahre Fertigkontur.
Ueber `git stash` gegen den alten Sehnen-Code verifiziert (schlaegt ohne
den Fix real mit einer Aufmass-Verletzung fehl: nur 0.04mm statt
0.2mm Restaufmass bei X12.0 Z-15.8). Damit sind fuer die urspruenglich
gemeldete Bogenkontur jetzt alle drei vom Nutzer geforderten Faelle
automatisiert abgesichert: Aussenbearbeitung per Zyklus, Aussenbearbeitung
explizit, und Innenbearbeitung explizit inklusive Vorschub-Unterbrechung.
637 Stub-/44 Qt-Tests, elf Referenzen und 43 Matrixfaelle unter rs274
bestanden (keine neue Referenzaenderung, reiner Testzuwachs).

### LES-045 G71/G72: D/I-Parameter vertauscht, Zustelltiefe und Aufmass falsch

WICHTIGER BEFUND (Nutzerfrage 2026-09-10 "wie sicher koennen wir sein, dass
es funktioniert?", waehrend der gezielten Absicherung des G71/G72-
Zyklus-Pfads): der reale G7x-Zyklus dieser LinuxCNC-Version (Quelle
`/usr/src/linuxcnc-master/src/emc/rs274ngc/interp_g7x.cc`, Version
2.10.0~pre1, Doku-Kommentar direkt im Quelltext) definiert die Parameter
anders, als der Turning-Generator (`gcode_roughing.py`) sie bisher
gesendet hat:

```
x,z  Anfahrpunkt/Rohteilecke
d    "Final distance to profile"  - senkrechtes AUFMASS, RADIUS-Einheit
i    "Increment of cutting"       - ZUSTELLTIEFE pro Schnitt, RADIUS-Einheit, Default 1.0mm
u,w  zusaetzlicher X/Z-Versatz    - vom installierten Interpreter NICHT unterstuetzt
                                    ("Bad character 'u' used", per rs274 verifiziert)
```

Unser Generator sendete bisher NUR `G71/G72 Q.. X.. Z.. D{depth_per_pass}`
- kein `I` (blieb beim Default 1.0mm), und `D` bekam die konfigurierte
Zustelltiefe statt des Aufmasses. Konkret bedeutete das:

1. **Die konfigurierte Zustelltiefe (`depth_per_pass`) wurde fuer JEDEN
   G71/G72-Zyklus ignoriert.** Empirisch mit `rs274` bestaetigt: ein Test
   mit `depth_per_pass=1.0` und einer mit `depth_per_pass=0.3` erzeugten
   BEIDE exakt dieselbe Schnittfolge (1.0mm Radius-Schritte, Default).
   Sicherheitsrelevant: eine bewusst reduzierte Zustellung (duenne
   Wandstaerke, hartes Material, schwaches Werkzeug) wurde beim Wechsel
   auf Zyklus-Ausgabe stillschweigend auf die volle Default-Zustellung
   angehoben.
2. **Das konfigurierte Schlichtaufmass (`finish_allow_x`/`finish_allow_z`)
   kam fuer G71/G72 NIE an.** Stattdessen wirkte `depth_per_pass` (zufaellig
   im `D`-Slot gelandet) als Aufmass. Beispiel `Kontur_Radius_Fase.ngc`
   (kein Aufmass konfiguriert): der Zyklus liess trotzdem 0.75mm Radius
   (1.5mm Durchmesser) unbeabsichtigtes Restmaterial stehen, das der
   nachfolgende Schlichtschnitt zusaetzlich abtrug - inkonsistent mit der
   Nutzerkonfiguration und inkonsistent mit dem bewegungsbasierten Pfad,
   der bei gleicher Konfiguration exakt 0mm Aufmass gelassen haette.

`U`/`W` (die im Quelltext vorgesehene Moeglichkeit, X- und Z-Aufmass
getrennt zu setzen) sind vom installierten Interpreter-Build nicht
nutzbar. Da unser Modell zwei unabhaengige Werte (`finish_allow_x`,
`finish_allow_z`) kennt, der Zyklus aber nur EIN Aufmass (`D`, radial,
wirkt als senkrechter Versatz zur Kontur) kennt, kann eine Kontur mit
`finish_allow_z > finish_allow_x` damit nicht sicher abgebildet werden
(an einem planparallelen Segment wirkt `D` vollstaendig als Z-Aufmass -
ist das geforderte Z-Aufmass groesser als das aus X abgeleitete `D`,
entstuende dort zu wenig Reserve).

**Fix** (`gcode_roughing.py`, G71- und G72-Zeile):
- `I{depth_per_pass / 2.0:.3f}` ergaenzt (Durchmesserwert der UI durch 2,
  da der Zyklus radial rechnet - identische Konvention wie beim
  bewegungsbasierten Pfad, dort aber direkt als Durchmesser-Bandbreite).
- `D{finish_allow_x / 2.0:.3f}` statt `D{depth_per_pass:.3f}`.
- Der bisherige `stock_x_adj = stock_x - finish_allow_x`-Hack im
  G72-Zweig (Versuch, Aufmass ueber eine verkleinerte Startgrenze
  nachzubilden) entfernt - jetzt ueberfluessig und irrefuehrend, da `D`
  das Aufmass korrekt uebernimmt.
- `can_use_cycles` um `finish_allow_z <= finish_allow_x` erweitert; bei
  Verletzung erzwingt das (wie Spanbruch/Freistich) den bewegungsbasierten
  Pfad, der beide Achsen unabhaengig versetzt. Neue Kommentarzeile
  `(Fallback-Grund: Z-Aufmass groesser als X-Aufmass - Zyklus kennt nur
  ein Aufmass)` in beiden Strategiezweigen.

**Verifikation:** D/I-Semantik empirisch per `rs274 -g -n 2` an einer
geraden Zylinderwand bestaetigt (`D0.2` erzeugte exakt 0.2mm Radius-
Restaufmass am letzten Schnitt, `I0.15` exakt 0.15mm Radius-Schritte,
unabhaengig vom vorher fuer `D` genutzten `depth_per_pass`-Wert).
Zusaetzlich an einer Bogenkontur (identisch zu `Kontur_Radius_Fase.ngc`,
mit `finish_allow_x=finish_allow_z=0.4`) nachgefahren: Restaufmass am
gesamten Schnitt >= dem konfigurierten Wert, nirgends darunter. `Kontur_
Radius_Fase.ngc` (einzige der zwoelf Referenzen mit echtem Dreh-G71) neu
erzeugt (`D0.750`->`D0.000 I0.375`, da dort kein Aufmass konfiguriert
ist); Planen/Planen_Radius/CSS_Wechsel nutzen den bereits VORHER korrekten
Facing-Zyklus-Pfad (`gcode_face.py`, sendet schon immer `D{finish_allow_z}
I{depth_per_pass} R{retract}` - dieses Vorbild lieferte den Fix-Ansatz)
und sind unveraendert. `tests/test_abspanen_finish_allowance.py` pruefte
bisher faelschlich das ALTE (falsche) Verhalten (`X39.500` als "reduzierter
Zyklusstart") - korrigiert auf die neuen, real verifizierten Werte
(`X40.000`, `D0.250`, `I0.500`). 638 Stub-/44 Qt-Tests, zwoelf Referenzen
und 43 Matrixfaelle unter rs274 bestanden.

- [x] `R` (Ruecklaufabstand) fuer den Dreh-Zyklus ergaenzen, analog zum
  bereits genutzten `retract` in `gcode_face.py` (aktuell Default 0.5mm,
  bisher unauffaellig, aber nicht bewusst gewaehlt)
- [x] pruefen, ob eine Kontur mit `finish_allow_z > finish_allow_x` in der
  Praxis haeufig genug vorkommt, um eine bessere Loesung als den
  Zwangs-Fallback zu rechtfertigen (z. B. Aufteilen in mehrere Zyklen)

Teilstand 2026-09-10 (R-Ruecklaufabstand): per `rs274`-Trace verifiziert,
dass `R` (wie `D`/`I`) ein reiner, unkonvertierter Radius-/Z-Abstand ist -
`R5.0` erzeugte einen exakt diagonalen 5mm-Ruecklauf in X UND Z
(`escape=r*{1,1}` im Quelltext). Der bisherige Default (0.5mm) war knapp,
aber nicht sicherheitskritisch falsch (nur kuerzere Freifahrt zwischen
Schruppgaengen, kein Kollisionsrisiko mit dem Material). Jetzt
`R{LEADOUT_LENGTH_DEFAULT}` (2.0mm) in beiden G71/G72-Zeilen ergaenzt -
matcht die im bewegungsbasierten Pfad bereits etablierte Freifahrtlaenge.
`Kontur_Radius_Fase.ngc` (einzige Referenz mit echtem Dreh-G71) neu
erzeugt (`R2.000` ergaenzt, sonst unveraendert). 638 Stub-/44 Qt-Tests,
zwoelf Referenzen und 43 Matrixfaelle unter rs274 bestanden.

Nutzerrueckmeldung 2026-09-10 (finish_allow_z > finish_allow_x): in der
Praxis selten/unwichtig - meist gleiches oder kleineres Z- als X-Aufmass.
Der bestehende Zwangs-Fallback auf den bewegungsbasierten Pfad reicht
aus; keine weitere Arbeit noetig. LES-045 damit vollstaendig
abgeschlossen.

### LES-005 Innen-Schlichtanfahrt und Rueckzug

Teilstand 2026-09-09: expliziter Innen-Schlichtrueckzug zuerst radial
auf XRI, dann axial auf ZRI. Bei Radiuskorrektur G40 und lineare Freifahrt
im Vorschub; zu kurzer Abwahlweg blockiert. Beide Konturrichtungen mit
Zylinder/Konus und Radiuskorrektur im Interpreter geprueft. Werkzeughuelle,
weitere korrigierte Konturen und reale Abnahme bleiben offen.

Ein Einfahrweg fuer aktive Schneidenradiuskorrektur existiert bereits.
Realtest-Frage 11 ist beantwortet: Innenstufe, Innenkonus und Innenradius
wirken korrekt; der Innenfreistich bleibt als bekannter Fehler unter
LES-010/LES-011 offen. Die Antwort schliesst die Nutzerfrage, ersetzt aber
nicht die reproduzierbare Generator- und LinuxCNC-Verifikation.

- [x] zuerst auf nachweislich freien Innendurchmesser fahren
- [x] axial auf Konturstart fahren, bevor der Schnittdurchmesser angefahren wird
- [x] Schneidenradiuskorrektur nur auf ausreichend langem Einfahrweg aktivieren
- [x] Konturstart vorne und hinten getrennt testen
- [x] nach dem Schnitt zuerst radial und danach axial freifahren
- [x] Innenstufe, Innenkonus und Innenradius als automatisierte Regressionen
  plus LinuxCNC-Backplot absichern
- [ ] Innenfreistich nach Umsetzung von LES-010/LES-011 separat abnehmen

Teilstand 2026-09-09 (native Fortsetzung): Der explizite Innen-Schlichtweg
faehrt nun auf XRI axial bis zur Z-Lage des Konturstarts und stellt erst dort
radial im Bearbeitungsvorschub auf den ersten Profildurchmesser zu. Zuvor
wurde bereits an der vorderen Sicherheitsebene auf Schnittdurchmesser
gefahren und anschliessend diagonal zum tiefen Konturstart geschnitten.
Die neue Reihenfolge gilt auch ohne Radiuskorrektur, damit ein separater
Schlichtstep vorhandenes Aufmass nicht per G0 trifft. Bei G41.1 wird der
radiale Einfahrweg anhand der auf drei Stellen gerundeten X-Ausgabe im
G7-Durchmessermass geprueft; er muss groesser als der Werkzeugdurchmesser
sein. Vorne/hinten, mit/ohne Kompensation und Rundungsgrenzen automatisiert
getestet. 595 Stub-/44 echte Qt-Tests sowie elf Referenzen und 43
Matrixfaelle mit nativem rs274 bestanden. `Innen_Stufe.ngc` und
`Innen_Radius.ngc` zeigen die geaenderte Anfahrt. Vollstaendiger Nachweis
des freien Innendurchmessers inklusive Werkzeughuelle sowie grafische und
reale Abnahme bleiben offen.

Teilstand 2026-09-09 (SIM-Konfiguration korrigiert, echter Trockenlauf):
Die QtDragon-Simulation (`sim.qtdragon_lathe.basic_xz_lathe-1/lathe.ini`,
ausserhalb dieses Projekts) verhinderte bisher jeden echten Trockenlauf -
`emcMotionInit: emcTrajInit failed` beim Start liess die Maschine nie aus
dem Not-Aus. Ursache war ein unnoetiger 50us-Base-Thread
(`BASE_PERIOD = 50000`), den `basic_sim.tcl` nur auf ausdruecklichen
INI-Wunsch anlegt und den diese reine Simulation (kein Stepgen/keine
Schrittmotor-Ausgabe) nicht braucht. Nach Entfernen von `BASE_PERIOD`,
Ergaenzen von `HOME = 0.0` in `[JOINT_0]`/`[JOINT_1]` und Umstellen von
`SUBROUTINE_PATH` auf einen absoluten Pfad (Sicherung der Original-INI:
`lathe.ini.bak-2026-09-09`) liess sich die Maschine erstmals aus dem
Not-Aus holen, beide Achsen referenzieren (`HOME=0/0`) und `Innen_Radius.ngc`
sowie `Innen_Stufe.ngc` je einmal vollstaendig im AUTO-Modus bis `M30`
abfahren - inklusive des manuellen Werkzeugwechseldialogs, ohne Eintrag im
NML-Fehlerkanal. Damit ist erstmals ein echter, nicht nur interpretierter
Trockenlauf fuer diese beiden Referenzen erbracht. Ein doppelt geladenes
`hal_manualtoolchange` (ein zweites, dauerhaft unsichtbares
Werkzeugwechsel-Fenster) ist als harmloser, aber unschoener Rest in der
SIM-Konfiguration aufgefallen und noch nicht bereinigt. Ein gezoomter,
grafisch abgelesener Konturvergleich (Backplot-Screenshot der Feinkontur)
bleibt weiterhin offen - die Vorschaugrafik stellt Eilgang zum weit
entfernten Werkzeugwechselpunkt und die millimetergenaue Kontur im selben
Massstab dar, sodass Letztere im Screenshot nicht lesbar wird. Details:
`doc/NATIVE_VERIFICATION_2026-09-09.md`.

Teilstand 2026-09-10 ("zuerst auf nachweislich freien Innendurchmesser
fahren"): Neue Pruefung `validate_internal_material_clearance()`
(`gcode_utils.py`), aufgerufen aus `generate_abspanen_gcode()` fuer jede
Innenoperation direkt nach der bestehenden `validate_internal_x_limit()`.
Sie blockiert die Ausgabe, sobald bekannte Werte der konfigurierten XRI
widersprechen: das im Programmkopf gesetzte `XI` (deckt die gesamte
Werkstuecklaenge ab, z. B. Rohr-Rohteil) oder Durchmesser UND Tiefe der
zuletzt vorangehenden Bohren-Operation (`_last_drill_diameter`/
`_last_drill_depth`, Tiefe neu in `gcode_program.py` mitverfolgt). Fehlt
sowohl XI als auch eine vorangehende Bohrung, bleibt die Pruefung bewusst
stumm (keine gesicherte Aussage moeglich) - dafuer existiert weiterhin die
separate Reihenfolge-Warnung in `checks.py::validate_program_setup`
(`tests/test_drill_before_internal_check.py`). Neuer Testfall
`tests/test_internal_material_clearance.py` (11 Faelle: XI/Bohrung
ausreichend, XI/Bohrdurchmesser zu klein, Bohrtiefe zu gering, fehlende
Angaben bleiben stumm, End-to-End ueber `generate_program_gcode`).
Zwei bestehende Testfixtures (`test_internal_finish_retract.py`,
`test_generation_boundaries.py::test_same_tool_internal_rough_then_finish_shares_single_toolchange`)
verwendeten XRI-Werte, die groesser als ihr eigenes XI/Bohrdurchmesser
waren (fuer die dort jeweils getestete, andere Grenze unerheblich) - auf
plausible Werte korrigiert. 607 Stub-/44 Qt-Tests, 88 statische Checks,
elf Referenzen und 43 Matrixfaelle unter rs274 bestanden; keine Referenz
geaendert (alle bestehenden XI/XRI-Kombinationen waren bereits konsistent).
Weiterhin offen: eine echte Werkzeughuellen-/Kollisionspruefung (Ø und
Tiefe sind ein Fortschritt, ersetzen aber keine geometrische
Kollisionspruefung des gesamten Werkzeugs) sowie grafische/reale Abnahme.

Teilstand 2026-09-10 (Innenkonus als vollwertige Referenz ergaenzt):
Innenstufe und Innenradius hatten bereits eigene `ngc/`-Referenzen samt
rs274- und SIM-Backplot-Nachweis; Innenkonus lief bisher nur als
Profil-Fall (`"cone"`) in der generischen Direktionsmatrix
(`tests/test_internal_profile_matrix.py`) mit, ohne eigene eingecheckte
Referenz. Neu ergaenzt: `Innen_Konus.ngc` in `examples.py`
(Kegelkontur (12,-30)->(18,0), sonst identischer Aufbau wie
`Innen_Stufe.ngc`: `xi=10`, `xri=9`, gleiches Werkzeug/Aufmass) und als
zwoelfte Referenz regeneriert. Alle zwoelf Referenzen bestehen weiterhin
statische Pruefung und `rs274`; 43 Matrixfaelle unveraendert bestanden.
Mit derselben Zoom-Testvariante (naher Werkzeugwechselpunkt) in der SIM
bis `M30` gefahren (42s, leerer NML-Fehlerkanal) - Backplot zeigt die
Kegelform klar erkennbar getrennt von der Schlichtkontur. Damit haben
jetzt alle drei genannten Innenkonturformen (Stufe, Konus, Radius) sowohl
automatisierte Generator-Regressionen als auch einen dokumentierten
nativen LinuxCNC-Nachweis (Parser + Trockenlauf + Backplot). 631 Stub-/44
Qt-Tests bestanden.

### LES-037 Freistich/Relief am Gewindeende verankern

Automatische DIN-Freistiche werden aus der Gewindeoperation abgeleitet und
nur in eine passende zylindrische Aussen-/Innenkontur eingespleisst. Das
G76-Ende liegt um die DIN-Ueberdeckung `f` innerhalb der Freistichbreite;
fehlt die gesamte Konturstrecke, bricht die Erzeugung sicher ab. Vorschau,
Schlichtweg und Kontur-Subroutine verwenden dieselben Primitive.

- [ ] realen Aussen- und Innengewinde-Fall mit automatischem Freistich im
  LinuxCNC-Backplot und Trockenlauf abnehmen

Teilstand 2026-09-09: neue automatisierte Matrix (`test_thread_relief_matrix.py`,
`lathe_easystep.verification_cases.thread_relief_case`) deckt Aussen/Innen
x Rechts/Links ab und beweist ausdruecklich die Kernaussage dieses
Punktes: eine Verlaengerung der Kontur HINTER dem Gewinde verschiebt den
Freistich NICHT (bleibt am Gewindeende verankert, nicht am Konturende).
Ebenso automatisiert: zu wenig Platz fuer den Freistich bricht sicher ab
und laesst eine bestehende Exportdatei unveraendert. Alle vier
Kombinationen unter WSL/Debian mit echtem rs274 verifiziert
(`thread_relief_*.ngc` in der Matrix). Der verbleibende Punkt (reale
Backplot-/Trockenlauf-Abnahme an der Maschine) bleibt unveraendert offen -
das kann automatisiert nicht ersetzt werden.

## P1 - Fachliche Vollstaendigkeit fuer 0.8.0

### LES-006 Rueckzugsstrategie je Bearbeitungsart

Den Inventor-LinuxCNC-Post als Referenz auswerten und fuer jede Operation
explizit festlegen:

- [x] nur X
- [x] nur Z
- [x] X dann Z
- [x] Z dann X
- [x] X/Z gleichzeitig
- [x] Matrix fuer Planen, Abspanen innen/aussen, Schlichten, Gewinde,
  Bohren, Einstich/Abstich, Keilnut, Werkzeugwechsel und Parken dokumentieren
- [ ] Strategie in Generator und Tests abbilden

Referenz ausgewertet 2026-09-09 (`doc/linuxcnc turning.cps`, Autodesk
generischer LinuxCNC-Drehpost): Der Post hat **keine** Matrix je
Operationstyp. `safePositionStyle` (Rueckzug: X / Z / X-dann-Z / Z-dann-X
/ beide in einer Zeile, Default X-dann-Z) und `approachStyle` (Anfahrt:
Z-dann-X oder beide in einer Zeile, Default beide in einer Zeile) sind
JE EINE globale Post-Eigenschaft fuer das gesamte Programm - unabhaengig
davon, ob davor geplant, gedreht, gestochen, gebohrt oder ein Gewinde
geschnitten wurde. Zurueckgezogen wird zudem nur bei Werkzeug-/Spindel-/
WCS-Wechsel (`insertToolCall || newSpindle || newWorkOffset`); zwischen
Operationen mit demselben Werkzeug gibt es keinen Zwischenrueckzug.
Der Rueckzug selbst geht auf eine feste Maschinenposition (`G28`/`G53`
zu einer konfigurierten Home-Position), nicht auf eine werkstueckrelative
XRA/ZRA-Position.

Damit ist die urspruenglich erwartete "Matrix je Operationstyp aus dem
Post extrahieren" nicht befuellbar - sie existiert dort nicht. Unser
Generator unterscheidet bereits FEINER als die Referenz (Bohren/Gewinde
Z-vor-X, Einstich/Keilnut X-vor-Z, siehe LES-001-Regressionstest
`test_safe_retract_axis_order_is_operation_specific`) - das ist eine
eigene Verfeinerung, keine Luecke gegenueber Inventor.

Gepruefter, bewusst NICHT umgesetzter Vorschlag: Rueckzug bei unbekanntem
Ausgangszustand (LES-039) auf eine feste G53-Maschinenposition umstellen,
analog zur Referenz. Geometrisch widerlegt: eine Diagonalbewegung von
einer beliebigen Startposition zu einem weit entfernten festen Punkt
durchquert nachweisbar trotzdem eine dazwischenliegende Sperrzone
(Gegenbeispiel: Sperrzone X0..100/Z-200..10, fester Punkt X200/Z500,
Start X5/Z-150 - bei t=0.1 des Diagonalwegs steht das Werkzeug bei
X24.5/Z-85, mitten in der Sperrzone). Ein fester Maschinenpunkt loest das
"unbekannter Ausgangszustand"-Problem also nicht besser als die aktuelle
werkstueckrelative Loesung, entzieht sich dabei aber vollstaendig der
`validate_chuck_segment()`/`validate_stock_segment()`-Pruefung aus
LES-001 (die nur in Werkstueckkoordinaten funktioniert). Der aktuelle,
achsweise gepruefte Ansatz bleibt daher die robustere Wahl.

Letzter Punkt ("Strategie in Generator und Tests abbilden") bleibt offen,
da er sich auf die urspruenglich erwartete Matrix bezog, die es so nicht
gibt; das tatsaechlich Uebertragbare (feinere Differenzierung als die
Referenz) ist bereits im Generator abgebildet und getestet.

### LES-010 Lokale DIN-Freistichgeometrie

Freistiche werden jetzt an JEDEM Segment erzeugt, nicht mehr nur am ersten
oder letzten Segment der gesamten Kontur (real gegen den LinuxCNC-
Interpreter verifiziert: sauberer, fehlerfreier Parse eines Freistichs
mitten in einer Welle, siehe CHANGELOG.md). Aussen- und Innenfreistich sind
beide bestaetigt korrekt.

- [ ] DIN-76-Geometrie (Breite/Tiefe je Gewindegroesse) gegen eine
  verifizierte Norm-Referenz pruefen - die Platzierung ist jetzt korrekt,
  die hinterlegten Zahlenwerte selbst sind noch nicht extern verifiziert
  (siehe LES-019, "keine Werte schaetzen")
- [x] Referenzbeispiel `Freistich_Mitte.ngc` in `examples.py` und Regeneration

### LES-012 Konturprimitive und G2/G3 erhalten

Der explizite Schlichtweg kann Radien als G2/G3 ausgeben. Der reale
LinuxCNC-Fehler bei Boegen mit echtem X-Zentrumsversatz ist behoben:
Im Durchmessermodus G7 wird die X-Differenz zum Zentrum fuer den radialen
`I`-Wert halbiert. Regressionen decken den direkten Schlichtpfad und die
G71/G72-Kontur-Subroutine ab. Verbleibende Move-based-Pfade linearisieren
Geometrie teilweise noch.

- [ ] Linien und Boegen bis zur Ausgabe als Primitive fuehren
- [ ] Radien nicht in reine G1-Punktlisten umwandeln
- [x] Arc-Intersections im Move-based Roughing vertiefen
- [ ] Vorschau und Generator auf dieselbe Primitive-Quelle umstellen

Einordnung 2026-09-09: die verbleibenden Punkte betreffen ausschliesslich
die *Schrupp-Zustellung* der Move-based-Ersatzloesung
(`rough_turn_parallel_x/z`, genutzt wenn G71/G72 nicht anwendbar ist, z. B.
Innenbearbeitung). Diese Funktionen nehmen bereits linearisierte
Punktlisten entgegen (`segments_from_polyline`), nicht die Primitive
selbst - ein Bogen im Schruppbereich wird dort als Sehnenfolge statt
echtem G2/G3 abgetragen. Die FERTIGKONTUR (was die tatsaechliche
Bauteilgeometrie bestimmt) ist davon NICHT betroffen: der explizite
Schlichtweg (`_emit_finish_primitives`) und die G71/G72-Kontur-Subroutine
geben Boegen bereits durchgehend als echte G2/G3 mit korrektem I/K aus,
real verifiziert (siehe oben, Nichtnull-I-Faelle).
- [x] mindestens einen Referenzbogen mit `I != 0` dauerhaft in
  `examples.py`/`ngc/` halten
- [x] fuer direkten Schlichtweg UND G71/G72-Subroutine im Test nachweisen,
  dass Start- und Endradius zum ausgegebenen I/K-Zentrum uebereinstimmen
- [x] denselben Nichtnull-I-Fall im LinuxCNC-Parser bestaetigen (Backplot
  grafisch weiterhin offen)

Teilstand 2026-09-09: `Kontur_Radius_Fase.ngc` (`G3 ... I-3.000 K0.000`)
sowie die daraus abgeleiteten Matrixfaelle `outside_arc_parallel_x/z.ngc`
sind Teil der bei jeder Sitzung gegen echten rs274 verifizierten
Referenzen - Parser-Teil damit abgedeckt. Primitive-Erhalt in
move-based Roughing-Pfaden und gemeinsame Vorschau-/Generatorquelle
bleiben die verbleibenden, groesseren Punkte.

Korrektur 2026-09-10: Die obige Einordnung "durch Schlichtaufmass
fachlich unkritisch" war **falsch** und wurde durch einen realen Befund
widerlegt. Beim Betrachten der SIM-Backplot-Screenshots fiel auf, dass
Schrupp-Paesse an der kleinen R1-Rundung zwischen Bohrung (Ø12) und
Schulter (Ø14/Z-15) in `Innen_Radius.ngc` sichtbar ins Fertigteil
schnitten. Nachrechnung mit der wahren Bogengeometrie (nicht der Sehne)
bestaetigte: bis zu 0.43mm Durchmesser-Uebermass bei 0.2mm konfiguriertem
Aufmass (Pass 6: X13.000 bei Z-15.300, wahre Kontur dort nur Ø12.572) -
bei kleinen Bogenradien kann der Sehnenfehler das Aufmass leicht
uebersteigen; "unkritisch" gilt also NICHT allgemein, nur fuer
hinreichend grosse Radien im Verhaeltnis zum Aufmass.

Behoben in `contour_features.py`: `primitive_to_points()` tastet
Bogen-Primitive jetzt entlang des wahren Kreises ab (adaptive Segmentzahl,
Sehnenabweichung <0.0005mm), statt sie auf ihre zwei Endpunkte zu
reduzieren. Die Materialreichweiten-Berechnung je X-Band
(`intersect_segment_with_x_band` in `gcode_roughing.py`) bekommt dadurch
eine praezise Bogenapproximation statt der Sehne - ohne Aenderung an der
Schrupp-Logik selbst. Regressionstest
`test_internal_rough_passes_never_undercut_allowance_through_arc`
(`tests/test_internal_profile_matrix.py`) reproduziert den alten Fehler
(schlaegt ohne Fix fehl, siehe Verifikation im Sitzungsverlauf) und
prueft dauerhaft, dass kein Schrupp-Schnitt entlang eines Bogens das
konfigurierte Aufmass unterschreitet. Einzige geaenderte Referenz:
`Innen_Radius.ngc` (vier Zeilen, Pass 4-7 jetzt flacher/sicherer).
596 Stub-/44 Qt-Tests, 88 statische Checks sowie elf Referenzen und 43
Matrixfaelle unter rs274 weiterhin bestanden.

### LES-013 Sichere CSS-Umschaltung

- [x] begrenzte G97-Anfahrdrehzahl berechnen und Ausgaberundung validieren
- [x] G96 vor Bearbeitung aktivieren, explizite Freifahrten mit G97 ausgeben
- [x] Move-based-Schruppen aktiviert/suspendiert CSS je Pass
- [x] CSS/Festdrehzahl/CSS-Folge und echten Qt-Save/Load pruefen
- [x] fuenf CSS-Bearbeitungen mit echtem rs274 verifizieren
- [ ] Aktivierungsdurchmesser und konstante Freifahrtdrehzahl fachlich fuer
  alle Pfade bewerten: stock_x ist nicht jeder einzelne Passdurchmesser
- [ ] Verhalten innerhalb von G71/G72/G76 und Groove-Makro getrennt bewerten;
  interne Zyklusbewegungen sind keine explizit mit G97 abgesicherten Moves
- [ ] grafischen Backplot und reale Maschinenabnahme dokumentieren

Review 2026-09-09: Die vorherige Aussage, alle Anfahr- und Aktivierungs-
durchmesser seien identisch und alle Punkte abgeschlossen, war zu weitgehend.
Die begrenzte Festdrehzahlstrategie bleibt erhalten. Nachweise und aktuelle
Grenzen: [Interpreterbericht](doc/linuxcnc_2026-09-09/README.md).

### LES-015 Innenkontur-Testmatrix

Realtest-Frage 11 ist beantwortet: Innenstufe, Innenkonus und Innenradius
erscheinen korrekt, der Freistich ist der bekannte offene LES-010/LES-011-Fall.
Offen ist deshalb keine weitere Grundsatzantwort, sondern eine reproduzierbare
Test- und Referenzmatrix.

- [ ] zylindrische Innenkontur
- [ ] Innenstufe
- [ ] Innenkonus
- [ ] Innenradius mit `I != 0`
- [ ] Innenkontur mit Freistich nach Umsetzung von LES-010/LES-011
- [ ] Schruppen mit anschliessendem Schlichten
- [ ] Konturstart vorne und hinten sowie steigende/fallende Z-Reihenfolge
- [ ] Werkzeugradiuskorrektur, Konturseite und sichere Ein-/Ausfahrt je Fall
- [ ] Vorschau, erzeugten G-Code und LinuxCNC-Backplot je Referenz vergleichen

Teilstand 2026-09-09: zusaetzlich sechs Innenradiusfaelle (beide
Konturrichtungen, drei Modi), gemeinsame Bogenquelle und I/K-Radien getestet;
`Innen_Radius.ngc` als Referenz. Die Checkboxen bleiben fuer die vollstaendige
Matrix einschliesslich Ein-/Ausfahrt, Kompensation und Backplot offen.

### LES-019 Fehlende DIN-76-Presets

- [ ] verifizierte Normwerte fuer M2, M2.5 und M3.5 beschaffen
- [ ] Aussen- und Innenvarianten ergaenzen
- [ ] Datenvalidierung und Preset-Tests erweitern
- [ ] keine Werte schaetzen

### LES-030 LinuxCNC-Simulationsmatrix

- [x] alle elf Referenzprogramme nach Generatoraenderungen regenerieren
- [ ] Planen, Bohren, Gewinde, Einstich, Abspanen innen/aussen und Konturen pruefen
- [ ] Nichtnull-I-Boegen unter G7 im direkten Schlichtweg und in
  G71/G72-Subroutinen auf Parserfehler und korrekten Backplot pruefen
- [ ] Innen-G71 mit monoton steigendem und fallendem Z sowie vorhandener
  Bohrung als Materialgrenze pruefen
- [ ] gemischte Operationsfolge G96 -> G97 -> G96 inklusive D/S-Einheiten
  und Aktivierungsposition pruefen
- [ ] Parserfehler, Backplot, Werkzeugwechsel und Parkbewegungen dokumentieren
- [ ] relevante Sicherheits- und Materialabtragsfaelle als reale Trockenlaeufe bestaetigen
- [ ] Maschinenprofile und Futter-Sperrzonen mit Beispielen verifizieren

Teilstand 2026-09-09: elf Referenzen und 30 Matrixfaelle unter WSL/Debian
mit echtem rs274 bis PROGRAM_END geprueft. CSS-Wechsel, Innenradius und
Aussenbogen unter G71/G72 bestanden. Grafischer Backplot und Trockenlauf
bleiben offen; synthetische Werkzeugtabelle ersetzt keine Maschinenkonfiguration.

Teilstand 2026-09-09 (native SIM, Trockenlauf-Versuch aller elf
Referenzen): Nach den INI-Fixes (siehe oben) liefen `Bohren.ngc`,
`CSS_Wechsel.ngc`, `Freistich_Mitte.ngc`, `Gewinde.ngc` und
`Kontur_Radius_Fase.ngc` automatisiert und fehlerfrei bis `M30` durch
(1-100s), inkl. automatischem Werkzeugwechsel ohne manuellen Klick. Die
restlichen sechs (`Abdrehen.ngc`, `Einstich.ngc`, `Innen_Radius.ngc`,
`Innen_Stufe.ngc`, `Planen.ngc`, `Planen_Radius.ngc`) ueberschritten das
150s-Testzeitbudget dieser Sitzung, liefen aber nachweislich weiter
(Position/Drehzahl aendern sich kontinuierlich) - kein Haenger, nur zu
knapp bemessenes Zeitbudget bei vielen Einzelpaessen. Noch offen: alle
elf mit ausreichendem Zeitbudget zu Ende laufen lassen und grafisch
(Backplot-Screenshot) dokumentieren. Details:
[nativer Bericht](doc/NATIVE_VERIFICATION_2026-09-09.md).

Teilstand 2026-09-10: mit 400s Zeitbudget liefen vier weitere Referenzen
durch (`Innen_Radius.ngc`, `Innen_Stufe.ngc`, `Planen.ngc`,
`Planen_Radius.ngc`) - damit 9/11. `Abdrehen.ngc` gezielt mit
Live-Tracking geprueft: kein Haenger, sondern kontinuierlich sehr viele
feine Schrupppaesse (materialintensivstes Referenzbeispiel). Gezoomter,
lesbarer Backplot-Screenshot (naher Werkzeugwechselpunkt als
Testvariante) fuer `Innen_Radius.ngc` erstellt - Schrupppaesse und
Schlichtkontur inkl. axialer Einfahrt klar erkennbar. Offen: `Abdrehen.ngc`
und `Einstich.ngc` einmal mit ausreichendem Zeitbudget (mehrere Minuten)
zu Ende laufen lassen; Werkzeughuellen-Kollisionspruefung bleibt
weiterhin unabhaengig davon offen.

### LES-036 Kantenform "Radius" beim Planen

Radius ist implementiert; Vorschau und G-Code verwenden gemeinsame
Primitive. Externe Parser-/Backplot- und Panelabnahme bleiben offen.

- [x] Radius-Eckengeometrie fuer den 90-Grad-Planen-Spezialfall umsetzen
- [x] Durchmesser-/Radiusumrechnung fuer X sowie G2/G3-I/K eindeutig herleiten
- [x] String-IDs und alte numerische Save-Dateien weiterhin unterstuetzen
- [x] Vorschau und G-Code aus derselben Geometrie ableiten
- [x] Grenzfaelle pruefen: Radius 0, zu grosser Radius, Schruppen,
  Schlichten und Schruppen+Schlichten
- [x] echten PyQt5-Roundtrip testen
- [x] LinuxCNC-Parser testen (Backplot grafisch weiterhin offen)
- [ ] Realtest am Panel nach Umsetzung dokumentieren

Teilstand 2026-09-09: `Planen_Radius.ngc` und `Kontur_Radius_Fase.ngc`
sind Teil der 11 Referenzen, die bei jeder Sitzung mit echtem `rs274`
verifiziert werden (zuletzt bestanden) - der Parser-Teil ist damit
abgedeckt. Grafischer Backplot und Panelabnahme bleiben offen.

## P2 - Bedienung, Wartbarkeit und Architektur

### LES-044 Modulare Panel-Architektur: Geruest, Text, Darstellung und Generator strikt trennen

Architekturvorgabe des Nutzers 2026-09-10 (uebergeordnetes Leitbild fuer
LES-020/LES-024/LES-034/LES-035, ersetzt keinen davon): Ziel ist ein
Geruest, das nur die grobe Aufteilung des Panels darstellt (Reiter/
Bereiche), darin einzelne grafische Felder mit jeweils eigener Funktion.
Jede der folgenden Schichten soll fuer sich austauschbar sein, OHNE dass
eine andere Schicht Funktion verliert:

1. **Textausgabe/Sprache** - alles, was Text betrifft, getrennt
   betrachtet, sodass die Sprache durch Austausch einer einzigen Datei
   wechselbar ist.
2. **Grafische Darstellungselemente** - z. B. die Vorschau-Darstellung
   der Schneidplatte - austauschbar, ohne dass die Funktion (Geometrie-
   berechnung, Auswahl, Speichern/Laden) beeintraechtigt wird.
3. **Generator** - von Praesentation/Darstellung unabhaengig (Vorgabe
   bereits weitgehend erfuellt, siehe unten).

Leitsatz: alles muss bearbeitbar sein, ohne dass Funktion verloren geht -
das gelingt am ehesten mit einer moeglichst feinen Aufteilung in
unabhaengige Teile.

Bestandsaufnahme (was die Vorgabe schon erfuellt / wo sie noch fehlt):

- [x] Sprache ist bereits dateibasiert getrennt: `de.lng`/`en.lng`/`es.lng`
  mit je 1.022 identischen, nichtleeren Schluesseln (`languages/`,
  `TRANSLATIONS`-Store) - entspricht Punkt 1 fuer reine UI-Label-Texte.
- [ ] Punkt 1 ist NICHT lueckenlos: G-Code-Kommentare (`(Schlichtschnitt
  Kontur)`, Warnungen wie in Zeile 18 von `Innen_Radius.ngc`,
  `ValueError`-Meldungen in `gcode_safety.py`/`gcode_roughing.py`) sind
  fest deutschsprachig in den Generator-Python-Dateien eingebettet, nicht
  ueber `TRANSLATIONS` gefuehrt - pruefen, ob/wie weit das fuer
  G-Code-Kommentare und Ausnahmetexte ueberhaupt sinnvoll/gewollt ist
  (G-Code-Kommentare sind Werkstattdokumentation, keine UI), und falls ja,
  wie sie ohne Aufwandsexplosion an denselben Sprachmechanismus
  angebunden werden koennen.
- [ ] Punkt 2 ist die groesste Luecke: `render_tool_preview(handler, tool)`
  (`tool_logic.py`) sowie die uebrige Vorschau-Geometrie (`preview_geometry.py`,
  601 Zeilen) nehmen `handler` direkt entgegen statt ueber eine definierte
  Schnittstelle (reine Geometrie/Daten rein, Zeichenbefehle raus) zu
  arbeiten - ein Austausch der Darstellung (andere Grafikbibliothek, andere
  Visualisierung der Schneidplatte) erfordert aktuell Aenderungen mitten in
  der Funktionslogik statt eines Austauschs an einer Stelle. Deckt sich mit
  dem bereits offenen LES-034 (Vorschau/G-Code auf denselben Bewegungen,
  Trennung Werkstueck/Werkzeugweg/Hilfsgeometrie) - LES-034 trennt
  fachliche Geometriequellen, LES-044 zusaetzlich die Rendering-Schicht
  selbst von der Geometrieberechnung.
- [x] Generator (`gcode_*.py`, `contour_logic.py`, `contour_features.py`)
  ist bereits unabhaengig von UI/Qt - importiert keine `qtpy`/`PyQt5`-Module,
  laesst sich (wie in dieser Sitzung mehrfach genutzt) direkt per
  `generate_program_gcode()` ohne laufende UI aufrufen und testen.
- [ ] "Geruest zeigt nur grobe Aufteilung" deckt sich mit LES-020 (Handler
  weiter verkleinern) und LES-024 (Vorschau/Schnittansicht sowie
  Step-Liste/Programmverwaltung in eigene Struktur auslagern, Controller/
  Tooltips/Sprach-IDs/Validierung je Modul zuordnen, direkte
  Widgetzugriffe zwischen Modulen durch definierte Schnittstellen
  ersetzen) - LES-024 bleibt die naechste konkrete Arbeit dafuer.

- [ ] Zielarchitektur (Geruest / Panel-Module / Text / Darstellung /
  Generator als getrennte, je fuer sich testbare Schichten mit
  definierten Schnittstellen dazwischen) als kurzes Architekturdokument
  festhalten, BEVOR LES-020/024/034 weitere Extraktionen vornehmen - sonst
  entstehen wieder Ad-hoc-Grenzen statt der hier vorgegebenen Struktur
- [ ] `render_tool_preview()`/Schneidplatten-Darstellung als erstes
  konkretes Beispiel fuer "Darstellungselement austauschbar, Funktion
  bleibt" umbauen (Geometrie-Berechnung von Zeichenaufruf trennen)
- [ ] pruefen, ob/wie G-Code-Kommentare und Fehlertexte an den
  bestehenden Sprachmechanismus angebunden werden sollen (siehe oben)
- [ ] nach jedem Modularisierungsschritt: voller Testlauf, echtes
  `uic.loadUi`, Embedded- und Standalone-Start vergleichen (LES-035)

### LES-018 G70 fuer separaten Schlichtstep

Der aktuelle explizite Schlichtweg ist fachlich korrekt. Zu pruefen ist nur die
Optimierung, einen bereits von einem frueheren G71/G72-Step verwendeten
Kontur-Sub spaeter per G70 wiederzuverwenden.

- [x] stabile Zuordnung Kontur -> Subroutine -> vorheriger Schruppstep entwerfen
- [x] reiner Schlichtstep darf niemals erneut schruppen
- [x] Fallback auf expliziten Schlichtweg beibehalten

Umgesetzt 2026-09-09: Kontur -> Subroutine war bereits stabil zugeordnet
(`settings["contour_subs"]`, vorab pro Konturname allokiert und ueber alle
Operationen geteilt, die dieselbe `contour_name` referenzieren). Neu:
`_cycle_defined_subs` merkt sich nach jedem tatsaechlich ausgegebenen
G71/G72 das Paar (Sub-Nummer, aussen/innen). Ein reiner Schlichtstep
(`mode == "finish"`, eigene Operation) nutzt `G70 Q<sub>` nur, wenn dieser
exakte Sub bereits nachweislich zyklisch definiert wurde UND keine
Werkzeugradiuskorrektur noetig ist (der bestehende G70-Pfad der
kombinierten Schruppen+Schlichten-Ausgabe unterstuetzt diese ebenfalls
nicht). Da G71/G72 bei Innenbearbeitung nie verwendet wird (LES-003),
bleibt die Menge dort automatisch leer - der bestehende explizite Weg
greift unveraendert als Fallback, ebenso wenn keine benannte Kontur,
keine passende vorherige Zyklusnutzung oder Werkzeugkorrektur vorliegt.
Real mit einem separaten Zwei-Werkzeug-Rough/Finish-Programm gegen echten
rs274 verifiziert: der Schlichtschritt fuehrt nur die zwei tatsaechlichen
Konturbewegungen aus `G70 Q100`, keine erneute Schruppbewegung, keine
zweite Subroutine-Definition. Alle 11 Referenzen und 30 Matrixfaelle
bestehen unveraendert (keine davon nutzt den neuen Pfad, da sie entweder
dasselbe Werkzeug fuer Schruppen+Schlichten in einer Operation verwenden
oder Kompensation/Innenbearbeitung einsetzen). 555 Stub-/44 Qt-Tests
bestanden.

### LES-020 Handler weiter verkleinern

Jede Extraktion einzeln mit vollem Testlauf und echtem `uic.loadUi` pruefen.

- [x] Programmkopf-Sammlung
- [x] Kontursegment-Sammlung
- [x] Gewinde-Preset-UI nach `ui_thread.py`
- [x] Widget-Bootstrapping nach `ui_widget_lookup.py` (19 Methoden, davon
      `_register_known_widgets`, `_resolve_core_widgets_strict`,
      `_get_widget_by_name`; `TAB_TRANSLATIONS`/`_looks_like_panel_widget`
      dafuer nach `ui_registry.py` verschoben, um einen Zirkelimport zu
      vermeiden - dabei einen bestehenden `NameError`-Bug in
      `widget_resolver.py` gefunden und behoben, der den
      "sieht wie unser Panel aus"-Fallback in `_pick_best_root()` stumm
      per `except Exception: pass` verschluckt hatte). 589 Stub-/44
      Qt-Tests bestanden, NGC-Referenzen unveraendert.
- [x] Tooltip-Erzwingung nach `ui_tooltips.py`

### LES-022 Zentraler Bewegungs- und Modalzustand

- [x] aktuelle X/Z-Position bei jeder Move-Emission mitfuehren, soweit
      DETERMINISTISCH bekannt (siehe Teilstand "dritte Etappe" unten - zwei
      bewusst verbleibende Ausnahmen mit undokumentiertem/datenabhaengigem
      Endpunkt bleiben explizit auf "unbekannt" gesetzt statt geraten)
- [ ] G90/G91, G94/G95, G96/G97, G18 und G40/G41/G42 verwalten (G96/G97
      CSS-Modalzustand erledigt, siehe Teilstand oben; die uebrigen Codes
      gezielt auf ein analoges Stale-State-Risiko geprueft - siehe
      Teilstand unten, kein Bug gefunden, aber auch kein ad-hoc Zustand zum
      Formalisieren vorhanden)
- [ ] M3/M4/M5, M7/M8/M9 und Werkstuecknullpunkt verwalten (ebenfalls
      geprueft, siehe Teilstand unten)
- [x] sichere Pfadentscheidungen auf reale aktuelle Position stuetzen (fuer
      die Rueckzugs-/Anfahrt-/Werkzeugwechsel-Positionierung; dabei einen
      echten Sicherheitsfehler gefunden und behoben, siehe Teilstand unten)
- [ ] robuste explizite Ausgabe fuer manuell bearbeitbaren G-Code erhalten

Teilstand 2026-09-09 (erste Etappe: Positions-Tracking): neue Klasse
`MotionState` (`lathe_easystep/motion_state.py`) ersetzt die bisherigen
ad-hoc settings-Keys `_is_at_safe`/`_safe_x`/`_safe_z` in `gcode_safety.py`
(`emit_safe_retract_for_op`, `emit_approach`, `append_tool_and_spindle`) und
`gcode_groove.py`. Dabei einen echten, reproduzierbaren Sicherheitsfehler
gefunden: nach einer Aussen-Operation liess ein kombinierter Schruppen+
Schlichten-Innen-Step (Move-based Fallback, z. B. jede Innenbearbeitung, da
G71/G72 dafuer nicht zuverlaessig ist) das veraltete `_is_at_safe`-Flag
faelschlich als "bereits sicher" gelten, obwohl die zuletzt tatsaechlich
erreichte Position die AUSSEN- statt der fuer diese Operation gueltigen
INNEN-Sicherheitsebene war - `emit_approach()` uebersprang dadurch den
Rueckzug auf die sichere Z-Ebene vor dem Schlichtschnitt und fuhr im Eilgang
(G0) diagonal direkt durch das noch stehengebliebene Restmaterial (real
reproduziert: `G0 X12.000` bei Z=-29.900, mitten durch 0.2mm unbearbeitetes
Aufmass). Zwei bestehende Referenzprogramme (`Innen_Radius.ngc`,
`Innen_Stufe.ngc`) waren betroffen und wurden neu generiert - beide fuegen
jetzt vor Schrupp- und Schlichteinstieg den fehlenden Rueckzug ein. Neuer
gezielter Regressionstest
(`test_combined_internal_rough_finish_after_external_op_retracts_before_finish_entry`).
590 Stub-/44 Qt-Tests, elf Referenzen und 43 rs274-Matrixfaelle bestanden.

Teilstand 2026-09-09 (zweite Etappe: CSS/G96-Modalzustand): neue Klasse
`SpindleState` (`lathe_easystep/motion_state.py`) ersetzt die bisherigen
ad-hoc settings-Keys `_pending_css`/`_active_css`/`_css_fixed_rpm` in
`activate_pending_css()`/`suspend_css()`/`append_tool_and_spindle()`
(`gcode_safety.py`) - dieselben Funktionen, die alle anderen Operations-
Generatoren (Abspanen, Bohren, Gewinde, Face, Groove) bereits ausschliess-
lich ueber die oeffentlichen Funktionen nutzen, keine weiteren Aenderungen
noetig. Anders als beim Positions-Tracking (erste Etappe) war die CSS-
Suspend/Resume-Logik bereits vollstaendig konsistent (kein Sicherheitsfehler
gefunden) - reine Architekturbereinigung, Ausgabe unveraendert (elf
Referenzen, 43 rs274-Matrixfaelle inkl. `css_clearance_*`-Faelle bestehen
identisch). 590 Stub-/44 Qt-Tests weiterhin bestanden.

Teilstand 2026-09-09 (Bestandsaufnahme uebrige modale Codes): gezielt auf
ein analoges Stale-State-Risiko wie bei Positions-Tracking/CSS geprueft -
in keinem Fall gefunden:

- G90/G91.1/G95/G54 werden ausschliesslich einmalig im Programmkopf gesetzt
  (`G18 G7 G90 G91.1 G40 G80` / `G95` / `G54`) und danach nie mehr
  veraendert; volles G91 (inkrementell) und G94 (Vorschub/Minute) werden im
  gesamten Code nirgends emittiert. Keine dynamische Umschaltung -> kein
  ad-hoc Zustand zum Formalisieren vorhanden.
- G40/G41/G42 (Werkzeugradiuskorrektur) wird ausschliesslich in
  `generate_abspanen_gcode()` verwendet, rein ueber lokale Variablen
  (`compensation_command`/`nose_disabled`) je Aufruf - Aktivierung und
  Abwahl sind im selben Funktionsaufruf zwingend gepaart (jeder Pfad
  zwischen Aktivierung und Abwahl endet entweder in der Abwahl oder in
  einer `ValueError`, die die gesamte Programmerzeugung abbricht, bevor
  unvollstaendiger G-Code je verwendet wird). Kein settings-Dict-Zustand
  beteiligt, kein Cross-Operation-Risiko moeglich.
- M4 (Spindel rueckwaerts) wird nirgends emittiert - bewusst, da
  Linksgewinde ueber die Z-Fahrtrichtung (`z_dir`) in `gcode_thread.py`
  abgebildet wird, nicht ueber Spindelumkehr.
- G17 erscheint einmalig als dokumentierter LinuxCNC-Bohrzyklus-Sonderfall
  (Kommentar "G17 nur fuer Bohrzyklus - LinuxCNC Besonderheit" in
  `gcode_drill.py`) und wird danach zuverlaessig wieder auf G18
  zurueckgesetzt - bereits vor dieser Session verifiziert.
- Werkstuecknullpunkt: ausschliesslich statisches G54 im Programmkopf,
  keine G55/G56/... oder dynamische Umschaltung im Code vorhanden.
- Dabei zwei bereits laenger unbenutzte Legacy-Funktionen gefunden
  (`gcode_for_turn`/`gcode_for_bore` fuer `OpType.TURN`/`BORE`), die M8
  direkt statt ueber `emit_coolant()` ausgeben und nie M9 abschalten -
  diese Operationstypen sind aber ueber die UI nicht mehr erreichbar
  (abgeloest durch ABSPANEN mit `side`-Parameter, kein `tabTurn`/`tabBore`
  in `ui_registry.TAB_TRANSLATIONS`). Kein LES-022-Thema, sondern eine
  separate Altlasten-/Aufraeumfrage (toter Code behalten fuer alte
  gespeicherte Programme vs. entfernen) - hier nicht angefasst.

Verbleibend fuer eine spaetere, deutlich groessere Etappe: vollstaendiges
Positions-Tracking ueber Schnittbewegungen (G1/G2/G3) in allen sechs
Operations-Generatoren (`gcode_roughing.py`, `gcode_drill.py`,
`gcode_thread.py`, `gcode_groove.py`, `gcode_keyway.py`, `gcode_face.py`) -
das wuerde erlauben, die in `gcode_roughing.py` nach dem Schruppen bewusst
konservative `_motion_state(settings).clear()`-Invalidierung durch echtes
Wissen ueber die real erreichte Endposition zu ersetzen und dadurch
zusaetzliche, tatsaechlich redundante Rueckzuege zu erkennen - ohne
begleitende, sorgfaeltige Verifikation (analog zur Positions-Tracking-
Etappe) aber ein reales Risiko, versehentlich einen neuen Fehler derselben
Klasse einzufuehren, die diese Etappe gerade behoben hat.

Teilstand 2026-09-10 (dritte Etappe: alle sechs Generatoren, Nutzerauftrag
nach LES-001-Rueckfrage): jede Operation, deren Endposition nach dem
letzten emittierten Bewegungsbefehl DETERMINISTISCH bekannt ist, aktualisiert
jetzt `_motion_state(settings)` - nichts wird mehr stillschweigend veraltet
stehen gelassen:

- `gcode_drill.py`: Bohrzyklen (G81/G82/G83/G73/G84) enden per rs274
  bestaetigt immer auf (x_start, safe_z) - G80 kehrt zuverlaessig auf die
  R-Ebene zurueck, X bewegt sich in keinem Bohrmodus.
- `gcode_thread.py`: **echter, zuvor unbemerkter Bug gefunden.** G76 endet
  per rs274 bestaetigt immer exakt auf (approach_x, end_z) - dem tiefsten
  Punkt des letzten Gewindeschnitts, OHNE automatischen Rueckzug. Der
  Bewegungszustand wurde bisher nach dem Gewindeschneiden ueberhaupt nicht
  aktualisiert und blieb faelschlich auf der Anfahrposition VOR dem Zyklus
  stehen (insbesondere Z blieb auf `start_z` statt `end_z` - bei einem
  20mm-Gewinde ein Versatz von 20mm). Ein direkt folgender Schritt haette
  einen tatsaechlich noetigen Rueckzug potenziell faelschlich als bereits
  erledigt ansehen koennen. Neuer Regressionstest
  `test_external_thread_records_real_end_position_not_stale_approach`
  (`tests/test_gcode_motion_regressions.py`), gegen den alten Code per
  `git stash` verifiziert (schlaegt mit `KeyError` fehl - vorher wurde
  `_motion` ueberhaupt nicht angelegt).
- `gcode_face.py`: G70 endet per rs274 bestaetigt (an einer geraden
  Zylinderwand UND an einer Bogenkontur getestet, siehe LES-045) immer
  exakt am letzten Punkt der referenzierten Kontur - bei Facing-Mode
  "finish"/"rough_finish" (G70 immer die letzte Bewegung) ist das
  `(end_x, end_z)`. Reines Schruppen (Mode "rough", nur G72 ohne G70) bleibt
  bewusst unbekannt (`clear()`) - siehe naechster Punkt.
- `gcode_roughing.py`: der bereits integrierte G70-Zyklus-Abschluss
  (`cycle_finish_done`, relief_mode "full") sowie die G70-Wiederverwendung
  eines frueheren Zyklus-Subs (reiner Schlichtschritt) und der explizite
  G1/G2/G3-Schlichtpfad (sowohl Aussen- als auch Innen-Rueckzuglogik)
  aktualisieren jetzt korrekt den Endpunkt. Die bestehende
  `clear()`-Invalidierung nach dem SCHRUPPEN bleibt unveraendert bestehen -
  siehe naechster Absatz.
- `gcode_keyway.py`: bricht immer mit `ValueError` ab (Makro-Variablen im
  G-Code sind verboten), erzeugt nie eine Bewegung - nichts zu tun.

**Bewusst NICHT geloest, aus demselben Grund wie oben angekuendigt (echtes
Risiko statt Verifikation vs. Aufwand):** zwei Faelle bleiben auf `clear()`
(vorher: stillschweigend veraltet - jetzt zumindest explizit als unbekannt
markiert, kein Verhaltensunterschied fuer nachfolgende Schritte, aber kein
Stale-State-Risiko mehr):

1. `gcode_groove.py`: der `o220`-Nutzyklus stuft die Nutbreite in einer
   datenabhaengigen Reihenfolge (0, +stepW, -stepW, +2*stepW, ...) bis zum
   Ueberschreiten von omin/omax. Die Plunge-Achse kehrt nachweislich (aus
   dem generierten Makro-Quelltext selbst ablesbar, `groove_sub_definition()`)
   immer auf `Astart` zurueck, die BREITENACHSE aber auf den letzten
   tatsaechlich erreichten Woff-Wert - der haengt vom genauen Verhaeltnis
   Werkzeugbreite/Nutbreite/Ueberdeckung ab. Das in Python nachzurechnen
   wuerde die Zustelllogik des Makros duplizieren - genau das Risiko
   ("Duplizierung der Zustelllogik in wc" per DEV.md-Prinzip vermeiden),
   das schon frueher bewusst umgangen wurde.
2. `gcode_roughing.py`: die eigentlichen Schrupp-Baender in
   `rough_turn_parallel_x()`/`rough_turn_parallel_z()` (mehrere X-/Z-Baender,
   je nach Kontur mit mehreren Z-/X-Intervallen, optionalem Spanbruch,
   `allow_undercut`) - das ist exakt die in der vorherigen Notiz als
   "deutlich groessere Etappe" angekuendigte Arbeit. Der Nutzen waere rein
   die Vermeidung zusaetzlicher, aber bereits SICHERER redundanter
   Rueckzuege (die bestehende `clear()`-Invalidierung fuehrt nie zu einer
   fehlenden Sicherheitspruefung, nur zu einem im Einzelfall unnoetigen
   Rueckzug) - das Risiko-Nutzen-Verhaeltnis einer ueberstuerzten Umsetzung
   ist damit unguenstig. Bleibt als eigener, spaeter zu planender Schritt
   offen.

639 Stub-/44 Qt-Tests, zwoelf Referenzen und 43 Matrixfaelle unter rs274
bestanden (keine Referenzaenderung ausser den bereits bekannten
Sehnen-/D-I-Diffs von heute - reines Positions-Tracking ohne Ausgabe-
aenderung, mit der einen Ausnahme des real gefundenen Thread-Bugs, der
aber in keiner der zwoelf Referenzen beobachtbar war, da keine davon einen
Schritt direkt nach einem Gewinde-Step hat).

### LES-024 Restliche UI-Modularisierung

- [ ] Vorschau/Schnittansicht in eigene UI-Struktur auslagern
- [ ] Step-Liste und Programmverwaltung auslagern
- [ ] je Modul Controller, Tooltips, Sprach-IDs und Validierung zuordnen
- [ ] direkte Widgetzugriffe zwischen Modulen durch definierte Schnittstellen ersetzen
- [ ] Embedded- und Standalone-Laden testen

### LES-027 Performance

Realtest-Frage 7 ist beantwortet, aber alarmierend: "startzeit momentan
wieder über 20 sec, also viel zu lange" - das Wort "wieder" deutet auf eine
Regression hin (fruehere Startzeit war offenbar besser). Noch nicht
root-caused; keine Codeaenderung in dieser Session dazu.

- [ ] Root Cause fuer die aktuell >20s Startzeit finden (Profiling: welcher
  Schritt dominiert - `.ui`-Laden, Preview-Erstaufbau, Sprachkatalog,
  Tool-Table-Laden, HAL/Qt-Init?)
- [ ] pruefen, ob ein frueherer Commit/eine frühere Version schneller war
  (git bisect auf Startzeit, falls reproduzierbar messbar)
- [ ] Startzeit bis sichtbares und bedienbares Panel messen
- [ ] Embedded und Standalone vergleichen
- [ ] Reiterwechsel, Stepwechsel und Preview-Refresh messen

Teilstand 2026-09-09: `measure_startup.py` (neu) startet pro Messung
einen frischen Prozess mit echtem PyQt5 offscreen und misst Shell-UI,
acht Teil-UIs, Zusatzwidgets und statische Uebersetzungsstruktur separat;
Handler-Instrumentierung macht `_auto_load_tool_table`,
`_init_contour_table` und `_update_contour_preview_temp` einzeln
messbar. Ergebnis: die gemeldeten >20s liessen sich unter Windows
(0.587s Prozesslaufzeit) und WSL/Debian (1.565s) NICHT reproduzieren -
kein Root Cause gefunden, keine unbelegte Optimierung vorgenommen.
Misst explizit NICHT: HAL-Start, reale Werkzeugtabelle, sichtbares/
bedienbares Panel, Embedded-Betrieb, Reiter-/Stepwechsel. Details:
[doc/STARTUP_2026-09-09.md](doc/STARTUP_2026-09-09.md). Alle
Checklistenpunkte bleiben fachlich offen - es existiert jetzt Mess-
infrastruktur, aber weder Reproduktion noch Root Cause noch Embedded-
Vergleich.

### LES-028 Eingaben zentral normalisieren

Teilstand: G76 blockiert ungueltige Steigung, Tiefe, Durchmesser, Laenge,
R/H/L und Taperlaenge; Zahlenstrings werden gleichwertig ausgewertet,
explizites H=0 bleibt erhalten. Null fuer automatische Schnitttiefen bleibt
kompatibel. Werkzeugnummern werden nicht mehr dezimal abgeschnitten.


- [ ] Werkzeugwechsel nur aus normalisiertem Werkzeugdatensatz erzeugen
- [ ] G76-Parameter vor Ausgabe vollstaendig normalisieren und validieren
- [x] bestaetigtes G7-Masssystem nicht erneut als offenen Fachfehler behandeln
- [ ] Preset- und manuelle Werte nachvollziehbar vergleichen

Teilstand 2026-09-09: `infeed_q` (G76-Zustellwinkel `Q`) floss bisher
vollstaendig ungeprueft in die Ausgabe ein - negative oder unplausibel
grosse Werte (z. B. >=90 Grad) waeren unveraendert als `Q`-Wort
ausgegeben worden. Jetzt auf den physikalisch gueltigen Bereich 0..<90
Grad geprueft (0 = radiale Zustellung, z. B. Quadratgewinde, bleibt
gueltig). Recherche zum "G7-Masssystem"-Punkt: keine verbleibende Stelle
in Doku oder Code gefunden, die das bereits per Realtest bestaetigte
G76-Massystem (Frage F12: "generierte Werte scheinen zu passen", siehe
CHANGELOG.md) noch als offenen Fachfehler fuehrt - Punkt abgehakt, ohne
Codeaenderung noetig.

Bewusst NICHT umgesetzt (Risiko einer Fehlinterpretation zu hoch fuer
eine Vermutung): "Werkzeugwechsel nur aus normalisiertem
Werkzeugdatensatz erzeugen" und "Preset-/manuelle Werte nachvollziehbar
vergleichen" sind im TODO nicht praezise genug spezifiziert, um sicher zu
entscheiden, WELCHE Striktheit gemeint ist (z. B. ob jede referenzierte
Werkzeugnummer zwingend einen Eintrag in `settings["tools"]` haben muss -
das koennte, aehnlich dem Drehzahl-Fund bei LES-040, viele bestehende
Testfixtures und ggf. reale Programme ohne vollstaendig gepflegte
Werkzeugtabelle brechen). Verbleibt offen fuer eine Sitzung mit Klaerung
der genauen Anforderung.

Unter WSL/Debian mit echtem rs274 verifiziert (11 Referenzen, 30
Matrixfaelle), keine Ausgabeaenderung. 559 Stub-Tests, 44 Real-Qt-Tests,
keine Skips.

### LES-031 Redundante Ausgabe

- [x] identische oder Null-G0-Bewegungen ueber alle Operationen pruefen
- [x] modale Befehle nur bei sinnvoller Zustandsaenderung ausgeben
- [x] Robustheit bei manueller Programmbearbeitung gegen minimale Ausgabe abwaegen

Teilstand 2026-09-09: zwei echte, quer durchs Projekt reproduzierbare
Nullbewegungen gefunden und behoben:

1. `gcode_drill.py` gab nach jedem Bohrzyklus (`G80`) unbedingt ein
   `G0 Z<safe_z>` aus. Empirisch gegen echten `rs274` verifiziert (siehe
   Gegenbeispiel mit Rueckzugsebene R oberhalb der Startposition):
   LinuxCNC-Zyklen kehren im Default-Modus `G99` auf die Rueckzugsebene R
   zurueck, NICHT auf die Z-Position vor dem Zyklus. Da `retract` (R) ohne
   explizite Angabe auf `safe_z` faellt, steht das Werkzeug nach `G80` im
   Standardfall bereits auf `safe_z` - die zusaetzliche Bewegung war eine
   Nullbewegung. Nur wenn `retract` bewusst hoeher als `safe_z` gesetzt
   ist, bleibt die Freifahrt eine echte, notwendige Bewegung (getestet).
2. `append_tool_and_spindle()` gab vor JEDEM Werkzeugwechsel unbedingt
   einen Rueckzug auf die Aussen-Sicherheitsposition aus - auch wenn die
   vorherige Operation (per `emit_safe_retract_for_op()`) bereits exakt
   dorthin zurueckgezogen hatte (der haeufigste Fall bei zwei
   aufeinanderfolgenden Aussenoperationen mit unterschiedlichem Werkzeug).
   Neue, eng begrenzte Zustandsverfolgung `_safe_x`/`_safe_z` (nur an den
   Stellen gesetzt, an denen unmittelbar zuvor sicher bekannt ist, dass das
   Werkzeug dort steht - keine generelle Positionsverfolgung) erkennt den
   Fall und ueberspringt die Nullbewegung.

Bewusst NICHT angefasst: eine dritte, in der Innenkontur-Matrix gefundene
Redundanz (`rough_turn_parallel_x()`/`rough_turn_parallel_z()` retrahieren
nach jedem Pass per `G0 X<XRI>` - beim letzten Pass doppelt sich das mit
dem anschliessenden `emit_safe_retract_for_op()`). Ein Fix dafuer wuerde
`_safe_x` auch OHNE zugehoeriges `_safe_z` setzen und muesste dann bei
JEDER folgenden Werkzeugbewegung (auch im `rough_finish`-Kombimodus, wo
danach ein Schlichtpass die Position tatsaechlich veraendert) zuverlaessig
wieder invalidiert werden - ohne echte zentrale Positionsverfolgung
(LES-022) ist das Risiko veralteten, faelschlich als sicher angenommenen
Zustands zu hoch fuer einen Nullbewegungs-Fix. Gehoert inhaltlich zu
LES-022.

Unter WSL/Debian mit echtem rs274 verifiziert (11 Referenzen, 30
Matrixfaelle), Ausgabe kuerzer (Bohren.ngc -1 Zeile, CSS_Wechsel.ngc -4
Zeilen). 553 Stub-Tests, 44 Real-Qt-Tests, keine Skips.

### LES-032 Werkzeuggeometrie

- [ ] Nasenradius, Schneidenlage, Schneidenlaenge und Werkzeugbreite auswerten
- [ ] Innen-/Aussenwerkzeuge plausibilisieren
- [ ] Tooltable-Daten fuer Kollisions- und Erreichbarkeitspruefungen nutzen
- [ ] Werkzeugvorschau und Generator auf denselben Datensatz stuetzen

Teilstand 2026-09-09 (Codepruefung, keine Aenderung): Nasenradius und
Orientierung sind bereits ausgewertet und validiert
(`nose_compensation_command()` in `gcode_safety.py` - Radius >=0,
Orientierung Q/L in 0..9, Ausgaberundung auf 0 abgefangen, real getestet
in `tests/test_tool_compensation_validation.py`). "Innen-/Aussenwerkzeuge
plausibilisieren" existiert ebenfalls bereits als Kommentartext-Heuristik
(`checks.py::validate_program_setup`).

Schneidenlage/-laenge und Werkzeugbreite fehlen dagegen: die `Tool`-
Datenklasse (`lathe_easystep/tools.py`) hat aktuell nur
`t, p, d, q, comment, iso_code, iso_size, radius_mm, kind, wear` - kein
Feld fuer Schneidenlaenge oder Werkzeugbreite wird aus der Tooltable
geparst. Das zu ergaenzen erfordert eine verifizierte Zuordnung der
zusaetzlichen `tool.tbl`-Spalten (LinuxCNC-Lathe-Tool-Tabellen nutzen
Spalten wie I/J fuer Frontal-/Rueckwinkel, die je nach Postprozessor/
Konvention unterschiedlich belegt sein koennen) - eine Annahme ohne
verifizierte Referenz waere dasselbe Risiko wie bei geschaetzten DIN-76-
Werten (LES-019). Bleibt offen fuer eine Sitzung mit vorgegebener
Spaltenzuordnung oder einer realen Beispiel-Tooltable als Referenz.

### LES-033 Gewindevorschau

- [ ] symbolische Vorschau durch Geometrie aus Steigung, Tiefe, Start und Ende ersetzen
- [ ] Innen/Aussen und Rechts/Links getrennt pruefen
- [ ] Preset, Vorschau und G76-Ausgabe nachvollziehbar abbilden

### LES-034 Preview-Pipeline

- [ ] Vorschau und G-Code auf denselben geplanten Bewegungen aufbauen,
  einschliesslich Anfahrt, Rueckzug, Werkzeugwechsel und Parken; gemeinsame
  Grundlage mit LES-022 und LES-041 abstimmen
- [ ] dargestellten Werkzeugweg fuer Referenzprogramme gegen die tatsaechliche
  Ausgabe und den LinuxCNC-Backplot vergleichen (siehe LES-030)
- [ ] Werkstueck-Endkontur, Werkzeugweg und Hilfs-/Sicherheitsgeometrie trennen
- [ ] keine impliziten Verbindungen oder Fantasie-Hilfslinien zeichnen
- [ ] im Zweifel weniger statt geometrisch falsche Elemente anzeigen
- [ ] komplexe Endgeometrien in Seiten- und Schnittansicht vergleichen

### LES-035 Embedded/Standalone-Paritaet

- [ ] Widget-Binding, Tooltips, Dialoge und Dateipfade vergleichen
- [ ] keine globalen Host-Widgets im Embedded-Betrieb binden
- [ ] Real-Qt-Smoke-Test fuer beide Startarten pflegen

### LES-042 Legacy TURN/BORE bereinigen

Fund aus der LES-022-Bestandsaufnahme der modalen Codes: `gcode_for_turn()`/
`gcode_for_bore()` (`gcode_program.py`, fuer `OpType.TURN`/`OpType.BORE`)
geben Kuehlmittel direkt als `M8` aus statt ueber den zentralen
`emit_coolant()`-Helfer und schalten es nie mit `M9` wieder ab. Beide
Operationstypen sind aber ueber die UI nicht mehr erstellbar (kein
`tabTurn`/`tabBore` in `ui_registry.TAB_TRANSLATIONS`, abgeloest durch
ABSPANEN mit `side`-Parameter) - noch reachable nur ueber den Dispatcher
in `gcode_for_operation()` und ggf. alte gespeicherte Programme/direkte
Tests.

- [ ] klaeren, ob `OpType.TURN`/`BORE` fuer alte gespeicherte Programme
  noch geladen werden koennen muessen (Migrationspfad noetig?)
- [ ] falls ja: `gcode_for_turn`/`gcode_for_bore` auf `emit_coolant()`
  umstellen (inkl. `M9` beim Operationsende)
- [ ] falls nein: `OpType.TURN`/`BORE`, `gcode_for_turn`/`gcode_for_bore`
  und zugehoerige Dispatcher-/Registry-Eintraege vollstaendig entfernen

### LES-043 Gegenspindel-Checkbox taeuscht Generatorunterstuetzung vor

Nutzerverdacht 2026-09-10 bestaetigt: Die Checkbox "Gegenspindel vorhanden"
(`program_has_subspindle`) und das zugehoerige Feld "max. Drehzahl S3"
(`program_s3`/`s3_max`) werden nirgends im Generator ausgewertet -
`grep -rn "s3_max\|s1_max\|has_subspindle" lathe_easystep/gcode_*.py` liefert
keinen einzigen Treffer. Das Datenmodell kennt keine einzige
Gegenspindel-Operation: `OpType` (`model.py`) hat keinen Eintrag fuer
Werkstueckuebergabe, Abstechen-an-Gegenspindel oder Spindelsynchronisation.
Die einzige Wirkung der Checkbox war bisher, ein Eingabefeld fuer die
S3-Maximaldrehzahl ein-/auszublenden (`update_subspindle_visibility` in
`ui_visibility.py`) - Wert wird gespeichert/geladen, aber weder in einer
Pruefung noch in der G-Code-Ausgabe (auch nicht als Kommentar) je wieder
gelesen. `doc/milestone1_spec.md` beschreibt die Checkbox als "aktiviert
Gegenspindel-Optionen" (Plural) - die tatsaechliche Umsetzung blieb dahinter
zurueck.

Risiko: Ein Bediener, der die Checkbox setzt und eine S3-Grenze eintraegt,
koennte annehmen, das Programm beruecksichtige diese Grenze oder unterstuetze
eine Werkstueckuebergabe/Synchronisation - keins von beidem geschieht. Das
ist keine falsche Fahrwegausgabe (es wird schlicht nichts Gegenspindel-
Spezifisches erzeugt), aber eine irrefuehrende Bedienoberflaeche mit
Sicherheitsbezug.

Sofortmassnahme (umgesetzt 2026-09-10): Checkbox und S3-Feld bleiben
sichtbar (bestehende gespeicherte Programme zeigen ihren Stand weiter
transparent an), werden aber in `update_subspindle_visibility()`
(`ui_visibility.py`) per `setEnabled(False)` gesperrt und erhalten einen
erklaerenden Tooltip. Kein Generatorverhalten geaendert (es gab keins zu
aendern) - nur die irrefuehrende Bedienbarkeit vorerst entfernt. Abgesichert
durch `tests/test_ui_visibility_guards.py::test_subspindle_visibility_uses_checkbox_state_not_label_text`.

- [ ] klaeren, ob eine echte Gegenspindel-Funktion (Werkstueckuebergabe,
  Spindelsynchronisation, S3-Drehzahlpruefung) fuer 0.8.0/0.9.0 vorgesehen
  ist, oder ob Checkbox/S3-Feld und die zugehoerigen Settings-Keys
  ersatzlos entfernt werden sollen
- [ ] falls Umsetzung gewuenscht: Operationstyp(en), Sicherheitspruefungen
  (S3-Grenze, Kollision beider Spindeln) und LinuxCNC-Backplot/Trockenlauf
  vor Freigabe verbindlich klaeren - kein Blindflug bei einer Funktion mit
  zwei gleichzeitig aktiven Spindeln

## Offene externe Antworten und Blocker

Alle bisher gestellten Realtest-Fragen sind beantwortet (Frage 7:
Startzeit >20s, siehe LES-027 - Antwort deutet auf eine Regression hin
und ist noch nicht root-caused). Fragen 16 und 18 wurden vom Nutzer
ausdruecklich ohne reale Testpflicht freigegeben ("das kann mit einem
Testprogramm geregelt werden") und sind durch automatisierte Tests plus
`rs274`-Verifikation bereits erfuellt - deshalb aus der Realtest-Datei
entfernt.

Norm-/Systemabhaengige Blocker:

- DIN-76-Werte fuer M2, M2.5 und M3.5 -> LES-019
- lokale Freistichgeometrie braucht verifizierte DIN-Referenz -> LES-010
- Innen-Schruppen braucht LinuxCNC-Backplot und Trockenlauf -> LES-003
- Generatoraenderungen brauchen LinuxCNC-Simulation -> LES-030

## Verbindlicher Abschluss jeder Generatoraenderung

1. fokussierte Regression, die den alten Fehler reproduziert und mit dem Fix besteht
2. kompletter `python run_tests.py`-Lauf (Stub und Real-Qt getrennt); neue oder geaenderte Skips muessen begruendet werden
3. `python3 regenerate_all_ngc.py`
4. Diff der Referenzprogramme fachlich pruefen
5. echter PyQt5-Test bei UI-, Sichtbarkeits- oder Save/Load-Aenderungen
6. LinuxCNC-Parser und Backplot bei geaenderten Fahrwegen oder Modals
7. bei G2/G3 mindestens ein Fall mit `I != 0`; Start-/Endradius zum
   ausgegebenen Zentrum muessen uebereinstimmen, direkt und in Zyklus-Subs
8. bei Innenbearbeitung steigende/fallende Konturrichtung, Materialgrenze,
   XRI-Verwendung sowie Ein-/Rueckzug getrennt pruefen
9. bei sicherheitsrelevanten Fahrwegen realen Trockenlauf dokumentieren
10. `TODO.md`, `ROADMAP.md`, `README.md`, `DEV.md` und
    `CHANGELOG.md` synchron halten

## Spaetere Erweiterungen nach stabiler 1.0-Basis

- weitergehende Keilnut- und Verzahnungsfunktionen
- weitere Maschinen-, Futter- und Werkzeugprofile
- automatisierte LinuxCNC-Simulationslaeufe
- zusaetzliche Abspanstrategien

WSL-Fortsetzung 2026-09-09: LinuxCNC-Interpreterpruefung erfolgreich fuer
elf Referenzen und 30 Matrixprogramme. Nichtmonotone Boegen vor G71/G72
abweisen; primitive Konturboegen auch beim expliziten Schlichten erhalten.
[Interpreterbericht und Nachweise](doc/linuxcnc_2026-09-09/README.md).

LES-005 Teilabschluss: Innen-Schlichtrueckzug radial vor axial, G40-Abwahl
mit geprueftem Freiraum. 524 Stub-/44 Qt-Tests und 11 Referenzen/30 Matrixfaelle
im Interpreter bestanden. [Details und Grenzen](doc/LES005_INNEN_RUECKZUG_2026-09-09.md).

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
