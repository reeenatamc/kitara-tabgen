"""Decisiones musicales sobre las notas detectadas.

Nada de esto toca el audio: entra una lista de notas y sale qué suena en cada semicorchea,
dónde empiezan los compases y qué acorde es cada uno. Son las decisiones que más se
equivocan, así que están aparte para poder probarlas con notas puestas a mano.
"""

#: Las doce notas, como las nombra la guía.
NOTE_NAMES = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]

#: Acordes que se intentan reconocer, como distancias desde la fundamental.
CHORD_SHAPES = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10)}

#: Por debajo de esta altura MIDI cuenta como bajo, para buscar las barras de compás.
BASS_CEILING = 52

#: Semicorcheas que tiene un compás de 4/4.
BAR_SLOTS = 16


def clean(notes, min_amplitude=0.35, retrigger=0.06, margin=1.1):
    """Quita las notas flojas y las que son una cuerda que todavía sonaba.

    basic-pitch vuelve a detectar una altura que sigue vibrando, y eso aparece como si se
    hubiera tocado otra vez. Se descarta cuando llega muy pegada a la anterior y no suena
    más fuerte, pero se alarga la nota original: dejó de ser un ataque nuevo, no dejó de
    sonar.
    """
    kept, last = [], {}
    for start, end, pitch, amp in notes:
        previous = last.get(pitch)
        weak = amp < min_amplitude
        echo = previous and start < previous[1] + retrigger and amp <= previous[2] * margin
        if weak or echo:
            if previous:
                last[pitch] = (previous[0], max(previous[1], end), previous[2])
            continue
        kept.append((start, end, pitch, amp))
        last[pitch] = (start, end, amp)
    return kept


def nearest_slot(grid, time):
    """La semicorchea de la rejilla más cercana a un instante."""
    best, distance = 0, None
    for i, tick in enumerate(grid):
        gap = abs(tick - time)
        if distance is None or gap < distance:
            best, distance = i, gap
    return best


def subdivide(gap, period):
    """Cuántas semicorcheas caben en el hueco entre dos golpes detectados.

    El detector de pulso se salta los golpes que no reconoce y deja huecos que valen dos
    pulsos o más. Repartir siempre cuatro semicorcheas da por bueno que cada hueco es un
    pulso, y donde no lo es la rejilla pierde tiempo y desplaza todo lo que viene después.

    La corrección va en pulsos enteros, no en semicorcheas: el detector encuentra un golpe o
    no lo encuentra, nunca se deja medio. Redondear a semicorcheas parecía más fino y era
    peor, porque entonces el vaivén normal del tempo —un hueco de pulso y cuarto en una
    grabación de guitarra sola— se convierte en una semicorchea de más que corre el resto de
    la pieza. Medido en «Solamente uno»: así bajaba del 52 % al 44 %.

    Nunca devuelve menos de cuatro: un hueco más corto que un pulso es el mismo pulso
    medido con prisa, no menos música.
    """
    if period <= 0:
        return 4
    return 4 * max(1, round(gap / period))


def grid_step(grid):
    """Cuánto dura una semicorchea en la rejilla."""
    if len(grid) < 2:
        return 0.0
    gaps = sorted(grid[i + 1] - grid[i] for i in range(len(grid) - 1))
    return gaps[len(gaps) // 2]


def timing_bias(notes, grid):
    """El desfase sistemático entre los ataques detectados y la rejilla, en semicorcheas.

    Los dos relojes no coinciden: el detector de notas marca el ataque un poco antes de
    donde el detector de pulso pone el golpe. En «Solamente uno» son -0,25 semicorcheas, 34
    ms, y es constante de principio a fin.

    Un cuarto de semicorchea no mueve ninguna nota por sí solo, porque el redondeo aguanta
    hasta la mitad. Lo que hace es dejar la pieza entera montada cerca del borde: con ese
    margen comido, la holgura normal de tocar basta para que una nota salte a la semicorchea
    siguiente, y eso sí desplaza compases enteros.

    Se mide con la mediana y no con el promedio: unas pocas notas muy desplazadas, que es lo
    que pasa donde el modelo se equivoca, no deben mover la corrección.
    """
    step = grid_step(grid)
    if not notes or step <= 0:
        return 0.0
    offsets = sorted((start - grid[nearest_slot(grid, start)]) / step for start, *_ in notes)
    return offsets[len(offsets) // 2]


def quantize(notes, grid, inner_voices=1):
    """Qué suena en cada semicorchea: `posición -> {altura: amplitud}`.

    Se queda con la nota más aguda (la melodía), la más grave (el bajo) y la voz interna más
    fuerte. Una guitarra puede tocar seis notas a la vez, pero un borrador con todo lo que
    detecta el modelo es ilegible, y lo que hay que corregir de oído es la melodía.

    Antes se tiran los armónicos: una altura una octava o una docena por encima de otra más
    fuerte casi siempre es el armónico de esa, no una nota pisada.
    """
    by_slot = {}
    shift = timing_bias(notes, grid) * grid_step(grid)
    for start, _, pitch, amp in notes:
        slot = nearest_slot(grid, start - shift)
        current = by_slot.setdefault(slot, {})
        current[pitch] = max(current.get(pitch, 0), amp)

    out = {}
    for slot, current in by_slot.items():
        without_overtones = {
            pitch: amp
            for pitch, amp in current.items()
            if not any(current.get(pitch - d, 0) >= amp for d in (12, 19, 24))
        }
        pitches = sorted(without_overtones)
        edges = {pitches[0], pitches[-1]}
        inner = sorted(pitches[1:-1], key=lambda p: -without_overtones[p])[:inner_voices]
        out[slot] = {p: without_overtones[p] for p in edges | set(inner)}
    return out


def bar_phase(slots):
    """En qué semicorchea del compás caen las barras.

    Los bajos marcan el compás: se prueba cada uno de los cuatro tiempos como principio y
    gana el que deje más peso grave en el primero y el tercero, contando doble el primero.
    Si esto se equivoca la tablatura sale corrida, y entonces no hay nada que corregir de
    oído, hay que rehacerla.
    """
    bass_weight = {
        slot: sum(amp for pitch, amp in voices.items() if pitch < BASS_CEILING)
        for slot, voices in slots.items()
    }
    return max(
        range(0, BAR_SLOTS, 4),
        key=lambda offset: (
            sum(w for slot, w in bass_weight.items() if (slot - offset) % BAR_SLOTS in (0, 8))
            + sum(w for slot, w in bass_weight.items() if (slot - offset) % BAR_SLOTS == 0)
        ),
    )


def bar_starts(slots, phase):
    """Las posiciones donde empieza cada compás."""
    first, last = min(slots), max(slots)
    return list(range(first - (first - phase) % BAR_SLOTS, last + 1, BAR_SLOTS))


def chord_name(slots, start):
    """Qué acorde suena en un compás.

    Suma la energía de cada una de las doce notas y prueba las formas conocidas. El bajo del
    primer y del tercer tiempo desempata: la misma colección de notas puede ser un acorde o
    su relativo, y lo que lo decide es qué nota está abajo.

    Los acordes de cuatro notas pagan una penalización, porque con suficientes notas
    detectadas cualquier séptima encaja y entonces todo saldría como séptima.
    """
    weight = [0.0] * 12
    bass = None
    for slot in range(start, start + BAR_SLOTS):
        for pitch, amp in slots.get(slot, {}).items():
            weight[pitch % 12] += amp
            if slot - start in (0, 8) and (bass is None or pitch < bass):
                bass = pitch

    total = sum(weight)
    if total == 0:
        return ""

    candidates = []
    for root in range(12):
        for suffix, shape in CHORD_SHAPES.items():
            score = sum(weight[(root + step) % 12] for step in shape)
            score -= 0.5 * total * (len(shape) - 3) / 4
            if bass is not None and bass % 12 == root:
                score += 0.5 * max(weight)
            candidates.append((score, root, suffix))

    _, root, suffix = max(candidates)
    return NOTE_NAMES[root] + suffix
