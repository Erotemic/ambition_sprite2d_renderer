"""Hand-authored procedural sprite sheet for reusable action VFX.

This target is intentionally *content*, not runtime integration.  It gives the
presentation layer a small visual vocabulary that can be reused across combat,
locomotion, pickups, spawning/despawning, and charged attacks without every game
system inventing its own rectangles or one-off art.

The renderer publishes two kinds of metadata:

* ``anchors`` live in ordinary frame metadata. ``sheet_build`` translates them
  through uniform auto-cropping and the existing RON emitter preserves them, so
  a runtime can already place these effects by an authored origin/contact point.
* ``effect`` frame notes plus ``*_authoring.yaml`` are author-owned semantics.
  The current Rust ``SheetRecord`` does not deserialize these fields. They are
  deliberately shipped next to the art so an integration pass can promote the
  useful pieces (looping, orientation, compositing, phase/intensity) without
  reconstructing authorial intent from pixels.

Rows are one-shot unless the authoring sidecar says otherwise.  One-shot rows
finish on a fully transparent frame so a simple animator can despawn on the end
without leaving a visual remnant. ``charge_pulse`` is the exception: it is a
seamless loop meant to sit between ``charge_start`` and a release effect.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet, write_canonical
from ...core.draw import overlay_draw
from ...yaml_io import safe_dump

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "generic_action_fx"
AUTHORING_FILE = f"{TARGET_NAME}_authoring.yaml"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
    AUTHORING_FILE,
)

FRAME_SIZE = (128, 128)
SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER

# Timing is part of the authored content.  The integration layer should use the
# published row durations rather than inventing its own effect lifetimes.
ROWS: List[Tuple[str, int, int]] = [
    ("hit_soft", 6, 42),
    ("hit_hard", 6, 38),
    ("hit_metal", 6, 38),
    ("hit_energy", 7, 42),
    ("landing_puff", 7, 55),
    ("skid_puff", 7, 48),
    ("wall_kick_puff", 6, 48),
    ("poof_small", 7, 58),
    ("poof_large", 8, 60),
    ("poof_magic", 8, 60),
    ("four_point_glint", 6, 66),
    ("pickup_twinkle", 8, 68),
    ("muzzle_flash", 5, 32),
    ("energy_release", 6, 40),
    ("beam_impact", 7, 42),
    ("charge_start", 8, 54),
    ("charge_pulse", 8, 58),
    ("release_ring", 7, 46),
]

# Palette: the same warm-light / plum-outline family as generic_explosions,
# expanded with cool energy and dusty neutrals. Effects should read as authored
# marks on top of the world rather than as opaque geometry.
OUTLINE = (42, 28, 48, 255)
OUTLINE_SOFT = (63, 50, 72, 220)
WHITE = (255, 255, 245, 255)
CREAM = (255, 244, 201, 255)
GOLD = (255, 211, 91, 255)
CORAL = (244, 130, 92, 255)
ROSE = (230, 112, 152, 255)
CYAN = (139, 225, 239, 255)
CYAN_HI = (218, 251, 255, 255)
BLUE = (101, 166, 220, 255)
VIOLET = (164, 120, 208, 255)
MAGENTA = (221, 116, 190, 255)
DUST = (177, 164, 177, 236)
DUST_HI = (216, 205, 207, 242)
DUST_DARK = (112, 96, 116, 220)
STEEL = (148, 181, 201, 255)
STEEL_DARK = (80, 112, 139, 230)


ACTOR_METADATA = {
    "actor": {
        "character_id": "fx_generic_action_fx",
        "display_name": "Generic Action FX",
    },
    "body": {
        "body_plan": "Effect",
        "body_kind": "Overlay",
        "mass_class": "Light",
        "locomotion_hint": "Stationary",
        "traits": ["fx", "overlay", "presentation"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "sockets": {
        "origin": {
            "source": f"{TARGET_NAME}.geometry",
            "point": {"x": 64.0, "y": 64.0},
        },
    },
    "tags": ["fx", "overlay", "presentation"],
}


# Row-level semantics authored alongside the art.  This is *not* silently
# treated as a runtime schema: write_authoring_sidecar() labels it accordingly.
EFFECT_SPECS: Dict[str, dict] = {
    "hit_soft": {
        "family": "impact",
        "intent": "Small organic/contact hit; readable without implying a heavy stagger.",
        "loop": False,
        "placement": "contact_point",
        "orientation": "radial",
        "mirror_x": False,
        "blend_mode_hint": "alpha",
        "nominal_diameter_px": 54,
    },
    "hit_hard": {
        "family": "impact",
        "intent": "Heavy contact punctuation with a broad, sharp silhouette.",
        "loop": False,
        "placement": "contact_point",
        "orientation": "radial",
        "mirror_x": False,
        "blend_mode_hint": "alpha",
        "nominal_diameter_px": 78,
    },
    "hit_metal": {
        "family": "impact",
        "intent": "Hard metallic clang: cool star core plus thrown sparks.",
        "loop": False,
        "placement": "contact_point",
        "orientation": "radial",
        "mirror_x": False,
        "blend_mode_hint": "alpha",
        "nominal_diameter_px": 70,
    },
    "hit_energy": {
        "family": "impact",
        "intent": "Energy/magic impact with a broken ring and petaled bloom.",
        "loop": False,
        "placement": "contact_point",
        "orientation": "radial",
        "mirror_x": False,
        "blend_mode_hint": "alpha_or_additive",
        "nominal_diameter_px": 82,
    },
    "landing_puff": {
        "family": "ground_contact",
        "intent": "Symmetric cartoon dust for landing, stomp, or sudden grounded stop.",
        "loop": False,
        "placement": "surface_contact",
        "orientation": "surface_tangent",
        "mirror_x": False,
        "blend_mode_hint": "alpha",
        "nominal_span_px": 90,
    },
    "skid_puff": {
        "family": "ground_contact",
        "intent": "Directional dust wake; authored trailing left and intended to mirror with travel/facing.",
        "loop": False,
        "placement": "surface_contact",
        "orientation": "surface_tangent_directional",
        "mirror_x": True,
        "blend_mode_hint": "alpha",
        "nominal_span_px": 96,
    },
    "wall_kick_puff": {
        "family": "surface_contact",
        "intent": "Kick-off puff emitted away from a wall or arbitrary contact surface.",
        "loop": False,
        "placement": "surface_contact",
        "orientation": "align_positive_x_to_surface_normal",
        "mirror_x": True,
        "blend_mode_hint": "alpha",
        "nominal_span_px": 74,
    },
    "poof_small": {
        "family": "poof",
        "intent": "Compact non-magical disappearance/spawn puff for small objects.",
        "loop": False,
        "placement": "entity_origin",
        "orientation": "radial",
        "mirror_x": False,
        "blend_mode_hint": "alpha",
        "nominal_diameter_px": 60,
    },
    "poof_large": {
        "family": "poof",
        "intent": "Large chunky smoke poof for enemies, props, or transformations.",
        "loop": False,
        "placement": "entity_origin",
        "orientation": "radial",
        "mirror_x": False,
        "blend_mode_hint": "alpha",
        "nominal_diameter_px": 92,
    },
    "poof_magic": {
        "family": "poof",
        "intent": "Magical transformation/teleport poof with cool swirl and glints.",
        "loop": False,
        "placement": "entity_origin",
        "orientation": "radial",
        "mirror_x": False,
        "blend_mode_hint": "alpha_or_additive",
        "nominal_diameter_px": 88,
    },
    "four_point_glint": {
        "family": "glint",
        "intent": "Fast neutral highlight glint for metal, glass, magic, or cleanliness beats.",
        "loop": False,
        "placement": "feature_point",
        "orientation": "screen_or_world_aligned",
        "mirror_x": False,
        "blend_mode_hint": "alpha_or_additive",
        "nominal_diameter_px": 54,
    },
    "pickup_twinkle": {
        "family": "glint",
        "intent": "Warm celebratory sparkle for pickups, rewards, and item presentation.",
        "loop": False,
        "placement": "entity_origin",
        "orientation": "radial",
        "mirror_x": False,
        "blend_mode_hint": "alpha_or_additive",
        "nominal_diameter_px": 64,
    },
    "muzzle_flash": {
        "family": "release",
        "intent": "Very fast warm directional release flash for projectile emitters.",
        "loop": False,
        "placement": "emitter_socket",
        "orientation": "positive_x_is_forward",
        "mirror_x": True,
        "blend_mode_hint": "alpha_or_additive",
        "nominal_length_px": 88,
    },
    "energy_release": {
        "family": "release",
        "intent": "Broad cool directional release for beams, spells, or charged projectiles.",
        "loop": False,
        "placement": "emitter_socket",
        "orientation": "positive_x_is_forward",
        "mirror_x": True,
        "blend_mode_hint": "alpha_or_additive",
        "nominal_length_px": 94,
    },
    "beam_impact": {
        "family": "impact",
        "intent": "Energetic terminal splash for a beam/projectile striking a surface.",
        "loop": False,
        "placement": "contact_point",
        "orientation": "align_positive_x_to_surface_normal_optional",
        "mirror_x": True,
        "blend_mode_hint": "alpha_or_additive",
        "nominal_diameter_px": 86,
    },
    "charge_start": {
        "family": "charge",
        "intent": "One-shot convergence into a stable charge core; precedes charge_pulse.",
        "loop": False,
        "placement": "charge_origin",
        "orientation": "radial",
        "mirror_x": False,
        "blend_mode_hint": "alpha_or_additive",
        "nominal_diameter_px": 86,
    },
    "charge_pulse": {
        "family": "charge",
        "intent": "Seamless held-charge loop; first and last samples meet continuously.",
        "loop": True,
        "placement": "charge_origin",
        "orientation": "radial",
        "mirror_x": False,
        "blend_mode_hint": "alpha_or_additive",
        "nominal_diameter_px": 68,
    },
    "release_ring": {
        "family": "release",
        "intent": "Radial release/shock ring for charge completion, teleport, shield pop, or pulse.",
        "loop": False,
        "placement": "effect_origin",
        "orientation": "radial",
        "mirror_x": False,
        "blend_mode_hint": "alpha_or_additive",
        "nominal_diameter_px": 108,
    },
}


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _mul_alpha(color: RGBA, factor: float) -> RGBA:
    factor = max(0.0, min(1.0, factor))
    return color[0], color[1], color[2], int(round(color[3] * factor))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _clamp(t: float) -> float:
    return max(0.0, min(1.0, t))


def _smooth(t: float) -> float:
    t = _clamp(t)
    return t * t * (3.0 - 2.0 * t)


def _ease_out(t: float) -> float:
    t = _clamp(t)
    return 1.0 - (1.0 - t) ** 3


def _layer(img: Image.Image) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    return overlay_draw(img)


def _polygon(
    img: Image.Image,
    points: Sequence[Point],
    *,
    fill: RGBA,
    outline: RGBA | None = None,
    width: float = 1.0,
) -> None:
    layer, draw = _layer(img)
    pts = [(_s(x), _s(y)) for x, y in points]
    draw.polygon(pts, fill=fill)
    if outline and len(pts) > 1:
        draw.line(pts + [pts[0]], fill=outline, width=max(1, _s(width)), joint="curve")
    img.alpha_composite(layer)


def _ellipse(
    img: Image.Image,
    bbox: tuple[float, float, float, float],
    *,
    fill: RGBA | None = None,
    outline: RGBA | None = None,
    width: float = 1.0,
) -> None:
    layer, draw = _layer(img)
    draw.ellipse(tuple(_s(v) for v in bbox), fill=fill, outline=outline, width=max(1, _s(width)))
    img.alpha_composite(layer)


def _line(
    img: Image.Image,
    points: Sequence[Point],
    *,
    fill: RGBA,
    width: float,
) -> None:
    layer, draw = _layer(img)
    draw.line([(_s(x), _s(y)) for x, y in points], fill=fill, width=max(1, _s(width)), joint="curve")
    img.alpha_composite(layer)


def _arc(
    img: Image.Image,
    bbox: tuple[float, float, float, float],
    start: float,
    end: float,
    *,
    fill: RGBA,
    width: float,
) -> None:
    layer, draw = _layer(img)
    draw.arc(tuple(_s(v) for v in bbox), start=start, end=end, fill=fill, width=max(1, _s(width)))
    img.alpha_composite(layer)


def _star_points(
    cx: float,
    cy: float,
    outer: float,
    inner: float,
    spokes: int,
    *,
    rotation: float = 0.0,
    aspect_y: float = 1.0,
) -> List[Point]:
    pts: List[Point] = []
    for i in range(spokes * 2):
        a = rotation + math.tau * i / (spokes * 2)
        r = outer if i % 2 == 0 else inner
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * aspect_y))
    return pts


def _four_point_points(cx: float, cy: float, rx: float, ry: float, waist: float = 0.23) -> List[Point]:
    return [
        (cx, cy - ry),
        (cx + rx * waist, cy - ry * waist),
        (cx + rx, cy),
        (cx + rx * waist, cy + ry * waist),
        (cx, cy + ry),
        (cx - rx * waist, cy + ry * waist),
        (cx - rx, cy),
        (cx - rx * waist, cy - ry * waist),
    ]


def _diamond(img: Image.Image, x: float, y: float, r: float, color: RGBA) -> None:
    _polygon(img, [(x, y - r), (x + r * 0.58, y), (x, y + r), (x - r * 0.58, y)], fill=color)


def _ring_cloud(
    img: Image.Image,
    cx: float,
    cy: float,
    radius: float,
    puff_r: float,
    count: int,
    *,
    fill: RGBA,
    outline: RGBA,
    phase: float = 0.0,
    aspect_y: float = 0.86,
) -> None:
    # Deterministic hand-drawn irregularity: each puff is intentionally a little
    # different, but no RNG means authored output stays byte-stable.
    for i in range(count):
        a = phase + math.tau * i / count
        wobble = 1.0 + 0.08 * math.sin(i * 2.17 + phase * 1.9)
        rr = radius * wobble
        x = cx + math.cos(a) * rr
        y = cy + math.sin(a) * rr * aspect_y
        prx = puff_r * (0.88 + 0.13 * math.sin(i * 1.51 + 0.4))
        pry = puff_r * (0.78 + 0.16 * math.cos(i * 1.73 + 0.7))
        _ellipse(
            img,
            (x - prx, y - pry, x + prx, y + pry),
            fill=fill,
            outline=outline,
            width=1.2,
        )


def _origin_for(anim: str) -> tuple[float, float]:
    if anim == "landing_puff":
        return 64.0, 89.0
    if anim == "skid_puff":
        return 88.0, 88.0
    if anim == "wall_kick_puff":
        return 28.0, 66.0
    if anim in {"muzzle_flash", "energy_release"}:
        return 24.0, 64.0
    if anim == "beam_impact":
        return 47.0, 64.0
    return 64.0, 64.0


def _draw_hit_soft(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.34) / 0.66))
    outer = _lerp(23.0, 34.0, q)
    inner = _lerp(10.5, 6.0, q)
    rot = -0.12 + p * 0.16
    _polygon(
        img,
        _star_points(cx, cy, outer, inner, 7, rotation=rot, aspect_y=0.86),
        fill=_mul_alpha(CREAM, 0.82 * fade),
        outline=_mul_alpha(OUTLINE, 0.72 * fade),
        width=1.4,
    )
    _ellipse(
        img,
        (cx - 10, cy - 8, cx + 10, cy + 8),
        fill=_mul_alpha(WHITE, fade),
        outline=_mul_alpha(CORAL, 0.68 * fade),
        width=1.0,
    )
    for i, a in enumerate((-0.50, 0.53, 2.65)):
        r0 = _lerp(22.0, 30.0, q)
        r1 = r0 + _lerp(5.0, 10.0, q)
        _line(
            img,
            [(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1)],
            fill=_mul_alpha(CORAL if i != 1 else GOLD, 0.72 * fade),
            width=2.0,
        )


def _draw_hit_hard(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.30) / 0.70))
    outer = _lerp(34.0, 50.0, q)
    _polygon(
        img,
        _star_points(cx, cy, outer, _lerp(11.0, 6.0, q), 8, rotation=math.pi / 8, aspect_y=0.92),
        fill=_mul_alpha(CORAL, 0.76 * fade),
        outline=_mul_alpha(OUTLINE, 0.82 * fade),
        width=1.5,
    )
    _polygon(
        img,
        _star_points(cx, cy, outer * 0.72, 8.0, 6, rotation=0.02, aspect_y=0.9),
        fill=_mul_alpha(GOLD, 0.92 * fade),
    )
    _ellipse(img, (cx - 10, cy - 9, cx + 10, cy + 9), fill=_mul_alpha(WHITE, fade))
    # Two broad hand-drawn cut marks give the impact a distinct, decisive beat.
    slash = _lerp(27.0, 40.0, q)
    _line(img, [(cx - slash, cy + slash * 0.44), (cx + slash, cy - slash * 0.44)], fill=_mul_alpha(WHITE, 0.82 * fade), width=3.2)
    _line(img, [(cx - slash * 0.55, cy - slash * 0.62), (cx + slash * 0.55, cy + slash * 0.62)], fill=_mul_alpha(CREAM, 0.58 * fade), width=1.9)


def _draw_hit_metal(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.28) / 0.72))
    rx = _lerp(19.0, 34.0, q)
    ry = _lerp(25.0, 44.0, q)
    _polygon(img, _four_point_points(cx, cy, rx, ry, 0.18), fill=_mul_alpha(CYAN_HI, fade), outline=_mul_alpha(STEEL_DARK, 0.8 * fade), width=1.2)
    _polygon(img, _four_point_points(cx, cy, rx * 0.50, ry * 0.50, 0.22), fill=_mul_alpha(WHITE, fade))
    spin = p * 0.45
    for i in range(7):
        a = spin + math.tau * i / 7.0
        r0 = _lerp(20.0, 33.0, q)
        r1 = r0 + _lerp(7.0, 20.0, q) * (0.72 + 0.25 * math.sin(i * 1.7))
        col = GOLD if i % 3 == 0 else STEEL
        _line(img, [(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], fill=_mul_alpha(col, 0.92 * fade), width=1.7)
        if i % 2 == 0:
            _diamond(img, cx + math.cos(a) * (r1 + 2.0), cy + math.sin(a) * (r1 + 2.0), 2.0, _mul_alpha(WHITE, 0.85 * fade))
    _arc(img, (cx - 39, cy - 31, cx + 39, cy + 31), 208, 320, fill=_mul_alpha(STEEL, 0.45 * fade), width=1.4)


def _draw_hit_energy(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.42) / 0.58))
    ring = _lerp(16.0, 44.0, q)
    _ellipse(img, (cx - ring, cy - ring, cx + ring, cy + ring), outline=_mul_alpha(CYAN, 0.72 * fade), width=_lerp(3.1, 1.2, q))
    _arc(img, (cx - ring * 1.05, cy - ring * 0.92, cx + ring * 1.05, cy + ring * 0.92), 22, 148, fill=_mul_alpha(MAGENTA, 0.72 * fade), width=2.2)
    _arc(img, (cx - ring * 1.05, cy - ring * 0.92, cx + ring * 1.05, cy + ring * 0.92), 205, 326, fill=_mul_alpha(BLUE, 0.65 * fade), width=1.8)
    bloom = _lerp(22.0, 29.0, q)
    _polygon(img, _star_points(cx, cy, bloom, 9.0, 9, rotation=p * 0.25), fill=_mul_alpha(VIOLET, 0.46 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.45 * fade), width=1.0)
    _ellipse(img, (cx - 11, cy - 11, cx + 11, cy + 11), fill=_mul_alpha(CYAN_HI, 0.96 * fade))
    _ellipse(img, (cx - 5, cy - 5, cx + 5, cy + 5), fill=_mul_alpha(WHITE, fade))


def _dust_puff(img: Image.Image, x: float, y: float, rx: float, ry: float, alpha: float, *, bright: bool = False) -> None:
    fill = DUST_HI if bright else DUST
    _ellipse(img, (x - rx, y - ry, x + rx, y + ry), fill=_mul_alpha(fill, alpha), outline=_mul_alpha(DUST_DARK, alpha * 0.75), width=1.1)


def _draw_landing_puff(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("landing_puff")
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.44) / 0.56))
    for side in (-1, 1):
        for i in range(4):
            dist = _lerp(7.0 + i * 4.0, 25.0 + i * 8.0, q)
            x = ox + side * dist
            y = oy - _lerp(4.0 + i * 1.8, 8.0 + i * 2.6, q) + 1.5 * math.sin(i * 1.9)
            rx = _lerp(8.0, 11.0 + i * 0.7, q)
            ry = _lerp(6.0, 3.5 + i * 0.4, q)
            _dust_puff(img, x, y, rx, ry, 0.88 * fade * (1.0 - i * 0.08), bright=i < 2)
    _line(img, [(ox - 16 - 15 * q, oy + 1), (ox + 16 + 15 * q, oy + 1)], fill=_mul_alpha(DUST_HI, 0.42 * fade), width=1.4)


def _draw_skid_puff(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("skid_puff")
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.46) / 0.54))
    for i in range(6):
        dist = _lerp(4.0 + i * 5.5, 10.0 + i * 12.0, q)
        x = ox - dist
        y = oy - 4.0 - (i % 2) * 4.0 - q * (2.0 + i * 0.8)
        rx = 8.5 + i * 0.8
        ry = max(3.2, 6.5 - i * 0.35)
        _dust_puff(img, x, y, rx, ry, 0.9 * fade * (1.0 - i * 0.075), bright=i < 2)
    for i in range(3):
        x = ox - _lerp(18.0 + i * 17.0, 35.0 + i * 22.0, q)
        _line(img, [(x, oy + 1.5), (x - 11.0 - i * 3.0, oy + 1.5)], fill=_mul_alpha(DUST_HI, 0.42 * fade), width=1.0 + i * 0.15)


def _draw_wall_kick_puff(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("wall_kick_puff")
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.42) / 0.58))
    for i, ang in enumerate((-0.52, -0.26, 0.0, 0.25, 0.50)):
        dist = _lerp(8.0, 42.0 + abs(i - 2) * 3.0, q)
        x = ox + math.cos(ang) * dist
        y = oy + math.sin(ang) * dist
        _dust_puff(img, x, y, 8.0 + i % 2, 5.4, 0.86 * fade, bright=i in (1, 2, 3))
        _line(img, [(ox + 4, oy), (ox + math.cos(ang) * (dist + 9), oy + math.sin(ang) * (dist + 9))], fill=_mul_alpha(DUST_HI, 0.30 * fade), width=1.0)


def _draw_poof(img: Image.Image, p: float, *, scale: float, magic: bool) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.52) / 0.48))
    radius = scale * _lerp(8.0, 31.0, q)
    puff = scale * _lerp(8.5, 12.5, q)
    if magic:
        fill = _mul_alpha(VIOLET, 0.66 * fade)
        outline = _mul_alpha(OUTLINE, 0.72 * fade)
        _ring_cloud(img, cx, cy, radius, puff, 8, fill=fill, outline=outline, phase=0.28 + p * 0.45)
        _arc(img, (cx - radius * 1.2, cy - radius * 1.2, cx + radius * 1.2, cy + radius * 1.2), 198 - p * 35, 350 - p * 35, fill=_mul_alpha(CYAN, 0.82 * fade), width=2.0)
        _arc(img, (cx - radius * 0.78, cy - radius * 0.78, cx + radius * 0.78, cy + radius * 0.78), 25 + p * 50, 175 + p * 50, fill=_mul_alpha(MAGENTA, 0.72 * fade), width=1.6)
        for i in range(3):
            a = 0.7 + i * 2.1 + p * 0.8
            r = radius + 9.0 + i * 2.0
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
            _polygon(img, _four_point_points(x, y, 3.2, 5.0), fill=_mul_alpha(CYAN_HI if i != 1 else CREAM, 0.9 * fade))
    else:
        fill = _mul_alpha(DUST_HI, 0.84 * fade)
        outline = _mul_alpha(DUST_DARK, 0.78 * fade)
        _ring_cloud(img, cx, cy, radius, puff, 8 if scale > 1.0 else 7, fill=fill, outline=outline, phase=0.18)
        if p < 0.58:
            core_r = scale * _lerp(10.0, 20.0, q)
            _ellipse(img, (cx - core_r, cy - core_r * 0.78, cx + core_r, cy + core_r * 0.78), fill=_mul_alpha(DUST, 0.62 * fade))
        for i in range(4):
            a = -0.8 + i * 1.7
            r = radius + 5.0 + 8.0 * q
            _diamond(img, cx + math.cos(a) * r, cy + math.sin(a) * r, 1.6 + (i % 2) * 0.7, _mul_alpha(CREAM, 0.48 * fade))


def _draw_four_point_glint(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    pulse = math.sin(math.pi * _clamp(p))
    fade = pulse ** 0.58
    rx = 5.0 + 27.0 * pulse
    ry = 7.0 + 35.0 * pulse
    _polygon(img, _four_point_points(cx, cy, rx, ry, 0.16), fill=_mul_alpha(CYAN_HI, fade), outline=_mul_alpha(BLUE, 0.46 * fade), width=1.0)
    _polygon(img, _four_point_points(cx, cy, rx * 0.43, ry * 0.43, 0.20), fill=_mul_alpha(WHITE, fade))
    if pulse > 0.35:
        _ellipse(img, (cx - rx * 0.58, cy - ry * 0.58, cx + rx * 0.58, cy + ry * 0.58), outline=_mul_alpha(CYAN, 0.34 * fade), width=1.0)


def _draw_pickup_twinkle(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    pulse = math.sin(math.pi * p) ** 0.72
    fade = pulse
    rot = -math.pi / 2 + p * 0.45
    _polygon(img, _star_points(cx, cy, 28.0 * pulse + 3.0, 11.0 * pulse + 2.0, 5, rotation=rot), fill=_mul_alpha(GOLD, 0.90 * fade), outline=_mul_alpha(OUTLINE, 0.65 * fade), width=1.2)
    _polygon(img, _star_points(cx, cy, 16.0 * pulse + 2.0, 7.0 * pulse + 1.0, 5, rotation=rot), fill=_mul_alpha(WHITE, 0.96 * fade))
    for i in range(4):
        a = p * 0.9 + math.tau * i / 4.0
        r = 31.0 + 7.0 * math.sin(math.pi * p)
        _diamond(img, cx + math.cos(a) * r, cy + math.sin(a) * r * 0.82, 2.0 + (i % 2), _mul_alpha(CREAM if i % 2 else CYAN_HI, 0.82 * fade))


def _draw_muzzle_flash(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("muzzle_flash")
    q = _ease_out(p)
    fade = 1.0 - _smooth(p)
    length = _lerp(82.0, 48.0, q)
    half = _lerp(22.0, 9.0, q)
    pts = [
        (ox - 2, oy),
        (ox + 13, oy - half * 0.42),
        (ox + 20, oy - half),
        (ox + length * 0.54, oy - half * 0.30),
        (ox + length, oy),
        (ox + length * 0.54, oy + half * 0.30),
        (ox + 20, oy + half),
        (ox + 13, oy + half * 0.42),
    ]
    _polygon(img, pts, fill=_mul_alpha(GOLD, 0.92 * fade), outline=_mul_alpha(OUTLINE, 0.75 * fade), width=1.2)
    inner = [(ox, oy), (ox + length * 0.70, oy - half * 0.17), (ox + length * 0.92, oy), (ox + length * 0.70, oy + half * 0.17)]
    _polygon(img, inner, fill=_mul_alpha(WHITE, fade))
    _ellipse(img, (ox - 8, oy - 8, ox + 8, oy + 8), outline=_mul_alpha(CORAL, 0.65 * fade), width=2.0)


def _draw_energy_release(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("energy_release")
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.18) / 0.82))
    length = _lerp(70.0, 94.0, q)
    half = _lerp(13.0, 26.0, math.sin(math.pi * min(1.0, p * 1.1)))
    pts = [(ox, oy), (ox + length * 0.58, oy - half), (ox + length, oy), (ox + length * 0.58, oy + half)]
    _polygon(img, pts, fill=_mul_alpha(BLUE, 0.46 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.50 * fade), width=1.1)
    inner = [(ox, oy), (ox + length * 0.52, oy - half * 0.38), (ox + length * 0.89, oy), (ox + length * 0.52, oy + half * 0.38)]
    _polygon(img, inner, fill=_mul_alpha(CYAN_HI, 0.92 * fade))
    _line(img, [(ox + 8, oy), (ox + length * 0.84, oy)], fill=_mul_alpha(WHITE, 0.92 * fade), width=2.5)
    ring = _lerp(9.0, 26.0, q)
    _ellipse(img, (ox - ring, oy - ring, ox + ring, oy + ring), outline=_mul_alpha(CYAN, 0.62 * fade), width=2.0)


def _draw_beam_impact(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("beam_impact")
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.40) / 0.60))
    # Contact is on the left; the bloom opens into +X, so it can align to a
    # struck surface normal just like the directional release effects.
    for i, ang in enumerate((-1.08, -0.64, -0.26, 0.20, 0.62, 1.02)):
        length = _lerp(17.0, 48.0 + (i % 2) * 7.0, q)
        end = (ox + math.cos(ang) * length, oy + math.sin(ang) * length)
        _line(img, [(ox + 4, oy), end], fill=_mul_alpha(CYAN if i % 2 else MAGENTA, 0.72 * fade), width=2.2 if i in (2, 3) else 1.5)
        _diamond(img, end[0], end[1], 2.5, _mul_alpha(CYAN_HI, 0.85 * fade))
    ring = _lerp(10.0, 34.0, q)
    _arc(img, (ox - ring * 0.35, oy - ring, ox + ring * 1.65, oy + ring), 205, 515, fill=_mul_alpha(CYAN, 0.62 * fade), width=2.0)
    _polygon(img, _star_points(ox + 11, oy, _lerp(16.0, 24.0, q), 7.0, 7, rotation=0.18), fill=_mul_alpha(VIOLET, 0.58 * fade), outline=_mul_alpha(OUTLINE, 0.55 * fade), width=1.0)
    _ellipse(img, (ox + 3, oy - 8, ox + 19, oy + 8), fill=_mul_alpha(WHITE, fade))


def _draw_charge_start(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _smooth(p)
    core = _lerp(2.0, 12.0, q)
    ring = _lerp(47.0, 19.0, q)
    _ellipse(img, (cx - core, cy - core, cx + core, cy + core), fill=_mul_alpha(CYAN_HI, 0.35 + 0.65 * q), outline=_mul_alpha(BLUE, 0.72), width=1.2)
    _arc(img, (cx - ring, cy - ring, cx + ring, cy + ring), 18 + p * 80, 168 + p * 80, fill=_mul_alpha(CYAN, 0.75), width=1.8)
    _arc(img, (cx - ring, cy - ring, cx + ring, cy + ring), 205 + p * 80, 332 + p * 80, fill=_mul_alpha(MAGENTA, 0.58), width=1.5)
    for i in range(8):
        a = math.tau * i / 8.0 + p * 0.55
        r = _lerp(50.0 + (i % 2) * 5.0, 16.0 + (i % 3), q)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        _diamond(img, x, y, _lerp(2.1, 3.0, q), _mul_alpha(CREAM if i % 3 == 0 else CYAN_HI, 0.88))
        # tiny inward comet tail: the visual motion is authored into each frame
        # rather than delegated to a particle system.
        tail = 6.0 + 4.0 * (1.0 - q)
        _line(img, [(x + math.cos(a) * tail, y + math.sin(a) * tail), (x, y)], fill=_mul_alpha(BLUE, 0.45), width=1.0)


def _draw_charge_pulse(img: Image.Image, p: float) -> None:
    # Sample a periodic function at n equally spaced points, not n-1: frame 0
    # does not duplicate the last frame, so looping frame N-1 -> 0 is smooth.
    cx, cy = 64.0, 64.0
    phase = math.tau * p
    pulse = 0.5 + 0.5 * math.sin(phase)
    core = 9.0 + 3.5 * pulse
    ring = 24.0 + 5.0 * pulse
    _ellipse(img, (cx - core, cy - core, cx + core, cy + core), fill=_mul_alpha(CYAN_HI, 0.82), outline=_mul_alpha(BLUE, 0.80), width=1.3)
    _ellipse(img, (cx - core * 0.42, cy - core * 0.42, cx + core * 0.42, cy + core * 0.42), fill=_mul_alpha(WHITE, 0.95))
    _ellipse(img, (cx - ring, cy - ring, cx + ring, cy + ring), outline=_mul_alpha(CYAN, 0.46 + 0.18 * pulse), width=1.5)
    for i in range(5):
        a = phase + math.tau * i / 5.0
        r = 31.0 + 3.0 * math.sin(phase * 2 + i)
        _diamond(img, cx + math.cos(a) * r, cy + math.sin(a) * r, 2.0 + (i % 2), _mul_alpha(CREAM if i == 0 else MAGENTA, 0.72))


def _draw_release_ring(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.38) / 0.62))
    r = _lerp(11.0, 54.0, q)
    _ellipse(img, (cx - r, cy - r, cx + r, cy + r), outline=_mul_alpha(CYAN_HI, 0.76 * fade), width=_lerp(4.0, 1.2, q))
    _arc(img, (cx - r * 1.05, cy - r * 1.05, cx + r * 1.05, cy + r * 1.05), 18, 102, fill=_mul_alpha(MAGENTA, 0.76 * fade), width=2.0)
    _arc(img, (cx - r * 1.05, cy - r * 1.05, cx + r * 1.05, cy + r * 1.05), 197, 292, fill=_mul_alpha(GOLD, 0.58 * fade), width=1.7)
    for i, a in enumerate((0.18, 1.72, 3.28, 4.86)):
        rr = r + _lerp(3.0, 10.0, q)
        _diamond(img, cx + math.cos(a) * rr, cy + math.sin(a) * rr, 2.2 + (i % 2), _mul_alpha(WHITE, 0.76 * fade))


def _frame_progress(anim: str, frame_idx: int, nframes: int) -> float:
    if anim == "charge_pulse":
        # Periodic samples around [0, 1); do not duplicate 0 at the end.
        return frame_idx / max(1, nframes)
    return frame_idx / max(1, nframes - 1)


def _phase(anim: str, p: float) -> str:
    if anim == "charge_pulse":
        return "hold"
    if anim == "charge_start":
        return "converge" if p < 0.75 else "settle"
    if anim in {"landing_puff", "skid_puff", "wall_kick_puff", "poof_small", "poof_large", "poof_magic"}:
        if p < 0.28:
            return "form"
        if p < 0.62:
            return "spread"
        return "dissipate"
    if anim in {"four_point_glint", "pickup_twinkle"}:
        return "brighten" if p < 0.5 else "fade"
    if anim == "release_ring":
        return "expand" if p < 0.55 else "dissipate"
    if p < 0.18:
        return "impact"
    if p < 0.58:
        return "follow_through"
    return "dissipate"


def _intensity(anim: str, p: float) -> float:
    if anim == "charge_pulse":
        return round(0.72 + 0.20 * (0.5 + 0.5 * math.sin(math.tau * p)), 4)
    if anim == "charge_start":
        return round(_lerp(0.3, 1.0, _smooth(p)), 4)
    if anim in {"four_point_glint", "pickup_twinkle"}:
        return round(math.sin(math.pi * p) ** 0.72, 4)
    return round(1.0 - 0.72 * _smooth(p), 4)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    p = _frame_progress(anim, frame_idx, nframes)
    # Every one-shot ends fully clear. This is authored playback behavior, not
    # a cleanup performed by the runtime.
    if anim != "charge_pulse" and frame_idx == nframes - 1:
        return Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if anim == "hit_soft":
        _draw_hit_soft(img, p)
    elif anim == "hit_hard":
        _draw_hit_hard(img, p)
    elif anim == "hit_metal":
        _draw_hit_metal(img, p)
    elif anim == "hit_energy":
        _draw_hit_energy(img, p)
    elif anim == "landing_puff":
        _draw_landing_puff(img, p)
    elif anim == "skid_puff":
        _draw_skid_puff(img, p)
    elif anim == "wall_kick_puff":
        _draw_wall_kick_puff(img, p)
    elif anim == "poof_small":
        _draw_poof(img, p, scale=0.76, magic=False)
    elif anim == "poof_large":
        _draw_poof(img, p, scale=1.15, magic=False)
    elif anim == "poof_magic":
        _draw_poof(img, p, scale=1.02, magic=True)
    elif anim == "four_point_glint":
        _draw_four_point_glint(img, p)
    elif anim == "pickup_twinkle":
        _draw_pickup_twinkle(img, p)
    elif anim == "muzzle_flash":
        _draw_muzzle_flash(img, p)
    elif anim == "energy_release":
        _draw_energy_release(img, p)
    elif anim == "beam_impact":
        _draw_beam_impact(img, p)
    elif anim == "charge_start":
        _draw_charge_start(img, p)
    elif anim == "charge_pulse":
        _draw_charge_pulse(img, p)
    elif anim == "release_ring":
        _draw_release_ring(img, p)
    else:
        raise ValueError(f"unknown animation: {anim}")
    return img.resize(FRAME_SIZE, Image.Resampling.NEAREST)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    p = _frame_progress(anim, frame_idx, nframes)
    ox, oy = _origin_for(anim)
    anchors = {"origin": {"x": ox, "y": oy}}
    if EFFECT_SPECS[anim]["placement"] in {"contact_point", "surface_contact"}:
        anchors["contact"] = {"x": ox, "y": oy}
    if EFFECT_SPECS[anim]["placement"] == "emitter_socket":
        anchors["emitter"] = {"x": ox, "y": oy}
    return {
        "anchors": anchors,
        # Human-/tool-facing author notes. The current RON emitter intentionally
        # preserves anchors only; see the companion authoring YAML for the
        # proposed contract and promotion guidance.
        "effect": {
            "family": EFFECT_SPECS[anim]["family"],
            "phase": _phase(anim, p),
            "progress": round(p, 4),
            "intensity_hint": _intensity(anim, p),
            "clear_frame": bool(anim != "charge_pulse" and frame_idx == nframes - 1),
        },
    }


def _frame_notes(anim: str, nframes: int) -> List[dict]:
    return [
        {
            "frame": i,
            "phase": _phase(anim, _frame_progress(anim, i, nframes)),
            "progress": round(_frame_progress(anim, i, nframes), 4),
            "intensity_hint": _intensity(anim, _frame_progress(anim, i, nframes)),
            "clear_frame": bool(anim != "charge_pulse" and i == nframes - 1),
        }
        for i in range(nframes)
    ]


def _authoring_document() -> dict:
    rows = {name: (frames, duration_ms) for name, frames, duration_ms in ROWS}
    animations = {}
    for name, spec in EFFECT_SPECS.items():
        nframes, duration_ms = rows[name]
        animations[name] = {
            **spec,
            "frame_count": nframes,
            "frame_duration_ms": duration_ms,
            "total_duration_ms": nframes * duration_ms,
            "origin_anchor": "origin",
            "frames": _frame_notes(name, nframes),
        }
    return {
        "schema": "ambition.sprite_vfx_authoring",
        "schema_version": 1,
        "target": TARGET_NAME,
        "status": "authoring_hints_not_yet_runtime_contract",
        "coordinate_space": "logical_frame_pixels; manifest anchors are translated through auto-crop/trim",
        "author_owned_fields": [
            "animation timing",
            "origin/contact/emitter anchors",
            "loop intent",
            "direction/orientation intent",
            "mirror allowance",
            "visual phase and relative intensity",
            "suggested compositing family",
            "nominal authored visual span",
        ],
        "runtime_promotion_notes": [
            "The current SheetRecord RON preserves frame anchors but not the arbitrary frame effect payload.",
            "Treat anchors and row duration as authoritative immediately; do not re-measure pivots from alpha bounds.",
            "If loop/orientation/blend hints become useful across multiple effects, promote them into a generic sprite-effect runtime schema rather than hard-coding animation names.",
            "Blend mode values are visual intent, not a requirement: alpha remains a valid fallback on render backends without additive material support.",
            "Directional rows are authored with +X as forward. Mirror or rotate the whole effect around the origin anchor; do not mirror individual packed frame rectangles by hand.",
            "One-shot rows end in a transparent clear frame. charge_pulse is intentionally periodic and should loop until a gameplay/presentation cue advances to release.",
        ],
        "animations": animations,
    }


def write_authoring_sidecar(out_dir: Path) -> Path:
    path = out_dir / AUTHORING_FILE
    path.write_text(safe_dump(_authoring_document(), sort_keys=False, width=120), encoding="utf8")
    return path


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_draw_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        frame_meta_fn=_frame_meta,
        auto_crop=True,
        crop_margin=5,
        actor_metadata=ACTOR_METADATA,
    )
    authoring = write_authoring_sidecar(out_dir)
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        authoring,
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ]


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        _draw_frame,
        Path(out_dir),
        frame_size=FRAME_SIZE,
        crop_margin=5,
    )
