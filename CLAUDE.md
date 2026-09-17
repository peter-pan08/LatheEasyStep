# Verbindliche Hinweise für Agenten

Diese Datei gilt für jede Sitzung, jeden Agenten und jeden Task in diesem
Projekt - unabhängig davon, wer oder was sie aufruft.

## Vor und während der Arbeit: Doku lesen und pflegen

- **README.md**, **TODO.md** und **CHANGELOG.md** vor Beginn einer Aufgabe
  lesen (mindestens die relevanten Abschnitte) - sie enthalten den
  verbindlichen Stand offener Arbeiten, bekannter Grenzen und bereits
  getroffener Entscheidungen. Nicht ohne diesen Kontext an bestehender
  Logik weiterarbeiten.
- Nach jeder inhaltlichen Änderung (Code, Verhalten, Testabdeckung) diese
  drei Dateien synchron halten: neue/geänderte Punkte in TODO.md
  abhaken/ergänzen, CHANGELOG.md um einen datierten Eintrag erweitern,
  README.md bei Verhaltensänderungen sichtbar für Nutzer anpassen. Siehe
  auch `TODO.md` → "Verbindlicher Abschluss jeder Generatoraenderung".
- DEV.md ebenfalls konsultieren/pflegen - dort stehen Architekturdetails
  und laufende Teilstand-Notizen, die TODO.md ergänzen.

## Vor dem Testen: LinuxCNC-Verfügbarkeit prüfen

Testabdeckung mit `pytest`/`run_tests.py` prüft nur die Generatorlogik
dieses Projekts, nicht ob der erzeugte G-Code von einem echten LinuxCNC-
Interpreter akzeptiert wird. Deshalb vor jeder Sitzung, in der G-Code-
Ausgabe oder Fahrwege geändert werden, prüfen, ob ein echter LinuxCNC-
Interpreter (`rs274`) verfügbar ist:

- **Linux/native LinuxCNC:** `which rs274` bzw. direkt
  `python3 check_linuxcnc.py --interpreter rs274` versuchen.
- **Windows:** prüfen, ob WSL mit einer LinuxCNC-Installation vorhanden
  ist, z. B.:
  ```
  wsl --list --quiet
  wsl -e bash -lc "which rs274"
  ```
  Falls vorhanden, das Projekt liegt unter Windows i. d. R. unter
  `/mnt/c/...` - Referenzen und ggf. die Matrix damit prüfen:
  ```
  wsl -e bash -lc "cd /mnt/c/Pfad/zum/Projekt && python3 check_linuxcnc.py --interpreter rs274"
  wsl -e bash -lc "cd /mnt/c/Pfad/zum/Projekt && python3 check_linuxcnc.py --interpreter rs274 --input-dir tests/_local/linuxcnc_matrix"
  ```
  (`tests/_local/linuxcnc_matrix` ggf. vorher mit
  `regenerate_linuxcnc_matrix.py` erzeugen.)

Ist ein echter Interpreter verfügbar, **immer** zusätzlich zur
Pytest-Suite damit verifizieren, bevor eine sicherheits- oder
fahrwegrelevante Änderung als abgeschlossen gilt (siehe TODO.md →
"Verbindlicher Abschluss jeder Generatoraenderung", Punkt 6/9). Ist kein
Interpreter verfügbar, das explizit vermerken (wie bisher in
TODO.md/CHANGELOG.md dokumentiert) statt es stillschweigend auszulassen.

## LinuxCNC-Konfigurationsdateien: das Panel selbst darf nur lesen, niemals schreiben

Das **Panel-Programm** (`lathe_easystep_handler.py` und alle
`lathe_easystep/`-Module - der Code, den ein Anwender bei sich auf dem
Rechner laufen lässt) darf LinuxCNC-Konfigurationsdateien - dazu zählt
insbesondere die Werkzeugtabelle (`tool.tbl` oder wie auch immer der
Anwender seine Datei nennt) - ausschließlich **lesen**, niemals schreiben
oder verändern. Die `tool.tbl` wird von LinuxCNC selbst erzeugt/verwaltet;
ein Schreibzugriff durch das Panel kann zu Problemen mit LinuxCNC führen.
Das Panel darf ausschließlich das schreiben, was zum Programm selbst
gehört: `.lse`-Programmdateien, Step-Dateien und erzeugter G-Code (NGC).
Das ist eine feste, dauerhafte Grenze für das Panel-Programm
(nutzerbestätigt 2026-09-17), keine Scoping-Frage, die später neu bewertet
werden darf - auch nicht, wenn ein "Zurückschreiben"-Feature
architektonisch naheliegend erscheint (z. B. als Erweiterung von
`parse_tool_table()`/`Tool.unknown_fields` in `lathe_easystep/tools.py`).

**Davon zu unterscheiden:** Änderungen an der lokalen SIM-Konfiguration
(`sim.qtdragon_lathe/...`) im Rahmen der Entwicklungsarbeit selbst (z. B.
Testaufbau anpassen) sind erlaubt - diese Regel betrifft nur, was das
fertige Panel-Programm zur Laufzeit auf dem Rechner eines Anwenders tut,
nicht Entwicklungstätigkeiten an der SIM-Umgebung in diesem Repo.
