# LatheEasyStep – kurzes Handbuch

LatheEasyStep ist ein QtVCP-Makro, das im QtDragon-Panel unter **Macros→LatheEasyStep** eingebettet wird. Es ersetzt das direkte G-Code-Tippen durch eine Schritt-für-Schritt-Maske, in der jeder Arbeitsschritt (Planen/Facing, Kontur/Contour, Abspanen/Parting, Gewinde/Thread, Einstich/Abstich, Bohren/Drilling, Keilnut/Keyway) seinen eigenen Tab mit Werkzeug-, Spindel-, Vorschub- und Kühlparametern hat. Links befindet sich die Liste der Schritte, rechts die Parameterübersicht mit der 2D-Vorschau; optional wird unten der generierte G-Code angezeigt.

## What this does

1. Rohteil definieren (Programmtab): Einheit, Rohteilform, Werkzeugwechsel, Rückzugsebenen, Sicherheitsabstände, Sprache (Deutsch oder English) und Spindelgrenzen.
2. Schritte bearbeiten: „Schritt hinzufügen“ erstellt einen neuen Workstep, „Schritt löschen“ entfernt ihn. Pfeile verschieben die Schritte in der Liste.
3. Tab-spezifische Parameter ausfüllen (Werkzeugnummer, Drehzahl, Vorschub, Kühlung, reduzierte Zonen, Spanbruch-Modi, Gewindestandards oder Schneidenbreiten).
4. Vorschau prüfen; „G-Code erzeugen“ schreibt `~/linuxcnc/nc_files/lathe_easystep.ngc`, öffnet die Datei und ergänzt Kommentare für Toolwechsel, Kühlung und reduzierte Bereiche.

## What you can do

1. Define the stock in the Program tab – unit, stock shape, tool-change offsets, retract planes, safety margins, language (Deutsch or English), and spindle limits.
2. Add and remove worksteps, and reorder them with the arrow buttons.
3. Fill the relevant parameters in each tab (tool number, spindle RPM, feed, coolant, reduced feed zones, chip-breaking and thread presets, cutting width).
4. Review the preview; “G-Code erzeugen” writes `~/linuxcnc/nc_files/lathe_easystep.ngc`, opens it, and annotates tool changes, coolant, and slow-down zones.

## Einbindung in die GUI

LatheEasyStep definiert die UI in `macros/LatheEasyStep/lathe_easystep.ui` und die Logik im Handler `lathe_easystep_handler.py`. Beim Start von `qtdragon_lathe` wird das Makro geladen und landet im „Macros“-Tab der Host-GUI. Screenshots und UI-Layouts findest du unter `macros/LatheEasyStep/doc/Bilder/`.

## GUI integration

The UI lives in `macros/LatheEasyStep/lathe_easystep.ui` and the handler logic in `lathe_easystep_handler.py`. When `qtdragon_lathe` starts, the macro is embedded into the host GUI’s “Macros” tab. See `macros/LatheEasyStep/doc/Bilder/` for screenshots of the layout.

## Sprache wechseln

Die Sprache wählst du oben links im Programm-Tab unter **Sprache**.  
 - Standard: **Deutsch**  
 - Auf **English** umstellen: Labels, Combos, Buttons und Tab-Titel (auch wenn das Panel eingebettet läuft) werden übersetzt.  
 - QtVCP speichert die Auswahl in den Preferences (`~/.config/QtVcp/qtdragon_lathe.conf`), sodass die Einstellung beim nächsten Start automatisch erhalten bleibt.  
 - Es gibt kein separates INI-Flag; wähle einmal im Dialog und die Einstellung bleibt erhalten.

## Language switch

Set the language at the Program tab’s **Sprache** combo (top-left):  
 - Default: **Deutsch**  
 - Select **English** to translate labels, combo entries, buttons, and tab titles (even within the embedded panel).  
 - QtVCP remembers the choice in `~/.config/QtVcp/qtdragon_lathe.conf`, so the preference survives restarts.  
 - There is no extra INI flag; change it once and the next session keeps the language.

## Referenzen

- Aktueller Funktionsumfang, Felder und G-Code-Erzeugung: `macros/LatheEasyStep/doc/milestone1_spec.md`  
- Gilt für LinuxCNC 2.10 mit QtDragon `qtdragon_lathe`-Panel  
- Screenshots: `macros/LatheEasyStep/doc/Bilder/`

## References

- Current feature set, fields, and G-code generation: `macros/LatheEasyStep/doc/milestone1_spec.md`  
- Targets LinuxCNC 2.10 with the QtDragon `qtdragon_lathe` panel  
- UI screenshots: `macros/LatheEasyStep/doc/Bilder/`

---
