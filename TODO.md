# TODO LatheEasyStep

Stand: 2026-09-16

Diese Datei enthaelt ausschliesslich offene Aufgaben. Abgeschlossene Arbeiten,
Befunde und historische Teststaende stehen im [CHANGELOG.md](CHANGELOG.md) und
in den Berichten unter `doc/`. Release-Ziele stehen in [ROADMAP.md](ROADMAP.md).

## Verifizierte Basis

- Branch `dev`, Entwicklungsstand `0.8.0-dev`; `main` bleibt die stabile
  0.7.0-Basis.
- 877 Stub-Qt-Tests und 108 Tests mit echtem PyQt5, keine Skips.
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
  kein Fehler im Log. 871 Stub-/106 Real-Qt-Tests bestanden. Zweiter
  Baustein: dieselbe Behandlung fuer die Status-/Warnungsbox -
  `STATUS_BOX_STYLE` (`preview_geometry.py`: Randfarbe, Fuellfarbe inkl.
  Alpha, Textfarbe, Kopfzeile "Warnungen") ersetzt die bisher direkt in
  `paintEvent()` hartkodierten `QColor`-Werte. Ein weiterer Stub-Test, per
  eingefuegtem unerwartetem Schluessel als echte Regression verifiziert.
  872 Stub-/106 Real-Qt-Tests bestanden (kein separater Standalone-Check -
  identisches, bereits live bestaetigtes Extraktionsmuster wie die Legende
  unmittelbar zuvor, keine neue Risikoflaeche). Dritter Baustein: der
  Haupt-Vorschau-Canvas (Seitenansicht) selbst - `PREVIEW_DRAW_STYLES`
  (`preview_geometry.py`) deckt alle elf `style_key`-Werte ab, die
  `build_preview_draw_plan()` erzeugen kann (Werkstueck/Werkzeugweg/
  Rohteil/Rueckzug/Futter-Sperrzone/Schruppkontur/Freistich/aktiv/
  Hilfsgeometrie), inklusive zweier vorher als Qt-Farbnamen ("gray"/
  "red"/"lime") statt RGB-Tripel hinterlegter Eintraege - fuer Konsistenz
  auf die per Laufzeitpruefung bestaetigten RGB-Aequivalente umgestellt
  (gray=(128,128,128) usw.), keine sichtbare Aenderung. Ein weiterer
  Stub-Test prueft, dass der Datenvertrag genau die von
  `build_preview_draw_plan()` moeglichen Schluessel abdeckt (ein fehlender
  wuerde `paintEvent()` mit `KeyError` abstuerzen lassen) - per entferntem
  Schluessel als echte Regression verifiziert. Kein separater Standalone-
  Klicktest (das Hinzufuegen eines Schritts per synthetischem X11-Klick
  liess sich in dieser Sitzung wiederholt nicht zuverlaessig ausloesen);
  stattdessen bereits bestehender, jetzt erneut gruener Real-Qt-Test
  `test_side_view_paints_expanded_legend_and_status_messages_without_crash`
  als staerkerer Nachweis herangezogen - er durchlaeuft denselben
  `styles`-Dict/`draw_plan`-Code mit echten synthetischen Pfaden.
  873 Stub-/106 Real-Qt-Tests bestanden. Preview-Canvas-Farbcontract ist
  damit umgesetzt; optionale Bedienelemente bleiben offen.
  Vierter/fuenfter Baustein (2026-09-16, LES-044): die verbliebenen
  Vorderansichts- und "Chrome"-Farben. `FRONT_VIEW_RING_STYLES`/
  `FRONT_VIEW_FILL_COLORS` decken alle sieben `style_key`-Werte von
  `build_front_view_draw_plan()` ab (Rohteilringe, Durchmesserringe,
  Endkontur-Fuellung/-Loch). Danach `PREVIEW_CHROME_STYLES`/
  `PREVIEW_CHROME_FILLS`: Achsen, Gitterticks/-beschriftung, Schnittlinie/
  -label der Seitenansicht, Legenden-Rahmen/-Hintergrund/-Text, Vorder-
  ansichts-Achsen/-Infotext, Keilnut-Overlay-Umriss/-Fuellung, Kreis/Text
  der Schnittansicht - Struktur-/Chrome-Elemente statt semantischer Rollen-
  Stile, aber genauso vorher hartkodiert. Zwei neue Hilfsmethoden
  `_chrome_pen()`/`_chrome_fill()` (`preview_widget.py`) buendeln die Qt-
  Adaption statt sie an jeder Stelle zu wiederholen; Stil-Mapping weiterhin
  lokal im Methodenkoerper (nicht Modulebene). Dabei eine echte Test-
  luecke geschlossen: `_paint_slice_view()` (Schnittansicht) hatte bislang
  keinen Real-Qt-Test - neuer Test `test_slice_view_paints_without_crash`
  (`tests/test_preview_widget_paint_no_crash.py`) deckt sie jetzt ab. Per
  entferntem Schluessel als echte Regression verifiziert - im Stub-Test als
  sauberer `AssertionError`, im Real-Qt-Test als harter Prozessabsturz
  (PyQt5 kann eine unbehandelte Python-Exception aus `paintEvent()` nicht
  sauber propagieren), beides wie erwartet. Einzig verbliebenes Farb-
  literal in `preview_widget.py`: der schwarze Canvas-Hintergrund
  (`QtCore.Qt.black`, 3x identisch) - bewusst nicht extrahiert, da eine
  einzelne, ueberall gleiche Konstante ohne Duplizierungsrisiko. Damit ist
  LES-044s erster Punkt ("Darstellungsberechnungen aus preview_widget.py/
  ui_preview.py in Qt-freie Planfunktionen verschieben") fuer alle
  Farb-/Stil-Werte des Preview-Widgets abgeschlossen; verbleibende
  fachliche Geometrieberechnungen (falls noch vorhanden) und die breiten
  `except Exception`-Fallbacks (zweiter Punkt) sind separat zu pruefen.
  877 Stub-/107 Real-Qt-Tests bestanden. Standalone-Panel offscreen bis
  `_finalize_ui_ready DONE` sauber gestartet.
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
und Vorderansicht weitgehend umgesetzt. Offen bleiben:

- [ ] verbleibende fachliche Darstellungsberechnungen aus
  `preview_widget.py`/`ui_preview.py` in Qt-freie Planfunktionen verschieben;
  Qt-Code soll nur Stil, Widget-Zustand und QPainter-Ausgabe enthalten.
  Teilschritt (2026-09-16): die Ringe/Fuellungen der Vorderansicht
  (`_paint_front_view()`) folgen jetzt demselben Datenvertrag-Muster wie die
  Seitenansicht (LES-051) - `FRONT_VIEW_RING_STYLES` (Rohteil-Aussen-/
  Innendurchmesser, sichtbare Aussen-/Innen-Durchmesserringe, aktiver Ring)
  und `FRONT_VIEW_FILL_COLORS` (Endkontur-Fuellung/-Loch, RGBA wegen
  Transparenz) in `preview_geometry.py` decken alle sieben `style_key`-Werte
  ab, die `build_front_view_draw_plan()` (`preview_scene.py`) erzeugen kann.
  Zwei neue Stub-Tests (`tests/test_preview_legend_and_status_layout.py`,
  875 Stub-/106 Real-Qt-Tests bestanden), per entferntem Schluessel als
  echte Regression verifiziert. Real-Qt-Abdeckung ueber die bereits
  bestehenden, weiterhin gruenen Tests
  `test_front_view_paints_external_abspanen_without_crash`/
  `test_front_view_paints_internal_abspanen_without_crash`/
  `test_front_view_paints_keyway_without_crash`
  (`tests/test_preview_widget_paint_no_crash.py`), die `_paint_front_view()`
  mit echtem PyQt5 durchlaufen. Standalone-Panel offscreen bis
  `_finalize_ui_ready DONE` sauber gestartet. Bewusst NICHT mit erledigt:
  die uebrigen Qt-Farbliterale in `preview_widget.py` (Achsen/Gitterticks,
  Legende-/Status-Box-Rahmen, Keilnut-Overlay, Schnittlinie) sind
  Chrome/Struktur statt semantischer Rollen-Stile und damit ein groesserer,
  separat zu bewertender Umfang als die bisherigen Datenvertrag-Schritte.
- [x] die verbleibenden breiten `except Exception`-Fallbacks einzeln bewerten
  und, wo fachlich moeglich, auf erwartete Ausnahmetypen begrenzen. Das
  inzwischen vorhandene Debug-Logging bleibt bis dahin die bewusste
  Zwischenloesung. Erster Baustein (2026-09-16): alle acht Vorkommen in
  `preview_widget.py` einzeln bewertet. Zwei liessen sich sicher begrenzen -
  `_debug_slice()` (nur `print()`, jetzt `(OSError, UnicodeError)`) und
  `set_primitives()` (liest primitive-Dicts per `tuple()`/Indexzugriff,
  jetzt `(TypeError, ValueError, IndexError)`, verifiziert per Monkeypatch:
  eine synthetische `AttributeError` wird korrekt NICHT mehr geschluckt,
  sondern propagiert). Zwei bleiben bewusst breit (`sliceChanged.emit()`/
  `_slice_change_callback()` in `set_slice_z()` - rufen synchron beliebigen
  Fremdcode auf, dessen Ausnahmeklassen ausserhalb der Kontrolle dieser
  Methode liegen) - jeweils mit Begruendung kommentiert. Die restlichen vier
  (`paintEvent()`-interne QPainter-Bloecke) bleiben ebenfalls bewusst breit,
  aber aus einem anderen, waehrenddessen entdeckten Grund: eine unbehandelte
  Ausnahme in `paintEvent()` beendet unter echtem PyQt5 nicht nur den
  Zeichenvorgang, sondern den gesamten Prozess (empirisch reproduziert -
  ein absichtlich entfernter Datenvertrag-Schluessel liess den Real-Qt-
  Testlauf hart abstuerzen statt einen Test fehlschlagen zu lassen). Dabei
  eine echte Luecke gefunden und geschlossen: die "slice"/"front"-Zweige in
  `paintEvent()` hatten bislang GAR kein Exception-Netz (nur `finally:
  painter.end()`) - jetzt wie der "side"-Zweig mit `except Exception`
  abgesichert. Die bestehenden Real-Qt-Paint-Tests
  (`tests/test_preview_widget_paint_no_crash.py`) pruefen jetzt zusaetzlich
  per `caplog`, dass `paintEvent()` keine unterdrueckte Ausnahme geloggt hat
  - sonst wuerde das neue Sicherheitsnetz einen echten Bug nur noch still
  verschlucken, statt ihn wie zuvor (als Absturz) sichtbar zu machen. Per
  entferntem Datenvertrag-Schluessel als echte Regression verifiziert: vor
  der Aenderung Prozessabsturz, danach sauberer, `caplog`-basierter
  Testfehlschlag. 877 Stub-/108 Real-Qt-Tests bestanden. Zweiter Baustein
  (2026-09-16): `ui_preview.py` (32 Vorkommen). 26 davon liessen sich
  begrenzen - durchgaengig Qt-Widget-Methodenaufrufe auf `handler.preview`/
  `preview_slice`/`btn_slice_view`/`btn_reset_view` oder auf per
  `_get_widget_by_name()` ermittelte Objekte, deren Lebensdauer/Typ nicht
  garantiert ist: `(RuntimeError, AttributeError)` (RuntimeError bei einem
  zwischen Lookup und Aufruf zerstoerten C++-Qt-Objekt, AttributeError bei
  fehlender Methode/fehlendem Attribut), bei `.connect()`-Aufrufen
  zusaetzlich `TypeError` (nicht-kompatible Signatur). Dabei zwei echte
  Fehleinschaetzungen gemacht und durch den vollen Testlauf sofort
  gefunden: `update_slice_view_button()`s `button.setText()`/
  `setToolTip()` zunaechst nur auf `RuntimeError` begrenzt, obwohl ein
  minimaler Test-Stub ohne `setToolTip()`-Methode (uebliches Testmuster in
  diesem Projekt) ein `AttributeError` ausloest - `test_keyway_preview.py::
  test_toggle_slice_view_switches_main_preview_mode` schlug prompt fehl.
  Ebenso `_current_language_code()`s eigener `get_widget_by_name()`-Aufruf:
  liest `self.root_widget` OHNE `getattr()`-Fallback - auf einem
  `object.__new__(HandlerClass)`-Test-Handler ohne dieses Attribut ebenfalls
  ein `AttributeError`, nicht nur `RuntimeError`. Beide Male die Ausnahme-
  liste um `AttributeError` ergaenzt, erneut den vollen Testlauf geprueft
  (877/108 gruen). Zusaetzlich per Monkeypatch (analog zu
  `preview_widget.py`) fuer `setup_slice_view()`/`on_toggle_slice_view()`
  verifiziert: eine synthetische `KeyError` propagiert korrekt, eine echte
  `RuntimeError` wird weiterhin sauber geschluckt. Dritter Baustein
  (2026-09-16): vier der restlichen sechs Vorkommen in `collect_preview_
  state()`/`_detect_preview_collision()` nach genauerer Einzelpruefung
  doch begrenzt - `_current_op_type()` (`(RuntimeError, AttributeError)`,
  liest `self.tab_params` ohne `getattr()`-Fallback), `_collect_params()`
  (dieselben zwei Klassen, liest `self.param_widgets` ebenso ungeschuetzt),
  die sechs Vorschau-Builder-Aufrufe (`build_face_path` u. a., `(TypeError,
  ValueError, IndexError)` - rechnen mit `params`-Werten, die `collect_
  params()` bei nicht als Zahl parsbarem Text roh als String ablegt) und
  `_detect_preview_collision()` selbst (`(TypeError, ValueError, IndexError,
  AttributeError)` - liest primitive-Dicts per `.get()`/Indexzugriff und
  entpackt p1/p2/points als (x, z)-Paare). Jede der vier Begrenzungen per
  Monkeypatch in beide Richtungen verifiziert: eine synthetische `KeyError`
  propagiert korrekt, die tatsaechlich erwartete Ausnahme (z. B. ein zu
  kurzes `p1`, ein `None`-Punkt, ein fehlendes `tab_params`-Attribut) wird
  weiterhin sauber geschluckt - diesmal im ersten Anlauf ohne Fehltritt
  gruen (877 Stub-/108 Real-Qt-Tests). Die verbleibenden zwei Vorkommen
  (Warnungs-Aggregation aus drei unabhaengigen Funktionen; Rohteil-/
  Rueckzugs-/Worklimit-/Sperrzonen-Builder-Aufrufe) bleiben bewusst breit
  und sind entsprechend kommentiert - sie aggregieren mehrere unabhaengige
  Funktionen, deren Fehlerursachen sich ohne tiefere Einzelpruefung jeder
  einzelnen nicht verlaesslich eingrenzen lassen, und betreffen ohnehin nur
  die Vorschau-/Warnungsanzeige, nie die G-Code-Erzeugung selbst. Damit ist
  diese Aufgabe fuer `preview_widget.py`/`ui_preview.py` abgeschlossen (36
  von 40 urspruenglichen Vorkommen begrenzt, 4 bewusst breit mit
  dokumentierter Begruendung); andere Module (`ui_header.py`, `ui_params.py`
  usw.) wurden nicht durchsucht.
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
