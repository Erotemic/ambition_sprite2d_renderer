"""Opaque scenes behind authored water volumes.

A backplate is a scene, not a water effect or a parallax layer. The game fits
one whole image to the water region's rectangle in world space. The water tint,
surface, dock props and characters stay independent of this picture.

Only themes that need a distinct underwater scene publish a backplate. Other
themes keep their current transparent water over their normal scenery.
"""

from __future__ import annotations

import math
import random
from typing import Callable

from PIL import Image, ImageDraw

from ..backgrounds.pirate_port import PORT


# The pirate docks currently author one 2816 x 144-unit harbor water volume.
# A different footprint is valid: the runtime fits the image to its volume.
PIRATE_PORT_SIZE = (2816, 144)
SIZES: dict[str, tuple[int, int]] = {"pirate_port": PIRATE_PORT_SIZE}

RGB = tuple[int, int, int]


def _blend(a: RGB, b: RGB, amount: float) -> RGB:
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


def pirate_port() -> Image.Image:
    """Harbor water in cross-section, behind the playable docks.

    The drawing uses the port's air and sea palette. Wood, distant rocks and
    weed are low contrast, so underwater characters remain easy to see.
    """
    w, h = PIRATE_PORT_SIZE
    upper = _blend(PORT["sea"], PORT["mid"], 0.32)
    lower = _blend(PORT["deep"], (12, 49, 59), 0.22)
    image = Image.new("RGBA", (w, h))
    pixels = image.load()
    for y in range(h):
        depth = y / (h - 1)
        color = _blend(upper, lower, depth**0.78)
        for x in range(w):
            pixels[x, y] = (*color, 255)

    # Light reaches only the top. Keep these broad, like the port's distant
    # buildings, rather than painting fine detail behind the player.
    light = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pen = ImageDraw.Draw(light)
    for x, width in ((260, 130), (890, 180), (1590, 145), (2370, 180)):
        pen.polygon([(x, 0), (x + width, 0), (x + width * 1.8, h - 22),
                     (x - width * 0.25, h - 22)], fill=(156, 212, 202, 11))
    for y in (4, 11, 19):
        # Short, interrupted horizontal reflections under the water surface.
        for x in range(36 + y * 13, w - 25, 113):
            span = 14 + (x // 113) % 24
            pen.rounded_rectangle((x, y, x + span, y + 1), radius=1, fill=(207, 238, 221, 38))
    image = Image.alpha_composite(image, light)
    pen = ImageDraw.Draw(image)

    # Darker, distant dock supports carry the geometry below the horizon.
    # These are scenery, not duplicates of collision-bearing pier columns.
    for index, x in enumerate((120, 405, 720, 1105, 1485, 1835, 2220, 2625)):
        width = 19 if index % 3 else 26
        pen.polygon(
            [(x, -5), (x + width, -5), (x + width + 4, h - 2), (x - 5, h - 2)],
            fill=_blend(PORT["deep"], PORT["timber"], 0.24),
        )
        pen.line([(x + 3, 0), (x + 3, h - 9)], fill=(79, 126, 129), width=2)
        for y in (35, 82, 119):
            pen.line([(x - 2, y), (x + width + 3, y + 3)], fill=(24, 70, 82), width=2)

    # The far floor is an irregular, quiet silhouette. It meets the authored
    # sea-floor blocks but never changes the play or collision geometry.
    floor = [(-1, h)]
    for x in range(0, w + 24, 24):
        y = h - 21 + 5 * math.sin(x * 0.009) + 3 * math.sin(x * 0.027 + 1.6)
        floor.append((x, y))
    floor.append((w, h))
    pen.polygon(floor, fill=(35, 88, 96))

    # Scattered rocks, sea grass and a few submerged fragments add depth.
    rng = random.Random(24211)
    for x in range(38, w - 20, 135):
        x += rng.randint(-40, 40)
        baseline = h - rng.randint(5, 16)
        radius = rng.randint(12, 25)
        rock = [(x - radius, baseline), (x - radius * 0.7, baseline - radius * 0.7),
                (x - radius * 0.2, baseline - radius),
                (x + radius * 0.65, baseline - radius * 0.65), (x + radius, baseline)]
        pen.polygon(rock, fill=(27, 74, 80))
        pen.line(rock[1:4], fill=(64, 115, 113), width=2, joint="curve")
    for x in (150, 314, 590, 970, 1280, 1660, 1940, 2130, 2480, 2740):
        bottom = h - 7
        for offset, height, lean in ((-8, 20, -12), (0, 33, 5), (7, 26, 12)):
            pen.line([(x + offset, bottom), (x + offset + lean * 0.3, bottom - height * 0.6),
                      (x + offset + lean, bottom - height)], fill=(37, 110, 103), width=4, joint="curve")
            pen.line([(x + offset + lean, bottom - height),
                      (x + offset + lean + (3 if lean >= 0 else -3), bottom - height + 7)],
                     fill=(53, 137, 117), width=2)

    # Sparse silt and bubbles. No bright outline competes with the player.
    for _ in range(125):
        x = rng.randrange(w)
        y = rng.randrange(26, h - 20)
        radius = rng.choice((1, 1, 2))
        pen.ellipse((x, y, x + radius * 2, y + radius * 2), outline=(99, 168, 160), width=1)
    return image


BACKDROPS: dict[str, Callable[[], Image.Image]] = {"pirate_port": pirate_port}
