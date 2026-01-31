# 🔍 Compliance-Audit: 9 Verbindliche Regeln für Generator

**Datum**: 29. Januar 2026  
**Status**: AUDIT IN PROGRESS  
**Betroffen**: `slicer.py`, `lathe_easystep_handler.py`

---

## Regel 1: Werkzeugwechselpunkt (TC) - nur bei Bedarf anfahren

### ✅ Anforderung
- Am **Programmanfang** anfahren
- Bei **tatsächlichem Werkzeugwechsel** anfahren
- Am **Programmende** anfahren
- **NICHT** zwischen Steps mit gleichem Tool

### 📋 Audit-Punkte
| Punkt | Status | Evidenz | Aktion |
|-------|--------|---------|--------|
| TC am Anfang | ❓ | Nicht im Kopf vorhanden | Muss hinzufügen: `G53 G0 X<xt> Z<zt>` nach Header |
| TC bei Wechsel | ❓ | Logik existiert (lines 2130-2160) aber untested | Testen mit mehreren Tools |
| TC am Ende | ❓ | M5/M9 vorhanden, aber TC nicht | Muss hinzufügen vor M5 |
| Duplikate eliminieren | ⚠️ | Logic prüft `tool_changed` aber greift nur bei op_lines nicht leer | Muss auditen: redundante M6? |

### 🔧 Gefundene Probleme
1. **Fehler**: Header hat keine `G53 G0 X<xt> Z<zt>` am Anfang
2. **Fehler**: End-Position (vor M5/M9) nicht im Code
3. **Warnung**: Tool-Change-Logik (lines 2137-2147) möglicherweise noch nicht vollständig

### 📝 Fix erforderlich
- [ ] Füge `G53 G0 X<xt> Z<zt>` am Start des Programms ein (nach Header-Kommentaren)
- [ ] Füge `G53 G0 X<xt> Z<zt>` vor M5 am Ende ein
- [ ] Verifiziere tool_changed Logic hat keine Double-M6

---

## Regel 2: Keine Variablen, keine Verweise

### ✅ Anforderung
- **Keine** `#<...>` Variablen im Output
- **Nur** Zahlenwerte in jedem Satz
- Variablen dürfen **nur** in Zyklus-Parametern vorkommen (z.B. `D#<var>`)

### 📋 Audit-Punkte
| Punkt | Status | Evidenz | Aktion |
|-------|--------|---------|--------|
| Bewegungen nur mit Zahlen | ❓ | `G0 Z{z:.3f}` ja, aber Generator nutzt helper functions | Prüfen: emit_g0, gcode_from_path |
| Keine Variablen in G0/G1 | ✅ | emit_g0 nutzt float-Format | OK |
| Variablen nur in Zyklus-Parametern | ⚠️ | `D#<_depth_per_pass>` existiert | Das ist OK (innen im Zyklus) |
| Zyklus-Startpunkte mit Zahlen | ❓ | G71 hat `X{x} Z{z}` mit Zahlen | Prüfen: alle Zyklen |

### 🔧 Gefundene Probleme
1. **Warnung**: `generate_abspanen_gcode()` Zeile 1128 - hat `#<_depth_per_pass>` aber ist das OK? (Ja, wenn nur in G71 Parameter)
2. **Zu prüfen**: Andere Generatoren (DRILL, GROOVE, THREAD, KEYWAY)

### 📝 Fix erforderlich
- [ ] Grep-Suche: Alle `#<` in output .ngc checken (sollten 0 sein außer Parameter)
- [ ] Verifiziere: `gcode_from_path()` gibt nur Zahlen aus
- [ ] Verifiziere: Alle G0/G1 verwenden float-Werte

---

## Regel 3: Quelle der Wahrheit: Kontur wie eingegeben

### ✅ Anforderung
- Kontur wird **exakt** so übernommen wie eingegeben
- **Keine** automatischen Annahmen über X0/Z0
- **Keine** Anfahrts-Ableitung aus path[0]

### 📋 Audit-Punkte
| Punkt | Status | Evidenz | Aktion |
|-------|--------|---------|--------|
| Kontur-Punkte unverändert | ⚠️ | `gcode_for_contour()` gibt nur Kommentare, nicht Bewegungen | OK |
| path[0] wird nicht als Anfahrung genutzt | ⚠️ | `_contour_retract_positions()` nutzt `entry_x = max(xs)` nicht path[0] | OK |
| Keine pauschal Z-Adjustments | ⚠️ | ABSPANEN nutzt `path` direkt | Prüfen: rough_turn_parallel_* |

### 🔧 Gefundene Probleme
1. **Warnung**: `rough_turn_parallel_x()` möglicherweise mit falscher Logik? (Line 1195+)
2. **Zu prüfen**: Andere roughing-Funktionen

### 📝 Fix erforderlich
- [ ] Verifiziere: `rough_turn_parallel_x()` nutzt path[0] korrekt
- [ ] Verifiziere: `rough_turn_parallel_z()` nutzt path[0] korrekt
- [ ] Verifiziere: Keine versteckten path-Manipulationen

---

## Regel 4: Anfahren vor Bearbeitung (Z → X → Zyklus)

### ✅ Anforderung
1. Sicheres Z (Rückzugsebene)
2. Sicherer Durchmesser (X)
3. Bearbeitung beginnt
- **Alle** als echte `G0`-Sätze mit Zahlenwerten

### 📋 Audit-Punkte
| Punkt | Status | Evidenz | Aktion |
|-------|--------|---------|--------|
| Z zuerst | ⚠️ | `generate_abspanen_gcode()` fehlt explizite G0 Z | Muss hinzufügen |
| X danach | ⚠️ | `generate_abspanen_gcode()` fehlt explizite G0 X | Muss hinzufügen |
| Reihenfolge Z→X | ✅ | Wenn vorhanden, ist Reihenfolge korrekt | OK |
| Vorher: Feedrate | ⚠️ | F wird gesetzt, aber Position nicht gelaut Spec | Fraglich |

### 🔧 Gefundene Probleme
1. **KRITISCH**: `generate_abspanen_gcode()` hat **keine** expliziten G0 Z / G0 X vor Zyklus
2. **KRITISCH**: `gcode_for_face()` auch zu prüfen
3. **KRITISCH**: `gcode_for_drill()` auch zu prüfen

**Beispiel aus aktuellem Code**:
```python
# generate_abspanen_gcode() Zeile ~1150:
lines.append("(ABSPANEN)")
# ⚠️ FEHLER: Keine G0 Z hier!
# ⚠️ FEHLER: Keine G0 X hier!
lines.append(f"G71 Q101 X{x:.3f} Z{z:.3f} D{depth:.3f}")
```

**Soll sein**:
```
(ABSPANEN)
G0 Z2.000
G0 X42.000
F0.150
G71 Q101 X40.000 Z2.000 D1.000
```

### 📝 Fix erforderlich
- [ ] **DRINGEND**: Alle Generatoren (FACE, ABSPANEN, DRILL, GROOVE, THREAD, KEYWAY) müssen vor Zyklus explizit `G0 Z... G0 X...` ausgeben
- [ ] **DRINGEND**: Reihenfolge: Z zuerst, dann X
- [ ] **DRINGEND**: Nur Zahlenwerte, keine Variablen

---

## Regel 5: Rückzug nach Bearbeitung (X → Z, nicht Z → X)

### ✅ Anforderung
- Nach Zyklus (wenn kein Tool-Wechsel folgt):
  1. Zuerst **X** sicher vom Material
  2. Dann **Z** sicher zurück
- **Nicht umgekehrt!**

### 📋 Audit-Punkte
| Punkt | Status | Evidenz | Aktion |
|-------|--------|---------|--------|
| X zuerst | ⚠️ | Phase 5-4 Code (lines 2150-2160) nicht verifiziert | Testen |
| Z danach | ⚠️ | Phase 5-4 Code nicht verifiziert | Testen |
| Nur wenn nötig | ⚠️ | Logik existiert (next_tool_different prüfen) | Testen |

### 🔧 Gefundene Probleme
1. **Warnung**: Retract-Logik (lines 2160-2185) untested

### 📝 Fix erforderlich
- [ ] Test: Verifiziere Rückzug-Reihenfolge X→Z in NGCs
- [ ] Test: Verifiziere Rückzug nur wenn nötig

---

## Regel 6: Rückzugsebene vs. Sicherheitsabstand

### ✅ Anforderung
- Nach Zyklus: **Sicherheitsabstand** (kurz)
- Bei Wechsel / Ende: **Rückzugsebene** (volle Position)
- **Nicht** automatisch nach jedem Zyklus zur Rückzugsebene

### 📋 Audit-Punkte
| Punkt | Status | Evidenz | Aktion |
|-------|--------|---------|--------|
| Unterschied erkannt | ⚠️ | Phase 4 Code prüft next_tool_different | Testen |
| Kurz-Rückzug verwendet | ⚠️ | Logik existiert aber untested | Testen |
| Volle Position bei Wechsel | ⚠️ | Logik existiert aber untested | Testen |

### 📝 Fix erforderlich
- [ ] Test: Zwei Steps mit gleichem Tool → Check: kurzer Rückzug
- [ ] Test: zwei Steps mit verschiedenem Tool → Check: volle Rückzugsebene

---

## Regel 7: Vollständiger Modalzustand vor G71/G72

### ✅ Anforderung
Vor jedem Drehzyklus: `T.. M6` → `S... M3` → `M8?` → `F...` → dann `G71/G72`

### 📋 Audit-Punkte
| Punkt | Status | Evidenz | Aktion |
|-------|--------|---------|--------|
| FACE (gcode_for_face) | ✅ | Lines 1755-1758: T → S → M8? → F vor Zyklus | OK |
| ABSPANEN (generate_abspanen_gcode) | ⚠️ | Lines 1112-1133: T → S → M8? → F aber vor G71? Prüfen | Testen |
| DRILL (gcode_for_drill) | ❓ | Nicht überprüft | Muss checken |
| GROOVE (gcode_for_groove) | ❓ | Nicht überprüft | Muss checken |
| THREAD (gcode_for_thread) | ❓ | Nicht überprüft | Muss checken |
| KEYWAY (gcode_for_keyway) | ❓ | Nicht überprüft | Muss checken |

### 📝 Fix erforderlich
- [ ] Audit: DRILL, GROOVE, THREAD, KEYWAY - Modal-Reihenfolge vor Zyklus
- [ ] Verifiziere: Alle Generatoren folgen T→S→M8→F Muster

---

## Regel 8: Profil-Subroutinen (keine Duplikate)

### ✅ Anforderung
- Keine doppelten identischen Punkte
- Keine Nullbewegungen
- Sub beschreibt nur Geometrie, nicht Anfahren

### 📋 Audit-Punkte
| Punkt | Status | Evidenz | Aktion |
|-------|--------|---------|--------|
| Duplikate entfernt | ✅ | `gcode_from_path()` Line 1195+: dedup logic | OK |
| Nullbewegungen weg | ✅ | Dedup entfernt auch |x=x,z=z| | OK |
| Sub-Struktur sauber | ⚠️ | Nicht verifiziert in aktuellem Code | Test |

### 📝 Fix erforderlich
- [ ] Verifiziere: gcode_from_path() hat Duplikate entfernt
- [ ] Test: Subroutine in NGC hat keine `G1 X40.000 Z-10.000` gefolgt von `G1 X40.000 Z-10.000`

---

## Regel 9: Eilgangbewegungen (G0) bei Außen/Innendrehen

### ✅ Anforderung (KRITISCH & KOMPLEX)

**Außendrehen**:
- Material bei großem X
- G0 von X_groß → X_klein = INS MATERIAL ❌ (VERBOTEN)
- G0 von X_klein → X_groß = VOM MATERIAL WEG ✅ (OK)

**Innendrehen**:
- Material bei kleinem X
- G0 von X_klein → X_groß = INS MATERIAL ❌ (VERBOTEN)
- G0 von X_groß → X_klein = VOM MATERIAL WEG ✅ (OK)

### 📋 Audit-Punkte
| Punkt | Status | Evidenz | Aktion |
|-------|--------|---------|--------|
| Außen/Innen erkannt | ❓ | Code nutzt side_idx (0=Außen, 1=Innen) | OK |
| G0-Richtung validiert | ❌ | **NICHT** implementiert | CRITICAL: Muss hinzufügen |
| Sicherheit beim Anfahren | ❌ | Keine Prüfung | CRITICAL: Muss hinzufügen |
| Fallback zu G1 | ❌ | Nicht vorhanden | Fallback-Strategie nötig |

### 🔧 Gefundene Probleme
1. **KRITISCH**: `emit_g0()` und `rough_turn_parallel_*()` prüfen **nicht**, ob G0 material-sicher ist
2. **KRITISCH**: Keine Kontext-Tracking (Außen/Innen, aktueller Sicherheitsstatus)
3. **KRITISCH**: Möglichkeit von Werkstück-Kollision ist **nicht ausgeschlossen**

**Beispiel-Problem**:
```python
# PROBLEM: Außendrehen, aktuell bei X42 (sicher), soll zu X20 (Kontur)
emit_g0("X20.000")  # ⚠️ VON 42 NACH 20 = INS MATERIAL!

# RICHTIG:
# G0 Z2.000      (sicher weg)
# G0 X20.000     (jetzt OK, weil Z sicher)
# G1 X20.000 F0.15  (oder besser G1 direkt)
```

### 📝 Fix erforderlich
- [ ] **DRINGEND**: Implementiere Sicherheitsprüfung für G0-Bewegungen
- [ ] **DRINGEND**: Tracke aktueller Bearbeitungsmodus (Außen/Innen) + Sicherheitsstatus
- [ ] **DRINGEND**: Prüfe vor jedem G0 in X:
  - Außen (side_idx=0): Ist X-Ziel >= X-aktuell? (sonst: Fehler oder G1)
  - Innen (side_idx=1): Ist X-Ziel <= X-aktuell? (sonst: Fehler oder G1)
- [ ] **FALLBACK**: Falls ungültig → entweder Fehler werfen oder zu G1 umwandeln

---

## 📊 Zusammenfassung: Compliance-Status

| Regel | Anforderung | Status | Priorität | Aktion |
|-------|-------------|--------|-----------|--------|
| 1 | TC nur bei Bedarf | ⚠️ Teils | HOCH | Start/End TC hinzufügen |
| 2 | Keine Variablen | ⚠️ Teils | MITTEL | Full Grep-Audit |
| 3 | Kontur wie eingegeben | ✅ OK | - | - |
| 4 | Anfahren Z→X | ❌ FEHLT | **KRITISCH** | Alle Generatoren |
| 5 | Rückzug X→Z | ⚠️ Teils | HOCH | Test + Verify |
| 6 | Rückzugsebene smart | ⚠️ Teils | MITTEL | Test + Verify |
| 7 | Modals vor Zyklus | ⚠️ Teils | MITTEL | Audit alle Generatoren |
| 8 | Sub sauber | ✅ OK | - | - |
| 9 | G0 material-sicher | ❌ FEHLT | **KRITISCH** | Sicherheitsprüfung |

---

## 🚨 KRITISCHE FINDINGS

### KRITISCH-1: Fehlendes explizites Anfahren (Regel 4)
**Status**: ❌ NICHT IMPLEMENTIERT
**Betroffen**: Alle Generatoren
**Auswirkung**: Programme fahren möglicherweise direkt in Werkstück hinein
**Aktion**: SOFORT implementieren

### KRITISCH-2: Keine G0-Validierung bei Außen/Innendrehen (Regel 9)
**Status**: ❌ NICHT IMPLEMENTIERT
**Betroffen**: Alle G0-Bewegungen in X
**Auswirkung**: Hochrisiko für Werkstück-Kollision und Werkzeug-Bruch
**Aktion**: SOFORT implementieren

---

## 📋 Implementierungs-Roadmap

### Phase A: KRITISCHE Fixes (SOFORT)
1. [ ] Implementiere G0-Sicherheitsprüfung für X-Bewegungen (Regel 9)
2. [ ] Füge explizite G0 Z + G0 X vor allen Zyklen ein (Regel 4)

### Phase B: HOHE Priorität (diese Woche)
3. [ ] Verifiziere TC-Logik (Start/End) (Regel 1)
4. [ ] Verifiziere Rückzug X→Z Reihenfolge (Regel 5)
5. [ ] Audit Variable in Output (Regel 2)

### Phase C: MITTLERE Priorität (nächste Woche)
6. [ ] Audit Modal-Reihenfolge in DRILL/GROOVE/THREAD/KEYWAY (Regel 7)
7. [ ] Test + Integration

---

## 🔬 Test-Strategie

```bash
# Test-Datei generieren
python3 regenerate_ngc.py

# Audit Output
grep "#<" ngc/*.ngc        # Sollte 0 Hits (außer Parametern)
grep -n "G0 X" ngc/*.ngc   # Prüfe: Vorher Z sicher?
grep -n "G0 Z" ngc/*.ngc   # Reihenfolge Z vor X?
grep -n "G71\|G72" ngc/*.ngc  # Sind T/S/F vorhanden?
```

---

**Nächster Schritt**: Implementierung der Phasen A (Kritisch), dann B, dann C
