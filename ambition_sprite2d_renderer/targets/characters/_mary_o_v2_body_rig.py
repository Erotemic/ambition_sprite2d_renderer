"""Mary-O's semantic body rig, read from the SVG rig that draws her.

The joints are the bones of the SIDE projection of ``assets/mary_o_v2.svg``,
and every clip frame is solved by the same ``RigDocument`` and the same
``_pose_values`` that draw the sheet row. So a hand in the rig is the hand in the
drawing: there is one pose table, not a second copy of it.

Only side-view rows are published. Death is a FRONT projection and stays visual
only; the transition clips (grow, shrink, transform) composite effects over
other forms and are not poses of this body.

Attachments come from the authored ``Rig Joints`` tip markers (hands and toes)
and from the head part's own extent. Hurt parts are deliberately few: a head,
a torso and two legs. The arms are not hurt geometry, so this rig does not make
her easier to hit than her body box does.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Mapping, Optional

from ...authoring.body_rig import BodyRigProduct, JointPose, RigShape, alpha_extent
from ._mary_o_v2_model import OUTPUT_RESOLUTION_SCALE, FormSpec, form_collision_box, poses_for_form
from ._mary_o_v2_svg_poc import _find_part_records, _pose_values, build_rig_document

#: Rows this rig does not publish, and why: see the module docstring.
_VISUAL_ONLY_ROWS = frozenset({"death", "grow", "shrink", "big_shrink", "transform"})

#: Tip marker per limb bone -> the attachment it publishes.
_LIMB_ATTACHMENTS = {
    "near_arm": "hand_near",
    "far_arm": "hand_far",
    "near_leg": "foot_near",
    "far_leg": "foot_far",
}

#: A leg capsule's radius, as a fraction of the leg art's width.
_LEG_RADIUS_FRACTION = 0.35
#: The head circle's radius, as a fraction of the head art's smaller side. The
#: head art includes the cap brim and the ponytail, which are not the head.
_HEAD_RADIUS_FRACTION = 0.4


def _tip_local(record: Mapping) -> Optional[tuple[float, float]]:
    """A limb's tip in its bone frame, in authored units.

    ``authored_angle`` is 0 = down, +90 = screen east (see ``_find_part_records``).
    """
    angle = record.get("authored_angle")
    length = record.get("authored_length")
    if angle is None or length is None:
        return None
    radians = math.radians(float(angle))
    return (float(length) * math.sin(radians), float(length) * math.cos(radians))


def body_rig_for_form(svg_path: Path, form: FormSpec) -> BodyRigProduct:
    doc = build_rig_document(svg_path, form, "side")
    records = {r["bone"]: r for r in _find_part_records(svg_path, form, "side")}
    scale = float(OUTPUT_RESOLUTION_SCALE)
    box = form_collision_box(form)
    # `solve` places bones in frame coordinates. The product is relative to the
    # sheet's feet pixel, the bottom centre of the body box, which is not the
    # frame centre: the box has an authored x offset.
    feet = (box["x"] + box["w"] / 2.0, float(box["y"] + box["h"]))

    bones = [str(bone["name"]) for bone in doc.bones]
    joints = [(name, None) for name in bones]

    attachments: List[tuple] = []
    for bone, attachment in _LIMB_ATTACHMENTS.items():
        record = records.get(bone)
        tip = None if record is None else _tip_local(record)
        if tip is not None:
            attachments.append((attachment, bone, (tip[0] * scale, tip[1] * scale)))

    parts = {str(part["name"]): part for part in doc.parts}
    extents: Dict[str, tuple] = {}
    for name in ("head", "torso", "near_leg", "far_leg"):
        part = parts.get(name)
        raster = None if part is None else doc.sprite_raster(part, scale)
        extent = None if raster is None else alpha_extent(raster.image, raster.pivot, 1.0)
        if extent is not None:
            extents[name] = extent

    hurt_parts: List[tuple] = []
    if "head" in extents:
        x0, y0, x1, y1 = extents["head"]
        radius = _HEAD_RADIUS_FRACTION * min(x1 - x0, y1 - y0)
        # The face is the leading edge of the head art; the ponytail trails
        # behind it and widens the extent. So the circle touches the leading
        # edge instead of sitting at the middle of the extent.
        center = (x1 - radius, (y0 + y1) / 2.0)
        attachments.append(("head", "head", center))
        hurt_parts.append(("head", "head", RigShape("circle", center, radius=radius)))
    if "torso" in extents:
        x0, y0, x1, y1 = extents["torso"]
        hurt_parts.append(
            (
                "torso",
                "torso",
                RigShape(
                    "rect",
                    ((x0 + x1) / 2.0, (y0 + y1) / 2.0),
                    half=((x1 - x0) / 2.0, (y1 - y0) / 2.0),
                ),
            )
        )
    for bone, name in (("near_leg", "leg_near"), ("far_leg", "leg_far")):
        record = records.get(bone)
        tip = None if record is None else _tip_local(record)
        if tip is None or bone not in extents:
            continue
        x0, _y0, x1, _y1 = extents[bone]
        hurt_parts.append(
            (
                name,
                bone,
                RigShape(
                    "capsule",
                    (0.0, 0.0),
                    b=(tip[0] * scale, tip[1] * scale),
                    radius=_LEG_RADIUS_FRACTION * (x1 - x0),
                ),
            )
        )

    authored = doc.data.get("maryo_authored_angles") or {}
    lengths = doc.data.get("maryo_authored_lengths") or {}
    poses = poses_for_form(form)
    clips: Dict[str, tuple] = {}
    for animation, frame_count, duration_ms in form.rows:
        if animation in _VISUAL_ONLY_ROWS or animation not in poses:
            continue
        pose_list = poses[animation]
        frames: List[List[JointPose]] = []
        for index in range(int(frame_count)):
            pose = pose_list[index % len(pose_list)]
            values = _pose_values(form, pose, authored, lengths)
            clip_name = "__body_rig_pose__"
            doc.data["clips"][clip_name] = {
                "loop": False,
                "frames": 1,
                "duration_ms": 1,
                "channels": {name: {"const": value} for name, value in values.items()},
            }
            world, params = doc.solve(clip_name, 0.0)
            joint_poses = []
            for name in bones:
                bone_world = world[name]
                flip = float(params.get(f"bone.{name}.flip_x", 0.0)) >= 0.5
                joint_poses.append(
                    JointPose(
                        translation=(
                            bone_world.origin[0] * scale - feet[0],
                            bone_world.origin[1] * scale - feet[1],
                        ),
                        rotation=math.radians(bone_world.angle),
                        scale=(
                            -1.0 if flip else 1.0,
                            float(params.get(f"bone.{name}.scale_y", 1.0)),
                        ),
                    )
                )
            frames.append(joint_poses)
        doc.data["clips"].pop("__body_rig_pose__", None)
        looping = animation in {"idle", "walk", "climb", "swim", "crouch_walk"}
        clips[animation] = (looping, float(duration_ms) / 1000.0, frames)

    return BodyRigProduct(
        target=form.target_name,
        joints=joints,
        attachments=attachments,
        hurt_parts=hurt_parts,
        clips=clips,
    )


def write_body_rig(svg_path: Path, form: FormSpec, out_dir: Path) -> Path:
    return body_rig_for_form(svg_path, form).write(out_dir)
