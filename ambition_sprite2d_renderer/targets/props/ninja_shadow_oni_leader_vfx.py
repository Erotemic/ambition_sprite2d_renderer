"""Detached VFX for the Shadow Oni Leader.

The leader's visual language comes from his authored voice and silhouette:
instant answers, one-breath timing, quiet footwork, the red oni eye, sheathed
katana precision, smoke folds, and disciplined shadow pressure.  The effects
avoid generic spellcasting and preserve the character's counter-puncher shape.
"""

from __future__ import annotations

import math
from pathlib import Path

from ._character_vfx_common import (
    Canvas,
    fade,
    make_spec,
    mix,
    publish_canonical,
    publish_catalog,
    pulse,
    sheet_files,
    smooth,
    window,
)

TARGET_NAME = "ninja_shadow_oni_leader_vfx"
SHEET_FILES = sheet_files(TARGET_NAME)
FRAME_SIZE = (144, 144)

ROWS = [
    ("shadow_answer_slash", 6, 42),
    ("breath_warning", 8, 60),
    ("oni_eye_flash", 6, 48),
    ("silent_step", 7, 48),
    ("blink_depart", 8, 46),
    ("blink_arrive", 8, 46),
    ("smoke_fold", 10, 64),
    ("iaijutsu_glint", 6, 40),
    ("counter_ring", 7, 46),
    ("missed_answer_cut", 7, 50),
    ("oni_mask_echo", 9, 54),
    ("gaze_lock", 10, 64),
    ("command_seal", 8, 58),
    ("shadow_veil", 12, 64),
]

OUTLINE = (17, 19, 26, 255)
CLOTH = (98, 105, 112, 255)
CLOTH_LIGHT = (184, 190, 194, 255)
ARMOR = (67, 74, 82, 255)
SHADOW = (8, 10, 15, 255)
SMOKE = (70, 80, 97, 255)
SASH = (109, 66, 94, 255)
SASH_HOT = (161, 90, 126, 255)
EYE = (229, 20, 36, 255)
EYE_HOT = (255, 107, 90, 255)
BLADE = (239, 244, 246, 255)
BLADE_SHADOW = (168, 176, 181, 255)
BRASS = (177, 140, 56, 255)


def _arc_points(center, radius: float, start: float, sweep: float, segments: int = 18):
    return [(center[0] + math.cos(start + sweep * i / segments) * radius, center[1] + math.sin(start + sweep * i / segments) * radius) for i in range(segments + 1)]


def _smoke_crescent(c: Canvas, center, radius: float, angle: float, alpha: float, width: float = 5.0) -> None:
    c.line(_arc_points(center, radius, angle - 0.75, 1.50), fade(SMOKE, alpha), width)
    c.line(_arc_points(center, radius - width * 0.5, angle - 0.62, 1.24), fade(CLOTH_LIGHT, alpha * 0.18), 0.8)


def _oni_mask(c: Canvas, center, scale: float, alpha: float) -> None:
    x, y = center
    c.polygon([(x - 22 * scale, y - 11 * scale), (x - 12 * scale, y - 25 * scale), (x, y - 18 * scale), (x + 12 * scale, y - 25 * scale), (x + 22 * scale, y - 11 * scale), (x + 17 * scale, y + 18 * scale), (x, y + 27 * scale), (x - 17 * scale, y + 18 * scale)], fill=fade(ARMOR, 0.20 * alpha), outline=fade(CLOTH_LIGHT, 0.62 * alpha), width=1.2)
    c.line([(x - 18 * scale, y - 13 * scale), (x - 26 * scale, y - 31 * scale), (x - 13 * scale, y - 23 * scale)], fade(BLADE_SHADOW, 0.72 * alpha), 2.0 * scale)
    c.line([(x + 18 * scale, y - 13 * scale), (x + 26 * scale, y - 31 * scale), (x + 13 * scale, y - 23 * scale)], fade(BLADE_SHADOW, 0.72 * alpha), 2.0 * scale)
    c.line([(x - 12 * scale, y - 2 * scale), (x - 3 * scale, y + 1 * scale)], fade(EYE_HOT, alpha), 2.2 * scale)
    c.line([(x + 12 * scale, y - 2 * scale), (x + 3 * scale, y + 1 * scale)], fade(EYE_HOT, alpha), 2.2 * scale)
    c.line([(x - 8 * scale, y + 15 * scale), (x - 3 * scale, y + 9 * scale)], fade(BLADE, 0.60 * alpha), 1.6 * scale)
    c.line([(x + 8 * scale, y + 15 * scale), (x + 3 * scale, y + 9 * scale)], fade(BLADE, 0.60 * alpha), 1.6 * scale)


def _shadow_answer_slash(c: Canvas, p: float) -> None:
    q = window(p, 0.24)
    center = (60, 78)
    sweep = 0.35 + 1.8 * smooth(p)
    pts = _arc_points(center, 50, -1.16, sweep, 22)
    c.line(pts, fade(SHADOW, 0.64 * q), 10.0)
    c.line(pts, fade(BLADE_SHADOW, 0.70 * q), 3.2)
    c.line(_arc_points(center, 47, -1.13, sweep, 22), fade(BLADE, q), 1.2)
    tip = pts[-1]
    c.star(tip, 6 + 5 * q, fade(EYE_HOT, q), points=4, inner=0.14, rotation=-0.2)


def _breath_warning(c: Canvas, p: float) -> None:
    q = window(p, 0.46)
    # One exhale and one red bead: "one breath left" without literal text.
    for i in range(5):
        phase = max(0.0, min(1.0, p * 1.35 - i * 0.09))
        x = 48 + phase * 54 + i * 2
        y = 74 - math.sin(phase * math.pi) * (8 + i)
        r = 4 + phase * 5
        c.ellipse((x, y), r, r * 0.65, fill=fade(CLOTH_LIGHT, q * 0.10 * (1 - phase)), outline=fade(SMOKE, q * 0.42 * (1 - phase * 0.5)), width=0.8)
    bead = 4 + 5 * (1 - abs(2 * p - 1))
    c.ellipse((38, 72), bead, fill=fade(EYE, q), outline=fade(EYE_HOT, q), width=1.0)
    c.arc((38, 72), 14 + p * 8, 14 + p * 8, 235, 485, fade(EYE_HOT, q * 0.45), 1.0)


def _oni_eye_flash(c: Canvas, p: float) -> None:
    q = window(p, 0.16)
    c.polygon([(25, 72), (55, 58), (94, 61), (119, 72), (91, 82), (54, 83)], fill=fade(SHADOW, 0.70 * q))
    c.polygon([(39, 72), (61, 66), (88, 67), (105, 72), (87, 76), (60, 77)], fill=fade(EYE, 0.82 * q))
    c.line([(47, 72), (100, 72)], fade(EYE_HOT, q), 2.2)
    c.star((103, 72), 8 + 8 * q, fade(EYE_HOT, q), points=4, inner=0.12, rotation=0.0)


def _silent_step(c: Canvas, p: float) -> None:
    q = window(p, 0.35)
    base_y = 91
    # A footfall is suggested only by two thin pressure crescents and a scarf-like wake.
    for i in range(3):
        r = 13 + p * 24 + i * 9
        c.arc((58, base_y), r, r * 0.30, 200, 340, fade(SMOKE, q * (0.48 - i * 0.10)), 1.2)
    c.line([(32, 75), (59 + p * 48, 68), (42 + p * 58, 82)], fade(SASH, q * 0.30), 3.0)
    c.ellipse((58, 89), 3.0, 1.6, fill=fade(CLOTH_LIGHT, q * 0.45))


def _blink_depart(c: Canvas, p: float) -> None:
    q = window(p, 0.42)
    shrink = 1.0 - 0.72 * smooth(p)
    for i in range(4):
        a = -0.8 + i * 0.53
        _smoke_crescent(c, (72, 76), 42 * shrink + i * 5, a + p * 0.7, q * (0.62 - i * 0.08), 5.0)
    c.line([(72, 39 + p * 26), (72, 109 - p * 26)], fade(EYE, q * (0.72 + 0.22 * (1 - p))), 1.5)
    c.star((72, 74), 7 * shrink + 2, fade(EYE_HOT, q), points=4, inner=0.12)


def _blink_arrive(c: Canvas, p: float) -> None:
    q = window(p, 0.58)
    grow = 0.28 + 0.72 * smooth(p)
    for i in range(4):
        a = 2.3 - i * 0.53
        _smoke_crescent(c, (72, 76), 20 + 24 * grow + i * 4, a - p * 0.65, q * (0.58 - i * 0.07), 5.0)
    c.line([(72, 56 - p * 18), (72, 92 + p * 18)], fade(EYE, q * (0.62 + 0.30 * p)), 1.6)
    c.star((72, 74), 4 + 7 * grow, fade(BLADE, q * 0.62), points=4, inner=0.12)


def _smoke_fold(c: Canvas, p: float) -> None:
    beat = pulse(p)
    for i in range(6):
        a = p * math.tau * (1 if i % 2 == 0 else -1) + i * 0.92
        r = 24 + i * 5 + math.sin(p * math.tau + i) * 3
        center = (72 + math.cos(a) * r * 0.35, 74 + math.sin(a) * r * 0.22)
        _smoke_crescent(c, center, 20 + i * 3, a + math.pi * 0.5, 0.30 + 0.16 * beat - i * 0.025, 6.0)
    c.ellipse((72, 74), 9 + beat * 3, fill=fade(SHADOW, 0.34 + 0.16 * beat))


def _iaijutsu_glint(c: Canvas, p: float) -> None:
    q = window(p, 0.12)
    # Deliberately tiny and punctual: the blade was already drawn by the time it is noticed.
    c.line([(27, 86), (118, 54)], fade(BLADE_SHADOW, q * 0.58), 2.0)
    c.line([(43, 80), (105, 59)], fade(BLADE, q), 0.9)
    center = (86, 66)
    c.star(center, 10 + 14 * q, fade(BLADE, q), points=4, inner=0.10, rotation=-0.32)
    c.star(center, 5 + 6 * q, fade(EYE_HOT, q * 0.76), points=4, inner=0.12, rotation=0.48)


def _counter_ring(c: Canvas, p: float) -> None:
    q = window(p, 0.22)
    center = (72, 72)
    r = 13 + 41 * smooth(p)
    c.ellipse(center, r, outline=fade(BLADE, q * 0.90), width=1.8)
    c.ellipse(center, r * 0.72, outline=fade(EYE, q * 0.58), width=1.1)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        c.line([(72 + math.cos(a) * (r - 8), 72 + math.sin(a) * (r - 8)), (72 + math.cos(a) * (r + 8), 72 + math.sin(a) * (r + 8))], fade(BLADE_SHADOW, q * 0.55), 1.0)
    c.star(center, 7 + 7 * q, fade(EYE_HOT, q), points=4, inner=0.15)


def _missed_answer_cut(c: Canvas, p: float) -> None:
    q = window(p, 0.30)
    x = 25 + p * 82
    c.line([(x - 34, 104), (x + 32, 38)], fade(SHADOW, q * 0.48), 8.0)
    c.line([(x - 32, 103), (x + 31, 40)], fade(BLADE_SHADOW, q * 0.64), 2.0)
    # Delayed red echo emphasizes the cost of whiffing the one instant.
    lag_x = x - 18
    c.line([(lag_x - 20, 96), (lag_x + 22, 54)], fade(EYE, q * 0.32 * p), 1.2)


def _oni_mask_echo(c: Canvas, p: float) -> None:
    q = window(p, 0.48)
    scale = 0.42 + 0.74 * smooth(p)
    _oni_mask(c, (72, 72), scale, q * (1.0 - 0.18 * p))
    if p > 0.35:
        echo = smooth((p - 0.35) / 0.65)
        _oni_mask(c, (72, 72), scale + echo * 0.36, q * (1 - echo) * 0.26)


def _gaze_lock(c: Canvas, p: float) -> None:
    beat = 0.68 + 0.32 * pulse(p)
    center = (72, 72)
    c.ellipse(center, 38 + beat * 4, 18 + beat * 2, outline=fade(SASH_HOT, 0.35 * beat), width=1.0)
    c.polygon([(37, 72), (57, 62), (88, 62), (107, 72), (88, 82), (57, 82)], fill=fade(SHADOW, 0.36 * beat), outline=fade(CLOTH, 0.30 * beat), width=0.8)
    c.line([(50, 72), (94, 72)], fade(EYE, 0.86 * beat), 2.0)
    c.ellipse(center, 3.5 + beat * 1.5, fill=fade(EYE_HOT, 0.95 * beat))
    for i in range(4):
        a = i * math.pi / 2 + p * 0.35
        c.line([(72 + math.cos(a) * 45, 72 + math.sin(a) * 24), (72 + math.cos(a) * 53, 72 + math.sin(a) * 30)], fade(BLADE_SHADOW, 0.36 * beat), 1.0)


def _command_seal(c: Canvas, p: float) -> None:
    q = window(p, 0.42)
    r = 18 + smooth(p) * 27
    center = (72, 72)
    c.ellipse(center, r, outline=fade(EYE, q * 0.74), width=2.0)
    # Four disciplined blade wedges: command, not magic rune soup.
    for i in range(4):
        a = -math.pi / 2 + i * math.pi / 2
        tip = (72 + math.cos(a) * r * 0.82, 72 + math.sin(a) * r * 0.82)
        left = (72 + math.cos(a + 0.32) * r * 0.34, 72 + math.sin(a + 0.32) * r * 0.34)
        right = (72 + math.cos(a - 0.32) * r * 0.34, 72 + math.sin(a - 0.32) * r * 0.34)
        c.polygon([tip, left, right], fill=fade(BLADE_SHADOW, q * 0.42), outline=fade(BLADE, q * 0.72), width=0.8)
    c.star(center, 8 + 5 * q, fade(EYE_HOT, q), points=4, inner=0.20, rotation=math.pi / 4)


def _shadow_veil(c: Canvas, p: float) -> None:
    beat = pulse(p)
    # Repeating descending cloth/smoke bands. It should feel like pressure around the leader, not a fire aura.
    for i in range(7):
        phase = (p + i / 7) % 1.0
        y = 28 + phase * 90
        width = 26 + 34 * (1 - abs(phase * 2 - 1))
        xoff = math.sin(p * math.tau + i * 1.3) * 8
        c.arc((72 + xoff, y), width, 12 + i * 0.7, 185, 355, fade(SHADOW, 0.20 + 0.12 * (1 - phase)), 6.0)
        c.arc((72 - xoff * 0.5, y + 2), width - 7, 8, 190, 350, fade(SMOKE, 0.14 + 0.10 * beat), 1.3)
    c.line([(72, 45), (72, 99)], fade(EYE, 0.12 + 0.08 * beat), 0.8)


DRAWERS = {
    "shadow_answer_slash": _shadow_answer_slash,
    "breath_warning": _breath_warning,
    "oni_eye_flash": _oni_eye_flash,
    "silent_step": _silent_step,
    "blink_depart": _blink_depart,
    "blink_arrive": _blink_arrive,
    "smoke_fold": _smoke_fold,
    "iaijutsu_glint": _iaijutsu_glint,
    "counter_ring": _counter_ring,
    "missed_answer_cut": _missed_answer_cut,
    "oni_mask_echo": _oni_mask_echo,
    "gaze_lock": _gaze_lock,
    "command_seal": _command_seal,
    "shadow_veil": _shadow_veil,
}

SPECS = {
    "shadow_answer_slash": make_spec("counter_cut", "A fast dark katana arc that ends in a red answer-glint; visualizes the leader replying rather than opening.", placement="source", orientation="positive_x_is_forward", mirror_x=True, relationship="active", extra_anchor="emitter", size=126),
    "breath_warning": make_spec("breath", "Single restrained exhale plus one red timing bead, referencing the leader's one-breath warning.", placement="target", orientation="positive_x_is_forward", mirror_x=True, relationship="startup", extra_anchor="target", size=110),
    "oni_eye_flash": make_spec("gaze", "Horizontal oni-eye slit flashes once; useful for reads, target acquisition, and punish confirmation.", placement="source", orientation="positive_x_is_forward", mirror_x=True, relationship="startup", extra_anchor="origin", size=110),
    "silent_step": make_spec("footwork", "Almost-empty pressure crescents and a sash-like wake for a step whose point is how little noise/visual mass it makes.", placement="surface", orientation="positive_x_is_forward", mirror_x=True, relationship="active", extra_anchor="contact", size=116),
    "blink_depart": make_spec("blink", "Smoke crescents fold inward around a narrowing red vertical seam at disappearance.", placement="source", relationship="release", size=116),
    "blink_arrive": make_spec("blink", "Inverse smoke fold and blade-white seam at reappearance.", placement="source", relationship="aftermath", size=116),
    "smoke_fold": make_spec("smoke", "Looping layered smoke crescents fold over one another instead of generic radial smoke particles.", loop=True, placement="source", attachment="source_follow", relationship="sustain", size=126),
    "iaijutsu_glint": make_spec("katana", "Tiny punctual draw-cut glint: the visible instant is intentionally shorter and smaller than a normal slash trail.", placement="hit_point", orientation="positive_x_is_forward", mirror_x=True, relationship="impact", extra_anchor="contact", size=112),
    "counter_ring": make_spec("counter", "Two precise concentric response rings with diagonal timing ticks and a red center flash.", placement="hit_point", relationship="impact", extra_anchor="contact", size=118),
    "missed_answer_cut": make_spec("whiff", "Blade-space scar followed by a delayed red echo, emphasizing the long commitment after the instant active window misses.", placement="world", orientation="positive_x_is_forward", mirror_x=True, relationship="aftermath", size=132),
    "oni_mask_echo": make_spec("oni", "Leader-mask silhouette appears as a restrained afterimage with horns, tusks, and the authored red eyes.", placement="source", relationship="release", size=120),
    "gaze_lock": make_spec("gaze", "Looping compressed eye geometry exerts target pressure without turning into a magical aura.", loop=True, placement="target", attachment="target_follow", relationship="sustain", extra_anchor="target", size=116),
    "command_seal": make_spec("command", "Red circular command mark built from four blade wedges, visually echoing an order obeyed instantly.", placement="world", relationship="release", size=118),
    "shadow_veil": make_spec("shadow", "Looping descending dark cloth/smoke bands for persistent leader pressure, defensive focus, or pre-counter sustain.", loop=True, placement="source", attachment="source_follow", relationship="sustain", size=126),
}

ORIGINS = {name: (72.0, 72.0) for name, _, _ in ROWS}
ORIGINS.update({
    "shadow_answer_slash": (60.0, 78.0),
    "breath_warning": (38.0, 72.0),
    "silent_step": (58.0, 91.0),
    "iaijutsu_glint": (86.0, 66.0),
    "counter_ring": (72.0, 72.0),
})


def render(out_dir: str | Path, **opts):
    del opts
    return publish_catalog(
        target_name=TARGET_NAME,
        display_name="Shadow Oni Leader Detached VFX",
        character_context_id="npc_ninja_shadow_oni_leader",
        character_context_display="Shadow Oni Leader",
        rows=ROWS,
        drawers=DRAWERS,
        specs=SPECS,
        origins=ORIGINS,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
    )


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return publish_canonical(
        target_name=TARGET_NAME,
        rows=ROWS,
        drawers=DRAWERS,
        specs=SPECS,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
    )
