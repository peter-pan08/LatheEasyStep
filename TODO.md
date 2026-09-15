# TODO LatheEasyStep

Stand: 2026-09-15

Diese Datei enthaelt ausschliesslich offene Aufgaben. Abgeschlossene Arbeiten,
Befunde und historische Teststaende stehen im [CHANGELOG.md](CHANGELOG.md) und
in den Berichten unter `doc/`. Release-Ziele stehen in [ROADMAP.md](ROADMAP.md).

## Verifizierte Basis

- Branch `dev`, Entwicklungsstand fuer 0.8.0; `main` bleibt die stabile
  0.7.0-Basis.
- 871 Stub-Qt-Tests und 106 Tests mit echtem PyQt5, keine Skips.
- Zwoelf Referenzprogramme bestehen statische NGC-Pruefung und den nativen
  LinuxCNC-Interpreter (`rs274`); zusaetzlich bestehen 43 Matrixprogramme.
- Alle zwoelf Referenzen wurden in der QtDragon-SIM bis `M30` ausgefuehrt.
- Der Generator ist von Qt getrennt. Reiter, Step-Verwaltung und Vorschau
  liegen in eigenen UI-/Fachmodulen.

## Priorisierter Arbeitsindex

| ID | Prio | Aufgabe | Aufwand | Ziel |
|---|---|---|---|---|
| LES-022 | P2 | Bewegungs- und Modalzustand vollstaendig fuehren | L | 0.9.0 |
| LES-051 | P1 | Panel-Grundgeruest und Darstellungsadapter weiter entkoppeln | XL | 0.9.0 |
| LES-052 | P1 | Panel-Architektur, Zustandsmodell und Wiederherstellung planen/umsetzen | XL | 0.9.0 |
| LES-044 | P2 | verbleibende Vorschau-Geometrie und Ausnahmegrenzen entkoppeln | L-XL | 0.9.0 |
| LES-032 | P2 | Werkzeuggeometrie fuer Plausibilitaet und Kollision erweitern | L | 0.9.0 |
| LES-043 | P2 | Gegenspindelfunktion als separates Projekt spezifizieren | XL | separat |
| LES-030 | extern | weitere reale Maschinenprofile verifizieren | extern | offen |

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

Erster Baustein umgesetzt: Besitzgrenzen sind in
`doc/PANEL_ARCHITECTURE.md` dokumentiert. Der Qt-freie `ToolVisualProvider`
loest logische Werkzeugdarstellungen aus einem Theme-Manifest auf und liefert
bei fehlenden oder ungueltigen PNG-/SVG-Dateien einen diagnostizierten
prozeduralen Fallback. Die Qt-Anbindung passt externe Bilder ein; Ressourcen-
fehler werden geloggt und im Fallback sichtbar markiert. Offen bleiben
konfigurierbare Theme-Auswahl, Cache und Lebensdauer.

- [ ] den verbleibenden Handler-Kleber weiter reduzieren. Neue Fachlogik darf
  nicht in `lathe_easystep_handler.py` entstehen; UI-Fragmente sollen nur
  definieren, welche Views geladen werden, nicht deren Zustand selbst besitzen.
- [x] Werkzeug- und Schneidplatten-Darstellungen aus der Funktion herausgeloest:
  der Qt-freie `ToolVisualProvider` (`tool_visuals.py`) loest ein Theme-
  Manifest auf, `render_tool_preview()` (`tool_logic.py`) bindet ihn als
  Qt-Adapter an - gueltige PNG-/SVG-Ressourcen werden seitenverhaeltnistreu
  eingepasst, fehlende/ungueltige Dateien fallen sichtbar markiert (Log +
  orangefarbenes Ausrufezeichen) auf die bisherige prozedurale Darstellung
  zurueck. Dabei einen bereits vorhandenen unausgeglichenen
  `QPainter.save()`-Zustand korrigiert.
- [x] Das Austauschen einer Schneidplatten-Grafik oder eines kompletten
  Darstellungs-Sets aendert weder Operationen, Werkzeugdaten noch G-Code -
  fuer Werkzeugdaten per Test nachgewiesen (`asdict(tool)` unveraendert vor/
  nach Ressourcenwechsel), fuer G-Code zusaetzlich end-to-end belegt
  (`test_switching_tool_visual_resource_never_affects_generated_gcode`:
  dasselbe Beispielprogramm zweimal erzeugt, einmal mit einer voellig
  unabhaengigen `render_tool_preview()`-Ausfuehrung mit externer Ressource
  dazwischen - identischer G-Code). Per absichtlich veraendertem Parameter
  (statt der Ressource) als echte Regression verifiziert: der Test schlaegt
  korrekt fehl, sobald sich der erzeugte G-Code tatsaechlich unterscheidet.
  Architekturell zusaetzlich abgesichert: kein `gcode_*.py`-/`checks.py`-
  Modul importiert `tool_visuals`/`render_tool_preview` ueberhaupt. Preview-
  Geometrie/Dirty-State sind ueber denselben Befund (keine Codeverbindung)
  ebenfalls unberuehrt, aber (noch) ohne eigenen End-to-End-Test - beide
  haengen ohnehin nicht von `tool_logic.py` ab.
- [x] Ressourcenpfade werden nicht in Fachobjekten oder gespeicherten
  Programmen verankert: `ToolVisualProvider` haelt Root/Manifest nur in der
  eigenen Instanz (Handler-Attribut, nicht Teil von `Tool` oder gespeicherten
  Programmdaten), loest Pfade je Aufruf frisch auf und lehnt absolute Pfade,
  nicht unterstuetzte Formate und Pfade ausserhalb der Theme-Root ab
  (`relative_to()`-Pruefung). Cache/Lebensdauer bleiben offen (siehe
  Kurzfassung oben).
- [ ] weitere austauschbare Panelbereiche identifizieren, insbesondere
  Preview-Canvas, Legende, Status-/Warnungsdarstellung und optionale
  Bedienelemente. Jede Darstellung soll ueber einen stabilen Datenvertrag
  auswechselbar sein. Erster Baustein umgesetzt: die Vorschau-Legende
  (10 Eintraege: Label, RGB-Farbe, Linienbreite, Qt-freier Stilname
  "solid"/"dash"/"dashdot") liegt jetzt als reiner Datenvertrag
  `LEGEND_ENTRIES` in `preview_geometry.py`; `paintEvent()`
  (`preview_widget.py`) konstruiert daraus nur noch `QPen`/`QColor` (Qt-
  Adapter). Bewusst NICHT gleichzeitig uebersetzt (die Legende ist seit je
  her ungebunden an `_tr()`, siehe LES-044 - eigenes Thema). Stil-Mapping
  bewusst lokal in `paintEvent()` statt auf Modulebene gehalten: ein
  Modulebenen-Dict mit `QtCore.Qt.SolidLine` haette den Import von
  `preview_widget.py` schon in der Stub-Qt-Suite gebrochen (`QtCore.Qt`
  ist dort ein leeres Fake-Namespace-Objekt) - echter Regressionsfund
  waehrend der Umsetzung, sofort korrigiert und per absichtlich
  zurueckgesetzter Korrektur verifiziert. Zwei neue Stub-Tests
  (`tests/test_preview_legend_and_status_layout.py`): Datenvertrag ist
  Qt-frei/eindeutig, `legend_layout()`-Zeilenzahl passt zur Eintragsanzahl;
  per absichtlich dupliziertem Label als echte Regression verifiziert.
  Live im Standalone-Panel bestaetigt: Legende sieht unveraendert aus,
  kein Fehler im Log. 871 Stub-/106 Real-Qt-Tests bestanden. Preview-
  Canvas, Status-/Warnungsbox und optionale Bedienelemente bleiben offen.
- [ ] Shell- und Fragment-Laden fuer Standalone und Embedded mit einem
  definierten Ladevertrag absichern: Reihenfolge, Widget-Registrierung,
  Signalbindung, Fehlerbehandlung und Wiederholung duerfen nicht vom
  konkreten Skin oder Ressourcenpaket abhaengen.
- [x] Je ein Test fuer einen alternativen Ressourcensatz (externes PNG) und
  eine fehlende Ressource ergaenzt, dazu ein dritter fuer eine nicht
  dekodierbare Datei (`tests/test_tool_preview_layout.py`). Stub-Qt (871)
  und Real-Qt (106) bestehen; Standalone-Panel bis `critical done` nach
  2,337 s gestartet und sauber beendet. Kein LinuxCNC-Lauf noetig, da G-Code
  und Fahrwege unveraendert bleiben.

## LES-052 Panel-Architektur, Zustandsmodell und Wiederherstellung

Diese Aufgabe beschreibt den groesseren Ausbauplan auf Basis von LES-051. Vor
der Umsetzung muessen die Grenzen zwischen fachlichem Zustand, Controller,
Views, Ressourcen und Persistenz festgelegt werden. Kein einzelner Umbau darf
die G-Code-Erzeugung oder bestehende Maschinenlogik nur wegen einer optischen
Aenderung veraendern.

### 1. Architektur und Ladevertrag

- [ ] `ProgramState`, `OperationState`, `ToolTableState`, `ViewState`,
  `DirtyState` und `RuntimeState` als fachlich getrennte Verantwortungen
  beschreiben und ihre Besitzverhaeltnisse dokumentieren.
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

## LES-044 Vorschau und Darstellung

Die Qt-freie Geometrieplanung ist fuer Navigation, Raster, Pfade, Sperrzonen
und Vorderansicht weitgehend umgesetzt. Offen bleiben:

- [ ] verbleibende fachliche Darstellungsberechnungen aus
  `preview_widget.py`/`ui_preview.py` in Qt-freie Planfunktionen verschieben;
  Qt-Code soll nur Stil, Widget-Zustand und QPainter-Ausgabe enthalten.
- [ ] die verbleibenden breiten `except Exception`-Fallbacks einzeln bewerten
  und, wo fachlich moeglich, auf erwartete Ausnahmetypen begrenzen. Das
  inzwischen vorhandene Debug-Logging bleibt bis dahin die bewusste
  Zwischenloesung.
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

## LES-043 Gegenspindel

Die nicht implementierten Bedienelemente bleiben sichtbar, aber gesperrt.

- [ ] separate Spezifikation erstellen: Operationen, Spindelsynchronisation,
  S3-Grenzen, Koordinatensysteme und Kollisionsmodell.
- [ ] LinuxCNC-SIM- und Maschinenkonzept fuer diese Spezifikation festlegen,
  bevor irgendeine Generatorimplementierung in LatheEasyStep beginnt.

## LES-030 Externe Maschinenverifikation

- [ ] unterschiedliche reale Drehmaschinen mit Achsgrenzen,
  Werkzeugwechselpositionen und Futterbauformen verifizieren.

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
