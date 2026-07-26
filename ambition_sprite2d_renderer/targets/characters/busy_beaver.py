"""Procedural sprite sheet for Busy Beaver, an overcommitted dam foreman.

Busy Beaver is a compact anthropomorphic beaver with a low center of gravity,
a broad paddle tail, a dented yellow hard hat, and a work vest loaded with
small tools.  The design deliberately avoids baked-in held props or effects so
runtime equipment and VFX remain composable.

Animations:
- ``idle``: heavy breathing, tail settling, occasional blink.
- ``walk``: short, determined construction-site march.
- ``work``: rapid two-handed tamping / inspection motion with empty hands.
- ``tail_slam``: full-body wind-up and broad tail strike.
- ``hurt``: compressed recoil with hat wobble.
- ``death``: stagger, sit, and exhausted collapse.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageColor, ImageDraw

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "busy_beaver"
FRAME_SIZE = (160, 160)
SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 145),
    ("walk", 8, 92),
    ("work", 8, 72),
    ("tail_slam", 10, 68),
    ("hurt", 5, 88),
    ("death", 10, 110),
]

SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_busy_beaver",
        "actor_id": "busy_beaver",
        "display_name": "Busy Beaver",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Heavy",
        "locomotion_hint": "Walk",
        "traits": [
            "animal",
            "beaver",
            "worker",
            "construction",
            "stocky",
            "tail_attack",
        ],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": None,
            "swim": True,
            "crawl": None,
            "use_lifts": True,
            "door_access": ["public", "service"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": True,
            "open_doors": ["public", "service"],
        },
    },
    "brain": {"default_preset": "busy_beaver_worker"},
    "actions": {"default_preset": "busy_beaver_tail_worker"},
    "visual": {"default_pose": "idle", "music_cue": "busy_beaver"},
    "dialogue_hints": {
        "barks": [
            "Busy, busy, busy.",
            "Dam inspection.",
            "That log is out of specification.",
            "The river can wait.",
            "No idle paws on my shift.",
        ]
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.use": {"animation": "work", "events": []},
        "action.melee.primary": {"animation": "tail_slam", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {
            "source": "busy_beaver.geometry",
            "point": {"x": 85.0, "y": 47.0},
        },
        "chest": {
            "source": "busy_beaver.geometry",
            "point": {"x": 78.0, "y": 85.0},
        },
        "hand_l": {
            "source": "busy_beaver.geometry",
            "point": {"x": 56.0, "y": 99.0},
        },
        "hand_r": {
            "source": "busy_beaver.geometry",
            "point": {"x": 101.0, "y": 98.0},
        },
        "tail": {
            "source": "busy_beaver.geometry",
            "point": {"x": 54.0, "y": 108.0},
        },
        "speech_bubble": {
            "source": "busy_beaver.geometry",
            "point": {"x": 82.0, "y": 10.0},
        },
    },
    "tags": ["npc", "animal", "worker", "beaver", "construction"],
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Busy Beaver personifies the computability-theory Busy Beaver function: a tiny, "
            "industrious creature whose apparent work schedule grows beyond any computable bound. The "
            "construction-worker beaver joke should read immediately, while the deeper reference "
            "rewards mathematically literate players."
        ),
        "gameplay_description": (
            "Use as a compulsively productive worker, foreman, quest giver, or deceptively dangerous "
            "escalation character. He should treat idleness as a technical defect and ordinary jobs "
            "as if they might never terminate."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'Busy, busy, busy.',
        'That log is out of specification.',
        'No idle paws on my shift.',
    ],
)

# Palette: dark low-register browns with a small safety-yellow accent.
OUTLINE = "#17110d"
OUTLINE_SOFT = "#33251d"
FUR_DARK = "#3a2418"
FUR_MID = "#6b4026"
FUR_LIGHT = "#a66a3a"
FUR_HIGHLIGHT = "#d7985b"
MUZZLE = "#c58c61"
MUZZLE_LIGHT = "#e4b384"
NOSE = "#211713"
EYE = "#17120f"
EYE_WHITE = "#f4e9d8"
TOOTH = "#f6ead1"
TAIL_DARK = "#3a261c"
TAIL_MID = "#62422c"
TAIL_LIGHT = "#8b6441"
VEST_DARK = "#303a37"
VEST_MID = "#465852"
VEST_LIGHT = "#65736a"
HAT_DARK = "#a46d11"
HAT = "#e5a91f"
HAT_LIGHT = "#ffd45c"
BELT = "#2b2520"
METAL = "#a8b0ae"


def _rgba(color: str, alpha: int = 255) -> RGBA:
    r, g, b = ImageColor.getrgb(color)
    return (r, g, b, alpha)


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(x: float, y: float) -> Tuple[int, int]:
    return (_s(x), _s(y))


def _box(x1: float, y1: float, x2: float, y2: float) -> Tuple[int, int, int, int]:
    return (_s(x1), _s(y1), _s(x2), _s(y2))


def _downsample(img: Image.Image) -> Image.Image:
    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _rotated_layer(
    size: Tuple[int, int],
    draw_fn,
    angle: float,
    center: Tuple[float, float],
) -> Image.Image:
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_fn(blending_draw(layer))
    return layer.rotate(
        angle,
        resample=Image.Resampling.BICUBIC,
        center=_pt(*center),
        fillcolor=(0, 0, 0, 0),
    )


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
    hat_angle: float = 0.0
    blink: bool = False
    mouth_open: float = 0.0
    brow: float = 0.0
    near_hand: Point = (102.0, 98.0)
    far_hand: Point = (56.0, 99.0)
    near_foot: Point = (91.0, 137.0)
    far_foot: Point = (65.0, 137.0)
    tail_angle: float = -8.0
    tail_x: float = 0.0
    tail_y: float = 0.0
    tail_flatten: float = 1.0


def _pose(animation: str, frame_idx: int, nframes: int) -> Pose:
    p = Pose()
    phase = frame_idx / max(1, nframes)
    t = frame_idx / max(1, nframes - 1)
    wave = math.sin(phase * math.tau)
    cosine = math.cos(phase * math.tau)

    if animation == "idle":
        breath = 0.5 - 0.5 * cosine
        p.body_y = -0.8 * breath
        p.head_y = -0.45 * breath
        p.head_angle = 0.8 * wave
        p.tail_angle = -8.0 + 2.0 * wave
        p.blink = frame_idx == 6
        p.brow = 0.4 * math.sin(phase * math.tau * 0.5)

    elif animation == "walk":
        stride = 9.0 * wave
        lift_near = max(0.0, wave) * 5.0
        lift_far = max(0.0, -wave) * 5.0
        p.body_x = 1.2 * wave
        p.body_y = -1.4 * abs(wave)
        p.body_angle = -1.8 * wave
        p.head_angle = 1.2 * wave
        p.near_foot = (91.0 + stride, 137.0 - lift_near)
        p.far_foot = (65.0 - stride, 137.0 - lift_far)
        p.near_hand = (102.0 - stride * 0.55, 98.0 + 1.5 * wave)
        p.far_hand = (56.0 + stride * 0.50, 99.0 - 1.2 * wave)
        p.tail_angle = -10.0 - 7.0 * wave

    elif animation == "work":
        hammer = 0.5 - 0.5 * math.cos(phase * math.tau * 2.0)
        p.body_y = 2.0 * hammer
        p.body_angle = 2.0 + 3.5 * hammer
        p.head_y = 1.0 * hammer
        p.head_angle = 3.0 + 4.0 * hammer
        p.near_hand = (88.0, 90.0 + 17.0 * hammer)
        p.far_hand = (72.0, 91.0 + 15.0 * hammer)
        p.near_foot = (93.0, 137.0)
        p.far_foot = (62.0, 137.0)
        p.tail_angle = -5.0 + 3.0 * wave
        p.mouth_open = 0.20 + 0.25 * hammer
        p.brow = -1.0

    elif animation == "tail_slam":
        # Wind-up, rotation through the hips, broad flat impact, recovery.
        if t < 0.30:
            u = t / 0.30
            p.body_x = 2.0 * u
            p.body_angle = -7.0 * u
            p.head_angle = -4.0 * u
            p.tail_angle = -12.0 - 58.0 * u
            p.tail_y = -3.0 * u
            p.near_hand = (98.0, 88.0)
            p.far_hand = (63.0, 91.0)
        elif t < 0.62:
            u = (t - 0.30) / 0.32
            p.body_x = 2.0 - 7.0 * u
            p.body_y = 2.0 * u
            p.body_angle = -7.0 + 17.0 * u
            p.head_angle = -4.0 + 8.0 * u
            p.tail_angle = -70.0 + 150.0 * u
            p.tail_flatten = 1.0 + 0.28 * u
            p.near_hand = (96.0, 91.0)
            p.far_hand = (61.0, 94.0)
            p.mouth_open = 0.5
            p.brow = -1.4
        else:
            u = (t - 0.62) / 0.38
            p.body_x = -5.0 * (1.0 - u)
            p.body_y = 2.0 * (1.0 - u)
            p.body_angle = 10.0 * (1.0 - u)
            p.head_angle = 4.0 * (1.0 - u)
            p.tail_angle = 80.0 - 88.0 * u
            p.tail_flatten = 1.28 - 0.28 * u
        p.near_foot = (96.0, 137.0)
        p.far_foot = (61.0, 137.0)

    elif animation == "hurt":
        impact = math.sin(t * math.pi)
        p.body_x = -7.0 * impact
        p.body_y = -2.0 * impact
        p.body_angle = -8.0 * impact
        p.squash_x = 1.0 + 0.08 * impact
        p.squash_y = 1.0 - 0.10 * impact
        p.head_x = -3.0 * impact
        p.head_angle = -10.0 * impact
        p.hat_angle = -14.0 * impact
        p.tail_angle = -8.0 - 18.0 * impact
        p.mouth_open = 0.65 * impact
        p.brow = 1.2

    elif animation == "death":
        if t < 0.35:
            u = t / 0.35
            p.body_x = -3.0 * u
            p.body_y = 2.0 * u
            p.body_angle = -8.0 * u
            p.hat_angle = -10.0 * u
            p.mouth_open = 0.35 * u
        elif t < 0.70:
            u = (t - 0.35) / 0.35
            p.body_x = -3.0 - 4.0 * u
            p.body_y = 2.0 + 13.0 * u
            p.body_angle = -8.0 - 45.0 * u
            p.head_y = 3.0 * u
            p.hat_angle = -10.0 - 40.0 * u
            p.near_foot = (93.0, 140.0)
            p.far_foot = (66.0, 140.0)
            p.tail_angle = -10.0 + 34.0 * u
        else:
            u = (t - 0.70) / 0.30
            p.body_x = -7.0
            p.body_y = 15.0 + 6.0 * u
            p.body_angle = -53.0 - 13.0 * u
            p.head_y = 3.0 + 4.0 * u
            p.hat_angle = -50.0 - 18.0 * u
            p.tail_angle = 24.0 + 8.0 * u
            p.blink = True
            p.mouth_open = 0.1

    return p


def _draw_tail(img: Image.Image, p: Pose) -> None:
    cx = 53.0 + p.body_x + p.tail_x
    cy = 107.0 + p.body_y + p.tail_y

    def draw_tail(d: ImageDraw.ImageDraw) -> None:
        pts = [
            (cx - 30.0 * p.tail_flatten, cy - 10.0),
            (cx - 17.0 * p.tail_flatten, cy - 18.0),
            (cx + 6.0, cy - 12.0),
            (cx + 13.0, cy),
            (cx + 4.0, cy + 12.0),
            (cx - 18.0 * p.tail_flatten, cy + 17.0),
            (cx - 31.0 * p.tail_flatten, cy + 8.0),
        ]
        d.polygon([_pt(*q) for q in pts], fill=_rgba(TAIL_DARK), outline=_rgba(OUTLINE))
        inner = [
            (cx - 25.0 * p.tail_flatten, cy - 7.0),
            (cx - 15.0 * p.tail_flatten, cy - 13.0),
            (cx + 5.0, cy - 8.0),
            (cx + 8.0, cy),
            (cx + 2.0, cy + 8.0),
            (cx - 16.0 * p.tail_flatten, cy + 12.0),
            (cx - 26.0 * p.tail_flatten, cy + 6.0),
        ]
        d.polygon([_pt(*q) for q in inner], fill=_rgba(TAIL_MID))
        # Cross-hatched paddle texture.
        for off in (-16, -7, 2):
            d.line(
                [_pt(cx - 25.0 * p.tail_flatten, cy + off), _pt(cx + 6.0, cy + off + 8.0)],
                fill=_rgba(TAIL_LIGHT),
                width=_s(0.8),
            )
        for off in (-18, -7, 4):
            d.line(
                [_pt(cx + off, cy - 12.0), _pt(cx + off - 8.0, cy + 11.0)],
                fill=_rgba(OUTLINE_SOFT),
                width=_s(0.65),
            )

    layer = _rotated_layer(img.size, draw_tail, p.tail_angle, (cx + 8.0, cy))
    img.alpha_composite(layer)


def _draw_leg(draw: ImageDraw.ImageDraw, hip: Point, foot: Point, far: bool) -> None:
    hx, hy = hip
    fx, fy = foot
    color = _rgba(FUR_DARK if far else FUR_MID)
    outline = _rgba(OUTLINE)
    knee = ((hx + fx) * 0.5 + (2.0 if far else -2.0), (hy + fy) * 0.5)
    draw.line([_pt(hx, hy), _pt(*knee), _pt(fx, fy - 4.0)], fill=outline, width=_s(13.0))
    draw.line([_pt(hx, hy), _pt(*knee), _pt(fx, fy - 4.0)], fill=color, width=_s(9.0))
    draw.ellipse(_box(fx - 8.5, fy - 6.0, fx + 9.0, fy + 2.0), fill=color, outline=outline, width=_s(1.3))
    # Broad webbed toes.
    for dx in (-4.5, 0.0, 4.5):
        draw.line([_pt(fx + dx - 1.8, fy - 2.0), _pt(fx + dx + 2.5, fy)], fill=_rgba(FUR_LIGHT), width=_s(0.8))


def _draw_arm(draw: ImageDraw.ImageDraw, shoulder: Point, hand: Point, far: bool) -> None:
    sx, sy = shoulder
    hx, hy = hand
    color = _rgba(FUR_DARK if far else FUR_MID)
    outline = _rgba(OUTLINE)
    elbow = ((sx + hx) * 0.5 + (-3.0 if far else 3.0), (sy + hy) * 0.5)
    draw.line([_pt(sx, sy), _pt(*elbow), _pt(hx, hy)], fill=outline, width=_s(11.0))
    draw.line([_pt(sx, sy), _pt(*elbow), _pt(hx, hy)], fill=color, width=_s(7.0))
    draw.ellipse(_box(hx - 5.0, hy - 4.0, hx + 5.5, hy + 5.0), fill=color, outline=outline, width=_s(1.0))
    draw.line([_pt(hx - 2.5, hy + 1.0), _pt(hx + 4.0, hy + 2.0)], fill=_rgba(FUR_LIGHT), width=_s(0.8))


def _draw_body(img: Image.Image, p: Pose) -> None:
    # Draw the body as one transformable layer so attack/death poses remain connected.
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = blending_draw(layer)
    bx = 79.0 + p.body_x
    by = 96.0 + p.body_y

    # Far limbs behind torso.
    _draw_leg(draw, (68.0 + p.body_x, 113.0 + p.body_y), p.far_foot, True)
    _draw_arm(draw, (61.0 + p.body_x, 81.0 + p.body_y), p.far_hand, True)

    # Stocky pear-shaped torso.
    torso = [
        (56.0 + p.body_x, 74.0 + p.body_y),
        (70.0 + p.body_x, 66.0 + p.body_y),
        (91.0 + p.body_x, 68.0 + p.body_y),
        (104.0 + p.body_x, 80.0 + p.body_y),
        (108.0 + p.body_x, 104.0 + p.body_y),
        (101.0 + p.body_x, 120.0 + p.body_y),
        (84.0 + p.body_x, 126.0 + p.body_y),
        (65.0 + p.body_x, 124.0 + p.body_y),
        (53.0 + p.body_x, 109.0 + p.body_y),
        (50.0 + p.body_x, 90.0 + p.body_y),
    ]
    draw.polygon([_pt(*q) for q in torso], fill=_rgba(FUR_DARK), outline=_rgba(OUTLINE))

    belly = [
        (62.0 + p.body_x, 82.0 + p.body_y),
        (74.0 + p.body_x, 73.0 + p.body_y),
        (91.0 + p.body_x, 76.0 + p.body_y),
        (99.0 + p.body_x, 91.0 + p.body_y),
        (96.0 + p.body_x, 111.0 + p.body_y),
        (84.0 + p.body_x, 120.0 + p.body_y),
        (68.0 + p.body_x, 116.0 + p.body_y),
        (59.0 + p.body_x, 103.0 + p.body_y),
    ]
    draw.polygon([_pt(*q) for q in belly], fill=_rgba(FUR_MID))

    # Work vest follows the torso rather than floating as a rectangle.
    vest = [
        (55.5 + p.body_x, 79.0 + p.body_y),
        (68.0 + p.body_x, 70.5 + p.body_y),
        (79.0 + p.body_x, 76.0 + p.body_y),
        (90.5 + p.body_x, 70.5 + p.body_y),
        (103.0 + p.body_x, 81.0 + p.body_y),
        (104.0 + p.body_x, 106.0 + p.body_y),
        (92.0 + p.body_x, 114.0 + p.body_y),
        (81.0 + p.body_x, 109.0 + p.body_y),
        (69.0 + p.body_x, 115.0 + p.body_y),
        (55.0 + p.body_x, 105.0 + p.body_y),
    ]
    draw.polygon([_pt(*q) for q in vest], fill=_rgba(VEST_DARK), outline=_rgba(OUTLINE))
    draw.polygon(
        [_pt(61.0 + p.body_x, 80.0 + p.body_y), _pt(72.0 + p.body_x, 74.0 + p.body_y), _pt(77.0 + p.body_x, 108.0 + p.body_y), _pt(64.0 + p.body_x, 112.0 + p.body_y)],
        fill=_rgba(VEST_MID),
    )
    draw.polygon(
        [_pt(87.0 + p.body_x, 74.0 + p.body_y), _pt(99.0 + p.body_x, 81.0 + p.body_y), _pt(98.0 + p.body_x, 108.0 + p.body_y), _pt(83.0 + p.body_x, 108.0 + p.body_y)],
        fill=_rgba(VEST_MID),
    )
    draw.line([_pt(80.0 + p.body_x, 76.0 + p.body_y), _pt(80.0 + p.body_x, 112.0 + p.body_y)], fill=_rgba(VEST_LIGHT), width=_s(1.1))
    # Tool belt and small integrated tools; no held prop.
    draw.rounded_rectangle(_box(57.0 + p.body_x, 105.0 + p.body_y, 103.0 + p.body_x, 114.0 + p.body_y), radius=_s(3.0), fill=_rgba(BELT), outline=_rgba(OUTLINE), width=_s(1.0))
    draw.rectangle(_box(67.0 + p.body_x, 106.5 + p.body_y, 77.0 + p.body_x, 115.0 + p.body_y), fill=_rgba(FUR_LIGHT), outline=_rgba(OUTLINE), width=_s(0.8))
    draw.line([_pt(93.0 + p.body_x, 105.0 + p.body_y), _pt(93.0 + p.body_x, 114.0 + p.body_y)], fill=_rgba(METAL), width=_s(2.2))

    # Near limbs in front.
    _draw_leg(draw, (89.0 + p.body_x, 113.0 + p.body_y), p.near_foot, False)
    _draw_arm(draw, (99.0 + p.body_x, 80.0 + p.body_y), p.near_hand, False)

    # Head: side-facing but turned enough toward camera to read both eyes.
    hx = 85.0 + p.body_x + p.head_x
    hy = 52.0 + p.body_y + p.head_y
    head = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = blending_draw(head)
    hd.ellipse(_box(hx - 28.0, hy - 23.0, hx + 24.0, hy + 24.0), fill=_rgba(FUR_DARK), outline=_rgba(OUTLINE), width=_s(1.5))
    hd.ellipse(_box(hx - 23.0, hy - 18.0, hx + 19.0, hy + 18.0), fill=_rgba(FUR_MID))
    # Ears remain attached to head silhouette.
    hd.ellipse(_box(hx - 22.0, hy - 23.0, hx - 9.0, hy - 9.0), fill=_rgba(FUR_DARK), outline=_rgba(OUTLINE), width=_s(1.0))
    hd.ellipse(_box(hx - 19.0, hy - 20.0, hx - 12.0, hy - 12.0), fill=_rgba(FUR_LIGHT))
    hd.ellipse(_box(hx + 4.0, hy - 24.0, hx + 17.0, hy - 11.0), fill=_rgba(FUR_DARK), outline=_rgba(OUTLINE), width=_s(1.0))
    hd.ellipse(_box(hx + 7.0, hy - 21.0, hx + 14.0, hy - 14.0), fill=_rgba(FUR_LIGHT))

    # Eyes and brows.
    eye_y = hy - 4.0
    for ex, far in ((hx - 7.0, True), (hx + 7.0, False)):
        if p.blink:
            hd.line([_pt(ex - 3.0, eye_y), _pt(ex + 3.0, eye_y + 0.5)], fill=_rgba(OUTLINE), width=_s(1.2))
        else:
            hd.ellipse(_box(ex - 4.0, eye_y - 4.0, ex + 4.0, eye_y + 4.2), fill=_rgba(EYE_WHITE), outline=_rgba(OUTLINE), width=_s(0.8))
            hd.ellipse(_box(ex + (0.4 if far else 0.9) - 1.7, eye_y - 1.8, ex + (0.4 if far else 0.9) + 1.7, eye_y + 1.8), fill=_rgba(EYE))
        hd.line([_pt(ex - 4.0, eye_y - 7.0 - p.brow), _pt(ex + 4.0, eye_y - 6.0 + p.brow)], fill=_rgba(OUTLINE), width=_s(1.2))

    # Broad muzzle, nose, and iconic incisors.
    hd.ellipse(_box(hx - 18.0, hy + 5.0, hx + 17.0, hy + 24.0), fill=_rgba(MUZZLE), outline=_rgba(OUTLINE), width=_s(1.0))
    hd.ellipse(_box(hx - 13.0, hy + 8.0, hx + 12.0, hy + 20.0), fill=_rgba(MUZZLE_LIGHT))
    hd.ellipse(_box(hx - 5.0, hy + 2.0, hx + 7.0, hy + 11.0), fill=_rgba(NOSE), outline=_rgba(OUTLINE), width=_s(0.7))
    mouth_y = hy + 17.0
    if p.mouth_open > 0.05:
        hd.ellipse(_box(hx - 7.0, mouth_y - 1.0, hx + 8.0, mouth_y + 3.0 + 7.0 * p.mouth_open), fill=_rgba(OUTLINE))
    else:
        hd.line([_pt(hx, mouth_y - 1.0), _pt(hx, mouth_y + 4.0)], fill=_rgba(OUTLINE), width=_s(0.9))
    hd.rounded_rectangle(_box(hx - 7.0, mouth_y + 2.0, hx - 0.5, mouth_y + 13.0), radius=_s(1.0), fill=_rgba(TOOTH), outline=_rgba(OUTLINE), width=_s(0.8))
    hd.rounded_rectangle(_box(hx + 0.5, mouth_y + 2.0, hx + 7.0, mouth_y + 13.0), radius=_s(1.0), fill=_rgba(TOOTH), outline=_rgba(OUTLINE), width=_s(0.8))
    hd.line([_pt(hx, mouth_y + 3.0), _pt(hx, mouth_y + 12.0)], fill=_rgba(MUZZLE), width=_s(0.7))

    # Dented hard hat; its brim overlaps the forehead so it feels worn, not floating.
    hat = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hdraw = blending_draw(hat)
    hdraw.rounded_rectangle(_box(hx - 25.0, hy - 31.0, hx + 22.0, hy - 20.0), radius=_s(4.0), fill=_rgba(HAT_DARK), outline=_rgba(OUTLINE), width=_s(1.2))
    hdraw.pieslice(_box(hx - 21.0, hy - 46.0, hx + 18.0, hy - 16.0), 180, 360, fill=_rgba(HAT), outline=_rgba(OUTLINE), width=_s(1.2))
    hdraw.polygon([_pt(hx - 2.0, hy - 44.0), _pt(hx + 4.0, hy - 42.0), _pt(hx + 1.0, hy - 25.0), _pt(hx - 5.0, hy - 25.0)], fill=_rgba(HAT_LIGHT))
    hdraw.line([_pt(hx - 18.0, hy - 27.0), _pt(hx + 18.0, hy - 27.0)], fill=_rgba(HAT_LIGHT), width=_s(1.2))
    if abs(p.hat_angle) > 0.01:
        hat = hat.rotate(p.hat_angle, resample=Image.Resampling.BICUBIC, center=_pt(hx, hy - 22.0), fillcolor=(0, 0, 0, 0))
    head.alpha_composite(hat)
    if abs(p.head_angle) > 0.01:
        head = head.rotate(p.head_angle, resample=Image.Resampling.BICUBIC, center=_pt(hx, hy + 8.0), fillcolor=(0, 0, 0, 0))
    layer.alpha_composite(head)

    if abs(p.body_angle) > 0.01 or p.squash_x != 1.0 or p.squash_y != 1.0:
        # Apply scale about the grounded body center before rotation.
        if p.squash_x != 1.0 or p.squash_y != 1.0:
            crop = layer.crop(_box(38.0, 25.0, 122.0, 145.0))
            target = (_s(84.0 * p.squash_x), _s(120.0 * p.squash_y))
            crop = crop.resize(target, Image.Resampling.BICUBIC)
            scaled = Image.new("RGBA", layer.size, (0, 0, 0, 0))
            x = _s(80.0) - target[0] // 2
            y = _s(140.0) - target[1]
            scaled.alpha_composite(crop, (x, y))
            layer = scaled
        layer = layer.rotate(p.body_angle, resample=Image.Resampling.BICUBIC, center=_pt(bx, 128.0 + p.body_y), fillcolor=(0, 0, 0, 0))

    img.alpha_composite(layer)


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p = _pose(animation, frame_idx, nframes)
    _draw_tail(img, p)
    _draw_body(img, p)
    return _downsample(img)


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=116,
        actor_metadata=ACTOR_METADATA,
        auto_crop=False,
        trim=False,
    )
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
    ]


__all__ = [
    "ACTOR_METADATA",
    "ROWS",
    "SHEET_FILES",
    "TARGET_NAME",
    "render",
    "render_frame",
]
