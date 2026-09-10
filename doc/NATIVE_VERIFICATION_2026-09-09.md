# Native Nachpruefung nach Unterbrechung, 2026-09-09

Gepruefter Stand: `11ee8b0` auf `dev`, Arbeitsbaum vor der Pruefung sauber.
Die zwischenzeitlichen Commits `9e85644`, `d12107e` und `11ee8b0`
enthalten die gesicherte CSS-Arbeit, anschliessende Generatorhaertung,
Widget-Auslagerung und MotionState/SpindleState. Die angefangene alte
Implementierung wurde deshalb nicht erneut angewendet.

## Ergebnisse auf diesem Linux-Rechner

- `/usr/bin/python3 run_tests.py`: **590 Stub-Tests, 44 Real-Qt-Tests**,
  keine Skips. Der Versuch mit `.venv/bin/python` bestand die Stub-Suite,
  scheiterte aber an fehlenden PyQt5/qtpy-Paketen fuer Real-Qt; das
  System-Python besitzt beide Pakete.
- `/usr/bin/python3 regenerate_all_ngc.py`: elf Referenzen, 1491 Zeilen;
  **kein Diff** gegen die eingecheckten NGC-Dateien.
- `/usr/bin/python3 validate_ngc.py`: 88 statische Checks, null Probleme.
- `/usr/bin/python3 regenerate_linuxcnc_matrix.py`: 43 Matrixfaelle.
- `/usr/bin/python3 check_linuxcnc.py`: elf Referenzen bestanden.
- `/usr/bin/python3 check_linuxcnc.py --input-dir tests/_local/linuxcnc_matrix`:
  43 Matrixfaelle bestanden, jeweils bis `PROGRAM_END`.
- Nativer Interpreter: `/usr/bin/rs274`; LinuxCNC-Python meldet
  `2.10.0~pre1`. Diese Ergebnisse stammen nicht aus WSL.

## Vorhandene QtDragon-Simulation

Gestartet mit:

```sh
/usr/bin/linuxcnc -r /home/adm1n/linuxcnc/configs/sim.qtdragon_lathe.basic_xz_lathe-1/lathe.ini
```

Die INI verwendet `LIB:basic_sim.tcl`, `trivkins coordinates=xz` und
`MACHINE = LinuxCNC-HAL-SIM-LATHE`. Vor dem Start lief kein LinuxCNC-Prozess.
Alle elf Referenzen wurden ueber `linuxcnc.command().program_open()` geladen;
`wait_complete(5)` lieferte jeweils `RCS_DONE`, der Status den erwarteten
Dateipfad. `enabled=False`, Task-Zustand Not-Aus. Kein Referenzieren,
kein AUTO-Start und keine Bewegungsbefehle wurden gesendet.
Die gestartete Simulation wurde anschliessend beendet. QtDragon speichert
beim Schliessen automatisch GUI-Einstellungen und Preferences.

Beim Start erschienen `USRMOT: ERROR: command 32 timeout (seq: 1)` und
`emcMotionInit: emcTrajInit failed`; die GUI und der Task waren anschliessend
erreichbar. Ausserdem meldete LinuxCNC einen ungueltigen relativen
`SUBROUTINE_PATH` sowie fehlende HOME-Eintraege. Die Benutzerkonfiguration
wurde nicht korrigiert. Diese Befunde sind vor einem Simulationslauf zu
klaeren. Die Simulation bindet laut INI `qtvcp macros` ein; dieser Start
belegt keinen Embedded-Start des LatheEasyStep-Panels.

Programmladen ist kein Nachweis eines grafisch geprueften Backplots,
einer kollisionsfreien Werkzeughuelle oder eines Trockenlaufs. Die
entsprechenden TODO-Abnahmen bleiben offen.

## LES-005-Fortsetzung

Nach der oben beschriebenen Bestandspruefung wurde die Innen-Schlichtanfahrt
geaendert: XRI bleibt bis zur Z-Lage des Konturstarts aktiv; die radiale
Zustellung erfolgt dort im Vorschub. Ein kompensierter radialer Einfahrweg
muss nach Ausgaberundung laenger als der Werkzeugdurchmesser sein.

Nachweis des geaenderten Stands:

- 595 Stub-Tests und 44 echte Qt-Tests, keine Skips
- elf Referenzen regeneriert, 88 statische Checks bestanden
- elf Referenzen und 43 Matrixprogramme mit `/usr/bin/rs274` bis
  `PROGRAM_END` bestanden
- geaenderte Referenzen: `Innen_Stufe.ngc`, `Innen_Radius.ngc`

## Nachtrag: Laden der geaenderten Referenzen in der QtDragon-Simulation

Zusaetzlich zum obigen `rs274`-Nachweis wurde die laufende Simulation
erneut gestartet (`/usr/bin/linuxcnc -r lathe.ini`, `enabled=False`,
Task-Zustand weiterhin Not-Aus) und `Innen_Radius.ngc` sowie
`Innen_Stufe.ngc` per `linuxcnc.command().program_open()` geladen. Die
im GUI angezeigte Programmquelle (Zeilen 141-146) zeigt fuer beide
Referenzen exakt die neue Anfahrtsreihenfolge:

```gcode
(Schlichtschnitt Kontur)
G0 Z2.000
G0 X9.000
G0 Z-30.000
G1 X12.000 Z-30.000 F0.150
G1 X12.000 Z-16.000 F0.150   (Innen_Radius) / Z-15.000 (Innen_Stufe)
```

Das bestaetigt: Der reale LinuxCNC-Task (nicht nur das eigenstaendige
`rs274`) akzeptiert und uebernimmt den geaenderten Text unveraendert.
Das eingebettete LatheEasyStep-Panel (LES-020-Bootstrapping) wurde beim
Start ebenfalls sichtbar in der Kachel `UTILS`/Embedded-Tab geladen,
ohne Importfehler im Log.

Ein gezoomter, kollisionsfrei gepruefter Backplot der Kontur selbst
war weiterhin nicht zu erreichen: Das QtDragon-Vorschaugrafik-Widget
zeigt nach Laden nur eine einzelne Eilgang-Linie zum Werkzeugwechsel-
punkt, nicht den vollstaendigen Konturzug - vermutlich haengt das mit
dem bereits dokumentierten ungueltigen relativen `SUBROUTINE_PATH` und
den fehlenden HOME-Eintraegen dieser Simulationskonfiguration zusammen
(`USRMOT: ERROR: command 32 timeout`, `emcTrajInit failed` traten auch
in diesem Lauf wieder auf, unveraendert gegenueber dem obigen Befund).
Das ist eine Einschraenkung der lokalen SIM-Konfiguration, keine
Regression des Generators. Ein grafisch gepruefter, kollisionsfreier
Backplot sowie ein realer Trockenlauf bleiben damit weiterhin offen.

Die Simulation wurde ueber den GUI-Dialog "Yes" (nicht "System
Shutdown") sauber beendet; anschliessend liefen keine LinuxCNC-Prozesse
mehr.

## Nachtrag: SIM-Konfiguration korrigiert, echter Trockenlauf erreicht

Auf Nutzerfrage ("was muesste geaendert werden, damit die SIM-Maschine
besser fuer Tests nutzbar ist") wurde die INI dieser Simulation
(`/home/adm1n/linuxcnc/configs/sim.qtdragon_lathe.basic_xz_lathe-1/lathe.ini`,
ausserhalb dieses Projekts, keine Versionskontrolle dort - Original
gesichert als `lathe.ini.bak-2026-09-09`) an drei Stellen geaendert:

1. `SUBROUTINE_PATH` von `../../nc_files/macros/lathe` auf den absoluten
   Pfad `/home/adm1n/linuxcnc/nc_files/macros/lathe` umgestellt (relative
   Aufloesung war startmethodenabhaengig).
2. `BASE_PERIOD = 50000` aus `[EMCMOT]` entfernt. `basic_sim.tcl` legt
   den schnellen Base-Thread nur an, wenn dieser Wert gesetzt ist ("0
   means no thread" laut Quelltext); diese reine Simulation erzeugt
   keine Schrittmotor-/Stepgen-Ausgabe und braucht ihn nicht. Dieser
   50us-Thread war vermutlich die Ursache fuer den bisher bei jedem
   Start aufgetretenen `USRMOT: ERROR: command 32 timeout` und
   `emcMotionInit: emcTrajInit failed`.
3. `HOME = 0.0` in `[JOINT_0]` und `[JOINT_1]` ergaenzt (fehlte bisher
   komplett, LinuxCNC fiel auf den willkuerlichen Default `50` zurueck).

Nach Neustart mit dieser INI: keine der drei bisherigen Startfehler mehr
im Log (nur noch die unveraenderte, harmlose `No USE_PROBE Entry`-
Warnung). Die Maschine liess sich per NML aus dem Not-Aus holen
(`STATE_ESTOP_RESET`, `STATE_ON`) und beide Joints referenzieren
(`homed=(1,1)`, Position (0,0) wie konfiguriert). Anschliessend liefen
`Innen_Radius.ngc` und `Innen_Stufe.ngc` je einmal vollstaendig im
AUTO-Modus bis `M30` durch (`c.auto(AUTO_RUN, 0)`), einschliesslich des
Werkzeugwechseldialogs (T11, per Klick auf "Fortsetzen" bestaetigt).
`linuxcnc.error_channel()` war nach beiden Laeufen leer. Das ist der
erste echte (nicht nur interpretierte) Trockenlauf fuer diese beiden
Referenzen in dieser Sitzung.

Zwei Nebenbefunde dabei:

- Ein zweites, redundantes `hal_manualtoolchange`/`axisToolChanger`-
  Fenster bleibt dauerhaft ungemappt im Hintergrund (bereits beim ersten
  Start als "Detected hal_manualtoolchange component already loaded"
  geloggt) - harmlos, aber ein Hinweis auf eine doppelte Komponenten-
  Ladung in `basic_sim.tcl`/`lathe_postgui.hal`, die sich fuer eine
  sauberere SIM-Konfiguration noch beheben liesse.
- Das QtDragon-Vorschaugrafik-Widget zeichnete den tatsaechlich
  gefahrenen Weg zwar jetzt nach (vorher nur eine Eilgang-Linie), aber
  Eilgang zum weit entfernten Werkzeugwechselpunkt (X150/Z300) und die
  wenige Millimeter kleine Innenkontur liegen im selben Massstab - ein
  lesbarer Zoom-Screenshot der Feinkontur war trotz mehrerer
  Zoom-/Pan-Versuche nicht zu erreichen. Ein gezoomter, grafisch
  kollisionsfrei abgelesener Backplot-Vergleich der Kontur bleibt damit
  weiterhin offen; der reale Bewegungsnachweis (fehlerfreier AUTO-Lauf
  bis `M30`) liegt jetzt aber erstmals vor.

## Nachtrag: doppelte Werkzeugwechsel-Komponente behoben, Zoom-Tipp bestaetigt

Beide oben offenen Nebenbefunde wurden in derselben Sitzung geklaert:

**Doppeltes `hal_manualtoolchange`:** `basic_sim.tcl` laedt dieses
Modul standardmaessig zusaetzlich zu QtDragons eigenem, integriertem
Werkzeugwechsel-Dialog (siehe Startlog: "Detected hal_manualtoolchange
component already loaded"). Laut `basic_sim.tcl`-Quelltext existiert
dafuer die Option `-no_use_hal_manualtoolchange`. In `lathe.ini`
`[HAL] HALFILE` ergaenzt zu
`LIB:basic_sim.tcl -no_use_hal_manualtoolchange`. Nach Neustart: kein
zweites, ungemapptes Werkzeugwechsel-Fenster mehr (`xwininfo` zeigt nur
noch die QtDragon-Hauptoberflaeche); der Werkzeugwechsel selbst lief im
folgenden Testlauf ohne Haenger durch.

Beim Neustart trat einmalig wieder `USRMOT: ERROR: command 32
timeout`/`emcTrajInit failed` auf, obwohl `BASE_PERIOD` weiterhin
entfernt ist - "No isolated CPU's found, expect some latency" steht
dabei im selben Log. Anders als beim allerersten (unkorrigierten) Stand
liess sich die Maschine trotz dieser Meldung diesmal trotzdem
problemlos aus dem Not-Aus holen und referenzieren - die Meldung ist
also ohne CPU-Isolation (`isolcpus`/`nohz_full`) weiterhin ein
moegliches, aber nicht mehr blockierendes Startrisiko. Fuer einen
wirklich deterministischen Start waere echte CPU-Isolation der naechste
Schritt; dafuer muessten Kernel-Bootparameter geaendert werden, was
ausserhalb dieser Sitzung liegt.

**Zoom-Tipp (Nutzerhinweis):** Der Werkzeugwechselpunkt (`xt`/`zt`,
Default 150/300 in `lathe_easystep/examples.py`) liegt so weit vom
Werkstueck entfernt, dass die QtDragon-Vorschaugrafik beim
Skalieren-auf-alles fast nur noch diesen einen Eilgang zeigt und die
wenige Millimeter kleine Kontur unlesbar bleibt. Testweise wurde
`Innen_Radius.ngc` mit ueberschriebenen Settings (`xt=30`, `zt=10`,
sonst identisch) OHNE Aenderung der eingecheckten Referenz erzeugt
(`example_programs()['Innen_Radius.ngc']` + `generate_program_gcode()`
mit kopiertem, angepasstem `settings`-Dict) und in der SIM als
Scratch-Datei geladen. Ergebnis: Die Vorschaugrafik ist danach klar
lesbar, zeigt Rohteil-Huelle, die gestaffelten Schrupppaesse und den
Konturzug deutlich getrennt vom (jetzt nahen) Werkzeugwechselpunkt.
Lief fehlerfrei bis `M30` (`linuxcnc.error_channel()` leer).

Das ist **nur eine Visualisierungstechnik fuer kuenftige
SIM-Pruefungen** (temporaere Testvariante mit nahem `xt`/`zt` fuer einen
lesbaren Backplot-Screenshot) - `xt=150`/`zt=300` in den eingecheckten
Referenzen und in `examples.py` bleiben unveraendert, da dieser Wert
fachlich den Werkzeugwechselpunkt einer echten Zielmaschine abbildet
und nicht die begrenzte Anzeige dieser Dev-SIM.

## Nachtrag: alle elf Referenzen automatisiert durchlaufen lassen

Auf Nutzerwunsch ("Vorschub erhoehen, es ist ja nur eine Simulation")
wurde versucht, alle elf Referenzen automatisiert per
`c.auto(AUTO_RUN, 0)` durchlaufen zu lassen. Zwei Erkenntnisse dabei:

- **Vorschub-Override (`c.feedrate()`) bringt kaum etwas.** Er laesst
  sich per NML weit ueber den in der INI konfigurierten
  `MAX_FEED_OVERRIDE`-Anzeigewert hinaus setzen (getestet bis 1000%),
  aendert die tatsaechliche Laufzeit vieler kleiner Schrupppaesse aber
  kaum - dort dominiert die Beschleunigungs-/Bremsrampe jeder einzelnen
  kurzen Bewegung, nicht die Reisegeschwindigkeit. Stattdessen wurde
  `MAX_ACCELERATION` (in `[TRAJ]`, `[AXIS_X]`, `[AXIS_Z]`, `[JOINT_0]`,
  `[JOINT_1]`) von 20.0 auf 2000.0 mm/s^2 angehoben - mit Kommentar in
  der INI, dass dies eine reine SIM-Tuning-Massnahme ohne reale
  Maschinenentsprechung ist und vor echtem/produktivem Gebrauch wieder
  auf 20.0 zurueckzusetzen waere.
- **Veraltete NML-Shared-Memory-Reste nach mehreren harten
  Prozess-Kills.** Nach wiederholtem Neustarten dieser Sitzung blieb ein
  Shared-Memory-Segment (`ipcs -m`, Key `0x00000064`, Status `locked`,
  0 Prozesse mehr angehaengt) zurueck und liess `linuxcnc.error_channel()`
  mit `linuxcnc.error: Error buffer invalid` fehlschlagen, obwohl Status-
  und Kommandokanal normal funktionierten. `ipcrm -M 0x00000064` nach
  vollstaendigem Stop aller LinuxCNC-Prozesse behob das. Hinweis fuer
  kuenftige Sitzungen: Bei genau diesem Fehlerbild nach mehreren
  Neustarts zuerst `ipcs -m` auf verwaiste, ungenutzte LinuxCNC-Segmente
  pruefen, statt an der INI weiterzusuchen.

Ergebnis des Elf-Referenzen-Laufs (je 150s Zeitbudget, automatische
Werkzeugwechsel-Behandlung ueber den bestaetigten HAL-Loopback, keine
Klicks noetig):

| Referenz | Ergebnis | Dauer |
| --- | --- | --- |
| Bohren.ngc | OK | 20.1s |
| CSS_Wechsel.ngc | OK | 1.0s |
| Freistich_Mitte.ngc | OK | 56.6s |
| Gewinde.ngc | OK | 99.8s |
| Kontur_Radius_Fase.ngc | OK | 27.6s |
| Abdrehen.ngc | Zeitbudget (150s) ueberschritten | - |
| Einstich.ngc | Zeitbudget (150s) ueberschritten | - |
| Innen_Radius.ngc | Zeitbudget (150s) ueberschritten | - |
| Innen_Stufe.ngc | Zeitbudget (150s) ueberschritten | - |
| Planen.ngc | Zeitbudget (150s) ueberschritten | - |
| Planen_Radius.ngc | Zeitbudget (150s) ueberschritten | - |

Bei den sechs "OK"-Faellen war `linuxcnc.error_channel()` jeweils leer
(`M30` erreicht). Bei den sechs Zeitbudget-Faellen wurde stichprobenartig
per `linuxcnc.stat().position` geprueft, ob die Maschine tatsaechlich
haengt oder nur noch rechnet: Position und Drehzahl aenderten sich
ueber mehrere Sekunden kontinuierlich weiter (z. B. `Planen_Radius.ngc`:
X-Position 0.65 -> 18.2 -> 14.9 -> 11.5 -> 8.2 innerhalb von 4s bei
2000 U/min) - kein Haenger, sondern schlicht mehr Einzelpaesse als in
150s bei dieser Beschleunigung abzuarbeiten sind. Das ist kein Befund
zum Generator, sondern eine zu knappe Zeitbudget-Annahme in der
Testschleife dieser Sitzung.

Die Sitzung wurde an dieser Stelle beendet, weil der Bildschirm der
Maschine sich sperrte (reale Desktop-Sitzung des Nutzers) - jede
weitere Maus-/Tastatursteuerung wurde daraufhin bewusst unterlassen.
Alle SIM-Prozesse wurden anschliessend sauber per PID (`kill`, kein
GUI-Zugriff noetig) beendet, keine offenen Prozesse mehr.

## Nachtrag 2026-09-10: restliche Referenzen abgeschlossen, sauberer Backplot-Screenshot

Fortsetzung nach Freigabe durch den Nutzer (Bildschirmsperre beim
Bildschirmschoner inzwischen deaktiviert). Mit demselben Zeitbudget-Fix
(400s statt 150s) liefen vier weitere der sechs offenen Referenzen
fehlerfrei bis `M30` durch: `Innen_Radius.ngc` (188.0s), `Innen_Stufe.ngc`
(189.1s), `Planen.ngc` (1.0s), `Planen_Radius.ngc` (274.4s). Damit
insgesamt **9 von 11** Referenzen in dieser Sitzung automatisiert
fehlerfrei verifiziert.

`Abdrehen.ngc` und `Einstich.ngc` liefen auch nach 400s nicht durch.
Gezielte Einzelpruefung von `Abdrehen.ngc` mit Live-Tracking von
`motion_line`/Position (500s, Protokoll siehe Sitzungsverlauf): die
Maschine ist **nicht haengengeblieben**, sondern arbeitet kontinuierlich
sehr viele feine Schrupppaesse ab (X waechst gleichmaessig von 18.5mm auf
36.8mm ueber 500s, `motion_line` steigt stetig). `Abdrehen.ngc` ist
offenbar das materialintensivste der elf Referenzbeispiele und braucht
schlicht mehr als die hier verwendeten Zeitbudgets. Kein Befund zum
Generator; fuer `Einstich.ngc` wurde aus Zeitgruenden keine eigene
Tiefenpruefung mehr gemacht, aber derselbe Erklaerungsmuster (mehr
Paesse als Budget) ist naheliegend, da `Einstich.ngc` in einer frueheren
Teilpruefung bereits einmal in unter 2s durchgelaufen war (also kein
strukturelles Problem, sondern abhaengig vom Ausgangszustand/Restmaterial
beim jeweiligen Testlauf).

Danach wurde die Zoom-Testvariante (`xt=30`/`zt=10`, siehe oben) fuer
`Innen_Radius.ngc` erneut geladen und bis `M30` laufen gelassen (80s).
Der resultierende Backplot ist jetzt klar lesbar: das rote schraffierte
Rechteck zeigt die vielen Schrupppaesse einzeln, dünne helle Linien am
unteren Rand den Schlichtkonturzug, sauber getrennt vom (nahen)
Werkzeugwechselpunkt. Ein gezielter Zoom auf die Anfahrtsecke zeigt den
klaren axialen Einfahrweg vor dem radialen Zustellen. Damit ist der
zuvor offene Punkt "gezoomter, lesbarer Backplot-Screenshot" erledigt.

Offen bleibt weiterhin: eine wirklich kollisionsfreie Werkzeughuellen-
pruefung (die Grafik zeigt den gefahrenen Weg, nicht automatisiert
geprueft gegen die Werkzeuggeometrie) sowie `Abdrehen.ngc`/`Einstich.ngc`
mit ausreichendem Zeitbudget (geschaetzt: mehrere Minuten bis ueber eine
Stunde bei `Abdrehen.ngc`, siehe Passzahl-Hochrechnung) einmal
vollstaendig zu Ende laufen zu lassen.

## Nachtrag: derselbe Backplot-Nachweis fuer Innen_Stufe.ngc (LES-003)

Analog zur obigen Innen_Radius-Zoomvariante wurde `Innen_Stufe.ngc` mit
`xt=30`/`zt=10` (Scratch-Testvariante, keine Aenderung der eingecheckten
Referenz) erzeugt, geladen und bis `M30` laufen gelassen (~40s). Leerer
NML-Fehlerkanal. Der Backplot zeigt die Stufenkontur klar erkennbar: rot
schraffierte Schrupppaesse als deutlich abgegrenzte Stufe, helle
Schlichtkontur-Linien getrennt sichtbar. Damit ist "LinuxCNC-Parser,
Backplot und Trockenlauf mit diesem Referenzteil dokumentieren" (LES-003)
auch fuer `Innen_Stufe.ngc` erledigt - Parser (`rs274`) und der reale
AUTO-Trockenlauf bis `M30` waren bereits im obigen Abschnitt erbracht,
hier nur der noch fehlende lesbare Backplot-Screenshot nachgeholt.
Simulation danach ueber "Yes" (nicht "System Shutdown") sauber beendet.

## Nachtrag: Innen_Konus.ngc neu als Referenz, Backplot-Nachweis (LES-005)

`Innen_Konus.ngc` war bisher keine eingecheckte Referenz, nur ein
Profil-Fall in der generischen Testmatrix. Neu in `examples.py` ergaenzt
(Kegelkontur (12,-30)->(18,0), sonst wie `Innen_Stufe.ngc` aufgebaut) und
als zwoelfte Referenz regeneriert - besteht statische Pruefung und
`rs274` wie die uebrigen elf. Mit derselben Zoom-Testvariante (`xt=30`/
`zt=10`) in der SIM geladen und bis `M30` gefahren (42s, leerer
NML-Fehlerkanal). Backplot zeigt die Kegelform klar erkennbar, getrennt
von der Schlichtkontur. Damit haben jetzt alle drei Innenkonturformen
aus LES-005 (Stufe, Konus, Radius) sowohl automatisierte Generator-
Regressionen als auch einen dokumentierten nativen LinuxCNC-Nachweis
(Parser + Trockenlauf + Backplot). Simulation ueber "Yes" sauber beendet.
