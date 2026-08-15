"""Detached presentation VFX authored for George Boo'l / George Booul.

George is a bedsheet ghost parody of George Boole.  His detached effects should
therefore read in two languages at once:

* **ghost comedy** — pale cloth wisps, eye-hole silhouettes, little spectral
  afterimages, and a compact BOO-like surprise beat without needing text; and
* **Boolean logic** — clean 0/1 sigils, binary inversion, paired inputs,
  implication arrows, bivalence, contradiction, and especially the law of the
  excluded middle used by his Up-B.

This module authors content only.  It deliberately does not bind the effects to
runtime moves.  The generated ``george_booul_vfx_authoring.yaml`` sidecar keeps
move/event timing hints next to the art so an integration pass can consume them
through a generic presentation mapping rather than hard-coding George in the
renderer.

Up-B timing is copied from ``george_booul_moveset.rs``:

* ``excluded_middle_windup`` is exactly 180 ms, matching ``ASCENT_AT_S``;
* launch effects synchronize to the Set impulse at 0.18 s;
* ``excluded_middle_ascent`` is 448 ms, approximately the authored
  ``ASCENT_SPEED / gravity`` time-to-apex under baseline tuning;
* the committed move runs until 1.15 s, so ``excluded_middle_tail`` is authored
  as a subdued aftermath/tail rather than a second launch.

Rows are one-shot unless declared in ``LOOPS``.  One-shots end on a fully clear
frame.  Directional rows author +X as forward.  Surface-relative rows use an
explicit contact anchor.  Author-owned semantics beyond current runtime frame
anchors remain advisory until the engine promotes them generically.
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

TARGET_NAME = "george_booul_vfx"
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

# Rows deliberately keep short gameplay punctuation compact.  Up-B windup is
# pinned to the move's exact 0.18 s authored startup.
ROWS: List[Tuple[str, int, int]] = [
    ("boo_pop", 7, 52),
    ("true_sigil", 6, 58),
    ("false_sigil", 6, 58),
    ("binary_toggle", 8, 56),
    ("not_inversion", 8, 54),
    ("and_converge", 8, 56),
    ("xor_split", 8, 56),
    ("ghost_afterimage", 8, 68),
    ("proof_collapse", 8, 62),
    ("bivalence_weak", 6, 52),
    ("bivalence_strong", 7, 52),
    ("modus_ponens_dash", 8, 48),
    ("modus_ponens_impact", 6, 44),
    ("excluded_middle_windup", 4, 45),
    ("excluded_middle_launch", 6, 42),
    ("excluded_middle_ascent", 7, 64),
    ("excluded_middle_gate", 8, 56),
    ("excluded_middle_tail", 10, 67),
    ("reductio_drop", 7, 48),
    ("reductio_impact", 6, 50),
    ("reductio_bounce", 7, 48),
]

LOOPS = {"ghost_afterimage"}

# George's character palette: TRUE is pale cloth + green logic, FALSE is the
# charcoal inversion + hot eye-orange.  Cyan/violet belong to ghost translucency
# rather than to a generic magical palette.
INK = (22, 26, 31, 255)
INK_SOFT = (60, 67, 76, 220)
TRUE = (239, 245, 234, 255)
TRUE_HI = (255, 255, 249, 255)
TRUE_SHADOW = (181, 201, 190, 255)
FALSE = (46, 44, 54, 255)
FALSE_HI = (83, 75, 93, 255)
FALSE_SHADOW = (25, 25, 32, 255)
LOGIC_GREEN = (113, 231, 135, 255)
LOGIC_GREEN_HI = (211, 255, 201, 255)
LOGIC_RED = (244, 96, 63, 255)
LOGIC_GOLD = (246, 214, 109, 255)
GHOST_CYAN = (151, 232, 232, 255)
GHOST_HI = (225, 255, 250, 255)
GHOST_VIOLET = (171, 137, 211, 255)

ACTOR_METADATA = {
    "actor": {
        "character_id": "fx_george_booul_vfx",
        "display_name": "George Boo'l Detached VFX",
    },
    "body": {
        "body_plan": "Effect",
        "body_kind": "Overlay",
        "mass_class": "Light",
        "locomotion_hint": "Stationary",
        "traits": ["fx", "overlay", "presentation", "george_booul", "boolean", "ghost"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "sockets": {
        "origin": {
            "source": f"{TARGET_NAME}.geometry",
            "point": {"x": 64.0, "y": 64.0},
        },
    },
    "tags": ["fx", "overlay", "presentation", "george_booul", "boolean", "ghost"],
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
    move_id: str | None = None,
    event_hint: str = "presentation_event",
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
        "move_id_hint": move_id,
        "event_hint": event_hint,
        "attachment_hint": attachment,
        "layer_hint": layer,
        "blend_mode_hint": blend,
        "nominal_span_px": size,
        "sfx_cue_hint": sfx,
        "requires_character_context": True,
    }


EFFECT_SPECS: Dict[str, dict] = {
    "boo_pop": _spec(
        "ghost_comedy",
        "Compact spectral surprise punctuation: eye holes and a sheet-like scallop pop out of a ghost ring.",
        placement="feature_point",
        relationship="impact",
        event_hint="surprise_or_taunt_beat",
        blend="alpha_or_additive",
        size=82,
        sfx="vfx.george_booul.boo_pop",
    ),
    "true_sigil": _spec(
        "boolean_state",
        "Affirmative TRUE/1 mark: pale ring, green 1, and a restrained confirmation flash.",
        placement="feature_point",
        relationship="active",
        event_hint="state_true_confirmed",
        size=66,
        sfx="vfx.george_booul.true_sigil",
    ),
    "false_sigil": _spec(
        "boolean_state",
        "FALSE/0 mark: charcoal disk with orange-red zero and inverted ghost accent.",
        placement="feature_point",
        relationship="active",
        event_hint="state_false_confirmed",
        size=66,
        sfx="vfx.george_booul.false_sigil",
    ),
    "binary_toggle": _spec(
        "boolean_operator",
        "TRUE and FALSE exchange sides while the central state flips; useful for George's palette/state transition.",
        placement="entity_origin",
        relationship="active",
        event_hint="boolean_state_toggle",
        attachment="follow_source_optional",
        size=92,
        sfx="vfx.george_booul.binary_toggle",
    ),
    "not_inversion": _spec(
        "boolean_operator",
        "Unary NOT: a state disk crosses through a diagonal negation slash and returns inverted.",
        placement="entity_origin",
        relationship="active",
        move_id="not_fade",
        event_hint="not_operator_applied",
        attachment="follow_source_optional",
        size=88,
        sfx="vfx.george_booul.not_inversion",
    ),
    "and_converge": _spec(
        "boolean_operator",
        "Two binary inputs converge through a bracket/gate and resolve to one green TRUE output.",
        placement="effect_origin",
        relationship="release",
        move_id="and_zap",
        event_hint="and_inputs_resolve",
        size=104,
        sfx="vfx.george_booul.and_converge",
    ),
    "xor_split": _spec(
        "boolean_operator",
        "Exclusive split: paired 0/1 paths cross and only the mismatched pair remains lit.",
        placement="effect_origin",
        relationship="active",
        event_hint="exclusive_choice",
        size=104,
        sfx="vfx.george_booul.xor_split",
    ),
    "ghost_afterimage": _spec(
        "ghost_motion",
        "Looping translucent sheet-ghost echoes for hover, fade, fast displacement, or recovery travel.",
        placement="entity_origin",
        orientation="positive_x_is_forward",
        mirror_x=True,
        loop=True,
        relationship="sustain",
        event_hint="fast_ghost_motion",
        attachment="follow_source",
        layer="behind_source",
        blend="alpha_or_additive",
        size=108,
        sfx="vfx.george_booul.ghost_afterimage.loop",
    ),
    "proof_collapse": _spec(
        "logic_failure",
        "A tidy binary proof grid loses support and collapses like George's defeated bedsheet.",
        placement="entity_origin",
        relationship="aftermath",
        event_hint="invalid_proposition_or_defeat",
        size=104,
        sfx="vfx.george_booul.proof_collapse",
    ),
    "bivalence_weak": _spec(
        "special_bivalence",
        "Neutral-B's early answer: small TRUE/FALSE half-disks disagree in a compact weak pop.",
        placement="entity_origin",
        relationship="active",
        move_id="bivalence",
        event_hint="active_window_early",
        attachment="follow_source_optional",
        size=82,
        sfx="vfx.george_booul.bivalence_weak",
    ),
    "bivalence_strong": _spec(
        "special_bivalence",
        "Neutral-B's late answer: the same two-valued proposition resolves into a much larger throw ring.",
        placement="entity_origin",
        relationship="release",
        move_id="bivalence",
        event_hint="active_window_late_0.42s",
        attachment="follow_source_optional",
        size=114,
        sfx="vfx.george_booul.bivalence_strong",
    ),
    "modus_ponens_dash": _spec(
        "special_implication",
        "Directional implication: source proposition, arrow, and destination proposition lock into one horizontal charge.",
        placement="entity_origin",
        orientation="positive_x_is_forward",
        mirror_x=True,
        relationship="active",
        move_id="modus_ponens",
        event_hint="set_impulse_0.20s",
        attachment="follow_source",
        layer="behind_source",
        size=118,
        sfx="vfx.george_booul.modus_ponens_dash",
    ),
    "modus_ponens_impact": _spec(
        "special_implication",
        "The implication arrow arrives and stamps the consequent into a hard contact bracket.",
        placement="contact_point",
        orientation="positive_x_is_forward",
        mirror_x=True,
        relationship="impact",
        move_id="modus_ponens",
        event_hint="hit_contact",
        size=92,
        sfx="vfx.george_booul.modus_ponens_impact",
    ),
    "excluded_middle_windup": _spec(
        "up_b_excluded_middle",
        "Exact 180 ms Up-B tell: FALSE/0 and TRUE/1 occupy opposite halves and squeeze out the middle.",
        placement="entity_origin",
        relationship="startup",
        move_id="excluded_middle",
        event_hint="move_press_0.00_to_impulse_0.18s",
        attachment="follow_source",
        size=104,
        sfx="vfx.george_booul.up_b.windup",
    ),
    "excluded_middle_launch": _spec(
        "up_b_excluded_middle",
        "The Up-B Set impulse resolves the proposition: a binary split snaps vertical and ejects George upward.",
        placement="entity_origin",
        orientation="gravity_up",
        relationship="release",
        move_id="excluded_middle",
        event_hint="impulse_set_at_0.18s",
        attachment="world_locked_after_spawn",
        blend="alpha_or_additive",
        size=116,
        sfx="vfx.george_booul.up_b.launch",
    ),
    "excluded_middle_ascent": _spec(
        "up_b_excluded_middle",
        "Approximately one time-to-apex of binary ladder marks and spectral wake after the commanded rise.",
        placement="entity_origin",
        orientation="gravity_up",
        relationship="active",
        move_id="excluded_middle",
        event_hint="start_at_impulse_nominal_448ms",
        attachment="follow_source",
        layer="behind_source",
        blend="alpha_or_additive",
        size=116,
        sfx="vfx.george_booul.up_b.ascent",
    ),
    "excluded_middle_gate": _spec(
        "up_b_excluded_middle",
        "Two Boolean walls labelled by shape as 0 and 1 part to create one narrow vertical escape corridor: no middle state.",
        placement="entity_origin",
        orientation="gravity_up",
        relationship="active",
        move_id="excluded_middle",
        event_hint="layer_at_impulse_during_ascent",
        attachment="follow_source_optional",
        layer="behind_source",
        blend="alpha_or_additive",
        size=124,
        sfx="vfx.george_booul.up_b.gate",
    ),
    "excluded_middle_tail": _spec(
        "up_b_excluded_middle",
        "Subdued post-launch logic fragments and ghost wisps peel away across the exact 0.48 s to 1.15 s committed recovery tail; not a second boost.",
        placement="entity_origin",
        orientation="gravity_up",
        mirror_x=True,
        relationship="aftermath",
        move_id="excluded_middle",
        event_hint="recovery_tail_after_active_window_until_1.15s",
        attachment="follow_source",
        layer="behind_source",
        size=100,
        sfx="vfx.george_booul.up_b.tail",
    ),
    "reductio_drop": _spec(
        "special_contradiction",
        "Down-B assumption plunges toward contradiction: TRUE and FALSE converge into one downward wedge.",
        placement="entity_origin",
        orientation="gravity_down",
        relationship="active",
        move_id="reductio",
        event_hint="set_downward_impulse_0.16s",
        attachment="follow_source",
        layer="behind_source",
        size=112,
        sfx="vfx.george_booul.reductio_drop",
    ),
    "reductio_impact": _spec(
        "special_contradiction",
        "The contradiction lands: 0 and 1 occupy the same contact point and explode into a hard X/bracket mark.",
        placement="contact_point",
        orientation="surface_normal",
        mirror_x=True,
        relationship="impact",
        move_id="reductio",
        event_hint="hit_contact",
        size=104,
        sfx="vfx.george_booul.reductio_impact",
    ),
    "reductio_bounce": _spec(
        "special_contradiction",
        "On-hit pogo consequence: the contradiction reverses into an upward proof-tree rebound.",
        placement="contact_point",
        orientation="gravity_up",
        relationship="aftermath",
        move_id="reductio",
        event_hint="pogo_bounce_on_hit",
        size=106,
        sfx="vfx.george_booul.reductio_bounce",
    ),
}


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _mul_alpha(c: RGBA, a: float) -> RGBA:
    a = max(0.0, min(1.0, a))
    return c[0], c[1], c[2], int(round(c[3] * a))


def _clamp(t: float) -> float:
    return max(0.0, min(1.0, t))


def _smooth(t: float) -> float:
    t = _clamp(t)
    return t * t * (3.0 - 2.0 * t)


def _ease_out(t: float) -> float:
    t = _clamp(t)
    return 1.0 - (1.0 - t) ** 3


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ellipse(img: Image.Image, box: Sequence[float], *, fill: RGBA | None = None, outline: RGBA | None = None, width: float = 1.0) -> None:
    layer, draw = overlay_draw(img)
    draw.ellipse(tuple(_s(v) for v in box), fill=fill, outline=outline, width=max(1, _s(width)))
    img.alpha_composite(layer)


def _line(img: Image.Image, points: Sequence[Point], *, fill: RGBA, width: float = 1.0) -> None:
    layer, draw = overlay_draw(img)
    draw.line([(_s(x), _s(y)) for x, y in points], fill=fill, width=max(1, _s(width)), joint="curve")
    img.alpha_composite(layer)


def _polygon(img: Image.Image, points: Sequence[Point], *, fill: RGBA | None = None, outline: RGBA | None = None, width: float = 1.0) -> None:
    layer, draw = overlay_draw(img)
    pts = [(_s(x), _s(y)) for x, y in points]
    draw.polygon(pts, fill=fill)
    if outline and len(pts) > 1:
        draw.line(pts + [pts[0]], fill=outline, width=max(1, _s(width)), joint="curve")
    img.alpha_composite(layer)


def _arc(img: Image.Image, box: Sequence[float], start: float, end: float, *, fill: RGBA, width: float = 1.0) -> None:
    layer, draw = overlay_draw(img)
    draw.arc(tuple(_s(v) for v in box), start=start, end=end, fill=fill, width=max(1, _s(width)))
    img.alpha_composite(layer)


def _digit_zero(img: Image.Image, cx: float, cy: float, r: float, color: RGBA, alpha: float = 1.0, width: float = 3.0) -> None:
    _ellipse(img, (cx - r * 0.72, cy - r, cx + r * 0.72, cy + r), outline=_mul_alpha(color, alpha), width=width)


def _digit_one(img: Image.Image, cx: float, cy: float, r: float, color: RGBA, alpha: float = 1.0, width: float = 3.0) -> None:
    col = _mul_alpha(color, alpha)
    _line(img, [(cx - r * 0.25, cy - r * 0.58), (cx + r * 0.12, cy - r), (cx + r * 0.12, cy + r)], fill=col, width=width)
    _line(img, [(cx - r * 0.40, cy + r), (cx + r * 0.45, cy + r)], fill=col, width=width)


def _bit_disk(img: Image.Image, cx: float, cy: float, r: float, bit: int, alpha: float = 1.0, *, inverted: bool = False) -> None:
    if bit:
        fill = FALSE if inverted else TRUE
        mark = LOGIC_RED if inverted else LOGIC_GREEN
        outline = FALSE_HI if inverted else TRUE_SHADOW
    else:
        fill = TRUE if inverted else FALSE
        mark = LOGIC_GREEN if inverted else LOGIC_RED
        outline = TRUE_SHADOW if inverted else FALSE_HI
    _ellipse(img, (cx - r, cy - r, cx + r, cy + r), fill=_mul_alpha(fill, 0.92 * alpha), outline=_mul_alpha(outline, 0.82 * alpha), width=1.3)
    if bit:
        _digit_one(img, cx, cy, r * 0.57, mark, alpha, max(1.4, r * 0.11))
    else:
        _digit_zero(img, cx, cy, r * 0.57, mark, alpha, max(1.4, r * 0.11))


def _ghost_face(img: Image.Image, cx: float, cy: float, scale: float, alpha: float = 1.0) -> None:
    # Minimal detached bedsheet silhouette: rounded cap, scalloped hem, two eye
    # holes. This intentionally echoes the character without becoming a second
    # body sprite.
    w = 34 * scale
    h = 36 * scale
    points = [
        (cx - w * 0.50, cy + h * 0.35),
        (cx - w * 0.47, cy - h * 0.10),
        (cx - w * 0.34, cy - h * 0.42),
        (cx, cy - h * 0.58),
        (cx + w * 0.34, cy - h * 0.42),
        (cx + w * 0.47, cy - h * 0.10),
        (cx + w * 0.50, cy + h * 0.35),
        (cx + w * 0.30, cy + h * 0.22),
        (cx + w * 0.12, cy + h * 0.42),
        (cx - w * 0.08, cy + h * 0.23),
        (cx - w * 0.27, cy + h * 0.43),
    ]
    _polygon(img, points, fill=_mul_alpha(TRUE, 0.55 * alpha), outline=_mul_alpha(GHOST_CYAN, 0.78 * alpha), width=1.2)
    eye_y = cy - h * 0.16
    for ex in (cx - w * 0.14, cx + w * 0.14):
        _ellipse(img, (ex - 2.3 * scale, eye_y - 4.0 * scale, ex + 2.3 * scale, eye_y + 4.0 * scale), fill=_mul_alpha(INK, 0.92 * alpha))


def _arrow(img: Image.Image, x0: float, y0: float, x1: float, y1: float, color: RGBA, alpha: float, width: float = 2.0) -> None:
    _line(img, [(x0, y0), (x1, y1)], fill=_mul_alpha(color, alpha), width=width)
    a = math.atan2(y1 - y0, x1 - x0)
    h = 8.0
    _polygon(
        img,
        [
            (x1, y1),
            (x1 - math.cos(a - 0.55) * h, y1 - math.sin(a - 0.55) * h),
            (x1 - math.cos(a + 0.55) * h, y1 - math.sin(a + 0.55) * h),
        ],
        fill=_mul_alpha(color, alpha),
    )


def _draw_boo_pop(img: Image.Image, p: float) -> None:
    q = math.sin(math.pi * _clamp(p)) ** 0.72
    fade = 1.0 - _smooth(max(0.0, (p - 0.60) / 0.40))
    r = _lerp(12, 45, _ease_out(p))
    _ellipse(img, (64-r, 64-r, 64+r, 64+r), outline=_mul_alpha(GHOST_CYAN, 0.64 * fade), width=_lerp(3.2, 1.1, p))
    _ghost_face(img, 64, 64, 0.55 + q * 0.78, fade)
    for i in range(5):
        a = -0.9 + i * 0.45
        rr = 30 + 20 * _ease_out(p)
        _line(img, [(64 + math.cos(a)*rr, 64 + math.sin(a)*rr), (64 + math.cos(a)*(rr+8), 64 + math.sin(a)*(rr+8))], fill=_mul_alpha(LOGIC_GOLD, 0.55 * fade), width=1.2)


def _draw_sigill(img: Image.Image, p: float, bit: int) -> None:
    pulse = math.sin(math.pi * _clamp(p)) ** 0.62
    fade = 1.0 - _smooth(max(0.0, (p - 0.72) / 0.28))
    r = 8 + 23 * pulse
    _bit_disk(img, 64, 64, r, bit, fade)
    ring = r + 6 + 8 * pulse
    _ellipse(img, (64-ring,64-ring,64+ring,64+ring), outline=_mul_alpha(LOGIC_GREEN if bit else LOGIC_RED, 0.38 * fade), width=1.0)


def _draw_binary_toggle(img: Image.Image, p: float) -> None:
    q = _smooth(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.82) / 0.18))
    # Paths cross vertically to make the state exchange unmistakable.
    x0, x1 = 38.0, 90.0
    y_a = _lerp(44.0, 84.0, q)
    y_b = _lerp(84.0, 44.0, q)
    _arc(img, (25, 29, 103, 99), 205, 335, fill=_mul_alpha(GHOST_VIOLET, 0.36 * fade), width=1.2)
    _arc(img, (25, 29, 103, 99), 25, 155, fill=_mul_alpha(GHOST_CYAN, 0.36 * fade), width=1.2)
    _bit_disk(img, _lerp(x0,64,q), y_a, 12, 1 if p < 0.5 else 0, fade)
    _bit_disk(img, _lerp(x1,64,q), y_b, 12, 0 if p < 0.5 else 1, fade)
    if 0.38 < p < 0.66:
        _ellipse(img, (55,55,73,73), fill=_mul_alpha(TRUE_HI, 0.72 * fade), outline=_mul_alpha(LOGIC_GOLD, 0.68 * fade), width=1.2)


def _draw_not_inversion(img: Image.Image, p: float) -> None:
    q = _smooth(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.82) / 0.18))
    bit = 1 if p < 0.50 else 0
    _bit_disk(img, 64, 64, 25, bit, fade, inverted=p > 0.50)
    slash = 18 + 28 * math.sin(math.pi * p)
    _line(img, [(64-slash,64+slash),(64+slash,64-slash)], fill=_mul_alpha(LOGIC_RED if p < 0.5 else LOGIC_GREEN, 0.82 * fade), width=3.2)
    _ellipse(img, (34,34,94,94), outline=_mul_alpha(GHOST_CYAN, 0.30 * fade), width=1.0)


def _draw_and_converge(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.78) / 0.22))
    left = (30 + 20*q, 45 + 16*q)
    right = (98 - 20*q, 83 - 16*q)
    _bit_disk(img, *left, 11, 1, fade)
    _bit_disk(img, *right, 11, 1, fade)
    # Curved gate bracket, then resolved output.
    _arc(img, (47,37,84,91), 270, 90, fill=_mul_alpha(LOGIC_GREEN, 0.58 * fade), width=2.3)
    if p > 0.36:
        outq = _smooth((p - 0.36) / 0.64)
        _arrow(img, 68,64, 92,64, LOGIC_GREEN_HI, 0.62*fade*outq, 1.8)
        _bit_disk(img, 103,64, 10+5*outq, 1, fade*outq)


def _draw_xor_split(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.76) / 0.24))
    _bit_disk(img, 44, 64, 12, 1 if int(p*8)%2==0 else 0, fade)
    _bit_disk(img, 84, 64, 12, 0 if int(p*8)%2==0 else 1, fade)
    # Crossed paths pull apart instead of converging.
    _line(img, [(48,52),(80,76)], fill=_mul_alpha(LOGIC_GREEN, 0.56*fade), width=1.8)
    _line(img, [(48,76),(80,52)], fill=_mul_alpha(LOGIC_RED, 0.56*fade), width=1.8)
    spread = 17 + 25*q
    _digit_one(img, 64-spread, 33, 7, LOGIC_GREEN_HI, 0.65*fade, 1.4)
    _digit_zero(img, 64+spread, 95, 7, LOGIC_RED, 0.65*fade, 1.4)


def _draw_ghost_afterimage(img: Image.Image, p: float) -> None:
    phase = math.tau * p
    for i in range(4):
        f = (p + i / 4.0) % 1.0
        x = 94 - 58 * f
        y = 64 + math.sin(phase + i*1.3) * 6
        alpha = (1.0 - f) * 0.72
        _ghost_face(img, x, y, 0.72 + 0.10*math.sin(phase+i), alpha)
        _digit_one(img, x+8, y+24, 5, LOGIC_GREEN, alpha*0.55, 1.0)
        _digit_zero(img, x-9, y+26, 5, LOGIC_RED, alpha*0.45, 1.0)


def _draw_proof_collapse(img: Image.Image, p: float) -> None:
    q = _smooth(p)
    fade = 1.0 - _smooth(max(0.0, (p - 0.78) / 0.22))
    for row in range(3):
        y = 36 + row*22 + q*q*(row+1)*14
        for col in range(4):
            x = 34 + col*20 + math.sin((row*4+col)*1.7)*q*4
            bit = (row + col) % 2
            _bit_disk(img, x, y, 6.2, bit, fade*(1-0.12*row))
    # The once-straight proof bars buckle downward.
    for row in range(2):
        y = 47 + row*22 + q*q*(row+1)*15
        _line(img, [(27,y),(101,y+5*q*math.sin(row+1))], fill=_mul_alpha(INK_SOFT,0.52*fade), width=1.0)


def _draw_bivalence(img: Image.Image, p: float, strong: bool) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0, (p - (0.62 if strong else 0.72)) / (0.38 if strong else 0.28)))
    r = _lerp(10, 52 if strong else 34, q)
    # Two semicircular answers; no blended middle color.
    layer, draw = overlay_draw(img)
    box = tuple(_s(v) for v in (64-r,64-r,64+r,64+r))
    draw.pieslice(box, 90, 270, fill=_mul_alpha(FALSE,0.82*fade), outline=_mul_alpha(FALSE_HI,0.82*fade))
    draw.pieslice(box, -90, 90, fill=_mul_alpha(TRUE,0.82*fade), outline=_mul_alpha(TRUE_SHADOW,0.82*fade))
    img.alpha_composite(layer)
    _digit_zero(img, 64-r*0.34,64,r*0.34,LOGIC_RED,fade, max(1.1,r*0.07))
    _digit_one(img, 64+r*0.34,64,r*0.34,LOGIC_GREEN,fade, max(1.1,r*0.07))
    _ellipse(img,(64-r-6,64-r-6,64+r+6,64+r+6),outline=_mul_alpha(LOGIC_GOLD if strong else GHOST_CYAN,0.44*fade),width=2.1 if strong else 1.2)


def _draw_modus_dash(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0 - _smooth(max(0.0,(p-0.70)/0.30))
    _bit_disk(img, 24,64,11,1,fade)
    _arrow(img, 37,64, 97,64, LOGIC_GREEN_HI, 0.82*fade, 2.7)
    _bit_disk(img, 107,64,11,1,fade)
    # Implication trail consists of alternating binary remnants rather than smoke.
    for i in range(5):
        x = 28 + i*14 - 18*q
        y = 47 + (i%2)*34
        if i%2:
            _digit_zero(img,x,y,4.8,LOGIC_RED,0.32*fade,1.0)
        else:
            _digit_one(img,x,y,4.8,LOGIC_GREEN,0.32*fade,1.0)


def _draw_modus_impact(img: Image.Image, p: float) -> None:
    q = _ease_out(p)
    fade = 1.0-_smooth(max(0.0,(p-0.62)/0.38))
    _arrow(img, 24,64, 69+23*q,64, LOGIC_GREEN_HI, 0.85*fade, 3.1)
    x=92
    _line(img,[(x,34),(x,94)],fill=_mul_alpha(LOGIC_GOLD,0.82*fade),width=3.0)
    _line(img,[(x,34),(108,34)],fill=_mul_alpha(LOGIC_GOLD,0.82*fade),width=2.0)
    _line(img,[(x,94),(108,94)],fill=_mul_alpha(LOGIC_GOLD,0.82*fade),width=2.0)
    _bit_disk(img, 104,64, 10+7*q,1,fade)


def _draw_upb_windup(img: Image.Image, p: float) -> None:
    q=_smooth(p)
    # FALSE and TRUE walls squeeze toward the body. The narrowing middle is the
    # readable tell; the launch frame then blows the corridor upward.
    lx=_lerp(25,47,q); rx=_lerp(103,81,q)
    _bit_disk(img,lx,64,14,0,1.0)
    _bit_disk(img,rx,64,14,1,1.0)
    _line(img,[(64,24),(64,104)],fill=_mul_alpha(LOGIC_GOLD,0.28+0.62*q),width=1.0+2.0*q)
    _arc(img,(39,36,89,92),110,250,fill=_mul_alpha(LOGIC_RED,0.46*q),width=1.6)
    _arc(img,(39,36,89,92),-70,70,fill=_mul_alpha(LOGIC_GREEN,0.46*q),width=1.6)
    if p>0.55:
        _ghost_face(img,64,67,0.58,0.28+0.40*q)


def _draw_upb_launch(img: Image.Image, p: float) -> None:
    q=_ease_out(p); fade=1.0-_smooth(max(0.0,(p-0.68)/0.32))
    # Vertical commanded impulse: bright center ray, split Boolean lobes, sheet
    # ghost echo already leaving the origin.
    h=_lerp(18,102,q)
    _line(img,[(64,96),(64,96-h)],fill=_mul_alpha(GHOST_HI,0.92*fade),width=_lerp(5.0,1.5,q))
    _arrow(img,64,84,64,22,LOGIC_GOLD,0.72*fade,2.1)
    _bit_disk(img,45,75-24*q,11,0,fade)
    _bit_disk(img,83,75-24*q,11,1,fade)
    _ellipse(img,(35-8*q,79-6*q,93+8*q,104+4*q),outline=_mul_alpha(GHOST_CYAN,0.48*fade),width=2.1)
    _ghost_face(img,64,57-16*q,0.52,0.52*fade)


def _draw_upb_ascent(img: Image.Image, p: float) -> None:
    q=_ease_out(p); fade=1.0-_smooth(max(0.0,(p-0.78)/0.22))
    # Binary ladder trails downward as the origin climbs. Keep the body itself out
    # of the detached effect; a small ghost cap suggests source motion only.
    for i in range(7):
        y=100 - i*12 + q*18
        a=fade*(0.75-i*0.07)
        if i%2:
            _digit_zero(img,51,y,5.5,LOGIC_RED,a,1.1)
            _digit_one(img,77,y,5.5,LOGIC_GREEN,a,1.1)
        else:
            _digit_one(img,51,y,5.5,LOGIC_GREEN,a,1.1)
            _digit_zero(img,77,y,5.5,LOGIC_RED,a,1.1)
        _line(img,[(58,y),(70,y)],fill=_mul_alpha(GHOST_CYAN,0.22*a),width=1.0)
    _ghost_face(img,64,31,0.48,0.46*fade)
    _line(img,[(64,42),(64,87)],fill=_mul_alpha(GHOST_CYAN,0.34*fade),width=1.2)


def _draw_upb_gate(img: Image.Image, p: float) -> None:
    q=_smooth(p); fade=1.0-_smooth(max(0.0,(p-0.80)/0.20))
    gap=_lerp(8,28,q)
    # Charcoal FALSE wall and pale TRUE wall physically part, leaving exactly one
    # route. The effect works without literal text.
    _polygon(img,[(18,22),(64-gap,22),(64-gap,106),(18,106)],fill=_mul_alpha(FALSE,0.26*fade),outline=_mul_alpha(LOGIC_RED,0.52*fade),width=1.2)
    _polygon(img,[(64+gap,22),(110,22),(110,106),(64+gap,106)],fill=_mul_alpha(TRUE,0.22*fade),outline=_mul_alpha(LOGIC_GREEN,0.52*fade),width=1.2)
    _digit_zero(img,34,64,14,LOGIC_RED,0.62*fade,2.2)
    _digit_one(img,94,64,14,LOGIC_GREEN,0.62*fade,2.2)
    _arrow(img,64,93,64,27,GHOST_HI,0.72*fade,1.8)


def _draw_upb_tail(img: Image.Image, p: float) -> None:
    q=_ease_out(p); fade=1.0-_smooth(max(0.0,(p-0.66)/0.34))
    for i in range(6):
        a=math.pi*0.18+i*0.55
        rr=_lerp(10,38+i*2,q)
        x=64+math.cos(a)*rr
        y=54+math.sin(a)*rr+18*q
        alpha=(0.55-i*0.055)*fade
        if i%2:
            _digit_zero(img,x,y,4.4,LOGIC_RED,alpha,0.9)
        else:
            _digit_one(img,x,y,4.4,LOGIC_GREEN,alpha,0.9)
    _ghost_face(img,64,55+18*q,0.58,0.28*fade)


def _draw_reductio_drop(img: Image.Image, p: float) -> None:
    q=_ease_out(p); fade=1.0-_smooth(max(0.0,(p-0.72)/0.28))
    _bit_disk(img,42,35+42*q,11,1,fade)
    _bit_disk(img,86,35+42*q,11,0,fade)
    _line(img,[(42,48+32*q),(64,93)],fill=_mul_alpha(LOGIC_GREEN,0.52*fade),width=1.7)
    _line(img,[(86,48+32*q),(64,93)],fill=_mul_alpha(LOGIC_RED,0.52*fade),width=1.7)
    _arrow(img,64,55,64,105,LOGIC_GOLD,0.76*fade,2.4)


def _draw_reductio_impact(img: Image.Image, p: float) -> None:
    q=_ease_out(p); fade=1.0-_smooth(max(0.0,(p-0.62)/0.38))
    r=_lerp(14,48,q)
    _line(img,[(64-r,64-r),(64+r,64+r)],fill=_mul_alpha(LOGIC_RED,0.78*fade),width=3.0)
    _line(img,[(64-r,64+r),(64+r,64-r)],fill=_mul_alpha(LOGIC_GREEN,0.78*fade),width=3.0)
    _bit_disk(img,64,64,12+7*(1-q),0,fade)
    _digit_one(img,64,64,8,LOGIC_GREEN_HI,0.88*fade,1.7)
    _ellipse(img,(64-r-6,64-r-6,64+r+6,64+r+6),outline=_mul_alpha(GHOST_CYAN,0.34*fade),width=1.1)


def _draw_reductio_bounce(img: Image.Image, p: float) -> None:
    q=_ease_out(p); fade=1.0-_smooth(max(0.0,(p-0.72)/0.28))
    _arrow(img,64,96,64,29,LOGIC_GOLD,0.76*fade,2.3)
    # Reversed proof-tree: one contradiction at contact branches back into two
    # propositions as George rebounds.
    _bit_disk(img,64,93,9,0,fade)
    _digit_one(img,64,93,6,LOGIC_GREEN_HI,0.82*fade,1.3)
    spread=10+23*q
    _line(img,[(64,80),(64-spread,47)],fill=_mul_alpha(LOGIC_RED,0.55*fade),width=1.6)
    _line(img,[(64,80),(64+spread,47)],fill=_mul_alpha(LOGIC_GREEN,0.55*fade),width=1.6)
    _bit_disk(img,64-spread,39,10,0,fade)
    _bit_disk(img,64+spread,39,10,1,fade)


DRAWERS = {
    "boo_pop": _draw_boo_pop,
    "true_sigil": lambda img,p: _draw_sigill(img,p,1),
    "false_sigil": lambda img,p: _draw_sigill(img,p,0),
    "binary_toggle": _draw_binary_toggle,
    "not_inversion": _draw_not_inversion,
    "and_converge": _draw_and_converge,
    "xor_split": _draw_xor_split,
    "ghost_afterimage": _draw_ghost_afterimage,
    "proof_collapse": _draw_proof_collapse,
    "bivalence_weak": lambda img,p: _draw_bivalence(img,p,False),
    "bivalence_strong": lambda img,p: _draw_bivalence(img,p,True),
    "modus_ponens_dash": _draw_modus_dash,
    "modus_ponens_impact": _draw_modus_impact,
    "excluded_middle_windup": _draw_upb_windup,
    "excluded_middle_launch": _draw_upb_launch,
    "excluded_middle_ascent": _draw_upb_ascent,
    "excluded_middle_gate": _draw_upb_gate,
    "excluded_middle_tail": _draw_upb_tail,
    "reductio_drop": _draw_reductio_drop,
    "reductio_impact": _draw_reductio_impact,
    "reductio_bounce": _draw_reductio_bounce,
}


def _origin_for(anim: str) -> Point:
    if anim in {"modus_ponens_dash", "modus_ponens_impact"}:
        return (24.0, 64.0)
    if anim in {"reductio_impact", "reductio_bounce"}:
        return (64.0, 94.0)
    if anim in {"excluded_middle_launch", "excluded_middle_ascent", "excluded_middle_gate", "excluded_middle_tail"}:
        return (64.0, 84.0)
    return (64.0, 64.0)


def _frame_progress(anim: str, frame_idx: int, nframes: int) -> float:
    if anim in LOOPS:
        return frame_idx / max(1, nframes)
    return frame_idx / max(1, nframes - 1)


def _phase(anim: str, p: float) -> str:
    if anim in LOOPS:
        return "sustain"
    if anim == "excluded_middle_windup":
        return "compress"
    if anim == "excluded_middle_launch":
        return "resolve" if p < 0.45 else "launch"
    if anim in {"excluded_middle_ascent", "excluded_middle_gate"}:
        return "ascent"
    if anim == "excluded_middle_tail":
        return "committed_tail"
    if anim == "reductio_drop":
        return "assumption" if p < 0.5 else "contradiction"
    if anim == "reductio_bounce":
        return "reversal"
    if p < 0.20:
        return "onset"
    if p < 0.66:
        return "active"
    return "dissipate"


def _intensity(anim: str, p: float) -> float:
    if anim in LOOPS:
        return round(0.66 + 0.16 * (0.5 + 0.5 * math.sin(math.tau*p)),4)
    if anim == "excluded_middle_windup":
        return round(0.35 + 0.65*_smooth(p),4)
    if anim in {"excluded_middle_launch", "reductio_impact", "bivalence_strong"}:
        return round(math.sin(math.pi*_clamp(p))**0.45,4)
    return round(max(0.0,1.0-0.68*_smooth(p)),4)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    p = _frame_progress(anim, frame_idx, nframes)
    if anim not in LOOPS and frame_idx == nframes - 1:
        return Image.new("RGBA", FRAME_SIZE, (0,0,0,0))
    img = Image.new("RGBA", (W,H), (0,0,0,0))
    try:
        DRAWERS[anim](img,p)
    except KeyError as exc:
        raise ValueError(f"unknown animation: {anim}") from exc
    return img.resize(FRAME_SIZE, Image.Resampling.NEAREST)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    p=_frame_progress(anim,frame_idx,nframes)
    ox,oy=_origin_for(anim)
    anchors={"origin":{"x":ox,"y":oy}}
    placement=EFFECT_SPECS[anim]["placement"]
    if placement=="contact_point":
        anchors["contact"]={"x":ox,"y":oy}
    if placement=="feature_point":
        anchors["feature"]={"x":ox,"y":oy}
    return {
        "anchors":anchors,
        "effect":{
            "family":EFFECT_SPECS[anim]["family"],
            "phase":_phase(anim,p),
            "progress":round(p,4),
            "intensity_hint":_intensity(anim,p),
            "clear_frame":bool(anim not in LOOPS and frame_idx==nframes-1),
        },
    }


def _frame_notes(anim: str, nframes: int) -> List[dict]:
    return [
        {
            "frame":i,
            "phase":_phase(anim,_frame_progress(anim,i,nframes)),
            "progress":round(_frame_progress(anim,i,nframes),4),
            "intensity_hint":_intensity(anim,_frame_progress(anim,i,nframes)),
            "clear_frame":bool(anim not in LOOPS and i==nframes-1),
        }
        for i in range(nframes)
    ]


def _authoring_document() -> dict:
    rows={name:(frames,duration) for name,frames,duration in ROWS}
    animations={}
    for name,spec in EFFECT_SPECS.items():
        nframes,duration=rows[name]
        animations[name]={
            **spec,
            "frame_count":nframes,
            "frame_duration_ms":duration,
            "total_duration_ms":nframes*duration,
            "origin_anchor":"origin",
            "completion_hint":"loop_until_cancelled" if spec["loop"] else "despawn_after_clear_frame",
            "frames":_frame_notes(name,nframes),
        }
    return {
        "schema":"ambition.sprite_vfx_authoring",
        "schema_version":1,
        "target":TARGET_NAME,
        "character_context":{
            "character_id":"smash_george_booul",
            "display_name":"George Booul / George Boo'l",
            "parody":"George Boole as a classic bedsheet ghost; boo is the pun",
            "visual_language":"binary TRUE/FALSE logic plus restrained spectral comedy",
        },
        "status":"authoring_hints_not_yet_runtime_contract",
        "coordinate_space":"logical_frame_pixels; manifest anchors are translated through auto-crop/trim",
        "move_timing_notes":{
            "excluded_middle":{
                "up_b":True,
                "windup_ms":180,
                "set_impulse_at_ms":180,
                "ascent_speed_units_per_s":1020,
                "nominal_time_to_apex_ms":450,
                "committed_until_ms":1150,
                "content_rule":"one save, not flight; tail must read as commitment rather than a second boost",
            },
            "modus_ponens":{"set_horizontal_impulse_at_ms":200},
            "reductio":{"set_downward_impulse_at_ms":160,"on_hit_technique":"pogo_bounce"},
            "bivalence":{"early_active_at_ms":300,"late_active_at_ms":420},
        },
        "author_owned_fields":[
            "frame timing and semantic anchors",
            "move/event synchronization hints",
            "startup/active/impact/sustain/release/aftermath relationship",
            "orientation and attachment intent",
            "loop/completion intent",
            "blend/layer hints",
            "paired SFX cue suggestion",
            "visual phase and intensity",
        ],
        "runtime_promotion_notes":[
            "Current runtime manifests preserve frame anchors but not the arbitrary effect payload or this sidecar.",
            "Treat row timing and anchors as authoritative now; do not re-measure pivots from alpha bounds.",
            "Promote move-event binding as a generic content mapping. Do not add George-specific branches to rendering or movement code.",
            "Up-B launch should synchronize to the authored Set impulse at 0.18 s, not to a guessed animation frame.",
            "The windup is intentionally exactly 180 ms so visual and audio tell can span press-to-impulse without retiming.",
            "The ascent assets orient to gravity-up. Camera rotation and local gravity belong to presentation transforms, not duplicated sprite rows.",
            "One-shots end clear. ghost_afterimage is periodic and may loop while the source is in the corresponding presentation state.",
        ],
        "animations":animations,
    }


def write_authoring_sidecar(out_dir: Path) -> Path:
    path=out_dir/AUTHORING_FILE
    path.write_text(safe_dump(_authoring_document(),sort_keys=False,width=120),encoding="utf8")
    return path


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    outputs=build_sheet(
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
    authoring=write_authoring_sidecar(out_dir)
    return [outputs["spritesheet"],outputs["yaml"],outputs["ron"],outputs["actor"],authoring,outputs["preview"],outputs["canonical"],outputs["canonical_transparent"]]


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME,ROWS,_draw_frame,Path(out_dir),frame_size=FRAME_SIZE,crop_margin=5)
