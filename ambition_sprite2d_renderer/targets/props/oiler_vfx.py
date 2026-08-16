"""Detached presentation VFX for Oiler, Ambition's Euler-inspired gate mechanic.

This target is intentionally additive and auto-discovered: the sprite renderer
registers any public module under ``targets/props`` that exports ``render``.
No central target list, regeneration roster, or runtime integration is required.

Oiler's detached effects use the visual language already present in his body
renderer and story role: chalk curves, tolerances, gauges, bearings, brass and
steel mechanisms, dark blue-green oil, and practical gate stabilization.  The
Euler reference stays structural rather than becoming generic wizard math.

Current sheet metadata carries authoritative frame timing and placement anchors.
The generated ``oiler_vfx_authoring.yaml`` sidecar preserves richer author-owned
intent (orientation, attachment, lifecycle, SFX pairing, and semantic meaning)
for a future generic presentation integration.
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

TARGET_NAME = "oiler_vfx"
AUTHORING_FILE = f"{TARGET_NAME}_authoring.yaml"
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
    AUTHORING_FILE,
]

FRAME_SIZE = (128, 128)
SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER

ROWS: List[Tuple[str, int, int]] = [
    ("chalk_spiral", 9, 56),
    ("curve_trace", 10, 52),
    ("invariant_loop", 12, 70),
    ("convergence_ticks", 9, 46),
    ("tolerance_brackets", 8, 50),
    ("error_term_collapse", 9, 48),
    ("bearing_ping", 7, 44),
    ("friction_tick", 6, 42),
    ("gauge_sweep", 9, 50),
    ("stabilizer_spinup", 12, 60),
    ("stabilizer_lock", 7, 48),
    ("gate_calibration", 12, 64),
    ("brass_spark", 7, 42),
    ("wrench_strike", 6, 44),
    ("oil_drip", 9, 58),
    ("oil_splash", 8, 46),
    ("oil_slick", 10, 64),
    ("pressure_vent", 10, 54),
    ("portal_leak", 12, 70),
    ("unit_circle_rotation", 10, 56),
    ("oil_geyser_emerge", 9, 48),
    ("oil_geyser_stream", 12, 56),
    ("oil_geyser_impact", 8, 46),
]

LOOPS = {"invariant_loop", "gate_calibration", "portal_leak", "oil_geyser_stream"}

# Palette shared conceptually with oiler_mechanic.py, copied here rather than
# importing a body renderer so detached VFX remain independently renderable.
OUTLINE = (23, 18, 14, 255)
CHALK = (229, 217, 181, 255)
CHALK_HI = (251, 244, 217, 255)
STEEL = (185, 192, 192, 255)
STEEL_HI = (227, 231, 226, 255)
STEEL_DARK = (89, 99, 101, 255)
BRASS = (211, 154, 59, 255)
BRASS_HI = (240, 201, 106, 255)
BRASS_DARK = (123, 81, 25, 255)
OIL = (40, 61, 67, 255)
OIL_HI = (78, 116, 120, 255)
OIL_GLEAM = (130, 167, 166, 255)
WARNING = (196, 76, 53, 255)
GAUGE = (217, 224, 216, 255)
GAUGE_INK = (62, 85, 87, 255)
RUST = (141, 69, 41, 255)
CREAM = (233, 223, 196, 255)

ACTOR_METADATA = {
    "actor": {"character_id": "fx_oiler_vfx", "display_name": "Oiler Detached VFX"},
    "body": {
        "body_plan": "Effect",
        "body_kind": "Overlay",
        "mass_class": "Light",
        "locomotion_hint": "Stationary",
        "traits": ["fx", "overlay", "presentation", "oiler", "mechanic", "euler"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "sockets": {
        "origin": {
            "source": f"{TARGET_NAME}.geometry",
            "point": {"x": 64.0, "y": 64.0},
        },
    },
    "tags": ["fx", "overlay", "presentation", "oiler", "mechanic", "euler"],
}


def _spec(
    family: str,
    intent: str,
    *,
    placement: str = "effect_origin",
    orientation: str = "radial",
    mirror_x: bool = False,
    loop: bool = False,
    relationship: str = "active",
    attachment: str = "world_locked_after_spawn",
    layer: str = "over_world",
    blend: str = "alpha",
    size: int = 96,
    sfx: str | None = None,
) -> dict:
    return {
        "family": family,
        "intent": intent,
        "placement": placement,
        "orientation": orientation,
        "mirror_x": mirror_x,
        "rotate_safe": True,
        "loop": loop,
        "effect_relationship": relationship,
        "attachment_hint": attachment,
        "layer_hint": layer,
        "blend_mode_hint": blend,
        "nominal_span_px": size,
        "sfx_cue_hint": sfx,
        "requires_character_context": True,
    }


EFFECT_SPECS: Dict[str, dict] = {
    "chalk_spiral": _spec(
        "eulerian_chalk",
        "A hand-drawn workshop spiral rapidly resolves from a rough chalk stroke into one confident curve.",
        placement="surface_or_feature_point",
        relationship="startup",
        blend="alpha_or_additive",
        sfx="vfx.oiler.chalk_spiral",
    ),
    "curve_trace": _spec(
        "eulerian_chalk",
        "A practical traced solution curve with moving construction ticks, like Oiler finding the route rather than declaring it.",
        placement="feature_point",
        orientation="positive_x_is_forward",
        mirror_x=True,
        sfx="vfx.oiler.curve_trace",
    ),
    "invariant_loop": _spec(
        "diagnostic_math",
        "Looping outer geometry changes while a central brass bearing remains fixed: a visual invariant used as a sustain marker.",
        loop=True,
        attachment="follow_source_optional",
        sfx="vfx.oiler.invariant_loop.loop",
    ),
    "convergence_ticks": _spec(
        "diagnostic_math",
        "Successive measured marks close in on one calibrated point, communicating convergence without decorative equations.",
        placement="target_point",
        sfx="vfx.oiler.convergence_ticks",
    ),
    "tolerance_brackets": _spec(
        "diagnostic_math",
        "Two machinist brackets squeeze inward until the subject sits inside an acceptable tolerance band.",
        placement="target_point",
        orientation="surface_tangent_optional",
        mirror_x=True,
        sfx="vfx.oiler.tolerance_brackets",
    ),
    "error_term_collapse": _spec(
        "diagnostic_math",
        "A warning wedge/error bar shrinks toward zero and resolves into a brass check point.",
        placement="target_point",
        relationship="release",
        sfx="vfx.oiler.error_term_collapse",
    ),
    "bearing_ping": _spec(
        "mechanical_diagnostic",
        "Concentric diagnostic rings and a tiny bearing crosshair identify a rotational fault.",
        placement="feature_point",
        sfx="vfx.oiler.bearing_ping",
    ),
    "friction_tick": _spec(
        "mechanical_diagnostic",
        "A tiny wheel/shaft stutters one notch and throws a brief hot friction mark; deliberately small and irritating.",
        placement="feature_point",
        orientation="surface_tangent_optional",
        sfx="vfx.oiler.friction_tick",
    ),
    "gauge_sweep": _spec(
        "instrumentation",
        "Semicircular workshop gauge sweeps from warning into calibrated brass/greenish center tolerance.",
        placement="feature_point",
        sfx="vfx.oiler.gauge_sweep",
    ),
    "stabilizer_spinup": _spec(
        "gate_stabilizer",
        "Three-clamp stabilizer rings spin at different rates and settle into phase around a steady center.",
        placement="effect_origin",
        relationship="startup",
        blend="alpha_or_additive",
        size=116,
        sfx="vfx.oiler.stabilizer_spinup",
    ),
    "stabilizer_lock": _spec(
        "gate_stabilizer",
        "Three brass clamps snap inward and lock a wobbling gate ring into a clean circle.",
        placement="effect_origin",
        relationship="release",
        size=112,
        sfx="vfx.oiler.stabilizer_lock",
    ),
    "gate_calibration": _spec(
        "gate_stabilizer",
        "Looping calibrated portal/gate reticle with rotating brass ticks and a restrained gauge pulse.",
        loop=True,
        attachment="follow_source_optional",
        blend="alpha_or_additive",
        size=118,
        sfx="vfx.oiler.gate_calibration.loop",
    ),
    "brass_spark": _spec(
        "mechanical_contact",
        "Short warm brass/steel contact spark for successful tool contact, clamp engagement, or a clean mechanical strike.",
        placement="contact_point",
        relationship="impact",
        blend="alpha_or_additive",
        sfx="vfx.oiler.brass_spark",
    ),
    "wrench_strike": _spec(
        "mechanical_contact",
        "Compact wrench-shaped motion slash terminating in a steel/brass contact star; a mechanic's punctuation mark.",
        placement="contact_point",
        orientation="positive_x_is_forward",
        mirror_x=True,
        relationship="impact",
        sfx="vfx.oiler.wrench_strike",
    ),
    "oil_drip": _spec(
        "oil",
        "One viscous blue-green drop stretches, releases, and beads on a surface.",
        placement="emitter_socket",
        orientation="gravity_down",
        attachment="follow_source_until_release",
        sfx="vfx.oiler.oil_drip",
    ),
    "oil_splash": _spec(
        "oil",
        "Dark blue-green oil contact splash with thick lobes and restrained reflected highlights.",
        placement="surface_contact",
        orientation="surface_normal",
        mirror_x=True,
        relationship="impact",
        sfx="vfx.oiler.oil_splash",
    ),
    "oil_slick": _spec(
        "oil",
        "A compact oil puddle spreads and settles into a thin reflective slick; useful as aftermath or hazard dressing.",
        placement="surface_contact",
        orientation="surface_tangent",
        mirror_x=True,
        relationship="aftermath",
        sfx="vfx.oiler.oil_slick",
    ),
    "pressure_vent": _spec(
        "gate_mechanic",
        "Directional pressure vent with a brass valve flash followed by pale vapor wedges.",
        placement="emitter_socket",
        orientation="positive_x_is_forward",
        mirror_x=True,
        sfx="vfx.oiler.pressure_vent",
    ),
    "portal_leak": _spec(
        "gate_mechanic",
        "Looping unstable gate leak: an imperfect oval sheds oily teal droplets and tiny brass diagnostic sparks.",
        placement="effect_origin",
        loop=True,
        attachment="follow_source_optional",
        blend="alpha_or_additive",
        size=118,
        sfx="vfx.oiler.portal_leak.loop",
    ),
    "unit_circle_rotation": _spec(
        "eulerian_calibration",
        "A unit-circle-like calibration dial rotates one vector while its orthogonal projections track along ruled axes.",
        placement="feature_point",
        relationship="active",
        blend="alpha_or_additive",
        sfx="vfx.oiler.unit_circle_rotation",
    ),
    "oil_geyser_emerge": _spec(
        "oil_attack",
        "A pressurized brass outlet coughs open and throws the first heavy crown of dark oil into the shot direction.",
        placement="emitter_socket",
        orientation="positive_x_is_forward",
        mirror_x=True,
        relationship="startup",
        attachment="follow_source_optional",
        blend="alpha_or_additive",
        size=116,
        sfx="vfx.oiler.oil_geyser_emerge",
    ),
    "oil_geyser_stream": _spec(
        "oil_attack",
        "A sustained high-pressure oil jet with a coherent core, shearing spray, and detached droplets to shove anything in its path.",
        placement="emitter_socket",
        orientation="positive_x_is_forward",
        mirror_x=True,
        loop=True,
        attachment="follow_source_optional",
        blend="alpha_or_additive",
        size=124,
        sfx="vfx.oiler.oil_geyser_stream.loop",
    ),
    "oil_geyser_impact": _spec(
        "oil_attack",
        "A forceful oily impact bloom: thick splat crown, rebound droplets, and a shove-mark where the pressurized stream lands.",
        placement="contact_point",
        orientation="surface_normal",
        mirror_x=True,
        relationship="impact",
        blend="alpha_or_additive",
        size=112,
        sfx="vfx.oiler.oil_geyser_impact",
    ),
}


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _smooth(v: float) -> float:
    v = _clamp(v)
    return v * v * (3.0 - 2.0 * v)


def _ease(v: float) -> float:
    v = _clamp(v)
    return 1.0 - (1.0 - v) ** 3


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _alpha(c: RGBA, a: float) -> RGBA:
    return c[0], c[1], c[2], max(0, min(255, round(c[3] * a)))


def _s(v: float) -> int:
    return round(v * SUPER)


def _draw(img: Image.Image) -> ImageDraw.ImageDraw:
    return ImageDraw.Draw(img, "RGBA")


def _line(img: Image.Image, pts: Sequence[Point], color: RGBA, width: float = 1.0) -> None:
    _draw(img).line([(_s(x), _s(y)) for x, y in pts], fill=color, width=max(1, _s(width)), joint="curve")


def _ellipse(img: Image.Image, box: Sequence[float], fill: RGBA | None = None, outline: RGBA | None = None, width: float = 1.0) -> None:
    _draw(img).ellipse(tuple(_s(x) for x in box), fill=fill, outline=outline, width=max(1, _s(width)))


def _arc(img: Image.Image, box: Sequence[float], start: float, end: float, color: RGBA, width: float = 1.0) -> None:
    _draw(img).arc(tuple(_s(x) for x in box), start=start, end=end, fill=color, width=max(1, _s(width)))


def _poly(img: Image.Image, pts: Sequence[Point], fill: RGBA | None = None, outline: RGBA | None = None, width: float = 1.0) -> None:
    d = _draw(img)
    p = [(_s(x), _s(y)) for x, y in pts]
    d.polygon(p, fill=fill)
    if outline:
        d.line(p + [p[0]], fill=outline, width=max(1, _s(width)), joint="curve")


def _rot(x: float, y: float, a: float) -> Point:
    c, s = math.cos(a), math.sin(a)
    return x * c - y * s, x * s + y * c


def _diamond(cx: float, cy: float, rx: float, ry: float, a: float = 0.0) -> List[Point]:
    return [(cx + dx, cy + dy) for dx, dy in (_rot(0, -ry, a), _rot(rx, 0, a), _rot(0, ry, a), _rot(-rx, 0, a))]


def _gear_ticks(img: Image.Image, cx: float, cy: float, r0: float, r1: float, count: int, phase: float, color: RGBA, width: float = 1.3) -> None:
    for i in range(count):
        a = phase + math.tau * i / count
        _line(img, [(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], color, width)


def _chalk_polyline(img: Image.Image, pts: Sequence[Point], alpha: float = 1.0, width: float = 2.1) -> None:
    # Double stroke provides a deliberately dry, imperfect chalk edge without RNG.
    _line(img, pts, _alpha(CHALK, 0.88 * alpha), width)
    shifted = [(x + 0.7 * math.sin(i * 2.1), y + 0.5 * math.cos(i * 1.7)) for i, (x, y) in enumerate(pts)]
    _line(img, shifted, _alpha(CHALK_HI, 0.42 * alpha), max(0.7, width * 0.42))


def _draw_chalk_spiral(img: Image.Image, p: float) -> None:
    q = _ease(p)
    pts = []
    n = max(3, round(48 * q))
    for i in range(n):
        t = i / 47
        a = t * math.tau * 2.25 - math.pi / 2
        r = 5 + 39 * t
        pts.append((64 + math.cos(a) * r, 65 + math.sin(a) * r * 0.78))
    _chalk_polyline(img, pts, 1.0 - 0.25 * p, 2.2)
    if p > 0.55:
        _ellipse(img, (59, 60, 69, 70), fill=_alpha(BRASS_HI, _smooth((p - 0.55) / 0.45)), outline=OUTLINE, width=0.8)


def _draw_curve_trace(img: Image.Image, p: float) -> None:
    q = _ease(p)
    pts = []
    for i in range(50):
        t = i / 49
        if t > q:
            break
        x = 18 + 94 * t
        y = 82 - 34 * math.sin(math.pi * t) + 8 * math.sin(math.tau * t * 1.7)
        pts.append((x, y))
    _chalk_polyline(img, pts, 0.95, 2.0)
    for i in range(5):
        t = 0.14 + i * 0.18
        if t <= q:
            x = 18 + 94 * t
            y = 82 - 34 * math.sin(math.pi * t) + 8 * math.sin(math.tau * t * 1.7)
            _line(img, [(x, y - 5), (x, y + 5)], _alpha(BRASS, 0.72), 1.0)


def _draw_invariant_loop(img: Image.Image, p: float) -> None:
    phase = math.tau * p
    cx, cy = 64.0, 64.0
    _ellipse(img, (27, 27, 101, 101), outline=_alpha(CHALK, 0.58), width=1.3)
    for k, col in ((0, BRASS), (1, STEEL), (2, OIL_HI)):
        a = phase * (1.0 if k != 1 else -0.7) + k * 2.1
        rx, ry = (34 - k * 4, 18 + k * 3)
        pts = []
        for i in range(36):
            t = math.tau * i / 35
            x, y = rx * math.cos(t), ry * math.sin(t)
            dx, dy = _rot(x, y, a * 0.32)
            pts.append((cx + dx, cy + dy))
        _line(img, pts, _alpha(col, 0.62), 1.2)
    _ellipse(img, (57, 57, 71, 71), fill=BRASS_HI, outline=OUTLINE, width=1.0)
    _ellipse(img, (61, 61, 67, 67), fill=STEEL_DARK)


def _draw_convergence_ticks(img: Image.Image, p: float) -> None:
    q = _ease(p)
    cx, cy = 64.0, 64.0
    for i in range(7):
        side = -1 if i % 2 == 0 else 1
        initial = 48 - i * 3
        x = cx + side * _lerp(initial, 4 + i * 0.5, q)
        h = 7 + (i % 3) * 3
        _line(img, [(x, cy - h), (x, cy + h)], _alpha(CHALK if i < 5 else BRASS, 0.85), 1.4)
    _ellipse(img, (60, 60, 68, 68), fill=_alpha(BRASS_HI, q), outline=_alpha(OUTLINE, q), width=0.8)


def _draw_tolerance_brackets(img: Image.Image, p: float) -> None:
    q = _ease(p)
    off = _lerp(43, 22, q)
    for side in (-1, 1):
        x = 64 + side * off
        inward = -side
        pts = [(x, 38), (x, 90), (x + inward * 12, 90), (x + inward * 12, 86), (x + inward * 4, 86), (x + inward * 4, 42), (x + inward * 12, 42), (x + inward * 12, 38)]
        _line(img, pts, _alpha(STEEL_HI, 0.85), 1.6)
    _line(img, [(42, 64), (86, 64)], _alpha(CHALK, 0.45), 1.0)
    if q > 0.72:
        _ellipse(img, (59, 59, 69, 69), fill=_alpha(BRASS_HI, (q - 0.72) / 0.28), outline=OUTLINE, width=0.8)


def _draw_error_term_collapse(img: Image.Image, p: float) -> None:
    q = _ease(p)
    w = _lerp(42, 4, q)
    _poly(img, [(64 - w, 76), (64 + w, 76), (64, 39 + 20 * q)], fill=_alpha(WARNING, 0.58 * (1 - 0.35 * q)), outline=_alpha(OUTLINE, 0.65), width=1.0)
    _line(img, [(64 - w, 84), (64 + w, 84)], _alpha(CHALK, 0.72), 1.3)
    if q > 0.65:
        a = (q - 0.65) / 0.35
        _ellipse(img, (57, 57, 71, 71), fill=_alpha(BRASS_HI, a), outline=_alpha(OUTLINE, a), width=1.0)


def _draw_bearing_ping(img: Image.Image, p: float) -> None:
    pulse = math.sin(math.pi * p)
    r1, r2 = 10 + 26 * pulse, 18 + 38 * pulse
    for r, col, a in ((r1, BRASS_HI, 0.8), (r2, STEEL, 0.48)):
        _ellipse(img, (64-r,64-r,64+r,64+r), outline=_alpha(col, a * pulse), width=1.4)
    _line(img, [(64, 46), (64, 82)], _alpha(GAUGE_INK, 0.72 * pulse), 1.1)
    _line(img, [(46, 64), (82, 64)], _alpha(GAUGE_INK, 0.72 * pulse), 1.1)
    _ellipse(img, (59,59,69,69), fill=_alpha(STEEL_HI, pulse), outline=_alpha(OUTLINE, pulse), width=0.8)


def _draw_friction_tick(img: Image.Image, p: float) -> None:
    q = _ease(p)
    a = _lerp(-0.35, 0.18, q)
    cx, cy = 58.0, 67.0
    _ellipse(img, (37,46,79,88), fill=_alpha(STEEL_DARK, 0.72), outline=OUTLINE, width=1.2)
    _ellipse(img, (45,54,71,80), fill=_alpha(STEEL_HI, 0.82), outline=OUTLINE, width=1.0)
    _line(img, [(cx,cy), (cx + math.cos(a)*19, cy + math.sin(a)*19)], BRASS_HI, 2.0)
    burst = math.sin(math.pi * p)
    for i in range(5):
        ang = -0.9 + i * 0.34
        r0, r1 = 22, 29 + i
        _line(img, [(cx+math.cos(ang)*r0,cy+math.sin(ang)*r0),(cx+math.cos(ang)*r1,cy+math.sin(ang)*r1)], _alpha(WARNING if i%2 else BRASS_HI, 0.72*burst), 1.2)


def _draw_gauge_sweep(img: Image.Image, p: float) -> None:
    q = _smooth(p)
    cx, cy = 64.0, 78.0
    _arc(img, (25,39,103,117), 200, 340, _alpha(GAUGE,0.88), 3.0)
    _arc(img, (31,45,97,111), 200, 248, _alpha(WARNING,0.9), 2.1)
    _arc(img, (31,45,97,111), 248, 305, _alpha(BRASS_HI,0.9), 2.1)
    _arc(img, (31,45,97,111), 305, 340, _alpha(OIL_HI,0.9), 2.1)
    ang = math.radians(_lerp(205, 315, q))
    _line(img, [(cx,cy),(cx+math.cos(ang)*32,cy+math.sin(ang)*32)], GAUGE_INK, 2.0)
    _ellipse(img, (59,73,69,83), fill=BRASS_HI, outline=OUTLINE, width=0.8)


def _draw_stabilizer_spinup(img: Image.Image, p: float) -> None:
    q = _smooth(p)
    phase = p * math.tau * 1.8
    for r, count, speed, col in ((43,12,1.0,STEEL_HI),(33,9,-1.35,BRASS_HI),(22,6,1.8,OIL_HI)):
        _gear_ticks(img,64,64,r-4,r,count,phase*speed,_alpha(col,0.72),1.6)
    wobble = (1-q)*5.0*math.sin(p*math.tau*3)
    _ellipse(img,(43+wobble,43,85+wobble,85),outline=_alpha(CHALK,0.55),width=1.5)
    for i in range(3):
        a = phase*0.4 + i*math.tau/3
        x,y=64+math.cos(a)*48,64+math.sin(a)*48
        _poly(img,_diamond(x,y,5,8,a),fill=_alpha(BRASS,0.88),outline=OUTLINE,width=0.8)


def _draw_stabilizer_lock(img: Image.Image, p: float) -> None:
    q = _ease(p)
    wobble = (1-q)*4*math.sin(p*math.tau*2)
    _ellipse(img,(31+wobble,31,97+wobble,97),outline=_alpha(STEEL_HI,0.72),width=2.0)
    for i in range(3):
        a = -math.pi/2 + i*math.tau/3
        r = _lerp(49,34,q)
        x,y=64+math.cos(a)*r,64+math.sin(a)*r
        _poly(img,_diamond(x,y,6,10,a),fill=BRASS_HI,outline=OUTLINE,width=1.0)
    if q>0.72:
        flash=(q-0.72)/0.28
        _ellipse(img,(50,50,78,78),outline=_alpha(CHALK_HI,flash),width=2.5)


def _draw_gate_calibration(img: Image.Image, p: float) -> None:
    phase=math.tau*p
    _ellipse(img,(22,22,106,106),outline=_alpha(OIL_HI,0.58),width=2.0)
    _ellipse(img,(31,31,97,97),outline=_alpha(CHALK,0.44),width=1.2)
    _gear_ticks(img,64,64,43,50,12,phase,_alpha(BRASS_HI,0.74),1.2)
    _gear_ticks(img,64,64,28,34,8,-phase*0.65,_alpha(STEEL_HI,0.62),1.0)
    pulse=0.5+0.5*math.sin(phase*2)
    _ellipse(img,(57,57,71,71),fill=_alpha(GAUGE,0.74+0.16*pulse),outline=OUTLINE,width=0.8)
    ang=-math.pi/2+phase*0.15
    _line(img,[(64,64),(64+math.cos(ang)*7,64+math.sin(ang)*7)],GAUGE_INK,1.2)


def _draw_brass_spark(img: Image.Image, p: float) -> None:
    pulse=math.sin(math.pi*p)
    for i in range(8):
        a=i*math.tau/8+0.17
        r0=8+9*pulse
        r1=r0+11+(i%3)*4
        col=BRASS_HI if i%2==0 else STEEL_HI
        _line(img,[(64+math.cos(a)*r0,64+math.sin(a)*r0),(64+math.cos(a)*r1,64+math.sin(a)*r1)],_alpha(col,0.9*pulse),1.6)
    _ellipse(img,(57,57,71,71),fill=_alpha(CHALK_HI,pulse),outline=_alpha(BRASS_DARK,pulse),width=1.0)


def _draw_wrench_strike(img: Image.Image, p: float) -> None:
    q=_ease(p); fade=1-_smooth(max(0,(p-0.5)/0.5))
    _arc(img,(20,24,104,108),205,318,_alpha(STEEL_HI,0.68*fade),3.0)
    x=_lerp(40,78,q); y=_lerp(84,55,q)
    a=-0.58
    _poly(img,[(x-19,y+4),(x+11,y-5),(x+16,y),(x-14,y+10)],fill=_alpha(STEEL,0.8*fade),outline=_alpha(OUTLINE,0.8*fade),width=0.8)
    _ellipse(img,(x+8,y-9,x+23,y+6),outline=_alpha(BRASS_HI,0.86*fade),width=2.0)
    for i in range(4):
        ang=-0.9+i*0.55
        _line(img,[(88,48),(88+math.cos(ang)*18,48+math.sin(ang)*18)],_alpha(BRASS_HI,0.75*fade),1.2)


def _draw_oil_drip(img: Image.Image, p: float) -> None:
    q=_ease(p)
    y=_lerp(34,91,q)
    stretch=_lerp(13,4,_smooth(p))
    _ellipse(img,(58,y-stretch,70,y+7),fill=OIL,outline=OUTLINE,width=1.0)
    _ellipse(img,(60,y-stretch+2,64,y-stretch+7),fill=_alpha(OIL_GLEAM,0.7))
    if p>0.7:
        a=(p-0.7)/0.3
        _ellipse(img,(48-12*a,95-2*a,80+12*a,101+2*a),fill=_alpha(OIL_HI,0.45*a),outline=_alpha(OUTLINE,0.5*a),width=0.8)


def _draw_oil_splash(img: Image.Image, p: float) -> None:
    q=_ease(p); fade=1-_smooth(max(0,(p-0.58)/0.42))
    _ellipse(img,(34-14*q,83,94+14*q,96),fill=_alpha(OIL,0.82*fade),outline=_alpha(OUTLINE,0.65*fade),width=1.0)
    for i in range(7):
        a=math.pi+math.pi*i/6
        rr=_lerp(6,34+(i%2)*7,q)
        x=64+math.cos(a)*rr; y=88+math.sin(a)*rr*0.62
        r=3+(i%3)
        _ellipse(img,(x-r,y-r,x+r,y+r),fill=_alpha(OIL_HI,0.85*fade),outline=_alpha(OUTLINE,0.4*fade),width=0.6)
    _line(img,[(47,86),(77,86)],_alpha(OIL_GLEAM,0.55*fade),1.0)


def _draw_oil_slick(img: Image.Image, p: float) -> None:
    q=_ease(p); fade=1-_smooth(max(0,(p-0.82)/0.18))
    rx=_lerp(10,47,q); ry=_lerp(7,11,q)
    _ellipse(img,(64-rx,79-ry,64+rx,79+ry),fill=_alpha(OIL,0.82*fade),outline=_alpha(OUTLINE,0.58*fade),width=1.0)
    _arc(img,(64-rx*0.65,79-ry*0.6,64+rx*0.55,79+ry*0.45),190,335,_alpha(OIL_GLEAM,0.55*fade),1.2)
    _ellipse(img,(38,76,45,80),fill=_alpha(BRASS_HI,0.24*fade))


def _draw_pressure_vent(img: Image.Image, p: float) -> None:
    q=_ease(p); fade=1-_smooth(max(0,(p-0.64)/0.36))
    ox,oy=22,64
    _ellipse(img,(15,55,29,73),fill=_alpha(BRASS,0.88*fade),outline=_alpha(OUTLINE,0.72*fade),width=1.0)
    _line(img,[(20,64),(33,64)],_alpha(STEEL_HI,0.9*fade),2.0)
    for i in range(6):
        t=(i+1)/6
        x=32+q*t*79
        y=oy+math.sin(i*1.7+p*8)*(4+5*t)
        r=4+7*t
        _ellipse(img,(x-r,y-r*0.65,x+r,y+r*0.65),fill=_alpha(CREAM,0.38*fade*(1-0.45*t)),outline=_alpha(STEEL_HI,0.28*fade),width=0.7)


def _draw_portal_leak(img: Image.Image, p: float) -> None:
    phase=math.tau*p
    cx,cy=64,61
    wob=3.5*math.sin(phase*1.7)
    _ellipse(img,(25+wob,24,103+wob,98),outline=_alpha(OIL_HI,0.72),width=3.0)
    _arc(img,(31-wob,30,97-wob,92),20+phase*18,170+phase*18,_alpha(BRASS_HI,0.52),1.4)
    for i in range(5):
        f=(p+i/5)%1
        x=cx+math.sin(i*1.8+phase)*30
        y=80+f*34
        r=2.4+(i%2)
        _ellipse(img,(x-r,y-r,x+r,y+r),fill=_alpha(OIL,0.75*(1-f)),outline=_alpha(OIL_GLEAM,0.35*(1-f)),width=0.6)
    for i in range(3):
        a=phase+i*math.tau/3
        x,y=cx+math.cos(a)*45,cy+math.sin(a)*38
        _poly(img,_diamond(x,y,2,5,a),fill=_alpha(BRASS_HI,0.62),outline=_alpha(OUTLINE,0.38),width=0.5)


def _draw_unit_circle_rotation(img: Image.Image, p: float) -> None:
    q=_ease(p); a=_lerp(-math.pi*0.85,math.pi*0.35,q)
    cx,cy=64,64; r=38
    _ellipse(img,(cx-r,cy-r,cx+r,cy+r),outline=_alpha(CHALK,0.62),width=1.4)
    _line(img,[(20,64),(108,64)],_alpha(GAUGE_INK,0.42),1.0)
    _line(img,[(64,20),(64,108)],_alpha(GAUGE_INK,0.42),1.0)
    ex,ey=cx+math.cos(a)*r,cy+math.sin(a)*r
    _line(img,[(cx,cy),(ex,ey)],BRASS_HI,2.0)
    _line(img,[(ex,ey),(ex,cy)],_alpha(OIL_GLEAM,0.65),1.2)
    _line(img,[(ex,ey),(cx,ey)],_alpha(STEEL_HI,0.60),1.2)
    _ellipse(img,(ex-4,ey-4,ex+4,ey+4),fill=BRASS_HI,outline=OUTLINE,width=0.8)
    _arc(img,(48,48,80,80),180,180+math.degrees(a)+180,_alpha(CHALK_HI,0.55),1.0)


def _draw_oil_geyser_emerge(img: Image.Image, p: float) -> None:
    q=_ease(p); fade=1-_smooth(max(0,(p-0.72)/0.28))
    ox,oy=22,64
    _ellipse(img,(12,54,28,74),fill=_alpha(BRASS,0.86*fade),outline=_alpha(OUTLINE,0.78*fade),width=1.0)
    _ellipse(img,(19,58,30,70),fill=_alpha(STEEL_HI,0.9*fade),outline=_alpha(OUTLINE,0.5*fade),width=0.8)
    crown_len=_lerp(10,30,q)
    for i,dy in enumerate((-11,-5,0,5,11)):
        x0=26
        x1=26+crown_len*(0.62+0.1*i)
        y0=64+dy*0.25
        y1=64+dy
        w=7-(i%3)
        _line(img,[(x0,y0),(x1,y1)],_alpha(OIL,0.88*fade),w)
        _line(img,[(x0+2,y0-1.2),(x1-2,y1-1.4)],_alpha(OIL_GLEAM,0.42*fade),max(1.0,w*0.22))
    for i in range(5):
        a=-0.8+i*0.4
        r=_lerp(8,20+3*i,q)
        x=28+math.cos(a)*r
        y=64+math.sin(a)*r
        rr=2.0+(i%2)*1.2
        _ellipse(img,(x-rr,y-rr,x+rr,y+rr),fill=_alpha(OIL_HI,0.74*fade),outline=_alpha(OUTLINE,0.35*fade),width=0.6)
    flash=_smooth(min(1,p/0.22))*(1-_smooth(max(0,(p-0.28)/0.24)))
    if flash>0:
        _arc(img,(10,48,38,80),292,68,_alpha(BRASS_HI,0.8*flash),2.0)


def _draw_oil_geyser_stream(img: Image.Image, p: float) -> None:
    phase=math.tau*p
    ox,oy=18,64
    _ellipse(img,(10,55,26,73),fill=_alpha(BRASS,0.78),outline=_alpha(OUTLINE,0.72),width=1.0)
    _ellipse(img,(17,59,27,69),fill=_alpha(STEEL_HI,0.82),outline=_alpha(OUTLINE,0.45),width=0.8)
    upper=[]
    lower=[]
    center=[]
    for i in range(18):
        t=i/17
        x=_lerp(24,106,t)
        sway=math.sin(phase*1.8+t*math.tau*2.1)
        spread=8.5+3.5*math.sin(phase+t*math.tau*1.3)
        cy=64+sway*3.6
        upper.append((x,cy-spread))
        lower.append((x,cy+spread*0.82))
        center.append((x,cy))
    _poly(img, upper + list(reversed(lower)), fill=_alpha(OIL,0.86), outline=_alpha(OUTLINE,0.55), width=1.0)
    _line(img, center, _alpha(OIL_HI,0.52), 5.0)
    gleam=[(x, y-2.3-0.8*math.sin(phase*2+t*11)) for t,(x,y) in zip([i/17 for i in range(18)], center)]
    _line(img, gleam, _alpha(OIL_GLEAM,0.34), 1.5)
    for i in range(7):
        t=(i/7 + p*0.85)%1.0
        x=_lerp(30,102,t)
        y=64+math.sin(t*math.tau*2.6+phase*1.3)*(9+2*(i%2))
        rr=1.8+(i%3)*0.65
        _ellipse(img,(x-rr,y-rr,x+rr,y+rr),fill=_alpha(OIL_HI,0.7*(1-0.22*t)),outline=_alpha(OUTLINE,0.22),width=0.5)


def _draw_oil_geyser_impact(img: Image.Image, p: float) -> None:
    q=_ease(p); fade=1-_smooth(max(0,(p-0.58)/0.42))
    cx,cy=92,64
    _ellipse(img,(cx-10-14*q,cy-8-10*q,cx+10+18*q,cy+8+10*q),fill=_alpha(OIL,0.82*fade),outline=_alpha(OUTLINE,0.62*fade),width=1.0)
    for i in range(8):
        a=-2.25+i*0.42
        r0=9+6*q
        r1=_lerp(16,34+(i%3)*3,q)
        x0,y0=cx+math.cos(a)*r0,cy+math.sin(a)*r0
        x1,y1=cx+math.cos(a)*r1,cy+math.sin(a)*r1
        w=4-(i%3)*0.7
        _line(img,[(x0,y0),(x1,y1)],_alpha(OIL_HI,0.72*fade),w)
    for i in range(9):
        a=-1.9+i*0.36
        r=_lerp(10,36+(i%2)*5,q)
        x=cx+math.cos(a)*r
        y=cy+math.sin(a)*r*0.82
        rr=2.2+(i%3)*0.8
        _ellipse(img,(x-rr,y-rr,x+rr,y+rr),fill=_alpha(OIL_HI,0.82*fade),outline=_alpha(OUTLINE,0.35*fade),width=0.6)
    _line(img,[(cx-18,cy),(cx+14,cy)],_alpha(OIL_GLEAM,0.44*fade),1.6)
    shove=max(0.0,1-abs(p-0.28)/0.28)
    if shove>0:
        _arc(img,(76,44,116,84),242,118,_alpha(BRASS_HI,0.58*shove),1.4)


DRAWERS = {
    "chalk_spiral": _draw_chalk_spiral,
    "curve_trace": _draw_curve_trace,
    "invariant_loop": _draw_invariant_loop,
    "convergence_ticks": _draw_convergence_ticks,
    "tolerance_brackets": _draw_tolerance_brackets,
    "error_term_collapse": _draw_error_term_collapse,
    "bearing_ping": _draw_bearing_ping,
    "friction_tick": _draw_friction_tick,
    "gauge_sweep": _draw_gauge_sweep,
    "stabilizer_spinup": _draw_stabilizer_spinup,
    "stabilizer_lock": _draw_stabilizer_lock,
    "gate_calibration": _draw_gate_calibration,
    "brass_spark": _draw_brass_spark,
    "wrench_strike": _draw_wrench_strike,
    "oil_drip": _draw_oil_drip,
    "oil_splash": _draw_oil_splash,
    "oil_slick": _draw_oil_slick,
    "pressure_vent": _draw_pressure_vent,
    "portal_leak": _draw_portal_leak,
    "unit_circle_rotation": _draw_unit_circle_rotation,
    "oil_geyser_emerge": _draw_oil_geyser_emerge,
    "oil_geyser_stream": _draw_oil_geyser_stream,
    "oil_geyser_impact": _draw_oil_geyser_impact,
}


def _origin_for(anim: str) -> Point:
    if anim in {"oil_splash", "oil_slick"}:
        return 64.0, 89.0
    if anim == "oil_drip":
        return 64.0, 32.0
    if anim in {"pressure_vent", "oil_geyser_emerge", "oil_geyser_stream"}:
        return 22.0, 64.0
    if anim == "oil_geyser_impact":
        return 92.0, 64.0
    if anim in {"wrench_strike", "brass_spark", "friction_tick"}:
        return 64.0, 64.0
    return 64.0, 64.0


def _progress(anim: str, frame_idx: int, frames: int) -> float:
    return frame_idx / max(1, frames) if anim in LOOPS else frame_idx / max(1, frames - 1)


def _phase(anim: str, p: float) -> str:
    if anim in LOOPS:
        return "loop"
    if anim in {"oil_splash", "brass_spark", "wrench_strike", "friction_tick", "oil_geyser_impact"}:
        return "impact" if p < 0.34 else "dissipate"
    if anim in {"stabilizer_spinup", "gauge_sweep", "convergence_ticks", "tolerance_brackets"}:
        return "calibrate" if p < 0.72 else "settle"
    if anim in {"oil_drip"}:
        return "stretch" if p < 0.45 else "fall"
    return "form" if p < 0.45 else "resolve"


def _draw_frame(anim: str, frame_idx: int, frames: int) -> Image.Image:
    p = _progress(anim, frame_idx, frames)
    if anim not in LOOPS and frame_idx == frames - 1:
        return Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    DRAWERS[anim](img, p)
    return img.resize(FRAME_SIZE, Image.Resampling.NEAREST)


def _frame_meta(anim: str, frame_idx: int, frames: int) -> dict:
    p = _progress(anim, frame_idx, frames)
    ox, oy = _origin_for(anim)
    anchors = {"origin": {"x": ox, "y": oy}}
    if anim == "oil_geyser_stream":
        anchors["target"] = {"x": 104.0, "y": 64.0}
    placement = EFFECT_SPECS[anim]["placement"]
    if placement in {"surface_contact", "contact_point", "surface_or_feature_point", "target_point", "feature_point"}:
        anchors["contact"] = {"x": ox, "y": oy}
    if placement == "emitter_socket":
        anchors["emitter"] = {"x": ox, "y": oy}
    return {
        "anchors": anchors,
        "effect": {
            "family": EFFECT_SPECS[anim]["family"],
            "phase": _phase(anim, p),
            "progress": round(p, 4),
            "clear_frame": bool(anim not in LOOPS and frame_idx == frames - 1),
        },
    }


def _authoring_document() -> dict:
    row_info = {name: (frames, duration) for name, frames, duration in ROWS}
    animations = {}
    for name, spec in EFFECT_SPECS.items():
        frames, duration = row_info[name]
        animations[name] = {
            **spec,
            "frame_count": frames,
            "frame_duration_ms": duration,
            "total_duration_ms": frames * duration,
            "origin_anchor": "origin",
            "completion_hint": "loop_until_cancelled" if spec["loop"] else "despawn_after_clear_frame",
        }
    return {
        "schema": "ambition.sprite_vfx_authoring",
        "schema_version": 1,
        "target": TARGET_NAME,
        "status": "authoring_hints_not_yet_runtime_contract",
        "character_context": "Oiler: Euler-inspired practical gate mechanic; curves, tolerances, bearings, oil, brass/steel instrumentation.",
        "auto_registration": {
            "mechanism": "public module under targets/props exporting render",
            "central_registry_edit_required": False,
        },
        "runtime_promotion_notes": [
            "Frame timing and translated anchors are authoritative now.",
            "Promote orientation, attachment, lifecycle, blend, and SFX cue fields only as generic presentation concepts shared across many effects.",
            "Do not special-case Oiler animation names in the engine.",
            "gravity_down, surface_normal, and surface_tangent are semantic author frames; presentation resolves them against the controlled body's/world geometry.",
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
    return [outputs["spritesheet"], outputs["yaml"], outputs["ron"], outputs["actor"], authoring, outputs["preview"], outputs["canonical"], outputs["canonical_transparent"]]


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME, ROWS, _draw_frame, Path(out_dir), frame_size=FRAME_SIZE, crop_margin=5)
