# TODO LatheEasyStep

Stand: 2026-07-10

## Prioritaet A

### 1. LinuxCNC-Simulation und Programmaufbau

- [ ] Einstich- und Abstich-Subroutine in LinuxCNC erneut pruefen.
  Sicherstellen, dass Einstich-/Abstichzyklen nicht erneut in Endlosschleifen laufen.

- [ ] Programmaufbau auf LinuxCNC-Best-Practice pruefen.
  Generatorseitig ist die Reihenfolge bereits per Regressionstest abgesichert.
  Offen bleibt die praktische Verifikation in LinuxCNC mit Einstich-/Abstich-Faellen.

### 2. Werkzeugwechsel und Verfahrwege absichern

- [ ] Werkzeugwechsel mit `G53` in Simulation und auf realem LinuxCNC verifizieren.
  Verhalten mit verschiedenen Werkstuecknullpunkten pruefen.

- [ ] Ursache der nach `M6` beobachteten Bewegung eindeutig zuordnen.
  Klaeren, ob die Ursache im Generator oder in der LinuxCNC-Konfiguration liegt.

- [ ] Anfahr- und Rueckzugsstrategie nach Bearbeitungsart unterscheiden.
  Aktuell generatorseitig bereits umgesetzt fuer:
  - Innen-Abspanen
  - Innengewinde
  Offen bleibt die Ausweitung auf:
  - Aussenbearbeitung
  - Ausseneinstich
  - Inneneinstich
  - Bohren
  - Aussengewinde

- [ ] Innenbearbeitung mit sicherer Bewegungsreihenfolge erzeugen.
  Fuer Innen-Abspanen und Innengewinde bereits generatorseitig umgesetzt.
  Offen bleibt dieselbe Sicherheitslogik fuer weitere Innenoperationen.

- [ ] Einstichwerkzeuge vor jeder axialen Bewegung vollstaendig freifahren.
  Gilt fuer Ausseneinstich, Inneneinstich, Abstich und Stirneinstich.

- [ ] Keine diagonalen Eilgangbewegungen aus noch im Material stehenden Einstichpositionen erzeugen.

### 3. Tooltips wieder als offen behandeln

- [ ] Tooltip-System grundlegend pruefen.
  Der Punkt darf nicht als erledigt gelten, solange Tooltips im echten QtVCP-Betrieb nicht zuverlaessig erscheinen.

- [ ] Nicht weiter nur Tooltip-Texte oder Relay-Logik ergaenzen.
  Die tatsaechliche technische Ursache muss ermittelt werden.

- [ ] Tooltips praktisch in beiden Betriebsarten testen.
  Testen in:
  - Standalone
  - eingebettetem QtVCP / QtDragon

- [ ] Technische Pruefpunkte systematisch abarbeiten.
  - Wird `QToolTip` global durch QtVCP oder das Stylesheet deaktiviert?
  - Erreichen `QEvent.ToolTip` und `QEvent.HoverEnter` die Zielwidgets?
  - Sind `mouseTracking`, `WA_Hover` oder Event-Filter falsch gesetzt?
  - Werden Tooltips nach dem UI-Aufbau ueberschrieben oder geleert?
  - Liegt ein transparenter Container ueber den Eingabefeldern?
  - Funktionieren normale Qt-Tooltips in einem minimalen Testwidget innerhalb derselben QtVCP-Instanz?

- [ ] Tooltip-Verhalten auf realen Widget-Typen pruefen.
  Abdecken:
  - Labels
  - Spinboxen
  - Comboboxen
  - Buttons
  - Tabellen

- [ ] Abnahmekriterium erfuellen.
  Tooltip erscheint im eingebetteten LinuxCNC-Panel zuverlaessig nach normalem Verweilen mit der Maus.

### 4. Innen-Abspanen korrigieren

- [ ] Innen-Abspanen ausserhalb des Zykluspfads vollstaendig als eigene Strategie behandeln.
  Zyklusstart, sichere Rueckzuege und `XRI`-Pflicht sind umgesetzt.
  Offen bleibt die komplette fachliche Trennung in allen Move-based Varianten.

- [ ] Materialmodell fuer Innenkonturen korrigieren.
  Das abzutragende Material liegt ausserhalb des aktuellen Innendurchmessers und innerhalb der fertigen Innenkontur.

- [ ] Schlichtaufmass fuer Innenbearbeitung in korrekter X-Richtung anwenden.

- [ ] Werkzeugradiuskorrektur, Konturseite, Rueckzug ueber `XRI`, `G71`-Parameter und Konturstart fuer Innenkonturen weiter absichern.
  `G71`-Start-X, `XRI`-Pflicht und Kompensations-Einfahrt sind bereits korrigiert und per Tests abgesichert.
  Offen bleibt die Verifikation weiterer Innenkonturformen und Move-based Pfade.

- [ ] Sicherstellen, dass Vorschau und erzeugter Werkzeugweg dieselbe Materialseite darstellen.

## Prioritaet B

### 5. Gewinde- und Freistich-Presets vereinheitlichen

- [ ] Pruefen, ob alle Gewindegroessen bis `M30` automatisch passende DIN-Freistich-Vorschlaege erhalten.

- [ ] Doppelte Zuordnungstabellen entfernen.

- [ ] Freistichgroessen ausschliesslich ueber zentrale Preset-Helper bestimmen.

- [ ] Hart codierte Tabellen wie `M3` bis `M16` vermeiden.

### 6. Drehzahlmodus pro Operation

- [ ] Auswahl zwischen `G96` und `G97` aus dem Programmkopf in die einzelnen Steps verlagern.

- [ ] Fuer jede spindelgefuehrte Operation eine eigene Auswahl anbieten:
  - `Konstante Drehzahl (G97)`
  - `Konstante Schnittgeschwindigkeit (G96)`

- [ ] Betroffene Steps pruefen und erweitern.
  - Planen
  - Aussen-/Innendrehen
  - Abspanen
  - Einstich
  - Abstich
  - Gewinde
  - Freistich
  - Schlichten

- [ ] Ausgabeverhalten pro Modus sauber definieren und generatorseitig umsetzen.

## Prioritaet C

### 7. Verifikation und Regressionstests

- [ ] Alle neuen Generatorfunktionen mindestens einmal in der LinuxCNC-Simulation verifizieren.

- [ ] Dabei mindestens folgende Kriterien pruefen:
  - G-Code syntaktisch korrekt
  - LinuxCNC fuehrt den Code ohne Warnungen aus
  - keine Endlosschleifen
  - keine unerwarteten Achsbewegungen
  - Vorschau und reale Ausfuehrung stimmen ueberein

- [ ] Regressionstests fuer LinuxCNC-Praxisfaelle erweitern.
  Abdecken:
  - Aussengewinde rechts
  - Aussengewinde links
  - Innengewinde rechts
  - Innengewinde links
  - Werkzeugwechsel mit Werkstueckkoordinaten
  - Werkzeugwechsel mit Maschinenkoordinaten (`G53`)
  - Einstich
  - Abstich
  - `G71` / `G72`
  - Freistich separat
  - Freistich integriert
  - `G96`
  - `G97`

- [ ] Regressionstests fuer Innen-Abspanen ergaenzen.
  Abdecken:
  - zylindrische Innenkontur
  - Innenstufe
  - Innenkonus
  - Innenradius
  - Innenkontur mit Freistich
  - Innen-Schruppen mit anschliessendem Schlichten

## Bereits in Code und Tests erledigt

- Generator startet nicht mehr unbeabsichtigt in `O`-Subroutinen; Reihenfolge von Subroutinen und Hauptprogramm ist per Regressionstest abgesichert.
- `M30` beendet das Hauptprogramm am Ende; nach `M30` werden keine Subroutinen mehr ausgegeben.
- Zusaetzliche Nullbewegungen nach Werkzeugwechselpfaden sind generatorseitig per Regressionstest abgesichert.
- Innen-Abspanen verwendet keinen unplausiblen `G71`-Startdurchmesser mehr.
- Innen-Gewinde und Innen-Abspanen erzwingen jetzt ein plausibles `XRI`; ohne gueltiges `XRI` bricht die G-Code-Erzeugung ab.
- Innen-Gewinde und Innen-Abspanen verwenden jetzt op-spezifische sichere Anfahr-/Rueckzugsebenen ueber `XRI/ZRI`.
- Der Schlicht-Einfahrweg mit aktiver Schneidenradiuskorrektur ist fuer Innenkonturen korrigiert.

## Naechste sinnvolle Reihenfolge

1. Programmaufbau und Einstich-/Abstich-Subroutinen in LinuxCNC absichern.
2. Werkzeugwechsel, `G53` und sichere Verfahrwege fuer Innenbearbeitung korrigieren.
3. Tooltip-System im echten QtVCP-Betrieb technisch isolieren und beheben.
4. Innen-Abspanen fachlich korrekt auf eigene Generatorlogik umstellen.
5. Gewinde-/Freistich-Presets und `G96`/`G97` pro Step bereinigen.
6. Simulation, Praxistests und Regressionen nachziehen.

## Grundsatz

- Generatorlogik muss sich an realem LinuxCNC-Verhalten messen lassen, nicht nur an internen Modellannahmen.
- Innenbearbeitung braucht eigene Sicherheits- und Bewegungslogik und darf nicht als Aussenbearbeitung gespiegelt werden.
- Tooltip-Funktion gilt erst dann als erledigt, wenn sie im eingebetteten Panel praktisch funktioniert.
