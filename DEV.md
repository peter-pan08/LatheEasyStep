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

- `start_x`/`start_z` werden jetzt als erster Punkt übernommen, sodass die erste Segmentzeile tatsächlich eine Ecke erzeugt.
- `validate_contour_segments_for_profile` überprüft jede Zeile auf Nullsegmente, Winkel und erreichbare Kantenlängen; bei Fehlern wird die Vorschau geleert und der Benutzer sieht die Details im Log (die Funktion ist der Eingang zu G71/G70).

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

## Planen / FACE
- `build_face_primitives()` repräsentiert die OD-Ecke als echte Primitive (Linien + Arc), sodass the preview die Kante am Außendurchmesser direkt zeigt.
- Die Parameter `edge_type`, `edge_size` und das neue `edge_in_roughing` bestimmen, ob die Kante als Linie, Fase oder Radius modelliert wird und ob sie schon im letzten Roughing-Pass vorgearbeitet wird.
- In `gcode_for_face()` wird bei aktivierter Vorform im Schruppen konkret eine diagonal abgesprungene Fase (G1) bzw. ein Viertelkreis (G2/G3) erzeugt; ohne Platz oder Edge-Inhalte bleibt es beim bewährten geraden Abziehen.

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
- Vorschau zeichnet X weiterhin als Durchmesser (für die Beschriftung), nutzt intern aber immer halbierte X-Werte, damit Kreise wirklich rund und in Radiusmaßstab dargestellt werden.

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
