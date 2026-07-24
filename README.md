Lathe EasyStep
==============

Current Version: `0.7.0+unreleased`
Status Date: `2026-07-24`
Primary Test Branch: `dev`

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

Stand: Version 0.7.0 + Unreleased, 24. Juli 2026

Das Projekt ist aktiv in Entwicklung, aber die technische Basis ist deutlich
weiter als ein reiner Prototyp:

- Generator- und Sicherheitsphasen fuer Werkzeugwechsel, Anfahrten,
  Rueckzuege und Modals sind umgesetzt
- Save/Load fuer einzelne Steps und komplette Programme ist vorhanden
- Embedded-Betrieb in LinuxCNC wurde gezielt stabilisiert
- Spannfutter-, No-Go- und Sicherheitslogik sind erweitert worden
- Handler-, G-Code-, Kontur- und Vorschau-Logik wurden fuer Version 0.7.0 deutlich weiter modularisiert
- gemeinsame UI-Helfer fuer Sprache, Uebersetzung, ComboBoxen und Tab-Bezeichnungen verhindern auseinanderlaufende Parallelimplementierungen
- generische G-Code-Parameter-Lookups und die Safe-X-Berechnung fuer Innenbearbeitung liegen zentral in `gcode_utils.py`
- das ungenutzte und nicht importierbare Alt-Paket `lathe_easystep/contour/` wurde entfernt; die aktive Konturlogik bleibt in `contour_logic.py` und `contour_features.py`
- die aktuelle Entwicklungsbasis inkl. Freistich-/Sicherheitsausbau, UI-Teilung, Real-Qt-Regressionen und realen Generatorfixes ist mit `331 passed, 3 skipped` validiert
- `lathe_easystep.ui` ist die Shell; acht Bearbeitungsreiter liegen unter `lathe_easystep/ui_parts/`
- `de.lng`, `en.lng` und `es.lng` besitzen jeweils 1.020 identische, nichtleere Sprachschluessel
- zusaetzlich wurden UI-Sichtbarkeitsregeln fuer weitere Bearbeitungsarten per Regressionstest abgesichert und die Test-Infrastruktur fuer echte PyQt5-Roundtrip-Tests gegen die uebrige Stub-Suite gehaertet

Der derzeit dokumentierte Arbeitsstand ist `Version 0.7.0` plus aktuelle `Unreleased`-Erweiterungen.

## Branch-Status

`main` gilt als lauffaehige Basis des Projekts.

Neue Aenderungen sollen zuerst auf dem Branch `dev` getestet werden. Erst wenn
die Anpassungen dort fachlich und technisch verifiziert wurden, werden sie in
den Hauptbranch migriert.

## Strikte UI-/Spracharchitektur (ID-only)

Fuer die UI gilt jetzt verbindlich eine strikte Trennung von Anzeige und Logik:

- sichtbare Texte kommen ausschliesslich aus Sprachdateien (`.lng`)
- Programmlogik arbeitet nur mit technischen IDs/Werten (`currentData`)
- es gibt keinen Fallback auf Python- oder `.ui`-Texte
- fehlt ein Sprachschluessel, wird absichtlich der Schluessel/ID angezeigt

Das macht unvollstaendige Sprachdateien sofort sichtbar und verhindert, dass
Logik von lokalisierten Anzeige-Texten abhaengt.

Der Umbau ist noch nicht vollstaendig abgeschlossen. Verbleibende direkte
Textquellen aus Python oder der `.ui` werden nicht mehr stillschweigend als
"ok" behandelt, sondern explizit als offene Architekturarbeit in `TODO.md`
gefuehrt.

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
- `lathe_easystep/ui_parts/`
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

Zur UI-Struktur:

- `lathe_easystep.ui` ist die Start-Shell des Panels.
- Die einzelnen Reiterinhalte liegen getrennt in `lathe_easystep/ui_parts/*.ui`.
- Der Handler laedt diese Teil-UIs beim Start in die vorhandenen Tab-Container nach.

## Grundsaetzlicher Workflow

Die Bedienung folgt einem festen Ablauf ueber die Reiter. Alle Eingaben wirken
sich direkt auf Vorschau und Step-Verwaltung aus.

## Reiter "Programm"

Hier werden die globalen Programmeinstellungen festgelegt:

- Sicherheitsabstaende und Rueckzugsebenen
- Sicherheitsabstand / Rueckzugsebene Z als Pflichtwert fuer sichere Anfahrten und Generatorvalidierung
- `XRI` als Pflichtwert fuer Innen-Gewinde und Innen-Abspanen; unplausible Innen-Rueckzugswerte werden generatorseitig abgewiesen
- `XRI` ist fuer Innenbearbeitung eine harte Sicherheitsgrenze: wenn ein
  Innengewinde, Inneneinstich oder Innen-Abspanen einen kleineren X-Wert als
  `XRI` anfahren muesste, wird kein G-Code erzeugt
- Rohteilgeometrie
- Nullpunkt und Bezug
- maximale Drehzahlen
- Werkzeugdatenbank
- Maschinenprofil, Spannfutter und Spannart
- explizite Koordinatensystemwahl fuer Werkzeugwechsel- und Parkpositionen (`Werkstueckkoordinaten` oder `Maschinenkoordinaten / G53`)
- vor jedem expliziten `T.. M6` wird derselbe definierte Werkzeugwechselpunkt angefahren

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
- offene Aenderungen werden im UI sichtbar markiert; Reiter- und Stepwechsel warnen, speichern aber weiterhin nichts automatisch

## Reiter "Kontur"

In diesem Reiter wird nur Geometrie definiert, keine Bearbeitung.

Unterstuetzt werden:

- nur X
- nur Z
- X und Z kombiniert
- Kanten als Fase oder Radius
- Innen-/Aussenseite pro Radius
- Konturfeatures fuer DIN-Freistich / Hinterschnitt am Konturanfang oder -ende

Aktueller Generatorstand fuer Konturfeatures:

- eine Kontur kann intern als Fertigkontur, Schruppkontur ohne Hinterschnitt und reine Feature-Teilkontur ausgewertet werden
- dieselbe Geometrie wird fuer Vorschau und G-Code wiederverwendet
- fuer DIN-Freistiche sind Standarddaten von `M3` bis `M30` hinterlegt
- die Segmentbearbeitung im Panel fuehrt jetzt auch Feature-Felder fuer `DIN-Freistich`, `Gewindegroesse`, `Norm`, `Innen/Aussen` und `Start/Ende`

## Reiter "Abspanen"

Hier wird eine zuvor definierte Kontur bearbeitet:

- Auswahl der Kontur ueber ihren Namen
- innen oder aussen
- Schruppen, Schlichten oder Schruppen + Schlichten
- Werkzeug
- Zustellung, Vorschub und Drehzahl

Der aktuelle Stand unterstuetzt fuer Hinterschnitt/Freistich vier Bearbeitungsarten:

- ignorieren
- nur beim Schlichten fahren
- separat schruppen
- voll in der Kontur mitschruppen

Die Generatorausgabe dokumentiert zusaetzlich:

- verwendete Strategie (`G71`, `G72`, move-based)
- Ausgabe-Praeferenz (`auto`, Zyklus bevorzugt, ausgeschrieben bevorzugt)
- Aufmass X/Z
- Fallback-Gruende bei nicht zyklustauglicher Kontur oder Expertenoptionen

Sicherheitsstand fuer Innen-Abspanen:

- `XRI` ist fuer Innen-Abspanen verpflichtend
- `XRI` ist nicht nur Rueckzugsebene, sondern eine harte Untergrenze fuer alle
  intern angeforderten X-Werte
- interne `G71`-Starts werden nicht mehr aus `X0/Z0` abgeleitet
- Anfahrt und Rueckzug verwenden fuer Innenkonturen `XRI/ZRI`
- der Schlicht-Einfahrweg fuer aktive Schneidenradiuskorrektur wird so erzeugt, dass LinuxCNC die Kompensation sauber annehmen kann

Die UI bietet dafuer jetzt auch direkte Bedienfelder fuer:

- Hinterschnitt-Modus
- Ausgabe-Praeferenz
- separates Hinterschnitt-Werkzeug samt Vorschub und Drehzahl
- Optionalstop vor separatem Hinterschnitt
- alle sicherheitsrelevanten Expertenfelder sind ueber zentrale Tooltips dokumentiert

## Reiter "Gewinde"

Dieser Reiter dient zum Gewindeschneiden:

- Innen- oder Aussengewinde
- Werkzeugauswahl
- vollstaendige G76-Parameter
- Presets fuer metrische Gewinde und Trapezgewinde

Der Generator prueft jetzt zusaetzlich auf fachlich unplausible `G76`-Parameter und kann bei kuenftigen Gewinde-Workflows an DIN-Freistiche gekoppelt werden.
Optional kann fuer Gewinde jetzt direkt ein DIN-Freistich als Vorschlag kommentiert werden, ohne dass automatisch Geometrie erzeugt wird.

Preset-Stand:

- metrische Gewinde-Presets zentral verfuegbar bis `M30`
- Trapezgewinde-Presets zentral verfuegbar
- DIN-Freistich-/Hinterschnitt-Daten zentral verfuegbar bis `M30`

Gewinde-Stand:

- separates Feld `Gewindestart Z`
- separate Auswahl fuer Rechts- und Linksgewinde
- `XRI`-Pflicht und Plausibilitaetspruefung fuer Innengewinde
- Innengewinde werden abgewiesen, sobald der benoetigte X-Wert die harte
  Sicherheitsgrenze `XRI` unterschreiten wuerde
- Vorschau und Generator fuer:
  - Aussengewinde rechts
  - Aussengewinde links
  - Innengewinde rechts
  - Innengewinde links

## Reiter "Einstich / Abstich"

Hier werden Einstiche und Abstiche definiert:

- klare Betriebsart `Einstich` oder `Abstich`
- innen oder aussen
- partingspezifische Reduktionswerte nur im Abstich-Modus sichtbar
- reduzierte Drehzahl ab definierter Position

Der Groove-/Abstich-Zyklus wird generatorseitig jetzt so ausgegeben, dass LinuxCNC erst das Hauptprogramm ausfuehrt und die O-Subroutinen erst spaeter definiert werden. Damit laeuft der Zyklus nicht mehr versehentlich in die Makrobibliothek hinein.

## Reiter "Bohren"

Der Bohr-Reiter ist bewusst einfach gehalten:

- Werkzeug auswaehlen
- normal bohren
- Spanbruch
- Spanbruch mit Rueckzug

## Reiter "Keilnut"

Dieser Reiter ist fuer Nutenstossen und spaetere Verzahnungsfunktionen
vorgesehen.

## Werkzeugwechsel und LinuxCNC

Lathe EasyStep trennt jetzt sauber zwischen Generatorverhalten und Maschinenlogik:

- `Werkstueckkoordinaten` erzeugen normale `G0 X.. Z..`-Bewegungen
- `Maschinenkoordinaten` erzeugen explizit `G53 G0 X.. Z..`
- der Generator fuegt nach `T.. M6` kein zusaetzliches `G0 X0 Z0` ein

Der mit dem realen Testprogramm gepruefte Stand (`/home/adm1n/linuxcnc/nc_files/Test.ngc`) zeigt:

- der definierte Werkzeugwechselpunkt wird korrekt generiert
- die beobachtete Zusatzbewegung zum manuellen Wechsel kommt aus der LinuxCNC-Konfiguration
- in der getesteten Konfiguration ist `TOOL_CHANGE_MODE = MANUAL` aktiv und `iocontrol.0.tool-change` ist auf `hal_manualtoolchange` verdrahtet

Vor dem Einsatz an einer realen Maschine muss deshalb immer sowohl der erzeugte G-Code als auch die konkrete `M6`-/Toolchange-Konfiguration der LinuxCNC-Installation geprueft werden.

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
- die Vorschau ist aus dem Scrollbereich geloest und bleibt beim Bearbeiten dauerhaft im unteren Panel-Bereich sichtbar
- die Schnittlage wird in der Seitenansicht farblich markiert
- die Schnittlage kann direkt in der Seitenansicht verschoben werden
- die Vorderansicht wird aus dem gesamten Programm berechnet
- die Vorderansicht nutzt den groessten Werkstueckdurchmesser als feste Referenz
- die aktuelle Endgeometrie wird in der Vorderansicht zusaetzlich flaechig hervorgehoben
- Start-, Rueckzug- und Futter-Sperrzonenwarnungen werden im erzeugten G-Code dokumentiert; die Vorschau bleibt weiterhin auf Geometrie und Sicherheitsflaechen fokussiert
- fuer Abspanoperationen koennen Schruppkontur und Freistichbereich jetzt getrennt in der Vorschau hervorgehoben werden
- Sicherheitswarnungen lassen sich optional direkt in der Vorschau einblenden

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

Die vollstaendige, priorisierte Aufgabenliste steht in der
[TODO.md](TODO.md), die Release-Zuordnung in der [ROADMAP.md](ROADMAP.md).

Aktuelle Reihenfolge:

1. sichere Anfahrt zwischen aufeinanderfolgenden Operationen
2. leere Schruppoperationen als Fehler abbrechen
3. Innen-Schruppen und Innen-Schlichten an weiteren Konturformen verifizieren
4. lokale DIN-Freistichgeometrie und gemeinsame Vorschau-/G-Code-Primitive
5. veraltete `slicer.py`-Parallelimplementierung entfernen
6. G96/G97-UI, Sichtbarkeitstests und LinuxCNC-Referenzmatrix
7. anschliessend Handler-, UI-, Sprach- und Modalarchitektur konsolidieren

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

- `emit_approach()` kann bei gesetztem `_is_at_safe` einen neuen Zielpunkt noch direkt diagonal anfahren
- leere Schruppoperationen werden noch nicht in allen Faellen als Generatorfehler abgebrochen
- Innen-Schruppen, Innenstufen, Innenkonen, Innenradien und Innenfreistiche brauchen weitere Realtests
- lokale DIN-Freistiche funktionieren noch nicht an beliebigen Segmenten einer laengeren Kontur
- `slicer.py` ist eine produktiv ungenutzte Parallelimplementierung, die noch von Legacy-Tests verwendet wird
- sichtbare Defaulttexte stehen trotz vollstaendiger Sprachkataloge noch in Python- und UI-Quellen
- reale Maschinen- und Kollisionsfaelle muessen weiterhin per Backplot und Trockenlauf verifiziert werden

## Aktuelle Modulstruktur

Die acht Bearbeitungsreiter sind bereits aus der Shell geloest:

- `lathe_easystep.ui`: Shell, Step-Liste, Tab-Container und Vorschau
- `lathe_easystep/ui_parts/*.ui`: Program, Face, Contour, Parting, Thread,
  Groove, Drill und Keyway
- `lathe_easystep/ui_split.py`: Laufzeit-Lader der Teil-UIs
- `lathe_easystep/*.py`: Fach-, UI-, Persistenz-, Vorschau- und Generatorlogik

Offen bleiben die weitere Trennung von Vorschau und Step-Verwaltung, klare
Controllergrenzen sowie der Abbau von `lathe_easystep_handler.py` und der
ungenutzten Parallelimplementierung in `slicer.py`.

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

Current documented state: Version 0.7.0 + Unreleased, July 24, 2026.

The project is still under active development, but it is no longer just an
early prototype:

- core G-code generation and safety phases are implemented
- save/load for single steps and complete programs is available
- LinuxCNC embedded usage was stabilized
- chuck, no-go and machine-safety logic was expanded
- handler, generator, contour and preview logic have been modularized substantially further for version 0.7.0
- the current development baseline is validated with `331 passed, 3 skipped`
- `lathe_easystep.ui` is now the shell and eight operation tabs live under `lathe_easystep/ui_parts/`
- the German, English and Spanish catalogs each contain the same 1,020 non-empty translation keys

## Branch Status

`main` is the stable runnable base.

New work is expected to be tested on `dev` first. Only verified changes should
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

The complete prioritized backlog is maintained in [TODO.md](TODO.md), with
release milestones in [ROADMAP.md](ROADMAP.md).

Current order:

1. make operation-to-operation approach moves safe
2. reject empty roughing operations
3. verify internal roughing and finishing on additional contour forms
4. complete local DIN-relief geometry and shared preview/G-code primitives
5. remove the obsolete parallel implementation in `slicer.py`
6. add per-operation G96/G97 UI and extend LinuxCNC reference tests
7. then consolidate handler, UI, translation and modal-state architecture

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

The current state is usable, but not yet technically complete.

- `emit_approach()` can still emit a direct diagonal target move when `_is_at_safe` is set
- empty roughing operations are not rejected in every case
- internal steps, tapers, radii and reliefs need additional real-machine verification
- local DIN reliefs do not yet work on arbitrary segments inside longer contours
- `slicer.py` is an unused parallel implementation still referenced by legacy tests
- UI and Python sources still contain visible defaults despite complete language catalogs
- real-machine clearance and collision behaviour still require backplot and dry-run verification
