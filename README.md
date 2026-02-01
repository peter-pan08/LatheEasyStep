Lathe EasyStep
Deutsch
Was ist Lathe EasyStep?

Lathe EasyStep ist ein konversationelles Drehbank-Panel für LinuxCNC, mit dem sich typische Drehbearbeitungen direkt an der Maschine programmieren lassen – ohne externes CAM.

Der Fokus liegt auf:

klaren, reproduzierbaren Abläufen

sicheren Werkzeugbewegungen

sofortiger grafischer Rückmeldung

Wiederverwendbarkeit von Bearbeitungsschritten

Das Panel ist für den Werkstattalltag gedacht und kein vollwertiger CAM-Ersatz.

🔧 Projektstatus / Haftungsausschluss

⚠️ Wichtiger Hinweis

Lathe EasyStep befindet sich aktiv in Entwicklung.

Es gibt keine Garantie auf vollständige oder fehlerfreie Funktion.

Der erzeugte G-Code muss vor der Nutzung geprüft werden.

Vor dem Einsatz an der realen Maschine sollte:

der Code verstanden werden

eine Simulation oder ein Trockenlauf durchgeführt werden

sichergestellt sein, dass Werkzeug, Spannmittel und Maschine geeignet sind

Die Nutzung erfolgt auf eigene Verantwortung.

Grundsätzlicher Workflow

Die Bedienung folgt einem festen Ablauf über die Reiter (Tabs).
Alle Eingaben wirken sich direkt auf die Vorschau aus.

Reiter „Programm“

Hier werden die globalen Programmeinstellungen festgelegt:

Sicherheitsabstände und Rückzugsebenen

Rohteilgeometrie (Form, Durchmesser, Länge)

Nullpunkt / Bezug

maximale Drehzahlen

Werkzeugdatenbank

Die Werkzeugdatenbank sollte hier geladen werden.

Dadurch weiß das Panel:

welches Werkzeug verwendet wird

welche Werkzeugorientierung vorliegt

ob eine Radiuskorrektur (Nasenradius) notwendig ist

Sind im Werkzeugkommentar ISO-Codes von Schneidplatten hinterlegt, können diese automatisch erkannt und ausgewertet werden.

➡️ Sobald alle Parameter gesetzt sind, wird das Rohteil in der Vorschau dargestellt.

Reiter „Planen“

Hier wird das Planen der Stirnfläche definiert:

zu planender Bereich

Strategie:

Schruppen

Schlichten

Schruppen + Schlichten

optionales Schlichtaufmaß beim Schruppen

Die Optionen sind bewusst selbsterklärend gehalten.

➡️ Werkzeugweg und Kontur sind sofort in der Vorschau sichtbar.
➡️ Der Schritt erscheint gleichzeitig in der Step-Liste auf der linken Seite.

Step-Verwaltung (linke Seite)

Links befindet sich die Liste aller Bearbeitungsschritte (Steps).

Unterhalb der Liste können Steps:

einzeln gespeichert

wieder geladen

in anderen Programmen wiederverwendet werden

Praxisbeispiel:
Ein Step „Planen 40 mm Welle“ wird gespeichert.
Später kann dieser Step in einem neuen Programm geladen werden, ohne alle Parameter neu einzugeben.

Zusätzlich können:

alle Steps gemeinsam gespeichert werden

komplette Programme wieder geladen werden

➡️ Ideal, um bestehende Programme gezielt zu ändern (z. B. Radius oder Durchmesser anpassen).

Reiter „Kontur“

In diesem Reiter wird nur Geometrie definiert – keine Bearbeitung.

Konturen entstehen durch Punktangaben

mögliche Eingaben:

nur X

nur Z

X und Z kombiniert

Aus den Punkten wird automatisch eine zusammenhängende Kontur berechnet.

Wichtig:

Jede Kontur sollte einen eindeutigen Namen erhalten

Dieser Name wird später zur Auswahl der Kontur verwendet

➡️ Die Kontur ist direkt in der Vorschau sichtbar.

Reiter „Abspanen“

Hier wird eine zuvor definierte Kontur bearbeitet:

Auswahl der Kontur über ihren Namen

Bearbeitungsparameter:

innen / außen

Schruppen oder Schlichten

Werkzeug

Zustellungen, Vorschub, Drehzahl

➡️ Die gewählte Strategie wird grafisch in der Vorschau dargestellt.

Reiter „Gewinde“

Dieser Reiter dient zum Gewindeschneiden:

Innen- oder Außengewinde

Werkzeugauswahl

vollständige G76-Parameter

Es stehen vordefinierte Presets für:

metrische Gewinde

Trapezgewinde

zur Verfügung.
Die Parameter können bei Bedarf angepasst werden.

Reiter „Einstich / Abstich“

Hier werden Einstiche und Abstiche definiert:

Einstich innen oder außen

Abstich mit:

reduziertem Vorschub

reduzierter Drehzahl ab bestimmter Position

Technischer Hintergrund:

Die Einstichlogik wird als Subroutine direkt in den G-Code geschrieben

Es wird keine zusätzliche Datei benötigt

➡️ Das erzeugte Programm ist systemunabhängig lauffähig.

Reiter „Bohren“

Der Reiter „Bohren“ ist bewusst einfach gehalten:

Werkzeug auswählen

Bohrart:

normal

Spanbruch

Spanbruch + Rückzug

➡️ Gedacht für zentrales Bohren auf der Drehbank.

Reiter „Keilnut“

Dieser Reiter ist für Nutenstoßen / Verzahnungen auf der Drehbank vorgesehen.

Aktueller Stand:

Funktion ist theoretisch vorbereitet

praktische Umsetzung erfolgt in einem späteren Entwicklungsschritt

Ziel:

Nuten stoßen

Verzahnungen herstellen

perspektivisch unter Nutzung der C-Achse

Zusammenfassung

Lathe EasyStep ist darauf ausgelegt:

typische Drehaufgaben schnell und sicher zu erstellen

Programme schrittweise aufzubauen

Bearbeitungsschritte wiederzuverwenden

Die Kombination aus:

klarer Reiter-Struktur

sofortiger Vorschau

speicherbaren Steps

macht das Panel besonders praxisnah für den Werkstattbetrieb.

English
What is Lathe EasyStep?

Lathe EasyStep is a conversational turning panel for LinuxCNC that allows common turning operations to be programmed directly at the machine, without external CAM software.

The focus is on:

clear and reproducible workflows

safe tool movements

immediate graphical feedback

reusability of machining steps

The panel is intended for shop-floor use and is not a full CAM replacement.

🔧 Project Status / Disclaimer

⚠️ Important Notice

Lathe EasyStep is under active development.

There is no guarantee that all features work correctly.

Any generated G-code must be reviewed before use.

Before running a program on a real machine, you should:

understand the generated code

perform a simulation or dry run

ensure compatibility with your machine, tooling, and setup

Use of this software is at your own risk.

Basic Workflow

Operation follows a fixed sequence via tabs.
All inputs are immediately reflected in the preview.

“Program” Tab

Defines the global program settings:

safety clearances and retract planes

stock geometry (shape, diameter, length)

work offset

maximum spindle speeds

Tool database

The tool table should be loaded here.

This allows the panel to know:

which tool is used

tool orientation

whether nose radius compensation is required

If ISO insert codes are stored in the tool comment, they can be parsed automatically.

➡️ Once all parameters are set, the stock is shown in the preview.

“Facing” Tab

Defines facing operations:

facing area

strategy:

roughing

finishing

rough + finish

optional finish allowance

➡️ Toolpath and contour are immediately visible in the preview.
➡️ The step appears in the step list on the left.

Step Management (left side)

The left panel shows a list of all machining steps.

Steps can be:

saved individually

loaded again

reused in other programs

Entire programs can also be saved and loaded.

“Contour” Tab

Defines geometry only, not machining.

contours are built from points

X only, Z only, or X/Z combined

Each contour should have a unique name, which is later used for machining selection.

“Parting / Roughing” Tab

Applies machining to an existing contour:

select contour by name

inside / outside

roughing or finishing

tool, feed, depth, spindle speed

“Thread” Tab

Used for thread cutting:

internal or external threads

tool selection

full G76 parameter set

metric and trapezoidal presets available

“Groove / Parting” Tab

Defines grooves and parting operations.

The groove logic is written as a subroutine directly into the G-code, requiring no external files.

“Drilling” Tab

Simple drilling operations:

normal

chip break

chip break + retract

Intended for center drilling on a lathe.

“Keyway” Tab

Intended for slotting / gear cutting.

Currently:

feature is theoretically prepared

implementation planned for future development

Summary

Lathe EasyStep is designed to:

create common turning operations quickly and safely

build programs step by step

efficiently reuse machining steps

The clear tab structure, instant preview, and reusable steps make it well suited for daily shop-floor use.