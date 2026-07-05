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
from dataclasses import dataclass
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

SHORT_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 1, 160),
    ("dead", 1, 120),
    ("walk", 3, 95),
    ("jump", 1, 120),
    ("skid", 1, 110),
    ("climb", 2, 120),
    ("swim", 4, 100),
]

TALL_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 1, 160),
    ("dead", 1, 120),
    ("walk", 3, 95),
    ("jump", 1, 120),
    ("skid", 1, 110),
    ("crouch", 1, 120),
    ("climb", 2, 120),
    ("swim", 6, 100),
    ("grow", 4, 70),
]

FIRE_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 1, 160),
    ("dead", 1, 120),
    ("walk", 3, 95),
    ("jump", 1, 120),
    ("skid", 1, 110),
    ("crouch", 1, 120),
    ("climb", 2, 120),
    ("swim", 6, 100),
    ("fireball", 1, 120),
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
    rows=FIRE_ROWS,
)


SHORT_POSES: Dict[str, List[Pose]] = {
    "idle": [Pose()],
    "dead": [Pose(mode="dead", bob=-4.2)],
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
    "dead": [Pose(mode="dead", bob=-4.4)],
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
        "state.dead": {"animation": "dead", "events": []},
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


def _draw_rotated_arm(
    px,
    shoulder_x: float,
    shoulder_y: float,
    *,
    front: bool,
    palette: MaryPalette,
    angle_deg: float,
    length: float = 4.4,
) -> None:
    hand_fill = palette.gloves if front else palette.skin
    end_x, end_y = _rotated_endpoint(shoulder_x, shoulder_y, angle_deg, length)
    _draw_segment(px, shoulder_x, shoulder_y, end_x, end_y, half_w=0.8, fill=palette.shirt)
    _outlined_rect(px, end_x - 1.0, end_y - 0.9, end_x + 1.0, end_y + 0.9, fill=hand_fill, inset=0.15)


def _draw_rotated_leg(
    px,
    hip_x: float,
    hip_y: float,
    *,
    palette: MaryPalette,
    angle_deg: float,
    length: float = 5.4,
    front: bool = False,
) -> None:
    fill = palette.overalls
    end_x, end_y = _rotated_endpoint(hip_x, hip_y, angle_deg, length)
    _draw_segment(px, hip_x, hip_y, end_x, end_y, half_w=0.95, fill=fill)
    shoe_dir = 1.0 if math.sin(math.radians(angle_deg)) >= 0 else -1.0
    x1 = end_x - 0.5 if shoe_dir > 0 else end_x - 2.7
    x2 = end_x + 2.3 if shoe_dir > 0 else end_x + 0.5
    _outlined_rect(px, x1, end_y - 0.4, x2, end_y + 1.0, fill=palette.shoes, inset=0.15)


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
        px.ellipse(x + 1.0, y + 0.1, x + 10.6, y + 5.0, fill=pal.cap, outline=OUTLINE, width=0.7)
        _outlined_rect(px, x + 0.8, y + 3.2, x + 10.2, y + 4.8, fill=pal.accent, inset=0.25)
        px.polygon(
            [(x + 10.9, y + 3.6), (x + 12.8, y + 5.7), (x + 10.6, y + 5.9)],
            fill=pal.accent,
            outline=OUTLINE,
            width=0.5,
        )
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
        px.rect(x + 3.4, y + 8.6, x + 4.8, y + 9.3, fill=(178, 89, 91, 255))
        px.rect(x + 2.8, y + 7.7, x + 3.8, y + 8.4, fill=(244, 157, 146, 255))
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
    px.ellipse(x + 1.0, y + 0.1, x + 10.6, y + 5.0, fill=pal.cap, outline=OUTLINE, width=0.7)
    _outlined_rect(px, x + 1.4, y + 3.2, x + 10.8, y + 4.8, fill=pal.accent, inset=0.25)
    px.polygon(
        [(x + 0.8, y + 3.6), (x - 1.3, y + 5.7), (x + 1.1, y + 5.9)],
        fill=pal.accent,
        outline=OUTLINE,
        width=0.5,
    )
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
    px.rect(x + 7.4, y + 8.6, x + 8.8, y + 9.3, fill=(178, 89, 91, 255))
    px.rect(x + 8.0, y + 7.7, x + 9.0, y + 8.4, fill=(244, 157, 146, 255))


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
    px.ellipse(x + 0.6, y + 0.2, x + 10.4, y + 5.0, fill=pal.cap, outline=OUTLINE, width=0.7)
    _outlined_rect(px, x + 1.0, y + 3.3, x + 10.0, y + 4.9, fill=pal.accent, inset=0.25)
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
    px.rect(x + 4.2, y + 9.2, x + 6.8, y + 9.9, fill=(178, 89, 91, 255))


def _draw_body_side(px, form: FormSpec, x: float, y: float, crouch: float) -> None:
    pal = form.palette
    body_h = form.body_height - 0.55 * crouch
    body_w = form.body_width + 0.4 * min(crouch, 1.4)
    waist = y + body_h * 0.63
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


def _draw_body_front(px, form: FormSpec, x: float, y: float, *, crouch: float = 0.0) -> None:
    pal = form.palette
    body_h = form.body_height - 0.55 * crouch
    body_w = form.body_width + 0.4 * min(crouch, 1.4)
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


def _draw_arm(px, x: float, y: float, *, front: bool, palette: MaryPalette, length: float = 4.2, glove_down: bool = True) -> None:
    glove_fill = palette.gloves if front else palette.skin
    shirt_fill = palette.shirt
    _outlined_rect(px, x, y, x + 1.6, y + length, fill=shirt_fill)
    glove_y = y + (length - 0.5 if glove_down else -1.2)
    _outlined_rect(px, x - 0.2, glove_y, x + 1.8, glove_y + 1.7, fill=glove_fill)


def _draw_leg(px, x: float, y: float, *, palette: MaryPalette, length: float = 5.2, front: bool = False) -> None:
    skin_fill = palette.overalls
    _outlined_rect(px, x + 0.2, y, x + 2.0, y + length, fill=skin_fill)
    _outlined_rect(px, x - 0.4, y + length - 0.4, x + 2.8, y + length + 1.2, fill=palette.shoes)


def _draw_dead_front(px, form: FormSpec, pose: Pose) -> None:
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
        palette=form.palette,
        angle_deg=-14.0,
        length=form.leg_height - 0.4,
        front=True,
    )
    _draw_rotated_leg(
        px,
        right_hip_x,
        hip_y,
        palette=form.palette,
        angle_deg=14.0,
        length=form.leg_height - 0.4,
        front=True,
    )

    _draw_body_front(px, form, body_x, body_top)
    _draw_head_front(px, form, body_x + 0.3, head_top)

    shoulder_y = body_top + 0.7
    _draw_rotated_arm(
        px,
        body_x + 3.0,
        shoulder_y,
        front=True,
        palette=form.palette,
        angle_deg=-135.0,
        length=5.3,
    )
    _draw_rotated_arm(
        px,
        body_x + 9.0,
        shoulder_y,
        front=True,
        palette=form.palette,
        angle_deg=135.0,
        length=5.3,
    )


def _draw_side_pose(px, form: FormSpec, pose: Pose) -> None:
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
            palette=form.palette,
            angle_deg=pose.arm_back_angle,
            length=4.4 if pose.mode != "climb" else 4.8,
        )
    else:
        _draw_arm(
            px,
            body_x - 1.4 + pose.arm_back_dx,
            body_top + 1.1 + pose.arm_back_dy,
            front=False,
            palette=form.palette,
            length=4.0,
        )

    if pose.leg_back_angle is not None:
        _draw_rotated_leg(
            px,
            back_hip[0],
            back_hip[1],
            palette=form.palette,
            angle_deg=pose.leg_back_angle,
            length=form.leg_height - 0.5 * pose.crouch,
            front=False,
        )
    else:
        _draw_leg(
            px,
            body_x + 2.1 + pose.leg_back_dx,
            torso_bottom + pose.leg_back_dy,
            palette=form.palette,
            length=form.leg_height - 0.6 * pose.crouch,
        )

    _draw_body_side(px, form, body_x, body_top, pose.crouch)
    _draw_head_side(px, form, body_x - 0.4 + pose.head_dx, head_top, lookback=pose.mode == "lookback")

    if pose.arm_front_angle is not None:
        _draw_rotated_arm(
            px,
            front_shoulder[0],
            front_shoulder[1],
            front=True,
            palette=form.palette,
            angle_deg=pose.arm_front_angle,
            length=5.2 if pose.mode == "fireball" else (4.8 if pose.mode in {"swim", "climb"} else 4.4),
        )
    else:
        _draw_arm(
            px,
            body_x + 8.3 + pose.arm_front_dx,
            body_top + 0.8 + pose.arm_front_dy,
            front=True,
            palette=form.palette,
            length=4.0,
        )

    if pose.leg_front_angle is not None:
        _draw_rotated_leg(
            px,
            front_hip[0],
            front_hip[1],
            palette=form.palette,
            angle_deg=pose.leg_front_angle,
            length=form.leg_height - 0.5 * pose.crouch,
            front=True,
        )
    else:
        _draw_leg(
            px,
            body_x + 5.1 + pose.leg_front_dx,
            torso_bottom + pose.leg_front_dy,
            palette=form.palette,
            length=form.leg_height - 0.6 * pose.crouch,
            front=True,
        )


def _poses_for(form: FormSpec) -> Dict[str, List[Pose]]:
    if form.tall:
        return TALL_LIKE_POSES
    return SHORT_POSES


def _draw_form(form: FormSpec, animation: str, frame_idx: int, nframes: int) -> Image.Image:
    if animation == "grow":
        alt_form = SHORT_FORM if frame_idx % 2 == 0 else form
        return _draw_form(alt_form, "idle", 0, 1)

    pose_seq = _poses_for(form).get(animation) or SHORT_POSES["idle"]
    pose = pose_seq[frame_idx % len(pose_seq)]

    def painter(px) -> None:
        if pose.mode == "dead":
            _draw_dead_front(px, form, pose)
        else:
            _draw_side_pose(px, form, pose)

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
        }
    )
    bindings = metadata["animation_bindings"]
    if form.tall:
        bindings["locomotion.crouch"] = {"animation": "crouch", "events": []}
    if form.power == "tall":
        bindings["power.grow"] = {"animation": "grow", "events": []}
    if form.power == "fire":
        bindings["ability.fireball"] = {"animation": "fireball", "events": []}
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
