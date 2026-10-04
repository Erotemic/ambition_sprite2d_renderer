"""Standalone generator for an attacking Viking man warrior sprite sheet.

Concept:
- broad, bearded Viking raider facing right: a spangenhelm with a nasal
  guard, a braided beard, a fur mantle and pelt cape, a blue tunic with a
  woven trim, wrapped legs and fur-topped boots
- a long two-handed dane axe for a distinct silhouette; the hands grip the
  haft and the arms follow the axe (raised behind the head for a cleave)
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
from . import _viking_warrior_rig


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


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


TARGET_NAME = "viking_warrior"
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


# --- Drawn as a rig: every rigid thing is a piece painted once in its own
# frame and turned into place (``_viking_common``). The skeleton is
# ``_viking_warrior_rig``: the axe grip and both hands come from the axe's
# angle, so a raised axe lifts the arms above the head. ---

TRIM = (196, 150, 62, 255)
TRIM_DARK = (132, 52, 44, 255)
WRAP = (182, 170, 148, 255)
WRAP_SHADE = (140, 130, 112, 255)
STEEL_LIGHT = (232, 236, 242, 255)
WOOD_LIGHT = (150, 110, 72, 255)

PAL = {
    "outline": OUTLINE,
    "boot": BOOT,
    "boot_shade": (36, 28, 22, 255),
    "steel": STEEL,
    "steel_shade": STEEL_SHADE,
    "steel_light": STEEL_LIGHT,
    "wood": WOOD,
    "wood_light": WOOD_LIGHT,
    "leather_dark": LEATHER_DARK,
    "gold": GOLD,
}

#: The head is drawn this much larger than its design (a readable face).
HEAD_K = 1.14
HEAD_EXTENT = (34, 48, 42, 70)
THIGH, SHIN = 42.0, 40.0
AXE_BUTT, AXE_TIP = 46.0, 60.0


def _k(*key):
    return (TARGET_NAME,) + key


def _paint_cape(pen: V.Pen) -> None:
    """A pelt hanging down the back from the mantle (behind the body)."""
    pts = [(-30, -200), (-10, -206), (12, -204), (18, -170), (10, -120), (2, -96), (-6, -102), (-14, -90), (-22, -100), (-32, -88), (-40, -100), (-48, -92), (-50, -120), (-46, -170), (-40, -194)]
    pen.poly(pts, FUR_SHADE, OUTLINE, 1.6)
    for x, y in [(-40, -150), (-30, -132), (-44, -118), (-24, -110), (-36, -104)]:
        pen.line([(x, y), (x - 2, y + 9)], (136, 128, 114, 255), 1.0)


def _paint_body(pen: V.Pen) -> None:
    O = OUTLINE
    # tunic skirt to above the knee, with a woven trim at the hem
    skirt = [(-30, -124), (30, -124), (40, -78), (30, -71), (2, -68), (-26, -71), (-38, -78)]
    pen.poly(skirt, TUNIC)
    pen.poly([(-30, -124), (-16, -124), (-20, -70), (-26, -71), (-38, -78)], TUNIC_SHADE)
    for a, b in [((-4, -118), (-6, -72)), ((14, -118), (20, -72))]:
        pen.line([a, b], TUNIC_SHADE, 1.2)
    pen.line([(-38, -79), (40, -79)], TRIM, 4.2)
    for x in range(-34, 38, 6):
        pen.poly([(x, -79), (x + 3, -81), (x + 6, -79), (x + 3, -77)], TRIM_DARK)
    pen.poly(skirt, None, O, 1.6)
    # torso: broad chest forward, the back in shade
    torso = [(-30, -196), (-10, -203), (14, -203), (32, -195), (41, -176), (43, -152), (37, -132), (31, -120), (-31, -120), (-37, -142), (-39, -172)]
    pen.poly(torso, TUNIC, smooth=True)
    pen.poly([(-30, -196), (-18, -200), (-22, -160), (-24, -120), (-31, -120), (-37, -142), (-39, -172)], TUNIC_SHADE)
    pen.line([(22, -186), (34, -170), (36, -150)], (98, 116, 150, 255), 2.0, smooth=True)
    pen.line([(10, -200), (10, -170), (14, -166)], TRIM, 2.8)
    pen.poly(torso, None, O, 1.6, smooth=True)
    # belt, buckle, a pouch at the back
    pen.poly([(-24, -118), (-14, -118), (-13, -102), (-25, -102)], LEATHER_DARK, O, 1.2)
    pen.poly([(-34, -129), (34, -129), (35, -116), (-35, -116)], LEATHER, O, 1.3)
    pen.line([(-33, -122.5), (34, -122.5)], LEATHER_DARK, 0.8)
    pen.line([(20, -117), (18, -98)], LEATHER, 3.0)
    pen.line([(20, -117), (18, -98)], LEATHER_DARK, 0.8)
    pen.poly([(12, -132), (25, -132), (25, -113), (12, -113)], GOLD, O, 1.2)
    pen.poly([(15, -128), (22, -128), (22, -117), (15, -117)], LEATHER)
    # fur mantle over the shoulders, its lower edge shaggy
    top = V.catmull([(-42, -184), (-37, -202), (-20, -212), (0, -216), (20, -214), (37, -205), (46, -188)], closed=False)
    shag = [(42, -180), (35, -186), (28, -177), (20, -184), (12, -175), (4, -182), (-4, -174), (-12, -182), (-20, -175), (-28, -183), (-36, -176)]
    mantle = top + shag
    pen.poly(mantle, FUR)
    pen.poly([(-42, -184), (-37, -202), (-26, -209), (-28, -183), (-36, -176)], FUR_SHADE)
    for x, y in [(-18, -204), (-6, -208), (8, -207), (22, -202), (32, -195), (-28, -196)]:
        pen.line([(x, y), (x + 3, y + 8)], FUR_SHADE, 1.0)
    pen.poly(mantle, None, O, 1.6)
    pen.circle((24, -196), 3.0, GOLD, O, 0.9)


def _paint_head_base(pen: V.Pen) -> None:
    O = OUTLINE
    # hair at the nape, under the helmet
    pen.poly([(-20, -12), (-27, 2), (-26, 16), (-16, 26), (-6, 20), (-6, -4)], HAIR_SHADE, O, 1.4, smooth=True)
    # beard braid, then the face, the ear, the beard
    pen.line([(10, 46), (12, 56), (11, 66)], O, 7.6)
    pen.line([(10, 46), (12, 56), (11, 66)], BEARD, 5.0)
    for y in (52, 60):
        pen.line([(8, y - 1), (14, y + 1)], HAIR_SHADE, 0.9)
    pen.ellipse(11.5, 58, 3.4, 2.4, GOLD, O, 0.8)
    pen.poly([(-14, -16), (4, -20), (20, -16), (25, -6), (25, 6), (22, 16), (12, 24), (-2, 24), (-12, 16), (-16, 2)], SKIN, O, 1.6, smooth=True)
    pen.poly([(-14, -14), (-4, -16), (-6, 10), (-12, 14), (-16, 2)], SKIN_SHADE)
    pen.ellipse(-7, 3, 4.4, 6.2, SKIN, O, 1.2)
    pen.line([(-8, 0), (-6, 4), (-8, 7)], SKIN_SHADE, 1.0)
    beard = [(-11, 6), (-4, 12), (8, 14), (18, 14), (29, 12), (32, 22), (29, 36), (20, 46), (8, 51), (-4, 45), (-11, 31), (-14, 16)]
    pen.poly(beard, BEARD, O, 1.6, smooth=True)
    for a, b in [((-2, 22), (0, 40)), ((8, 24), (9, 46)), ((18, 24), (17, 42)), ((26, 22), (24, 34))]:
        pen.line([a, b], HAIR_SHADE, 1.0)
    # nose, moustache
    pen.poly([(21, -7), (29, 0), (32, 7), (28, 11), (22, 9)], SKIN, O, 1.3, smooth=True)
    pen.poly([(13, 12), (22, 9), (30, 11), (36, 19), (31, 20), (26, 15), (20, 16), (13, 21), (9, 18)], HAIR, O, 1.2, smooth=True)
    # spangenhelm: a dome, a bronze brow band and crest band, a nasal guard
    dome = [(-20, -12), (-19, -26), (-8, -38), (8, -41), (22, -33), (28, -20), (28, -12)]
    pen.poly(dome, STEEL, smooth=False)
    pen.poly(V.catmull(dome, closed=False) + [(28, -12), (-20, -12)], STEEL)
    pen.poly([(-20, -12), (-19, -26), (-8, -38), (2, -40.5), (-2, -12)], STEEL_SHADE)
    pen.line([(12, -37), (21, -29), (24, -20)], STEEL_LIGHT, 1.6, smooth=True)
    pen.poly(V.catmull(dome, closed=False) + [(28, -12), (-20, -12)], None, O, 1.6)
    pen.poly([(2, -41), (9, -41), (10, -15), (1, -15)], GOLD, O, 1.1)
    pen.poly([(-22, -17), (30, -17), (30, -9), (-22, -9)], GOLD, O, 1.3)
    for x in (-15, -6, 14, 23):
        pen.circle((x, -13), 1.1, (150, 116, 50, 255))
    pen.poly([(19.5, -10), (23.5, -10), (23.5, 3), (21.5, 5), (19.5, 3)], STEEL, O, 1.1)


def _paint_eyes(pen: V.Pen, state: str) -> None:
    O = OUTLINE
    if state == "x":
        pen.line([(9, -5), (16, 2)], O, 1.5)
        pen.line([(9, 2), (16, -5)], O, 1.5)
    elif state == "blink":
        pen.line([(8, -1), (12, 0.6), (16, -1)], O, 1.5, smooth=True)
    else:
        pen.ellipse(12.0, -1.8, 4.4, 3.9, EYE, O, 1.0)
        pen.ellipse(13.8, -1.4, 2.2, 2.7, PUPIL)
        pen.circle((13.2, -2.6), 0.7, EYE)
    pen.poly([(4, -8.5), (18, -6.5), (18, -4), (5, -5.5)], HAIR_SHADE, O, 0.7)


def _paint_mouth(pen: V.Pen, state: int) -> None:
    O = OUTLINE
    rx, ry = [(0, 0), (4.0, 2.4), (5.0, 4.2), (6.0, 6.6)][state]
    cy = 20 + ry * 0.6
    pen.ellipse(22, cy, rx, ry, MOUTH, O, 1.1)
    if state >= 2:
        pen.ellipse(22.5, cy + ry * 0.45, rx * 0.6, ry * 0.4, TONGUE)
    if state == 3:
        pen.poly([(17.5, cy - ry * 0.75), (26.5, cy - ry * 0.75), (26, cy - ry * 0.4), (18, cy - ry * 0.4)], EYE)
    pen.poly([(13, 12), (22, 9), (30, 11), (36, 19), (31, 20), (26, 15), (20, 16), (13, 21), (9, 18)], HAIR, O, 1.2, smooth=True)


def _draw_head(img: Image.Image, J, pose: "Pose") -> None:
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


def _wraps(color: RGBA):
    def detail(pen: V.Pen) -> None:
        for x in range(6, 36, 6):
            pen.line([(x, -5), (x + 5, 5)], color, 1.3)

    return detail


def _band(x0: float, x1: float, color: RGBA, r: float, ring: RGBA = None):
    def detail(pen: V.Pen) -> None:
        pen.poly([(x0, -r), (x1, -r * 0.94), (x1, r * 0.94), (x0, r)], color, OUTLINE, 1.0)
        if ring is not None:
            pen.line([(x0 - 1.5, -r), (x0 - 1.5, r)], ring, 1.8)

    return detail


def _limb_parts(front: bool) -> dict:
    pants = PANTS if front else PANTS_SHADE
    tunic = TUNIC if front else TUNIC_SHADE
    skin = SKIN if front else SKIN_SHADE
    leather = LEATHER if front else LEATHER_DARK
    side = "near" if front else "far"
    return {
        "thigh": V.tube_piece(_k("thigh", side), THIGH, 8.6, 7.2, pants, OUTLINE, 1.6),
        "shin": V.tube_piece(_k("shin", side), SHIN, 7.2, 5.6, pants, OUTLINE, 1.6, start_cap=False, detail=_wraps(WRAP if front else WRAP_SHADE)),
        "upper": V.tube_piece(_k("upper", side), _rig_arm()[0], 7.4, 6.4, tunic, OUTLINE, 1.6, detail=_band(31, 35, TRIM, 6.6)),
        "fore": V.tube_piece(_k("fore", side), _rig_arm()[1], 6.2, 5.0, skin, OUTLINE, 1.6, start_cap=False, detail=_band(18, 35, leather, 5.6, GOLD)),
        "fist": V.fist_piece(_k("fist", side), skin, OUTLINE, 6.4),
    }


def _rig_arm():
    return (_viking_warrior_rig.UPPER_ARM, _viking_warrior_rig.FOREARM)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = V.new_canvas()
    pose = Pose(anim, frame_idx, nframes)
    J = _viking_warrior_rig.evaluate(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    near, far = _limb_parts(True), _limb_parts(False)
    boot = V.boot_piece(_k("boot"), PAL, cuff=FUR)
    raised = _viking_warrior_rig.raised(J.weapon_deg) > 0.25

    V.put(img, V.piece(_k("cape"), (56, 222, 26, 0), _paint_cape), J.root, J.body_ang, "cape")
    # legs keep the feet under the body; a falling body takes its legs along
    fall = J.body_ang if anim == "death" else 0.0
    V.leg(img, J.far_hip, 92 + pose.right_leg + fall, pose.right_lift, THIGH, SHIN, far["thigh"], far["shin"], boot, "far", fall)
    near_foot = V.leg(img, J.near_hip, 92 + pose.left_leg + fall, pose.left_lift, THIGH, SHIN, near["thigh"], near["shin"], boot, "near", fall)
    l1, l2 = _rig_arm()
    _e, far_hand = V.arm(img, J.far_shoulder, J.far_hand, l1, l2, J.far_bend, far["upper"], far["fore"], "far")
    V.put(img, V.piece(_k("body"), (52, 222, 52, 0), _paint_body), J.root, J.body_ang, "body")

    axe = V.dane_axe_piece(_k("axe"), PAL, AXE_BUTT, AXE_TIP)

    def weapon_and_hands() -> None:
        V.put(img, axe, J.grip, J.weapon_deg, "axe")
        V.put(img, far["fist"], far_hand, V.angle(_e, far_hand), "far_fist")
        V.put(img, near["fist"], near_hand, V.angle(near_elbow, near_hand), "near_fist")

    if raised:
        near_elbow, near_hand = V.arm(img, J.near_shoulder, J.near_hand, l1, l2, J.near_bend, near["upper"], near["fore"], "near")
        weapon_and_hands()
        _draw_head(img, J, pose)
    else:
        _draw_head(img, J, pose)
        near_elbow, near_hand = V.arm(img, J.near_shoulder, J.near_hand, l1, l2, J.near_bend, near["upper"], near["fore"], "near")
        weapon_and_hands()

    # effects: pieces painted once, placed with an opacity
    if anim in {"cleave", "leap_chop", "charge"} and pose.impact > 0.18:
        arc = V.swing_arc_piece(_k("arc"), FX, 62.0, span=110.0, width=7.0, lead=28.0)
        V.put(img, arc, J.grip, J.weapon_deg, "fx_arc", opacity=min(1.0, pose.impact * 1.1))
    if anim in {"walk", "charge", "leap_chop"} and (pose.left_lift > 0.5 or pose.right_lift > 0.5):
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
