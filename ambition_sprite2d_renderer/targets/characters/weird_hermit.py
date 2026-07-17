"""Polished renderer for the original Weird Hermit design.

This keeps the character's original read intact: a compact, hunched,
side-profile hermit with a floppy head rag, absurdly long nose, moustache,
wrinkled bare torso, shorts, knobby legs, and unsettlingly long fingers.  The
polish pass improves silhouette separation, anatomy, color planes, facial
readability, and attack staging without replacing him with a hooded wizard or
adding a prop.  There is no baked drop shadow.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

ACTOR_METADATA = {
    "actor": {"character_id": "npc_weird_hermit", "display_name": "Weird Hermit"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "hermit", "sideways_seer"],
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
    "tags": ["story", "humanoid", "hermit", "sideways_seer"],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 113.0, "y": 51.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 101.0, "y": 105.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 108.0, "y": 142.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 143.0, "y": 139.0}},
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 113.0, "y": 13.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "creep", "events": []},
        "action.melee.primary": {"animation": "finger_jab", "events": []},
        "action.melee.secondary": {"animation": "grab", "events": []},
        "action.cast": {"animation": "curse_sneeze", "events": []},
        "interaction.talk": {"animation": "idle", "events": []},
        "interaction.use": {"animation": "grab", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "damage.death": {"animation": "death", "events": []},
    },
}


RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_BASENAME = "weird_hermit"
# Files the tack-on installer copies into the sandbox sprites dir.
# Aligned with the rest of the project's `<target>_spritesheet.{ext}`
# convention as of 2026-05-24 — the previous bare-name output was a
# divergence from the runtime's manifest scanner expectations.
SHEET_FILES = [
    f"{TARGET_BASENAME}_spritesheet.png",
    f"{TARGET_BASENAME}_spritesheet.yaml",
    f"{TARGET_BASENAME}_spritesheet.ron",
]
FRAME_SIZE = (240, 224)
# The original used a large work canvas and therefore rendered unusually small.
# This tighter canvas preserves the same proportions while making him readable.
WORK_FRAME_SIZE = (360, 336)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("creep", 8, 95),
    ("finger_jab", 7, 75),
    ("grab", 7, 85),
    ("curse_sneeze", 7, 90),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

OUTLINE = (22, 19, 18, 255)
OUTLINE_SOFT = (71, 54, 45, 255)
SKIN = (195, 151, 111, 255)
SKIN_SHADOW = (135, 91, 67, 255)
SKIN_LIGHT = (226, 187, 139, 255)
SKIN_DEEP = (96, 60, 48, 255)
NOSE = (181, 121, 86, 255)
NOSE_LIGHT = (214, 156, 111, 255)
MOUSTACHE = (62, 48, 39, 255)
MOUSTACHE_HI = (105, 84, 64, 255)
CLOTH = (215, 207, 183, 255)
CLOTH_LIGHT = (237, 231, 208, 255)
CLOTH_SHADOW = (139, 130, 111, 255)
SHORTS = (73, 62, 69, 255)
SHORTS_HI = (117, 99, 107, 255)
WRAP = (133, 91, 68, 255)
EYE_WHITE = (245, 236, 208, 255)
EYE = (34, 30, 28, 255)
CURSE = (116, 220, 176, 145)
CURSE_CORE = (188, 245, 203, 175)


@dataclass
class Pose:
    root_x: float = 0.0
    root_y: float = 0.0
    bob: float = 0.0
    lean: float = 0.0
    torso_tilt: float = 0.0
    head_tilt: float = 0.0
    cap_swing: float = 0.0
    jaw: float = 0.0
    near_arm: float = 0.0
    far_arm: float = 0.0
    near_reach: float = 0.0
    far_reach: float = 0.0
    near_leg: float = 0.0
    far_leg: float = 0.0
    near_foot_lift: float = 0.0
    far_foot_lift: float = 0.0
    crouch: float = 0.0
    jab: float = 0.0
    grab: float = 0.0
    sneeze: float = 0.0
    hurt: float = 0.0
    x_eyes: bool = False
    blink: bool = False

    def __init__(self, anim: str, frame_idx: int, nframes: int) -> None:
        t = frame_idx / max(1, nframes - 1)
        cyc = math.tau * frame_idx / max(1, nframes)
        s = math.sin(cyc)
        c = math.cos(cyc)
        self.root_x = self.root_y = self.bob = self.lean = 0.0
        self.torso_tilt = self.head_tilt = self.cap_swing = self.jaw = 0.0
        self.near_arm = self.far_arm = self.near_reach = self.far_reach = 0.0
        self.near_leg = self.far_leg = self.near_foot_lift = self.far_foot_lift = 0.0
        self.crouch = self.jab = self.grab = self.sneeze = self.hurt = 0.0
        self.x_eyes = self.blink = False
        if anim == "idle":
            self.bob = s * 1.3
            self.lean = -2.0 + s * 1.3
            self.torso_tilt = -6.0 + s * 1.0
            self.head_tilt = -6.0 - s * 1.4
            self.cap_swing = s * 7.0
            self.near_arm = -8.0 + s * 4.0
            self.far_arm = -18.0 - s * 3.0
            self.near_leg = c * 1.2
            self.far_leg = -c * 1.2
            self.crouch = 4.0 + abs(s) * 1.0
            self.jaw = max(0.0, s) * 0.04
            self.blink = frame_idx == nframes - 2
        elif anim == "creep":
            self.root_x = s * 2.2
            self.bob = abs(s) * 2.8 - 0.8
            self.lean = -5.0 + s * 2.0
            self.torso_tilt = -8.0 + s * 2.0
            self.head_tilt = -8.0 - s * 2.0
            self.cap_swing = -s * 10.0
            self.near_arm = -16.0 * s - 6.0
            self.far_arm = 14.0 * s - 20.0
            self.near_reach = max(0.0, -s) * 8.0
            self.far_reach = max(0.0, s) * 7.0
            self.near_leg = 18.0 * s
            self.far_leg = -18.0 * s
            self.near_foot_lift = max(0.0, s) * 8.0
            self.far_foot_lift = max(0.0, -s) * 7.0
            self.crouch = 6.0
        elif anim == "finger_jab":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-7.0, 11.0, tt)
            self.bob = -hit * 3.0
            self.lean = _lerp(-12.0, 10.0, tt)
            self.torso_tilt = _lerp(-10.0, 5.0, tt)
            self.head_tilt = _lerp(-12.0, 8.0, tt)
            self.cap_swing = _lerp(10.0, -8.0, tt)
            self.near_arm = _lerp(-60.0, 18.0, tt)
            self.near_reach = _lerp(0.0, 42.0, tt)
            self.far_arm = _lerp(-20.0, 0.0, tt)
            self.near_leg = -8.0 - hit * 3.0
            self.far_leg = 12.0 + hit * 2.0
            self.crouch = _lerp(10.0, 3.0, tt)
            self.jab = hit
            self.jaw = 0.10 * hit
        elif anim == "grab":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-5.0, 8.0, tt)
            self.bob = -hit * 2.0
            self.lean = _lerp(-4.0, 16.0, tt)
            self.torso_tilt = _lerp(-8.0, 8.0, tt)
            self.head_tilt = _lerp(-8.0, 6.0, tt)
            self.near_arm = _lerp(-72.0, 28.0, tt)
            self.far_arm = _lerp(-56.0, 20.0, tt)
            self.near_reach = _lerp(10.0, 36.0, tt)
            self.far_reach = _lerp(0.0, 28.0, tt)
            self.near_leg = -10.0
            self.far_leg = 12.0
            self.crouch = 8.0 - hit * 2.0
            self.grab = hit
            self.jaw = 0.15 * hit
        elif anim == "curse_sneeze":
            tt = _ease(t)
            puff = math.sin(tt * math.pi)
            self.root_x = math.sin(t * math.pi * 5.0) * (1.0 - t) * 3.0
            self.bob = -puff * 2.5
            self.lean = _lerp(8.0, -20.0, tt)
            self.torso_tilt = _lerp(2.0, -18.0, tt)
            self.head_tilt = _lerp(12.0, -18.0, tt)
            self.cap_swing = _lerp(-14.0, 18.0, tt)
            self.near_arm = 26.0 * puff - 8.0
            self.far_arm = 18.0 * puff - 18.0
            self.near_leg = 8.0 * puff
            self.far_leg = -8.0 * puff
            self.crouch = 9.0 + puff * 2.0
            self.jaw = 0.35 * puff
            self.sneeze = puff
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 4.0) * (1.0 - t)
            self.root_x = shake * 4.0
            self.bob = -hit * 2.0
            self.lean = -18.0 * hit
            self.torso_tilt = -14.0 * hit
            self.head_tilt = 18.0 * hit
            self.near_arm = 32.0 * hit
            self.far_arm = 26.0 * hit
            self.near_leg = 10.0 * hit
            self.far_leg = -8.0 * hit
            self.jaw = 0.24 * hit
            self.hurt = hit
        elif anim == "death":
            tt = _ease(t)
            self.root_x = tt * 16.0
            self.root_y = tt * 7.0
            self.bob = -tt * 4.0
            self.lean = -82.0 * tt
            self.torso_tilt = -38.0 * tt
            self.head_tilt = 30.0 * tt
            self.cap_swing = 20.0 * tt
            self.near_arm = _lerp(-8.0, 58.0, tt)
            self.far_arm = _lerp(-18.0, -55.0, tt)
            self.near_leg = _lerp(0.0, 28.0, tt)
            self.far_leg = _lerp(0.0, -26.0, tt)
            self.near_foot_lift = tt * 8.0
            self.far_foot_lift = tt * 5.0
            self.crouch = tt * 5.0
            self.jaw = 0.25 * tt
            self.x_eyes = tt > 0.55


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


def _rot_local(x: float, y: float, deg: float) -> Point:
    rad = math.radians(deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return (x * c - y * s, x * s + y * c)


def _poly(draw: ImageDraw.ImageDraw, pts: Sequence[Point], fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.0) -> None:
    ipts = [_pt(p) for p in pts]
    draw.polygon(ipts, fill=fill)
    if outline and width > 0:
        draw.line(ipts + [ipts[0]], fill=outline, width=max(1, _s(width)), joint="curve")


def _line(draw: ImageDraw.ImageDraw, pts: Sequence[Point], fill: RGBA, width: float = 1.0) -> None:
    draw.line([_pt(p) for p in pts], fill=fill, width=max(1, _s(width)), joint="curve")


def _ellipse(draw: ImageDraw.ImageDraw, cx: float, cy: float, rx: float, ry: float, fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.0) -> None:
    draw.ellipse(_box(cx, cy, rx, ry), fill=fill, outline=outline, width=max(1, _s(width)))


def _circle(draw: ImageDraw.ImageDraw, c: Point, r: float, fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.0) -> None:
    _ellipse(draw, c[0], c[1], r, r, fill, outline, width)


def _downsample(img: Image.Image) -> Image.Image:
    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


class WeirdHermitRenderer:
    """Draw the original Weird Hermit silhouette with cleaner construction."""

    USES_PROPS = False
    USES_DROP_SHADOW = False

    def render_frame(self, anim: str, frame_idx: int, nframes: int) -> Image.Image:
        img = Image.new(
            "RGBA",
            (WORK_FRAME_SIZE[0] * SUPER, WORK_FRAME_SIZE[1] * SUPER),
            (0, 0, 0, 0),
        )
        draw = ImageDraw.Draw(img, "RGBA")
        pose = Pose(anim, frame_idx, nframes)
        # Keep the original compact scale and profile, but use more of the frame.
        base_x = 0.42 if anim != "death" else 0.47
        root = (
            WORK_FRAME_SIZE[0] * base_x + pose.root_x,
            WORK_FRAME_SIZE[1] * 0.82 + pose.root_y + pose.bob,
        )
        global_tilt = pose.lean * (0.90 if anim != "death" else 0.78)

        def P(x: float, y: float) -> Point:
            rx, ry = _rot_local(x, y, global_tilt)
            return (root[0] + rx, root[1] + ry)

        # No floor ellipse or baked contact shadow.
        self._draw_far_leg(draw, P, pose)
        self._draw_far_arm(draw, P, pose)
        self._draw_torso(draw, P, pose)
        self._draw_near_leg(draw, P, pose)
        self._draw_near_arm(draw, P, pose)
        # The expressive profile is always the top body layer.
        self._draw_head(draw, P, pose)
        if pose.jab > 0.2:
            self._draw_jab_fx(draw, P, pose)
        if pose.grab > 0.2:
            self._draw_grab_fx(draw, P, pose)
        if pose.sneeze > 0.15:
            self._draw_sneeze_fx(draw, P, pose)
        return _downsample(img)

    def _draw_torso(self, draw, P, pose):
        # Same bare, hunched, pot-bellied body as the original, but with a
        # cleaner back curve and readable shoulder / belly planes.
        torso = [
            P(-32, -120 - pose.crouch),
            P(-19, -139 - pose.crouch),
            P(5, -151 - pose.crouch),
            P(31, -137 - pose.crouch),
            P(43, -116 - pose.crouch),
            P(49, -83),
            P(40, -49),
            P(16, -34),
            P(-10, -35),
            P(-31, -51),
            P(-43, -86),
        ]
        _poly(draw, torso, SKIN, OUTLINE, 1.8)

        # Lit belly plane and darker folded back preserve his odd, naked-hermit
        # read without making the body look flat or balloon-like.
        belly = [
            P(-4, -100),
            P(24, -98),
            P(42, -82),
            P(43, -62),
            P(29, -47),
            P(3, -49),
            P(-14, -68),
            P(-14, -87),
        ]
        _poly(draw, belly, SKIN_LIGHT, outline=None, width=0)
        back_plane = [
            P(-31, -116 - pose.crouch),
            P(-18, -137 - pose.crouch),
            P(-5, -142 - pose.crouch),
            P(-12, -70),
            P(-29, -53),
            P(-40, -85),
        ]
        _poly(draw, back_plane, SKIN_SHADOW, outline=None, width=0)

        # Sparse age marks, ribs, and navel: intrinsic anatomy, not costume.
        _line(draw, [P(-1, -118), P(11, -121), P(19, -113)], SKIN_DEEP, 1.0)
        _line(draw, [P(-3, -108), P(10, -105)], SKIN_SHADOW, 0.75)
        _line(draw, [P(1, -91), P(12, -87)], SKIN_SHADOW, 0.75)
        _ellipse(draw, *P(21, -76), 2.4, 3.1, SKIN_DEEP, OUTLINE_SOFT, 0.35)
        _poly(draw, [P(-2, -110), P(5, -117), P(12, -108), P(6, -100)], SKIN_SHADOW, OUTLINE_SOFT, 0.45)
        _ellipse(draw, *P(22, -99), 2.8, 3.5, SKIN_SHADOW, OUTLINE_SOFT, 0.35)

        # Retain the original angular shorts / loincloth silhouette, but give it
        # a waistband, side patch, and leg separation.
        shorts = [
            P(-25, -47),
            P(41, -46),
            P(52, -26),
            P(42, -15),
            P(19, -7),
            P(-18, -14),
            P(-34, -31),
        ]
        _poly(draw, shorts, SHORTS, OUTLINE, 1.4)
        waistband = [P(-23, -46), P(39, -45), P(43, -38), P(-26, -38)]
        _poly(draw, waistband, SHORTS_HI, OUTLINE_SOFT, 0.5)
        _line(draw, [P(12, -38), P(17, -10)], OUTLINE_SOFT, 0.85)
        patch = [P(-18, -33), P(-2, -34), P(0, -23), P(-15, -21)]
        _poly(draw, patch, WRAP, OUTLINE_SOFT, 0.55)
        _line(draw, [P(-14, -31), P(-4, -24)], CLOTH_LIGHT, 0.45)
        _line(draw, [P(-5, -32), P(-13, -24)], CLOTH_LIGHT, 0.45)

    def _draw_head(self, draw, P, pose):
        hx, hy = P(11, -158 - pose.crouch * 0.35 + pose.head_tilt * 0.14)

        # Preserve the original floppy cloth cap / head rag.  The pointed flap
        # is the secondary silhouette after the nose.
        cap = [
            (hx - 18, hy - 31),
            (hx - 6, hy - 45),
            (hx + 17, hy - 47),
            (hx + 38, hy - 36),
            (hx + 48 + pose.cap_swing * 0.22, hy - 21),
            (hx + 38 + pose.cap_swing * 0.34, hy - 7),
            (hx + 17, hy - 19),
        ]
        _poly(draw, cap, CLOTH, OUTLINE, 1.15)
        cap_light = [
            (hx - 10, hy - 39),
            (hx + 12, hy - 42),
            (hx + 31, hy - 34),
            (hx + 20, hy - 29),
            (hx - 4, hy - 30),
        ]
        _poly(draw, cap_light, CLOTH_LIGHT, outline=None, width=0)
        flap = [
            (hx + 31, hy - 34),
            (hx + 73 + pose.cap_swing * 0.34, hy - 38),
            (hx + 67 + pose.cap_swing * 0.48, hy - 10),
            (hx + 36, hy - 7),
        ]
        _poly(draw, flap, CLOTH_SHADOW, OUTLINE, 1.05)
        _line(draw, [(hx + 34, hy - 31), (hx + 63 + pose.cap_swing * 0.30, hy - 31)], CLOTH_LIGHT, 0.75)

        head = [
            (hx - 24, hy - 27),
            (hx - 8, hy - 37),
            (hx + 14, hy - 35),
            (hx + 34, hy - 20),
            (hx + 39, hy + 5),
            (hx + 28, hy + 26),
            (hx + 9, hy + 34),
            (hx - 13, hy + 26),
            (hx - 29, hy + 4),
        ]
        _poly(draw, head, SKIN, OUTLINE, 1.45)
        _poly(
            draw,
            [(hx - 18, hy - 23), (hx - 4, hy - 32), (hx + 9, hy - 29), (hx + 5, hy - 6), (hx - 18, hy - 2)],
            SKIN_LIGHT,
            outline=None,
            width=0,
        )
        _poly(
            draw,
            [(hx + 13, hy + 3), (hx + 33, hy + 7), (hx + 25, hy + 24), (hx + 8, hy + 31), (hx + 4, hy + 17)],
            SKIN_SHADOW,
            outline=None,
            width=0,
        )

        # Long nose and sagging face are still the primary read, now with a
        # clear bridge, bulb, nostril, and highlight.
        nose = [
            (hx + 13, hy - 10),
            (hx + 31, hy - 11),
            (hx + 60, hy - 6),
            (hx + 74, hy + 1),
            (hx + 67, hy + 9),
            (hx + 48, hy + 12),
            (hx + 19, hy + 6),
        ]
        _poly(draw, nose, NOSE, OUTLINE, 1.15)
        nose_light = [
            (hx + 24, hy - 7),
            (hx + 57, hy - 3),
            (hx + 67, hy + 1),
            (hx + 53, hy + 4),
            (hx + 27, hy + 1),
        ]
        _poly(draw, nose_light, NOSE_LIGHT, outline=None, width=0)
        _circle(draw, (hx + 64, hy + 4), 2.2, SKIN_DEEP, SKIN_DEEP, 0.2)
        _line(draw, [(hx + 18, hy - 8), (hx + 24, hy + 4)], SKIN_DEEP, 0.75)

        chin = [
            (hx + 8, hy + 17),
            (hx + 34, hy + 19 + pose.jaw * 18),
            (hx + 27, hy + 37 + pose.jaw * 14),
            (hx + 5, hy + 31),
            (hx - 2, hy + 23),
        ]
        _poly(draw, chin, SKIN_SHADOW, OUTLINE, 0.9)

        # Split moustache keeps the original ratty expression but reads at game
        # scale better than one straight line.
        left_moustache = [(hx + 18, hy + 7), (hx + 31, hy + 14), (hx + 38, hy + 13)]
        right_moustache = [(hx + 35, hy + 13), (hx + 47, hy + 15), (hx + 54, hy + 10)]
        _line(draw, left_moustache, OUTLINE, 3.4)
        _line(draw, left_moustache, MOUSTACHE, 2.2)
        _line(draw, right_moustache, OUTLINE, 3.2)
        _line(draw, right_moustache, MOUSTACHE, 2.0)
        _line(draw, [(hx + 24, hy + 12), (hx + 31, hy + 21)], MOUSTACHE_HI, 0.7)

        # Ear, brow, single visible eye, and multiple crooked wrinkles.
        _ellipse(draw, hx - 23, hy - 1, 6.5, 10.5, SKIN_SHADOW, OUTLINE, 0.9)
        _line(draw, [(hx - 24, hy - 3), (hx - 20, hy + 2), (hx - 23, hy + 7)], SKIN_DEEP, 0.55)
        _line(draw, [(hx - 8, hy - 15), (hx + 11, hy - 18)], MOUSTACHE, 1.45)
        if pose.x_eyes:
            _line(draw, [(hx + 1, hy - 10), (hx + 12, hy + 0)], OUTLINE, 1.15)
            _line(draw, [(hx + 1, hy + 0), (hx + 12, hy - 10)], OUTLINE, 1.15)
        elif pose.blink:
            _line(draw, [(hx + 1, hy - 7), (hx + 14, hy - 7)], OUTLINE, 1.1)
        else:
            _ellipse(draw, hx + 8, hy - 8, 4.3, 3.0, EYE_WHITE, OUTLINE, 0.65)
            _circle(draw, (hx + 9.2, hy - 8.0), 1.3, EYE, EYE, 0.2)
            _circle(draw, (hx + 9.7, hy - 8.6), 0.35, SKIN_LIGHT, None, 0)
        _line(draw, [(hx - 3, hy + 5), (hx + 10, hy + 9)], SKIN_DEEP, 0.75)
        _line(draw, [(hx - 4, hy + 13), (hx + 8, hy + 17)], SKIN_DEEP, 0.65)
        _line(draw, [(hx - 7, hy + 20), (hx + 5, hy + 23)], SKIN_SHADOW, 0.55)

    def _draw_arm(self, draw, shoulder, elbow, hand, front: bool, reach: float):
        skin = SKIN if front else SKIN_SHADOW
        highlight = SKIN_LIGHT if front else SKIN
        upper_w = 8.4 if front else 6.8
        lower_w = 7.4 if front else 5.8

        # Proper outlined tubes instead of a dark line painted through the limb.
        _line(draw, [shoulder, elbow], OUTLINE, upper_w + 3.0)
        _line(draw, [shoulder, elbow], skin, upper_w)
        _line(draw, [elbow, hand], OUTLINE, lower_w + 2.8)
        _line(draw, [elbow, hand], skin, lower_w)
        _ellipse(draw, elbow[0], elbow[1], 6.8 if front else 5.3, 8.2 if front else 6.4, skin, OUTLINE, 0.9)
        _line(draw, [(elbow[0] - 2, elbow[1] - 2), (elbow[0] + 2, elbow[1] + 2)], highlight, 0.7)
        _ellipse(draw, hand[0], hand[1], 5.8 if front else 4.7, 5.0 if front else 4.0, skin, OUTLINE, 0.9)

        # Four long, crooked fingers are integral to the original character.
        # Each bends slightly rather than reading as detached straight whiskers.
        spreads = (-6.0, -2.0, 2.2, 6.0)
        for idx, dy in enumerate(spreads):
            length = (19.0 + idx * 2.2 + reach * 0.10) if front else (14.0 + idx * 1.4)
            base = (hand[0] + 3.0, hand[1] + dy * 0.38)
            knuckle = (hand[0] + length * 0.55, hand[1] + dy + (idx - 1.5) * 0.6)
            tip = (hand[0] + length, hand[1] + dy + idx * 1.05)
            finger_w = 1.65 if front else 1.15
            _line(draw, [base, knuckle, tip], OUTLINE, finger_w + 1.3)
            _line(draw, [base, knuckle, tip], skin, finger_w)
            _circle(draw, knuckle, 1.15 if front else 0.85, highlight, OUTLINE_SOFT, 0.25)

    def _draw_near_arm(self, draw, P, pose):
        shoulder = P(29, -112)
        elbow = P(42 + pose.near_arm * 0.10 + pose.near_reach * 0.22, -76 + pose.near_arm * 0.18)
        hand = P(55 + pose.near_arm * 0.20 + pose.near_reach, -47 + pose.near_arm * 0.14)
        self._draw_arm(draw, shoulder, elbow, hand, True, pose.near_reach)

    def _draw_far_arm(self, draw, P, pose):
        shoulder = P(2, -112)
        elbow = P(10 + pose.far_arm * 0.10 + pose.far_reach * 0.16, -78 + pose.far_arm * 0.14)
        hand = P(23 + pose.far_arm * 0.16 + pose.far_reach, -54 + pose.far_arm * 0.12)
        self._draw_arm(draw, shoulder, elbow, hand, False, pose.far_reach)

    def _draw_leg(self, draw, hip, knee, foot, front: bool):
        skin = SKIN if front else SKIN_SHADOW
        highlight = SKIN_LIGHT if front else SKIN
        thigh_w = 10.0 if front else 8.0
        shin_w = 8.5 if front else 6.8
        _line(draw, [hip, knee], OUTLINE, thigh_w + 3.2)
        _line(draw, [hip, knee], skin, thigh_w)
        _line(draw, [knee, foot], OUTLINE, shin_w + 3.0)
        _line(draw, [knee, foot], skin, shin_w)
        _ellipse(draw, knee[0], knee[1], 7.5 if front else 6.0, 9.3 if front else 7.4, skin, OUTLINE, 0.9)
        _line(draw, [(knee[0] - 2, knee[1] - 2), (knee[0] + 2, knee[1] + 1)], highlight, 0.7)
        _ellipse(draw, foot[0], foot[1] + 1.0, 5.0 if front else 4.2, 5.5 if front else 4.6, skin, OUTLINE, 0.7)
        toes = [
            (foot[0] - 12, foot[1] + 2),
            (foot[0] + 21, foot[1] + 1),
            (foot[0] + 27, foot[1] + 7),
            (foot[0] + 18, foot[1] + 10),
            (foot[0] - 10, foot[1] + 9),
        ]
        _poly(draw, toes, skin, OUTLINE, 1.0)
        _line(draw, [(foot[0] - 5, foot[1] + 5), (foot[0] + 15, foot[1] + 5)], highlight, 0.55)
        for dx in (7, 14, 21):
            _line(draw, [(foot[0] + dx, foot[1] + 3), (foot[0] + dx + 4, foot[1] + 8)], OUTLINE_SOFT, 0.6)

    def _draw_near_leg(self, draw, P, pose):
        hip = P(30, -22)
        knee = P(44 + pose.near_leg * 0.16, 18 - pose.crouch * 0.35)
        foot = P(30 + pose.near_leg * 0.14, 28 - pose.near_foot_lift)
        self._draw_leg(draw, hip, knee, foot, True)

    def _draw_far_leg(self, draw, P, pose):
        hip = P(-18, -24)
        knee = P(-26 + pose.far_leg * 0.16, 12 - pose.crouch * 0.22)
        foot = P(-8 + pose.far_leg * 0.14, 29 - pose.far_foot_lift)
        self._draw_leg(draw, hip, knee, foot, False)

    def _draw_jab_fx(self, draw, P, pose):
        c = P(109 + pose.near_reach * 0.35, -48)
        # Two attached scratch-lines make the finger extension legible without
        # turning the attack into a held weapon.
        _line(draw, [(c[0] - 17, c[1]), (c[0] + 20, c[1] - 2)], OUTLINE, 3.1)
        _line(draw, [(c[0] - 17, c[1]), (c[0] + 20, c[1] - 2)], (255, 235, 180, 170), 1.5)
        _line(draw, [(c[0] - 7, c[1] - 8), (c[0] + 13, c[1] - 15)], (255, 235, 180, 125), 1.1)

    def _draw_grab_fx(self, draw, P, pose):
        c = P(105 + pose.near_reach * 0.25, -52)
        box = (_s(c[0] - 38), _s(c[1] - 28), _s(c[0] + 38), _s(c[1] + 28))
        draw.arc(box, 200, 340, fill=OUTLINE, width=_s(4.2))
        draw.arc(box, 200, 340, fill=(255, 230, 160, 155), width=_s(2.2))
        _line(draw, [(c[0] - 23, c[1] + 13), (c[0] - 10, c[1] + 4)], (255, 230, 160, 135), 1.0)

    def _draw_sneeze_fx(self, draw, P, pose):
        origin = P(76, -154)
        plume = [
            (origin[0], origin[1]),
            (origin[0] + 18, origin[1] - 4),
            (origin[0] + 38, origin[1] - 8),
            (origin[0] + 62, origin[1] - 4),
            (origin[0] + 84, origin[1] + 4),
        ]
        _line(draw, plume, OUTLINE, 4.6)
        _line(draw, plume, (*CURSE[:3], 170), 2.6)
        for i, (dx, dy, r) in enumerate([(24, -5, 9), (43, -10, 13), (63, -5, 17), (83, 4, 12)]):
            alpha = int(100 + pose.sneeze * 70 - i * 10)
            _ellipse(
                draw,
                origin[0] + dx,
                origin[1] + dy,
                r,
                r * 0.70,
                (*CURSE[:3], max(0, alpha)),
                outline=OUTLINE_SOFT,
                width=0.55,
            )
            _circle(
                draw,
                (origin[0] + dx + r * 0.15, origin[1] + dy - r * 0.10),
                max(1.0, r * 0.20),
                CURSE_CORE,
                outline=None,
                width=0,
            )


def _write_yaml(path: Path) -> None:
    # Emit the SheetRow shape the rest of the project uses:
    # animation/row_index/frame_count/duration_ms/duration_secs/rects.
    fw, fh = FRAME_SIZE
    lines = [
        f"target: {TARGET_BASENAME}",
        f"image: {TARGET_BASENAME}_spritesheet.png",
        "label_width: 0",
        f"frame_width: {fw}",
        f"frame_height: {fh}",
        "rows:",
    ]
    for row_index, (name, frames, ms) in enumerate(ROWS):
        lines += [
            f"  - animation: {name}",
            f"    row_index: {row_index}",
            f"    frame_count: {frames}",
            f"    duration_ms: {ms}",
            f"    duration_secs: {ms / 1000.0}",
            "    rects:",
        ]
        for fi in range(frames):
            lines += [
                f"      - x: {fi * fw}",
                f"        y: {row_index * fh}",
                f"        w: {fw}",
                f"        h: {fh}",
            ]
    path.write_text("\n".join(lines) + "\n")


def _write_ron(path: Path) -> None:
    # Vec<SheetRecord>-shaped RON so the runtime + record_index can
    # consume the file without special-casing weird_hermit.
    fw, fh = FRAME_SIZE
    out_lines = ["[", "(", f'    target: "{TARGET_BASENAME}",',
                 f'    image: "{TARGET_BASENAME}_spritesheet.png",',
                 "    label_width: 0,",
                 f"    frame_width: {fw},",
                 f"    frame_height: {fh},",
                 "    rows: ["]
    for row_index, (name, frames, ms) in enumerate(ROWS):
        out_lines.append("        (")
        out_lines.append(f'            animation: "{name}",')
        out_lines.append(f"            row_index: {row_index},")
        out_lines.append(f"            frame_count: {frames},")
        out_lines.append(f"            duration_ms: {ms},")
        out_lines.append(f"            duration_secs: {ms / 1000.0},")
        out_lines.append("            rects: [")
        for fi in range(frames):
            out_lines.append(
                f"                (x: {fi * fw}, y: {row_index * fh}, "
                f"w: {fw}, h: {fh}, anchors: {{}}),"
            )
        out_lines.append("            ],")
        out_lines.append("        ),")
    out_lines += ["    ],", ")", "]"]
    path.write_text("\n".join(out_lines) + "\n")


def _render_sheet(renderer: WeirdHermitRenderer, out_dir: Path) -> List[Path]:
    fw, fh = FRAME_SIZE
    sheet_w = max(frames for _, frames, _ in ROWS) * fw
    sheet_h = len(ROWS) * fh
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    preview = Image.new("RGBA", (sheet_w + 128, sheet_h), (248, 246, 242, 255))
    pdraw = ImageDraw.Draw(preview)
    canonical = None
    for row_idx, (name, nframes, _ms) in enumerate(ROWS):
        pdraw.text((8, row_idx * fh + 8), name, fill=(36, 36, 36, 255))
        for frame_idx in range(nframes):
            frame = renderer.render_frame(name, frame_idx, nframes)
            x = frame_idx * fw
            y = row_idx * fh
            sheet.alpha_composite(frame, (x, y))
            preview.alpha_composite(frame, (x + 128, y))
            if canonical is None and name == "idle" and frame_idx == 0:
                canonical = frame
    if canonical is None:
        canonical = renderer.render_frame(ROWS[0][0], 0, ROWS[0][1])
    paths = [
        out_dir / f"{TARGET_BASENAME}_spritesheet.png",
        out_dir / f"{TARGET_BASENAME}_spritesheet.yaml",
        out_dir / f"{TARGET_BASENAME}_spritesheet.ron",
        out_dir / f"{TARGET_BASENAME}_preview_labeled.png",
        out_dir / f"{TARGET_BASENAME}_canonical.png",
    ]
    sheet.save(paths[0])
    _write_yaml(paths[1])
    _write_ron(paths[2])
    preview.save(paths[3])
    canonical.save(paths[4])
    return paths


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return _render_sheet(WeirdHermitRenderer(), out_dir)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a side-profile weird hermit enemy spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_BASENAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
