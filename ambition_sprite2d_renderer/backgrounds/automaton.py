"""The scenes of the Automaton dimension (gate address CELLS,
`docs/planning/game/automaton-dimension.md`).

`automaton`: the Works, the clockwork town. A lavender sky with soft
clouds, and high in it a glider of lit cells stepping across, the other
kind of automaton looking in. Far off, a great brass ring stands over the
towers with an armillary turning in it, and the giant robot sits in the
haze with its hand open. Nearer, an aqueduct on arches carries a small
train, water falls from it on a wheel, and gear towers stand among trees.

`automaton_life`: the Life field. Night, a galaxy, and a floor of cells
running off to the horizon; pillars of cubes with lit patterns on their
tops, a tower of cubes in an amber ring, and panels in the air showing the
patterns of the rule: a glider, a blinker, a Sierpinski triangle.

`automaton_tower`: inside the clock tower, where the Tape Room is. Walls of
lavender stone in the warm light that comes through the back of the clock
face, a great disc of lit glass with the shadows of its hands; brass gears
turning behind; beams across, chains and the pendulum hanging in front.

`automaton_arena`: the Cell-ular Arena's backdrop (the room's terrain is the
Life field's): a bowl of cube stands, the crowd lit cells, and a screen
over the ring with Gosper's glider gun firing on it.

Nothing on a backdrop is writing (the game draws some backdrops mirrored).
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, smoothstep
from .parts import HORIZON, cumulus, fog, haze, lamps, solid

WORKS = {
    "sky_top": (128, 128, 200),
    "sky": (176, 170, 226),
    "sky_low": (232, 208, 226),
    "cloud": (250, 240, 248),
    "cloud_shadow": (196, 180, 220),
    "cell": (255, 236, 170),
    "brass": (214, 170, 92),
    "brass_dark": (150, 110, 60),
    "stone": (176, 160, 196),
    "stone_dark": (118, 104, 150),
    "stone_far": (186, 176, 214),
    "robot": (170, 166, 196),
    "water": (150, 214, 236),
    "leaf": (110, 150, 96),
    "leaf_dark": (70, 110, 76),
    "train": (150, 96, 70),
    "lamp": (255, 222, 150),
    "haze": (214, 200, 232),
}

LIFE = {
    "top": (10, 12, 34),
    "mid": (28, 24, 70),
    "low": (60, 44, 110),
    "star": (210, 220, 255),
    "galaxy": (150, 120, 240),
    "galaxy_core": (200, 220, 255),
    "cube": (36, 36, 70),
    "cube_light": (70, 70, 120),
    "cell": (120, 220, 255),
    "amber": (255, 184, 70),
    "grid": (80, 120, 220),
    "haze": (50, 44, 100),
}

#: The patterns of the rule, as rows of cells.
GLIDER = ("010", "001", "111")
BLINKER = ("010", "010", "010")
SPACESHIP = ("01111", "10001", "00001", "10010")


def cells(pen: Pen, pattern, u: float, v: float, s: float, gap: float = 0.18) -> None:
    """The live cells of `pattern` (rows of '0'/'1'), its top left at (u, v),
    each cell `s` wide."""
    inset = s * gap / 2.0
    for r, row in enumerate(pattern):
        for c, ch in enumerate(row):
            if ch == "1":
                pen.rect(u + c * s + inset, v + r * s + inset, u + (c + 1) * s - inset, v + (r + 1) * s - inset)


def sierpinski(rows: int) -> list[str]:
    """Rule 90 from one live cell: the rows of a Sierpinski triangle."""
    w = 2 * rows - 1
    row = [0] * w
    row[rows - 1] = 1
    out = []
    for _ in range(rows):
        out.append("".join(str(x) for x in row))
        row = [(row[i - 1] if i > 0 else 0) ^ (row[i + 1] if i < w - 1 else 0) for i in range(w)]
    return out


def gear(pen: Pen, cu: float, cv: float, r: float, teeth: int, hole: float = 0.45, value: int = 255) -> None:
    """A gear: a disc with `teeth` teeth, the hub left open."""
    pts = []
    for k in range(teeth * 4):
        a = math.tau * k / (teeth * 4)
        rr = r if (k % 4) in (0, 1) else r * 0.84
        pts.append((cu + rr * math.cos(a), cv + rr * math.sin(a)))
    pen.poly(pts, value)
    if hole > 0.0:
        pen.ellipse(cu, cv, r * hole, value=0)


# ---------------------------------------------------------------------------
# The Works
# ---------------------------------------------------------------------------


def automaton(layer_key: str, art: Art) -> np.ndarray:
    p = WORKS
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["sky_top"]), (0.4, p["sky"]), (HORIZON + 0.05, p["sky_low"]), (1.0, p["sky_low"])]))
        clouds = cumulus(art, "works clouds", 0.34, 0.14, 3.0, 0.45, p["cloud"], p["cloud_shadow"])
        layer = art.over(layer, clouds)
        # A glider of lit cells stepping across the sky, its trail fading.
        s = 0.012
        for k, fade in enumerate((60, 110, 170)):
            img, pen = art.drawing()
            cells(pen, GLIDER, 0.66 + k * 0.045, 0.06 + k * 0.045, s)
            art.light(layer, art.mask_of(img, blur=0.4), p["cell"], fade / 255.0 * 0.6)
        head, h_pen = art.drawing()
        cells(h_pen, GLIDER, 0.66 + 3 * 0.045, 0.06 + 3 * 0.045, s)
        hm = art.mask_of(head, blur=0.4)
        art.put(layer, hm, p["cell"], 0.95)
        art.light(layer, art.blur(hm, 4.0), p["cell"], 0.4)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # Towers under a great brass ring, an armillary in it; the giant
        # robot sitting in the haze, its hand open.
        rng = art.rand("works towers")
        image, pen = art.drawing()
        foot = HORIZON + 0.06
        for _ in range(16):
            u = rng.uniform(0.0, 1.0)
            w = rng.uniform(0.012, 0.03)
            h = rng.uniform(0.08, 0.22)
            pen.rect(u - w, foot - h, u + w, foot)
            pen.poly([(u - w * 1.2, foot - h), (u + w * 1.2, foot - h), (u, foot - h - w * 2.6)])
        pen.rect(-0.02, foot, 1.02, 1.0)
        # The robot: head, shoulders, an arm out with the hand open.
        ru, rv = 0.80, foot
        pen.rect(ru - 0.07, rv - 0.26, ru + 0.07, rv)
        pen.ellipse(ru, rv - 0.32, 0.05, 0.06)
        pen.ellipse(ru - 0.09, rv - 0.25, 0.04, 0.035)
        pen.line([(ru - 0.10, rv - 0.24), (ru - 0.20, rv - 0.20), (ru - 0.26, rv - 0.26)], 0.022)
        for k in range(4):
            a = math.radians(200 + k * 25)
            pen.line([(ru - 0.26, rv - 0.26), (ru - 0.26 + 0.03 * math.cos(a), rv - 0.26 + 0.03 * math.sin(a))], 0.006)
        body = art.mask_of(image)
        layer = solid(art, body, p["stone_far"], mix(p["stone"], p["haze"], 0.3), HORIZON - 0.3, HORIZON + 0.1, "towers", 0.05)
        art.light(layer, art.rim(body, -0.003, -0.002, 0.5) * body, p["cloud"], 0.3)
        # The robot's eye, lit, and a gear on its head.
        eye, e_pen = art.drawing()
        e_pen.ellipse(ru - 0.015, rv - 0.325, 0.012, 0.006)
        art.put(layer, art.mask_of(eye, blur=0.4), p["lamp"])
        g, g_pen = art.drawing()
        gear(g_pen, ru + 0.012, rv - 0.37, 0.03, 10)
        art.put(layer, art.mask_of(g, blur=0.4), mix(p["brass"], p["haze"], 0.35))
        # The ring and its armillary.
        ring, r_pen = art.drawing()
        cu, cv, r = 0.36, foot - 0.26, 0.17
        r_pen.ring(cu, cv, r, 0.018)
        for k in range(24):
            a = math.tau * k / 24
            r_pen.rect(cu + (r + 0.012) * math.cos(a) - 0.006, cv + (r + 0.012) * math.sin(a) - 0.006,
                       cu + (r + 0.012) * math.cos(a) + 0.006, cv + (r + 0.012) * math.sin(a) + 0.006)
        r_pen.ring(cu, cv, r * 0.5, 0.004)
        r_pen.arc(cu, cv, r * 0.38, 200.0, 520.0, 0.004)
        r_pen.rect(cu - 0.006, cv, cu + 0.006, foot)
        rm = art.mask_of(ring, blur=0.4)
        art.put(layer, rm, mix(p["brass"], p["haze"], 0.25))
        orb, o_pen = art.drawing()
        o_pen.ellipse(cu, cv, 0.03)
        om = art.mask_of(orb, blur=0.5)
        art.put(layer, om, p["lamp"])
        art.light(layer, art.blur(om, 10.0), p["lamp"], 0.5)
        haze(art, layer, p["haze"], 0.25, foot)
        return layer
    if layer_key == "near_background":
        # The aqueduct on its arches with a train on it, the water falling
        # from it onto a wheel; gear towers and trees.
        image, pen = art.drawing()
        deck = 0.52
        pen.rect(-0.02, deck, 1.02, 0.92)
        arches, a_pen = art.drawing()
        for k in range(11):
            u = -0.02 + k * 0.095 + 0.022
            a_pen.ellipse(u + 0.0365, deck + 0.11, 0.0365, 0.05, value=255)
            a_pen.rect(u, deck + 0.11, u + 0.073, 0.92)
        # Gear towers.
        for u, h in ((0.12, 0.30), (0.62, 0.24)):
            pen.rect(u - 0.03, 0.86 - h, u + 0.03, 0.92)
            pen.poly([(u - 0.04, 0.86 - h), (u + 0.04, 0.86 - h), (u, 0.86 - h - 0.06)])
        pen.rect(-0.02, 0.86, 1.02, 1.0)
        body = np.clip(art.mask_of(image) - art.mask_of(arches) * smoothstep(0.92, 0.90, art.v), 0, 1)
        layer = solid(art, body, p["stone"], p["stone_dark"], 0.4, 0.95, "aqueduct", 0.06)
        art.light(layer, art.rim(body, -0.003, -0.002, 0.4) * body, p["cloud"], 0.25)
        # The channel's water on the deck, and the fall onto the wheel.
        water, w_pen = art.drawing()
        w_pen.rect(-0.02, deck - 0.006, 1.02, deck + 0.004)
        w_pen.rect(0.40, deck + 0.035, 0.425, 0.86)
        wm = art.mask_of(water, blur=0.5)
        art.put(layer, wm, p["water"], 0.9)
        art.light(layer, wm * art.noise("fall foam", cells=20.0, octaves=3, stretch=0.2).clip(0.5, 1.0), p["cloud"], 0.4)
        wheel, wh_pen = art.drawing()
        gear(wh_pen, 0.44, 0.80, 0.07, 16, hole=0.0)
        for k in range(8):
            a = math.tau * k / 8
            wh_pen.line([(0.44, 0.80), (0.44 + 0.06 * math.cos(a), 0.80 + 0.06 * math.sin(a))], 0.004, value=0)
        whm = art.mask_of(wheel, blur=0.4)
        art.put(layer, whm, p["brass_dark"])
        art.light(layer, art.rim(whm, -0.003, -0.003, 0.4) * whm, p["brass"], 0.6)
        # Gears on the towers' faces, and their clock lamps.
        gears, g_pen = art.drawing()
        for u, h in ((0.12, 0.30), (0.62, 0.24)):
            gear(g_pen, u, 0.86 - h + 0.06, 0.022, 10)
        art.put(layer, art.mask_of(gears, blur=0.4), p["brass"])
        # The train on the deck: an engine and three cars.
        train, t_pen = art.drawing()
        for k in range(4):
            u = 0.64 + k * 0.05
            t_pen.rect(u, deck - 0.04, u + 0.045, deck - 0.008)
        t_pen.rect(0.64 + 3 * 0.05 + 0.03, deck - 0.06, 0.64 + 3 * 0.05 + 0.04, deck - 0.04)
        tm = art.mask_of(train, blur=0.4)
        art.put(layer, tm, p["train"])
        windows, wi_pen = art.drawing()
        for k in range(3):
            u = 0.645 + k * 0.05
            for j in range(3):
                wi_pen.rect(u + j * 0.013 + 0.002, deck - 0.032, u + j * 0.013 + 0.01, deck - 0.022)
        art.put(layer, art.mask_of(windows, blur=0.3), p["lamp"])
        # Trees in front of the arches.
        trees, tr_pen = art.drawing()
        rng = art.rand("works trees")
        for u in (0.04, 0.27, 0.52, 0.78, 0.95):
            tr_pen.rect(u - 0.004, 0.80, u + 0.004, 0.88)
            for _ in range(5):
                tr_pen.ellipse(u + rng.uniform(-0.03, 0.03), 0.78 + rng.uniform(-0.03, 0.02), rng.uniform(0.02, 0.035))
        trm = art.mask_of(trees, blur=0.6)
        art.put(layer, trm, art.ramp([(0.0, p["leaf"]), (0.74, p["leaf"]), (0.86, p["leaf_dark"]), (1.0, p["leaf_dark"])]))
        art.light(layer, art.rim(trm, -0.004, -0.004, 0.5) * trm, p["cloud"], 0.2)
        lamps(art, layer, [(0.12, 0.62, 0.004), (0.62, 0.68, 0.004)], p["lamp"], halo=4.0, strength=0.6)
        haze(art, layer, p["haze"], 0.12, None)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "works mist", 0.88, 0.08, cells=3.0), p["haze"], 0.25)
    return layer


# ---------------------------------------------------------------------------
# The Life field
# ---------------------------------------------------------------------------


def automaton_life(layer_key: str, art: Art) -> np.ndarray:
    p = LIFE
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.45, p["mid"]), (1.0, p["low"])]))
        rng = art.rand("life stars")
        stars, s_pen = art.drawing()
        for _ in range(200):
            s_pen.ellipse(rng.random(), rng.uniform(0.0, 0.7), rng.uniform(0.0008, 0.002), value=rng.randint(80, 255))
        art.light(layer, art.mask_of(stars, blur=0.4), p["star"], 0.7)
        # The galaxy, high, its arms made of cells.
        cu, cv = 0.40, 0.18
        du, dv = art.u - cu, (art.v - cv) * 2.0
        r = np.hypot(du, dv)
        a = np.arctan2(dv, du)
        arms = (0.5 + 0.5 * np.cos(2.0 * a - r * 34.0)) ** 2
        quant = (np.abs(np.cos(art.u * math.pi * 160.0)) > 0.3) * (np.abs(np.cos(art.v * math.pi * 160.0)) > 0.3)
        spiral = arms * smoothstep(0.2, 0.0, r)
        art.light(layer, spiral * (0.4 + 0.6 * quant), p["galaxy"], 0.8)
        art.light(layer, smoothstep(0.035, 0.0, r), p["galaxy_core"], 0.8)
        art.light(layer, fog(art, "nebula", 0.3, 0.2, cells=3.0) * smoothstep(0.0, 0.4, art.u), p["galaxy"], 0.18)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The floor of cells to the horizon, pillars of cubes on it, and the
        # tower in its ring.
        layer = art.blank()
        horizon = HORIZON + 0.02
        image, pen = art.drawing()
        rng = art.rand("life pillars")
        tops = []
        for _ in range(26):
            u = rng.random()
            w = rng.uniform(0.012, 0.03)
            h = rng.uniform(0.02, 0.10)
            pen.rect(u - w, horizon - h, u + w, horizon + 0.02)
            tops.append((u, horizon - h, w))
        # The tower: cubes stacked, wider at the top.
        tu = 0.68
        pen.rect(tu - 0.025, horizon - 0.34, tu + 0.025, horizon + 0.02)
        pen.rect(tu - 0.06, horizon - 0.46, tu + 0.06, horizon - 0.32)
        pen.rect(-0.02, horizon + 0.02, 1.02, 1.0)
        body = art.mask_of(image)
        layer = solid(art, body, p["cube_light"], p["cube"], horizon - 0.4, horizon + 0.1, "pillars", 0.06)
        # Cell lines on the floor, running off to the horizon.
        lines, l_pen = art.drawing()
        for k in range(-24, 25):
            l_pen.line([(0.5 + k * 0.012, horizon + 0.02), (0.5 + k * 0.14, 1.1)], 0.0012)
        v, step = horizon + 0.02, 0.006
        while v < 1.0:
            l_pen.line([(-0.02, v), (1.02, v)], 0.0012)
            step *= 1.3
            v += step
        art.light(layer, art.mask_of(lines, blur=0.4) * smoothstep(horizon, horizon + 0.2, art.v), p["grid"], 0.5)
        # Lit patterns on the pillars' tops.
        lit, li_pen = art.drawing()
        for u, v, w in tops:
            s = w * 0.5
            cells(li_pen, (GLIDER, BLINKER)[int(u * 100) % 2], u - 1.5 * s, v - 3.4 * s, s, 0.3)
        lm = art.mask_of(lit, blur=0.4)
        art.put(layer, lm, p["cell"], 0.85)
        art.light(layer, art.blur(lm, 3.0), p["cell"], 0.4)
        # The tower's faces lit, and the ring round it.
        face, f_pen = art.drawing()
        cells(f_pen, ("10101", "01010", "10101", "01010", "10101"), tu - 0.05, horizon - 0.45, 0.02, 0.3)
        art.put(layer, art.mask_of(face, blur=0.4), p["cell"], 0.8)
        ring, r_pen = art.drawing()
        r_pen.line([(tu + 0.13 * math.cos(math.tau * k / 64), horizon - 0.33 + 0.026 * math.sin(math.tau * k / 64)) for k in range(65)], 0.005)
        ring_m = art.mask_of(ring, blur=0.5)
        art.put(layer, ring_m, p["amber"])
        art.light(layer, art.blur(ring_m, 5.0), p["amber"], 0.6)
        beam, b_pen = art.drawing()
        b_pen.rect(tu - 0.008, horizon - 0.32, tu + 0.008, horizon + 0.02)
        art.light(layer, art.mask_of(beam, blur=4.0), p["cell"], 0.5)
        haze(art, layer, p["haze"], 0.2, horizon)
        return layer
    if layer_key == "near_background":
        # Panels in the air showing the patterns of the rule.
        layer = art.blank()
        frames, f_pen = art.drawing()
        panels = ((0.04, 0.10, 0.16, 0.12), (0.74, 0.06, 0.20, 0.16), (0.34, 0.30, 0.10, 0.10))
        for u, v, w, h in panels:
            f_pen.rect(u, v, u + w, v + h)
        fm = art.mask_of(frames, blur=0.4)
        art.put(layer, fm, mix(p["cube"], p["top"], 0.3), 0.92)
        edges, e_pen = art.drawing()
        for u, v, w, h in panels:
            e_pen.line([(u, v), (u + w, v), (u + w, v + h), (u, v + h), (u, v)], 0.003)
        art.put(layer, art.mask_of(edges, blur=0.4), p["amber"], 0.9)
        lit, l_pen = art.drawing()
        # The glider in its four phases, west panel.
        phases = (GLIDER, ("101", "011", "010"), ("001", "101", "011"), ("100", "011", "110"))
        for k, ph in enumerate(phases):
            cells(l_pen, ph, 0.05 + k * 0.038, 0.13 + (k % 2) * 0.01, 0.01)
        # A Sierpinski triangle (rule 90), east panel.
        tri = sierpinski(16)
        cells(l_pen, tri, 0.75, 0.075, 0.0058, 0.2)
        # A spaceship, the small panel.
        cells(l_pen, SPACESHIP, 0.355, 0.325, 0.014)
        lm = art.mask_of(lit, blur=0.4)
        art.put(layer, lm, p["cell"])
        art.light(layer, art.blur(lm, 3.0), p["cell"], 0.5)
        # Chains of cubes up out of sight, holding the panels.
        chains, c_pen = art.drawing()
        for u, v, w, h in panels:
            for x in (u + w * 0.2, u + w * 0.8):
                for k in range(int(v / 0.02) + 1):
                    c_pen.rect(x - 0.003, v - (k + 1) * 0.02 + 0.004, x + 0.003, v - k * 0.02)
        art.put(layer, art.mask_of(chains, blur=0.3), p["cube_light"])
        # Near pillars at the edges, with their lit tops.
        image, pen = art.drawing()
        for u, top in ((0.08, 0.72), (0.92, 0.66)):
            pen.rect(u - 0.05, top, u + 0.05, 1.0)
        body = art.mask_of(image)
        art.put(layer, body, art.ramp([(0.0, p["cube_light"]), (0.7, p["cube_light"]), (1.0, p["cube"])]))
        grid = (smoothstep(0.93, 0.99, np.abs(np.cos(art.u * math.pi * 50.0))) + smoothstep(0.93, 0.99, np.abs(np.cos(art.v * math.pi * 50.0)))).clip(0, 1)
        art.shade(layer, grid * body, 0.35)
        tops, t_pen = art.drawing()
        for u, top in ((0.08, 0.72), (0.92, 0.66)):
            t_pen.rect(u - 0.05, top, u + 0.05, top + 0.006)
        art.put(layer, art.mask_of(tops, blur=0.4), p["amber"])
        haze(art, layer, p["haze"], 0.18, None)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "life mist", 0.9, 0.08, cells=3.0), p["galaxy"], 0.12)
    return layer


#: Gosper's glider gun (1970): the first pattern found to grow without end.
#: It fires a glider every thirty generations. The arena's screen shows it.
GOSPER_GUN = (
    "000000000000000000000000100000000000",
    "000000000000000000000010100000000000",
    "000000000000110000001100000000000011",
    "000000000001000100001100000000000011",
    "110000000010000010001100000000000000",
    "110000000010001011000010100000000000",
    "000000000010000010000000100000000000",
    "000000000001000100000000000000000000",
    "000000000000110000000000000000000000",
)

#: The two gliders the gun has fired by generation 120, in its cells (the
#: rule run from `GOSPER_GUN`: one leaves every thirty generations, going
#: down and right).
FIRED = ((30, 17), (31, 18), (31, 19), (32, 17), (32, 18), (38, 24), (38, 26), (39, 25), (39, 26), (40, 25))


def automaton_arena(layer_key: str, art: Art) -> np.ndarray:
    """The Cell-ular Arena: the Life field's night, and round it a bowl of
    stands made of cubes, the crowd a scatter of lit cells that blink; light
    pylons at the sides throw beams up; over the ring a great screen hangs on
    chains of cubes, Gosper's glider gun on it, firing."""
    p = LIFE
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.5, p["mid"]), (1.0, p["low"])]))
        rng = art.rand("arena stars")
        stars, s_pen = art.drawing()
        for _ in range(120):
            s_pen.ellipse(rng.random(), rng.uniform(0.0, 0.5), rng.uniform(0.0008, 0.0018), value=rng.randint(80, 255))
        art.light(layer, art.mask_of(stars, blur=0.4), p["star"], 0.6)
        # The pylons' beams, crossing high over the ring.
        beams, b_pen = art.drawing()
        for u0, u1 in ((0.04, 0.30), (0.10, 0.46), (0.96, 0.70), (0.90, 0.54)):
            b_pen.poly([(u0 - 0.006, HORIZON - 0.18), (u0 + 0.006, HORIZON - 0.18), (u1 + 0.04, -0.05), (u1 - 0.04, -0.05)])
        art.light(layer, art.mask_of(beams, blur=6.0) * smoothstep(-0.05, HORIZON, art.v), p["cell"], 0.22)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The bowl: tier on tier of cube stands, curving round behind the ring.
        layer = art.blank()
        foot = HORIZON + 0.06
        image, pen = art.drawing()
        rows = 7
        for r in range(rows):
            top = foot - 0.05 - r * 0.045
            sag = 0.03 + r * 0.008
            pts = [(u, top + sag * (1.0 - (2.0 * u - 1.0) ** 2)) for u in np.linspace(-0.02, 1.02, 40)]
            pen.poly(pts + [(1.02, 1.0), (-0.02, 1.0)])
        body = art.mask_of(image)
        layer = solid(art, body, p["cube_light"], p["cube"], foot - 0.4, foot, "stands", 0.05)
        # Each tier's lip, lit amber.
        lips, l_pen = art.drawing()
        for r in range(rows):
            top = foot - 0.05 - r * 0.045
            sag = 0.03 + r * 0.008
            l_pen.line([(u, top + sag * (1.0 - (2.0 * u - 1.0) ** 2)) for u in np.linspace(-0.02, 1.02, 40)], 0.0022)
        lm = art.mask_of(lips, blur=0.4)
        art.put(layer, lm, p["amber"], 0.7)
        # The crowd: lit cells on the tiers, some in blinkers.
        rng = art.rand("arena crowd")
        crowd, c_pen = art.drawing()
        for r in range(rows):
            top = foot - 0.05 - r * 0.045
            sag = 0.03 + r * 0.008
            for _ in range(70):
                u = rng.random()
                v = top + sag * (1.0 - (2.0 * u - 1.0) ** 2) + 0.012
                s = 0.006 - r * 0.0004
                if rng.random() < 0.2:
                    cells(c_pen, BLINKER if rng.random() < 0.5 else ("111",), u, v - 0.02, s * 0.8, 0.3)
                else:
                    c_pen.rect(u, v, u + s, v + s)
        cm = art.mask_of(crowd, blur=0.4)
        art.put(layer, cm, p["cell"], 0.9)
        art.light(layer, art.blur(cm, 3.0), p["cell"], 0.35)
        # The arena floor in front of the stands, its cell lines.
        floor, f_pen = art.drawing()
        f_pen.rect(-0.02, foot, 1.02, 1.0)
        art.put(layer, art.mask_of(floor), p["cube"])
        lines, g_pen = art.drawing()
        for k in range(-30, 31):
            g_pen.line([(0.5 + k * 0.02, foot), (0.5 + k * 0.12, 1.1)], 0.0012)
        v, step = foot, 0.008
        while v < 1.0:
            g_pen.line([(-0.02, v), (1.02, v)], 0.0012)
            step *= 1.3
            v += step
        art.light(layer, art.mask_of(lines, blur=0.4) * smoothstep(foot, foot + 0.2, art.v), p["grid"], 0.5)
        haze(art, layer, p["haze"], 0.18, foot)
        return layer
    if layer_key == "near_background":
        layer = art.blank()
        # The pylons at the sides, their lamp heads.
        image, pen = art.drawing()
        for u in (0.16, 0.84):
            pen.rect(u - 0.012, HORIZON - 0.18, u + 0.012, 1.0)
            pen.rect(u - 0.04, HORIZON - 0.22, u + 0.04, HORIZON - 0.17)
        body = art.mask_of(image)
        art.put(layer, body, art.ramp([(0.0, p["cube_light"]), (0.8, p["cube"]), (1.0, p["cube"])]))
        heads, h_pen = art.drawing()
        for u in (0.16, 0.84):
            for k in range(4):
                h_pen.rect(u - 0.034 + k * 0.018, HORIZON - 0.214, u - 0.022 + k * 0.018, HORIZON - 0.18)
        hm = art.mask_of(heads, blur=0.4)
        art.put(layer, hm, p["cell"])
        art.light(layer, art.blur(hm, 6.0), p["cell"], 0.6)
        # The screen over the ring, on chains of cubes.
        # Low on the panel: the near layer is larger than the view, so its
        # top is above the room's top.
        su0, sv0, su1, sv1 = 0.32, 0.30, 0.68, 0.51
        screen, sc_pen = art.drawing()
        sc_pen.rect(su0, sv0, su1, sv1)
        art.put(layer, art.mask_of(screen, blur=0.4), mix(p["cube"], p["top"], 0.4), 0.95)
        edge, e_pen = art.drawing()
        e_pen.line([(su0, sv0), (su1, sv0), (su1, sv1), (su0, sv1), (su0, sv0)], 0.003)
        art.put(layer, art.mask_of(edge, blur=0.4), p["amber"], 0.9)
        chains, ch_pen = art.drawing()
        for x in (su0 + 0.04, su1 - 0.04):
            for k in range(int(sv0 / 0.02) + 1):
                ch_pen.rect(x - 0.003, sv0 - (k + 1) * 0.02 + 0.004, x + 0.003, sv0 - k * 0.02)
        art.put(layer, art.mask_of(chains, blur=0.3), p["cube_light"])
        # Gosper's gun on it, and the gliders it has fired going down-right.
        lit, li_pen = art.drawing()
        s = 0.007
        gu, gv = su0 + 0.035, sv0 + 0.008
        cells(li_pen, GOSPER_GUN, gu, gv, s, 0.2)
        for x, y in FIRED:
            li_pen.rect(gu + (x + 0.1) * s, gv + (y + 0.1) * s, gu + (x + 0.9) * s, gv + (y + 0.9) * s)
        lm = art.mask_of(lit, blur=0.4)
        art.put(layer, lm, p["cell"])
        art.light(layer, art.blur(lm, 3.0), p["cell"], 0.5)
        # Banners down from the screen's corners, a glider on each.
        flags, fl_pen = art.drawing()
        for u in (su0 - 0.06, su1 + 0.02):
            fl_pen.poly([(u, sv0), (u + 0.04, sv0), (u + 0.04, sv0 + 0.16), (u + 0.02, sv0 + 0.13), (u, sv0 + 0.16)])
        art.put(layer, art.mask_of(flags, blur=0.4), mix(p["galaxy"], p["cube"], 0.4), 0.95)
        marks, m_pen = art.drawing()
        for u in (su0 - 0.06, su1 + 0.02):
            cells(m_pen, GLIDER, u + 0.008, sv0 + 0.03, 0.008, 0.25)
        art.put(layer, art.mask_of(marks, blur=0.4), p["amber"])
        haze(art, layer, p["haze"], 0.12, None)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "arena mist", 0.9, 0.08, cells=3.0), p["galaxy"], 0.12)
    return layer


# ---------------------------------------------------------------------------
# Inside the clock tower
# ---------------------------------------------------------------------------

TOWER = {
    "wall_top": (70, 60, 96),
    "wall": (126, 110, 150),
    "wall_low": (150, 124, 140),
    "mortar": (60, 50, 80),
    "glass": (255, 226, 160),
    "glass_edge": (214, 170, 92),
    "brass": (196, 150, 80),
    "brass_dark": (120, 86, 50),
    "beam": (96, 64, 46),
    "chain": (70, 62, 84),
    "light": (255, 220, 160),
    "haze": (110, 96, 130),
}


def automaton_tower(layer_key: str, art: Art) -> np.ndarray:
    p = TOWER
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["wall_top"]), (0.5, p["wall"]), (1.0, p["wall_low"])]))
        # Courses of stone.
        rows = smoothstep(0.93, 0.99, np.abs(np.cos(art.v * math.pi * 18.0)))
        stagger = np.floor(art.v * 18.0) % 2
        cols = smoothstep(0.96, 0.995, np.abs(np.cos((art.u + stagger * 0.025) * math.pi * 20.0))) * (1.0 - rows)
        art.put(layer, np.clip(rows + cols, 0, 1), p["mortar"], 0.4)
        art.grain(layer, "stone grain", 2.0)
        # The back of the clock face: a disc of lit glass, the shadows of
        # its hands and its ring of hour marks.
        cu, cv, r = 0.5, 0.3, 0.2
        d = np.hypot(art.u - cu, art.v - cv)
        disc = smoothstep(r, r - 0.004, d)
        art.put(layer, disc, art.ramp([(cv - r, p["glass"]), (cv + r, mix(p["glass"], p["glass_edge"], 0.5))]), 0.95)
        art.put(layer, smoothstep(0.012, 0.004, np.abs(d - r)), p["brass_dark"])
        marks, m_pen = art.drawing()
        for k in range(12):
            a = math.tau * k / 12
            m_pen.ellipse(cu + (r - 0.025) * math.cos(a), cv + (r - 0.025) * math.sin(a), 0.008)
        hands, h_pen = art.drawing()
        h_pen.line([(cu, cv), (cu - 0.12, cv - 0.07)], 0.012)
        h_pen.line([(cu, cv), (cu + 0.03, cv - 0.16)], 0.008)
        h_pen.ellipse(cu, cv, 0.02)
        art.put(layer, art.mask_of(marks, blur=0.4) * disc, p["brass_dark"], 0.8)
        art.put(layer, art.mask_of(hands, blur=1.0) * disc, p["brass_dark"], 0.7)
        # Its light falling across the room.
        art.light(layer, art.spot(cu, cv + 0.25, 0.5, 2.0, 0.7) * (1.0 - disc), p["light"], 0.3)
        return layer
    if layer_key == "far_backplate":
        # Brass gears behind, on their shafts.
        image, pen = art.drawing()
        for u, v, r, n in ((0.12, 0.62, 0.14, 18), (0.86, 0.56, 0.17, 20), (0.30, 0.86, 0.09, 12), (0.70, 0.88, 0.1, 14)):
            gear(pen, u, v, r, n, hole=0.25)
        body = art.mask_of(image)
        layer = solid(art, body, p["brass"], p["brass_dark"], 0.4, 1.0, "gears", 0.05)
        art.shade(layer, art.rim(body, 0.0, 0.006, 0.4) * body, 0.3)
        art.light(layer, art.rim(body, -0.004, -0.004, 0.4) * body, p["light"], 0.4)
        haze(art, layer, p["haze"], 0.3, None)
        return layer
    if layer_key == "near_background":
        # Beams across, chains and the pendulum hanging.
        image, pen = art.drawing()
        pen.rect(-0.02, 0.06, 1.02, 0.1)
        for u in (0.04, 0.96):
            pen.rect(u - 0.025, 0.06, u + 0.025, 1.0)
        pen.poly([(0.04, 0.1), (0.12, 0.1), (0.04, 0.22)])
        pen.poly([(0.96, 0.1), (0.88, 0.1), (0.96, 0.22)])
        body = art.mask_of(image)
        layer = solid(art, body, p["beam"], scale_rgb(p["beam"], 0.7), 0.1, 0.9, "beams", 0.12)
        chains, c_pen = art.drawing()
        for u, length in ((0.22, 0.42), (0.78, 0.36)):
            for k in range(int(length / 0.02)):
                c_pen.ring(u, 0.11 + k * 0.02, 0.006, 0.0025)
            c_pen.rect(u - 0.02, 0.11 + length, u + 0.02, 0.15 + length)
        # The pendulum: a rod from the beam and a brass bob.
        c_pen.rect(0.638, 0.1, 0.646, 0.62)
        art.put(layer, art.mask_of(chains, blur=0.4), p["chain"])
        bob, b_pen = art.drawing()
        b_pen.ellipse(0.642, 0.66, 0.045)
        bm = art.mask_of(bob, blur=0.4)
        art.put(layer, bm, p["brass"])
        art.light(layer, art.rim(bm, -0.01, -0.01, 0.5) * bm, p["light"], 0.5)
        haze(art, layer, p["haze"], 0.08, None)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "tower dust", 0.5, 0.3, cells=3.0), p["light"], 0.1)
    return layer


def scale_rgb(c, k):
    return tuple(int(min(255, x * k)) for x in c)


# ---------------------------------------------------------------------------
# Foregrounds
# ---------------------------------------------------------------------------


def automaton_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A gear's edge from below, and a lamp post."""
    gear(pen, 0.12, 0.74, 0.07, 14, hole=0.5)
    pen.rect(0.86, 0.50, 0.866, 0.72)
    pen.rect(0.85, 0.48, 0.876, 0.505)


def life_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """Cubes from below, a cell's corner."""
    for k in range(3):
        pen.rect(0.80 + k * 0.05, 0.70 - (k % 2) * 0.03, 0.845 + k * 0.05, 0.75)
    pen.rect(0.06, 0.32, 0.10, 0.36)


def tower_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A gear's teeth from below, and a hanging chain's end."""
    gear(pen, 0.9, 0.76, 0.08, 16, hole=0.4)
    pen.rect(0.06, 0.0, 0.066, 0.3)
