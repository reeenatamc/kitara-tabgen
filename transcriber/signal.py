"""Lo que se oye: notas y pulso sacados del audio.

Es la única parte que necesita los modelos pesados. basic-pitch da las notas con su
amplitud, librosa da dónde caen los golpes. Todo lo que viene después son decisiones sobre
esos datos y vive en los otros módulos, que se pueden probar sin cargar nada.
"""

import warnings

warnings.filterwarnings("ignore")

import librosa
import numpy as np
from basic_pitch.inference import predict

from . import music


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

    Los golpes que da el detector tiemblan, y la rejilla no se interpola entre ellos: se
    ajusta un pulso constante a todos a la vez con `music.steady_grid`, que es lo que quita
    ese temblor.

    Después se extiende hacia los dos extremos con ese mismo pulso, porque el detector no
    llega al principio ni al final de la grabación y sin eso las primeras notas se quedarían
    fuera del primer compás.
    """
    y, sr = librosa.load(wav, sr=22050)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, start_bpm=100, units="time")
    tempo = float(np.atleast_1d(tempo)[0])

    grid, step = music.steady_grid([float(b) for b in beats])
    if not grid or step <= 0:
        return np.asarray(grid), tempo

    sixteenth = step / 4
    duration = len(y) / sr
    before = [grid[0] - sixteenth * i for i in range(int(np.ceil(grid[0] / sixteenth)), 0, -1)]
    after = [
        grid[-1] + sixteenth * i
        for i in range(1, int(np.ceil((duration - grid[-1]) / sixteenth)) + 1)
    ]

    return np.asarray(before + grid + after), 60.0 / step
