"""Standalone generator for a lean pirate duelist with real side/profile rows.

This target deliberately does NOT reuse the shared pirate template. It draws a
bespoke agile silhouette: tricorn hat, bandana, ponytail, fitted bodice,
overskirt tails, tall boots, and a curved cutlass. In addition to the usual
front-facing rows, it includes dedicated left/right profile idles and turning
rows drawn with separate side-view geometry rather than a simple squashed front
view.

Only ``build_sheet`` is reused for PNG / YAML / RON emission.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from types import SimpleNamespace
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw
from . import _pirate_cutlass_viper_rig
from . import _solo_shape_rig as _rig

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_pirate_cutlass_viper",
        "display_name": "Pirate Cutlass Viper",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "story",
            "humanoid",
            "enemy",
            "combatant",
            "pirate",
            "cutlass",
            "duelist",
        ],
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
    "tags": ["story", "humanoid", "enemy", "combatant", "pirate", "cutlass", "duelist"],
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
        "poison_edge": {
            "source": "explicit.profile.pirate",
            "point": {"x": 108.0, "y": 58.0},
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

TARGET_NAME = "pirate_cutlass_viper"
FRAME_SIZE = (320, 288)
WORK_FRAME_SIZE = (640, 576)
#: Work pixels to canvas pixels: the frame is a whole-factor (8x) reduction.
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("walk", 8, 95),
    ("turn_right", 5, 90),
    ("profile_right", 4, 120),
    ("turn_left", 5, 90),
    ("profile_left", 4, 120),
    ("slash", 7, 78),
    ("taunt", 6, 110),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

OUTLINE = (20, 15, 18, 255)
SKIN = (192, 132, 92, 255)
SKIN_SHADOW = (128, 82, 56, 255)
HAIR = (58, 31, 23, 255)
HAIR_HI = (103, 69, 45, 255)
HAT = (54, 34, 28, 255)
HAT_HI = (88, 55, 43, 255)
BANDANA = (166, 34, 58, 255)
BANDANA_HI = (220, 78, 102, 220)
BLOUSE = (236, 222, 196, 255)
BODICE = (108, 46, 60, 255)
BODICE_HI = (169, 97, 111, 255)
SASH = (222, 180, 66, 255)
SKIRT = (46, 83, 120, 255)
SKIRT_HI = (86, 134, 178, 255)
BOOT = (68, 45, 34, 255)
BOOT_HI = (111, 77, 50, 255)
STEEL = (206, 212, 219, 255)
STEEL_DARK = (109, 118, 127, 255)
GOLD = (226, 180, 72, 255)
SLASH = (255, 244, 192, 155)
DUST = (132, 102, 70, 150)


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


def _rect(center: Point, w: float, h: float, deg: float) -> List[Point]:
    hw = w * 0.5
    hh = h * 0.5
    out = []
    for x, y in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
        rx, ry = _rot(x, y, deg)
        out.append((center[0] + rx, center[1] + ry))
    return out


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


class FrontPose:
    def __init__(self, anim: str, frame_idx: int, nframes: int) -> None:
        t = frame_idx / max(1, nframes - 1)
        cyc = math.tau * frame_idx / max(1, nframes)
        s = math.sin(cyc)
        c = math.cos(cyc)

        self.root_x = 0.0
        self.root_y = 0.0
        self.bob = 0.0
        self.lean = 0.0
        self.left_arm = 0.0
        self.right_arm = 0.0
        self.left_leg = 0.0
        self.right_leg = 0.0
        self.blade = -28.0
        self.blade_lift = 0.0
        self.left_foot_lift = 0.0
        self.right_foot_lift = 0.0
        self.skirt_sway = 0.0
        self.hair_swing = 0.0
        self.mouth = 0.04
        self.blink = False
        self.dead_t = 0.0
        self.impact = 0.0
        self.x_eyes = False

        if anim == "idle":
            self.root_x = s * 1.0
            self.bob = s * 1.4
            self.lean = s * 1.8
            self.left_arm = -4.0 + s * 6.0
            self.right_arm = 7.0 - s * 4.0
            self.left_leg = -3.0 + c * 1.6
            self.right_leg = 4.0 - c * 1.2
            self.blade = -24.0 + s * 5.0
            self.skirt_sway = s * 4.0
            self.hair_swing = -s * 5.0
            self.mouth = max(0.0, s) * 0.05
            self.blink = frame_idx == nframes - 2
        elif anim == "walk":
            self.root_x = s * 2.2
            self.bob = abs(s) * 2.6 - 0.6
            self.lean = s * 4.5
            self.left_leg = -24.0 * s
            self.right_leg = 24.0 * s
            self.left_arm = 18.0 * s - 6.0
            self.right_arm = -14.0 * s + 3.0
            self.blade = -30.0 - s * 8.0
            self.left_foot_lift = max(0.0, -s) * 8.0
            self.right_foot_lift = max(0.0, s) * 8.0
            self.skirt_sway = -s * 8.0
            self.hair_swing = -s * 10.0
        elif anim == "slash":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-6.0, 10.0, tt)
            self.bob = -hit * 3.0
            self.lean = _lerp(-11.0, 18.0, tt)
            self.left_arm = _lerp(12.0, -22.0, tt)
            self.right_arm = _lerp(-78.0, 54.0, tt)
            self.blade = _lerp(-124.0, 26.0, tt)
            self.blade_lift = -hit * 10.0 + tt * 11.0
            self.left_leg = -8.0 - hit * 4.0
            self.right_leg = 16.0 + hit * 8.0
            self.skirt_sway = _lerp(10.0, -15.0, tt)
            self.hair_swing = _lerp(18.0, -20.0, tt)
            self.mouth = 0.20 + hit * 0.18
            self.impact = hit
        elif anim == "taunt":
            self.root_x = s * 1.0
            self.bob = s * 1.4
            self.lean = -7.0 + s * 2.5
            self.left_arm = -44.0 + s * 6.0
            self.right_arm = -18.0 + s * 7.0
            self.blade = -64.0 + s * 6.0
            self.skirt_sway = s * 4.0
            self.hair_swing = s * 6.0
            self.mouth = 0.30
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
            self.root_x = shake * 5.0
            self.bob = -hit * 2.7
            self.lean = -17.0 * hit
            self.left_arm = 20.0 * hit
            self.right_arm = 18.0 * hit
            self.blade = -40.0 + 16.0 * hit
            self.left_leg = 8.0 * hit
            self.right_leg = -8.0 * hit
            self.skirt_sway = -10.0 * hit
            self.hair_swing = -12.0 * hit
            self.mouth = 0.22 * hit
        elif anim == "death":
            tt = _ease(t)
            self.dead_t = tt
            self.root_x = tt * 13.0
            self.root_y = tt * 5.0
            self.bob = -tt * 5.0
            self.lean = -77.0 * tt
            self.left_arm = _lerp(-2.0, 60.0, tt)
            self.right_arm = _lerp(6.0, -68.0, tt)
            self.blade = _lerp(-24.0, -116.0, tt)
            self.left_leg = _lerp(-2.0, 24.0, tt)
            self.right_leg = _lerp(4.0, -26.0, tt)
            self.skirt_sway = 14.0 * tt
            self.hair_swing = -22.0 * tt
            self.mouth = 0.25 * tt
            self.x_eyes = tt > 0.56


class SidePose:
    def __init__(
        self,
        side: int,
        openness: float,
        frame_idx: int,
        nframes: int,
        walkish: bool = False,
    ) -> None:
        cyc = math.tau * frame_idx / max(1, nframes)
        s = math.sin(cyc)
        c = math.cos(cyc)
        self.side = side
        self.openness = openness
        self.root_x = side * openness * 1.2 + s * 0.6
        self.root_y = 0.0
        self.bob = s * (1.0 + 0.4 * openness)
        self.lean = side * (-1.5 + openness * 5.5) + s * 1.0
        self.front_arm = -10.0 + s * 3.0
        self.back_arm = 6.0 - s * 2.0
        self.front_leg = -6.0 + c * 2.0
        self.back_leg = 5.0 - c * 2.0
        self.front_foot_lift = 0.0
        self.back_foot_lift = 0.0
        self.sword_angle = side * _lerp(-18.0, -55.0, openness) + s * 2.0
        self.sword_lift = 0.0
        self.skirt_sway = s * (2.0 + openness * 2.0)
        self.hair_swing = -side * openness * 8.0 - s * 3.5
        self.mouth = max(0.0, s) * 0.04
        self.blink = frame_idx == nframes - 1 and openness > 0.8
        if walkish:
            self.root_x += s * 1.2
            self.bob = abs(s) * 2.0 - 0.4
            self.front_leg = -14.0 * s
            self.back_leg = 12.0 * s
            self.front_foot_lift = max(0.0, -s) * 6.0
            self.back_foot_lift = max(0.0, s) * 4.0
            self.front_arm = -12.0 + s * 6.0
            self.back_arm = 9.0 - s * 6.0
            self.skirt_sway = -s * 5.0
            self.hair_swing = -side * openness * 10.0 - s * 5.0
            self.sword_angle = side * _lerp(-20.0, -70.0, openness) - s * 4.0


def _draw_cutlass(
    draw: ImageDraw.ImageDraw, hand: Point, angle: float, front: bool = True
) -> None:
    def tr(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, angle)
        return (hand[0] + rx, hand[1] + ry)

    _line(draw, [tr(-2, 2), tr(22, 0), tr(82, -4)], OUTLINE, 5.0)
    _line(draw, [tr(-2, 2), tr(22, 0), tr(82, -4)], STEEL_DARK, 2.2)
    _poly(draw, _rect(tr(0, 3), 12, 8, angle - 8), GOLD, OUTLINE, 1.0)
    _poly(draw, [tr(3, -2), tr(13, -12), tr(22, -10), tr(17, -1)], GOLD, OUTLINE, 0.8)
    _circle(draw, tr(-8, 3), 3.8, GOLD, OUTLINE, 0.9)
    blade = [
        tr(21, -3),
        tr(40, -10),
        tr(62, -13),
        tr(83, -11),
        tr(90, -6),
        tr(88, 2),
        tr(80, 9),
        tr(60, 14),
        tr(38, 16),
        tr(23, 12),
        tr(28, 6),
        tr(20, 2),
    ]
    _poly(draw, blade, STEEL, OUTLINE, 1.2)
    _line(draw, [tr(26, 2), tr(84, -2)], (250, 252, 252, 140), 0.8)
    if front:
        _line(draw, [tr(22, 6), tr(84, 1)], (172, 182, 188, 180), 0.7)


def _draw_boot_front(draw: ImageDraw.ImageDraw, p: Point, toe_dir: float) -> None:
    shaft = [
        (p[0] - 7, p[1] - 19),
        (p[0] + 7, p[1] - 19),
        (p[0] + 8, p[1] - 2),
        (p[0] - 8, p[1] - 2),
    ]
    _poly(draw, shaft, BOOT, OUTLINE, 1.0)
    foot = [
        (p[0] - 9, p[1] - 3),
        (p[0] + 9 + toe_dir * 2.2, p[1] - 4),
        (p[0] + 15 + toe_dir * 3.0, p[1] + 4),
        (p[0] - 8, p[1] + 6),
    ]
    _poly(draw, foot, BOOT_HI, OUTLINE, 1.0)
    _line(draw, [(p[0] - 5, p[1] - 15), (p[0] + 5, p[1] - 14)], GOLD, 0.8)


def _draw_boot_side(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    side: int,
    scale: float = 1.0,
    lifted: float = 0.0,
) -> None:
    y -= lifted
    shaft = [
        (x - 5 * scale, y - 20 * scale),
        (x + 4 * scale, y - 20 * scale),
        (x + 5 * scale, y - 4 * scale),
        (x - 6 * scale, y - 4 * scale),
    ]
    _poly(draw, shaft, BOOT, OUTLINE, 1.0)
    foot = [
        (x - 5 * scale, y - 5 * scale),
        (x + 10 * side * scale, y - 5 * scale),
        (x + 17 * side * scale, y + 1 * scale),
        (x + 10 * side * scale, y + 6 * scale),
        (x - 6 * scale, y + 5 * scale),
    ]
    _poly(draw, foot, BOOT_HI, OUTLINE, 1.0)
    _line(
        draw,
        [(x - 3 * scale, y - 15 * scale), (x + 3 * scale, y - 15 * scale)],
        GOLD,
        0.8,
    )


def _draw_front_head(draw: ImageDraw.ImageDraw, P, pose: FrontPose, part: str = "all") -> None:
    """The front head; ``part`` "tails" paints only the swinging hair tails,
    "face" everything else."""
    if part != "face":
        _draw_front_tails(draw, P, pose)
    if part != "tails":
        _draw_front_face(draw, P, pose)


def _draw_front_tails(draw: ImageDraw.ImageDraw, P, pose: FrontPose) -> None:
    tail = [
        P(18, -128),
        P(42 + pose.hair_swing * 0.35, -118),
        P(34 + pose.hair_swing * 0.55, -96),
        P(16, -101),
    ]
    _poly(draw, tail, HAIR, OUTLINE, 1.0)
    tail2 = [
        P(12, -112),
        P(30 + pose.hair_swing * 0.28, -94),
        P(18 + pose.hair_swing * 0.48, -72),
        P(7, -85),
    ]
    _poly(draw, tail2, HAIR_HI, OUTLINE, 0.8)


def _draw_front_face(draw: ImageDraw.ImageDraw, P, pose: FrontPose) -> None:
    head = [
        P(-18, -137),
        P(-8, -150),
        P(10, -151),
        P(21, -139),
        P(19, -116),
        P(10, -101),
        P(-6, -101),
        P(-19, -114),
    ]
    _poly(draw, head, SKIN, OUTLINE, 1.2)
    brim = [
        P(-33, -145),
        P(-12, -161),
        P(10, -165),
        P(32, -154),
        P(27, -138),
        P(10, -135),
        P(-7, -136),
        P(-28, -136),
    ]
    _poly(draw, brim, HAT, OUTLINE, 1.5)
    _poly(
        draw,
        [P(-31, -145), P(-19, -158), P(-6, -149), P(-10, -138)],
        HAT_HI,
        OUTLINE,
        0.8,
    )
    _poly(
        draw, [P(13, -160), P(32, -154), P(23, -140), P(8, -142)], HAT_HI, OUTLINE, 0.8
    )
    band = [P(-16, -139), P(14, -139), P(16, -131), P(-17, -131)]
    _poly(draw, band, BANDANA, OUTLINE, 0.8)
    _poly(draw, [P(16, -137), P(29, -143), P(24, -131)], BANDANA, OUTLINE, 0.8)
    _poly(draw, [P(16, -134), P(28, -123), P(19, -122)], BANDANA, OUTLINE, 0.8)
    _line(draw, [P(-14, -137), P(11, -137)], BANDANA_HI, 0.8)
    hair_l = [P(-16, -128), P(-29, -108), P(-20, -85), P(-10, -99)]
    _poly(draw, hair_l, HAIR, OUTLINE, 0.9)
    _line(draw, [P(-14, -124), P(-22, -106), P(-16, -90)], HAIR_HI, 0.8)

    eye_y = -124
    if pose.x_eyes:
        for ex in [-7, 8]:
            _line(draw, [P(ex - 4, eye_y - 4), P(ex + 4, eye_y + 4)], OUTLINE, 1.0)
            _line(draw, [P(ex - 4, eye_y + 4), P(ex + 4, eye_y - 4)], OUTLINE, 1.0)
    else:
        if pose.blink:
            _line(draw, [P(-12, eye_y), P(-4, eye_y + 1)], OUTLINE, 1.0)
            _line(draw, [P(4, eye_y + 1), P(12, eye_y)], OUTLINE, 1.0)
        else:
            _ellipse(
                draw,
                P(-8, eye_y + 2)[0],
                P(-8, eye_y + 2)[1],
                4,
                3,
                (248, 244, 234, 255),
                OUTLINE,
                0.7,
            )
            _ellipse(
                draw,
                P(8, eye_y + 2)[0],
                P(8, eye_y + 2)[1],
                4,
                3,
                (248, 244, 234, 255),
                OUTLINE,
                0.7,
            )
            _circle(draw, P(-7, eye_y + 2), 1.1, OUTLINE, OUTLINE, 0.2)
            _circle(draw, P(8, eye_y + 2), 1.1, OUTLINE, OUTLINE, 0.2)
            _line(draw, [P(-13, eye_y - 1), P(-4, eye_y - 3)], OUTLINE, 0.9)
            _line(draw, [P(4, eye_y - 3), P(13, eye_y - 1)], OUTLINE, 0.9)
        _line(draw, [P(0, -122), P(2, -114), P(-2, -112)], SKIN_SHADOW, 0.9)
        mouth_y = -107 + pose.mouth * 6.0
        if pose.mouth > 0.18:
            _ellipse(
                draw,
                P(0, mouth_y)[0],
                P(0, mouth_y)[1],
                6,
                3.0 + pose.mouth * 2.0,
                (82, 34, 40, 255),
                OUTLINE,
                0.8,
            )
        else:
            _line(
                draw, [P(-6, mouth_y), P(0, mouth_y + 2), P(7, mouth_y)], OUTLINE, 0.9
            )
    _circle(draw, P(11, -110), 0.9, OUTLINE, OUTLINE, 0.1)
    _circle(draw, P(20, -118), 2.0, GOLD, OUTLINE, 0.4)


def _draw_front_torso(draw: ImageDraw.ImageDraw, P, pose: FrontPose) -> None:
    blouse = [
        P(-29, -102),
        P(-16, -118),
        P(19, -118),
        P(31, -103),
        P(26, -73),
        P(0, -61),
        P(-25, -74),
    ]
    _poly(draw, blouse, BLOUSE, OUTLINE, 1.5)
    _ellipse(draw, P(-33, -96)[0], P(-33, -96)[1], 11, 11, BLOUSE, OUTLINE, 1.0)
    _ellipse(draw, P(33, -96)[0], P(33, -96)[1], 11, 11, BLOUSE, OUTLINE, 1.0)

    bodice = [
        P(-26, -103),
        P(-12, -115),
        P(14, -115),
        P(28, -102),
        P(26, -75),
        P(13, -63),
        P(0, -59),
        P(-15, -64),
        P(-26, -74),
    ]
    _poly(draw, bodice, BODICE, OUTLINE, 1.3)
    left_bust = [
        P(-22, -101),
        P(-8, -110),
        P(-1, -98),
        P(-5, -81),
        P(-16, -68),
        P(-24, -77),
    ]
    right_bust = [P(8, -110), P(23, -101), P(24, -77), P(14, -68), P(4, -81), P(1, -98)]
    _poly(draw, left_bust, BODICE_HI, OUTLINE, 0.8)
    _poly(draw, right_bust, BODICE_HI, OUTLINE, 0.8)
    _line(
        draw,
        [P(-18, -80), P(-8, -72), P(0, -69), P(9, -72), P(19, -80)],
        (98, 52, 66, 255),
        1.0,
    )
    _line(draw, [P(0, -110), P(0, -60)], OUTLINE, 0.8)

    belt = [P(-32, -67), P(31, -66), P(28, -54), P(-32, -55)]
    _poly(draw, belt, SASH, OUTLINE, 1.1)
    _poly(draw, [P(-7, -69), P(8, -69), P(6, -54), P(-8, -54)], GOLD, OUTLINE, 0.8)

    sway = pose.skirt_sway
    left_panel = [P(-27, -54), P(-1, -54), P(-5, 0), P(-34 + sway * 0.16, -6)]
    right_panel = [P(1, -54), P(26, -54), P(33 + sway * 0.16, -6), P(4, 0)]
    center = [P(-3, -54), P(4, -54), P(2, -6), P(-2, -6)]
    _poly(draw, left_panel, SKIRT, OUTLINE, 1.4)
    _poly(draw, right_panel, SKIRT, OUTLINE, 1.4)
    _poly(draw, center, BODICE, OUTLINE, 0.8)
    for x in [-19, -10, 10, 18]:
        _line(draw, [P(x + sway * 0.05, -50), P(x + sway * 0.12, -5)], SKIRT_HI, 0.9)
    _poly(
        draw,
        [P(-9, -62), P(-34, -58), P(-43 + sway * 0.18, -20), P(-22, -9), P(-4, -28)],
        BODICE,
        OUTLINE,
        1.0,
    )
    _poly(
        draw,
        [P(8, -62), P(32, -58), P(42 + sway * 0.18, -20), P(22, -9), P(5, -28)],
        BODICE,
        OUTLINE,
        1.0,
    )


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
_REST_ROOT: Point = (WORK_FRAME_SIZE[0] * 0.47, WORK_FRAME_SIZE[1] * 0.68)


def _P0(x: float, y: float) -> Point:
    return (_REST_ROOT[0] + x, _REST_ROOT[1] + y)


def _joints(anim: str, frame_idx: int, nframes: int) -> dict:
    """Both views' limbs at rest: the front view's from ``anim``, the side
    view's from the right profile's first frame."""
    F = _pirate_cutlass_viper_rig.evaluate_front(FrontPose(anim, frame_idx, nframes), WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    Sd = _pirate_cutlass_viper_rig.evaluate_side(SidePose(1, 1.0, 0, 4, walkish=True), WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    return {
        "left_leg": (F.left_hip, F.left_knee, F.left_foot),
        "right_leg": (F.right_hip, F.right_knee, F.right_foot),
        "left_arm": (F.left_shoulder, F.left_elbow, F.left_hand),
        "right_arm": (F.right_shoulder, F.right_elbow, F.right_hand),
        "side_back_leg": (Sd.back_hip, Sd.back_knee, Sd.back_foot),
        "side_front_leg": (Sd.front_hip, Sd.front_knee, Sd.front_foot),
        "side_back_arm": (Sd.back_shoulder, Sd.back_elbow, Sd.back_hand),
        "side_front_arm": (Sd.front_shoulder, Sd.front_elbow, Sd.front_hand),
    }


def _chains(J) -> dict:
    return J


def _draw_leg(img: Image.Image, limb: str, hip: Point, knee_ref: Point, foot: Point, width: float, line_w: float) -> None:
    knee, l1, l2 = _limb(_chains, limb, hip, knee_ref, foot)
    _put(img, _bone_piece((limb, 1), l1, width, SKIN_SHADOW, OUTLINE, line_w), hip, _deg(hip, knee), f"{limb}_thigh")
    _put(img, _bone_piece((limb, 2), l2, width, SKIN_SHADOW, OUTLINE, line_w, cap=True), knee, _deg(knee, foot), f"{limb}_shin")


def _draw_arm(img: Image.Image, limb: str, shoulder: Point, elbow_ref: Point, hand: Point, w1: float, w2: float, line_w: float, elbow_r: Tuple[float, float, float], hand_r: Tuple[float, float]) -> None:
    """Upper arm (shadowed) and forearm bones bent at the painter's elbow;
    the elbow and the hand ride their points."""
    elbow, l1, l2 = _limb(_chains, limb, shoulder, elbow_ref, hand)
    _put(img, _bone_piece((limb, 1), l1, w1, SKIN_SHADOW, OUTLINE, line_w), shoulder, _deg(shoulder, elbow), f"{limb}_upper")
    _put(img, _bone_piece((limb, 2), l2, w2, SKIN, OUTLINE, line_w, cap=True), elbow, _deg(elbow, hand), f"{limb}_fore")
    O = _BONE_O
    rx, ry, ew = elbow_r
    _put(img, _rest(("elbow", rx, ry, ew), lambda d: _ellipse(d, O[0], O[1], rx, ry, SKIN, OUTLINE, ew), O), elbow, 0.0, f"{limb}_elbow")
    r, hw = hand_r
    _put(img, _rest(("hand", r, hw), lambda d: _circle(d, O, r, SKIN, OUTLINE, hw), O), hand, 0.0, f"{limb}_hand")


def _place_cutlass(img: Image.Image, hand: Point, angle: float, front: bool, name: str) -> None:
    """The cutlass painted once at angle 0 and turned about the hand."""
    part = _rest(("cutlass", front), lambda d: _draw_cutlass(d, _MID_O, 0.0, front=front), _MID_O)
    _put(img, part, hand, angle, name)


def _render_front(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", _CANVAS, (0, 0, 0, 0))
    pose = FrontPose(anim, frame_idx, nframes)

    # Joints come from the explicit skeleton (see _pirate_cutlass_viper_rig).
    J = _pirate_cutlass_viper_rig.evaluate_front(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    root = J.root
    tilt = J.body_ang

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, tilt)
        return (root[0] + rx, root[1] + ry)

    if anim != "slash":
        _place_cutlass(img, J.back_hand, pose.blade + tilt, False, "cutlass")

    if anim == "slash" and pose.impact > 0.1:
        def arc(draw) -> None:
            cx, cy = P(38, -62)
            box = (_s(cx - 82), _s(cy - 76), _s(cx + 96), _s(cy + 64))
            draw.arc(box, 192, 342, fill=SLASH, width=_s(5.8 + pose.impact * 1.8))
            draw.arc(box, 205, 330, fill=(255, 255, 255, 120), width=_s(2.2))

        _fx_layer(img, arc, "fx_slash")

    # legs with their boots, then the arms
    for limb, hip, knee, foot in (("left_leg", J.left_hip, J.left_knee, J.left_foot), ("right_leg", J.right_hip, J.right_knee, J.right_foot)):
        _draw_leg(img, limb, hip, knee, foot, 5.9, 1.4)
        toe = 1 if foot[0] > hip[0] else -1
        _put(img, _rest(("boot_front", toe), lambda d, toe=toe: _draw_boot_front(d, _MID_O, toe), _MID_O), foot, 0.0, f"{limb}_boot")
    _draw_arm(img, "left_arm", J.left_shoulder, J.left_elbow, J.left_hand, 7.2, 6.4, 1.7, (6.3, 7.2, 1.0), (5.5, 1.0))
    _draw_arm(img, "right_arm", J.right_shoulder, J.right_elbow, J.right_hand, 7.2, 6.4, 1.7, (6.3, 7.2, 1.0), (5.5, 1.0))

    # torso (the skirt sways in a few steps), hair tails, face: pieces riding the body
    sway = _rig.q(pose.skirt_sway, 1.0)
    torso = _rest(("front_torso", sway), lambda d: _draw_front_torso(d, _P0, SimpleNamespace(skirt_sway=sway)), _REST_ROOT)
    _put(img, torso, root, tilt, "torso")
    hair = _rig.q(pose.hair_swing, 2.0)
    tails = _rest(("front_tails", hair), lambda d: _draw_front_tails(d, _P0, SimpleNamespace(hair_swing=hair)), _REST_ROOT)
    _put(img, tails, root, tilt, "hair_tails")
    face_pose = SimpleNamespace(x_eyes=pose.x_eyes, blink=pose.blink, mouth=_rig.q(pose.mouth, 0.04))
    face = _rest(("front_face", face_pose.x_eyes, face_pose.blink, face_pose.mouth), lambda d: _draw_front_face(d, _P0, face_pose), _REST_ROOT)
    _put(img, face, root, tilt, "face")

    if anim == "slash":
        _place_cutlass(img, J.right_hand, pose.blade + tilt, True, "cutlass")

    if anim == "slash" and pose.impact > 0.46:
        def dust(draw) -> None:
            for i, (dx, dy) in enumerate([(-38, 5), (-26, 11), (30, 6), (45, 10)]):
                jitter = math.sin(frame_idx + i) * 1.4
                c = P(dx + jitter, dy)
                _poly(draw, [(c[0] - 2.2, c[1] - 1.4), (c[0] + 2.7, c[1]), (c[0], c[1] + 2.8)], DUST, (88, 68, 45, 110), 0.4)

        _fx_layer(img, dust, "fx_dust")

    return _downsample(img)


def _paint_side_torso(draw: ImageDraw.ImageDraw, side: int, sway: float) -> None:
    P = _P0
    _poly(draw, [P(-12 * side, -106), P(-1 * side, -116), P(8 * side, -111), P(5 * side, -70), P(-10 * side, -65)], BLOUSE, OUTLINE, 1.0)
    _poly(draw, [P(-10 * side, -105), P(7 * side, -113), P(17 * side, -102), P(18 * side, -83), P(13 * side, -68), P(2 * side, -59), P(-10 * side, -65), P(-12 * side, -86)], BODICE, OUTLINE, 1.2)
    _poly(draw, [P(3 * side, -108), P(16 * side, -98), P(20 * side, -86), P(14 * side, -71), P(4 * side, -66), P(-1 * side, -82)], BODICE_HI, OUTLINE, 0.9)
    _line(draw, [P(-1 * side, -90), P(10 * side, -79), P(16 * side, -72)], (98, 52, 66, 255), 1.0)
    _poly(draw, [P(-16 * side, -104), P(-9 * side, -112), P(0 * side, -108), P(-1 * side, -91), P(-14 * side, -90)], BLOUSE, OUTLINE, 0.8)
    _poly(draw, [P(4 * side, -108), P(16 * side, -113), P(23 * side, -103), P(22 * side, -88), P(8 * side, -90)], BLOUSE, OUTLINE, 0.8)
    _poly(draw, [P(-12 * side, -67), P(15 * side, -66), P(17 * side, -54), P(-10 * side, -54)], SASH, OUTLINE, 1.0)
    _poly(draw, [P(0 * side, -68), P(9 * side, -68), P(9 * side, -54), P(0 * side, -54)], GOLD, OUTLINE, 0.8)
    rear_tail = [P(-5 * side, -60), P(-18 * side, -58), P(-28 * side - sway * 0.20 * side, -22), P(-11 * side, -8), P(1 * side, -28)]
    front_tail = [P(6 * side, -61), P(25 * side, -56), P(34 * side + sway * 0.28 * side, -17), P(16 * side, -3), P(1 * side, -20)]
    skirt_front = [P(-4 * side, -54), P(14 * side, -53), P(24 * side + sway * 0.22 * side, -7), P(1 * side, 1)]
    skirt_back = [P(-10 * side, -54), P(-1 * side, -54), P(2 * side, 1), P(-18 * side - sway * 0.12 * side, -4)]
    _poly(draw, rear_tail, BODICE, OUTLINE, 1.0)
    _poly(draw, front_tail, BODICE, OUTLINE, 1.0)
    _poly(draw, skirt_back, SKIRT, OUTLINE, 1.1)
    _poly(draw, skirt_front, SKIRT, OUTLINE, 1.3)
    _line(draw, [P(2 * side, -49), P(17 * side + sway * 0.15 * side, -9)], SKIRT_HI, 0.9)
    _line(draw, [P(-6 * side, -49), P(-11 * side - sway * 0.08 * side, -7)], SKIRT_HI, 0.7)


def _paint_side_tails(draw: ImageDraw.ImageDraw, side: int, hair: float) -> None:
    P = _P0
    tail = [P(-7 * side, -127), P(-22 * side - hair * 0.2 * side, -118), P(-28 * side - hair * 0.35 * side, -96), P(-12 * side, -98)]
    tail2 = [P(-4 * side, -114), P(-18 * side - hair * 0.20 * side, -97), P(-20 * side - hair * 0.28 * side, -76), P(-8 * side, -85)]
    _poly(draw, tail, HAIR, OUTLINE, 1.0)
    _poly(draw, tail2, HAIR_HI, OUTLINE, 0.8)


def _paint_side_head(draw: ImageDraw.ImageDraw, side: int, blink: bool, mouth: float) -> None:
    P = _P0
    head = [
        P(-12 * side, -139), P(-2 * side, -151), P(10 * side, -150), P(18 * side, -141), P(20 * side, -130), P(15 * side, -121),
        P(18 * side, -114), P(13 * side, -106), P(2 * side, -101), P(-10 * side, -106), P(-16 * side, -118), P(-16 * side, -131),
    ]
    _poly(draw, head, SKIN, OUTLINE, 1.2)
    hat = [P(-28 * side, -148), P(-12 * side, -160), P(6 * side, -165), P(27 * side, -158), P(36 * side, -147), P(27 * side, -139), P(6 * side, -136), P(-21 * side, -137)]
    _poly(draw, hat, HAT, OUTLINE, 1.4)
    _poly(draw, [P(-22 * side, -146), P(-9 * side, -157), P(2 * side, -149), P(-2 * side, -140)], HAT_HI, OUTLINE, 0.8)
    _poly(draw, [P(-14 * side, -139), P(14 * side, -138), P(16 * side, -131), P(-15 * side, -131)], BANDANA, OUTLINE, 0.8)
    _poly(draw, [P(16 * side, -137), P(28 * side, -141), P(24 * side, -130)], BANDANA, OUTLINE, 0.7)
    _poly(draw, [P(18 * side, -136), P(30 * side, -126), P(20 * side, -122)], BANDANA, OUTLINE, 0.7)
    _poly(draw, [P(18 * side, -138), P(29 * side, -145), P(25 * side, -133)], BANDANA, OUTLINE, 0.7)
    _line(draw, [P(-12 * side, -137), P(8 * side, -137)], BANDANA_HI, 0.8)
    if blink:
        _line(draw, [P(4 * side, -122), P(12 * side, -123)], OUTLINE, 0.9)
    else:
        _ellipse(draw, P(8 * side, -121)[0], P(8 * side, -121)[1], 4.6, 3.2, (248, 244, 234, 255), OUTLINE, 0.7)
        _circle(draw, P(9 * side, -121), 1.1, OUTLINE, OUTLINE, 0.2)
        _line(draw, [P(2 * side, -125), P(12 * side, -127)], OUTLINE, 0.9)
        _line(draw, [P(12 * side, -124), P(15 * side, -127)], OUTLINE, 0.8)
    _line(draw, [P(11 * side, -121), P(18 * side, -116), P(12 * side, -110)], SKIN_SHADOW, 0.9)
    mouth_y = -107 + mouth * 5.0
    if mouth > 0.16:
        _ellipse(draw, P(8 * side, mouth_y)[0], P(8 * side, mouth_y)[1], 4.8, 2.8 + mouth * 1.8, (82, 34, 40, 255), OUTLINE, 0.8)
    else:
        _line(draw, [P(4 * side, mouth_y), P(10 * side, mouth_y + 1)], OUTLINE, 0.8)
    _circle(draw, P(15 * side, -118), 1.9, GOLD, OUTLINE, 0.4)
    _circle(draw, P(11 * side, -109), 0.8, OUTLINE, OUTLINE, 0.1)


def _render_side(turn_side: int, openness: float, frame_idx: int, nframes: int, *, walkish: bool = False) -> Image.Image:
    """Draw genuine side/profile geometry.

    ``openness`` ranges from 0 (nearly front) to 1 (full profile), but this is
    not a simple width squash; body parts use dedicated side-view placements.
    """
    img = Image.new("RGBA", _CANVAS, (0, 0, 0, 0))
    pose = SidePose(turn_side, openness, frame_idx, nframes, walkish=walkish)
    side = pose.side

    # Joints come from the explicit skeleton (see _pirate_cutlass_viper_rig).
    J = _pirate_cutlass_viper_rig.evaluate_side(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    root = J.root
    tilt = J.body_ang

    # --- legs: back leg behind, front leg leading the pose ---------------
    _draw_leg(img, "side_back_leg", J.back_hip, J.back_knee, J.back_foot, 4.4, 1.1)
    boot = _rest(("boot_side", side, 0.85), lambda d: _draw_boot_side(d, _MID_O[0], _MID_O[1], side, scale=0.85), _MID_O)
    _put(img, boot, J.back_foot, 0.0, "back_boot")
    _draw_leg(img, "side_front_leg", J.front_hip, J.front_knee, J.front_foot, 5.8, 1.4)
    boot = _rest(("boot_side", side, 1.0), lambda d: _draw_boot_side(d, _MID_O[0], _MID_O[1], side, scale=1.0), _MID_O)
    _put(img, boot, J.front_foot, 0.0, "front_boot")

    # --- back arm / off arm ----------------------------------------------
    _draw_arm(img, "side_back_arm", J.back_shoulder, J.back_elbow, J.back_hand, 4.7, 4.4, 1.1, (4.5, 5.4, 0.8), (4.1, 0.8))

    # --- torso: dedicated side silhouette (the skirt sways in a few steps) --
    sway = _rig.q(pose.skirt_sway, 1.0)
    _put(img, _rest(("side_torso", side, sway), lambda d: _paint_side_torso(d, side, sway), _REST_ROOT), root, tilt, "torso")

    # --- weapon arm in front ---------------------------------------------
    front_hand = J.front_hand
    _draw_arm(img, "side_front_arm", J.front_shoulder, J.front_elbow, front_hand, 6.0, 5.4, 1.3, (5.5, 6.0, 0.8), (4.9, 0.8))

    # --- head: actual profile geometry -----------------------------------
    hair = _rig.q(pose.hair_swing, 2.0)
    _put(img, _rest(("side_tails", side, hair), lambda d: _paint_side_tails(d, side, hair), _REST_ROOT), root, tilt, "hair_tails")
    mouth = _rig.q(pose.mouth, 0.04)
    _put(img, _rest(("side_head", side, pose.blink, mouth), lambda d: _paint_side_head(d, side, pose.blink, mouth), _REST_ROOT), root, tilt, "face")

    # cutlass always visible in turn/profile rows
    _place_cutlass(img, front_hand, pose.sword_angle + tilt, True, "cutlass")

    return _downsample(img)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    if anim in {"turn_right", "profile_right", "turn_left", "profile_left"}:
        if anim == "turn_right":
            return _render_side(
                1, _ease(frame_idx / max(1, nframes - 1)), frame_idx, nframes
            )
        if anim == "turn_left":
            return _render_side(
                -1, _ease(frame_idx / max(1, nframes - 1)), frame_idx, nframes
            )
        if anim == "profile_right":
            return _render_side(1, 1.0, frame_idx, nframes, walkish=True)
        return _render_side(-1, 1.0, frame_idx, nframes, walkish=True)
    return _render_front(anim, frame_idx, nframes)


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
        description="Render the Cutlass Viper pirate spritesheet with dedicated side/profile and turning animations."
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
