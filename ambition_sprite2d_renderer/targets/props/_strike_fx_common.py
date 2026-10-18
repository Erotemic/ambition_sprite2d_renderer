"""The strike effects of the Smash cast: one recipe, a style and a palette each.

A fighter that names an attack sheet (`attack_vfx` in its catalog row) has its
strikes drawn with that sheet's rows (`rendering/slash_visuals.rs`); one that
names none draws a flat stand-in wedge. Each public `*_strike_fx` module is
one fighter's sheet: it states a STYLE (what kind of blow it is) and a PALETTE
(whose blow it is), and this module draws it.

Every row is in SWING SPACE, as `gnu_ton_slash.py` and `robot_slash.py` are:
the game stretches the frame onto the hit volume and turns it along the
strike, so `x = 0` is the hand end of the volume, `x = REACH` its far end, and
`y` runs across it about `AXIS_Y`.

Jon's rule for a strike effect (2026-10-12): it TRAVELS and FOLLOWS THROUGH.
The whole blow is there on the first frame (it lands with its picture), then
it goes from the end it started at, thins, and sheds bits that fly back and
out; the last frame is clear. Nothing is drawn ahead of the tip, and no frame
is the same at both ends.

Rows (the names `SlashSource` reads):

- ``side``: the forward blow, bowed a little over the axis.
- ``up``: the blow over the head, a bigger bow that curls at its end.
- ``down``: the low blow, bowed under the axis.
- ``poke``: a straight thrust.
- ``rise`` / ``fall``: a blow that goes from low to high (or high to low)
  across the front; the game turns it, so a rise to the left is a fall.

Styles:

- ``blade``: a crescent with a hard bright edge and fibres behind it.
- ``impact``: a fist or a kick: speed streaks along the blow and a burst
  where it lands.
- ``ink``: a pen stroke that lifts, with drops off its tip.
- ``shard``: a faceted crescent that breaks into triangles.
- ``energy``: a glowing ribbon that sheds motes (``mote`` names their shape:
  ``cell``, ``star``, ``dot`` or ``chalk``).

Each palette has a light core, a body colour and a darker edge, so a blow
reads in a dark room and a light one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ...core.draw import blending_draw

RGB = Tuple[int, int, int]
Point = Tuple[float, float]

FRAME_SIZE = (192, 96)
SUPER = 4
REACH = float(FRAME_SIZE[0])
AXIS_Y = FRAME_SIZE[1] / 2.0
HALF = FRAME_SIZE[1] / 2.0
# Six frames of 24 ms: the blow is up for the live part of a quick move and its
# trail is gone a little after.
ROWS: List[Tuple[str, int, int]] = [
    ("side", 6, 24),
    ("up", 6, 24),
    ("down", 6, 24),
    ("poke", 6, 24),
    ("rise", 6, 24),
    ("fall", 6, 24),
]


@dataclass(frozen=True)
class Palette:
    """A light core, the body colour, and the darker edge that keeps it legible
    on a light room. `accent` is the colour of what flies off."""

    core: RGB
    body: RGB
    edge: RGB
    accent: RGB


@dataclass(frozen=True)
class Path_:
    """The line of a blow in swing space: from `start` to `end` (x as a part of
    the reach, y in half heights, down positive), bowed by `bow` half heights,
    with a curl of `hook` at its end. `belly` is its widest (half heights) and
    `peak` where along it that is."""

    start: Point
    end: Point
    bow: float
    belly: float
    peak: float
    hook: float = 0.0
    #: A band about the line (a thrust, a streak) rather than a crescent on
    #: one side of it.
    centred: bool = False


PATHS: Dict[str, Path_] = {
    "side": Path_((0.05, 0.3), (0.95, 0.05), bow=-0.78, belly=1.0, peak=0.58),
    "up": Path_((0.05, 0.4), (0.9, 0.0), bow=-0.86, belly=0.95, peak=0.5, hook=1.0),
    "down": Path_((0.05, -0.3), (0.95, -0.05), bow=0.78, belly=0.95, peak=0.62),
    "poke": Path_((0.06, 0.0), (0.97, 0.0), bow=0.0, belly=0.62, peak=0.8, centred=True),
    "rise": Path_((0.06, 0.78), (0.93, -0.66), bow=-0.36, belly=0.9, peak=0.6, hook=0.6),
    "fall": Path_((0.06, -0.78), (0.93, 0.66), bow=0.36, belly=0.9, peak=0.6, hook=0.6),
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smooth(edge0: float, edge1: float, value: float) -> float:
    t = _clamp((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def _mix(a: RGB, b: RGB, k: float) -> RGB:
    k = _clamp(k)
    return tuple(round(a[i] * (1.0 - k) + b[i] * k) for i in range(3))  # type: ignore[return-value]


def _rgba(c: RGB, alpha: float = 1.0) -> Tuple[int, int, int, int]:
    return (c[0], c[1], c[2], max(0, min(255, round(255 * alpha))))


def _point(path: Path_, t: float) -> Point:
    """The line of the blow at `t` (0 at the hand, 1 at the tip), in pixels."""
    x0, y0 = path.start
    x1, y1 = path.end
    x = REACH * (x0 + (x1 - x0) * t)
    y = AXIS_Y + HALF * (y0 + (y1 - y0) * t) + HALF * path.bow * math.sin(math.pi * t) ** 0.85
    if path.hook > 0.0 and t > 0.62:
        # The follow through: the end of the blow comes round toward the hand,
        # on the side it was bowed to.
        k = _smooth(0.62, 1.0, t)
        x -= REACH * 0.14 * path.hook * k * k
        curl = -1.0 if (path.bow < 0.0 or (path.bow == 0.0 and y1 < y0)) else 1.0
        y += HALF * 0.42 * path.hook * k * k * curl
    return x, min(FRAME_SIZE[1] - 1.0, max(1.0, y))


def _width(path: Path_, t: float) -> float:
    """The full width of the blow at `t`: a point at each end, widest at `peak`."""
    k = _clamp(t) ** (math.log(0.5) / math.log(path.peak))
    return path.belly * HALF * math.sin(math.pi * k) ** 1.1


def _normal(path: Path_, t: float) -> Point:
    """The unit normal of the line at `t`, toward the inside of its bow."""
    a = _point(path, max(0.0, t - 0.01))
    b = _point(path, min(1.0, t + 0.01))
    tx, ty = b[0] - a[0], b[1] - a[1]
    n = math.hypot(tx, ty) or 1.0
    nx, ny = -ty / n, tx / n
    # Toward the inside: away from the side the line is bowed to.
    inside = 1.0 if path.bow <= 0.0 else -1.0
    if ny * inside < 0.0:
        nx, ny = -nx, -ny
    return nx, ny


def _band(path: Path_, t0: float, t1: float, scale: float, inset: float, steps: int = 56) -> List[Point]:
    """The outline of the blow from `t0` to `t1`: its edge and an edge `scale`
    of its width inside it, moved in by `inset` of the width. A centred blow is
    a band about its line."""
    outer: List[Point] = []
    inner: List[Point] = []
    for i in range(steps + 1):
        t = t0 + (t1 - t0) * i / steps
        x, y = _point(path, t)
        nx, ny = _normal(path, t)
        # A piece of the blow has a point at each of its ends.
        ends = math.sin(math.pi * i / steps) ** 0.45 if (t0, t1) != (0.0, 1.0) else 1.0
        w = _width(path, t) * ends
        if path.centred:
            # `inset` has no meaning for a band about the line: it narrows by
            # `scale` alone.
            half = w * scale * 0.5
            outer.append((x + nx * half, y + ny * half))
            inner.append((x - nx * half, y - ny * half))
        else:
            outer.append((x + nx * w * inset, y + ny * w * inset))
            inner.append((x + nx * w * max(inset, scale), y + ny * w * max(inset, scale)))
    return outer + inner[::-1]


def _scaled(points: Sequence[Point]) -> List[Point]:
    return [(x * SUPER, y * SUPER) for x, y in points]


def _inside_frame(x: float, y: float) -> bool:
    return 0.0 <= x <= REACH * 0.99 and 0.0 <= y <= FRAME_SIZE[1]


# ── what flies off ─────────────────────────────────────────────────────────


def _bits(path: Path_, count: int, seed: int) -> List[Tuple[float, float, float, float]]:
    """`count` bits along the blow: (t along it, way back, way out, size).
    A fixed sequence, so each frame of a row draws the same bits further on."""
    out = []
    for i in range(count):
        a = math.sin((i + 1) * 12.9898 + seed * 78.233) * 43758.5453
        b = math.sin((i + 1) * 39.3468 + seed * 11.135) * 24634.6345
        c = math.sin((i + 1) * 73.156 + seed * 52.235) * 13758.937
        fa, fb, fc = a - math.floor(a), b - math.floor(b), c - math.floor(c)
        out.append((0.35 + 0.6 * fa, 0.04 + 0.12 * fb, 0.18 + 0.5 * fc, 0.55 + 0.6 * fb))
    return out


def _bit_at(path: Path_, bit, fly: float) -> Tuple[float, float, float, float]:
    """Where a bit is after flying `fly` (0..1): back along the blow and out
    to the outside of its bow. Never ahead of the tip."""
    t, back, out, size = bit
    x, y = _point(path, t)
    nx, ny = _normal(path, t)
    x = x - REACH * back * fly
    sign = -1.0 if not path.centred else (1.0 if t * 10 % 2 < 1 else -1.0)
    x += nx * sign * HALF * out * fly
    y += ny * sign * HALF * out * fly + HALF * 0.15 * fly * fly
    return min(x, REACH * 0.97), y, size, 1.0 - fly


def _mote(draw, kind: str, x: float, y: float, r: float, fill, rim) -> None:
    """One bit of an energy blow, in its own shape."""
    s = SUPER
    if r <= 0.35:
        return
    if kind == "cell":
        for grow, f in ((1.2, rim), (0.0, fill)):
            q = r + grow
            draw.rectangle((round((x - q) * s), round((y - q) * s), round((x + q) * s), round((y + q) * s)), fill=f)
    elif kind == "star":
        for grow, f in ((1.0, rim), (0.0, fill)):
            q = r * 2.2 + grow
            p = r * 0.45 + grow * 0.5
            pts = [(x + q, y), (x + p, y + p), (x, y + q), (x - p, y + p), (x - q, y), (x - p, y - p), (x, y - q), (x + p, y - p)]
            draw.polygon(_scaled(pts), fill=f)
    elif kind == "chalk":
        # A short dash of chalk, a little rough.
        for grow, f in ((0.9, rim), (0.0, fill)):
            q = r + grow
            draw.polygon(_scaled([(x - q * 1.8, y - q * 0.5), (x + q * 1.6, y - q * 0.8), (x + q * 1.8, y + q * 0.5), (x - q * 1.5, y + q * 0.7)]), fill=f)
    else:
        for grow, f in ((1.0, rim), (0.0, fill)):
            q = r + grow
            draw.ellipse(((x - q) * s, (y - q) * s, (x + q) * s, (y + q) * s), fill=f)


def _shard(draw, x: float, y: float, r: float, turn: float, fill, rim) -> None:
    """A thrown triangle."""
    if r <= 0.4:
        return
    for grow, f in ((1.1, rim), (0.0, fill)):
        q = r + grow
        pts = [(x + q * 1.6 * math.cos(turn + k * 2.2), y + q * math.sin(turn + k * 2.2)) for k in range(3)]
        draw.polygon(_scaled(pts), fill=f)


# ── the styles ─────────────────────────────────────────────────────────────


def _spend(p: float) -> Tuple[float, float]:
    """(where the blow now starts along its line, how thick it still is) at
    progress `p`: it goes from the hand's end, and thins."""
    return 0.82 * _smooth(0.0, 0.92, p), 1.0 - 0.78 * _smooth(0.08, 1.0, p)


def _draw_crescent(draw, path: Path_, pal: Palette, p: float, fibres: bool) -> None:
    start, thin = _spend(p)
    span = (start, 1.0)
    core = 1.0 - _smooth(0.15, 0.75, p)
    draw.polygon(_scaled(_band(path, *span, thin, 0.0)), fill=_rgba(pal.edge))
    draw.polygon(_scaled(_band(path, *span, thin * 0.9, 0.06)), fill=_rgba(pal.body))
    if core > 0.04:
        draw.polygon(_scaled(_band(path, *span, thin * (0.28 + 0.3 * core), 0.1)), fill=_rgba(pal.core))
    if fibres:
        # Lines behind the edge where the blade went: they say it moved.
        for k, (off, alpha) in enumerate(((1.25, 0.75), (1.55, 0.5), (1.85, 0.3))):
            lag = 0.08 * (k + 1)
            t0 = min(0.95, start + lag)
            if t0 >= 0.95:
                continue
            band = _band(path, t0, 0.97, thin * off * 0.12 + 0.02, thin * off * 0.92)
            draw.polygon(_scaled(band), fill=_rgba(_mix(pal.body, pal.core, 0.75), alpha * (1.0 - 0.7 * p)))


def _draw_blade(draw, path: Path_, pal: Palette, p: float, mote: str) -> None:
    _draw_crescent(draw, path, pal, p, fibres=True)
    # Sparks off the edge as the blade spends.
    if p > 0.0:
        fly = _smooth(0.0, 1.0, p)
        for bit in _bits(path, 5, 3):
            x, y, size, life = _bit_at(path, bit, fly)
            if _inside_frame(x, y):
                _mote(draw, "dot", x, y, size * 1.6 * life, _rgba(pal.core), _rgba(pal.accent))


def _draw_impact(draw, path: Path_, pal: Palette, p: float, mote: str) -> None:
    start, thin = _spend(p)
    # Speed streaks along the blow: three thin bands, the middle one brightest.
    streak = Path_(path.start, path.end, path.bow, path.belly * 0.55, path.peak, path.hook, centred=True)
    for scale, colour, lag in ((1.0, pal.edge, 0.0), (0.62, pal.body, 0.06), (0.26, pal.core, 0.12)):
        t0 = min(0.96, start + lag * (0.5 + p))
        draw.polygon(_scaled(_band(streak, t0, 0.9, thin * scale, 0.0)), fill=_rgba(colour))
    for side in (-1.0, 1.0):
        # Two hair lines beside the streak, lagging behind it.
        t0 = min(0.9, start + 0.18)
        line = []
        for i in range(25):
            t = t0 + (0.82 - t0) * i / 24
            x, y = _point(path, t)
            nx, ny = _normal(path, t)
            off = side * HALF * (0.42 + 0.1 * side) * (1.0 - 0.3 * p)
            line.append((x + nx * off, y + ny * off))
        if len(line) > 1:
            draw.line(_scaled(line), fill=_rgba(pal.body, 0.8 * (1.0 - p)), width=max(1, round(1.6 * SUPER * (1.0 - 0.6 * p))))
    # The burst where the blow lands: a star of rays that opens and goes, and a
    # ring. It sits at the end of the blow, wholly behind its tip.
    bx, by = _point(path, 0.84)
    open_ = _smooth(0.0, 0.7, p)
    gone = 1.0 - _smooth(0.3, 1.0, p)
    if gone > 0.02:
        # Full on the first frame, then it shrinks as it goes.
        rays = 8
        outer_r = HALF * (0.8 - 0.3 * open_)
        inner_r = HALF * (0.26 - 0.08 * open_)
        outer_r = min(outer_r, REACH * 0.985 - bx + inner_r)
        for scale, colour in ((1.0, pal.edge), (0.78, pal.body), (0.5, pal.core)):
            pts = []
            for k in range(rays * 2):
                a = math.pi * k / rays + 0.2
                r = (outer_r if k % 2 == 0 else inner_r) * scale * (0.6 + 0.4 * gone)
                pts.append((bx + r * math.cos(a), by + r * math.sin(a)))
            draw.polygon(_scaled(pts), fill=_rgba(colour, min(1.0, gone * 1.3)))
        ring = HALF * (0.3 + 0.55 * open_)
        if p > 0.0:
            w = max(1, round(SUPER * 2.2 * gone))
            draw.ellipse(((bx - ring) * SUPER, (by - ring) * SUPER, (bx + min(ring, REACH * 0.985 - bx)) * SUPER, (by + ring) * SUPER), outline=_rgba(pal.core, gone), width=w)
    if p > 0.0:
        fly = _smooth(0.0, 1.0, p)
        for bit in _bits(path, 6, 7):
            x, y, size, life = _bit_at(path, bit, fly)
            if _inside_frame(x, y):
                _mote(draw, "dot", x, y, size * 1.4 * life, _rgba(pal.core), _rgba(pal.accent))


def _draw_ink(draw, path: Path_, pal: Palette, p: float, mote: str) -> None:
    # Ink is dark: the body of the stroke is the ink, and the light colour is
    # the paper showing in its middle.
    inked = Palette(core=pal.core, body=_mix(pal.edge, pal.body, 0.3), edge=pal.edge, accent=pal.accent)
    _draw_crescent(draw, path, inked, p, fibres=False)
    if p > 0.0:
        fly = _smooth(0.0, 1.0, p)
        for bit in _bits(path, 5, 11):
            x, y, size, life = _bit_at(path, bit, fly)
            if not _inside_frame(x, y):
                continue
            r = size * 2.4 * (1.0 - 0.6 * p)
            # A drop: a round head with a point behind it.
            for grow, fill in ((1.2, _rgba(pal.core)), (0.0, _rgba(pal.edge))):
                q = r + grow
                draw.polygon(_scaled([(x, y - q), (x - q * 2.6, y), (x, y + q)]), fill=fill)
                draw.ellipse(((x - q) * SUPER, (y - q) * SUPER, (x + q) * SUPER, (y + q) * SUPER), fill=fill)


def _draw_shard(draw, path: Path_, pal: Palette, p: float, mote: str) -> None:
    start, thin = _spend(p)
    # A crescent of a few hard facets: sample the band coarsely, so its edges
    # are straight, and colour alternate facets.
    steps = 7
    for layer, (scale, inset, colour) in enumerate(((thin, 0.0, pal.edge), (thin * 0.86, 0.07, pal.body), (thin * 0.42, 0.12, pal.core))):
        if layer == 2 and p > 0.6:
            continue
        band = _band(path, start, 1.0, scale, inset, steps=steps)
        draw.polygon(_scaled(band), fill=_rgba(colour))
    # Facet lines across the crescent.
    for i in range(1, steps):
        t = start + (1.0 - start) * i / steps
        x, y = _point(path, t)
        nx, ny = _normal(path, t)
        w = _width(path, t) * thin
        draw.line(_scaled([(x, y), (x + nx * w * 0.9, y + ny * w * 0.9)]), fill=_rgba(pal.edge, 0.7), width=max(1, round(SUPER * 1.2)))
    if p > 0.0:
        fly = _smooth(0.0, 1.0, p)
        for k, bit in enumerate(_bits(path, 6, 5)):
            x, y, size, life = _bit_at(path, bit, fly)
            if _inside_frame(x, y):
                _shard(draw, x, y, size * 3.0 * life, k * 1.7 + fly * 2.0, _rgba(pal.body), _rgba(pal.edge))


def _draw_energy(draw, path: Path_, pal: Palette, p: float, mote: str) -> None:
    start, thin = _spend(p)
    # A soft glow wider than the ribbon, then the ribbon, then its hot line.
    draw.polygon(_scaled(_band(path, start, 1.0, thin * 0.85, 0.0)), fill=_rgba(pal.edge))
    draw.polygon(_scaled(_band(path, start, 1.0, thin * 0.72, 0.08)), fill=_rgba(pal.body))
    core = 1.0 - _smooth(0.2, 0.8, p)
    if core > 0.04:
        draw.polygon(_scaled(_band(path, start, 1.0, thin * 0.3 * (0.5 + core), 0.14)), fill=_rgba(pal.core))
    # Motes: on the ribbon at first, then shed back and out.
    fly = _smooth(0.0, 1.0, p)
    for bit in _bits(path, 9, 13):
        x, y, size, life = _bit_at(path, bit, fly)
        if _inside_frame(x, y):
            _mote(draw, mote, x, y, size * 1.7 * (0.5 + 0.5 * life), _rgba(pal.core), _rgba(pal.edge))


STYLES: Dict[str, Callable] = {
    "blade": _draw_blade,
    "impact": _draw_impact,
    "ink": _draw_ink,
    "shard": _draw_shard,
    "energy": _draw_energy,
}


def draw_frame(style: str, palette: Palette, mote: str, animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    """One frame of one row, at `FRAME_SIZE`."""
    p = frame_idx / max(1, frame_count - 1)
    canvas = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    if p < 1.0:
        STYLES[style](blending_draw(canvas), PATHS[animation], palette, p, mote)
    return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _frame_meta(animation: str, frame_idx: int, frame_count: int) -> dict:
    return {
        "anchors": {
            "origin": {"x": 0.0, "y": AXIS_Y},
            "tip": {"x": REACH, "y": AXIS_Y},
        },
        "effect": {"kind": animation, "progress": round(frame_idx / max(1, frame_count - 1), 4)},
    }


def sheet_files(target: str) -> Tuple[str, ...]:
    return (
        f"{target}_spritesheet.png",
        f"{target}_spritesheet.yaml",
        f"{target}_spritesheet.ron",
        f"{target}_actor.ron",
    )


def actor_metadata(target: str, display_name: str) -> dict:
    return {
        "actor": {"character_id": f"fx_{target}", "display_name": display_name},
        "body": {
            "body_plan": "Effect",
            "body_kind": "Slash",
            "locomotion_hint": "Stationary",
            "traits": ["fx", "slash", "melee", "overlay"],
        },
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {
            "default": {"animation": "side", "events": []},
            "action.melee.side": {"animation": "side", "events": []},
            "action.melee.up": {"animation": "up", "events": []},
            "action.melee.down_air": {"animation": "down", "events": []},
        },
        "sockets": {
            "origin": {"source": f"{target}.geometry", "point": {"x": 0.0, "y": AXIS_Y}},
        },
        "tags": ["fx", "slash", "melee", "overlay"],
    }


def renderer(target: str, style: str, palette: Palette, display_name: str, mote: str = "dot"):
    """The `render(out_dir, **opts)` of one fighter's strike sheet."""
    if style not in STYLES:
        raise ValueError(f"unknown strike style {style!r}")
    metadata = actor_metadata(target, display_name)

    def render(out_dir: str | Path, **opts) -> List[Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        outputs = build_sheet(
            target=target,
            rows=ROWS,
            render_fn=lambda animation, i, n: draw_frame(style, palette, mote, animation, i, n),
            out_dir=out_dir,
            frame_size=opts.get("frame_size") or FRAME_SIZE,
            frame_meta_fn=_frame_meta,
            # The game samples this sheet as a grid of whole frames.
            auto_crop=False,
            actor_metadata=metadata,
        )
        return [
            outputs["canonical"],
            outputs["canonical_transparent"],
            outputs["spritesheet"],
            outputs["yaml"],
            outputs["ron"],
            outputs["actor"],
            outputs["preview"],
        ]

    return render, metadata
