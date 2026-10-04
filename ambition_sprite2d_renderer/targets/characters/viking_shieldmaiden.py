"""Standalone generator for an attacking Viking shieldmaiden sprite sheet.

Concept:
- a Viking shieldmaiden facing right: a pointed helmet over blonde hair
  and a long braid, a purple apron dress with oval brooches and beads over
  a long blue underdress, a fur capelet, leather legs and boots
- a red and gold round shield on the near arm (driven forward on a bash)
  and a bearded hand axe; the axe arm follows the swing
- drawn as a rig (``_viking_common``): every rigid thing a piece painted
  once, the face a base and expression overlays, effects pieces with opacity

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
from . import _viking_shieldmaiden_rig


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


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


TARGET_NAME = "viking_shieldmaiden"
# Files the tack-on installer copies into the sandbox sprites dir.
# Names match what `build_sheet` writes (target_spritesheet.{png,yaml,ron}).
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
]
FRAME_SIZE = (320, 320)
WORK_FRAME_SIZE = V.WORK_FRAME_SIZE
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


# --- Drawn as a rig: every rigid thing is a piece painted once in its own
# frame and turned into place (``_viking_common``). The skeleton is
# ``_viking_shieldmaiden_rig``: the axe arm follows the axe's swing, the
# shield hand drives the shield forward on a bash. ---

TRIM = (204, 160, 70, 255)
BEAD_A = (66, 150, 150, 255)
BEAD_B = (196, 82, 60, 255)
STEEL_LIGHT = (232, 236, 242, 255)
WOOD_LIGHT = (146, 104, 68, 255)
BLUSH = (232, 142, 140, 120)
LIP = (178, 92, 92, 255)

PAL = {
    "outline": OUTLINE,
    "boot": BOOT,
    "boot_shade": (38, 28, 22, 255),
    "steel": STEEL,
    "steel_shade": STEEL_SHADE,
    "steel_light": STEEL_LIGHT,
    "wood": LEATHER,
    "wood_light": WOOD_LIGHT,
    "leather_dark": LEATHER_DARK,
    "gold": GOLD,
    "shield": SHIELD_RED,
    "shield_dark": SHIELD_RED_DARK,
    "shield_pattern": GOLD,
}

HEAD_K = 1.12
HEAD_EXTENT = (40, 54, 40, 40)
THIGH, SHIN = 40.0, 38.0
AXE_LEN = 58.0
SHIELD_R = 28.0
#: The braid at rest from its root (head-local), and how far its end sways
#: per unit of ``pose.hair``: it turns about its root by that.
BRAID_ROOT: Point = (-14.0, 8.0)
BRAID_LEN = 56.0
BRAID_SWAY = 0.22


def _k(*key):
    return (TARGET_NAME,) + key


def _paint_body(pen: V.Pen) -> None:
    O = OUTLINE
    # the blue underdress: a long skirt to below the knee
    skirt = [(-28, -122), (26, -122), (36, -64), (40, -52), (20, -47), (-4, -46), (-28, -48), (-40, -54)]
    pen.poly(skirt, SKIRT)
    pen.poly([(-28, -122), (-16, -122), (-18, -46), (-28, -48), (-40, -54)], SKIRT_SHADE)
    for a, b in [((-4, -110), (-6, -48)), ((10, -110), (14, -48)), ((22, -100), (30, -52))]:
        pen.line([a, b], SKIRT_SHADE, 1.2)
    pen.line([(-39, -55), (39, -53)], TRIM, 3.2)
    pen.poly(skirt, None, O, 1.6)
    # the purple apron dress over it, to mid thigh
    apron = [(-26, -196), (-8, -201), (14, -201), (30, -194), (37, -174), (36, -146), (31, -126), (34, -100), (30, -86), (0, -82), (-26, -86), (-32, -102), (-30, -128), (-34, -150), (-34, -176)]
    pen.poly(apron, TUNIC, smooth=True)
    pen.poly([(-26, -196), (-14, -199), (-18, -150), (-22, -84), (-26, -86), (-32, -102), (-30, -128), (-34, -150), (-34, -176)], TUNIC_SHADE)
    pen.line([(-30, -91), (32, -91)], TRIM, 2.6)
    pen.poly(apron, None, O, 1.6, smooth=True)
    # belt and pouch
    pen.poly([(-34, -130), (32, -130), (33, -119), (-35, -119)], LEATHER, O, 1.3)
    pen.poly([(-26, -120), (-15, -120), (-14, -104), (-27, -104)], LEATHER_DARK, O, 1.2)
    pen.poly([(8, -132), (19, -132), (19, -117), (8, -117)], GOLD, O, 1.1)
    pen.poly([(11, -128), (16, -128), (16, -121), (11, -121)], LEATHER)
    # two oval brooches and a string of beads between them
    pen.line([(-6, -172), (0, -160), (8, -156), (16, -160), (22, -170)], BEAD_A, 2.4, smooth=True)
    for i, (x, y) in enumerate([(-3, -165), (2, -159), (8, -157), (14, -159), (19, -164)]):
        pen.circle((x, y), 1.6, BEAD_B if i % 2 else BEAD_A, O, 0.5)
    for x in (-8, 22):
        pen.ellipse(x, -177, 5.2, 6.4, GOLD, O, 1.2)
        pen.ellipse(x, -177, 2.4, 3.2, (170, 132, 54, 255))
    # a short fur capelet on the shoulders
    top = V.catmull([(-36, -186), (-32, -200), (-16, -209), (2, -211), (20, -209), (33, -201), (40, -188)], closed=False)
    shag = [(36, -182), (29, -187), (23, -180), (16, -186), (9, -179), (2, -185), (-5, -179), (-12, -186), (-19, -180), (-26, -186), (-32, -180)]
    pen.poly(top + shag, FUR)
    pen.poly([(-36, -186), (-32, -200), (-22, -206), (-24, -185), (-32, -180)], FUR_SHADE)
    for x, y in [(-14, -202), (-2, -205), (12, -204), (26, -198)]:
        pen.line([(x, y), (x + 3, y + 7)], FUR_SHADE, 1.0)
    pen.poly(top + shag, None, O, 1.6)


def _paint_braid(pen: V.Pen) -> None:
    """The braid hanging from its root along +y, turned by its sway."""
    O = OUTLINE
    pts = [(0, 0), (-3, 18), (-1, 36), (-4, BRAID_LEN)]
    pen.line(pts, O, 8.6, smooth=True)
    pen.line(pts, HAIR, 6.2, smooth=True)
    for y in range(6, int(BRAID_LEN) - 4, 7):
        pen.line([(-4.5, y - 2), (2.5, y + 2)], HAIR_SHADE, 1.0)
    pen.ellipse(-4, BRAID_LEN + 3, 3.4, 4.4, HAIR, O, 1.0)
    pen.poly([(-7, BRAID_LEN - 3), (0, BRAID_LEN - 3), (0, BRAID_LEN + 1), (-7, BRAID_LEN + 1)], GOLD, O, 0.8)


def _paint_head_base(pen: V.Pen) -> None:
    O = OUTLINE
    # hair falling behind the head to the nape
    pen.poly([(-18, -14), (-27, -2), (-28, 14), (-22, 24), (-10, 26), (-4, 12), (-4, -8)], HAIR, O, 1.4, smooth=True)
    pen.line([(-20, 0), (-22, 16)], HAIR_SHADE, 1.0)
    # face: a softer jaw, a small nose, lips
    pen.poly([(-13, -16), (5, -20), (19, -15), (24, -5), (24, 5), (22, 13), (14, 21), (4, 23), (-6, 19), (-13, 10), (-15, -2)], SKIN, O, 1.6, smooth=True)
    pen.poly([(-13, -14), (-5, -16), (-6, 12), (-12, 10), (-15, -2)], SKIN_SHADE)
    pen.poly([(22, -5), (28, 3), (27, 7), (22, 7)], SKIN, O, 1.2, smooth=True)
    pen.ellipse(13, 9, 3.6, 2.2, BLUSH)
    pen.line([(16, 14.5), (20, 15), (23, 14)], LIP, 1.6)
    # hair framing the face under the helmet, and the ear in it
    pen.poly([(-14, -14), (2, -15), (-2, -6), (-8, 2), (-10, 14), (-15, 4)], HAIR, O, 1.2, smooth=True)
    pen.ellipse(-6, 4, 3.4, 5.0, SKIN, O, 1.1)
    pen.line([(-7, 1), (-5, 4), (-7, 7)], SKIN_SHADE, 0.9)
    # a pointed helmet with a bronze brow band
    dome = V.catmull([(-19, -12), (-18, -26), (-6, -38), (6, -46), (18, -36), (26, -22), (27, -12)], closed=False)
    pen.poly(dome + [(27, -12), (-19, -12)], STEEL)
    pen.poly([(-19, -12), (-18, -26), (-6, -38), (4, -45), (0, -12)], STEEL_SHADE)
    pen.line([(10, -40), (19, -32), (23, -22)], STEEL_LIGHT, 1.5, smooth=True)
    pen.poly(dome + [(27, -12), (-19, -12)], None, O, 1.6)
    pen.poly([(4, -45), (7, -52), (9, -44)], STEEL_SHADE, O, 1.0)
    pen.poly([(-21, -17), (29, -17), (29, -10), (-21, -10)], GOLD, O, 1.3)
    for x in (-13, -3, 7, 17, 25):
        pen.circle((x, -13.5), 1.0, (150, 116, 50, 255))


def _paint_eyes(pen: V.Pen, state: str) -> None:
    O = OUTLINE
    if state == "x":
        pen.line([(9, -5), (16, 2)], O, 1.5)
        pen.line([(9, 2), (16, -5)], O, 1.5)
    elif state == "blink":
        pen.line([(8, -1), (12, 1), (17, -1)], O, 1.5, smooth=True)
        pen.line([(17, -1), (19, -2.4)], O, 1.0)
    else:
        pen.ellipse(12.5, -1.5, 4.2, 4.0, EYE, O, 1.0)
        pen.ellipse(14.2, -1.0, 2.2, 2.8, (64, 104, 132, 255))
        pen.circle((14.6, -1.0), 1.1, PUPIL)
        pen.circle((13.4, -2.4), 0.7, EYE)
        pen.line([(8, -4.8), (13, -6.2), (18, -4.6), (20, -6)], O, 1.3, smooth=True)
    pen.line([(7, -9.5), (13, -11), (19, -9.5)], HAIR_SHADE, 1.6, smooth=True)


def _paint_mouth(pen: V.Pen, state: int) -> None:
    O = OUTLINE
    rx, ry = [(0, 0), (3.2, 2.2), (4.0, 3.8), (4.8, 5.8)][state]
    cy = 15 + ry * 0.55
    pen.ellipse(19.5, cy, rx, ry, MOUTH, O, 1.1)
    if state >= 2:
        pen.ellipse(20, cy + ry * 0.45, rx * 0.6, ry * 0.4, TONGUE)
    if state == 3:
        pen.poly([(16, cy - ry * 0.75), (23, cy - ry * 0.75), (22.6, cy - ry * 0.4), (16.4, cy - ry * 0.4)], EYE)


def _draw_head(img: Image.Image, J, pose: "Pose") -> None:
    P = V.frame_point(J.head_root, J.head_ang)
    turn = -math.degrees(math.atan2(pose.hair * BRAID_SWAY, BRAID_LEN))
    braid = V.piece(_k("braid"), (12, 4, 12, BRAID_LEN + 10), _paint_braid, k=HEAD_K)
    V.put(img, braid, P(BRAID_ROOT[0] * HEAD_K, BRAID_ROOT[1] * HEAD_K), J.head_ang + turn, "braid")
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
        k=HEAD_K,
    )


def _band(x0: float, x1: float, color: RGBA, r: float, ring: RGBA = None):
    def detail(pen: V.Pen) -> None:
        pen.poly([(x0, -r), (x1, -r * 0.94), (x1, r * 0.94), (x0, r)], color, OUTLINE, 1.0)
        if ring is not None:
            pen.line([(x0 - 1.5, -r), (x0 - 1.5, r)], ring, 1.8)

    return detail


def _limb_parts(front: bool) -> dict:
    leg = LEATHER if front else LEATHER_DARK
    sleeve = SKIRT if front else SKIRT_SHADE
    skin = SKIN if front else SKIN_SHADE
    side = "near" if front else "far"
    L1, L2 = _viking_shieldmaiden_rig.UPPER_ARM, _viking_shieldmaiden_rig.FOREARM
    return {
        "thigh": V.tube_piece(_k("thigh", side), THIGH, 7.6, 6.4, leg, OUTLINE, 1.6),
        "shin": V.tube_piece(_k("shin", side), SHIN, 6.4, 5.0, leg, OUTLINE, 1.6, start_cap=False),
        "upper": V.tube_piece(_k("upper", side), L1, 6.6, 5.6, sleeve, OUTLINE, 1.6, detail=_band(30, 34, TRIM, 5.8)),
        "fore": V.tube_piece(_k("fore", side), L2, 5.4, 4.4, skin, OUTLINE, 1.6, start_cap=False, detail=_band(20, 34, LEATHER if front else LEATHER_DARK, 4.9, GOLD)),
        "fist": V.fist_piece(_k("fist", side), skin, OUTLINE, 5.8),
    }


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = V.new_canvas()
    pose = Pose(anim, frame_idx, nframes)
    J = _viking_shieldmaiden_rig.evaluate(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    near, far = _limb_parts(True), _limb_parts(False)
    boot = V.boot_piece(_k("boot"), PAL, cuff=FUR_SHADE)
    L1, L2 = _viking_shieldmaiden_rig.UPPER_ARM, _viking_shieldmaiden_rig.FOREARM

    fall = J.body_ang if anim == "death" else 0.0
    V.leg(img, J.far_hip, 92 + pose.right_leg + fall, pose.right_lift, THIGH, SHIN, far["thigh"], far["shin"], boot, "far", fall)
    near_foot = V.leg(img, J.near_hip, 92 + pose.left_leg + fall, pose.left_lift, THIGH, SHIN, near["thigh"], near["shin"], boot, "near", fall)
    far_elbow, far_hand = V.arm(img, J.far_shoulder, J.far_hand, L1, L2, J.far_bend, far["upper"], far["fore"], "far")
    V.put(img, V.piece(_k("body"), (48, 216, 48, 0), _paint_body), J.root, J.body_ang, "body")
    _draw_head(img, J, pose)
    V.arm(img, J.near_shoulder, J.near_hand, L1, L2, J.near_bend, near["upper"], near["fore"], "near")
    V.put(img, V.round_shield_piece(_k("shield"), PAL, SHIELD_R), J.shield_center, 0.0, "shield")
    V.put(img, V.hand_axe_piece(_k("axe"), PAL, AXE_LEN), far_hand, J.axe_deg, "axe")
    V.put(img, far["fist"], far_hand, V.angle(far_elbow, far_hand), "far_fist")

    # effects: pieces painted once, placed with an opacity
    if anim in {"axe_swing", "overhead_chop"} and pose.impact > 0.18:
        arc = V.swing_arc_piece(_k("arc"), FX, 60.0, span=110.0, width=7.0, lead=18.0)
        V.put(img, arc, far_hand, J.axe_deg, "fx_arc", opacity=min(1.0, pose.impact * 1.1))
    if anim == "shield_bash" and pose.impact > 0.18:
        burst = V.burst_piece(_k("burst"), FX, 22.0)
        V.put(img, burst, V.along(J.shield_center, J.body_ang, SHIELD_R + 6), J.body_ang, "fx_burst", opacity=min(1.0, pose.impact * 1.1))
    if anim in {"walk", "shield_bash", "overhead_chop"} and (pose.left_lift > 0.5 or pose.right_lift > 0.5):
        V.put(img, V.dust_piece(_k("dust"), DUST), (near_foot[0], near_foot[1] + 10), 0.0, "fx_dust", opacity=0.9)

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
