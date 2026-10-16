"""Builds a fretwork song and its practice guide from a compact bar notation.

A bar is a list of (slot, "string:fret:finger:marks ...") with slot in sixteenths (0-15). An empty spec is a rest.
Marks, any combination: p hammer or pull (on the origin note), t tied, v vibrato, a accent
(melody), n natural harmonic, s slide in from below. Each beat lasts until the next slot.
"""
import json
import uuid

DUR = {1: (16, 0), 2: (8, 0), 3: (8, 1), 4: (4, 0), 6: (4, 1), 8: (2, 0), 12: (2, 1), 16: (1, 0)}


class Builder:
    def __init__(self):
        self.next_id = 0

    def nid(self):
        self.next_id += 1
        return self.next_id

    def bar(self, events, dynamics, arpeggio=False):
        beats = []
        for i, (pos, spec) in enumerate(events):
            end = events[i + 1][0] if i + 1 < len(events) else 16
            if end - pos not in DUR:
                raise ValueError("gap %d at slot %d in %r" % (end - pos, pos, events))
            duration, dots = DUR[end - pos]
            notes, fingers = [], []
            for token in spec.split():
                parts = (token.split(":") + ["", ""])[:4]
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
                        raise ValueError("no finger for %s in %r" % (token, events))
                    fingers.append(parts[2])
                flags = [name for mark, name in (("p", "HAMMER_PULL"), ("v", "VIBRATO"), ("a", "ACCENT")) if mark in marks]
                note["techniques"] = " | ".join(flags + ["LET_RING"])
                notes.append(note)
            if len({n["string"] for n in notes}) != len(notes):
                raise ValueError("two notes on one string at slot %d in %r" % (pos, events))
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
    """The same bar with voices added underneath: fuller chords on beats 1 and 3, pairs in between."""
    out = []
    for pos, spec in events:
        tokens = spec.split()
        used = {t.split(":")[0] for t in tokens}
        extra = []
        if pos in (0, 8):
            extra = (full_late if pos == 8 and full_late else full).split()
        elif len(tokens) == 1 and "a" not in (tokens[0].split(":") + ["", ""])[3]:
            key = ":".join(tokens[0].split(":")[:2])
            extra = pairs.get(key, "").split()
        for token in extra:
            if token.split(":")[0] not in used:
                tokens.append(token)
                used.add(token.split(":")[0])
        out.append((pos, " ".join(tokens)))
    return out


def write_song(path, meta, capo, sections, plan, tempos=None, chords=None):
    """plan: one (events, dynamics, arpeggio) per bar. sections: (kind, label, start, end). chords: a name per bar."""
    builder = Builder()
    bars = [builder.bar(events, dynamics, arpeggio) for events, dynamics, arpeggio in plan]
    for bar, chord in zip(bars, chords or []):
        if chord:
            bar["voices"][0]["beats"][0]["chord"] = chord
    masters = []
    for i in range(len(plan)):
        master = {"index": i, "time_signature": {"numerator": 4, "denominator": 4},
                  "key_signature": {"fifths": 0, "mode": "Major"}}
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
        "tracks": [{"name": "Guitarra", "short_name": "Gtr", "midi_program": 25, "midi_channel": 0,
                    "tuning": {"midi_notes": [64, 59, 55, 50, 45, 40], "label": "Estándar"},
                    "capo": capo, "fret_count": 22,
                    "staves": [{"show_standard": False, "show_tabs": True, "bars": bars}]}],
        "sections": [{"id": i, "kind": kind, "label": label, "bar_start": start, "bar_end": end}
                     for i, (kind, label, start, end) in enumerate(sections)],
        "sync_points": [],
        "next_id": builder.next_id + 1,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(score, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return score


def write_guide(path, score, info):
    """info: one dict per bar with step, section, mood, chord, cue, tip."""
    bars = score["tracks"][0]["staves"][0]["bars"]
    tempos = {m["index"]: m["tempo"]["bpm"] for m in score["master_bars"] if m.get("tempo")}
    out = []
    for i, bar in enumerate(bars):
        pos, beats = 0.0, []
        for beat in bar["voices"][0]["beats"]:
            fretted = [n for n in beat.get("notes", []) if n["fret"] > 0 and not n.get("harmonic")]
            fingers = dict(zip([n["id"] for n in fretted], (beat.get("text") or "").split()))
            beats.append({"slot": int(round(pos)), "notes": [
                {"string": n["string"], "fret": n["fret"], "finger": fingers.get(n["id"], ""),
                 "melody": "ACCENT" in n["techniques"], "harmonic": bool(n.get("harmonic")),
                 "vibrato": "VIBRATO" in n["techniques"]} for n in beat.get("notes", [])]})
            pos += 16 / beat["duration"] * (1.5 if beat.get("dots") else 1)
        out.append({**info[i], "slower": tempos.get(i), "beats": beats})
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"tempo": score["meta"]["tempo_bpm"], "capo": score["tracks"][0]["capo"], "bars": out},
                  f, ensure_ascii=False, indent=1)
        f.write("\n")
