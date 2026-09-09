# Changelog

## [Unreleased]

### LES-028/032 Werkzeugdatenvalidierung 2026-09-09

- Explizite Werkzeugorientierung fuer Radiuskorrektur ganzzahlig in 0..9
  pruefen; defekte Werte nicht mehr abschneiden oder still ignorieren.
- Negative Radien, Ueberlauf des Schneidendurchmessers und auf D0 gerundete
  Korrekturwerte blockieren. Fehlende optionale Daten behalten ihr Verhalten.
- Neun Fehlerfaelle reproduziert, elf Regressionen ergaenzt. 589 Stub-/44
  Qt-Tests, 88 statische Checks, elf Referenzen und 43 rs274-Matrixfaelle
  bestanden. Referenzausgabe unveraendert; keine Werkzeughuellenabnahme.

### LES-027 Startzeitmessung 2026-09-09

- Reproduzierbarer Benchmark fuer den isolierten Aufbau mit echtem Qt:
  je fuenf frische Prozesse unter Windows und WSL, Rohdaten gespeichert.
- Neun nachgelagerte Startaufgaben des echten Panels erhalten Begin/Ende-
  Zeitmarken, einschliesslich Werkzeugtabelle und erster Konturvorschau.
- Gemessener UI-Ausschnitt: Median 0.368 s Windows, 1.362 s WSL.
  Kein vollstaendiger Panelstart; Ursache der >20 s bleibt unbekannt.
  Keine Beschleunigung behauptet, keine Generatoraenderung.
- 578 Stub-/44 Qt-Tests bestanden, keine Skips.
  [Messbericht](doc/STARTUP_2026-09-09.md).

### LES-040/028 Einstich-Ausgabegrenzen 2026-09-09

- Positive Vorschuebe/Zustellungen duerfen bei der o220-Ausgabe nicht
  auf null runden. Breiten-/Ueberdeckungspruefung verwendet gerundete
  Makrowerte; Start und Ende muessen unterscheidbar bleiben.
- Spanbruchanzahl wird ganzzahlig und nichtnegativ validiert statt gerundet.
- Fuenf Fehlerfaelle vor Korrektur reproduziert. 578 Stub-/44 Qt-Tests,
  elf Referenzen und 43 LinuxCNC-Matrixfaelle sowie 88 statische Checks bestanden.
  Referenzprogramme unveraendert; keine Maschinenabnahme.
- Bestehende harte Keilnut-Generatorsperre als verbleibende Funktionsluecke
  dokumentiert; in diesem Schritt nicht aufgehoben.

### LES-037 und Operationsfolgen: Matrix erweitert 2026-09-09

- Vier automatische M12-Gewindefreistichprogramme (innen/aussen,
  rechts/links) und zwei CSS-Schruppen-/Schlichten-Folgen mit identischem
  Werkzeug in gemeinsame Regression-/Interpreterfaelle aufgenommen.
- Fehlender Platz erhaelt bestehende Exportdateien; Konturverlaengerung
  verschiebt weder Freistichboegen noch Gewindeende. Kein Generatorfix
  fuer diese Faelle erforderlich.
- 573 Stub-/44 Qt-Tests, keine Skips; 88 statische Checks und 43
  Matrixprogramme im echten rs274 bestanden. Elf Referenzen unveraendert.
- WSLg/AXIS verfuegbar, verborgener GUI-Test erfolgreich. Grafischer
  Backplot und reale Maschinenabnahme wurden damit nicht durchgefuehrt.
  [Nachweise und Grenzen](doc/linuxcnc_2026-09-09/README.md).

### Review und Fortsetzung nach Unterbrechung 2026-09-09

- Zwischenstand mit 559 Stub-/44 Qt-Tests geprueft und weitgehend behalten.
- LES-018: `prefer_explicit` verhindert jetzt auch beim separaten Schlichten
  eine automatische G70-Wiederverwendung; auto/G70 bleibt erhalten.
- LES-028/040: G76 Q darf nach Ausgaberundung nicht 90 erreichen;
  CSS-Schnittgeschwindigkeit und Startdurchmesser duerfen nicht auf null runden.
  Vier zuvor fehlschlagende Regressionen sichern die Korrekturen ab.
- Fuenf CSS-Faelle und zwei G70-/explizite Schlichtfolgen in die
  reproduzierbare LinuxCNC-Matrix aufgenommen: elf Referenzen und
  37 Matrixfaelle bestanden. 563 Stub-/44 Qt-Tests, 88 statische Checks.
- Zu weitgehende LES-013-Abschlussaussage korrigiert: stock_x entspricht
  nicht jedem Passdurchmesser; explizite Freifahrten und zyklusinterne
  Bewegungen sind getrennt zu bewerten. Backplot/Maschinenabnahme offen.
  [Review und Interpreter-Nachweise](doc/linuxcnc_2026-09-09/README.md).

### Dokumentations-Nachtrag 2026-09-09 (LES-012/027/037)

- LES-012: `Kontur_Radius_Fase.ngc` (`G3 ... I-3.000`) und die daraus
  abgeleiteten Matrixfaelle sind Teil der bei jeder Sitzung gegen echten
  rs274 verifizierten Referenzen - der Nichtnull-I-Parser-Punkt ist damit
  abgedeckt (Backplot grafisch weiterhin offen).
- LES-027: neues `measure_startup.py` misst Shell-UI, acht Teil-UIs,
  Zusatzwidgets und statische Uebersetzungsstruktur separat, mit
  Handler-Instrumentierung fuer die neun nachgelagerten Startaufgaben. Die
  gemeldeten >20s liessen sich unter Windows (0.587s) und WSL/Debian
  (1.565s) NICHT reproduzieren - kein Root Cause, keine unbelegte
  Optimierung. Siehe [doc/STARTUP_2026-09-09.md](doc/STARTUP_2026-09-09.md).
- LES-037: neue automatisierte Matrix (`test_thread_relief_matrix.py`)
  beweist die Kernaussage - eine Konturverlaengerung hinter dem Gewinde
  verschiebt den Freistich nicht - fuer Aussen/Innen x Rechts/Links, alle
  vier real gegen rs274 verifiziert. Reale Backplot-/Trockenlauf-Abnahme
  bleibt der einzige noch offene Punkt.

### LES-028 G76-Zustellwinkel begrenzt 2026-09-09

- `infeed_q` (G76-Zustellwinkel `Q`) floss bisher vollstaendig ungeprueft
  in die Ausgabe ein - ein negativer oder unplausibel grosser Wert
  (>=90 Grad) waere unveraendert als `Q`-Wort ausgegeben worden. Jetzt auf
  den physikalisch gueltigen Bereich 0..<90 Grad geprueft (0 = radiale
  Zustellung, z. B. Quadratgewinde, bleibt explizit gueltig).
- "G7-Massystem nicht erneut als offenen Fachfehler behandeln": keine
  verbleibende Stelle gefunden, die das bereits per Realtest bestaetigte
  G76-Massystem noch als offen fuehrt - kein Codegap.
- Bewusst nicht umgesetzt: "Werkzeugwechsel nur aus normalisiertem
  Werkzeugdatensatz erzeugen" und "Preset-/manuelle Werte nachvollziehbar
  vergleichen" sind im TODO nicht praezise genug spezifiziert fuer eine
  sichere Entscheidung, ohne moeglicherweise viele bestehende Testfixtures
  oder reale Programme ohne vollstaendig gepflegte Werkzeugtabelle zu
  brechen (aehnliches Risiko wie beim Drehzahl-Fund in LES-040) - bleibt
  offen fuer eine Sitzung mit Klaerung der genauen Anforderung.
- Unter WSL/Debian mit echtem rs274 verifiziert, keine Ausgabeaenderung.
  559 Stub-Tests, 44 Real-Qt-Tests, keine Skips.

### LES-018 G70-Wiederverwendung fuer separaten Schlichtstep 2026-09-09

- Ein reiner Schlichtstep (eigene Operation, typischerweise eigenes
  Werkzeug) nutzt jetzt `G70 Q<sub>`, um den Kontur-Sub eines frueheren,
  separaten Schruppschritts wiederzuverwenden, statt die Fertigkontur
  nochmal explizit als G1/G2/G3-Liste auszugeben - aber nur, wenn dieser
  exakte Sub nachweislich per G71/G72 zyklisch definiert wurde (neue
  `_cycle_defined_subs`-Zustandsverfolgung) und keine Werkzeugradius-
  korrektur noetig ist.
- Fallback auf den bestehenden expliziten Schlichtweg bleibt fuer alle
  anderen Faelle unveraendert (keine benannte Kontur, kein vorheriger
  Zyklus, Innenbearbeitung - nutzt G71/G72 ohnehin nie -, Werkzeug-
  korrektur). Reiner Schlichtstep schruppt dabei nie erneut: G70 fuehrt
  ausschliesslich den bereits vorhandenen Fertigkontur-Sub aus.
- Real mit einem separaten Zwei-Werkzeug-Rough/Finish-Programm gegen
  echten rs274 verifiziert: der Schlichtschritt fuehrt nur die zwei
  tatsaechlichen Konturbewegungen aus, keine erneute Schruppbewegung,
  keine zweite Subroutine-Definition.
- Alle 11 Referenzen und 30 Matrixfaelle bestehen unveraendert (keine
  nutzt den neuen Pfad). 555 Stub-Tests, 44 Real-Qt-Tests, keine Skips.

### LES-013 CSS-Aktivierungsposition verifiziert 2026-09-09

- Codepruefung: jeder Aufrufer von `append_tool_and_spindle()` mit CSS-
  Parametern (`gcode_face.py`, `gcode_roughing.py` - Schrupp-Zyklus,
  Move-based-Schruppen je Pass, separater Hinterschnitt, Schlichtschnitt,
  `gcode_thread.py`, `gcode_groove.py`) uebergibt als `css_start_diameter`
  konsistent den Durchmesser, an dem `emit_approach()` unmittelbar danach
  tatsaechlich ankommt, bevor G96 aktiviert wird - keine Diskrepanz
  gefunden. Move-based-Schruppen aktiviert/suspendiert CSS sogar je Pass.
- Modalsequenz frisch gegen echten rs274 verifiziert (kanonische
  `SET_SPINDLE_MODE`/`SET_SPINDLE_SPEED`-Ausgabe eines CSS-Wechsel-
  Programms geprueft).
- Kein Codegap gefunden, keine Aenderung noetig - alle offenen
  Checklistenpunkte in TODO.md abgehakt. Grafischer Backplot und reale
  Maschinenabnahme bleiben separate, unveraenderte Grenzen (LES-030).

### LES-031 Redundante Nullbewegungen entfernt 2026-09-09

- `gcode_drill.py` gab nach jedem Bohrzyklus unbedingt ein `G0 Z<safe_z>`
  aus. Empirisch gegen echten `rs274` verifiziert: LinuxCNC-Zyklen kehren
  im Default-Modus G99 auf die Rueckzugsebene R zurueck, nicht auf die
  Z-Position vor dem Zyklus - da `retract` ohne Angabe auf `safe_z`
  faellt, stand das Werkzeug nach `G80` im Standardfall bereits auf
  `safe_z`. Die zusaetzliche Bewegung wird jetzt nur noch ausgegeben, wenn
  `retract` explizit hoeher als `safe_z` gesetzt ist (dann echt noetig).
- `append_tool_and_spindle()` gab vor jedem Werkzeugwechsel unbedingt
  einen Rueckzug auf die Aussen-Sicherheitsposition aus, auch wenn die
  vorherige Operation dort bereits exakt stand. Eng begrenzte
  Zustandsverfolgung (`_safe_x`/`_safe_z`, nur an Stellen gesetzt, wo die
  Position unmittelbar zuvor sicher bekannt ist) erkennt und ueberspringt
  diesen Fall jetzt.
- Bewusst nicht angefasst: eine dritte Redundanz in den Innen-Schrupp-
  zyklen (`rough_turn_parallel_x/z`) - ein Fix dafuer bräuchte echte
  zentrale Positionsverfolgung (LES-022), sonst Risiko veralteten, im
  `rough_finish`-Kombimodus falsch als sicher angenommenen Zustands.
- Unter WSL/Debian mit echtem rs274 verifiziert (11 Referenzen, 30
  Matrixfaelle). 553 Stub-Tests, 44 Real-Qt-Tests, keine Skips.

### LES-001 Warnung und Fahrweg abgeglichen 2026-09-09

- `get_approach_warnings()` meldete "Rueckzugsebene schneidet den
  Futterbereich" bisher allein anhand des Z-Grenzwerts der Futter-
  Sperrzone, ohne wie `validate_chuck_segment()` auch das X-Intervall zu
  pruefen. Eine sichere Position mit X ausserhalb der Sperrzone wurde
  dadurch faelschlich als gefaehrdet gemeldet, obwohl der tatsaechliche,
  bereits abgesicherte Fahrweg dort nie hinfuehrt - Warnungstext und
  echtes Verhalten widersprachen sich. Beide pruefen jetzt dieselbe
  Bedingung.
- Damit ist LES-001 vollstaendig durchgegangen bis auf die bewusst nicht
  umgesetzte "dynamische" Achsreihenfolge-Wahl je Eilgang: das wuerde den
  Projektzielen (deterministische, nachvollziehbare Bewegungen)
  zuwiderlaufen und ist auch im ausgewerteten Inventor-Post (LES-006)
  nicht vorgesehen - der nutzt ebenfalls eine feste, global konfigurierte
  Reihenfolge statt einer Fall-zu-Fall-Entscheidung.
- Unter WSL/Debian mit echtem rs274 verifiziert (11 Referenzen, 30
  Matrixfaelle), keine Ausgabeaenderung. 550 Stub-Tests, 44 Real-Qt-Tests,
  keine Skips.

### LES-006 Inventor-Post als Referenz ausgewertet 2026-09-09

- `doc/linuxcnc turning.cps` (Autodesk generischer LinuxCNC-Drehpost)
  ausgewertet: der Post hat keine Matrix je Operationstyp - Rueckzugs- und
  Anfahrreihenfolge sind je eine globale Post-Eigenschaft fuer das gesamte
  Programm, unabhaengig vom Operationstyp. Unser Generator unterscheidet
  bereits feiner (Bohren/Gewinde Z-vor-X, Einstich/Keilnut X-vor-Z).
- Gepruefter, bewusst nicht umgesetzter Vorschlag: Rueckzug bei
  unbekanntem Ausgangszustand auf eine feste G53-Maschinenposition
  umstellen (wie in der Referenz). Geometrisch widerlegt: ein fester
  Punkt macht eine Diagonalbewegung von unbekannter Startposition nicht
  automatisch kollisionsfrei (Gegenbeispiel dokumentiert in TODO.md) und
  entzieht sich vollstaendig der LES-001-Segmentpruefung. Keine
  Codeaenderung; Ergebnis in TODO.md/DEV.md festgehalten.

### LES-040 Spindel-Start darf nicht stillschweigend ausbleiben 2026-09-09

- `append_tool_and_spindle()` - die zentrale Funktion, die fuer JEDE
  Operation (Abspanen, Einstich, Bohren, Gewinde, Planen) die Drehzahl
  ausgibt - schluckte `spindle=0`, negative Werte, fehlende Werte sowie
  eine auf 0 U/min gerundete positive Drehzahl bisher vollstaendig
  stillschweigend: kein Fehler, kein `M3`/`S..` irgendwo im Programm. Real
  reproduziert: eine komplette Abspanen-Operation mit `spindle=0` erzeugte
  ein vollstaendig "gueltiges" Programm, in dem die Spindel nie gestartet
  wird.
- Blockiert jetzt die Ausgabe, mit einer bewussten Ausnahme fuer die reine
  Werkzeugwechsel-Positionierung (`require_spindle=False` an den zwei
  Stellen in `gcode_program.py`, deren Aufgabe nur das Anfahren des
  Wechselpunkts ist - die eigentliche Drehzahl inkl. CSS setzt danach
  immer der jeweilige Operations-Generator selbst).
- Aendert 22 Testfixtures quer durchs Projekt (Innenkontur-Matrix,
  Subroutinen, Rueckzugslogik, CSS, Parting), die bisher nie eine
  Drehzahl gesetzt hatten, um eine sinnvolle Drehzahl - keine Aufweichung
  der neuen Pruefung.
- Unter WSL/Debian mit echtem rs274 verifiziert (11 Referenzen, 30
  Matrixfaelle), keine Ausgabeaenderung fuer bestehende Programme. 549
  Stub-Tests, 44 Real-Qt-Tests, keine Skips. "Koordinaten, Vorschuebe,
  Zustellungen und Sicherheitswerte" ausserhalb der Drehzahl sind weiterhin
  nicht vollstaendig auf fachlich passende Wertebereiche durchgegangen.

### LES-039 M1 vor dem ersten Werkzeugwechsel 2026-09-09

- `optional_stop_toolchange` ("Fuegt vor JEDEM Werkzeugwechsel ein
  optionales M1 ein") schloss den allerersten Werkzeugwechsel bisher
  stillschweigend aus - genau dort, wo Werkzeug und Ausgangsposition am
  wenigsten bekannt sind, weil keine vorherige Operation existiert. M1
  gilt jetzt fuer jeden Werkzeugwechsel einschliesslich des ersten.
- M1 steht jetzt VOR der angenommenen sicheren Z-vor-X-Rueckzugsbewegung,
  nicht mehr danach - der Bediener kann den tatsaechlichen Maschinen-
  zustand pruefen, bevor irgendeine Bewegung ausgefuehrt wird.
- Das ist eine prozedurale Absicherung fuer LES-039 ("unbekannten Zustand
  nicht als sicher annehmen"), keine geometrische: die pauschale
  Z-vor-X-Reihenfolge bei unbekanntem Ausgangszustand bleibt bestehen, da
  eine Textgenerierung den realen Maschinenzustand nicht kennen kann.
- Unter WSL/Debian mit echtem rs274 verifiziert (11 Referenzen, 30
  Matrixfaelle, Sonderfall mit M1 vor dem ersten Wechsel), keine
  Ausgabeaenderung fuer bestehende Programme. 543 Stub-Tests, 44
  Real-Qt-Tests, keine Skips.

### LES-001 Zweiter Rueckzugsschritt gegen Rohteil/Futterzone 2026-09-09

- Der zweite Teilschritt jeder Rueckzugsreihenfolge (die zuerst erreichte
  sichere Achse bleibt dabei konstant, nur die andere Achse bewegt sich)
  wird jetzt in `emit_safe_retract_for_op()` (Einstich/Keilnut, Bohren/
  Gewinde, X-vor-Z-Fallback bei Start im Rohteil/in der Futterzone) UND in
  `emit_approach()` (Aussen-Modus) gegen Futter-Sperrzone und - ausser im
  Innen-Modus, der eine Bohrung nicht als Rechteck abbilden kann - gegen
  die Rohteil-Huellkurve geprueft. Der erste Teilschritt (Flucht aus der
  aktuellen Position) bleibt bewusst ungeprueft, da er dort legitim
  beginnen darf.
- Dabei einen echten, bis dahin unentdeckten Fall gefunden und behoben:
  ein bestehender Test konfigurierte eine "sichere" XRA=60, die selbst noch
  innerhalb der Futter-Sperrzone (X20..80) lag - der zweite Rueckzugsschritt
  haette die gesamte restliche Z-Strecke ungeprueft mitten durch die Sperr-
  zone gefuehrt. Testfixture auf eine tatsaechlich sichere XRA=90 korrigiert.
- Unter WSL/Debian mit echtem rs274 verifiziert: alle 11 Referenzen und
  30 Matrixfaelle bis PROGRAM_END bestanden, keine Ausgabeaenderung.
  542 Stub-Tests, 44 Real-Qt-Tests, keine Skips. Die eigentliche
  Achsreihenfolge-Entscheidung nach Rohteil-/Futterzone (LES-001,
  Kernpunkt: Reihenfolge dynamisch statt fest je Operationstyp) bleibt
  offen - fixe Konventionen, die im Einzelfall nicht sicher sind, werden
  jetzt aber blockiert statt stillschweigend ausgefuehrt.

### LES-001 Achsreihenfolge und Werkzeugwechsel-Regressionen 2026-09-09

- Regressionstest fixiert die op-spezifische Rueckzugs-Achsreihenfolge:
  Einstich/Keilnut zieht X vor Z zurueck, Bohren/Gewinde immer Z vor X -
  unabhaengig vom Startpunkt, damit ein im Einstich/Gewindegang stehendes
  Werkzeug nicht zuerst radial bewegt wird.
- Aussen- UND Innen-Schruppen->Schlichten mit identischem Werkzeug erzeugen
  nachweislich nur einen Werkzeugwechsel; die Anfahrt der zweiten Operation
  lief in beiden Faellen fehlerfrei durch (bei Innenarbeit bleibt die
  sichere Position innerhalb der bereits gebohrten/hohlen Zone - kein neuer
  Fehler gefunden, bestehendes Verhalten jetzt regressionsgesichert).
- 539 Stub-Tests, 44 Real-Qt-Tests, keine Skips; Referenzprogramme
  unveraendert. Die eigentliche Achsreihenfolge-Entscheidung nach Rohteil-/
  Futterzone (LES-001, Kernpunkt) und der Abgleich Warnung/tatsaechlicher
  Fahrweg bleiben offen.

### LES-001 Diagonal-Eilgaenge gegen Rohteil 2026-09-09

- `validate_stock_segment()` prueft reine Diagonal-Eilgaenge (`G0 X.. Z..`
  in einer Zeile) gegen die Rohteil-Huellkurve als vollstaendiges Rechteck -
  auch wenn Start- und Zielpunkt jeweils fuer sich ausserhalb liegen, die
  Strecke dazwischen aber mitten durchs Rohteil fuehrt. Betrifft den
  Diagonal-Rueckzug in `emit_safe_retract_for_op` und die Anfahrt der
  Werkzeugwechselposition in `move_to_toolchange_pos`.
- Bewusst ausgenommen: die achsweise Anfahrt-/Rueckzugsfolge in
  `emit_approach` (dort landet der Zielpunkt bei Folgeoperationen wie
  Schlichten nach Schruppen absichtlich innerhalb der Rohteil-Huellkurve)
  sowie jede Sicherheitsposition im Innen-Modus - die Huellkurve ist ein
  reines Aussenmass-Rechteck und kann eine Bohrung nicht abbilden.
- Regressionsfaelle fuer Rohteil-Diagonalkreuzung ergaenzt, analog zur
  bestehenden Futter-Sperrzonen-Pruefung. 533 Stub-Tests, 44 Real-Qt-Tests,
  keine Skips; Referenzprogramme unveraendert (reine Zusatzpruefung ohne
  Ausgabeaenderung). Die eigentliche "sichere Achsreihenfolge je nach
  Rohteil-/Futterzone" (LES-001, erster Punkt) bleibt offen.

### LES-005 Innen-Schlichtrueckzug 2026-09-09

- Innen-Schlichten zieht zuerst radial nach XRI und erst danach axial nach
  ZRI zurueck. Programmierte Segmente werden gegen Futter-Sperrzonen geprueft.
- Bei aktiver Radiuskorrektur G40 vor der radialen G1-Freifahrt; physischer
  Weg im G7-Masssystem nach Ausgaberundung muss laenger als der Schneiden-
  durchmesser sein. Bei zu wenig Freiraum wird die Ausgabe blockiert.
- Richtungs-, Korrektur- und Rundungsregressionen ergaenzt. Vier weitere
  LinuxCNC-Matrixfaelle mit Radiuskorrektur an Innenzylinder/-konus.
- 524 Stub-Tests, 44 Qt-Tests, 88 statische Checks; elf Referenzen und
  30 Matrixprogramme im echten Interpreter bestanden. Werkzeughuellen,
  weitere kompensierte Konturformen und reale Abnahme bleiben offen.
  [Pruefbericht](doc/LES005_INNEN_RUECKZUG_2026-09-09.md).

### WSL-/LinuxCNC-Fortsetzung 2026-09-09

- Echter rs274-Lauf deckt nichtmonotonen Bogen in `Kontur_Radius_Fase` auf.
  G71/G72-Pruefung beruecksichtigt jetzt analytische Bogenextrema und weist
  solche Konturen ab; urspruenglicher Fehler fuer beide Achsstrategien getestet.
- Positives Referenzbeispiel auf monotonen Viertelkreis umgestellt; Nutzer-
  konturen werden nicht automatisch veraendert. Expliziter Schlichtweg erhaelt
  jetzt auch bei rein primitiven Konturen G2/G3 statt gerader Verbindungen.
- Elf Referenzen und 26 Matrixprogramme bestehen LinuxCNC 2.10.0~pre1 unter
  WSL/Debian bis PROGRAM_END. Kanonische Ausgaben und SHA256-Manifeste
  archiviert; Matrixgenerator und Report-/Eingabeordneroptionen hinzugefuegt.
- 516 Stub-Tests, 44 Real-Qt-Tests, keine Skips; 88 statische NGC-Checks.
  Grafischer Backplot, Trockenlauf und verbleibende Sicherheitsaufgaben offen.
  [Interpreterbericht](doc/linuxcnc_2026-09-09/README.md).

### Fortsetzung 2026-09-09 (LinuxCNC-Abnahme offen)

- LES-013: gesicherten CSS-Zwischenstand geprueft; veraltete vorbereitete
  Aktivierung beim G97-Fallback entfernt, Maximaldrehzahl ohne Ueberschreitung
  durch Ganzzahlrundung. Gemischtes CSS/G97/CSS-Referenzprogramm und echter
  Qt-Programmdatei-/Formular-Roundtrip ergaenzt.
- LES-040/028: Bohrmodi werden nicht mehr still zu G81 umgedeutet;
  endliche Bohrwerte, positive ausgegebene Vorschuebe/Zustelltiefen und
  nichtnegative Verweilzeiten vor Bewegungsplanung geprueft. Zahlenleser
  ersetzen defekte explizite Werte nicht durch andere Aliase oder Defaults.
  Fehler beim G-Code-Export erhalten bestehende Dateien.
- LES-003/012/015: Innenradius in beiden Konturrichtungen und drei Modi,
  Schnittgrenzen und erhaltene Boegen getestet. Ausgabe von Schlichtweg und
  Kontur-Subroutine sowie G7-Bogenradien verglichen.
- Elf Referenzen regeneriert; neu `CSS_Wechsel.ngc` und `Innen_Radius.ngc`.
  Die bisherigen neun Dateien bleiben unveraendert. 513 Stub-Tests,
  44 Real-Qt-Tests und 88 statische NGC-Checks bestanden, keine Skips.
- Testabhaengigkeiten festgehalten und veraltete README-Einschraenkungen
  korrigiert. WSL und rs274 fehlen auf diesem Rechner; offene P0-Punkte,
  komplette CSS-Modalsequenz und reale Abnahmen bleiben offen.
  [Verifikationsbericht](doc/VERIFICATION_2026-09-09.md).

### Lokale Umsetzung 2026-09-08 (noch keine Maschinenabnahme)

- LES-041 abgeschlossen: Generierung auf tief kopiertem Programmsnapshot;
  Konturen/Freistiche frisch aufloesen, keine alten Ableitungen wiederverwenden.
  Fehlende oder doppelte Konturnamen und unbekannte Operationen brechen ab.
- LES-042 abgeschlossen: Programm-JSON ueber temporaere Datei und atomaren
  Ersatz schreiben; bei Fehler bleiben Datei und bisheriger Programmpfad erhalten.
- LES-043 abgeschlossen: Step-Dateien ebenfalls atomar, Verknuepfung erst
  nach erfolgreichem Schreiben; Teilfehler melden bereits gespeicherte Steps,
  ungespeicherte/verknuepfungslose Steps bleiben dirty.
- LES-038 abgeschlossen: Stub-/Real-Qt in getrennten Prozessen, gemeinsamer
  `run_tests.py`; 472 Stub-Tests und 43 echte Qt-Tests bestanden, keine Skips.
- LES-023 abgeschlossen: automatische Kommentare ohne gespeicherte Nummer;
  manuelle Kommentare bleiben erhalten. Konturen zaehlen in der Step-Liste
  als Geometrieschritte mit, erzeugen aber keine eigene Bearbeitung.
- LES-011 abgeschlossen: gemeinsame Freistich-Primitive fuer Vorschau,
  Kontur-Sub und explizites Schlichten auf identische Ausgabe getestet;
  Segment-Features ueberstehen Save/Load.
- LES-016 abgeschlossen: Freistichnorm nur bei Vorschlagsmodus sichtbar;
  alte IDs normalisiert, beide Zweige und Sprach-/Save-/Load-Wechsel mit
  echtem Qt geprueft. Kontur-Kantenfelder bleiben sichtbar/deaktivierbar;
  Innen/Aussen bekommt ohne fachlichen Bedarf keine zusaetzliche Ausblendung.
- LES-001/039 teilweise: gemeinsame Anfahrt achsweise; Futter-Sperrzone
  blockiert Ziel- und Segmentverletzungen. XT/ZT auch bei Einzelwerkzeug
  zwingend. Unbekannte Startposition und vollstaendige Kollisionsplanung offen.
- LES-040/028 teilweise: endliche Zahlen an Daten-/Geometriegrenzen,
  ganzzahlige Werkzeugnummern und G76-Eingaben; defekte Pfadpunkte abweisen.
  Ungueltige Gewindesteigung wird nicht mehr still ersetzt, H=0 bleibt H=0.
- LES-003/015 teilweise: vorhandenes XI als Bohrungsgrenze erhalten,
  Innenaufmass richtig ausrichten; 18 Profil-/Richtungs-/Moduskombinationen.
- LES-036 implementiert: Planradius aus gemeinsamen Geometrieprimitiven,
  G2 mit radialem I im Durchmessermodus, G91.1 im Programmkopf;
  analytische Bogen- und echte Qt-Roundtrip-Tests. LinuxCNC-Abnahme offen.
- LES-020 teilweise: Kopf-, Kontur-, Gewinde-Preset- und Tooltip-Funktionen
  aus Handler in eigene Module extrahiert; Widget-Bootstrapping bleibt offen.
- Neun NGC-Referenzen regeneriert, darunter Innenstufe, mittiger Freistich
  und Planradius; statischer Validator korrigiert, rs274-Batchpruefung
  vorbereitet. Fuer diesen Stand keine reale Parser-/Backplot-Verifikation.

- Fix: Die neue sichere Innenanfahrt in `emit_approach()` (axial auf XRI,
  erst danach radial zustellen, kein diagonaler Schnellgang durch die
  Bohrung) erzeugte einen bedeutungslosen zusaetzlichen `G0 Z...` auf
  denselben Z-Wert, sobald der Konturstart bereits auf der sicheren
  Z-Ebene lag (haeufiger Fall, z. B. bei einem reinen Innen-Schlichtstep).
  Die Zeile wird jetzt nur noch ausgegeben, wenn sich der Z-Wert tatsaechlich
  aendert. Verifiziert mit `rs274` (keine Diagonalbewegung, keine
  Nullbewegung) und gegen den alten Code per manuellem Revert bestaetigt
  fehlgeschlagen; `tests/test_parting_slice.py::test_internal_finish_with_nose_comp_gets_nonzero_entry_move`
  auf die korrigierte Sequenz umgestellt
- Fix: Die axiale Lage der 30°-Flanke wurde faelschlich von Innen/Aussen
  abgeleitet. Sie folgt jetzt ausschliesslich der Gewinderichtung: Die Flanke
  liegt immer an der Seite, an der das Gewinde in den Freistich einlaeuft.
  Das gilt fuer Aussen- und Innengewinde sowie Rechts- und Linksgewinde.
- Gewinde: Der Reiter hat jetzt die getrennten Eingaben "Gewinde-Vorlauf"
  und "Gewinde-Auslauf". Sie erzeugen einen G76-Taper vor bzw. nach dem
  programmierten Gewinde und werden in der Vorschau als schräge An-/Ausläufe
  dargestellt. LinuxCNC G76 kann technisch nur eine gemeinsame E-Laenge:
  ein einzelner Wert wird mit `L1` oder `L2` ausgegeben, zwei gleiche Werte
  mit `L3`; zwei unterschiedliche Werte brechen mit einer klaren Meldung ab,
  statt einen falschen Taper zu erzeugen.
- Fix (P0): Ein Innen-Freistich mit dynamischer Werkzeugradiuskorrektur
  `G41.1` fuehrte LinuxCNC an der konkaven Schulter zu einem Interpreterabbruch
  ("Straight feed in concave corner ..."). Der nachfolgende Innen-G76-Zyklus
  wurde dadurch nie erreicht und erschien weder im Backplot noch beim Lauf.
  Bei integrierten Innenfreistichen wird diese fuer die Form unzulaessige
  Kompensation jetzt gezielt deaktiviert; der Kontur- und Gewindeschritt wird
  vollstaendig verarbeitet.
- Freistich (P0): Automatische DIN-76-Freistiche fuer Aussen- und
  Innengewinde werden nicht mehr als rechteckige Tasche erzeugt. Die Kontur
  besteht jetzt aus Ein-/Auslaufflanken, tangentialen G2/G3-Boegen und dem
  Freistichgrund; dieselbe Primitive-Geometrie wird fuer Schlichten,
  Kontur-Subroutine und Vorschau verwendet.
- Korrektur Freistichprofil: `g1` und `g2` werden jetzt entsprechend der
  DIN-Skizze von der Schulter aus ausgewertet. Die Form ist asymmetrisch:
  eine 30°-Flanke auf der Gewindeseite, gerader Grund, Schulterradius und
  radiale Schulter. Die vorherige beidseitig schraege Trapezform war keine
  DIN-76-Form.
- Presets: Die automatische DIN-76-1-Auswahl verwendet jetzt je Gewindeseite
  die Tabellenmasse `dg`, `g1`, `g2`, Kurzform und `r`. Die frueher
  geschaetzten Tiefen und die fuer Innengewinde faelschlich wiederverwendeten
  Aussenwerte sind entfernt. M30x3,5 hat damit aussen `dg=d-5`, innen
  `dg=D+0,5`; M12 innen verwendet Form C/D mit `g2=9,1 mm`.
- Vorschau: Automatische Gewindefreistiche werden als Bauteilgeometrie aller
  verknuepften Aussen-/Innenkonturen dargestellt, auch wenn gerade der
  Gewinde-Step oder ein anderer Reiter aktiv ist. Die Anzeige haengt nicht
  mehr von der Auswahl eines Abspanen-Steps ab.
- Verifikation: `doc/Test_Dateien/test.ngc` aus `Test.lse` neu erzeugt;
  LinuxCNC `rs274 -g` akzeptiert die neuen Freistichboegen bis `M30`.
- Innenbearbeitung: Move-based-Innen-Schruppen vermeidet jetzt diagonale
  Schnellgaenge innerhalb der Bohrung und redundante Safe-Moves. Jeder Pass
  faehrt axial ausschliesslich auf `XRI`, stellt erst dort auf den
  Schnittdurchmesser zu und zieht danach nur radial auf `XRI` zurueck.
- Innen-Schlichten und Innengewinde verwenden fuer die Einfahrt ebenfalls
  immer `Z` auf der freien `XRI`-Ebene, danach `X`; der bisherige direkte
  diagonale Schnellgang vom Rueckzugspunkt in die Kontur ist entfernt.
- Referenzprogramm: Das M12-Innengewinde nutzt jetzt ebenfalls den
  automatischen DIN-76-Freistich; der Innen-Schlichtstep verarbeitet ihn
  vollstaendig statt ihn zu ignorieren.
- Fix (P0): Ein Generatorfehler wurde bisher still in ein dreizeiliges
  Fallback-Programm umgesetzt und anschliessend als erfolgreicher Export
  gemeldet. Fehler werden jetzt an die UI weitergegeben; die NC-Datei wird
  nur nach einer vollstaendigen Erzeugung atomar ersetzt. Eine vorhandene
  Programmdatei bleibt bei einem Fehlschlag unveraendert.
- Freistich: Reicht die lange DIN-76-Form bis zur folgenden Kontur-Schulter
  nicht aus, waehlt der Generator jetzt die hinterlegte Kurzform nur dann,
  wenn sie vollstaendig in die zylindrische Gewindestrecke passt; anderenfalls
  bleibt der sichere Generierungsabbruch bestehen. Das Referenzprogramm
  verwendet fuer das M30-Gewinde damit die Kurzform von `Z=-25,3` bis `-34,3`
  statt eines alten manuellen Freistichs bei `Z=-35`.
- Fix: Beim Ausblenden eines Freistichs fuer G71/G72 werden die getrennten
  zylindrischen Teilsegmente wieder zu einer Schruppkontur zusammengefasst.
  LinuxCNC erhaelt damit keine nicht schneidbare Parallel-Linienfolge mehr
  (`G7X error: Cannot intersect parallel lines`).
- Fix (P0): Abspanen verwendet fuer Konturen mit Freistich keine ungeeignete
  globale Fertigkontur mehr als `G71/G72`-Subroutine. Relief-freie
  Schruppvarianten erhalten eine eigene Subroutine; bei "voll in Kontur" wird
  wegen der axial nichtmonotonen U-Geometrie sicher auf Move-based-Ausgabe
  gewechselt. Damit entsteht kein LinuxCNC-Fehler `G7X error: Not monotonic`.
- Verifikation: `doc/Test_Dateien/test.ngc` aus `Test.lse` regeneriert und mit
  `/home/adm1n/linuxcnc/configs/Drehbank/tool.tbl` ueber den lokalen
  LinuxCNC-Interpreter `rs274 -g` vollstaendig bis `M30` geparst.
- Freistich (LES-037): Ein aktivierter DIN-76-Gewindefreistich wird jetzt aus
  Gewindeende, Hand, Durchmesser und der normierten Ueberdeckung `f`
  abgeleitet. Er wird nur in eine passende zylindrische Aussen-/Innenkontur
  eingespleisst und dadurch identisch in Vorschau, Kontur-Subroutine,
  Schruppen und Schlichten verwendet. Fehlt die Konturstrecke, bricht die
  G-Code-Erzeugung ab statt einen Freistich am Konturende oder im Vollmaterial
  zu erzeugen. Regressionen decken Aussen- und Innengeometrie sowie den
  sicheren Abbruch ab.
- Docs: README und DEV-Dokumentation beschreiben die verbindliche
  Gewinde-zu-Kontur-Zuordnung; der Realtest-Fragenkatalog enthaelt die
  LinuxCNC-Abnahme fuer automatischen Aussen- und Innenfreistich.
- Presets: DIN-76-1-Regelgewinde bis M30 enthalten jetzt Steigung, Freistichbreite fuer Aussen/Innen, Kurzformbreite, normierte Gewindeueberdeckung und Radius. Die bisherige rein groessenbasierte Breiten-Schaetzung wird dadurch fuer vorhandene Regelgewinde ersetzt; M30x3,5 verwendet beispielsweise `g2=12,0 mm`, `f=4,7 mm`, `r=1,6 mm` aussen und `g2=17,7 mm` innen.
- Performance: Die vollstaendige Sprach-/Widget-Praesentation bleibt Teil der synchronen Startbereitschaft. Ihre statische Uebersetzung indexiert den Widgetbaum jetzt einmal nach `objectName`, statt fuer jeden Schluessel erneut eine rekursive `findChild()`-Suche auszufuehren; das beseitigt die quadratische Startzeit nach der UI-Aufteilung.
- Safety/Audit (LES-037): Ein Kontur-Freistich ist derzeit nur an ein Kontursegment gebunden, nicht an eine konkrete Gewindeoperation. Im Referenzprogramm liegt das Feature bei `Z=-35`, das Gewinde endet aber bei `Z=-30`; Vorschau und Ausgabe duerfen diese fehlende Zuordnung nicht als korrekt behandeln.
- Fix (LES-037, P0): Der Gewinde-Generator bricht jetzt vor der Ausgabe mit einer klaren Fehlermeldung ab, wenn die vorgeschlagene DIN-Freistichbreite laenger als das Gewinde ist. Damit wird kein ungueltiger Freistich-Vorschlag erzeugt; die tatsaechliche Freistichgeometrie bleibt weiterhin eine Kontur-Funktion und ist noch unter LES-037 zu vervollstaendigen.
- Fix: Das Sperren des Programmkopf-Loeschens funktioniert auch ohne Qt-Elternwidget robust. Statt in einem Headless-/Testpfad beim Oeffnen eines Dialogs fehlzuschlagen, wird der Vorgang nachvollziehbar geloggt.
- Test-Audit: Der kombinierte Gesamtlauf mischt echte Qt- und Stub-Tests im selben Python-Prozess. Die aktuelle globale Import-Umschaltung kann dabei `qtpy`-Rekursionen ausloesen; die Testarten muessen in getrennte, reproduzierbare Laeufe aufgeteilt werden (LES-038).
- Dokumentation: Nullbytes aus `TODO.md` und `CHANGELOG.md` entfernt. Beide Dateien sind wieder normale Textdateien, so dass Suche, Diff und Changelog-Pruefungen sie vollstaendig verarbeiten.
- Audit/Plan (P0, real reproduzierbar): Freistich/Relief am Gewindeende muss am Ende der Gewindelaenge und nicht am Ende der Gesamtkontur verankert werden. Der derzeitige Fehlerpfad kann zu einem LinuxCNC-Fehler `not monotonic` fuehren, weil der letzte Freistich-Schritt nach der Gesamtkontur statt hinter dem Gewindeschritt liegt; der Generator muss hier sofort mit einer klaren Fehlermeldung abbrechen, wenn der verbleibende Platz nicht ausreicht
- Fix (LES-003, P0, schwerwiegend, real bestaetigt - Nutzerhinweis: "es wird keine wirkliche abspahnaufgabe generiert"): Die bewegungsbasierte Ersatzloesung `rough_turn_parallel_x()` (`gcode_roughing.py`, siehe unten fuer den Grund, warum G71/G72 fuer Innenbearbeitung nicht genutzt werden) suchte pro Zustelltiefe nur in einem hauchduennen Fenster (`x_cut +/- 1e-3`) nach Material - bei den meisten X-Baendern einer realen Innenkontur (Anfahrt, Radien, senkrechte Bohrungswand, Uebergaenge) traf dieses Fenster kein Kontursegment ("no cut region"), waehrend ein einzelnes Band zufaellig die GESAMTE lange Bohrungswand in einem einzigen ~33mm-Schnitt erfasste - exakt das gemeldete Symptom. Ersetzt durch eine "Materialreichweite"-Baenderung: pro Zustelltiefe `x_cut` wird jetzt ueberall dort geschnitten, wo die Zielkontur ueber `x_cut` hinausgeht (intern: Kontur-X >= x_cut bis zum Kontur-Maximum; extern: Kontur-X <= x_cut bis zum Kontur-Minimum) - fuer die reale Nutzerkontur ("ausdrehen") ergeben sich jetzt 9 gleichmaessige Einzelzustellungen statt eines Riesenschnitts, die letzten 3 Baender (steiler, kurzer Uebergang zur Bohrungsoeffnung) melden konsistent "no cut region" statt einer irrefuehrenden leeren "X-band"-Kopfzeile (zusaetzlicher Konsistenz-Fix: ein Band, dessen gefundene Intervalle alle entartet/zu flach sind, meldet jetzt ebenfalls "no cut region" statt einer Kopfzeile ohne folgenden Schnitt)
- Verifikation: der generierte G-Code fuer die reale Bohrungskontur (inkl. vorangehendem Bohren-Step) wurde mit dem echten LinuxCNC-Interpreter `rs274` geparst und ausgefuehrt - fehlerfrei, mit der erwarteten Treppenstufen-Bewegungssequenz (`STRAIGHT_TRAVERSE`/`STRAIGHT_FEED` je Zustellung)
- Tests: `tests/test_internal_roughing_uses_g71_cycle.py::test_internal_roughing_with_real_bore_contour_produces_even_stepped_passes` (vormals `..._still_produces_uneven_passes`, dokumentierte bewusst den alten Bug) auf das jetzt korrekte Verhalten umgeschrieben; `tests/test_gcode_motion_regressions.py::test_parallel_x_roughing_merges_touching_wall_and_transition_segments` an den jetzt vollstaendigeren zusammenhaengenden Schnitt angepasst (Z-10.0 statt Z-10.5, da die Baenderung ein kurzes Uebergangssegment korrekt mit erfasst); zwei `test_slicer_extra.py`-Tests zum `allow_undercut`-Verhalten neu geschrieben (das alte schmale Fenster lieferte dort nur hauchduenne ~0.001mm-Splitter, die faelschlich als Testerfolg gewertet wurden); alle geaenderten Tests gegen den alten Code per `git stash` auf `gcode_roughing.py` bestaetigt fehlgeschlagen; Stand `368 passed, 7 skipped`
- Fix (LES-010/LES-011, P1, real bestaetigt - Nutzerhinweis: "Freistich muss funktionieren, sonst kann es zu Problemen beim Gewinde drehen kommen"): DIN-Freistiche wurden bisher nur erzeugt, wenn das Feature am absolut ERSTEN oder LETZTEN Segment der GESAMTEN Kontur lag - ein Freistich mitten in einer laengeren Wellenkontur (z. B. Gewinde-Freistich, gefolgt von weiterem Profil bis zur naechsten Stufe) blieb komplett ohne Geometrie, nur mit einer unauffaelligen Warnung im G-Code-Kopf. `build_contour_variants()` (`contour_logic.py`) verfolgt jetzt waehrend der Haupt-Konturschleife fuer jedes Segment den zugehoerigen Primitiv-Indexbereich (`segment_prim_bounds`) und spleisst die Freistich-Primitive an der GENAU RICHTIGEN Stelle ein (vor dem Segment bei `orientation="start"`, danach bei `orientation="end"`) - die zugrundeliegende Geometrieformel war bereits generisch (haengt nur vom lokalen Segment-Punktpaar ab), die Anfang/Ende-Beschraenkung war eine rein kuenstliche `idx`-Pruefung. Mehrere Freistiche in einer Kontur werden in absteigender Segmentreihenfolge eingefuegt, damit sich Primitiv-Indizes nicht gegenseitig verschieben. Die jetzt veraltete Warnfunktion `_check_din_relief_feature_position()` (`checks.py`) wurde entfernt
- Verifikation: der reale, betroffene G-Code (M30-Aussengewinde-Freistich der Nutzerkontur "abdrehen", mitten in der Kontur) wurde mit dem echten LinuxCNC-Interpreter `rs274` geparst - fehlerfrei, mit der erwarteten Zustellsequenz (radial rein, axial durch die Freistichbreite, radial raus, zurueck auf die Hauptkontur, dann Fortsetzung des Wellenprofils). Aussen- UND Innenfreistich mitten in der Kontur beide bestaetigt
- Tests: `tests/test_din_relief_position_check.py` von "Warnung" auf "erzeugt korrekte Geometrie" umgestellt (Segment-1/mittleres Segment/letztes Segment als Faelle, inkl. Reihenfolge- und Rough-Pfad-Pruefung); `tests/test_relief_and_safety.py::test_validation_warning_comment_sanitizes_parentheses` auf eine andere, weiterhin bestehende Warnung mit Klammern umgestellt (die bisherige Freistich-Warnung existiert nicht mehr); Stand `368 passed, 7 skipped`
- Fix (LES-003, P0, sehr schwerwiegend, empirisch gegen den echten LinuxCNC-Interpreter verifiziert): `G71`/`G72` erzeugen bei Innenkonturen entgegen der Erwartung nur EINEN durchgehenden Schnitt statt echter Treppenstufen-Schrupppaesse. Verifiziert durch direktes Ausfuehren von generiertem G-Code (echte und minimale Testkonturen) mit dem eigenstaendigen LinuxCNC-Interpreter `rs274` gegen den auf dieser Maschine vorhandenen LinuxCNC-Quellcode (`/home/adm1n/linuxcnc-src`, Version 2.10.0~pre1 - identisch zur installierten Version): identisch aufgebaute Aussenkonturen zeigen im selben Test den korrekten, mehrfach zustellenden Treppenstufen-Zyklus (`interp_g7x.cc::pocket()`), Innenkonturen dagegen nur einen einzigen Schnitt von Anfahrpunkt bis Zielkontur - unabhaengig von Konturrichtung, -komplexitaet oder dem verwendeten `stock_x`-Wert. Kein Fehler dieses Generators, sondern eine Einschraenkung von G71/G72 fuer Innenbearbeitung in dieser LinuxCNC-Version. `G71`/`G72` werden in `generate_abspanen_gcode()` (`gcode_roughing.py`) jetzt nur noch fuer Aussenbearbeitung (`external=True`) gewaehlt; Innenbearbeitung nutzt immer die bewegungsbasierte Ersatzloesung, mit neuem, erklaerendem Fallback-Kommentar im generierten Code
- Erkenntnis (noch NICHT behoben, LES-003 bleibt offen): dieser Fix behebt die falsche Zyklus-Wahl, loest aber NICHT den urspruenglich gemeldeten Fehler ("keine wirkliche Abspanaufgabe generiert") vollstaendig - dieser liegt in der bewegungsbasierten Ersatzloesung `rough_turn_parallel_x()` selbst: ihre schmale Fenster-Intersection (`x_cut +/- 1e-3`) findet fuer mehrere X-Baender keinen Treffer ("no cut region"), waehrend ein anderes Band eine lange senkrechte Bohrungswand komplett in einem einzigen ~33mm-Schnitt zusammenfasst statt das Material ueber mehrere Zustellungen zu verteilen. Bewusst NICHT als schnelle Aenderung an sicherheitsrelevanter Fahrweg-Geometrie umgesetzt - braucht eine echte Neuentwicklung der Zustelllogik; als offener Punkt in TODO.md LES-003 dokumentiert, real-verifiziertes Verhalten in `tests/test_internal_roughing_uses_g71_cycle.py` festgehalten
- Tests: `tests/test_internal_roughing_uses_g71_cycle.py` ueberarbeitet - bestaetigt, dass G71/G72 fuer Innenbearbeitung nie mehr gewaehlt werden (Aussenbearbeitung bleibt unveraendert per G71 bestaetigt), dass die Bohrdurchmesser-basierte Materialgrenze (siehe unten) weiterhin korrekt berechnet wird, und dokumentiert per Test den noch unregelmaessigen Zustellverlauf der Ersatzloesung fuer die reale Nutzerkontur; drei bestehende Tests in `test_parting_slice.py`/`test_regression_contracts.py` an das neue (korrekte) Verhalten angepasst; Stand `367 passed, 7 skipped`
- Fix (LES-003, P0, real bestaetigt): Innen-Abspanen mit Vollzylinder-Rohteil (kein `XI` im Programmkopf gesetzt, da die Bohrung erst durch einen vorangehenden Bohren-Step entsteht) rechnete faelschlich mit dem kleinsten X-Wert der ZIELKONTUR selbst als Materialgrenze fuer den `G71`-Zyklus - der Zyklus "startete" damit praktisch schon auf der Fertigkontur, ohne echten Zustellweg zum Abfahren (Symptom: "die Kontur wird nur einmal quasi wie eine Aussenkontur nachgefahren, keine richtige Abspanstrategie"). `gcode_program.py` fuehrt jetzt den zuletzt gebohrten Durchmesser (`op.params["diameter"]` der letzten `DRILL`-Operation vor dem Abspanen-Step) als `_last_drill_diameter` mit; `_resolve_roughing_stock_x()` (`gcode_roughing.py`) nutzt diesen Wert als Materialgrenze, sobald kein plausibles `XI` gesetzt ist und der gebohrte Durchmesser kleiner als die Zielkontur ist - andernfalls bleibt der bisherige sichere Fallback (kleinster Konturwert) erhalten
- Tests: Neue Datei-Ergaenzung in `tests/test_internal_roughing_uses_g71_cycle.py` (zwei neue Faelle: gebohrter Durchmesser wird uebernommen; ein zu grosser gebohrter Durchmesser wird sicher ignoriert) - beide gegen den alten Code bestaetigt; Stand `366 passed, 7 skipped`
- Docs: `TODO.md`, `ROADMAP.md` und `doc/REALTEST_FRAGEN_2026-07-15.md` auf den aktuellen Entwicklungsstand synchronisiert. Die bereits vorhandenen Nutzerantworten zu Realtest 9 (Innen-Zustellrichtung bestaetigt), 11 (Innenstufe/-konus/-radius plausibel, Freistich offen) und 13 (Duplikate erlaubt, aber mit Warnung) werden nicht mehr faelschlich als unbeantwortete Blocker gefuehrt; TODO.md und die Realtest-Datei zeigen anschliessend wieder nur noch aktuell offene Aufgaben (erledigte Erlaeuterungstexte stehen bereits hier im Changelog)
- Planung: LES-013 auf die tatsaechlich noch offene sichere CSS-Aktivierungssequenz reduziert, LES-016 an die entfernte globale Spindelmodus-Combo angepasst und LES-036 als sichtbare, aber noch nicht implementierte P1-Funktion dem Ziel 0.8.0 zugeordnet
- Testprozess: Verbindliche Abnahmeanforderungen fuer G7-Boegen mit `I != 0`, direkten Schlichtweg und G71/G72-Subroutine, Innen-G71 mit beiden Z-Richtungen, gemischte G96/G97-Operationsfolgen sowie Planen-Radius ergaenzt. Neue/geaenderte Skips muessen begruendet werden; sicherheitsrelevante Fahrwege erfordern LinuxCNC-Backplot und dokumentierten Trockenlauf
- Verifikation: reine Dokumentationsaenderung; produktiver Code unveraendert, daher kein neuer Testlauf. Dokumentierter Stand bleibt `364 passed, 7 skipped`
- Fix (P0, schwerwiegend, real bestaetigt durch LinuxCNC-Fehlermeldung): Generierte Programme mit Bogenkontur (G2/G3 aus Kontur-Primitiven) wurden von LinuxCNC mit "Radius to end of arc differs from radius to start" abgelehnt. Ursache: `I` (X-Achsen-Offset zum Bogenzentrum) wurde als rohe Durchmesser-Differenz zum Zentrum berechnet (`cx - cur_x`) - `I` ist in LinuxCNC/Fanuc-Drehmaschinen-Dialekten aber IMMER ein Radiuswert, auch im Durchmessermodus `G7`, in dem die X-Koordinaten selbst Durchmesser sind. Betraf `_emit_finish_primitives()` (Schlichtschnitt/direkter Bogen) und `contour_sub_from_primitives()` (G71/G72-Zyklus-Subroutine) gleichermassen; unbemerkt bisher nur, weil alle Bogen in den Referenzbeispielen zufaellig `I0.000` hatten (Zentrum exakt auf der Startachse) - der Fehler trat erst bei einem Bogen mit echtem X-Versatz zutage (reale Innenkontur des Nutzers)
- Fix: Das Referenzbeispiel `Kontur_Radius_Fase.ngc` (`examples.py`) enthielt selbst einen handgeschriebenen, geometrisch ungueltigen Bogenmittelpunkt (Radius zum Start und zum Ende waren nie gleich, unabhaengig vom obigen Fix) - korrigiert auf einen tatsaechlich gueltigen Mittelpunkt (gleicher Radius zu beiden Endpunkten, per Mittelsenkrechte nachgerechnet)
- Tests: `tests/test_contour_arc_gcode.py` um drei neue Faelle ergaenzt (reale Nutzerkontur, G71-Subroutine-Pfad, Kontrollfall mit dem bereits validen Fillet-Algorithmus) - alle drei bestaetigt gegen den alten Code; `regenerate_all_ngc.py` zeigt den korrigierten `I`-Wert in `Kontur_Radius_Fase.ngc`; Stand `364 passed, 7 skipped`
- Fix (LES-003, P0, schwerwiegend, real bestaetigt): Innen-Abspanen nutzte bei vielen realen Innenkonturen keinen `G71`-Zyklus, sondern eine grobe bewegungsbasierte Ersatzloesung (sichtbar am Kommentar "Fallback-Grund: automatische Entscheidung -> Move-based" und ungleichmaessigen, teils winzigen Zustellungen). Root Cause: `is_monotonic_z_decreasing()` (`gcode_utils.py`) akzeptierte fuer die G71-Eignungspruefung (`parallel_z`-Strategie) nur FALLENDE Z-Werte - anders als bei X (`is_monotonic_x()` prueft beide Richtungen) fehlte eine "Z steigend"-Variante. Innenkonturen werden aber haeufig vom tiefsten Punkt zur Bohrungsoeffnung definiert (Z steigt monoton) - eine geometrisch einwandfreie, aber bisher faelschlich als "nicht zyklustauglich" abgelehnte Richtung. Neue Funktion `is_monotonic_z()` (faellt ODER steigt) ergaenzt und in der G71-Pruefung verwendet
- Tests: Neue Datei `tests/test_internal_roughing_uses_g71_cycle.py` (bestaetigt gegen den alten Code: Import-Fehler, da die neue Funktion vorher nicht existierte; mit dem realen "ausdrehen"-Konturbeispiel des Nutzers manuell nachvollzogen: G71-Aufruf statt 10 ungleichmaessiger Move-based-Passes); Referenz-`.ngc` unveraendert (kein Innen-Abspanen-Beispiel in `examples.py` vorhanden - als neuer TODO-Punkt unter LES-003 vermerkt); Stand `361 passed, 7 skipped`
- Fix (LES-013, P1, real bestaetigt): Innengewinde-Anfahrt fuhr eine sichere Position an und entfernte sich danach nochmal in Z vom Material, bevor eingefahren wurde. Ursache: `gcode_thread.py` routete fuer Innengewinde zusaetzlich ueber das eigene "Sicherheits-Z"-Feld des Gewinde-Steps (`safe_z`), obwohl bereits `XRI` (radial bei JEDER Z-Position sicher) erreicht war - wich `safe_z` vom Gewindestart (`start_z`) ab, entstand ein unnoetiger Zwischenstopp. Anfahrt geht jetzt direkt auf `(XRI, start_z)`
- Tests: `tests/test_thread_internal.py` - bestehenden Test auf das korrigierte Verhalten angepasst, neuen Regressionstest ergaenzt (beide gegen den alten Code bestaetigt); Referenz-`.ngc` unveraendert (kein Fall mit abweichendem `safe_z` darin)
- Fix (real bestaetigt, physikalisch falsche Einheit): `G96` (CSS) sendete unter `S` bisher denselben Zahlenwert wie die Drehzahl (`spindle`, U/min) - `G96` erwartet dort aber die Schnittgeschwindigkeit Vc in m/min. `append_tool_and_spindle()` (`gcode_safety.py`) nutzt jetzt einen eigenen `cutting_speed`-Parameter fuer `G96 S`; ohne gueltigen Wert faellt der Generator sicher auf `G97` mit der Drehzahl zurueck (Warnkommentar), statt eine falsche Zahl als Vc zu senden
- Feature (LES-013, P1): G96/G97 ist jetzt pro Operation waehlbar (Planen, Abspanen, Einstich/Abstich, Gewinde - Bohren bewusst ausgenommen, da sich der Werkzeugdurchmesser beim Bohren nicht aendert). Neue Felder `<prefix>_spindle_mode`/`<prefix>_cutting_speed` je Reiter; kontextabhaengige Anzeige (Drehzahl bei G97, Schnittgeschwindigkeit Vc bei G96) ueber neu gefasste `update_spindle_mode_visibility()`. Die globale `program_spindle_mode`-Combo im Programmkopf entfaellt (gehoerte fachlich nicht dorthin); `program_spindle_max_rpm` bleibt als programmweite CSS-Sicherheitsobergrenze erhalten und ist jetzt immer sichtbar
- Docs (LES-013): "bei CSS sicher mit G97 anfahren, G96 erst an der Bearbeitungsposition aktivieren" bewusst NICHT umgesetzt - erfordert eine verifizierte Vc-zu-Drehzahl-Umrechnung fuer die Anfahrt, die noch keine etablierte Konvention im Projekt hat; als offener Punkt in `TODO.md` LES-013 dokumentiert statt geraten
- Tests: Neue Datei `tests/test_per_operation_spindle_mode_ui.py` (echtes PyQt5: Widget-Erzeugung, Sichtbarkeit, Entfernen der globalen Combo); `tests/test_regression_contracts.py` und `tests/test_advanced_options.py` auf die korrigierte G96-Semantik (Vc statt Drehzahl) angepasst, ein neuer Test fuer den sicheren G97-Fallback ohne Vc ergaenzt; Stand `358 passed, 7 skipped`
- Analyse (kein Codeaenderung, auf Nutzerwunsch zurueckgestellt): Innen-Abspanen faellt bei vielen real vorkommenden Innenkonturen auf eine grobe bewegungsbasierte Ersatzloesung zurueck statt `G71` zu nutzen (sichtbar am Kommentar "Fallback-Grund: automatische Entscheidung -> Move-based"). Root Cause identifiziert: `is_monotonic_z_decreasing()` in `gcode_utils.py` akzeptiert nur FALLENDE Z-Werte fuer die G71-Eignungspruefung (`gcode_roughing.py`, `parallel_z`-Strategie) - anders als bei X existiert keine "Z steigend"-Variante und kein ODER-Fall. Innenkonturen werden aber haeufig vom tiefsten Punkt zur Bohrungsoeffnung definiert (Z steigt monoton) - eine geometrisch einwandfreie, aber bisher abgelehnte Konturrichtung. Vor einer Umsetzung noch zu klaeren: ob die `G71`-Startkoordinate (aktuell `X{stock_x} Z{safe_z}`) bei umgekehrter Konturrichtung weiterhin zum tatsaechlichen ersten Konturpunkt passt; Fix erfordert Backplot-/Trockenlauf-Verifikation vor Praxiseinsatz (siehe LES-003)
- Fix (schwerwiegend, real bestaetigt): Planen mit Kantenform "Fase" schlug im Generator fehl (`Invalid float for 'edge_type': 'chamfer'`) und brach die Programmerzeugung ab. Ursache: `gcode_face.py` las `edge_type` weiterhin ueber `int(float(...))`, obwohl die Combo seit der ID-only-Umstellung ueber `currentData()` die String-IDs `"none"/"chamfer"/"radius"` liefert (wie bereits bei `mode` ueber `resolve_enum_index()` korrekt gehandhabt) - eine der beiden Stellen wurde bei dieser Umstellung nicht mitgezogen. Nutzt jetzt ebenfalls `resolve_enum_index()` (neue `FACE_EDGE_TYPE_INDEX`-Tabelle), inklusive Rueckwaertskompatibilitaet zu alten numerischen Werten (siehe `examples.py`-Referenzprogramm)
- Fix: Kantenform "Radius" beim Planen ist im Generator noch nicht umgesetzt (nur "Fase" erzeugt eine Geometrie) - waere nach obigem Fix sonst still wie "Keine" behandelt worden (Nutzerwahl wortlos ignoriert). Erzeugt jetzt einen klaren Fehler statt eines unbemerkt falschen Ergebnisses (neuer Punkt LES-036 fuer die eigentliche Umsetzung)
- Tests: Neue Datei `tests/test_face_edge_type.py` (bestaetigt gegen den alten Code); Stand `352 passed, 5 skipped`
- Fix (schwerwiegend, real bestaetigt): Nach "Programm laden" fehlte bei einigen Operationen das Werkzeug in der Combo, obwohl beim Programmstart eine Werkzeugtabelle geladen wurde - erst ein manuelles Neuladen der Werkzeugtabelle stellte die Auswahl wieder her. Zwei Ursachen: (1) `handle_load_program()` rief nur `_auto_load_tool_table()` auf, das nach dem ersten (automatischen) Aufruf beim Programmstart dauerhaft gesperrt ist und beim Laden eines Programms nichts mehr tut; die im Speicher bereits vorhandene Werkzeugtabelle (`handler.tools`) wurde dadurch nie erneut auf (ggf. erst jetzt vorhandene) Werkzeug-Combos angewendet. (2) `load_operation_params_to_form()` interpretierte eine nicht in der Combo gefundene Werkzeugnummer (`findData()` ohne Treffer) ueber den generischen Fallback als Positions-Index in der Combo - je nach Combo-Inhalt wurde dadurch ein voellig falsches Werkzeug angezeigt, ohne dass dies auffiel, statt korrekt "kein Werkzeug ausgewaehlt" zu zeigen
- Fix: "Neues Programm" wendet die bereits geladene Werkzeugtabelle jetzt ebenfalls erneut auf alle Werkzeug-Combos an (vorher gar nicht, unabhaengig vom obigen Auto-Load-Zustand)
- Tests: Neue Dateien `tests/test_tool_table_persists_across_program_actions.py` und `tests/test_tool_combo_selection.py` (beide gegen den alten Code bestaetigt, letztere benoetigt echtes PyQt5); Stand `355 passed, 6 skipped`
- Fix (LES-023, P2, real reproduzierbarer Bug): `_insert_loaded_operation()` ("Step laden") und `_handle_add_operation()` frischten den in `params["comment"]` gespeicherten, nummerierten Steptext nur auf, wenn er komplett LEER war. Eine per "Step speichern" gesicherte Datei enthaelt aber ihren zum Speicherzeitpunkt gueltigen, bereits nummerierten Kommentar (z. B. "5. Innenabspanen ..."); wird dieselbe Datei spaeter per "Step laden" an anderer Position eingefuegt, blieb die alte, jetzt falsche Nummer im gespeicherten Kommentar (und damit im generierten `(STEP: ...)`-G-Code-Kommentar) stehen, obwohl die Operationsliste bereits die korrekte neue Nummer anzeigte - derselbe Widerspruch, der frueher schon fuer Verschieben/Loeschen behoben wurde (`renumber_operations()`). Neue Hilfsfunktion `_looks_like_generated_step_comment()` (`ui_flow.py`) erkennt maschinell nummerierte Kommentare (`^\d+\.\s`) und lässt nur diese neu erzeugen; ein bewusst individueller Kommentar ohne Nummern-Vorsilbe bleibt wie bisher unangetastet
- Tests: `tests/test_auto_comment_on_creation.py` um zwei Faelle ergaenzt (bestaetigt gegen den alten Code per manuellem Revert: veraltete Nummer wird jetzt aufgefrischt, Helper-Funktion unterscheidet generiert/individuell korrekt); `regenerate_all_ngc.py` unveraendert (Fix betrifft nur die UI-Einfuegepfade, nicht die Referenzbeispiele); Stand `347 passed, 5 skipped`
- Docs (LES-023): grössere architekturelle Restfrage bewusst offen gelassen und in `TODO.md` praezisiert - die Nummer dauerhaft dem laufenden `params["comment"]` einzuschreiben bleibt fehleranfaellig; die sauberere Loesung (Nummer ausschliesslich beim Programmexport erzeugen) sowie die Frage, ob Konturen in der Step-Nummerierung mitzaehlen sollen, sind eigene, noch offene Entscheidungen
- Docs/Tests (LES-025): Audit aller `_mark_dirty()`/`_mark_program_structure_dirty()`-Aufrufstellen (`ui_visibility.handle_global_change`, `ui_flow.handle_move_up/down`, `_handle_add_operation`, `_handle_delete_operation`, `_handle_param_change`) ergab, dass Sprachumschaltung (expliziter `program_language`-Ausschluss in `handle_global_change`), Step-/Operationswechsel (`load_operation_params_to_form`/`apply_program_header_to_handler` befuellen alle Widgets ausschliesslich unter `blockSignals(True)`) und Programm laden (`handle_load_program` ruft `_clear_dirty_state()` nach dem Laden explizit auf) bereits korrekt NICHT als Aenderung gewertet werden, waehrend echte Struktur-/Parameteraenderungen (Step verschieben/hinzufuegen/loeschen, echte Formulareingabe) korrekt markieren. Diese Pfade waren bisher unentdeckt, aber ungetestet
- Tests: Neue Datei `tests/test_dirty_state_signal_blocking.py` (echtes PyQt5) bestaetigt, dass `load_operation_params_to_form()` beim Befuellen aus gespeicherten Werten keine Widget-Signale ausloest; `tests/test_ui_visibility_guards.py` um drei Faelle fuer `handle_global_change()` ergaenzt (Sprachumschaltung markiert nicht, `_ui_loading` markiert nicht, echte Nutzeraenderung markiert); Stand `345 passed, 5 skipped`
- Fix (LES-021, P2, real gefundener Bug): `lathe_easystep/ui_static.py::load_ui_static_map()` scannte fuer die automatische Sprachumschaltung von "statischen" (nicht per `ui_advanced.py` dynamisch erzeugten) Widgets ausschliesslich die Shell-Datei `lathe_easystep.ui`. Beim fruehreren UI-Refactor (Aufteilung aller acht Bearbeitungsreiter in `lathe_easystep/ui_parts/*.ui`) wurde diese Funktion nicht mitgezogen - seither wurden Labels, Tooltips und Combo-Eintraege aus ALLEN acht Reiter-Dateien (u. a. Bohren, Gewinde, Einstich/Abstich, Kontur, Programm) bei einer Sprachumschaltung nie aktualisiert, obwohl fuer praktisch alle betroffenen Strings (z. B. `label_drill_dwell`, `groove_lage`-Comboeintraege, `btn_slice_view`-Tooltip, diverse `program_*_absolute`-Checkboxen) bereits vollstaendige de/en/es-Uebersetzungen im `.lng`-Katalog vorhanden waren - sie wurden schlicht nie angewendet. `load_ui_static_map()` scannt jetzt zusaetzlich alle Dateien unter `lathe_easystep/ui_parts/*.ui`
- Tests: Neue Datei `tests/test_ui_static_translation_split_tabs.py` (echtes PyQt5): bestaetigt gegen den alten Code per manuellem Revert (`git stash` auf `ui_static.py`), dass betroffene Labels/Tooltips/Combo-Eintraege aus Reiter-Dateien vor dem Fix bei Sprachumschaltung eingefroren blieben, und nach dem Fix korrekt zwischen de/en/es wechseln
- Feature/Fix (LES-016, P1): `program_spindle_max_rpm`/"CSS Max-RPM" (Programm-Reiter) war unabhaengig vom gewaehlten Spindelmodus (`program_spindle_mode`, G97/Festdrehzahl vs. G96/CSS) immer sichtbar - ein fuer G97 irrelevantes Feld stand dauerhaft im Formular. Neue Funktion `update_spindle_mode_visibility()` in `lathe_easystep/ui_visibility.py` blendet Feld und Label jetzt nur bei G96/CSS ein, analog zu den bestehenden Regeln fuer Bohrmodus (Dwell/Peck) und Planen (Kantentyp); an allen bestehenden Aufrufstellen der uebrigen Sichtbarkeitsfunktionen ergaenzt (`handle_global_change`, `_force_visibility_updates`, `_check_unit_change`, `_update_ui_after_widget_found`, `sync_form_to_operation`)
- Tests: `tests/test_ui_visibility_guards.py` um zwei neue Faelle fuer `update_spindle_mode_visibility()` ergaenzt; ausserdem drei bisher ungetestete, bereits bestehende Sichtbarkeitsregeln nachtraeglich abgesichert: Abspanen-Freistich "separat" (`parting_undercut_mode == "separate"` zeigt Werkzeug/Spindel/Vorschub-Felder fuer den Freistich), sowie am Einstich/Abstich-Reiter sowohl `groove_use_tool_width` (Schnittbreite-Feld) als auch der bisher ungetestete "kein Abstich"-Zweig von `groove_process_type`; Stand `342 passed, 3 skipped`
- Docs (LES-016): TODO.md praezisiert - Kontur, Gewinde und Innen/Aussen haben nach Audit aktuell KEINE Sichtbarkeitsregel im Code (kein Testluecken-, sondern ein Funktionsluecken-Befund); as solche als eigene, klar begruendete Punkte belassen statt als "erledigt" markiert
- Docs (LES-026): Verhalten bei doppelten geladenen Steps entschieden - Duplikate werden weiterhin zugelassen, aber (bereits ueber `_check_duplicate_operations()` implementiert und in `tests/test_duplicate_operation_check.py` abgesichert) bei gleichem Operationstyp und identischen Bearbeitungsparametern als Warnung gemeldet, ohne automatisch zu loeschen oder zu veraendern. Realtest-Frage 13 blieb ohne Nutzerantwort; die bereits im Code umgesetzte, in `TODO.md` dokumentierte Empfehlung deckt den Fall ab und wurde in `doc/REALTEST_FRAGEN_2026-07-15.md` entsprechend vermerkt
- Cleanup (LES-017): `slicer.py` (2496 Zeilen, Top-Level-Modul) entfernt. Es duplizierte weite Teile von `gcode_roughing.py`/`gcode_safety.py`/`gcode_utils.py`/`gcode_program.py`, reassignte an seinem Ende (Zeilen ~2410-2495) aber fast alle eigenen Top-Level-Namen auf die echten Funktionen aus diesen Modulen zurueck - der grosse Teil des Datei-Inhalts war damit toter, nie ausgefuehrter Code. Produktivcode hat `slicer.py` nie importiert; genutzt wurde es ausschliesslich noch von sechs Testdateien und dem alten `regenerate_ngc.py`. `regenerate_ngc.py` (einzelnes Referenzprogramm, importierte aus `slicer.py`) war bereits durch `regenerate_all_ngc.py` (alle sechs Referenzprogramme, importiert aus den echten `lathe_easystep`-Modulen) ersetzt und wurde ebenfalls entfernt
- Tests: `tests/test_abspanen_finish_allow.py`, `tests/test_contour_arc_gcode.py`, `tests/test_drill_modes.py`, `tests/test_thread_internal.py`, `tests/test_slicer.py` und `tests/test_slicer_extra.py` importieren jetzt aus den echten Modulen (`lathe_easystep.gcode_roughing`, `.gcode_program`, `.gcode_drill`, `.contour_logic`, `.model`) statt aus `slicer.py`; `regenerate_all_ngc.py` erzeugt nach der Entfernung weiterhin byte-identische Referenzdateien (`git diff` auf `ngc/*.ngc` leer)
- Cleanup (LES-029): `lathe_easystep/i18n/de.json`/`en.json` waren vom aktiven `.lng`-Loader (`translations.py`, laedt ausschliesslich aus `languages/*.lng`) nie verwendet worden. Nach Audit (keine Referenzen in Python-Code, Tests, `.ui`-Dateien oder Packaging-Konfiguration) entfernt; `DEV.md` entsprechend aktualisiert
- Fix/Feature (LES-002, P0): Ein Schruppstep (`mode=rough` oder `rough_finish`), der keinen einzigen echten Schnittbefehl erzeugt (fehlende Bearbeitungsrichtung, nicht zyklustaugliche Kontur ohne Schnittbereich, o. ae.), erzeugte bisher bestenfalls eine Kommentar-/Warnzeile im G-Code - ein leicht zu uebersehendes, scheinbar gueltiges, aber leeres Programm. `generate_abspanen_gcode()` bricht jetzt mit `ValueError` ab, sobald fuer den Schrupp-Anteil kein `G1`/`G71`/`G72` erzeugt wurde. Die alte, jetzt unerreichbare Warnzeile fuer den Fall "keine Strategie gewaehlt" wurde entfernt (der neue Fehler deckt diesen Fall vollstaendig ab, inklusive `mode=rough_finish`, das vorher gar keine Meldung bekam)
- Tests: Neue Datei `tests/test_empty_roughing_aborts.py`; mehrere bestehende Tests, die versehentlich ohne `slice_strategy` schruppten (aber etwas anderes pruefen wollten), um eine gueltige Strategie ergaenzt; Stand `336 passed, 3 skipped`
- Docs: `TODO.md`, `ROADMAP.md`, `README.md` und `DEV.md` auf den Stand 24.07.2026 synchronisiert: erledigte ZRA/ZRI- und G76-Pruefpunkte aus dem offenen Plan entfernt, UI-Teilung und vollstaendige de/en/es-Kataloge dokumentiert, `slicer.py`-Bereinigung und alle verbleibenden Sicherheits-, Kontur-, UI-, Preview-, Werkzeug- und Architekturaufgaben eindeutig priorisiert
- Docs: `doc/REALTEST_FRAGEN_2026-07-15.md` ausgewertet (Nutzerantworten zu 15 Realtest-Fragen) und `TODO.md` entsprechend bereinigt:
  - Erledigt/durch Antwort geschlossen: G53-Werkzeugwechsel (F1: "funktioniert"), Bewegung nach M6 (F2: "nein, alles korrekt"), Tooltips (F4: "scheinen alle zu funktionieren"), Sprachumschaltung (F5: "gerade alle ok"), Vorschau/Slice/Frontview (F6: "sieht alles ok aus" - nach den Absturz-/Freeze-Fixes dieser Session), G76-Masssystem (F12: "generierte Werte scheinen zu passen")
  - `safe_z`/`ZRA`/`ZRI` absolut vs. relativ bei ABSPANEN (F10): Nutzer bestaetigt, dass die Regel in der Praxis beachtet wird und Abweichungen bereits beim Generieren gemeldet werden - aus der bereits dokumentierten "Blockiert"-Liste entfernt, da ohne konkretes Gegenbeispiel kein Aenderungsbedarf ersichtlich ist
  - Durch Antwort ausgeloeste Fixes/Features: siehe die eigenen Eintraege weiter unten (erster Werkzeugwechsel, Bohr-Anfahrt, drittes Combo-Item "Schruppen + Schlichten", Innen-Schruppen-Bug)
  - Weiterhin offen (unbeantwortet): Startzeit/Reaktionszeit (F7), Materialmodell-Richtung fuer Innen-Schruppen Parallel-Z (F9), Innenkonturformen-Verifikation (F11), Verhalten bei doppelten Operationen beim Step-Laden (F13)
- Fix (schwerwiegend, real bestaetigt via Realtest-Antwort Q15: "innenabspanen ... das ist Blödsinn, was da generiert wird"): `rough_turn_parallel_x()` (Move-based-Fallback fuer die Strategie "parallel_z") baute pro X-Band ungemergte Z-Intervalle aus allen schneidenden Kontursegmenten. Beruehren/ueberlappen sich zwei Segmente am selben X (z. B. eine senkrechte Bohrungswand, die exakt dort endet, wo eine Fase/ein Radius beginnt - genau die reale "ausdrehen"-Innenkontur), entstanden fuer dasselbe Band mehrere sich ueberschneidende Schnitt-Intervalle: das Werkzeug fuhr denselben Tiefenbereich mehrfach anstatt in einem zusammenhaengenden Zug an (sichtbar als naeherungsweise identische, aber leicht abweichende Z-Werte in aufeinanderfolgenden Zeilen). Das Pendant `rough_turn_parallel_z()` mergt seine Intervalle bereits ueber die vorhandene `merge_intervals()`-Funktion - der Aufruf fehlte hier
- Tests: Neue Regression `test_parallel_x_roughing_merges_touching_wall_and_transition_segments` (bestaetigt gegen den alten Code per manuellem Revert); Stand `331 passed, 3 skipped`
- Feature (Realtest-Antwort Q14: "drittes Combo-Item Schruppen + Schlichten? - ja"): `parting_mode` (Abspanen-Reiter) hatte in `lathe_easystep/ui_parts/tabParting.ui` nur zwei `<item>`-Eintraege (Schruppen/Schlichten), obwohl Registry/Uebersetzungen (`ui_registry.py`, alle drei `.lng`-Dateien) den dritten Wert "rough_finish" bereits vorbereitet hatten - im echten Panel war die kombinierte Option nicht auswaehlbar. Drittes `<item>` "Schruppen + Schlichten" ergaenzt, analog zum bereits vollstaendigen `face_mode`
- Fix: `PARTING_MODE_INDEX` in `gcode_roughing.py` kannte nur `"rough"`/`"finish"`, nicht `"rough_finish"` - `resolve_enum_index()` waere fuer die String-ID des neuen dritten Combo-Items auf den Default (0/Schruppen) zurueckgefallen und haette den Schlichtschnitt stillschweigend uebersprungen. Ergaenzt (analog zu `FACE_MODE_INDEX`, das den Eintrag bereits korrekt hatte)
- Tests: Neue Datei-Ergaenzungen `tests/test_finish_mode_never_reroughs.py` (String-ID-Aufloesung) und `tests/test_split_ui_loader.py` (echtes PyQt5, drei sichtbare Combo-Eintraege); Stand `330 passed, 3 skipped`
- Fix (real bestaetigt via Realtest-Antwort Q8: "Anfahrt sollte so sein wie die Abfahrt, Abfahrt ist gut"): Bohren nutzte eine eigene, bespoke Anfahrlogik (`emit_drill_approach` in `gcode_drill.py`) statt des projektweiten `emit_approach()`-Helfers - mit teils redundanten Bewegungen (generische sichere Position, danach nochmal separat auf Startpunkt) und einer anderen Struktur als die bereits als korrekt bestaetigte Rueckzugssequenz. Bohren verwendet jetzt `emit_approach()`, denselben Helfer wie Abspanen/Einstich
- Tests: `test_drill_approach_uses_shared_safety_helper_like_other_operations` (ersetzt einen Test, der die alte bespoke Struktur festschrieb); Referenzdatei `ngc/Bohren.ngc` angepasst; Stand `329 passed, 3 skipped`
- Fix (schwerwiegend, real bestaetigt via Realtest-Antwort): Der ERSTE Werkzeugwechsel eines Programms fuhr nicht zum definierten Werkzeugwechselpunkt. Ursache: `generate_program_gcode()` ruft `gcode_for_operation()` zuerst nur zur Vorab-Validierung auf, mutiert dabei aber denselben `settings`-Dict (u. a. `_current_tool` ueber `append_tool_and_spindle()`). Verwenden alle Operationen dasselbe Werkzeug, stand `_current_tool` nach der Validierung bereits auf dem ERSTEN echten Werkzeug - der Vergleich "tool_num != last_tool" im echten Erzeugungsdurchlauf wurde dadurch faelschlich `False`, und der Werkzeugwechselpunkt wurde beim ersten (und einzigen) Wechsel nicht angefahren. Die Werkzeug-/Positions-Laufzeittracker (`_current_tool`, `_is_at_safe`, `_active_retract_mode`) werden nach der Validierungsschleife jetzt zurueckgesetzt; die `needs_step_*_pause_sub`-Flags bleiben davon unberuehrt erhalten (werden fuer die Subroutinen-Definitionen gebraucht)
- Tests: Neue Regression `test_first_toolchange_moves_to_toolchange_point_when_only_one_tool_used` (bestehender Test mit zwei unterschiedlichen Werkzeugen uebersah den Fehler zufaellig); mehrere Tests mit unspezifischen `in lines`/`.index()`-Pruefungen auf Retract-Zeilen praezisiert, die durch die jetzt korrekt erscheinende erste Werkzeugwechsel-Sequenz auf denselben Text (z. B. `G0 X45.000 Z5.000`) trafen; alle sechs Referenzdateien in `ngc/` an die jetzt korrekte erste Werkzeugwechsel-Sequenz angepasst; Stand `329 passed, 3 skipped`
- UI: Vorschau-Dock kompakter aufgebaut; Seitenvorschau und Schnittansicht liegen jetzt nebeneinander und belegen deutlich weniger Hoehe im rechten Bereich
- UI: Fehlende Tooltips in `Abspanen`, `Gewinde` und `Einstich/Abstich` ueber das Sprachsystem fuer `de`, `en` und `es` vervollstaendigt
- UI-Refactor: `lathe_easystep.ui` ist jetzt die Start-Shell; die Reiter `Program`, `Face`, `Contour`, `Parting`, `Thread`, `Groove`, `Drill` und `Keyway` liegen als einzelne Dateien unter `lathe_easystep/ui_parts/*.ui` und werden zur Laufzeit ueber `lathe_easystep/ui_split.py` in die bestehenden Tab-Container geladen
- Tests: Zusätzliche UI-Sichtbarkeits-Regressionen für Rohteilform (`tube`/`polygon`) und Rueckzugsmodus (`simple`/`all`) ergaenzt; offene Sichtbarkeitsarbeit in der `TODO` auf die fachlichen Restbereiche Kontur/Abspanen/Gewinde reduziert
- Drill: Die Bohr-Einfahrt nutzt jetzt eine eigene sichere Sequenz statt des generischen Diagonal-Endzugs von `emit_approach()`. Aus der Safe-Position wird erst auf die Bohr-Rueckzugsebene in `Z`, dann auf die Bohr-Achse in `X` gefahren; das spiegelt die bereits als korrekt bestaetigte Abfahrt sauber
- Fix: Validierungs- und Sicherheitswarnungen werden vor der Ausgabe als LinuxCNC-Kommentar jetzt konsequent geklammert-sicher bereinigt; Texte wie `Segment 3 (z. B. ...)` erzeugen damit keinen `nested comment`-Fehler mehr im generierten `.ngc`
- Toolchange: Der erste echte Werkzeugwechsel im Programm nutzt jetzt denselben definierten Werkzeugwechselpfad wie Folgewechsel; vor jedem expliziten `T.. M6` wird der konfigurierte Wechselpunkt sauber angefahren
- UI: `rough_finish` ist im Abspanen-/Einstich-Modus jetzt auch im Panel als drittes Strategie-Combo-Item sichtbar und an die bestehende Sichtbarkeitslogik angebunden
- Safety: `XRI` ist jetzt fuer Innenbearbeitung eine harte Sicherheitsgrenze. Innengewinde, Inneneinstich und Innen-Abspanen werden abgewiesen, sobald irgendein angeforderter X-Wert kleiner als `XRI` waere
- Safety: Innen-Gewindeanfahrt haelt `XRI` jetzt bis zur Start-Z-Position ein; der Generator faehrt erst dort auf den eigentlichen Gewinde-Anfahrdurchmesser
- Safety: Werkzeugwechsel rueckziehen vor `M6` immer ueber die aeusseren Safe-Planes; die naechste Innenoperation schaltet den Rueckzug nicht mehr schon vor dem Wechsel auf `XRI/ZRI` um
- Motion: Schlichtwege fuer Konturen mit Radius erhalten Boegen jetzt im expliziten Finish-Pfad als `G2/G3` statt sie zu `G1`-Fasen zu linearisieren
- Motion: Groove-/Einstich-Anfahrten nutzen fuer sichere Anfahrt jetzt die hinterlegten Rueckzugsebenen statt direkt vor der Bearbeitungsposition am Material zu starten
- Motion: Innen-Schruppen mit `parallel_z` verwendet `XRI` nicht mehr als Ersatz fuer den Schrupp-Startstock; bei fehlendem/untauglichem `XI` wird der Kontur-Mindestdurchmesser als Start fuer reale Innen-Schruppbahnen verwendet
- Workflow: neue Datei `doc/REALTEST_FRAGEN_2026-07-15.md` als ausfuellbare Sammelstelle fuer reale LinuxCNC-/QtVCP-Tests und offene Nutzerentscheidungen
- Repo: `.cps`-Postprozessor-Dateien sind jetzt in `.gitignore`, damit lokale LinuxCNC-/Inventor-Postprozessoren nicht versehentlich committed werden
- Docs: README und DEV-Dokumentation um die harte `XRI`-Sicherheitsregel und den neuen Realtest-Workflow ergaenzt
- Fix: Die Schnittansicht (Frontview) wirkte nach dem Ziehen an der Schnittkante eingefroren - die dargestellte Z-Position aktualisierte sich visuell nicht. Ursache: `_ensure_slice_z_matches_operation()` wird bei JEDEM `_refresh_preview()`-Durchlauf aufgerufen (nicht nur beim Wechsel des ausgewaehlten Steps) und setzte `slice_z` fuer jede Nicht-Nut-Operation bedingungslos auf den vorgeschlagenen Standardwert zurueck. Jeder beliebige Refresh waehrend des Ziehens (Tab-Wechsel, Parameteraenderung, periodische Aktualisierung) machte die manuelle Positionierung dadurch unsichtbar rueckgaengig, noch bevor sie sichtbar wurde. Der Vorschlag greift jetzt nur noch, wenn sich die aktive Operation seit dem letzten Aufruf tatsaechlich geaendert hat
- Tests: Neue Datei `tests/test_slice_view_z_not_reset_on_refresh.py`; bestaetigt gegen den alten Code (verifiziert per `git stash`); Stand `309 passed, 2 skipped`
- Fix (kritisch, Absturz): `lathe_easystep/preview_widget.py` (bei der Extraktion aus dem Handler in einer frueheren Session ausgelagert) verwendete vier Namen ohne Import: `is_internal_side` (Aussen-/Innenerkennung fuer die Schnittansicht) sowie `build_keyway_slot_angles`/`front_view_polar_to_cartesian`/`keyway_slice_bounds` (Nutkontur in der Frontansicht). Sobald die Schnittansicht (Slice-/Frontview-Toggle) tatsaechlich gemalt wurde, stuerzte PyQt5 mit `NameError` beim `paintEvent` hart ab (Panel-Absturz, exakt wie gemeldet). Alle vier Imports ergaenzt (aus `gcode_utils.py` bzw. `preview_geometry.py`, wo die Funktionen tatsaechlich definiert sind)
- Tests: Neue Datei `tests/test_preview_widget_paint_no_crash.py` (echtes PyQt5, da der qtpy-Stub `paintEvent()` nie wirklich aufruft und den fehlenden Import nicht gefunden haette) - malt die Frontansicht fuer Aussen-/Innen-Abspanen und Nut und bestaetigt gegen den alten Code einen echten Prozessabsturz (`Fatal Python error: Aborted`), gegen den neuen Code sauberes Bestehen. Ausfuehren mit `/usr/bin/python3 -m pytest tests/test_preview_widget_paint_no_crash.py`
- Docs: `TODO.md` erneut bereinigt und gestrafft; erledigter `currentText()`-Audit entfernt, Sichtbarkeits-Tests auf den tatsaechlich noch offenen Rest reduziert und die strikte UI-/Sprachtrennung als eigener Architekturblock explizit dokumentiert
- Tests: Neue Datei `tests/test_ui_visibility_guards.py` ergaenzt Regressionen fuer Sichtbarkeitslogik in Planen, Bohren und Subspindel, fuer `chuck_size_mm()` sowie einen Guard, der verbleibende `currentText()`-Verwendungen auf bewusst auditierten Fallback-/Debug-Stellen einfriert
- Tests: Test-Infrastruktur fuer Real-Qt- und Stub-basierte Laeufe entkoppelt (`tests/conftest.py`, `tests/test_slice_strategy_ui_roundtrip.py`, `tests/test_dirty_and_messages.py`), damit echte PyQt5-Tests die uebrige Suite nicht mehr durch entfernte `qtpy.QtCore`/`qtpy.QtWidgets`-Aliase destabilisieren
- Verifikation: Neue und betroffene fokussierte Testbloecke erfolgreich geprueft:
  - `tests/test_ui_visibility_guards.py`
  - `tests/test_parting_visibility.py`
  - `tests/test_dirty_and_messages.py`
  - `tests/test_slice_strategy_ui_roundtrip.py`
  - `tests/test_step_path_persistence.py`
- Refactor: Gemeinsame UI-Helfer fuer Sprachcode, Uebersetzung, ComboBox-Befuellen und Tab-Bezeichnungen in `lathe_easystep/ui_helpers.py` zentralisiert
- Refactor: Doppelte Safe-X-Berechnung fuer Innen-Abspanen und Innengewinde nach `gcode_utils.py` verschoben
- Refactor: Generische `get_param_int()`-/`get_param_float()`-Lookups aus dem Groove-Generator nach `gcode_utils.py` verschoben; Werkzeugnummern verwenden dieselbe zentrale Konvertierung
- Cleanup: Ungenutztes und durch fehlende interne Module nicht importierbares Alt-Paket `lathe_easystep/contour/` entfernt; aktive Konturpfade ueber `contour_logic.py`/`contour_features.py` bleiben unveraendert
- Verifikation: Python-Syntaxpruefung, Diff-Pruefung und fokussierte dependency-freie Tests der zentralisierten G-Code-Helfer erfolgreich; vollstaendiger Testlauf lokal wegen fehlendem `pytest`/`qtpy` nicht moeglich
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
- Safety: Einstich-/Abstich-Zyklus (`o220` in `gcode_groove.py`) bricht bei ungueltigen Parametern (Werkzeugbreite/Nutbreite/Zustellung <= 0, Werkzeug breiter als Nut) jetzt ueber echtes `M99` ab statt wirkungslose Kommentare zu haben; Schrupp-Schleife hat eine harte Iterationsobergrenze gegen Endlosschleifen bei Nullbewegung
- Safety: Innen-Nut-Einstich (`GROOVE lage=1`) verwendet jetzt ebenfalls `XRI`/`ZRI` statt `XRA`/`ZRA` fuer Anfahrt/Rueckzug, analog zu Innengewinde und Innen-Abspanen
- Safety: Sichere Z-Rueckzugsebene bei Innenbearbeitung korrigiert - `gcode_safety._safe_axis_value()` nutzte faelschlich `ZI` (hinteres Endmass, nahe Futter) statt `ZA` (vorderes, zugaengliches Mass) als Bezug; dadurch fuhr der Rueckzug teils mitten ins bzw. durchs Rohteil (der Generator warnte selbst davor, fuhr aber trotzdem)
- Fix: G-Code-Kommentare werden nicht mehr zeilenuebergreifend erzeugt (LinuxCNC schliesst `(...)`-Kommentare nicht ueber Zeilenumbrueche hinweg)
- Fix: Fuenf `QFormLayout`-Zellenkollisionen (Face-/Parting-/Thread-/Groove-/Drill-Reiter: Werkzeug-Combo + Tool-Preview-Bild in ungueltiger dritter Spalte, von Qt als `SpanningRole` fehlinterpretiert) behoben; mit echtem PyQt5 warnungsfrei verifiziert
- Fix: Systemisches String- vs. Int-Problem bei ID-only-Combo-Werten (Gewinderichtung/-hand, Innen/Aussen-Seite, Bohr-/Abspan-/Planmodus) behoben - fuehrte teils zu Abstuerzen, teils zu stillem Fehlverhalten (z. B. Innengewinde wurde als Aussengewinde erzeugt, G82/G83/G73/G84-Bohrzyklen liefen heimlich als G81); neue Helfer `is_internal_side()`/`is_left_hand()`/`resolve_enum_index()` in `gcode_utils.py`
- Fix: Innenkontur-Vorschau leerte sich faelschlich bei Konturelementen, die nur eine Achse setzen (`x_empty`/`z_empty`-Markierung wurde von der Validierung ignoriert)
- Fix: `setup_param_maps()` baute die komplette Widget-Zuordnung bisher bei jedem Step-/Tabwechsel und jeder Feldaenderung komplett neu auf (100+ Widget-Suchen ohne Zwischenspeicherung); jetzt einmalig und selbstheilend gecacht
- Fix: Fehlermeldung bei fehlgeschlagener G-Code-Erzeugung zeigt jetzt zuverlaessig Reiter und Feldname; das Panel springt bei einem Generierungsfehler automatisch zum betroffenen Step/Reiter und hebt das Feld farblich hervor
- Fix: Preset-Button im Gewinde-Reiter kollidierte im Formular-Grid mit der Standard-Auswahl, jetzt eigene Zeile
- Fix: Zahlreiche fehlende Uebersetzungsschluessel ergaenzt (Gewinde-Presets, Groove-Diagramm-Labels, Kontur-Laufzeitwerte, Drill-/Parting-Beschreibung); `ui_static.py` verlangt keinen Schluessel mehr fuer leere Platzhalter-Labels (z. B. Diagramm-Vorschaubilder)
- Feature: Aktivierbarer Debug-Modus (`LATHEEASYSTEP_DEBUG=1` vor dem Start setzen) fuer ausfuehrliche Laufzeit-Logs: Feldaenderungen, Step-/Tabwechsel inkl. Zeitmessung, Vorschau-Refresh inkl. Zeitmessung, Dirty-State-Aenderungen, G-Code-Generierung inkl. Zeitmessung, Fehler-Navigation
- Feature: Tooltips fuer alle Bedienelemente in Planen, Bohren, Kontur und Keilnut ergaenzt (vorher dort keine registriert) in Deutsch/Englisch/Spanisch
- Validierung: DIN-Freistich-Presets bekommen jetzt Plausibilitaetspruefungen wie Gewinde-Presets (`validate_din_relief_preset_data()`)
- Tests: umfangreiche neue Regressionen fuer alle oben genannten Fixes, u. a. mit echtem PyQt5 (Systempaket `python3-pyqt5`) statt nur Test-Stubs verifiziert; Stand `260 passed`
- Refactor: `lathe_easystep_handler.py` deutlich verkleinert (7501 -> 4965 Zeilen), damit der Handler wieder naeher an "nur Kleber zwischen den Modulen" ist:
  - Ueber 1100 Zeilen totes, laengst durch `preview_geometry.py`/`contour_logic.py` ersetztes Code entfernt (u. a. Duplikate von `build_face_path`, `build_contour_path`, `validate_contour_segments_for_profile`, `gcode_for_operation` - alle durch spaetere Imports bereits ueberschattet und nie erreicht)
  - `LathePreviewWidget` (2D-Vorschau-Canvas) nach `lathe_easystep/preview_widget.py` ausgegliedert; als promoted Widget in `lathe_easystep.ui` unveraendert ueber den bestehenden `<header>lathe_easystep_handler</header>` erreichbar, da der Handler die Klasse re-exportiert
  - `WidgetResolver`/`WidgetResolveError` (Widget-Suche fuer Standalone-/eingebettetes Panel) nach `lathe_easystep/widget_resolver.py` ausgegliedert
  - `_collect_params()` nach `lathe_easystep/ui_params.py` (`collect_params()`) ausgegliedert, neben dem bereits dort lebenden `setup_param_maps()`
  - `PANEL_WIDGET_NAMES` nach `lathe_easystep/ui_registry.py` verschoben (gemeinsam von Handler und `widget_resolver.py` genutzt)
  - Vier lebende, bisher nur im Handler vorhandene Vorschau-Hilfsfunktionen (`build_stock_outline`, `build_retract_primitives`, `build_worklimit_primitives`, `build_chuck_nogo_primitives`) nach `preview_geometry.py` verschoben statt geloescht
  - Jede Extraktion einzeln mit vollem Testlauf und echtem PyQt5 (`uic.loadUi` gegen `lathe_easystep.ui`) verifiziert
- Docs: `TODO.md` bereinigt - enthaelt nur noch offene Punkte, erledigte Punkte stehen ausschliesslich hier im Changelog
- Fix: Futter-Sperrzone in der Vorschau begann bisher nicht bei `ZB` (Bearbeitungsmass - die tatsaechliche Grenze, ab der das Rohteil aus dem Futter herausschaut), sondern wurde komplett aus `chuck_no_go_z_limit` plus einem geschaetzten Abstand konstruiert. Die Zone beginnt jetzt korrekt bei `ZB` und reicht von dort Richtung Futter (weiter negativ)
- Fix: Gewinde-Presets wurden nie uebernommen (`thread preset skipped: missing label` bei jedem Klick auf "Preset uebernehmen"). Ursache: `_populate_thread_standard_options()` baute das Combo-itemData ohne den von `validate_thread_preset_data()` zwingend verlangten Schluessel `label` (nur `label_key` war vorhanden)
- Fix (schwerwiegend): Kontur-Punkte mit einem absoluten Ziel von exakt `X0`/`Z0` wurden in `contour_logic.py` stillschweigend durch die vorherige Koordinate ersetzt (`s.get(key, last) or last` - `0.0` ist in Python falsy). Betraf sowohl die Vorschau als auch den generierten G-Code: eine Kontur, die z. B. bis `X19.2`/`Z0` laufen sollte, brach vorher bei einem Zwischenpunkt ab, sobald ein Segment exakt auf `0` zielte
- Fix: `Programm laden` sprang bisher immer auf den ersten fachlichen Schritt (Zeile 1) statt auf den Programmkopf (Zeile 0), sobald das geladene Programm mehr als eine Operation enthielt - praktisch immer der Fall. Ausgangspunkt nach dem Laden ist jetzt immer der Programmkopf
- Tests: Regressionen fuer alle vier Fixes ergaenzt, u. a. mit den exakten Werten aus einem real geladenen Testprogramm; Stand `264 passed`
- Fix (schwerwiegend): Innen-Schruppen (`Abspanen`, Modus Schruppen) erzeugte bei einem realen Testprogramm keinerlei Schnittbewegung, nur eine WARN-Zeile ("ohne Bearbeitungsrichtung deaktiviert"). Ursache war ein UI/Generator-Widerspruch bei `slice_strategy`:
  - `_select_slice_strategy_index()` suchte per `combo.findData(<int>, ...)`, obwohl das itemData der Combo immer die Strings `"parallel_x"`/`"parallel_z"` enthaelt - der Treffer konnte nie gelingen, gueltige gespeicherte Werte (`1`/`2`) wurden beim Laden nie korrekt auf die Combo angewandt
  - `load_operation_params_to_form()` liess `slice_strategy` danach in den generischen `setCurrentIndex(int(val))`-Fallback durchfallen; ein ungueltiger gespeicherter Wert wie `0` landete dadurch auf einem echten Combo-Eintrag ("Parallel X") - die Anzeige log also eine Auswahl vor, die nie getroffen wurde, waehrend `gcode_roughing.py` denselben Wert `0` korrekt als "keine Strategie gewaehlt" behandelte und nur warnte
  - `collect_params()` erzeugte fuer eine Combo ganz ohne Auswahl (`currentIndex() == -1`) ueber den Fallback `idx + 1` den ungueltigen Wert `0` und schrieb ihn in die Operation - exakt der Wert, der spaeter die widerspruechliche Anzeige verursachte
  - Alle drei Stellen korrigiert: numerische Legacy-Codes werden jetzt korrekt auf die String-itemData abgebildet, eine nicht aufloesbare/fehlende Auswahl zeigt die Combo jetzt ehrlich als "nicht ausgewaehlt" (`currentIndex() == -1`) statt eine falsche Strategie vorzutaeuschen, und `collect_params()` fabriziert keinen ungueltigen Platzhalterwert mehr
  - Klarstellung: Die Erzeugung verweigert weiterhin bewusst einen Schruppschnitt ohne explizit gewaehlte Bearbeitungsrichtung (kein automatisches Raten) - das ist beabsichtigt; der Fix beseitigt nur den Widerspruch zwischen UI-Anzeige und tatsaechlichem Generatorverhalten, so dass die Warnung jetzt tatsaechlich handlungsleitend ist
- Tests: Neue Datei `tests/test_slice_strategy_ui_roundtrip.py` (mit echtem PyQt5 statt Stub, da der projektweite qtpy-Stub isinstance-Unterscheidungen zwischen Widget-Typen nicht abbilden kann); `6 passed`. Ausfuehren mit `/usr/bin/python3 -m pytest tests/test_slice_strategy_ui_roundtrip.py`
- Feature: Neue Plausibilitaetspruefung `_check_drill_before_internal_machining()` in `checks.py` - warnt (ohne selbst umzusortieren), sobald eine Innenbearbeitung (Innen-Abspanen, Innen-Einstich, Innengewinde) in der Ablaufreihenfolge vor der ersten Bohrung steht oder gar keine Bohrung vorhanden ist. Das Werkzeug haette sonst keinen Zugang zum noch vollen Material
- Tests: Neue Datei `tests/test_drill_before_internal_check.py` deckt Innen-vor-Bohrung, Bohrung-vor-Innen, fehlende Bohrung, gemischte Groove/Gewinde-Faelle und reine Aussenbearbeitung ab; Stand `269 passed, 1 skipped`
- Fix (schwerwiegend, Datenintegritaet): `ProgramModel.update_geometry()` fror bei bestimmten Operationstypen (u. a. Einstich/Abstich, Planen) den jeweils aktuellen `op.path` als Snapshot in `op.params["path"]` ein (write-once: nur solange der Key noch fehlte). Dieser Snapshot wurde bei spaeteren Parameteraenderungen (z. B. Aussen-Einstich zu Innen-Einstich mit anderem Werkzeug/Durchmesser umgebaut) nie aktualisiert und driftete stillschweigend von der tatsaechlichen Geometrie weg - mit in der gespeicherten Step-Datei sichtbaren, in sich widerspruechlichen Angaben (Werkzeug/Lage/Durchmesser in den Parametern vs. eingefrorener alter Pfad). Geometrie wird jetzt ausschliesslich ueber `op.path` gefuehrt, `params["path"]` wird nicht mehr geschrieben
- Tests: Neue Datei `tests/test_geometry_cache_staleness.py` reproduziert exakt das reale Fehlerbild (Aussen- zu Innen-Einstich-Umbau) und schlaegt gegen den alten Code fehl (verifiziert per `git stash`); Stand `270 passed, 1 skipped`
- Fix (Sicherheit): Die Einfahrt vor dem Schlichtschnitt bei Abspanen (`generate_abspanen_gcode`, Innen- und Aussenbearbeitung) war ein einzelner diagonaler `G0` (X und Z gleichzeitig) direkt aus der vorherigen Position - ohne die Rohteil-/Futter-Sperrzonen-Pruefung und ohne die sichere Zwei-Schritt-Sequenz (erst Z, dann X), die dieselbe Funktion fuer die Schrupp-Zustellung bereits verwendet (`emit_approach()`). Die Schlicht-Einfahrt nutzt jetzt denselben, bereits vorhandenen Sicherheits-Helfer; ein realer Testfall (Innen-Schlichten, Einfahrpunkt X10/Z0 mit ZA=1/ZI=-80) erzeugt jetzt korrekt `(WARN: Startpunkt X10.000 Z0.000 liegt im Rohteil)` statt stillschweigend zu verfahren
- Untersucht, NICHT geaendert (zu riskant ohne Fachbestaetigung): `safe_z` in `generate_abspanen_gcode` wird weiterhin aus dem rohen `ZRA`/`ZRI`-Wert gebildet und ignoriert dabei das `*_absolute`-Flag - bei relativem `ZRI`/`ZRA` (z. B. `0.0`, `absolute=False`) muesste der sicherheitsrelevante Wert eigentlich `ZA + ZRI` sein (siehe bereits vorhandene, korrekte Logik in `gcode_safety._safe_axis_value()`, dort exakt so kommentiert). Ein Versuch, `generate_abspanen_gcode` auf diese bereits vorhandene Funktion umzustellen, brach 21 bestehende Tests, die alle den rohen Wert als korrekt voraussetzen - die Aenderung wurde verworfen und stattdessen als offener, mit Fachwissen zu klaerender Punkt in `TODO.md` dokumentiert (gleiche Kategorie wie die bereits dokumentierte G71/G72-Materialmodell-Unsicherheit)
- Tests: `tests/test_parting_slice.py` um `test_internal_finish_entry_uses_checked_approach_not_raw_diagonal_move` erweitert; Referenzdatei `ngc/Kontur_Radius_Fase.ngc` an die jetzt sicherere Schlicht-Einfahrt angepasst; Stand `271 passed, 1 skipped`
- Fix (Datenintegritaet, Vorschau): `build_program_data()` (vor jedem Speichern aufgerufen) hat abgeleitete Geometrie bisher nicht aufgefrischt - nur `handle_load_program()` tat das ueber `_rebuild_all_operation_geometry()`. Wurde eine Kontur bearbeitet, ohne dass ein davon abhaengiger Abspanen-Step zwischenzeitlich erneut ausgewaehlt wurde, landete die veraltete Kontur-Geometrie (`params["source_path"]`) im gespeicherten Programm. Die G-Code-Erzeugung selbst war davon nicht betroffen (loest die Kontur beim Generieren immer frisch ueber `contour_name` auf), wohl aber die Vorschau in der "alle Steps"-Uebersicht. `build_program_data()` ruft jetzt vor dem Schreiben ebenfalls `_rebuild_all_operation_geometry()` auf
- Fix (Datenintegritaet, Vorschau): `build_abspanen_path()` (Vorschau-Geometrie fuer Abspanen-Operationen) akzeptierte nur eine flache Liste aus `(x, z)`-Punkten in `params["source_path"]`. Die tatsaechliche Quelle (`resolve_contour_path()`) liefert aber IMMER das primitiven-foermige `op.path` der referenzierten Kontur-Operation (`{"type": "line"/"arc", "p1": ..., "p2": ...}`) - der Tupel-Zweig griff dadurch bei keiner echten Kontur-Referenz und jede Abspanen-Vorschau in der "alle Steps"-Uebersicht war leer. `build_abspanen_path()` erkennt jetzt beide Formen (wiederverwendet `contour_features.primitive_to_points()`)
- Tests: Neue Datei `tests/test_contour_source_path_refresh.py`; `tests/test_geometry_cache_staleness.py` um zwei Tests fuer `build_abspanen_path()` (primitiven-foermig und flach) erweitert; Stand `274 passed, 1 skipped`
- Fix: Neu hinzugefuegte oder per "Step laden" eingefuegte Operationen bekamen `params["comment"]` bisher nur beim NAECHSTEN Stepwechsel/Speichern gesetzt (`sync_form_to_operation()`). Wurde ein Step danach nie erneut ausgewaehlt, blieb der Kommentar dauerhaft leer (reale Test.lse: Innen-Einstich-Step ohne jeden Kommentar). `_handle_add_operation()` und `_insert_loaded_operation()` setzen jetzt sofort einen automatischen Kommentar, falls noch keiner vorhanden ist - ein bereits vorhandener (z. B. aus der geladenen Step-Datei uebernommener) Kommentar wird nicht ueberschrieben
- Feature: Neue Plausibilitaetspruefung `_check_duplicate_operations()` in `checks.py` - meldet Operationen mit identischem Typ und identischen Bearbeitungsparametern (Kommentar/Cache-Felder wie `source_path`/`_contour_params`/`path` werden beim Vergleich ignoriert) als Hinweis. Loescht oder aendert nichts automatisch - der Nutzer entscheidet, ob eine Mehrfachverwendung beabsichtigt ist (z. B. dieselbe Nut an zwei Stellen)
- Tests: Neue Dateien `tests/test_auto_comment_on_creation.py` und `tests/test_duplicate_operation_check.py`; Stand `280 passed, 1 skipped`
- Fix: Kontur-Subroutinen (`o<n> sub ... endsub`) wurden fuer JEDE benannte Kontur unbedingt definiert, unabhaengig davon, ob ein Abspanen-Schritt sie tatsaechlich per `G71`/`G72` (`Q<num>`) referenziert. Faellt die Bearbeitung auf Move-based-Code zurueck (nicht zyklustaugliche Kontur oder `Ausgabe bevorzugen: explizit`), blieb die Definition als toter Code im Programm stehen (real reproduziert: `o101` fuer die Innenkontur "ausdrehen", nie aufgerufen). Kontur-Subroutinen werden jetzt erst NACH der Haupt-Ablauferzeugung eingehaengt und nur dann, wenn ihre Nummer tatsaechlich als `Q<num>` im generierten Code vorkommt
- Tests: Neue Datei `tests/test_unused_contour_subroutine_suppressed.py`; Referenzdatei `ngc/Abdrehen.ngc` an die jetzt fehlende (weil ungenutzte) Subroutine-Definition angepasst; Stand `282 passed, 1 skipped`
- Fix: Verschieben (`handle_move_up`/`handle_move_down`) und Loeschen (`_handle_delete_operation`) einer Operation aktualisierte bisher nur den Anzeigetext der Step-Liste, nicht den in `op.params["comment"]` gespeicherten - und in der G-Code-Ausgabe als `(STEP: ...)` verwendeten - Kommentar. Nach einer Umsortierung driftete die gespeicherte Stepnummer im Kommentar von der tatsaechlichen Position auseinander (real reproduziert: `(Step 4: ...)` direkt gefolgt von `(STEP: 5. ...)`). `renumber_operations()` (bisher definiert, aber nie aufgerufen) aktualisiert jetzt auch den gespeicherten Kommentar und wird nach Verschieben/Loeschen aufgerufen
- Fix: `sanitize_gcode_text()` transliterierte Umlaute (ä/ö/ü/ß) explizit, aber keinen Pfeil (→, U+2192). Ein gespeicherter Kommentar mit Pfeil (z. B. aus einer vor der Umstellung auf `->` gespeicherten Planen-Operation) fiel dadurch auf den generischen ASCII-Fallback zurueck, der jedes verbleibende Nicht-ASCII-Zeichen durch ein bedeutungsloses `?` ersetzt (real reproduziert: `Z 0.0→0.0` wurde zu `Z 0.0?0.0`). Pfeil wird jetzt zu `->` transliteriert, konsistent mit der bereits in den `.lng`-Dateien verwendeten Schreibweise
- Tests: Neue Datei `tests/test_comment_encoding_and_renumbering.py`; `tests/test_dirty_and_messages.py` um Stub fuer `_renumber_operations` ergaenzt; Stand `285 passed, 1 skipped`
- Fix (schwerwiegend): `emit_coolant()` verstand nur Strings (`"on"`/`"flood"`/...) und echte `bool`-Werte. Anders als bei Planen (das vorher `opt_bool()` anwendet) reichen Bohren/Einstich/Gewinde `params["coolant"]` unveraendert durch - ein gespeicherter Zahlenwert `1.0` traf dadurch weder den str- noch den bool-Zweig und fiel stillschweigend auf `M9` (AUS) zurueck, obwohl `1.0` "an" bedeuten sollte. Real reproduziert: Innen-Einstich (Op 11), Innengewinde (Op 12) und Bohren (Op 8) mit `coolant=1.0` blieben ohne Kuehlung. `emit_coolant()` behandelt numerische Werte jetzt wie `opt_bool()` (ungleich 0 = an)
- Tests: Neue Datei `tests/test_coolant_normalization.py`; Stand `288 passed, 1 skipped`
- Feature: Neue Plausibilitaetspruefung fuer Gewinde-Presets in `validate_program_setup()` - meldet, wenn die in `params["standard"]` gespeicherten Preset-Metadaten (Steigung/Nenndurchmesser) vom tatsaechlich fuer die G76-Erzeugung verwendeten `pitch`/`major_diameter` abweichen (real reproduziert: Preset "M30x3.5" mit `standard.pitch=3.5`, tatsaechlich verwendet `pitch=1.75` - vermutlich Preset gewaehlt, dann Steigung manuell ueberschrieben, ohne dass die Preset-Metadaten nachgezogen wurden). Meldet nur, aendert nichts automatisch - unklar, welcher Wert gewollt ist
- Tests: Neue Datei `tests/test_thread_preset_consistency_check.py`; Stand `292 passed, 1 skipped`
- Untersucht, NICHT vollstaendig behoben (Geometrie-Splicing zu riskant ohne Backplot-Verifikation): DIN-Freistich-Features in Kontur-Segmenten (`din_relief`) erzeugen nur dann tatsaechlich Geometrie, wenn das betroffene Segment das ABSOLUT ERSTE oder LETZTE Segment der GESAMTEN Kontur ist (`contour_logic.py`, Zeilen ~244-247: `if anchor_mode == "end" and idx != len(segments) - 1: continue`). Bei einem Gewinde-Freistich MITTEN in einer laengeren Kontur (z. B. M30-Aussengewinde mit Freistich bei Z=-35, gefolgt von weiterem Wellenprofil bis Z=-60 - genau der reale Testfall) wird die Pruefung nie erfuellt und `feature_points`/`feature_primitives` bleiben leer. Eine korrekte Behebung muss die Freistich-Primitiven an der Position des EIGENEN Segment-Index in die Kontur einfuegen (nicht nur an den Gesamtkontur-Rand an-/vorhaengen) - das erfordert eine Segment-zu-Primitive-Indexzuordnung (Kantenbehandlungen wie Fase/Radius erzeugen mehrere Primitiven pro Segment) und sollte gegen eine reale DIN-76-Referenzgeometrie verifiziert werden, bevor daran etwas geaendert wird
- Feature: Neue Plausibilitaetspruefung `_check_din_relief_feature_position()` - meldet, sobald ein `din_relief`-Feature wegen der obigen Einschraenkung keine Geometrie erzeugen kann (statt wie bisher stillschweigend leer zu bleiben), inkl. Kontur-Name und betroffenem Segment
- Tests: Neue Datei `tests/test_din_relief_position_check.py`; Stand `295 passed, 1 skipped`
- Fix (schwerwiegend): Ein dedizierter Schlichtstep (`mode=finish`) mit gueltiger Bearbeitungsrichtung (`slice_strategy`) fuehrte trotzdem einen vollen `G71`/`G72`-Schruppzyklus aus, bevor der eigentliche Schlichtschnitt kam - das Material war durch einen fruaheren, separaten Schruppstep bereits abgetragen (z. B. mit eigenem Schruppwerkzeug). Die Wiederholung war unnoetig und potenziell riskant (Schlichtwerkzeug schruppt unbemerkt erneut). `mode=finish` (reiner Schlichtstep) ueberspringt den Schruppzyklus jetzt vollstaendig; `mode=rough` und `mode=rough_finish` sind unveraendert
- Tests: Neue Datei `tests/test_finish_mode_never_reroughs.py`; Stand `298 passed, 1 skipped`
- Fix: Endete die Schlichtkontur bereits genau auf `safe_z` (z. B. Konturende an der Stirnflaeche bei Z0, `ZRA`/`ZRI` ebenfalls 0), wurde trotzdem ein zusaetzliches `G0 Z{safe_z}` angehaengt - eine bedeutungslose Nullbewegung auf eine bereits erreichte Position (real reproduziert in Test.lse's Innen-Schlichten). Wird jetzt uebersprungen, wenn der letzte Konturpunkt bereits auf `safe_z` liegt
- Tests: Neue Datei `tests/test_no_redundant_zero_move_after_finish.py`; Stand `300 passed, 1 skipped`

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
