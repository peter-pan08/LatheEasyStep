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
