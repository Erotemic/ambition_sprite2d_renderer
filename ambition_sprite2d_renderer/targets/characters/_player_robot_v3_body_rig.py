"""Scout's (``player_robot_v3``) VISUAL body rig, read from the SVG rig that
draws him.

The joints are the bones of the side rig document, and every clip frame is
solved by the same ``RigDocument.solve`` that draws the sheet row. A part's
pivot sits on its bone's origin, turned by the bone's angle less its rest
angle (``rigdoc.paint_part``), so each part rides one joint exactly, and the
rig names that joint for every part track (``part_bindings``), and the three
joints of each limb (``limbs``). The runtime can then place the parts from
joint frames (``PosedParts``) and hold a hand where a pose plants it.

It is a visual product. It has no hurt parts, and gameplay reads no rig unless
a composition admits rigs (``BodyRigAdmission``, off by default), so
publishing it moves no hurt volume and no muzzle.

Joints are published in world frames (no parents). The torso and the head
squash (``bone.<name>.scale_y``) and the head flips (``flip_x``); rigdoc
applies both to the part only, never to the bones hung from it. A frame local
to a squashed parent would need a shear the product cannot state.

Published rows: the side rows, each also as its mirror (``MIRRORED``), which
the sheet draws from the other side and flips about the frame's centre. Not
published, because a part must sit in one place on its joint and a clip must
cover its row's every frame:

- the back rows (``BACK_ROWS``: another rig, seen from behind);
- the side rows with front or back frames in them (the turns);
- the pure side rows (``PURE_SIDE_ROWS``): their rig has the same bones but
  hangs the shared limb rasters a few degrees and about a pixel apart from
  the side rig, so one raster would have two places on one joint.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from ...authoring.body_rig import BodyRigProduct, JointPose
from ...authoring.rigdoc import RigDocument

#: Attachment -> the limb that ends at it: upper bone, lower bone, end.
_LIMBS = {
    "hand_near": ("near_arm_u", "near_arm_l", "near_arm_hand"),
    "hand_far": ("far_arm_u", "far_arm_l", "far_arm_hand"),
    "foot_near": ("near_leg_u", "near_leg_l", "near_leg_foot"),
    "foot_far": ("far_leg_u", "far_leg_l", "far_leg_foot"),
}

#: Attachment -> (bone, along the bone as a fraction of its length): the hands
#: at the ends of the hand bones, the feet at the ankles.
_TIPS = {
    "hand_near": ("near_arm_hand", 1.0),
    "hand_far": ("far_arm_hand", 1.0),
    "foot_near": ("near_leg_foot", 0.0),
    "foot_far": ("far_leg_foot", 0.0),
    # The head's own joint: what a follow-through turns the head about.
    "head": ("head", 0.0),
}


def _joint(origin: Tuple[float, float], angle_deg: float, flip: bool, squash: float,
           feet: Tuple[float, float], mirror_width: float | None) -> JointPose:
    """One bone's world frame relative to the feet, mirrored about the frame's
    centre when ``mirror_width`` is the frame's width. A mirror maps the frame
    ``R(a)`` to ``M R(a) = R(-a) M``: the angle negated and the x axis flipped."""
    x, y = origin
    angle = math.radians(angle_deg)
    sx = -1.0 if flip else 1.0
    if mirror_width is not None:
        x, angle, sx = mirror_width - x, -angle, -sx
    return JointPose(translation=(x - feet[0], y - feet[1]), rotation=angle, scale=(sx, squash))


def body_rig(target: str, rows: Iterable[Tuple[str, int, int]], mirrored_name: str, side: RigDocument,
             excluded, feet: Tuple[float, float]) -> BodyRigProduct:
    """The rig of ``rows`` (the authored side rows, before their mirrors), less
    the rows in ``excluded``.

    ``mirrored_name`` formats a row's mirror (``MIRRORED``). ``feet`` is the
    sheet's feet pixel in the logical frame (``body_metrics`` less the publish
    padding); joint frames are relative to it."""
    bones = [str(bone["name"]) for bone in side.bones]
    width = float(side.frame["width"])
    clips: Dict[str, tuple] = {}
    for row, count, duration_ms in rows:
        if row in excluded:
            continue
        for mirrored in (False, True):
            clip = row
            if mirrored and mirrored_name.format(row) in side.clips:
                # A strike authors its own other-side clip (the blade stays in
                # the hand that holds it); the sheet draws that one mirrored.
                clip = mirrored_name.format(row)
            frames: List[List[JointPose]] = []
            for index in range(int(count)):
                world, params = side.solve(clip, side.frame_time(clip, index, count))
                frames.append([
                    _joint(
                        world[name].origin,
                        world[name].angle,
                        float(params.get(f"bone.{name}.flip_x", 0.0)) >= 0.5,
                        round(float(params.get(f"bone.{name}.scale_y", 1.0)), 4) or 1.0,
                        feet,
                        width if mirrored else None,
                    )
                    for name in bones
                ])
            looping = bool(side.clips[row].get("loop", False))
            clips[mirrored_name.format(row) if mirrored else row] = (looping, float(duration_ms) / 1000.0, frames)

    rest, _params = side.solve("idle", 0.0)
    lengths = {name: float(rest[name].length) for name in bones}
    attachments = [
        (attachment, bone, (lengths[bone] * along, 0.0)) for attachment, (bone, along) in _TIPS.items()
    ]
    # Every rig part rides its bone. The flipbook may draw a symmetric raster
    # as one half and its mirror (`<track>~mirror`); that half rides it too.
    part_bindings: Dict[str, str] = {}
    for part in side.parts:
        if part.get("kind") == "sprite" and part.get("bone") in lengths:
            for track in (str(part["name"]), f"{part['name']}~mirror"):
                part_bindings[track] = str(part["bone"])
    return BodyRigProduct(target=target, joints=[(name, None) for name in bones], attachments=attachments,
                          clips=clips, part_bindings=part_bindings, limbs=dict(_LIMBS))


def write_body_rig(target: str, rows, mirrored_name: str, side: RigDocument, excluded,
                   feet: Tuple[float, float], out_dir: Path) -> Path:
    return body_rig(target, rows, mirrored_name, side, excluded, feet).write(out_dir)
