"""De alturas a cuerdas y trastes, buscando que la mano se mueva lo menos posible.

Una nota se puede pisar en varias cuerdas y un acorde tiene muchas posturas. Lo que decide
no es cada nota por separado sino la secuencia: la postura buena es la que deja la mano
cerca de donde ya estaba. Eso se resuelve sobre el pasaje entero, no eligiendo la más cómoda
de cada compás, porque la más cómoda aislada puede dejar la mano lejos de la siguiente.
"""

import itertools

#: Altura MIDI de cada cuerda al aire, de la primera a la sexta.
TUNING = [64, 59, 55, 50, 45, 40]

#: Hasta qué traste se considera tocable.
MAX_FRET = 17

#: Cuántos trastes abarca la mano sin moverse.
MAX_SPAN = 3

#: Los dedos, en el orden en que los nombra la guía.
FINGERS = "IMAÑ"


def fit_range(pitch):
    """Sube o baja la nota por octavas hasta que quepa en el instrumento."""
    while pitch < TUNING[-1]:
        pitch += 12
    while pitch > TUNING[0] + MAX_FRET:
        pitch -= 12
    return pitch


def voicings(pitches):
    """Todas las formas de pisar esas alturas en cuerdas distintas y bajo una mano.

    Devuelve tuplas de `(cuerda, traste)`. Se descartan las que repiten cuerda, que son
    imposibles, y las que abren más de lo que alcanza la mano.
    """
    options = [
        [
            (string + 1, pitch - open_pitch)
            for string, open_pitch in enumerate(TUNING)
            if 0 <= pitch - open_pitch <= MAX_FRET
        ]
        for pitch in pitches
    ]

    found = []
    for combo in itertools.product(*options):
        if len({string for string, _ in combo}) < len(combo):
            continue
        fretted = [fret for _, fret in combo if fret > 0]
        if fretted and max(fretted) - min(fretted) > MAX_SPAN:
            continue
        found.append(combo)
    return found


def hand_position(combo, previous):
    """En qué traste queda la mano. Si todo va al aire, se queda donde estaba."""
    fretted = [fret for _, fret in combo if fret > 0]
    return min(fretted) if fretted else previous


def voicing_cost(combo):
    """Lo que cuesta una postura por sí sola: abrir la mano y subir por el mástil."""
    fretted = [fret for _, fret in combo if fret > 0]
    if not fretted:
        return 0.0
    span = max(fretted) - min(fretted)
    return 0.3 * span + 0.04 * min(fretted)


def _layers(slots):
    """Para cada posición, las alturas que caben y sus posturas posibles.

    Si un acorde no cabe bajo una mano se le quitan voces internas, de la más grave hacia
    arriba. La melodía y el bajo no se tocan: son lo que hace reconocible la pieza.
    """
    layers = []
    for slot in sorted(slots):
        pitches = sorted({fit_range(p) for p in slots[slot]}, reverse=True)
        while True:
            options = voicings(pitches)
            if options or len(pitches) == 1:
                break
            pitches = pitches[:1] + pitches[2:]
        layers.append((pitches, options))
    return layers


def place(slots):
    """Cuerdas y trastes de cada posición, con la mano moviéndose lo menos posible.

    Para cada postura candidata se guarda el camino más barato que llega a ella, y al final
    se reconstruye hacia atrás.

    Devuelve `posición -> (postura, traste donde queda la mano)`.
    """
    keys = sorted(slots)
    layers = _layers(slots)

    paths = [{i: (0.0, None, hand_position(combo, 0)) for i, combo in enumerate(layers[0][1])}]
    for _, options in layers[1:]:
        previous = paths[-1]
        current = {}
        for i, combo in enumerate(options):
            local = voicing_cost(combo)
            fretted = [fret for _, fret in combo if fret > 0]
            best = None
            for j, (cost, _, previous_position) in previous.items():
                here = hand_position(combo, previous_position)
                jump = abs(here - previous_position) if fretted else 0
                total = cost + local + jump
                if best is None or total < best[0]:
                    best = (total, j, here)
            current[i] = best
        paths.append(current)

    node = min(paths[-1], key=lambda n: paths[-1][n][0])
    chosen = []
    for depth in range(len(paths) - 1, -1, -1):
        chosen.append((layers[depth][1][node], paths[depth][node][2]))
        node = paths[depth][node][1]
    chosen.reverse()
    # strict=True: hay exactamente una postura por posición, y si no, es un error.
    return dict(zip(keys, chosen, strict=True))


def notation(combo, position, accented_string):
    """La postura en la notación que entiende tabgen: `cuerda:traste:dedo:marca`.

    El dedo sale de la distancia al traste donde está la mano, que es como se digita de
    verdad: el índice en la posición y los demás por detrás.
    """
    tokens = []
    for string, fret in combo:
        finger = FINGERS[min(3, fret - position)] if fret > 0 else ""
        mark = "a" if string == accented_string else ""
        tokens.append("%d:%d:%s:%s" % (string, fret, finger, mark))
    return " ".join(tokens)
