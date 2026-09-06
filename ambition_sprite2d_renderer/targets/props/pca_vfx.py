"""Detached discrete-generation VFX for the Perfect Cellular Automaton.

Every effect advances in visible cellular generations.  The sheet avoids smooth
particle drift as a primary visual grammar: cells are born, die, propagate,
oscillate, settle, or corrupt in explicit local-rule steps.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

from ._character_vfx_common import (
    Canvas,
    fade,
    make_spec,
    publish_canonical,
    publish_catalog,
    sheet_files,
    window,
)

TARGET_NAME = "pca_vfx"
SHEET_FILES = sheet_files(TARGET_NAME)
FRAME_SIZE = (144, 144)

ROWS = [
    ("cell_birth", 9, 54),
    ("cell_death", 9, 54),
    ("rule_front", 11, 58),
    ("glider_launch", 10, 50),
    ("glider_impact", 10, 48),
    ("oscillator_pulse", 12, 68),
    ("still_life_lock", 10, 58),
    ("garden_growth", 12, 60),
    ("causal_cone_expand", 11, 56),
    ("causal_cone_collapse", 11, 56),
    ("fixed_point_acquire", 11, 58),
    ("phase_boundary", 12, 66),
    ("generation_wipe", 10, 50),
    ("corruption_seed", 12, 64),
]

OUTLINE = (8, 16, 15, 255)
ACID = (182, 243, 74, 255)
ACID_LIGHT = (232, 255, 175, 255)
EMERALD = (19, 122, 90, 255)
EMERALD_DARK = (13, 59, 49, 255)
VIOLET = (112, 70, 168, 255)
VIOLET_LIGHT = (182, 108, 227, 255)
MAGENTA = (240, 92, 184, 255)
CYAN = (84, 216, 232, 255)
CERAMIC = (239, 232, 207, 255)


def _cell(c: Canvas, x: float, y: float, size: float, color, alpha: float = 1.0, fill_alpha: float = 0.36) -> None:
    h = size * 0.5
    c.rect(
        (x - h, y - h, x + h, y + h),
        fill=fade(color, fill_alpha * alpha),
        outline=fade(ACID_LIGHT, 0.82 * alpha),
        width=0.65,
    )


def _rule110_step(row: Sequence[int]) -> list[int]:
    bits = (0, 1, 1, 0, 1, 1, 1, 0)
    n = len(row)
    return [bits[(int(row[(i - 1) % n]) << 2) | (int(row[i]) << 1) | int(row[(i + 1) % n])] for i in range(n)]


def _rule_rows(width: int, steps: int, seed: int = 0) -> list[list[int]]:
    row = [0] * width
    row[width // 2] = 1
    if width > 5:
        row[(width // 2 + 2 + seed) % width] = 1
    rows = [row]
    for _ in range(steps - 1):
        row = _rule110_step(row)
        rows.append(row)
    return rows


def _glider_cells(cx: float, cy: float, size: float, mirror: bool = False) -> list[tuple[float, float]]:
    pattern = ((1, 0), (2, 1), (0, 2), (1, 2), (2, 2))
    s = -1.0 if mirror else 1.0
    return [(cx + s * (x - 1) * size, cy + (y - 1) * size) for x, y in pattern]


def _cell_birth(c: Canvas, p: float) -> None:
    q = window(p, 0.52)
    generation = min(5, int(p * 6.5))
    patterns = [
        [(0, 0)],
        [(0, 0), (-1, 0), (1, 0)],
        [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)],
        [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, 0), (-2, 0), (2, 0)],
        [(-2, -1), (-1, -1), (1, -1), (2, -1), (-2, 1), (-1, 1), (1, 1), (2, 1), (0, 0)],
        [(-2, -2), (0, -2), (2, -2), (-1, 0), (0, 0), (1, 0), (-2, 2), (0, 2), (2, 2)],
    ]
    for ix, iy in patterns[generation]:
        _cell(c, 72 + ix * 13, 72 + iy * 13, 9, ACID if (ix + iy) % 2 == 0 else CYAN, q)


def _cell_death(c: Canvas, p: float) -> None:
    q = window(p, 0.38)
    initial = [(-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (-2, -1), (0, -1), (2, -1), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-2, 1), (0, 1), (2, 1), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2)]
    generation = min(5, int(p * 6.5))
    for i, (ix, iy) in enumerate(initial):
        if (i * 3 + abs(ix) + 2 * abs(iy)) % 6 < generation:
            continue
        _cell(c, 72 + ix * 12, 72 + iy * 12, 8, ACID if i % 3 else VIOLET_LIGHT, q)


def _rule_front(c: Canvas, p: float) -> None:
    rows = _rule_rows(17, 11, seed=1)
    visible = min(len(rows), 1 + int(p * len(rows)))
    for gy, row in enumerate(rows[:visible]):
        y = 28 + gy * 8.5
        for gx, live in enumerate(row):
            if live:
                _cell(c, 72 + (gx - 8) * 7.2, y, 5.5, ACID if (gx + gy) % 3 else CYAN, 0.86)
    c.line([(13, 24), (131, 24)], fade(EMERALD, 0.42), 0.8)


def _glider_launch(c: Canvas, p: float) -> None:
    q = window(p, 0.50)
    generation = min(7, int(p * 8.0))
    if generation < 3:
        # Individual cells arrive and lock into the glider configuration.
        cells = _glider_cells(48, 72, 10)
        shown = 2 + generation
        for i, pt in enumerate(cells[:shown]):
            _cell(c, pt[0], pt[1], 7.5, ACID if i % 2 == 0 else CYAN, q)
    else:
        cx = 48 + (generation - 2) * 11
        cy = 72 - (generation - 2) * 5
        for i, pt in enumerate(_glider_cells(cx, cy, 10)):
            _cell(c, pt[0], pt[1], 7.5, ACID if i % 2 == 0 else CYAN, q)
        for trail in range(1, 4):
            _cell(c, cx - trail * 12, cy + trail * 4, 4.5, EMERALD, q * (0.45 / trail))


def _glider_impact(c: Canvas, p: float) -> None:
    q = window(p, 0.42)
    generation = min(7, int(p * 8.0))
    if generation < 3:
        cx = 34 + generation * 16
        for i, pt in enumerate(_glider_cells(cx, 72, 9)):
            _cell(c, pt[0], pt[1], 7, ACID if i % 2 == 0 else CYAN, q)
    else:
        c.rect((69, 43, 75, 101), fill=fade(CERAMIC, 0.12 * q), outline=fade(CERAMIC, 0.55 * q), width=1.0)
        spread = generation - 2
        fragments = [(-3, -2), (-2, 1), (-1, -3), (1, 2), (2, -1), (3, 3), (0, 0), (2, 3)]
        for i, (ix, iy) in enumerate(fragments):
            x = 72 + ix * (5 + spread * 2.1)
            y = 72 + iy * (5 + spread * 1.6)
            _cell(c, x, y, max(3.5, 7.5 - spread * 0.45), ACID if i % 2 == 0 else VIOLET_LIGHT, q * (1.0 - spread * 0.06))


def _oscillator_pulse(c: Canvas, p: float) -> None:
    generation = int(p * 12) % 2
    center = (72, 72)
    c.ellipse(center, 37, outline=fade(EMERALD, 0.28), width=0.8)
    if generation == 0:
        coords = [(-1, 0), (0, 0), (1, 0)]
    else:
        coords = [(0, -1), (0, 0), (0, 1)]
    for ix, iy in coords:
        _cell(c, 72 + ix * 13, 72 + iy * 13, 9.5, ACID if ix == 0 and iy == 0 else CYAN, 0.95)
    for i in range(4):
        a = i * math.pi / 2 + generation * math.pi / 4
        _cell(c, 72 + math.cos(a) * 42, 72 + math.sin(a) * 42, 4.5, VIOLET_LIGHT, 0.55)


def _still_life_lock(c: Canvas, p: float) -> None:
    q = window(p, 0.55)
    generation = min(6, int(p * 7.2))
    chaos = [(-3, -2), (-2, 2), (-1, -1), (0, 3), (1, -3), (2, 1), (3, -1), (-3, 1), (2, -2)]
    for i, (ix, iy) in enumerate(chaos):
        if i < generation + 1:
            continue
        _cell(c, 72 + ix * 12, 72 + iy * 11, 6.2, VIOLET_LIGHT if i % 2 else CYAN, q * 0.68)
    stable_alpha = max(0.0, min(1.0, (generation - 2) / 3.0))
    for ix, iy in ((-1, -1), (0, -1), (-1, 0), (0, 0)):
        _cell(c, 72 + ix * 11 + 5.5, 72 + iy * 11 + 5.5, 9, ACID, q * stable_alpha)
    if stable_alpha > 0:
        c.rect((56, 56, 77, 77), outline=fade(ACID_LIGHT, 0.28 * q * stable_alpha), width=1.0)


def _garden_growth(c: Canvas, p: float) -> None:
    rows = _rule_rows(19, 12, seed=3)
    visible = min(len(rows), 1 + int(p * len(rows)))
    for gy, row in enumerate(rows[:visible]):
        y = 122 - gy * 8.2
        for gx, live in enumerate(row):
            if live:
                color = ACID if (gx + gy) % 4 else VIOLET_LIGHT
                _cell(c, 72 + (gx - 9) * 6.4, y, 5.0, color, 0.76)
    # Stable bright seed remains visible through all generations.
    _cell(c, 72, 122, 7, CYAN, 0.95)


def _causal_cone(c: Canvas, p: float, collapse: bool) -> None:
    q = window(p, 0.55)
    generation = min(9, int(p * 10.2))
    if collapse:
        generation = 9 - generation
    apex = (72.0, 28.0 if collapse else 116.0)
    direction = 1 if collapse else -1
    for g in range(generation + 1):
        y = apex[1] + direction * g * 9.0
        for xstep in range(-g, g + 1, 2):
            color = ACID if (g + xstep) % 4 else CYAN
            _cell(c, 72 + xstep * 5.4, y, 5.2, color, q * (0.88 - g * 0.035))
    _cell(c, apex[0], apex[1], 7.0, VIOLET_LIGHT, q)


def _causal_cone_expand(c: Canvas, p: float) -> None:
    _causal_cone(c, p, False)


def _causal_cone_collapse(c: Canvas, p: float) -> None:
    _causal_cone(c, p, True)


def _fixed_point_acquire(c: Canvas, p: float) -> None:
    q = window(p, 0.56)
    generation = min(7, int(p * 8.0))
    noise = [(-3, -3), (-2, 1), (-1, -2), (0, 3), (1, -1), (2, 2), (3, -2), (-3, 2), (3, 1), (0, -3)]
    for i, (ix, iy) in enumerate(noise):
        if (i + generation) % 8 < generation:
            continue
        _cell(c, 72 + ix * 11, 72 + iy * 11, 5.5, CYAN if i % 2 else VIOLET_LIGHT, q * 0.60)
    stable = max(0.0, min(1.0, (generation - 2) / 4.0))
    fixed = [(-1, -1), (0, -1), (1, 0), (0, 1), (-1, 1), (-2, 0)]
    for ix, iy in fixed:
        _cell(c, 72 + ix * 10, 72 + iy * 10, 7.2, ACID, q * stable)
    c.ellipse((72, 72), 3.2, fill=fade(CERAMIC, q * stable), outline=fade(ACID_LIGHT, q * stable), width=0.6)


def _phase_boundary(c: Canvas, p: float) -> None:
    generation = int(p * 12)
    cell = 8.0
    for iy in range(-6, 7):
        y = 72 + iy * cell
        boundary = int(2.0 * math.sin((iy + generation) * 0.9))
        for ix in range(-7, 8):
            if abs(ix) > 6:
                continue
            x = 72 + ix * cell
            if ix < boundary:
                color = ACID
            elif ix > boundary:
                color = VIOLET_LIGHT
            else:
                color = CYAN if (iy + generation) % 2 == 0 else MAGENTA
            alpha = 0.52 if abs(ix - boundary) > 2 else 0.88
            _cell(c, x, y, 5.5, color, alpha)


def _generation_wipe(c: Canvas, p: float) -> None:
    q = window(p, 0.55)
    generation = min(8, int(p * 9.0))
    rows_a = _rule_rows(15, 9, seed=0)
    rows_b = _rule_rows(15, 9, seed=2)
    threshold = 22 + generation * 12
    for gy in range(9):
        y = 37 + gy * 10
        for gx in range(15):
            x = 23 + gx * 7
            source = rows_b if y <= threshold else rows_a
            if source[gy][gx]:
                _cell(c, x, y, 5.2, ACID if y <= threshold else VIOLET_LIGHT, q * 0.76)
    c.line([(19, threshold), (125, threshold)], fade(CYAN, 0.82 * q), 1.6)


def _corruption_seed(c: Canvas, p: float) -> None:
    generation = int(p * 12)
    radius = min(6, generation // 2 + 1)
    for iy in range(-6, 7):
        for ix in range(-6, 7):
            if (ix + iy * 2) % 3 != 0:
                continue
            dist = abs(ix) + abs(iy)
            corrupt = dist <= radius and ((ix * 3 + iy + generation) % 4 != 0)
            color = MAGENTA if corrupt else ACID
            _cell(c, 72 + ix * 8, 72 + iy * 8, 5.4, color, 0.80 if corrupt else 0.48)
    _cell(c, 72, 72, 7.4, MAGENTA, 1.0)


DRAWERS = {
    "cell_birth": _cell_birth,
    "cell_death": _cell_death,
    "rule_front": _rule_front,
    "glider_launch": _glider_launch,
    "glider_impact": _glider_impact,
    "oscillator_pulse": _oscillator_pulse,
    "still_life_lock": _still_life_lock,
    "garden_growth": _garden_growth,
    "causal_cone_expand": _causal_cone_expand,
    "causal_cone_collapse": _causal_cone_collapse,
    "fixed_point_acquire": _fixed_point_acquire,
    "phase_boundary": _phase_boundary,
    "generation_wipe": _generation_wipe,
    "corruption_seed": _corruption_seed,
}

SPECS = {
    "cell_birth": make_spec("cellular_growth", "A single live seed produces a visibly larger local population over discrete generations.", placement="target", relationship="startup", extra_anchor="target", size=104),
    "cell_death": make_spec("cellular_decay", "A populated patch loses cells generation by generation rather than fading continuously.", placement="target", relationship="aftermath", extra_anchor="target", size=108),
    "rule_front": make_spec("rule_evolution", "A Rule-110-like spacetime strip reveals successive cellular generations as a advancing front.", placement="world", relationship="active", rotate_safe=False, size=126),
    "glider_launch": make_spec("glider", "Five cells assemble into a glider configuration, then advance in discrete screen-right steps.", placement="source", orientation="positive_x_is_forward", mirror_x=True, relationship="release", extra_anchor="emitter", size=124),
    "glider_impact": make_spec("glider", "A cellular glider meets a barrier and breaks into evolving local fragments.", placement="contact", orientation="positive_x_is_incoming", mirror_x=True, relationship="impact", extra_anchor="contact", size=118),
    "oscillator_pulse": make_spec("oscillator", "A blinker-like cellular oscillator alternates exact horizontal and vertical states.", loop=True, placement="source", attachment="follow_source", relationship="sustain", extra_anchor="emitter", size=104),
    "still_life_lock": make_spec("fixed_pattern", "Transient cellular noise settles into a stable block still-life.", placement="target", relationship="aftermath", extra_anchor="target", size=112),
    "garden_growth": make_spec("rule_evolution", "A bottom seed unfolds into a dense deterministic cellular garden over visible generations.", placement="surface", orientation="positive_y_points_toward_surface", relationship="active", extra_anchor="contact", rotate_safe=True, size=128),
    "causal_cone_expand": make_spec("causal_cone", "A single cause expands into the exact reachable cellular cone over discrete ticks.", placement="target", relationship="active", extra_anchor="target", rotate_safe=False, size=126),
    "causal_cone_collapse": make_spec("causal_cone", "A populated causal cone contracts generation by generation back to one origin cell.", placement="target", relationship="release", extra_anchor="target", rotate_safe=False, size=126),
    "fixed_point_acquire": make_spec("fixed_point", "Noisy local states iterate toward one stable repeating configuration.", placement="target", relationship="aftermath", extra_anchor="target", size=112),
    "phase_boundary": make_spec("phase_boundary", "Two cellular phases maintain a jagged discrete frontier whose local cells update each tick.", loop=True, placement="world", relationship="sustain", rotate_safe=False, size=116),
    "generation_wipe": make_spec("generation_transition", "A hard cellular scanline replaces one generation field with another.", placement="world", orientation="positive_y_is_wipe_direction", mirror_x=False, relationship="release", rotate_safe=False, size=120),
    "corruption_seed": make_spec("corruption", "One anomalous magenta seed deterministically converts nearby cells while the lattice continues to tick.", loop=True, placement="target", attachment="follow_target", relationship="sustain", extra_anchor="target", size=116),
}

ORIGINS = {name: (72.0, 72.0) for name, _, _ in ROWS}
ORIGINS["garden_growth"] = (72.0, 122.0)
ORIGINS["rule_front"] = (72.0, 24.0)


def render(out_dir: str | Path, **opts):
    del opts
    return publish_catalog(
        target_name=TARGET_NAME,
        display_name="Perfect Cellular Automaton Detached VFX",
        character_context_id="perfect_cellular_automaton",
        character_context_display="Perfect Cellular Automaton",
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
