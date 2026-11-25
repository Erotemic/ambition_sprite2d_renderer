"""The Spaceship: the lightweight spaceship of the Game of Life, loose on the
Life field of the Automaton dimension (gate address CELLS,
`docs/planning/game/automaton-dimension.md`).

Its frames are the rule's own: the pattern is stepped by Conway's rule (a
live cell with two or three live neighbours lives, a dead cell with exactly
three is born), and a lightweight spaceship comes back to its shape every
four generations two cells along, so it flies at c/2. Each cell is a lit
square of cyan with a dark core; behind it a faint trail of the cells that
just died.

It flies in its four phases; when it sees you its cells brighten; its
windup pulses; its strike is a dash with the trail drawn out long. A hit
knocks cells out of true; at its death its cells die a generation at a
time, the way a pattern that has been hit falls apart.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Set, Tuple

from . import _art_cast_kit as K

TARGET_NAME = "life_spaceship"
FRAME_SIZE = (128, 96)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 140),
    ("walk", 8, 90),
    ("notice", 4, 110),
    ("windup", 4, 90),
    ("attack_side", 6, 70),
    ("hit", 3, 90),
    ("death", 6, 110),
]
LOOPS = {"idle", "walk", "windup"}

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Spaceship", "Floating", "Small", "Light", "Fly", ["cellular_automaton", "pattern", "spaceship"],
    "The lightweight spaceship of Conway's Game of Life, flying the Life field at c/2: its frames are the rule's own "
    "four generations, lit cyan cells with a trail of the cells that just died.",
)
ACTOR_METADATA["tags"] = ["enemy", "automaton"]

CELL = (120, 220, 255, 255)
CORE = (30, 40, 90, 255)
DEAD = (120, 160, 255, 255)
HOT = (255, 200, 110, 255)

#: The lightweight spaceship, flying right (+x), as (x, y) live cells.
LWSS = {(0, 0), (3, 0), (4, 1), (0, 2), (4, 2), (1, 3), (2, 3), (3, 3), (4, 3)}

Cells = Set[Tuple[int, int]]


def step(live: Cells) -> Cells:
    """One generation of Conway's rule (B3/S23)."""
    counts: dict = {}
    for x, y in live:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    counts[(x + dx, y + dy)] = counts.get((x + dx, y + dy), 0) + 1
    return {c for c, n in counts.items() if n == 3 or (n == 2 and c in live)}


def generations(n: int) -> List[Cells]:
    out = [set(LWSS)]
    for _ in range(n - 1):
        out.append(step(out[-1]))
    return out


GENS = generations(5)
assert {(x - 2, y) for x, y in GENS[4]} == LWSS, "the lightweight spaceship comes back two cells along"

#: The size of a cell in the frame, and where the pattern sits.
S = 13.0


def _draw(f: K.Frame, live: Cells, ox: float, oy: float, glow: float = 1.0, jitter: float = 0.0, seed: int = 0) -> None:
    """The live cells of `live` with their top left at (ox, oy)."""
    for k, (x, y) in enumerate(sorted(live)):
        j = jitter * math.sin(seed * 1.7 + k * 2.3)
        cx, cy = ox + x * S + j, oy + y * S - j * 0.6
        sq = [(cx + 1.0, cy + 1.0), (cx + S - 1.0, cy + 1.0), (cx + S - 1.0, cy + S - 1.0), (cx + 1.0, cy + S - 1.0)]
        f.poly(sq, CELL)
        f.poly(K.grow(sq, -3.2), CORE, body=False)
        f.glow(cx + S / 2, cy + S / 2, S * 0.6, K.alpha(CELL, min(0.5, 0.2 * glow)))


def _trail(f: K.Frame, live: Cells, ox: float, oy: float, length: float, strength: float) -> None:
    """A faint smear of the cells that just died, behind the pattern."""
    rows = {y for _, y in live}
    for y in rows:
        xs = [x for x, yy in live if yy == y]
        x0 = ox + min(xs) * S
        cy = oy + y * S + S / 2
        f.glow_line([(x0 - length, cy), (x0, cy)], 4.0, K.alpha(DEAD, strength))


def _origin(live: Cells) -> Tuple[float, float]:
    """Where to put `live`'s cell (0, 0) so its bounding box is centred."""
    xs, ys = [x for x, _ in live], [y for _, y in live]
    w, h = (max(xs) - min(xs) + 1) * S, (max(ys) - min(ys) + 1) * S
    return 64.0 - w / 2.0 - min(xs) * S, 48.0 - h / 2.0 - min(ys) * S


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in LOOPS)
    f = K.Frame(FRAME_SIZE)
    ox, oy = _origin(GENS[0])
    if anim in ("idle", "walk"):
        # The game moves the body; the frame keeps each generation centred.
        gen = GENS[i % 4]
        gx, gy = _origin(gen)
        _trail(f, gen, gx, gy, 18.0 if anim == "idle" else 28.0, 0.4)
        _draw(f, gen, gx, gy)
    elif anim == "notice":
        _trail(f, GENS[0], ox, oy, 14.0, 0.3)
        _draw(f, GENS[0], ox, oy, glow=1.0 + 1.5 * math.sin(math.pi * t))
    elif anim == "windup":
        pulse = 0.5 + 0.5 * math.sin(math.tau * t)
        _draw(f, GENS[i % 2 * 2], ox - 3.0 * pulse, oy, glow=1.0 + 2.0 * pulse)
    elif anim == "attack_side":
        dash = math.sin(math.pi * min(1.0, t * 1.3))
        _trail(f, GENS[i % 4], ox + 10.0 * dash, oy, 20.0 + 50.0 * dash, 0.6)
        _draw(f, GENS[i % 4], ox + 10.0 * dash, oy, glow=2.0)
    elif anim == "hit":
        _draw(f, GENS[0], ox - 4.0, oy, glow=0.6, jitter=5.0 * math.sin(math.pi * t) + 1.0, seed=i)
    elif anim == "death":
        # It falls apart a generation at a time: each frame keeps fewer cells.
        live = sorted(GENS[0])
        keep = max(0, int(round(len(live) * (1.0 - t))))
        _draw(f, set(live[:keep]), ox, oy + 6.0 * t, glow=1.0 - t)
        for k, (x, y) in enumerate(live[keep:]):
            f.glow(ox + x * S + S / 2, oy + y * S + S / 2 + 10.0 * t, S * 0.6, K.alpha(HOT, 0.5 * (1.0 - t)))
    return f.finish(outline=K.shade(CORE, 0.6), width=1.0, glow_blur=2.0)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
