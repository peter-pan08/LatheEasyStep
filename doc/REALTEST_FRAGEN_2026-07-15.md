# Realtest-Fragen LatheEasyStep

Stand: 2026-07-15

Diese Datei ist fuer Punkte gedacht, die ich lokal nicht risikofrei verifizieren
kann. Bitte die Antworten direkt unter den Fragen eintragen oder jeweils mit
`Antwort:` ergaenzen.

## A. LinuxCNC / QtVCP / Werkzeugwechsel

### 1. `G53`-Werkzeugwechsel
- Test:
  - Programm mit mindestens zwei Werkzeugen laden
  - verschiedene Werkstuecknullpunkte aktivieren
  - Werkzeugwechsel ausfuehren
- Frage:
  - Faehren alle `G53`-Wechsel exakt zur erwarteten Maschinenposition?
- Antwort: funktioniert
- Status: bestaetigt, keine Aenderung noetig

### 2. Bewegung direkt nach `M6`
- Test:
  - denselben Werkzeugwechsel mit realer Konfiguration beobachten
- Frage:
  - Siehst du nach `T.. M6` zusaetzliche Bewegungen, die NICHT direkt aus dem generierten G-Code kommen?
  - Falls ja: welche Achse, welche Richtung, nach welchem Werkzeug?
- Antwort: nein, alles korrekt
- Status: bestaetigt, keine Aenderung noetig

### 3. Erster Werkzeugwechsel
- Test:
  - Programmstart mit Werkzeugwechsel auf erstes Werkzeug
- Frage:
  - Soll auch vor dem ERSTEN `M6` immer erst der definierte Werkzeugwechselpunkt angefahren werden?
  - Oder nur vor Folgewechseln?
- Antwort: erster wechsel leider nicht am werkzeugwechselpunkt
- Status: umgesetzt - Ursache gefunden und behoben (Vorab-Validierung in
  `generate_program_gcode()` mutierte `_current_tool` und pollute damit den
  echten Erzeugungsdurchlauf; siehe Changelog "erster Werkzeugwechsel")

## B. UI / Panel / Embedded-Betrieb

### 4. Tooltips
- Test:
  - alle Reiter einmal oeffnen
  - auch dynamische Widgets pruefen
- Frage:
  - Fehlen noch Tooltips? Wenn ja: Reiter, Feldname, Sprache notieren.
- Antwort: tooltips scheinen gerade alle zu funktionieren
- Status: bestaetigt, keine Aenderung noetig

### 5. Sprachumschaltung
- Test:
  - Deutsch / Englisch / Spanisch umschalten
- Frage:
  - Bleibt irgendwo sichtbarer Text in der falschen Sprache stehen?
  - Bitte Reiter + Text nennen.
- Antwort: gerade alle ok
- Status: bestaetigt, keine Aenderung noetig

### 6. Vorschau / Slice / Frontview
- Test:
  - mehrere Z-Positionen durchfahren
  - Innen-/Aussenkonturen, Gewinde, Einstiche pruefen
- Frage:
  - Welche Z-Positionen sehen noch fachlich falsch aus?
  - Bitte je Fall angeben:
    - Step / Operation
    - erwartete Geometrie
    - tatsaechlich gezeigte Geometrie
- Antwort: gerade sieht es alles ok aus
- Status: bestaetigt (zusaetzlich wurden in dieser Session zwei reale Fehler
  in der Schnittansicht gefunden und behoben: ein fehlender Import fuehrte zu
  einem Absturz beim Malen der Frontansicht, und ein zu haeufig ausgeloester
  Vorschau-Refresh setzte die per Ziehen gewaehlte Schnitt-Z-Position
  unbemerkt zurueck - siehe Changelog)

### 7. Startzeit / Reaktionszeit
- Test:
  - Panel frisch starten
  - Reiterwechsel und Stepwechsel pruefen
- Frage:
  - Subjektiv ok oder zu traege?
  - Falls moeglich: Startzeit bis GUI sichtbar, auffaellige Reiter/Funktionen notieren.
- Antwort:

## C. Generator / reale Fahrwege

### 8. Bohren: Rueckzug nach Zyklus
- Test:
  - Bohrprogramm ausfuehren / Backplot ansehen
- Frage:
  - Welche Rueckzugsregel ist fachlich korrekt?
  - Nur axial auf Z?
  - Danach auf aeussere Safe-Plane?
  - Eigene Bohr-Sonderregel?
- Antwort: die anfahrt sollte so sein wie die abfahrt. abfahrt ist gut
- Status: umgesetzt - Bohren nutzt jetzt denselben `emit_approach()`-Helfer wie
  Abspanen/Einstich statt einer eigenen, abweichenden Anfahrlogik

### 9. Innen-Schruppen Parallel-Z Materialmodell
- Test:
  - Innen-Schruppen mit vorhandener Bohrung und anschliessender Fertigkontur pruefen
- Frage:
  - Ist die Zustellrichtung von kleinem zu groesserem Durchmesser fachlich korrekt?
  - Falls nicht: welches konkrete Gegenbeispiel?
- Antwort:

### 10. `safe_z` / ZRA/ZRI relativ vs. absolut bei `ABSPANEN`
- Test:
  - Fall mit relativem `ZRA`/`ZRI` pruefen, z. B. `0.0` bei `absolute=False`
- Frage:
  - Ist fuer `ABSPANEN` der rohe Wert korrekt oder muss wirklich `ZA + ZRI` bzw. `ZA + ZRA` verwendet werden?
- Antwort: augenscheinlich wird diese regel beachtet, wird schon meim generieren des programm gemeldet.
- Status: als "kein Aenderungsbedarf ersichtlich" aus der Blockiert-Liste in
  TODO.md entfernt. Der rohe Wert wird technisch weiterhin ohne `*_absolute`-
  Beruecksichtigung verwendet (siehe Code-Kommentar in `gcode_roughing.py`) -
  falls doch einmal ein konkretes Gegenbeispiel auftaucht, bitte hier erneut
  vermerken.

### 11. Innenkonturformen
- Test:
  - Innenstufe
  - Innenkonus
  - Innenradius
  - Innenkontur mit Freistich
- Frage:
  - Welche Form ist generatorseitig korrekt, welche nicht?
  - Bitte je Fall Problemstelle / Step / G-Code-Zeile nennen.
- Antwort:

### 12. G76-Masssystem
- Test:
  - isolierte LinuxCNC-Simulationsfaelle fuer M12x1.75 und M30x3.5
- Frage:
  - Welche Parameter unter `G7` sind radial, welche im Durchmesser zu verstehen?
  - Insbesondere `I`, `J`, `K`.
- Antwort: generierte werte scheinen zu passen, soweit ich das aus der simulation sagen kann.
- Status: bestaetigt, keine Aenderung noetig

## D. Nutzerentscheidung / Fachentscheidung

### 13. Doppelte Operationen beim Step-Laden
- Frage:
  - Soll `Step laden` identische Operationen mehrfach einfuegen duerfen?
  - Oder soll bei Dubletten gewarnt / ersetzt werden?
- Antwort:

### 14. `rough_finish` im UI
- Frage:
  - Soll im Abspanen-/Einstich-UI ein drittes Combo-Item `Schruppen + Schlichten` sichtbar werden?
- Antwort: ja
- Status: umgesetzt - drittes `<item>` in `ui_parts/tabParting.ui` ergaenzt,
  fehlender `"rough_finish"`-Eintrag in `PARTING_MODE_INDEX` (gcode_roughing.py)
  ebenfalls ergaenzt (sonst waere die Auswahl stillschweigend als Schruppen
  behandelt worden)

### 15. Generator behandelt Kontur-/Rohteilmasse als Fahrwege
- Frage:
  - Bitte ein konkretes Beispiel nennen:
    - Step
    - erwartete Zeile
    - tatsaechlich generierte Zeile
- Antwort: schau dir die testdatei an, innenabspanen ist keine strategie, das ist blödsinn, was da generiert wird.
- Status: umgesetzt - realer Bug gefunden und behoben: `rough_turn_parallel_x()`
  mergte seine Z-Intervalle pro X-Band nicht (anders als das Pendant
  `rough_turn_parallel_z()`), wodurch sich beruehrende Segmente (Bohrungswand
  trifft Fase) zu doppelten/ueberlappenden Schnittbewegungen fuehrten. Die in
  der Frage erwaehnte fehlende Strategie selbst war zum Zeitpunkt der
  Untersuchung bereits durch den Nutzer im Panel korrigiert (`slice_strategy`
  stand in der aktuellen Test.lse bereits korrekt auf "parallel_z")
