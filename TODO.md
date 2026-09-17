# TODO LatheEasyStep

Stand: 2026-09-17

Diese Datei enthaelt ausschliesslich offene Aufgaben. Abgeschlossene Arbeiten,
Befunde und historische Teststaende stehen im [CHANGELOG.md](CHANGELOG.md) und
in den Berichten unter `doc/`. Release-Ziele stehen in [ROADMAP.md](ROADMAP.md).

## Verifizierte Basis

- Branch `dev` ist der vollstaendige Entwicklungsstand (Quelltext, Tests,
  Entwicklungsdokumentation). `main` enthaelt seit dem 17.09.2026 nur noch
  kompakte Release-Commits nach `RELEASE_POLICY.md`
  (`release_manifest.txt` definiert die veroeffentlichten Pfade); die
  Historie von `main` sowie die Tags `v0.7.0`/`v0.8.0` wurden dafuer einmalig
  neu aufgebaut (siehe README.md-Hinweis fuer bestehende Klone).
- 898 Stub-Qt-Tests und 108 Tests mit echtem PyQt5, keine Skips.
- Zwoelf Referenzprogramme bestehen statische NGC-Pruefung und den nativen
  LinuxCNC-Interpreter (`rs274`); zusaetzlich bestehen 43 Matrixprogramme.
- Alle zwoelf Referenzen wurden in der QtDragon-SIM bis `M30` ausgefuehrt.
- Der Generator ist von Qt getrennt. Reiter, Step-Verwaltung und Vorschau
  liegen in eigenen UI-/Fachmodulen.

## Priorisierter Arbeitsindex

| ID | Prio | Aufgabe | Aufwand | Ziel |
|---|---|---|---|---|
| Release-Prozess | P1 | echten Release-Pfad testen, Manifest-Vollstaendigkeit absichern | S | vor 0.9.0 |
| LES-022 | P2 | Bewegungs- und Modalzustand vollstaendig fuehren | L | 0.9.0 |
| LES-051 | P1 | Panel-Grundgeruest und Darstellungsadapter weiter entkoppeln | XL | 0.9.0 |
| LES-052 | P1 | Panel-Architektur, Zustandsmodell und Wiederherstellung planen/umsetzen | XL | 0.9.0 |
| LES-044 | P2 | verbleibende Vorschau-Geometrie und Ausnahmegrenzen entkoppeln | L-XL | 0.9.0 |
| LES-032 | P2 | Werkzeuggeometrie fuer Plausibilitaet und Kollision erweitern | L | 0.9.0 |
| LES-043 | P2 | Gegenspindelfunktion als separates Projekt spezifizieren | XL | separat |
| LES-030 | extern | weitere reale Maschinenprofile verifizieren | extern | offen |

## Release-Prozess

`RELEASE_POLICY.md` und `scripts/create_release.py` (mit `release_manifest.txt`)
wurden am 17.09.2026 eingefuehrt und bislang nur mit `--check` gegengeprueft
(reine Validierung, kein Schreibvorgang). Vor 0.9.0 noch offen:

- [ ] den tatsaechlich schreibenden Release-Pfad einmal vollstaendig
  durchspielen: `scripts/create_release.py` ohne `--check` fuer einen
  Wegwerf-/Test-Release ausfuehren, den erzeugten `main`-Commit und den
  Manifestvergleich pruefen, danach lokal zuruecksetzen (`git branch -f
  main <vorheriger main-Commit>`, temporaeren Worktree/Tag entfernen).
  Bisher wurde nur der lesende `--check`-Pfad unter Windows und Debian
  getestet.
- [ ] vor jedem Release explizit pruefen, ob seit dem letzten Release neue
  Laufzeitabhaengigkeiten ausserhalb der `release_manifest.txt`-Pfade
  hinzugekommen sind. Das Skript erkennt fehlende/veraenderte Manifest-
  Eintraege, aber nicht, dass ein neuer Laufzeitpfad ueberhaupt ins Manifest
  gehoert.
- [ ] die vorhandenen Agenten-Instruktionsdateien (`CLAUDE.md` u. Ae.) um
  einen kurzen Verweis ergaenzen: fuer Release-Arbeiten ist
  `RELEASE_POLICY.md` verbindlich. Keine Kopie der Regeln, sonst laufen
  beide Texte auseinander.

## LES-022 Bewegungs- und Modalzustand

`MotionState` und `SpindleState` sind bereits eingefuehrt. Offen bleiben:

- [ ] weitere relevante modale G-/M-Codes in einem zentralen, typisierten
  Zustand fuehren, statt sie ueber verstreute Settings-Schluessel abzuleiten.
- [ ] Bewegungen auch waehrend der Schnittpfade granular nachfuehren; die
  aktuelle Invalidierung nach Roughing bleibt nur eine Zwischenloesung.
- [ ] fuer die neuen Zustandsuebergaenge gezielte Regressionen ergaenzen und
  sicherstellen, dass daraus keine unnoetigen Eilgaenge oder Modalwechsel
  entstehen.

## LES-051 Panel-Grundgeruest, Ressourcen und Darstellungsadapter

Die bestehende Shell-/Fragment-Struktur ist die richtige Basis, aber noch
keine vollstaendige Trennung von Zustand, Fachlogik und optischer Darstellung.
Das Panel soll ueber ein stabiles Grundgeruest geladen werden, waehrend
Darstellungen und Ressourcen austauschbare Adapter bleiben.

Umgesetzt (Details im Changelog): Besitzgrenzen sind in
`doc/PANEL_ARCHITECTURE.md` dokumentiert; der Qt-freie `ToolVisualProvider`
loest Werkzeug-/Schneidplatten-Darstellungen aus einem Theme-Manifest auf
(diagnostizierter Fallback bei fehlenden/ungueltigen Ressourcen, Pfade nicht
in Fachobjekten verankert, per Test belegt dass ein Ressourcenwechsel weder
Operationen/Werkzeugdaten noch G-Code veraendert); Vorschau-Legende,
Status-/Warnungsbox, Haupt-Vorschau-Canvas, Vorderansicht-Ringe/-Fuellungen
und die uebrigen "Chrome"-Farben (Achsen, Gitterticks, Legenden-/Status-Box-
Rahmen, Keilnut-Overlay, Schnittlinie) sind vollstaendig als Qt-freie
Datenvertraege in `preview_geometry.py` ausgelagert. Offen bleiben
konfigurierbare Theme-Auswahl, Cache und Lebensdauer fuer `ToolVisualProvider`.

- [ ] den verbleibenden Handler-Kleber weiter reduzieren. Neue Fachlogik darf
  nicht in `lathe_easystep_handler.py` entstehen; UI-Fragmente sollen nur
  definieren, welche Views geladen werden, nicht deren Zustand selbst besitzen.
- [ ] weitere austauschbare Panelbereiche identifizieren. Preview-Canvas,
  Legende und Status-/Warnungsdarstellung sind als Farb-/Stil-Datenvertraege
  bereits umgesetzt (siehe oben); offen bleiben optionale Bedienelemente
  (z. B. Schnittansicht-/Ansicht-zuruecksetzen-Buttons) als austauschbare
  Komponenten ueber einen eigenen Datenvertrag.
- [ ] Shell- und Fragment-Laden fuer Standalone und Embedded mit einem
  definierten Ladevertrag absichern: Reihenfolge, Widget-Registrierung,
  Signalbindung, Fehlerbehandlung und Wiederholung duerfen nicht vom
  konkreten Skin oder Ressourcenpaket abhaengen.

## LES-052 Panel-Architektur, Zustandsmodell und Wiederherstellung

Diese Aufgabe beschreibt den groesseren Ausbauplan auf Basis von LES-051. Vor
der Umsetzung muessen die Grenzen zwischen fachlichem Zustand, Controller,
Views, Ressourcen und Persistenz festgelegt werden. Kein einzelner Umbau darf
die G-Code-Erzeugung oder bestehende Maschinenlogik nur wegen einer optischen
Aenderung veraendern.

### 1. Architektur und Ladevertrag

Umgesetzt (Details im Changelog und `doc/PANEL_ARCHITECTURE.md`): alle sechs
Zustandskategorien (`ProgramState`, `OperationState`, `ToolTableState`,
`ViewState`, `DirtyState`, `RuntimeState`) sind jetzt fachlich getrennte,
Qt-freie Verantwortungen mit dokumentierten Besitzverhaeltnissen -
`ProgramState`/`OperationState` (`model.py`) und `MotionState`/`SpindleState`
(`motion_state.py`) waren es schon vorher; `DirtyState` (`dirty_state.py`),
`ToolTableState` (`tool_table_state.py`) und `RuntimeState`
(`runtime_state.py`) wurden neu gekapselt, jeweils als duenner `handler.
_<name>`-Adapter ueber den bestehenden Aufrufstellen.

- [ ] den Handler auf Bootstrap, Controller-Verbindungen und Kompatibilitaets-
  Wrapper begrenzen; neue Fachlogik gehoert in testbare Module unter
  `lathe_easystep/`.
- [ ] einen einheitlichen Ladevertrag fuer Grundgeruest, UI-Fragmente,
  Widget-Registrierung und Signalbindung fuer Standalone und Embedded
  definieren. Laden muss idempotent und in einer nachvollziehbaren Reihenfolge
  erfolgen.
- [ ] Views duerfen keinen eigenen fachlichen Programmzustand als zweite
  Wahrheit fuehren. Benutzeraktionen werden als definierte Events oder
  Controller-Aufrufe an das Modell gemeldet.

### 2. Darstellungs- und Ressourcenadapter

- [ ] einen neutralen `ToolVisualProvider` fuer Werkzeug- und
  Schneidplatten-Darstellungen einfuehren. Er liefert ein Render-/Bildmodell,
  nicht Operationen oder G-Code.
- [ ] SVG, PNG und spaetere Darstellungsformate ueber eine eigene
  Ressourcen-/Theme-Schicht aufloesen; Pfade, Cache und Fallbacks duerfen nicht
  in gespeicherten Programmdaten oder `Tool`-Fachobjekten landen.
- [ ] Preview-Canvas, Werkzeugbild, Legende, Status-/Warnungsbox und optionale
  UI-Bereiche ueber stabile Datenvertraege austauschbar machen.
- [ ] nachweisen, dass alternative oder fehlende Grafiken weder
  Operationsdaten, Werkzeugdaten, Preview-Geometrie, G-Code noch Dirty-/
  Save-State veraendern.

### 3. Atomare Zustandsaenderungen und Fehlergrenzen

- [ ] Aenderungen nach dem Ablauf Eingabe -> Normalisierung -> Validierung ->
  Modelluebernahme -> Dirty-State -> Preview/Warnungen ordnen.
- [ ] bei Validierungs- oder Darstellungsfehlern den letzten gueltigen
  Modellzustand behalten; keine teilweise aktualisierten Widget-Zustaende als
  neue fachliche Wahrheit uebernehmen.
- [ ] breite `except Exception`-Fallbacks in den betroffenen UI-/Preview-
  Modulen durch definierte Fehlerklassen oder engere Fehlergrenzen ersetzen,
  ohne erwartete optionale Ressourcenfehler zu verschlucken.
- [ ] Fehlerdiagnosen zentral sammeln und fuer Log, UI-Warnung und Tests
  strukturiert nutzbar machen.
- [ ] Fehlerklassen vereinheitlichen: `INFO`, `WARNING`, `BLOCKING_ERROR` und
  `INTERNAL_ERROR`; insbesondere muss klar sein, wann kein G-Code entstehen
  darf.

### 4. Bedienbarkeit und Wiederherstellung

- [ ] Undo/Redo auf Modell- oder Command-Ebene entwerfen; Widget-Zustaende
  duerfen nicht die Undo-Historie bilden.
- [ ] Undo/Redo fuer Parameter-, Segment-, Step-, Werkzeug- und Preset-
  Aenderungen mit klarer Dirty-State-Behandlung testen.
- [ ] Autosave und Absturzwiederherstellung als getrennte, atomare
  Wiederherstellungsdatei vorsehen. Originaldateien duerfen niemals ungefragt
  ueberschrieben werden.
- [ ] Wiederherstellung, Versionskennung, unvollstaendige Autosaves und die
  Entscheidung des Anwenders im UI nachvollziehbar behandeln.

### 5. Werkzeugdaten und technische Pruefung

- [ ] die Werkzeugtabelle als eigene Domaene kapseln: Parser, normalisierte
  Werkzeuge, Parse-Warnungen, unbekannte Felder und optionales Zurueckschreiben.
- [ ] Werkzeugdaten, Werkzeuggeometrie und Werkzeugdarstellung getrennt
  halten; dies bildet die Grundlage fuer die offenen LES-032-Pruefungen.
- [ ] beim Laden oder Erzeugen gespeicherte erwartete Werkzeugmerkmale gegen
  die aktuelle Werkzeugtabelle pruefen und erkennbare Abweichungen melden.
- [ ] einen technischen Pruefbericht pro Programm vorsehen: Werkzeuge,
  Grenzen, Futter-Sperrzone, XRI/XRA, Vorschub/Drehzahl, Warnungen und
  verwendete G-Code-Strategien.

### Abnahme fuer LES-052

- [ ] gleicher Programmzustand und identischer G-Code bei mindestens zwei
  Darstellungs-/Ressourcensaetzen.
- [ ] fehlende optionale Ressource fuehrt zu sichtbarer Diagnose, aber nicht
  zu geaendertem G-Code oder verlorenen Daten.
- [ ] Save/Load-, Undo/Redo- und Autosave-Roundtrips erhalten alle fachlichen
  Daten und den korrekten Dirty-State.
- [ ] Stub-Qt- und Real-Qt-Suite sowie Embedded-/Standalone-Start bestehen.
- [ ] bei Generator- oder Fahrwegaenderungen zusaetzlich Referenzen, statische
  NGC-Pruefung, `rs274` und erforderliche SIM-/Backplot-Nachweise aus den
  Abschlussregeln ausfuehren.

## LES-053 Programm-/Step-Dateiformat versionieren

Das Dateiformat wird vor 1.0 explizit versioniert. Migrationen gehoeren in
eine zentrale Persistenzschicht und duerfen nicht von UI- oder Generator-
Modulen erraten werden.

- [ ] `format_version` in Programm- und Step-Dateien einfuehren.
- [ ] Migrationen fuer alle unterstuetzten Altformate zentral definieren
  (zunaechst `v1 -> v2` und `v2 -> v3`).
- [ ] kein Format-Raten in Loadern, UI-Fragmenten oder Generatoren.
- [ ] Roundtrip-Tests fuer jede unterstuetzte Altversion ergaenzen.
- [ ] unbekannte neuere Versionen sauber ablehnen.
- [ ] Migrationen duerfen die Quelldatei nicht ungefragt ueberschreiben.

Ziel: 0.9.0, verpflichtendes 1.0.0-Gate.

## LES-054 Deterministische Programmerzeugung

Aus denselben normalisierten Programmdaten muss unabhaengig von Eingabeweg,
Sprache, Vorschau, Theme sowie Embedded-/Standalone-Betrieb derselbe fachlich
identische G-Code entstehen.

- [ ] deterministische Erzeugung als expliziten Vertrag dokumentieren.
- [ ] Eingabe -> Speichern -> Laden -> Erzeugen als Regression testen.
- [ ] Erzeugen -> Vorschau/Theme-/Sprachwechsel -> Erzeugen als Regression
  testen.
- [ ] Embedded und Standalone gegen dieselben normalisierten Daten pruefen.
- [ ] G-Code-Vergleiche auf fachlicher Ebene statt auf UI-Zustaenden aufbauen.

Ziel: 0.9.0, Gate fuer die 1.0.0-Abnahme.

## LES-055 Maschinenprofil-Identitaet und Kompatibilitaet

Ein gespeichertes Programm muss erkennen lassen, fuer welches Maschinenprofil
es erstellt wurde. Das Profil umfasst mindestens Achsgrenzen,
Werkzeugwechselpunkt, Futter-/Sperrzonen, X/Z-Konvention und
Drehzahlgrenzen.

- [ ] stabile Identitaet und Version fuer Maschinenprofile definieren.
- [ ] verwendetes Profil in Programm- oder Laufmetadaten speichern.
- [ ] Abweichung zwischen gespeichertem und aktuellem Profil erkennen und
  nachvollziehbar melden.
- [ ] Kompatibilitaetspruefung fuer sicherheitsrelevante Profilparameter
  spezifizieren; eine harte Sperre ist gesondert zu entscheiden.
- [ ] positive, inkompatible und fehlende Profilfaelle testen.

Ziel: 1.0.0.

## LES-044 Vorschau und Darstellung

Die Qt-freie Geometrieplanung ist fuer Navigation, Raster, Pfade, Sperrzonen
und Vorderansicht weitgehend umgesetzt. Farb-/Stil-Datenvertraege fuer das
Preview-Widget sind vollstaendig ausgelagert (siehe LES-051); die breiten
`except Exception`-Fallbacks in `preview_widget.py`/`ui_preview.py` wurden
einzeln bewertet und, wo fachlich moeglich, auf erwartete Ausnahmetypen
begrenzt (36 von 40 Vorkommen, Details im Changelog). Offen bleiben:

- [ ] verbleibende fachliche Darstellungsberechnungen (Geometrie, nicht
  Farbe/Stil) aus `preview_widget.py`/`ui_preview.py` in Qt-freie
  Planfunktionen verschieben; Qt-Code soll nur Stil, Widget-Zustand und
  QPainter-Ausgabe enthalten.
- [ ] `except Exception`-Fallbacks ausserhalb von `preview_widget.py`/
  `ui_preview.py` (z. B. `ui_header.py`, `ui_params.py`) noch nicht
  durchsucht - falls dort ebenfalls relevant, nach demselben Muster bewerten.
- [ ] jeden weiteren Extraktionsschritt mit einem kleinen Stub-Test und einem
  Real-Qt-Start pruefen; bestehende Vorschau-Pakete nicht erneut als offene
  Aufgaben dokumentieren.

## LES-032 Werkzeuggeometrie

Werkzeugnummer, Radius, ISO-Code, Orientierung und Stechbreite werden bereits
aus dem normalisierten `Tool`-Datensatz verwendet. Die Q-basierte Innen-/
Aussenableitung ist bewusst verworfen; Details stehen im Changelog.

- [ ] eine belastbare Datenquelle fuer Schneidenlaenge und Haltergeometrie
  festlegen. Im aktuell verwendeten `Drehbank/tool.tbl` gibt es dafuer keine
  erkennbare Spalte oder Kommentarkonvention.
- [ ] erst danach die Werkzeughuellenpruefung fuer Dreh- und Bohrwerkzeuge
  erweitern; keine Geometrie aus geratenen Defaults ableiten.
- [ ] fuer jede neue Reichweiten-/Kollisionsregel einen positiven und einen
  negativen Test mit realistischen Tooltable-Daten ergaenzen.
- [ ] Aenderungen der Werkzeugmerkmale seit Programmerstellung erkennen;
  mindestens Werkzeugnummer, Radius und Orientierung vergleichen. Eine
  Diskrepanz muss nachvollziehbar gemeldet werden, ohne pauschal jede
  Abweichung als harte Sperre zu behandeln.

## LES-043 Gegenspindel

Die nicht implementierten Bedienelemente bleiben sichtbar, aber gesperrt.

- [ ] separate Spezifikation erstellen: Operationen, Spindelsynchronisation,
  S3-Grenzen, Koordinatensysteme und Kollisionsmodell.
- [ ] LinuxCNC-SIM- und Maschinenkonzept fuer diese Spezifikation festlegen,
  bevor irgendeine Generatorimplementierung in LatheEasyStep beginnt.

## LES-030 Externe Maschinenverifikation

- [ ] unterschiedliche reale Drehmaschinen mit Achsgrenzen,
  Werkzeugwechselpositionen und Futterbauformen verifizieren.
- [ ] Referenzprogramme als formale Schnittstelle dokumentieren: Quelldatei,
  normalisierte Operationen, G-Code-Eigenschaften, `rs274`-, SIM- und
  Backplot-Ergebnis sowie gegebenenfalls Maschinenlauf.

Dieser Punkt ist mit der vorhandenen einzelnen QtDragon-SIM nicht abschliessbar
und blockiert die 0.8.0-Softwarebasis nicht.

## Spaetere Funktionen

- Keilnut ohne verbotene Makrovariablen neu implementieren.
- weitergehende Verzahnungs- und Gegenspindelfunktionen.
- weitere Maschinen-, Futter- und Werkzeugprofile.
- automatisierte LinuxCNC-SIM-Laeufe als dauerhafte Testinfrastruktur.

## Abschlussregeln fuer Aenderungen

1. Regression, die den alten Fehler oder die neue Grenze konkret abdeckt.
2. Voller Lauf von `python3 run_tests.py`, ohne unbegruendete Skips.
3. Bei Generatoraenderungen Referenzen regenerieren und Diff pruefen.
4. Statische NGC-Pruefung sowie nativer `rs274`-Lauf.
5. Bei UI-Aenderungen echtes PyQt5 sowie Embedded/Standalone pruefen.
6. Bei Fahrweg-/Modal-Aenderungen LinuxCNC-Backplot und AUTO-Trockenlauf.
7. Dokumentation und aktuelle Testzahlen synchron halten.
