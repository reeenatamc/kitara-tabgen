"""Mide el transcriptor en varias canciones a la vez.

Ajustar contra una sola canción es la forma más fácil de engañarse: cualquier cambio se
puede afinar hasta que ese número suba, y lo normal es que entonces baje en las demás. Esto
corre todas y muestra la tabla completa, así que un cambio que ayuda en una y estropea tres
se ve en el momento.

Las grabaciones de `out/*.wav` son el render de las tablaturas escritas a mano, así que la
verdad es exacta: si el transcriptor no recupera una tablatura desde el audio de esa misma
tablatura, el problema es suyo y no de la grabación. Son más fáciles que un video de verdad
—sin ruido de sala, un solo instrumento— y a la vez más difíciles para el detector de
pulso, porque el sintetizador no da el golpe de la uña. Lo que vale de ellas es la
comparación entre dos ejecuciones, no el número suelto.

La fila que manda es la del video, que es el caso real. Las demás son la red de seguridad.

Tres columnas, y hay que leerlas en este orden:

- **tempo**: la razón entre el detectado y el de la tablatura. Si no es 1, las barras del
  borrador no se corresponden con las de la mano y la columna de melodía no mide nada.
- **melodía**: notas acertadas en su compás y su semicorchea. Es lo que de verdad importa,
  porque es lo que se puede corregir de oído.
- **sin ritmo**: las mismas notas en el mismo orden, sin mirar cuándo suenan. Separa «no oyó
  las notas» de «las oyó y las colocó mal».

Uso: validate.py [slug ...]
"""

import subprocess
import sys
from pathlib import Path

import measure
import paths

HERE = Path(__file__).resolve().parent

#: El caso real: audio de un video, con su tablatura a mano como referencia.
#: La melodía reconocible está en los compases de la vuelta, las dos pasadas.
REAL = [("solamente-uno-auto", "solamente-uno", 17, 31)]

#: Renders de las tablaturas a mano. La referencia es la propia tablatura.
RENDERS = [
    "solamente-uno",
    "solamente-uno-facil",
    "solamente-uno-melodica",
    "salvatore",
    "hasta-siempre-lo-mejor",
]


def transcribe(wav, slug, title):
    """Saca un borrador de un wav y lo deja en kitara con ese nombre."""
    subprocess.run(
        [
            str(HERE / ".venv" / "bin" / "python"),
            str(HERE / "transcribe.py"),
            str(wav),
            str(paths.song(slug)),
            str(paths.guide(slug)),
            title,
        ],
        check=True,
        capture_output=True,
    )


def tempo_ratio(reference_slug, draft_slug):
    """El tempo detectado partido por el de la tablatura a mano."""
    hand = measure.read(paths.song(reference_slug))["meta"]["tempo_bpm"]
    draft = measure.read(paths.song(draft_slug))["meta"]["tempo_bpm"]
    return draft / hand if hand else 0.0


def result(reference_slug, draft_slug, first=None, last=None):
    """Las tres medidas de un borrador contra su referencia."""
    return {
        "tempo": tempo_ratio(reference_slug, draft_slug),
        "rows": measure.rows_for(draft_slug, reference_slug, first, last),
        "sequence": measure.sequence_score(paths.song(reference_slug), paths.song(draft_slug)),
    }


def line(name, r):
    """Una fila de la tabla. El tempo se marca cuando no es 1, porque invalida la melodía."""
    t = measure.totals(r["rows"])
    mark = "" if 0.95 <= r["tempo"] <= 1.05 else "  <-- tempo"
    return "%-26s %5.2f  %5.0f%%  %5.0f%%  %4d/%-4d %5d   %5d/%d%s" % (
        name,
        r["tempo"],
        measure.score(r["rows"]),
        r["sequence"],
        t["hits"],
        t["wanted"],
        t["invented"],
        t["hand_notes"],
        t["draft_notes"],
        mark,
    )


def main(*slugs):
    wanted = set(slugs) if slugs else None
    header = ("", "tempo", "melodía", "sin ritmo", "acertada", "inventa", "notas mano/auto")
    print("%-26s %5s  %7s  %9s  %9s %5s   %11s" % header)

    for draft_slug, reference, first, last in REAL:
        if wanted and reference not in wanted:
            continue
        if paths.song(draft_slug).exists():
            print(line("VIDEO " + reference, result(reference, draft_slug, first, last)))

    print()
    for slug in RENDERS:
        if wanted and slug not in wanted:
            continue
        wav = HERE / "out" / f"{slug}.wav"
        if not wav.exists():
            print("%-26s sin render" % ("render " + slug))
            continue
        draft = f"{slug}-desde-render"
        transcribe(wav, draft, f"{slug} (desde el render)")
        print(line("render " + slug, result(slug, draft)))


if __name__ == "__main__":
    main(*sys.argv[1:])
