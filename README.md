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

---
