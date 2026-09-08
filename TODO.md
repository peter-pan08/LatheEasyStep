# TODO LatheEasyStep

Stand: 2026-09-08

Diese Datei ist die verbindliche Liste aller offenen Aufgaben. Erledigte Punkte
werden entfernt und im `CHANGELOG.md` dokumentiert. Release-Ziele und
Abhaengigkeiten stehen in der [ROADMAP.md](ROADMAP.md), reale Tests in
[doc/REALTEST_FRAGEN_2026-07-15.md](doc/REALTEST_FRAGEN_2026-07-15.md).

## Aktuell verifizierte Basis

- `main`: Version 0.7.0 als lauffaehige Basis
- `dev`: aktueller Entwicklungsstand fuer 0.8.0; `main` bleibt die stabile Basis
- Teststand: `472 passed` (Stub-Qt) und `43 passed` (echtes PyQt5),
  getrennte Prozesse ueber `python run_tests.py`, keine Skips.
- Neun Referenzprogramme regeneriert; statische NGC-Pruefung bestanden.
  LinuxCNC-Parser/Backplot fuer diese Aenderungen noch nicht ausgefuehrt.
- Umfang, Testbefehle und verbleibende Grenzen:
  [Verifikationsbericht 2026-09-08](doc/VERIFICATION_2026-09-08.md).
- UI-Shell und acht Reiter-Teil-UIs sind getrennt und werden ueber
  `lathe_easystep/ui_split.py` geladen
- `de.lng`, `en.lng` und `es.lng` enthalten jeweils 1.022 identische,
  nichtleere und eindeutige Sprachschluessel
- derzeit keine offenen GitHub-Issues; diese Datei ist der Aufgabenbestand
- Real am Panel bestaetigt (Nutzertest 2026-08-22): DIN-Freistich mitten in
  der Kontur (Vorschau UND generierter G-Code) sowie Innen-Schruppen
  erzeugen jetzt beide sinnvolle, tatsaechlich abtragende Ergebnisse -
  siehe LES-003/LES-010/LES-011

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
| LES-039 | P0 | Werkzeugwechselposition und sichere erste Freifahrt verbindlich pruefen | sehr hoch | M-L | 0.8.0-alpha |
| LES-040 | P0 | Nicht endliche Zahlen vor Geometrie und Ausgabe ablehnen | hoch | M | 0.8.0-alpha |
| LES-003 | P0 | Innen-Schruppen Parallel-Z abschliessend verifizieren | sehr hoch | L | 0.8.0-alpha |
| LES-005 | P0 | Innen-Schlichtanfahrt und Rueckzug fuer weitere Konturformen absichern | sehr hoch | M-L | 0.8.0-alpha |
| LES-006 | P1 | Rueckzugsstrategie und Achsreihenfolge je Bearbeitungsart festlegen | hoch | M | 0.8.0 |
| LES-010 | P1 | Lokale DIN-Freistichgeometrie am markierten Segment erzeugen | hoch | L | 0.8.0 |
| LES-012 | P1 | Konturprimitive bis zur finalen G1/G2/G3-Ausgabe erhalten | hoch | L | 0.8.0 |
| LES-013 | P1 | Sichere CSS-Umschaltung nach per-Operation-G96/G97 | mittel-hoch | S-M | 0.8.0 |
| LES-015 | P1 | Innenkontur-Testmatrix automatisieren und in LinuxCNC verifizieren | hoch | M-L | 0.8.0 |
| LES-019 | P1 | Verifizierte DIN-76-Presets fuer M2, M2.5 und M3.5 ergaenzen | mittel | S-M | 0.8.0 |
| LES-030 | P1 | Neue Generatorfunktionen systematisch in LinuxCNC simulieren | hoch | M-L | 0.8.0 |
| LES-037 | P0 | Freistich/Relief am Gewindeende verankern, nicht am Konturende; bei zu wenig Platz klar fehlern | sehr hoch | M | 0.8.0-alpha |
| LES-018 | P2 | G70-Wiederverwendung fuer separaten Schlichtstep pruefen | mittel | M-L | 0.9.0 |
| LES-020 | P2 | Handler in kleinen Paketen weiter verkleinern | mittel | M je Paket | 0.9.0 |
| LES-022 | P2 | Zentralen Bewegungs- und Modalzustand einfuehren | langfristig hoch | XL | 0.9.0 |
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

Ausgangsbefund (in der gemeinsamen Anfahrt inzwischen behoben):
`emit_approach()` gab bei gesetztem `_is_at_safe` einen
direkten diagonalen Zielmove aus. Der Status sagt nur, dass die vorherige
Operation an einer sicheren Position endete; er beweist nicht, dass der neue
Zielpunkt von dort direkt kollisionsfrei erreichbar ist.

- [x] direkten Zielmove nicht allein aus dem Boolean `_is_at_safe` ableiten
- [ ] sichere Achsreihenfolge anhand Start-, Ziel-, Rohteil- und Futterzone waehlen
- [ ] gleiches Werkzeug ohne dazwischenliegenden Werkzeugwechsel testen
- [ ] Aussen-Schruppen -> Schlichten und Innen-Schruppen -> Schlichten testen
- [ ] Bohren und Gewinde als Z-vor-X-Sonderfaelle pruefen
- [ ] Warnung und tatsaechlicher Fahrweg duerfen sich nicht widersprechen
- [ ] Regressionen fuer Rohteil- und Chuck-No-Go-Faelle ergaenzen

Ergaenzung aus Codepruefung 2026-09-08: `gcode_safety.emit_approach()`
erzeugt trotz erkannter Futter-Sperrzone weiterhin einen Eilgang. Lokal auf
Funktionsebene reproduziert: Rohteil XA=50, XI=0, ZA=0, ZI=-50;
relative Rueckzuege XRA=5/ZRA=5; Sperrzone X=0..100, Z<=-40;
Ziel X30/Z-45 ergibt Warnkommentare und danach `G0 X30.000 Z-45.000`.

- [x] Verletzungen der Futter-Sperrzone in `emit_approach` als blockierenden Fehler behandeln;
  ein WARN-Kommentar darf die Bewegung nicht freigeben
- [ ] gesamte Eilgangstrecke gegen Rohteil und Futterzone pruefen, auch wenn
  Start und Ziel jeweils ausserhalb liegen; beabsichtigte Schnittbewegungen
  gesondert behandeln
- [x] obigen Fall sowohl direkt als auch ueber Gesamtgenerator und Export
  testen: keine ausfuehrbare Ausgabe, bestehende G-Code-Datei bleibt erhalten

Teilstand 2026-09-08: gemeinsame Anfahrt achsweise; Futterpruefung
auch fuer kreuzende Segmente und Werkzeugwechsel in Werkstueckkoordinaten.
Noch keine vollstaendige Rohteil-/Werkzeughuellenpruefung aller direkten
Moves oder Zyklen; angenommene Safe-Position ersetzt keinen Positionsnachweis.

### LES-039 Werkzeugwechselposition und erste Freifahrt absichern

Codepruefung 2026-09-08: `gcode_safety.append_tool_and_spindle()` gibt bei
fehlendem XT/ZT nach einer Warnung trotzdem `T01 M6` aus (lokal reproduziert).
`ui_flow.build_gcode_lines()` verlangt XT/ZT erst bei mindestens zwei
unterschiedlichen Werkzeugen. Vor dem ersten Wechsel wird zudem pauschal
Z vor X freigefahren, ohne Ausgangsposition und aktuell eingesetztes Werkzeug
zu kennen. Ein noch im Einstich stehendes Werkzeug ist ein Kollisionsrisiko;
dieses Szenario wurde nicht an der Maschine getestet.

- [x] XT/ZT fuer jedes ausgegebene T/M6 verlangen,
  auch bei nur einem Werkzeug; fehlende notwendige XT/ZT blockieren die Ausgabe
- [ ] Startbedingungen fuer Position, aktives Werkzeug und freien Eingriff
  explizit festlegen und pruefen; unbekannten Zustand nicht als sicher annehmen
- [ ] erste Freifahrt passend zu Werkzeug und Eingriff planen; kein pauschales
  Z-vor-X bei einem im Einstich stehenden Werkzeug
- [ ] Wechselposition und Hin-/Rueckweg im ausgewaehlten Koordinatensystem
  pruefen; mit LES-001, LES-006 und LES-022 abstimmen
- [ ] Einzelwerkzeug ohne XT/ZT, mehrere Werkzeuge, Innenwerkzeug und
  Stechwerkzeug im Eingriff als Regressionen plus LinuxCNC-Simulation abdecken

Teilstand: fehlendes XT/ZT blockiert auch Einzelwerkzeugprogramme.
G53-Hin-/Rueckwege koennen ohne Maschinenoffsets nicht gegen die
Werkstueck-Sperrzone geprueft werden. Erste Freifahrt bleibt offen.

### LES-040 Nicht endliche Zahlen zentral ablehnen

Codepruefung 2026-09-08: `gcode_utils.require_positive()` akzeptiert
`"nan"` und `"inf"` (lokal reproduziert). `float()` und reine
Groessenvergleiche sichern die Geometrie und Ausgabe daher nicht ausreichend.

- [x] gemeinsame Zahlenvalidierung mit `math.isfinite()` vor Berechnung und
  Ausgabe einsetzen, einschliesslich geladener Programm-/Step-Daten
- [ ] Koordinaten, Vorschuebe, Drehzahlen, Zustellungen und Sicherheitswerte
  auf Endlichkeit und fachlich passende Wertebereiche pruefen
- [x] Werkzeugnummern als gueltige ganze Zahlen validieren statt Dezimalwerte
  still mit `int(float(...))` abzuschneiden; mit LES-028 abstimmen
- [ ] NaN, positive/negative Unendlichkeit, ungueltige Texte und Grenzwerte
  testen; Fehler muss vor Bewegungsplanung und Dateiersetzung auftreten

Teilstand: NaN/Inf an Import-, Modell- und Gesamtgeneratorgrenzen
blockiert; defekte X/Z-Punkte werden nicht mehr still uebersprungen.
Regressionsfaelle fuer Zahlen, Werkzeugnummern und Dateierhalt vorhanden.
Fachliche Wertebereiche aller Operationen und direkter Generatoraufrufe
bleiben vollstaendig durchzugehen (LES-028).

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

Der urspruenglich gemeldete Fehler ("keine wirkliche Abspanaufgabe
generiert") ist jetzt ebenfalls behoben: `rough_turn_parallel_x()` nutzte
eine viel zu schmale Fenster-Intersection (`x_cut +/- 1e-3`), die pro
X-Band meist gar kein Kontursegment traf ("no cut region"), waehrend ein
anderes Band zufaellig eine lange senkrechte Bohrungswand komplett in
einem einzigen Schnitt zusammenfasste. Ersetzt durch eine
"Materialreichweite"-Baenderung (pro `x_cut` wird der volle Z-Bereich
gesucht, in dem die Zielkontur ueber diese Tiefe hinausgeht) - real fuer die
Nutzerkontur "ausdrehen" verifiziert (9 gleichmaessige Einzelzustellungen
statt eines Riesenschnitts) und mit `rs274` fehlerfrei ausgefuehrt. Test:
`tests/test_internal_roughing_uses_g71_cycle.py::test_internal_roughing_with_real_bore_contour_produces_even_stepped_passes`.

- [ ] `XRI` nur als sichere Einfahr-/Rueckzugsebene verwenden, niemals als
  Schnittbahn; Regression muss jeden G1-Profilwert gegen diese Grenze pruefen
- [x] Schlichtaufmass X/Z fuer Innenkonturen korrekt ausrichten
- [ ] automatisierte Faelle fuer monoton steigende UND fallende Z-Konturen
  sowie Innen-/Aussenbearbeitung pflegen
- [x] `examples.py` um Innen-Abspanen (`Innen_Stufe.ngc`, `side=inside`)
  ergaenzen; automatisiert getestet und regeneriert, reale Abnahme unten offen
- [ ] LinuxCNC-Parser, Backplot und Trockenlauf mit diesem Referenzteil
  dokumentieren (P0 - vor Praxiseinsatz zwingend)

Teilstand: positive vorhandene Bohrung XI bleibt Materialgrenze;
Zylinder, Stufe und Konus jeweils in beiden Konturrichtungen und drei
Bearbeitungsmodi automatisiert getestet (18 Kombinationen). XRI-Grenze,
mehrere Zustellungen und reines Schlichten ohne erneutes Schruppen geprueft.
Innenradius, Werkzeughuelle und reale Abnahme bleiben offen.

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

### LES-037 Freistich/Relief am Gewindeende verankern

Automatische DIN-Freistiche werden aus der Gewindeoperation abgeleitet und
nur in eine passende zylindrische Aussen-/Innenkontur eingespleisst. Das
G76-Ende liegt um die DIN-Ueberdeckung `f` innerhalb der Freistichbreite;
fehlt die gesamte Konturstrecke, bricht die Erzeugung sicher ab. Vorschau,
Schlichtweg und Kontur-Subroutine verwenden dieselben Primitive.

- [ ] realen Aussen- und Innengewinde-Fall mit automatischem Freistich im
  LinuxCNC-Backplot und Trockenlauf abnehmen

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

Freistiche werden jetzt an JEDEM Segment erzeugt, nicht mehr nur am ersten
oder letzten Segment der gesamten Kontur (real gegen den LinuxCNC-
Interpreter verifiziert: sauberer, fehlerfreier Parse eines Freistichs
mitten in einer Welle, siehe CHANGELOG.md). Aussen- und Innenfreistich sind
beide bestaetigt korrekt.

- [ ] DIN-76-Geometrie (Breite/Tiefe je Gewindegroesse) gegen eine
  verifizierte Norm-Referenz pruefen - die Platzierung ist jetzt korrekt,
  die hinterlegten Zahlenwerte selbst sind noch nicht extern verifiziert
  (siehe LES-019, "keine Werte schaetzen")
- [x] Referenzbeispiel `Freistich_Mitte.ngc` in `examples.py` und Regeneration

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

### LES-019 Fehlende DIN-76-Presets

- [ ] verifizierte Normwerte fuer M2, M2.5 und M3.5 beschaffen
- [ ] Aussen- und Innenvarianten ergaenzen
- [ ] Datenvalidierung und Preset-Tests erweitern
- [ ] keine Werte schaetzen

### LES-030 LinuxCNC-Simulationsmatrix

- [x] alle neun Referenzprogramme nach Generatoraenderungen regenerieren
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

Teilstand: `validate_ngc.py` prueft statisch, `check_linuxcnc.py` ist
als separater rs274-Batchlauf vorbereitet. Hier fehlt der Interpreter;
synthetische Werkzeugtabelle ersetzt keine Maschinenkonfiguration.

### LES-036 Kantenform "Radius" beim Planen

Radius ist implementiert; Vorschau und G-Code verwenden gemeinsame
Primitive. Externe Parser-/Backplot- und Panelabnahme bleiben offen.

- [x] Radius-Eckengeometrie fuer den 90-Grad-Planen-Spezialfall umsetzen
- [x] Durchmesser-/Radiusumrechnung fuer X sowie G2/G3-I/K eindeutig herleiten
- [x] String-IDs und alte numerische Save-Dateien weiterhin unterstuetzen
- [x] Vorschau und G-Code aus derselben Geometrie ableiten
- [x] Grenzfaelle pruefen: Radius 0, zu grosser Radius, Schruppen,
  Schlichten und Schruppen+Schlichten
- [x] echten PyQt5-Roundtrip testen
- [ ] LinuxCNC-Parser/Backplot testen
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

- [x] Programmkopf-Sammlung
- [x] Kontursegment-Sammlung
- [x] Gewinde-Preset-UI nach `ui_thread.py`
- [ ] Widget-Bootstrapping
- [x] Tooltip-Erzwingung nach `ui_tooltips.py`

### LES-022 Zentraler Bewegungs- und Modalzustand

- [ ] aktuelle X/Z-Position bei jeder Move-Emission mitfuehren
- [ ] G90/G91, G94/G95, G96/G97, G18 und G40/G41/G42 verwalten
- [ ] M3/M4/M5, M7/M8/M9 und Werkstuecknullpunkt verwalten
- [ ] sichere Pfadentscheidungen auf reale aktuelle Position stuetzen
- [ ] robuste explizite Ausgabe fuer manuell bearbeitbaren G-Code erhalten

### LES-024 Restliche UI-Modularisierung

- [ ] Vorschau/Schnittansicht in eigene UI-Struktur auslagern
- [ ] Step-Liste und Programmverwaltung auslagern
- [ ] je Modul Controller, Tooltips, Sprach-IDs und Validierung zuordnen
- [ ] direkte Widgetzugriffe zwischen Modulen durch definierte Schnittstellen ersetzen
- [ ] Embedded- und Standalone-Laden testen

### LES-027 Performance

Realtest-Frage 7 ist beantwortet, aber alarmierend: "startzeit momentan
wieder über 20 sec, also viel zu lange" - das Wort "wieder" deutet auf eine
Regression hin (fruehere Startzeit war offenbar besser). Noch nicht
root-caused; keine Codeaenderung in dieser Session dazu.

- [ ] Root Cause fuer die aktuell >20s Startzeit finden (Profiling: welcher
  Schritt dominiert - `.ui`-Laden, Preview-Erstaufbau, Sprachkatalog,
  Tool-Table-Laden, HAL/Qt-Init?)
- [ ] pruefen, ob ein frueherer Commit/eine frühere Version schneller war
  (git bisect auf Startzeit, falls reproduzierbar messbar)
- [ ] Startzeit bis sichtbares und bedienbares Panel messen
- [ ] Embedded und Standalone vergleichen
- [ ] Reiterwechsel, Stepwechsel und Preview-Refresh messen

### LES-028 Eingaben zentral normalisieren

Teilstand: G76 blockiert ungueltige Steigung, Tiefe, Durchmesser, Laenge,
R/H/L und Taperlaenge; Zahlenstrings werden gleichwertig ausgewertet,
explizites H=0 bleibt erhalten. Null fuer automatische Schnitttiefen bleibt
kompatibel. Werkzeugnummern werden nicht mehr dezimal abgeschnitten.


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

- [ ] Vorschau und G-Code auf denselben geplanten Bewegungen aufbauen,
  einschliesslich Anfahrt, Rueckzug, Werkzeugwechsel und Parken; gemeinsame
  Grundlage mit LES-022 und LES-041 abstimmen
- [ ] dargestellten Werkzeugweg fuer Referenzprogramme gegen die tatsaechliche
  Ausgabe und den LinuxCNC-Backplot vergleichen (siehe LES-030)
- [ ] Werkstueck-Endkontur, Werkzeugweg und Hilfs-/Sicherheitsgeometrie trennen
- [ ] keine impliziten Verbindungen oder Fantasie-Hilfslinien zeichnen
- [ ] im Zweifel weniger statt geometrisch falsche Elemente anzeigen
- [ ] komplexe Endgeometrien in Seiten- und Schnittansicht vergleichen

### LES-035 Embedded/Standalone-Paritaet

- [ ] Widget-Binding, Tooltips, Dialoge und Dateipfade vergleichen
- [ ] keine globalen Host-Widgets im Embedded-Betrieb binden
- [ ] Real-Qt-Smoke-Test fuer beide Startarten pflegen

## Offene externe Antworten und Blocker

Alle bisher gestellten Realtest-Fragen sind beantwortet (Frage 7:
Startzeit >20s, siehe LES-027 - Antwort deutet auf eine Regression hin
und ist noch nicht root-caused). Fragen 16 und 18 wurden vom Nutzer
ausdruecklich ohne reale Testpflicht freigegeben ("das kann mit einem
Testprogramm geregelt werden") und sind durch automatisierte Tests plus
`rs274`-Verifikation bereits erfuellt - deshalb aus der Realtest-Datei
entfernt.

Norm-/Systemabhaengige Blocker:

- DIN-76-Werte fuer M2, M2.5 und M3.5 -> LES-019
- lokale Freistichgeometrie braucht verifizierte DIN-Referenz -> LES-010
- Innen-Schruppen braucht LinuxCNC-Backplot und Trockenlauf -> LES-003
- Generatoraenderungen brauchen LinuxCNC-Simulation -> LES-030

## Verbindlicher Abschluss jeder Generatoraenderung

1. fokussierte Regression, die den alten Fehler reproduziert und mit dem Fix besteht
2. kompletter `python run_tests.py`-Lauf (Stub und Real-Qt getrennt); neue oder geaenderte Skips muessen begruendet werden
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
