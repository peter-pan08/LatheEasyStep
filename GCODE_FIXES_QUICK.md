# ✅ G-Code Bugs – BEHOBEN

## 4 kritische Fehler wurden repariert:

### 1. ✅ Subroutinen kommen NACH M30 → JETZT VOR M30
**Impact:** LinuxCNC konnte Subroutinen nicht definieren, Preview fehlgeschlagen  
**Status:** BEHOBEN – Subroutinen jetzt vor M30

### 2. ✅ Alle Subs haben ID o100 → JETZT o100, o101, o102...  
**Impact:** Duplikate, Konflikt-Fehler  
**Status:** BEHOBEN – SubAllocator verwaltet eindeutige IDs

### 3. ✅ Kein Toolchange-Move vor M6 → JETZT mit Positions-Move
**Impact:** Safety-Risiko, Maschine in unbekannter Position  
**Status:** BEHOBEN – Jedes M6 wird durch G0 X### Z### eingeleitet

### 4. ✅ Footer-Lines doppelt → JETZT nur einmal
**Impact:** Verwirrung, ungültig nach M30  
**Status:** BEHOBEN – Footer nur einmal vor M30

---

## Was sich ändert für Sie:

✅ G-Code ist jetzt **LinuxCNC-kompatibel**  
✅ Preview funktioniert korrekt  
✅ Programme können korrekt gelesen werden  
✅ Toolchange-Sicherheit gewährleistet  

---

## Keine Änderungen nötig bei:

- UI (lathe_easystep.ui)
- Handler-Aufrufe
- Bestehende Tests
- Settings-Format

---

## Test-Bestätigung

```
Generated G-Code mit Multi-Abspanen:
✓ G72 Q100 ... (Operation 1)
✓ G72 Q101 ... (Operation 2)
✓ (=== Subroutine Definitions ===)
✓ o100 sub ... o100 endsub
✓ o101 sub ... o101 endsub  ← Eindeutig!
✓ (=== End Subroutines ===)
✓ M30
✓ %
```

Alle Checks bestanden! ✅
