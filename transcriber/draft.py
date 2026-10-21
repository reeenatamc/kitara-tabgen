"""Arma el borrador: de las posturas colocadas al JSON de la canción y su guía.

La parte fina es rellenar los huecos. Entre dos ataques puede haber un hueco que no es una
figura sola —cinco semicorcheas no son ninguna figura—, así que se parte en figuras que sí
existen y las de en medio van ligadas a la anterior. Sin eso el compás no suma y el
validador lo rechaza.
"""

from .guitar import TUNING, fit_range, notation
from .music import NOTE_NAMES, chord_name

#: Figuras disponibles, en semicorcheas y de mayor a menor. La de 24 es la redonda con
#: puntillo: el compás entero de 12/8.
FIGURES = (24, 16, 12, 8, 6, 4, 3, 2, 1)

#: A partir de esta altura MIDI una nota cuenta como melodía y se acentúa.
MELODY_FLOOR = 57

#: Compases por sección, mientras no haya forma detectada de verdad.
BARS_PER_SECTION = 8


#: Dónde puede caer el bajo del pulgar: de la cuarta cuerda hacia abajo.
BASS_RANGE = (40, 55)

#: Desde esta altura una nota es de los dedos, no del pulgar, y se deja como se oyó.
BASS_FLOOR = 56


def thumb_bass(chord, slot, meter):
    """La altura que toca el pulgar en ese tiempo, o nada si no hay acorde.

    En fingerstyle el pulgar lleva negras constantes alternando la fundamental y la quinta
    del acorde: es el esqueleto de la pieza, y lo que hace que un arreglo suene armónico
    aunque la melodía de arriba vaya sincopada.

    Es el bajo que el acorde pide, no uno medido: `harmonize` lo usa sólo para rellenar los
    tiempos donde el detector no oyó ningún bajo. La fundamental va en el primer tiempo fuerte
    del compás y la quinta en el segundo (`meter.strong`).
    """
    if not chord:
        return None
    root = NOTE_NAMES.index(chord.rstrip("m7"))
    wanted = root if slot == meter.strong[0] else (root + 7) % 12
    low, high = BASS_RANGE
    for pitch in range(low, high + 1):
        if pitch % 12 == wanted:
            return pitch
    return None


def harmonize(slots, starts, chords, meter):
    """Completa el pulgar donde el detector lo perdió, sin borrar el bajo que se oyó.

    En fingerstyle el pulgar pone fundamental en el primer tiempo y quinta en el tercero.
    El detector pierde algunos de esos ataques porque quedan tapados, y esos huecos suenan a
    error. Así que, si en esos tiempos no hay ningún bajo, se escribe el que pide el acorde.

    Sólo se completa en los compases donde el bajo oído trae la fundamental del acorde.
    El acorde se adivina, y cuando se adivina mal el pulgar escrito es un bajo que nadie
    tocó: sin esa confirmación, en el cover de «Salvatore» siete de cada diez bajos escritos
    no sonaban en la grabación.

    Antes este paso borraba todo el grave y lo reescribía con la alternancia. Sonaba a
    música, pero en GuitarSet dejaba el bajo en 12 % de acierto cuando lo detectado tenía
    81 %. Conservándolo, el acierto total del borrador pasa del 49 % al 76 %, y en
    «Solamente uno» el bajo en su sitio del 69 % al 76 %. El precio es un borrador más
    cargado: el pulgar escrito era más simple que lo que se toca.
    """
    harmonized = {slot: dict(voices) for slot, voices in slots.items()}
    for start, chord in zip(starts, chords, strict=True):
        if not chord or not _root_is_heard(slots, start, chord, meter):
            continue
        for beat in meter.strong:
            pitch = thumb_bass(chord, beat, meter)
            voices = harmonized.setdefault(start + beat, {})
            if pitch is not None and not any(p < BASS_FLOOR for p in voices):
                voices[pitch] = max(voices.values(), default=0.7)
    return harmonized


def _root_is_heard(slots, start, chord, meter):
    """Si algún bajo detectado en el compás es la fundamental del acorde."""
    root = NOTE_NAMES.index(chord.rstrip("m7"))
    return any(
        pitch % 12 == root
        for slot in range(start, start + meter.bar_slots)
        for pitch in slots.get(slot, {})
        if pitch < BASS_FLOOR
    )


def _melody_string(combo):
    """La cuerda que lleva la melodía, para acentuarla. Nada si el pulso es sólo bajo."""
    sounds_high = any(
        fit_range(TUNING[string - 1] + fret) >= MELODY_FLOOR for string, fret in combo
    )
    return min(combo)[0] if sounds_high else None


def bar_events(placed, start, meter):
    """Un compás en los eventos que entiende tabgen.

    Cada ataque ocupa desde su posición hasta el siguiente, repartido en figuras reales. La
    primera lleva la postura completa con dedos; las demás repiten las notas ligadas.
    """
    size = meter.bar_slots
    hits = [slot for slot in range(start, start + size) if slot in placed]
    marks = [start, *hits] if not hits or hits[0] != start else hits

    events = []
    for n, slot in enumerate(marks):
        end = marks[n + 1] if n + 1 < len(marks) else start + size
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


def chords_of(slots, starts, meter):
    """El acorde de cada compás."""
    return [chord_name(slots, start, meter) for start in starts]


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


def metadata(title, bpm, meter):
    """La cabecera del borrador. La etiqueta deja claro que no es una tablatura acabada.

    `bpm` son pulsos por minuto, pero alphaTab mide el tempo en negras. En simple el pulso es
    una negra y coinciden; en compuesto el pulso es una negra con puntillo, que vale una
    negra y media, y el tempo en negras es una vez y media el del pulso.
    """
    return {
        "title": title,
        "artist": "",
        "tab_author": "borrador automático",
        "source_url": "",
        "tempo_bpm": float(round(bpm * meter.beat_slots / 4)),
        "tags": ["borrador"],
    }
