"""Salvatore (Lana Del Rey), own arrangement for solo guitar. Capo 2, A minor shapes, sounds in B minor.

Melody and harmony transcribed from the album recording (quarter = 60). Frets count from the capo.
Usage: salvatore.py song.json guide.json
"""

import sys

from tabgen import thicken, write_guide, write_song

AM, G, E, F = "Lam", "Sol", "Mi", "Fa"

# name: (events, chord, tip)
P = {
    "I1": (
        [
            (0, "5:0"),
            (2, "4:2:M"),
            (4, "3:2:A"),
            (6, "2:1:I"),
            (8, "1:0"),
            (10, "2:1:I"),
            (12, "3:2:A"),
            (14, "4:2:M"),
        ],
        AM,
        "Arma La menor y deja la mano quieta. El pulgar toca la cuerda 5 y los otros dedos suben y bajan.",
    ),
    "I2": (
        [
            (0, "6:3:A"),
            (2, "4:0"),
            (4, "3:0"),
            (6, "2:0"),
            (8, "2:3:Ñ"),
            (10, "2:0"),
            (12, "3:0"),
            (14, "4:0"),
        ],
        G,
        "Solo pisas el bajo de Sol en la cuerda 6. El meñique entra un momento en la cuerda 2.",
    ),
    "I3": (
        [
            (0, "6:3:A"),
            (2, "4:0"),
            (4, "3:0"),
            (6, "2:3:Ñ"),
            (8, "6:0"),
            (10, "4:2:A"),
            (12, "3:1:I"),
            (14, "2:0"),
        ],
        "Sol, Mi",
        "Medio compás en Sol y medio en Mi. En el tiempo 3 sueltas todo y armas Mi.",
    ),
    "I4": (
        [(0, "5:0"), (2, "4:2:M"), (4, "3:2:A"), (6, "2:1:I"), (8, "1:0"), (12, "3:2:A")],
        AM,
        "La menor otra vez. Deja sonar la cuerda 1 al aire antes de entrar a la estrofa.",
    ),
    "V1": (
        [
            (0, "3:2:A:a 5:0"),
            (1, "2:1:I:a"),
            (2, "3:2:A:a"),
            (4, "4:2:M"),
            (6, "5:0"),
            (8, "2:3:Ñ:a"),
            (10, "1:0::a"),
            (12, "4:2:M"),
            (14, "2:0::a"),
            (15, "2:1:I:a"),
        ],
        AM,
        "La melodía empieza grave, en la cuerda 3. No sueltes La menor: el meñique sube solo al traste 3.",
    ),
    "V2": (
        [
            (0, "2:0::a 6:3:A"),
            (2, "4:0"),
            (4, "3:0"),
            (5, "2:3:Ñ:a"),
            (8, "6:3:A"),
            (10, "4:0"),
            (12, "3:0"),
            (14, "3:2:M:a"),
            (15, "2:0::a"),
        ],
        G,
        "Bajo de Sol con el anular. Casi todo son cuerdas al aire, así que la mano descansa.",
    ),
    "V3": (
        [
            (0, "3:2:M:a 4:3:A"),
            (2, "2:1:I"),
            (4, "3:2:M"),
            (6, "2:1:I"),
            (8, "4:3:A"),
            (10, "2:1:I"),
            (12, "3:2:M"),
            (15, "2:1:I:a"),
        ],
        F,
        "Fa chiquito: anular en la cuerda 4, medio en la 3, índice en la 2. La nota larga es la de la cuerda 3.",
    ),
    "V4": (
        [
            (0, "3:1:I:a 6:0"),
            (2, "4:2:A"),
            (4, "5:2:M"),
            (6, "4:2:A"),
            (8, "6:0"),
            (10, "4:2:A"),
            (12, "3:1:I:a"),
            (14, "4:2:A"),
        ],
        E,
        "Mi mayor. La melodía se queda quieta en la cuerda 3, traste 1.",
    ),
    "V5": (
        [
            (0, "3:2:A:a 5:0"),
            (1, "2:1:I:a"),
            (2, "3:2:A:a"),
            (4, "4:2:M"),
            (6, "2:3:Ñ:a"),
            (8, "1:0::a 5:0"),
            (10, "1:0::a"),
            (12, "1:0::a"),
            (14, "2:0::a"),
            (15, "2:1:I:a"),
        ],
        AM,
        "Igual que el primer compás de la estrofa, pero la melodía sube y repite la cuerda 1 al aire tres veces.",
    ),
    "V6": (
        [
            (0, "2:0::a 6:3:A"),
            (1, "3:2:M:a"),
            (3, "3:0::a"),
            (4, "4:0"),
            (6, "3:0"),
            (8, "6:3:A"),
            (10, "4:0"),
            (12, "3:0"),
            (14, "3:0::a"),
        ],
        G,
        "La melodía baja tres escalones seguidos: cuerda 2 al aire, cuerda 3 traste 2, cuerda 3 al aire.",
    ),
    "V7": (
        [
            (0, "3:2:M:a 4:3:A"),
            (2, "2:1:I"),
            (4, "3:2:M"),
            (6, "2:1:I"),
            (8, "4:3:A"),
            (10, "3:2:M"),
            (12, "2:1:I:a"),
            (15, "3:2:M:a"),
        ],
        F,
        "Fa chiquito otra vez. Al final la melodía toca la cuerda 2 y vuelve a la 3.",
    ),
    "V8": (
        [
            (0, "3:1:I:a 6:0"),
            (2, "4:2:A"),
            (4, "5:2:M"),
            (6, "4:2:A"),
            (8, "6:0"),
            (10, "4:2:A"),
            (12, "1:0::a"),
            (13, "1:1:I:a"),
            (14, "1:0::a"),
            (15, "2:3:Ñ:a"),
        ],
        E,
        "Mi mayor. Las cuatro notas rápidas del final son la entrada del coro: aire, traste 1, aire, y meñique en la cuerda 2.",
    ),
    "C1": (
        [
            (0, "1:0::a 5:0"),
            (2, "3:2:A"),
            (4, "2:1:I"),
            (6, "3:2:A"),
            (8, "1:0::a 5:0"),
            (10, "3:2:A"),
            (12, "2:1:I"),
            (14, "1:0::a"),
        ],
        AM,
        "El coro canta en la cuerda 1 al aire. Tócala más fuerte que el resto para que se oiga encima.",
    ),
    "C2": (
        [
            (0, "1:0::a 6:3:A"),
            (2, "3:0"),
            (3, "2:3:Ñ:a"),
            (4, "4:0"),
            (6, "3:0"),
            (8, "6:3:A"),
            (10, "3:0"),
            (12, "2:3:Ñ:a"),
            (14, "2:3:Ñ:a"),
            (15, "2:2:M:a"),
        ],
        G,
        "La melodía baja un escalón: de la cuerda 1 al aire al meñique en la cuerda 2, traste 3. Déjalo pisado.",
    ),
    "C3": (
        [
            (0, "2:3:Ñ:a 6:3:A"),
            (2, "3:0"),
            (4, "2:3:Ñ:a"),
            (6, "4:0"),
            (7, "2:2:M:a"),
            (8, "2:3:Ñ:a 6:0"),
            (10, "3:1:I"),
            (12, "1:1:I:a"),
            (14, "1:0::a"),
        ],
        "Sol, Mi",
        "Aquí va Cacciatore. El meñique repite su nota, y al final el índice se acuesta en el traste 1 para la cuerda 1.",
    ),
    "C4": (
        [
            (0, "1:0::a 5:0"),
            (2, "3:2:A"),
            (4, "2:1:I"),
            (6, "3:2:A"),
            (8, "5:0"),
            (10, "3:2:A"),
            (12, "1:0::a"),
            (13, "1:1:I:a"),
            (14, "1:0::a"),
            (15, "2:3:Ñ:a"),
        ],
        AM,
        "Descanso en La menor y otra vez las cuatro notas rápidas de entrada.",
    ),
    "C6": (
        [
            (0, "1:0::a 6:3:A"),
            (2, "3:0"),
            (3, "2:3:Ñ:a"),
            (4, "4:0"),
            (6, "3:0"),
            (8, "6:3:A"),
            (10, "3:0"),
            (12, "2:3:Ñ:a"),
            (13, "2:1:I:a"),
            (14, "2:0::a"),
            (15, "3:2:M:a"),
        ],
        G,
        "Empieza igual que antes, pero termina con una escalera hacia abajo: traste 3, traste 1, aire, y cuerda 3.",
    ),
    "C7": (
        [
            (0, "3:1:I:a 6:0"),
            (2, "4:2:A"),
            (4, "5:2:M"),
            (5, "2:1:I:a"),
            (6, "2:0::a"),
            (7, "3:2:M:a"),
            (8, "3:1:I:a 6:0"),
            (10, "4:2:A"),
            (12, "2:3:Ñ:a"),
            (13, "2:1:I:a"),
            (14, "2:0::a"),
        ],
        E,
        "Aquí va Limousines. Mi mayor con el índice acostado en el traste 1 para alcanzar la cuerda 2.",
    ),
    "C8": (
        [
            (0, "2:0::a 5:0"),
            (2, "3:2:A:a"),
            (4, "4:2:M"),
            (6, "3:2:A"),
            (8, "5:0"),
            (10, "4:2:M"),
            (12, "3:2:A"),
        ],
        AM,
        "La frase cae a La menor y descansa.",
    ),
    "B1": (
        [
            (0, "1:5:I:pa 5:0"),
            (1, "1:7:A:a"),
            (3, "2:5:I 3:5:I"),
            (5, "1:0::a"),
            (6, "3:5:I:a"),
            (7, "1:0::a"),
            (8, "1:5:I:pa 5:0"),
            (9, "1:7:A:a"),
            (11, "2:5:I 3:5:I"),
            (13, "1:0::a"),
            (14, "3:5:I:a"),
            (15, "1:0::a"),
        ],
        "Lam en el traste 5",
        "Sube la mano: índice acostado en el traste 5 sobre las cuerdas 1, 2 y 3. El anular martilla el traste 7 sin volver a pulsar.",
    ),
    "B2": (
        [
            (0, "1:1:I:pa 4:3:A"),
            (1, "1:3:Ñ:a"),
            (3, "3:2:M"),
            (5, "2:1:I:a"),
            (6, "3:2:M"),
            (8, "1:1:I:pa 4:3:A"),
            (9, "1:3:Ñ:a"),
            (11, "3:2:M"),
            (13, "2:1:I:a"),
            (14, "3:2:M:a"),
        ],
        F,
        "La misma figura, abajo: índice acostado en el traste 1 y el meñique martilla el traste 3 de la cuerda 1.",
    ),
    "B3": (
        [
            (0, "6:0"),
            (2, "4:2:A"),
            (4, "3:1:I"),
            (5, "1:0::a"),
            (8, "6:0"),
            (10, "4:2:A"),
            (12, "3:1:I"),
            (13, "2:3:Ñ:a"),
        ],
        E,
        "Mi mayor tranquilo. La melodía son solo dos notas largas: cuerda 1 al aire y luego meñique en la cuerda 2.",
    ),
    "B4": (
        [
            (0, "2:1:I:a 5:0"),
            (2, "3:2:A"),
            (4, "4:2:M"),
            (6, "3:2:A"),
            (8, "5:0"),
            (10, "4:2:M"),
            (12, "1:2:M:a"),
            (14, "1:4:Ñ:a"),
        ],
        AM,
        "La menor. Las dos notas del final suben por la cuerda 1, trastes 2 y 4, para volver al traste 5.",
    ),
    "B8": (
        [
            (0, "2:1:I:a 5:0"),
            (2, "3:2:A"),
            (4, "4:2:M"),
            (6, "3:2:A"),
            (8, "5:0"),
            (10, "4:2:M"),
            (12, "1:0::a"),
            (13, "1:1:I:a"),
            (14, "1:0::a"),
            (15, "2:3:Ñ:a"),
        ],
        AM,
        "La menor y las cuatro notas rápidas que devuelven al coro.",
    ),
    "O1": (
        [(0, "5:0"), (4, "4:2:M"), (8, "3:2:A"), (12, "2:1:I")],
        AM,
        "La menor, una cuerda por tiempo, cada vez más lento.",
    ),
    "O2": (
        [(0, "5:0"), (4, "3:12::n"), (8, "1:12::n")],
        "Lam con armónicos",
        "Roza la cuerda justo encima del traste 12, sin apretar, y suelta el dedo apenas suene.",
    ),
    "O3": (
        [(0, "1:0 2:1:I 3:2:A 4:2:M 5:0")],
        AM,
        "Último acorde: arrastra el pulgar despacio desde la cuerda 5 hasta la 1.",
    ),
}

FULL = {AM: "2:1:I 3:2:A 4:2:M", G: "2:0 3:0 4:0", E: "4:2:A 5:2:M"}
PAIRS = {
    AM: {"3:2": "4:2:M", "2:1": "3:2:A", "4:2": "3:2:A"},
    G: {"3:0": "4:0", "4:0": "3:0"},
    E: {"4:2": "5:2:M", "5:2": "4:2:A", "3:1": "4:2:A"},
}
STRONG_TIP = " Ahora con más cuerdas debajo: la melodía es la misma del primer coro."
for name in ("C1", "C2", "C3", "C4", "C6", "C7", "C8"):
    events, chord, tip = P[name]
    if name == "C3":
        strong = thicken(events, FULL[G], {**PAIRS[G], **PAIRS[E]}, FULL[E])
    else:
        strong = thicken(events, FULL[chord], PAIRS[chord])
    P[name + "P"] = (strong, chord, tip + STRONG_TIP)
# Before the bridge the chorus ends climbing string 1 towards fret 5.
P["C8B"] = (
    [*P["C8P"][0][:-1], (12, "1:2:M:a"), (14, "1:4:Ñ:a")],
    AM,
    "La frase cae a La menor. Las dos notas del final suben por la cuerda 1, trastes 2 y 4, hacia el puente.",
)

VERSE = ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"]
CHORUS = ["C1", "C2", "C3", "C4", "C1", "C6", "C7", "C8"]
STRONG = [n + "P" for n in CHORUS]
BRIDGE = ["B1", "B2", "B3", "B4", "B1", "B2", "B3", "B8"]
# kind, label, mood, dynamics, bars, cue for each pair of bars
PARTS = [
    ("Intro", "Intro", "suave", "MP", ["I1", "I2", "I3", "I4"], ["", ""]),
    (
        "Verso",
        "Estrofa 1",
        "suave",
        "MP",
        VERSE,
        ["All the lights...", "Ruby, blue...", "Everything looks...", "Like aquamarine..."],
    ),
    (
        "Coro",
        "Coro 1",
        "fuerte",
        "F",
        CHORUS,
        ["Ah-ah-ah-ah...", "Cacciatore", "La-da-da-da-da...", "Limousines"],
    ),
    (
        "Verso",
        "Estrofa 2",
        "suave",
        "MP",
        VERSE,
        ["All the lights are...", "On the downtown...", "Beatboxing...", "Like a boss..."],
    ),
    (
        "Coro",
        "Coro 2",
        "muy fuerte",
        "FF",
        [*STRONG[:-1], "C8B"],
        ["Ah-ah-ah-ah...", "Ciao amore", "La-da-da-da-da...", "Soft ice cream"],
    ),
    (
        "Puente",
        "Puente",
        "fuerte",
        "F",
        BRIDGE,
        ["The summer's wild...", "I adore you...", "Summer's hot...", "I was so wrong..."],
    ),
    (
        "Coro",
        "Coro 3",
        "muy fuerte",
        "FF",
        STRONG,
        ["Catch me if you can...", "Salvatore", "Calling out my name...", "Ciao amore"],
    ),
    ("Outro", "Final", "suave", "P", ["O1", "O2", "O3"], ["", ""]),
]

plan, info, sections, steps = [], [], [], {}
for kind, label, mood, dynamics, names, cues in PARTS:
    start = len(plan)
    for i, name in enumerate(names):
        pair = tuple(names[i - i % 2 : i - i % 2 + 2])
        step = steps.setdefault(pair, len(steps) + 1)
        events, chord, tip = P[name]
        plan.append((events, dynamics, name == "O3"))
        info.append(
            {
                "step": step,
                "section": label,
                "mood": mood,
                "chord": chord,
                "cue": cues[i // 2],
                "tip": tip,
            }
        )
    sections.append((kind, label, start, len(plan)))

meta = {
    "title": "Salvatore",
    "artist": "Lana Del Rey",
    "tab_author": "arreglo propio",
    "source_url": "https://youtu.be/ChzeixqkU6k",
    "tempo_bpm": 60.0,
    "tags": ["dedos", "cejilla 2"],
}
end = len(plan)
score = write_song(sys.argv[1], meta, 2, sections, plan, {end - 3: 54, end - 2: 48})
write_guide(sys.argv[2], score, info)
print("compases", end, "pasos", len(steps))
