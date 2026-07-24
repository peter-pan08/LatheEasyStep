# TODO LatheEasyStep

Stand: 2026-07-24

Diese Datei enthaelt nur offene, konkret bearbeitbare Punkte. Erledigtes wird
in das `CHANGELOG.md` verschoben. Die Release-Ziele und Meilensteine stehen
in der [ROADMAP.md](ROADMAP.md).

Aufwand:

- `S`: wenige Stunden bis etwa ein Tag
- `M`: ein bis drei Entwicklungstage
- `L`: mehrere Tage mit Tests und Simulation
- `XL`: groessere Architekturarbeit in mehreren Etappen

Prioritaeten:

- `P0`: Sicherheit, falsche Fahrwege oder ungueltige Programmausgabe
- `P1`: hoher praktischer Nutzen und fachliche Vollstaendigkeit
- `P2`: Wartbarkeit, Bedienkomfort und langfristige Architektur

## Priorisierte Entwicklungsreihenfolge

Die nachfolgende Tabelle ist der Arbeitsindex. Die ausfuehrlichen technischen
Notizen und Checklisten bleiben in den anschliessenden Abschnitten erhalten.

| ID | Prioritaet | Aufgabe | Nutzen | Aufwand | Ziel-Meilenstein |
|---|---|---|---|---|---|
| LES-001 | P0 | Sichere Anfahrt zwischen aufeinanderfolgenden Operationen | sehr hoch | M | 0.8.0-alpha |
| LES-002 | P0 | Leere Schruppoperationen als Generatorfehler abbrechen | sehr hoch | S | 0.8.0-alpha |
| LES-003 | P0 | Innen-Schruppen Parallel-Z fachlich verifizieren und reparieren | sehr hoch | L | 0.8.0-alpha |
| LES-004 | P0 | ZRA/ZRI relativ/absolut im Sicherheits- und Abspan-Generator vereinheitlichen | sehr hoch | M | 0.8.0-alpha |
| LES-005 | P0 | Innen-Schlichtanfahrt, Schneidenradiuskorrektur und Rueckzug absichern | sehr hoch | L | 0.8.0 |
| LES-010 | P1 | DIN-Freistich relativ zum markierten Kontursegment erzeugen | hoch | L | 0.8.0 |
| LES-011 | P1 | Freistich in Vorschau, Subroutine und Schlichtweg identisch darstellen | hoch | M-L | 0.8.0 |
| LES-012 | P1 | Konturprimitive in allen relevanten move-based Pfaden bis zur G2/G3-Ausgabe erhalten | hoch | L | 0.8.0 |
| LES-013 | P1 | G96/G97-Bedienfelder pro Operation ergaenzen | mittel-hoch | M | 0.8.0 |
| LES-014 | P1 | G76-Masssystem mit M12x1.75 und M30x3.5 dokumentiert verifizieren | hoch | M | 0.8.0 |
| LES-015 | P1 | Weitere Innenkonturformen als Regression und LinuxCNC-Referenzfaelle absichern | hoch | M | 0.8.0 |
| LES-016 | P1 | Verbleibende UI-Sichtbarkeitsregeln testen | mittel | S-M | 0.8.0 |
| LES-020 | P2 | Handler in kleinen, einzeln getesteten Paketen weiter verkleinern | mittel | M je Paket | 0.9.0 |
| LES-021 | P2 | Strikte UI-/Sprachtrennung vervollstaendigen | mittel | M-L | 0.9.0 |
| LES-022 | P2 | Zentralen Bewegungs- und Modalzustand einfuehren | langfristig hoch | XL | 0.9.0 |
| LES-023 | P2 | Step-Kommentare und Exportnummerierung normalisieren | mittel | M | 0.9.0 |
| LES-024 | P2 | Monolithische UI erst nach funktionaler Stabilisierung modularisieren | langfristig mittel | XL | nach 0.9.0 |

## Verbindliche Arbeitsreihenfolge

1. Sicherheitsanfahrt und leere Schruppoperationen
2. Innen-Schruppen und ZRA/ZRI-Auslegung
3. Innen-Schlichtanfahrt und Rueckzug
4. lokale Freistichgeometrie
5. gemeinsame Geometrie fuer Vorschau und G-Code
6. G96/G97-UI, G76-Verifikation und weitere Regressionen
7. erst danach groessere Architekturumbauten


## Externe Verifikation / Nutzerantworten

Reale LinuxCNC-/QtVCP-Tests und offene Nutzerentscheidungen sind in
`doc/REALTEST_FRAGEN_2026-07-15.md` gesammelt, damit sie gezielt beantwortet
und danach hier abgeschlossen werden koennen.

## Blockiert auf verifizierte Fachdaten/Domainwissen

- Materialmodell / Schlichtaufmass-Richtung fuer Innenkonturen beim
  `G71`/`G72`-Zyklus (`strategy_code == "parallel_x"` in `gcode_roughing.py`):
  Vorzeichen ist fuer Aussenbearbeitung per Test bestaetigt, fuer
  Innenbearbeitung ungetestet. Braucht Backplot oder jemanden mit Kenntnis der
  G71/G72-Auslegung dieses Projekts, bevor hier etwas geaendert wird.
- Fehlende DIN-Freistich-Presets fuer `M2`, `M2.5`, `M3.5` ergaenzen. Braucht
  eine verifizierte DIN-76-Referenztabelle, keine Schaetzung.
- `safe_z` in `generate_abspanen_gcode()` (`gcode_roughing.py`) wird aus dem
  rohen `ZRA`/`ZRI`-Wert gebildet und ignoriert dabei das `*_absolute`-Flag.
  Bei relativem `ZRI`/`ZRA` (z. B. `0.0`, `absolute=False`) muesste der Wert
  vermutlich `ZA + ZRI` sein (siehe die bereits korrekt implementierte, analoge
  Logik in `gcode_safety._safe_axis_value()`, dort auch so kommentiert und fuer
  `get_safe_position()`/`emit_approach()` verwendet). Ein Versuch, beide
  Stellen zu vereinheitlichen, brach 21 bestehende Tests, die den rohen Wert
  als korrekt voraussetzen - ob das Testverhalten oder die aktuelle
  `generate_abspanen_gcode`-Logik der eigentliche Fehler ist, braucht Klaerung
  mit jemandem, der die ZRA/ZRI-Auslegung dieses Projekts kennt, bevor daran
  etwas geaendert wird (gleiche Vorsicht wie beim bereits dokumentierten
  G71/G72-Materialmodell-Punkt oben).
- DIN-Freistich-Features (`din_relief`) in Kontur-Segmenten erzeugen nur dann
  Geometrie, wenn ihr Segment das absolut erste/letzte Segment der GESAMTEN
  Kontur ist (`contour_logic.py`, `anchor_mode`-Pruefung mit `idx == 0`/
  `idx == len(segments) - 1`). Sitzt der Freistich mitten in einer laengeren
  Kontur (z. B. Gewinde-Freistich, gefolgt von weiterem Wellenprofil - der
  reale Testfall M30-Aussengewinde bei Z=-35 mit Profil bis Z=-60), bleibt die
  Geometrie leer. Eine Warnung dafuer existiert jetzt
  (`_check_din_relief_feature_position()`), die Geometrie selbst fehlt aber
  weiterhin. Korrekte Behebung braucht eine Segment-zu-Primitive-
  Indexzuordnung (Kantenbehandlungen wie Fase/Radius erzeugen mehrere
  Primitiven pro Segment) und sollte gegen eine reale DIN-76-
  Referenzgeometrie verifiziert werden, bevor daran etwas geaendert wird.
- `emit_approach()`s `_is_at_safe`-Kurzschluss (ein einzelner direkter Zielmove
  statt der sicheren Z-dann-X-Sequenz, sobald die vorherige Operation als "an
  der sicheren Position" markiert wurde) prueft nur, OB eine vorherige
  Operation dort endete, nicht ob der NEUE Zielpunkt (andere X-Position!) von
  dort sicher direkt erreichbar ist. Bei Test.lse's Innen-Schlichten (Schruppen
  und Schlichten nutzen dasselbe Werkzeug, kein Toolchange dazwischen) fuehrt
  das dazu, dass trotz korrekt gemeldetem `(WARN: ... liegt im Rohteil)`
  weiterhin ein einzelner diagonaler Move statt der sicheren Sequenz
  ausgegeben wird. Betrifft grundsaetzlich jede Operation, die denselben
  Sicherheits-Helfer nutzt - Aenderung braucht sorgfaeltige Pruefung des
  Blast-Radius, nicht nur einen Punkt-Fix fuer Abspanen.

## Offene Code-Aufgaben

- `lathe_easystep_handler.py` weiter verkleinern (aktuell 4965 Zeilen, vorher
  7501). Naechste Kandidaten mit substanzieller Eigenlogik statt reinem
  Delegieren: `_collect_program_header`, `_collect_contour_segments`,
  `_apply_thread_preset`/`_populate_thread_standard_options` (-> z. B. neues
  `ui_thread.py`), Widget-Bootstrapping (`_get_widget_by_name`,
  `_resolve_core_widgets_strict`, `_register_known_widgets`), Tooltip-
  Erzwingung (`_set_tooltip_deep`, `_fallback_tooltip_text` -> z. B. neues
  `ui_tooltips.py`). Jede Extraktion einzeln mit vollem Testlauf und echtem
  PyQt5 (`uic.loadUi`) gegenpruefen, nicht alles in einem Schritt.
- Diagonale Eilgangbewegungen aus noch im Material stehenden Positionen fuer
  Abspanen/Kontur/Gewinde-Zustellung pruefen (Einstich/Groove-Zyklus bereits
  geprueft und sicher, da X dort vor jeder Z-Bewegung bereits zurueckgezogen ist).
- Werkzeugradiuskorrektur, Konturseite, `G71`-Parameter und Konturstart fuer
  weitere Innenkonturformen verifizieren (Innenstufe, Innenkonus, Innenradius,
  Innenkontur mit Freistich) - bisher nur fuer die getesteten Grundfaelle
  (Innen-Abspanen, Innengewinde) abgesichert.
- Freistich/Hinterschnitt in der Vorschau geometrisch darstellen (bisher nicht
  implementiert); Vorschau muss Aussenfreistich, Innenfreistich sowie Lage am
  Gewindeanfang/-ende unterscheiden.
- Verbleibende UI-Refresh-Pfade auf ungewollte Dirty-Markierung pruefen
  (Move/Delete/Add und Sprachumschaltung sind bereits ausgenommen).
- Sichtbarkeitsregeln je Bearbeitungsart mit dedizierten Tests absichern.
  Planen, Bohren, Subspindel, Rohteilform und Rueckzugsmodus sind jetzt
  ebenfalls mit Regressionstests abgedeckt (`tests/test_ui_visibility_guards.py`);
  offen bleiben weiterhin Kontur, Abspanen, Gewinde,
  Innen-/Aussenbearbeitung, Schruppen/Schlichten, `G96`/`G97`.
- UI-Bedienelemente fuer Drehzahlmodus pro Step ergaenzen (Combo `G97`/`G96` +
  Feld fuer Schnittgeschwindigkeit/max. Drehzahl in Planen, Abspanen,
  Einstich/Abstich, Gewinde, Bohren). Der Generator unterstuetzt das bereits
  (`spindle_mode`/`spindle_max_rpm` pro Operation mit Fallback auf den
  Programmkopf) - es fehlt nur die UI-Verdrahtung. Braucht Sichtpruefung am
  echten Panel, da mehrere `QFormLayout`-Bloecke manuell erweitert werden
  muessen (siehe Zeilen-Kollisions-Bug in der Historie).
- Regressionstests fuer weitere Innen-Abspanen-Konturformen ergaenzen
  (zylindrische Innenkontur, Innenstufe, Innenkonus, Innenradius, Innenkontur
  mit Freistich, Innen-Schruppen mit anschliessendem Schlichten).
- Alle neuen Generatorfunktionen zusaetzlich in LinuxCNC-Simulation
  verifizieren, sobald ein System dafuer verfuegbar ist.

## Offene Architekturaufgaben fuer UI-Textsystem

- Strikte Trennung von UI und Sprache fertig umsetzen:
  kein sichtbarer Text darf final aus Python oder unveraendert aus der `.ui`
  kommen; stattdessen nur technische IDs/Schluessel, die ausschliesslich in
  `.lng`-Dateien aufgeloest werden.
- Verbleibende direkte UI-Textquellen in Python eliminieren
  (`QLabel(...)`, `setText(...)`, `setToolTip(...)`, `addItem(...)`,
  Tabellenkopftexte, Dialogtexte), soweit sie sichtbare Inhalte erzeugen.
- Bootstrap-/Hilfswidgets ohne sichtbaren Fallbacktext erzeugen:
  statt sprachlicher Platzhalter in Python muessen sie mit IDs/Keys starten und
  erst ueber das Sprachsystem sichtbaren Text erhalten.
- `.ui`-Datei weiter entkoppeln:
  sichtbare Defaulttexte dort nur noch als technische Schluessel/IDs oder leer;
  keine deutschsprachigen Ausgangstexte mehr als scheinbare Fallbacks.
- Sprachsystem ohne implizites Default-Deutsch vollstaendig durchziehen:
  fehlt ein Eintrag, muss sichtbar der Key/die ID erscheinen, nicht ein
  Python-/`.ui`-Fallback.

## Grundsatz

- Generatorlogik muss sich an realem LinuxCNC-Verhalten messen lassen, nicht
  nur an internen Modellannahmen.
- Innenbearbeitung braucht eigene Sicherheits- und Bewegungslogik und darf
  nicht als Aussenbearbeitung gespiegelt werden.
- Tooltip-Funktion gilt erst dann als erledigt, wenn sie im eingebetteten
  Panel praktisch funktioniert.
- Wo eine Codeaenderung ohne echtes LinuxCNC/QtVCP-System oder ohne
  verifizierte Normquelle nicht risikofrei verifiziert werden kann, wird nicht
  geraten - der offene Punkt bleibt sichtbar dokumentiert statt stillschweigend
  als erledigt markiert zu werden.

### Inventor-LinuxCNC-Post als Referenz auswerten

- [ ] Rückzugslogik mit expliziter Achsreihenfolge strukturieren:
  - X
  - Z
  - X dann Z
  - Z dann X
  - X/Z gleichzeitig

- [ ] Rückzugsstrategie pro Bearbeitungsart festlegen.

- [ ] G96/G97 pro Operation ausgeben (Generator unterstuetzt `spindle_mode`/
  `spindle_max_rpm` pro Operation bereits, siehe `append_tool_and_spindle()` -
  es fehlt nur die UI-Verdrahtung, siehe "Offene Code-Aufgaben" oben).

- [ ] CSS beim sicheren Anfahren gegebenenfalls zunächst als G97 ausgeben und erst an der Bearbeitungsposition aktivieren.

- [ ] Werkzeugwechsel nur anhand eines normalisierten Werkzeugdatensatzes erzeugen.

- [ ] Modalzustände zentral verwalten:
  - G90/G91
  - G94/G95
  - G96/G97
  - G18
  - G40/G41/G42
  - M3/M4/M5
  - M7/M8/M9
  - Werkstücknullpunkt

- [ ] Bögen bis zur finalen G-Code-Ausgabe als Bögen erhalten.

- [ ] G76-Parameter vor der Ausgabe vollständig normalisieren und validieren.

- [ ] Redundante Befehle und Nullbewegungen vermeiden.

### Innen-Schruppen mit Parallel-Z reparieren

- [ ] Materialbereich zwischen vorhandener Bohrung und Fertigkontur berechnen /
  [ ] Zustellung von kleinem zu groesserem Durchmesser: die Vorzeichen-/
  Richtungskorrektheit fuer Innenbearbeitung ist NICHT verifiziert - siehe
  den bereits bestehenden Punkt "Materialmodell / Schlichtaufmass-Richtung
  fuer Innenkonturen" oben. Nicht ohne Backplot/Fachwissen aendern.
- [ ] Leere Schruppoperationen als Generatorfehler behandeln und die Programmerzeugung abbrechen.

### Schlichtmodus korrekt auswerten

- [ ] Reiner Schlichtstep erzeugt nur den Schlichtlauf, zum Beispiel `G70`.
  Aktuell faellt `mode=finish` immer auf den expliziten G1-Konturweg zurueck
  (fachlich korrekt, aber ohne die G70-Zyklus-Optimierung). Ein G70, das einen
  von einem FRUEHEREN, separaten Schruppstep bereits allokierten Sub referenziert,
  waere effizienter, braucht aber eine verlaessliche Zuordnung "wurde dieser
  Sub bereits vor diesem Step per G71/G72 geschruppt".

### Konturprimitive im Move-based Generator erhalten

- [ ] Linien und Boegen bis zur finalen G-Code-Ausgabe als Primitive erhalten.
- [ ] Radien nicht in reine Punktlisten mit `G1` umwandeln.
- [ ] Fuer Boegen korrekt `G2` oder `G3` mit `I/K` ausgeben.
- [ ] Vorschau, Kontur-Subroutine und ausgeschriebener Schlichtweg muessen dieselbe Geometrie verwenden.

### Innen-Schlichtanfahrt und -Rueckzug korrigieren

- [ ] Innenbearbeitung zuerst auf einen nachweislich freien Durchmesser fahren.
- [ ] Fuer die axiale Einfahrt `XRI` beziehungsweise eine daraus abgeleitete freie Position verwenden.
- [ ] Schneidenradiuskorrektur nicht auf einem unkontrollierten Einfahrweg aktivieren.
- [ ] Korrekte Einfahrbewegung fuer Konturstart hinten und vorne getrennt behandeln.
- [ ] Nach dem Schnitt zuerst radial freifahren und danach axial zurueckziehen.

### Lokale Freistichgeometrie erzeugen

Siehe auch den Punkt "DIN-Freistich-Features (`din_relief`)..." unter
"Blockiert auf verifizierte Fachdaten/Domainwissen" oben - dort steht die
genaue Fundstelle (`contour_logic.py`) und warum eine Behebung Backplot-
Verifikation braucht. Eine Warnung bei nicht erzeugter Geometrie existiert
bereits (`_check_din_relief_feature_position()`).

- [ ] DIN-Freistich relativ zum markierten Kontursegment erzeugen.
- [ ] Nicht verlangen, dass der Freistich am Ende der gesamten Werkstueckkontur liegt.
- [ ] Nachbarsegmente und lokale Bearbeitungsrichtung zur Orientierung verwenden.
- [ ] Aussen- und Innenfreistich getrennt behandeln.
- [ ] Freistich in Vorschau, Subroutine und Schlichtweg identisch darstellen.

### G76-Masssystem verifizieren

- [ ] Klaeren, welche G76-Parameter unter aktivem `G7` radial und welche im Durchmesser angegeben werden.
- [ ] Insbesondere `I`, `J` und `K` fuer Innen- und Aussengewinde pruefen.
- [ ] M12x1.75 und M30x3.5 als isolierte LinuxCNC-Simulationsfaelle testen.
- [ ] Presetwert, Vorschaugeometrie und ausgegebener G76-Wert dokumentiert aufeinander abbilden.

### Bewegungs- und Modalbereinigung

- [ ] Doppelte identische G0-Saetze entfernen (Stichprobe an Test.lse zeigt
  aktuell keine exakten Duplikate mehr, aber keine systematische Pruefung
  ueber alle Operationstypen).
- [ ] Aktuelle X/Z-Position generatorseitig mitfuehren (grössere
  Architekturaenderung - jede Move-Emission muesste durch eine zentrale
  Stelle laufen, die die Position kennt; aktuell wird pro Funktion lokal
  gerechnet).
- [ ] Modale Befehle nur bei tatsaechlicher Zustandsaenderung ausgeben
  (`G97 S... M3` etc. werden aktuell pro Operation neu ausgegeben, auch wenn
  sich Spindeldrehzahl/-richtung nicht geaendert hat - bewusst so fuer
  Robustheit bei manueller Programmbearbeitung, aber nicht "minimal").

### Step-Kommentare normalisieren

- [ ] Laufende Nummer nur beim Gesamtprogrammexport erzeugen (Architekturwechsel:
  `comment` wuerde nur noch die Beschreibung ohne Nummer speichern, die Nummer
  kaeme ausschliesslich aus dem G-Code-Generator zur Exportzeit - waere robuster
  als die aktuelle "Nummer im Kommentar + bei jeder Umsortierung nachziehen"-
  Loesung, ist aber eine groessere, hier noch nicht umgesetzte Aenderung).
- [ ] Konturen entweder bewusst mitzaehlen oder als nicht ausfuehrbare Geometrieeintraege kennzeichnen.
- [ ] Kommentare aus aktuellen normalisierten Stepdaten erzeugen (Voraussetzung:
  siehe Gewinde-/Preset-Normalisierung oben - Warnung existiert, vollstaendige
  Normalisierung noch nicht).


## UI modularisieren

### Ziel
Die bisherige monolithische `lathe_easystep.ui` in logisch getrennte Teil-UI-Dateien aufteilen.

### Aufteilung

- [ ] `ui_program_header.ui`
  - Programmkopf
  - Rohteil
  - Sicherheitseinstellungen
  - Maschinenprofil
  - Werkzeugwechselposition
  - Spannfutter

- [ ] `ui_face.ui`
  - Planen

- [ ] `ui_contour.ui`
  - Konturerstellung

- [ ] `ui_roughing.ui`
  - Abspanen

- [ ] `ui_thread.ui`
  - Gewinde

- [ ] `ui_groove.ui`
  - Einstich / Abstich

- [ ] `ui_drill.ui`
  - Bohren

- [ ] `ui_keyway.ui`
  - Nutenstoßen

- [ ] `ui_preview.ui`
  - Vorschau
  - Schnittansicht

- [ ] `ui_steps.ui`
  - Step-Liste
  - Programmverwaltung

### Architektur

- [ ] Jede Teil-UI besitzt einen eigenen Controller.
- [ ] Jede Teil-UI besitzt eigene Tooltips.
- [ ] Jede Teil-UI besitzt eigene Sprach-IDs.
- [ ] Jede Teil-UI besitzt eigene Validierung.
- [ ] Keine Teil-UI greift direkt auf Widgets einer anderen Teil-UI zu.

### Laden

- [ ] Hauptfenster lädt nur die einzelnen Module.
- [ ] Module werden zentral registriert.
- [ ] Module kommunizieren ausschließlich über definierte Schnittstellen.

### Ziel

- kleinere `.ui`-Dateien
- schnellere Wartung
- geringere Merge-Konflikte
- einfacheres Refactoring
- bessere Testbarkeit
- bessere Erweiterbarkeit
