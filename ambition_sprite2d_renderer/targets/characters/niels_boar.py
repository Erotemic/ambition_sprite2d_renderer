"""Procedural full-action renderer for Niels Boar.

Niels Boar is an affectionate fighting-game parody of Danish physicist Niels
Bohr.  He is a compact, dignified anthropomorphic boar in a dark three-piece
suit, with a swept bristle crest, broad thoughtful brow, and prominent tusks.
Three luminous orbital planes surround his body even at rest, making the Bohr
model readable in silhouette rather than relegating the science joke to VFX.

The authored combat language treats the familiar planetary atom as a visual
starting point, not a claim that it is the final modern description of atomic
structure.  Electrons jump between discrete shells, released energy appears as
photons, and complementarity is staged as alternating wave and particle forms.
His heaviest attack deliberately exaggerates the correspondence principle: a
clean classical orbit grows into an unapologetically physical boar charge.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.sheet_build import build_sheet, write_canonical
from ...core.draw import blending_draw
from . import _solo_shape_rig as SR

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "niels_boar"
DESIGN_SIZE = (144, 144)
DESIGN_OFFSET = 16.0
FRAME_SIZE = (176, 176)
SUPER = 3
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER
USES_DROP_SHADOW = False
USES_PROPS = False

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 145),
    ("walk", 8, 100),
    ("run", 8, 76),
    ("crouch", 6, 94),
    ("crouch_walk", 8, 88),
    ("jump", 6, 90),
    ("fall", 6, 90),
    ("land_hard", 8, 86),
    ("land_recovery", 6, 70),
    ("dash_startup", 4, 48),
    ("dash", 6, 58),
    ("slide", 6, 66),
    ("roll", 8, 54),
    ("wall_grab", 6, 102),
    ("wall_jump", 6, 80),
    ("ledge_grab", 6, 96),
    ("ledge_climb", 6, 96),
    ("ledge_getup", 6, 42),
    ("ledge_roll", 8, 38),
    ("climb", 8, 96),
    ("swim", 8, 100),
    ("float_glide", 8, 105),
    ("block", 6, 80),
    ("hit", 5, 84),
    ("death", 8, 104),
    ("talk", 8, 102),
    ("interact", 8, 88),
    ("tusk_jab", 7, 60),
    ("orbital_sweep", 8, 68),
    ("shell_shift", 9, 74),
    ("quantum_leap", 9, 70),
    ("complementarity", 10, 76),
    ("correspondence_charge", 10, 66),
    ("air_neutral", 8, 60),
    ("air_forward", 7, 58),
    ("air_back", 7, 58),
    ("air_down", 7, 66),
    ("air_up", 7, 58),
    ("celebrate", 8, 88),
    ("taunt", 8, 94),
]

AUTHORING_DESCRIPTION = (
    "Niels Boar is an affectionate parody of Danish physicist Niels Bohr. The "
    "boar transformation turns the sound of Bohr's surname into a compact, "
    "tusked fighting-game silhouette while retaining a formal early-twentieth-"
    "century scientific presentation: dark three-piece suit, restrained bow "
    "tie, broad reflective expression, and swept bristle crest. Three luminous "
    "orbital planes reference the familiar Bohr model of the atom. They are "
    "kept visible during ordinary poses so the scientific idea is readable in "
    "the sprite itself. Shell Shift depicts a discrete transition and emitted "
    "photon; Complementarity alternates wave and particle imagery; Quantum "
    "Leap exaggerates a discontinuous state change into teleport-like movement; "
    "and Correspondence Charge turns the passage toward classical behavior into "
    "a literal boar rush. These are playful gameplay metaphors, not claims that "
    "the old planetary atom is the complete modern theory."
)

GAMEPLAY_DESCRIPTION = (
    "A compact medium-heavy control fighter whose orbiting electrons double as "
    "close defense, delayed projectiles, and state indicators. Niels Boar wants "
    "to hold a deliberate midrange, shift electrons between shells to release "
    "photons, and alternate wave-shaped area control with particle-like direct "
    "hits. His tusks give him dependable grounded melee, while Quantum Leap is "
    "a short discontinuous reposition rather than sustained mobility."
)

SUGGESTED_BARKS = [
    "A small jump. A definite consequence.",
    "The orbit is only the picture.",
    "Now observe the transition.",
    "Wave or particle? Choose your question carefully.",
    "Classical manners, quantum behavior.",
    "Do not confuse certainty with understanding.",
    "There is room for both descriptions.",
]

FALLBACK_DIALOGUE = [
    "A model may be useful without being the last word.",
    "The difficult part is deciding what can meaningfully be asked.",
    "My electrons are better behaved than most dinner guests.",
    "Please stop calling every sudden movement a quantum leap.",
    "The tusks are classical. The timing is not.",
]

ACTOR_METADATA = {
    "authoring_description": AUTHORING_DESCRIPTION,
    "gameplay_description": GAMEPLAY_DESCRIPTION,
    "dialogue_hints": {
        "barks": SUGGESTED_BARKS,
        "fallback": FALLBACK_DIALOGUE,
    },
    "actor": {
        "character_id": "npc_niels_boar",
        "actor_id": "niels_boar",
        "display_name": "Niels Boar",
    },
    "lineage": {
        "family": "niels_boar",
        "variant": "orbital_boar_physicist",
        "creator": {"kind": "model", "model": "GPT-5.6 Thinking"},
        "method": "procedural_python_pillow",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "locomotion_hint": "Walk",
        "traits": [
            "story",
            "animal",
            "boar",
            "physicist",
            "orbital_controller",
            "tusk_melee",
            "playable_candidate",
        ],
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
            "door_access": ["public", "laboratory"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public", "laboratory"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "face_guide": {
            "center": {"x": 88.0, "y": 55.0},
            "size": {"w": 48.0, "h": 42.0},
            "source_size": {"w": 176.0, "h": 176.0},
        },
    },
    "tags": [
        "story",
        "animal",
        "boar",
        "physicist",
        "orbital_controller",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.profile.boar", "point": {"x": 88.0, "y": 55.0}},
        "chest": {"source": "explicit.profile.boar", "point": {"x": 88.0, "y": 92.0}},
        "hand_l": {"source": "explicit.profile.boar", "point": {"x": 64.0, "y": 104.0}},
        "hand_r": {"source": "explicit.profile.boar", "point": {"x": 112.0, "y": 104.0}},
        "tusk": {"source": "explicit.profile.boar", "point": {"x": 114.0, "y": 65.0}},
        "projectile_origin": {"source": "explicit.orbit", "point": {"x": 129.0, "y": 86.0}},
        "speech_bubble": {"source": "explicit.profile.boar", "point": {"x": 88.0, "y": 21.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "tusk_jab", "events": []},
        "action.melee.secondary": {"animation": "correspondence_charge", "events": []},
        "action.ranged.primary": {"animation": "shell_shift", "events": []},
        "action.special.primary": {"animation": "complementarity", "events": []},
        "action.special.secondary": {"animation": "quantum_leap", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}

SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
    f"{TARGET_NAME}_portraits.png",
    f"{TARGET_NAME}_portraits.ron",
]

OUTLINE: RGBA = (22, 17, 19, 255)
OUTLINE_SOFT: RGBA = (58, 42, 43, 255)
FUR_DARK: RGBA = (67, 44, 39, 255)
FUR_MID: RGBA = (105, 67, 52, 255)
FUR_LIGHT: RGBA = (153, 104, 76, 255)
FUR_HIGHLIGHT: RGBA = (191, 140, 101, 255)
SNOUT: RGBA = (188, 123, 105, 255)
SNOUT_LIGHT: RGBA = (220, 158, 132, 255)
NOSTRIL: RGBA = (49, 29, 31, 255)
TUSK: RGBA = (239, 226, 185, 255)
TUSK_SHADE: RGBA = (191, 175, 139, 255)
EYE_WHITE: RGBA = (244, 235, 211, 255)
EYE: RGBA = (28, 25, 26, 255)
SUIT_DARK: RGBA = (31, 39, 58, 255)
SUIT: RGBA = (45, 58, 82, 255)
SUIT_LIGHT: RGBA = (70, 84, 109, 255)
SHIRT: RGBA = (227, 222, 201, 255)
BOW: RGBA = (156, 68, 57, 255)
BOW_LIGHT: RGBA = (208, 105, 79, 255)
SHOE: RGBA = (40, 30, 31, 255)
RING_BLUE: RGBA = (79, 177, 225, 210)
RING_CYAN: RGBA = (93, 220, 208, 195)
RING_VIOLET: RGBA = (155, 119, 227, 190)
ELECTRON: RGBA = (242, 248, 255, 255)
ELECTRON_GLOW: RGBA = (118, 220, 255, 150)
PHOTON: RGBA = (255, 213, 91, 255)
PHOTON_GLOW: RGBA = (255, 230, 131, 120)
WAVE: RGBA = (104, 194, 240, 205)
PARTICLE: RGBA = (238, 179, 93, 235)


def _s(value: float) -> int:
    return int(round(value * SUPER))


def _pt(x: float, y: float) -> Tuple[int, int]:
    return (_s(x + DESIGN_OFFSET), _s(y + DESIGN_OFFSET))


def _box(x1: float, y1: float, x2: float, y2: float) -> Tuple[int, int, int, int]:
    return (
        _s(x1 + DESIGN_OFFSET),
        _s(y1 + DESIGN_OFFSET),
        _s(x2 + DESIGN_OFFSET),
        _s(y2 + DESIGN_OFFSET),
    )


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smooth(value: float) -> float:
    value = _clamp01(value)
    return value * value * (3.0 - 2.0 * value)


def _pulse(value: float) -> float:
    return math.sin(_clamp01(value) * math.pi)


def _lerp(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def _rotate(point: Point, degrees: float) -> Point:
    angle = math.radians(degrees)
    c = math.cos(angle)
    s = math.sin(angle)
    return (point[0] * c - point[1] * s, point[0] * s + point[1] * c)


@dataclass
class Pose:
    body_x: float = 0.0
    body_y: float = 0.0
    body_angle: float = 0.0
    squash_x: float = 1.0
    squash_y: float = 1.0
    head_x: float = 0.0
    head_y: float = 0.0
    head_angle: float = 0.0
    blink: bool = False
    mouth_open: float = 0.0
    brow: float = 0.0
    near_hand: Point = (96.0, 87.0)
    far_hand: Point = (48.0, 88.0)
    near_foot: Point = (88.0, 132.0)
    far_foot: Point = (58.0, 132.0)
    ring_scale: float = 1.0
    ring_alpha: float = 1.0
    ring_spin: float = 0.0
    ring_center_x: float = 0.0
    ring_center_y: float = 0.0
    electron_boost: float = 0.0
    body_alpha: float = 1.0
    effect: str = ""
    effect_t: float = 0.0


def _pose(animation: str, frame_idx: int, nframes: int) -> Pose:
    p = Pose()
    phase = frame_idx / max(1, nframes)
    t = frame_idx / max(1, nframes - 1)
    wave = math.sin(phase * math.tau)
    cosine = math.cos(phase * math.tau)
    p.ring_spin = phase * 16.0

    if animation == "idle":
        breath = 0.5 - 0.5 * cosine
        p.body_y = -0.8 * breath
        p.head_y = -0.4 * breath
        p.head_angle = 0.8 * wave
        p.ring_scale = 1.0 + 0.025 * breath
        p.ring_spin += 2.5 * wave
        p.blink = frame_idx == 6

    elif animation in {"walk", "crouch_walk"}:
        crouch = animation == "crouch_walk"
        stride = (8.0 if crouch else 10.0) * wave
        p.body_y = (7.0 if crouch else 0.0) - 1.5 * abs(wave)
        p.body_angle = -2.0 * wave
        p.head_angle = 1.4 * wave
        p.near_foot = (88.0 + stride, 132.0 - max(0.0, wave) * 5.0)
        p.far_foot = (58.0 - stride, 132.0 - max(0.0, -wave) * 5.0)
        p.near_hand = (96.0 - stride * 0.55, 87.0 + 2.0 * wave + (5.0 if crouch else 0.0))
        p.far_hand = (48.0 + stride * 0.5, 88.0 - 2.0 * wave + (5.0 if crouch else 0.0))
        p.ring_scale = 0.9 if crouch else 1.0

    elif animation == "run":
        stride = 14.0 * wave
        p.body_x = 2.0 * wave
        p.body_y = -2.8 * abs(wave)
        p.body_angle = -7.0
        p.head_angle = 4.0 * wave
        p.near_foot = (89.0 + stride, 132.0 - max(0.0, wave) * 8.0)
        p.far_foot = (57.0 - stride, 132.0 - max(0.0, -wave) * 8.0)
        p.near_hand = (97.0 - stride * 0.65, 86.0)
        p.far_hand = (47.0 + stride * 0.65, 88.0)
        p.ring_scale = 0.94
        p.ring_spin += 18.0 * wave

    elif animation == "crouch":
        settle = _smooth(t)
        p.body_y = 8.0 * settle
        p.squash_y = 1.0 - 0.09 * settle
        p.squash_x = 1.0 + 0.06 * settle
        p.near_hand = (94.0, 95.0)
        p.far_hand = (50.0, 95.0)
        p.ring_scale = 1.0 - 0.16 * settle

    elif animation in {"jump", "fall", "float_glide"}:
        if animation == "jump":
            p.body_y = -10.0 * _smooth(t)
            p.body_angle = -4.0 + 6.0 * t
        elif animation == "fall":
            p.body_y = -5.0 + 7.0 * t
            p.body_angle = 3.0
        else:
            p.body_y = -7.0 + 1.2 * wave
            p.body_angle = -1.5 * wave
            p.ring_scale = 1.22
            p.ring_spin += 40.0 * phase
        p.near_foot = (86.0, 124.0)
        p.far_foot = (60.0, 123.0)
        p.near_hand = (103.0, 78.0)
        p.far_hand = (42.0, 80.0)

    elif animation in {"land_hard", "land_recovery"}:
        impact = _pulse(t) if animation == "land_hard" else 1.0 - _smooth(t)
        p.body_y = 8.0 * impact
        p.squash_x = 1.0 + 0.12 * impact
        p.squash_y = 1.0 - 0.16 * impact
        p.near_hand = (99.0, 98.0)
        p.far_hand = (45.0, 98.0)
        p.ring_scale = 1.0 + 0.18 * impact

    elif animation in {"dash_startup", "dash"}:
        u = _smooth(t)
        p.body_angle = -14.0 * u if animation == "dash_startup" else -14.0 + 2.0 * wave
        p.body_x = 4.0 * u if animation == "dash_startup" else 4.0 + 2.0 * wave
        p.body_y = 4.0 * u
        p.near_hand = (87.0, 92.0)
        p.far_hand = (44.0, 92.0)
        p.near_foot = (94.0, 132.0)
        p.far_foot = (61.0, 132.0)
        p.ring_scale = 0.82
        p.ring_spin += 55.0 * t

    elif animation in {"slide", "roll", "ledge_roll"}:
        p.effect = animation
        p.effect_t = t
        p.body_y = 4.0 * _pulse(t)
        p.body_angle = 18.0 * _pulse(t) if animation == "slide" else 360.0 * t
        p.squash_x = 1.12
        p.squash_y = 0.82
        p.near_hand = (91.0, 96.0)
        p.far_hand = (52.0, 97.0)
        p.near_foot = (92.0, 128.0)
        p.far_foot = (60.0, 128.0)
        p.ring_scale = 0.76
        p.ring_spin += 180.0 * t

    elif animation in {"wall_grab", "ledge_grab"}:
        p.body_x = 8.0
        p.body_y = -4.0 + 1.0 * wave
        p.body_angle = 4.0
        p.near_hand = (109.0, 65.0)
        p.far_hand = (105.0, 82.0)
        p.near_foot = (91.0, 116.0)
        p.far_foot = (82.0, 126.0)
        p.ring_scale = 0.82

    elif animation in {"wall_jump", "ledge_climb", "ledge_getup"}:
        u = _smooth(t)
        p.body_x = _lerp(8.0, -5.0, u)
        p.body_y = _lerp(-4.0, -15.0 if animation == "wall_jump" else -2.0, u)
        p.body_angle = _lerp(4.0, -18.0 if animation == "wall_jump" else 0.0, u)
        p.near_hand = (_lerp(109.0, 96.0, u), _lerp(65.0, 84.0, u))
        p.far_hand = (_lerp(105.0, 48.0, u), _lerp(82.0, 87.0, u))
        p.ring_scale = 0.84 + 0.16 * u

    elif animation == "climb":
        p.body_y = -2.0 * wave
        p.near_hand = (95.0, 68.0 + 12.0 * wave)
        p.far_hand = (50.0, 68.0 - 12.0 * wave)
        p.near_foot = (87.0, 125.0 - 7.0 * wave)
        p.far_foot = (59.0, 125.0 + 7.0 * wave)
        p.ring_scale = 0.82

    elif animation == "swim":
        p.body_y = -4.0 + 2.0 * wave
        p.body_angle = -13.0 + 3.0 * wave
        p.near_hand = (104.0 + 7.0 * wave, 78.0)
        p.far_hand = (42.0 - 7.0 * wave, 81.0)
        p.near_foot = (89.0 - 8.0 * wave, 122.0)
        p.far_foot = (58.0 + 8.0 * wave, 123.0)
        p.ring_scale = 0.9

    elif animation == "block":
        guard = 0.8 + 0.2 * _pulse(t)
        p.near_hand = (91.0, 67.0)
        p.far_hand = (55.0, 67.0)
        p.body_y = 3.0
        p.ring_scale = 0.70 * guard
        p.ring_alpha = 1.0
        p.electron_boost = 1.0
        p.effect = "block"
        p.effect_t = t

    elif animation == "hit":
        impact = _pulse(t)
        p.body_x = -7.0 * impact
        p.body_y = -2.0 * impact
        p.body_angle = -9.0 * impact
        p.head_angle = -12.0 * impact
        p.ring_scale = 1.0 + 0.2 * impact
        p.ring_alpha = 1.0 - 0.45 * impact
        p.mouth_open = 0.7 * impact
        p.brow = 1.0

    elif animation == "death":
        p.effect = "death"
        p.effect_t = t
        if t < 0.58:
            u = _smooth(t / 0.58)
            p.body_x = -8.0 * u
            p.body_y = 11.0 * u
            p.body_angle = -62.0 * u
            p.ring_scale = 1.0 + 0.35 * u
            p.ring_alpha = 1.0 - 0.75 * u
        else:
            u = (t - 0.58) / 0.42
            p.body_x = -14.0
            p.body_y = 6.0 + 2.0 * u
            p.body_angle = -62.0 - 4.0 * u
            p.ring_alpha = 0.25 * (1.0 - u)
            p.blink = True
        p.mouth_open = 0.2

    elif animation == "talk":
        p.body_y = -0.5 * abs(wave)
        p.head_angle = 2.0 * wave
        p.mouth_open = 0.25 + 0.45 * max(0.0, wave)
        p.near_hand = (99.0 + 5.0 * wave, 76.0 - 5.0 * abs(wave))
        p.brow = -0.4 * wave

    elif animation == "interact":
        reach = _pulse(t)
        p.body_angle = -4.0 * reach
        p.near_hand = (96.0 + 18.0 * reach, 86.0 - 8.0 * reach)
        p.head_angle = -4.0 * reach
        p.ring_center_x = 3.0 * reach

    elif animation == "tusk_jab":
        strike = _pulse(t)
        p.body_x = 12.0 * strike
        p.body_y = 2.0 * strike
        p.body_angle = -13.0 * strike
        p.head_x = 8.0 * strike
        p.head_angle = -7.0 * strike
        p.near_hand = (88.0, 91.0)
        p.far_hand = (48.0, 92.0)
        p.ring_scale = 1.0 - 0.22 * strike
        p.effect = "tusk_jab"
        p.effect_t = t
        p.brow = -1.0

    elif animation == "orbital_sweep":
        sweep = _smooth(t)
        p.body_angle = -5.0 + 10.0 * _pulse(t)
        p.near_hand = (103.0 + 7.0 * _pulse(t), 69.0)
        p.far_hand = (43.0, 84.0)
        p.ring_scale = 1.0 + 0.48 * _pulse(t)
        p.ring_spin += 210.0 * sweep
        p.electron_boost = 1.0
        p.effect = "orbital_sweep"
        p.effect_t = t

    elif animation == "shell_shift":
        p.near_hand = (104.0, 71.0)
        p.far_hand = (48.0, 79.0)
        p.ring_scale = 1.0 + 0.08 * _pulse(t)
        p.electron_boost = 1.0
        p.effect = "shell_shift"
        p.effect_t = t
        p.head_angle = -3.0 * _pulse(t)

    elif animation == "quantum_leap":
        p.effect = "quantum_leap"
        p.effect_t = t
        if t < 0.33:
            u = _smooth(t / 0.33)
            p.body_y = -5.0 * u
            p.body_alpha = 1.0 - 0.85 * u
            p.ring_scale = 1.0 - 0.65 * u
        elif t < 0.66:
            p.body_y = -14.0
            p.body_x = 8.0
            p.body_alpha = 0.15
            p.ring_scale = 0.30
            p.ring_spin += 250.0 * t
        else:
            u = _smooth((t - 0.66) / 0.34)
            p.body_x = 8.0 * (1.0 - u)
            p.body_y = -14.0 * (1.0 - u)
            p.body_alpha = 0.15 + 0.85 * u
            p.ring_scale = 0.30 + 0.70 * u

    elif animation == "complementarity":
        p.effect = "complementarity"
        p.effect_t = t
        p.near_hand = (104.0, 74.0)
        p.far_hand = (40.0, 74.0)
        p.ring_scale = 1.05 + 0.12 * _pulse(t)
        p.ring_spin += 80.0 * t
        p.brow = -0.5

    elif animation == "correspondence_charge":
        charge = _smooth(min(1.0, t / 0.42))
        rush = _smooth(max(0.0, (t - 0.35) / 0.65))
        p.effect = "correspondence_charge"
        p.effect_t = t
        p.body_x = -5.0 * charge + 16.0 * rush
        p.body_y = 3.0 * charge
        p.body_angle = 8.0 * charge - 20.0 * rush
        p.head_x = 5.0 * rush
        p.near_hand = (87.0, 93.0)
        p.far_hand = (48.0, 94.0)
        p.ring_scale = 1.0 + 0.5 * charge - 0.55 * rush
        p.ring_spin += 260.0 * t
        p.brow = -1.2
        p.mouth_open = 0.5 * rush

    elif animation.startswith("air_"):
        p.body_y = -7.0 + 1.0 * wave
        p.near_foot = (87.0, 123.0)
        p.far_foot = (60.0, 123.0)
        p.ring_scale = 1.05
        p.effect = animation
        p.effect_t = t
        direction = {"air_forward": -13.0, "air_back": 13.0, "air_down": 4.0, "air_up": -4.0}.get(animation, 0.0)
        p.body_angle = direction * _pulse(t)
        if animation == "air_down":
            p.body_y += 8.0 * _pulse(t)
        elif animation == "air_up":
            p.body_y -= 8.0 * _pulse(t)
        p.ring_spin += 160.0 * t

    elif animation == "celebrate":
        lift = _pulse(t)
        p.body_y = -6.0 * lift
        p.near_hand = (100.0, 55.0 - 6.0 * lift)
        p.far_hand = (44.0, 55.0 - 6.0 * lift)
        p.ring_scale = 1.0 + 0.25 * lift
        p.electron_boost = 1.0
        p.mouth_open = 0.45

    elif animation == "taunt":
        p.near_hand = (101.0, 77.0)
        p.far_hand = (46.0, 86.0)
        p.head_angle = -4.0 + 2.0 * wave
        p.brow = -0.8
        p.mouth_open = 0.15 + 0.25 * max(0.0, wave)
        p.ring_scale = 0.94 + 0.03 * wave
        p.effect = "taunt"
        p.effect_t = t

    return p


def _orbit_point(center: Point, rx: float, ry: float, angle: float, theta: float) -> Point:
    local = (rx * math.cos(theta), ry * math.sin(theta))
    rotated = _rotate(local, angle)
    return (center[0] + rotated[0], center[1] + rotated[1])


def _ring_piece(rx: float, ry: float, color: RGBA):
    """One orbital plane, unturned, centred on its pivot."""
    pad = _s(max(rx, ry) + 3.0)

    def paint(d) -> None:
        d.ellipse((pad - _s(rx), pad - _s(ry), pad + _s(rx), pad + _s(ry)), outline=color, width=max(1, _s(1.15)))

    return shape_rig.piece(("niels_ring", rx, ry, color), (2 * pad, 2 * pad), (pad, pad), paint)


def _electron_piece(color: RGBA, electron_scale: float):
    pad = _s(5.2 * electron_scale + 2.0)

    def paint(d) -> None:
        g, c = 5.2 * electron_scale, 2.2 * electron_scale
        d.ellipse((pad - _s(g), pad - _s(g), pad + _s(g), pad + _s(g)), fill=ELECTRON_GLOW)
        d.ellipse((pad - _s(c), pad - _s(c), pad + _s(c), pad + _s(c)), fill=ELECTRON, outline=(color[0], color[1], color[2], 255), width=max(1, _s(0.65)))

    return shape_rig.piece(("niels_electron", color, electron_scale), (2 * pad, 2 * pad), (pad, pad), paint)


def _draw_orbits(img: Image.Image, p: Pose, foreground: bool = False) -> None:
    """The orbital planes as turned pieces (one per plane and scale step) and
    their electrons riding them, faded by the pose's ring alpha."""
    center = (72.0 + p.body_x + p.ring_center_x, 76.0 + p.body_y + p.ring_center_y)
    scale = SR.q(max(0.12, p.ring_scale), 0.05)
    electron_scale = 1.0 + 0.35 * p.electron_boost
    alpha = _clamp01(p.ring_alpha)
    specs = [
        (44.0, 15.0, -12.0 + p.ring_spin, RING_BLUE, 0.6),
        (39.0, 17.0, 55.0 + p.ring_spin * 0.73, RING_CYAN, 2.8),
        (35.0, 14.0, -58.0 - p.ring_spin * 0.55, RING_VIOLET, 4.7),
    ]
    for idx, (rx, ry, angle, color, phase) in enumerate(specs):
        # The far two planes live behind the body; one electron is redrawn in
        # front to preserve the readable atom without flattening the character.
        if foreground != (idx == 0):
            continue
        rx, ry = round(rx * scale, 2), round(ry * scale, 2)
        at = (_s(center[0] + DESIGN_OFFSET), _s(center[1] + DESIGN_OFFSET))
        SR.place(img, _ring_piece(rx, ry, color), at, -angle, f"ring{idx}", alpha)
        ex, ey = _orbit_point(center, rx, ry, angle, phase + math.radians(p.ring_spin * (1.1 + idx * 0.2)))
        SR.place(img, _electron_piece(color, round(electron_scale, 2)), (_s(ex + DESIGN_OFFSET), _s(ey + DESIGN_OFFSET)), 0.0, f"electron{idx}", alpha)


# Limb bones (frame pixels at SUPER): fixed lengths, IK-bent toward the
# old elbow/knee offset; a reach past both bones stretches them a step.
LEG_BONE = 9.0 * SUPER
ARM_BONE = 6.0 * SUPER


def _sp(x: float, y: float) -> Point:
    """A design point in supersampled canvas pixels, unrounded."""
    return ((x + DESIGN_OFFSET) * SUPER, (y + DESIGN_OFFSET) * SUPER)


def _draw_leg(canvas: Image.Image, T: SR.Xform, hip: Point, foot: Point, far: bool, alpha: float = 1.0) -> None:
    fx, fy = foot
    suit = SUIT_DARK if far else SUIT
    side = "far" if far else "near"
    root, target = T.pt(_sp(*hip)), T.pt(_sp(fx, fy - 4.0))
    SR.limb(canvas, root, target, LEG_BONE, T.vec((-1.0 if far else 1.0, 0.0)), 4.0 * SUPER, suit, OUTLINE, 2.0 * SUPER, f"{side}_leg", opacity=alpha)
    pivot = _pt(88.0, 132.0)

    def paint(d) -> None:
        d.ellipse(_box(88.0 - 8.0, 132.0 - 5.0, 88.0 + 8.5, 132.0 + 2.0), fill=SHOE, outline=OUTLINE, width=_s(1.0))

    SR.place(canvas, SR.rest_piece(("niels_shoe",), (W, H), pivot, paint), T.pt(_sp(fx, fy)), T.deg, f"{side}_shoe", alpha)


def _draw_arm(canvas: Image.Image, T: SR.Xform, shoulder: Point, hand: Point, far: bool, alpha: float = 1.0) -> None:
    hx, hy = hand
    suit = SUIT_DARK if far else SUIT
    side = "far" if far else "near"
    root, target = T.pt(_sp(*shoulder)), T.pt(_sp(hx, hy))
    SR.limb(canvas, root, target, ARM_BONE, T.vec((-1.0 if far else 1.0, 0.3)), 3.5 * SUPER, suit, OUTLINE, 2.0 * SUPER, f"{side}_arm", opacity=alpha)
    pivot = _pt(96.0, 87.0)

    def paint(d) -> None:
        x, y = 96.0, 87.0
        d.ellipse(_box(x - 5.0, y - 4.5, x + 5.5, y + 5.0), fill=FUR_MID, outline=OUTLINE, width=_s(1.0))
        for dy in (-1.5, 1.2):
            d.line([_pt(x + 0.5, y + dy), _pt(x + 4.5, y + dy + 0.5)], fill=FUR_HIGHLIGHT, width=_s(0.7))

    SR.place(canvas, SR.rest_piece(("niels_hand",), (W, H), pivot, paint), T.pt(_sp(hx, hy)), T.deg, f"{side}_hand", alpha)


def _paint_torso(draw) -> None:
    """The stocky torso under its three-piece suit, at rest (body offset 0)."""
    torso = [(52.0, 68.0), (64.0, 61.0), (83.0, 61.0), (96.0, 70.0), (102.0, 96.0), (94.0, 116.0), (76.0, 123.0), (58.0, 117.0), (47.0, 97.0), (47.0, 79.0)]
    draw.polygon([_pt(*q) for q in torso], fill=SUIT_DARK, outline=OUTLINE)
    jacket = [(52.0, 71.0), (64.0, 63.0), (72.0, 70.0), (82.0, 63.0), (96.0, 72.0), (98.0, 99.0), (88.0, 113.0), (73.0, 108.0), (58.0, 114.0), (49.0, 99.0)]
    draw.polygon([_pt(*q) for q in jacket], fill=SUIT, outline=OUTLINE)
    draw.polygon([_pt(60.0, 68.0), _pt(71.0, 74.0), _pt(66.0, 104.0), _pt(54.0, 96.0)], fill=SUIT_LIGHT)
    draw.polygon([_pt(85.0, 68.0), _pt(74.0, 74.0), _pt(79.0, 104.0), _pt(95.0, 96.0)], fill=SUIT_LIGHT)
    draw.polygon([_pt(65.0, 64.0), _pt(72.0, 72.0), _pt(81.0, 64.0), _pt(78.0, 82.0), _pt(68.0, 82.0)], fill=SHIRT, outline=OUTLINE)
    draw.polygon([_pt(66.0, 73.0), _pt(72.0, 76.0), _pt(66.0, 80.0), _pt(62.0, 76.0)], fill=BOW, outline=OUTLINE)
    draw.polygon([_pt(78.0, 73.0), _pt(72.0, 76.0), _pt(78.0, 80.0), _pt(82.0, 76.0)], fill=BOW_LIGHT, outline=OUTLINE)
    draw.ellipse(_box(69.5, 73.5, 74.5, 78.5), fill=BOW_LIGHT, outline=OUTLINE, width=_s(0.7))
    for yy in (90.0, 101.0):
        draw.ellipse(_box(71.0, yy, 74.0, yy + 3.0), fill=(198, 174, 103, 255))


def _paint_head(hd, blink: bool, mouth_open: float, brow: float) -> None:
    """Head and crest at rest (centre (73, 42)), for one expression."""
    hx, hy = 73.0, 42.0
    # Ears behind the head.
    hd.polygon([_pt(hx - 23.0, hy - 13.0), _pt(hx - 33.0, hy - 25.0), _pt(hx - 14.0, hy - 22.0)], fill=FUR_DARK, outline=OUTLINE)
    hd.polygon([_pt(hx + 20.0, hy - 14.0), _pt(hx + 31.0, hy - 25.0), _pt(hx + 12.0, hy - 22.0)], fill=FUR_DARK, outline=OUTLINE)
    hd.polygon([_pt(hx - 22.0, hy - 16.0), _pt(hx - 29.0, hy - 22.0), _pt(hx - 16.0, hy - 20.0)], fill=SNOUT)
    hd.polygon([_pt(hx + 19.0, hy - 16.0), _pt(hx + 27.0, hy - 22.0), _pt(hx + 14.0, hy - 20.0)], fill=SNOUT)
    hd.ellipse(_box(hx - 27.0, hy - 24.0, hx + 28.0, hy + 24.0), fill=FUR_DARK, outline=OUTLINE, width=_s(1.5))
    hd.ellipse(_box(hx - 22.0, hy - 18.0, hx + 23.0, hy + 20.0), fill=FUR_MID)

    # Swept Bohr-like bristle crest, a restrained historical caricature rather
    # than a generic punk mane.
    crest = [
        (hx - 22.0, hy - 18.0),
        (hx - 18.0, hy - 31.0),
        (hx - 9.0, hy - 24.0),
        (hx - 3.0, hy - 35.0),
        (hx + 4.0, hy - 25.0),
        (hx + 13.0, hy - 32.0),
        (hx + 18.0, hy - 20.0),
        (hx + 5.0, hy - 13.0),
        (hx - 9.0, hy - 12.0),
    ]
    hd.polygon([_pt(*q) for q in crest], fill=OUTLINE_SOFT, outline=OUTLINE)
    hd.line([_pt(hx - 16.0, hy - 22.0), _pt(hx + 12.0, hy - 18.0)], fill=FUR_LIGHT, width=_s(1.2))

    eye_y = hy - 3.0
    for ex, far in ((hx - 9.0, True), (hx + 8.0, False)):
        if blink:
            hd.line([_pt(ex - 3.5, eye_y), _pt(ex + 3.5, eye_y + 0.5)], fill=OUTLINE, width=_s(1.2))
        else:
            hd.ellipse(_box(ex - 4.0, eye_y - 4.0, ex + 4.0, eye_y + 4.2), fill=EYE_WHITE, outline=OUTLINE, width=_s(0.8))
            hd.ellipse(_box(ex + (0.8 if far else 1.2) - 1.6, eye_y - 1.8, ex + (0.8 if far else 1.2) + 1.6, eye_y + 1.8), fill=EYE)
        hd.line([_pt(ex - 4.5, eye_y - 7.0 - brow), _pt(ex + 4.5, eye_y - 6.0 + brow)], fill=OUTLINE, width=_s(1.25))

    # Broad boar snout and curved tusks.
    hd.ellipse(_box(hx - 23.0, hy + 5.0, hx + 27.0, hy + 27.0), fill=SNOUT, outline=OUTLINE, width=_s(1.1))
    hd.ellipse(_box(hx - 18.0, hy + 8.0, hx + 22.0, hy + 23.0), fill=SNOUT_LIGHT)
    hd.ellipse(_box(hx - 12.0, hy + 10.0, hx - 5.0, hy + 16.0), fill=NOSTRIL)
    hd.ellipse(_box(hx + 8.0, hy + 10.0, hx + 15.0, hy + 16.0), fill=NOSTRIL)
    mouth_y = hy + 23.0
    if mouth_open > 0.04:
        hd.ellipse(_box(hx - 10.0, mouth_y - 1.0, hx + 13.0, mouth_y + 4.0 + 8.0 * mouth_open), fill=OUTLINE)
    else:
        hd.arc(_box(hx - 10.0, mouth_y - 5.0, hx + 12.0, mouth_y + 5.0), 10, 170, fill=OUTLINE, width=_s(1.0))
    # Tusks sweep outward and upward so they remain readable at gameplay scale.
    left_tusk = [(hx - 17.0, hy + 20.0), (hx - 27.0, hy + 30.0), (hx - 23.0, hy + 14.0), (hx - 14.0, hy + 13.0)]
    right_tusk = [(hx + 18.0, hy + 20.0), (hx + 31.0, hy + 28.0), (hx + 25.0, hy + 12.0), (hx + 15.0, hy + 13.0)]
    hd.polygon([_pt(*q) for q in left_tusk], fill=TUSK, outline=OUTLINE)
    hd.polygon([_pt(*q) for q in right_tusk], fill=TUSK, outline=OUTLINE)
    hd.line([_pt(hx - 20.0, hy + 21.0), _pt(hx - 24.0, hy + 25.0)], fill=TUSK_SHADE, width=_s(0.8))
    hd.line([_pt(hx + 21.0, hy + 20.0), _pt(hx + 26.0, hy + 24.0)], fill=TUSK_SHADE, width=_s(0.8))


def _body_xform(p: Pose) -> SR.Xform:
    """The body layer's squash (its crop resized about the feet) and turn, as
    a map of where each piece lands: the pieces move, they are not resized."""
    T = SR.IDENTITY
    if p.squash_x != 1.0 or p.squash_y != 1.0:
        x0, y0 = _s(28.0 + DESIGN_OFFSET), _s(6.0 + DESIGN_OFFSET)
        tw, th = _s(92.0 * p.squash_x), _s(132.0 * p.squash_y)
        ox = _s(72.0 + DESIGN_OFFSET) - tw // 2
        oy = _s(137.0 + DESIGN_OFFSET) - th
        T = T.affine(tw / _s(92.0), ox, x0, th / _s(132.0), oy, y0)
    if abs(p.body_angle) > 0.01:
        rotation_y = 126.0 + p.body_y
        if p.effect in {"roll", "ledge_roll"}:
            rotation_y = 89.0 + p.body_y
        elif p.effect == "death":
            rotation_y = 104.0 + p.body_y
        T = T.rotate_ccw(_pt(72.0 + p.body_x, rotation_y), p.body_angle)
    return T


def _draw_boar_body(img: Image.Image, p: Pose) -> None:
    """The boar as a rig: limbs are fixed bones, the torso and each head
    expression are pieces painted once, all riding the body's squash and turn.
    A faded body fades each piece (a frame has one opacity, and the orbits
    beside it are not faded)."""
    T = _body_xform(p)
    alpha = _clamp01(p.body_alpha)

    _draw_leg(img, T, (62.0 + p.body_x, 111.0 + p.body_y), p.far_foot, True, alpha)
    _draw_arm(img, T, (51.0 + p.body_x, 77.0 + p.body_y), p.far_hand, True, alpha)

    torso = SR.rest_piece(("niels_torso",), (W, H), _pt(72.0, 86.0), _paint_torso)
    SR.place(img, torso, T.pt(_sp(72.0 + p.body_x, 86.0 + p.body_y)), T.deg, "torso", alpha)

    _draw_leg(img, T, (84.0 + p.body_x, 111.0 + p.body_y), p.near_foot, False, alpha)
    _draw_arm(img, T, (94.0 + p.body_x, 77.0 + p.body_y), p.near_hand, False, alpha)

    # Head and crest: one piece per expression, turned by the head's tilt
    # about the jaw, riding the body.
    blink, mouth, brow = bool(p.blink), SR.q(p.mouth_open, 0.1), SR.q(p.brow, 0.4)
    head = SR.rest_piece(("niels_head", blink, mouth, brow), (W, H), _pt(73.0, 52.0), lambda d: _paint_head(d, blink, mouth, brow))
    at = T.pt(_sp(73.0 + p.body_x + p.head_x, 52.0 + p.body_y + p.head_y))
    SR.place(img, head, at, T.deg - p.head_angle, "head", alpha)


def _draw_photon(draw: ImageDraw.ImageDraw, start: Point, end: Point, amount: float = 1.0) -> None:
    x1, y1 = start
    x2, y2 = end
    points = []
    segments = 10
    for idx in range(segments + 1):
        u = idx / segments
        x = _lerp(x1, x2, u)
        y = _lerp(y1, y2, u) + math.sin(u * math.tau * 3.0) * 2.4 * amount
        points.append(_pt(x, y))
    draw.line(points, fill=PHOTON_GLOW, width=_s(4.0 * amount))
    draw.line(points, fill=PHOTON, width=max(1, _s(1.2 * amount)))


def _draw_effects(img: Image.Image, p: Pose, foreground: bool) -> None:
    if not p.effect:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = blending_draw(layer)
    t = p.effect_t
    center = (72.0 + p.body_x, 76.0 + p.body_y)

    if p.effect == "block" and foreground:
        pulse = 0.7 + 0.3 * _pulse(t)
        draw.ellipse(_box(center[0] - 31.0 * pulse, center[1] - 36.0 * pulse, center[0] + 31.0 * pulse, center[1] + 36.0 * pulse), outline=(116, 218, 246, 185), width=_s(2.2))

    elif p.effect == "tusk_jab" and foreground:
        strike = _pulse(t)
        if strike > 0.15:
            draw.arc(_box(82.0 + p.body_x, 27.0 + p.body_y, 135.0 + p.body_x, 82.0 + p.body_y), 205, 315, fill=(240, 229, 190, int(220 * strike)), width=_s(2.6))
            draw.line([_pt(103.0 + p.body_x, 52.0 + p.body_y), _pt(132.0 + p.body_x, 48.0 + p.body_y)], fill=(255, 244, 205, int(180 * strike)), width=_s(1.1))

    elif p.effect == "orbital_sweep":
        sweep = _smooth(t)
        if foreground:
            radius = 31.0 + 32.0 * _pulse(t)
            draw.arc(_box(center[0] - radius, center[1] - radius * 0.55, center[0] + radius, center[1] + radius * 0.55), 205, 355, fill=(111, 224, 250, 225), width=_s(3.0))
            ex = center[0] + radius * math.cos(sweep * math.pi * 1.5)
            ey = center[1] + radius * 0.55 * math.sin(sweep * math.pi * 1.5)
            draw.ellipse(_box(ex - 4.0, ey - 4.0, ex + 4.0, ey + 4.0), fill=ELECTRON, outline=RING_BLUE, width=_s(1.0))

    elif p.effect == "shell_shift" and foreground:
        jump = _smooth(min(1.0, t / 0.62))
        outer = _orbit_point(center, 46.0, 16.0, -12.0, 0.3 + jump * 1.8)
        inner = _orbit_point(center, 24.0, 9.0, -12.0, 2.1)
        ex = _lerp(outer[0], inner[0], jump)
        ey = _lerp(outer[1], inner[1], jump) - math.sin(jump * math.pi) * 8.0
        draw.line([_pt(*outer), _pt(ex, ey)], fill=(100, 197, 239, 120), width=_s(1.0))
        draw.ellipse(_box(ex - 5.0, ey - 5.0, ex + 5.0, ey + 5.0), fill=ELECTRON_GLOW)
        draw.ellipse(_box(ex - 2.3, ey - 2.3, ex + 2.3, ey + 2.3), fill=ELECTRON)
        if t > 0.48:
            amount = _clamp01((t - 0.48) / 0.25)
            _draw_photon(draw, (ex + 3.0, ey), (136.0, ey - 8.0), amount)

    elif p.effect == "quantum_leap":
        if not foreground:
            intensity = _pulse(min(1.0, t * 1.5)) if t < 0.66 else _pulse((t - 0.55) / 0.45)
            for idx in range(3):
                radius = 14.0 + idx * 10.0 + intensity * 8.0
                draw.ellipse(_box(center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), outline=(118, 222, 248, int(120 * intensity)), width=_s(1.2))
        elif 0.26 < t < 0.75:
            _draw_photon(draw, (40.0, 77.0), (113.0, 65.0), 0.8)

    elif p.effect == "complementarity" and foreground:
        reveal = _smooth(min(1.0, t / 0.35)) * (1.0 - _smooth(max(0.0, (t - 0.78) / 0.22)))
        # Wave packet to the left.
        wave_points = []
        for idx in range(25):
            u = idx / 24.0
            x = 67.0 - 48.0 * u
            envelope = math.sin(u * math.pi)
            y = 74.0 + math.sin(u * math.tau * 3.0 + t * math.tau) * 8.0 * envelope
            wave_points.append(_pt(x, y))
        draw.line(wave_points, fill=(WAVE[0], WAVE[1], WAVE[2], int(WAVE[3] * reveal)), width=_s(2.0))
        # Discrete particle packet to the right.
        for idx in range(5):
            u = idx / 4.0
            x = 82.0 + 11.0 * idx + 3.0 * math.sin(t * math.tau + idx)
            y = 73.0 + 8.0 * math.sin(idx * 1.7 + t * math.tau)
            r = 2.3 + 1.0 * (1.0 - abs(0.5 - u) * 2.0)
            draw.ellipse(_box(x - r, y - r, x + r, y + r), fill=(PARTICLE[0], PARTICLE[1], PARTICLE[2], int(PARTICLE[3] * reveal)), outline=OUTLINE, width=_s(0.6))

    elif p.effect == "correspondence_charge":
        if not foreground:
            charge = _smooth(min(1.0, t / 0.45))
            for idx in range(4):
                x = 48.0 - idx * 9.0 + p.body_x
                y = 82.0 + idx * 5.0
                draw.arc(_box(x - 18.0, y - 7.0, x + 18.0, y + 7.0), 170, 350, fill=(RING_BLUE[0], RING_BLUE[1], RING_BLUE[2], int(150 * charge)), width=_s(1.4))
        else:
            rush = _smooth(max(0.0, (t - 0.35) / 0.65))
            if rush > 0.05:
                draw.line([_pt(28.0, 104.0), _pt(58.0 + p.body_x, 104.0 + p.body_y)], fill=(222, 191, 129, int(150 * rush)), width=_s(2.0))

    elif p.effect.startswith("air_") and foreground:
        impact = _pulse(t)
        if p.effect == "air_neutral":
            draw.ellipse(_box(center[0] - 35.0 * impact, center[1] - 24.0 * impact, center[0] + 35.0 * impact, center[1] + 24.0 * impact), outline=(104, 211, 242, int(210 * impact)), width=_s(2.2))
        elif p.effect == "air_down":
            draw.polygon([_pt(62.0, 102.0), _pt(72.0, 139.0), _pt(82.0, 102.0)], fill=(PHOTON[0], PHOTON[1], PHOTON[2], int(150 * impact)))
        elif p.effect == "air_up":
            draw.polygon([_pt(62.0, 48.0), _pt(72.0, 12.0), _pt(82.0, 48.0)], fill=(RING_CYAN[0], RING_CYAN[1], RING_CYAN[2], int(150 * impact)))
        else:
            side = 1.0 if p.effect == "air_forward" else -1.0
            draw.arc(_box(center[0] - 40.0, center[1] - 28.0, center[0] + 40.0, center[1] + 28.0), 200 if side > 0 else 20, 340 if side > 0 else 160, fill=(RING_BLUE[0], RING_BLUE[1], RING_BLUE[2], int(210 * impact)), width=_s(2.5))

    elif p.effect == "taunt" and foreground:
        if 0.25 < t < 0.75:
            draw.arc(_box(94.0, 54.0, 132.0, 88.0), 190, 345, fill=(RING_BLUE[0], RING_BLUE[1], RING_BLUE[2], 170), width=_s(1.2))
            draw.ellipse(_box(124.0, 67.0, 129.0, 72.0), fill=ELECTRON)

    rigdoc.composite_canvas(img, layer)


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p = _pose(animation, frame_idx, nframes)
    _draw_effects(img, p, foreground=False)
    _draw_orbits(img, p, foreground=False)
    _draw_boar_body(img, p)
    _draw_orbits(img, p, foreground=True)
    _draw_effects(img, p, foreground=True)
    return _downsample(img)


def render_portraits(out_dir: str | Path, **opts) -> List[Path]:
    """Publish close-up expressions from freshly rendered character frames."""
    del opts
    face = FaceGuide(
        center_x=88.0,
        center_y=55.0,
        width=48.0,
        height=42.0,
        source_width=176.0,
        source_height=176.0,
    )

    def portrait_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        return render_framed_portrait(
            render_frame(animation, frame_idx, frame_count),
            face,
            output_size=(192, 192),
            view_width=78.0,
            center_y=63.0,
        )

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 1, 8)),
        "talk": PortraitClip(
            tuple(portrait_frame("talk", frame, 8) for frame in range(8)),
            duration_ms=102,
            looping=True,
        ),
        "stern": PortraitClip(
            tuple(portrait_frame("taunt", frame, 8) for frame in (1, 3, 5, 7)),
            duration_ms=140,
            looping=True,
        ),
        "delighted": PortraitClip(
            tuple(portrait_frame("celebrate", frame, 8) for frame in (1, 3, 5, 7)),
            duration_ms=128,
            looping=True,
        ),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=130,
        actor_metadata=ACTOR_METADATA,
        auto_crop=False,
    )
    portrait_outputs = render_portraits(out_dir, **opts)
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
        *portrait_outputs,
    ] + list(parts.values())


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        render_frame,
        Path(out_dir),
        frame_size=FRAME_SIZE,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir", nargs="?", type=Path, default=Path("generated") / TARGET_NAME)
    args = parser.parse_args(argv)
    outputs = render(args.out_dir)
    for path in outputs:
        print(path)
    return 0


__all__ = [
    "ACTOR_METADATA",
    "AUTHORING_DESCRIPTION",
    "FALLBACK_DIALOGUE",
    "GAMEPLAY_DESCRIPTION",
    "ROWS",
    "SHEET_FILES",
    "SUGGESTED_BARKS",
    "TARGET_NAME",
    "render",
    "render_canonical",
    "render_frame",
    "render_portraits",
]


if __name__ == "__main__":
    raise SystemExit(main())
