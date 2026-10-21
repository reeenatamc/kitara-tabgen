"""Banco de pruebas del transcriptor contra GuitarSet.

`measure.py` compara un borrador con una tablatura hecha a mano, compás a compás. Sirve para
una canción, pero un cambio que mejora una canción puede empeorar otras, y no hay forma de
saberlo mirando una sola. Este banco corre el transcriptor sobre muchas grabaciones cuya
respuesta se conoce nota por nota y dice, etapa por etapa, cuánto acierta, cuánto pierde y
cuánto inventa.

La respuesta sale de GuitarSet: guitarra acústica grabada con una pastilla que capta cada
cuerda por separado, así que las notas anotadas son las que vibraron, no las que alguien
creyó oír. Se baja aparte a `datasets/guitarset/` (ver el README).

Se usan los estilos más cercanos a «Solamente uno», que es la canción modelo: bossa nova y
cantautor, acústica con bajo y melodía a la vez. El rock, el funk y el jazz quedan fuera
porque no se parecen a lo que se transcribe aquí, y medir contra ellos empujaría las reglas
hacia otra música.

Las notas detectadas y los pulsos se guardan en `out/bench/`, porque basic-pitch es lo lento
y no cambia cuando se tocan las reglas: con eso guardado, probar una regla tarda segundos.

Uso: bench.py [estilos] [máximo de fragmentos]    p. ej. `bench.py BN,SS 12`
"""

import json
import pickle
import re
import sys
from pathlib import Path

from transcriber import draft, music, pipeline

#: Dónde se descomprime GuitarSet.
GUITARSET = Path(__file__).resolve().parent / "datasets" / "guitarset"

#: Dónde se guardan las etapas ya calculadas de cada fragmento.
CACHE = Path(__file__).resolve().parent / "out" / "bench"

#: Estilos de GuitarSet que se parecen a lo que se transcribe: bossa nova y cantautor.
STYLES = ("BN", "SS")

#: Segundos de margen para dar una nota por acertada.
#:
#: Es el mismo para todas las etapas, para que se puedan comparar entre sí. Cubre una
#: semicorchea a unos 150 bpm: el borrador coloca todo en semicorcheas, así que pedir menos
#: mediría el redondeo de la cuadrícula en vez de la transcripción.
TOLERANCE = 0.1

#: Ataques más juntos que esto forman un solo golpe de mano: el mismo margen con el que el
#: transcriptor junta los ataques simultáneos.
TOGETHER = music.TOGETHER

#: Distancias en semitonos de los armónicos que más se confunden con una nota. Incluye la
#: doble octava y tercera (28), que el transcriptor no filtra, para que el banco la cuente.
OVERTONES = (12, 19, 24, 28)


def excerpts(styles=STYLES):
    """Los fragmentos de esos estilos que tienen audio y anotación, en orden."""
    found = []
    for jams in sorted((GUITARSET / "annotation").glob("*.jams")):
        style = jams.stem.split("_")[1][:2]
        wav = GUITARSET / "audio_mono-mic" / f"{jams.stem}_mic.wav"
        if style in styles and wav.exists():
            found.append((jams, wav))
    return found


def tempo_of(jams):
    """El tempo con que se tocó, que va en el nombre: `00_BN1-129-Eb_comp`."""
    match = re.search(r"-(\d+)-", jams.stem)
    return int(match.group(1)) if match else None


def truth(jams):
    """Las notas anotadas, `(inicio, altura)`, de las seis cuerdas juntas.

    GuitarSet guarda una anotación `note_midi` por cuerda, con la altura en decimales porque
    sigue la afinación real. Se redondea al semitono, que es lo que puede escribir una tab.
    """
    with open(jams, encoding="utf-8") as f:
        data = json.load(f)
    notes = []
    for annotation in data["annotations"]:
        if annotation["namespace"] != "note_midi":
            continue
        for event in annotation["data"]:
            notes.append((event["time"], round(event["value"])))
    return sorted(notes)


def detect(wav):
    """Lo que sale del audio: las notas de basic-pitch y los pulsos de librosa.

    Es lo lento y no depende de las reglas, así que es lo único que se guarda. La rejilla de
    semicorcheas no: depende de cómo se parta el pulso, y eso lo decide el transcriptor.
    """
    # Se importa aquí porque carga basic-pitch y TensorFlow: el resto del banco, y sus
    # pruebas, no los necesitan.
    from transcriber import signal

    notes = signal.detect_notes(str(wav))
    beats, period = signal.beats(str(wav))
    return {"notes": notes, "beats": beats, "period": period}


def cached_detect(wav):
    """`detect`, guardando el resultado para no volver a pasar basic-pitch.

    Los archivos guardados antes de que la rejilla se calculara aparte traen `grid` y `bpm`
    en vez de `beats` y `period`: se completan calculando sólo los pulsos, que es rápido, y
    se reescriben. Las notas no se tocan, porque volver a pasarlas por basic-pitch tarda
    diez minutos y no han cambiado.
    """
    path = CACHE / f"{wav.stem}.pkl"
    if path.exists():
        with open(path, "rb") as f:
            result = pickle.load(f)
        if "beats" in result:
            return result
        from transcriber import signal

        beats, period = signal.beats(str(wav))
        result = {"notes": result["notes"], "beats": beats, "period": period}
    else:
        result = detect(wav)
    CACHE.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(result, f)
    return result


def stages(detected):
    """Las notas que deja cada etapa del transcriptor, como `(inicio, altura)`.

    Usa el mismo recorrido que `transcribe.py`, hasta antes de elegir cuerdas, que es donde
    se pierden o se inventan notas. Las posiciones de la rejilla se pasan a segundos para
    poder compararlas con la respuesta. Devuelve también el compás que se detectó.
    """
    notes = detected["notes"]
    result = pipeline.run(notes, detected["beats"], detected["period"])
    grid = result.grid

    def timed(by_slot):
        return sorted(
            (grid[slot], pitch)
            for slot, voices in by_slot.items()
            if 0 <= slot < len(grid)
            for pitch in voices
        )

    by_stage = {
        "basic-pitch": sorted((start, pitch) for start, _, pitch, _ in notes),
        "clean": sorted((start, pitch) for start, _, pitch, _ in result.cleaned),
        "quantize": timed(result.heard),
        "harmonize": timed(result.slots),
    }
    return by_stage, result.meter


def roles(notes, together=TOGETHER):
    """Qué papel tiene cada nota: `mel`, `bajo` o `int`.

    Las notas se juntan por ataques; en cada uno la más aguda es la melodía si llega a
    `draft.MELODY_FLOOR`, la más grave es el bajo si queda por debajo de `music.BASS_CEILING`,
    y el resto son voces internas. Son los mismos límites que usa el transcriptor.
    """
    out, group = [], []

    def flush():
        if not group:
            return
        high = max(p for _, p in group)
        low = min(p for _, p in group)
        for t, p in group:
            if p == high and p >= draft.MELODY_FLOOR:
                role = "mel"
            elif p == low and p < music.BASS_CEILING:
                role = "bajo"
            else:
                role = "int"
            out.append((t, p, role))

    for t, p in notes:
        if group and t - group[0][0] > together:
            flush()
            group = []
        group.append((t, p))
    flush()
    return out


def match(wanted, got, tolerance=TOLERANCE):
    """Empareja cada nota de la respuesta con a lo sumo una detectada.

    Devuelve los índices emparejados de cada lista. Una nota detectada no puede acertar dos
    notas de la respuesta: si no, un borrador que repite la misma altura sin parar
    acertaría todo.
    """
    used = set()
    hits = {}
    for i, (t, p) in enumerate(wanted):
        best = None
        for j, (s, q) in enumerate(got):
            if q != p or j in used or abs(s - t) > tolerance:
                continue
            if best is None or abs(s - t) < abs(got[best][0] - t):
                best = j
        if best is not None:
            used.add(best)
            hits[i] = best
    return hits


def is_overtone(note, wanted, tolerance=TOLERANCE):
    """Si una nota inventada cae justo en un armónico de una nota que sí sonaba."""
    t, p = note
    return any(abs(s - t) <= tolerance and p - q in OVERTONES for s, q in wanted)


def score(wanted, got):
    """Cuentas de una etapa en un fragmento."""
    hits = match(wanted, got)
    hit_got = set(hits.values())
    invented = [n for j, n in enumerate(got) if j not in hit_got]
    by_role = {}
    for i, (_, _, role) in enumerate(roles(wanted)):
        total, found = by_role.get(role, (0, 0))
        by_role[role] = (total + 1, found + (i in hits))
    return {
        "wanted": len(wanted),
        "got": len(got),
        "hits": len(hits),
        "invented": len(invented),
        "overtones": sum(is_overtone(n, wanted) for n in invented),
        "roles": by_role,
    }


def add(total, part):
    """Suma las cuentas de un fragmento al acumulado."""
    for key in ("wanted", "got", "hits", "invented", "overtones"):
        total[key] = total.get(key, 0) + part[key]
    roles_total = total.setdefault("roles", {})
    for role, (n, found) in part["roles"].items():
        a, b = roles_total.get(role, (0, 0))
        roles_total[role] = (a + n, b + found)
    return total


def percent(a, b):
    return 100 * a / b if b else 0.0


def report(totals, tempos, meters):
    """Una línea por etapa con lo que acierta, lo que pierde y lo que inventa."""
    print("etapa         acierta  melodía  bajo   inventa  (de eso, armónicos)")
    for name, t in totals.items():
        mel = t["roles"].get("mel", (0, 0))
        bass = t["roles"].get("bajo", (0, 0))
        print(
            "%-12s  %6.0f%%  %6.0f%%  %4.0f%%  %6.0f%%  %6.0f%%"
            % (
                name,
                percent(t["hits"], t["wanted"]),
                percent(mel[1], mel[0]),
                percent(bass[1], bass[0]),
                percent(t["invented"], t["got"]),
                percent(t["overtones"], t["invented"]),
            )
        )
    right = sum(1 for real, seen in tempos if abs(seen - real) / real < 0.08)
    halved = sum(
        1 for real, seen in tempos if min(abs(seen - 2 * real), abs(seen - real / 2)) / real < 0.08
    )
    print(
        "\ntempo: %d de %d bien, %d al doble o a la mitad, %d en otra cosa"
        % (right, len(tempos), halved, len(tempos) - right - halved)
    )
    compound = sum(1 for meter in meters if meter == music.COMPOUND)
    print(
        "compás: %d simples, %d compuestos (en GuitarSet BN y SS todos son 4/4)"
        % (len(meters) - compound, compound)
    )
    print(
        "acierta: notas de la respuesta encontradas con la misma altura a %.2f s o menos."
        % TOLERANCE
    )
    print("inventa: notas detectadas que no corresponden a ninguna de la respuesta.")


def main(styles=None, limit=None):
    styles = styles or ",".join(STYLES)
    chosen = excerpts(tuple(styles.split(",")))
    if limit:
        chosen = chosen[: int(limit)]
    if not chosen:
        sys.exit("No hay fragmentos: falta bajar GuitarSet a %s" % GUITARSET)

    totals, tempos, meters = {}, [], []
    for n, (jams, wav) in enumerate(chosen, 1):
        print("%d/%d %s" % (n, len(chosen), jams.stem), file=sys.stderr)
        wanted = truth(jams)
        detected = cached_detect(wav)
        result, meter = stages(detected)
        meters.append(meter)
        for name in ("basic-pitch", "clean", "quantize", "harmonize"):
            totals[name] = add(totals.get(name, {}), score(wanted, result[name]))
        real = tempo_of(jams)
        if real:
            tempos.append((real, 60.0 / detected["period"]))

    print("%d fragmentos de %s\n" % (len(chosen), styles))
    report(totals, tempos, meters)


if __name__ == "__main__":
    main(*sys.argv[1:3])
