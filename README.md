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

