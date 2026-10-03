"""Standalone generator for a crouched skulking ghoul enemy.

Visual inspiration:
- hunched, creeping humanoid silhouette
- long hooked nose and moustache tendrils
- simple cap / hood flap
- loincloth and bony limbs
- clawing hands and bent stalking legs

This is intentionally *not* a pirate. It is a creepy dark-lord-adjacent minion /
wretch enemy with a sneaky, crouched stance suitable for a side scroller or
arena enemy roster.

Only ``build_sheet`` is reused for spritesheet / YAML / RON emission.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw
from . import _ghoul_skulker_rig
from . import _solo_shape_rig as _rig

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "ghoul_skulker"
# Files the tack-on installer copies into the sandbox sprites dir.
# Names match what `build_sheet` writes (target_spritesheet.{png,yaml,ron}).
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]
FRAME_SIZE = (320, 320)
WORK_FRAME_SIZE = (640, 640)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("skulk", 8, 95),
    ("claw", 7, 82),
    ("pounce", 6, 78),
    ("cackle", 6, 108),
    ("hurt", 4, 90),
    ("death", 8, 112),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_ghoul_skulker",
        "display_name": "Ghoul Skulker",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "LowProfile",
        "mass_class": "Light",
        "locomotion_hint": "Skulk",
        "traits": ["enemy", "undead", "skulker", "clawed", "low_profile"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": {
                "height_px": None,
                "distance_px": None,
                "source": "ghoul_pounce_animation",
            },
            "climb": None,
            "crawl": True,
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
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "striker_swipe"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.skulk": {"animation": "skulk", "events": []},
        "action.melee.primary": {
            "animation": "claw",
            "events": [
                {
                    "t": 0.34,
                    "event": "hitbox_active_start",
                    "source": "ghoul_skulker.claw",
                },
                {
                    "t": 0.58,
                    "event": "hitbox_active_end",
                    "source": "ghoul_skulker.claw",
                },
            ],
        },
        "action.special.pounce": {
            "animation": "pounce",
            "events": [
                {"t": 0.25, "event": "leap_commit", "source": "ghoul_skulker.pounce"},
                {
                    "t": 0.54,
                    "event": "hitbox_active_start",
                    "source": "ghoul_skulker.pounce",
                },
                {
                    "t": 0.70,
                    "event": "hitbox_active_end",
                    "source": "ghoul_skulker.pounce",
                },
            ],
        },
        "interaction.cackle": {"animation": "cackle", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "ghoul_skulker.geometry", "point": {"x": 166.0, "y": 82.0}},
        "mouth": {
            "source": "ghoul_skulker.geometry",
            "point": {"x": 188.0, "y": 102.0},
        },
        "hand_l": {
            "source": "ghoul_skulker.geometry",
            "point": {"x": 90.0, "y": 198.0},
        },
        "hand_r": {
            "source": "ghoul_skulker.geometry",
            "point": {"x": 238.0, "y": 194.0},
        },
        "claw_tip": {
            "source": "ghoul_skulker.geometry",
            "point": {"x": 254.0, "y": 202.0},
        },
        "pounce_origin": {
            "source": "ghoul_skulker.geometry",
            "point": {"x": 170.0, "y": 245.0},
        },
    },
    "tags": ["enemy", "undead", "skulker"],
}

OUTLINE = (24, 20, 19, 255)
SKIN = (214, 205, 192, 255)
SKIN_SHADE = (164, 149, 139, 255)
SKIN_DARK = (118, 104, 95, 255)
LIP = (110, 70, 72, 255)
MOUTH = (70, 40, 46, 255)
TEETH = (246, 242, 230, 255)
EYE = (238, 234, 220, 255)
PUPIL = (24, 21, 22, 255)
CAP = (146, 112, 92, 255)
CAP_SHADE = (103, 78, 64, 255)
CLOTH = (122, 110, 96, 255)
CLOTH_HI = (160, 148, 132, 255)
NAIL = (212, 205, 188, 255)
DUST = (124, 112, 96, 150)
FX = (245, 236, 160, 150)


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(p: Point) -> Tuple[int, int]:
    return (_s(p[0]), _s(p[1]))


def _box(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _rot(x: float, y: float, deg: float) -> Point:
    rad = math.radians(deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return (x * c - y * s, x * s + y * c)


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
        self.lean = 0.0
        self.head_tilt = 0.0
        self.left_arm = 0.0
        self.right_arm = 0.0
        self.left_leg = 0.0
        self.right_leg = 0.0
        self.left_lift = 0.0
        self.right_lift = 0.0
        self.hand_spread = 0.0
        self.nose_pitch = 0.0
        self.cap_swing = 0.0
        self.mouth = 0.0
        self.dead_t = 0.0
        self.impact = 0.0
        self.blink = False
        self.x_eye = False

        if anim == "idle":
            self.root_x = s * 1.2
            self.bob = s * 1.8
            self.lean = -6.0 + s * 2.0
            self.head_tilt = -6.0 + s * 1.8
            self.left_arm = -6.0 + s * 5.0
            self.right_arm = 8.0 - s * 4.0
            self.left_leg = -3.0 + c * 2.0
            self.right_leg = 4.0 - c * 1.5
            self.hand_spread = 1.0 + max(0.0, s) * 2.0
            self.cap_swing = -s * 6.0
            self.mouth = max(0.0, s) * 0.06
            self.blink = frame_idx == nframes - 2
        elif anim == "skulk":
            self.root_x = s * 2.2
            self.bob = abs(s) * 2.8 - 0.6
            self.lean = -10.0 + s * 3.0
            self.head_tilt = -10.0 - s * 3.0
            self.left_leg = -24.0 * s
            self.right_leg = 22.0 * s
            self.left_lift = max(0.0, -s) * 10.0
            self.right_lift = max(0.0, s) * 9.0
            self.left_arm = 18.0 * s - 10.0
            self.right_arm = -16.0 * s + 7.0
            self.hand_spread = 2.0 + abs(s) * 2.0
            self.cap_swing = -s * 9.0
            self.nose_pitch = -s * 4.0
        elif anim == "claw":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-10.0, 12.0, tt)
            self.bob = -hit * 4.0
            self.lean = _lerp(-18.0, 18.0, tt)
            self.head_tilt = _lerp(-16.0, 12.0, tt)
            self.left_arm = _lerp(-34.0, 44.0, tt)
            self.right_arm = _lerp(10.0, -28.0, tt)
            self.left_leg = _lerp(-8.0, 12.0, tt)
            self.right_leg = _lerp(10.0, -4.0, tt)
            self.hand_spread = 3.0 + hit * 6.0
            self.cap_swing = _lerp(12.0, -16.0, tt)
            self.nose_pitch = _lerp(-8.0, 8.0, tt)
            self.mouth = 0.18 + hit * 0.14
            self.impact = hit
        elif anim == "pounce":
            tt = _ease(t)
            self.root_x = _lerp(-16.0, 18.0, tt)
            self.root_y = _lerp(4.0, -14.0, tt)
            self.bob = -math.sin(tt * math.pi) * 3.0
            self.lean = _lerp(-18.0, 24.0, tt)
            self.head_tilt = _lerp(-14.0, 16.0, tt)
            self.left_arm = _lerp(-20.0, 36.0, tt)
            self.right_arm = _lerp(-10.0, 30.0, tt)
            self.left_leg = _lerp(-18.0, 20.0, tt)
            self.right_leg = _lerp(-6.0, 16.0, tt)
            self.left_lift = _lerp(0.0, 10.0, tt)
            self.right_lift = _lerp(0.0, 6.0, tt)
            self.hand_spread = 3.0 + tt * 5.0
            self.cap_swing = _lerp(10.0, -12.0, tt)
            self.nose_pitch = _lerp(-6.0, 6.0, tt)
            self.mouth = 0.20 + tt * 0.12
            self.impact = math.sin(tt * math.pi)
        elif anim == "cackle":
            self.root_x = s * 1.0
            self.bob = s * 2.0
            self.lean = -8.0 + s * 6.0
            self.head_tilt = -6.0 - s * 5.0
            self.left_arm = -28.0 + s * 10.0
            self.right_arm = -34.0 - s * 9.0
            self.left_leg = -2.0
            self.right_leg = 6.0
            self.hand_spread = 4.0 + max(0.0, s) * 5.0
            self.cap_swing = s * 8.0
            self.nose_pitch = s * 4.0
            self.mouth = 0.30 + max(0.0, s) * 0.18
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
            self.root_x = shake * 4.0 - hit * 4.0
            self.bob = -hit * 2.5
            self.lean = -18.0 * hit
            self.head_tilt = 10.0 * hit
            self.left_arm = 20.0 * hit
            self.right_arm = 18.0 * hit
            self.left_leg = -10.0 * hit
            self.right_leg = 8.0 * hit
            self.hand_spread = 2.0 + hit * 3.0
            self.cap_swing = -14.0 * hit
            self.mouth = 0.16 * hit
        elif anim == "death":
            tt = _ease(t)
            self.dead_t = tt
            self.root_x = tt * 20.0
            self.root_y = tt * 8.0
            self.bob = -tt * 5.0
            self.lean = -82.0 * tt
            self.head_tilt = -28.0 * tt
            self.left_arm = _lerp(-4.0, 56.0, tt)
            self.right_arm = _lerp(6.0, -66.0, tt)
            self.left_leg = _lerp(-4.0, 26.0, tt)
            self.right_leg = _lerp(6.0, -22.0, tt)
            self.hand_spread = 2.0 + tt * 4.0
            self.cap_swing = -22.0 * tt
            self.mouth = 0.26 * tt
            self.x_eye = tt > 0.55


# --- Drawn as a rig (``shape_rig``): each rigid piece is painted once at its
# rest place and turned into the frame; limbs are bones of a fixed length. ---

#: Where a bone piece's root sits on its rest canvas (work pixels).
_BONE_O: Point = (30.0, 30.0)


def _sp(p: Point) -> Point:
    return (p[0] * SUPER, p[1] * SUPER)


def _rest(key, paint, pivot: Point):
    """A piece painted at its rest place on a frame-sized canvas, cut to what
    it covers (``_solo_shape_rig.rest_piece``); ``pivot`` in work pixels."""
    return _rig.rest_piece((TARGET_NAME,) + tuple(key), _CANVAS, _sp(pivot), paint)


def _put(img: Image.Image, part, at: Point, deg: float, name: str) -> None:
    shape_rig.place(img, part, _sp(at), deg, name)


def _fx_layer(img: Image.Image, paint, name: str) -> None:
    """A per-frame effect (it changes every frame) as ONE raster: painted on
    its own canvas, cut to what it covers and placed at its corner."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    paint(blending_draw(layer))
    box = layer.getchannel("A").getbbox()
    if box is not None:
        shape_rig.place(img, (layer.crop(box), (0.0, 0.0)), (float(box[0]), float(box[1])), 0.0, name)


def _deg(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _ik(root: Point, target: Point, l1: float, l2: float, ref: Point) -> Point:
    """The middle joint of a two-bone limb (lengths ``l1``, ``l2``) from
    ``root`` to ``target``, on the side of ``ref`` (the painter's own joint)."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = max(1e-6, min(math.hypot(dx, dy), l1 + l2 - 1e-6))
    ux, uy = dx / d, dy / d
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    bx, by = root[0] + ux * a, root[1] + uy * a
    c1 = (bx - uy * h, by + ux * h)
    c2 = (bx + uy * h, by - ux * h)
    d1 = (c1[0] - ref[0]) ** 2 + (c1[1] - ref[1]) ** 2
    d2 = (c2[0] - ref[0]) ** 2 + (c2[1] - ref[1]) ** 2
    return c1 if d1 <= d2 else c2


def _bone_piece(key, length: float, width: float, fill: RGBA, centre: RGBA, centre_w: float, cap: bool = False):
    """A straight limb segment along +x from its root: the painter's thick
    stroke with its dark centre line (``cap`` rounds the root end)."""
    O = _BONE_O

    def paint(d) -> None:
        end = (O[0] + length, O[1])
        if cap:
            _circle(d, O, width / 2.0, fill, fill, 0.1)
        _line(d, [O, end], fill, width)
        if centre is not None:
            _line(d, [O, end], centre, centre_w)

    return _rest(("bone",) + tuple(key) + (length, width, fill, centre, centre_w, cap), paint, O)


_LIMB_LENGTHS: dict = {}


def _limb_lengths(chains) -> dict:
    """Each limb's bone lengths: the painter's own in the rest pose (the
    first frame). ``chains(J)`` names each limb's ``(root, joint, end)``."""
    if not _LIMB_LENGTHS:
        for limb, (a, b, c) in chains(_joints(ROWS[0][0], 0, ROWS[0][1])).items():
            _LIMB_LENGTHS[limb] = (round(math.dist(a, b), 1), round(math.dist(b, c), 1))
    return _LIMB_LENGTHS


def _limb(chains, limb: str, root: Point, ref: Point, end: Point) -> Tuple[Point, float, float]:
    """A two-bone limb from ``root`` to ``end`` of its rest bone lengths,
    bent toward the painter's joint ``ref``. Out of reach (the painter's
    position-shift limb grows), both bones lengthen to the next 3-pixel
    step: a stretched limb takes a few lengths. Returns (joint, l1, l2)."""
    l1, l2 = _limb_lengths(chains)[limb]
    d = math.dist(root, end)
    if d > l1 + l2 - 0.5:
        k = math.ceil((d + 0.5) / 3.0) * 3.0 / (l1 + l2)
        l1, l2 = round(l1 * k, 1), round(l2 * k, 1)
    return _ik(root, end, l1, l2, ref), l1, l2


_CANVAS = (WORK_FRAME_SIZE[0] * SUPER, WORK_FRAME_SIZE[1] * SUPER)
_REST_ROOT: Point = (WORK_FRAME_SIZE[0] * 0.47, WORK_FRAME_SIZE[1] * 0.75)
_REST_HEAD: Point = (_REST_ROOT[0], _REST_ROOT[1] - 128)


def _joints(anim: str, frame_idx: int, nframes: int):
    return _ghoul_skulker_rig.evaluate(Pose(anim, frame_idx, nframes), WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])


def _chains(J) -> dict:
    return {
        "far_leg": (J.right_hip, J.right_knee, J.right_foot),
        "near_leg": (J.left_hip, J.left_knee, J.left_foot),
        "far_arm": (J.right_shoulder, J.right_elbow, J.right_hand),
        "near_arm": (J.left_shoulder, J.left_elbow, J.left_hand),
    }


def _paint_hand(draw: ImageDraw.ImageDraw, hand: Point, spread: float, front: bool) -> None:
    """The clawed hand at angle 0, palm at ``hand`` (turned into place)."""
    ang = 0.0
    palm_r = 6.0 if front else 5.0
    _circle(draw, hand, palm_r, SKIN if front else SKIN_SHADE, OUTLINE, 0.8)
    finger_len = 12.0 if front else 10.0
    for i, base_ang in enumerate([-34, -10, 14, 34]):
        a = ang + base_ang + (i - 1.5) * spread * 0.7
        base = (hand[0] + math.cos(math.radians(a - 10)) * 4.0, hand[1] + math.sin(math.radians(a - 10)) * 4.0)
        tip = (base[0] + math.cos(math.radians(a)) * finger_len, base[1] + math.sin(math.radians(a)) * finger_len)
        _line(draw, [hand, base, tip], SKIN if front else SKIN_SHADE, 2.8 if front else 2.3)
        _line(draw, [hand, base, tip], OUTLINE, 0.6)
        _poly(
            draw,
            [
                tip,
                (tip[0] + 4 * math.cos(math.radians(a - 18)), tip[1] + 4 * math.sin(math.radians(a - 18))),
                (tip[0] + 3 * math.cos(math.radians(a + 20)), tip[1] + 3 * math.sin(math.radians(a + 20))),
            ],
            NAIL,
            OUTLINE,
            0.35,
        )


def _draw_hand(img: Image.Image, hand: Point, ang: float, spread: float, *, front: bool, name: str) -> None:
    spread = _rig.q(spread, 0.5)
    part = _rest(("hand", front, spread), lambda d: _paint_hand(d, _BONE_O, spread, front), _BONE_O)
    _put(img, part, hand, ang, name)


def _draw_foot(draw: ImageDraw.ImageDraw, foot: Point, facing: float) -> None:
    sole = [
        (foot[0] - 8, foot[1] - 3),
        (foot[0] + 10 + facing * 4, foot[1] - 4),
        (foot[0] + 16 + facing * 5, foot[1] + 3),
        (foot[0] + 8, foot[1] + 7),
        (foot[0] - 7, foot[1] + 5),
    ]
    _poly(draw, sole, SKIN_SHADE, OUTLINE, 0.8)
    for frac in [0.65, 0.82, 0.98]:
        toe = (foot[0] + (12 + facing * 4) * frac, foot[1] + 2)
        _poly(draw, [toe, (toe[0] + 4, toe[1] - 1), (toe[0] + 2, toe[1] + 3)], NAIL, OUTLINE, 0.3)


def _draw_limb(img: Image.Image, limb: str, a: Point, joint_ref: Point, c: Point, w1: float, w2: float, fill: RGBA, line_w: float, joint_r: float, joint_w: float) -> Point:
    """A two-bone limb of fixed lengths (thick strokes, a dark centre line and
    a round joint), bent where the painter's joint is. Returns the end."""
    b, l1, l2 = _limb(_chains, limb, a, joint_ref, c)
    _put(img, _bone_piece((limb, 1), l1, w1, fill, OUTLINE, line_w), a, _deg(a, b), f"{limb}_upper")
    _put(img, _bone_piece((limb, 2), l2, w2, fill, OUTLINE, line_w), b, _deg(b, c), f"{limb}_lower")
    joint = _rest(("joint", joint_r, fill, joint_w), lambda d: _circle(d, _BONE_O, joint_r, fill, OUTLINE, joint_w), _BONE_O)
    _put(img, joint, b, 0.0, f"{limb}_joint")
    return c


def _P0(x: float, y: float) -> Point:
    return (_REST_ROOT[0] + x, _REST_ROOT[1] + y)


def _paint_body(draw: ImageDraw.ImageDraw) -> None:
    P = _P0
    _poly(draw, [P(-18, -66), P(14, -66), P(28, -44), P(12, -24), P(-12, -26), P(-26, -46)], SKIN_SHADE, OUTLINE, 1.0)
    _poly(draw, [P(-10, -60), P(16, -60), P(18, -25), P(4, -6), P(-10, -12), P(-14, -34)], CLOTH, OUTLINE, 0.8)
    _line(draw, [P(-4, -54), P(4, -10)], CLOTH_HI, 0.8)
    _poly(draw, [P(-18, -116), P(18, -124), P(34, -102), P(28, -58), P(12, -40), P(-16, -46), P(-30, -84)], SKIN, OUTLINE, 1.2)
    _poly(draw, [P(-14, -94), P(-6, -102), P(0, -90), P(-4, -78), P(-12, -78)], SKIN_SHADE, OUTLINE, 0.5)
    _poly(draw, [P(2, -94), P(12, -100), P(16, -86), P(12, -76), P(2, -78)], SKIN_SHADE, OUTLINE, 0.5)
    _circle(draw, P(-7, -86), 1.8, LIP, OUTLINE, 0.2)
    _circle(draw, P(8, -84), 1.8, LIP, OUTLINE, 0.2)
    _line(draw, [P(-5, -70), P(2, -66), P(10, -64)], SKIN_SHADE, 0.8)


def _H0(x: float, y: float) -> Point:
    return (_REST_HEAD[0] + x, _REST_HEAD[1] + y)


def _paint_cap(draw: ImageDraw.ImageDraw, cap_swing: float) -> None:
    H = _H0
    cap = [H(-16, -22), H(0, -40), H(22, -38), H(36 + cap_swing * 0.35, -18 + cap_swing * 0.12), H(26 + cap_swing * 0.45, -4), H(8, -8), H(-10, -4)]
    _poly(draw, cap, CAP, OUTLINE, 1.0)
    tail = [H(18, -28), H(44 + cap_swing * 0.35, -42), H(66 + cap_swing * 0.5, -26), H(34 + cap_swing * 0.25, -10)]
    _poly(draw, tail, CAP_SHADE, OUTLINE, 0.8)


def _paint_head(draw: ImageDraw.ImageDraw, nose_pitch: float, blink: bool, x_eye: bool, mouth: float) -> None:
    H = _H0
    _poly(draw, [H(-16, -14), H(-10, -26), H(6, -30), H(18, -20), H(20, -4), H(12, 10), H(-6, 14), H(-18, 2)], SKIN, OUTLINE, 1.1)
    nose = [H(10, -10), H(28, -12 + nose_pitch * 0.2), H(42, -4 + nose_pitch * 0.25), H(22, 0), H(14, 2)]
    _poly(draw, nose, SKIN_SHADE, OUTLINE, 0.8)
    _poly(draw, [H(8, 0), H(-2, 4), H(-12, 2), H(-18, -4), H(-14, -8), H(-4, -5)], SKIN_DARK, OUTLINE, 0.5)
    _poly(draw, [H(14, 0), H(22, 2), H(34, 0), H(40, -7), H(36, -12), H(24, -8)], SKIN_DARK, OUTLINE, 0.5)
    if x_eye:
        _line(draw, [H(-5, -10), H(3, -2)], OUTLINE, 0.9)
        _line(draw, [H(-5, -2), H(3, -10)], OUTLINE, 0.9)
    elif blink:
        _line(draw, [H(-6, -7), H(2, -7)], OUTLINE, 0.9)
    else:
        _ellipse(draw, H(-2, -6)[0], H(-2, -6)[1], 3.8, 3.0, EYE, OUTLINE, 0.5)
        _circle(draw, H(-1, -6), 1.0, PUPIL, PUPIL, 0.1)
        _line(draw, [H(-8, -11), H(2, -12)], OUTLINE, 0.8)
    _line(draw, [H(15, -4), H(18, 2)], SKIN_DARK, 0.6)
    if mouth > 0.16:
        _ellipse(draw, H(4, 8)[0], H(4, 8)[1], 6.0, 3.6 + mouth * 3.0, MOUTH, OUTLINE, 0.6)
        _poly(draw, [H(0, 8), H(4, 13), H(8, 8)], TEETH, OUTLINE, 0.25)
    else:
        _line(draw, [H(0, 8), H(6, 10), H(12, 8)], LIP, 0.8)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", _CANVAS, (0, 0, 0, 0))
    pose = Pose(anim, frame_idx, nframes)

    J = _ghoul_skulker_rig.evaluate(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    root = J.root
    tilt = J.body_ang

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, tilt)
        return (root[0] + rx, root[1] + ry)

    foot = _rest(("foot",), lambda d: _draw_foot(d, _BONE_O, 1), _BONE_O)

    # far leg first
    _draw_limb(img, "far_leg", J.right_hip, J.right_knee, J.right_foot, 7.5, 7.5, SKIN_SHADE, 1.2, 5.2, 0.6)
    _put(img, foot, J.right_foot, 0.0, "far_foot")

    # pelvis and torso: one piece turned with the lean
    _put(img, _rest(("body",), _paint_body, _REST_ROOT), root, tilt, "body")

    # far arm first
    _draw_limb(img, "far_arm", J.right_shoulder, J.right_elbow, J.right_hand, 6.2, 5.2, SKIN_SHADE, 1.0, 4.8, 0.5)
    _draw_hand(img, J.right_hand, 12 + pose.right_arm * 0.3, pose.hand_spread, front=False, name="far_hand")

    # head and cap
    cap_swing = _rig.q(pose.cap_swing, 2.0)
    _put(img, _rest(("cap", cap_swing), lambda d: _paint_cap(d, cap_swing), _REST_HEAD), J.head_root, J.head_ang, "cap")
    nose_pitch = _rig.q(pose.nose_pitch, 2.0)
    mouth = _rig.q(pose.mouth, 0.02)
    head = _rest(
        ("head", nose_pitch, pose.blink, pose.x_eye, mouth),
        lambda d: _paint_head(d, nose_pitch, pose.blink, pose.x_eye, mouth),
        _REST_HEAD,
    )
    _put(img, head, J.head_root, J.head_ang, "head")

    # front leg on top
    _draw_limb(img, "near_leg", J.left_hip, J.left_knee, J.left_foot, 8.6, 8.6, SKIN, 1.4, 5.8, 0.6)
    _put(img, foot, J.left_foot, 0.0, "near_foot")

    # front arm on top
    left_hand = J.left_hand
    _draw_limb(img, "near_arm", J.left_shoulder, J.left_elbow, left_hand, 7.0, 5.8, SKIN, 1.1, 5.0, 0.5)
    _draw_hand(img, left_hand, 186 - pose.left_arm * 0.3, pose.hand_spread, front=True, name="near_hand")

    # effects change every frame: one raster each
    if anim in {"claw", "pounce"} and pose.impact > 0.2:
        hx, hy = left_hand
        _fx_layer(img, lambda d: d.arc((_s(hx - 44), _s(hy - 26), _s(hx + 40), _s(hy + 36)), 168, 308, fill=FX, width=_s(3.8)), "fx_arc")
    if anim in {"skulk", "pounce"} and (pose.left_lift > 1.0 or pose.right_lift > 1.0):
        def dust(draw) -> None:
            for dx, dy in [(-26, 0), (-10, 4), (12, 1), (30, 5)]:
                c = P(dx, 34 + dy)
                _poly(draw, [(c[0] - 2, c[1]), (c[0], c[1] - 4), (c[0] + 3, c[1] - 1), (c[0] + 1, c[1] + 2)], DUST, (88, 80, 70, 100), 0.25)

        _fx_layer(img, dust, "fx_dust")

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
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, lambda anim, frame_idx, nframes: _render_frame(anim, frame_idx, nframes), outputs, frame_transform, Path(out_dir))
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
        description="Render the standalone Ghoul Skulker sprite sheet."
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
