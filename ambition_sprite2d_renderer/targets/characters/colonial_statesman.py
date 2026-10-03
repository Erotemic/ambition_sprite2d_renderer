"""Standalone generator for a portrait-inspired colonial statesman character.

Visual goal:
- inspired by formal 18th-century oil portrait aesthetics
- powdered white wig with side rolls
- stern face, pale skin, dark formal coat, white cravat
- restrained, dignified motion rather than wild cartoon posing
- still readable as a side-scroller unit with a few active combat / command moves

This character is not a pirate; it is a formal statesman / aristocratic duelist
that leans into classic portrait styling.
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
from . import _colonial_statesman_rig
from . import _solo_shape_rig as _rig

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_colonial_statesman",
        "display_name": "Colonial Statesman",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "story", "statesman"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": None,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "story", "statesman"],
    "sockets": {
        "head": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 24.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 54.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 48.0, "y": 64.0},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 80.0, "y": 64.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 8.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
    },
}


RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "colonial_statesman"
FRAME_SIZE = (320, 352)
WORK_FRAME_SIZE = (640, 704)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("walk", 8, 96),
    ("address", 6, 112),
    ("thrust", 7, 82),
    ("pistol", 6, 88),
    ("hurt", 4, 92),
    ("death", 8, 112),
]

OUTLINE = (28, 22, 20, 255)
SKIN = (232, 205, 177, 255)
SKIN_SHADE = (198, 166, 142, 255)
BLUSH = (208, 151, 132, 255)
WIG = (236, 236, 228, 255)
WIG_SHADE = (206, 205, 197, 255)
COAT = (36, 36, 40, 255)
COAT_HI = (70, 72, 82, 255)
VEST = (244, 242, 236, 255)
CRAVAT = (252, 251, 247, 255)
BREECH = (228, 226, 219, 255)
BOOT = (30, 28, 30, 255)
GOLD = (209, 176, 87, 255)
RAPIER = (190, 199, 212, 255)
GUNMETAL = (98, 103, 112, 255)
WOOD = (114, 74, 46, 255)
MUZZLE = (244, 218, 142, 176)
FX = (240, 220, 150, 160)
SHADOW = (90, 70, 54, 80)


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


def _circle(
    draw: ImageDraw.ImageDraw,
    p: Point,
    r: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    _ellipse(draw, p[0], p[1], r, r, fill, outline, width)


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
        self.tilt = 0.0
        self.head = 0.0
        self.left_arm = 0.0
        self.right_arm = 0.0
        self.left_leg = 0.0
        self.right_leg = 0.0
        self.left_lift = 0.0
        self.right_lift = 0.0
        self.coat_sway = 0.0
        self.cravat = 0.0
        self.rapier = 0.0
        self.pistol = 0.0
        self.flash = 0.0
        self.open_mouth = 0.0
        self.dead_t = 0.0
        self.blink = False
        self.x_eye = False

        if anim == "idle":
            self.bob = s * 1.5
            self.tilt = s * 1.3
            self.head = -2.0 + s * 1.0
            self.left_arm = -4.0 + s * 2.0
            self.right_arm = 2.0 - s * 1.5
            self.left_leg = -2.0 + c * 1.2
            self.right_leg = 2.0 - c * 1.0
            self.coat_sway = s * 2.0
            self.cravat = max(0.0, s) * 2.0
            self.blink = frame_idx == nframes - 2
        elif anim == "walk":
            self.root_x = s * 2.0
            self.bob = abs(s) * 2.6 - 0.4
            self.tilt = s * 2.2
            self.head = -2.0 - s * 0.8
            self.left_leg = -22.0 * s
            self.right_leg = 20.0 * s
            self.left_lift = max(0.0, -s) * 8.0
            self.right_lift = max(0.0, s) * 7.0
            self.left_arm = 12.0 * s - 4.0
            self.right_arm = -10.0 * s + 4.0
            self.coat_sway = -s * 6.0
        elif anim == "address":
            self.bob = s * 1.0
            self.tilt = -1.5 + s * 0.8
            self.head = -1.5 + s * 1.2
            self.left_arm = _lerp(-6.0, 30.0, math.sin(t * math.pi))
            self.right_arm = -4.0
            self.left_leg = -1.0
            self.right_leg = 2.0
            self.open_mouth = 0.08 + max(0.0, s) * 0.06
            self.coat_sway = s * 1.4
            self.cravat = 1.0 + max(0.0, s) * 2.0
        elif anim == "thrust":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-6.0, 18.0, tt)
            self.bob = -hit * 2.0
            self.tilt = _lerp(-6.0, 10.0, tt)
            self.head = _lerp(-4.0, 8.0, tt)
            self.left_arm = _lerp(-18.0, 56.0, tt)
            self.right_arm = _lerp(6.0, -24.0, tt)
            self.left_leg = _lerp(-10.0, 16.0, tt)
            self.right_leg = _lerp(8.0, -6.0, tt)
            self.left_lift = _lerp(0.0, 6.0, tt)
            self.coat_sway = _lerp(6.0, -14.0, tt)
            self.rapier = hit
        elif anim == "pistol":
            tt = _ease(t)
            self.root_x = _lerp(-4.0, 8.0, tt)
            self.bob = -math.sin(tt * math.pi) * 1.6
            self.tilt = _lerp(-2.0, 4.0, tt)
            self.head = _lerp(-2.0, 3.0, tt)
            self.left_arm = -8.0
            self.right_arm = _lerp(-12.0, 40.0, tt)
            self.left_leg = -4.0
            self.right_leg = 4.0
            self.coat_sway = _lerp(3.0, -6.0, tt)
            self.pistol = tt
            self.flash = 1.0 if frame_idx == nframes - 2 else 0.0
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
            self.root_x = shake * 3.0 - hit * 3.5
            self.bob = -hit * 2.0
            self.tilt = -9.0 * hit
            self.head = 6.0 * hit
            self.left_arm = 12.0 * hit
            self.right_arm = 16.0 * hit
            self.left_leg = -8.0 * hit
            self.right_leg = 7.0 * hit
            self.coat_sway = -8.0 * hit
            self.open_mouth = 0.10 * hit
        elif anim == "death":
            tt = _ease(t)
            self.dead_t = tt
            self.root_x = tt * 14.0
            self.root_y = tt * 8.0
            self.bob = -tt * 4.0
            self.tilt = -78.0 * tt
            self.head = -16.0 * tt
            self.left_arm = _lerp(-4.0, 48.0, tt)
            self.right_arm = _lerp(4.0, -52.0, tt)
            self.left_leg = _lerp(-2.0, 18.0, tt)
            self.right_leg = _lerp(2.0, -18.0, tt)
            self.coat_sway = -20.0 * tt
            self.x_eye = tt > 0.58


# --- Drawn as a rig (``shape_rig``): each rigid piece is painted once at its
# rest place and turned into the frame; limbs are bones of a fixed length. ---

#: Where a bone piece's root sits on its rest canvas (work pixels); a
#: piece reaching every way is painted about the canvas middle.
_BONE_O: Point = (30.0, 30.0)
_MID_O: Point = (WORK_FRAME_SIZE[0] / 2.0, WORK_FRAME_SIZE[1] / 2.0)


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
_REST_ROOT: Point = (WORK_FRAME_SIZE[0] * 0.47, WORK_FRAME_SIZE[1] * 0.77)
_REST_HEAD: Point = (_REST_ROOT[0] - 2, _REST_ROOT[1] - 246)
_THIGH, _SHIN = 46.0, 44.0


def _joints(anim: str, frame_idx: int, nframes: int):
    return _colonial_statesman_rig.evaluate(Pose(anim, frame_idx, nframes), WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])


def _chains(J) -> dict:
    return {
        "far_arm": (J.far_shoulder, J.far_elbow, J.far_hand),
        "near_arm": (J.near_shoulder, J.near_elbow, J.near_hand),
    }


def _P0(x: float, y: float) -> Point:
    return (_REST_ROOT[0] + x, _REST_ROOT[1] + y)


def _H0(x: float, y: float) -> Point:
    return (_REST_HEAD[0] + x, _REST_HEAD[1] + y)


def _draw_leg(img: Image.Image, hip: Point, thigh_ang: float, lift: float, front: bool, side: str) -> Point:
    """Thigh and shin bones (fixed lengths), the knee and the boot riding
    the ankle."""
    knee = (hip[0] + _THIGH * math.cos(math.radians(thigh_ang)), hip[1] + _THIGH * math.sin(math.radians(thigh_ang)))
    reach = (knee[0] + _SHIN * math.cos(math.radians(thigh_ang + 10)), knee[1] + _SHIN * math.sin(math.radians(thigh_ang + 10)) - lift)
    shin_deg = _deg(knee, reach)
    ankle = (knee[0] + _SHIN * math.cos(math.radians(shin_deg)), knee[1] + _SHIN * math.sin(math.radians(shin_deg)))
    col = BREECH if front else (212, 210, 205, 255)
    width = 8.0 if front else 7.0
    _put(img, _bone_piece(("thigh", front), _THIGH, width, col, OUTLINE, 1.1), hip, thigh_ang, f"{side}_thigh")
    _put(img, _bone_piece(("shin", front), _SHIN, width, col, OUTLINE, 1.1), knee, shin_deg, f"{side}_shin")
    _put(img, _rest(("knee", front), lambda d: _ellipse(d, _BONE_O[0], _BONE_O[1], 5.2, 5.6, col, OUTLINE, 0.5), _BONE_O), knee, 0.0, f"{side}_knee")

    def boot(d) -> None:
        x, y = _BONE_O
        _poly(d, [(x - 7, y - 6), (x + 10, y - 6), (x + 16, y + 4), (x + 6, y + 10), (x - 8, y + 8)], BOOT, OUTLINE, 0.8)

    _put(img, _rest(("boot",), boot, _BONE_O), ankle, 0.0, f"{side}_boot")
    return ankle


def _draw_arm(img: Image.Image, limb: str, shoulder: Point, elbow_ref: Point, hand: Point, width: float, hand_r: float) -> None:
    """Two coat-sleeve bones bent at the painter's elbow, and the hand."""
    elbow, l1, l2 = _limb(_chains, limb, shoulder, elbow_ref, hand)
    _put(img, _bone_piece((limb, 1), l1, width, COAT, OUTLINE, 1.0), shoulder, _deg(shoulder, elbow), f"{limb}_upper")
    _put(img, _bone_piece((limb, 2), l2, width, COAT, OUTLINE, 1.0, cap=True), elbow, _deg(elbow, hand), f"{limb}_fore")
    hand_part = _rest(("hand", hand_r), lambda d: _ellipse(d, _BONE_O[0], _BONE_O[1], hand_r, hand_r * 0.88, SKIN, OUTLINE, 0.5), _BONE_O)
    _put(img, hand_part, hand, 0.0, f"{limb}_hand")


def _paint_tails(draw: ImageDraw.ImageDraw, sway: float) -> None:
    P = _P0
    _poly(draw, [P(-18, -102), P(-6, -38), P(-20 + sway * 0.4, 22), P(-2, 18), P(10, -24), P(2, -102)], COAT, OUTLINE, 1.0)
    _poly(draw, [P(8, -102), P(12, -34), P(28 + sway * 0.55, 18), P(44, 12), P(32, -40), P(26, -102)], COAT, OUTLINE, 1.0)


def _paint_torso(draw: ImageDraw.ImageDraw, cravat: float) -> None:
    P = _P0
    _poly(draw, [P(-34, -200), P(6, -214), P(36, -198), P(48, -148), P(44, -100), P(22, -76), P(-10, -72), P(-36, -94), P(-42, -148)], COAT, OUTLINE, 1.2)
    _poly(draw, [P(-12, -188), P(0, -194), P(-4, -116), P(-18, -100), P(-26, -124)], COAT_HI, OUTLINE, 0.6)
    _poly(draw, [P(10, -190), P(22, -188), P(34, -124), P(18, -98), P(6, -118)], COAT_HI, OUTLINE, 0.6)
    _poly(draw, [P(-8, -196), P(14, -194), P(18, -104), P(-2, -92), P(-18, -108), P(-18, -176)], VEST, OUTLINE, 0.8)
    _poly(draw, [P(-2, -202), P(10, -202), P(14, -174 + cravat * 0.2), P(6, -144), P(-4, -170), P(-10, -184)], CRAVAT, OUTLINE, 0.7)
    _line(draw, [P(0, -182), P(8, -166), P(2, -152), P(12, -138)], (214, 214, 210, 255), 0.8)


def _paint_trim(draw: ImageDraw.ImageDraw) -> None:
    P = _P0
    for y in [-176, -154, -132]:
        _ellipse(draw, P(4, y)[0], P(4, y)[1], 2.0, 2.0, GOLD, OUTLINE, 0.3)
    _line(draw, [P(-36, -126), P(-28, -126)], CRAVAT, 0.8)
    _line(draw, [P(42, -124), P(50, -124)], CRAVAT, 0.8)


def _paint_head(draw: ImageDraw.ImageDraw, blink: bool, x_eye: bool, open_mouth: float) -> None:
    H = _H0
    _poly(draw, [H(-28, -10), H(-22, -40), H(0, -54), H(20, -46), H(32, -20), H(30, 12), H(22, 26), H(12, 24), H(8, 0), H(-20, 8)], WIG_SHADE, OUTLINE, 1.0)
    _poly(draw, [H(-34, -4), H(-48, 10), H(-50, 28), H(-38, 42), H(-18, 34), H(-20, 12)], WIG, OUTLINE, 0.8)
    _poly(draw, [H(30, -4), H(46, 6), H(50, 24), H(42, 42), H(24, 36), H(22, 8)], WIG, OUTLINE, 0.8)
    _poly(draw, [H(-20, -18), H(-10, -36), H(12, -40), H(28, -26), H(30, 0), H(16, 20), H(-6, 24), H(-24, 10)], SKIN, OUTLINE, 1.0)
    _ellipse(draw, H(8, -2)[0], H(8, -2)[1], 9.0, 7.2, BLUSH, None, 0)
    _ellipse(draw, H(-8, 0)[0], H(-8, 0)[1], 8.5, 6.8, BLUSH, None, 0)
    if x_eye:
        _line(draw, [H(-6, -6), H(0, 0)], OUTLINE, 0.8)
        _line(draw, [H(-6, 0), H(0, -6)], OUTLINE, 0.8)
        _line(draw, [H(12, -6), H(18, 0)], OUTLINE, 0.8)
        _line(draw, [H(12, 0), H(18, -6)], OUTLINE, 0.8)
    elif blink:
        _line(draw, [H(-8, -3), H(0, -3)], OUTLINE, 0.8)
        _line(draw, [H(10, -4), H(18, -4)], OUTLINE, 0.8)
    else:
        _ellipse(draw, H(-4, -3)[0], H(-4, -3)[1], 3.5, 2.8, (239, 241, 240, 255), OUTLINE, 0.4)
        _ellipse(draw, H(14, -4)[0], H(14, -4)[1], 3.5, 2.8, (239, 241, 240, 255), OUTLINE, 0.4)
        _circle(draw, H(-3, -3), 0.9, (36, 44, 54, 255), (36, 44, 54, 255), 0.1)
        _circle(draw, H(15, -4), 0.9, (36, 44, 54, 255), (36, 44, 54, 255), 0.1)
        _line(draw, [H(-9, -8), H(-1, -10)], OUTLINE, 0.5)
        _line(draw, [H(10, -9), H(18, -10)], OUTLINE, 0.5)
    _poly(draw, [H(6, -2), H(10, 6), H(4, 10), H(2, 4)], SKIN_SHADE, OUTLINE, 0.3)
    if open_mouth > 0.02:
        _ellipse(draw, H(7, 14)[0], H(7, 14)[1], 4.6, 2.4 + open_mouth * 10.0, (102, 62, 66, 255), OUTLINE, 0.4)
    else:
        _line(draw, [H(2, 14), H(8, 15), H(14, 14)], (114, 76, 72, 255), 0.7)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", _CANVAS, (0, 0, 0, 0))
    pose = Pose(anim, frame_idx, nframes)

    J = _colonial_statesman_rig.evaluate(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    root = J.root
    tilt = J.body_ang

    # subtle drop shadow
    shadow = _rest(("shadow",), lambda d: _ellipse(d, _MID_O[0], _MID_O[1], 54, 12, SHADOW, None, 0), _MID_O)
    _put(img, shadow, (root[0] + 6, root[1] + 14), 0.0, "shadow")

    # far leg first
    _draw_leg(img, J.far_hip, 92 + pose.right_leg, pose.right_lift, False, "far")

    # coat tails behind body (they sway in a few steps), then the torso
    sway = _rig.q(pose.coat_sway, 2.0)
    _put(img, _rest(("tails", sway), lambda d: _paint_tails(d, sway), _REST_ROOT), root, tilt, "coat_tails")
    cravat = _rig.q(pose.cravat, 2.5)
    _put(img, _rest(("torso", cravat), lambda d: _paint_torso(d, cravat), _REST_ROOT), root, tilt, "torso")

    # far arm
    far_hand = J.far_hand
    _draw_arm(img, "far_arm", J.far_shoulder, J.far_elbow, far_hand, 7.2, 4.2)

    # head + wig: one piece per face
    mouth = _rig.q(pose.open_mouth, 0.02)
    head = _rest(("head", pose.blink, pose.x_eye, mouth), lambda d: _paint_head(d, pose.blink, pose.x_eye, mouth), _REST_HEAD)
    _put(img, head, J.head_root, J.head_ang, "head")

    # near leg
    _draw_leg(img, J.near_hip, 92 + pose.left_leg, pose.left_lift, True, "near")

    # near arm with weapon / gesturing
    near_hand = J.near_hand
    _draw_arm(img, "near_arm", J.near_shoulder, J.near_elbow, near_hand, 7.6, 4.4)

    if anim == "thrust":
        guard = (near_hand[0] + 6, near_hand[1] + 2)
        reach = _rig.q(94 + pose.rapier * 40, 4.0)

        def rapier(draw) -> None:
            g = _MID_O
            _line(draw, [g, (g[0] + reach, g[1] - 8)], RAPIER, 1.6)
            _line(draw, [g, (g[0] + 12, g[1] - 1)], OUTLINE, 0.5)
            _poly(draw, [(g[0] - 2, g[1] - 4), (g[0] + 8, g[1] - 2), (g[0] + 8, g[1] + 4), (g[0] - 2, g[1] + 2)], GOLD, OUTLINE, 0.4)

        _put(img, _rest(("rapier", reach), rapier, _MID_O), guard, 0.0, "rapier")
        if pose.rapier > 0.2:
            cx, cy = (guard[0] + 94 + pose.rapier * 40, guard[1] - 8)
            _fx_layer(img, lambda d: d.arc((_s(cx - 40), _s(cy - 20), _s(cx + 24), _s(cy + 26)), 200, 350, fill=FX, width=_s(3.0)), "fx_arc")
    elif anim == "pistol":
        gun_base = (far_hand[0] + 6, far_hand[1] - 1)
        barrel_len = _rig.q(44 + pose.pistol * 8, 2.0)
        flash = pose.flash > 0.5

        def pistol(draw) -> None:
            g = _MID_O
            barrel = (g[0] + barrel_len, g[1] - 2)
            _poly(draw, [(g[0] - 3, g[1] - 3), (g[0] + 10, g[1] - 4), (g[0] + 14, g[1] + 2), (g[0] + 2, g[1] + 4)], WOOD, OUTLINE, 0.4)
            _line(draw, [(g[0] + 8, g[1] - 1), barrel], GUNMETAL, 1.8)
            if flash:
                cx, cy = barrel
                _poly(draw, [(cx, cy), (cx + 16, cy - 6), (cx + 26, cy), (cx + 16, cy + 6)], MUZZLE, None, 0)

        _put(img, _rest(("pistol", barrel_len, flash), pistol, _MID_O), gun_base, 0.0, "pistol")

    # buttons and cuff details
    _put(img, _rest(("trim",), _paint_trim, _REST_ROOT), root, tilt, "trim")

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
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, lambda anim, frame_idx, nframes: _render_frame(anim, frame_idx, nframes), outputs, frame_transform, Path(out_dir))
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ] + list(parts.values())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the portrait-inspired Colonial Statesman sprite sheet."
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
