"""Procedural full-action renderer for Joseph Furrier.

Joseph Furrier is a bundled-up harmonic eccentric whose oversized blanket is
both his signature silhouette and the affectionate biographical joke at the
center of the parody. The blanket stays visually dominant in ordinary movement;
stair-step geometry belongs only to selected gameplay actions, where it reads as
a discrete/stepwise Fourier homage rather than as a biographical prop.

The character is intentionally human rather than a literal fox. The "Furrier"
pun appears in the thick fur-trimmed blanket, which opens during attacks to
reveal spectral embroidery and separated bands of harmonic color. His dark,
slightly nocturnal presentation remains playful: he looks cold, private, and
absorbed in signals that nobody else can hear, not monstrous.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ...authoring.sheet_build import build_sheet, write_canonical
from ...core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "joseph_furrier"
FRAME_W = 128
FRAME_H = 128
SUPER = 4
USES_DROP_SHADOW = False
USES_PROPS = False

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 145),
    ("walk", 8, 106),
    ("run", 8, 78),
    ("crouch", 6, 96),
    ("crouch_walk", 8, 90),
    ("jump", 6, 92),
    ("fall", 6, 92),
    ("land_hard", 8, 88),
    ("land_recovery", 6, 72),
    ("dash_startup", 4, 48),
    ("dash", 6, 60),
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
    ("blanket_snap", 7, 62),
    ("step_function", 8, 70),
    ("harmonic_split", 8, 74),
    ("low_pass_lament", 8, 82),
    ("spectral_descent", 8, 72),
    ("air_neutral", 8, 62),
    ("air_forward", 7, 60),
    ("air_back", 7, 60),
    ("air_down", 7, 68),
    ("air_up", 7, 60),
    ("full_turn", 10, 72),
    ("celebrate", 8, 88),
    ("taunt", 8, 96),
]

authoring_description = (
    "Joseph Furrier is a transformative parody of French mathematician and "
    "physicist Joseph Fourier. The oversized blanket is inspired by the "
    "commonly repeated biographical anecdote that Fourier habitually kept "
    "himself heavily wrapped for warmth; Ambition exaggerates that private "
    "eccentricity into his permanent bundled silhouette. The name's furrier "
    "pun is expressed through the blanket's thick trim rather than by turning "
    "Fourier into an animal. Stair shapes are deliberately limited to the "
    "step_function and spectral_descent gameplay actions: they are a game-facing "
    "homage to stepwise/discrete approximation and platforming, not another "
    "claim about Fourier's life. The spectral lining, separated color bands, "
    "wave attacks, and low-pass defensive posture draw on Fourier analysis, "
    "frequency decomposition, and filtering. The overall tone is dark, cold, "
    "and eccentric, but affectionate rather than horrific."
)

ACTOR_METADATA = {
    "authoring_description": authoring_description,
    "actor": {
        "character_id": "npc_joseph_furrier",
        "display_name": "Joseph Furrier",
    },
    "lineage": {
        "family": "joseph_furrier",
        "variant": "blanket_harmonic_eccentric",
        "creator": {"kind": "model", "model": "GPT-5.6 Thinking"},
        "method": "procedural_python_pillow",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "mathematician",
            "blanket_wrapped",
            "harmonic_caster",
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
        "blanket_wrapped",
        "harmonic_caster",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 29.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 64.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 48.0, "y": 73.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 82.0, "y": 73.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 5.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "blanket_snap", "events": []},
        "action.ranged.primary": {"animation": "harmonic_split", "events": []},
        "action.special.primary": {"animation": "step_function", "events": []},
        "action.special.secondary": {"animation": "spectral_descent", "events": []},
        "action.defense.block": {"animation": "low_pass_lament", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}

OUTLINE = (18, 18, 24, 255)
OUTLINE_SOFT = (48, 47, 59, 255)
SKIN = (204, 164, 132, 255)
SKIN_LIGHT = (232, 198, 166, 255)
SKIN_SHADE = (154, 111, 91, 255)
HAIR = (55, 48, 51, 255)
HAIR_LIGHT = (95, 82, 83, 255)
EYE = (26, 23, 26, 255)
MOUTH = (118, 67, 65, 255)
SHIRT = (220, 214, 193, 255)
SHIRT_SHADE = (174, 164, 143, 255)
TROUSER = (44, 46, 57, 255)
TROUSER_LIGHT = (69, 72, 88, 255)
SHOE = (63, 44, 38, 255)
SHOE_LIGHT = (98, 68, 54, 255)
BLANKET = (42, 45, 62, 255)
BLANKET_LIGHT = (67, 71, 94, 255)
BLANKET_DARK = (28, 30, 43, 255)
BLANKET_DEEP = (19, 20, 30, 255)
LINING = (93, 39, 57, 255)
LINING_LIGHT = (142, 59, 78, 255)
FUR = (180, 170, 149, 255)
FUR_LIGHT = (221, 212, 193, 255)
FUR_DARK = (126, 117, 104, 255)
GOLD = (218, 176, 83, 255)
GOLD_LIGHT = (247, 220, 145, 255)
SPECTRAL_BLUE = (83, 177, 217, 255)
SPECTRAL_TEAL = (87, 201, 177, 255)
SPECTRAL_VIOLET = (150, 112, 203, 255)
SPECTRAL_RED = (205, 82, 100, 255)
DAMP_FIELD = (83, 105, 141, 255)


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


def _fade(color: RGBA, alpha: float) -> RGBA:
    return (color[0], color[1], color[2], int(round(color[3] * _clamp01(alpha))))


def _polygon(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    pts = [_pt(point) for point in points]
    draw.polygon(pts, fill=fill)
    if outline is not None:
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


@dataclass
class Pose:
    root_x: float = 0.0
    root_y: float = 0.0
    bob: float = 0.0
    lean: float = 0.0
    rotation: float = 0.0
    rotation_pivot: Point = (64.0, 82.0)
    crouch: float = 0.0
    head_x: float = 0.0
    head_y: float = 0.0
    head_tilt: float = 0.0
    blink: bool = False
    mouth_open: float = 0.0
    brow: float = 0.0
    blanket_open: float = 0.0
    blanket_wrap: float = 0.0
    blanket_sway: float = 0.0
    blanket_flare: float = 0.0
    near_shoulder: Point = (79.0, 51.0)
    near_elbow: Point = (82.0, 66.0)
    near_hand: Point = (76.0, 72.0)
    far_shoulder: Point = (49.0, 51.0)
    far_elbow: Point = (46.0, 66.0)
    far_hand: Point = (52.0, 72.0)
    near_hip: Point = (69.0, 96.0)
    near_knee: Point = (72.0, 106.0)
    near_ankle: Point = (73.0, 117.0)
    far_hip: Point = (59.0, 96.0)
    far_knee: Point = (57.0, 106.0)
    far_ankle: Point = (56.0, 117.0)
    step: float = 0.0
    harmonic: float = 0.0
    damping: float = 0.0
    descent: float = 0.0
    snap: float = 0.0
    turn: float = 0.0
    celebrate: float = 0.0


def _pose(animation: str, frame_idx: int, nframes: int) -> Pose:
    phase = frame_idx / float(max(1, nframes))
    t = 0.0 if nframes <= 1 else frame_idx / float(nframes - 1)
    wave = math.sin(phase * math.tau)
    cosine = math.cos(phase * math.tau)
    p = Pose()

    def standing_legs(stride: float = 0.0, lift: float = 0.0) -> None:
        p.near_hip = (69.0, 96.0)
        p.far_hip = (59.0, 96.0)
        p.near_knee = (70.0 - stride * 0.35, 106.0 - max(0.0, lift) * 2.5)
        p.far_knee = (58.0 + stride * 0.30, 106.0 - max(0.0, -lift) * 2.5)
        p.near_ankle = (73.0 + stride, 117.0 - max(0.0, lift) * 5.0)
        p.far_ankle = (55.0 - stride, 117.0 - max(0.0, -lift) * 5.0)

    def arms_tucked() -> None:
        p.near_shoulder = (79.0, 51.0)
        p.near_elbow = (81.0, 64.0)
        p.near_hand = (73.5, 69.0)
        p.far_shoulder = (49.0, 51.0)
        p.far_elbow = (47.0, 64.0)
        p.far_hand = (54.5, 69.0)

    standing_legs()
    arms_tucked()

    if animation == "idle":
        p.bob = wave * 0.8
        p.blanket_sway = wave * 0.8
        p.blink = frame_idx in {3, 4}
        p.head_tilt = cosine * 0.7
    elif animation in {"walk", "crouch_walk"}:
        stride = wave * (8.0 if animation == "walk" else 5.0)
        standing_legs(stride, cosine)
        p.bob = abs(cosine) * 1.1
        p.lean = 1.5
        p.blanket_sway = -wave * 3.0
        if animation == "crouch_walk":
            p.crouch = 0.75
            p.root_y = 7.0
            p.blanket_flare = 0.25
    elif animation == "run":
        stride = wave * 12.0
        standing_legs(stride, cosine * 1.3)
        p.bob = abs(cosine) * 2.0
        p.lean = 6.0
        p.blanket_sway = -wave * 5.0
        p.blanket_flare = 0.35
    elif animation == "crouch":
        p.crouch = 0.85
        p.root_y = 8.0
        p.blanket_wrap = 0.35 + 0.08 * wave
    elif animation in {"jump", "wall_jump"}:
        lift = _pulse(t)
        p.root_y = -5.0 * lift
        p.lean = 3.0 if animation == "jump" else -6.0
        p.blanket_flare = 0.55 * lift
        p.near_ankle = (73.0, 108.0 - 5.0 * lift)
        p.far_ankle = (55.0, 110.0 - 4.0 * lift)
        if animation == "wall_jump":
            p.rotation = -10.0 * _pulse(t)
    elif animation == "fall":
        p.root_y = -4.0 + 4.0 * t
        p.blanket_flare = 0.42
        p.blanket_sway = -2.0
        p.near_ankle = (71.0, 111.0)
        p.far_ankle = (57.0, 110.0)
    elif animation in {"land_hard", "land_recovery"}:
        amount = (1.0 - t) if animation == "land_recovery" else _pulse(t)
        p.crouch = 0.9 * amount
        p.root_y = 8.0 * amount
        p.blanket_flare = 0.35 * amount
    elif animation == "dash_startup":
        p.lean = 10.0 * _smooth(t)
        p.crouch = 0.25 * _smooth(t)
        p.root_y = 2.0 * _smooth(t)
        p.blanket_sway = -4.0 * _smooth(t)
    elif animation == "dash":
        p.lean = 12.0
        p.root_x = wave * 1.2
        p.blanket_sway = -7.0 + wave * 2.0
        p.blanket_flare = 0.42
        standing_legs(wave * 10.0, cosine)
    elif animation == "slide":
        p.crouch = 1.0
        p.root_y = 11.0
        p.lean = 12.0
        p.blanket_sway = -6.0
        p.blanket_flare = 0.5
        p.near_ankle = (86.0, 118.0)
        p.far_ankle = (51.0, 116.0)
    elif animation in {"roll", "ledge_roll"}:
        p.crouch = 1.0
        p.root_y = -2.0
        p.blanket_wrap = 0.85
        p.rotation = math.sin(t * math.tau) * 34.0
        p.rotation_pivot = (64.0, 79.0)
        p.near_ankle = (75.0, 105.0)
        p.far_ankle = (54.0, 105.0)
    elif animation in {"wall_grab", "ledge_grab"}:
        p.lean = -7.0
        p.root_x = -5.0
        p.near_hand = (44.0, 43.0)
        p.far_hand = (43.0, 56.0)
        p.near_elbow = (55.0, 52.0)
        p.far_elbow = (53.0, 62.0)
        p.near_ankle = (55.0, 111.0)
        p.far_ankle = (51.0, 104.0)
        p.blanket_open = 0.2
    elif animation in {"ledge_climb", "ledge_getup", "climb"}:
        climb = _smooth(t)
        p.root_y = 1.0 - 5.0 * climb if animation != "climb" else wave * 3.0
        p.near_hand = (53.0, 42.0 + wave * 4.0)
        p.far_hand = (76.0, 46.0 - wave * 4.0)
        p.near_elbow = (59.0, 54.0)
        p.far_elbow = (70.0, 56.0)
        p.blanket_open = 0.25
        p.blanket_sway = wave * 2.0
    elif animation == "swim":
        p.rotation = wave * 4.0
        p.root_y = -1.0 + wave * 1.5
        p.blanket_flare = 0.65
        p.blanket_open = 0.35
        p.near_hand = (91.0, 65.0 + wave * 5.0)
        p.far_hand = (39.0, 65.0 - wave * 5.0)
        p.near_elbow = (82.0, 56.0)
        p.far_elbow = (48.0, 56.0)
        p.near_ankle = (78.0, 107.0)
        p.far_ankle = (50.0, 109.0)
    elif animation == "float_glide":
        p.root_y = -3.0 + wave * 1.2
        p.blanket_open = 0.85
        p.blanket_flare = 0.85
        p.near_hand = (96.0, 65.0)
        p.far_hand = (32.0, 65.0)
        p.near_elbow = (84.0, 57.0)
        p.far_elbow = (44.0, 57.0)
        p.near_ankle = (72.0, 110.0)
        p.far_ankle = (57.0, 110.0)
    elif animation == "block":
        p.blanket_wrap = 0.9
        p.crouch = 0.25
        p.root_y = 2.0
        p.near_hand = (72.0, 54.0)
        p.far_hand = (56.0, 54.0)
    elif animation == "hit":
        impact = _pulse(t)
        p.lean = -10.0 * impact
        p.root_x = -5.0 * impact
        p.head_tilt = -8.0 * impact
        p.blanket_sway = 6.0 * impact
        p.blanket_open = 0.25 * impact
        p.mouth_open = impact
    elif animation == "death":
        fall = _smooth(t)
        p.rotation = 78.0 * fall
        p.root_x = -8.0 * fall
        p.root_y = -4.0 * fall
        p.rotation_pivot = (64.0, 79.0)
        p.blanket_open = 0.25 * fall
        p.mouth_open = 0.25
    elif animation == "talk":
        p.mouth_open = 0.65 if frame_idx % 3 else 0.1
        p.brow = wave * 0.8
        p.blanket_open = 0.18
        p.near_elbow = (84.0, 63.0)
        p.near_hand = (91.0, 58.0 + wave * 3.0)
    elif animation == "interact":
        reach = _pulse(t)
        p.blanket_open = 0.35 * reach
        p.near_elbow = _lerp_point((81.0, 64.0), (89.0, 60.0), reach)
        p.near_hand = _lerp_point((73.5, 69.0), (104.0, 60.0), reach)
        p.lean = 3.0 * reach
    elif animation == "blanket_snap":
        attack = _pulse(t)
        p.snap = attack
        p.blanket_open = 0.95 * attack
        p.blanket_flare = 0.65 * attack
        p.lean = 5.0 * attack
        p.near_elbow = (87.0, 57.0)
        p.near_hand = (90.0, 54.0)
        p.far_elbow = (43.0, 61.0)
        p.far_hand = (31.0, 62.0)
    elif animation == "step_function":
        cast = _pulse(t)
        p.step = cast
        p.blanket_open = 0.45 * cast
        p.near_elbow = (85.0, 58.0)
        p.near_hand = (91.0, 49.0 - 4.0 * cast)
        p.lean = 2.0 * cast
    elif animation == "harmonic_split":
        cast = _pulse(t)
        p.harmonic = cast
        p.blanket_open = 0.78 * cast
        p.near_hand = (96.0, 60.0)
        p.near_elbow = (87.0, 58.0)
        p.far_hand = (36.0, 62.0)
        p.far_elbow = (45.0, 59.0)
    elif animation == "low_pass_lament":
        cast = _pulse(t)
        p.damping = cast
        p.blanket_wrap = 0.8 * cast
        p.crouch = 0.15 * cast
        p.near_hand = (72.0, 57.0)
        p.far_hand = (56.0, 57.0)
    elif animation == "spectral_descent":
        cast = _pulse(t)
        p.descent = cast
        p.step = cast
        p.root_y = -4.0 * cast + 2.0 * t
        p.blanket_flare = 0.55 * cast
        p.near_hand = (93.0, 48.0)
        p.near_elbow = (83.0, 57.0)
    elif animation.startswith("air_"):
        attack = _pulse(t)
        p.root_y = -5.0
        p.blanket_flare = 0.5
        p.blanket_open = 0.35 * attack
        if animation == "air_neutral":
            p.rotation = math.sin(t * math.tau) * 16.0
            p.snap = 0.55 * attack
        elif animation == "air_forward":
            p.near_hand = (91.0, 58.0)
            p.near_elbow = (88.0, 58.0)
            p.snap = attack
        elif animation == "air_back":
            p.far_hand = (28.0, 58.0)
            p.far_elbow = (43.0, 58.0)
            p.snap = attack
        elif animation == "air_down":
            p.near_hand = (77.0, 100.0)
            p.near_elbow = (78.0, 78.0)
            p.step = 0.6 * attack
        elif animation == "air_up":
            p.near_hand = (74.0, 22.0)
            p.near_elbow = (77.0, 42.0)
            p.harmonic = 0.55 * attack
    elif animation == "full_turn":
        p.turn = _pulse(t)
        p.rotation = math.sin(t * math.tau) * 18.0
        p.blanket_open = 0.55 * p.turn
        p.blanket_flare = 0.45 * p.turn
        p.harmonic = 0.45 * p.turn
    elif animation == "celebrate":
        cheer = _pulse(t)
        p.celebrate = cheer
        p.blanket_open = 0.9 * cheer
        p.near_hand = (89.0, 30.0)
        p.near_elbow = (82.0, 46.0)
        p.far_hand = (39.0, 30.0)
        p.far_elbow = (46.0, 46.0)
        p.mouth_open = 0.7 * cheer
    elif animation == "taunt":
        settle = _smooth(t)
        p.crouch = 0.35
        p.root_y = 4.0
        p.blanket_wrap = 0.75
        p.head_tilt = -4.0 + wave * 1.0
        p.blink = frame_idx in {4, 5}
        p.mouth_open = 0.25 if frame_idx in {1, 2, 6} else 0.0
        p.near_hand = (71.0, 58.0 + settle)
        p.far_hand = (57.0, 58.0 + settle)

    return p


def _transform(point: Point, pose: Pose) -> Point:
    x = point[0] + pose.root_x + pose.lean * ((92.0 - point[1]) / 70.0)
    y = point[1] + pose.root_y + pose.bob
    if point[1] > 72.0:
        y -= pose.crouch * (point[1] - 72.0) * 0.23
    if point[1] < 72.0:
        y += pose.crouch * (72.0 - point[1]) * 0.08
    result = (x, y)
    if pose.rotation:
        pivot = (
            pose.rotation_pivot[0] + pose.root_x,
            pose.rotation_pivot[1] + pose.root_y,
        )
        result = _rotate(result, pivot, pose.rotation)
    return result


def _draw_leg(draw: ImageDraw.ImageDraw, pose: Pose, hip: Point, knee: Point, ankle: Point, *, far: bool) -> None:
    T = lambda q: _transform(q, pose)
    hip_t, knee_t, ankle_t = T(hip), T(knee), T(ankle)
    trouser = TROUSER if not far else BLANKET_DEEP
    trouser_light = TROUSER_LIGHT if not far else TROUSER
    _polygon(draw, _segment_quad(hip_t, knee_t, 4.0, 3.6), trouser, OUTLINE, 0.9)
    _polygon(draw, _segment_quad(knee_t, ankle_t, 3.6, 3.0), trouser_light, OUTLINE, 0.9)
    direction = 1.0 if ankle_t[0] >= knee_t[0] else -1.0
    shoe_center = (ankle_t[0] + direction * 2.1, ankle_t[1] + 1.0)
    _ellipse(draw, shoe_center, 5.2, 2.6, SHOE if not far else SHOE_LIGHT, OUTLINE, 0.9)


def _draw_arm(draw: ImageDraw.ImageDraw, pose: Pose, shoulder: Point, elbow: Point, hand: Point, *, far: bool) -> None:
    T = lambda q: _transform(q, pose)
    shoulder_t, elbow_t, hand_t = T(shoulder), T(elbow), T(hand)
    sleeve = BLANKET_DARK if far else BLANKET_LIGHT
    _polygon(draw, _segment_quad(shoulder_t, elbow_t, 5.0, 4.2), sleeve, OUTLINE, 0.9)
    _polygon(draw, _segment_quad(elbow_t, hand_t, 4.2, 3.1), sleeve, OUTLINE, 0.9)
    _ellipse(draw, hand_t, 3.4, 3.6, SKIN_SHADE if far else SKIN, OUTLINE, 0.8)
    # A simple thumb keeps the hand readable at gameplay scale.
    _line(draw, [hand_t, (hand_t[0] + (2.5 if not far else -2.5), hand_t[1] + 1.1)], OUTLINE_SOFT, 0.8)


def _blanket_geometry(pose: Pose) -> Tuple[List[Point], List[Point], List[Point]]:
    sway = pose.blanket_sway
    flare = pose.blanket_flare
    opening = pose.blanket_open
    wrap = pose.blanket_wrap
    shoulder_y = 46.0
    hem_y = 105.0 - pose.crouch * 4.0
    left_outer = 42.0 - flare * 10.0 - sway * 0.35 + wrap * 3.0
    right_outer = 86.0 + flare * 10.0 - sway * 0.35 - wrap * 3.0
    center_gap = 2.5 + opening * 10.0 - wrap * 1.8
    center = 64.0 - sway * 0.08
    left = [
        (52.0 - sway * 0.12, shoulder_y),
        (43.0 - opening * 7.0, 58.0),
        (left_outer, 84.0),
        (47.0 - flare * 7.0 + sway * 0.2, hem_y),
        (center - center_gap, hem_y - 2.0),
        (center - center_gap * 0.45, 61.0),
    ]
    right = [
        (76.0 - sway * 0.12, shoulder_y),
        (85.0 + opening * 7.0, 58.0),
        (right_outer, 84.0),
        (81.0 + flare * 7.0 + sway * 0.2, hem_y),
        (center + center_gap, hem_y - 2.0),
        (center + center_gap * 0.45, 61.0),
    ]
    lining = [
        (center - center_gap * 0.5, 57.0),
        (center + center_gap * 0.5, 57.0),
        (center + center_gap, hem_y - 2.0),
        (center - center_gap, hem_y - 2.0),
    ]
    return left, right, lining


def _draw_spectral_lining(draw: ImageDraw.ImageDraw, pose: Pose, lining: Sequence[Point]) -> None:
    T = lambda q: _transform(q, pose)
    mapped = [T(q) for q in lining]
    _polygon(draw, mapped, LINING, OUTLINE, 0.8)
    alpha = 0.35 + 0.65 * pose.blanket_open
    colors = [SPECTRAL_BLUE, SPECTRAL_TEAL, GOLD, SPECTRAL_RED, SPECTRAL_VIOLET]
    y0 = 64.0
    for idx, color in enumerate(colors):
        y = y0 + idx * 6.7
        half = 2.0 + pose.blanket_open * (4.0 + idx * 0.7)
        _line(
            draw,
            [T((64.0 - half, y)), T((64.0 + half, y + math.sin(idx) * 1.0))],
            _fade(color, alpha),
            1.0,
        )


def _draw_blanket(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    left, right, lining = _blanket_geometry(pose)
    if pose.blanket_open > 0.08:
        _draw_spectral_lining(draw, pose, lining)
    _polygon(draw, [T(q) for q in left], BLANKET, OUTLINE, 1.1)
    _polygon(draw, [T(q) for q in right], BLANKET_LIGHT, OUTLINE, 1.1)

    # Deep folds make the large simple mass read as a blanket instead of a robe.
    fold_alpha = 0.75
    for x, bias in ((51.0, -1.0), (57.0, -0.5), (71.0, 0.5), (78.0, 1.0)):
        _line(
            draw,
            [T((x, 58.0)), T((x + bias + pose.blanket_sway * 0.25, 99.0))],
            _fade(BLANKET_DARK, fold_alpha),
            1.0,
        )

    # Fur collar is the visual expression of the name pun.
    collar = [
        (49.0, 48.0),
        (54.0, 43.5),
        (61.0, 46.5),
        (64.0, 43.5),
        (67.0, 46.5),
        (74.0, 43.5),
        (79.0, 48.0),
        (74.0, 55.0),
        (64.0, 58.0),
        (54.0, 55.0),
    ]
    _polygon(draw, [T(q) for q in collar], FUR, OUTLINE, 1.0)
    _line(draw, [T((51.5, 49.0)), T((64.0, 55.5)), T((76.5, 49.0))], FUR_LIGHT, 1.1)
    _line(draw, [T((54.0, 53.0)), T((64.0, 57.0)), T((74.0, 53.0))], FUR_DARK, 0.7)

    # A restrained step border foreshadows the specials without making stairs
    # the everyday silhouette.
    border_y = 99.0 - pose.crouch * 3.5
    step_points = []
    for idx in range(7):
        x = 49.0 + idx * 5.0
        y = border_y - (idx % 2) * 2.0
        step_points.extend([(x, y), (x + 2.5, y)])
    _line(draw, [T(q) for q in step_points], _fade(GOLD, 0.72), 0.9)


def _draw_head(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    center = (64.0 + pose.head_x, 29.0 + pose.head_y)
    T = lambda q: _transform(_rotate(q, center, pose.head_tilt), pose)

    # Hair mass and sideburns first.
    _ellipse(draw, T((63.0, 26.5)), 14.0, 17.5, HAIR, OUTLINE, 1.0)
    _ellipse(draw, T((52.5, 34.5)), 4.0, 9.0, HAIR, OUTLINE, 0.8)
    _ellipse(draw, T((75.0, 34.0)), 4.0, 8.5, HAIR, OUTLINE, 0.8)
    _ellipse(draw, T((64.0, 30.0)), 11.5, 15.0, SKIN, OUTLINE, 1.0)
    _ellipse(draw, T((64.0, 24.0)), 10.5, 8.0, SKIN_LIGHT, None)

    # High, slightly unruly hairline.
    _arc(draw, T((63.0, 24.0)), 10.5, 8.0, 194, 345, HAIR_LIGHT, 1.4)
    _line(draw, [T((54.0, 20.5)), T((59.0, 16.5)), T((64.0, 19.0)), T((70.0, 16.8)), T((74.5, 21.0))], HAIR, 4.0)

    eye_y = 29.0
    if pose.blink:
        _line(draw, [T((58.0, eye_y)), T((61.0, eye_y + 0.4))], EYE, 0.9)
        _line(draw, [T((68.0, eye_y + 0.4)), T((71.0, eye_y))], EYE, 0.9)
    else:
        _ellipse(draw, T((59.5, eye_y)), 1.15, 1.35, EYE, None)
        _ellipse(draw, T((69.5, eye_y)), 1.15, 1.35, EYE, None)
        _ellipse(draw, T((59.2, eye_y - 0.35)), 0.35, 0.38, SKIN_LIGHT, None)
        _ellipse(draw, T((69.2, eye_y - 0.35)), 0.35, 0.38, SKIN_LIGHT, None)

    _line(draw, [T((56.5, 25.5 - pose.brow)), T((61.0, 25.0))], HAIR, 1.0)
    _line(draw, [T((67.5, 25.0)), T((72.0, 25.5 + pose.brow))], HAIR, 1.0)

    # Long angular nose gives a recognizable non-generic face at sprite scale.
    _polygon(draw, [T((64.0, 28.0)), T((66.8, 35.0)), T((63.2, 35.8))], SKIN_SHADE, OUTLINE_SOFT, 0.55)
    mouth_y = 39.0
    if pose.mouth_open > 0.1:
        _ellipse(draw, T((64.5, mouth_y)), 3.0, 1.2 + 1.6 * pose.mouth_open, MOUTH, OUTLINE_SOFT, 0.55)
    else:
        _arc(draw, T((64.5, 37.5)), 4.0, 2.0, 20, 160, MOUTH, 0.8)

    # Pronounced sideburn wisps, not a beard.
    _line(draw, [T((53.0, 30.5)), T((52.5, 39.5))], HAIR_LIGHT, 2.0)
    _line(draw, [T((75.0, 30.0)), T((75.5, 39.0))], HAIR_LIGHT, 2.0)


def _draw_effects_behind(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    if pose.damping > 0.02:
        for idx in range(3):
            radius = 20.0 + idx * 8.0 + pose.damping * 5.0
            _arc(
                draw,
                (64.0 + pose.root_x, 68.0 + pose.root_y),
                radius,
                radius * 0.72,
                190,
                350,
                _fade(DAMP_FIELD, pose.damping * (0.65 - idx * 0.13)),
                2.0 - idx * 0.35,
            )
    if pose.step > 0.02:
        alpha = pose.step
        base_x = 16.0
        base_y = 102.0
        for idx in range(6):
            x0 = base_x + idx * 14.0
            y0 = base_y - idx * 8.0
            grow = 2.0 + alpha * 5.0
            _polygon(
                draw,
                [(x0, y0), (x0 + 14.0, y0), (x0 + 14.0, y0 - grow), (x0, y0 - grow)],
                _fade(BLANKET_DARK, alpha * 0.8),
                _fade(GOLD, alpha * 0.85),
                0.7,
            )
    if pose.descent > 0.02:
        for idx in range(5):
            x = 34.0 + idx * 12.0
            y = 108.0 - idx * 10.0
            _line(draw, [(x, y), (x + 12.0, y)], _fade(SPECTRAL_VIOLET, pose.descent * (0.8 - idx * 0.08)), 2.0)


def _draw_effects_front(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    if pose.snap > 0.02:
        hand = T(pose.near_hand)
        for idx, color in enumerate((GOLD_LIGHT, SPECTRAL_RED, SPECTRAL_BLUE)):
            extent = 8.0 + idx * 5.0 + pose.snap * 7.0
            _arc(draw, (hand[0] + 4.0, hand[1]), extent, 8.0 + idx * 4.0, 280, 80, _fade(color, pose.snap * (0.95 - idx * 0.15)), 1.7)
    if pose.harmonic > 0.02:
        origin = T((77.0, 62.0))
        colors = (SPECTRAL_BLUE, SPECTRAL_TEAL, GOLD, SPECTRAL_RED, SPECTRAL_VIOLET)
        for idx, color in enumerate(colors):
            points = []
            amp = 2.0 + idx * 1.2
            length = 27.0 + pose.harmonic * 12.0
            for step_idx in range(9):
                u = step_idx / 8.0
                x = origin[0] + u * length
                y = origin[1] - 13.0 + idx * 6.0 + math.sin(u * math.tau * (1.0 + idx * 0.25)) * amp
                points.append((x, y))
            _line(draw, points, _fade(color, pose.harmonic), 1.2)
    if pose.step > 0.02:
        hand = T(pose.near_hand)
        points = [hand]
        for idx in range(5):
            x = hand[0] + 5.0 + idx * 5.0
            y = hand[1] - idx * 4.0
            points.extend([(x, y + 4.0), (x, y)])
        _line(draw, points, _fade(GOLD_LIGHT, pose.step), 1.8)
    if pose.celebrate > 0.02:
        center = T((64.0, 48.0))
        for idx, color in enumerate((GOLD_LIGHT, SPECTRAL_TEAL, SPECTRAL_VIOLET)):
            angle = -70.0 + idx * 70.0
            rad = math.radians(angle)
            end = (center[0] + math.cos(rad) * 28.0, center[1] + math.sin(rad) * 28.0)
            _line(draw, [center, end], _fade(color, pose.celebrate), 1.5)


def _render_native_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose(animation, frame_idx, nframes)
    image = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    draw = blending_draw(image)

    _draw_effects_behind(draw, pose)
    _draw_leg(draw, pose, pose.far_hip, pose.far_knee, pose.far_ankle, far=True)
    _draw_leg(draw, pose, pose.near_hip, pose.near_knee, pose.near_ankle, far=False)

    # Shirt wedge under the collar appears only when the blanket opens.
    T = lambda q: _transform(q, pose)
    _polygon(draw, [T((57.0, 48.0)), T((71.0, 48.0)), T((68.0, 70.0)), T((60.0, 70.0))], SHIRT, OUTLINE, 0.8)
    _line(draw, [T((64.0, 49.0)), T((64.0, 68.0))], SHIRT_SHADE, 0.8)

    _draw_arm(draw, pose, pose.far_shoulder, pose.far_elbow, pose.far_hand, far=True)
    _draw_blanket(draw, pose)
    _draw_arm(draw, pose, pose.near_shoulder, pose.near_elbow, pose.near_hand, far=False)
    _draw_effects_front(draw, pose)
    _draw_head(draw, pose)
    return image


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _render_native_frame(animation, frame_idx, nframes).resize(
        (FRAME_W, FRAME_H), Image.Resampling.LANCZOS
    )


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    """Publish native close-up expressions while preserving the blanket collar."""
    del opts
    face = FaceGuide(
        center_x=64.0,
        center_y=31.0,
        width=30.0,
        height=35.0,
        source_width=FRAME_W,
        source_height=FRAME_H,
    )

    def portrait_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        return render_framed_portrait(
            _render_native_frame(animation, frame_idx, frame_count),
            face,
            view_width=70.0,
            center_y=39.0,
        )

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 1, 8)),
        "murmuring": PortraitClip(
            tuple(portrait_frame("talk", frame, 8) for frame in range(8)),
            duration_ms=104,
            looping=True,
        ),
        "listening": PortraitClip(
            tuple(portrait_frame("idle", frame, 8) for frame in (1, 3, 4, 6)),
            duration_ms=145,
            looping=True,
        ),
        "spectral": PortraitClip(
            tuple(portrait_frame("harmonic_split", frame, 8) for frame in (1, 3, 5, 7)),
            duration_ms=118,
            looping=True,
        ),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {
            "x": int(fw * 0.25),
            "y": int(fh * 0.08),
            "w": int(fw * 0.52),
            "h": int(fh * 0.86),
        },
        "feet_pixel": {"x": fw * 0.50, "y": fh * 0.925},
        "feet_anchor_norm": {"x": 0.0, "y": round(0.5 - 0.925, 6)},
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
            "blanket_snap": {"bbox": {"x": 75, "y": 43, "w": 50, "h": 42}},
            "step_function": {"bbox": {"x": 76, "y": 30, "w": 50, "h": 62}},
            "harmonic_split": {"bbox": {"x": 78, "y": 30, "w": 49, "h": 66}},
            "spectral_descent": {"bbox": {"x": 29, "y": 43, "w": 82, "h": 76}},
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


__all__ = [
    "ACTOR_METADATA",
    "authoring_description",
    "render",
    "render_canonical",
    "render_frame",
    "render_portraits",
]


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
