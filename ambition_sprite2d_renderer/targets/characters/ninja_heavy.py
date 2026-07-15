"""Procedural Iron Lotus redesign for the heavy ninja sprite.

The previous target read as a small hooded figure carrying a pale axe-like
shape.  This version rebuilds the character around a stronger silhouette and a
clear visual hierarchy: an oni-inspired iron mask, layered lamellar armor,
asymmetric shoulder plating, broad split hakama, wrapped greaves, and a truly
massive studded kanabo.  Every frame remains authored in Python/Pillow and goes
through the normal Ambition sheet build/publish path.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet

ACTOR_METADATA = {
    "actor": {"character_id": "npc_ninja_heavy", "display_name": "Ninja Heavy"},
    "lineage": {
        "family": "npc_ninja_heavy",
        "variant": "iron_lotus",
        "parents": ["npc_ninja_heavy/legacy"],
        "creator": {
            "kind": "model",
            "model": "GPT-5.6 Thinking",
        },
        "method": "procedural_python_pillow",
        "revision": "anatomy_and_connectivity_polish",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": ["story", "humanoid", "enemy", "combatant", "ninja", "heavy"],
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
    "tags": ["story", "humanoid", "enemy", "combatant", "ninja", "heavy"],
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
        "interaction.talk": {"animation": "taunt", "events": []},
        "interaction.use": {"animation": "taunt", "events": []},
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

TARGET_NAME = "ninja_heavy"
FRAME_SIZE = (320, 288)
WORK_FRAME_SIZE = (640, 576)
SUPER = 4
FIGURE_SCALE = 1.46
WEAPON_SCALE = 1.02
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("walk", 8, 95),
    ("slash", 7, 80),
    ("taunt", 6, 110),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

# Palette: near-black cloth, blue-black armor, lacquer red, aged brass, and
# cold iron.  The values are separated enough to survive low-quality scaling.
TRANSPARENT = (0, 0, 0, 0)
OUTLINE = (10, 12, 17, 255)
OUTLINE_SOFT = (22, 25, 33, 255)
SHADOW = (12, 14, 22, 88)
SMOKE = (36, 43, 58, 115)
UNDERSUIT = (17, 21, 30, 255)
CLOTH_DEEP = (23, 28, 39, 255)
CLOTH = (39, 47, 63, 255)
CLOTH_MID = (63, 74, 95, 255)
CLOTH_HI = (104, 117, 143, 255)
ARMOR_DEEP = (31, 38, 55, 255)
ARMOR = (53, 66, 92, 255)
ARMOR_HI = (91, 111, 149, 255)
LACQUER = (112, 24, 31, 255)
LACQUER_HI = (190, 47, 49, 255)
LACQUER_GLOW = (255, 91, 70, 255)
BRASS_DARK = (100, 70, 34, 255)
BRASS = (181, 135, 59, 255)
BRASS_HI = (232, 190, 93, 255)
IRON_DEEP = (43, 47, 55, 255)
IRON = (89, 96, 108, 255)
IRON_HI = (157, 166, 178, 255)
WRAP = (79, 48, 45, 255)
WRAP_HI = (149, 91, 77, 255)
ROPE = (165, 124, 68, 255)
ROPE_HI = (222, 180, 101, 255)
SKIN_SHADOW = (93, 57, 47, 255)
EYE = (241, 46, 48, 255)
EYE_CORE = (255, 176, 113, 255)
DUST = (142, 117, 79, 155)
WHITE_FLASH = (255, 240, 215, 195)


def _s(value: float) -> int:
    return int(round(value * SUPER))


def _pt(point: Point) -> Tuple[int, int]:
    return (_s(point[0]), _s(point[1]))


def _box(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = _clamp01(t)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _smoothstep(t: float) -> float:
    t = _clamp01(t)
    return t * t * (3.0 - 2.0 * t)


def _rot(x: float, y: float, deg: float) -> Point:
    rad = math.radians(deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return (x * c - y * s, x * s + y * c)


def _add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def _polar(origin: Point, length: float, deg: float) -> Point:
    dx, dy = _rot(length, 0.0, deg)
    return (origin[0] + dx, origin[1] + dy)


def _poly(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    pts = [_pt(p) for p in points]
    draw.polygon(pts, fill=fill)
    if outline is not None and width > 0:
        draw.line(pts + [pts[0]], fill=outline, width=max(1, _s(width)), joint="curve")


def _line(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    width: float = 1.0,
) -> None:
    draw.line(
        [_pt(p) for p in points],
        fill=fill,
        width=max(1, _s(width)),
        joint="curve",
    )


def _ellipse(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        _box(cx, cy, rx, ry),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)) if outline is not None and width > 0 else 1,
    )


def _circle(
    draw: ImageDraw.ImageDraw,
    point: Point,
    radius: float,
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    _ellipse(draw, point[0], point[1], radius, radius, fill, outline, width)


def _quad(center: Point, width: float, height: float, deg: float) -> List[Point]:
    hw = width * 0.5
    hh = height * 0.5
    out: List[Point] = []
    for x, y in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
        rx, ry = _rot(x, y, deg)
        out.append((center[0] + rx, center[1] + ry))
    return out


def _segment_polygon(
    a: Point,
    b: Point,
    start_radius: float,
    end_radius: float,
) -> List[Point]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = max(1e-6, math.hypot(dx, dy))
    nx = -dy / length
    ny = dx / length
    return [
        (a[0] + nx * start_radius, a[1] + ny * start_radius),
        (b[0] + nx * end_radius, b[1] + ny * end_radius),
        (b[0] - nx * end_radius, b[1] - ny * end_radius),
        (a[0] - nx * start_radius, a[1] - ny * start_radius),
    ]


def _draw_segment(
    draw: ImageDraw.ImageDraw,
    a: Point,
    b: Point,
    start_radius: float,
    end_radius: float,
    fill: RGBA,
    *,
    highlight: RGBA | None = None,
) -> None:
    _poly(draw, _segment_polygon(a, b, start_radius, end_radius), fill, OUTLINE, 1.5)
    _circle(draw, a, start_radius, fill, OUTLINE, 1.2)
    _circle(draw, b, end_radius, fill, OUTLINE, 1.2)
    if highlight is not None:
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        length = max(1e-6, math.hypot(dx, dy))
        nx = -dy / length
        ny = dx / length
        inset_a = (a[0] + nx * start_radius * 0.45, a[1] + ny * start_radius * 0.45)
        inset_b = (b[0] + nx * end_radius * 0.45, b[1] + ny * end_radius * 0.45)
        _line(draw, [inset_a, inset_b], highlight, 1.0)


def _draw_solid_segment(
    draw: ImageDraw.ImageDraw,
    a: Point,
    b: Point,
    start_radius: float,
    end_radius: float,
    fill: RGBA,
) -> None:
    """Paint a joint-safe capsule without an internal outline.

    This is used for the continuous cloth undersuit beneath armor and robes.
    The visible costume can overlap or occlude it, but transparent cracks can
    no longer appear between neighboring anatomical pieces.
    """
    _poly(draw, _segment_polygon(a, b, start_radius, end_radius), fill, None, 0)
    _circle(draw, a, start_radius, fill, None, 0)
    _circle(draw, b, end_radius, fill, None, 0)


def _downsample(image: Image.Image) -> Image.Image:
    return image.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


@dataclass
class Pose:
    anim: str
    frame_idx: int
    nframes: int
    root_x: float = 0.0
    root_y: float = 0.0
    bob: float = 0.0
    torso: float = 0.0
    head: float = 0.0
    crouch: float = 0.0
    left_arm: float = 0.0
    right_arm: float = 0.0
    left_leg: float = 0.0
    right_leg: float = 0.0
    left_foot_lift: float = 0.0
    right_foot_lift: float = 0.0
    cloth_sway: float = 0.0
    weapon_angle: float = -58.0
    weapon_shift_x: float = 0.0
    weapon_shift_y: float = 0.0
    weapon_front: bool = False
    strike: float = 0.0
    recoil: float = 0.0
    taunt: float = 0.0
    eye_flare: float = 0.0
    death: float = 0.0
    death_weapon: float = 0.0
    x_eyes: bool = False

    def __post_init__(self) -> None:
        t = self.frame_idx / max(1, self.nframes - 1)
        phase = math.tau * self.frame_idx / max(1, self.nframes)
        s = math.sin(phase)
        c = math.cos(phase)

        if self.anim == "idle":
            breath = 0.5 + 0.5 * s
            self.root_x = s * 1.0
            self.bob = -breath * 2.0
            self.torso = -4.0 + s * 1.4
            self.head = 2.0 - s * 1.1
            self.crouch = 2.0 + breath * 1.5
            self.left_arm = -6.0 + s * 3.0
            self.right_arm = 5.0 - s * 2.5
            self.left_leg = -3.0 + c * 1.5
            self.right_leg = 3.0 - c * 1.5
            self.cloth_sway = s * 2.5
            self.weapon_angle = -56.0 + s * 2.0
            self.eye_flare = 0.18 + max(0.0, s) * 0.12
        elif self.anim == "walk":
            stride = math.sin(phase)
            step = abs(stride)
            self.root_x = stride * 2.2
            self.bob = step * 4.0 - 1.5
            self.torso = -8.0 + stride * 3.0
            self.head = 4.0 - stride * 1.8
            self.crouch = 4.0 + step * 2.0
            self.left_leg = stride * 23.0
            self.right_leg = -stride * 23.0
            self.left_foot_lift = max(0.0, -stride) * 10.0
            self.right_foot_lift = max(0.0, stride) * 10.0
            self.left_arm = -stride * 15.0 - 5.0
            self.right_arm = stride * 10.0 + 4.0
            self.cloth_sway = -stride * 8.0
            self.weapon_angle = -62.0 - stride * 6.0
            self.eye_flare = 0.28
        elif self.anim == "slash":
            if t < 0.28:
                wind = _ease(t / 0.28)
                self.torso = _lerp(-5.0, -19.0, wind)
                self.head = _lerp(2.0, 9.0, wind)
                self.crouch = _lerp(3.0, 11.0, wind)
                self.root_x = _lerp(0.0, -10.0, wind)
                self.left_arm = _lerp(-5.0, -24.0, wind)
                self.right_arm = _lerp(4.0, -52.0, wind)
                self.weapon_angle = _lerp(-56.0, -142.0, wind)
                self.weapon_shift_y = _lerp(0.0, -7.0, wind)
                self.eye_flare = _lerp(0.25, 0.8, wind)
            elif t < 0.72:
                hit = _ease((t - 0.28) / 0.44)
                self.strike = math.sin(hit * math.pi)
                self.torso = _lerp(-19.0, 21.0, hit)
                self.head = _lerp(9.0, -5.0, hit)
                self.crouch = 11.0 - self.strike * 5.0
                self.root_x = _lerp(-10.0, 15.0, hit)
                self.root_y = -self.strike * 4.0
                self.left_arm = _lerp(-24.0, 28.0, hit)
                self.right_arm = _lerp(-52.0, 29.0, hit)
                self.weapon_angle = _lerp(-142.0, 28.0, hit)
                self.weapon_shift_x = hit * 4.0
                self.weapon_shift_y = -self.strike * 8.0
                self.weapon_front = hit > 0.18
                self.left_leg = -8.0 - self.strike * 6.0
                self.right_leg = 10.0 + self.strike * 8.0
                self.cloth_sway = _lerp(8.0, -13.0, hit)
                self.eye_flare = 1.0
            else:
                recover = _smoothstep((t - 0.72) / 0.28)
                self.torso = _lerp(21.0, -3.0, recover)
                self.head = _lerp(-5.0, 1.0, recover)
                self.crouch = _lerp(6.0, 3.0, recover)
                self.root_x = _lerp(15.0, 1.0, recover)
                self.left_arm = _lerp(28.0, -4.0, recover)
                self.right_arm = _lerp(29.0, 5.0, recover)
                self.weapon_angle = _lerp(28.0, -54.0, recover)
                self.weapon_front = recover < 0.55
                self.cloth_sway = _lerp(-13.0, 0.0, recover)
                self.eye_flare = _lerp(1.0, 0.3, recover)
        elif self.anim == "taunt":
            pulse = 0.5 + 0.5 * s
            self.taunt = pulse
            self.root_x = s * 0.8
            self.bob = -pulse * 2.0
            self.torso = -10.0 + s * 2.2
            self.head = -5.0 - s * 2.0
            self.crouch = 4.0
            self.left_arm = -82.0 + s * 7.0
            self.right_arm = -7.0 + s * 4.0
            self.weapon_angle = -84.0 + s * 3.0
            self.weapon_shift_y = -pulse * 2.0
            self.cloth_sway = s * 4.0
            self.eye_flare = 0.72 + pulse * 0.28
        elif self.anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
            self.recoil = hit
            self.root_x = shake * 6.0 - hit * 6.0
            self.root_y = -hit * 3.0
            self.bob = -hit * 2.0
            self.torso = -22.0 * hit
            self.head = 15.0 * hit
            self.crouch = 5.0 + hit * 7.0
            self.left_arm = 27.0 * hit
            self.right_arm = 22.0 * hit
            self.weapon_angle = -58.0 + hit * 20.0
            self.left_leg = 7.0 * hit
            self.right_leg = -7.0 * hit
            self.cloth_sway = -10.0 * hit
            self.eye_flare = 0.55
        elif self.anim == "death":
            fall = _ease(t)
            drop = _ease(_clamp01((t - 0.12) / 0.7))
            self.death = fall
            self.death_weapon = drop
            self.root_x = fall * 23.0
            self.root_y = fall * 14.0
            self.bob = -fall * 3.0
            self.torso = -88.0 * fall
            self.head = 21.0 * fall
            self.crouch = fall * 8.0
            self.left_arm = _lerp(-6.0, 64.0, fall)
            self.right_arm = _lerp(4.0, -58.0, fall)
            self.weapon_angle = _lerp(-56.0, 37.0, drop)
            self.weapon_shift_x = drop * 20.0
            self.weapon_shift_y = drop * 30.0
            self.left_leg = _lerp(-3.0, 25.0, fall)
            self.right_leg = _lerp(3.0, -24.0, fall)
            self.cloth_sway = fall * 13.0
            self.eye_flare = _lerp(0.25, 0.0, fall)
            self.x_eyes = fall > 0.62


@dataclass
class Rig:
    root: Point
    pelvis: Point
    chest: Point
    neck: Point
    head: Point
    left_shoulder: Point
    right_shoulder: Point
    left_elbow: Point
    right_elbow: Point
    left_hand: Point
    right_hand: Point
    left_hip: Point
    right_hip: Point
    left_knee: Point
    right_knee: Point
    left_foot: Point
    right_foot: Point


def _build_rig(pose: Pose) -> Tuple[Rig, callable]:
    frame_center_x = WORK_FRAME_SIZE[0] * 0.46
    if pose.anim == "slash":
        frame_center_x -= 36.0
    root = (
        frame_center_x + pose.root_x + pose.death * 8.0,
        WORK_FRAME_SIZE[1] * 0.76 + pose.root_y + pose.bob,
    )

    def local(x: float, y: float) -> Point:
        x *= FIGURE_SCALE
        y *= FIGURE_SCALE
        rx, ry = _rot(x, y, pose.torso)
        return (root[0] + rx, root[1] + ry)

    pelvis = local(0.0, -54.0 + pose.crouch * 0.2)
    chest = local(0.0, -104.0 + pose.crouch * 0.25)
    neck = local(0.0, -137.0 + pose.crouch * 0.18)
    head_offset = _rot(0.0, -25.0 * FIGURE_SCALE, pose.torso + pose.head)
    head = _add(neck, head_offset)

    left_shoulder = local(-37.0, -113.0)
    right_shoulder = local(39.0, -112.0)

    left_upper = -112.0 + pose.torso + pose.left_arm
    left_fore = -28.0 + pose.torso + pose.left_arm * 0.55
    right_upper = -66.0 + pose.torso + pose.right_arm
    right_fore = -13.0 + pose.torso + pose.right_arm * 0.52

    left_elbow = _polar(left_shoulder, 38.0 * FIGURE_SCALE, left_upper)
    left_hand = _polar(left_elbow, 34.0 * FIGURE_SCALE, left_fore)
    right_elbow = _polar(right_shoulder, 40.0 * FIGURE_SCALE, right_upper)
    right_hand = _polar(right_elbow, 34.0 * FIGURE_SCALE, right_fore)
    right_hand = (
        right_hand[0] + pose.weapon_shift_x * FIGURE_SCALE,
        right_hand[1] + pose.weapon_shift_y * FIGURE_SCALE,
    )

    left_hip = local(-19.0, -55.0)
    right_hip = local(19.0, -55.0)
    left_knee = local(-24.0 + pose.left_leg * 0.22, -25.0 + pose.crouch * 0.45)
    right_knee = local(24.0 + pose.right_leg * 0.22, -25.0 + pose.crouch * 0.45)
    left_foot = local(
        -31.0 + pose.left_leg * 0.25,
        8.0 + pose.crouch - pose.left_foot_lift,
    )
    right_foot = local(
        31.0 + pose.right_leg * 0.25,
        8.0 + pose.crouch - pose.right_foot_lift,
    )

    return (
        Rig(
            root=root,
            pelvis=pelvis,
            chest=chest,
            neck=neck,
            head=head,
            left_shoulder=left_shoulder,
            right_shoulder=right_shoulder,
            left_elbow=left_elbow,
            right_elbow=right_elbow,
            left_hand=left_hand,
            right_hand=right_hand,
            left_hip=left_hip,
            right_hip=right_hip,
            left_knee=left_knee,
            right_knee=right_knee,
            left_foot=left_foot,
            right_foot=right_foot,
        ),
        local,
    )


def _draw_ground_shadow(draw: ImageDraw.ImageDraw, rig: Rig, pose: Pose) -> None:
    width = 60.0 * FIGURE_SCALE * (1.0 - pose.death * 0.12)
    height = 10.0 * FIGURE_SCALE
    cx = rig.root[0] + pose.death * 14.0
    cy = rig.root[1] + 10.0 * FIGURE_SCALE
    _ellipse(draw, cx, cy, width, height, SHADOW, None, 0)
    _ellipse(draw, cx - 5, cy - 1, width * 0.62, height * 0.55, (8, 10, 16, 55), None, 0)


def _draw_smoke_ribbon(draw: ImageDraw.ImageDraw, rig: Rig, pose: Pose) -> None:
    sway = pose.cloth_sway * FIGURE_SCALE
    y = rig.pelvis[1] + 30.0 * FIGURE_SCALE
    points = [
        (rig.pelvis[0] - 43 * FIGURE_SCALE, y - 5),
        (rig.pelvis[0] - 64 * FIGURE_SCALE + sway, y + 7),
        (rig.pelvis[0] - 35 * FIGURE_SCALE + sway * 0.5, y + 15),
        (rig.pelvis[0] + 4 * FIGURE_SCALE, y + 8),
        (rig.pelvis[0] + 47 * FIGURE_SCALE - sway * 0.3, y + 14),
        (rig.pelvis[0] + 63 * FIGURE_SCALE - sway, y + 4),
        (rig.pelvis[0] + 39 * FIGURE_SCALE, y - 8),
    ]
    _poly(draw, points, SMOKE, None, 0)


def _draw_anatomical_understructure(
    draw: ImageDraw.ImageDraw,
    rig: Rig,
    local,
) -> None:
    """Draw the continuous body beneath the visible costume.

    Armor, sleeves, hakama, and boots are separate design layers, but the
    character is not assembled from floating stickers.  A broad cloth yoke,
    wrapped neck, trunk, pelvis, and complete limb capsules establish a real
    connected humanoid body first; costume layers then describe its surface.
    """
    # Central trunk, shoulder yoke, and pelvis.  These deliberately overlap
    # their neighboring joints by several pixels at final resolution.
    trunk = [
        local(-32, -121),
        local(32, -121),
        local(35, -58),
        local(23, -45),
        local(-23, -45),
        local(-35, -58),
    ]
    _poly(draw, trunk, UNDERSUIT, None, 0)
    _draw_solid_segment(
        draw, rig.left_shoulder, rig.right_shoulder,
        14.5 * FIGURE_SCALE, 14.5 * FIGURE_SCALE, UNDERSUIT,
    )
    _draw_solid_segment(
        draw, rig.chest, rig.pelvis,
        27.0 * FIGURE_SCALE, 25.0 * FIGURE_SCALE, UNDERSUIT,
    )
    _draw_solid_segment(
        draw, rig.left_hip, rig.right_hip,
        15.0 * FIGURE_SCALE, 15.0 * FIGURE_SCALE, UNDERSUIT,
    )

    # The head is carried by an actual wrapped neck rather than relying on a
    # pauldron or a raised arm to accidentally touch the cowl.
    collar_anchor = local(0.0, -119.0)
    neck_target = _lerp_point(rig.neck, rig.head, 0.58)
    _draw_solid_segment(
        draw, collar_anchor, neck_target,
        16.0 * FIGURE_SCALE, 13.5 * FIGURE_SCALE, CLOTH_DEEP,
    )

    # Complete limb underpainting.  The visible arm/leg pieces remain more
    # angular, but any overlap or extreme pose still has a continuous body.
    for shoulder, elbow, hand in (
        (rig.left_shoulder, rig.left_elbow, rig.left_hand),
        (rig.right_shoulder, rig.right_elbow, rig.right_hand),
    ):
        _draw_solid_segment(
            draw, shoulder, elbow,
            12.5 * FIGURE_SCALE, 10.5 * FIGURE_SCALE, UNDERSUIT,
        )
        _draw_solid_segment(
            draw, elbow, hand,
            10.5 * FIGURE_SCALE, 8.0 * FIGURE_SCALE, UNDERSUIT,
        )

    for hip, knee, foot in (
        (rig.left_hip, rig.left_knee, rig.left_foot),
        (rig.right_hip, rig.right_knee, rig.right_foot),
    ):
        _draw_solid_segment(
            draw, hip, knee,
            12.0 * FIGURE_SCALE, 10.5 * FIGURE_SCALE, UNDERSUIT,
        )
        _draw_solid_segment(
            draw, knee, foot,
            10.5 * FIGURE_SCALE, 8.5 * FIGURE_SCALE, UNDERSUIT,
        )


def _lerp_point(a: Point, b: Point, t: float) -> Point:
    return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t))


def _draw_kanabo(
    draw: ImageDraw.ImageDraw,
    hand: Point,
    angle: float,
    *,
    alpha: int = 255,
) -> Point:
    def col(color: RGBA) -> RGBA:
        return (color[0], color[1], color[2], min(color[3], alpha))

    def tr(distance: float, offset: float) -> Point:
        x, y = _rot(distance * WEAPON_SCALE, offset * WEAPON_SCALE, angle)
        return (hand[0] + x, hand[1] + y)

    # Pommel and wrapped grip.
    _circle(draw, tr(-13, 0), 5.8 * WEAPON_SCALE, col(BRASS), col(OUTLINE), 1.2)
    handle = [tr(-12, -5.4), tr(52, -5.7), tr(55, 5.7), tr(-12, 5.4)]
    _poly(draw, handle, col(WRAP), col(OUTLINE), 1.5)
    for distance in range(-8, 50, 8):
        _line(draw, [tr(distance, -5.2), tr(distance + 7, 5.2)], col(WRAP_HI), 1.0)
    _poly(draw, [tr(49, -9), tr(61, -10), tr(62, 10), tr(49, 9)], col(BRASS_DARK), col(OUTLINE), 1.3)
    _line(draw, [tr(52, -7), tr(58, -7)], col(BRASS_HI), 1.0)

    # Tapered iron body with a slightly crooked forged silhouette.
    club = [
        tr(58, -12),
        tr(84, -17),
        tr(119, -20),
        tr(148, -16),
        tr(158, -8),
        tr(160, 8),
        tr(149, 17),
        tr(118, 22),
        tr(83, 18),
        tr(58, 12),
    ]
    _poly(draw, club, col(IRON_DEEP), col(OUTLINE), 2.0)
    inner = [
        tr(64, -8),
        tr(88, -12),
        tr(119, -15),
        tr(145, -12),
        tr(153, -6),
        tr(153, 5),
        tr(144, 11),
        tr(117, 16),
        tr(88, 13),
        tr(64, 8),
    ]
    _poly(draw, inner, col(IRON), col(OUTLINE_SOFT), 0.9)
    _line(draw, [tr(70, -7), tr(139, -10)], col(IRON_HI), 1.4)
    _line(draw, [tr(72, 10), tr(132, 13)], col((58, 62, 72, 255)), 1.1)

    # Alternating studs sell the weapon as a kanabo rather than an axe.
    for index, distance in enumerate((76, 96, 117, 138, 151)):
        side = -1 if index % 2 == 0 else 1
        radius = (4.4 if distance < 145 else 5.0) * WEAPON_SCALE
        center = tr(distance, side * 14.0)
        _circle(draw, center, radius, col(BRASS), col(OUTLINE), 1.0)
        tip = tr(distance, side * 22.0)
        flank = 3.0
        _poly(
            draw,
            [tr(distance - flank, side * 15.5), tr(distance + flank, side * 15.5), tip],
            col(BRASS_HI),
            col(OUTLINE),
            0.8,
        )
    cap = tr(157, 0)
    _circle(draw, cap, 10.0 * WEAPON_SCALE, col(IRON), col(OUTLINE), 1.6)
    _circle(draw, cap, 4.0 * WEAPON_SCALE, col(BRASS), col(OUTLINE), 0.8)
    return tr(160, 0)


def _draw_foot(
    draw: ImageDraw.ImageDraw,
    knee: Point,
    foot: Point,
    facing: float,
) -> None:
    """Draw a boot whose cuff visibly grows out of the shin."""
    dx = knee[0] - foot[0]
    dy = knee[1] - foot[1]
    length = max(1.0, math.hypot(dx, dy))
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux

    ankle = (
        foot[0] + ux * 12.0 * FIGURE_SCALE,
        foot[1] + uy * 12.0 * FIGURE_SCALE,
    )
    heel = (
        foot[0] - facing * 10.0 * FIGURE_SCALE,
        foot[1] + 4.5 * FIGURE_SCALE,
    )
    toe = (
        foot[0] + facing * 22.0 * FIGURE_SCALE,
        foot[1] + 3.0 * FIGURE_SCALE,
    )
    boot = [
        (ankle[0] + nx * 8.5 * FIGURE_SCALE, ankle[1] + ny * 8.5 * FIGURE_SCALE),
        (ankle[0] - nx * 8.5 * FIGURE_SCALE, ankle[1] - ny * 8.5 * FIGURE_SCALE),
        heel,
        (toe[0], toe[1] - 7.0 * FIGURE_SCALE),
        (toe[0] + facing * 3.0 * FIGURE_SCALE, toe[1] + 2.5 * FIGURE_SCALE),
        (heel[0] + facing * 2.0 * FIGURE_SCALE, heel[1] + 3.0 * FIGURE_SCALE),
    ]
    _poly(draw, boot, CLOTH_DEEP, OUTLINE, 1.5)

    # A wrap cuff bridges the lower-leg capsule into the boot and gives the
    # ankle a readable joint instead of an empty pixel gap under the hakama.
    cuff_a = (ankle[0] + nx * 9.0 * FIGURE_SCALE, ankle[1] + ny * 9.0 * FIGURE_SCALE)
    cuff_b = (ankle[0] - nx * 9.0 * FIGURE_SCALE, ankle[1] - ny * 9.0 * FIGURE_SCALE)
    _line(draw, [cuff_a, cuff_b], WRAP_HI, 2.0)
    _line(
        draw,
        [
            (heel[0] + facing * 1.0 * FIGURE_SCALE, heel[1] + 1.0 * FIGURE_SCALE),
            (toe[0] + facing * 1.0 * FIGURE_SCALE, toe[1] + 1.0 * FIGURE_SCALE),
        ],
        CLOTH_HI,
        1.0,
    )


def _draw_leg(
    draw: ImageDraw.ImageDraw,
    hip: Point,
    knee: Point,
    foot: Point,
    *,
    front: bool,
) -> None:
    base = CLOTH_MID if front else CLOTH
    _draw_segment(
        draw,
        hip,
        knee,
        10.0 * FIGURE_SCALE,
        9.0 * FIGURE_SCALE,
        base,
        highlight=CLOTH_HI if front else None,
    )
    _draw_segment(
        draw,
        knee,
        foot,
        9.0 * FIGURE_SCALE,
        7.0 * FIGURE_SCALE,
        CLOTH_DEEP,
        highlight=CLOTH_MID if front else None,
    )
    # Wrapped shin bands.
    for fraction in (0.35, 0.55, 0.75):
        x = _lerp(knee[0], foot[0], fraction)
        y = _lerp(knee[1], foot[1], fraction)
        dx = foot[0] - knee[0]
        dy = foot[1] - knee[1]
        length = max(1.0, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length
        _line(
            draw,
            [
                (x - nx * 7.5 * FIGURE_SCALE, y - ny * 7.5 * FIGURE_SCALE),
                (x + nx * 7.5 * FIGURE_SCALE, y + ny * 7.5 * FIGURE_SCALE),
            ],
            WRAP_HI if front else WRAP,
            1.4,
        )
    _draw_foot(draw, knee, foot, 1.0 if foot[0] >= hip[0] else -1.0)


def _draw_hakama(draw: ImageDraw.ImageDraw, local, pose: Pose) -> None:
    sway = pose.cloth_sway
    back = [
        local(-34, -61),
        local(34, -61),
        local(49 + sway * 0.25, -5),
        local(8 + sway * 0.1, 6),
        local(0, -2),
        local(-9 + sway * 0.1, 6),
        local(-49 + sway * 0.25, -5),
    ]
    _poly(draw, back, CLOTH_DEEP, OUTLINE, 1.8)

    left_panel = [
        local(-35, -57),
        local(-3, -58),
        local(-7 + sway * 0.12, 4),
        local(-48 + sway * 0.28, -3),
    ]
    right_panel = [
        local(3, -58),
        local(35, -57),
        local(48 + sway * 0.28, -3),
        local(7 + sway * 0.12, 4),
    ]
    _poly(draw, left_panel, ARMOR_DEEP, OUTLINE, 1.5)
    _poly(draw, right_panel, ARMOR, OUTLINE, 1.5)
    _line(draw, [local(-24, -51), local(-30 + sway * 0.16, -4)], ARMOR_HI, 1.2)
    _line(draw, [local(22, -51), local(29 + sway * 0.16, -5)], ARMOR_HI, 1.2)

    # Red inner split appears in motion without turning the whole sprite red.
    center = [local(-6, -58), local(7, -58), local(5, 1), local(-5, 1)]
    _poly(draw, center, LACQUER, OUTLINE, 1.1)
    _line(draw, [local(0, -53), local(0, -4)], LACQUER_HI, 0.9)


def _draw_torso(draw: ImageDraw.ImageDraw, local, pose: Pose) -> None:
    # Under-robe mass.
    under = [
        local(-36, -116),
        local(35, -116),
        local(41, -72),
        local(29, -55),
        local(-30, -55),
        local(-42, -74),
    ]
    _poly(draw, under, CLOTH, OUTLINE, 2.0)

    # Asymmetric plated shoulders: weapon side is larger and higher.
    left_pauldron = [
        local(-51, -113),
        local(-39, -127),
        local(-18, -122),
        local(-20, -98),
        local(-44, -91),
        local(-56, -100),
    ]
    right_pauldron = [
        local(17, -125),
        local(43, -133),
        local(58, -118),
        local(58, -96),
        local(44, -88),
        local(20, -96),
    ]
    _poly(draw, left_pauldron, ARMOR_DEEP, OUTLINE, 1.7)
    _poly(draw, right_pauldron, ARMOR, OUTLINE, 2.0)
    _poly(
        draw,
        [local(24, -121), local(43, -126), local(51, -116), local(48, -107), local(27, -111)],
        ARMOR_HI,
        OUTLINE_SOFT,
        0.9,
    )
    for y in (-113, -104, -95):
        _line(draw, [local(-48, y), local(-23, y + 4)], ARMOR_HI, 0.9)

    # Five overlapping lamellar plates create a broad, readable chest.
    plate_specs = [
        (-101, 48, 20, ARMOR),
        (-92, 51, 20, ARMOR_DEEP),
        (-83, 52, 20, ARMOR),
        (-74, 48, 18, ARMOR_DEEP),
    ]
    for y, width, height, color in plate_specs:
        left = -width * 0.5
        right = width * 0.5
        plate = [
            local(left, y - height * 0.5),
            local(right, y - height * 0.5),
            local(right - 4, y + height * 0.5),
            local(0, y + height * 0.5 + 5),
            local(left + 4, y + height * 0.5),
        ]
        _poly(draw, plate, color, OUTLINE, 1.25)
        _line(draw, [local(left + 8, y - 5), local(right - 8, y - 5)], ARMOR_HI, 0.9)
        _circle(draw, local(left + 9, y + 2), 1.6 * FIGURE_SCALE, BRASS, OUTLINE, 0.6)
        _circle(draw, local(right - 9, y + 2), 1.6 * FIGURE_SCALE, BRASS, OUTLINE, 0.6)

    # Diagonal red harness and heavy rope belt.
    harness = [local(-28, -116), local(-17, -119), local(30, -63), local(20, -59)]
    _poly(draw, harness, LACQUER, OUTLINE, 1.1)
    _line(draw, [local(-23, -115), local(25, -63)], LACQUER_HI, 1.0)

    belt = [local(-39, -66), local(39, -66), local(36, -54), local(-37, -54)]
    _poly(draw, belt, ROPE, OUTLINE, 1.4)
    for x in range(-30, 34, 10):
        _line(draw, [local(x, -67), local(x + 5, -54)], ROPE_HI, 1.0)
    knot = local(-2, -58)
    _circle(draw, knot, 5.5 * FIGURE_SCALE, ROPE_HI, OUTLINE, 1.0)
    _poly(draw, [local(-2, -54), local(-12, -35), local(-2, -39)], ROPE, OUTLINE, 0.9)
    _poly(draw, [local(2, -54), local(13, -36), local(3, -39)], ROPE, OUTLINE, 0.9)


def _draw_arm(
    draw: ImageDraw.ImageDraw,
    shoulder: Point,
    elbow: Point,
    hand: Point,
    *,
    front: bool,
    raised_talisman: bool = False,
) -> None:
    base = CLOTH_MID if front else CLOTH
    _draw_segment(
        draw,
        shoulder,
        elbow,
        11.0 * FIGURE_SCALE,
        9.5 * FIGURE_SCALE,
        base,
        highlight=CLOTH_HI if front else None,
    )
    _draw_segment(
        draw,
        elbow,
        hand,
        9.5 * FIGURE_SCALE,
        7.5 * FIGURE_SCALE,
        CLOTH_DEEP,
        highlight=CLOTH_MID if front else None,
    )
    _circle(draw, elbow, 9.0 * FIGURE_SCALE, ARMOR if front else ARMOR_DEEP, OUTLINE, 1.2)
    # Bracer with red binding.
    dx = hand[0] - elbow[0]
    dy = hand[1] - elbow[1]
    angle = math.degrees(math.atan2(dy, dx))
    bracer_center = (_lerp(elbow[0], hand[0], 0.72), _lerp(elbow[1], hand[1], 0.72))
    _poly(draw, _quad(bracer_center, 20 * FIGURE_SCALE, 15 * FIGURE_SCALE, angle), ARMOR_DEEP, OUTLINE, 1.2)
    _line(draw, [_polar(bracer_center, -8 * FIGURE_SCALE, angle), _polar(bracer_center, 8 * FIGURE_SCALE, angle)], LACQUER_HI, 1.4)
    _circle(draw, hand, 7.8 * FIGURE_SCALE, WRAP, OUTLINE, 1.2)

    if raised_talisman:
        # A small paper seal makes the taunt read as occult ninja ritual rather
        # than a generic fist pump.
        paper_center = (hand[0] - 2 * FIGURE_SCALE, hand[1] - 18 * FIGURE_SCALE)
        paper = _quad(paper_center, 14 * FIGURE_SCALE, 28 * FIGURE_SCALE, -7.0)
        _poly(draw, paper, (224, 205, 164, 255), OUTLINE, 1.0)
        _line(draw, [(paper_center[0] - 4, paper_center[1] - 7), (paper_center[0] + 3, paper_center[1] + 7)], LACQUER, 1.0)
        _line(draw, [(paper_center[0] + 4, paper_center[1] - 8), (paper_center[0] - 3, paper_center[1] + 6)], LACQUER, 1.0)


def _draw_neck_and_gorget(
    draw: ImageDraw.ImageDraw,
    rig: Rig,
    local,
    pose: Pose,
) -> None:
    """Resolve the head-to-torso transition as layered cloth and armor."""
    collar_anchor = local(0.0, -118.0)
    neck_target = _lerp_point(rig.neck, rig.head, 0.62)
    _poly(
        draw,
        _segment_polygon(
            collar_anchor, neck_target,
            15.5 * FIGURE_SCALE, 12.5 * FIGURE_SCALE,
        ),
        CLOTH_DEEP,
        OUTLINE,
        1.4,
    )

    # Broad gorget sits over the upper chest and tucks under the cowl.
    gorget = [
        local(-28, -123),
        local(-16, -134),
        local(16, -134),
        local(29, -122),
        local(22, -107),
        local(-22, -107),
    ]
    _poly(draw, gorget, ARMOR_DEEP, OUTLINE, 1.6)
    _poly(
        draw,
        [local(-18, -124), local(18, -124), local(14, -113), local(-14, -113)],
        ARMOR,
        OUTLINE_SOFT,
        0.9,
    )
    _line(draw, [local(-13, -119), local(13, -119)], ARMOR_HI, 1.0)

    # Two wrap bands make the neck read as intentional anatomy rather than a
    # dark bridge.  Their angle follows the torso while the head can counterpose.
    for t in (0.35, 0.58):
        center = _lerp_point(collar_anchor, neck_target, t)
        dx = neck_target[0] - collar_anchor[0]
        dy = neck_target[1] - collar_anchor[1]
        length = max(1.0, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length
        half = _lerp(13.0, 10.0, t) * FIGURE_SCALE
        _line(
            draw,
            [(center[0] - nx * half, center[1] - ny * half),
             (center[0] + nx * half, center[1] + ny * half)],
            CLOTH_MID,
            1.0,
        )


def _draw_gripping_hand(
    draw: ImageDraw.ImageDraw,
    elbow: Point,
    hand: Point,
    weapon_angle: float,
) -> None:
    """Repaint the weapon hand over the handle as a closed, attached grip."""
    wrist = _lerp_point(elbow, hand, 0.80)
    _draw_solid_segment(
        draw, wrist, hand,
        6.5 * FIGURE_SCALE, 8.5 * FIGURE_SCALE, WRAP,
    )
    _circle(draw, hand, 8.6 * FIGURE_SCALE, WRAP, OUTLINE, 1.2)

    # Four knuckle pads cross the handle; the dark handle seam remains visible
    # between them, so the hand reads as wrapped around rather than pasted on.
    across = weapon_angle + 90.0
    for offset in (-4.5, -1.5, 1.5, 4.5):
        p = _polar(hand, offset * FIGURE_SCALE, across)
        _circle(draw, p, 2.1 * FIGURE_SCALE, WRAP_HI, OUTLINE_SOFT, 0.55)
    _line(
        draw,
        [_polar(hand, -7.0 * FIGURE_SCALE, weapon_angle),
         _polar(hand, 7.0 * FIGURE_SCALE, weapon_angle)],
        OUTLINE_SOFT,
        1.0,
    )


def _draw_head(draw: ImageDraw.ImageDraw, rig: Rig, pose: Pose) -> None:
    center = rig.head
    angle = pose.torso + pose.head

    def hp(x: float, y: float) -> Point:
        rx, ry = _rot(x * FIGURE_SCALE, y * FIGURE_SCALE, angle)
        return (center[0] + rx, center[1] + ry)

    # Cowl silhouette, with a clipped top and swept side flaps.
    cowl = [
        hp(-26, -25),
        hp(-15, -36),
        hp(13, -36),
        hp(27, -25),
        hp(31, -2),
        hp(22, 22),
        hp(8, 30),
        hp(-10, 29),
        hp(-24, 20),
        hp(-31, -2),
    ]
    _poly(draw, cowl, CLOTH_DEEP, OUTLINE, 2.0)
    inner = [
        hp(-19, -22),
        hp(-10, -29),
        hp(10, -29),
        hp(20, -20),
        hp(22, 2),
        hp(14, 18),
        hp(-14, 18),
        hp(-22, 2),
    ]
    _poly(draw, inner, CLOTH_MID, OUTLINE, 1.1)

    # Iron oni mask: angular cheek guards, central nose ridge, brass tusks.
    mask = [
        hp(-20, -12),
        hp(-12, -21),
        hp(13, -21),
        hp(21, -11),
        hp(19, 11),
        hp(10, 23),
        hp(0, 27),
        hp(-11, 22),
        hp(-20, 10),
    ]
    _poly(draw, mask, IRON_DEEP, OUTLINE, 1.7)
    faceplate = [
        hp(-15, -9),
        hp(-8, -16),
        hp(9, -16),
        hp(16, -8),
        hp(14, 10),
        hp(5, 18),
        hp(-6, 18),
        hp(-14, 9),
    ]
    _poly(draw, faceplate, IRON, OUTLINE_SOFT, 1.0)
    _poly(draw, [hp(-3, -14), hp(4, -14), hp(7, 11), hp(0, 16), hp(-6, 10)], IRON_HI, OUTLINE_SOFT, 0.8)

    # Horn-like cowl crests frame the head without turning it into a literal oni.
    _poly(draw, [hp(-20, -29), hp(-34, -39), hp(-28, -18)], ARMOR, OUTLINE, 1.0)
    _poly(draw, [hp(18, -29), hp(34, -38), hp(27, -17)], ARMOR, OUTLINE, 1.0)
    _line(draw, [hp(-31, -35), hp(-25, -22)], ARMOR_HI, 0.8)
    _line(draw, [hp(30, -34), hp(24, -21)], ARMOR_HI, 0.8)

    if pose.x_eyes:
        for x in (-8, 8):
            _line(draw, [hp(x - 4, -6), hp(x + 4, 2)], OUTLINE, 1.5)
            _line(draw, [hp(x - 4, 2), hp(x + 4, -6)], OUTLINE, 1.5)
    else:
        flare = pose.eye_flare
        left_eye = [hp(-14, -8), hp(-3, -11), hp(-1, -5), hp(-12, -3)]
        right_eye = [hp(2, -11), hp(14, -8), hp(12, -3), hp(1, -5)]
        _poly(draw, left_eye, EYE, OUTLINE, 0.7)
        _poly(draw, right_eye, EYE, OUTLINE, 0.7)
        _line(draw, [hp(-11, -6), hp(-4, -8)], EYE_CORE, 0.9 + flare * 0.8)
        _line(draw, [hp(4, -8), hp(11, -6)], EYE_CORE, 0.9 + flare * 0.8)
        if flare > 0.7:
            _line(draw, [hp(-17, -8), hp(-24 - flare * 3, -10)], (255, 70, 58, 120), 1.0)
            _line(draw, [hp(17, -8), hp(24 + flare * 3, -10)], (255, 70, 58, 120), 1.0)

    # Fanged lower vent and tusks.
    _line(draw, [hp(-9, 8), hp(0, 12), hp(9, 8)], OUTLINE_SOFT, 1.2)
    _poly(draw, [hp(-12, 10), hp(-5, 12), hp(-10, 20)], BRASS_HI, OUTLINE, 0.8)
    _poly(draw, [hp(12, 10), hp(5, 12), hp(10, 20)], BRASS_HI, OUTLINE, 0.8)
    for x in (-5, 0, 5):
        _line(draw, [hp(x, 12), hp(x, 17)], OUTLINE, 0.7)

    # Tied scarf tails.
    tail_anchor = hp(20, -20)
    tail1 = [tail_anchor, hp(44 + pose.cloth_sway * 0.4, -26), hp(35 + pose.cloth_sway * 0.6, -14)]
    tail2 = [hp(21, -17), hp(46 + pose.cloth_sway * 0.5, -8), hp(33 + pose.cloth_sway * 0.7, -4)]
    _poly(draw, tail1, LACQUER, OUTLINE, 0.9)
    _poly(draw, tail2, LACQUER_HI, OUTLINE, 0.9)


def _draw_attack_effects(draw: ImageDraw.ImageDraw, rig: Rig, pose: Pose, weapon_tip: Point) -> None:
    if pose.anim != "slash" or pose.strike <= 0.08:
        return
    cx = rig.chest[0] + 18 * FIGURE_SCALE
    cy = rig.chest[1] + 22 * FIGURE_SCALE
    radius = 105 * FIGURE_SCALE
    bbox = (_s(cx - radius), _s(cy - radius), _s(cx + radius), _s(cy + radius))
    alpha = int(90 + pose.strike * 80)
    draw.arc(bbox, 203, 330, fill=(231, 209, 173, alpha), width=_s(7.0 * FIGURE_SCALE))
    draw.arc(bbox, 211, 323, fill=(255, 250, 232, 155), width=_s(2.3 * FIGURE_SCALE))
    # A short red echo nearest the club gives the swing some character identity.
    draw.arc(bbox, 236, 318, fill=(225, 48, 48, 105), width=_s(2.1 * FIGURE_SCALE))
    _circle(draw, weapon_tip, 5.0 * FIGURE_SCALE * pose.strike, WHITE_FLASH, None, 0)

    for index, (dx, dy) in enumerate(((-53, 9), (-37, 14), (35, 10), (55, 13))):
        jitter = math.sin(pose.frame_idx * 1.7 + index) * 2.0
        c = (rig.root[0] + (dx + jitter) * FIGURE_SCALE, rig.root[1] + dy * FIGURE_SCALE)
        _poly(
            draw,
            [
                (c[0] - 3 * FIGURE_SCALE, c[1]),
                (c[0] + 4 * FIGURE_SCALE, c[1] - 2 * FIGURE_SCALE),
                (c[0] + 1 * FIGURE_SCALE, c[1] + 4 * FIGURE_SCALE),
            ],
            DUST,
            (80, 65, 46, 110),
            0.6,
        )


def _draw_hurt_marks(draw: ImageDraw.ImageDraw, rig: Rig, pose: Pose) -> None:
    if pose.recoil <= 0.08:
        return
    alpha = int(90 + pose.recoil * 150)
    for offset in (-1, 1):
        x = rig.chest[0] + offset * 18 * FIGURE_SCALE
        y = rig.chest[1] - 4 * FIGURE_SCALE
        _line(
            draw,
            [(x - 9 * FIGURE_SCALE, y - 8 * FIGURE_SCALE), (x + 8 * FIGURE_SCALE, y + 8 * FIGURE_SCALE)],
            (255, 102, 79, alpha),
            2.0,
        )


def _render_frame(
    anim: str,
    frame_idx: int,
    nframes: int,
    *,
    include_effects: bool = True,
) -> Image.Image:
    image = Image.new(
        "RGBA",
        (WORK_FRAME_SIZE[0] * SUPER, WORK_FRAME_SIZE[1] * SUPER),
        TRANSPARENT,
    )
    draw = ImageDraw.Draw(image, "RGBA")
    pose = Pose(anim, frame_idx, nframes)
    rig, local = _build_rig(pose)

    _draw_ground_shadow(draw, rig, pose)
    _draw_smoke_ribbon(draw, rig, pose)

    # Weapon behind the body in neutral poses.  During the strike it crosses in
    # front after the release point; the death drop also remains behind.
    weapon_tip = rig.right_hand
    if not pose.weapon_front:
        weapon_tip = _draw_kanabo(draw, rig.right_hand, pose.weapon_angle + pose.torso)

    _draw_anatomical_understructure(draw, rig, local)

    # Rear leg and arm establish depth before the central costume mass.
    _draw_leg(draw, rig.left_hip, rig.left_knee, rig.left_foot, front=False)
    _draw_arm(
        draw,
        rig.right_shoulder,
        rig.right_elbow,
        rig.right_hand,
        front=False,
    )

    _draw_hakama(draw, local, pose)
    _draw_torso(draw, local, pose)

    _draw_leg(draw, rig.right_hip, rig.right_knee, rig.right_foot, front=True)
    _draw_arm(
        draw,
        rig.left_shoulder,
        rig.left_elbow,
        rig.left_hand,
        front=True,
        raised_talisman=anim == "taunt",
    )
    _draw_neck_and_gorget(draw, rig, local, pose)
    _draw_head(draw, rig, pose)

    weapon_angle = pose.weapon_angle + pose.torso
    if pose.weapon_front:
        weapon_tip = _draw_kanabo(draw, rig.right_hand, weapon_angle)
    _draw_gripping_hand(draw, rig.right_elbow, rig.right_hand, weapon_angle)

    if include_effects:
        _draw_attack_effects(draw, rig, pose, weapon_tip)
        _draw_hurt_marks(draw, rig, pose)

    return _downsample(image)


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_size = opts.get("frame_size", FRAME_SIZE)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda anim, frame_idx, nframes: _render_frame(anim, frame_idx, nframes),
        out_dir=out_dir,
        frame_size=frame_size,
        crop_margin=10,
        auto_crop=True,
    )
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the Iron Lotus heavy-ninja spritesheet."
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
