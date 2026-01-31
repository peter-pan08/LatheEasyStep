# Lathe EasyStep

## Deutsch

### Was ist Lathe EasyStep?
Lathe EasyStep ist ein **Onboard-Drehpanel für LinuxCNC**, mit dem sich viele Drehteile **direkt an der Maschine** programmieren lassen – ohne externes CAM.

Der Fokus liegt auf:
- reproduzierbaren, maschinensicheren Bewegungen
- klaren Zustellungen und Rückzugsbewegungen
- schneller Bedienung im Werkstattalltag

Ziel ist es, einen großen Teil typischer Drehteile (Schruppen, Konturen, Fasen, Radien) direkt im Panel zu erzeugen.

### Funktionen
- **Programmkopf**: Definition von Rohteilgeometrie, Einheiten (mm/inch), Rückzugsebenen und Sicherheitsabständen
- **Operationen**:
  - **Planen (FACE)**: Ebenes Bearbeiten mit optionalen Fasen oder Radien an den Ecken
  - **Kontur (CONTOUR)**: Punktweise Definition von Profilen mit Geraden, Fasen und Radien (innen/außen) – nur Geometrie, kein G-Code
  - **Gewinde (THREAD)**: Erzeugung von metrischen oder Trapezgewinden mit G76-Zyklus
  - **Nut (GROOVE)**: Axial oder radial gerichtete Nuten mit variabler Breite
  - **Bohren (DRILL)**: Bohroperationen mit LinuxCNC-Zyklen (G81 einfaches Bohren, G82 mit Verweilzeit, G83/G73 Peck-Bohrung, G84 Gewindebohren) – dynamische UI für zyklusspezifische Parameter
  - **Abspanen (ABSPANEN)**: Schruppbearbeitung mit parallelen oder Querschnitt-Strategien, G71/G72-Zyklen für monotone Konturen, sonst Moves-Modus
  - **Keilnut (KEYWAY)**: Makro-basierte Keilnutbearbeitung
- **Live-Vorschau**: XZ-Seitenansicht mit Kollisionserkennung, Rohteildarstellung und Bearbeitungspfaden
- **Validierung**: Automatische Prüfung geometrischer Machbarkeit vor G-Code-Generierung, harte Validierung ohne Defaults für Pflichtparameter
- **Zweisprachige Benutzeroberfläche**: Deutsch (Standard) und Englisch
- **Dynamische UI**: Parameterfelder erscheinen/verschwinden basierend auf gewählten Modi (z.B. Verweilzeit nur bei G82)
- **G-Code-Generierung**: Optimierte Ausgabe mit LinuxCNC-Zyklen, Fanuc-kompatibel, mit Save-Dialog für Dateien
- **Speicherung und Laden**: Programme als JSON-Dateien speichern/laden
- **Sicherheitsfeatures**: Simultane X/Z-Rückzüge, parametergesteuerte Zustellungen, Kollisionsvermeidung
- **Werkzeugintegration**: Automatisches Laden von Tools aus LinuxCNC, Dropdown-Auswahl mit Lagegrafik, Warnungen bei Innen/Außen-Mismatch
- **G-Code-Generator (aktuelle Logik)**:
  - **Toolwechsel**: Vor jedem `T.. M6` immer `G53 G0 X<TC_X> Z<TC_Z>` (TC aus Panel), danach `G0 X<X_safe> Z<Z_safe>`
  - **Safe-Bereich**: `X_safe = Rohteil_OD + XRA`, `Z_safe = ZRA` (absolute Zahlen)
  - **Rückzug nach jedem Cutting-Step**: immer getrennt `G0 X<X_safe>` dann `G0 Z<Z_safe>`
  - **Anfahrt aus SAFE**: diagonal erlaubt `G0 X<X_start> Z<Z_start>`
  - **Kühlung**: pro Step explizit `M7` (Mist), `M8` (Flood), `M9` (Off)
  - **Bohren (LinuxCNC)**: Canned Cycles mit `G17` vor dem Zyklus, danach `G80` und zurück zu `G18`
  - **Kommentare**: Inhalte werden von Klammern bereinigt (keine verschachtelten Kommentare)

---

### Voraussetzungen
- LinuxCNC (getestet mit QTVCP / QtDragon)
- Python 3
- `qtpy` (falls nicht vorhanden: `pip3 install --user qtpy`)
  - Die Panel-Initialisierung fällt zurück auf PyQt5, wenn qtpy nicht importierbar ist.

Installation / Einbindung
Panel-Dateien in ein geeignetes Verzeichnis kopieren (z. B. in den Screen-Ordner)

Panel im verwendeten QTVCP-Screen einbinden

LinuxCNC neu starten

Hinweis: Details zur Einbindung hängen vom verwendeten Screen ab (QtDragon, eigener Screen etc.).

Grundbedienung (Kurzüberblick)
Kontur
Kontur wird punktweise aufgebaut – die Vorschau rechnet aus den Segmenten echte Linien oder Bögen.

Pro Punkt können Kanten definiert werden:

- keine
- Fase
- Radius (nur gültige Winkel + Länge lösen echte Bögen aus; bei zu großen Radien erscheint eine Warnung in der Konsole)

Bei Radien kann Innen/Außen gewählt werden

Abspanen
Auswahl der Abspanstrategie (z. B. parallel Z)

Zustellung, Schrittweite und Sicherheitsabstände einstellen

Vorschau prüfen

G-Code erzeugen

Sicherheitsparameter
SC: Sicherheitsabstand vor dem Material

XRA / ZRA: Rückzugsbewegungen (absolut oder inkremental)

Aktueller Stand / Einschränkungen
- Vollständige Integration von LinuxCNC-Zyklen (G71/G72 für Abspanen, G81-G84 für Bohren)
- Fokus auf Schrupp- und Schlichtstrategien mit geometrisch korrekter Behandlung von Radien
- Radien werden als echte Bögen in der Vorschau dargestellt; G-Code nutzt Zyklen für optimale Ausgabe
- **LinuxCNC-spezifisch**: Bohrzyklen schalten intern auf `G17` und zurück zu `G18`
- Projekt ist aktiv in Entwicklung – neue Operationen und Verbesserungen werden regelmäßig hinzugefügt

Lizenz
Siehe Lizenzdatei im Repository.

English
What is Lathe EasyStep?
Lathe EasyStep is an onboard turning panel for LinuxCNC designed to create turning programs directly at the machine, without external CAM software.

The focus is on:

deterministic and machine-safe toolpaths

clear depth-of-cut and retract logic

fast shop-floor usability

The goal is to cover a large portion of typical turning jobs directly inside the panel.

Features
- **Program Header**: Definition of stock geometry, units (mm/inch), retract planes and safety clearances
- **Operations**:
  - **Facing (FACE)**: Flat machining with optional chamfers or radii at corners
  - **Contour (CONTOUR)**: Point-wise profile definition with lines, chamfers and radii (inner/outer) – geometry only, no G-code
  - **Threading (THREAD)**: Generation of metric or trapezoidal threads using G76 cycle
  - **Grooving (GROOVE)**: Axial or radial grooves with variable width
  - **Drilling (DRILL)**: Drilling operations with LinuxCNC cycles (G81 simple drilling, G82 with dwell, G83/G73 peck drilling, G84 tapping) – dynamic UI for cycle-specific parameters
  - **Parting (ABSPANEN)**: Roughing with parallel or cross-section strategies, G71/G72 cycles for monotonic contours, otherwise moves mode
  - **Keyway (KEYWAY)**: Macro-based keyway machining
- **Live Preview**: XZ side view with collision detection, stock display and toolpaths
- **Validation**: Automatic check of geometric feasibility before G-code generation, strict validation without defaults for required parameters
- **Bilingual UI**: German (default) and English
- **Dynamic UI**: Parameter fields appear/disappear based on selected modes (e.g., dwell only for G82)
- **G-Code Generation**: Optimized output with LinuxCNC cycles, Fanuc-compatible, with save dialog for files
- **Save/Load**: Programs saved/loaded as JSON files
- **Safety Features**: Simultaneous X/Z retracts, parameter-driven feeds, collision avoidance
- **Tool Integration**: Automatic loading of tools from LinuxCNC, dropdown selection with location graphic, warnings for inner/outer mismatch
- **G-code generator (current behavior)**:
  - **Tool change**: Always `G53 G0 X<TC_X> Z<TC_Z>` before any `T.. M6` (TC from panel), then `G0 X<X_safe> Z<Z_safe>`
  - **Safe zone**: `X_safe = stock_OD + XRA`, `Z_safe = ZRA` (absolute values)
  - **Retract after each cutting step**: always separate `G0 X<X_safe>` then `G0 Z<Z_safe>`
  - **Approach from SAFE**: diagonal allowed `G0 X<X_start> Z<Z_start>`
  - **Coolant**: explicit per step `M7` (mist), `M8` (flood), `M9` (off)
  - **Drilling (LinuxCNC)**: canned cycles switch to `G17`, then `G80`, then back to `G18`
  - **Comments**: content is sanitized (no nested parentheses)

Requirements
- LinuxCNC (tested with QTVCP / QtDragon)
- Python 3
- `qtpy` (install via `pip3 install --user qtpy`; the panel automatically falls back to PyQt5 if qtpy is unavailable)

Installation / Integration
Copy the panel files into an appropriate screen directory

Integrate the panel into your QTVCP screen

Restart LinuxCNC

Current limitations
- Full integration of LinuxCNC cycles (G71/G72 for parting, G81-G84 for drilling)
- Focus on roughing and finishing strategies with geometrically correct radius handling
- Radii displayed as true arcs in preview; G-code uses cycles for optimal output
- **LinuxCNC-specific**: drilling cycles temporarily switch to `G17` and back to `G18`
- Project under active development – new operations and improvements added regularly


## 🔍 Vorschau & Geometrie-Darstellung

### Interaktive Legende
- Die Vorschau enthält eine **interaktive Legende**.
- **Das Wort „Legende“ ist immer sichtbar** und dient als Klickfläche.
- Durch Anklicken kann die Legende **ein- und ausgeklappt** werden.
- Im eingeklappten Zustand wird nur der Titel angezeigt.
- Die Legende beeinflusst ausschließlich die Anzeige, **nicht** die Berechnung.

### Linienarten in der Vorschau
| Darstellung | Bedeutung |
|------------|----------|
| Grün (durchgezogen) | Kontur / Soll-Geometrie |
| Gelb (durchgezogen) | Aktiver Bearbeitungspfad |
| Grau (gestrichelt) | Rohteil |
| Türkis (gestrichelt) | Rückzugsebenen |
| Rot (gestrichelt) | Bearbeitungs- / Sicherheitsgrenze |

## 🛡 Sicherheitsbereiche
- Rohteil, Rückzugsebenen und Bearbeitungsgrenzen werden geometrisch korrekt dargestellt.
- Überschreitungen der Bearbeitungsgrenze werden visuell hervorgehoben.

## 🔧 Reiter „Planen“ – Fase oder Radius
- Am Ende der Planfläche kann optional eine **Fase oder ein Radius** definiert werden.
- Unterstützt: Keine / Fase / Radius.
- Wirkt sich auf Vorschau und generierten Bearbeitungspfad aus.



## 🔍 Preview & Geometry Display

### Interactive Legend
- The preview includes an **interactive legend**.
- The word **“Legend” is always visible** and acts as a click target.
- Clicking toggles the legend **collapsed / expanded**.
- In collapsed state only the title is shown.
- The legend affects visualization only, **not calculations**.

### Line Types in Preview
| Style | Meaning |
|------|--------|
| Green (solid) | Target contour |
| Yellow (solid) | Active toolpath |
| Grey (dashed) | Stock |
| Cyan (dashed) | Retract planes |
| Red (dashed) | Machining / safety limit |

## 🛡 Safety Areas
- Stock, retract planes and safety limits are shown geometrically correct.
- Violations of the machining limit are highlighted visually.

## 🔧 Facing Tab – Chamfer or Radius
- A **chamfer or radius** can be defined at the end of a facing operation.
- Supported: None / Chamfer / Radius.
- Affects preview geometry and generated toolpath.
