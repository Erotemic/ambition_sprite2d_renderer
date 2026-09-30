"""The semantic body-rig product: joints, attachments, hurt parts, sampled poses.

A body rig is a GAMEPLAY product. The game reads it to place hurt volumes and
attachment points (a hand that fires a projectile) on a body. It does not read
it to draw the body, so it holds no texture, no atlas rectangle, and no SVG or
Python concept.

Units and axes (the contract the Rust reader `BodyRigDefinition` expects):

- lengths are published sheet pixels, the same pixels as ``body_pixel_bbox``;
- the origin is the sheet's ``feet_pixel`` (the bottom centre of the body box);
- +x is the direction the art faces, +y is DOWN;
- a rotation is in radians, positive is clockwise on screen (the same sign as
  ``rigdoc`` degrees);
- a joint transform is LOCAL to its parent (a joint with no parent is local to
  the origin). A point ``p`` in a joint's frame is placed at
  ``translation + rotate(rotation, (scale_x * p.x, scale_y * p.y))``.

Clips are keyed by the sheet's own row names, so the game selects a rig clip
with the same vocabulary it uses to select a sheet row. Each clip has exactly
the frame count and frame duration of its row.

The product is independent of the render quality tier: it is written once, next
to the full-resolution sheet, and the quality-variant generator does not scale
it. Moving a quality setting must not move a hand or a hurt volume.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCHEMA_VERSION = 1

Point = Tuple[float, float]


@dataclass(frozen=True)
class JointPose:
    """One joint's transform in one frame, local to its parent."""

    translation: Point
    rotation: float = 0.0
    scale: Point = (1.0, 1.0)


@dataclass(frozen=True)
class RigShape:
    """A simple hurt shape in its joint's frame.

    ``kind`` is ``circle`` (``a`` = centre), ``capsule`` (segment ``a``-``b``)
    or ``rect`` (``a`` = centre, ``half`` = half extents).
    """

    kind: str
    a: Point
    b: Point = (0.0, 0.0)
    radius: float = 0.0
    half: Point = (0.0, 0.0)


@dataclass
class BodyRigProduct:
    target: str
    joints: List[Tuple[str, Optional[str]]]
    attachments: List[Tuple[str, str, Point]] = field(default_factory=list)
    hurt_parts: List[Tuple[str, str, RigShape]] = field(default_factory=list)
    #: row name -> (looping, frame duration in seconds, frames); a frame holds
    #: one ``JointPose`` per joint, in ``joints`` order.
    clips: Dict[str, Tuple[bool, float, List[List[JointPose]]]] = field(default_factory=dict)

    def validate(self) -> None:
        names = [name for name, _parent in self.joints]
        if len(set(names)) != len(names):
            raise ValueError(f"{self.target}: duplicate joint names in {names}")
        known = set(names)
        for name, parent in self.joints:
            if parent is not None and parent not in known:
                raise ValueError(f"{self.target}: joint {name!r} names unknown parent {parent!r}")
        for name, joint, _offset in self.attachments:
            if joint not in known:
                raise ValueError(f"{self.target}: attachment {name!r} names unknown joint {joint!r}")
        for name, joint, _shape in self.hurt_parts:
            if joint not in known:
                raise ValueError(f"{self.target}: hurt part {name!r} names unknown joint {joint!r}")
        for clip, (_loop, duration, frames) in self.clips.items():
            if not frames:
                raise ValueError(f"{self.target}: clip {clip!r} has no frames")
            if not (duration > 0.0 and math.isfinite(duration)):
                raise ValueError(f"{self.target}: clip {clip!r} has frame duration {duration}")
            for index, frame in enumerate(frames):
                if len(frame) != len(self.joints):
                    raise ValueError(
                        f"{self.target}: clip {clip!r} frame {index} poses {len(frame)} "
                        f"joints, the rig has {len(self.joints)}"
                    )

    def to_ron(self) -> str:
        self.validate()
        out: List[str] = [
            "// Auto-emitted body rig. See `ambition_sprite2d_renderer.authoring.body_rig`.",
            "(",
            f"    schema_version: {SCHEMA_VERSION},",
            f"    target: {_s(self.target)},",
            "    joints: [",
        ]
        for name, parent in self.joints:
            parent_ron = "None" if parent is None else f"Some({_s(parent)})"
            out.append(f"        (name: {_s(name)}, parent: {parent_ron}),")
        out.append("    ],")
        out.append("    attachments: [")
        for name, joint, offset in self.attachments:
            out.append(f"        (name: {_s(name)}, joint: {_s(joint)}, offset: {_p(offset)}),")
        out.append("    ],")
        out.append("    hurt_parts: [")
        for name, joint, shape in self.hurt_parts:
            out.append(f"        (name: {_s(name)}, joint: {_s(joint)}, shape: {_shape(shape)}),")
        out.append("    ],")
        out.append("    clips: {")
        for clip in sorted(self.clips):
            looping, duration, frames = self.clips[clip]
            out.append(f"        {_s(clip)}: (")
            out.append(f"            looping: {'true' if looping else 'false'},")
            out.append(f"            frame_duration_s: {_f(duration)},")
            out.append("            frames: [")
            for frame in frames:
                poses = ", ".join(_pose(pose) for pose in frame)
                out.append(f"                [{poses}],")
            out.append("            ],")
            out.append("        ),")
        out.append("    },")
        out.append(")")
        return "\n".join(out) + "\n"

    def write(self, out_dir: Path) -> Path:
        path = Path(out_dir) / f"{self.target}_body_rig.ron"
        path.write_text(self.to_ron())
        return path


def _s(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _f(value: float) -> str:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"non-finite body-rig value {value}")
    text = f"{round(value, 5):.5f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def _p(point: Point) -> str:
    return f"({_f(point[0])}, {_f(point[1])})"


def _pose(pose: JointPose) -> str:
    return (
        f"(translation: {_p(pose.translation)}, rotation: {_f(pose.rotation)}, "
        f"scale: {_p(pose.scale)})"
    )


def _shape(shape: RigShape) -> str:
    if shape.kind == "circle":
        return f"Circle(center: {_p(shape.a)}, radius: {_f(shape.radius)})"
    if shape.kind == "capsule":
        return f"Capsule(a: {_p(shape.a)}, b: {_p(shape.b)}, radius: {_f(shape.radius)})"
    if shape.kind == "rect":
        return f"Rect(center: {_p(shape.a)}, half_extents: {_p(shape.half)})"
    raise ValueError(f"unknown body-rig shape kind {shape.kind!r}")


def place(pose: JointPose, local: Point) -> Point:
    """``local`` in ``pose``'s frame, in its parent's frame."""
    x = pose.scale[0] * local[0]
    y = pose.scale[1] * local[1]
    c, s = math.cos(pose.rotation), math.sin(pose.rotation)
    return (pose.translation[0] + x * c - y * s, pose.translation[1] + x * s + y * c)


def alpha_extent(image, pivot: Point, scale: float) -> Optional[Tuple[float, float, float, float]]:
    """The drawn extent of one part raster, relative to its pivot.

    Returns ``(x0, y0, x1, y1)`` in units of ``1 / scale`` raster pixels, or
    ``None`` when the raster is empty. This is an offline measurement of
    authored art; the game never measures an image.
    """
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return None
    x0, y0, x1, y1 = bbox
    return (
        (x0 - pivot[0]) / scale,
        (y0 - pivot[1]) / scale,
        (x1 - pivot[0]) / scale,
        (y1 - pivot[1]) / scale,
    )


__all__ = [
    "BodyRigProduct",
    "JointPose",
    "RigShape",
    "SCHEMA_VERSION",
    "alpha_extent",
    "place",
]
