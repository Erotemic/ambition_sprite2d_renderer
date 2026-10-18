"""A shared vocabulary of BLASTS, drawn into an :class:`FxCanvas`.

A blast is what an attack does to the space around where it lands. Not every
blast is a fireball: a column can ERUPT out of the floor, a ring can run out
thin and fast, shards can fly, a point can gather in and then pop, a lattice
can bloom cell by cell. Each style here is a pure function of

    (canvas, u, origin, *, size/direction..., style)

where ``u`` in [0, 1] is the blast's OWN life (0 = it starts, 1 = it is gone;
outside that range nothing is drawn), so a character maps its clip time onto
the window it wants and the same blast reads the same in any attack.

A :class:`BlastStyle` says what the blast is MADE of: square ``cell``s (the
Perfect Cellular Automaton's discrete grammar -- they snap to a lattice and
are born and die rather than drift), ``spark`` streaks, angular ``shard``s or
round ``dot``s, and the three heats it burns at (``core`` hottest, ``body``,
``edge`` coolest). Nothing here knows a character; coordinates are the
caller's logical rig space, angles are degrees with 0 = +x and 90 = down.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Sequence

from ._svg_fighter_effects import FxCanvas, clamp01, fade, mix, smooth

Color = tuple[int, int, int, int]
Point = tuple[float, float]

PARTICLES = ("cell", "spark", "shard", "dot")


@dataclass(frozen=True)
class BlastStyle:
    """What a blast is made of and how hot it burns."""

    particle: str = "spark"
    core: Color = (255, 250, 228, 255)
    body: Color = (255, 196, 92, 255)
    edge: Color = (214, 92, 60, 255)
    #: Ink around a particle; ``None`` draws them borderless.
    outline: Color | None = None
    #: Alpha of a cell's/shard's fill relative to its outline.
    fill: float = 0.55
    #: Lattice pitch cells snap to (``cell`` particles only; 0 = no snap).
    grid: float = 0.0
    #: Scales every particle.
    grain: float = 1.0
    seed: int = 0

    def __post_init__(self) -> None:
        if self.particle not in PARTICLES:
            raise ValueError(f"unknown blast particle {self.particle!r}; expected one of {PARTICLES}")

    def heat(self, h: float) -> Color:
        """``h`` = 1 the core colour, 0.5 the body, 0 the edge."""
        h = clamp01(h)
        if h >= 0.5:
            return mix(self.body, self.core, (h - 0.5) * 2.0)
        return mix(self.edge, self.body, h * 2.0)

    def with_seed(self, seed: int) -> "BlastStyle":
        return replace(self, seed=seed)


# --- small helpers --------------------------------------------------------------


def _rand(*keys: float) -> float:
    """Deterministic 0..1 from integer-ish keys (FNV-1a + an avalanche)."""
    h = 2166136261
    for key in keys:
        h = ((h ^ (int(key) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5BD1E995) & 0xFFFFFFFF
    h ^= h >> 15
    return h / 4294967296.0


def _dir(angle: float) -> Point:
    a = math.radians(angle)
    return math.cos(a), math.sin(a)


def _ease_out(u: float) -> float:
    u = clamp01(u)
    return 1.0 - (1.0 - u) ** 3


def _live(u: float) -> bool:
    return 0.0 <= u <= 1.0


def _snap(style: BlastStyle, origin: Point, p: Point) -> Point:
    if style.particle != "cell" or style.grid <= 0.0:
        return p
    g = style.grid
    return (
        origin[0] + round((p[0] - origin[0]) / g) * g,
        origin[1] + round((p[1] - origin[1]) / g) * g,
    )


def inked_line(canvas: FxCanvas, style: BlastStyle, points: Sequence[Point], color: Color, width: float) -> None:
    """A stroke in ``color``, laid over a wider stroke of the style's ``outline``
    (when it has one) so a pale blast still reads on a pale background."""
    if style.outline is not None and color[3] > 0:
        canvas.line(points, fade(style.outline, color[3] / 255.0 * 0.75), width + 1.1)
    canvas.line(points, color, width)


def particle(
    canvas: FxCanvas,
    style: BlastStyle,
    at: Point,
    size: float,
    alpha: float,
    *,
    heat: float = 0.5,
    angle: float = 0.0,
    stretch: float = 1.0,
) -> None:
    """One grain of a blast at ``at``: ``size`` across, pointing along ``angle``."""
    size *= style.grain
    if alpha <= 0.01 or size <= 0.15:
        return
    color = style.heat(heat)
    rim = style.outline if style.outline is not None else style.heat(min(1.0, heat + 0.35))
    kind = style.particle
    if kind == "cell":
        h = size * 0.5
        x, y = at
        canvas.polygon(
            [(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)],
            fade(color, alpha * style.fill),
            fade(rim, alpha),
            0.6,
        )
    elif kind == "dot":
        canvas.ellipse(at, size * 0.5, size * 0.5, fade(color, alpha * style.fill), fade(rim, alpha), 0.5)
    elif kind == "spark":
        dx, dy = _dir(angle)
        length = size * 1.6 * stretch
        tail = (at[0] - dx * length, at[1] - dy * length)
        inked_line(canvas, style, [tail, at], fade(color, alpha * 0.85), max(0.5, size * 0.42))
        canvas.line([((tail[0] + at[0]) * 0.5, (tail[1] + at[1]) * 0.5), at], fade(style.core, alpha), max(0.35, size * 0.18))
    else:  # shard
        dx, dy = _dir(angle)
        px, py = -dy, dx
        length = size * 1.3 * stretch
        tip = (at[0] + dx * length * 0.6, at[1] + dy * length * 0.6)
        back = (at[0] - dx * length * 0.4, at[1] - dy * length * 0.4)
        w = size * 0.32
        canvas.polygon(
            [tip, (back[0] + px * w, back[1] + py * w), (back[0] - px * w * 0.6, back[1] - py * w * 0.6)],
            fade(color, alpha * style.fill),
            fade(rim, alpha),
            0.5,
        )


def _ring_points(center: Point, rx: float, ry: float, rotation: float, start: float = 0.0, end: float = 360.0, steps: int = 40) -> list[Point]:
    c, s = math.cos(math.radians(rotation)), math.sin(math.radians(rotation))
    pts = []
    for i in range(steps + 1):
        a = math.radians(start + (end - start) * i / steps)
        x, y = math.cos(a) * rx, math.sin(a) * ry
        pts.append((center[0] + x * c - y * s, center[1] + x * s + y * c))
    return pts


def _rule90_rows(rows: int, width: int, seed: int = 0) -> list[list[int]]:
    """A Sierpinski spread from one live cell: each row one cell wider."""
    row = [0] * width
    row[width // 2] = 1
    if seed % 3 == 1 and width > 4:
        row[width // 2 - 2] = 1
    out = [row]
    for _ in range(rows - 1):
        row = [row[i - 1] ^ row[(i + 1) % width] for i in range(width)]
        out.append(row)
    return out


# --- the blasts -----------------------------------------------------------------


def eruption(
    canvas: FxCanvas,
    u: float,
    base: Point,
    style: BlastStyle,
    *,
    height: float = 64.0,
    pitch: float = 6.0,
    life: float | None = None,
    lean: float = 0.0,
    spray: int = 7,
    spread: float = 0.36,
) -> None:
    """A column ERUPTS out of the ground at ``base`` and climbs ``height``.

    Rows are born from the ground up, one a generation, each wider than the
    last (a Sierpinski spread for cells), live ``life`` generations (most of
    the column's height by default) and die from the bottom; when the front
    tops out it throws a spray that falls back. ``spread`` sets how fast the
    plume widens (cell spacing per row, as a fraction of ``pitch``).
    """
    if not _live(u):
        return
    rows = max(2, int(round(height / pitch)))
    life = float(life) if life is not None else max(2.0, rows * 0.75)
    front = u * (rows + life)
    width = rows * 2 + 3
    pattern = _rule90_rows(rows, width, style.seed)
    for k in range(rows):
        age = front - k
        if age < 0.0 or age > life:
            continue
        q = 1.0 - age / life
        y = base[1] - (k + 0.5) * pitch
        x0 = base[0] + lean * k * pitch
        fresh = 1.0 if age < 1.0 else 0.0
        for i, live in enumerate(pattern[k]):
            if not live:
                continue
            off = (i - width // 2) * pitch * spread
            if abs(off) > height * 0.3:
                continue
            p = (x0 + off, y)
            if style.particle != "cell":
                p = (p[0] + (_rand(style.seed, k, i) - 0.5) * pitch * 0.6, p[1])
            particle(canvas, style, p, pitch * (0.55 + 0.35 * q), q ** 0.7, heat=0.35 + 0.5 * q + 0.15 * fresh, angle=-90.0, stretch=1.2)
    # Base flash: the ground breaking open.
    if u < 0.35:
        q = 1.0 - u / 0.35
        inked_line(canvas, style, [(base[0] - pitch * 2.2 * (1.0 - q * 0.4), base[1]), (base[0] + pitch * 2.2 * (1.0 - q * 0.4), base[1])],
                   fade(style.core, q), 1.2)
    # Spray thrown off the top once the front has topped out.
    top_u = (front - rows) / life
    if 0.0 <= top_u <= 1.0:
        top = (base[0] + lean * rows * pitch, base[1] - height)
        for i in range(spray):
            a = -90.0 + (_rand(style.seed, 91, i) - 0.5) * 120.0
            v = height * (0.25 + 0.25 * _rand(style.seed, 92, i))
            dx, dy = _dir(a)
            tt = top_u
            p = (top[0] + dx * v * tt, top[1] + dy * v * tt + 0.5 * height * 0.9 * tt * tt)
            vel_angle = math.degrees(math.atan2(dy * v + height * 0.9 * tt, dx * v))
            particle(canvas, style, _snap(style, base, p), pitch * 0.6, (1.0 - tt) * 0.9, heat=0.6, angle=vel_angle)


def shockwave_ring(
    canvas: FxCanvas,
    u: float,
    center: Point,
    style: BlastStyle,
    *,
    radius: float = 30.0,
    flatten: float = 1.0,
    rotation: float = 0.0,
    width: float = 1.6,
    beads: int = 0,
) -> None:
    """A THIN ring runs out fast and fades: a pressure front, not a fireball.

    ``flatten`` < 1 squashes it (a ring on the ground, or a pressure wave seen
    edge-on with ``rotation``); ``beads`` > 0 strings particles on the front.
    """
    if not _live(u):
        return
    r = radius * _ease_out(u)
    q = (1.0 - u) ** 1.3
    for lag, a, w in ((0.0, 1.0, width), (0.16, 0.45, width * 0.55)):
        rr = max(0.5, r * (1.0 - lag))
        pts = _ring_points(center, rr, rr * flatten, rotation)
        inked_line(canvas, style, pts, fade(style.heat(0.9 - lag * 2.0), q * a), max(0.35, w * (1.0 - u * 0.6)))
    for i in range(beads):
        a = 360.0 * i / beads + _rand(style.seed, i) * 10.0
        pts = _ring_points(center, r, r * flatten, rotation, a, a, 1)
        particle(canvas, style, _snap(style, center, pts[0]), 3.6 * (1.0 - u * 0.5), q, heat=0.8, angle=a)


def shard_burst(
    canvas: FxCanvas,
    u: float,
    center: Point,
    style: BlastStyle,
    *,
    radius: float = 26.0,
    direction: float = 0.0,
    spread: float = 360.0,
    count: int = 9,
    size: float = 5.0,
) -> None:
    """Angular pieces fly out of ``center`` (a cone with ``spread`` < 360)."""
    if not _live(u):
        return
    if u < 0.18:
        q = 1.0 - u / 0.18
        canvas.star(center, size * (1.2 + 0.8 * (1.0 - q)), fade(style.core, q), points=4, inner=0.3,
                    rotation=direction + 45.0, outline=fade(style.body, q))
    travel = _ease_out(u)
    for i in range(count):
        a = direction + (((i + 0.5) / count) - 0.5) * spread + (_rand(style.seed, i, 1) - 0.5) * spread / count
        dist = radius * (0.45 + 0.55 * _rand(style.seed, i, 2)) * travel
        dx, dy = _dir(a)
        p = (center[0] + dx * dist, center[1] + dy * dist)
        q = (1.0 - u) ** 0.8
        particle(canvas, style, _snap(style, center, p), size * (0.7 + 0.5 * _rand(style.seed, i, 3)) * (1.0 - 0.45 * u),
                 q, heat=0.95 - u * 0.8, angle=a, stretch=1.0 + (1.0 - u))


def implosion_pop(
    canvas: FxCanvas,
    u: float,
    center: Point,
    style: BlastStyle,
    *,
    radius: float = 26.0,
    count: int = 10,
    pop_at: float = 0.62,
    size: float = 4.0,
) -> None:
    """Grains GATHER into ``center`` along a twist, then it pops once."""
    if not _live(u):
        return
    if u < pop_at:
        k = smooth(u / pop_at)
        for i in range(count):
            a0 = 360.0 * i / count + _rand(style.seed, i) * 20.0
            a = a0 + 70.0 * k
            r = radius * (1.0 - k) * (0.75 + 0.25 * _rand(style.seed, i, 7)) + 1.0
            dx, dy = _dir(a)
            p = (center[0] + dx * r, center[1] + dy * r)
            particle(canvas, style, _snap(style, center, p), size * (0.6 + 0.4 * k), 0.25 + 0.75 * k,
                     heat=0.3 + 0.6 * k, angle=a + 180.0, stretch=0.8)
        canvas.ellipse(center, 1.0 + 2.5 * k, 1.0 + 2.5 * k, fade(style.core, 0.6 * k), None)
        return
    v = (u - pop_at) / (1.0 - pop_at)
    q = 1.0 - v
    canvas.star(center, size * (1.6 + 2.2 * smooth(min(1.0, v * 2.5))), fade(style.core, q), points=4, inner=0.28,
                rotation=45.0, outline=fade(style.body, q))
    shockwave_ring(canvas, v, center, style, radius=radius * 0.8, width=1.1)


def spark_spray(
    canvas: FxCanvas,
    u: float,
    origin: Point,
    style: BlastStyle,
    *,
    direction: float = -90.0,
    spread: float = 50.0,
    length: float = 34.0,
    count: int = 10,
    gravity: float = 22.0,
    size: float = 3.2,
) -> None:
    """Fast streaks leave ``origin`` in a cone and droop under ``gravity``."""
    if not _live(u):
        return
    for i in range(count):
        a = direction + (_rand(style.seed, i, 11) - 0.5) * spread
        speed = length * (0.55 + 0.45 * _rand(style.seed, i, 12))
        dx, dy = _dir(a)
        tt = _ease_out(u) * (0.85 + 0.15 * _rand(style.seed, i, 13))
        p = (origin[0] + dx * speed * tt, origin[1] + dy * speed * tt + gravity * u * u)
        vel = math.degrees(math.atan2(dy * speed * (1.0 - u) ** 2 + 2.0 * gravity * u, dx * speed * (1.0 - u) ** 2 + 1e-6))
        particle(canvas, style, _snap(style, origin, p), size * (1.0 - 0.5 * u), (1.0 - u) ** 0.9, heat=1.0 - u,
                 angle=vel, stretch=1.0 + 1.6 * (1.0 - u))


def ripple_arcs(
    canvas: FxCanvas,
    u: float,
    origin: Point,
    style: BlastStyle,
    *,
    direction: float = 0.0,
    spread: float = 70.0,
    reach: float = 40.0,
    count: int = 3,
    width: float = 1.4,
    flatten: float = 1.0,
) -> None:
    """Concentric arcs run out of ``origin`` along ``direction``: a sound
    wave's grammar, three fronts a beat apart, each thinner than the last."""
    if not _live(u):
        return
    for j in range(count):
        v = u * 1.25 - j * 0.16
        if not 0.0 < v <= 1.0:
            continue
        r = 4.0 + reach * _ease_out(v)
        q = (1.0 - v) * (1.0 - 0.22 * j)
        pts = _ring_points(origin, r, r * flatten, direction, -spread / 2, spread / 2, 14)
        if style.particle == "cell" and style.grid > 0:
            for p in pts[::2]:
                particle(canvas, style, _snap(style, origin, p), style.grid * 0.75, q, heat=0.9 - 0.3 * j)
        else:
            inked_line(canvas, style, pts, fade(style.heat(0.95 - 0.3 * j), q), max(0.35, width * (1.0 - 0.3 * j)))


def light_pillar(
    canvas: FxCanvas,
    u: float,
    base: Point,
    style: BlastStyle,
    *,
    height: float = 80.0,
    width: float = 9.0,
    direction: float = -90.0,
    motes: int = 6,
) -> None:
    """A beam SHOOTS out of ``base`` (up, by default), swells, and thins away;
    ``motes`` ride up inside it."""
    if not _live(u):
        return
    grow = _ease_out(min(1.0, u / 0.3))
    q = 1.0 if u < 0.45 else (1.0 - (u - 0.45) / 0.55)
    w = width * (0.35 + 0.65 * math.sin(math.pi * min(1.0, u * 1.3))) * (1.0 - 0.5 * max(0.0, u - 0.6))
    dx, dy = _dir(direction)
    px, py = -dy, dx
    tip = (base[0] + dx * height * grow, base[1] + dy * height * grow)
    for scale, h, a in ((1.0, 0.25, 0.32), (0.55, 0.65, 0.6), (0.18, 1.0, 0.95)):
        ww = w * scale * 0.5
        canvas.polygon(
            [(base[0] + px * ww, base[1] + py * ww), (tip[0] + px * ww * 0.6, tip[1] + py * ww * 0.6),
             (tip[0] - px * ww * 0.6, tip[1] - py * ww * 0.6), (base[0] - px * ww, base[1] - py * ww)],
            fade(style.heat(h), q * a),
        )
    for i in range(motes):
        f = (_rand(style.seed, i, 21) + u * 1.4) % 1.0
        if f > grow:
            continue
        off = (_rand(style.seed, i, 22) - 0.5) * w
        p = (base[0] + dx * height * f + px * off, base[1] + dy * height * f + py * off)
        particle(canvas, style, _snap(style, base, p), 3.0, q * (1.0 - f * 0.5), heat=0.9, angle=direction)


def fracture(
    canvas: FxCanvas,
    u: float,
    origin: Point,
    style: BlastStyle,
    *,
    reach: float = 36.0,
    directions: Sequence[float] = (0.0, 180.0),
    chips: int = 10,
    rise: float = 18.0,
) -> None:
    """The ground CRACKS from ``origin`` along ``directions`` (jagged, with a
    branch), and chips pop up off the crack and fall back."""
    if not _live(u):
        return
    grow = _ease_out(min(1.0, u / 0.5))
    q = 1.0 if u < 0.55 else (1.0 - (u - 0.55) / 0.45)
    for d_i, d in enumerate(directions):
        dx, dy = _dir(d)
        pts = [origin]
        steps = 6
        for s in range(1, steps + 1):
            f = s / steps * reach * grow
            jag = (_rand(style.seed, d_i, s) - 0.5) * 4.0
            pts.append((origin[0] + dx * f, origin[1] + dy * f + jag * 0.6 - abs(dx) * jag * 0.2))
        canvas.line(pts, fade(style.heat(0.35), q * 0.8), 2.6)
        inked_line(canvas, style, pts, fade(style.heat(1.0), q), 1.1)
        if len(pts) > 3:
            mid = pts[3]
            bd = d + (25.0 if d_i % 2 == 0 else -25.0)
            bx, by = _dir(bd)
            canvas.line([mid, (mid[0] + bx * reach * 0.3 * grow, mid[1] + by * reach * 0.3 * grow - 1.0)],
                        fade(style.heat(0.8), q), 0.9)
        for c in range(chips // max(1, len(directions))):
            f = (0.25 + 0.7 * _rand(style.seed, d_i, c, 31)) * reach
            if f > reach * grow:
                continue
            born = f / reach * 0.5
            v = clamp01((u - born) / 0.5)
            if v <= 0.0 or v >= 1.0:
                continue
            h = rise * (0.6 + 0.4 * _rand(style.seed, d_i, c, 32)) * 4.0 * v * (1.0 - v)
            p = (origin[0] + dx * f + dx * 6.0 * v, origin[1] - h)
            particle(canvas, style, _snap(style, origin, p), 4.6 * (1.0 - 0.4 * v), 1.0 - v * v, heat=0.8,
                     angle=-90.0 if v < 0.5 else 90.0)


def lattice_bloom(
    canvas: FxCanvas,
    u: float,
    origin: Point,
    style: BlastStyle,
    *,
    radius: int = 5,
    pitch: float = 6.0,
    life: float = 2.5,
    direction: float | None = None,
    cone: float = 80.0,
) -> None:
    """A grid BLOOMS out of ``origin``: the cell ``d`` steps away (Manhattan)
    is born on generation ``d`` and dies ``life`` generations later -- a
    diamond front with a dying wake. ``direction`` limits it to a cone."""
    if not _live(u):
        return
    front = u * (radius + life)
    for iy in range(-radius, radius + 1):
        for ix in range(-radius, radius + 1):
            d = abs(ix) + abs(iy)
            if d > radius:
                continue
            if direction is not None and d > 0:
                a = math.degrees(math.atan2(iy, ix))
                diff = (a - direction + 180.0) % 360.0 - 180.0
                if abs(diff) > cone / 2:
                    continue
            age = front - d
            if age < 0.0 or age > life:
                continue
            # Checkerboard parity: half the lattice is live on each generation.
            if (ix + iy + int(front)) % 2 and d > 1:
                continue
            q = 1.0 - age / life
            p = (origin[0] + ix * pitch, origin[1] + iy * pitch)
            particle(canvas, style, p, pitch * (0.55 + 0.3 * q), q, heat=0.4 + 0.6 * q,
                     angle=math.degrees(math.atan2(iy, ix)) if d else 0.0)


def fan_burst(
    canvas: FxCanvas,
    u: float,
    origin: Point,
    style: BlastStyle,
    *,
    direction: float = -90.0,
    spread: float = 100.0,
    length: float = 30.0,
    petals: int = 5,
    width: float = 6.0,
) -> None:
    """Lens-shaped petals OPEN one after another across a fan, then fade."""
    if not _live(u):
        return
    for i in range(petals):
        born = i / petals * 0.35
        v = clamp01((u - born) / (1.0 - born))
        if v <= 0.0 or v >= 1.0:
            continue
        a = direction - spread / 2 + spread * (i + 0.5) / petals
        dx, dy = _dir(a)
        px, py = -dy, dx
        ln = length * _ease_out(min(1.0, v * 1.8)) * (0.8 + 0.2 * _rand(style.seed, i))
        w = width * math.sin(math.pi * min(1.0, v * 1.2)) * 0.5
        start = (origin[0] + dx * 3.0, origin[1] + dy * 3.0)
        end = (origin[0] + dx * ln, origin[1] + dy * ln)
        mid = ((start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5)
        q = 1.0 - v
        canvas.polygon([start, (mid[0] + px * w, mid[1] + py * w), end, (mid[0] - px * w, mid[1] - py * w)],
                       fade(style.heat(0.55), q * 0.55), fade(style.heat(0.95), q), 0.6)
        particle(canvas, style, _snap(style, origin, end), width * 0.55, q, heat=0.9, angle=a)


def impact_pop(
    canvas: FxCanvas,
    u: float,
    center: Point,
    style: BlastStyle,
    *,
    size: float = 8.0,
    direction: float = 0.0,
    ticks: int = 6,
) -> None:
    """A small, quick HIT: a four-point flash, short ticks thrown mostly along
    ``direction``, a ring. For jabs and kicks rather than smashes."""
    if not _live(u):
        return
    flash = math.sin(math.pi * min(1.0, u * 2.2)) if u < 0.45 else 0.0
    if flash > 0.0:
        canvas.star(center, size * (0.7 + 0.5 * flash), fade(style.core, flash), points=4, inner=0.3,
                    rotation=direction + 45.0, outline=fade(style.body, flash))
    for i in range(ticks):
        a = direction + (i - (ticks - 1) / 2) * (150.0 / max(1, ticks - 1)) + (_rand(style.seed, i, 41) - 0.5) * 12.0
        dx, dy = _dir(a)
        d0 = size * (0.5 + 1.1 * _ease_out(u))
        p = (center[0] + dx * d0, center[1] + dy * d0)
        particle(canvas, style, _snap(style, center, p), size * 0.38 * (1.0 - 0.5 * u), (1.0 - u) ** 1.1, heat=0.9 - 0.5 * u,
                 angle=a, stretch=1.4 - u)
    shockwave_ring(canvas, u, center, style, radius=size * 1.6, width=0.9)


def swept_trail(
    canvas: FxCanvas,
    path: Sequence[Point],
    style: BlastStyle,
    *,
    width: float = 7.0,
    alpha: float = 1.0,
    spacing: float = 5.0,
) -> None:
    """A trail laid along ``path`` (oldest first, the striking tip LAST).

    It is widest and hottest at the tip and tapers to nothing at the tail, and
    nothing is drawn past the tip: a trail is where the strike WAS. Cells drop
    on a lattice along it, older ones smaller and cooler.
    """
    if len(path) < 2 or alpha <= 0.01:
        return
    n = len(path)
    # Ribbon: one quad per segment, so its width tapers along the path.
    for i in range(n - 1):
        a, b = path[i], path[i + 1]
        fa, fb = i / (n - 1), (i + 1) / (n - 1)
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        px, py = -dy / L, dx / L
        wa, wb = width * 0.5 * fa ** 0.9, width * 0.5 * fb ** 0.9
        canvas.polygon(
            [(a[0] + px * wa, a[1] + py * wa), (b[0] + px * wb, b[1] + py * wb),
             (b[0] - px * wb * 0.35, b[1] - py * wb * 0.35), (a[0] - px * wa * 0.35, a[1] - py * wa * 0.35)],
            fade(style.heat(0.3 + 0.5 * fb), alpha * (0.15 + 0.55 * fb)),
        )
    inked_line(canvas, style, list(path[max(0, n // 3):]), fade(style.core, alpha), 0.9)
    # Grains dropped along the path, spaced by arc length.
    carried = 0.0
    for i in range(n - 1):
        a, b = path[i], path[i + 1]
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        pos = spacing - carried
        while pos <= seg:
            f = (i + pos / max(seg, 1e-6)) / (n - 1)
            p = (a[0] + (b[0] - a[0]) * pos / max(seg, 1e-6), a[1] + (b[1] - a[1]) * pos / max(seg, 1e-6))
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            particle(canvas, style, _snap(style, path[-1], p), width * 0.5 * (0.35 + 0.65 * f), alpha * f, heat=0.3 + 0.7 * f,
                     angle=ang)
            pos += spacing
        carried = seg - (pos - spacing)


#: Every blast by name: for galleries, and for a character choosing by name.
BLASTS = {
    "eruption": eruption,
    "shockwave_ring": shockwave_ring,
    "shard_burst": shard_burst,
    "implosion_pop": implosion_pop,
    "spark_spray": spark_spray,
    "ripple_arcs": ripple_arcs,
    "light_pillar": light_pillar,
    "fracture": fracture,
    "lattice_bloom": lattice_bloom,
    "fan_burst": fan_burst,
    "impact_pop": impact_pop,
}


def window(t: float, start: float, end: float) -> float:
    """Map clip time ``t`` onto a blast's own life over [start, end]; outside
    it the result is outside [0, 1] and the blast draws nothing."""
    return (t - start) / max(1e-6, end - start)


__all__ = [
    "BLASTS",
    "BlastStyle",
    "PARTICLES",
    "eruption",
    "fan_burst",
    "fracture",
    "inked_line",
    "implosion_pop",
    "impact_pop",
    "lattice_bloom",
    "light_pillar",
    "particle",
    "ripple_arcs",
    "shard_burst",
    "shockwave_ring",
    "spark_spray",
    "swept_trail",
    "window",
]
