"""Standalone generator for an attacking Viking man warrior sprite sheet.

Concept:
- broad, bearded Viking man warrior / raider
- heavy two-handed dane axe for a distinct silhouette
- fur mantle, leather boots, tunic, bracers
- aggressive attack-forward poses suited to a side scroller

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

ACTOR_METADATA = {
    "actor": {"character_id": "npc_viking_warrior", "display_name": "Viking Warrior"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
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
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "striker_swipe"},
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

from . import _viking_warrior_rig as _viking_warrior_rig
from . import _solo_shape_rig as _rig

TARGET_NAME = "viking_warrior"
# Files the tack-on installer copies into the sandbox sprites dir.
# Names match what `build_sheet` writes (target_spritesheet.{png,yaml,ron}).
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
]
FRAME_SIZE = (320, 320)
WORK_FRAME_SIZE = (640, 640)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 128),
    ("walk", 8, 96),
    ("cleave", 7, 80),
    ("charge", 7, 80),
    ("leap_chop", 7, 82),
    ("roar", 6, 106),
    ("hurt", 4, 90),
    ("death", 8, 112),
]

OUTLINE = (28, 22, 18, 255)
SKIN = (214, 166, 132, 255)
SKIN_SHADE = (172, 126, 98, 255)
HAIR = (170, 112, 58, 255)
HAIR_SHADE = (126, 80, 42, 255)
BEARD = (136, 86, 48, 255)
FUR = (208, 200, 184, 255)
FUR_SHADE = (164, 154, 138, 255)
TUNIC = (76, 92, 124, 255)
TUNIC_SHADE = (56, 68, 92, 255)
PANTS = (92, 66, 48, 255)
PANTS_SHADE = (70, 50, 36, 255)
LEATHER = (112, 76, 46, 255)
LEATHER_DARK = (82, 56, 34, 255)
STEEL = (190, 198, 208, 255)
STEEL_SHADE = (130, 140, 152, 255)
WOOD = (118, 82, 52, 255)
GOLD = (212, 174, 82, 255)
BOOT = (50, 38, 30, 255)
EYE = (242, 240, 236, 255)
PUPIL = (34, 34, 40, 255)
MOUTH = (102, 64, 66, 255)
TONGUE = (194, 94, 108, 255)
FX = (245, 232, 164, 150)
DUST = (134, 116, 92, 130)


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
        self.hair = 0.0
        self.mouth = 0.0
        self.impact = 0.0
        self.dead_t = 0.0
        self.blink = False
        self.x_eye = False

        if anim == "idle":
            self.bob = s * 1.2
            self.lean = s * 1.3
            self.head = -2.0 + s * 1.2
            self.left_leg = -2.0 + c * 1.4
            self.right_leg = 2.0 - c * 1.4
            self.left_arm = -2.0 + s * 2.0
            self.right_arm = 2.0 - s * 2.0
            self.weapon_angle = -44.0 + s * 4.0
            self.weapon_len = 0.0
            self.hair = s * 2.0
            self.blink = frame_idx == nframes - 2
        elif anim == "walk":
            self.root_x = s * 2.0
            self.bob = abs(s) * 2.8 - 0.5
            self.lean = s * 2.0
            self.head = -2.0 - s * 1.0
            self.left_leg = -22.0 * s
            self.right_leg = 22.0 * s
            self.left_lift = max(0.0, -s) * 8.0
            self.right_lift = max(0.0, s) * 8.0
            self.left_arm = 12.0 * s - 4.0
            self.right_arm = -12.0 * s + 4.0
            self.weapon_angle = -48.0 - s * 10.0
            self.hair = -s * 6.0
        elif anim == "cleave":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-10.0, 16.0, tt)
            self.bob = -hit * 2.0
            self.lean = _lerp(-12.0, 16.0, tt)
            self.head = _lerp(-8.0, 10.0, tt)
            self.left_leg = _lerp(-12.0, 12.0, tt)
            self.right_leg = _lerp(10.0, -6.0, tt)
            self.left_arm = _lerp(-46.0, 26.0, tt)
            self.right_arm = _lerp(-18.0, 34.0, tt)
            self.weapon_angle = _lerp(-120.0, 24.0, tt)
            self.weapon_len = hit * 10.0
            self.hair = _lerp(10.0, -10.0, tt)
            self.mouth = 0.12 + hit * 0.06
            self.impact = hit
        elif anim == "charge":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-14.0, 26.0, tt)
            self.bob = -hit * 2.0
            self.lean = _lerp(-10.0, 20.0, tt)
            self.head = _lerp(-6.0, 8.0, tt)
            self.left_leg = _lerp(-18.0, 16.0, tt)
            self.right_leg = _lerp(12.0, -10.0, tt)
            self.left_lift = _lerp(0.0, 5.0, tt)
            self.right_lift = _lerp(0.0, 2.0, tt)
            self.left_arm = _lerp(-14.0, 8.0, tt)
            self.right_arm = _lerp(-10.0, 14.0, tt)
            self.weapon_angle = _lerp(-54.0, -6.0, tt)
            self.weapon_len = hit * 6.0
            self.hair = _lerp(6.0, -6.0, tt)
            self.mouth = 0.10
            self.impact = hit
        elif anim == "leap_chop":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-8.0, 14.0, tt)
            self.root_y = _lerp(0.0, -10.0, hit)
            self.bob = -hit * 4.0
            self.lean = _lerp(-8.0, 14.0, tt)
            self.head = _lerp(-6.0, 10.0, tt)
            self.left_leg = _lerp(-8.0, 18.0, tt)
            self.right_leg = _lerp(10.0, -12.0, tt)
            self.left_lift = hit * 6.0
            self.right_lift = hit * 9.0
            self.left_arm = _lerp(-58.0, 32.0, tt)
            self.right_arm = _lerp(-26.0, 36.0, tt)
            self.weapon_angle = _lerp(-132.0, 36.0, tt)
            self.weapon_len = hit * 12.0
            self.hair = _lerp(12.0, -12.0, tt)
            self.mouth = 0.14
            self.impact = hit
        elif anim == "roar":
            self.bob = s * 0.8
            self.lean = -2.0 + s * 2.0
            self.head = -4.0 + s * 2.0
            self.left_leg = -2.0
            self.right_leg = 3.0
            self.left_arm = -12.0 + s * 4.0
            self.right_arm = -18.0 - s * 3.0
            self.weapon_angle = -96.0 + s * 6.0
            self.weapon_len = 10.0
            self.hair = s * 8.0
            self.mouth = 0.26 + max(0.0, s) * 0.08
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
            self.root_x = shake * 3.0 - hit * 3.0
            self.bob = -hit * 2.0
            self.lean = -12.0 * hit
            self.head = 8.0 * hit
            self.left_leg = -8.0 * hit
            self.right_leg = 8.0 * hit
            self.left_arm = 20.0 * hit
            self.right_arm = 12.0 * hit
            self.weapon_angle = -40.0 + hit * 12.0
            self.hair = -12.0 * hit
            self.mouth = 0.10 * hit
        elif anim == "death":
            tt = _ease(t)
            self.dead_t = tt
            self.root_x = tt * 18.0
            self.root_y = tt * 10.0
            self.bob = -tt * 4.0
            self.lean = -80.0 * tt
            self.head = -18.0 * tt
            self.left_leg = _lerp(-2.0, 18.0, tt)
            self.right_leg = _lerp(2.0, -18.0, tt)
            self.left_arm = _lerp(-4.0, 52.0, tt)
            self.right_arm = _lerp(4.0, -44.0, tt)
            self.weapon_angle = _lerp(-46.0, -10.0, tt)
            self.weapon_len = tt * 8.0
            self.hair = -18.0 * tt
            self.x_eye = tt > 0.56


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


_CANVAS = (WORK_FRAME_SIZE[0] * SUPER, WORK_FRAME_SIZE[1] * SUPER)
_REST_ROOT: Point = (WORK_FRAME_SIZE[0] * 0.47, WORK_FRAME_SIZE[1] * 0.79)
_REST_HEAD: Point = (_REST_ROOT[0] - 2, _REST_ROOT[1] - 248)
_THIGH, _SHIN = 42.0, 40.0
#: The axe's angle in the idle pose: its head and spike are painted as the
#: painter drew them there, and turn with the haft.
_AXE_REST = -44.0


def _joints(anim: str, frame_idx: int, nframes: int):
    return _viking_warrior_rig.evaluate(Pose(anim, frame_idx, nframes), WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])


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
    """Thigh and shin bones (fixed lengths) and the boot riding the ankle."""
    knee = (hip[0] + _THIGH * math.cos(math.radians(ang)), hip[1] + _THIGH * math.sin(math.radians(ang)))
    reach = (knee[0] + _SHIN * math.cos(math.radians(ang + 8)), knee[1] + _SHIN * math.sin(math.radians(ang + 8)) - lift)
    shin_deg = _deg(knee, reach)
    ankle = (knee[0] + _SHIN * math.cos(math.radians(shin_deg)), knee[1] + _SHIN * math.sin(math.radians(shin_deg)))
    col = PANTS if front else PANTS_SHADE
    width = 8.6 if front else 7.6
    _put(img, _bone_piece(("thigh",), _THIGH, width, col, OUTLINE, 1.1), hip, ang, f"{side}_thigh")
    _put(img, _bone_piece(("shin",), _SHIN, width, col, OUTLINE, 1.1, cap=True), knee, shin_deg, f"{side}_shin")

    def boot(d) -> None:
        x, y = _BONE_O
        _poly(d, [(x - 8, y - 5), (x + 10, y - 5), (x + 15, y + 4), (x + 6, y + 10), (x - 8, y + 8)], BOOT, OUTLINE, 0.8)

    _put(img, _rest(("boot",), boot, _BONE_O), ankle, 0.0, f"{side}_boot")
    return ankle


def _draw_arm(img: Image.Image, limb: str, shoulder: Point, elbow_ref: Point, hand: Point, skin: RGBA, width: float, line_w: float) -> None:
    """Two bones of fixed length, bent at the painter's elbow (a round
    elbow, as the painter's curved polyline joint)."""
    elbow, l1, l2 = _limb(_chains, limb, shoulder, elbow_ref, hand)
    _put(img, _bone_piece((limb, 1, l1), l1, width, skin, OUTLINE, line_w), shoulder, _deg(shoulder, elbow), f"{limb}_upper")
    _put(img, _bone_piece((limb, 2, l2), l2, width, skin, OUTLINE, line_w, cap=True), elbow, _deg(elbow, hand), f"{limb}_fore")


def _paint_axe(draw: ImageDraw.ImageDraw, mid: Point, length: float) -> None:
    """The axe at angle 0 (haft along +x) gripped at ``mid``; head and spike
    are the painter's, turned back by the rest angle."""
    tail = (mid[0] - length * 0.45, mid[1])
    tip = (mid[0] + length * 0.55, mid[1])
    _line(draw, [tail, tip], WOOD, 3.2)
    _line(draw, [tail, tip], OUTLINE, 0.6)

    def at(origin: Point, dx: float, dy: float) -> Point:
        rx, ry = _rot(dx, dy, -_AXE_REST)
        return (origin[0] + rx, origin[1] + ry)

    _poly(draw, [at(tip, -4, -6), at(tip, 8, -18), at(tip, 26, -10), at(tip, 28, 6), at(tip, 10, 16), at(tip, -8, 8)], STEEL, OUTLINE, 0.7)
    _poly(draw, [at(tip, 2, -2), at(tip, 30, -10), at(tip, 42, 0), at(tip, 18, 16)], STEEL_SHADE, OUTLINE, 0.6)
    _poly(draw, [at(tail, -2, -2), at(tail, -16, -6), at(tail, -24, 2), at(tail, -12, 8)], STEEL_SHADE, OUTLINE, 0.5)
    _line(draw, [at(tip, 4, -12), at(tip, 18, 8)], (226, 230, 236, 255), 0.8)


def _paint_body(draw: ImageDraw.ImageDraw) -> None:
    P = _P0
    _poly(draw, [P(-24, -114), P(22, -114), P(28, -54), P(8, -16), P(-18, -20), P(-30, -60)], TUNIC_SHADE, OUTLINE, 1.0)
    _poly(draw, [P(-38, -214), P(8, -222), P(40, -200), P(50, -146), P(42, -106), P(12, -86), P(-22, -90), P(-44, -146)], TUNIC, OUTLINE, 1.2)
    _poly(draw, [P(-12, -198), P(18, -198), P(22, -122), P(2, -98), P(-18, -122), P(-22, -182)], TUNIC_SHADE, OUTLINE, 0.7)
    _poly(draw, [P(-34, -214), P(10, -224), P(40, -206), P(52, -176), P(30, -162), P(2, -170), P(-24, -158), P(-44, -176)], FUR, OUTLINE, 1.0)
    for x, y in [(-26, -192), (-10, -200), (8, -194), (24, -186)]:
        _line(draw, [P(x, y), P(x + 6, y + 8)], FUR_SHADE, 0.8)


def _paint_kilt_front(draw: ImageDraw.ImageDraw) -> None:
    P = _P0
    _poly(draw, [P(-28, -112), P(20, -112), P(26, -50), P(10, -12), P(-14, -14), P(-30, -56)], TUNIC, OUTLINE, 1.0)
    _line(draw, [P(-10, -104), P(-8, -20)], TUNIC_SHADE, 0.8)
    _line(draw, [P(6, -104), P(10, -18)], TUNIC_SHADE, 0.8)
    _poly(draw, [P(-28, -124), P(20, -124), P(20, -110), P(-28, -110)], LEATHER, OUTLINE, 0.7)
    _ellipse(draw, P(-4, -117)[0], P(-4, -117)[1], 5.0, 4.0, GOLD, OUTLINE, 0.3)


#: The hair tail at rest from its root (head-local), and how far its end
#: sways per unit of ``pose.hair``: it turns about its root by that.
_TAIL_ROOT: Point = (16.0, 4.0)
_TAIL = [(0.0, 0.0), (10.0, 14.0), (18.0, 30.0), (14.0, 50.0)]
_TAIL_SWAY = 0.22


def _paint_hair_tail(draw: ImageDraw.ImageDraw) -> None:
    tail = [_H0(_TAIL_ROOT[0] + x, _TAIL_ROOT[1] + y) for x, y in _TAIL]
    _line(draw, tail, HAIR, 6.0)
    _line(draw, tail, OUTLINE, 0.7)


def _paint_hair_back(draw: ImageDraw.ImageDraw) -> None:
    H = _H0
    _poly(draw, [H(-24, -10), H(-14, -36), H(10, -38), H(28, -20), H(30, 8), H(16, 24), H(-4, 20), H(-24, 8)], HAIR_SHADE, OUTLINE, 0.8)


def _paint_head(draw: ImageDraw.ImageDraw, blink: bool, x_eye: bool, mouth: float) -> None:
    H = _H0
    _poly(draw, [H(-18, -18), H(-4, -32), H(18, -30), H(30, -12), H(26, 2), H(8, 8), H(-12, 2)], STEEL, OUTLINE, 0.8)
    _poly(draw, [H(4, -18), H(10, -6), H(6, 14), H(0, 8)], STEEL_SHADE, OUTLINE, 0.35)
    _poly(draw, [H(-18, -10), H(-12, -26), H(10, -28), H(24, -16), H(24, 6), H(12, 18), H(-6, 18), H(-20, 6)], SKIN, OUTLINE, 0.9)
    _poly(draw, [H(-12, 2), H(0, 10), H(12, 8), H(22, 2), H(18, 28), H(6, 42), H(-6, 38), H(-16, 20)], BEARD, OUTLINE, 0.8)
    _poly(draw, [H(-8, 6), H(-2, 10), H(2, 8), H(-2, 2)], HAIR, OUTLINE, 0.25)
    _poly(draw, [H(2, 8), H(10, 10), H(14, 6), H(6, 2)], HAIR, OUTLINE, 0.25)
    if x_eye:
        _line(draw, [H(-8, -2), H(-1, 5)], OUTLINE, 0.8)
        _line(draw, [H(-8, 5), H(-1, -2)], OUTLINE, 0.8)
        _line(draw, [H(8, -3), H(15, 4)], OUTLINE, 0.8)
        _line(draw, [H(8, 4), H(15, -3)], OUTLINE, 0.8)
    elif blink:
        _line(draw, [H(-10, 0), H(-2, 0)], OUTLINE, 0.7)
        _line(draw, [H(8, -1), H(16, -1)], OUTLINE, 0.7)
    else:
        _ellipse(draw, H(-6, 0)[0], H(-6, 0)[1], 3.8, 2.8, EYE, OUTLINE, 0.4)
        _ellipse(draw, H(12, -1)[0], H(12, -1)[1], 3.8, 2.8, EYE, OUTLINE, 0.4)
        _circle(draw, H(-5, 0), 1.0, PUPIL, PUPIL, 0.1)
        _circle(draw, H(13, -1), 1.0, PUPIL, PUPIL, 0.1)
    _line(draw, [H(-11, -8), H(-2, -10)], OUTLINE, 0.5)
    _line(draw, [H(8, -9), H(16, -10)], OUTLINE, 0.5)
    if mouth > 0.03:
        _ellipse(draw, H(4, 12)[0], H(4, 12)[1], 5.0, 2.6 + mouth * 10.0, MOUTH, OUTLINE, 0.4)
        if mouth > 0.15:
            _poly(draw, [H(0, 12), H(4, 18), H(8, 12)], TONGUE, OUTLINE, 0.2)
    else:
        _line(draw, [H(-1, 12), H(5, 14), H(11, 12)], MOUTH, 0.7)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", _CANVAS, (0, 0, 0, 0))
    pose = Pose(anim, frame_idx, nframes)

    # Joints come from the explicit skeleton (see _viking_warrior_rig).
    J = _viking_warrior_rig.evaluate(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    root = J.root
    body_ang = J.body_ang
    head_root = J.head_root
    head_ang = J.head_ang

    def H(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, head_ang)
        return (head_root[0] + rx, head_root[1] + ry)

    _draw_leg(img, J.far_hip, 92 + pose.right_leg, pose.right_lift, front=False, side="far")
    # hips, torso and fur: one piece turned with the lean
    _put(img, _rest(("body",), _paint_body, _REST_ROOT), root, body_ang, "body")

    far_hand = J.far_hand
    _draw_arm(img, "far_arm", J.far_shoulder, J.far_elbow, far_hand, SKIN_SHADE, 7.0, 0.95)

    # head: hair behind, the tail swaying about its root, the face
    _put(img, _rest(("hair_back",), _paint_hair_back, _REST_HEAD), head_root, head_ang, "hair_back")
    turn = -math.degrees(math.atan2(pose.hair * _TAIL_SWAY, _TAIL[-1][1]))
    _put(img, _rest(("hair_tail",), _paint_hair_tail, _H0(*_TAIL_ROOT)), H(*_TAIL_ROOT), head_ang + turn, "hair_tail")
    mouth = round(pose.mouth, 2)
    head = _rest(("head", pose.blink, pose.x_eye, mouth), lambda d: _paint_head(d, pose.blink, pose.x_eye, mouth), _REST_HEAD)
    _put(img, head, head_root, head_ang, "head")

    near_foot = _draw_leg(img, J.near_hip, 92 + pose.left_leg, pose.left_lift, front=True, side="near")
    _put(img, _rest(("kilt_front",), _paint_kilt_front, _REST_ROOT), root, body_ang, "kilt_front")

    # near arm / both hands grip axe shaft
    near_hand = J.near_hand
    _draw_arm(img, "near_arm", J.near_shoulder, J.near_elbow, near_hand, SKIN, 7.2, 1.0)
    mid = ((near_hand[0] + far_hand[0]) / 2.0, (near_hand[1] + far_hand[1]) / 2.0)
    axe_len = _rig.q(88 + pose.weapon_len, 2.0)
    _put(img, _rest(("axe", axe_len), lambda d: _paint_axe(d, _MID_O, axe_len), _MID_O), mid, pose.weapon_angle, "axe")
    axe_tip = (mid[0] + axe_len * 0.55 * math.cos(math.radians(pose.weapon_angle)), mid[1] + axe_len * 0.55 * math.sin(math.radians(pose.weapon_angle)))

    # hand grips over shaft, with their arm bands
    for side, hand, skin, band in (("near", near_hand, SKIN, ((-8, -2), (5, 2))), ("far", far_hand, SKIN_SHADE, ((-7, -2), (4, 1)))):
        def grip(d, skin=skin, band=band) -> None:
            x, y = _BONE_O
            _circle(d, _BONE_O, 4.5, skin, OUTLINE, 0.35)
            _line(d, [(x - 5, y - 2), (x + 5, y + 2)], LEATHER_DARK, 0.5)

        _put(img, _rest(("grip", side), grip, _BONE_O), hand, 0.0, f"{side}_grip")
    for side, hand, band in (("near", near_hand, ((-8, -2), (5, 2))), ("far", far_hand, ((-7, -2), (4, 1)))):
        def armband(d, band=band) -> None:
            x, y = _BONE_O
            _line(d, [(x + band[0][0], y + band[0][1]), (x + band[1][0], y + band[1][1])], GOLD, 0.6)

        _put(img, _rest(("band", side), armband, _BONE_O), hand, 0.0, f"{side}_band")

    # effects change every frame: one raster each
    def arcs(draw) -> None:
        cx, cy = axe_tip
        if anim in {"cleave", "leap_chop"}:
            draw.arc((_s(cx - 48), _s(cy - 26), _s(cx + 40), _s(cy + 44)), 195, 344, fill=FX, width=_s(3.6))
        else:
            draw.arc((_s(cx - 24), _s(cy - 20), _s(cx + 64), _s(cy + 28)), 215, 350, fill=FX, width=_s(3.2))

    if anim in {"cleave", "leap_chop", "charge"} and pose.impact > 0.18:
        _fx_layer(img, arcs, "fx_arc")
    if anim in {"walk", "charge", "leap_chop"} and (pose.left_lift > 0.5 or pose.right_lift > 0.5):
        def dust(draw) -> None:
            for dx in [-20, 0, 18]:
                c = (near_foot[0] + dx, near_foot[1] + 8)
                _poly(draw, [(c[0] - 3, c[1]), (c[0], c[1] - 4), (c[0] + 4, c[1] - 1), (c[0] + 1, c[1] + 3)], DUST, None, 0)

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
        description="Render the standalone Viking Warrior sprite sheet."
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
