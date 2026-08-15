"""Hand-authored procedural sprites for unusual reusable presentation VFX.

This third generic VFX catalog deliberately explores visual grammars not covered
by ``generic_action_fx`` or ``generic_world_fx``: smoke and gas, slime and acid,
sonic and psychic marks, time distortion, ritual/rune magic, mechanical debris,
loot punctuation, vegetation/spores, sand, and shadow wisps.

The module is authored content only. Runtime integration belongs to the game and
presentation layers. Current sheet metadata carries authoritative frame timing
and placement anchors. The companion ``*_authoring.yaml`` publishes additional
author-owned semantics that are intentionally non-binding until repeated use
justifies promotion into a generic engine VFX schema.

Conventions:
* one-shots end on a deliberately clear frame;
* loops are periodic over [0, 1) and do not contain a clear terminal frame;
* directional effects author +X as forward;
* placement anchors are semantic pivots, not alpha-bound guesses;
* visual motion is authored in local effect space so presentation may rotate the
  whole sprite into a gravity-relative or surface-relative frame later.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet, write_canonical
from ...yaml_io import safe_dump

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "generic_exotic_fx"
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

# Frame duration is authored content. Faster mechanical/sonic marks read as
# snap; smoke, growth, and ritual effects breathe longer.
ROWS: List[Tuple[str, int, int]] = [
    ("smoke_puff", 9, 58),
    ("smoke_column", 12, 74),
    ("steam_vent", 10, 58),
    ("poison_cloud", 12, 78),
    ("acid_sizzle", 9, 50),
    ("slime_splat", 8, 48),
    ("goo_bubble_pop", 8, 46),
    ("sonic_boom", 8, 38),
    ("sonic_ripple", 10, 44),
    ("psychic_pulse", 9, 48),
    ("confusion_swirl", 12, 72),
    ("rewind_echo", 10, 52),
    ("time_shatter", 9, 46),
    ("rune_circle", 12, 70),
    ("rune_burst", 9, 48),
    ("magic_seal_break", 10, 50),
    ("loot_burst", 9, 48),
    ("gear_scatter", 9, 42),
    ("vine_sprout", 11, 64),
    ("petal_burst", 10, 54),
    ("spore_puff", 11, 70),
    ("sand_burst", 9, 48),
    ("sand_whorl", 12, 70),
    ("shadow_wisp", 12, 76),
]

LOOPS = {
    "smoke_column",
    "poison_cloud",
    "confusion_swirl",
    "rune_circle",
    "sand_whorl",
    "shadow_wisp",
}

OUTLINE = (38, 30, 49, 255)
OUTLINE_SOFT = (61, 50, 73, 220)
WHITE = (255, 252, 239, 255)
CREAM = (255, 236, 184, 255)
SMOKE = (116, 111, 126, 255)
SMOKE_DARK = (74, 72, 86, 255)
STEAM = (219, 239, 240, 255)
LIME = (174, 225, 92, 255)
ACID = (206, 244, 74, 255)
SLIME = (94, 188, 105, 255)
SLIME_HI = (177, 232, 129, 255)
CYAN = (110, 222, 236, 255)
CYAN_HI = (219, 253, 255, 255)
BLUE = (86, 147, 218, 255)
VIOLET = (153, 105, 207, 255)
MAGENTA = (224, 111, 190, 255)
PINK = (246, 157, 197, 255)
GOLD = (250, 199, 77, 255)
ORANGE = (234, 135, 66, 255)
RED = (222, 79, 91, 255)
TEAL = (97, 190, 176, 255)
MINT = (159, 225, 172, 255)
GREEN = (72, 149, 88, 255)
LEAF = (95, 176, 86, 255)
PETAL = (245, 147, 174, 255)
PETAL_HI = (255, 209, 215, 255)
SAND = (209, 177, 114, 255)
SAND_HI = (247, 220, 160, 255)
SHADOW = (65, 53, 93, 255)
SHADOW_HI = (126, 89, 166, 255)
METAL = (151, 158, 170, 255)
METAL_HI = (217, 221, 226, 255)

ACTOR_METADATA = {
    "actor": {
        "character_id": "fx_generic_exotic_fx",
        "display_name": "Generic Exotic FX",
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


def _spec(
    family: str,
    intent: str,
    *,
    loop: bool = False,
    placement: str = "effect_origin",
    orientation: str = "radial",
    mirror_x: bool = False,
    rotate_safe: bool = True,
    blend: str = "alpha",
    layer: str = "over_world",
    attachment: str = "world_locked_after_spawn",
    tint: str = "preserve_palette_preferred",
    size: int = 100,
) -> dict:
    return {
        "family": family,
        "intent": intent,
        "loop": loop,
        "placement": placement,
        "orientation": orientation,
        "mirror_x": mirror_x,
        "rotate_safe": rotate_safe,
        "blend_mode_hint": blend,
        "layer_hint": layer,
        "attachment_hint": attachment,
        "tint_policy_hint": tint,
        "nominal_span_px": size,
    }


EFFECT_SPECS: Dict[str, dict] = {
    "smoke_puff": _spec(
        "smoke",
        "Single expanding cartoon smoke puff for destruction, footsteps, machinery, or obscured disappearance.",
        placement="surface_contact",
        orientation="surface_normal_or_world_up",
        mirror_x=True,
        attachment="world_locked_after_spawn",
        tint="safe_to_tint",
        size=100,
    ),
    "smoke_column": _spec(
        "smoke",
        "Continuous rising smoke stack for fires, damaged machines, vents, chimneys, or environmental ambience.",
        loop=True,
        placement="emitter_socket",
        orientation="gravity_up_or_emitter_up",
        mirror_x=True,
        attachment="follow_source",
        tint="safe_to_tint",
        size=92,
    ),
    "steam_vent": _spec(
        "vapor",
        "Forceful directional steam jet for vents, pressure releases, hot machinery, or cold breath-like vapor.",
        placement="emitter_socket",
        orientation="positive_x_is_forward",
        mirror_x=True,
        blend="alpha_or_additive",
        attachment="follow_source_optional",
        tint="safe_to_tint",
        size=106,
    ),
    "poison_cloud": _spec(
        "hazard_gas",
        "Breathing toxic cloud for poison status, hazardous rooms, spores, alchemy, or cartoon stink gas.",
        loop=True,
        placement="effect_origin",
        orientation="screen_or_world_aligned",
        rotate_safe=True,
        attachment="world_locked_after_spawn",
        tint="safe_to_tint",
        size=108,
    ),
    "acid_sizzle": _spec(
        "corrosive",
        "Surface-local fizz and popping droplets for acid contact, corrosion, hot chemistry, or dissolving matter.",
        placement="surface_contact",
        orientation="surface_normal",
        mirror_x=True,
        attachment="world_locked_after_spawn",
        tint="preserve_palette_preferred",
        size=92,
    ),
    "slime_splat": _spec(
        "goo",
        "Flattening wet splat for slime projectiles, goo impacts, paint-like hazards, or squishy enemies.",
        placement="surface_contact",
        orientation="surface_normal",
        mirror_x=True,
        attachment="world_locked_after_spawn",
        tint="safe_to_tint",
        size=106,
    ),
    "goo_bubble_pop": _spec(
        "goo",
        "Elastic bubble swell and pop for slime, potion vats, swamp ambience, goo creatures, or viscous projectiles.",
        placement="effect_origin",
        orientation="radial",
        attachment="follow_source_optional",
        tint="safe_to_tint",
        size=78,
    ),
    "sonic_boom": _spec(
        "sonic",
        "Directional compressed wavefront for loud attacks, supersonic motion, roars, cannons, or shock blasts.",
        placement="effect_origin",
        orientation="positive_x_is_forward",
        mirror_x=True,
        blend="alpha_or_additive",
        tint="safe_to_tint",
        size=116,
    ),
    "sonic_ripple": _spec(
        "sonic",
        "Concentric traveling wave rings for resonance, sonar, music attacks, bells, or environmental pulses.",
        placement="effect_origin",
        orientation="positive_x_is_forward",
        mirror_x=True,
        blend="alpha_or_additive",
        tint="safe_to_tint",
        size=112,
    ),
    "psychic_pulse": _spec(
        "psychic",
        "Radial mind-energy flare for telekinesis, psionics, awareness bursts, mind control, or occult pressure.",
        placement="entity_origin",
        orientation="radial",
        blend="alpha_or_additive",
        attachment="follow_source_optional",
        tint="safe_to_tint",
        size=108,
    ),
    "confusion_swirl": _spec(
        "status_negative",
        "Looping crooked orbit marks for confusion, drunkenness, hypnosis, disorientation, or cartoon daze.",
        loop=True,
        placement="feature_point",
        orientation="screen_or_world_aligned",
        attachment="follow_source",
        tint="safe_to_tint",
        size=86,
    ),
    "rewind_echo": _spec(
        "time",
        "Layered backward-moving echoes for rewind, undo, temporal recall, rollback, or time-step abilities.",
        placement="entity_origin",
        orientation="positive_x_is_forward",
        mirror_x=True,
        blend="alpha_or_additive",
        layer="behind_source",
        attachment="world_locked_after_spawn",
        tint="safe_to_tint",
        size=112,
    ),
    "time_shatter": _spec(
        "time",
        "Broken clock/radial glass motif for time stop ending, timeline fracture, paradox, or temporal impact.",
        placement="effect_origin",
        orientation="radial",
        blend="alpha_or_additive",
        tint="preserve_palette_preferred",
        size=112,
    ),
    "rune_circle": _spec(
        "ritual_magic",
        "Looping geometric seal for casting, summoning, wards, checkpoints, portals, or persistent magical fields.",
        loop=True,
        placement="effect_origin",
        orientation="screen_or_world_aligned",
        blend="alpha_or_additive",
        attachment="follow_source_optional",
        tint="safe_to_tint",
        size=104,
    ),
    "rune_burst": _spec(
        "ritual_magic",
        "Runic symbols thrown outward from a cast, spell completion, magical hit, or artifact activation.",
        placement="effect_origin",
        orientation="radial",
        blend="alpha_or_additive",
        tint="safe_to_tint",
        size=112,
    ),
    "magic_seal_break": _spec(
        "ritual_magic",
        "Cracking segmented seal for broken wards, dispels, lock removal, barrier failure, or cursed objects.",
        placement="effect_origin",
        orientation="radial",
        blend="alpha_or_additive",
        tint="safe_to_tint",
        size=114,
    ),
    "loot_burst": _spec(
        "reward",
        "Playful celebratory burst of stars, diamonds, and rays for loot, rare drops, rewards, or discoveries.",
        placement="feature_point",
        orientation="screen_or_world_aligned",
        blend="alpha_or_additive",
        tint="preserve_palette_preferred",
        size=108,
    ),
    "gear_scatter": _spec(
        "mechanical_debris",
        "Stylized gears, screws, and metal chips scattering from robotic impacts, machine breaks, or repairs.",
        placement="effect_origin",
        orientation="radial",
        attachment="world_locked_after_spawn",
        tint="preserve_palette_preferred",
        size=108,
    ),
    "vine_sprout": _spec(
        "nature_growth",
        "Fast curling plant growth for nature magic, healing flora, traps, environmental changes, or roots.",
        placement="surface_contact",
        orientation="surface_normal_or_gravity_up",
        mirror_x=True,
        attachment="world_locked_after_spawn",
        tint="preserve_palette_preferred",
        size=96,
    ),
    "petal_burst": _spec(
        "nature_particles",
        "Radial flower-petal flourish for nature magic, charming hits, healing, seasonal ambience, or celebration.",
        placement="effect_origin",
        orientation="radial",
        tint="preserve_palette_preferred",
        size=106,
    ),
    "spore_puff": _spec(
        "nature_particles",
        "Soft cloud plus drifting motes for mushrooms, pollen, spores, dusty plants, or magical forest ambience.",
        placement="surface_contact",
        orientation="gravity_up_or_surface_normal",
        mirror_x=True,
        attachment="world_locked_after_spawn",
        tint="safe_to_tint",
        size=100,
    ),
    "sand_burst": _spec(
        "granular",
        "Low sweeping sand eruption for impacts on dunes, burrowing, earth magic, dry debris, or desert movement.",
        placement="surface_contact",
        orientation="surface_normal",
        mirror_x=True,
        attachment="world_locked_after_spawn",
        tint="preserve_palette_preferred",
        size=108,
    ),
    "sand_whorl": _spec(
        "granular",
        "Looping miniature dust-devil spiral for desert ambience, wind magic, sand traps, or cursed dust.",
        loop=True,
        placement="effect_origin",
        orientation="gravity_up_or_world_up",
        mirror_x=True,
        attachment="world_locked_after_spawn",
        tint="safe_to_tint",
        size=92,
    ),
    "shadow_wisp": _spec(
        "shadow",
        "Looping soft dark flame/wisp for hauntings, curses, stealth, void energy, or shadowy environment dressing.",
        loop=True,
        placement="emitter_socket",
        orientation="gravity_up_or_emitter_up",
        mirror_x=True,
        blend="alpha_or_multiply",
        attachment="follow_source_optional",
        tint="safe_to_tint",
        size=78,
    ),
}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _smooth(x: float) -> float:
    x = _clamp(x)
    return x * x * (3.0 - 2.0 * x)


def _ease_out(x: float) -> float:
    x = _clamp(x)
    return 1.0 - (1.0 - x) ** 3


def _ease_in_out(x: float) -> float:
    x = _clamp(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _mul_alpha(c: RGBA, factor: float) -> RGBA:
    return (c[0], c[1], c[2], max(0, min(255, round(c[3] * factor))))


def _sc(v: float) -> int:
    return round(v * SUPER)


def _pt(p: Point) -> Tuple[int, int]:
    return (_sc(p[0]), _sc(p[1]))


def _ellipse(img: Image.Image, box: Sequence[float], *, fill: RGBA | None = None, outline: RGBA | None = None, width: float = 1.0) -> None:
    d = ImageDraw.Draw(img, "RGBA")
    b = tuple(_sc(x) for x in box)
    d.ellipse(b, fill=fill, outline=outline, width=max(1, _sc(width)))


def _arc(img: Image.Image, box: Sequence[float], start: float, end: float, *, fill: RGBA, width: float = 1.0) -> None:
    d = ImageDraw.Draw(img, "RGBA")
    d.arc(tuple(_sc(x) for x in box), start=start, end=end, fill=fill, width=max(1, _sc(width)))


def _line(img: Image.Image, points: Sequence[Point], *, fill: RGBA, width: float = 1.0, joint: str = "curve") -> None:
    d = ImageDraw.Draw(img, "RGBA")
    d.line([_pt(p) for p in points], fill=fill, width=max(1, _sc(width)), joint=joint)


def _polygon(img: Image.Image, points: Sequence[Point], *, fill: RGBA | None = None, outline: RGBA | None = None, width: float = 1.0) -> None:
    d = ImageDraw.Draw(img, "RGBA")
    pts = [_pt(p) for p in points]
    d.polygon(pts, fill=fill)
    if outline is not None:
        d.line(pts + [pts[0]], fill=outline, width=max(1, _sc(width)), joint="curve")


def _regular_polygon(cx: float, cy: float, radius: float, n: int, rotation: float = 0.0) -> List[Point]:
    return [
        (cx + math.cos(rotation + math.tau * i / n) * radius, cy + math.sin(rotation + math.tau * i / n) * radius)
        for i in range(n)
    ]


def _star_points(cx: float, cy: float, outer: float, inner: float, n: int, rotation: float = 0.0) -> List[Point]:
    pts: List[Point] = []
    for i in range(n * 2):
        r = outer if i % 2 == 0 else inner
        a = rotation + math.pi * i / n
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def _diamond(cx: float, cy: float, rx: float, ry: float, rotation: float = 0.0) -> List[Point]:
    pts = [(0.0, -ry), (rx, 0.0), (0.0, ry), (-rx, 0.0)]
    c, s = math.cos(rotation), math.sin(rotation)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def _rotated_rect(cx: float, cy: float, half_w: float, half_h: float, rotation: float) -> List[Point]:
    c, s = math.cos(rotation), math.sin(rotation)
    pts = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def _bubble(img: Image.Image, x: float, y: float, r: float, color: RGBA, alpha: float = 1.0) -> None:
    _ellipse(img, (x - r, y - r, x + r, y + r), fill=_mul_alpha(color, 0.78 * alpha), outline=_mul_alpha(OUTLINE_SOFT, 0.72 * alpha), width=1.2)
    _ellipse(img, (x - r * 0.42, y - r * 0.48, x - r * 0.05, y - r * 0.10), fill=_mul_alpha(WHITE, 0.48 * alpha))


def _cloud_blob(img: Image.Image, lobes: Sequence[Tuple[float, float, float]], color: RGBA, alpha: float = 1.0) -> None:
    for x, y, r in lobes:
        _ellipse(img, (x - r, y - r, x + r, y + r), fill=_mul_alpha(color, 0.78 * alpha), outline=_mul_alpha(OUTLINE_SOFT, 0.42 * alpha), width=0.9)


def _draw_smoke_puff(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.55) / 0.45))
    cx, base = 64.0, 84.0
    lobes = []
    for i in range(8):
        a = math.pi + math.tau * (i + 0.5) / 8.0
        rr = _lerp(6.0, 27.0 + (i % 3) * 3.0, q)
        x = cx + math.cos(a) * rr
        y = base + math.sin(a) * rr * 0.68 - 13.0 * q
        r = _lerp(7.0, 13.0 + (i % 2) * 2.0, q)
        lobes.append((x, y, r))
    _cloud_blob(img, lobes, SMOKE, fade)
    _cloud_blob(img, [(55, 70 - 12 * q, 9 + 5 * q), (72, 68 - 14 * q, 10 + 5 * q)], (143, 137, 151, 255), 0.62 * fade)
    _ellipse(img, (35 - 9 * q, 87 - 3 * q, 93 + 9 * q, 94 + 4 * q), fill=_mul_alpha(SMOKE_DARK, 0.36 * fade))


def _draw_smoke_column(img: Image.Image, p: float) -> None:
    phase = math.tau * p
    for i in range(7):
        f = (p + i / 7.0) % 1.0
        y = 104.0 - 82.0 * f
        sway = math.sin(phase * 1.5 + i * 1.9) * (3.0 + 7.0 * f)
        x = 64.0 + sway
        r = 6.0 + 10.0 * f
        alpha = math.sin(math.pi * f) ** 0.65
        color = SMOKE if i % 2 else (137, 131, 146, 255)
        _bubble(img, x, y, r, color, 0.68 * alpha)
    _ellipse(img, (53, 98, 75, 108), fill=_mul_alpha(SMOKE_DARK, 0.32))


def _draw_steam_vent(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.58) / 0.42))
    ox, oy = 18.0, 64.0
    _ellipse(img, (ox - 7, oy - 8, ox + 7, oy + 8), fill=_mul_alpha(CYAN_HI, 0.76 * fade), outline=_mul_alpha(BLUE, 0.44 * fade), width=1.0)
    for i in range(6):
        t = (i + 1) / 6.0
        x = ox + _lerp(10.0, 91.0, q * t)
        y = oy + math.sin(i * 2.2 + p * 7.0) * (3.0 + 5.0 * t)
        r = _lerp(4.0, 11.0, t) * (0.65 + 0.35 * q)
        _bubble(img, x, y, r, STEAM if i % 2 else CYAN_HI, fade * (0.86 - 0.25 * t))
    _line(img, [(22, 55), (78 + 24 * q, 50)], fill=_mul_alpha(WHITE, 0.32 * fade), width=1.2)
    _line(img, [(22, 73), (82 + 18 * q, 77)], fill=_mul_alpha(CYAN, 0.28 * fade), width=1.0)


def _draw_poison_cloud(img: Image.Image, p: float) -> None:
    phase = math.tau * p
    lobes = []
    for i in range(9):
        a = math.tau * i / 9.0 + 0.13 * math.sin(phase + i)
        r0 = 26.0 + 6.0 * math.sin(phase * 1.3 + i * 1.7)
        x = 64 + math.cos(a) * r0
        y = 67 + math.sin(a) * r0 * 0.64
        rr = 12.0 + 3.5 * math.sin(phase * 1.9 + i)
        lobes.append((x, y, rr))
    _cloud_blob(img, lobes, SLIME, 0.76)
    _cloud_blob(img, [(58, 61, 18), (75, 65, 16)], (126, 199, 91, 255), 0.58)
    for i in range(5):
        a = phase * (0.35 if i % 2 else -0.28) + i * 1.4
        x = 64 + math.cos(a) * (18 + i * 4)
        y = 60 + math.sin(a) * (10 + i * 2)
        _ellipse(img, (x - 2.2, y - 2.2, x + 2.2, y + 2.2), fill=_mul_alpha(ACID, 0.76))


def _draw_acid_sizzle(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.62) / 0.38))
    y0 = 86.0
    _ellipse(img, (28 - 5 * q, y0 - 5, 100 + 5 * q, y0 + 5), fill=_mul_alpha(SLIME, 0.62 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.45 * fade), width=0.8)
    for i in range(7):
        x = 35 + i * 10 + math.sin(i * 2.1) * 3
        rise = (8 + (i % 3) * 8) * math.sin(math.pi * _clamp(p * 1.35 - i * 0.035))
        r = 2.5 + (i % 2) * 1.4
        _bubble(img, x + (i - 3) * q * 1.5, y0 - 3 - rise, r, ACID if i % 2 else SLIME_HI, fade)
    for i in range(5):
        x = 42 + i * 12
        _line(img, [(x, y0 - 4), (x + math.sin(i) * 3, y0 - 11 - 8 * q)], fill=_mul_alpha(ACID, 0.48 * fade), width=1.0)


def _draw_slime_splat(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.66) / 0.34))
    cx, cy = 64.0, 84.0
    rx = _lerp(10.0, 43.0, q)
    ry = _lerp(16.0, 8.0, q)
    _ellipse(img, (cx - rx, cy - ry, cx + rx, cy + ry), fill=_mul_alpha(SLIME, 0.88 * fade), outline=_mul_alpha(OUTLINE, 0.66 * fade), width=1.0)
    for i in range(7):
        a = math.pi + math.pi * i / 6.0
        length = _lerp(5.0, 19.0 + (i % 3) * 5.0, q)
        tipx = cx + math.cos(a) * (rx + length)
        tipy = cy + math.sin(a) * (ry + length * 0.42)
        _polygon(img, [(cx + math.cos(a - 0.12) * rx, cy + math.sin(a - 0.12) * ry), (tipx, tipy), (cx + math.cos(a + 0.12) * rx, cy + math.sin(a + 0.12) * ry)], fill=_mul_alpha(SLIME_HI, 0.72 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.5 * fade), width=0.8)
    _ellipse(img, (49, 79, 60, 84), fill=_mul_alpha(WHITE, 0.28 * fade))


def _draw_goo_bubble_pop(img: Image.Image, p: float) -> None:
    if p < 0.50:
        q = _smooth(p / 0.50)
        r = _lerp(10.0, 27.0, q)
        _bubble(img, 64, 68, r, SLIME_HI, 0.95)
        _ellipse(img, (58 - r * 0.18, 61 - r * 0.22, 62, 65), fill=_mul_alpha(WHITE, 0.56))
    else:
        q = _ease_out((p - 0.50) / 0.50)
        fade = 1.0 - _smooth(q)
        for i in range(9):
            a = math.tau * i / 9.0
            rr = _lerp(22.0, 48.0 + (i % 3) * 3, q)
            x, y = 64 + math.cos(a) * rr, 68 + math.sin(a) * rr
            r = 3.5 + (i % 2) * 1.4
            _ellipse(img, (x - r, y - r, x + r, y + r), fill=_mul_alpha(SLIME_HI if i % 2 else ACID, 0.82 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.42 * fade), width=0.7)
        _arc(img, (41, 45, 87, 91), 210, 330, fill=_mul_alpha(SLIME, 0.64 * fade), width=2.2)


def _draw_sonic_boom(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.52) / 0.48))
    ox, oy = 22.0, 64.0
    for i, scale in enumerate((0.58, 0.78, 1.0)):
        x = _lerp(30.0, 100.0 * scale, q)
        h = _lerp(8.0, 34.0 * scale, q)
        _arc(img, (x - 12, oy - h, x + 12, oy + h), 270, 90, fill=_mul_alpha(CYAN_HI if i == 2 else CYAN, (0.82 - i * 0.12) * fade), width=2.5 - i * 0.4)
    _polygon(img, [(ox, oy), (37 + 18 * q, oy - 6), (37 + 18 * q, oy + 6)], fill=_mul_alpha(WHITE, 0.78 * fade), outline=_mul_alpha(BLUE, 0.56 * fade), width=0.8)
    _line(img, [(28, 48), (61 + 22 * q, 43)], fill=_mul_alpha(CYAN, 0.40 * fade), width=1.2)
    _line(img, [(28, 80), (61 + 22 * q, 85)], fill=_mul_alpha(CYAN, 0.40 * fade), width=1.2)


def _draw_sonic_ripple(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.62) / 0.38))
    ox, oy = 18.0, 64.0
    for i in range(5):
        local = _clamp(q * 1.35 - i * 0.12)
        x = ox + 18 + local * (78 + i * 3)
        h = 9 + local * (12 + i * 3)
        alpha = fade * (0.78 - i * 0.10)
        _arc(img, (x - 9, oy - h, x + 9, oy + h), 270, 90, fill=_mul_alpha(CYAN_HI if i % 2 == 0 else BLUE, alpha), width=1.8)
    _ellipse(img, (ox - 3, oy - 3, ox + 3, oy + 3), fill=_mul_alpha(WHITE, 0.88 * fade))


def _draw_psychic_pulse(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.58) / 0.42))
    cx, cy = 64.0, 64.0
    r = _lerp(10.0, 49.0, q)
    _ellipse(img, (cx - r, cy - r, cx + r, cy + r), outline=_mul_alpha(MAGENTA, 0.72 * fade), width=2.2)
    r2 = r * 0.66
    _ellipse(img, (cx - r2, cy - r2, cx + r2, cy + r2), outline=_mul_alpha(VIOLET, 0.58 * fade), width=1.6)
    for i in range(8):
        a = math.tau * i / 8.0 + p * 0.55
        rr = r * (0.45 + 0.16 * (i % 2))
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        _polygon(img, _diamond(x, y, 2.2, 5.2, a), fill=_mul_alpha(PINK, 0.78 * fade))
    _polygon(img, _star_points(cx, cy, 12 + 5 * (1 - q), 5, 7, rotation=p), fill=_mul_alpha(WHITE, 0.74 * fade), outline=_mul_alpha(MAGENTA, 0.58 * fade), width=0.9)


def _draw_confusion_swirl(img: Image.Image, p: float) -> None:
    phase = math.tau * p
    cx, cy = 64.0, 62.0
    # Crooked double spiral.
    pts1: List[Point] = []
    pts2: List[Point] = []
    for j in range(28):
        t = j / 27.0
        a = phase + t * math.tau * 1.6
        r = 8 + 33 * t
        wobble = math.sin(a * 2.5) * 2.2
        pts1.append((cx + math.cos(a) * (r + wobble), cy + math.sin(a) * (r * 0.62)))
        pts2.append((cx + math.cos(a + math.pi) * (r * 0.72), cy + math.sin(a + math.pi) * (r * 0.48)))
    _line(img, pts1, fill=_mul_alpha(MAGENTA, 0.86), width=2.1)
    _line(img, pts2, fill=_mul_alpha(CYAN, 0.72), width=1.6)
    for i in range(4):
        a = phase * (-0.7 if i % 2 else 0.9) + i * 1.5
        x, y = cx + math.cos(a) * (30 + i * 4), cy + math.sin(a) * (17 + i * 2)
        _polygon(img, _star_points(x, y, 5.5, 2.2, 4, rotation=a), fill=GOLD if i % 2 else PINK, outline=OUTLINE_SOFT, width=0.7)


def _draw_rewind_echo(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.66) / 0.34))
    # Three chevron/time echoes moving backward (left).
    for i in range(4):
        local = _clamp(q * 1.25 - i * 0.11)
        x = 93 - local * (24 + i * 11)
        alpha = (0.86 - i * 0.15) * fade
        pts = [(x + 9, 45), (x - 8, 64), (x + 9, 83)]
        _line(img, pts, fill=_mul_alpha(CYAN_HI if i == 0 else VIOLET, alpha), width=3.0 - i * 0.35)
    r = _lerp(9.0, 31.0, q)
    _arc(img, (64 - r, 64 - r, 64 + r, 64 + r), 35, 305, fill=_mul_alpha(MAGENTA, 0.62 * fade), width=1.7)
    # Backward arrow head on ring.
    _polygon(img, [(38 - 4 * q, 52), (27 - 6 * q, 58), (38 - 2 * q, 63)], fill=_mul_alpha(CYAN, 0.72 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.44 * fade), width=0.7)


def _draw_time_shatter(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.58) / 0.42))
    cx, cy = 64.0, 64.0
    r = _lerp(18.0, 40.0, q)
    _ellipse(img, (cx - r, cy - r, cx + r, cy + r), outline=_mul_alpha(GOLD, 0.60 * fade), width=1.4)
    # Clock ticks become radial cracks.
    for i in range(12):
        a = -math.pi / 2 + math.tau * i / 12
        r0 = r * 0.72
        r1 = r * (0.92 + 0.22 * q * (i % 3 == 0))
        bend = 0.10 * ((i % 3) - 1)
        pts = [
            (cx + math.cos(a) * r0, cy + math.sin(a) * r0),
            (cx + math.cos(a + bend) * (r0 + r1) * 0.52, cy + math.sin(a + bend) * (r0 + r1) * 0.52),
            (cx + math.cos(a) * r1, cy + math.sin(a) * r1),
        ]
        _line(img, pts, fill=_mul_alpha(CYAN_HI if i % 4 else MAGENTA, 0.68 * fade), width=1.1)
    hand_len = r * 0.57
    _line(img, [(cx, cy), (cx + math.cos(-1.4 - p * 2.4) * hand_len, cy + math.sin(-1.4 - p * 2.4) * hand_len)], fill=_mul_alpha(WHITE, 0.78 * fade), width=1.7)
    _line(img, [(cx, cy), (cx + math.cos(0.35 + p * 4.2) * hand_len * 0.7, cy + math.sin(0.35 + p * 4.2) * hand_len * 0.7)], fill=_mul_alpha(GOLD, 0.78 * fade), width=1.7)
    _ellipse(img, (59, 59, 69, 69), fill=_mul_alpha(WHITE, 0.75 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.4 * fade), width=0.8)


def _draw_rune_circle(img: Image.Image, p: float) -> None:
    phase = math.tau * p
    cx, cy = 64.0, 64.0
    for r, color, alpha in ((43, VIOLET, 0.72), (33, CYAN, 0.56), (21, MAGENTA, 0.46)):
        _ellipse(img, (cx - r, cy - r, cx + r, cy + r), outline=_mul_alpha(color, alpha), width=1.4)
    # Counter-rotating polygons and small rune ticks.
    _polygon(img, _regular_polygon(cx, cy, 36, 6, phase * 0.28), outline=_mul_alpha(CYAN_HI, 0.68), width=1.1)
    _polygon(img, _regular_polygon(cx, cy, 25, 3, -phase * 0.34 + math.pi / 2), outline=_mul_alpha(MAGENTA, 0.70), width=1.2)
    for i in range(12):
        a = phase * (0.23 if i % 2 else -0.19) + math.tau * i / 12
        r = 47
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        tangent = a + math.pi / 2
        _line(img, [(x - math.cos(tangent) * 3, y - math.sin(tangent) * 3), (x + math.cos(tangent) * 3, y + math.sin(tangent) * 3)], fill=_mul_alpha(GOLD if i % 3 == 0 else WHITE, 0.70), width=1.0)
    pulse = 4 + 2 * (0.5 + 0.5 * math.sin(phase * 2))
    _polygon(img, _star_points(cx, cy, pulse * 2.1, pulse, 6, rotation=-phase * 0.2), fill=_mul_alpha(WHITE, 0.56), outline=_mul_alpha(VIOLET, 0.62), width=0.8)


def _draw_rune_burst(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.56) / 0.44))
    cx, cy = 64.0, 64.0
    for i in range(8):
        a = math.tau * i / 8.0 + 0.16
        rr = _lerp(12.0, 45.0 + (i % 2) * 6.0, q)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        rot = a + p * (0.7 if i % 2 else -0.9)
        if i % 3 == 0:
            pts = _regular_polygon(x, y, 5.5, 3, rot)
        elif i % 3 == 1:
            pts = _diamond(x, y, 4.0, 7.0, rot)
        else:
            pts = _star_points(x, y, 5.5, 2.2, 4, rot)
        _polygon(img, pts, fill=_mul_alpha(CYAN if i % 2 else MAGENTA, 0.74 * fade), outline=_mul_alpha(WHITE, 0.52 * fade), width=0.7)
    r = _lerp(9.0, 31.0, q)
    _ellipse(img, (cx - r, cy - r, cx + r, cy + r), outline=_mul_alpha(VIOLET, 0.52 * fade), width=1.2)


def _draw_magic_seal_break(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.64) / 0.36))
    cx, cy = 64.0, 64.0
    r = 39.0 + 5.0 * q
    # Broken ring segments separate outward.
    for i in range(8):
        a0 = i * 45 + 5 + q * (i % 2) * 2
        a1 = a0 + 31
        off_a = math.radians((a0 + a1) / 2)
        off = 9.0 * q
        xoff, yoff = math.cos(off_a) * off, math.sin(off_a) * off
        _arc(img, (cx - r + xoff, cy - r + yoff, cx + r + xoff, cy + r + yoff), a0, a1, fill=_mul_alpha(MAGENTA if i % 2 else CYAN_HI, 0.76 * fade), width=2.2)
    for i in range(6):
        a = 0.4 + math.tau * i / 6.0
        rr = _lerp(12.0, 46.0, q)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        _polygon(img, _diamond(x, y, 2.8, 7.0, a), fill=_mul_alpha(WHITE, 0.66 * fade), outline=_mul_alpha(VIOLET, 0.5 * fade), width=0.6)
    _polygon(img, _regular_polygon(cx, cy, _lerp(28.0, 18.0, q), 5, p), outline=_mul_alpha(VIOLET, 0.38 * fade), width=1.0)


def _draw_loot_burst(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.60) / 0.40))
    cx, cy = 64.0, 66.0
    for i in range(10):
        a = -math.pi * 0.92 + math.pi * 1.84 * i / 9.0
        rr = _lerp(8.0, 34.0 + (i % 3) * 8.0, q)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        if i % 3 == 0:
            pts = _star_points(x, y, 6.0, 2.5, 4, rotation=a)
            col = GOLD
        elif i % 3 == 1:
            pts = _diamond(x, y, 4.0, 6.0, a)
            col = CYAN_HI
        else:
            pts = _regular_polygon(x, y, 4.5, 5, a)
            col = PINK
        _polygon(img, pts, fill=_mul_alpha(col, 0.86 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.52 * fade), width=0.7)
    for i in range(7):
        a = math.tau * i / 7.0
        r0 = _lerp(9, 21, q)
        r1 = _lerp(15, 44, q)
        _line(img, [(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], fill=_mul_alpha(WHITE, 0.50 * fade), width=1.1)
    _polygon(img, _star_points(cx, cy, _lerp(15, 9, q), 5, 8, rotation=p), fill=_mul_alpha(CREAM, 0.76 * fade), outline=_mul_alpha(GOLD, 0.70 * fade), width=0.9)


def _gear_points(cx: float, cy: float, r0: float, r1: float, teeth: int, rotation: float) -> List[Point]:
    pts: List[Point] = []
    for i in range(teeth * 4):
        a = rotation + math.tau * i / (teeth * 4)
        r = r1 if i % 4 in (1, 2) else r0
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def _draw_gear_scatter(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.64) / 0.36))
    cx, cy = 64.0, 64.0
    for i in range(5):
        a = 0.35 + math.tau * i / 5.0
        rr = _lerp(5.0, 34.0 + i * 3.0, q)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        r = 7.5 - i * 0.6
        pts = _gear_points(x, y, r * 0.78, r, 7, p * (3.0 if i % 2 else -2.5) + i)
        _polygon(img, pts, fill=_mul_alpha(METAL if i % 2 else METAL_HI, 0.82 * fade), outline=_mul_alpha(OUTLINE, 0.66 * fade), width=0.8)
        _ellipse(img, (x - r * 0.28, y - r * 0.28, x + r * 0.28, y + r * 0.28), fill=_mul_alpha(OUTLINE_SOFT, 0.62 * fade))
    for i in range(5):
        a = 1.0 + i * 1.17
        rr = _lerp(10.0, 48.0, q)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        _polygon(img, _rotated_rect(x, y, 2.0, 6.0, a + p * 4), fill=_mul_alpha(ORANGE if i % 2 else METAL_HI, 0.72 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.44 * fade), width=0.6)


def _draw_vine_sprout(img: Image.Image, p: float) -> None:
    q = _ease_in_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.82) / 0.18))
    base = (64.0, 103.0)
    # Curving stem grows from ground to top.
    points: List[Point] = []
    segments = 18
    for i in range(segments + 1):
        t = i / segments
        if t > q:
            break
        y = base[1] - t * 74.0
        x = base[0] + math.sin(t * math.pi * 2.1) * (8.0 + 4.0 * t)
        points.append((x, y))
    if len(points) >= 2:
        _line(img, points, fill=_mul_alpha(GREEN, 0.92 * fade), width=3.0)
        _line(img, [(x - 1.2, y) for x, y in points], fill=_mul_alpha(MINT, 0.58 * fade), width=1.0)
    # Leaves appear as the growth front passes them.
    for i, t in enumerate((0.28, 0.45, 0.62, 0.78)):
        appear = _smooth((q - t) / 0.13)
        if appear <= 0:
            continue
        y = base[1] - t * 74.0
        x = base[0] + math.sin(t * math.pi * 2.1) * (8.0 + 4.0 * t)
        side = -1 if i % 2 else 1
        a = -0.55 * side
        tip = (x + side * 18 * appear, y - 8 * appear)
        _polygon(img, [(x, y), (x + side * 7 * appear, y - 7 * appear), tip, (x + side * 6 * appear, y + 3 * appear)], fill=_mul_alpha(LEAF if i % 2 else MINT, 0.86 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.52 * fade), width=0.7)
        _line(img, [(x, y), tip], fill=_mul_alpha(GREEN, 0.62 * fade), width=0.7)
    _ellipse(img, (42, 101, 86, 108), fill=_mul_alpha((74, 91, 54, 255), 0.38 * fade))


def _petal_points(cx: float, cy: float, length: float, width: float, rotation: float) -> List[Point]:
    c, s = math.cos(rotation), math.sin(rotation)
    raw = [(0, -length * 0.52), (width, -length * 0.05), (0, length * 0.52), (-width, -length * 0.05)]
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in raw]


def _draw_petal_burst(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.60) / 0.40))
    cx, cy = 64.0, 64.0
    for i in range(12):
        a = -math.pi / 2 + math.tau * i / 12.0 + 0.18 * math.sin(i)
        rr = _lerp(7.0, 34.0 + (i % 4) * 4.0, q)
        x = cx + math.cos(a) * rr
        y = cy + math.sin(a) * rr + 8.0 * q * q
        rot = a + math.pi / 2 + p * (1.4 if i % 2 else -1.0)
        _polygon(img, _petal_points(x, y, 10 - (i % 3), 4.6, rot), fill=_mul_alpha(PETAL_HI if i % 3 == 0 else PETAL, 0.84 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.40 * fade), width=0.6)
    _ellipse(img, (56, 56, 72, 72), fill=_mul_alpha(GOLD, 0.62 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.44 * fade), width=0.7)


def _draw_spore_puff(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.62) / 0.38))
    cx, cy = 64.0, 83.0
    lobes = []
    for i in range(7):
        a = math.pi + math.pi * i / 6.0
        rr = _lerp(6.0, 26.0, q)
        x = cx + math.cos(a) * rr
        y = cy + math.sin(a) * rr * 0.65 - 12 * q
        lobes.append((x, y, 8 + 5 * q + (i % 2) * 2))
    _cloud_blob(img, lobes, (148, 185, 111, 255), 0.56 * fade)
    for i in range(14):
        a = i * 2.17 + p * (0.8 if i % 2 else -0.6)
        rr = _lerp(8.0, 22.0 + (i % 5) * 6.0, q)
        x = cx + math.cos(a) * rr
        y = cy - 9 * q + math.sin(a) * rr * 0.72 - q * (i % 4) * 3
        r = 1.7 + (i % 3) * 0.7
        _ellipse(img, (x - r, y - r, x + r, y + r), fill=_mul_alpha(CREAM if i % 3 else MINT, 0.78 * fade))


def _draw_sand_burst(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.63) / 0.37))
    cx, base = 64.0, 91.0
    # Low fan wedges.
    for i in range(9):
        a = math.pi + math.pi * i / 8.0
        rr = _lerp(4.0, 24.0 + (i % 3) * 8.0, q)
        x = cx + math.cos(a) * rr
        y = base + math.sin(a) * rr * 0.55
        _polygon(img, [(cx, base), (x - 4, y + 2), (x, y - 7 - (i % 3) * 2), (x + 4, y + 2)], fill=_mul_alpha(SAND if i % 2 else SAND_HI, 0.54 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.28 * fade), width=0.6)
    for i in range(16):
        a = math.pi * (1.06 + 0.88 * (i / 15.0))
        rr = _lerp(6.0, 31.0 + (i % 4) * 5.0, q)
        x = cx + math.cos(a) * rr
        y = base + math.sin(a) * rr * 0.62
        r = 1.4 + (i % 3) * 0.55
        _ellipse(img, (x - r, y - r, x + r, y + r), fill=_mul_alpha(GOLD if i % 4 == 0 else SAND_HI, 0.76 * fade))
    _ellipse(img, (25 - 5 * q, 90, 103 + 5 * q, 98), fill=_mul_alpha(SAND, 0.35 * fade))


def _draw_sand_whorl(img: Image.Image, p: float) -> None:
    phase = math.tau * p
    cx, base = 64.0, 96.0
    # Three nested spiral traces with dots.
    for band in range(3):
        pts: List[Point] = []
        for j in range(28):
            t = j / 27.0
            a = phase * (1.0 + band * 0.18) + t * math.tau * (1.35 + band * 0.2)
            r = 8 + 19 * t + band * 2
            x = cx + math.cos(a) * r
            y = base - t * 66 + math.sin(a) * r * 0.28
            pts.append((x, y))
        _line(img, pts, fill=_mul_alpha(SAND_HI if band == 0 else SAND, 0.58 - band * 0.10), width=1.4 - band * 0.2)
    for i in range(12):
        f = (p + i / 12.0) % 1.0
        a = phase * 1.1 + i * 1.83
        r = 10 + 22 * f
        x = cx + math.cos(a) * r
        y = base - f * 68 + math.sin(a) * r * 0.25
        _ellipse(img, (x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=_mul_alpha(GOLD if i % 4 == 0 else SAND_HI, 0.72))


def _draw_shadow_wisp(img: Image.Image, p: float) -> None:
    phase = math.tau * p
    cx, base = 64.0, 96.0
    # Layered dark flame body with wandering tip.
    tipx = cx + math.sin(phase * 1.2) * 12
    tipy = 30 + math.cos(phase * 1.7) * 5
    left = [(cx - 16, base), (cx - 22, 80), (cx - 14, 62), (cx - 9 + math.sin(phase) * 5, 49), (tipx, tipy)]
    right = [(tipx, tipy), (cx + 10 + math.cos(phase * 1.3) * 5, 50), (cx + 15, 66), (cx + 21, 82), (cx + 16, base)]
    _polygon(img, left + right[1:], fill=_mul_alpha(SHADOW, 0.84), outline=_mul_alpha(OUTLINE, 0.78), width=1.2)
    inner_tip = (cx + math.sin(phase * 1.6 + 1) * 6, 49 + math.cos(phase) * 3)
    _polygon(img, [(cx - 10, 92), (cx - 12, 72), inner_tip, (cx + 10, 72), (cx + 9, 92)], fill=_mul_alpha(SHADOW_HI, 0.58), outline=_mul_alpha(VIOLET, 0.34), width=0.8)
    for i in range(4):
        a = phase * (0.45 if i % 2 else -0.5) + i * 1.6
        rr = 25 + i * 5
        x = cx + math.cos(a) * rr
        y = 67 + math.sin(a) * rr * 0.55
        _ellipse(img, (x - 2.2, y - 2.2, x + 2.2, y + 2.2), fill=_mul_alpha(SHADOW_HI, 0.58))


DRAWERS = {
    "smoke_puff": _draw_smoke_puff,
    "smoke_column": _draw_smoke_column,
    "steam_vent": _draw_steam_vent,
    "poison_cloud": _draw_poison_cloud,
    "acid_sizzle": _draw_acid_sizzle,
    "slime_splat": _draw_slime_splat,
    "goo_bubble_pop": _draw_goo_bubble_pop,
    "sonic_boom": _draw_sonic_boom,
    "sonic_ripple": _draw_sonic_ripple,
    "psychic_pulse": _draw_psychic_pulse,
    "confusion_swirl": _draw_confusion_swirl,
    "rewind_echo": _draw_rewind_echo,
    "time_shatter": _draw_time_shatter,
    "rune_circle": _draw_rune_circle,
    "rune_burst": _draw_rune_burst,
    "magic_seal_break": _draw_magic_seal_break,
    "loot_burst": _draw_loot_burst,
    "gear_scatter": _draw_gear_scatter,
    "vine_sprout": _draw_vine_sprout,
    "petal_burst": _draw_petal_burst,
    "spore_puff": _draw_spore_puff,
    "sand_burst": _draw_sand_burst,
    "sand_whorl": _draw_sand_whorl,
    "shadow_wisp": _draw_shadow_wisp,
}


def _origin_for(anim: str) -> Point:
    if anim in {"smoke_puff", "acid_sizzle", "slime_splat", "vine_sprout", "spore_puff", "sand_burst"}:
        return (64.0, 96.0)
    if anim in {"smoke_column", "shadow_wisp"}:
        return (64.0, 104.0)
    if anim == "steam_vent":
        return (18.0, 64.0)
    if anim in {"sonic_boom", "sonic_ripple"}:
        return (18.0, 64.0)
    return (64.0, 64.0)


def _frame_progress(anim: str, frame_idx: int, nframes: int) -> float:
    if anim in LOOPS:
        return frame_idx / max(1, nframes)
    return frame_idx / max(1, nframes - 1)


def _phase(anim: str, p: float) -> str:
    if anim in LOOPS:
        return "loop"
    if anim in {"goo_bubble_pop"}:
        return "swell" if p < 0.5 else "pop"
    if anim in {"vine_sprout"}:
        return "grow" if p < 0.78 else "settle"
    if anim in {"time_shatter", "magic_seal_break"}:
        return "fracture" if p < 0.58 else "scatter"
    if anim in {"smoke_puff", "spore_puff", "sand_burst", "slime_splat"}:
        if p < 0.28:
            return "form"
        if p < 0.66:
            return "spread"
        return "dissipate"
    if p < 0.2:
        return "onset"
    if p < 0.62:
        return "follow_through"
    return "dissipate"


def _intensity(anim: str, p: float) -> float:
    if anim in LOOPS:
        return round(0.72 + 0.16 * (0.5 + 0.5 * math.sin(math.tau * p)), 4)
    if anim in {"goo_bubble_pop", "time_shatter", "magic_seal_break"}:
        return round(min(1.0, 0.4 + 0.8 * math.sin(math.pi * _clamp(p))), 4)
    if anim == "vine_sprout":
        return round(math.sin(math.pi * _clamp(p)) ** 0.55, 4)
    return round(1.0 - 0.70 * _smooth(p), 4)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    p = _frame_progress(anim, frame_idx, nframes)
    if anim not in LOOPS and frame_idx == nframes - 1:
        return Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    try:
        DRAWERS[anim](img, p)
    except KeyError as exc:
        raise ValueError(f"unknown animation: {anim}") from exc
    return img.resize(FRAME_SIZE, Image.Resampling.NEAREST)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    p = _frame_progress(anim, frame_idx, nframes)
    ox, oy = _origin_for(anim)
    anchors = {"origin": {"x": ox, "y": oy}}
    placement = EFFECT_SPECS[anim]["placement"]
    if placement in {"surface_contact", "feature_point"}:
        anchors["contact"] = {"x": ox, "y": oy}
    if placement == "emitter_socket":
        anchors["emitter"] = {"x": ox, "y": oy}
    return {
        "anchors": anchors,
        "effect": {
            "family": EFFECT_SPECS[anim]["family"],
            "phase": _phase(anim, p),
            "progress": round(p, 4),
            "intensity_hint": _intensity(anim, p),
            "clear_frame": bool(anim not in LOOPS and frame_idx == nframes - 1),
        },
    }


def _frame_notes(anim: str, nframes: int) -> List[dict]:
    return [
        {
            "frame": i,
            "phase": _phase(anim, _frame_progress(anim, i, nframes)),
            "progress": round(_frame_progress(anim, i, nframes), 4),
            "intensity_hint": _intensity(anim, _frame_progress(anim, i, nframes)),
            "clear_frame": bool(anim not in LOOPS and i == nframes - 1),
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
            "completion_hint": "loop_until_cancelled" if spec["loop"] else "despawn_after_clear_frame",
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
            "loop/completion intent",
            "direction/orientation and transform safety",
            "mirror allowance",
            "visual phase and relative intensity",
            "suggested compositing family",
            "suggested source attachment and draw layer",
            "tintability intent",
            "nominal authored visual span",
        ],
        "runtime_promotion_notes": [
            "The current SheetRecord RON preserves frame anchors but not the arbitrary frame effect payload.",
            "Treat row timing and anchors as authoritative immediately; do not recover pivots from alpha bounds.",
            "Promote loop, orientation, attachment, layer, tint, and completion only as generic presentation fields shared by many effect catalogs; do not special-case these animation names.",
            "Directional rows author +X as forward. Rotate or mirror the complete sprite around origin rather than modifying packed rectangles.",
            "Surface rows author a contact anchor. Surface normal/gravity-relative orientation belongs to presentation transforms, not authored pixel duplication.",
            "Loop rows are periodic and contain no clear terminal frame. One-shots deliberately end clear and may be despawned after that frame.",
            "Emitter anchors describe where an attached looping effect is rooted. They do not imply simulation ownership or a special particle system.",
            "blend_mode_hint includes alpha_or_multiply for shadow content as an aspiration; ordinary alpha is the authored fallback if multiply composition is unavailable.",
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
