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
- Abspanen **parallel Z** (Schruppen)
- Konturdefinition mit:
  - Geraden
  - Fasen
  - Radien (Innen / Außen pro Radius)
- Vorschau der Kontur (echte Linien/Arc-Primitives, nur gültige Radien erscheinen)
- Validierung vor Vorschau und G71/G70 – Ungültiges wird im Terminal geloggt und die Vorschau bleibt leer
- Planen: Ecken am Außendurchmesser erscheinen als Linie/Fase/Radius (inkl. Arc-Primitives)
- Optionales „Edge in Roughing“ modelliert die Kante schon im letzten Schrupphub
- Sichere Anfahr- und Rückzugsbewegungen (X/Z simultan)
- Parametergesteuerte Zustellung und Schrittweiten
- G-Code-Erzeugung direkt aus dem Panel
- Speicherung und Laden von STEP/Projektdateien

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
Fokus liegt aktuell auf Schruppstrategien

Radien werden geometrisch korrekt behandelt, Ausgabe aktuell noch linearisiert

G2/G3-Ausgabe ist geplant, aber noch nicht umgesetzt

Projekt ist aktiv in Entwicklung – Änderungen möglich

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
Roughing parallel Z

Contour definition with:

lines

chamfers

radii (inner / outer per radius)

Contour preview (genuine lines/arcs, invalid radii blocked by validation)

Safe approach and simultaneous X/Z retract

Parameter-driven roughing

Direct G-code generation

Save and load STEP/project files

Requirements
- LinuxCNC (tested with QTVCP / QtDragon)
- Python 3
- `qtpy` (install via `pip3 install --user qtpy`; the panel automatically falls back to PyQt5 if qtpy is unavailable)

Installation / Integration
Copy the panel files into an appropriate screen directory

Integrate the panel into your QTVCP screen

Restart LinuxCNC

Current limitations
Focus on roughing operations

Radii are geometrically correct but currently output as linearized segments

Native G2/G3 output planned

Project is under active development


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
