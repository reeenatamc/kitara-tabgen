#!/bin/sh
# Usage: render.sh <slug> [audio.m4a]. Checks songs/<slug>.json with kitara-core and renders its audio.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$HOME/Documents/GitHub/kitara"
SLUG="$1"
OUT="${2:-$HERE/out/$SLUG.m4a}"
mkdir -p "$HERE/out" "$(dirname "$OUT")"
(cd "$HERE/check" && cargo run -q -- "$REPO/songs/$SLUG.json" > "$HERE/out/$SLUG.tex")
grep COMPAS "$HERE/out/$SLUG.tex" && exit 1
cp "$HERE/render.mjs" "$REPO/scripts/_tmp_render.mjs"
STATUS=0
(cd "$REPO" && node scripts/_tmp_render.mjs "$HERE/out/$SLUG.tex" "$HERE/out/$SLUG.wav") || STATUS=$?
rm -f "$REPO/scripts/_tmp_render.mjs"
[ $STATUS -eq 0 ] || exit $STATUS
ffmpeg -v error -y -i "$HERE/out/$SLUG.wav" -c:a aac -b:a 192k "$OUT"
echo "audio: $OUT"
