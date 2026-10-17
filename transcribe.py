"""Borrador de tablatura desde una grabación.

Las notas las da basic-pitch, el pulso librosa, y las cuerdas y trastes salen de buscar el
menor movimiento de mano. El resultado es un borrador para corregir de oído, no una
transcripción: cada posición guarda su nota más aguda (la melodía), el bajo y una voz
interna.

Medido contra la versión a mano de «Solamente uno»: acierta la forma y los acordes, y poco
más de la mitad de la melodía. Donde el pulso es parejo sale casi completa; donde se toca
libre o la cuadrícula se corre, se pierde.

Uso: transcribe.py audio.wav cancion.json guia.json "Título"
"""

import sys

from tabgen import write_guide, write_song
from transcriber import draft, guitar, music, signal


def main(wav, song_path, guide_path, title):
    notes = signal.detect_notes(wav)
    grid, bpm = signal.beat_grid(wav)
    heard = music.quantize(music.clean(music.drop_knocks(notes)), grid)

    starts = music.bar_starts(heard, music.bar_phase(heard))
    chords = draft.chords_of(heard, starts)

    # El bajo se escribe, no se copia: el pulgar del fingerstyle es una alternancia regular
    # y los huecos del detector en el grave suenan a error.
    slots = draft.harmonize(heard, starts, chords)

    placed = guitar.place(slots)

    plan = [(draft.bar_events(placed, start), "MP", False) for start in starts]

    score = write_song(
        song_path,
        draft.metadata(title, bpm),
        0,
        draft.sections_of(len(plan)),
        plan,
        chords=draft.only_on_change(chords),
    )
    write_guide(guide_path, score, draft.guide_steps(chords))

    detected = sum(len(voices) for voices in slots.values())
    print("notas %d, tempo %d, compases %d" % (detected, round(bpm), len(plan)))
    print("acordes:", " ".join(chord or "-" for chord in chords))


if __name__ == "__main__":
    main(*sys.argv[1:5])
