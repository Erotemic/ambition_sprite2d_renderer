"""Drawing a posed hand: the 2D parts painted at the 3D model's joints.

The look that reads as ONE hand, not stitched pieces:

- each digit is one piece of flesh (no line between its own phalanges),
  the palm and the thumb's web one more;
- the INK is a single outline round the whole silhouette;
- where one part passes over another, a soft pale SEAM, never ink;
- joints show only as faint creases (palm side) or wrinkles (back);
- which face of each phalanx shows (pads and creases, or the back and its
  nail) comes from the model, so a curl toward us shows nails, a fist from
  the back tucks its fingers behind a raised knuckle row.

``HandStyle`` holds the colours and the optional extras (glowing bones,
glowing fingertips, tendons, palm lines). ``draw_hand`` returns the layer
(with its ink) at the supersample plus the projected landmarks, for a
caller to composite and to hang things on (a ring, a cuff, a held item).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ..core.draw import blending_draw
from .model import FINGER_NAMES, Camera, Digit, HandPose, HandSpec, Point, digits, face_depth, knuckle_edge, landmarks, local, palm_face, thumb_web

RGBA = Tuple[int, int, int, int]


@dataclass(frozen=True)
class HandStyle:
    flesh: RGBA = (236, 196, 168, 255)
    #: The heel's shade and the light pass's dark side.
    shade: RGBA = (196, 146, 124, 255)
    #: The soft line where one part passes over another.
    seam: RGBA = (176, 124, 104, 220)
    ink: RGBA = (40, 24, 28, 255)
    #: Highlights: the pads, the knuckle bumps.
    highlight: RGBA = (255, 236, 222, 255)
    nail: Optional[RGBA] = (246, 214, 204, 255)
    nail_shine: RGBA = (255, 246, 240, 255)
    #: Glowing bones inside (a spectral hand), or None.
    bone: Optional[RGBA] = None
    #: A glow at each fingertip, or None.
    tip_glow: Optional[RGBA] = None
    #: A rim light along the upper edges, or None.
    rim: Optional[RGBA] = None
    tendons: bool = False
    palm_lines: bool = True
    #: The ink's width (frame px).
    ink_width: float = 1.0


STYLES: Dict[str, HandStyle] = {
    "skin": HandStyle(),
    "spectral": HandStyle(
        flesh=(226, 238, 248, 215), shade=(150, 168, 210, 215), seam=(138, 156, 206, 220), ink=(24, 16, 44, 255), highlight=(250, 252, 255, 255),
        nail=(58, 24, 96, 255), nail_shine=(176, 120, 255, 255), bone=(150, 255, 230, 255), tip_glow=(110, 240, 220, 255), rim=(110, 240, 220, 255),
        tendons=True,
    ),
    "glove": HandStyle(flesh=(248, 248, 252, 255), shade=(200, 204, 222, 255), seam=(170, 176, 200, 220), ink=(30, 30, 40, 255), highlight=(255, 255, 255, 255), nail=None, palm_lines=False),
}


@dataclass
class HandDrawing:
    """The drawn hand at ``ss`` x the frame, and its landmarks (frame px)."""

    image: Image.Image
    landmarks: Dict[str, Point]
    ss: int

    def frame(self) -> Image.Image:
        """The hand at frame size."""
        w, h = self.image.size
        return self.image.resize((w // self.ss, h // self.ss), Image.Resampling.LANCZOS)


def _a(c: RGBA, a: float) -> RGBA:
    return (c[0], c[1], c[2], int(max(0.0, min(1.0, a)) * c[3]))


class _Painter:
    """Drawing helpers in frame px on a supersampled layer."""

    def __init__(self, layer: Image.Image, ss: int):
        self.layer, self.ss = layer, ss

    def s(self, p: Point) -> Tuple[float, float]:
        return (p[0] * self.ss, p[1] * self.ss)

    def draw(self):
        return blending_draw(self.layer)

    def disk(self, d, p: Point, r: float, fill: RGBA) -> None:
        q = self.s(p)
        d.ellipse((q[0] - r * self.ss, q[1] - r * self.ss, q[0] + r * self.ss, q[1] + r * self.ss), fill=fill)

    def capsule(self, d, a: Point, b: Point, w: float, fill: RGBA) -> None:
        d.line([self.s(a), self.s(b)], fill=fill, width=max(1, int(w * self.ss)))
        for p in (a, b):
            self.disk(d, p, w / 2, fill)

    def glow(self, fn: Callable, blur: float) -> None:
        g = Image.new("RGBA", self.layer.size, (0, 0, 0, 0))
        fn(blending_draw(g))
        self.layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur * self.ss)))


def _draw_digit(pt: _Painter, cam: Camera, digit: Digit, style: HandStyle, glow: float, fade: float, tip_fade: float, only_first: bool = False) -> None:
    """A DIGIT: one piece of flesh over its phalanges, then per phalanx its
    face's details; from the palm drawn base to tip (a curl folds toward us),
    from the back tip first (it folds away, tucked behind)."""
    pts = [cam.project(j) for j in digit.joints]
    pads = [cam.faces_us(p) for p in digit.pads]
    widths = [w * cam.scale for w in digit.widths]
    n = len(pts) - 1
    keep = max(0.0, n * (1.0 - tip_fade))
    order = list(range(n)) if cam.palm_faces_us() else list(range(n - 1, -1, -1))
    if only_first:
        order = [0]
    shown = [i for i in order if i < keep]

    def segment(i):
        a, b = pts[i], pts[i + 1]
        frac = min(1.0, keep - i)
        return a, (a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac), frac

    d = pt.draw()
    for colour, grow in ((_a(style.seam, fade), 0.9 * cam.scale), (_a(style.flesh, fade), 0.0)):
        for i in shown:
            a, b, _ = segment(i)
            pt.capsule(d, a, b, widths[i] + grow, colour)
    for i in shown:
        a, b, frac = segment(i)
        w = widths[i]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        ux, uy = (dx / ln, dy / ln) if ln > 0.3 else (math.cos(math.radians(cam.palm_deg)), math.sin(math.radians(cam.palm_deg)))
        half = w * 0.42
        if style.bone is not None:
            strength = 0.35 if pads[i] else 1.0
            pt.glow(lambda g, a=a, b=b, k=strength: g.line([pt.s(a), pt.s(b)], fill=_a(style.bone, 0.55 * glow * fade * k), width=int(1.8 * cam.scale * pt.ss)), 0.8 * cam.scale)
            pt.draw().line([pt.s(a), pt.s(b)], fill=_a(style.bone, 0.8 * fade * strength), width=max(1, int(0.6 * cam.scale * pt.ss)))
        d = pt.draw()
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if pads[i] and ln > 2.0 * cam.scale:
            pt.disk(d, m, half * 0.55, _a(style.highlight, 0.18 * fade))
        if i == n - 1 and frac >= 1.0 and not pads[i] and style.nail is not None:
            # The NAIL, set INSIDE the rounded tip (never past it).
            q = (a[0] + dx * 0.62, a[1] + dy * 0.62)
            rl, rw = max(1.3 * cam.scale, ln * 0.26), w * 0.26
            nail = [(q[0] + ux * rl * math.cos(t) - uy * rw * math.sin(t), q[1] + uy * rl * math.cos(t) + ux * rw * math.sin(t)) for t in np.linspace(0, math.tau, 14)]
            d.polygon([pt.s(p) for p in nail], fill=_a(style.nail, 0.85 * fade))
            d.line([pt.s((q[0] - ux * rl * 0.4 - uy * rw * 0.4, q[1] - uy * rl * 0.4 + ux * rw * 0.4)), pt.s((q[0] + ux * rl * 0.3 - uy * rw * 0.4, q[1] + uy * rl * 0.3 + ux * rw * 0.4))],
                   fill=_a(style.nail_shine, 0.9 * fade), width=max(1, int(0.5 * cam.scale * pt.ss)))
        if i > 0:
            # The JOINT: only a faint crease (palm side) or wrinkles (back).
            lw = max(1, int(0.4 * cam.scale * pt.ss))
            if pads[i]:
                r = w * 0.3
                for s0, s1 in ((-half, -r), (r, half)):
                    d.line([pt.s((a[0] - uy * s0, a[1] + ux * s0)), pt.s((a[0] - uy * s1, a[1] + ux * s1))], fill=_a(style.seam, 0.45 * fade), width=lw)
            else:
                for off in (-0.9 * cam.scale, 0.9 * cam.scale):
                    c = (a[0] + ux * off, a[1] + uy * off)
                    d.line([pt.s((c[0] - uy * half * 0.5, c[1] + ux * half * 0.5)), pt.s((c[0] + uy * half * 0.5, c[1] - ux * half * 0.5))], fill=_a(style.seam, 0.35 * fade), width=lw)
    if keep >= n and not only_first and style.tip_glow is not None:
        tip = pts[-1]
        pt.glow(lambda g: g.ellipse((*pt.s((tip[0] - 2.4 * cam.scale, tip[1] - 2.4 * cam.scale)), *pt.s((tip[0] + 2.4 * cam.scale, tip[1] + 2.4 * cam.scale))), fill=_a(style.tip_glow, 0.8 * glow * fade)), 1.0 * cam.scale)
        pt.disk(pt.draw(), tip, widths[-1] * 0.28, _a((200, 255, 245, 255), 0.85 * fade))


def _draw_palm(pt: _Painter, spec: HandSpec, pose: HandPose, cam: Camera, style: HandStyle, glow: float, fade: float) -> None:
    """The PALM and the thumb's web, one piece of flesh; shaded toward the
    heel; its pads and lines from the front, its tendons from the back."""
    front = cam.palm_faces_us()
    fn = face_depth(spec, cam)
    P = lambda u, v, n=fn: cam.project(local(spec, u, v, n))  # noqa: E731
    d = pt.draw()
    # The palm is a SLAB: its edge (the hull of both faces) in shade, then
    # the face we see over it, the thumb's web with it; all one flesh.
    near, far = palm_face(spec, front), palm_face(spec, not front)
    hull = _hull([cam.project(p) for p in near + far])
    d.polygon([pt.s(p) for p in hull], fill=_a(style.flesh, fade))
    d.polygon([pt.s(p) for p in hull], fill=_a(style.shade, 0.45 * fade))
    d.polygon([pt.s(cam.project(p)) for p in thumb_web(spec, pose)], fill=_a(style.flesh, fade))
    d.polygon([pt.s(cam.project(p)) for p in near], fill=_a(style.flesh, fade))
    # Its details (shade, pads, lines, tendons, bones) stay ON the face we
    # see and the web: drawn apart, then clipped to them.
    base, pt = pt, _Painter(Image.new("RGBA", pt.layer.size, (0, 0, 0, 0)), pt.ss)
    d = pt.draw()
    h, length = spec.palm_half_width, spec.palm_length
    # The heel's shade, fading up the palm in bands.
    for k in range(5):
        top = length * 0.4 * (1.0 - k / 5.0)
        d.polygon([pt.s(p) for p in (P(0, -h), P(top, -h), P(top, h), P(0, h))], fill=_a(style.shade, 0.12 * fade))
    knuckles = [P(length, f.across) for f in spec.fingers]
    lw = max(1, int(0.5 * cam.scale * pt.ss))
    if cam.palm_faces_us():
        # The PADS: the thumb's mound, the mound opposite, one under each knuckle.
        for along, off, rx, ry, a in ((0.35, -0.72, 7.5, 5.5, 0.55), (0.5, 0.67, 6.0, 4.5, 0.43)):
            q = P(length * along, h * off)
            rx, ry = rx * cam.scale, ry * cam.scale
            d.ellipse((*pt.s((q[0] - rx, q[1] - ry)), *pt.s((q[0] + rx, q[1] + ry))), fill=_a(style.highlight, a * fade))
        for f in spec.fingers:
            q = P(length - 3.2, f.across)
            rx, ry = 2.6 * cam.scale, 2.0 * cam.scale
            d.ellipse((*pt.s((q[0] - rx, q[1] - ry)), *pt.s((q[0] + rx, q[1] + ry))), fill=_a(style.highlight, 0.47 * fade))
        if style.palm_lines:
            # Its life line and heart line.
            for t0, t1, off in ((0.25, 0.75, -4.0), (0.45, 0.9, 3.5)):
                line = [P(length * t0, off), P(length * (t0 + t1) / 2, off + 2), P(length * t1, off * 0.5)]
                d.line([pt.s(p) for p in line], fill=_a(style.seam, 0.5 * fade), width=lw, joint="curve")
    else:
        # From the back its knuckle edge passes over the tucked fingers.
        d.line([pt.s(cam.project(p)) for p in knuckle_edge(spec, False)], fill=_a(style.seam, fade), width=max(1, int(0.9 * cam.scale * pt.ss)), joint="curve")
        if style.tendons:
            # One TENDON along each metacarpal, wrist to its own knuckle.
            for f, k in zip(spec.fingers, knuckles):
                start = P(3, f.across * 0.45)
                d.line([pt.s(start), pt.s(k)], fill=_a(style.highlight, 0.67 * fade), width=max(1, int(1.4 * cam.scale * pt.ss)))
                d.line([pt.s(P(3, f.across * 0.45 + 0.8)), pt.s(P(length, f.across + 0.8))], fill=_a(style.seam, 0.65 * fade), width=lw)
    if style.bone is not None:
        k = 0.3 if cam.palm_faces_us() else 0.9
        for f, end in zip(spec.fingers, knuckles):
            start = P(length * 0.18, f.across * 0.4)
            pt.glow(lambda g, a=start, b=end: g.line([pt.s(a), pt.s(b)], fill=_a(style.bone, 0.5 * glow * fade * k), width=int(1.6 * cam.scale * pt.ss)), 0.8 * cam.scale)
            pt.draw().line([pt.s(start), pt.s(end)], fill=_a(style.bone, 0.75 * fade * k), width=max(1, int(0.6 * cam.scale * pt.ss)))
    mask = Image.new("L", base.layer.size, 0)
    md = ImageDraw.Draw(mask)
    for part in (near, thumb_web(spec, pose)):
        md.polygon([pt.s(cam.project(p)) for p in part], fill=255)
    detail = np.asarray(pt.layer, np.float32)
    detail[..., 3] *= np.asarray(mask, np.float32) / 255.0
    base.layer.alpha_composite(Image.fromarray(detail.astype(np.uint8), "RGBA"))


def _draw_knuckles(pt: _Painter, spec: HandSpec, pose: HandPose, cam: Camera, style: HandStyle, fade: float) -> None:
    """The KNUCKLE ROW from the back: a raised bump per finger, the more
    prominent the more it curls (the fist's ridge)."""
    if cam.palm_faces_us():
        return
    d = pt.draw()
    for f in spec.fingers:
        q = cam.project(local(spec, spec.palm_length, f.across, -spec.palm_depth / 2 - spec.palm_arch * 0.6))
        r = f.width * cam.scale * (0.5 + 0.22 * max(0.0, pose.curl(f.name)))
        d.ellipse((*pt.s((q[0] - r, q[1] - r * 0.85)), *pt.s((q[0] + r, q[1] + r * 0.85))), fill=_a(style.flesh, fade), outline=_a(style.seam, 0.35 * fade), width=max(1, int(0.5 * cam.scale * pt.ss)))
        hr = r * 0.55
        o = 0.6 * cam.scale
        d.ellipse((*pt.s((q[0] - hr - o, q[1] - hr - 1.5 * o)), *pt.s((q[0] + hr - o, q[1] + hr * 0.4 - 1.5 * o))), fill=_a(style.highlight, 0.24 * fade))


def _hull(points: List[Point]) -> List[Point]:
    """The convex hull (monotone chain)."""
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _ink(hand: Image.Image, style: HandStyle, ss: int, scale: float, fade: float) -> Image.Image:
    """One outline round the whole silhouette (its flesh, not its glows),
    under the hand."""
    a = np.asarray(hand, np.float32)[..., 3] / 255.0
    body = np.clip((a - 0.45) / 0.25, 0.0, 1.0)
    grow = 2 * max(1, int(0.7 * style.ink_width * scale * ss)) + 1
    grown = np.asarray(Image.fromarray((body * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(0.3 * ss)), np.float32) / 255.0
    ring = np.clip(grown - body, 0.0, 1.0) * fade
    ink = np.zeros(a.shape + (4,), np.uint8)
    ink[..., :3] = style.ink[:3]
    ink[..., 3] = (ring * style.ink[3]).astype(np.uint8)
    out = Image.fromarray(ink, "RGBA")
    out.alpha_composite(hand)
    return out


def _light(img: Image.Image, cam: Camera, style: HandStyle, ss: int) -> Image.Image:
    """Lit from the upper left, darker toward the hand's lower side; a rim
    light along its upper edges if the style has one. Alpha is kept."""
    px = np.asarray(img, np.float32)
    h, w = px.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    span = 50.0 * cam.scale
    rel = (ys / ss - (cam.wrist[1] - 30.0 * cam.scale)) / span
    light = np.clip(1.12 - 0.42 * rel - 0.06 * (xs / ss - cam.wrist[0]) / (1.2 * span), 0.6, 1.15)
    rgb = px[..., :3] * light[..., None]
    if style.rim is not None:
        a = px[..., 3] / 255.0
        above = np.roll(a, max(1, int(1.4 * cam.scale * ss)), axis=0)
        rim = np.clip(a - above, 0, 1) * (a > 0.5)
        rim = np.asarray(Image.fromarray((rim * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6 * ss)), np.float32) / 255.0
        rgb = rgb + rim[..., None] * np.array(style.rim[:3], np.float32) * 0.7
    px[..., :3] = np.clip(rgb, 0, 255)
    return Image.fromarray(px.astype(np.uint8), "RGBA")


def draw_hand(spec: HandSpec, pose: HandPose, cam: Camera, canvas: Tuple[int, int], style: HandStyle = STYLES["skin"], ss: int = 4,
              glow: float = 0.7, fade: float = 1.0, tip_fade: float = 0.0, between: Optional[Callable[[Image.Image, Dict[str, Point], int], None]] = None) -> HandDrawing:
    """The hand posed and seen, on a transparent ``canvas`` (frame px) at
    ``ss`` x. ``fade`` fades it all; ``tip_fade`` eats the digits from their
    tips (0..1); ``glow`` drives the spectral style's bones. ``between`` is
    called (layer, landmarks, ss) where something HELD would draw: over the
    palm, under the fingers that close on it (a die in a cupped hand)."""
    layer = Image.new("RGBA", (canvas[0] * ss, canvas[1] * ss), (0, 0, 0, 0))
    pt = _Painter(layer, ss)
    marks = landmarks(spec, pose, cam)
    ds = digits(spec, pose)
    fingers = [ds[n] for n in FINGER_NAMES]
    args = (style, glow, fade, tip_fade)
    if cam.palm_faces_us():
        # From the palm: the palm, a held thing, the fingers folding toward
        # us over it (little to index), the thumb across them.
        _draw_palm(pt, spec, pose, cam, style, glow, fade)
        if between:
            between(layer, marks, ss)
        for dg in reversed(fingers):
            _draw_digit(pt, cam, dg, *args)
        _draw_digit(pt, cam, ds["thumb"], *args)
    else:
        # From the back: the thumb on the far edge, the fingers folding away
        # behind the knuckle row, the back of the hand over them, then each
        # finger's first phalanx again where it leaves the knuckles.
        _draw_digit(pt, cam, ds["thumb"], *args)
        for dg in fingers:
            _draw_digit(pt, cam, dg, *args)
        _draw_palm(pt, spec, pose, cam, style, glow, fade)
        for dg in fingers:
            _draw_digit(pt, cam, dg, *args, only_first=True)
        _draw_knuckles(pt, spec, pose, cam, style, fade)
        if between:
            between(layer, marks, ss)
    out = _light(_ink(layer, style, ss, cam.scale, fade), cam, style, ss)
    return HandDrawing(out, marks, ss)
