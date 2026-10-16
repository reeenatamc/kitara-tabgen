"""Solamente uno, two-guitar instrumental from a TikTok clip reduced to one guitar. A minor, no capo.

Transcribed by ear from the clip audio (quarter = 110): lead melody plus the bass and pedal notes of the second guitar.
Usage: solamente-uno.py song.json guide.json
"""
import sys

from tabgen import write_guide, write_song

AM, F, DM, E, G, C, B7, A = "Lam", "Fa", "Rem", "Mi", "Sol", "Do", "Si7", "La"

LIFT = [(0, "5:0"), (2, "1:12:I:a"), (4, "2:15:Ñ:a"), (6, "1:12:I:a"), (8, "2:13:M:a"), (10, "1:12:I:a"), (12, "2:12:I:a"),
        (14, "1:12:I:a")]

# name: (events, chord, tip)
P = {
    "PK": ([(0, "3:2:M:a"), (8, "3:2:M:a"), (10, "2:0::a"), (12, "2:1:I:a"), (14, "2:3:Ñ:a")],
           AM, "Una nota larga y luego la escalera de entrada: cuerda 3 traste 2, cuerda 2 al aire, traste 1 y traste 3."),

    "T1": ([(0, "1:0::a 5:0"), (2, "2:3:Ñ:a"), (4, "2:1:I:a"), (6, "1:0::a"), (10, "2:1:I:a"), (12, "4:2:M"), (14, "2:1:I:a")],
           AM, "La escalera cae en la cuerda 1 al aire junto con el bajo. Deja el índice quieto en la cuerda 2, traste 1."),
    "T2": ([(0, "5:0"), (2, "3:2:A"), (4, "1:0::a"), (6, "1:3:Ñ:a"), (8, "1:3:Ñ:a"), (10, "2:1:I 3:2:A"), (12, "1:2:M:a")],
           AM, "La melodía sube al traste 3 de la cuerda 1 y lo repite. La última nota, traste 2, empuja hacia el compás siguiente."),
    "T3": ([(0, "6:1:I"), (2, "1:3:Ñ:a"), (4, "1:3:Ñ:a"), (6, "1:1:I:a"), (8, "4:3:A"), (10, "2:1:I 3:2:M"), (12, "3:2:M"),
            (14, "1:1:I:a 2:1:I")],
           F, "Fa con cejilla en el traste 1. El meñique canta en el traste 3 y baja al índice."),
    "T4": ([(0, "6:1:I"), (4, "2:1:I 3:2:M"), (6, "4:3:A"), (8, "1:1:I:a"), (10, "1:0::a 2:1:I 3:2:M"), (12, "4:3:A"),
            (13, "2:3:Ñ:a"), (14, "2:1:I:a")],
           F, "Sigue en Fa. Al final la melodía baja rápido: cuerda 1 al aire, cuerda 2 traste 3 y traste 1."),
    "T5": ([(0, "4:0"), (2, "3:2:M 2:3:A"), (4, "1:1:I:a"), (10, "4:0 3:2:M 1:1:I:a"), (12, "5:0"), (14, "2:3:A:a"), (15, "1:0::a")],
           DM, "Re menor. La nota de la cuerda 1 se queda sonando; las dos últimas son rápidas y llevan a Mi."),
    "T6": ([(0, "2:3:Ñ:a 6:0"), (4, "3:1:I 2:0"), (6, "5:2:M"), (8, "2:3:Ñ:a"), (10, "2:0::a 3:1:I"), (12, "4:2:A"), (14, "2:1:I:a")],
           E, "Mi mayor con el meñique en la cuerda 2, traste 3. La melodía baja por la cuerda 2: traste 3, aire, traste 1."),
    "T7": ([(0, "5:0"), (2, "3:2:A"), (4, "2:1:I 3:2:A"), (6, "6:0"), (10, "1:0::a 2:1:I 3:2:A"), (14, "2:1:I:a")],
           AM, "Descanso en La menor. Toca suave, casi sin atacar."),
    "T8": ([(0, "5:0"), (2, "2:1:I"), (4, "4:2:M"), (6, "1:0::a"), (8, "3:2:A:a"), (10, "2:0::a"), (12, "2:1:I:a"), (14, "2:3:Ñ:a")],
           AM, "La segunda mitad es otra vez la escalera de entrada, para repetir el tema."),
    "T8B": (LIFT, AM,
            "Sube la mano al traste 12. El índice acostado toca la cuerda 1 y entre medio baja la cuerda 2: trastes 15, 13 y 12."),

    "B1": ([(0, "4:0"), (2, "3:2:M"), (4, "2:3:A 1:1:I"), (6, "3:2:M"), (8, "2:3:A 1:1:I"), (10, "3:2:M"), (12, "2:3:A 1:1:I"),
            (14, "3:0")],
           DM, "Vuelve abajo a Re menor. El pulgar marca el bajo y los dedos alternan la cuerda 3 con las dos de arriba."),
    "B1M": ([(0, "4:0"), (2, "3:2:M"), (4, "1:7:I:a"), (6, "1:8:M:a"), (8, "4:0"), (10, "1:7:I:a"), (12, "4:0"), (14, "1:5:I:a")],
            DM, "La segunda vez la melodía entra arriba, en la cuerda 1: trastes 7, 8, 7 y 5, con la cuerda 4 al aire debajo."),
    "B2": ([(0, "6:3:I"), (2, "1:10:Ñ:a"), (4, "1:8:M:a"), (6, "3:0"), (8, "1:7:I:a"), (10, "3:0"), (12, "1:5:I:a"), (14, "3:0")],
           G, "El bajo de Sol y enseguida arriba. La melodía baja por la cuerda 1 (10, 8, 7, 5) con la cuerda 3 al aire entre nota y nota."),
    "B2M": ([(0, "6:3:I"), (2, "1:10:Ñ:a"), (4, "1:8:M:a"), (6, "1:10:Ñ:a"), (8, "1:7:I:a"), (10, "3:0"), (12, "1:5:I:a"),
             (14, "1:10:Ñ:a")],
            G, "Igual que antes, pero el traste 10 vuelve a sonar dos veces más."),
    "B3": ([(0, "1:3:Ñ:a 5:3:A"), (2, "3:0"), (4, "2:1:I 1:0"), (6, "3:0"), (8, "2:1:I 1:0"), (10, "3:0"), (12, "1:10:Ñ:a"),
            (14, "1:8:M:a")],
           C, "Do con el meñique en la cuerda 1, traste 3: ahí termina la bajada. Las dos últimas notas vuelven a subir."),
    "B4": ([(0, "6:1:I"), (4, "1:7:I:a"), (6, "1:8:M:a"), (8, "2:10:Ñ:a"), (10, "1:8:M:a"), (12, "2:8:M:a"), (14, "1:8:M:a")],
           F, "Bajo de Fa y la mano al traste 7. El traste 8 de la cuerda 1 se repite; entre medio toca la cuerda 2, trastes 10 y 8."),
    "B5": ([(0, "5:2:M"), (2, "3:2:A"), (4, "2:0"), (6, "3:2:A"), (8, "2:0"), (10, "4:1:I"), (12, "2:0"), (14, "3:0")],
           B7, "Si7 abajo: medio en la cuerda 5, índice en la 4, anular en la 3. Es un compás de respiro, sin melodía."),
    "B6": ([(0, "6:0"), (2, "1:0::a 3:1:I"), (4, "2:3:Ñ:a"), (6, "3:1:I"), (8, "2:1:M:a"), (10, "3:1:I"), (12, "2:0::a"), (14, "3:1:I")],
           E, "Mi mayor. La melodía baja (cuerda 1 al aire, cuerda 2 trastes 3, 1 y aire) con la cuerda 3 traste 1 entre medio."),
    "B7": ([(0, "5:0 3:2:A:a"), (6, "4:2:M"), (8, "2:1:I 1:0"), (10, "3:2:A"), (12, "2:1:I 1:0"), (14, "3:2:A")],
           AM, "La frase cae a La menor. Deja sonar la primera nota."),
    "B8": (LIFT, AM, "Otra vez arriba, al traste 12, para repetir la vuelta."),

    "E1": ([(0, "5:0"), (2, "3:2:A"), (4, "2:1:I 3:2:A"), (6, "4:2:M"), (8, "1:0 2:1:I 3:2:A"), (10, "4:2:M"), (12, "2:1:I 3:2:A")],
           AM, "La menor tranquilo para cerrar la vuelta."),
    "E2": ([(0, "5:0"), (2, "4:2:M"), (4, "3:2:A:a"), (6, "2:0::a"), (8, "2:1:I:a"), (10, "2:3:Ñ:a"), (12, "1:0::a"), (14, "1:3:Ñ:a")],
           AM, "La escalera del principio, esta vez hasta el traste 3 de la cuerda 1."),
    "E3": ([(0, "1:5:Ñ:av 2:2:I 3:2:I 4:2:I 5:0")],
           A, "Acorde final en La mayor: índice acostado en el traste 2 y meñique en la cuerda 1, traste 5. Arrastra el pulgar despacio."),
}

THEME = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]
# kind, label, mood, dynamics, bars
PARTS = [
    ("Intro", "Entrada", "suave", "MP", ["PK"]),
    ("Verso", "Tema 1", "suave", "MP", THEME + ["T8"]),
    ("Verso", "Tema 2", "suave", "MP", THEME + ["T8B"]),
    ("Coro", "Vuelta 1", "fuerte", "F", ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]),
    ("Coro", "Vuelta 2", "fuerte", "F", ["B1M", "B2M", "B3", "B4", "B5", "B6"]),
    ("Outro", "Final", "suave", "MP", ["E1", "E2", "E3"]),
]

plan, info, sections, steps = [], [], [], {}
for kind, label, mood, dynamics, names in PARTS:
    start = len(plan)
    for i, name in enumerate(names):
        pair = tuple(names[i - i % 2:i - i % 2 + 2])
        step = steps.setdefault(pair, len(steps) + 1)
        events, chord, tip = P[name]
        plan.append((events, dynamics, name == "E3"))
        info.append({"step": step, "section": label, "mood": mood, "chord": chord, "cue": "", "tip": tip})
    sections.append((kind, label, start, len(plan)))

meta = {"title": "Solamente uno", "artist": "dúo de guitarras (video de TikTok)", "tab_author": "transcripción de oído",
        "source_url": "", "tempo_bpm": 110.0, "tags": ["dedos", "instrumental"]}
end = len(plan)
score = write_song(sys.argv[1], meta, 0, sections, plan, {end - 2: 100, end - 1: 84})
write_guide(sys.argv[2], score, info)
print("compases", end, "pasos", len(steps))
