"""Retro platformer protagonist sheets for the "Super Mary-O" push.

This module keeps the Mary family on the same unified, tack-on friendly
surface as other modern character sheets:

- a single drawing core with form specs + palette swaps
- module-level ``TARGETS`` so small / tall / fire forms stay colocated
- ``build_sheet`` for all spritesheet / YAML / RON / actor sidecars

The animation lineup follows the SMB1-style reference more closely while
keeping Mary as her own readable heroine silhouette: visible hair, head scarf,
jumper/shortalls, and no moustache.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ..super_mary_o_common import (
    OUTLINE,
    WHITE,
    MaryPalette,
    bottom_center_canvas,
    rasterize_logical,
)

TARGET_BASE = "super_mary_o"
FRAME_SIZE = (80, 96)
LOGICAL_SIZE = (24, 32)
SCALE = 3
LABEL_WIDTH = 122

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

RIBBON_PINK = (255, 179, 210, 255)
BROOCH_GOLD = (255, 221, 114, 255)
BROOCH_LIGHT = (255, 244, 205, 255)
EMBER_ORANGE = (255, 159, 76, 255)
EMBER_CORE = (255, 240, 190, 255)
BLUSH = (244, 157, 146, 255)
LIP = (178, 89, 91, 255)
WING_PEARL = (255, 246, 235, 255)
AURA_PINK = (255, 200, 228, 255)
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
    ("transform", 8, 80),
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
    display_name="Super Mary-O",
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
    display_name="Super Mary-O Tall",
    body_height=9.2,
    leg_height=8.8,
    body_width=9.0,
    palette=MARY_NORMAL,
    power="tall",
    tall=True,
    magic_stage=1,
    rows=TALL_ROWS,
)

FIRE_FORM = FormSpec(
    target_name=f"{TARGET_BASE}_fire",
    display_name="Super Mary-O Fire",
    body_height=9.2,
    leg_height=8.8,
    body_width=9.0,
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


def _outlined_rect(px, x1, y1, x2, y2, *, fill, inset: float = 0.5) -> None:
    px.rect(x1, y1, x2, y2, fill=OUTLINE)
    ix1, iy1 = x1 + inset, y1 + inset
    ix2, iy2 = x2 - inset, y2 - inset
    if ix2 <= ix1 or iy2 <= iy1:
        px.rect(x1, y1, x2, y2, fill=fill)
        return
    px.rect(ix1, iy1, ix2, iy2, fill=fill)


def _segment_quad(x1: float, y1: float, x2: float, y2: float, half_w: float) -> List[Tuple[float, float]]:
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy) or 1.0
    ox = -dy / dist * half_w
    oy = dx / dist * half_w
    return [
        (x1 + ox, y1 + oy),
        (x2 + ox, y2 + oy),
        (x2 - ox, y2 - oy),
        (x1 - ox, y1 - oy),
    ]


def _draw_segment(px, x1: float, y1: float, x2: float, y2: float, *, half_w: float, fill) -> None:
    px.polygon(_segment_quad(x1, y1, x2, y2, half_w), fill=fill, outline=OUTLINE, width=0.55)


def _rotated_endpoint(pivot_x: float, pivot_y: float, angle_deg: float, length: float) -> Tuple[float, float]:
    radians = math.radians(angle_deg)
    return (
        pivot_x + math.sin(radians) * length,
        pivot_y + math.cos(radians) * length,
    )


def _draw_star(px, cx: float, cy: float, *, outer: float, inner: float, fill, outline=OUTLINE, width: float = 0.45) -> None:
    pts: List[Tuple[float, float]] = []
    for idx in range(10):
        angle = math.radians(-90 + idx * 36)
        radius = outer if idx % 2 == 0 else inner
        pts.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    px.polygon(pts, fill=fill, outline=outline, width=width)


def _draw_ribbon_tail(px, x: float, y: float, *, flip: bool, fill, long: bool = False) -> None:
    sign = -1.0 if flip else 1.0
    loop_dx = 1.5 * sign
    px.polygon(
        [(x, y), (x + loop_dx, y - 1.0), (x + loop_dx * 1.2, y + 0.9)],
        fill=fill,
        outline=OUTLINE,
        width=0.45,
    )
    px.polygon(
        [(x, y), (x + loop_dx, y + 1.0), (x + loop_dx * 1.1, y + 2.1)],
        fill=fill,
        outline=OUTLINE,
        width=0.45,
    )
    tail_len = 4.2 if long else 3.0
    px.polygon(
        [(x, y + 0.4), (x + sign * 0.9, y + 2.0), (x + sign * 0.4, y + tail_len), (x - sign * 0.3, y + 2.6)],
        fill=fill,
        outline=OUTLINE,
        width=0.45,
    )


def _draw_rotated_arm(
    px,
    shoulder_x: float,
    shoulder_y: float,
    *,
    front: bool,
    form: FormSpec,
    angle_deg: float,
    length: float = 4.4,
) -> None:
    pal = form.palette
    hand_fill = pal.gloves if form.power != "normal" else pal.skin
    end_x, end_y = _rotated_endpoint(shoulder_x, shoulder_y, angle_deg, length)
    _draw_segment(px, shoulder_x, shoulder_y, end_x, end_y, half_w=0.8, fill=pal.shirt)
    if form.magic_stage >= 1:
        cuff_fill = pal.accent if form.magic_stage == 1 else pal.buttons
        cuff_x, cuff_y = _rotated_endpoint(shoulder_x, shoulder_y, angle_deg, max(0.0, length - 0.9))
        _draw_segment(px, cuff_x, cuff_y, end_x, end_y, half_w=0.9, fill=cuff_fill)
    _outlined_rect(px, end_x - 1.0, end_y - 0.9, end_x + 1.0, end_y + 0.9, fill=hand_fill, inset=0.15)


def _draw_rotated_leg(
    px,
    hip_x: float,
    hip_y: float,
    *,
    form: FormSpec,
    angle_deg: float,
    length: float = 5.4,
    front: bool = False,
) -> None:
    pal = form.palette
    end_x, end_y = _rotated_endpoint(hip_x, hip_y, angle_deg, length)
    _draw_segment(px, hip_x, hip_y, end_x, end_y, half_w=0.95, fill=pal.overalls)
    shoe_dir = 1.0 if math.sin(math.radians(angle_deg)) >= 0 else -1.0
    x1 = end_x - 0.5 if shoe_dir > 0 else end_x - 2.7
    x2 = end_x + 2.3 if shoe_dir > 0 else end_x + 0.5
    if form.magic_stage >= 1:
        cuff_fill = pal.accent if form.magic_stage == 1 else pal.buttons
        _outlined_rect(px, x1 + 0.2, end_y - 1.3, x2 - 0.2, end_y - 0.1, fill=cuff_fill, inset=0.15)
    _outlined_rect(px, x1, end_y - 0.4, x2, end_y + 1.0, fill=pal.shoes, inset=0.15)


def _draw_head_side(px, form: FormSpec, x: float, y: float, *, lookback: bool = False) -> None:
    pal = form.palette
    if lookback:
        px.polygon(
            [
                (x + 8.6, y + 3.2),
                (x + 12.8, y + 8.2),
                (x + 11.5, y + 13.8),
                (x + 8.1, y + 11.8),
            ],
            fill=pal.hair,
            outline=OUTLINE,
            width=0.75,
        )
        px.polygon(
            [
                (x + 1.9, y + 2.9),
                (x + 10.0, y + 3.2),
                (x + 9.1, y + 11.2),
                (x + 2.5, y + 10.7),
            ],
            fill=pal.hair,
            outline=OUTLINE,
            width=0.75,
        )
        if form.magic_stage >= 1:
            _draw_ribbon_tail(px, x + 10.7, y + 4.3, flip=False, fill=RIBBON_PINK, long=form.magic_stage >= 2)
            if form.magic_stage >= 2:
                px.polygon(
                    [(x + 11.0, y + 1.4), (x + 13.2, y + 2.6), (x + 11.8, y + 4.1)],
                    fill=pal.buttons,
                    outline=OUTLINE,
                    width=0.4,
                )
        px.ellipse(x + 1.0, y + 0.1, x + 10.6, y + 5.0, fill=pal.cap, outline=OUTLINE, width=0.7)
        _outlined_rect(px, x + 0.8, y + 3.2, x + 10.2, y + 4.8, fill=pal.accent, inset=0.25)
        px.polygon(
            [(x + 10.9, y + 3.6), (x + 12.8, y + 5.7), (x + 10.6, y + 5.9)],
            fill=pal.accent,
            outline=OUTLINE,
            width=0.5,
        )
        if form.magic_stage >= 1:
            _draw_star(px, x + 5.2, y + 2.4, outer=1.4 if form.magic_stage >= 2 else 1.1, inner=0.55, fill=BROOCH_GOLD)
        _outlined_rect(px, x + 2.1, y + 4.9, x + 9.1, y + 11.1, fill=pal.skin)
        px.polygon(
            [(x + 6.3, y + 4.8), (x + 9.0, y + 4.8), (x + 8.1, y + 7.2)],
            fill=pal.hair,
            outline=OUTLINE,
            width=0.35,
        )
        eye_x = x + 3.3
        _outlined_rect(px, eye_x, y + 6.2, eye_x + 1.3, y + 7.3, fill=WHITE, inset=0.2)
        _outlined_rect(px, eye_x + 0.2, y + 6.5, eye_x + 0.6, y + 7.0, fill=OUTLINE, inset=0.0)
        px.line([(x + 4.5, y + 6.0), (x + 3.6, y + 5.7)], fill=OUTLINE, width=0.35)
        px.rect(x + 3.4, y + 8.6, x + 4.8, y + 9.3, fill=LIP)
        px.rect(x + 2.8, y + 7.7, x + 3.8, y + 8.4, fill=BLUSH)
        if form.magic_stage >= 2:
            _draw_star(px, x + 8.7, y + 6.0, outer=0.7, inner=0.3, fill=BROOCH_LIGHT, width=0.25)
        return

    px.polygon(
        [
            (x + 1.0, y + 3.2),
            (x - 3.3, y + 8.3),
            (x - 2.1, y + 13.8),
            (x + 1.6, y + 11.9),
        ],
        fill=pal.hair,
        outline=OUTLINE,
        width=0.75,
    )
    px.polygon(
        [
            (x + 2.0, y + 2.9),
            (x + 10.1, y + 3.2),
            (x + 9.0, y + 11.2),
            (x + 1.5, y + 10.6),
        ],
        fill=pal.hair,
        outline=OUTLINE,
        width=0.75,
    )
    if form.magic_stage >= 1:
        _draw_ribbon_tail(px, x + 1.2, y + 4.2, flip=True, fill=RIBBON_PINK, long=form.magic_stage >= 2)
        if form.magic_stage >= 2:
            px.polygon(
                [(x - 0.8, y + 1.5), (x - 2.8, y + 2.7), (x - 1.5, y + 4.3)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.4,
            )
    px.ellipse(x + 1.0, y + 0.1, x + 10.6, y + 5.0, fill=pal.cap, outline=OUTLINE, width=0.7)
    _outlined_rect(px, x + 1.4, y + 3.2, x + 10.8, y + 4.8, fill=pal.accent, inset=0.25)
    px.polygon(
        [(x + 0.8, y + 3.6), (x - 1.3, y + 5.7), (x + 1.1, y + 5.9)],
        fill=pal.accent,
        outline=OUTLINE,
        width=0.5,
    )
    if form.magic_stage >= 1:
        _draw_star(px, x + 6.3, y + 2.4, outer=1.4 if form.magic_stage >= 2 else 1.1, inner=0.55, fill=BROOCH_GOLD)
    _outlined_rect(px, x + 2.5, y + 4.9, x + 9.5, y + 11.1, fill=pal.skin)
    px.polygon(
        [(x + 2.4, y + 4.8), (x + 5.1, y + 4.8), (x + 3.2, y + 7.2)],
        fill=pal.hair,
        outline=OUTLINE,
        width=0.35,
    )
    eye_x = x + 6.1
    _outlined_rect(px, eye_x, y + 6.2, eye_x + 1.3, y + 7.3, fill=WHITE, inset=0.2)
    _outlined_rect(px, eye_x + 0.8, y + 6.5, eye_x + 1.2, y + 7.0, fill=OUTLINE, inset=0.0)
    px.line([(x + 7.4, y + 6.1), (x + 8.2, y + 5.7)], fill=OUTLINE, width=0.35)
    px.rect(x + 7.4, y + 8.6, x + 8.8, y + 9.3, fill=LIP)
    px.rect(x + 8.0, y + 7.7, x + 9.0, y + 8.4, fill=BLUSH)
    if form.magic_stage >= 2:
        _draw_star(px, x + 2.8, y + 6.0, outer=0.7, inner=0.3, fill=BROOCH_LIGHT, width=0.25)


def _draw_head_front(px, form: FormSpec, x: float, y: float) -> None:
    pal = form.palette
    px.polygon(
        [(x + 1.5, y + 3.0), (x - 1.5, y + 9.5), (x + 1.0, y + 14.0), (x + 4.5, y + 11.2)],
        fill=pal.hair,
        outline=OUTLINE,
        width=0.75,
    )
    px.polygon(
        [(x + 8.5, y + 3.0), (x + 11.5, y + 9.5), (x + 9.0, y + 14.0), (x + 5.5, y + 11.2)],
        fill=pal.hair,
        outline=OUTLINE,
        width=0.75,
    )
    if form.magic_stage >= 1:
        _draw_ribbon_tail(px, x + 1.3, y + 4.4, flip=True, fill=RIBBON_PINK, long=form.magic_stage >= 2)
        _draw_ribbon_tail(px, x + 9.7, y + 4.4, flip=False, fill=RIBBON_PINK, long=form.magic_stage >= 2)
    px.ellipse(x + 0.6, y + 0.2, x + 10.4, y + 5.0, fill=pal.cap, outline=OUTLINE, width=0.7)
    _outlined_rect(px, x + 1.0, y + 3.3, x + 10.0, y + 4.9, fill=pal.accent, inset=0.25)
    if form.magic_stage >= 1:
        _draw_star(px, x + 5.4, y + 2.4, outer=1.5 if form.magic_stage >= 2 else 1.2, inner=0.6, fill=BROOCH_GOLD)
        if form.magic_stage >= 2:
            px.polygon(
                [(x + 0.8, y + 2.5), (x - 1.2, y + 3.3), (x + 0.1, y + 5.0)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )
            px.polygon(
                [(x + 10.2, y + 2.5), (x + 12.2, y + 3.3), (x + 10.9, y + 5.0)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )
    _outlined_rect(px, x + 2.0, y + 4.8, x + 9.0, y + 11.1, fill=pal.skin)
    px.polygon(
        [(x + 2.2, y + 4.6), (x + 8.8, y + 4.6), (x + 7.6, y + 6.2), (x + 3.4, y + 6.2)],
        fill=pal.hair,
        outline=OUTLINE,
        width=0.35,
    )
    _outlined_rect(px, x + 3.4, y + 6.5, x + 4.8, y + 7.6, fill=WHITE, inset=0.2)
    _outlined_rect(px, x + 6.2, y + 6.5, x + 7.6, y + 7.6, fill=WHITE, inset=0.2)
    _outlined_rect(px, x + 4.0, y + 6.8, x + 4.4, y + 7.3, fill=OUTLINE, inset=0.0)
    _outlined_rect(px, x + 6.8, y + 6.8, x + 7.2, y + 7.3, fill=OUTLINE, inset=0.0)
    px.line([(x + 5.4, y + 7.2), (x + 5.1, y + 8.6), (x + 5.8, y + 8.8)], fill=OUTLINE, width=0.35)
    px.rect(x + 4.2, y + 9.2, x + 6.8, y + 9.9, fill=LIP)
    px.rect(x + 2.6, y + 7.7, x + 3.6, y + 8.4, fill=BLUSH)
    px.rect(x + 7.4, y + 7.7, x + 8.4, y + 8.4, fill=BLUSH)


def _draw_body_side(px, form: FormSpec, x: float, y: float, crouch: float) -> None:
    pal = form.palette
    body_h = form.body_height - 0.55 * crouch
    body_w = form.body_width + 0.4 * min(crouch, 1.4)
    waist = y + body_h * 0.63
    if form.magic_stage >= 1:
        skirt_fill = pal.accent if form.magic_stage == 1 else pal.shirt
        hem_fill = pal.buttons if form.magic_stage == 1 else BROOCH_LIGHT
        px.polygon(
            [
                (x + 1.0, waist - 0.1),
                (x + 1.0 + body_w - 0.6, waist + 0.1),
                (x + 1.0 + body_w + 1.2, y + body_h + 1.9),
                (x + 0.5, y + body_h + 1.7),
            ],
            fill=skirt_fill,
            outline=OUTLINE,
            width=0.55,
        )
        px.line([(x + 1.5, y + body_h + 1.2), (x + 1.0 + body_w + 0.6, y + body_h + 1.2)], fill=hem_fill, width=0.6)
        px.polygon(
            [(x + 0.6, waist + 0.2), (x - 1.0, waist - 0.6), (x - 0.2, waist + 1.0)],
            fill=RIBBON_PINK if form.magic_stage == 1 else pal.buttons,
            outline=OUTLINE,
            width=0.35,
        )
        _outlined_rect(px, x + 4.1, y + body_h + 0.2, x + 5.0, y + body_h + 1.1, fill=pal.buttons, inset=0.18)
        _outlined_rect(px, x + 7.0, y + body_h + 0.2, x + 7.9, y + body_h + 1.1, fill=pal.buttons, inset=0.18)
    _outlined_rect(px, x + 1.0, y + 0.0, x + 1.0 + body_w, y + body_h, fill=pal.shirt)
    px.polygon(
        [
            (x + 2.0, y + 1.5),
            (x + 1.0 + body_w - 0.8, y + 1.5),
            (x + 1.0 + body_w, y + body_h + 0.9),
            (x + 1.0, y + body_h + 0.9),
        ],
        fill=pal.overalls,
        outline=OUTLINE,
        width=0.75,
    )
    px.line([(x + 2.3, y + 0.4), (x + 4.5, waist)], fill=pal.overalls, width=1.2)
    px.line([(x + 1.0 + body_w - 1.3, y + 0.4), (x + 6.3, waist)], fill=pal.overalls, width=1.2)
    px.line([(x + 2.0, waist), (x + 1.0 + body_w - 0.9, waist)], fill=OUTLINE, width=0.45)
    _outlined_rect(px, x + 3.5, y + 3.0, x + 4.5, y + 4.1, fill=pal.buttons, inset=0.2)
    _outlined_rect(px, x + 6.5, y + 3.0, x + 7.5, y + 4.1, fill=pal.buttons, inset=0.2)
    if form.magic_stage >= 1:
        _draw_star(px, x + 5.7, y + 2.3, outer=1.0 if form.magic_stage == 1 else 1.3, inner=0.45, fill=BROOCH_GOLD, width=0.35)
        px.polygon(
            [(x + 5.7, y + 2.9), (x + 4.6, y + 4.1), (x + 6.8, y + 4.1)],
            fill=RIBBON_PINK if form.magic_stage == 1 else pal.accent,
            outline=OUTLINE,
            width=0.3,
        )
        if form.magic_stage >= 2:
            px.polygon(
                [(x + 1.2, y + 1.2), (x - 0.9, y + 2.3), (x + 0.4, y + 5.4)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )
            px.polygon(
                [(x + 10.2, y + 1.0), (x + 12.0, y + 2.2), (x + 9.8, y + 5.6)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )
        _draw_suspender_fasteners_side(px, x, y, form)


def _draw_body_front(px, form: FormSpec, x: float, y: float, *, crouch: float = 0.0) -> None:
    pal = form.palette
    body_h = form.body_height - 0.55 * crouch
    body_w = form.body_width + 0.4 * min(crouch, 1.4)
    waist = y + body_h * 0.63
    if form.magic_stage >= 1:
        skirt_fill = pal.accent if form.magic_stage == 1 else pal.shirt
        hem_fill = pal.buttons if form.magic_stage == 1 else BROOCH_LIGHT
        px.polygon(
            [
                (x + 1.4, waist),
                (x + 1.2 + body_w - 0.2, waist),
                (x + 1.2 + body_w + 0.8, y + body_h + 1.9),
                (x + 0.4, y + body_h + 1.9),
            ],
            fill=skirt_fill,
            outline=OUTLINE,
            width=0.55,
        )
        px.line([(x + 1.0, y + body_h + 1.2), (x + 1.2 + body_w, y + body_h + 1.2)], fill=hem_fill, width=0.6)
        px.polygon(
            [(x + 1.2, waist + 0.2), (x - 0.9, waist - 0.6), (x - 0.1, waist + 1.2)],
            fill=RIBBON_PINK if form.magic_stage == 1 else pal.buttons,
            outline=OUTLINE,
            width=0.35,
        )
        px.polygon(
            [(x + 1.2 + body_w, waist + 0.2), (x + 3.3 + body_w, waist - 0.6), (x + 2.5 + body_w, waist + 1.2)],
            fill=RIBBON_PINK if form.magic_stage == 1 else pal.buttons,
            outline=OUTLINE,
            width=0.35,
        )
    _outlined_rect(px, x + 1.2, y + 0.0, x + 1.2 + body_w, y + body_h, fill=pal.shirt)
    px.polygon(
        [
            (x + 2.0, y + 1.4),
            (x + 1.2 + body_w - 0.8, y + 1.4),
            (x + 1.2 + body_w - 1.4, y + body_h + 0.8),
            (x + 2.8, y + body_h + 0.8),
        ],
        fill=pal.overalls,
        outline=OUTLINE,
        width=0.75,
    )
    px.line([(x + 3.2, y + 0.6), (x + 4.8, y + 4.6)], fill=pal.overalls, width=1.2)
    px.line([(x + 8.8, y + 0.6), (x + 7.2, y + 4.6)], fill=pal.overalls, width=1.2)
    _outlined_rect(px, x + 4.0, y + 2.8, x + 5.0, y + 4.0, fill=pal.buttons, inset=0.2)
    _outlined_rect(px, x + 7.0, y + 2.8, x + 8.0, y + 4.0, fill=pal.buttons, inset=0.2)
    if form.magic_stage >= 1:
        _draw_star(px, x + 5.9, y + 2.1, outer=1.0 if form.magic_stage == 1 else 1.35, inner=0.45, fill=BROOCH_GOLD, width=0.35)
        px.polygon(
            [(x + 5.9, y + 2.8), (x + 4.7, y + 4.1), (x + 7.1, y + 4.1)],
            fill=RIBBON_PINK if form.magic_stage == 1 else pal.accent,
            outline=OUTLINE,
            width=0.3,
        )
        if form.magic_stage >= 2:
            px.polygon(
                [(x + 1.4, y + 1.0), (x - 1.0, y + 2.0), (x + 1.0, y + 5.4)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )
            px.polygon(
                [(x + 10.8, y + 1.0), (x + 13.2, y + 2.0), (x + 11.2, y + 5.4)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )


def _draw_arm(px, x: float, y: float, *, front: bool, form: FormSpec, length: float = 4.2, glove_down: bool = True) -> None:
    pal = form.palette
    glove_fill = pal.gloves if form.power != "normal" else pal.skin
    _outlined_rect(px, x, y, x + 1.6, y + length, fill=pal.shirt)
    glove_y = y + (length - 0.5 if glove_down else -1.2)
    if form.magic_stage >= 1:
        cuff_fill = pal.accent if form.magic_stage == 1 else pal.buttons
        _outlined_rect(px, x - 0.1, glove_y - 0.8, x + 1.7, glove_y + 0.1, fill=cuff_fill, inset=0.15)
    _outlined_rect(px, x - 0.2, glove_y, x + 1.8, glove_y + 1.7, fill=glove_fill, inset=0.15)


def _draw_leg(px, x: float, y: float, *, form: FormSpec, length: float = 5.2, front: bool = False) -> None:
    pal = form.palette
    _outlined_rect(px, x + 0.2, y, x + 2.0, y + length, fill=pal.overalls)
    if form.magic_stage >= 1:
        cuff_fill = pal.accent if form.magic_stage == 1 else pal.buttons
        _outlined_rect(px, x, y + length - 1.1, x + 2.2, y + length - 0.2, fill=cuff_fill, inset=0.15)
    _outlined_rect(px, x - 0.4, y + length - 0.4, x + 2.8, y + length + 1.2, fill=pal.shoes)


def _draw_fire_orb(px, x: float, y: float) -> None:
    px.ellipse(x - 2.0, y - 2.0, x + 2.0, y + 2.0, fill=EMBER_ORANGE, outline=OUTLINE, width=0.45)
    px.ellipse(x - 1.0, y - 1.0, x + 1.0, y + 1.0, fill=EMBER_CORE, outline=OUTLINE, width=0.3)
    _draw_star(px, x + 2.3, y - 1.4, outer=0.8, inner=0.35, fill=BROOCH_LIGHT, width=0.25)


def _draw_suspender_fasteners_front(px, x: float, y: float, form: FormSpec) -> None:
    # Keep the classic overall-button read from the base Mary-O sprite.
    for cx in (x + 4.5, x + 7.5):
        px.ellipse(cx - 0.9, y + 2.65, cx + 0.9, y + 4.15, fill=form.palette.buttons, outline=OUTLINE, width=0.34)
        px.ellipse(cx - 0.28, y + 2.95, cx + 0.28, y + 3.50, fill=BROOCH_LIGHT, outline=None)


def _draw_suspender_fasteners_side(px, x: float, y: float, form: FormSpec) -> None:
    # Side views still keep two readable gold fasteners so the silhouette maps
    # back to the corresponding detail in the short/base form.
    for cx in (x + 4.15, x + 7.05):
        px.ellipse(cx - 0.84, y + 2.75, cx + 0.84, y + 4.18, fill=form.palette.buttons, outline=OUTLINE, width=0.34)
        px.ellipse(cx - 0.24, y + 3.02, cx + 0.24, y + 3.56, fill=BROOCH_LIGHT, outline=None)


def _draw_transform_outfit_stars(px, body_x: float, body_top: float, *, phase: int, form: FormSpec) -> None:
    star_fill = AURA_GOLD if form.magic_stage >= 2 else BROOCH_GOLD
    positions = [
        (body_x + 8.6, body_top + 2.2, 0.9),
        (body_x + 6.0, body_top + 6.3, 0.8),
        (body_x + 3.5, body_top + 9.2, 0.72),
    ]
    for sx, sy, outer in positions[: max(0, min(phase, len(positions)))]:
        _draw_star(px, sx, sy, outer=outer, inner=outer * 0.42, fill=star_fill, width=0.22)


def _draw_sleeve_wing_side(px, anchor_x: float, anchor_y: float, *, form: FormSpec, strength: float = 1.0, facing: float = 1.0) -> None:
    if strength <= 0.0 or form.magic_stage < 1:
        return
    outer = form.palette.buttons if form.magic_stage >= 2 else form.palette.accent
    inner = WING_PEARL if form.magic_stage >= 2 else BROOCH_LIGHT
    span = 1.3 + 0.8 * strength + (0.45 if form.magic_stage >= 2 else 0.0)
    lift = 0.8 + 0.35 * strength
    px.polygon(
        [
            (anchor_x, anchor_y),
            (anchor_x + facing * span, anchor_y - lift),
            (anchor_x + facing * 0.2, anchor_y + 0.9),
        ],
        fill=outer,
        outline=OUTLINE,
        width=0.3,
    )
    px.polygon(
        [
            (anchor_x + facing * 0.1, anchor_y + 0.35),
            (anchor_x + facing * (span + 0.5), anchor_y + 0.1),
            (anchor_x + facing * 0.25, anchor_y + 1.2),
        ],
        fill=inner,
        outline=OUTLINE,
        width=0.28,
    )
    if form.magic_stage >= 2 or strength > 0.8:
        px.polygon(
            [
                (anchor_x + facing * 0.15, anchor_y + 0.8),
                (anchor_x + facing * (span * 0.9), anchor_y + 1.35),
                (anchor_x + facing * 0.2, anchor_y + 1.55),
            ],
            fill=outer,
            outline=OUTLINE,
            width=0.28,
        )


def _draw_wing_side(px, anchor_x: float, anchor_y: float, *, form: FormSpec, spread: float = 0.0) -> None:
    if form.magic_stage < 1:
        return
    pal = form.palette
    phase = form.magic_stage + spread
    outer = pal.buttons if form.magic_stage >= 2 else pal.accent
    inner = WING_PEARL if form.magic_stage >= 2 else BROOCH_LIGHT
    fire_bonus = 0.9 if form.magic_stage >= 2 else 0.0
    depth = 2.4 + 0.8 * phase + fire_bonus
    height = 1.4 + 0.45 * phase + 0.35 * fire_bonus
    lift = 0.5 * spread + 0.2 * fire_bonus
    px.polygon(
        [
            (anchor_x, anchor_y + 0.4),
            (anchor_x - depth, anchor_y - height - lift),
            (anchor_x - 0.4, anchor_y - 0.3),
        ],
        fill=outer,
        outline=OUTLINE,
        width=0.35,
    )
    px.polygon(
        [
            (anchor_x, anchor_y + 0.8),
            (anchor_x - depth - 0.8, anchor_y + 0.6),
            (anchor_x - 0.4, anchor_y + 1.1),
        ],
        fill=inner,
        outline=OUTLINE,
        width=0.35,
    )
    if form.magic_stage >= 2 or spread >= 0.45:
        px.polygon(
            [
                (anchor_x + 0.2, anchor_y + 1.0),
                (anchor_x - depth * 0.9, anchor_y + height + 1.3 + lift),
                (anchor_x - 0.2, anchor_y + 1.8),
            ],
            fill=outer,
            outline=OUTLINE,
            width=0.35,
        )
        if form.magic_stage >= 2:
            px.polygon(
                [
                    (anchor_x + 0.35, anchor_y + 0.1),
                    (anchor_x - depth * 0.72, anchor_y - height * 0.2),
                    (anchor_x + 0.15, anchor_y + 0.95),
                ],
                fill=inner,
                outline=OUTLINE,
                width=0.28,
            )
        _draw_star(px, anchor_x - depth * 0.7, anchor_y - height - 0.4, outer=0.7, inner=0.3, fill=AURA_GOLD, width=0.25)


def _draw_wings_front(px, center_x: float, shoulder_y: float, *, form: FormSpec, spread: float = 0.0) -> None:
    if form.magic_stage < 1:
        return
    pal = form.palette
    outer = pal.buttons if form.magic_stage >= 2 else pal.accent
    inner = WING_PEARL if form.magic_stage >= 2 else BROOCH_LIGHT
    fire_bonus = 0.8 if form.magic_stage >= 2 else 0.0
    wing_h = 2.6 + 0.7 * (form.magic_stage + spread) + 0.5 * fire_bonus
    wing_w = 3.8 + 0.9 * (form.magic_stage + spread) + 0.9 * fire_bonus
    for sign in (-1, 1):
        px.polygon(
            [
                (center_x + sign * 1.4, shoulder_y + 0.6),
                (center_x + sign * wing_w, shoulder_y - wing_h),
                (center_x + sign * 2.2, shoulder_y + 0.4),
            ],
            fill=outer,
            outline=OUTLINE,
            width=0.35,
        )
        px.polygon(
            [
                (center_x + sign * 1.6, shoulder_y + 1.2),
                (center_x + sign * (wing_w + 0.3), shoulder_y + 0.8),
                (center_x + sign * 2.0, shoulder_y + 2.0),
            ],
            fill=inner,
            outline=OUTLINE,
            width=0.35,
        )
    if form.magic_stage >= 2 or spread >= 0.5:
        for sign in (-1, 1):
            px.polygon(
                [
                    (center_x + sign * 1.5, shoulder_y + 1.7),
                    (center_x + sign * (wing_w + 0.5), shoulder_y + 2.2),
                    (center_x + sign * 2.0, shoulder_y + 2.8),
                ],
                fill=outer,
                outline=OUTLINE,
                width=0.28,
            )
        _draw_star(px, center_x - wing_w - 0.6, shoulder_y - wing_h + 0.2, outer=0.7, inner=0.3, fill=AURA_GOLD, width=0.25)
        _draw_star(px, center_x + wing_w + 0.6, shoulder_y - wing_h + 0.2, outer=0.7, inner=0.3, fill=AURA_GOLD, width=0.25)


def _draw_transform_aura(px, frame_idx: int) -> None:
    sparkle_sets = [
        [(3.6, 8.0, 0.55), (20.5, 9.0, 0.55), (5.5, 18.2, 0.45)],
        [(3.0, 7.0, 0.65), (20.5, 6.8, 0.65), (4.6, 17.2, 0.55), (19.0, 18.2, 0.45)],
        [(2.8, 6.2, 0.8), (20.8, 6.0, 0.8), (6.0, 15.8, 0.6), (18.2, 16.2, 0.6)],
        [(2.4, 5.4, 0.95), (21.2, 5.4, 0.95), (4.0, 14.8, 0.75), (18.8, 14.8, 0.75), (12.0, 4.0, 0.7)],
        [(2.3, 5.0, 1.05), (21.3, 5.0, 1.05), (4.4, 13.8, 0.82), (18.2, 13.8, 0.82), (12.0, 3.6, 0.82), (11.8, 19.8, 0.7)],
        [(3.2, 6.0, 0.9), (20.5, 6.0, 0.9), (4.4, 14.8, 0.7), (18.4, 15.0, 0.7), (12.0, 4.0, 0.65)],
        [(4.0, 7.0, 0.75), (20.0, 7.0, 0.75), (5.0, 15.8, 0.6), (18.0, 15.8, 0.6)],
        [(4.2, 7.4, 0.65), (19.6, 7.4, 0.65), (5.8, 16.1, 0.55), (17.7, 16.1, 0.55)],
    ]
    for x, y, outer in sparkle_sets[frame_idx % len(sparkle_sets)]:
        fill = AURA_GOLD if outer >= 0.75 else AURA_PINK
        _draw_star(px, x, y, outer=outer, inner=outer * 0.45, fill=fill, width=0.22)


def _draw_power_loss_sparkles(px, frame_idx: int, *, fire: bool = False) -> None:
    sparkle_sets = [
        [(6.0, 8.4, 0.7), (17.8, 9.2, 0.6), (11.8, 18.4, 0.5)],
        [(7.0, 10.1, 0.65), (18.0, 11.0, 0.55), (12.0, 19.6, 0.45)],
        [(8.4, 12.0, 0.55), (17.0, 13.0, 0.45)],
        [(9.4, 14.0, 0.5), (15.8, 14.8, 0.4)],
        [(10.3, 15.2, 0.42)],
        [],
    ]
    for x, y, outer in sparkle_sets[min(frame_idx, len(sparkle_sets) - 1)]:
        fill = AURA_GOLD if fire and outer >= 0.55 else AURA_PINK
        _draw_star(px, x, y, outer=outer, inner=max(0.2, outer * 0.42), fill=fill, width=0.22)
    if fire and frame_idx <= 3:
        # a few embers trail downward as the power drains away
        ember_sets = [
            [(18.8, 13.5), (20.3, 15.2)],
            [(18.1, 14.7), (19.4, 16.4)],
            [(17.2, 16.0)],
            [(16.4, 17.2)],
        ]
        for ex, ey in ember_sets[min(frame_idx, len(ember_sets) - 1)]:
            px.ellipse(ex - 0.55, ey - 0.55, ex + 0.55, ey + 0.55, fill=EMBER_ORANGE, outline=OUTLINE, width=0.2)


def _draw_dead_front(px, form: FormSpec, pose: Pose, *, wing_boost: float = 0.0) -> None:
    body_x = 6.0
    foot_y = 28.8 + pose.bob
    torso_bottom = foot_y - form.leg_height
    body_top = torso_bottom - form.body_height
    head_top = body_top - 10.2

    left_hip_x = body_x + 4.9
    right_hip_x = body_x + 7.3
    hip_y = torso_bottom + 0.2
    _draw_rotated_leg(
        px,
        left_hip_x,
        hip_y,
        form=form,
        angle_deg=-14.0,
        length=form.leg_height - 0.4,
        front=True,
    )
    _draw_rotated_leg(
        px,
        right_hip_x,
        hip_y,
        form=form,
        angle_deg=14.0,
        length=form.leg_height - 0.4,
        front=True,
    )

    _draw_wings_front(px, body_x + 6.0, body_top + 2.2, form=form, spread=wing_boost)
    _draw_body_front(px, form, body_x, body_top)
    _draw_head_front(px, form, body_x + 0.3, head_top)

    shoulder_y = body_top + 0.7
    _draw_rotated_arm(
        px,
        body_x + 3.0,
        shoulder_y,
        front=True,
        form=form,
        angle_deg=-135.0,
        length=5.3,
    )
    _draw_rotated_arm(
        px,
        body_x + 9.0,
        shoulder_y,
        front=True,
        form=form,
        angle_deg=135.0,
        length=5.3,
    )


def _draw_side_pose(px, form: FormSpec, pose: Pose, *, animation: str = "idle", wing_boost: float = 0.0, sleeve_wing_boost: float = 0.0, extra_star_phase: int = 0) -> None:
    foot_y = 30.2 + pose.bob
    torso_bottom = foot_y - form.leg_height + 0.4 * pose.crouch
    body_top = torso_bottom - form.body_height + 0.6 * pose.crouch
    head_top = body_top - 10.0 + 0.8 * pose.crouch + pose.head_dy
    body_x = 7.0 + pose.body_lean

    if pose.mode == "swim":
        body_x = 6.3 + pose.body_lean
        head_top -= 0.6
    elif pose.mode == "crouch":
        body_x = 6.8 + pose.body_lean
    elif pose.mode == "climb":
        body_x = 6.4 + pose.body_lean

    body_w = form.body_width + 0.4 * min(pose.crouch, 1.4)
    back_shoulder = (body_x + 1.8 + pose.arm_back_dx, body_top + 1.4 + pose.arm_back_dy)
    front_shoulder = (body_x + body_w - 0.2 + pose.arm_front_dx, body_top + 1.2 + pose.arm_front_dy)
    back_hip = (body_x + 3.0 + pose.leg_back_dx, torso_bottom + pose.leg_back_dy)
    front_hip = (body_x + 6.3 + pose.leg_front_dx, torso_bottom + pose.leg_front_dy)

    if pose.arm_back_angle is not None:
        _draw_rotated_arm(
            px,
            back_shoulder[0],
            back_shoulder[1],
            front=False,
            form=form,
            angle_deg=pose.arm_back_angle,
            length=4.4 if pose.mode != "climb" else 4.8,
        )
    else:
        _draw_arm(
            px,
            body_x - 1.4 + pose.arm_back_dx,
            body_top + 1.1 + pose.arm_back_dy,
            front=False,
            form=form,
            length=4.0,
        )

    if pose.leg_back_angle is not None:
        _draw_rotated_leg(
            px,
            back_hip[0],
            back_hip[1],
            form=form,
            angle_deg=pose.leg_back_angle,
            length=form.leg_height - 0.5 * pose.crouch,
            front=False,
        )
    else:
        _draw_leg(
            px,
            body_x + 2.1 + pose.leg_back_dx,
            torso_bottom + pose.leg_back_dy,
            form=form,
            length=form.leg_height - 0.6 * pose.crouch,
        )

    side_wing_boost = wing_boost + (0.45 if form.power == "fire" else 0.0) + (0.25 if animation == "fireball" else 0.0)
    sleeve_boost = sleeve_wing_boost + (0.85 if form.power == "fire" else 0.0)
    _draw_wing_side(px, body_x + 1.6, body_top + 3.4, form=form, spread=side_wing_boost)
    if form.magic_stage >= 2:
        _draw_wing_side(px, body_x + 2.6, body_top + 5.1, form=form, spread=max(0.0, side_wing_boost - 0.15))
    if sleeve_boost > 0.0:
        _draw_sleeve_wing_side(px, back_shoulder[0] - 0.3, back_shoulder[1] + 1.1, form=form, strength=max(0.45, sleeve_boost * 0.8), facing=-1.0)

    # Keep the front leg tucked behind the dress / skirt silhouette in side view.
    if pose.leg_front_angle is not None:
        _draw_rotated_leg(
            px,
            front_hip[0],
            front_hip[1],
            form=form,
            angle_deg=pose.leg_front_angle,
            length=form.leg_height - 0.5 * pose.crouch,
            front=True,
        )
    else:
        _draw_leg(
            px,
            body_x + 5.1 + pose.leg_front_dx,
            torso_bottom + pose.leg_front_dy,
            form=form,
            length=form.leg_height - 0.6 * pose.crouch,
            front=True,
        )

    _draw_body_side(px, form, body_x, body_top, pose.crouch)
    if extra_star_phase > 0:
        _draw_transform_outfit_stars(px, body_x, body_top, phase=extra_star_phase, form=form)
    _draw_head_side(px, form, body_x - 0.4 + pose.head_dx, head_top, lookback=pose.mode == "lookback")

    if sleeve_boost > 0.0:
        _draw_sleeve_wing_side(px, front_shoulder[0] + 0.2, front_shoulder[1] + 1.0, form=form, strength=sleeve_boost, facing=1.0)
    if pose.arm_front_angle is not None:
        _draw_rotated_arm(
            px,
            front_shoulder[0],
            front_shoulder[1],
            front=True,
            form=form,
            angle_deg=pose.arm_front_angle,
            length=5.2 if pose.mode == "fireball" else (4.8 if pose.mode in {"swim", "climb"} else 4.4),
        )
    else:
        _draw_arm(
            px,
            body_x + 8.3 + pose.arm_front_dx,
            body_top + 0.8 + pose.arm_front_dy,
            front=True,
            form=form,
            length=4.0,
        )

    if form.power == "fire" and animation == "fireball":
        orb_x = front_shoulder[0] + 5.0
        orb_y = front_shoulder[1] + 0.8
        _draw_fire_orb(px, orb_x, orb_y)


def _poses_for(form: FormSpec) -> Dict[str, List[Pose]]:
    if form.tall:
        return TALL_LIKE_POSES
    return SHORT_POSES


def _draw_form(form: FormSpec, animation: str, frame_idx: int, nframes: int) -> Image.Image:
    if animation == "grow":
        # Hosted by the TALL sheet (the form arrived at). Named explicitly
        # rather than taken from `form` so the clip keeps meaning "small becomes
        # tall" wherever it is hosted, and ends on the form it arrives at.
        alt_form = SHORT_FORM if frame_idx % 2 == 0 else TALL_FORM
        return _draw_form(alt_form, "idle", 0, 1)

    if animation == "transform":
        fire_flash_1 = _mix_outfit_palette(MARY_NORMAL, MARY_FIRE_FLASH, 0.68)
        fire_flash_2 = MARY_FIRE_FLASH
        fire_reveal_1 = _mix_outfit_palette(MARY_FIRE_FLASH, MARY_FIRE, 0.35)
        fire_reveal_2 = _mix_outfit_palette(MARY_FIRE_FLASH, MARY_FIRE, 0.72)
        transform_seq = [
            (_form_with_palette(TALL_FORM, MARY_NORMAL), Pose(), 0.00, 0.00, 0, False),
            (_form_with_palette(TALL_FORM, MARY_NORMAL), Pose(bob=-0.4, arm_front_angle=118, arm_back_angle=42, leg_front_angle=8, leg_back_angle=-8), 0.12, 0.00, 2, False),
            (_form_with_palette(TALL_FORM, MARY_NORMAL), Pose(bob=-0.8, body_lean=0.05, arm_front_angle=92, arm_back_angle=26, leg_front_angle=14, leg_back_angle=-10), 0.60, 0.85, 3, False),
            (_form_with_palette(FIRE_FORM, fire_flash_1), Pose(bob=-1.05, body_lean=0.10, arm_front_angle=86, arm_back_angle=18, leg_front_angle=16, leg_back_angle=-12), 0.90, 1.00, 3, False),
            (_form_with_palette(FIRE_FORM, fire_flash_2), Pose(bob=-1.15, body_lean=0.12, arm_front_angle=102, arm_back_angle=22, leg_front_angle=18, leg_back_angle=-14), 1.20, 1.15, 3, True),
            (_form_with_palette(FIRE_FORM, fire_reveal_1), Pose(bob=-0.9, body_lean=0.14, arm_front_angle=110, arm_back_angle=20, leg_front_angle=18, leg_back_angle=-12), 1.25, 1.15, 3, True),
            (_form_with_palette(FIRE_FORM, fire_reveal_2), Pose(bob=-0.5, body_lean=0.10, arm_front_angle=70, arm_back_angle=-4, leg_front_angle=10, leg_back_angle=-6), 1.15, 1.05, 3, True),
            (FIRE_FORM, TALL_LIKE_POSES["fireball"][0], 0.90, 1.0, 3, True),
        ]
        active_form, pose, wing_boost, sleeve_wing_boost, extra_star_phase, show_orb = transform_seq[frame_idx % len(transform_seq)]

        def painter(px) -> None:
            _draw_transform_aura(px, frame_idx)
            _draw_side_pose(
                px,
                active_form,
                pose,
                animation="transform",
                wing_boost=wing_boost,
                sleeve_wing_boost=sleeve_wing_boost,
                extra_star_phase=extra_star_phase,
            )
            if show_orb:
                _draw_fire_orb(px, 19.4, 13.2 + 0.3 * math.sin(frame_idx))

        sprite = rasterize_logical(LOGICAL_SIZE, SCALE, painter)
        return bottom_center_canvas(sprite, FRAME_SIZE)

    if animation == "shrink":
        # Two hosts, two clips: the TALL sheet's shrink is "fire became tall"
        # and the SHORT sheet's is "tall became small". Both end on the sheet's
        # own form, which is what makes the arriving-sheet rule hold.
        if form.power == "tall":
            fire_dull_1 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.28)
            fire_dull_2 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.52)
            fire_dull_3 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.78)
            hurt_seq = [
                (FIRE_FORM, Pose(mode="fireball", bob=0.1, arm_front_angle=35, arm_back_angle=-18, leg_front_angle=-12, leg_back_angle=22), 0.85, 0.95, 2),
                (_form_with_palette(FIRE_FORM, fire_dull_1), Pose(bob=0.35, body_lean=-0.1, arm_front_angle=24, arm_back_angle=-36, leg_front_angle=-8, leg_back_angle=18), 0.55, 0.70, 1),
                (_form_with_palette(FIRE_FORM, fire_dull_2), Pose(bob=0.7, body_lean=-0.18, arm_front_angle=10, arm_back_angle=-58, leg_front_angle=5, leg_back_angle=10), 0.20, 0.35, 1),
                (_form_with_palette(FIRE_FORM, fire_dull_3), Pose(bob=1.0, body_lean=-0.08, arm_front_angle=88, arm_back_angle=-80, leg_front_angle=14, leg_back_angle=4), 0.0, 0.08, 0),
                (_form_with_palette(TALL_FORM, _mix_outfit_palette(MARY_NORMAL, MARY_FIRE, 0.18)), Pose(bob=0.75, body_lean=0.02, arm_front_angle=118, arm_back_angle=-48, leg_front_angle=10, leg_back_angle=-2), 0.0, 0.0, 0),
                (TALL_FORM, Pose(bob=0.3, body_lean=0.0, arm_front_angle=52, arm_back_angle=-12, leg_front_angle=0, leg_back_angle=0), 0.0, 0.0, 0),
            ]
            active_form, pose, wing_boost, sleeve_wing_boost, extra_star_phase = hurt_seq[frame_idx % len(hurt_seq)]

            def painter(px) -> None:
                _draw_power_loss_sparkles(px, frame_idx, fire=True)
                _draw_side_pose(
                    px,
                    active_form,
                    pose,
                    animation="shrink",
                    wing_boost=wing_boost,
                    sleeve_wing_boost=sleeve_wing_boost,
                    extra_star_phase=extra_star_phase,
                )

            sprite = rasterize_logical(LOGICAL_SIZE, SCALE, painter)
            return bottom_center_canvas(sprite, FRAME_SIZE)
        else:
            tall_dull = _mix_outfit_palette(MARY_NORMAL, MARY_FIRE_FLASH, 0.06)
            hurt_seq = [
                (TALL_FORM, Pose(bob=0.2, body_lean=-0.06, arm_front_angle=24, arm_back_angle=-18, leg_front_angle=-10, leg_back_angle=18), 1),
                (SHORT_FORM, Pose(bob=0.55, body_lean=-0.02, arm_front_angle=40, arm_back_angle=-18, leg_front_angle=-4, leg_back_angle=10), 0),
                (_form_with_palette(TALL_FORM, tall_dull), Pose(bob=0.85, body_lean=-0.10, arm_front_angle=88, arm_back_angle=-54, leg_front_angle=8, leg_back_angle=6), 0),
                (SHORT_FORM, Pose(bob=0.35, body_lean=0.0, arm_front_angle=46, arm_back_angle=-10, leg_front_angle=0, leg_back_angle=0), 0),
            ]
            active_form, pose, extra_star_phase = hurt_seq[frame_idx % len(hurt_seq)]

            def painter(px) -> None:
                _draw_power_loss_sparkles(px, frame_idx, fire=False)
                _draw_side_pose(px, active_form, pose, animation="shrink", extra_star_phase=extra_star_phase)

            sprite = rasterize_logical(LOGICAL_SIZE, SCALE, painter)
            return bottom_center_canvas(sprite, FRAME_SIZE)

    if animation == "big_shrink":
        # Hosted by the SHORT sheet: fire loses two tiers at once and arrives
        # small. No power guard — the sheet that owns the clip is the one it
        # ends on, and only the short sheet lists this row.
        fire_dull_1 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.28)
        fire_dull_2 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.58)
        fire_dull_3 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.84)
        big_shrink_seq = [
            (FIRE_FORM, Pose(mode="fireball", bob=0.1, arm_front_angle=35, arm_back_angle=-18, leg_front_angle=-12, leg_back_angle=22), 0.95, 1.05, 2),
            (_form_with_palette(FIRE_FORM, fire_dull_1), Pose(bob=0.35, body_lean=-0.1, arm_front_angle=24, arm_back_angle=-36, leg_front_angle=-8, leg_back_angle=18), 0.60, 0.72, 1),
            (_form_with_palette(FIRE_FORM, fire_dull_2), Pose(bob=0.7, body_lean=-0.16, arm_front_angle=12, arm_back_angle=-58, leg_front_angle=4, leg_back_angle=12), 0.18, 0.32, 0),
            (_form_with_palette(FIRE_FORM, fire_dull_3), Pose(bob=0.95, body_lean=-0.08, arm_front_angle=84, arm_back_angle=-76, leg_front_angle=12, leg_back_angle=4), 0.0, 0.0, 0),
            (TALL_FORM, Pose(bob=0.55, body_lean=-0.02, arm_front_angle=58, arm_back_angle=-22, leg_front_angle=-2, leg_back_angle=8), 0.0, 0.0, 0),
            (SHORT_FORM, Pose(bob=0.78, body_lean=-0.02, arm_front_angle=36, arm_back_angle=-18, leg_front_angle=-2, leg_back_angle=8), 0.0, 0.0, 0),
            (TALL_FORM, Pose(bob=0.48, body_lean=0.0, arm_front_angle=72, arm_back_angle=-28, leg_front_angle=4, leg_back_angle=2), 0.0, 0.0, 0),
            (SHORT_FORM, Pose(bob=0.25, body_lean=0.0, arm_front_angle=46, arm_back_angle=-10, leg_front_angle=0, leg_back_angle=0), 0.0, 0.0, 0),
        ]
        active_form, pose, wing_boost, sleeve_wing_boost, extra_star_phase = big_shrink_seq[frame_idx % len(big_shrink_seq)]

        def painter(px) -> None:
            _draw_power_loss_sparkles(px, frame_idx, fire=True)
            _draw_side_pose(
                px,
                active_form,
                pose,
                animation="big_shrink",
                wing_boost=wing_boost,
                sleeve_wing_boost=sleeve_wing_boost,
                extra_star_phase=extra_star_phase,
            )

        sprite = rasterize_logical(LOGICAL_SIZE, SCALE, painter)
        return bottom_center_canvas(sprite, FRAME_SIZE)

    pose_seq = _poses_for(form).get(animation) or SHORT_POSES["idle"]
    pose = pose_seq[frame_idx % len(pose_seq)]

    def painter(px) -> None:
        if pose.mode == "dead":
            _draw_dead_front(px, form, pose)
        else:
            _draw_side_pose(px, form, pose, animation=animation)

    sprite = rasterize_logical(LOGICAL_SIZE, SCALE, painter)
    return bottom_center_canvas(sprite, FRAME_SIZE)


def _actor_metadata(form: FormSpec) -> dict:
    metadata = copy.deepcopy(ACTOR_METADATA_BASE)
    metadata.update(
        {
            "actor": {
                "character_id": f"pc_{form.target_name}",
                "display_name": form.display_name,
            },
            "body": {
                **ACTOR_METADATA_BASE["body"],
                "body_kind": "Tall" if form.tall else "Compact",
                "traits": ["hero", "retro", "platformer", form.power],
            },
            "sockets": {
                "head": {"source": f"{form.target_name}.geometry", "point": {"x": 39.0, "y": 16.0 if form.tall else 20.0}},
                "hand_r": {"source": f"{form.target_name}.geometry", "point": {"x": 58.0, "y": 54.0}},
                "hand_l": {"source": f"{form.target_name}.geometry", "point": {"x": 23.0, "y": 54.0}},
                "foot_r": {"source": f"{form.target_name}.geometry", "point": {"x": 49.0, "y": 88.0}},
                "foot_l": {"source": f"{form.target_name}.geometry", "point": {"x": 35.0, "y": 88.0}},
            },
            "tags": [*ACTOR_METADATA_BASE["tags"], form.power],
            "authoring_description": (
                "Super Mary-O is an original heroine built as an affectionate parody of "
                "Mario and classic Super Mario platformers. The altered name, silhouette, "
                "power states, and movement vocabulary should evoke the genre while keeping "
                "Mary-O a distinct character rather than a direct copy."
            ),
            "gameplay_description": (
                f"Use the {form.display_name} sheet as a responsive retro-platform hero "
                f"in her {form.power} state. Games may opt into running, jumping, skidding, "
                "climbing, swimming, growth, or fireball actions according to the form's "
                "published animation set."
            ),
            "dialogue_hints": {
                "barks": [
                    "A clear jump is a kind of argument.",
                    "The level can keep its royal road. I brought running shoes.",
                    "One more platform.",
                ]
            },
        }
    )
    bindings = metadata["animation_bindings"]
    if form.tall:
        bindings["locomotion.crouch"] = {"animation": "crouch", "events": []}
    # Each sheet publishes the transitions that ARRIVE at it (see the row
    # tables): the short form knows how it was shrunk into, the tall form knows
    # how it was grown or dropped into, and the fire form knows how it was
    # transformed into.
    if form.power == "short":
        bindings["power.shrink"] = {"animation": "shrink", "events": []}
        bindings["power.big_shrink"] = {"animation": "big_shrink", "events": []}
    if form.power == "tall":
        bindings["power.grow"] = {"animation": "grow", "events": []}
        bindings["power.shrink"] = {"animation": "shrink", "events": []}
    if form.power == "fire":
        bindings["ability.fireball"] = {"animation": "fireball", "events": []}
        bindings["power.transform"] = {"animation": "transform", "events": []}
    return metadata


def _render_form(form: FormSpec, out_dir: str | Path) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
        return _draw_form(form, animation, frame_idx, nframes)

    outputs = build_sheet(
        target=form.target_name,
        rows=form.rows,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=LABEL_WIDTH,
        auto_crop=False,
        actor_metadata=_actor_metadata(form),
        trim=False,
    )
    return [
        outputs[k]
        for k in (
            "canonical",
            "canonical_transparent",
            "spritesheet",
            "yaml",
            "ron",
            "actor",
            "preview",
        )
    ]


def render_super_mary_o(out_dir: str | Path, **opts) -> List[Path]:
    return _render_form(SHORT_FORM, out_dir)


def render_super_mary_o_tall(out_dir: str | Path, **opts) -> List[Path]:
    return _render_form(TALL_FORM, out_dir)


def render_super_mary_o_fire(out_dir: str | Path, **opts) -> List[Path]:
    return _render_form(FIRE_FORM, out_dir)


TARGETS = {
    SHORT_FORM.target_name: {"render": render_super_mary_o, "actor_metadata": _actor_metadata(SHORT_FORM)},
    TALL_FORM.target_name: {"render": render_super_mary_o_tall, "actor_metadata": _actor_metadata(TALL_FORM)},
    FIRE_FORM.target_name: {"render": render_super_mary_o_fire, "actor_metadata": _actor_metadata(FIRE_FORM)},
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    return render_super_mary_o(out_dir, **opts)
