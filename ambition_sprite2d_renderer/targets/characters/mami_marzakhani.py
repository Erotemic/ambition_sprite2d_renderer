"""Procedural full-action renderer for Mami Marzakhani.

Mami is a modern geometer whose silhouette is carried by a broad halo of dark
curls, a long asymmetrical garnet jacket, an ivory collar, and quick expressive
hands.  Her mathematical effects are contour lines, boundaries, and geodesics
that grow directly from her gestures.  The base character uses no held prop and
no floor ellipse or drop shadow.

The gameplay sprite and the dialog portrait are independently rerendered from
vector-like Pillow geometry.  Portraits therefore preserve facial detail and
hair texture at native portrait resolution rather than enlarging a gameplay
frame.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from ...authoring.portrait import PortraitClip, write_portrait_sheet
from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "mami_marzakhani"
FRAME_W = 128
FRAME_H = 128
SUPER = 4
USES_PROPS = False
USES_DROP_SHADOW = False

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 150),
    ("walk", 8, 104),
    ("run", 8, 78),
    ("crouch", 6, 96),
    ("crouch_walk", 8, 90),
    ("jump", 6, 88),
    ("fall", 6, 92),
    ("land_hard", 7, 82),
    ("dash_startup", 4, 52),
    ("dash", 6, 58),
    ("slide", 6, 70),
    ("roll", 8, 60),
    ("wall_grab", 6, 104),
    ("wall_jump", 6, 82),
    ("ledge_grab", 6, 98),
    ("ledge_climb", 6, 94),
    ("climb", 8, 98),
    ("swim", 8, 104),
    ("block", 6, 82),
    ("hit", 5, 84),
    ("death", 8, 106),
    ("talk", 8, 106),
    ("interact", 8, 94),
    ("geodesic_sweep", 8, 66),
    ("boundary_fold", 8, 72),
    ("moduli_bloom", 10, 78),
    ("celebrate", 8, 88),
    ("taunt", 8, 94),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_mami_marzakhani",
        "display_name": "Mami Marzakhani",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "mathematician",
            "geometer",
            "boundary_walker",
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
        "portrait": {
            "face_guide": {
                "center": {"x": 64.0, "y": 33.0},
                "size": {"w": 30.0, "h": 34.0},
                "source_size": {"w": 128.0, "h": 128.0},
            }
        },
    },
    "tags": [
        "story",
        "humanoid",
        "mathematician",
        "geometer",
        "boundary_walker",
        "playable_candidate",
    ],
    "sockets": {
        "head": {
            "source": "explicit.mami_marzakhani",
            "point": {"x": 64.0, "y": 31.0},
        },
        "chest": {
            "source": "explicit.mami_marzakhani",
            "point": {"x": 64.0, "y": 68.0},
        },
        "hand_l": {
            "source": "explicit.mami_marzakhani",
            "point": {"x": 43.0, "y": 78.0},
        },
        "hand_r": {
            "source": "explicit.mami_marzakhani",
            "point": {"x": 86.0, "y": 77.0},
        },
        "speech_bubble": {
            "source": "explicit.mami_marzakhani",
            "point": {"x": 64.0, "y": 4.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "geodesic_sweep", "events": []},
        "action.ranged.primary": {"animation": "boundary_fold", "events": []},
        "action.special.primary": {"animation": "moduli_bloom", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "gpt_5_6_thinking_original_2026_07_20",
        "lineage": [
            {
                "revision_id": "mami_marzakhani_name_and_direction",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "contribution": "character_name_quality_bar_and_no_drop_shadow_direction",
            },
            {
                "revision_id": "mami_marzakhani_procedural_sprite_v1",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "parent_revision_id": "mami_marzakhani_name_and_direction",
                "contribution": "procedural_full_action_sprite_and_native_portrait_authoring",
            },
            {
                "revision_id": "mami_marzakhani_rename_from_mary",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "parent_revision_id": "mami_marzakhani_procedural_sprite_v1",
                "contribution": "renamed_character_mary_to_mami_across_target_and_assets",
            },
        ],
    },
}

# A restrained, warm palette.  Hair and clothing use several close values so
# the sprite reads as dimensional without relying on blur, gradients, or a cast
# floor shadow.
OUTLINE = (19, 20, 24, 255)
OUTLINE_SOFT = (46, 39, 45, 255)
SKIN = (181, 127, 92, 255)
SKIN_LIGHT = (226, 170, 128, 255)
SKIN_SHADE = (137, 88, 69, 255)
SKIN_WARM = (195, 121, 94, 255)
HAIR_DEEP = (24, 20, 24, 255)
HAIR = (42, 31, 38, 255)
HAIR_MID = (67, 47, 57, 255)
HAIR_GLEAM = (105, 72, 80, 255)
GARNET = (125, 39, 58, 255)
GARNET_LIGHT = (165, 55, 75, 255)
GARNET_DARK = (83, 28, 44, 255)
GARNET_DEEP = (58, 23, 36, 255)
IVORY = (237, 221, 191, 255)
IVORY_SHADE = (190, 169, 145, 255)
TEAL = (39, 103, 103, 255)
TEAL_LIGHT = (67, 139, 135, 255)
TEAL_DARK = (27, 67, 73, 255)
TROUSER = (46, 49, 61, 255)
TROUSER_LIGHT = (72, 75, 88, 255)
TROUSER_DARK = (29, 31, 41, 255)
SHOE = (48, 39, 44, 255)
SHOE_LIGHT = (84, 67, 70, 255)
EYE = (40, 28, 26, 255)
BROW = (57, 35, 35, 255)
MOUTH = (119, 55, 57, 255)
LIP_LIGHT = (186, 93, 91, 255)
GEODESIC = (245, 203, 91, 255)
GEODESIC_LIGHT = (255, 235, 164, 255)
BOUNDARY = (85, 205, 191, 255)
BOUNDARY_LIGHT = (169, 239, 226, 255)
MODULI = (176, 116, 205, 255)
MODULI_LIGHT = (229, 190, 243, 255)


def _s(value: float) -> int:
    return max(1, int(round(value * SUPER)))


def _pt(point: Point) -> Tuple[int, int]:
    return (int(round(point[0] * SUPER)), int(round(point[1] * SUPER)))


def _box(center: Point, rx: float, ry: float) -> Tuple[int, int, int, int]:
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
    _along, normal, _length = _unit(a, b)
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
        _box(center, rx, ry),
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
    draw.arc(_box(center, rx, ry), start=start, end=end, fill=fill, width=_s(width))


def _fade(color: RGBA, strength: float) -> RGBA:
    return (color[0], color[1], color[2], int(round(color[3] * _clamp01(strength))))


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf")
        if bold
        else ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
    )
    for name in names:
        try:
            return ImageFont.truetype(name, _s(size))
        except OSError:
            pass
    return ImageFont.load_default()


@dataclass(frozen=True)
class Pose:
    root: Point = (64.0, 0.0)
    root_angle: float = 0.0
    head: Point = (64.0, 31.0)
    head_angle: float = 0.0
    torso: Point = (64.0, 68.0)
    far_shoulder: Point = (51.0, 59.0)
    near_shoulder: Point = (78.0, 58.0)
    far_elbow: Point = (44.0, 75.0)
    near_elbow: Point = (86.0, 75.0)
    far_hand: Point = (43.0, 88.0)
    near_hand: Point = (88.0, 88.0)
    far_hip: Point = (57.0, 89.0)
    near_hip: Point = (70.0, 89.0)
    far_knee: Point = (54.0, 104.0)
    near_knee: Point = (73.0, 104.0)
    far_ankle: Point = (53.0, 117.0)
    near_ankle: Point = (75.0, 117.0)
    far_hand_mode: str = "relaxed"
    near_hand_mode: str = "open"
    expression: str = "focused"
    hair_lift: float = 0.0
    coat_flare: float = 0.0
    squash: float = 0.0
    geodesic: float = 0.0
    boundary: float = 0.0
    moduli: float = 0.0
    effect_phase: float = 0.0
    hidden: float = 0.0


def _base_pose() -> Pose:
    return Pose()


def _pose(animation: str, frame_idx: int, nframes: int) -> Pose:
    t = frame_idx / max(1, nframes - 1)
    phase = frame_idx / max(1, nframes)
    wave = math.sin(phase * math.tau)
    bob = math.sin(phase * math.tau * 2.0)
    pose = _base_pose()

    if animation == "idle":
        breath = 0.7 * math.sin(phase * math.tau)
        return replace(
            pose,
            root=(64.0, breath * 0.35),
            head=(64.2, 31.0 - breath * 0.25),
            near_hand=(88.0 + 0.8 * wave, 88.0 - 0.7 * wave),
            hair_lift=0.25 * wave,
            coat_flare=0.15 * wave,
            expression="soft" if frame_idx in (2, 3) else "focused",
        )

    if animation in {"walk", "run", "crouch_walk"}:
        speed = 1.0 if animation == "walk" else 1.45
        crouch = 4.0 if animation == "crouch_walk" else 0.0
        stride = math.sin(phase * math.tau) * (9.0 if animation == "walk" else 14.0)
        arm = -stride * 0.72
        lift_far = max(0.0, math.sin(phase * math.tau)) * 4.0
        lift_near = max(0.0, -math.sin(phase * math.tau)) * 4.0
        lean = 1.5 if animation == "walk" else 7.0
        return replace(
            pose,
            root=(64.0, crouch * 0.42 + abs(bob) * speed),
            root_angle=lean,
            head=(64.5 + lean * 0.08, 31.0 + crouch),
            torso=(64.0, 68.0 + crouch),
            far_shoulder=(51.0, 59.0 + crouch),
            near_shoulder=(78.0, 58.0 + crouch),
            far_elbow=(44.0 + arm * 0.32, 74.0 + crouch),
            near_elbow=(86.0 - arm * 0.32, 74.0 + crouch),
            far_hand=(42.0 + arm * 0.70, 87.0 + crouch),
            near_hand=(89.0 - arm * 0.70, 87.0 + crouch),
            far_hip=(57.0, 89.0 + crouch),
            near_hip=(70.0, 89.0 + crouch),
            far_knee=(54.0 - stride * 0.35, 103.0 + crouch - lift_far),
            near_knee=(73.0 + stride * 0.35, 103.0 + crouch - lift_near),
            far_ankle=(53.0 - stride, 114.0 + crouch * 0.15 - lift_far),
            near_ankle=(75.0 + stride, 114.0 + crouch * 0.15 - lift_near),
            hair_lift=0.5 * bob + (0.8 if animation == "run" else 0.0),
            coat_flare=0.55 * stride,
            expression="determined" if animation == "run" else "focused",
        )

    if animation == "crouch":
        amount = _smooth(t)
        return replace(
            pose,
            root=(64.0, 2.0 * amount),
            head=(64.0, 31.0 + 5.0 * amount),
            torso=(64.0, 68.0 + 6.0 * amount),
            far_shoulder=(51.0, 59.0 + 5.5 * amount),
            near_shoulder=(78.0, 58.0 + 5.5 * amount),
            far_elbow=(47.0, 76.0 + 5.0 * amount),
            near_elbow=(82.0, 76.0 + 5.0 * amount),
            far_hand=(50.0, 88.0 + 5.0 * amount),
            near_hand=(79.0, 88.0 + 5.0 * amount),
            far_knee=(47.0, 103.0 + 2.0 * amount),
            near_knee=(79.0, 103.0 + 2.0 * amount),
            far_ankle=(44.0, 117.0),
            near_ankle=(83.0, 117.0),
            squash=amount,
        )

    if animation in {"jump", "fall", "wall_jump"}:
        if animation == "jump":
            lift = -6.0 * _pulse(t)
            direction = 1.0
        elif animation == "fall":
            lift = -5.0 + 8.0 * t
            direction = 1.0
        else:
            lift = -6.0 * _pulse(t)
            direction = -1.0
        tuck = _pulse(t)
        return replace(
            pose,
            root=(64.0 + direction * 3.0 * t, lift),
            root_angle=direction * 6.0,
            far_elbow=(42.0, 67.0 - 5.0 * tuck),
            near_elbow=(88.0, 67.0 - 6.0 * tuck),
            far_hand=(39.0, 78.0 - 10.0 * tuck),
            near_hand=(92.0, 77.0 - 11.0 * tuck),
            far_knee=(49.0, 99.0 - 5.0 * tuck),
            near_knee=(79.0, 99.0 - 7.0 * tuck),
            far_ankle=(56.0, 110.0 - 6.0 * tuck),
            near_ankle=(73.0, 108.0 - 8.0 * tuck),
            far_hand_mode="open",
            hair_lift=1.7 * tuck,
            coat_flare=7.0 * direction,
            expression="determined",
        )

    if animation == "land_hard":
        impact = _pulse(min(1.0, t * 1.45))
        recover = _smooth(max(0.0, (t - 0.35) / 0.65))
        down = 3.0 * impact * (1.0 - 0.45 * recover)
        return replace(
            pose,
            root=(64.0, down),
            head=(64.0, 31.0 + down * 0.60),
            torso=(64.0, 68.0 + down * 0.72),
            far_elbow=(45.0, 78.0 + down * 0.7),
            near_elbow=(85.0, 78.0 + down * 0.7),
            far_hand=(40.0, 91.0 + down * 0.45),
            near_hand=(91.0, 91.0 + down * 0.45),
            far_knee=(46.0, 104.0 + down * 0.25),
            near_knee=(81.0, 104.0 + down * 0.25),
            far_ankle=(43.0, 117.0),
            near_ankle=(85.0, 117.0),
            squash=impact,
            hair_lift=-0.8 * impact,
            coat_flare=4.0 * impact,
            expression="strained" if impact > 0.35 else "focused",
        )

    if animation in {"dash_startup", "dash", "slide"}:
        if animation == "dash_startup":
            amount = _smooth(t)
            travel = 0.0
        elif animation == "dash":
            amount = 1.0
            travel = 5.0 * t
        else:
            amount = 1.0
            travel = 3.0 * t
        low = 0.0
        return replace(
            pose,
            root=(64.0 + travel, low),
            root_angle=16.0 * amount,
            head=(67.0 + travel, 31.0 + low),
            torso=(68.0 + travel, 68.0 + low),
            far_shoulder=(54.0 + travel, 61.0 + low),
            near_shoulder=(81.0 + travel, 59.0 + low),
            far_elbow=(42.0 + travel, 70.0 + low),
            near_elbow=(90.0 + travel, 67.0 + low),
            far_hand=(33.0 + travel, 74.0 + low),
            near_hand=(101.0 + travel, 68.0 + low),
            far_hip=(60.0 + travel, 89.0 + low),
            near_hip=(73.0 + travel, 89.0 + low),
            far_knee=(49.0 + travel, 101.0 + low),
            near_knee=(78.0 + travel, 100.0 + low),
            far_ankle=(41.0 + travel, 112.0 + low),
            near_ankle=(92.0 + travel, 108.0 + low),
            far_hand_mode="fist",
            near_hand_mode="fist",
            hair_lift=1.5 * amount,
            coat_flare=-9.0 * amount,
            expression="determined",
        )

    if animation == "roll":
        angle = -74.0 * math.sin(t * math.pi)
        center = (73.0 + 2.0 * math.sin(t * math.pi), -2.0 * _pulse(t))
        compressed = replace(
            pose,
            root=center,
            root_angle=angle,
            head=(64.0, 58.0),
            torso=(64.0, 76.0),
            far_shoulder=(53.0, 68.0),
            near_shoulder=(75.0, 67.0),
            far_elbow=(49.0, 78.0),
            near_elbow=(79.0, 78.0),
            far_hand=(54.0, 86.0),
            near_hand=(74.0, 86.0),
            far_hip=(57.0, 87.0),
            near_hip=(70.0, 87.0),
            far_knee=(51.0, 95.0),
            near_knee=(77.0, 95.0),
            far_ankle=(58.0, 101.0),
            near_ankle=(71.0, 101.0),
            squash=1.0,
            hair_lift=1.0,
            coat_flare=4.0,
            expression="determined",
        )
        return compressed

    if animation in {"wall_grab", "ledge_grab", "ledge_climb", "climb"}:
        reach = 10.0 if animation in {"wall_grab", "ledge_grab"} else 5.0
        climb_wave = math.sin(phase * math.tau)
        return replace(
            pose,
            root=(64.0, -3.0 * climb_wave if animation == "climb" else 0.0),
            root_angle=-4.0,
            far_elbow=(45.0, 55.0 - reach),
            near_elbow=(85.0, 54.0 - reach),
            far_hand=(41.0, 43.0 - reach),
            near_hand=(90.0, 42.0 - reach),
            far_hip=(58.0, 88.0),
            near_hip=(70.0, 89.0),
            far_knee=(52.0 + 5.0 * climb_wave, 101.0),
            near_knee=(76.0 - 5.0 * climb_wave, 103.0),
            far_ankle=(48.0 + 8.0 * climb_wave, 114.0),
            near_ankle=(80.0 - 8.0 * climb_wave, 116.0),
            far_hand_mode="grip",
            near_hand_mode="grip",
            hair_lift=0.3 * climb_wave,
            expression="determined",
        )

    if animation == "swim":
        stroke = math.sin(phase * math.tau)
        return replace(
            pose,
            root=(59.0, -1.0),
            root_angle=56.0,
            head=(83.0, 54.0),
            torso=(64.0, 67.0),
            far_shoulder=(72.0, 55.0),
            near_shoulder=(76.0, 73.0),
            far_elbow=(83.0 + 10.0 * stroke, 48.0),
            near_elbow=(81.0 - 10.0 * stroke, 82.0),
            far_hand=(96.0 + 13.0 * stroke, 45.0),
            near_hand=(94.0 - 13.0 * stroke, 86.0),
            far_hip=(52.0, 63.0),
            near_hip=(52.0, 75.0),
            far_knee=(38.0, 58.0 + 5.0 * stroke),
            near_knee=(36.0, 78.0 - 5.0 * stroke),
            far_ankle=(22.0, 56.0 + 8.0 * stroke),
            near_ankle=(20.0, 82.0 - 8.0 * stroke),
            far_hand_mode="open",
            near_hand_mode="open",
            hair_lift=1.0,
            coat_flare=-8.0,
        )

    if animation == "block":
        amount = _pulse(t)
        return replace(
            pose,
            far_elbow=(51.0, 66.0),
            near_elbow=(76.0, 65.0),
            far_hand=(66.0, 60.0),
            near_hand=(73.0, 53.0),
            far_hand_mode="open",
            near_hand_mode="open",
            expression="determined",
            boundary=amount,
            effect_phase=t,
        )

    if animation == "hit":
        amount = _pulse(t)
        return replace(
            pose,
            root=(64.0 - 5.0 * amount, 1.5 * amount),
            root_angle=-12.0 * amount,
            head=(62.0 - 4.0 * amount, 31.0 + amount),
            far_elbow=(40.0, 73.0),
            near_elbow=(84.0, 72.0),
            far_hand=(36.0, 86.0),
            near_hand=(86.0, 87.0),
            expression="hurt",
            hair_lift=1.2 * amount,
            coat_flare=-4.0 * amount,
        )

    if animation == "death":
        amount = _smooth(t)
        angle = -60.0 * amount
        return replace(
            pose,
            root=(64.0 + 6.0 * amount, 0.0),
            root_angle=angle,
            head=(65.0, 31.0),
            far_elbow=(43.0, 72.0),
            near_elbow=(88.0, 74.0),
            far_hand=(36.0, 82.0),
            near_hand=(98.0, 83.0),
            far_knee=(51.0, 103.0),
            near_knee=(78.0, 103.0),
            far_ankle=(45.0, 116.0),
            near_ankle=(85.0, 116.0),
            expression="hurt",
            hair_lift=1.5 * amount,
            coat_flare=5.0 * amount,
        )

    if animation == "talk":
        gesture = math.sin(phase * math.tau)
        mouth_frames = ("talk_a", "talk_b", "talk_c", "talk_b")
        return replace(
            pose,
            near_elbow=(83.0 - 2.0 * gesture, 70.0 - 3.0 * abs(gesture)),
            near_hand=(91.0 + 2.0 * gesture, 65.0 - 4.0 * abs(gesture)),
            near_hand_mode="open",
            far_hand_mode="relaxed",
            expression=mouth_frames[frame_idx % len(mouth_frames)],
            hair_lift=0.18 * gesture,
        )

    if animation == "interact":
        reach = _pulse(t)
        return replace(
            pose,
            near_elbow=(87.0, 69.0 - 2.0 * reach),
            near_hand=(101.0 + 7.0 * reach, 66.0 - 2.0 * reach),
            near_hand_mode="open",
            expression="curious",
        )

    if animation == "geodesic_sweep":
        charge = _smooth(min(1.0, t * 1.7))
        release = _smooth(max(0.0, (t - 0.28) / 0.72))
        sweep = _lerp_point((88.0, 76.0), (99.0, 59.0), release)
        return replace(
            pose,
            root_angle=7.0 * release,
            far_elbow=(46.0, 70.0),
            far_hand=(39.0, 80.0),
            near_elbow=(86.0 + 5.0 * release, 70.0 - 7.0 * release),
            near_hand=sweep,
            near_hand_mode="open",
            expression="determined",
            hair_lift=0.8 * release,
            coat_flare=-5.0 * release,
            geodesic=max(charge * 0.45, release),
            effect_phase=t,
        )

    if animation == "boundary_fold":
        gather = _pulse(t)
        release = _smooth(max(0.0, (t - 0.45) / 0.55))
        return replace(
            pose,
            far_elbow=(50.0 - 6.0 * gather, 68.0),
            near_elbow=(78.0 + 7.0 * gather, 67.0),
            far_hand=(59.0 - 15.0 * gather, 61.0),
            near_hand=(71.0 + 20.0 * gather + 13.0 * release, 60.0 - 4.0 * release),
            far_hand_mode="open",
            near_hand_mode="open",
            expression="focused",
            boundary=max(gather, release),
            effect_phase=t,
            coat_flare=3.0 * gather,
        )

    if animation == "moduli_bloom":
        lift = _pulse(t)
        open_amount = _smooth(min(1.0, t * 1.4))
        return replace(
            pose,
            root=(64.0, -4.0 * lift),
            head=(64.0, 30.0 - 2.0 * lift),
            far_elbow=(47.0 - 6.0 * open_amount, 65.0 - 7.0 * open_amount),
            near_elbow=(81.0 + 7.0 * open_amount, 64.0 - 8.0 * open_amount),
            far_hand=(34.0 - 5.0 * open_amount, 58.0 - 10.0 * open_amount),
            near_hand=(96.0 + 6.0 * open_amount, 56.0 - 11.0 * open_amount),
            far_hand_mode="open",
            near_hand_mode="open",
            expression="delighted" if t > 0.45 else "focused",
            hair_lift=1.8 * lift,
            coat_flare=6.0 * open_amount,
            moduli=open_amount,
            effect_phase=t,
        )

    if animation == "celebrate":
        cheer = _pulse(t)
        return replace(
            pose,
            root=(64.0, -3.0 * cheer),
            far_elbow=(49.0, 53.0 - 5.0 * cheer),
            near_elbow=(80.0, 52.0 - 6.0 * cheer),
            far_hand=(42.0, 39.0 - 9.0 * cheer),
            near_hand=(89.0, 37.0 - 10.0 * cheer),
            far_hand_mode="open",
            near_hand_mode="open",
            expression="delighted",
            hair_lift=1.2 * cheer,
            coat_flare=2.0 * cheer,
        )

    if animation == "taunt":
        shrug = _pulse(t)
        return replace(
            pose,
            head=(64.0, 31.0 - shrug),
            head_angle=-4.0 + 7.0 * shrug,
            far_elbow=(48.0, 69.0 - 3.0 * shrug),
            near_elbow=(81.0, 68.0 - 3.0 * shrug),
            far_hand=(37.0, 63.0 - 6.0 * shrug),
            near_hand=(94.0, 61.0 - 6.0 * shrug),
            far_hand_mode="open",
            near_hand_mode="open",
            expression="wry",
        )

    raise KeyError(f"unknown Mami Marzakhani animation: {animation}")


def _transform(point: Point, pose: Pose) -> Point:
    if pose.root_angle:
        point = _rotate(point, (64.0, 78.0), pose.root_angle)
    return (point[0] + pose.root[0] - 64.0, point[1] + pose.root[1])


def _draw_hair_back(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    t = lambda q: _transform(q, pose)
    center = t((63.0, 34.0 - pose.hair_lift))
    # One connected mass gives the silhouette authority; layered curls add
    # texture without turning the hair into a collection of floating beads.
    mass = [
        t((45.0, 24.0 - pose.hair_lift)),
        t((51.0, 15.0 - pose.hair_lift)),
        t((63.0, 11.0 - pose.hair_lift)),
        t((76.0, 15.0 - pose.hair_lift)),
        t((84.0, 24.0 - pose.hair_lift)),
        t((85.0, 38.0 - pose.hair_lift)),
        t((80.0, 50.0 - pose.hair_lift * 0.6)),
        t((73.0, 57.0 - pose.hair_lift * 0.3)),
        t((56.0, 57.0 - pose.hair_lift * 0.3)),
        t((46.0, 49.0 - pose.hair_lift * 0.6)),
        t((42.0, 37.0 - pose.hair_lift)),
    ]
    _polygon(draw, mass, HAIR_DEEP, OUTLINE, 1.4)
    curl_specs = [
        (-15, -5, 6.8), (-8, -12, 7.2), (1, -14, 7.5), (10, -11, 7.4),
        (16, -4, 7.0), (-17, 5, 7.2), (-11, 13, 7.6), (-3, 17, 7.4),
        (6, 17, 7.0), (14, 12, 7.6), (18, 5, 6.8),
    ]
    for idx, (dx, dy, radius) in enumerate(curl_specs):
        fill = HAIR if idx % 3 else HAIR_MID
        _ellipse(draw, (center[0] + dx, center[1] + dy), radius, radius * 0.94, fill, OUTLINE, 0.75)
    # Warm, sparse gleams describe curl direction instead of a generic shine.
    for dx, dy, start, end in [
        (-11, -7, 196, 300), (-1, -11, 205, 305), (10, -7, 215, 315),
        (-13, 7, 195, 290), (2, 12, 210, 305), (13, 7, 220, 320),
    ]:
        _arc(draw, (center[0] + dx, center[1] + dy), 4.5, 4.0, start, end, HAIR_GLEAM, 0.8)


def _draw_leg(
    draw: ImageDraw.ImageDraw,
    pose: Pose,
    hip: Point,
    knee: Point,
    ankle: Point,
    *,
    far: bool,
) -> None:
    t = lambda q: _transform(q, pose)
    hip_t, knee_t, ankle_t = t(hip), t(knee), t(ankle)
    trouser = TROUSER_DARK if far else TROUSER
    trouser_hi = TROUSER if far else TROUSER_LIGHT
    _polygon(draw, _segment_quad(hip_t, knee_t, 5.0, 4.5), trouser, OUTLINE, 1.0)
    _polygon(draw, _segment_quad(knee_t, ankle_t, 4.5, 3.9), trouser, OUTLINE, 1.0)
    along, normal, _length = _unit(knee_t, ankle_t)
    _line(
        draw,
        [
            (knee_t[0] + normal[0] * 1.7, knee_t[1] + normal[1] * 1.7),
            (ankle_t[0] + normal[0] * 1.3, ankle_t[1] + normal[1] * 1.3),
        ],
        trouser_hi,
        0.8,
    )
    foot_dir = -1.0 if far else 1.0
    foot = [
        (ankle_t[0] - 4.2, ankle_t[1] - 2.2),
        (ankle_t[0] + foot_dir * 8.5, ankle_t[1] - 1.6),
        (ankle_t[0] + foot_dir * 10.0, ankle_t[1] + 3.6),
        (ankle_t[0] - 4.5, ankle_t[1] + 3.8),
    ]
    _polygon(draw, foot, SHOE if not far else OUTLINE_SOFT, OUTLINE, 1.0)
    _line(draw, [foot[2], foot[3]], SHOE_LIGHT, 0.8)


def _draw_coat(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    t = lambda q: _transform(q, pose)
    flare = pose.coat_flare
    shoulder_l = t((50.0, 57.0))
    shoulder_r = t((79.0, 56.0))
    waist_l = t((54.0, 83.0))
    waist_r = t((74.0, 83.0))
    hem_l = t((49.0 - flare * 0.20, 101.0))
    hem_m = t((65.0, 98.0))
    hem_r = t((82.0 + flare * 0.42, 104.0))
    body = [shoulder_l, shoulder_r, waist_r, hem_r, hem_m, hem_l, waist_l]
    _polygon(draw, body, GARNET, OUTLINE, 1.3)
    # Asymmetric overlapping lapels and long diagonal opening make the modern
    # jacket distinct from the game's existing white-dress silhouette.
    left_panel = [
        shoulder_l,
        t((63.0, 58.0)),
        t((65.0, 96.0)),
        hem_l,
        waist_l,
    ]
    _polygon(draw, left_panel, GARNET_DARK, OUTLINE_SOFT, 0.85)
    right_panel = [
        t((65.0, 58.0)),
        shoulder_r,
        waist_r,
        hem_r,
        t((68.0, 96.0)),
    ]
    _polygon(draw, right_panel, GARNET_LIGHT, OUTLINE_SOFT, 0.85)
    _line(draw, [t((64.0, 59.0)), t((68.0, 96.0))], IVORY_SHADE, 1.0)
    _line(draw, [t((57.0, 84.0)), t((51.0 - flare * 0.15, 98.0))], GARNET_LIGHT, 0.75)
    _line(draw, [t((73.0, 84.0)), t((79.0 + flare * 0.32, 100.0))], GARNET_DARK, 0.75)
    # Ivory collar and a narrow teal boundary-stitch accent.
    collar = [t((55.0, 57.0)), t((63.5, 63.5)), t((72.0, 56.5)), t((68.0, 52.5)), t((61.0, 52.5))]
    _polygon(draw, collar, IVORY, OUTLINE, 0.85)
    _line(draw, [t((57.0, 60.0)), t((64.0, 66.0)), t((72.0, 58.5))], TEAL_LIGHT, 0.9)


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
    t = lambda q: _transform(q, pose)
    s, e, h = t(shoulder), t(elbow), t(hand)
    sleeve = GARNET_DARK if far else GARNET
    sleeve_hi = GARNET if far else GARNET_LIGHT
    _polygon(draw, _segment_quad(s, e, 5.2, 4.4), sleeve, OUTLINE, 1.0)
    fore_end = _lerp_point(e, h, 0.75)
    _polygon(draw, _segment_quad(e, fore_end, 4.4, 3.7), sleeve, OUTLINE, 1.0)
    along, normal, _length = _unit(e, fore_end)
    _line(
        draw,
        [
            (e[0] + normal[0] * 1.6, e[1] + normal[1] * 1.6),
            (fore_end[0] + normal[0] * 1.2, fore_end[1] + normal[1] * 1.2),
        ],
        sleeve_hi,
        0.75,
    )
    _line(draw, [
        (fore_end[0] - normal[0] * 3.1, fore_end[1] - normal[1] * 3.1),
        (fore_end[0] + normal[0] * 3.1, fore_end[1] + normal[1] * 3.1),
    ], IVORY, 1.25)
    _draw_hand(draw, h, mode, far=far)


def _draw_hand(draw: ImageDraw.ImageDraw, hand: Point, mode: str, *, far: bool) -> None:
    skin = SKIN_SHADE if far else SKIN
    if mode == "fist":
        _ellipse(draw, hand, 4.1, 4.0, skin, OUTLINE, 0.9)
        _line(draw, [(hand[0] - 2.2, hand[1]), (hand[0] + 2.0, hand[1] + 0.3)], SKIN_LIGHT, 0.65)
        return
    if mode == "grip":
        _ellipse(draw, hand, 3.8, 4.5, skin, OUTLINE, 0.9)
        _arc(draw, hand, 2.2, 2.5, 210, 30, SKIN_LIGHT, 0.65)
        return
    palm = hand
    _ellipse(draw, palm, 3.6, 4.0, skin, OUTLINE, 0.85)
    if mode == "open":
        for angle, length in [(-48, 4.5), (-24, 5.0), (0, 5.2), (22, 4.7)]:
            radians = math.radians(angle)
            tip = (palm[0] + math.cos(radians) * length, palm[1] - 2.0 + math.sin(radians) * length)
            _line(draw, [(palm[0] + 0.4, palm[1] - 1.5), tip], skin, 1.25)
            _line(draw, [tip, tip], OUTLINE, 0.45)
    else:
        _arc(draw, palm, 2.2, 2.4, 20, 155, SKIN_LIGHT, 0.6)


def _draw_neck_and_face(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    t = lambda q: _transform(q, pose)
    neck = [t((59.0, 46.0)), t((69.0, 46.0)), t((70.0, 58.0)), t((58.0, 58.0))]
    _polygon(draw, neck, SKIN_SHADE, OUTLINE, 0.9)
    _line(draw, [t((61.0, 49.0)), t((61.0, 56.0))], SKIN_LIGHT, 0.7)

    center = t(pose.head)
    # A softly angular three-quarter face with a recognizable long nose.
    face = [
        (center[0] - 12.5, center[1] - 13.0),
        (center[0] + 7.5, center[1] - 14.0),
        (center[0] + 14.0, center[1] - 6.0),
        (center[0] + 13.0, center[1] + 8.0),
        (center[0] + 5.5, center[1] + 15.5),
        (center[0] - 3.5, center[1] + 16.5),
        (center[0] - 12.0, center[1] + 9.0),
        (center[0] - 14.0, center[1] - 2.0),
    ]
    if pose.head_angle:
        face = [_rotate(p, center, pose.head_angle) for p in face]
    _polygon(draw, face, SKIN, OUTLINE, 1.15)
    ear = _rotate((center[0] - 13.0, center[1] + 1.0), center, pose.head_angle)
    _ellipse(draw, ear, 3.2, 4.7, SKIN_SHADE, OUTLINE, 0.8)
    _arc(draw, ear, 1.5, 2.5, 245, 100, SKIN_LIGHT, 0.55)

    def hp(local: Point) -> Point:
        return _rotate((center[0] + local[0], center[1] + local[1]), center, pose.head_angle)

    # Brows are not mirrored: the far brow is shorter, preserving the 3/4 view.
    _line(draw, [hp((-8.5, -4.4)), hp((-2.2, -5.0))], BROW, 1.25)
    _line(draw, [hp((2.0, -5.2)), hp((9.0, -4.3))], BROW, 1.35)
    _line(draw, [hp((-7.8, -1.9)), hp((-2.2, -1.8))], OUTLINE, 0.85)
    _line(draw, [hp((2.6, -2.1)), hp((9.0, -1.8))], OUTLINE, 0.9)
    _ellipse(draw, hp((-4.8, -1.7)), 2.25, 1.15, IVORY, OUTLINE, 0.35)
    _ellipse(draw, hp((5.7, -1.9)), 2.55, 1.25, IVORY, OUTLINE, 0.35)
    _ellipse(draw, hp((-4.3, -1.6)), 0.58, 0.72, EYE, None)
    _ellipse(draw, hp((5.4, -1.8)), 0.64, 0.78, EYE, None)
    # Long nose: bridge and a small warm underside.
    _line(draw, [hp((0.3, -1.0)), hp((1.2, 5.8)), hp((4.1, 6.7))], SKIN_SHADE, 0.95)
    _line(draw, [hp((1.7, 0.0)), hp((2.2, 4.2))], SKIN_LIGHT, 0.65)
    _arc(draw, hp((4.2, 6.0)), 2.5, 1.2, 155, 310, SKIN_WARM, 0.65)

    expression = pose.expression
    if expression in {"talk_a", "talk_b", "talk_c"}:
        heights = {"talk_a": 1.2, "talk_b": 2.1, "talk_c": 2.8}
        ry = heights[expression]
        _ellipse(draw, hp((1.6, 10.4)), 3.9, ry, MOUTH, OUTLINE, 0.55)
        if ry > 1.8:
            _line(draw, [hp((-0.7, 9.8)), hp((3.7, 9.8))], LIP_LIGHT, 0.55)
    elif expression == "delighted":
        _arc(draw, hp((1.2, 8.7)), 5.2, 4.2, 22, 158, MOUTH, 1.0)
        _line(draw, [hp((-2.4, 10.2)), hp((4.8, 10.5))], LIP_LIGHT, 0.5)
    elif expression == "hurt":
        _arc(draw, hp((1.5, 12.2)), 4.5, 3.4, 205, 335, MOUTH, 0.95)
    elif expression == "wry":
        _line(draw, [hp((-2.0, 10.5)), hp((1.0, 10.8)), hp((5.4, 9.6))], MOUTH, 0.9)
    elif expression == "curious":
        _ellipse(draw, hp((1.4, 10.5)), 2.2, 1.4, MOUTH, OUTLINE, 0.45)
    else:
        _line(draw, [hp((-2.4, 10.2)), hp((1.4, 10.6)), hp((5.0, 10.0))], MOUTH, 0.8)

    # Foreground curls overlap the face and shoulder to make the hair feel like
    # one three-dimensional volume rather than a helmet.
    for dx, dy, radius in [(-12.5, -9.0, 5.6), (-14.5, 0.0, 5.7), (-12.5, 10.0, 5.5), (11.5, -10.0, 5.3), (13.2, 0.5, 5.6), (10.5, 11.0, 5.2)]:
        c = hp((dx, dy))
        _ellipse(draw, c, radius, radius * 0.92, HAIR, OUTLINE, 0.75)
        _arc(draw, c, radius * 0.52, radius * 0.46, 205, 315, HAIR_GLEAM, 0.65)


def _draw_effects_behind(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    t = lambda q: _transform(q, pose)
    if pose.boundary > 0.02:
        center = t((67.0, 69.0))
        alpha = pose.boundary
        for idx, (rx, ry) in enumerate([(27, 34), (32, 40), (37, 46)]):
            phase = pose.effect_phase * 80.0 + idx * 17.0
            _arc(draw, center, rx, ry, 195 + phase, 342 + phase, _fade(BOUNDARY, alpha * (0.85 - idx * 0.15)), 1.4 - idx * 0.18)
    if pose.moduli > 0.02:
        center = t((64.0, 63.0))
        growth = pose.moduli
        for idx in range(5):
            angle = pose.effect_phase * math.tau + idx * math.tau / 5.0
            radius = 14.0 + 12.0 * growth
            c = (center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius * 0.72)
            _ellipse(draw, c, 3.0 + 2.3 * growth, 2.2 + 1.8 * growth, _fade(MODULI, 0.30 * growth), _fade(MODULI_LIGHT, 0.78 * growth), 0.8)


def _draw_effects_front(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    t = lambda q: _transform(q, pose)
    if pose.geodesic > 0.02:
        hand = t(pose.near_hand)
        amount = pose.geodesic
        center = (hand[0] - 5.0, hand[1] + 12.0)
        start = 194.0 - 30.0 * amount
        end = 345.0 + 50.0 * amount
        _arc(draw, center, 20.0 + 5.0 * amount, 18.0 + 4.0 * amount, start, end, _fade(GEODESIC, amount), 2.1)
        _arc(draw, center, 17.0 + 4.0 * amount, 14.0 + 3.0 * amount, start + 8.0, end - 4.0, _fade(GEODESIC_LIGHT, amount * 0.85), 0.85)
        for marker in (0.18, 0.52, 0.82):
            angle = math.radians(_lerp(start, end, marker))
            p = (center[0] + math.cos(angle) * (20.0 + 5.0 * amount), center[1] + math.sin(angle) * (18.0 + 4.0 * amount))
            _ellipse(draw, p, 1.6, 1.6, _fade(GEODESIC_LIGHT, amount), OUTLINE_SOFT, 0.4)
    if pose.boundary > 0.18:
        hand = t(pose.near_hand)
        _line(draw, [hand, (hand[0] + 17.0 * pose.boundary, hand[1] - 3.0)], _fade(BOUNDARY_LIGHT, pose.boundary), 1.6)
    if pose.moduli > 0.30:
        center = t((64.0, 63.0))
        _arc(draw, center, 18.0 + 11.0 * pose.moduli, 22.0 + 10.0 * pose.moduli, 200, 520, _fade(MODULI_LIGHT, pose.moduli * 0.68), 1.0)


def _render_native_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose(animation, frame_idx, nframes)
    image = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    draw = blending_draw(image)

    _draw_effects_behind(draw, pose)
    _draw_hair_back(draw, pose)
    _draw_leg(draw, pose, pose.far_hip, pose.far_knee, pose.far_ankle, far=True)
    _draw_leg(draw, pose, pose.near_hip, pose.near_knee, pose.near_ankle, far=False)
    _draw_coat(draw, pose)
    _draw_arm(draw, pose, pose.far_shoulder, pose.far_elbow, pose.far_hand, pose.far_hand_mode, far=True)
    _draw_arm(draw, pose, pose.near_shoulder, pose.near_elbow, pose.near_hand, pose.near_hand_mode, far=False)
    _draw_effects_front(draw, pose)
    _draw_neck_and_face(draw, pose)
    return image


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _render_native_frame(animation, frame_idx, nframes).resize(
        (FRAME_W, FRAME_H), Image.Resampling.LANCZOS
    )


# ---------------------------------------------------------------------------
# Bespoke native portrait renderer

PORTRAIT_W = 256
PORTRAIT_H = 320
PORTRAIT_SUPER = 4


def _portrait_scale(point: Point) -> Point:
    return (point[0] * PORTRAIT_SUPER, point[1] * PORTRAIT_SUPER)


def _portrait_box(center: Point, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (
        int(round((center[0] - rx) * PORTRAIT_SUPER)),
        int(round((center[1] - ry) * PORTRAIT_SUPER)),
        int(round((center[0] + rx) * PORTRAIT_SUPER)),
        int(round((center[1] + ry) * PORTRAIT_SUPER)),
    )


def _portrait_poly(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.0) -> None:
    pts = [_portrait_scale(p) for p in points]
    draw.polygon(pts, fill=fill)
    draw.line(pts + [pts[0]], fill=outline, width=max(1, int(round(width * PORTRAIT_SUPER))), joint="curve")


def _portrait_line(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, width: float) -> None:
    draw.line([_portrait_scale(p) for p in points], fill=fill, width=max(1, int(round(width * PORTRAIT_SUPER))), joint="curve")


def _portrait_ellipse(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, fill: RGBA, outline: RGBA | None = OUTLINE, width: float = 1.0) -> None:
    draw.ellipse(
        _portrait_box(center, rx, ry),
        fill=fill,
        outline=outline,
        width=max(1, int(round(width * PORTRAIT_SUPER))) if outline is not None else 1,
    )


def _portrait_arc(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, start: float, end: float, fill: RGBA, width: float) -> None:
    draw.arc(_portrait_box(center, rx, ry), start=start, end=end, fill=fill, width=max(1, int(round(width * PORTRAIT_SUPER))))


def _portrait_expression_frame(expression: str, frame_idx: int = 0, nframes: int = 1) -> Image.Image:
    phase = frame_idx / max(1, nframes)
    gesture = math.sin(phase * math.tau)
    image = Image.new("RGBA", (PORTRAIT_W * PORTRAIT_SUPER, PORTRAIT_H * PORTRAIT_SUPER), (0, 0, 0, 0))
    draw = blending_draw(image)

    # Shoulders and long jacket.  The portrait is authored directly at this
    # scale and contains details that do not exist in the gameplay render.
    shoulder_y = 236.0
    jacket = [
        (28.0, 320.0), (38.0, 264.0), (76.0, shoulder_y), (122.0, 230.0),
        (170.0, shoulder_y - 2.0), (218.0, 263.0), (230.0, 320.0),
    ]
    _portrait_poly(draw, jacket, GARNET, OUTLINE, 2.4)
    _portrait_poly(draw, [(28, 320), (38, 264), (86, 237), (126, 320)], GARNET_DARK, OUTLINE_SOFT, 1.4)
    _portrait_poly(draw, [(122, 230), (170, 234), (218, 263), (230, 320), (126, 320)], GARNET_LIGHT, OUTLINE_SOFT, 1.4)
    _portrait_line(draw, [(122, 232), (132, 320)], IVORY_SHADE, 2.0)
    _portrait_poly(draw, [(83, 238), (118, 263), (157, 235), (145, 214), (104, 214)], IVORY, OUTLINE, 1.8)
    _portrait_line(draw, [(92, 239), (120, 265), (153, 237)], TEAL_LIGHT, 2.0)

    # Hair mass behind the head: deliberately asymmetric, with more volume on
    # screen-left and a few curls extending over the jacket.
    hair_mass = [
        (50, 76), (61, 41), (90, 18), (128, 12), (165, 23), (193, 52),
        (205, 92), (201, 142), (187, 188), (169, 226), (137, 246),
        (91, 239), (61, 214), (39, 178), (31, 128),
    ]
    _portrait_poly(draw, hair_mass, HAIR_DEEP, OUTLINE, 2.8)
    portrait_curls = [
        (61, 72, 22), (79, 43, 23), (110, 31, 24), (142, 34, 25),
        (172, 52, 24), (191, 82, 22), (48, 104, 24), (54, 140, 25),
        (64, 176, 25), (83, 207, 26), (113, 222, 25), (148, 216, 25),
        (177, 188, 24), (192, 154, 24), (199, 118, 23),
    ]
    for idx, (cx, cy, radius) in enumerate(portrait_curls):
        fill = HAIR if idx % 4 else HAIR_MID
        _portrait_ellipse(draw, (cx, cy), radius, radius * 0.92, fill, OUTLINE, 1.25)
        if idx % 2 == 0:
            _portrait_arc(draw, (cx - 1, cy - 1), radius * 0.58, radius * 0.50, 205, 315, HAIR_GLEAM, 1.5)

    # Neck and three-quarter face.
    _portrait_poly(draw, [(102, 194), (148, 193), (154, 239), (94, 240)], SKIN_SHADE, OUTLINE, 1.8)
    _portrait_line(draw, [(111, 200), (110, 233)], SKIN_LIGHT, 1.5)
    face = [
        (83, 73), (121, 55), (160, 65), (181, 96), (179, 144),
        (163, 181), (132, 203), (101, 194), (76, 164), (66, 120),
    ]
    _portrait_poly(draw, face, SKIN, OUTLINE, 2.6)
    _portrait_ellipse(draw, (69, 127), 12, 20, SKIN_SHADE, OUTLINE, 1.7)
    _portrait_arc(draw, (70, 127), 6, 11, 235, 105, SKIN_LIGHT, 1.3)

    # Hairline and foreground curls.
    _portrait_poly(draw, [(78, 91), (83, 67), (113, 52), (151, 59), (177, 83), (164, 90), (146, 81), (125, 78), (105, 86)], HAIR, OUTLINE, 1.7)
    for cx, cy, radius in [(75, 83, 18), (71, 113, 20), (76, 151, 20), (169, 78, 18), (183, 112, 20), (179, 151, 19), (164, 181, 18)]:
        _portrait_ellipse(draw, (cx, cy), radius, radius * 0.92, HAIR, OUTLINE, 1.25)
        _portrait_arc(draw, (cx, cy), radius * 0.54, radius * 0.48, 205, 315, HAIR_GLEAM, 1.25)

    # Brows, eyes, and eyelids.  Fine highlights make the portrait more alive
    # while preserving the game's graphic outline style.
    brow_raise = 2.0 if expression == "curious" else 0.0
    _portrait_line(draw, [(91, 107 - brow_raise), (112, 102 - brow_raise)], BROW, 3.0)
    _portrait_line(draw, [(131, 101), (159, 105)], BROW, 3.3)
    _portrait_line(draw, [(92, 116), (112, 115)], OUTLINE, 2.1)
    _portrait_line(draw, [(132, 114), (160, 116)], OUTLINE, 2.3)
    _portrait_ellipse(draw, (102, 116), 9.0, 4.8, IVORY, OUTLINE, 0.9)
    _portrait_ellipse(draw, (146, 116), 10.0, 5.0, IVORY, OUTLINE, 0.9)
    eye_shift = 1.0 * gesture if expression == "thinking" else 0.0
    _portrait_ellipse(draw, (103 + eye_shift, 116), 3.0, 3.4, EYE, None)
    _portrait_ellipse(draw, (145 + eye_shift, 116), 3.2, 3.6, EYE, None)
    _portrait_ellipse(draw, (104 + eye_shift, 114.7), 0.9, 1.1, (255, 255, 244, 255), None)
    _portrait_ellipse(draw, (146 + eye_shift, 114.7), 0.9, 1.1, (255, 255, 244, 255), None)

    # Long nose and a quiet warm cheek plane.
    _portrait_line(draw, [(122, 118), (126, 148), (139, 153)], SKIN_SHADE, 2.3)
    _portrait_line(draw, [(128, 121), (131, 143)], SKIN_LIGHT, 1.6)
    _portrait_arc(draw, (140, 150), 9, 5, 150, 310, SKIN_WARM, 1.4)
    _portrait_arc(draw, (154, 143), 12, 18, 80, 168, _fade(SKIN_WARM, 0.55), 2.2)

    if expression == "speaking":
        mouth_cycle = frame_idx % 4
        ry = (3.0, 6.5, 9.0, 5.0)[mouth_cycle]
        _portrait_ellipse(draw, (128, 172), 12.5, ry, MOUTH, OUTLINE, 1.5)
        if ry >= 5.0:
            _portrait_line(draw, [(119, 170), (136, 170)], LIP_LIGHT, 1.3)
    elif expression == "delighted":
        _portrait_arc(draw, (128, 162), 17, 15, 20, 160, MOUTH, 2.5)
        _portrait_line(draw, [(117, 174), (139, 174)], LIP_LIGHT, 1.2)
    elif expression == "thinking":
        _portrait_line(draw, [(115, 171), (128, 173), (142, 169)], MOUTH, 2.0)
    else:
        _portrait_line(draw, [(115, 170), (128, 172), (141, 169)], MOUTH, 2.0)

    # A portrait-only hand gesture enters from the side during explanation.
    if expression == "speaking":
        hand_y = 245.0 - 7.0 * abs(gesture)
        _portrait_poly(draw, [(205, 320), (190, 276), (198, 248), (217, 253), (235, 291), (244, 320)], GARNET, OUTLINE, 2.0)
        _portrait_poly(draw, [(196, 263), (210, 261), (208, hand_y + 7), (194, hand_y + 8)], SKIN, OUTLINE, 1.2)
        _portrait_ellipse(draw, (198, hand_y), 14, 16, SKIN, OUTLINE, 1.5)
        for idx, angle in enumerate((-58, -32, -7, 18)):
            length = 22.0 - idx * 1.5
            radians = math.radians(angle)
            tip = (198 + math.cos(radians) * length, hand_y - 7 + math.sin(radians) * length)
            _portrait_line(draw, [(198, hand_y - 6), tip], SKIN, 4.1)
            _portrait_ellipse(draw, tip, 2.1, 2.1, SKIN, OUTLINE, 0.7)

    return image.resize((PORTRAIT_W, PORTRAIT_H), Image.Resampling.LANCZOS)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    """Publish independent native-resolution expression art."""
    del opts
    clips = {
        "default": PortraitClip.still(_portrait_expression_frame("default")),
        "explaining": PortraitClip(
            tuple(_portrait_expression_frame("speaking", idx, 8) for idx in range(8)),
            duration_ms=104,
            looping=True,
        ),
        "thinking": PortraitClip(
            tuple(_portrait_expression_frame("thinking", idx, 6) for idx in range(6)),
            duration_ms=128,
            looping=True,
        ),
        "delighted": PortraitClip.still(_portrait_expression_frame("delighted")),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {
            "x": int(fw * 0.28),
            "y": int(fh * 0.07),
            "w": int(fw * 0.49),
            "h": int(fh * 0.87),
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
            "geodesic_sweep": {"bbox": {"x": 76, "y": 35, "w": 50, "h": 60}},
            "boundary_fold": {"bbox": {"x": 79, "y": 38, "w": 47, "h": 50}},
            "moduli_bloom": {"bbox": {"x": 25, "y": 22, "w": 81, "h": 88}},
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


def source_uses_forbidden_raster_effects() -> bool:
    """The target uses only explicit geometry and LANCZOS downsampling."""
    return False



__all__ = [
    "ACTOR_METADATA",
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
