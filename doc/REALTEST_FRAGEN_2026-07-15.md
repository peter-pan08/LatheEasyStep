# Realtest-Fragen LatheEasyStep

Stand: 2026-07-24

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
- Antwort: erster Wechsel funktioniert jetzt wie gewuenscht
- Status: umgesetzt - Ursache gefunden und behoben (Vorab-Validierung in
  `generate_program_gcode()` mutierte `_current_tool` und beeinflusste damit
  den echten Erzeugungsdurchlauf; siehe Changelog "erster Werkzeugwechsel")

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
- Status: offen; Messung bleibt unter LES-027 eingeplant

## C. Generator / reale Fahrwege

### 8. Bohren: Rueckzug nach Zyklus
- Test:
  - Bohrprogramm ausfuehren / Backplot ansehen
- Frage:
  - Welche Rueckzugsregel ist fachlich korrekt?
  - Nur axial auf Z?
  - Danach auf aeussere Safe-Plane?
  - Eigene Bohr-Sonderregel?
- Antwort: ist gerade ok
- Status: bestaetigt; Bohren nutzt jetzt denselben `emit_approach()`-Helfer wie
  Abspanen/Einstich statt einer eigenen, abweichenden Anfahrlogik

### 9. Innen-Schruppen Parallel-Z Materialmodell
- Test:
  - Innen-Schruppen mit vorhandener Bohrung und anschliessender Fertigkontur pruefen
- Frage:
  - Ist die Zustellrichtung von kleinem zu groesserem Durchmesser fachlich korrekt?
  - Falls nicht: welches konkrete Gegenbeispiel?
- Antwort: natürlich, denn die bohrung ist das was an material abgetragen wird und was frei ist, der rest zum größeren durchmesser muss ja erst abgespant werden.
- Status: Zustellrichtung bestaetigt korrekt. Bei der Untersuchung zusaetzlich
  einen realen, schwerwiegenden Bug gefunden und behoben: Innen-Abspanen nutzte
  fuer viele Innenkonturen (vom Bohrungsgrund zur Oeffnung definiert, Z steigt
  monoton) keinen `G71`-Zyklus, sondern eine grobe Move-based-Ersatzloesung,
  weil die G71-Eignungspruefung nur fallende Z-Werte akzeptierte. Siehe
  Changelog/TODO LES-003 fuer Details (`is_monotonic_z()` ergaenzt)

### 10. `safe_z` / ZRA/ZRI relativ vs. absolut bei `ABSPANEN`
- Test:
  - Fall mit relativem `ZRA`/`ZRI` pruefen, z. B. `0.0` bei `absolute=False`
- Frage:
  - Ist fuer `ABSPANEN` der rohe Wert korrekt oder muss wirklich `ZA + ZRI` bzw. `ZA + ZRA` verwendet werden?
- Antwort: augenscheinlich wird diese regel beachtet, wird schon meim generieren des programm gemeldet.
- Status: beantwortet; im Realtest ist kein konkreter Fehler erkennbar.
  Relative und absolute Rueckzugswerte bleiben als automatisierte
  Generatorregression unter LES-003/LES-006 erhalten. Bei einem konkreten
  Gegenbeispiel wird dieser Punkt erneut geoeffnet.

### 11. Innenkonturformen
- Test:
  - Innenstufe
  - Innenkonus
  - Innenradius
  - Innenkontur mit Freistich
- Frage:
  - Welche Form ist generatorseitig korrekt, welche nicht?
  - Bitte je Fall Problemstelle / Step / G-Code-Zeile nennen.
- Antwort: es ist scheinbar alles, bis auf den Freistich ok
- Status: Innenstufe/Innenkonus/Innenradius bestaetigt korrekt. Der Freistich
  (DIN-Freistich mitten in einer Kontur) ist der bereits unter LES-010/LES-011
  dokumentierte, bekannte offene Punkt (Freistich-Splicing nur am Anfang/Ende
  der GESAMTEN Kontur unterstuetzt, nicht an beliebiger Segmentposition) -
  keine neue Erkenntnis, aber durch den Realtest bestaetigt/priorisiert

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
- Antwort: grundsaetzlich erlaubt, mit Warnung
- Status: entschieden und umgesetzt. Identische Operationen werden nicht
  geloescht oder automatisch veraendert, sondern ueber
  `lathe_easystep/checks.py::_check_duplicate_operations` als Warnung im
  Vorschau-/Programmcheck gemeldet; abgesichert durch
  `tests/test_duplicate_operation_check.py`.

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

## E. Naechste verbindliche Abnahmetests

Diese Punkte pruefen gezielt die seit dem ersten Realtest neu geaenderten oder
noch offenen Generatorpfade. Sie sind erst abgeschlossen, wenn Ergebnis und
verwendete Referenzdatei dokumentiert sind.

### 16. G2/G3-Bogen mit echtem X-Zentrumsversatz

- Voraussetzung:
  - Kontur mit `I != 0` im Durchmessermodus G7
  - einmal direkter Schlichtweg, einmal G71/G72-Kontur-Subroutine
- Test:
  - beide Programme mit LinuxCNC parsen und im Backplot kontrollieren
  - auf die fruehere Meldung
    `Radius to end of arc differs from radius to start` achten
  - Bogenstart, Bogenende und Drehrichtung mit der Sollkontur vergleichen
- Erfolgreich, wenn:
  - kein Radius-/Parserfehler entsteht
  - direkter Pfad und Zyklus-Sub dieselbe Geometrie zeigen
- Antwort:
- Status: offen -> LES-012/LES-030

### 17. Innen-G71 mit steigender und fallender Z-Kontur

- Voraussetzung:
  - vorhandene Bohrung als freie Materialgrenze
  - zwei gleichwertige Innenkonturen mit umgekehrter Punktreihenfolge
- Test:
  - kontrollieren, dass beide Faelle G71 statt eines unbegruendeten
    Move-based-Fallbacks verwenden
  - Zustellung vom freien Bohrungsdurchmesser zur Fertigkontur pruefen
  - sicherstellen, dass XRI nur Einfahr-/Rueckzugsebene und keine Schnittbahn ist
  - Anfahrt, Schlichtaufmass und Rueckzug im Backplot vergleichen
- Erfolgreich, wenn:
  - beide Konturrichtungen denselben Materialabtrag erzeugen
  - Parser, Backplot und anschliessender Trockenlauf unauffaellig sind
- Antwort:
- Status: offen -> LES-003/LES-005/LES-015/LES-030

### 18. Gemischtes Programm G96 -> G97 -> G96

- Voraussetzung:
  - erste Drehoperation mit CSS
  - Bohren mit Festdrehzahl
  - anschliessende Dreh-/Gewindeoperation wieder mit CSS
- Test:
  - `G96 S` muss Vc in m/min enthalten, `G97 S` die Drehzahl in U/min
  - `D` muss die programmweite CSS-Maximaldrehzahl enthalten
  - Save/Load darf die drei Operationsmodi und Werte nicht vertauschen
  - nach Umsetzung der sicheren CSS-Anfahrt: G97 waehrend der Anfahrt,
    G96 erst an der festgelegten Bearbeitungsposition
- Erfolgreich, wenn:
  - keine Operation Werte oder Modalzustand der vorherigen Operation erbt
  - LinuxCNC-Parser und Backplot die erwartete Umschaltfolge zeigen
- Antwort:
- Status: offen -> LES-013/LES-030

### 19. Planen mit Kantenform Radius

- Voraussetzung:
  - erst nach Umsetzung von LES-036
- Test:
  - Radius in Schruppen, Schlichten und Schruppen+Schlichten erzeugen
  - Preview, G-Code und Backplot vergleichen
  - kleinen, maximal gueltigen und ungueltig grossen Radius pruefen
  - Save/Load mit String-ID sowie einer alten numerischen Datei pruefen
- Erfolgreich, wenn:
  - gueltige Radien als korrekte G2/G3-Geometrie erscheinen
  - ungueltige Radien vor der G-Code-Ausgabe klar abgewiesen werden
- Antwort:
- Status: offen -> LES-036/LES-030

