# Implementation Plan: NGC Generator Refactoring

## Status

Dieser Plan ist inhaltlich abgearbeitet und dient nur noch als Referenz.
Die beschriebenen Generator- und Sicherheitsphasen wurden laut aktuellem
Projektstand umgesetzt und in den Abschlussdokumenten dokumentiert.

Relevante Referenzen:
- `PHASES_COMPLETION_REPORT.md`
- `FINAL_SUMMARY.md`
- `IMPLEMENTATION_SUMMARY.md`

---

## Abgeschlossene Phasen

- [x] Phase 1: Programmkopf mit Sicherheits-Kommentaren
- [x] Phase 2: Tool Tracking
- [x] Phase 3: Explizite Anfahrbewegungen
- [x] Phase 4: Intelligentes Abfahren
- [x] Phase 5: Kontur-Logik
- [x] Phase 6: Modals vor Zyklen
- [x] Phase 7: Tests und Validierung der Generator-Änderungen

---

## Historischer Umfang

Die ursprünglichen Ziele dieses Plans waren:

1. Sicherheits-Kommentare im Programmkopf
2. Intelligente Werkzeugwechsel
3. Explizite, zahlenbasierte Anfahrbewegungen
4. Intelligentes Abfahren nach Bearbeitung
5. Konturbehandlung ohne versteckte Geometrie-Annahmen
6. Vollständige Modals vor G71/G72/G81/G76 usw.
7. Generator-Validierung mit Test- und NGC-Prüfung

Diese Punkte bleiben als Designvorgabe gültig, sind aber nicht mehr als
offene Roadmap zu verstehen.

---

## Offene Folgearbeiten

Die aktuellen offenen Arbeiten liegen nicht mehr primär im Generator-Plan,
sondern in angrenzenden Bereichen:

- UI-/Handler-Regressionen im Testkontext und Embedded-Kontext
- Preview-Haertung: klare Trennung zwischen Werkstueckkontur, Bearbeitungsbild und Hilfsgeometrie
- Preview-Haertung: keine impliziten oder "phantomhaften" Verbindungslinien bzw. Default-Hilfslinien
- Preview-Restpunkt: Programmkopf-Geometrie soll ohne vorherigen Doppelklick sofort stabil sichtbar sein
- Preview-Restpunkt: Gewindegeometrie soll die eingestellten Werte fachlich abbilden, nicht nur symbolisches Zickzack
- Dokumentation auf einen konsistenten Projektstatus bringen
- README und Developer Notes auf den realen Werkstatt-Workflow zuschneiden
- Weitere Sicherheits- und Integrationstests mit realen Maschinenprofilen
