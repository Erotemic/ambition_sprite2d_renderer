"""Standalone generator for an attacking Viking lady warrior sprite sheet.

Concept:
- a fierce shieldmaiden / viking lady warrior
- broad round shield, one-handed axe, fur mantle, braided hair
- attack-forward moveset suited to a side scroller
- readable silhouette with strong weapon and shield posing

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
from . import _viking_shieldmaiden_rig
from . import _solo_shape_rig as _rig

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_viking_shieldmaiden",
        "display_name": "Viking Shieldmaiden",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "enemy", "combatant", "viking", "shield"],
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
    "tags": ["story", "humanoid", "enemy", "combatant", "viking", "shield"],
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
        "shield_center": {
            "source": "explicit.profile.viking",
            "point": {"x": 46.0, "y": 62.0},
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
        "action.defend.block": {"animation": "block", "events": []},
    },
}


RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "viking_shieldmaiden"
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
    ("axe_swing", 7, 82),
    ("shield_bash", 6, 84),
    ("overhead_chop", 7, 80),
    ("battle_cry", 6, 108),
    ("hurt", 4, 92),
    ("death", 8, 112),
]

OUTLINE = (28, 22, 20, 255)
SKIN = (220, 178, 146, 255)
SKIN_SHADE = (182, 140, 114, 255)
HAIR = (194, 154, 78, 255)
HAIR_SHADE = (148, 112, 54, 255)
FUR = (214, 206, 188, 255)
FUR_SHADE = (170, 162, 146, 255)
TUNIC = (106, 74, 120, 255)
TUNIC_SHADE = (76, 52, 90, 255)
SKIRT = (56, 82, 126, 255)
SKIRT_SHADE = (40, 62, 98, 255)
LEATHER = (112, 76, 48, 255)
LEATHER_DARK = (82, 54, 34, 255)
STEEL = (188, 196, 206, 255)
STEEL_SHADE = (132, 142, 154, 255)
GOLD = (214, 176, 84, 255)
SHIELD_RED = (146, 56, 50, 255)
SHIELD_RED_DARK = (106, 38, 36, 255)
BOOT = (54, 40, 32, 255)
MOUTH = (108, 64, 68, 255)
TONGUE = (194, 98, 112, 255)
EYE = (242, 242, 238, 255)
PUPIL = (34, 34, 40, 255)
FX = (246, 230, 162, 150)
DUST = (130, 116, 92, 130)


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
        self.weapon_arm = 0.0
        self.shield_arm = 0.0
        self.weapon_raise = 0.0
        self.shield_push = 0.0
        self.hair = 0.0
        self.mouth = 0.0
        self.impact = 0.0
        self.dead_t = 0.0
        self.blink = False
        self.x_eye = False

        if anim == "idle":
            self.bob = s * 1.4
            self.lean = s * 1.5
            self.head = -2.0 + s * 1.2
            self.left_leg = -2.0 + c * 1.5
            self.right_leg = 2.0 - c * 1.4
            self.weapon_arm = 4.0 - s * 3.0
            self.shield_arm = -4.0 + s * 2.0
            self.hair = s * 3.0
            self.blink = frame_idx == nframes - 2
        elif anim == "walk":
            self.root_x = s * 2.2
            self.bob = abs(s) * 2.8 - 0.5
            self.lean = s * 2.0
            self.head = -2.0 - s * 1.0
            self.left_leg = -22.0 * s
            self.right_leg = 22.0 * s
            self.left_lift = max(0.0, -s) * 8.0
            self.right_lift = max(0.0, s) * 8.0
            self.weapon_arm = -14.0 * s + 2.0
            self.shield_arm = 14.0 * s - 2.0
            self.hair = -s * 8.0
        elif anim == "axe_swing":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-6.0, 14.0, tt)
            self.bob = -hit * 2.0
            self.lean = _lerp(-10.0, 14.0, tt)
            self.head = _lerp(-6.0, 8.0, tt)
            self.left_leg = _lerp(-10.0, 10.0, tt)
            self.right_leg = _lerp(10.0, -4.0, tt)
            self.weapon_arm = _lerp(-58.0, 44.0, tt)
            self.shield_arm = _lerp(6.0, -14.0, tt)
            self.weapon_raise = hit
            self.hair = _lerp(10.0, -10.0, tt)
            self.mouth = 0.10 + hit * 0.06
            self.impact = hit
        elif anim == "shield_bash":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-12.0, 18.0, tt)
            self.bob = -hit * 2.0
            self.lean = _lerp(-8.0, 18.0, tt)
            self.head = _lerp(-4.0, 6.0, tt)
            self.left_leg = _lerp(-14.0, 12.0, tt)
            self.right_leg = _lerp(10.0, -6.0, tt)
            self.weapon_arm = _lerp(6.0, -16.0, tt)
            self.shield_arm = _lerp(-36.0, 24.0, tt)
            self.shield_push = hit
            self.hair = _lerp(6.0, -8.0, tt)
            self.mouth = 0.12
            self.impact = hit
        elif anim == "overhead_chop":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-6.0, 10.0, tt)
            self.root_y = _lerp(0.0, -3.0, tt)
            self.bob = -hit * 3.0
            self.lean = _lerp(-6.0, 12.0, tt)
            self.head = _lerp(-4.0, 10.0, tt)
            self.left_leg = _lerp(-6.0, 8.0, tt)
            self.right_leg = _lerp(8.0, -6.0, tt)
            self.weapon_arm = _lerp(-90.0, 70.0, tt)
            self.shield_arm = _lerp(-4.0, -18.0, tt)
            self.weapon_raise = hit
            self.hair = _lerp(12.0, -12.0, tt)
            self.mouth = 0.14
            self.impact = hit
        elif anim == "battle_cry":
            self.bob = s * 1.0
            self.lean = -2.0 + s * 2.0
            self.head = -4.0 + s * 2.0
            self.left_leg = -2.0
            self.right_leg = 4.0
            self.weapon_arm = -48.0 + s * 6.0
            self.shield_arm = -30.0 - s * 5.0
            self.weapon_raise = 1.0
            self.hair = s * 8.0
            self.mouth = 0.24 + max(0.0, s) * 0.10
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
            self.root_x = shake * 3.0 - hit * 3.0
            self.bob = -hit * 2.0
            self.lean = -12.0 * hit
            self.head = 8.0 * hit
            self.left_leg = -8.0 * hit
            self.right_leg = 8.0 * hit
            self.weapon_arm = 20.0 * hit
            self.shield_arm = 14.0 * hit
            self.hair = -12.0 * hit
            self.mouth = 0.10 * hit
        elif anim == "death":
            tt = _ease(t)
            self.dead_t = tt
            self.root_x = tt * 18.0
            self.root_y = tt * 10.0
            self.bob = -tt * 4.0
            self.lean = -82.0 * tt
            self.head = -18.0 * tt
            self.left_leg = _lerp(-2.0, 18.0, tt)
            self.right_leg = _lerp(2.0, -18.0, tt)
            self.weapon_arm = _lerp(4.0, 58.0, tt)
            self.shield_arm = _lerp(-4.0, -56.0, tt)
            self.hair = -22.0 * tt
            self.x_eye = tt > 0.58


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
_REST_ROOT: Point = (WORK_FRAME_SIZE[0] * 0.48, WORK_FRAME_SIZE[1] * 0.78)
_REST_HEAD: Point = (_REST_ROOT[0] - 2, _REST_ROOT[1] - 244)
_THIGH, _SHIN = 40.0, 38.0
#: The axe's angle in the idle pose: its head is painted as the painter drew
#: it there, and turns with the haft.
_AXE_REST = -32.0


def _joints(anim: str, frame_idx: int, nframes: int):
    return _viking_shieldmaiden_rig.evaluate(Pose(anim, frame_idx, nframes), WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])


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
    col = LEATHER if front else LEATHER_DARK
    width = 8.2 if front else 7.2
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
    _put(img, _bone_piece((limb, 1), l1, width, skin, OUTLINE, line_w), shoulder, _deg(shoulder, elbow), f"{limb}_upper")
    _put(img, _bone_piece((limb, 2), l2, width, skin, OUTLINE, line_w, cap=True), elbow, _deg(elbow, hand), f"{limb}_fore")


def _draw_shield(draw: ImageDraw.ImageDraw, center: Point, r: float, *, angle: float = 0.0, front: bool = True) -> None:
    rim = STEEL if front else STEEL_SHADE
    face = SHIELD_RED if front else SHIELD_RED_DARK
    _ellipse(draw, center[0], center[1], r + 3, r + 3, rim, OUTLINE, 0.8)
    _ellipse(draw, center[0], center[1], r, r, face, OUTLINE, 0.7)
    _ellipse(draw, center[0], center[1], r * 0.58, r * 0.58, rim, OUTLINE, 0.4)
    _line(draw, [(center[0] - r * 0.74, center[1]), (center[0] + r * 0.74, center[1])], GOLD, 0.9)
    _line(draw, [(center[0], center[1] - r * 0.74), (center[0], center[1] + r * 0.74)], GOLD, 0.9)
    _circle(draw, center, r * 0.18, STEEL_SHADE, OUTLINE, 0.3)


def _paint_axe(draw: ImageDraw.ImageDraw, hand: Point, length: float) -> None:
    """The axe at angle 0 (haft along +x) held at ``hand``; its head is the
    painter's, turned back by the rest angle."""
    tip = (hand[0] + length, hand[1])
    _line(draw, [hand, tip], LEATHER, 2.8)
    _line(draw, [hand, tip], OUTLINE, 0.5)

    def at(dx: float, dy: float) -> Point:
        rx, ry = _rot(dx, dy, -_AXE_REST)
        return (tip[0] + rx, tip[1] + ry)

    _poly(draw, [at(-4, -6), at(8, -16), at(22, -6), at(18, 8), at(6, 14), at(-6, 6)], STEEL, OUTLINE, 0.7)
    _poly(draw, [at(2, -2), at(26, -6), at(36, 4), at(18, 14)], STEEL_SHADE, OUTLINE, 0.6)
    _line(draw, [at(4, -10), at(18, 8)], (224, 228, 236, 255), 0.8)


def _paint_body(draw: ImageDraw.ImageDraw) -> None:
    P = _P0
    _poly(draw, [P(-22, -106), P(20, -106), P(32, -40), P(10, -10), P(-18, -14), P(-34, -48)], SKIRT_SHADE, OUTLINE, 1.0)
    _poly(draw, [P(-34, -206), P(6, -214), P(34, -198), P(44, -150), P(36, -108), P(8, -88), P(-18, -94), P(-40, -144)], TUNIC, OUTLINE, 1.2)
    _poly(draw, [P(-12, -192), P(10, -196), P(20, -120), P(0, -100), P(-18, -120), P(-22, -176)], TUNIC_SHADE, OUTLINE, 0.7)
    _poly(draw, [P(-16, -168), P(-7, -180), P(0, -166), P(-4, -148), P(-14, -148)], TUNIC, OUTLINE, 0.4)
    _poly(draw, [P(0, -168), P(12, -178), P(18, -160), P(10, -146), P(0, -148)], TUNIC, OUTLINE, 0.4)
    _poly(draw, [P(-30, -206), P(8, -216), P(34, -204), P(48, -174), P(28, -160), P(2, -168), P(-22, -158), P(-40, -176)], FUR, OUTLINE, 0.9)
    for x, y in [(-22, -188), (-6, -196), (10, -190), (24, -182)]:
        _line(draw, [P(x, y), P(x + 6, y + 8)], FUR_SHADE, 0.8)


def _paint_skirt_front(draw: ImageDraw.ImageDraw) -> None:
    P = _P0
    _poly(draw, [P(-28, -104), P(16, -104), P(24, -40), P(6, -8), P(-16, -10), P(-32, -44)], SKIRT, OUTLINE, 1.0)
    _line(draw, [P(-12, -98), P(-8, -18)], SKIRT_SHADE, 0.9)
    _line(draw, [P(2, -98), P(8, -14)], SKIRT_SHADE, 0.9)


def _paint_belt(draw: ImageDraw.ImageDraw) -> None:
    P = _P0
    _poly(draw, [P(-26, -118), P(18, -118), P(18, -104), P(-26, -104)], LEATHER, OUTLINE, 0.6)
    _ellipse(draw, P(-4, -111)[0], P(-4, -111)[1], 5.0, 4.0, GOLD, OUTLINE, 0.3)
    _line(draw, [P(-24, -112), P(16, -112)], LEATHER_DARK, 0.6)


#: The braid at rest from its root (head-local), and how far its end sways
#: per unit of ``pose.hair``: it turns about its root by that.
_BRAID_ROOT: Point = (18.0, 8.0)
_BRAID = [(0.0, 0.0), (8.0, 16.0), (14.0, 34.0), (8.0, 52.0)]
_BRAID_SWAY = 0.22


def _paint_braid(draw: ImageDraw.ImageDraw) -> None:
    braid = [_H0(_BRAID_ROOT[0] + x, _BRAID_ROOT[1] + y) for x, y in _BRAID]
    _line(draw, braid, HAIR, 5.6)
    _line(draw, braid, OUTLINE, 0.7)
    for frac in [0.2, 0.45, 0.7]:
        bx = _lerp(braid[0][0], braid[-1][0], frac)
        by = _lerp(braid[0][1], braid[-1][1], frac)
        _line(draw, [(bx - 4, by - 3), (bx + 4, by + 3)], GOLD, 0.5)


def _paint_hair_back(draw: ImageDraw.ImageDraw) -> None:
    H = _H0
    _poly(draw, [H(-24, -8), H(-14, -34), H(10, -36), H(28, -18), H(28, 10), H(16, 26), H(-4, 20), H(-24, 8)], HAIR_SHADE, OUTLINE, 0.9)


def _paint_head(draw: ImageDraw.ImageDraw, blink: bool, x_eye: bool, mouth: float) -> None:
    H = _H0
    _poly(draw, [H(-20, -16), H(-6, -34), H(18, -30), H(30, -10), H(26, 4), H(8, 10), H(-12, 4)], STEEL, OUTLINE, 0.9)
    _poly(draw, [H(-6, -34), H(2, -46), H(12, -34)], STEEL_SHADE, OUTLINE, 0.5)
    _poly(draw, [H(-18, -10), H(-12, -26), H(8, -30), H(22, -18), H(24, 6), H(12, 22), H(-8, 22), H(-22, 8)], SKIN, OUTLINE, 0.9)
    if x_eye:
        _line(draw, [H(-8, -4), H(-1, 3)], OUTLINE, 0.8)
        _line(draw, [H(-8, 3), H(-1, -4)], OUTLINE, 0.8)
        _line(draw, [H(8, -5), H(15, 2)], OUTLINE, 0.8)
        _line(draw, [H(8, 2), H(15, -5)], OUTLINE, 0.8)
    elif blink:
        _line(draw, [H(-10, -2), H(-2, -2)], OUTLINE, 0.7)
        _line(draw, [H(8, -3), H(16, -3)], OUTLINE, 0.7)
    else:
        _ellipse(draw, H(-6, -2)[0], H(-6, -2)[1], 3.8, 3.0, EYE, OUTLINE, 0.4)
        _ellipse(draw, H(12, -3)[0], H(12, -3)[1], 3.8, 3.0, EYE, OUTLINE, 0.4)
        _circle(draw, H(-5, -2), 1.0, PUPIL, PUPIL, 0.1)
        _circle(draw, H(13, -3), 1.0, PUPIL, PUPIL, 0.1)
    _line(draw, [H(-11, -9), H(-2, -10)], OUTLINE, 0.5)
    _line(draw, [H(8, -10), H(16, -11)], OUTLINE, 0.5)
    _poly(draw, [H(2, 0), H(6, 8), H(2, 10), H(-1, 5)], SKIN_SHADE, OUTLINE, 0.25)
    if mouth > 0.03:
        _ellipse(draw, H(4, 14)[0], H(4, 14)[1], 5.0, 2.6 + mouth * 10.0, MOUTH, OUTLINE, 0.4)
        if mouth > 0.14:
            _poly(draw, [H(0, 14), H(4, 20), H(8, 14)], TONGUE, OUTLINE, 0.2)
    else:
        _line(draw, [H(-1, 14), H(5, 16), H(11, 14)], MOUTH, 0.7)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", _CANVAS, (0, 0, 0, 0))
    pose = Pose(anim, frame_idx, nframes)

    J = _viking_shieldmaiden_rig.evaluate(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    root = J.root
    body_ang = J.body_ang
    head_root = J.head_root
    head_ang = J.head_ang

    def H(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, head_ang)
        return (head_root[0] + rx, head_root[1] + ry)

    # far leg, then the body (skirt back, torso, mantle) as one piece
    _draw_leg(img, J.far_hip, 92 + pose.right_leg, pose.right_lift, front=False, side="far")
    _put(img, _rest(("body",), _paint_body, _REST_ROOT), root, body_ang, "body")

    # far arm / shield arm behind body sometimes
    far_hand = J.far_hand
    _draw_arm(img, "far_arm", J.far_shoulder, J.far_elbow, far_hand, SKIN_SHADE, 6.4, 0.9)

    # head: hair behind, the braid swaying about its root, the face
    _put(img, _rest(("hair_back",), _paint_hair_back, _REST_HEAD), head_root, head_ang, "hair_back")
    turn = -math.degrees(math.atan2(pose.hair * _BRAID_SWAY, _BRAID[-1][1]))
    _put(img, _rest(("braid",), _paint_braid, _H0(*_BRAID_ROOT)), H(*_BRAID_ROOT), head_ang + turn, "braid")
    mouth = round(pose.mouth, 2)
    head = _rest(("head", pose.blink, pose.x_eye, mouth), lambda d: _paint_head(d, pose.blink, pose.x_eye, mouth), _REST_HEAD)
    _put(img, head, head_root, head_ang, "head")

    # near leg, front skirt
    near_foot = _draw_leg(img, J.near_hip, 92 + pose.left_leg, pose.left_lift, front=True, side="near")
    _put(img, _rest(("skirt_front",), _paint_skirt_front, _REST_ROOT), root, body_ang, "skirt_front")

    # near arm / shield on top
    near_hand = J.near_hand
    _draw_arm(img, "near_arm", J.near_shoulder, J.near_elbow, near_hand, SKIN, 6.8, 0.95)
    shield_center = (near_hand[0] - 12 - pose.shield_push * 12, near_hand[1] - 2)
    _put(img, _rest(("shield",), lambda d: _draw_shield(d, _BONE_O, 24, front=True), _BONE_O), shield_center, 0.0, "shield")

    # weapon on top for readability
    axe_ang = -32 + pose.weapon_arm * 1.15 - pose.weapon_raise * 28
    axe_len = _rig.q(54 + pose.weapon_raise * 10, 2.0)
    _put(img, _rest(("axe", axe_len), lambda d: _paint_axe(d, _BONE_O, axe_len), _BONE_O), far_hand, axe_ang, "axe")
    axe_tip = (far_hand[0] + axe_len * math.cos(math.radians(axe_ang)), far_hand[1] + axe_len * math.sin(math.radians(axe_ang)))

    # belt and trim
    _put(img, _rest(("belt",), _paint_belt, _REST_ROOT), root, body_ang, "belt")

    # wrist bands
    def band(dx: float, dy: float):
        return lambda d: _line(d, [_BONE_O, (_BONE_O[0] + dx, _BONE_O[1] + dy)], GOLD, 0.6)

    _put(img, _rest(("band", "near"), band(10, 2), _BONE_O), near_hand, 0.0, "near_band")
    _put(img, _rest(("band", "far"), band(-8, -2), _BONE_O), far_hand, 0.0, "far_band")

    # effects change every frame: one raster each
    def arcs(draw) -> None:
        if anim in {"axe_swing", "overhead_chop"} and pose.impact > 0.18:
            cx, cy = axe_tip
            draw.arc((_s(cx - 48), _s(cy - 24), _s(cx + 36), _s(cy + 42)), 196, 344, fill=FX, width=_s(3.6))
        if anim == "shield_bash" and pose.impact > 0.18:
            cx, cy = shield_center
            draw.arc((_s(cx - 34), _s(cy - 24), _s(cx + 46), _s(cy + 32)), 210, 350, fill=FX, width=_s(3.2))

    if pose.impact > 0.18 and anim in {"axe_swing", "overhead_chop", "shield_bash"}:
        _fx_layer(img, arcs, "fx_arc")
    if anim in {"walk", "shield_bash", "overhead_chop"} and (pose.left_lift > 0.5 or pose.right_lift > 0.5):
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
        description="Render the standalone Viking Shieldmaiden sprite sheet."
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
