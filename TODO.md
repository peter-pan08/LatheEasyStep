# TODO LatheEasyStep

Stand: 2026-09-09

Diese Datei ist die verbindliche Liste aller offenen Aufgaben. Erledigte Punkte
werden entfernt und im `CHANGELOG.md` dokumentiert. Release-Ziele und
Abhaengigkeiten stehen in der [ROADMAP.md](ROADMAP.md), reale Tests in
[doc/REALTEST_FRAGEN_2026-07-15.md](doc/REALTEST_FRAGEN_2026-07-15.md).

## Aktuell verifizierte Basis

- Native Nachpruefung von `11ee8b0`: 590/44 Tests und 11+43 rs274-Faelle
  bestanden; Simulations-Programmladen ebenfalls geprueft. Startbefunde und
  verbleibende Grenzen: [nativer Bericht](doc/NATIVE_VERIFICATION_2026-09-09.md).
- Zusaetzlich `Innen_Radius.ngc`/`Innen_Stufe.ngc` (neue Innen-
  Schlichtanfahrt) in der QtDragon-Simulation ueber die Task-NML geladen;
  die geladene Programmquelle bestaetigt den erwarteten Fahrweg. Ein
  gezoomter, kollisionsfrei gepruefter Backplot bleibt an derselben
  Simulationskonfiguration (SUBROUTINE_PATH/HOME) weiterhin offen.

- `main`: Version 0.7.0 als lauffaehige Basis
- `dev`: aktueller Entwicklungsstand fuer 0.8.0; `main` bleibt die stabile Basis
- Teststand: `595 passed` (Stub-Qt) und `44 passed` (echtes PyQt5),
  getrennte Prozesse ueber `python run_tests.py`, keine Skips.
- Elf Referenzprogramme regeneriert; statische NGC-Pruefung bestanden.
  LinuxCNC-Parser: elf Referenzen und 43 Matrixfaelle bestanden;
  grafischer Backplot und Trockenlauf bleiben offen.
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
- [ ] NaN, positive/negative Unendlichkeit, ungueltige Texte und Grenzwerte
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

Damit ist die "Drehzahlen"-Teilmenge des zweiten Punktes oben
geschlossen. "Koordinaten, Vorschuebe, Zustellungen und Sicherheitswerte"
sind weiterhin nicht vollstaendig auf fachlich passende Wertebereiche
durchgegangen (z. B. GROOVE/THREAD ausserhalb der zentralen
`require_positive()`-Liste bei anderen Feldern als Drehzahl) - bleibt
offen.

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

- [ ] `XRI` nur als sichere Einfahr-/Rueckzugsebene verwenden, niemals als
  Schnittbahn; Regression muss jeden G1-Profilwert gegen diese Grenze pruefen
- [x] Schlichtaufmass X/Z fuer Innenkonturen korrekt ausrichten
- [ ] automatisierte Faelle fuer monoton steigende UND fallende Z-Konturen
  sowie Innen-/Aussenbearbeitung pflegen
- [x] `examples.py` um Innen-Abspanen (`Innen_Stufe.ngc`, `side=inside`)
  ergaenzen; automatisiert getestet und regeneriert, reale Abnahme unten offen
- [ ] LinuxCNC-Parser, Backplot und Trockenlauf mit diesem Referenzteil
  dokumentieren (P0 - vor Praxiseinsatz zwingend)

Teilstand: positive vorhandene Bohrung XI bleibt Materialgrenze;
Zylinder, Stufe und Konus jeweils in beiden Konturrichtungen und drei
Bearbeitungsmodi automatisiert getestet (18 Kombinationen). XRI-Grenze,
mehrere Zustellungen und reines Schlichten ohne erneutes Schruppen geprueft.
Innenradius ist seit 09.09. in beiden Richtungen und drei Modi getestet;
Werkzeughuelle, sichere Ein-/Ausfahrt und reale Abnahme bleiben offen.

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

- [ ] zuerst auf nachweislich freien Innendurchmesser fahren
- [x] axial auf Konturstart fahren, bevor der Schnittdurchmesser angefahren wird
- [x] Schneidenradiuskorrektur nur auf ausreichend langem Einfahrweg aktivieren
- [x] Konturstart vorne und hinten getrennt testen
- [x] nach dem Schnitt zuerst radial und danach axial freifahren
- [ ] Innenstufe, Innenkonus und Innenradius als automatisierte Regressionen
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
- [ ] Arc-Intersections im Move-based Roughing vertiefen
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
real verifiziert (siehe oben, Nichtnull-I-Faelle). Der verbleibende
Punkt ist damit eine Praezisions-/Eleganzfrage der Schrupp-Zustellung
(Sehne statt Bogen beim Materialabtrag, durch Schlichtaufmass fachlich
unkritisch), keine Korrektheitsluecke der Endkontur. Echte Bogen-Band-
Schnittmathematik fuer move-based Roughing ist ein mehrstuendiger,
geometrisch fehleranfaelliger Umbau (Teilbogen-Ausgabe mit korrektem I/K
pro Zustellung) und wurde bewusst nicht ad hoc angegangen.
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

- [ ] aktuelle X/Z-Position bei jeder Move-Emission mitfuehren (bisher nur
      fuer Rueckzug/Anfahrt/Werkzeugwechsel in `gcode_safety.py`, siehe
      Teilstand unten - Schnittbewegungen G1/G2/G3 in den Operations-
      Generatoren sind noch nicht erfasst)
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
