"""Procedural full-action renderer for Davy Hylbert.

Davy Hylbert is a playful David Hilbert parody: a confident early-modern
mathematical showman with a formal waistcoat, tidy moustache, round spectacles,
and a signature dark homburg hat that always reads clearly even at sprite scale.
He should feel instantly distinct from the newer casual mathematicians in the
hall: upright, sharply tailored, a little theatrical, and impossible to mistake
for anyone who forgot his hat.

The silhouette is built around that hat and a broad-shouldered frock coat over a
warm ivory waistcoat. The ability language nods to Hilbert space, the infinite
hotel, and the habit of turning a disorderly universe into numbered rooms and
clean orthogonal structure. There are no held props, no floor ellipses, and no
drop shadows; every effect remains tethered to the body.

Painter order remains deliberate: legs -> torso -> both arms -> integrated
ability marks -> head, so both arms stay in front of the coat while the hat and
face remain the dominant read.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ...authoring.sheet_build import build_sheet, write_canonical

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "davy_hylbert"
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
    "actor": {"character_id": "npc_davy_hylbert", "display_name": "Davy Hylbert"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "mathematician",
            "axiomatic_showman",
            "infinite_hotel",
            "playable_candidate",
        ],
        "locomotion_hint": "Walk",
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
        "axiomatic_showman",
        "infinite_hotel",
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

OUTLINE = (20, 18, 22, 255)
OUTLINE_SOFT = (51, 45, 49, 255)
SKIN = (214, 174, 142, 255)
SKIN_LIGHT = (236, 202, 172, 255)
SKIN_SHADE = (170, 129, 104, 255)
HAIR = (81, 71, 63, 255)
HAIR_MID = (116, 103, 92, 255)
HAIR_GLEAM = (153, 138, 123, 255)
COAT = (58, 64, 83, 255)
COAT_LIGHT = (88, 96, 122, 255)
COAT_DARK = (39, 43, 57, 255)
COAT_DEEP = (26, 28, 39, 255)
WAISTCOAT = (224, 215, 190, 255)
WAISTCOAT_SHADE = (188, 177, 149, 255)
TROUSER = (54, 54, 67, 255)
TROUSER_LIGHT = (82, 82, 100, 255)
TROUSER_DARK = (34, 34, 44, 255)
SHOE = (95, 67, 42, 255)
SHOE_DARK = (53, 35, 24, 255)
SOLE = (26, 24, 28, 255)
GLASS = (244, 240, 225, 52)
EYE = (27, 22, 20, 255)
MOUTH = (126, 77, 68, 255)
HILBERT_GOLD = (226, 184, 83, 255)
HILBERT_LIGHT = (250, 229, 164, 255)
HAT_STRAW = (236, 230, 212, 255)
HAT_STRAW_LIGHT = (250, 246, 234, 255)
HAT_STRAW_SHADE = (198, 188, 166, 255)
HAT_BAND = (41, 43, 55, 255)
COLLAR = (246, 242, 235, 255)
COLLAR_SHADE = (213, 205, 194, 255)
ROOM_BLUE = (123, 183, 231, 255)
ROOM_RED = (201, 102, 108, 255)
ROOM_GREEN = (132, 180, 128, 255)
FIELD = (173, 211, 226, 255)


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
        _line(draw, [_lerp_point(ankle_t, toe, 0.35), _lerp_point(ankle_t, toe, 0.72)], HILBERT_GOLD, 0.8)


def _draw_tau_shirt_mark(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    chest = T((65.1, 63.4))
    for y in (57.2, 63.0, 68.8):
        _ellipse(draw, T((65.1, y)), 1.25, 1.25, HILBERT_GOLD, OUTLINE_SOFT, 0.5)
    font = _font(
        10.8,
        preferred=("DejaVuSerif-Italic.ttf", "DejaVuSerif.ttf", "DejaVuSans.ttf"),
    )
    draw.text(
        _pt(_offset(chest, 0.0, 8.4)),
        "H",
        font=font,
        fill=(88, 64, 42, 255),
        anchor="mm",
        stroke_width=max(1, _s(0.8)),
        stroke_fill=WAISTCOAT,
    )


def _draw_neck(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    center = T((65.0 + pose.head_x, 34.0 + pose.head_y))
    neck = [
        T((60.7 + pose.head_x, 47.5 + pose.head_y)),
        T((69.3 + pose.head_x, 47.1 + pose.head_y)),
        T((70.0 + pose.head_x, 58.5 + pose.head_y)),
        T((60.4 + pose.head_x, 58.7 + pose.head_y)),
    ]
    neck = [_rotate(q, center, pose.head_tilt) for q in neck]
    _polygon(draw, neck, SKIN, OUTLINE_SOFT, 0.85)
    _line(draw, [_rotate(T((62.0 + pose.head_x, 49.7 + pose.head_y)), center, pose.head_tilt), _rotate(T((62.0 + pose.head_x, 56.6 + pose.head_y)), center, pose.head_tilt)], SKIN_SHADE, 0.6)
    _line(draw, [_rotate(T((68.0 + pose.head_x, 49.4 + pose.head_y)), center, pose.head_tilt), _rotate(T((68.0 + pose.head_x, 56.6 + pose.head_y)), center, pose.head_tilt)], SKIN_SHADE, 0.6)
    _arc(draw, T((65.0, 58.0)), 6.4, 3.6, 196, 344, OUTLINE_SOFT, 0.9)
    _arc(draw, T((65.0, 58.5)), 5.4, 3.0, 198, 342, WAISTCOAT_SHADE, 0.75)


def _draw_torso(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    coat = [
        T((51.2, 55.5)),
        T((60.8, 50.8)),
        T((69.8, 50.3)),
        T((79.4, 55.1)),
        T((82.8, 71.8)),
        T((81.8, 88.8)),
        T((73.0, 96.2)),
        T((57.8, 95.7)),
        T((49.6, 87.9)),
        T((48.6, 71.1)),
    ]
    _polygon(draw, coat, COAT_DARK, OUTLINE, 1.2)
    left_panel = [T((52.2, 56.1)), T((61.7, 51.5)), T((63.2, 91.6)), T((57.2, 93.3)), T((50.5, 74.2))]
    right_panel = [T((68.3, 50.9)), T((78.5, 55.7)), T((81.2, 73.4)), T((78.2, 92.7)), T((69.1, 94.4))]
    _polygon(draw, left_panel, COAT, OUTLINE_SOFT, 0.7)
    _polygon(draw, right_panel, COAT_LIGHT, OUTLINE_SOFT, 0.7)

    waistcoat = [T((58.0, 55.2)), T((72.0, 55.2)), T((74.1, 66.3)), T((70.0, 88.6)), T((60.1, 88.9)), T((56.2, 66.3))]
    _polygon(draw, waistcoat, WAISTCOAT, OUTLINE_SOFT, 0.65)
    left_lapel = [T((58.2, 54.9)), T((63.6, 56.1)), T((60.8, 68.6)), T((55.8, 63.8))]
    right_lapel = [T((66.2, 56.0)), T((71.9, 55.0)), T((74.5, 63.9)), T((69.2, 68.7))]
    _polygon(draw, left_lapel, COAT_DEEP, OUTLINE_SOFT, 0.55)
    _polygon(draw, right_lapel, COAT_DEEP, OUTLINE_SOFT, 0.55)

    collar_left = [T((60.9, 51.9)), T((64.5, 55.6)), T((61.7, 58.5)), T((57.8, 54.2))]
    collar_right = [T((65.7, 55.6)), T((69.3, 51.8)), T((72.4, 54.4)), T((68.2, 58.6))]
    _polygon(draw, collar_left, COLLAR, OUTLINE_SOFT, 0.5)
    _polygon(draw, collar_right, COLLAR, OUTLINE_SOFT, 0.5)

    tie = [T((63.8, 56.5)), T((66.2, 56.5)), T((67.1, 63.8)), T((65.0, 74.4)), T((62.9, 63.8))]
    knot = [T((62.7, 55.0)), T((67.3, 55.0)), T((65.0, 58.4))]
    _polygon(draw, tie, ROOM_RED, OUTLINE_SOFT, 0.5)
    _polygon(draw, knot, ROOM_RED, OUTLINE_SOFT, 0.5)

    _draw_tau_shirt_mark(draw, pose)
    for y in (61.8, 67.6, 73.3, 79.1):
        _ellipse(draw, T((65.0, y)), 1.15, 1.15, HILBERT_GOLD, OUTLINE_SOFT, 0.4)

    _line(draw, [T((56.0, 89.3)), T((63.7, 80.4))], COAT_DEEP, 0.65)
    _line(draw, [T((74.0, 89.3)), T((66.4, 80.4))], COAT_DEEP, 0.65)
    _line(draw, [T((57.2, 76.4)), T((50.5, 83.8))], COAT_LIGHT, 0.65)
    _line(draw, [T((72.9, 76.4)), T((79.6, 83.8))], COAT, 0.65)


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
    sleeve = COAT if far else COAT_LIGHT
    cuff = COLLAR
    along, _, length = _unit(elbow_t, hand_t)
    wrist = (hand_t[0] - along[0] * min(3.2, length * 0.30), hand_t[1] - along[1] * min(3.2, length * 0.30))
    upper_end = _lerp_point(shoulder_t, elbow_t, 0.54)
    _polygon(draw, _segment_quad(shoulder_t, upper_end, 5.2, 4.5), sleeve, OUTLINE, 0.95)
    _polygon(draw, _segment_quad(upper_end, elbow_t, 4.5, 4.0), sleeve, OUTLINE, 0.95)
    _polygon(draw, _segment_quad(elbow_t, wrist, 4.0, 3.4), sleeve, OUTLINE, 0.9)
    _ellipse(draw, elbow_t, 3.4, 3.1, sleeve, OUTLINE, 0.75)
    cuff_center = _lerp_point(wrist, hand_t, 0.32)
    _polygon(draw, _segment_quad(wrist, cuff_center, 3.1, 2.8), cuff, OUTLINE_SOFT, 0.6)
    _draw_hand(draw, cuff_center, hand_t, mode, SKIN_LIGHT)


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
    base = (65.0 + pose.head_x, 34.0 + pose.head_y)
    T = lambda q: _transform(q, pose)
    center = T(base)
    _draw_neck(draw, pose)

    ear = _rotate(T((52.0 + pose.head_x, 34.8 + pose.head_y)), center, pose.head_tilt)
    _ellipse(draw, ear, 3.8, 5.4, SKIN, OUTLINE, 0.8)
    face = [
        T((54.0 + pose.head_x, 22.3 + pose.head_y)),
        T((62.6 + pose.head_x, 18.6 + pose.head_y)),
        T((71.7 + pose.head_x, 19.3 + pose.head_y)),
        T((77.5 + pose.head_x, 24.8 + pose.head_y)),
        T((78.7 + pose.head_x, 35.8 + pose.head_y)),
        T((75.1 + pose.head_x, 47.4 + pose.head_y)),
        T((65.2 + pose.head_x, 52.2 + pose.head_y)),
        T((56.0 + pose.head_x, 47.9 + pose.head_y)),
        T((52.0 + pose.head_x, 37.0 + pose.head_y)),
    ]
    face = [_rotate(q, center, pose.head_tilt) for q in face]
    _polygon(draw, face, SKIN, OUTLINE, 1.2)

    side_hair = [
        T((53.2 + pose.head_x, 28.8 + pose.head_y)),
        T((54.8 + pose.head_x, 23.4 + pose.head_y)),
        T((59.8 + pose.head_x, 20.0 + pose.head_y)),
        T((59.6 + pose.head_x, 26.7 + pose.head_y)),
        T((55.7 + pose.head_x, 33.0 + pose.head_y)),
    ]
    side_hair = [_rotate(q, center, pose.head_tilt) for q in side_hair]
    _polygon(draw, side_hair, HAIR, OUTLINE_SOFT, 0.7)
    _line(draw, [_rotate(T((73.6 + pose.head_x, 22.3 + pose.head_y)), center, pose.head_tilt), _rotate(T((76.7 + pose.head_x, 28.7 + pose.head_y)), center, pose.head_tilt)], HAIR, 0.7)

    brim = [
        T((43.8 + pose.head_x, 21.6 + pose.head_y)),
        T((51.3 + pose.head_x, 17.4 + pose.head_y)),
        T((64.8 + pose.head_x, 15.8 + pose.head_y)),
        T((78.7 + pose.head_x, 17.3 + pose.head_y)),
        T((86.0 + pose.head_x, 20.8 + pose.head_y)),
        T((81.7 + pose.head_x, 26.0 + pose.head_y)),
        T((68.6 + pose.head_x, 24.2 + pose.head_y)),
        T((58.2 + pose.head_x, 24.8 + pose.head_y)),
        T((45.8 + pose.head_x, 24.2 + pose.head_y)),
    ]
    crown = [
        T((54.8 + pose.head_x, 18.0 + pose.head_y)),
        T((56.5 + pose.head_x, 8.2 + pose.head_y)),
        T((69.8 + pose.head_x, 7.3 + pose.head_y)),
        T((76.1 + pose.head_x, 10.6 + pose.head_y)),
        T((77.1 + pose.head_x, 18.6 + pose.head_y)),
    ]
    band = [
        T((55.1 + pose.head_x, 14.0 + pose.head_y)),
        T((76.8 + pose.head_x, 14.4 + pose.head_y)),
        T((76.7 + pose.head_x, 18.0 + pose.head_y)),
        T((55.0 + pose.head_x, 17.8 + pose.head_y)),
    ]
    brim_rot = [_rotate(q, center, pose.head_tilt) for q in brim]
    crown_rot = [_rotate(q, center, pose.head_tilt) for q in crown]
    band_rot = [_rotate(q, center, pose.head_tilt) for q in band]
    _polygon(draw, brim_rot, HAT_STRAW, OUTLINE, 1.1)
    _polygon(draw, crown_rot, HAT_STRAW, OUTLINE, 1.05)
    _polygon(draw, band_rot, HAT_BAND, OUTLINE_SOFT, 0.7)
    _line(draw, [_rotate(T((58.1 + pose.head_x, 9.7 + pose.head_y)), center, pose.head_tilt), _rotate(T((71.2 + pose.head_x, 9.4 + pose.head_y)), center, pose.head_tilt)], HAT_STRAW_LIGHT, 0.95)
    _line(draw, [_rotate(T((47.5 + pose.head_x, 22.7 + pose.head_y)), center, pose.head_tilt), _rotate(T((80.7 + pose.head_x, 22.7 + pose.head_y)), center, pose.head_tilt)], HAT_STRAW_SHADE, 0.55)

    brow_y = -0.4 - pose.brow * 0.7
    left_eye = _rotate(T((60.3 + pose.head_x, 34.1 + pose.head_y)), center, pose.head_tilt)
    right_eye = _rotate(T((70.4 + pose.head_x, 33.4 + pose.head_y)), center, pose.head_tilt)
    for eye_center, rx in ((left_eye, 3.55), (right_eye, 3.65)):
        _ellipse(draw, eye_center, rx, 3.25, GLASS, OUTLINE_SOFT, 0.82)
        if pose.blink:
            _line(draw, [_offset(eye_center, -1.9, -0.1), _offset(eye_center, 1.9, -0.2)], EYE, 0.9)
        else:
            _line(draw, [_offset(eye_center, -1.8, -0.6), _offset(eye_center, 1.8, -0.8)], HAIR_MID, 0.55)
            _line(draw, [_offset(eye_center, -1.7, 0.85), _offset(eye_center, 1.5, 0.55)], SKIN_SHADE, 0.42)
            _ellipse(draw, _offset(eye_center, 0.25, 0.25), 0.72, 0.82, EYE, None, 0.0)
            _ellipse(draw, _offset(eye_center, 0.55, -0.02), 0.18, 0.18, HAT_STRAW_LIGHT, None, 0.0)
    _line(draw, [_offset(left_eye, 3.25, -0.05), _offset(right_eye, -3.3, -0.15)], OUTLINE_SOFT, 0.72)
    _line(draw, [_offset(left_eye, -2.5, brow_y - 3.8), _offset(left_eye, 2.3, brow_y - 4.3)], HAIR, 0.85)
    _line(draw, [_offset(right_eye, -2.5, brow_y - 4.2), _offset(right_eye, 2.5, brow_y - 3.9)], HAIR, 0.85)

    nose_top = _rotate(T((67.7 + pose.head_x, 35.7 + pose.head_y)), center, pose.head_tilt)
    nose_tip = _rotate(T((68.3 + pose.head_x, 40.0 + pose.head_y)), center, pose.head_tilt)
    _line(draw, [nose_top, nose_tip, _offset(nose_tip, -1.2, 0.9)], SKIN_SHADE, 0.75)

    moustache_left = [
        _rotate(T((61.0 + pose.head_x, 41.8 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((64.8 + pose.head_x, 41.0 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((66.0 + pose.head_x, 42.4 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((63.3 + pose.head_x, 43.5 + pose.head_y)), center, pose.head_tilt),
    ]
    moustache_right = [
        _rotate(T((66.0 + pose.head_x, 42.4 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((68.8 + pose.head_x, 41.0 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((72.7 + pose.head_x, 41.8 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((68.7 + pose.head_x, 43.5 + pose.head_y)), center, pose.head_tilt),
    ]
    beard = [
        _rotate(T((61.3 + pose.head_x, 43.3 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((69.0 + pose.head_x, 43.3 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((72.2 + pose.head_x, 46.4 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((69.1 + pose.head_x, 51.0 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((65.2 + pose.head_x, 53.4 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((61.0 + pose.head_x, 50.6 + pose.head_y)), center, pose.head_tilt),
        _rotate(T((58.9 + pose.head_x, 46.2 + pose.head_y)), center, pose.head_tilt),
    ]
    _polygon(draw, moustache_left, HAIR_MID, OUTLINE_SOFT, 0.35)
    _polygon(draw, moustache_right, HAIR_MID, OUTLINE_SOFT, 0.35)
    _polygon(draw, beard, HAIR_GLEAM, OUTLINE_SOFT, 0.45)
    _line(draw, [_rotate(T((65.1 + pose.head_x, 44.1 + pose.head_y)), center, pose.head_tilt), _rotate(T((65.1 + pose.head_x, 51.5 + pose.head_y)), center, pose.head_tilt)], HAIR, 0.45)
    mouth = _rotate(T((65.3 + pose.head_x, 46.5 + pose.head_y)), center, pose.head_tilt)
    if pose.mouth_open > 0.14:
        _ellipse(draw, mouth, 2.4, 0.7 + 1.25 * pose.mouth_open, MOUTH, OUTLINE_SOFT, 0.45)
    else:
        _line(draw, [_offset(mouth, -1.8, 0.05), mouth, _offset(mouth, 1.9, -0.25 - 0.55 * pose.smile)], MOUTH, 0.75)


def _draw_ability_effects_behind(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    if pose.full_turn > 0.02:
        center = T((65.0, 69.0))
        progress = 55.0 + 300.0 * pose.full_turn
        _arc(draw, center, 31.0, 36.0, -88.0, -88.0 + progress, _fade(HILBERT_GOLD, 0.78), 2.2)
        _arc(draw, center, 27.0, 32.0, -88.0, -88.0 + progress * 0.84, _fade(HILBERT_LIGHT, 0.48), 0.9)
        for idx, room in enumerate((1, 2, 3, 4)):
            angle = math.radians(-78.0 + progress * (0.18 + idx * 0.17))
            pos = (center[0] + math.cos(angle) * (22.0 + idx * 2.0), center[1] + math.sin(angle) * (26.0 + idx * 1.8))
            _ellipse(draw, pos, 4.4, 3.6, _fade(COAT_DARK, 0.72), HILBERT_GOLD, 0.55)
            font = _font(6.6, preferred=("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"))
            draw.text(_pt(_offset(pos, 0.0, -0.1)), str(room), font=font, fill=_fade(HILBERT_LIGHT, 0.95), anchor="mm")
    if pose.field > 0.02:
        center = T((65.0, 63.0))
        for idx in range(3):
            _arc(draw, center, 18.0 + idx * 5.2, 12.0 + idx * 4.4, 205, 335, _fade(FIELD, pose.field * (0.55 + idx * 0.12)), 1.0 + idx * 0.25)
    if pose.prime > 0.03:
        hand = T(pose.near_hand)
        for idx, offset in enumerate((2.0, 7.0, 13.5, 21.0)):
            room = (hand[0] - offset * 1.25, hand[1] + math.sin(idx * 1.9) * 3.0)
            _ellipse(draw, room, 3.4, 2.8, _fade(ROOM_BLUE if idx % 2 == 0 else ROOM_GREEN, pose.prime * 0.9), HILBERT_LIGHT, 0.45)
    if pose.compress > 0.02:
        center = T((75.0, 62.0))
        for idx in range(4):
            radius = _lerp(24.0 - idx * 4.0, 7.0 + idx * 1.0, pose.compress)
            _arc(draw, center, radius, radius * 0.84, 160, 380, _fade(FIELD, 0.28 + idx * 0.12), 1.05)
    if pose.chain > 0.02:
        chest = T((65.0, 67.0))
        nodes = [T((42.0, 47.0)), T((65.0, 38.0)), T((88.0, 47.0))]
        colors = [ROOM_BLUE, ROOM_RED, ROOM_GREEN]
        for idx, (node, color) in enumerate(zip(nodes, colors), start=1):
            end = _lerp_point(node, chest, pose.chain)
            _line(draw, [node, end], _fade(color, 0.82), 1.2)
            _ellipse(draw, node, 4.4, 3.4, _fade(COAT_DARK, 0.9), OUTLINE_SOFT, 0.45)
            font = _font(6.2, preferred=("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"))
            draw.text(_pt(_offset(node, 0.0, 0.0)), str(idx), font=font, fill=_fade(HILBERT_LIGHT, 0.95), anchor="mm")
        if pose.chain > 0.55:
            out = T(pose.near_hand)
            _line(draw, [chest, out], _fade(HILBERT_LIGHT, (pose.chain - 0.55) / 0.45), 2.0)


def _draw_ability_effects_front(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    if pose.field > 0.02:
        center = T((76.0, 64.0))
        _arc(draw, center, 18.0, 25.0, 110, 250, _fade(FIELD, pose.field), 2.2)
        _arc(draw, center, 14.0, 20.0, 110, 250, _fade(HILBERT_LIGHT, pose.field * 0.55), 0.9)
    if pose.compress > 0.45:
        hand = T(pose.near_hand)
        release = (pose.compress - 0.45) / 0.55
        _line(draw, [hand, (hand[0] + 22.0 * release, hand[1] - 1.2)], _fade(HILBERT_LIGHT, release), 2.4)
        _line(draw, [hand, (hand[0] + 29.0 * release, hand[1] + 1.7)], _fade(FIELD, release * 0.8), 1.0)


def _render_native_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    """Render into the authored supersampled canvas without raster scaling."""
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
    return image


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _render_native_frame(animation, frame_idx, nframes).resize(
        (FRAME_W, FRAME_H), Image.Resampling.LANCZOS
    )


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    """Publish Davy Hylbert's native close-up expressions and talk loop."""
    del opts
    face = FaceGuide(
        center_x=65.0,
        center_y=28.0,
        width=27.0,
        height=31.0,
        source_width=FRAME_W,
        source_height=FRAME_H,
    )

    def portrait_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        return render_framed_portrait(
            _render_native_frame(animation, frame_idx, frame_count),
            face,
            view_width=60.0,
            center_y=35.0,
        )

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 1, 8)),
        "lecturing": PortraitClip(
            tuple(portrait_frame("talk", frame, 8) for frame in range(8)),
            duration_ms=104,
            looping=True,
        ),
        "axiomatic": PortraitClip(
            tuple(
                portrait_frame("compressed_sense", frame, 8)
                for frame in (1, 3, 5, 7)
            ),
            duration_ms=118,
            looping=True,
        ),
        "delighted": PortraitClip(
            tuple(portrait_frame("celebrate", frame, 8) for frame in (1, 3, 5, 7)),
            duration_ms=118,
            looping=True,
        ),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


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


__all__ = ["ACTOR_METADATA", "render", "render_canonical", "render_portraits"]


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
