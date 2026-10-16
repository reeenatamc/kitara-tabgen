#!/bin/bash
# Usage: transcribe.sh <video o audio> <slug> ["Título"]. Draft tab from a recording, checked and with audio, into kitara.
set -eo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$HOME/Documents/GitHub/kitara"
SLUG="$2"
TITLE="${3:-$2}"
mkdir -p "$HERE/out"
ffmpeg -v error -y -i "$1" -vn -ac 1 -ar 22050 "$HERE/out/$SLUG-fuente.wav"
"$HERE/.venv/bin/python" "$HERE/transcribe.py" "$HERE/out/$SLUG-fuente.wav" "$REPO/songs/$SLUG.json" "$REPO/guides/$SLUG.json" "$TITLE" 2>&1 \
  | grep -v -i -e warning -e tensorflow -e coreml -e scikit -e tflite
"$HERE/render.sh" "$SLUG"
