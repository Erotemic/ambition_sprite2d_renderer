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
from ambition_sprite2d_renderer.core.draw import blending_draw

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


def _place_bar(img: Image.Image, a: Point, b: Point, width: float, color: RGBA, stripe: float, name: str, step: Optional[float] = None) -> None:
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    if step:
        length = max(step, round(length / step) * step)
    SR.place(img, _bar(round(length, 3), width, color, stripe), _S(a), _heading(a, b), name)


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
TAIL_STEP = 3.0


def _draw_tail(img: Image.Image, joints: Sequence[Point]) -> None:
    """The tail as three tapered segments, every outline first and then every
    fill, so the joints read as one silhouette."""
    segs = []
    for i in range(3):
        a, b = joints[i], joints[i + 1]
        length = max(TAIL_STEP, round(math.hypot(b[0] - a[0], b[1] - a[1]) / TAIL_STEP) * TAIL_STEP)
        segs.append((a, _heading(a, b), length, TAIL_WIDTHS[i], TAIL_WIDTHS[i + 1]))
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


def _draw_hind_leg(img: Image.Image, hip: Point, thigh_deg: float, knee_bend: float, foot_lift: float, *, scale: float, front: bool, side: str) -> Point:
    """Thigh (a fixed bone), shin (stretched by the foot lift, in steps), knee
    and foot: pieces placed along the old leg."""
    thigh_len = 68 * scale
    shin_len = 74 * scale
    knee = (hip[0] + thigh_len * math.cos(math.radians(thigh_deg)), hip[1] + thigh_len * math.sin(math.radians(thigh_deg)))
    shin_deg = thigh_deg + knee_bend
    ankle = (knee[0] + shin_len * math.cos(math.radians(shin_deg)), knee[1] + shin_len * math.sin(math.radians(shin_deg)) - foot_lift)
    col = GREEN if front else GREEN_DARK
    w = 16 * scale if front else 13 * scale
    _place_bar(img, hip, knee, w, col, 1.5, f"{side}_thigh")
    _place_bar(img, knee, ankle, w, col, 1.5, f"{side}_shin", step=2.0)
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


def _draw_tiny_arm(img: Image.Image, shoulder: Point, ang: float, reach: float, *, front: bool, side: str) -> Point:
    upper = 18 if front else 16
    lower = 16 + reach
    elbow = (shoulder[0] + upper * math.cos(math.radians(ang)), shoulder[1] + upper * math.sin(math.radians(ang)))
    hand = (elbow[0] + lower * math.cos(math.radians(ang + 14)), elbow[1] + lower * math.sin(math.radians(ang + 14)))
    col = GREEN_LIGHT if front else GREEN_DARK
    w = 6.8 if front else 5.2
    _place_bar(img, shoulder, elbow, w, col, 1.0, f"{side}_upper_arm")
    _place_bar(img, elbow, hand, w, col, 1.0, f"{side}_forearm")
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
# its belly strip on the throat side.
NECK_W = (46.0, 32.0)
NECK_BELLY_W = (28.0, 20.0)
NECK_BELLY_OFFSET = 10.0
NECK_STEP = 3.0


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


def _paint_head(d, pivot: Point, jaw: float, x_eye: bool, blink: bool) -> None:
    """The head unturned, its pivot at ``pivot``, the jaw open ``jaw``."""

    def H(x: float, y: float) -> Point:
        return (pivot[0] + x, pivot[1] + y)

    skull = [H(-26, -22), H(-6, -40), H(34, -44), H(54, -30), H(22, -8), H(-18, -4)]
    upper_jaw = [H(-4, -26), H(40, -38), H(104, -34), H(154, -20), H(188, -3), H(176, 7), H(126, 4), H(58, 0), H(10, -6)]
    lower_jaw = [
        H(2, 10),
        H(48, 18),
        H(118, 24 + jaw * 0.20),
        H(172, 18 + jaw * 0.18),
        H(188, 9 + jaw * 0.14),
        H(134, 4 + jaw * 0.18),
        H(62, 2),
        H(8, 4),
    ]
    _poly(d, skull, GREEN_LIGHT, OUTLINE, 1.2)
    _poly(d, upper_jaw, GREEN, OUTLINE, 1.3)
    _poly(d, lower_jaw, GREEN_LIGHT, OUTLINE, 1.1)
    snout_belly = [H(24, -2), H(90, 2), H(164, 8), H(172, 14), H(114, 16), H(48, 12), H(12, 8)]
    _poly(d, snout_belly, BELLY, OUTLINE, 0.8)
    # Mouth interior and teeth
    _poly(d, [H(18, 3), H(62, 8), H(132, 14 + jaw * 0.10), H(162, 10 + jaw * 0.10), H(118, 24 + jaw * 0.11), H(56, 18)], MOUTH, OUTLINE, 0.6)
    _poly(d, [H(70, 16), H(116, 20 + jaw * 0.10), H(92, 30 + jaw * 0.11)], TONGUE, OUTLINE, 0.5)
    for tx in [32, 54, 78, 102, 126, 148, 166]:
        _poly(d, [H(tx, 2), H(tx + 5, 10), H(tx + 10, 2)], TOOTH, OUTLINE, 0.4)
    for tx in [40, 72, 104, 138]:
        _poly(d, [H(tx, 15 + jaw * 0.09), H(tx + 5, 7 + jaw * 0.06), H(tx + 10, 15 + jaw * 0.09)], TOOTH, OUTLINE, 0.4)
    eye = H(40, -18)
    _line(d, [H(28, -24), H(46, -30)], OUTLINE, 1.1)
    if x_eye:
        _line(d, [H(34, -22), H(46, -14)], OUTLINE, 1.0)
        _line(d, [H(34, -14), H(46, -22)], OUTLINE, 1.0)
    elif blink:
        _line(d, [H(34, -18), H(46, -18)], OUTLINE, 1.0)
    else:
        _ellipse(d, eye[0], eye[1], 6.0, 5.0, EYE, OUTLINE, 0.7)
        _circle(d, (eye[0] + 1.5, eye[1] + 0.5), 1.5, PUPIL, PUPIL, 0.1)
    nostril = H(128, -12)
    _line(d, [(nostril[0] - _s(2), nostril[1]), (nostril[0] + _s(4), nostril[1] + _s(1))], OUTLINE, 0.8)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    """The T-rex as a rig: torso, neck, head (per jaw step and eye state), tail
    segments and limb bones are pieces painted once and turned into place;
    the attack effects stay shapes."""
    img = Image.new("RGBA", (WORK_FRAME_SIZE[0] * SUPER, WORK_FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    draw = blending_draw(img)
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
    tail0 = P(-36, -40)
    tail1 = P(-112, -82, pose.tail_base)
    tail2 = P(-214, -92, pose.tail_mid)
    tail3 = P(-322, -70, pose.tail_tip)
    _draw_tail(img, [tail0, tail1, tail2, tail3])

    # Far hind leg (still only one of the two biped legs)
    _draw_hind_leg(img, P(-10, -4), 90 + pose.far_leg, 34 + pose.far_knee, pose.far_lift, scale=0.92, front=False, side="far")

    # Main torso: one piece turned by the body's tilt about the hip.
    torso = _local_piece(("trex_torso",), (52.0, 150.0, 236.0, 26.0), _paint_torso)
    SR.place(img, torso, _S(root), body_angle, "torso")

    # Far tiny arm
    _draw_tiny_arm(img, P(126, -70), 128 + pose.far_arm, pose.far_reach, front=False, side="far")

    # Neck: from its base on the torso to the head's root.
    neck_top = P(228, -134, pose.neck)
    base = P(166, -67)
    top = (neck_top[0] - 4.0, neck_top[1] + 1.0)
    length = max(NECK_STEP, round(math.hypot(top[0] - base[0], top[1] - base[1]) / NECK_STEP) * NECK_STEP)
    SR.place(img, _neck_piece(length), _S(base), _heading(base, top), "neck")

    head_pivot = (
        neck_top[0] + 28 * math.cos(math.radians(body_angle + pose.neck - 16)),
        neck_top[1] + 28 * math.sin(math.radians(body_angle + pose.neck - 16)),
    )
    head_ang = body_angle + pose.neck + pose.head - 6
    jaw = SR.q(pose.jaw, 4.0)
    head = _local_piece(("trex_head", jaw, pose.x_eye, pose.blink), (36.0, 52.0, 198.0, 36.0), lambda d, o: _paint_head(d, o, jaw, pose.x_eye, pose.blink))
    SR.place(img, head, _S(head_pivot), head_ang, "head")

    def H(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, head_ang)
        return (head_pivot[0] + rx, head_pivot[1] + ry)

    # Near tiny arm
    _draw_tiny_arm(img, P(136, -62), 124 + pose.near_arm, pose.near_reach, front=True, side="near")

    # Near hind leg (second and last leg)
    near_ankle = _draw_hind_leg(img, P(34, -2), 92 + pose.near_leg, 38 + pose.near_knee, pose.near_lift, scale=1.0, front=True, side="near")

    # Attack FX
    if anim == "bite" and pose.bite_fx > 0.15:
        cx, cy = H(162, 6)
        box = (_s(cx - 66), _s(cy - 40), _s(cx + 52), _s(cy + 48))
        draw.arc(box, 210, 350, fill=FX, width=_s(4.8 + pose.bite_fx))
    if anim == "roar" and pose.roar > 0.15:
        for i in range(3):
            rad = 28 + i * 22 + pose.roar * 8
            cx, cy = H(176, 10)
            box = (_s(cx - rad), _s(cy - rad * 0.66), _s(cx + rad), _s(cy + rad * 0.66))
            draw.arc(box, 300, 30, fill=ROAR, width=_s(2.0))
    if anim == "tail_swipe" and pose.swipe > 0.12:
        tx, ty = tail3
        box = (_s(tx - 76), _s(ty - 56), _s(tx + 46), _s(ty + 52))
        draw.arc(box, 100, 252, fill=FX, width=_s(4.2))
    if anim in {"charge", "stomp"} and pose.dust > 0.1:
        for i, dx in enumerate([-34, -10, 16, 42]):
            base = (near_ankle[0] + dx, near_ankle[1] + 10 + (i % 2) * 2)
            scale = pose.dust * (1.0 - i * 0.08)
            _poly(
                draw,
                [
                    (base[0] - 9 * scale, base[1]),
                    (base[0], base[1] - 12 * scale),
                    (base[0] + 10 * scale, base[1] - 1 * scale),
                    (base[0] + 3 * scale, base[1] + 7 * scale),
                ],
                DUST,
                (95, 78, 54, 110),
                0.4,
            )
    if anim == "stomp" and pose.dust > 0.1:
        sx, sy = near_ankle
        box = (_s(sx - 78), _s(sy - 14), _s(sx + 88), _s(sy + 32))
        draw.arc(box, 190, 350, fill=FX, width=_s(3.8))

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
