"""The T-rex's semantic body rig, read from the SVG rig that draws him.

The joints are the bones of ``rigged/trex_enemy/trex_enemy_side.rig.json``, and
every clip frame is the same ``RigDocument.solve`` that draws the sheet row, so
a head in the rig is the head in the drawing: one pose table, not two.

Attachments are the named points the game reads: ``jaw``, where his jaws hold
a body (``ATTACHMENTS``).

Hurt parts are what you can hit: his head and jaw, neck, torso, the first three
tail bones and his legs. Each is MEASURED from the drawn part it covers (its
raster's opaque extent), not guessed. The arms (tiny) and the tail tip (a
whip's thinnest third) are left out; a box only errs toward hittable once the
game takes each part's axis-aligned bound.

Coordinates follow ``authoring.body_rig``: published sheet pixels, origin at
the published feet pixel, +x the way the art faces, +y down. The rig solves in
the DRAWN frame; ``frame_transform`` (``build_sheet``'s, drawn -> published:
padding added, auto-crop removed) carries it to the published one.
"""

from __future__ import annotations

import math
from typing import Dict, List, Mapping, Sequence, Tuple

from ...authoring.body_rig import BodyRigProduct, JointPose, RigShape, alpha_extent
from ...authoring.rigdoc import RigDocument

Point = Tuple[float, float]

#: hurt part name -> (the part whose art measures it, its joint, shape kind,
#: how much of the measured thickness counts). The shrink keeps a part's
#: soft edges (outline, spikes, a jaw's fangs) out of its hurt volume.
HURT_PARTS: Sequence[Tuple[str, str, str, str, float]] = (
    ("head", "head", "head", "rect", 0.85),
    ("jaw", "jaw", "jaw", "capsule", 0.8),
    ("neck", "neck", "neck", "capsule", 0.75),
    ("torso", "torso", "torso", "rect", 0.85),
    ("tail1", "tail1", "tail1", "capsule", 0.8),
    ("tail2", "tail2", "tail2", "capsule", 0.8),
    ("tail3", "tail3", "tail3", "capsule", 0.8),
    ("thigh_near", "near_thigh", "near_thigh", "capsule", 0.75),
    ("shin_near", "near_shin", "near_shin", "capsule", 0.75),
    ("thigh_far", "far_thigh", "far_thigh", "capsule", 0.75),
    ("shin_far", "far_shin", "far_shin", "capsule", 0.75),
)

#: attachment name -> (its joint, its place in the joint's frame, sheet pixels).
#:
#: ``jaw``: where his jaws hold a body. It is on the teeth line of his lower
#: jaw, near its front (the jaw bone runs from the hinge, 0, to the tip, about
#: 66). It rides the jaw joint, so a held body follows his mouth through the
#: reach, the thrash and the fling. The game reads this point
#: (``ambition.body.attachments``); it keeps no pixel of its own for it.
ATTACHMENTS: Sequence[Tuple[str, str, Point]] = (("jaw", "jaw", (60.0, -10.0)),)


def _rotate(p: Point, degrees: float) -> Point:
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def _joint_extent(doc: RigDocument, part: Mapping) -> Tuple[float, float, float, float] | None:
    """The part's opaque extent in its JOINT's frame (sheet pixels).

    A part is drawn rotated by ``bone.angle - part.rest_angle`` about its pivot
    at the bone's origin, so a raster point ``p`` is ``rotate(-part.rest_angle,
    p)`` in the joint's frame.
    """
    raster = doc.sprite_raster(part, 1.0)
    extent = None if raster is None else alpha_extent(raster.image, raster.pivot, 1.0)
    if extent is None:
        return None
    x0, y0, x1, y1 = extent
    rest = float(part.get("rest_angle", 0.0))
    corners = [_rotate(c, -rest) for c in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
    xs, ys = [c[0] for c in corners], [c[1] for c in corners]
    return (min(xs), min(ys), max(xs), max(ys))


def _shape(kind: str, extent: Tuple[float, float, float, float], keep: float) -> RigShape:
    x0, y0, x1, y1 = extent
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    if kind == "rect":
        return RigShape("rect", (cx, cy), half=((x1 - x0) / 2.0 * keep, (y1 - y0) / 2.0 * keep))
    # A capsule along the joint's +x (the bone): as long as the art, as thick
    # as `keep` of it.
    radius = (y1 - y0) / 2.0 * keep
    a = (min(x0 + radius, cx), cy)
    b = (max(x1 - radius, cx), cy)
    return RigShape("capsule", a, b=b, radius=radius)


def body_rig(
    doc: RigDocument,
    target: str,
    rows: Sequence[Tuple[str, int, int]],
    frame_transform: Mapping[str, float],
    feet_published: Point,
) -> BodyRigProduct:
    bones = [str(bone["name"]) for bone in doc.bones]
    parts = {str(part["name"]): part for part in doc.parts}
    dx, dy = float(frame_transform.get("dx", 0.0)), float(frame_transform.get("dy", 0.0))

    hurt: List[tuple] = []
    for name, part_name, joint, kind, keep in HURT_PARTS:
        part = parts.get(part_name)
        extent = None if part is None else _joint_extent(doc, part)
        if extent is None or joint not in bones:
            raise ValueError(f"{target}: hurt part {name!r} has no measurable art ({part_name!r} on {joint!r})")
        hurt.append((name, joint, _shape(kind, extent, keep)))

    clips: Dict[str, Tuple[bool, float, List[List[JointPose]]]] = {}
    for animation, frame_count, duration_ms in rows:
        frames: List[List[JointPose]] = []
        for index in range(int(frame_count)):
            world, _params = doc.solve(animation, doc.frame_time(animation, index, int(frame_count)))
            frames.append(
                [
                    JointPose(
                        translation=(
                            world[bone].origin[0] + dx - feet_published[0],
                            world[bone].origin[1] + dy - feet_published[1],
                        ),
                        rotation=math.radians(world[bone].angle),
                    )
                    for bone in bones
                ]
            )
        looping = bool((doc.clips.get(animation) or {}).get("loop", True))
        clips[animation] = (looping, float(duration_ms) / 1000.0, frames)

    return BodyRigProduct(
        target=target,
        joints=[(bone, None) for bone in bones],
        attachments=list(ATTACHMENTS),
        hurt_parts=hurt,
        clips=clips,
    )
