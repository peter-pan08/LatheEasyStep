# LatheEasyStep – Anweisungen für KI-Coding-Agenten

## Projektübersicht
**LatheEasyStep** ist ein conversational turning panel (Drehpanel) für LinuxCNC (QTVCP), das die G-Code-Erzeugung direkt an der Maschine ohne externe CAM-Software ermöglicht. Es ist speziell für **deutschsprachige Werkstätten** konzipiert (zweisprachige Benutzeroberfläche).

### Architektur-Schichten
- **UI-Schicht**: PyQt5/QTVCP-basiertes conversational panel (`lathe_easystep.ui` + `lathe_easystep_handler.py`)
- **Modell-Schicht**: `ProgramModel` dataclass verwaltet Operationen, Parameter und erzeugt optimierte G-Code
- **Pfad-Builder**: Geometrische Algorithmen (`build_*_path()`, `build_*_primitives()`) erzeugen 2D XZ-Konturen
- **Preview-Widget**: `LathePreviewWidget` rendert live XZ-Seitenansicht mit Kollisionserkennung und Schnittansicht
- **Generator-Schicht**: `gcode_for_*()` Funktionen erzeugen LinuxCNC Fanuc-kompatible G-Code (G71/G70 für Konturen, G76 für Gewinde)
- **Slicer-Modul**: `slicer.py` implementiert parallele/Querschnitt-Schrupperstrategien (Abspanen = Abstechbearbeitung)

---

## Wichtige Entwickler-Workflows

### Neue Operationstypen hinzufügen
1. Operationstyp in `OpType` Klasse definieren (z.B. `MYOP = "myop"`)
2. Parameter-Zuordnung in `_setup_param_maps()` erstellen (Qt-Widgets → Operationsparameter)
3. `build_myop_path(params)` implementieren — gibt Liste von (x,z)-Punkten oder dict-Primitives für Preview zurück
4. `gcode_for_myop(op: Operation)` implementieren — gibt Liste von G-Code-Strings zurück
5. Operationstyp zum `gcode_for_operation()` Dispatcher hinzufügen
6. UI-Tab in `lathe_easystep.ui` mit Parameter-Spinboxen/Combos hinzufügen
7. Tab-Übersetzungen in `TAB_TRANSLATIONS` dict registrieren

### Gewinde-Logik ändern
- Gewinde-G-Code verwendet **G76** (Fanuc-Standard) mit Parametern: `P` (Steigung), `Z` (Länge), `K` (Tiefe), `J` (erste Zustellung), `Q` (Winkel), usw.
- Profilspezifische Standardwerte (metrisch vs. Trapezgewinde) befinden sich in `_apply_thread_preset()`
- **Steigungsnormalisierung**: User-Input immer auf `.` vs `,` Dezimaltrennzeichen prüfen (deutsche Locale)

### Änderungen testen
```bash
# Umgebung einrichten (WICHTIG: venv verwenden wegen LinuxCNC hal-Modul)
source .venv/bin/activate
pip install -r requirements-dev.txt

# Alle Tests ausführen (Mock-Objekte für hal-Modul)
pytest

# Spezifisches Modul testen
pytest tests/test_lathe_easystep_handler.py -v
```

---

## Kritische Muster & Konventionen

### X-Koordinatensystem (Durchmesser)
- **ÜBERALL**: X-Werte sind **Durchmesser**-Koordinaten (nicht Radius), entsprechend LinuxCNC-Lathe-Konvention
- Im Preview: X-Werte werden als Radius gezeichnet für visuelle Klarheit, aber als Durchmesser beschriftet
- Beim Lesen aus UI-Spinboxen mit Label „Durchmesser" → das ist Durchmesser, direkt verwenden

### Z-Koordinaten-Konventionen
- **Z0** = Stirnfläche (Planseite) des Werkstücks
- **Negatives Z** = ins Werkstück hinein (typische Drehrichtung bei dieser Maschine)
- Rückzugsebenen (`xra`, `xri`, `zra`, `zri`) können absolut oder inkremental sein (Flags: `*_absolute` Checkboxen)

### Programmkopf + Rohteilgeometrie
- Jedes Programm beginnt mit einer **Programmkopf**-Operation (OpType.PROGRAM_HEADER)
- Rohteilkontur + Rückzugsebenen werden aus Header-Parametern (`xa`, `xi`, `za`, `zi`, `xra`…) hergeleitet via `build_stock_outline()` + `build_retract_primitives()`
- Diese werden als **Referenz-Geometrie** (gestrichelte Linien) im Preview gezeichnet, nicht als zerspanbare Konturen

### Sprachunterstützung
- **Standard**: Deutsch (`de`), Fallback auf Englisch (`en`)
- Übersetzungen befinden sich in `TEXT_TRANSLATIONS`, `COMBO_OPTION_TRANSLATIONS`, `TAB_TRANSLATIONS` Dicts
- **Kritisch**: Widget-Labels müssen im Übersetzungs-Dict vorhanden sein, sonst werden sie unübersetzt angezeigt
- `_apply_language_texts()` verwenden, um alle Widgets nach Sprachänderung zu aktualisieren

### Eingebettete Panel-Integration (QtVCP-Kontext)
- LatheEasyStep kann **eingebettet** in LinuxCNCs MainWindow oder als **standalone** Panel laufen
- Widget-Discovery nutzt Fallback-Suche: direktes Attribut → panel-lokaler Baum → globale allWidgets()
- **Nie annehmen**, dass Widgets direkte Attribute sind; `_get_widget_by_name()` für späte Bindung nutzen
- Panel-Root-Erkennung prüft `objectName` gegen `PANEL_WIDGET_NAMES` Tuple (Robustheit für MainWindow/VCPWindow-Umhüllung)
- **Deferred Widget Loading**: Widgets werden nicht sofort bei `initialized__()` verfügbar; multiple QTimer.singleShot() Retries (0ms, 100ms, 200ms, 300ms, 500ms, 700ms, 1000ms, 1500ms, 2000ms)
- **Polling für Missing Widgets**: `_poll_for_widget()` sucht 30x alle 100ms (3 Sekunden) nach nicht gefundenen Widgets
- **Signal Connection Retries**: Buttons werden bei Fund automatisch mit `_connect_button_signal()` verbunden
- **Visibility Force Updates**: `_force_visibility_updates()` erzwingt UI-Updates nach Widget-Discovery für korrekte Sichtbarkeit in embedded Mode

### Kontur-Geometrie
- Kontur wird als Liste von **Segmenten** definiert (jede Zeile in Tabelle = Segment-Endpunkt)
- **Kanten** (Fase/Radius) werden an Ecken **zwischen** Segmenten angewendet, nicht an Endpunkten
- Letztes Segment kann keine Kante haben (kein folgendes Segment → keine Ecke)
- Inkrementaler Modus (`coord_mode=1`) interpretiert Bewegungen relativ zum vorherigen Punkt
- Radius-Validierung nutzt Kreis-Geometrie: `r / tan(angle/2)` muss in beiden angrenzenden Segmenten passen

### G-Code-Ausgabe-Invarianten
1. Immer `G18 G7 G90 G40 G80` emittieren (Lathe-Standardwerte: XZ-Ebene, Durchmesser, absolut, keine Fräser-Kompensation, modal abbrechen)
2. `G21` bei metrischen Einheiten, `G20` bei Imperial emittieren
3. `G95` emittieren (Vorschub pro Umdrehung) — erforderlich für Lathe-Vorschub in mm/U
4. Arbeits-Versatz beibehalten (`G54` Standard, konfigurierbar)
5. **Standardmäßig keine Satznummern** (`emit_line_numbers=False`) — Nutzer-Opt-in über Einstellungen

### Gewinde (G76) Parameter-Details
- **P**: Steigung (exakt, z.B. 1,5 mm)
- **Z**: Gewinde-Ende (absolut, z.B. -50,0 für 50mm Tiefe ins Teil)
- **K**: Gesamttiefe (radial, z.B. 0,92mm für M6)
- **J**: Erste Zustellung (radial, oft K×0,1)
- **Q**: Zustellwinkel (°, typisch 29,5° für metrisch, 15° für Trapezgewinde)
- **I**: Spitzenabzug / Grat-Reduktion (oft negativ, z.B. -0,5 für Nachbearbeitung)
- **R**: Rückzugsdistanz (Sicherheits-Ausfahrt, z.B. 1,5mm)
- **H**: Leerschnitte (Nachbearbeitungsschnitte, typisch 1)
- **E, L**: Optional (Finish-/Mehrstart-Flags)

### Kollisionserkennung & Validierung
- `validate_contour_segments_for_profile()` prüft geometrische Machbarkeit **vor** Preview-Zeichnung
- Gibt (bool, list[error_strings]) zurück — für UI-Feedback nutzen
- Wichtige Prüfungen: Segmentlänge, Eckenwinkel, Radius-/Fasen-Machbarkeit
- Terminal-Debug-Ausgabe protokolliert ungültige Radien → Konsole inspizieren, wenn Preview leer ist

---

## Überblick über Datenflüsse

### Programm-Generierungs-Workflow
```
Nutzer füllt Programm-Tab aus (Header-Parameter)
  ↓
Nutzer erstellt Operationen (Planen, Kontur, Gewinde, usw.)
  ↓
_handle_param_change() → _update_selected_operation()
  ↓
ProgramModel.update_geometry() → ruft build_*_path(params) auf
  ↓
LathePreviewWidget.set_paths() → rendert XZ-Preview mit Rohteilkontur
  ↓
Nutzer klickt „Programm erzeugen"
  ↓
ProgramModel.generate_gcode() → verbindet alle gcode_for_*() Ausgaben
  ↓
Schreibt in Datei (Standard: ~/linuxcnc/nc_files/generated.ngc)
```

### Kontur-Bearbeitung
```
Nutzer wählt Zeile in contour_segments Tabelle
  ↓
_on_contour_cell_changed() → validiert Zelle + aktualisiert Segment-Dict
  ↓
_update_contour_preview_temp() → Primitives via build_contour_path() neu aufbauen
  ↓
Preview-Widget aktualisiert sich (Live-Feedback)
```

### Schnittansicht (Optional)
- Umgeschaltet mit `btn_slice_view` (falls in UI vorhanden)
- Zeigt **Querschnitt** an benutzer-verschiebbarer Z-Position
- Interpoliert Werkstück-Durchmesser aus aktiver Kontur-Pfad
- Nützlich, um zu überprüfen, dass Schrupp-Schnitte nicht übergehen

---

## Dateiorganisation

| Datei | Zweck |
|-------|-------|
| `lathe_easystep_handler.py` | Haupt-Handler; 7100+ Zeilen mit Modell, Buildern, Generatoren, Qt-Integration |
| `lathe_easystep.ui` | Qt Designer Datei (XML); definiert Parameter-Tabs, Preview-Layout, Buttons |
| `slicer.py` | Parallele/Querschnitt-Schruppbearbeitung (Abspanen-Strategie); importiert vom Generator |
| `README.md` | Nutzer-Dokumentation (Operationstypen, Feature-Matrix) |
| `DEV.md` | Entwickler-Notizen (Test-Setup, bekannte Limitierungen) |
| `tests/` | Unit-Tests mit `unittest`; alle Tests nutzen Mocks für `qtvcp.core` |

---

## Häufige Fehler & Lösungen

| Problem | Root Cause | Lösung |
|---------|-----------|--------|
| Preview leer bei Kontur | Ungültiger Radius (zu groß für Segmente) | Terminal-Ausgabe überprüfen; mit `validate_contour_segments_for_profile()` validieren |
| Gewinde erscheint nicht im Preview | G76 ist nicht-modales G-Code (keine Pfad-Geometrie) | Erwartet; Terminal auf Warnungen prüfen |
| Sprachänderung aktualisiert Button-Text nicht | Button nicht in `_apply_language_texts()` registriert | Button-Text-Mapping in `BUTTON_TRANSLATIONS` hinzufügen |
| Eingebettete Panel-Widgets nicht gefunden | Qt-Discovery-Timing-Problem | Mehrfach-Retries in `initialized__()` (9 Timer von 0-2000ms), Polling für missing Widgets (3s), erweiterte Fallbacks in `_find_any_widget()` |
| Buttons funktionieren nicht (None-Objekte) | Signale nicht verbunden bei deferred Loading | Automatische Signal-Verbindung in `_connect_button_signal()` bei Widget-Fund, `_connect_button_once()` verhindert Duplikate |
| Visibility-Änderungen funktionieren nicht | UI-Updates nicht angewendet in embedded Mode | `_force_visibility_updates()` erzwingt Updates nach Discovery, alle visibility-dependent Widgets werden neu berechnet |
| Einheits-Suffix (mm/inch) aktualisiert nicht | `program_unit` Combo nicht verbunden | Combo in `_find_unit_combo()` gefunden + Signal in `_connect_signals()` verbunden sein |
| Kontur-Kanten-Einstellungen unsichtbar | `face_edge_type` / `face_edge_size` Widgets nicht in UI | PATCH in `initialized__()` nutzt `contour_edge_*` als Fallback |

---

## Schlüssel-Dateien für häufige Aufgaben

**Operationsparameter hinzufügen?** → `lathe_easystep_handler.py:_setup_param_maps()` + `lathe_easystep.ui` (neue Spinbox + Label)

**Preview-Rendering reparieren?** → `LathePreviewWidget.paintEvent()` (Koordinaten-Abbildung, Achsen-Skalierung)

**Threading-Defaults anpassen?** → `_apply_thread_preset()`, `STANDARD_METRIC_THREAD_SPECS`, `STANDARD_TR_THREAD_SPECS`

**Neue Sprache unterstützen?** → Einträge zu `TEXT_TRANSLATIONS`, `COMBO_OPTION_TRANSLATIONS`, `TAB_TRANSLATIONS` Dicts hinzufügen

**Eingebettete Integration debuggen?** → Überprüfe `_find_root_widget()`, aktiviere Terminal-Ausgaben in `initialized__()`, nutze `_poll_for_widget()` für deferred Widgets, `_force_visibility_updates()` für UI-Updates

---

## Test-Erwartungen
- **Keine Hardware erforderlich** — alle Tests nutzen Qt-Mocks und Dummy `hal`-Modul
- **Von venv aus ausführen** — sichert korrekte Python-Pfade für `qtvcp`-Imports
- **Terminal-Ausgabe** — Unit-Tests drucken Widget-Resolving-Debug-Infos; zur Überprüfung durchsehen
- **UI-Tests begrenzt** — Fokus auf Modell/Builder-Logik; Qt-Signal-Mocking ist komplex

---

## Schnellreferenz: Operationstypen

| Op-Typ | Builder | Generator | Preview-Typ | G-Code |
|--------|---------|-----------|-------------|--------|
| FACE | `build_face_path()` | `gcode_for_face()` | Punkte+Kanten | G0/G1 mit opt. Pausen |
| CONTOUR | `build_contour_path()` | `gcode_for_contour()` | Primitives (Linie/Bogen) | G71/G70 (nur Kommentare in aktueller Impl.) |
| THREAD | `build_thread_path()` | `gcode_for_thread()` | Punkte | G76 (Fanuc) |
| GROOVE | `build_groove_path()` | `gcode_for_groove()` | Punkte | G0/G1 |
| DRILL | `build_drill_path()` | `gcode_for_drill()` | Punkte | G81/G83 |
| ABSPANEN (Abstechbearbeitung) | `build_abspanen_path()` | `gcode_for_abspanen()` | Punkte | G71 Schruppbearbeitung + G1 Schlichtbearbeitung |
| KEYWAY | `build_keyway_path()` | `gcode_for_keyway()` | Punkte | Makro-Aufruf `o<keyway_c>` |

---

## Setup & Abhängigkeiten

**Python 3.7+** erforderlich. Wichtigste Abhängigkeiten:
- `qtpy` (Qt-Abstraktion; fällt zu PyQt5 zurück)
- `qtvcp` (LinuxCNC's Qt-Wrapper) — systemweit installiert
- Testing: `pytest`, `unittest.mock`

Zur Entwicklung venv nutzen:
```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Das `--system-site-packages` Flag stellt sicher, dass `qtvcp.hal` verfügbar ist (LinuxCNC's System-Modul).
