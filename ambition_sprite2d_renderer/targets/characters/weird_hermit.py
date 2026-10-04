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
from ambition_sprite2d_renderer.authoring import rigdoc, shape_rig
from ambition_sprite2d_renderer.authoring.part_flipbook import LOCOMOTION_LOOPS, build_rig_flipbook, write_with_realization
from ambition_sprite2d_renderer.authoring.sheet_build import rendering_quality_tier
from ambition_sprite2d_renderer.core.draw import blending_draw

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
# Files the tack-on installer copies using the runtime's standard
# `<target>_spritesheet.{ext}` naming convention.
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
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


#: The torso piece's root inside its canvas, and the head pieces' centre.
TORSO_ORIGIN = (48.0, 168.0)
#: The hump piece keeps the torso above this line (torso units, from the root).
HUMP_CUT = -112.0
HEAD_ORIGIN = (34.0, 52.0)
HEAD_SIZE = (118.0, 100.0)
#: Where the cap's flap and the chin turn (head units, from its centre).
FLAP_HINGE = (33.0, -20.0)
JAW_HINGE = (-2.0, 23.0)
#: Fixed leg bone lengths (work units): hip to knee, knee to foot.
NEAR_THIGH, NEAR_SHIN = 40.0, 17.0
FAR_THIGH, FAR_SHIN = 36.0, 21.0


def _rig_piece(key: tuple, size: Tuple[float, float], origin: Point, paint) -> tuple:
    """A piece of the hermit painted once (``shape_rig``): ``paint(draw)`` draws
    in work units with its anchor at ``origin`` on a ``size`` canvas (work
    units). ``key`` names everything ``paint`` reads."""
    return shape_rig.piece(("weird_hermit",) + key, (size[0] * SUPER, size[1] * SUPER), (origin[0] * SUPER, origin[1] * SUPER), paint)


def _put(img: Image.Image, part: tuple, at: Point, name: str, degrees: float = 0.0) -> None:
    """``part`` with its anchor at the work point ``at``, turned ``degrees``."""
    shape_rig.place(img, part, (at[0] * SUPER, at[1] * SUPER), degrees, name)


def _bone(img: Image.Image, a: Point, b: Point, length: float, width: float, rim: float, fill: RGBA, name: str) -> None:
    """An outlined tube of ``length`` from ``a`` toward ``b``, painted once along +x."""
    pad = (width + rim) / 2.0 + 2.0

    def paint(d) -> None:
        _line(d, [(pad, pad), (pad + length, pad)], OUTLINE, width + rim)
        _line(d, [(pad, pad), (pad + length, pad)], fill, width)

    part = _rig_piece(("bone", length, width, rim, fill), (length + 2 * pad, 2 * pad), (pad, pad), paint)
    _put(img, part, a, name, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))


#: An arm bone's lengths are whole steps of this many work units.
ARM_STEP = 8.0


def _arm_length(a: Point, b: Point) -> float:
    return max(ARM_STEP, round(math.dist(a, b) / ARM_STEP) * ARM_STEP)


def _leg_chain(hip: Point, foot: Point, thigh: float, shin: float, bend: float) -> Tuple[Point, Point]:
    """Knee and foot of a two-bone leg of fixed lengths reaching from ``hip``
    toward ``foot``; ``bend`` -1 bends the knee forward (+x when upright), +1
    back. Out of reach, the leg straightens and its foot is the chain's end."""
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = max(1e-6, math.hypot(dx, dy))
    base = math.atan2(dy, dx)
    if d >= thigh + shin:
        return (
            (hip[0] + math.cos(base) * thigh, hip[1] + math.sin(base) * thigh),
            (hip[0] + math.cos(base) * (thigh + shin), hip[1] + math.sin(base) * (thigh + shin)),
        )
    a = math.acos(max(-1.0, min(1.0, (thigh * thigh + d * d - shin * shin) / (2 * thigh * d))))
    return (hip[0] + math.cos(base + bend * a) * thigh, hip[1] + math.sin(base + bend * a) * thigh), foot


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

        # No floor ellipse or baked contact shadow. Every rigid piece is
        # painted once and placed (``shape_rig``); the torso turns with the
        # body's tilt, the head, joints, hands and feet stay upright.
        self._draw_leg(img, P, pose, front=False)
        self._draw_arm(img, P, pose, front=False)
        self._draw_torso(img, root, global_tilt, pose)
        self._draw_leg(img, P, pose, front=True)
        self._draw_arm(img, P, pose, front=True)
        # The expressive profile is always the top body layer.
        self._draw_head(img, P, pose)
        # Each effect is one piece that only moves (and fades).
        if pose.jab > 0.2:
            _put(img, _rig_piece(("jab_fx",), (46, 24), (21, 19), lambda d: self._paint_jab_fx(d, (21, 19))), P(109 + pose.near_reach * 0.35, -48), "jab_fx")
        if pose.grab > 0.2:
            _put(img, _rig_piece(("grab_fx",), (84, 64), (42, 32), lambda d: self._paint_grab_fx(d, (42, 32))), P(105 + pose.near_reach * 0.25, -52), "grab_fx")
        if pose.sneeze > 0.15:
            origin = P(76, -154)
            _put(img, _rig_piece(("sneeze_plume",), (104, 40), (6, 22), lambda d: self._paint_sneeze_plume(d, (6, 22))), origin, "sneeze_plume")
            puffs = _rig_piece(("sneeze_puffs",), (104, 40), (6, 22), lambda d: self._paint_sneeze_puffs(d, (6, 22)))
            rigdoc.blit_rotated(img, puffs[0], puffs[1], (origin[0] * SUPER, origin[1] * SUPER), 0.0, round((100 + pose.sneeze * 70) / 170, 3), part_name="sneeze_puffs")
        return _downsample(img)

    def _draw_torso(self, img, root, tilt, pose):
        """The torso as two pieces turned with the tilt: the body, and its
        hunched back (above ``HUMP_CUT``) raised by the crouch."""
        lower = _rig_piece(("torso",), (104, 172), TORSO_ORIGIN, lambda d: self._paint_torso(d, upper=False))
        _put(img, lower, root, "torso", tilt)
        upper = _rig_piece(("hump",), (104, 172), TORSO_ORIGIN, lambda d: self._paint_torso(d, upper=True))
        lift = _rot_local(0.0, -pose.crouch, tilt)
        _put(img, upper, (root[0] + lift[0], root[1] + lift[1]), "hump", tilt)

    def _paint_torso(self, draw, upper: bool):
        """The torso in its own unturned frame, the root at ``TORSO_ORIGIN``:
        the hump (``upper``, only above ``HUMP_CUT``) or the body without
        the marks the hump carries."""
        crouch = 0.0

        def P(x: float, y: float) -> Point:
            return (TORSO_ORIGIN[0] + x, TORSO_ORIGIN[1] + y)

        # Same bare, hunched, pot-bellied body as the original, but with a
        # cleaner back curve and readable shoulder / belly planes.
        torso = [
            P(-32, -120 - crouch),
            P(-19, -139 - crouch),
            P(5, -151 - crouch),
            P(31, -137 - crouch),
            P(43, -116 - crouch),
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
            P(-31, -116 - crouch),
            P(-18, -137 - crouch),
            P(-5, -142 - crouch),
            P(-12, -70),
            P(-29, -53),
            P(-40, -85),
        ]
        _poly(draw, back_plane, SKIN_SHADOW, outline=None, width=0)

        if upper:
            # The age mark rides the hump; nothing below the cut is kept.
            _line(draw, [P(-1, -118), P(11, -121), P(19, -113)], SKIN_DEEP, 1.0)
            image = draw._image
            image.paste((0, 0, 0, 0), (0, _s(TORSO_ORIGIN[1] + HUMP_CUT), image.width, image.height))
            return

        # Sparse ribs, a scar and the navel: intrinsic anatomy, not costume.
        _line(draw, [P(-3, -108), P(10, -105)], SKIN_SHADOW, 0.75)
        _line(draw, [P(1, -91), P(12, -87)], SKIN_SHADOW, 0.75)
        _ellipse(draw, *P(21, -76), 2.4, 3.1, SKIN_DEEP, OUTLINE_SOFT, 0.35)
        _poly(draw, [P(-2, -105), P(5, -112), P(12, -103), P(6, -95)], SKIN_SHADOW, OUTLINE_SOFT, 0.45)
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

    def _draw_head(self, img, P, pose):
        """Upright at the head's centre: the cap, its flap turned by the
        swing about its hinge, the skull and nose, the chin turned open by
        the jaw about its hinge, the face and one eye piece per eye state."""
        at = P(11, -158 - pose.crouch * 0.35 + pose.head_tilt * 0.14)
        eyes = "x" if pose.x_eyes else ("blink" if pose.blink else "open")
        hx, hy = HEAD_ORIGIN
        _put(img, _rig_piece(("cap",), HEAD_SIZE, HEAD_ORIGIN, lambda d: self._paint_cap(d)), at, "cap")
        fx, fy = FLAP_HINGE
        flap = _rig_piece(("flap",), HEAD_SIZE, (hx + fx, hy + fy), lambda d: self._paint_flap(d))
        _put(img, flap, (at[0] + fx, at[1] + fy), "flap", pose.cap_swing * 0.5)
        _put(img, _rig_piece(("skull",), HEAD_SIZE, HEAD_ORIGIN, lambda d: self._paint_skull(d)), at, "skull")
        cx, cy = JAW_HINGE
        chin = _rig_piece(("chin",), HEAD_SIZE, (hx + cx, hy + cy), lambda d: self._paint_chin(d))
        _put(img, chin, (at[0] + cx, at[1] + cy), "chin", pose.jaw * 30.0)
        _put(img, _rig_piece(("face",), HEAD_SIZE, HEAD_ORIGIN, lambda d: self._paint_face(d)), at, "face")
        _put(img, _rig_piece(("eye", eyes), (24, 20), (4, 14), lambda d: self._paint_eye(d, (4, 14), eyes)), at, "eye")

    def _paint_cap(self, draw):
        hx, hy = HEAD_ORIGIN
        swing = 0.0

        # Preserve the original floppy cloth cap / head rag.  The pointed flap
        # is the secondary silhouette after the nose.
        cap = [
            (hx - 18, hy - 31),
            (hx - 6, hy - 45),
            (hx + 17, hy - 47),
            (hx + 38, hy - 36),
            (hx + 48 + swing * 0.22, hy - 21),
            (hx + 38 + swing * 0.34, hy - 7),
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

    def _paint_flap(self, draw):
        """The cap's flap, at rest (it turns about ``FLAP_HINGE``)."""
        hx, hy = HEAD_ORIGIN
        swing = 0.0
        flap = [
            (hx + 31, hy - 34),
            (hx + 73 + swing * 0.34, hy - 38),
            (hx + 67 + swing * 0.48, hy - 10),
            (hx + 36, hy - 7),
        ]
        _poly(draw, flap, CLOTH_SHADOW, OUTLINE, 1.05)
        _line(draw, [(hx + 34, hy - 31), (hx + 63 + swing * 0.30, hy - 31)], CLOTH_LIGHT, 0.75)

    def _paint_skull(self, draw):
        hx, hy = HEAD_ORIGIN
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

    def _paint_chin(self, draw):
        """The chin closed (it turns open about ``JAW_HINGE``)."""
        hx, hy = HEAD_ORIGIN
        jaw = 0.0
        chin = [
            (hx + 8, hy + 17),
            (hx + 34, hy + 19 + jaw * 18),
            (hx + 27, hy + 37 + jaw * 14),
            (hx + 5, hy + 31),
            (hx - 2, hy + 23),
        ]
        _poly(draw, chin, SKIN_SHADOW, OUTLINE, 0.9)

    def _paint_face(self, draw):
        """Moustache, ear, brow and wrinkles (the eye is its own piece)."""
        hx, hy = HEAD_ORIGIN
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
        _line(draw, [(hx - 3, hy + 5), (hx + 10, hy + 9)], SKIN_DEEP, 0.75)
        _line(draw, [(hx - 4, hy + 13), (hx + 8, hy + 17)], SKIN_DEEP, 0.65)
        _line(draw, [(hx - 7, hy + 20), (hx + 5, hy + 23)], SKIN_SHADOW, 0.55)

    def _paint_eye(self, draw, origin, eyes):
        """The eye, its piece's ``origin`` at the head's centre."""
        hx, hy = origin
        if eyes == "x":
            _line(draw, [(hx + 1, hy - 10), (hx + 12, hy + 0)], OUTLINE, 1.15)
            _line(draw, [(hx + 1, hy + 0), (hx + 12, hy - 10)], OUTLINE, 1.15)
        elif eyes == "blink":
            _line(draw, [(hx + 1, hy - 7), (hx + 14, hy - 7)], OUTLINE, 1.1)
        else:
            _ellipse(draw, hx + 8, hy - 8, 4.3, 3.0, EYE_WHITE, OUTLINE, 0.65)
            _circle(draw, (hx + 9.2, hy - 8.0), 1.3, EYE, EYE, 0.2)
            _circle(draw, (hx + 9.7, hy - 8.6), 0.35, SKIN_LIGHT, None, 0)

    def _draw_arm(self, img, P, pose, front: bool):
        """An arm: two bones (their lengths follow the authored stretch of the
        jab and grab, rounded to whole units), an elbow and a hand, the joint
        and hand upright."""
        if front:
            reach = pose.near_reach
            shoulder = P(29, -112)
            elbow = P(42 + pose.near_arm * 0.10 + pose.near_reach * 0.22, -76 + pose.near_arm * 0.18)
            hand = P(55 + pose.near_arm * 0.20 + pose.near_reach, -47 + pose.near_arm * 0.14)
        else:
            reach = pose.far_reach
            shoulder = P(2, -112)
            elbow = P(10 + pose.far_arm * 0.10 + pose.far_reach * 0.16, -78 + pose.far_arm * 0.14)
            hand = P(23 + pose.far_arm * 0.16 + pose.far_reach, -54 + pose.far_arm * 0.12)
        side = "near" if front else "far"
        skin = SKIN if front else SKIN_SHADOW
        upper_w = 8.4 if front else 6.8
        lower_w = 7.4 if front else 5.8
        # The arm stretches: each bone takes a length in steps of
        # ``ARM_STEP``; the upper arm grows from the shoulder and the forearm
        # from the hand, and the elbow covers where they miss each other.
        _bone(img, shoulder, elbow, _arm_length(shoulder, elbow), upper_w, 3.0, skin, f"{side}_upper_arm")
        _bone(img, hand, elbow, _arm_length(elbow, hand), lower_w, 2.8, skin, f"{side}_forearm")
        _put(img, _rig_piece(("elbow", front), (20, 22), (10, 11), lambda d: self._paint_elbow(d, (10, 11), front)), elbow, f"{side}_elbow")
        reach_q = float(round(reach / 14.0) * 14) if front else 0.0
        _put(img, _rig_piece(("hand", front, reach_q), (44, 22), (8, 10), lambda d: self._paint_hand(d, (8, 10), front, reach_q)), hand, f"{side}_hand")

    def _paint_elbow(self, draw, elbow, front: bool):
        skin = SKIN if front else SKIN_SHADOW
        highlight = SKIN_LIGHT if front else SKIN
        _ellipse(draw, elbow[0], elbow[1], 6.8 if front else 5.3, 8.2 if front else 6.4, skin, OUTLINE, 0.9)
        _line(draw, [(elbow[0] - 2, elbow[1] - 2), (elbow[0] + 2, elbow[1] + 2)], highlight, 0.7)

    def _paint_hand(self, draw, hand, front: bool, reach: float):
        skin = SKIN if front else SKIN_SHADOW
        highlight = SKIN_LIGHT if front else SKIN
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

    def _draw_leg(self, img, P, pose, front: bool):
        """A leg: thigh and shin bones of fixed length reaching the foot (the
        near knee bends forward, the far one back), a knee and a foot."""
        if front:
            hip = P(30, -22)
            foot = P(30 + pose.near_leg * 0.14, 28 - pose.near_foot_lift)
            thigh, shin, bend = NEAR_THIGH, NEAR_SHIN, -1.0
        else:
            hip = P(-18, -24)
            foot = P(-8 + pose.far_leg * 0.14, 29 - pose.far_foot_lift)
            thigh, shin, bend = FAR_THIGH, FAR_SHIN, 1.0
        knee, foot = _leg_chain(hip, foot, thigh, shin, bend)
        side = "near" if front else "far"
        skin = SKIN if front else SKIN_SHADOW
        thigh_w = 10.0 if front else 8.0
        shin_w = 8.5 if front else 6.8
        _bone(img, hip, knee, thigh, thigh_w, 3.2, skin, f"{side}_thigh")
        _bone(img, knee, foot, shin, shin_w, 3.0, skin, f"{side}_shin")
        _put(img, _rig_piece(("knee", front), (20, 24), (10, 12), lambda d: self._paint_knee(d, (10, 12), front)), knee, f"{side}_knee")
        _put(img, _rig_piece(("foot", front), (46, 22), (15, 8), lambda d: self._paint_foot(d, (15, 8), front)), foot, f"{side}_foot")

    def _paint_knee(self, draw, knee, front: bool):
        skin = SKIN if front else SKIN_SHADOW
        highlight = SKIN_LIGHT if front else SKIN
        _ellipse(draw, knee[0], knee[1], 7.5 if front else 6.0, 9.3 if front else 7.4, skin, OUTLINE, 0.9)
        _line(draw, [(knee[0] - 2, knee[1] - 2), (knee[0] + 2, knee[1] + 1)], highlight, 0.7)

    def _paint_foot(self, draw, foot, front: bool):
        skin = SKIN if front else SKIN_SHADOW
        highlight = SKIN_LIGHT if front else SKIN
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

    def _paint_jab_fx(self, draw, c):
        # Two attached scratch-lines make the finger extension legible without
        # turning the attack into a held weapon.
        _line(draw, [(c[0] - 17, c[1]), (c[0] + 20, c[1] - 2)], OUTLINE, 3.1)
        _line(draw, [(c[0] - 17, c[1]), (c[0] + 20, c[1] - 2)], (255, 235, 180, 170), 1.5)
        _line(draw, [(c[0] - 7, c[1] - 8), (c[0] + 13, c[1] - 15)], (255, 235, 180, 125), 1.1)

    def _paint_grab_fx(self, draw, c):
        box = (_s(c[0] - 38), _s(c[1] - 28), _s(c[0] + 38), _s(c[1] + 28))
        draw.arc(box, 200, 340, fill=OUTLINE, width=_s(4.2))
        draw.arc(box, 200, 340, fill=(255, 230, 160, 155), width=_s(2.2))
        _line(draw, [(c[0] - 23, c[1] + 13), (c[0] - 10, c[1] + 4)], (255, 230, 160, 135), 1.0)

    def _paint_sneeze_plume(self, draw, origin):
        plume = [
            (origin[0], origin[1]),
            (origin[0] + 18, origin[1] - 4),
            (origin[0] + 38, origin[1] - 8),
            (origin[0] + 62, origin[1] - 4),
            (origin[0] + 84, origin[1] + 4),
        ]
        _line(draw, plume, OUTLINE, 4.6)
        _line(draw, plume, (*CURSE[:3], 170), 2.6)

    def _paint_sneeze_puffs(self, draw, origin):
        """The puffs at the sneeze's peak (placed fading with its strength)."""
        for i, (dx, dy, r) in enumerate([(24, -5, 9), (43, -10, 13), (63, -5, 17), (83, 4, 12)]):
            alpha = int(170 - i * 10)
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
    pdraw = blending_draw(preview)
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
    # The part flipbook. This sheet places every frame whole at its cell and
    # states no feet: the flipbook's origin is the frame's bottom centre (its
    # draws are relative to it, so any origin draws the same pixels).
    if rendering_quality_tier():
        return paths
    tweened = [name for name, _frames, _ms in ROWS if name in LOCOMOTION_LOOPS]
    flipbook = build_rig_flipbook(TARGET_BASENAME, ROWS, renderer.render_frame, None, (fw / 2, float(fh)), FRAME_SIZE, tweened)
    return paths + list(write_with_realization(flipbook, paths[1], out_dir).values())


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
