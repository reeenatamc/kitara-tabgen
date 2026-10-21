"""Escribe una canción de kitara y su guía de práctica desde una notación compacta.

Un compás es una lista de `(posición, "cuerda:traste:dedo:marcas ...")`, con la posición en
semicorcheas de 0 a 15 (de 0 a 23 en un compás de 12/8). Una especificación vacía es un
silencio, y cada pulso dura hasta la posición siguiente: eso es lo que permite escribir un
compás entero en una línea y leerlo de un golpe al compararlo con la tablatura.

Las marcas se combinan entre sí:

    p   ligado de martillo o tirón, en la nota de origen
    t   nota ligada a la anterior
    v   vibrato
    a   acento, o sea que esa es la melodía
    n   armónico natural
    s   entra con un ligado desde abajo
    c   corta: se apaga al llegar el siguiente ataque en vez de seguir sonando

Las duraciones salen de `DUR`, que traduce semicorcheas a figura y puntillos. Si un hueco no
es una figura que exista —cinco semicorcheas no lo son—, el compás no suma y revienta aquí
en vez de salir descuadrado en la aplicación.
"""

import json
import uuid

DUR = {
    1: (16, 0),
    2: (8, 0),
    3: (8, 1),
    4: (4, 0),
    6: (4, 1),
    8: (2, 0),
    12: (2, 1),
    16: (1, 0),
    24: (1, 1),
}


class Builder:
    def __init__(self):
        self.next_id = 0

    def nid(self):
        self.next_id += 1
        return self.next_id

    def bar(self, events, dynamics, arpeggio=False, slots=16):
        beats = []
        for i, (pos, spec) in enumerate(events):
            end = events[i + 1][0] if i + 1 < len(events) else slots
            if end - pos not in DUR:
                raise ValueError("hueco de %d en la posicion %d de %r" % (end - pos, pos, events))
            duration, dots = DUR[end - pos]
            notes, fingers = [], []
            for token in spec.split():
                parts = ([*token.split(":"), "", ""])[:4]
                marks = parts[3]
                note = {"id": self.nid(), "string": int(parts[0]), "fret": int(parts[1])}
                if "n" in marks:
                    note["harmonic"] = "Natural"
                if "s" in marks:
                    note["slide_in"] = "FromBelow"
                if "t" in marks:
                    note["tie_destination"] = True
                elif note["fret"] > 0 and "n" not in marks:
                    if not parts[2]:
                        raise ValueError("falta el dedo de %s en %r" % (token, events))
                    fingers.append(parts[2])
                flags = [
                    name
                    for mark, name in (("p", "HAMMER_PULL"), ("v", "VIBRATO"), ("a", "ACCENT"))
                    if mark in marks
                ]
                ring = [] if "c" in marks else ["LET_RING"]
                note["techniques"] = " | ".join([*flags, *ring])
                notes.append(note)
            if len({n["string"] for n in notes}) != len(notes):
                raise ValueError(
                    "dos notas en la misma cuerda en la posicion %d de %r" % (pos, events)
                )
            beat = {"id": self.nid(), "duration": duration}
            if dots:
                beat["dots"] = dots
            if notes:
                beat["notes"] = notes
            else:
                beat["is_rest"] = True
            if fingers:
                beat["text"] = " ".join(fingers)
            beat["provenance"] = None
            beat["dynamics"] = dynamics
            if arpeggio:
                beat["effects"] = {"arpeggio": ["Down", 960]}
            beats.append(beat)
        return {"voices": [{"beats": beats}]}


def thicken(events, full, pairs, full_late=None):
    """El mismo compás con voces añadidas por debajo.

    Acordes más llenos en el primer y el tercer tiempo, y parejas de notas en los de en
    medio. Es lo que convierte una melodía pelada en algo que suena a guitarra sola.

    No toca los pulsos acentuados: ahí la melodía va sola a propósito y meterle voces la
    tapa. Y nunca pone dos notas en la misma cuerda, que es imposible de tocar.
    """
    out = []
    for pos, spec in events:
        tokens = spec.split()
        used = {t.split(":")[0] for t in tokens}
        extra = []
        if pos in (0, 8):
            extra = (full_late if pos == 8 and full_late else full).split()
        elif len(tokens) == 1 and "a" not in ([*tokens[0].split(":"), "", ""])[3]:
            key = ":".join(tokens[0].split(":")[:2])
            extra = pairs.get(key, "").split()
        for token in extra:
            if token.split(":")[0] not in used:
                tokens.append(token)
                used.add(token.split(":")[0])
        out.append((pos, " ".join(tokens)))
    return out


def write_song(path, meta, capo, sections, plan, tempos=None, chords=None, time_signature=(4, 4)):
    """Escribe el JSON de la canción.

    - `plan`: una tupla `(eventos, dinámica, arpegio)` por compás.
    - `sections`: tuplas `(tipo, etiqueta, compás inicial, compás final)`.
    - `tempos`: por compás, para los que van más lentos.
    - `chords`: un nombre por compás, y los vacíos no se escriben.
    - `time_signature`: `(numerador, denominador)`, el mismo en todos los compases. Fija
      cuántas semicorcheas suma cada uno: 16 en 4/4, 24 en 12/8.
    """
    numerator, denominator = time_signature
    slots = numerator * 16 // denominator
    builder = Builder()
    bars = [builder.bar(events, dynamics, arpeggio, slots) for events, dynamics, arpeggio in plan]
    # strict=False a propósito: chords puede venir vacía o más corta que los compases.
    for bar, chord in zip(bars, chords or [], strict=False):
        if chord:
            bar["voices"][0]["beats"][0]["chord"] = chord
    masters = []
    for i in range(len(plan)):
        master = {
            "index": i,
            "time_signature": {"numerator": numerator, "denominator": denominator},
            "key_signature": {"fifths": 0, "mode": "Major"},
        }
        for _, label, start, _ in sections:
            if start == i:
                master["section"] = {"text": label, "marker": None}
        if tempos and i in tempos:
            master["tempo"] = {"bpm": float(tempos[i]), "label": "rit."}
        masters.append(master)
    score = {
        "schema_version": 1,
        "id": str(uuid.uuid4()),
        "meta": meta,
        "master_bars": masters,
        "tracks": [
            {
                "name": "Guitarra",
                "short_name": "Gtr",
                "midi_program": 25,
                "midi_channel": 0,
                "tuning": {"midi_notes": [64, 59, 55, 50, 45, 40], "label": "Estándar"},
                "capo": capo,
                "fret_count": 22,
                "staves": [{"show_standard": False, "show_tabs": True, "bars": bars}],
            }
        ],
        "sections": [
            {"id": i, "kind": kind, "label": label, "bar_start": start, "bar_end": end}
            for i, (kind, label, start, end) in enumerate(sections)
        ],
        "sync_points": [],
        "next_id": builder.next_id + 1,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(score, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return score


def write_guide(path, score, info):
    """Escribe el JSON de la guía de práctica.

    `info` lleva un diccionario por compás con el paso, la sección, el ánimo, el acorde, la
    entrada y el consejo. De la partitura saca lo que la guía necesita mostrar: en qué
    semicorchea cae cada pulso, qué dedo va en cada nota y cuál es la melodía.
    """
    bars = score["tracks"][0]["staves"][0]["bars"]
    tempos = {m["index"]: m["tempo"]["bpm"] for m in score["master_bars"] if m.get("tempo")}
    out = []
    for i, bar in enumerate(bars):
        pos, beats = 0.0, []
        for beat in bar["voices"][0]["beats"]:
            fretted = [n for n in beat.get("notes", []) if n["fret"] > 0 and not n.get("harmonic")]
            # strict=False: puede haber menos dedos escritos que notas pisadas.
            fingers = dict(
                zip([n["id"] for n in fretted], (beat.get("text") or "").split(), strict=False)
            )
            beats.append(
                {
                    "slot": int(round(pos)),
                    "notes": [
                        {
                            "string": n["string"],
                            "fret": n["fret"],
                            "finger": fingers.get(n["id"], ""),
                            "melody": "ACCENT" in n["techniques"],
                            "harmonic": bool(n.get("harmonic")),
                            "vibrato": "VIBRATO" in n["techniques"],
                        }
                        for n in beat.get("notes", [])
                    ],
                }
            )
            pos += 16 / beat["duration"] * (1.5 if beat.get("dots") else 1)
        out.append({**info[i], "slower": tempos.get(i), "beats": beats})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"tempo": score["meta"]["tempo_bpm"], "capo": score["tracks"][0]["capo"], "bars": out},
            f,
            ensure_ascii=False,
            indent=1,
        )
        f.write("\n")
