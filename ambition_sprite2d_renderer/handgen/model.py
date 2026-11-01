"""The 3D hand: one skeleton (``HandSpec``), posed by joint angles
(``HandPose``), seen by a ``Camera``.

The model only PLACES: it gives the joints and which face of each piece
looks at us; ``draw`` paints the 2D parts there. Every pose and view of one
spec is the same hand, so a phalanx in one frame is the same physical piece
in every other.

Hand space (in the spec's units, frame px at ``Camera.scale`` 1): ``u`` from
the wrist along the fingers, ``v`` across the hand (a right hand's index and
thumb on its negative side), ``n`` out of the palm. A finger FLEXES about
its own lateral axis toward ``n``; the thumb OPPOSES by swinging its axis
from beside the index across in front of the palm, flexing toward the
little finger. A LEFT hand is the right one mirrored across ``v``.

The camera: ``u`` points along ``palm_deg`` on screen (0 right, negative
up); ``roll`` turns the hand about ``u`` (0 its palm faces us, 180 its
back); the view is pitched ``pitch`` degrees so depth reads (a fold toward
us rises on screen, away from us drops).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Dict, List, Sequence, Tuple

import numpy as np

Vec = np.ndarray
Point = Tuple[float, float]

FINGER_NAMES = ("index", "middle", "ring", "little")
DIGIT_NAMES = FINGER_NAMES + ("thumb",)


@dataclass(frozen=True)
class FingerSpec:
    name: str
    #: The knuckle's place across the palm (v).
    across: float
    width: float
    #: The three phalanges, knuckle to tip.
    bones: Tuple[float, float, float]


@dataclass(frozen=True)
class HandSpec:
    """The skeleton and proportions: fixed for a character, every pose and
    view drawn from it."""

    fingers: Tuple[FingerSpec, ...] = (
        FingerSpec("index", -9.0, 5.6, (16.0, 11.0, 8.0)),
        FingerSpec("middle", -3.0, 5.8, (17.5, 12.0, 8.5)),
        FingerSpec("ring", 3.0, 5.4, (16.0, 11.0, 8.0)),
        FingerSpec("little", 8.5, 4.8, (12.5, 9.0, 7.0)),
    )
    #: The thumb's root (u, v, n), its metacarpal and two phalanges.
    thumb_root: Tuple[float, float, float] = (5.0, -7.0, 1.5)
    thumb_bones: Tuple[float, float, float] = (9.0, 10.0, 8.0)
    thumb_width: float = 6.2
    #: How far the thumb spreads off the fingers when open (degrees).
    thumb_spread: float = 58.0
    palm_length: float = 26.0
    palm_half_width: float = 9.0
    #: The palm's thickness (n), and how much its back domes across the
    #: knuckles (the metacarpal arch).
    palm_depth: float = 6.0
    palm_arch: float = 1.5
    #: How far each finger joint (knuckle, middle, end) bends at a full
    #: curl, and the thumb's (root, knuckle, end).
    #: A full curl lands the fingertips on the palm's face (a fist).
    joint_bend: Tuple[float, float, float] = (90.0, 100.0, 60.0)
    thumb_bend: Tuple[float, float, float] = (10.0, 35.0, 55.0)
    #: How much the fingers fan out from the middle (degrees per unit of v).
    fan: float = 1.2
    handedness: str = "right"

    def scaled(self, length: float = 1.0, width: float = 1.0) -> "HandSpec":
        """The same hand longer/shorter (``length``) and thicker/thinner
        (``width``)."""
        fingers = tuple(replace(f, across=f.across * width, width=f.width * width, bones=tuple(b * length for b in f.bones)) for f in self.fingers)
        r = self.thumb_root
        return replace(self, fingers=fingers, thumb_root=(r[0] * length, r[1] * width, r[2] * width), thumb_bones=tuple(b * length for b in self.thumb_bones),
                       thumb_width=self.thumb_width * width, palm_length=self.palm_length * length, palm_half_width=self.palm_half_width * width,
                       palm_depth=self.palm_depth * width, palm_arch=self.palm_arch * width)

    def mirrored(self) -> "HandSpec":
        return replace(self, handedness="left" if self.handedness == "right" else "right")

    def finger(self, name: str) -> FingerSpec:
        return next(f for f in self.fingers if f.name == name)


#: Named proportions.
SPECS: Dict[str, HandSpec] = {
    "default": HandSpec(),
    "slender": HandSpec().scaled(1.12, 0.82),
    "broad": HandSpec().scaled(0.92, 1.22),
    "stubby": HandSpec().scaled(0.78, 1.1),
}


@dataclass(frozen=True)
class HandPose:
    """The joint angles. ``curls`` per finger (0 straight, 1 closed, below 0
    bent back), ``thumb`` (it opposes as it curls), ``spread`` (0 natural,
    1 splayed, below 0 together), ``hook`` (0 even, 1 the bend moved into
    the end joints: a claw)."""

    curls: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    thumb: float = 0.0
    spread: float = 0.0
    hook: float = 0.0

    def curl(self, name: str) -> float:
        return self.curls[FINGER_NAMES.index(name)]


@dataclass(frozen=True)
class Camera:
    #: Where the wrist is on screen (frame px).
    wrist: Point
    palm_deg: float = 0.0
    roll: float = 0.0
    #: Screen px per hand unit.
    scale: float = 1.0
    pitch: float = 20.0

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

    def to_camera(self, local: Sequence[float]) -> Vec:
        u, v, n = self.basis()
        p = local[0] * u + local[1] * v + local[2] * n
        b = math.radians(self.pitch)
        return np.array([p[0], p[1] * math.cos(b) - p[2] * math.sin(b), p[1] * math.sin(b) + p[2] * math.cos(b)])

    def project(self, local: Sequence[float]) -> Point:
        p = self.to_camera(np.asarray(local, float))
        return (self.wrist[0] + p[0] * self.scale, self.wrist[1] + p[1] * self.scale)

    def depth(self, local: Sequence[float]) -> float:
        return float(self.to_camera(np.asarray(local, float))[2])

    def faces_us(self, local_dir: Sequence[float]) -> bool:
        """Whether a surface with this hand-space normal faces the camera."""
        return self.depth(local_dir) > 0.0

    def palm_faces_us(self) -> bool:
        return self.faces_us((0.0, 0.0, 1.0))


@dataclass(frozen=True)
class Digit:
    """One posed digit in hand space: its joints (base to tip), each
    phalanx's PAD normal (the palm side of that piece), its widths."""

    name: str
    joints: List[Vec]
    pads: List[Vec]
    widths: List[float]


def _unit(v: Vec) -> Vec:
    return v / (np.linalg.norm(v) or 1.0)


def _flex(name: str, start: Vec, axis: Vec, toward: Vec, bones, bends, width: float) -> Digit:
    """A chain from ``start`` along ``axis``, joint i folding ``bends[i]``
    degrees toward ``toward`` (perpendicular to ``axis``)."""
    joints, pads = [start], []
    theta = 0.0
    for bone, bend in zip(bones, bends):
        theta += math.radians(bend)
        d = math.cos(theta) * axis + math.sin(theta) * toward
        joints.append(joints[-1] + bone * d)
        pads.append(math.cos(theta) * toward - math.sin(theta) * axis)
    return Digit(name, joints, pads, [width * (1.0 - 0.1 * i) for i in range(len(bones))])


def _mirror(spec: HandSpec, p: Vec) -> Vec:
    return p * np.array([1.0, -1.0, 1.0]) if spec.handedness == "left" else p


#: How a full ``hook`` moves the bend between the joints.
_HOOK = (-0.8, 0.3, 0.6)


def finger(spec: HandSpec, pose: HandPose, name: str) -> Digit:
    f = spec.finger(name)
    curl = pose.curl(name)
    knuckle = np.array([spec.palm_length, f.across, 0.0])
    fan = math.radians(f.across * spec.fan * (1.0 + 1.6 * pose.spread))
    axis = np.array([math.cos(fan), math.sin(fan), 0.0])
    bends = [b * curl * (1.0 + pose.hook * h) if curl >= 0 else b * curl * (0.5 if i else 1.0) for i, (b, h) in enumerate(zip(spec.joint_bend, _HOOK))]
    d = _flex(name, knuckle, axis, np.array([0.0, 0.0, 1.0]), f.bones, bends, f.width)
    return Digit(name, [_mirror(spec, j) for j in d.joints], [_mirror(spec, p) for p in d.pads], d.widths)


def thumb(spec: HandSpec, pose: HandPose) -> Digit:
    """The thumb: open, it spreads off the index side, a little palmward;
    curling swings its axis across in front of the palm toward the little
    finger (opposition) and folds its joints."""
    spread = math.radians(spec.thumb_spread * (1.0 + 0.3 * pose.spread))
    open_axis = _unit(np.array([math.cos(spread), -math.sin(spread), 0.3]))
    opposed = _unit(np.array([0.55, 0.45, 0.7]))
    t = max(0.0, min(1.0, pose.thumb))
    axis = _unit((1 - t) * open_axis + t * opposed)
    want = np.array([0.0, 1.0, 0.6])  # its pad faces across, toward the fingers
    toward = _unit(want - np.dot(want, axis) * axis)
    d = _flex("thumb", np.array(spec.thumb_root), axis, toward, spec.thumb_bones, [b * pose.thumb for b in spec.thumb_bend], spec.thumb_width)
    return Digit("thumb", [_mirror(spec, j) for j in d.joints], [_mirror(spec, p) for p in d.pads], d.widths)


def digits(spec: HandSpec, pose: HandPose) -> Dict[str, Digit]:
    out = {name: finger(spec, pose, name) for name in FINGER_NAMES}
    out["thumb"] = thumb(spec, pose)
    return out


def _outline_uv(spec: HandSpec) -> Tuple[List[Tuple[float, float]], int, int]:
    """The palm's rounded outline in (u, v), right-handed: up the index
    side past the thumb's mound, along the knuckle edge (a little beyond
    each knuckle, dipping between them), down the little finger's bulging
    edge, round the heel. Returns it and the knuckle edge's first and last
    index."""
    h, length = spec.palm_half_width, spec.palm_length
    fs = spec.fingers
    lo, hi = fs[0].across - 3.0, fs[-1].across + 3.0
    pts = [(1.0, -0.95 * h), (length * 0.3, -h - 1.2), (length * 0.62, lo - 0.4), (length - 1.5, lo)]
    first = len(pts) - 1
    for k, f in enumerate(fs):
        pts.append((length + 2.2, f.across))
        if k + 1 < len(fs):
            pts.append((length + 1.2, (f.across + fs[k + 1].across) / 2))
    pts.append((length - 1.5, hi))
    last = len(pts) - 1
    pts += [(length * 0.62, hi + 0.3), (length * 0.3, 0.5 * (h + hi) + 1.0), (1.0, 0.95 * h), (-1.5, 0.5 * h), (-2.2, 0.0), (-1.5, -0.5 * h)]
    return pts, first, last


def palm_face(spec: HandSpec, front: bool) -> List[Vec]:
    """The palm's outline on its FRONT (palm) face or its back, in hand
    space; the back domes over the metacarpals."""
    pts, _, _ = _outline_uv(spec)
    half = spec.palm_depth / 2
    out = []
    for u, v in pts:
        if front:
            n = half
        else:
            w = max(0.0, 1.0 - (v / (spec.palm_half_width + 3.0)) ** 2)
            n = -half - spec.palm_arch * w * min(1.0, max(0.0, u / spec.palm_length) * 1.5)
        out.append(_mirror(spec, np.array([u, v, n])))
    return out


def knuckle_edge(spec: HandSpec, front: bool) -> List[Vec]:
    """The knuckle edge of a face, index side to little."""
    _, first, last = _outline_uv(spec)
    return palm_face(spec, front)[first:last + 1]


def palm_outline(spec: HandSpec) -> List[Vec]:
    """The palm's outline at its middle depth (n 0)."""
    return [_mirror(spec, np.array([u, v, 0.0])) for u, v in _outline_uv(spec)[0]]


def face_depth(spec: HandSpec, cam: "Camera") -> float:
    """The n of the palm face the camera sees."""
    return spec.palm_depth / 2 if cam.palm_faces_us() else -spec.palm_depth / 2


def thumb_web(spec: HandSpec, pose: HandPose) -> List[Vec]:
    """The web of the thumb in hand space: its root, its knuckle, the index
    knuckle, the wrist (the thumb's mound, from the palm)."""
    t = thumb(spec, pose)
    index = _mirror(spec, np.array([spec.palm_length, spec.fingers[0].across, 0.0]))
    return [t.joints[0], t.joints[1], (t.joints[1] + index) / 2, index, _mirror(spec, np.array([spec.palm_length * 0.3, -spec.palm_half_width, spec.thumb_root[2]]))]


def local(spec: HandSpec, u: float, v: float, n: float = 0.0) -> Vec:
    """A hand-space point given in RIGHT-hand terms (mirrored for a left)."""
    return _mirror(spec, np.array([u, v, n], float))


def landmarks(spec: HandSpec, pose: HandPose, cam: Camera) -> Dict[str, Point]:
    """Named screen points for attaching things: ``wrist``, ``palm``
    (centre), ``grip`` (where a held item sits), and per digit
    ``<name>_<i>`` for each joint (0 its base) and ``<name>_tip``."""
    out = {"wrist": cam.project((0.0, 0.0, 0.0)), "palm": cam.project(local(spec, spec.palm_length * 0.55, 0.0))}
    ds = digits(spec, pose)
    for name, d in ds.items():
        for i, j in enumerate(d.joints):
            out[f"{name}_{i}"] = cam.project(j)
        out[f"{name}_tip"] = cam.project(d.joints[-1])
    # The grip: inside the curled fingers, a little off the palm.
    mids = [ds[n].joints[1] for n in FINGER_NAMES]
    grip = np.mean(mids, axis=0) + np.array([0.0, 0.0, 5.0])
    out["grip"] = cam.project(grip)
    return out
