"""Procedural sprite target for Jeff Hinter in his shrinkwrap-converged armor.

This sibling target keeps the same caricature, proportions, and broad acting
vocabulary as the base Jeff Hinter sheet, but assumes the manifold optimization
has already converged into his body-conforming segmented armor. The ordinary
rows therefore render Jeff fully plated while preserving his recognizable
glasses, swept silver hair, and academic silhouette.

It also includes a dedicated transformation row that begins as ordinary Jeff,
deploys the manifold field, and settles into the armored form. The coordinate
plane, optimization mesh, and typography remain transient effects rather than
props. As with the base target, there is no drop shadow and no baked held
object; painter order stays legs -> torso -> both arms -> head.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_BASENAME = "jeff_hinter_armored"
FRAME_SIZE = (160, 160)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 145),
    ("walk", 8, 105),
    ("talk", 8, 108),
    ("interact", 10, 92),
    ("hint", 10, 92),
    ("visualize_2d", 12, 92),
    ("shout_14", 12, 78),
    ("shout_3", 12, 78),
    ("manifold_shrinkwrap", 16, 82),
    ("transform_armor", 18, 82),
    # Runtime-recognized defensive alias. On the armored sheet it uses the
    # plated brace directly rather than re-running the full transformation.
    ("block", 10, 82),
    # Runtime-recognized expressive alias for scripted uses that only know the
    # common CharacterAnim vocabulary. It intentionally reuses the outburst.
    ("taunt", 12, 78),
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_jeff_hinter_armored", "display_name": "Jeff Hinter (Armored)"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": ["story", "humanoid", "scholar", "hint_npc", "ai_history", "manifold_armor", "armored_variant"],
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
    "tags": ["story", "humanoid", "scholar", "hint_npc", "ai_history", "manifold_armor", "armored_variant"],
    "sockets": {
        "head": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 70.0, "y": 43.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 72.0, "y": 91.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 52.0, "y": 105.0},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 94.0, "y": 101.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 72.0, "y": 10.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "interaction.hint": {"animation": "hint", "events": []},
        "emote.visualize_2d": {"animation": "visualize_2d", "events": []},
        "emote.shout_14": {"animation": "shout_14", "events": []},
        "emote.shout_3": {"animation": "shout_3", "events": []},
        "ability.manifold_shrinkwrap": {"animation": "manifold_shrinkwrap", "events": []},
        "ability.transform_armor": {"animation": "transform_armor", "events": []},
        "defense.block": {"animation": "block", "events": []},
    },
}

ARMORED_DEFAULT_ANIMATIONS = {
    "idle",
    "walk",
    "talk",
    "interact",
    "hint",
    "visualize_2d",
    "shout_14",
    "shout_3",
    "taunt",
}

# Muted academic clothing makes the silver hair, glasses, gestures, and effects
# do the identifying work without turning the character into a costume gag.
OUTLINE: RGBA = (16, 20, 26, 255)
OUTLINE_SOFT: RGBA = (42, 49, 58, 255)
SKIN: RGBA = (218, 185, 157, 255)
SKIN_LIGHT: RGBA = (241, 216, 190, 255)
SKIN_SHADE: RGBA = (177, 137, 111, 255)
SKIN_DEEP: RGBA = (126, 91, 75, 255)
HAIR: RGBA = (204, 207, 207, 255)
HAIR_LIGHT: RGBA = (242, 242, 235, 255)
HAIR_SHADE: RGBA = (133, 142, 148, 255)
JACKET: RGBA = (42, 62, 78, 255)
JACKET_MID: RGBA = (59, 83, 101, 255)
JACKET_LIGHT: RGBA = (79, 106, 124, 255)
JACKET_DARK: RGBA = (28, 40, 52, 255)
SHIRT: RGBA = (127, 157, 171, 255)
SHIRT_LIGHT: RGBA = (167, 191, 199, 255)
SHIRT_DARK: RGBA = (82, 111, 126, 255)
TROUSER: RGBA = (50, 54, 61, 255)
TROUSER_LIGHT: RGBA = (72, 77, 85, 255)
SHOE: RGBA = (65, 48, 40, 255)
SHOE_LIGHT: RGBA = (102, 76, 61, 255)
GLASS_FRAME: RGBA = (29, 35, 43, 255)
GLASS_TINT: RGBA = (194, 224, 235, 46)
EYE_WHITE: RGBA = (239, 235, 223, 255)
EYE: RGBA = (41, 52, 58, 255)
MOUTH: RGBA = (105, 48, 47, 255)
TEETH: RGBA = (243, 233, 214, 255)
PLANE: RGBA = (89, 189, 202, 170)
PLANE_SOFT: RGBA = (89, 189, 202, 74)
POINT_A: RGBA = (237, 174, 72, 230)
POINT_B: RGBA = (223, 92, 102, 230)
POINT_C: RGBA = (132, 209, 147, 230)
SHOUT: RGBA = (246, 196, 78, 255)
SHOUT_DEEP: RGBA = (133, 72, 42, 255)
MANIFOLD: RGBA = (84, 226, 211, 220)
MANIFOLD_SOFT: RGBA = (84, 226, 211, 74)
MANIFOLD_NODE: RGBA = (246, 181, 71, 245)
ARMOR_DARK: RGBA = (20, 37, 50, 255)
ARMOR_MID: RGBA = (42, 78, 94, 255)
ARMOR_LIGHT: RGBA = (84, 128, 139, 255)
ARMOR_CORE: RGBA = (35, 117, 119, 255)
ARMOR_EDGE: RGBA = (130, 245, 222, 255)


def _s(value: float) -> int:
    return int(round(value * SUPER))


def _pt(point: Point) -> Tuple[int, int]:
    return (_s(point[0]), _s(point[1]))


def _box(center: Point, rx: float, ry: float) -> Tuple[int, int, int, int]:
    cx, cy = center
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _lerp(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def _lerp_point(a: Point, b: Point, amount: float) -> Point:
    return (_lerp(a[0], b[0], amount), _lerp(a[1], b[1], amount))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smoothstep(value: float) -> float:
    value = _clamp01(value)
    return value * value * (3.0 - 2.0 * value)


def _pulse01(value: float) -> float:
    return math.sin(_clamp01(value) * math.pi)


def _rotate(point: Point, origin: Point, degrees: float) -> Point:
    radians = math.radians(degrees)
    c = math.cos(radians)
    s = math.sin(radians)
    x = point[0] - origin[0]
    y = point[1] - origin[1]
    return (origin[0] + x * c - y * s, origin[1] + x * s + y * c)


def _offset(point: Point, dx: float, dy: float) -> Point:
    return (point[0] + dx, point[1] + dy)


def _fade(color: RGBA, strength: float, alpha_scale: float = 1.0) -> RGBA:
    alpha = int(round(color[3] * _clamp01(strength) * alpha_scale))
    return (color[0], color[1], color[2], max(0, min(255, alpha)))


def _segment_quad(a: Point, b: Point, radius_a: float, radius_b: float) -> list[Point]:
    _, normal, _ = _unit_segment(a, b)
    return [
        (a[0] + normal[0] * radius_a, a[1] + normal[1] * radius_a),
        (b[0] + normal[0] * radius_b, b[1] + normal[1] * radius_b),
        (b[0] - normal[0] * radius_b, b[1] - normal[1] * radius_b),
        (a[0] - normal[0] * radius_a, a[1] - normal[1] * radius_a),
    ]


def _line(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    width: float,
) -> None:
    draw.line(
        [_pt(point) for point in points],
        fill=fill,
        width=max(1, _s(width)),
        joint="curve",
    )


def _poly(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA | None,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    scaled = [_pt(point) for point in points]
    draw.polygon(scaled, fill=fill)
    if outline is not None and width > 0:
        draw.line(
            scaled + [scaled[0]],
            fill=outline,
            width=max(1, _s(width)),
            joint="curve",
        )


def _ellipse(
    draw: ImageDraw.ImageDraw,
    center: Point,
    rx: float,
    ry: float,
    fill: RGBA | None,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        _box(center, rx, ry),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)),
    )


def _rounded(
    draw: ImageDraw.ImageDraw,
    box: Tuple[float, float, float, float],
    radius: float,
    fill: RGBA | None,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.rounded_rectangle(
        tuple(_s(value) for value in box),
        radius=max(1, _s(radius)),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)),
    )


def _unit_segment(a: Point, b: Point) -> Tuple[Point, Point, float]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = max(1.0e-6, math.hypot(dx, dy))
    along = (dx / length, dy / length)
    normal = (-along[1], along[0])
    return along, normal, length


def _bent_tube(
    draw: ImageDraw.ImageDraw,
    start: Point,
    bend: Point,
    end: Point,
    radii: Tuple[float, float, float],
    *,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.15,
) -> None:
    """Draw one connected tapered limb with no detached elbow/knee disc."""
    _, n1, _ = _unit_segment(start, bend)
    _, n2, _ = _unit_segment(bend, end)
    average = (n1[0] + n2[0], n1[1] + n2[1])
    average_len = max(1.0e-6, math.hypot(*average))
    middle_normal = (average[0] / average_len, average[1] / average_len)
    r0, r1, r2 = radii
    points = [
        (start[0] + n1[0] * r0, start[1] + n1[1] * r0),
        (bend[0] + middle_normal[0] * r1, bend[1] + middle_normal[1] * r1),
        (end[0] + n2[0] * r2, end[1] + n2[1] * r2),
        (end[0] - n2[0] * r2, end[1] - n2[1] * r2),
        (bend[0] - middle_normal[0] * r1, bend[1] - middle_normal[1] * r1),
        (start[0] - n1[0] * r0, start[1] - n1[1] * r0),
    ]
    _poly(draw, points, fill, outline, width)
    _ellipse(draw, start, r0, r0, fill, outline, width)
    _ellipse(draw, end, r2, r2, fill, outline, width)


def _font(size: float, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, _s(size))
    except OSError:
        return ImageFont.load_default()


@dataclass
class Pose:
    body_x: float = 0.0
    body_y: float = 0.0
    lean: float = 0.0
    head_x: float = 0.0
    head_y: float = 0.0
    head_tilt: float = 0.0
    blink: bool = False
    mouth_open: float = 0.0
    mouth_round: float = 0.0
    mouth_smile: float = 0.0
    brow_lift: float = 0.0
    gaze_x: float = 0.0
    gaze_y: float = 0.0
    near_shoulder: Point = (86.0, 78.0)
    near_elbow: Point = (94.0, 96.0)
    near_hand: Point = (93.0, 113.0)
    far_shoulder: Point = (59.0, 80.0)
    far_elbow: Point = (50.0, 98.0)
    far_hand: Point = (52.0, 114.0)
    near_hand_mode: str = "relaxed"
    far_hand_mode: str = "relaxed"
    near_hip: Point = (80.0, 116.0)
    near_knee: Point = (82.0, 133.0)
    near_ankle: Point = (83.0, 149.0)
    far_hip: Point = (66.0, 116.0)
    far_knee: Point = (64.0, 133.0)
    far_ankle: Point = (63.0, 149.0)
    plane_strength: float = 0.0
    plane_phase: float = 0.0
    hint_strength: float = 0.0
    shout_strength: float = 0.0
    shout_phase: float = 0.0
    shout_text: str = "14"
    manifold_strength: float = 0.0
    manifold_progress: float = 0.0
    manifold_phase: float = 0.0
    armor_strength: float = 0.0
    armor_lock: float = 0.0

    def __init__(self, animation: str, frame_idx: int, nframes: int) -> None:
        t = frame_idx / max(1, nframes - 1)
        phase = frame_idx / max(1, nframes)
        wave = math.sin(phase * math.tau)
        cosine = math.cos(phase * math.tau)

        self.body_x = 0.0
        self.body_y = 0.0
        self.lean = -1.5
        self.head_x = 0.0
        self.head_y = 0.0
        self.head_tilt = -2.0
        self.blink = False
        self.mouth_open = 0.0
        self.mouth_round = 0.0
        self.mouth_smile = 0.0
        self.brow_lift = 0.0
        self.gaze_x = 0.4
        self.gaze_y = 0.0
        self.near_shoulder = (86.0, 78.0)
        self.near_elbow = (94.0, 96.0)
        self.near_hand = (93.0, 113.0)
        self.far_shoulder = (59.0, 80.0)
        self.far_elbow = (50.0, 98.0)
        self.far_hand = (52.0, 114.0)
        self.near_hand_mode = "relaxed"
        self.far_hand_mode = "relaxed"
        self.near_hip = (80.0, 116.0)
        self.near_knee = (82.0, 133.0)
        self.near_ankle = (83.0, 149.0)
        self.far_hip = (66.0, 116.0)
        self.far_knee = (64.0, 133.0)
        self.far_ankle = (63.0, 149.0)
        self.plane_strength = 0.0
        self.plane_phase = phase
        self.hint_strength = 0.0
        self.shout_strength = 0.0
        self.shout_phase = t
        self.shout_text = "14"
        self.manifold_strength = 0.0
        self.manifold_progress = 0.0
        self.manifold_phase = phase
        self.armor_strength = 0.0
        self.armor_lock = 0.0

        if animation == "idle":
            breath = 0.5 - 0.5 * cosine
            self.body_y = -0.55 * breath
            self.head_y = -0.35 * breath
            self.head_x = 0.25 * wave
            self.head_tilt = -2.5 + 0.8 * wave
            self.near_elbow = (94.0 + 0.4 * wave, 96.0)
            self.near_hand = (93.0 + 0.35 * wave, 113.0 + 0.35 * cosine)
            self.far_elbow = (50.0 - 0.35 * wave, 98.0)
            self.far_hand = (52.0 - 0.25 * wave, 114.0)
            self.gaze_x = 0.55 + 0.22 * wave
            self.blink = frame_idx == 6
            self.mouth_smile = 0.08

        elif animation == "walk":
            stride = 8.5 * wave
            near_lift = max(0.0, wave) * 4.5
            far_lift = max(0.0, -wave) * 4.5
            self.body_x = 0.5 * wave
            self.body_y = -1.25 * abs(wave)
            self.lean = -3.5
            self.head_x = 0.35 * wave
            self.head_y = -0.25 * abs(wave)
            self.head_tilt = -3.6 - 0.45 * wave
            self.near_knee = (82.0 + stride * 0.50, 133.0 - near_lift * 0.2)
            self.near_ankle = (83.0 + stride, 149.0 - near_lift)
            self.far_knee = (64.0 - stride * 0.48, 133.0 - far_lift * 0.2)
            self.far_ankle = (63.0 - stride * 0.92, 149.0 - far_lift)
            self.near_elbow = (94.0 - stride * 0.34, 96.0)
            self.near_hand = (93.0 - stride * 0.48, 113.0)
            self.far_elbow = (50.0 + stride * 0.28, 98.0)
            self.far_hand = (52.0 + stride * 0.40, 114.0)
            self.blink = frame_idx == 7

        elif animation == "talk":
            gesture = 0.5 - 0.5 * math.cos(phase * math.tau)
            alternate = math.sin(phase * math.tau)
            self.body_y = -0.45 * gesture
            self.head_tilt = -4.0 + 3.5 * alternate
            self.head_x = 0.6 * alternate
            self.mouth_open = 0.25 + 0.65 * max(0.0, math.sin(phase * math.tau * 2.0))
            self.mouth_smile = 0.18
            self.brow_lift = 0.35 + 0.5 * gesture
            self.near_elbow = (101.0 + 2.0 * alternate, 90.0 - 4.0 * gesture)
            self.near_hand = (110.0 + 3.0 * alternate, 82.0 - 2.0 * gesture)
            self.near_hand_mode = "open"
            self.far_elbow = (48.0, 96.0 - 2.0 * gesture)
            self.far_hand = (57.0, 101.0 - 3.0 * gesture)
            self.far_hand_mode = "open"
            self.gaze_x = 0.8
            self.blink = frame_idx == 6

        elif animation in {"interact", "hint"}:
            # Tap temple -> realize -> point outward.  The explicit point is an
            # empty-hand gesture, not a baked held item.
            gather = _smoothstep(min(1.0, t / 0.32))
            reveal = _smoothstep((t - 0.28) / 0.42)
            settle = _smoothstep((t - 0.72) / 0.28)
            self.hint_strength = _pulse01((t - 0.12) / 0.88)
            self.body_x = 1.6 * reveal - 0.7 * settle
            self.body_y = -1.2 * self.hint_strength
            self.lean = -4.0 + 5.0 * reveal
            self.head_tilt = -10.0 * gather + 13.0 * reveal - 4.0 * settle
            self.head_x = 1.1 * reveal
            self.brow_lift = 0.4 + 1.2 * reveal
            self.mouth_smile = 0.15 + 0.45 * reveal
            self.mouth_open = 0.15 + 0.35 * math.sin(t * math.pi * 3.0) ** 2
            self.gaze_x = _lerp(-0.45, 1.0, reveal)
            self.gaze_y = _lerp(-0.25, 0.0, reveal)
            temple_hand = (88.0, 47.0)
            point_hand = (126.0, 73.0)
            self.near_elbow = _lerp_point((94.0, 96.0), (102.0, 76.0), gather)
            self.near_elbow = _lerp_point(self.near_elbow, (108.0, 78.0), reveal)
            self.near_hand = _lerp_point((93.0, 113.0), temple_hand, gather)
            self.near_hand = _lerp_point(self.near_hand, point_hand, reveal)
            self.near_hand = _lerp_point(self.near_hand, (112.0, 91.0), settle)
            self.near_hand_mode = "temple" if reveal < 0.48 else "point"
            self.far_elbow = _lerp_point((50.0, 98.0), (51.0, 90.0), reveal)
            self.far_hand = _lerp_point((52.0, 114.0), (61.0, 90.0), reveal)
            self.far_hand_mode = "open"
            self.blink = frame_idx == 2

        elif animation == "visualize_2d":
            emerge = _smoothstep(t / 0.24)
            focus = _smoothstep((t - 0.18) / 0.25)
            release = _smoothstep((t - 0.82) / 0.18)
            strength = emerge * (1.0 - 0.55 * release)
            self.plane_strength = strength
            self.plane_phase = phase
            self.body_x = -1.5 * focus + 0.8 * release
            self.body_y = -0.7 * strength
            self.lean = -4.0 - 3.5 * focus
            self.head_x = 0.8 * focus
            self.head_y = -0.8 * focus
            self.head_tilt = -8.0 + 2.0 * wave
            self.brow_lift = 0.75
            self.mouth_open = 0.12 + 0.18 * abs(wave)
            self.gaze_x = 1.15
            self.gaze_y = -0.15 + 0.2 * wave
            self.far_elbow = _lerp_point((50.0, 98.0), (45.0, 82.0), focus)
            self.far_hand = _lerp_point((52.0, 114.0), (53.0, 70.0), focus)
            self.far_hand_mode = "frame"
            self.near_elbow = _lerp_point((94.0, 96.0), (101.0, 91.0), focus)
            self.near_hand = _lerp_point((93.0, 113.0), (120.0, 104.0), focus)
            self.near_hand_mode = "frame"
            self.blink = frame_idx == 10

        elif animation == "manifold_shrinkwrap":
            # Three nested contours iteratively contract onto Jeff's silhouette.
            # The residual vectors shorten as the fit improves; at convergence the
            # manifold hardens into segmented armor rather than becoming a bubble.
            deploy = _smoothstep(t / 0.18)
            optimize = _smoothstep((t - 0.10) / 0.48)
            lock = _smoothstep((t - 0.50) / 0.22)
            field_fade = _smoothstep((t - 0.68) / 0.27)
            self.manifold_strength = deploy * (1.0 - 0.82 * field_fade)
            self.manifold_progress = optimize
            self.manifold_phase = phase
            self.armor_strength = _smoothstep((t - 0.30) / 0.40)
            self.armor_lock = _pulse01((t - 0.48) / 0.40)

            # Open calibration stance -> compressed fit -> broad armored brace.
            self.body_y = 2.4 * deploy - 2.0 * lock
            self.body_x = -0.7 * optimize + 1.1 * lock
            self.lean = -5.0 - 2.5 * optimize + 8.5 * lock
            self.head_x = -0.8 * optimize + 0.7 * lock
            self.head_y = 1.0 * deploy - 1.2 * lock
            self.head_tilt = -8.0 - 3.0 * optimize + 10.0 * lock
            self.brow_lift = 0.5 + 0.8 * optimize
            self.mouth_open = 0.08 + 0.28 * (1.0 - lock) * abs(wave)
            self.mouth_smile = 0.10 + 0.18 * lock
            self.gaze_x = -0.15 + 0.55 * lock
            self.gaze_y = 0.45 - 0.35 * lock

            near_open_elbow = (104.0, 91.0)
            near_open_hand = (119.0, 87.0)
            far_open_elbow = (43.0, 92.0)
            far_open_hand = (29.0, 88.0)
            self.near_elbow = _lerp_point((94.0, 96.0), near_open_elbow, deploy)
            self.near_hand = _lerp_point((93.0, 113.0), near_open_hand, deploy)
            self.far_elbow = _lerp_point((50.0, 98.0), far_open_elbow, deploy)
            self.far_hand = _lerp_point((52.0, 114.0), far_open_hand, deploy)
            self.near_elbow = _lerp_point(self.near_elbow, (100.0, 103.0), lock)
            self.near_hand = _lerp_point(self.near_hand, (101.0, 117.0), lock)
            self.far_elbow = _lerp_point(self.far_elbow, (47.0, 103.0), lock)
            self.far_hand = _lerp_point(self.far_hand, (47.0, 117.0), lock)
            self.near_hand_mode = "open" if lock < 0.58 else "relaxed"
            self.far_hand_mode = "open" if lock < 0.58 else "relaxed"

            self.near_knee = _lerp_point((82.0, 133.0), (86.0, 133.0), lock)
            self.near_ankle = _lerp_point((83.0, 149.0), (92.0, 149.0), lock)
            self.far_knee = _lerp_point((64.0, 133.0), (60.0, 133.0), lock)
            self.far_ankle = _lerp_point((63.0, 149.0), (53.0, 149.0), lock)

            # A crisp one-frame settling vibration makes the lock-in read as a
            # mechanical optimization result rather than a costume dissolve.
            if self.armor_lock > 0.35:
                settle_shake = math.sin(t * math.pi * 18.0) * 0.65 * self.armor_lock
                self.body_x += settle_shake
                self.head_x -= settle_shake * 0.45
            self.blink = 0.34 < t < 0.46

        elif animation == "transform_armor":
            # Base Jeff -> manifold field deploy -> converged armor -> calm plated
            # settle. This ends close to the armored idle pose so it chains cleanly.
            deploy = _smoothstep(t / 0.16)
            optimize = _smoothstep((t - 0.08) / 0.28)
            lock = _smoothstep((t - 0.34) / 0.18)
            settle = _smoothstep((t - 0.64) / 0.20)
            field_fade = _smoothstep((t - 0.54) / 0.24)
            self.manifold_strength = deploy * (1.0 - 0.90 * field_fade)
            self.manifold_progress = optimize
            self.manifold_phase = phase
            self.armor_strength = _smoothstep((t - 0.18) / 0.26)
            self.armor_lock = _smoothstep((t - 0.40) / 0.16)

            self.body_y = 1.3 * deploy - 1.6 * lock - 0.8 * settle
            self.body_x = -0.4 * optimize + 0.6 * lock
            self.lean = -3.5 - 1.8 * optimize + 7.2 * lock - 1.6 * settle
            self.head_x = -0.5 * optimize + 0.55 * lock
            self.head_y = 0.5 * deploy - 0.9 * lock - 0.2 * settle
            self.head_tilt = -5.0 - 2.0 * optimize + 8.5 * lock - 2.0 * settle
            self.brow_lift = 0.25 + 0.75 * optimize
            self.mouth_open = 0.06 + 0.24 * (1.0 - lock) * abs(wave)
            self.mouth_smile = 0.05 + 0.15 * lock + 0.06 * settle
            self.gaze_x = 0.10 + 0.42 * lock
            self.gaze_y = 0.20 - 0.20 * lock

            self.near_elbow = _lerp_point((94.0, 96.0), (101.0, 90.0), deploy)
            self.near_hand = _lerp_point((93.0, 113.0), (117.0, 86.0), deploy)
            self.far_elbow = _lerp_point((50.0, 98.0), (44.0, 92.0), deploy)
            self.far_hand = _lerp_point((52.0, 114.0), (30.0, 88.0), deploy)
            self.near_elbow = _lerp_point(self.near_elbow, (100.0, 103.0), lock)
            self.near_hand = _lerp_point(self.near_hand, (98.0, 115.0), lock)
            self.far_elbow = _lerp_point(self.far_elbow, (48.0, 103.0), lock)
            self.far_hand = _lerp_point(self.far_hand, (49.0, 116.0), lock)
            self.near_elbow = _lerp_point(self.near_elbow, (95.0, 97.0), settle)
            self.near_hand = _lerp_point(self.near_hand, (94.0, 113.0), settle)
            self.far_elbow = _lerp_point(self.far_elbow, (51.0, 98.0), settle)
            self.far_hand = _lerp_point(self.far_hand, (53.0, 114.0), settle)
            self.near_hand_mode = "open" if lock < 0.50 else "relaxed"
            self.far_hand_mode = "open" if lock < 0.50 else "relaxed"

            self.near_knee = _lerp_point((82.0, 133.0), (85.0, 133.0), lock)
            self.near_ankle = _lerp_point((83.0, 149.0), (88.0, 149.0), lock)
            self.far_knee = _lerp_point((64.0, 133.0), (61.0, 133.0), lock)
            self.far_ankle = _lerp_point((63.0, 149.0), (58.0, 149.0), lock)

            if self.armor_lock > 0.2 and settle < 0.75:
                settle_shake = math.sin(t * math.pi * 18.0) * 0.58 * self.armor_lock * (1.0 - settle)
                self.body_x += settle_shake
                self.head_x -= settle_shake * 0.42
            self.blink = 0.28 < t < 0.42

        elif animation == "block":
            # Already-armored defensive brace.
            brace = _smoothstep(t / 0.22)
            pulse = 0.5 - 0.5 * math.cos(phase * math.tau)
            self.armor_strength = 1.0
            self.armor_lock = 1.0
            self.body_y = -1.3 * brace - 0.35 * pulse
            self.body_x = 0.45 * brace
            self.lean = 4.0 + 1.8 * brace
            self.head_x = 0.35 * brace
            self.head_y = -0.45 * brace
            self.head_tilt = 4.5 + 1.2 * brace
            self.brow_lift = 0.55 + 0.15 * pulse
            self.mouth_open = 0.05 + 0.08 * pulse
            self.mouth_smile = 0.08
            self.gaze_x = 0.55
            self.gaze_y = -0.05
            self.near_elbow = (98.0, 101.0)
            self.near_hand = (98.0, 116.0)
            self.far_elbow = (48.0, 101.0)
            self.far_hand = (49.0, 117.0)
            self.near_hand_mode = "relaxed"
            self.far_hand_mode = "relaxed"
            self.near_knee = (85.0, 133.0)
            self.near_ankle = (90.0, 149.0)
            self.far_knee = (61.0, 133.0)
            self.far_ankle = (56.0, 149.0)
            self.blink = frame_idx == nframes - 2

        elif animation in {"shout_14", "shout_3", "taunt"}:
            # ``14`` parodies the classic high-dimensional visualization
            # trick; ``3`` is Jeff trying to recover the missing depth axis
            # of this deliberately two-dimensional game.
            self.shout_text = "3" if animation == "shout_3" else "14"
            inhale = _smoothstep(min(1.0, t / 0.26))
            blast = _smoothstep((t - 0.22) / 0.18)
            decay = _smoothstep((t - 0.66) / 0.34)
            strength = blast * (1.0 - 0.65 * decay)
            self.shout_strength = strength
            self.shout_phase = t
            self.body_x = -2.0 * inhale + 4.2 * strength - 2.0 * decay
            self.body_y = 1.2 * inhale - 3.0 * strength + 2.2 * decay
            self.lean = -8.0 * inhale + 15.0 * strength - 7.0 * decay
            self.head_x = -1.4 * inhale + 2.6 * strength
            self.head_y = 0.7 * inhale - 2.5 * strength
            self.head_tilt = -13.0 * inhale + 21.0 * strength - 7.0 * decay
            self.brow_lift = 1.4 * strength
            self.mouth_open = 0.1 + 1.35 * strength
            self.mouth_round = 0.95 * strength
            self.gaze_x = 0.95
            self.gaze_y = -0.25
            self.near_elbow = _lerp_point((94.0, 96.0), (102.0, 75.0), inhale)
            self.near_hand = _lerp_point((93.0, 113.0), (101.0, 64.0), inhale)
            self.far_elbow = _lerp_point((50.0, 98.0), (54.0, 76.0), inhale)
            self.far_hand = _lerp_point((52.0, 114.0), (57.0, 65.0), inhale)
            self.near_hand_mode = "cup_mouth"
            self.far_hand_mode = "cup_mouth"
            # The body rattles slightly at peak volume.
            if strength > 0.55:
                shake = math.sin(t * math.pi * 12.0) * 0.9 * strength
                self.body_x += shake
                self.head_x -= shake * 0.7
            self.blink = strength > 0.5

        if animation in ARMORED_DEFAULT_ANIMATIONS:
            # The alternate sheet assumes Jeff has already completed the shrinkwrap
            # optimization. Ordinary actions therefore keep the acting vocabulary
            # but render with the converged segmented armor at all times.
            self.armor_strength = 1.0
            self.armor_lock = 1.0
            self.body_y -= 0.8
            self.head_y -= 0.2
            self.lean += 0.7
            self.brow_lift += 0.08


class JeffHinterRenderer:
    def render_frame(self, animation: str, frame_idx: int, nframes: int) -> Image.Image:
        image = Image.new(
            "RGBA",
            (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER),
            (0, 0, 0, 0),
        )
        draw = blending_draw(image)
        pose = Pose(animation, frame_idx, nframes)

        pivot = (73.0 + pose.body_x, 112.0 + pose.body_y)

        def T(point: Point) -> Point:
            moved = (point[0] + pose.body_x, point[1] + pose.body_y)
            return _rotate(moved, pivot, pose.lean)

        # Effects are staged behind the person so the silhouette remains the
        # strongest read.  The shrinkwrap gets a second foreground pass below the
        # face so the contracting surface visibly crosses the body.
        if pose.plane_strength > 0.01:
            self._draw_coordinate_plane(draw, pose)
        if pose.hint_strength > 0.01:
            self._draw_hint_trace(draw, pose)
        if pose.manifold_strength > 0.01:
            self._draw_shrinkwrap_field(draw, pose, T, front=False)

        def composite_armor(paint) -> None:
            # ImageDraw on an RGBA target replaces pixels instead of blending them.
            # Armor therefore lives on a temporary layer so partial convergence
            # tints the clothing rather than punching translucent holes through it.
            overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
            overlay_draw = blending_draw(overlay)
            paint(overlay_draw)
            image.alpha_composite(overlay)

        # No baked floor ellipse or drop shadow.
        self._draw_legs(draw, pose, T)
        if pose.armor_strength > 0.01:
            composite_armor(lambda layer: self._draw_leg_armor(layer, pose, T))
            draw = blending_draw(image)

        self._draw_torso(draw, pose, T)
        if pose.armor_strength > 0.01:
            composite_armor(lambda layer: self._draw_torso_armor(layer, pose, T))
            draw = blending_draw(image)

        # Both arms are deliberately in front of the torso.
        far_shoulder = T(pose.far_shoulder)
        far_elbow = T(pose.far_elbow)
        far_hand = T(pose.far_hand)
        self._draw_arm(draw, far_shoulder, far_elbow, far_hand, pose.far_hand_mode, far=True)
        if pose.armor_strength > 0.01:
            composite_armor(
                lambda layer: self._draw_arm_armor(
                    layer, pose, far_shoulder, far_elbow, far_hand, far=True
                )
            )
            draw = blending_draw(image)

        near_shoulder = T(pose.near_shoulder)
        near_elbow = T(pose.near_elbow)
        near_hand = T(pose.near_hand)
        self._draw_arm(draw, near_shoulder, near_elbow, near_hand, pose.near_hand_mode, far=False)
        if pose.armor_strength > 0.01:
            def paint_near_armor(layer) -> None:
                self._draw_arm_armor(
                    layer, pose, near_shoulder, near_elbow, near_hand, far=False
                )
                self._draw_armor_collar(layer, pose, T)

            composite_armor(paint_near_armor)
            draw = blending_draw(image)

        head_center = T((72.0 + pose.head_x, 48.0 + pose.head_y))
        self._draw_head(image, draw, head_center, pose)

        if pose.manifold_strength > 0.01:
            self._draw_shrinkwrap_field(draw, pose, T, front=True)
        if pose.shout_strength > 0.01:
            self._draw_shout(image, pose, head_center)

        return image.resize(FRAME_SIZE, Image.Resampling.LANCZOS)

    def _draw_legs(self, draw: ImageDraw.ImageDraw, pose: Pose, T) -> None:
        # Far leg first.
        far_hip = T(pose.far_hip)
        far_knee = T(pose.far_knee)
        far_ankle = T(pose.far_ankle)
        _bent_tube(
            draw,
            far_hip,
            far_knee,
            far_ankle,
            (6.3, 5.2, 4.4),
            fill=TROUSER,
            outline=OUTLINE,
            width=1.15,
        )
        self._draw_shoe(draw, far_knee, far_ankle, far=True)

        near_hip = T(pose.near_hip)
        near_knee = T(pose.near_knee)
        near_ankle = T(pose.near_ankle)
        _bent_tube(
            draw,
            near_hip,
            near_knee,
            near_ankle,
            (6.6, 5.4, 4.6),
            fill=TROUSER_LIGHT,
            outline=OUTLINE,
            width=1.2,
        )
        # Trouser crease reinforces the long, slightly rumpled academic silhouette.
        _line(draw, [near_knee, near_ankle], TROUSER, 0.55)
        self._draw_shoe(draw, near_knee, near_ankle, far=False)

    def _draw_shoe(self, draw: ImageDraw.ImageDraw, knee: Point, ankle: Point, *, far: bool) -> None:
        along, normal, _ = _unit_segment(knee, ankle)
        toe = (ankle[0] + along[0] * 1.2 + 7.5, ankle[1] + along[1] * 1.0 + 0.8)
        heel = (ankle[0] - 3.3, ankle[1] + 2.2)
        points = [
            (ankle[0] - normal[0] * 4.6, ankle[1] - normal[1] * 4.6),
            (ankle[0] + normal[0] * 4.6, ankle[1] + normal[1] * 4.6),
            (toe[0], toe[1] + 2.0),
            (toe[0] + 0.4, toe[1] + 4.2),
            (heel[0], heel[1] + 4.0),
        ]
        fill = SHOE if far else SHOE_LIGHT
        _poly(draw, points, fill, OUTLINE, 1.1)
        _line(draw, [(heel[0], heel[1] + 3.2), (toe[0] + 0.2, toe[1] + 3.5)], OUTLINE, 0.8)

    def _draw_torso(self, draw: ImageDraw.ImageDraw, pose: Pose, T) -> None:
        left_shoulder = T((57.0, 78.0))
        right_shoulder = T((87.5, 76.0))
        left_waist = T((61.0, 116.0))
        right_waist = T((84.0, 116.0))

        # Shirt collar and neck are drawn before the jacket shell.
        neck_center = T((72.0, 70.5))
        _rounded(
            draw,
            (neck_center[0] - 5.1, neck_center[1] - 5.0, neck_center[0] + 5.1, neck_center[1] + 8.5),
            3.0,
            SKIN_SHADE,
            OUTLINE,
            0.8,
        )

        torso = [
            left_shoulder,
            T((66.0, 72.5)),
            T((77.0, 72.0)),
            right_shoulder,
            T((91.0, 91.0)),
            right_waist,
            T((72.5, 119.5)),
            left_waist,
            T((53.0, 93.0)),
        ]
        _poly(draw, torso, JACKET, OUTLINE, 1.3)

        # Open jacket exposes a soft blue shirt and makes the forward stoop read.
        shirt = [
            T((67.0, 74.0)),
            T((77.0, 73.7)),
            T((80.5, 112.5)),
            T((68.0, 116.0)),
            T((63.0, 85.0)),
        ]
        _poly(draw, shirt, SHIRT, OUTLINE_SOFT, 0.65)
        _poly(
            draw,
            [T((67.0, 74.0)), T((72.0, 80.0)), T((64.5, 83.0))],
            SHIRT_LIGHT,
            OUTLINE_SOFT,
            0.5,
        )
        _poly(
            draw,
            [T((77.0, 73.7)), T((72.0, 80.0)), T((80.0, 83.0))],
            SHIRT_DARK,
            OUTLINE_SOFT,
            0.5,
        )

        # Jacket lapels, seams, and subtle academic rumpling.
        _poly(
            draw,
            [T((62.0, 76.0)), T((68.0, 75.0)), T((66.0, 95.0)), T((57.5, 84.0))],
            JACKET_MID,
            OUTLINE_SOFT,
            0.55,
        )
        _poly(
            draw,
            [T((78.0, 74.0)), T((86.5, 77.0)), T((87.5, 88.0)), T((79.0, 96.0))],
            JACKET_LIGHT,
            OUTLINE_SOFT,
            0.55,
        )
        _line(draw, [T((72.5, 84.0)), T((73.0, 114.0))], OUTLINE_SOFT, 0.55)
        _line(draw, [T((57.0, 103.0)), T((64.0, 106.5))], JACKET_LIGHT, 0.55)
        _line(draw, [T((81.0, 105.0)), T((87.0, 102.0))], JACKET_DARK, 0.55)
        _ellipse(draw, T((73.0, 98.0)), 0.85, 0.85, OUTLINE_SOFT, OUTLINE_SOFT, 0.2)
        _ellipse(draw, T((73.0, 108.0)), 0.85, 0.85, OUTLINE_SOFT, OUTLINE_SOFT, 0.2)

    def _draw_arm(
        self,
        draw: ImageDraw.ImageDraw,
        shoulder: Point,
        elbow: Point,
        hand: Point,
        mode: str,
        *,
        far: bool,
    ) -> None:
        sleeve = JACKET if far else JACKET_MID
        _bent_tube(
            draw,
            shoulder,
            elbow,
            hand,
            (5.8 if far else 6.2, 4.8, 3.8),
            fill=sleeve,
            outline=OUTLINE,
            width=1.15,
        )
        # Shirt cuff prevents the hand from looking fused directly to the jacket.
        _, normal, _ = _unit_segment(elbow, hand)
        cuff_center = _lerp_point(elbow, hand, 0.85)
        cuff_a = (cuff_center[0] + normal[0] * 4.0, cuff_center[1] + normal[1] * 4.0)
        cuff_b = (cuff_center[0] - normal[0] * 4.0, cuff_center[1] - normal[1] * 4.0)
        _line(draw, [cuff_a, cuff_b], SHIRT_LIGHT, 2.0)
        self._draw_hand(draw, elbow, hand, mode, far=far)

    def _draw_hand(
        self,
        draw: ImageDraw.ImageDraw,
        elbow: Point,
        center: Point,
        mode: str,
        *,
        far: bool,
    ) -> None:
        along, normal, _ = _unit_segment(elbow, center)
        skin = SKIN_SHADE if far else SKIN
        _ellipse(draw, center, 4.2, 4.8, skin, OUTLINE, 0.9)

        def finger(start: Point, end: Point, width: float = 1.05) -> None:
            _line(draw, [start, end], OUTLINE, width + 1.1)
            _line(draw, [start, end], skin, width)

        if mode == "point":
            start = _offset(center, along[0] * 1.0, along[1] * 1.0)
            end = _offset(start, along[0] * 7.6, along[1] * 7.6)
            finger(start, end, 1.25)
            curled = _offset(center, normal[0] * 1.8, normal[1] * 1.8)
            _line(draw, [curled, _offset(curled, along[0] * 2.2, along[1] * 2.2)], SKIN_DEEP, 0.55)
        elif mode == "temple":
            start = _offset(center, -normal[0] * 1.2, -normal[1] * 1.2)
            end = _offset(start, along[0] * 5.2, along[1] * 5.2)
            finger(start, end, 1.0)
            _line(draw, [_offset(center, normal[0] * 1.0, normal[1] * 1.0), _offset(center, along[0] * 2.0, along[1] * 2.0)], SKIN_DEEP, 0.5)
        elif mode == "open":
            for index, spread in enumerate((-2.4, -0.8, 0.8, 2.4)):
                start = _offset(center, normal[0] * spread * 0.45, normal[1] * spread * 0.45)
                length = 4.4 - abs(index - 1.5) * 0.35
                end = _offset(start, along[0] * length + normal[0] * spread * 0.35, along[1] * length + normal[1] * spread * 0.35)
                finger(start, end, 0.75)
        elif mode == "frame":
            # Thumb and index form a right-angle corner used to bracket the
            # imagined coordinate plane.
            index_start = _offset(center, along[0] * 0.8, along[1] * 0.8)
            index_end = _offset(index_start, along[0] * 6.2, along[1] * 6.2)
            thumb_start = _offset(center, normal[0] * 0.8, normal[1] * 0.8)
            thumb_end = _offset(thumb_start, normal[0] * 4.5, normal[1] * 4.5)
            finger(index_start, index_end, 1.0)
            finger(thumb_start, thumb_end, 0.9)
        elif mode == "cup_mouth":
            # Splayed fingers curve toward the mouth without adding a megaphone.
            for index, spread in enumerate((-2.0, -0.65, 0.65, 2.0)):
                start = _offset(center, normal[0] * spread * 0.55, normal[1] * spread * 0.55)
                curl = 3.5 + 0.4 * (1.5 - abs(index - 1.5))
                end = _offset(start, along[0] * curl - normal[0] * spread * 0.28, along[1] * curl - normal[1] * spread * 0.28)
                finger(start, end, 0.75)
        else:
            thumb = _offset(center, normal[0] * 1.2, normal[1] * 1.2)
            finger(thumb, _offset(thumb, along[0] * 2.2, along[1] * 2.2), 0.75)

    def _draw_head(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
        center: Point,
        pose: Pose,
    ) -> None:
        cx, cy = center

        def R(point: Point) -> Point:
            return _rotate(point, center, pose.head_tilt)

        # Ear first, behind the long three-quarter face.
        ear = R((cx - 13.7, cy + 0.8))
        _ellipse(draw, ear, 4.5, 6.7, SKIN_SHADE, OUTLINE, 0.9)
        _line(draw, [R((cx - 15.0, cy - 1.0)), R((cx - 12.8, cy + 1.5)), R((cx - 14.5, cy + 4.8))], SKIN_DEEP, 0.5)

        face = [
            R((cx - 9.0, cy - 20.0)),
            R((cx + 1.0, cy - 22.0)),
            R((cx + 9.5, cy - 18.0)),
            R((cx + 13.5, cy - 10.0)),
            R((cx + 15.0, cy - 2.0)),
            R((cx + 20.0, cy + 2.8)),
            R((cx + 14.4, cy + 7.0)),
            R((cx + 11.0, cy + 15.0)),
            R((cx + 3.5, cy + 21.0)),
            R((cx - 3.2, cy + 18.0)),
            R((cx - 8.0, cy + 10.5)),
            R((cx - 10.5, cy + 1.0)),
            R((cx - 10.0, cy - 11.5)),
        ]
        _poly(draw, face, SKIN, OUTLINE, 1.2)

        # High forehead and gaunt cheek planes.
        _poly(
            draw,
            [R((cx - 6.0, cy - 16.5)), R((cx + 1.5, cy - 20.0)), R((cx + 5.0, cy - 9.0)), R((cx - 2.5, cy - 6.5))],
            SKIN_LIGHT,
            None,
            0,
        )
        _poly(
            draw,
            [R((cx + 7.5, cy + 3.5)), R((cx + 14.0, cy + 6.0)), R((cx + 10.5, cy + 14.0)), R((cx + 3.0, cy + 17.0))],
            SKIN_SHADE,
            None,
            0,
        )

        # Swept-back silver hair: high crown, separated wisps, exposed forehead.
        hair_mass = [
            R((cx - 9.5, cy - 15.5)),
            R((cx - 11.0, cy - 24.0)),
            R((cx - 5.0, cy - 28.5)),
            R((cx + 1.5, cy - 31.5)),
            R((cx + 8.0, cy - 30.0)),
            R((cx + 12.5, cy - 25.0)),
            R((cx + 8.5, cy - 21.5)),
            R((cx + 3.0, cy - 24.0)),
            R((cx - 1.5, cy - 18.0)),
            R((cx - 6.0, cy - 9.0)),
            R((cx - 11.0, cy - 7.5)),
        ]
        _poly(draw, hair_mass, HAIR, OUTLINE, 1.0)
        # Distinct upward/backward tufts make the silhouette recognizable at 1x.
        _poly(
            draw,
            [R((cx - 7.0, cy - 25.0)), R((cx - 8.0, cy - 32.0)), R((cx - 2.0, cy - 28.0))],
            HAIR_LIGHT,
            OUTLINE_SOFT,
            0.45,
        )
        _poly(
            draw,
            [R((cx - 1.5, cy - 29.0)), R((cx + 1.0, cy - 35.0)), R((cx + 5.0, cy - 29.5))],
            HAIR_LIGHT,
            OUTLINE_SOFT,
            0.45,
        )
        _poly(
            draw,
            [R((cx + 4.0, cy - 29.0)), R((cx + 9.0, cy - 34.0)), R((cx + 10.5, cy - 27.0))],
            HAIR_SHADE,
            OUTLINE_SOFT,
            0.45,
        )
        _line(draw, [R((cx - 4.0, cy - 25.5)), R((cx + 2.5, cy - 31.0)), R((cx + 8.5, cy - 29.0))], HAIR_LIGHT, 0.8)
        _line(draw, [R((cx - 8.0, cy - 15.0)), R((cx - 6.0, cy - 25.0))], HAIR_SHADE, 0.7)
        _line(draw, [R((cx - 6.0, cy - 9.0)), R((cx - 10.0, cy - 19.0))], HAIR, 1.0)
        _line(draw, [R((cx - 2.0, cy - 17.0)), R((cx + 2.0, cy - 23.0)), R((cx + 6.0, cy - 22.0))], OUTLINE_SOFT, 0.6)

        # Rectangular glasses with a slightly oversized near lens.
        far_center = R((cx - 2.3, cy - 4.7))
        near_center = R((cx + 7.0, cy - 4.5))
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        od = blending_draw(overlay)
        _rounded(od, (far_center[0] - 4.6, far_center[1] - 3.8, far_center[0] + 4.6, far_center[1] + 3.8), 1.6, GLASS_TINT, None, 0)
        _rounded(od, (near_center[0] - 5.3, near_center[1] - 4.2, near_center[0] + 5.3, near_center[1] + 4.2), 1.8, GLASS_TINT, None, 0)
        image.alpha_composite(overlay)
        draw = blending_draw(image)
        _rounded(draw, (far_center[0] - 4.6, far_center[1] - 3.8, far_center[0] + 4.6, far_center[1] + 3.8), 1.6, None, GLASS_FRAME, 0.95)
        _rounded(draw, (near_center[0] - 5.3, near_center[1] - 4.2, near_center[0] + 5.3, near_center[1] + 4.2), 1.8, None, GLASS_FRAME, 1.05)
        _line(draw, [R((cx + 2.3, cy - 4.6)), R((cx + 2.7, cy - 4.6))], GLASS_FRAME, 0.8)
        _line(draw, [R((cx + 12.4, cy - 5.0)), R((cx + 16.0, cy - 6.5))], GLASS_FRAME, 0.65)
        _line(draw, [R((cx - 6.8, cy - 4.8)), R((cx - 11.0, cy - 6.0))], GLASS_FRAME, 0.55)

        # Eyes track the imagined plane rather than the viewer.
        for near, lens in ((False, far_center), (True, near_center)):
            if pose.blink:
                _line(draw, [(lens[0] - 2.0, lens[1]), (lens[0] + 2.0, lens[1])], EYE, 0.65)
            else:
                rx = 1.18 if near else 1.0
                _ellipse(draw, lens, rx, 1.15, EYE_WHITE, OUTLINE, 0.3)
                pupil = (
                    lens[0] + pose.gaze_x * (0.65 if near else 0.5),
                    lens[1] + pose.gaze_y * 0.55,
                )
                _ellipse(draw, pupil, 0.52 if near else 0.43, 0.56, EYE, EYE, 0.1)
            brow_y = -10.5 - pose.brow_lift * (1.0 if near else 0.7)
            if near:
                _line(draw, [R((cx + 2.0, cy + brow_y)), R((cx + 10.5, cy + brow_y - 0.8))], HAIR_SHADE, 0.8)
            else:
                _line(draw, [R((cx - 6.5, cy + brow_y + 0.5)), R((cx - 0.8, cy + brow_y))], HAIR_SHADE, 0.65)

        # Long nose bridge and projected tip keep the head from reading as a
        # generic round elderly face.
        _line(draw, [R((cx + 2.8, cy - 0.5)), R((cx + 5.3, cy + 5.5))], SKIN_SHADE, 0.8)
        _line(draw, [R((cx + 5.3, cy + 5.5)), R((cx + 12.0, cy + 6.0)), R((cx + 7.2, cy + 8.2))], OUTLINE_SOFT, 0.68)
        _line(draw, [R((cx + 8.0, cy + 7.5)), R((cx + 10.0, cy + 8.6))], SKIN_DEEP, 0.35)

        mouth_center = R((cx + 5.5, cy + 13.0))
        if pose.mouth_open > 0.2:
            mouth_rx = 3.7 + pose.mouth_round * 1.8
            mouth_ry = 0.75 + pose.mouth_open * 2.2
            _ellipse(draw, mouth_center, mouth_rx, mouth_ry, MOUTH, OUTLINE, 0.55)
            if pose.mouth_round < 0.55:
                _line(draw, [(mouth_center[0] - mouth_rx * 0.55, mouth_center[1] - 0.1), (mouth_center[0] + mouth_rx * 0.45, mouth_center[1] - 0.1)], TEETH, 0.55)
        else:
            curve = pose.mouth_smile * 2.2
            _line(
                draw,
                [
                    R((cx + 1.2, cy + 12.7)),
                    R((cx + 5.6, cy + 13.2 + curve)),
                    R((cx + 10.0, cy + 12.5)),
                ],
                MOUTH,
                0.75,
            )

        # Sparse age lines survive the downsample without muddying the face.
        _line(draw, [R((cx - 4.0, cy - 14.0)), R((cx + 2.0, cy - 14.8))], SKIN_SHADE, 0.35)
        _line(draw, [R((cx + 7.0, cy + 7.2)), R((cx + 10.0, cy + 8.5))], SKIN_DEEP, 0.35)
        _line(draw, [R((cx - 5.5, cy + 3.5)), R((cx - 4.5, cy + 9.0))], SKIN_SHADE, 0.35)
        _line(draw, [R((cx + 0.5, cy + 17.1)), R((cx + 6.3, cy + 17.4))], SKIN_DEEP, 0.4)

    def _draw_shrinkwrap_field(self, draw: ImageDraw.ImageDraw, pose: Pose, T, *, front: bool) -> None:
        """Draw iterative manifold contours and shrinking residual vectors."""
        strength = pose.manifold_strength
        progress = pose.manifold_progress
        center = (72.0, 103.0)
        target = [
            (58.0, 72.0),
            (76.0, 68.0),
            (91.0, 75.0),
            (107.0, 90.0),
            (103.0, 111.0),
            (91.0, 123.0),
            (91.0, 148.0),
            (73.0, 153.0),
            (53.0, 148.0),
            (53.0, 123.0),
            (40.0, 111.0),
            (36.0, 90.0),
        ]
        rings: list[list[Point]] = []
        for ring_idx, start_scale in enumerate((1.31, 1.20, 1.10)):
            local_progress = _smoothstep((progress - ring_idx * 0.11) / 0.78)
            scale = _lerp(start_scale, 1.015 + ring_idx * 0.008, local_progress)
            wobble = (1.0 - local_progress) * (1.8 - ring_idx * 0.35)
            ring: list[Point] = []
            for index, point in enumerate(target):
                angle = pose.manifold_phase * math.tau * 1.35 + index * 0.83 + ring_idx
                radial = (
                    center[0] + (point[0] - center[0]) * scale + math.cos(angle) * wobble,
                    center[1] + (point[1] - center[1]) * scale + math.sin(angle) * wobble,
                )
                ring.append(T(radial))
            rings.append(ring)

        if not front:
            # Back pass: all optimization iterates and sparse cross-links form a
            # genuine surface rather than a magic circular shield.
            for ring_idx, ring in enumerate(rings):
                alpha_scale = strength * (0.56 + ring_idx * 0.17)
                color = _fade(MANIFOLD_SOFT if ring_idx < 2 else MANIFOLD, alpha_scale)
                _line(draw, ring + [ring[0]], color, 0.72 + ring_idx * 0.18)
            for index in range(0, len(target), 2):
                _line(
                    draw,
                    [rings[0][index], rings[1][index], rings[2][index]],
                    _fade(MANIFOLD_SOFT, strength, 0.9),
                    0.48,
                )
            return

        # Foreground pass: the near/lower half crosses his body.  Orange residual
        # vectors visibly collapse to zero as the inner contour reaches the fit.
        near_indices = list(range(3, 10))
        inner = rings[2]
        near_path = [inner[index] for index in near_indices]
        _line(draw, near_path, _fade(MANIFOLD, strength, 0.95), 1.05)
        for index in (3, 5, 7, 9):
            node = inner[index]
            target_point = T(target[index])
            residual_alpha = strength * (1.0 - progress)
            if residual_alpha > 0.04:
                _line(draw, [node, target_point], _fade(MANIFOLD_NODE, residual_alpha), 0.72)
            pulse = 0.80 + 0.20 * math.sin((pose.manifold_phase + index / 12.0) * math.tau) ** 2
            _ellipse(
                draw,
                node,
                1.15 + 0.45 * pulse,
                1.15 + 0.45 * pulse,
                _fade(MANIFOLD_NODE, strength, pulse),
                _fade(OUTLINE_SOFT, strength),
                0.35,
            )

    def _draw_leg_armor(self, draw: ImageDraw.ImageDraw, pose: Pose, T) -> None:
        strength = pose.armor_strength
        edge_strength = min(1.0, strength + pose.armor_lock * 0.55)
        for far, hip, knee, ankle in (
            (True, T(pose.far_hip), T(pose.far_knee), T(pose.far_ankle)),
            (False, T(pose.near_hip), T(pose.near_knee), T(pose.near_ankle)),
        ):
            base = ARMOR_DARK if far else ARMOR_MID
            highlight = ARMOR_MID if far else ARMOR_LIGHT
            thigh_end = _lerp_point(hip, knee, 0.88)
            shin_start = _lerp_point(knee, ankle, 0.16)
            shin_end = _lerp_point(knee, ankle, 0.88)
            _poly(draw, _segment_quad(hip, thigh_end, 5.8, 4.5), _fade(base, strength), _fade(OUTLINE, strength), 0.85)
            _poly(draw, _segment_quad(shin_start, shin_end, 4.7, 4.0), _fade(highlight, strength), _fade(OUTLINE, strength), 0.85)
            _ellipse(draw, knee, 5.0, 4.2, _fade(ARMOR_CORE, strength), _fade(OUTLINE, strength), 0.75)
            _, normal, _ = _unit_segment(shin_start, shin_end)
            ridge_a = _offset(shin_start, normal[0] * 1.2, normal[1] * 1.2)
            ridge_b = _offset(shin_end, normal[0] * 0.8, normal[1] * 0.8)
            _line(draw, [ridge_a, ridge_b], _fade(ARMOR_EDGE, edge_strength), 0.62)

    def _draw_torso_armor(self, draw: ImageDraw.ImageDraw, pose: Pose, T) -> None:
        strength = pose.armor_strength
        edge_strength = min(1.0, strength + pose.armor_lock * 0.65)
        shell = [
            T((58.0, 79.0)),
            T((67.0, 73.0)),
            T((78.0, 72.5)),
            T((88.5, 78.0)),
            T((90.0, 93.0)),
            T((84.0, 112.0)),
            T((73.0, 118.0)),
            T((61.0, 112.0)),
            T((54.0, 94.0)),
        ]
        _poly(draw, shell, _fade(ARMOR_DARK, strength), _fade(OUTLINE, strength), 1.05)
        left_plate = [T((59.0, 81.0)), T((69.5, 75.5)), T((71.0, 94.0)), T((61.0, 103.0)), T((56.5, 91.5))]
        right_plate = [T((75.0, 75.0)), T((86.5, 80.0)), T((88.0, 93.0)), T((78.0, 103.0)), T((73.5, 94.0))]
        abdomen = [T((62.0, 105.0)), T((72.5, 96.0)), T((82.5, 104.0)), T((81.0, 114.0)), T((72.5, 118.0)), T((63.0, 113.0))]
        _poly(draw, left_plate, _fade(ARMOR_MID, strength), _fade(OUTLINE_SOFT, strength), 0.62)
        _poly(draw, right_plate, _fade(ARMOR_LIGHT, strength), _fade(OUTLINE_SOFT, strength), 0.62)
        _poly(draw, abdomen, _fade(ARMOR_CORE, strength), _fade(OUTLINE_SOFT, strength), 0.62)
        seam = [T((72.5, 76.0)), T((72.5, 94.0)), T((72.5, 116.0))]
        _line(draw, seam, _fade(ARMOR_EDGE, edge_strength), 0.88)
        for y in (87.0, 101.0, 113.0):
            _ellipse(draw, T((72.5, y)), 1.15, 1.15, _fade(ARMOR_EDGE, edge_strength), _fade(OUTLINE_SOFT, strength), 0.25)

    def _draw_arm_armor(
        self,
        draw: ImageDraw.ImageDraw,
        pose: Pose,
        shoulder: Point,
        elbow: Point,
        hand: Point,
        *,
        far: bool,
    ) -> None:
        strength = pose.armor_strength
        edge_strength = min(1.0, strength + pose.armor_lock * 0.55)
        upper_end = _lerp_point(shoulder, elbow, 0.86)
        fore_start = _lerp_point(elbow, hand, 0.10)
        fore_end = _lerp_point(elbow, hand, 0.72)
        base = ARMOR_DARK if far else ARMOR_MID
        highlight = ARMOR_MID if far else ARMOR_LIGHT
        _ellipse(draw, shoulder, 6.7, 6.0, _fade(base, strength), _fade(OUTLINE, strength), 0.85)
        _poly(draw, _segment_quad(shoulder, upper_end, 5.7, 4.4), _fade(base, strength), _fade(OUTLINE, strength), 0.78)
        _poly(draw, _segment_quad(fore_start, fore_end, 4.5, 3.7), _fade(highlight, strength), _fade(OUTLINE, strength), 0.78)
        _ellipse(draw, elbow, 4.5, 4.2, _fade(ARMOR_CORE, strength), _fade(OUTLINE, strength), 0.7)
        _, normal, _ = _unit_segment(fore_start, fore_end)
        ridge_a = _offset(fore_start, normal[0] * 1.0, normal[1] * 1.0)
        ridge_b = _offset(fore_end, normal[0] * 0.7, normal[1] * 0.7)
        _line(draw, [ridge_a, ridge_b], _fade(ARMOR_EDGE, edge_strength), 0.58)

    def _draw_armor_collar(self, draw: ImageDraw.ImageDraw, pose: Pose, T) -> None:
        strength = pose.armor_strength
        edge_strength = min(1.0, strength + pose.armor_lock * 0.7)
        left = [T((58.0, 78.0)), T((64.0, 69.5)), T((69.5, 75.0)), T((66.0, 84.0))]
        right = [T((77.0, 74.0)), T((82.0, 68.8)), T((88.0, 78.0)), T((80.0, 84.0))]
        _poly(draw, left, _fade(ARMOR_MID, strength), _fade(OUTLINE, strength), 0.75)
        _poly(draw, right, _fade(ARMOR_LIGHT, strength), _fade(OUTLINE, strength), 0.75)
        _line(draw, [T((64.0, 70.5)), T((72.5, 76.0)), T((82.0, 69.8))], _fade(ARMOR_EDGE, edge_strength), 0.72)

    def _draw_hint_trace(self, draw: ImageDraw.ImageDraw, pose: Pose) -> None:
        strength = pose.hint_strength
        alpha = int(160 * strength)
        path_color = (PLANE[0], PLANE[1], PLANE[2], alpha)
        # A short reasoning path exits the temple and bends toward the pointing
        # hand.  It reads as thought motion, not a physical pointer or prop.
        points = [(89.0, 45.0), (101.0, 38.0), (111.0, 45.0), (119.0, 58.0)]
        _line(draw, points, path_color, 1.1 + strength)
        for index, point in enumerate(points[1:]):
            radius = 1.2 + 0.7 * math.sin((pose.plane_phase + index / 3.0) * math.tau) ** 2
            _ellipse(draw, point, radius, radius, (POINT_A[0], POINT_A[1], POINT_A[2], int(210 * strength)), OUTLINE_SOFT, 0.35)
        # Arrow chevron only; no floating bulb icon.
        _line(draw, [(116.5, 54.5), (121.0, 59.0), (116.0, 61.0)], path_color, 1.25)

    def _draw_coordinate_plane(self, draw: ImageDraw.ImageDraw, pose: Pose) -> None:
        strength = pose.plane_strength
        alpha = int(PLANE[3] * strength)
        soft_alpha = int(PLANE_SOFT[3] * strength)
        axis = (PLANE[0], PLANE[1], PLANE[2], alpha)
        grid = (PLANE_SOFT[0], PLANE_SOFT[1], PLANE_SOFT[2], soft_alpha)
        left, top, right, bottom = 92.0, 28.0, 154.0, 105.0

        # Perspective-free, explicitly 2-D axes and grid.
        for x in (104.0, 116.0, 128.0, 140.0, 152.0):
            _line(draw, [(x, top + 4.0), (x, bottom - 4.0)], grid, 0.55)
        for y in (40.0, 52.0, 64.0, 76.0, 88.0, 100.0):
            _line(draw, [(left + 4.0, y), (right - 3.0, y)], grid, 0.55)
        origin = (106.0, 88.0)
        _line(draw, [(left + 2.0, origin[1]), (right - 1.0, origin[1])], axis, 1.15)
        _line(draw, [(origin[0], bottom - 2.0), (origin[0], top + 1.0)], axis, 1.15)
        _line(draw, [(right - 5.0, origin[1] - 2.4), (right - 1.0, origin[1]), (right - 5.0, origin[1] + 2.4)], axis, 0.85)
        _line(draw, [(origin[0] - 2.4, top + 5.0), (origin[0], top + 1.0), (origin[0] + 2.4, top + 5.0)], axis, 0.85)

        # A rotating cloud and covariance ellipse provide the "visualizing a 2-D
        # space" gag without relying on any external asset.
        angle = pose.plane_phase * math.tau * 0.7
        points = [
            (-15.0, 10.0, POINT_A),
            (-8.0, -7.0, POINT_B),
            (2.0, 4.0, POINT_C),
            (11.0, -12.0, POINT_A),
            (17.0, 7.0, POINT_B),
            (4.0, -20.0, POINT_C),
            (23.0, -3.0, POINT_A),
        ]
        c = math.cos(angle)
        s = math.sin(angle)
        cloud_center = (126.0, 64.0)
        rotated_points: list[Point] = []
        for index, (px, py, color) in enumerate(points):
            rx = px * c - py * s
            ry = px * s + py * c
            point = (cloud_center[0] + rx, cloud_center[1] + ry)
            rotated_points.append(point)
            pulse = 0.75 + 0.25 * math.sin((pose.plane_phase + index / len(points)) * math.tau) ** 2
            fill = (color[0], color[1], color[2], int(color[3] * strength * pulse))
            _ellipse(draw, point, 1.6 + 0.5 * pulse, 1.6 + 0.5 * pulse, fill, OUTLINE_SOFT, 0.35)

        # Principal axis and a projected point make the mental model concrete.
        axis_a = (111.0, 76.0)
        axis_b = (146.0, 48.0)
        _line(draw, [axis_a, axis_b], (POINT_A[0], POINT_A[1], POINT_A[2], int(180 * strength)), 0.85)
        tracked = rotated_points[1]
        projection = (tracked[0], origin[1])
        _line(draw, [tracked, projection], (POINT_B[0], POINT_B[1], POINT_B[2], int(115 * strength)), 0.65)
        _ellipse(draw, projection, 1.1, 1.1, (POINT_B[0], POINT_B[1], POINT_B[2], int(170 * strength)), None, 0)

        # Handwritten-style x/y labels kept tiny enough not to dominate.
        label_font = _font(4.2, bold=True)
        draw.text(_pt((150.0, 90.0)), "x", font=label_font, fill=axis, anchor="mm")
        draw.text(_pt((102.0, 32.0)), "y", font=label_font, fill=axis, anchor="mm")

    def _draw_shout(self, image: Image.Image, pose: Pose, head_center: Point) -> None:
        strength = pose.shout_strength
        if strength <= 0.0:
            return
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = blending_draw(overlay)

        # The word starts near the mouth and expands sharply to the right.  It is
        # intentionally diegetic sprite FX, not dialogue UI.
        pop = _smoothstep(min(1.0, strength * 1.35))
        wobble = math.sin(pose.shout_phase * math.pi * 9.0) * (1.0 - pose.shout_phase) * 1.5
        text = pose.shout_text
        # A single digit can flare larger than the two-digit scientific
        # reference while staying inside the 160 px frame.
        if text == "3":
            size = 13.0 + 14.0 * pop
            x_offset = 29.0 + 2.0 * pop
        else:
            size = 12.0 + 12.0 * pop
            x_offset = 32.0 + 3.0 * pop
        font = _font(size, bold=True)
        origin = (
            head_center[0] + x_offset,
            head_center[1] - 15.0 - 9.0 * pop + wobble,
        )
        stroke_width = max(1, _s(0.9 + 0.5 * pop))
        draw.text(
            _pt(origin),
            text,
            font=font,
            fill=(SHOUT[0], SHOUT[1], SHOUT[2], int(255 * strength)),
            stroke_width=stroke_width,
            stroke_fill=(SHOUT_DEEP[0], SHOUT_DEEP[1], SHOUT_DEEP[2], int(245 * strength)),
            anchor="mm",
        )

        # Expanding sound rays and smaller numeral echoes sell absurd volume.
        ray_alpha = int(220 * strength)
        ray = (SHOUT[0], SHOUT[1], SHOUT[2], ray_alpha)
        ray_origin = (head_center[0] + 19.0, head_center[1] + 6.0)
        for degrees, length in ((-54.0, 15.0), (-27.0, 19.0), (0.0, 21.0), (26.0, 18.0), (51.0, 14.0)):
            radians = math.radians(degrees)
            start = (ray_origin[0] + math.cos(radians) * 5.0, ray_origin[1] + math.sin(radians) * 5.0)
            end = (ray_origin[0] + math.cos(radians) * length, ray_origin[1] + math.sin(radians) * length)
            _line(draw, [start, end], ray, 1.0 + 0.55 * pop)

        small_font = _font(4.8, bold=True)
        for index, (dx, dy) in enumerate(((42.0, 13.0), (50.0, 4.0), (46.0, 24.0))):
            fade = strength * (0.55 + 0.15 * index)
            draw.text(
                _pt((head_center[0] + dx, head_center[1] + dy)),
                text,
                font=small_font,
                fill=(SHOUT[0], SHOUT[1], SHOUT[2], int(190 * fade)),
                anchor="mm",
            )

        image.alpha_composite(overlay)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    from ...authoring.sheet_build import build_sheet

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    renderer = JeffHinterRenderer()
    outputs = build_sheet(
        target=TARGET_BASENAME,
        rows=ROWS,
        render_fn=renderer.render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.05},
        trim=False,
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


__all__ = ["ACTOR_METADATA", "render"]
