# Realtest-Fragen LatheEasyStep

Stand: 2026-08-22

Diese Datei ist fuer Punkte gedacht, die ich lokal nicht risikofrei verifizieren
kann. Bitte die Antworten direkt unter den Fragen eintragen oder jeweils mit
`Antwort:` ergaenzen. Beantwortete und umgesetzte Fragen werden aus dieser
Datei entfernt und im `CHANGELOG.md` dokumentiert.

## 7. Startzeit / Reaktionszeit

- Test:
  - Panel frisch starten
  - Reiterwechsel und Stepwechsel pruefen
- Frage:
  - Subjektiv ok oder zu traege?
  - Falls moeglich: Startzeit bis GUI sichtbar, auffaellige Reiter/Funktionen notieren.
- Antwort: startzeit momentan wieder über 20 sec, also viel zu lange

## Naechste verbindliche Abnahmetests

Diese Punkte pruefen gezielt die seit dem ersten Realtest neu geaenderten oder
noch offenen Generatorpfade. Sie sind erst abgeschlossen, wenn Ergebnis und
verwendete Referenzdatei dokumentiert sind.

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
- Antwort: sicherstellen das die aus den punkten generierte kontur beachtet wird, die reihenvolge, aus welcher richtung programiert wurde darf keinen einfluss auf den generierten code haben!
- Stand 2026-08-22: die geforderte Richtungsunabhaengigkeit ist umgesetzt
  und automatisiert getestet (`is_monotonic_z()` akzeptiert steigend UND
  fallend, `test_internal_roughing_never_uses_g71_g72_cycle` prueft beide
  Punktreihenfolgen der realen Nutzerkontur auf identisches Ergebnis) sowie
  vom Nutzer am Panel bestaetigt ("innen drehen ... funktioniert"). Die
  Materialabtrag-Zustellung selbst war zusaetzlich fehlerhaft (siehe
  CHANGELOG "Innen-Schruppen erzeugt jetzt echte Mehrfachpaesse") und ist
  jetzt ebenfalls behoben und real bestaetigt.
- Status: offen, nur noch fuer den ausstehenden LinuxCNC-Backplot/Trockenlauf
  am realen Referenzteil -> LES-003/LES-015/LES-030

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

### 20. Automatischer DIN-76-Freistich am Gewindeende

- Voraussetzung:
  - je ein Aussen- und Innengewinde mit aktivem automatischem DIN-76-Freistich
  - die zugeordnete Abspan-Kontur muss den Gewindedurchmesser vor und nach dem
    Gewindeende enthalten
- Test:
  - Programm generieren und in LinuxCNC laden
  - im Backplot pruefen, dass der Freistich um das Gewindeende liegt, nicht am
    Ende der gesamten Kontur
  - pruefen, dass die Gewindespur um die angezeigte Ueberdeckung `f` in den
    Freistich hineinlaeuft
  - Aussenfreistich muss radial nach innen, Innenfreistich radial nach aussen
    gehen
  - Gegenprobe: die passende zylindrische Konturstrecke kuerzen oder entfernen;
    die Erzeugung muss mit einer Zuordnungsfehlermeldung abbrechen
- Erfolgreich, wenn:
  - Parser und Backplot fehlerfrei sind
  - Vorschau und Backplot dieselbe Freistichlage zeigen
  - kein Freistich im Vollmaterial oder am Konturende entsteht
- Antwort:
- Stand 2026-08-22: Placement-Logik ist umgesetzt und mit `rs274`
  real gegen den LinuxCNC-Interpreter verifiziert (Freistich am
  Gewindeende, nicht am Konturende; Aussen-/Innenrichtung korrekt; die
  zugehoerige Kontur "abdrehen" des Nutzers wurde per echtem Panel-Test
  bestaetigt: "vorschau und gcode generierung mit freistich ...
  funktioniert"). Offen bleibt ausschliesslich der reale Trockenlauf mit
  tatsaechlich geschnittenem Gewinde an der Maschine.
- Status: offen, nur noch fuer den realen Trockenlauf -> LES-037/LES-030
