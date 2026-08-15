"""Hand-authored procedural sprite sheet for reusable world/motion VFX.

This is a second generic VFX vocabulary alongside ``generic_action_fx``.  The
first sheet concentrates on impacts, dust, poofs, glints, and charge/release
punctuation; this sheet deliberately covers different visual grammars:

* motion streaks and wind marks,
* defensive/shield feedback,
* status and recovery cues,
* teleport/phase distortion,
* water and ambient environmental accents,
* elemental electricity/ice.

The target is content only. Runtime integration remains outside the sprite
renderer. Existing sheet metadata carries authoritative frame timing and
placement anchors today. Richer effect semantics are emitted in the companion
``*_authoring.yaml`` as author-owned guidance for a future generic VFX runtime
schema rather than requiring integration code to reverse-engineer pixels.

One-shot rows end on a fully transparent frame. Explicit loops are sampled as
periodic functions over [0, 1), so frame N-1 -> frame 0 remains continuous.
Directional rows author +X as forward and are safe to rotate around ``origin``;
rows marked ``mirror_x`` are also safe to mirror as whole sprites.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet, write_canonical
from ...core.draw import overlay_draw
from ...yaml_io import safe_dump

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "generic_world_fx"
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

# Frame duration is authored content, not a runtime guess.
ROWS: List[Tuple[str, int, int]] = [
    ("dash_streak", 7, 34),
    ("air_slice", 7, 42),
    ("wind_curl", 8, 50),
    ("shield_hit", 7, 44),
    ("shield_break", 8, 48),
    ("heal_bloom", 8, 58),
    ("alert_ping", 7, 54),
    ("dizzy_stars", 10, 78),
    ("teleport_depart", 8, 50),
    ("teleport_arrive", 8, 50),
    ("phase_ripple", 8, 48),
    ("water_splash", 8, 54),
    ("water_ripple", 8, 60),
    ("ember_wisp", 10, 72),
    ("leaf_swirl", 10, 72),
    ("electric_arc", 7, 36),
    ("electric_burst", 7, 40),
    ("ice_shatter", 8, 46),
]

# Strong shared outline plus family-specific hues keeps the catalog coherent
# while allowing each row to announce its semantic family immediately.
OUTLINE = (39, 31, 54, 255)
OUTLINE_SOFT = (64, 55, 82, 220)
WHITE = (255, 255, 247, 255)
CREAM = (255, 241, 189, 255)
GOLD = (255, 208, 82, 255)
ORANGE = (246, 139, 65, 255)
RED = (231, 91, 93, 255)
CYAN = (124, 225, 239, 255)
CYAN_HI = (219, 252, 255, 255)
BLUE = (93, 159, 222, 255)
VIOLET = (158, 113, 212, 255)
MAGENTA = (222, 115, 194, 255)
MINT = (149, 231, 181, 255)
MINT_HI = (223, 255, 225, 255)
GREEN = (75, 157, 100, 255)
LEAF = (99, 175, 91, 255)
LEAF_HI = (177, 218, 111, 255)
WATER = (87, 170, 225, 255)
WATER_HI = (194, 239, 255, 255)
ICE = (149, 216, 242, 255)
ICE_HI = (227, 251, 255, 255)

ACTOR_METADATA = {
    "actor": {
        "character_id": "fx_generic_world_fx",
        "display_name": "Generic World FX",
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

# These are author-owned semantics. Some are already actionable through frame
# anchors/timing; the rest intentionally remain non-consumed notes until a
# generic runtime contract has enough users to justify the field.
EFFECT_SPECS: Dict[str, dict] = {
    "dash_streak": {
        "family": "motion",
        "intent": "Short directional speed burst behind a fast body, dash, dodge, or projectile.",
        "loop": False,
        "placement": "entity_origin",
        "orientation": "positive_x_is_forward",
        "mirror_x": True,
        "rotate_safe": True,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "behind_source",
        "attachment_hint": "world_locked_after_spawn",
        "tint_policy_hint": "safe_to_tint",
        "nominal_span_px": 104,
    },
    "air_slice": {
        "family": "motion",
        "intent": "Curved directional air/cutting wake for fast melee, wind attacks, or swept movement.",
        "loop": False,
        "placement": "effect_origin",
        "orientation": "positive_x_is_forward",
        "mirror_x": True,
        "rotate_safe": True,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "over_world",
        "attachment_hint": "world_locked_after_spawn",
        "tint_policy_hint": "safe_to_tint",
        "nominal_span_px": 102,
    },
    "wind_curl": {
        "family": "motion",
        "intent": "Loose curling wind mark for gusts, launches, fans, airborne movement, or magical wind.",
        "loop": False,
        "placement": "effect_origin",
        "orientation": "radial_or_rotate_to_flow",
        "mirror_x": True,
        "rotate_safe": True,
        "blend_mode_hint": "alpha",
        "layer_hint": "over_world",
        "attachment_hint": "world_locked_after_spawn",
        "tint_policy_hint": "safe_to_tint",
        "nominal_diameter_px": 92,
    },
    "shield_hit": {
        "family": "defense",
        "intent": "Brief curved barrier flare centered on a guarded body or shield contact.",
        "loop": False,
        "placement": "entity_origin",
        "orientation": "radial",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "over_source",
        "attachment_hint": "follow_source",
        "tint_policy_hint": "safe_to_tint",
        "nominal_diameter_px": 96,
    },
    "shield_break": {
        "family": "defense",
        "intent": "Broken barrier ring and outward fragments for guard break, bubble pop, or ward collapse.",
        "loop": False,
        "placement": "entity_origin",
        "orientation": "radial",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "over_source",
        "attachment_hint": "world_locked_after_spawn",
        "tint_policy_hint": "safe_to_tint",
        "nominal_diameter_px": 112,
    },
    "heal_bloom": {
        "family": "status_positive",
        "intent": "Soft upward bloom for healing, regeneration, cleansing, or restorative pickups.",
        "loop": False,
        "placement": "entity_origin",
        "orientation": "world_or_gravity_up",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "over_source",
        "attachment_hint": "follow_source_optional",
        "tint_policy_hint": "preserve_palette_preferred",
        "nominal_diameter_px": 86,
    },
    "alert_ping": {
        "family": "status_attention",
        "intent": "Neutral attention ping for detection, target acquisition, warning, or interaction readiness.",
        "loop": False,
        "placement": "feature_point",
        "orientation": "screen_or_world_aligned",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha",
        "layer_hint": "over_source",
        "attachment_hint": "follow_source",
        "tint_policy_hint": "safe_to_tint",
        "nominal_diameter_px": 66,
    },
    "dizzy_stars": {
        "family": "status_negative",
        "intent": "Looping orbiting stars for stun, daze, confusion, or cartoon incapacitation.",
        "loop": True,
        "placement": "entity_origin",
        "orientation": "screen_or_world_aligned",
        "mirror_x": False,
        "rotate_safe": False,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "over_source",
        "attachment_hint": "follow_source",
        "tint_policy_hint": "preserve_palette_preferred",
        "nominal_span_px": 92,
    },
    "teleport_depart": {
        "family": "teleport",
        "intent": "Contracting broken rings and inward slivers for disappearance or phase-out.",
        "loop": False,
        "placement": "entity_origin",
        "orientation": "radial",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "over_source",
        "attachment_hint": "follow_source_until_visual_exit",
        "tint_policy_hint": "safe_to_tint",
        "nominal_diameter_px": 108,
    },
    "teleport_arrive": {
        "family": "teleport",
        "intent": "Outward phase ring and vertical flare for arrival, respawn, or materialization.",
        "loop": False,
        "placement": "entity_origin",
        "orientation": "radial",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "over_source",
        "attachment_hint": "world_locked_after_spawn",
        "tint_policy_hint": "safe_to_tint",
        "nominal_diameter_px": 108,
    },
    "phase_ripple": {
        "family": "teleport",
        "intent": "Offset concentric distortion ripple for phase shifts, invisibility changes, or reality warps.",
        "loop": False,
        "placement": "entity_origin",
        "orientation": "radial",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "over_source",
        "attachment_hint": "world_locked_after_spawn",
        "tint_policy_hint": "safe_to_tint",
        "nominal_diameter_px": 114,
    },
    "water_splash": {
        "family": "surface_water",
        "intent": "Hand-shaped crown splash for entering water, puddle impacts, rain hits, or wet landings.",
        "loop": False,
        "placement": "surface_contact",
        "orientation": "align_positive_y_to_surface_normal_opposite",
        "mirror_x": True,
        "rotate_safe": True,
        "blend_mode_hint": "alpha",
        "layer_hint": "over_world",
        "attachment_hint": "surface_locked",
        "tint_policy_hint": "safe_to_tint",
        "nominal_span_px": 94,
    },
    "water_ripple": {
        "family": "surface_water",
        "intent": "Flattened expanding surface ripple for water contact, drips, footsteps, or calm impacts.",
        "loop": False,
        "placement": "surface_contact",
        "orientation": "surface_tangent",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha",
        "layer_hint": "surface_overlay",
        "attachment_hint": "surface_locked",
        "tint_policy_hint": "safe_to_tint",
        "nominal_span_px": 108,
    },
    "ember_wisp": {
        "family": "ambient_elemental",
        "intent": "Looping rising flame/ember wisp for fires, hot machinery, torches, or magical heat.",
        "loop": True,
        "placement": "emitter_socket",
        "orientation": "gravity_up_or_world_up",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "over_world",
        "attachment_hint": "follow_emitter",
        "tint_policy_hint": "preserve_palette_preferred",
        "nominal_span_px": 52,
    },
    "leaf_swirl": {
        "family": "ambient_nature",
        "intent": "Looping small leaf orbit for wind pockets, forest ambience, nature magic, or movement accents.",
        "loop": True,
        "placement": "effect_origin",
        "orientation": "world_or_gravity_plane",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha",
        "layer_hint": "over_world",
        "attachment_hint": "world_locked_or_follow_source",
        "tint_policy_hint": "preserve_palette_preferred",
        "nominal_diameter_px": 92,
    },
    "electric_arc": {
        "family": "elemental_electric",
        "intent": "Directional forked lightning stroke for zap contact, taser-like beams, or electrical links.",
        "loop": False,
        "placement": "emitter_socket",
        "orientation": "positive_x_is_forward",
        "mirror_x": True,
        "rotate_safe": True,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "over_world",
        "attachment_hint": "world_locked_after_spawn",
        "tint_policy_hint": "safe_to_tint",
        "nominal_length_px": 100,
    },
    "electric_burst": {
        "family": "elemental_electric",
        "intent": "Radial jagged electrical punctuation for stun, overload, machinery, or shock impacts.",
        "loop": False,
        "placement": "effect_origin",
        "orientation": "radial",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha_or_additive",
        "layer_hint": "over_source",
        "attachment_hint": "world_locked_after_spawn",
        "tint_policy_hint": "safe_to_tint",
        "nominal_diameter_px": 98,
    },
    "ice_shatter": {
        "family": "elemental_ice",
        "intent": "Crystalline radial shatter for frozen breakage, brittle armor, ice attacks, or glass-like magic.",
        "loop": False,
        "placement": "effect_origin",
        "orientation": "radial",
        "mirror_x": False,
        "rotate_safe": True,
        "blend_mode_hint": "alpha",
        "layer_hint": "over_world",
        "attachment_hint": "world_locked_after_spawn",
        "tint_policy_hint": "safe_to_tint",
        "nominal_diameter_px": 106,
    },
}

LOOPS = {name for name, spec in EFFECT_SPECS.items() if spec["loop"]}


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


def _line(img: Image.Image, points: Sequence[Point], *, fill: RGBA, width: float) -> None:
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


def _diamond_points(cx: float, cy: float, rx: float, ry: float, rotation: float = 0.0) -> List[Point]:
    pts: List[Point] = []
    for a in (-math.pi / 2, 0.0, math.pi / 2, math.pi):
        x = math.cos(a) * rx
        y = math.sin(a) * ry
        pts.append((cx + x * math.cos(rotation) - y * math.sin(rotation), cy + x * math.sin(rotation) + y * math.cos(rotation)))
    return pts


def _star_points(cx: float, cy: float, outer: float, inner: float, spokes: int, rotation: float = 0.0) -> List[Point]:
    pts: List[Point] = []
    for i in range(spokes * 2):
        a = rotation + math.tau * i / (spokes * 2)
        r = outer if i % 2 == 0 else inner
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def _leaf_points(cx: float, cy: float, length: float, width: float, angle: float) -> List[Point]:
    ux, uy = math.cos(angle), math.sin(angle)
    vx, vy = -uy, ux
    return [
        (cx - ux * length * 0.48, cy - uy * length * 0.48),
        (cx + vx * width, cy + vy * width),
        (cx + ux * length * 0.52, cy + uy * length * 0.52),
        (cx - vx * width, cy - vy * width),
    ]


def _origin_for(anim: str) -> tuple[float, float]:
    if anim in {"dash_streak", "air_slice", "electric_arc"}:
        return 22.0, 64.0
    if anim in {"water_splash", "water_ripple"}:
        return 64.0, 88.0
    if anim == "ember_wisp":
        return 64.0, 94.0
    if anim == "alert_ping":
        return 64.0, 78.0
    return 64.0, 64.0


def _draw_dash_streak(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("dash_streak")
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.30) / 0.70))
    for i, off in enumerate((-15.0, -6.0, 4.0, 14.0)):
        head = ox + _lerp(38.0 + i * 8.0, 92.0 + i * 3.0, q)
        tail = ox + _lerp(5.0, 28.0 + i * 2.0, q)
        y = oy + off + math.sin(i * 1.7) * 2.0
        bend = 5.0 * math.sin(p * math.pi + i * 0.8)
        _line(img, [(tail, y + bend), ((tail + head) * 0.52, y - bend * 0.4), (head, y)], fill=_mul_alpha(CYAN_HI if i < 2 else BLUE, fade * (0.86 - i * 0.11)), width=3.2 - i * 0.38)
    wedge = [(ox + 11, oy - 20), (ox + 53 + 25 * q, oy), (ox + 10, oy + 20), (ox + 25, oy)]
    _polygon(img, wedge, fill=_mul_alpha(CYAN, 0.14 * fade))


def _draw_air_slice(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("air_slice")
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.42) / 0.58))
    span = _lerp(35.0, 92.0, q)
    h = _lerp(20.0, 49.0, q)
    # Two swept arcs make a crescent that feels hand-cut rather than geometric.
    _arc(img, (ox - 9, oy - h, ox + span, oy + h), 208, 334, fill=_mul_alpha(CYAN_HI, 0.94 * fade), width=_lerp(5.0, 2.0, q))
    _arc(img, (ox + 3, oy - h * 0.72, ox + span * 0.88, oy + h * 0.72), 210, 333, fill=_mul_alpha(BLUE, 0.62 * fade), width=2.0)
    for i in range(3):
        x = ox + _lerp(24.0 + i * 8, 62.0 + i * 11, q)
        y = oy + (-1 if i % 2 else 1) * (16.0 + i * 4.0)
        _line(img, [(x - 9, y), (x + 5, y - (4 if i % 2 else -4))], fill=_mul_alpha(WHITE, 0.48 * fade), width=1.2)


def _draw_wind_curl(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.46) / 0.54))
    r = _lerp(18.0, 44.0, q)
    phase = -25 + 185 * p
    _arc(img, (cx - r, cy - r * 0.72, cx + r, cy + r * 0.72), phase, phase + 248, fill=_mul_alpha(CYAN_HI, 0.78 * fade), width=_lerp(4.0, 1.5, q))
    r2 = r * 0.62
    _arc(img, (cx - r2, cy - r2 * 0.70, cx + r2, cy + r2 * 0.70), phase + 70, phase + 298, fill=_mul_alpha(BLUE, 0.58 * fade), width=1.6)
    for i in range(4):
        a = math.radians(phase + 46 + i * 61)
        rr = r * (0.76 + 0.06 * i)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.72
        _line(img, [(x - math.cos(a) * 7, y - math.sin(a) * 5), (x + math.cos(a) * 5, y + math.sin(a) * 4)], fill=_mul_alpha(WHITE, 0.45 * fade), width=1.1)


def _draw_shield_hit(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.34) / 0.66))
    r = _lerp(30.0, 48.0, q)
    _ellipse(img, (cx - r, cy - r, cx + r, cy + r), fill=_mul_alpha(BLUE, 0.10 * fade), outline=_mul_alpha(CYAN_HI, 0.72 * fade), width=_lerp(4.2, 1.5, q))
    _arc(img, (cx - r * 0.90, cy - r * 0.90, cx + r * 0.90, cy + r * 0.90), 204, 322, fill=_mul_alpha(VIOLET, 0.70 * fade), width=2.7)
    # Contact flash at upper-left, intentionally asymmetric.
    fx, fy = cx - r * 0.58, cy - r * 0.34
    _polygon(img, _star_points(fx, fy, _lerp(12.0, 20.0, q), 4.5, 6, rotation=0.12), fill=_mul_alpha(WHITE, 0.96 * fade), outline=_mul_alpha(CYAN, 0.62 * fade), width=1.0)


def _draw_shield_break(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.42) / 0.58))
    r = _lerp(24.0, 52.0, q)
    for start, end, col in ((12, 70, CYAN_HI), (96, 162, BLUE), (188, 248, VIOLET), (282, 342, CYAN)):
        _arc(img, (cx - r, cy - r, cx + r, cy + r), start, end, fill=_mul_alpha(col, 0.82 * fade), width=_lerp(4.0, 1.6, q))
    for i in range(8):
        a = 0.24 + math.tau * i / 8.0
        rr = _lerp(24.0, 53.0 + (i % 3) * 7.0, q)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        _polygon(img, _diamond_points(x, y, 4.0 + (i % 2), 7.0, a + 0.4), fill=_mul_alpha(CYAN_HI if i % 3 else VIOLET, 0.76 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.55 * fade), width=0.8)
    _line(img, [(cx - 3, cy - 30), (cx + 8, cy - 8), (cx - 5, cy + 8), (cx + 4, cy + 30)], fill=_mul_alpha(WHITE, 0.55 * fade), width=1.6)


def _draw_heal_bloom(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 70.0
    q = _smooth(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.58) / 0.42))
    core = _lerp(8.0, 17.0, math.sin(math.pi * min(1.0, p * 1.15)))
    _ellipse(img, (cx - core, cy - core, cx + core, cy + core), fill=_mul_alpha(MINT_HI, 0.72 * fade), outline=_mul_alpha(GREEN, 0.64 * fade), width=1.3)
    for i in range(6):
        a = -math.pi / 2 + math.tau * i / 6.0
        rr = _lerp(9.0, 31.0, q)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        _ellipse(img, (x - 7, y - 4, x + 7, y + 4), fill=_mul_alpha(MINT if i % 2 else MINT_HI, 0.62 * fade), outline=_mul_alpha(GREEN, 0.40 * fade), width=0.8)
    for i in range(4):
        x = cx + (-1.5 + i) * 12.0 + math.sin(i * 2.1) * 3.0
        y = cy + 22.0 - q * (34.0 + i * 6.0)
        _polygon(img, _diamond_points(x, y, 2.5, 5.5), fill=_mul_alpha(WHITE if i % 2 else CREAM, 0.72 * fade))


def _draw_alert_ping(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("alert_ping")
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.42) / 0.58))
    cy = oy - 25.0
    r = _lerp(8.0, 28.0, q)
    _ellipse(img, (ox - r, cy - r, ox + r, cy + r), outline=_mul_alpha(GOLD, 0.72 * fade), width=_lerp(3.2, 1.0, q))
    _polygon(img, [(ox, cy - 18), (ox + 8, cy + 4), (ox + 3.5, cy + 11), (ox - 3.5, cy + 11), (ox - 8, cy + 4)], fill=_mul_alpha(CREAM, 0.92 * fade), outline=_mul_alpha(OUTLINE, 0.72 * fade), width=1.0)
    _ellipse(img, (ox - 3, cy + 15, ox + 3, cy + 21), fill=_mul_alpha(WHITE, 0.94 * fade), outline=_mul_alpha(OUTLINE, 0.65 * fade), width=0.8)
    for i, a in enumerate((-2.55, -1.92, -1.22, -0.58)):
        rr = r + 7 + (i % 2) * 3
        _line(img, [(ox + math.cos(a) * rr, cy + math.sin(a) * rr), (ox + math.cos(a) * (rr + 8), cy + math.sin(a) * (rr + 8))], fill=_mul_alpha(GOLD, 0.60 * fade), width=1.4)


def _draw_dizzy_stars(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 58.0
    phase = math.tau * p
    # Tilted orbit gives apparent depth. Stars change scale as they pass front/back.
    _arc(img, (cx - 43, cy - 18, cx + 43, cy + 18), 190, 350, fill=_mul_alpha(OUTLINE_SOFT, 0.24), width=1.0)
    for i in range(5):
        a = phase + math.tau * i / 5.0
        x = cx + math.cos(a) * 39.0
        y = cy + math.sin(a) * 15.0
        front = 0.5 + 0.5 * math.sin(a)
        outer = 5.0 + 2.7 * front
        _polygon(img, _star_points(x, y, outer, outer * 0.44, 5, rotation=-math.pi / 2 + a * 0.25), fill=_mul_alpha(GOLD if i % 2 else CREAM, 0.74 + 0.22 * front), outline=_mul_alpha(OUTLINE, 0.68), width=0.8)


def _draw_teleport_depart(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _smooth(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.66) / 0.34))
    r = _lerp(50.0, 9.0, q)
    for i, col in enumerate((CYAN, MAGENTA, CYAN_HI)):
        rr = r + i * 4.0
        _arc(img, (cx - rr, cy - rr, cx + rr, cy + rr), 25 + i * 92 + p * 110, 130 + i * 92 + p * 110, fill=_mul_alpha(col, (0.78 - i * 0.12) * fade), width=2.0 - i * 0.2)
    for i in range(8):
        a = math.tau * i / 8.0 + p * 0.45
        rr = _lerp(56.0 + (i % 2) * 7.0, 13.0, q)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        tail = 8.0 + 10.0 * (1.0 - q)
        _line(img, [(x + math.cos(a) * tail, y + math.sin(a) * tail), (x, y)], fill=_mul_alpha(CYAN_HI if i % 3 else MAGENTA, 0.72 * fade), width=1.4)
    _ellipse(img, (cx - 6, cy - 15, cx + 6, cy + 15), fill=_mul_alpha(WHITE, 0.34 * q * fade))


def _draw_teleport_arrive(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.50) / 0.50))
    r = _lerp(6.0, 52.0, q)
    _ellipse(img, (cx - r, cy - r, cx + r, cy + r), outline=_mul_alpha(CYAN_HI, 0.76 * fade), width=_lerp(4.0, 1.0, q))
    _arc(img, (cx - r * 1.05, cy - r * 1.05, cx + r * 1.05, cy + r * 1.05), 25, 134, fill=_mul_alpha(MAGENTA, 0.70 * fade), width=2.0)
    _arc(img, (cx - r * 1.05, cy - r * 1.05, cx + r * 1.05, cy + r * 1.05), 202, 322, fill=_mul_alpha(BLUE, 0.60 * fade), width=1.7)
    flare_h = _lerp(46.0, 17.0, q)
    flare_w = _lerp(4.0, 12.0, q)
    _polygon(img, [(cx, cy - flare_h), (cx + flare_w, cy), (cx, cy + flare_h), (cx - flare_w, cy)], fill=_mul_alpha(WHITE, 0.65 * fade))
    for i in range(6):
        a = 0.35 + math.tau * i / 6.0
        rr = r + 8.0
        _polygon(img, _diamond_points(cx + math.cos(a) * rr, cy + math.sin(a) * rr, 2.0, 4.5, a), fill=_mul_alpha(CREAM if i % 2 else CYAN_HI, 0.62 * fade))


def _draw_phase_ripple(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.48) / 0.52))
    for i, col in enumerate((MAGENTA, CYAN, VIOLET)):
        r = _lerp(10.0 + i * 3.0, 54.0 - i * 3.0, q)
        xoff = math.sin(p * math.pi * 2 + i * 1.8) * (2.0 + i)
        yoff = math.cos(p * math.pi * 2 + i * 1.2) * (1.0 + i * 0.7)
        _ellipse(img, (cx + xoff - r, cy + yoff - r * 0.88, cx + xoff + r, cy + yoff + r * 0.88), outline=_mul_alpha(col, (0.68 - i * 0.10) * fade), width=2.0 - i * 0.2)
    for i in range(4):
        y = cy - 26 + i * 17
        shift = math.sin(p * math.pi + i) * 12 * fade
        _line(img, [(cx - 17 + shift, y), (cx + 18 + shift, y)], fill=_mul_alpha(WHITE, 0.25 * fade), width=1.2)


def _draw_water_splash(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("water_splash")
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.55) / 0.45))
    # Flattened base splash.
    _ellipse(img, (ox - _lerp(15, 43, q), oy - 5, ox + _lerp(15, 43, q), oy + 5), fill=_mul_alpha(WATER, 0.25 * fade), outline=_mul_alpha(WATER_HI, 0.62 * fade), width=1.4)
    for i, angle in enumerate((-2.30, -1.95, -1.62, -1.28, -0.90)):
        height = _lerp(16.0 + (i % 2) * 4, 48.0 - abs(2 - i) * 4.0, q)
        x = ox + math.cos(angle) * _lerp(6.0, 30.0 + i * 2.0, q)
        y = oy + math.sin(angle) * height
        _line(img, [(ox + (i - 2) * 5.5, oy - 1), (x, y)], fill=_mul_alpha(WATER_HI if i in (1, 2, 3) else WATER, 0.78 * fade), width=2.5 if i == 2 else 1.8)
        _ellipse(img, (x - 3.2, y - 4.7, x + 3.2, y + 4.7), fill=_mul_alpha(WATER_HI, 0.72 * fade))
    for i in range(4):
        x = ox - 37 + i * 25
        y = oy - _lerp(6.0, 18.0 + (i % 2) * 7, q)
        _ellipse(img, (x - 2.8, y - 3.8, x + 2.8, y + 3.8), fill=_mul_alpha(WATER_HI, 0.68 * fade))


def _draw_water_ripple(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("water_ripple")
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.34) / 0.66))
    for i in range(3):
        rx = _lerp(8.0 + i * 4.0, 52.0 - i * 5.0, q)
        ry = rx * (0.15 + i * 0.015)
        _ellipse(img, (ox - rx, oy - ry, ox + rx, oy + ry), outline=_mul_alpha(WATER_HI if i == 0 else WATER, (0.72 - i * 0.16) * fade), width=1.8 - i * 0.2)


def _draw_ember_wisp(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("ember_wisp")
    phase = math.tau * p
    # A periodic flame built from overlapping teardrop-like diamonds and a curl.
    sway = math.sin(phase) * 5.0
    pulse = 0.5 + 0.5 * math.sin(phase + 0.9)
    h = 34.0 + 5.0 * pulse
    outer = [(ox, oy), (ox - 12 + sway * 0.3, oy - h * 0.42), (ox + sway, oy - h), (ox + 12 + sway * 0.25, oy - h * 0.38)]
    _polygon(img, outer, fill=_mul_alpha(ORANGE, 0.84), outline=_mul_alpha(OUTLINE, 0.72), width=1.0)
    inner = [(ox, oy - 3), (ox - 5 + sway * 0.18, oy - h * 0.42), (ox + sway * 0.55, oy - h * 0.76), (ox + 5 + sway * 0.12, oy - h * 0.38)]
    _polygon(img, inner, fill=_mul_alpha(CREAM, 0.92))
    _arc(img, (ox - 14 + sway, oy - h - 11, ox + 14 + sway, oy - h + 15), 202 + math.degrees(phase) * 0.12, 336 + math.degrees(phase) * 0.12, fill=_mul_alpha(GOLD, 0.68), width=1.5)
    for i in range(3):
        a = phase + i * 2.1
        x = ox + math.sin(a) * (12 + i * 3)
        y = oy - 28 - i * 12 + math.cos(a) * 4
        _polygon(img, _diamond_points(x, y, 1.8, 3.2), fill=_mul_alpha(GOLD if i % 2 else CREAM, 0.62))


def _draw_leaf_swirl(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    phase = math.tau * p
    for i in range(5):
        a = phase + math.tau * i / 5.0
        radius = 31.0 + 7.0 * math.sin(phase * 2 + i * 1.1)
        x = cx + math.cos(a) * radius
        y = cy + math.sin(a) * radius * 0.72
        angle = a + 0.8 + 0.45 * math.sin(phase + i)
        _polygon(img, _leaf_points(x, y, 13.0, 4.2, angle), fill=_mul_alpha(LEAF_HI if i % 2 else LEAF, 0.86), outline=_mul_alpha(GREEN, 0.62), width=0.8)
        _line(img, [(x - math.cos(angle) * 5, y - math.sin(angle) * 5), (x + math.cos(angle) * 5, y + math.sin(angle) * 5)], fill=_mul_alpha(CREAM, 0.42), width=0.7)
    _arc(img, (cx - 42, cy - 28, cx + 42, cy + 28), 15 + math.degrees(phase) * 0.15, 178 + math.degrees(phase) * 0.15, fill=_mul_alpha(MINT, 0.20), width=1.0)


def _draw_electric_arc(img: Image.Image, p: float) -> None:
    ox, oy = _origin_for("electric_arc")
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.40) / 0.60))
    length = _lerp(38.0, 96.0, q)
    # Authored deterministic jitter changes each frame through p, avoiding RNG.
    pts = [(ox, oy)]
    for i in range(1, 7):
        x = ox + length * i / 7.0
        y = oy + math.sin(i * 4.3 + p * 18.0) * (7.5 + (i % 2) * 2.5)
        pts.append((x, y))
    pts.append((ox + length, oy + math.sin(p * 17.0) * 2.0))
    _line(img, pts, fill=_mul_alpha(OUTLINE, 0.70 * fade), width=5.0)
    _line(img, pts, fill=_mul_alpha(GOLD, 0.96 * fade), width=2.6)
    _line(img, pts, fill=_mul_alpha(WHITE, 0.90 * fade), width=1.0)
    for i in (2, 4, 5):
        x, y = pts[i]
        a = (-0.8 if i % 2 else 0.8) + math.sin(p * 11 + i) * 0.2
        end = (x + math.cos(a) * (13 + i), y + math.sin(a) * (13 + i))
        _line(img, [(x, y), end], fill=_mul_alpha(CREAM, 0.76 * fade), width=1.3)


def _draw_electric_burst(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.34) / 0.66))
    ring = _lerp(10.0, 32.0, q)
    _ellipse(img, (cx - ring, cy - ring, cx + ring, cy + ring), outline=_mul_alpha(CYAN, 0.45 * fade), width=1.4)
    for i in range(9):
        a = 0.18 + math.tau * i / 9.0
        r0 = _lerp(10.0, 20.0, q)
        r1 = _lerp(28.0, 52.0 + (i % 3) * 4.0, q)
        mid = (r0 + r1) * 0.53
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0)
        pm = (cx + math.cos(a + 0.12 * (-1 if i % 2 else 1)) * mid, cy + math.sin(a + 0.12 * (-1 if i % 2 else 1)) * mid)
        p1 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1)
        _line(img, [p0, pm, p1], fill=_mul_alpha(GOLD if i % 3 else CYAN_HI, 0.82 * fade), width=2.0)
    _polygon(img, _star_points(cx, cy, _lerp(13.0, 20.0, q), 5.0, 7, rotation=p * 0.3), fill=_mul_alpha(WHITE, 0.90 * fade), outline=_mul_alpha(GOLD, 0.72 * fade), width=1.0)


def _draw_ice_shatter(img: Image.Image, p: float) -> None:
    cx, cy = 64.0, 64.0
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.46) / 0.54))
    # Large shards lead the eye; small shards fill negative space.
    for i in range(10):
        a = 0.16 + math.tau * i / 10.0
        rr = _lerp(8.0 + (i % 2) * 4.0, 35.0 + (i % 3) * 8.0, q)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        length = 12.0 + (i % 4) * 3.0
        width = 4.0 + (i % 2) * 1.5
        _polygon(img, _diamond_points(x, y, width, length, a + 0.35), fill=_mul_alpha(ICE_HI if i % 3 else ICE, 0.74 * fade), outline=_mul_alpha(BLUE, 0.58 * fade), width=0.8)
    crack = _lerp(9.0, 24.0, q)
    for a in (-2.55, -1.72, -0.76, 0.18, 1.10, 2.12):
        _line(img, [(cx, cy), (cx + math.cos(a) * crack, cy + math.sin(a) * crack)], fill=_mul_alpha(WHITE, 0.62 * fade), width=1.1)
    _polygon(img, _star_points(cx, cy, 11.0, 5.0, 6, rotation=0.1), fill=_mul_alpha(ICE_HI, 0.86 * fade), outline=_mul_alpha(OUTLINE_SOFT, 0.44 * fade), width=0.8)


def _frame_progress(anim: str, frame_idx: int, nframes: int) -> float:
    if anim in LOOPS:
        return frame_idx / max(1, nframes)
    return frame_idx / max(1, nframes - 1)


def _phase(anim: str, p: float) -> str:
    if anim in LOOPS:
        return "loop"
    if anim in {"teleport_depart"}:
        return "contract" if p < 0.64 else "vanish"
    if anim in {"teleport_arrive", "phase_ripple", "water_ripple"}:
        return "expand" if p < 0.60 else "dissipate"
    if anim in {"water_splash", "heal_bloom"}:
        if p < 0.28:
            return "form"
        if p < 0.65:
            return "spread"
        return "dissipate"
    if anim in {"shield_break", "ice_shatter"}:
        return "fracture" if p < 0.55 else "scatter"
    if p < 0.20:
        return "onset"
    if p < 0.62:
        return "follow_through"
    return "dissipate"


def _intensity(anim: str, p: float) -> float:
    if anim in LOOPS:
        return round(0.72 + 0.18 * (0.5 + 0.5 * math.sin(math.tau * p)), 4)
    if anim == "heal_bloom":
        return round(math.sin(math.pi * _clamp(p)) ** 0.72, 4)
    return round(1.0 - 0.70 * _smooth(p), 4)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    p = _frame_progress(anim, frame_idx, nframes)
    if anim not in LOOPS and frame_idx == nframes - 1:
        return Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    drawers = {
        "dash_streak": _draw_dash_streak,
        "air_slice": _draw_air_slice,
        "wind_curl": _draw_wind_curl,
        "shield_hit": _draw_shield_hit,
        "shield_break": _draw_shield_break,
        "heal_bloom": _draw_heal_bloom,
        "alert_ping": _draw_alert_ping,
        "dizzy_stars": _draw_dizzy_stars,
        "teleport_depart": _draw_teleport_depart,
        "teleport_arrive": _draw_teleport_arrive,
        "phase_ripple": _draw_phase_ripple,
        "water_splash": _draw_water_splash,
        "water_ripple": _draw_water_ripple,
        "ember_wisp": _draw_ember_wisp,
        "leaf_swirl": _draw_leaf_swirl,
        "electric_arc": _draw_electric_arc,
        "electric_burst": _draw_electric_burst,
        "ice_shatter": _draw_ice_shatter,
    }
    try:
        drawers[anim](img, p)
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
            "Promote repeated authoring hints such as loop, orientation, attachment, layer, and tint policy only as generic presentation schema fields; do not hard-code these animation names.",
            "Directional rows author +X as forward. Rotate or mirror the whole effect around origin rather than manipulating packed rectangles.",
            "Surface rows author their contact point explicitly. Surface orientation is a presentation transform, not a pixel rewrite.",
            "Loop rows are periodic and contain no clear terminal frame. One-shots deliberately end clear and may be despawned after that frame.",
            "attachment_hint and layer_hint express visual intent, not simulation ownership; presentation remains free to map them to engine concepts.",
            "tint_policy_hint distinguishes palette-bearing effects from deliberately tint-friendly neutral marks; alpha rendering remains a valid fallback when additive blending is unavailable.",
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
