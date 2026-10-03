"""Standalone generator for a heavy Viking warrior sprite sheet.

Redesigned from scratch with a broad opera / saga silhouette:
- giant horned steel helmet
- thick beard and barrel torso
- big beefy arms and short strong legs
- heavy double axe and exaggerated bellow poses
- clearly distinct from slimmer Viking targets

Generator only. No registration or GUI wiring.
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
from . import _viking_heavy_warrior_rig
from . import _solo_shape_rig as _rig

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_viking_heavy_warrior",
        "display_name": "Viking Heavy Warrior",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": ["story", "humanoid", "enemy", "combatant", "viking"],
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
    "brain": {"default_preset": "melee_brute_brute"},
    "actions": {"default_preset": "brute_lunge"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "enemy", "combatant", "viking"],
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
        "weapon_grip": {
            "source": "explicit.profile.combat_humanoid",
            "point": {"x": 80.0, "y": 64.0},
        },
        "weapon_tip": {
            "source": "explicit.profile.combat_humanoid",
            "point": {"x": 104.0, "y": 60.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {
                    "t": 0.34,
                    "event": "hitbox_active_start",
                    "source": "explicit.profile.combat_humanoid",
                },
                {
                    "t": 0.58,
                    "event": "hitbox_active_end",
                    "source": "explicit.profile.combat_humanoid",
                },
            ],
        },
    },
}


RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "viking_heavy_warrior"
FRAME_SIZE = (320, 320)
WORK_FRAME_SIZE = (760, 760)
#: Work pixels to canvas pixels: the canvas is 8x the frame, so the frame is
#: a WHOLE-factor reduction of it (a turned piece reduces only that way).
SUPER = FRAME_SIZE[0] * 8 / WORK_FRAME_SIZE[0]
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 132),
    ("march", 8, 98),
    ("axe_cleave", 7, 82),
    ("helm_bash", 7, 84),
    ("bass_bellow", 6, 106),
    ("hurt", 4, 92),
    ("death", 8, 112),
]

OUTLINE = (26, 20, 18, 255)
SKIN = (222, 176, 136, 255)
SKIN_SHADE = (184, 136, 100, 255)
HAIR = (184, 104, 52, 255)
HAIR_SHADE = (132, 72, 38, 255)
BEARD = (146, 80, 38, 255)
BEARD_SHADE = (112, 60, 30, 255)
STEEL = (186, 196, 208, 255)
STEEL_SHADE = (126, 138, 150, 255)
HORN = (235, 228, 176, 255)
HORN_SHADE = (198, 188, 132, 255)
FUR = (224, 212, 196, 255)
FUR_SHADE = (182, 166, 150, 255)
TUNIC = (96, 128, 184, 255)
TUNIC_SHADE = (70, 98, 150, 255)
LEATHER = (130, 88, 54, 255)
LEATHER_DARK = (92, 60, 38, 255)
GOLD = (228, 186, 64, 255)
PANTS = (110, 96, 80, 255)
PANTS_SHADE = (84, 72, 58, 255)
SANDAL = (76, 54, 34, 255)
WOOD = (124, 88, 54, 255)
EYE = (248, 246, 238, 255)
PUPIL = (40, 38, 42, 255)
MOUTH = (102, 44, 48, 255)
TONGUE = (210, 104, 118, 255)
FX = (248, 238, 188, 148)
DUST = (136, 118, 92, 132)


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
    def __init__(self, anim: str, idx: int, n: int) -> None:
        t = idx / max(1, n - 1)
        cyc = math.tau * idx / max(1, n)
        s = math.sin(cyc)

        self.root_x = 0.0
        self.root_y = 0.0
        self.bob = 0.0
        self.lean = 0.0
        self.head = 0.0
        self.left_leg = 0.0
        self.right_leg = 0.0
        self.left_lift = 0.0
        self.right_lift = 0.0
        self.left_arm = 0.0
        self.right_arm = 0.0
        self.weapon_angle = 0.0
        self.weapon_len = 0.0
        self.beard = 0.0
        self.mouth = 0.0
        self.impact = 0.0
        self.blink = False
        self.x_eye = False

        if anim == "idle":
            self.bob = s * 1.0
            self.lean = s * 1.2
            self.head = -1.0 + s * 1.0
            self.left_arm = -2.0 + s * 1.2
            self.right_arm = 2.0 - s * 1.2
            self.weapon_angle = -12.0 + s * 4.0
            self.beard = s * 3.0
            self.blink = idx == n - 2
        elif anim == "march":
            self.root_x = s * 2.2
            self.bob = abs(s) * 3.4 - 0.5
            self.lean = s * 2.0
            self.head = -2.0 - s * 1.2
            self.left_leg = -20.0 * s
            self.right_leg = 20.0 * s
            self.left_lift = max(0.0, -s) * 8.0
            self.right_lift = max(0.0, s) * 8.0
            self.left_arm = 14.0 * s - 4.0
            self.right_arm = -12.0 * s + 4.0
            self.weapon_angle = -22.0 - s * 8.0
            self.beard = -s * 8.0
        elif anim == "axe_cleave":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-14.0, 24.0, tt)
            self.bob = -hit * 2.6
            self.lean = _lerp(-14.0, 18.0, tt)
            self.head = _lerp(-6.0, 8.0, tt)
            self.left_leg = _lerp(-10.0, 10.0, tt)
            self.right_leg = _lerp(10.0, -8.0, tt)
            self.left_arm = _lerp(-58.0, 22.0, tt)
            self.right_arm = _lerp(-24.0, 30.0, tt)
            self.weapon_angle = _lerp(-118.0, 34.0, tt)
            self.weapon_len = hit * 12.0
            self.beard = _lerp(10.0, -10.0, tt)
            self.mouth = 0.12
            self.impact = hit
        elif anim == "helm_bash":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-12.0, 26.0, tt)
            self.bob = -hit * 2.0
            self.lean = _lerp(-12.0, 24.0, tt)
            self.head = _lerp(-4.0, 12.0, tt)
            self.left_leg = _lerp(-12.0, 16.0, tt)
            self.right_leg = _lerp(12.0, -10.0, tt)
            self.left_arm = _lerp(10.0, 16.0, tt)
            self.right_arm = _lerp(-16.0, 18.0, tt)
            self.weapon_angle = _lerp(-34.0, 8.0, tt)
            self.weapon_len = hit * 8.0
            self.beard = _lerp(8.0, -8.0, tt)
            self.mouth = 0.10
            self.impact = hit
        elif anim == "bass_bellow":
            self.bob = s * 1.0
            self.lean = -2.0 + s * 2.0
            self.head = -4.0 + s * 2.0
            self.left_arm = -20.0 + s * 3.0
            self.right_arm = -28.0 - s * 4.0
            self.weapon_angle = -76.0 + s * 6.0
            self.beard = s * 8.0
            self.mouth = 0.30 + max(0.0, s) * 0.08
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
            self.root_x = shake * 3.0 - hit * 5.0
            self.bob = -hit * 2.2
            self.lean = -14.0 * hit
            self.head = 10.0 * hit
            self.left_leg = -8.0 * hit
            self.right_leg = 8.0 * hit
            self.left_arm = 20.0 * hit
            self.right_arm = 14.0 * hit
            self.weapon_angle = -18.0 + hit * 20.0
            self.beard = -14.0 * hit
            self.mouth = 0.10 * hit
        elif anim == "death":
            tt = _ease(t)
            self.root_x = tt * 18.0
            self.root_y = tt * 12.0
            self.lean = -84.0 * tt
            self.head = -18.0 * tt
            self.left_leg = _lerp(-2.0, 18.0, tt)
            self.right_leg = _lerp(2.0, -18.0, tt)
            self.left_arm = _lerp(0.0, 50.0, tt)
            self.right_arm = _lerp(0.0, -44.0, tt)
            self.weapon_angle = _lerp(-18.0, 22.0, tt)
            self.weapon_len = tt * 10.0
            self.beard = -20.0 * tt
            self.x_eye = tt > 0.58


# --- Drawn as a rig (``shape_rig``): each rigid piece is painted once at its
# rest place and turned into the frame; limbs are bones of a fixed length. ---

#: Where a bone piece's root sits on its rest canvas (work pixels); a
#: weapon reaching both ways is painted about the canvas middle.
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


_CANVAS = (FRAME_SIZE[0] * 8, FRAME_SIZE[1] * 8)
_REST_ROOT: Point = (WORK_FRAME_SIZE[0] * 0.48, WORK_FRAME_SIZE[1] * 0.80)
_REST_HEAD: Point = (_REST_ROOT[0] - 4, _REST_ROOT[1] - 304)
_THIGH, _SHIN = 36.0, 34.0


def _joints(anim: str, idx: int, n: int):
    return _viking_heavy_warrior_rig.evaluate(Pose(anim, idx, n), WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])


def _chains(J) -> dict:
    return {
        "far_arm": (J.far_shoulder, J.far_elbow, J.far_hand),
        "near_arm": (J.near_shoulder, J.near_elbow, J.near_hand),
    }


def _P0(x: float, y: float) -> Point:
    return (_REST_ROOT[0] + x, _REST_ROOT[1] + y)


def _H0(x: float, y: float) -> Point:
    return (_REST_HEAD[0] + x, _REST_HEAD[1] + y)


def _draw_leg(img: Image.Image, hip: Point, ang: float, lift: float, *, front: bool, side: str) -> Point:
    """Thigh and shin bones (fixed lengths) and the sandal riding the ankle."""
    knee = (hip[0] + _THIGH * math.cos(math.radians(ang)), hip[1] + _THIGH * math.sin(math.radians(ang)))
    reach = (knee[0] + _SHIN * math.cos(math.radians(ang + 8)), knee[1] + _SHIN * math.sin(math.radians(ang + 8)) - lift)
    shin_deg = _deg(knee, reach)
    ankle = (knee[0] + _SHIN * math.cos(math.radians(shin_deg)), knee[1] + _SHIN * math.sin(math.radians(shin_deg)))
    col = PANTS if front else PANTS_SHADE
    width = 7.2 if front else 6.6
    _put(img, _bone_piece(("thigh",), _THIGH, width, col, OUTLINE, 1.0), hip, ang, f"{side}_thigh")
    _put(img, _bone_piece(("shin",), _SHIN, width, col, OUTLINE, 1.0, cap=True), knee, shin_deg, f"{side}_shin")

    def sandal(d) -> None:
        x, y = _BONE_O
        _poly(d, [(x - 10, y - 4), (x + 10, y - 4), (x + 14, y + 4), (x + 6, y + 10), (x - 10, y + 8)], SANDAL, OUTLINE, 0.8)

    _put(img, _rest(("sandal",), sandal, _BONE_O), ankle, 0.0, f"{side}_sandal")
    return ankle


def _draw_beefy_arm(img: Image.Image, limb: str, shoulder: Point, elbow_ref: Point, hand: Point, skin: RGBA) -> None:
    """Upper arm and forearm bones of fixed length, bent at the painter's
    elbow; the muscle bulges ride their bone."""
    elbow, l1, l2 = _limb(_chains, limb, shoulder, elbow_ref, hand)
    O = _BONE_O

    def upper(d) -> None:
        end = (O[0] + l1, O[1])
        _line(d, [O, end], skin, 10.8)
        _line(d, [O, end], OUTLINE, 1.15)
        mid = (O[0] + l1 / 2.0, O[1])
        _ellipse(d, mid[0], mid[1], 10.6, 8.8, skin, OUTLINE, 0.45)
        _line(d, [(mid[0] - 7, mid[1] - 4), (mid[0] + 7, mid[1] + 4)], GOLD, 0.9)

    def fore(d) -> None:
        end = (O[0] + l2, O[1])
        _circle(d, O, 5.4, skin, skin, 0.1)
        _line(d, [O, end], skin, 10.8)
        _line(d, [O, end], OUTLINE, 1.15)
        _ellipse(d, O[0] + l2 / 2.0, O[1], 9.0, 7.4, skin, OUTLINE, 0.4)

    _put(img, _rest(("upper_arm", limb, l1, skin), upper, O), shoulder, _deg(shoulder, elbow), f"{limb}_upper")
    _put(img, _rest(("forearm", limb, l2, skin), fore, O), elbow, _deg(elbow, hand), f"{limb}_fore")


def _paint_double_axe(draw: ImageDraw.ImageDraw, mid: Point, length: float) -> None:
    """The double axe at angle 0 (haft along +x) gripped at ``mid``."""
    angle = 0.0
    tail = (mid[0] - length * 0.46, mid[1])
    tip = (mid[0] + length * 0.56, mid[1])
    _line(draw, [tail, tip], WOOD, 3.1)
    _line(draw, [tail, tip], OUTLINE, 0.55)
    for anchor, sign in [(tip, 1), (tail, -1)]:
        hx, hy = anchor
        forward = angle if sign > 0 else angle + 180

        def at(r: float, deg: float) -> Point:
            return (hx + r * math.cos(math.radians(forward + deg)), hy + r * math.sin(math.radians(forward + deg)))

        p1, left, right, outer1, outer2 = at(6, 0), at(10, 90), at(10, -90), at(36, 34), at(36, -34)
        _poly(draw, [p1, outer1, left], STEEL, OUTLINE, 0.55)
        _poly(draw, [p1, outer2, right], STEEL_SHADE, OUTLINE, 0.55)


def _paint_body(draw: ImageDraw.ImageDraw) -> None:
    P = _P0
    _poly(draw, [P(-48, -180), P(44, -180), P(56, -52), P(16, -4), P(-26, -4), P(-60, -58)], TUNIC_SHADE, OUTLINE, 1.0)
    _poly(draw, [P(-60, -274), P(14, -282), P(62, -246), P(74, -180), P(58, -124), P(2, -102), P(-50, -124), P(-74, -190)], TUNIC, OUTLINE, 1.2)
    _poly(draw, [P(-38, -212), P(28, -214), P(50, -176), P(40, -130), P(0, -108), P(-40, -126), P(-50, -174)], FUR, OUTLINE, 0.8)
    _poly(draw, [P(-50, -258), P(14, -276), P(58, -250), P(74, -220), P(46, -202), P(6, -212), P(-36, -198), P(-64, -222)], FUR, OUTLINE, 0.9)
    for x, y in [(-34, -230), (-14, -238), (8, -232), (28, -222)]:
        _line(draw, [P(x, y), P(x + 6, y + 9)], FUR_SHADE, 0.9)
    _poly(draw, [P(-42, -132), P(34, -132), P(34, -114), P(-42, -114)], LEATHER, OUTLINE, 0.7)
    _ellipse(draw, P(-4, -123)[0], P(-4, -123)[1], 7, 5, GOLD, OUTLINE, 0.35)


def _paint_tunic_front(draw: ImageDraw.ImageDraw) -> None:
    P = _P0
    _poly(draw, [P(-52, -176), P(46, -176), P(56, -48), P(18, 0), P(-28, -2), P(-62, -54)], TUNIC, OUTLINE, 1.0)
    for x in [-24, -4, 16, 34]:
        _line(draw, [P(x, -166), P(x + 6, -8)], TUNIC_SHADE, 0.9)


def _paint_head(draw: ImageDraw.ImageDraw, blink: bool, x_eye: bool, mouth: float, beard_sway: float) -> None:
    H = _H0
    _poly(draw, [H(-20, -14), H(-46, -34), H(-58, -18), H(-46, 2), H(-24, -2)], HORN, OUTLINE, 0.55)
    _poly(draw, [H(18, -16), H(44, -36), H(56, -20), H(46, 2), H(22, -4)], HORN, OUTLINE, 0.55)
    _line(draw, [H(-36, -22), H(-48, -20)], HORN_SHADE, 0.45)
    _line(draw, [H(34, -24), H(46, -22)], HORN_SHADE, 0.45)
    _poly(draw, [H(-28, -8), H(-24, -28), H(18, -28), H(28, -10), H(28, 18), H(12, 30), H(-12, 24), H(-28, 12)], HAIR_SHADE, OUTLINE, 0.7)
    _poly(draw, [H(-26, -8), H(-20, -34), H(20, -34), H(28, -10), H(24, 18), H(10, 26), H(-12, 26), H(-28, 10)], STEEL, OUTLINE, 0.9)
    _poly(draw, [H(2, -10), H(10, -2), H(6, 18), H(-2, 12)], STEEL_SHADE, OUTLINE, 0.35)
    _poly(draw, [H(-22, -2), H(-16, -20), H(12, -20), H(22, -2), H(18, 16), H(8, 24), H(-8, 24), H(-22, 12)], SKIN, OUTLINE, 0.8)
    _poly(draw, [H(-10, 10), H(-2, 14), H(0, 10), H(-4, 6)], HAIR, OUTLINE, 0.2)
    _poly(draw, [H(2, 10), H(10, 14), H(14, 10), H(6, 6)], HAIR, OUTLINE, 0.2)
    b = beard_sway
    beard = [H(-18, 14), H(-2, 28 + b * 0.1), H(16, 22 + b * 0.08), H(22, 44 + b * 0.1), H(6, 64 + b * 0.1), H(-10, 58 + b * 0.1), H(-22, 34)]
    _poly(draw, beard, BEARD, OUTLINE, 0.8)
    for frac in [0.3, 0.6]:
        bx = _lerp(beard[0][0], beard[-2][0], frac)
        by = _lerp(beard[0][1], beard[-2][1], frac)
        _line(draw, [(bx - 3, by - 2), (bx + 3, by + 4)], BEARD_SHADE, 0.35)
    if x_eye:
        _line(draw, [H(-10, 0), H(-3, 7)], OUTLINE, 0.8)
        _line(draw, [H(-10, 7), H(-3, 0)], OUTLINE, 0.8)
        _line(draw, [H(6, 0), H(13, 7)], OUTLINE, 0.8)
        _line(draw, [H(6, 7), H(13, 0)], OUTLINE, 0.8)
    elif blink:
        _line(draw, [H(-12, 1), H(-4, 1)], OUTLINE, 0.7)
        _line(draw, [H(6, 1), H(14, 1)], OUTLINE, 0.7)
    else:
        _ellipse(draw, H(-8, 1)[0], H(-8, 1)[1], 3.8, 3.0, EYE, OUTLINE, 0.35)
        _ellipse(draw, H(10, 1)[0], H(10, 1)[1], 3.8, 3.0, EYE, OUTLINE, 0.35)
        _circle(draw, H(-7, 1), 1.0, PUPIL, PUPIL, 0.1)
        _circle(draw, H(11, 1), 1.0, PUPIL, PUPIL, 0.1)
    _line(draw, [H(-14, -6), H(-4, -8)], OUTLINE, 0.45)
    _line(draw, [H(6, -8), H(16, -6)], OUTLINE, 0.45)
    if mouth > 0.03:
        _ellipse(draw, H(2, 20)[0], H(2, 20)[1], 6.0, 3.2 + mouth * 12.0, MOUTH, OUTLINE, 0.35)
        if mouth > 0.14:
            _poly(draw, [H(-2, 20), H(2, 28), H(6, 20)], TONGUE, OUTLINE, 0.2)
    else:
        _line(draw, [H(-2, 18), H(4, 20), H(10, 18)], MOUTH, 0.7)


def _render_frame(anim: str, idx: int, n: int) -> Image.Image:
    img = Image.new("RGBA", _CANVAS, (0, 0, 0, 0))
    pose = Pose(anim, idx, n)

    J = _viking_heavy_warrior_rig.evaluate(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    root = J.root
    body_ang = J.body_ang
    head_root = J.head_root
    head_ang = J.head_ang

    def H(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, head_ang)
        return (head_root[0] + rx, head_root[1] + ry)

    _draw_leg(img, J.far_hip, 94 + pose.right_leg, pose.right_lift, front=False, side="far")
    # tunic back, torso, fur and belt: one piece turned with the lean
    _put(img, _rest(("body",), _paint_body, _REST_ROOT), root, body_ang, "body")

    far_hand = J.far_hand
    _draw_beefy_arm(img, "far_arm", J.far_shoulder, J.far_elbow, far_hand, SKIN_SHADE)

    # the head: one piece per face (the beard sways in a few steps)
    mouth = round(pose.mouth, 2)
    beard_sway = _rig.q(pose.beard, 5.0)
    head = _rest(
        ("head", pose.blink, pose.x_eye, mouth, beard_sway),
        lambda d: _paint_head(d, pose.blink, pose.x_eye, mouth, beard_sway),
        _REST_HEAD,
    )
    _put(img, head, head_root, head_ang, "head")

    near_foot = _draw_leg(img, J.near_hip, 94 + pose.left_leg, pose.left_lift, front=True, side="near")
    _put(img, _rest(("tunic_front",), _paint_tunic_front, _REST_ROOT), root, body_ang, "tunic_front")

    near_hand = J.near_hand
    _draw_beefy_arm(img, "near_arm", J.near_shoulder, J.near_elbow, near_hand, SKIN)

    mid = ((near_hand[0] + far_hand[0]) / 2.0, (near_hand[1] + far_hand[1]) / 2.0)
    axe_len = _rig.q(122 + pose.weapon_len, 2.0)
    _put(img, _rest(("axe", axe_len), lambda d: _paint_double_axe(d, _MID_O, axe_len), _MID_O), mid, pose.weapon_angle, "axe")
    axe_tip = (mid[0] + axe_len * 0.56 * math.cos(math.radians(pose.weapon_angle)), mid[1] + axe_len * 0.56 * math.sin(math.radians(pose.weapon_angle)))
    for side, hand, skin in (("near", near_hand, SKIN), ("far", far_hand, SKIN_SHADE)):
        def grip(d, skin=skin) -> None:
            x, y = _BONE_O
            _circle(d, _BONE_O, 4.6, skin, OUTLINE, 0.3)
            _line(d, [(x - 5, y - 2), (x + 5, y + 2)], LEATHER_DARK, 0.45)

        _put(img, _rest(("grip", side), grip, _BONE_O), hand, 0.0, f"{side}_grip")

    # effects change every frame: one raster each
    if anim in {"march", "helm_bash"} and (pose.left_lift > 0.5 or pose.right_lift > 0.5):
        def dust(draw) -> None:
            for dx in [-18, 0, 14]:
                c = (near_foot[0] + dx, near_foot[1] + 8)
                _poly(draw, [(c[0] - 3, c[1]), (c[0], c[1] - 4), (c[0] + 4, c[1] - 1), (c[0] + 1, c[1] + 3)], DUST, None, 0)

        _fx_layer(img, dust, "fx_dust")

    def arcs(draw) -> None:
        if anim == "axe_cleave" and pose.impact > 0.18:
            cx, cy = axe_tip
            draw.arc((_s(cx - 54), _s(cy - 30), _s(cx + 44), _s(cy + 50)), 194, 344, fill=FX, width=_s(3.4))
        if anim == "helm_bash" and pose.impact > 0.18:
            cx, cy = H(0, -2)
            draw.arc((_s(cx - 34), _s(cy - 24), _s(cx + 54), _s(cy + 32)), 210, 350, fill=FX, width=_s(3.2))
        if anim == "bass_bellow" and pose.mouth > 0.2:
            cx, cy = H(6, 20)
            for expand in [0, 14]:
                box = (_s(cx - 18 - expand), _s(cy - 20 - expand * 0.6), _s(cx + 42 + expand), _s(cy + 20 + expand * 0.6))
                draw.arc(box, 330, 30, fill=FX, width=_s(2.1))

    if (anim in {"axe_cleave", "helm_bash"} and pose.impact > 0.18) or (anim == "bass_bellow" and pose.mouth > 0.2):
        _fx_layer(img, arcs, "fx_arc")

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
        outputs[k]
        for k in [
            "spritesheet",
            "yaml",
            "ron",
            "preview",
            "canonical",
            "canonical_transparent",
        ]
    ] + list(parts.values())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the standalone opera-style heavy Viking warrior sprite sheet."
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
