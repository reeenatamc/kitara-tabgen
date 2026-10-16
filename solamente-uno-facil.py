"""Solamente uno, easier to play: same notes on top, same bass and inner notes, fewer hard moves.

What changes from the plain version: no barre (the F bass moves to string 4), open strings as bass wherever the
left hand has to travel, and the whole Dm-G-C-F descent stays between frets 5 and 13 instead of jumping to fret 1-3.
Usage: solamente-uno-facil.py song.json guide.json
"""
import sys

from solamente_uno_base import A, C, DM, F, G, P, build

EASY = {
    "T3": ([(0, "4:3:A"), (2, "1:3:Ñ:a"), (4, "1:3:Ñ:a"), (6, "1:1:I:a"), (8, "4:3:A"), (10, "2:1:I 3:2:M"), (12, "3:2:M"),
            (14, "1:1:I:a 3:2:M")],
           F, "Fa sin cejilla: el bajo es el anular en la cuerda 4, traste 3. El índice va solo, primero a la cuerda 1 y después a la 2."),
    "T4": ([(0, "4:3:A"), (4, "2:1:I 3:2:M"), (6, "4:3:A"), (8, "1:1:I:a"), (10, "1:0::a 2:1:I 3:2:M"), (12, "4:3:A"),
            (13, "2:3:Ñ:a"), (14, "2:1:I:a")],
           F, "Sigue el Fa sin cejilla. Al final la melodía baja rápido: cuerda 1 al aire, cuerda 2 traste 3 y traste 1."),
    "B1M": ([(0, "4:0"), (2, "5:0"), (4, "1:7:A:a"), (6, "1:8:Ñ:a"), (8, "4:0"), (10, "1:7:A:a"), (12, "4:0"), (14, "1:5:I:a")],
            DM, "Dos bajos al aire te dan tiempo de poner la mano en el traste 5. Índice en el 5, anular en el 7, meñique en el 8."),
    "B2": ([(0, "4:0 3:0"), (2, "1:10:I:a"), (4, "2:13:Ñ:a"), (6, "3:0"), (8, "2:12:A:a"), (10, "3:0"), (12, "2:10:I:a"), (14, "3:0")],
           G, "El bajo son las cuerdas 4 y 3 al aire: mientras suenan, sube al traste 10. La mano no se mueve: índice en el 10, anular en el 12, meñique en el 13."),
    "B2M": ([(0, "4:0 3:0"), (2, "1:10:I:a"), (4, "2:13:Ñ:a"), (6, "1:10:I:a"), (8, "2:12:A:a"), (10, "3:0"), (12, "2:10:I:a"),
             (14, "1:10:I:a")],
            G, "Igual que antes, con la cuerda 1 del traste 10 sonando dos veces más. La mano sigue quieta en el traste 10."),
    "B3": ([(0, "2:8:I:a 4:10:A"), (2, "3:0"), (4, "4:10:A 1:0"), (6, "3:0"), (8, "4:10:A 1:0"), (10, "3:0"), (12, "1:10:Ñ:a"),
            (14, "1:8:I:a")],
           C, "Do sin bajar: índice en la cuerda 2 traste 8, anular en la cuerda 4 traste 10. Las cuerdas 3 y 1 suenan al aire y los dedos no se levantan."),
    "B4": ([(0, "5:8:I"), (4, "2:12:Ñ:a"), (6, "1:8:I:a"), (8, "2:10:A:a"), (10, "1:8:I:a"), (12, "2:8:I:a"), (14, "3:0")],
           F, "El bajo de Fa está ahí mismo: índice en la cuerda 5, traste 8. La cuerda 3 al aire del final te da tiempo de bajar a Si7."),
    "E3": ([(0, "1:5:Ñ:av 2:2:M 3:2:I 5:0")],
           A, "Acorde final de La mayor con tres dedos: índice y medio en el traste 2 de las cuerdas 3 y 2, meñique en la cuerda 1 traste 5."),
}

THEME = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]
PARTS = [
    ("Intro", "Entrada", "suave", "MP", ["PK"]),
    ("Verso", "Tema 1", "suave", "MP", THEME + ["T8"]),
    ("Verso", "Tema 2", "suave", "MP", THEME + ["T8B"]),
    ("Coro", "Vuelta 1", "fuerte", "F", ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]),
    ("Coro", "Vuelta 2", "fuerte", "F", ["B1M", "B2M", "B3", "B4", "B5", "B6"]),
    ("Outro", "Final", "suave", "MP", ["E1", "E2", "E3"]),
]

build(sys.argv[1], sys.argv[2], "Solamente uno (fácil)", ["dedos", "instrumental", "sin cejilla"], PARTS, {**P, **EASY},
      {2: 100, 1: 84})
