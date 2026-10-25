"""The interdimensional gate's wormhole: a triangle door (Jon, 2026-10-24:
"triangle is better"). It draws the rows of
``interdimensional_gate.PORTAL_ROWS`` on the ring's own canvas;
``interdimensional_gate.render_portal_frame`` calls it.

- ``opening``: three rays of energy start at the three clamp lamps (12, 4
  and 8 o'clock, where the inner ring meets them) and each runs along a
  chord to the next lamp. They inscribe a triangle in the ring. The triangle
  ignites, divides into its medial triangles, and the door opens out from
  its edges to the lip of the aperture.
- ``stable``: a tunnel of nested triangles, each one inscribed in the one
  outside it and turned a little: a vortex that falls away into a violet
  depth, each level divided into its medial triangle (a Sierpinski step). The
  zoom is self-similar, so the row loops without a seam. Three sparks run
  round the triangle, one edge per loop.
- ``closing``: the door drains back into the triangle, the triangle turns a
  third of a turn and falls into its centre, a last flash, nothing.
- ``swallow`` / ``emit``: a triangular wave runs from the centre to the lip
  (a dent and dark for a body that goes in, a swell and bright for a body
  that comes out). Both start on the stable surface's clock.

``render_tunnel_picture`` draws the picture the Ultra layer streams down
the tunnel (``gate_portal_fx.wgsl``): a lattice of Sierpinski triangles that
tiles both ways.

The output size is a parameter (``out_size``): the geometry is the gate's,
scaled from its 192 px frame, so 384 px frames are drawn at full detail.
"""

from __future__ import annotations

import functools
import math
from typing import Tuple

import numpy as np
from PIL import Image

from . import interdimensional_gate as gate

PORTAL_ROWS = gate.PORTAL_ROWS

#: The gate's geometry is authored on this frame (output pixels).
BASE_FRAME = 192
#: Work at this many samples per output pixel, then filter down.
SS = 4

#: The tunnel: each level is inscribed in the one outside it, its corners
#: this far along the outer level's edges (0.5 is the medial triangle).
WHIRL_F = 0.2

# Palette: the gate's cyan light, pushed toward violet in the depth.
VOID_DEEP = np.array([6, 4, 26], np.float32)
VOID_MID = np.array([30, 22, 92], np.float32)
VOID_EDGE = np.array([40, 120, 205], np.float32)
FAR = np.array([168, 96, 255], np.float32)
NEAR = np.array(gate.GLYPH_CORE, np.float32)
WHITE = np.array([236, 255, 255], np.float32)
GLOW = np.array(gate.GLYPH_GLOW, np.float32)

Rgb = np.ndarray


def _clamp01(t: float) -> float:
    return max(0.0, min(1.0, t))


def _ease(t: float) -> float:
    t = _clamp01(t)
    return t * t * (3.0 - 2.0 * t)


def _smooth(e0: float, e1: float, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# --- geometry -----------------------------------------------------------------


class _Geo:
    """The assembly's geometry at one output size, in work pixels."""

    def __init__(self, out_size: int):
        self.out = out_size
        self.w = out_size * SS
        k = out_size / BASE_FRAME
        #: One output pixel, in work pixels.
        self.px = float(SS)
        unit = k * SS
        self.cx = self.cy = self.w / 2.0
        self.portal_r = gate.PORTAL_R / gate.SUPER * unit
        self.inner_r = gate.INNER_R / gate.SUPER * unit
        #: The inscribed triangle: its corners touch the inner ring.
        self.frame_r = self.inner_r - 0.6 * unit
        ys, xs = np.mgrid[0 : self.w, 0 : self.w].astype(np.float32)
        self.dx = xs + 0.5 - self.cx
        self.dy = ys + 0.5 - self.cy
        self.dist = np.sqrt(self.dx * self.dx + self.dy * self.dy)
        # The scale of the gate drawing: an output pixel of the 192 frame.
        self.unit = unit


@functools.lru_cache(maxsize=4)
def _geo(out_size: int) -> _Geo:
    return _Geo(out_size)


def _corner(r: float, rot: float, k: int) -> Tuple[float, float]:
    """Corner ``k`` of an upright triangle (apex at 12 o'clock) of
    circumradius ``r``, turned ``rot`` degrees clockwise, about the centre."""
    ang = math.radians(-90.0 + rot + 120.0 * k)
    return (math.cos(ang) * r, math.sin(ang) * r)


@functools.lru_cache(maxsize=1)
def _whirl() -> Tuple[float, float]:
    """The scale and the turn (degrees) from one tunnel level to the next."""
    a = np.array(_corner(1.0, 0.0, 0))
    b = np.array(_corner(1.0, 0.0, 1))
    p = a + (b - a) * WHIRL_F
    scale = float(np.hypot(*p))
    turn = math.degrees(math.atan2(p[1], p[0])) - (-90.0)
    return scale, turn


def _tri_sdf(px: np.ndarray, py: np.ndarray, r: float, rot: float) -> np.ndarray:
    """Signed distance to an equilateral triangle about the origin
    (negative inside): circumradius ``r``, apex up, turned ``rot`` degrees
    clockwise (y down)."""
    a = math.radians(rot)
    c, s = math.cos(a), math.sin(a)
    x = px * c + py * s
    y = -(-px * s + py * c)
    k = math.sqrt(3.0)
    h = r * k / 2.0
    x = np.abs(x) - h
    y = y + h / k
    m = x + k * y > 0.0
    x2 = np.where(m, (x - k * y) / 2.0, x)
    y2 = np.where(m, (-k * x - y) / 2.0, y)
    x2 = x2 - np.clip(x2, -2.0 * h, 0.0)
    return -np.sqrt(x2 * x2 + y2 * y2) * np.sign(y2)


# --- the canvas -----------------------------------------------------------------


class _Canvas:
    """Premultiplied light over the membrane, plus a glow buffer."""

    def __init__(self, geo: _Geo):
        self.g = geo
        n = geo.w
        self.rgb = np.zeros((n, n, 3), np.float32)
        self.a = np.zeros((n, n), np.float32)
        self.glow = np.zeros((n, n, 3), np.float32)
        #: A clip for strokes (1 = drawn), set while drawing the tunnel.
        self.clip: np.ndarray | None = None

    def _box(self, r: float, pad: float):
        g = self.g
        x0 = max(0, int(g.cx - r - pad))
        x1 = min(g.w, int(g.cx + r + pad) + 1)
        y0 = max(0, int(g.cy - r - pad))
        y1 = min(g.w, int(g.cy + r + pad) + 1)
        return slice(y0, y1), slice(x0, x1)

    def over(self, sl, cov: np.ndarray, color: Rgb, glow: float = 0.0) -> None:
        if self.clip is not None:
            cov = cov * self.clip[sl]
        c = cov[..., None]
        self.rgb[sl] = self.rgb[sl] * (1.0 - c) + color * c
        self.a[sl] = self.a[sl] * (1.0 - cov) + cov
        if glow > 0.0:
            self.glow[sl] += color * c * glow

    def triangle(self, r: float, rot: float, width: float, color: Rgb, alpha: float, glow: float = 0.0) -> None:
        """Stroke a triangle's edges, ``width`` output pixels wide."""
        if alpha <= 0.003 or r <= 0.5:
            return
        g = self.g
        w = width * g.px
        sl = self._box(r, w + 2)
        d = _tri_sdf(g.dx[sl], g.dy[sl], r, rot)
        cov = np.clip(w / 2.0 - np.abs(d) + 0.5, 0.0, 1.0) * alpha
        self.over(sl, cov, color, glow)

    def segment(self, p: Tuple[float, float], q: Tuple[float, float], width: float, color: Rgb, alpha: float, glow: float = 0.0) -> None:
        g = self.g
        w = width * g.px
        pad = w + 2
        x0 = max(0, int(g.cx + min(p[0], q[0]) - pad))
        x1 = min(g.w, int(g.cx + max(p[0], q[0]) + pad) + 1)
        y0 = max(0, int(g.cy + min(p[1], q[1]) - pad))
        y1 = min(g.w, int(g.cy + max(p[1], q[1]) + pad) + 1)
        if x1 <= x0 or y1 <= y0:
            return
        sl = (slice(y0, y1), slice(x0, x1))
        px = g.dx[sl] - p[0]
        py = g.dy[sl] - p[1]
        vx, vy = q[0] - p[0], q[1] - p[1]
        ll = max(vx * vx + vy * vy, 1e-6)
        h = np.clip((px * vx + py * vy) / ll, 0.0, 1.0)
        d = np.sqrt((px - vx * h) ** 2 + (py - vy * h) ** 2)
        cov = np.clip(w / 2.0 - d + 0.5, 0.0, 1.0) * alpha
        self.over(sl, cov, color, glow)

    def dot(self, p: Tuple[float, float], radius: float, color: Rgb, alpha: float, glow: float = 0.0) -> None:
        """A soft round light, ``radius`` output pixels."""
        if alpha <= 0.003:
            return
        g = self.g
        r = radius * g.px
        pad = r * 2.5 + 2
        sl = (
            slice(max(0, int(g.cy + p[1] - pad)), min(g.w, int(g.cy + p[1] + pad) + 1)),
            slice(max(0, int(g.cx + p[0] - pad)), min(g.w, int(g.cx + p[0] + pad) + 1)),
        )
        d = np.sqrt((g.dx[sl] - p[0]) ** 2 + (g.dy[sl] - p[1]) ** 2)
        cov = np.clip(r - d + 0.5, 0.0, 1.0) * alpha
        self.over(sl, cov, color, glow)
        self.glow[sl] += color * (np.exp(-((d / (r * 2.2)) ** 2)) * alpha * glow * 0.6)[..., None]

    def finish(self, glow_radius: float, glow_gain: float, aperture: float) -> Image.Image:
        """Filter down to the output size and lay the glow over, cut to
        ``aperture`` (work pixels) plus its own soft edge."""
        g = self.g
        n, o = g.w, g.out
        rgb = self.rgb.reshape(o, SS, o, SS, 3).mean(axis=(1, 3))
        a = self.a.reshape(o, SS, o, SS).mean(axis=(1, 3))
        glow = self.glow.reshape(o, SS, o, SS, 3).mean(axis=(1, 3))
        glow = _blur(glow, glow_radius * g.unit / SS) * glow_gain
        # The glow does not spill past the ring's inner edge: the band covers it.
        yy, xx = np.mgrid[0:o, 0:o].astype(np.float32)
        r = np.sqrt((xx + 0.5 - o / 2) ** 2 + (yy + 0.5 - o / 2) ** 2) * SS
        keep = np.clip((aperture - r) / (1.5 * SS) + 0.5, 0.0, 1.0)
        glow = glow * keep[..., None]
        ga = np.clip(glow.max(axis=2) / 255.0, 0.0, 1.0)
        out_a = a + ga * (1.0 - a)
        prem = rgb + glow
        color = np.where(out_a[..., None] > 1e-5, prem / np.maximum(out_a, 1e-5)[..., None], 0.0)
        px = np.dstack([np.clip(color, 0, 255), np.clip(out_a * 255.0, 0, 255)])
        del n
        return Image.fromarray(px.astype(np.uint8), "RGBA")


def _blur(img: np.ndarray, sigma: float) -> np.ndarray:
    """A Gaussian blur by FFT (the edges are clear, so wrapping is safe)."""
    if sigma <= 0.1:
        return img
    h, w = img.shape[:2]
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    kern = np.exp(-2.0 * (math.pi * sigma) ** 2 * (fx * fx + fy * fy))
    out = np.empty_like(img)
    for ch in range(img.shape[2]):
        out[..., ch] = np.fft.irfft2(np.fft.rfft2(img[..., ch]) * kern, s=(h, w))
    return np.maximum(out, 0.0)


# --- the parts ------------------------------------------------------------------


def _mix(a: Rgb, b: Rgb, t: float) -> Rgb:
    t = _clamp01(t)
    return a * (1.0 - t) + b * t


def _membrane(
    cv: _Canvas, reveal: float, phase: float, alpha: float, splash: float, outward: bool, scale: float = 1.0, rot: float = 0.0
) -> None:
    """The void the door opens on: deep violet at the centre, cyan at the
    lip, with a faint three-fold shimmer turning in it. ``reveal`` (0..1)
    opens it out from the triangle's edges to the lip; ``scale`` and
    ``rot`` move the triangle (the door) as it closes."""
    g = cv.g
    d = g.dist / g.portal_r
    # Triangular distance from the centre: 1 on the inscribed triangle.
    tri = _tri_sdf(g.dx, g.dy, g.frame_r * scale, rot)
    inr = g.frame_r * scale / 2.0
    tri_d = (tri + inr) / inr
    k = np.clip(d, 0.0, 1.0)[..., None]
    base = VOID_DEEP * (1 - k) ** 2 + VOID_MID * 2 * k * (1 - k) + VOID_EDGE * k**2
    theta = np.arctan2(g.dy, g.dx)
    shimmer = (0.5 + 0.5 * np.sin(theta * 3.0 - np.log(np.maximum(d, 0.02)) * 4.0 - phase * math.tau)) ** 6
    light = shimmer * np.clip(d, 0, 1) * 34.0
    if splash >= 0.0:
        u = splash
        fade = (1.0 - u) ** 1.3
        front = u * 2.0
        lead = np.exp(-(((tri_d - front) / 0.08) ** 2))
        trough = np.exp(-(((tri_d - front + 0.14) / 0.08) ** 2)) * (tri_d < front)
        light = light + lead * (230.0 if outward else 140.0) * fade
        base = base * (1.0 - (trough * 0.5 * fade)[..., None])
        middle = np.exp(-((tri_d / (0.3 + 0.4 * u)) ** 2)) * (1.0 - _ease(u))
        if outward:
            light = light + middle * 200.0
        else:
            base = base * (1.0 - middle[..., None] * 0.7)
    # Inside the triangle the void is deeper: the other side of the door.
    door = np.clip(-tri / (2.0 * g.px) + 0.5, 0.0, 1.0)[..., None] * 0.55
    base = base * (1.0 - door) + VOID_DEEP * door
    rgb = base + light[..., None] * np.array([0.7, 0.9, 1.0], np.float32)
    lip = np.exp(-(((d - 0.97) / 0.03) ** 2))
    rgb = rgb * (1 - lip[..., None] * 0.55) + WHITE * lip[..., None] * 0.55
    inside = np.clip((g.portal_r - g.dist) / g.px + 0.5, 0.0, 1.0)
    edge = 1.0 + reveal * (g.portal_r / inr + 0.1 - 1.0)
    shown = np.clip((edge - tri_d) * inr / (5.0 * g.px) + 0.5, 0.0, 1.0) if reveal < 1.0 else 1.0
    cov = inside * shown * alpha
    if 0.0 < reveal < 1.0:
        # The opening front: a bright edge running out to the lip.
        front = np.exp(-(((tri_d - edge) * inr / (2.5 * g.px)) ** 2)) * inside * alpha
        rgb = rgb + (front * 120.0)[..., None]
        cv.glow += GLOW * (front * 0.6)[..., None]
    c = cov[..., None]
    cv.rgb = cv.rgb * (1.0 - c) + rgb * c
    cv.a = cv.a * (1.0 - cov) + cov
    # The lip's glow.
    cv.glow += (GLOW * (lip * cov * 0.5)[..., None])


def _tunnel(cv: _Canvas, phase: float, alpha: float, scale: float, rot: float, depth: float = 1.0) -> None:
    """The vortex of nested triangles inside the inscribed one. Level ``j``
    is the frame triangle scaled by ``q**(j - phase)`` and turned by
    ``turn * (j - phase)``; brightness and width follow the scale alone, so
    phase 1 is phase 0."""
    if alpha <= 0.003:
        return
    g = cv.g
    q, turn = _whirl()
    big = g.frame_r * scale
    inside = _tri_sdf(g.dx, g.dy, big, rot)
    cv.clip = np.clip(-inside / (1.2 * g.px) + 0.5, 0.0, 1.0)
    j = 0
    while True:
        lv = j - phase
        s = q**lv
        if s * big < 1.2 * g.px:
            break
        j += 1
        # Fades in from the depth, and out as it grows past the frame.
        fade_in = float(_smooth(0.05, 0.3, s)) * depth + (1.0 - depth) * float(_smooth(0.6, 0.95, s))
        fade_out = 1.0 - float(_smooth(1.0, 1.0 / q, s))
        a = alpha * fade_in * fade_out
        if a <= 0.003:
            continue
        near = float(_smooth(0.05, 1.0, s))
        color = _mix(FAR, NEAR, near)
        r = big * s
        ang = rot + turn * lv
        width = 0.55 + 1.15 * s
        cv.triangle(r, ang, width, color, a * (0.55 + 0.45 * near), glow=0.5 + 0.5 * near)
        # A Sierpinski step: the medial triangle is a hole, a little darker,
        # so the holes stack into the depth; its edges faint and fine.
        _fill_triangle(cv, (0.0, 0.0), r * 0.5, ang + 180.0, VOID_DEEP, a * 0.22 * depth)
        cv.triangle(r * 0.5, ang + 180.0, max(0.45, width * 0.55), _mix(FAR, NEAR, near * 0.7), a * 0.6 * depth * float(_smooth(0.12, 0.4, s)), glow=0.3)
        # And on the near levels, the next step in the three corners.
        corner_a = a * 0.3 * float(_smooth(0.35, 0.8, s)) * depth
        if corner_a > 0.01:
            for kk in range(3):
                cx, cy = _corner(r * 0.5, ang, kk)
                _corner_triangle(cv, (cx, cy), r * 0.25, ang + 180.0, max(0.4, width * 0.4), _mix(FAR, NEAR, near * 0.6), corner_a)
    cv.clip = None
    # The vanishing point: a small violet light at the far end.
    cv.dot((0.0, 0.0), 1.1 * scale, _mix(FAR, WHITE, 0.35), alpha * 0.8, glow=1.4)


def _fill_triangle(cv: _Canvas, at: Tuple[float, float], r: float, rot: float, color: Rgb, alpha: float) -> None:
    """Fill a triangle about ``at`` (centre-relative)."""
    if alpha <= 0.003:
        return
    g = cv.g
    pad = r + 2
    sl = (
        slice(max(0, int(g.cy + at[1] - pad)), min(g.w, int(g.cy + at[1] + pad) + 1)),
        slice(max(0, int(g.cx + at[0] - pad)), min(g.w, int(g.cx + at[0] + pad) + 1)),
    )
    d = _tri_sdf(g.dx[sl] - at[0], g.dy[sl] - at[1], r, rot)
    cv.over(sl, np.clip(0.5 - d, 0.0, 1.0) * alpha, color)


def _gasket(cv: _Canvas, at: Tuple[float, float], r: float, rot: float, depth: int, width: float, color: Rgb, alpha: float) -> None:
    """The Sierpinski gasket of an upright triangle about ``at``: its medial
    triangle, then the same in each of the three corners, ``depth`` steps."""
    if depth <= 0 or alpha <= 0.01:
        return
    _corner_triangle(cv, at, r * 0.5, rot + 180.0, width, color, alpha)
    for k in range(3):
        cx, cy = _corner(r * 0.5, rot, k)
        _gasket(cv, (at[0] + cx, at[1] + cy), r * 0.5, rot, depth - 1, width * 0.75, color, alpha * 0.8)


def _corner_triangle(cv: _Canvas, at: Tuple[float, float], r: float, rot: float, width: float, color: Rgb, alpha: float) -> None:
    """A triangle about ``at`` (centre-relative) instead of the centre."""
    g = cv.g
    w = width * g.px
    pad = r + w + 2
    sl = (
        slice(max(0, int(g.cy + at[1] - pad)), min(g.w, int(g.cy + at[1] + pad) + 1)),
        slice(max(0, int(g.cx + at[0] - pad)), min(g.w, int(g.cx + at[0] + pad) + 1)),
    )
    d = _tri_sdf(g.dx[sl] - at[0], g.dy[sl] - at[1], r, rot)
    cov = np.clip(w / 2.0 - np.abs(d) + 0.5, 0.0, 1.0) * alpha
    cv.over(sl, cov, color, 0.2)


def _frame(cv: _Canvas, scale: float, rot: float, alpha: float, heat: float, sparks: float, phase: float) -> None:
    """The inscribed triangle: the door's frame of light, and its corners'
    nodes where it meets the ring."""
    if alpha <= 0.003:
        return
    g = cv.g
    r = g.frame_r * scale
    color = _mix(NEAR, WHITE, 0.35 + 0.65 * heat)
    cv.triangle(r, rot, (2.2 + 1.2 * heat) * min(1.0, 0.35 + scale), color, alpha, glow=1.2 + heat)
    for k in range(3):
        cv.dot(_corner(r, rot, k), (1.9 + 1.2 * heat) * min(1.0, 0.3 + scale), WHITE, alpha, glow=1.4)
    if sparks > 0.0:
        # Three sparks run round the frame, one edge per loop.
        for k in range(3):
            a = np.array(_corner(r, rot, k))
            b = np.array(_corner(r, rot, k + 1))
            p = a + (b - a) * (phase % 1.0)
            cv.dot((float(p[0]), float(p[1])), 1.7, WHITE, alpha * sparks, glow=1.6)


def _rays(cv: _Canvas, u: float, flare: float) -> None:
    """The opening's rays: from each lamp's corner along the chord to the
    next corner, ``u`` (0..1) of the way."""
    g = cv.g
    r = g.frame_r
    for k in range(3):
        a = np.array(_corner(r, 0.0, k))
        b = np.array(_corner(r, 0.0, k + 1))
        cv.dot((float(a[0]), float(a[1])), 2.4 + 2.0 * flare, WHITE, 1.0, glow=1.6 + 1.5 * flare)
        if u <= 0.0:
            continue
        head = a + (b - a) * u
        # The trail cools behind the head.
        cv.segment(tuple(a), tuple(head), 2.2, NEAR, 0.95, glow=1.3)
        tail = a + (b - a) * max(0.0, u - 0.25)
        cv.segment(tuple(tail), tuple(head), 2.8, WHITE, 1.0, glow=1.6)
        cv.dot((float(head[0]), float(head[1])), 2.6, WHITE, 1.0, glow=2.2)


def _specks(cv: _Canvas, phase: float, alpha: float) -> None:
    """Motes falling out of the tunnel toward the viewer, on the loop."""
    if alpha <= 0.01:
        return
    g = cv.g
    for i in range(18):
        u = (i * 0.618034 + phase) % 1.0
        rr = g.portal_r * (0.06 + 0.9 * u**1.6)
        ang = i * 137.5 + u * 40.0
        x = math.cos(math.radians(ang)) * rr
        y = math.sin(math.radians(ang)) * rr
        a = alpha * math.sin(u * math.pi) ** 1.5 * 0.7
        cv.dot((x, y), 0.45 + 0.8 * u, WHITE, a, glow=0.6)


# --- frames ---------------------------------------------------------------------


def _stable(cv: _Canvas, phase: float, *, splash: float = -1.0, outward: bool = False, surge: float = 0.0, flex: float = 1.0) -> None:
    _membrane(cv, 1.0, phase, 1.0, splash, outward)
    _tunnel(cv, phase + surge, 1.0, flex, 0.0)
    _specks(cv, phase, 1.0)
    _frame(cv, flex, 0.0, 1.0, 0.0, 1.0, phase)


def render_portal_frame(animation: str, frame_index: int, nframes: int, out_size: int = BASE_FRAME) -> Image.Image:
    """One frame of a portal row, ``out_size`` pixels square, on the gate's
    assembly canvas (the same centre and aperture as the ring)."""
    g = _geo(out_size)
    cv = _Canvas(g)
    t = frame_index / max(1, nframes - 1)
    aperture = g.inner_r - 0.5 * g.px
    if animation == "stable":
        _stable(cv, frame_index / max(1, nframes))
    elif animation == "opening":
        # 0..3: the rays inscribe the triangle. 4..7: it ignites, divides
        # and opens out to the lip; the last frame is the stable row's first.
        draw_u = _clamp01(t / (3.0 / 7.0))
        open_v = _clamp01((t - 3.0 / 7.0) / (4.0 / 7.0))
        if open_v <= 0.0:
            _rays(cv, _ease(draw_u) if draw_u < 1.0 else 1.0, 1.0 - draw_u)
        else:
            reveal = _ease((open_v - 0.2) / 0.8)
            _membrane(cv, reveal, 0.0, _ease(open_v * 2.0), -1.0, False)
            # The interior flashes, then the levels fall away into it.
            flash = (1.0 - open_v) ** 2
            if flash > 0.01:
                tri = _tri_sdf(g.dx, g.dy, g.frame_r, 0.0)
                cov = np.clip(-tri / g.px, 0.0, 1.0) * flash * 0.85
                cv.over((slice(None), slice(None)), cov * 0.75, _mix(NEAR, WHITE, 0.4), glow=0.5)
                # The flash divides: a Sierpinski gasket burns in it, then
                # gives way to the tunnel.
                _gasket(cv, (0.0, 0.0), g.frame_r, 0.0, 3, 2.0, WHITE, flash ** 0.5)
            _tunnel(cv, 0.0, _ease(open_v * 1.6), 1.0, 0.0, depth=_ease(open_v))
            _specks(cv, 0.0, open_v)
            _frame(cv, 1.0, 0.0, 1.0, 1.0 - open_v, open_v, 0.0)
    elif animation == "closing":
        # 0..2: the door drains back into the triangle. 2..6: the triangle
        # turns a third of a turn and falls into its centre. 7: gone.
        drain = _ease(t / 0.35)
        fall = _ease((t - 0.25) / 0.6) ** 1.5
        scale = 1.0 - fall
        rot = 120.0 * fall
        phase = t * 1.6
        if scale > 0.02:
            _membrane(cv, 1.0 - drain, phase, 1.0 - _ease((t - 0.55) / 0.3), -1.0, False, scale, rot)
            _tunnel(cv, phase, 1.0 - fall * 0.5, scale, rot)
            _specks(cv, phase, 1.0 - drain)
            _frame(cv, scale, rot, 1.0, fall, 1.0 - drain, phase)
        burst = max(0.0, 1.0 - abs(t - 0.86) / 0.16)
        if burst > 0.0:
            cv.dot((0.0, 0.0), 1.5 + 4.0 * burst, WHITE, burst, glow=2.5)
    elif animation in ("swallow", "emit"):
        outward = animation == "emit"
        phase = frame_index / max(1, nframes)
        bump = math.sin(_clamp01(t) * math.pi) ** 2
        surge = (-0.35 if outward else 0.35) * bump
        flex = 1.0 + (0.03 if outward else -0.025) * math.sin(min(1.0, t * 3.0) * math.pi) * (1.0 - t)
        _stable(cv, phase, splash=t, outward=outward, surge=surge, flex=flex)
    else:
        raise ValueError(f"unknown animation: {animation}")
    return cv.finish(glow_radius=2.4, glow_gain=1.0, aperture=aperture)


# --- the tunnel picture (Ultra) -------------------------------------------------

#: The tunnel picture's lattice: triangles round the tunnel per tile, rows
#: of triangles along the way in per tile (even, so the half-step offset of
#: alternate rows tiles), and the Sierpinski steps cut into each triangle.
TUNNEL_AROUND = 6
TUNNEL_ROWS = 2
TUNNEL_STEPS = 3


def _hole_levels(xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Which Sierpinski step removed each point: 0 for the lattice's open
    triangles (apex toward the lip), ``k`` for a hole cut at step ``k``,
    ``TUNNEL_STEPS + 1`` for what stands at the last step. ``xs`` and ``ys``
    are in tiles (0..1)."""
    r = ys * TUNNEL_ROWS
    q = xs * TUNNEL_AROUND + 0.5 * r
    fq = q - np.floor(q)
    fr = r - np.floor(r)
    level = np.zeros(xs.shape, np.int32)
    # The standing lattice triangles have their apex toward the way in.
    solid = fq >= fr
    u = np.where(solid, fq - fr, 0.0)
    w = np.where(solid, fr, 0.0)
    alive = solid.copy()
    for step in range(1, TUNNEL_STEPS + 1):
        u, w = u * 2.0, w * 2.0
        cu, cw = u >= 1.0, w >= 1.0
        middle = alive & ~cu & ~cw & (u + w >= 1.0)
        level[middle] = step
        alive &= ~middle
        u = np.where(cu, u - 1.0, u)
        w = np.where(cw, w - 1.0, w)
    level[alive] = TUNNEL_STEPS + 1
    return level


def _wrap_dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    """Grow ``mask`` by ``radius`` pixels (a square), wrapping at the edges."""
    out = mask.copy()
    for _ in range(radius):
        grown = out.copy()
        for axis in (0, 1):
            grown |= np.roll(out, 1, axis) | np.roll(out, -1, axis)
        out = grown
    return out


def render_tunnel_picture(size: int = gate.TUNNEL_SIZE) -> Image.Image:
    """The inside of the wormhole for the Ultra layer (``gate_portal_fx.wgsl``):
    a lattice of triangles, each cut into a Sierpinski gasket, in the stable
    row's violet void and cyan light. Across is the way round the tunnel,
    down is the way in, and it tiles both ways: every part is periodic in the
    tile (``TUNNEL_AROUND`` triangles across, ``TUNNEL_ROWS`` rows down), and
    the edges and the glow wrap. Opaque."""
    n = size * SS
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float64)
    level = _hole_levels((xs + 0.5) / n, (ys + 0.5) / n)
    top = TUNNEL_STEPS + 1
    # Fills: the open triangles are the deep void; a hole is darker the
    # earlier it was cut; what stands is a dim violet.
    # The shader adds two samples of it and a light at the far end, so it
    # is dark: lines of light on a void.
    fills = {0: VOID_DEEP * 0.5, top: _mix(VOID_DEEP, VOID_MID, 0.8)}
    for step in range(1, top):
        fills[step] = _mix(VOID_DEEP * 0.5, VOID_MID, 0.25 * step / top)
    rgb = np.zeros((n, n, 3), np.float32)
    for k, c in fills.items():
        rgb[level == k] = c
    # Edges: the rim of each region, wider and nearer cyan for the early cuts.
    glow = np.zeros_like(rgb)
    for k in range(top):
        region = level == k
        rim = _wrap_dilate(region, 1) & ~region
        width = {0: 3, 1: 2, 2: 1}.get(k, 0)
        line = _wrap_dilate(rim, width) if width > 0 else rim
        color = _mix(NEAR, WHITE, 0.3) if k == 0 else _mix(NEAR, FAR, (k - 1) / max(1, top - 2))
        a = {0: 0.85, 1: 0.7, 2: 0.55}.get(k, 0.45)
        rgb[line] = rgb[line] * (1.0 - a) + color * a
        glow[line] += color * (0.5 if k <= 1 else 0.25)
    # Filter down; the glow wraps, so it tiles too.
    rgb = rgb.reshape(size, SS, size, SS, 3).mean(axis=(1, 3))
    glow = glow.reshape(size, SS, size, SS, 3).mean(axis=(1, 3))
    rgb = rgb + _blur(glow, 1.6 * size / 256.0) * 0.6
    px = np.dstack([np.clip(rgb, 0, 255), np.full((size, size), 255.0)])
    return Image.fromarray(px.astype(np.uint8), "RGBA")
