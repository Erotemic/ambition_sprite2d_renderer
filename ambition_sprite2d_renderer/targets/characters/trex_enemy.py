"""Standalone generator for a big classic green T-rex enemy.

Design goals:
- unmistakably *bipedal* silhouette: two powerful hind legs and two tiny arms
- clear side-view read for a 2D side scroller
- big classic T-rex proportions: oversized head, deep torso, long balancing tail
- fun attack tells: bite, roar, tail swipe, stomp, charge

Only ``build_sheet`` is reused for PNG / YAML / RON emission.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet

from . import _solo_shape_rig as SR

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "trex_enemy"
FRAME_SIZE = (500, 380)
WORK_FRAME_SIZE = (1000, 760)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 120),
    ("walk", 8, 90),
    ("charge", 8, 76),
    ("bite", 7, 78),
    ("roar", 6, 104),
    ("tail_swipe", 7, 82),
    ("stomp", 6, 92),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_trex_enemy",
        "display_name": "T-Rex Enemy",
    },
    "body": {
        "body_plan": "BeastBiped",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "locomotion_hint": "HeavyWalk",
        "traits": ["enemy", "beast", "dinosaur", "heavy", "no_hands", "stomper"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "crawl": None,
            "fly": None,
            "swim": None,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {
            "talk": None,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "melee_brute_brute"},
    "actions": {"default_preset": "brute_lunge"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk_heavy": {"animation": "walk", "events": []},
        "action.special.charge": {
            "animation": "charge",
            "events": [
                {"t": 0.20, "event": "charge_commit", "source": "trex_enemy.charge"}
            ],
        },
        "action.melee.primary": {
            "animation": "bite",
            "events": [
                {
                    "t": 0.32,
                    "event": "hitbox_active_start",
                    "source": "trex_enemy.bite",
                },
                {"t": 0.55, "event": "hitbox_active_end", "source": "trex_enemy.bite"},
            ],
        },
        "action.melee.tail_sweep": {
            "animation": "tail_swipe",
            "events": [
                {
                    "t": 0.36,
                    "event": "hitbox_active_start",
                    "source": "trex_enemy.tail_swipe",
                },
                {
                    "t": 0.66,
                    "event": "hitbox_active_end",
                    "source": "trex_enemy.tail_swipe",
                },
            ],
        },
        "action.melee.stomp": {
            "animation": "stomp",
            "events": [
                {"t": 0.48, "event": "ground_impact", "source": "trex_enemy.stomp"}
            ],
        },
        "interaction.roar": {
            "animation": "roar",
            "events": [{"t": 0.44, "event": "sfx_cue", "source": "trex_enemy.roar"}],
        },
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "trex_enemy.geometry", "point": {"x": 296.0, "y": 82.0}},
        "mouth": {"source": "trex_enemy.geometry", "point": {"x": 346.0, "y": 108.0}},
        "roar_origin": {
            "source": "trex_enemy.geometry",
            "point": {"x": 360.0, "y": 110.0},
        },
        "tail_base": {
            "source": "trex_enemy.geometry",
            "point": {"x": 130.0, "y": 158.0},
        },
        "tail_tip": {"source": "trex_enemy.geometry", "point": {"x": 48.0, "y": 164.0}},
        "foot_l": {"source": "trex_enemy.geometry", "point": {"x": 180.0, "y": 286.0}},
        "foot_r": {"source": "trex_enemy.geometry", "point": {"x": 244.0, "y": 286.0}},
    },
    "tags": ["enemy", "heavy", "dinosaur"],
}

OUTLINE = (22, 16, 12, 255)
GREEN_DARK = (54, 109, 44, 255)
GREEN = (74, 148, 58, 255)
GREEN_LIGHT = (110, 185, 88, 255)
BELLY = (188, 172, 112, 255)
BELLY_SHADE = (146, 128, 84, 255)
MOUTH = (110, 46, 52, 255)
TONGUE = (182, 98, 106, 255)
TOOTH = (247, 242, 224, 255)
CLAW = (234, 228, 208, 255)
EYE = (238, 216, 96, 255)
PUPIL = (34, 22, 17, 255)
DUST = (135, 112, 76, 170)
FX = (255, 235, 164, 170)
ROAR = (230, 244, 255, 118)
SCAR = (192, 115, 88, 255)


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(p: Point) -> Tuple[int, int]:
    return (_s(p[0]), _s(p[1]))


def _box(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _rot(x: float, y: float, deg: float) -> Point:
    rad = math.radians(deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return (x * c - y * s, x * s + y * c)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _poly(
    draw: ImageDraw.ImageDraw,
    pts: Sequence[Point],
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    ipts = [_pt(p) for p in pts]
    draw.polygon(ipts, fill=fill)
    if outline and width > 0:
        draw.line(
            ipts + [ipts[0]], fill=outline, width=max(1, _s(width)), joint="curve"
        )


def _line(
    draw: ImageDraw.ImageDraw, pts: Sequence[Point], fill: RGBA, width: float = 1.0
) -> None:
    draw.line([_pt(p) for p in pts], fill=fill, width=max(1, _s(width)), joint="curve")


def _circle(
    draw: ImageDraw.ImageDraw,
    p: Point,
    r: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        (_s(p[0] - r), _s(p[1] - r), _s(p[0] + r), _s(p[1] + r)),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)),
    )


def _ellipse(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        _box(cx, cy, rx, ry), fill=fill, outline=outline, width=max(1, _s(width))
    )


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


class Pose:
    def __init__(self, anim: str, frame_idx: int, nframes: int) -> None:
        t = frame_idx / max(1, nframes - 1)
        cyc = math.tau * frame_idx / max(1, nframes)
        s = math.sin(cyc)
        c = math.cos(cyc)

        self.root_x = 0.0
        self.root_y = 0.0
        self.bob = 0.0
        self.body_tilt = 0.0
        self.neck = -6.0
        self.head = -6.0
        self.jaw = 8.0
        self.tail_base = -8.0
        self.tail_mid = -14.0
        self.tail_tip = -18.0
        self.near_leg = 0.0
        self.far_leg = 0.0
        self.near_knee = 0.0
        self.far_knee = 0.0
        self.near_lift = 0.0
        self.far_lift = 0.0
        self.near_arm = 0.0
        self.far_arm = 0.0
        self.near_reach = 0.0
        self.far_reach = 0.0
        self.bite_fx = 0.0
        self.roar = 0.0
        self.swipe = 0.0
        self.dust = 0.0
        self.dead_t = 0.0
        self.blink = False
        self.x_eye = False

        if anim == "idle":
            self.bob = s * 2.2
            self.body_tilt = s * 1.8
            self.neck = -6.0 + s * 1.8
            self.head = -5.0 + s * 1.5
            self.jaw = 7.0 + max(0.0, s) * 2.0
            self.near_leg = -4.0 + c * 2.0
            self.far_leg = 4.0 - c * 1.8
            self.tail_base = -10.0 + s * 4.0
            self.tail_mid = -16.0 + s * 6.0
            self.tail_tip = -20.0 + s * 8.0
            self.near_arm = -4.0 + s * 3.0
            self.far_arm = 3.0 - s * 2.5
            self.blink = frame_idx == nframes - 1
        elif anim == "walk":
            self.root_x = s * 2.6
            self.bob = abs(s) * 4.0 - 1.0
            self.body_tilt = s * 3.0
            self.neck = -7.0 - s * 1.2
            self.head = -6.0 - s * 1.8
            self.near_leg = -24.0 * s
            self.far_leg = 22.0 * s
            self.near_knee = 10.0 * max(0.0, -s)
            self.far_knee = 9.0 * max(0.0, s)
            self.near_lift = max(0.0, -s) * 10.0
            self.far_lift = max(0.0, s) * 8.0
            self.tail_base = -8.0 - s * 8.0
            self.tail_mid = -16.0 - s * 12.0
            self.tail_tip = -22.0 - s * 16.0
            self.near_arm = -8.0 * s
            self.far_arm = 6.0 * s
        elif anim == "charge":
            self.root_x = frame_idx * 3.0 + s * 1.0
            self.bob = abs(s) * 4.4 - 0.8
            self.body_tilt = -9.0 + s * 2.6
            self.neck = -16.0 - s * 3.5
            self.head = -13.0 - s * 4.0
            self.jaw = 8.0 + max(0.0, -s) * 5.0
            self.near_leg = -28.0 * s
            self.far_leg = 24.0 * s
            self.near_knee = 12.0 * max(0.0, -s)
            self.far_knee = 11.0 * max(0.0, s)
            self.near_lift = max(0.0, -s) * 10.0
            self.far_lift = max(0.0, s) * 8.0
            self.tail_base = -2.0 - s * 10.0
            self.tail_mid = -8.0 - s * 15.0
            self.tail_tip = -12.0 - s * 20.0
            self.near_arm = -12.0 * s
            self.far_arm = 10.0 * s
            self.dust = 0.45 + abs(s) * 0.55
        elif anim == "bite":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-8.0, 24.0, tt)
            self.bob = -hit * 3.4
            self.body_tilt = _lerp(-4.0, 10.0, tt)
            self.neck = _lerp(-12.0, 20.0, tt)
            self.head = _lerp(-16.0, 24.0, tt)
            self.jaw = 8.0 + hit * 34.0
            self.near_leg = _lerp(-6.0, 12.0, tt)
            self.far_leg = _lerp(4.0, -8.0, tt)
            self.tail_base = _lerp(-6.0, -20.0, tt)
            self.tail_mid = _lerp(-12.0, -30.0, tt)
            self.tail_tip = _lerp(-18.0, -38.0, tt)
            self.near_arm = _lerp(0.0, 8.0, tt)
            self.far_arm = _lerp(0.0, 6.0, tt)
            self.bite_fx = hit
        elif anim == "roar":
            tt = math.sin(t * math.pi)
            self.bob = -tt * 1.5
            self.body_tilt = -2.0
            self.neck = -28.0 * tt
            self.head = -32.0 * tt
            self.jaw = 16.0 + tt * 34.0
            self.near_leg = -5.0 * tt
            self.far_leg = 4.0 * tt
            self.tail_base = -8.0 + tt * 5.0
            self.tail_mid = -14.0 + tt * 7.0
            self.tail_tip = -18.0 + tt * 9.0
            self.roar = tt
        elif anim == "tail_swipe":
            tt = _ease(t)
            sweep = math.sin(tt * math.pi)
            self.root_x = _lerp(8.0, -10.0, tt)
            self.bob = -sweep * 2.0
            self.body_tilt = _lerp(8.0, -14.0, tt)
            self.neck = _lerp(8.0, -16.0, tt)
            self.head = _lerp(4.0, -10.0, tt)
            self.near_leg = _lerp(5.0, -8.0, tt)
            self.far_leg = _lerp(-8.0, 12.0, tt)
            self.tail_base = _lerp(26.0, -34.0, tt)
            self.tail_mid = _lerp(44.0, -58.0, tt)
            self.tail_tip = _lerp(62.0, -84.0, tt)
            self.near_arm = _lerp(-4.0, 8.0, tt)
            self.swipe = sweep
        elif anim == "stomp":
            tt = _ease(t)
            slam = math.sin(tt * math.pi)
            self.root_x = _lerp(-4.0, 8.0, tt)
            self.bob = -slam * 7.0
            self.body_tilt = _lerp(-8.0, 14.0, tt)
            self.neck = _lerp(-10.0, 10.0, tt)
            self.head = _lerp(-8.0, 8.0, tt)
            self.jaw = 8.0 + slam * 8.0
            self.near_leg = _lerp(-24.0, 24.0, tt)
            self.far_leg = _lerp(10.0, -8.0, tt)
            self.near_knee = 16.0 * (1.0 - tt)
            self.near_lift = (1.0 - tt) * 24.0
            self.tail_base = _lerp(-12.0, -4.0, tt)
            self.tail_mid = _lerp(-18.0, -8.0, tt)
            self.tail_tip = _lerp(-24.0, -12.0, tt)
            self.dust = max(0.0, tt - 0.4) * 1.9
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
            self.root_x = -hit * 8.0 + shake * 3.0
            self.bob = -hit * 2.0
            self.body_tilt = -10.0 * hit
            self.neck = 12.0 * hit
            self.head = 18.0 * hit
            self.jaw = 14.0 * hit
            self.near_leg = -6.0 * hit
            self.far_leg = 5.0 * hit
            self.tail_base = 8.0 * hit
            self.tail_mid = 12.0 * hit
            self.tail_tip = 18.0 * hit
            self.near_arm = 10.0 * hit
        elif anim == "death":
            tt = _ease(t)
            self.dead_t = tt
            self.root_x = -tt * 28.0
            self.root_y = tt * 8.0
            self.bob = -tt * 7.0
            self.body_tilt = 84.0 * tt
            self.neck = -20.0 * tt
            self.head = -14.0 * tt
            self.jaw = 18.0 + tt * 10.0
            self.near_leg = -16.0 * tt
            self.far_leg = 20.0 * tt
            self.tail_base = -10.0 - 24.0 * tt
            self.tail_mid = -18.0 - 38.0 * tt
            self.tail_tip = -24.0 - 50.0 * tt
            self.near_arm = -8.0 * tt
            self.far_arm = 4.0 * tt
            self.x_eye = tt > 0.58


def _S(p: Point) -> Point:
    """A work-space point in supersampled canvas pixels, unrounded."""
    return (p[0] * SUPER, p[1] * SUPER)


def _heading(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _local_piece(key, extent: Tuple[float, float, float, float], paint) -> Tuple[Image.Image, Point]:
    """A piece painted in its own work-space frame: ``paint(draw, origin)``
    draws with the piece's pivot at ``origin`` (work units) on a canvas that
    covers ``extent`` = (left, top, right, bottom) around the pivot."""
    left, top, right, bottom = extent
    origin = (left + 2.0, top + 2.0)
    size = (_s(left + right + 4.0), _s(top + bottom + 4.0))
    return SR.rest_piece(key, size, _S(origin), lambda d: paint(d, origin))


def _bar(length: float, width: float, color: RGBA, stripe: float):
    """A limb bone along +x: a flat-ended band ``width`` wide with a thin
    outline stripe down its middle (the old polyline, one bone of it)."""

    def paint(d, o) -> None:
        _line(d, [o, (o[0] + length, o[1])], color, width)
        _line(d, [o, (o[0] + length, o[1])], OUTLINE, stripe)

    half = width / 2.0 + 1.0
    return _local_piece(("trex_bar", length, width, color, stripe), (half, half, length + half, half), paint)


def _place_bone(img: Image.Image, a: Point, b: Point, length: float, width: float, color: RGBA, stripe: float, name: str) -> None:
    """A limb bone of a FIXED ``length`` from ``a`` toward ``b``: one raster
    for every pose."""
    SR.place(img, _bar(length, width, color, stripe), _S(a), _heading(a, b), name)


def _ik_joint(root: Point, target: Point, length: float, bend: Point) -> Tuple[Point, Point]:
    """The joint and the reached end of a two-bone limb with both bones
    ``length`` long. A target out of reach is pulled in along its direction
    (the limb straightens; it does not stretch)."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = math.hypot(dx, dy)
    reach = 2.0 * length * 0.999
    if d > reach:
        target = (root[0] + dx / d * reach, root[1] + dy / d * reach)
    joint, _seg = SR.two_bone(root, target, length, bend)
    return joint, target


def _taper(length: float, w0: float, w1: float, fill: RGBA, outline_w: float, stripe: Optional[RGBA] = None, stripe_w: float = 0.0, outline: RGBA = OUTLINE):
    """A tapered segment along +x, round at both ends: its outline only
    (``fill`` None) grown by ``outline_w``, or its fill (with an optional
    centre stripe)."""
    grow = outline_w if fill is None else 0.0
    r0, r1 = w0 / 2.0 + grow, w1 / 2.0 + grow
    ink = outline if fill is None else fill

    def paint(d, o) -> None:
        x, y = o
        d.polygon([_pt((x, y - r0)), _pt((x + length, y - r1)), _pt((x + length, y + r1)), _pt((x, y + r0))], fill=ink)
        d.ellipse(_box(x, y, r0, r0), fill=ink)
        d.ellipse(_box(x + length, y, r1, r1), fill=ink)
        if stripe is not None:
            _line(d, [(x, y), (x + length, y)], stripe, stripe_w)

    r = max(r0, r1) + 1.0
    return _local_piece(("trex_taper", length, w0, w1, fill, outline_w, stripe, stripe_w), (r, r, length + r, r), paint)


# The tail's three segments: widths at each joint (the old polygon's spread).
TAIL_WIDTHS = (28.0, 32.0, 22.0, 10.0)
# Where the old painter put the tail's joints (body frame, about the hip) and
# how far each was turned by the pose (Pose.tail_base / tail_mid / tail_tip).
TAIL_REST = ((-36.0, -40.0), (-112.0, -82.0), (-214.0, -92.0), (-322.0, -70.0))
# Each segment's FIXED length: its length at the default pose (a chain of
# rigid bones, one raster each, instead of a length a frame).
TAIL_REST_TURN = (0.0, -8.0, -14.0, -18.0)


def _tail_rest_length(i: int) -> float:
    a = _rot(*TAIL_REST[i], TAIL_REST_TURN[i])
    b = _rot(*TAIL_REST[i + 1], TAIL_REST_TURN[i + 1])
    return float(round(math.hypot(b[0] - a[0], b[1] - a[1])))


TAIL_LENGTHS = tuple(_tail_rest_length(i) for i in range(3))


def _tail_joints(P, pose: "Pose") -> List[Point]:
    """The tail as a chain of fixed bones: each bone points where the old
    painter's segment pointed."""
    old = [P(*TAIL_REST[0]), P(*TAIL_REST[1], pose.tail_base), P(*TAIL_REST[2], pose.tail_mid), P(*TAIL_REST[3], pose.tail_tip)]
    joints = [old[0]]
    for i in range(3):
        h = math.radians(_heading(old[i], old[i + 1]))
        a = joints[-1]
        joints.append((a[0] + TAIL_LENGTHS[i] * math.cos(h), a[1] + TAIL_LENGTHS[i] * math.sin(h)))
    return joints


def _draw_tail(img: Image.Image, joints: Sequence[Point]) -> None:
    """The tail as three tapered bones, every outline first and then every
    fill, so the joints read as one silhouette."""
    segs = [(joints[i], _heading(joints[i], joints[i + 1]), TAIL_LENGTHS[i], TAIL_WIDTHS[i], TAIL_WIDTHS[i + 1]) for i in range(3)]
    for i, (a, deg, length, w0, w1) in enumerate(segs):
        SR.place(img, _taper(length, w0, w1, None, 1.4), _S(a), deg, f"tail{i}_line")
    for i, (a, deg, length, w0, w1) in enumerate(segs):
        SR.place(img, _taper(length, w0, w1, GREEN_DARK, 0.0, GREEN_LIGHT, 2.0), _S(a), deg, f"tail{i}")


def _foot_piece(scale: float, front: bool):
    foot_len = 42 * scale

    def paint(d, ankle) -> None:
        foot = [
            (ankle[0] - 8 * scale, ankle[1] - 5 * scale),
            (ankle[0] + foot_len * 0.52, ankle[1] - 7 * scale),
            (ankle[0] + foot_len, ankle[1] + 3 * scale),
            (ankle[0] + foot_len * 0.62, ankle[1] + 10 * scale),
            (ankle[0] - 6 * scale, ankle[1] + 8 * scale),
        ]
        _poly(d, foot, GREEN_LIGHT if front else GREEN, OUTLINE, 1.0)
        for frac in [0.52, 0.76, 0.96]:
            tip = (ankle[0] + foot_len * frac, ankle[1] + 5 * scale)
            _poly(d, [tip, (tip[0] + 6 * scale, tip[1] - 2 * scale), (tip[0] + 3 * scale, tip[1] + 5 * scale)], CLAW, OUTLINE, 0.4)

    return _local_piece(("trex_foot", scale, front), (12 * scale, 10 * scale, foot_len + 10 * scale, 14 * scale), paint)


#: Thigh and shin share one length (one raster per leg).
LEG_BONE = 71.0


def _draw_hind_leg(img: Image.Image, hip: Point, thigh_deg: float, knee_bend: float, foot_lift: float, *, scale: float, front: bool, side: str) -> Point:
    """Thigh and shin (two bones of one fixed length reaching the foot the old
    painter placed), knee and foot: pieces placed along the leg."""
    thigh_len = 68 * scale
    shin_len = 74 * scale
    knee0 = (hip[0] + thigh_len * math.cos(math.radians(thigh_deg)), hip[1] + thigh_len * math.sin(math.radians(thigh_deg)))
    shin_deg = thigh_deg + knee_bend
    target = (knee0[0] + shin_len * math.cos(math.radians(shin_deg)), knee0[1] + shin_len * math.sin(math.radians(shin_deg)) - foot_lift)
    bone = LEG_BONE * scale
    knee, ankle = _ik_joint(hip, target, bone, (1.0, 0.0))
    col = GREEN if front else GREEN_DARK
    w = 16 * scale if front else 13 * scale
    _place_bone(img, hip, knee, bone, w, col, 1.5, f"{side}_thigh")
    _place_bone(img, knee, ankle, bone, w, col, 1.5, f"{side}_shin")
    r = 7.0 * scale
    knee_part = _local_piece(("trex_knee", scale, front), (r + 1, r + 1, r + 1, r + 1), lambda d, o: _circle(d, o, r, GREEN_LIGHT if front else GREEN, OUTLINE, 0.8))
    SR.place(img, knee_part, _S(knee), 0.0, f"{side}_knee")
    SR.place(img, _foot_piece(scale, front), _S(ankle), 0.0, f"{side}_foot")
    return ankle


def _claws_piece(front: bool):
    def paint(d, hand) -> None:
        for i in range(2):
            claw = (hand[0] + 4 + i * 2.8, hand[1] + 2 + i * 1.5)
            _poly(d, [hand, (claw[0] + 5, claw[1] - 1), (claw[0] + 3, claw[1] + 4)], CLAW, OUTLINE, 0.35)

    return _local_piece(("trex_claws", front), (2.0, 2.0, 16.0, 10.0), paint)


def _draw_tiny_arm(img: Image.Image, shoulder: Point, ang: float, *, front: bool, side: str) -> Point:
    """Upper arm and forearm: bones of one length (one raster per arm)."""
    bone = 17.0 if front else 16.0
    elbow = (shoulder[0] + bone * math.cos(math.radians(ang)), shoulder[1] + bone * math.sin(math.radians(ang)))
    hand = (elbow[0] + bone * math.cos(math.radians(ang + 14)), elbow[1] + bone * math.sin(math.radians(ang + 14)))
    col = GREEN_LIGHT if front else GREEN_DARK
    w = 6.8 if front else 5.2
    _place_bone(img, shoulder, elbow, bone, w, col, 1.0, f"{side}_upper_arm")
    _place_bone(img, elbow, hand, bone, w, col, 1.0, f"{side}_forearm")
    SR.place(img, _claws_piece(front), _S(hand), 0.0, f"{side}_claws")
    return hand


def _paint_torso(d, root: Point) -> None:
    """Torso, belly, back bumps and scars, unturned, the hip at ``root``."""

    def P(x: float, y: float) -> Point:
        return (root[0] + x, root[1] + y)

    torso = [P(-44, -96), P(34, -132), P(138, -128), P(210, -96), P(226, -44), P(182, -6), P(96, 14), P(6, 8), P(-40, -18)]
    _poly(d, torso, GREEN, OUTLINE, 1.8)
    belly = [P(6, -74), P(100, -76), P(180, -48), P(172, -4), P(84, 16), P(8, -4), P(-10, -30)]
    _poly(d, belly, BELLY, OUTLINE, 1.1)
    _line(d, [P(-6, -82), P(64, -116), P(148, -112)], GREEN_LIGHT, 2.2)
    _line(d, [P(12, -52), P(82, -42), P(162, -24)], BELLY_SHADE, 1.7)
    # Subtle back bumps, not fantasy spikes
    for bx, by, h in [(-12, -104, 12), (24, -120, 15), (70, -126, 16), (120, -122, 15), (168, -108, 11)]:
        a = P(bx, by)
        _poly(d, [(a[0] - 7, a[1] + 4), (a[0] + 4, a[1] - h), (a[0] + 12, a[1] + 2)], GREEN_LIGHT, OUTLINE, 0.6)
    # Battle wear
    _line(d, [P(62, -84), P(78, -72), P(88, -92)], SCAR, 1.3)
    _line(d, [P(104, -58), P(116, -46)], SCAR, 1.1)


# The neck: a tapered band from its base on the torso to the head's root,
# its belly strip on the throat side. One FIXED length: the neck turns at its
# base and carries the head; it does not stretch.
NECK_W = (46.0, 32.0)
NECK_BELLY_W = (28.0, 20.0)
NECK_BELLY_OFFSET = 10.0
NECK_BASE = (166.0, -67.0)
NECK_TOP = (228.0, -134.0)
NECK_LENGTH = round(math.hypot(NECK_TOP[0] - 4.0 - NECK_BASE[0], NECK_TOP[1] + 1.0 - NECK_BASE[1]))


def _neck_piece(length: float):
    w0, w1 = NECK_W
    b0, b1 = NECK_BELLY_W
    off = NECK_BELLY_OFFSET

    def paint(d, o) -> None:
        x, y = o
        _poly(d, [(x, y - w0 / 2), (x + length, y - w1 / 2), (x + length, y + w1 / 2), (x, y + w0 / 2)], GREEN, OUTLINE, 1.2)
        _poly(d, [(x, y + off - b0 / 2), (x + length, y + off - b1 / 2), (x + length + 6, y + off + b1 / 2), (x, y + off + b0 / 2)], BELLY, OUTLINE, 0.9)

    r = max(w0 / 2, off + b0 / 2) + 2.0
    return _local_piece(("trex_neck", length), (r, r, length + 10.0, r), paint)


# -- the head: a base, a hinged lower jaw and an eye overlay ------------------
#
# The head is three rasters for every pose: the BASE (skull, upper jaw, its
# pale lip, upper teeth, nostril, brow), the LOWER JAW (jaw, tongue, lower
# teeth) turned about its hinge by the jaw's opening, and the mouth's dark
# INSIDE. The inside is two pieces that a closed mouth hides: a dark copy of
# the lower jaw that turns with the head (behind the jaw), and a dark copy of
# the upper jaw that turns with the lower jaw (behind the base). An open jaw
# shows them in the gap. The eye (open, shut or crossed out) is a small
# overlay placed on the base.

JAW_HINGE = (4.0, 2.0)
#: How far the head's pivot is from the neck's end.
HEAD_REACH = 12.0
#: Degrees the lower jaw turns per unit of ``Pose.jaw`` (the old painter's
#: jaw value, which moved the jaw's front down about a fifth of a unit).
JAW_DEG_PER_UNIT = 0.2
JAW_CLOSED = 6.0
UPPER_JAW = ((-4, -26), (40, -38), (104, -34), (154, -20), (188, -3), (176, 7), (126, 4), (58, 0), (10, -6))
LOWER_JAW = ((2, 10), (48, 18), (118, 24), (172, 18), (188, 9), (134, 4), (62, 2), (8, 4))
EYE_AT = (40.0, -18.0)
HEAD_EXTENT = (36.0, 52.0, 198.0, 36.0)


def _paint_head_base(d, o: Point) -> None:
    def H(x: float, y: float) -> Point:
        return (o[0] + x, o[1] + y)

    skull = [H(-26, -22), H(-6, -40), H(34, -44), H(54, -30), H(22, -8), H(-18, -4)]
    _poly(d, skull, GREEN_LIGHT, OUTLINE, 1.2)
    _poly(d, [H(*p) for p in UPPER_JAW], GREEN, OUTLINE, 1.3)
    # The pale lip along the upper jaw's lower edge.
    _poly(d, [H(14, -4), H(58, -4), H(126, 0), H(170, 3), H(176, 7), H(126, 4), H(58, 0), H(10, -2)], BELLY, OUTLINE, 0.6)
    for tx in [32, 54, 78, 102, 126, 148, 166]:
        _poly(d, [H(tx, 1), H(tx + 5, 10), H(tx + 10, 2)], TOOTH, OUTLINE, 0.4)
    _line(d, [H(28, -24), H(46, -30)], OUTLINE, 1.1)
    _line(d, [H(126, -12), H(132, -11)], OUTLINE, 0.8)


def _paint_lower_jaw(d, o: Point) -> None:
    def H(x: float, y: float) -> Point:
        return (o[0] + x, o[1] + y)

    # The dark inside of the upper jaw: hidden behind the base until the jaw opens.
    _poly(d, [H(*p) for p in UPPER_JAW[4:] + UPPER_JAW[:1]], MOUTH, None, 0.0)
    _poly(d, [H(*p) for p in LOWER_JAW], GREEN_LIGHT, OUTLINE, 1.1)
    _line(d, [H(12, 11), H(48, 16), H(118, 21), H(166, 16)], BELLY, 2.4)
    _poly(d, [H(18, 3), H(62, 6), H(132, 7), H(162, 8), H(118, 14), H(56, 11)], MOUTH, OUTLINE, 0.6)
    _poly(d, [H(70, 8), H(116, 9), H(92, 15)], TONGUE, OUTLINE, 0.5)
    for tx in [40, 72, 104, 138]:
        _poly(d, [H(tx, 9), H(tx + 5, 1), H(tx + 10, 9)], TOOTH, OUTLINE, 0.4)


def _paint_mouth_floor(d, o: Point) -> None:
    _poly(d, [(o[0] + x, o[1] + y) for x, y in LOWER_JAW], MOUTH, None, 0.0)


def _paint_eye(d, o: Point, state: str) -> None:
    x, y = o
    if state == "x":
        _line(d, [(x - 6, y - 4), (x + 6, y + 4)], OUTLINE, 1.0)
        _line(d, [(x - 6, y + 4), (x + 6, y - 4)], OUTLINE, 1.0)
    elif state == "shut":
        _line(d, [(x - 6, y), (x + 6, y)], OUTLINE, 1.0)
    else:
        _ellipse(d, x, y, 6.0, 5.0, EYE, OUTLINE, 0.7)
        _circle(d, (x + 1.5, y + 0.5), 1.5, PUPIL, PUPIL, 0.1)


def _draw_head(img: Image.Image, pivot: Point, degrees: float, pose: "Pose") -> None:
    def H(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, degrees)
        return (pivot[0] + rx, pivot[1] + ry)

    hinge = H(*JAW_HINGE)
    jaw_deg = max(0.0, pose.jaw - JAW_CLOSED) * JAW_DEG_PER_UNIT
    rel = (-JAW_HINGE[0], -JAW_HINGE[1])
    floor = _local_piece(("trex_mouth_floor",), HEAD_EXTENT, _paint_mouth_floor)
    jaw = _local_piece(("trex_lower_jaw",), (HEAD_EXTENT[0] - rel[0], HEAD_EXTENT[1] - rel[1], HEAD_EXTENT[2] + rel[0], HEAD_EXTENT[3] + rel[1]), lambda d, o: _paint_lower_jaw(d, (o[0] + rel[0], o[1] + rel[1])))
    base = _local_piece(("trex_head_base",), HEAD_EXTENT, _paint_head_base)
    if jaw_deg > 0.25:
        SR.place(img, floor, _S(pivot), degrees, "mouth_floor")
    SR.place(img, jaw, _S(hinge), degrees + jaw_deg, "lower_jaw")
    SR.place(img, base, _S(pivot), degrees, "head")
    state = "x" if pose.x_eye else ("shut" if pose.blink else "open")
    eye = _local_piece(("trex_eye", state), (8.0, 7.0, 8.0, 7.0), lambda d, o: _paint_eye(d, o, state))
    SR.place(img, eye, _S(H(*EYE_AT)), degrees, "eye")


# -- effects: pieces painted once, placed with their strength as opacity ------


def _arc_piece(key: str, box: Tuple[float, float, float, float], start: float, end: float, color: RGBA, width: float):
    """An arc of the ellipse ``box`` (work units about the piece's origin)."""
    l, t, r, b = box
    pad = width + 2.0

    def paint(d, o) -> None:
        d.arc((_s(o[0] + l), _s(o[1] + t), _s(o[0] + r), _s(o[1] + b)), start, end, fill=color, width=_s(width))

    return _local_piece(("trex_arc", key), (pad - l, pad - t, r + pad, b + pad), paint)


def _dust_piece():
    def paint(d, o) -> None:
        x, y = o
        _poly(d, [(x - 9, y), (x, y - 12), (x + 10, y - 1), (x + 3, y + 7)], DUST, (95, 78, 54, 110), 0.4)

    return _local_piece(("trex_dust",), (11.0, 14.0, 12.0, 9.0), paint)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    """The T-rex as a rig: every piece is painted once and turned into place.
    The tail, neck and limbs are bones of fixed length; the head is a base, a
    hinged lower jaw and an eye overlay; the attack effects are pieces placed
    with their strength as opacity."""
    img = Image.new("RGBA", (WORK_FRAME_SIZE[0] * SUPER, WORK_FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    pose = Pose(anim, frame_idx, nframes)

    root = (
        WORK_FRAME_SIZE[0] * 0.4426 + pose.root_x,
        WORK_FRAME_SIZE[1] * 0.6063 + pose.root_y + pose.bob,
    )
    body_angle = pose.body_tilt

    def P(x: float, y: float, extra: float = 0.0) -> Point:
        rx, ry = _rot(x, y, body_angle + extra)
        return (root[0] + rx, root[1] + ry)

    # Tail first, big and classic
    tail = _tail_joints(P, pose)
    _draw_tail(img, tail)

    # Far hind leg (still only one of the two biped legs)
    _draw_hind_leg(img, P(-10, -4), 90 + pose.far_leg, 34 + pose.far_knee, pose.far_lift, scale=0.92, front=False, side="far")

    # Main torso: one piece turned by the body's tilt about the hip.
    torso = _local_piece(("trex_torso",), (52.0, 150.0, 236.0, 26.0), _paint_torso)
    SR.place(img, torso, _S(root), body_angle, "torso")

    # Far tiny arm
    _draw_tiny_arm(img, P(126, -70), 128 + pose.far_arm, front=False, side="far")

    # Neck: one fixed bone from its base on the torso, pointed where the old
    # painter's neck top was; it carries the head.
    neck_top = P(*NECK_TOP, pose.neck)
    base = P(*NECK_BASE)
    heading = _heading(base, (neck_top[0] - 4.0, neck_top[1] + 1.0))
    SR.place(img, _neck_piece(NECK_LENGTH), _S(base), heading, "neck")
    end = (base[0] + NECK_LENGTH * math.cos(math.radians(heading)) + 4.0, base[1] + NECK_LENGTH * math.sin(math.radians(heading)) - 1.0)
    # The head sits ON the neck's end (the old painter left a gap there).
    head_pivot = (
        end[0] + HEAD_REACH * math.cos(math.radians(body_angle + pose.neck - 16)),
        end[1] + HEAD_REACH * math.sin(math.radians(body_angle + pose.neck - 16)),
    )
    head_ang = body_angle + pose.neck + pose.head - 6
    _draw_head(img, head_pivot, head_ang, pose)

    def H(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, head_ang)
        return (head_pivot[0] + rx, head_pivot[1] + ry)

    # Near tiny arm
    _draw_tiny_arm(img, P(136, -62), 124 + pose.near_arm, front=True, side="near")

    # Near hind leg (second and last leg)
    near_ankle = _draw_hind_leg(img, P(34, -2), 92 + pose.near_leg, 38 + pose.near_knee, pose.near_lift, scale=1.0, front=True, side="near")

    # Attack FX: each a piece, its strength the draw's opacity.
    if anim == "bite" and pose.bite_fx > 0.15:
        SR.place(img, _arc_piece("bite", (-66, -40, 52, 48), 210, 350, FX, 5.4), _S(H(162, 6)), head_ang, "bite_fx", min(1.0, 0.4 + pose.bite_fx))
    if anim == "roar" and pose.roar > 0.15:
        for i in range(3):
            rad = 32.0 + i * 22.0
            push = pose.roar * 8.0
            SR.place(img, _arc_piece(f"roar{i}", (-rad, -rad * 0.66, rad, rad * 0.66), 300, 30, ROAR, 2.0), _S(H(176 + push, 10)), head_ang, f"roar{i}", min(1.0, 0.3 + pose.roar))
    if anim == "tail_swipe" and pose.swipe > 0.12:
        SR.place(img, _arc_piece("swipe", (-76, -56, 46, 52), 100, 252, FX, 4.2), _S(tail[3]), 0.0, "swipe_fx", min(1.0, 0.3 + pose.swipe))
    if anim in {"charge", "stomp"} and pose.dust > 0.1:
        for i, dx in enumerate([-34, -10, 16, 42]):
            at = (near_ankle[0] + dx, near_ankle[1] + 10 + (i % 2) * 2)
            SR.place(img, _dust_piece(), _S(at), 0.0, f"dust{i}", min(1.0, pose.dust * (1.0 - i * 0.08)))
    if anim == "stomp" and pose.dust > 0.1:
        SR.place(img, _arc_piece("stomp", (-78, -14, 88, 32), 190, 350, FX, 3.8), _S(near_ankle), 0.0, "stomp_fx", min(1.0, pose.dust))

    return _downsample(img)


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda anim, frame_idx, nframes: _render_frame(
            anim, frame_idx, nframes
        ),
        out_dir=out_dir,
        frame_size=opts.get("frame_size", FRAME_SIZE),
        crop_margin=10,
        auto_crop=True,
        actor_metadata=ACTOR_METADATA,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, _render_frame, outputs, frame_transform, Path(out_dir))
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ] + list(parts.values())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the standalone big classic T-rex enemy spritesheet."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME,
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
