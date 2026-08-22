# TODO LatheEasyStep

Stand: 2026-07-24

Diese Datei ist die verbindliche Liste aller offenen Aufgaben. Erledigte Punkte
werden entfernt und im `CHANGELOG.md` dokumentiert. Release-Ziele und
Abhaengigkeiten stehen in der [ROADMAP.md](ROADMAP.md), reale Tests in
[doc/REALTEST_FRAGEN_2026-07-15.md](doc/REALTEST_FRAGEN_2026-07-15.md).

## Aktuell verifizierte Basis

- `main`: Version 0.7.0 als lauffaehige Basis
- `dev`: aktueller Entwicklungsstand fuer 0.8.0; `main` bleibt die stabile Basis
- Teststand: `364 passed, 7 skipped`
- UI-Shell und acht Reiter-Teil-UIs sind getrennt und werden ueber
  `lathe_easystep/ui_split.py` geladen
- `de.lng`, `en.lng` und `es.lng` enthalten jeweils 1.022 identische,
  nichtleere und eindeutige Sprachschluessel
- derzeit keine offenen GitHub-Issues; diese Datei ist der Aufgabenbestand

Aufwand:

- `S`: wenige Stunden bis etwa ein Tag
- `M`: ein bis drei Entwicklungstage
- `L`: mehrere Tage mit Tests und Simulation
- `XL`: groessere Architekturarbeit in mehreren Etappen

Prioritaeten:

- `P0`: Sicherheit, falsche Fahrwege oder ungueltige Programmausgabe
- `P1`: fachliche Vollstaendigkeit und hoher praktischer Nutzen
- `P2`: Bedienkomfort, Wartbarkeit und langfristige Architektur

## Priorisierter Arbeitsindex

| ID | Prio | Aufgabe | Nutzen | Aufwand | Ziel |
|---|---|---|---|---|---|
| LES-001 | P0 | Sichere Anfahrt zwischen aufeinanderfolgenden Operationen | sehr hoch | M | 0.8.0-alpha |
| LES-003 | P0 | Innen-Schruppen Parallel-Z abschliessend verifizieren | sehr hoch | L | 0.8.0-alpha |
| LES-005 | P0 | Innen-Schlichtanfahrt und Rueckzug fuer weitere Konturformen absichern | sehr hoch | M-L | 0.8.0-alpha |
| LES-006 | P1 | Rueckzugsstrategie und Achsreihenfolge je Bearbeitungsart festlegen | hoch | M | 0.8.0 |
| LES-010 | P1 | Lokale DIN-Freistichgeometrie am markierten Segment erzeugen | hoch | L | 0.8.0 |
| LES-011 | P1 | Freistich in Vorschau, Subroutine und Schlichtweg identisch darstellen | hoch | M-L | 0.8.0 |
| LES-012 | P1 | Konturprimitive bis zur finalen G1/G2/G3-Ausgabe erhalten | hoch | L | 0.8.0 |
| LES-013 | P1 | Sichere CSS-Umschaltung nach per-Operation-G96/G97 | mittel-hoch | S-M | 0.8.0 |
| LES-015 | P1 | Innenkontur-Testmatrix automatisieren und in LinuxCNC verifizieren | hoch | M-L | 0.8.0 |
| LES-016 | P1 | UI-Sichtbarkeitsregeln fachlich festlegen und testen | mittel | S-M | 0.8.0 |
| LES-019 | P1 | Verifizierte DIN-76-Presets fuer M2, M2.5 und M3.5 ergaenzen | mittel | S-M | 0.8.0 |
| LES-030 | P1 | Neue Generatorfunktionen systematisch in LinuxCNC simulieren | hoch | M-L | 0.8.0 |
| LES-018 | P2 | G70-Wiederverwendung fuer separaten Schlichtstep pruefen | mittel | M-L | 0.9.0 |
| LES-020 | P2 | Handler in kleinen Paketen weiter verkleinern | mittel | M je Paket | 0.9.0 |
| LES-022 | P2 | Zentralen Bewegungs- und Modalzustand einfuehren | langfristig hoch | XL | 0.9.0 |
| LES-023 | P2 | Nummer nur bei Export erzeugen statt dauerhaft speichern (Rest) | gering-mittel | S-M | 0.9.0 |
| LES-024 | P2 | Restliche UI-Modularisierung und Controllergrenzen abschliessen | mittel | L | 0.9.0 |
| LES-027 | P2 | Start- und Reaktionszeit im Embedded-Betrieb messen | mittel | S | 0.9.0 |
| LES-028 | P2 | Werkzeug- und G76-Parameter vor Ausgabe zentral normalisieren | mittel-hoch | M | 0.9.0 |
| LES-031 | P2 | Redundante Bewegungen und Modalbefehle systematisch bereinigen | mittel | M-L | 0.9.0 |
| LES-032 | P2 | Werkzeuggeometrie und Tooltable-Plausibilitaet vertiefen | hoch | L | 0.9.0 |
| LES-033 | P2 | Gewindevorschau aus realen Gewindeparametern ableiten | mittel | M-L | 0.9.0 |
| LES-034 | P2 | Preview-Pipeline fachlich in Werkstueck, Werkzeugweg und Hilfsgeometrie trennen | mittel | L | 0.9.0 |
| LES-035 | P2 | Embedded- und Standalone-Verhalten weiter angleichen | mittel | M | 0.9.0 |
| LES-036 | P1 | Kantenform "Radius" beim Planen umsetzen | mittel | M | 0.8.0 |

## P0 - Sicherheits- und Generatorblocker

### LES-001 Sichere Anfahrt zwischen Operationen

Aktueller Fehler: `emit_approach()` gibt bei gesetztem `_is_at_safe` einen
direkten diagonalen Zielmove aus. Der Status sagt nur, dass die vorherige
Operation an einer sicheren Position endete; er beweist nicht, dass der neue
Zielpunkt von dort direkt kollisionsfrei erreichbar ist.

- [ ] direkten Zielmove nicht allein aus dem Boolean `_is_at_safe` ableiten
- [ ] sichere Achsreihenfolge anhand Start-, Ziel-, Rohteil- und Futterzone waehlen
- [ ] gleiches Werkzeug ohne dazwischenliegenden Werkzeugwechsel testen
- [ ] Aussen-Schruppen -> Schlichten und Innen-Schruppen -> Schlichten testen
- [ ] Bohren und Gewinde als Z-vor-X-Sonderfaelle pruefen
- [ ] Warnung und tatsaechlicher Fahrweg duerfen sich nicht widersprechen
- [ ] Regressionen fuer Rohteil- und Chuck-No-Go-Faelle ergaenzen

### LES-003 Innen-Schruppen Parallel-Z abschliessend verifizieren

WICHTIGER BEFUND (real gegen den LinuxCNC-Interpreter verifiziert, Quelle
`/home/adm1n/linuxcnc-src/src/emc/rs274ngc/interp_g7x.cc`, Version
2.10.0~pre1 - identisch zur installierten Version): `G71`/`G72` erzeugen bei
Innenkonturen nur EINEN durchgehenden Schnitt statt echter Treppenstufen-
Schrupppaesse (empirisch mit `rs274` bestaetigt, sowohl fuer die reale
Nutzerkontur als auch fuer einen trivialen linearen Innenkegel), waehrend
identisch aufgebaute Aussenkonturen korrekt mehrfach zustellen. Kein Fehler
dieses Generators, sondern eine Einschraenkung dieser LinuxCNC-Version fuer
Innenbearbeitung. `G71`/`G72` werden deshalb jetzt AUSSCHLIESSLICH fuer
Aussenbearbeitung gewaehlt; Innenbearbeitung nutzt immer die
bewegungsbasierte Ersatzloesung (`rough_turn_parallel_x()`).

Damit ist aber der eigentliche, urspruenglich gemeldete Fehler
("keine wirkliche Abspanaufgabe generiert") NICHT geloest, sondern nur die
falsche Zyklus-Wahl behoben - er liegt jetzt sichtbar in
`rough_turn_parallel_x()` selbst: die schmale Fenster-Intersection
(`x_cut +/- 1e-3`) findet fuer mehrere X-Baender keinen Treffer ("no cut
region"), waehrend ein anderes Band eine lange senkrechte Bohrungswand
komplett in einem einzigen Schnitt zusammenfasst statt sie ueber mehrere
Zustellungen zu verteilen (dokumentiert, aber bewusst NICHT behoben, in
`tests/test_internal_roughing_uses_g71_cycle.py::test_internal_roughing_with_real_bore_contour_still_produces_uneven_passes`).
Ein Fix braucht eine echte Neuentwicklung der Zustelllogik (fuer jedes
X-Band den Z-Bereich finden, in dem die Zielkontur ueber diese Tiefe
hinausgeht, statt nur die Kontur an einem schmalen Fenster zu schneiden) -
zu risikoreich fuer eine schnelle Aenderung an sicherheitsrelevanter
Fahrweg-Geometrie.

- [ ] `rough_turn_parallel_x()` neu entwerfen: pro X-Band den vollstaendigen
  Z-Bereich ermitteln, der bei dieser Tiefe noch Material hat (nicht nur wo
  die Kontur das schmale Fenster kreuzt), damit Material gleichmaessig ueber
  mehrere Zustellungen abgetragen wird
  statt in eine einzelne Bohrungswand komplett auf einmal
- [ ] `XRI` nur als sichere Einfahr-/Rueckzugsebene verwenden, niemals als
  Schnittbahn; Regression muss jeden G1-Profilwert gegen diese Grenze pruefen
- [ ] Schlichtaufmass X/Z fuer Innenkonturen korrekt ausrichten
- [ ] automatisierte Faelle fuer monoton steigende UND fallende Z-Konturen
  sowie Innen-/Aussenbearbeitung pflegen
- [ ] `examples.py` um ein verifiziertes Innen-Abspanen-Beispiel
  (`side=inside`) ergaenzen und in `regenerate_all_ngc.py` aufnehmen
- [ ] LinuxCNC-Parser, Backplot und Trockenlauf mit diesem Referenzteil
  dokumentieren (P0 - vor Praxiseinsatz zwingend)

### LES-005 Innen-Schlichtanfahrt und Rueckzug

Ein Einfahrweg fuer aktive Schneidenradiuskorrektur existiert bereits.
Realtest-Frage 11 ist beantwortet: Innenstufe, Innenkonus und Innenradius
wirken korrekt; der Innenfreistich bleibt als bekannter Fehler unter
LES-010/LES-011 offen. Die Antwort schliesst die Nutzerfrage, ersetzt aber
nicht die reproduzierbare Generator- und LinuxCNC-Verifikation.

- [ ] zuerst auf nachweislich freien Innendurchmesser fahren
- [ ] axial auf Konturstart fahren, bevor der Schnittdurchmesser angefahren wird
- [ ] Schneidenradiuskorrektur nur auf ausreichend langem Einfahrweg aktivieren
- [ ] Konturstart vorne und hinten getrennt testen
- [ ] nach dem Schnitt zuerst radial und danach axial freifahren
- [ ] Innenstufe, Innenkonus und Innenradius als automatisierte Regressionen
  plus LinuxCNC-Backplot absichern
- [ ] Innenfreistich nach Umsetzung von LES-010/LES-011 separat abnehmen

## P1 - Fachliche Vollstaendigkeit fuer 0.8.0

### LES-006 Rueckzugsstrategie je Bearbeitungsart

Den Inventor-LinuxCNC-Post als Referenz auswerten und fuer jede Operation
explizit festlegen:

- [ ] nur X
- [ ] nur Z
- [ ] X dann Z
- [ ] Z dann X
- [ ] X/Z gleichzeitig
- [ ] Matrix fuer Planen, Abspanen innen/aussen, Schlichten, Gewinde,
  Bohren, Einstich/Abstich, Keilnut, Werkzeugwechsel und Parken dokumentieren
- [ ] Strategie in Generator und Tests abbilden

### LES-010 Lokale DIN-Freistichgeometrie

Freistiche werden derzeit nur erzeugt, wenn das Feature am ersten oder letzten
Segment der gesamten Kontur liegt.

- [ ] Segment-zu-Primitive-Zuordnung einfuehren
- [ ] Freistich relativ zum markierten Segment erzeugen
- [ ] Nachbarsegmente und lokale Bearbeitungsrichtung auswerten
- [ ] Freistich mitten in einer laengeren Wellenkontur unterstuetzen
- [ ] Innen- und Aussenfreistich getrennt behandeln
- [ ] DIN-76-Geometrie gegen verifizierte Referenz pruefen

### LES-011 Einheitliche Freistichdarstellung

- [ ] Fertigkontur, Schruppkontur und Feature-Teilkontur aus derselben Geometrie ableiten
- [ ] Aussen-/Innenfreistich in der Seitenvorschau darstellen
- [ ] Gewindeanfang und Gewindeende unterscheiden
- [ ] Vorschau, Kontur-Subroutine und ausgeschriebenen Schlichtweg vergleichen
- [ ] Save/Load-Roundtrip der Segment-Features testen

### LES-012 Konturprimitive und G2/G3 erhalten

Der explizite Schlichtweg kann Radien als G2/G3 ausgeben. Der reale
LinuxCNC-Fehler bei Boegen mit echtem X-Zentrumsversatz ist behoben:
Im Durchmessermodus G7 wird die X-Differenz zum Zentrum fuer den radialen
`I`-Wert halbiert. Regressionen decken den direkten Schlichtpfad und die
G71/G72-Kontur-Subroutine ab. Verbleibende Move-based-Pfade linearisieren
Geometrie teilweise noch.

- [ ] Linien und Boegen bis zur Ausgabe als Primitive fuehren
- [ ] Radien nicht in reine G1-Punktlisten umwandeln
- [ ] Arc-Intersections im Move-based Roughing vertiefen
- [ ] Vorschau und Generator auf dieselbe Primitive-Quelle umstellen
- [ ] mindestens einen Referenzbogen mit `I != 0` dauerhaft in
  `examples.py`/`ngc/` halten
- [ ] fuer direkten Schlichtweg UND G71/G72-Subroutine im Test nachweisen,
  dass Start- und Endradius zum ausgegebenen I/K-Zentrum uebereinstimmen
- [ ] denselben Nichtnull-I-Fall im LinuxCNC-Parser und Backplot bestaetigen

### LES-013 Sichere CSS-Umschaltung

G96/G97 ist pro Operation fuer Planen, Abspanen, Einstich/Abstich und Gewinde
umgesetzt; Bohren bleibt bewusst bei G97. `G96 S` verwendet jetzt Vc in
m/min, `D` die programmweite Maximaldrehzahl (siehe CHANGELOG.md). Offen ist
ausschliesslich die sichere Aktivierungssequenz:

- [ ] festlegen, welcher reale Durchmesser fuer die feste Anfahrdrehzahl gilt
- [ ] sichere Anfahrdrehzahl aus Vc, Durchmesser und Maximaldrehzahl berechnen
  und Grenz-/Nullfaelle eindeutig behandeln
- [ ] Anfahrt mit G97 ausgeben und G96 erst an einer definierten,
  fachlich sicheren Bearbeitungsposition aktivieren
- [ ] Operationsfolge G96 -> G97 (Bohren) -> G96 als Regression testen;
  weder Drehzahl noch Vc duerfen zwischen den Operationen verwechselt werden
- [ ] Save/Load eines gemischten G96/G97-Programms mit echtem PyQt5 testen
- [ ] resultierende Modalsequenz in LinuxCNC-Parser und Backplot bestaetigen

### LES-015 Innenkontur-Testmatrix

Realtest-Frage 11 ist beantwortet: Innenstufe, Innenkonus und Innenradius
erscheinen korrekt, der Freistich ist der bekannte offene LES-010/LES-011-Fall.
Offen ist deshalb keine weitere Grundsatzantwort, sondern eine reproduzierbare
Test- und Referenzmatrix.

- [ ] zylindrische Innenkontur
- [ ] Innenstufe
- [ ] Innenkonus
- [ ] Innenradius mit `I != 0`
- [ ] Innenkontur mit Freistich nach Umsetzung von LES-010/LES-011
- [ ] Schruppen mit anschliessendem Schlichten
- [ ] Konturstart vorne und hinten sowie steigende/fallende Z-Reihenfolge
- [ ] Werkzeugradiuskorrektur, Konturseite und sichere Ein-/Ausfahrt je Fall
- [ ] Vorschau, erzeugten G-Code und LinuxCNC-Backplot je Referenz vergleichen

### LES-016 UI-Sichtbarkeitsregeln

Fuer die folgenden Punkte bestehen AKTUELL KEINE Sichtbarkeitsregeln im Code
- hier fehlt nicht ein Test, sondern eine Produktentscheidung, welche Felder
ueberhaupt bedingt ein-/ausgeblendet werden sollen, bevor eine Regression
sinnvoll ist:

- [ ] Kontur: entscheiden und dokumentieren, ob `setEnabled` fuer
  Kantengroesse ausreicht oder Felder wirklich ausgeblendet werden sollen
- [ ] Gewinde: entscheiden, ob `thread_relief_norm` nur bei
  `thread_relief_mode == "suggest"` sichtbar sein soll
- [ ] Innen/Aussen: je Operation festlegen, ob `side`/`lage`/
  `orientation` weitere Felder bedingt ein- oder ausblenden
- [ ] jede neu eingefuehrte Regel mit echtem PyQt5 fuer beide Zweige testen
- [ ] Sprachumschaltung und Save/Load duerfen Sichtbarkeit und technische
  `currentData()`-Werte nicht veraendern
- [ ] falls keine fachlich sinnvolle Regel benoetigt wird, den jeweiligen
  Unterpunkt begruendet schliessen statt kuenstliche UI-Logik einzubauen

### LES-019 Fehlende DIN-76-Presets

- [ ] verifizierte Normwerte fuer M2, M2.5 und M3.5 beschaffen
- [ ] Aussen- und Innenvarianten ergaenzen
- [ ] Datenvalidierung und Preset-Tests erweitern
- [ ] keine Werte schaetzen

### LES-030 LinuxCNC-Simulationsmatrix

- [ ] alle Referenzprogramme nach Generatoraenderungen regenerieren
- [ ] Planen, Bohren, Gewinde, Einstich, Abspanen innen/aussen und Konturen pruefen
- [ ] Nichtnull-I-Boegen unter G7 im direkten Schlichtweg und in
  G71/G72-Subroutinen auf Parserfehler und korrekten Backplot pruefen
- [ ] Innen-G71 mit monoton steigendem und fallendem Z sowie vorhandener
  Bohrung als Materialgrenze pruefen
- [ ] gemischte Operationsfolge G96 -> G97 -> G96 inklusive D/S-Einheiten
  und Aktivierungsposition pruefen
- [ ] Parserfehler, Backplot, Werkzeugwechsel und Parkbewegungen dokumentieren
- [ ] relevante Sicherheits- und Materialabtragsfaelle als reale Trockenlaeufe bestaetigen
- [ ] Maschinenprofile und Futter-Sperrzonen mit Beispielen verifizieren

### LES-036 Kantenform "Radius" beim Planen

Die String-ID-Auswertung fuer die Planen-Kantenform ist repariert: "Fase"
funktioniert wieder. "Radius" ist im UI waehlbar, im Generator aber noch nicht
umgesetzt und wird deshalb derzeit mit einer klaren Fehlermeldung abgewiesen.
Da die Option sichtbar angeboten wird, gehoert die Umsetzung als P1 in 0.8.0.

- [ ] Radius-Eckengeometrie fuer den 90-Grad-Planen-Spezialfall umsetzen
- [ ] Durchmesser-/Radiusumrechnung fuer X sowie G2/G3-I/K eindeutig herleiten
- [ ] String-IDs und alte numerische Save-Dateien weiterhin unterstuetzen
- [ ] Vorschau und G-Code aus derselben Geometrie ableiten
- [ ] Grenzfaelle pruefen: Radius 0, zu grosser Radius, Schruppen,
  Schlichten und Schruppen+Schlichten
- [ ] echten PyQt5-Roundtrip sowie LinuxCNC-Parser/Backplot testen
- [ ] Realtest am Panel nach Umsetzung dokumentieren

## P2 - Bedienung, Wartbarkeit und Architektur

### LES-018 G70 fuer separaten Schlichtstep

Der aktuelle explizite Schlichtweg ist fachlich korrekt. Zu pruefen ist nur die
Optimierung, einen bereits von einem frueheren G71/G72-Step verwendeten
Kontur-Sub spaeter per G70 wiederzuverwenden.

- [ ] stabile Zuordnung Kontur -> Subroutine -> vorheriger Schruppstep entwerfen
- [ ] reiner Schlichtstep darf niemals erneut schruppen
- [ ] Fallback auf expliziten Schlichtweg beibehalten

### LES-020 Handler weiter verkleinern

Jede Extraktion einzeln mit vollem Testlauf und echtem `uic.loadUi` pruefen.

- [ ] Programmkopf-Sammlung
- [ ] Kontursegment-Sammlung
- [ ] Gewinde-Preset-UI nach `ui_thread.py`
- [ ] Widget-Bootstrapping
- [ ] Tooltip-Erzwingung nach `ui_tooltips.py`

### LES-022 Zentraler Bewegungs- und Modalzustand

- [ ] aktuelle X/Z-Position bei jeder Move-Emission mitfuehren
- [ ] G90/G91, G94/G95, G96/G97, G18 und G40/G41/G42 verwalten
- [ ] M3/M4/M5, M7/M8/M9 und Werkstuecknullpunkt verwalten
- [ ] sichere Pfadentscheidungen auf reale aktuelle Position stuetzen
- [ ] robuste explizite Ausgabe fuer manuell bearbeitbaren G-Code erhalten

### LES-023 Step-Kommentare normalisieren

Groessere Architekturfrage, nicht nur ein Bugfix (Detailfix siehe CHANGELOG.md):

- [ ] laufende Nummer nur beim Gesamtprogrammexport erzeugen, nicht dauerhaft in `params["comment"]` speichern
- [ ] Konturen bewusst mitzaehlen oder als nicht ausfuehrbare Geometrie markieren

### LES-024 Restliche UI-Modularisierung

- [ ] Vorschau/Schnittansicht in eigene UI-Struktur auslagern
- [ ] Step-Liste und Programmverwaltung auslagern
- [ ] je Modul Controller, Tooltips, Sprach-IDs und Validierung zuordnen
- [ ] direkte Widgetzugriffe zwischen Modulen durch definierte Schnittstellen ersetzen
- [ ] Embedded- und Standalone-Laden testen

### LES-027 Performance

- [ ] Startzeit bis sichtbares und bedienbares Panel messen
- [ ] Embedded und Standalone vergleichen
- [ ] Reiterwechsel, Stepwechsel und Preview-Refresh messen
- [ ] Realtest-Frage 7 abschliessen

### LES-028 Eingaben zentral normalisieren

- [ ] Werkzeugwechsel nur aus normalisiertem Werkzeugdatensatz erzeugen
- [ ] G76-Parameter vor Ausgabe vollstaendig normalisieren und validieren
- [ ] bestaetigtes G7-Masssystem nicht erneut als offenen Fachfehler behandeln
- [ ] Preset- und manuelle Werte nachvollziehbar vergleichen

### LES-031 Redundante Ausgabe

- [ ] identische oder Null-G0-Bewegungen ueber alle Operationen pruefen
- [ ] modale Befehle nur bei sinnvoller Zustandsaenderung ausgeben
- [ ] Robustheit bei manueller Programmbearbeitung gegen minimale Ausgabe abwaegen

### LES-032 Werkzeuggeometrie

- [ ] Nasenradius, Schneidenlage, Schneidenlaenge und Werkzeugbreite auswerten
- [ ] Innen-/Aussenwerkzeuge plausibilisieren
- [ ] Tooltable-Daten fuer Kollisions- und Erreichbarkeitspruefungen nutzen
- [ ] Werkzeugvorschau und Generator auf denselben Datensatz stuetzen

### LES-033 Gewindevorschau

- [ ] symbolische Vorschau durch Geometrie aus Steigung, Tiefe, Start und Ende ersetzen
- [ ] Innen/Aussen und Rechts/Links getrennt pruefen
- [ ] Preset, Vorschau und G76-Ausgabe nachvollziehbar abbilden

### LES-034 Preview-Pipeline

- [ ] Werkstueck-Endkontur, Werkzeugweg und Hilfs-/Sicherheitsgeometrie trennen
- [ ] keine impliziten Verbindungen oder Fantasie-Hilfslinien zeichnen
- [ ] im Zweifel weniger statt geometrisch falsche Elemente anzeigen
- [ ] komplexe Endgeometrien in Seiten- und Schnittansicht vergleichen

### LES-035 Embedded/Standalone-Paritaet

- [ ] Widget-Binding, Tooltips, Dialoge und Dateipfade vergleichen
- [ ] keine globalen Host-Widgets im Embedded-Betrieb binden
- [ ] Real-Qt-Smoke-Test fuer beide Startarten pflegen

## Offene externe Antworten und Blocker

Noch unbeantwortet in der Realtest-Datei:

- Frage 7: Startzeit und Reaktionszeit -> LES-027

Norm-/Systemabhaengige Blocker:

- DIN-76-Werte fuer M2, M2.5 und M3.5 -> LES-019
- lokale Freistichgeometrie braucht verifizierte DIN-Referenz -> LES-010
- Innen-Schruppen braucht LinuxCNC-Backplot und Trockenlauf -> LES-003
- Generatoraenderungen brauchen LinuxCNC-Simulation -> LES-030

## Verbindlicher Abschluss jeder Generatoraenderung

1. fokussierte Regression, die den alten Fehler reproduziert und mit dem Fix besteht
2. kompletter `pytest -q`-Lauf; neue oder geaenderte Skips muessen begruendet werden
3. `python3 regenerate_all_ngc.py`
4. Diff der Referenzprogramme fachlich pruefen
5. echter PyQt5-Test bei UI-, Sichtbarkeits- oder Save/Load-Aenderungen
6. LinuxCNC-Parser und Backplot bei geaenderten Fahrwegen oder Modals
7. bei G2/G3 mindestens ein Fall mit `I != 0`; Start-/Endradius zum
   ausgegebenen Zentrum muessen uebereinstimmen, direkt und in Zyklus-Subs
8. bei Innenbearbeitung steigende/fallende Konturrichtung, Materialgrenze,
   XRI-Verwendung sowie Ein-/Rueckzug getrennt pruefen
9. bei sicherheitsrelevanten Fahrwegen realen Trockenlauf dokumentieren
10. `TODO.md`, `ROADMAP.md`, `README.md`, `DEV.md` und
    `CHANGELOG.md` synchron halten

## Spaetere Erweiterungen nach stabiler 1.0-Basis

- weitergehende Keilnut- und Verzahnungsfunktionen
- weitere Maschinen-, Futter- und Werkzeugprofile
- automatisierte LinuxCNC-Simulationslaeufe
- zusaetzliche Abspanstrategien