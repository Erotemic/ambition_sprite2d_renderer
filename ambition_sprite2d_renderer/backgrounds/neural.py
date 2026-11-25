"""The scenes of the Neural dimension, both biological and artificial (gate
address LATENT, `docs/planning/game/neural-dimension.md`).

`neural`: the Cortex, the living half. Indigo air full of neurons: glowing
cell bodies with their dendrites reaching out, sparks running along the
axons between them. Far off the Neural Cathedral, a tree of a brain on its
stem, with a ring of memories (frames, each a little picture of a place)
turning round it. Nearer, arches of pink membrane full of round holes, with
drops of glowing fluid hanging from them; under it all, pools of teal fluid.

`neural_circuit`: the Weights, the artificial half. Navy dark crossed by
the cyan traces of a circuit board; the layers of a network hung in the air,
node to node; racks of memory with their lights blinking; a cold violet
glow from under the floor.

Nothing on a backdrop is writing (the game draws some backdrops mirrored).
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import HORIZON, fog, haze, lamps, solid

CORTEX = {
    "top": (18, 14, 52),
    "high": (40, 28, 96),
    "mid": (90, 50, 140),
    "low": (150, 80, 160),
    "haze": (120, 80, 170),
    "neuron": (255, 150, 210),
    "spark": (255, 236, 170),
    "membrane": (200, 96, 150),
    "membrane_light": (255, 170, 200),
    "membrane_dark": (96, 40, 88),
    "fluid": (90, 236, 220),
    "frame": (150, 210, 255),
    "tree": (176, 110, 190),
}

CIRCUIT = {
    "top": (6, 10, 30),
    "mid": (16, 26, 64),
    "low": (40, 40, 104),
    "haze": (60, 64, 140),
    "trace": (70, 200, 255),
    "trace_dim": (40, 90, 160),
    "node": (150, 240, 255),
    "violet": (170, 90, 255),
    "rack": (24, 28, 56),
    "rack_light": (60, 70, 120),
    "led": (110, 255, 200),
    "led_warm": (255, 170, 80),
    "warn": (255, 70, 90),
}


def _cells(art: Art, tag: object, count: int, v0: float, v1: float) -> tuple[np.ndarray, np.ndarray]:
    """A lattice of cells (Voronoi): returns (edge, inside), each 0..1. The
    edge is near 1 on the walls between two cells; `inside` is the distance
    to the nearest centre, 0 at a centre."""
    rng = art.rand(tag)
    pts = np.array([(rng.random(), rng.uniform(v0, v1)) for _ in range(count)], dtype=np.float32)
    u, v = art.u, art.v
    d1 = np.full(u.shape, 9.0, dtype=np.float32)
    d2 = np.full(u.shape, 9.0, dtype=np.float32)
    for pu, pv in pts:
        du = np.minimum(np.abs(u - pu), 1.0 - np.abs(u - pu))
        d = np.sqrt(du * du + (v - pv) ** 2)
        d2 = np.where(d < d1, d1, np.minimum(d2, d))
        d1 = np.minimum(d1, d)
    return (d2 - d1).astype(np.float32), d1


def _neuron(pen: Pen, rng, u: float, v: float, r: float, arms: int) -> list[tuple[float, float]]:
    """A neuron: its body and its dendrites, each forking once. Returns the
    tips of its dendrites."""
    pen.ellipse(u, v, r, r * 0.85)
    tips = []
    for k in range(arms):
        a = math.tau * k / arms + rng.uniform(-0.4, 0.4)
        length = r * rng.uniform(4.0, 7.0)
        mid = (u + math.cos(a) * length * 0.5, v + math.sin(a) * length * 0.5)
        end = (u + math.cos(a) * length, v + math.sin(a) * length)
        pen.line([(u, v), mid, end], r * 0.22)
        for fork in (-0.5, 0.5):
            b = a + fork
            tip = (mid[0] + math.cos(b) * length * 0.45, mid[1] + math.sin(b) * length * 0.45)
            pen.line([mid, tip], r * 0.12)
            tips.append(tip)
        tips.append(end)
    return tips


def neural(layer_key: str, art: Art) -> np.ndarray:
    p = CORTEX
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.30, p["high"]), (HORIZON - 0.04, p["mid"]), (HORIZON + 0.1, p["low"]), (1.0, p["mid"])]))
        art.light(layer, art.spot(0.5, HORIZON - 0.1, 0.6, 1.8), p["low"], 0.35)
        # The far network: neurons and the axons between them, firing.
        rng = art.rand("far neurons")
        net, pen = art.drawing()
        bodies = []
        for _ in range(16):
            u, v = rng.random(), rng.uniform(0.12, HORIZON - 0.05)
            _neuron(pen, rng, u, v, rng.uniform(0.006, 0.011), rng.randint(4, 6))
            bodies.append((u, v))
        axons, ax_pen = art.drawing()
        sparks, sp_pen = art.drawing()
        for k in range(len(bodies) - 1):
            a, b = bodies[k], bodies[k + 1]
            ax_pen.curve(a, b, rng.uniform(-0.05, 0.05), 0.0012)
            t = rng.uniform(0.2, 0.8)
            sp_pen.ellipse(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 0.0025)
        net_mask = art.mask_of(net, blur=0.6)
        art.put(layer, art.mask_of(axons, blur=0.8), mix(p["neuron"], p["mid"], 0.5), 0.6)
        art.put(layer, net_mask, mix(p["neuron"], p["high"], 0.55))
        art.light(layer, art.blur(net_mask, 10.0), p["neuron"], 0.45)
        art.light(layer, art.mask_of(sparks, blur=1.5), p["spark"], 0.9)
        art.light(layer, art.blur(art.mask_of(sparks), 8.0), p["spark"], 0.5)
        # The Neural Cathedral far off: a tree of a brain on its stem, and the
        # ring of memories turning round it.
        tree, t_pen = art.drawing()
        cu, cv = 0.5, HORIZON - 0.20
        t_pen.poly([(cu - 0.012, HORIZON + 0.02), (cu + 0.012, HORIZON + 0.02), (cu + 0.007, cv + 0.05), (cu - 0.007, cv + 0.05)])
        for k in range(14):
            a = math.pi + math.pi * k / 13
            t_pen.ellipse(cu + math.cos(a) * 0.075, cv + 0.02 + math.sin(a) * 0.065, 0.032, 0.026)
        t_pen.ellipse(cu, cv, 0.09, 0.07)
        tree_mask = art.mask_of(tree, blur=0.8)
        folds = 0.5 + 0.5 * np.sin(art.noise("brain folds", cells=40.0, octaves=2) * 20.0)
        art.put(layer, tree_mask, mix(p["tree"], p["mid"], 0.35))
        art.tint(layer, tree_mask * folds, mix(p["membrane_light"], p["mid"], 0.4), 0.3)
        art.light(layer, art.blur(tree_mask, 12.0), p["neuron"], 0.25)
        frames, f_pen = art.drawing()
        for k in range(12):
            a = math.tau * k / 12 + 0.2
            fu, fv = cu + math.cos(a) * 0.15, cv + 0.02 + math.sin(a) * 0.035
            w = 0.012 * (0.7 + 0.3 * (math.sin(a) + 1) / 2)
            f_pen.rect(fu - w, fv - w * 0.7, fu + w, fv + w * 0.7)
        frame_mask = art.mask_of(frames, blur=0.4)
        art.put(layer, frame_mask * (1.0 - tree_mask * 0.7), mix(p["frame"], p["mid"], 0.4))
        art.light(layer, art.blur(frame_mask, 6.0), p["frame"], 0.3)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # Arches of membrane: a lattice of cells whose walls are flesh, open
        # (holes) in their middles, thicker low down.
        edge, inside = _cells(art, "membrane cells", 48, 0.25, 1.1)
        walls = smoothstep(0.004, 0.018, edge * (0.6 + 0.8 * art.v))
        holes = 1.0 - smoothstep(0.012, 0.024, edge)
        web = np.clip(holes * smoothstep(HORIZON - 0.3, HORIZON + 0.05, art.v + 0.06 * art.noise("web reach", cells=3.0)), 0, 1)
        layer = solid(art, web, mix(p["membrane"], p["haze"], 0.45), mix(p["membrane_dark"], p["haze"], 0.3), HORIZON - 0.2, HORIZON + 0.2, "flesh", 0.08)
        art.light(layer, art.rim(web, 0.0, 0.004, 0.6) * web, p["membrane_light"], 0.35)
        # Glowing drops hang from the undersides of the arches.
        rng = art.rand("drops")
        drops, d_pen = art.drawing()
        for _ in range(60):
            u, v = rng.random(), rng.uniform(HORIZON - 0.15, HORIZON + 0.1)
            d_pen.ellipse(u, v, 0.0022, 0.004)
        drop_mask = art.mask_of(drops, blur=0.4)
        art.put(layer, drop_mask * web, p["spark"], 0.6)
        art.light(layer, art.blur(drop_mask * web, 5.0), p["spark"], 0.35)
        haze(art, layer, p["haze"], 0.22, None)
        return layer
    if layer_key == "near_background":
        # Dendrites near: dark branches that reach up from the floor and fork,
        # each with a glowing synapse bulb at its tip.
        rng = art.rand("near dendrites")
        image, pen = art.drawing()
        tips = []
        for k in range(7):
            u = 0.06 + k * 0.145 + rng.uniform(-0.03, 0.03)
            base = 0.86
            a = -math.pi / 2 + rng.uniform(-0.35, 0.35)
            pts = [(u, base)]
            x, y, w = u, base, 0.012
            for _ in range(4):
                x += math.cos(a) * 0.05
                y += math.sin(a) * 0.05
                pts.append((x, y))
                a += rng.uniform(-0.45, 0.45)
            pen.line(pts, w)
            for fork in (-0.7, 0.7):
                fx, fy = pts[2]
                tip = (fx + math.cos(a + fork) * 0.06, fy + math.sin(a + fork) * 0.06)
                pen.line([pts[2], tip], w * 0.5)
                tips.append(tip)
            tips.append(pts[-1])
        pen.rect(-0.02, 0.86, 1.02, 1.0)
        body = art.mask_of(image)
        layer = solid(art, body, mix(p["membrane_dark"], p["high"], 0.3), scale(p["membrane_dark"], 0.6), 0.4, 0.9, "dendrite", 0.10)
        art.light(layer, art.rim(body, -0.003, -0.002, 0.5) * body, p["membrane_light"], 0.35)
        lamps(art, layer, [(u, v, 0.006) for u, v in tips], p["neuron"], halo=4.0, strength=0.7)
        haze(art, layer, p["haze"], 0.12, None)
        return layer
    # The air: teal fluid glowing low, motes of light.
    layer = art.blank()
    art.put(layer, fog(art, "csf glow", 0.80, 0.08, cells=3.0), p["fluid"], 0.20)
    art.put(layer, fog(art, "cortex haze", 0.55, 0.16, cells=2.0), p["haze"], 0.10)
    return layer


def _layer_net(pen: Pen, nodes: Pen, u0: float, u1: float, v0: float, v1: float, layers: tuple[int, ...]) -> list[tuple[float, float]]:
    """A network drawn as its diagram: columns of nodes, each joined to every
    node of the next column. Returns the nodes."""
    cols = []
    for k, n in enumerate(layers):
        u = u0 + (u1 - u0) * k / (len(layers) - 1)
        cols.append([(u, v0 + (v1 - v0) * (j + 0.5) / n) for j in range(n)])
    for a, b in zip(cols, cols[1:]):
        for pa in a:
            for pb in b:
                pen.line([pa, pb], 0.0008)
    out = [pt for col in cols for pt in col]
    for u, v in out:
        nodes.ellipse(u, v, 0.006)
    return out


def neural_circuit(layer_key: str, art: Art) -> np.ndarray:
    p = CIRCUIT
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.4, p["mid"]), (HORIZON + 0.05, p["low"]), (1.0, p["mid"])]))
        # The traces of a circuit board, far off: right-angled runs with a pad
        # at each end.
        rng = art.rand("traces")
        traces, t_pen = art.drawing()
        pads, p_pen = art.drawing()
        for _ in range(70):
            u, v = rng.random(), rng.uniform(0.05, 0.95)
            pts = [(u, v)]
            for _ in range(rng.randint(2, 4)):
                if rng.random() < 0.5:
                    u += rng.uniform(-0.12, 0.12)
                else:
                    v += rng.uniform(-0.08, 0.08)
                pts.append((u, v))
            t_pen.line(pts, 0.0012)
            p_pen.ellipse(pts[0][0], pts[0][1], 0.0028)
            p_pen.ellipse(pts[-1][0], pts[-1][1], 0.0028)
        art.put(layer, art.mask_of(traces, blur=0.5), mix(p["trace_dim"], p["mid"], 0.3), 0.7)
        art.light(layer, art.mask_of(pads, blur=0.5), p["trace"], 0.5)
        # The network hung in the air: its layers, node to node.
        net, n_pen = art.drawing()
        nodes, node_pen = art.drawing()
        _layer_net(n_pen, node_pen, 0.22, 0.78, 0.16, HORIZON - 0.06, (4, 6, 6, 3))
        art.light(layer, art.mask_of(net, blur=0.6), p["trace"], 0.35)
        node_mask = art.mask_of(nodes, blur=0.5)
        art.put(layer, node_mask, p["node"], 0.85)
        art.light(layer, art.blur(node_mask, 8.0), p["node"], 0.5)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # Racks of memory, row on row: cabinets of one height, each a stack
        # of units with a column of lights at its edge.
        rng = art.rand("racks")
        image, pen = art.drawing()
        slots, s_pen = art.drawing()
        leds, l_pen = art.drawing()
        warm, w_pen = art.drawing()
        foot = HORIZON + 0.12
        h = 0.27
        u = -0.01
        while u < 1.0:
            w = 0.052
            pen.rect(u, foot - h, u + w, foot)
            pen.rect(u - 0.002, foot - h - 0.01, u + w + 0.002, foot - h)
            v = foot - h + 0.008
            while v < foot - 0.01:
                s_pen.rect(u + 0.004, v + 0.0085, u + w - 0.004, v + 0.0105)
                for k in range(3):
                    if rng.random() < 0.5:
                        (w_pen if rng.random() < 0.15 else l_pen).rect(u + w - 0.012 + k * 0.003, v + 0.003, u + w - 0.0105 + k * 0.003, v + 0.0045)
                v += 0.0105
            u += w + 0.006
        pen.rect(-0.02, foot, 1.02, 1.0)
        body = art.mask_of(image)
        layer = solid(art, body, mix(p["rack_light"], p["haze"], 0.35), mix(p["rack"], p["haze"], 0.25), HORIZON - 0.2, HORIZON + 0.1, "racks", 0.05)
        art.light(layer, art.rim(body, 0.003, 0.0, 0.5) * body, p["trace"], 0.25)
        art.shade(layer, art.mask_of(slots) * body, 0.35)
        art.light(layer, art.mask_of(leds, blur=0.3) * body, p["led"], 0.8)
        art.light(layer, art.mask_of(warm, blur=0.3) * body, p["led_warm"], 0.8)
        haze(art, layer, p["haze"], 0.2, foot)
        return layer
    if layer_key == "near_background":
        # Bundles of cable and conduit along the top and down the sides,
        # with junction boxes.
        image, pen = art.drawing()
        for k, v in enumerate((0.20, 0.235, 0.26)):
            pen.curve((-0.02, v), (1.02, v + 0.02 * (k - 1)), 0.03 + 0.01 * k, 0.006)
        for u in (0.08, 0.92):
            pen.rect(u - 0.012, 0.22, u + 0.012, 1.0)
            pen.rect(u - 0.022, 0.5, u + 0.022, 0.56)
        pen.rect(-0.02, 0.88, 1.02, 1.0)
        body = art.mask_of(image)
        layer = solid(art, body, p["rack_light"], p["rack"], 0.3, 0.9, "conduit", 0.06)
        art.light(layer, art.rim(body, 0.0, -0.003, 0.4) * body, p["violet"], 0.4)
        lamps(art, layer, [(0.08, 0.53, 0.004), (0.92, 0.53, 0.004)], p["led"], halo=4.0, strength=0.7)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "circuit glow", 0.84, 0.08, cells=3.0), p["violet"], 0.2)
    return layer


def neural_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A dendrite reaching in from the top of the view, and two synapse bulbs
    rising from below."""
    pen.curve((0.70, 0.33), (0.95, 0.38), 0.02, 0.006)
    pen.curve((0.82, 0.345), (0.86, 0.40), -0.01, 0.003)
    for u in (0.12, 0.30):
        pen.rect(u - 0.003, 0.66, u + 0.003, 0.70)
        pen.ellipse(u, 0.658, 0.009, 0.007)


def circuit_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A cable tray across the top of the view, and the corner of a rack from
    below."""
    pen.rect(-0.02, 0.35, 1.02, 0.362)
    for u in np.arange(0.0, 1.0, 0.1):
        pen.rect(float(u), 0.346, float(u) + 0.004, 0.366)
    pen.rect(0.86, 0.66, 0.96, 0.70)
