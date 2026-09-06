#!/bin/bash
__doc__='
Small helper function
'

set -euo pipefail

FALLBACK_DIR="$HOME/code/ambition/tools/ambition_sprite2d_renderer"

if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
    SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$FALLBACK_DIR"
fi

uv run \
    --directory "$SCRIPT_DIR" \
    --extra gui \
    python -m ambition_sprite2d_renderer.gui \
    ambition_sprite2d_renderer/targets/characters/rigged/player_robot/player_robot.rig.json
