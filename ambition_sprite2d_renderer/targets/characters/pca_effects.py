"""Cellular-automaton combat effects for the Perfect Cellular Automaton.

The effect language is discrete and rule-driven: square cells, spacetime rows,
causal cones, fixed points, and stable gliders.  Nothing here changes the body
art. Effects are composed around the solved rig so they follow hands/core while
the canonical SVG remains authoritative.
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

from ...profiling import profile

from . import _fx_blasts as fxb
from ._svg_fighter_effects import FxCanvas, bone_origin, clamp01, fade, pulse, smooth

Color = tuple[int, int, int, int]
Point = tuple[float, float]
World = Mapping[str, object]

OUTLINE: Color = (8, 16, 15, 255)
ACID: Color = (182, 243, 74, 255)
ACID_LIGHT: Color = (232, 255, 175, 255)
EMERALD: Color = (19, 122, 90, 255)
EMERALD_DARK: Color = (13, 59, 49, 255)
VIOLET: Color = (112, 70, 168, 255)
VIOLET_LIGHT: Color = (182, 108, 227, 255)
MAGENTA: Color = (240, 92, 184, 255)
CYAN: Color = (84, 216, 232, 255)
CERAMIC: Color = (239, 232, 207, 255)

EFFECTFUL_ANIMATIONS = frozenset(
    {
        "parry",
        "jab",
        "punch",
        "slash",
        "dash_attack",
        "attack_side",
        "attack_up",
        "attack_down",
        "smash_charge",
        "smash_forward",
        "smash_up",
        "smash_down",
        "air_neutral",
        "air_forward",
        "air_back",
        "air_up",
        "air_down",
        "shoot",
        "special",
        "charge",
        "fly",
        "final_smash",
        "blink_out",
        "blink_in",
    }
)


def _window(t: float, attack: float = 0.52) -> float:
    t = clamp01(t)
    if t <= attack:
        return smooth(t / max(attack, 1e-6))
    return smooth((1.0 - t) / max(1.0 - attack, 1e-6))


def _core(world: World) -> Point:
    torso = bone_origin(world, "torso", (64.0, 86.0))
    pelvis = bone_origin(world, "pelvis", (64.0, 108.0))
    return ((torso[0] + pelvis[0]) * 0.5, (torso[1] + pelvis[1]) * 0.5)


def _hands(world: World) -> tuple[Point, Point]:
    a = bone_origin(world, "near_arm_hand", (42.0, 112.0))
    b = bone_origin(world, "far_arm_hand", (86.0, 112.0))
    # This view faces +x. Pick the screen-right hand dynamically so the effect
    # follows whichever arm actually becomes the forward attacking limb.
    return (a, b) if a[0] >= b[0] else (b, a)


@profile
def _cell(
    canvas: FxCanvas,
    center: Point,
    size: float,
    color: Color,
    *,
    alpha: float,
    fill_alpha: float = 0.36,
) -> None:
    h = size * 0.5
    canvas.polygon(
        [
            (center[0] - h, center[1] - h),
            (center[0] + h, center[1] - h),
            (center[0] + h, center[1] + h),
            (center[0] - h, center[1] + h),
        ],
        fade(color, fill_alpha * alpha),
        fade(ACID_LIGHT, 0.82 * alpha),
        0.65,
    )


def _rule110_step(row: Sequence[int]) -> list[int]:
    # Wolfram rule 110, periodic boundary. This is a deterministic visual seed,
    # not gameplay simulation state.
    bits = (0, 1, 1, 0, 1, 1, 1, 0)
    n = len(row)
    out = []
    for i in range(n):
        left = int(row[(i - 1) % n])
        mid = int(row[i])
        right = int(row[(i + 1) % n])
        pattern = (left << 2) | (mid << 1) | right
        out.append(bits[pattern])
    return out


@profile
def _rule_rows(width: int, steps: int, *, seed: int = 0) -> list[list[int]]:
    row = [0] * width
    row[width // 2] = 1
    if width > 5:
        row[(width // 2 + 2 + seed) % width] = 1
    rows = [row]
    for _ in range(max(0, steps - 1)):
        row = _rule110_step(row)
        rows.append(row)
    return rows


@profile
def _draw_rule_strip(
    canvas: FxCanvas,
    origin: Point,
    *,
    cols: int,
    rows: int,
    cell: float,
    dx: float,
    dy: float,
    alpha: float,
    seed: int = 0,
    color: Color = ACID,
) -> None:
    states = _rule_rows(cols, rows, seed=seed)
    for iy, state in enumerate(states):
        for ix, live in enumerate(state):
            if not live:
                continue
            p = (origin[0] + ix * dx, origin[1] + iy * dy)
            _cell(canvas, p, cell, color if (ix + iy) % 3 else CYAN, alpha=alpha)


def _glider(canvas: FxCanvas, center: Point, size: float, color: Color, alpha: float, mirror: bool = False) -> None:
    pattern = ((1, 0), (2, 1), (0, 2), (1, 2), (2, 2))
    s = -1.0 if mirror else 1.0
    for x, y in pattern:
        _cell(
            canvas,
            (center[0] + s * (x - 1) * size, center[1] + (y - 1) * size),
            size * 0.72,
            color,
            alpha=alpha,
            fill_alpha=0.46,
        )


@profile
def _lattice(canvas: FxCanvas, center: Point, rx: float, ry: float, step: float, alpha: float) -> None:
    x = -rx
    while x <= rx + 0.01:
        canvas.line(
            [(center[0] + x, center[1] - ry), (center[0] + x, center[1] + ry)],
            fade(EMERALD, 0.26 * alpha),
            0.45,
        )
        x += step
    y = -ry
    while y <= ry + 0.01:
        canvas.line(
            [(center[0] - rx, center[1] + y), (center[0] + rx, center[1] + y)],
            fade(VIOLET, 0.22 * alpha),
            0.45,
        )
        y += step


@profile
def _generation_beam(canvas: FxCanvas, t: float, world: World, *, front: bool) -> None:
    hand, _other = _hands(world)
    q = _window(t, 0.50)
    if q <= 0.001:
        return
    if not front:
        canvas.line([hand, (139.0, hand[1])], fade(EMERALD, 0.28 * q), 2.8)
        canvas.line([hand, (139.0, hand[1])], fade(ACID_LIGHT, 0.62 * q), 0.75)
        return
    rows = _rule_rows(11, 4, seed=1)
    x0 = hand[0] + 8.0
    for iy, row in enumerate(rows):
        for ix, live in enumerate(row):
            if not live:
                continue
            x = x0 + ix * 6.0
            y = hand[1] + (iy - 1.5) * 6.0
            age = 0.72 + 0.28 * math.sin((x * 0.07 + t * math.tau))
            _cell(canvas, (x, y), 4.6, ACID if (ix + iy) % 2 else CYAN, alpha=q * age)
    canvas.ellipse(hand, 5.0 + 2.0 * pulse(t), 5.0 + 2.0 * pulse(t), fade(ACID, 0.28 * q), fade(ACID_LIGHT, 0.86 * q), 0.85)


@profile
def _causal_cone(canvas: FxCanvas, t: float, world: World, *, front: bool) -> None:
    core = _core(world)
    hand, _ = _hands(world)
    q = _window(t, 0.58)
    apex = (max(hand[0], core[0] + 5.0), core[1])
    if not front:
        canvas.polygon(
            [apex, (138.0, core[1] - 48.0), (138.0, core[1] + 48.0)],
            fade(EMERALD_DARK, 0.10 * q),
            fade(ACID, 0.38 * q),
            0.8,
        )
        return
    states = _rule_rows(9, 8, seed=2)
    for generation, row in enumerate(states):
        x = apex[0] + 6.0 + generation * 8.2
        spread = 3.2 + generation * 2.1
        live_indexes = [i for i, value in enumerate(row) if value]
        for index in live_indexes:
            y = core[1] + (index - 4) * spread * 0.62
            _cell(canvas, (x, y), 4.8, ACID if generation % 2 == 0 else VIOLET_LIGHT, alpha=0.76 * q, fill_alpha=0.40)
    canvas.arrow(apex, (137.0, core[1]), fade(CYAN, 0.64 * q), 0.8, 3.2)


@profile
def _fixed_point(canvas: FxCanvas, t: float, world: World, *, front: bool) -> None:
    core = _core(world)
    q = 0.55 + 0.45 * pulse(t)
    if not front:
        _lattice(canvas, core, 40.0, 44.0, 10.0, q)
        for radius, color in ((42.0, VIOLET), (31.0, EMERALD), (21.0, ACID)):
            h = radius * (0.90 + 0.08 * math.sin(t * math.tau))
            canvas.polygon(
                [(core[0], core[1] - h), (core[0] + h, core[1]), (core[0], core[1] + h), (core[0] - h, core[1])],
                fade(color, 0.025 * q),
                fade(color, 0.42 * q),
                0.9,
            )
    else:
        # Stable 3x3 attractor: center and corners always on, edges pulse.
        for iy in range(-1, 2):
            for ix in range(-1, 2):
                stable = (ix == 0 and iy == 0) or (abs(ix) == 1 and abs(iy) == 1)
                alpha = q * (0.88 if stable else 0.34 + 0.25 * pulse(t))
                _cell(canvas, (core[0] + ix * 7.2, core[1] + iy * 7.2), 5.2, ACID if stable else CYAN, alpha=alpha)


@profile
def _glider_ascent(canvas: FxCanvas, t: float, world: World, *, front: bool) -> None:
    core = _core(world)
    q = 0.52 + 0.48 * pulse(t)
    if not front:
        for dx, color in ((-18.0, VIOLET), (18.0, EMERALD)):
            canvas.line([(core[0] + dx, 174.0), (core[0] + dx, 18.0)], fade(color, 0.30 * q), 0.85)
    for i in range(4):
        y = 168.0 - ((t * 108.0 + i * 38.0) % 168.0)
        x = core[0] + (-13.0 if i % 2 == 0 else 13.0)
        _glider(canvas, (x, y), 4.0, ACID if i % 2 == 0 else CYAN, 0.65 * q, mirror=bool(i % 2))
    if front:
        for r in (11.0, 18.0, 26.0):
            canvas.ellipse((core[0], 159.0), r, r * 0.28, None, fade(ACID_LIGHT, (0.52 - r * 0.009) * q), 0.8)


@profile
def _final_lattice(canvas: FxCanvas, t: float, world: World, *, front: bool) -> None:
    core = _core(world)
    q = _window(t, 0.62)
    if not front:
        _lattice(canvas, core, 61.0, 82.0, 8.0, q)
        canvas.polygon(
            [(core[0], 9.0), (126.0, core[1]), (core[0], 181.0), (2.0, core[1])],
            fade(EMERALD_DARK, 0.075 * q),
            fade(ACID, 0.40 * q),
            1.1,
        )
        return
    rows = _rule_rows(15, 12, seed=3)
    for gy, row in enumerate(rows):
        y = 26.0 + gy * 11.0
        phase = (t * 12.0 - gy) % 12.0
        row_alpha = q * (0.42 + 0.38 * math.exp(-0.18 * phase * phase))
        for gx, live in enumerate(row):
            if not live:
                continue
            x = 8.0 + gx * 8.0
            _cell(canvas, (x, y), 5.0, ACID if (gx + gy) % 4 else VIOLET_LIGHT, alpha=row_alpha, fill_alpha=0.33)
    for radius, color in ((7.0, ACID_LIGHT), (13.0, MAGENTA), (20.0, CYAN)):
        canvas.ellipse(core, radius * (0.85 + 0.15 * pulse(t)), radius * (0.85 + 0.15 * pulse(t)), None, fade(color, 0.72 * q), 0.9)
    canvas.star(core, 5.3 + 2.0 * pulse(t), fade(CERAMIC, 0.42 * q), points=4, inner=0.36, outline=fade(ACID_LIGHT, 0.82 * q))


@profile
def _parry(canvas: FxCanvas, t: float, world: World) -> None:
    core = _core(world)
    q = _window(t, 0.48)
    for ring, color in ((0, ACID), (1, CYAN), (2, VIOLET_LIGHT)):
        r = 27.0 + ring * 7.0
        canvas.polygon(
            [(core[0], core[1] - r), (core[0] + r, core[1]), (core[0], core[1] + r), (core[0] - r, core[1])],
            fade(color, 0.025 * q),
            fade(color, (0.62 - ring * 0.12) * q),
            1.0,
        )
    for ix, iy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        _cell(canvas, (core[0] + ix * 20.0, core[1] + iy * 26.0), 5.0, ACID, alpha=0.70 * q)


# --- Ground attacks: blasts from the shared vocabulary ----------------------
#
# Each attack anchors its blast on the limb that lands it (solved `world`), and
# maps clip time onto the blast's own life with `window`. One-shot frames sit
# at i/(n-1), so the windows below are written around each row's contact
# frames. PCA's blasts are made of lattice cells; sparks only as accents.

# A dark emerald rim keeps the pale cells legible on a pale stage.
PCA_CELLS = fxb.BlastStyle(particle="cell", core=ACID_LIGHT, body=ACID, edge=VIOLET_LIGHT,
                           outline=EMERALD_DARK, fill=0.9, grid=6.0)
PCA_CELLS_COOL = fxb.BlastStyle(particle="cell", core=ACID_LIGHT, body=CYAN, edge=VIOLET,
                                outline=EMERALD_DARK, fill=0.9, grid=6.0, seed=3)
PCA_SPARKS = fxb.BlastStyle(particle="spark", core=ACID_LIGHT, body=ACID, edge=EMERALD, outline=EMERALD_DARK, seed=5)
GROUND_Y = 176.0


def _bone_lengths() -> Mapping[str, float]:
    global _LENGTHS
    if _LENGTHS is None:
        # Late import: the target module imports this one.
        from .perfect_cellular_automaton import _doc

        _LENGTHS = {name: bone.length for name, bone in _doc().build_skeleton().bones.items()}
    return _LENGTHS


_LENGTHS: Mapping[str, float] | None = None


def _tip(world: World, name: str, frac: float = 0.75, fallback: Point = (64.0, 100.0)) -> Point:
    """A point ``frac`` of the way along a hand/foot bone: its business end."""
    origin = bone_origin(world, name, fallback)
    angle = getattr(world.get(name), "angle", None)
    if angle is None:
        return origin
    length = _bone_lengths().get(name, 0.0) * frac
    a = math.radians(float(angle))
    return origin[0] + math.cos(a) * length, origin[1] + math.sin(a) * length


def _palms(world: World) -> Point:
    a = _tip(world, "near_arm_hand", 0.5)
    b = _tip(world, "far_arm_hand", 0.5)
    return (a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5


def _jab(canvas: FxCanvas, t: float, world: World) -> None:
    fxb.impact_pop(canvas, fxb.window(t, 0.40, 0.95), _tip(world, "far_arm_hand"), PCA_CELLS, size=10.0)


def _punch(canvas: FxCanvas, t: float, world: World) -> None:
    fist = _tip(world, "near_arm_hand")
    fxb.impact_pop(canvas, fxb.window(t, 0.30, 0.95), fist, PCA_CELLS, size=12.0)
    fxb.ripple_arcs(canvas, fxb.window(t, 0.36, 1.0), fist, PCA_CELLS_COOL, spread=64.0, reach=30.0, count=2)


#: The slash's trail: its head stops where the rake's follow-through ends
#: (later frames are the recovery, which must not draw backwards), its tail
#: lags behind and catches up, so the trail travels and leaves nothing ahead.
_SLASH_START, _SLASH_HEAD_END, _SLASH_LAG = 0.15, 0.72, 0.30


def _slash(canvas: FxCanvas, t: float, world: World) -> None:
    head = min(t, _SLASH_HEAD_END)
    tail = max(_SLASH_START, t - _SLASH_LAG)
    if head - tail < 0.03:
        return
    from .perfect_cellular_automaton import _doc

    doc = _doc()
    steps = 9
    path = []
    for i in range(steps + 1):
        st = tail + (head - tail) * i / steps
        solved, _ = doc.solve("slash", st)
        path.append(_tip(solved, "near_arm_hand", 0.9))
    alpha = 1.0 if t <= _SLASH_HEAD_END else clamp01(1.0 - (t - _SLASH_HEAD_END) / (1.0 - _SLASH_HEAD_END))
    fxb.swept_trail(canvas, path, PCA_CELLS, width=15.0, alpha=alpha, spacing=5.0)


def _kick(canvas: FxCanvas, t: float, world: World) -> None:
    foot = _tip(world, "far_leg_foot", 0.85)
    u = fxb.window(t, 0.32, 0.92)
    fxb.shard_burst(canvas, u, foot, PCA_CELLS, radius=28.0, direction=0.0, spread=110.0, count=9, size=6.0)
    fxb.shockwave_ring(canvas, fxb.window(t, 0.34, 0.80), foot, PCA_CELLS_COOL, radius=12.0, flatten=2.2, width=1.6)


def _rising_claw(canvas: FxCanvas, t: float, world: World) -> None:
    claw = _tip(world, "far_arm_hand", 0.9)
    fxb.spark_spray(canvas, fxb.window(t, 0.30, 0.90), claw, PCA_SPARKS, direction=-95.0, spread=70.0,
                    length=36.0, count=10, gravity=12.0, size=4.4)
    fxb.fan_burst(canvas, fxb.window(t, 0.34, 0.90), claw, PCA_CELLS, direction=-90.0, spread=90.0,
                  length=22.0, petals=4, width=7.0)


def _sweep(canvas: FxCanvas, t: float, world: World) -> None:
    foot = _tip(world, "far_leg_foot", 0.85)
    ground = (foot[0], GROUND_Y - 1.0)
    fxb.fracture(canvas, fxb.window(t, 0.32, 1.0), ground, PCA_CELLS, reach=34.0, directions=(0.0, 172.0), chips=10, rise=18.0)
    fxb.spark_spray(canvas, fxb.window(t, 0.34, 0.86), ground, PCA_SPARKS, direction=-20.0, spread=30.0,
                    length=36.0, count=9, gravity=8.0, size=4.2)


def _palm_strike(canvas: FxCanvas, t: float, world: World) -> None:
    palms = _palms(world)
    fxb.ripple_arcs(canvas, fxb.window(t, 0.26, 0.96), palms, PCA_CELLS, spread=72.0, reach=28.0, count=3)
    fxb.shockwave_ring(canvas, fxb.window(t, 0.30, 0.78), palms, PCA_CELLS_COOL, radius=13.0, flatten=2.3, width=1.8)


def _smash_gather(canvas: FxCanvas, t: float, world: World) -> None:
    """The held charge: cells keep gathering into the drawn-back hands."""
    u = ((t * 2.0) % 1.0) * 0.6
    fxb.implosion_pop(canvas, u, _palms(world), PCA_CELLS, radius=28.0, count=12, pop_at=0.62, size=5.0)


def _smash_forward(canvas: FxCanvas, t: float, world: World) -> None:
    palms = _palms(world)
    # Gathers through the coil and pops on the thrust frame (t = 3/7).
    fxb.implosion_pop(canvas, fxb.window(t, 0.05, 0.66), palms, PCA_CELLS_COOL, radius=28.0, count=12, pop_at=0.62, size=5.0)
    fxb.lattice_bloom(canvas, fxb.window(t, 0.40, 0.98), (palms[0] + 4.0, palms[1]), PCA_CELLS, radius=6, pitch=6.0,
                      life=3.5, direction=0.0, cone=80.0)


def _smash_up(canvas: FxCanvas, t: float, world: World, *, front: bool) -> None:
    palms = _palms(world)
    if not front:
        fxb.light_pillar(canvas, fxb.window(t, 0.36, 1.0), palms, PCA_CELLS, height=62.0, width=20.0, motes=8)
        return
    fxb.shard_burst(canvas, fxb.window(t, 0.40, 0.88), palms, PCA_CELLS_COOL, radius=30.0, direction=-90.0,
                    spread=120.0, count=9, size=6.0)


#: The down smash's slam frame (frame 3 of 8): the eruptions stay where the
#: claws HIT, not where the recovering hands drift to.
_SLAM_T = 3.0 / 7.0


def _smash_down(canvas: FxCanvas, t: float, world: World, *, front: bool) -> None:
    """Two cell columns erupt from the floor where the claws hit (behind the
    body, so they flank it); the floor cracks between them (in front)."""
    core = _core(world)
    from .perfect_cellular_automaton import _doc

    slam, _ = _doc().solve("smash_down", _SLAM_T)
    hands = (_tip(slam, "near_arm_hand", 0.6), _tip(slam, "far_arm_hand", 0.6))
    for i, hand in enumerate(hands):
        style = PCA_CELLS if i else PCA_CELLS_COOL
        if not front:
            fxb.eruption(canvas, fxb.window(t, 0.38, 1.0), (hand[0], GROUND_Y), style.with_seed(i), height=96.0, pitch=7.0)
            continue
        fxb.shockwave_ring(canvas, fxb.window(t, 0.40, 0.80), (hand[0], GROUND_Y), style, radius=20.0, flatten=0.28, width=1.8)
    if front:
        fxb.fracture(canvas, fxb.window(t, 0.38, 0.95), (core[0], GROUND_Y), PCA_CELLS, reach=46.0, chips=10)


_GROUND_ATTACKS = {
    "jab": _jab,
    "punch": _punch,
    "slash": _slash,
    "attack_side": _kick,
    "attack_up": _rising_claw,
    "attack_down": _sweep,
    "dash_attack": _palm_strike,
    "smash_charge": _smash_gather,
    "smash_forward": _smash_forward,
}


@profile
def _air_cells(canvas: FxCanvas, t: float, world: World, animation: str) -> None:
    core = _core(world)
    q = _window(t, 0.50)
    if animation == "air_neutral":
        for i in range(10):
            a = t * math.tau * 0.65 + i * math.tau / 10.0
            p = (core[0] + math.cos(a) * 39.0, core[1] + math.sin(a) * 42.0)
            _cell(canvas, p, 5.0, ACID if i % 2 == 0 else CYAN, alpha=0.68 * q)
        return
    direction = {
        "air_forward": (1.0, 0.0),
        "air_back": (-1.0, 0.0),
        "air_up": (0.0, -1.0),
        "air_down": (0.0, 1.0),
    }[animation]
    for i in range(5):
        along = 18.0 + i * 9.0
        cross = (i - 2) * 5.0
        x = core[0] + direction[0] * along - direction[1] * cross
        y = core[1] + direction[1] * along + direction[0] * cross
        _cell(canvas, (x, y), 6.0, ACID if i < 3 else VIOLET_LIGHT, alpha=(0.78 - i * 0.08) * q)


@profile
def _blink_cells(canvas: FxCanvas, t: float, world: World, *, entering: bool) -> None:
    core = _core(world)
    q = smooth(t) if entering else smooth(1.0 - t)
    radius = 48.0 * (1.0 - q)
    for i in range(14):
        a = i * math.tau / 14.0 + 0.4
        r = radius + (i % 3) * 5.0
        p = (core[0] + math.cos(a) * r, core[1] + math.sin(a) * r * 1.35)
        _cell(canvas, p, 4.6, ACID if i % 3 else MAGENTA, alpha=0.54 + 0.34 * q)


@profile
def draw_pca_behind(
    animation: str,
    canvas: FxCanvas,
    t: float,
    world: World,
    params: Mapping[str, float],
) -> None:
    del params
    if animation == "shoot":
        _generation_beam(canvas, t, world, front=False)
    elif animation == "special":
        _causal_cone(canvas, t, world, front=False)
    elif animation == "charge":
        _fixed_point(canvas, t, world, front=False)
    elif animation == "fly":
        _glider_ascent(canvas, t, world, front=False)
    elif animation == "final_smash":
        _final_lattice(canvas, t, world, front=False)
    elif animation == "parry":
        _parry(canvas, t, world)
    elif animation == "smash_up":
        _smash_up(canvas, t, world, front=False)
    elif animation == "smash_down":
        _smash_down(canvas, t, world, front=False)


@profile
def draw_pca_front(
    animation: str,
    canvas: FxCanvas,
    t: float,
    world: World,
    params: Mapping[str, float],
) -> None:
    del params
    if animation == "shoot":
        _generation_beam(canvas, t, world, front=True)
    elif animation == "special":
        _causal_cone(canvas, t, world, front=True)
    elif animation == "charge":
        _fixed_point(canvas, t, world, front=True)
    elif animation == "fly":
        _glider_ascent(canvas, t, world, front=True)
    elif animation == "final_smash":
        _final_lattice(canvas, t, world, front=True)
    elif animation == "smash_up":
        _smash_up(canvas, t, world, front=True)
    elif animation == "smash_down":
        _smash_down(canvas, t, world, front=True)
    elif animation in _GROUND_ATTACKS:
        _GROUND_ATTACKS[animation](canvas, t, world)
    elif animation in {"air_neutral", "air_forward", "air_back", "air_up", "air_down"}:
        _air_cells(canvas, t, world, animation)
    elif animation == "blink_out":
        _blink_cells(canvas, t, world, entering=False)
    elif animation == "blink_in":
        _blink_cells(canvas, t, world, entering=True)


__all__ = [
    "EFFECTFUL_ANIMATIONS",
    "draw_pca_behind",
    "draw_pca_front",
]
