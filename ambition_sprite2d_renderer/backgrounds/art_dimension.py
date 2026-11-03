"""The scenes of the Art dimension: a world where art is the material.

Three looks, one for each layer of the dimension:

- ``art`` (the surface: the Painter's Plaza and the Sculpture Garden). A sky
  of washed colour, as a wet painting is. Gold frames float in it with
  pictures of the sky in them. Far off are mesas whose sides are runs of
  paint, a city of crayons on one of them, and a great marble head that is
  not finished. Near are crayons that stand as tall as trees, the handles of
  brushes, and paint that runs over the edges of the land.
- ``art_sketchbook`` (the sky: the Sketchbook Cliffs). The sky is paper. The
  clouds are drawn in pencil, the hills far off are lines with hatching, and
  a castle is a sketch that nobody finished. Near, pages stand up from the
  ground like cliffs, and the rings of the binding hang over the view.
- ``art_inkfall`` (under: the Inkfall Caverns). A cave of violet stone where
  ink falls and glows. The falls are magenta and cyan; the ink pools at the
  foot of the view, and drops of it hang from the roof.

The palette is the one of the concept sheets: magenta, cyan, yellow and
violet, with white paper and grey stone. Bright paint is kept far off or at
the edges, so the play in front of it reads. The flecks of paint in the air
are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import HORIZON, cloud_mask, fog, haze, shafts, solid, vignette

ART = {
    "top": (58, 96, 196),
    "mid": (112, 170, 236),
    "low": (250, 214, 236),
    "glow": (255, 244, 214),
    "wash_pink": (246, 150, 210),
    "wash_cyan": (120, 222, 240),
    "magenta": (232, 54, 172),
    "cyan": (40, 200, 236),
    "yellow": (255, 210, 50),
    "violet": (118, 64, 196),
    "gold": (236, 180, 60),
    "gold_dark": (150, 96, 30),
    "marble": (226, 222, 236),
    "marble_dark": (146, 140, 168),
    "far": (126, 112, 196),
    "near": (54, 34, 92),
    "near_light": (140, 92, 196),
    "paper": (250, 246, 236),
}

SKETCH = {
    "paper": (246, 241, 228),
    "paper_shadow": (214, 206, 190),
    "graphite": (92, 94, 110),
    "graphite_light": (160, 160, 172),
    "blue_line": (150, 190, 226),
    "near": (112, 108, 122),
    "near_light": (232, 226, 210),
    "crayon": (236, 82, 170),
}

INKFALL = {
    "top": (14, 8, 34),
    "mid": (40, 20, 84),
    "low": (74, 34, 128),
    "rock": (36, 22, 70),
    "rock_light": (96, 64, 160),
    "magenta": (246, 70, 200),
    "cyan": (60, 220, 250),
    "glow": (255, 170, 236),
    "near": (16, 8, 34),
    "near_light": (70, 40, 128),
}


# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------


def _frame(pen: Pen, inner: Pen, u: float, v: float, w: float, h: float, tilt: float) -> None:
    """A picture frame turned by `tilt` radians about its middle: `pen` takes
    the moulding, `inner` the picture."""

    def box(half_w: float, half_h: float) -> list[tuple[float, float]]:
        c, s = math.cos(tilt), math.sin(tilt)
        return [(u + x * c - y * s, v + x * s + y * c) for x, y in ((-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h))]

    pen.poly(box(w * 0.5, h * 0.5))
    inner.poly(box(w * 0.36, h * 0.34))


def _crayon(pen: Pen, u: float, v_foot: float, h: float, w: float, lean: float = 0.0) -> list[tuple[float, float]]:
    """A crayon that stands on its foot with its point up. Returns the band
    of its paper wrapper, so a caller can draw the band in another colour."""
    top = v_foot - h
    tip = top - w * 1.6
    pen.poly([(u - w, v_foot), (u + w, v_foot), (u + w + lean, top), (u + lean + w * 0.35, tip + w * 0.3), (u + lean - w * 0.35, tip + w * 0.3), (u - w + lean, top)])
    t0, t1 = 0.30, 0.62
    return [
        (u - w + lean * t0, v_foot - h * t0),
        (u + w + lean * t0, v_foot - h * t0),
        (u + w + lean * t1, v_foot - h * t1),
        (u - w + lean * t1, v_foot - h * t1),
    ]


def _brush(pen: Pen, tuft: Pen, u: float, v_foot: float, h: float, w: float, lean: float) -> None:
    """A paint brush that stands on the end of its handle, as a tree does:
    `pen` takes the handle and the ferrule, `tuft` the hairs with paint on them."""
    top = v_foot - h
    pen.poly([(u - w * 0.5, v_foot), (u + w * 0.5, v_foot), (u + lean + w * 0.8, top + h * 0.22), (u + lean - w * 0.8, top + h * 0.22)])
    pen.rect(u + lean - w * 0.95, top + h * 0.14, u + lean + w * 0.95, top + h * 0.24)
    tuft.poly([(u + lean - w * 0.95, top + h * 0.15), (u + lean + w * 0.95, top + h * 0.15), (u + lean + w * 0.55, top + h * 0.03), (u + lean, top - h * 0.02), (u + lean - w * 0.55, top + h * 0.03)])


def _drips(pen: Pen, rng, u0: float, u1: float, v: float, longest: float, width: float) -> None:
    """Paint that runs down from a level edge between `u0` and `u1`: a band
    with round drops of each length under it."""
    pen.rect(u0, v - width, u1, v + width * 0.6)
    u = u0 + rng.uniform(0.0, 0.01)
    while u < u1:
        w = rng.uniform(0.004, 0.009)
        length = rng.uniform(0.15, 1.0) * longest
        pen.rect(u - w * 0.5, v, u + w * 0.5, v + length)
        pen.ellipse(u, v + length, w * 0.75, w * 0.9)
        u += rng.uniform(0.012, 0.03)


def _head(pen: Pen, cut: Pen, u: float, v_foot: float, h: float) -> None:
    """A great marble head and shoulders on the land, looking left. Its back
    is a block that the chisel did not reach: `cut` takes the rough faces."""
    w = h * 0.62
    # Shoulders: a slab wider than the head.
    pen.poly([(u - w * 1.2, v_foot), (u + w * 1.25, v_foot), (u + w * 1.05, v_foot - h * 0.30), (u - w * 0.95, v_foot - h * 0.32)])
    # The neck and the head, the face to the left.
    pen.rect(u - w * 0.30, v_foot - h * 0.48, u + w * 0.34, v_foot - h * 0.28)
    pen.ellipse(u, v_foot - h * 0.70, w * 0.52, h * 0.30)
    # The nose and the brow stand out of the face.
    pen.poly([(u - w * 0.50, v_foot - h * 0.78), (u - w * 0.64, v_foot - h * 0.64), (u - w * 0.48, v_foot - h * 0.60)])
    # The back of the head is still a block.
    cut.poly([(u + w * 0.10, v_foot - h * 0.98), (u + w * 0.62, v_foot - h * 0.92), (u + w * 0.70, v_foot - h * 0.45), (u + w * 0.22, v_foot - h * 0.40)])


def _sketch_castle(pen: Pen, u: float, v_foot: float, h: float) -> None:
    """A castle drawn in lines: towers with cone roofs, a wall, a gate."""
    w = h * 0.9
    lw = 0.0016
    for tu, th in ((-0.42, 0.62), (-0.14, 0.88), (0.18, 1.0), (0.44, 0.70)):
        x = u + tu * w
        top = v_foot - th * h
        tw = w * 0.07
        pen.line([(x - tw, v_foot), (x - tw, top), (x + tw, top), (x + tw, v_foot)], lw)
        pen.line([(x - tw * 1.3, top), (x, top - h * 0.18), (x + tw * 1.3, top), (x - tw * 1.3, top)], lw)
        pen.line([(x, top - h * 0.18), (x, top - h * 0.26), (x + tw * 0.9, top - h * 0.23), (x, top - h * 0.21)], lw * 0.8)
    pen.line([(u - w * 0.42, v_foot - h * 0.36), (u + w * 0.44, v_foot - h * 0.36)], lw)
    pen.arc(u + w * 0.02, v_foot, h * 0.12, 180.0, 360.0, lw)


def _hatch(pen: Pen, u0: float, v0: float, u1: float, v1: float, step: float, width: float) -> None:
    """Pencil hatching at 45 degrees, in the box from `(u0, v0)` to `(u1, v1)`."""
    k = u0 - (v1 - v0)
    while k < u1:
        a = (max(u0, k), v1 - (max(u0, k) - k))
        b = (min(u1, k + (v1 - v0)), v1 - (min(u1, k + (v1 - v0)) - k))
        pen.line([a, b], width)
        k += step


def _stalactite(pen: Pen, u: float, v_root: float, length: float, w: float) -> None:
    pen.poly([(u - w, v_root), (u + w, v_root), (u + w * 0.2, v_root + length), (u - w * 0.15, v_root + length * 0.96)])


def _fall(art: Art, u: float, v0: float, v1: float, w: float, tag: object) -> np.ndarray:
    """A fall of ink: a column from `v0` to `v1`, its edges moved by noise
    so it ripples, brighter at its middle."""
    ripple = art.noise(tag, cells=10.0, octaves=3, stretch=0.2)
    width = w * (0.85 + 0.3 * ripple)
    across = np.abs(art.u - u) / np.maximum(width, 1e-4)
    body = np.clip(1.0 - across, 0.0, 1.0) ** 0.5
    return body * smoothstep(v0 - 0.01, v0 + 0.01, art.v) * smoothstep(v1 + 0.02, v1 - 0.01, art.v)


# ---------------------------------------------------------------------------
# The surface: the plaza and the garden
# ---------------------------------------------------------------------------


def art(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = ART
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.28, p["mid"]), (HORIZON - 0.04, mix(p["low"], p["glow"], 0.4)), (HORIZON + 0.08, p["low"]), (0.82, mix(p["mid"], p["low"], 0.5)), (1.0, p["mid"])]))
        # Washes of colour that run into each other, as wet paint on paper.
        for tag, colour, amount in (("pink wash", p["wash_pink"], 0.55), ("cyan wash", p["wash_cyan"], 0.45), ("yellow wash", p["glow"], 0.35)):
            wash = smoothstep(0.55, 0.85, a.noise(tag, cells=2.2, octaves=4, stretch=1.8)) * smoothstep(0.02, 0.30, a.v) * smoothstep(0.75, 0.50, a.v)
            a.tint(layer, wash, colour, amount)
        # A halo of light high up, a ring as the concept's floating rings are.
        halo, halo_pen = a.drawing()
        halo_pen.ring(0.62, 0.22, 0.09, 0.006)
        halo_pen.ring(0.62, 0.22, 0.12, 0.003)
        a.light(layer, a.mask_of(halo, blur=2.0), p["glow"], 0.55)
        # Clouds: soft and round, a little pink at their feet.
        clouds = cloud_mask(a, "clouds", 0.36, 0.12, cells=3.0, cover=0.40, soft=0.18, stretch=2.4)
        a.tint(layer, clouds, p["paper"], 0.70)
        a.tint(layer, clouds * smoothstep(0.30, 0.44, a.v), p["wash_pink"], 0.30)
        # The far mesas: blue and violet in the haze, with runs of paint down them.
        for tag, base, amp, colour, amount in (("mesa a", 0.56, 0.05, mix(p["far"], p["mid"], 0.55), 0.70), ("mesa b", 0.60, 0.04, mix(p["far"], p["mid"], 0.25), 0.82)):
            land, line = a.ridge(tag, base, amp, cells=3.0, octaves=4, sharp=0.6)
            a.tint(layer, land, colour, amount)
            rng = a.rand((tag, "runs"))
            runs, run_pen = a.drawing()
            for _ in range(10):
                u = rng.random()
                v = float(line[min(a.n - 1, int(u * a.n))])
                run_pen.rect(u - 0.004, v, u + 0.004, v + rng.uniform(0.02, 0.06))
            a.tint(layer, a.mask_of(runs, blur=1.0) * land, rng.choice([p["magenta"], p["cyan"], p["yellow"]]), 0.40)
        a.tint(layer, fog(a, "mesa mist", HORIZON + 0.02, 0.05), p["low"], 0.45)
        a.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far art")
        ground, line = a.ridge("far land", HORIZON + 0.03, 0.025, cells=3.0, octaves=4)
        image, pen = a.drawing()
        marble, marble_pen = a.drawing()
        rough, rough_pen = a.drawing()
        frames, frame_pen = a.drawing()
        pictures, picture_pen = a.drawing()
        # A city of crayons on the land at the left: towers with points.
        crayons = []
        for k in range(9):
            u = 0.06 + k * 0.035 + rng.uniform(-0.01, 0.01)
            v = float(line[min(a.n - 1, int(u * a.n))]) + 0.01
            crayons.append((u, v, rng.uniform(0.06, 0.16), rng.uniform(0.007, 0.011)))
        crayon_masks = []
        for u, v, h, w in crayons:
            one, one_pen = a.drawing()
            _crayon(one_pen, u, v, h, w)
            crayon_masks.append(a.mask_of(one))
        # The great head on the land at the right, half made.
        _head(marble_pen, rough_pen, 0.74, float(line[int(0.74 * a.n)]) + 0.01, 0.20)
        # Frames that float over the land, each turned a little.
        for u, v, w, h, tilt in ((0.36, 0.30, 0.07, 0.055, -0.18), (0.55, 0.41, 0.05, 0.065, 0.22), (0.93, 0.30, 0.06, 0.05, 0.10)):
            _frame(frame_pen, picture_pen, u, v, w, h, tilt)
        # Paint that falls off the edge of the land in two places.
        for u, colour in ((0.30, "magenta"), (0.58, "cyan")):
            v = float(line[int(u * a.n)])
            pen.rect(u - 0.012, v - 0.005, u + 0.012, v + 0.012)
        mask = np.maximum(ground, a.mask_of(image))
        layer = solid(a, mask, mix(p["far"], p["mid"], 0.35), scale(p["far"], 0.85), 0.50, 0.70, "canvas", 0.06)
        palette = [p["magenta"], p["cyan"], p["yellow"], p["violet"], p["wash_pink"]]
        for index, one in enumerate(crayon_masks):
            colour = mix(palette[index % len(palette)], p["far"], 0.35)
            a.put(layer, one, colour)
            a.shade(layer, a.rim(one, 0.002, 0.0) * one, 0.30)
        stone = a.mask_of(marble, blur=0.5)
        a.put(layer, stone, mix(p["marble"], p["far"], 0.25))
        a.shade(layer, a.rim(stone, 0.004, 0.002, 0.6) * stone, 0.28)
        block = a.mask_of(rough, blur=0.3) * stone
        a.put(layer, block, mix(p["marble_dark"], p["far"], 0.30), 0.55)
        # A stripe of magenta paint across the marble face, as in the sheets.
        stripe = a.band(float(line[int(0.74 * a.n)]) - 0.14, 0.010) * smoothstep(0.66, 0.70, a.u) * smoothstep(0.80, 0.76, a.u)
        a.tint(layer, stripe * stone, p["magenta"], 0.55)
        gold = a.mask_of(frames, blur=0.3)
        a.put(layer, gold, mix(p["gold"], p["far"], 0.15))
        a.shade(layer, a.rim(gold, 0.002, 0.002) * gold, 0.40)
        picture = a.mask_of(pictures, blur=0.3)
        a.put(layer, picture, a.ramp([(0.2, p["wash_pink"]), (0.45, p["wash_cyan"])]))
        # Runs of paint over the land's edge.
        runs, run_pen = a.drawing()
        _drips(run_pen, rng, 0.0, 1.0, HORIZON + 0.03, 0.04, 0.003)
        paint = a.mask_of(runs, blur=0.4) * ground
        a.put(layer, paint, a.ramp([(0.6, p["magenta"]), (0.7, p["violet"])]), 0.55)
        a.light(layer, a.rim(mask, -0.003, 0.003, 0.6) * mask, p["glow"], 0.34)
        haze(a, layer, p["low"], 0.22, HORIZON + 0.05)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near art")
        image, pen = a.drawing()
        tufts, tuft_pen = a.drawing()
        bands, band_pen = a.drawing()
        ground, _ = a.ridge("near land", 0.70, 0.014, cells=5.0, octaves=3)
        # Giant crayons at the sides, as tall as trees, and brushes between.
        crayons = []
        for u, h, w, lean in ((0.04, 0.62, 0.028, 0.01), (0.12, 0.44, 0.020, -0.012), (0.88, 0.50, 0.022, 0.012), (0.965, 0.70, 0.030, -0.01)):
            one, one_pen = a.drawing()
            band = _crayon(one_pen, u, 0.74, h, w, lean)
            band_pen.poly(band)
            crayons.append(a.mask_of(one))
        for u, h, lean in ((0.22, 0.36, -0.02), (0.78, 0.40, 0.025)):
            _brush(pen, tuft_pen, u, 0.74, h, 0.010, lean)
        # A palette lies tilted on the land at the middle, and pots of paint.
        pen.ellipse(0.50, 0.712, 0.07, 0.014)
        for _ in range(5):
            u = rng.choice([rng.uniform(0.28, 0.42), rng.uniform(0.58, 0.72)])
            pen.rect(u - 0.012, 0.69, u + 0.012, 0.72)
            pen.ellipse(u, 0.69, 0.012, 0.004)
        mask = np.maximum.reduce([ground, a.mask_of(image)] + crayons)
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.55), p["near"], 0.24, 0.74, "canvas", 0.10)
        palette = [p["magenta"], p["yellow"], p["cyan"], p["violet"]]
        for index, one in enumerate(crayons):
            a.put(layer, one, mix(palette[index], p["near"], 0.38))
            a.light(layer, a.rim(one, -0.004, 0.0, 0.4) * one, p["glow"], 0.30)
            a.shade(layer, a.rim(one, 0.005, 0.0, 0.6) * one, 0.34)
        a.shade(layer, a.mask_of(bands) * mask, 0.36)
        hair = a.mask_of(tufts, blur=0.3)
        a.put(layer, hair, mix(p["magenta"], p["near"], 0.30))
        a.light(layer, a.rim(hair, -0.002, 0.002, 0.3) * hair, p["wash_pink"], 0.40)
        # Paint that runs over the near land, in the three primaries.
        for tag, colour, u0, u1 in (("pink run", p["magenta"], 0.0, 0.36), ("cyan run", p["cyan"], 0.62, 1.0), ("yellow run", p["yellow"], 0.40, 0.58)):
            runs, run_pen = a.drawing()
            _drips(run_pen, a.rand(tag), u0, u1, 0.706, 0.035, 0.004)
            paint = a.mask_of(runs, blur=0.3) * ground
            a.put(layer, paint, mix(colour, p["near"], 0.30), 0.85)
        a.light(layer, a.rim(mask, -0.003, 0.003, 0.4) * mask, p["glow"], 0.30)
        a.shade(layer, a.rim(mask, 0.005, -0.003, 1.2) * mask, 0.24)
        haze(a, layer, p["far"], 0.10, 0.73)
        return layer
    layer = a.blank()
    a.put(layer, shafts(a, "sun shafts", 5, -0.10, 0.0, 0.80, 0.05), p["glow"], 0.16)
    a.put(layer, fog(a, "paint mist", 0.70, 0.12), p["low"], 0.26)
    vignette(a, layer, p["near"], 0.30)
    return layer


def art_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Brushes that lean in from below at the edges, and a crayon. Nothing hangs."""
    del layer_lights
    rng = art_.rand("art foreground")
    for k in range(5):
        u = (k + rng.uniform(0.15, 0.85)) / 5.0
        top = rng.uniform(0.66, 0.70)
        w = rng.choice([0.006, 0.008])
        lean = rng.uniform(-0.02, 0.02)
        pen.poly([(u - w, 1.0), (u + w, 1.0), (u + lean + w * 0.7, top + 0.03), (u + lean - w * 0.7, top + 0.03)])
        pen.poly([(u + lean - w, top + 0.034), (u + lean + w, top + 0.034), (u + lean, top)])


# ---------------------------------------------------------------------------
# The sky: the Sketchbook Cliffs
# ---------------------------------------------------------------------------


def art_sketchbook(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = SKETCH
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, mix(p["paper"], p["blue_line"], 0.25)), (0.5, p["paper"]), (1.0, mix(p["paper"], p["paper_shadow"], 0.5))]))
        # The lines of the page, faint and blue, as on a pad.
        lines, line_pen = a.drawing()
        v = 0.04
        while v < 1.0:
            line_pen.line([(0.0, v), (1.0, v)], 0.0012)
            v += 0.035
        a.tint(layer, a.mask_of(lines), p["blue_line"], 0.30)
        # Clouds drawn in pencil: a round edge, hatched under.
        clouds, cloud_pen = a.drawing()
        shade_marks, shade_pen = a.drawing()
        rng = a.rand("pencil clouds")
        for _ in range(7):
            u, v = rng.uniform(0.0, 1.0), rng.uniform(0.18, 0.46)
            r = rng.uniform(0.03, 0.05)
            for k in range(4):
                cloud_pen.arc(u + (k - 1.5) * r * 0.9, v - (0.3 if k in (1, 2) else 0.0) * r, r * (1.1 if k in (1, 2) else 0.8), 180.0, 360.0, 0.0018)
            cloud_pen.line([(u - r * 2.2, v + r * 0.2), (u + r * 2.2, v + r * 0.2)], 0.0016)
            _hatch(shade_pen, u - r * 1.8, v - r * 0.1, u + r * 1.8, v + r * 0.2, 0.006, 0.0010)
        a.tint(layer, a.mask_of(clouds, blur=0.3), p["graphite"], 0.70)
        a.tint(layer, a.mask_of(shade_marks, blur=0.2), p["graphite_light"], 0.40)
        # Hills far off: one line each, with hatching under the line.
        for tag, base, amp, amount in (("far hills a", 0.57, 0.04, 0.45), ("far hills b", 0.62, 0.03, 0.65)):
            land, line = a.ridge(tag, base, amp, cells=3.5, octaves=4)
            edge = a.rim(land, 0.0, 0.0015)
            a.tint(layer, edge, p["graphite"], amount)
            hatch, hatch_pen = a.drawing()
            _hatch(hatch_pen, 0.0, base - amp, 1.0, 1.0, 0.012, 0.0009)
            a.tint(layer, a.mask_of(hatch) * land * smoothstep(0.08, 0.0, a.v - line[None, :]), p["graphite_light"], amount * 0.6)
        castle, castle_pen = a.drawing()
        _sketch_castle(castle_pen, 0.30, 0.58, 0.16)
        a.tint(layer, a.mask_of(castle, blur=0.3), p["graphite"], 0.80)
        a.grain(layer, "paper grain", 3.0)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far pages")
        image, pen = a.drawing()
        marks, mark_pen = a.drawing()
        # Pages that stand up out of the land, each a little turned: the cliffs.
        ground, line = a.ridge("page land", HORIZON + 0.04, 0.02, cells=3.0, octaves=3)
        for k in range(7):
            u = 0.05 + k * 0.15 + rng.uniform(-0.03, 0.03)
            v = float(line[min(a.n - 1, int(u * a.n))]) + 0.01
            h, w = rng.uniform(0.14, 0.26), rng.uniform(0.05, 0.09)
            lean = rng.uniform(-0.02, 0.02)
            pen.poly([(u - w, v), (u + w, v), (u + w + lean, v - h + 0.01), (u + lean, v - h), (u - w + lean, v - h + 0.008)])
            # A drawing on the page: a scribble of lines.
            for _ in range(4):
                y = v - h * rng.uniform(0.25, 0.8)
                mark_pen.line([(u - w * 0.6 + lean * 0.5, y), (u + w * 0.5 + lean * 0.5, y + rng.uniform(-0.01, 0.01))], 0.0014)
        # Paper planes far off.
        for _ in range(4):
            u, v, s = rng.uniform(0.1, 0.9), rng.uniform(0.22, 0.42), rng.uniform(0.010, 0.016)
            pen.poly([(u - s, v), (u + s, v - s * 0.3), (u - s * 0.2, v + s * 0.35)])
        mask = np.maximum(ground, a.mask_of(image))
        layer = solid(a, mask, p["paper"], p["paper_shadow"], 0.40, 0.72, "paper", 0.04)
        a.shade(layer, a.rim(mask, 0.003, 0.0, 0.5) * mask, 0.22)
        outline = np.clip(a.rim(mask, -0.0015, -0.0015) + a.rim(mask, 0.0015, 0.0015), 0.0, 1.0) * mask
        a.tint(layer, outline, p["graphite"], 0.85)
        a.tint(layer, a.mask_of(marks) * mask, p["graphite_light"], 0.70)
        haze(a, layer, p["paper"], 0.25, HORIZON + 0.05)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near pages")
        image, pen = a.drawing()
        rings, ring_pen = a.drawing()
        ground, _ = a.ridge("near land", 0.70, 0.012, cells=5.0, octaves=3)
        # Torn pages that stand at the sides.
        for u, w, h in ((0.05, 0.07, 0.50), (0.93, 0.08, 0.56)):
            pts = [(u - w, 0.74)]
            steps = 10
            for i in range(steps + 1):
                t = i / steps
                pts.append((u - w + 2.0 * w * t, 0.74 - h + rng.uniform(-0.012, 0.012)))
            pts.append((u + w, 0.74))
            pen.poly(pts)
        # The rings of the binding over the top of the view.
        for k in range(14):
            u = 0.04 + k * 0.07
            ring_pen.arc(u, 0.03, 0.022, 20.0, 340.0, 0.006)
        # Crayon stubs on the land.
        stubs, stub_pen = a.drawing()
        for _ in range(6):
            u = rng.uniform(0.16, 0.84)
            _crayon(stub_pen, u, 0.72, rng.uniform(0.03, 0.05), 0.008, rng.uniform(-0.01, 0.01))
        mask = np.maximum.reduce([ground, a.mask_of(image)])
        layer = solid(a, mask, p["near_light"], mix(p["near_light"], p["near"], 0.4), 0.20, 0.74, "paper", 0.05)
        outline = np.clip(a.rim(mask, -0.002, -0.002) + a.rim(mask, 0.002, 0.002), 0.0, 1.0) * mask
        a.tint(layer, outline, p["graphite"], 0.80)
        hatch, hatch_pen = a.drawing()
        _hatch(hatch_pen, 0.0, 0.70, 1.0, 1.0, 0.010, 0.0012)
        a.tint(layer, a.mask_of(hatch) * mask, p["graphite_light"], 0.45)
        metal = a.mask_of(rings, blur=0.4)
        a.put(layer, metal, p["graphite_light"])
        a.light(layer, a.rim(metal, -0.002, -0.002, 0.3) * metal, p["paper"], 0.60)
        stub = a.mask_of(stubs)
        a.put(layer, stub, p["crayon"])
        a.shade(layer, a.rim(stub, 0.003, 0.0) * stub, 0.30)
        return layer
    layer = a.blank()
    a.put(layer, fog(a, "paper dust", 0.68, 0.14), p["paper"], 0.30)
    vignette(a, layer, p["paper_shadow"], 0.30)
    return layer


# ---------------------------------------------------------------------------
# Under: the Inkfall Caverns
# ---------------------------------------------------------------------------


def art_inkfall(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = INKFALL
    if layer_key == "sky":
        # The back of the cave: dark at the roof, lit violet at the falls.
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.35, p["mid"]), (HORIZON, p["low"]), (0.80, p["mid"]), (1.0, p["top"])]))
        a.light(layer, a.spot(0.30, 0.55, 0.30, 2.0, squash=0.8), p["magenta"], 0.30)
        a.light(layer, a.spot(0.72, 0.52, 0.26, 2.0, squash=0.8), p["cyan"], 0.24)
        # Far walls of the cave, stacked.
        for tag, base, amp, colour, amount in (("far wall a", 0.50, 0.08, mix(p["rock"], p["low"], 0.5), 0.75), ("far wall b", 0.60, 0.06, p["rock"], 0.85)):
            wall, _ = a.ridge(tag, base, amp, cells=4.0, octaves=5, sharp=0.5)
            a.tint(layer, wall, colour, amount)
        # Far falls: thin and bright.
        for u, colour in ((0.18, p["magenta"]), (0.44, p["cyan"]), (0.83, p["magenta"])):
            falling = _fall(a, u, 0.30, 0.66, 0.013, ("far fall", u))
            a.glow(layer, a.blur(falling, 10.0), colour, 0.45)
            a.glow(layer, falling, colour, 0.80)
            a.glow(layer, a.spot(u, 0.66, 0.05, 2.0, squash=2.5), colour, 0.40)
        a.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far cave")
        image, pen = a.drawing()
        # A roof of rock with ink stalactites, and a floor of rock.
        roof = 1.0 - a.ridge("roof", 0.16, 0.05, cells=4.0, octaves=4)[0]
        for _ in range(16):
            u = rng.random()
            _stalactite(pen, u, 0.12, rng.uniform(0.05, 0.13), rng.uniform(0.008, 0.016))
        ground, _line = a.ridge("cave floor", HORIZON + 0.06, 0.03, cells=4.0, octaves=4)
        # Ledges in the middle distance, each with ink running off it.
        ledges, ledge_pen = a.drawing()
        for u, v, w in ((0.20, 0.50, 0.08), (0.52, 0.44, 0.07), (0.80, 0.48, 0.09)):
            ledge_pen.poly([(u - w, v), (u + w, v), (u + w * 0.6, v + 0.03), (u - w * 0.7, v + 0.035)])
        rock = np.maximum.reduce([roof, ground, a.mask_of(image), a.mask_of(ledges)])
        layer = solid(a, rock, mix(p["rock"], p["low"], 0.35), p["rock"], 0.20, 0.70, "rock", 0.10)
        a.light(layer, a.rim(rock, -0.003, -0.003, 0.5) * rock, p["rock_light"], 0.40)
        for (u, v, w), colour in zip(((0.20, 0.50, 0.08), (0.52, 0.44, 0.07), (0.80, 0.48, 0.09)), (p["magenta"], p["cyan"], p["magenta"])):
            falling = _fall(a, u + w * 0.5, v + 0.02, HORIZON + 0.08, 0.020, ("mid fall", u))
            a.put(layer, falling, colour, 0.85)
            a.glow(layer, a.blur(falling, 12.0), colour, 0.35)
            # The lip of the ledge glows with the ink on it.
            lip = a.band(v, 0.004) * smoothstep(w, w * 0.8, np.abs(a.u - u))
            a.put(layer, lip, colour, 0.80)
        pools = a.band(HORIZON + 0.075, 0.012) * ground
        a.put(layer, pools, mix(p["magenta"], p["low"], 0.4), 0.55)
        haze(a, layer, p["low"], 0.16, HORIZON + 0.06)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near cave")
        image, pen = a.drawing()
        drops, drop_pen = a.drawing()
        ground, _ = a.ridge("near floor", 0.70, 0.016, cells=5.0, octaves=3)
        # Columns of rock at the sides.
        for u, w in ((0.03, 0.05), (0.16, 0.022), (0.86, 0.03), (0.97, 0.05)):
            pen.poly([(u - w, 0.74), (u - w * 0.6, 0.0), (u + w * 0.6, 0.0), (u + w, 0.74)])
        # The roof and its stalactites, with a drop of ink at each tip.
        roof = smoothstep(0.52, 0.56, a.noise("near roof", cells=6.0, octaves=4) * smoothstep(0.24, 0.06, a.v))
        for _ in range(12):
            u = rng.random()
            length = rng.uniform(0.06, 0.16)
            _stalactite(pen, u, 0.0, length, rng.uniform(0.010, 0.020))
            drop_pen.ellipse(u + 0.002, length + 0.012, 0.0035, 0.005)
        mask = np.maximum.reduce([ground, a.mask_of(image), roof])
        layer = solid(a, mask, p["near_light"], p["near"], 0.20, 0.74, "rock", 0.12)
        a.light(layer, a.rim(mask, -0.003, 0.0, 0.4) * mask, p["magenta"], 0.22)
        a.light(layer, a.rim(mask, 0.003, 0.0, 0.4) * mask, p["cyan"], 0.18)
        a.shade(layer, a.rim(mask, 0.0, -0.004, 1.0) * mask, 0.30)
        ink = a.mask_of(drops, blur=0.3)
        a.put(layer, ink, p["magenta"])
        a.glow(layer, a.blur(ink, 6.0), p["glow"], 0.40)
        # A skin of ink on the floor that glows.
        sheen = a.band(0.712, 0.006) * ground
        a.put(layer, sheen, mix(p["magenta"], p["near"], 0.3), 0.60)
        return layer
    layer = a.blank()
    a.put(layer, fog(a, "ink mist", 0.70, 0.14), p["magenta"], 0.16)
    vignette(a, layer, p["top"], 0.42)
    return layer
