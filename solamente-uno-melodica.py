"""Solamente uno, more melodic: the tune sings on top with slurs and vibrato, and the repeats add a second voice.

One idea of texture: the first time through each part is the plain line, the repeat doubles it in thirds or
sixths. The melody notes that the plain version leaves out (the held A over Dm, the held F sharp over B7) are back.
Uses the easy fingerings (no barre, descent between frets 5 and 13).
Usage: solamente-uno-melodica.py song.json guide.json
"""
import sys

from solamente_uno_base import A, AM, B7, C, DM, E, F, G, P, build

SONG = {
    # Theme with slurs and vibrato on the long notes.
    "T2": ([(0, "5:0"), (2, "3:2:A"), (4, "1:0::pa"), (6, "1:3:Ñ:a"), (8, "1:3:Ñ:a"), (10, "2:1:I 3:2:A"), (12, "1:2:M:va 3:2:A")],
           AM, "Ligado de la cuerda 1 al aire al traste 3: pulsas una sola vez. La última nota, traste 2, con vibrato."),
    "T3": ([(0, "4:3:A"), (2, "1:3:Ñ:a"), (4, "1:3:Ñ:a"), (6, "1:1:I:va"), (8, "4:3:A"), (10, "2:1:I 3:2:M"), (12, "3:2:M"),
            (14, "1:1:I:a 3:2:M")],
           F, "Fa sin cejilla, bajo en la cuerda 4. Cuando el meñique baja al índice, mueve un poco la nota."),
    "T4": ([(0, "4:3:A"), (4, "2:1:I 3:2:M"), (6, "4:3:A"), (8, "1:1:I:a"), (10, "1:0::a 2:1:I 3:2:M"), (12, "4:3:A"),
            (13, "2:3:Ñ:a"), (14, "2:1:I:a")],
           F, "Sigue el Fa sin cejilla. Al final la melodía baja rápido: cuerda 1 al aire, cuerda 2 traste 3 y traste 1."),
    "T5": ([(0, "4:0"), (2, "3:2:M 2:3:A"), (4, "1:1:I:va"), (10, "4:0 3:2:M 1:1:I:a"), (12, "5:0"), (14, "2:3:A:a"), (15, "1:0::a")],
           DM, "Re menor. La nota de la cuerda 1 dura casi medio compás: hazla cantar con vibrato."),
    "T6": ([(0, "2:3:Ñ:va 6:0"), (4, "3:1:I 2:0"), (6, "5:2:M"), (8, "2:3:Ñ:a"), (10, "2:0::a 3:1:I"), (12, "4:2:A"), (14, "2:1:I:a")],
           E, "Mi mayor con el meñique en la cuerda 2, traste 3, con vibrato. Después la melodía baja por la cuerda 2."),
    # Repeat of the theme: the opening line in sixths, all open strings and the A minor shape.
    "T1S": ([(0, "1:0::a 3:0 5:0"), (2, "2:3:Ñ:a 4:3:A"), (4, "2:1:I:a 4:2:M"), (6, "1:0::a 3:0"), (10, "2:1:I:a 4:2:M"),
             (12, "5:0"), (14, "2:1:I:a")],
            AM, "La misma frase con una segunda voz debajo, dos cuerdas más abajo: cuerda 3 al aire, cuerda 4 traste 3 y traste 2."),

    # First time round: the plain line, with the held notes back on top.
    "B1": ([(0, "4:0 1:5:I:va"), (2, "4:7:Ñ"), (4, "3:7:A 2:6:M"), (6, "4:7:Ñ"), (8, "3:7:A 2:6:M"), (12, "3:7:A 2:6:M"),
            (14, "3:0")],
           DM, "Bajas del traste 12 al 5 por la cuerda 1 y esa nota se queda cantando todo el compás. Debajo: medio en la cuerda 2, anular en la 3, meñique en la 4."),
    "B2": ([(0, "4:0 3:0"), (2, "1:10:I:a"), (4, "2:13:Ñ:a"), (6, "1:10:I:a 3:0"), (8, "2:12:A:a"), (10, "3:0"), (12, "2:10:I:a"),
            (14, "1:10:I:a 3:0")],
           G, "El dibujo del traste 12, ahora en el 10. La cuerda 1 se repite arriba y la cuerda 2 baja 13, 12, 10. El bajo son las cuerdas 4 y 3 al aire."),
    "B3": ([(0, "2:8:I:va 4:10:A"), (2, "3:0"), (4, "4:10:A 1:0"), (6, "3:0"), (8, "4:10:A 1:0"), (10, "3:0"), (12, "1:10:Ñ:a"),
            (14, "1:8:I:a")],
           C, "Do sin bajar: índice en la cuerda 2 traste 8, anular en la cuerda 4 traste 10. La nota del índice es la melodía; las cuerdas 3 y 1 suenan al aire."),
    "B4": ([(0, "5:8:I"), (2, "4:10:A"), (4, "2:12:Ñ:a"), (6, "1:8:I:a"), (8, "2:10:A:a"), (10, "1:8:I:a"), (12, "2:8:I:a"), (14, "3:0")],
           F, "Sigues en el traste 8. La cuerda 1 se repite y la cuerda 2 baja 12, 10, 8. La cuerda 3 al aire del final te da tiempo de bajar a Si7."),
    "B5": ([(0, "5:2:M 1:2:Ñ:va"), (2, "3:2:A"), (4, "2:0"), (6, "3:2:A"), (8, "2:0"), (10, "4:1:I"), (12, "2:0 1:2:Ñ:a"), (14, "3:0")],
           B7, "Si7 con el meñique en la cuerda 1, traste 2: ahí termina la bajada de la melodía. Que se quede sonando encima."),

    # Second time round: the descending line sings in thirds, without the repeated top note.
    "B1S": ([(0, "4:0 1:5:I:a 2:6:M"), (2, "5:0"), (4, "1:7:I:a 2:8:M"), (6, "1:8:I:a 2:10:A"), (8, "4:0"), (10, "1:7:I:a 2:8:M"),
             (12, "4:0"), (14, "1:5:I:a 2:6:M")],
            DM, "La melodía ahora va de a dos cuerdas. Índice en la cuerda 1 y otro dedo en la 2: trastes 5 y 6, 7 y 8, 8 y 10, y de vuelta."),
    "B2S": ([(0, "4:0 3:0"), (2, "1:10:I:a 2:12:A"), (4, "1:8:I:a 2:10:A"), (6, "3:0"), (8, "1:7:I:a 2:8:M"), (10, "3:0"),
             (12, "1:5:I:a 2:6:M"), (14, "3:0")],
            G, "La bajada entera de a dos cuerdas: 10 y 12, 8 y 10, 7 y 8, 5 y 6. La cuerda 3 al aire va entre medio y te da tiempo de mover la mano."),
    "B3S": ([(0, "2:8:I:va 4:10:A"), (2, "3:0"), (4, "4:10:A 1:0"), (6, "3:0"), (8, "4:10:A 1:0"), (10, "3:0"), (12, "1:10:A:a 2:12:Ñ"),
             (14, "1:8:I:a 2:10:A")],
            C, "Do en el traste 8 como antes. Las dos últimas notas suben de a dos cuerdas: 10 y 12, después 8 y 10."),
    "B4S": ([(0, "5:8:I"), (2, "4:10:A"), (4, "2:12:Ñ:a"), (6, "1:8:I:a"), (8, "2:10:A:a 3:10:M"), (10, "1:8:I:a"),
             (12, "2:8:I:a 3:9:M"), (14, "3:0")],
            F, "El mismo compás de Fa con una nota más debajo de la cuerda 2: medio en la cuerda 3, traste 10 y después traste 9."),
    "B5S": ([(0, "5:2:M 1:2:Ñ:va"), (2, "3:2:A"), (4, "2:0"), (6, "3:2:A 4:1:I"), (8, "2:0"), (10, "4:1:I"), (12, "2:0 1:2:Ñ:a"),
             (14, "3:0")],
            B7, "Si7 con la melodía arriba. En el tiempo 2 suenan juntas las cuerdas 3 y 4."),
    "E3": ([(0, "1:5:Ñ:av 2:2:M 3:2:I 5:0")],
           A, "Acorde final de La mayor con tres dedos: índice y medio en el traste 2 de las cuerdas 3 y 2, meñique en la cuerda 1 traste 5."),
}

PARTS = [
    ("Intro", "Entrada", "suave", "MP", ["PK"]),
    ("Verso", "Tema 1", "suave", "MP", ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]),
    ("Verso", "Tema 2, a dos voces", "suave", "MP", ["T1S", "T2", "T3", "T4", "T5", "T6", "T7", "T8B"]),
    ("Coro", "Vuelta 1", "fuerte", "F", ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]),
    ("Coro", "Vuelta 2, a dos voces", "muy fuerte", "FF", ["B1S", "B2S", "B3S", "B4S", "B5S", "B6"]),
    ("Outro", "Final", "suave", "MP", ["E1", "E2", "E3"]),
]

build(sys.argv[1], sys.argv[2], "Solamente uno (melódica)", ["dedos", "instrumental", "sin cejilla"], PARTS, {**P, **SONG},
      {2: 100, 1: 84})
