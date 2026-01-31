# Implementation Plan: NGC Generator Refactoring (ohne Variablen)

## Anforderungen zusammengefasst

### 1. **Programmkopf mit Sicherheits-Kommentaren**
   - Werkzeugwechselpunkt (XT/ZT in Maschinenkoordinaten)
   - Rückzugsebenen (XRA/XRI/ZRA/ZRI mit Werten)
   - Sicherheitsabstand SC (Zahlenwert)
   - Rohteil-Daten (Ø, Z-Bezug)
   - Aufmaß (Schruppen/Schlichten)
   - **NUR KOMMENTARE** - keine G-Code-Logik

### 2. **Werkzeugwechsel intelligent**
   - Nur am Anfang, bei Wechsel, am Ende
   - Step-zu-Step vergleich: `tool gleich → kein T.. M6`
   - Nur anfahren + M6 wenn Werkzeug wechselt

### 3. **Anfahren vor Bearbeitung (explizit mit Zahlen)**
   - G0 Z<Z_RUECKZUG> (Eilgang ins sichere Z)
   - G0 X<X_SICHER> Z<Z_SICHER> (Sicherheitsposition)
   - F<FEED> (Vorschub setzen)
   - Dann Zyklus (G71/G72/G81/etc.)
   - **Keine Variablen** - nur konkrete Zahlen

### 4. **Abfahren nach Bearbeitung (intelligent)**
   - Nach Zyklus: zurück zum Sicherheitsabstand
   - Zur Rückzugsebene + Werkzeugwechselpunkt NUR wenn:
     - Werkzeugwechsel folgt, ODER
     - Programm endet
   - Zwischen Steps mit gleichem Werkzeug: im Sicherheitsbereich bleiben

### 5. **Kontur-Nullpunkt genau wie eingegeben**
   - Kontur = Geometrie (keine pauschal Annahmen)
   - Rohteil + Sicherheit bestimmen Annäherung
   - Nicht aus erstem Konturpunkt ableiten

### 6. **Vollständige Modals vor G71/G72**
   - T.. M6 (wenn Tool nötig)
   - S... M3 (Spindel + Richtung)
   - F... (Vorschub)
   - M8 (Kühlung, falls gewünscht)
   - **Alle mit konkreten Zahlen**

### 7. **Subroutine sauber**
   - Keine doppelten Punkte ✓ (bereits implementiert)

---

## Änderungen in slicer.py

### Change 1: Programmkopf mit Sicherheits-Kommentaren

**Location**: `generate_program_gcode()`, nach header_lines

**Code**:
```python
# --- Security header comments ---
header_lines.append("")
header_lines.append("(=== SICHERHEITSPARAMETER ===)")

# Werkzeugwechselpunkt
xt = settings.get("xt")
zt = settings.get("zt")
xt_abs = settings.get("xt_absolute", True)
zt_abs = settings.get("zt_absolute", True)
if xt is not None and zt is not None:
    coord_note = ""
    if not xt_abs or not zt_abs:
        coord_note = " (Maschinenkoordinaten G53)"
    header_lines.append(f"(Werkzeugwechselpunkt: X{float(xt):.3f} Z{float(zt):.3f}{coord_note})")

# Rückzugsebenen
xra = settings.get("xra")
xri = settings.get("xri")
zra = settings.get("zra")
zri = settings.get("zri")
if xra is not None or xri is not None:
    header_lines.append(f"(Rückzugsebenen: XRA={xra if xra else 'n.def.'} XRI={xri if xri else 'n.def.'})")
if zra is not None or zri is not None:
    header_lines.append(f"(                ZRA={zra if zra else 'n.def.'} ZRI={zri if zri else 'n.def.'})")

# Stock info
xa = settings.get("xa")
xi = settings.get("xi")
za = settings.get("za")
zi = settings.get("zi")
if xa is not None:
    header_lines.append(f"(Rohteil Außendurchmesser: {float(xa):.3f} mm)")
if zi is not None:
    header_lines.append(f"(Rohteil Z-Bereich: {float(za):.3f} bis {float(zi):.3f} mm)")

header_lines.append("(=== END SICHERHEITSPARAMETER ===)")
header_lines.append("")
```

### Change 2: Tool tracking für intelligente Werkzeugwechsel

**Location**: `generate_program_gcode()`, operations loop

Vor operations loop:
```python
last_tool: int = 0  # Track last tool used
```

Im operations loop (vor step comment):
```python
current_tool = int(op.params.get("tool", 0)) if op.op_type != OpType.PROGRAM_HEADER else 0

if current_tool > 0 and current_tool != last_tool:
    # Tool hat gewechselt → M6 und Anfahren erlaubt
    emit_toolchange_if_needed = True
else:
    # Gleiches Werkzeug → M6 und Anfahren unterdrücken
    emit_toolchange_if_needed = False

last_tool = current_tool
```

### Change 3: Explizite Anfahrbewegungen (nur mit Zahlen)

**Location**: Vor G71/G72/G81/etc. in den Generatoren

**Muster**:
```python
# Vor G71/G72:
safe_z = <konkrete Zahl aus Rückzug>
safe_x = <konkrete Zahl aus Rohteil/Rückzug>
lines.append(f"G0 Z{safe_z:.3f}")  # Erst Z (sicheres Z)
lines.append(f"G0 X{safe_x:.3f} Z{safe_z:.3f}")  # Dann X+Z
lines.append(f"F{feed:.3f}")  # Vorschub
lines.append("G71 ...")  # Zyklus
```

### Change 4: Intelligentes Abfahren

**Location**: Nach Zyklus-Aufrufen

**Logik**:
```python
# Nach Zyklus:
if next_op_tool_differs or is_last_operation:
    # Werkzeugwechsel folgt oder Ende → zurück zu Rückzugsebene + WT-Punkt
    lines.append(f"G0 Z{rückzug_z:.3f}")
    lines.append(f"G0 X{rückzug_x:.3f}")
else:
    # Gleich Werkzeug folgt → nur zur Sicherheitsposition
    lines.append(f"G0 Z{sicher_z:.3f}")
    lines.append(f"G0 X{sicher_x:.3f} Z{sicher_z:.3f}")
```

### Change 5: Kontur genau wie eingegeben

**Location**: Alle Generatoren (CONTOUR, ABSPANEN, FACE)

**Regel**:
- Kontur-Punkte: SO ausgeben, WIE sie eingegeben wurden
- Keine pauschal Anpassung des Start-Punkts
- Rohteil + Rückzug → separate Anfahrbewegung

**Beispiel**:
```python
# FALSCH (alte Logik):
contour_start = path[0]  # Annahme: X0/Z0?
path_adjusted = adjust_to_stock(path)

# RICHTIG (neue Logik):
contour = path  # Wie eingegeben
stock_x = settings.get("xa")  # Rohteil
retract_x = settings.get("xra")  # Rückzug
# Anfahren SEPARAT mit stock_x/retract_x, nicht mit path[0]
```

### Change 6: Vollständige Modals vor Zyklus

**Location**: In jedem Zyklus-Generator (FACE, ABSPANEN, etc.)

**Reihenfolge**:
1. Tool (T.. M6) - wenn nötig
2. Spindle (S... M3)
3. Coolant (M8) - falls enabled
4. Feed (F...)
5. Dann erst Zyklus

```python
if tool_num > 0:
    lines.append(f"T{tool_num:02d} M6")
if spindle > 0:
    lines.append(f"S{spindle:.0f} M3")
if coolant:
    lines.append("M8")
lines.append(f"F{feed:.3f}")
# DANN Zyklus
lines.append("G71 ...")
```

---

## Implementierungsstrategie

1. **Phase 1**: Programmkopf mit Sicherheits-Kommentaren
2. **Phase 2**: Tool tracking + intelligente Werkzeugwechsel
3. **Phase 3**: Explizite Anfahrbewegungen refaktorieren
4. **Phase 4**: Intelligentes Abfahren
5. **Phase 5**: Kontur-Logik prüfen und ggf. anpassen
6. **Phase 6**: Modal-Vorbereitung prüfen und standardisieren
7. **Phase 7**: Tests + Validierung

---

## Status

- [ ] Phase 1: Programmkopf
- [ ] Phase 2: Tool Tracking
- [ ] Phase 3: Anfahren
- [ ] Phase 4: Abfahren
- [ ] Phase 5: Kontur
- [ ] Phase 6: Modals
- [ ] Phase 7: Tests
