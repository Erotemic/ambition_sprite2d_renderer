#!/usr/bin/env python3
"""Build the rig document of the attack hound of Castle Godwin.

    uv run python scripts/svg_art/evil_attack_hound_art.py   # the drawing, once
    uv run python scripts/build_evil_attack_hound_rig.py

The hound is drawn with the companion dog's parts about the companion dog's
joints, as the house dogs are (``scripts/svg_art/evil_attack_hound_art.py``).
So its bones are the companion dog's, with the legs ``LEG_SCALE`` as long,
and ONE more bone: ``jaw``, the lower jaw, which turns about its hinge on
the head. Its clips are its own (``CLIPS``): a guard dog that growls, stalks,
gallops, bites, lunges and barks. It never borrows the companion dog's.

Each clip gives each frame its own pose (``pose_clip``): the keys are at the
times of the frames, so no two frames of a row are the same.

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

from build_house_dog_rigs import COMPANION_RIG, fit_legs  # noqa: E402
from evil_attack_hound_art import HEAD_PIVOT, JAW_HINGE, LAYERS, LEG_SCALE, NAME, OUT, SVG_NAME, VIEW  # noqa: E402

import numpy as np  # noqa: E402

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument  # noqa: E402
from ambition_sprite2d_renderer.devtools import svg_rig_tool  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"
RIG_PATH = PKG / "targets" / "characters" / "rigged" / NAME / f"{SVG_NAME}.rig.json"

#: Wide enough for the lunge and the gallop, high enough for the jump.
FRAME = {"width": 232, "height": 168, "center_x": 100, "ground_y": 142, "ankle_h": 0, "supersample": 4, "render_scale": 1, "trim": False}

TAU = math.tau
LEGS = ("near_fore", "far_fore", "near_hind", "far_hind")

#: The stance of the hound when a frame does not say: the head low, the
#: ears forward, the tail out stiff behind, the lip up off the teeth.
STANCE: Dict[str, float] = {
    "head": 9.0, "ear": 5.0, "jaw": 6.0, "body": 0.0, "root_x": 0.0, "root_y": 0.0,
    "tail_base": -30.0, "tail_tip": -30.0,
    "near_fore_upper": -3.0, "far_fore_upper": -3.0, "near_hind_upper": 5.0, "far_hind_upper": 5.0,
}


def pose_clip(frames: List[Dict[str, float]], ms: int, loop: bool) -> dict:
    """A clip with one key for each frame, at the time of that frame. A
    channel that a frame does not state is at ``STANCE`` (else 0)."""
    n = len(frames)
    names = sorted(set(STANCE) | {name for frame in frames for name in frame})
    channels = {}
    for name in names:
        keys = []
        for i, frame in enumerate(frames):
            t = i / n if loop else i / max(1, n - 1)
            value = frame.get(name, STANCE.get(name, 0.0))
            keys.append([round(t, 6), round(float(value), 3), "linear"])
        channels[name] = {"keys": keys}
    return {"loop": loop, "frames": n, "duration_ms": ms, "channels": channels}


def idle() -> dict:
    """Tense, and a growl: the lip quivers, the body is still."""
    frames = []
    for i in range(8):
        ph = TAU * i / 8
        frames.append({
            "root_y": 0.6 * math.sin(ph),
            "head": 9 + 1.0 * math.sin(ph) + 0.7 * math.sin(3 * ph),
            "jaw": 6 + 3.0 * (0.5 + 0.5 * math.sin(3 * ph + 0.5)),
            "ear": 5 + 1.5 * math.sin(ph + 1.0),
            "tail_base": -30 + 2 * math.sin(ph),
            "tail_tip": -30 + 3 * math.sin(ph + 0.7),
        })
    return pose_clip(frames, 130, loop=True)


def walk() -> dict:
    """A stalk: the head low, the legs as the companion dog walks."""
    frames = []
    for i in range(8):
        s = math.sin(TAU * i / 8)
        frame = {
            "root_y": 1.3 * abs(s) - 0.6,
            "head": 12 - 1.5 * s,
            "ear": 6 + 1.5 * s,
            "jaw": 4 + 1.5 * abs(s),
            "tail_base": -32 + 3 * s,
            "tail_tip": -30 + 4 * math.sin(TAU * i / 8 + 0.8),
        }
        for leg, sign in (("near_fore", 1), ("far_fore", -1), ("near_hind", -1), ("far_hind", 1)):
            fore = leg.endswith("fore")
            frame[f"{leg}_upper"] = STANCE[f"{leg}_upper"] + sign * (18 if fore else 17) * s
            frame[f"{leg}_lower"] = -sign * (10 if fore else 9) * s
            frame[f"{leg}_paw"] = -sign * 7 * s
        frames.append(frame)
    return pose_clip(frames, 110, loop=True)


def run() -> dict:
    """A full gallop. At the start of the cycle the hound is stretched out
    (the forelegs reach, the hind legs push back); at its middle it is
    gathered (the four legs under it). The far legs come a little after
    the near ones."""
    frames = []
    for i in range(8):
        frame: Dict[str, float] = {}
        for leg, lag in (("near_fore", 0.0), ("far_fore", 0.09), ("near_hind", 0.0), ("far_hind", 0.09)):
            ph = TAU * (i / 8 - lag)
            c, s = math.cos(ph), math.sin(ph)
            if leg.endswith("fore"):
                frame[f"{leg}_upper"] = -38 * c + 4
                # The forearm folds back as the leg comes forward again.
                frame[f"{leg}_lower"] = 55 * max(0.0, -s) + 4
                frame[f"{leg}_paw"] = 25 * max(0.0, -s)
            else:
                frame[f"{leg}_upper"] = 42 * c
                # The hock folds forward as the leg comes under the body.
                frame[f"{leg}_lower"] = -40 * max(0.0, s) + 8 * c
                frame[f"{leg}_paw"] = -20 * max(0.0, s)
        ph = TAU * i / 8
        frame.update({
            "root_y": -4 * abs(math.cos(ph)) + 1,
            "body": 6 * math.sin(ph),
            "head": 5 - 4 * math.sin(ph + 0.6),
            "ear": -14 + 3 * math.sin(ph),
            "jaw": 9 + 4 * math.sin(ph + 1.2),
            "tail_base": -42 + 6 * math.sin(ph),
            "tail_tip": -26 + 6 * math.sin(ph + 0.8),
        })
        frames.append(frame)
    return pose_clip(frames, 70, loop=True)


def legs_pose(fore_upper: float, fore_lower: float, hind_upper: float, hind_lower: float, spread: float = 4.0) -> Dict[str, float]:
    """The two forelegs and the two hind legs, the far one ``spread`` behind the near one."""
    return {
        "near_fore_upper": fore_upper, "far_fore_upper": fore_upper + spread,
        "near_fore_lower": fore_lower, "far_fore_lower": fore_lower,
        "near_hind_upper": hind_upper, "far_hind_upper": hind_upper + spread,
        "near_hind_lower": hind_lower, "far_hind_lower": hind_lower,
    }


def jump() -> dict:
    """Crouch, spring, tuck. The game moves the body; the row only poses it."""
    rows = [
        dict(root_y=4, body=-3, head=6, ear=4, jaw=6, **legs_pose(-12, 26, -16, 30)),
        dict(root_y=0, body=-12, head=-4, ear=-6, jaw=12, tail_base=-24, **legs_pose(-34, 60, 36, 4)),
        dict(root_y=0, body=-8, head=-2, ear=-8, jaw=14, tail_base=-28, **legs_pose(-48, 80, 30, 14)),
        dict(root_y=0, body=-2, head=4, ear=-8, jaw=10, tail_base=-34, **legs_pose(-42, 86, -24, -46)),
        dict(root_y=0, body=2, head=6, ear=-4, jaw=8, tail_base=-36, **legs_pose(-30, 50, -14, -30)),
        dict(root_y=0, body=4, head=8, ear=0, jaw=6, tail_base=-36, **legs_pose(-22, 18, -4, -12)),
    ]
    return pose_clip(rows, 85, loop=False)


def fall() -> dict:
    """Down through the air: the forelegs reach to land, the tail up."""
    rows = []
    for i in range(4):
        ph = TAU * i / 4
        rows.append(dict(
            body=5 + 1.5 * math.sin(ph), head=6 + 2 * math.sin(ph + 1), ear=-3 + 3 * math.sin(ph + 2), jaw=8 + 3 * math.sin(ph),
            tail_base=-18 + 4 * math.sin(ph), tail_tip=-24 + 6 * math.sin(ph + 1),
            **legs_pose(-26 + 4 * math.sin(ph), 12 + 6 * math.sin(ph + 1), 14 + 4 * math.sin(ph + 2), -16 + 5 * math.sin(ph + 3)),
        ))
    return pose_clip(rows, 100, loop=True)


def slash() -> dict:
    """The snapping bite: rear back, the jaws wide, snap shut, a shake."""
    rows = [
        dict(head=7, jaw=8),
        dict(root_x=-3, body=-3, head=-8, jaw=24, ear=-4),
        dict(root_x=5, body=4, head=10, jaw=42, ear=-8, **{"bone.head.x": 3.0}, **legs_pose(-10, 4, 8, 0)),
        dict(root_x=8, body=5, head=15, jaw=-1, ear=-6, **{"bone.head.x": 5.0}, **legs_pose(-12, 4, 10, 0)),
        dict(root_x=8, body=4, head=3, jaw=0, ear=-2, **{"bone.head.x": 4.0}, **legs_pose(-10, 4, 9, 0)),
        dict(root_x=4, body=2, head=11, jaw=6, ear=2, **{"bone.head.x": 2.0}),
        dict(root_x=1, head=8, jaw=5, ear=4),
    ]
    return pose_clip(rows, 60, loop=False)


def attack_side() -> dict:
    """The long leaping lunge: coil, launch with the jaws wide, bite in the
    air, land, and pull back as a guard dog does at the end of its chain."""
    rows = [
        dict(root_x=-5, root_y=3, body=-4, head=4, jaw=8, ear=8, tail_base=-36, **legs_pose(-8, 16, -12, 22)),
        dict(root_x=-9, root_y=6, body=-7, head=2, jaw=12, ear=8, tail_base=-38, **legs_pose(-14, 30, -24, 40)),
        dict(root_x=0, root_y=-6, body=-14, head=-4, jaw=30, ear=-6, tail_base=-30, **legs_pose(-52, 48, 42, 8)),
        dict(root_x=12, root_y=-15, body=-4, head=2, jaw=44, ear=-12, tail_base=-40, **legs_pose(-72, 14, 58, 6)),
        dict(root_x=20, root_y=-11, body=8, head=14, jaw=0, ear=-10, tail_base=-44, **{"bone.head.x": 4.0}, **legs_pose(-58, 4, 46, 18)),
        dict(root_x=22, root_y=-2, body=9, head=12, jaw=-1, ear=-6, tail_base=-36, **{"bone.head.x": 3.0}, **legs_pose(-22, 2, 26, 28)),
        dict(root_x=21, root_y=1, body=4, head=10, jaw=3, ear=-2, **legs_pose(-12, 6, 8, -6)),
        dict(root_x=16, root_y=0, body=-2, head=6, jaw=14, ear=2, **legs_pose(6, -10, -4, 6)),
        dict(root_x=9, root_y=0, body=-1, head=8, jaw=8, ear=4, **legs_pose(10, -12, -8, 8)),
        dict(root_x=3, head=9, jaw=5, ear=5),
    ]
    return pose_clip(rows, 65, loop=False)


def hit() -> dict:
    """Struck: the head thrown up, a yelp, the ears back."""
    rows = [
        dict(root_x=-4, body=-8, head=-20, jaw=24, ear=-18, tail_base=-12, tail_tip=-10, **legs_pose(8, -6, -2, 6)),
        dict(root_x=-6, body=-5, head=-10, jaw=16, ear=-14, tail_base=-16, **legs_pose(6, -4, 0, 4)),
        dict(root_x=-4, body=-2, head=1, jaw=9, ear=-6, tail_base=-24),
        dict(root_x=-1, head=7, jaw=5, ear=2),
    ]
    return pose_clip(rows, 80, loop=False)


def death() -> dict:
    """A recoil, then the hound goes down, the eye an X, the jaw slack."""
    rows = [dict(root_x=-3, body=-8, head=-18, jaw=26, ear=-16, tail_base=-14, **legs_pose(6, -4, 0, 4))]
    drop = 42 * LEG_SCALE
    for k in range(8):
        t = k / 7
        rows.append(dict(
            root_y=drop * t, body=18 * t, head=-8 + 58 * t, ear=-16 - 4 * t, jaw=18 - 6 * t,
            tail_base=-24 - 14 * t, tail_tip=-30 - 10 * t,
            near_fore_upper=65 * t, near_fore_lower=-125 * t, far_fore_upper=4 + 61 * t, far_fore_lower=-125 * t,
            near_hind_upper=80 * t, near_hind_lower=-130 * t, far_hind_upper=4 + 76 * t, far_hind_lower=-130 * t,
            eye_open=1.0 if t < 0.5 else 0.0, eye_x=0.0 if t < 0.5 else 1.0,
        ))
    return pose_clip(rows, 110, loop=False)


def taunt() -> dict:
    """Barking: three barks, each a snap of the head and a stamp of a forefoot."""
    jaw = [4, 34, 6, 38, 5, 30, 9, 5]
    head = [8, -6, 10, -9, 9, -4, 11, 8]
    body = [0, -3, 1, -4, 1, -2, 1, 0]
    root_y = [0, -1.5, 0.5, -2, 0.5, -1, 0.5, 0]
    stamp = [0, -9, 2, -10, 3, -6, 1, 0]
    ear = [5, 1, 6, 0, 6, 2, 6, 5]
    rows = []
    for i in range(8):
        rows.append({
            "jaw": jaw[i], "head": head[i], "body": body[i], "root_y": root_y[i], "ear": ear[i],
            "near_fore_upper": STANCE["near_fore_upper"] + stamp[i], "near_fore_lower": -0.8 * stamp[i],
            "tail_base": -30 + (3 if i % 2 else -2), "tail_tip": -30 + (4 if i % 2 else -3),
        })
    return pose_clip(rows, 85, loop=False)


def notice() -> dict:
    """It has seen you: the head comes up and round, the ears go flat back,
    the hackles stand over a stiffened neck, the tail goes up stiff and the
    lip curls. The game loops it, so each frame is the whole pose with a
    shiver of the lip."""
    rows = []
    for shiver in (0.0, 1.0, -1.0):
        rows.append(dict(
            root_x=-2, body=-6, head=-10 + 0.5 * shiver, ear=-48, jaw=12 + 2.5 * shiver,
            tail_base=-14, tail_tip=-12 + 2 * shiver, **legs_pose(-8, 4, 10, -4),
        ))
    return pose_clip(rows, 110, loop=False)


def windup() -> dict:
    """The lunge held back: down in a low crouch on bent legs, the head low
    and level, the teeth bared wide, the ears flat. A shiver runs through it."""
    rows = []
    for shiver in (0.0, 1.0, -1.0):
        rows.append(dict(
            root_x=-8 + 0.6 * shiver, body=5, head=14 + 0.6 * shiver, ear=-62, jaw=22 + 2 * shiver,
            tail_base=-40, tail_tip=-34 + 2 * shiver, **legs_pose(-18, 38, -26, 44),
        ))
    return pose_clip(rows, 90, loop=False)


#: The frames in which a paw is on the ground, by row (None: each frame).
#: In the air (the top of a jump, a fall, the flight of the lunge) the
#: game moves the body and the row only poses it.
GROUNDED = {
    "idle": None, "walk": None, "run": None, "slash": None, "hit": None, "death": None, "taunt": None,
    "jump": (0, 1), "attack_side": (0, 1, 2, 5, 6, 7, 8, 9), "fall": (), "notice": None, "windup": None,
}


def _lowest(doc: RigDocument, row: str, frame: int, frames: int) -> int:
    alpha = np.asarray(doc.render_frame(row, frame, frames).convert("RGBA"))[..., 3]
    return int(np.nonzero(alpha.max(axis=1) > 40)[0].max())


def put_paws_on_the_ground(doc: dict) -> None:
    """Move each grounded frame up or down so its lowest point is on the
    ground line of the frame. The legs of a pose do not reach the ground by
    themselves (there is no IK on a leg): without this a paw is in the floor
    or over it."""
    rig = RigDocument(copy.deepcopy(doc), source_path=RIG_PATH)
    ground = int(doc["frame"]["ground_y"])
    for row, which in GROUNDED.items():
        clip = doc["clips"][row]
        keys = clip["channels"]["root_y"]["keys"]
        for frame in range(clip["frames"]) if which is None else which:
            keys[frame][1] = round(keys[frame][1] + ground - _lowest(rig, row, frame, clip["frames"]), 3)
        clip["channels"]["root_y"]["keys"] = keys


CLIPS = {
    "idle": idle, "walk": walk, "run": run, "jump": jump, "fall": fall,
    "slash": slash, "attack_side": attack_side, "hit": hit, "death": death, "taunt": taunt,
    "notice": notice, "windup": windup,
}


def build() -> dict:
    companion = json.loads(COMPANION_RIG.read_text())
    doc = copy.deepcopy(companion)
    doc["name"] = NAME
    doc["svg_source"]["path"] = f"../../../../data/characters/{NAME}/{SVG_NAME}.svg"
    doc["svg_source"]["view"] = VIEW
    doc["frame"] = dict(FRAME)
    unit = float(doc["svg_source"]["scale"])
    # The parts of the drawing. A part the companion dog has keeps its joint.
    known = {part["name"]: part for part in companion["parts"]}
    parts = []
    for group, _label, name, bone, z in LAYERS:
        if name in known:
            part = copy.deepcopy(known[name])
        else:
            pivot = list(JAW_HINGE) if bone == "jaw" else list(HEAD_PIVOT)
            part = {"name": name, "bone": bone, "kind": "sprite", "include": [group], "pivot": pivot, "rest_angle": 0}
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
    put_paws_on_the_ground(doc)
    return doc


def write_catalog(rig_path: Path, svg_path: Path) -> None:
    """The rig catalog in the SVG, from this rig document only."""
    catalog, quality = svg_rig_tool.catalog_from_rigdoc(rig_path, svg_path, used_view_ids=set())
    svg_rig_tool.install_block(svg_path, svg_rig_tool._serialize_character_block([catalog], {catalog.view_id: quality}))


def main() -> None:
    doc = build()
    RIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = RIG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf8")
    tmp.replace(RIG_PATH)
    print(f"wrote {RIG_PATH.relative_to(ROOT)}")
    write_catalog(RIG_PATH, OUT)
    print(f"catalog {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
