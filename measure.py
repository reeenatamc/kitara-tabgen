"""Mide un borrador automático contra la transcripción a mano.

El número que importa es cuánta melodía acierta, no cuántas notas detecta: un borrador con
el doble de notas de las que se tocan es más trabajo de corregir que uno con la mitad.

La melodía es la nota más aguda de cada pulso, de Do3 (MIDI 57) hacia arriba. Una nota
cuenta como acertada si está en la misma altura y a no más de una semicorchea de donde la
puso la mano: el borrador cuantiza a la semicorchea y clavarla exacta no es razonable.

Uso: measure.py <slug-del-borrador> [compás-inicial] [compás-final]
"""

import json
import sys

import paths

#: Afinación estándar, de la primera cuerda a la sexta.
TUNING = [64, 59, 55, 50, 45, 40]

#: Desde esta altura MIDI una nota cuenta como melodía.
MELODY_FLOOR = 57

#: Tolerancia en semicorcheas al comparar cuándo entra una nota.
SLOP = 1

#: Los compases de la vuelta, las dos pasadas, que es donde está la melodía reconocible.
DEFAULT_RANGE = (17, 31)


def melody_by_bar(path):
    """Por compás, las parejas `(semicorchea, altura)` de la melodía y el total de notas."""
    with open(path, encoding="utf-8") as f:
        score = json.load(f)
    out = []
    for bar in score["tracks"][0]["staves"][0]["bars"]:
        position, melody, total = 0.0, set(), 0
        for beat in bar["voices"][0]["beats"]:
            notes = [n for n in beat.get("notes", []) if not n.get("tie_destination")]
            total += len(notes)
            if notes:
                highest = max(TUNING[n["string"] - 1] + n["fret"] for n in notes)
                if highest >= MELODY_FLOOR:
                    melody.add((int(position), highest))
            position += 16 / beat["duration"] * (1.5 if beat.get("dots") else 1)
        out.append((melody, total))
    return out


def found(wanted, draft):
    """Las notas de la mano que el borrador acertó, con su tolerancia."""
    return {
        (slot, pitch)
        for slot, pitch in wanted
        if any(abs(slot - s) <= SLOP and pitch == p for s, p in draft)
    }


def compare(hand, draft, first, last):
    """Compás a compás: qué se acertó, qué se perdió y qué se inventó."""
    rows = []
    for i in range(first, last):
        wanted, hand_notes = hand[i]
        got, draft_notes = draft[i] if i < len(draft) else (set(), 0)
        hits = found(wanted, got)
        rows.append(
            {
                "bar": i,
                "wanted": len(wanted),
                "hits": len(hits),
                "missed": sorted(wanted - hits),
                "invented": len(got) - len(hits),
                "hand_notes": hand_notes,
                "draft_notes": draft_notes,
            }
        )
    return rows


def report(rows):
    """Lo imprime, con una línea por compás y el total al final."""
    print("compás  melodía  acertada  inventada  notas mano/auto")
    for r in rows:
        print(
            "%6d  %7d  %8d  %9d  %6d/%d"
            % (r["bar"], r["wanted"], r["hits"], r["invented"], r["hand_notes"], r["draft_notes"])
        )

    wanted = sum(r["wanted"] for r in rows)
    hits = sum(r["hits"] for r in rows)
    print(
        "\nmelodía acertada %d/%d (%.0f%%), inventadas %d, notas mano %d auto %d"
        % (
            hits,
            wanted,
            100 * hits / wanted if wanted else 0,
            sum(r["invented"] for r in rows),
            sum(r["hand_notes"] for r in rows),
            sum(r["draft_notes"] for r in rows),
        )
    )


def main(slug, first=None, last=None):
    hand = melody_by_bar(paths.song("solamente-uno"))
    draft = melody_by_bar(paths.song(slug))
    a, b = (int(first), int(last)) if first and last else DEFAULT_RANGE
    report(compare(hand, draft, a, b))


if __name__ == "__main__":
    main(*sys.argv[1:4])
