"""A 3D HAND: the one model the Dealer's Hand is drawn from (Jon,
2026-10-31: "a 3d model for reference? Like with the person characters").

As with the cast in the round, the 3D model only PLACES: it holds the
hand's fixed skeleton (knuckles, phalanx lengths, the thumb's root), poses
it by joint angles, and projects it for a view; the sprite's 2D parts draw
at the projected joints. Every view and pose comes from the same skeleton,
so each phalanx in one frame is the same physical piece in every other.

Hand frame (px, the frame's own units): ``u`` from the wrist along the
fingers, ``v`` across the hand (the index and thumb on its negative side),
``n`` out of the palm. A finger FLEXES about its own lateral axis toward
``n``; the thumb OPPOSES by swinging its axis from beside the index across
in front of the palm, and flexes toward the little finger.

The camera: the hand's ``u`` points along ``palm_deg`` on screen; ``roll``
turns it about ``u`` (0 the palm faces us, 180 its back does); the view is
pitched ``PITCH`` so depth reads (a curl toward us rises, away drops).

``reference_sheet`` renders the model itself, colour-coded digit by digit,
over poses x rolls: the turnaround to check a sprite against.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw

Vec = np.ndarray
Point = Tuple[float, float]

#: Each finger: its knuckle across the palm (v), its width, its three
#: phalanges. Index, middle, ring, little.
FINGERS = [(-9.0, 5.6, (16.0, 11.0, 8.0)), (-3.0, 5.8, (17.5, 12.0, 8.5)), (3.0, 5.4, (16.0, 11.0, 8.0)), (8.5, 4.8, (12.5, 9.0, 7.0))]
#: The thumb: its root (u, v, n), its metacarpal and two phalanges, width.
THUMB_ROOT = (5.0, -7.0, 1.5)
THUMB = (9.0, 10.0, 8.0)
THUMB_WIDTH = 6.2
PALM_LENGTH = 26.0
PALM_HALF_WIDTH = 9.0
#: How far each finger joint (knuckle, middle, end) bends at a full curl.
JOINT_BEND = (70.0, 95.0, 70.0)
#: The thumb's joints at a full curl (root, knuckle, end).
THUMB_BEND = (10.0, 35.0, 55.0)
#: The camera's pitch, degrees.
PITCH = 20.0


@dataclass(frozen=True)
class HandPose:
    """The joint angles: each finger's curl (0 straight, 1 closed, below 0
    bent back) and the thumb's (it opposes as it curls)."""

    curls: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    thumb: float = 0.0


@dataclass(frozen=True)
class Camera:
    wrist: Point
    palm_deg: float
    roll: float = 0.0
    #: Screen px per hand unit (1 in the sprite; larger for the reference).
    scale: float = 1.0

    def basis(self) -> Tuple[Vec, Vec, Vec]:
        """The hand's u, v, n in camera space (x right, y down, z toward us)."""
        a = math.radians(self.palm_deg)
        u = np.array([math.cos(a), math.sin(a), 0.0])
        perp = np.array([-math.sin(a), math.cos(a), 0.0])
        z = np.array([0.0, 0.0, 1.0])
        r = math.radians(self.roll)
        v = math.cos(r) * perp + math.sin(r) * z
        n = math.cos(r) * z - math.sin(r) * perp
        return u, v, n

    def to_camera(self, local: Vec) -> Vec:
        u, v, n = self.basis()
        p = local[0] * u + local[1] * v + local[2] * n
        b = math.radians(PITCH)
        return np.array([p[0], p[1] * math.cos(b) - p[2] * math.sin(b), p[1] * math.sin(b) + p[2] * math.cos(b)])

    def project(self, local: Sequence[float]) -> Point:
        p = self.to_camera(np.asarray(local, float))
        return (self.wrist[0] + p[0] * self.scale, self.wrist[1] + p[1] * self.scale)

    def depth(self, local: Sequence[float]) -> float:
        return float(self.to_camera(np.asarray(local, float))[2])

    def faces_us(self, local_dir: Sequence[float]) -> bool:
        """Whether a surface with this local normal faces the camera."""
        return self.depth(local_dir) - self.depth((0.0, 0.0, 0.0)) > 0.0


@dataclass(frozen=True)
class Digit:
    """One posed digit, in hand space: its joints (base to tip) and each
    phalanx's PAD normal (the palm side of that piece)."""

    joints: List[Vec]
    pads: List[Vec]
    width: float


def _unit(v: Vec) -> Vec:
    return v / (np.linalg.norm(v) or 1.0)


def _flex(start: Vec, axis: Vec, toward: Vec, bones, bends, curl: float, width: float) -> Digit:
    """A chain from ``start`` along ``axis``, each joint folding by
    bends x curl toward ``toward`` (perpendicular to ``axis``)."""
    joints, pads = [start], []
    theta = 0.0
    for bone, bend in zip(bones, bends):
        theta += math.radians(bend * curl)
        d = math.cos(theta) * axis + math.sin(theta) * toward
        joints.append(joints[-1] + bone * d)
        pads.append(math.cos(theta) * toward - math.sin(theta) * axis)
    return Digit(joints, pads, width)


def finger(pose: HandPose, k: int) -> Digit:
    across, width, bones = FINGERS[k]
    knuckle = np.array([PALM_LENGTH, across, 0.0])
    fan = math.radians(across * 1.2)
    axis = np.array([math.cos(fan), math.sin(fan), 0.0])
    return _flex(knuckle, axis, np.array([0.0, 0.0, 1.0]), bones, JOINT_BEND, pose.curls[k], width)


def thumb(pose: HandPose) -> Digit:
    """The thumb: open, it spreads off the index side, a little palmward;
    curling it swings its axis across in front of the palm toward the
    little finger (opposition) and folds its joints."""
    open_axis = _unit(np.array([math.cos(math.radians(58)), -math.sin(math.radians(58)), 0.3]))
    opposed = _unit(np.array([0.55, 0.45, 0.7]))
    t = max(0.0, min(1.0, pose.thumb))
    axis = _unit((1 - t) * open_axis + t * opposed)
    want = np.array([0.0, 1.0, 0.6])  # its pad faces across, toward the fingers
    toward = _unit(want - np.dot(want, axis) * axis)
    return _flex(np.array(THUMB_ROOT), axis, toward, THUMB, THUMB_BEND, pose.thumb, THUMB_WIDTH)


def digits(pose: HandPose) -> Dict[str, Digit]:
    out = {name: finger(pose, k) for k, name in enumerate(("index", "middle", "ring", "little"))}
    out["thumb"] = thumb(pose)
    return out


def thumb_web(pose: HandPose) -> List[Vec]:
    """The web of the thumb in hand space: its root, its knuckle, the index
    knuckle, the wrist (the thumb's mound, from the palm)."""
    t = thumb(pose)
    index = np.array([PALM_LENGTH, FINGERS[0][0], 0.0])
    return [t.joints[0], t.joints[1], (t.joints[1] + index) / 2, index, np.array([0.0, -PALM_HALF_WIDTH * 0.5, 0.0])]


def palm_outline() -> List[Vec]:
    """The palm plate's corners in hand space, heel to knuckles."""
    lo, hi = FINGERS[0][0] - 3.5, FINGERS[3][0] + 3.5
    return [np.array(p) for p in ((0.0, -PALM_HALF_WIDTH, 0.0), (PALM_LENGTH, lo, 0.0), (PALM_LENGTH, hi, 0.0), (0.0, PALM_HALF_WIDTH, 0.0))]


# --- the reference turnaround ------------------------------------------------------

DIGIT_COLOURS = {"index": (232, 92, 92), "middle": (92, 200, 110), "ring": (90, 130, 236), "little": (232, 200, 70), "thumb": (236, 140, 60)}
REFERENCE_POSES = {
    "open": HandPose((0.05,) * 4, 0.0),
    "grasp": HandPose((0.8, 0.85, 0.85, 0.9), 0.75),
    "fist": HandPose((1.0,) * 4, 0.9),
}


def _shade(colour, facing: float) -> Tuple[int, int, int, int]:
    k = 0.55 + 0.45 * max(0.0, facing)
    return (int(colour[0] * k), int(colour[1] * k), int(colour[2] * k), 255)


def render_model(pose: HandPose, cam: Camera, size: Tuple[int, int], scale: int = 4) -> Image.Image:
    """The bare model: the palm a plate (lighter on its palm side), each
    phalanx a capsule in its digit's colour (darker where its back faces
    us), joints dark pivots, a white dot on each pad side; painter's order
    by depth."""
    img = Image.new("RGBA", (size[0] * scale, size[1] * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    S = lambda p: (p[0] * scale, p[1] * scale)  # noqa: E731
    parts = []
    outline = palm_outline()
    palm_front = cam.faces_us((0.0, 0.0, 1.0))
    palm_col = (236, 226, 214) if palm_front else (170, 160, 150)
    parts.append((np.mean([cam.depth(p) for p in outline]), "palm", outline, palm_col))
    web = thumb_web(pose)
    parts.append((np.mean([cam.depth(p) for p in outline]) - 0.01, "palm", web, palm_col))
    for name, dg in digits(pose).items():
        for i in range(len(dg.joints) - 1):
            a, b = dg.joints[i], dg.joints[i + 1]
            facing = cam.depth(dg.pads[i]) - cam.depth((0, 0, 0))
            w = dg.width * (1.0 - 0.1 * i) * cam.scale
            parts.append(((cam.depth(a) + cam.depth(b)) / 2, "bone", (a, b, w, facing, i, name == "thumb"), DIGIT_COLOURS[name]))
    for depth, kind, data, colour in sorted(parts, key=lambda p: p[0]):
        if kind == "palm":
            d.polygon([S(cam.project(p)) for p in data], fill=colour + (255,), outline=(30, 24, 40, 255), width=scale)
            continue
        a, b, w, facing, i, is_thumb = data
        pa, pb = S(cam.project(a)), S(cam.project(b))
        for col, ww in (((30, 24, 40, 255), w + 1.2), (_shade(colour, facing), w)):
            r = ww * scale / 2
            d.line([pa, pb], fill=col, width=int(ww * scale))
            for p in (pa, pb):
                d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=col)
        r = 0.9 * scale * cam.scale
        d.ellipse((pa[0] - r, pa[1] - r, pa[0] + r, pa[1] + r), fill=(30, 24, 40, 255))
        if facing > 0.2:
            m = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            d.ellipse((m[0] - r, m[1] - r, m[0] + r, m[1] + r), fill=(255, 255, 255, 255))
    return img.resize(size, Image.Resampling.LANCZOS)


def reference_sheet(rolls: Sequence[float] = (0, 45, 90, 135, 180), cell: Tuple[int, int] = (240, 220), zoom: int = 1) -> Image.Image:
    """Poses (rows) x rolls (columns): the turnaround, each digit its own
    colour so a piece can be followed across every cell."""
    label_h = 18
    sheet = Image.new("RGBA", (cell[0] * zoom * len(rolls) + 70, (cell[1] * zoom + label_h) * len(REFERENCE_POSES) + label_h), (40, 34, 60, 255))
    d = ImageDraw.Draw(sheet)
    for c, roll in enumerate(rolls):
        d.text((70 + c * cell[0] * zoom + 6, 4), f"roll {roll:g}" + (" (palm)" if roll == 0 else " (back)" if roll == 180 else ""), fill=(230, 230, 240, 255))
    for r, (name, pose) in enumerate(REFERENCE_POSES.items()):
        y = label_h + r * (cell[1] * zoom + label_h)
        d.text((6, y + cell[1] * zoom // 2), name, fill=(230, 230, 240, 255))
        for c, roll in enumerate(rolls):
            cam = Camera((cell[0] * 0.3, cell[1] * 0.72), -40.0, float(roll), 2.6)
            im = render_model(pose, cam, cell).resize((cell[0] * zoom, cell[1] * zoom), Image.Resampling.LANCZOS)
            sheet.alpha_composite(im, (70 + c * cell[0] * zoom, y))
    return sheet
