"""Draft tab from a recording: notes with basic-pitch, beat grid with librosa, strings and frets by least hand movement.

Usage: transcribir.py audio.wav song.json guide.json "Title"
The result is a draft to correct by ear: every slot keeps its top note (melody) and bass, plus up to two inner voices.
"""
import itertools
import sys
import warnings

warnings.filterwarnings("ignore")

import librosa
import numpy as np
from basic_pitch.inference import predict

from tabgen import write_guide, write_song

TUNING = [64, 59, 55, 50, 45, 40]  # string 1 to 6
MAX_FRET = 17
DUR_STEPS = (16, 12, 8, 6, 4, 3, 2, 1)
FINGERS = "IMAÑ"
NAMES = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
CHORD_SHAPES = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10)}


def detect_notes(wav):
    _, _, events = predict(wav, onset_threshold=0.5, frame_threshold=0.3, minimum_note_length=80,
                           minimum_frequency=75, maximum_frequency=1400)
    return sorted((s, e, p, a) for s, e, p, a, _ in events)


def sixteenth_grid(wav):
    y, sr = librosa.load(wav, sr=22050)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, start_bpm=100, units="time")
    tempo = float(np.atleast_1d(tempo)[0])
    period = float(np.median(np.diff(beats)))
    lead = int(np.ceil(beats[0] / period)) + 1
    tail = int(np.ceil((len(y) / sr - beats[-1]) / period)) + 1
    beats = np.concatenate([beats[0] - period * np.arange(lead, 0, -1), beats, beats[-1] + period * np.arange(1, tail + 1)])
    grid = np.concatenate([np.linspace(a, b, 4, endpoint=False) for a, b in zip(beats[:-1], beats[1:])])
    return grid, 60.0 / period if period else tempo


def clean(notes, min_amp=0.35, retrigger=0.06, factor=1.1):
    """Drops weak notes and the re-detections of a pitch that is still ringing from its previous attack."""
    kept, last = [], {}
    for start, end, pitch, amp in notes:
        prev = last.get(pitch)
        if amp < min_amp or (prev and start < prev[1] + retrigger and amp <= prev[2] * factor):
            if prev:
                last[pitch] = (prev[0], max(prev[1], end), prev[2])
            continue
        kept.append((start, end, pitch, amp))
        last[pitch] = (start, end, amp)
    return kept


def quantize(notes, grid, inner_voices=1):
    """slot -> {pitch: amplitude}: melody, bass and the strongest inner voice, without octave ghosts."""
    slots = {}
    for start, _, pitch, amp in notes:
        k = int(np.argmin(np.abs(grid - start)))
        cur = slots.setdefault(k, {})
        cur[pitch] = max(cur.get(pitch, 0), amp)
    out = {}
    for k, cur in slots.items():
        # A pitch an octave or a twelfth above a louder note is usually that note's overtone.
        cur = {p: a for p, a in cur.items() if not any(cur.get(p - d, 0) >= a for d in (12, 19, 24))}
        pitches = sorted(cur)
        keep = {pitches[0], pitches[-1]}
        inner = sorted(pitches[1:-1], key=lambda p: -cur[p])[:inner_voices]
        out[k] = {p: cur[p] for p in keep | set(inner)}
    return out


def fit_range(pitch):
    while pitch < TUNING[-1]:
        pitch += 12
    while pitch > TUNING[0] + MAX_FRET:
        pitch -= 12
    return pitch


def voicings(pitches):
    """Every way to put the pitches on distinct strings with a fretted span of at most four frets."""
    options = [[(s + 1, p - open_) for s, open_ in enumerate(TUNING) if 0 <= p - open_ <= MAX_FRET] for p in pitches]
    found = []
    for combo in itertools.product(*options):
        if len({s for s, _ in combo}) < len(combo):
            continue
        fretted = [f for _, f in combo if f > 0]
        if fretted and max(fretted) - min(fretted) > 3:
            continue
        found.append(combo)
    return found


def place(slots):
    """Strings and frets for every slot, minimizing hand jumps (Viterbi over voicings)."""
    keys = sorted(slots)
    layers = []
    for k in keys:
        pitches = sorted({fit_range(p) for p in slots[k]}, reverse=True)
        while True:
            options = voicings(pitches)
            if options or len(pitches) == 1:
                break
            pitches = pitches[:1] + pitches[2:]  # drop inner voices until it fits under one hand
        layers.append((pitches, options))

    def position(combo, prev):
        fretted = [f for _, f in combo if f > 0]
        return min(fretted) if fretted else prev

    best = [{i: (0.0, None, position(c, 0)) for i, c in enumerate(layers[0][1])}]
    for pitches, options in layers[1:]:
        prev_layer, prev_opts = best[-1], layers[len(best) - 1][1]
        cur = {}
        for i, combo in enumerate(options):
            fretted = [f for _, f in combo if f > 0]
            span = max(fretted) - min(fretted) if fretted else 0
            local = 0.3 * span + 0.04 * (min(fretted) if fretted else 0)
            choice = None
            for j, (cost, _, pos) in prev_layer.items():
                here = position(combo, pos)
                total = cost + local + (abs(here - pos) if fretted else 0)
                if choice is None or total < choice[0]:
                    choice = (total, j, here)
            cur[i] = choice
        best.append(cur)
    i = min(best[-1], key=lambda n: best[-1][n][0])
    chosen = []
    for depth in range(len(best) - 1, -1, -1):
        chosen.append((layers[depth][1][i], best[depth][i][2]))
        i = best[depth][i][1]
    chosen.reverse()
    return dict(zip(keys, chosen))


def spec(combo, pos, accent_string):
    tokens = []
    for string, fret in combo:
        finger = FINGERS[min(3, fret - pos)] if fret > 0 else ""
        tokens.append("%d:%d:%s:%s" % (string, fret, finger, "a" if string == accent_string else ""))
    return " ".join(tokens)


def bar_events(placed, start):
    """One bar of tabgen events; gaps that are not a single figure are split with tied notes or rests."""
    hits = [k for k in range(start, start + 16) if k in placed]
    marks = [start] + hits if not hits or hits[0] != start else hits
    events = []
    for n, k in enumerate(marks):
        end = marks[n + 1] if n + 1 < len(marks) else start + 16
        if k in placed:
            combo, pos = placed[k]
            top = min(combo)[0] if any(fit_range(TUNING[s - 1] + f) >= 57 for s, f in combo) else None
            first = spec(combo, pos, top)
            tied = " ".join("%d:%d::t" % (s, f) for s, f in combo)
        else:
            first = tied = ""
        slot, text = k, first
        while slot < end:
            step = next(d for d in DUR_STEPS if d <= end - slot)
            events.append((slot - start, text))
            slot += step
            text = tied
    return events


def chord_name(slots, start):
    weight = np.zeros(12)
    bass = None
    for k in range(start, start + 16):
        for p, a in slots.get(k, {}).items():
            weight[p % 12] += a
            if k - start in (0, 8) and (bass is None or p < bass):
                bass = p
    if weight.sum() == 0:
        return ""
    scores = []
    for root in range(12):
        for kind, shape in CHORD_SHAPES.items():
            score = sum(weight[(root + i) % 12] for i in shape) - 0.5 * weight.sum() * (len(shape) - 3) / 4
            if bass is not None and bass % 12 == root:
                score += 0.5 * weight.max()
            scores.append((score, root, kind))
    _, root, kind = max(scores)
    return NAMES[root] + kind


def main(wav, song_path, guide_path, title):
    notes = detect_notes(wav)
    grid, bpm = sixteenth_grid(wav)
    slots = quantize(clean(notes), grid)
    # Bar lines go where the low notes land most often.
    low = {k: sum(a for p, a in v.items() if p < 52) for k, v in slots.items()}
    phase = max(range(0, 16, 4), key=lambda o: sum(w for k, w in low.items() if (k - o) % 16 in (0, 8)) +
                sum(w for k, w in low.items() if (k - o) % 16 == 0))
    first, last = min(slots), max(slots)
    starts = list(range(first - (first - phase) % 16, last + 1, 16))
    placed = place(slots)

    plan, chords, info, sections = [], [], [], []
    for n, start in enumerate(starts):
        plan.append((bar_events(placed, start), "MP", False))
        chords.append(chord_name(slots, start))
    # The chord only shows when it changes.
    shown = [c if i == 0 or c != chords[i - 1] else "" for i, c in enumerate(chords)]
    for i in range(0, len(plan), 8):
        sections.append(("Verso", "Parte %d" % (i // 8 + 1), i, min(i + 8, len(plan))))
    for i, chord in enumerate(chords):
        info.append({"step": i // 2 + 1, "section": "Parte %d" % (i // 8 + 1), "mood": "", "chord": chord, "cue": "",
                     "tip": "Borrador automático: revisa este compás de oído contra el video."})
    meta = {"title": title, "artist": "", "tab_author": "borrador automático", "source_url": "",
            "tempo_bpm": float(round(bpm)), "tags": ["borrador"]}
    score = write_song(song_path, meta, 0, sections, plan, chords=shown)
    write_guide(guide_path, score, info)
    print("notas %d, tempo %d, compases %d" % (sum(len(v) for v in slots.values()), round(bpm), len(plan)))
    print("acordes:", " ".join(c or "-" for c in chords))


if __name__ == "__main__":
    main(*sys.argv[1:5])
