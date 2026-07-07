Lathe EasyStep
===============

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

Stand: 5. Juli 2026

Das Projekt ist aktiv in Entwicklung, aber die technische Basis ist deutlich
weiter als ein reiner Prototyp:

- Generator- und Sicherheitsphasen fuer Werkzeugwechsel, Anfahrten,
  Rueckzuege und Modals sind umgesetzt
- Save/Load fuer einzelne Steps und komplette Programme ist vorhanden
- Embedded-Betrieb in LinuxCNC wurde zuletzt gezielt stabilisiert
- Spannfutter-, No-Go- und Sicherheitslogik sind erweitert worden

Der aktuelle Schwerpunkt liegt nicht mehr auf der Grundfunktion des
G-Code-Generators, sondern auf:

- Konsolidierung der UI-/Handler-Logik
- Regressionen im Test- und Embedded-Kontext
- sauberer, konsistenter Dokumentation
- weiterer Absicherung fuer reale Maschinenablaeufe

## Branch-Status

`main` gilt als lauffaehige Basis des Projekts.

Neue Aenderungen sollen zuerst auf dem Branch `DEV` getestet werden. Erst wenn
die Anpassungen dort fachlich und technisch verifiziert wurden, werden sie in
den Hauptbranch migriert.

Wer neue Preview-, UI- oder G-Code-Aenderungen prueft, sollte daher gezielt den
Stand von `DEV` testen und nicht automatisch von derselben Stabilitaet wie auf
`main` ausgehen.

## Wichtiger Hinweis

Es gibt keine Garantie auf vollstaendige oder fehlerfreie Funktion.

Der erzeugte G-Code muss vor der Nutzung geprueft werden. Vor dem Einsatz an
der realen Maschine sollte:

- der Code verstanden werden
- eine Simulation oder ein Trockenlauf durchgefuehrt werden
- sichergestellt sein, dass Werkzeug, Spannmittel und Maschine geeignet sind

Die Nutzung erfolgt auf eigene Verantwortung.

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

Sobald alle Parameter gesetzt sind, wird das Rohteil in der Vorschau
dargestellt.

## Reiter "Planen"

Hier wird das Planen der Stirnflaeche definiert:

- zu planender Bereich
- Schruppen, Schlichten oder kombiniert
- optionales Schlichtaufmass
- Kantenform und Kantenmass

Werkzeugweg und Kontur sind sofort in der Vorschau sichtbar. Der Schritt
erscheint gleichzeitig in der Step-Liste.

## Step-Verwaltung

Links befindet sich die Liste aller Bearbeitungsschritte.

Moeglich sind:

- einzelne Steps speichern und wieder laden
- komplette Programme speichern und wieder laden
- bestehende Programme gezielt aendern

Im Embedded-Betrieb wird die sichtbare Step-Liste bewusst strikt ueber die
Operationsliste gefuehrt, damit geladene Steps und Programme konsistent in der
UI erscheinen.

## Reiter "Kontur"

In diesem Reiter wird nur Geometrie definiert, keine Bearbeitung.

Konturen entstehen aus Punktangaben und Segmenten. Unterstuetzt werden:

- nur X
- nur Z
- X und Z kombiniert
- Kanten als Fase oder Radius
- Innen-/Aussenseite pro Radius

Jede Kontur sollte einen eindeutigen Namen erhalten, damit sie spaeter fuer
Abspanen oder Folgeoperationen ausgewaehlt werden kann.

## Reiter "Abspanen"

Hier wird eine zuvor definierte Kontur bearbeitet:

- Auswahl der Kontur ueber ihren Namen
- innen oder aussen
- Schruppen oder Schlichten
- Werkzeug
- Zustellung, Vorschub und Drehzahl

Die Strategie wird grafisch dargestellt. Die Sicherheits- und Retract-Logik
wurde zuletzt gezielt ueberarbeitet.

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

Die Einstichlogik wird als Subroutine direkt in den G-Code geschrieben. Es
wird keine zusaetzliche Datei benoetigt.

## Reiter "Bohren"

Der Bohr-Reiter ist bewusst einfach gehalten:

- Werkzeug auswaehlen
- normal bohren
- Spanbruch
- Spanbruch mit Rueckzug

Gedacht ist er fuer zentrales Bohren auf der Drehbank.

## Reiter "Keilnut"

Dieser Reiter ist fuer Nutenstossen und spaetere Verzahnungsfunktionen
vorgesehen.

Aktueller Stand:

- funktional vorbereitet
- noch kein fertig ausgearbeiteter Werkstatt-Workflow
- perspektivisch fuer C-Achsen-nahe Erweiterungen gedacht

## Aktuelle Prioritaeten

Die naechsten sinnvollen Arbeiten im Projekt sind:

1. Test- und UI-Regressionen im Handler sauber schliessen
2. Vorschau robuster machen, damit nur beabsichtigte Werkstueck- und Hilfsgeometrie sichtbar wird
3. Embedded- und Standalone-Verhalten weiter angleichen
4. Dokumentation und interne Statusdokumente konsistent halten
5. reale Werkstattablaeufe und Maschinenprofile weiter verifizieren

Aktuell offen in der Vorschau:

- der Programmkopf soll seine Rohteil- und Sicherheitsgeometrie sofort stabil zeigen, nicht erst nach expliziter Auswahl
- die Gewindedarstellung soll kuenftig aus den eingestellten Geometriewerten abgeleitet werden, nicht nur symbolisch erscheinen

## Zusammenfassung

Lathe EasyStep ist ein praxisorientiertes LinuxCNC-Drehpanel mit Fokus auf
sichere Bewegungen, direkter Vorschau und wiederverwendbaren Steps. Der Kern
des Systems ist vorhanden; die laufende Arbeit verschiebt sich zunehmend von
Grundfunktionalitaet zu Robustheit, Integration und Werkstattreife.

English
-------

## What is Lathe EasyStep?

Lathe EasyStep is a conversational turning panel for LinuxCNC. It is intended
to create common lathe operations directly at the machine, with immediate
preview and reusable steps, without relying on external CAM.

Current focus areas are:

- safe tool motion
- deterministic workflows
- direct visual feedback
- reusable machining steps

The project is under active development. The current work is focused less on
basic generator features and more on stability, UI consistency, and shop-floor
readiness.
