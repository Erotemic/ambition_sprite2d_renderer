"""Bespoke procedural renderer for Patent Clerk.

Patent Clerk is a prestigious secret fighter whose public identity begins and
ends with his job title.  The design is intentionally coy: the sprite never
prints a surname, equation, or explanatory biography.  Recognition comes from
his compact clerk silhouette, severe moustache, quiet administrative gestures,
and especially the enormous unruly salt-and-pepper hair halo.

The hair is not an accessory pasted onto a shared humanoid.  It is a deterministic
field of individually authored locks.  Each lock has its own root angle, length,
width, curl, layer, and tonal bias; the field responds to head rotation, body
acceleration, sustained velocity, and special-move charge.  Primary halo masses
keep the silhouette legible at gameplay scale, while directional locks and fine
flyaways carry pose-specific motion.  The same authored geometry is freshly
rendered for native portraits.

The body, poses, effects, and portraits are all direct Python/Pillow geometry.
There are no image-generation inputs, floor shadows, blur filters, borrowed
character rigs, or permanently held props.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from ambition_sprite2d_renderer.core.draw import blending_draw
from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.sheet_build import build_sheet, write_canonical

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "patent_clerk"
FRAME_W = 176
FRAME_H = 176
AUTHORED_W = 128
AUTHORED_H = 128
CANVAS_OFFSET_X = 24.0
CANVAS_OFFSET_Y = 24.0
SUPER = 5
USES_PROPS = False
USES_DROP_SHADOW = False

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 148),
    ("walk", 8, 106),
    ("run", 8, 76),
    ("crouch", 6, 94),
    ("crouch_walk", 8, 90),
    ("jump", 6, 88),
    ("fall", 6, 92),
    ("land_hard", 7, 80),
    ("dash_startup", 4, 50),
    ("dash", 6, 58),
    ("slide", 6, 68),
    ("roll", 8, 58),
    ("wall_grab", 6, 102),
    ("wall_jump", 6, 80),
    ("ledge_grab", 6, 96),
    ("ledge_climb", 6, 92),
    ("climb", 8, 96),
    ("swim", 8, 102),
    ("block", 6, 80),
    ("known_result", 7, 62),
    ("hit", 5, 82),
    ("death", 9, 102),
    ("talk", 8, 104),
    ("interact", 8, 92),
    ("application_review", 6, 58),
    ("margin_correction", 7, 64),
    ("light_argument", 8, 66),
    ("reference_frame", 9, 72),
    ("elevator_thought", 9, 72),
    ("synchronize_clocks", 10, 78),
    ("mass_energy_conversion", 10, 80),
    ("annus_mirabilis", 12, 82),
    ("celebrate", 8, 88),
    ("taunt", 8, 92),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "special_patent_clerk",
        "display_name": "Patent Clerk",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Compact",
        "mass_class": "Heavy",
        "traits": [
            "special_character",
            "humanoid",
            "patent_clerk",
            "reference_frame_controller",
            "classification_fighter",
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
            "door_access": ["public", "administrative"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public", "administrative"],
        },
    },
    "brain": {"default_preset": "special_examiner"},
    "actions": {"default_preset": "patent_clerk"},
    "visual": {
        "default_pose": "idle",
        "portrait": {
            "face_guide": {
                "center": {"x": 88.0, "y": 58.0},
                "size": {"w": 42.0, "h": 45.0},
                "source_size": {"w": 176.0, "h": 176.0},
            }
        },
    },
    "tags": [
        "special_character",
        "humanoid",
        "patent_clerk",
        "reference_frame_controller",
        "classification_fighter",
        "playable_candidate",
    ],
    "sockets": {
        "head": {
            "source": "explicit.patent_clerk",
            "point": {"x": 88.0, "y": 58.0},
        },
        "chest": {
            "source": "explicit.patent_clerk",
            "point": {"x": 87.0, "y": 92.0},
        },
        "hand_l": {
            "source": "explicit.patent_clerk",
            "point": {"x": 67.0, "y": 104.0},
        },
        "hand_r": {
            "source": "explicit.patent_clerk",
            "point": {"x": 108.0, "y": 103.0},
        },
        "speech_bubble": {
            "source": "explicit.patent_clerk",
            "point": {"x": 88.0, "y": 7.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "margin_correction", "events": []},
        "action.ranged.primary": {"animation": "light_argument", "events": []},
        "action.special.primary": {"animation": "reference_frame", "events": []},
        "action.special.secondary": {"animation": "mass_energy_conversion", "events": []},
        "action.special.up": {"animation": "elevator_thought", "events": []},
        "action.special.down": {"animation": "synchronize_clocks", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.parry": {"animation": "known_result", "events": []},
        "action.super": {"animation": "annus_mirabilis", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "gpt_5_6_thinking_bespoke_2026_08_05",
        "lineage": [
            {
                "revision_id": "patent_clerk_character_direction",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "contribution": "coy_identity_special_character_and_hair_first_design_direction",
            },
            {
                "revision_id": "patent_clerk_procedural_sprite_v1",
                "creator_kind": "model",
                "creator": "GPT-5.6 Thinking",
                "parent_revision_id": "patent_clerk_character_direction",
                "contribution": "bespoke_body_pose_effect_portrait_and_dynamic_hair_authoring",
            },
        ],
    },
    "authoring_description": (
        "Patent Clerk is a coy parody of Albert Einstein, designed around his patent-office period, "
        "iconic unruly hair, moustache, relativity thought experiments, clock synchronization, "
        "reference frames, and mass-energy equivalence. The public character never confirms the "
        "identity: recognition is carried by silhouette, mechanics, and restrained bureaucratic "
        "dialogue. The combat classifications and administrative stamps are deliberate game "
        "inventions rather than biographical claims."
    ),
    "gameplay_description": (
        "A high-mastery heavyweight controller who classifies bodies as MASS, ENERGY, MOVING, or "
        "AT REST; manipulates relative velocity and local reference frames; and turns careful "
        "observation into unusually strong parries and finishers. His recovery uses an accelerating "
        "elevator frame, his stage control uses synchronized clocks, and his super resolves several "
        "quiet office observations into one inevitable conversion."
    ),
    "dialogue_hints": {
        "barks": [
            "Your application has several interesting assumptions.",
            "Please remain in your chosen frame.",
            "The distinction is useful—for now.",
            "Your timing was local.",
            "Approved.",
            "No, I am only a clerk.",
        ],
        "fallback_lines": [
            "A clock is reliable until you ask where it has been.",
            "Common sense is often a local regulation.",
            "You may call yourself stationary. Courtesy permits it.",
            "The office prefers inventions. I find assumptions more interesting.",
            "There are many patent clerks.",
            "Not required in this field.",
        ],
    },
}

# Restrained office clothing lets the hair own the silhouette.
OUTLINE = (22, 22, 24, 255)
OUTLINE_SOFT = (48, 46, 48, 255)
SKIN = (193, 145, 109, 255)
SKIN_LIGHT = (229, 184, 145, 255)
SKIN_SHADE = (143, 99, 79, 255)
SKIN_RED = (179, 103, 86, 255)
EYE = (38, 31, 27, 255)
BROW = (70, 61, 56, 255)
MOUSTACHE = (67, 61, 59, 255)
HAIR_DARK = (67, 65, 66, 255)
HAIR_MID = (113, 111, 109, 255)
HAIR_LIGHT = (174, 172, 166, 255)
HAIR_WHITE = (226, 224, 214, 255)
HAIR_GLEAM = (248, 244, 226, 255)
SHIRT = (223, 216, 198, 255)
SHIRT_LIGHT = (244, 239, 221, 255)
SHIRT_SHADE = (174, 166, 151, 255)
VEST = (65, 70, 72, 255)
VEST_LIGHT = (90, 96, 96, 255)
VEST_DARK = (42, 45, 49, 255)
TIE = (112, 50, 48, 255)
TIE_LIGHT = (156, 69, 62, 255)
TROUSER = (68, 67, 70, 255)
TROUSER_LIGHT = (94, 92, 95, 255)
TROUSER_DARK = (42, 42, 46, 255)
SHOE = (48, 37, 32, 255)
SHOE_LIGHT = (84, 65, 54, 255)
PAPER = (237, 230, 205, 255)
PAPER_SHADE = (181, 174, 155, 255)
INK = (42, 48, 58, 255)
STAMP = (157, 43, 47, 255)
STAMP_LIGHT = (218, 82, 78, 255)
FRAME_BLUE = (79, 166, 204, 255)
FRAME_LIGHT = (165, 225, 245, 255)
CLOCK_GOLD = (218, 178, 74, 255)
CLOCK_LIGHT = (255, 231, 151, 255)
MASS_COLOR = (116, 126, 151, 255)
ENERGY_COLOR = (244, 167, 63, 255)
ENERGY_LIGHT = (255, 231, 145, 255)
CONVERSION = (240, 236, 207, 255)


def _s(value: float) -> int:
    return max(1, int(round(value * SUPER)))


def _pt(point: Point) -> Tuple[int, int]:
    return (
        int(round((point[0] + CANVAS_OFFSET_X) * SUPER)),
        int(round((point[1] + CANVAS_OFFSET_Y) * SUPER)),
    )


def _rect(left: float, top: float, right: float, bottom: float) -> Tuple[int, int, int, int]:
    x1, y1 = _pt((left, top))
    x2, y2 = _pt((right, bottom))
    return (x1, y1, x2, y2)


def _bbox(center: Point, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return _rect(center[0] - rx, center[1] - ry, center[0] + rx, center[1] + ry)


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
    return along, (-along[1], along[0]), length


def _segment_quad(a: Point, b: Point, ra: float, rb: float) -> List[Point]:
    _along, normal, _length = _unit(a, b)
    return [
        (a[0] + normal[0] * ra, a[1] + normal[1] * ra),
        (b[0] + normal[0] * rb, b[1] + normal[1] * rb),
        (b[0] - normal[0] * rb, b[1] - normal[1] * rb),
        (a[0] - normal[0] * ra, a[1] - normal[1] * ra),
    ]


def _jointed_strip(a: Point, b: Point, c: Point, wa: float, wb: float, wc: float) -> List[Point]:
    _ab, nab, _ = _unit(a, b)
    _bc, nbc, _ = _unit(b, c)
    nx = nab[0] + nbc[0]
    ny = nab[1] + nbc[1]
    nlen = max(1.0e-6, math.hypot(nx, ny))
    mid_n = (nx / nlen, ny / nlen)
    return [
        (a[0] + nab[0] * wa, a[1] + nab[1] * wa),
        (b[0] + mid_n[0] * wb, b[1] + mid_n[1] * wb),
        (c[0] + nbc[0] * wc, c[1] + nbc[1] * wc),
        (c[0] - nbc[0] * wc, c[1] - nbc[1] * wc),
        (b[0] - mid_n[0] * wb, b[1] - mid_n[1] * wb),
        (a[0] - nab[0] * wa, a[1] - nab[1] * wa),
    ]


def _polygon(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.0) -> None:
    pts = [_pt(point) for point in points]
    draw.polygon(pts, fill=fill)
    if outline is not None:
        draw.line(pts + [pts[0]], fill=outline, width=_s(width), joint="curve")


def _line(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, width: float) -> None:
    draw.line([_pt(point) for point in points], fill=fill, width=_s(width), joint="curve")


def _ellipse(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, fill: RGBA, outline: RGBA | None = OUTLINE, width: float = 1.0) -> None:
    draw.ellipse(_bbox(center, rx, ry), fill=fill, outline=outline, width=_s(width) if outline else 1)


def _arc(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, start: float, end: float, fill: RGBA, width: float) -> None:
    draw.arc(_bbox(center, rx, ry), start=start, end=end, fill=fill, width=_s(width))


def _fade(color: RGBA, amount: float) -> RGBA:
    return (color[0], color[1], color[2], int(round(color[3] * _clamp01(amount))))


def _mix(a: RGBA, b: RGBA, amount: float) -> RGBA:
    amount = _clamp01(amount)
    return tuple(int(round(_lerp(a[i], b[i], amount))) for i in range(4))  # type: ignore[return-value]


def _font(size: float, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf") if bold else ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
    for name in names:
        try:
            return ImageFont.truetype(name, _s(size))
        except OSError:
            continue
    return ImageFont.load_default()


def _bezier(a: Point, b: Point, c: Point, d: Point, t: float) -> Point:
    u = 1.0 - t
    return (
        u * u * u * a[0] + 3.0 * u * u * t * b[0] + 3.0 * u * t * t * c[0] + t * t * t * d[0],
        u * u * u * a[1] + 3.0 * u * u * t * b[1] + 3.0 * u * t * t * c[1] + t * t * t * d[1],
    )


def _catmull_open(points: Sequence[Point], steps: int = 5) -> List[Point]:
    """Sample a smooth open curve through authored silhouette points."""
    if len(points) < 2:
        return list(points)
    padded = [points[0], *points, points[-1]]
    out: List[Point] = []
    for i in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[i - 1 : i + 3]
        for step in range(steps):
            t = step / float(steps)
            t2 = t * t
            t3 = t2 * t
            out.append(
                (
                    0.5
                    * (
                        2.0 * p1[0]
                        + (-p0[0] + p2[0]) * t
                        + (2.0 * p0[0] - 5.0 * p1[0] + 4.0 * p2[0] - p3[0]) * t2
                        + (-p0[0] + 3.0 * p1[0] - 3.0 * p2[0] + p3[0]) * t3
                    ),
                    0.5
                    * (
                        2.0 * p1[1]
                        + (-p0[1] + p2[1]) * t
                        + (2.0 * p0[1] - 5.0 * p1[1] + 4.0 * p2[1] - p3[1]) * t2
                        + (-p0[1] + 3.0 * p1[1] - 3.0 * p2[1] + p3[1]) * t3
                    ),
                )
            )
    out.append(points[-1])
    return out


@dataclass(frozen=True)
class HairLock:
    angle: float
    length: float
    width: float
    curl: float
    sweep: float
    layer: str
    tone: float
    phase: float


# Deliberately irregular.  The right crown is taller and more open; the left
# temple is denser and curls back toward the ear.  Mirroring this table would
# destroy the recognition silhouette.
HAIR_LOCKS: Tuple[HairLock, ...] = (
    # These are tangled waves inside the connected halo, not radial spikes.
    # Large curl magnitudes turn outward growth sideways before it reaches the
    # silhouette, producing the characteristic tousled cloud.
    HairLock(174, 6.6, 3.8, -0.92, -0.10, "back", 0.18, 0.2),
    HairLock(192, 7.4, 4.2, 0.86, -0.06, "back", 0.54, 1.4),
    HairLock(212, 8.0, 4.0, -1.02, 0.00, "back", 0.78, 2.8),
    HairLock(233, 8.8, 4.4, 0.94, 0.05, "back", 0.34, 0.7),
    HairLock(253, 9.4, 4.2, -0.82, 0.08, "back", 0.86, 2.2),
    HairLock(273, 9.8, 4.5, 0.88, 0.10, "back", 0.60, 3.1),
    HairLock(294, 10.2, 4.3, -0.96, 0.12, "back", 0.90, 1.0),
    HairLock(315, 9.2, 4.4, 1.00, 0.08, "back", 0.46, 2.5),
    HairLock(336, 8.2, 4.1, -0.88, 0.02, "back", 0.76, 1.2),
    HairLock(356, 7.2, 3.9, 0.92, -0.04, "back", 0.38, 2.9),
    HairLock(15, 6.2, 3.7, -0.84, -0.09, "back", 0.70, 0.5),
    HairLock(188, 5.2, 3.5, 0.90, -0.06, "front", 0.64, 2.1),
    HairLock(225, 6.0, 3.7, -0.98, 0.02, "front", 0.28, 0.6),
    HairLock(263, 6.8, 3.8, 0.84, 0.08, "front", 0.82, 2.7),
    HairLock(302, 7.0, 3.8, -0.92, 0.09, "front", 0.50, 1.3),
    HairLock(340, 6.2, 3.6, 0.96, 0.02, "front", 0.74, 3.0),
    HairLock(4, 5.0, 3.4, -0.86, -0.06, "front", 0.40, 0.9),
)


@dataclass
class Pose:
    root_x: float = 0.0
    root_y: float = 0.0
    rotation: float = 0.0
    rotation_pivot: Point = (64.0, 88.0)
    body_lean: float = -1.5
    head_x: float = 0.0
    head_y: float = 0.0
    head_tilt: float = 0.0
    blink: bool = False
    eye_wide: float = 0.0
    mouth_open: float = 0.0
    smile: float = 0.0
    brow: float = 0.1
    skeptical: float = 0.0
    left_foot: Point = (54.0, 113.0)
    left_knee: Point = (55.0, 94.0)
    left_hip: Point = (58.0, 78.0)
    right_foot: Point = (74.0, 113.0)
    right_knee: Point = (72.0, 94.0)
    right_hip: Point = (68.0, 78.0)
    left_shoulder: Point = (51.0, 58.0)
    left_elbow: Point = (45.0, 74.0)
    left_hand: Point = (44.0, 87.0)
    right_shoulder: Point = (76.0, 58.0)
    right_elbow: Point = (82.0, 73.0)
    right_hand: Point = (82.0, 86.0)
    left_hand_mode: str = "relaxed"
    right_hand_mode: str = "relaxed"
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    acceleration_x: float = 0.0
    acceleration_y: float = 0.0
    hair_charge: float = 0.0
    hair_phase: float = 0.0
    effect: str = ""
    effect_phase: float = 0.0
    label: str = ""


def _phase(frame_idx: int, nframes: int) -> float:
    return frame_idx / max(1, nframes)


def _base_pose() -> Pose:
    return Pose()


def _walking_pose(t: float, *, running: bool = False, crouched: bool = False) -> Pose:
    p = _base_pose()
    stride = math.sin(t * math.tau)
    lift_l = max(0.0, math.sin(t * math.tau + math.pi * 0.5))
    lift_r = max(0.0, math.sin(t * math.tau + math.pi * 1.5))
    span = 10.5 if running else 7.0
    if crouched:
        span = 5.5
        p.root_y = 9.0
        p.body_lean = 7.0
        p.head_y = 1.5
    p.left_foot = (54.0 - stride * span, 113.0 - lift_l * (7.0 if running else 4.0))
    p.right_foot = (74.0 + stride * span, 113.0 - lift_r * (7.0 if running else 4.0))
    p.left_knee = (56.0 - stride * span * 0.42, 94.0 - lift_l * 3.0 + (5.0 if crouched else 0.0))
    p.right_knee = (71.0 + stride * span * 0.42, 94.0 - lift_r * 3.0 + (5.0 if crouched else 0.0))
    p.left_hand = (44.0 + stride * (9.0 if running else 6.0), 84.0 + (3.0 if crouched else 0.0))
    p.left_elbow = (46.0 + stride * 5.0, 71.0 + (3.0 if crouched else 0.0))
    p.right_hand = (83.0 - stride * (9.0 if running else 6.0), 84.0 + (3.0 if crouched else 0.0))
    p.right_elbow = (81.0 - stride * 5.0, 71.0 + (3.0 if crouched else 0.0))
    p.root_y += abs(math.sin(t * math.tau)) * (1.8 if running else 0.8)
    p.body_lean += 8.0 if running else 1.5
    p.velocity_x = 6.0 if running else 3.0
    p.acceleration_x = math.cos(t * math.tau) * (5.0 if running else 2.0)
    p.hair_phase = t
    return p


def _pose(animation: str, frame_idx: int, nframes: int) -> Pose:
    t = _phase(frame_idx, nframes)
    cycle = t * math.tau
    p = _base_pose()
    p.hair_phase = t

    if animation == "idle":
        breath = math.sin(cycle)
        p.root_y = breath * 0.65
        p.head_y = -breath * 0.22
        p.head_tilt = math.sin(cycle * 0.5) * 1.4
        p.blink = frame_idx in (5,)
        p.left_hand = (44.0, 86.0 + breath * 0.3)
        p.right_hand = (82.0, 85.0 - breath * 0.2)
        p.hair_charge = 0.04 + 0.02 * (breath + 1.0)
        return p

    if animation == "walk":
        return _walking_pose(t)

    if animation == "run":
        return _walking_pose(t, running=True)

    if animation == "crouch":
        q = _smooth(min(1.0, t * 2.0))
        p.root_y = 9.0 * q
        p.body_lean = 8.0 * q
        p.head_y = 2.0 * q
        p.left_knee = (56.0, 100.0)
        p.right_knee = (71.0, 100.0)
        p.left_foot = (51.0, 113.0)
        p.right_foot = (77.0, 113.0)
        p.left_hand = (46.0, 91.0)
        p.right_hand = (81.0, 90.0)
        p.velocity_y = 2.0
        return p

    if animation == "crouch_walk":
        return _walking_pose(t, crouched=True)

    if animation == "jump":
        q = _smooth(t)
        p.root_y = -10.0 - 6.0 * _pulse(t)
        p.velocity_y = -7.0 + 14.0 * q
        p.acceleration_y = 5.0
        p.left_knee = (57.0, 90.0)
        p.left_foot = (48.0, 101.0)
        p.right_knee = (71.0, 89.0)
        p.right_foot = (79.0, 99.0)
        p.left_hand = (42.0, 70.0)
        p.left_elbow = (45.0, 62.0)
        p.right_hand = (87.0, 69.0)
        p.right_elbow = (81.0, 61.0)
        p.hair_charge = 0.12
        return p

    if animation == "fall":
        p.root_y = -7.0 + t * 5.0
        p.velocity_y = 7.0
        p.acceleration_y = 2.0
        p.left_foot = (49.0, 108.0)
        p.left_knee = (57.0, 92.0)
        p.right_foot = (79.0, 106.0)
        p.right_knee = (70.0, 91.0)
        p.left_hand = (40.0, 73.0)
        p.right_hand = (88.0, 72.0)
        p.body_lean = -5.0
        p.eye_wide = 0.15
        return p

    if animation == "land_hard":
        impact = _pulse(min(1.0, t * 1.8))
        recover = _smooth(max(0.0, (t - 0.35) / 0.65))
        p.root_y = 9.0 * impact - 4.0 * recover
        p.body_lean = 18.0 * impact - 5.0 * recover
        p.left_knee = (53.0, 100.0)
        p.right_knee = (73.0, 100.0)
        p.left_foot = (46.0, 114.0)
        p.right_foot = (81.0, 114.0)
        p.left_hand = (40.0, 94.0)
        p.right_hand = (86.0, 93.0)
        p.acceleration_y = 12.0 * impact
        p.hair_charge = 0.18 * impact
        return p

    if animation == "dash_startup":
        q = _smooth(t)
        p.body_lean = 21.0 * q
        p.root_x = 4.0 * q
        p.left_foot = (49.0, 113.0)
        p.right_foot = (76.0, 113.0)
        p.left_knee = (56.0, 99.0)
        p.right_knee = (71.0, 92.0)
        p.left_hand = (41.0, 79.0)
        p.right_hand = (78.0, 90.0)
        p.acceleration_x = 13.0 * q
        return p

    if animation == "dash":
        p = _walking_pose(t, running=True)
        p.body_lean = 24.0
        p.root_x = 7.0
        p.velocity_x = 12.0
        p.acceleration_x = math.cos(cycle) * 6.0
        p.left_hand = (42.0, 74.0)
        p.right_hand = (79.0, 91.0)
        return p

    if animation == "slide":
        q = _smooth(t)
        p.root_x = 9.0 * q
        p.root_y = 14.0
        p.body_lean = 35.0
        p.left_hip = (56.0, 83.0)
        p.right_hip = (67.0, 83.0)
        p.left_knee = (72.0, 100.0)
        p.left_foot = (89.0, 111.0)
        p.right_knee = (56.0, 105.0)
        p.right_foot = (42.0, 113.0)
        p.left_hand = (47.0, 96.0)
        p.right_hand = (84.0, 93.0)
        p.velocity_x = 11.0
        return p

    if animation == "roll":
        p.rotation = t * 360.0
        p.rotation_pivot = (64.0, 87.0)
        p.root_y = -10.0
        p.left_foot = (58.0, 96.0)
        p.right_foot = (70.0, 96.0)
        p.left_knee = (58.0, 86.0)
        p.right_knee = (70.0, 86.0)
        p.left_hand = (55.0, 81.0)
        p.right_hand = (72.0, 81.0)
        p.velocity_x = 8.0
        p.hair_charge = 0.22
        return p

    if animation == "wall_grab":
        p.rotation = -8.0
        p.root_x = 13.0
        p.root_y = -2.0
        p.left_hand = (89.0, 52.0)
        p.left_elbow = (78.0, 61.0)
        p.right_hand = (91.0, 69.0)
        p.right_elbow = (80.0, 71.0)
        p.left_foot = (87.0, 101.0)
        p.left_knee = (75.0, 92.0)
        p.right_foot = (89.0, 113.0)
        p.right_knee = (75.0, 99.0)
        p.velocity_y = math.sin(cycle) * 1.5
        return p

    if animation == "wall_jump":
        q = _smooth(t)
        p.root_x = 11.0 - 20.0 * q
        p.root_y = -3.0 - 12.0 * _pulse(t)
        p.body_lean = -18.0
        p.left_hand = (83.0, 59.0)
        p.right_hand = (43.0, 66.0)
        p.left_foot = (77.0, 105.0)
        p.right_foot = (47.0, 101.0)
        p.velocity_x = -10.0
        p.velocity_y = -8.0 + 12.0 * q
        p.acceleration_x = -11.0
        return p

    if animation == "ledge_grab":
        p.root_y = 11.0
        p.left_hand = (46.0, 50.0)
        p.right_hand = (78.0, 50.0)
        p.left_elbow = (49.0, 64.0)
        p.right_elbow = (75.0, 64.0)
        p.left_foot = (54.0, 116.0)
        p.right_foot = (72.0, 116.0)
        p.hair_charge = 0.05
        return p

    if animation == "ledge_climb":
        q = _smooth(t)
        p.root_y = _lerp(12.0, 0.0, q)
        p.root_x = _lerp(-5.0, 5.0, q)
        p.body_lean = _lerp(18.0, -1.5, q)
        p.left_hand = _lerp_point((45.0, 51.0), (44.0, 85.0), q)
        p.right_hand = _lerp_point((78.0, 51.0), (82.0, 85.0), q)
        p.left_foot = _lerp_point((50.0, 118.0), (54.0, 113.0), q)
        p.right_foot = _lerp_point((73.0, 118.0), (74.0, 113.0), q)
        return p

    if animation == "climb":
        reach = math.sin(cycle)
        p.root_y = -2.0
        p.left_hand = (48.0, 54.0 - reach * 9.0)
        p.left_elbow = (50.0, 66.0 - reach * 5.0)
        p.right_hand = (78.0, 54.0 + reach * 9.0)
        p.right_elbow = (76.0, 66.0 + reach * 5.0)
        p.left_foot = (54.0, 108.0 + reach * 7.0)
        p.right_foot = (74.0, 108.0 - reach * 7.0)
        p.velocity_y = -2.0
        return p

    if animation == "swim":
        p.rotation = math.sin(cycle) * 5.0
        p.root_y = -3.0 + math.sin(cycle) * 2.0
        p.left_hand = (37.0 + math.cos(cycle) * 8.0, 72.0)
        p.right_hand = (91.0 - math.cos(cycle) * 8.0, 71.0)
        p.left_foot = (48.0, 110.0 + math.sin(cycle) * 5.0)
        p.right_foot = (80.0, 110.0 - math.sin(cycle) * 5.0)
        p.velocity_x = 3.5
        return p

    if animation == "block":
        q = _pulse(t)
        p.body_lean = -4.0
        p.left_hand = (56.0, 60.0)
        p.left_elbow = (48.0, 69.0)
        p.right_hand = (71.0, 58.0)
        p.right_elbow = (79.0, 69.0)
        p.left_hand_mode = "open"
        p.right_hand_mode = "open"
        p.effect = "block"
        p.effect_phase = q
        p.hair_charge = 0.15 * q
        return p

    if animation == "known_result":
        q = _pulse(t)
        p.body_lean = -7.0 * q
        p.root_x = -2.0 * q
        p.left_hand = (50.0, 71.0)
        p.right_hand = (75.0 + 7.0 * q, 64.0)
        p.right_elbow = (78.0, 74.0)
        p.right_hand_mode = "precise"
        p.skeptical = 0.8
        p.effect = "known_result"
        p.effect_phase = q
        p.hair_charge = 0.36 * q
        p.acceleration_x = -7.0 * q
        return p

    if animation == "hit":
        q = _pulse(t)
        p.root_x = -7.0 * q
        p.body_lean = -22.0 * q
        p.head_tilt = -13.0 * q
        p.left_hand = (37.0, 75.0)
        p.right_hand = (78.0, 91.0)
        p.eye_wide = 0.8
        p.mouth_open = 0.5
        p.velocity_x = -8.0 * q
        p.acceleration_x = -10.0 * q
        return p

    if animation == "death":
        q = _smooth(t)
        p.rotation = -78.0 * q
        p.rotation_pivot = (64.0, 106.0)
        p.root_x = 18.0 * q
        p.root_y = 11.0 * q
        p.left_hand = (37.0, 75.0)
        p.right_hand = (87.0, 73.0)
        p.left_foot = (49.0, 111.0)
        p.right_foot = (79.0, 111.0)
        p.blink = q > 0.65
        p.mouth_open = 0.15
        p.velocity_x = -5.0 * (1.0 - q)
        return p

    if animation == "talk":
        gesture = math.sin(cycle)
        p.mouth_open = 0.35 + 0.28 * max(0.0, math.sin(cycle * 2.0))
        p.brow = 0.25
        p.right_hand = (82.0 + gesture * 3.0, 70.0 - abs(gesture) * 4.0)
        p.right_elbow = (80.0, 76.0)
        p.right_hand_mode = "explaining"
        p.left_hand = (46.0, 86.0)
        p.head_tilt = -gesture * 2.0
        return p

    if animation == "interact":
        q = _pulse(t)
        p.body_lean = 6.0 * q
        p.right_hand = (91.0, 72.0 - q * 4.0)
        p.right_elbow = (80.0, 73.0)
        p.right_hand_mode = "precise"
        p.effect = "small_stamp"
        p.effect_phase = q
        p.label = "FILED"
        p.hair_charge = 0.08 * q
        return p

    if animation == "application_review":
        q = _smooth(t)
        strike = _pulse(min(1.0, t * 1.45))
        p.body_lean = 5.0 * strike
        p.right_elbow = (75.0 + 8.0 * strike, 69.0)
        p.right_hand = (82.0 + 18.0 * strike, 72.0)
        p.right_hand_mode = "stamp"
        p.left_hand = (49.0, 73.0)
        p.left_hand_mode = "page"
        p.effect = "application_review"
        p.effect_phase = strike
        p.label = ("MASS", "ENERGY", "MOVING", "AT REST")[frame_idx % 4]
        p.acceleration_x = 8.0 * strike
        p.hair_charge = 0.16 * strike
        p.skeptical = 0.4 * q
        return p

    if animation == "margin_correction":
        strike = _pulse(min(1.0, t * 1.35))
        p.body_lean = 15.0 * strike
        p.root_x = 4.0 * strike
        p.right_shoulder = (77.0, 57.0)
        p.right_elbow = (84.0 + 9.0 * strike, 66.0)
        p.right_hand = (88.0 + 20.0 * strike, 67.0 - 3.0 * strike)
        p.right_hand_mode = "precise"
        p.left_hand = (43.0, 83.0)
        p.effect = "margin_correction"
        p.effect_phase = strike
        p.velocity_x = 4.0 * strike
        p.acceleration_x = 10.0 * strike
        p.hair_charge = 0.22 * strike
        return p

    if animation == "light_argument":
        charge = _smooth(min(1.0, t * 2.0))
        release = _smooth(max(0.0, (t - 0.35) / 0.35)) * (1.0 - _smooth(max(0.0, (t - 0.82) / 0.18)))
        p.body_lean = -6.0 + release * 11.0
        p.left_hand = (47.0, 78.0)
        p.right_elbow = (81.0, 66.0)
        p.right_hand = (91.0, 59.0)
        p.right_hand_mode = "precise"
        p.eye_wide = 0.2
        p.effect = "light_argument"
        p.effect_phase = max(charge * 0.35, release)
        p.hair_charge = 0.25 * charge + 0.38 * release
        p.acceleration_x = 6.0 * release
        return p

    if animation == "reference_frame":
        q = _pulse(t)
        p.left_hand = (42.0, 69.0)
        p.right_hand = (87.0, 69.0)
        p.left_hand_mode = "open"
        p.right_hand_mode = "open"
        p.body_lean = math.sin(cycle) * 2.0
        p.effect = "reference_frame"
        p.effect_phase = q
        p.velocity_x = 5.0 * math.sin(cycle)
        p.acceleration_x = 8.0 * math.cos(cycle)
        p.hair_charge = 0.30 * q
        return p

    if animation == "elevator_thought":
        rise = _smooth(t)
        p.root_y = -17.0 * rise
        p.velocity_y = -10.0 * _pulse(t)
        p.acceleration_y = -12.0 * _pulse(t)
        p.left_hand = (48.0, 72.0)
        p.right_hand = (78.0, 72.0)
        p.left_hand_mode = "open"
        p.right_hand_mode = "open"
        p.effect = "elevator"
        p.effect_phase = _pulse(t)
        p.eye_wide = 0.12
        p.hair_charge = 0.50 * _pulse(t)
        return p

    if animation == "synchronize_clocks":
        q = _pulse(t)
        p.left_hand = (42.0, 66.0)
        p.right_hand = (86.0, 66.0)
        p.left_hand_mode = "precise"
        p.right_hand_mode = "precise"
        p.effect = "clocks"
        p.effect_phase = q
        p.skeptical = 0.7
        p.head_tilt = math.sin(cycle) * 2.0
        p.hair_charge = 0.28 * q
        return p

    if animation == "mass_energy_conversion":
        gather = _smooth(min(1.0, t * 1.8))
        collapse = _smooth(max(0.0, (t - 0.45) / 0.32))
        release = _smooth(max(0.0, (t - 0.68) / 0.20))
        q = max(gather * (1.0 - collapse), release)
        p.left_hand = (_lerp(40.0, 57.0, collapse), 68.0)
        p.right_hand = (_lerp(88.0, 70.0, collapse), 68.0)
        p.left_hand_mode = "open"
        p.right_hand_mode = "open"
        p.body_lean = -8.0 * gather + 16.0 * release
        p.root_x = -3.0 * gather + 6.0 * release
        p.effect = "conversion"
        p.effect_phase = t
        p.hair_charge = _clamp01(0.30 + 0.70 * q)
        p.acceleration_x = 14.0 * release
        p.eye_wide = 0.25 * gather
        return p

    if animation == "annus_mirabilis":
        q = _smooth(t)
        climax = _pulse(_clamp01((t - 0.28) / 0.72))
        p.root_y = -2.0 * q
        p.left_hand = (48.0, 74.0)
        p.right_hand = (79.0, 69.0)
        p.right_hand_mode = "precise"
        p.left_hand_mode = "page"
        p.body_lean = -4.0
        p.effect = "annus_mirabilis"
        p.effect_phase = t
        p.hair_charge = _clamp01(0.25 + 0.80 * climax)
        p.eye_wide = 0.18
        p.brow = 0.35
        return p

    if animation == "celebrate":
        q = _pulse(t)
        p.root_y = -4.0 * q
        p.left_hand = (43.0, 52.0 - q * 4.0)
        p.right_hand = (84.0, 52.0 - q * 4.0)
        p.left_elbow = (48.0, 64.0)
        p.right_elbow = (79.0, 64.0)
        p.left_hand_mode = "open"
        p.right_hand_mode = "open"
        p.smile = 0.8
        p.hair_charge = 0.24 * q
        return p

    if animation == "taunt":
        q = _pulse(t)
        p.right_hand = (83.0, 65.0 - q * 3.0)
        p.right_elbow = (80.0, 75.0)
        p.right_hand_mode = "precise"
        p.left_hand = (47.0, 86.0)
        p.skeptical = 1.0
        p.head_tilt = -4.0 * q
        p.effect = "small_stamp"
        p.effect_phase = q
        p.label = "ORDINARY"
        return p

    raise KeyError(f"unknown Patent Clerk animation: {animation}")


def _transform(point: Point, pose: Pose) -> Point:
    shifted = (point[0] + pose.root_x, point[1] + pose.root_y)
    if pose.rotation:
        pivot = (pose.rotation_pivot[0] + pose.root_x, pose.rotation_pivot[1] + pose.root_y)
        shifted = _rotate(shifted, pivot, pose.rotation)
    return shifted


def _body_point(point: Point, pose: Pose) -> Point:
    pivot = (64.0, 79.0)
    leaned = _rotate(point, pivot, pose.body_lean)
    return _transform(leaned, pose)


def _head_center(pose: Pose) -> Point:
    center = (64.0 + pose.head_x, 35.0 + pose.head_y)
    center = _rotate(center, (64.0, 55.0), pose.body_lean * 0.35)
    return _transform(center, pose)


def _hair_color(lock: HairLock, pose: Pose, *, highlight: bool = False) -> RGBA:
    if lock.tone < 0.28:
        base = HAIR_DARK
    elif lock.tone < 0.58:
        base = HAIR_MID
    else:
        base = HAIR_LIGHT
    charge = _clamp01(pose.hair_charge)
    target = HAIR_GLEAM if highlight else HAIR_WHITE
    return _mix(base, target, charge * (0.58 + lock.tone * 0.32))


def _lock_curve(lock: HairLock, pose: Pose) -> Tuple[List[Point], List[float]]:
    center = _head_center(pose)
    theta = math.radians(lock.angle + pose.head_tilt)
    outward = (math.cos(theta), math.sin(theta))
    tangent = (-outward[1], outward[0])
    head_rx = 14.2
    head_ry = 16.8
    root = (center[0] + outward[0] * head_rx, center[1] + outward[1] * head_ry)

    wind_x = -pose.velocity_x * 0.42 - pose.acceleration_x * 0.16
    wind_y = -pose.velocity_y * 0.18 - pose.acceleration_y * 0.09
    bloom = pose.hair_charge * (4.2 + lock.tone * 2.0)
    pulse = math.sin(pose.hair_phase * math.tau + lock.phase) * (0.55 + pose.hair_charge * 0.8)
    length = lock.length + bloom + pulse
    curl = lock.curl * length
    tip = (
        root[0] + outward[0] * length * 0.52 + tangent[0] * curl * 0.62 + wind_x * (0.36 + lock.sweep),
        root[1] + outward[1] * length * 0.52 + tangent[1] * curl * 0.62 + wind_y * (0.36 + lock.sweep),
    )
    c1 = (
        root[0] + outward[0] * length * 0.28 - tangent[0] * curl * 0.18 + wind_x * 0.08,
        root[1] + outward[1] * length * 0.28 - tangent[1] * curl * 0.18 + wind_y * 0.08,
    )
    c2 = (
        root[0] + outward[0] * length * 0.48 + tangent[0] * curl * 0.88 + wind_x * 0.24,
        root[1] + outward[1] * length * 0.48 + tangent[1] * curl * 0.88 + wind_y * 0.24,
    )
    points = [_bezier(root, c1, c2, tip, i / 7.0) for i in range(8)]
    widths = [max(1.0, lock.width * (1.0 - (i / 7.0) ** 1.70)) for i in range(8)]
    return points, widths


def _draw_hair_mass(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    center = _head_center(pose)
    charge = pose.hair_charge
    wind_x = -pose.velocity_x * 0.42 - pose.acceleration_x * 0.15
    wind_y = -pose.velocity_y * 0.18 - pose.acceleration_y * 0.08

    # Authored in Cartesian space rather than as a radial fan.  The alternating
    # bulges and notches make a messy cloud with a higher, looser right crown.
    local_profile = (
        (-17.5, 10.0, 0.45, 0.25),
        (-23.5, 7.0, 0.70, 0.42),
        (-27.0, 1.0, 0.82, 0.55),
        (-24.0, -4.0, 0.74, 0.64),
        (-29.0, -9.0, 0.90, 0.72),
        (-23.0, -13.0, 0.78, 0.80),
        (-25.0, -19.0, 0.96, 0.86),
        (-18.0, -20.5, 0.84, 0.92),
        (-16.0, -27.0, 1.00, 0.98),
        (-9.0, -24.0, 0.88, 1.02),
        (-5.0, -31.0, 1.06, 1.08),
        (1.0, -26.0, 0.92, 1.04),
        (6.0, -33.0, 1.10, 1.12),
        (11.0, -26.0, 0.94, 1.02),
        (18.0, -29.0, 1.12, 1.08),
        (19.5, -21.0, 0.92, 0.92),
        (27.0, -21.0, 1.06, 0.88),
        (24.0, -14.0, 0.88, 0.80),
        (30.0, -9.0, 1.00, 0.72),
        (25.0, -3.0, 0.82, 0.60),
        (28.0, 3.0, 0.90, 0.50),
        (22.0, 7.5, 0.72, 0.38),
        (17.0, 11.0, 0.48, 0.26),
        (10.0, 12.5, 0.34, 0.18),
        (3.0, 11.0, 0.28, 0.12),
        (-5.0, 13.0, 0.30, 0.12),
        (-11.0, 10.5, 0.36, 0.18),
    )
    outer: List[Point] = []
    for index, (lx, ly, charge_gain, wind_gain) in enumerate(local_profile):
        length = max(1.0, math.hypot(lx, ly))
        nx, ny = lx / length, ly / length
        pulse = math.sin(pose.hair_phase * math.tau + index * 1.11) * (0.28 + charge * 0.52)
        expanded = (
            lx + nx * (charge * 4.2 * charge_gain + pulse),
            ly + ny * (charge * 4.8 * charge_gain + pulse),
        )
        point = (
            center[0] + expanded[0] + wind_x * wind_gain,
            center[1] + expanded[1] + wind_y * wind_gain,
        )
        outer.append(_rotate(point, center, pose.head_tilt * 0.40))
    halo = _catmull_open([*outer, outer[0]], steps=4)
    _polygon(draw, halo, _mix(HAIR_MID, HAIR_LIGHT, charge * 0.34), OUTLINE, 0.95)

    # Tonal cloud masses overlap without internal black borders.  Their shapes
    # are intentionally broad and soft; the fine lock field supplies motion.
    islands = (
        ((-17.0, -10.0), 10.5, 12.0, HAIR_DARK, 0.70),
        ((-7.0, -20.0), 12.0, 12.5, HAIR_LIGHT, 0.72),
        ((5.0, -23.0), 12.5, 13.0, HAIR_WHITE, 0.62),
        ((17.0, -18.0), 12.0, 12.0, HAIR_LIGHT, 0.66),
        ((21.0, -7.0), 9.5, 11.5, HAIR_DARK, 0.48),
        ((-20.0, 0.0), 8.5, 10.5, HAIR_MID, 0.55),
        ((8.0, -8.0), 13.0, 11.0, HAIR_MID, 0.45),
    )
    for (dx, dy), rx, ry, color, alpha in islands:
        island_center = _rotate(
            (center[0] + dx + wind_x * 0.20, center[1] + dy + wind_y * 0.20),
            center,
            pose.head_tilt * 0.45,
        )
        _ellipse(
            draw,
            island_center,
            rx + charge * 0.9,
            ry + charge * 1.0,
            _fade(_mix(color, HAIR_GLEAM, charge * 0.34), alpha),
            None,
        )


def _draw_tapered_lock(draw: ImageDraw.ImageDraw, points: Sequence[Point], widths: Sequence[float], fill: RGBA, outline: RGBA) -> None:
    # Rounded variable-width segments read as tangled hair clumps.  Drawing the
    # outline pass first keeps the outer contour crisp while avoiding leaf-like
    # polygon seams through the connected halo.
    for color, extra in ((outline, 0.42), (fill, 0.0)):
        for i in range(len(points) - 1):
            width = max(0.8, (widths[i] + widths[i + 1]) * 0.5 + extra)
            _line(draw, [points[i], points[i + 1]], color, width)
            _ellipse(draw, points[i + 1], width * 0.52, width * 0.45, color, None)
    tip_width = max(0.9, widths[-1])
    _ellipse(draw, points[-1], tip_width * 0.62, tip_width * 0.54, fill, outline, 0.35)


def _draw_hair_layer(draw: ImageDraw.ImageDraw, pose: Pose, layer: str) -> None:
    if layer == "back":
        _draw_hair_mass(draw, pose)
    for lock in HAIR_LOCKS:
        if lock.layer != layer:
            continue
        points, widths = _lock_curve(lock, pose)
        fill = _hair_color(lock, pose)
        outline = _mix(fill, OUTLINE_SOFT, 0.42) if layer == "back" else OUTLINE
        _draw_tapered_lock(draw, points, widths, fill, outline)
        if lock.tone > 0.42:
            highlight = [
                _lerp_point(points[i], points[min(i + 1, len(points) - 1)], 0.18)
                for i in range(1, len(points) - 2)
            ]
            if len(highlight) >= 2:
                _line(draw, highlight, _fade(_hair_color(lock, pose, highlight=True), 0.48), max(0.42, lock.width * 0.10))

    if layer == "front":
        center = _head_center(pose)
        # A soft, irregular hairline makes the halo belong to the head rather
        # than sit behind it as a detachable crown.
        hairline = _catmull_open(
            [
                _rotate((center[0] - 11.5, center[1] - 4.0), center, pose.head_tilt),
                _rotate((center[0] - 7.0, center[1] - 9.0), center, pose.head_tilt),
                _rotate((center[0] - 1.5, center[1] - 10.5), center, pose.head_tilt),
                _rotate((center[0] + 4.0, center[1] - 9.2), center, pose.head_tilt),
                _rotate((center[0] + 10.8, center[1] - 4.5), center, pose.head_tilt),
            ],
            steps=5,
        )
        _line(draw, hairline, _mix(HAIR_DARK, HAIR_WHITE, pose.hair_charge * 0.45), 2.5)

        activity = _clamp01(abs(pose.acceleration_x) / 10.0 + pose.hair_charge * 0.8)
        for i, angle in enumerate((196, 231, 263, 294, 326, 351, 18, 169)):
            theta = math.radians(angle + pose.head_tilt)
            length = 5.0 + i % 3 * 1.2 + activity * 3.2
            root = (center[0] + math.cos(theta) * 23.0, center[1] + math.sin(theta) * 24.0)
            tip = (
                root[0] + math.cos(theta) * length - pose.velocity_x * 0.18,
                root[1] + math.sin(theta) * length - pose.velocity_y * 0.08,
            )
            bend = ((root[0] + tip[0]) * 0.5 + math.sin(i * 1.7) * 1.5, (root[1] + tip[1]) * 0.5)
            _line(draw, [root, bend, tip], _fade(HAIR_GLEAM, 0.18 + activity * 0.52), 0.45)


def _draw_leg(draw: ImageDraw.ImageDraw, pose: Pose, hip: Point, knee: Point, foot: Point, *, far: bool) -> None:
    hip = _body_point(hip, pose)
    knee = _body_point(knee, pose)
    foot = _body_point(foot, pose)
    trouser = TROUSER_DARK if far else TROUSER
    highlight = TROUSER if far else TROUSER_LIGHT
    _polygon(draw, _jointed_strip(hip, knee, foot, 5.2, 4.6, 3.8), trouser, OUTLINE, 1.0)
    _line(draw, [_lerp_point(hip, knee, 0.3), _lerp_point(knee, foot, 0.55)], highlight, 1.0)
    shoe_tip = (foot[0] + (7.0 if foot[0] >= 64.0 else -6.0), foot[1] + 0.5)
    _polygon(draw, _segment_quad(foot, shoe_tip, 3.8, 2.9), SHOE if not far else TROUSER_DARK, OUTLINE, 1.0)
    _line(draw, [_lerp_point(foot, shoe_tip, 0.35), shoe_tip], SHOE_LIGHT, 0.8)


def _draw_torso(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    shoulder_l = _body_point((51.0, 57.0), pose)
    shoulder_r = _body_point((77.0, 57.0), pose)
    waist_r = _body_point((71.0, 82.0), pose)
    waist_l = _body_point((56.0, 82.0), pose)
    torso = [shoulder_l, shoulder_r, waist_r, waist_l]
    _polygon(draw, torso, VEST, OUTLINE, 1.0)

    collar_l = _body_point((58.0, 56.0), pose)
    collar_r = _body_point((69.0, 56.0), pose)
    chest = _body_point((63.5, 66.0), pose)
    _polygon(draw, [shoulder_l, collar_l, chest, waist_l], VEST_LIGHT, OUTLINE_SOFT, 0.65)
    _polygon(draw, [shoulder_r, collar_r, chest, waist_r], VEST_DARK, OUTLINE_SOFT, 0.65)
    _polygon(draw, [collar_l, (63.5, 62.0), collar_r, (63.5, 54.0)], SHIRT_LIGHT, OUTLINE, 0.7)
    tie_top = _body_point((63.5, 59.0), pose)
    tie_mid = _body_point((63.5, 69.0), pose)
    tie_tip = _body_point((63.5, 75.0), pose)
    _polygon(draw, [(tie_top[0] - 2.0, tie_top[1]), (tie_top[0] + 2.0, tie_top[1]), (tie_mid[0] + 1.7, tie_mid[1]), tie_tip, (tie_mid[0] - 1.7, tie_mid[1])], TIE, OUTLINE, 0.7)
    _line(draw, [tie_top, tie_mid], TIE_LIGHT, 0.6)
    for y in (68.0, 76.0):
        pnt = _body_point((65.0, y), pose)
        _ellipse(draw, pnt, 0.9, 0.9, SHIRT_SHADE, OUTLINE_SOFT, 0.4)


def _draw_arm(draw: ImageDraw.ImageDraw, pose: Pose, shoulder: Point, elbow: Point, hand: Point, hand_mode: str, *, far: bool) -> None:
    shoulder = _body_point(shoulder, pose)
    elbow = _body_point(elbow, pose)
    hand = _body_point(hand, pose)
    shirt = SHIRT_SHADE if far else SHIRT
    _polygon(draw, _jointed_strip(shoulder, elbow, hand, 4.7, 4.2, 3.2), shirt, OUTLINE, 1.0)
    cuff_a = _lerp_point(elbow, hand, 0.60)
    cuff_b = _lerp_point(elbow, hand, 0.78)
    _polygon(draw, _segment_quad(cuff_a, cuff_b, 3.6, 3.3), SHIRT_LIGHT if not far else SHIRT, OUTLINE, 0.7)
    _draw_hand(draw, hand, hand_mode, far=far)


def _draw_hand(draw: ImageDraw.ImageDraw, hand: Point, mode: str, *, far: bool) -> None:
    skin = SKIN_SHADE if far else SKIN
    _ellipse(draw, hand, 3.3, 3.7, skin, OUTLINE, 0.8)
    if mode == "open":
        for offset_y, spread in ((-1.8, 1.0), (-0.5, 1.5), (0.8, 1.2)):
            _line(draw, [hand, (hand[0] + 4.5, hand[1] + offset_y * spread)], skin, 1.05)
    elif mode in ("precise", "explaining"):
        _line(draw, [hand, (hand[0] + 5.2, hand[1] - 4.2)], skin, 1.15)
        if mode == "explaining":
            _line(draw, [hand, (hand[0] + 4.4, hand[1] - 1.2)], skin, 1.0)
    elif mode == "stamp":
        _line(draw, [hand, (hand[0] + 4.0, hand[1] + 2.0)], skin, 1.2)
    elif mode == "page":
        _line(draw, [hand, (hand[0] - 3.8, hand[1] - 1.0)], skin, 1.0)


def _draw_neck_and_face(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    neck_center = _body_point((64.0, 53.0), pose)
    _ellipse(draw, neck_center, 5.0, 7.0, SKIN_SHADE, OUTLINE, 0.9)
    center = _head_center(pose)
    face_center = _rotate((center[0], center[1] + 3.0), center, pose.head_tilt)
    ear_l = _rotate((center[0] - 12.8, center[1] + 3.2), center, pose.head_tilt)
    ear_r = _rotate((center[0] + 12.4, center[1] + 2.8), center, pose.head_tilt)
    _ellipse(draw, ear_l, 3.1, 4.3, SKIN_SHADE, OUTLINE, 0.8)
    _ellipse(draw, ear_r, 3.0, 4.1, SKIN, OUTLINE, 0.8)
    _ellipse(draw, face_center, 12.8, 15.4, SKIN, OUTLINE, 1.1)
    _ellipse(draw, _rotate((center[0] - 4.5, center[1] - 1.8), center, pose.head_tilt), 5.0, 8.5, SKIN_LIGHT, None)
    _arc(draw, _rotate((center[0] + 5.2, center[1] + 2.2), center, pose.head_tilt), 5.4, 9.0, 278, 82, SKIN_SHADE, 0.8)

    eye_y = center[1] + 1.0
    left_eye = _rotate((center[0] - 4.7, eye_y), center, pose.head_tilt)
    right_eye = _rotate((center[0] + 4.5, eye_y), center, pose.head_tilt)
    if pose.blink:
        _line(draw, [(left_eye[0] - 2.0, left_eye[1]), (left_eye[0] + 2.0, left_eye[1] + 0.3)], EYE, 0.8)
        _line(draw, [(right_eye[0] - 2.0, right_eye[1] + 0.2), (right_eye[0] + 2.0, right_eye[1])], EYE, 0.8)
    else:
        eye_ry = 1.15 + pose.eye_wide * 0.8
        _ellipse(draw, left_eye, 1.55, eye_ry, SHIRT_LIGHT, EYE, 0.55)
        _ellipse(draw, right_eye, 1.55, eye_ry, SHIRT_LIGHT, EYE, 0.55)
        pupil_shift = 0.7 * pose.skeptical
        _ellipse(draw, (left_eye[0] + pupil_shift, left_eye[1] + 0.15), 0.55, 0.75, EYE, None)
        _ellipse(draw, (right_eye[0] + pupil_shift, right_eye[1] + 0.15), 0.55, 0.75, EYE, None)

    brow_y = center[1] - 3.4
    skeptical = pose.skeptical
    _line(draw, [
        _rotate((center[0] - 7.0, brow_y + skeptical * 1.2), center, pose.head_tilt),
        _rotate((center[0] - 2.1, brow_y - pose.brow), center, pose.head_tilt),
    ], BROW, 1.25)
    _line(draw, [
        _rotate((center[0] + 2.0, brow_y - skeptical * 1.0), center, pose.head_tilt),
        _rotate((center[0] + 7.0, brow_y + pose.brow), center, pose.head_tilt),
    ], BROW, 1.25)

    nose_top = _rotate((center[0] + 0.2, center[1] + 1.0), center, pose.head_tilt)
    nose_tip = _rotate((center[0] + 1.3, center[1] + 7.2), center, pose.head_tilt)
    _line(draw, [nose_top, nose_tip, (nose_tip[0] - 1.8, nose_tip[1] + 0.7)], SKIN_SHADE, 1.0)

    moustache_center = _rotate((center[0] + 0.2, center[1] + 9.2), center, pose.head_tilt)
    left_curve = [
        moustache_center,
        (moustache_center[0] - 2.3, moustache_center[1] - 1.2),
        (moustache_center[0] - 5.0, moustache_center[1] - 0.4),
        (moustache_center[0] - 7.0, moustache_center[1] + 1.2),
    ]
    right_curve = [
        moustache_center,
        (moustache_center[0] + 2.2, moustache_center[1] - 1.3),
        (moustache_center[0] + 4.9, moustache_center[1] - 0.5),
        (moustache_center[0] + 6.8, moustache_center[1] + 0.9),
    ]
    _line(draw, left_curve, MOUSTACHE, 2.25)
    _line(draw, right_curve, MOUSTACHE, 2.25)
    _ellipse(draw, left_curve[-1], 1.25, 0.9, MOUSTACHE, OUTLINE, 0.35)
    _ellipse(draw, right_curve[-1], 1.25, 0.9, MOUSTACHE, OUTLINE, 0.35)

    mouth_y = center[1] + 12.0
    mouth_center = _rotate((center[0], mouth_y), center, pose.head_tilt)
    if pose.mouth_open > 0.05:
        _ellipse(draw, mouth_center, 2.8 + pose.smile, 1.1 + pose.mouth_open * 2.0, SKIN_RED, OUTLINE, 0.55)
        _line(draw, [(mouth_center[0] - 1.5, mouth_center[1] - 0.4), (mouth_center[0] + 1.6, mouth_center[1] - 0.4)], SHIRT_LIGHT, 0.45)
    else:
        _arc(draw, mouth_center, 3.3 + pose.smile, 2.0, 18 - pose.smile * 20, 162 + pose.smile * 20, SKIN_RED, 0.75)


def _draw_label(draw: ImageDraw.ImageDraw, center: Point, text: str, *, color: RGBA = STAMP, scale: float = 1.0) -> None:
    if not text:
        return
    font = _font(4.2 * scale, bold=True)
    anchor = "mm"
    pad_x = 2.4 * scale
    pad_y = 1.4 * scale
    box = draw.textbbox(_pt(center), text, font=font, anchor=anchor, stroke_width=0)
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 - _s(pad_x), y1 - _s(pad_y), x2 + _s(pad_x), y2 + _s(pad_y)), radius=_s(1.2), fill=_fade(PAPER, 0.94), outline=color, width=_s(0.8))
    draw.text(_pt(center), text, font=font, fill=color, anchor=anchor)


def _draw_clock(draw: ImageDraw.ImageDraw, center: Point, radius: float, phase: float, *, alpha: float = 1.0) -> None:
    _ellipse(draw, center, radius, radius, _fade(PAPER, alpha), _fade(CLOCK_GOLD, alpha), 1.1)
    _ellipse(draw, center, radius * 0.12, radius * 0.12, _fade(INK, alpha), None)
    for i in range(12):
        theta = math.radians(i * 30.0 - 90.0)
        a = (center[0] + math.cos(theta) * radius * 0.74, center[1] + math.sin(theta) * radius * 0.74)
        b = (center[0] + math.cos(theta) * radius * 0.90, center[1] + math.sin(theta) * radius * 0.90)
        _line(draw, [a, b], _fade(INK, alpha), 0.45 if i % 3 else 0.75)
    hour = math.radians(phase * 240.0 - 90.0)
    minute = math.radians(phase * 720.0 - 90.0)
    _line(draw, [center, (center[0] + math.cos(hour) * radius * 0.48, center[1] + math.sin(hour) * radius * 0.48)], _fade(INK, alpha), 1.0)
    _line(draw, [center, (center[0] + math.cos(minute) * radius * 0.68, center[1] + math.sin(minute) * radius * 0.68)], _fade(INK, alpha), 0.65)


def _draw_arrow(draw: ImageDraw.ImageDraw, a: Point, b: Point, color: RGBA, width: float = 1.0) -> None:
    _line(draw, [a, b], color, width)
    along, normal, _ = _unit(a, b)
    tip = b
    wing = 3.0 + width
    left = (tip[0] - along[0] * wing + normal[0] * wing * 0.55, tip[1] - along[1] * wing + normal[1] * wing * 0.55)
    right = (tip[0] - along[0] * wing - normal[0] * wing * 0.55, tip[1] - along[1] * wing - normal[1] * wing * 0.55)
    _polygon(draw, [tip, left, right], color, color, 0.4)


def _draw_effects_behind(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    q = pose.effect_phase
    if pose.effect == "reference_frame":
        alpha = 0.25 + 0.55 * q
        left = 21.0 - q * 4.0
        top = 27.0 - q * 5.0
        right = 108.0 + q * 3.0
        bottom = 112.0 + q * 2.0
        draw.rounded_rectangle(_rect(left, top, right, bottom), radius=_s(5.0), fill=_fade(FRAME_BLUE, 0.08 * q), outline=_fade(FRAME_BLUE, alpha), width=_s(1.2))
        _draw_arrow(draw, (27.0, 103.0), (101.0, 103.0), _fade(FRAME_LIGHT, alpha), 1.1)
        _draw_arrow(draw, (101.0, 36.0), (27.0, 36.0), _fade(FRAME_LIGHT, alpha), 0.8)

    elif pose.effect == "elevator":
        alpha = 0.35 + 0.55 * q
        left, right = 40.0, 89.0
        top, bottom = 16.0, 117.0
        draw.rectangle(_rect(left, top, right, bottom), fill=_fade(FRAME_BLUE, 0.05 * q), outline=_fade(FRAME_LIGHT, alpha), width=_s(1.2))
        _line(draw, [(left + 5.0, bottom - 8.0), (right - 5.0, bottom - 8.0)], _fade(FRAME_BLUE, alpha), 1.4)
        for x in (50.0, 64.5, 79.0):
            _draw_arrow(draw, (x, bottom - 5.0), (x, top + 9.0), _fade(FRAME_LIGHT, alpha), 0.75)

    elif pose.effect == "clocks":
        _line(draw, [(31.0, 59.0), (97.0, 59.0)], _fade(CLOCK_LIGHT, 0.25 + q * 0.5), 0.7)
        _draw_clock(draw, (28.0, 54.0), 12.0 + q * 1.5, pose.hair_phase + 0.05, alpha=0.45 + q * 0.55)
        _draw_clock(draw, (100.0, 54.0), 12.0 + q * 1.5, pose.hair_phase + 0.31, alpha=0.45 + q * 0.55)

    elif pose.effect == "conversion":
        t = q
        gather = _smooth(min(1.0, t * 2.0))
        collapse = _smooth(max(0.0, (t - 0.43) / 0.32))
        release = _smooth(max(0.0, (t - 0.68) / 0.22))
        sep = _lerp(27.0, 7.0, collapse)
        center_y = 66.0
        _ellipse(draw, (64.0 - sep, center_y), 9.0 + gather * 2.0, 9.0 + gather * 2.0, _fade(MASS_COLOR, 0.28 + gather * 0.55), MASS_COLOR, 1.1)
        _ellipse(draw, (64.0 + sep, center_y), 9.0 + gather * 2.0, 9.0 + gather * 2.0, _fade(ENERGY_COLOR, 0.24 + gather * 0.6), ENERGY_LIGHT, 1.1)
        if release > 0.0:
            for i in range(3):
                radius = 9.0 + release * (15.0 + i * 10.0)
                _ellipse(draw, (64.0, center_y), radius, radius, (0, 0, 0, 0), _fade(CONVERSION, (1.0 - release) * (0.7 - i * 0.12)), 1.0)

    elif pose.effect == "annus_mirabilis":
        t = q
        office = _smooth(min(1.0, t * 3.2)) * (1.0 - _smooth(max(0.0, (t - 0.86) / 0.14)))
        draw.rectangle(_rect(18.0, 18.0, 110.0, 116.0), fill=_fade((20, 24, 34, 255), office * 0.32), outline=_fade(FRAME_LIGHT, office * 0.28), width=_s(0.8))
        beam_y = 31.0 + t * 59.0
        _polygon(draw, [(18.0, beam_y - 3.0), (110.0, beam_y + 5.0), (110.0, beam_y + 9.0), (18.0, beam_y + 1.0)], _fade(CONVERSION, office * 0.18), _fade(CONVERSION, office * 0.22), 0.4)
        _draw_clock(draw, (31.0, 37.0), 9.0, t * 0.72, alpha=office * 0.8)
        _draw_clock(draw, (97.0, 37.0), 9.0, t * 1.31, alpha=office * 0.8)
        for i in range(4):
            page_t = _clamp01(t * 1.5 - i * 0.15)
            x = 35.0 + i * 17.0
            y = 95.0 - page_t * 9.0 + math.sin(t * math.tau + i) * 1.2
            draw.rounded_rectangle(_rect(x - 6.0, y - 5.0, x + 6.0, y + 5.0), radius=_s(1.0), fill=_fade(PAPER, office * 0.75), outline=_fade(PAPER_SHADE, office * 0.85), width=_s(0.6))

    elif pose.effect in ("block", "known_result"):
        radius = 24.0 + q * 8.0
        _arc(draw, (64.0, 68.0), radius, radius * 1.25, 198, 342, _fade(FRAME_LIGHT, 0.35 + q * 0.55), 1.4)


def _draw_effects_front(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    q = pose.effect_phase
    if pose.effect == "small_stamp":
        center = _body_point((95.0, 69.0), pose)
        _draw_label(draw, center, pose.label, color=STAMP, scale=0.9)
        _line(draw, [(center[0] - 10.0, center[1] + 7.0), (center[0] + 10.0, center[1] + 7.0)], _fade(STAMP, q), 0.8)

    elif pose.effect == "application_review":
        hand = _body_point(pose.right_hand, pose)
        paper_center = (hand[0] + 7.0, hand[1] + 1.0)
        draw.rounded_rectangle(_rect(paper_center[0] - 11.0, paper_center[1] - 7.0, paper_center[0] + 11.0, paper_center[1] + 7.0), radius=_s(1.3), fill=_fade(PAPER, 0.88), outline=PAPER_SHADE, width=_s(0.8))
        _draw_label(draw, paper_center, pose.label, color=STAMP, scale=0.72)
        _line(draw, [(paper_center[0] - 8.0, paper_center[1] + 5.0), (paper_center[0] + 7.0, paper_center[1] + 5.0)], _fade(INK, 0.65), 0.45)

    elif pose.effect == "margin_correction":
        hand = _body_point(pose.right_hand, pose)
        end = (min(126.0, hand[0] + 22.0), hand[1] - 6.0)
        elbow = ((hand[0] + end[0]) * 0.5, hand[1] + 4.0)
        _line(draw, [hand, elbow, end], _fade(INK, 0.35 + q * 0.65), 2.0)
        _line(draw, [(end[0] - 5.0, end[1] - 5.0), (end[0] + 2.0, end[1] + 3.0)], _fade(STAMP_LIGHT, q), 1.1)
        _line(draw, [(end[0] - 4.0, end[1] + 4.0), (end[0] + 4.0, end[1] - 4.0)], _fade(STAMP_LIGHT, q), 1.1)

    elif pose.effect == "light_argument":
        hand = _body_point(pose.right_hand, pose)
        beam_end = (127.0, hand[1] - 2.0)
        _line(draw, [hand, beam_end], _fade(CONVERSION, 0.28 + q * 0.72), 1.5)
        _line(draw, [(hand[0] + 4.0, hand[1] - 1.0), beam_end], _fade(FRAME_LIGHT, 0.18 + q * 0.65), 0.65)
        _ellipse(draw, hand, 3.5 + q * 2.0, 3.5 + q * 2.0, _fade(CONVERSION, 0.20 + q * 0.35), CONVERSION, 0.7)

    elif pose.effect == "reference_frame":
        _draw_label(draw, (92.0, 106.0), "LOCAL", color=FRAME_BLUE, scale=0.68)

    elif pose.effect == "elevator":
        _draw_label(draw, (64.5, 113.0), "ACCELERATING", color=FRAME_BLUE, scale=0.68)

    elif pose.effect == "clocks":
        _draw_label(draw, (64.0, 91.0), "SYNCHRONIZE", color=CLOCK_GOLD, scale=0.66)

    elif pose.effect == "conversion":
        t = q
        collapse = _smooth(max(0.0, (t - 0.43) / 0.32))
        sep = _lerp(27.0, 7.0, collapse)
        _draw_label(draw, (64.0 - sep, 82.0), "MASS", color=MASS_COLOR, scale=0.66)
        _draw_label(draw, (64.0 + sep, 82.0), "ENERGY", color=ENERGY_COLOR, scale=0.66)
        if t > 0.67:
            flash = _pulse(_clamp01((t - 0.67) / 0.33))
            _ellipse(draw, (64.0, 66.0), 6.0 + flash * 8.0, 6.0 + flash * 8.0, _fade(CONVERSION, flash * 0.65), CONVERSION, 0.9)

    elif pose.effect == "known_result":
        _draw_label(draw, (94.0, 47.0), "KNOWN RESULT", color=FRAME_BLUE, scale=0.68)
        _draw_arrow(draw, (104.0, 61.0), (82.0, 67.0), _fade(FRAME_LIGHT, q), 0.8)

    elif pose.effect == "block":
        _draw_label(draw, (64.0, 43.0), "AT REST", color=MASS_COLOR, scale=0.75)

    elif pose.effect == "annus_mirabilis":
        t = q
        labels = ("MASS", "ENERGY", "MOVING", "AT REST")
        for i, label in enumerate(labels):
            appear = _smooth(_clamp01(t * 4.0 - i * 0.55))
            x = 35.0 + i * 19.0
            y = 96.0 - appear * 12.0
            color = MASS_COLOR if i in (0, 3) else ENERGY_COLOR if i == 1 else FRAME_BLUE
            _draw_label(draw, (x, y), label, color=_fade(color, appear), scale=0.58)
        if t > 0.78:
            flash = _smooth((t - 0.78) / 0.22)
            for i in range(5):
                radius = 12.0 + flash * (8.0 + i * 9.0)
                _ellipse(draw, (64.0, 66.0), radius, radius, (0, 0, 0, 0), _fade(CONVERSION, (1.0 - flash) * (0.75 - i * 0.10)), 1.0)


def _render_native_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose(animation, frame_idx, nframes)
    image = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    draw = blending_draw(image)

    _draw_effects_behind(draw, pose)
    _draw_hair_layer(draw, pose, "back")

    # Far limbs first, then body, then near limbs.  The ordering is bespoke to
    # the compact clerk posture and keeps the rolled sleeves readable.
    _draw_leg(draw, pose, pose.right_hip, pose.right_knee, pose.right_foot, far=True)
    _draw_arm(draw, pose, pose.left_shoulder, pose.left_elbow, pose.left_hand, pose.left_hand_mode, far=True)
    _draw_leg(draw, pose, pose.left_hip, pose.left_knee, pose.left_foot, far=False)
    _draw_torso(draw, pose)
    _draw_arm(draw, pose, pose.right_shoulder, pose.right_elbow, pose.right_hand, pose.right_hand_mode, far=False)
    _draw_neck_and_face(draw, pose)
    _draw_hair_layer(draw, pose, "front")
    _draw_effects_front(draw, pose)
    return image


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _render_native_frame(animation, frame_idx, nframes).resize((FRAME_W, FRAME_H), Image.Resampling.LANCZOS)


def _portrait_pose(expression: str, frame_idx: int, nframes: int) -> Pose:
    if expression == "default":
        pose = _pose("idle", 1, 8)
        pose.smile = 0.08
        pose.skeptical = 0.22
        pose.hair_charge = 0.10
        return pose
    if expression == "speaking":
        pose = _pose("talk", frame_idx, nframes)
        pose.hair_charge = 0.12
        return pose
    if expression == "reviewing":
        pose = _pose("application_review", min(frame_idx, 4), max(6, nframes))
        pose.skeptical = 0.85
        pose.mouth_open = 0.08
        pose.hair_charge = 0.22
        return pose
    if expression == "illumination":
        pose = _pose("annus_mirabilis", max(5, frame_idx), max(10, nframes))
        pose.hair_charge = 0.92
        pose.eye_wide = 0.35
        return pose
    raise KeyError(expression)


def _render_native_portrait(expression: str, frame_idx: int = 0, nframes: int = 1) -> Image.Image:
    pose = _portrait_pose(expression, frame_idx, nframes)
    # Portraits are freshly rerendered from the authored geometry at native
    # supersampled resolution.  This is not a crop of a sheet frame.
    image = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    draw = blending_draw(image)
    _draw_effects_behind(draw, pose)
    _draw_hair_layer(draw, pose, "back")
    _draw_leg(draw, pose, pose.right_hip, pose.right_knee, pose.right_foot, far=True)
    _draw_arm(draw, pose, pose.left_shoulder, pose.left_elbow, pose.left_hand, pose.left_hand_mode, far=True)
    _draw_leg(draw, pose, pose.left_hip, pose.left_knee, pose.left_foot, far=False)
    _draw_torso(draw, pose)
    _draw_arm(draw, pose, pose.right_shoulder, pose.right_elbow, pose.right_hand, pose.right_hand_mode, far=False)
    _draw_neck_and_face(draw, pose)
    _draw_hair_layer(draw, pose, "front")
    _draw_effects_front(draw, pose)
    guide = FaceGuide(center_x=88.0, center_y=58.0, width=42.0, height=45.0, source_width=176.0, source_height=176.0)
    return render_framed_portrait(image, guide, output_size=(256, 320), view_width=76.0, center_y=70.0)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    del opts
    clips = {
        "default": PortraitClip.still(_render_native_portrait("default")),
        "speaking": PortraitClip(
            tuple(_render_native_portrait("speaking", idx, 8) for idx in range(8)),
            duration_ms=104,
            looping=True,
        ),
        "reviewing": PortraitClip.still(_render_native_portrait("reviewing", 4, 6)),
        "illumination": PortraitClip.still(_render_native_portrait("illumination", 8, 10)),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def _body_metrics_override(fw: int, fh: int):
    del fw, fh
    return {
        "body_pixel_bbox": {"x": 62, "y": 56, "w": 54, "h": 91},
        "feet_pixel": {"x": 88.0, "y": 137.0},
        "feet_anchor_norm": {"x": 0.0, "y": round(0.5 - 137.0 / 176.0, 6)},
    }


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        label_width=116,
        auto_crop=False,
        body_metrics_fn=_body_metrics_override,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.0, "frame_sample_inset": 1},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        trim=False,
        attack_hitboxes={
            "application_review": {"bbox": {"x": 100, "y": 75, "w": 46, "h": 40}},
            "margin_correction": {"bbox": {"x": 104, "y": 66, "w": 48, "h": 50}},
            "light_argument": {"bbox": {"x": 108, "y": 66, "w": 44, "h": 34}},
            "reference_frame": {"bbox": {"x": 44, "y": 50, "w": 90, "h": 87}},
            "mass_energy_conversion": {"bbox": {"x": 46, "y": 61, "w": 84, "h": 65}},
            "annus_mirabilis": {"bbox": {"x": 42, "y": 42, "w": 92, "h": 98}},
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
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=(FRAME_W, FRAME_H))


def source_uses_forbidden_raster_effects() -> bool:
    """This target uses explicit geometry and LANCZOS downsampling only."""
    return False


__all__ = [
    "ACTOR_METADATA",
    "HAIR_LOCKS",
    "ROWS",
    "TARGET_NAME",
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
    outputs.extend(render_portraits(args.out_dir))
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
