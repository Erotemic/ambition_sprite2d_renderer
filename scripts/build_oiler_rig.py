#!/usr/bin/env python3
"""Bind Oiler's multiview SVG to five view rigs and author their clips.

    uv run python scripts/svg_art/oiler_art.py --multiview \
        ambition_sprite2d_renderer/data/characters/oiler/oiler-multiview.svg
    uv run python scripts/build_oiler_rig.py build --fresh
    uv run python scripts/build_oiler_rig.py validate

The SVG is drawn by ``scripts/svg_art/oiler_art.py`` (the 2026-10-20 redesign:
Euler after the 1753 pastel, a silk banyan over his workshop clothes). This
command checks its art contract, then refreshes geometry and seeds the clips.
A plain ``build`` keeps clips already in the ``.rig.json`` files; ``--fresh``
reseeds them from this script (their hand targets are absolute, so a redrawn
body needs ``--fresh``).

Oiler is ASYMMETRIC: his right eye fails. The two left views
(``three_quarter_left``, ``side_left``) are his left side, drawn facing right
like their right-facing twins and bound to the same skeleton, so they take the
same clips; the sprite target mirrors their frames into the ``~mirrored`` rows
the game draws instead of flipping.

Each view's face is one of ``FACES``, an opacity channel apiece
(``face_<name>_vis``; ``knowing`` by default), under the ``blink_vis`` and
``talk_vis`` overlays.
"""

from __future__ import annotations

import argparse
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    HumanoidViewSpec,
    build_humanoid_view_document,
    merge_generated_geometry,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "ambition_sprite2d_renderer/data/characters/oiler/oiler-multiview.svg"
RIG_DIR = ROOT / "ambition_sprite2d_renderer/targets/characters/rigged/oiler"
SCRATCH = ROOT / "agent-scratch/oiler_rig"
DESIGN_ID = "euler-banyan-v2"
#: The expressions every view draws, in the art script's order.
FACES = ("knowing", "pleased", "delighted", "surprised", "thinking", "stern", "worried", "hurt")
#: The face each clip wears; any clip not named here keeps ``knowing``.
FACE_OF = {
    "interact": "thinking",
    "hit": "hurt",
    "death": "hurt",
    "taunt": "delighted",
    **{name: "stern" for name in (
        "attack_side", "attack_up", "attack_down", "smash_forward", "special", "jab", "dash_attack", "smash_up", "smash_down",
        "air_neutral", "air_forward", "air_back", "air_up", "air_down", "convergence", "special_side", "special_up", "special_down")},
}
#: view key -> (layer label, whether it is a left view stored facing right)
VIEW_LAYERS = {
    "three_quarter": ("Oiler - Three Quarter", False),
    "front": ("Oiler - Front", False),
    "side": ("Oiler - Side Right", False),
    "three_quarter_left": ("Oiler - Three Quarter Left", True),
    "side_left": ("Oiler - Side Left", True),
}
VIEWS = {
    "three_quarter": HumanoidViewSpec(
        view="Oiler - Three Quarter",
        name="oiler_three_quarter",
        target_height=105.0,
        collision_scale=1.72,
    ),
    "front": HumanoidViewSpec(
        view="Oiler - Front",
        name="oiler_front",
        target_height=105.0,
        collision_scale=1.72,
    ),
    "side": HumanoidViewSpec(
        view="Oiler - Side Right",
        name="oiler_side",
        target_height=105.0,
        collision_scale=1.72,
    ),
    "three_quarter_left": HumanoidViewSpec(
        view="Oiler - Three Quarter Left",
        name="oiler_three_quarter_left",
        target_height=105.0,
        collision_scale=1.72,
    ),
    "side_left": HumanoidViewSpec(
        view="Oiler - Side Left",
        name="oiler_side_left",
        target_height=105.0,
        collision_scale=1.72,
    ),
}


def _validate_svg_source() -> None:
    """Reject a source that drifted from Oiler's art contract: flat paint and
    no props, the redesign's marker, all five views, every expression."""

    text = SVG.read_text(encoding="utf8").lower()
    forbidden = (
        "<filter",
        "<lineargradient",
        "<radialgradient",
        "drop-shadow",
        "dropshadow",
        'data-rig-part="machine"',
        'data-rig-part="wrench"',
        "oil-flask",
        "satchel",
    )
    present = [token for token in forbidden if token in text]
    if present:
        raise ValueError(f"Oiler SVG contains forbidden art features: {present}")

    root = ET.parse(SVG).getroot()
    if root.get("data-character-design") != DESIGN_ID:
        raise ValueError(f"Oiler SVG must declare data-character-design={DESIGN_ID!r}")
    label = "{http://www.inkscape.org/namespaces/inkscape}label"
    views = {elem.get(label): elem for elem in root if elem.get(label)}
    for key, (name, stored_facing_right) in VIEW_LAYERS.items():
        layer = views.get(name)
        if layer is None:
            raise ValueError(f"Oiler SVG lacks the {name!r} view")
        if (layer.get("data-view-mirror") == "x") != stored_facing_right:
            raise ValueError(f"{name!r}: only the left views carry data-view-mirror=\"x\"")
        channels = {}
        for elem in layer.iter():
            ch = elem.get("data-rig-opacity")
            if ch:
                channels[ch] = elem.get("data-rig-opacity-default")
        wanted = {f"face_{face}_vis" for face in FACES} | {"blink_vis", "talk_vis"}
        if set(channels) != wanted:
            raise ValueError(f"{name!r} face channels {sorted(channels)} != {sorted(wanted)}")
        defaults = sorted(ch for ch, d in channels.items() if d == "1")
        if defaults != ["face_knowing_vis"]:
            raise ValueError(f"{name!r}: exactly face_knowing_vis is shown by default, not {defaults}")


def _const(value: float) -> dict:
    return {"const": round(float(value), 4)}


def _expr(expr: str) -> dict:
    return {"expr": expr}


def _keys(values, *, ease: str = "smooth") -> dict:
    n = len(values)
    return {
        "keys": [
            [round(i / n, 6), round(float(value), 4), ease]
            for i, value in enumerate(values)
        ]
    }


def _shot(values, *, ease: str = "smooth") -> dict:
    """Keys for a ONE-SHOT clip, spaced the way one-shots are sampled.

    ``RigDocument.frame_time`` samples a loop at ``i/n`` and a one-shot at
    ``i/(n-1)`` -- so a one-shot authored with :func:`_keys` puts its last key at
    ``(n-1)/n`` and its last FRAME at ``1.0``, which clamps and spends the final
    frame repeating the one before it.  For a walk cycle that is invisible; for
    an attack it eats the recovery frame, which is the one the eye reads as "the
    swing is over".  These land on the frames.
    """

    n = len(values)
    return {
        "keys": [
            [round(i / max(1, n - 1), 6), round(float(value), 4), ease]
            for i, value in enumerate(values)
        ]
    }


def _rest(doc: dict, prefix: str, axis: str) -> float:
    for chain in doc.get("ik_chains", []):
        if chain.get("channel_prefix") == prefix:
            return float(chain[f"rest_{axis}"])
    for leg in doc.get("ik_legs", []):
        if leg.get("channel_prefix") == prefix:
            return float(leg[f"rest_{axis}"])
    raise KeyError((prefix, axis))


def _rest_pitch(doc: dict, prefix: str) -> float:
    for collection in (doc.get("ik_chains", []), doc.get("ik_legs", [])):
        for chain in collection:
            if chain.get("channel_prefix") == prefix:
                return float(chain["rest_pitch"])
    raise KeyError(prefix)


def _set_face(channels: dict, face: str) -> dict:
    """Show ``face`` and hide every other expression, unless the clip already
    chooses one."""
    if any(key.startswith("face_") for key in channels):
        return channels
    for name in FACES:
        channels[f"face_{name}_vis"] = _const(1.0 if name == face else 0.0)
    return channels


def _face_stills() -> dict:
    """One still per expression, at rest: the portraits are drawn from these."""
    return {
        f"face_{face}": {"loop": False, "frames": 1, "duration_ms": 100, "channels": _set_face(_with_visibility({}), face)}
        for face in FACES
    }


def _with_visibility(channels: dict, *, blink=0.0, talk=0.0):
    """Set the blink and talk overlays.

    Character art deliberately contains no tools, machines, bags, or other
    detachable props. Runtime props should bind to the exported hand sockets.
    """

    channels.update(
        {
            "blink_vis": _const(blink),
            "talk_vis": _const(talk),
        }
    )
    return channels


#: Pose offsets (SVG units, and degrees of hand pitch) from the rest hands.
IDLE_HAND = (26.0, -26.0, -50.0)
TALK_HAND = (18.0, -58.0, -80.0)


def _three_quarter_clips(doc: dict) -> dict:
    nx = _rest(doc, "near_hand", "x")
    ny = _rest(doc, "near_hand", "y")
    fx = _rest(doc, "far_hand", "x")
    fy = _rest(doc, "far_hand", "y")
    np = _rest_pitch(doc, "near_hand")
    fp = _rest_pitch(doc, "far_hand")
    scale = float(doc["svg_source"]["scale"])

    # At ease, the near hand resting on the apron's pouch, the far one hanging.
    rest_x, rest_y = nx + IDLE_HAND[0] * scale, ny + IDLE_HAND[1] * scale
    idle = _with_visibility(
        {
            "root_y": _expr("-0.55*sin(tau*t)"),
            "torso": _expr("0.7*sin(tau*t)"),
            "head": _expr("-0.5*sin(tau*t)"),
            "near_hand_x": _expr(f"{rest_x:.4f} - 0.4*sin(tau*t)"),
            "near_hand_y": _expr(f"{rest_y:.4f} + 0.4*sin(tau*t)"),
            "near_hand_pitch": _const(np + IDLE_HAND[2]),
            "far_hand_x": _expr(f"{fx:.4f} + 0.5*sin(tau*t)"),
            "far_hand_y": _expr(f"{fy:.4f} - 0.35*sin(tau*t)"),
            "far_hand_pitch": _const(fp),
            # Narrow pulse near the end of the 8-frame loop.
            "blink_vis": {
                "keys": [
                    [0.0, 0.0, "linear"],
                    [0.72, 0.0, "linear"],
                    [0.78, 1.0, "linear"],
                    [0.88, 0.0, "linear"],
                ]
            },
        }
    )

    near_dx = 15.0 * scale
    near_dy = 15.0 * scale
    far_dx = 7.0 * scale
    far_dy = 1.0 * scale
    interact = _with_visibility(
        {
            "root_y": _keys([0.0, 0.5, 0.9, 0.7, 0.3, 0.0]),
            "torso": _keys([0.0, 1.0, 2.2, 1.3, 2.0, 0.0]),
            "head": _keys([0.0, -1.0, -2.1, -1.5, -2.0, 0.0]),
            "near_hand_x": _keys(
                [
                    nx,
                    nx + near_dx * 0.45,
                    nx + near_dx,
                    nx + near_dx * 0.8,
                    nx + near_dx,
                    nx,
                ]
            ),
            "near_hand_y": _keys(
                [
                    ny,
                    ny + near_dy * 0.4,
                    ny + near_dy,
                    ny + near_dy * 0.8,
                    ny + near_dy,
                    ny,
                ]
            ),
            "near_hand_pitch": _keys([np, np + 4, np + 13, np - 7, np + 12, np]),
            "far_hand_x": _keys([fx, fx + far_dx, fx + far_dx, fx + far_dx, fx, fx]),
            "far_hand_y": _keys([fy, fy + far_dy, fy + far_dy, fy, fy, fy]),
            "far_hand_pitch": _const(fp),
        }
    )
    return {
        "idle": {"loop": True, "frames": 8, "duration_ms": 120, "channels": idle},
        "interact": {
            "loop": False,
            "frames": 6,
            "duration_ms": 105,
            "channels": interact,
        },
    }


def _front_clips(doc: dict) -> dict:
    nx = _rest(doc, "near_hand", "x")
    ny = _rest(doc, "near_hand", "y")
    fx = _rest(doc, "far_hand", "x")
    fy = _rest(doc, "far_hand", "y")
    np = _rest_pitch(doc, "near_hand")
    fp = _rest_pitch(doc, "far_hand")
    scale = float(doc["svg_source"]["scale"])

    # The teacher's gesture: the near hand lifts open to his chest and turns
    # up, as if setting the point down in front of you.
    gesture_x = TALK_HAND[0] * scale
    gesture_y = TALK_HAND[1] * scale
    talk = _with_visibility(
        {
            "root_y": _keys([0.0, -0.4, 0.0, -0.5, 0.0, -0.2]),
            "torso": _keys([0.0, -0.5, 0.3, -0.4, 0.2, 0.0]),
            "head": _keys([0.0, 0.8, -0.5, 0.6, -0.4, 0.0]),
            "near_hand_x": _keys(
                [
                    nx,
                    nx + gesture_x * 0.45,
                    nx + gesture_x,
                    nx + gesture_x * 0.75,
                    nx + gesture_x * 0.2,
                    nx,
                ]
            ),
            "near_hand_y": _keys(
                [
                    ny,
                    ny + gesture_y * 0.35,
                    ny + gesture_y,
                    ny + gesture_y * 0.7,
                    ny + gesture_y * 0.15,
                    ny,
                ]
            ),
            "near_hand_pitch": _keys([np, np + TALK_HAND[2] * 0.5, np + TALK_HAND[2], np + TALK_HAND[2] * 0.8, np + TALK_HAND[2] * 0.2, np]),
            "far_hand_x": _keys([fx, fx + 1.2, fx + 2.0, fx + 1.0, fx, fx]),
            "far_hand_y": _keys([fy, fy - 0.5, fy - 1.0, fy - 0.5, fy, fy]),
            "far_hand_pitch": _const(fp),
            "talk_vis": _keys([0.0, 1.0, 0.0, 1.0, 0.0, 1.0], ease="linear"),
            "blink_vis": _keys([0.0, 0.0, 0.0, 0.0, 1.0, 0.0], ease="linear"),
        }
    )
    return {"talk": {"loop": True, "frames": 6, "duration_ms": 100, "channels": talk}}


def _side_clips(doc: dict) -> dict:
    nfx = _rest(doc, "near_foot", "x")
    nfp = _rest_pitch(doc, "near_foot")
    ffx = _rest(doc, "far_foot", "x")
    ffp = _rest_pitch(doc, "far_foot")
    nhx = _rest(doc, "near_hand", "x")
    nhy = _rest(doc, "near_hand", "y")
    nhp = _rest_pitch(doc, "near_hand")
    fhx = _rest(doc, "far_hand", "x")
    fhy = _rest(doc, "far_hand", "y")
    fhp = _rest_pitch(doc, "far_hand")

    stride = [10, 7, 3, -2, -10, -8, -3, 4]
    lift = [0, 0, 0, 0, 0, 3, 6, 3]
    far_stride = stride[4:] + stride[:4]
    far_lift = lift[4:] + lift[:4]
    arm = [-5.5, -4.0, -1.5, 2.5, 5.5, 4.0, 1.5, -2.5]
    far_arm = arm[4:] + arm[:4]

    walk = _with_visibility(
        {
            "root_y": _keys([0.0, 1.15, 0.35, -0.55, 0.0, 1.15, 0.35, -0.55]),
            "torso": _keys([0.5, 1.2, 0.4, -0.2, -0.5, -1.2, -0.4, 0.2]),
            "head": _keys([-0.3, -0.7, -0.2, 0.2, 0.3, 0.7, 0.2, -0.2]),
            "near_foot_x": _keys([nfx + v for v in stride], ease="linear"),
            "near_foot_lift": _keys(lift),
            "near_foot_pitch": _keys([nfp + v for v in (6, 2, -2, -5, 0, 3, 9, 11)]),
            "far_foot_x": _keys([ffx + v for v in far_stride], ease="linear"),
            "far_foot_lift": _keys(far_lift),
            "far_foot_pitch": _keys([ffp + v for v in (0, 3, 9, 11, 6, 2, -2, -5)]),
            "near_hand_x": _keys([nhx + v for v in arm]),
            "near_hand_y": _keys(
                [nhy + v for v in (0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5)]
            ),
            "near_hand_pitch": _keys([nhp + v for v in (0, 1, 2, 1, 0, -1, -2, -1)]),
            "far_hand_x": _keys([fhx + v for v in far_arm]),
            "far_hand_y": _keys([fhy + v for v in (0, -0.5, -1, -0.5, 0, 0.5, 1, 0.5)]),
            "far_hand_pitch": _keys([fhp + v for v in (0, -1, -2, -1, 0, 1, 2, 1)]),
            "blink_vis": _keys([0, 0, 0, 0, 0, 0, 1, 0], ease="linear"),
        }
    )
    clips = {"walk": {"loop": True, "frames": 8, "duration_ms": 100, "channels": walk}}
    clips.update(_side_fight_clips(doc))
    return clips


def _arm_envelope(doc: dict, prefix: str) -> tuple:
    """Where this arm hangs from, and how far it can get -- in CHANNEL units.

    IK hand channels are frame offsets from ``(center_x, ground_y)``, and the
    shoulder is a fact of the SVG, so hardcoding either would silently rot the
    moment the drawing moves.  Returns ``(shoulder_x, shoulder_y, reach)``.
    """

    document = RigDocument(doc)
    skeleton = document.build_skeleton()
    frame = doc["frame"]
    cx = float(frame["center_x"])
    gy = float(frame["ground_y"])
    chain = next(
        c for c in doc["ik_chains"] if c.get("channel_prefix") == prefix
    )
    world = skeleton.world({}, root=(cx, gy))
    shoulder = world[chain["upper"]].origin
    reach = skeleton.bones[chain["upper"]].length + skeleton.bones[chain["lower"]].length
    return (shoulder[0] - cx, shoulder[1] - gy, reach)


def _side_fight_clips(doc: dict) -> dict:
    """**The rows Oiler needed before he could fight.**

    His sheet published four: idle, walk, talk, interact.  A platform-fighter
    move names the row it wants and settles for ``attack_side`` -> ``attack`` ->
    ``slash`` -> ``idle``, so every swing in a sixteen-move repertoire drew the
    STANDING POSE -- and cost the gameplay nothing to do it, which is why it
    stayed broken.  These are the rows that table names
    (``game/ambition_content/src/oiler_moveset.rs``).

    Side view, because a platform fighter is a side-on game and it is the
    silhouette his walk already reads in.

    NB the art is contractually propless -- no wrench, no oil can, no satchel --
    so every pose here is MIMED at the hand sockets.  A tool belongs on
    ``sockets.tool_grip`` at runtime, never in the SVG.

    !! **poses are authored as ANGLES on the arm's reachable circle, not as
    (x, y) guesses.**  Oiler's arms are short and already near full extension
    at rest -- a 26.5px reach from a shoulder 25.6px above the hanging wrist --
    so a target picked by eye lands outside the circle, gets clamped by the IK,
    and every "big" swing collapses onto the same 45-degree pose.  The first
    draft of these clips did exactly that and read as a man shrugging.
    """

    sx, sy, reach = _arm_envelope(doc, "near_hand")
    fsx, fsy, freach = _arm_envelope(doc, "far_hand")
    nhp = _rest_pitch(doc, "near_hand")
    fhp = _rest_pitch(doc, "far_hand")
    nfx = _rest(doc, "near_foot", "x")
    ffx = _rest(doc, "far_foot", "x")

    # Forward is +x: the side rig's own geometry check requires the wrist to
    # return forward of the elbow and the elbow to sit behind the shoulder.
    # Angles are measured from straight-forward, positive downward, so the
    # hanging rest pose is +90 and straight overhead is -90.
    REST_DEG = 90.0

    def near(deg: float, frac: float = 0.94) -> tuple:
        rad = math.radians(deg)
        return (sx + reach * frac * math.cos(rad), sy + reach * frac * math.sin(rad))

    def far(deg: float, frac: float = 0.94) -> tuple:
        rad = math.radians(deg)
        return (
            fsx + freach * frac * math.cos(rad),
            fsy + freach * frac * math.sin(rad),
        )

    def pitch(rest: float, deg: float) -> float:
        """Hand pitch that follows the arm, calibrated off its own rest pose."""
        return rest + (deg - REST_DEG)

    def arm(poses, *, side="near"):
        """Expand ``[(deg, frac), ...]`` into the three channels one arm needs."""
        place = near if side == "near" else far
        rest = nhp if side == "near" else fhp
        targets = [place(deg, frac) for deg, frac in poses]
        prefix = "near_hand" if side == "near" else "far_hand"
        return {
            f"{prefix}_x": _shot([t[0] for t in targets]),
            f"{prefix}_y": _shot([t[1] for t in targets]),
            f"{prefix}_pitch": _shot([pitch(rest, deg) for deg, _ in poses]),
        }

    # ---- the swings ------------------------------------------------------
    # A flat wrench swing at chest height: wind back over the shoulder, come
    # through level, follow through low.
    attack_side = _with_visibility(
        {
            "root_x": _shot([0.0, -2.0, 0.0, 2.5, 3.0, 0.5]),
            "torso": _shot([0.0, -7.0, 0.0, 9.0, 8.0, 2.0]),
            "head": _shot([0.0, 4.0, 0.0, -5.0, -4.0, -1.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (152.0, 0.72),
                    (118.0, 0.80),
                    (18.0, 0.98),
                    (2.0, 0.99),
                    (52.0, 0.92),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (128.0, 0.78),
                    (110.0, 0.82),
                    (56.0, 0.92),
                    (44.0, 0.94),
                    (78.0, 0.92),
                ],
                side="far",
            ),
            "near_foot_x": _shot([nfx + 2, nfx, nfx + 3, nfx + 8, nfx + 9, nfx + 3]),
            "far_foot_x": _shot([ffx - 1, ffx - 3, ffx - 4, ffx - 6, ffx - 6, ffx - 2]),
        }
    )

    # The gauge needle sweeping: an overhead arc that beats a shorthop.
    attack_up = _with_visibility(
        {
            "root_y": _shot([0.0, 1.5, 0.0, -1.5, -2.0, -0.5]),
            "torso": _shot([0.0, 6.0, -2.0, -10.0, -11.0, -3.0]),
            "head": _shot([0.0, -4.0, 2.0, 8.0, 9.0, 3.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (128.0, 0.70),
                    (28.0, 0.78),
                    (-52.0, 0.96),
                    (-76.0, 0.99),
                    (-24.0, 0.90),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (104.0, 0.80),
                    (78.0, 0.84),
                    (36.0, 0.88),
                    (24.0, 0.90),
                    (64.0, 0.90),
                ],
                side="far",
            ),
            "near_foot_x": _shot([nfx, nfx - 1, nfx + 1, nfx + 3, nfx + 3, nfx]),
        }
    )

    # Oil dragged forward at shin height.  He drops onto the trailing leg for
    # it, because the arm alone cannot get anywhere near the floor.
    attack_down = _with_visibility(
        {
            "root_y": _shot([0.0, 1.0, 5.0, 8.5, 9.0, 2.5]),
            "torso": _shot([0.0, -4.0, 5.0, 13.0, 14.0, 4.0]),
            "head": _shot([0.0, 3.0, -4.0, -9.0, -10.0, -3.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (146.0, 0.72),
                    (110.0, 0.84),
                    (46.0, 0.98),
                    (34.0, 0.99),
                    (74.0, 0.92),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (124.0, 0.78),
                    (112.0, 0.84),
                    (86.0, 0.90),
                    (80.0, 0.92),
                    (86.0, 0.92),
                ],
                side="far",
            ),
            "near_foot_x": _shot([nfx + 1, nfx, nfx + 5, nfx + 10, nfx + 11, nfx + 3]),
            "far_foot_x": _shot([ffx - 1, ffx - 3, ffx - 6, ffx - 9, ffx - 9, ffx - 3]),
        }
    )

    # THE TORQUE SPEC -- Oiler's one kill move.  Four frames of visible windup,
    # because a heavyweight swing nobody can see coming is not a smash.
    smash_forward = _with_visibility(
        {
            "root_x": _shot([0.0, -2.5, -4.5, -4.5, 0.0, 4.0, 5.0, 1.5]),
            "root_y": _shot([0.0, 1.0, 2.5, 3.0, 1.0, -1.0, -1.5, 0.0]),
            "torso": _shot([0.0, -8.0, -13.0, -14.0, 0.0, 12.0, 15.0, 4.0]),
            "head": _shot([0.0, 5.0, 8.0, 9.0, 0.0, -8.0, -10.0, -3.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (150.0, 0.74),
                    (176.0, 0.86),
                    (182.0, 0.90),
                    (108.0, 0.80),
                    (16.0, 0.99),
                    (4.0, 1.00),
                    (56.0, 0.92),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (136.0, 0.80),
                    (158.0, 0.86),
                    (162.0, 0.88),
                    (114.0, 0.82),
                    (52.0, 0.94),
                    (42.0, 0.96),
                    (80.0, 0.92),
                ],
                side="far",
            ),
            "near_foot_x": _shot(
                [nfx, nfx - 3, nfx - 4, nfx - 4, nfx + 2, nfx + 9, nfx + 10, nfx + 3]
            ),
            "far_foot_x": _shot(
                [ffx, ffx - 1, ffx - 2, ffx - 2, ffx - 4, ffx - 7, ffx - 7, ffx - 2]
            ),
        }
    )

    # THE GEYSER, and the pose every special borrows: both hands down to a valve
    # at his feet, brace, and then flung up as the line lets go.
    special = _with_visibility(
        {
            "root_y": _shot([0.0, 2.5, 6.0, 7.0, 3.0, -2.0, -4.0, -2.5]),
            "root_x": _shot([0.0, 0.5, 1.5, 1.5, 0.5, -1.0, -1.5, -1.0]),
            "torso": _shot([0.0, 6.0, 13.0, 15.0, 5.0, -9.0, -16.0, -11.0]),
            "head": _shot([0.0, -4.0, -9.0, -11.0, -3.0, 7.0, 13.0, 9.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (76.0, 0.94),
                    (58.0, 0.99),
                    (52.0, 1.00),
                    (74.0, 0.92),
                    (-16.0, 0.90),
                    (-64.0, 0.99),
                    (-48.0, 0.94),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (80.0, 0.94),
                    (64.0, 0.98),
                    (58.0, 0.99),
                    (78.0, 0.92),
                    (-8.0, 0.90),
                    (-56.0, 0.98),
                    (-40.0, 0.94),
                ],
                side="far",
            ),
            "near_foot_x": _shot(
                [nfx, nfx + 2, nfx + 4, nfx + 4, nfx + 2, nfx, nfx - 1, nfx]
            ),
            "far_foot_x": _shot(
                [ffx, ffx - 2, ffx - 4, ffx - 4, ffx - 2, ffx, ffx + 1, ffx]
            ),
        }
    )

    # Struck: snapped back off his heels, and back to stance.
    hit = _with_visibility(
        {
            "root_x": _shot([0.0, -4.5, -3.0, -1.0, 0.0]),
            "root_y": _shot([0.0, -1.5, -0.5, 0.0, 0.0]),
            "torso": _shot([0.0, 13.0, 8.0, 3.0, 0.0]),
            "head": _shot([0.0, -15.0, -10.0, -4.0, 0.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (126.0, 0.72),
                    (112.0, 0.78),
                    (98.0, 0.86),
                    (REST_DEG, 0.90),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (134.0, 0.74),
                    (118.0, 0.80),
                    (100.0, 0.88),
                    (REST_DEG, 0.92),
                ],
                side="far",
            ),
            "near_foot_x": _shot([nfx, nfx - 5, nfx - 3, nfx - 1, nfx]),
            "far_foot_x": _shot([ffx, ffx - 3, ffx - 2, ffx - 1, ffx]),
        }
    )
    # !! after `_with_visibility`, which writes both gates as consts.
    hit["blink_vis"] = _shot([0.0, 1.0, 1.0, 0.0, 0.0], ease="linear")

    # Down: he folds backwards over the hip and stays there.  The lean stops at
    # 30 degrees so his head never leaves the logical frame.
    death = _with_visibility(
        {
            "root_x": _shot([0.0, -1.5, -4.0, -6.0, -7.5, -8.0]),
            "root_y": _shot([0.0, -1.0, 3.0, 8.0, 12.0, 14.0]),
            "torso": _shot([0.0, 7.0, 15.0, 23.0, 28.0, 30.0]),
            "head": _shot([0.0, -7.0, -12.0, -16.0, -18.0, -19.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (108.0, 0.84),
                    (126.0, 0.76),
                    (142.0, 0.70),
                    (152.0, 0.66),
                    (156.0, 0.64),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (104.0, 0.86),
                    (120.0, 0.78),
                    (136.0, 0.72),
                    (146.0, 0.68),
                    (150.0, 0.66),
                ],
                side="far",
            ),
            "near_foot_x": _shot([nfx, nfx + 2, nfx + 5, nfx + 8, nfx + 10, nfx + 11]),
            "near_foot_lift": _shot([0.0, 0.0, 0.5, 1.5, 2.0, 2.0]),
            "far_foot_x": _shot([ffx, ffx + 1, ffx + 3, ffx + 5, ffx + 6, ffx + 6]),
        },
        blink=1.0,
    )

    # Wipes his hands on the apron, then points at the mess you are about to be.
    taunt = _with_visibility(
        {
            "root_y": _shot([0.0, 0.5, 1.0, 0.5, 0.0, -0.5, -1.0, -0.5]),
            "torso": _shot([0.0, 3.0, 6.0, 3.0, 0.0, -3.0, -6.0, -3.0]),
            "head": _shot([0.0, -2.0, -3.0, -2.0, 0.0, 3.0, 6.0, 3.0]),
            **arm(
                [
                    (REST_DEG, 0.90),
                    (98.0, 0.66),
                    (104.0, 0.58),
                    (98.0, 0.66),
                    (REST_DEG, 0.90),
                    (46.0, 0.86),
                    (6.0, 0.99),
                    (48.0, 0.92),
                ]
            ),
            **arm(
                [
                    (REST_DEG, 0.92),
                    (94.0, 0.68),
                    (100.0, 0.60),
                    (94.0, 0.68),
                    (REST_DEG, 0.92),
                    (96.0, 0.90),
                    (98.0, 0.92),
                    (94.0, 0.92),
                ],
                side="far",
            ),
        }
    )
    taunt["blink_vis"] = _shot(
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0], ease="linear"
    )

    def one_shot(frames: int, duration_ms: int, channels: dict) -> dict:
        return {
            "loop": False,
            "frames": frames,
            "duration_ms": duration_ms,
            "channels": channels,
        }

    clips = {
        "attack_side": one_shot(6, 70, attack_side),
        "attack_up": one_shot(6, 66, attack_up),
        "attack_down": one_shot(6, 70, attack_down),
        "smash_forward": one_shot(8, 64, smash_forward),
        "special": one_shot(8, 72, special),
        "hit": one_shot(5, 80, hit),
        "death": one_shot(6, 90, death),
        "taunt": one_shot(8, 100, taunt),
    }
    # The Smash rows, and the four swings above retimed to their moves.
    clips.update(_side_smash_clips(doc))
    return clips


#: Where each Smash move of his table (``data/movesets/oiler.ron``) is live,
#: as parts of the move: (window start, window end) / duration.  A fight row
#: is slaved to its move -- frame ``floor(progress * frames)`` -- so the strike
#: pose is put on every frame that shows a live window.  Keep in step with the
#: table.
SMASH_ROW_WINDOWS = {
    "jab": (8, [(0.188, 0.5)]),
    "attack_side": (8, [(0.262, 0.524)]),
    "attack_up": (8, [(0.238, 0.524)]),
    "attack_down": (8, [(0.225, 0.525)]),
    "dash_attack": (10, [(0.119, 0.381)]),
    "smash_forward": (10, [(0.371, 0.514)]),
    "smash_up": (10, [(0.358, 0.522)]),
    "smash_down": (10, [(0.324, 0.5)]),
    "air_neutral": (8, [(0.179, 0.59)]),
    "air_forward": (8, [(0.279, 0.535)]),
    "air_back": (8, [(0.289, 0.511)]),
    "air_up": (8, [(0.231, 0.538)]),
    "air_down": (8, [(0.265, 0.51)]),
    "convergence": (12, [(0.28, 0.4), (0.52, 0.64), (0.72, 0.88)]),
    "special_side": (10, [(0.242, 0.424)]),
    "special_up": (12, [(0.183, 0.3)]),
    "special_down": (10, [(0.208, 0.458)]),
}


def _side_smash_clips(doc: dict) -> dict:
    """**Every Smash move its own row, struck on the frames the move is live.**

    A pose is a dict: ``near``/``far`` are ``(deg, frac)`` on the arm's
    reachable circle (forward 0, down +90, up -90, back 180; see
    `_side_fight_clips`), ``nfx``/``ffx`` move a foot from its rest x,
    ``nlift``/``flift`` raise it, and ``torso``/``head``/``root_x``/``root_y``
    are the channels of the same names.  A row has a rest pose (the standing
    guard, or a tuck in the air), an anticipation, and one strike pose per live
    window (two give the strike a direction through its frames).  Mimed: he is
    propless.
    """

    sx, sy, reach = _arm_envelope(doc, "near_hand")
    fsx, fsy, freach = _arm_envelope(doc, "far_hand")
    nhp = _rest_pitch(doc, "near_hand")
    fhp = _rest_pitch(doc, "far_hand")
    nfx = _rest(doc, "near_foot", "x")
    ffx = _rest(doc, "far_foot", "x")

    skeleton = RigDocument(doc).build_skeleton()
    cx = float(doc["frame"]["center_x"])
    gy = float(doc["frame"]["ground_y"])
    stand = {"near": (90.0, 0.90), "far": (90.0, 0.92)}
    tuck = {"near": (70.0, 0.9), "far": (80.0, 0.9), "nlift": 10.0, "flift": 12.0, "nfx": 3.0, "ffx": -2.0}
    fields = ("torso", "head", "root_x", "root_y", "nfx", "ffx", "nlift", "flift")

    def blend(a: dict, b: dict, k: float) -> dict:
        out = {}
        for name in fields:
            va, vb = a.get(name, 0.0), b.get(name, 0.0)
            out[name] = va + (vb - va) * k
        for arm_name in ("near", "far"):
            (da, fa), (db, fb) = a[arm_name], b[arm_name]
            out[arm_name] = (da + (db - da) * k, fa + (fb - fa) * k)
        return out

    def full(pose: dict, rest: dict) -> dict:
        return {**{name: 0.0 for name in fields}, **rest, **pose}

    def smooth(t: float) -> float:
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

    def row(name: str, wind: dict, strikes: list, *, rest: dict = stand, hold: float = 0.0) -> dict:
        frames, windows = SMASH_ROW_WINDOWS[name]
        rest = full({}, rest)
        wind = full(wind, rest)
        strikes = [[full(s, rest) for s in (k if isinstance(k, list) else [k])] for k in strikes]
        live = [
            [i for i in range(frames) if i / frames < b and (i + 1) / frames > a]
            for a, b in windows
        ]
        first, last = live[0][0], live[-1][-1]
        poses = []
        for i in range(frames):
            hit = next((k for k, idx in enumerate(live) if i in idx), None)
            if hit is not None:
                keys, idx = strikes[min(hit, len(strikes) - 1)], live[hit]
                u = 0.0 if len(idx) == 1 else (i - idx[0]) / (len(idx) - 1)
                pose = keys[0] if len(keys) == 1 else blend(keys[0], keys[1], u)
            elif i < first:
                pose = blend(rest, wind, smooth((i + 1) / first))
            elif i > last:
                end = strikes[min(len(live), len(strikes)) - 1][-1]
                u = (i - last) / (frames - 1 - last)
                u = max(0.0, (u - hold) / (1.0 - hold)) if hold else u
                pose = blend(end, rest, smooth(u))
            else:
                prev = max(k for k, idx in enumerate(live) if idx[-1] < i)
                pose = blend(strikes[min(prev, len(strikes) - 1)][-1], wind, 0.6)
            poses.append(pose)

        def place(side: str, deg: float, frac: float, pose: dict) -> tuple:
            # The hand target is a frame point, but the shoulder moves with the
            # root and the lean: aim from where the shoulder IS in this pose,
            # or a lunge crumples the arm it is meant to extend.
            r = reach if side == "near" else freach
            world = skeleton.world({"torso": pose["torso"]}, root=(cx + pose["root_x"], gy + pose["root_y"]))
            ox, oy = world[f"{side}_arm_u"].origin
            rad = math.radians(deg)
            return (ox - cx + r * frac * math.cos(rad), oy - gy + r * frac * math.sin(rad))

        channels = {}
        for name_, key in (("torso", "torso"), ("head", "head"), ("root_x", "root_x"), ("root_y", "root_y")):
            channels[name_] = _shot([p[key] for p in poses])
        channels["near_foot_x"] = _shot([nfx + p["nfx"] for p in poses])
        channels["far_foot_x"] = _shot([ffx + p["ffx"] for p in poses])
        channels["near_foot_lift"] = _shot([p["nlift"] for p in poses])
        channels["far_foot_lift"] = _shot([p["flift"] for p in poses])
        for side, rest_pitch in (("near", nhp), ("far", fhp)):
            targets = [place(side, *p[side], p) for p in poses]
            channels[f"{side}_hand_x"] = _shot([t[0] for t in targets])
            channels[f"{side}_hand_y"] = _shot([t[1] for t in targets])
            channels[f"{side}_hand_pitch"] = _shot([rest_pitch + (p[side][0] - 90.0) for p in poses])
        return {"loop": False, "frames": frames, "duration_ms": 60, "channels": _with_visibility(channels)}

    return {
        # A straight punch off the front hand, a half step in.
        "jab": row(
            "jab",
            {"near": (124.0, 0.74), "far": (74.0, 0.9), "torso": -3.0, "root_x": -1.0},
            [[{"near": (4.0, 0.99), "far": (66.0, 0.9), "torso": 6.0, "head": -3.0, "root_x": 2.0, "nfx": 4.0},
              {"near": (0.0, 1.0), "far": (60.0, 0.9), "torso": 7.0, "head": -4.0, "root_x": 2.5, "nfx": 5.0}]],
        ),
        # The flat swing at chest height, now on the frames the move is live.
        "attack_side": row(
            "attack_side",
            {"near": (152.0, 0.72), "far": (128.0, 0.78), "torso": -7.0, "head": 4.0, "root_x": -2.0, "ffx": -2.0},
            [[{"near": (18.0, 0.98), "far": (56.0, 0.92), "torso": 9.0, "head": -5.0, "root_x": 2.5, "nfx": 8.0, "ffx": -6.0},
              {"near": (2.0, 0.99), "far": (44.0, 0.94), "torso": 8.0, "head": -4.0, "root_x": 3.0, "nfx": 9.0, "ffx": -6.0}]],
        ),
        # The overhead arc.
        "attack_up": row(
            "attack_up",
            {"near": (128.0, 0.70), "far": (104.0, 0.8), "torso": 6.0, "head": -4.0, "root_y": 1.5},
            [[{"near": (-40.0, 0.96), "far": (36.0, 0.88), "torso": -8.0, "head": 6.0, "root_y": -1.5, "nfx": 3.0},
              {"near": (-80.0, 0.99), "far": (20.0, 0.9), "torso": -11.0, "head": 9.0, "root_y": -2.0, "nfx": 3.0}]],
        ),
        # Low drag at shin height, dropped onto the trailing leg.
        "attack_down": row(
            "attack_down",
            {"near": (146.0, 0.72), "far": (124.0, 0.78), "torso": -4.0, "head": 3.0, "root_y": 1.0},
            [[{"near": (46.0, 0.98), "far": (86.0, 0.9), "torso": 13.0, "head": -9.0, "root_y": 8.5, "nfx": 10.0, "ffx": -9.0},
              {"near": (34.0, 0.99), "far": (80.0, 0.92), "torso": 14.0, "head": -10.0, "root_y": 9.0, "nfx": 11.0, "ffx": -9.0}]],
        ),
        # Shoulder first out of the run, both hands low and in front.
        "dash_attack": row(
            "dash_attack",
            {"near": (110.0, 0.8), "far": (100.0, 0.85), "torso": 8.0},
            [[{"near": (28.0, 0.99), "far": (44.0, 0.97), "torso": 18.0, "head": -6.0, "root_x": 5.0, "root_y": 2.0, "nfx": 12.0, "ffx": -10.0},
              {"near": (20.0, 1.0), "far": (36.0, 0.98), "torso": 19.0, "head": -7.0, "root_x": 6.0, "root_y": 2.5, "nfx": 13.0, "ffx": -11.0}]],
        ),
        # The torque spec, his kill move: back over the shoulder, then through.
        "smash_forward": row(
            "smash_forward",
            {"near": (176.0, 0.8), "far": (160.0, 0.8), "torso": -14.0, "head": 9.0, "root_x": -4.5, "root_y": 3.0, "nfx": -2.0, "ffx": -2.0},
            [[{"near": (6.0, 0.99), "far": (30.0, 0.95), "torso": 12.0, "head": -8.0, "root_x": 4.0, "root_y": -1.0, "nfx": 11.0, "ffx": -9.0},
              {"near": (-8.0, 1.0), "far": (20.0, 0.97), "torso": 15.0, "head": -10.0, "root_x": 5.0, "root_y": -1.5, "nfx": 12.0, "ffx": -9.0}]],
        ),
        # Out of a crouch, both fists straight up.
        "smash_up": row(
            "smash_up",
            {"near": (132.0, 0.8), "far": (122.0, 0.8), "torso": 10.0, "head": -4.0, "root_y": 7.0, "nfx": 3.0, "ffx": -3.0},
            [[{"near": (-66.0, 0.99), "far": (-52.0, 0.95), "torso": -8.0, "head": 5.0, "root_y": -3.0},
              {"near": (-92.0, 1.0), "far": (-80.0, 0.98), "torso": -12.0, "head": 7.0, "root_y": -5.0}]],
        ),
        # Hands up, then driven down to both sides of him at once.
        "smash_down": row(
            "smash_down",
            {"near": (-40.0, 0.9), "far": (-52.0, 0.9), "torso": -6.0, "head": 3.0, "root_y": -1.0},
            [[{"near": (26.0, 0.99), "far": (150.0, 0.99), "torso": 8.0, "head": -6.0, "root_y": 9.0, "nfx": 10.0, "ffx": -10.0},
              {"near": (36.0, 1.0), "far": (142.0, 1.0), "torso": 10.0, "head": -7.0, "root_y": 10.0, "nfx": 11.0, "ffx": -11.0}]],
        ),
        # Spread like a star: a hand and a foot each way.
        "air_neutral": row(
            "air_neutral",
            {"near": (60.0, 0.85), "far": (100.0, 0.85), "nlift": 16.0, "flift": 16.0},
            [[{"near": (-14.0, 0.99), "far": (176.0, 0.97), "torso": -4.0, "nlift": 14.0, "flift": 12.0, "nfx": 13.0, "ffx": -13.0},
              {"near": (-4.0, 1.0), "far": (186.0, 0.98), "torso": -2.0, "nlift": 12.0, "flift": 14.0, "nfx": 14.0, "ffx": -14.0}]],
            rest=tuck,
        ),
        # Both hands from overhead down through the front.
        "air_forward": row(
            "air_forward",
            {"near": (-76.0, 0.95), "far": (-62.0, 0.9), "torso": -6.0, "head": 4.0},
            [[{"near": (4.0, 0.99), "far": (22.0, 0.95), "torso": 10.0, "head": -5.0},
              {"near": (36.0, 0.99), "far": (50.0, 0.96), "torso": 14.0, "head": -7.0}]],
            rest=tuck,
        ),
        # A back kick, chambered, then out behind him at hip height.
        "air_back": row(
            "air_back",
            {"near": (60.0, 0.9), "far": (70.0, 0.9), "flift": 18.0, "ffx": -2.0, "torso": 4.0},
            [[{"near": (30.0, 0.95), "far": (40.0, 0.9), "torso": 14.0, "head": -4.0, "ffx": -30.0, "flift": 32.0, "nlift": 14.0, "nfx": 6.0},
              {"near": (26.0, 0.95), "far": (36.0, 0.9), "torso": 16.0, "head": -5.0, "ffx": -33.0, "flift": 34.0, "nlift": 14.0, "nfx": 6.0}]],
            rest=tuck,
        ),
        # Both fists up over his head.
        "air_up": row(
            "air_up",
            {"near": (110.0, 0.85), "far": (100.0, 0.85), "torso": 6.0},
            [[{"near": (-60.0, 0.99), "far": (-46.0, 0.95), "torso": -8.0, "head": 4.0},
              {"near": (-94.0, 1.0), "far": (-80.0, 0.98), "torso": -11.0, "head": 6.0}]],
            rest=tuck,
        ),
        # A stomp: one heel driven straight down, the hands up for balance.
        "air_down": row(
            "air_down",
            {"near": (60.0, 0.9), "far": (70.0, 0.9), "nlift": 18.0, "flift": 18.0},
            [[{"near": (-46.0, 0.9), "far": (-66.0, 0.9), "torso": 4.0, "head": -4.0, "nlift": 0.0, "nfx": 2.0, "flift": 20.0, "ffx": -6.0},
              {"near": (-52.0, 0.92), "far": (-72.0, 0.9), "torso": 5.0, "head": -5.0, "nlift": -2.0, "nfx": 1.0, "flift": 20.0, "ffx": -6.0}]],
            rest=tuck,
        ),
        # Three blows that land on one point: front hand, back hand, both.
        "convergence": row(
            "convergence",
            {"near": (120.0, 0.78), "far": (114.0, 0.8), "torso": -3.0},
            [
                {"near": (2.0, 0.99), "far": (96.0, 0.9), "torso": 6.0, "head": -3.0, "nfx": 4.0},
                {"near": (112.0, 0.8), "far": (2.0, 0.99), "torso": 8.0, "head": -4.0, "nfx": 5.0},
                {"near": (-4.0, 1.0), "far": (6.0, 0.99), "torso": 12.0, "head": -6.0, "root_x": 3.0, "nfx": 9.0, "ffx": -6.0},
            ],
        ),
        # A slide on the oil: low, long, the front hand leading.
        "special_side": row(
            "special_side",
            {"near": (140.0, 0.8), "far": (120.0, 0.82), "torso": -4.0, "root_y": 3.0},
            [[{"near": (14.0, 0.99), "far": (168.0, 0.95), "torso": 18.0, "head": -8.0, "root_x": 5.0, "root_y": 6.0, "nfx": 14.0, "ffx": -14.0},
              {"near": (8.0, 1.0), "far": (172.0, 0.96), "torso": 20.0, "head": -9.0, "root_x": 6.0, "root_y": 7.0, "nfx": 15.0, "ffx": -15.0}]],
        ),
        # Ridden up on the geyser, arms high; held while he rises.
        "special_up": row(
            "special_up",
            {"near": (122.0, 0.8), "far": (116.0, 0.8), "torso": 12.0, "head": -5.0, "root_y": 7.0},
            [[{"near": (-82.0, 0.99), "far": (-74.0, 0.97), "torso": -6.0, "head": 4.0, "root_y": -4.0, "nfx": -1.0, "ffx": 1.0},
              {"near": (-90.0, 1.0), "far": (-82.0, 0.98), "torso": -7.0, "head": 5.0, "root_y": -5.0, "nfx": -1.0, "ffx": 1.0}]],
            hold=0.55,
        ),
        # Down on the vents: both palms driven to the floor beside him.
        "special_down": row(
            "special_down",
            {"near": (-40.0, 0.9), "far": (-50.0, 0.9), "torso": -4.0, "root_y": -2.0},
            [[{"near": (54.0, 0.99), "far": (126.0, 0.99), "torso": 8.0, "head": -6.0, "root_y": 10.0, "nfx": 9.0, "ffx": -9.0},
              {"near": (58.0, 1.0), "far": (122.0, 1.0), "torso": 10.0, "head": -7.0, "root_y": 11.0, "nfx": 10.0, "ffx": -10.0}]],
        ),
    }


def seed_clips(view_name: str, doc: dict) -> dict:
    """A view's clips, each wearing its face (``FACE_OF``). A left view takes
    its right twin's clips: the same skeleton, his other side."""
    base = view_name.removesuffix("_left")
    if base == "three_quarter":
        clips = {**_three_quarter_clips(doc), **_face_stills()}
    elif base == "front":
        clips = {**_front_clips(doc), **_face_stills()}
    elif base == "side":
        clips = _side_clips(doc)
    else:
        raise KeyError(view_name)
    for name, clip in clips.items():
        _set_face(clip["channels"], FACE_OF.get(name, "knowing"))
    return clips


def _drop_retired_prop_channels(clips: dict) -> None:
    """Remove visibility channels from the earlier embedded-prop prototype."""

    for clip in clips.values():
        channels = clip.get("channels", {})
        channels.pop("tool_vis", None)
        channels.pop("machine_vis", None)


def build_one(view_name: str, *, fresh: bool) -> Path:
    spec = VIEWS[view_name]
    path = RIG_DIR / f"{spec.name}.rig.json"
    generated = build_humanoid_view_document(SVG, RIG_DIR, spec)
    generated["clips"] = seed_clips(view_name, generated)
    existing = {}
    if path.exists() and not fresh:
        existing = json.loads(path.read_text(encoding="utf8"))
    doc = generated if fresh else merge_generated_geometry(existing, generated)
    _drop_retired_prop_channels(doc.get("clips", {}))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf8")
    print(
        f"wrote {path.relative_to(ROOT)}: {len(doc['bones'])} bones, "
        f"{len(doc['parts'])} SVG parts, clips={list(doc['clips'])}"
    )
    return path


def cmd_build(args) -> None:
    _validate_svg_source()
    for name in VIEWS:
        build_one(name, fresh=args.fresh)


def cmd_validate(args) -> None:
    _validate_svg_source()
    paths = [build_one(name, fresh=args.fresh) for name in VIEWS]
    SCRATCH.mkdir(parents=True, exist_ok=True)
    for path in paths:
        doc = RigDocument.load(path)
        for clip, frames, _duration in doc.rows():
            images = [doc.render_frame(clip, i, frames) for i in range(frames)]
            if any(im.getchannel("A").getbbox() is None for im in images):
                raise RuntimeError(f"{path.name}:{clip} produced an empty frame")
            w = sum(im.width for im in images)
            strip = Image.new("RGBA", (w, images[0].height), (0, 0, 0, 0))
            x = 0
            for image in images:
                strip.alpha_composite(image, (x, 0))
                x += image.width
            out = SCRATCH / f"{path.stem}_{clip}.png"
            strip.save(out)
            print(f"validated {clip}: {out.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--fresh", action="store_true")
    build.set_defaults(func=cmd_build)
    validate = sub.add_parser("validate")
    validate.add_argument("--fresh", action="store_true")
    validate.set_defaults(func=cmd_validate)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
