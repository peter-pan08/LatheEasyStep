# LatheEasyStep – Milestone 1 Spezifikation
## Umfang

Milestone 1 umfasst:

- Programm-Reiter:
  - Name des Programms
  - Maßeinheit (mm / inch)
  - Rohteilform (für später, aktuell rein informativ)
  - Basis-Rohteilmaße:
    - XA (Außendurchmesser)
    - XI (Innendurchmesser, nur bei Rohr relevant)
    - L (Länge in Z)
- Operationstypen:
  - Planen (FACE)
  - Längsdrehen (TURN)
- 2D-Vorschau im X–Z-Schnitt
- G-Code-Erzeugung in `~/linuxcnc/nc_files/lathe_easystep.ngc`

Keine Werkzeugtabellen, keine Vorschub/Schnittdaten-Automatik – das kommt später.

---

## 2. Koordinaten- und Zeichenkonventionen

- Koordinatensystem: LinuxCNC Standard für Drehbank
  - X: Durchmesserbezogen (G18, X = Durchmesser)
  - Z: Längsachse, Z=0 wird als Spannfutter-nahe Fläche angenommen
- Vorzeichen:
  - Minus-Z in Richtung Reitstock
  - Tiefen / Längen in Z werden im UI „positiv“ eingegeben, der Handler macht daraus negative Z-Werte.
- Einheiten:
  - `Program.Unit = mm` → G21
  - `Program.Unit = inch` → G20
- Sicherheitsposition:
  - `safe_z` pro Operation (Standard +2.0 mm)
  - Vorschubwerte sind mm/U (Drehbank-Stil).

---

## 3. Programm-Reiter (Programm-Parameter)

### Felder (Milestone 1)

| UI-Name          | interne Variable | Typ           | Einheit | Bemerkung                          |
|------------------|------------------|---------------|--------|------------------------------------|
| Programmname     | `program_name`   | Text          | –      | Nur Kommentar im G-Code           |
| Maßeinheit       | `program_unit`   | Combo (mm/inch) | –    | Steuert G20/G21                   |
| Rohteilform      | `program_shape`  | Combo         | –      | Informativ, später für Checks     |
| XA Außendurchm.  | `program_xa`     | DoubleSpinBox | mm/inch| Info, aktuell nur im Kommentar    |
| XI Innendurchm.  | `program_xi`     | DoubleSpinBox | mm/inch| Nur relevant bei „Rohr“           |
| Länge L          | `program_l`      | DoubleSpinBox | mm/inch| Info, später für Plausibilitätscheck |

Diese Felder landen gesammelt im `ProgramModel.program_settings` und werden beim G-Code-Header ausgegeben:

```gcode
(LatheEasyStep – auto generated)
(Program: Welle_01)
(Stock: XA=40.000 XI=0.000 L=80.000 mm)
G18 G90 G40 G80
G54
G21

4. Operation „Planen“ (FACE)
UI-Felder
Bezeichnung	interner Schlüssel	Einheit	Bedeutung
Startdurchmesser (X)	start_diameter	mm/inch	aktueller Außendurchmesser beim Zustellen
Ziel-Z	target_z	mm/inch	Endfläche nach Planen (i. d. R. 0.0)
Sicherheits-Z	safe_z	mm/inch	Position, auf der Werkzeug frei verfährt
Vorschub (mm/U)	feed	mm/U	Zustellvorschub
Geometrie-Pfad

(x_start, safe_z) -> (x_start, z_target) -> (0, z_target)


Beispiel-G-Code (vereinfacht)

( Operation 1: face )
G0 X50.000 Z2.000
G1 Z0.000 F0.200
G1 X0.000 Z0.000

5. Operation „Längsdrehen“ (TURN)
UI-Felder
Bezeichnung	interner Schlüssel	Einheit	Bedeutung
Startdurchmesser (X)	start_diameter	mm/inch	aktueller Durchmesser am Start
Enddurchmesser (X)	end_diameter	mm/inch	Ziel-Durchmesser am Ende der Kontur
Länge (Z)	length	mm/inch	axiale Bearbeitungslänge (positiv eingegeben)
Sicherheits-Z	safe_z	mm/inch	wie oben
Vorschub (mm/U)	feed	mm/U	wie oben
Geometrie-Pfad

(x_start, safe_z) -> (x_start, 0.0) -> (x_end, -|length|)

Beispiel-G-Code

( Operation 2: turn )
G0 X40.000 Z2.000
G1 Z0.000 F0.200
G1 X30.000 Z-20.000

6. G-Code-Datei und Integration

Dateiname: ~/linuxcnc/nc_files/lathe_easystep.ngc

Erzeugung:

vorhandene Datei wird überschrieben

nach dem Schreiben: Action.CALLBACK_OPEN_PROGRAM(path)

Kopf/Konstanten:

G18 G90 G40 G80

G54

G20 oder G21 je nach Einheit

Ende:

M9

M30

%

7. Milestone-Checkliste

Panel startet ohne Python-Traceback.

Programmreiter lässt sich öffnen, Werte bleiben in der Session erhalten.

„Planen“-Operation erzeugt sichtbare Kontur in der Vorschau.

„Längsdrehen“-Operation erzeugt sichtbare Kontur in der Vorschau.

Schritte können hinzugefügt, gelöscht und verschoben werden.

G-Code-Datei wird erzeugt und lässt sich in LinuxCNC öffnen.

Beispielteil mit 1× Planen + 1× Längsdrehen ergibt plausiblen G-Code.
