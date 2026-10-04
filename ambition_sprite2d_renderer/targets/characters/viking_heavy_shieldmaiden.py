"""Standalone generator for a heavy Viking shieldmaiden sprite sheet.

A distinct, opera-singer inspired silhouette:
- a round steel helmet with great curved horns, long blonde twin braids
- a gold corselet with the two great breastplate cups, a steel gorget, a
  brown bodice and cape, a long pleated blue dress
- big beefy arms, a toothed round shield and a long spear (couched and
  driven forward for the jab, raised aloft for the bellow)
- drawn as a rig (``_viking_common``): every rigid thing a piece painted
  once (horns and braids one raster each, mirrored), the face a base and
  expression overlays, effects pieces with opacity

Generator only. No registration or GUI wiring.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from . import _viking_common as V
from . import _viking_heavy_shieldmaiden_rig


ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_viking_heavy_shieldmaiden",
        "display_name": "Viking Heavy Shieldmaiden",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Wide",
        "mass_class": "Heavy",
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
    "brain": {"default_preset": "melee_brute_brute"},
    "actions": {"default_preset": "brute_lunge"},
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


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


TARGET_NAME = "viking_heavy_shieldmaiden"
FRAME_SIZE = (320, 320)
WORK_FRAME_SIZE = V.WORK_FRAME_SIZE
#: Work pixels to canvas pixels: the canvas is 8x the frame, so the frame is
#: a WHOLE-factor reduction of it (a turned piece reduces only that way).
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 132),
    ("march", 8, 98),
    ("shield_barge", 7, 84),
    ("spear_jab", 7, 82),
    ("diva_bellow", 6, 104),
    ("hurt", 4, 92),
    ("death", 8, 112),
]

OUTLINE = (26, 20, 18, 255)
SKIN = (232, 194, 164, 255)
SKIN_SHADE = (194, 156, 126, 255)
BLONDE = (247, 194, 56, 255)
BLONDE_SHADE = (210, 156, 36, 255)
STEEL = (188, 198, 210, 255)
STEEL_SHADE = (132, 142, 154, 255)
HORN = (235, 228, 176, 255)
HORN_SHADE = (198, 188, 132, 255)
GOLD = (236, 192, 68, 255)
GOLD_SHADE = (188, 138, 38, 255)
BROWN = (138, 90, 54, 255)
BROWN_DARK = (92, 60, 38, 255)
DRESS = (120, 162, 212, 255)
DRESS_SHADE = (80, 120, 174, 255)
CLOTH = (118, 96, 92, 255)
CLOTH_SHADE = (88, 70, 68, 255)
SHIELD = (168, 172, 182, 255)
SHIELD_SHADE = (118, 122, 132, 255)
SANDAL = (82, 58, 34, 255)
EYE = (248, 246, 238, 255)
PUPIL = (40, 38, 42, 255)
LIP = (190, 58, 70, 255)
MOUTH = (108, 48, 52, 255)
TONGUE = (212, 100, 116, 255)
FX = (248, 238, 188, 148)
DUST = (136, 118, 92, 132)



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
        self.shield_arm = 0.0
        self.weapon_arm = 0.0
        self.weapon_pitch = 0.0
        self.shield_push = 0.0
        self.mouth = 0.0
        self.braid = 0.0
        self.blink = False
        self.x_eye = False
        self.impact = 0.0

        if anim == "idle":
            self.bob = s * 1.2
            self.lean = s * 1.4
            self.head = -1.0 + s * 1.0
            self.shield_arm = -2.0 + s * 1.5
            self.weapon_arm = 2.0 - s * 1.5
            self.weapon_pitch = -2.0
            self.braid = s * 4.0
            self.blink = idx == n - 2
        elif anim == "march":
            self.root_x = s * 2.4
            self.bob = abs(s) * 3.6 - 0.6
            self.lean = s * 2.2
            self.head = -2.0 - s * 1.2
            self.left_leg = -20.0 * s
            self.right_leg = 20.0 * s
            self.left_lift = max(0.0, -s) * 8.0
            self.right_lift = max(0.0, s) * 8.0
            self.shield_arm = 14.0 * s - 4.0
            self.weapon_arm = -10.0 * s + 4.0
            self.weapon_pitch = -10.0 * s
            self.braid = -s * 10.0
        elif anim == "shield_barge":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-14.0, 24.0, tt)
            self.bob = -hit * 2.4
            self.lean = _lerp(-12.0, 22.0, tt)
            self.head = _lerp(-4.0, 8.0, tt)
            self.left_leg = _lerp(-12.0, 14.0, tt)
            self.right_leg = _lerp(10.0, -10.0, tt)
            self.shield_arm = _lerp(-42.0, 28.0, tt)
            self.weapon_arm = _lerp(-12.0, -2.0, tt)
            self.weapon_pitch = _lerp(16.0, 32.0, tt)
            self.shield_push = hit
            self.mouth = 0.10
            self.braid = _lerp(8.0, -8.0, tt)
            self.impact = hit
        elif anim == "spear_jab":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-12.0, 22.0, tt)
            self.bob = -hit * 2.0
            self.lean = _lerp(-10.0, 18.0, tt)
            self.head = _lerp(-5.0, 8.0, tt)
            self.left_leg = _lerp(-8.0, 10.0, tt)
            self.right_leg = _lerp(8.0, -8.0, tt)
            self.shield_arm = _lerp(-8.0, -12.0, tt)
            self.weapon_arm = _lerp(-34.0, 38.0, tt)
            self.weapon_pitch = _lerp(-46.0, 8.0, tt)
            self.mouth = 0.12
            self.braid = _lerp(12.0, -12.0, tt)
            self.impact = hit
        elif anim == "diva_bellow":
            self.bob = s * 1.2
            self.lean = -2.0 + s * 2.0
            self.head = -4.0 + s * 2.0
            self.left_leg = -2.0
            self.right_leg = 2.0
            self.shield_arm = -18.0 - s * 3.0
            self.weapon_arm = -46.0 + s * 4.0
            self.weapon_pitch = -42.0 + s * 4.0
            self.braid = s * 8.0
            self.mouth = 0.28 + max(0.0, s) * 0.08
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
            self.root_x = shake * 3.0 - hit * 5.0
            self.bob = -hit * 2.2
            self.lean = -12.0 * hit
            self.head = 10.0 * hit
            self.left_leg = -8.0 * hit
            self.right_leg = 8.0 * hit
            self.shield_arm = 16.0 * hit
            self.weapon_arm = 20.0 * hit
            self.weapon_pitch = 18.0 * hit
            self.braid = -14.0 * hit
            self.mouth = 0.12 * hit
        elif anim == "death":
            tt = _ease(t)
            self.root_x = tt * 16.0
            self.root_y = tt * 10.0
            self.lean = -84.0 * tt
            self.head = -18.0 * tt
            self.left_leg = _lerp(-2.0, 18.0, tt)
            self.right_leg = _lerp(2.0, -18.0, tt)
            self.shield_arm = _lerp(0.0, -42.0, tt)
            self.weapon_arm = _lerp(0.0, 34.0, tt)
            self.weapon_pitch = _lerp(-2.0, 40.0, tt)
            self.braid = -18.0 * tt
            self.x_eye = tt > 0.58


# --- Drawn as a rig: every rigid thing is a piece painted once in its own
# frame and turned into place (``_viking_common``). The skeleton is
# ``_viking_heavy_shieldmaiden_rig``. The horns are ONE raster and the
# braids ONE raster, each left copy placed mirrored. ---

STEEL_LIGHT = (234, 240, 246, 255)
WOOD_LIGHT = (176, 124, 80, 255)
BLUSH = (232, 142, 150, 130)
BEAD = (190, 60, 70, 255)

PAL = {
    "outline": OUTLINE,
    "boot": SANDAL,
    "boot_shade": (60, 42, 24, 255),
    "steel": STEEL,
    "steel_shade": STEEL_SHADE,
    "steel_light": STEEL_LIGHT,
    "wood": BROWN,
    "wood_light": WOOD_LIGHT,
    "leather_dark": BROWN_DARK,
    "gold": GOLD,
    "gold_shade": GOLD_SHADE,
    "shield": SHIELD,
    "shield_shade": SHIELD_SHADE,
}

S = _viking_heavy_shieldmaiden_rig.S
HEAD_K = 1.14 * S
HEAD_EXTENT = (40, 56, 46, 40)
THIGH, SHIN = 36.0, 34.0
SPEAR_BUTT, SPEAR_TIP = 50.0, 140.0
SHIELD_R = 44.0
HEAD_MID = 3.0
HORN_ROOT: Point = (30.0, -18.0)
BRAID_ROOT: Point = (29.0, 4.0)
BRAID_LEN = 70.0
BRAID_SWAY = 0.2


def _k(*key):
    return (TARGET_NAME,) + key


def _paint_cape(pen: V.Pen) -> None:
    pts = [(-50, -252), (-16, -262), (20, -258), (26, -200), (16, -120), (6, -60), (-10, -66), (-24, -54), (-40, -64), (-56, -52), (-68, -66), (-70, -130), (-68, -200), (-62, -240)]
    pen.poly(pts, CLOTH_SHADE, OUTLINE, 1.8)
    for a, b in [((-58, -200), (-62, -70)), ((-40, -210), (-42, -66)), ((-22, -220), (-24, -62))]:
        pen.line([a, b], (72, 56, 54, 255), 1.4)


def _paint_body(pen: V.Pen) -> None:
    O = OUTLINE
    # the long blue dress to the calf, pleated, trimmed in gold
    dress = [(-48, -168), (44, -168), (56, -100), (64, -58), (40, -50), (0, -48), (-40, -50), (-62, -58), (-56, -110)]
    pen.poly(dress, DRESS)
    pen.poly([(-48, -168), (-28, -168), (-30, -48), (-40, -50), (-62, -58), (-56, -110)], DRESS_SHADE)
    for x in (-12, 4, 20, 36):
        pen.line([(x, -160), (x * 1.25, -52)], DRESS_SHADE, 1.4)
    pen.line([(-61, -60), (63, -60)], GOLD, 4.2)
    pen.poly(dress, None, O, 1.8)
    # the bodice and shoulders in brown cloth
    torso = [(-50, -256), (-18, -266), (22, -264), (52, -252), (64, -220), (62, -180), (48, -164), (-48, -164), (-62, -184), (-66, -224), (-60, -246)]
    pen.poly(torso, CLOTH, smooth=True)
    pen.poly([(-50, -256), (-34, -262), (-40, -200), (-38, -164), (-48, -164), (-62, -184), (-66, -224), (-60, -246)], CLOTH_SHADE)
    pen.poly(torso, None, O, 1.8, smooth=True)
    # a gold corselet with the two great breastplate cups
    plate = [(-44, -238), (40, -238), (50, -206), (44, -172), (-44, -172), (-52, -206)]
    pen.poly(plate, GOLD, O, 1.6, smooth=True)
    pen.poly([(-44, -238), (-28, -238), (-36, -200), (-34, -172), (-44, -172), (-52, -206)], GOLD_SHADE)
    for cx in (-18.0, 20.0):
        pen.circle((cx, -210), 22.0, GOLD_SHADE, O, 1.6)
        for r, col in ((17.0, GOLD), (12.0, GOLD_SHADE), (7.0, GOLD)):
            pen.circle((cx, -210), r, col)
        pen.circle((cx, -210), 2.6, (252, 232, 160, 255), O, 0.7)
        pen.arc(cx, -210, 19, 19, 200, 260, (252, 232, 160, 255), 1.6)
    pen.poly(plate, None, O, 1.6, smooth=True)
    # a steel gorget at the neck
    pen.poly([(-34, -258), (-12, -268), (16, -268), (38, -258), (28, -244), (-26, -244)], STEEL, O, 1.4)
    pen.line([(-20, -252), (24, -252)], STEEL_LIGHT, 1.4)
    # a belt with a gold clasp
    pen.poly([(-52, -178), (52, -178), (53, -162), (-53, -162)], BROWN, O, 1.5)
    pen.poly([(4, -182), (24, -182), (24, -158), (4, -158)], GOLD, O, 1.3)
    pen.circle((14, -170), 3.6, BEAD, O, 0.8)


def _paint_horn(pen: V.Pen) -> None:
    """The right horn from its root on the helmet: a great curve outward and
    up, banded."""
    O = OUTLINE
    a, c, b = (0, 0), (40, 4), (46, -48)
    pen.poly(V.horn_outline(a, c, b, 8.0), HORN, O, 1.6)
    for t, w in ((0.22, 6.6), (0.42, 5.4), (0.62, 4.0), (0.8, 2.6)):
        (x, y), (nx, ny) = V.horn_frame(a, c, b, t)
        pen.line([(x - nx * w, y - ny * w), (x + nx * w, y + ny * w)], HORN_SHADE, 1.6)
    pen.poly([(-3, -9), (5, -9), (5, 9), (-3, 9)], GOLD, O, 1.1)


def _paint_braid(pen: V.Pen) -> None:
    """The right braid hanging from its root along +y."""
    O = OUTLINE
    pts = [(0, 0), (4, 22), (2, 46), (5, BRAID_LEN)]
    pen.line(pts, O, 10.4, smooth=True)
    pen.line(pts, BLONDE, 7.8, smooth=True)
    for y in range(6, int(BRAID_LEN) - 4, 8):
        pen.line([(-1.5, y - 2.5), (6.5, y + 2.5)], BLONDE_SHADE, 1.2)
    pen.ellipse(5, BRAID_LEN + 4, 4.0, 5.0, BLONDE, O, 1.0)
    pen.poly([(1, BRAID_LEN - 4), (9, BRAID_LEN - 4), (9, BRAID_LEN + 1), (1, BRAID_LEN + 1)], GOLD, O, 0.9)


def _paint_head_base(pen: V.Pen) -> None:
    O = OUTLINE
    # blonde hair at the sides, a round face, rosy cheeks, a small nose
    pen.poly([(-30, -10), (-32, 10), (-24, 18), (-16, 6), (22, 6), (30, 18), (38, 10), (36, -10)], BLONDE, O, 1.4, smooth=True)
    pen.poly([(-22, -12), (2, -16), (28, -12), (30, 2), (27, 16), (16, 27), (2, 29), (-12, 25), (-22, 14), (-25, 0)], SKIN, O, 1.8, smooth=True)
    pen.ellipse(-11, 12, 5.0, 3.2, BLUSH)
    pen.ellipse(20, 12, 4.6, 3.2, BLUSH)
    pen.line([(8, 1), (11.5, 9), (9, 11.5), (6, 11)], SKIN_SHADE, 1.5, smooth=True)
    pen.poly([(-1, 19), (5, 17), (9, 18), (13, 17), (18, 19), (12, 22), (4, 22)], LIP, O, 1.0)
    # a fringe under the helmet
    pen.poly([(-24, -12), (32, -12), (30, -4), (20, -8), (10, -3), (0, -8), (-10, -3), (-20, -7), (-26, -2)], BLONDE, O, 1.2)
    # a round helmet with a ridge and a riveted brow band
    dome = V.catmull([(-30, -8), (-28, -28), (-14, -42), (4, -47), (22, -42), (34, -28), (36, -8)], closed=False)
    pen.poly(dome + [(36, -8), (-30, -8)], STEEL)
    pen.poly([(-30, -8), (-28, -28), (-14, -42), (-2, -46.5), (-6, -8)], STEEL_SHADE)
    pen.line([(14, -42), (26, -34), (31, -22)], STEEL_LIGHT, 1.8, smooth=True)
    pen.poly(dome + [(36, -8), (-30, -8)], None, O, 1.8)
    pen.poly([(0, -47), (8, -47), (9, -14), (-1, -14)], GOLD, O, 1.2)
    pen.poly([(-32, -15), (38, -15), (38, -6), (-32, -6)], GOLD, O, 1.4)
    for x in (-25, -15, 18, 28):
        pen.circle((x, -10.5), 1.3, GOLD_SHADE)


def _paint_eyes(pen: V.Pen, state: str) -> None:
    O = OUTLINE
    for cx in (-8.0, 15.0):
        if state == "x":
            pen.line([(cx - 3.5, -3), (cx + 3.5, 4)], O, 1.6)
            pen.line([(cx - 3.5, 4), (cx + 3.5, -3)], O, 1.6)
        elif state == "blink":
            pen.line([(cx - 4, 1), (cx, 2.8), (cx + 4, 1)], O, 1.6, smooth=True)
        else:
            pen.ellipse(cx, 0.5, 4.4, 4.2, EYE, O, 1.1)
            pen.ellipse(cx + 1.4, 0.8, 2.4, 3.0, (70, 118, 160, 255))
            pen.circle((cx + 1.6, 0.8), 1.2, PUPIL)
            pen.circle((cx + 0.6, -0.6), 0.8, EYE)
            pen.line([(cx - 4.6, -2.6), (cx, -4.4), (cx + 4.6, -2.8), (cx + 6.4, -4.6)], O, 1.3, smooth=True)
        pen.line([(cx - 5, -7.5), (cx, -9), (cx + 5, -7.5)], BLONDE_SHADE, 1.6, smooth=True)


def _paint_mouth(pen: V.Pen, state: int) -> None:
    O = OUTLINE
    rx, ry = [(0, 0), (4.6, 2.8), (5.6, 5.0), (6.8, 8.0)][state]
    cy = 19 + ry * 0.55
    pen.ellipse(8.5, cy, rx + 1.2, ry + 1.2, LIP)
    pen.ellipse(8.5, cy, rx, ry, MOUTH, O, 1.1)
    if state >= 2:
        pen.ellipse(9, cy + ry * 0.45, rx * 0.6, ry * 0.4, TONGUE)
    if state == 3:
        pen.poly([(3, cy - ry * 0.78), (14, cy - ry * 0.78), (13.5, cy - ry * 0.42), (3.5, cy - ry * 0.42)], EYE)


def _draw_head(img: Image.Image, J, pose: "Pose") -> None:
    H = V.frame_point(J.head_root, J.head_ang)
    k = HEAD_K
    off = BRAID_ROOT[0] - HEAD_MID
    braid = V.piece(_k("braid"), (10, 6, 16, BRAID_LEN + 12), _paint_braid, k=k)
    turn = -math.degrees(math.atan2(pose.braid * BRAID_SWAY, BRAID_LEN))
    V.put(img, braid, H((HEAD_MID + off) * k, BRAID_ROOT[1] * k), J.head_ang + turn, "braid_r")
    V.put_mirrored(img, braid, H((HEAD_MID - off) * k, BRAID_ROOT[1] * k), J.head_ang + turn, "braid_l")
    horn = V.piece(_k("horn"), (6, 60, 56, 12), _paint_horn, k=k)
    off = HORN_ROOT[0] - HEAD_MID
    V.put(img, horn, H((HEAD_MID + off) * k, HORN_ROOT[1] * k), J.head_ang, "horn_r")
    V.put_mirrored(img, horn, H((HEAD_MID - off) * k, HORN_ROOT[1] * k), J.head_ang, "horn_l")
    eyes = "x" if pose.x_eye else ("blink" if pose.blink else "open")
    mouth = V.mouth_state(pose.mouth)
    V.face(
        img,
        J.head_root,
        J.head_ang,
        "head",
        HEAD_EXTENT,
        (_k("head"), _paint_head_base),
        [
            ("eyes", _k("eyes", eyes), lambda pen: _paint_eyes(pen, eyes)),
            ("mouth", _k("mouth", mouth) if mouth else None, lambda pen: _paint_mouth(pen, mouth)),
        ],
        k=k,
    )


def _muscle(r: float, band: RGBA, at: float, skin_shade: RGBA):
    def detail(pen: V.Pen) -> None:
        pen.arc(at + 18, 0, 12, r * 0.7, 200, 300, skin_shade, 1.2)
        pen.poly([(at + 6, -r * 1.02), (at + 11, -r), (at + 11, r), (at + 6, r * 1.02)], band, OUTLINE, 1.0)

    return detail


def _bracer(x0: float, x1: float, color: RGBA, r: float):
    def detail(pen: V.Pen) -> None:
        pen.poly([(x0, -r), (x1, -r * 0.92), (x1, r * 0.92), (x0, r)], color, OUTLINE, 1.1)
        pen.line([(x0 + 3, -r * 0.9), (x0 + 3, r * 0.9)], GOLD, 1.6)

    return detail


def _limb_parts(front: bool) -> dict:
    skin = SKIN if front else SKIN_SHADE
    side = "near" if front else "far"
    L1, L2 = _viking_heavy_shieldmaiden_rig.UPPER_ARM, _viking_heavy_shieldmaiden_rig.FOREARM
    return {
        "thigh": V.tube_piece(_k("thigh", side), THIGH, 9.0, 8.0, skin, OUTLINE, 1.8, k=S),
        "shin": V.tube_piece(_k("shin", side), SHIN, 8.0, 6.2, skin, OUTLINE, 1.8, start_cap=False, k=S),
        "upper": V.tube_piece(_k("upper", side), L1, 12.6, 10.8, skin, OUTLINE, 1.8, detail=_muscle(11.2, GOLD, 18.0, SKIN_SHADE), k=S),
        "fore": V.tube_piece(_k("fore", side), L2, 10.8, 8.2, skin, OUTLINE, 1.8, start_cap=False, detail=_bracer(26, 46, BROWN if front else BROWN_DARK, 8.8), k=S),
        "fist": V.fist_piece(_k("fist", side), skin, OUTLINE, 9.2, k=S),
    }


def _render_frame(anim: str, idx: int, n: int) -> Image.Image:
    img = V.new_canvas()
    pose = Pose(anim, idx, n)
    J = _viking_heavy_shieldmaiden_rig.evaluate(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1], anim)
    near, far = _limb_parts(True), _limb_parts(False)
    sandal = V.boot_piece(_k("sandal"), PAL, toe=16.0, height=7.0, straps=GOLD_SHADE, k=S)
    L1, L2 = S * _viking_heavy_shieldmaiden_rig.UPPER_ARM, S * _viking_heavy_shieldmaiden_rig.FOREARM

    V.put(img, V.piece(_k("cape"), (76, 270, 32, 0), _paint_cape, k=S), J.root, J.body_ang, "cape")
    fall = J.body_ang if anim == "death" else 0.0
    V.leg(img, J.far_hip, 94 + pose.right_leg + fall, S * pose.right_lift, S * THIGH, S * SHIN, far["thigh"], far["shin"], sandal, "far", fall)
    near_foot = V.leg(img, J.near_hip, 94 + pose.left_leg + fall, S * pose.left_lift, S * THIGH, S * SHIN, near["thigh"], near["shin"], sandal, "near", fall)
    far_elbow, far_hand = V.arm(img, J.far_shoulder, J.far_hand, L1, L2, J.far_bend, far["upper"], far["fore"], "far")
    V.put(img, V.piece(_k("body"), (74, 274, 72, 0), _paint_body, k=S), J.root, J.body_ang, "body")
    _draw_head(img, J, pose)
    V.arm(img, J.near_shoulder, J.near_hand, L1, L2, J.near_bend, near["upper"], near["fore"], "near")
    V.put(img, V.saw_shield_piece(_k("shield"), PAL, SHIELD_R, k=S), J.shield_center, 0.0, "shield")
    V.put(img, V.spear_piece(_k("spear"), PAL, SPEAR_BUTT, SPEAR_TIP, k=S), far_hand, J.spear_deg, "spear")
    V.put(img, far["fist"], far_hand, V.angle(far_elbow, far_hand), "far_fist")

    # effects: pieces painted once, placed with an opacity
    H = V.frame_point(J.head_root, J.head_ang)
    if anim == "shield_barge" and pose.impact > 0.18:
        burst = V.burst_piece(_k("burst"), FX, 26.0, k=S)
        V.put(img, burst, V.along(J.shield_center, J.body_ang, S * (SHIELD_R + 10)), J.body_ang, "fx_burst", opacity=min(1.0, pose.impact * 1.1))
    if anim == "spear_jab" and pose.impact > 0.18:
        burst = V.burst_piece(_k("burst"), FX, 26.0, k=S)
        V.put(img, burst, V.along(far_hand, J.spear_deg, S * (SPEAR_TIP + 40)), J.spear_deg, "fx_burst", opacity=min(1.0, pose.impact * 1.1))
    if anim == "diva_bellow" and pose.mouth > 0.2:
        V.put(img, V.shout_piece(_k("shout"), FX, 30.0, k=S), H(34 * HEAD_K, 22 * HEAD_K), J.head_ang, "fx_shout", opacity=min(1.0, (pose.mouth - 0.2) * 6.0))
    if anim in {"march", "shield_barge"} and (pose.left_lift > 0.5 or pose.right_lift > 0.5):
        V.put(img, V.dust_piece(_k("dust"), DUST, k=S), (near_foot[0], near_foot[1] + 10 * S), 0.0, "fx_dust", opacity=0.9)

    return V.downsample(img)


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
        description="Render the standalone opera-style heavy Viking shieldmaiden sprite sheet."
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
