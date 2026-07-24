# TODO LatheEasyStep

Stand: 2026-07-24

Diese Datei ist die verbindliche Liste aller offenen Aufgaben. Erledigte Punkte
werden entfernt und im `CHANGELOG.md` dokumentiert. Release-Ziele und
Abhaengigkeiten stehen in der [ROADMAP.md](ROADMAP.md), reale Tests in
[doc/REALTEST_FRAGEN_2026-07-15.md](doc/REALTEST_FRAGEN_2026-07-15.md).

## Aktuell verifizierte Basis

- `main`: Version 0.7.0 als lauffaehige Basis
- `dev`: aktueller Entwicklungsstand fuer 0.8.0; `main` bleibt die stabile Basis
- Teststand: `364 passed, 7 skipped`
- UI-Shell und acht Reiter-Teil-UIs sind getrennt und werden ueber
  `lathe_easystep/ui_split.py` geladen
- `de.lng`, `en.lng` und `es.lng` enthalten jeweils 1.022 identische,
  nichtleere und eindeutige Sprachschluessel
- derzeit keine offenen GitHub-Issues; diese Datei ist der Aufgabenbestand

Aufwand:

- `S`: wenige Stunden bis etwa ein Tag
- `M`: ein bis drei Entwicklungstage
- `L`: mehrere Tage mit Tests und Simulation
- `XL`: groessere Architekturarbeit in mehreren Etappen

Prioritaeten:

- `P0`: Sicherheit, falsche Fahrwege oder ungueltige Programmausgabe
- `P1`: fachliche Vollstaendigkeit und hoher praktischer Nutzen
- `P2`: Bedienkomfort, Wartbarkeit und langfristige Architektur

## Priorisierter Arbeitsindex

| ID | Prio | Aufgabe | Nutzen | Aufwand | Ziel |
|---|---|---|---|---|---|
| LES-001 | P0 | Sichere Anfahrt zwischen aufeinanderfolgenden Operationen | sehr hoch | M | 0.8.0-alpha |
| LES-003 | P0 | Innen-Schruppen Parallel-Z fachlich verifizieren und reparieren | sehr hoch | L | 0.8.0-alpha |
| LES-005 | P0 | Innen-Schlichtanfahrt und Rueckzug fuer weitere Konturformen absichern | sehr hoch | M-L | 0.8.0-alpha |
| LES-006 | P1 | Rueckzugsstrategie und Achsreihenfolge je Bearbeitungsart festlegen | hoch | M | 0.8.0 |
| LES-010 | P1 | Lokale DIN-Freistichgeometrie am markierten Segment erzeugen | hoch | L | 0.8.0 |
| LES-011 | P1 | Freistich in Vorschau, Subroutine und Schlichtweg identisch darstellen | hoch | M-L | 0.8.0 |
| LES-012 | P1 | Konturprimitive bis zur finalen G1/G2/G3-Ausgabe erhalten | hoch | L | 0.8.0 |
| LES-013 | P1 | G96/G97-Bedienfelder pro Operation und sichere CSS-Umschaltung | mittel-hoch | M | 0.8.0 |
| LES-015 | P1 | Weitere Innenkonturformen als Regression und Realtest absichern | hoch | M | 0.8.0 |
| LES-016 | P1 | Verbleibende UI-Sichtbarkeitsregeln testen | mittel | S-M | 0.8.0 |
| LES-019 | P1 | Verifizierte DIN-76-Presets fuer M2, M2.5 und M3.5 ergaenzen | mittel | S-M | 0.8.0 |
| LES-030 | P1 | Neue Generatorfunktionen systematisch in LinuxCNC simulieren | hoch | M-L | 0.8.0 |
| LES-018 | P2 | G70-Wiederverwendung fuer separaten Schlichtstep pruefen | mittel | M-L | 0.9.0 |
| LES-020 | P2 | Handler in kleinen Paketen weiter verkleinern | mittel | M je Paket | 0.9.0 |
| LES-022 | P2 | Zentralen Bewegungs- und Modalzustand einfuehren | langfristig hoch | XL | 0.9.0 |
| LES-023 | P2 | Nummer nur bei Export erzeugen statt dauerhaft speichern (Rest) | gering-mittel | S-M | 0.9.0 |
| LES-024 | P2 | Restliche UI-Modularisierung und Controllergrenzen abschliessen | mittel | L | 0.9.0 |
| LES-027 | P2 | Start- und Reaktionszeit im Embedded-Betrieb messen | mittel | S | 0.9.0 |
| LES-028 | P2 | Werkzeug- und G76-Parameter vor Ausgabe zentral normalisieren | mittel-hoch | M | 0.9.0 |
| LES-031 | P2 | Redundante Bewegungen und Modalbefehle systematisch bereinigen | mittel | M-L | 0.9.0 |
| LES-032 | P2 | Werkzeuggeometrie und Tooltable-Plausibilitaet vertiefen | hoch | L | 0.9.0 |
| LES-033 | P2 | Gewindevorschau aus realen Gewindeparametern ableiten | mittel | M-L | 0.9.0 |
| LES-034 | P2 | Preview-Pipeline fachlich in Werkstueck, Werkzeugweg und Hilfsgeometrie trennen | mittel | L | 0.9.0 |
| LES-035 | P2 | Embedded- und Standalone-Verhalten weiter angleichen | mittel | M | 0.9.0 |
| LES-036 | P1 | Kantenform "Radius" beim Planen umsetzen | mittel | M | 0.9.0 |

## P0 - Sicherheits- und Generatorblocker

### LES-001 Sichere Anfahrt zwischen Operationen

Aktueller Fehler: `emit_approach()` gibt bei gesetztem `_is_at_safe` einen
direkten diagonalen Zielmove aus. Der Status sagt nur, dass die vorherige
Operation an einer sicheren Position endete; er beweist nicht, dass der neue
Zielpunkt von dort direkt kollisionsfrei erreichbar ist.

- [ ] direkten Zielmove nicht allein aus dem Boolean `_is_at_safe` ableiten
- [ ] sichere Achsreihenfolge anhand Start-, Ziel-, Rohteil- und Futterzone waehlen
- [ ] gleiches Werkzeug ohne dazwischenliegenden Werkzeugwechsel testen
- [ ] Aussen-Schruppen -> Schlichten und Innen-Schruppen -> Schlichten testen
- [ ] Bohren und Gewinde als Z-vor-X-Sonderfaelle pruefen
- [ ] Warnung und tatsaechlicher Fahrweg duerfen sich nicht widersprechen
- [ ] Regressionen fuer Rohteil- und Chuck-No-Go-Faelle ergaenzen

### LES-003 Innen-Schruppen Parallel-Z verifizieren

Die Intervall-Ueberlappung in `rough_turn_parallel_x()` ist behoben.
Realtest-Frage 9 beantwortet (Zustellrichtung klein->gross bestaetigt
korrekt: "die Bohrung ist das was an Material abgetragen ist und frei ist,
der Rest zum groesseren Durchmesser muss ja erst abgespant werden").

Real bestaetigt und behoben (Nutzer-Testprogramm, Kommentar im generierten
Code: "Fallback-Grund: automatische Entscheidung -> Move-based"): Innen-
Abspanen nutzte bei vielen realen Innenkonturen NICHT den `G71`-Zyklus (wie
Aussendrehen), sondern die grobe bewegungsbasierte Ersatzloesung - sichtbar
an ungleichmaessigen, teils winzigen Zustellungen. Root Cause:
`is_monotonic_z_decreasing()` (`gcode_utils.py`) akzeptierte nur FALLENDE
Z-Werte fuer die G71-Eignungspruefung (`parallel_z`-Strategie in
`gcode_roughing.py`) - anders als bei X (`is_monotonic_x()` prueft BEIDE
Richtungen) gab es keine "Z steigend"-Variante. Innenkonturen werden aber
haeufig vom tiefsten Punkt zur Bohrungsoeffnung definiert (Z steigt
monoton) - eine geometrisch einwandfreie, aber bisher als "nicht
zyklustauglich" abgelehnte Konturrichtung. Neue symmetrische Pruefung
`is_monotonic_z()` (faellt ODER steigt, analog zu `is_monotonic_x()`)
ergaenzt; mit dem realen Testprogramm des Nutzers verifiziert (`ausdrehen`-
Kontur erzeugt jetzt einen sauberen `G71`-Aufruf statt 10 ungleichmaessiger
Move-based-Passes). Die `G71`-Startkoordinate (`X{stock_x} Z{safe_z}`)
brauchte keine Anpassung - sie referenziert bereits (wie beim laengst
funktionierenden Aussendrehen) die Rohteil-/Sicherheitsgrenze, nicht den
exakten ersten Konturpunkt, und bleibt bei beiden Konturrichtungen korrekt.

- [ ] vorhandenen Bohrungsdurchmesser als Materialgrenze verwenden
- [ ] `XRI` nur als sichere Einfahr-/Rueckzugsebene verwenden, nicht als Schnittbahn
- [ ] Schlichtaufmass X/Z fuer Innenkonturen korrekt ausrichten
- [ ] G71/G72-Vorzeichen und Konturstart fuer Innenbearbeitung pruefen
- [ ] Backplot und Trockenlauf mit einem konkreten Referenzteil dokumentieren (P0 - vor Praxiseinsatz zwingend)
- [ ] `examples.py` fehlt bisher ein Referenzbeispiel mit Innen-Abspanen
  (`side=inside`) - deshalb ist der `G71`-vs-Move-based-Fallback fuer
  Innenkonturen nicht durch den regulaeren `regenerate_all_ngc.py`-Diff-
  Workflow abgedeckt; ein Beispiel ergaenzen, sobald ein passendes,
  verifiziertes Referenzteil feststeht

### LES-005 Innen-Schlichtanfahrt und Rueckzug

Ein Einfahrweg fuer aktive Schneidenradiuskorrektur existiert bereits. Die
Funktion gilt erst nach Pruefung weiterer Innenkonturen als abgeschlossen.

- [ ] zuerst auf nachweislich freien Innendurchmesser fahren
- [ ] axial auf Konturstart fahren, bevor der Schnittdurchmesser angefahren wird
- [ ] Schneidenradiuskorrektur nur auf ausreichend langem Einfahrweg aktivieren
- [ ] Konturstart vorne und hinten getrennt testen
- [ ] nach dem Schnitt zuerst radial und danach axial freifahren
- [ ] Innenstufe, Innenkonus, Innenradius und Innenfreistich testen

## P1 - Fachliche Vollstaendigkeit fuer 0.8.0

### LES-006 Rueckzugsstrategie je Bearbeitungsart

Den Inventor-LinuxCNC-Post als Referenz auswerten und fuer jede Operation
explizit festlegen:

- [ ] nur X
- [ ] nur Z
- [ ] X dann Z
- [ ] Z dann X
- [ ] X/Z gleichzeitig
- [ ] Matrix fuer Planen, Abspanen innen/aussen, Schlichten, Gewinde,
  Bohren, Einstich/Abstich, Keilnut, Werkzeugwechsel und Parken dokumentieren
- [ ] Strategie in Generator und Tests abbilden

### LES-010 Lokale DIN-Freistichgeometrie

Freistiche werden derzeit nur erzeugt, wenn das Feature am ersten oder letzten
Segment der gesamten Kontur liegt.

- [ ] Segment-zu-Primitive-Zuordnung einfuehren
- [ ] Freistich relativ zum markierten Segment erzeugen
- [ ] Nachbarsegmente und lokale Bearbeitungsrichtung auswerten
- [ ] Freistich mitten in einer laengeren Wellenkontur unterstuetzen
- [ ] Innen- und Aussenfreistich getrennt behandeln
- [ ] DIN-76-Geometrie gegen verifizierte Referenz pruefen

### LES-011 Einheitliche Freistichdarstellung

- [ ] Fertigkontur, Schruppkontur und Feature-Teilkontur aus derselben Geometrie ableiten
- [ ] Aussen-/Innenfreistich in der Seitenvorschau darstellen
- [ ] Gewindeanfang und Gewindeende unterscheiden
- [ ] Vorschau, Kontur-Subroutine und ausgeschriebenen Schlichtweg vergleichen
- [ ] Save/Load-Roundtrip der Segment-Features testen

### LES-012 Konturprimitive erhalten

Der explizite Schlichtweg kann Radien bereits als G2/G3 ausgeben. Verbleibende
move-based Pfade linearisieren Geometrie teilweise noch.

- [ ] Linien und Boegen bis zur Ausgabe als Primitive fuehren
- [ ] Radien nicht in reine G1-Punktlisten umwandeln
- [ ] G18-Boegen mit korrektem G2/G3 und I/K ausgeben
- [ ] Arc-Intersections im Move-based Roughing vertiefen
- [ ] Vorschau und Generator auf dieselbe Primitive-Quelle umstellen

### LES-013 G96/G97 pro Operation

Real bestaetigter Architekturfehler (Nutzer-Feedback): G96/G97 war eine
globale Programmkopf-Einstellung, obwohl die Wahl fachlich pro Operation
getroffen werden muss (z. B. Aussendrehen mit CSS, aber ein danach folgendes
Bohren zwingend mit Festdrehzahl). Zusaetzlich verwendete `G96` unter `S`
bisher denselben Zahlenwert wie die Drehzahl (`spindle`) - physikalisch
falsch, da G96 unter `S` die Schnittgeschwindigkeit Vc (m/min) erwartet,
nicht U/min.

Umgesetzt:
- [x] Combo G97/G96 in Planen, Abspanen, Einstich/Abstich und Gewinde (neue
  Felder `<prefix>_spindle_mode`/`<prefix>_cutting_speed`, dynamisch ueber
  `ui_advanced.py` ergaenzt, analog zu bereits bestehenden Mustern wie
  `parting_undercut_mode`). Bohren bewusst ausgenommen (Nutzerentscheidung:
  Werkzeugdurchmesser aendert sich beim Bohren nicht, CSS ist dort ohne
  fachlichen Nutzen)
- [x] Schnittgeschwindigkeit (Vc, m/min) und Drehzahl (U/min) werden
  kontextabhaengig ein-/ausgeblendet (`update_spindle_mode_visibility()`)
- [x] `G96 D<max_rpm> S<Vc>` statt der bisherigen (falschen) Wiederverwendung
  der Drehzahl; ohne gueltige Vc faellt der Generator sicher auf `G97` mit
  Warnhinweis zurueck statt eine falsche Zahl als Vc zu senden
- [x] Save/Load: `spindle_mode`/`cutting_speed` sind normale `op.params`-
  Schluessel und werden ueber den bestehenden generischen Persistenzpfad
  automatisch mitgespeichert/geladen; alte Programme ohne diese Schluessel
  fallen unveraendert auf Festdrehzahl/G97 zurueck (kein Sonderfall noetig)
- [x] Sichtbarkeitsregeln mit echtem PyQt5 getestet
  (`tests/test_per_operation_spindle_mode_ui.py`)
- [x] globale `program_spindle_mode`-Combo entfernt; `program_spindle_max_rpm`
  bleibt als programmweite CSS-Sicherheitsobergrenze erhalten und ist jetzt
  immer sichtbar (keine sinnvolle Bedingung mehr ohne globale Modus-Combo)

Noch offen (bewusst nicht ungeprueft umgesetzt - siehe Analyse im Changelog):

- [ ] bei CSS sicher mit G97 anfahren und G96 erst an der Bearbeitungsposition
  aktivieren: erfordert eine physikalisch verifizierte Vc->Drehzahl-Umrechnung
  fuer die sichere Anfahr-Drehzahl (welcher Durchmesser gilt waehrend der
  Anfahrt?), dafuer gibt es noch keine etablierte Konvention im Projekt -
  keine Zahl raten, sondern gemeinsam entscheiden

### LES-015 Innenkontur-Testmatrix

- [ ] zylindrische Innenkontur
- [ ] Innenstufe
- [ ] Innenkonus
- [ ] Innenradius
- [ ] Innenkontur mit Freistich
- [ ] Schruppen mit anschliessendem Schlichten
- [ ] Werkzeugradiuskorrektur, Konturseite und Konturstart je Fall pruefen
- [ ] Realtest-Frage 11 abschliessen

### LES-016 UI-Sichtbarkeitsregressionen

Bereits abgedeckt: Planen, Bohren, Subspindel, Rohteilform, Rueckzugsmodus,
Abspanen-Schruppen/Schlichten/Schruppen+Schlichten (inkl. der bisher
ungetesteten "Freistich separat"-Teilregel), Einstich/Abstich (beide Zweige:
Werkzeugbreite-Checkbox und Abstich- vs. Einstich-Modus) und das einzige
bestehende globale G96/G97-Feld (`program_spindle_mode` blendet
"CSS Max-RPM" jetzt korrekt nur bei G96/CSS ein - Funktion neu ergaenzt,
da bisher keine Sichtbarkeitsregel dafuer existierte, siehe
`update_spindle_mode_visibility()` in `ui_visibility.py`).

Nach Audit (siehe Recherche zu dieser Aufgabe) bestehen fuer die folgenden
Punkte AKTUELL KEINE Sichtbarkeitsregeln im Code - hier fehlt nicht ein Test,
sondern eine Produktentscheidung, welche Felder ueberhaupt bedingt ein-/
ausgeblendet werden sollen, bevor eine Regression sinnvoll ist:

- [ ] Kontur: keine bedingte Sichtbarkeit vorhanden (Kantengroesse nutzt nur
  `setEnabled`, keine Kontur-Sichtbarkeitsregel identifiziert)
- [ ] Gewinde: keine bedingte Sichtbarkeit vorhanden (z. B. koennte
  `thread_relief_norm` sinnvollerweise nur bei `thread_relief_mode == "suggest"`
  sichtbar sein - aktuell immer sichtbar; haengt am per-Operation-Signalpfad
  `_handle_param_change`, noch nicht auditiert)
- [ ] Innen/Aussen: `side`/`lage`/`orientation` werden nirgends zum Ein-/
  Ausblenden anderer Felder verwendet (nur als G-Code-Parameter bzw. fuer die
  Einstich-Diagrammgrafik) - siehe auch LES-013 fuer die groessere,
  zusammenhaengende Aufgabe (G96/G97 pro Operation auf allen Reitern)

### LES-019 Fehlende DIN-76-Presets

- [ ] verifizierte Normwerte fuer M2, M2.5 und M3.5 beschaffen
- [ ] Aussen- und Innenvarianten ergaenzen
- [ ] Datenvalidierung und Preset-Tests erweitern
- [ ] keine Werte schaetzen

### LES-030 LinuxCNC-Simulationsmatrix

- [ ] alle Referenzprogramme nach Generatoraenderungen regenerieren
- [ ] Planen, Bohren, Gewinde, Einstich, Abspanen innen/aussen und Konturen pruefen
- [ ] Parserfehler, Backplot, Werkzeugwechsel und Parkbewegungen dokumentieren
- [ ] relevante Faelle als reale Trockenlaeufe bestaetigen
- [ ] Maschinenprofile und Futter-Sperrzonen mit Beispielen verifizieren

## P2 - Bedienung, Wartbarkeit und Architektur

### LES-018 G70 fuer separaten Schlichtstep

Der aktuelle explizite Schlichtweg ist fachlich korrekt. Zu pruefen ist nur die
Optimierung, einen bereits von einem frueheren G71/G72-Step verwendeten
Kontur-Sub spaeter per G70 wiederzuverwenden.

- [ ] stabile Zuordnung Kontur -> Subroutine -> vorheriger Schruppstep entwerfen
- [ ] reiner Schlichtstep darf niemals erneut schruppen
- [ ] Fallback auf expliziten Schlichtweg beibehalten

### LES-020 Handler weiter verkleinern

Jede Extraktion einzeln mit vollem Testlauf und echtem `uic.loadUi` pruefen.

- [ ] Programmkopf-Sammlung
- [ ] Kontursegment-Sammlung
- [ ] Gewinde-Preset-UI nach `ui_thread.py`
- [ ] Widget-Bootstrapping
- [ ] Tooltip-Erzwingung nach `ui_tooltips.py`

### LES-022 Zentraler Bewegungs- und Modalzustand

- [ ] aktuelle X/Z-Position bei jeder Move-Emission mitfuehren
- [ ] G90/G91, G94/G95, G96/G97, G18 und G40/G41/G42 verwalten
- [ ] M3/M4/M5, M7/M8/M9 und Werkstuecknullpunkt verwalten
- [ ] sichere Pfadentscheidungen auf reale aktuelle Position stuetzen
- [ ] robuste explizite Ausgabe fuer manuell bearbeitbaren G-Code erhalten

### LES-023 Step-Kommentare normalisieren

Erledigt: `_insert_loaded_operation()` und `_handle_add_operation()` frischten
eine bereits nummeriert aussehende, aber veraltete `comment`-Vorsilbe (z. B.
"5. Innenabspanen ..." aus einer per "Step speichern" gesicherten Datei, die
spaeter an anderer Position per "Step laden" wieder eingefuegt wird) bisher
NICHT auf - nur ein komplett leerer Kommentar wurde neu erzeugt. Beide Stellen
erzeugen die Nummer jetzt ueber `_looks_like_generated_step_comment()` neu,
sobald der bestehende Kommentar wie eine maschinell nummerierte Beschreibung
aussieht; ein bewusst individueller Kommentar ohne Nummern-Vorsilbe bleibt
weiterhin unangetastet (siehe `tests/test_auto_comment_on_creation.py`).
`renumber_operations()` (Verschieben/Loeschen) aktualisierte alle Kommentare
bereits zuvor unconditional.

Weiterhin offen (groessere Architekturfrage, nicht nur ein Bugfix):

- [ ] laufende Nummer nur beim Gesamtprogrammexport erzeugen, nicht dauerhaft in `params["comment"]` speichern
- [ ] Konturen bewusst mitzaehlen oder als nicht ausfuehrbare Geometrie markieren

### LES-024 Restliche UI-Modularisierung

Erledigt: Shell sowie Program, Face, Contour, Parting, Thread, Groove, Drill und
Keyway als Teil-UIs.

- [ ] Vorschau/Schnittansicht in eigene UI-Struktur auslagern
- [ ] Step-Liste und Programmverwaltung auslagern
- [ ] je Modul Controller, Tooltips, Sprach-IDs und Validierung zuordnen
- [ ] direkte Widgetzugriffe zwischen Modulen durch definierte Schnittstellen ersetzen
- [ ] Embedded- und Standalone-Laden testen

### LES-027 Performance

- [ ] Startzeit bis sichtbares und bedienbares Panel messen
- [ ] Embedded und Standalone vergleichen
- [ ] Reiterwechsel, Stepwechsel und Preview-Refresh messen
- [ ] Realtest-Frage 7 abschliessen

### LES-028 Eingaben zentral normalisieren

- [ ] Werkzeugwechsel nur aus normalisiertem Werkzeugdatensatz erzeugen
- [ ] G76-Parameter vor Ausgabe vollstaendig normalisieren und validieren
- [ ] bestaetigtes G7-Masssystem nicht erneut als offenen Fachfehler behandeln
- [ ] Preset- und manuelle Werte nachvollziehbar vergleichen

### LES-031 Redundante Ausgabe

- [ ] identische oder Null-G0-Bewegungen ueber alle Operationen pruefen
- [ ] modale Befehle nur bei sinnvoller Zustandsaenderung ausgeben
- [ ] Robustheit bei manueller Programmbearbeitung gegen minimale Ausgabe abwaegen

### LES-032 Werkzeuggeometrie

- [ ] Nasenradius, Schneidenlage, Schneidenlaenge und Werkzeugbreite auswerten
- [ ] Innen-/Aussenwerkzeuge plausibilisieren
- [ ] Tooltable-Daten fuer Kollisions- und Erreichbarkeitspruefungen nutzen
- [ ] Werkzeugvorschau und Generator auf denselben Datensatz stuetzen

### LES-033 Gewindevorschau

- [ ] symbolische Vorschau durch Geometrie aus Steigung, Tiefe, Start und Ende ersetzen
- [ ] Innen/Aussen und Rechts/Links getrennt pruefen
- [ ] Preset, Vorschau und G76-Ausgabe nachvollziehbar abbilden

### LES-034 Preview-Pipeline

- [ ] Werkstueck-Endkontur, Werkzeugweg und Hilfs-/Sicherheitsgeometrie trennen
- [ ] keine impliziten Verbindungen oder Fantasie-Hilfslinien zeichnen
- [ ] im Zweifel weniger statt geometrisch falsche Elemente anzeigen
- [ ] komplexe Endgeometrien in Seiten- und Schnittansicht vergleichen

### LES-035 Embedded/Standalone-Paritaet

- [ ] Widget-Binding, Tooltips, Dialoge und Dateipfade vergleichen
- [ ] keine globalen Host-Widgets im Embedded-Betrieb binden
- [ ] Real-Qt-Smoke-Test fuer beide Startarten pflegen

### LES-036 Kantenform "Radius" beim Planen

Real bestaetigter Bug (Realtest): Planen mit Kantenform "Fase" schlug im
Generator fehl, weil `edge_type` weiterhin ueber `int(float(...))` gelesen
wurde statt ueber `resolve_enum_index()` wie `mode`. Behoben. "Radius" ist in
der Combo waehlbar, im Generator (`gcode_face.py`) aber nach wie vor nicht
umgesetzt - waehlt der Nutzer "Radius", bricht die Erzeugung jetzt mit einer
klaren Fehlermeldung ab, statt (vor diesem Fix) still wie "Keine" behandelt
zu werden.

- [ ] Radius-Eckengeometrie fuer Planen umsetzen (Kontur-Reiter hat mit dem
  Fase/Radius-Freistich in `contour_logic.py` bereits eine funktionierende,
  aber allgemeine 3-Punkt-Fillet-Berechnung - fuer den Spezialfall Planen
  ggf. wiederverwendbar, sofern die Radius/Durchmesser-Umrechnung fuer den
  einfacheren 90°-Eckfall aus Anfahrpunkt/Endpunkt/Aussenkontur korrekt
  uebertragen wird)
- [ ] Realtest nach Umsetzung: Planen mit Radius am echten Panel pruefen

## Offene externe Antworten und Blocker

Noch unbeantwortet in der Realtest-Datei:

- Frage 7: Startzeit und Reaktionszeit -> LES-027
- Frage 9: Materialmodell Innen-Schruppen -> LES-003
- Frage 11: weitere Innenkonturformen -> LES-005/LES-015
- Frage 13: doppelte Operationen -> LES-026

Norm-/Systemabhaengige Blocker:

- DIN-76-Werte fuer M2, M2.5 und M3.5 -> LES-019
- lokale Freistichgeometrie braucht verifizierte DIN-Referenz -> LES-010
- Innen-Schruppen braucht LinuxCNC-Backplot und Trockenlauf -> LES-003
- Generatoraenderungen brauchen LinuxCNC-Simulation -> LES-030

## Verbindlicher Abschluss jeder Generatoraenderung

1. fokussierte Regressionen
2. kompletter `pytest -q`-Lauf
3. `python3 regenerate_all_ngc.py`
4. Diff der Referenzprogramme fachlich pruefen
5. echter PyQt5-Test bei UI-Aenderungen
6. LinuxCNC-Parser/Backplot bei geaenderten Fahrwegen
7. `TODO.md`, `ROADMAP.md`, `README.md`, `DEV.md` und `CHANGELOG.md` synchron halten

## Spaetere Erweiterungen nach stabiler 1.0-Basis

- weitergehende Keilnut- und Verzahnungsfunktionen
- weitere Maschinen-, Futter- und Werkzeugprofile
- automatisierte LinuxCNC-Simulationslaeufe
- zusaetzliche Abspanstrategien
