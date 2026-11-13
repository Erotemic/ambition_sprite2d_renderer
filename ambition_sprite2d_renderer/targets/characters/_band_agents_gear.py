"""The bossofthegame's three named agents, on the character generator's body.

Geppetto (the GPT parody), Clause (the Claude parody) and Wren (the Qwen
parody) are one family in Jon's concept sheets
(``assets/concept_art/misc/agent-concepts/`` in the game repo): a dark
visor for a face with two glowing eyes, a cream garment over a dark chassis,
and one accent colour each. The spec of each draws the body and its clothes
(``data/characters/<name>/<name>.chargen.yaml``); this module draws what
makes each of them that agent, in 3D, in every view (``chargen.extras``):

* every agent: the visor over the face and its glowing eyes, one shape per
  expression, on the face channels of the generated face
  (``face_eyes__<face>_vis``), so a clip that names a face changes the eyes;
* Geppetto, the Orchestrator: a wide-brimmed plum hat with a magenta band and
  a gold gear on it, a magenta collar, gears on his coat, a plum mantle
  behind, and a conductor's baton in his right fist (``prop.baton``);
* Clause, the Analyst: a crown of orange petal fins round the back of his
  head, a cream poncho with orange edges and his starburst on it;
* Wren, the Generalist: a purple hood (the sheet's Field Agent) and a wrench
  in her right fist (the sheet's Engineer, ``prop.wrench``); Jon,
  2026-11-13: the wide hat and the fan were too much.

The band's instruments are parts every agent carries, hidden until a clip
shows one (``_band_instruments``).

Units are the figure's: centimetres, ``x`` to the body's left, ``y`` down
(the ground is 0), ``z`` forward; the body's right (``x < 0``) is the near
side in a side view.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence, Tuple

from ...chargen.draw import ITEM_REST_ANGLE, grip_point
from ...chargen.drawkit import Ctx, Part, shaded_region, surface_line
from ...chargen.face import FACES, eyes_part
from ...chargen.geometry import Loft, RingKey, ellipse3, lerp, loft_region, norm3, smoothstep, wrap180
from ...chargen.svgout import FINE, light, mix, shade

Point = Tuple[float, float]
Vec3 = Tuple[float, float, float]


@dataclass(frozen=True)
class Look:
    """One agent's colours."""

    visor: str
    eye: str
    glow: str
    cream: str
    accent: str
    accent_dark: str
    metal: str


GEPPETTO = Look(visor="#221b2c", eye="#ffd27a", glow="#ff9ad8", cream="#f0e4cc", accent="#d23d7e", accent_dark="#5b3470",
                metal="#e0b44a")
CLAUSE = Look(visor="#1e1b22", eye="#ffb057", glow="#ff8a3c", cream="#f2e8d8", accent="#e2763c", accent_dark="#41394a",
              metal="#f0a868")
WREN = Look(visor="#1f1b2a", eye="#ffd36a", glow="#ffc65a", cream="#f2e8d4", accent="#7a52c0", accent_dark="#3e2f63",
            metal="#b9c0cc")


def _poly(pt, pts: Sequence[Point], color: str, *, ink: bool = True, outline: float | None = None) -> None:
    if outline is not None:
        pt.region([list(pts)], color, outline=outline)
    elif ink:
        pt.region([list(pts)], color)
    else:
        pt.flat([list(pts)], color)


def _circle(x: float, y: float, r: float, n: int = 16) -> List[Point]:
    return [(x + r * math.cos(t), y + r * math.sin(t)) for t in (i * math.tau / n for i in range(n))]


# ---- the visor and the eyes --------------------------------------------------------------------------

#: The visor's edge round the face: (angle round the head, its top and its
#: bottom as parts of the head's height). It covers the brow to the chin.
VISOR_HALF = 74.0
VISOR_TOP = 0.2
VISOR_BOTTOM = 0.98


def _visor_margin(fig):
    def m(alpha: float, y: float) -> float:
        f = (y - fig.crown) / fig.hh
        a = abs(wrap180(alpha)) / VISOR_HALF
        # An oval: wide at the eyes, rounded to the brow and the chin.
        u = (f - 0.58) / (0.5 * (VISOR_BOTTOM - VISOR_TOP))
        return 1.0 - (a ** 2.4 + abs(u) ** 2.6)

    return m


def visor_parts(ctx: Ctx, look: Look) -> List[Part]:
    """A glossy dark visor over the face: the generated face under it does
    not show, the eyes on it do."""
    fig = ctx.fig
    if ctx.view.c < -0.55:
        return []
    loft = fig.head.shell(0.35, bumps=False)
    m = _visor_margin(fig)
    pt = ctx.new()
    polys = loft_region(ctx.view, loft, fig.fy(VISOR_TOP - 0.02), fig.fy(VISOR_BOTTOM + 0.02), m, step=0.35)
    if not polys:
        return []
    pt.region(polys, look.visor)
    return [Part("agent_visor", "head", 55.4, pt.els, "Visor")]


#: The eyes on the visor: their angle either side of the middle and their
#: height (parts of the head). Each face is a shape in (across, up) units of
#: the eye's size, drawn on the visor's surface.
EYE_ALPHA = 21.0
EYE_F = 0.55


def _pill(w: float, h: float, n: int = 10) -> List[Point]:
    """A rounded upright bar, centred."""
    r = w / 2.0
    top = [(r * math.cos(t), -(h / 2.0 - r) - r * math.sin(t)) for t in (math.pi * i / n for i in range(n + 1))]
    bot = [(-r * math.cos(t), (h / 2.0 - r) + r * math.sin(t)) for t in (math.pi * i / n for i in range(n + 1))]
    return top + bot


def _arc(w: float, h: float, up: bool, thick: float, n: int = 10) -> List[Point]:
    """A thick arc (a closed eye smiling ``up``, or drooping)."""
    s = -1.0 if up else 1.0
    outer = [(-w / 2 + w * i / n, s * h * math.sin(math.pi * i / n)) for i in range(n + 1)]
    inner = [(x, y - s * thick) for x, y in reversed(outer)]
    return outer + inner


def _eye_shape(face: str, side: float) -> List[Point]:
    """The eye of ``face`` (``side``: -1 the right eye, 1 the left), in
    units of the eye's height, centred, ``y`` down."""
    tilt = 0.0
    if face in ("happy",):
        return _arc(0.75, 0.32, True, 0.2)
    if face in ("smug",):
        return [(-0.3, -0.05), (0.3, -0.05), (0.26, 0.2), (0.0, 0.3), (-0.26, 0.2)]
    if face == "surprised":
        return _circle(0.0, 0.0, 0.34, 14)
    if face == "afraid":
        return _circle(0.0, 0.05, 0.22, 12)
    if face == "pained":
        a, w = 0.32, 0.09
        return [(-a, -a), (-a + w, -a), (0.0, -w), (a - w, -a), (a, -a), (w, 0.0), (a, a), (a - w, a), (0.0, w), (-a + w, a), (-a, a),
                (-w, 0.0)]
    if face == "sad":
        return _arc(0.7, 0.24, False, 0.18)
    if face in ("angry", "determined"):
        tilt = 0.32 if face == "angry" else 0.2
        pts = _pill(0.3, 0.72 if face == "determined" else 0.62)
        # Cut the top on a slant down toward the nose.
        return [(x, max(y, -0.36 + tilt * side * x * 3.0 * -1.0)) for x, y in pts]
    if face.startswith("look_"):
        return _pill(0.36, 0.8)
    return _pill(0.4, 0.9)


def _gaze(face: str) -> Point:
    return {"look_left": (0.35, 0.0), "look_right": (-0.35, 0.0), "look_up": (0.0, -0.18), "look_down": (0.0, 0.16)}.get(face, (0.0, 0.0))


def _eye_on_visor(ctx: Ctx, side: float, shape: Sequence[Point], size: float, gaze: Point) -> List[Point]:
    """``shape`` (units of ``size`` cm) laid on the visor at the eye of
    ``side``, as screen points; [] when that eye faces away."""
    fig = ctx.fig
    loft = fig.head.shell(0.45, bumps=False)
    a0 = side * EYE_ALPHA + gaze[0] * 9.0
    if ctx.view.facing(a0) < 0.12:
        return []
    out = []
    circ = math.radians(1.0) * max(1.0, fig.head.section(fig.fy(EYE_F)).rx)
    for x, y in shape:
        da = (x + gaze[0] * 0.0) * size / max(0.5, circ)
        yy = fig.fy(EYE_F) + (y + gaze[1]) * size
        out.append(ctx.p(loft.point(a0 + da, yy, 0.0)))
    return out


def eye_parts(ctx: Ctx, look: Look) -> List[Part]:
    """The glowing eyes, one part per face on that face's eye channel (the
    neutral face's is shown by default), and the blink."""
    fig = ctx.fig
    size = 0.3 * fig.hh
    out: List[Part] = []
    for face in FACES:
        pt = ctx.new()
        for side in (-1.0, 1.0):
            pts = _eye_on_visor(ctx, side, _eye_shape(face, side), size, _gaze(face))
            if len(pts) < 3:
                continue
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            halo = [(cx + (x - cx) * 1.55, cy + (y - cy) * 1.4) for x, y in pts]
            pt.flat([halo], look.glow, opacity=0.35)
            pt.flat([pts], look.eye)
            core = [(cx + (x - cx) * 0.45, cy + (y - cy) * 0.6) for x, y in pts]
            pt.flat([core], light(look.eye, 0.7))
        if pt.els:
            out.append(Part(f"agent_{eyes_part(face)}", "head", 55.6, pt.els, f"Visor Eyes - {face}", eyes_part(face) + "_vis",
                            1 if face == "neutral" else 0))
    blink = ctx.new()
    for side in (-1.0, 1.0):
        cover = _eye_on_visor(ctx, side, [(x * 1.5, y * 1.25) for x, y in _pill(0.4, 0.9)], size, (0.0, 0.0))
        if len(cover) < 3:
            continue
        blink.flat([cover], look.visor)
        line = _eye_on_visor(ctx, side, [(-0.28, 0.06), (0.28, 0.06), (0.28, 0.14), (-0.28, 0.14)], size, (0.0, 0.0))
        blink.flat([line], look.eye)
    if blink.els:
        out.append(Part("agent_blink", "head", 55.8, blink.els, "Visor Blink", "face_blink_vis", 0))
    return out


def earpiece_parts(ctx: Ctx, look: Look) -> List[Part]:
    """A round earpiece over each ear, as the sheets draw them: a metal rim
    round a dark disc with a light in it. The generated ears are under it."""
    fig = ctx.fig
    hh = fig.hh
    pt = ctx.new()
    for sgn in (-1.0, 1.0):
        a = sgn * 96.0
        f = ctx.view.facing(a)
        if f < 0.05:
            continue
        c = fig.skull.point(a, fig.fy(0.53), 0.04 * hh)
        n = (math.sin(math.radians(a)), 0.0, math.cos(math.radians(a)))
        u = norm3((n[2], 0.0, -n[0]))
        rim = [ctx.p(q) for q in ellipse3(c, u, (0.0, 1.0, 0.0), 0.13 * hh, 0.13 * hh, 18)]
        disc = [ctx.p(q) for q in ellipse3(c, u, (0.0, 1.0, 0.0), 0.085 * hh, 0.085 * hh, 16)]
        dot = [ctx.p(q) for q in ellipse3(c, u, (0.0, 1.0, 0.0), 0.035 * hh, 0.035 * hh, 10)]
        pt.region([rim], mix(look.visor, look.metal, 0.55), outline=FINE * 0.9)
        pt.flat([disc], look.visor)
        pt.flat([dot], look.eye)
    if not pt.els:
        return []
    return [Part("agent_earpieces", "head", 55.5, pt.els, "Earpieces")]


# ---- a mantle or a poncho hung from the shoulders ------------------------------------------------------


def _drape(fig, *, top: float, hem: float, flare: float, back: float, front: float) -> Loft:
    """A cloth body from the neck to ``hem`` (a height): its rings are the
    torso's, grown by ``flare`` (cm at the hem) and pushed ``back`` and
    ``front`` cm."""
    t = fig.torso
    keys = []
    n = 9
    for i in range(n):
        u = i / (n - 1)
        y = lerp(top, hem, u)
        s = t.section(min(max(y, t.top), t.bottom))
        g = 1.5 + flare * smoothstep(0.0, 1.0, u)
        shoulder = 4.0 * fig.k * math.sin(math.pi * min(1.0, u * 2.2))
        keys.append(RingKey(y, s.rx + g + shoulder, s.rzf + front * u + g * 0.6 + 1.0, s.rzb + back * u + g * 0.7 + 1.0, s.cl, s.cz, 2.2))
    return Loft(keys)


def _behind(view_c: float, near: float, far: float) -> float:
    """A cloth's paint order: behind the body when the camera sees the
    front, over it from behind."""
    return near if view_c > -0.25 else far


def mantle_parts(ctx: Ctx, look: Look, *, color: str, lining: str, hem_f: float, name: str, label: str, open_: float = 92.0,
                 flare: float = 22.0, back: float = 16.0) -> List[Part]:
    """A mantle hung from the shoulders, open ``open_`` degrees either side
    of the front, its hem cut in points (Geppetto's plum mantle down his
    back; Wren's short cape round her shoulders)."""
    fig = ctx.fig
    hem = lerp(fig.y_sh, 0.0, hem_f)
    loft = _drape(fig, top=fig.y_sh - 3.0 * fig.k, hem=hem, flare=flare * fig.k, back=back * fig.k, front=0.0)

    def m(alpha: float, y: float) -> float:
        a = abs(wrap180(alpha))
        u = (y - loft.top) / (loft.bottom - loft.top)
        # The back half, and a point every 40 degrees along the hem.
        tooth = 0.16 * (1.0 - abs(((wrap180(alpha) + 180.0) / 36.0) % 2.0 - 1.0))
        return min((a - open_) / 30.0, (1.0 - tooth) - u)

    pt = ctx.new()
    polys = loft_region(ctx.view, loft, loft.top, loft.bottom, m, step=0.6, solid=True)
    if not polys:
        return []
    pt.region(polys, color)
    # Its lining shows at the edges in a side view.
    def edge(alpha: float, y: float) -> float:
        return min(m(alpha, y), 0.12 - abs(abs(wrap180(alpha)) - (open_ + 8.0)) / 30.0)

    pt.flat(loft_region(ctx.view, loft, loft.top, loft.bottom, edge, step=0.6), lining)
    if open_ < 80.0:
        # A short cape round the shoulders is over the arms from every side.
        return [Part(name, "torso", 47.0, pt.els, label)]
    z = _behind(ctx.view.c, 2.0, 58.0)
    return [Part(name, "torso", z, pt.els, label)]


# ---- Geppetto ---------------------------------------------------------------------------------------


def _gear_outline(x: float, y: float, r: float, teeth: int = 8) -> List[Point]:
    pts = []
    for i in range(teeth * 4):
        t = i / (teeth * 4) * math.tau
        rr = r if (i % 4) in (0, 1) else r * 0.78
        pts.append((x + rr * math.cos(t), y + rr * math.sin(t)))
    return pts


def gear_badge(pt, x: float, y: float, r: float, color: str, hole: str) -> None:
    pt.region([_gear_outline(x, y, r)], color, outline=FINE * 0.8)
    pt.flat([_circle(x, y, r * 0.38, 12)], hole)


def geppetto_hat_parts(ctx: Ctx, look: Look) -> List[Part]:
    """A gear on the band of his hat (the spec draws the brimmed hat): the
    gear sits on the band at the front-right of the crown."""
    fig = ctx.fig
    out: List[Part] = []
    pt = ctx.new()
    a = -28.0
    if ctx.view.facing(a) > 0.1:
        c = fig.skull.point(a, fig.fy(0.06), 2.6 * fig.k)
        x, y = ctx.p(c)
        gear_badge(pt, x, y, 3.2 * fig.k, look.metal, look.accent_dark)
    if pt.els:
        out.append(Part("geppetto_hat_gear", "head", 60.5, pt.els, "Hat Gear"))
    return out


def coat_gears(ctx: Ctx, look: Look) -> List[Part]:
    """Magenta gears on the skirts of his coat, front and back, as the
    Orchestrator's coat has them."""
    fig = ctx.fig
    pt = ctx.new()
    y = lerp(fig.y_hip, 0.0, 0.42)
    for alpha in (-38.0, 38.0, 150.0, -150.0):
        f = ctx.view.facing(alpha)
        if f < 0.25:
            continue
        r_out = fig.torso.section(fig.y_hip).rx * 1.45 + 6.0 * fig.k
        c = (r_out * math.sin(math.radians(alpha)), y, r_out * 0.8 * math.cos(math.radians(alpha)))
        x, yy = ctx.p(c)
        r = 6.0 * fig.k
        sx = max(0.3, f)
        gear = [(x + (px - x) * sx, py) for px, py in _gear_outline(x, yy, r, 8)]
        pt.flat([gear], look.accent, opacity=0.9)
        pt.flat([[(x + (px - x) * sx, py) for px, py in _circle(x, yy, r * 0.36, 12)]], look.cream)
    if not pt.els:
        return []
    return [Part("geppetto_coat_gears", "torso", 33.4, pt.els, "Coat Gears")]


def baton_parts(ctx: Ctx, look: Look) -> List[Part]:
    """His conductor's baton, in his right fist: he orchestrates."""
    fig = ctx.fig
    g = ctx.p(grip_point(fig, "right"))
    a = math.radians(-ITEM_REST_ANGLE)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    k = fig.k

    def at(s: float, w: float) -> Point:
        return (g[0] + ux * s + nx * w, g[1] + uy * s + ny * w)

    pt = ctx.new()
    pt.region([[at(-5.5, 1.1 * k), at(4.0, 0.9 * k), at(46.0 * k, 0.28 * k), at(46.0 * k, -0.28 * k), at(4.0, -0.9 * k), at(-5.5, -1.1 * k)]],
              "#f6f1e6", outline=FINE * 0.8)
    pt.region([[at(-6.5, 1.5 * k), at(-1.5, 1.5 * k), at(-1.5, -1.5 * k), at(-6.5, -1.5 * k)]], look.accent_dark, outline=FINE * 0.8)
    tip = at(46.0 * k, 0.0)
    pt.flat([_circle(tip[0], tip[1], 1.6 * k, 10)], look.glow, opacity=0.6)
    return [Part("baton", "near_grip", 48.0, pt.els, "Conductor's Baton (in his right fist)", opacity="prop.baton", opacity_default=1)]


def geppetto_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    look = GEPPETTO
    return (visor_parts(ctx, look) + eye_parts(ctx, look) + geppetto_hat_parts(ctx, look) + coat_gears(ctx, look)
            + earpiece_parts(ctx, look)
            + mantle_parts(ctx, look, color=look.accent_dark, lining=look.accent, hem_f=0.86, name="geppetto_mantle", label="Mantle")
            + _with_zmap(baton_parts(ctx, look), zmap, "near_arm_hand", -0.2))


# ---- Clause -----------------------------------------------------------------------------------------

#: His petal fins: how many, the fan's spread either side of straight up
#: (degrees), and their length and width as parts of the head's height.
FINS = 9
FIN_SPREAD = 84.0
FIN_LEN = 0.62
FIN_W = 0.2


def crown_parts(ctx: Ctx, look: Look) -> List[Part]:
    """A crown of orange petal fins in a fan round the back of his head,
    each fin a blunt blade, darker at its root; they lean back so the fan
    shows from the side too."""
    fig = ctx.fig
    hh = fig.hh
    c = (0.0, fig.fy(0.48), -0.12 * hh)
    r0 = 0.4 * hh
    pt_back = ctx.new()
    pt_front = ctx.new()
    fins = []
    # The fins stand on a cone round an axis that points up and back from
    # the head: from the front they ring the head, from the side they fan
    # out behind it, as the sheet draws them in both.
    axis = norm3((0.0, -0.5, -0.87))
    up = norm3((0.0, -0.87, 0.5))
    cone = math.radians(62.0)
    for i in range(FINS):
        th = math.radians(-FIN_SPREAD - 14.0 + 2.0 * (FIN_SPREAD + 14.0) * i / (FINS - 1))
        radial = tuple(math.cos(th) * up[j] + math.sin(th) * (1.0, 0.0, 0.0)[j] for j in range(3))
        d = norm3(tuple(math.cos(cone) * axis[j] + math.sin(cone) * radial[j] for j in range(3)))
        side = norm3((d[1] * axis[2] - d[2] * axis[1], d[2] * axis[0] - d[0] * axis[2], d[0] * axis[1] - d[1] * axis[0]))
        length = FIN_LEN * hh * (1.0 - 0.12 * abs(math.sin(th)))
        w = FIN_W * hh * 0.5

        def P(s: float, t: float) -> Vec3:
            return (c[0] + d[0] * s + side[0] * t, c[1] + d[1] * s + side[1] * t, c[2] + d[2] * s + side[2] * t)

        quad = [P(r0, -w * 0.8), P(r0 + length, -w), P(r0 + length + 0.04 * hh, 0.0), P(r0 + length, w), P(r0, w * 0.8)]
        root = [P(r0, -w * 0.8), P(r0 + length * 0.35, -w * 0.9), P(r0 + length * 0.35, w * 0.9), P(r0, w * 0.8)]
        depth = sum(ctx.view.depth(q) for q in quad) / len(quad)
        fins.append((depth, quad, root))
    for depth, quad, root in sorted(fins, key=lambda f: f[0]):
        pt = pt_front if depth > ctx.view.depth(c) + 0.05 * hh else pt_back
        pt.region([[ctx.p(q) for q in quad]], look.accent)
        pt.flat([[ctx.p(q) for q in root]], shade(look.accent, 0.3))
    out = []
    if pt_back.els:
        out.append(Part("clause_crown_back", "head", 1.5, pt_back.els, "Crown of Fins (behind)"))
    if pt_front.els:
        out.append(Part("clause_crown_front", "head", 56.0, pt_front.els, "Crown of Fins (in front)"))
    return out


def poncho_parts(ctx: Ctx, look: Look) -> List[Part]:
    """A cream poncho over his chassis, to the hips at the sides and longer
    at the front and back in two points, its edges orange, with his
    starburst on his left breast."""
    fig = ctx.fig
    hem = lerp(fig.y_sh, 0.0, 0.62)
    loft = _drape(fig, top=fig.y_nb + 1.0, hem=hem, flare=16.0 * fig.k, back=6.0 * fig.k, front=6.0 * fig.k)

    def m(alpha: float, y: float) -> float:
        u = (y - loft.top) / (loft.bottom - loft.top)
        # Cut on a slant, as the sheet's poncho: short at his left front, a
        # long point at his right front and a longer one down his back.
        a = math.radians(alpha)
        front = max(0.0, math.cos(a + math.radians(40.0))) ** 1.6
        back = max(0.0, -math.cos(a + math.radians(15.0))) ** 1.4
        reach = 0.42 + 0.33 * front + 0.55 * back
        return reach - u

    pt = ctx.new()
    polys = loft_region(ctx.view, loft, loft.top, loft.bottom, m, step=0.5)
    if not polys:
        return []
    pt.region(polys, look.cream)

    def edge(alpha: float, y: float) -> float:
        return min(m(alpha, y), 0.06 - m(alpha, y) + 0.0)

    pt.flat(loft_region(ctx.view, loft, loft.top, loft.bottom, lambda a, y: 0.06 - abs(m(a, y) - 0.03), step=0.4), look.accent)
    # The starburst on his left breast.
    a0 = 30.0
    if ctx.view.facing(a0) > 0.2:
        cy = lerp(fig.y_sh, fig.y_belt, 0.32)
        cpt = loft.point(a0, cy, 0.3)
        x, y = ctx.p(cpt)
        r = 4.6 * fig.k
        sx = max(0.35, ctx.view.facing(a0))
        for i in range(4):
            t = math.radians(i * 45.0 + 10.0)
            pt.line([(x - r * math.cos(t) * sx, y - r * math.sin(t)), (x + r * math.cos(t) * sx, y + r * math.sin(t))], look.accent,
                    0.9 * fig.k, smooth=False, fixed=True)
    z = 34.0 if ctx.view.c > -0.25 else 34.0
    return [Part("clause_poncho", "torso", z, pt.els, "Poncho")]


def clause_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    look = CLAUSE
    return visor_parts(ctx, look) + eye_parts(ctx, look) + earpiece_parts(ctx, look) + crown_parts(ctx, look) + poncho_parts(ctx, look)


# ---- Wren -------------------------------------------------------------------------------------------


def hood_parts(ctx: Ctx, look: Look) -> List[Part]:
    """A purple hood over her head, open round the face, falling to the
    shoulders behind, with a peak over the brow."""
    fig = ctx.fig
    hh = fig.hh
    sk = fig.skull
    keys = []
    for kk in sk.keys:
        f = (kk.y - fig.crown) / hh
        if f > 1.02:
            break
        g = 0.07 * hh + 0.04 * hh * smoothstep(0.5, 1.0, f)
        keys.append(RingKey(kk.y, kk.rx + g, kk.rzf + g * 0.8, kk.rzb + g * 1.3, kk.cl, kk.cz, kk.sq))
    k0 = sk.keys[0]
    keys[0] = RingKey(k0.y - 0.08 * hh, 0.0, 0.0, 0.0, k0.cl, k0.cz - 0.03 * hh, k0.sq)
    neck = fig.neck.section(fig.y_nb)
    keys.append(RingKey(fig.y_nb + 2.0 * fig.k, neck.rx + 0.42 * hh, neck.rzf + 0.25 * hh, neck.rzb + 0.4 * hh, 0.0, 0.0, 2.2))
    loft = Loft(keys)

    def face_hole(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        a = abs(wrap180(alpha)) / 68.0
        u = (f - 0.62) / 0.5
        return (a ** 2.2 + abs(u) ** 2.4) - 1.0

    pt = ctx.new()
    outer = loft_region(ctx.view, loft, loft.top, loft.bottom, face_hole, step=0.4)
    if not outer:
        return []
    pt.region(outer, look.accent)
    pt.flat(loft_region(ctx.view, loft, loft.top, loft.bottom, lambda a, y: min(face_hole(a, y), 0.25 - face_hole(a, y)), step=0.4),
            shade(look.accent, 0.3))
    # The fold down the back of the hood, and its hem.
    for run in surface_line(ctx, loft, [(180.0, lerp(loft.top + 2.0, loft.bottom - 3.0, i / 12.0)) for i in range(13)], out=0.1):
        pt.line(run, shade(look.accent, 0.4), FINE * 1.2)
    out = [Part("wren_hood", "head", 57.0, pt.els, "Hood")]
    # Inside the hood, round the face: the dark lining.
    if ctx.view.c > -0.2:
        inside = ctx.new()
        lining = loft_region(ctx.view, loft.shell(-0.04 * hh, bumps=False), loft.top, loft.bottom,
                             lambda a, y: -face_hole(a, y) + 0.0, step=0.4, solid=True)
        if lining:
            inside.flat(lining, look.accent_dark)
            out.append(Part("wren_hood_inside", "head", 1.2, inside.els, "Hood - Inside"))
    return out


def wrench_parts(ctx: Ctx, look: Look) -> List[Part]:
    """A big steel wrench in her right fist (the sheet's Engineer): open jaws
    ahead, a ring behind."""
    fig = ctx.fig
    g = ctx.p(grip_point(fig, "right"))
    a = math.radians(-ITEM_REST_ANGLE)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    k = fig.k

    def at(s: float, w: float) -> Point:
        return (g[0] + ux * s * k + nx * w * k, g[1] + uy * s * k + ny * w * k)

    pt = ctx.new()
    steel, dark = look.metal, shade(look.metal, 0.35)
    # The handle.
    pt.region([[at(-10.0, 1.5), at(28.0, 1.7), at(28.0, -1.7), at(-10.0, -1.5)]], steel, outline=FINE * 0.9)
    pt.flat([[at(-8.0, 0.4), at(26.0, 0.5), at(26.0, -0.4), at(-8.0, -0.4)]], dark, opacity=0.6)
    # The open jaws ahead.
    jaw = [at(26.0, 2.2), at(31.0, 5.2), at(37.0, 5.6), at(38.5, 3.4), at(33.5, 2.6), at(33.5, -2.6), at(38.5, -3.4), at(37.0, -5.6),
           at(31.0, -5.2), at(26.0, -2.2)]
    pt.region([jaw], steel, outline=FINE * 0.9)
    # The ring behind the fist.
    c = at(-13.5, 0.0)
    pt.region([_circle(c[0], c[1], 4.0 * k, 16)], steel, outline=FINE * 0.9)
    pt.region([_circle(c[0], c[1], 2.1 * k, 12)], look.accent_dark, outline=FINE * 0.6)
    # A purple grip wrapped round the handle under her fist.
    pt.flat([[at(-4.0, 1.9), at(6.0, 1.9), at(6.0, -1.9), at(-4.0, -1.9)]], look.accent)
    return [Part("wrench", "near_grip", 48.0, pt.els, "Wrench (in her right fist)", opacity="prop.wrench", opacity_default=1)]


def wren_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    look = WREN
    return (visor_parts(ctx, look) + eye_parts(ctx, look) + hood_parts(ctx, look)
            + mantle_parts(ctx, look, color=look.accent, lining=look.eye, hem_f=0.22, name="wren_cape", label="Short Cape", open_=48.0,
                           flare=7.0, back=5.0)
            + _with_zmap(wrench_parts(ctx, look), zmap, "near_arm_hand", -0.2))


# ---- shared ---------------------------------------------------------------------------------------


def _with_zmap(parts: List[Part], zmap: Dict[str, float], key: str, dz: float) -> List[Part]:
    """``parts`` painted just over (or under) the part ``key`` of this view."""
    from dataclasses import replace

    return [replace(p, z=zmap[key] + dz) for p in parts]


__all__ = ["CLAUSE", "GEPPETTO", "WREN", "Look", "clause_parts", "geppetto_parts", "wren_parts"]
