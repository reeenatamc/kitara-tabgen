"""Hasta siempre without the index barre: the "otro arreglo" version with its barre bars rewritten.

Reads the song and guide it starts from, replaces the bars below and writes the new pair.
The capo stays on fret 2; frets are counted from it.
"""
import json
import sys
import uuid

from tabgen import Builder, write_guide

REPO = "/Users/renata/Documents/GitHub/fretwork"
BASE = "hasta-siempre-otro-arreglo"

# Si7 in the verses: the open shape, with the line that went down string 2 moved to string 1.
V_LINE = [(0, "5:2:M"), (2, "1:5:Ñ"), (4, "1:3:Ñ"), (6, "3:2:A"), (8, "1:2:Ñ 5:2:M"), (10, "3:2:A"), (12, "4:1:I"), (14, "3:2:A")]
V_PLAIN = [(0, "5:2:M"), (2, "1:3:Ñ"), (4, "3:2:A"), (6, "4:1:I"), (8, "1:2:Ñ 5:2:M"), (10, "3:2:A"), (12, "4:1:I"), (14, "3:2:A")]
V_END = V_PLAIN[:-1] + [(14, "2:0")]
# Si7 in the choruses: the melody stays high, the index only holds the bass, string 2 rings open.
C_SI7 = [(0, "1:10:Ñ:a 6:7:I"), (2, "1:8:M:a"), (4, "2:0"), (6, "1:7:I:a"), (8, "3:8:M 6:7:I"), (10, "2:0"), (12, "3:8:M"), (14, "2:0")]
C_SI7_END = [(0, "1:8:A:a 6:7:I"), (2, "2:0"), (4, "2:10:Ñ:a"), (6, "1:7:I:a"), (8, "6:7:I"), (10, "2:0"), (12, "3:8:M"), (14, "2:0")]
C_SI7_BIG = [(0, "1:10:Ñ:a 2:0 6:7:I"), (2, "1:8:M:a 2:0"), (4, "2:0"), (6, "1:7:I:a 2:0 3:8:M"), (8, "2:0 3:8:M 6:7:I"), (10, "2:0"), (12, "2:0 3:8:M"), (14, "3:8:M")]
C_SI7_BIG_END = [(0, "1:8:A:a 2:10:Ñ 6:7:I"), (2, "2:0"), (4, "2:10:Ñ:a 3:8:M"), (6, "1:7:I:a 2:0 3:8:M"), (8, "2:0 6:7:I"), (10, "2:0"), (12, "2:0 3:8:M"), (14, "2:0")]
# Do in the choruses: the bass becomes the open string 6, so the index only covers strings 1 and 2.
C_DO = [(0, "1:8:I:a 6:0"), (2, "2:8:I"), (4, "3:9:M"), (6, "2:8:I"), (8, "3:11:Ñ:va"), (12, "2:8:I:a"), (14, "2:10:A:a")]
C_DO_BIG = [(0, "1:8:I:a 2:8:I 3:9:M 6:0"), (2, "2:8:I 4:10:A"), (4, "3:9:M 4:10:A"), (6, "2:8:I 3:9:M"), (8, "3:11:Ñ:va 6:0"), (12, "2:8:I:a 4:10:A"), (14, "2:10:A:a 3:9:M")]

TIP_VERSE = "Si7 abierto, sin cejilla de dedo: medio en cuerda 5, índice en cuerda 4, anular en cuerda 3. El meñique lleva las notas de la cuerda 1."
TIP_CHORUS = "Sin cejilla: el índice pisa solo el bajo en cuerda 6 traste 7 y después baja a la cuerda 1. La cuerda 2 suena al aire."
TIP_DO = "Sin cejilla completa: el bajo es la cuerda 6 al aire. El índice acostado cubre solo las cuerdas 1 y 2 en el traste 8."

# bar number (from 1) -> (events, tip)
CHANGES = {
    6: (V_LINE, TIP_VERSE), 8: (V_PLAIN, TIP_VERSE), 12: (V_END, TIP_VERSE),
    22: (V_LINE, TIP_VERSE), 24: (V_PLAIN, TIP_VERSE), 28: (V_END, TIP_VERSE),
    14: (C_SI7, TIP_CHORUS), 16: (C_SI7, TIP_CHORUS), 20: (C_SI7_END, TIP_CHORUS),
    30: (C_SI7_BIG, TIP_CHORUS), 32: (C_SI7_BIG, TIP_CHORUS), 36: (C_SI7_BIG_END, TIP_CHORUS),
    19: (C_DO, TIP_DO), 35: (C_DO_BIG, TIP_DO),
}

song_path, guide_path = sys.argv[1], sys.argv[2]
with open("%s/songs/%s.json" % (REPO, BASE), encoding="utf-8") as f:
    score = json.load(f)
with open("%s/guides/%s.json" % (REPO, BASE), encoding="utf-8") as f:
    guide = json.load(f)

builder = Builder()
builder.next_id = score["next_id"]
bars = score["tracks"][0]["staves"][0]["bars"]
info = [{k: bar[k] for k in ("step", "section", "mood", "chord", "cue", "tip")} for bar in guide["bars"]]
for number, (events, tip) in CHANGES.items():
    dynamics = bars[number - 1]["voices"][0]["beats"][0]["dynamics"]
    bars[number - 1] = builder.bar(events, dynamics)
    info[number - 1]["tip"] = tip
score["id"] = str(uuid.uuid4())
score["meta"]["title"] = "Hasta siempre sin cejilla"
score["next_id"] = builder.next_id + 1

with open(song_path, "w", encoding="utf-8") as f:
    json.dump(score, f, ensure_ascii=False, indent=2)
    f.write("\n")
write_guide(guide_path, score, info)
