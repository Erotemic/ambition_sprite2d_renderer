"""Procedural full-action renderer for Le Beast.

Le Beast is an affectionate mathematical monster inspired by Henri Lebesgue.
The pun turns the surname into a theatrical creature title, while the combat
language turns measure theory into physical appetite: points have no substance,
measurable regions become translucent morsels, countable unions arrive as a
multi-course meal, and rearranged shapes retain the same total nourishment.

The character is not a portrait. He is a huge velvet-robed scholar-beast with a
brass measuring sash, chalky integral-shaped horns, a sigma medallion, and a maw
that opens onto an impossible gridded interior. Everything is rendered with
supersampled Pillow geometry and publishes through Ambition's normal character
target contract, including portraits and behind-the-scenes authoring metadata.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.portrait import PortraitClip, write_portrait_sheet
from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "le_beast"
FRAME_W = 128
FRAME_H = 128
SUPER = 4
PORTRAIT_SIZE = (192, 192)

AUTHORING_DESCRIPTION = {
    "parody_of": "Henri Lebesgue",
    "character_name": "Le Beast",
    "concept": (
        "A grand, ravenous measure-theory monster who judges every object by how much "
        "of it there is rather than by its individual points. Measurable regions become "
        "food, null sets pass through him without nourishment, and countable unions are "
        "served as elaborate courses beneath a glowing sigma seal."
    ),
    "name_origin": (
        "Le Beast is a phonetic monster-title transformation of Lebesgue. The joke is "
        "used to build a complete character rather than merely renaming the mathematician."
    ),
    "visual_inspiration": [
        "A huge scholarly beast in plum velvet combines lecture-hall dignity with storybook-monster mass.",
        "Chalk-white horns curl like elongated integral signs without literally printing notation on his head.",
        "A brass measuring tape crosses the body as a sash and a sigma medallion seals the robe.",
        "The open maw reveals a luminous coordinate grid, suggesting that swallowed regions are being measured rather than chewed.",
        "Translucent colored regions and tiny vanishing points make abstract set-measure ideas readable at sprite scale.",
    ],
    "gameplay_inspiration": [
        "measurable_maw bites a whole region while isolated points slip through harmlessly.",
        "null_set dissolves the body into scattered points that cannot be struck for a brief interval.",
        "sigma_swallow combines several disjoint regions into one countable-union feast.",
        "rearrangement chops and moves pieces while preserving the total visible area.",
        "dominated_convergence pulls a sequence of increasingly calm shapes toward one bounded final form.",
    ],
    "gameplay_description": (
        "A heavyweight space-control fighter who consumes broad regions and largely ignores "
        "point-like pokes. Le Beast is slow, difficult to dislodge, and strongest when opponents "
        "cluster inside measurable zones. His specials reshape or merge those zones without "
        "changing their total area, rewarding deliberate control rather than frantic pursuit."
    ),
    "suggested_barks": {
        "idle": [
            "A point? No nourishment at all.",
            "Bring me something measurable.",
            "I have an appetite for almost everywhere.",
        ],
        "combat": [
            "Countably many courses!",
            "Your shape changes. Your measure does not.",
            "Null. Entirely null!",
            "I consume the region, not the rumor of it.",
        ],
        "on_hit": [
            "A non-negligible impact!",
            "That had positive measure.",
        ],
        "victory": [
            "At last, a substantial meal.",
            "Convergence is served.",
        ],
    },
    "fallback_dialogue": [
        "You keep pointing at individual points. I keep telling you they have no weight by themselves.",
        "Cut the meal into pieces, rearrange it, plate it upside down. The amount remains the amount.",
        "Riemann invited only the well-behaved functions. I opened the dining hall.",
        "Almost everywhere is not everywhere. The exception may be tiny, but it remains an exception.",
        "The sigma on my clasp is not decoration. It is the menu.",
    ],
    "boundaries": [
        "Treat the design as a fictional mathematical homage, not a literal likeness or biographical claim.",
        "Keep the humor centered on measure theory, appetite, abstraction, and theatrical monster behavior.",
        "Do not present large body size itself as the joke; the joke is that measure has become appetite and mass.",
        "Le Beast should remain intelligent, precise, and imposing even when his hunger is absurd.",
    ],
}

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 150),
    ("walk", 8, 112),
    ("run", 8, 86),
    ("crouch", 6, 96),
    ("jump", 6, 92),
    ("fall", 6, 94),
    ("land_hard", 6, 90),
    ("dash", 7, 70),
    ("roll", 8, 70),
    ("block", 6, 86),
    ("hit", 5, 88),
    ("death", 8, 112),
    ("talk", 8, 108),
    ("interact", 8, 96),
    ("measurable_maw", 10, 72),
    ("null_set", 10, 74),
    ("sigma_swallow", 12, 70),
    ("rearrangement", 10, 76),
    ("dominated_convergence", 10, 80),
    ("celebrate", 8, 92),
    ("taunt", 8, 98),
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_le_beast", "display_name": "Le Beast"},
    "authoring_description": AUTHORING_DESCRIPTION,
    "body": {
        "body_plan": "BestialBiped",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": [
            "story", "beast", "mathematician", "measure_theorist", "heavyweight",
            "zone_controller", "playable_candidate",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True, "jump": True, "climb": None, "fly": None,
            "swim": None, "crawl": True, "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True, "trade": None, "carry": True,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "portrait": {"face_guide": {
            "center": {"x": 65.0, "y": 39.0},
            "size": {"w": 49.0, "h": 45.0},
            "source_size": {"w": 128.0, "h": 128.0},
        }},
    },
    "tags": [
        "story", "beast", "mathematician", "measure_theorist", "heavyweight",
        "zone_controller", "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.le_beast", "point": {"x": 65.0, "y": 38.0}},
        "chest": {"source": "explicit.le_beast", "point": {"x": 63.0, "y": 69.0}},
        "claw_l": {"source": "explicit.le_beast", "point": {"x": 36.0, "y": 75.0}},
        "claw_r": {"source": "explicit.le_beast", "point": {"x": 94.0, "y": 74.0}},
        "maw": {"source": "explicit.le_beast", "point": {"x": 72.0, "y": 47.0}},
        "speech_bubble": {"source": "explicit.le_beast", "point": {"x": 65.0, "y": 4.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "measurable_maw", "events": []},
        "action.special.primary": {"animation": "null_set", "events": []},
        "action.special.secondary": {"animation": "sigma_swallow", "events": []},
        "action.special.tertiary": {"animation": "rearrangement", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "gpt_5_6_thinking_original_2026_07_26",
        "lineage": [
            {
                "revision_id": "le_beast_concept_direction",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "contribution": "selected_le_beast_as_a_fun_henri_lebesgue_parody",
            },
            {
                "revision_id": "le_beast_procedural_sprite_v1",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "parent_revision_id": "le_beast_concept_direction",
                "contribution": "procedural_full_action_measure_theory_monster_with_portraits_barks_and_gameplay_notes",
            },
        ],
    },
}

OUTLINE = (24, 18, 29, 255)
OUTLINE_SOFT = (66, 47, 72, 255)
FUR = (91, 67, 72, 255)
FUR_LIGHT = (139, 102, 94, 255)
FUR_DARK = (53, 39, 48, 255)
VELVET = (83, 28, 78, 255)
VELVET_LIGHT = (131, 50, 118, 255)
VELVET_DARK = (48, 20, 54, 255)
BRASS = (196, 145, 55, 255)
BRASS_LIGHT = (243, 209, 100, 255)
CHALK = (231, 226, 206, 255)
MAW = (39, 17, 37, 255)
TONGUE = (173, 66, 100, 255)
GRID = (100, 229, 206, 255)
EYE = (250, 221, 104, 255)
CYAN = (73, 210, 209, 255)
MAGENTA = (219, 74, 173, 255)
LIME = (157, 218, 93, 255)
ORANGE = (240, 144, 57, 255)


def _fade(color: RGBA, alpha: float) -> RGBA:
    return color[:3] + (max(0, min(255, int(color[3] * alpha))),)


def _p(point: Point) -> Tuple[int, int]:
    return (round(point[0] * SUPER), round(point[1] * SUPER))


def _line(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, width: float = 1.0) -> None:
    draw.line([_p(p) for p in points], fill=fill, width=max(1, round(width * SUPER)), joint="curve")


def _ellipse(draw: ImageDraw.ImageDraw, box: Tuple[float, float, float, float], fill: RGBA, outline: RGBA | None = None, width: float = 1.0) -> None:
    b = tuple(round(v * SUPER) for v in box)
    draw.ellipse(b, fill=fill, outline=outline, width=max(1, round(width * SUPER)) if outline else 1)


def _poly(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, outline: RGBA | None = None, width: float = 1.0) -> None:
    pts = [_p(p) for p in points]
    draw.polygon(pts, fill=fill)
    if outline:
        draw.line(pts + [pts[0]], fill=outline, width=max(1, round(width * SUPER)), joint="curve")


def _arc(draw: ImageDraw.ImageDraw, box: Tuple[float, float, float, float], start: float, end: float, fill: RGBA, width: float = 1.0) -> None:
    b = tuple(round(v * SUPER) for v in box)
    draw.arc(b, start=start, end=end, fill=fill, width=max(1, round(width * SUPER)))


def _capsule(draw: ImageDraw.ImageDraw, a: Point, b: Point, radius: float, fill: RGBA, outline: RGBA = OUTLINE) -> None:
    _line(draw, [a, b], outline, radius * 2.0 + 2.0)
    _line(draw, [a, b], fill, radius * 2.0)


@dataclass(frozen=True)
class Pose:
    phase: float
    x: float = 0.0
    y: float = 0.0
    lean: float = 0.0
    squat: float = 0.0
    mouth: float = 0.16
    arm_l: float = 0.0
    arm_r: float = 0.0
    foot_l: float = 0.0
    foot_r: float = 0.0
    dissolve: float = 0.0
    power: float = 0.0
    expression: int = 0
    anim: str = "idle"


def _pose(anim: str, frame_idx: int, nframes: int) -> Pose:
    t = frame_idx / max(1, nframes)
    wave = math.sin(t * math.tau)
    p = Pose(t, y=wave * 1.2, arm_l=-wave * 5, arm_r=wave * 5, anim=anim)
    if anim == "walk":
        p = Pose(t, y=abs(wave) * 1.6, lean=2, arm_l=-wave * 16, arm_r=wave * 16, foot_l=wave * 9, foot_r=-wave * 9, anim=anim)
    elif anim == "run":
        p = Pose(t, y=abs(wave) * 2.3, lean=9, arm_l=-wave * 23, arm_r=wave * 23, foot_l=wave * 14, foot_r=-wave * 14, mouth=.2, anim=anim)
    elif anim == "crouch":
        p = Pose(t, y=5, squat=8 + 2 * math.sin(t * math.pi), arm_l=-12, arm_r=12, anim=anim)
    elif anim == "jump":
        p = Pose(t, y=-8 * math.sin(t * math.pi), lean=-4 + 8*t, arm_l=-22, arm_r=20, foot_l=-8, foot_r=8, mouth=.22, anim=anim)
    elif anim == "fall":
        p = Pose(t, y=-2 + 6*t, lean=5, arm_l=22, arm_r=-22, foot_l=6, foot_r=-6, mouth=.26, anim=anim)
    elif anim == "land_hard":
        impact = math.sin(t * math.pi)
        p = Pose(t, y=5*impact, squat=12*impact, arm_l=-28*impact, arm_r=28*impact, mouth=.3, power=impact, anim=anim)
    elif anim == "dash":
        p = Pose(t, x=3*math.sin(t*math.pi), y=1, lean=19, arm_l=-34, arm_r=30, foot_l=11*wave, foot_r=-11*wave, anim=anim)
    elif anim == "roll":
        p = Pose(t, y=8, squat=17, lean=t*360, mouth=.08, power=math.sin(t*math.pi), anim=anim)
    elif anim == "block":
        p = Pose(t, squat=4, arm_l=-45, arm_r=-35, mouth=.08, power=.35 + .15*wave, anim=anim)
    elif anim == "hit":
        hit = math.sin(t*math.pi)
        p = Pose(t, x=-5*hit, lean=-17*hit, arm_l=35*hit, arm_r=-30*hit, mouth=.55*hit, expression=1, power=hit, anim=anim)
    elif anim == "death":
        p = Pose(t, y=12*t, lean=-82*min(1, t*1.25), arm_l=30, arm_r=-30, mouth=.4, expression=2, anim=anim)
    elif anim == "talk":
        p = Pose(t, y=wave*.8, arm_l=-18+8*wave, arm_r=20-5*wave, mouth=.15+.35*abs(wave), anim=anim)
    elif anim == "interact":
        reach = math.sin(t*math.pi)
        p = Pose(t, lean=5*reach, arm_r=-55*reach, arm_l=8, power=reach, anim=anim)
    elif anim == "measurable_maw":
        power = math.sin(t*math.pi)
        p = Pose(t, lean=13*power, squat=3*power, arm_l=-25*power, arm_r=28*power, mouth=.12+.82*power, power=power, expression=3, anim=anim)
    elif anim == "null_set":
        power = math.sin(t*math.pi)
        p = Pose(t, y=-2*power, arm_l=-35*power, arm_r=35*power, dissolve=power, mouth=.1, power=power, anim=anim)
    elif anim == "sigma_swallow":
        power = math.sin(t*math.pi)
        p = Pose(t, lean=5*power, squat=5*power, arm_l=-42*power, arm_r=42*power, mouth=.18+.7*power, power=power, expression=3, anim=anim)
    elif anim == "rearrangement":
        power = math.sin(t*math.pi)
        p = Pose(t, arm_l=-55*power+15*wave, arm_r=55*power-15*wave, mouth=.2, power=power, anim=anim)
    elif anim == "dominated_convergence":
        power = math.sin(t*math.pi)
        p = Pose(t, y=-2*power, arm_l=-34*power, arm_r=34*power, mouth=.12, power=power, anim=anim)
    elif anim == "celebrate":
        p = Pose(t, y=-4*abs(wave), arm_l=-58+8*wave, arm_r=58-8*wave, mouth=.45, expression=4, anim=anim)
    elif anim == "taunt":
        p = Pose(t, arm_l=-8, arm_r=-28+12*wave, mouth=.18+.12*abs(wave), expression=5, power=.45+.25*wave, anim=anim)
    return p


def _draw_region(draw: ImageDraw.ImageDraw, cx: float, cy: float, rx: float, ry: float, color: RGBA, phase: float = 0.0) -> None:
    pts = []
    for i in range(12):
        a = i / 12 * math.tau
        wobble = 1 + .12 * math.sin(i * 2.3 + phase * math.tau)
        pts.append((cx + math.cos(a)*rx*wobble, cy + math.sin(a)*ry*wobble))
    _poly(draw, pts, _fade(color, .42), color, 1.2)
    for i in range(5):
        x = cx + math.cos(i*2.1+phase*3)*rx*.45
        y = cy + math.sin(i*1.7+phase*4)*ry*.45
        _ellipse(draw, (x-1.5, y-1.5, x+1.5, y+1.5), _fade(CHALK, .8))


def _draw_effects_behind(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    if pose.anim == "null_set":
        for i in range(22):
            a = i * 2.399 + pose.phase*2
            r = 9 + (i % 7) * 5 * pose.power
            x = 64 + math.cos(a)*r
            y = 61 + math.sin(a)*r*.72
            _ellipse(draw, (x-1.5, y-1.5, x+1.5, y+1.5), _fade(CYAN if i%2 else MAGENTA, .25+.55*pose.power))
    elif pose.anim == "sigma_swallow":
        colors = [CYAN, MAGENTA, LIME, ORANGE]
        for i, c in enumerate(colors):
            a = pose.phase*math.tau + i*math.pi/2
            r = 47*(1-pose.power*.55)
            _draw_region(draw, 64+math.cos(a)*r, 52+math.sin(a)*r*.48, 9, 6, c, pose.phase+i)
        _ellipse(draw, (42, 18, 86, 62), _fade(BRASS, .08+.17*pose.power), _fade(BRASS_LIGHT, .4), 1)
    elif pose.anim == "dominated_convergence":
        for i in range(5):
            k = i/4
            rx = 28 - 15*k*pose.power
            ry = 16 - 8*k*pose.power
            _draw_region(draw, 64, 44, rx, ry, _fade([CYAN,MAGENTA,LIME,ORANGE,BRASS_LIGHT][i], .35), pose.phase+i)
    elif pose.anim == "rearrangement":
        pieces = [(-29,-18,CYAN),(-10,-26,MAGENTA),(18,-20,LIME),(31,-5,ORANGE)]
        for i,(dx,dy,c) in enumerate(pieces):
            a = pose.phase*math.tau + i
            shift = pose.power*14
            _draw_region(draw, 64+dx+math.cos(a)*shift, 58+dy+math.sin(a)*shift*.5, 8, 6, c, pose.phase+i)


def _rig_piece(key: tuple, size: Tuple[float, float], origin: Point, paint) -> tuple:
    """A piece of Le Beast painted once (``shape_rig``): ``paint(draw)`` draws
    in frame units with its anchor at ``origin`` (frame units) on a ``size``
    (frame units) canvas. ``key`` names everything ``paint`` reads."""
    return shape_rig.piece(("le_beast",) + key, (size[0] * SUPER, size[1] * SUPER), (origin[0] * SUPER, origin[1] * SUPER), paint)


def _put(img: Image.Image, part: tuple, at: Point, name: str, degrees: float = 0.0) -> None:
    """``part`` with its anchor at the frame point ``at``, turned ``degrees``."""
    shape_rig.place(img, part, (at[0] * SUPER, at[1] * SUPER), degrees, name)


def _bone(img: Image.Image, a: Point, b: Point, length: float, radius: float, fill: RGBA, name: str) -> None:
    """``_capsule`` from ``a`` toward ``b`` as a bone of fixed ``length``,
    painted once along +x and turned into place about ``a``."""
    pad = radius + 3
    part = _rig_piece(
        ("bone", length, radius, fill), (length + 2 * pad, 2 * pad), (pad, pad),
        lambda d: _capsule(d, (pad, pad), (pad + length, pad), radius, fill),
    )
    _put(img, part, a, name, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))


def _frame_layer(img: Image.Image, paint, name: str) -> None:
    """A per-frame effect (it changes every frame) as ONE draw: ``paint(draw)``
    paints frame-unit coordinates into a fresh canvas, placed cropped."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    paint(blending_draw(layer))
    box = layer.getbbox()
    if box is not None:
        shape_rig.place(img, (layer.crop(box), (0.0, 0.0)), (float(box[0]), float(box[1])), 0.0, name)


#: The leg bone's fixed length (hip to ankle at rest); anchored at the ankle,
#: its hip end hides under the cloak when he squats.
LEG_LENGTH = 25.0


def _paint_foot(draw: ImageDraw.ImageDraw, side: int, ox: float, oy: float) -> None:
    """A clawed foot centred on ``(ox, oy)`` = (foot x, ground)."""
    _ellipse(draw, (ox - 12, oy - 11, ox + 12, oy + 1), FUR, OUTLINE, 1.5)
    for k in range(3):
        tx = ox + side * (7 + k * 2)
        _poly(draw, [(tx, oy - 4 - k * .6), (tx + side * 6, oy - 1), (tx, oy + 1)], CHALK, OUTLINE, 1)


def _paint_hand(draw: ImageDraw.ImageDraw, side: int, ox: float, oy: float) -> None:
    """A clawed paw centred on the wrist ``(ox, oy)``."""
    _ellipse(draw, (ox - 8, oy - 7, ox + 8, oy + 7), FUR_LIGHT, OUTLINE, 1.5)
    for k in (-1, 0, 1):
        _poly(draw, [(ox + side * 5, oy + k * 3), (ox + side * 12, oy + k * 3 - 1), (ox + side * 6, oy + k * 3 + 2)], CHALK, OUTLINE, 1)


def _paint_cloak(draw: ImageDraw.ImageDraw, ox: float, oy: float, squat: float) -> None:
    """The cloak behind the body, anchored at ``(cx, pose.y)``."""
    body_top = 50 + oy + squat * .25
    body_bottom = 101 + oy - squat * .15
    _poly(draw, [(ox - 31, body_top + 14), (ox - 24, body_bottom), (ox + 27, body_bottom), (ox + 32, body_top + 13), (ox + 20, 47 + oy), (ox - 18, 47 + oy)], VELVET_DARK, OUTLINE, 2)


def _paint_body(draw: ImageDraw.ImageDraw, ox: float, oy: float) -> None:
    """Fur, robe, brass sash and sigma medallion, anchored at ``(cx, pose.y)``."""
    _ellipse(draw, (ox - 31, 45 + oy, ox + 31, 96 + oy), FUR_DARK, OUTLINE, 2)
    _poly(draw, [(ox - 27, 55 + oy), (ox - 24, 96 + oy), (ox + 24, 96 + oy), (ox + 27, 55 + oy), (ox + 14, 48 + oy), (ox - 14, 48 + oy)], VELVET, OUTLINE, 2)
    _line(draw, [(ox - 22, 62 + oy), (ox + 20, 91 + oy)], BRASS, 5)
    for i in range(6):
        x = ox - 18 + i * 7
        y = 64 + oy + i * 4.8
        _line(draw, [(x, y - 2), (x, y + 3)], BRASS_LIGHT, 1)
    _ellipse(draw, (ox - 7, 73 + oy, ox + 7, 87 + oy), BRASS, OUTLINE, 1.5)
    _arc(draw, (ox - 4, 75 + oy, ox + 4, 84 + oy), 70, 290, VELVET_DARK, 2)


def _paint_head(draw: ImageDraw.ImageDraw, hx: float, hy: float, brow: int) -> None:
    """Head, integral horns, ears, eyes and brow, centred on ``(hx, hy)``."""
    _ellipse(draw, (hx - 27, hy - 23, hx + 27, hy + 24), FUR, OUTLINE, 2)
    _ellipse(draw, (hx - 23, hy - 20, hx + 22, hy + 17), FUR_LIGHT, None)
    # horns as integral curls
    _line(draw, [(hx - 17, hy - 18), (hx - 26, hy - 29), (hx - 20, hy - 35), (hx - 11, hy - 31)], OUTLINE, 7)
    _line(draw, [(hx - 17, hy - 18), (hx - 26, hy - 29), (hx - 20, hy - 35), (hx - 11, hy - 31)], CHALK, 4.5)
    _line(draw, [(hx + 17, hy - 18), (hx + 28, hy - 28), (hx + 23, hy - 35), (hx + 13, hy - 31)], OUTLINE, 7)
    _line(draw, [(hx + 17, hy - 18), (hx + 28, hy - 28), (hx + 23, hy - 35), (hx + 13, hy - 31)], CHALK, 4.5)
    # ears
    _poly(draw, [(hx - 23, hy - 9), (hx - 35, hy - 15), (hx - 29, hy + 1)], FUR_DARK, OUTLINE, 1.5)
    _poly(draw, [(hx + 23, hy - 9), (hx + 35, hy - 15), (hx + 29, hy + 1)], FUR_DARK, OUTLINE, 1.5)
    # eyes and brow
    _line(draw, [(hx - 16, hy - 6 - brow), (hx - 5, hy - 8 + brow)], OUTLINE, 2.5)
    _line(draw, [(hx + 5, hy - 8 + brow), (hx + 16, hy - 6 - brow)], OUTLINE, 2.5)
    _ellipse(draw, (hx - 14, hy - 5, hx - 7, hy + 3), EYE, OUTLINE, 1)
    _ellipse(draw, (hx + 7, hy - 5, hx + 14, hy + 3), EYE, OUTLINE, 1)
    _ellipse(draw, (hx - 11, hy - 2, hx - 9, hy + 2), OUTLINE)
    _ellipse(draw, (hx + 9, hy - 2, hx + 11, hy + 2), OUTLINE)


def _paint_mouth(draw: ImageDraw.ImageDraw, hx: float, hy: float, mouth: float) -> None:
    """Muzzle, the expanding grid maw and the nose, on the head centre."""
    mw = 12 + 16 * mouth
    mh = 5 + 18 * mouth
    _ellipse(draw, (hx - mw, hy + 4, hx + mw, hy + 4 + mh), MAW, OUTLINE, 1.5)
    if mouth > .25:
        clip_top = hy + 7
        for k in range(-2, 3):
            x = hx + k * mw / 3
            _line(draw, [(x, clip_top), (x, hy + 2 + mh)], _fade(GRID, .75), .8)
        for k in range(1, 4):
            y = clip_top + k * (mh - 4) / 4
            _line(draw, [(hx - mw + 2, y), (hx + mw - 2, y)], _fade(GRID, .6), .8)
        _ellipse(draw, (hx - 8, hy + 5 + mh * .62, hx + 8, hy + 5 + mh), TONGUE)
    else:
        _line(draw, [(hx - 9, hy + 10), (hx + 9, hy + 10)], OUTLINE, 1.5)
    _ellipse(draw, (hx - 6, hy + 1, hx + 6, hy + 8), OUTLINE)


def _draw_character(img: Image.Image, pose: Pose) -> None:
    """Le Beast as a rig: each rigid piece painted once and placed (feet,
    cloak, body, paws, head, maw), limbs as fixed-length bones."""
    cx = 63 + pose.x
    base = 112 + pose.y
    if pose.anim == "roll":
        cx += math.sin(pose.phase*math.tau)*5
    # legs and broad clawed feet
    leg_y = base - 25 + pose.squat*.25
    for side, dx, step in [(-1,-18,pose.foot_l),(1,18,pose.foot_r)]:
        tag = "l" if side < 0 else "r"
        hip=(cx+dx*.65, leg_y-8)
        ankle=(cx+dx+step*.25, base-9+abs(step)*.05)
        _bone(img, ankle, hip, LEG_LENGTH, 7.5, FUR_DARK, f"leg_{tag}")
        footx=ankle[0]+side*5
        foot = _rig_piece(("foot", side), (40, 24), (20, 14), lambda d, side=side: _paint_foot(d, side, 20, 14))
        _put(img, foot, (footx, base), f"foot_{tag}")
    # cloak/body
    squat = round(pose.squat)
    cloak = _rig_piece(("cloak", squat), (72, 72), (36, -40), lambda d: _paint_cloak(d, 36, -40, squat))
    _put(img, cloak, (cx, pose.y), "cloak")
    body = _rig_piece(("body",), (72, 60), (36, -40), lambda d: _paint_body(d, 36, -40))
    _put(img, body, (cx, pose.y), "body")
    # arms
    shoulder_y=59+pose.y
    for side, ang in [(-1,pose.arm_l),(1,pose.arm_r)]:
        tag = "l" if side < 0 else "r"
        shoulder=(cx+side*24,shoulder_y)
        rad=math.radians(90+side*15+ang)
        elbow=(shoulder[0]+math.cos(rad)*21,shoulder[1]+math.sin(rad)*21)
        wrist=(elbow[0]+math.cos(rad+side*.15)*17,elbow[1]+math.sin(rad+side*.15)*17)
        _bone(img, shoulder, elbow, 21.0, 8, FUR_DARK, f"upper_arm_{tag}")
        _bone(img, elbow, wrist, 17.0, 7, FUR, f"forearm_{tag}")
        paw = _rig_piece(("paw", side), (32, 20), (16, 10), lambda d, side=side: _paint_hand(d, side, 16, 10))
        _put(img, paw, wrist, f"paw_{tag}")
    # head
    hx=cx+2+pose.lean*.14
    hy=37+pose.y+pose.squat*.14
    brow = 2 if pose.expression in (1,5) else 0
    head = _rig_piece(("head", brow), (76, 70), (38, 42), lambda d: _paint_head(d, 38, 42, brow))
    _put(img, head, (hx, hy), "head")
    # muzzle and expanding grid maw, its opening quantized to twentieths
    mouth = round(pose.mouth * 20) / 20
    maw = _rig_piece(("maw", mouth), (64, 40), (32, 4), lambda d: _paint_mouth(d, 32, 4, mouth))
    _put(img, maw, (hx, hy), "maw")
    # dissolve overlay removes coherent body by drawing holes as translucent points
    if pose.dissolve>0:
        def dots(draw: ImageDraw.ImageDraw) -> None:
            for i in range(34):
                a=i*2.27+pose.phase*5
                r=(i%9)*3.4
                x=hx+math.cos(a)*r
                y=hy+23+math.sin(a)*r*.9
                _ellipse(draw,(x-2,y-2,x+2,y+2),_fade(CYAN,.3+.5*pose.dissolve))
        _frame_layer(img, dots, "dissolve")


def _draw_effects_front(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    if pose.anim == "measurable_maw":
        x=100-24*pose.power
        _draw_region(draw,x,52,14,11,CYAN,pose.phase)
        for i in range(5):
            px=105+i*4
            _ellipse(draw,(px-1,34+i*3,px+1,36+i*3),_fade(CHALK,1-pose.power*.7))
    elif pose.anim == "sigma_swallow":
        # sigma-like three-stroke seal, deliberately drawn rather than font-dependent
        _line(draw,[(48,20),(80,20),(55,39),(80,58),(48,58)],BRASS_LIGHT,4)
    elif pose.anim == "rearrangement":
        _line(draw,[(30,89),(98,89)],_fade(CHALK,.7),1)
        for x in (42,64,86):
            _line(draw,[(x,84),(x,94)],_fade(CHALK,.7),1)
    elif pose.anim == "taunt":
        _draw_region(draw,100,35,8+4*pose.power,5+3*pose.power,_fade(CHALK,.8),pose.phase)
        _line(draw,[(94,28),(106,42)],MAGENTA,2)
        _line(draw,[(106,28),(94,42)],MAGENTA,2)
    if pose.anim == "land_hard":
        for side in (-1,1):
            _line(draw,[(64+side*10,108),(64+side*(30+15*pose.power),116)],_fade(CHALK,.7*pose.power),2)


def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose=_pose(anim,frame_idx,nframes)
    image=Image.new("RGBA",(FRAME_W*SUPER,FRAME_H*SUPER),(0,0,0,0))
    # The effects change every frame: each layer is one draw.
    _frame_layer(image, lambda d: _draw_effects_behind(d, pose), "effects_behind")
    _draw_character(image,pose)
    _frame_layer(image, lambda d: _draw_effects_front(d, pose), "effects_front")
    return rigdoc.downsampled_canvas(image,(FRAME_W,FRAME_H),Image.Resampling.LANCZOS)


def _render_native_portrait(expression: str="default", phase: float=0.0) -> Image.Image:
    anim={"default":"idle","talk":"talk","maw":"measurable_maw","null":"null_set","smug":"taunt"}.get(expression,"idle")
    frame=render_frame(anim,int(phase*7)%8,10 if anim in {"measurable_maw","null_set"} else 8)
    crop=frame.crop((28,2,103,78)).resize(PORTRAIT_SIZE,Image.Resampling.LANCZOS)
    return crop


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    del opts
    clips={
        "default": PortraitClip.still(_render_native_portrait("default")),
        "talk": PortraitClip(tuple(_render_native_portrait("talk",i/8) for i in range(8)),duration_ms=104,looping=True),
        "maw": PortraitClip(tuple(_render_native_portrait("maw",i/8) for i in range(8)),duration_ms=82,looping=True),
        "null": PortraitClip.still(_render_native_portrait("null",.5)),
        "smug": PortraitClip.still(_render_native_portrait("smug",.25)),
    }
    return write_portrait_sheet(TARGET_NAME,clips,Path(out_dir))


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {"x": int(fw*.20), "y": int(fh*.05), "w": int(fw*.63), "h": int(fh*.88)},
        "feet_pixel": {"x": fw*.5, "y": fh*.91},
        "feet_anchor_norm": {"x": 0.0, "y": round(.5-.91,6)},
    }


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    frame_transform:dict={}
    outputs=build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME, rows=ROWS, render_fn=render_frame, out_dir=Path(out_dir),
        frame_size=(FRAME_W,FRAME_H), label_width=112, auto_crop=False,
        body_metrics_fn=_body_metrics_override, actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale":1.12,"frame_sample_inset":1},
        animation_key_map={name:name for name,_frames,_duration in ROWS},
        attack_hitboxes={
            "measurable_maw":{"bbox":{"x":58,"y":22,"w":70,"h":65}},
            "sigma_swallow":{"bbox":{"x":20,"y":12,"w":108,"h":87}},
            "rearrangement":{"bbox":{"x":18,"y":18,"w":110,"h":83}},
            "dominated_convergence":{"bbox":{"x":24,"y":15,"w":80,"h":65}},
        },
    )
    keys=("spritesheet","yaml","ron","actor","canonical","canonical_transparent","preview")
    parts=publish_rig_flipbook(TARGET_NAME,ROWS,render_frame,outputs,frame_transform,Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)]+list(parts.values())


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME,ROWS,render_frame,Path(out_dir),frame_size=(FRAME_W,FRAME_H))


__all__=["ACTOR_METADATA","AUTHORING_DESCRIPTION","TARGET_NAME","render","render_canonical","render_frame","render_portraits"]

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir",nargs="?",type=Path,default=Path("generated")/TARGET_NAME)
    args=parser.parse_args()
    for path in render(args.out_dir): print(path)
    for path in render_portraits(args.out_dir): print(path)
