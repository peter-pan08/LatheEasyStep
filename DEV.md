# Developer Notes – Lathe EasyStep

## Projektziel
Lathe EasyStep soll ein **shop-floor-taugliches Drehpanel** sein, kein vollwertiges CAM.
Ziel ist:
- deterministische Bewegungen
- nachvollziehbare Geometrie
- minimale Überraschungen an der Maschine

---

## Architektur-Überblick
- `lathe_easystep_handler.py`
  - UI-Logik
  - Konturverwaltung
  - Benutzerparameter
- `slicer.py`
  - Geometrische Auswertung
  - Abspanstrategien
  - G-Code-Erzeugung

UI und Toolpath-Logik sind bewusst getrennt.

---

## Kontur-Datenmodell
Konturen bestehen aus Segmenten mit:
- Punkt (X/Z)
- Kantentyp: none / chamfer / radius
- Kantenmaß
- bei Radius zusätzlich:
  - `arc_side`: auto / inner / outer

Die Kontur ist die **Quelle der Wahrheit** für:
- Vorschau
- Abspanlogik
- spätere G2/G3-Ausgabe

---

## Radien (Wichtiger Punkt)
Radien werden **nicht** als einfache Polylines verstanden, sondern als:
- echte Fillet-Geometrie zwischen zwei Geraden
- mit berechneten Tangentialpunkten
- und eindeutigem Kreismittelpunkt

Der aktuelle Stand erzeugt intern echte Arc-Geometrie, die Ausgabe erfolgt derzeit noch linearisiert.
Geplante Erweiterung:
- echte Arc-Primitiven
- G2/G3-Ausgabe (G18-Ebene)

---

## Abspanlogik
- Aktuell: Schruppen parallel Z
- Kontur wird entlang X-Linien ausgewertet
- Sichere Anfahrt, Lead-in, Lead-out und Retract werden explizit erzeugt
- Rückzug X/Z erfolgt simultan (kein sequentielles „hochziehen“)

---

## UI-Design-Entscheidungen
- Dropdowns pro Kontursegment statt globaler Optionen
- Deutsch als Primärsprache
- qtpy als Abstraktionsschicht (Fallback möglich)

---

## Bekannte technische Baustellen
- Native Arc-Intersections (statt Sampling)
- G2/G3-Ausgabe
- Werkzeuggeometrie (Nasenradius, Lage, Schneidenlänge)
- Tooltable-Integration mit Plausibilitätsprüfungen

---

## Mitwirken
Das Projekt ist experimentell, aber strukturiert.
Beiträge sind willkommen, insbesondere:
- Geometrie / Arc-Berechnungen
- zusätzliche Abspanstrategien
- Tests mit realen Maschinen

