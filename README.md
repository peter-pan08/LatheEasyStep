# LatheEasyStep  
**Ein moderner, intuitiver, schrittbasierter CNC-Dreh-Programmierassistent für LinuxCNC – inspiriert von Siemens ShopTurn**

---

## 🚀 Projektziel

LatheEasyStep soll ein **vollwertiges, interaktives, visuelles Programmierwerkzeug** für CNC-Drehmaschinen unter LinuxCNC werden – ähnlich dem, was Siemens mit **ShopTurn** anbietet:

- Programmierung durch **Arbeitsschritte**, nicht durch G-Code  
- Ein **kontextbasiertes Dialogsystem**, das immer nur die wirklich relevanten Eingabefelder zeigt  
- Grafische **2D-Vorschau** der Schritte und später vollständige Konturvorschau  
- Automatische **G-Code-Erzeugung**  
- Vollständige Integration als **QtVCP-Panel** für *QtDragon Lathe*

Dieses Projekt dient nicht der Erweiterung der aktuellen *lathemacros*, sondern dem Aufbau einer **neuen, modernen, modularen und langfristig erweiterbaren Programmierumgebung** für LinuxCNC-Drehanwendungen.

---

## 📌 Warum ein komplett neuer Ansatz?

Bestehende Lösungen (lathemacros etc.) sind historisch gewachsen, überladen oder inkonsistent und basieren auf einem rein G-Code-zentrierten Workflow.

LatheEasyStep soll:

- **klar strukturiert**
- **erweiterbar**
- **UI-geführt**
- **benutzerfreundlich**
- **nah am ShopTurn-Arbeitsablauf**

sein.  
Damit können auch Anfänger effizient Programme erstellen, ohne CAD/CAM zu benötigen.

---

## 🧱 Projektarchitektur

### 1. **Program Model (Grundstruktur)**

LatheEasyStep arbeitet intern mit einem strukturierten Datenmodell:

Program
├── Global Settings (Rohteil, Maßeinheit, Nullpunkt, Werkzeug, Drehzahl etc.)
├── Worksteps [Liste]
│ └── Workstep (Typ + Parameter)
└── G-Code Generator

### 2. **Worksteps (Arbeitsschritte)**

Eine Operation (Workstep) besteht aus:

- Typ (z.B. „Planen“, „Längsdrehen“, „Bohren“ …)
- UI-Maske mit genau den passenden Parametern
- 2D-Vorschau (Geometriepfad)
- G-Code-Generatorfunktion

### 3. **Modularität**

Neue Arbeitsschritte können später leicht hinzugefügt werden.  
Gleiches gilt für:

- Zyklen (z.B. Gewinde, Stechoperationen)
- Konturbausteine (Linie, Radius, Fase)
- Rohteildefinitionen
- Werkzeugverwaltung

---

## 🧭 Roadmap (Schritt-für-Schritt)

### **Phase 1 – Minimalfunktionalität**  
*Basis schaffen, um schnell ein funktionierendes Grundsystem zu erhalten.*

#### ✔ UI Grundlayout
- Linke Seite: **Arbeitsplan (Liste der Schritte)**
- Rechts oben: Parameter der gewählten Operation
- Rechts unten: **2D-Vorschau**
- Oben: Kopfbereich mit Programmname und Rohteilform

#### ✔ Arbeitsschritt-Typen (erste Version)
1. **Planen**  
2. **Längsdrehen**

Nur die absolut notwendigen Parameter anzeigen:
- Start-Ø  
- End-Ø  
- Länge Z  
- Vorschub  
- Sicherheits-Z  

#### ✔ Geometrie-Builder
Entwicklung der Funktionen:
- `build_face_path()`
- `build_turn_path()`

#### ✔ Preview
Einbindung eines universellen 2D-Zeichenwidgets:
- schwarze Fläche
- gelbe/lime Pfade
- automatische Skalierung

#### ✔ G-Code Export
Einheitliche Ausgabe nach:

~/linuxcnc/nc_files/lathe_easystep.ngc

oder über Action → direkt laden.

---

### **Phase 2 – Erweiterung**
Nachdem alles stabil läuft:

#### ➕ Weitere Arbeitsschritte
- Ausdrehen
- Bohren
- Gewinde
- Nut
- Abspanen
- Freistich
- Einstiche außen/innen

#### ➕ Kontur-Editor (großer Meilenstein)
Analog Siemens:  
Linie, Radius, Punktfolge, Spiegeln, Drehen, Taschenkonturen …

#### ➕ Rohteilgenerator
Zylinder, Rohr, Rechteck, N-Eck – mit dynamischer Vorschau.

#### ➕ Grafische Simulation
- Komplettes Werkstück als Kontur
- Schrittweise Vorschau
- Werkzeugwegüberlagerung

---

## 🛠 Technische Grundlagen

### Das Projekt basiert auf:
- **QtVCP (QtPy/QWidgets)**
- Python 3
- LinuxCNC ab 2.9/2.10
- eigenes UI (`lathe_easystep.ui`)
- eigenes Handler-Script (`lathe_easystep_handler.py`)

### Struktur im Repo:

/ui/lathe_easystep.ui
/src/lathe_easystep_handler.py
/src/model/program.py
/src/model/workstep.py
/src/geometry/.py
/src/gcode/.py
/README.md


---

## 📄 Beispielablauf (Sollverhalten)

Ein Nutzer möchte ein einfaches Teil drehen:

1. Programm starten → „Neues Programm“
2. Rohteil definieren (z.B. Zylinder Ø40 x 60)
3. Schritt „Planen“ hinzufügen  
   - Start-Ø: 40  
   - Ziel-Z: 0  
4. Schritt „Längsdrehen“ hinzufügen  
   - Start-Ø: 40  
   - End-Ø: 20  
   - Länge: 30  
5. Vorschau zeigt die beiden Schritte grafisch
6. „G-Code erzeugen“ → Datei fertig

Das ist **1:1 das Siemens-Konzept**, aber LinuxCNC-freundlich umgesetzt.

---

## 🤝 Ziel für die Community

LatheEasyStep soll:

- das **erste echte ShopTurn-ähnliche System** für LinuxCNC werden
- vollständig Open Source sein
- modular erweiterbar
- für Hobby- und Industrieanwender geeignet
- langfristig Wartbar bleiben

Wenn wir das schaffen, wird es **einer der wichtigsten Beiträge für LinuxCNC auf Drehmaschinen** in den letzten Jahren.

---

## 💬 Mitmachen

Pull-Requests, Issues und Feature-Vorschläge sind willkommen.  
Die Architektur wird bewusst offen dokumentiert, damit andere Entwickler ohne Hürden beitragen können.

---

## 📧 Kontakt

Projektbetreuer: *Matthias*  
Unterstützung durch ChatGPT (architektonische Planung, technische Umsetzungshinweise)

---

## 📜 Lizenz

Wird empfohlen: **GPLv3** (wie LinuxCNC) oder **MIT** (offenere Nutzung).  
Bitte im Repo ergänzen.

---
