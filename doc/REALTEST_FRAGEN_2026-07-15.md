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
- Status: offen, 0.8.0-Blocker fuer den ausstehenden LinuxCNC-Backplot-/
  SIM-Nachweis; der reale Maschinenlauf bleibt dem 1.0.0-Gate vorbehalten ->
  LES-003/LES-015/LES-030
