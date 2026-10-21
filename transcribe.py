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
from transcriber import draft, guitar, pipeline, signal


def main(wav, song_path, guide_path, title):
    notes = signal.detect_notes(wav)
    beats, period = signal.beats(wav)
    bpm = 60.0 / period

    # Las reglas van en `pipeline` para que `bench.py` mida exactamente las mismas.
    stages = pipeline.run(notes, beats, period)
    starts, chords, slots, meter = stages.starts, stages.chords, stages.slots, stages.meter

    placed = guitar.place(slots)

    plan = [(draft.bar_events(placed, start, meter), "MP", False) for start in starts]

    score = write_song(
        song_path,
        draft.metadata(title, bpm, meter),
        0,
        draft.sections_of(len(plan)),
        plan,
        chords=draft.only_on_change(chords),
        time_signature=(meter.numerator, meter.denominator),
    )
    write_guide(guide_path, score, draft.guide_steps(chords))

    detected = sum(len(voices) for voices in slots.values())
    print(
        "notas %d, tempo %d, compás %d/%d, compases %d"
        % (detected, round(bpm), meter.numerator, meter.denominator, len(plan))
    )
    print("acordes:", " ".join(chord or "-" for chord in chords))


if __name__ == "__main__":
    main(*sys.argv[1:5])
