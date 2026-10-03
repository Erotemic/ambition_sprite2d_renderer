"""Procedural sprite target for Jeff Hinter, the excessively emphatic hint NPC.

Jeff Hinter is a playful academic caricature: a compact elderly researcher with
swept silver hair, a high forehead, rectangular glasses, a long analytical face,
and a permanently inward-looking posture.  He gives useful hints, but sometimes
forgets the room exists while mentally arranging points in a two-dimensional
space.  When a high-dimensional pattern clicks, he bellows ``14``; when
the two-dimensional game refuses to provide a way around a wall, he tries
to conjure the missing axis by shouting ``3`` instead.

The renderer is deliberately character-specific rather than a recolored toon
preset.  It authors all geometry in Python/Pillow and includes dedicated acting
for conversation, hint delivery, 2-D visualization, the ``14`` and ``3``
dimensional outbursts, and a manifold shrinkwrap that converges into
body-conforming armor.  The coordinate
plane, optimization mesh, and typography are transient effects, not held
props.  The base character has no held item, no floor ellipse, and no drop
shadow.  Painter order is legs -> torso -> both arms -> head, keeping the head
and face cleanly readable and both arms in front of the torso.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont
from ambition_sprite2d_renderer.core.draw import blending_draw

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_BASENAME = "jeff_hinter"
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
    # Runtime-recognized defensive alias.  It reuses the full shrinkwrap beat so
    # ordinary block requests still produce Jeff's character-specific armor.
    ("block", 16, 82),
    # Runtime-recognized expressive alias for scripted uses that only know the
    # common CharacterAnim vocabulary.  It intentionally reuses the outburst.
    ("taunt", 12, 78),
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_jeff_hinter", "display_name": "Jeff Hinter"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": ["story", "humanoid", "scholar", "hint_npc", "ai_history", "manifold_armor"],
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
    "tags": ["story", "humanoid", "scholar", "hint_npc", "ai_history", "manifold_armor"],
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
        "defense.block": {"animation": "block", "events": []},
    },
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Jeff Hinter is an affectionate caricature of Geoffrey Hinton, recast as an "
            "overenthusiastic hint NPC. He thinks in representations, dimensions, optimization "
            "landscapes, and manifold geometry, but is liable to shout the missing dimension before "
            "noticing that the game remains stubbornly two-dimensional."
        ),
        "gameplay_description": (
            "Use as a hint giver, machine-learning sage, comic lecturer, or transformation-capable "
            "support character. His hints should become useful before they become lectures; his "
            "special effects should project, compress, optimize, and occasionally lose something "
            "important."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'THREE! ...No. Still two-dimensional.',
        'A hint should become useful before it becomes a lecture.',
        'I projected away something important, usually a ladder.',
    ],
)

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

        elif animation in {"manifold_shrinkwrap", "block"}:
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


# --- Rig construction -------------------------------------------------------
#
# Jeff is drawn as a rig (``shape_rig``): every rigid piece is painted once in
# its own frame, at the supersampled scale, and turned into place. The torso
# rides the body's lean, the head its tilt, each limb is two bones turned
# from joint to joint (one piece per whole-pixel length), and the hands,
# shoes and armor plates ride their bones. The coordinate plane, hint trace,
# manifold field and shout are effects that change every frame: each layer is
# one raster a frame.

def _bone_length(a: Point, b: Point) -> float:
    """A limb bone's length, to the whole frame pixel: the poses foreshorten
    Jeff's arms (a hand cupped to the mouth, a frame bracketed in front of
    him), so a bone keeps its pose's length, and a piece is one per length."""
    return float(max(1, round(math.hypot(b[0] - a[0], b[1] - a[1]))))


def _angle(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _piece(key, half: float, paint) -> Tuple[Image.Image, Point]:
    """A piece ``2 * half`` frame pixels square, its pivot at the centre:
    ``paint(draw, o)`` paints it with the local origin at ``(o, o)`` frame px."""
    size = 2 * _s(half)
    return shape_rig.piece(("jeff_hinter",) + tuple(key), (size, size), (size / 2, size / 2), lambda d: paint(d, half))


def _put(canvas: Image.Image, part, at: Point, degrees: float, name: str, opacity: float = 1.0) -> None:
    image, pivot = part
    rigdoc.blit_rotated(canvas, image, pivot, (at[0] * SUPER, at[1] * SUPER), degrees, opacity, part_name=name)


def _effect(canvas: Image.Image, paint, name: str) -> None:
    """A per-frame effect layer as one raster: painted on its own canvas,
    cropped to what it covers, placed at its corner."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    paint(layer, blending_draw(layer))
    box = layer.getbbox()
    if box is None:
        return
    shape_rig.place(canvas, (layer.crop(box), (0.0, 0.0)), (box[0], box[1]), 0.0, name)


def _paint_bone(draw, o: float, length: float, ra: float, rb: float, fill: RGBA, width: float, *, root_cap: bool, joint_cap: bool) -> None:
    """A tapered limb segment along +x from ``(o, o)``: the joint disc first
    (under the segment, so its outline shows only past the bend), the
    segment's fill and side outlines, and the root/end disc."""
    a, b = (o, o), (o + length, o)
    if joint_cap:
        _ellipse(draw, b, rb, rb, fill, OUTLINE, width)
    _poly(draw, [(a[0], o + ra), (b[0], o + rb), (b[0], o - rb), (a[0], o - ra)], fill, None, 0)
    _line(draw, [(a[0], o + ra), (b[0], o + rb)], OUTLINE, width)
    _line(draw, [(a[0], o - ra), (b[0], o - rb)], OUTLINE, width)
    if root_cap:
        _ellipse(draw, a, ra, ra, fill, OUTLINE, width)
    else:
        _ellipse(draw, b, rb, rb, fill, OUTLINE, width)


class JeffHinterRenderer:
    #: The pose a frame is drawn from (the armored sheet passes its own).
    pose_cls = Pose

    def render_frame(self, animation: str, frame_idx: int, nframes: int) -> Image.Image:
        image = Image.new(
            "RGBA",
            (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER),
            (0, 0, 0, 0),
        )
        pose = self.pose_cls(animation, frame_idx, nframes)

        pivot = (73.0 + pose.body_x, 112.0 + pose.body_y)

        def T(point: Point) -> Point:
            moved = (point[0] + pose.body_x, point[1] + pose.body_y)
            return _rotate(moved, pivot, pose.lean)

        # Effects are staged behind the person so the silhouette remains the
        # strongest read.  The shrinkwrap gets a second foreground pass below the
        # face so the contracting surface visibly crosses the body.
        if pose.plane_strength > 0.01 or pose.hint_strength > 0.01 or pose.manifold_strength > 0.01:

            def behind(_layer, draw) -> None:
                if pose.plane_strength > 0.01:
                    self._draw_coordinate_plane(draw, pose)
                if pose.hint_strength > 0.01:
                    self._draw_hint_trace(draw, pose)
                if pose.manifold_strength > 0.01:
                    self._draw_shrinkwrap_field(draw, pose, T, front=False)

            _effect(image, behind, "effects_behind")

        # The armor fades in as whole plates (a draw's opacity). Painted shape by
        # shape, a plate over the shell compounded its fade; this matches that.
        armor = 1.0 - (1.0 - pose.armor_strength) ** 2 if pose.armor_strength > 0.01 else 0.0

        # No baked floor ellipse or drop shadow.  Far leg, then near.
        for far, hip, knee, ankle in (
            (True, pose.far_hip, pose.far_knee, pose.far_ankle),
            (False, pose.near_hip, pose.near_knee, pose.near_ankle),
        ):
            self._place_leg(image, T(hip), T(knee), T(ankle), far, armor)

        torso_at = (73.0 + pose.body_x, 112.0 + pose.body_y)
        _put(image, _piece(("torso",), 52.0, self._paint_torso), torso_at, pose.lean, "torso")
        if armor:
            _put(image, _piece(("torso_armor",), 52.0, self._paint_torso_armor), torso_at, pose.lean, "torso_armor", armor)

        # Both arms are deliberately in front of the torso.
        self._place_arm(image, T(pose.far_shoulder), T(pose.far_elbow), T(pose.far_hand), pose.far_hand_mode, True, armor)
        self._place_arm(image, T(pose.near_shoulder), T(pose.near_elbow), T(pose.near_hand), pose.near_hand_mode, False, armor)
        if armor:
            _put(image, _piece(("collar",), 52.0, self._paint_collar), torso_at, pose.lean, "collar", armor)

        head_center = T((72.0 + pose.head_x, 48.0 + pose.head_y))
        self._place_head(image, head_center, pose)

        if pose.manifold_strength > 0.01 or pose.shout_strength > 0.01:

            def front(layer, draw) -> None:
                if pose.manifold_strength > 0.01:
                    self._draw_shrinkwrap_field(draw, pose, T, front=True)
                if pose.shout_strength > 0.01:
                    self._draw_shout(layer, pose, head_center)

            _effect(image, front, "effects_front")

        return rigdoc.downsampled_canvas(image, FRAME_SIZE, Image.Resampling.LANCZOS)

    # -- limbs --------------------------------------------------------------

    def _place_leg(self, image: Image.Image, hip: Point, knee: Point, ankle: Point, far: bool, armor: float) -> None:
        side = "far" if far else "near"
        thigh_len, shin_len = _bone_length(hip, knee), _bone_length(knee, ankle)
        radii = (6.3, 5.2, 4.4) if far else (6.6, 5.4, 4.6)
        fill = TROUSER if far else TROUSER_LIGHT
        width = 1.15 if far else 1.2
        thigh = _piece(("thigh", far, thigh_len), 30.0, lambda d, o: _paint_bone(d, o, thigh_len, radii[0], radii[1], fill, width, root_cap=True, joint_cap=True))
        _put(image, thigh, hip, _angle(hip, knee), f"{side}_thigh")

        def paint_shin(d, o) -> None:
            _paint_bone(d, o, shin_len, radii[1], radii[2], fill, width, root_cap=False, joint_cap=False)
            if not far:
                # Trouser crease reinforces the long, slightly rumpled academic silhouette.
                _line(d, [(o, o), (o + shin_len, o)], TROUSER, 0.55)

        _put(image, _piece(("shin", far, shin_len), 30.0, paint_shin), knee, _angle(knee, ankle), f"{side}_shin")
        # The shoe stays flat on the ground: painted with the shin upright.
        _put(image, _piece(("shoe", far), 16.0, lambda d, o: self._paint_shoe(d, o, far)), ankle, 0.0, f"{side}_shoe")
        if armor:
            _put(image, _piece(("thigh_armor", far, thigh_len), 30.0, lambda d, o: self._paint_limb_plate(d, o, thigh_len, far, leg=True, upper=True)), hip, _angle(hip, knee), f"{side}_thigh_armor", armor)
            _put(image, _piece(("shin_armor", far, shin_len), 30.0, lambda d, o: self._paint_limb_plate(d, o, shin_len, far, leg=True, upper=False)), knee, _angle(knee, ankle), f"{side}_shin_armor", armor)

    def _place_arm(self, image: Image.Image, shoulder: Point, elbow: Point, hand: Point, mode: str, far: bool, armor: float) -> None:
        side = "far" if far else "near"
        upper_len, fore_len = _bone_length(shoulder, elbow), _bone_length(elbow, hand)
        sleeve = JACKET if far else JACKET_MID
        radii = (5.8 if far else 6.2, 4.8, 3.8)
        upper = _piece(("upper_arm", far, upper_len), 30.0, lambda d, o: _paint_bone(d, o, upper_len, radii[0], radii[1], sleeve, 1.15, root_cap=True, joint_cap=True))
        upper_angle = _angle(shoulder, elbow)
        _put(image, upper, shoulder, upper_angle, f"{side}_upper_arm")

        def paint_forearm(d, o) -> None:
            _paint_bone(d, o, fore_len, radii[1], radii[2], sleeve, 1.15, root_cap=False, joint_cap=False)
            # Shirt cuff prevents the hand from looking fused directly to the jacket.
            _line(d, [(o + fore_len * 0.85, o + 4.0), (o + fore_len * 0.85, o - 4.0)], SHIRT_LIGHT, 2.0)

        fore_angle = _angle(elbow, hand)
        _put(image, _piece(("forearm", far, fore_len), 30.0, paint_forearm), elbow, fore_angle, f"{side}_forearm")
        _put(image, _piece(("hand", far, mode), 16.0, lambda d, o: self._paint_hand(d, o, mode, far)), hand, fore_angle, f"{side}_hand")
        if armor:
            _put(image, _piece(("upper_arm_armor", far, upper_len), 30.0, lambda d, o: self._paint_limb_plate(d, o, upper_len, far, leg=False, upper=True)), shoulder, upper_angle, f"{side}_upper_arm_armor", armor)
            _put(image, _piece(("forearm_armor", far, fore_len), 30.0, lambda d, o: self._paint_limb_plate(d, o, fore_len, far, leg=False, upper=False)), elbow, fore_angle, f"{side}_forearm_armor", armor)

    def _paint_shoe(self, draw, o: float, far: bool) -> None:
        ankle = (o, o)
        along, normal = (0.0, 1.0), (-1.0, 0.0)
        toe = (ankle[0] + along[0] * 1.2 + 7.5, ankle[1] + along[1] * 1.0 + 0.8)
        heel = (ankle[0] - 3.3, ankle[1] + 2.2)
        points = [
            (ankle[0] - normal[0] * 4.6, ankle[1] - normal[1] * 4.6),
            (ankle[0] + normal[0] * 4.6, ankle[1] + normal[1] * 4.6),
            (toe[0], toe[1] + 2.0),
            (toe[0] + 0.4, toe[1] + 4.2),
            (heel[0], heel[1] + 4.0),
        ]
        _poly(draw, points, SHOE if far else SHOE_LIGHT, OUTLINE, 1.1)
        _line(draw, [(heel[0], heel[1] + 3.2), (toe[0] + 0.2, toe[1] + 3.5)], OUTLINE, 0.8)

    def _paint_hand(self, draw, o: float, mode: str, far: bool) -> None:
        """The hand in its forearm's frame (the forearm runs along +x)."""
        center = (o, o)
        along, normal = (1.0, 0.0), (0.0, 1.0)
        skin = SKIN_SHADE if far else SKIN
        _ellipse(draw, center, 4.8, 4.2, skin, OUTLINE, 0.9)

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

    def _paint_limb_plate(self, draw, o: float, length: float, far: bool, *, leg: bool, upper: bool) -> None:
        """One bone's armor plate in the bone's frame, at full strength (the
        draw's opacity fades it in): the upper plate (with the shoulder cap on
        an arm), or the lower plate with its joint cap and ridge."""
        root, end = (o, o), (o + length, o)
        base = ARMOR_DARK if far else ARMOR_MID
        highlight = ARMOR_MID if far else ARMOR_LIGHT
        if upper:
            if not leg:
                _ellipse(draw, root, 6.7, 6.0, base, OUTLINE, 0.85)
            reach, ra, rb, width = (0.88, 5.8, 4.5, 0.85) if leg else (0.86, 5.7, 4.4, 0.78)
            _poly(draw, _segment_quad(root, _lerp_point(root, end, reach), ra, rb), base, OUTLINE, width)
            return
        lo, hi, ra, rb, width = (0.16, 0.88, 4.7, 4.0, 0.85) if leg else (0.10, 0.72, 4.5, 3.7, 0.78)
        start, stop = _lerp_point(root, end, lo), _lerp_point(root, end, hi)
        if leg:
            _poly(draw, _segment_quad(start, stop, ra, rb), highlight, OUTLINE, width)
            _ellipse(draw, root, 5.0, 4.2, ARMOR_CORE, OUTLINE, 0.75)
            ridge = (1.2, 0.8, 0.62)
        else:
            _poly(draw, _segment_quad(start, stop, ra, rb), highlight, OUTLINE, width)
            _ellipse(draw, root, 4.5, 4.2, ARMOR_CORE, OUTLINE, 0.7)
            ridge = (1.0, 0.7, 0.58)
        _line(draw, [(start[0], start[1] + ridge[0]), (stop[0], stop[1] + ridge[1])], ARMOR_EDGE, ridge[2])

    # -- torso ------------------------------------------------------------

    def _paint_torso(self, draw, o: float) -> None:
        """The torso in the body's frame: ``(o, o)`` is the lean pivot (73, 112)."""

        def T(point: Point) -> Point:
            return (point[0] - 73.0 + o, point[1] - 112.0 + o)

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
        shirt = [T((67.0, 74.0)), T((77.0, 73.7)), T((80.5, 112.5)), T((68.0, 116.0)), T((63.0, 85.0))]
        _poly(draw, shirt, SHIRT, OUTLINE_SOFT, 0.65)
        _poly(draw, [T((67.0, 74.0)), T((72.0, 80.0)), T((64.5, 83.0))], SHIRT_LIGHT, OUTLINE_SOFT, 0.5)
        _poly(draw, [T((77.0, 73.7)), T((72.0, 80.0)), T((80.0, 83.0))], SHIRT_DARK, OUTLINE_SOFT, 0.5)
        # Jacket lapels, seams, and subtle academic rumpling.
        _poly(draw, [T((62.0, 76.0)), T((68.0, 75.0)), T((66.0, 95.0)), T((57.5, 84.0))], JACKET_MID, OUTLINE_SOFT, 0.55)
        _poly(draw, [T((78.0, 74.0)), T((86.5, 77.0)), T((87.5, 88.0)), T((79.0, 96.0))], JACKET_LIGHT, OUTLINE_SOFT, 0.55)
        _line(draw, [T((72.5, 84.0)), T((73.0, 114.0))], OUTLINE_SOFT, 0.55)
        _line(draw, [T((57.0, 103.0)), T((64.0, 106.5))], JACKET_LIGHT, 0.55)
        _line(draw, [T((81.0, 105.0)), T((87.0, 102.0))], JACKET_DARK, 0.55)
        _ellipse(draw, T((73.0, 98.0)), 0.85, 0.85, OUTLINE_SOFT, OUTLINE_SOFT, 0.2)
        _ellipse(draw, T((73.0, 108.0)), 0.85, 0.85, OUTLINE_SOFT, OUTLINE_SOFT, 0.2)

    def _paint_torso_armor(self, draw, o: float) -> None:
        def T(point: Point) -> Point:
            return (point[0] - 73.0 + o, point[1] - 112.0 + o)

        shell = [T((58.0, 79.0)), T((67.0, 73.0)), T((78.0, 72.5)), T((88.5, 78.0)), T((90.0, 93.0)), T((84.0, 112.0)), T((73.0, 118.0)), T((61.0, 112.0)), T((54.0, 94.0))]
        _poly(draw, shell, ARMOR_DARK, OUTLINE, 1.05)
        left_plate = [T((59.0, 81.0)), T((69.5, 75.5)), T((71.0, 94.0)), T((61.0, 103.0)), T((56.5, 91.5))]
        right_plate = [T((75.0, 75.0)), T((86.5, 80.0)), T((88.0, 93.0)), T((78.0, 103.0)), T((73.5, 94.0))]
        abdomen = [T((62.0, 105.0)), T((72.5, 96.0)), T((82.5, 104.0)), T((81.0, 114.0)), T((72.5, 118.0)), T((63.0, 113.0))]
        _poly(draw, left_plate, ARMOR_MID, OUTLINE_SOFT, 0.62)
        _poly(draw, right_plate, ARMOR_LIGHT, OUTLINE_SOFT, 0.62)
        _poly(draw, abdomen, ARMOR_CORE, OUTLINE_SOFT, 0.62)
        _line(draw, [T((72.5, 76.0)), T((72.5, 94.0)), T((72.5, 116.0))], ARMOR_EDGE, 0.88)
        for y in (87.0, 101.0, 113.0):
            _ellipse(draw, T((72.5, y)), 1.15, 1.15, ARMOR_EDGE, OUTLINE_SOFT, 0.25)

    def _paint_collar(self, draw, o: float) -> None:
        def T(point: Point) -> Point:
            return (point[0] - 73.0 + o, point[1] - 112.0 + o)

        _poly(draw, [T((58.0, 78.0)), T((64.0, 69.5)), T((69.5, 75.0)), T((66.0, 84.0))], ARMOR_MID, OUTLINE, 0.75)
        _poly(draw, [T((77.0, 74.0)), T((82.0, 68.8)), T((88.0, 78.0)), T((80.0, 84.0))], ARMOR_LIGHT, OUTLINE, 0.75)
        _line(draw, [T((64.0, 70.5)), T((72.5, 76.0)), T((82.0, 69.8))], ARMOR_EDGE, 0.72)

    # -- head -------------------------------------------------------------

    def _place_head(self, image: Image.Image, center: Point, pose: Pose) -> None:
        """The head turned by its tilt: the unchanging head, then the eyes,
        brows and mouth, each a piece keyed by its (rounded) expression."""
        tilt = pose.head_tilt
        _put(image, _piece(("head",), 40.0, self._paint_head), center, tilt, "head")
        gaze = (round(pose.gaze_x, 1), round(pose.gaze_y, 1))
        _put(image, _piece(("eyes", pose.blink) + gaze, 40.0, lambda d, o: self._paint_eyes(d, o, pose.blink, gaze)), center, tilt, "eyes")
        brow = round(pose.brow_lift, 1)
        _put(image, _piece(("brows", brow), 40.0, lambda d, o: self._paint_brows(d, o, brow)), center, tilt, "brows")
        mouth = (round(pose.mouth_open, 1), round(pose.mouth_round, 1), round(pose.mouth_smile, 2))
        _put(image, _piece(("mouth",) + mouth, 40.0, lambda d, o: self._paint_mouth(d, o, *mouth)), center, tilt, "mouth")

    def _paint_head(self, draw, o: float) -> None:
        cx, cy = o, o

        def R(point: Point) -> Point:
            return point

        # Ear first, behind the long three-quarter face.
        ear = R((cx - 13.7, cy + 0.8))
        _ellipse(draw, ear, 4.5, 6.7, SKIN_SHADE, OUTLINE, 0.9)
        _line(draw, [R((cx - 15.0, cy - 1.0)), R((cx - 12.8, cy + 1.5)), R((cx - 14.5, cy + 4.8))], SKIN_DEEP, 0.5)
        face = [
            R((cx - 9.0, cy - 20.0)), R((cx + 1.0, cy - 22.0)), R((cx + 9.5, cy - 18.0)), R((cx + 13.5, cy - 10.0)),
            R((cx + 15.0, cy - 2.0)), R((cx + 20.0, cy + 2.8)), R((cx + 14.4, cy + 7.0)), R((cx + 11.0, cy + 15.0)),
            R((cx + 3.5, cy + 21.0)), R((cx - 3.2, cy + 18.0)), R((cx - 8.0, cy + 10.5)), R((cx - 10.5, cy + 1.0)),
            R((cx - 10.0, cy - 11.5)),
        ]
        _poly(draw, face, SKIN, OUTLINE, 1.2)
        # High forehead and gaunt cheek planes.
        _poly(draw, [R((cx - 6.0, cy - 16.5)), R((cx + 1.5, cy - 20.0)), R((cx + 5.0, cy - 9.0)), R((cx - 2.5, cy - 6.5))], SKIN_LIGHT, None, 0)
        _poly(draw, [R((cx + 7.5, cy + 3.5)), R((cx + 14.0, cy + 6.0)), R((cx + 10.5, cy + 14.0)), R((cx + 3.0, cy + 17.0))], SKIN_SHADE, None, 0)
        # Swept-back silver hair: high crown, separated wisps, exposed forehead.
        hair_mass = [
            R((cx - 9.5, cy - 15.5)), R((cx - 11.0, cy - 24.0)), R((cx - 5.0, cy - 28.5)), R((cx + 1.5, cy - 31.5)),
            R((cx + 8.0, cy - 30.0)), R((cx + 12.5, cy - 25.0)), R((cx + 8.5, cy - 21.5)), R((cx + 3.0, cy - 24.0)),
            R((cx - 1.5, cy - 18.0)), R((cx - 6.0, cy - 9.0)), R((cx - 11.0, cy - 7.5)),
        ]
        _poly(draw, hair_mass, HAIR, OUTLINE, 1.0)
        # Distinct upward/backward tufts make the silhouette recognizable at 1x.
        _poly(draw, [R((cx - 7.0, cy - 25.0)), R((cx - 8.0, cy - 32.0)), R((cx - 2.0, cy - 28.0))], HAIR_LIGHT, OUTLINE_SOFT, 0.45)
        _poly(draw, [R((cx - 1.5, cy - 29.0)), R((cx + 1.0, cy - 35.0)), R((cx + 5.0, cy - 29.5))], HAIR_LIGHT, OUTLINE_SOFT, 0.45)
        _poly(draw, [R((cx + 4.0, cy - 29.0)), R((cx + 9.0, cy - 34.0)), R((cx + 10.5, cy - 27.0))], HAIR_SHADE, OUTLINE_SOFT, 0.45)
        _line(draw, [R((cx - 4.0, cy - 25.5)), R((cx + 2.5, cy - 31.0)), R((cx + 8.5, cy - 29.0))], HAIR_LIGHT, 0.8)
        _line(draw, [R((cx - 8.0, cy - 15.0)), R((cx - 6.0, cy - 25.0))], HAIR_SHADE, 0.7)
        _line(draw, [R((cx - 6.0, cy - 9.0)), R((cx - 10.0, cy - 19.0))], HAIR, 1.0)
        _line(draw, [R((cx - 2.0, cy - 17.0)), R((cx + 2.0, cy - 23.0)), R((cx + 6.0, cy - 22.0))], OUTLINE_SOFT, 0.6)

        # Rectangular glasses with a slightly oversized near lens: a tinted
        # layer composited over the face, then the frames.
        far_center = R((cx - 2.3, cy - 4.7))
        near_center = R((cx + 7.0, cy - 4.5))
        canvas = draw._img
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        od = blending_draw(overlay)
        _rounded(od, (far_center[0] - 4.6, far_center[1] - 3.8, far_center[0] + 4.6, far_center[1] + 3.8), 1.6, GLASS_TINT, None, 0)
        _rounded(od, (near_center[0] - 5.3, near_center[1] - 4.2, near_center[0] + 5.3, near_center[1] + 4.2), 1.8, GLASS_TINT, None, 0)
        canvas.alpha_composite(overlay)
        draw = blending_draw(canvas)
        _rounded(draw, (far_center[0] - 4.6, far_center[1] - 3.8, far_center[0] + 4.6, far_center[1] + 3.8), 1.6, None, GLASS_FRAME, 0.95)
        _rounded(draw, (near_center[0] - 5.3, near_center[1] - 4.2, near_center[0] + 5.3, near_center[1] + 4.2), 1.8, None, GLASS_FRAME, 1.05)
        _line(draw, [R((cx + 2.3, cy - 4.6)), R((cx + 2.7, cy - 4.6))], GLASS_FRAME, 0.8)
        _line(draw, [R((cx + 12.4, cy - 5.0)), R((cx + 16.0, cy - 6.5))], GLASS_FRAME, 0.65)
        _line(draw, [R((cx - 6.8, cy - 4.8)), R((cx - 11.0, cy - 6.0))], GLASS_FRAME, 0.55)

        # Long nose bridge and projected tip keep the head from reading as a
        # generic round elderly face.
        _line(draw, [R((cx + 2.8, cy - 0.5)), R((cx + 5.3, cy + 5.5))], SKIN_SHADE, 0.8)
        _line(draw, [R((cx + 5.3, cy + 5.5)), R((cx + 12.0, cy + 6.0)), R((cx + 7.2, cy + 8.2))], OUTLINE_SOFT, 0.68)
        _line(draw, [R((cx + 8.0, cy + 7.5)), R((cx + 10.0, cy + 8.6))], SKIN_DEEP, 0.35)
        # Sparse age lines survive the downsample without muddying the face.
        _line(draw, [R((cx - 4.0, cy - 14.0)), R((cx + 2.0, cy - 14.8))], SKIN_SHADE, 0.35)
        _line(draw, [R((cx + 7.0, cy + 7.2)), R((cx + 10.0, cy + 8.5))], SKIN_DEEP, 0.35)
        _line(draw, [R((cx - 5.5, cy + 3.5)), R((cx - 4.5, cy + 9.0))], SKIN_SHADE, 0.35)
        _line(draw, [R((cx + 0.5, cy + 17.1)), R((cx + 6.3, cy + 17.4))], SKIN_DEEP, 0.4)

    def _paint_eyes(self, draw, o: float, blink: bool, gaze: Tuple[float, float]) -> None:
        """Eyes track the imagined plane rather than the viewer."""
        for near, lens in ((False, (o - 2.3, o - 4.7)), (True, (o + 7.0, o - 4.5))):
            if blink:
                _line(draw, [(lens[0] - 2.0, lens[1]), (lens[0] + 2.0, lens[1])], EYE, 0.65)
            else:
                rx = 1.18 if near else 1.0
                _ellipse(draw, lens, rx, 1.15, EYE_WHITE, OUTLINE, 0.3)
                pupil = (lens[0] + gaze[0] * (0.65 if near else 0.5), lens[1] + gaze[1] * 0.55)
                _ellipse(draw, pupil, 0.52 if near else 0.43, 0.56, EYE, EYE, 0.1)

    def _paint_brows(self, draw, o: float, brow_lift: float) -> None:
        cx, cy = o, o
        near_y = -10.5 - brow_lift
        far_y = -10.5 - brow_lift * 0.7
        _line(draw, [(cx - 6.5, cy + far_y + 0.5), (cx - 0.8, cy + far_y)], HAIR_SHADE, 0.65)
        _line(draw, [(cx + 2.0, cy + near_y), (cx + 10.5, cy + near_y - 0.8)], HAIR_SHADE, 0.8)

    def _paint_mouth(self, draw, o: float, mouth_open: float, mouth_round: float, mouth_smile: float) -> None:
        cx, cy = o, o
        mouth_center = (cx + 5.5, cy + 13.0)
        if mouth_open > 0.2:
            mouth_rx = 3.7 + mouth_round * 1.8
            mouth_ry = 0.75 + mouth_open * 2.2
            _ellipse(draw, mouth_center, mouth_rx, mouth_ry, MOUTH, OUTLINE, 0.55)
            if mouth_round < 0.55:
                _line(draw, [(mouth_center[0] - mouth_rx * 0.55, mouth_center[1] - 0.1), (mouth_center[0] + mouth_rx * 0.45, mouth_center[1] - 0.1)], TEETH, 0.55)
        else:
            curve = mouth_smile * 2.2
            _line(draw, [(cx + 1.2, cy + 12.7), (cx + 5.6, cy + 13.2 + curve), (cx + 10.0, cy + 12.5)], MOUTH, 0.75)

    # -- effects ----------------------------------------------------------

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
        draw = blending_draw(image)

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


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    from ...authoring.sheet_build import build_sheet

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    renderer = JeffHinterRenderer()
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_BASENAME,
        rows=ROWS,
        render_fn=renderer.render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.05},
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
    parts = publish_rig_flipbook(TARGET_BASENAME, ROWS, renderer.render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "render"]
