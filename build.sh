#!/bin/sh
# Usage: build.sh <slug> [audio.m4a]. Generates the song and guide from <slug>.py, checks them and renders the audio.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$HOME/Documents/GitHub/kitara"
python3 "$HERE/$1.py" "$REPO/songs/$1.json" "$REPO/guides/$1.json"
"$HERE/render.sh" "$@"
