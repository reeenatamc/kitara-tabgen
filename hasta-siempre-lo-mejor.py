"""Hasta siempre, the best of both: the source tab where it has its own colour, our arrangement where it sings.

Verse 1 comes from the source tab (songs/hasta-siempre.json): the melody in the low register. Everything else,
including the intro and the ending, comes from "hasta-siempre-fiel" (the source intro figure was too hard).
Capo on fret 2, 42 bars, same sections.
"""

import copy
import json
import os
import sys
import uuid

import paths
from tabgen import write_guide

# La ruta sale de paths.py: estuvo clavada aqui con el nombre viejo del repo.
REPO = paths.require()
# The arrangement this one starts from was removed from the app on 2026-10-13; its files live here.
# Relativo al script: la carpeta se renombró una vez y la ruta absoluta quedó muerta.
ARCHIVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")
OURS, SOURCE = "hasta-siempre-fiel", "hasta-siempre"

# our bar (from 1) -> source bar (from 1)
FROM_SOURCE = {n: n for n in range(5, 13)}
# source bar -> (slot, string) of the melody notes, accented so they stand out of the arpeggio
VERSE_A = [(4, 4), (6, 3), (8, 2), (10, 2), (14, 3)]
VERSE_B = [(0, 3), (2, 3), (6, 3), (8, 3), (12, 4)]
MELODY = {
    5: [(0, 4), (4, 4), (6, 3), (8, 2), (9, 2), (12, 3), (14, 2)],
    6: [(0, 2), (2, 3), (4, 3), (6, 3), (8, 3), (12, 4)],
    7: VERSE_A,
    8: VERSE_B,
    11: VERSE_A,
    12: VERSE_B,
    9: [(0, 4), (4, 4), (8, 3), (12, 4), (14, 4)],
    10: [(0, 3), (2, 3), (12, 4)],
}
RIFF_1 = "Figura de la intro original en la cuerda 1: traste 3, ligado al 2, al aire y otra vez 2. Pulsas solo la primera de cada grupo de dos; el bajo cambia debajo."
RIFF_2 = (
    "La misma figura un escalón abajo: traste 2 ligado al aire, y la cuerda 2 traste 3 entre medio."
)
LOW = "Melodía grave, como en la tablatura original. "
TIPS = {
    1: ("Mi menor", RIFF_1),
    2: ("Re", RIFF_2),
    3: (
        "Do",
        "Do con la cuerda 1 al aire arriba. La cuerda 2 se mueve: traste 3, traste 1, traste 3 y traste 4.",
    ),
    4: (
        "Si7",
        "Si7: medio en cuerda 5 traste 2, índice en cuerda 4 traste 1, anular en cuerda 3 traste 2. El meñique baja a la cuerda 4 traste 4.",
    ),
    5: (
        "Mi menor, La menor",
        LOW + "Canta en las cuerdas 4, 3 y 2; la cuerda 2 traste 1 suena dos veces rápido.",
    ),
    6: (
        "Si7",
        LOW
        + "Baja por la cuerda 3: traste 2, al aire, traste 2, al aire, y termina en la cuerda 4 traste 4 con el meñique.",
    ),
    7: ("Mi menor, La menor", LOW + "Como el compás 5 sin la nota repetida: entra solo el bajo."),
    8: (
        "Si7",
        LOW
        + "La cuerda 3 va y vuelve entre el traste 2 y el aire; termina en la cuerda 4 traste 4.",
    ),
    9: (
        "Mi menor, Sol",
        LOW + "Sube por la cuerda 4: traste 2, traste 4, y la cuerda 3 al aire con el bajo de Sol.",
    ),
    10: (
        "Si7",
        "Dos notas largas: cuerda 3 traste 2 y al final cuerda 4 traste 4. Déjalas sonar, es el respiro de la estrofa.",
    ),
    11: ("Mi menor, La menor", "Igual al compás 7."),
    12: (
        "Si7",
        "Igual al compás 8; la última nota es la cuerda 3 al aire y de ahí subes al traste 7 para el coro.",
    ),
    37: ("Mi menor", RIFF_1),
    38: ("Re", RIFF_2),
    39: ("Do", "Igual al compás 3."),
    40: (
        "Si7",
        "Igual al compás 4, con el bajo bajando al final por la cuerda 6: traste 3 y traste 2. Aquí empieza a frenar.",
    ),
}

song_path, guide_path = sys.argv[1], sys.argv[2]
with open("%s/songs/%s.json" % (ARCHIVE, OURS), encoding="utf-8") as f:
    score = json.load(f)
with open("%s/guides/%s.json" % (ARCHIVE, OURS), encoding="utf-8") as f:
    guide = json.load(f)
with open("%s/songs/%s.json" % (REPO, SOURCE), encoding="utf-8") as f:
    source = json.load(f)["tracks"][0]["staves"][0]["bars"]

next_id = score["next_id"]
bars = score["tracks"][0]["staves"][0]["bars"]
info = [
    {k: bar[k] for k in ("step", "section", "mood", "chord", "cue", "tip")} for bar in guide["bars"]
]
for ours, theirs in FROM_SOURCE.items():
    bar = copy.deepcopy(source[theirs - 1])
    slot = 0.0
    for beat in bar["voices"][0]["beats"]:
        beat["dynamics"] = "MP"
        for note in beat["notes"]:
            flags = [f for f in (note.get("techniques") or "").split(" | ") if f]
            if (int(round(slot)), note["string"]) in MELODY.get(theirs, []):
                flags.append("ACCENT")
            note["techniques"] = " | ".join([*flags, "LET_RING"])
            next_id += 1
            note["id"] = next_id
        next_id += 1
        beat["id"] = next_id
        slot += 16 / beat["duration"] * (1.5 if beat.get("dots") else 1)
    bars[ours - 1] = bar
    info[ours - 1]["chord"], info[ours - 1]["tip"] = TIPS[ours]
score["id"] = str(uuid.uuid4())
score["meta"]["title"] = "Hasta siempre (lo mejor de las dos)"
score["next_id"] = next_id + 1

with open(song_path, "w", encoding="utf-8") as f:
    json.dump(score, f, ensure_ascii=False, indent=2)
    f.write("\n")
write_guide(guide_path, score, info)
