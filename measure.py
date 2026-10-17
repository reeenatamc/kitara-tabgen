"""Mide un borrador automático contra una transcripción a mano.

El número que importa es cuánta melodía acierta, no cuántas notas detecta: un borrador con
el doble de notas de las que se tocan es más trabajo de corregir que uno con la mitad.

La melodía es la nota más aguda de cada pulso, de Do3 (MIDI 57) hacia arriba. Una nota
cuenta como acertada si está en la misma altura y a no más de una semicorchea de donde la
puso la mano. Esa tolerancia es el paso de cuantización del borrador, no un número elegido
para que el resultado salga mejor: el borrador coloca todo en semicorcheas, así que exigir
el instante exacto mediría el redondeo en vez de la transcripción.

Uso: measure.py <borrador> [referencia] [compás-inicial] [compás-final]

La referencia por omisión es el nombre del borrador sin el sufijo `-auto`. Sin compases, se
miden todos los que tenga la referencia.
"""

import json
import sys

import paths

#: Afinación estándar, de la primera cuerda a la sexta.
TUNING = [64, 59, 55, 50, 45, 40]

#: Desde esta altura MIDI una nota cuenta como melodía.
MELODY_FLOOR = 57

#: Tolerancia en semicorcheas: es el paso al que cuantiza el borrador.
SLOP = 1


def melody_of(score):
    """Por compás, las parejas `(semicorchea, altura)` de la melodía y el total de notas.

    La cejilla se suma a la altura. Sin eso, una tablatura con cejilla en el traste 2 se
    compara dos semitonos por debajo de lo que suena, y el acierto cae al 1 % aunque la
    transcripción sea buena: pasó con `salvatore` y con `hasta-siempre`.
    """
    track = score["tracks"][0]
    capo = track.get("capo", 0)
    out = []
    for bar in track["staves"][0]["bars"]:
        position, melody, total = 0.0, set(), 0
        for beat in bar["voices"][0]["beats"]:
            notes = [n for n in beat.get("notes", []) if not n.get("tie_destination")]
            total += len(notes)
            if notes:
                highest = max(TUNING[n["string"] - 1] + n["fret"] + capo for n in notes)
                if highest >= MELODY_FLOOR:
                    melody.add((int(position), highest))
            position += 16 / beat["duration"] * (1.5 if beat.get("dots") else 1)
        out.append((melody, total))
    return out


def read(path):
    """La partitura de un archivo."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def melody_by_bar(path):
    """Lo mismo que `melody_of`, leyendo la partitura de un archivo."""
    return melody_of(read(path))


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
    for i in range(first, min(last, len(hand))):
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


def sequence_of(score):
    """La melodía como lista de alturas, en orden, sin cuándo suena cada una.

    Es lo que queda de una melodía si se le quita el ritmo: «sol, la, si, do» sigue siendo
    reconocible aunque las figuras estén mal.
    """
    return [pitch for melody, _ in melody_of(score) for _, pitch in sorted(melody)]


def common_run(wanted, got):
    """La subsecuencia común más larga entre dos listas de alturas.

    Cuenta cuántas notas de la melodía aparecen en el borrador **en el mismo orden**,
    pudiendo saltarse las que sobran por medio.
    """
    rows = [[0] * (len(got) + 1) for _ in range(len(wanted) + 1)]
    for i, a in enumerate(wanted):
        for j, b in enumerate(got):
            rows[i + 1][j + 1] = rows[i][j] + 1 if a == b else max(rows[i][j + 1], rows[i + 1][j])
    return rows[len(wanted)][len(got)]


def sequence_score_of(reference, draft):
    """Qué parte de la melodía oyó el borrador, sin mirar el ritmo.

    Hace falta porque la medida por compás y semicorchea deja de medir nada cuando el tempo
    se detecta mal: a dos tercios del real, los compases del borrador no se corresponden con
    los de la tablatura y el acierto cae al 6 % aunque las notas estén. Esta no depende del
    tempo ni de dónde caigan las barras, así que separa «no oyó las notas» de «las oyó y las
    colocó mal», que son dos problemas distintos con arreglos distintos.

    No sustituye a la otra: un borrador con las notas correctas y el ritmo inventado no se
    puede corregir de oído. Sirve para saber cuál de los dos hay que arreglar.
    """
    wanted = sequence_of(reference)
    got = sequence_of(draft)
    if not wanted:
        return 0.0
    return 100 * common_run(wanted, got) / len(wanted)


def sequence_score(reference_path, draft_path):
    """Lo mismo, leyendo las dos partituras de sus archivos."""
    return sequence_score_of(read(reference_path), read(draft_path))


def totals(rows):
    """Los acumulados de una comparación."""
    return {
        "wanted": sum(r["wanted"] for r in rows),
        "hits": sum(r["hits"] for r in rows),
        "invented": sum(r["invented"] for r in rows),
        "hand_notes": sum(r["hand_notes"] for r in rows),
        "draft_notes": sum(r["draft_notes"] for r in rows),
    }


def score(rows):
    """El porcentaje de melodía acertada."""
    t = totals(rows)
    return 100 * t["hits"] / t["wanted"] if t["wanted"] else 0.0


def report(rows):
    """Una línea por compás y el total al final.

    El detalle por compás es lo que hace falta: un porcentaje global no distingue entre
    fallar todo un poco y tener tres compases a cero, que son fallos distintos con arreglos
    distintos.
    """
    print("compás  melodía  acertada  inventada  notas mano/auto")
    for r in rows:
        print(
            "%6d  %7d  %8d  %9d  %6d/%d"
            % (r["bar"], r["wanted"], r["hits"], r["invented"], r["hand_notes"], r["draft_notes"])
        )

    t = totals(rows)
    print(
        "\nmelodía acertada %d/%d (%.0f%%), inventadas %d, notas mano %d auto %d"
        % (t["hits"], t["wanted"], score(rows), t["invented"], t["hand_notes"], t["draft_notes"])
    )


def rows_between(reference_path, draft_path, first=None, last=None):
    """La comparación entre dos archivos de partitura."""
    hand = melody_by_bar(reference_path)
    draft = melody_by_bar(draft_path)
    a = int(first) if first is not None else 0
    b = int(last) if last is not None else len(hand)
    return compare(hand, draft, a, b)


def rows_for(draft_slug, reference_slug=None, first=None, last=None):
    """Lo mismo, con los nombres de dos canciones de kitara."""
    reference = paths.song(reference_slug or draft_slug.removesuffix("-auto"))
    return rows_between(reference, paths.song(draft_slug), first, last)


def main(draft_slug, reference_slug=None, first=None, last=None):
    report(rows_for(draft_slug, reference_slug, first, last))


if __name__ == "__main__":
    main(*sys.argv[1:5])
