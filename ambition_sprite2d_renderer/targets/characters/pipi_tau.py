"""Procedural full-action renderer for Pipi Tau.

Pipi Tau is a playful mathematical-action parody built around breadth,
collaboration, and the habit of turning one impossible problem into a sequence
of tractable lemmas.  He is deliberately *not* another robed professor.  His
silhouette is a compact, quick-footed problem runner: side-swept black hair,
rectangular glasses, a short asymmetric teal jacket over a dark tau tee,
tapered trousers, and broad running shoes.

The animation vocabulary turns mathematical habits into movement rather than
held props:

* ``prime_stride`` advances in an uneven but purposeful rhythm;
* ``compressed_sense`` gathers a broad circular field into one narrow strike;
* ``polymath_chain`` links several small contributions into a larger result;
* ``full_turn`` traces a complete tau-ring around the body;
* ``epsilon_dash`` wins a tiny amount of distance repeatedly and very quickly.

Everything is authored in Python/Pillow.  There are no generated-image inputs,
held props, floor ellipses, or drop shadows.  Ability marks are tethered to the
body or attack path so the base character remains authoritative.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from ...authoring.sheet_build import build_sheet, write_canonical

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "pipi_tau"
FRAME_W = 128
FRAME_H = 128
SUPER = 4

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 145),
    ("walk", 8, 104),
    ("run", 8, 76),
    ("crouch", 6, 95),
    ("crouch_walk", 8, 88),
    ("jump", 6, 92),
    ("fall", 6, 92),
    ("land_hard", 8, 92),
    ("land_recovery", 6, 72),
    ("dash_startup", 4, 48),
    ("dash", 6, 60),
    ("epsilon_dash", 8, 54),
    ("slide", 6, 68),
    ("roll", 8, 56),
    ("wall_grab", 6, 105),
    ("wall_jump", 6, 82),
    ("ledge_grab", 6, 98),
    ("ledge_climb", 6, 98),
    ("ledge_getup", 6, 42),
    ("ledge_roll", 8, 38),
    ("climb", 8, 98),
    ("swim", 8, 102),
    ("float_glide", 8, 108),
    ("block", 6, 82),
    ("hit", 5, 86),
    ("death", 8, 105),
    ("talk", 8, 104),
    ("interact", 8, 90),
    ("jab", 5, 56),
    ("punch", 7, 68),
    ("prime_stride", 8, 64),
    ("attack_up", 8, 64),
    ("attack_down", 8, 64),
    ("air_neutral", 8, 60),
    ("air_forward", 7, 60),
    ("air_back", 7, 60),
    ("air_down", 7, 68),
    ("air_up", 7, 60),
    ("compressed_sense", 8, 74),
    ("polymath_chain", 8, 78),
    ("full_turn", 10, 76),
    ("celebrate", 8, 88),
    ("taunt", 8, 92),
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_pipi_tau", "display_name": "Pipi Tau"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "mathematician",
            "problem_runner",
            "collaborative",
            "playable_candidate",
        ],
        "locomotion_hint": "Run",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": True,
            "fly": None,
            "swim": True,
            "crawl": True,
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
    "tags": [
        "story",
        "humanoid",
        "mathematician",
        "problem_runner",
        "collaborative",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 28.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 63.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 48.0, "y": 79.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 84.0, "y": 79.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 5.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "prime_stride", "events": []},
        "action.ranged.primary": {"animation": "compressed_sense", "events": []},
        "action.special.primary": {"animation": "full_turn", "events": []},
        "action.special.secondary": {"animation": "polymath_chain", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}

OUTLINE = (13, 20, 25, 255)
OUTLINE_SOFT = (30, 47, 53, 255)
SKIN = (190, 137, 101, 255)
SKIN_LIGHT = (224, 174, 132, 255)
SKIN_SHADE = (145, 96, 73, 255)
HAIR = (20, 27, 31, 255)
HAIR_MID = (37, 49, 54, 255)
HAIR_GLEAM = (72, 88, 91, 255)
JACKET = (35, 129, 136, 255)
JACKET_LIGHT = (63, 164, 166, 255)
JACKET_DARK = (22, 82, 91, 255)
JACKET_DEEP = (17, 57, 68, 255)
SHIRT = (36, 49, 58, 255)
SHIRT_SHADE = (70, 88, 98, 255)
TROUSER = (37, 47, 67, 255)
TROUSER_LIGHT = (56, 70, 91, 255)
TROUSER_DARK = (24, 31, 48, 255)
SHOE = (232, 219, 188, 255)
SHOE_DARK = (83, 82, 77, 255)
SOLE = (22, 34, 42, 255)
GLASS = (225, 246, 244, 46)
EYE = (28, 25, 22, 255)
MOUTH = (109, 55, 48, 255)
TAU_GOLD = (246, 184, 65, 255)
TAU_LIGHT = (255, 227, 134, 255)
LEMMA_BLUE = (96, 205, 227, 255)
LEMMA_PINK = (230, 108, 153, 255)
LEMMA_GREEN = (117, 207, 125, 255)
FIELD = (126, 224, 211, 255)


def _s(value: float) -> int:
    return max(1, int(round(value * SUPER)))


def _pt(point: Point) -> Tuple[int, int]:
    return (int(round(point[0] * SUPER)), int(round(point[1] * SUPER)))


def _bbox(center: Point, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (
        _s(center[0] - rx),
        _s(center[1] - ry),
        _s(center[0] + rx),
        _s(center[1] + ry),
    )


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smooth(value: float) -> float:
    value = _clamp01(value)
    return value * value * (3.0 - 2.0 * value)


def _pulse(value: float) -> float:
    return math.sin(_clamp01(value) * math.pi)


def _lerp(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def _lerp_point(a: Point, b: Point, amount: float) -> Point:
    return (_lerp(a[0], b[0], amount), _lerp(a[1], b[1], amount))


def _offset(point: Point, dx: float, dy: float) -> Point:
    return (point[0] + dx, point[1] + dy)


def _rotate(point: Point, origin: Point, degrees: float) -> Point:
    radians = math.radians(degrees)
    c = math.cos(radians)
    s = math.sin(radians)
    x = point[0] - origin[0]
    y = point[1] - origin[1]
    return (origin[0] + x * c - y * s, origin[1] + x * s + y * c)


def _unit(a: Point, b: Point) -> Tuple[Point, Point, float]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = max(1.0e-6, math.hypot(dx, dy))
    along = (dx / length, dy / length)
    normal = (-along[1], along[0])
    return along, normal, length


def _segment_quad(a: Point, b: Point, ra: float, rb: float) -> List[Point]:
    _, normal, _ = _unit(a, b)
    return [
        (a[0] + normal[0] * ra, a[1] + normal[1] * ra),
        (b[0] + normal[0] * rb, b[1] + normal[1] * rb),
        (b[0] - normal[0] * rb, b[1] - normal[1] * rb),
        (a[0] - normal[0] * ra, a[1] - normal[1] * ra),
    ]



def _polygon(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    pts = [_pt(point) for point in points]
    draw.polygon(pts, fill=fill)
    draw.line(pts + [pts[0]], fill=outline, width=_s(width), joint="curve")


def _line(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    width: float,
) -> None:
    draw.line([_pt(point) for point in points], fill=fill, width=_s(width), joint="curve")


def _ellipse(
    draw: ImageDraw.ImageDraw,
    center: Point,
    rx: float,
    ry: float,
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        _bbox(center, rx, ry),
        fill=fill,
        outline=outline,
        width=_s(width) if outline is not None else 1,
    )


def _arc(
    draw: ImageDraw.ImageDraw,
    center: Point,
    rx: float,
    ry: float,
    start: float,
    end: float,
    fill: RGBA,
    width: float,
) -> None:
    draw.arc(_bbox(center, rx, ry), start=start, end=end, fill=fill, width=_s(width))


def _font(
    size: float,
    *,
    bold: bool = False,
    preferred: tuple[str, ...] | None = None,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if preferred is not None:
        names = preferred
    else:
        names = ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf") if bold else ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
    for name in names:
        try:
            return ImageFont.truetype(name, _s(size))
        except OSError:
            pass
    return ImageFont.load_default()


def _fade(color: RGBA, alpha: float) -> RGBA:
    return (color[0], color[1], color[2], int(round(color[3] * _clamp01(alpha))))


@dataclass
class Pose:
    root_x: float = 0.0
    root_y: float = 0.0
    rotation: float = 0.0
    rotation_pivot: Point = (64.0, 86.0)
    body_lean: float = 0.0
    head_x: float = 0.0
    head_y: float = 0.0
    head_tilt: float = 0.0
    blink: bool = False
    mouth_open: float = 0.0
    smile: float = 0.25
    brow: float = 0.0
    near_shoulder: Point = (78.0, 55.0)
    near_elbow: Point = (84.0, 72.0)
    near_hand: Point = (83.0, 86.0)
    far_shoulder: Point = (51.0, 56.0)
    far_elbow: Point = (45.0, 73.0)
    far_hand: Point = (47.0, 87.0)
    near_hip: Point = (70.0, 87.0)
    near_knee: Point = (72.0, 102.0)
    near_ankle: Point = (74.0, 117.0)
    far_hip: Point = (59.0, 87.0)
    far_knee: Point = (57.0, 102.0)
    far_ankle: Point = (56.0, 117.0)
    near_hand_mode: str = "relaxed"
    far_hand_mode: str = "relaxed"
    field: float = 0.0
    field_phase: float = 0.0
    full_turn: float = 0.0
    compress: float = 0.0
    chain: float = 0.0
    prime: float = 0.0
    epsilon: float = 0.0


def _pose(animation: str, frame_idx: int, nframes: int) -> Pose:
    phase = frame_idx / max(1, nframes)
    t = frame_idx / max(1, nframes - 1)
    cyc = math.tau * phase
    wave = math.sin(cyc)
    cosine = math.cos(cyc)
    p = Pose()
    p.root_y = 0.6 * math.sin(cyc)
    p.head_y = -0.35 * math.sin(cyc)
    p.blink = animation == "idle" and frame_idx in {5}

    if animation == "walk":
        stride = 8.5 * wave
        p.root_y = -1.0 * abs(cosine)
        p.body_lean = 2.0
        p.near_knee = (72.0 + stride * 0.42, 102.0 - abs(stride) * 0.18)
        p.near_ankle = (74.0 + stride, 117.0 - max(0.0, -wave) * 3.0)
        p.far_knee = (57.0 - stride * 0.42, 102.0 - abs(stride) * 0.18)
        p.far_ankle = (56.0 - stride, 117.0 - max(0.0, wave) * 3.0)
        p.near_elbow = (83.0 - stride * 0.35, 71.0)
        p.near_hand = (80.0 - stride * 0.65, 84.0)
        p.far_elbow = (47.0 + stride * 0.35, 72.0)
        p.far_hand = (49.0 + stride * 0.65, 85.0)
    elif animation == "run":
        stride = 13.0 * wave
        p.root_y = -2.5 * abs(cosine)
        p.body_lean = 9.0
        p.head_x = 1.5
        p.near_knee = (73.0 + stride * 0.45, 100.0 - abs(stride) * 0.20)
        p.near_ankle = (75.0 + stride, 115.0 - max(0.0, -wave) * 5.0)
        p.far_knee = (58.0 - stride * 0.45, 101.0 - abs(stride) * 0.20)
        p.far_ankle = (56.0 - stride, 116.0 - max(0.0, wave) * 5.0)
        p.near_elbow = (78.0 - stride * 0.35, 66.0)
        p.near_hand = (74.0 - stride * 0.62, 77.0)
        p.far_elbow = (54.0 + stride * 0.35, 68.0)
        p.far_hand = (57.0 + stride * 0.62, 80.0)
    elif animation in {"crouch", "crouch_walk"}:
        step = 5.0 * wave if animation == "crouch_walk" else 0.0
        p.root_y = 13.0
        p.body_lean = 8.0
        p.head_y = 4.0
        p.near_hip = (70.0, 91.0)
        p.near_knee = (79.0 + step, 104.0)
        p.near_ankle = (73.0 + step * 1.3, 117.0)
        p.far_hip = (59.0, 91.0)
        p.far_knee = (51.0 - step, 105.0)
        p.far_ankle = (57.0 - step * 1.3, 117.0)
        p.near_elbow = (84.0, 79.0)
        p.near_hand = (76.0, 91.0)
        p.far_elbow = (50.0, 79.0)
        p.far_hand = (57.0, 92.0)
    elif animation == "jump":
        lift = math.sin(t * math.pi)
        p.root_y = -12.0 * lift
        p.body_lean = 5.0
        p.near_knee = (74.0, 100.0 - 4.0 * lift)
        p.near_ankle = (82.0, 111.0 - 8.0 * lift)
        p.far_knee = (57.0, 99.0 - 3.0 * lift)
        p.far_ankle = (51.0, 110.0 - 7.0 * lift)
        p.near_elbow = (86.0, 62.0)
        p.near_hand = (90.0, 48.0)
        p.far_elbow = (48.0, 64.0)
        p.far_hand = (43.0, 53.0)
    elif animation == "fall":
        p.root_y = -6.0 + 8.0 * t
        p.body_lean = -2.0
        p.near_elbow = (88.0, 66.0)
        p.near_hand = (94.0, 57.0)
        p.far_elbow = (44.0, 67.0)
        p.far_hand = (38.0, 59.0)
        p.near_knee = (77.0, 101.0)
        p.near_ankle = (82.0, 112.0)
        p.far_knee = (53.0, 101.0)
        p.far_ankle = (49.0, 113.0)
    elif animation in {"land_hard", "land_recovery"}:
        impact = 1.0 - t if animation == "land_recovery" else _pulse(min(1.0, t * 1.6))
        p.root_y = 11.0 * impact
        p.body_lean = 9.0 * impact
        p.head_y = 3.0 * impact
        p.near_knee = (79.0, 103.0)
        p.near_ankle = (75.0, 117.0)
        p.far_knee = (52.0, 104.0)
        p.far_ankle = (56.0, 117.0)
        p.near_hand = (82.0, 101.0)
        p.far_hand = (52.0, 101.0)
    elif animation in {"dash_startup", "dash", "epsilon_dash", "slide"}:
        amount = _smooth(t) if animation == "dash_startup" else 1.0
        if animation == "slide":
            p.root_y = 15.0
            p.body_lean = 22.0
            p.rotation = -7.0
        else:
            p.root_y = 4.0 - 2.0 * abs(wave)
            p.body_lean = 18.0 * amount
        p.head_x = 2.0 * amount
        p.near_shoulder = (79.0, 57.0)
        p.near_elbow = (69.0, 65.0)
        p.near_hand = (57.0, 70.0)
        p.far_shoulder = (54.0, 58.0)
        p.far_elbow = (42.0, 63.0)
        p.far_hand = (31.0, 64.0)
        p.near_hip = (70.0, 89.0)
        p.near_knee = (82.0, 100.0)
        p.near_ankle = (94.0, 108.0)
        p.far_hip = (59.0, 89.0)
        p.far_knee = (54.0, 104.0)
        p.far_ankle = (42.0, 114.0)
        if animation == "epsilon_dash":
            p.epsilon = 0.35 + 0.65 * abs(math.sin(cyc * 2.0))
            p.field_phase = phase
    elif animation == "roll" or animation == "ledge_roll":
        p.rotation = -360.0 * t
        p.rotation_pivot = (65.0, 93.0)
        p.root_y = 9.0
        p.near_hand = (75.0, 87.0)
        p.far_hand = (57.0, 87.0)
        p.near_knee = (76.0, 98.0)
        p.near_ankle = (71.0, 106.0)
        p.far_knee = (56.0, 98.0)
        p.far_ankle = (61.0, 106.0)
    elif animation in {"wall_grab", "ledge_grab"}:
        p.root_x = 12.0
        p.body_lean = 6.0
        p.near_elbow = (86.0, 55.0)
        p.near_hand = (94.0, 47.0)
        p.far_elbow = (74.0, 58.0)
        p.far_hand = (91.0, 53.0)
        p.near_knee = (76.0, 102.0)
        p.near_ankle = (89.0, 108.0)
        p.far_knee = (59.0, 101.0)
        p.far_ankle = (83.0, 113.0)
        p.near_hand_mode = p.far_hand_mode = "grip"
    elif animation in {"wall_jump", "ledge_climb", "ledge_getup"}:
        rise = _smooth(t)
        p.root_x = 10.0 - 16.0 * rise
        p.root_y = 6.0 - 13.0 * rise
        p.body_lean = -8.0 + 14.0 * rise
        p.near_elbow = (86.0, 57.0)
        p.near_hand = (93.0, 48.0)
        p.far_elbow = (74.0, 58.0)
        p.far_hand = (91.0, 52.0)
        p.near_knee = (79.0, 100.0)
        p.near_ankle = (89.0, 110.0)
        p.far_knee = (55.0, 100.0)
        p.far_ankle = (50.0, 111.0)
        p.near_hand_mode = p.far_hand_mode = "grip"
    elif animation == "climb":
        step = 6.0 * wave
        p.root_y = -1.5 * abs(cosine)
        p.near_hand = (83.0, 53.0 + step)
        p.near_elbow = (82.0, 65.0 + step * 0.4)
        p.far_hand = (50.0, 53.0 - step)
        p.far_elbow = (49.0, 66.0 - step * 0.4)
        p.near_ankle = (78.0, 114.0 - step)
        p.far_ankle = (53.0, 114.0 + step)
        p.near_hand_mode = p.far_hand_mode = "grip"
    elif animation in {"swim", "float_glide"}:
        p.rotation = -12.0 if animation == "swim" else -5.0
        p.root_y = -3.0 + 2.0 * wave
        p.near_hand = (92.0 + 5.0 * wave, 61.0)
        p.near_elbow = (82.0, 65.0)
        p.far_hand = (40.0 - 5.0 * wave, 64.0)
        p.far_elbow = (49.0, 68.0)
        p.near_ankle = (86.0, 111.0 + 3.0 * wave)
        p.far_ankle = (44.0, 113.0 - 3.0 * wave)
        if animation == "float_glide":
            p.full_turn = 0.35
    elif animation == "block":
        p.body_lean = -4.0
        p.near_elbow = (84.0, 63.0)
        p.near_hand = (75.0, 57.0)
        p.far_elbow = (67.0, 67.0)
        p.far_hand = (74.0, 69.0)
        p.near_hand_mode = p.far_hand_mode = "open"
        p.field = 0.8
    elif animation == "hit":
        shock = _pulse(t)
        p.root_x = -7.0 * shock
        p.rotation = -8.0 * shock
        p.head_x = -2.0 * shock
        p.mouth_open = 0.65 * shock
        p.near_hand = (91.0, 78.0)
        p.far_hand = (38.0, 81.0)
    elif animation == "death":
        fall = _smooth(t)
        p.rotation = -82.0 * fall
        p.rotation_pivot = (62.0, 111.0)
        p.root_x = -6.0 * fall
        p.root_y = 9.0 * fall
        p.mouth_open = 0.45 * fall
        p.smile = 0.0
    elif animation == "talk":
        p.mouth_open = 0.15 + 0.55 * max(0.0, math.sin(cyc * 1.5))
        p.smile = 0.5
        p.brow = 1.0
        p.near_elbow = (85.0, 69.0)
        p.near_hand = (91.0, 60.0 + 3.0 * wave)
        p.near_hand_mode = "open"
        p.far_elbow = (47.0, 71.0)
        p.far_hand = (53.0, 80.0)
    elif animation == "interact":
        reach = _pulse(t)
        p.body_lean = 7.0 * reach
        p.near_elbow = (88.0, 65.0)
        p.near_hand = (99.0, 63.0)
        p.near_hand_mode = "point"
        p.far_hand = (56.0, 81.0)
    elif animation in {"jab", "punch", "prime_stride"}:
        strike = _pulse(t)
        p.body_lean = 10.0 * strike
        p.root_x = 3.0 * strike
        p.near_elbow = (86.0 + 5.0 * strike, 67.0)
        p.near_hand = (84.0 + 24.0 * strike, 68.0)
        p.near_hand_mode = "fist"
        p.far_hand = (55.0, 75.0)
        p.far_hand_mode = "fist"
        p.near_knee = (74.0 + 4.0 * strike, 102.0)
        p.near_ankle = (82.0 + 9.0 * strike, 117.0)
        if animation == "prime_stride":
            p.prime = strike
            p.field_phase = phase
    elif animation == "attack_up" or animation == "air_up":
        strike = _pulse(t)
        p.near_elbow = (82.0, 52.0)
        p.near_hand = (79.0, 34.0 - 4.0 * strike)
        p.near_hand_mode = "fist"
        p.far_hand = (54.0, 77.0)
        p.body_lean = -4.0
        p.field = 0.35 * strike
    elif animation == "attack_down" or animation == "air_down":
        strike = _pulse(t)
        p.near_elbow = (84.0, 76.0)
        p.near_hand = (87.0, 99.0 + 5.0 * strike)
        p.near_hand_mode = "fist"
        p.far_hand = (55.0, 72.0)
        p.body_lean = 7.0
    elif animation.startswith("air_"):
        p.root_y = -8.0
        p.rotation = 18.0 * wave
        p.near_hand = (90.0, 68.0)
        p.far_hand = (40.0, 70.0)
        p.near_ankle = (84.0, 109.0)
        p.far_ankle = (47.0, 110.0)
        p.field = 0.25
    elif animation == "compressed_sense":
        gather = _smooth(min(1.0, t * 1.6))
        release = _smooth(max(0.0, (t - 0.55) / 0.45))
        p.compress = gather * (1.0 - 0.45 * release)
        p.field_phase = phase
        p.body_lean = 3.0 + 8.0 * release
        p.near_elbow = (84.0, 64.0)
        p.near_hand = (92.0 + 12.0 * release, 61.0)
        p.near_hand_mode = "open"
        p.far_elbow = (48.0, 66.0)
        p.far_hand = (57.0, 62.0)
        p.far_hand_mode = "open"
    elif animation == "polymath_chain":
        p.chain = _smooth(t)
        p.field_phase = phase
        p.near_elbow = (85.0, 63.0)
        p.near_hand = (93.0, 50.0 + 5.0 * wave)
        p.near_hand_mode = "open"
        p.far_elbow = (46.0, 64.0)
        p.far_hand = (38.0, 53.0 - 5.0 * wave)
        p.far_hand_mode = "open"
        p.mouth_open = 0.25 + 0.25 * abs(wave)
    elif animation == "full_turn":
        p.full_turn = _smooth(t)
        p.field_phase = phase
        p.near_elbow = (87.0, 63.0)
        p.near_hand = (95.0, 52.0)
        p.near_hand_mode = "open"
        p.far_elbow = (44.0, 65.0)
        p.far_hand = (36.0, 57.0)
        p.far_hand_mode = "open"
        p.root_y = -2.0 * math.sin(t * math.pi)
    elif animation == "celebrate":
        lift = abs(math.sin(cyc))
        p.root_y = -7.0 * lift
        p.near_elbow = (81.0, 49.0)
        p.near_hand = (86.0, 35.0)
        p.far_elbow = (49.0, 49.0)
        p.far_hand = (44.0, 35.0)
        p.near_hand_mode = p.far_hand_mode = "open"
        p.smile = 1.0
        p.mouth_open = 0.35
        p.full_turn = 0.35 + 0.25 * lift
    elif animation == "taunt":
        p.near_elbow = (85.0, 67.0)
        p.near_hand = (91.0, 56.0)
        p.near_hand_mode = "point"
        p.far_elbow = (49.0, 68.0)
        p.far_hand = (55.0, 80.0)
        p.smile = 0.7
        p.brow = 0.7
        p.full_turn = 0.25 + 0.15 * (0.5 + 0.5 * wave)

    return p


def _transform(point: Point, pose: Pose) -> Point:
    x, y = point
    # Forward lean is a shear around the waist, not a rigid rotation; this
    # keeps the shoes planted while giving the runner silhouette momentum.
    y_rel = y - 86.0
    x += -pose.body_lean * y_rel / 75.0
    point = (x + pose.root_x, y + pose.root_y)
    return _rotate(point, pose.rotation_pivot, pose.rotation)


def _draw_leg(
    draw: ImageDraw.ImageDraw,
    pose: Pose,
    hip: Point,
    knee: Point,
    ankle: Point,
    *,
    far: bool,
) -> None:
    T = lambda q: _transform(q, pose)
    hip_t, knee_t, ankle_t = T(hip), T(knee), T(ankle)
    trouser = TROUSER_DARK if far else TROUSER
    trouser_hi = TROUSER if far else TROUSER_LIGHT
    _polygon(draw, _segment_quad(hip_t, knee_t, 5.0, 4.3), trouser, OUTLINE, 1.0)
    _polygon(draw, _segment_quad(knee_t, ankle_t, 4.2, 3.4), trouser_hi, OUTLINE, 1.0)
    _ellipse(draw, knee_t, 4.4, 3.8, trouser_hi, OUTLINE, 0.8)
    along, normal, _ = _unit(knee_t, ankle_t)
    toe = (ankle_t[0] + along[0] * 2.5 + normal[0] * 4.8, ankle_t[1] + along[1] * 2.5 + normal[1] * 4.8)
    shoe_poly = [
        (ankle_t[0] - normal[0] * 3.6, ankle_t[1] - normal[1] * 3.6),
        (ankle_t[0] + normal[0] * 3.7, ankle_t[1] + normal[1] * 3.7),
        (toe[0] + normal[0] * 3.2, toe[1] + normal[1] * 3.2),
        (toe[0] - normal[0] * 2.6, toe[1] - normal[1] * 2.6),
    ]
    _polygon(draw, shoe_poly, SHOE if not far else SHOE_DARK, OUTLINE, 1.0)
    _line(draw, [shoe_poly[2], shoe_poly[3]], SOLE, 1.8)
    if not far:
        _line(draw, [_lerp_point(ankle_t, toe, 0.35), _lerp_point(ankle_t, toe, 0.72)], TAU_GOLD, 0.8)


def _draw_tau_shirt_mark(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    chest = _transform((65.2, 61.5), pose)
    font = _font(21.0, preferred=("GentiumPlus-Italic.ttf", "LinLibertine_RI.otf", "DejaVuSerif-Italic.ttf", "DejaVuSans-Oblique.ttf"))
    # Use a real Greek tau glyph from an italic serif font. Those fonts make the
    # descender read much more clearly than the T-like sans-serif forms.
    draw.text(
        _pt(_offset(chest, 0.0, 0.15)),
        "τ",
        font=font,
        fill=(246, 241, 222, 255),
        anchor="mm",
        stroke_width=max(1, _s(1.2)),
        stroke_fill=OUTLINE,
    )
    # A second tiny fill pass thickens the glyph without changing its shape.
    draw.text(
        _pt(_offset(chest, -0.08, 0.15)),
        "τ",
        font=font,
        fill=(246, 241, 222, 255),
        anchor="mm",
    )


def _draw_neck(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    center = T((65.0 + pose.head_x, 31.0 + pose.head_y))
    neck = [
        T((60.4 + pose.head_x, 44.8 + pose.head_y)),
        T((68.7 + pose.head_x, 44.2 + pose.head_y)),
        T((69.8 + pose.head_x, 55.7 + pose.head_y)),
        T((60.7 + pose.head_x, 55.9 + pose.head_y)),
    ]
    neck = [_rotate(q, center, pose.head_tilt) for q in neck]
    _polygon(draw, neck, SKIN, OUTLINE_SOFT, 0.85)
    _line(draw, [_rotate(T((61.7 + pose.head_x, 47.3 + pose.head_y)), center, pose.head_tilt), _rotate(T((61.6 + pose.head_x, 54.0 + pose.head_y)), center, pose.head_tilt)], SKIN_SHADE, 0.65)
    _line(draw, [_rotate(T((67.7 + pose.head_x, 46.8 + pose.head_y)), center, pose.head_tilt), _rotate(T((67.7 + pose.head_x, 54.0 + pose.head_y)), center, pose.head_tilt)], SKIN_SHADE, 0.65)
    # Collar lines under the neck help connect the head to the shirt.
    _arc(draw, T((65.3, 54.8)), 5.7, 3.4, 194, 346, OUTLINE_SOFT, 0.95)
    _arc(draw, T((65.3, 55.2)), 4.9, 2.8, 196, 344, SHIRT_SHADE, 0.75)


def _draw_torso(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    jacket = [
        T((52.0, 54.0)),
        T((61.0, 49.0)),
        T((70.0, 49.0)),
        T((80.0, 54.0)),
        T((83.0, 72.0)),
        T((77.0, 89.0)),
        T((66.0, 92.0)),
        T((54.0, 88.0)),
        T((48.0, 71.0)),
    ]
    _polygon(draw, jacket, JACKET_DARK, OUTLINE, 1.2)
    # Asymmetric short jacket: near panel is bright and cut higher, creating a
    # runner/courier silhouette instead of a suit coat or academic robe.
    near_panel = [T((68.0, 51.2)), T((78.0, 55.0)), T((81.0, 71.0)), T((74.0, 86.0)), T((67.1, 90.0))]
    far_panel = [T((53.0, 55.0)), T((61.9, 51.2)), T((62.8, 90.0)), T((55.0, 85.0)), T((50.0, 70.0))]
    _polygon(draw, far_panel, JACKET, OUTLINE_SOFT, 0.7)
    _polygon(draw, near_panel, JACKET_LIGHT, OUTLINE_SOFT, 0.7)
    # Open jacket over a dark crew-neck tee, with a bold tau mark that stays
    # legible from sprite scale.
    shirt = [T((57.1, 52.8)), T((73.1, 52.8)), T((74.0, 65.0)), T((66.7, 73.0)), T((56.3, 65.4))]
    _polygon(draw, shirt, SHIRT, OUTLINE_SOFT, 0.7)
    _ellipse(draw, T((65.2, 54.1)), 5.6, 2.8, SHIRT, None, 0.0)
    _arc(draw, T((65.2, 55.2)), 6.0, 3.6, 198, 342, SHIRT_SHADE, 1.0)
    _draw_tau_shirt_mark(draw, pose)
    _line(draw, [T((65.0, 52.4)), T((65.0, 89.0))], JACKET_DEEP, 0.8)
    # Short sleeves and shoulder caps keep both arms visually attached.
    _ellipse(draw, T((52.5, 56.0)), 6.0, 5.3, JACKET, OUTLINE, 0.9)
    _ellipse(draw, T((78.0, 55.5)), 6.2, 5.4, JACKET, OUTLINE, 0.9)


def _draw_arm(
    draw: ImageDraw.ImageDraw,
    pose: Pose,
    shoulder: Point,
    elbow: Point,
    hand: Point,
    mode: str,
    *,
    far: bool,
) -> None:
    T = lambda q: _transform(q, pose)
    shoulder_t, elbow_t, hand_t = T(shoulder), T(elbow), T(hand)
    # For the mostly front-facing hall sprite, both arms should read as the same
    # body rather than one near arm and one deeply shadowed far arm.
    skin = SKIN_LIGHT
    sleeve = JACKET
    along, _, length = _unit(elbow_t, hand_t)
    wrist = (hand_t[0] - along[0] * min(3.0, length * 0.28), hand_t[1] - along[1] * min(3.0, length * 0.28))
    upper_end = _lerp_point(shoulder_t, elbow_t, 0.58)
    _polygon(draw, _segment_quad(shoulder_t, upper_end, 5.0, 4.0), sleeve, OUTLINE, 0.95)
    _polygon(draw, _segment_quad(upper_end, elbow_t, 4.0, 3.6), skin, OUTLINE, 0.9)
    _polygon(draw, _segment_quad(elbow_t, wrist, 3.6, 2.8), skin, OUTLINE, 0.9)
    _ellipse(draw, elbow_t, 3.7, 3.3, skin, OUTLINE, 0.75)
    _draw_hand(draw, wrist, hand_t, mode, skin)


def _draw_hand(draw: ImageDraw.ImageDraw, wrist: Point, hand: Point, mode: str, skin: RGBA) -> None:
    along, normal, _ = _unit(wrist, hand)
    rx = 3.5 if mode == "open" else 3.0
    _ellipse(draw, hand, rx, 2.8, skin, OUTLINE, 0.8)
    if mode == "open":
        for offset in (-1.4, -0.45, 0.45, 1.4):
            start = (hand[0] + along[0] * 1.1 + normal[0] * offset, hand[1] + along[1] * 1.1 + normal[1] * offset)
            end = (start[0] + along[0] * (2.8 - abs(offset) * 0.2), start[1] + along[1] * (2.8 - abs(offset) * 0.2))
            _line(draw, [start, end], OUTLINE, 1.4)
            _line(draw, [start, end], skin, 0.75)
    elif mode == "point":
        start = (hand[0] + along[0] * 1.4, hand[1] + along[1] * 1.4)
        end = (hand[0] + along[0] * 5.5, hand[1] + along[1] * 5.5)
        _line(draw, [start, end], OUTLINE, 1.6)
        _line(draw, [start, end], skin, 0.85)
    elif mode == "grip":
        _line(draw, [hand, (hand[0] + normal[0] * 3.0, hand[1] + normal[1] * 3.0)], OUTLINE, 1.4)
    elif mode == "fist":
        _line(draw, [(hand[0] - normal[0] * 1.8, hand[1] - normal[1] * 1.8), (hand[0] + normal[0] * 1.8, hand[1] + normal[1] * 1.8)], SKIN_SHADE, 0.8)


def _draw_head(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    base = (65.0 + pose.head_x, 31.0 + pose.head_y)
    T = lambda q: _transform(q, pose)
    center = T(base)
    _draw_neck(draw, pose)
    # Ear behind head, then a tapered three-quarter face.
    _ellipse(draw, T((51.8 + pose.head_x, 32.0 + pose.head_y)), 3.8, 5.7, SKIN, OUTLINE, 0.8)
    face = [
        T((53.0 + pose.head_x, 20.0 + pose.head_y)),
        T((64.0 + pose.head_x, 15.5 + pose.head_y)),
        T((76.0 + pose.head_x, 20.0 + pose.head_y)),
        T((79.0 + pose.head_x, 31.0 + pose.head_y)),
        T((75.0 + pose.head_x, 43.0 + pose.head_y)),
        T((65.0 + pose.head_x, 47.0 + pose.head_y)),
        T((55.0 + pose.head_x, 41.0 + pose.head_y)),
        T((51.5 + pose.head_x, 30.0 + pose.head_y)),
    ]
    face = [_rotate(q, center, pose.head_tilt) for q in face]
    _polygon(draw, face, SKIN, OUTLINE, 1.2)
    # Side-swept hair is a connected cap with one long diagonal fringe.
    hair = [
        T((51.5 + pose.head_x, 29.0 + pose.head_y)),
        T((52.0 + pose.head_x, 20.0 + pose.head_y)),
        T((59.0 + pose.head_x, 13.0 + pose.head_y)),
        T((72.0 + pose.head_x, 13.5 + pose.head_y)),
        T((80.0 + pose.head_x, 20.0 + pose.head_y)),
        T((78.5 + pose.head_x, 27.0 + pose.head_y)),
        T((72.0 + pose.head_x, 22.5 + pose.head_y)),
        T((63.0 + pose.head_x, 27.0 + pose.head_y)),
        T((55.0 + pose.head_x, 31.5 + pose.head_y)),
    ]
    hair = [_rotate(q, center, pose.head_tilt) for q in hair]
    _polygon(draw, hair, HAIR, OUTLINE, 1.1)
    _line(draw, [_rotate(T((57.0 + pose.head_x, 18.0 + pose.head_y)), center, pose.head_tilt), _rotate(T((71.5 + pose.head_x, 17.0 + pose.head_y)), center, pose.head_tilt)], HAIR_GLEAM, 1.1)
    _line(draw, [_rotate(T((62.0 + pose.head_x, 21.0 + pose.head_y)), center, pose.head_tilt), _rotate(T((75.0 + pose.head_x, 18.5 + pose.head_y)), center, pose.head_tilt)], HAIR_MID, 1.0)

    # Rectangular glasses are the primary face read at hall scale.
    left = _rotate(T((59.0 + pose.head_x, 30.5 + pose.head_y)), center, pose.head_tilt)
    right = _rotate(T((70.5 + pose.head_x, 30.2 + pose.head_y)), center, pose.head_tilt)
    for eye_center, far in ((left, True), (right, False)):
        rx = 5.1 if not far else 4.7
        draw.rounded_rectangle(
            _bbox(eye_center, rx, 3.4),
            radius=_s(1.2),
            fill=GLASS,
            outline=OUTLINE_SOFT,
            width=_s(0.9),
        )
        if pose.blink:
            _line(draw, [_offset(eye_center, -2.3, 0.2), _offset(eye_center, 2.3, 0.0)], EYE, 1.0)
        else:
            _ellipse(draw, _offset(eye_center, 0.7, 0.4), 1.15, 1.4, EYE, None, 0.0)
            _ellipse(draw, _offset(eye_center, 1.0, 0.0), 0.35, 0.35, TAU_LIGHT, None, 0.0)
    _line(draw, [_offset(left, 4.7, -0.2), _offset(right, -5.0, -0.2)], OUTLINE_SOFT, 0.9)
    _line(draw, [_offset(left, -4.6, -0.2), _offset(left, -8.5, -1.3)], OUTLINE_SOFT, 0.8)
    _line(draw, [_offset(right, 4.8, -0.2), _offset(right, 7.4, -1.0)], OUTLINE_SOFT, 0.8)

    # Narrow nose and understated, friendly mouth.
    nose = _rotate(T((72.8 + pose.head_x, 35.0 + pose.head_y)), center, pose.head_tilt)
    _line(draw, [_offset(nose, -0.9, -3.0), nose, _offset(nose, -1.6, 0.8)], SKIN_SHADE, 0.8)
    mouth = _rotate(T((67.8 + pose.head_x, 40.2 + pose.head_y)), center, pose.head_tilt)
    if pose.mouth_open > 0.14:
        _ellipse(draw, mouth, 3.5, 0.8 + 1.5 * pose.mouth_open, MOUTH, OUTLINE_SOFT, 0.55)
        if pose.smile > 0.35:
            _line(draw, [_offset(mouth, -2.2, -0.2), _offset(mouth, 2.2, -0.2)], SKIN_LIGHT, 0.55)
    else:
        lift = 0.8 * pose.smile
        _line(draw, [_offset(mouth, -3.0, -0.1), mouth, _offset(mouth, 3.0, -lift)], MOUTH, 0.9)
    if pose.brow > 0.0:
        _line(draw, [_offset(left, -2.8, -5.2 - pose.brow), _offset(left, 2.8, -5.8 - pose.brow)], HAIR, 0.9)
        _line(draw, [_offset(right, -2.8, -5.6 - pose.brow), _offset(right, 2.8, -5.0 - pose.brow)], HAIR, 0.9)


def _draw_ability_effects_behind(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    if pose.full_turn > 0.02:
        center = T((65.0, 70.0))
        progress = 45.0 + 315.0 * pose.full_turn
        _arc(draw, center, 31.0, 38.0, -90.0, -90.0 + progress, _fade(TAU_GOLD, 0.75), 2.2)
        _arc(draw, center, 27.5, 34.0, -90.0, -90.0 + progress * 0.84, _fade(TAU_LIGHT, 0.42), 0.9)
        angle = math.radians(-90.0 + progress)
        marker = (center[0] + 31.0 * math.cos(angle), center[1] + 38.0 * math.sin(angle))
        _ellipse(draw, marker, 2.4, 2.4, TAU_LIGHT, OUTLINE_SOFT, 0.5)
    if pose.epsilon > 0.02:
        # Several tiny gains behind the dash, each smaller than the last.
        for idx in range(4):
            amount = pose.epsilon * (1.0 - idx * 0.16)
            center = T((44.0 - idx * 9.0, 75.0 + (idx % 2) * 2.0))
            _arc(draw, center, 6.0 - idx * 0.7, 10.0 - idx * 0.8, 92, 268, _fade(FIELD, amount * 0.75), 1.4)
    if pose.prime > 0.02:
        # Unevenly spaced points (2, 3, 5, 7 offsets) tethered to the strike path.
        hand = T(pose.near_hand)
        for idx, gap in enumerate((2.0, 5.0, 10.0, 17.0)):
            center = (hand[0] - gap * 1.45, hand[1] + math.sin(idx * 1.7) * 3.0)
            _ellipse(draw, center, 1.6 + 0.2 * idx, 1.6 + 0.2 * idx, _fade(TAU_GOLD, pose.prime), None, 0.0)
            if idx:
                prev_gap = (2.0, 5.0, 10.0, 17.0)[idx - 1]
                prev = (hand[0] - prev_gap * 1.45, hand[1] + math.sin((idx - 1) * 1.7) * 3.0)
                _line(draw, [prev, center], _fade(TAU_LIGHT, pose.prime * 0.55), 0.75)
    if pose.compress > 0.02:
        center = T((75.0, 62.0))
        for idx in range(4):
            radius = _lerp(26.0 - idx * 4.5, 6.0 + idx * 1.0, pose.compress)
            _arc(draw, center, radius, radius * 0.82, 160, 380, _fade(FIELD, 0.26 + idx * 0.12), 1.1)
    if pose.chain > 0.02:
        # Three contributor nodes join at the chest before the combined line
        # exits through the near hand.  They are effects, not held objects.
        chest = T((65.0, 67.0))
        nodes = [T((42.0, 48.0)), T((65.0, 39.0)), T((88.0, 47.0))]
        colors = [LEMMA_BLUE, LEMMA_PINK, LEMMA_GREEN]
        for node, color in zip(nodes, colors):
            progress = pose.chain
            end = _lerp_point(node, chest, progress)
            _line(draw, [node, end], _fade(color, 0.8), 1.2)
            _ellipse(draw, node, 2.6, 2.6, _fade(color, 0.9), OUTLINE_SOFT, 0.45)
        if pose.chain > 0.55:
            out = T(pose.near_hand)
            _line(draw, [chest, out], _fade(TAU_LIGHT, (pose.chain - 0.55) / 0.45), 2.0)


def _draw_ability_effects_front(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    if pose.field > 0.02:
        center = T((76.0, 64.0))
        _arc(draw, center, 18.0, 25.0, 110, 250, _fade(FIELD, pose.field), 2.4)
        _arc(draw, center, 14.0, 20.0, 110, 250, _fade(TAU_LIGHT, pose.field * 0.55), 0.9)
    if pose.compress > 0.45:
        hand = T(pose.near_hand)
        release = (pose.compress - 0.45) / 0.55
        _line(draw, [hand, (hand[0] + 22.0 * release, hand[1] - 1.5)], _fade(TAU_LIGHT, release), 2.6)
        _line(draw, [hand, (hand[0] + 28.0 * release, hand[1] + 2.0)], _fade(FIELD, release * 0.75), 1.0)


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose(animation, frame_idx, nframes)
    image = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")

    _draw_ability_effects_behind(draw, pose)
    _draw_leg(draw, pose, pose.far_hip, pose.far_knee, pose.far_ankle, far=True)
    _draw_leg(draw, pose, pose.near_hip, pose.near_knee, pose.near_ankle, far=False)
    _draw_torso(draw, pose)
    _draw_arm(draw, pose, pose.far_shoulder, pose.far_elbow, pose.far_hand, pose.far_hand_mode, far=True)
    _draw_arm(draw, pose, pose.near_shoulder, pose.near_elbow, pose.near_hand, pose.near_hand_mode, far=False)
    _draw_ability_effects_front(draw, pose)
    _draw_head(draw, pose)

    return image.resize((FRAME_W, FRAME_H), Image.Resampling.LANCZOS)


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {
            "x": int(fw * 0.24),
            "y": int(fh * 0.09),
            "w": int(fw * 0.55),
            "h": int(fh * 0.85),
        },
        "feet_pixel": {"x": fw * 0.51, "y": fh * 0.925},
        "feet_anchor_norm": {"x": 0.01, "y": round(0.5 - 0.925, 6)},
    }


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        label_width=108,
        auto_crop=False,
        body_metrics_fn=_body_metrics_override,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.0, "frame_sample_inset": 1},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        trim=False,
        attack_hitboxes={
            "prime_stride": {"bbox": {"x": 74, "y": 48, "w": 50, "h": 40}},
            "compressed_sense": {"bbox": {"x": 82, "y": 42, "w": 44, "h": 43}},
            "full_turn": {"bbox": {"x": 24, "y": 25, "w": 82, "h": 86}},
        },
    )
    keys = (
        "spritesheet",
        "yaml",
        "ron",
        "actor",
        "canonical",
        "canonical_transparent",
        "preview",
    )
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        render_frame,
        Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir", nargs="?", type=Path, default=Path("generated") / TARGET_NAME)
    args = parser.parse_args(argv)
    outputs = render(args.out_dir)
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
