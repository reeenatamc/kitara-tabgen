"""Hasta siempre, closer to the sung line: the "sin cejilla" version with the melody notes of the source tab put back.

The source tab (songs/hasta-siempre.json) repeats notes where the verse has more syllables; the arrangement had
thinned them to one note per beat. Same shapes, same capo (fret 2), same bars otherwise.
"""

import json
import sys
import uuid

import paths
from tabgen import Builder, write_guide

# Este arreglo se hizo encima de otro que luego quedo superado: su fuente esta en archive/,
# no en kitara. La ruta estuvo clavada aqui con el nombre viejo del repo.
BASE = "hasta-siempre-sin-cejilla"

# Em to Am: the line starts with the bass and the high C sounds twice before it comes down.
V_RISE = [
    (0, "1:0::a 6:0"),
    (2, "2:0"),
    (4, "1:0::a"),
    (6, "1:5:I:a"),
    (8, "1:8:Ñ:a 5:0"),
    (9, "1:8:Ñ:a"),
    (10, "3:5:I"),
    (12, "1:5:I:a"),
    (14, "1:7:A:a"),
]
# B7 in the verses: the line rocks between frets 5 and 3 before it lands on fret 2.
V_LINE = [
    (0, "5:2:M"),
    (2, "1:5:Ñ:a"),
    (4, "1:3:A:a"),
    (6, "1:5:Ñ:a"),
    (8, "1:3:A:a 5:2:M"),
    (10, "4:1:I"),
    (12, "1:2:Ñ:a"),
    (14, "3:2:A"),
]
V_PLAIN = [(0, "1:5:Ñ:a 5:2:M"), *V_LINE[1:]]
V_END = [*V_PLAIN[:-1], (14, "2:0")]
# B7 in the choruses: the last melody note sounds twice.
C_SI7 = [
    (0, "1:10:Ñ:a 6:7:I"),
    (2, "1:8:M:a"),
    (4, "2:0"),
    (6, "1:7:I:a"),
    (8, "1:7:I:a 3:8:M"),
    (10, "2:0"),
    (12, "6:7:I"),
    (14, "2:0"),
]
C_SI7_BIG = [
    (0, "1:10:Ñ:a 2:0 6:7:I"),
    (2, "1:8:M:a 2:0"),
    (4, "2:0"),
    (6, "1:7:I:a 2:0 3:8:M"),
    (8, "1:7:I:a 2:0 3:8:M"),
    (10, "2:0"),
    (12, "2:0 3:8:M 6:7:I"),
    (14, "3:8:M"),
]

TIP_RISE = "La cuerda 1 al aire suena dos veces, la primera junto con el bajo. Arriba, el traste 8 también suena dos veces seguidas y rápido; después traste 5 y traste 7."
TIP_LINE = "Medio fijo en cuerda 5 traste 2. La cuerda 1 va y vuelve: traste 5 con el meñique, traste 3 con el anular, otra vez 5 y 3, y cae al traste 2."
TIP_PLAIN = "Igual que el compás 6, pero la melodía entra ya en el tiempo 1, junto con el bajo."
TIP_CHORUS = "Sin cejilla. El traste 7 de la cuerda 1 suena dos veces seguidas; el índice vuelve al bajo de la cuerda 6 recién en el tiempo 4."

# bar number (from 1) -> (events, tip)
CHANGES = {
    5: (V_RISE, TIP_RISE),
    21: (V_RISE, TIP_RISE),
    6: (V_LINE, TIP_LINE),
    22: (V_LINE, TIP_LINE),
    8: (V_PLAIN, TIP_PLAIN),
    24: (V_PLAIN, TIP_PLAIN),
    12: (V_END, TIP_PLAIN),
    28: (V_END, TIP_PLAIN),
    14: (C_SI7, TIP_CHORUS),
    16: (C_SI7, TIP_CHORUS),
    30: (C_SI7_BIG, TIP_CHORUS),
    32: (C_SI7_BIG, TIP_CHORUS),
}

song_path, guide_path = sys.argv[1], sys.argv[2]
with open(paths.archived_song(BASE), encoding="utf-8") as f:
    score = json.load(f)
with open(paths.archived_guide(BASE), encoding="utf-8") as f:
    guide = json.load(f)

builder = Builder()
builder.next_id = score["next_id"]
bars = score["tracks"][0]["staves"][0]["bars"]
info = [
    {k: bar[k] for k in ("step", "section", "mood", "chord", "cue", "tip")} for bar in guide["bars"]
]
for number, (events, tip) in CHANGES.items():
    dynamics = bars[number - 1]["voices"][0]["beats"][0]["dynamics"]
    bars[number - 1] = builder.bar(events, dynamics)
    info[number - 1]["tip"] = tip
score["id"] = str(uuid.uuid4())
score["meta"]["title"] = "Hasta siempre (fiel a la letra)"
score["next_id"] = builder.next_id + 1

with open(song_path, "w", encoding="utf-8") as f:
    json.dump(score, f, ensure_ascii=False, indent=2)
    f.write("\n")
write_guide(guide_path, score, info)
