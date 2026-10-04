"""Canonical SVG-rigged full-action generator for Carl Stargan.

The manually traced ``assets/carl-stargan.svg`` is the visual authority. Python
owns the rig clips, cosmic effects, portraits, and sheet publication—not the
character's anatomy or clothing geometry.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageFont

import json

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring import shape_rig, strike_axis, swing_effects
from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.canonical_scientist_rig import ensure_scientist_rig
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from ._svg_fighter_effects import (
    FxCanvas,
    bone_origin,
    clamp01,
    compose_rig_frame,
    fade,
    orbit_point,
    pulse,
    smooth,
)
from .carl_stargan_motion import CARL_ROWS, EFFECT_ALIASES

TARGET_NAME = "carl_stargan"

#: Room around the rig's own canvas, in RIG units.
#:
#: ⭐⭐ THE SHARED SCIENTIST ROLL TUCKS BELOW THE GROUND LINE. `_common_clips`
#: authors ONE `roll` for all three canonical scientist rigs, and it puts the
#: body 38-42px below each rig's `ground_y` at the tuck — the pelvis sweeps a
#: full turn while the root drops, which is what a forward roll IS. Carl's rig
#: frame leaves 24px below the ground line, so on HIS sheet alone the tuck was
#: drawn off the canvas and lost: eight frames across `roll`, `roll_back`,
#: `tumble`, `spot_dodge` and the four clips that clone the roll.
#:
#: ⛔ HIS TWO RIG-SIBLINGS ALREADY HAD THIS and he never adopted it —
#: `patent_clerk.RIG_RENDER_PADDING` is 24 and `noether_gameplay.PADDING` is its
#: own; both derive their published frame from the rig canvas PLUS the padding
#: rather than restating the rig canvas as the frame. This is that pattern, not
#: a new one.
RIG_RENDER_PADDING = 24
ROWS = list(CARL_ROWS)


def frame_size() -> tuple[int, int]:
    """The published frame: the RIG's own canvas plus this target's padding.

    ⛔ **not a restated constant.** This was the rig canvas, copied, until
    2026-08-31 — the shape `noether.frame_size` warns about: when the rig is
    rebuilt only one of the two copies moves. Read at call time, so the rig
    document is the single authority.
    """
    frame = _doc().frame
    # `render_scale` is the third term: the composer pads in RIG units and scales
    # the padded canvas, so a rig published at 2x emits a frame twice this wide.
    scale = max(1, int(frame.get("render_scale", 1)))
    return (
        (int(frame["width"]) + RIG_RENDER_PADDING * 2) * scale,
        (int(frame["height"]) + RIG_RENDER_PADDING * 2) * scale,
    )

ACTOR_METADATA = {'actor': {'character_id': 'npc_carl_stargan', 'display_name': 'Carl Stargan'},
 'body': {'body_plan': 'HumanoidBiped',
          'body_kind': 'Standard',
          'mass_class': 'Medium',
          'traits': ['story',
                     'humanoid',
                     'science_communicator',
                     'cosmic_storyteller',
                     'skeptic',
                     'playable_candidate'],
          'locomotion_hint': 'Walk'},
 'capabilities': {'traversal': {'walk': True,
                                'jump': True,
                                'climb': True,
                                'fly': None,
                                'swim': True,
                                'crawl': True,
                                'use_lifts': True,
                                'door_access': ['public']},
                  'interactions': {'talk': True, 'trade': None, 'carry': None, 'open_doors': ['public']}},
 'brain': {'default_preset': 'patrol_peaceful'},
 'actions': {'default_preset': 'peaceful'},
 'visual': {'default_pose': 'idle',
            'face_guide': {'center': {'x': 64.0, 'y': 29.0},
                           'size': {'w': 31.0, 'h': 36.0},
                           'source_size': {'w': 128.0, 'h': 128.0}}},
 'tags': ['story', 'humanoid', 'science_communicator', 'cosmic_storyteller', 'skeptic', 'playable_candidate'],
 'sockets': {'head': {'source': 'explicit.profile.humanoid', 'point': {'x': 64.0, 'y': 29.0}},
             'chest': {'source': 'explicit.profile.humanoid', 'point': {'x': 64.0, 'y': 64.0}},
             'hand_l': {'source': 'explicit.profile.humanoid', 'point': {'x': 44.0, 'y': 79.0}},
             'hand_r': {'source': 'explicit.profile.humanoid', 'point': {'x': 86.0, 'y': 79.0}},
             'speech_bubble': {'source': 'explicit.profile.humanoid', 'point': {'x': 64.0, 'y': 3.0}}},
 'animation_bindings': {'default': {'animation': 'idle', 'events': []},
                        'locomotion.walk': {'animation': 'walk', 'events': []},
                        'locomotion.run': {'animation': 'run', 'events': []},
                        'traversal.jump': {'animation': 'jump', 'events': []},
                        'traversal.fall': {'animation': 'fall', 'events': []},
                        'action.melee.primary': {'animation': 'planetary_orbit', 'events': []},
                        'action.ranged.primary': {'animation': 'pale_blue_dot', 'events': []},
                        'action.special.primary': {'animation': 'cosmic_calendar', 'events': []},
                        'action.special.secondary': {'animation': 'billions_and_billions', 'events': []},
                        'action.special.up': {'animation': 'cosmic_drift', 'events': []},
                        'action.special.down': {'animation': 'billions_and_billions', 'events': []},
                        'action.super': {'animation': 'starstuff', 'events': []},
                        'action.defense.block': {'animation': 'block', 'events': []},
                        'action.defense.roll': {'animation': 'roll', 'events': []},
                        'interaction.talk': {'animation': 'talk', 'events': []},
                        'interaction.use': {'animation': 'use_telescope', 'events': []},
                        'emote.think': {'animation': 'think', 'events': []},
                        'emote.inspire': {'animation': 'stargaze', 'events': []},
                        'emote.taunt': {'animation': 'taunt', 'events': []}},
 'authoring_description': 'Carl Stargan is a warm, theatrically cosmic parody of science communicator Carl '
                          'Sagan. The name bends Sagan toward stars while the character pairs wonder, scale, '
                          'skepticism, and an inability to discuss a room without locating it in the '
                          'universe. The visual target is a warmly caricatured 1970s science presenter: soft '
                          'brown jacket, black turtleneck, dark trousers, expressive hands, swept wavy hair, '
                          'and a pocket telescope used as a recurring prop. Cosmic effects are gameplay '
                          "inventions inspired by Sagan's public language about starstuff, the pale blue "
                          'dot, planetary scale, and evidence-led wonder.',
 'gameplay_description': 'Use as a science guide, narrator, lecturer, or playable explorer whose hints '
                         'reframe local obstacles at cosmic scale. He should inspire curiosity but '
                         'ultimately defer to evidence rather than vibes.',
 'dialogue_hints': {'barks': ['Billions and billions of pedestals in this hall...',
                              'Scale is not decoration, it is the point.',
                              'Wonder gets me to the question. Evidence decides who leaves with it.']}}

ACTOR_METADATA.setdefault("tags", []).append("svg_rigged")
ACTOR_METADATA.setdefault("body", {}).setdefault("traits", []).append("svg_rigged")
ACTOR_METADATA.setdefault("visual", {})["canonical_source"] = "assets/carl-stargan.svg"
ACTOR_METADATA["actions"] = {"default_preset": "carl_stargan"}
ACTOR_METADATA["provenance"] = {
    "variant_family": TARGET_NAME,
    "variant_id": "manual_svg_rig_canonical_2026_08_06",
    "lineage": [
        {
            "revision_id": "carl_stargan_character_direction",
            "creator_kind": "human",
            "creator": "Jon Crall",
            "contribution": "cosmic_storyteller_smash_fighter_direction",
        },
        {
            "revision_id": "carl_stargan_manual_svg_paperdoll",
            "creator_kind": "human",
            "creator": "Jon Crall",
            "parent_revision_id": "carl_stargan_character_direction",
            "contribution": "canonical_manually_traced_svg_parts_and_joint_layout",
        },
        {
            "revision_id": "carl_stargan_svg_rig_generator",
            "creator_kind": "model",
            "creator": "GPT-5.6 Thinking",
            "parent_revision_id": "carl_stargan_manual_svg_paperdoll",
            "contribution": "rig_clip_cosmic_effect_and_sheet_generator_authoring",
        },
    ],
}

OUTLINE = (27, 22, 26, 255)
STAR_GOLD = (248, 203, 112, 255)
STAR_WHITE = (251, 244, 214, 255)
NEBULA_BLUE = (91, 164, 220, 255)
NEBULA_VIOLET = (148, 101, 186, 255)
PALE_BLUE = (104, 190, 225, 255)
PLANET_OCHRE = (208, 139, 66, 255)
PLANET_RUST = (150, 71, 50, 255)
COSMIC_DARK = (22, 30, 50, 255)
TELESCOPE = (72, 72, 82, 255)
TELESCOPE_LIGHT = (151, 151, 162, 255)


@lru_cache(maxsize=4)
def _load_doc_cached(path_text: str, mtime_ns: int, size: int) -> RigDocument:
    del mtime_ns, size
    return RigDocument.load(path_text)


def _doc() -> RigDocument:
    path = ensure_scientist_rig("carl_stargan")
    stat = path.stat()
    return _load_doc_cached(str(path), stat.st_mtime_ns, stat.st_size)


# --- Cosmic effects as GLYPHS -------------------------------------------------
#
# ⭐ EACH EFFECT IS A GLYPH PAINTED ONCE AND PLACED (2026-10-04). A ring is a
# raster of one fixed size, a planet moves along its orbit, a swirl turns (a
# turn is a draw transform), the calendar is one arc dash turned along a
# spiral, and a star field is a few star CLUSTERS placed. Growth is a few fixed
# sizes or a fade (the glyph's opacity). These effects drew a radius and a
# point that changed every frame, so a part flipbook stored a new raster each
# frame: 0.74 MTexel of parts, almost all effects
# (`scripts/measure_part_waste.py --tracks`).
#
# A shape that a half turn maps onto itself (an ellipse, a ring) is painted as
# its TOP HALF and placed twice, turned 0 and 180 degrees: a half turn costs
# nothing on a part page (`docs/planning/engine/mary-o-part-realization.md`).

#: Transparent canvas pixels round a glyph's drawn extent.
GLYPH_PAD = 4


def _glyph(canvas: FxCanvas, key, half: tuple[float, float], paint, *, top_half: bool = False):
    """A glyph painted once at the canvas's pixels, its pivot at its centre.

    ``half`` is the drawn extent from the pivot, in logical units.
    ``paint(draw, s, cx, cy)`` paints it about the pixel CORNER ``(cx, cy)``,
    with ``s`` canvas pixels a logical unit. With ``top_half`` the raster ends
    at the pivot row: placed again turned 180 degrees about the same corner, a
    shape symmetric about its centre tiles back exactly.
    """
    s = canvas.draw_scale
    cx = int(math.ceil(half[0] * s)) + GLYPH_PAD
    cy = int(math.ceil(half[1] * s)) + GLYPH_PAD
    size = (2 * cx, cy if top_half else 2 * cy)
    return shape_rig.piece(
        (TARGET_NAME, key, s, top_half),
        size,
        (float(cx), float(cy)),
        lambda draw: paint(draw, s, cx, cy),
    )


def _box(s: float, cx: int, cy: int, rx: float, ry: float, dx: float = 0.0, dy: float = 0.0):
    """The ellipse box centred on the pixel corner ``(cx, cy)`` (+ an offset)."""
    x, y = cx + dx * s, cy + dy * s
    return (x - rx * s, y - ry * s, x + rx * s - 1, y + ry * s - 1)


def _width(s: float, width: float) -> int:
    return max(1, int(round(width * s)))


def _place_halves(canvas: FxCanvas, part, at: tuple[float, float], opacity: float, name: str) -> None:
    """A ``top_half`` glyph placed whole: as painted, and turned a half turn."""
    canvas.place(part, at, 0.0, opacity, f"{name}_top")
    canvas.place(part, at, 180.0, opacity, f"{name}_bottom")


def _ring(canvas: FxCanvas, rx: float, ry: float, color, width: float):
    """The top half of an elliptical ring (see ``_place_halves``)."""
    def paint(draw, s, cx, cy):
        draw.ellipse(_box(s, cx, cy, rx, ry), outline=color, width=_width(s, width))

    return _glyph(canvas, ("ring", rx, ry, color, width), (rx + width, ry + width), paint, top_half=True)


def _disc(canvas: FxCanvas, rx: float, ry: float, color):
    """The top half of a filled ellipse (see ``_place_halves``)."""
    def paint(draw, s, cx, cy):
        draw.ellipse(_box(s, cx, cy, rx, ry), fill=color)

    return _glyph(canvas, ("disc", rx, ry, color), (rx, ry), paint, top_half=True)


def _star_points(s: float, cx: float, cy: float, radius: float, points: int, inner: float = 0.43,
                 rotation: float = -90.0) -> list[tuple[float, float]]:
    vertices = []
    for index in range(points * 2):
        angle = math.radians(rotation + index * 180.0 / points)
        r = (radius if index % 2 == 0 else radius * inner) * s
        vertices.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    return vertices


def _star(canvas: FxCanvas, radius: float, color, points: int = 4, outline=None):
    """One star, ``FxCanvas.star``'s shape, about its centre."""
    def paint(draw, s, cx, cy):
        vertices = _star_points(s, cx, cy, radius, points)
        draw.polygon(vertices, fill=color)
        if outline is not None:
            draw.line([*vertices, vertices[0]], fill=outline, width=_width(s, 0.7), joint="curve")

    return _glyph(canvas, ("star", radius, color, points, outline), (radius + 1, radius + 1), paint)


#: Star clusters: (dx, dy, radius, gold) per star. A star field is a few of
#: these placed (and quarter-turned): a star a draw would spend the frame's
#: draw budget on one field.
_CLUSTERS = (
    ((-6.0, -2.5, 1.9, False), (-1.0, 3.5, 1.3, True), (3.5, -4.0, 1.6, True), (7.0, 2.0, 1.2, False),
     (1.5, 0.0, 0.9, True)),
    ((-7.0, 3.0, 1.4, True), (-3.0, -3.5, 1.2, False), (2.0, 1.5, 2.1, True), (6.5, -2.5, 1.2, True),
     (-1.0, 5.5, 0.9, False)),
    ((-5.0, 0.5, 1.2, True), (-0.5, -4.5, 1.7, False), (4.0, 4.0, 1.3, True), (6.0, -1.5, 0.9, False),
     (-6.5, -5.0, 0.9, True)),
)


def _cluster(canvas: FxCanvas, variant: int):
    stars = _CLUSTERS[variant % len(_CLUSTERS)]

    def paint(draw, s, cx, cy):
        for dx, dy, radius, gold in stars:
            draw.polygon(_star_points(s, cx + dx * s, cy + dy * s, radius, 4), fill=STAR_GOLD if gold else STAR_WHITE)

    return _glyph(canvas, ("cluster", variant % len(_CLUSTERS)), (9.5, 8.0), paint)


def _field(canvas: FxCanvas, center: tuple[float, float], radius: float, clusters: int, phase: float,
           alpha: float, name: str = "stars") -> None:
    """A turning star field: ``clusters`` star clusters on a golden-angle
    spiral of ``radius``, each twinkling by its opacity."""
    for index in range(clusters):
        angle = phase * math.tau + index * 2.399963
        r = radius * (0.25 + 0.75 * ((index * 0.6180339887) % 1.0))
        at = (center[0] + math.cos(angle) * r, center[1] + math.sin(angle) * r * 0.68)
        opacity = alpha * (0.45 + 0.45 * pulse(phase + index / max(1, clusters)))
        canvas.place(_cluster(canvas, index), at, 90.0 * ((index // len(_CLUSTERS)) % 4), opacity, name)


def _arcs(canvas: FxCanvas, key, center_offset, arcs, half):
    """Arcs of ellipses about the glyph's pivot: (rx, ry, start, end, color, width) each."""
    def paint(draw, s, cx, cy):
        for rx, ry, start, end, color, width in arcs:
            draw.arc(_box(s, cx, cy, rx, ry, *center_offset), start=start, end=end, fill=color, width=_width(s, width))

    return _glyph(canvas, ("arcs", key), half, paint)


def _shield(canvas: FxCanvas):
    """The block shield's three rings, top half."""
    def paint(draw, s, cx, cy):
        for radius in (18, 25, 32):
            draw.ellipse(_box(s, cx, cy, radius, radius * 0.78), fill=fade(COSMIC_DARK, 0.09),
                         outline=fade(PALE_BLUE, 0.46), width=_width(s, 0.9))

    return _glyph(canvas, ("shield",), (33.0, 26.0), paint, top_half=True)


def _halo(canvas: FxCanvas, radius: int):
    """The orbiting planet's glow and ring, behind the body."""
    def paint(draw, s, cx, cy):
        draw.ellipse(_box(s, cx, cy, radius, radius), fill=fade(PLANET_OCHRE, 0.48), outline=fade(PLANET_RUST, 0.9),
                     width=_width(s, 1.0))
        draw.arc(_box(s, cx, cy, 10, 3.5), start=180, end=360, fill=fade(STAR_GOLD, 0.65), width=_width(s, 0.8))

    return _glyph(canvas, ("halo", radius), (radius + 1.0, radius + 1.0), paint)


def _planet(canvas: FxCanvas):
    def paint(draw, s, cx, cy):
        draw.ellipse(_box(s, cx, cy, 5.5, 5.5), fill=PLANET_OCHRE, outline=PLANET_RUST, width=_width(s, 1.0))
        draw.ellipse(_box(s, cx, cy, 1.5, 1.5, -2.0, -2.0), fill=fade(STAR_WHITE, 0.65))

    return _glyph(canvas, ("planet",), (6.5, 6.5), paint)


def _dot(canvas: FxCanvas, radius: float):
    def paint(draw, s, cx, cy):
        draw.ellipse(_box(s, cx, cy, radius, radius), fill=PALE_BLUE, outline=STAR_WHITE, width=_width(s, 0.8))

    return _glyph(canvas, ("dot", radius), (radius + 1.0, radius + 1.0), paint)


#: The cosmic calendar's dash radius per colour band (inner, middle, outer).
CALENDAR_BANDS = ((NEBULA_VIOLET, 35.0), (NEBULA_BLUE, 46.0), (STAR_GOLD, 55.0))


def _dash(canvas: FxCanvas, band: int):
    """One calendar dash: 14 degrees of a circle, running along +x about its
    middle, curving toward +y (the calendar's centre once turned)."""
    color, radius = CALENDAR_BANDS[band]
    half_chord = radius * math.sin(math.radians(7.0))

    def paint(draw, s, cx, cy):
        draw.arc(_box(s, cx, cy, radius, radius, 0.0, radius), start=263, end=277, fill=color, width=_width(s, 2.2))

    return _glyph(canvas, ("dash", band), (half_chord + 1.5, 2.5), paint)


#: The collapsible telescope's lengths, from the far hand to the lens.
TELESCOPE_LENGTHS = (6.0, 14.0, 25.0, 36.0)


def _telescope(canvas: FxCanvas, length: float):
    """The telescope along +x: eyepiece at the pivot, lens ``length`` away."""
    def paint(draw, s, cx, cy):
        a, b = (cx, cy), (cx + length * s, cy)
        polygon = [(a[0], a[1] - 3 * s), (b[0], b[1] - 5 * s), (b[0], b[1] + 5 * s), (a[0], a[1] + 3 * s)]
        draw.polygon(polygon, fill=TELESCOPE)
        draw.line([*polygon, polygon[0]], fill=OUTLINE, width=_width(s, 1.0), joint="curve")
        draw.line([a, b], fill=TELESCOPE_LIGHT, width=_width(s, 1.1))
        draw.ellipse(_box(s, cx, cy, 5.5, 5.5, length, 0.0), fill=TELESCOPE_LIGHT, outline=OUTLINE, width=_width(s, 0.9))

    # Centred on the eyepiece, so the half-extent reaches the lens both ways.
    return _glyph(canvas, ("telescope", length), (length + 7.0, 7.0), paint)


def _swirl(canvas: FxCanvas, scale: float):
    """Four spiral arms at ``scale`` of full size, at no turn."""
    def paint(draw, s, cx, cy):
        for arm in range(4):
            points = []
            for index in range(22):
                a = arm * math.pi / 2 + index * 0.27
                r = 2.2 * index * scale * s
                points.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
            draw.line(points, fill=NEBULA_VIOLET if arm % 2 else NEBULA_BLUE, width=_width(s, 1.0), joint="curve")

    reach = 2.2 * 21 * scale + 1.0
    return _glyph(canvas, ("swirl", scale), (reach, reach), paint)


def _thought(canvas: FxCanvas):
    """The three thought bubbles, about the first."""
    def paint(draw, s, cx, cy):
        for index, radius in enumerate((2.0, 3.0, 4.0)):
            draw.ellipse(_box(s, cx, cy, radius, radius, 8.0 * index, -7.0 * index), fill=fade(PALE_BLUE, 0.35 + 0.12 * index),
                         outline=fade(OUTLINE, 0.35), width=_width(s, 0.5))

    return _glyph(canvas, ("thought",), (21.0, 19.0), paint)


def _label(canvas: FxCanvas, text: str, size: float):
    font_size = max(5, int(round(size * canvas.draw_scale)))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    stroke = max(1, canvas.scale // 2)
    left, top, right, bottom = font.getbbox(text, stroke_width=stroke, anchor="mm")
    half = (max(-left, right) / canvas.draw_scale, max(-top, bottom) / canvas.draw_scale)

    def paint(draw, s, cx, cy):
        draw.text((cx, cy), text, font=font, fill=STAR_GOLD, anchor="mm", stroke_width=stroke,
                  stroke_fill=fade(OUTLINE, 0.6))

    return _glyph(canvas, ("label", text, font_size), half, paint)


def _quantized(value: float, low: float, high: float, steps: int = 2) -> float:
    """``low + (high - low) * value`` on ``steps + 1`` fixed sizes."""
    return low + (high - low) * round(clamp01(value) * steps) / steps


def _behind(animation: str, canvas: FxCanvas, t: float, world, params) -> None:
    del params
    center = (80.0, 82.0)
    if animation in {"cosmic_drift", "float_glide"}:
        for index in range(9):
            x = 150 - ((t * 70 + index * 17) % 72)
            y = 43 + (index * 13) % 78
            star = _star(canvas, 1.4 + index % 3, STAR_GOLD if index % 2 else PALE_BLUE)
            canvas.place(star, (x, y), 0.0, 0.32 + 0.25 * pulse(t + index / 9), "drift")
        canvas.line([(150, 85), (118, 85), (98, 89)], fade(NEBULA_BLUE, 0.22), 4.0)
    elif animation == "block":
        hand = bone_origin(world, "near_arm_hand", (55, 90))
        shield = (hand[0] - 8, hand[1] - 1)
        _place_halves(canvas, _shield(canvas), shield, (0.28 + 0.18 * pulse(t + 0.5)) / 0.46, "shield")
        _field(canvas, shield, 27, 2, t, 0.45)
    elif animation == "stargaze":
        q = smooth(t)
        arcs = _arcs(canvas, "stargaze", (0.0, 0.0), (
            (67, 51, 205, 340, fade(NEBULA_BLUE, 0.70), 1.4),
            (72, 57, 205, 340, fade(NEBULA_VIOLET, 0.53), 2.5),
        ), (74.0, 59.0))
        canvas.place(arcs, center, 0.0, (0.25 + 0.45 * q) / 0.70, "sky")
        _field(canvas, (80, 70), 68, 5, t * 0.18, 0.4 + 0.4 * q)
    elif animation == "planetary_orbit":
        q = smooth(t)
        _place_halves(canvas, _ring(canvas, 61, 31, NEBULA_BLUE, 1.1), center, 0.3 + 0.4 * pulse(t), "orbit")
        planet = orbit_point(center, 61, 31, t + 0.15)
        canvas.place(_halo(canvas, 8 + int(round(2 * q))), planet, 0.0, 1.0, "halo")
    elif animation == "pale_blue_dot":
        q = smooth(t)
        hand = bone_origin(world, "near_arm_hand", (43, 80))
        dot = (max(34.0, hand[0] - 12), hand[1] - 2)
        # The zoom out: each ring appears as the view widens past it.
        alpha = (1 - q) * 0.42 + 0.08
        for radius in (8, 16, 24, 31):
            reached = clamp01((q * 31 - radius) / 8 + 1)
            if reached > 0:
                _place_halves(canvas, _ring(canvas, radius, radius, PALE_BLUE, 0.8), dot, alpha * reached, "ripple")
        _field(canvas, dot, 29 * q, 3, t * 0.2, 0.22 + 0.3 * q)
    elif animation == "cosmic_calendar":
        q = smooth(t)
        for index in range(12):
            middle = math.radians(-165 + index * 20 + 7)
            rx, ry = 30 + index * 2.5 * q, 22 + index * 1.7 * q
            at = (center[0] + math.cos(middle) * rx, center[1] + math.sin(middle) * ry)
            heading = math.degrees(math.atan2(math.cos(middle) * ry, -math.sin(middle) * rx))
            band = 2 if index > 8 else 1 if index > 4 else 0
            canvas.place(_dash(canvas, band), at, heading, 0.25 + 0.45 * q, "month")
        _field(canvas, center, 45 * q, 3, -t * 0.16, 0.35)
    elif animation == "billions_and_billions":
        q = smooth(t)
        _field(canvas, center, 12 + 62 * q, 8, t * 0.25, 0.28 + 0.5 * q)
        grown = round(q * 2) / 2
        nebula = _disc(canvas, 20 + 34 * grown, 12 + 23 * grown, fade(NEBULA_VIOLET, 0.13))
        _place_halves(canvas, nebula, center, (0.05 + 0.08 * q) / 0.13, "nebula")
    elif animation == "starstuff":
        q = smooth(t)
        # Round, not squashed, so a turn is a draw transform: kept smaller than
        # the squashed spiral's width so it stays about his body.
        swirl = _swirl(canvas, 0.35 if q < 0.3 else 0.55 if q < 0.65 else 0.75)
        canvas.place(swirl, center, math.degrees(t * math.tau), (0.22 + 0.35 * q) * min(1.0, q / 0.2), "swirl")
        _field(canvas, center, 64 * q, 7, -t * 0.33, 0.35 + 0.35 * q)
    elif animation in {"attack_up", "attack_down", "air_neutral", "air_forward", "air_back", "air_down", "air_up", "jab", "punch"}:
        hand = bone_origin(world, "near_arm_hand", (48, 82))
        arcs = _arcs(canvas, "strike", (0.0, 0.0), tuple(
            (radius, radius * 0.72, 130, 310, fade(STAR_GOLD, 0.68 - radius / 70), 1.3) for radius in (12, 19, 27)
        ), (28.5, 21.0))
        canvas.place(arcs, hand, 0.0, pulse(t), "strike")


def _front(animation: str, canvas: FxCanvas, t: float, world, params) -> None:
    del params
    near = bone_origin(world, "near_arm_hand", (50, 90))
    far = bone_origin(world, "far_arm_hand", (78, 92))
    if animation == "use_telescope":
        q = smooth(min(1.0, t * 2.0)) * smooth(min(1.0, (1.0 - t) * 3.0))
        reach = math.dist(far, near)
        length = min(TELESCOPE_LENGTHS, key=lambda value: abs(value - reach))
        heading = math.degrees(math.atan2(near[1] - far[1], near[0] - far[0]))
        canvas.place(_telescope(canvas, length), far, heading, 0.45 + 0.55 * q, "telescope")
        glint = _star(canvas, _quantized(pulse(t), 2.8, 5.3), PALE_BLUE)
        canvas.place(glint, (near[0] - 10, near[1] - 4), 0.0, q, "glint")
    elif animation == "planetary_orbit":
        canvas.place(_planet(canvas), orbit_point((80, 82), 61, 31, t + 0.15), 0.0, 1.0, "planet")
    elif animation == "pale_blue_dot":
        canvas.place(_dot(canvas, _quantized(pulse(t), 2.2, 3.7)), (max(34.0, near[0] - 12), near[1] - 2), 0.0, 1.0, "dot")
    elif animation == "billions_and_billions":
        star = _star(canvas, _quantized(pulse(t), 3.0, 5.0), fade(STAR_GOLD, 0.75), 6, fade(OUTLINE, 0.55))
        for hand in (near, far):
            canvas.place(star, (hand[0], hand[1] - 2), 0.0, 1.0, "hand_star")
    elif animation == "starstuff":
        _field(canvas, (80, 82), 44 * smooth(t), 3, t * 0.6, 0.55, "front_stars")
    elif animation in {"stargaze", "celebrate"}:
        canvas.place(_star(canvas, _quantized(pulse(t), 3.2, 4.6), STAR_GOLD, 5), (near[0] - 5, near[1] - 7), 0.0, 0.75, "star")
        canvas.place(_star(canvas, _quantized(pulse(t + 0.2), 2.6, 3.8), PALE_BLUE), (far[0] + 5, far[1] - 6), 0.0, 0.65, "star")
    elif animation == "think":
        canvas.place(_thought(canvas), (112, 42), 0.0, 1.0, "thought")
    elif animation == "taunt":
        canvas.place(_label(canvas, "EVIDENCE?", 4.1), (30, 31), 0.0, 1.0, "taunt")


SPEC_DIR = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "specs"


def _spec_for(animation: str) -> dict | None:
    """The authored swing spec for one clip, or `None` for a clip with no swing."""
    path = SPEC_DIR / f"{animation}.spec.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _swing_axes(animation: str, frame_count: int):
    """Where the telescope is on each frame, measured on the sword part alone.

    ⛔ NOT the luminance inference `swing_effects` falls back to. That one holds
    for a dark fighter carrying bright steel; Carl is the other way round — a
    pale jacket and a dark brass barrel — so it would find his coat and miss the
    weapon. The rig knows which part is the sword, so it says so.
    """
    doc = _doc()
    samples = [doc.frame_time(animation, i, frame_count) for i in range(frame_count)]
    return strike_axis.from_part(doc, animation, samples, "sword")


def _raw_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    effect_animation = EFFECT_ALIASES.get(animation, animation)
    return compose_rig_frame(
        _doc(),
        animation,
        frame_idx,
        frame_count,
        behind=lambda canvas, t, world, params: _behind(effect_animation, canvas, t, world, params),
        front=lambda canvas, t, world, params: _front(effect_animation, canvas, t, world, params),
        # The composited swing trail and the authored hit volume are both derived
        # from these frames, so they land in the same padded space and
        # `build_sheet`'s auto-crop translates all three together.
        padding=RIG_RENDER_PADDING,
        # His effects are glyphs placed (`_glyph`); a pieces canvas records
        # each placement as a part.
        fx_pieces=True,
    )


@lru_cache(maxsize=None)
def _clip_frames(animation: str, frame_count: int) -> tuple:
    """Every frame of one clip, with its authored swing composited on.

    Cached per CLIP, not per frame: the trail on frame 4 is drawn from where the
    barrel was on frames 1-3, so a `render_fn` that only ever sees one frame
    cannot draw it — which is how a sheet ships with none of it.
    """
    raw = [_raw_frame(animation, i, frame_count) for i in range(frame_count)]
    spec = _spec_for(animation)
    if not spec:
        return tuple(raw)
    axes = _swing_axes(animation, frame_count)
    return tuple(swing_effects.composite_authored_effect(raw, spec, axes=axes))


@lru_cache(maxsize=1)
def _attack_hitboxes() -> dict:
    """The authored hit volume for every telescope swing that has a spec.

    Derived from the same axes and spec as the trail, so the arc a player is
    shown is the arc that hits them.
    """
    out = {}
    for animation, frame_count, _duration in ROWS:
        spec = _spec_for(animation)
        if not spec:
            continue
        raw = [_raw_frame(animation, i, frame_count) for i in range(frame_count)]
        poly = swing_effects.authored_hit_volume(
            raw, spec, axes=_swing_axes(animation, frame_count)
        )
        if poly:
            out[animation] = {"poly": poly}
    return out


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return _clip_frames(animation, frame_count)[frame_idx]


def render_portraits(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    face = FaceGuide(
        center_x=66.0,
        center_y=41.0,
        width=40.0,
        height=43.0,
        source_width=float(doc.frame["width"]),
        source_height=float(doc.frame["height"]),
    )

    def frame(animation: str, index: int, count: int):
        source = doc.render_at(
            animation,
            doc.frame_time(animation, index, count),
            supersample=4,
            scale=3,
        )
        return render_framed_portrait(source, face, view_width=70.0, center_y=59.0)

    clips = {
        "default": PortraitClip.loop(
            tuple(frame("idle", index, 8) for index in range(8)),
            duration_ms=148,
        ),
        # The pose a UI BOX draws. Frame 2 of the same idle — the still
        # this target published before its default began to move.
        "portrait": PortraitClip.still(frame("idle", 2, 8)),
        "curious": PortraitClip.still(frame("think", 4, 8)),
        "observing": PortraitClip.still(frame("use_telescope", 5, 10)),
        "cosmic": PortraitClip.still(frame("starstuff", 6, 10)),
    }
    return write_portrait_sheet(
        TARGET_NAME, clips, Path(out_dir), still_clip="portrait"
    )


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=frame_size(),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning or {"collision_scale": 1.58},
        attack_hitboxes=_attack_hitboxes(),
        pose_bodies="authored",
        # His paperdoll view is `Carl Stargan - Side Left` and both his rig
        # (`features.facing: "west"`) and his SVG (`data-rig-facing="west"`)
        # declare it. Publishing it is what makes the declaration real: without
        # this line the fact is authored at every layer and read by none, and he
        # renders facing away from his own movement exactly as the Patent Clerk
        # did.
        authored_faces_left=doc.authored_faces_left,
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        # trim: NOT passed, deliberately. `registry/pack_groups.py` is the single
        # authority — "all build paths ask `policy_for(target)` instead of
        # carrying independent defaults" — and its default packs, because Carl
        # draws through the trim-aware CharacterAnimator like every character.
        # He carried `trim=False` with no reason beside it, which is what left a
        # 155x156 frame around a 58x114 body: 3.7x the area, all of it
        # transparent margin that the height contract would scale.
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    # The part flipbook: a swing trail is drawn from the frames before it,
    # so each clip is recorded whole, uncached (`publish_rig_flipbook`).
    parts = publish_rig_flipbook(
        TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir),
        render_clip=lambda row, count: list(_clip_frames.__wrapped__(row, count)),
    )
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=frame_size())


__all__ = [
    "ACTOR_METADATA", "ROWS", "TARGET_NAME", "render", "render_canonical",
    "render_frame", "render_portraits",
]
