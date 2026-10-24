"""The scene of the village of the ninja dimension.

A mountain village at dusk. The sky goes from indigo to the rose of the
evening, over ranges of blue-green mountains with mist between them. In
the valley stand farmhouses with heavy tiled roofs, white plaster and dark
timber, a pagoda on the hill above them, and maples red in the autumn. Near
the play: the eave of a house with a paper lantern lit under it, the branch
of a maple, and a low fence of bamboo. It is a quiet, lived-in place; the
`forest` scene is the wild bamboo grove.
"""

from __future__ import annotations

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import HORIZON, cloud_mask, fog, haze, lamps, pine, solid

VILLAGE = {
    "top": (40, 44, 88),
    "mid": (110, 94, 142),
    "low": (238, 164, 124),
    "glow": (255, 206, 156),
    "range_far": (150, 140, 170),
    "range_near": (74, 98, 116),
    "mist": (196, 178, 196),
    "plaster": (232, 226, 210),
    "timber": (58, 42, 36),
    "tile": (64, 70, 86),
    "cedar": (40, 62, 64),
    "maple": (196, 62, 44),
    "maple_light": (236, 112, 64),
    "near": (34, 30, 42),
    "near_light": (110, 84, 92),
    "lantern": (255, 176, 96),
}


def _eave(pen: Pen, u0: float, u1: float, v: float, lift: float, thick: float) -> None:
    """A roof edge from `u0` to `u1` at `v` whose ends turn up by `lift`."""
    n = 16
    top = [(u0 + (u1 - u0) * i / n, v - lift * (abs(2.0 * i / n - 1.0) ** 3)) for i in range(n + 1)]
    pen.poly(top + [(x, y + thick) for x, y in reversed(top)])


def _minka(walls: Pen, roofs: Pen, timber: Pen, windows: Pen, rng, u: float, foot: float, w: float, h: float) -> None:
    """A farmhouse: a white wall in a frame of dark timber, and a heavy roof
    of tiles in two steps (a hip below, a small gable over it)."""
    top = foot - h
    walls.rect(u, top, u + w, foot + 0.01)
    for k in range(4):
        x = u + w * k / 3.0
        timber.rect(x - w * 0.02, top, x + w * 0.02, foot)
    timber.rect(u, top + h * 0.45, u + w, top + h * 0.50)
    if rng.random() < 0.7:
        windows.rect(u + w * 0.40, top + h * 0.15, u + w * 0.60, top + h * 0.40)
    over = w * 0.18
    roof_h = w * 0.52
    roofs.poly([(u - over, top + 0.003), (u + w + over, top + 0.003), (u + w * 0.82, top - roof_h * 0.7), (u + w * 0.18, top - roof_h * 0.7)])
    _eave(roofs, u - over, u + w + over, top + 0.003, w * 0.06, w * 0.05)
    roofs.poly([(u + w * 0.28, top - roof_h * 0.68), (u + w * 0.72, top - roof_h * 0.68), (u + w * 0.5, top - roof_h * 1.15)])
    roofs.rect(u + w * 0.26, top - roof_h * 0.74, u + w * 0.74, top - roof_h * 0.66)


def _pagoda(pen: Pen, cu: float, base: float, w: float, tiers: int = 5) -> list:
    """A pagoda standing on `base`: `tiers` floors, each with a roof whose
    corners turn up, each smaller than the one below. Returns where its
    lamps hang."""
    lights = []
    v = base
    for k in range(tiers):
        half = w * (1.0 - k * 0.12) * 0.5
        storey = w * 0.30
        pen.rect(cu - half * 0.62, v - storey, cu + half * 0.62, v)
        _eave(pen, cu - half * 1.25, cu + half * 1.25, v - storey, w * 0.06, w * 0.05)
        pen.poly([(cu - half * 1.15, v - storey + 0.001), (cu + half * 1.15, v - storey + 0.001), (cu + half * 0.6, v - storey - w * 0.12), (cu - half * 0.6, v - storey - w * 0.12)])
        lights.append((cu, v - storey * 0.45, w * 0.03))
        v -= storey + w * 0.12
    pen.rect(cu - w * 0.015, v - w * 0.45, cu + w * 0.015, v + 0.002)
    for j in range(5):
        pen.ellipse(cu, v - w * (0.08 + j * 0.07), w * 0.035, w * 0.012)
    return lights


def _maple(pen: Pen, crown: Pen, rng, u: float, foot: float, h: float) -> None:
    """A maple: a short trunk that forks, and a round crown of lumps."""
    pen.poly([(u - h * 0.05, foot), (u + h * 0.05, foot), (u + h * 0.03, foot - h * 0.5), (u - h * 0.03, foot - h * 0.5)])
    pen.line([(u, foot - h * 0.45), (u - h * 0.18, foot - h * 0.75)], h * 0.03)
    pen.line([(u, foot - h * 0.45), (u + h * 0.2, foot - h * 0.7)], h * 0.03)
    for _ in range(9):
        crown.ellipse(u + rng.uniform(-0.32, 0.32) * h, foot - h * rng.uniform(0.62, 0.95), h * rng.uniform(0.14, 0.22))


def ninja_village(layer_key: str, art: Art) -> np.ndarray:
    p = VILLAGE
    glow_at = (0.56, HORIZON - 0.06)
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.30, p["mid"]), (HORIZON - 0.08, mix(p["mid"], p["low"], 0.7)), (HORIZON, p["low"]), (0.75, mix(p["low"], p["range_near"], 0.6)), (1.0, p["range_near"])]))
        art.light(layer, art.spot(*glow_at, 0.45, 1.8, squash=1.6), p["glow"], 0.50)
        # Long thin clouds lit from below by the evening.
        streaks = cloud_mask(art, "evening streaks", 0.36, 0.08, cells=3.0, cover=0.40, soft=0.25, stretch=6.0)
        art.tint(layer, streaks, mix(p["mid"], p["low"], 0.45), 0.55)
        art.light(layer, np.clip(streaks - art.shift(streaks, 0.0, -0.006), 0, 1), p["glow"], 0.40)
        # Ranges of mountains, each paler and more violet the further it is,
        # with mist in the valleys between them.
        for tag, base, amp, colour, amount in (
            ("range far", HORIZON - 0.06, 0.09, mix(p["range_far"], p["low"], 0.30), 0.85),
            ("range mid", HORIZON - 0.02, 0.07, mix(p["range_far"], p["range_near"], 0.45), 0.92),
            ("range near", HORIZON + 0.03, 0.05, p["range_near"], 1.0),
        ):
            hills, line = art.ridge(tag, base, amp, cells=3.0, octaves=5, sharp=0.55)
            art.tint(layer, hills, colour, amount)
            art.light(layer, art.rim(hills, 0.004, 0.0, 0.6) * hills, p["glow"], 0.25)
            art.tint(layer, fog(art, (tag, "mist"), base + 0.05, 0.05), p["mist"], 0.55)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("village")
        ground, line = art.ridge("valley floor", HORIZON + 0.03, 0.015, cells=3.0, octaves=3)
        # The hill of the pagoda, on the left.
        hill, hill_line = art.ridge("pagoda hill", HORIZON - 0.03, 0.03, cells=1.5, octaves=3)
        hill = hill * smoothstep(0.42, 0.30, art.u)
        trees, tree_pen = art.drawing()
        for _ in range(26):
            u = rng.uniform(0.0, 0.40)
            v = float(np.minimum(hill_line, line)[min(art.n - 1, int(u * art.n))])
            if u > 0.36:
                v = float(line[int(u * art.n)])
            h = rng.uniform(0.04, 0.08)
            pine(tree_pen, u, v + 0.006, h, h * 0.40, tiers=rng.randint(4, 6))
        pag, pag_pen = art.drawing()
        pu = 0.20
        lights = _pagoda(pag_pen, pu, float(hill_line[int(pu * art.n)]) + 0.004, 0.05)
        walls, wall_pen = art.drawing()
        roofs, roof_pen = art.drawing()
        beams, beam_pen = art.drawing()
        wins, win_pen = art.drawing()
        maples, maple_pen = art.drawing()
        crowns, crown_pen = art.drawing()
        u = 0.30
        while u < 1.02:
            w = rng.uniform(0.045, 0.07)
            foot = float(line[min(art.n - 1, int((u + w * 0.5) * art.n))]) + 0.008
            if rng.random() < 0.25:
                _maple(maple_pen, crown_pen, rng, u + w * 0.4, foot, rng.uniform(0.05, 0.07))
                u += w * 0.7
                continue
            _minka(wall_pen, roof_pen, beam_pen, win_pen, rng, u, foot, w, w * rng.uniform(0.32, 0.42))
            u += w * rng.uniform(1.25, 1.6)
        body = np.clip(np.maximum.reduce([ground, hill, art.mask_of(trees), art.mask_of(pag), art.mask_of(walls), art.mask_of(roofs), art.mask_of(maples), art.mask_of(crowns)]), 0, 1)
        air = mix(p["mid"], p["low"], 0.55)
        layer = solid(art, np.maximum(ground, hill), mix(p["cedar"], air, 0.40), mix(p["cedar"], air, 0.25), HORIZON - 0.1, HORIZON + 0.05, "valley", 0.08)
        art.put(layer, art.mask_of(trees), mix(p["cedar"], air, 0.35))
        art.put(layer, art.mask_of(pag), mix(p["timber"], air, 0.40))
        art.put(layer, art.mask_of(walls), mix(p["plaster"], air, 0.50))
        art.put(layer, art.mask_of(beams) * art.mask_of(walls), mix(p["timber"], air, 0.35))
        art.put(layer, art.mask_of(roofs), mix(p["tile"], air, 0.22))
        art.put(layer, art.mask_of(maples), mix(p["timber"], air, 0.40))
        art.put(layer, art.mask_of(crowns), mix(p["maple"], air, 0.25))
        art.light(layer, art.rim(body, 0.0, 0.003, 0.5) * body, p["glow"], 0.30)
        art.put(layer, art.mask_of(wins) * art.mask_of(walls), mix(p["lantern"], p["plaster"], 0.25), 0.9)
        lamps(art, layer, lights, p["lantern"], halo=4.0, strength=0.7)
        haze(art, layer, p["mist"], 0.12, HORIZON + 0.05)
        return layer
    if layer_key == "near_background":
        rng = art.rand("near village")
        image, pen = art.drawing()
        crown, crown_pen = art.drawing()
        paper, paper_pen = art.drawing()
        # The ground and a low fence of bamboo along it.
        pen.rect(0.0, 0.715, 1.0, 1.0)
        for k in range(46):
            u = 0.30 + k * 0.012
            pen.rect(u - 0.0025, 0.665, u + 0.0025, 0.715)
        pen.rect(0.29, 0.675, 0.86, 0.68)
        pen.rect(0.29, 0.70, 0.86, 0.705)
        # The corner of a house on the right: posts, a deep eave, a lantern.
        pen.rect(0.79, 0.42, 0.92, 0.72)
        pen.rect(0.77, 0.42, 0.785, 0.72)
        _eave(pen, 0.70, 0.95, 0.38, 0.03, 0.028)
        pen.poly([(0.72, 0.39), (0.95, 0.39), (0.95, 0.31), (0.80, 0.31)])
        pen.line([(0.745, 0.40), (0.745, 0.44)], 0.0016)
        paper_pen.ellipse(0.745, 0.465, 0.013, 0.023)
        pen.rect(0.736, 0.439, 0.754, 0.445)
        pen.rect(0.736, 0.485, 0.754, 0.491)
        # A maple on the left: its trunk, and a branch over the path.
        pen.poly([(0.15, 0.72), (0.21, 0.72), (0.195, 0.40), (0.18, 0.0), (0.155, 0.0), (0.165, 0.40)])
        pen.line([(0.185, 0.42), (0.27, 0.33), (0.40, 0.30)], 0.008)
        pen.line([(0.25, 0.35), (0.31, 0.40)], 0.004)
        # Leaves of the maple: small hands of five points in thick clumps.
        clumps = [(0.20, 0.22), (0.27, 0.28), (0.34, 0.27), (0.40, 0.29), (0.15, 0.30), (0.24, 0.17)]
        for _ in range(520):
            cu0, cv0 = clumps[rng.randrange(len(clumps))]
            cu, cv = cu0 + rng.gauss(0.0, 0.025), cv0 + rng.gauss(0.0, 0.018)
            r = rng.uniform(0.005, 0.010)
            a0 = rng.uniform(0, 72)
            pts = []
            for k in range(10):
                ang = np.radians(a0 + k * 36)
                rr = r if k % 2 == 0 else r * 0.5
                pts.append((cu + np.cos(ang) * rr, cv + np.sin(ang) * rr))
            crown_pen.poly(pts)
        crown_mask = art.mask_of(crown) * smoothstep(0.40, 0.34, art.v)
        mask = art.mask_of(image)
        layer = solid(art, mask, mix(p["near"], p["near_light"], 0.35), scale(p["near"], 0.85), 0.25, 0.75, "cedar", 0.10)
        art.put(layer, crown_mask, mix(p["maple"], p["near"], 0.35))
        art.light(layer, crown_mask * art.noise("leaf light", cells=14.0, octaves=2), p["maple_light"], 0.35)
        body = np.maximum(mask, crown_mask)
        art.light(layer, art.rim(body, 0.0, 0.003, 0.4) * body, p["glow"], 0.35)
        art.put(layer, art.mask_of(paper), mix(p["lantern"], (255, 240, 220), 0.3))
        lamps(art, layer, [(0.745, 0.465, 0.01)], p["lantern"], halo=6.0, strength=0.9)
        haze(art, layer, mix(p["mid"], p["low"], 0.4), 0.10, 0.74)
        return layer
    # The air: mist low in the valley, and the glow of the evening.
    layer = art.blank()
    art.put(layer, fog(art, "valley mist", 0.66, 0.08), p["mist"], 0.18)
    art.put(layer, art.spot(*glow_at, 0.40, 2.0, squash=1.6), p["glow"], 0.08)
    return layer
