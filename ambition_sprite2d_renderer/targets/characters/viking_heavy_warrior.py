"""Standalone generator for a heavy Viking warrior sprite sheet.

A broad opera / saga silhouette, clearly distinct from the slimmer vikings:
- a round horned steel helmet and a huge braided red beard
- a barrel torso in a blue tunic, a fur vest, mantle and cape
- big beefy arms and short strong legs in wrapped trousers and sandals
- a heavy double axe held in both hands; the arms follow the axe
- drawn as a rig (``_viking_common``): every rigid thing a piece painted
  once (the horns one raster, mirrored), the face a base and expression
  overlays, the beard swaying about the chin, effects pieces with opacity

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
from . import _viking_heavy_warrior_rig


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


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


TARGET_NAME = "viking_heavy_warrior"
FRAME_SIZE = (320, 320)
WORK_FRAME_SIZE = V.WORK_FRAME_SIZE
#: Work pixels to canvas pixels: the canvas is 8x the frame, so the frame is
#: a WHOLE-factor reduction of it (a turned piece reduces only that way).
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


# --- Drawn as a rig: every rigid thing is a piece painted once in its own
# frame and turned into place (``_viking_common``). The skeleton is
# ``_viking_heavy_warrior_rig``: the grip and both hands come from the axe's
# angle. The horns are ONE raster, the left one placed mirrored; the long
# beard is a piece that sways about the chin. ---

TRIM = (214, 168, 66, 255)
TRIM_DARK = (150, 58, 44, 255)
WRAP = (196, 180, 152, 255)
WRAP_SHADE = (150, 138, 116, 255)
STEEL_LIGHT = (232, 238, 244, 255)
WOOD_LIGHT = (156, 116, 74, 255)
BLUSH = (226, 128, 110, 110)

PAL = {
    "outline": OUTLINE,
    "boot": SANDAL,
    "boot_shade": (56, 40, 26, 255),
    "steel": STEEL,
    "steel_shade": STEEL_SHADE,
    "steel_light": STEEL_LIGHT,
    "wood": WOOD,
    "wood_light": WOOD_LIGHT,
    "leather_dark": LEATHER_DARK,
    "gold": GOLD,
}

#: Design lengths to the shared frame (``_viking_heavy_warrior_rig.S``).
S = _viking_heavy_warrior_rig.S
HEAD_K = 1.12 * S
HEAD_EXTENT = (40, 54, 46, 40)
THIGH, SHIN = 38.0, 36.0
AXE_BUTT, AXE_TIP = 56.0, 72.0
#: Where the horns and the long beard hang on the head (head-local design units).
HORN_ROOT: Point = (31.0, -20.0)
HEAD_MID = 3.0
BEARD_ROOT: Point = (3.0, 24.0)


def _k(*key):
    return (TARGET_NAME,) + key


def _paint_cape(pen: V.Pen) -> None:
    pts = [(-56, -262), (-20, -272), (20, -268), (30, -220), (20, -150), (8, -100), (-4, -108), (-16, -92), (-28, -104), (-42, -88), (-56, -102), (-70, -90), (-74, -130), (-72, -200), (-66, -250)]
    pen.poly(pts, FUR_SHADE, OUTLINE, 1.8)
    for x, y in [(-62, -200), (-50, -170), (-66, -150), (-44, -132), (-58, -118), (-36, -112)]:
        pen.line([(x, y), (x - 2, y + 10)], (150, 136, 122, 255), 1.1)


def _paint_body(pen: V.Pen) -> None:
    O = OUTLINE
    # pleated tunic skirt to the knee, trimmed at the hem
    skirt = [(-50, -142), (50, -142), (62, -90), (48, -82), (2, -78), (-42, -82), (-60, -90)]
    pen.poly(skirt, TUNIC)
    pen.poly([(-50, -142), (-30, -142), (-34, -80), (-42, -82), (-60, -90)], TUNIC_SHADE)
    for x in (-16, 0, 16, 32):
        pen.line([(x, -136), (x * 1.2, -82)], TUNIC_SHADE, 1.3)
    pen.line([(-59, -91), (61, -91)], TRIM, 5.0)
    for x in range(-54, 58, 7):
        pen.poly([(x, -91), (x + 3.5, -93.5), (x + 7, -91), (x + 3.5, -88.5)], TRIM_DARK)
    pen.poly(skirt, None, O, 1.8)
    # a barrel torso, the belly forward
    torso = [(-52, -258), (-20, -268), (24, -266), (54, -254), (68, -222), (74, -186), (68, -156), (52, -138), (-52, -138), (-64, -164), (-68, -210), (-62, -244)]
    pen.poly(torso, TUNIC, smooth=True)
    pen.poly([(-52, -258), (-34, -264), (-40, -190), (-38, -138), (-52, -138), (-64, -164), (-68, -210), (-62, -244)], TUNIC_SHADE)
    pen.line([(40, -236), (60, -210), (64, -176)], (124, 154, 204, 255), 2.4, smooth=True)
    pen.poly(torso, None, O, 1.8, smooth=True)
    # a fur vest down the front
    pen.poly([(-10, -250), (30, -250), (40, -200), (34, -150), (20, -150), (8, -200)], FUR, O, 1.4)
    for x, y in [(14, -232), (24, -214), (18, -190), (28, -172)]:
        pen.line([(x, y), (x + 3, y + 8)], FUR_SHADE, 1.0)
    # a broad belt with a round gold buckle
    pen.poly([(-56, -154), (56, -154), (57, -136), (-57, -136)], LEATHER, O, 1.5)
    pen.line([(-55, -145), (56, -145)], LEATHER_DARK, 1.0)
    pen.circle((22, -145), 11.0, GOLD, O, 1.4)
    pen.circle((22, -145), 6.0, (186, 140, 48, 255), O, 0.9)
    pen.circle((19, -148), 2.0, (252, 228, 150, 255))
    # the fur mantle across the shoulders
    top = V.catmull([(-72, -236), (-66, -262), (-40, -278), (0, -284), (40, -280), (66, -264), (78, -238)], closed=False)
    shag = [(72, -228), (63, -236), (55, -224), (45, -233), (35, -222), (25, -232), (15, -221), (4, -231), (-6, -220), (-16, -231), (-26, -221), (-36, -231), (-46, -222), (-56, -232), (-64, -224)]
    pen.poly(top + shag, FUR)
    pen.poly([(-72, -236), (-66, -262), (-50, -273), (-52, -230), (-56, -232), (-64, -224)], FUR_SHADE)
    for x, y in [(-30, -270), (-12, -276), (8, -276), (28, -272), (48, -262), (-48, -256)]:
        pen.line([(x, y), (x + 3, y + 10)], FUR_SHADE, 1.1)
    pen.poly(top + shag, None, O, 1.8)


def _paint_horn(pen: V.Pen) -> None:
    """The right horn from its root on the helmet, curving out and up."""
    O = OUTLINE
    pen.poly(V.horn_outline((0, 0), (30, 2), (34, -40), 7.0), HORN, O, 1.5)
    for t, w in ((0.3, 5.6), (0.5, 4.4), (0.7, 3.2)):
        (x, y), (nx, ny) = V.horn_frame((0, 0), (30, 2), (34, -40), t)
        pen.line([(x - nx * w, y - ny * w), (x + nx * w, y + ny * w)], HORN_SHADE, 1.4)
    pen.poly([(-3, -8), (4, -8), (4, 8), (-3, 8)], GOLD, O, 1.0)


def _paint_beard(pen: V.Pen) -> None:
    """The long beard hanging from the chin (+y), two braided tips."""
    O = OUTLINE
    for x in (-8, 10):
        pen.line([(x, 46), (x + 1, 60), (x, 72)], O, 8.8)
        pen.line([(x, 46), (x + 1, 60), (x, 72)], BEARD, 6.2)
        pen.line([(x - 3, 56), (x + 3, 59)], BEARD_SHADE, 1.0)
        pen.ellipse(x + 0.5, 64, 4.0, 2.6, GOLD, O, 0.9)
    pts = [(-26, -4), (28, -4), (32, 16), (28, 36), (18, 50), (2, 56), (-14, 50), (-24, 36), (-30, 14)]
    pen.poly(pts, BEARD, O, 1.8, smooth=True)
    for a, b in [((-14, 12), (-12, 40)), ((-2, 14), (0, 48)), ((10, 14), (10, 46)), ((22, 12), (20, 36))]:
        pen.line([a, b], BEARD_SHADE, 1.2)


def _paint_head_base(pen: V.Pen) -> None:
    O = OUTLINE
    # ears, a broad face, a bulbous nose
    pen.ellipse(-25, 2, 5.0, 7.0, SKIN, O, 1.3)
    pen.ellipse(31, 2, 4.0, 6.6, SKIN_SHADE, O, 1.2)
    pen.poly([(-22, -14), (2, -18), (26, -14), (30, 0), (28, 16), (16, 26), (2, 28), (-12, 24), (-23, 12), (-25, -2)], SKIN, O, 1.8, smooth=True)
    pen.ellipse(-10, 10, 5.0, 3.0, BLUSH)
    pen.ellipse(20, 10, 4.4, 3.0, BLUSH)
    # the rigid chin beard around the mouth, the moustache
    chin = [(-26, 2), (-22, 18), (-12, 30), (4, 34), (20, 30), (30, 16), (32, 2), (26, 10), (16, 17), (4, 19), (-8, 17), (-18, 11)]
    pen.poly(chin, BEARD, O, 1.6, smooth=True)
    pen.poly([(7, -3), (14, 4), (15, 10), (10, 13), (3, 12), (0, 6)], SKIN, O, 1.4, smooth=True)
    pen.line([(5, 10), (8, 11)], SKIN_SHADE, 1.0)
    pen.poly([(-14, 19), (-6, 12), (6, 11), (18, 12), (26, 19), (20, 18), (6, 15), (-8, 17)], HAIR, O, 1.3, smooth=True)
    # a round helmet with a ridge and a riveted brow band
    dome = V.catmull([(-30, -8), (-28, -28), (-14, -42), (4, -46), (22, -42), (34, -28), (36, -8)], closed=False)
    pen.poly(dome + [(36, -8), (-30, -8)], STEEL)
    pen.poly([(-30, -8), (-28, -28), (-14, -42), (-2, -45.5), (-6, -8)], STEEL_SHADE)
    pen.line([(14, -42), (26, -34), (31, -22)], STEEL_LIGHT, 1.8, smooth=True)
    pen.poly(dome + [(36, -8), (-30, -8)], None, O, 1.8)
    pen.poly([(0, -46), (8, -46), (9, -14), (-1, -14)], GOLD, O, 1.2)
    pen.poly([(-32, -15), (38, -15), (38, -6), (-32, -6)], GOLD, O, 1.4)
    for x in (-25, -15, 18, 28):
        pen.circle((x, -10.5), 1.3, (160, 120, 40, 255))


def _paint_eyes(pen: V.Pen, state: str) -> None:
    O = OUTLINE
    for cx in (-9.0, 15.0):
        if state == "x":
            pen.line([(cx - 3.5, -4), (cx + 3.5, 3)], O, 1.6)
            pen.line([(cx - 3.5, 3), (cx + 3.5, -4)], O, 1.6)
        elif state == "blink":
            pen.line([(cx - 4, 0), (cx, 1.8), (cx + 4, 0)], O, 1.6, smooth=True)
        else:
            pen.ellipse(cx, -0.5, 4.2, 3.8, EYE, O, 1.1)
            pen.ellipse(cx + 1.6, -0.2, 2.1, 2.6, PUPIL)
            pen.circle((cx + 1.0, -1.4), 0.7, EYE)
    pen.poly([(-17, -7), (-3, -5), (-3, -2.5), (-16, -4)], BEARD, O, 0.8)
    pen.poly([(7, -5), (22, -7), (23, -4), (7, -2.5)], BEARD, O, 0.8)


def _paint_mouth(pen: V.Pen, state: int) -> None:
    O = OUTLINE
    rx, ry = [(0, 0), (5.0, 2.6), (6.0, 4.6), (7.2, 7.4)][state]
    cy = 20 + ry * 0.55
    pen.ellipse(6, cy, rx, ry, MOUTH, O, 1.2)
    if state >= 2:
        pen.ellipse(6.5, cy + ry * 0.45, rx * 0.6, ry * 0.4, TONGUE)
    if state == 3:
        pen.poly([(0, cy - ry * 0.78), (12, cy - ry * 0.78), (11.5, cy - ry * 0.42), (0.5, cy - ry * 0.42)], EYE)
    pen.poly([(-14, 19), (-6, 12), (6, 11), (18, 12), (26, 19), (20, 18), (6, 15), (-8, 17)], HAIR, O, 1.3, smooth=True)


def _draw_head(img: Image.Image, J, pose: "Pose") -> None:
    H = V.frame_point(J.head_root, J.head_ang)
    k = HEAD_K
    horn = V.piece(_k("horn"), (6, 52, 44, 10), _paint_horn, k=k)
    V.put(img, horn, H((HEAD_MID + (HORN_ROOT[0] - HEAD_MID)) * k, HORN_ROOT[1] * k), J.head_ang, "horn_r")
    V.put_mirrored(img, horn, H((HEAD_MID - (HORN_ROOT[0] - HEAD_MID)) * k, HORN_ROOT[1] * k), J.head_ang, "horn_l")
    beard = V.piece(_k("beard"), (34, 8, 36, 78), _paint_beard, k=k)
    V.put(img, beard, H(BEARD_ROOT[0] * k, BEARD_ROOT[1] * k), J.head_ang + pose.beard * 0.6, "beard")
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


def _wraps(color: RGBA):
    def detail(pen: V.Pen) -> None:
        for x in range(6, 32, 6):
            pen.line([(x, -7), (x + 6, 7)], color, 1.5)

    return detail


def _muscle(r: float, band: RGBA = None, at: float = 0.0):
    def detail(pen: V.Pen) -> None:
        pen.arc(at + 18, 0, 12, r * 0.7, 200, 300, SKIN_SHADE, 1.2)
        if band is not None:
            pen.poly([(at + 6, -r * 1.02), (at + 11, -r), (at + 11, r), (at + 6, r * 1.02)], band, OUTLINE, 1.0)

    return detail


def _bracer(x0: float, x1: float, color: RGBA, r: float):
    def detail(pen: V.Pen) -> None:
        pen.poly([(x0, -r), (x1, -r * 0.92), (x1, r * 0.92), (x0, r)], color, OUTLINE, 1.1)
        for x in (x0 + 4, x1 - 4):
            pen.circle((x, 0), 1.2, GOLD)

    return detail


def _limb_parts(front: bool) -> dict:
    pants = PANTS if front else PANTS_SHADE
    skin = SKIN if front else SKIN_SHADE
    side = "near" if front else "far"
    L1, L2 = _viking_heavy_warrior_rig.UPPER_ARM, _viking_heavy_warrior_rig.FOREARM
    return {
        "thigh": V.tube_piece(_k("thigh", side), THIGH, 11.0, 9.6, pants, OUTLINE, 1.8, k=S),
        "shin": V.tube_piece(_k("shin", side), SHIN, 9.6, 7.2, pants, OUTLINE, 1.8, start_cap=False, detail=_wraps(WRAP if front else WRAP_SHADE), k=S),
        "upper": V.tube_piece(_k("upper", side), L1, 12.4, 10.6, skin, OUTLINE, 1.8, detail=_muscle(11.0, GOLD, 18.0), k=S),
        "fore": V.tube_piece(_k("fore", side), L2, 10.6, 8.0, skin, OUTLINE, 1.8, start_cap=False, detail=_bracer(24, 44, LEATHER if front else LEATHER_DARK, 8.6), k=S),
        "fist": V.fist_piece(_k("fist", side), skin, OUTLINE, 9.0, k=S),
    }


def _render_frame(anim: str, idx: int, n: int) -> Image.Image:
    img = V.new_canvas()
    pose = Pose(anim, idx, n)
    J = _viking_heavy_warrior_rig.evaluate(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    near, far = _limb_parts(True), _limb_parts(False)
    sandal = V.boot_piece(_k("sandal"), PAL, toe=16.0, height=7.0, straps=LEATHER_DARK, k=S)
    raised = _viking_heavy_warrior_rig.raised(J.weapon_deg) > 0.25
    L1, L2 = S * _viking_heavy_warrior_rig.UPPER_ARM, S * _viking_heavy_warrior_rig.FOREARM

    V.put(img, V.piece(_k("cape"), (80, 290, 36, 0), _paint_cape, k=S), J.root, J.body_ang, "cape")
    fall = J.body_ang if anim == "death" else 0.0
    V.leg(img, J.far_hip, 94 + pose.right_leg + fall, S * pose.right_lift, S * THIGH, S * SHIN, far["thigh"], far["shin"], sandal, "far", fall)
    near_foot = V.leg(img, J.near_hip, 94 + pose.left_leg + fall, S * pose.left_lift, S * THIGH, S * SHIN, near["thigh"], near["shin"], sandal, "near", fall)
    far_elbow, far_hand = V.arm(img, J.far_shoulder, J.far_hand, L1, L2, J.far_bend, far["upper"], far["fore"], "far")
    V.put(img, V.piece(_k("body"), (82, 292, 82, 0), _paint_body, k=S), J.root, J.body_ang, "body")
    axe = V.double_axe_piece(_k("axe"), PAL, AXE_BUTT, AXE_TIP, k=S)

    def weapon_and_hands() -> None:
        V.put(img, axe, J.grip, J.weapon_deg, "axe")
        V.put(img, far["fist"], far_hand, V.angle(far_elbow, far_hand), "far_fist")
        V.put(img, near["fist"], near_hand, V.angle(near_elbow, near_hand), "near_fist")

    if raised:
        near_elbow, near_hand = V.arm(img, J.near_shoulder, J.near_hand, L1, L2, J.near_bend, near["upper"], near["fore"], "near")
        weapon_and_hands()
        _draw_head(img, J, pose)
    else:
        _draw_head(img, J, pose)
        near_elbow, near_hand = V.arm(img, J.near_shoulder, J.near_hand, L1, L2, J.near_bend, near["upper"], near["fore"], "near")
        weapon_and_hands()

    # effects: pieces painted once, placed with an opacity
    H = V.frame_point(J.head_root, J.head_ang)
    if anim == "axe_cleave" and pose.impact > 0.18:
        arc = V.swing_arc_piece(_k("arc"), FX, 80.0, span=110.0, width=8.0, lead=24.0, k=S)
        V.put(img, arc, J.grip, J.weapon_deg, "fx_arc", opacity=min(1.0, pose.impact * 1.1))
    if anim == "helm_bash" and pose.impact > 0.18:
        V.put(img, V.burst_piece(_k("burst"), FX, 26.0, k=S), H(46 * HEAD_K, -24 * HEAD_K), J.head_ang, "fx_burst", opacity=min(1.0, pose.impact * 1.1))
    if anim == "bass_bellow" and pose.mouth > 0.2:
        V.put(img, V.shout_piece(_k("shout"), FX, 30.0, k=S), H(32 * HEAD_K, 22 * HEAD_K), J.head_ang, "fx_shout", opacity=min(1.0, (pose.mouth - 0.2) * 6.0))
    if anim in {"march", "helm_bash"} and (pose.left_lift > 0.5 or pose.right_lift > 0.5):
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
