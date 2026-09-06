"""Bespoke full-action renderer for Paul Diracula.

Paul Diracula is a Paul Dirac parody built as a severe, aristocratic vampire:
quiet, exact, unnervingly still, and far more frightening for never raising his
voice.  This is not a generic toon preset.  It uses the polished full-action
mathematician animation scaffold, but the silhouette, head, costume, cape,
portraits, and ability effects are authored specifically for Diracula.

The visual language combines Dirac's famously laconic public persona with a
restrained gothic silhouette: narrow pale face, widow's-peak hair, high collar,
long dark coat, crimson lining, and surgical gestures.  His combat effects draw
from the Dirac sea, particle-antiparticle pairing, spinors, gamma matrices, and
delta-like impulses.  Effects stay sparse and geometrically clean.

Painter order is deliberate: vacuum effects -> cape -> legs -> torso -> arms ->
foreground effects -> head.  The cape is body-integrated rather than a detached
prop, and no floor shadow is baked into the sheet.
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
from ambition_sprite2d_renderer.core.draw import blending_draw
from ...authoring.sheet_build import build_sheet, write_canonical

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "paul_diracula"
FRAME_W = 128
FRAME_H = 128
SUPER = 4

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 155),
    ("walk", 8, 108),
    ("run", 8, 78),
    ("crouch", 6, 98),
    ("crouch_walk", 8, 90),
    ("jump", 6, 94),
    ("fall", 6, 94),
    ("land_hard", 8, 94),
    ("land_recovery", 6, 74),
    ("dash_startup", 4, 50),
    ("dash", 6, 61),
    ("vacuum_step", 8, 55),
    ("slide", 6, 69),
    ("roll", 8, 58),
    ("wall_grab", 6, 106),
    ("wall_jump", 6, 84),
    ("ledge_grab", 6, 100),
    ("ledge_climb", 6, 100),
    ("ledge_getup", 6, 44),
    ("ledge_roll", 8, 40),
    ("climb", 8, 100),
    ("swim", 8, 104),
    ("float_glide", 8, 110),
    ("block", 6, 84),
    ("hit", 5, 88),
    ("death", 8, 108),
    ("talk", 8, 112),
    ("interact", 8, 92),
    ("jab", 5, 58),
    ("punch", 7, 70),
    ("delta_spike", 8, 66),
    ("attack_up", 8, 66),
    ("attack_down", 8, 66),
    ("air_neutral", 8, 62),
    ("air_forward", 7, 62),
    ("air_back", 7, 62),
    ("air_down", 7, 70),
    ("air_up", 7, 62),
    ("dirac_sea", 8, 78),
    ("pair_creation", 8, 80),
    ("spinor_turn", 10, 78),
    ("celebrate", 8, 92),
    ("taunt", 8, 98),
]

AUTHORING_DESCRIPTION = """Paul Diracula parodies theoretical physicist Paul Dirac.
The name turns Dirac into a restrained vampire rather than a broad Halloween
caricature.  Dirac's famous economy of speech, severe elegance, mathematical
precision, and emotionally unreadable public persona already support the
vampire interpretation.  The visual design draws on a narrow pale face, a
widow's peak, an austere high collar, long black-violet tailoring, crimson cape
lining, and almost motionless idle poses.

Scientific references include the Dirac sea, antimatter, particle-hole pairs,
spinors, gamma matrices, delta distributions, and the idea that apparently
empty space contains consequential structure.  Keep the comedy deadpan.  He
should not become florid, campy, chatty, or bestial; the joke works because he
treats supernatural horror as a clean consequence of the equations."""

GAMEPLAY_DESCRIPTION = """Paul Diracula is intended as a precise mid-range
caster-duelist.  His attacks should have thin, exact hit regions, strong timing,
and clean polarity or particle-antiparticle interactions rather than noisy area
spam.  The current authored vocabulary proposes Vacuum Step for evasive motion,
Delta Spike for a narrow impulse strike, Dirac Sea for controlled field pressure,
Pair Creation for linked positive/negative projectiles, and Spinor Turn for a
rotating defensive special.  He should reward composure and spacing, with lower
attack volume but unusually decisive confirms."""

SUGGESTED_BARKS = [
    "Your approximation is vulgar.",
    "The vacuum is not empty.",
    "Antimatter, then.",
    "You have chosen the wrong sign.",
    "Be still. The equation resolves.",
    "Symmetry does not oblige your survival.",
    "Into the sea with you.",
]

FALLBACK_DIALOGUE = [
    "Beauty in a theory is not decoration. It is evidence.",
    "Most people use too many words and too little precision.",
    "There is more structure in emptiness than amateurs suspect.",
    "A result should be clean enough to survive silence.",
    "The difficult part is usually deciding what need not be said.",
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_paul_diracula", "display_name": "Paul Diracula"},
    "lineage": {
        "authoring_description": AUTHORING_DESCRIPTION,
        "gameplay_description": GAMEPLAY_DESCRIPTION,
        "suggested_barks": SUGGESTED_BARKS,
        "fallback_dialogue": FALLBACK_DIALOGUE,
        "animation_scaffold": "polished_full_action_mathematician",
    },
    "dialogue_hints": {
        "suggested_barks": [
            'I vant to annihilate your positron.',
            'The equation demanded a mirror. I merely opened it.',
            'Antimatter, darling. Not undeath.',
            'Symmetry. Always symmetry.',
        ],
        "fallback_dialogue": [
            'The mathematics predicted a partner nobody had seen. I trusted the mathematics.',
            'Beauty in an equation is not decoration. It is usually a load-bearing wall.',
            'Every particle has a reflection waiting to cancel it. I find that romantic.',
            'I speak rarely. When the algebra is correct there is not much left to add.',
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story", "humanoid", "scientist", "mathematician", "physicist",
            "vampire_parody", "precision_duelist", "playable_candidate",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True, "jump": True, "climb": True, "fly": None,
            "swim": True, "crawl": True, "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True, "trade": None, "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "striker_swipe"},
    "visual": {"default_pose": "idle"},
    "tags": [
        "story", "humanoid", "scientist", "mathematician", "physicist",
        "vampire_parody", "precision_duelist", "playable_candidate",
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
        "action.melee.primary": {"animation": "delta_spike", "events": []},
        "action.ranged.primary": {"animation": "dirac_sea", "events": []},
        "action.special.primary": {"animation": "spinor_turn", "events": []},
        "action.special.secondary": {"animation": "pair_creation", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "missing_information": [
        "Narrative alignment and encounter placement remain intentionally unresolved.",
        "Final damage, resource, and polarity rules belong to gameplay authoring.",
    ],
}

OUTLINE = (10, 9, 14, 255)
OUTLINE_SOFT = (43, 35, 50, 255)
SKIN = (222, 211, 207, 255)
SKIN_LIGHT = (244, 237, 233, 255)
SKIN_SHADE = (174, 154, 157, 255)
HAIR = (20, 18, 25, 255)
HAIR_MID = (48, 40, 56, 255)
HAIR_GLEAM = (82, 69, 94, 255)
COAT = (44, 34, 52, 255)
COAT_LIGHT = (67, 49, 78, 255)
COAT_DARK = (27, 22, 34, 255)
COAT_DEEP = (13, 11, 18, 255)
WAISTCOAT = (121, 22, 43, 255)
WAISTCOAT_SHADE = (75, 13, 29, 255)
TROUSER = (38, 32, 45, 255)
TROUSER_LIGHT = (61, 49, 70, 255)
TROUSER_DARK = (22, 19, 27, 255)
SHOE = (24, 20, 29, 255)
SHOE_DARK = (13, 11, 16, 255)
SOLE = (8, 7, 10, 255)
GLASS = (225, 232, 255, 28)
EYE = (30, 20, 34, 255)
MOUTH = (112, 31, 48, 255)
DIRAC_SILVER = (205, 213, 229, 255)
DIRAC_LIGHT = (241, 244, 255, 255)
COLLAR = (236, 230, 230, 255)
COLLAR_SHADE = (184, 169, 177, 255)
ANTIMATTER_CYAN = (104, 218, 232, 255)
BLOOD_RED = (192, 36, 63, 255)
VACUUM_VIOLET = (145, 92, 211, 255)
VACUUM_FIELD = (151, 135, 201, 255)
CAPE_LINING = (101, 14, 37, 255)
FANG = (250, 245, 238, 255)


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
    spinor_turn: float = 0.0
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
    elif animation in {"dash_startup", "dash", "vacuum_step", "slide"}:
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
        if animation == "vacuum_step":
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
            p.spinor_turn = 0.35
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
    elif animation in {"jab", "punch", "delta_spike"}:
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
        if animation == "delta_spike":
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
    elif animation == "dirac_sea":
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
    elif animation == "pair_creation":
        p.chain = _smooth(t)
        p.field_phase = phase
        p.near_elbow = (85.0, 63.0)
        p.near_hand = (93.0, 50.0 + 5.0 * wave)
        p.near_hand_mode = "open"
        p.far_elbow = (46.0, 64.0)
        p.far_hand = (38.0, 53.0 - 5.0 * wave)
        p.far_hand_mode = "open"
        p.mouth_open = 0.25 + 0.25 * abs(wave)
    elif animation == "spinor_turn":
        p.spinor_turn = _smooth(t)
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
        p.spinor_turn = 0.35 + 0.25 * lift
    elif animation == "taunt":
        p.near_elbow = (85.0, 67.0)
        p.near_hand = (91.0, 56.0)
        p.near_hand_mode = "point"
        p.far_elbow = (49.0, 68.0)
        p.far_hand = (55.0, 80.0)
        p.smile = 0.7
        p.brow = 0.7
        p.spinor_turn = 0.25 + 0.15 * (0.5 + 0.5 * wave)

    return p


def _transform(point: Point, pose: Pose) -> Point:
    x, y = point
    # Forward lean is a shear around the waist, not a rigid rotation; this
    # keeps the shoes planted while giving the runner silhouette momentum.
    y_rel = y - 86.0
    x += -pose.body_lean * y_rel / 75.0
    point = (x + pose.root_x, y + pose.root_y)
    return _rotate(point, pose.rotation_pivot, pose.rotation)


def _draw_cape_behind(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    """Body-integrated cape with motion driven by the authored pose."""
    T = lambda q: _transform(q, pose)
    spread = 3.0 + 13.0 * pose.spinor_turn + 7.0 * pose.epsilon + 4.0 * pose.field
    lift = 5.0 * pose.spinor_turn + 2.0 * pose.epsilon
    outer = [
        T((53.0, 55.0)), T((76.5, 54.5)),
        T((84.0 + spread, 69.0 - lift)),
        T((90.0 + spread, 91.0 - lift * 0.4)),
        T((82.0 + spread * 0.5, 113.0)),
        T((72.0, 105.0)), T((64.8, 116.5)),
        T((57.0, 105.0)), T((47.0 - spread * 0.35, 113.0)),
        T((42.0 - spread, 91.0 - lift * 0.4)),
        T((47.0 - spread, 69.0 - lift)),
    ]
    _polygon(draw, outer, COAT_DEEP, OUTLINE, 1.25)
    lining = [
        T((56.0, 58.0)), T((73.0, 57.5)),
        T((80.0 + spread * 0.72, 72.0 - lift)),
        T((84.0 + spread * 0.68, 92.0)),
        T((74.0, 104.0)), T((65.0, 111.0)),
        T((56.5, 103.5)), T((48.0 - spread * 0.62, 91.0)),
        T((50.0 - spread * 0.65, 72.0 - lift)),
    ]
    _polygon(draw, lining, CAPE_LINING, OUTLINE_SOFT, 0.65)
    _line(draw, [T((53.5, 61.0)), T((64.8, 110.0)), T((76.0, 61.0))], COAT_LIGHT, 0.75)


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
        _line(draw, [_lerp_point(ankle_t, toe, 0.35), _lerp_point(ankle_t, toe, 0.72)], DIRAC_SILVER, 0.8)


def _draw_dirac_mark(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    """Small gamma/spinor chest mark; readable without becoming a held prop."""
    T = lambda q: _transform(q, pose)
    chest = T((65.1, 67.0))
    _ellipse(draw, T((65.1, 61.2)), 1.05, 1.05, DIRAC_SILVER, OUTLINE_SOFT, 0.45)
    font = _font(11.0, preferred=("DejaVuSerif-Italic.ttf", "DejaVuSerif.ttf", "DejaVuSans.ttf"))
    draw.text(
        _pt(_offset(chest, 0.0, 4.8)),
        "γ",
        font=font,
        fill=DIRAC_LIGHT,
        anchor="mm",
        stroke_width=max(1, _s(0.65)),
        stroke_fill=WAISTCOAT_SHADE,
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
        T((51.0, 56.0)), T((59.0, 51.2)), T((71.0, 50.8)), T((79.6, 55.4)),
        T((82.8, 72.0)), T((81.0, 91.0)), T((72.0, 98.0)), T((57.0, 97.0)),
        T((49.2, 89.0)), T((48.2, 70.8)),
    ]
    _polygon(draw, coat, COAT_DARK, OUTLINE, 1.2)
    _polygon(draw, [T((51.8, 57.0)), T((60.6, 52.0)), T((63.0, 92.0)), T((56.5, 94.0)), T((50.0, 74.0))], COAT, OUTLINE_SOFT, 0.7)
    _polygon(draw, [T((68.5, 51.6)), T((78.5, 56.0)), T((81.0, 74.0)), T((77.5, 94.0)), T((68.0, 95.0))], COAT_LIGHT, OUTLINE_SOFT, 0.7)

    waistcoat = [T((59.0, 57.0)), T((71.0, 56.8)), T((73.0, 67.0)), T((69.0, 89.0)), T((61.0, 89.0)), T((57.0, 67.0))]
    _polygon(draw, waistcoat, WAISTCOAT, OUTLINE_SOFT, 0.65)
    _line(draw, [T((65.0, 58.0)), T((65.0, 89.0))], WAISTCOAT_SHADE, 0.65)

    # Tall vampire collar and narrow white jabot.
    collar_l = [T((58.0, 55.0)), T((58.5, 46.5)), T((64.0, 55.0)), T((61.0, 63.0))]
    collar_r = [T((66.0, 55.0)), T((72.0, 46.0)), T((72.0, 55.0)), T((69.0, 63.0))]
    _polygon(draw, collar_l, COAT_DEEP, OUTLINE, 0.8)
    _polygon(draw, collar_r, COAT_DEEP, OUTLINE, 0.8)
    jabot = [T((62.0, 53.0)), T((68.0, 53.0)), T((69.0, 60.5)), T((66.6, 66.5)), T((65.0, 72.0)), T((63.4, 66.5)), T((61.0, 60.5))]
    _polygon(draw, jabot, COLLAR, OUTLINE_SOFT, 0.55)
    _line(draw, [T((62.3, 58.0)), T((67.7, 58.0))], COLLAR_SHADE, 0.45)
    _line(draw, [T((62.8, 62.5)), T((67.2, 62.5))], COLLAR_SHADE, 0.45)

    _draw_dirac_mark(draw, pose)
    for y in (75.0, 81.0, 87.0):
        _ellipse(draw, T((65.0, y)), 0.95, 0.95, DIRAC_SILVER, OUTLINE_SOFT, 0.35)
    _line(draw, [T((55.5, 90.0)), T((63.0, 82.0))], COAT_DEEP, 0.65)
    _line(draw, [T((74.5, 90.0)), T((67.0, 82.0))], COAT_DEEP, 0.65)

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

    ear = _rotate(T((52.4 + pose.head_x, 35.0 + pose.head_y)), center, pose.head_tilt)
    _ellipse(draw, ear, 3.2, 5.0, SKIN_SHADE, OUTLINE, 0.75)
    face = [
        T((54.0 + pose.head_x, 21.5 + pose.head_y)), T((62.0 + pose.head_x, 18.0 + pose.head_y)),
        T((71.0 + pose.head_x, 19.0 + pose.head_y)), T((77.0 + pose.head_x, 25.0 + pose.head_y)),
        T((78.0 + pose.head_x, 36.0 + pose.head_y)), T((73.8 + pose.head_x, 47.0 + pose.head_y)),
        T((65.0 + pose.head_x, 51.5 + pose.head_y)), T((56.5 + pose.head_x, 47.0 + pose.head_y)),
        T((52.2 + pose.head_x, 36.5 + pose.head_y)),
    ]
    face = [_rotate(q, center, pose.head_tilt) for q in face]
    _polygon(draw, face, SKIN, OUTLINE, 1.15)

    # Slick hair with a strong widow's peak and swept-back side mass.
    hair = [
        T((52.8 + pose.head_x, 31.0 + pose.head_y)), T((53.0 + pose.head_x, 23.0 + pose.head_y)),
        T((57.0 + pose.head_x, 16.0 + pose.head_y)), T((63.2 + pose.head_x, 11.0 + pose.head_y)),
        T((65.0 + pose.head_x, 20.5 + pose.head_y)), T((68.0 + pose.head_x, 13.2 + pose.head_y)),
        T((75.0 + pose.head_x, 16.5 + pose.head_y)), T((78.4 + pose.head_x, 24.0 + pose.head_y)),
        T((77.0 + pose.head_x, 31.5 + pose.head_y)), T((73.0 + pose.head_x, 25.0 + pose.head_y)),
        T((68.0 + pose.head_x, 23.0 + pose.head_y)), T((65.0 + pose.head_x, 27.5 + pose.head_y)),
        T((61.5 + pose.head_x, 23.0 + pose.head_y)), T((56.0 + pose.head_x, 26.0 + pose.head_y)),
    ]
    hair = [_rotate(q, center, pose.head_tilt) for q in hair]
    _polygon(draw, hair, HAIR, OUTLINE, 0.95)
    _line(draw, [_rotate(T((58.0 + pose.head_x, 18.0 + pose.head_y)), center, pose.head_tilt), _rotate(T((63.5 + pose.head_x, 13.5 + pose.head_y)), center, pose.head_tilt)], HAIR_GLEAM, 0.7)
    _line(draw, [_rotate(T((69.0 + pose.head_x, 15.0 + pose.head_y)), center, pose.head_tilt), _rotate(T((75.0 + pose.head_x, 20.0 + pose.head_y)), center, pose.head_tilt)], HAIR_MID, 0.7)

    brow_y = -0.5 - pose.brow * 0.6
    left_eye = _rotate(T((60.0 + pose.head_x, 34.0 + pose.head_y)), center, pose.head_tilt)
    right_eye = _rotate(T((70.3 + pose.head_x, 33.6 + pose.head_y)), center, pose.head_tilt)
    for eye_center, near in ((left_eye, False), (right_eye, True)):
        if pose.blink:
            _line(draw, [_offset(eye_center, -2.0, 0.0), _offset(eye_center, 2.0, -0.15)], EYE, 0.9)
        else:
            _ellipse(draw, eye_center, 2.9 if near else 2.65, 1.95, DIRAC_LIGHT, OUTLINE_SOFT, 0.45)
            _ellipse(draw, _offset(eye_center, 0.35, 0.1), 0.76, 0.92, VACUUM_VIOLET, EYE, 0.3)
            _ellipse(draw, _offset(eye_center, 0.55, -0.18), 0.20, 0.20, DIRAC_LIGHT, None, 0.0)
    _line(draw, [_offset(left_eye, -2.5, brow_y - 4.0), _offset(left_eye, 2.2, brow_y - 4.5)], HAIR, 0.9)
    _line(draw, [_offset(right_eye, -2.4, brow_y - 4.5), _offset(right_eye, 2.5, brow_y - 4.0)], HAIR, 0.9)

    nose_top = _rotate(T((67.0 + pose.head_x, 35.0 + pose.head_y)), center, pose.head_tilt)
    nose_tip = _rotate(T((68.0 + pose.head_x, 40.2 + pose.head_y)), center, pose.head_tilt)
    _line(draw, [nose_top, nose_tip, _offset(nose_tip, -1.4, 0.8)], SKIN_SHADE, 0.7)

    mouth = _rotate(T((65.5 + pose.head_x, 45.8 + pose.head_y)), center, pose.head_tilt)
    if pose.mouth_open > 0.14:
        _ellipse(draw, mouth, 2.8, 0.8 + 1.3 * pose.mouth_open, MOUTH, OUTLINE_SOFT, 0.45)
        # One restrained fang is enough at sprite scale.
        fang = [_offset(mouth, 0.7, -0.8), _offset(mouth, 1.5, -0.8), _offset(mouth, 1.1, 0.8)]
        _polygon(draw, fang, FANG, None, 0.0)
    else:
        _line(draw, [_offset(mouth, -2.5, 0.0), mouth, _offset(mouth, 2.4, -0.15 - 0.3 * pose.smile)], MOUTH, 0.72)
    _line(draw, [_rotate(T((61.0 + pose.head_x, 48.0 + pose.head_y)), center, pose.head_tilt), _rotate(T((69.0 + pose.head_x, 48.0 + pose.head_y)), center, pose.head_tilt)], SKIN_SHADE, 0.35)

def _draw_ability_effects_behind(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    if pose.spinor_turn > 0.02:
        center = T((65.0, 68.0))
        progress = 50.0 + 310.0 * pose.spinor_turn
        _arc(draw, center, 32.0, 36.0, -90.0, -90.0 + progress, _fade(ANTIMATTER_CYAN, 0.72), 2.0)
        _arc(draw, center, 27.0, 31.0, 90.0, 90.0 + progress * 0.88, _fade(VACUUM_VIOLET, 0.64), 1.3)
        for idx, sign in enumerate(("+", "−", "+", "−")):
            angle = math.radians(-80.0 + progress * (0.18 + idx * 0.18))
            pos = (center[0] + math.cos(angle) * (23.0 + idx), center[1] + math.sin(angle) * (27.0 + idx))
            _ellipse(draw, pos, 3.7, 3.7, _fade(COAT_DEEP, 0.82), DIRAC_SILVER, 0.45)
            font = _font(6.4, preferred=("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"))
            draw.text(_pt(pos), sign, font=font, fill=DIRAC_LIGHT, anchor="mm")
    if pose.field > 0.02:
        center = T((65.0, 64.0))
        for idx in range(3):
            _arc(draw, center, 18.0 + idx * 5.0, 12.0 + idx * 4.2, 200, 340, _fade(VACUUM_FIELD, pose.field * (0.45 + idx * 0.13)), 1.0 + idx * 0.22)
    if pose.prime > 0.03:
        hand = T(pose.near_hand)
        reach = 10.0 + 28.0 * pose.prime
        _line(draw, [hand, (hand[0] + reach, hand[1] - 0.8)], _fade(DIRAC_LIGHT, pose.prime), 2.0)
        tip = (hand[0] + reach, hand[1] - 0.8)
        _polygon(draw, [tip, (tip[0] - 5.0, tip[1] - 3.2), (tip[0] - 5.0, tip[1] + 3.2)], _fade(BLOOD_RED, pose.prime), DIRAC_SILVER, 0.45)
    if pose.compress > 0.02:
        center = T((75.0, 62.0))
        for idx in range(5):
            radius = _lerp(27.0 - idx * 4.2, 6.0 + idx * 0.9, pose.compress)
            color = ANTIMATTER_CYAN if idx % 2 == 0 else VACUUM_VIOLET
            _arc(draw, center, radius, radius * 0.82, 155, 385, _fade(color, 0.24 + idx * 0.10), 0.9 + idx * 0.18)
    if pose.chain > 0.02:
        chest = T((65.0, 67.0))
        left = T((42.0, 48.0))
        right = T((88.0, 48.0))
        for node, color, sign in ((left, ANTIMATTER_CYAN, "+"), (right, VACUUM_VIOLET, "−")):
            end = _lerp_point(node, chest, pose.chain)
            _line(draw, [node, end], _fade(color, 0.82), 1.25)
            _ellipse(draw, node, 5.0, 5.0, _fade(COAT_DEEP, 0.9), color, 0.65)
            font = _font(7.0, preferred=("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"))
            draw.text(_pt(node), sign, font=font, fill=DIRAC_LIGHT, anchor="mm")
        if pose.chain > 0.55:
            out = T(pose.near_hand)
            _line(draw, [chest, out], _fade(DIRAC_LIGHT, (pose.chain - 0.55) / 0.45), 2.0)


def _draw_ability_effects_front(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    T = lambda q: _transform(q, pose)
    if pose.field > 0.02:
        center = T((76.0, 64.0))
        _arc(draw, center, 18.0, 25.0, 110, 250, _fade(VACUUM_FIELD, pose.field), 2.1)
        _arc(draw, center, 14.0, 20.0, 110, 250, _fade(DIRAC_LIGHT, pose.field * 0.48), 0.85)
    if pose.compress > 0.45:
        hand = T(pose.near_hand)
        release = (pose.compress - 0.45) / 0.55
        _line(draw, [hand, (hand[0] + 24.0 * release, hand[1] - 1.2)], _fade(ANTIMATTER_CYAN, release), 2.3)
        _line(draw, [hand, (hand[0] + 31.0 * release, hand[1] + 1.6)], _fade(VACUUM_VIOLET, release * 0.82), 1.1)

def _render_native_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    """Render into the authored supersampled canvas without raster scaling."""
    pose = _pose(animation, frame_idx, nframes)
    image = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    draw = blending_draw(image)

    _draw_ability_effects_behind(draw, pose)
    _draw_cape_behind(draw, pose)
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
    """Publish Paul Diracula's native close-up expressions and talk loop."""
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
        "speaking": PortraitClip(
            tuple(portrait_frame("talk", frame, 8) for frame in range(8)),
            duration_ms=104,
            looping=True,
        ),
        "vacuum": PortraitClip(
            tuple(
                portrait_frame("dirac_sea", frame, 8)
                for frame in (1, 3, 5, 7)
            ),
            duration_ms=118,
            looping=True,
        ),
        "satisfied": PortraitClip(
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
        attack_hitboxes={
            "delta_spike": {"bbox": {"x": 74, "y": 47, "w": 52, "h": 39}},
            "dirac_sea": {"bbox": {"x": 80, "y": 39, "w": 47, "h": 48}},
            "spinor_turn": {"bbox": {"x": 22, "y": 24, "w": 86, "h": 88}},
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
    "ACTOR_METADATA", "AUTHORING_DESCRIPTION", "GAMEPLAY_DESCRIPTION",
    "SUGGESTED_BARKS", "FALLBACK_DIALOGUE", "render",
    "render_canonical", "render_frame", "render_portraits",
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
