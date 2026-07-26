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

from ...authoring.portrait import PortraitClip, write_portrait_sheet
from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw

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


def _ring_nodes(center: Point, rx: float, ry: float, phase: float) -> List[Point]:
    points: List[Point] = []
    for offset in (0.0, 1.0 / 3.0, 2.0 / 3.0):
        angle = (phase + offset) * math.tau
        points.append((center[0] + math.cos(angle) * rx, center[1] + math.sin(angle) * ry))
    return points


def _draw_back_ring(draw: ImageDraw.ImageDraw, center: Point, pose: Pose) -> None:
    rx = 48.0 * pose.ring_scale
    ry = 20.0 * pose.ring_scale
    _arc(draw, center, rx, ry, 188, 352, OUTLINE, 6.0)
    _arc(draw, center, rx, ry, 190, 350, BRASS_DARK, 3.2)
    _arc(draw, center, rx - 5.0, ry - 3.0, 198, 342, COAT_LIGHT, 1.3)
    for index, point in enumerate(_ring_nodes(center, rx, ry, pose.ring_phase)):
        if point[1] <= center[1]:
            fill = (CYAN, MAGENTA, GOLD)[index]
            _ellipse(draw, point, 3.2, 3.2, fill, OUTLINE, 0.9)


def _draw_front_ring(draw: ImageDraw.ImageDraw, center: Point, pose: Pose) -> None:
    if pose.ring_front <= 0.0:
        return
    rx = 48.0 * pose.ring_scale
    ry = 20.0 * pose.ring_scale
    alpha = int(255 * pose.ring_front)
    dark = (*BRASS_DARK[:3], alpha)
    bright = (*BRASS[:3], alpha)
    _arc(draw, center, rx, ry, 8, 172, dark, 5.4)
    _arc(draw, center, rx, ry, 10, 170, bright, 2.8)
    # Engraved velocity ticks.
    for idx in range(9):
        angle = math.radians(18.0 + idx * 17.0)
        outer = (center[0] + math.cos(angle) * rx, center[1] + math.sin(angle) * ry)
        inner = (center[0] + math.cos(angle) * (rx - 4.0), center[1] + math.sin(angle) * (ry - 2.0))
        _line(draw, [inner, outer], BRASS_LIGHT, 0.9)
    for index, point in enumerate(_ring_nodes(center, rx, ry, pose.ring_phase)):
        if point[1] > center[1]:
            fill = (CYAN, MAGENTA, GOLD)[index]
            _ellipse(draw, point, 3.4, 3.4, fill, OUTLINE, 0.9)


def _draw_leg(draw: ImageDraw.ImageDraw, hip: Point, knee: Point, ankle: Point, near: bool) -> None:
    trouser = TROUSER_LIGHT if near else TROUSER
    _capsule(draw, hip, knee, 5.0, trouser)
    _capsule(draw, knee, ankle, 4.5, trouser)
    direction = 1.0 if near else -1.0
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


def _draw_coat(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    fs = _xf(pose.far_shoulder, pose)
    ns = _xf(pose.near_shoulder, pose)
    fh = _xf(pose.far_hip, pose)
    nh = _xf(pose.near_hip, pose)
    flare = pose.coat_flare
    left_tail = _xf((83.0 - flare * 8.0, 156.0 + flare * 3.0), pose)
    right_tail = _xf((118.0 + flare * 11.0, 151.0 + flare * 2.0), pose)
    center_tail = _xf((97.0, 137.0), pose)

    # Plum lining first, exposed by the asymmetric split.
    _poly(draw, [fh, center_tail, left_tail, _xf((92.0, 118.0), pose)], LINING, OUTLINE, 1.4)
    for star in ((88.0, 133.0), (83.0, 144.0), (94.0, 145.0)):
        point = _xf(star, pose)
        _ellipse(draw, point, 1.0, 1.0, STAR, None)

    # Main field coat: one long right tail and one cropped left panel.
    coat = [
        fs,
        _xf((91.0, 65.0), pose),
        _xf((101.0, 64.0), pose),
        ns,
        _xf((117.0, 111.0), pose),
        right_tail,
        center_tail,
        _xf((83.0, 137.0), pose),
        _xf((78.0, 108.0), pose),
    ]
    _poly(draw, coat, COAT, OUTLINE, 1.7)

    # Asymmetric brighter lapel and cream spectral strip.
    _poly(
        draw,
        [
            _xf((99.0, 66.0), pose),
            ns,
            _xf((108.0, 108.0), pose),
            _xf((99.0, 120.0), pose),
            _xf((96.0, 83.0), pose),
        ],
        COAT_LIGHT,
        OUTLINE_SOFT,
        1.1,
    )
    _poly(
        draw,
        [
            _xf((91.0, 65.0), pose),
            _xf((101.0, 64.0), pose),
            _xf((101.0, 112.0), pose),
            _xf((94.0, 119.0), pose),
            _xf((91.0, 85.0), pose),
        ],
        BLOUSE,
        OUTLINE,
        1.2,
    )
    _line(draw, [_xf((96.0, 73.0), pose), _xf((96.0, 111.0), pose)], BLOUSE_SHADE, 1.2)

    # Brass calibration clasp and a deliberately flat rotation-curve badge.
    clasp = _xf((98.0, 88.0), pose)
    _ellipse(draw, clasp, 3.2, 3.2, BRASS, OUTLINE, 0.8)
    badge_start = _xf((103.0, 99.0), pose)
    badge_end = _xf((113.0, 99.0), pose)
    _line(draw, [badge_start, badge_end], GOLD, 1.4)
    for x in (105.0, 109.0, 113.0):
        _ellipse(draw, _xf((x, 99.0), pose), 0.9, 0.9, RED, None)


def _draw_arm(
    draw: ImageDraw.ImageDraw,
    shoulder: Point,
    elbow: Point,
    hand: Point,
    near: bool,
) -> None:
    sleeve = COAT_LIGHT if near else COAT_DARK
    _capsule(draw, shoulder, elbow, 5.0, sleeve)
    _capsule(draw, elbow, hand, 4.4, sleeve)
    # Cream cuff and compact hand.
    cuff = _lp(elbow, hand, 0.78)
    _capsule(draw, cuff, hand, 3.5, BLOUSE if near else BLOUSE_SHADE)
    _ellipse(draw, hand, 4.1, 4.3, SKIN, OUTLINE, 1.0)
    # One short index-finger extension for observational gestures.
    direction = 1.0 if hand[0] >= elbow[0] else -1.0
    _line(draw, [hand, (hand[0] + direction * 4.3, hand[1] - 0.5)], SKIN_LIGHT, 1.5)


def _draw_head(base: Image.Image, center: Point, pose: Pose) -> None:
    size = 70 * SUPER
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = blending_draw(layer)
    cx = cy = size / (2 * SUPER)

    def p(point: Point) -> Point:
        return (point[0] * SUPER, point[1] * SUPER)

    # Local helper wrappers use coordinates in logical pixels but draw directly
    # into the already-supersampled local layer.
    def e(c: Point, rx: float, ry: float, fill: RGBA, outline: RGBA | None = OUTLINE, width: float = 1.2) -> None:
        box = (
            int((c[0] - rx) * SUPER),
            int((c[1] - ry) * SUPER),
            int((c[0] + rx) * SUPER),
            int((c[1] + ry) * SUPER),
        )
        draw.ellipse(box, fill=fill, outline=outline, width=_s(width) if outline else 1)

    def l(points: Sequence[Point], fill: RGBA, width: float) -> None:
        draw.line([p(point) for point in points], fill=fill, width=_s(width), joint="curve")

    def poly(points: Sequence[Point], fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.2) -> None:
        pts = [p(point) for point in points]
        draw.polygon(pts, fill=fill)
        draw.line(pts + [pts[0]], fill=outline, width=_s(width), joint="curve")

    # Short silver bob with a hard side part and one darker underlayer.
    e((cx - 1.0, cy - 2.0), 20.0, 22.0, HAIR_DARK, OUTLINE, 1.5)
    poly(
        [
            (cx - 19.0, cy - 2.0),
            (cx - 14.0, cy - 18.0),
            (cx - 3.0, cy - 24.0),
            (cx + 13.0, cy - 20.0),
            (cx + 20.0, cy - 7.0),
            (cx + 18.0, cy + 12.0),
            (cx + 8.0, cy + 17.0),
            (cx - 11.0, cy + 16.0),
            (cx - 19.0, cy + 7.0),
        ],
        HAIR,
        OUTLINE,
        1.5,
    )
    # Face is rounder and older than the existing young-scholar sprites.
    e((cx + 1.0, cy + 2.0), 14.7, 17.0, SKIN, OUTLINE, 1.5)
    e((cx - 14.2, cy + 3.0), 3.3, 5.2, SKIN_SHADE, OUTLINE, 0.8)

    # Silver cap mass and distinct side streak.
    poly(
        [
            (cx - 17.0, cy - 5.0),
            (cx - 11.0, cy - 19.0),
            (cx + 1.0, cy - 23.0),
            (cx + 16.0, cy - 15.0),
            (cx + 18.0, cy - 5.0),
            (cx + 8.0, cy - 10.0),
            (cx - 2.0, cy - 11.0),
            (cx - 10.0, cy - 6.0),
        ],
        HAIR_LIGHT,
        OUTLINE,
        1.1,
    )
    l([(cx - 5.0, cy - 20.0), (cx - 2.0, cy - 7.0)], STAR, 1.2)
    l([(cx + 4.0, cy - 20.0), (cx + 10.0, cy - 7.0)], HAIR, 2.0)

    # Brows and round glasses. The near lens has a brass spectral eyepiece.
    brow_y = cy - 3.5 - pose.brow * 1.4
    l([(cx - 10.5, brow_y), (cx - 3.0, brow_y - 1.0)], HAIR_DARK, 1.4)
    l([(cx + 3.0, brow_y - 1.0), (cx + 11.5, brow_y)], HAIR_DARK, 1.4)
    if pose.blink > 0.5:
        l([(cx - 10.0, cy + 0.5), (cx - 3.5, cy + 0.5)], EYE, 1.3)
        l([(cx + 3.5, cy + 0.5), (cx + 10.0, cy + 0.5)], EYE, 1.3)
    else:
        e((cx - 6.8, cy + 0.4), 1.5, 1.8, EYE, None)
        e((cx + 7.0, cy + 0.3), 1.5, 1.8, EYE, None)
        e((cx - 6.3, cy - 0.2), 0.45, 0.55, STAR, None)
        e((cx + 7.5, cy - 0.3), 0.45, 0.55, STAR, None)
    e((cx - 6.8, cy + 0.2), 7.0, 5.6, GLASS, BRASS_DARK, 1.1)
    e((cx + 7.0, cy + 0.2), 7.0, 5.6, GLASS, BRASS, 1.3)
    l([(cx + 0.2, cy + 0.2), (cx + 0.8, cy + 0.2)], BRASS_DARK, 1.1)
    l([(cx - 13.7, cy - 0.5), (cx - 18.0, cy - 2.0)], BRASS_DARK, 1.1)
    l([(cx + 13.7, cy - 0.5), (cx + 18.0, cy - 2.0)], BRASS_DARK, 1.1)

    if pose.glint > 0.05:
        glint = pose.glint
        l([(cx + 7.0 - glint * 4.0, cy - 5.0), (cx + 7.0 + glint * 4.0, cy + 5.0)], CYAN, 0.8 + glint)
        l([(cx + 7.0 - glint * 4.0, cy + 5.0), (cx + 7.0 + glint * 4.0, cy - 5.0)], STAR, 0.6 + glint * 0.8)

    # Nose, age lines, and mouth.
    l([(cx + 0.5, cy + 1.5), (cx + 2.0, cy + 7.0), (cx + 4.4, cy + 8.0)], SKIN_SHADE, 1.0)
    l([(cx - 12.0, cy + 7.5), (cx - 9.0, cy + 8.8)], SKIN_SHADE, 0.7)
    l([(cx + 10.0, cy + 8.5), (cx + 13.0, cy + 7.5)], SKIN_SHADE, 0.7)
    mouth_y = cy + 12.0
    if pose.mouth > 0.12:
        e((cx + 1.0, mouth_y), 4.8, 1.4 + pose.mouth * 2.0, MOUTH, OUTLINE, 0.7)
    elif pose.smile > 0.15:
        draw.arc(
            (
                int((cx - 5.0) * SUPER),
                int((mouth_y - 2.0) * SUPER),
                int((cx + 7.0) * SUPER),
                int((mouth_y + 5.0) * SUPER),
            ),
            start=10,
            end=170,
            fill=MOUTH,
            width=_s(1.2),
        )
    else:
        l([(cx - 3.5, mouth_y), (cx + 5.0, mouth_y - 0.2)], MOUTH, 1.1)

    # Small brass star earring.
    e((cx - 16.0, cy + 8.5), 1.8, 1.8, BRASS_LIGHT, OUTLINE, 0.6)

    rotated = layer.rotate(-pose.head_tilt, resample=Image.Resampling.BICUBIC, expand=True)
    base.alpha_composite(
        rotated,
        (
            int(center[0] * SUPER - rotated.width / 2),
            int(center[1] * SUPER - rotated.height / 2),
        ),
    )


def _draw_effects(draw: ImageDraw.ImageDraw, pose: Pose, ring_center: Point) -> None:
    # Flat rotation curve: measured points rise, then remain stubbornly flat.
    if pose.curve > 0.02:
        amount = pose.curve
        start = _xf((113.0, 88.0), pose)
        end_x = _lerp(start[0] + 18.0, min(180.0, start[0] + 71.0), amount)
        points = [
            start,
            (start[0] + 10.0, start[1] - 8.0 * amount),
            (start[0] + 22.0, start[1] - 11.0 * amount),
            (end_x, start[1] - 11.0 * amount),
        ]
        _line(draw, points, GOLD, 2.2)
        for index in range(6):
            local = index / 5.0
            x = _lerp(start[0] + 3.0, end_x, local)
            y = start[1] - min(11.0 * amount, local * 28.0 * amount)
            _ellipse(draw, (x, y), 1.8, 1.8, RED if index % 2 else CYAN, OUTLINE, 0.5)

    if pose.lens > 0.02:
        amount = pose.lens
        hand = _xf(pose.near_hand, pose)
        radius = 12.0 + 20.0 * amount
        _arc(draw, hand, radius, radius * 0.70, 194, 342, CYAN, 2.0)
        _arc(draw, hand, radius - 4.0, (radius - 4.0) * 0.70, 198, 338, MAGENTA, 1.6)
        _ellipse(draw, hand, 3.0 + amount * 2.0, 3.0 + amount * 2.0, STAR, BRASS, 0.8)

    if pose.spectrum > 0.02:
        amount = pose.spectrum
        hand = _xf(pose.near_hand, pose)
        length = 16.0 + 30.0 * amount
        _line(draw, [hand, (hand[0] + length, hand[1] - 7.0)], CYAN, 2.0)
        _line(draw, [hand, (hand[0] + length, hand[1] + 7.0)], MAGENTA, 2.0)
        for i in range(4):
            x = hand[0] + length * (i + 1) / 4.0
            _line(draw, [(x, hand[1] - 6.0), (x, hand[1] + 6.0)], STAR, 0.7)

    if pose.halo > 0.02:
        amount = pose.halo
        rx = 54.0 + amount * 24.0
        ry = 38.0 + amount * 15.0
        _arc(draw, ring_center, rx, ry, 0, 360, CYAN_SOFT, 5.0)
        _arc(draw, ring_center, rx - 7.0, ry - 5.0, 0, 360, MAGENTA_SOFT, 3.0)
        for index in range(12):
            angle = index / 12.0 * math.tau + pose.ring_phase
            point = (ring_center[0] + math.cos(angle) * rx, ring_center[1] + math.sin(angle) * ry)
            fill = CYAN if index % 3 else MAGENTA
            _ellipse(draw, point, 1.7 + amount, 1.7 + amount, fill, OUTLINE, 0.4)

    if pose.counter > 0.02:
        amount = pose.counter
        rx = 52.0 + amount * 12.0
        ry = 26.0 + amount * 8.0
        _arc(draw, ring_center, rx, ry, 20, 200, CYAN, 2.2)
        _arc(draw, ring_center, rx, ry, 205, 380, MAGENTA, 2.2)
        for direction, fill, phase in ((1.0, CYAN, pose.ring_phase), (-1.0, MAGENTA, -pose.ring_phase * 1.3)):
            angle = phase * math.tau * direction
            point = (ring_center[0] + math.cos(angle) * rx, ring_center[1] + math.sin(angle) * ry)
            _ellipse(draw, point, 3.0, 3.0, fill, OUTLINE, 0.7)
            tail = (ring_center[0] + math.cos(angle - direction * 0.2) * rx, ring_center[1] + math.sin(angle - direction * 0.2) * ry)
            _line(draw, [tail, point], fill, 1.5)

    if pose.starfield > 0.02:
        amount = pose.starfield
        stars = [
            (54.0, 54.0),
            (138.0, 48.0),
            (153.0, 109.0),
            (39.0, 112.0),
            (67.0, 142.0),
            (135.0, 145.0),
        ]
        for index, star in enumerate(stars):
            twinkle = 0.45 + 0.55 * math.sin((pose.ring_phase * 3.0 + index * 0.17) * math.tau) ** 2
            size = 0.7 + amount * twinkle * 1.8
            _ellipse(draw, star, size, size, STAR if index % 2 else CYAN, None)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    pose = _pose(animation, frame_idx, frame_count)
    canvas = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    draw = blending_draw(canvas)

    ring_center = _xf((96.0, 80.0), pose)
    _draw_back_ring(draw, ring_center, pose)

    # Far leg, near leg, then coat and arms. This order makes the spectrograph
    # ring read as mounted around one coherent body rather than pasted on top.
    _draw_leg(
        draw,
        _xf(pose.far_hip, pose),
        _xf(pose.far_knee, pose),
        _xf(pose.far_ankle, pose),
        False,
    )
    _draw_leg(
        draw,
        _xf(pose.near_hip, pose),
        _xf(pose.near_knee, pose),
        _xf(pose.near_ankle, pose),
        True,
    )
    _draw_coat(draw, pose)

    _draw_arm(
        draw,
        _xf(pose.far_shoulder, pose),
        _xf(pose.far_elbow, pose),
        _xf(pose.far_hand, pose),
        False,
    )
    _draw_arm(
        draw,
        _xf(pose.near_shoulder, pose),
        _xf(pose.near_elbow, pose),
        _xf(pose.near_hand, pose),
        True,
    )

    _draw_front_ring(draw, ring_center, pose)
    _draw_head(canvas, _xf(pose.head, pose), pose)
    draw = blending_draw(canvas)
    _draw_effects(draw, pose, ring_center)

    return canvas.resize((FRAME_W, FRAME_H), Image.Resampling.LANCZOS)


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
