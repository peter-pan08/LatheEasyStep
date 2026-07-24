# Roadmap LatheEasyStep

Stand: 2026-07-24

LatheEasyStep soll ein werkstattnahes, konversationelles Drehpanel fuer
LinuxCNC werden. Die Roadmap beschreibt die Release-Ziele. Konkrete offene
Arbeitspunkte stehen in der [TODO.md](TODO.md), erledigte Aenderungen im
[CHANGELOG.md](CHANGELOG.md).

## Ausgangsstand

- `main`: Version 0.7.0 als lauffaehige Basis
- `dev`: Entwicklungsstand fuer die kommende 0.8.0
- neue Funktionen und Generatoraenderungen werden zuerst auf `dev` getestet
- Sicherheits- und Generatorlogik wird an LinuxCNC-Verhalten, Backplot und
  realen Trockenlaeufen gemessen

Der aktuelle `dev`-Umfang ist wegen der neuen Sicherheits-, Kontur-,
Freistich-, Gewinde- und UI-Funktionen als Entwicklung zu 0.8.0 einzuordnen,
nicht als kleine Patchversion 0.7.1.

## 0.8.0-alpha - Sicherheits- und Realtest-Gate

Ziel: Der Generator darf keine offensichtlich unsicheren, leeren oder
widerspruechlich gewarnten Bearbeitungsablaeufe akzeptieren.

Umfang:

- sichere Anfahrt zwischen aufeinanderfolgenden Operationen
- leere Schruppoperationen als Fehler abbrechen
- Innen-Schruppen Parallel-Z mit vorhandenem Bohrungsdurchmesser verifizieren
- ZRA/ZRI-Auslegung fuer relative und absolute Werte festlegen
- Innen- und Aussenbearbeitung getrennt pruefen
- Referenzprogramme regenerieren
- vollstaendige Test-Suite und echte PyQt5-Tests
- LinuxCNC-Parser, Backplot und Trockenlauf der Sicherheitsfaelle

Abnahmekriterien:

- kein bekannter sicherheitskritischer P0-Punkt offen
- keine diagonale Eilgangbewegung durch bekanntes Rohmaterial
- kein erfolgreich erzeugter Schruppstep ohne reale Schnittbewegung
- Warnung und ausgegebener Fahrweg widersprechen sich nicht

## 0.8.0 - Belastbare Kontur- und Innenbearbeitung

Ziel: Die angebotenen Standardkonturen sind innen und aussen nachvollziehbar
nutzbar und verwenden in Vorschau und G-Code dieselbe Geometrie.

Umfang:

- zylindrische Innenkontur
- Innenstufe
- Innenkonus
- Innenradius
- Innenkontur mit Freistich
- Innen-Schruppen mit anschliessendem Schlichten
- lokale DIN-Freistiche an geeigneten Kontursegmenten
- identische Freistichgeometrie in Vorschau, Subroutine und Schlichtweg
- Linien und Boegen bis zur finalen G1/G2/G3-Ausgabe als Primitive erhalten
- G96/G97 pro Operation in UI, Save/Load und Generator
- G76-Referenzfaelle fuer M12x1.75 und M30x3.5
- verbleibende Sichtbarkeits- und Innenkontur-Regressionen

Abnahmekriterien:

- alle angebotenen 0.8.0-Konturfaelle besitzen Referenzprogramme
- Vorschau und ausgegebener Konturweg stimmen geometrisch ueberein
- Innen- und Aussenbearbeitung sind getrennt getestet
- alle Referenzprogramme werden von LinuxCNC ohne Generator- oder Parserfehler
  angenommen

## 0.9.0 - Bedienung und technische Konsolidierung

Ziel: Die funktionale Basis wird leichter wartbar, besser testbar und im
Werkstattalltag eindeutiger.

Umfang:

- Handler schrittweise weiter verkleinern
- Gewinde-, Tooltip-, Programmkopf- und Widget-Logik in getrennte Module
  auslagern
- strikte ID-only-UI- und Spracharchitektur abschliessen
- Step-Kommentare und Exportnummerierung normalisieren
- Werkzeugdaten fuer Werkzeugwechsel zentral normalisieren
- Bewegungsposition und Modalzustaende schrittweise zentral verwalten
- redundante Bewegungen reduzieren, ohne die robuste explizite Ausgabe zu
  verlieren

Nicht Bestandteil der ersten 0.9.0-Arbeiten ist ein Komplettumbau aller
UI-Dateien in einem Schritt. Jede Extraktion wird einzeln getestet.

## 1.0.0 - Werkstattgeeigneter dokumentierter Stand

Version 1.0 bedeutet nicht, dass jede denkbare Drehoperation vorhanden ist.
Sie bedeutet, dass der dokumentierte Funktionsumfang reproduzierbar und
fachlich verifiziert ist.

Voraussetzungen:

- keine offenen sicherheitskritischen Punkte
- jede angebotene Bearbeitungsart besitzt mindestens ein Referenzprogramm
- Innen- und Aussenvarianten sind getrennt getestet
- Save/Load-Roundtrips fuer aktuelle und unterstuetzte aeltere Dateien
- LinuxCNC-Parsing und Backplot aller Referenzprogramme
- dokumentierte Trockenlaeufe an der realen Maschine
- konsistente Vorschau- und G-Code-Geometrie
- definierte Maschinenprofile, Rueckzugsebenen und Futter-Sperrzonen
- verstaendliche Fehlermeldungen statt fragwuerdiger G-Code-Ausgabe
- Release-Tag, konsistentes Changelog und aktualisierte Bedienhinweise

## Nach 1.0 / spaetere Erweiterungen

- vollstaendige Aufteilung der monolithischen `lathe_easystep.ui`
- weitergehende Keilnut- und Verzahnungsfunktionen
- zusaetzliche Maschinenprofile und Werkzeugbibliotheken
- weitere Automatisierung von LinuxCNC-Simulations- und Referenztests
