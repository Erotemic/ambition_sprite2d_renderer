"""The Perfect Cellular Automaton's charge shot: a ball of LIVE CELLS.

Jon, 2026-10-18: the PCA plays like Mewtwo, and his neutral special is a
Shadow Ball-like charge blast, with art of his own. He is a cellular automaton,
so the ball is not a stylised energy orb with a cell texture painted on: each
tier is a real Conway's Life OSCILLATOR, stepped by the actual rules, sealed in
a glowing membrane. A tap throws a blinker; a full charge throws a pulsar.

**Five tiers, told apart by the pattern, not just the size** (the same rule as
the Projectile Polygon's shot): a held ball has to read as a different object
from a tap the instant it leaves.

* tier 1, a BLINKER (period 2): three cells, a bare membrane;
* tier 2, a TOAD (period 2): the membrane gains a rim;
* tier 3, a BEACON (period 2) inside a ring of orbiting cells;
* tier 4, the 4-8-12 diamond's cousin, a CLOCK (period 2), with two gliders
  circling it and stray cells thrown off;
* tier 5, a PULSAR (period 3), the most recognisable oscillator in Life, with a
  compression ring of cells standing off the surface.

Each travel row is one or more whole periods of its oscillator, so it loops
exactly; the membrane's pulse runs at another rate so the ball never reads as
a still being shuffled. The palette is the glider's (`glider.py`): the PCA's
energised green.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageFilter

from ambition_sprite2d_renderer.core.draw import blending_draw

from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_NAME = "pca_charge_shot"
FRAME_W, FRAME_H = 112, 112
SUPERSAMPLE = 4

#: The glider's energised-cell palette, so the shot reads as the PCA's.
DEEP = (4, 20, 15)
MEMBRANE = (30, 143, 90)
CELL_RIM = (57, 224, 110)
CELL_CORE = (176, 255, 196)
GLINT = (207, 255, 224)

Cell = tuple[int, int]

#: (name, frames, ms). Travel rows loop (whole oscillator periods); impacts and
#: the spawn do not.
ROWS: list[tuple[str, int, int]] = [
    ("travel_tier1", 4, 80),
    ("travel_tier2", 4, 76),
    ("travel_tier3", 4, 70),
    ("travel_tier4", 6, 64),
    ("travel_tier5", 6, 60),
    ("spawn", 5, 40),
    ("impact_light", 6, 46),
    ("impact_heavy", 9, 48),
]

#: The membrane's radius at each tier, in logical px. Tier 5 is more than three
#: times tier 1: the reward for holding is visible at a glance.
TIER_RADIUS = {1: 7.0, 2: 10.0, 3: 14.0, 4: 18.5, 5: 25.0}


def _parse(rows: list[str]) -> set[Cell]:
    return {(x, y) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch == "#"}


#: One phase of each tier's oscillator. The rows are the patterns' canonical
#: drawings; `_life_step` makes the other phases.
SEEDS: dict[int, set[Cell]] = {
    1: _parse(["###"]),
    2: _parse([".###", "###."]),
    3: _parse(["##..", "##..", "..##", "..##"]),
    4: _parse([".#..", "..##", "##..", "..#."]),
    5: _parse([
        "..###...###..",
        ".............",
        "#....#.#....#",
        "#....#.#....#",
        "#....#.#....#",
        "..###...###..",
        ".............",
        "..###...###..",
        "#....#.#....#",
        "#....#.#....#",
        "#....#.#....#",
        ".............",
        "..###...###..",
    ]),
}


def _life_step(cells: set[Cell]) -> set[Cell]:
    """One generation of Conway's Game of Life over a sparse cell set."""
    counts: dict[Cell, int] = {}
    for x, y in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    key = (x + dx, y + dy)
                    counts[key] = counts.get(key, 0) + 1
    return {cell for cell, n in counts.items() if n == 3 or (n == 2 and cell in cells)}


def _generation(tier: int, index: int) -> set[Cell]:
    cells = set(SEEDS[tier])
    for _ in range(index):
        cells = _life_step(cells)
    return cells


def _canvas() -> tuple[Image.Image, object]:
    image = Image.new("RGBA", (FRAME_W * SUPERSAMPLE, FRAME_H * SUPERSAMPLE), (0, 0, 0, 0))
    return image, blending_draw(image)


def _disc(draw, centre, radius: float, colour, alpha: int) -> None:
    if radius <= 0 or alpha <= 1:
        return
    x, y = centre[0] * SUPERSAMPLE, centre[1] * SUPERSAMPLE
    r = radius * SUPERSAMPLE
    draw.ellipse([x - r, y - r, x + r, y + r], fill=tuple(colour) + (alpha,))


def _ring(draw, centre, radius: float, width: float, colour, alpha: int) -> None:
    if radius <= 0 or alpha <= 1:
        return
    x, y = centre[0] * SUPERSAMPLE, centre[1] * SUPERSAMPLE
    r = radius * SUPERSAMPLE
    draw.ellipse(
        [x - r, y - r, x + r, y + r],
        outline=tuple(colour) + (alpha,),
        width=max(1, round(width * SUPERSAMPLE)),
    )


def _cell(draw, centre, size: float, alpha: float) -> None:
    """One live cell: a dark-edged square with a bright core, as the glider draws them."""
    x, y = centre[0] * SUPERSAMPLE, centre[1] * SUPERSAMPLE
    half = size * 0.5 * SUPERSAMPLE
    inner = half * 0.62
    draw.rectangle([x - half, y - half, x + half, y + half], fill=CELL_RIM + (int(235 * alpha),))
    draw.rectangle([x - inner, y - inner, x + inner, y + inner], fill=CELL_CORE + (int(245 * alpha),))


def _pattern(draw, centre, cells: set[Cell], cell_px: float, alpha: float) -> None:
    """Draw `cells` centred on `centre`, at `cell_px` logical px per cell."""
    if not cells:
        return
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    mid_x = (min(xs) + max(xs)) * 0.5
    mid_y = (min(ys) + max(ys)) * 0.5
    for x, y in cells:
        point = (centre[0] + (x - mid_x) * cell_px, centre[1] + (y - mid_y) * cell_px)
        _cell(draw, point, cell_px * 0.86, alpha)


def _ball(draw, centre, radius: float, tier: int, generation: int, phase: float,
          alpha: float = 1.0) -> None:
    """One charge ball: a membrane and the tier's oscillator inside it."""
    pulse = 1.0 + 0.07 * math.sin(phase * math.tau)
    swell = radius * pulse
    _disc(draw, centre, swell * 1.25, MEMBRANE, int(60 * alpha))
    _disc(draw, centre, swell, DEEP, int(200 * alpha))
    _disc(draw, centre, swell * 0.92, MEMBRANE, int(70 * alpha))
    if tier >= 2:
        _ring(draw, centre, swell, max(0.6, radius * 0.08), CELL_RIM, int(200 * alpha))
    cells = _generation(tier, generation)
    span = max(max(x for x, _ in cells) - min(x for x, _ in cells),
               max(y for _, y in cells) - min(y for _, y in cells)) + 1
    cell_px = (swell * 1.45) / max(span, 3)
    _pattern(draw, centre, cells, cell_px, alpha)
    if tier >= 3:
        # A ring of orbiting cells: the membrane is visibly ALIVE.
        count = 6 if tier == 3 else 10
        for index in range(count):
            angle = phase * math.tau * 0.6 + index * math.tau / count
            point = (centre[0] + math.cos(angle) * swell * 1.18,
                     centre[1] + math.sin(angle) * swell * 1.18)
            _cell(draw, point, max(1.4, radius * 0.11), 0.85 * alpha)
    if tier >= 4:
        # Two gliders circling it, each in its own Life phase.
        glider = {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)}
        for index in range(2):
            angle = -phase * math.tau * 0.45 + index * math.pi
            orbit = (centre[0] + math.cos(angle) * swell * 1.55,
                     centre[1] + math.sin(angle) * swell * 1.55)
            cells = glider
            for _ in range((generation + index * 2) % 4):
                cells = _life_step(cells)
            _pattern(draw, orbit, cells, max(1.0, radius * 0.07), 0.8 * alpha)
    if tier >= 5:
        # A compression ring of cells standing off the surface.
        count = 24
        for index in range(count):
            angle = index * math.tau / count + phase * math.tau * 0.25
            point = (centre[0] + math.cos(angle) * swell * 1.82,
                     centre[1] + math.sin(angle) * swell * 1.82)
            if (index + generation) % 3:
                _cell(draw, point, max(1.0, radius * 0.07), 0.7 * alpha)
        _ring(draw, centre, swell * 1.82, max(0.5, radius * 0.03), GLINT, int(70 * alpha))


def _travel(tier: int, frame_idx: int, frame_count: int) -> Image.Image:
    image, draw = _canvas()
    phase = frame_idx / frame_count
    centre = (FRAME_W * 0.5, FRAME_H * 0.5)
    radius = TIER_RADIUS[tier]
    # The wake trails BEHIND (-x): the sheet travels +x and the runtime mirrors it.
    for step in range(1, 4 if tier >= 3 else 2):
        back = (centre[0] - radius * 0.8 * step, centre[1])
        _disc(draw, back, radius * (0.7 - 0.16 * step), MEMBRANE, int(80 / step))
    _ball(draw, centre, radius, tier, frame_idx, phase)
    return _finish(image, blur=0.8 + 0.12 * tier)


def _spawn(frame_idx: int, frame_count: int) -> Image.Image:
    """Release: the membrane closes round the pattern."""
    image, draw = _canvas()
    t = frame_idx / max(1, frame_count - 1)
    centre = (FRAME_W * 0.5, FRAME_H * 0.5)
    flare = (1.0 - t) ** 1.6
    _disc(draw, centre, 24.0 * flare + 3.0, GLINT, int(200 * flare))
    _ring(draw, centre, 10.0 + 28.0 * t, 2.2 * (1.0 - t) + 0.4, CELL_RIM, int(200 * (1.0 - t)))
    _ball(draw, centre, TIER_RADIUS[5] * (0.35 + 0.65 * t), 5, frame_idx, t, alpha=min(1.0, t * 1.8))
    return _finish(image, blur=1.3)


def _impact(heavy: bool, frame_idx: int, frame_count: int) -> Image.Image:
    """The membrane bursts and its cells scatter: a light hit puffs, a heavy one
    throws a shockwave of cells."""
    image, draw = _canvas()
    t = frame_idx / max(1, frame_count - 1)
    centre = (FRAME_W * 0.5, FRAME_H * 0.5)
    fade = (1.0 - t) ** 1.4
    peak = 38.0 if heavy else 18.0
    _disc(draw, centre, peak * (0.25 + 0.75 * t) * 0.55, GLINT, int(190 * fade))
    _ring(draw, centre, peak * (0.2 + t), 3.0 * fade + 0.5, CELL_RIM, int(220 * fade))
    count = 14 if heavy else 8
    for index in range(count):
        angle = index * math.tau / count + 0.3
        reach = peak * (0.3 + t * (1.6 if heavy else 1.1))
        point = (centre[0] + math.cos(angle) * reach, centre[1] + math.sin(angle) * reach)
        _cell(draw, point, (3.6 if heavy else 2.6) * fade + 0.6, fade)
    if heavy:
        _ring(draw, centre, peak * (0.2 + t * 1.7), 2.0 * fade + 0.4, GLINT, int(140 * fade))
    return _finish(image, blur=1.5)


def _finish(image: Image.Image, blur: float) -> Image.Image:
    glow = image.filter(ImageFilter.GaussianBlur(blur * SUPERSAMPLE))
    out = Image.new("RGBA", image.size, (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(image)
    return out.resize((FRAME_W, FRAME_H), Image.LANCZOS)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    if animation.startswith("travel_tier"):
        return _travel(int(animation[-1]), frame_idx, frame_count)
    if animation == "spawn":
        return _spawn(frame_idx, frame_count)
    if animation == "impact_light":
        return _impact(False, frame_idx, frame_count)
    if animation == "impact_heavy":
        return _impact(True, frame_idx, frame_count)
    raise ValueError(f"{TARGET_NAME}: no drawer for {animation!r}")


ACTOR_METADATA = {
    "actor": {
        "character_id": TARGET_NAME,
        "display_name": "PCA Charge Shot",
    },
    "authoring_description": {
        "concept": (
            "The Perfect Cellular Automaton's held-and-released charge blast "
            "(a Mewtwo Shadow Ball). Each tier is a real Life oscillator sealed "
            "in a membrane: blinker, toad, beacon, clock, pulsar."
        ),
        "visual_language": [
            "the glider's energised green: dark membrane, bright cells with dark rims",
            "cells are stepped by Conway's rules, so the pattern inside is genuinely alive",
            "layers added by tier: rim, then orbiting cells, then circling gliders, then a compression ring of cells",
            "the wake trails behind on the authored +x travel direction",
        ],
    },
    "gameplay_description": {
        "role": "chargeable neutral-special projectile",
        "authoring_notes": [
            "Tier rows are separate animations: the runtime picks the row for the release tier.",
            "Each travel row is whole oscillator periods, so it loops exactly.",
        ],
    },
    "tags": ["projectile", "charge_shot", "cellular", "perfect_cellular_automaton"],
}


def render(out_dir: str | Path, **opts):
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        auto_crop=True,
        crop_margin=3,
        actor_metadata=ACTOR_METADATA,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(
        TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=(FRAME_W, FRAME_H)
    )


__all__ = ["ACTOR_METADATA", "ROWS", "TARGET_NAME", "render", "render_canonical", "render_frame"]
