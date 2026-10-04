"""Bespoke procedural full-action sprite target for Vera Ruin.

Vera Ruin is a parody of astronomer Vera Rubin, built around the observational
case for unseen mass in spiral galaxies.  This renderer is a fresh construction:
it does not inherit another character renderer, copy another character's pose
function, or use the generic toon family.

The visual identity is an older field astronomer wearing a sharply asymmetric
observatory coat.  A segmented spectrograph halo is mounted behind her shoulders;
three calibration lights travel around it and make the otherwise invisible halo
read at sprite scale.  Her short silver bob, round optics, brass eyepiece, broad
ring silhouette, and star-map coat lining keep her distinct from every existing
mathematician sprite.

The attack language is observational rather than wizardly: flat rotation-curve
data, split spectra, gravitational-lensing arcs, and counter-rotating orbits.  No
held weapon, floor ellipse, cast shadow, blur, or generated-image input is used.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import PortraitClip, write_portrait_sheet
from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw

from . import _solo_shape_rig as SR

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "vera_ruin"
FRAME_W = 192
FRAME_H = 192
SUPER = 4
USES_PROPS = False
USES_DROP_SHADOW = False

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 145),
    ("walk", 8, 104),
    ("run", 8, 76),
    ("crouch", 6, 94),
    ("crouch_walk", 8, 88),
    ("jump", 6, 88),
    ("fall", 6, 90),
    ("land_hard", 7, 82),
    ("dash_startup", 4, 52),
    ("dash", 6, 60),
    ("slide", 6, 68),
    ("roll", 8, 58),
    ("wall_grab", 6, 104),
    ("wall_jump", 6, 82),
    ("ledge_grab", 6, 98),
    ("ledge_climb", 6, 94),
    ("climb", 8, 98),
    ("swim", 8, 102),
    ("block", 6, 82),
    ("hit", 5, 84),
    ("death", 8, 108),
    ("talk", 8, 104),
    ("interact", 8, 92),
    ("jab", 5, 56),
    ("curve_cut", 8, 66),
    ("air_neutral", 8, 62),
    ("air_forward", 7, 60),
    ("air_up", 7, 60),
    ("air_down", 7, 66),
    ("spectral_lens", 9, 72),
    ("halo_reveal", 10, 78),
    ("counter_rotation", 10, 72),
    ("celebrate", 8, 88),
    ("taunt", 8, 94),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_vera_ruin",
        "display_name": "Vera Ruin",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Compact",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "scientist",
            "astronomer",
            "dark_matter_hunter",
            "spectrograph_duelist",
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
                "center": {"x": 96.0, "y": 49.0},
                "size": {"width": 38.0, "height": 40.0},
                "source_size": {"width": FRAME_W, "height": FRAME_H},
            }
        },
    },
    "tags": [
        "story",
        "humanoid",
        "scientist",
        "astronomer",
        "dark_matter_hunter",
        "spectrograph_duelist",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.vera_ruin", "point": {"x": 96.0, "y": 49.0}},
        "chest": {"source": "explicit.vera_ruin", "point": {"x": 96.0, "y": 91.0}},
        "hand_l": {"source": "explicit.vera_ruin", "point": {"x": 73.0, "y": 108.0}},
        "hand_r": {"source": "explicit.vera_ruin", "point": {"x": 122.0, "y": 104.0}},
        "speech_bubble": {"source": "explicit.vera_ruin", "point": {"x": 96.0, "y": 8.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "curve_cut", "events": []},
        "action.ranged.primary": {"animation": "spectral_lens", "events": []},
        "action.special.primary": {"animation": "halo_reveal", "events": []},
        "action.special.secondary": {"animation": "counter_rotation", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "authoring_description": (
        "Vera Ruin parodies astronomer Vera Rubin. Rubin's measurements of spiral-galaxy "
        "rotation curves helped establish the observational case for large quantities of "
        "unseen mass. The name turns Rubin into 'Ruin' because this character calmly ruins "
        "bad cosmological models by showing that their visible mass cannot explain the motion. "
        "Her sprite is intentionally an older human astronomer rather than a generic cosmic "
        "sorcerer. The segmented halo is a wearable spectrograph and calibration rig, not a "
        "magic circle. Its moving lamps reference measured velocity points, while the star-map "
        "lining and antique-globe nodes nod to Rubin's lifelong observational interests. The "
        "short silver bob, round glasses, brass eyepiece, asymmetric coat, and wide ring silhouette "
        "are the non-negotiable visual identifiers."
    ),
    "gameplay_description": (
        "A technical mid-range control fighter who exposes hidden structure. Curve Cut traces a "
        "flat velocity curve into a close horizontal strike. Spectral Lens separates a narrow beam "
        "into red and cyan channels and bends it around the spectrograph ring. Halo Reveal expands "
        "the rig into a circular denial field marked by observed data points. Counter Rotation "
        "creates two opposed orbital bands that redirect momentum. Her attacks should be crisp, "
        "measured, and diagrammatic, with modest startup and strong positional reward rather than "
        "large explosive effects."
    ),
    "suggested_barks": [
        "The curve stays flat.",
        "Unseen is not unmeasured.",
        "Your model is missing most of the mass.",
        "Motion first. Explanation second.",
        "The halo is not optional.",
        "Observation ruins another elegant guess.",
        "Counter-rotation confirmed.",
    ],
    "fallback_dialogue": [
        "Most people watch the light. I watch what the light is forced to do.",
        "A galaxy may be beautiful, but it still has to balance its books.",
        "Invisible matter is inconvenient only if you insist that seeing is the same as measuring.",
        "The outer stars did not slow down merely because the prevailing theory expected them to.",
        "I am not trying to ruin the model. The data arrived that way.",
        "When two components rotate in opposite directions, the history becomes much more interesting.",
    ],
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "gpt_5_6_thinking_spectrograph_halo_v3_2026_07_26",
        "lineage": [
            {
                "revision_id": "vera_ruin_name_and_dark_matter_direction",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "contribution": "character_name_and_dark_matter_parody_direction",
            },
            {
                "revision_id": "vera_ruin_spectrograph_halo_renderer_v3",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "parent_revision_id": "vera_ruin_name_and_dark_matter_direction",
                "contribution": "from_scratch_silhouette_pose_renderer_effects_portraits_and_authoring_metadata",
            },
        ],
    },
}

# Observatory palette: teal-black coat, plum lining, brass optics, and split
# spectrum effects. It intentionally avoids the blue/garnet palettes of the
# existing mathematician sprites.
OUTLINE = (12, 15, 20, 255)
OUTLINE_SOFT = (38, 45, 52, 255)
SKIN = (202, 158, 126, 255)
SKIN_LIGHT = (235, 195, 159, 255)
SKIN_SHADE = (154, 109, 88, 255)
HAIR = (100, 105, 112, 255)
HAIR_LIGHT = (172, 178, 184, 255)
HAIR_DARK = (54, 58, 65, 255)
COAT = (24, 71, 75, 255)
COAT_LIGHT = (43, 105, 106, 255)
COAT_DARK = (15, 42, 48, 255)
COAT_DEEP = (10, 26, 33, 255)
LINING = (80, 42, 94, 255)
LINING_LIGHT = (126, 70, 137, 255)
BLOUSE = (222, 212, 193, 255)
BLOUSE_SHADE = (181, 169, 150, 255)
BRASS = (205, 150, 67, 255)
BRASS_LIGHT = (244, 201, 113, 255)
BRASS_DARK = (133, 88, 34, 255)
TROUSER = (39, 42, 49, 255)
TROUSER_LIGHT = (65, 68, 77, 255)
BOOT = (27, 30, 35, 255)
EYE = (34, 27, 25, 255)
GLASS = (193, 232, 232, 50)
MOUTH = (129, 67, 69, 255)
CYAN = (97, 225, 229, 255)
CYAN_SOFT = (97, 225, 229, 82)
MAGENTA = (222, 96, 184, 255)
MAGENTA_SOFT = (222, 96, 184, 72)
GOLD = (247, 207, 104, 255)
RED = (230, 94, 95, 255)
STAR = (241, 239, 211, 255)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smooth(value: float) -> float:
    value = _clamp01(value)
    return value * value * (3.0 - 2.0 * value)


def _pulse(value: float) -> float:
    return math.sin(_clamp01(value) * math.pi)


def _lerp(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def _lp(a: Point, b: Point, amount: float) -> Point:
    return (_lerp(a[0], b[0], amount), _lerp(a[1], b[1], amount))


def _add(point: Point, dx: float, dy: float) -> Point:
    return (point[0] + dx, point[1] + dy)


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


def _poly(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.3,
) -> None:
    pts = [_pt(point) for point in points]
    draw.polygon(pts, fill=fill)
    if outline and len(pts) > 1:
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
    width: float = 1.2,
) -> None:
    draw.ellipse(_box(center, rx, ry), fill=fill, outline=outline, width=_s(width) if outline else 1)


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


def _capsule(
    draw: ImageDraw.ImageDraw,
    start: Point,
    end: Point,
    radius: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
) -> None:
    _line(draw, [start, end], outline, radius * 2.0 + 2.2)
    _ellipse(draw, start, radius + 1.1, radius + 1.1, outline, None)
    _ellipse(draw, end, radius + 1.1, radius + 1.1, outline, None)
    _line(draw, [start, end], fill, radius * 2.0)
    _ellipse(draw, start, radius, radius, fill, None)
    _ellipse(draw, end, radius, radius, fill, None)


@dataclass
class Pose:
    head: Point = (96.0, 47.0)
    neck: Point = (96.0, 64.0)
    far_shoulder: Point = (80.0, 73.0)
    near_shoulder: Point = (112.0, 70.0)
    far_elbow: Point = (74.0, 91.0)
    near_elbow: Point = (121.0, 89.0)
    far_hand: Point = (77.0, 109.0)
    near_hand: Point = (120.0, 108.0)
    far_hip: Point = (87.0, 119.0)
    near_hip: Point = (106.0, 118.0)
    far_knee: Point = (84.0, 143.0)
    near_knee: Point = (109.0, 143.0)
    far_ankle: Point = (82.0, 169.0)
    near_ankle: Point = (113.0, 169.0)
    root_x: float = 0.0
    root_y: float = 0.0
    body_angle: float = 0.0
    head_tilt: float = 0.0
    crouch: float = 0.0
    coat_flare: float = 0.0
    ring_phase: float = 0.0
    ring_scale: float = 1.0
    ring_front: float = 1.0
    mouth: float = 0.0
    smile: float = 0.0
    blink: float = 0.0
    brow: float = 0.0
    block: float = 0.0
    hurt: float = 0.0
    defeat: float = 0.0
    curve: float = 0.0
    lens: float = 0.0
    halo: float = 0.0
    counter: float = 0.0
    spectrum: float = 0.0
    starfield: float = 0.0
    glint: float = 0.0


PIVOT = (96.0, 119.0)


def _xf(point: Point, pose: Pose) -> Point:
    angle = math.radians(pose.body_angle)
    dx = point[0] - PIVOT[0]
    dy = point[1] - PIVOT[1]
    ca = math.cos(angle)
    sa = math.sin(angle)
    return (
        PIVOT[0] + dx * ca - dy * sa + pose.root_x,
        PIVOT[1] + dx * sa + dy * ca + pose.root_y,
    )


def _shift_upper(pose: Pose, dy: float) -> None:
    for name in (
        "head",
        "neck",
        "far_shoulder",
        "near_shoulder",
        "far_elbow",
        "near_elbow",
        "far_hand",
        "near_hand",
        "far_hip",
        "near_hip",
        "far_knee",
        "near_knee",
    ):
        point = getattr(pose, name)
        setattr(pose, name, (point[0], point[1] + dy))


def _pose(animation: str, frame_idx: int, frame_count: int) -> Pose:
    p = Pose()
    t = 0.0 if frame_count <= 1 else frame_idx / float(frame_count - 1)
    wave = math.sin(t * math.tau)
    cwave = math.cos(t * math.tau)
    p.ring_phase = t

    if animation == "idle":
        breath = math.sin(t * math.tau * 2.0)
        p.root_y = -0.8 * abs(breath)
        p.head_tilt = wave * 1.2
        p.near_hand = _add(p.near_hand, -1.0, breath * 1.2)
        p.far_hand = _add(p.far_hand, 1.0, -breath * 0.8)
        p.blink = 1.0 if frame_idx == frame_count // 2 else 0.0
        p.glint = max(0.0, math.sin((t - 0.15) * math.pi * 2.0)) * 0.4
        p.starfield = 0.18

    elif animation in {"walk", "run"}:
        amp = 14.0 if animation == "walk" else 22.0
        bounce = (1.0 - math.cos(t * math.tau * 2.0)) * (0.9 if animation == "walk" else 1.5)
        p.root_y = bounce
        p.body_angle = -2.0 - wave * (2.0 if animation == "walk" else 4.0)
        p.near_ankle = _add(p.near_ankle, wave * amp, -abs(wave) * 3.0)
        p.far_ankle = _add(p.far_ankle, -wave * amp, -abs(wave) * 3.0)
        p.near_knee = _add(p.near_knee, wave * amp * 0.45, -max(0.0, wave) * 4.0)
        p.far_knee = _add(p.far_knee, -wave * amp * 0.45, -max(0.0, -wave) * 4.0)
        arm = 11.0 if animation == "walk" else 17.0
        p.near_elbow = _add(p.near_elbow, -wave * arm * 0.55, wave * 2.0)
        p.near_hand = _add(p.near_hand, -wave * arm, wave * 2.0)
        p.far_elbow = _add(p.far_elbow, wave * arm * 0.55, -wave * 2.0)
        p.far_hand = _add(p.far_hand, wave * arm, -wave * 2.0)
        p.coat_flare = abs(wave) * (0.55 if animation == "walk" else 1.0)
        p.ring_phase = t * (1.2 if animation == "walk" else 2.0)

    elif animation == "crouch":
        p.crouch = _smooth(t if t < 0.5 else 1.0 - t) * 1.2 + 0.65
        _shift_upper(p, 15.0)
        p.near_knee = (113.0, 149.0)
        p.far_knee = (80.0, 149.0)
        p.near_ankle = (123.0, 168.0)
        p.far_ankle = (73.0, 168.0)
        p.ring_scale = 0.92

    elif animation == "crouch_walk":
        stride = wave
        _shift_upper(p, 15.0)
        p.near_knee = (110.0 + stride * 5.0, 149.0)
        p.far_knee = (82.0 - stride * 5.0, 149.0)
        p.near_ankle = (116.0 + stride * 10.0, 169.0)
        p.far_ankle = (78.0 - stride * 10.0, 169.0)
        p.coat_flare = 0.4
        p.ring_scale = 0.92

    elif animation == "jump":
        lift = math.sin(t * math.pi)
        p.root_y = -15.0 * lift
        p.body_angle = -5.0 + 7.0 * t
        p.near_knee = (113.0, 139.0)
        p.near_ankle = (103.0, 154.0)
        p.far_knee = (82.0, 140.0)
        p.far_ankle = (93.0, 155.0)
        p.near_elbow = (121.0, 82.0)
        p.near_hand = (125.0, 68.0)
        p.far_elbow = (73.0, 83.0)
        p.far_hand = (69.0, 69.0)
        p.coat_flare = lift
        p.ring_phase = t * 1.7

    elif animation == "fall":
        p.root_y = -13.0 + 16.0 * t
        p.body_angle = 6.0
        p.near_hand = (132.0, 88.0)
        p.far_hand = (61.0, 88.0)
        p.near_ankle = (119.0, 161.0)
        p.far_ankle = (76.0, 160.0)
        p.coat_flare = 0.85

    elif animation == "land_hard":
        impact = _pulse(_clamp01((t - 0.18) / 0.62))
        p.root_y = 9.0 * impact
        p.body_angle = 8.0 * impact
        _shift_upper(p, 10.0 * impact)
        p.near_knee = (116.0, 150.0)
        p.far_knee = (77.0, 150.0)
        p.near_hand = (129.0, 132.0)
        p.far_hand = (66.0, 132.0)
        p.ring_scale = 1.0 - impact * 0.15

    elif animation == "dash_startup":
        charge = _smooth(t)
        p.body_angle = -13.0 * charge
        p.root_x = -4.0 * charge
        p.near_hand = _lp(p.near_hand, (104.0, 94.0), charge)
        p.far_hand = _lp(p.far_hand, (91.0, 96.0), charge)
        p.coat_flare = charge
        p.ring_scale = 1.0 - charge * 0.12

    elif animation == "dash":
        p.root_x = 12.0 * _smooth(t)
        p.body_angle = -17.0
        p.near_hand = (137.0, 87.0)
        p.far_hand = (72.0, 100.0)
        p.near_ankle = (124.0, 164.0)
        p.far_ankle = (78.0, 163.0)
        p.coat_flare = 1.0
        p.ring_phase = t * 3.0
        p.spectrum = 0.35

    elif animation == "slide":
        p.root_y = 4.0
        p.body_angle = -20.0
        p.near_knee = (128.0, 144.0)
        p.near_ankle = (150.0, 155.0)
        p.far_knee = (82.0, 150.0)
        p.far_ankle = (65.0, 165.0)
        p.near_hand = (133.0, 104.0)
        p.far_hand = (81.0, 118.0)
        p.coat_flare = 1.0
        p.ring_scale = 0.88

    elif animation == "roll":
        p.body_angle = t * 360.0
        p.root_y = 13.0 - 4.0 * math.sin(t * math.pi)
        p.head = (96.0, 87.0)
        p.neck = (96.0, 97.0)
        p.near_shoulder = (107.0, 100.0)
        p.far_shoulder = (85.0, 100.0)
        p.near_elbow = (114.0, 111.0)
        p.far_elbow = (78.0, 111.0)
        p.near_hand = (108.0, 123.0)
        p.far_hand = (84.0, 123.0)
        p.near_hip = (106.0, 123.0)
        p.far_hip = (86.0, 123.0)
        p.near_knee = (110.0, 135.0)
        p.far_knee = (82.0, 135.0)
        p.near_ankle = (103.0, 143.0)
        p.far_ankle = (89.0, 143.0)
        p.ring_scale = 0.70
        p.ring_front = 0.45

    elif animation == "wall_grab":
        p.root_x = 12.0
        p.body_angle = 4.0
        p.near_hand = (143.0, 68.0)
        p.far_hand = (139.0, 84.0)
        p.near_elbow = (126.0, 74.0)
        p.far_elbow = (119.0, 87.0)
        p.near_ankle = (139.0, 151.0)
        p.far_ankle = (133.0, 166.0)
        p.near_knee = (120.0, 143.0)
        p.far_knee = (115.0, 151.0)
        p.ring_scale = 0.90

    elif animation == "wall_jump":
        launch = _smooth(t)
        p.root_x = 10.0 - 22.0 * launch
        p.root_y = -14.0 * math.sin(t * math.pi)
        p.body_angle = -16.0 + 28.0 * launch
        p.near_hand = (132.0, 78.0)
        p.far_hand = (65.0, 84.0)
        p.near_ankle = (125.0, 155.0)
        p.far_ankle = (79.0, 158.0)
        p.coat_flare = 1.0

    elif animation == "ledge_grab":
        p.root_y = 13.0
        p.near_hand = (115.0, 38.0)
        p.far_hand = (83.0, 38.0)
        p.near_elbow = (111.0, 56.0)
        p.far_elbow = (82.0, 57.0)
        p.near_ankle = (110.0, 166.0)
        p.far_ankle = (84.0, 166.0)
        p.ring_scale = 0.88

    elif animation == "ledge_climb":
        climb = _smooth(t)
        p.root_y = 13.0 - 32.0 * climb
        p.near_hand = (116.0, 39.0 + climb * 30.0)
        p.far_hand = (82.0, 39.0 + climb * 30.0)
        p.near_elbow = (111.0, 57.0 + climb * 21.0)
        p.far_elbow = (82.0, 57.0 + climb * 21.0)
        p.near_knee = (113.0, 143.0 - climb * 18.0)
        p.far_knee = (82.0, 146.0 - climb * 14.0)
        p.ring_scale = 0.88 + climb * 0.12

    elif animation == "climb":
        reach = wave
        p.near_hand = (116.0, 54.0 - reach * 12.0)
        p.far_hand = (80.0, 54.0 + reach * 12.0)
        p.near_elbow = (112.0, 74.0 - reach * 7.0)
        p.far_elbow = (82.0, 74.0 + reach * 7.0)
        p.near_ankle = (111.0, 162.0 + reach * 8.0)
        p.far_ankle = (83.0, 162.0 - reach * 8.0)
        p.ring_phase = t * 1.6

    elif animation == "swim":
        p.body_angle = -72.0
        p.root_y = 7.0 + wave * 2.0
        p.near_hand = (137.0 + wave * 6.0, 101.0)
        p.far_hand = (130.0 - wave * 5.0, 116.0)
        p.near_ankle = (61.0, 158.0 + wave * 8.0)
        p.far_ankle = (69.0, 142.0 - wave * 8.0)
        p.coat_flare = 1.0
        p.ring_scale = 0.90

    elif animation == "block":
        guard = _pulse(t)
        p.near_elbow = _lp(p.near_elbow, (112.0, 83.0), guard)
        p.near_hand = _lp(p.near_hand, (91.0, 92.0), guard)
        p.far_elbow = _lp(p.far_elbow, (83.0, 84.0), guard)
        p.far_hand = _lp(p.far_hand, (107.0, 94.0), guard)
        p.block = guard
        p.ring_scale = 1.0 + guard * 0.08

    elif animation == "hit":
        flinch = _pulse(t)
        p.root_x = -7.0 * flinch
        p.body_angle = 13.0 * flinch
        p.head_tilt = 11.0 * flinch
        p.near_hand = _add(p.near_hand, -8.0 * flinch, -3.0 * flinch)
        p.far_hand = _add(p.far_hand, -5.0 * flinch, 5.0 * flinch)
        p.hurt = flinch
        p.ring_phase = 0.5 + t * 0.2

    elif animation == "death":
        fall = _smooth(t)
        p.body_angle = 64.0 * fall
        p.root_x = 0.0
        p.root_y = 17.0 * fall
        p.near_hand = _lp(p.near_hand, (137.0, 119.0), fall)
        p.far_hand = _lp(p.far_hand, (67.0, 122.0), fall)
        p.defeat = fall
        p.ring_scale = 1.0 - fall * 0.25
        p.ring_front = 1.0 - fall * 0.6

    elif animation == "talk":
        gesture = max(0.0, wave)
        p.near_elbow = _add(p.near_elbow, -7.0 * gesture, -7.0 * gesture)
        p.near_hand = _add(p.near_hand, 7.0 * gesture, -17.0 * gesture)
        p.far_hand = _add(p.far_hand, -3.0 * max(0.0, -wave), -7.0 * max(0.0, -wave))
        p.head_tilt = -wave * 2.2
        p.mouth = 0.35 + abs(wave) * 0.65
        p.brow = gesture * 0.3
        p.glint = 0.15

    elif animation == "interact":
        reach = _smooth(t)
        p.body_angle = -5.0 * reach
        p.near_elbow = _lp(p.near_elbow, (127.0, 91.0), reach)
        p.near_hand = _lp(p.near_hand, (151.0, 91.0), reach)
        p.far_hand = _lp(p.far_hand, (84.0, 103.0), reach)
        p.glint = reach

    elif animation == "jab":
        strike = _pulse(_clamp01((t - 0.08) / 0.82))
        p.body_angle = -6.0 * strike
        p.near_elbow = _lp(p.near_elbow, (133.0, 88.0), strike)
        p.near_hand = _lp(p.near_hand, (157.0, 84.0), strike)
        p.far_hand = _lp(p.far_hand, (88.0, 93.0), strike)
        p.curve = strike * 0.18

    elif animation == "curve_cut":
        wind = _smooth(_clamp01(t / 0.32))
        strike = _smooth(_clamp01((t - 0.24) / 0.52))
        recover = _smooth(_clamp01((t - 0.78) / 0.22))
        p.body_angle = -13.0 * wind + 18.0 * strike - 5.0 * recover
        p.near_hand = _lp((108.0, 72.0), (161.0, 89.0), strike)
        p.near_elbow = _lp((111.0, 83.0), (133.0, 87.0), strike)
        p.far_hand = _lp(p.far_hand, (88.0, 94.0), wind)
        p.curve = max(0.0, strike - recover * 0.65)
        p.coat_flare = max(wind, strike)

    elif animation in {"air_neutral", "air_forward", "air_up", "air_down"}:
        p.root_y = -10.0 + 4.0 * math.sin(t * math.pi)
        p.coat_flare = 1.0
        if animation == "air_neutral":
            p.counter = 0.35 + 0.65 * _pulse(t)
            p.near_hand = (131.0, 83.0)
            p.far_hand = (63.0, 84.0)
            p.near_ankle = (121.0, 154.0)
            p.far_ankle = (72.0, 153.0)
        elif animation == "air_forward":
            strike = _pulse(t)
            p.body_angle = -10.0
            p.near_hand = (156.0, 82.0)
            p.near_elbow = (130.0, 86.0)
            p.curve = strike * 0.7
            p.near_ankle = (126.0, 157.0)
            p.far_ankle = (78.0, 156.0)
        elif animation == "air_up":
            p.near_hand = (113.0, 35.0)
            p.far_hand = (80.0, 41.0)
            p.lens = _pulse(t) * 0.7
            p.near_ankle = (114.0, 157.0)
            p.far_ankle = (83.0, 157.0)
        else:
            p.body_angle = 10.0
            p.near_hand = (124.0, 111.0)
            p.far_hand = (74.0, 109.0)
            p.near_ankle = (124.0, 176.0)
            p.far_ankle = (82.0, 171.0)
            p.halo = _pulse(t) * 0.45

    elif animation == "spectral_lens":
        charge = _smooth(_clamp01(t / 0.45))
        release = _smooth(_clamp01((t - 0.42) / 0.36))
        fade = _smooth(_clamp01((t - 0.82) / 0.18))
        p.near_elbow = _lp(p.near_elbow, (122.0, 73.0), charge)
        p.near_hand = _lp(p.near_hand, (137.0, 62.0), charge)
        p.far_hand = _lp(p.far_hand, (91.0, 92.0), charge)
        p.lens = max(charge * 0.45, release * (1.0 - fade))
        p.spectrum = release * (1.0 - fade)
        p.glint = charge
        p.ring_scale = 1.0 + charge * 0.12

    elif animation == "halo_reveal":
        rise = _smooth(_clamp01(t / 0.42))
        fall = _smooth(_clamp01((t - 0.76) / 0.24))
        p.near_hand = _lp(p.near_hand, (137.0, 81.0), rise)
        p.far_hand = _lp(p.far_hand, (57.0, 83.0), rise)
        p.near_elbow = _lp(p.near_elbow, (122.0, 87.0), rise)
        p.far_elbow = _lp(p.far_elbow, (72.0, 88.0), rise)
        p.halo = rise * (1.0 - fall)
        p.ring_scale = 1.0 + p.halo * 0.34
        p.ring_phase = t * 2.4
        p.starfield = p.halo
        p.mouth = 0.15 * p.halo

    elif animation == "counter_rotation":
        charge = _smooth(_clamp01(t / 0.3))
        sustain = 1.0 - _smooth(_clamp01((t - 0.78) / 0.22))
        p.counter = charge * sustain
        p.ring_phase = t * 4.0
        p.near_hand = _lp(p.near_hand, (128.0, 77.0), charge)
        p.far_hand = _lp(p.far_hand, (66.0, 79.0), charge)
        p.near_elbow = _lp(p.near_elbow, (117.0, 87.0), charge)
        p.far_elbow = _lp(p.far_elbow, (76.0, 88.0), charge)
        p.body_angle = wave * 3.0 * p.counter
        p.ring_scale = 1.0 + p.counter * 0.18
        p.starfield = p.counter * 0.6

    elif animation == "celebrate":
        lift = _pulse(t)
        p.near_hand = _lp(p.near_hand, (119.0, 38.0), lift)
        p.far_hand = _lp(p.far_hand, (74.0, 41.0), lift)
        p.near_elbow = _lp(p.near_elbow, (116.0, 61.0), lift)
        p.far_elbow = _lp(p.far_elbow, (77.0, 63.0), lift)
        p.smile = lift
        p.starfield = lift * 0.65
        p.ring_phase = t * 2.0

    elif animation == "taunt":
        p.near_hand = (108.0, 118.0)
        p.far_hand = (84.0, 119.0)
        p.near_elbow = (120.0, 101.0)
        p.far_elbow = (72.0, 102.0)
        p.head_tilt = -4.0 + wave * 1.2
        p.brow = 0.6
        p.glint = max(0.0, math.sin(t * math.pi))
        p.ring_phase = 0.1 + t * 0.25

    else:
        raise KeyError(f"unknown Vera Ruin animation: {animation}")

    return p


def _sp(point: Point) -> Point:
    """A logical point in supersampled canvas pixels, unrounded."""
    return (point[0] * SUPER, point[1] * SUPER)


# -- pieces ---------------------------------------------------------------------
#
# Vera is drawn as a rig: each piece is painted ONCE in its own frame and
# placed turned (``_solo_shape_rig``). A piece symmetric about an axis (the
# ring's arcs, the halo's ellipses, a hand) is painted as one half or quarter
# and placed again MIRRORED: the same raster transposed, which the part
# flipbook stores once with a flip on the draw.

Part = Tuple[Image.Image, Point]
_PIECES: dict = {}
_TRANSPOSED: dict = {}


def _piece(key, box: Tuple[float, float, float, float], paint) -> Part:
    """A piece whose pivot is the logical origin, painted by ``paint(draw, o)``
    with the origin at ``o`` on a canvas covering ``box`` = (left, top, right,
    bottom) logical pixels around it. The canvas is whole logical pixels (a
    multiple of the supersample), so a mirrored copy reduces to the mirror of
    the reduced piece. Cached under ``key``."""
    cached = _PIECES.get(key)
    if cached is None:
        left, top, right, bottom = (int(math.ceil(v)) for v in box)
        image = Image.new("RGBA", ((left + right) * SUPER, (top + bottom) * SUPER), (0, 0, 0, 0))
        o = (float(left), float(top))
        paint(blending_draw(image), o)
        cached = (image, _sp(o))
        _PIECES[key] = cached
    return cached


def _transposed(part: Part, op) -> Part:
    """``part`` mirrored (``Image.FLIP_LEFT_RIGHT``, ``FLIP_TOP_BOTTOM`` or
    ``ROTATE_180``) about its own canvas, its pivot moved with it."""
    image, (px, py) = part
    key = (id(image), op)
    cached = _TRANSPOSED.get(key)
    if cached is None or cached[0] is not image:
        w, h = image.size
        pivot = {
            Image.Transpose.FLIP_LEFT_RIGHT: (w - px, py),
            Image.Transpose.FLIP_TOP_BOTTOM: (px, h - py),
            Image.Transpose.ROTATE_180: (w - px, h - py),
        }[op]
        cached = (image, (image.transpose(op), pivot))
        _TRANSPOSED[key] = cached
    return cached[1]


def _place(canvas: Image.Image, part: Part, at: Point, degrees: float, name: str, opacity: float = 1.0) -> None:
    SR.place(canvas, part, _sp(at), degrees, name, opacity)


def _place_mirrored(canvas: Image.Image, part: Part, at: Point, degrees: float, name: str, ops, opacity: float = 1.0) -> None:
    """``part`` and its mirrors ``ops`` (a ``None`` is the part itself), all
    with their pivot at ``at``."""
    for index, op in enumerate(ops):
        piece = part if op is None else _transposed(part, op)
        _place(canvas, piece, at, degrees, f"{name}{index}", opacity)


FLIP_X = Image.Transpose.FLIP_LEFT_RIGHT
FLIP_Y = Image.Transpose.FLIP_TOP_BOTTOM
TURN_HALF = Image.Transpose.ROTATE_180
QUARTERS = (None, FLIP_X, FLIP_Y, TURN_HALF)


def _nearest(value: float, levels: Sequence[float]) -> float:
    return min(levels, key=lambda level: abs(level - value))


# -- the spectrograph ring ------------------------------------------------------

#: The ring's sizes: ``Pose.ring_scale`` snaps to the nearest (each size is
#: two half-arc rasters).
RING_SCALES = (0.75, 0.88, 1.0, 1.12, 1.3)


def _ring_nodes(center: Point, rx: float, ry: float, phase: float) -> List[Point]:
    points: List[Point] = []
    for offset in (0.0, 1.0 / 3.0, 2.0 / 3.0):
        angle = (phase + offset) * math.tau
        points.append((center[0] + math.cos(angle) * rx, center[1] + math.sin(angle) * ry))
    return points


def _ring_half_piece(which: str, scale: float) -> Part:
    """The right half of the ring's back (top) or front (bottom, with its
    engraved velocity ticks) arc at ``scale``, centred on its pivot; the left
    half is its mirror."""
    rx, ry = 48.0 * scale, 20.0 * scale
    pad = 6.0

    def paint(draw, c) -> None:
        if which == "back":
            _arc(draw, c, rx, ry, 270, 352, OUTLINE, 6.0)
            _arc(draw, c, rx, ry, 270, 350, BRASS_DARK, 3.2)
            _arc(draw, c, rx - 5.0, ry - 3.0, 270, 342, COAT_LIGHT, 1.3)
        else:
            _arc(draw, c, rx, ry, 8, 90, BRASS_DARK, 5.4)
            _arc(draw, c, rx, ry, 10, 90, BRASS, 2.8)
            for idx in range(4):
                angle = math.radians(22.0 + idx * 17.0)
                outer = (c[0] + math.cos(angle) * rx, c[1] + math.sin(angle) * ry)
                inner = (c[0] + math.cos(angle) * (rx - 4.0), c[1] + math.sin(angle) * (ry - 2.0))
                _line(draw, [inner, outer], BRASS_LIGHT, 0.9)

    # The canvas spans the whole ellipse box (``_box`` clamps a negative
    # corner); the empty half costs nothing once the part is trimmed.
    box = (rx + pad, ry + pad, rx + pad, 2.0) if which == "back" else (rx + pad, 2.0, rx + pad, ry + pad)
    return _piece(("vera_ring_half", which, scale), box, paint)


def _dot_piece(radius: float, fill: RGBA, outline: RGBA | None, width: float) -> Part:
    """A small round node (a ring bead, a star) centred on its pivot."""
    pad = radius + width + 1.0
    return _piece(("vera_dot", radius, fill, outline, width), (pad, pad, pad, pad), lambda d, c: _ellipse(d, c, radius, radius, fill, outline, width))


def _ring_scale(pose: Pose) -> float:
    return _nearest(pose.ring_scale, RING_SCALES)


def _draw_back_ring(canvas: Image.Image, center: Point, pose: Pose) -> None:
    scale = _ring_scale(pose)
    rx, ry = 48.0 * scale, 20.0 * scale
    _place_mirrored(canvas, _ring_half_piece("back", scale), center, 0.0, "ring_back", (None, FLIP_X))
    for index, point in enumerate(_ring_nodes(center, rx, ry, pose.ring_phase)):
        if point[1] <= center[1]:
            fill = (CYAN, MAGENTA, GOLD)[index]
            _place(canvas, _dot_piece(3.2, fill, OUTLINE, 0.9), point, 0.0, f"ring_node{index}")


def _draw_front_ring(canvas: Image.Image, center: Point, pose: Pose) -> None:
    if pose.ring_front <= 0.0:
        return
    scale = _ring_scale(pose)
    rx, ry = 48.0 * scale, 20.0 * scale
    _place_mirrored(canvas, _ring_half_piece("front", scale), center, 0.0, "ring_front", (None, FLIP_X), _clamp01(pose.ring_front))
    for index, point in enumerate(_ring_nodes(center, rx, ry, pose.ring_phase)):
        if point[1] > center[1]:
            fill = (CYAN, MAGENTA, GOLD)[index]
            _place(canvas, _dot_piece(3.4, fill, OUTLINE, 0.9), point, 0.0, f"ring_node{index}")


# -- limbs ----------------------------------------------------------------------
#
# A limb is two bones of ONE length (one raster a limb), bent toward the joint
# the pose authors, reaching the hand or ankle the pose authors. The old
# painter stretched every bone to fit each pose; a limb here takes the
# shortest of a few lengths that reaches (a short ladder of rasters), and past
# the longest it points at the target, straight.

ARM_BONE = (21.0, 25.0, 29.0, 33.0)
LEG_BONE = (26.0, 30.0, 34.0)
ARM_RADIUS = 4.7
LEG_RADIUS = 4.75


def _two_bone(root: Point, target: Point, joint: Point, lengths: Sequence[float], forward: Point) -> Tuple[Point, Point, float]:
    """``(joint, end, bone length)`` of a limb from ``root`` toward ``target``
    bent toward the authored ``joint`` (toward ``forward`` when the authored
    limb is nearly straight)."""
    d = math.hypot(target[0] - root[0], target[1] - root[1])
    length = next((v for v in lengths if d < 2.0 * v * 0.999), lengths[-1])
    reach = 2.0 * length * 0.999
    if d > reach:
        target = (root[0] + (target[0] - root[0]) * reach / d, root[1] + (target[1] - root[1]) * reach / d)
    mid = ((root[0] + target[0]) / 2.0, (root[1] + target[1]) / 2.0)
    bend = (joint[0] - mid[0], joint[1] - mid[1])
    if math.hypot(*bend) < 3.0:
        bend = forward
    knee, _seg = SR.two_bone(root, target, length, bend)
    return knee, target, length


def _bone(canvas: Image.Image, a: Point, b: Point, length: float, radius: float, fill: RGBA, name: str, cuff: RGBA | None = None) -> None:
    """A capsule bone of a fixed ``length`` from ``a`` toward ``b`` (outline
    first, then fill: no ring across its ends); ``cuff`` paints the last
    fifth of it as a cream cuff."""
    pad = radius + 1.1 + 1.0

    def paint(draw, o) -> None:
        end = (o[0] + length, o[1])
        _line(draw, [o, end], OUTLINE, radius * 2.0 + 2.2)
        _ellipse(draw, o, radius + 1.1, radius + 1.1, OUTLINE, None)
        _ellipse(draw, end, radius + 1.1, radius + 1.1, OUTLINE, None)
        _line(draw, [o, end], fill, radius * 2.0)
        _ellipse(draw, o, radius, radius, fill, None)
        _ellipse(draw, end, radius, radius, fill, None)
        if cuff is not None:
            start = (o[0] + length * 0.78, o[1])
            _capsule(draw, start, end, 3.5, cuff)

    part = _piece(("vera_bone", length, radius, fill, cuff), (pad, pad, length + pad, pad), paint)
    _place(canvas, part, a, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), name)


def _boot_piece(near: bool) -> Part:
    """The boot, in its own frame: the pivot is the ankle."""
    direction = 1.0 if near else -1.0

    def paint(draw, ankle) -> None:
        boot_center = (ankle[0] + direction * 3.7, ankle[1] + 2.0)
        _poly(
            draw,
            [
                (boot_center[0] - 5.8, boot_center[1] - 4.2),
                (boot_center[0] + 6.8, boot_center[1] - 3.2),
                (boot_center[0] + 8.0, boot_center[1] + 3.2),
                (boot_center[0] - 5.0, boot_center[1] + 3.5),
            ],
            BOOT,
            OUTLINE,
            1.1,
        )
        _line(draw, [(boot_center[0] - 4.0, boot_center[1] + 1.5), (boot_center[0] + 7.0, boot_center[1] + 1.2)], OUTLINE_SOFT, 1.0)

    return _piece(("vera_boot", near), (10.0, 6.0, 14.0, 8.0), paint)


def _forward(x: float, y: float, body_angle: float) -> Point:
    """A body-frame direction turned with the body (knees bend forward,
    elbows hang back and down)."""
    a = math.radians(body_angle)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


def _draw_leg(canvas: Image.Image, hip: Point, knee: Point, ankle: Point, near: bool, body_angle: float) -> None:
    trouser = TROUSER_LIGHT if near else TROUSER
    side = "near" if near else "far"
    knee, ankle, length = _two_bone(hip, ankle, knee, LEG_BONE, _forward(1.0, 0.0, body_angle))
    # The boot stands on a whole pixel: its flat sole between two pixel rows
    # is a soft edge a part replayed between pixels does not reproduce.
    ankle = (float(round(ankle[0])), float(round(ankle[1])))
    _bone(canvas, hip, knee, length, LEG_RADIUS, trouser, f"{side}_thigh")
    _bone(canvas, knee, ankle, length, LEG_RADIUS, trouser, f"{side}_shin")
    _place(canvas, _boot_piece(near), ankle, 0.0, f"{side}_boot")


def _hand_piece(direction: float) -> Part:
    """Hand and index finger, in their own frame: the pivot is the hand. The
    hand pointing left is the right one mirrored."""

    def paint(draw, hand) -> None:
        _ellipse(draw, hand, 4.1, 4.3, SKIN, OUTLINE, 1.0)
        # One short index-finger extension for observational gestures.
        _line(draw, [hand, (hand[0] + 4.3, hand[1] - 0.5)], SKIN_LIGHT, 1.5)

    part = _piece(("vera_hand",), (7.0, 7.0, 7.0, 7.0), paint)
    return part if direction > 0 else _transposed(part, FLIP_X)


def _draw_arm(canvas: Image.Image, shoulder: Point, elbow: Point, hand: Point, near: bool, body_angle: float) -> None:
    sleeve = COAT_LIGHT if near else COAT_DARK
    side = "near" if near else "far"
    elbow, hand, length = _two_bone(shoulder, hand, elbow, ARM_BONE, _forward(-0.3, 1.0, body_angle))
    _bone(canvas, shoulder, elbow, length, ARM_RADIUS, sleeve, f"{side}_upper_arm")
    # The forearm carries its cream cuff.
    _bone(canvas, elbow, hand, length, ARM_RADIUS, sleeve, f"{side}_forearm", BLOUSE if near else BLOUSE_SHADE)
    direction = 1.0 if hand[0] >= elbow[0] else -1.0
    _place(canvas, _hand_piece(direction), hand, 0.0, f"{side}_hand")


# -- the coat -------------------------------------------------------------------
#
# The coat is three rigid pieces riding the body: the plum lining and the long
# right tail, each turned about its hip by the coat's flare, under the main
# coat (collar to hem, lapel, blouse strip, clasp and badge). A crouch moves
# the whole coat with the upper body. The tucked roll has its own layout.

RIGHT_TAIL_HINGE = (112.0, 115.0)
LINING_HINGE = (90.0, 120.0)
#: Degrees the flare turns each tail (the old tails' tips swung this far).
RIGHT_TAIL_FLARE_DEG = -14.6
LINING_FLARE_DEG = 10.0


def _coat_layout(pose: Pose) -> Tuple[str, Pose, Point]:
    """The coat's layout, the pose it is painted for, and how far the pose's
    upper body moved it."""
    if pose.near_shoulder[0] - pose.far_shoulder[0] < 26.0:
        rest = Pose(far_shoulder=(85.0, 100.0), near_shoulder=(107.0, 100.0), far_hip=(86.0, 123.0), near_hip=(106.0, 123.0))
        layout = "tuck"
    else:
        rest = Pose()
        layout = "stand"
    offset = (pose.far_shoulder[0] - rest.far_shoulder[0], pose.far_shoulder[1] - rest.far_shoulder[1])
    return layout, rest, offset


def _paint_coat_main(draw, rest: Pose, o: Point) -> None:
    def P(x: float, y: float) -> Point:
        return (o[0] + x - PIVOT[0], o[1] + y - PIVOT[1])

    def Q(point: Point) -> Point:
        return P(*point)

    coat = [Q(rest.far_shoulder), P(91.0, 65.0), P(101.0, 64.0), Q(rest.near_shoulder), P(117.0, 111.0), P(108.0, 128.0), P(97.0, 137.0), P(83.0, 137.0), P(78.0, 108.0)]
    _poly(draw, coat, COAT, OUTLINE, 1.7)
    # Asymmetric brighter lapel and cream spectral strip.
    _poly(draw, [P(99.0, 66.0), Q(rest.near_shoulder), P(108.0, 108.0), P(99.0, 120.0), P(96.0, 83.0)], COAT_LIGHT, OUTLINE_SOFT, 1.1)
    _poly(draw, [P(91.0, 65.0), P(101.0, 64.0), P(101.0, 112.0), P(94.0, 119.0), P(91.0, 85.0)], BLOUSE, OUTLINE, 1.2)
    _line(draw, [P(96.0, 73.0), P(96.0, 111.0)], BLOUSE_SHADE, 1.2)
    # Brass calibration clasp and a deliberately flat rotation-curve badge.
    _ellipse(draw, P(98.0, 88.0), 3.2, 3.2, BRASS, OUTLINE, 0.8)
    _line(draw, [P(103.0, 99.0), P(113.0, 99.0)], GOLD, 1.4)
    for x in (105.0, 109.0, 113.0):
        _ellipse(draw, P(x, 99.0), 0.9, 0.9, RED, None)


def _paint_right_tail(draw, o: Point) -> None:
    def P(x: float, y: float) -> Point:
        return (o[0] + x - RIGHT_TAIL_HINGE[0], o[1] + y - RIGHT_TAIL_HINGE[1])

    _poly(draw, [P(115.0, 102.0), P(120.0, 151.0), P(97.0, 137.0), P(103.0, 120.0)], COAT, OUTLINE, 1.7)


def _paint_lining(draw, hip: Point, o: Point) -> None:
    def P(x: float, y: float) -> Point:
        return (o[0] + x - LINING_HINGE[0], o[1] + y - LINING_HINGE[1])

    _poly(draw, [P(*hip), P(97.0, 137.0), P(83.0, 156.0), P(92.0, 118.0)], LINING, OUTLINE, 1.4)
    for star in ((88.0, 133.0), (83.0, 144.0), (94.0, 145.0)):
        _ellipse(draw, P(*star), 1.0, 1.0, STAR, None)


def _draw_coat(canvas: Image.Image, pose: Pose) -> None:
    layout, rest, offset = _coat_layout(pose)
    flare = pose.coat_flare

    def at(point: Point) -> Point:
        return _xf((point[0] + offset[0], point[1] + offset[1]), pose)

    lining = _piece(("vera_lining", layout), (12.0, 8.0, 12.0, 40.0), lambda d, o: _paint_lining(d, rest.far_hip, o))
    _place(canvas, lining, at(LINING_HINGE), pose.body_angle + LINING_FLARE_DEG * flare, "coat_lining")
    tail = _piece(("vera_right_tail",), (19.0, 16.0, 10.0, 40.0), _paint_right_tail)
    _place(canvas, tail, at(RIGHT_TAIL_HINGE), pose.body_angle + RIGHT_TAIL_FLARE_DEG * flare, "coat_tail")
    main = _piece(("vera_coat", layout), (22.0, 59.0, 24.0, 21.0), lambda d, o: _paint_coat_main(d, rest, o))
    _place(canvas, main, at(PIVOT), pose.body_angle, "coat")


# -- the head: a base and expression overlays -----------------------------------

HEAD_HALF = 35.0


def _head_painters(draw, o: Point):
    """Drawing helpers in the head's own frame (logical pixels, the head's
    centre at ``o``)."""
    cx, cy = o

    def e(c: Point, rx: float, ry: float, fill: RGBA, outline: RGBA | None = OUTLINE, width: float = 1.2) -> None:
        _ellipse(draw, (cx + c[0], cy + c[1]), rx, ry, fill, outline, width)

    def l(points: Sequence[Point], fill: RGBA, width: float) -> None:
        _line(draw, [(cx + x, cy + y) for x, y in points], fill, width)

    def poly(points: Sequence[Point], fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.2) -> None:
        _poly(draw, [(cx + x, cy + y) for x, y in points], fill, outline, width)

    return e, l, poly


def _paint_head_base(draw, o: Point) -> None:
    """Hair, face, glasses, nose, age lines and earring: every expression's
    head."""
    e, l, poly = _head_painters(draw, o)
    # Short silver bob with a hard side part and one darker underlayer.
    e((-1.0, -2.0), 20.0, 22.0, HAIR_DARK, OUTLINE, 1.5)
    poly([(-19.0, -2.0), (-14.0, -18.0), (-3.0, -24.0), (13.0, -20.0), (20.0, -7.0), (18.0, 12.0), (8.0, 17.0), (-11.0, 16.0), (-19.0, 7.0)], HAIR, OUTLINE, 1.5)
    # Face is rounder and older than the existing young-scholar sprites.
    e((1.0, 2.0), 14.7, 17.0, SKIN, OUTLINE, 1.5)
    e((-14.2, 3.0), 3.3, 5.2, SKIN_SHADE, OUTLINE, 0.8)
    # Silver cap mass and distinct side streak.
    poly([(-17.0, -5.0), (-11.0, -19.0), (1.0, -23.0), (16.0, -15.0), (18.0, -5.0), (8.0, -10.0), (-2.0, -11.0), (-10.0, -6.0)], HAIR_LIGHT, OUTLINE, 1.1)
    l([(-5.0, -20.0), (-2.0, -7.0)], STAR, 1.2)
    l([(4.0, -20.0), (10.0, -7.0)], HAIR, 2.0)
    # Round glasses. The near lens has a brass spectral eyepiece.
    e((-6.8, 0.2), 7.0, 5.6, GLASS, BRASS_DARK, 1.1)
    e((7.0, 0.2), 7.0, 5.6, GLASS, BRASS, 1.3)
    l([(0.2, 0.2), (0.8, 0.2)], BRASS_DARK, 1.1)
    l([(-13.7, -0.5), (-18.0, -2.0)], BRASS_DARK, 1.1)
    l([(13.7, -0.5), (18.0, -2.0)], BRASS_DARK, 1.1)
    # Nose and age lines.
    l([(0.5, 1.5), (2.0, 7.0), (4.4, 8.0)], SKIN_SHADE, 1.0)
    l([(-12.0, 7.5), (-9.0, 8.8)], SKIN_SHADE, 0.7)
    l([(10.0, 8.5), (13.0, 7.5)], SKIN_SHADE, 0.7)
    # Small brass star earring.
    e((-16.0, 8.5), 1.8, 1.8, BRASS_LIGHT, OUTLINE, 0.6)


def _paint_eyes(draw, o: Point, blink: bool, brow: float) -> None:
    """Brows and eyes (open or shut): the eye overlay."""
    e, l, _poly_ = _head_painters(draw, o)
    brow_y = -3.5 - brow * 1.4
    l([(-10.5, brow_y), (-3.0, brow_y - 1.0)], HAIR_DARK, 1.4)
    l([(3.0, brow_y - 1.0), (11.5, brow_y)], HAIR_DARK, 1.4)
    if blink:
        l([(-10.0, 0.5), (-3.5, 0.5)], EYE, 1.3)
        l([(3.5, 0.5), (10.0, 0.5)], EYE, 1.3)
    else:
        e((-6.8, 0.4), 1.5, 1.8, EYE, None)
        e((7.0, 0.3), 1.5, 1.8, EYE, None)
        e((-6.3, -0.2), 0.45, 0.55, STAR, None)
        e((7.5, -0.3), 0.45, 0.55, STAR, None)


def _paint_mouth(draw, o: Point, shape: str, opening: float) -> None:
    e, l, _poly_ = _head_painters(draw, o)
    mouth_y = 12.0
    if shape == "open":
        e((1.0, mouth_y), 4.8, 1.4 + opening * 2.0, MOUTH, OUTLINE, 0.7)
    elif shape == "smile":
        _arc(draw, (o[0] + 1.0, o[1] + mouth_y + 1.5), 6.0, 3.5, 10, 170, MOUTH, 1.2)
    else:
        l([(-3.5, mouth_y), (5.0, mouth_y - 0.2)], MOUTH, 1.1)


def _paint_glint(draw, o: Point) -> None:
    """The near lens's spectral glint at full strength."""
    _e, l, _poly_ = _head_painters(draw, o)
    l([(3.0, -5.0), (11.0, 5.0)], CYAN, 1.8)
    l([(3.0, 5.0), (11.0, -5.0)], STAR, 1.4)


def _draw_head(canvas: Image.Image, center: Point, pose: Pose) -> None:
    """The head: one base for every expression, turned by the head tilt about
    its centre, with the eyes (open or shut, brows raised a step), the mouth
    and the lens glint (its strength the draw's opacity) as overlays on it."""
    box = (HEAD_HALF,) * 4
    tilt = pose.head_tilt
    _place(canvas, _piece(("vera_head",), box, _paint_head_base), center, tilt, "head")
    blink = pose.blink > 0.5
    brow = _nearest(pose.brow, (0.0, 0.3, 0.6))
    _place(canvas, _piece(("vera_eyes", blink, brow), box, lambda d, o: _paint_eyes(d, o, blink, brow)), center, tilt, "eyes")
    if pose.mouth > 0.12:
        shape, opening = "open", _nearest(pose.mouth, (0.15, 0.4, 0.7, 1.0))
    elif pose.smile > 0.15:
        shape, opening = "smile", 0.0
    else:
        shape, opening = "line", 0.0
    _place(canvas, _piece(("vera_mouth", shape, opening), box, lambda d, o: _paint_mouth(d, o, shape, opening)), center, tilt, "mouth")
    if pose.glint > 0.05:
        _place(canvas, _piece(("vera_glint",), box, _paint_glint), center, tilt, "glint", min(1.0, pose.glint))


# -- effects: pieces placed with their strength as opacity ----------------------
#
# Each effect is painted once per size step. The halo's and the counter
# orbit's ellipses are a quarter (or half) placed mirrored.


def _ellipse_quarter(key, rx: float, ry: float, paint) -> Part:
    """A piece covering the lower-right quarter of an ellipse centred on its
    pivot (plus what crosses its axes)."""
    pad = 6.0
    # The canvas spans the whole ellipse box (``_box`` clamps a negative corner).
    return _piece(("vera_quarter", key, rx, ry), (rx + pad, ry + pad, rx + pad, ry + pad), paint)


HALO_LEVELS = (0.25, 0.5, 0.75, 1.0)


def _halo_quarter(amount: float) -> Part:
    rx, ry = 54.0 + amount * 24.0, 38.0 + amount * 15.0

    def paint(draw, c) -> None:
        _arc(draw, c, rx, ry, 0, 90, CYAN_SOFT, 5.0)
        _arc(draw, c, rx - 7.0, ry - 5.0, 0, 90, MAGENTA_SOFT, 3.0)
        # Observed data points every twelfth of a turn (the ones on the axes
        # are painted whole by both quarters that meet there).
        for index in range(4):
            angle = index / 12.0 * math.tau
            point = (c[0] + math.cos(angle) * rx, c[1] + math.sin(angle) * ry)
            _ellipse(draw, point, 1.7 + amount, 1.7 + amount, CYAN if index % 3 else MAGENTA, OUTLINE, 0.4)

    return _ellipse_quarter(("halo", amount), rx, ry, paint)


COUNTER_LEVELS = (0.5, 1.0)


def _counter_quarter(amount: float, colour: RGBA) -> Part:
    rx, ry = 52.0 + amount * 12.0, 26.0 + amount * 8.0
    return _ellipse_quarter(("counter", amount, colour), rx, ry, lambda d, c: _arc(d, c, rx, ry, 4, 86, colour, 2.2))


def _comet_piece(colour: RGBA) -> Part:
    """A counter-rotating node with its short trail behind it (along -x)."""

    def paint(draw, o) -> None:
        _line(draw, [(o[0] - 12.0, o[1]), o], colour, 1.5)
        _ellipse(draw, o, 3.0, 3.0, colour, OUTLINE, 0.7)

    return _piece(("vera_comet", colour), (14.0, 5.0, 5.0, 5.0), paint)


CURVE_LEVELS = (0.2, 0.6, 1.0)


def _curve_piece(amount: float) -> Part:
    """The flat rotation curve traced from its start: points rise, then stay
    stubbornly flat."""

    def paint(draw, s) -> None:
        end_x = s[0] + _lerp(18.0, 71.0, amount)
        points = [s, (s[0] + 10.0, s[1] - 8.0 * amount), (s[0] + 22.0, s[1] - 11.0 * amount), (end_x, s[1] - 11.0 * amount)]
        _line(draw, points, GOLD, 2.2)
        for index in range(6):
            local = index / 5.0
            x = _lerp(s[0] + 3.0, end_x, local)
            y = s[1] - min(11.0 * amount, local * 28.0 * amount)
            _ellipse(draw, (x, y), 1.8, 1.8, RED if index % 2 else CYAN, OUTLINE, 0.5)

    return _piece(("vera_curve", amount), (4.0, 15.0, 76.0, 4.0), paint)


LENS_LEVELS = (0.25, 0.5, 0.75, 1.0)


def _lens_piece(amount: float) -> Part:
    radius = 12.0 + 20.0 * amount

    def paint(draw, c) -> None:
        _arc(draw, c, radius, radius * 0.70, 194, 342, CYAN, 2.0)
        _arc(draw, c, radius - 4.0, (radius - 4.0) * 0.70, 198, 338, MAGENTA, 1.6)
        _ellipse(draw, c, 3.0 + amount * 2.0, 3.0 + amount * 2.0, STAR, BRASS, 0.8)

    return _piece(("vera_lens", amount), (radius + 3.0, radius * 0.7 + 3.0, radius + 3.0, 7.0), paint)


SPECTRUM_LEVELS = (0.5, 1.0)


def _spectrum_piece(amount: float) -> Part:
    """The split beam: red and cyan channels fanning from the hand."""
    length = 16.0 + 30.0 * amount

    def paint(draw, h) -> None:
        _line(draw, [h, (h[0] + length, h[1] - 7.0)], CYAN, 2.0)
        _line(draw, [h, (h[0] + length, h[1] + 7.0)], MAGENTA, 2.0)
        for i in range(4):
            x = h[0] + length * (i + 1) / 4.0
            _line(draw, [(x, h[1] - 6.0), (x, h[1] + 6.0)], STAR, 0.7)

    return _piece(("vera_spectrum", amount), (2.0, 9.0, length + 2.0, 9.0), paint)


STARS = ((54.0, 54.0), (138.0, 48.0), (153.0, 109.0), (39.0, 112.0), (67.0, 142.0), (135.0, 145.0))


def _draw_effects(canvas: Image.Image, pose: Pose, ring_center: Point) -> None:
    if pose.curve > 0.02:
        amount = _nearest(pose.curve, CURVE_LEVELS)
        _place(canvas, _curve_piece(amount), _xf((113.0, 88.0), pose), 0.0, "curve", min(1.0, pose.curve / amount))

    if pose.lens > 0.02:
        amount = _nearest(pose.lens, LENS_LEVELS)
        _place(canvas, _lens_piece(amount), _xf(pose.near_hand, pose), 0.0, "lens", min(1.0, pose.lens / amount))

    if pose.spectrum > 0.02:
        amount = _nearest(pose.spectrum, SPECTRUM_LEVELS)
        _place(canvas, _spectrum_piece(amount), _xf(pose.near_hand, pose), 0.0, "spectrum", min(1.0, pose.spectrum / amount))

    if pose.halo > 0.02:
        amount = _nearest(pose.halo, HALO_LEVELS)
        _place_mirrored(canvas, _halo_quarter(amount), ring_center, 0.0, "halo", QUARTERS, min(1.0, pose.halo / amount))

    if pose.counter > 0.02:
        amount = _nearest(pose.counter, COUNTER_LEVELS)
        rx, ry = 52.0 + amount * 12.0, 26.0 + amount * 8.0
        opacity = min(1.0, pose.counter / amount)
        # Cyan orbit below, magenta above.
        _place_mirrored(canvas, _counter_quarter(amount, CYAN), ring_center, 0.0, "counter_low", (None, FLIP_X), opacity)
        _place_mirrored(canvas, _counter_quarter(amount, MAGENTA), ring_center, 0.0, "counter_high", (FLIP_Y, TURN_HALF), opacity)
        for direction, fill, phase in ((1.0, CYAN, pose.ring_phase), (-1.0, MAGENTA, -pose.ring_phase * 1.3)):
            angle = phase * math.tau * direction
            point = (ring_center[0] + math.cos(angle) * rx, ring_center[1] + math.sin(angle) * ry)
            # The node heads along the orbit, its trail behind it.
            tangent = (-math.sin(angle) * rx * direction, math.cos(angle) * ry * direction)
            _place(canvas, _comet_piece(fill), point, math.degrees(math.atan2(tangent[1], tangent[0])), f"comet_{'cyan' if direction > 0 else 'magenta'}", opacity)

    if pose.starfield > 0.02:
        amount = pose.starfield
        radius = 1.1 if amount < 0.4 else 2.5
        for index, star in enumerate(STARS):
            twinkle = 0.45 + 0.55 * math.sin((pose.ring_phase * 3.0 + index * 0.17) * math.tau) ** 2
            _place(canvas, _dot_piece(radius, STAR if index % 2 else CYAN, None, 0.0), star, 0.0, f"star{index}", twinkle)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    pose = _pose(animation, frame_idx, frame_count)
    canvas = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))

    ring_center = _xf((96.0, 80.0), pose)
    _draw_back_ring(canvas, ring_center, pose)

    # Far leg, near leg, then coat and arms. This order makes the spectrograph
    # ring read as mounted around one coherent body rather than pasted on top.
    _draw_leg(canvas, _xf(pose.far_hip, pose), _xf(pose.far_knee, pose), _xf(pose.far_ankle, pose), False, pose.body_angle)
    _draw_leg(canvas, _xf(pose.near_hip, pose), _xf(pose.near_knee, pose), _xf(pose.near_ankle, pose), True, pose.body_angle)
    _draw_coat(canvas, pose)
    _draw_arm(canvas, _xf(pose.far_shoulder, pose), _xf(pose.far_elbow, pose), _xf(pose.far_hand, pose), False, pose.body_angle)
    _draw_arm(canvas, _xf(pose.near_shoulder, pose), _xf(pose.near_elbow, pose), _xf(pose.near_hand, pose), True, pose.body_angle)

    _draw_front_ring(canvas, ring_center, pose)
    _draw_head(canvas, _xf(pose.head, pose), pose)
    _draw_effects(canvas, pose, ring_center)

    # Through rigdoc's seam, so a part flipbook records each shape.
    return rigdoc.downsampled_canvas(canvas, (FRAME_W, FRAME_H), Image.Resampling.LANCZOS)


# Native dialog portrait -------------------------------------------------------

PORTRAIT_W = 256
PORTRAIT_H = 256
PORTRAIT_SUPER = 2


def _portrait(expression: str, frame_idx: int = 0, frame_count: int = 1) -> Image.Image:
    image = Image.new(
        "RGBA",
        (PORTRAIT_W * PORTRAIT_SUPER, PORTRAIT_H * PORTRAIT_SUPER),
        (0, 0, 0, 0),
    )
    draw = blending_draw(image)
    S = PORTRAIT_SUPER

    def pt(point: Point) -> Tuple[int, int]:
        return (int(round(point[0] * S)), int(round(point[1] * S)))

    def box(center: Point, rx: float, ry: float) -> Tuple[int, int, int, int]:
        return (
            int((center[0] - rx) * S),
            int((center[1] - ry) * S),
            int((center[0] + rx) * S),
            int((center[1] + ry) * S),
        )

    def line(points: Sequence[Point], fill: RGBA, width: float) -> None:
        draw.line([pt(p) for p in points], fill=fill, width=max(1, int(width * S)), joint="curve")

    def ellipse(center: Point, rx: float, ry: float, fill: RGBA, outline: RGBA | None = OUTLINE, width: float = 1.2) -> None:
        draw.ellipse(box(center, rx, ry), fill=fill, outline=outline, width=max(1, int(width * S)) if outline else 1)

    def poly(points: Sequence[Point], fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.3) -> None:
        pts = [pt(p) for p in points]
        draw.polygon(pts, fill=fill)
        draw.line(pts + [pts[0]], fill=outline, width=max(1, int(width * S)), joint="curve")

    t = 0.0 if frame_count <= 1 else frame_idx / float(frame_count - 1)
    wave = math.sin(t * math.tau)
    speaking = expression == "speaking"
    skeptical = expression == "skeptical"
    delighted = expression == "delighted"

    # Large halo rig behind the shoulders.
    draw.arc(box((128.0, 142.0), 104.0, 39.0), 185, 355, fill=OUTLINE, width=int(9 * S))
    draw.arc(box((128.0, 142.0), 104.0, 39.0), 188, 352, fill=BRASS, width=int(4 * S))
    for idx, color in enumerate((CYAN, MAGENTA, GOLD)):
        angle = (t + idx / 3.0) * math.tau
        center = (128.0 + math.cos(angle) * 101.0, 142.0 + math.sin(angle) * 37.0)
        if center[1] < 142.0:
            ellipse(center, 6.0, 6.0, color, OUTLINE, 1.2)

    # Shoulders and asymmetrical coat.
    poly([(13, 256), (29, 201), (69, 177), (121, 180), (122, 256)], COAT_DARK, OUTLINE, 2.5)
    poly([(121, 180), (187, 178), (230, 205), (250, 256), (122, 256)], COAT, OUTLINE, 2.5)
    poly([(142, 181), (187, 181), (214, 256), (154, 256)], COAT_LIGHT, OUTLINE_SOFT, 1.6)
    poly([(91, 179), (139, 179), (153, 256), (111, 256)], BLOUSE, OUTLINE, 1.8)
    line([(123, 193), (124, 250)], BLOUSE_SHADE, 1.7)
    ellipse((136, 215), 7.0, 7.0, BRASS, OUTLINE, 1.2)

    # Back hair mass and face.
    ellipse((126, 101), 62.0, 68.0, HAIR_DARK, OUTLINE, 3.0)
    ellipse((128, 112), 47.0, 54.0, SKIN, OUTLINE, 3.0)
    ellipse((80, 112), 10.0, 17.0, SKIN_SHADE, OUTLINE, 1.5)

    # Silver bob and side part.
    poly(
        [
            (69, 105), (74, 61), (100, 36), (143, 32), (178, 55),
            (192, 92), (178, 84), (157, 70), (134, 68), (111, 76),
            (91, 99),
        ],
        HAIR,
        OUTLINE,
        2.3,
    )
    poly(
        [
            (77, 84), (83, 55), (111, 36), (143, 34), (173, 55),
            (178, 73), (151, 60), (125, 61), (101, 71),
        ],
        HAIR_LIGHT,
        OUTLINE,
        1.8,
    )
    line([(119, 39), (111, 69)], STAR, 2.2)
    line([(145, 38), (157, 69)], HAIR_DARK, 3.0)

    brow_raise = -4.0 if delighted else (4.0 if skeptical else -wave * 1.0)
    line([(93, 99 + brow_raise), (112, 96 + brow_raise)], HAIR_DARK, 3.0)
    line([(139, 96 + brow_raise), (162, 99 + brow_raise)], HAIR_DARK, 3.0)

    eye_shift = 2.0 if skeptical else 0.0
    ellipse((104 + eye_shift, 111), 4.0, 4.8, EYE, None)
    ellipse((151 + eye_shift, 111), 4.0, 4.8, EYE, None)
    ellipse((105 + eye_shift, 109), 1.1, 1.3, STAR, None)
    ellipse((152 + eye_shift, 109), 1.1, 1.3, STAR, None)
    ellipse((104, 111), 24.0, 17.0, GLASS, BRASS_DARK, 2.0)
    ellipse((151, 111), 24.0, 17.0, GLASS, BRASS, 2.5)
    line([(128, 111), (127, 111)], BRASS_DARK, 2.0)
    line([(80, 108), (69, 103)], BRASS_DARK, 2.0)
    line([(175, 108), (187, 103)], BRASS_DARK, 2.0)

    # Near-lens spectral glint.
    if speaking or delighted:
        glint = 0.5 + 0.5 * abs(wave)
        line([(151 - 10 * glint, 97), (151 + 10 * glint, 125)], CYAN, 1.5 + glint)
        line([(151 - 10 * glint, 125), (151 + 10 * glint, 97)], STAR, 1.1 + glint)

    # Nose, age lines, and expression.
    line([(129, 112), (133, 137), (141, 141)], SKIN_SHADE, 2.3)
    line([(91, 128), (99, 132)], SKIN_SHADE, 1.4)
    line([(157, 132), (166, 128)], SKIN_SHADE, 1.4)
    line([(101, 151), (112, 155)], SKIN_SHADE, 1.1)
    line([(150, 155), (162, 151)], SKIN_SHADE, 1.1)

    if speaking:
        openness = 4.0 + abs(wave) * 8.0
        ellipse((132, 164), 15.0, openness, MOUTH, OUTLINE, 1.7)
        line([(121, 160), (142, 160)], SKIN_LIGHT, 1.0)
    elif delighted:
        draw.arc(box((132, 158), 20.0, 17.0), 10, 170, fill=MOUTH, width=int(3 * S))
    elif skeptical:
        line([(116, 166), (133, 163), (149, 166)], MOUTH, 2.3)
    else:
        line([(117, 165), (146, 165)], MOUTH, 2.0)

    ellipse((77, 140), 4.0, 4.0, BRASS_LIGHT, OUTLINE, 1.0)

    # Front ring segment and ticks.
    draw.arc(box((128.0, 142.0), 104.0, 39.0), 5, 175, fill=OUTLINE, width=int(8 * S))
    draw.arc(box((128.0, 142.0), 104.0, 39.0), 8, 172, fill=BRASS, width=int(3 * S))
    for idx in range(13):
        angle = math.radians(13 + idx * 12.8)
        outer = (128.0 + math.cos(angle) * 104.0, 142.0 + math.sin(angle) * 39.0)
        inner = (128.0 + math.cos(angle) * 98.0, 142.0 + math.sin(angle) * 34.0)
        line([inner, outer], BRASS_LIGHT, 1.0)

    return image.resize((PORTRAIT_W, PORTRAIT_H), Image.Resampling.LANCZOS)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    del opts
    clips = {
        "default": PortraitClip.still(_portrait("default")),
        "speaking": PortraitClip(
            tuple(_portrait("speaking", idx, 8) for idx in range(8)),
            duration_ms=105,
            looping=True,
        ),
        "skeptical": PortraitClip.still(_portrait("skeptical")),
        "delighted": PortraitClip.still(_portrait("delighted")),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {
            "x": int(fw * 0.26),
            "y": int(fh * 0.10),
            "w": int(fw * 0.49),
            "h": int(fh * 0.82),
        },
        "feet_pixel": {"x": fw * 0.51, "y": fh * 0.90},
        "feet_anchor_norm": {"x": 0.01, "y": round(0.5 - 0.90, 6)},
    }


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
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
        attack_hitboxes={
            "jab": {"bbox": {"x": 111, "y": 65, "w": 55, "h": 50}},
            "curve_cut": {"bbox": {"x": 108, "y": 58, "w": 76, "h": 61}},
            "air_forward": {"bbox": {"x": 112, "y": 47, "w": 70, "h": 68}},
            "air_up": {"bbox": {"x": 70, "y": 18, "w": 62, "h": 64}},
            "air_down": {"bbox": {"x": 67, "y": 101, "w": 72, "h": 77}},
            "spectral_lens": {"bbox": {"x": 116, "y": 39, "w": 70, "h": 92}},
            "halo_reveal": {"bbox": {"x": 18, "y": 27, "w": 158, "h": 128}},
            "counter_rotation": {"bbox": {"x": 29, "y": 43, "w": 138, "h": 98}},
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
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


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
    return False


__all__ = [
    "ACTOR_METADATA",
    "FRAME_H",
    "FRAME_W",
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
