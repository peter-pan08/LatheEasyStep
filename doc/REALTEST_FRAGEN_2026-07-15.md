# Realtest-Fragen LatheEasyStep

Stand: 2026-07-24

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
- Antwort:

## Naechste verbindliche Abnahmetests

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
