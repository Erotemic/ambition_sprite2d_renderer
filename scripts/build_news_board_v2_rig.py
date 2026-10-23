#!/usr/bin/env python3
"""Build the rig document of the News Board v2 (``news_board_v2``).

    uv run python scripts/svg_art/news_board_art.py        # the drawing, once
    uv run python scripts/build_news_board_v2_rig.py

The drawing (look A, the Drain Market board, from the front) says where each
part turns (``cast_joints`` and ``MARKET_LAYERS`` in the art script). This
script makes the skeleton from those joints, binds each part layer to its
bone, and authors the rows. It never draws. A channel is the turn of a bone in
degrees (positive clockwise on the screen), or the opacity of a part.

The rows:

- ``idle``: the board stands. The loose slip lifts and settles in a draught;
  the horn is still.
- ``talk``: the horn speaks. It kicks back on each word, its two rings of
  sound show in turn, and the slip flutters in the blast.

The board is a prop: its body never moves.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_catalog  # noqa: E402

_spec = importlib.util.spec_from_file_location("news_board_art", ROOT / "scripts" / "svg_art" / "news_board_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
OUT = PKG / "targets" / "characters" / "rigged" / art.CAST_NAME / f"{art.CAST_NAME}.rig.json"

#: Frame pixels for each SVG unit. The board is about 360 units high, so 180
#: frame pixels: more than twice what the game draws, for the high tiers.
SCALE = 0.5
FRAME = {"width": 144, "height": 200, "center_x": 72, "ground_y": 192, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

#: Each bone: its parent and its joint (a key of ``cast_joints``). Parents first.
BONES = {"body": ("", "body"), "horn": ("body", "horn"), "slip": ("body", "slip")}


def expr(text: str) -> dict:
    return {"expr": text}


#: The word of the talk row: which of its 8 frames, 0..7.
WORD = "floor(t*8 + 0.01)"

CLIPS = {
    "idle": {
        "loop": True, "frames": 8, "duration_ms": 170,
        "channels": {
            "slip": expr("2.5*sin(tau*t) + 1.0*sin(2*tau*t + 0.7)"),
            "horn": expr("0"),
            "voice_near": expr("0"),
            "voice_far": expr("0"),
        },
    },
    "talk": {
        "loop": True, "frames": 8, "duration_ms": 95,
        "channels": {
            # a kick back (counter-clockwise, toward the bell) on each word
            "horn": expr(f"-3.0 if {WORD} % 2 == 0 else 1.0"),
            "voice_near": expr(f"1 if {WORD} % 4 in (0, 1) else 0"),
            "voice_far": expr(f"1 if {WORD} % 4 in (1, 2) else 0"),
            "slip": expr("6.0*sin(2*tau*t) + 2.0"),
        },
    },
}


def build() -> dict:
    joints = art.cast_joints()
    gx, gy = joints["body"]
    bones = []
    for name, (parent, at) in BONES.items():
        x, y = joints[at]
        if parent:
            px, py = joints[BONES[parent][1]]
            offset = [round((x - px) * SCALE, 4), round((y - py) * SCALE, 4)]
        else:
            offset = [round((x - gx) * SCALE, 4), round((y - gy) * SCALE, 4)]
        bones.append({"name": name, "parent": parent or None, "offset": offset, "length": 0, "rest_angle": 0})
    parts = []
    for group, _label, z in art.MARKET_LAYERS:
        bone, channel = art.CAST_BONES.get(group, ("body", ""))
        x, y = joints[BONES[bone][1]]
        entry = {"name": group.replace("-", "_"), "bone": bone, "z": z, "kind": "sprite", "include": [group],
                 "pivot": [round(x, 3), round(y, 3)], "rest_angle": 0}
        if channel:
            entry["opacity_channel"] = channel
            entry["opacity_default"] = 0
        parts.append(entry)
    return {
        "name": art.CAST_NAME,
        "frame": FRAME,
        "svg_source": {"path": f"../../../../data/characters/{art.CAST_NAME}/{art.CAST_NAME}.svg", "view": art.CAST_VIEW,
                       "ref_dpi": 25.4, "scale": SCALE},
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": [],
        "ik_chains": [],
        "clips": CLIPS,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")
    # The rig block of this board's SVG only: the drawing writes the SVG
    # without one, and other SVGs are not this script's to touch.
    if install_catalog(art.OUT, [OUT]):
        print(f"catalog {art.OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
