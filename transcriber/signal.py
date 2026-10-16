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

    librosa sólo marca los golpes donde los reconoce, así que la rejilla se extiende hacia
    atrás y hacia delante con el mismo periodo: si la grabación empieza con una nota antes
    del primer golpe detectado, sin eso se quedaría fuera del primer compás.
    """
    y, sr = librosa.load(wav, sr=22050)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, start_bpm=100, units="time")
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

    grid = np.concatenate([np.linspace(a, b, 4, endpoint=False) for a, b in pairwise(beats)])
    return grid, 60.0 / period if period else tempo
