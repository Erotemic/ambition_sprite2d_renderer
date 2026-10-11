"""The shimmer of a biome: what a shader moves in the air of its rooms.

A shimmer is one picture that repeats, `SIZE` pixels square. It is data for a
shader, and it is art: each shape in it is drawn here, and the shader only
moves it and gives it its colour (`starlight_shimmer.wgsl` in Mary-O).

- red: the shapes that come and go (the sparkles of a wand, or embers), each
  with a soft light round it.
- green: when each shape is bright. One value for the whole of a shape, so
  that a shape comes and goes as one thing.
- blue: long soft ribbons that go across the picture and meet themselves at
  its left and right edges. They do not reach its top or its bottom.

A biome with no entry in `SHIMMERS` has no shimmer.
"""

from __future__ import annotations

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = 512
SUPERSAMPLE = 2


def _sparkle(pen: ImageDraw.ImageDraw, x: float, y: float, r: float, value: int) -> None:
    """A star of four points."""
    w = r * 0.20
    pen.polygon([(x, y - r), (x + w, y - w), (x + r, y), (x + w, y + w), (x, y + r), (x - w, y + w), (x - r, y), (x - w, y - w)], fill=value)


def _ember(pen: ImageDraw.ImageDraw, x: float, y: float, r: float, value: int) -> None:
    """A round point of light."""
    pen.ellipse((x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45), fill=value)


#: The shimmer of each biome: its shape, how many, the least and the most
#: radius of a shape (published pixels), and the number of its ribbons.
SHIMMERS = {
    "starlight": (_sparkle, 30, 5.0, 15.0, 3),
    "starless": (_ember, 44, 3.0, 8.0, 2),
}


def picture(key: str) -> Image.Image:
    draw, count, r0, r1, ribbons = SHIMMERS[key]
    rng = random.Random(f"shimmer:{key}")
    n = SIZE * SUPERSAMPLE
    shapes = Image.new("L", (n, n), 0)
    phases = Image.new("L", (n, n), 0)
    shape_pen, phase_pen = ImageDraw.Draw(shapes), ImageDraw.Draw(phases)
    placed: list[tuple[float, float, float]] = []
    tries = 0
    while len(placed) < count and tries < 4000:
        tries += 1
        r = rng.uniform(r0, r1) * SUPERSAMPLE
        x, y = rng.uniform(0, n), rng.uniform(0, n)
        reach = r * 2.4

        def apart(other: tuple[float, float, float]) -> bool:
            dx = min(abs(x - other[0]), n - abs(x - other[0]))
            dy = min(abs(y - other[1]), n - abs(y - other[1]))
            return math.hypot(dx, dy) > reach + other[2] * 2.4 + 4.0

        if not all(apart(other) for other in placed):
            continue
        placed.append((x, y, r))
        phase = rng.randrange(8, 256)
        # A copy at each edge the shape goes over, so that the picture repeats.
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                draw(shape_pen, x + ox, y + oy, r, 255)
                phase_pen.ellipse((x + ox - reach, y + oy - reach, x + ox + reach, y + oy + reach), fill=phase)
    wide = Image.new("L", (3 * n, 3 * n))
    for ix in range(3):
        for iy in range(3):
            wide.paste(shapes, (ix * n, iy * n))
    light = wide.filter(ImageFilter.GaussianBlur(r1 * SUPERSAMPLE * 0.45)).crop((n, n, 2 * n, 2 * n))
    red = np.maximum(np.asarray(shapes, dtype=np.float32), np.asarray(light, dtype=np.float32) * 1.6)

    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32)
    u, v = xs / n, ys / n
    blue = np.zeros((n, n), dtype=np.float32)
    for k in range(ribbons):
        centre = 0.30 + 0.40 * (k + 0.5) / ribbons
        line = centre + 0.07 * np.sin(math.tau * (u + rng.random())) + 0.03 * np.sin(math.tau * (2.0 * u + rng.random()))
        width = 0.045 + 0.025 * np.sin(math.tau * (u + rng.random()))
        # Fine lines down the ribbon, as the folds of a curtain of light.
        folds = 0.62 + 0.38 * np.sin(math.tau * (9.0 * u + rng.random()) + 2.4 * np.sin(math.tau * (3.0 * u + rng.random())))
        above = np.clip((line - v) / (width * 2.6), 0.0, 1.0)
        below = np.clip((v - line) / (width * 0.8), 0.0, 1.0)
        body = np.where(v < line, (1.0 - above) ** 2.2, (1.0 - below) ** 1.4)
        blue = np.maximum(blue, body * folds)
    out = np.dstack([np.clip(red, 0, 255), np.asarray(phases, dtype=np.float32), np.clip(blue * 255.0, 0, 255)])
    image = Image.fromarray(np.rint(out).astype(np.uint8), "RGB")
    return image.resize((SIZE, SIZE), Image.Resampling.BOX)
