"""The band's instruments, as parts a generated body carries, and the clips
that play them.

Jon, 2026-11-13: in the final battle the bossofthegame's agents play in a
band with him and Full Stack, so each agent can pose with a rock band's
instruments. The agents are instrumentalists only: the microphone is the
Boss's. Each instrument is its own part, hidden until a clip shows it by its
channel, so any agent can play any of them:

* ``prop.guitar``: an electric guitar on a strap, its six strings straight
  and parallel from the bridge to the nut;
* ``prop.bass``: a bass guitar on a strap, longer, four strings;
* ``prop.keytar``: a keytar on a strap, the keys under the right hand, the
  neck under the left;
* ``prop.sticks``: a drumstick in each fist (the kit itself is a prop of the
  stage, not of the body).

A strapped instrument rides the torso and is drawn in 3D from the figure in
every view; the clips (``band_clips``) put the hands where its strings,
frets and keys are.

Units are the figure's: centimetres, ``x`` to the body's left, ``y`` down,
``z`` forward.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Dict, List, Sequence, Tuple

from ...chargen.draw import ITEM_REST_ANGLE, grip_point
from ...chargen.drawkit import Ctx, Part
from ...chargen.geometry import add3, norm3, scale3, sub3
from ...chargen.motion import Clip, Kit
from ...chargen.pose3d import Hand, Pose
from ...chargen.svgout import FINE, light, mix, shade

Point = Tuple[float, float]
Vec3 = Tuple[float, float, float]

#: The channels of the band's instruments (all hidden by default).
CHANNELS = ("prop.guitar", "prop.bass", "prop.keytar", "prop.sticks")
#: The rows that play them.
ROWS = ("band_guitar", "band_bass", "band_keytar", "band_drums")


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


@dataclass(frozen=True)
class Strap:
    """Where a strapped instrument hangs on a figure: the middle of its body
    ``c``, the direction its neck runs ``u``, the direction across it ``v``
    and its face's normal ``n``."""

    c: Vec3
    u: Vec3
    v: Vec3
    n: Vec3

    def at(self, a: float, b: float, d: float = 0.0) -> Vec3:
        return add3(add3(self.c, scale3(self.u, a)), add3(scale3(self.v, b), scale3(self.n, d)))


def strap(fig, *, rise: float, drop: float = 0.0) -> Strap:
    """The strap of an instrument whose neck rises ``rise`` degrees toward
    the body's left, its body ``drop`` cm below the belt."""
    t = fig.torso.section(fig.y_belt)
    c = (-4.0 * fig.k, fig.y_belt + drop * fig.k, t.rzf + 7.0 * fig.k)
    r = math.radians(rise)
    u = norm3((math.cos(r), -math.sin(r), 0.12))
    # The face is turned a little toward the body's right, so it shows in a
    # side view too.
    n0 = norm3((-0.3, 0.0, 1.0))
    v = norm3(_cross(n0, u))
    n = norm3(_cross(u, v))
    return Strap(c, u, v, n)


# ---- drawing ---------------------------------------------------------------------------------------


def _shape(ctx: Ctx, s: Strap, pts: Sequence[Point], k: float, d: float = 0.0) -> List[Point]:
    return [ctx.p(s.at(a * k, b * k, d * k)) for a, b in pts]


def _ellipse(a: float, b: float, ra: float, rb: float, n: int = 14) -> List[Point]:
    return [(a + ra * math.cos(t), b + rb * math.sin(t)) for t in (i * math.tau / n for i in range(n))]


#: An electric guitar's body, double cutaway, in cm along its neck (a) and
#: across it (b); the neck joins at a = 14.
GUITAR_BODY = [(-21.0, 0.0), (-20.0, 9.0), (-15.0, 15.5), (-7.0, 16.0), (0.0, 12.0), (6.0, 13.0), (12.0, 16.5), (16.0, 14.5), (12.0, 8.0),
               (11.0, 3.0), (14.0, 2.4), (14.0, -2.4), (11.0, -3.0), (12.0, -9.0), (17.0, -12.5), (13.0, -15.5), (5.0, -12.0),
               (-2.0, -14.0), (-12.0, -16.0), (-19.0, -11.0)]
#: A bass's body: bigger, its horns longer.
BASS_BODY = [(-25.0, 0.0), (-24.0, 11.0), (-18.0, 18.0), (-8.0, 17.5), (0.0, 13.0), (8.0, 14.0), (16.0, 18.5), (21.0, 15.0), (15.0, 8.0),
             (14.0, 3.0), (17.0, 2.6), (17.0, -2.6), (14.0, -3.0), (15.0, -10.0), (22.0, -15.0), (17.0, -18.0), (6.0, -13.5),
             (-3.0, -16.0), (-15.0, -18.0), (-23.0, -12.0)]


def _strung(ctx: Ctx, pt, s: Strap, k: float, *, body: Sequence[Point], body_color: str, neck_to: float, head_len: float,
            strings: int, scale_from: float, guard: str, neck_color: str = "#c99a5b", head_color: str = "#2a2230") -> None:
    """A body, a neck, a headstock and its strings, in paint order: the back
    edge first (its thickness), then the face."""
    edge = shade(body_color, 0.45)
    # The thickness: the outline pushed back along the normal.
    pt.region([_shape(ctx, s, body, k, -4.0)], edge)
    pt.region([_shape(ctx, s, body, k)], body_color)
    # A pickguard and the pickups.
    pt.flat([_shape(ctx, s, [(-14.0, 7.0), (-4.0, 11.0), (8.0, 9.0), (12.0, 4.0), (12.0, -4.0), (2.0, -6.0), (-12.0, -6.0)], k)], guard)
    for a in (-10.0, -2.0, 6.0) if strings == 6 else (-6.0, 4.0):
        pt.region([_shape(ctx, s, [(a - 1.2, 3.6), (a + 1.2, 3.6), (a + 1.2, -3.6), (a - 1.2, -3.6)], k)], "#2c2a30", outline=FINE * 0.6)
    # Knobs.
    for a, b in ((-16.0, -8.0), (-12.0, -11.0), (-8.0, -12.5)):
        pt.region([_shape(ctx, s, _ellipse(a, b, 1.3, 1.3, 10), k)], "#e8e2d4", outline=FINE * 0.6)
    # The neck, the frets, the headstock.
    w = 2.3 if strings == 6 else 2.6
    pt.region([_shape(ctx, s, [(12.0, w), (neck_to, w * 0.88), (neck_to, -w * 0.88), (12.0, -w)], k)], neck_color, outline=FINE * 0.8)
    fret = 16.0
    step = (neck_to - 16.0) / 13.0
    while fret < neck_to - 1.0:
        pt.line(_shape(ctx, s, [(fret, w * 0.85), (fret, -w * 0.85)], k), "#e6e0d0", FINE * 0.6, smooth=False)
        fret += step * (1.0 - 0.025 * (fret - 16.0) / step)
    head = [(neck_to, w * 0.9), (neck_to + head_len, w * 1.6), (neck_to + head_len + 1.5, 0.0), (neck_to + head_len, -w * 1.9),
            (neck_to, -w * 0.9)]
    pt.region([_shape(ctx, s, head, k)], head_color, outline=FINE * 0.8)
    for i in range(strings // 2 if strings == 6 else strings):
        a = neck_to + 2.5 + i * (head_len - 3.0) / max(1, (strings // 2 if strings == 6 else strings) - 1)
        for b in ((1.9 * w, -1.9 * w) if strings == 6 else (-1.9 * w,)):
            pt.flat([_shape(ctx, s, _ellipse(a, b * 0.55, 0.6, 0.6, 8), k)], "#d8d4cc")
    # The bridge, and the strings straight and parallel from it to the nut.
    pt.region([_shape(ctx, s, [(scale_from - 1.4, w * 1.2), (scale_from + 1.4, w * 1.2), (scale_from + 1.4, -w * 1.2),
                                (scale_from - 1.4, -w * 1.2)], k)], "#b9bcc4", outline=FINE * 0.6)
    for i in range(strings):
        b = (i - (strings - 1) / 2.0) * (2.0 * w * 0.78 / max(1, strings - 1))
        pt.line(_shape(ctx, s, [(scale_from, b), (neck_to, b * 0.88)], k), "#f2f0ea", FINE * (0.45 if strings == 6 else 0.6), smooth=False)


def guitar_parts(ctx: Ctx, color: str = "#c8323c") -> List[Part]:
    """The electric guitar: a cherry double-cutaway body with a cream guard."""
    fig = ctx.fig
    s = strap(fig, rise=28.0)
    pt = ctx.new()
    _strung(ctx, pt, s, fig.k, body=GUITAR_BODY, body_color=color, neck_to=62.0, head_len=16.0, strings=6, scale_from=-14.0,
            guard="#f1ead8")
    _strap_line(ctx, pt, fig, s)
    return [Part("band_guitar", "torso", _z(ctx), pt.els, "Electric Guitar (on its strap)", opacity="prop.guitar", opacity_default=0)]


def bass_parts(ctx: Ctx, color: str = "#2f5d8a") -> List[Part]:
    """The bass: a long-necked blue body with a black guard, four strings."""
    fig = ctx.fig
    s = strap(fig, rise=22.0, drop=3.0)
    pt = ctx.new()
    _strung(ctx, pt, s, fig.k, body=BASS_BODY, body_color=color, neck_to=78.0, head_len=18.0, strings=4, scale_from=-17.0,
            guard="#1f1c22")
    _strap_line(ctx, pt, fig, s)
    return [Part("band_bass", "torso", _z(ctx), pt.els, "Bass Guitar (on its strap)", opacity="prop.bass", opacity_default=0)]


def keytar_parts(ctx: Ctx, color: str = "#f2f2f4") -> List[Part]:
    """The keytar: a white slab with two octaves of keys under the right
    hand, a neck with a ribbon under the left."""
    fig = ctx.fig
    s = strap(fig, rise=14.0, drop=-2.0)
    k = fig.k
    pt = ctx.new()
    slab = [(-30.0, 6.5), (14.0, 8.0), (20.0, 4.0), (20.0, -4.0), (14.0, -9.5), (-30.0, -9.5), (-33.0, -1.5)]
    pt.region([_shape(ctx, s, slab, k, -4.0)], shade(color, 0.45))
    pt.region([_shape(ctx, s, slab, k)], color)
    # The keys: white keys across the slab, black keys between.
    n = 15
    for i in range(n):
        a0 = -28.0 + i * 2.8
        pt.region([_shape(ctx, s, [(a0, 5.0), (a0 + 2.5, 5.0), (a0 + 2.5, -8.0), (a0, -8.0)], k)], "#ffffff", outline=FINE * 0.5)
    for i in range(n - 1):
        if i % 7 in (2, 6):
            continue
        a0 = -28.0 + i * 2.8 + 1.8
        pt.flat([_shape(ctx, s, [(a0, 5.0), (a0 + 1.6, 5.0), (a0 + 1.6, -1.5), (a0, -1.5)], k)], "#1d1b22")
    # The neck with its ribbon and buttons.
    pt.region([_shape(ctx, s, [(18.0, 2.8), (52.0, 2.4), (56.0, 0.0), (52.0, -2.4), (18.0, -2.8)], k)], "#c23a6a", outline=FINE * 0.8)
    pt.flat([_shape(ctx, s, [(22.0, 0.8), (48.0, 0.7), (48.0, -0.7), (22.0, -0.8)], k)], "#1d1b22")
    for a in (24.0, 28.0):
        pt.flat([_shape(ctx, s, _ellipse(a, -1.7, 0.7, 0.7, 8), k)], "#ffd36a")
    _strap_line(ctx, pt, fig, s)
    return [Part("band_keytar", "torso", _z(ctx), pt.els, "Keytar (on its strap)", opacity="prop.keytar", opacity_default=0)]


def _strap_line(ctx: Ctx, pt, fig, s: Strap) -> None:
    """The strap over the left shoulder, from the horn to the bottom of the
    body, behind the neck."""
    if ctx.view.c < -0.3:
        return
    j = fig.joints
    sh = add3(j["left_shoulder"], (-2.0 * fig.k, -2.5 * fig.k, 2.0 * fig.k))
    pts = [s.at(16.0 * fig.k, 12.0 * fig.k), sh]
    pt.line([ctx.p(q) for q in pts], "#1d1b22", 1.4 * fig.k, smooth=False, fixed=True)


def _z(ctx: Ctx) -> float:
    """Over the clothes and under the near arm from the front; behind the
    body from the back."""
    return 36.0 if ctx.view.c > -0.3 else 1.4


def sticks_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """A drumstick in each fist, run through it as the game holds an item."""
    fig = ctx.fig
    out = []
    a = math.radians(-ITEM_REST_ANGLE)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    k = fig.k
    for depth, side in (("near", "right"), ("far", "left")):
        g = ctx.p(grip_point(fig, side))

        def at(t: float, w: float) -> Point:
            return (g[0] + ux * t * k + nx * w * k, g[1] + uy * t * k + ny * w * k)

        pt = ctx.new()
        pt.region([[at(-9.0, 0.75), at(30.0, 0.6), at(32.0, 0.0), at(30.0, -0.6), at(-9.0, -0.75)]], "#e7cf9a", outline=FINE * 0.7)
        pt.flat([[at(29.0, 0.9), at(32.5, 0.0), at(29.0, -0.9)]], "#f4ead2")
        out.append(Part(f"band_stick_{depth}", f"{depth}_grip", zmap[f"{depth}_arm_hand"] - 0.2, pt.els, f"Drumstick ({side} fist)",
                        opacity="prop.sticks", opacity_default=0))
    return out


def instrument_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """Every instrument of the band, all hidden (the ``chargen.extras``
    hook): a clip shows the one it plays."""
    return guitar_parts(ctx) + bass_parts(ctx) + keytar_parts(ctx) + sticks_parts(ctx, zmap)


# ---- playing ---------------------------------------------------------------------------------------


def _hand_at(fig, side: str, wrist: Vec3, pole: Vec3, item: float | None = None) -> Hand:
    """A hand whose wrist is at ``wrist`` (body frame, at rest)."""
    sh = fig.joints[f"{side}_shoulder"]
    sgn = -1.0 if side == "right" else 1.0
    it = None
    if item is not None:
        r = math.radians(item)
        it = (0.0, -math.sin(r), math.cos(r))
    return Hand(sub3(wrist, sh), (sgn * pole[0], pole[1], pole[2]), 0.0, it, 0.0)


def _off(p: Vec3, dx: float, dy: float, dz: float, k: float) -> Vec3:
    return (p[0] + dx * k, p[1] + dy * k, p[2] + dz * k)


def band_clips(fig, extras: Dict[str, float]) -> Dict[str, Clip]:
    """The rows that play each instrument. ``extras``: the channels the
    agent's own props take while it plays (its baton or wrench put away)."""
    kit = Kit(fig)
    k = fig.k
    out: Dict[str, Clip] = {}

    def pose(prop: str, rh: Hand, lh: Hand, *, bob: float = 0.0, nod: float = 0.0, lean: float = 3.0, face: str = "determined",
             **kw) -> Pose:
        ch = {c: (1.0 if c == prop else 0.0) for c in CHANNELS}
        ch.update(extras)
        return kit.pose(root=(0.0, -0.01 - bob, 0.0), lean=lean, head=(nod, 0.0), rh=rh, lh=lh,
                        rf=kit.foot("right", 0.1, 0.0, 0.05), lf=kit.foot("left", -0.1, 0.0, 0.06, toe=-6), face=face, **ch, **kw)

    def strummed(name: str, prop: str, s: Strap, strum_a: float, fret_a: float, *, sweep: float, slide: float, frames: int, ms: int) -> None:
        keys = []
        n = 8
        for i in range(n):
            t = i / n
            down = math.cos(t * math.tau * 2.0)
            strum = _off(s.at(strum_a * k, 0.0, 3.0 * k), -2.5, -3.0 + sweep * down, 3.0, k)
            fret = _off(s.at((fret_a + slide * math.sin(t * math.tau)) * k, 0.0, 1.0 * k), 0.0, 6.5, 1.0, k)
            rh = _hand_at(fig, "right", strum, (0.3, 0.6, -0.4))
            lh = _hand_at(fig, "left", fret, (0.6, 0.6, -0.3))
            bob = 0.008 * (1.0 - abs(down))
            keys.append((t, pose(prop, rh, lh, bob=bob, nod=-4.0 * down)))
        keys.append((1.0, keys[0][1]))
        out[name] = Clip(name, frames, ms, True, keys, "front_3q", "band")

    strummed("band_guitar", "prop.guitar", strap(fig, rise=28.0), -6.0, 40.0, sweep=4.5, slide=6.0, frames=8, ms=90)
    strummed("band_bass", "prop.bass", strap(fig, rise=22.0, drop=3.0), -8.0, 48.0, sweep=2.0, slide=8.0, frames=8, ms=110)

    # The keytar: the right hand walks along the keys, the left holds the neck.
    s = strap(fig, rise=14.0, drop=-2.0)
    keys = []
    for i in range(8):
        t = i / 8
        run = math.sin(t * math.tau)
        press = 0.5 + 0.5 * math.cos(t * math.tau * 4.0)
        rh = _hand_at(fig, "right", _off(s.at((-14.0 + 9.0 * run) * k, -2.0 * k, (4.0 - 2.0 * press) * k), -2.0, -2.0, 2.0, k), (0.3, 0.6, -0.4))
        lh = _hand_at(fig, "left", _off(s.at(30.0 * k, 0.0, 1.5 * k), 0.0, 6.0, 1.0, k), (0.6, 0.6, -0.3))
        keys.append((t, pose("prop.keytar", rh, lh, bob=0.006 * press, nod=-3.0 * press, face="happy")))
    keys.append((1.0, keys[0][1]))
    out["band_keytar"] = Clip("band_keytar", 8, 95, True, keys, "front_3q", "band")

    # The drums: sat on the throne, a stick in each fist, the hands beating
    # in turn.
    keys = []
    j = fig.joints
    for i in range(8):
        t = i / 8
        r_up = 0.5 + 0.5 * math.cos(t * math.tau * 2.0)
        l_up = 0.5 + 0.5 * math.cos(t * math.tau * 2.0 + math.pi)
        rh = kit.hand("right", 0.42, 0.42 + 0.22 * (1.0 - r_up), 0.18, pole=(0.5, 0.6, -0.3), item=8.0 + 26.0 * r_up)
        lh = kit.hand("left", 0.4, 0.44 + 0.22 * (1.0 - l_up), 0.2, pole=(0.5, 0.6, -0.3), item=8.0 + 26.0 * l_up)
        ch = {c: (1.0 if c == "prop.sticks" else 0.0) for c in CHANNELS}
        ch.update(extras)
        keys.append((t, kit.sitting(rh=rh, lh=lh, lean=8.0 + 3.0 * r_up, head=(-3.0 * l_up, 0.0), face="determined", **ch)))
    keys.append((1.0, keys[0][1]))
    out["band_drums"] = Clip("band_drums", 8, 85, True, keys, "front_3q", "band")
    del j
    return out


__all__ = ["CHANNELS", "ROWS", "band_clips", "instrument_parts", "strap"]
