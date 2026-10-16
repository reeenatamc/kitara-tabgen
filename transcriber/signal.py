"""Lo que se oye: notas y pulso sacados del audio.

Es la única parte que necesita los modelos pesados. basic-pitch da las notas con su
amplitud, librosa da dónde caen los golpes. Todo lo que viene después son decisiones sobre
esos datos y vive en los otros módulos, que se pueden probar sin cargar nada.
"""

import warnings
from itertools import pairwise

warnings.filterwarnings("ignore")

import librosa
import numpy as np
from basic_pitch.inference import predict

from . import music

#: Cuánto se insiste en separar lo percusivo de lo armónico antes de buscar el pulso.
#: Más alto deja menos señal pero más limpia de ataques; 3 es lo que arregló el render de
#: «Solamente uno» sin estropear los casos que ya salían bien.
PERCUSSIVE_MARGIN = 3.0


def detect_notes(wav):
    """Notas del audio, ordenadas por cuándo empiezan.

    Devuelve tuplas `(inicio, fin, altura MIDI, amplitud)`.

    Los límites de frecuencia recortan por abajo el ruido de la caja y por arriba los
    armónicos: una guitarra con cejilla no llega a 1400 Hz ni en la primera cuerda.
    """
    _, _, events = predict(
        wav,
        onset_threshold=0.5,
        frame_threshold=0.3,
        minimum_note_length=80,
        minimum_frequency=75,
        maximum_frequency=1400,
    )
    return sorted((start, end, pitch, amp) for start, end, pitch, amp, _ in events)


def beat_grid(wav):
    """Los instantes de cada semicorchea, y el tempo que sale de ellos.

    El detector de pulso se guía por los ataques, así que antes se separa la parte percusiva
    de la armónica y se le da sólo esa. Las cuerdas sostenidas confunden: en el render de
    «Solamente uno» el detector daba 74 pulsos por minuto donde la pieza va a 110, y con el
    realce da 108. Donde ya acertaba no cambia nada.

    Lo que no arregla es el tempo al doble o a la mitad. `salvatore` va a 60 y se detecta a
    117, que es una lectura musicalmente válida —cada compás sale partido en dos— pero
    entonces las barras no se corresponden con la tablatura escrita a mano.

    La rejilla se extiende hacia los dos extremos con el mismo periodo, porque el detector
    no llega al principio ni al final de la grabación, y sin eso las primeras notas se
    quedarían fuera del primer compás.
    """
    y, sr = librosa.load(wav, sr=22050)
    tempo, beats = librosa.beat.beat_track(
        y=librosa.effects.percussive(y, margin=PERCUSSIVE_MARGIN),
        sr=sr,
        start_bpm=100,
        units="time",
    )
    tempo = float(np.atleast_1d(tempo)[0])
    period = float(np.median(np.diff(beats)))

    before = int(np.ceil(beats[0] / period)) + 1
    after = int(np.ceil((len(y) / sr - beats[-1]) / period)) + 1
    beats = np.concatenate(
        [
            beats[0] - period * np.arange(before, 0, -1),
            beats,
            beats[-1] + period * np.arange(1, after + 1),
        ]
    )

    grid = np.concatenate(
        [
            np.linspace(a, b, music.subdivide(b - a, period), endpoint=False)
            for a, b in pairwise(beats)
        ]
    )
    return grid, 60.0 / period if period else tempo
