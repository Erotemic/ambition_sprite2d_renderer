"""The paint box of the parallax scenes.

A scene (`scenes.py`) is a stack of layers, and each layer is made of masks:
a mask says where a thing is, and a paint says what colour it has there. This
module has the masks (noise, ridge lines, drawn shapes), the paints (ramps,
rim light, haze), and the canvas they go on.

Coordinates are in parts of the panel: `u` goes right from 0 to 1 and `v`
goes down from 0 to 1. A scene written in them does not change when the size
of the panel changes.

The work is done at more than the published size (`SUPERSAMPLE`) and made
small at the end, so a drawn edge has no steps.
"""

from __future__ import annotations

import hashlib
import math
import random
from typing import Iterable, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RGB = tuple[int, int, int]
SUPERSAMPLE = 2


def seed_of(*parts: object) -> int:
    digest = hashlib.blake2b(":".join(str(p) for p in parts).encode(), digest_size=8).digest()
    return int.from_bytes(digest, "little")


def mix(a: Sequence[float], b: Sequence[float], t: float) -> RGB:
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))  # type: ignore[return-value]


def scale(colour: Sequence[float], k: float) -> RGB:
    return tuple(max(0, min(255, int(round(c * k)))) for c in colour)  # type: ignore[return-value]


def smoothstep(lo: float, hi: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


class Art:
    """One panel in work: a square of `size` published pixels.

    A layer is a float array `(n, n, 4)`: colour 0..255, alpha 0..1, not
    premultiplied. A mask is a float array `(n, n)`, 0..1.
    """

    def __init__(self, size: int, *seed_parts: object) -> None:
        self.size = size
        self.n = size * SUPERSAMPLE
        self.seed_parts = seed_parts
        self.rng = random.Random(seed_of(*seed_parts))
        ramp = np.linspace(0.0, 1.0, self.n, dtype=np.float32)
        #: `u` and `v` of each pixel.
        self.u, self.v = np.meshgrid(ramp, ramp)

    # -- randomness ---------------------------------------------------------

    def rand(self, tag: object) -> random.Random:
        """A generator of its own for `tag`: a change to one part of a scene
        does not move the dice of the other parts."""
        return random.Random(seed_of(*self.seed_parts, tag))

    def _np_rng(self, tag: object) -> np.random.Generator:
        return np.random.default_rng(seed_of(*self.seed_parts, tag) % (2**63))

    # -- noise --------------------------------------------------------------

    def noise(
        self,
        tag: object,
        cells: float = 4.0,
        octaves: int = 4,
        gain: float = 0.5,
        stretch: float = 1.0,
    ) -> np.ndarray:
        """Smooth noise 0..1 with `cells` lumps across the panel. `stretch`
        more than 1 makes the lumps that much longer than they are high."""
        rng = self._np_rng(tag)
        total = np.zeros((self.n, self.n), dtype=np.float32)
        amplitude, norm = 1.0, 0.0
        for octave in range(octaves):
            freq = cells * (2**octave)
            gx = max(2, int(round(freq / stretch)) + 1)
            gy = max(2, int(round(freq)) + 1)
            grid = rng.random((gy, gx), dtype=np.float32)
            lump = Image.fromarray((grid * 255).astype(np.uint8), "L").resize(
                (self.n, self.n), Image.BICUBIC
            )
            total += np.asarray(lump, dtype=np.float32) / 255.0 * amplitude
            norm += amplitude
            amplitude *= gain
        total /= norm
        lo, hi = float(total.min()), float(total.max())
        return (total - lo) / max(hi - lo, 1e-6)

    def line_noise(self, tag: object, cells: float = 4.0, octaves: int = 5, gain: float = 0.5) -> np.ndarray:
        """Noise 0..1 along `u` only: one value for each column."""
        rng = self._np_rng(tag)
        xs = np.linspace(0.0, 1.0, self.n, dtype=np.float32)
        total = np.zeros(self.n, dtype=np.float32)
        amplitude, norm = 1.0, 0.0
        for octave in range(octaves):
            knots = max(2, int(round(cells * (2**octave))) + 1)
            values = rng.random(knots).astype(np.float32)
            position = xs * (knots - 1)
            index = np.minimum(position.astype(int), knots - 2)
            t = position - index
            t = t * t * (3.0 - 2.0 * t)
            total += (values[index] * (1 - t) + values[index + 1] * t) * amplitude
            norm += amplitude
            amplitude *= gain
        total /= norm
        lo, hi = float(total.min()), float(total.max())
        return (total - lo) / max(hi - lo, 1e-6)

    # -- masks --------------------------------------------------------------

    def ridge(
        self,
        tag: object,
        base_v: float,
        amp: float,
        cells: float = 3.0,
        octaves: int = 5,
        gain: float = 0.5,
        sharp: float = 0.0,
    ) -> tuple[np.ndarray, np.ndarray]:
        """The land under a ridge line: `(mask, line)`. `line` is the `v` of
        the ridge at each column; it is at `base_v` in the mean and goes
        `amp` each way. `sharp` 1 makes peaks of the lumps."""
        h = self.line_noise(tag, cells, octaves, gain)
        if sharp > 0.0:
            peaks = 1.0 - np.abs(h * 2.0 - 1.0)
            h = h * (1.0 - sharp) + peaks * sharp
        line = base_v - (h - 0.5) * 2.0 * amp
        edge = 1.0 / self.n
        mask = np.clip((self.v - line[None, :]) / edge + 0.5, 0.0, 1.0)
        return mask.astype(np.float32), line

    def drawing(self) -> tuple[Image.Image, "Pen"]:
        """A blank mask to draw shapes on, and its pen."""
        image = Image.new("L", (self.n, self.n), 0)
        return image, Pen(ImageDraw.Draw(image), self.n)

    def mask_of(self, image: Image.Image, blur: float = 0.0) -> np.ndarray:
        """The mask a drawing made. `blur` is in parts of a thousand of the panel."""
        if blur > 0.0:
            image = image.filter(ImageFilter.GaussianBlur(blur * self.n / 1000.0))
        return np.asarray(image, dtype=np.float32) / 255.0

    def blur(self, mask: np.ndarray, amount: float) -> np.ndarray:
        """`mask`, made soft. `amount` is in parts of a thousand of the panel."""
        image = Image.fromarray(np.clip(mask * 255.0, 0, 255).astype(np.uint8), "L")
        return self.mask_of(image, amount)

    def shift(self, mask: np.ndarray, du: float, dv: float) -> np.ndarray:
        """`mask` moved by `(du, dv)`; what comes in at an edge is empty."""
        dx, dy = int(round(du * self.n)), int(round(dv * self.n))
        out = np.zeros_like(mask)
        src_x = slice(max(0, -dx), self.n - max(0, dx))
        dst_x = slice(max(0, dx), self.n - max(0, -dx))
        src_y = slice(max(0, -dy), self.n - max(0, dy))
        dst_y = slice(max(0, dy), self.n - max(0, -dy))
        out[dst_y, dst_x] = mask[src_y, src_x]
        return out

    def rim(self, mask: np.ndarray, du: float, dv: float, soft: float = 0.0) -> np.ndarray:
        """The edge of `mask` that faces a light in the direction `(-du, -dv)`:
        the part of the mask that the mask moved by `(du, dv)` does not cover."""
        edge = np.clip(mask - self.shift(mask, du, dv), 0.0, 1.0)
        return self.blur(edge, soft) if soft > 0.0 else edge

    def spot(self, cu: float, cv: float, radius: float, power: float = 2.0, squash: float = 1.0) -> np.ndarray:
        """A soft round light: 1 at `(cu, cv)`, 0 at `radius` and beyond.
        `squash` more than 1 makes it that much wider than it is high."""
        d = np.sqrt(((self.u - cu) / squash) ** 2 + (self.v - cv) ** 2) / radius
        return np.clip(1.0 - d, 0.0, 1.0) ** power

    def band(self, centre_v: float, half: float, power: float = 2.0) -> np.ndarray:
        """A soft level band: 1 at `centre_v`, 0 at `half` away from it."""
        return np.clip(1.0 - np.abs(self.v - centre_v) / half, 0.0, 1.0) ** power

    # -- paints -------------------------------------------------------------

    def ramp(self, stops: Sequence[tuple[float, Sequence[float]]]) -> np.ndarray:
        """Colour that changes down the panel: `stops` are `(v, colour)`."""
        vs = np.array([s[0] for s in stops], dtype=np.float32)
        ramp = np.linspace(0.0, 1.0, self.n, dtype=np.float32)
        out = np.zeros((self.n, self.n, 3), dtype=np.float32)
        for channel in range(3):
            values = np.array([s[1][channel] for s in stops], dtype=np.float32)
            out[:, :, channel] = np.interp(ramp, vs, values)[:, None]
        return out

    def flat(self, colour: Sequence[float]) -> np.ndarray:
        out = np.empty((self.n, self.n, 3), dtype=np.float32)
        out[:, :] = colour
        return out

    def blank(self) -> np.ndarray:
        return np.zeros((self.n, self.n, 4), dtype=np.float32)

    def opaque(self, paint: np.ndarray) -> np.ndarray:
        layer = np.empty((self.n, self.n, 4), dtype=np.float32)
        layer[:, :, :3] = paint
        layer[:, :, 3] = 1.0
        return layer

    @staticmethod
    def put(layer: np.ndarray, mask: np.ndarray, paint: np.ndarray | Sequence[float], alpha: float = 1.0) -> None:
        """Paint `paint` on `layer` where `mask` is: the paint goes over what
        the layer has."""
        cover = np.clip(mask * alpha, 0.0, 1.0)
        below = layer[:, :, 3]
        out_alpha = cover + below * (1.0 - cover)
        paint_arr = np.asarray(paint, dtype=np.float32)
        weight = np.where(out_alpha > 1e-6, cover / np.maximum(out_alpha, 1e-6), 0.0)[:, :, None]
        layer[:, :, :3] = layer[:, :, :3] * (1.0 - weight) + paint_arr * weight
        layer[:, :, 3] = out_alpha

    @staticmethod
    def light(layer: np.ndarray, mask: np.ndarray, colour: Sequence[float], strength: float = 1.0) -> None:
        """Add light of `colour` to the colour the layer has (screen blend).
        It does not change where the layer is."""
        k = np.clip(mask * strength, 0.0, 1.0)[:, :, None]
        c = np.asarray(colour, dtype=np.float32) / 255.0
        base = layer[:, :, :3] / 255.0
        layer[:, :, :3] = (1.0 - (1.0 - base) * (1.0 - c * k)) * 255.0

    @staticmethod
    def glow(layer: np.ndarray, mask: np.ndarray, colour: Sequence[float], strength: float = 1.0) -> None:
        """Put light of `colour` in the air of a layer: where the layer is
        empty, the light is what is there."""
        Art.put(layer, mask, colour, strength)

    @staticmethod
    def shade(layer: np.ndarray, mask: np.ndarray, strength: float = 1.0) -> None:
        """Make the colour of the layer darker where `mask` is."""
        layer[:, :, :3] *= (1.0 - np.clip(mask * strength, 0.0, 1.0))[:, :, None]

    @staticmethod
    def tint(layer: np.ndarray, mask: np.ndarray, colour: Sequence[float], strength: float = 1.0) -> None:
        """Move the colour of the layer to `colour` where `mask` is. This is
        the haze of the air between the eye and a far thing."""
        k = np.clip(mask * strength, 0.0, 1.0)[:, :, None]
        layer[:, :, :3] = layer[:, :, :3] * (1.0 - k) + np.asarray(colour, dtype=np.float32) * k

    @staticmethod
    def fade(layer: np.ndarray, mask: np.ndarray) -> None:
        """Keep the layer only where `mask` is."""
        layer[:, :, 3] *= np.clip(mask, 0.0, 1.0)

    @staticmethod
    def over(below: np.ndarray, above: np.ndarray) -> np.ndarray:
        """`above` on `below`, as a new layer."""
        out = below.copy()
        Art.put(out, above[:, :, 3], above[:, :, :3])
        return out

    # -- finish -------------------------------------------------------------

    def grain(self, layer: np.ndarray, tag: object, amount: float = 1.6) -> None:
        """Fine noise, so a slow ramp has no bands in 8 bits."""
        noise = self._np_rng(tag).random((self.n, self.n), dtype=np.float32) - 0.5
        layer[:, :, :3] += noise[:, :, None] * amount * 2.0

    def publish(self, layer: np.ndarray, blur: float = 0.0, opaque: bool = False) -> Image.Image:
        """The layer as the picture to publish. `blur` is in published pixels.

        The picture is made small with its colour multiplied by its alpha, so
        an edge has no dark line, and an empty pixel has the colour of the
        nearest full one, so a sampler that mixes it in adds no dark. The
        arithmetic stays in floats to the end: a faint light that is rounded
        to 8 bits before its alpha is divided out shows as rings."""
        alpha = np.clip(layer[:, :, 3], 0.0, 1.0)
        if opaque:
            alpha = np.ones_like(alpha)
        rgb = np.clip(layer[:, :, :3], 0.0, 255.0)
        pre = np.dstack([rgb * alpha[:, :, None], alpha])
        k = SUPERSAMPLE
        small = pre.reshape(self.size, k, self.size, k, 4).mean(axis=(1, 3))
        if blur > 0.0:
            small = gaussian(small, blur)
        a = small[:, :, 3:4]
        colour = small[:, :, :3] / np.maximum(a, 1e-4)
        if not opaque:
            wide = gaussian(small, 5.0)
            wide_a = wide[:, :, 3:4]
            full = a[:, :, 0] > 0.5
            mean = colour[full].mean(axis=0) if full.any() else np.zeros(3, dtype=np.float32)
            wide_colour = np.where(wide_a > 1e-3, wide[:, :, :3] / np.maximum(wide_a, 1e-3), mean)
            colour = np.where(a > 4e-3, colour, wide_colour)
        # A pattern of half steps, so the 8 bit picture has no bands.
        dither = (self._np_rng("publish dither").random((self.size, self.size, 1), dtype=np.float32) - 0.5)
        out = np.dstack([np.clip(colour + dither, 0, 255), np.clip(a * 255.0 + dither * (0.0 if opaque else 1.0), 0, 255)])
        return Image.fromarray(np.rint(out).astype(np.uint8), "RGBA")


def gaussian(array: np.ndarray, sigma: float) -> np.ndarray:
    """`array` (rows, columns, channels), made soft by `sigma` pixels."""
    radius = max(1, int(math.ceil(sigma * 3.0)))
    xs = np.arange(-radius, radius + 1, dtype=np.float32)
    kernel = np.exp(-(xs**2) / (2.0 * sigma * sigma))
    kernel /= kernel.sum()
    out = array.astype(np.float32)
    for axis in (0, 1):
        pad = [(0, 0)] * out.ndim
        pad[axis] = (radius, radius)
        padded = np.pad(out, pad, mode="edge")
        total = np.zeros_like(out)
        length = out.shape[axis]
        for i, weight in enumerate(kernel):
            index = [slice(None)] * out.ndim
            index[axis] = slice(i, i + length)
            total += padded[tuple(index)] * weight
        out = total
    return out


class Pen:
    """Draws shapes on a mask, in parts of the panel."""

    def __init__(self, draw: ImageDraw.ImageDraw, n: int) -> None:
        self.draw = draw
        self.n = n

    def _p(self, pts: Iterable[tuple[float, float]]) -> list[tuple[float, float]]:
        return [(x * self.n, y * self.n) for x, y in pts]

    def poly(self, pts: Iterable[tuple[float, float]], value: int = 255) -> None:
        self.draw.polygon(self._p(pts), fill=value)

    def rect(self, u0: float, v0: float, u1: float, v1: float, value: int = 255) -> None:
        u0, u1 = min(u0, u1), max(u0, u1)
        v0, v1 = min(v0, v1), max(v0, v1)
        self.draw.rectangle([u0 * self.n, v0 * self.n, u1 * self.n, v1 * self.n], fill=value)

    def ellipse(self, cu: float, cv: float, ru: float, rv: float | None = None, value: int = 255) -> None:
        rv = ru if rv is None else rv
        self.draw.ellipse(
            [(cu - ru) * self.n, (cv - rv) * self.n, (cu + ru) * self.n, (cv + rv) * self.n], fill=value
        )

    def ring(self, cu: float, cv: float, r: float, width: float, value: int = 255) -> None:
        self.draw.ellipse(
            [(cu - r) * self.n, (cv - r) * self.n, (cu + r) * self.n, (cv + r) * self.n],
            outline=value,
            width=max(1, int(round(width * self.n))),
        )

    def arc(self, cu: float, cv: float, r: float, start: float, end: float, width: float, value: int = 255) -> None:
        self.draw.arc(
            [(cu - r) * self.n, (cv - r) * self.n, (cu + r) * self.n, (cv + r) * self.n],
            start,
            end,
            fill=value,
            width=max(1, int(round(width * self.n))),
        )

    def line(self, pts: Iterable[tuple[float, float]], width: float, value: int = 255) -> None:
        self.draw.line(self._p(pts), fill=value, width=max(1, int(round(width * self.n))), joint="curve")

    def curve(
        self, a: tuple[float, float], b: tuple[float, float], sag: float, width: float, value: int = 255, steps: int = 24
    ) -> None:
        """A hanging line from `a` to `b` that is `sag` lower in the middle."""
        pts = []
        for i in range(steps + 1):
            t = i / steps
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + sag * 4.0 * t * (1.0 - t)))
        self.line(pts, width, value)


def polar(cu: float, cv: float, r: float, degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    return (cu + math.cos(a) * r, cv + math.sin(a) * r)
