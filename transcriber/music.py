"""Decisiones musicales sobre las notas detectadas.

Nada de esto toca el audio: entra una lista de notas y sale qué suena en cada semicorchea,
dónde empiezan los compases y qué acorde es cada uno. Son las decisiones que más se
equivocan, así que están aparte para poder probarlas con notas puestas a mano.
"""

from bisect import bisect_right
from dataclasses import dataclass
from itertools import pairwise

#: Las doce notas, como las nombra la guía.
NOTE_NAMES = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]

#: Acordes que se intentan reconocer, como distancias desde la fundamental.
CHORD_SHAPES = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10)}

#: Por debajo de esta altura MIDI cuenta como bajo, para buscar las barras de compás.
BASS_CEILING = 52


@dataclass(frozen=True)
class Meter:
    """Cómo se divide el pulso, y con eso el largo del compás.

    El compás siempre tiene cuatro pulsos, igual que antes de distinguir los compases: no se
    separa 2/4 de 4/4. Por eso un 6/8 sale escrito como 12/8, que suena igual y tiene el mismo
    pulso con puntillo cuatro veces.
    """

    #: Semicorcheas por pulso: 4 si el pulso se parte en dos, 6 si se parte en tres.
    beat_slots: int
    #: El compás tal como se escribe en la partitura.
    numerator: int
    denominator: int

    @property
    def bar_slots(self):
        """Semicorcheas por compás: 16 en simple, 24 en compuesto."""
        return 4 * self.beat_slots

    @property
    def strong(self):
        """Los dos tiempos fuertes: el primero y el tercero, donde el pulgar toca el bajo."""
        return (0, self.bar_slots // 2)


#: Compás simple: cada pulso se parte en dos (negra, corcheas, semicorcheas).
SIMPLE = Meter(4, 4, 4)

#: Compás compuesto: cada pulso se parte en tres (negra con puntillo, corcheas de tresillo).
COMPOUND = Meter(6, 12, 8)

#: Con menos ataques entre pulsos que estos no hay forma de decir cómo se parte el pulso.
MIN_ATTACKS = 8


#: Cuerdas que tiene una guitarra. Más ataques a la vez que esto no es música.
STRINGS = 6

#: Ventana en segundos dentro de la cual los ataques cuentan como simultáneos.
TOGETHER = 0.05


def drop_knocks(notes, strings=STRINGS, together=TOGETHER):
    """Quita los ataques que salen de un golpe en la caja o en el micrófono.

    Un golpe es ruido de banda ancha: el detector dispara a la vez en decenas de alturas que
    no tienen nada que ver entre sí. En el video de «Solamente uno» hay uno en el segundo 73
    que entra como un acorde de veintiséis notas.

    Una guitarra tiene seis cuerdas, así que más de seis ataques simultáneos no se pueden
    tocar: eso no es un acorde, es un porrazo. Se descarta el grupo entero, porque dentro de
    un golpe no hay forma de saber cuál de las alturas era música.

    Importa más de lo que parece, porque las amplitudes que da el detector son relativas: un
    golpe mucho más fuerte que la música deja a todo lo demás por debajo del umbral.
    """
    kept = []
    group = []
    for note in notes:
        if group and note[0] - group[0][0] >= together:
            if len(group) <= strings:
                kept.extend(group)
            group = []
        group.append(note)
    if len(group) <= strings:
        kept.extend(group)
    return kept


def clean(notes, min_amplitude=0.35, retrigger=0.08, margin=1.1):
    """Quita las notas flojas y las que son una cuerda que todavía sonaba.

    basic-pitch vuelve a detectar una altura que sigue vibrando, y eso aparece como si se
    hubiera tocado otra vez. Se descarta cuando llega muy pegada al ataque anterior y no
    suena más fuerte, pero se alarga la nota original: dejó de ser un ataque nuevo, no dejó
    de sonar.

    La distancia se mide desde el ataque anterior, no desde donde terminó. Medida desde el
    final, toda cuerda que se vuelve a pulsar mientras suena pasaba por eco, y en guitarra
    eso es casi cualquier nota repetida: en GuitarSet esta regla tiraba un tercio de las
    notas reales (de 87 % a 59 % de acierto). Desde el ataque, la melodía final sube del
    60 % al 73 % allí, y en «Solamente uno» la melodía en orden del 71 % al 77 %.
    """
    kept, last = [], {}
    for start, end, pitch, amp in notes:
        previous = last.get(pitch)
        weak = amp < min_amplitude
        echo = previous and start - previous[0] < retrigger and amp <= previous[2] * margin
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


def subdivide(gap, period, beat_slots):
    """Cuántas semicorcheas caben en el hueco entre dos golpes detectados.

    El detector de pulso se salta los golpes que no reconoce y deja huecos que valen dos
    pulsos o más. Repartir siempre cuatro semicorcheas da por bueno que cada hueco es un
    pulso, y donde no lo es la rejilla pierde tiempo y desplaza todo lo que viene después.

    La corrección va en pulsos enteros, no en semicorcheas: el detector encuentra un golpe o
    no lo encuentra, nunca se deja medio. Redondear a semicorcheas parecía más fino y era
    peor, porque entonces el vaivén normal del tempo —un hueco de pulso y cuarto en una
    grabación de guitarra sola— se convierte en una semicorchea de más que corre el resto de
    la pieza. Medido en «Solamente uno»: así bajaba del 52 % al 44 %.

    Nunca devuelve menos de un pulso: un hueco más corto es el mismo pulso medido con prisa,
    no menos música.
    """
    if period <= 0:
        return beat_slots
    return beat_slots * max(1, round(gap / period))


def grid_of(beats, period, meter):
    """El instante de cada semicorchea: cada hueco entre golpes se reparte en partes iguales."""
    grid = []
    for a, b in pairwise(float(t) for t in beats):
        count = subdivide(b - a, period, meter.beat_slots)
        step = (b - a) / count
        grid.extend(a + k * step for k in range(count))
    return grid


def beat_phases(notes, beats):
    """La fase de cada ataque dentro de su pulso, `(fase de 0 a 1, amplitud)`.

    Se cuenta desde el golpe anterior. Los ataques que caen antes del primer golpe o después
    del último no tienen pulso entre el que medirse y se saltan.
    """
    beats = [float(t) for t in beats]
    out = []
    for start, _, _, amp in notes:
        i = bisect_right(beats, start) - 1
        if 0 <= i < len(beats) - 1:
            out.append(((start - beats[i]) / (beats[i + 1] - beats[i]), amp))
    return out


def phase_bias(phases):
    """Lo que se adelanta el detector de notas al de pulso, como fracción de pulso.

    Es el mismo desfase que corrige `timing_bias` en la rejilla, y aquí hay que quitarlo
    antes de comparar: medido sobre los 144 fragmentos de GuitarSet, los ataques caen en
    mediana a -1/16 de pulso del golpe, que es justo el error medio de un reparto al azar en
    la rejilla binaria. Sin corregirlo, las dos rejillas puntúan casi igual en todo (105
    fragmentos de 4/4 salían compuestos) porque los ataques no caen exactamente en ninguna.

    Se mide sólo con los ataques que caen a menos de 1/8 de pulso del golpe, que es donde
    caen los de ambas rejillas y ninguna otra subdivisión (la más cercana es 1/4), así que el
    desfase no depende de qué rejilla sea la buena. Mediana, no promedio, por la misma razón
    que en `timing_bias`.
    """
    near = sorted(p - round(p) for p, _ in phases if abs(p - round(p)) <= 1 / 8)
    return near[len(near) // 2] if near else 0.0


def meter_errors(notes, beats):
    """Cuánto se aleja cada rejilla de los ataques: `(binaria, ternaria)`, sin unidades.

    De cada ataque se toma su fase dentro del pulso (0 a 1, contando desde el golpe anterior,
    y quitado el desfase de `phase_bias`) y se mide la distancia a la subdivisión más
    cercana. La binaria es {0, 1/4, 1/2, 3/4} y la ternaria {0, 1/3, 2/3}. La distancia
    media se pondera por la amplitud, para que un ataque débil dudoso pese menos que el golpe
    del bajo, y se divide entre lo que daría tocar al azar (1/16 y 1/12): la ternaria tiene
    menos distancia media posible, así que sin normalizar saldría favorecida siempre.

    Con menos de `MIN_ATTACKS` ataques entre pulsos devuelve `None`.
    """
    phases = beat_phases(notes, beats)
    if len(phases) < MIN_ATTACKS:
        return None
    bias = phase_bias(phases)
    binary = ternary = total = 0.0
    for phase, amp in phases:
        phase -= bias
        binary += amp * abs(phase * 4 - round(phase * 4)) / 4
        ternary += amp * abs(phase * 3 - round(phase * 3)) / 3
        total += amp
    if total <= 0:
        return None
    return binary / total * 16, ternary / total * 12


def meter_of(notes, beats):
    """Si el pulso se parte en dos (`SIMPLE`) o en tres (`COMPOUND`).

    Gana la rejilla que deja los ataques más cerca de sus puntos, según `meter_errors`. Un
    empate, o no tener ataques suficientes, da `SIMPLE`: es lo que se asumía antes y lo que
    es casi toda la música de guitarra que se transcribe aquí.
    """
    errors = meter_errors(notes, beats)
    if errors is None:
        return SIMPLE
    binary, ternary = errors
    return COMPOUND if ternary < binary else SIMPLE


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


def bar_phase(slots, meter):
    """En qué semicorchea del compás caen las barras.

    Los bajos marcan el compás: se prueba cada posición como principio y gana la que deje
    más peso grave en el primer y el tercer tiempo, contando doble el primero.

    Se prueban todas las del compás, no sólo los cuatro tiempos. El detector de pulso no pone sus
    golpes exactamente donde cae el pulso, así que la rejilla entera puede estar corrida una
    o dos semicorcheas; si sólo se prueban los tiempos no hay ninguna fase que arregle eso.
    Medido en «Solamente uno»: correr la rejilla tres semicorcheas a mano subía el arranque
    del 24 % al 63 %, y eso era justo lo que la fase no podía hacer.

    Si esto se equivoca la tablatura sale corrida, y entonces no hay nada que corregir de
    oído, hay que rehacerla.
    """
    bass_weight = {
        slot: sum(amp for pitch, amp in voices.items() if pitch < BASS_CEILING)
        for slot, voices in slots.items()
    }
    size = meter.bar_slots
    return max(
        range(size),
        key=lambda offset: (
            sum(w for slot, w in bass_weight.items() if (slot - offset) % size in meter.strong)
            + sum(w for slot, w in bass_weight.items() if (slot - offset) % size == 0)
        ),
    )


def bar_starts(slots, phase, meter):
    """Las posiciones donde empieza cada compás."""
    first, last = min(slots), max(slots)
    return list(range(first - (first - phase) % meter.bar_slots, last + 1, meter.bar_slots))


def chord_name(slots, start, meter):
    """Qué acorde suena en un compás.

    Suma la energía de cada una de las doce notas y prueba las formas conocidas. El bajo del
    primer y del tercer tiempo desempata: la misma colección de notas puede ser un acorde o
    su relativo, y lo que lo decide es qué nota está abajo.

    Los acordes de cuatro notas pagan una penalización, porque con suficientes notas
    detectadas cualquier séptima encaja y entonces todo saldría como séptima.
    """
    weight = [0.0] * 12
    bass = None
    for slot in range(start, start + meter.bar_slots):
        for pitch, amp in slots.get(slot, {}).items():
            weight[pitch % 12] += amp
            if slot - start in meter.strong and (bass is None or pitch < bass):
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
