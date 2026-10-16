"""Arma el borrador: de las posturas colocadas al JSON de la canción y su guía.

La parte fina es rellenar los huecos. Entre dos ataques puede haber un hueco que no es una
figura sola —cinco semicorcheas no son ninguna figura—, así que se parte en figuras que sí
existen y las de en medio van ligadas a la anterior. Sin eso el compás no suma y el
validador lo rechaza.
"""

from .guitar import TUNING, fit_range, notation
from .music import BAR_SLOTS, chord_name

#: Figuras disponibles, en semicorcheas y de mayor a menor.
FIGURES = (16, 12, 8, 6, 4, 3, 2, 1)

#: A partir de esta altura MIDI una nota cuenta como melodía y se acentúa.
MELODY_FLOOR = 57

#: Compases por sección, mientras no haya forma detectada de verdad.
BARS_PER_SECTION = 8


def _melody_string(combo):
    """La cuerda que lleva la melodía, para acentuarla. Nada si el pulso es sólo bajo."""
    sounds_high = any(
        fit_range(TUNING[string - 1] + fret) >= MELODY_FLOOR for string, fret in combo
    )
    return min(combo)[0] if sounds_high else None


def bar_events(placed, start):
    """Un compás en los eventos que entiende tabgen.

    Cada ataque ocupa desde su posición hasta el siguiente, repartido en figuras reales. La
    primera lleva la postura completa con dedos; las demás repiten las notas ligadas.
    """
    hits = [slot for slot in range(start, start + BAR_SLOTS) if slot in placed]
    marks = [start, *hits] if not hits or hits[0] != start else hits

    events = []
    for n, slot in enumerate(marks):
        end = marks[n + 1] if n + 1 < len(marks) else start + BAR_SLOTS
        if slot in placed:
            combo, position = placed[slot]
            first = notation(combo, position, _melody_string(combo))
            tied = " ".join("%d:%d::t" % (string, fret) for string, fret in combo)
        else:
            first = tied = ""

        at, text = slot, first
        while at < end:
            step = next(figure for figure in FIGURES if figure <= end - at)
            events.append((at - start, text))
            at += step
            text = tied
    return events


def chords_of(slots, starts):
    """El acorde de cada compás."""
    return [chord_name(slots, start) for start in starts]


def only_on_change(chords):
    """El acorde sólo se escribe cuando cambia; repetirlo en cada compás ensucia la hoja."""
    return [chord if i == 0 or chord != chords[i - 1] else "" for i, chord in enumerate(chords)]


def sections_of(bar_count):
    """Secciones provisionales, de ocho compases.

    La forma de verdad (estrofa, coro, puente) no se detecta todavía: esto sólo parte la
    pieza en trozos manejables para que la guía no sea una lista de cincuenta pasos.
    """
    return [
        ("Verso", "Parte %d" % (i // BARS_PER_SECTION + 1), i, min(i + BARS_PER_SECTION, bar_count))
        for i in range(0, bar_count, BARS_PER_SECTION)
    ]


def guide_steps(chords):
    """Un paso de guía por compás, avisando de que hay que revisarlo de oído."""
    return [
        {
            "step": i // 2 + 1,
            "section": "Parte %d" % (i // BARS_PER_SECTION + 1),
            "mood": "",
            "chord": chord,
            "cue": "",
            "tip": "Borrador automático: revisa este compás de oído contra el video.",
        }
        for i, chord in enumerate(chords)
    ]


def metadata(title, bpm):
    """La cabecera del borrador. La etiqueta deja claro que no es una tablatura acabada."""
    return {
        "title": title,
        "artist": "",
        "tab_author": "borrador automático",
        "source_url": "",
        "tempo_bpm": float(round(bpm)),
        "tags": ["borrador"],
    }
