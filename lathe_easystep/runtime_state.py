"""Zentraler Panel-Laufzeitzustand (LES-052, vierte Etappe).

Ersetzt die bisherigen neun losen Handler-Attribute durch ein einzelnes
typisiertes Objekt (`handler._runtime`). Qt-frei. Acht der neun Felder sind
reine Reentranz-Sperren nach demselben Muster: `if state.x: return`,
`state.x = True`, dann im `finally`-Block `state.x = False` - verhindert,
dass ein doppelt gefeuertes Qt-Signal (z. B. ein versehentlicher Doppel-
klick) dieselbe Aktion zweimal parallel ausfuehrt. `ui_loading` ist
semantisch anders: es unterdrueckt Signal-Reaktionen (Dirty-Markierung,
Parameter-Uebernahme) waehrend ein Step/Programm programmatisch in die
Formularfelder zurueckgeschrieben wird, damit dieses Zurueckschreiben nicht
selbst als Nutzeraenderung gewertet wird.

Bewusst NICHT Teil dieser Klasse: eine `guard()`-Kontextmanager-Abstraktion
fuer das wiederkehrende Reentranz-Muster - das waere eine echte
Verhaltens-/Strukturaenderung an den Aufrufstellen, nicht nur eine
Verschiebung des Speicherorts, und damit ausserhalb des Umfangs dieser
Kapselung (siehe DirtyState/ToolTableState fuer dasselbe Prinzip: Aufruf-
stellen aendern nur den Attributzugriff, nicht ihre Struktur)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuntimeState:
    loading_step: bool = False
    deleting: bool = False
    saving_step: bool = False
    saving_changes: bool = False
    moving_up: bool = False
    moving_down: bool = False
    generating_gcode: bool = False
    creating_new_program: bool = False
    ui_loading: bool = False


__all__ = ["RuntimeState"]
