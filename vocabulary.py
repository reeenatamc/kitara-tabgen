"""El vocabulario de ritmos de las tablaturas escritas a mano, y para qué sirve.

Las tablaturas hechas a mano no son compases cualesquiera: 30 moldes de ritmo cubren 195 de
sus 199 compases, y uno solo —corcheas seguidas, o sea ataque en las semicorcheas 0 2 4 6 8
10 12 14— cubre 91. Eso es una idea previa de qué posiciones suelen estar ocupadas, y es
justo lo que le faltaba al transcriptor.

Para qué importa: el detector de pulso no se equivoca por poco, elige otro nivel métrico.
`salvatore` va a 60 pulsos por minuto y librosa lo lee a 117; los renders van a 110 y los lee
a 74. Intenté decidir el nivel con la señal, puntuando cuántos ataques caen encima de los
pulsos, y falla en los cinco casos: en fingerstyle hay nota en casi cada subdivisión, así que
*cualquier* periodo cae encima de ataques y no hay nada que distinguir.

Con el vocabulario sí se distingue, porque un tempo al doble produce compases que no se
parecen a ningún molde conocido. Medido en los cinco casos con tempo escrito a mano, y
sacando cada canción de su propio vocabulario para no hacerse la prueba con las respuestas
delante: acierta los cinco, donde librosa acierta dos.

```
                       escrito  librosa  vocabulario
salvatore                   60      117           59
solamente-uno (video)      110      112          112
solamente-uno (render)     110       74          111
solamente-uno (facil)      110       74          111
hasta-siempre              100       99           99
```

El vocabulario sale de las tablaturas propias y no de un dataset a propósito: no hay ninguno
público de fingerstyle acústico simbólico con licencia abierta y acordes anotados. DadaGP es
por solicitud y tira a rock y metal, GOAT es guitarra eléctrica, mySongBook es de pago, y
GuitarSet —que sí es CC BY 4.0 y está descargado— son 30 progresiones de comping
improvisado: sirve para validar la cobertura, no como fuente del vocabulario.

Uso: `vocabulary.py [ruta a kitara]` imprime el vocabulario y su cobertura.
"""

import json
import sys
from collections import Counter
from pathlib import Path

#: La afinación estándar, de la primera cuerda a la sexta, en alturas MIDI.
TUNING = (64, 59, 55, 50, 45, 40)

#: Semicorcheas por compás de 4/4, que es la rejilla en la que se escriben los moldes.
SLOTS = 16

#: Las canciones escritas a mano, que son la única verdad disponible.
SONGS = (
    "solamente-uno",
    "solamente-uno-facil",
    "solamente-uno-melodica",
    "salvatore",
    "hasta-siempre-lo-mejor",
)

#: Los factores con los que un detector de pulso se equivoca de nivel métrico: la mitad, el
#: doble, y las confusiones entre binario y ternario, que son las que explican el 110 leído
#: como 74.
FACTORS = (1 / 3, 1 / 2, 2 / 3, 1.0, 3 / 2, 2.0, 3.0)

#: Un molde entra en el vocabulario si aparece al menos dos veces. Los que aparecen una sola
#: vez son el compás concreto de una canción concreta, no un patrón.
MIN_TIMES = 2


def bar_shapes(score):
    """En qué semicorcheas hay ataque en cada compás de una partitura."""
    shapes = []
    for bar in score["tracks"][0]["staves"][0]["bars"]:
        position = 0.0
        hits = set()
        for beat in bar["voices"][0]["beats"]:
            if any(not note.get("tie_destination") for note in beat.get("notes", [])):
                hits.add(int(position))
            position += 16 / beat["duration"] * (1.5 if beat.get("dots") else 1)
        if hits:
            shapes.append(tuple(sorted(hits)))
    return shapes


def shapes_from(repo, exclude=()):
    """El vocabulario de moldes y cuántas veces aparece cada uno.

    `exclude` saca canciones del vocabulario, y hace falta para medir sin trampa: comprobar
    una canción con su propia tablatura dentro es hacerse la prueba con las respuestas
    delante, porque el molde exacto de cada compás está ahí por construcción.
    """
    counter = Counter()
    for slug in SONGS:
        if slug in exclude:
            continue
        path = Path(repo) / "songs" / f"{slug}.json"
        if not path.exists():
            continue
        with open(path) as handle:
            counter.update(bar_shapes(json.load(handle)))
    return Counter({shape: n for shape, n in counter.items() if n >= MIN_TIMES})


def fit(hits, vocabulary):
    """Cuánto se parece el ritmo de un compás al molde más cercano, de 0 a 1.

    Se compara con la proporción de posiciones compartidas sobre la unión, para que no gane
    un molde sólo por tener muchos ataques. Y se pesa por lo frecuente que es el molde:
    parecerse al más común dice más que parecerse a uno raro.
    """
    if not hits or not vocabulary:
        return 0.0
    total = sum(vocabulary.values())
    best = 0.0
    for shape, count in vocabulary.items():
        shared = len(set(hits) & set(shape))
        union = len(set(hits) | set(shape))
        weight = min(0.5 + 0.5 * (count / total) * len(vocabulary), 1.5)
        best = max(best, (shared / union) * weight)
    return best


def grid_support(onsets, start, period, span, vocabulary):
    """Lo bien que encajan los compases en el vocabulario con este pulso y esta fase."""
    bar = period * 4
    if bar <= 0 or span / bar < 4:
        return 0.0
    scores = []
    edge = start
    while edge + bar <= span:
        inside = [t for t in onsets if edge <= t < edge + bar]
        hits = {int(round((t - edge) / bar * SLOTS)) % SLOTS for t in inside}
        if hits:
            scores.append(fit(tuple(sorted(hits)), vocabulary))
        edge += bar
    return sum(scores) / len(scores) if scores else 0.0


def choose_level(onsets, first_beat, period, span, vocabulary):
    """El periodo y la fase que dejan los compases más parecidos al vocabulario.

    Devuelve `(periodo, fase en semicorcheas, nota)`. Se prueban los factores de `FACTORS`
    sobre el periodo que dio el detector, y dentro de cada uno las dieciséis fases del
    compás, porque la rejilla entera puede ir corrida y entonces ninguna de las cuatro
    posiciones de tiempo fuerte arregla nada.
    """
    best = (period, 0, 0.0)
    for factor in FACTORS:
        candidate = period * factor
        step = candidate * 4 / SLOTS
        for shift in range(SLOTS):
            score = grid_support(onsets, first_beat + shift * step, candidate, span, vocabulary)
            if score > best[2]:
                best = (candidate, shift, score)
    return best


def main(repo):
    vocabulary = shapes_from(repo)
    print(f"{len(vocabulary)} moldes, {sum(vocabulary.values())} compases cubiertos\n")
    for shape, count in vocabulary.most_common():
        print(f"  x{count:<4d} {' '.join(str(slot) for slot in shape)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "Documents/GitHub/kitara"))
