"""The town kit: parts of the houses of the Math town, drawn in world units.

A `Canvas` is a window of the world (an origin, a size in units, and pixels to
the unit); a `Pen` draws masks on it in world units; a `Kit` paints walls,
roofs, windows, doors, balconies, awnings, signs and lamps in one light. It
was made for the town's look-dev (`untracked/art-candidates/town/`) and the
house fronts of `math_town_facades` are drawn with it.

Form shading (the shade of an eave on its own wall, a set-back window) is
architecture, not a drop shadow: nothing here paints a shadow on the ground.
"""

from __future__ import annotations

import hashlib
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

#: A canvas's default size in world units, its pixels to the unit, and its
#: supersample.
VIEW_W, VIEW_H = 640, 360
PPU = 2.5
S = 2
#: The floor doors and lamps stand on, until a caller sets `Kit.ground`.
GROUND = 0.0


def _seed(*parts) -> int:
    return int.from_bytes(hashlib.blake2b(":".join(map(str, parts)).encode(), digest_size=8).digest(), "little")


def mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def scale(c, k):
    return tuple(max(0, min(255, int(round(x * k)))) for x in c)


class Pen:
    """Draws in world units on a mask whose top left is the world point `o`."""

    def __init__(self, draw: ImageDraw.ImageDraw, k: float, value: int = 255, o=(0.0, 0.0)):
        self.d, self.k, self.value = draw, k, value
        self.ox, self.oy = o

    def _p(self, pts):
        return [((x - self.ox) * self.k, (y - self.oy) * self.k) for x, y in pts]

    def _x(self, x):
        return (x - self.ox) * self.k

    def _y(self, y):
        return (y - self.oy) * self.k

    def rect(self, x0, y0, x1, y1, value=None):
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        if x1 - x0 <= 0 or y1 - y0 <= 0:
            return
        self.d.rectangle([self._x(x0), self._y(y0), max(self._x(x0), self._x(x1) - 1), max(self._y(y0), self._y(y1) - 1)], fill=self.value if value is None else value)

    def poly(self, pts, value=None):
        self.d.polygon(self._p(pts), fill=self.value if value is None else value)

    def ellipse(self, cx, cy, rx, ry=None, value=None):
        ry = rx if ry is None else ry
        self.d.ellipse([self._x(cx - rx), self._y(cy - ry), self._x(cx + rx), self._y(cy + ry)], fill=self.value if value is None else value)

    def line(self, pts, width, value=None):
        self.d.line(self._p(pts), fill=self.value if value is None else value, width=max(1, int(round(width * self.k))), joint="curve")

    def ring(self, cx, cy, r, width, value=None):
        self.d.ellipse([self._x(cx - r), self._y(cy - r), self._x(cx + r), self._y(cy + r)], outline=self.value if value is None else value, width=max(1, int(round(width * self.k))))

    def arch(self, x0, y0, x1, y1, value=None):
        """A box with a half-round top: `y0` is the top of the round."""
        r = (x1 - x0) / 2.0
        self.rect(x0, y0 + r, x1, y1, value)
        self.ellipse((x0 + x1) / 2.0, y0 + r, r, r, value)


class Canvas:
    def __init__(self, tag: str, w=VIEW_W, h=VIEW_H, origin=(0.0, 0.0), ppu=PPU):
        self.tag = tag
        self.k = ppu * S
        self.o = origin
        self.W, self.H = int(w * self.k), int(h * self.k)
        self.rgb = np.zeros((self.H, self.W, 3), np.float32)
        self.alpha = np.zeros((self.H, self.W), np.float32)
        ys, xs = np.mgrid[0 : self.H, 0 : self.W]
        self.x = (xs + 0.5) / self.k + origin[0]
        self.y = (ys + 0.5) / self.k + origin[1]

    def rand(self, *tag) -> random.Random:
        return random.Random(_seed(self.tag, *tag))

    def mask(self, draw, blur: float = 0.0) -> np.ndarray:
        img = Image.new("L", (self.W, self.H), 0)
        draw(Pen(ImageDraw.Draw(img), self.k, o=self.o))
        if blur > 0:
            img = img.filter(ImageFilter.GaussianBlur(blur * self.k))
        return np.asarray(img, np.float32) / 255.0

    def soften(self, m: np.ndarray, blur: float) -> np.ndarray:
        img = Image.fromarray(np.clip(m * 255, 0, 255).astype(np.uint8), "L")
        return np.asarray(img.filter(ImageFilter.GaussianBlur(blur * self.k)), np.float32) / 255.0

    def noise(self, tag, cells_x: float, cells_y: float, octaves: int = 3) -> np.ndarray:
        rng = np.random.default_rng(_seed(self.tag, "noise", tag) % 2**63)
        total = np.zeros((self.H, self.W), np.float32)
        amp, norm = 1.0, 0.0
        for o in range(octaves):
            gx, gy = max(2, int(cells_x * 2**o) + 2), max(2, int(cells_y * 2**o) + 2)
            grid = (rng.random((gy, gx)) * 255).astype(np.uint8)
            total += np.asarray(Image.fromarray(grid, "L").resize((self.W, self.H), Image.BICUBIC), np.float32) / 255.0 * amp
            norm += amp
            amp *= 0.5
        total /= norm
        lo, hi = total.min(), total.max()
        return (total - lo) / max(hi - lo, 1e-6)

    @staticmethod
    def _box(m):
        """The slices of the part of `m` that is not zero: paint only there."""
        m = np.asarray(m, np.float32)
        rows = np.flatnonzero(np.any(m != 0, axis=1))
        if rows.size == 0:
            return m, None
        cols = np.flatnonzero(np.any(m[rows[0] : rows[-1] + 1] != 0, axis=0))
        return m, (slice(rows[0], rows[-1] + 1), slice(cols[0], cols[-1] + 1))

    def put(self, m, colour, a: float = 1.0):
        m, sl = self._box(m)
        if sl is None:
            return
        cover = np.clip(m[sl] * a, 0, 1)
        alpha = self.alpha[sl]
        out = cover + alpha * (1 - cover)
        w = np.where(out > 1e-6, cover / np.maximum(out, 1e-6), 0)[:, :, None]
        paint = np.asarray(colour, np.float32)
        self.rgb[sl] = self.rgb[sl] * (1 - w) + paint * w
        self.alpha[sl] = out

    def paint(self, m, paint_rgb: np.ndarray, a: float = 1.0):
        """`put` with a per-pixel colour (H, W, 3)."""
        m, sl = self._box(m)
        if sl is None:
            return
        cover = np.clip(m[sl] * a, 0, 1)
        alpha = self.alpha[sl]
        out = cover + alpha * (1 - cover)
        w = np.where(out > 1e-6, cover / np.maximum(out, 1e-6), 0)[:, :, None]
        self.rgb[sl] = self.rgb[sl] * (1 - w) + paint_rgb[sl] * w
        self.alpha[sl] = out

    def tone(self, m, amount: float):
        """Lighter (amount > 0) or darker (< 0) where `m` is."""
        m, sl = self._box(m)
        if sl is None:
            return
        self.rgb[sl] = np.clip(self.rgb[sl] * (1 + np.clip(m[sl], -1, 1)[:, :, None] * amount), 0, 255)

    def light(self, m, colour, strength=1.0):
        m, sl = self._box(m)
        if sl is None:
            return
        k = np.clip(m[sl] * strength, 0, 1)[:, :, None]
        c = np.asarray(colour, np.float32) / 255.0
        base = self.rgb[sl] / 255.0
        self.rgb[sl] = (1 - (1 - base) * (1 - c * k)) * 255.0

    def tint(self, m, colour, k):
        m, sl = self._box(m)
        if sl is None:
            return
        kk = np.clip(m[sl] * k, 0, 1)[:, :, None]
        self.rgb[sl] = self.rgb[sl] * (1 - kk) + np.asarray(colour, np.float32) * kk

    def ramp(self, stops):
        vs = np.array([s[0] for s in stops], np.float32)
        out = np.zeros((self.H, self.W, 3), np.float32)
        col = self.y[:, 0]
        for ch in range(3):
            out[:, :, ch] = np.interp(col, vs, np.array([s[1][ch] for s in stops], np.float32))[:, None]
        return out

    def image(self) -> Image.Image:
        pre = np.dstack([self.rgb * self.alpha[:, :, None], self.alpha])
        small = pre.reshape(self.H // S, S, self.W // S, S, 4).mean(axis=(1, 3))
        a = small[:, :, 3:4]
        col = small[:, :, :3] / np.maximum(a, 1e-4)
        dither = np.random.default_rng(1).random(col.shape[:2] + (1,)) - 0.5
        out = np.dstack([np.clip(col + dither, 0, 255), np.clip(a * 255, 0, 255)])
        return Image.fromarray(np.rint(out).astype(np.uint8), "RGBA")


def box(x0, y0, x1, y1):
    return lambda p: p.rect(x0, y0, x1, y1)


# ---------------------------------------------------------------------------
# The kit: parts of a house
# ---------------------------------------------------------------------------


class Kit:
    """Paints parts of a town on a canvas, in one light: the sun comes from
    `sun` (-1 left, 1 right) and above."""

    def __init__(self, c: Canvas, pal: dict, sun: float = -1.0):
        self.c, self.p, self.sun = c, pal, sun
        #: The floor that doors and lamps stand on; a terrace sets its own.
        self.ground = GROUND

    # -- walls --------------------------------------------------------------

    def wall(self, x0, y0, x1, y1, colour, texture="plaster", tag="wall"):
        c = self.c
        m = c.mask(box(x0, y0, x1, y1))
        c.put(m, colour)
        if texture == "plaster":
            n = c.noise((tag, "plaster"), 10, 6, 4)
            c.tone(m * (n - 0.5), 0.16)
            # Worn patches where the stone under shows.
            rng = c.rand(tag, "patches")
            patches = c.mask(lambda p: [p.ellipse(rng.uniform(x0 + 8, x1 - 8), rng.uniform(y0 + 10, y1 - 6), rng.uniform(4, 9), rng.uniform(2.5, 5)) for _ in range(int((x1 - x0) * (y1 - y0) / 2600))], blur=0.6)
            c.put(patches * m, mix(colour, self.p["stone"], 0.55), 0.55)
            c.tone(patches * m * c.noise((tag, "patchn"), 40, 40, 2), -0.12)
        elif texture in ("stone", "limestone"):
            rng = c.rand(tag, "courses")
            rows = []
            y = y1
            while y > y0:
                h = rng.choice([9.0, 11.0, 13.0]) if texture == "stone" else 12.0
                rows.append((max(y0, y - h), y))
                y -= h
            for i, (ry0, ry1) in enumerate(rows):
                x = x0 - rng.uniform(0, 14)
                while x < x1:
                    w = rng.uniform(14, 26) if texture == "stone" else 24.0
                    sx0, sx1 = max(x0, x + 0.6), min(x1, x + w - 0.6)
                    if sx1 > sx0 + 1:
                        sm = c.mask(box(sx0, ry0 + 0.6, sx1, ry1 - 0.6), blur=0.25)
                        c.tone(sm, rng.uniform(-0.08, 0.08))
                        c.put(sm * c.mask(box(sx0, ry0 + 0.6, sx1, ry0 + 1.6)), self.p["stone_light"], 0.25)
                    x += w + (12 if texture == "limestone" and i % 2 else 0) * 0
                # joints
            joints = c.mask(lambda p: [p.rect(x0, ry0, x1, ry0 + 0.7) for ry0, _ in rows])
            c.put(joints * m, scale(colour, 0.72), 0.55)
            n = c.noise((tag, "stone"), 16, 10, 3)
            c.tone(m * (n - 0.5), 0.12)
        elif texture == "brick":
            rows = int((y1 - y0) / 4.5)
            joints = c.mask(lambda p: [p.rect(x0, y1 - k * 4.5, x1, y1 - k * 4.5 + 0.6) for k in range(rows + 1)])
            c.put(joints * m, mix(colour, (230, 220, 200), 0.35), 0.5)
            n = c.noise((tag, "brick"), 30, 40, 2)
            c.tone(m * (n - 0.5), 0.2)
        # The face of the wall is lit by the sky from above, less near the ground.
        c.tone(m * np.clip((c.y - y0) / max(1.0, y1 - y0), 0, 1), -0.10)
        return m

    def timber(self, x0, y0, x1, y1, colour, posts=4, braces=True, tag="timber"):
        """A frame of dark beams on a plaster wall: sill, head, posts, braces."""
        c = self.c
        w = 3.2
        xs = [x0 + (x1 - x0) * i / posts for i in range(posts + 1)]
        rng = c.rand(tag, "braces")

        def draw(p):
            p.rect(x0, y0, x1, y0 + w)
            p.rect(x0, y1 - w, x1, y1)
            for x in xs:
                p.rect(max(x0, x - w / 2), y0, min(x1, x + w / 2), y1)
            if braces:
                for a, b in zip(xs, xs[1:]):
                    if rng.random() < 0.6:
                        if rng.random() < 0.5:
                            p.line([(a + 1, y1 - 2), (b - 1, y0 + 2)], w * 0.8)
                        else:
                            p.line([(a + 1, y0 + 2), (b - 1, y1 - 2)], w * 0.8)

        m = c.mask(draw)
        c.put(m, colour)
        c.tone(m * (c.noise((tag, "grain"), 4, 60, 2) - 0.5), 0.35)
        c.put(m * self.c.mask(lambda p: [p.rect(x0, y0, x1, y0 + 0.8)]), mix(colour, (255, 230, 190), 0.35), 0.6)
        return m

    def eave_shade(self, x0, x1, y, depth=6.0, k=0.32):
        """The form shade a roof's overhang makes on its own wall."""
        c = self.c
        band = np.clip(1 - (c.y - y) / depth, 0, 1) * (c.y >= y) * (c.x >= x0) * (c.x <= x1)
        c.tone(band.astype(np.float32), -k)

    # -- roofs --------------------------------------------------------------

    def gable(self, x0, x1, eave_y, peak, colour, tiles="clay", overhang=8.0, tag="roof", walk=False):
        """A gable seen from the front: a triangle of roof over the wall,
        with its tiles in rows."""
        c = self.c
        cx = (x0 + x1) / 2
        pts = [(x0 - overhang, eave_y), (x1 + overhang, eave_y), (cx, eave_y - peak)]
        m = c.mask(lambda p: p.poly(pts))
        c.put(m, colour)
        self._tiles(m, x0 - overhang, x1 + overhang, eave_y - peak, eave_y, colour, tiles, tag)
        # The barge boards: the light edge of the roof, sun side brighter.
        left = [(x0 - overhang, eave_y), (cx, eave_y - peak)]
        right = [(cx, eave_y - peak), (x1 + overhang, eave_y)]
        lit, dark = (left, right) if self.sun < 0 else (right, left)
        c.put(c.mask(lambda p: p.line(lit, 2.6)), mix(colour, (255, 236, 200), 0.45))
        c.put(c.mask(lambda p: p.line(dark, 2.6)), scale(colour, 0.7))
        c.put(c.mask(box(x0 - overhang, eave_y - 1.2, x1 + overhang, eave_y + 1.6)), scale(colour, 0.55))
        return m

    def hipped(self, x0, x1, eave_y, h, colour, tiles="clay", overhang=8.0, inset=0.35, tag="roof"):
        """A roof whose slope faces us: a trapezoid, its ridge `h` above the eave."""
        c = self.c
        w = x1 - x0
        pts = [(x0 - overhang, eave_y), (x1 + overhang, eave_y), (x1 - w * inset, eave_y - h), (x0 + w * inset, eave_y - h)]
        m = c.mask(lambda p: p.poly(pts))
        c.put(m, colour)
        self._tiles(m, x0 - overhang, x1 + overhang, eave_y - h, eave_y, colour, tiles, tag)
        c.put(c.mask(box(x0 + w * inset, eave_y - h - 1.2, x1 - w * inset, eave_y - h + 1.0)), mix(colour, (255, 236, 200), 0.4))
        c.put(c.mask(box(x0 - overhang, eave_y - 1.2, x1 + overhang, eave_y + 1.6)), scale(colour, 0.55))
        # The near slope faces the sky: lighter at the ridge.
        c.tone(m * np.clip((eave_y - c.y) / h, 0, 1), 0.12)
        return m

    def _tiles(self, m, x0, x1, top, bottom, colour, tiles, tag):
        c = self.c
        rng = c.rand(tag, "tiles")
        if tiles == "clay":
            # Barrel tiles: columns of round tops, rows of lips.
            rows = c.mask(lambda p: [p.rect(x0, y, x1, y + 0.9) for y in np.arange(bottom - 5.0, top, -5.0)])
            c.put(rows * m, scale(colour, 0.62), 0.8)
            cols = np.abs(((c.x - x0) % 5.0) - 2.5) / 2.5
            c.tone(m * (0.5 - cols), 0.28)
            c.tone(m * (c.noise((tag, "clay"), 30, 20, 2) - 0.5), 0.22)
        elif tiles == "slate":
            rows = c.mask(lambda p: [p.rect(x0, y, x1, y + 0.6) for y in np.arange(bottom - 3.6, top, -3.6)])
            c.put(rows * m, scale(colour, 0.6), 0.85)
            # Slates staggered: vertical joints each row.
            def joints(p):
                for i, y in enumerate(np.arange(bottom - 3.6, top - 3.6, -3.6)):
                    off = (i % 2) * 3.0
                    for x in np.arange(x0 + off, x1, 6.0):
                        p.rect(x, y, x + 0.45, y + 3.6)
            c.put(c.mask(joints) * m, scale(colour, 0.65), 0.6)
            n = c.noise((tag, "slate"), 40, 30, 2)
            c.tone(m * (n - 0.5), 0.25)
        elif tiles == "hex":
            # A tessellation of hexagonal tiles, every seventh glazed.
            r = 3.4
            dx, dy = r * 1.732, r * 1.5

            def hexes(p, glazed=False):
                j = 0
                for row, y in enumerate(np.arange(top - r, bottom + r, dy)):
                    for x in np.arange(x0 - r + (row % 2) * dx / 2, x1 + r, dx):
                        j += 1
                        if glazed != (j % 7 == 0):
                            continue
                        pts = [(x + r * 0.92 * math.cos(math.radians(30 + 60 * k)), y + r * 0.92 * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
                        p.poly(pts)

            c.put(m, scale(colour, 0.6))
            c.put(c.mask(hexes) * m, colour)
            c.put(c.mask(lambda p: hexes(p, True)) * m, self.p["glaze"])
            c.tone(m * (c.noise((tag, "hex"), 30, 20, 2) - 0.5), 0.15)

    # -- openings -----------------------------------------------------------

    def glass(self, m, lit: float, top: float, bottom: float, tag):
        """Glass in `m`: the sky in it by day, a warm room at `lit`."""
        c = self.c
        sky = c.ramp([(top, self.p["glass_top"]), (bottom, self.p["glass_low"])])
        c.paint(m, sky)
        if lit > 0:
            warm = c.ramp([(top, self.p["lamp"]), (bottom, mix(self.p["lamp"], (120, 60, 30), 0.5))])
            c.paint(m, warm, lit)
        # A glint across the pane.
        streak = np.clip(1 - np.abs((c.x + c.y * 0.9) % 23.0 - 6.0) / 2.2, 0, 1)
        c.light(m * streak, (255, 255, 255), 0.18 * (1 - lit))

    def window(self, cx, y_top, w, h, kind="rect", shutters=None, lit=0.0, frame=None, sill=True, bars=True, flowers=None, tag="win"):
        c = self.c
        frame = frame or self.p["trim"]
        x0, x1, y1 = cx - w / 2, cx + w / 2, y_top + h
        f = 2.2
        if kind == "arch":
            outer = c.mask(lambda p: p.arch(x0 - f, y_top - f, x1 + f, y1 + f))
            inner = c.mask(lambda p: p.arch(x0, y_top, x1, y1))
        elif kind == "round":
            outer = c.mask(lambda p: p.ellipse(cx, y_top + h / 2, w / 2 + f, h / 2 + f))
            inner = c.mask(lambda p: p.ellipse(cx, y_top + h / 2, w / 2, h / 2))
        else:
            outer = c.mask(box(x0 - f, y_top - f, x1 + f, y1 + f))
            inner = c.mask(box(x0, y_top, x1, y1))
        if shutters:
            sw = w * 0.5
            for sx0, sx1 in ((x0 - f - sw, x0 - f), (x1 + f, x1 + f + sw)):
                sm = c.mask(box(sx0, y_top - 1, sx1, y1 + 1))
                c.put(sm, shutters)
                slats = c.mask(lambda p: [p.rect(sx0 + 1.2, y, sx1 - 1.2, y + 0.6) for y in np.arange(y_top + 2, y1, 2.4)])
                c.put(slats * sm, scale(shutters, 0.7), 0.8)
                c.put(c.mask(box(sx0, y_top - 1, sx1, y_top + 0.4)), mix(shutters, (255, 255, 255), 0.35), 0.7)
        c.put(outer, frame)
        c.put(outer * (1 - inner) * c.mask(box(x0 - f, y_top - f, x1 + f, y_top - f + 0.8)), mix(frame, (255, 255, 255), 0.4), 0.7)
        # The reveal: the glass is set back, so its top and sun-side edge are in shade.
        c.put(inner, scale(self.p["dark"], 1.0))
        g = c.mask(box(x0 + 1.4, y_top + 1.6, x1 - 1.0, y1 - 0.4)) * inner if kind != "round" else c.mask(lambda p: p.ellipse(cx, y_top + h / 2, w / 2 - 1.2, h / 2 - 1.2))
        if kind == "arch":
            g = c.mask(lambda p: p.arch(x0 + 1.2, y_top + 1.4, x1 - 1.2, y1 - 0.4))
        self.glass(g, lit, y_top, y1, tag)
        if bars:
            def mullions(p):
                if kind == "round":
                    p.rect(cx - 0.5, y_top, cx + 0.5, y1)
                    p.rect(x0, y_top + h / 2 - 0.5, x1, y_top + h / 2 + 0.5)
                else:
                    p.rect(cx - 0.6, y_top, cx + 0.6, y1)
                    p.rect(x0, y_top + h * 0.42, x1, y_top + h * 0.42 + 1.0)
            c.put(c.mask(mullions) * inner, frame)
        if sill:
            c.put(c.mask(box(x0 - f - 1.6, y1 + f - 0.4, x1 + f + 1.6, y1 + f + 2.0)), mix(frame, (255, 255, 255), 0.25))
            c.put(c.mask(box(x0 - f - 1.6, y1 + f + 1.4, x1 + f + 1.6, y1 + f + 2.0)), scale(frame, 0.6))
        if flowers:
            self.flowerbox(x0 - 1, x1 + 1, y1 + f + 2.0, flowers, tag)

    def flowerbox(self, x0, x1, y, blooms, tag):
        c = self.c
        rng = c.rand(tag, "flowers")
        c.put(c.mask(box(x0, y, x1, y + 4.0)), self.p["wood"])
        c.put(c.mask(box(x0, y, x1, y + 0.8)), mix(self.p["wood"], (255, 230, 190), 0.3))
        leaves = c.mask(lambda p: [p.ellipse(rng.uniform(x0, x1), y - rng.uniform(0, 2.5), rng.uniform(1.4, 2.6), rng.uniform(1.0, 1.8)) for _ in range(int((x1 - x0) * 0.9))])
        c.put(leaves, self.p["leaf"])
        c.tone(leaves * c.noise((tag, "leafn"), 80, 80, 1), 0.2)
        dots = c.mask(lambda p: [p.ellipse(rng.uniform(x0 + 1, x1 - 1), y - rng.uniform(0.5, 3.5), 1.0) for _ in range(int((x1 - x0) * 0.35))])
        c.put(dots, blooms)
        # Trailing leaves over the edge.
        trail = c.mask(lambda p: [p.line([(x, y + 3), (x + rng.uniform(-1, 1), y + rng.uniform(5, 10))], 1.1) for x in np.arange(x0 + 2, x1, rng.uniform(3, 5))])
        c.put(trail, scale(self.p["leaf"], 0.85))

    def door(self, cx, w, h, colour, arch=True, step=True, glass_lit=0.0, number=None, tag="door"):
        c = self.c
        x0, x1 = cx - w / 2, cx + w / 2
        y0 = self.ground - h
        f = 3.0
        surround = c.mask(lambda p: (p.arch(x0 - f, y0 - f, x1 + f, self.ground) if arch else p.rect(x0 - f, y0 - f, x1 + f, self.ground)))
        c.put(surround, self.p["trim"])
        c.put(surround * c.mask(box(x0 - f, y0 - f, x0 - f + 1.0, self.ground)), mix(self.p["trim"], (255, 255, 255), 0.35), 0.6)
        leaf = c.mask(lambda p: (p.arch(x0, y0, x1, self.ground) if arch else p.rect(x0, y0, x1, self.ground)))
        c.put(leaf, colour)
        # Boards and panels.
        c.put(c.mask(lambda p: [p.rect(x, y0, x + 0.5, self.ground) for x in np.arange(x0 + w / 4, x1, w / 4)]) * leaf, scale(colour, 0.7), 0.8)
        c.tone(leaf * (c.noise((tag, "grain"), 6, 50, 2) - 0.5), 0.3)
        # The leaf is set back: shade along the top and sun-side jamb.
        jamb = c.mask(box(x0, y0, x0 + 2.4, self.ground) if self.sun < 0 else box(x1 - 2.4, y0, x1, self.ground))
        c.tone(leaf * jamb, -0.35)
        c.tone(leaf * np.clip(1 - (c.y - y0 - (w / 2 if arch else 0)) / 6.0, 0, 1), -0.25)
        # A fanlight or a small window.
        if arch:
            fan = c.mask(lambda p: p.ellipse(cx, y0 + w / 2, w / 2 - 2.0, w / 2 - 2.0)) * c.mask(box(x0, y0, x1, y0 + w / 2))
            self.glass(fan, glass_lit, y0, y0 + w / 2, tag)
            c.put(c.mask(lambda p: [p.line([(cx, y0 + w / 2), (cx + (w / 2 - 2) * math.cos(math.radians(a)), y0 + w / 2 - (w / 2 - 2) * math.sin(math.radians(a)))], 0.7) for a in (30, 60, 90, 120, 150)]) * fan, self.p["trim"])
            c.put(c.mask(box(x0, y0 + w / 2 - 0.6, x1, y0 + w / 2 + 0.8)), self.p["trim"])
        # Knob and plate.
        kx = x1 - 4.0 if self.sun < 0 else x0 + 4.0
        c.put(c.mask(lambda p: p.ellipse(kx, self.ground - h * 0.45, 1.2)), self.p["brass"])
        if number:
            c.put(c.mask(lambda p: p.ellipse(cx, y0 + h * (0.42 if arch else 0.2), 2.6)), self.p["brass"])
        if step:
            c.put(c.mask(box(x0 - f - 3, self.ground - 3.0, x1 + f + 3, self.ground)), self.p["stone_light"])
            c.put(c.mask(box(x0 - f - 3, self.ground - 3.0, x1 + f + 3, self.ground - 2.3)), mix(self.p["stone_light"], (255, 255, 255), 0.4))

    # -- things on the street ------------------------------------------------

    def balcony(self, x0, x1, y, colour, rail=None):
        """A balcony a body can stand on: its floor's top edge is the one
        light line (walkable), the rail is thin and behind the play."""
        c = self.c
        rail = rail or self.p["iron"]
        c.put(c.mask(box(x0, y, x1, y + 3.4)), colour)
        c.put(c.mask(box(x0, y, x1, y + 0.9)), mix(colour, (255, 255, 240), 0.55))
        c.put(c.mask(lambda p: [p.poly([(x, y + 3.4), (x + 3, y + 3.4), (x + 1.5, y + 9)]) for x in np.arange(x0 + 4, x1 - 4, 14)]), scale(colour, 0.7))
        bars = c.mask(lambda p: ([p.rect(x, y - 13, x + 0.8, y) for x in np.arange(x0 + 1, x1, 3.2)], p.rect(x0, y - 14, x1, y - 12.6), p.rect(x0, y - 4, x1, y - 3.2)))
        c.put(bars, rail, 0.9)

    def awning(self, x0, x1, y, depth, colours, tag="awning"):
        c = self.c
        stripe = 5.0
        m = c.mask(lambda p: p.poly([(x0, y), (x1, y), (x1 + 3, y + depth), (x0 - 3, y + depth)]))
        band = ((c.x - x0) // stripe % 2).astype(np.float32)
        c.put(m, colours[0])
        c.put(m * band, colours[1])
        c.tone(m * np.clip((c.y - y) / depth, 0, 1), -0.18)
        # Scalloped valance.
        val = c.mask(lambda p: [p.ellipse(x + stripe / 2, y + depth, stripe / 2, 2.4) for x in np.arange(x0 - 3, x1 + 3, stripe)])
        c.put(val, colours[0])
        c.put(val * band, colours[1])
        c.tone(val, -0.12)

    def lamp(self, x, h=70, colour=None, lit=0.0, tag="lamp"):
        c = self.c
        colour = colour or self.p["iron"]
        c.put(c.mask(lambda p: (p.rect(x - 1.1, self.ground - h, x + 1.1, self.ground), p.rect(x - 2.6, self.ground - 4, x + 2.6, self.ground), p.rect(x - 1.8, self.ground - 9, x + 1.8, self.ground - 4))), colour)
        # The arm and the lantern.
        c.put(c.mask(lambda p: (p.line([(x, self.ground - h + 6), (x + 7, self.ground - h + 2), (x + 10, self.ground - h + 3)], 1.0))), colour)
        lx, ly = x + 10, self.ground - h + 4
        cage = c.mask(lambda p: p.poly([(lx - 3.4, ly), (lx + 3.4, ly), (lx + 2.4, ly + 8), (lx - 2.4, ly + 8)]))
        c.put(cage, colour)
        pane = c.mask(lambda p: p.poly([(lx - 2.4, ly + 1), (lx + 2.4, ly + 1), (lx + 1.7, ly + 7), (lx - 1.7, ly + 7)]))
        c.put(pane, mix(self.p["lamp"], (255, 255, 230), 0.4) if lit > 0 else self.p["glass_low"])
        c.put(c.mask(lambda p: p.poly([(lx - 4.2, ly), (lx + 4.2, ly), (lx, ly - 3.4)])), colour)
        if lit > 0:
            c.light(c.mask(lambda p: p.ellipse(lx, ly + 4, 3), blur=9), self.p["lamp"], lit)
            c.light(c.mask(lambda p: p.ellipse(lx, ly + 4, 22, 22), blur=14), self.p["lamp"], lit * 0.35)

    def sign(self, x, y, w, h, colour, glyph="circle", tag="sign"):
        """A hanging sign on an iron bracket, painted with a sign of its trade."""
        c = self.c
        c.put(c.mask(lambda p: (p.line([(x - 2, y - 6), (x + w + 2, y - 6)], 1.2), p.line([(x - 2, y - 6), (x + 6, y - 14)], 0.8))), self.p["iron"])
        c.put(c.mask(lambda p: [p.line([(xx, y - 6), (xx, y)], 0.5) for xx in (x + 3, x + w - 3)]), self.p["iron"])
        board = c.mask(box(x, y, x + w, y + h))
        c.put(board, colour)
        c.put(c.mask(box(x, y, x + w, y + 0.9)), mix(colour, (255, 255, 255), 0.35), 0.8)
        c.put(c.mask(box(x, y + h - 0.8, x + w, y + h)), scale(colour, 0.6))
        cx, cy = x + w / 2, y + h / 2
        ink = self.p["brass"]
        if glyph == "circle":  # a compass: the surveyor
            c.put(c.mask(lambda p: (p.ring(cx, cy, h * 0.3, 0.9), p.line([(cx, cy - h * 0.38), (cx - h * 0.22, cy + h * 0.3)], 0.9), p.line([(cx, cy - h * 0.38), (cx + h * 0.22, cy + h * 0.3)], 0.9))), ink)
        elif glyph == "cup":  # the inn
            c.put(c.mask(lambda p: (p.poly([(cx - 4, cy - 4), (cx + 4, cy - 4), (cx + 3, cy + 4), (cx - 3, cy + 4)]), p.ring(cx + 4.6, cy, 2.2, 0.8))), ink)
        elif glyph == "gear":  # the mechanic
            c.put(c.mask(lambda p: ([p.line([(cx, cy), (cx + h * 0.36 * math.cos(a), cy + h * 0.36 * math.sin(a))], 1.6) for a in np.linspace(0, math.tau, 9)[:-1]], p.ellipse(cx, cy, h * 0.24))), ink)
            c.put(c.mask(lambda p: p.ellipse(cx, cy, h * 0.1)), colour)
        elif glyph == "triangle":
            c.put(c.mask(lambda p: p.line([(cx - 5, cy + 3.5), (cx + 5, cy + 3.5), (cx - 5, cy - 4), (cx - 5, cy + 3.5)], 0.9)), ink)
            c.put(c.mask(box(cx - 5, cy + 1.5, cx - 3, cy + 3.5)), ink)

    def chimney(self, x, y_base, w, h, colour, smoke=None, tag="chim"):
        c = self.c
        c.put(c.mask(box(x, y_base - h, x + w, y_base)), colour)
        c.put(c.mask(box(x - 1.4, y_base - h - 2.4, x + w + 1.4, y_base - h)), scale(colour, 0.8))
        side = box(x + w * 0.6, y_base - h, x + w, y_base) if self.sun < 0 else box(x, y_base - h, x + w * 0.4, y_base)
        c.tone(c.mask(side), -0.18)
        c.put(c.mask(lambda p: [p.rect(x, y, x + w, y + 0.5) for y in np.arange(y_base - h + 3, y_base, 3.5)]), scale(colour, 0.75), 0.6)
        if smoke:
            rng = c.rand(tag, "smoke")
            pts = [(x + w / 2 + (i * 0.9) ** 1.5 + math.sin(i * 0.5) * 2.0, y_base - h - 3 - i * 4.2) for i in range(14)]
            for i, (px_, py_) in enumerate(pts):
                puff = c.mask(lambda p: p.ellipse(px_, py_, 2.2 + i * 0.55, 1.8 + i * 0.4), blur=1.0 + i * 0.35)
                c.put(puff, smoke, 0.10 * (1 - i / 14) + 0.02)

    def string_lights(self, a, b, sag, colour, n=14):
        c = self.c
        pts = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + sag * 4 * t * (1 - t)) for t in np.linspace(0, 1, 40)]
        c.put(c.mask(lambda p: p.line(pts, 0.5)), self.p["iron"], 0.9)
        bulbs = [pts[int(i * 39 / (n - 1))] for i in range(n)]
        c.put(c.mask(lambda p: [p.ellipse(x, y + 1.6, 1.1) for x, y in bulbs]), mix(colour, (255, 255, 255), 0.5))
        c.light(c.mask(lambda p: [p.ellipse(x, y + 1.6, 4.5) for x, y in bulbs], blur=3), colour, 0.6)
