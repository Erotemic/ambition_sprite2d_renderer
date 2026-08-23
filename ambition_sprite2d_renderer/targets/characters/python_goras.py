"""Procedural sprite target for Python Goras.

Python Goras is a playful Pythagoras parody: a mystic geometer in a white toga
with a living green python draped around his shoulders. The silhouette leans
into three readable themes at once:

- the philosopher-mathematician (beard, robe, sandals, scroll);
- the snake pun (a bright python companion that coils through most poses);
- triangle / ratio iconography (a bronze triangle medallion and luminous
  theorem glyphs during combat / taunt poses).

Authoring intent:
- The parody is Pythagoras, but transformed into a more game-readable cartoon
  sage whose seriousness keeps getting undercut by a very expressive snake.
- The sprite should read as a roster scientist / mathematician immediately,
  even before dialogue.
- The move language is geometry-first rather than weapon-first: theorem sigils,
  angle cuts, and triangular spacing tools.

Suggested gameplay role:
- Mid-range control / zoner with a geometry gimmick.
- The python acts like a visual extension of his reach.
- His strongest fantasy is "I know where you must stand" — shaping space with
  triangles, beams, and line segments rather than brute force.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "python_goras"
FRAME_SIZE = (128, 128)
SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 150),
    ("walk", 8, 96),
    ("talk", 8, 112),
    ("taunt", 8, 108),
    ("slash", 7, 84),
    ("hurt", 4, 86),
    ("death", 8, 112),
]

AUTHORING_DESCRIPTION = (
    "Parody of Pythagoras. The joke is not just the near-homophone 'Python '"
    "Goras'; the design pushes him toward a mystical mathematician whose "
    "relationship with triangles, ratios, and secretive doctrine is constantly "
    "literalized by a pet python. Visual inspirations include classical Greek "
    "philosopher iconography, schoolbook right-triangle diagrams, occult "
    "geometry, and cartoon snake charmers. The costume stays mostly toga-based "
    "so he still reads as Pythagoras rather than as a generic wizard."
)

GAMEPLAY_DESCRIPTION = (
    "A mid-range geometry controller. Python Goras should pressure space with "
    "triangle-shaped hit areas, measured pokes, and serpent-assisted lashes. "
    "He reads best as a thoughtful spacing character: not the heaviest hitter, "
    "but good at creating awkward approach angles and rewarding clean positioning. "
    "A future bespoke kit could include a right-triangle dash cut, a harmonic "
    "projectile, and a theorem stance that changes the angle of his follow-up."
)

SUGGESTED_BARKS = [
    "Observe the hypotenuse.",
    "All things are number!",
    "Mind the angle.",
    "The serpent agrees.",
    "You stand at the wrong vertex.",
]

FALLBACK_DIALOGUE_LINES = [
    "I seek the hidden ratios beneath ordinary things.",
    "Most people remember the triangle. Fewer remember the cult.",
    "The python is not symbolic. He simply chose to stay.",
    "Harmony, number, and a clean right angle can solve more than people think.",
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_python_goras", "display_name": "Python Goras"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "locomotion_hint": "Walk",
        "traits": [
            "humanoid",
            "mathematician",
            "philosopher",
            "snake_companion",
            "geometry_mage",
            "playable_candidate",
        ],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": None,
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
        "face_guide": {
            "center": {"x": 64.0, "y": 27.0},
            "size": {"w": 28.0, "h": 30.0},
            "source_size": {"w": 128.0, "h": 128.0},
        },
        "portrait": {"animation": "idle", "frame": 1},
    },
    "tags": [
        "humanoid",
        "mathematician",
        "philosopher",
        "snake_companion",
        "geometry_mage",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "python_goras.geometry", "point": {"x": 64.0, "y": 26.0}},
        "chest": {"source": "python_goras.geometry", "point": {"x": 64.0, "y": 60.0}},
        "hand_l": {"source": "python_goras.geometry", "point": {"x": 47.0, "y": 70.0}},
        "hand_r": {"source": "python_goras.geometry", "point": {"x": 83.0, "y": 70.0}},
        "speech_bubble": {
            "source": "python_goras.geometry",
            "point": {"x": 64.0, "y": 4.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
        "action.melee.primary": {"animation": "slash", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "dialogue_hints": {
        "barks": SUGGESTED_BARKS,
        "fallback_lines": FALLBACK_DIALOGUE_LINES,
    },
    "authoring": {
        "authoring_description": AUTHORING_DESCRIPTION,
        "gameplay_description": GAMEPLAY_DESCRIPTION,
    },
}

OUTLINE = (24, 18, 18, 255)
OUTLINE_SOFT = (63, 49, 45, 255)
SKIN = (206, 158, 116, 255)
SKIN_SHADE = (153, 108, 76, 255)
SKIN_LIGHT = (230, 188, 146, 255)
HAIR = (53, 38, 31, 255)
HAIR_LIGHT = (90, 64, 53, 255)
BEARD = (74, 57, 46, 255)
TOGA = (245, 241, 224, 255)
TOGA_SHADE = (216, 206, 183, 255)
TOGA_DEEP = (171, 159, 136, 255)
SANDAL = (108, 76, 45, 255)
PYTHON_GREEN = (102, 165, 81, 255)
PYTHON_DARK = (61, 106, 56, 255)
PYTHON_LIGHT = (156, 211, 120, 255)
PYTHON_BELLY = (225, 219, 165, 255)
EYE = (32, 26, 22, 255)
MOUTH = (122, 63, 60, 255)
SCROLL = (229, 219, 178, 255)
SCROLL_SHADE = (191, 173, 128, 255)
BRONZE = (187, 142, 71, 255)
BRONZE_LIGHT = (224, 184, 96, 255)
GLYPH = (130, 220, 255, 220)
GLYPH_DIM = (88, 150, 198, 140)
HIT_RED = (192, 86, 83, 120)
TRANSPARENT = (0, 0, 0, 0)


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(p: Point) -> Tuple[int, int]:
    return (_s(p[0]), _s(p[1]))


def _line(draw: ImageDraw.ImageDraw, pts: List[Point], fill: RGBA, width: float) -> None:
    draw.line([_pt(p) for p in pts], fill=fill, width=max(1, _s(width)), joint="curve")


def _poly(
    draw: ImageDraw.ImageDraw,
    pts: List[Point],
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    qp = [_pt(p) for p in pts]
    draw.polygon(qp, fill=fill)
    if outline is not None:
        draw.line(qp + [qp[0]], fill=outline, width=max(1, _s(width)), joint="curve")


def _circle(
    draw: ImageDraw.ImageDraw,
    center: Point,
    radius: float,
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    box = (
        _s(center[0] - radius),
        _s(center[1] - radius),
        _s(center[0] + radius),
        _s(center[1] + radius),
    )
    draw.ellipse(box, fill=fill, outline=outline, width=max(1, _s(width)) if outline else 0)


def _arc(
    draw: ImageDraw.ImageDraw,
    center: Point,
    rx: float,
    ry: float,
    start_deg: float,
    end_deg: float,
    fill: RGBA,
    width: float,
) -> None:
    box = (
        _s(center[0] - rx),
        _s(center[1] - ry),
        _s(center[0] + rx),
        _s(center[1] + ry),
    )
    draw.arc(box, start=start_deg, end=end_deg, fill=fill, width=max(1, _s(width)))


def _osc(i: int, n: int, phase: float = 0.0) -> float:
    return math.sin((i / max(1, n)) * math.tau + phase)


def _draw_triangle_glyph(draw: ImageDraw.ImageDraw, center: Point, scale: float, glow: RGBA) -> None:
    pts = [
        (center[0], center[1] - 8.0 * scale),
        (center[0] - 7.0 * scale, center[1] + 5.5 * scale),
        (center[0] + 7.0 * scale, center[1] + 5.5 * scale),
    ]
    _poly(draw, pts, (0, 0, 0, 0), outline=glow, width=1.4 * scale)
    _line(draw, [pts[1], ((pts[1][0] + pts[2][0]) / 2.0, pts[1][1] - 3.2 * scale), pts[2]], glow, 1.0 * scale)


def _draw_python(
    draw: ImageDraw.ImageDraw,
    *,
    shoulder_y: float,
    sway: float,
    emphasis: float,
    head_lift: float,
    body_dx: float,
) -> None:
    # Tail / body wrap.
    body = [
        (48 + body_dx, shoulder_y + 6),
        (42 + body_dx + sway * 1.5, shoulder_y + 12),
        (46 + body_dx + sway * 2.0, shoulder_y + 19),
        (59 + body_dx + sway * 0.6, shoulder_y + 21),
        (77 + body_dx - sway * 0.7, shoulder_y + 19),
        (88 + body_dx - sway * 1.2, shoulder_y + 12),
        (84 + body_dx, shoulder_y + 4),
    ]
    _line(draw, body, OUTLINE, 7.4)
    _line(draw, body, PYTHON_DARK, 5.6)
    _line(draw, body, PYTHON_GREEN, 4.4)
    for x, y in body[1:-1]:
        _circle(draw, (x, y + 0.6), 1.1, PYTHON_LIGHT, outline=None)
    # Belly band.
    belly = [(57 + body_dx, shoulder_y + 18), (72 + body_dx, shoulder_y + 17), (81 + body_dx, shoulder_y + 13)]
    _line(draw, belly, PYTHON_BELLY, 1.8)
    # Head.
    head_center = (88 + body_dx + sway * 0.4, shoulder_y - 2 - head_lift)
    _circle(draw, head_center, 5.5 + emphasis * 0.3, PYTHON_GREEN, outline=OUTLINE, width=1.0)
    _circle(draw, (head_center[0] + 1.6, head_center[1] - 0.8), 2.2, PYTHON_LIGHT, outline=None)
    _circle(draw, (head_center[0] + 1.6, head_center[1] - 0.5), 0.75, EYE, outline=None)
    _line(draw, [(head_center[0] + 4.8, head_center[1] + 0.7), (head_center[0] + 8.0, head_center[1] + 1.5)], MOUTH, 0.9)
    tongue_end = (head_center[0] + 10.8 + emphasis * 1.6, head_center[1] + 2.0)
    _line(draw, [(head_center[0] + 7.7, head_center[1] + 1.7), tongue_end], (188, 58, 88, 255), 0.8)
    _line(draw, [tongue_end, (tongue_end[0] + 2.2, tongue_end[1] - 1.3)], (188, 58, 88, 255), 0.7)
    _line(draw, [tongue_end, (tongue_end[0] + 2.1, tongue_end[1] + 1.2)], (188, 58, 88, 255), 0.7)


def _draw_character(anim: str, i: int, n: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), TRANSPARENT)
    draw = blending_draw(img)

    t = i / max(1, n - 1)
    bob = _osc(i, n) * (1.0 if anim in {"walk", "talk", "taunt"} else 0.6)
    body_shift = 0.0
    lean = 0.0
    arm_raise_r = 0.0
    arm_raise_l = 0.0
    glyph = 0.0
    head_lift = 0.0
    robe_spread = 0.0
    collapse = 0.0
    hurt_flash = 0.0
    scroll_visible = True

    if anim == "walk":
        body_shift = _osc(i, n, math.pi / 2) * 2.8
        robe_spread = abs(_osc(i, n)) * 4.0
        arm_raise_r = _osc(i, n) * 10.0
        arm_raise_l = -_osc(i, n) * 8.0
    elif anim == "talk":
        arm_raise_r = 8.0 + _osc(i, n) * 6.0
        arm_raise_l = -4.0 + _osc(i, n, math.pi / 2) * 5.0
        glyph = 0.6 + 0.4 * (0.5 + 0.5 * _osc(i, n))
        head_lift = 0.5
    elif anim == "taunt":
        arm_raise_r = 18.0 + _osc(i, n) * 4.0
        arm_raise_l = 10.0 + _osc(i, n, math.pi / 2) * 4.0
        glyph = 1.0
        head_lift = 1.4
        robe_spread = 1.5
    elif anim == "slash":
        lean = -10.0 + 22.0 * t
        body_shift = -10.0 + 20.0 * t
        arm_raise_r = 35.0 - 65.0 * t
        arm_raise_l = -12.0 + 10.0 * t
        glyph = max(0.0, math.sin(t * math.pi))
        head_lift = glyph * 2.0
        scroll_visible = t < 0.4
    elif anim == "hurt":
        lean = -16.0
        body_shift = -4.0
        arm_raise_r = -12.0
        arm_raise_l = -8.0
        hurt_flash = 0.65 + 0.25 * _osc(i, n)
        head_lift = 1.0
    elif anim == "death":
        collapse = t
        lean = 58.0 * t
        body_shift = 8.0 * t
        arm_raise_r = -18.0 * t
        arm_raise_l = -10.0 * t
        glyph = max(0.0, 0.7 - t)
        head_lift = -4.0 * t
        scroll_visible = t < 0.25

    cx = 64 + body_shift
    base_y = 104 + collapse * 12.0
    shoulder_y = 48 + bob * 0.7 + collapse * 6.0
    hip_y = 76 + bob * 0.6 + collapse * 7.0
    head_y = 26 + bob * 0.35 + collapse * 3.0 - head_lift

    # Legs and sandals
    step = _osc(i, n) if anim == "walk" else 0.0
    left_foot = (cx - 10 - step * 5.0 + collapse * 10.0, base_y)
    right_foot = (cx + 8 + step * 5.0 + collapse * 4.0, base_y - collapse * 3.0)
    left_knee = (cx - 9 + step * 1.5, hip_y + 12 + abs(step) * 2.5 + collapse * 4.0)
    right_knee = (cx + 8 - step * 1.5, hip_y + 11 + abs(step) * 1.4 + collapse * 2.0)
    _line(draw, [(cx - 7, hip_y), left_knee, left_foot], OUTLINE, 4.0)
    _line(draw, [(cx - 7, hip_y), left_knee, left_foot], TOGA_DEEP, 2.4)
    _line(draw, [(cx + 7, hip_y), right_knee, right_foot], OUTLINE, 4.0)
    _line(draw, [(cx + 7, hip_y), right_knee, right_foot], TOGA_DEEP, 2.4)
    _poly(draw, [
        (left_foot[0] - 6, left_foot[1] + 2),
        (left_foot[0] + 6, left_foot[1] + 2),
        (left_foot[0] + 5, left_foot[1] + 6),
        (left_foot[0] - 7, left_foot[1] + 6),
    ], SANDAL)
    _poly(draw, [
        (right_foot[0] - 6, right_foot[1] + 2),
        (right_foot[0] + 6, right_foot[1] + 2),
        (right_foot[0] + 5, right_foot[1] + 6),
        (right_foot[0] - 7, right_foot[1] + 6),
    ], SANDAL)

    # Toga body.
    robe_pts = [
        (cx - 18 - robe_spread * 0.7, shoulder_y + 4),
        (cx - 24 - robe_spread, hip_y + 16),
        (cx - 18 - robe_spread * 0.4, base_y - 3),
        (cx + 22 + robe_spread * 0.5, base_y - 3),
        (cx + 25 + robe_spread, hip_y + 12),
        (cx + 15, shoulder_y + 4),
        (cx + 2, shoulder_y - 2),
    ]
    _poly(draw, robe_pts, TOGA, outline=OUTLINE, width=1.0)
    _poly(draw, [
        (cx - 16, shoulder_y + 6),
        (cx - 8, hip_y + 16),
        (cx - 2, base_y - 2),
        (cx + 3, base_y - 2),
        (cx - 1, hip_y + 7),
        (cx - 4, shoulder_y + 7),
    ], TOGA_SHADE, outline=None)
    _poly(draw, [
        (cx + 2, shoulder_y + 4),
        (cx + 13, hip_y + 10),
        (cx + 17, base_y - 4),
        (cx + 21, base_y - 4),
        (cx + 19, hip_y + 8),
        (cx + 8, shoulder_y + 4),
    ], TOGA_SHADE, outline=None)

    # Gold triangle medallion.
    med_y = shoulder_y + 19
    _poly(draw, [
        (cx + 1, med_y - 4),
        (cx - 4, med_y + 5),
        (cx + 6, med_y + 5),
    ], BRONZE, outline=OUTLINE, width=0.8)
    _circle(draw, (cx + 1, med_y + 2), 0.9, BRONZE_LIGHT, outline=None)

    # Arms.
    shoulder_l = (cx - 13, shoulder_y + 5)
    shoulder_r = (cx + 12, shoulder_y + 3)
    elbow_l = (cx - 19, shoulder_y + 20 + arm_raise_l * 0.16)
    hand_l = (cx - 20, shoulder_y + 33 + arm_raise_l * 0.34)
    elbow_r = (cx + 22, shoulder_y + 18 - arm_raise_r * 0.12)
    hand_r = (cx + 27, shoulder_y + 31 - arm_raise_r * 0.42)
    if anim == "death":
        hand_l = (hand_l[0] + 18 * collapse, hand_l[1] + 2 * collapse)
        hand_r = (hand_r[0] + 4 * collapse, hand_r[1] + 8 * collapse)
    _line(draw, [shoulder_l, elbow_l, hand_l], OUTLINE, 4.2)
    _line(draw, [shoulder_l, elbow_l, hand_l], TOGA, 2.6)
    _line(draw, [shoulder_r, elbow_r, hand_r], OUTLINE, 4.2)
    _line(draw, [shoulder_r, elbow_r, hand_r], TOGA, 2.6)
    _circle(draw, hand_l, 2.8, SKIN, outline=OUTLINE, width=0.8)
    _circle(draw, hand_r, 2.8, SKIN, outline=OUTLINE, width=0.8)

    # Scroll in left hand where appropriate.
    if scroll_visible:
        scroll_c = (hand_l[0] - 5, hand_l[1] + 2)
        _poly(draw, [
            (scroll_c[0] - 6, scroll_c[1] - 4),
            (scroll_c[0] + 6, scroll_c[1] - 3),
            (scroll_c[0] + 5, scroll_c[1] + 4),
            (scroll_c[0] - 7, scroll_c[1] + 3),
        ], SCROLL, outline=OUTLINE, width=0.8)
        _arc(draw, (scroll_c[0] - 7, scroll_c[1]), 2.0, 2.4, 70, 290, SCROLL_SHADE, 1.0)
        _arc(draw, (scroll_c[0] + 6, scroll_c[1]), 2.0, 2.4, -110, 110, SCROLL_SHADE, 1.0)

    # Head, hair, beard.
    _circle(draw, (cx, head_y), 11.5, SKIN, outline=OUTLINE, width=1.0)
    _circle(draw, (cx + 2.2, head_y - 2.0), 8.8, SKIN_LIGHT, outline=None)
    hair_pts = [
        (cx - 10, head_y - 2),
        (cx - 8, head_y - 10),
        (cx, head_y - 13),
        (cx + 10, head_y - 10),
        (cx + 12, head_y - 2),
        (cx + 9, head_y + 1),
        (cx + 5, head_y - 1),
        (cx - 2, head_y - 2),
        (cx - 7, head_y + 1),
    ]
    _poly(draw, hair_pts, HAIR, outline=OUTLINE, width=0.8)
    _line(draw, [(cx - 7, head_y - 5), (cx - 1, head_y - 9), (cx + 5, head_y - 6)], HAIR_LIGHT, 1.0)
    beard_pts = [
        (cx - 8, head_y + 5),
        (cx - 4, head_y + 12),
        (cx + 1, head_y + 16),
        (cx + 8, head_y + 10),
        (cx + 6, head_y + 4),
        (cx - 2, head_y + 7),
    ]
    _poly(draw, beard_pts, BEARD, outline=OUTLINE, width=0.8)

    eye_y = head_y - 0.8
    blink = anim == "talk" and i % 5 == 0
    if blink:
        _line(draw, [(cx - 4.4, eye_y), (cx - 1.3, eye_y)], EYE, 0.8)
        _line(draw, [(cx + 1.8, eye_y), (cx + 4.8, eye_y)], EYE, 0.8)
    else:
        _circle(draw, (cx - 2.8, eye_y), 0.9, EYE, outline=None)
        _circle(draw, (cx + 3.2, eye_y - 0.2), 0.9, EYE, outline=None)
    mouth_open = anim == "talk" and (i % 2 == 0)
    if mouth_open:
        _arc(draw, (cx + 0.5, head_y + 4.0), 2.4, 1.7, 15, 165, MOUTH, 0.9)
    else:
        _line(draw, [(cx - 1.7, head_y + 4.5), (cx + 3.0, head_y + 5.2)], MOUTH, 0.8)

    # Python companion draped over shoulders.
    _draw_python(
        draw,
        shoulder_y=shoulder_y - 1.0,
        sway=_osc(i, n, math.pi / 3) * (1.8 if anim != "death" else 0.8),
        emphasis=glyph,
        head_lift=arm_raise_r * 0.07 + collapse * -3.0,
        body_dx=body_shift * 0.25,
    )

    # Gesture glyphs / theorem effects.
    if glyph > 0.05:
        glow = tuple(int(a * glyph) if idx == 3 else int(v) for idx, (v, a) in enumerate(zip(GLYPH, GLYPH)))
        del glow
        alpha = int(180 * glyph)
        g1 = (GLYPH[0], GLYPH[1], GLYPH[2], alpha)
        g2 = (GLYPH_DIM[0], GLYPH_DIM[1], GLYPH_DIM[2], int(120 * glyph))
        _draw_triangle_glyph(draw, (hand_r[0] + 10, hand_r[1] - 10), 1.0 + 0.2 * glyph, g1)
        if anim in {"taunt", "talk", "slash"}:
            _draw_triangle_glyph(draw, (cx + 24, shoulder_y + 5), 0.8 + 0.3 * glyph, g2)
            _line(draw, [(hand_r[0] + 8, hand_r[1] - 2), (cx + 18, shoulder_y + 1), (cx + 24, shoulder_y + 12)], g2, 1.0)
        if anim == "slash":
            _line(draw, [(cx + 12, shoulder_y + 1), (cx + 40, shoulder_y - 4), (cx + 57, shoulder_y + 6)], g1, 2.2)
            _line(draw, [(cx + 12, shoulder_y + 8), (cx + 40, shoulder_y + 12), (cx + 57, shoulder_y + 3)], g2, 1.2)

    if hurt_flash > 0.1:
        overlay = Image.new("RGBA", (W, H), (255, 0, 0, 0))
        odraw = blending_draw(overlay)
        alpha = int(80 * hurt_flash)
        _poly(odraw, [
            (cx - 26, head_y - 14),
            (cx - 30, base_y + 8),
            (cx + 30, base_y + 8),
            (cx + 24, head_y - 14),
        ], (HIT_RED[0], HIT_RED[1], HIT_RED[2], alpha), outline=None)
        img.alpha_composite(overlay)

    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def render(out_dir: str | Path, **opts):
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_draw_character,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        auto_crop=True,
        actor_metadata=ACTOR_METADATA,
    )
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ]


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render Python Goras.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME,
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
