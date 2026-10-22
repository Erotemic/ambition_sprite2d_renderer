#!/usr/bin/env python3
"""Build the rig document of the spectral wolf of Castle Godwin.

    uv run python scripts/svg_art/evil_spectral_wolf_art.py   # the drawing, once
    uv run python scripts/build_evil_spectral_wolf_rig.py

The wolf is the attack hound's body made a spirit
(``scripts/svg_art/evil_spectral_wolf_art.py``): the same parts about the same
joints, and one more part, the ghost fire off its back, on the body bone. So
its bones are the hound's, and so are the clips of the moves it shares with
the hound (``build_evil_attack_hound_rig``). Its own clips:

- ``taunt``: it howls (a wolf does not bark).
- ``fade_out``: it sinks low and its fire flattens, as it goes faint.
- ``faded``: faint, it prowls round you, low, the head turned to you.
- ``fade_in``: it comes solid, gathered to spring.

How faint each frame is, the target says (``targets/characters/evil_spectral_wolf.py``).

This script never draws. It also writes the rig catalog into the SVG.
"""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT, ROOT / "scripts", ROOT / "scripts" / "svg_art"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import build_evil_attack_hound_rig as HOUND  # noqa: E402
from build_house_dog_rigs import COMPANION_RIG, fit_legs  # noqa: E402
from evil_spectral_wolf_art import HEAD_PIVOT, JAW_HINGE, LAYERS, LEG_SCALE, NAME, OUT, SVG_NAME, VIEW  # noqa: E402

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"
RIG_PATH = PKG / "targets" / "characters" / "rigged" / NAME / f"{SVG_NAME}.rig.json"

#: The hound's frame, taller for the fire over its back and its tail.
FRAME = dict(HOUND.FRAME, height=184, ground_y=158)

TAU = math.tau
STANCE = HOUND.STANCE
pose_clip = HOUND.pose_clip
legs_pose = HOUND.legs_pose


def taunt() -> dict:
    """It howls: it sits back, lifts its head to the sky, its jaws open, and
    holds it; then it drops its head."""
    rows = []
    n = 10
    for i in range(n):
        u = i / (n - 1)
        up = min(1.0, u / 0.3) if u < 0.8 else 1.0 - (u - 0.8) / 0.2
        up = up * up * (3.0 - 2.0 * up)
        rows.append({
            "root_y": 4.0 * up, "body": -10.0 * up, "head": 9.0 - 58.0 * up + 1.5 * math.sin(TAU * u * 3),
            "jaw": 6.0 + 22.0 * up, "ear": 5.0 - 14.0 * up,
            "tail_base": -30.0 + 8.0 * up, "tail_tip": -30.0 + 6.0 * up,
            "near_hind_upper": STANCE["near_hind_upper"] + 22.0 * up, "near_hind_lower": -30.0 * up,
            "far_hind_upper": STANCE["far_hind_upper"] + 22.0 * up, "far_hind_lower": -30.0 * up,
        })
    return pose_clip(rows, 90, loop=False)


def _low(i: int, n: int) -> Dict[str, float]:
    """The prowl: low, the legs as the hound walks, the head level and turned to you."""
    s = math.sin(TAU * i / n)
    pose: Dict[str, float] = {
        "root_y": 7.0 + 1.0 * abs(s), "body": 2.0, "head": 14.0 - 1.5 * s, "ear": -8.0, "jaw": 3.0,
        "tail_base": -20.0 + 3.0 * s, "tail_tip": -16.0 + 4.0 * math.sin(TAU * i / n + 0.8),
    }
    for leg, sign in (("near_fore", 1), ("far_fore", -1), ("near_hind", -1), ("far_hind", 1)):
        fore = leg.endswith("fore")
        pose[f"{leg}_upper"] = STANCE[f"{leg}_upper"] + sign * 14.0 * s + (6.0 if fore else -8.0)
        pose[f"{leg}_lower"] = -sign * 8.0 * s + (-14.0 if fore else 16.0)
        pose[f"{leg}_paw"] = -sign * 6.0 * s
    return pose


def faded() -> dict:
    """Faint, it prowls round you: low and slow."""
    return pose_clip([_low(i, 8) for i in range(8)], 120, loop=True)


def _mix(a: Dict[str, float], b: Dict[str, float], f: float) -> Dict[str, float]:
    keys = set(a) | set(b)
    return {k: a.get(k, STANCE.get(k, 0.0)) + (b.get(k, STANCE.get(k, 0.0)) - a.get(k, STANCE.get(k, 0.0))) * f for k in keys}


def fade_out() -> dict:
    """From its stance down into the prowl."""
    stand = {"head": 9.0, "jaw": 6.0, "ear": 5.0}
    rows = [_mix(stand, _low(0, 8), (k / 5) ** 0.8) for k in range(6)]
    return pose_clip(rows, 70, loop=False)


def fade_in() -> dict:
    """Out of the prowl, gathered to spring: the lunge's coil."""
    coil = dict(root_x=-9, root_y=6, body=-7, head=2, jaw=12, ear=8, tail_base=-38, **legs_pose(-14, 30, -24, 40))
    rows = [_mix(_low(0, 8), coil, (k / 5) ** 1.2) for k in range(6)]
    return pose_clip(rows, 60, loop=False)


CLIPS = dict(HOUND.CLIPS, taunt=taunt, faded=faded, fade_out=fade_out, fade_in=fade_in)
GROUNDED = dict(HOUND.GROUNDED, faded=None, fade_out=None, fade_in=None)


def build() -> dict:
    companion = json.loads(COMPANION_RIG.read_text())
    doc = copy.deepcopy(companion)
    doc["name"] = NAME
    doc["svg_source"]["path"] = f"../../../../data/characters/{NAME}/{SVG_NAME}.svg"
    doc["svg_source"]["view"] = VIEW
    doc["frame"] = dict(FRAME)
    unit = float(doc["svg_source"]["scale"])
    known = {part["name"]: part for part in companion["parts"]}
    parts = []
    for group, _label, name, bone, z in LAYERS:
        if name in known:
            part = copy.deepcopy(known[name])
        elif bone in known:
            # A part of the wolf's own (its ghost fire) turns with its bone's part.
            part = {"name": name, "bone": bone, "kind": "sprite", "pivot": list(known[bone]["pivot"]), "rest_angle": 0}
        else:
            pivot = list(JAW_HINGE) if bone == "jaw" else list(HEAD_PIVOT)
            part = {"name": name, "bone": bone, "kind": "sprite", "pivot": pivot, "rest_angle": 0}
        part.update(z=z, bone=bone, include=[group])
        parts.append(part)
    doc["parts"] = parts
    doc["bones"].append({
        "name": "jaw", "parent": "head",
        "offset": [round((JAW_HINGE[0] - HEAD_PIVOT[0]) * unit, 4), round((JAW_HINGE[1] - HEAD_PIVOT[1]) * unit, 4)],
        "length": 0, "rest_angle": 0,
    })
    fit_legs(doc, LEG_SCALE)
    doc["clips"] = {name: make() for name, make in CLIPS.items()}
    _put_paws_on_the_ground(doc)
    return doc


def _put_paws_on_the_ground(doc: dict) -> None:
    """The hound's rule (``build_evil_attack_hound_rig.put_paws_on_the_ground``)
    for the wolf's rows: each grounded frame's lowest point on the ground."""
    rig = RigDocument(copy.deepcopy(doc), source_path=RIG_PATH)
    ground = int(doc["frame"]["ground_y"])
    for row, which in GROUNDED.items():
        clip = doc["clips"][row]
        keys = clip["channels"]["root_y"]["keys"]
        for frame in range(clip["frames"]) if which is None else which:
            keys[frame][1] = round(keys[frame][1] + ground - HOUND._lowest(rig, row, frame, clip["frames"]), 3)
        clip["channels"]["root_y"]["keys"] = keys


def main() -> None:
    doc = build()
    RIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = RIG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf8")
    tmp.replace(RIG_PATH)
    print(f"wrote {RIG_PATH.relative_to(ROOT)}")
    HOUND.write_catalog(RIG_PATH, OUT)
    print(f"catalog {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
