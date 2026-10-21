# Generador de tablaturas

Herramientas con las que se sacan, arreglan y validan las tablaturas de
[kitara](https://github.com/reeenatamc/kitara). Viven fuera del repo de la aplicación porque
son taller, no producto.

## Qué hay

- `tabgen.py` — escribe la canción y su guía desde una notación compacta: una lista por
  compás de `(posición en semicorcheas 0-15, o 0-23 en 12/8, "cuerda:traste:dedo:marca ...")`.
- `transcriber/` — borrador automático desde una grabación.
- `bench.py` — mide el borrador contra GuitarSet, etapa por etapa.
- `measure.py` — mide un borrador contra una tablatura hecha a mano.
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

**Es un borrador para corregir de oído, no una transcripción.** Medido con `bench.py` sobre
144 grabaciones de GuitarSet (bossa nova y cantautor): acierta el 76 % de las notas, el 77 %
de la melodía y el 81 % del bajo, y un 29 % de lo que escribe no se tocó. Contra la versión a
mano de «Solamente uno»: el 77 % de la melodía en orden y el 41 % en su sitio exacto; lo que
más falla ahí es la cuadrícula, porque el tempo sale bien sólo en 80 de los 144 fragmentos.
Sale etiquetado con `borrador` en `meta.tags`.

Por dentro son cuatro piezas, y sólo la primera necesita los modelos pesados:

| pieza | qué decide |
|---|---|
| `signal` | qué notas suenan y dónde cae el pulso |
| `music` | qué se queda en cada semicorchea, dónde empiezan los compases, qué acorde es |
| `guitar` | en qué cuerda y traste se pisa, con la mano moviéndose lo menos posible |
| `draft` | el bajo del pulgar, y el JSON de la canción y de la guía |

El compás se decide por el pulso: `music.meter_of` mira en qué parte del pulso caen los
ataques y elige entre dos reglas, el pulso partido en dos (4/4, 16 semicorcheas por compás)
o en tres (se escribe como 12/8, 24 semicorcheas por compás). Un 6/8 sale como 12/8. La
rejilla, las barras de compás, el pulgar y el tempo (en negras en 12/8) siguen de ahí.

`pipeline` encadena las reglas de `music` y `draft` en un solo sitio. Lo usan `transcribe.py`
y `bench.py`, así que lo que se mide es exactamente lo que se entrega.

## Medir y cambiar una regla

El banco necesita GuitarSet (Zenodo, CC BY 4.0, doi 10.5281/zenodo.3371780): sólo
`annotation.zip` y `audio_mono-mic.zip`, descomprimidos en `datasets/guitarset/annotation` y
`datasets/guitarset/audio_mono-mic`. La carpeta está fuera de git.

```bash
.venv/bin/python bench.py            # 144 fragmentos de bossa nova y cantautor
.venv/bin/python measure.py solamente-uno-auto solamente-uno
```

La primera vez pasa todo por basic-pitch (unos diez minutos) y lo guarda en `out/bench/`;
después, medir una regla cambiada tarda segundos.

Una regla entra sólo si cumple las tres cosas:

1. Mejora el banco completo, no un fragmento ni una canción.
2. No empeora «Solamente uno» frente a su versión a mano.
3. Funciona sola, sin opciones ni perillas: si una regla sirve para unas grabaciones y
   empeora otras, el programa tiene que distinguirlas por sí mismo, o la regla no entra.

Lo medido se anota en el docstring de la regla, con los números de antes y después, para
que nadie la deshaga sin volver a medir.

## Entorno

Python 3.11 con uv. En esta Mac Intel hacen falta `numba<0.61`, `llvmlite<0.44`,
`setuptools<81` y `scikit-learn<1.6`.

```bash
uv venv --python 3.11 && .venv/bin/python -m unittest discover -s tests -t .
```

Las rutas a kitara son absolutas en `check/Cargo.toml`, `transcribe.sh` y `render.sh`: si el
repo se renombra o se mueve, hay que tocarlas.

El seguidor de pulso necesita el modelo de Beat This en ONNX, 190 MB, que va fuera de git:

```bash
mkdir -p models
for f in beat_this.onnx config.json mel-filterbank.bin; do
  curl -sL -o "models/$f" "https://huggingface.co/musetric/beat-this-onnx/resolve/main/$f"
done
```

## Licencia

GPL-3.0, la misma que kitara: se puede usar, estudiar, modificar y redistribuir, y quien lo
distribuya tiene que publicar su código bajo la misma licencia. Está en [LICENSE](LICENSE).

Las obras de terceros conservan la suya: basic-pitch es Apache-2.0, librosa ISC, y el modelo
de Beat This que se baja aparte es MIT. GuitarSet, que sólo hace falta para medir y no se
distribuye aquí, es CC BY 4.0.

