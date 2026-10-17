"""Mide el transcriptor en varios casos a la vez.

Ajustar contra una sola canción es la forma más fácil de engañarse: cualquier cambio se
puede afinar hasta que ese número suba, y lo normal es que entonces baje en las demás. Esto
corre todos los casos y muestra la tabla completa, así que un cambio que ayuda en uno y
estropea tres se ve en el momento. Pasó: realzar la parte percusiva antes de buscar el pulso
subía los renders del 6 % al 64 % y hundía el video del 53 % al 18 %.

Los borradores van a `out/drafts/`, que está fuera de git. No son tablaturas de nadie, son
material de medición que se rehace en cada ejecución, y escribirlos en kitara ensuciaba ese
repo con archivos que no eran de nadie.

Dos clases de caso:

- **El video** es el real y es el que manda. Una regresión aquí no la compensa ninguna
  mejora en los demás.
- **Los renders** son el audio de las tablaturas escritas a mano, así que la verdad es
  exacta: si el transcriptor no recupera una tablatura desde el audio de esa misma
  tablatura, el problema es suyo. Son más fáciles en todo menos para el detector de pulso,
  porque el sintetizador no da el golpe de la uña. Son la red de seguridad.

Tres columnas, y se leen en este orden:

- **tempo**: el detectado partido por el de la tablatura. Si no es 1, las barras no se
  corresponden y la columna de melodía no mide nada.
- **melodía**: notas acertadas en su compás y su semicorchea. Es lo que importa, porque es
  lo que se puede corregir de oído.
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

#: El caso real: el audio sacado del video, con la tablatura a mano como referencia.
#: La melodía reconocible está en los compases de la vuelta, las dos pasadas.
REAL = [("solamente-uno-auto-fuente.wav", "solamente-uno", 17, 31)]

#: Renders de las tablaturas a mano. La referencia es la propia tablatura.
RENDERS = [
    "solamente-uno",
    "solamente-uno-facil",
    "solamente-uno-melodica",
    "salvatore",
    "hasta-siempre-lo-mejor",
]


def transcribe(wav, slug):
    """Saca un borrador de un wav y lo deja en `out/drafts/`. Devuelve su ruta."""
    song = paths.draft(slug)
    subprocess.run(
        [
            str(HERE / ".venv" / "bin" / "python"),
            str(HERE / "transcribe.py"),
            str(wav),
            str(song),
            str(paths.draft(f"{slug}-guia")),
            slug,
        ],
        check=True,
        capture_output=True,
    )
    return song


def tempo_ratio(reference, draft):
    """El tempo detectado partido por el de la tablatura a mano."""
    hand = measure.read(reference)["meta"]["tempo_bpm"]
    got = measure.read(draft)["meta"]["tempo_bpm"]
    return got / hand if hand else 0.0


def result(reference, draft, first=None, last=None):
    """Las tres medidas de un borrador contra su referencia."""
    return {
        "tempo": tempo_ratio(reference, draft),
        "rows": measure.rows_between(reference, draft, first, last),
        "sequence": measure.sequence_score(reference, draft),
    }


def line(name, r):
    """Una fila de la tabla. El tempo se marca cuando no es 1, porque invalida la melodía."""
    t = measure.totals(r["rows"])
    mark = "" if 0.95 <= r["tempo"] <= 1.05 else "  <-- tempo"
    return "%-30s %5.2f  %5.0f%%  %5.0f%%  %4d/%-4d %5d   %5d/%d%s" % (
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
    print("%-30s %5s  %7s  %9s  %9s %5s   %11s" % header)

    for source, reference, first, last in REAL:
        if wanted and reference not in wanted:
            continue
        wav = HERE / "out" / source
        if not wav.exists():
            print("%-30s sin audio de origen" % ("VIDEO " + reference))
            continue
        draft = transcribe(wav, f"{reference}-desde-video")
        print(line("VIDEO " + reference, result(paths.song(reference), draft, first, last)))

    print()
    for slug in RENDERS:
        if wanted and slug not in wanted:
            continue
        wav = HERE / "out" / f"{slug}.wav"
        if not wav.exists():
            print("%-30s sin render" % ("render " + slug))
            continue
        draft = transcribe(wav, f"{slug}-desde-render")
        print(line("render " + slug, result(paths.song(slug), draft)))


if __name__ == "__main__":
    main(*sys.argv[1:])
