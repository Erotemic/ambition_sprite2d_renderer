"""Procedural full-action renderer for Carl Stargan.

Carl Stargan is a warm, theatrical cosmic storyteller whose combat vocabulary
turns scale, wonder, skepticism, and planetary motion into readable action. His
silhouette is deliberately specific rather than a generic professor: a tall
1970s science-presenter frame, a broad camel corduroy jacket with wide lapels,
a black turtleneck, burgundy trousers, expressive hands, a long animated face,
and a dense crown of swept, wavy dark hair.

The authored moves are intrinsic visual metaphors rather than held props:

* ``planetary_orbit`` slings a small world around his body and releases it;
* ``pale_blue_dot`` concentrates an immense field onto one tiny blue point;
* ``cosmic_calendar`` compresses a radial history into a forward sweep;
* ``billions_and_billions`` expands a dense handful of stars into open space;
* ``starstuff`` briefly resolves the body into a rotating spiral field.

Everything is drawn in Python/Pillow at supersampled resolution. There are no
image-generation inputs, floor ellipses, drop shadows, or permanently held
props. Portraits are native rerenders from the same authored geometry and expose
multiple named expression clips through the standard portrait API.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from ...authoring.portrait import (
    PortraitClip,
    write_portrait_sheet,
)
from ...authoring.sheet_build import build_sheet, write_canonical

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "carl_stargan"
FRAME_W = 128
FRAME_H = 128
SUPER = 5

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 150),
    ("walk", 8, 108),
    ("run", 8, 82),
    ("crouch", 6, 96),
    ("crouch_walk", 8, 90),
    ("jump", 6, 92),
    ("fall", 6, 92),
    ("land_hard", 8, 92),
    ("land_recovery", 6, 74),
    ("dash_startup", 4, 52),
    ("dash", 6, 62),
    ("cosmic_drift", 8, 58),
    ("slide", 6, 70),
    ("roll", 8, 58),
    ("wall_grab", 6, 105),
    ("wall_jump", 6, 82),
    ("ledge_grab", 6, 98),
    ("ledge_climb", 6, 98),
    ("ledge_getup", 6, 44),
    ("ledge_roll", 8, 40),
    ("climb", 8, 98),
    ("swim", 8, 104),
    ("float_glide", 8, 108),
    ("block", 6, 84),
    ("hit", 5, 88),
    ("death", 8, 108),
    ("talk", 8, 108),
    ("interact", 8, 92),
    ("jab", 5, 58),
    ("punch", 7, 70),
    ("planetary_orbit", 9, 72),
    ("attack_up", 8, 66),
    ("attack_down", 8, 66),
    ("air_neutral", 8, 62),
    ("air_forward", 7, 62),
    ("air_back", 7, 62),
    ("air_down", 7, 70),
    ("air_up", 7, 62),
    ("pale_blue_dot", 9, 78),
    ("cosmic_calendar", 10, 78),
    ("billions_and_billions", 10, 76),
    ("starstuff", 10, 76),
    ("celebrate", 8, 90),
    ("taunt", 8, 94),
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_carl_stargan", "display_name": "Carl Stargan"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "story",
            "humanoid",
            "science_communicator",
            "cosmic_storyteller",
            "skeptic",
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
    "visual": {
        "default_pose": "idle",
        "face_guide": {
            "center": {"x": 64.0, "y": 29.0},
            "size": {"w": 31.0, "h": 36.0},
            "source_size": {"w": 128.0, "h": 128.0},
        },
    },
    "tags": [
        "story",
        "humanoid",
        "science_communicator",
        "cosmic_storyteller",
        "skeptic",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 29.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 64.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 44.0, "y": 79.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 86.0, "y": 79.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 3.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "planetary_orbit", "events": []},
        "action.ranged.primary": {"animation": "pale_blue_dot", "events": []},
        "action.special.primary": {"animation": "cosmic_calendar", "events": []},
        "action.special.secondary": {"animation": "billions_and_billions", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}

OUTLINE = (23, 17, 18, 255)
OUTLINE_SOFT = (58, 40, 35, 255)
SKIN = (184, 126, 91, 255)
SKIN_LIGHT = (221, 166, 122, 255)
SKIN_HIGHLIGHT = (210, 153, 112, 255)
SKIN_SHADE = (137, 84, 65, 255)
HAIR = (25, 20, 20, 255)
HAIR_MID = (39, 29, 27, 255)
HAIR_GLEAM = (87, 63, 49, 255)
JACKET = (171, 118, 69, 255)
JACKET_LIGHT = (207, 157, 95, 255)
JACKET_DARK = (121, 76, 45, 255)
JACKET_DEEP = (78, 48, 34, 255)
TURTLENECK = (25, 28, 34, 255)
TURTLENECK_LIGHT = (57, 60, 68, 255)
TROUSER = (111, 42, 52, 255)
TROUSER_LIGHT = (149, 62, 68, 255)
TROUSER_DARK = (72, 28, 39, 255)
SHOE = (76, 48, 35, 255)
SHOE_LIGHT = (125, 82, 54, 255)
SOLE = (29, 24, 22, 255)
EYE = (30, 24, 22, 255)
EYE_LIGHT = (228, 216, 188, 255)
MOUTH = (112, 54, 49, 255)
STAR_GOLD = (248, 203, 112, 255)
STAR_WHITE = (251, 244, 214, 255)
NEBULA_BLUE = (91, 164, 220, 255)
NEBULA_VIOLET = (148, 101, 186, 255)
PALE_BLUE = (104, 190, 225, 255)
PLANET_OCHRE = (208, 139, 66, 255)
PLANET_RUST = (150, 71, 50, 255)
COSMIC_DARK = (22, 30, 50, 255)


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
    rotation_pivot: Point = (64.0, 88.0)
    body_lean: float = 0.0
    head_x: float = 0.0
    head_y: float = 0.0
    head_tilt: float = 0.0
    blink: bool = False
    mouth_open: float = 0.0
    smile: float = 0.34
    brow: float = 0.2
    skeptical: float = 0.0
    wonder: float = 0.0
    near_shoulder: Point = (81.0, 55.0)
    near_elbow: Point = (87.0, 72.0)
    near_hand: Point = (86.0, 87.0)
    far_shoulder: Point = (47.0, 56.0)
    far_elbow: Point = (42.0, 73.0)
    far_hand: Point = (44.0, 87.0)
    near_hip: Point = (70.0, 89.0)
    near_knee: Point = (72.0, 103.0)
    near_ankle: Point = (74.0, 118.0)
    far_hip: Point = (58.0, 89.0)
    far_knee: Point = (56.0, 103.0)
    far_ankle: Point = (55.0, 118.0)
    near_hand_mode: str = "relaxed"
    far_hand_mode: str = "relaxed"
    orbit: float = 0.0
    orbit_phase: float = 0.0
    orbit_release: float = 0.0
    pale_dot: float = 0.0
    calendar: float = 0.0
    billions: float = 0.0
    starstuff: float = 0.0
    cosmic_trail: float = 0.0


def _pose(animation: str, frame_idx: int, nframes: int) -> Pose:
    phase = frame_idx / max(1, nframes)
    t = frame_idx / max(1, nframes - 1)
    cyc = math.tau * phase
    wave = math.sin(cyc)
    cosine = math.cos(cyc)
    p = Pose()
    p.root_y = 0.55 * math.sin(cyc)
    p.head_y = -0.32 * math.sin(cyc)
    p.blink = animation == "idle" and frame_idx in {5}

    if animation == "walk":
        stride = 8.0 * wave
        p.root_y = -0.9 * abs(cosine)
        p.body_lean = 1.2
        p.near_knee = (72.0 + stride * 0.40, 103.0 - abs(stride) * 0.16)
        p.near_ankle = (74.0 + stride, 118.0 - max(0.0, -wave) * 3.0)
        p.far_knee = (56.0 - stride * 0.40, 103.0 - abs(stride) * 0.16)
        p.far_ankle = (55.0 - stride, 118.0 - max(0.0, wave) * 3.0)
        p.near_elbow = (86.0 - stride * 0.34, 71.0)
        p.near_hand = (83.0 - stride * 0.62, 85.0)
        p.far_elbow = (44.0 + stride * 0.34, 72.0)
        p.far_hand = (46.0 + stride * 0.62, 86.0)
    elif animation == "run":
        stride = 12.5 * wave
        p.root_y = -2.3 * abs(cosine)
        p.body_lean = 8.0
        p.head_x = 1.2
        p.near_knee = (73.0 + stride * 0.45, 101.0 - abs(stride) * 0.18)
        p.near_ankle = (75.0 + stride, 116.0 - max(0.0, -wave) * 5.0)
        p.far_knee = (57.0 - stride * 0.45, 102.0 - abs(stride) * 0.18)
        p.far_ankle = (55.0 - stride, 117.0 - max(0.0, wave) * 5.0)
        p.near_elbow = (80.0 - stride * 0.35, 66.0)
        p.near_hand = (76.0 - stride * 0.62, 78.0)
        p.far_elbow = (51.0 + stride * 0.35, 68.0)
        p.far_hand = (54.0 + stride * 0.62, 80.0)
    elif animation in {"crouch", "crouch_walk"}:
        step = 5.0 * wave if animation == "crouch_walk" else 0.0
        p.root_y = 13.0
        p.body_lean = 7.0
        p.head_y = 4.0
        p.near_hip = (70.0, 93.0)
        p.near_knee = (80.0 + step, 106.0)
        p.near_ankle = (74.0 + step * 1.25, 118.0)
        p.far_hip = (58.0, 93.0)
        p.far_knee = (49.0 - step, 106.0)
        p.far_ankle = (55.0 - step * 1.25, 118.0)
        p.near_elbow = (86.0, 79.0)
        p.near_hand = (77.0, 92.0)
        p.far_elbow = (46.0, 80.0)
        p.far_hand = (54.0, 93.0)
    elif animation == "jump":
        lift = math.sin(t * math.pi)
        p.root_y = -12.0 * lift
        p.body_lean = 4.0
        p.near_knee = (74.0, 101.0 - 4.0 * lift)
        p.near_ankle = (82.0, 112.0 - 8.0 * lift)
        p.far_knee = (56.0, 100.0 - 3.0 * lift)
        p.far_ankle = (49.0, 111.0 - 7.0 * lift)
        p.near_elbow = (88.0, 62.0)
        p.near_hand = (92.0, 47.0)
        p.far_elbow = (44.0, 64.0)
        p.far_hand = (38.0, 52.0)
        p.near_hand_mode = p.far_hand_mode = "open"
    elif animation == "fall":
        p.root_y = -6.0 + 8.0 * t
        p.body_lean = -2.0
        p.near_elbow = (89.0, 66.0)
        p.near_hand = (96.0, 57.0)
        p.far_elbow = (41.0, 67.0)
        p.far_hand = (34.0, 59.0)
        p.near_knee = (77.0, 102.0)
        p.near_ankle = (83.0, 113.0)
        p.far_knee = (52.0, 102.0)
        p.far_ankle = (47.0, 114.0)
        p.near_hand_mode = p.far_hand_mode = "open"
    elif animation in {"land_hard", "land_recovery"}:
        impact = 1.0 - t if animation == "land_recovery" else _pulse(min(1.0, t * 1.6))
        p.root_y = 11.0 * impact
        p.body_lean = 8.0 * impact
        p.head_y = 3.0 * impact
        p.near_knee = (80.0, 104.0)
        p.near_ankle = (75.0, 118.0)
        p.far_knee = (49.0, 105.0)
        p.far_ankle = (55.0, 118.0)
        p.near_hand = (84.0, 101.0)
        p.far_hand = (49.0, 101.0)
    elif animation in {"dash_startup", "dash", "cosmic_drift", "slide"}:
        amount = _smooth(t) if animation == "dash_startup" else 1.0
        if animation == "slide":
            p.root_y = 15.0
            p.body_lean = 21.0
            p.rotation = -7.0
        else:
            p.root_y = 4.0 - 2.0 * abs(wave)
            p.body_lean = 17.0 * amount
        p.head_x = 2.0 * amount
        p.near_shoulder = (81.0, 57.0)
        p.near_elbow = (70.0, 65.0)
        p.near_hand = (57.0, 70.0)
        p.far_shoulder = (50.0, 58.0)
        p.far_elbow = (37.0, 63.0)
        p.far_hand = (25.0, 64.0)
        p.near_hip = (70.0, 91.0)
        p.near_knee = (83.0, 101.0)
        p.near_ankle = (96.0, 109.0)
        p.far_hip = (58.0, 91.0)
        p.far_knee = (52.0, 105.0)
        p.far_ankle = (39.0, 115.0)
        if animation == "cosmic_drift":
            p.cosmic_trail = 0.45 + 0.55 * abs(math.sin(cyc * 2.0))
            p.orbit_phase = phase
    elif animation in {"roll", "ledge_roll"}:
        p.rotation = -360.0 * t
        p.rotation_pivot = (64.0, 94.0)
        p.root_y = 9.0
        p.near_hand = (75.0, 88.0)
        p.far_hand = (54.0, 88.0)
        p.near_knee = (76.0, 99.0)
        p.near_ankle = (71.0, 107.0)
        p.far_knee = (54.0, 99.0)
        p.far_ankle = (60.0, 107.0)
        p.starstuff = 0.22
    elif animation in {"wall_grab", "ledge_grab"}:
        p.root_x = 12.0
        p.body_lean = 6.0
        p.near_elbow = (87.0, 55.0)
        p.near_hand = (96.0, 47.0)
        p.far_elbow = (73.0, 58.0)
        p.far_hand = (93.0, 53.0)
        p.near_knee = (77.0, 103.0)
        p.near_ankle = (91.0, 109.0)
        p.far_knee = (58.0, 102.0)
        p.far_ankle = (84.0, 114.0)
        p.near_hand_mode = p.far_hand_mode = "grip"
    elif animation in {"wall_jump", "ledge_climb", "ledge_getup"}:
        rise = _smooth(t)
        p.root_x = 10.0 - 16.0 * rise
        p.root_y = 6.0 - 13.0 * rise
        p.body_lean = -8.0 + 14.0 * rise
        p.near_elbow = (87.0, 57.0)
        p.near_hand = (95.0, 48.0)
        p.far_elbow = (73.0, 58.0)
        p.far_hand = (93.0, 52.0)
        p.near_knee = (80.0, 101.0)
        p.near_ankle = (91.0, 111.0)
        p.far_knee = (53.0, 101.0)
        p.far_ankle = (47.0, 112.0)
        p.near_hand_mode = p.far_hand_mode = "grip"
    elif animation == "climb":
        step = 6.0 * wave
        p.root_y = -1.5 * abs(cosine)
        p.near_hand = (85.0, 53.0 + step)
        p.near_elbow = (84.0, 65.0 + step * 0.4)
        p.far_hand = (47.0, 53.0 - step)
        p.far_elbow = (46.0, 66.0 - step * 0.4)
        p.near_ankle = (79.0, 115.0 - step)
        p.far_ankle = (51.0, 115.0 + step)
        p.near_hand_mode = p.far_hand_mode = "grip"
    elif animation in {"swim", "float_glide"}:
        p.rotation = -12.0 if animation == "swim" else -5.0
        p.root_y = -3.0 + 2.0 * wave
        p.near_hand = (94.0 + 5.0 * wave, 61.0)
        p.near_elbow = (83.0, 65.0)
        p.far_hand = (36.0 - 5.0 * wave, 64.0)
        p.far_elbow = (46.0, 68.0)
        p.near_ankle = (87.0, 112.0 + 3.0 * wave)
        p.far_ankle = (42.0, 114.0 - 3.0 * wave)
        p.near_hand_mode = p.far_hand_mode = "open"
        if animation == "float_glide":
            p.orbit = 0.32
            p.orbit_phase = phase
    elif animation == "block":
        p.body_lean = -4.0
        p.near_elbow = (86.0, 63.0)
        p.near_hand = (77.0, 57.0)
        p.far_elbow = (65.0, 67.0)
        p.far_hand = (74.0, 69.0)
        p.near_hand_mode = p.far_hand_mode = "open"
        p.orbit = 0.82
        p.orbit_phase = phase
    elif animation == "hit":
        shock = _pulse(t)
        p.root_x = -7.0 * shock
        p.rotation = -8.0 * shock
        p.head_x = -2.0 * shock
        p.mouth_open = 0.65 * shock
        p.near_hand = (93.0, 78.0)
        p.far_hand = (34.0, 81.0)
    elif animation == "death":
        fall = _smooth(t)
        p.rotation = -82.0 * fall
        p.rotation_pivot = (61.0, 112.0)
        p.root_x = -6.0 * fall
        p.root_y = 9.0 * fall
        p.mouth_open = 0.45 * fall
        p.smile = 0.0
        p.starstuff = 0.4 * fall
    elif animation == "talk":
        p.mouth_open = 0.14 + 0.56 * max(0.0, math.sin(cyc * 1.5))
        p.smile = 0.58
        p.brow = 0.78
        p.wonder = 0.35 + 0.25 * max(0.0, wave)
        p.near_elbow = (87.0, 68.0)
        p.near_hand = (96.0, 58.0 + 3.0 * wave)
        p.near_hand_mode = "open"
        p.far_elbow = (43.0, 70.0)
        p.far_hand = (50.0, 79.0)
        p.far_hand_mode = "open"
    elif animation == "interact":
        reach = _pulse(t)
        p.body_lean = 7.0 * reach
        p.near_elbow = (89.0, 65.0)
        p.near_hand = (101.0, 63.0)
        p.near_hand_mode = "point"
        p.far_hand = (53.0, 81.0)
    elif animation in {"jab", "punch", "planetary_orbit"}:
        strike = _pulse(t)
        p.body_lean = 10.0 * strike
        p.root_x = 3.0 * strike
        p.near_elbow = (88.0 + 5.0 * strike, 67.0)
        p.near_hand = (86.0 + 24.0 * strike, 68.0)
        p.near_hand_mode = "fist" if animation != "planetary_orbit" else "open"
        p.far_hand = (52.0, 75.0)
        p.far_hand_mode = "fist" if animation != "planetary_orbit" else "open"
        p.near_knee = (74.0 + 4.0 * strike, 103.0)
        p.near_ankle = (82.0 + 9.0 * strike, 118.0)
        if animation == "planetary_orbit":
            p.orbit = 0.35 + 0.65 * _smooth(min(1.0, t * 1.35))
            p.orbit_phase = phase * 1.3
            p.orbit_release = _smooth(max(0.0, (t - 0.58) / 0.42))
            p.wonder = 0.42
    elif animation in {"attack_up", "air_up"}:
        strike = _pulse(t)
        p.near_elbow = (84.0, 52.0)
        p.near_hand = (81.0, 33.0 - 4.0 * strike)
        p.near_hand_mode = "open"
        p.far_hand = (51.0, 77.0)
        p.body_lean = -4.0
        p.orbit = 0.24 * strike
        p.orbit_phase = phase
    elif animation in {"attack_down", "air_down"}:
        strike = _pulse(t)
        p.near_elbow = (86.0, 76.0)
        p.near_hand = (90.0, 100.0 + 5.0 * strike)
        p.near_hand_mode = "fist"
        p.far_hand = (52.0, 72.0)
        p.body_lean = 7.0
    elif animation.startswith("air_"):
        p.root_y = -8.0
        p.rotation = 18.0 * wave
        p.near_hand = (92.0, 68.0)
        p.far_hand = (36.0, 70.0)
        p.near_ankle = (86.0, 110.0)
        p.far_ankle = (44.0, 111.0)
        p.orbit = 0.20
        p.orbit_phase = phase
    elif animation == "pale_blue_dot":
        gather = _smooth(min(1.0, t * 1.55))
        release = _smooth(max(0.0, (t - 0.56) / 0.44))
        p.pale_dot = gather * (1.0 - 0.35 * release)
        p.orbit_phase = phase
        p.body_lean = 2.0 + 8.0 * release
        p.near_elbow = (85.0, 64.0)
        p.near_hand = (95.0 + 12.0 * release, 61.0)
        p.near_hand_mode = "open"
        p.far_elbow = (45.0, 66.0)
        p.far_hand = (55.0, 62.0)
        p.far_hand_mode = "open"
        p.wonder = 0.7
    elif animation == "cosmic_calendar":
        p.calendar = _smooth(t)
        p.orbit_phase = phase
        p.near_elbow = (88.0, 63.0)
        p.near_hand = (97.0, 50.0 + 5.0 * wave)
        p.near_hand_mode = "open"
        p.far_elbow = (42.0, 64.0)
        p.far_hand = (33.0, 53.0 - 5.0 * wave)
        p.far_hand_mode = "open"
        p.mouth_open = 0.20 + 0.25 * abs(wave)
        p.wonder = 0.55
    elif animation == "billions_and_billions":
        p.billions = _smooth(t)
        p.orbit_phase = phase
        p.near_elbow = (89.0, 62.0)
        p.near_hand = (100.0, 49.0)
        p.near_hand_mode = "open"
        p.far_elbow = (40.0, 64.0)
        p.far_hand = (28.0, 52.0)
        p.far_hand_mode = "open"
        p.root_y = -2.0 * math.sin(t * math.pi)
        p.mouth_open = 0.22 + 0.25 * abs(wave)
        p.wonder = 0.8
    elif animation == "starstuff":
        p.starstuff = math.sin(math.pi * t)
        p.orbit_phase = phase
        p.rotation = 8.0 * math.sin(cyc)
        p.near_elbow = (88.0, 62.0)
        p.near_hand = (98.0, 54.0)
        p.far_elbow = (41.0, 64.0)
        p.far_hand = (31.0, 56.0)
        p.near_hand_mode = p.far_hand_mode = "open"
        p.wonder = 0.9
    elif animation == "celebrate":
        lift = abs(math.sin(cyc))
        p.root_y = -7.0 * lift
        p.near_elbow = (83.0, 49.0)
        p.near_hand = (88.0, 34.0)
        p.far_elbow = (46.0, 49.0)
        p.far_hand = (40.0, 34.0)
        p.near_hand_mode = p.far_hand_mode = "open"
        p.smile = 1.0
        p.mouth_open = 0.35
        p.billions = 0.25 + 0.30 * lift
        p.wonder = 0.9
    elif animation == "taunt":
        p.near_elbow = (87.0, 67.0)
        p.near_hand = (95.0, 55.0)
        p.near_hand_mode = "point"
        p.far_elbow = (45.0, 69.0)
        p.far_hand = (52.0, 80.0)
        p.smile = 0.22
        p.brow = 0.82
        p.skeptical = 1.0
        p.head_tilt = -3.5

    return p


def _transform(point: Point, pose: Pose) -> Point:
    x, y = point
    # Forward lean is a shear around the waist, not a rigid rotation; this
    # keeps the shoes planted while giving the runner silhouette momentum.
    y_rel = y - 88.0
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
    _polygon(draw, _segment_quad(hip_t, knee_t, 5.2, 4.5), trouser, OUTLINE, 1.0)
    # A slight 1970s flare helps the lower-body silhouette read at sprite scale.
    _polygon(draw, _segment_quad(knee_t, ankle_t, 4.5, 4.4), trouser_hi, OUTLINE, 1.0)
    _ellipse(draw, knee_t, 4.6, 3.8, trouser_hi, OUTLINE, 0.8)
    along, normal, _ = _unit(knee_t, ankle_t)
    toe = (
        ankle_t[0] + along[0] * 2.7 + normal[0] * 5.0,
        ankle_t[1] + along[1] * 2.7 + normal[1] * 5.0,
    )
    shoe_poly = [
        (ankle_t[0] - normal[0] * 3.8, ankle_t[1] - normal[1] * 3.8),
        (ankle_t[0] + normal[0] * 3.9, ankle_t[1] + normal[1] * 3.9),
        (toe[0] + normal[0] * 3.3, toe[1] + normal[1] * 3.3),
        (toe[0] - normal[0] * 2.7, toe[1] - normal[1] * 2.7),
    ]
    _polygon(draw, shoe_poly, SHOE if not far else JACKET_DEEP, OUTLINE, 1.0)
    _line(draw, [shoe_poly[2], shoe_poly[3]], SOLE, 1.8)
    if not far:
        _line(draw, [_lerp_point(ankle_t, toe, 0.30), _lerp_point(ankle_t, toe, 0.70)], SHOE_LIGHT, 0.75)


def _draw_neck(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    center = T((64.0 + pose.head_x, 30.0 + pose.head_y))
    neck = [
        T((59.4 + pose.head_x, 44.0 + pose.head_y)),
        T((68.4 + pose.head_x, 43.7 + pose.head_y)),
        T((69.2 + pose.head_x, 54.8 + pose.head_y)),
        T((59.0 + pose.head_x, 55.0 + pose.head_y)),
    ]
    neck = [_rotate(q, center, pose.head_tilt) for q in neck]
    _polygon(draw, neck, SKIN, OUTLINE_SOFT, 0.85)
    _line(draw, [neck[0], neck[3]], SKIN_SHADE, 0.65)
    _line(draw, [neck[1], neck[2]], SKIN_HIGHLIGHT, 0.55)


def _draw_torso(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    # Wide shoulders, long jacket, and broad lapels produce the specific
    # broadcaster silhouette before any facial detail is visible.
    jacket = [
        T((46.5, 56.0)),
        T((55.5, 50.2)),
        T((72.0, 49.8)),
        T((82.8, 55.0)),
        T((86.0, 72.0)),
        T((79.0, 91.0)),
        T((67.0, 94.0)),
        T((51.5, 90.5)),
        T((43.8, 71.0)),
    ]
    _polygon(draw, jacket, JACKET_DARK, OUTLINE, 1.25)
    far_panel = [T((47.2, 57.0)), T((57.0, 51.2)), T((62.0, 92.0)), T((52.0, 88.7)), T((45.5, 70.0))]
    near_panel = [T((70.0, 51.0)), T((81.4, 56.0)), T((84.2, 71.0)), T((77.0, 89.0)), T((66.0, 93.0))]
    _polygon(draw, far_panel, JACKET, OUTLINE_SOFT, 0.72)
    _polygon(draw, near_panel, JACKET_LIGHT, OUTLINE_SOFT, 0.72)

    # Black turtleneck, not a shirt-and-tie academic uniform.
    shirt = [T((57.0, 52.0)), T((70.5, 51.8)), T((74.0, 68.0)), T((67.0, 79.0)), T((55.5, 68.5))]
    _polygon(draw, shirt, TURTLENECK, OUTLINE_SOFT, 0.7)
    _ellipse(draw, T((64.0, 53.2)), 6.6, 3.2, TURTLENECK, None, 0.0)
    _arc(draw, T((64.0, 54.7)), 6.5, 3.7, 190, 350, TURTLENECK_LIGHT, 0.9)

    # Generous lapels with a strong V frame the turtleneck and survive downsample.
    left_lapel = [T((56.5, 51.2)), T((61.5, 56.0)), T((57.0, 73.5)), T((48.5, 57.0))]
    right_lapel = [T((70.5, 51.1)), T((65.0, 56.0)), T((71.0, 72.0)), T((81.5, 56.0))]
    _polygon(draw, left_lapel, JACKET_LIGHT, OUTLINE_SOFT, 0.75)
    _polygon(draw, right_lapel, JACKET, OUTLINE_SOFT, 0.75)
    _line(draw, [T((63.7, 55.0)), T((65.5, 92.2))], JACKET_DEEP, 0.8)

    # Corduroy ribs are restrained, following each panel instead of becoming noise.
    for x in (50.8, 54.0, 57.2):
        _line(draw, [T((x, 60.0)), T((x + 2.2, 84.5))], JACKET_DEEP, 0.45)
    for x in (72.2, 75.5, 78.5):
        _line(draw, [T((x, 59.0)), T((x - 1.8, 84.0))], JACKET_DEEP, 0.42)
    _ellipse(draw, T((47.8, 57.0)), 6.2, 5.5, JACKET, OUTLINE, 0.9)
    _ellipse(draw, T((81.2, 56.3)), 6.5, 5.6, JACKET_LIGHT, OUTLINE, 0.9)


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
    # Both arms retain the same skin value; depth is carried by jacket panels and
    # overlap, avoiding the mismatched-arm artifact of older front-facing sprites.
    skin = SKIN_LIGHT
    sleeve = JACKET if far else JACKET_LIGHT
    along, _, length = _unit(elbow_t, hand_t)
    wrist = (
        hand_t[0] - along[0] * min(3.1, length * 0.28),
        hand_t[1] - along[1] * min(3.1, length * 0.28),
    )
    upper_end = _lerp_point(shoulder_t, elbow_t, 0.67)
    _polygon(draw, _segment_quad(shoulder_t, upper_end, 5.4, 4.2), sleeve, OUTLINE, 0.95)
    _polygon(draw, _segment_quad(upper_end, elbow_t, 4.2, 3.7), sleeve, OUTLINE, 0.9)
    _polygon(draw, _segment_quad(elbow_t, wrist, 3.6, 2.8), skin, OUTLINE, 0.9)
    _ellipse(draw, elbow_t, 3.8, 3.4, sleeve, OUTLINE, 0.75)
    # Fine sleeve ribs give the jacket texture without depending on a texture asset.
    _line(draw, [_lerp_point(shoulder_t, upper_end, 0.25), _lerp_point(shoulder_t, upper_end, 0.80)], JACKET_DEEP, 0.45)
    _draw_hand(draw, wrist, hand_t, mode, skin)


def _draw_hand(draw: ImageDraw.ImageDraw, wrist: Point, hand: Point, mode: str, skin: RGBA) -> None:
    along, normal, _ = _unit(wrist, hand)
    rx = 3.7 if mode == "open" else 3.1
    _ellipse(draw, hand, rx, 2.9, skin, OUTLINE, 0.8)
    if mode == "open":
        for offset in (-1.55, -0.5, 0.5, 1.55):
            start = (
                hand[0] + along[0] * 1.0 + normal[0] * offset,
                hand[1] + along[1] * 1.0 + normal[1] * offset,
            )
            end = (
                start[0] + along[0] * (3.1 - abs(offset) * 0.18),
                start[1] + along[1] * (3.1 - abs(offset) * 0.18),
            )
            _line(draw, [start, end], OUTLINE, 1.35)
            _line(draw, [start, end], skin, 0.72)
    elif mode == "point":
        start = (hand[0] + along[0] * 1.4, hand[1] + along[1] * 1.4)
        end = (hand[0] + along[0] * 5.8, hand[1] + along[1] * 5.8)
        _line(draw, [start, end], OUTLINE, 1.6)
        _line(draw, [start, end], skin, 0.85)
    elif mode == "grip":
        _line(draw, [hand, (hand[0] + normal[0] * 3.1, hand[1] + normal[1] * 3.1)], OUTLINE, 1.4)
    elif mode == "fist":
        _line(draw, [(hand[0] - normal[0] * 1.8, hand[1] - normal[1] * 1.8), (hand[0] + normal[0] * 1.8, hand[1] + normal[1] * 1.8)], SKIN_SHADE, 0.8)


def _draw_head(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    center = T((64.0 + pose.head_x, 30.0 + pose.head_y))

    def H(point: Point) -> Point:
        q = T((point[0] + pose.head_x, point[1] + pose.head_y))
        return _rotate(q, center, pose.head_tilt)

    _draw_neck(draw, pose)
    _ellipse(draw, H((49.8, 31.0)), 3.8, 5.9, SKIN, OUTLINE, 0.8)
    _ellipse(draw, H((78.1, 30.5)), 3.2, 5.4, SKIN_LIGHT, OUTLINE, 0.75)

    face = [
        H((51.0, 18.5)),
        H((61.0, 13.8)),
        H((71.8, 15.0)),
        H((78.2, 22.0)),
        H((79.2, 32.5)),
        H((75.3, 43.1)),
        H((67.0, 48.8)),
        H((58.1, 46.2)),
        H((51.6, 38.7)),
        H((49.3, 28.0)),
    ]
    _polygon(draw, face, SKIN, OUTLINE, 1.2)

    # Strong cheek plane and long central nose keep the face recognizable at 128px.
    _polygon(draw, [H((53.0, 23.0)), H((59.0, 17.0)), H((58.0, 42.0)), H((52.0, 37.0))], (157, 99, 73, 255), None, 0.0)
    _polygon(draw, [H((69.0, 18.0)), H((75.0, 23.0)), H((74.0, 38.0)), H((69.0, 42.0))], (198, 139, 101, 255), None, 0.0)

    # Dense, swept, wavy hair: a connected cap plus discrete curls around the edge.
    hair = [
        H((49.2, 29.0)), H((48.8, 20.7)), H((52.5, 13.5)), H((58.0, 8.9)),
        H((65.0, 8.2)), H((72.0, 10.2)), H((78.4, 15.4)), H((81.0, 22.0)),
        H((78.5, 26.2)), H((73.5, 21.7)), H((68.5, 18.8)), H((63.0, 18.0)),
        H((58.0, 20.0)), H((54.0, 25.5)),
    ]
    _polygon(draw, hair, HAIR, OUTLINE, 1.05)
    for c, rx, ry in [
        ((52.5, 14.5), 4.6, 3.8), ((58.0, 10.2), 5.0, 3.7), ((64.0, 9.0), 5.2, 3.5),
        ((70.3, 10.5), 5.0, 3.8), ((76.0, 14.7), 4.5, 4.0), ((78.5, 20.2), 3.8, 4.4),
        ((52.0, 22.0), 3.7, 4.8),
    ]:
        _ellipse(draw, H(c), rx, ry, HAIR, OUTLINE_SOFT, 0.48)
    _arc(draw, H((62.0, 11.5)), 8.8, 4.2, 195, 350, HAIR_GLEAM, 0.75)
    _arc(draw, H((72.0, 14.2)), 5.8, 3.7, 180, 340, HAIR_GLEAM, 0.65)
    _arc(draw, H((53.5, 19.0)), 4.8, 5.8, 265, 75, HAIR_GLEAM, 0.55)

    left_eye = H((58.4, 29.0))
    right_eye = H((70.1, 28.5))
    left_brow_y = 24.8 - 0.8 * pose.brow + 0.65 * pose.skeptical
    right_brow_y = 24.5 - 0.8 * pose.brow - 0.85 * pose.skeptical
    _line(draw, [H((54.7, left_brow_y + 0.5)), H((61.7, left_brow_y - 0.4))], HAIR, 1.35)
    _line(draw, [H((66.5, right_brow_y - 0.2)), H((73.7, right_brow_y + 0.5))], HAIR, 1.35)

    if pose.blink:
        _arc(draw, left_eye, 3.2, 1.2, 8, 172, OUTLINE, 0.9)
        _arc(draw, right_eye, 3.2, 1.2, 8, 172, OUTLINE, 0.9)
    else:
        eye_ry = 1.28 + 0.24 * pose.wonder
        _ellipse(draw, left_eye, 2.75, eye_ry, EYE_LIGHT, OUTLINE, 0.65)
        _ellipse(draw, right_eye, 2.85, eye_ry, EYE_LIGHT, OUTLINE, 0.65)
        _ellipse(draw, H((58.8, 29.1)), 0.95, 1.05, EYE, None, 0.0)
        _ellipse(draw, H((70.5, 28.6)), 0.95, 1.05, EYE, None, 0.0)
        _ellipse(draw, H((59.2, 28.7)), 0.25, 0.25, STAR_WHITE, None, 0.0)
        _ellipse(draw, H((70.9, 28.2)), 0.25, 0.25, STAR_WHITE, None, 0.0)

    # Prominent long nose, softened with a lit bridge and a clear tip.
    _line(draw, [H((64.0, 27.0)), H((63.2, 36.1)), H((60.8, 38.5))], SKIN_SHADE, 0.9)
    _line(draw, [H((65.0, 27.4)), H((65.7, 35.7)), H((67.2, 37.2))], SKIN_HIGHLIGHT, 0.62)
    _arc(draw, H((63.7, 38.1)), 3.3, 1.8, 15, 175, OUTLINE_SOFT, 0.6)

    mouth_y = 42.2
    if pose.mouth_open > 0.12:
        _ellipse(draw, H((64.2, mouth_y)), 3.5 + 0.7 * pose.smile, 1.0 + 2.1 * pose.mouth_open, MOUTH, OUTLINE, 0.7)
        if pose.mouth_open > 0.42:
            _arc(draw, H((64.2, mouth_y + 0.3)), 2.4, 1.0, 190, 350, SKIN_HIGHLIGHT, 0.45)
    else:
        lift = 1.0 * pose.smile
        _arc(draw, H((64.0, mouth_y - lift * 0.25)), 4.3, 2.2 + lift, 12, 168, MOUTH, 0.85)
    _line(draw, [H((61.8, 46.2)), H((66.8, 46.6))], (151, 91, 68, 255), 0.55)
    _arc(draw, H((54.8, 36.0)), 4.0, 5.0, 300, 70, (204, 145, 106, 255), 0.5)
    _arc(draw, H((73.5, 36.0)), 4.0, 5.0, 110, 235, (158, 100, 74, 255), 0.5)


def _draw_star(draw: ImageDraw.ImageDraw, center: Point, radius: float, color: RGBA, alpha: float = 1.0) -> None:
    color = _fade(color, alpha)
    x, y = center
    points: List[Point] = []
    for i in range(8):
        angle = -math.pi / 2.0 + i * math.pi / 4.0
        r = radius if i % 2 == 0 else radius * 0.34
        points.append((x + math.cos(angle) * r, y + math.sin(angle) * r))
    _polygon(draw, points, color, None, 0.0)


def _orbit_point(center: Point, rx: float, ry: float, phase: float) -> Point:
    angle = math.tau * phase
    return (center[0] + math.cos(angle) * rx, center[1] + math.sin(angle) * ry)


def _draw_ability_effects_behind(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    center = T((64.0, 66.0))
    if pose.cosmic_trail > 0.02:
        for i in range(9):
            f = i / 8.0
            x = center[0] - 16.0 - 48.0 * f
            y = center[1] - 12.0 + 24.0 * math.sin((f + pose.orbit_phase) * math.tau) * (0.2 + 0.45 * f)
            _draw_star(draw, (x, y), 1.1 + 1.4 * (1.0 - f), STAR_GOLD if i % 2 else STAR_WHITE, pose.cosmic_trail * (1.0 - 0.65 * f))
            _line(draw, [(x + 2.0, y), (x + 8.0 + 14.0 * f, y)], _fade(NEBULA_BLUE, pose.cosmic_trail * 0.35 * (1.0 - f)), 0.65)

    if pose.orbit > 0.02:
        alpha = 0.25 + 0.55 * pose.orbit
        _arc(draw, center, 31.0, 20.0, 190, 350, _fade(NEBULA_BLUE, alpha), 1.4)
        _arc(draw, center, 25.0, 34.0, 100, 270, _fade(STAR_GOLD, alpha * 0.75), 1.1)

    if pose.calendar > 0.02:
        radius = 37.0
        alpha = 0.20 + 0.62 * pose.calendar
        _arc(draw, center, radius, radius, 145, 395, _fade(STAR_GOLD, alpha), 1.4)
        for i in range(12):
            angle = math.radians(145.0 + (250.0 * i / 11.0))
            inner = (center[0] + math.cos(angle) * (radius - 3.0), center[1] + math.sin(angle) * (radius - 3.0))
            outer = (center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius)
            _line(draw, [inner, outer], _fade(STAR_WHITE, alpha * (0.45 + 0.55 * i / 11.0)), 0.8)

    if pose.pale_dot > 0.02:
        alpha = pose.pale_dot
        _ellipse(draw, center, 28.0, 34.0, _fade(COSMIC_DARK, 0.14 * alpha), None, 0.0)
        _arc(draw, center, 31.0, 37.0, 205, 335, _fade(NEBULA_VIOLET, 0.50 * alpha), 1.5)
        _arc(draw, center, 23.0, 29.0, 200, 340, _fade(NEBULA_BLUE, 0.55 * alpha), 1.0)

    if pose.billions > 0.02 or pose.starstuff > 0.02:
        amount = max(pose.billions, pose.starstuff)
        for i in range(24):
            angle = i * 2.399963229728653 + pose.orbit_phase * math.tau
            radius = (5.0 + (i % 7) * 4.8) * (0.28 + 0.72 * amount)
            squash = 0.58 + 0.12 * math.sin(i * 1.7)
            q = (center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius * squash)
            color = (STAR_WHITE, STAR_GOLD, NEBULA_BLUE, NEBULA_VIOLET)[i % 4]
            _draw_star(draw, q, 0.85 + (i % 3) * 0.35, color, amount * (0.40 + 0.55 * ((i % 5) / 4.0)))


def _draw_ability_effects_front(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    center = T((64.0, 66.0))
    if pose.orbit > 0.02:
        _arc(draw, center, 31.0, 20.0, 10, 170, _fade(NEBULA_BLUE, 0.35 + 0.55 * pose.orbit), 1.7)
        _arc(draw, center, 25.0, 34.0, 280, 455, _fade(STAR_GOLD, 0.32 + 0.48 * pose.orbit), 1.25)
        planet = _orbit_point(center, 31.0 + 30.0 * pose.orbit_release, 20.0, pose.orbit_phase + 0.08)
        pr = 3.2 + 1.2 * pose.orbit
        _ellipse(draw, planet, pr, pr, PLANET_OCHRE, OUTLINE_SOFT, 0.65)
        _arc(draw, planet, pr * 1.45, pr * 0.55, 178, 358, _fade(STAR_GOLD, 0.85), 0.9)
        _ellipse(draw, (planet[0] - pr * 0.35, planet[1] - pr * 0.25), pr * 0.22, pr * 0.17, PLANET_RUST, None, 0.0)

    if pose.pale_dot > 0.02:
        hand = T(pose.near_hand)
        dot = (hand[0] + 8.0 + 24.0 * max(0.0, pose.pale_dot - 0.62) / 0.38, hand[1] - 1.0)
        _line(draw, [center, dot], _fade(NEBULA_BLUE, 0.16 * pose.pale_dot), 8.0)
        _line(draw, [hand, dot], _fade(STAR_WHITE, 0.80 * pose.pale_dot), 1.15)
        _ellipse(draw, dot, 1.8, 1.8, PALE_BLUE, STAR_WHITE, 0.55)
        _ellipse(draw, dot, 5.0, 5.0, _fade(PALE_BLUE, 0.16 * pose.pale_dot), None, 0.0)

    if pose.calendar > 0.02:
        angle = math.radians(145.0 + 250.0 * pose.calendar)
        end = (center[0] + math.cos(angle) * 37.0, center[1] + math.sin(angle) * 37.0)
        _line(draw, [center, end], _fade(STAR_WHITE, 0.72 * pose.calendar), 1.2)
        _draw_star(draw, end, 2.4, STAR_GOLD, pose.calendar)
        hand = T(pose.near_hand)
        _line(draw, [hand, end], _fade(NEBULA_VIOLET, 0.48 * pose.calendar), 0.9)

    if pose.billions > 0.02:
        for hand, sign in ((T(pose.far_hand), -1.0), (T(pose.near_hand), 1.0)):
            for i in range(7):
                spread = pose.billions
                x = hand[0] + sign * (4.0 + 4.8 * i) * spread
                y = hand[1] + math.sin(i * 2.1 + pose.orbit_phase * math.tau) * (2.0 + 7.0 * spread)
                _draw_star(draw, (x, y), 0.9 + 0.22 * i, STAR_WHITE if i % 2 == 0 else STAR_GOLD, 0.35 + 0.65 * spread)

    if pose.starstuff > 0.02:
        # A front spiral arm crosses the body, making the transformation read as
        # volumetric rather than a decorative ring behind him.
        pts: List[Point] = []
        for i in range(22):
            f = i / 21.0
            angle = pose.orbit_phase * math.tau + f * math.tau * 1.6
            radius = 4.0 + 31.0 * f
            pts.append((center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius * 0.48))
        _line(draw, pts, _fade(NEBULA_BLUE, 0.58 * pose.starstuff), 1.6)
        for i in (3, 7, 12, 17, 21):
            _draw_star(draw, pts[i], 1.4 + 0.08 * i, STAR_WHITE if i % 2 else STAR_GOLD, pose.starstuff)


def _render_native_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    """Render one frame at native supersampled resolution.

    Translucent ability work is isolated on scratch layers and composited; this
    avoids Pillow's RGBA alpha-replacement trap when effects cross opaque art.
    """
    pose = _pose(animation, frame_idx, nframes)
    size = (FRAME_W * SUPER, FRAME_H * SUPER)
    behind = Image.new("RGBA", size, (0, 0, 0, 0))
    body = Image.new("RGBA", size, (0, 0, 0, 0))
    front = Image.new("RGBA", size, (0, 0, 0, 0))

    _draw_ability_effects_behind(ImageDraw.Draw(behind, "RGBA"), pose)
    draw = ImageDraw.Draw(body, "RGBA")
    _draw_leg(draw, pose, pose.far_hip, pose.far_knee, pose.far_ankle, far=True)
    _draw_leg(draw, pose, pose.near_hip, pose.near_knee, pose.near_ankle, far=False)
    _draw_torso(draw, pose)
    _draw_arm(draw, pose, pose.far_shoulder, pose.far_elbow, pose.far_hand, pose.far_hand_mode, far=True)
    _draw_arm(draw, pose, pose.near_shoulder, pose.near_elbow, pose.near_hand, pose.near_hand_mode, far=False)
    _draw_head(draw, pose)
    _draw_ability_effects_front(ImageDraw.Draw(front, "RGBA"), pose)

    return Image.alpha_composite(Image.alpha_composite(behind, body), front)


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _render_native_frame(animation, frame_idx, nframes).resize(
        (FRAME_W, FRAME_H), Image.Resampling.LANCZOS
    )


PORTRAIT_SIZE = (256, 320)
PORTRAIT_SUPER = 4


def _render_native_portrait(expression: str, phase: float = 0.0) -> Image.Image:
    """Draw a bespoke dialog portrait from native vector-like geometry.

    This is not a gameplay-sheet crop. The portrait has its own composition and
    detail budget while sharing Carl's palette, anatomy, clothing, and expression
    model with the sprite target.
    """
    scale = PORTRAIT_SUPER
    width, height = PORTRAIT_SIZE
    size = (width * scale, height * scale)

    def P(point: Point) -> Tuple[int, int]:
        return (int(round(point[0] * scale)), int(round(point[1] * scale)))

    def B(box: Tuple[float, float, float, float]) -> Tuple[int, int, int, int]:
        return tuple(int(round(value * scale)) for value in box)  # type: ignore[return-value]

    def poly(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, outline: RGBA | None = None, line_width: float = 1.0) -> None:
        pts = [P(point) for point in points]
        draw.polygon(pts, fill=fill)
        if outline is not None:
            draw.line(pts + [pts[0]], fill=outline, width=max(1, int(round(line_width * scale))), joint="curve")

    def line(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, line_width: float = 1.0) -> None:
        draw.line([P(point) for point in points], fill=fill, width=max(1, int(round(line_width * scale))), joint="curve")

    def ellipse(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, fill: RGBA, outline: RGBA | None = None, line_width: float = 1.0) -> None:
        box = (center[0] - rx, center[1] - ry, center[0] + rx, center[1] + ry)
        draw.ellipse(B(box), fill=fill, outline=outline, width=max(1, int(round(line_width * scale))) if outline else 1)

    def arc(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, start: float, end: float, fill: RGBA, line_width: float = 1.0) -> None:
        box = (center[0] - rx, center[1] - ry, center[0] + rx, center[1] + ry)
        draw.arc(B(box), start=start, end=end, fill=fill, width=max(1, int(round(line_width * scale))))

    def star(draw: ImageDraw.ImageDraw, center: Point, radius: float, color: RGBA) -> None:
        points: List[Point] = []
        for index in range(8):
            angle = -math.pi / 2.0 + index * math.pi / 4.0
            r = radius if index % 2 == 0 else radius * 0.34
            points.append((center[0] + math.cos(angle) * r, center[1] + math.sin(angle) * r))
        poly(draw, points, color)

    expression_phase = phase % 1.0
    talk = expression == "explaining"
    wonder = expression in {"wonder", "pale_blue_dot"}
    skeptical = expression == "skeptical"
    mouth_open = 0.0
    if talk:
        mouth_open = 0.18 + 0.72 * max(0.0, math.sin(expression_phase * math.tau))
    elif wonder:
        mouth_open = 0.16 + 0.16 * max(0.0, math.sin(expression_phase * math.tau))

    behind = Image.new("RGBA", size, (0, 0, 0, 0))
    body = Image.new("RGBA", size, (0, 0, 0, 0))
    front = Image.new("RGBA", size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(behind, "RGBA")
    d = ImageDraw.Draw(body, "RGBA")
    fd = ImageDraw.Draw(front, "RGBA")

    if wonder:
        arc(bd, (128.0, 182.0), 91.0, 112.0, 196, 344, _fade(NEBULA_BLUE, 0.72), 4.0)
        arc(bd, (128.0, 181.0), 76.0, 100.0, 202, 338, _fade(NEBULA_VIOLET, 0.58), 2.4)
        for index in range(13):
            angle = 0.48 + index * 0.49 + expression_phase * 0.7
            radius = 78.0 + (index % 4) * 9.0
            star(
                bd,
                (128.0 + math.cos(angle) * radius, 165.0 + math.sin(angle) * radius * 0.58),
                1.8 + (index % 3) * 0.8,
                _fade(STAR_WHITE if index % 2 else STAR_GOLD, 0.70),
            )
    elif skeptical:
        arc(bd, (128.0, 198.0), 86.0, 105.0, 208, 332, _fade(JACKET_DEEP, 0.24), 2.0)

    # Shoulders and jacket body.
    poly(d, [(18, 320), (25, 238), (55, 205), (91, 190), (165, 190), (202, 205), (232, 238), (240, 320)], JACKET_DARK, OUTLINE, 4.0)
    poly(d, [(24, 320), (31, 242), (63, 210), (112, 194), (122, 320)], JACKET, OUTLINE_SOFT, 2.0)
    poly(d, [(134, 194), (194, 210), (225, 242), (235, 320), (128, 320)], JACKET_LIGHT, OUTLINE_SOFT, 2.0)

    # Neck and turtleneck collar.
    poly(d, [(105, 163), (151, 163), (154, 211), (102, 211)], SKIN, OUTLINE, 3.0)
    poly(d, [(97, 192), (159, 192), (166, 231), (128, 253), (90, 231)], TURTLENECK, OUTLINE, 3.0)
    arc(d, (128, 203), 31, 15, 188, 352, TURTLENECK_LIGHT, 2.0)

    # Ears behind the face.
    ellipse(d, (76, 111), 14, 25, SKIN, OUTLINE, 3.0)
    ellipse(d, (180, 109), 13, 24, SKIN_LIGHT, OUTLINE, 3.0)
    arc(d, (76, 112), 7, 15, 275, 80, SKIN_SHADE, 1.6)
    arc(d, (179, 110), 6, 14, 100, 260, SKIN_SHADE, 1.4)

    # Long but soft face with a broad forehead and tapered chin.
    face = [(83, 68), (99, 48), (128, 41), (157, 49), (175, 70), (180, 106), (171, 143), (151, 170), (128, 181), (103, 171), (84, 146), (75, 111)]
    poly(d, face, SKIN, OUTLINE, 4.0)
    poly(d, [(83, 71), (101, 53), (104, 157), (86, 143), (76, 111)], (158, 99, 73, 255))
    poly(d, [(151, 53), (173, 72), (179, 106), (169, 139), (151, 157)], (199, 141, 103, 255))
    ellipse(d, (101, 136), 15, 9, (190, 121, 89, 255))
    ellipse(d, (155, 136), 15, 9, (207, 148, 108, 255))

    # Hair cap first, then irregular swept curls. The left-front wave is the
    # signature shape and avoids the helmet-like symmetry of generic sprites.
    hair_cap = [(75, 99), (69, 76), (75, 49), (92, 26), (116, 16), (143, 18), (166, 31), (184, 53), (187, 78), (178, 92), (163, 76), (148, 67), (128, 65), (108, 69), (92, 82)]
    poly(d, hair_cap, HAIR, OUTLINE, 3.5)
    curls = [
        ((84, 51), 18, 16), ((101, 31), 20, 15), ((124, 24), 21, 14),
        ((148, 28), 20, 15), ((168, 43), 18, 17), ((178, 65), 15, 19),
        ((78, 76), 16, 22), ((94, 70), 18, 18),
    ]
    for center, rx, ry in curls:
        ellipse(d, center, rx, ry, HAIR, OUTLINE_SOFT, 1.5)
    poly(d, [(74, 55), (88, 37), (111, 33), (103, 54), (91, 73), (77, 84)], HAIR_MID, OUTLINE_SOFT, 1.3)
    arc(d, (126, 28), 36, 14, 192, 350, HAIR_GLEAM, 2.0)
    arc(d, (158, 42), 21, 15, 180, 333, HAIR_GLEAM, 1.7)
    arc(d, (88, 58), 15, 22, 266, 70, HAIR_GLEAM, 1.5)

    # Eyebrows and eyes: expressive without the oversized worried-eye look.
    left_brow = 87.0 + (5.0 if skeptical else 0.0) - (2.0 if wonder else 0.0)
    right_brow = 86.0 - (5.0 if skeptical else 0.0) - (2.0 if wonder else 0.0)
    line(d, [(94, left_brow + 2), (107, left_brow - 1), (119, left_brow + 1)], HAIR, 3.4)
    line(d, [(137, right_brow + 1), (149, right_brow - 1), (162, right_brow + 2)], HAIR, 3.4)
    eye_ry = 4.8 + (1.0 if wonder else 0.0)
    ellipse(d, (108, 101), 9.5, eye_ry, EYE_LIGHT, OUTLINE, 1.8)
    ellipse(d, (149, 100), 9.8, eye_ry, EYE_LIGHT, OUTLINE, 1.8)
    ellipse(d, (109, 101), 3.7, 4.2, EYE, None)
    ellipse(d, (150, 100), 3.7, 4.2, EYE, None)
    ellipse(d, (110.5, 99.7), 1.0, 1.0, STAR_WHITE, None)
    ellipse(d, (151.5, 98.7), 1.0, 1.0, STAR_WHITE, None)
    arc(d, (108, 105), 9.0, 4.2, 12, 168, SKIN_SHADE, 1.0)
    arc(d, (149, 104), 9.0, 4.2, 12, 168, SKIN_SHADE, 1.0)

    # Prominent nose with a warm lit bridge, nostril definition, and soft tip.
    line(d, [(128, 98), (126, 122), (120, 137), (124, 141)], SKIN_SHADE, 2.2)
    line(d, [(132, 100), (135, 124), (139, 136)], SKIN_HIGHLIGHT, 1.6)
    arc(d, (130, 139), 11, 6, 10, 174, OUTLINE_SOFT, 1.5)
    ellipse(d, (123, 140), 1.7, 1.2, OUTLINE_SOFT, None)
    ellipse(d, (138, 139), 1.7, 1.2, OUTLINE_SOFT, None)

    # Mouth and smile lines.
    if mouth_open > 0.08:
        ellipse(d, (130, 157), 13.0 + 2.0 * mouth_open, 3.8 + 8.0 * mouth_open, MOUTH, OUTLINE, 2.0)
        if mouth_open > 0.42:
            arc(d, (130, 160), 8.0, 4.0, 190, 350, (225, 151, 130, 255), 1.2)
    else:
        arc(d, (130, 155), 15.0, 8.0, 12, 168, MOUTH, 2.2)
    arc(d, (108, 151), 10, 11, 302, 64, (153, 93, 70, 255), 1.0)
    arc(d, (151, 151), 10, 11, 116, 238, (190, 127, 93, 255), 1.0)
    line(d, [(121, 171), (139, 172)], (151, 91, 69, 255), 1.2)

    # Wide lapels and corduroy ribs are redrawn over the shoulder mass.
    poly(d, [(62, 209), (101, 192), (119, 221), (90, 283), (37, 239)], JACKET_LIGHT, OUTLINE_SOFT, 2.2)
    poly(d, [(154, 193), (195, 210), (219, 239), (165, 282), (137, 220)], JACKET, OUTLINE_SOFT, 2.2)
    for x in (48, 58, 69, 80):
        line(d, [(x, 235), (x + 25, 313)], JACKET_DEEP, 1.0)
    for x in (178, 189, 200, 211):
        line(d, [(x, 230), (x - 25, 313)], JACKET_DEEP, 1.0)

    # Expression-specific hands enter from the crop edges, supporting the face
    # rather than becoming permanent props.
    if talk or wonder:
        hand_bob = 4.0 * math.sin(expression_phase * math.tau)
        # Right sleeve and forearm connect the gesture to the shoulder instead
        # of leaving a floating hand at the crop edge.
        poly(d, [(183, 217), (199, 211), (226, 232 + hand_bob), (216, 257 + hand_bob), (194, 247)], JACKET_LIGHT, OUTLINE, 2.4)
        poly(d, [(215, 254 + hand_bob), (224, 232 + hand_bob), (237, 224 + hand_bob), (249, 233 + hand_bob), (244, 246 + hand_bob), (225, 263 + hand_bob)], SKIN_LIGHT, OUTLINE, 2.2)
        for offset in range(4):
            x = 234 + offset * 3.0
            line(d, [(x, 231 + hand_bob - offset), (x + 7.0, 221 + hand_bob - offset * 2.6)], OUTLINE_SOFT, 0.95)
        if wonder:
            poly(d, [(72, 217), (57, 211), (29, 232 + hand_bob), (40, 257 + hand_bob), (62, 247)], JACKET, OUTLINE, 2.4)
            poly(d, [(41, 254 + hand_bob), (31, 232 + hand_bob), (18, 224 + hand_bob), (6, 233 + hand_bob), (12, 246 + hand_bob), (31, 263 + hand_bob)], SKIN_LIGHT, OUTLINE, 2.2)
            for offset in range(4):
                x = 22 - offset * 3.0
                line(d, [(x, 231 + hand_bob - offset), (x - 7.0, 221 + hand_bob - offset * 2.6)], OUTLINE_SOFT, 0.95)

    if expression == "pale_blue_dot":
        dot = (218.0 + 5.0 * math.sin(expression_phase * math.tau), 210.0)
        line(fd, [(184, 224), dot], _fade(STAR_WHITE, 0.82), 1.8)
        ellipse(fd, dot, 3.4, 3.4, PALE_BLUE, STAR_WHITE, 1.0)
        ellipse(fd, dot, 13.0, 13.0, _fade(PALE_BLUE, 0.16), None)

    return Image.alpha_composite(Image.alpha_composite(behind, body), front).resize(PORTRAIT_SIZE, Image.Resampling.LANCZOS)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    """Publish bespoke native portraits through the standard named-clip API."""
    del opts
    clips = {
        "default": PortraitClip.still(_render_native_portrait("default")),
        "explaining": PortraitClip(
            tuple(_render_native_portrait("explaining", frame / 8.0) for frame in range(8)),
            duration_ms=108,
            looping=True,
        ),
        "wonder": PortraitClip(
            tuple(_render_native_portrait("wonder", frame / 6.0) for frame in range(6)),
            duration_ms=124,
            looping=True,
        ),
        "skeptical": PortraitClip.still(_render_native_portrait("skeptical")),
        "pale_blue_dot": PortraitClip(
            tuple(_render_native_portrait("pale_blue_dot", frame / 6.0) for frame in range(6)),
            duration_ms=132,
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
            "planetary_orbit": {"bbox": {"x": 72, "y": 40, "w": 55, "h": 54}},
            "pale_blue_dot": {"bbox": {"x": 86, "y": 42, "w": 41, "h": 40}},
            "cosmic_calendar": {"bbox": {"x": 22, "y": 23, "w": 84, "h": 86}},
            "billions_and_billions": {"bbox": {"x": 13, "y": 26, "w": 111, "h": 75}},
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
