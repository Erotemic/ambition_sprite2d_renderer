#!/usr/bin/env python3
"""Build the Imperfect Cellular Automaton's two rig documents from her SVGs.

The SVGs in ``data/characters/imperfect_cellular_automaton/`` own the art and
say where every joint is (the hidden ``Rig Joints`` layer). This script
derives the skeleton from the joints and binds every part layer to its bone.
It never draws.

    uv run python scripts/build_imperfect_cellular_automaton_rig.py

There are two documents because she is not the same on her two sides: one
for the view with her green half toward the camera, and one for the other
side. They have the same skeleton; only the art differs.

THE BONES HAVE THE NAMES OF THE PERFECT CELLULAR AUTOMATON'S. She plays the
perfect one's move table, so she plays the perfect one's clips: the target
(``targets/characters/imperfect_cellular_automaton.py``) borrows them when it
loads a document, and these documents hold no clip. A clip's angles are added
to her own rest pose, so every move is done hunched, as she stands. Her tail
and her wings are bones the perfect one does not have; the target moves them.

A foot's rest angle is DECLARED, not measured: a clip gives a foot's pitch as
a world angle about the perfect one's rest pitch, so her foot bone says its
rest is that same angle and a clip that holds the rest pitch draws her foot as
it is drawn.
"""

from __future__ import annotations

import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PKG = ROOT / "ambition_sprite2d_renderer"
DATA = PKG / "data" / "characters" / "imperfect_cellular_automaton"
RIGGED = PKG / "targets" / "characters" / "rigged" / "imperfect_cellular_automaton"
PERFECT = PKG / "targets" / "characters" / "rigged" / "perfect_cellular_automaton.rig.json"

Point = Tuple[float, float]

#: Frame units for each SVG unit: her legs are as long as the perfect one's.
SCALE = 0.31
#: The root of the rig in the drawing (SVG units): the ground, and the line
#: the clips put her feet about. It is ahead of her hips, because she leans.
ROOT_X, GROUND_Y = 306.0, 590.0
FRAME = {"width": 160, "height": 192, "ground_y": 176.0, "center_x": 80.0, "supersample": 2, "render_scale": 2}

TAIL_BONES = 7
VIEWS = {
    "imperfect_cellular_automaton": ("imperfect_cellular_automaton.svg", "ICA - Clean Side"),
    "imperfect_cellular_automaton_fault_side": ("imperfect_cellular_automaton_fault_side.svg", "ICA - Fault Side"),
}

#: ``(bone, parent, the joint it turns about, the joint at its end)``, parents first.
BONES: List[Tuple[str, Optional[str], str, Optional[str]]] = [
    ("pelvis", None, "pelvis", None),
    ("torso", "pelvis", "torso", None),
    ("head", "torso", "head", None),
]
for _side in ("far", "near"):
    BONES += [
        (f"{_side}_arm_u", "torso", f"{_side}_shoulder", f"{_side}_elbow"),
        (f"{_side}_arm_l", f"{_side}_arm_u", f"{_side}_elbow", f"{_side}_wrist"),
        (f"{_side}_arm_hand", f"{_side}_arm_l", f"{_side}_wrist", f"{_side}_hand_tip"),
        (f"{_side}_leg_u", "pelvis", f"{_side}_hip", f"{_side}_knee"),
        (f"{_side}_leg_l", f"{_side}_leg_u", f"{_side}_knee", f"{_side}_ankle"),
        (f"{_side}_leg_foot", f"{_side}_leg_l", f"{_side}_ankle", f"{_side}_toe"),
    ]
BONES += [(f"tail_{n}", "pelvis" if n == 1 else f"tail_{n - 1}", f"tail_{n - 1}", f"tail_{n}") for n in range(1, TAIL_BONES + 1)]
BONES += [(f"wing_{_side}", "torso", "wing_root", f"wing_{_side}_tip") for _side in ("far", "near")]


def read_svg(path: Path):
    """``(joints, parts)`` of one SVG: where each joint is, and each part
    layer as ``(name, bone, z, layer id, opacity channel)``."""
    root = ET.parse(path).getroot()
    joints: Dict[str, Point] = {}
    parts = []
    for elem in root.iter():
        if elem.get("data-joint"):
            joints[elem.get("data-joint")] = (float(elem.get("cx")), float(elem.get("cy")))
        if elem.get("data-rig-part"):
            parts.append((elem.get("data-rig-part"), elem.get("data-rig-bone"), float(elem.get("data-rig-z")),
                          elem.get("id"), elem.get("data-rig-opacity")))
    return joints, parts


def perfect_rest_pitch() -> Dict[str, float]:
    legs = json.loads(PERFECT.read_text())["ik_legs"]
    return {leg["foot"]: float(leg["rest_pitch"]) for leg in legs}


def build(name: str, svg_file: str, view: str) -> dict:
    joints, svg_parts = read_svg(DATA / svg_file)
    pitch = perfect_rest_pitch()

    def frame(p: Point) -> Point:
        return ((p[0] - ROOT_X) * SCALE, (p[1] - GROUND_Y) * SCALE)

    world_angle: Dict[str, float] = {}
    origin: Dict[str, Point] = {}
    bones = []
    for bone, parent, at, end in BONES:
        a = joints[at]
        origin[bone] = a
        length = 0.0
        if end is None:
            angle = 0.0
        else:
            b = joints[end]
            length = math.hypot(b[0] - a[0], b[1] - a[1]) * SCALE
            angle = pitch.get(bone, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
        world_angle[bone] = angle
        if parent is None:
            offset = frame(a)
            rest = angle
        else:
            pa = origin[parent]
            dx, dy = (a[0] - pa[0]) * SCALE, (a[1] - pa[1]) * SCALE
            r = math.radians(-world_angle[parent])
            offset = (dx * math.cos(r) - dy * math.sin(r), dx * math.sin(r) + dy * math.cos(r))
            rest = angle - world_angle[parent]
        bones.append({"name": bone, "parent": parent, "offset": [round(offset[0], 3), round(offset[1], 3)],
                      "length": round(length, 3), "rest_angle": round(rest, 3)})

    parts = []
    for part, bone, z, layer_id, opacity in sorted(svg_parts, key=lambda p: p[2]):
        entry = {"name": part, "bone": bone, "z": z, "kind": "sprite", "include": [layer_id],
                 "pivot": [round(origin[bone][0], 3), round(origin[bone][1], 3)], "rest_angle": round(world_angle[bone], 3)}
        if opacity:
            entry["opacity_channel"] = opacity
        parts.append(entry)

    ankle_h = (GROUND_Y - joints["near_ankle"][1]) * SCALE
    legs = []
    for side in ("near", "far"):
        ankle = frame(joints[f"{side}_ankle"])
        legs.append({"upper": f"{side}_leg_u", "lower": f"{side}_leg_l", "foot": f"{side}_leg_foot",
                     "channel_prefix": f"{side}_foot", "rest_x": round(ankle[0], 3),
                     "rest_lift": round(-ankle[1] - ankle_h, 3), "rest_pitch": pitch[f"{side}_leg_foot"], "bend": 1.0})

    return {
        "name": name,
        "frame": {**FRAME, "ankle_h": round(ankle_h, 3)},
        "svg_source": {"path": f"../../../../data/characters/imperfect_cellular_automaton/{svg_file}", "view": view,
                       "ref_dpi": 25.4, "scale": SCALE},
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": legs,
        # The clips are the perfect one's, borrowed when the target loads this document.
        "clips": {},
        "sprite_tuning": {"collision_scale": 1.12},
    }


def main() -> None:
    RIGGED.mkdir(parents=True, exist_ok=True)
    for name, (svg_file, view) in VIEWS.items():
        path = RIGGED / f"{name}.rig.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(build(name, svg_file, view), indent=1) + "\n")
        tmp.replace(path)
        print(path)
    # The SVGs carry a catalog of the rig; put it in again, for a drawing that was made new.
    from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_repo_metadata

    for path in install_repo_metadata(ROOT):
        print("catalog:", path)


if __name__ == "__main__":
    sys.exit(main())
