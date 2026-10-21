"""El pulso y los inicios de compás con Beat This, sin PyTorch.

El detector de pulso de librosa se equivoca en factores simples: `salvatore` va a 60 pulsos
por minuto y lo lee a 117, los renders van a 110 y los lee a 74. No es ruido, es que elige
otro nivel métrico, y de ahí sale casi toda la diferencia entre acertar la mitad de la
melodía y acertar un 3 %.

Intenté decidir el nivel bueno con la señal: probar los factores 1/3, 1/2, 2/3, 1, 3/2, 2 y
3, y quedarme con el que tuviera más ataques en los pulsos y más regularidad entre pulsos
alternos. Falla en los cinco casos medidos y elige tempos absurdos de 300 pulsos por minuto.
El motivo es estructural y vale anotarlo: en fingerstyle hay una nota en casi cada
subdivisión, así que *cualquier* periodo cae encima de ataques y el respaldo no distingue
nada. Un criterio hecho a mano no puede resolverlo; hace falta algo que haya aprendido de
datos a qué se parece un pulso.

Beat This (Foscarin, Schlüter y Widmer, ISMIR 2024) hace eso, y además da los downbeats, que
son los inicios de compás: justo la fase que aquí se venía adivinando.

Se ejecuta en ONNX y no con PyTorch por dos razones. La primera es que el torch que hay para
esta máquina se compiló contra numpy 1 y aquí hay numpy 2, así que ni se importa. La segunda
es que el núcleo de kitara va en Rust, y un grafo ONNX se ejecuta allí con `ort`: hacerlo ya
así significa que esto no se tira a la basura al portarlo.

El preprocesado y el recorte en ventanas son los del paquete original, copiados de su
código, porque el modelo no los lleva dentro y desviarse mueve los pulsos.
"""

import numpy as np

#: Receta del modelo, de su `config.json`. No se tocan: el modelo se entrenó con esto.
SAMPLE_RATE = 22050
N_FFT = 1024
HOP = 441
MEL_BINS = 128
FPS = 50.0
LOG_MULTIPLIER = 1000

#: Ventanas con las que se parte una grabación larga, y el borde que el modelo no predice
#: bien porque no se entrenó en los extremos de cada ventana.
CHUNK = 1500
BORDER = 6

#: Un pico es máximo dentro de +-70 ms y su logit pasa de cero, que es media probabilidad.
PEAK_KERNEL = 7


def _mel_filterbank(path):
    """El banco de filtros mel que acompaña al modelo, de 513 frecuencias a 128 bandas."""
    data = np.fromfile(path, dtype=np.float32)
    return data.reshape(513, MEL_BINS)


def log_mel(samples, filterbank):
    """El espectrograma log-mel tal como lo espera el modelo, de forma (tiempo, 128).

    La división por el largo de la ventana es el `normalized="frame_length"` de torchaudio, y
    la amplitud va sin elevar al cuadrado (`power=1`). El `log1p` con multiplicador 1000
    comprime el rango: por eso un cambio de volumen no es un desplazamiento constante y la
    mezcla a mono tiene que ser la media, no una suma que preserve energía.
    """
    import librosa

    spectrum = librosa.stft(
        samples, n_fft=N_FFT, hop_length=HOP, window="hann", center=True, pad_mode="reflect"
    )
    magnitude = np.abs(spectrum) / N_FFT
    mel = magnitude.T @ filterbank
    return np.log1p(LOG_MULTIPLIER * mel).astype(np.float32)


def _windows(spect):
    """Las ventanas de 1500 cuadros y dónde empieza cada una.

    La primera y la última se rellenan con ceros por fuera, y las de en medio se solapan en
    el borde, porque los `BORDER` cuadros de cada extremo se descartan después. La última se
    corre hacia atrás para que acabe donde acaba la grabación en vez de quedar corta.
    """
    step = CHUNK - 2 * BORDER
    starts = np.arange(-BORDER, len(spect) - BORDER, step)
    if len(spect) > step:
        starts[-1] = len(spect) - (CHUNK - BORDER)
    chunks = []
    for start in starts:
        piece = spect[max(start, 0) : min(start + CHUNK, len(spect))]
        left = max(0, -start)
        right = CHUNK - len(piece) - left
        chunks.append(np.pad(piece, ((left, right), (0, 0))))
    return chunks, starts


def _join(pieces, starts, total):
    """Pega las predicciones de cada ventana quedándose con la primera que cubre cada cuadro.

    Se recorre al revés para que lo que escribe una ventana temprana sobreviva a la
    siguiente, que es el `keep_first` del original.
    """
    beat = np.full(total, -1000.0, dtype=np.float32)
    down = np.full(total, -1000.0, dtype=np.float32)
    for start, piece in reversed(list(zip(starts, pieces, strict=True))):
        inner = slice(BORDER, CHUNK - BORDER)
        target = slice(start + BORDER, start + CHUNK - BORDER)
        beat[target] = piece[0][inner]
        down[target] = piece[1][inner]
    return beat, down


def _peaks(logits):
    """Los cuadros donde hay un pico de verdad: máximo local y con probabilidad sobre media."""
    radius = PEAK_KERNEL // 2
    padded = np.pad(logits, radius, constant_values=-1000.0)
    windows = np.lib.stride_tricks.sliding_window_view(padded, PEAK_KERNEL)
    is_max = logits == windows.max(axis=1)
    return np.nonzero(is_max & (logits > 0))[0]


def _merge(frames, width=1):
    """Junta picos pegados en uno solo, puesto en su promedio."""
    if len(frames) == 0:
        return np.array([])
    result = []
    current = float(frames[0])
    count = 1
    for frame in frames[1:]:
        if frame - current <= width:
            count += 1
            current += (frame - current) / count
        else:
            result.append(current)
            current = float(frame)
            count = 1
    result.append(current)
    return np.array(result)


def track(wav, model_dir):
    """Los pulsos y los inicios de compás de una grabación, en segundos.

    Cada inicio de compás se lleva al pulso más cercano, porque un compás empieza en un
    pulso: si las dos predicciones no coinciden del todo, manda la del pulso.
    """
    import librosa
    import onnxruntime

    samples, _ = librosa.load(wav, sr=SAMPLE_RATE, mono=True)
    spect = log_mel(samples, _mel_filterbank(f"{model_dir}/mel-filterbank.bin"))

    session = onnxruntime.InferenceSession(f"{model_dir}/beat_this.onnx")
    chunks, starts = _windows(spect)
    pieces = []
    for chunk in chunks:
        out = session.run(None, {"spect": chunk[None, :, :]})
        pieces.append((out[0][0], out[1][0]))

    beat_logits, down_logits = _join(pieces, starts, len(spect))
    beats = _merge(_peaks(beat_logits)) / FPS
    downbeats = _merge(_peaks(down_logits)) / FPS

    if len(beats):
        downbeats = np.unique([beats[np.argmin(np.abs(beats - d))] for d in downbeats])
    return beats, downbeats
