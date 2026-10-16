# Generador de tablaturas

Herramientas con las que se sacan, arreglan y validan las tablaturas de
[kitara](https://github.com/reeenatamc/kitara). Viven fuera del repo de la aplicación porque
son taller, no producto.

## Qué hay

- `tabgen.py` — escribe la canción y su guía desde una notación compacta: una lista por
  compás de `(posición en semicorcheas 0-15, "cuerda:traste:dedo:marca ...")`.
- `transcriber/` — borrador automático desde una grabación.
- `check/` — valida un JSON contra `kitara-core` y saca su AlphaTex.
- `render.sh`, `render.mjs` — audio de una tablatura con alphaTab en node.
- Un archivo por canción (`salvatore.py`, `solamente-uno.py`) con su notación.

## El borrador automático

```bash
./transcribe.sh video.mp4 mi-cancion "Mi canción"
```

Saca el audio, detecta las notas con basic-pitch, el pulso con librosa, y elige cuerdas y
trastes buscando que la mano se mueva lo menos posible. Deja la canción y la guía en kitara,
las valida y renderiza el audio. Tarda unos 30 segundos por minuto de grabación.

**Es un borrador para corregir de oído, no una transcripción.** Medido contra la versión a
mano de «Solamente uno»: acierta la forma y los acordes, y el 52 % de la melodía de la
vuelta. Donde el pulso es parejo sale casi completa; donde se toca libre o la cuadrícula se
corre, se pierde. Sale etiquetado con `borrador` en `meta.tags`.

Por dentro son cuatro piezas, y sólo la primera necesita los modelos pesados:

| pieza | qué decide |
|---|---|
| `signal` | qué notas suenan y dónde cae el pulso |
| `music` | qué se queda en cada semicorchea, dónde empiezan los compases, qué acorde es |
| `guitar` | en qué cuerda y traste se pisa, con la mano moviéndose lo menos posible |
| `draft` | el JSON de la canción y de la guía |

## Entorno

Python 3.11 con uv. En esta Mac Intel hacen falta `numba<0.61`, `llvmlite<0.44`,
`setuptools<81` y `scikit-learn<1.6`.

```bash
uv venv --python 3.11 && .venv/bin/python -m unittest discover -s tests -t .
```

Las rutas a kitara son absolutas en `check/Cargo.toml`, `transcribe.sh` y `render.sh`: si el
repo se renombra o se mueve, hay que tocarlas.
