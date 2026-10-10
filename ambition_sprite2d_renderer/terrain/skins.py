"""The terrain skin of each biome.

A room of the game is made of collision blocks: rectangles. A skin is the
art the game lays on them:

    fill     64 by 64 units, repeats each way: the inside of a block
    cap      64 by 20 units, repeats along a top edge that nothing covers.
             The surface a body stands on is `CAP_SURFACE` units below the
             top of the picture: what is above it (grass) stands over the
             edge.
    under    64 by 16 units, repeats along a bottom edge that nothing
             covers. The edge is `UNDER_EDGE` units below the top of the
             picture: what is below it hangs under the block.
    side     16 by 64 units, repeats down a left edge (the game mirrors it
             for a right edge): a shade that gives the block a round edge.
    oneway   64 by 16 units, repeats: a platform a body can jump up through.

A unit is a world unit of the game. Each picture has `PX_PER_UNIT` pixels to
the unit: the play camera shows a unit as two and a half pixels of a 1600 px
window.

Each picture repeats with no seam in the direction it is laid.

The fill is dark and has low contrast, and the cap has the one light line:
the top of the ground is what a player must see first.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RGB = tuple[int, int, int]

PX_PER_UNIT = 2
SUPERSAMPLE = 4
#: Working pixels to the unit.
K = PX_PER_UNIT * SUPERSAMPLE

FILL = (64, 64)
CAP = (64, 20)
UNDER = (64, 16)
SIDE = (16, 64)
ONEWAY = (64, 16)

#: How far below the top of the cap picture the surface of the block is.
CAP_SURFACE = 4.0
#: How far below the top of the underside picture the bottom of the block is.
UNDER_EDGE = 4.0


@dataclass(frozen=True)
class Skin:
    key: str
    material: str
    base: RGB
    dark: RGB
    light: RGB
    accent: RGB
    cap: str
    cap_colour: RGB
    under: str
    oneway: str


SKINS: tuple[Skin, ...] = (
    # The lab is steel, not the teal of its air: the ground must not have the
    # colour of what is behind it.
    Skin("lab", "panel", (38, 54, 74), (14, 22, 36), (84, 112, 138), (120, 236, 220), "strip", (62, 84, 108), "pipes", "grate"),
    # The clean state of the two-state hub: pale marble with a line of gold.
    # The look of that room draws its own blocks, and this is what the room
    # has on a device that does not draw the look.
    Skin("hub_clean", "block", (226, 220, 208), (150, 144, 138), (255, 252, 244), (226, 178, 86), "edge", (240, 234, 222), "lip", "slab"),
    Skin("hub", "panel", (40, 40, 94), (15, 15, 46), (92, 94, 164), (255, 206, 140), "strip", (70, 70, 134), "lip", "grate"),
    Skin("basement", "brick", (88, 42, 32), (30, 13, 11), (146, 78, 54), (255, 150, 60), "plate", (58, 42, 40), "bolts", "grate"),
    Skin("boss", "block", (86, 30, 44), (26, 8, 14), (150, 58, 70), (255, 112, 72), "plate", (40, 14, 20), "spikes", "grate"),
    Skin("cave", "rock", (48, 46, 90), (16, 15, 36), (94, 94, 152), (124, 222, 255), "moss", (46, 112, 112), "stalactites", "plank"),
    Skin("cove", "rock", (44, 78, 88), (12, 30, 40), (100, 150, 150), (255, 224, 170), "sand", (214, 190, 140), "weed", "plank"),
    Skin("water", "block", (30, 84, 104), (8, 34, 52), (82, 152, 162), (150, 240, 200), "moss", (36, 132, 108), "weed", "slab"),
    Skin("forest", "earth", (60, 46, 36), (24, 18, 14), (106, 86, 62), (236, 222, 120), "grass", (84, 140, 62), "roots", "plank"),
    Skin("skybridge", "block", (150, 164, 198), (86, 100, 142), (216, 224, 242), (255, 236, 150), "grass", (112, 178, 96), "roots", "slab"),
    Skin("eclipse", "block", (30, 34, 86), (10, 12, 36), (72, 78, 152), (92, 232, 200), "edge", (44, 50, 112), "lip", "slab"),
)


def _mix(a, b, t: float) -> RGB:
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))  # type: ignore[return-value]


def _seed(*parts: object) -> int:
    import hashlib

    return int.from_bytes(hashlib.blake2b(":".join(map(str, parts)).encode(), digest_size=8).digest(), "little")


class Tile:
    """A picture of `w` by `h` units in work. `wrap_x` and `wrap_y` say in
    which directions a shape that goes off one edge comes in at the other."""

    def __init__(self, size: tuple[int, int], wrap_x: bool, wrap_y: bool, *seed: object) -> None:
        self.w, self.h = size
        self.wrap_x, self.wrap_y = wrap_x, wrap_y
        self.W, self.H = self.w * K, self.h * K
        self.rng = random.Random(_seed(*seed))
        self.np_rng = np.random.default_rng(_seed(*seed) % (2**63))
        self.rgb = np.zeros((self.H, self.W, 3), dtype=np.float32)
        self.alpha = np.zeros((self.H, self.W), dtype=np.float32)
        ys, xs = np.mgrid[0 : self.H, 0 : self.W]
        #: The place of each pixel, in units.
        self.x = (xs + 0.5) / K
        self.y = (ys + 0.5) / K

    # -- masks --------------------------------------------------------------

    def mask(self, draw: Callable[[ImageDraw.ImageDraw, float, float], None], blur: float = 0.0) -> np.ndarray:
        """The mask that `draw(pen, dx, dy)` makes. It is called one time for
        each copy a wrap needs, with the offset of that copy in pixels."""
        image = Image.new("L", (self.W, self.H), 0)
        pen = ImageDraw.Draw(image)
        for dx in (-self.W, 0, self.W) if self.wrap_x else (0,):
            for dy in (-self.H, 0, self.H) if self.wrap_y else (0,):
                draw(pen, dx, dy)
        if blur > 0.0:
            image = self._blur(image, blur)
        return np.asarray(image, dtype=np.float32) / 255.0

    def _blur(self, image: Image.Image, units: float) -> Image.Image:
        """Blur that wraps in the directions the tile wraps in."""
        pad_x = self.W if self.wrap_x else 0
        pad_y = self.H if self.wrap_y else 0
        if pad_x or pad_y:
            wide = Image.new("L", (self.W + 2 * pad_x, self.H + 2 * pad_y))
            for ix in range(-1 if pad_x else 0, 2 if pad_x else 1):
                for iy in range(-1 if pad_y else 0, 2 if pad_y else 1):
                    wide.paste(image, (pad_x + ix * self.W, pad_y + iy * self.H))
            wide = wide.filter(ImageFilter.GaussianBlur(units * K))
            return wide.crop((pad_x, pad_y, pad_x + self.W, pad_y + self.H))
        return image.filter(ImageFilter.GaussianBlur(units * K))

    def noise(self, cells_x: int, cells_y: int, octaves: int = 3) -> np.ndarray:
        """Noise 0..1 that repeats with the tile."""
        total = np.zeros((self.H, self.W), dtype=np.float32)
        amplitude, norm = 1.0, 0.0
        for octave in range(octaves):
            cx, cy = cells_x * 2**octave, cells_y * 2**octave
            grid = self.np_rng.random((cy, cx), dtype=np.float32)
            fx, fy = self.x / self.w * cx, self.y / self.h * cy
            x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
            tx, ty = fx - x0, fy - y0
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = grid[y0 % cy, x0 % cx]
            b = grid[y0 % cy, (x0 + 1) % cx]
            c = grid[(y0 + 1) % cy, x0 % cx]
            d = grid[(y0 + 1) % cy, (x0 + 1) % cx]
            total += ((a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty) * amplitude
            norm += amplitude
            amplitude *= 0.5
        return total / norm

    def profile(self, cells: int, octaves: int = 3) -> np.ndarray:
        """Noise 0..1 along x only, that repeats: one value for each column."""
        total = np.zeros(self.W, dtype=np.float32)
        amplitude, norm = 1.0, 0.0
        xs = (np.arange(self.W) + 0.5) / self.W
        for octave in range(octaves):
            c = cells * 2**octave
            grid = self.np_rng.random(c, dtype=np.float32)
            f = xs * c
            i = np.floor(f).astype(int)
            t = f - i
            t = t * t * (3 - 2 * t)
            total += (grid[i % c] * (1 - t) + grid[(i + 1) % c] * t) * amplitude
            norm += amplitude
            amplitude *= 0.5
        return total / norm

    # -- paint --------------------------------------------------------------

    def put(self, mask: np.ndarray, colour, alpha: float = 1.0) -> None:
        cover = np.clip(mask * alpha, 0.0, 1.0)
        out = cover + self.alpha * (1.0 - cover)
        weight = np.where(out > 1e-6, cover / np.maximum(out, 1e-6), 0.0)[:, :, None]
        self.rgb = self.rgb * (1.0 - weight) + np.asarray(colour, dtype=np.float32) * weight
        self.alpha = out

    def tone(self, amount: np.ndarray) -> None:
        """Make the colour lighter (amount over 0) or darker (under 0)."""
        self.rgb = np.clip(self.rgb * (1.0 + amount[:, :, None]), 0.0, 255.0)

    def publish(self, supersample: int = SUPERSAMPLE) -> Image.Image:
        """The picture to publish. It is made `supersample` times smaller
        than the work: a smaller number gives more pixels to the unit."""
        pre = np.dstack([self.rgb * self.alpha[:, :, None], self.alpha])
        s = supersample
        small = pre.reshape(self.H // s, s, self.W // s, s, 4).mean(axis=(1, 3))
        a = small[:, :, 3:4]
        # An empty pixel has the mean colour of the picture, so a sampler that
        # mixes it in adds no dark line.
        full = a[:, :, 0] > 0.5
        mean = (small[:, :, :3][full] / a[full]).mean(axis=0) if full.any() else np.zeros(3)
        colour = np.where(a > 4e-3, small[:, :, :3] / np.maximum(a, 1e-4), mean)
        out = np.dstack([np.clip(colour, 0, 255), np.clip(a * 255.0, 0, 255)])
        return Image.fromarray(np.rint(out).astype(np.uint8), "RGBA")


def _box(pen: ImageDraw.ImageDraw, dx: float, dy: float, x0: float, y0: float, x1: float, y1: float, value: int = 255) -> None:
    pen.rectangle([x0 * K + dx, y0 * K + dy, x1 * K + dx - 1, y1 * K + dy - 1], fill=value)


def _dot(pen: ImageDraw.ImageDraw, dx: float, dy: float, x: float, y: float, r: float, value: int = 255, ry: float | None = None) -> None:
    ry = r if ry is None else ry
    pen.ellipse([(x - r) * K + dx, (y - ry) * K + dy, (x + r) * K + dx, (y + ry) * K + dy], fill=value)


def _poly(pen: ImageDraw.ImageDraw, dx: float, dy: float, pts, value: int = 255) -> None:
    pen.polygon([(x * K + dx, y * K + dy) for x, y in pts], fill=value)


def _line(pen: ImageDraw.ImageDraw, dx: float, dy: float, pts, width: float, value: int = 255) -> None:
    pen.line([(x * K + dx, y * K + dy) for x, y in pts], fill=value, width=max(1, int(round(width * K))), joint="curve")


# ---------------------------------------------------------------------------
# Fills
# ---------------------------------------------------------------------------


def _courses(tile: Tile, skin: Skin, row_h: float, unit_w: float, joint: float, bevel: float) -> None:
    """Laid units in rows, each row half a unit along from the one above:
    bricks or cut blocks."""
    rows = int(round(tile.h / row_h))
    count = int(round(tile.w / unit_w))
    tile.put(np.ones_like(tile.alpha), skin.dark)
    for row in range(rows):
        for i in range(count):
            x0 = i * unit_w + (unit_w * 0.5 if row % 2 else 0.0)
            y0 = row * row_h
            tone = tile.rng.uniform(-0.16, 0.14)
            colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 1.6)
            body = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + joint, y0 + joint, x0 + unit_w - joint, y0 + row_h - joint))
            tile.put(body, colour)
            top = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + joint, y0 + joint, x0 + unit_w - joint, y0 + joint + bevel))
            left = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + joint, y0 + joint, x0 + joint + bevel, y0 + row_h - joint))
            tile.put(np.maximum(top, left), skin.light, 0.30)
            low = tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + joint, y0 + row_h - joint - bevel, x0 + unit_w - joint, y0 + row_h - joint))
            tile.put(low, skin.dark, 0.35)


def fill(skin: Skin) -> Image.Image:
    tile = Tile(FILL, True, True, skin.key, "fill")
    rng = tile.rng
    if skin.material == "panel":
        tile.put(np.ones_like(tile.alpha), skin.dark)
        for px in range(2):
            for py in range(2):
                x0, y0 = px * 32.0, py * 32.0
                tone = rng.uniform(-0.10, 0.10)
                colour = _mix(skin.base, skin.light if tone > 0 else skin.dark, abs(tone) * 2.0)
                tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 0.6, y0 + 0.6, x0 + 31.4, y0 + 31.4)), colour)
                edge = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.6, y0 + 0.6, x0 + 31.4, y0 + 1.2), _box(p, dx, dy, x0 + 0.6, y0 + 0.6, x0 + 1.2, y0 + 31.4)))
                tile.put(edge, skin.light, 0.38)
                low = tile.mask(lambda p, dx, dy: (_box(p, dx, dy, x0 + 0.6, y0 + 30.8, x0 + 31.4, y0 + 31.4), _box(p, dx, dy, x0 + 30.8, y0 + 0.6, x0 + 31.4, y0 + 31.4)))
                tile.put(low, skin.dark, 0.5)
                rivets = tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x0 + cx, y0 + cy, 0.75) for cx in (3.2, 28.8) for cy in (3.2, 28.8)])
                tile.put(rivets, skin.light, 0.55)
                kind = px + py * 2
                if kind == 0:
                    slats = tile.mask(lambda p, dx, dy: [_box(p, dx, dy, x0 + 8, y0 + 9 + k * 3.2, x0 + 24, y0 + 10.4 + k * 3.2) for k in range(5)])
                    tile.put(slats, skin.dark, 0.5)
                elif kind == 1:
                    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 7, y0 + 15.3, x0 + 25, y0 + 16.7)), skin.dark, 0.5)
                    tile.put(tile.mask(lambda p, dx, dy: _box(p, dx, dy, x0 + 21, y0 + 15.5, x0 + 24, y0 + 16.5)), skin.accent, 0.6)
                elif kind == 2:
                    tile.put(tile.mask(lambda p, dx, dy: _line(p, dx, dy, [(x0 + 6, y0 + 24), (x0 + 16, y0 + 24), (x0 + 22, y0 + 18), (x0 + 22, y0 + 7)], 0.8)), skin.dark, 0.4)
        tile.tone((tile.noise(4, 4, 3) - 0.5) * 0.14)
    elif skin.material == "brick":
        _courses(tile, skin, 8.0, 16.0, 0.45, 0.45)
        tile.tone((tile.noise(3, 3, 4) - 0.55) * 0.34)
    elif skin.material == "block":
        _courses(tile, skin, 16.0, 32.0, 0.5, 0.7)
        cracks = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(x, y), (x + a, y + 3), (x + a - 1.5, y + 7)], 0.3) for x, y, a in [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(-3, 3)) for _ in range(6)]])
        tile.put(cracks, skin.dark, 0.55)
        tile.tone((tile.noise(3, 3, 4) - 0.5) * 0.22)
    elif skin.material == "rock":
        # Broken stone: each pixel is in the cell of its nearest point, and
        # the cracks are where the two nearest points are as near.
        points = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(-0.2, 0.2)) for _ in range(16)]
        d1 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
        d2 = np.full(tile.alpha.shape, 1e9, dtype=np.float32)
        tone = np.zeros_like(d1)
        lit = np.zeros_like(d1)
        for px, py, t in points:
            ddx = (tile.x - px + 32.0) % 64.0 - 32.0
            ddy = (tile.y - py + 32.0) % 64.0 - 32.0
            d = np.sqrt(ddx * ddx + (ddy * 1.25) ** 2)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            tone = np.where(closer, t, tone)
            lit = np.where(closer, -(ddx + ddy) * 0.012, lit)
            d1 = np.where(closer, d, d1)
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone(tone + lit)
        crack = np.clip(1.0 - (d2 - d1) / 1.3, 0.0, 1.0)
        tile.put(crack, skin.dark, 0.85)
        tile.put(np.clip(1.0 - np.abs((d2 - d1) - 1.9) / 0.7, 0, 1) * (lit > 0), skin.light, 0.25)
        tile.tone((tile.noise(5, 5, 3) - 0.5) * 0.20)
    else:  # earth
        tile.put(np.ones_like(tile.alpha), skin.base)
        tile.tone((tile.noise(6, 6, 4) - 0.5) * 0.5)
        stones = [(rng.uniform(0, 64), rng.uniform(0, 64), rng.uniform(1.6, 4.2)) for _ in range(9)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y + 0.5, r, ry=r * 0.7) for x, y, r in stones]), skin.dark, 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, r * 0.92, ry=r * 0.62) for x, y, r in stones]), _mix(skin.light, (150, 150, 150), 0.3))
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x - r * 0.25, y - r * 0.2, r * 0.45, ry=r * 0.26) for x, y, r in stones]), (220, 220, 210), 0.22)
        roots = []
        for _ in range(5):
            x, y = rng.uniform(0, 64), rng.uniform(0, 64)
            pts = [(x, y)]
            for _ in range(6):
                x, y = x + rng.uniform(2, 6), y + rng.uniform(-3, 3)
                pts.append((x, y))
            roots.append(pts)
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.7) for pts in roots]), skin.light, 0.5)
        specks = [(rng.uniform(0, 64), rng.uniform(0, 64)) for _ in range(40)]
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, y, 0.4) for x, y in specks]), skin.dark, 0.6)
    return tile.publish()


# ---------------------------------------------------------------------------
# Caps
# ---------------------------------------------------------------------------


def cap(skin: Skin) -> Image.Image:
    tile = Tile(CAP, True, False, skin.key, "cap")
    rng = tile.rng
    s = CAP_SURFACE
    y = tile.y
    if skin.cap in ("strip", "plate", "edge"):
        thick = {"strip": 5.5, "plate": 5.0, "edge": 4.2}[skin.cap]
        body = ((y >= s) & (y < s + thick)).astype(np.float32)
        tile.put(body, skin.cap_colour)
        tile.put(((y >= s) & (y < s + 0.7)).astype(np.float32), _mix(skin.cap_colour, (255, 255, 255), 0.45))
        tile.put(((y >= s + thick - 0.8) & (y < s + thick)).astype(np.float32), skin.dark, 0.7)
        # The shade the cap throws on the block under it.
        tile.put(np.clip(1.0 - (y - s - thick) / 3.5, 0.0, 1.0) * (y >= s + thick), (0, 0, 0), 0.42)
        if skin.cap == "strip":
            tile.put(((y >= s + 1.7) & (y < s + 2.9)).astype(np.float32) * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16 + 1.5, 0, k * 16 + 14.5, 20) for k in range(4)]), skin.accent)
            tile.put(np.clip(1.0 - np.abs(y - s - 2.3) / 2.6, 0, 1) ** 2, skin.accent, 0.22)
            tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16 - 0.4, s, k * 16 + 0.4, s + thick) for k in range(5)]), skin.dark, 0.7)
        elif skin.cap == "plate":
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8 + 4, s + 2.6, 0.75) for k in range(8)]), _mix(skin.cap_colour, (255, 255, 255), 0.35))
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8 + 4.2, s + 2.9, 0.75) for k in range(8)]), skin.dark, 0.35)
            tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32 - 0.3, s, k * 32 + 0.3, s + thick) for k in range(3)]), skin.dark, 0.8)
            # Heat in the joints of the stone under the plate.
            seams = []
            for _ in range(3):
                x, yy = rng.uniform(0, 64), s + thick + rng.uniform(0.3, 1.0)
                pts = [(x, yy)]
                for _ in range(5):
                    x, yy = x + rng.uniform(-1.6, 1.6), yy + rng.uniform(0.8, 1.9)
                    pts.append((x, yy))
                seams.append(pts)
            glow = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.3) for pts in seams])
            fade = np.clip(1.0 - (y - s - thick) / 9.0, 0.0, 1.0)
            tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, 0.4) for pts in seams], blur=0.9) * fade, skin.accent, 0.45)
            tile.put(glow * fade, _mix(skin.accent, (255, 255, 220), 0.3), 0.7)
        else:
            tile.put(((y >= s) & (y < s + 0.9)).astype(np.float32), skin.accent)
            tile.put(np.clip(1.0 - np.abs(y - s - 0.4) / 3.0, 0, 1) ** 2, skin.accent, 0.30)
            signs = tile.mask(lambda p, dx, dy: [(_box(p, dx, dy, k * 8 + 2.5, s + 2.0, k * 8 + 5.5, s + 2.5) if k % 3 else _dot(p, dx, dy, k * 8 + 4, s + 2.4, 0.7)) for k in range(8)])
            tile.put(signs, skin.accent, 0.7)
    else:
        # Soft ground: a body that the surface cuts, with an uneven lower edge.
        depth = {"grass": (5.0, 6.0), "moss": (4.0, 9.0), "sand": (3.5, 2.5)}[skin.cap]
        lower = s + depth[0] + tile.profile(8, 3)[None, :] * depth[1]
        top = s - (tile.profile(16, 2)[None, :] - 0.5) * (1.0 if skin.cap != "sand" else 0.6)
        body = np.clip((lower - y) * K * 0.5 + 0.5, 0, 1) * np.clip((y - top) * K * 0.5 + 0.5, 0, 1)
        tile.put(np.clip((lower + 2.5 - y) / 2.5, 0, 1) * (y >= top), (0, 0, 0), 0.34)
        tile.put(body, skin.cap_colour)
        tile.tone((tile.noise(16, 5, 2) - 0.5) * 0.30 * (tile.alpha > 0))
        tile.put(body * np.clip((y - (lower - 2.2)) / 2.2, 0, 1), skin.dark, 0.5)
        tile.put(body * np.clip(1.0 - (y - top) / 1.2, 0, 1), _mix(skin.cap_colour, (255, 255, 235), 0.42), 0.8)
        if skin.cap == "grass":
            blades = []
            for _ in range(70):
                x = rng.uniform(0, 64)
                h = rng.uniform(1.6, 3.8)
                lean = rng.uniform(-1.0, 1.0)
                blades.append([(x - 0.45, s + 0.8), (x + 0.45, s + 0.8), (x + lean, s - h)])
            for shade, part in ((0.0, blades[::2]), (0.28, blades[1::2])):
                tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in part]), _mix(skin.cap_colour, (255, 255, 200), shade))
            flowers = [(rng.uniform(0, 64), s - rng.uniform(0.6, 2.2)) for _ in range(5)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.55) for x, yy in flowers]), skin.accent)
        elif skin.cap == "moss":
            lumps = [(rng.uniform(0, 64), s + rng.uniform(-0.3, 0.6), rng.uniform(1.2, 2.6)) for _ in range(22)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.6) for x, yy, r in lumps]), _mix(skin.cap_colour, (255, 255, 235), 0.2))
            lights = [(rng.uniform(0, 64), s + rng.uniform(1.5, 5.0)) for _ in range(7)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 1.3) for x, yy in lights], blur=0.5), skin.accent, 0.45)
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.42) for x, yy in lights]), _mix(skin.accent, (255, 255, 255), 0.4))
        else:
            pebbles = [(rng.uniform(0, 64), s + rng.uniform(1.0, 3.0), rng.uniform(0.35, 0.8)) for _ in range(12)]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, r, ry=r * 0.7) for x, yy, r in pebbles]), skin.dark, 0.45)
            tufts = []
            for _ in range(4):
                x = rng.uniform(0, 64)
                for k in range(4):
                    tufts.append([(x + k * 0.5 - 0.3, s + 0.6), (x + k * 0.5 + 0.3, s + 0.6), (x + k * 0.9 - 1.2, s - rng.uniform(1.5, 3.2))])
            tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, pts) for pts in tufts]), (96, 140, 110))
    return tile.publish()


# ---------------------------------------------------------------------------
# Undersides
# ---------------------------------------------------------------------------


def under(skin: Skin) -> Image.Image:
    tile = Tile(UNDER, True, False, skin.key, "under")
    rng = tile.rng
    e = UNDER_EDGE
    y = tile.y
    # The lower lip of the block is in shade.
    tile.put(np.clip(1.0 - (e - y) / e, 0.0, 1.0) * (y < e), (0, 0, 0), 0.5)
    rock, rock_light = skin.dark, _mix(skin.base, skin.light, 0.3)
    if skin.under == "pipes":
        tile.put(((y >= e + 0.8) & (y < e + 4.4)).astype(np.float32), _mix(skin.base, skin.dark, 0.3))
        tile.put(((y >= e + 1.1) & (y < e + 1.8)).astype(np.float32), skin.light, 0.7)
        tile.put(((y >= e + 3.6) & (y < e + 4.4)).astype(np.float32), skin.dark, 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16 + 2, e - 0.5, k * 16 + 4.2, e + 5.2) for k in range(4)]), _mix(skin.base, skin.light, 0.25))
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, 40, e + 4.4, 41.5, e + 7.5), _dot(p, dx, dy, 40.75, e + 8.2, 1.1)]), _mix(skin.base, skin.dark, 0.2))
        tile.put(tile.mask(lambda p, dx, dy: _dot(p, dx, dy, 40.75, e + 8.2, 0.45)), skin.accent)
    elif skin.under in ("stalactites", "spikes"):
        teeth = []
        x = 0.0
        while x < 64.0:
            w = 4.0 if skin.under == "spikes" else rng.uniform(2.6, 7.0)
            h = rng.uniform(4.5, 6.5) if skin.under == "spikes" else rng.uniform(2.5, 11.0)
            teeth.append((x, min(w, 64.0 - x) if 64.0 - x < 2.6 else w, h))
            x += w
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x0, e - 0.6), (x0 + w, e - 0.6), (x0 + w * 0.55, e + h)]) for x0, w, h in teeth]), rock)
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x0, e - 0.6), (x0 + w * 0.32, e - 0.6), (x0 + w * 0.55, e + h)]) for x0, w, h in teeth]), rock_light, 0.75)
        if skin.under == "stalactites":
            drops = [(x0 + w * 0.55, e + h + 0.5) for x0, w, h in teeth if h > 8.0]
            tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, x, yy, 0.45) for x, yy in drops]), skin.accent, 0.9)
    elif skin.under in ("roots", "weed"):
        weed = skin.under == "weed"
        colour = (34, 112, 92) if weed else _mix(skin.light, (120, 96, 70), 0.5)
        leaf = (70, 160, 120) if weed else _mix(skin.cap_colour, (255, 255, 220), 0.1)
        strands, leaves = [], []
        for _ in range(9):
            x = rng.uniform(0, 64)
            length = rng.uniform(4.0, 11.0)
            phase = rng.uniform(0, 6.28)
            pts = [(x + math.sin(phase + t * 0.5) * 0.9 * (t / 10.0), e - 0.8 + length * t / 10.0) for t in range(11)]
            strands.append((pts, rng.uniform(0.45, 0.8) if weed else rng.uniform(0.3, 0.6)))
            if weed:
                leaves.extend((px + (1.0 if k % 2 else -1.0), py, 1 if k % 2 else -1) for k, (px, py) in enumerate(pts[2::2]))
            elif rng.random() < 0.35:
                leaves.append((pts[-1][0], pts[-1][1], 1))
        tile.put(tile.mask(lambda p, dx, dy: [_line(p, dx, dy, pts, w) for pts, w in strands]), colour)
        tile.put(tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(x - s * 1.0, yy), (x + s * 0.9, yy - 0.5), (x + s * 0.9, yy + 0.5)]) for x, yy, s in leaves]), leaf)
    elif skin.under == "bolts":
        tile.put(((y >= e - 0.4) & (y < e + 2.6)).astype(np.float32), skin.cap_colour)
        tile.put(((y >= e - 0.4) & (y < e + 0.2)).astype(np.float32), _mix(skin.cap_colour, (255, 255, 255), 0.3))
        tile.put(((y >= e + 2.0) & (y < e + 2.6)).astype(np.float32), skin.dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 8 + 4, e + 1.1, 0.7) for k in range(8)]), _mix(skin.cap_colour, (255, 255, 255), 0.3))
        hooks = [(10.0, 4.5), (41.0, 6.5)]
        tile.put(tile.mask(lambda p, dx, dy: [[_dot(p, dx, dy, x, e + 2.8 + k * 1.3, 0.45, ry=0.7) for k in range(int(h))] for x, h in hooks]), skin.cap_colour)
        tile.put(np.clip(1.0 - (y - e - 2.6) / 5.0, 0, 1) ** 2 * (y >= e + 2.6), skin.accent, 0.16)
    else:  # lip
        tile.put(((y >= e - 0.3) & (y < e + 1.4)).astype(np.float32), _mix(skin.base, skin.dark, 0.5))
        tile.put(((y >= e + 0.9) & (y < e + 1.4)).astype(np.float32), skin.accent, 0.55)
        tile.put(np.clip(1.0 - (y - e - 1.4) / 4.0, 0, 1) ** 2 * (y >= e + 1.4), skin.accent, 0.16)
    return tile.publish()


def side(skin: Skin) -> Image.Image:
    tile = Tile(SIDE, False, True, skin.key, "side")
    x = tile.x
    tile.put(np.clip(1.0 - x / 9.0, 0.0, 1.0) ** 1.6, (0, 0, 0), 0.46)
    tile.put(((x >= 0.25) & (x < 0.85)).astype(np.float32), skin.light, 0.42)
    tile.put((x < 0.25).astype(np.float32), skin.dark, 0.8)
    return tile.publish()


# ---------------------------------------------------------------------------
# One-way platforms
# ---------------------------------------------------------------------------


def oneway(skin: Skin) -> Image.Image:
    tile = Tile(ONEWAY, True, False, skin.key, "oneway")
    rng = tile.rng
    y = tile.y
    if skin.oneway == "grate":
        metal = _mix(skin.cap_colour, skin.light, 0.35)
        tile.put((y < 3.4).astype(np.float32), metal)
        tile.put((y < 0.7).astype(np.float32), _mix(metal, (255, 255, 255), 0.5))
        tile.put(((y >= 1.3) & (y < 2.2)).astype(np.float32) * tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 8 + 1, 0, k * 8 + 7, 16) for k in range(8)]), skin.accent)
        tile.put(((y >= 2.8) & (y < 3.4)).astype(np.float32), skin.dark, 0.8)
        truss = tile.mask(lambda p, dx, dy: [_line(p, dx, dy, [(k * 8, 3.4), (k * 8 + 4, 9.2), (k * 8 + 8, 3.4)], 0.8) for k in range(8)])
        tile.put(truss, _mix(metal, skin.dark, 0.45))
        tile.put(((y >= 9.0) & (y < 10.2)).astype(np.float32), _mix(metal, skin.dark, 0.3))
        tile.put(np.clip(1.0 - (y - 10.2) / 3.0, 0, 1) * (y >= 10.2), (0, 0, 0), 0.22)
    elif skin.oneway == "plank":
        wood, wood_dark, wood_light = (126, 88, 54), (60, 38, 24), (178, 136, 88)
        wood = _mix(wood, skin.base, 0.25)
        tile.put((y < 5.6).astype(np.float32), wood)
        tile.tone((tile.noise(3, 10, 2) - 0.5) * 0.3 * (tile.alpha > 0))
        tile.put((y < 0.8).astype(np.float32), wood_light, 0.85)
        tile.put(((y >= 4.8) & (y < 5.6)).astype(np.float32), wood_dark, 0.8)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 16 - 0.3, 0, k * 16 + 0.3, 5.6) for k in range(5)]), wood_dark, 0.85)
        tile.put(tile.mask(lambda p, dx, dy: [_dot(p, dx, dy, k * 16 + s, 2.6, 0.5) for k in range(4) for s in (1.6, 14.4)]), wood_dark, 0.8)
        brackets = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(k * 32 + 14, 5.6), (k * 32 + 18, 5.6), (k * 32 + 18, 12.5), (k * 32 + 16.8, 12.5)]) for k in range(2)])
        tile.put(brackets, wood_dark)
        tile.put(np.clip(1.0 - (y - 5.6) / 3.0, 0, 1) * (y >= 5.6) * (1.0 - brackets), (0, 0, 0), 0.25)
    else:  # slab
        stone = _mix(skin.base, skin.light, 0.45)
        tile.put((y < 6.4).astype(np.float32), stone)
        tile.tone((tile.noise(6, 3, 3) - 0.5) * 0.16 * (tile.alpha > 0))
        tile.put((y < 0.8).astype(np.float32), _mix(stone, (255, 255, 255), 0.5))
        tile.put(((y >= 5.5) & (y < 6.4)).astype(np.float32), skin.dark, 0.7)
        tile.put(tile.mask(lambda p, dx, dy: [_box(p, dx, dy, k * 32 - 0.3, 0, k * 32 + 0.3, 6.4) for k in range(3)]), skin.dark, 0.7)
        corbels = tile.mask(lambda p, dx, dy: [_poly(p, dx, dy, [(k * 32 + 12, 6.4), (k * 32 + 20, 6.4), (k * 32 + 18, 10.5), (k * 32 + 14, 10.5)]) for k in range(2)])
        tile.put(corbels, _mix(skin.base, skin.dark, 0.3))
        tile.put(np.clip(1.0 - (y - 6.4) / 3.0, 0, 1) * (y >= 6.4) * (1.0 - corbels), (0, 0, 0), 0.22)
    del rng
    return tile.publish()


PARTS: dict[str, Callable[[Skin], Image.Image]] = {
    "fill": fill,
    "cap": cap,
    "under": under,
    "side": side,
    "oneway": oneway,
}


def mockup(skin: Skin, parts: dict[str, Image.Image], scale: int = 2) -> Image.Image:
    """A small made-up room in the skin, to look at without the game: a
    floor, a block in the air and a one-way platform, on the mean colour of
    a dark room."""
    w, h = 384, 216
    px = PX_PER_UNIT
    out = Image.new("RGBA", (w * px, h * px), (*_mix(skin.dark, (20, 24, 34), 0.55), 255))

    def lay(part: str, x0: float, y0: float, bw: float, bh: float, flip: bool = False) -> None:
        tile = parts[part]
        if flip:
            tile = tile.transpose(Image.FLIP_LEFT_RIGHT)
        strip = Image.new("RGBA", (int(bw * px), int(bh * px)))
        for tx in range(0, strip.width, tile.width):
            for ty in range(0, strip.height, tile.height):
                strip.paste(tile, (tx, ty))
        out.alpha_composite(strip, (int(x0 * px), int(y0 * px)))

    for x0, y0, bw, bh in ((0, 160, 384, 56), (200, 70, 120, 40), (0, 40, 40, 120)):
        lay("fill", x0, y0, bw, bh)
        lay("side", x0, y0, SIDE[0], bh)
        lay("side", x0 + bw - SIDE[0], y0, SIDE[0], bh, flip=True)
        if y0 + bh < h:
            lay("under", x0, y0 + bh - UNDER_EDGE, bw, UNDER[1])
        lay("cap", x0, y0 - CAP_SURFACE, bw, CAP[1])
    lay("oneway", 70, 110, 96, 16)
    return out.resize((out.width * scale // px, out.height * scale // px), Image.LANCZOS)
