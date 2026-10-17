#!/bin/sh
# Uso: render.sh <slug o ruta a un .json> [salida.m4a]
#
# Valida la partitura con kitara-core y renderiza su audio con alphaTab.
#
# Acepta una ruta directa además del nombre de una cancion de kitara, para poder renderizar
# un borrador de out/drafts/ sin copiarlo a songs/: ahi solo van las tablaturas de verdad.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$HOME/Documents/GitHub/kitara"

if [ -f "$1" ]; then
  # Absoluta: mas abajo se hace cd a check/ y a kitara, y una relativa se rompe ahi.
  SONG="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
  SLUG="$(basename "$1" .json)"
else
  SLUG="$1"
  SONG="$REPO/songs/$SLUG.json"
fi
OUT="${2:-$HERE/out/$SLUG.m4a}"

mkdir -p "$HERE/out" "$(dirname "$OUT")"
(cd "$HERE/check" && cargo run -q -- "$SONG" > "$HERE/out/$SLUG.tex")
grep COMPAS "$HERE/out/$SLUG.tex" && exit 1
cp "$HERE/render.mjs" "$REPO/scripts/_tmp_render.mjs"
STATUS=0
(cd "$REPO" && node scripts/_tmp_render.mjs "$HERE/out/$SLUG.tex" "$HERE/out/$SLUG.wav") || STATUS=$?
rm -f "$REPO/scripts/_tmp_render.mjs"
[ $STATUS -eq 0 ] || exit $STATUS
ffmpeg -v error -y -i "$HERE/out/$SLUG.wav" -c:a aac -b:a 192k "$OUT"
echo "audio: $OUT"
