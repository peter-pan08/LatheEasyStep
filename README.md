# LatheEasyStep – Kurzes Handbuch (Deutsch)

LatheEasyStep ist ein QtVCP-Makro, das im QtDragon-Panel unter **Macros → LatheEasyStep** eingebettet wird. Es ersetzt das direkte G-Code-Tippen durch eine Schritt-für-Schritt-Maske, in der jeder Arbeitsschritt (Planen/Facing, Kontur/Contour, Abspanen/Parting, Gewinde/Thread, Einstich/Abstich, Bohren/Drilling, Keilnut/Keyway) seinen eigenen Tab mit Werkzeug-, Spindel-, Vorschub- und Kühlparametern hat. Links befindet sich die Liste der Schritte, rechts die Parameterübersicht mit 2D-Vorschau; optional wird unten der generierte G-Code angezeigt.

## Funktionen

1. Rohteil im Programm-Tab definieren: Einheit, Rohteilform, Werkzeugwechsel, Rückzugsebenen, Sicherheitsabstände, Sprache (Deutsch oder English) und Spindelgrenzen.
2. Arbeitsschritte hinzufügen oder löschen; Pfeile verschieben die Reihenfolge in der Liste.
3. Tab-spezifische Parameter ausfüllen (Werkzeugnummer, Drehzahl, Vorschub, Kühlung, reduzierte Zonen, Spanbruch-Modi, Gewindestandards, Schneidenbreite usw.).
4. Vorschau prüfen; **G-Code erzeugen** schreibt `~/linuxcnc/nc_files/lathe_easystep.ngc`, öffnet die Datei und ergänzt Kommentare zu Toolwechsel, Kühlung und reduzierten Bereichen.

## Einbindung in die GUI

Die UI liegt in `macros/LatheEasyStep/lathe_easystep.ui`, die Logik im Handler `lathe_easystep_handler.py`. Beim Start von `qtdragon_lathe` wird das Makro geladen und erscheint im „Macros“-Tab der Host-GUI. Screenshots und UI-Layouts findest du unter `macros/LatheEasyStep/doc/Bilder/`.

## Sprache wechseln

Die Sprache stellst du oben links im Programm-Tab über **Sprache** ein:
- Standard: **Deutsch**
- Auf **English** umstellen übersetzt Labels, Combo-Einträge, Buttons und Tab-Titel (auch im eingebetteten Panel).
- QtVCP speichert die Auswahl in `~/.config/QtVcp/qtdragon_lathe.conf`, sodass die Einstellung beim nächsten Start erhalten bleibt.
- Es gibt kein separates INI-Flag; einmal ändern, beim nächsten Start ist die Wahl gesetzt.

## Referenzen

- Aktueller Funktionsumfang, Felder und G-Code-Erzeugung: `macros/LatheEasyStep/doc/milestone1_spec.md`
- Gilt für LinuxCNC 2.10 mit dem QtDragon-Panel `qtdragon_lathe`
- Screenshots: `macros/LatheEasyStep/doc/Bilder/`

---

# LatheEasyStep – Quick Guide (English)

LatheEasyStep is a QtVCP macro embedded in the QtDragon panel under **Macros → LatheEasyStep**. It replaces manual G-code entry with a step-by-step form: each operation (Facing, Contour, Parting, Thread, Groove/Parting, Drilling, Keyway) has its own tab for tool, spindle, feed, and coolant settings. The step list is on the left, a parameter summary with 2D preview on the right, and optionally the generated G-code at the bottom.

## What you can do

1. Define stock in the Program tab: unit, stock shape, tool-change offsets, retract planes, safety margins, language (German or English), and spindle limits.
2. Add or remove worksteps and reorder them with the arrow buttons.
3. Fill each tab’s parameters (tool number, spindle RPM, feed, coolant, reduced feed zones, chip-breaking and thread presets, cutting width, and more).
4. Review the preview; **G-Code erzeugen** writes `~/linuxcnc/nc_files/lathe_easystep.ngc`, opens it, and annotates tool changes, coolant, and reduced-speed zones.

## GUI integration

The UI is defined in `macros/LatheEasyStep/lathe_easystep.ui`; the handler logic lives in `lathe_easystep_handler.py`. When `qtdragon_lathe` starts, the macro loads into the host GUI’s “Macros” tab. Screenshots and UI layouts are available at `macros/LatheEasyStep/doc/Bilder/`.

## Language switch

Select the language from the Program tab’s **Sprache** combo (top-left):
- Default: **Deutsch**
- Choose **English** to translate labels, combo entries, buttons, and tab titles (including in the embedded panel).
- QtVCP stores the choice in `~/.config/QtVcp/qtdragon_lathe.conf`, so it persists across restarts.
- There is no extra INI flag; set it once and the next session keeps the language.

## References

- Current feature set, fields, and G-code generation: `macros/LatheEasyStep/doc/milestone1_spec.md`
- Targets LinuxCNC 2.10 with the QtDragon `qtdragon_lathe` panel
- UI screenshots: `macros/LatheEasyStep/doc/Bilder/`

## Änderungen & Nutzungshinweise (2025-12-16)

### Wichtige Code-Änderungen
- Entferntes Duplikat: Es gab zwei Varianten zur Behandlung von Vorschub-Unterbrechungen in Segmenten; es bleibt nur die kompakte Variante mit O-Word-Aufrufen (`o<step_x_pause>` / `o<step_line_pause>`). Dadurch bleibt der generierte G-Code schlank (keine Aufblähung durch viele `G1`/`G4`-Schleifen).
- Sicherheit: Bei `Abspanen` werden Vorschub-Unterbrechungen (Pause) jetzt **nur** erlaubt, wenn der Modus auf **Schruppen** steht. Selbst wenn UI oder Parameter fälschlich Pausen aktivieren, werden Pausen für Schlichten unterdrückt.
- Header-Optimierung: Die O-Subs (`o<step_x_pause>`, `o<step_line_pause>`) werden nur in den Programm-Header eingefügt, wenn mindestens eine Operation sie tatsächlich braucht (Modus & Pause aktiviert & Pause-Abstand > 0). Dadurch entstehen keine unnötigen Subroutinen im Header.

### Kurze Anleitung: Abspanen & Vorschub-Unterbrechung
- Mode wählen: Im Tab **Abspanen** die Strategie auf **Schruppen** stellen, falls du die Vorschub-Unterbrechung benötigst. Bei **Schlichten** sind die Pause-Optionen ausgeblendet und werden ignoriert.
- Pause aktivieren: Hake *Pause aktivieren* an und setze **Pause-Abstand** (mm). Wenn ein Segment länger als der Abstand ist, wird an passenden Stellen `o<step_line_pause> call ...` aufgerufen.
- Verhalten im G-Code: Bei Bedarf wird im Header die Subroutine `o<step_line_pause>` angelegt und `o<step_line_pause> call ...` im Pass-Body aufgerufen. Ist keine Operation mit Pause vorhanden, wird die Subroutine nicht erzeugt.

### Neuerungen (Slicing & UI) — Kurz
- Slicing-Strategien: Zusätzlich zu **Parallel X** gibt es jetzt **Parallel Z** (horizontaler Band-Slicing). Diese Strategien sind in **Abspanen → Slicing Strategy** auswählbar (Optionen: None, Parallel X, Parallel Z).
- Slicing‑Parameter: `Slicing Step` (mm) bestimmt die Bandbreite; `Allow Undercut` erlaubt/verbietet Pässe, die über die Kontur hinausgehen. Wenn **Allow Undercut** deaktiviert ist, überspringt der Slicer Pässe, die nicht erreichbar oder deutlich außerhalb der Kontur wären.
- Pausen & Sicherheit: Vorschub‑Unterbrechungen bleiben weiterhin **auf Schruppen beschränkt**; beim Schlichten werden sie unterdrückt und die Pause‑Widgets ausgeblendet.
- Tooltips & Lokalisierung: Die neuen UI‑Tooltips und What'sThis‑Texte sind in `lathe_easystep.ui` als englische Quelltexte hinterlegt (für Qt‑Linguist) und werden zur Laufzeit in DE/EN gesetzt. Dadurch sind Designer-Extrakt und Laufzeit‑Lokalisierung konsistent.
- G-Code-Header: O‑Subs (`o<step_x_pause>`, `o<step_line_pause>`) werden nur eingefügt, wenn mindestens ein Arbeitsschritt sie tatsächlich benötigt (reduziert unnötige Subs).
- Tests: Neue Unit‑Tests wurden hinzugefügt: `tests/test_parting_slice.py`, `tests/test_parting_tooltips.py`, `tests/test_parting_visibility.py`, `tests/test_slicer_extra.py`.
- Datum & Hinweis: Änderungen vorgenommen am 2025-12-16; siehe die Tests für Beispiele der erwarteten G‑Code-Ausgabe.

Beispiel (Kurz) — Abspanen mit Parallel X und Pause:
```gcode
G0 X0.000 Z2.000
o<step_line_pause> call [0.000] [-0.200] [0.000] [0.000] [0.100] [0.150] [0.500]
```

Entwickler‑Hinweis — Refactor (2025-12-16) 🔧
- Ziel: Trennung von UI/Handler und CAM‑Logik zur besseren Testbarkeit, Debugging und Wiederverwendbarkeit.
- Neues Modul: `slicer.py` enthält die Abspanen-/Slicing‑Logik and CAM‑Hilfsfunktionen.
- Wichtige API:
  - `generate_abspanen_gcode(p: Dict[str,object], path: List[(x,z)], settings: Dict[str,object]) -> List[str]` — Hauptfunktion zur Generierung des G‑Codes für `OpType.ABSPANEN`.
  - `rough_turn_parallel_x(...)`, `rough_turn_parallel_z(...)` — Kerndateien für Band‑Weises Schruppen.
  - Hilfsfunktionen: `gcode_from_path`, `_abspanen_safe_z`, `_offset_abspanen_path`, `_abspanen_offsets`, `_emit_segment_with_pauses`, `_gcode_for_abspanen_pass`, `_contour_retract_positions`.
- Verwendung: `lathe_easystep_handler.py` delegiert jetzt an `slicer.generate_abspanen_gcode(op.params, op.path, settings)`; Wrapper mit Fallbacks bleiben vorhanden.
- Tests: Unit‑Tests für Slicer und Pause/Visibility befinden sich in `tests/` (mit `pytest` ausführen).

Example (Developer note) — Refactor (2025-12-16) 🔧
- Goal: separate UI/handler and CAM logic for better testability, debugging and reusability.
- New module: `slicer.py` contains parting/slicing logic and CAM helper functions.
- Key API:
  - `generate_abspanen_gcode(p: Dict[str,object], path: List[(x,z)], settings: Dict[str,object]) -> List[str]` — main generator used by `OpType.ABSPANEN`.
  - `rough_turn_parallel_x(...)`, `rough_turn_parallel_z(...)` — core band-wise roughing routines.
  - Helpers: `gcode_from_path`, `_abspanen_safe_z`, `_offset_abspanen_path`, `_abspanen_offsets`, `_emit_segment_with_pauses`, `_gcode_for_abspanen_pass`, `_contour_retract_positions`.
- Usage: `lathe_easystep_handler.py` now delegates to `slicer.generate_abspanen_gcode(op.params, op.path, settings)`; thin wrappers with fallbacks remain.
- Tests: Unit tests for the slicer and pause/visibility logic live in `tests/` (run with `pytest`).


### Kurze Anleitung: Gewindeschneiden
- Presets: Das Dropdown `Standardgewinde` enthält metrische und TR-Profile. Bei Auswahl werden Steigung & Nenndurchmesser gesetzt; weitere Werte (Zustellungen, Peak-Offset, Zustellwinkel, Retract usw.) werden sinnvoll vorbelegt, aber **nur** wenn die entsprechenden Felder zuvor leer (0) waren — so werden Benutzerwerte nicht überschrieben.
- Preset übernehmen: Der Button **Preset übernehmen** erzwingt das Überschreiben aller Gewinde-Parameter mit den Preset-Werten, falls du schnell auf sichere Standardwerte wechseln willst.
- Empfehlung: Für das erste Testgewinde genügt oft Steigung und Durchmesser; lasse die voreingestellten Tiefe/Zustellung zu Beginn unverändert und prüfe per Vorschau oder Simulation.

---

## Changes & Usage Notes (2025-12-16)

### Key code changes
- Duplicate removed: Previously there were two approaches to handling feed pauses in segments; only the compact O-word approach remains (`o<step_x_pause>` / `o<step_line_pause>`). This keeps generated G-code compact and avoids inflation by many `G1`/`G4` loops.
- Safety: For `Parting` (Abspanen) feed pauses are now **only** allowed when the MODE is set to **Rough**. If the UI/params mistakenly enable pauses, pauses for Finish are suppressed.
- Header optimization: The O-subs (`o<step_x_pause>`, `o<step_line_pause>`) are now included in the program header only when at least one operation actually needs them (mode + pause enabled + pause_distance > 0). This prevents unnecessary subs in the header.

### Quick guide: Parting & feed interruption
- Mode selection: In the **Parting** tab choose **Rough** when you want feed interruption; **Finish** hides and ignores pause options.
- Enable pause: Tick *Pause enabled* and set **Pause distance** (mm). If a segment is longer than the distance, `o<step_line_pause> call ...` will be used.
- G-code behavior: When needed the header gets `o<step_line_pause>` sub and calls `o<step_line_pause> call ...` in the pass body. If no operation uses pauses the sub is omitted.

### New (Slicing & UI) — Short
- Slicing strategies: In addition to **Parallel X**, there is now **Parallel Z** (horizontal band slicing). Select the strategy in **Parting → Slicing Strategy** (options: None, Parallel X, Parallel Z).
- Slicing parameters: `Slicing Step` (mm) controls the band thickness; `Allow Undercut` permits or forbids passes that extend beyond the contour. When **Allow Undercut** is disabled, the slicer skips passes that would clearly cut outside the contour.
- Pauses & safety: Feed interruptions remain restricted to **Rough**; they are suppressed during Finish and the pause widgets are hidden.
- Tooltips & localization: The new UI tooltips and What'sThis texts are stored as English source strings in `lathe_easystep.ui` (for Qt‑Linguist) and are set at runtime for DE/EN, ensuring consistent designer extraction and runtime localization.
- G-code header: O-subs (`o<step_x_pause>`, `o<step_line_pause>`) are only injected if at least one step actually needs them.
- Tests: New unit tests included: `tests/test_parting_slice.py`, `tests/test_parting_tooltips.py`, `tests/test_parting_visibility.py`, `tests/test_slicer_extra.py`.
- Date & note: Changes made on 2025-12-16; see tests for example expected outputs.

Example (Short) — Parting with Parallel X and pause:
```gcode
G0 X0.000 Z2.000
o<step_line_pause> call [0.000] [-0.200] [0.000] [0.000] [0.100] [0.150] [0.500]
```


### Quick guide: Thread cutting
- Presets: The `Standard thread` dropdown contains metric and TR profiles. Selecting a preset sets pitch & nominal diameter; additional parameters (depths, first cut, peak offset, infeed angle, retract, etc.) are **pre-filled** but only when the fields were previously empty (0), so user values are preserved.
- Force apply: Use the **Apply preset** button to overwrite *all* thread parameter fields with the preset defaults.
- Recommendation: For first tests, set pitch & diameter and keep machine parameters conservative; verify preview/simulation before actual cut.

---
---
