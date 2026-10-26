"""What the cast wears, in the round, as data: garments, hats, cloaks, manes,
props, circlets and antlers for ``_person_round``.

A garment is a loft (its shape, ``Ring``s) and the features painted on it:
an opening onto what is under it, a neckline, lapels, a belt and its
buckle, buttons, a tie, a watch chain, pockets, seams, folds, a hem cut in
points. Each feature says where on the garment it is: ``u`` is the turn round
it in degrees (0 in front, 90 to the person's left, 180 behind), ``v`` its
height in body space. A width across the front (a tie, a stripe) is in
pixels, round a front of ``Garment.radius``.

A character's coat is a choice of features and numbers, not a function of
its own, so a new character is a new choice: the generator that makes new
people of the cast picks from these.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

import numpy as np

from . import _person_round as O
from ._ai_era_kit import RGBA, Kit, WHITE

Vec = Tuple[float, float, float]


# ---- Features ----------------------------------------------------------------


@dataclass(frozen=True)
class Opening:
    """The garment hangs open in front, ``half`` degrees each side, from
    ``top`` down to ``bottom``, onto ``colour`` (what is under it)."""

    half: float
    colour: RGBA
    top: float = -1e9
    bottom: float = 1e9

    def apply(self, g, out, u, v, x, lit):
        O.put(out, (np.abs(u) < self.half) & (v > self.top) & (v < self.bottom), self.colour)


@dataclass(frozen=True)
class Behind:
    """Behind, beyond ``half`` degrees each side of the front, from ``top``
    down to ``bottom``, the garment is ``colour``: what a thing worn only in
    front (an apron) does not cover."""

    half: float
    colour: RGBA
    top: float = -1e9
    bottom: float = 1e9

    def apply(self, g, out, u, v, x, lit):
        O.put(out, (np.abs(u) >= self.half) & (v > self.top) & (v < self.bottom), self.colour)


@dataclass(frozen=True)
class Stripes:
    """Bands that slant (``slant`` pixels across for each pixel down), one
    ``period`` pixels wide each, in turn of ``colours``, from ``top`` to
    ``bottom``, within ``half`` degrees of the front (the stripes of a
    barber's pole at a hem)."""

    top: float
    bottom: float
    period: float
    colours: Sequence[RGBA]
    slant: float = 0.5
    half: float = 180.0

    def apply(self, g, out, u, v, x, lit):
        band = np.floor((x + self.slant * v) / self.period).astype(int) % len(self.colours)
        on = (v > self.top) & (v < self.bottom) & (np.abs(u) < self.half)
        for k, colour in enumerate(self.colours):
            O.put(out, on & (band == k), colour)


@dataclass(frozen=True)
class Neckline:
    """A V (or a narrowing opening) at the neck: ``half`` degrees each side
    at ``top``, to a point at ``bottom``."""

    top: float
    bottom: float
    half: float
    colour: RGBA

    def apply(self, g, out, u, v, x, lit):
        O.put(out, (v < self.bottom) & (np.abs(u) < self.half * (self.bottom - v) / (self.bottom - self.top)), self.colour)


@dataclass(frozen=True)
class Lapels:
    """Lapels on an open front whose edge is at ``edge`` degrees: ``spread``
    degrees wide at ``top``, to nothing at ``bottom``; and the line of the
    edge below them."""

    edge: float
    top: float
    bottom: float
    spread: float
    colour: RGBA
    line: Optional[RGBA] = None

    def apply(self, g, out, u, v, x, lit):
        a = np.abs(u)
        lapel = (v < self.bottom) & (v > self.top - 1.0) & (a >= self.edge - self.spread * (v - self.bottom) / (self.top - self.bottom)) & (a < self.edge + 2.0)
        O.put(out, lapel, self.colour)
        if self.line is not None:
            O.put(out, (np.abs(np.abs(x) - O.arc(self.edge, g.radius)) < 0.35) & (v > self.bottom), self.line)


@dataclass(frozen=True)
class Band:
    """A band all round: a belt, a sash, a hat band."""

    top: float
    bottom: float
    colour: RGBA

    def apply(self, g, out, u, v, x, lit):
        O.put(out, (v > self.top) & (v < self.bottom), self.colour)


@dataclass(frozen=True)
class Dot:
    """A disc at ``(u, v)``, ``r`` across (a buckle, a button), with a ring."""

    u: float
    v: float
    r: float
    colour: RGBA
    ring: Optional[RGBA] = None

    def apply(self, g, out, u, v, x, lit):
        d2 = (x - O.arc(self.u, g.radius)) ** 2 + (v - self.v) ** 2
        O.put(out, d2 < self.r ** 2, self.colour)
        if self.ring is not None:
            O.put(out, (d2 < (self.r * 0.55) ** 2) & (d2 > (self.r * 0.35) ** 2), self.ring)


@dataclass(frozen=True)
class Buttons:
    """``count`` buttons in a line at ``u``, from ``top`` to ``bottom``."""

    u: float
    top: float
    bottom: float
    count: int
    r: float
    colour: RGBA

    def apply(self, g, out, u, v, x, lit):
        for k in range(self.count):
            y = self.top + (self.bottom - self.top) * k / max(1, self.count - 1)
            Dot(self.u, y, self.r, self.colour).apply(g, out, u, v, x, lit)


@dataclass(frozen=True)
class Strip:
    """A strip down the garment at ``u``: ``half`` pixels each side at
    ``top``, ``half + flare`` at ``bottom`` (a tie, the tail of a belt, a
    placket)."""

    u: float
    top: float
    bottom: float
    half: float
    colour: RGBA
    flare: float = 0.0

    def apply(self, g, out, u, v, x, lit):
        t = np.clip((v - self.top) / max(1e-6, self.bottom - self.top), 0.0, 1.0)
        O.put(out, (v > self.top) & (v < self.bottom) & (np.abs(x - O.arc(self.u, g.radius)) < self.half + self.flare * t), self.colour)


@dataclass(frozen=True)
class Swag:
    """Something that hangs in a curve across the front from ``left`` to
    ``right`` (degrees): at ``v`` in the middle, ``rise`` higher at each end
    (a watch chain). ``dark`` is under it, twice as wide."""

    left: float
    right: float
    v: float
    rise: Tuple[float, float]
    colour: RGBA
    dark: Optional[RGBA] = None
    width: float = 0.35

    def apply(self, g, out, u, v, x, lit):
        lo, hi = O.arc(self.left, g.radius), O.arc(self.right, g.radius)
        reach = np.where(x < 0.0, abs(lo), abs(hi))
        sag = self.v - np.where(x < 0.0, self.rise[0], self.rise[1]) * (x / reach) ** 2
        on = (x > lo) & (x < hi)
        if self.dark is not None:
            O.put(out, on & (np.abs(v - sag) < 2.0 * self.width), self.dark)
        O.put(out, on & (np.abs(v - sag) < self.width), self.colour)


@dataclass(frozen=True)
class Across:
    """A line across from ``u0`` to ``u1`` degrees at ``v`` (the top of a
    pocket, a seam). ``both``: on the two sides, mirrored."""

    u0: float
    u1: float
    v: float
    colour: RGBA
    both: bool = False
    width: float = 0.35

    def apply(self, g, out, u, v, x, lit):
        uu = np.abs(u) if self.both else u
        O.put(out, (uu > self.u0) & (uu < self.u1) & (np.abs(v - self.v) < self.width), self.colour)


@dataclass(frozen=True)
class Down:
    """A line down at ``u`` from ``top`` to ``bottom`` (a seam); it goes out
    by ``spread`` degrees by the bottom (a fold)."""

    u: float
    top: float
    bottom: float
    colour: RGBA
    spread: float = 0.0
    width: float = 0.35

    def apply(self, g, out, u, v, x, lit):
        t = np.clip((v - self.top) / max(1e-6, self.bottom - self.top), 0.0, 1.0)
        at = self.u + np.sign(self.u) * self.spread * t if self.u not in (0.0, 180.0, -180.0) else self.u
        d = (u - at + 180.0) % 360.0 - 180.0
        O.put(out, (v > self.top) & (v < self.bottom) & (np.abs(O.arc(d, g.radius)) < self.width), self.colour)


@dataclass(frozen=True)
class Patch:
    """A patch from ``u0`` to ``u1`` degrees, ``top`` to ``bottom`` (a stick
    of chalk in a pocket, a pen)."""

    u0: float
    u1: float
    top: float
    bottom: float
    colour: RGBA

    def apply(self, g, out, u, v, x, lit):
        O.put(out, (u > self.u0) & (u < self.u1) & (v > self.top) & (v < self.bottom), self.colour)


@dataclass(frozen=True)
class Glow:
    """An oval of light (or shade) at ``(u, v)``, ``ru`` pixels across and
    ``rv`` high; ``both``: and its mirror (the light on a bust)."""

    u: float
    v: float
    ru: float
    rv: float
    colour: RGBA
    both: bool = False

    def apply(self, g, out, u, v, x, lit):
        for s in ((1.0, -1.0) if self.both else (1.0,)):
            O.put(out, ((x - s * O.arc(self.u, g.radius)) / self.ru) ** 2 + ((v - self.v) / self.rv) ** 2 < 1.0, self.colour)


@dataclass(frozen=True)
class Path:
    """A line through ``points`` (``(u, v)``), ``width`` pixels each side:
    stitching, a constellation of dots joined."""

    points: Sequence[Tuple[float, float]]
    colour: RGBA
    width: float = 0.3

    def apply(self, g, out, u, v, x, lit):
        pts = [(O.arc(pu, g.radius), pv) for pu, pv in self.points]
        near = np.full(len(u), np.inf)
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            dx, dy = bx - ax, by - ay
            t = np.clip(((x - ax) * dx + (v - ay) * dy) / max(1e-9, dx * dx + dy * dy), 0.0, 1.0)
            near = np.minimum(near, np.hypot(x - (ax + t * dx), v - (ay + t * dy)))
        O.put(out, near < self.width, self.colour)


@dataclass(frozen=True)
class PointedHem:
    """A hem cut in points (leaves): from ``top`` to ``bottom`` a row of
    points ``period`` pixels apart, in ``colour``; under them, ``under``."""

    top: float
    bottom: float
    period: float
    colour: RGBA
    under: Optional[RGBA] = None

    def apply(self, g, out, u, v, x, lit):
        f = (x / self.period) % 1.0
        depth = (self.bottom - self.top) * (1.0 - np.abs(2.0 * f - 1.0))
        O.put(out, (v > self.top) & (v - self.top < depth), self.colour)
        if self.under is not None:
            O.put(out, v > self.bottom, self.under)


@dataclass(frozen=True)
class Shade:
    """Where the key light does not reach (``lit`` under ``at``), the
    garment's dark colour: the far side of a body in its own shade."""

    at: float = -0.45

    def apply(self, g, out, u, v, x, lit):
        O.put(out, lit < self.at, g.dark)


@dataclass(frozen=True)
class Garment:
    """A colour, its dark, and the features painted on it, in order."""

    colour: RGBA
    dark: RGBA
    features: Sequence[object] = ()
    #: How far round the front is from the middle, for widths in pixels.
    radius: float = 9.0

    def paint(self, u, v, lit, far):
        out = O.fill(self.colour, len(u))
        x = O.arc(u, self.radius)
        for f in self.features:
            f.apply(self, out, u, v, x, lit)
        return out


# ---- Pieces --------------------------------------------------------------------


@dataclass(frozen=True)
class Trunk:
    """The trunk and what is worn on it: a garment on a loft from the neck to
    the hem, the round of each shoulder, and a collar."""

    rings: Sequence[O.Ring]
    garment: Garment
    #: ``(l, y, z)`` of the right shoulder's middle and its radii (the left is
    #: its mirror).
    shoulder: Optional[Tuple[Vec, Vec]] = None
    collar: Optional[Tuple[Sequence[O.Ring], Garment]] = None

    def part(self, anchor: Vec = (0.0, -20.0, 0.4)) -> O.Part:
        g = self.garment
        surfaces = [O.loft(self.rings, g.paint, cols=64)]
        if self.shoulder is not None:
            (sl, sy, sz), r = self.shoulder
            for s in (-1.0, 1.0):
                surfaces.append(O.ellipsoid((s * abs(sl), sy, sz), r, O.flat(g.colour, shade=g.dark, at=-0.45)))
        if self.collar is not None:
            surfaces.append(O.loft(self.collar[0], self.collar[1].paint))
        return O.Part("trunk", surfaces, base=g.colour, shade_colour=g.dark, anchor=anchor)


@dataclass(frozen=True)
class Hat:
    """A hat: a crown (a loft) and a brim (a loft from its inner edge out,
    over, and back under; its rings' ``v`` says top 0-1, underside 2-3), on
    the head's middle."""

    crown: Sequence[O.Ring]
    brim: Optional[Sequence[O.Ring]]
    garment: Garment
    under: RGBA
    lines: Sequence[O.Line] = ()

    def piece(self, K: Kit, J, head: Vec) -> O.Part:
        return self.part(head)

    def part(self, head: Vec) -> O.Part:
        g = self.garment

        def brim(u, v, lit, far):
            return O.put(O.fill(g.colour, len(u)), v > 1.5, self.under)

        surfaces = [O.loft(self.crown, g.paint).moved(head)]
        if self.brim is not None:
            surfaces.append(O.loft(self.brim, brim).moved(head))
        return O.Part("hat", surfaces, [ln.moved(head) for ln in self.lines], base=g.colour, outline=1.2, shade=0.35, shade_colour=self.under,
                      anchor=(head[0], head[1] - 10.0, head[2]))


@dataclass(frozen=True)
class Cloak:
    """A cloak from the shoulders: a loft round the back only (``turns``,
    degrees, e.g. 110 to 250), so it never hides the front."""

    rings: Sequence[O.Ring]
    garment: Garment
    turns: Tuple[float, float] = (110.0, 250.0)

    def piece(self, K: Kit, J, head: Vec) -> O.Part:
        return self.part()

    def part(self) -> O.Part:
        g = self.garment
        surface = O.loft(self.rings, g.paint, cols=48, turns=self.turns)
        mid = self.rings[len(self.rings) // 2]
        return O.Part("cloak", [surface], base=g.colour, rim=0.2, shade=0.4, shade_colour=g.dark, anchor=(mid.l, mid.y, mid.z - mid.rz))


def mane(K: Kit, points: Sequence[Vec], width: float, colour: RGBA, dark: RGBA, *, back_width: Optional[float] = None, taper: float = 0.45,
         lead: float = 0.0) -> O.Drawn:
    """Hair (or a tail, a scarf end) hanging through 3D ``points``, drawn as
    the cast draws it (``_person_rig.ribbon``). ``back_width``: as wide as it
    is seen from behind (long hair is broad behind, a lock from the side)."""
    from ._person_rig import ribbon

    def draw(view: O.View, far: bool, at) -> object:
        pts = [at(p) for p in points]
        root = (float(round(pts[0][0])), float(round(pts[0][1])))
        toward = -math.cos(math.radians(O.facing(view)))
        w = width if back_width is None else width + (back_width - width) * max(0.0, toward)
        piece = ribbon(K, ("mane", round(w, 1)), [[(x - root[0], y - root[1]) for x, y in pts]], w, colour, dark, taper=taper)
        img = K.new_frame()
        K.place(img, piece, root, "mane", 0.0)
        return img

    middle = points[len(points) // 2]
    return O.Drawn("mane", tuple(middle), draw, lead=lead)


def prop(K: Kit, name: str, foot: Vec, head: Vec, make: Callable[[int], object], *, lead: float = 0.0, when=None) -> O.Drawn:
    """A thing drawn along +x from its foot (``make(length)``: a staff, a
    sword, a pen) between two 3D points, its length what the view makes of
    it."""

    def draw(view: O.View, far: bool, at) -> object:
        a, b = at(foot), at(head)
        img = K.new_frame()
        K.place(img, make(int(round(math.dist(a, b)))), a, name, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
        return img

    mid = tuple((np.asarray(foot) + np.asarray(head)) / 2.0)
    return O.Drawn(name, mid, draw, lead=lead, when=when)


def strokes(K: Kit, name: str, lines: Sequence[Sequence[Vec]], width: float, colour: RGBA, dark: RGBA, anchor: Vec, *, lead: float = 0.0,
            when=None) -> O.Drawn:
    """Branches drawn as strokes through 3D points, lit and outlined as one
    piece (antlers, horns, a crown of twigs)."""

    def draw(view: O.View, far: bool, at) -> object:
        pts = [[at(p) for p in ln] for ln in lines]
        root = at(anchor)
        rel = tuple(tuple((round(x - root[0], 1), round(y - root[1], 1)) for x, y in ln) for ln in pts)

        def shape(d) -> None:
            for ln in rel:
                K.stroke(d, [K.at(x, y) for x, y in ln], WHITE, width)

        piece = K.solid((name, rel, width, colour), shape, colour, None, outline=1.1, rim=0.3, shade=0.35, shade_colour=dark)
        img = K.new_frame()
        K.place(img, piece, root, name, 0.0)
        return img

    return O.Drawn(name, tuple(anchor), draw, lead=lead, when=when)


@dataclass(frozen=True)
class Worn:
    """A thing worn round the body or the head, as a loft with its own
    outline: a scarf wound round the neck, a circlet. ``on``: ``"body"``
    (rings in body space) or ``"head"`` (from the head's middle).
    ``lumps``: ellipsoids of it (the knot of a scarf)."""

    name: str
    rings: Sequence[O.Ring]
    garment: Garment
    on: str = "body"
    lumps: Sequence[Tuple[Vec, Vec]] = ()
    #: How much nearer it counts as being (``Part.lead``).
    lead: float = 0.0

    def piece(self, K: Kit, J, head: Vec) -> O.Part:
        g = self.garment
        surfaces = [O.loft(self.rings, g.paint)] + [O.ellipsoid(c, r, O.flat(g.colour, shade=g.dark, at=-0.45)) for c, r in self.lumps]
        at = np.asarray(head if self.on == "head" else (0.0, 0.0, 0.0))
        mid = self.rings[len(self.rings) // 2]
        return O.Part(self.name, [s.moved(tuple(at)) for s in surfaces], base=g.colour, outline=1.2, rim=0.4, shade=0.45, shade_colour=g.dark,
                      anchor=tuple(at + (mid.l, mid.y, mid.z)), lead=self.lead)


@dataclass(frozen=True)
class Chains:
    """Things that hang through 3D ``chains`` of points (body space), drawn
    by the character's own maker: ``make(chains)`` gets each chain as frame
    points from a whole frame pixel and returns the piece placed there (the
    tails of a scarf). It is as near as the middle of the first chain."""

    name: str
    chains: Sequence[Sequence[Vec]]
    make: Callable
    lead: float = 0.0

    def piece(self, K: Kit, J, head: Vec) -> O.Drawn:
        chains = self.chains

        def draw(view: O.View, far: bool, at) -> object:
            pts = [[at(p) for p in ch] for ch in chains]
            root = (float(round(pts[0][0][0])), float(round(pts[0][0][1])))
            piece = self.make(tuple(tuple((x - root[0], y - root[1]) for x, y in ch) for ch in pts))
            img = K.new_frame()
            K.place(img, piece, root, self.name, 0.0)
            return img

        first = chains[0]
        return O.Drawn(self.name, tuple(first[len(first) // 2]), draw, lead=self.lead)


@dataclass(frozen=True)
class Mane:
    """Hair down the back (or a tail, the end of a scarf): ``points`` from
    the head's middle, ``width`` from the side, ``back_width`` from behind
    (``mane``)."""

    points: Sequence[Vec]
    width: float
    colour: RGBA
    dark: RGBA
    back_width: Optional[float] = None
    lead: float = 1.0

    def piece(self, K: Kit, J, head: Vec) -> O.Drawn:
        return mane(K, [tuple(np.asarray(head) + p) for p in self.points], self.width, self.colour, self.dark, back_width=self.back_width, lead=self.lead)


@dataclass(frozen=True)
class Prop:
    """A thing carried on the body (a staff across the back): ``make(length)``
    drawn from ``foot`` to ``head``, body-space points (``prop``)."""

    name: str
    foot: Vec
    head: Vec
    make: Callable[[int], object]
    lead: float = 0.0

    def piece(self, K: Kit, J, head: Vec) -> O.Drawn:
        return prop(K, self.name, self.foot, self.head, self.make, lead=self.lead)


@dataclass(frozen=True)
class Antlers:
    """Branches on the head (antlers, horns): ``lines`` of points from the
    head's middle, drawn as strokes (``strokes``)."""

    lines: Sequence[Sequence[Vec]]
    width: float
    colour: RGBA
    dark: RGBA
    name: str = "antlers"
    lead: float = 2.0

    def piece(self, K: Kit, J, head: Vec) -> O.Drawn:
        h = np.asarray(head)
        return strokes(K, self.name, [[tuple(h + p) for p in ln] for ln in self.lines], self.width, self.colour, self.dark, tuple(h + (0.0, -12.0, 2.0)),
                       lead=self.lead)


__all__ = ["Behind", "Stripes", "Chains", "Path", "Worn", "Antlers", "Mane", "Prop", "Across", "Band", "Buttons", "Cloak", "Dot", "Down", "Garment", "Glow", "Hat", "Lapels", "Neckline", "Opening", "Patch", "PointedHem",
           "Shade", "Strip", "Swag", "Trunk", "mane", "prop", "strokes"]
