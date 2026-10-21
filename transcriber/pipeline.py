"""El recorrido de las reglas, de las notas detectadas a lo que suena en cada semicorchea.

Está en un solo sitio porque lo usan dos programas: `transcribe.py`, que hace el borrador, y
`bench.py`, que lo mide. Si cada uno repitiera los pasos, bastaría con cambiar uno para que
el banco midiera algo distinto de lo que se entrega, sin que nada avisara.
"""

from dataclasses import dataclass

from . import draft, music


@dataclass(frozen=True)
class Stages:
    """Lo que deja cada paso, para poder medir dónde se pierde o se inventa una nota."""

    cleaned: list
    meter: music.Meter
    grid: list
    heard: dict
    starts: list
    chords: list
    slots: dict


def run(notes, beats, period):
    """Aplica las reglas en orden a las notas y los pulsos de `signal`.

    Primero se decide cómo se parte el pulso, porque de eso depende la rejilla, y de la
    rejilla todo lo demás: dónde caen las semicorcheas, el largo del compás y los tiempos
    fuertes. Se decide con las notas ya limpias, que son las que se van a colocar.
    """
    cleaned = music.clean(music.drop_knocks(notes))
    meter = music.meter_of(cleaned, beats)
    grid = music.grid_of(beats, period, meter)
    heard = music.quantize(cleaned, grid)
    starts = music.bar_starts(heard, music.bar_phase(heard, meter), meter)
    chords = draft.chords_of(heard, starts, meter)
    slots = draft.harmonize(heard, starts, chords, meter)
    return Stages(cleaned, meter, grid, heard, starts, chords, slots)
