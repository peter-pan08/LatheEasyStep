# TODO LatheEasyStep

Stand: 2026-07-13

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

### 3. Tooltips wieder als offen behandeln (teilweise nach Sprachumschaltung sichtbar)

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


### 5. Sprache und Tooltips

- [ ] Sprachumschaltung im Reiter `Programmkopf` reparieren.
  Aktuell bleibt die Oberflaeche nach der Umschaltung weiterhin deutsch.

- [ ] Sicherstellen, dass die Sprachumschaltung alle sichtbaren Texte aktualisiert:
  - Reiter
  - Labels
  - Comboboxen
  - Buttons
  - Hilfetexte
  - Tooltips
  - dynamisch erzeugte Widgets

- [ ] Tooltip-System auf den aktuell beobachteten Zwischenstand anpassen.
  Nach Ausloesen der Sprachumschaltung funktionieren Tooltips teilweise, aber nicht auf allen Widgets.

- [ ] Ursache klaeren, warum Tooltips erst nach einer Sprachumschaltung teilweise aktiv werden.
  Das deutet auf eine fehlerhafte oder zu spaete Initialisierung hin.

- [ ] Tooltips vollstaendig und reproduzierbar pruefen.
  Abdecken:
  - Labels
  - Spinboxen
  - Comboboxen
  - Buttons
  - Tabellen
  - dynamisch erzeugte Widgets
  - Embedded-QtVCP
  - Standalone

### 5a. UI-Identitaeten und Uebersetzungssystem vereinheitlichen

- [ ] Jedem Widget einen eindeutigen und stabilen `objectName` geben.
  Namensschema konsequent nach Rolle und Funktion aufbauen, zum Beispiel:
  - `lbl_face_spindle_mode`
  - `cmb_face_spindle_mode`
  - `spin_face_spindle_speed`
  - `btn_thread_apply_preset`

- [ ] Sichtbare Texte nicht mehr als interne Logikkennung verwenden.
  Weder Sichtbarkeitslogik noch Generator, Dirty-State oder Validierung duerfen von `currentText()`, Labeltexten oder Buttontiteln abhaengen.

- [ ] Fachliche Werte sprachunabhaengig ueber stabile interne Kennungen fuehren.
  Zum Beispiel:
  - `g97`
  - `g96`
  - `rough`
  - `finish`
  - `internal`
  - `external`

- [ ] Comboboxen und Auswahlfelder konsequent ueber `itemData` auswerten.
  `currentText()` darf nur noch fuer Anzeigezwecke verwendet werden.

- [ ] Checkboxen, Buttons und dynamische Widgets mit festen Properties fuer ihre fachliche Zuordnung versehen.
  Verwenden:
  - `setting_key`
  - `text_key`
  - `tooltip_key`

- [ ] Zentrale Sprachdateien fuer mindestens Deutsch und Englisch anlegen.
  Vorgesehene Struktur:
  - `lathe_easystep/i18n/de.json`
  - `lathe_easystep/i18n/en.json`

- [ ] Ein zentrales Uebersetzungsmodul aufbauen.
  Vorgesehene Bausteine:
  - `translations.py` fuer Laden und `tr(key)` ohne Text-Fallback
  - `ui_registry.py` fuer statische Widget-Zuordnungen

### 5b. Verbindliche Architekturregel UI-Sprache (streng)

- [ ] Kein sichtbarer Text darf aus Python kommen.
  Verboten sind insbesondere direkte sichtbare Literale in `setText`, `QLabel`, `QPushButton`, `addItem`, Dialogen, Warnungen, Tooltips, Tabellenueberschriften und Statusmeldungen.

- [ ] Kein sichtbarer Text darf aus der `.ui` als Laufzeittext verwendet werden.
  `.ui`-Texte sind nur Platzhalter und muessen zur Laufzeit durch ID-basierte Aufloesung ersetzt werden.

- [ ] Jedes sichtbare Element braucht eine stabile technische ID.
  Beispiele:
  - `face.spindle_mode`
  - `thread.preset_apply`
  - `safety.xri`

- [ ] Sprachdateien ordnen ausschliesslich IDs auf sichtbare Texte ab.
  Beispiel:
  - `1001=Programmkopf`
  - `1002=Planen`

- [ ] Es gibt keinen Sprachfallback.
  Wenn ein Eintrag fehlt, wird die ID angezeigt, nicht ein deutscher/englischer Ersatztext.

- [ ] Eine unvollstaendige Sprachdatei muss sichtbar unvollstaendig rendern.
  Genau dadurch werden fehlende IDs sofort erkannt.

- [ ] Ohne gueltige Sprachdatei bleibt die UI absichtlich nur technisch bedienbar (IDs/Werte sichtbar).

- [ ] Programmlogik darf niemals mit sichtbaren Texten arbeiten.
  Nicht `currentText()`, sondern technische Werte ueber `currentData()` und stabile interne Codes.

- [ ] Auswahlwerte muessen feste interne IDs haben.
  Beispiel:
  - `combo.addItem("", "g97")`
  - `combo.addItem("", "g96")`

- [ ] Sprachwechsel darf ausschliesslich die Aufloesung derselben IDs gegen eine andere `.lng`-Datei aendern.

- [ ] Neue UI-Funktionen zuerst mit IDs einfuehren, dann Sprachdatei-Eintraege ergaenzen.

- [ ] Texte, Buttonbeschriftungen, Combo-Eintraege und Tooltips nur noch ueber Uebersetzungsschluessel belegen.
  Beispiele:
  - `face.spindle_mode.label`
  - `face.spindle_mode.g97`
  - `thread.preset_apply`
  - `thread.relief_enabled.tooltip`

- [ ] Sprachwechsel zentral fuer alle statischen Widgets anwenden.
  Die Aktualisierung darf nicht mehr aus verteilten Spezialfaellen bestehen.

- [ ] Sprachwechsel auch auf dynamisch erzeugte Widgets anwenden.
  Dynamische Widgets muessen ihre `text_key`- und `tooltip_key`-Properties selbst tragen, damit sie ohne Sondertabellen uebersetzt werden koennen.

- [ ] Fehlende Uebersetzungsschluessel beim Start und beim Sprachwechsel protokollieren.
  Fehlende Eintraege muessen gezielt erkennbar sein und duerfen nicht stillschweigend verschwinden.

- [ ] Sichtbarkeitslogik, Vorschau und Generator ausschliesslich anhand stabiler IDs und fachlicher Werte ausfuehren.
  Beispiel:
  - nicht `if combo.currentText() == "Konstante Drehzahl"`
  - sondern `if combo.currentData() == "g97"`

- [ ] Tests auf sprachunabhaengige IDs und Werte umstellen.
  UI-Tests duerfen nicht daran haengen, wie ein sichtbarer Text in Deutsch oder Englisch gerade formuliert ist.

### 6. Dirty-State und Speichern korrigieren

- [ ] Aenderungsstatus pro Datenpunkt und pro Step fuehren.
  Eine Aenderung an einem Feld darf nur den aktuell bearbeiteten Step beziehungsweise den betroffenen Programmpunkt als geaendert markieren.

- [ ] Nach dem Speichern eines neu angelegten Steps darf nicht ploetzlich angezeigt werden, dass alle zuvor angelegten Steps ungespeicherte Aenderungen enthalten.
  Strukturaenderungen markieren jetzt nur noch das Programm und bei neuen Steps den neuen Step selbst.
  Offen bleibt die Sichtpruefung im echten UI-Ablauf.

- [ ] Globale Dirty-Markierung aller Operationen entfernen, sofern keine globale Programmaenderung vorliegt.
  Fuer Move/Delete/Add ist die pauschale Dirty-Markierung aller Steps jetzt reduziert.
  Offen bleibt die weitere Entkopplung anderer UI-Refresh-Pfade.

- [ ] Folgende Faelle getrennt behandeln:
  - einzelnes Feld eines bestehenden Steps geaendert
  - neuer Step angelegt
  - Step gespeichert
  - Programmkopf geaendert
  - Kontur geaendert
  - Sprachumschaltung
  - reine Vorschauaktualisierung ohne Datenveraenderung

- [ ] Reine UI-Aktualisierungen duerfen keinen Dirty-State ausloesen.
  Sprachumschaltung ist generatorseitig bereits ausgenommen; offen bleiben weitere reine UI-Refresh-Pfade.

### 7. Vorschau und Sicherheitsabstaende korrigieren

- [ ] In der Vorschau alle gesetzten Sicherheitsabstaende darstellen.
  `XRI` und `ZRI` werden jetzt mit derselben Semantik wie der Generator verarbeitet.
  Sichtbar werden sie weiterhin nur entsprechend der Auswahl:
  - `einfach`: nur `XRA` und `ZRA`
  - `erweitert`: zusaetzlich `XRI`
  - `alle`: zusaetzlich `ZRI`
  Offen bleibt die vollstaendige Sichtpruefung im eingebetteten Betrieb.

- [ ] Nicht gesetzte Sicherheitsabstaende weiterhin ausblenden.

- [ ] Darstellung fuer Innen- und Aussenbearbeitung optisch eindeutig unterscheiden.

- [ ] X-Achsenbeschriftung der Vorschau auf Durchmesserwerte umstellen.
  Generatorseitig und im Preview-Widget sind Durchmesserlabels jetzt umgestellt.
  Offen bleibt die Sichtpruefung im realen Panel.

### 8. Sichtbarkeitslogik der UI stabilisieren

- [ ] Ein- und Ausblenden nicht benoetigter Bedienelemente grundlegend ueberarbeiten.

- [ ] Sicherstellen, dass Sichtbarkeitsregeln reproduzierbar sind und nicht von der Reihenfolge vorheriger Bedienaktionen abhaengen.

- [ ] Verhindern, dass Widgets nach einer Umschaltung dauerhaft verschwinden.

- [ ] Sichtbarkeitszustand bei jedem relevanten Moduswechsel vollstaendig neu aus dem aktuellen Datenmodell ableiten.

- [ ] Alte Zustandsreste aus vorherigen Steps oder Reitern duerfen nicht uebernommen werden.

- [ ] Sichtbarkeitsregeln getrennt testen fuer:
  - Planen
  - Kontur
  - Abspanen
  - Gewinde
  - Einstich
  - Abstich
  - Bohren
  - Innen-/Aussenbearbeitung
  - Schruppen/Schlichten
  - G96/G97

### 9. Gewinde- und Freistichdaten ueberarbeiten

- [ ] Preset-Daten fuer Gewinde vollstaendig pruefen und korrigieren.

- [ ] Preset-Daten fuer DIN-Freistiche vollstaendig pruefen und korrigieren.

- [ ] Fehlende Werte ergaenzen.

- [ ] Platzhalterwerte `0` entfernen, sofern sie keine fachlich gueltige Bedeutung haben.

- [ ] Fuer jeden Preset-Datensatz Plausibilitaetspruefungen einfuehren:
  - Nenndurchmesser
  - Steigung
  - Gewindetiefe
  - erster Zustich
  - Spitzenversatz
  - Freistichbreite
  - Freistichtiefe
  - Innen-/Aussenvariante
  - Normbezeichnung

- [ ] Unvollstaendige Presets duerfen nicht stillschweigend uebernommen werden.
  Benutzerdefiniert bzw. unvollstaendige Preset-Daten werden generatorseitig nicht mehr als gueltiges Preset angewendet.
  Offen bleibt eine explizite Warnanzeige direkt in der UI.

- [ ] Freistich in der Vorschau geometrisch darstellen.

- [ ] Vorschau muss unterscheiden zwischen:
  - Aussenfreistich
  - Innenfreistich
  - Lage am Gewindeanfang
  - Lage am Gewindeende

- [ ] Position des Buttons `Preset uebernehmen` im Gewinde-Reiter korrigieren.
  Der Button ist aktuell oben links verrutscht und fast nicht lesbar.

- [ ] Button wieder an die urspruenglich vorgesehene, klar erkennbare Position setzen.

### 10. Drehzahlmodus pro Step in der UI

- [ ] In allen relevanten Reitern Auswahl zwischen konstanter Drehzahl und konstanter Schnittgeschwindigkeit sichtbar machen.

- [ ] Aktuell kann zwar eine Drehzahl eingegeben werden, eine Umschaltung zwischen `G97` und `G96` ist jedoch nicht vorhanden.

- [ ] Pro Step folgende Auswahl anbieten:
  - `Konstante Drehzahl (G97)`
  - `Konstante Schnittgeschwindigkeit (G96)`

- [ ] Abhaengig vom Modus die passenden Felder anzeigen:
  - bei `G97`: Drehzahl in `1/min`
  - bei `G96`: Schnittgeschwindigkeit in `m/min`
  - bei `G96`: maximale Spindeldrehzahl

- [ ] Nicht benoetigte Felder zuverlaessig ausblenden und beim Wechsel korrekt wieder einblenden.

- [ ] Save/Load, Dirty-State, Vorschau und Generator auf den Step-bezogenen Drehzahlmodus abstimmen.

### 11. Performance und Aktualisierungslogik

- [ ] Startzeit des Panels spaeter optimieren.
  Aktuell dauert der Start wieder etwa 15 Sekunden; zuvor waren etwa 4 Sekunden erreicht.

- [ ] Vorrangig die Reaktionszeit bei Eingaben verbessern.

- [ ] Verhindern, dass bei jeder einfachen Eingabe alle Reiter und alle Formulare vollstaendig durchsucht oder synchronisiert werden.

- [ ] Bei Aenderungen nur die unmittelbar betroffenen Daten und Ansichten aktualisieren.

- [ ] Kontureingaben duerfen keine mehrsekundige Blockierung verursachen.

- [ ] Vorschauaktualisierung entkoppeln oder zeitlich buendeln:
  - Debounce fuer schnelle Eingabefolgen
  - keine komplette Neuberechnung bei jedem Tastendruck
  - nur betroffene Vorschaugeometrie neu berechnen

- [ ] Signalverbindungen auf Mehrfachregistrierung pruefen.
  Mehrfach verbundene Signale koennen dieselbe Aktualisierung mehrfach ausloesen.

- [ ] Globale Durchlaeufe ueber alle Tabs, Widgets und Steps aus normalen Feld-Callbacks entfernen.

- [ ] Performance messen und dokumentieren fuer:
  - Panelstart
  - Laden eines Programms
  - Wechsel eines Steps
  - Aenderung eines einzelnen Zahlenfeldes
  - Bearbeitung einer Kontur
  - Aktualisierung der Vorschau

- [ ] Zielwerte festlegen:
  - normale Feldeingabe ohne wahrnehmbare Verzoegerung
  - Konturfeld-Aenderung deutlich unter 0,5 Sekunden
  - Panelstart wieder in Richtung des frueheren Standes von etwa 4 Sekunden


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

- Wiederholte UI-Helfer fuer Sprache, Uebersetzung, ComboBox-Befuellen und Tab-Bezeichnungen sind in `ui_helpers.py` zentralisiert.
- Generische Parameter-Lookups und die gemeinsame interne Safe-X-Berechnung liegen in `gcode_utils.py`; Groove, Roughing und Thread verwenden diese zentrale Implementierung.
- Das ungenutzte, intern unvollstaendige Alt-Paket `lathe_easystep/contour/` ist entfernt; die produktive Konturimplementierung liegt weiterhin in `contour_logic.py` und `contour_features.py`.
- Generator startet nicht mehr unbeabsichtigt in `O`-Subroutinen; Reihenfolge von Subroutinen und Hauptprogramm ist per Regressionstest abgesichert.
- `M30` beendet das Hauptprogramm am Ende; nach `M30` werden keine Subroutinen mehr ausgegeben.
- Zusaetzliche Nullbewegungen nach Werkzeugwechselpfaden sind generatorseitig per Regressionstest abgesichert.
- Innen-Abspanen verwendet keinen unplausiblen `G71`-Startdurchmesser mehr.
- Innen-Gewinde und Innen-Abspanen erzwingen jetzt ein plausibles `XRI`; ohne gueltiges `XRI` bricht die G-Code-Erzeugung ab.
- Innen-Gewinde und Innen-Abspanen verwenden jetzt op-spezifische sichere Anfahr-/Rueckzugsebenen ueber `XRI/ZRI`.
- Der Schlicht-Einfahrweg mit aktiver Schneidenradiuskorrektur ist fuer Innenkonturen korrigiert.
- Sprachumschaltung markiert den Programmkopf nicht mehr faelschlich als geaendert.
- Sprachumschaltung behaelt bei uebersetzten Comboboxen jetzt die internen `itemData` bei; Betriebsmodi wie `fixed/css` gehen beim Umschalten nicht mehr verloren.
- Sprachumschaltung wendet Text- und Button-Uebersetzungen jetzt auf alle Widgets mit passendem `objectName` im Panel-Baum an, nicht nur auf den ersten Resolver-Treffer.
- Fuer den oberen Bereich des Reiters `Programm` sind jetzt ebenfalls allgemeine Tooltips hinterlegt; der fruehere Bruch ab `XRA` ist code-seitig geschlossen.
- Fuer alle Reiter gibt es jetzt einen generischen Tooltip-Fallback: fehlende Feld-Tooltips werden aus zugeordneten Labels oder Formularzeilen abgeleitet, statt still leer zu bleiben.
- Vorschau-Helfer verarbeiten `XRI` und `ZRI` jetzt mit derselben Inkrement-/Absolut-Semantik wie der Generator.
  Die sichtbare Anzeige im Panel bleibt an die Auswahl `einfach` / `erweitert` / `alle` gebunden.
- X-Achsenbeschriftung der Vorschau zeigt in Drehdurchmesserprogrammierung jetzt Durchmesserwerte statt Radiuswerte.
- Neue Steps markieren beim Anlegen nicht mehr pauschal alle vorhandenen Steps als ungespeichert; Strukturwechsel markieren jetzt primaer das Programm und nur den neu angelegten Step.
- Gewinde-Presets werden nur noch bei vollstaendigen, plausiblen Preset-Daten angewendet; `Benutzerdefiniert` erzeugt keine impliziten Pseudo-Defaultwerte mehr.

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
