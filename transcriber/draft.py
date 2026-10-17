"""Arma el borrador: de las posturas colocadas al JSON de la canción y su guía.

La parte fina es rellenar los huecos. Entre dos ataques puede haber un hueco que no es una
figura sola —cinco semicorcheas no son ninguna figura—, así que se parte en figuras que sí
existen y las de en medio van ligadas a la anterior. Sin eso el compás no suma y el
validador lo rechaza.
"""

from .guitar import TUNING, fit_range, notation
from .music import BAR_SLOTS, NOTE_NAMES, chord_name

#: Figuras disponibles, en semicorcheas y de mayor a menor.
FIGURES = (16, 12, 8, 6, 4, 3, 2, 1)

#: A partir de esta altura MIDI una nota cuenta como melodía y se acentúa.
MELODY_FLOOR = 57

#: Compases por sección, mientras no haya forma detectada de verdad.
BARS_PER_SECTION = 8


#: Dónde puede caer el bajo del pulgar: de la cuarta cuerda hacia abajo.
BASS_RANGE = (40, 55)

#: Desde esta altura una nota es de los dedos, no del pulgar, y se deja como se oyó.
BASS_FLOOR = 56

#: Los tiempos donde el pulgar pone fundamental y quinta.
THUMB_BEATS = (0, 8)


def thumb_bass(chord, slot):
    """La altura que toca el pulgar en ese tiempo, o nada si no hay acorde.

    En fingerstyle el pulgar lleva negras constantes alternando la fundamental y la quinta
    del acorde: es el esqueleto de la pieza, y lo que hace que un arreglo suene armónico
    aunque la melodía de arriba vaya sincopada.

    Se escribe el bajo que el acorde pide, no el que el detector midió. Un bajo detectado a
    medias deja huecos que suenan a error; una alternancia regular suena a música, y si el
    acorde está bien es además lo que se toca de verdad.
    """
    if not chord:
        return None
    root = NOTE_NAMES.index(chord.rstrip("m7"))
    wanted = root if slot == THUMB_BEATS[0] else (root + 7) % 12
    low, high = BASS_RANGE
    for pitch in range(low, high + 1):
        if pitch % 12 == wanted:
            return pitch
    return None


def harmonize(slots, starts, chords):
    """Cambia el bajo detectado por la alternancia regular del pulgar.

    Deja la melodía y las voces internas tal como se oyeron, y reescribe sólo el registro
    grave: fundamental en el primer tiempo, quinta en el tercero, nada en los demás.

    Es la diferencia entre transcribir y arreglar. Lo detectado en el grave viene a trozos
    —el detector pierde ataques del pulgar porque quedan tapados— y esos huecos suenan a
    error. La alternancia regular suena a música, y donde el acorde está bien acertado es
    además lo que se toca de verdad.

    El precio es que deja de ser literal: si el acorde se detectó mal, el bajo sale mal con
    seguridad en vez de salir a medias. Por eso lo que más vale la pena mejorar ahora es la
    detección de acordes, que es lo que sostiene todo esto.
    """
    bass_by_bar = {}
    for start, chord in zip(starts, chords, strict=True):
        for beat in THUMB_BEATS:
            pitch = thumb_bass(chord, beat)
            if pitch is not None:
                bass_by_bar[start + beat] = pitch

    harmonized = {}
    for slot, voices in slots.items():
        upper = {p: a for p, a in voices.items() if p >= BASS_FLOOR}
        if slot in bass_by_bar:
            upper[bass_by_bar[slot]] = max(voices.values(), default=0.7)
        if upper:
            harmonized[slot] = upper

    # Los tiempos del pulgar que no tenían nada detectado también llevan su bajo.
    for slot, pitch in bass_by_bar.items():
        harmonized.setdefault(slot, {pitch: 0.7})

    return harmonized


#: Cuánto se tienen que parecer dos compases para contarlos como el mismo motivo.
SAME_BAR = 0.55

#: En qué fracción de las repeticiones tiene que aparecer una nota para quedarse.
MAJORITY = 0.5


def bar_signature(slots, start):
    """Las notas de un compás como posiciones relativas a su barra."""
    return {
        (slot - start, pitch)
        for slot in range(start, start + BAR_SLOTS)
        for pitch in slots.get(slot, {})
    }


def similarity(a, b):
    """Qué fracción comparten dos compases, de 0 a 1."""
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if (a | b) else 0.0


def group_repeats(signatures, threshold=SAME_BAR):
    """Agrupa los compases que son el mismo motivo tocado otra vez.

    Una pieza de fingerstyle repite: la versión escrita a mano de «Solamente uno» cubre
    treinta y cuatro compases con unos quince motivos con nombre. El transcriptor trataba
    cada compás como nuevo, así que cada uno cargaba sus propios errores de detección.
    """
    groups = []
    for i, signature in enumerate(signatures):
        for group in groups:
            if similarity(signature, signatures[group[0]]) >= threshold:
                group.append(i)
                break
        else:
            groups.append([i])
    return groups


def vote(signatures, group, majority=MAJORITY):
    """Las notas que aparecen en la mayoría de las repeticiones de un motivo.

    Es lo que limpia el borrador sin tocar nada del detector: una nota que suena en cinco
    de las seis pasadas es música, y una que sale en una sola es un fallo. Las repeticiones
    se corrigen unas a otras.
    """
    counts = {}
    for i in group:
        for note in signatures[i]:
            counts[note] = counts.get(note, 0) + 1
    needed = max(1, round(len(group) * majority))
    return {note for note, count in counts.items() if count >= needed}


def unify_repeats(slots, starts):
    """Escribe igual los compases que son el mismo motivo, votando entre sus repeticiones.

    Si un motivo aparece seis veces, las seis salen con lo que coincidió en la mayoría. Eso
    quita las notas que el detector inventó una sola vez y recupera las que perdió en
    algunas pasadas, y además hace que la pieza suene coherente: un arreglo donde el mismo
    compás suena distinto cada vez no se oye como música, se oye como un error.
    """
    signatures = [bar_signature(slots, start) for start in starts]
    groups = group_repeats(signatures)

    unified = {}
    for group in groups:
        agreed = vote(signatures, group)
        for i in group:
            start = starts[i]
            for offset, pitch in agreed:
                amplitude = slots.get(start + offset, {}).get(pitch, 0.6)
                unified.setdefault(start + offset, {})[pitch] = amplitude
    return unified


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
