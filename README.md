Lathe EasyStep
==============

Current Version: `0.7.0`
Status Date: `2026-07-08`
Primary Test Branch: `DEV`

Deutsch
-------

## Was ist Lathe EasyStep?

Lathe EasyStep ist ein konversationelles Drehbank-Panel fuer LinuxCNC. Typische
Drehbearbeitungen koennen direkt an der Maschine erstellt, geprueft und als
G-Code ausgegeben werden, ohne externes CAM.

Der Fokus liegt auf:

- klaren, reproduzierbaren Ablaeufen
- sicheren Werkzeugbewegungen
- sofortiger grafischer Rueckmeldung
- wiederverwendbaren Bearbeitungsschritten

Lathe EasyStep ist fuer den Werkstattalltag gedacht, nicht als vollwertiger
CAM-Ersatz.

## Projektstatus

Stand: Version 0.7.0, 8. Juli 2026

Das Projekt ist aktiv in Entwicklung, aber die technische Basis ist deutlich
weiter als ein reiner Prototyp:

- Generator- und Sicherheitsphasen fuer Werkzeugwechsel, Anfahrten,
  Rueckzuege und Modals sind umgesetzt
- Save/Load fuer einzelne Steps und komplette Programme ist vorhanden
- Embedded-Betrieb in LinuxCNC wurde gezielt stabilisiert
- Spannfutter-, No-Go- und Sicherheitslogik sind erweitert worden
- Handler-, G-Code-, Kontur- und Vorschau-Logik wurden fuer Version 0.7.0 deutlich weiter modularisiert
- die aktuelle Refactor-Basis ist mit `171 passed` validiert

Der derzeit dokumentierte Arbeitsstand ist `Version 0.7.0`.

## Branch-Status

`main` gilt als lauffaehige Basis des Projekts.

Neue Aenderungen sollen zuerst auf dem Branch `DEV` getestet werden. Erst wenn
die Anpassungen dort fachlich und technisch verifiziert wurden, werden sie in
den Hauptbranch migriert.

## Wichtiger Hinweis

Es gibt keine Garantie auf vollstaendige oder fehlerfreie Funktion.

Der erzeugte G-Code muss vor der Nutzung geprueft werden. Vor dem Einsatz an
der realen Maschine sollte:

- der Code verstanden werden
- eine Simulation oder ein Trockenlauf durchgefuehrt werden
- sichergestellt sein, dass Werkzeug, Spannmittel und Maschine geeignet sind

Die Nutzung erfolgt auf eigene Verantwortung.

## Einbindung in LinuxCNC / Standalone-Start

Lathe EasyStep ist als QTVCP-Panel aufgebaut. Die zugehoerigen Dateien in
diesem Verzeichnis sind:

- `lathe_easystep.ui`
- `lathe_easystep_handler.py`

### Einbau als eingebettetes Panel in die LinuxCNC-INI

In der LinuxCNC-INI kann das Panel als zusaetzlicher Tab eingebunden werden.
Ein funktionierendes Beispiel aus der vorhandenen Konfiguration ist:

```ini
EMBED_TAB_NAME=Macros
EMBED_TAB_COMMAND=qtvcp -x {XID} -c easystep ~/linuxcnc/configs/Drehbank/macros/LatheEasyStep/lathe_easystep
EMBED_TAB_LOCATION=tabWidget_utilities
```

Wichtig dabei:

- `-x {XID}` bettet das QTVCP-Fenster in den LinuxCNC-Tab ein
- `-c easystep` setzt den Komponentennamen
- der Pfad zeigt auf das Panel `lathe_easystep`
- `EMBED_TAB_LOCATION` muss zu dem Tab-Container deiner LinuxCNC-Oberflaeche passen

### Standalone starten

Zum direkten Testen ausserhalb von LinuxCNC kann das Panel auch separat mit
`qtvcp` gestartet werden:

```bash
cd ~/linuxcnc/configs/Drehbank/macros/LatheEasyStep
qtvcp -c easystep -u ./lathe_easystep_handler.py ./lathe_easystep.ui
```

Nuetzlich fuer Debugging:

```bash
qtvcp -d -c easystep -u ./lathe_easystep_handler.py ./lathe_easystep.ui
```

Voraussetzung ist eine LinuxCNC-/QTVCP-Installation, in der `qtvcp` im `PATH`
liegt.

## Grundsaetzlicher Workflow

Die Bedienung folgt einem festen Ablauf ueber die Reiter. Alle Eingaben wirken
sich direkt auf Vorschau und Step-Verwaltung aus.

## Reiter "Programm"

Hier werden die globalen Programmeinstellungen festgelegt:

- Sicherheitsabstaende und Rueckzugsebenen
- Rohteilgeometrie
- Nullpunkt und Bezug
- maximale Drehzahlen
- Werkzeugdatenbank
- Maschinenprofil, Spannfutter und Spannart

## Reiter "Planen"

Hier wird das Planen der Stirnflaeche definiert:

- zu planender Bereich
- Schruppen, Schlichten oder kombiniert
- optionales Schlichtaufmass
- Kantenform und Kantenmass

## Step-Verwaltung

Links befindet sich die Liste aller Bearbeitungsschritte.

Moeglich sind:

- einzelne Steps speichern und wieder laden
- komplette Programme speichern und wieder laden
- bestehende Programme gezielt aendern
- verknuepfte Steps und Programme ueber `Aenderungen speichern` direkt aktualisieren

Wichtig fuer den aktuellen Workflow:

- jeder Bearbeitungsschritt soll eine eigene Step-Datei besitzen
- beim Programmspeichern werden die verknuepften Step-Dateien im Programm mit abgelegt
- bestehende Programme koennen dadurch spaeter geladen und gezielt in ihre Einzel-Steps zurueckgeschrieben werden
- Dateidialoge starten immer im zuletzt verwendeten Ordner

## Reiter "Kontur"

In diesem Reiter wird nur Geometrie definiert, keine Bearbeitung.

Unterstuetzt werden:

- nur X
- nur Z
- X und Z kombiniert
- Kanten als Fase oder Radius
- Innen-/Aussenseite pro Radius

## Reiter "Abspanen"

Hier wird eine zuvor definierte Kontur bearbeitet:

- Auswahl der Kontur ueber ihren Namen
- innen oder aussen
- Schruppen oder Schlichten
- Werkzeug
- Zustellung, Vorschub und Drehzahl

## Reiter "Gewinde"

Dieser Reiter dient zum Gewindeschneiden:

- Innen- oder Aussengewinde
- Werkzeugauswahl
- vollstaendige G76-Parameter
- Presets fuer metrische Gewinde und Trapezgewinde

## Reiter "Einstich / Abstich"

Hier werden Einstiche und Abstiche definiert:

- innen oder aussen
- reduzierter Vorschub
- reduzierte Drehzahl ab definierter Position

## Reiter "Bohren"

Der Bohr-Reiter ist bewusst einfach gehalten:

- Werkzeug auswaehlen
- normal bohren
- Spanbruch
- Spanbruch mit Rueckzug

## Reiter "Keilnut"

Dieser Reiter ist fuer Nutenstossen und spaetere Verzahnungsfunktionen
vorgesehen.

Aktueller Stand:

- Werkzeugauswahl vorhanden
- Startwinkel und Winkelversatz fuer Wiederholungen vorhanden
- Winkelversatz bedeutet Abstand der Nutmitten von Wiederholung zu Wiederholung
- Winkeleingaben werden in Grad gefuehrt
- keine unnoetige Drehzahl-Eingabe fuer stillstehendes Werkstueck beim Nutenstossen
- geladene Programmdaten fuer Keilnut werden wieder sichtbar in die Eingabefelder geschrieben
- Aenderungen im Keilnut-Reiter wirken wieder auf Vorschau, Step-Datei und Programmspeicherung

## Vorschau und Schnittansicht

Die Vorschau besteht derzeit aus einer Seitenansicht des Werkstuecks und einer
zusaetzlichen Vorderansicht fuer einen frei waehlbaren Z-Schnitt.

Aktueller Stand:

- die Seitenansicht bleibt sichtbar
- die Schnittlage wird in der Seitenansicht farblich markiert
- die Schnittlage kann direkt in der Seitenansicht verschoben werden
- die Vorderansicht wird aus dem gesamten Programm berechnet
- die Vorderansicht nutzt den groessten Werkstueckdurchmesser als feste Referenz
- die aktuelle Endgeometrie wird in der Vorderansicht zusaetzlich flaechig hervorgehoben

## Werkzeugtabelle

Die Werkzeugtabelle wird wie bisher manuell geladen, der zuletzt verwendete
Pfad wird aber gespeichert und beim naechsten Start des Panels automatisch
wieder verwendet.

## Programmdaten und Reiterbindung

Die Eingabemasken arbeiten immer gegen die aktuell aktive Operation in der
Step-Liste.

Fuer den aktuellen Stand wurde diese Kopplung vor allem fuer `Keilnut` und den
Programmkopf nachgezogen, damit geladene Programme wieder nachvollziehbar
editiert werden koennen.

## Aktuelle Prioritaeten

Die naechsten sinnvollen Arbeiten im Projekt sind:

1. Handler-Logik weiter modularisieren
2. Preview robuster machen
3. Embedded- und Standalone-Verhalten weiter angleichen
4. Dokumentation und Statusdokumente konsistent halten
5. reale Werkstattablaeufe und Maschinenprofile weiter verifizieren

## Regressionstests und Smoke-Test

Der aktuelle Refactor-Stand wird nicht nur mit Unit-Tests, sondern auch mit
Referenzprogrammen abgesichert.

- `pytest -q`
- `python3 regenerate_all_ngc.py`

Die Referenzprogramme liegen unter `ngc/` und decken derzeit ab:

- Planen
- Bohren
- Gewinde
- Einstich
- Abspanen aussen
- Kontur mit Radius/Fase

## Known Limitations

Der aktuelle Stand ist funktional, aber noch nicht fachlich abgeschlossen.

- `slicer.py` dient jetzt weitgehend als Kompatibilitaetsschicht, enthaelt aber noch Altbestand und sollte langfristig weiter ausgeduennt werden
- die neue Modulstruktur ist funktional, aber noch nicht in allen Bereichen in kleinere, fachlich scharf getrennte Teilmodule zerlegt
- die Schnittansicht ist funktional, aber die visuelle Darstellung komplexer Endgeometrien ist noch nicht in allen Faellen endgueltig abgestimmt
- reale Maschinen- und Kollisionsfaelle muessen weiterhin an Beispielteilen und Trockenlaeufen verifiziert werden

## Geplante Modulaufteilung

Fuer den Stand `0.7.0` ist bereits ein grosser Teil der Logik aus
`lathe_easystep_handler.py` und `slicer.py` in eigene Module ausgelagert
worden. Die sinnvolle Zielstruktur ist:

```text
lathe_easystep/
  model.py
  tools.py
  persistence.py
  storage.py
  ui_program.py
  ui_operations.py
  ui_preview.py
  gcode/
    program.py
    safety.py
    face.py
    contour.py
    roughing.py
    drill.py
    thread.py
    groove.py
    keyway.py
  preview/
    widget.py
    geometry.py
  ui/
    handler.py
    translations.py
```

English
-------

## What is Lathe EasyStep?

Lathe EasyStep is a conversational turning panel for LinuxCNC. It is intended
to create common lathe operations directly at the machine, with immediate
preview and reusable steps, without relying on external CAM.

The main focus is:

- safe tool motion
- deterministic workflows
- direct visual feedback
- reusable machining steps

## Project Status

Current documented state: Version 0.7.0, July 8, 2026.

The project is still under active development, but it is no longer just an
early prototype:

- core G-code generation and safety phases are implemented
- save/load for single steps and complete programs is available
- LinuxCNC embedded usage was stabilized
- chuck, no-go and machine-safety logic was expanded
- handler, generator, contour and preview logic have been modularized substantially further for version 0.7.0
- the current refactor baseline is validated with `171 passed`

## Branch Status

`main` is the stable runnable base.

New work is expected to be tested on `DEV` first. Only verified changes should
be merged back into `main`.

## Important Notice

No guarantee is given that generated code is complete or error-free.

Before using generated G-code on a real machine, you should:

- understand the code
- run a simulation or dry run
- verify that machine, tooling and workholding are suitable

Use at your own risk.

## LinuxCNC Integration / Standalone Start

Lathe EasyStep is built as a QTVCP panel. The relevant files in this directory
are:

- `lathe_easystep.ui`
- `lathe_easystep_handler.py`

### Embedded inside a LinuxCNC INI

Example:

```ini
EMBED_TAB_NAME=Macros
EMBED_TAB_COMMAND=qtvcp -x {XID} -c easystep ~/linuxcnc/configs/Drehbank/macros/LatheEasyStep/lathe_easystep
EMBED_TAB_LOCATION=tabWidget_utilities
```

Notes:

- `-x {XID}` embeds the QTVCP window into a LinuxCNC tab
- `-c easystep` sets the component name
- the path points to the `lathe_easystep` panel
- `EMBED_TAB_LOCATION` must match the tab container of your LinuxCNC screen

### Standalone Start

```bash
cd ~/linuxcnc/configs/Drehbank/macros/LatheEasyStep
qtvcp -c easystep -u ./lathe_easystep_handler.py ./lathe_easystep.ui
```

Debug start:

```bash
qtvcp -d -c easystep -u ./lathe_easystep_handler.py ./lathe_easystep.ui
```

## Workflow

The UI follows a tab-based workflow. Inputs directly affect preview, step
storage and generated program data.

Important workflow properties in the current state:

- every machining step should have its own step file
- program files store links to their referenced step files
- `Save Changes` updates linked step, program and existing G-code files
- file dialogs reopen in the most recently used directory
- the most recently used tool table is loaded automatically on startup

## Main Tabs

`Program`

- stock geometry
- retract and safety positions
- spindle limits
- machine profile
- chuck and no-go configuration

`Face`

- face area
- rough / finish / combined mode
- optional finish allowance
- edge type and edge size

`Contour`

- X-only, Z-only or X/Z combined segments
- chamfers and radii
- inner/outer radius side selection

`Parting / Roughing`

- named contour selection
- inside / outside
- roughing / finishing
- tool, feed and infeed parameters

`Thread`

- internal or external threading
- full G76 parameter set
- presets for metric and trapezoidal threads

`Groove / Parting`

- inside or outside groove logic
- reduced feed / speed behaviour near critical positions

`Drill`

- simple drilling
- chip breaking
- peck drilling with retract

`Keyway`

- tool selection
- start angle and repetition angle step
- angle values are handled in degrees
- keyway program data is loaded back into the UI correctly
- edits affect preview, step files and program files again

## Preview and Section View

The preview currently combines a side view of the turned part with an
additional front section view at a selectable Z position.

Current behaviour:

- the side view remains visible
- the section position is marked in the side view
- the section line can be moved directly
- the front section is calculated from the whole program, not only the selected step
- the front section uses the largest workpiece diameter as a fixed visual reference
- the resulting final section geometry is additionally highlighted as a filled area

## Current Priorities

The next meaningful work areas are:

1. continue splitting handler logic into dedicated modules
2. make preview handling more robust
3. keep embedded and standalone behaviour aligned
4. keep documentation and status files in sync
5. verify real machine workflows further

## Regression and Smoke Test

The current refactor state is protected by both unit tests and reference
program snapshots.

- `pytest -q`
- `python3 regenerate_all_ngc.py`

The checked-in reference programs under `ngc/` currently cover:

- facing
- drilling
- threading
- grooving
- external roughing
- contour with radius/chamfer

## Known Limitations

The current state is usable, but not yet the final technical structure.

- `slicer.py` now acts largely as a compatibility layer, but it still contains legacy code and should be reduced further over time
- the new module structure is functional, but not every area has been split into the smallest clean domain modules yet
- the section view works, but the visual representation of complex final geometry is not yet fully finalized in every case
- real machine clearance and collision behaviour still need verification on practical dry runs
