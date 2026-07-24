# Roadmap LatheEasyStep

Stand: 2026-07-24

LatheEasyStep soll ein werkstattnahes, konversationelles Drehpanel fuer
LinuxCNC werden. Die Roadmap beschreibt Release-Ziele und Abhaengigkeiten.
Die vollstaendige Aufgabenliste steht in der [TODO.md](TODO.md), reale
Verifikation in
[doc/REALTEST_FRAGEN_2026-07-15.md](doc/REALTEST_FRAGEN_2026-07-15.md).

## Ausgangsstand

- `main`: Version 0.7.0 als lauffaehige Basis
- `dev`: aktueller Entwicklungsstand fuer 0.8.0; `main` bleibt die stabile Basis
- aktueller Teststand: `364 passed, 7 skipped`
- UI-Shell und acht Reiter sind bereits in Teil-UIs getrennt
- Deutsch, Englisch und Spanisch besitzen jeweils 1.022 identische,
  nichtleere Sprachschluessel
- G53-Werkzeugwechsel, erster Werkzeugwechsel, Tooltips, Sprachumschaltung,
  Slice-/Frontview, Bohren-Anfahrt, G76-Plausibilitaet und `rough_finish`
  wurden praktisch bestaetigt oder umgesetzt

Der Umfang auf `dev` ist als Entwicklung zu Version 0.8.0 einzuordnen, nicht
als kleine Patchversion 0.7.1.

## 0.8.0-alpha - Sicherheits- und Realtest-Gate

Ziel: Keine bekannte Operation darf unsichere, leere oder widerspruechlich
gewarnte Fahrwege erzeugen.

Verbindliche Aufgaben:

- LES-001 sichere Anfahrt zwischen Operationen
- LES-003 Innen-Schruppen Parallel-Z abschliessend verifizieren
- LES-005 Innen-Schlichtanfahrt und Rueckzug absichern

Abnahmekriterien:

- kein offener P0-Punkt
- kein diagonaler Eilgang allein aufgrund von `_is_at_safe`
- kein erfolgreicher Roughing-Step ohne reale Schnittbewegung
- Innen-Schruppen besitzt einen bestaetigten Referenz-, Backplot- und
  Trockenlauffall fuer monoton steigende und fallende Z-Konturen
- mindestens ein G7-Bogen mit `I != 0` wird sowohl im direkten Schlichtweg
  als auch in der G71/G72-Subroutine vom LinuxCNC-Parser akzeptiert
- Warnung und ausgegebener Fahrweg widersprechen sich nicht
- komplette Testsuite, Referenzprogramme und LinuxCNC-Parser laufen erfolgreich

## 0.8.0 - Belastbare Kontur- und Innenbearbeitung

Ziel: Die angebotenen Konturfaelle sind innen und aussen nachvollziehbar
nutzbar und verwenden in Vorschau und G-Code dieselbe Geometrie.

Verbindliche Aufgaben:

- LES-006 Rueckzugsstrategie je Bearbeitungsart
- LES-010 lokale DIN-Freistichgeometrie
- LES-011 einheitliche Freistichdarstellung
- LES-012 G1/G2/G3-Primitive durchgaengig erhalten
- LES-013 sichere CSS-Umschaltung nach per-Operation-G96/G97
- LES-015 automatisierte Innenkontur-Testmatrix
- LES-016 fachlich definierte UI-Sichtbarkeitsregeln
- LES-019 fehlende DIN-76-Presets
- LES-030 LinuxCNC-Simulationsmatrix
- LES-036 Kantenform "Radius" beim Planen

Abnahmekriterien:

- zylindrische Innenkontur, Innenstufe, Innenkonus, Innenradius und
  Innenfreistich besitzen Referenzfaelle
- Vorschau, Subroutine und Schlichtweg verwenden dieselben Primitive
- lokale Freistiche funktionieren auch mitten in einer laengeren Kontur
- keine produktiv ungenutzte Generator-Kopie wird von Tests als Referenz benutzt
- G96/G97-Wechsel zwischen Operationen verwechseln weder Vc noch Drehzahl;
  CSS wird erst an der fachlich festgelegten Position aktiviert
- die im UI angebotene Planen-Kantenform "Radius" besitzt Generator-,
  Preview-, Save/Load- und LinuxCNC-Referenztests
- alle angebotenen 0.8.0-Faelle werden von LinuxCNC ohne Parserfehler angenommen

## 0.9.0 - Bedienung und technische Konsolidierung

Ziel: Die funktionale Basis wird leichter wartbar, besser testbar und im
Werkstattalltag eindeutiger.

Aufgabenbereiche:

- LES-018 optionale G70-Wiederverwendung
- LES-020 weitere Handler-Extraktionen
- LES-022 zentraler Bewegungs- und Modalzustand
- LES-023 Step-Kommentare und Exportnummerierung
- LES-024 Vorschau-/Step-UI und Controllergrenzen
- LES-027 Embedded-/Standalone-Performance
- LES-028 normalisierte Werkzeug- und G76-Daten
- LES-031 redundante Bewegungen und Modals
- LES-032 Werkzeuggeometrie und Tooltable-Plausibilitaet
- LES-033 reale Gewindevorschau
- LES-034 fachlich getrennte Preview-Pipeline
- LES-035 Embedded-/Standalone-Paritaet

Die bereits erledigte Trennung der acht Bearbeitungsreiter wird nicht erneut
geplant. Offen bleiben Vorschau, Step-Verwaltung und saubere Schnittstellen
zwischen den Modulen.

## 1.0.0 - Werkstattgeeigneter dokumentierter Stand

Version 1.0 bedeutet nicht, dass jede denkbare Drehoperation vorhanden ist.
Sie bedeutet, dass der dokumentierte Funktionsumfang reproduzierbar und
fachlich verifiziert ist.

Voraussetzungen:

- keine offenen P0- oder P1-Aufgaben
- jede angebotene Bearbeitungsart besitzt mindestens ein Referenzprogramm
- Innen- und Aussenvarianten sind getrennt getestet
- Save/Load-Roundtrips fuer aktuelle und unterstuetzte aeltere Dateien
- LinuxCNC-Parsing und Backplot aller Referenzprogramme
- dokumentierte Trockenlaeufe an der realen Maschine
- konsistente Vorschau- und G-Code-Geometrie
- definierte Maschinenprofile, Rueckzugsebenen und Futter-Sperrzonen
- verstaendliche Fehlermeldungen statt fragwuerdiger G-Code-Ausgabe
- reproduzierbarer Teststand; jeder Skip ist begruendet und kein
  sicherheitsrelevanter Generatorfall wird im regulaeren Lauf uebersprungen
- Release-Tag, Changelog und Bedienhinweise

## Nach 1.0

- weitergehende Keilnut- und Verzahnungsfunktionen
- weitere Maschinen-, Futter- und Werkzeugprofile
- automatisierte LinuxCNC-Simulationslaeufe
- zusaetzliche Abspanstrategien