# Zielarchitektur: Geruest / Panel-Module / Text / Darstellung / Generator

Nutzerauftrag 2026-09-10 (LES-044): das Panel soll in fuenf getrennte,
je fuer sich austauschbare Schichten aufgeteilt sein, OHNE dass eine
Schicht beim Austausch einer anderen Funktion verliert. Dieses Dokument
haelt die Zielarchitektur fest, BEVOR LES-020/024/034 weitere
Extraktionen vornehmen (Reihenfolge laut LES-044 selbst vorgegeben) -
es beschreibt den angestrebten Zustand und den aktuellen Ist-Stand mit
seinen Luecken, keine neue Codeaenderung.

## Die fuenf Schichten

### 1. Geruest (Shell)

Zeigt nur die grobe Aufteilung des Panels (Reiter/Bereiche), enthaelt
selbst keine fachliche Logik.

- `lathe_easystep.ui` - Hauptfenster-Skelett: Reiterleiste, immer
  sichtbare Bereiche (Step-Liste, Programmverwaltung, Vorschau).
- `lathe_easystep/ui_split.py` - laedt die acht Reiter-Inhalte aus
  eigenen `.ui`-Dateien (`ui_parts/tab*.ui`) zur Laufzeit in die im
  Geruest nur als leere Container vorhandenen Reiter. Kennt die
  Reiter nur ueber `objectName`, liest/schreibt keine Inhalte.

**Schnittstelle nach aussen:** ein Reiter-Container ist ein benannter
`QWidget`; was hineingeladen wird, entscheidet ausschliesslich
`TAB_UI_FILES` in `ui_split.py`. Das Geruest selbst kennt keine
Feldnamen, Validierung oder Generatorlogik.

### 2. Panel-Module (fachliche Bereiche)

Je ein Modul pro fachlichem Bereich, mit eigenen Widgets, eigener
Validierung, eigenen Tooltips und eigenen Sprach-IDs.

- Die acht Reiter-Inhalte (`tabProgram`, `tabFace`, `tabContour`,
  `tabParting`, `tabThread`, `tabGroove`, `tabDrill`, `tabKeyway`)
  sind bereits als eigene `.ui`-Dateien unter `ui_parts/` getrennt und
  haben groesstenteils eigene `ui_*.py`-Logikdateien (`ui_header.py`,
  `ui_contour.py`, `ui_thread.py`, `ui_groove.py`, `ui_tools.py`, ...).
- **Luecke:** die zwei IMMER sichtbaren Bereiche - Step-Liste/
  Programmverwaltung (`list_ops`, Speichern/Laden-Buttons) und
  Vorschau/Schnittansicht (Preview-Widget samt Schnittebenen-Regler) -
  liegen direkt im Geruest-`.ui` und werden ueberwiegend aus
  `lathe_easystep_handler.py` heraus bedient, nicht als eigene Module
  mit klarer Grenze. Das ist der konkrete Gegenstand von LES-024s
  ersten beiden Punkten ("Vorschau/Schnittansicht auslagern",
  "Step-Liste/Programmverwaltung auslagern").

**Schnittstelle nach aussen:** ein Panel-Modul darf Text nur ueber
`TRANSLATIONS.tr(key, lang)` ausgeben (Schicht 3), Zeichenoperationen
nur ueber ein Darstellungselement mit reinen Geometriedaten anstossen
(Schicht 4) und G-Code/Vorschau-Geometrie nur ueber die oeffentlichen
Generator-Funktionen anfordern (Schicht 5) - nie eigene Zeichen- oder
G-Code-Logik enthalten.

### 3. Text/Sprache

Bereits die Referenzimplementierung des Prinzips "Schicht durch
Austausch einer Datei ersetzbar":

- `lathe_easystep/languages/{de,en,es}.lng` - je 1.031 identische,
  nichtleere Sprachschluessel.
- `lathe_easystep/translations.py::TRANSLATIONS` - laedt die aktive
  Sprachdatei, `TRANSLATIONS.tr(key, lang)` ist der einzige erlaubte
  Zugriffsweg fuer UI-Text.

**Bekannte, bewusst nicht geschlossene Luecke** (siehe LES-044-Notiz
in TODO.md): G-Code-Kommentare (`(Schlichtschnitt Kontur)`) und
`ValueError`-Meldungen in `gcode_safety.py`/`gcode_roughing.py`/etc.
sind fest deutschsprachig in den Generator-Dateien eingebettet, nicht
ueber `TRANSLATIONS` gefuehrt. Das ist fachlich vertretbar (G-Code-
Kommentare sind Werkstattdokumentation fuer die Maschine, keine
UI-Praesentation) und wird hier bewusst nicht angetastet, bis explizit
entschieden ist, ob/wie weit das ueberhaupt gewuenscht ist.

### 4. Darstellung (Rendering)

Reine Zeichen-/Geometrieklassen, die NUR Daten entgegennehmen (Punkte,
Segmente, Primitive), niemals den Handler selbst.

- **Gutes Beispiel:** `lathe_easystep/preview_widget.py::LathePreviewWidget`
  - ein `QWidget`, dessen Konstruktor keinen `handler` entgegennimmt.
  Befuellt wird es ausschliesslich ueber die Felder `paths`/
  `primitives` (Listen aus Punkten/Zeichenprimitiven) sowie
  `preview_geometry.py`-Hilfsfunktionen, die ihrerseits nur Zahlen/
  Operationsdaten entgegennehmen und Koordinaten zurueckgeben - keine
  Qt-Abhaengigkeit in der Geometrieberechnung selbst.
- **Gegenbeispiel / erster konkreter Umbaukandidat (LES-044):**
  `lathe_easystep/tool_logic.py::render_tool_preview(handler, tool)`
  vermischt Geometrieberechnung (Einsatz-Polygon, Schaft-Rechteck,
  Orientierungswinkel, Nasenradius-Position) UND `QPainter`-
  Zeichenaufrufe in einer einzigen ca. 80-zeiligen Funktion, die
  direkt ein `QPixmap` zurueckgibt. Ein Austausch der Darstellung
  (andere Grafikbibliothek, andere Visualisierung der Schneidplatte)
  erfordert aktuell Aenderungen mitten in dieser Funktion statt eines
  Austauschs an einer Stelle.

**Schnittstelle nach aussen:** eine Darstellungsklasse/-funktion
bekommt ausschliesslich Geometrie-Primitive oder einfache Datentypen
(z. B. `Tool`-Dataclass-Felder) als Parameter, nie `handler`. Wo eine
Funktion wie `render_tool_preview()` heute `handler` nur nutzt, um
andere reine Geometriefunktionen aufzurufen (`_infer_insert_profile`,
`_build_insert_geometry`, `_tool_orientation_angle`,
`_tool_holder_angle` - alle bereits zustandslos), ist das ein Zeichen,
dass diese Funktionen direkt (ohne `handler`-Umweg) aufgerufen werden
koennten.

### 5. Generator

Bereits vollstaendig unabhaengig von UI/Qt - der am weitesten
fortgeschrittene Teil der Zielarchitektur.

- `gcode_*.py`, `contour_logic.py`, `contour_features.py` importieren
  kein `qtpy`/`PyQt5`, lassen sich direkt per
  `generate_program_gcode()`/`gcode_for_operation()` ohne laufende UI
  aufrufen und testen (wie in dieser Sitzung durchgaengig genutzt, u. a.
  fuer alle LES-046/047/048/049-Regressionstests).

**Schnittstelle nach aussen:** nimmt ausschliesslich `Operation`-Objekte
und ein `settings`-Dict entgegen, gibt Listen von G-Code-Zeilen bzw.
Vorschau-Primitiven zurueck. Kein Zugriff auf Qt-Widgets, keine
Seiteneffekte auf den Handler.

## Reihenfolge der naechsten Schritte (LES-024/LES-044)

1. **Dieses Dokument** (erledigt mit diesem Commit).
2. `render_tool_preview()` entlang der oben beschriebenen Trennung
   umbauen - kleinster, konkretester Umbaukandidat, von LES-044 selbst
   als erstes Beispiel benannt. Aktuell KEINE Testabdeckung fuer diese
   Funktion vorhanden (`grep` ueber `tests/` liefert keinen Treffer fuer
   `render_tool_preview`/die vier reinen Geometriehelfer, die sie nutzt)
   - der Umbau muss deshalb zuerst neue Tests fuer die extrahierte
   Geometrieberechnung schaffen, BEVOR die Zeichenaufrufe angefasst
   werden, um die Trennung selbst abzusichern.
3. Step-Liste/Programmverwaltung als eigenes Panel-Modul auslagern
   (Widgets bereits klar benannt: `list_ops`, `btn_save_changes`,
   `btnSaveProgram`, `btnLoadProgram`, `btnSaveStep`, `btnLoadStep`) -
   kleinerer Umfang als die Vorschau, da bereits ueberwiegend in
   `ui_persistence.py`/`ui_dirty.py`/`ui_flow.py` gekapselt ist und vor
   allem noch die Widget-Registrierung selbst im Handler verbleibt.
4. Vorschau/Schnittansicht als eigenes Panel-Modul auslagern (groesserer
   Umfang: `preview_widget.py` ist bereits sauber, aber die Befuellung
   ueber `_refresh_preview()` und die Schnittebenen-Steuerung liegen
   noch verteilt im Handler).
5. Nach jedem Schritt: voller Testlauf, echtes `uic.loadUi`, Embedded-
   und Standalone-Start vergleichen (LES-035).

Nicht Gegenstand dieses Dokuments: die Punkte "G-Code-Kommentare/
Fehlertexte an Sprachmechanismus anbinden" und "Geruest zeigt nur grobe
Aufteilung" bleiben als eigene, spaeter zu entscheidende Fragen offen
(siehe TODO.md LES-044).
