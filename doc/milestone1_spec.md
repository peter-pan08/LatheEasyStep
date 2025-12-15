# LatheEasyStep – Milestone 1 Spezifikation
## Umfang

Milestone 1 deckt den aktuellen Stand des LatheEasyStep-Makros ab:

- **Programm-Reiter** mit Sprache (Deutsch/English), Rohteilparametern, Einheitenwahl, Rückzugsebene, Werkzeugwechselabständen und Spindelgrenzen sowie Tool- und Kühllogik.
- **Operationen** über eigene Tabs: Planen (Facing), Kontur (Contour), Abspanen (Parting), Gewinde (Thread), Einstich/Abstich (Groove/Parting), Bohren (Drilling) und Keilnut (Keyway). Jeder Tab bietet Werkzeug-, Spindel-, Vorschub- und Kühlungsfelder plus spezielle Optionen (Thread-Standards, reduzierte Zonen, Spanbruchmodi, Schneidenbreiten, Tool-Nummer, etc.).
- **2D-Vorschau** im X–Z-Schnitt mit synchronisierter Operationsliste.
- **G-Code-Erstellung** nach LinuxCNC-Standards inkl. Kommentare, Kühlung, reduzierter Vorschubbereich und Werkzeughandhabung; Datei `~/linuxcnc/nc_files/lathe_easystep.ngc` wird aktualisiert.
- **Mehrsprachigkeit**: Tab-Titel, Labels, Combos und Buttons wechseln beim Sprachschalter auf dem Programm-Reiter (Deutsch ist Default, Englisch schaltet alle Texte um). Die Tab-Überschriften folgen auch im eingebetteten QtDragon-Panel (Program / Facing / ...).

---

## 2. Koordinaten- und Zeichenkonventionen

- Koordinatensystem: LinuxCNC-Standard für Drehbank (G18). X bezeichnet Durchmesser, Z die Laufachse.
- Vorzeichen: Tiefe Z-Werte werden im Handler automatisch negativ gesetzt, die Anwender geben positive Werte ein (z. B. „Tiefe 2 mm“ bedeutet `Z-2`).
- Einheitenswitch: `Program.Unit = mm` → `G21`, `Program.Unit = inch` → `G20`.
- Sicherheitsposition: `safe_z` pro Operation (Standard +2,0 mm vor der Materialoberfläche).
- Vorschub: mm/U bzw. mm/U bei Drehoperationen, linearer Vorschub bei Kontur.

---

## 3. Programm-Reiter (Programm-Parameter)

| Feld | Beschreibung |
| --- | --- |
| Sprache | Combo `program_language` (Deutsch/English), beeinflusst alle Labels, Tab-Titel und Combo-Einträge. |
| Programmname | Freies Textfeld `program_name` für Kommentare im G-Code. |
| Maßeinheit | `program_unit` (mm / inch) steuert G20/G21 und Suffixe der Spinboxen. |
| Rohteilform | `program_shape` (Zylinder, Rohr, Rechteck, N-Eck) – aktuell informativ, später für Plausibilitätschecks. |
| XA / XI / L | Rohteilmaße für Kommentare (Außendurchmesser, Innendurchmesser, Länge). |
| Rückzug | `program_retract_mode` (einfach/erweitert/alle) mit separaten Ebenen für X/Z, Werkzeugwechsel > `program_xt`, `program_zt`. |
| Sicherheit | `program_sc`, `program_s1`, `program_s3` zur Kontrolle von Sicherheitsabstand und Drehzahlgrenzen. |
| Werkzeugmanagement | `program_xt`/`program_zt` steuern Werkzeugwechsel, `program_has_subspindle` aktiviert Gegenspindel-Optionen. |

Alle Werte landen in `ProgramModel.program_settings` und werden im Header sowie bei G-Code-Generierung genutzt.

---

## 4. Planen (Face)

- Felder: Werkzeug, Spindel, Kühlung, Vorschub, Finish-Richtung, Finish-Übermaß (X/Z), Kantenform/-größe, Pause mit Distanz.
- G-Code: `G0 X{start} Z{safe_z}`, dann `G1` zu Ziel, ggf. Finish-Z.
- Spindel- und Werkzeugnummer müssen immer angegeben werden, sonst wird der Schritt übersprungen.
- Kühlungswahl („Aus“/„Ein“) dokumentiert den Zustand mit Kommentar.

## 5. Kontur (Contour)

- Unterstützt Start-/Endpunkte, Koordinatenmodus und Auswahl gespeicherter Konturen.
- Kontursegments-Buttons (`Segment +`, `Segment -`, Verschieben) bleiben aktiv, Tab-Titel übersetzt.
- Vorschub und Sicherheitsz definieren, ob die Zufuhr auf `safe_z` zurückgeht.

## 6. Abspanen (Parting)

- Felder: Werkzeug, Spindel, Kühlung, Vorschub, Tiefe pro Pass, Strategie (Schruppen/Schlichten), Konturwahl, Pause.
- Kühlung per Combo – wirkt sich auf generierten G-Code aus (`(Coolant On/Off)`).
- Pause-Checkbox mit Distanz unterbricht den Vorschub an definiertem Abstand.

## 7. Gewinde (Thread)

- Werkzeug, Spindel, Kühlung, Gewindetyp (Innen/Außen), Standardgewinde-Liste (M2 … M25), Major-Durchmesser, Steigung, Gewindelänge, Passanzahl, Sicherheits-Z.
- Standardgewinde füllen Major/Pitch automatisch, man kann eigene Werte eingeben.
- G-Code nutzt Tool-/Spindle-Zuordnung und generiert passende Comments.

## 8. Einstich/Abstich (Groove/Parting)

- Felder: Werkzeug, Spindel, Kühlung, Durchmesser, Breite, Schneidenbreite, Tiefe, Z-Position, Vorschub, Sicherheits-Z.
- Abstech-Optionen: `reduced_feed_start_x`, `reduced_feed`, `reduced_rpm` definieren eine Zone mit reduzierter Drehzahl/Vorschub ab einer `X`-Position.
- Schneidenbreite ist erforderlich für präzise Werkzeugwege.
- G-Code: Wechselt ab der Schwellenposition automatisch die Vorschub-/Drehzahlangaben, kommentiert den reduzierten Abschnitt.

## 9. Bohren (Drilling)

- Felder: Werkzeugnummer, Spindel, Kühlung, Modus (Normal / Spanbruch / Spanbruch + Rückzug), Bohrdurchmesser, Tiefe, Vorschub, Sicherheits-Z.
- Modus `Normal` generiert `G81`; die Spanbruch-Modi erzeugen `G83` mit `Q`-Wert und optionalem Rückzug zwischen den Einstichen (`retract`).
- Die Kombos für Kühlung und Modus sind übersetzt und werden beim Sprachwechsel angepasst.

## 10. Keilnut (Keyway)

- Felder: Modus (Axial/Face), Radialseite, Kühlung, Anzahl, Startwinkel, Startdurchmesser/Z, Nutlänge/Tiefe, Schneidenbreite, Kopffreiheit, Zustellung/Passe.
- Kühlungsoption analog zu anderen Tabs, Schneidenbreite wichtig für Wegberechnung und G-Code-Korrektheit.
- Die generierte Routine nutzt definierte Hilfsvariablen (`#<_nut_length>` etc.) und setzt Tool-/Spindelkommandos.

---

## 11. G-Code-Generierung

- Datei `~/linuxcnc/nc_files/lathe_easystep.ngc` wird bei jedem Generieren neu geschrieben und anschließend mit `Action.CALLBACK_OPEN_PROGRAM` geöffnet.
- Standardheader: `(LatheEasyStep – auto generated)`, `(Program: ...)`, `(Stock: ...)`, `G18 G90 G40 G80`, `G54`, `G20`/`G21` je nach Einheit.
- Toolwechsel: `Tnn M6`, gefolgt von `Snn M3` bei gesetzter Spindelzahl. Kommentare dokumentieren Kühlung, Translationsmodus und reduzierte Bereiche.
- Bohren: `G81` oder `G83`, Rückzug auf `safe_z` mit `G0`, Abschluss `G80`.
- Grooves/Parting: G1 in X/Z, bei reduzierter Zone wird `F`/`S` angepasst und kommentiert.
- Gewinde und Kontur: `G0` zum Start, dann `G1` mit feed, ggf. Modals.
- Coolant/Zufuhroptionen werden als Kommentare ergänzt (z. B. `(Coolant On)`), realer Befehl wie `M8/M9` kann später ergänzt.

---

## 12. Milestone-Checkliste

- [x] Panel startet ohne Python-Traceback und findet `tabParams` auch eingebettet in QtDragon.
- [x] Programm-Tab lässt sich öffnen, Spracheinstellung und Werte bleiben erhalten.
- [x] Jeder Operationstyp hat einen eigenen Tab mit obligatorischer Werkzeug-/Spindelwahl.
- [x] Planen/Kontur/Abspanen/Gewinde/Groove/Bohren/Keilnut erzeugen Vorschau-OPs und synchronisieren mit der Operationenliste.
- [x] G-Code wird erzeugt (Standardzyklen, Tool/Spindle, reduzierte Bereiche, Kommentare) und unter `~/linuxcnc/nc_files/lathe_easystep.ngc` geschrieben.
- [x] Sprachwechsel setzt Labels, Combo-Einträge, Buttons und Tab-Titel auf Englisch, inklusive der eingebetteten QtDragon-Tabs.
- [x] Thread-Tab bietet ISO-Standardgewinde und füllt Major/Pitch automatisch.
- [x] Groove-Tab verarbeitet reduzierte Drehzahlen/Vorschübe ab einer X-Grenze und erfordert Schneidenbreite.
- [x] Bohren-Tab deckt Normal-, Spanbruch- und Spanbruch+Rückzug-Modi mit `G81`/`G83` ab.
- [x] Keilnut-Tab bietet Axial/Face-Modi, Radialseite und Kühlung sowie Schneidenbreite, die im G-Code mit Variablen dokumentiert wird.

## English summary

- Panel and tabs are embedded inside the QtDragon macros tab and locate `tabParams` even when nested.
- Program tab preserves language, units, stock metadata, tool change offsets, and spindle limits between sessions.
- Every workstep gets its own tab (Facing, Contour, Parting, Thread, Groove/Parting, Drilling, Keyway) with mandatory tool+spindle settings.
- Path preview and operation list stay in sync for Face, Contour, Parting, Thread, Groove, Drilling, and Keyway.
- G-code output (`~/linuxcnc/nc_files/lathe_easystep.ngc`) uses standard cycles, documents coolant/reduced zones, and includes tool/spindle commands.
- Language switch translates labels, combos, buttons, and tab titles (embedded QtDragon included).
- Thread tab provides ISO metric standards, autopopulating major diameter and pitch.
- Groove tab supports reduced RPM/feed zones triggered by an X threshold and requires cutting width.
- Drill tab covers Normal, Chip-Break, and Chip-Break + Retract modes using `G81`/`G83`.
- Keyway tab supports axial/face modes, radial side selection, coolant, and cutting width exported into helper variables for the generated G-code.
