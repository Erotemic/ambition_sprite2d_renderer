"""Authored data for Mary-O v2.

This module contains no drawing code. It owns palettes, form geometry, pose
records, animation row declarations, and palette-transition helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Tuple

from ..super_mary_o_common import MaryPalette

TARGET_BASE = "mary_o_v2"
OUTPUT_RESOLUTION_SCALE = 2.0
AUTHORING_FRAME_SIZE = (80, 96)
FRAME_SIZE = tuple(
    round(value * OUTPUT_RESOLUTION_SCALE)
    for value in AUTHORING_FRAME_SIZE
)
LOGICAL_SIZE = (24, 32)
SCALE = 3
LABEL_WIDTH = round(122 * OUTPUT_RESOLUTION_SCALE)

MARY_NORMAL = MaryPalette(
    cap=(188, 48, 92, 255),
    shirt=(223, 83, 76, 255),
    overalls=(38, 135, 160, 255),
    buttons=(255, 220, 91, 255),
    gloves=(248, 245, 239, 255),
    hair=(94, 54, 36, 255),
    skin=(251, 194, 148, 255),
    shoes=(96, 61, 42, 255),
    accent=(255, 155, 189, 255),
)

MARY_FIRE = MaryPalette(
    cap=(236, 88, 58, 255),
    shirt=(242, 112, 56, 255),
    overalls=(246, 242, 232, 255),
    buttons=(255, 190, 75, 255),
    gloves=(255, 251, 246, 255),
    hair=(98, 55, 35, 255),
    skin=(252, 198, 152, 255),
    shoes=(103, 65, 43, 255),
    accent=(255, 219, 108, 255),
)

MARY_FIRE_FLASH = MaryPalette(
    cap=(255, 176, 120, 255),
    shirt=(255, 237, 162, 255),
    overalls=(255, 252, 248, 255),
    buttons=(255, 232, 152, 255),
    gloves=(255, 255, 250, 255),
    hair=MARY_NORMAL.hair,
    skin=MARY_NORMAL.skin,
    shoes=(168, 116, 76, 255),
    accent=(255, 242, 178, 255),
)

MARY_FIRE_BLAST = MaryPalette(
    cap=(255, 246, 208, 255),
    shirt=(255, 255, 252, 255),
    overalls=(255, 255, 255, 255),
    buttons=(255, 240, 174, 255),
    gloves=(255, 255, 255, 255),
    hair=MARY_NORMAL.hair,
    skin=MARY_NORMAL.skin,
    shoes=(255, 226, 160, 255),
    accent=(255, 228, 148, 255),
)

RIBBON_PINK = (231, 120, 170, 255)
BROOCH_GOLD = (255, 208, 84, 255)
BROOCH_LIGHT = (255, 244, 205, 255)
EMBER_ORANGE = (255, 159, 76, 255)
EMBER_CORE = (255, 240, 190, 255)
BLUSH = (244, 157, 146, 255)
LIP = (178, 89, 91, 255)
WING_PEARL = (255, 246, 235, 255)
AURA_PINK = (244, 162, 202, 255)
AURA_GOLD = (255, 213, 118, 255)

# A form-transition clip is authored on the sheet of the form it ARRIVES AT, so
# the runtime plays it from the identity it has already switched to and nothing
# has to defer a swap to show it. Read the three lists together and each sheet
# answers "how did I get here":
#
#   short:  shrink (from tall), big_shrink (from fire)
#   tall:   grow   (from short), shrink     (from fire)
#   fire:   transform (from tall)
#
# The frames themselves draw whatever silhouettes the transition needs — the
# short sheet's `shrink` opens on the TALL body — so hosting is about who OWNS
# the clip, not about which forms appear in it.
SHORT_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 1, 160),
    ("death", 1, 120),
    ("walk", 3, 95),
    ("jump", 1, 120),
    ("skid", 1, 110),
    ("climb", 2, 120),
    ("swim", 4, 100),
    ("shrink", 4, 85),
    ("big_shrink", 8, 85),
]

TALL_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 1, 160),
    ("death", 1, 120),
    ("walk", 3, 95),
    ("jump", 1, 120),
    ("skid", 1, 110),
    ("crouch", 1, 120),
    ("climb", 2, 120),
    ("swim", 6, 100),
    ("grow", 4, 70),
    ("shrink", 6, 85),
]

FIRE_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 1, 160),
    ("death", 1, 120),
    ("walk", 3, 95),
    ("jump", 1, 120),
    ("skid", 1, 110),
    ("crouch", 1, 120),
    ("climb", 2, 120),
    ("swim", 6, 100),
    ("fireball", 1, 120),
    ("transform", 11, 80),
]


@dataclass(frozen=True)
class Pose:
    bob: float = 0.0
    body_lean: float = 0.0
    head_dx: float = 0.0
    head_dy: float = 0.0
    arm_front_dx: float = 0.0
    arm_front_dy: float = 0.0
    arm_back_dx: float = 0.0
    arm_back_dy: float = 0.0
    leg_front_dx: float = 0.0
    leg_front_dy: float = 0.0
    leg_back_dx: float = 0.0
    leg_back_dy: float = 0.0
    arm_front_angle: float | None = None
    arm_back_angle: float | None = None
    leg_front_angle: float | None = None
    leg_back_angle: float | None = None
    crouch: float = 0.0
    mode: str = "side"


@dataclass(frozen=True)
class FormSpec:
    target_name: str
    display_name: str
    body_height: float
    leg_height: float
    body_width: float
    palette: MaryPalette
    power: str
    tall: bool
    magic_stage: int
    rows: List[Tuple[str, int, int]]


SHORT_FORM = FormSpec(
    target_name=TARGET_BASE,
    display_name="Mary-O v2",
    body_height=4.8,
    leg_height=4.8,
    body_width=8.5,
    palette=MARY_NORMAL,
    power="short",
    tall=False,
    magic_stage=0,
    rows=SHORT_ROWS,
)

TALL_FORM = FormSpec(
    target_name=f"{TARGET_BASE}_tall",
    display_name="Mary-O v2 Tall",
    body_height=9.5,
    leg_height=8.6,
    body_width=9.4,
    palette=MARY_NORMAL,
    power="tall",
    tall=True,
    magic_stage=1,
    rows=TALL_ROWS,
)

FIRE_FORM = FormSpec(
    target_name=f"{TARGET_BASE}_fire",
    display_name="Mary-O v2 Fire",
    body_height=9.7,
    leg_height=8.5,
    body_width=9.6,
    palette=MARY_FIRE,
    power="fire",
    tall=True,
    magic_stage=2,
    rows=FIRE_ROWS,
)


def _lerp_rgba(a: tuple[int, int, int, int], b: tuple[int, int, int, int], t: float) -> tuple[int, int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def _mix_outfit_palette(base: MaryPalette, target: MaryPalette, t: float) -> MaryPalette:
    return MaryPalette(
        cap=_lerp_rgba(base.cap, target.cap, t),
        shirt=_lerp_rgba(base.shirt, target.shirt, t),
        overalls=_lerp_rgba(base.overalls, target.overalls, t),
        buttons=_lerp_rgba(base.buttons, target.buttons, t),
        gloves=_lerp_rgba(base.gloves, target.gloves, t),
        hair=base.hair,
        skin=base.skin,
        shoes=_lerp_rgba(base.shoes, target.shoes, t),
        accent=_lerp_rgba(base.accent, target.accent, t),
    )


def _form_with_palette(form: FormSpec, palette: MaryPalette) -> FormSpec:
    return replace(form, palette=palette)


def _transition_form(form: FormSpec, palette: MaryPalette, *, stage: float | None = None, power: str | None = None) -> FormSpec:
    updates = {"palette": palette}
    if stage is not None:
        updates["magic_stage"] = stage
    if power is not None:
        updates["power"] = power
    return replace(form, **updates)


def _magic_stage_value(form: FormSpec) -> float:
    return float(form.magic_stage)


def _fire_transition_t(form: FormSpec) -> float:
    return max(0.0, min(1.0, _magic_stage_value(form) - 1.0))


def _fire_accessory_t(form: FormSpec) -> float:
    return max(0.0, min(1.0, (_magic_stage_value(form) - 1.35) / 0.65))


SHORT_POSES: Dict[str, List[Pose]] = {
    "idle": [Pose()],
    "death": [Pose(mode="dead", bob=-4.2)],
    "walk": [
        Pose(
            body_lean=0.5,
            arm_front_dx=1.2,
            arm_front_dy=-1.0,
            arm_back_dx=-0.9,
            arm_back_dy=1.0,
            leg_front_dx=1.3,
            leg_back_dx=-0.9,
            leg_back_dy=1.0,
        ),
        Pose(
            bob=0.4,
            arm_front_dy=0.6,
            arm_back_dy=0.2,
            leg_front_dx=0.2,
            leg_back_dx=-0.2,
        ),
        Pose(
            body_lean=-0.4,
            arm_front_dx=-0.9,
            arm_front_dy=1.0,
            arm_back_dx=1.1,
            arm_back_dy=-1.1,
            leg_front_dx=-0.8,
            leg_front_dy=1.0,
            leg_back_dx=1.4,
        ),
    ],
    "jump": [
        Pose(
            bob=-1.8,
            arm_front_dx=0.6,
            arm_front_dy=-0.4,
            arm_back_dx=-0.5,
            arm_back_dy=0.3,
            arm_front_angle=145,
            arm_back_angle=-18,
            leg_front_angle=42,
            leg_back_angle=-30,
        ),
    ],
    "skid": [
        Pose(
            mode="lookback",
            body_lean=-1.6,
            head_dx=-1.1,
            arm_front_dx=0.5,
            arm_front_dy=-0.5,
            arm_back_dx=0.8,
            arm_back_dy=1.0,
            leg_front_angle=-36,
            leg_back_angle=-58,
            leg_front_dy=0.5,
            leg_back_dy=1.0,
        ),
    ],
    "climb": [
        Pose(mode="climb", bob=-0.2, arm_front_angle=88, arm_back_angle=82, leg_front_angle=92, leg_back_angle=86),
        Pose(mode="climb", bob=0.2, arm_front_angle=126, arm_back_angle=112, leg_front_angle=54, leg_back_angle=68),
    ],
    "swim": [
        Pose(mode="swim", bob=-0.7, arm_front_angle=125, arm_back_angle=45, leg_front_angle=25, leg_back_angle=-12),
        Pose(mode="swim", bob=-0.9, arm_front_angle=92, arm_back_angle=12, leg_front_angle=5, leg_back_angle=18),
        Pose(mode="swim", bob=-0.5, arm_front_angle=48, arm_back_angle=-25, leg_front_angle=-18, leg_back_angle=28),
        Pose(mode="swim", bob=-0.8, body_lean=-0.2, arm_front_angle=8, arm_back_angle=78, leg_front_angle=16, leg_back_angle=-22),
    ],
}

TALL_LIKE_POSES: Dict[str, List[Pose]] = {
    "idle": [Pose()],
    "death": [Pose(mode="dead", bob=-4.4)],
    "walk": [
        Pose(
            body_lean=0.5,
            arm_front_dx=1.4,
            arm_front_dy=-1.1,
            arm_back_dx=-1.0,
            arm_back_dy=1.1,
            leg_front_dx=1.4,
            leg_back_dx=-1.0,
            leg_back_dy=1.2,
        ),
        Pose(
            bob=0.4,
            arm_front_dy=0.7,
            arm_back_dy=0.2,
            leg_front_dx=0.3,
            leg_back_dx=-0.2,
        ),
        Pose(
            body_lean=-0.5,
            arm_front_dx=-1.0,
            arm_front_dy=1.1,
            arm_back_dx=1.2,
            arm_back_dy=-1.2,
            leg_front_dx=-0.8,
            leg_front_dy=1.1,
            leg_back_dx=1.5,
        ),
    ],
    "jump": [
        Pose(
            bob=-2.0,
            arm_front_dx=0.8,
            arm_front_dy=-0.5,
            arm_back_dx=-0.6,
            arm_back_dy=0.4,
            arm_front_angle=148,
            arm_back_angle=-22,
            leg_front_angle=45,
            leg_back_angle=-32,
        ),
    ],
    "skid": [
        Pose(
            mode="lookback",
            body_lean=-1.8,
            head_dx=-1.5,
            arm_front_dx=0.7,
            arm_front_dy=-0.5,
            arm_back_dx=1.0,
            arm_back_dy=1.1,
            leg_front_angle=-38,
            leg_back_angle=-62,
            leg_front_dy=0.6,
            leg_back_dy=1.2,
        ),
    ],
    "crouch": [
        Pose(
            mode="crouch",
            crouch=2.4,
            head_dx=0.6,
            arm_front_dx=0.8,
            arm_back_dx=-0.4,
            leg_front_dx=0.3,
            leg_back_dx=-0.2,
        )
    ],
    "climb": [
        Pose(mode="climb", bob=-0.2, arm_front_angle=88, arm_back_angle=82, leg_front_angle=92, leg_back_angle=86),
        Pose(mode="climb", bob=0.2, arm_front_angle=126, arm_back_angle=112, leg_front_angle=54, leg_back_angle=68),
    ],
    "swim": [
        Pose(mode="swim", bob=-0.6, arm_front_angle=132, arm_back_angle=52, leg_front_angle=30, leg_back_angle=-10),
        Pose(mode="swim", bob=-0.8, arm_front_angle=108, arm_back_angle=25, leg_front_angle=15, leg_back_angle=6),
        Pose(mode="swim", bob=-1.0, arm_front_angle=82, arm_back_angle=-8, leg_front_angle=-2, leg_back_angle=18),
        Pose(mode="swim", bob=-0.8, arm_front_angle=48, arm_back_angle=-35, leg_front_angle=-20, leg_back_angle=26),
        Pose(mode="swim", bob=-0.6, arm_front_angle=18, arm_back_angle=8, leg_front_angle=6, leg_back_angle=-16),
        Pose(mode="swim", bob=-0.7, body_lean=-0.2, arm_front_angle=2, arm_back_angle=88, leg_front_angle=22, leg_back_angle=-24),
    ],
    "fireball": [
        Pose(
            mode="fireball",
            body_lean=0.3,
            arm_front_angle=92,
            arm_back_angle=-12,
            leg_front_dx=0.8,
        )
    ],
}

ACTOR_METADATA_BASE = {
    "body": {
        "body_plan": "HumanoidBiped",
        "mass_class": "Light",
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": {"height_px": 48, "distance_px": 80, "source": "super_mary_o"},
            "climb": None,
            "crawl": None,
            "fly": None,
            "swim": None,
            "use_lifts": True,
            "door_access": [],
        },
        "interactions": {"talk": None, "trade": None, "carry": True, "open_doors": []},
    },
    "brain": {"default_preset": "wanderer_puppy_slug"},
    "actions": {"default_preset": "peaceful_float"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "walk", "events": []},
        "locomotion.jump": {"animation": "jump", "events": []},
        "locomotion.fall": {"animation": "jump", "events": []},
        "locomotion.skid": {"animation": "skid", "events": []},
        "locomotion.climb": {"animation": "climb", "events": []},
        "locomotion.swim": {"animation": "swim", "events": []},
        "state.dead": {"animation": "death", "events": []},
    },
    "tags": ["hero", "platformer", "mary_o", "retro"],
}
