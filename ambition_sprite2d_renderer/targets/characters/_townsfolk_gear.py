"""Gear a resident carries that the character generator has no slot for.

A resident's spec file names its gear in its ``game`` section
(``gear: [laser_sword, wizard_hat]``); each name here is a function that
draws parts from the figure, in 3D, in every view (``chargen.extras``), as
the band agents' gear is drawn. The first of them are Hobford's adventurers
(2026-11-20): fantasy kit, and the imports the gate brought them.

Units are the figure's: centimetres, ``x`` to the body's left, ``y`` down
(the ground is 0), ``z`` forward; the body's right (``x < 0``) is the near
side in a side view.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Callable, Dict, List, Sequence, Tuple

from ...chargen.draw import ITEM_REST_ANGLE, grip_point
from ...chargen.drawkit import Ctx, Part, shaded_region
from ...chargen.geometry import Loft, RingKey
from ...chargen.svgout import FINE, shade
from . import _western_gear as _western

Point = Tuple[float, float]


def _in_fist(ctx: Ctx, side: str = "right", angle: float = ITEM_REST_ANGLE) -> Callable[[float, float], Point]:
    """A point ``s`` cm along an item held in the ``side`` fist and ``w`` cm
    across it, as the band's wrench is held."""
    fig = ctx.fig
    g = ctx.p(grip_point(fig, side))
    a = math.radians(-angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    k = fig.k

    def at(s: float, w: float) -> Point:
        return (g[0] + ux * s * k + nx * w * k, g[1] + uy * s * k + ny * w * k)

    return at


def _circle(x: float, y: float, r: float, n: int = 14) -> List[Point]:
    return [(x + r * math.cos(t), y + r * math.sin(t)) for t in (i * math.tau / n for i in range(n))]


def _over(parts: List[Part], zmap: Dict[str, float], key: str, dz: float) -> List[Part]:
    """``parts`` painted just over (or under) the part ``key`` of this view."""
    return [replace(p, z=zmap[key] + dz) for p in parts]


#: The laser sword's blade: its glow and its white core.
BLADE_GLOW = "#5fe8ff"
BLADE_CORE = "#f4feff"
HILT = "#3a3d44"
GUARD = "#c9a54a"
WRAP = "#6b4a2e"


def laser_sword(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """An imported laser sword in the right fist, fitted with the valley's
    idea of a sword: a brass crossguard, a leather-wrapped grip and a round
    pommel on the steel tube, and the blade a bar of cyan light."""
    at = _in_fist(ctx)
    pt = ctx.new()
    # The blade: a soft glow, then the white core.
    pt.flat([[at(9.0, 3.6), at(78.0, 3.0), at(81.0, 0.0), at(78.0, -3.0), at(9.0, -3.6)]], BLADE_GLOW, opacity=0.45)
    pt.region([[at(9.0, 1.7), at(77.0, 1.5), at(79.5, 0.0), at(77.0, -1.5), at(9.0, -1.7)]], BLADE_GLOW, outline=FINE * 0.5)
    pt.flat([[at(9.0, 0.8), at(76.0, 0.7), at(78.0, 0.0), at(76.0, -0.7), at(9.0, -0.8)]], BLADE_CORE)
    # The tube, the wrap, the guard and the pommel.
    pt.region([[at(-7.0, 1.7), at(9.0, 1.9), at(9.0, -1.9), at(-7.0, -1.7)]], HILT, outline=FINE * 0.9)
    pt.flat([[at(-4.0, 1.9), at(5.0, 1.9), at(5.0, -1.9), at(-4.0, -1.9)]], WRAP)
    pt.region([[at(6.5, 6.5), at(9.0, 6.5), at(9.0, -6.5), at(6.5, -6.5)]], GUARD, outline=FINE * 0.9)
    c = at(-8.5, 0.0)
    pt.region([_circle(c[0], c[1], 2.4 * ctx.fig.k)], GUARD, outline=FINE * 0.8)
    return _over([Part("laser_sword", "near_grip", 48.0, pt.els, "Laser sword (in the right fist)")], zmap, "near_arm_hand", -0.2)


CALC_CASE = "#2b2d33"
CALC_SCREEN = "#a9c48a"
CALC_KEY = "#d8d4c8"


def calculator(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """An imported pocket calculator held up in the right fist like a book
    of spells: a dark case, a green screen and rows of pale keys."""
    fist = _in_fist(ctx, angle=-60.0)
    # A little larger than life, so it reads at play scale.

    def at(s: float, w: float) -> Point:
        return fist(s * 1.5, w * 1.5)

    pt = ctx.new()
    pt.region([[at(-2.0, 4.5), at(14.0, 4.5), at(14.0, -4.5), at(-2.0, -4.5)]], CALC_CASE, outline=FINE * 0.9)
    pt.flat([[at(9.0, 3.4), at(13.0, 3.4), at(13.0, -3.4), at(9.0, -3.4)]], CALC_SCREEN)
    for row in range(3):
        for col in range(3):
            s, w = 1.0 + row * 2.6, -2.8 + col * 2.8
            pt.flat([[at(s, w + 0.9), at(s + 1.6, w + 0.9), at(s + 1.6, w - 0.9), at(s, w - 0.9)]], CALC_KEY)
    return _over([Part("calculator", "near_grip", 48.0, pt.els, "Calculator (in the right fist)")], zmap, "near_arm_hand", -0.2)


HAT = "#3b3f8a"
HAT_BAND = "#d9b44a"


def wizard_hat(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """A hedge wizard's hat: a tall cone with a bent tip, a wide floppy brim
    and a brass-coloured band. It sits on the skull above the ears."""
    fig = ctx.fig
    hh = fig.hh
    sit = fig.crown + 0.3 * hh
    base = fig.skull.section(sit)
    g = 0.03 * hh
    keys = [
        RingKey(fig.crown - 0.95 * hh, 0.02 * hh, 0.02 * hh, 0.02 * hh, 0.0, base.cz - 0.22 * hh),
        RingKey(fig.crown - 0.6 * hh, 0.12 * hh, 0.12 * hh, 0.12 * hh, 0.0, base.cz - 0.08 * hh),
        RingKey(fig.crown - 0.1 * hh, base.rx * 0.8, base.rzf * 0.8, base.rzb * 0.8, 0.0, base.cz),
        RingKey(sit - 0.04 * hh, base.rx + g, base.rzf + g, base.rzb + g, base.cl, base.cz),
        RingKey(sit, base.rx + 0.42 * hh, base.rzf + 0.42 * hh, base.rzb + 0.42 * hh, base.cl, base.cz),
        RingKey(sit + 0.04 * hh, base.rx + 0.45 * hh, base.rzf + 0.45 * hh, base.rzb + 0.45 * hh, base.cl, base.cz),
    ]
    loft = Loft(keys)
    pt = ctx.new()
    if not shaded_region(ctx, pt, loft, loft.top, loft.bottom, HAT):
        return []
    band = Loft([RingKey(sit - 0.16 * hh, base.rx * 0.93 + g, base.rzf * 0.93 + g, base.rzb * 0.93 + g, base.cl, base.cz),
                 RingKey(sit - 0.05 * hh, base.rx + g * 1.2, base.rzf + g * 1.2, base.rzb + g * 1.2, base.cl, base.cz)])
    shaded_region(ctx, pt, band, band.top, band.bottom, HAT_BAND, shade_frac=0.1)
    return [Part("wizard_hat", "head", 58.0, pt.els, "Wizard's hat")]


HELM = "#9aa3ad"


def head_torch(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """An imported head torch strapped round a ranger's hood: an elastic
    band at the brow and a lamp over the forehead, lit."""
    fig = ctx.fig
    hh = fig.hh
    y = fig.crown + 0.32 * hh
    sk = fig.skull.section(y)
    strap = Loft([RingKey(y - 0.035 * hh, sk.rx + 0.05 * hh, sk.rzf + 0.05 * hh, sk.rzb + 0.05 * hh, sk.cl, sk.cz),
                  RingKey(y + 0.035 * hh, sk.rx + 0.05 * hh, sk.rzf + 0.05 * hh, sk.rzb + 0.05 * hh, sk.cl, sk.cz)])
    pt = ctx.new()
    shaded_region(ctx, pt, strap, strap.top, strap.bottom, "#2e3a2c", shade_frac=0.1)
    out = [Part("head_torch_strap", "head", 58.5, pt.els, "Head torch strap")]
    if ctx.view.c > -0.1:
        lamp = ctx.p((0.0, y, sk.cz + sk.rzf + 0.08 * hh))
        lp = ctx.new()
        r = 0.07 * hh * fig.k
        lp.region([_circle(lamp[0], lamp[1], r * 1.2)], "#3c3f44", outline=FINE * 0.8)
        lp.flat([_circle(lamp[0], lamp[1], r * 0.75)], "#fff6c8")
        out.append(Part("head_torch_lamp", "head", 58.6, lp.els, "Head torch lamp"))
    return out


#: Each name a resident's ``game.gear`` may list.
GEAR: Dict[str, Callable[[Ctx, Dict[str, float]], List[Part]]] = {
    "laser_sword": laser_sword,
    "calculator": calculator,
    "wizard_hat": wizard_hat,
    "head_torch": head_torch,
    "cowboy_hat": _western.cowboy_hat,
    "muzzle_cage": _western.muzzle_cage,
    "bushy_tail": _western.bushy_tail,
    "poncho": _western.poncho,
    "gun_belt": _western.gun_belt,
}


def gear_parts(names: Sequence[str]) -> List[Callable[[Ctx, Dict[str, float]], List[Part]]]:
    """The part functions of ``names``; an unknown name is refused."""
    unknown = [n for n in names if n not in GEAR]
    if unknown:
        raise KeyError(f"unknown gear {unknown}; one of {sorted(GEAR)}")
    return [GEAR[n] for n in names]


__all__ = ["GEAR", "gear_parts"]
