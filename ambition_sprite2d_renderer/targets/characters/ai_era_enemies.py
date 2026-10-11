"""Custom sprite-sheet generators for AI-culture enemy archetypes.

This module intentionally avoids the repo's human / toon rigs. Each target is a
standalone custom creature or animated prop-creature rendered directly with PIL.

Targets provided:
- puppy_slug_variant2   : psychedelic dog-face slug homage to DeepDream era (puppy_slug variant).
- hand_saint            : floating palm-idol diffusion-hand horror saint.

The tack-on registry discovers this module automatically because it exposes a
TARGETS dict. Each entry renders a separate spritesheet.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_ROWS: Dict[str, List[Tuple[str, int, int]]] = {
    "puppy_slug_variant2": [
        ("idle", 6, 125),
        ("crawl", 8, 92),
        ("gaze", 6, 98),
        ("lunge", 6, 82),
        ("howl", 6, 102),
        ("hurt", 4, 90),
        ("death", 8, 112),
    ],
    "hand_saint": [
        ("idle", 6, 126),
        ("hover", 8, 92),
        ("bless", 6, 94),
        ("grasp", 6, 86),
        ("judgement", 6, 88),
        ("hurt", 4, 90),
        ("death", 8, 112),
    ],
}

FRAME_SIZE = (320, 320)
WORK_FRAME_SIZE = (640, 640)  # logical canvas is 160×160 at SUPER=4.
SUPER = 4
OUTLINE = (28, 22, 28, 255)
WHITE = (250, 250, 250, 255)
BLACK = (28, 24, 28, 255)
YELLOW = (246, 222, 108, 255)
CYAN = (106, 222, 242, 255)
MAGENTA = (244, 114, 214, 255)
GREEN = (140, 236, 136, 255)


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(p: Point) -> Tuple[int, int]:
    return (_s(p[0]), _s(p[1]))


def _box(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _poly(
    draw: ImageDraw.ImageDraw,
    pts: Sequence[Point],
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    ipts = [_pt(p) for p in pts]
    draw.polygon(ipts, fill=fill)
    if outline is not None and width > 0 and len(ipts) >= 2:
        draw.line(
            ipts + [ipts[0]], fill=outline, width=max(1, _s(width)), joint="curve"
        )


def _line(
    draw: ImageDraw.ImageDraw, pts: Sequence[Point], fill: RGBA, width: float = 1.0
) -> None:
    if len(pts) >= 2:
        draw.line(
            [_pt(p) for p in pts], fill=fill, width=max(1, _s(width)), joint="curve"
        )


def _ellipse(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        _box(cx, cy, rx, ry),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)) if outline is not None else 0,
    )


def _alpha_ellipse(
    target: Image.Image, cx: float, cy: float, rx: float, ry: float, fill: RGBA
) -> None:
    """Alpha-composite a translucent ellipse onto ``target``.

    PIL's ``ImageDraw.ellipse(fill=(r, g, b, a<255))`` writes the
    translucent RGBA into the destination pixels directly — it does
    NOT blend against whatever was already there. For damage flashes
    and other wash overlays that must sit ON TOP of the existing
    body pixels, draw onto a fresh transparent layer first and
    ``Image.alpha_composite`` it onto the target. Without this the
    hurt tint erases the body wherever the ellipse covers.
    """
    overlay = Image.new("RGBA", target.size, (0, 0, 0, 0))
    od = blending_draw(overlay)
    od.ellipse(_box(cx, cy, rx, ry), fill=fill)
    rigdoc.composite_canvas(target, overlay)


def _circle(
    draw: ImageDraw.ImageDraw,
    p: Point,
    r: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    _ellipse(draw, p[0], p[1], r, r, fill, outline, width)


def _bezier(a: Point, b: Point, c: Point, d: Point, steps: int = 18) -> List[Point]:
    pts: List[Point] = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        pts.append(
            (
                u * u * u * a[0]
                + 3 * u * u * t * b[0]
                + 3 * u * t * t * c[0]
                + t * t * t * d[0],
                u * u * u * a[1]
                + 3 * u * u * t * b[1]
                + 3 * u * t * t * c[1]
                + t * t * t * d[1],
            )
        )
    return pts


def _ribbon(
    draw: ImageDraw.ImageDraw,
    pts: Sequence[Point],
    width: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    highlight: RGBA | None = None,
) -> None:
    _line(draw, pts, outline, width + 1.8)
    _line(draw, pts, fill, width)
    if highlight is not None:
        hi = [(x - width * 0.08, y - width * 0.10) for x, y in pts]
        _line(draw, hi, highlight, max(0.8, width * 0.2))


def _capsule(
    draw: ImageDraw.ImageDraw,
    a: Point,
    b: Point,
    width: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    highlight: RGBA | None = None,
) -> None:
    _ribbon(draw, [a, b], width, fill, outline, highlight)
    _circle(draw, a, width / 2.0, fill, outline, 0.8)
    _circle(draw, b, width / 2.0, fill, outline, 0.8)


def _star(
    draw: ImageDraw.ImageDraw,
    center: Point,
    r1: float,
    r2: float,
    points: int,
    fill: RGBA,
    outline: RGBA = OUTLINE,
) -> None:
    pts: List[Point] = []
    for i in range(points * 2):
        ang = math.radians(-90 + i * 180.0 / points)
        rr = r1 if i % 2 == 0 else r2
        pts.append((center[0] + math.cos(ang) * rr, center[1] + math.sin(ang) * rr))
    _poly(draw, pts, fill, outline, 0.8)


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


# ---------------------------------------------------------------------------
# Pieces
#
# Every enemy here is drawn as a rig: each rigid thing (a body, a card, a
# face, a hand, a drone) is painted ONCE by its painter on a scratch canvas
# with its anchor at ``HOME``, cut to what it covers, and placed (and turned)
# through ``shape_rig``. A part flipbook stores each once. A thing that
# changes shape with the pose (a grin opening, a bending arm) is one piece per
# pose value. The old renderers turned a whole body layer each frame, so each
# frame was one picture; a ``_Frame`` turns the body's pieces instead.

#: Where a piece's anchor is painted (logical pixels) on the scratch canvas,
#: which is twice the work frame.
HOME = (float(WORK_FRAME_SIZE[0]) / SUPER, float(WORK_FRAME_SIZE[1]) / SUPER)
_PIECES: Dict[tuple, object] = {}


def _piece(key: tuple, paint: Callable):
    """``(raster, anchor)``: what ``paint(draw)`` paints with its anchor at
    ``HOME``, cut to its box; ``None`` when it paints nothing. ``key`` must
    name everything ``paint`` reads."""
    if key not in _PIECES:
        canvas = Image.new("RGBA", (WORK_FRAME_SIZE[0] * 2, WORK_FRAME_SIZE[1] * 2), (0, 0, 0, 0))
        paint(blending_draw(canvas))
        box = canvas.getchannel("A").getbbox()
        _PIECES[key] = None if box is None else (canvas.crop(box), (HOME[0] * SUPER - box[0], HOME[1] * SUPER - box[1]))
    return _PIECES[key]


class _Frame:
    """A rigid frame pieces ride: turned ``degrees`` (clockwise, as
    ``shape_rig``) about ``pivot`` (logical pixels). ``Image.rotate(a)``
    turns by ``-a`` here."""

    def __init__(self, pivot: Point = (0.0, 0.0), degrees: float = 0.0) -> None:
        self.pivot = pivot
        self.degrees = degrees

    def put(self, img: Image.Image, key: tuple, paint: Callable, at: Point, name: str, degrees: float = 0.0) -> None:
        """Place the piece ``key`` with its anchor at ``at`` (logical pixels
        of this frame, before its turn), turned ``degrees`` more."""
        part = _piece(key, paint)
        if part is not None:
            self.place(img, part, at, name, degrees)

    def place(self, img: Image.Image, part, at: Point, name: str, degrees: float = 0.0, opacity: float = 1.0) -> None:
        """Place the raster ``part`` = (image, anchor) as ``put`` places a
        piece, its alpha scaled by ``opacity``."""
        px, py = self.pivot
        dx, dy = at[0] - px, at[1] - py
        c, s = math.cos(math.radians(self.degrees)), math.sin(math.radians(self.degrees))
        x, y = px + dx * c - dy * s, py + dx * s + dy * c
        rigdoc.blit_rotated(img, part[0], part[1], (x * SUPER, y * SUPER), self.degrees + degrees, round(opacity, 3), part_name=name)


#: The frame itself: no turn.
WORLD = _Frame()


def _stroke_piece(img: Image.Image, frame: _Frame, a: Point, b: Point, paint_line: Callable, key: tuple, name: str) -> None:
    """A straight thing from ``a`` to ``b`` as one piece per quarter-pixel
    length, turned to it: ``paint_line(draw, start, end)`` paints it along +x."""
    length = round(math.hypot(b[0] - a[0], b[1] - a[1]) * 4) / 4
    hx, hy = HOME
    frame.put(
        img,
        key + (length,),
        lambda d: paint_line(d, (hx, hy), (hx + length, hy)),
        a,
        name,
        math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])),
    )


def _new_frame() -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", WORK_FRAME_SIZE, (0, 0, 0, 0))
    return img, blending_draw(img)


def _emotion_eye(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    rx: float,
    ry: float,
    iris: RGBA,
    pupil_shift: float = 0.0,
    blink: float = 0.0,
    outline: RGBA = OUTLINE,
) -> None:
    ry2 = max(0.6, ry * (1.0 - blink))
    _ellipse(draw, x, y, rx, ry2, WHITE, outline, 0.8)
    if blink < 0.92:
        _circle(
            draw, (x + pupil_shift, y + 0.2), min(rx, ry2) * 0.55, iris, outline, 0.7
        )
        _circle(
            draw, (x + pupil_shift * 1.18, y + 0.3), min(rx, ry2) * 0.24, BLACK, None, 0
        )
        _circle(
            draw,
            (x + pupil_shift * 0.8 - 0.7, y - 0.7),
            max(0.5, min(rx, ry2) * 0.12),
            (255, 255, 255, 180),
            None,
            0,
        )


def _draw_hand(
    draw: ImageDraw.ImageDraw,
    wrist: Point,
    ang: float,
    spread: float,
    scale: float,
    palm: RGBA,
    finger: RGBA | None = None,
    outline: RGBA = OUTLINE,
) -> Point:
    finger = finger or palm
    length1 = 9.0 * scale
    length2 = 7.0 * scale
    hand = (
        wrist[0] + math.cos(math.radians(ang)) * length1,
        wrist[1] + math.sin(math.radians(ang)) * length1,
    )
    _capsule(draw, wrist, hand, 4.4 * scale, palm, outline, None)
    _circle(draw, hand, 4.6 * scale, palm, outline, 0.7)
    for i, off in enumerate([-34, -12, 10, 30]):
        a = ang - 8 + off + spread * (i - 1.5)
        tip = (
            hand[0] + math.cos(math.radians(a)) * length2,
            hand[1] + math.sin(math.radians(a)) * length2,
        )
        _capsule(draw, hand, tip, 1.9 * scale, finger, outline, None)
    thumb_a = ang + 115
    thumb = (
        hand[0] + math.cos(math.radians(thumb_a)) * (length2 * 0.75),
        hand[1] + math.sin(math.radians(thumb_a)) * (length2 * 0.75),
    )
    _capsule(draw, hand, thumb, 1.8 * scale, finger, outline, None)
    return hand


def _noise_squiggles(
    draw: ImageDraw.ImageDraw, pts: Sequence[Point], color: RGBA, width: float = 0.8
) -> None:
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        _line(draw, [a, b], color, width)


# ---------------------------------------------------------------------------
# DeepDream puppy slug


def _pose_puppy_slug_v2(anim: str, frame_idx: int, nframes: int) -> Dict[str, float]:
    t = 0.0 if nframes <= 1 else frame_idx / float(max(1, nframes - 1))
    cyc = math.tau * frame_idx / max(1, nframes)
    s = math.sin(cyc)
    pose = {
        "x": 0.0,
        "bob": 0.0,
        "wave": s,
        "stretch": 0.0,
        "eyes": 0.0,
        "mouth": 0.0,
        "coil": 0.0,
        "impact": 0.0,
        "dead": 0.0,
    }
    if anim == "idle":
        pose["bob"] = s * 1.2
        pose["eyes"] = max(0.0, s) * 0.15
    elif anim == "crawl":
        pose["x"] = s * 2.4
        pose["bob"] = abs(s) * 2.1 - 0.3
        pose["stretch"] = s * 0.7
    elif anim == "gaze":
        tt = _ease(t)
        pose["bob"] = -math.sin(tt * math.pi) * 1.2
        pose["eyes"] = 0.18 + math.sin(tt * math.pi) * 0.32
        pose["mouth"] = 0.08
    elif anim == "lunge":
        tt = _ease(t)
        pose["x"] = _lerp(-4.0, 10.0, tt)
        pose["stretch"] = _lerp(-0.4, 1.0, tt)
        pose["bob"] = -math.sin(tt * math.pi) * 2.0
        pose["mouth"] = 0.15 + math.sin(tt * math.pi) * 0.2
        pose["impact"] = math.sin(tt * math.pi)
    elif anim == "howl":
        pose["bob"] = s * 1.0
        pose["coil"] = max(0.0, s) * 1.0
        pose["mouth"] = 0.18 + max(0.0, s) * 0.26
        pose["eyes"] = 0.2
    elif anim == "hurt":
        hit = math.sin(t * math.pi)
        pose["x"] = (1 if frame_idx % 2 == 0 else -1) * 2.0
        pose["bob"] = -hit * 1.2
        pose["impact"] = hit
        pose["eyes"] = 0.12 * hit
    elif anim == "death":
        tt = _ease(t)
        pose["x"] = tt * 7.0
        pose["bob"] = tt * 8.0
        pose["stretch"] = -0.6 * tt
        pose["dead"] = tt
    return pose


def _draw_puppy_head(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    scale: float,
    tilt: float,
    eye_pop: float,
    palette: Tuple[RGBA, RGBA, RGBA],
) -> None:
    fur, fur_hi, muzzle = palette
    head = Image.new("RGBA", draw._image.size, (0, 0, 0, 0))
    hd = blending_draw(head)
    _ellipse(hd, cx, cy, 7.5 * scale, 6.2 * scale, fur, OUTLINE, 0.8)
    _poly(
        hd,
        [
            (cx - 6.5 * scale, cy - 3.0 * scale),
            (cx - 11.0 * scale, cy - 8.6 * scale),
            (cx - 4.5 * scale, cy - 7.0 * scale),
        ],
        fur_hi,
        OUTLINE,
        0.8,
    )
    _poly(
        hd,
        [
            (cx + 6.3 * scale, cy - 3.2 * scale),
            (cx + 10.8 * scale, cy - 8.0 * scale),
            (cx + 4.3 * scale, cy - 7.3 * scale),
        ],
        fur_hi,
        OUTLINE,
        0.8,
    )
    _ellipse(
        hd,
        cx + 5.4 * scale,
        cy + 1.5 * scale,
        4.6 * scale,
        3.7 * scale,
        muzzle,
        OUTLINE,
        0.7,
    )
    _emotion_eye(
        hd,
        cx - 1.2 * scale,
        cy - 0.9 * scale,
        2.0 * scale,
        2.4 * scale,
        CYAN,
        pupil_shift=eye_pop * 0.4,
    )
    _emotion_eye(
        hd,
        cx + 2.4 * scale,
        cy - 0.7 * scale,
        2.0 * scale,
        2.4 * scale,
        MAGENTA,
        pupil_shift=eye_pop * 0.6,
    )
    _circle(hd, (cx + 8.2 * scale, cy + 1.6 * scale), 0.95 * scale, BLACK, None, 0)
    _line(
        hd,
        [(cx + 7.8 * scale, cy + 4.0 * scale), (cx + 10.2 * scale, cy + 3.2 * scale)],
        BLACK,
        0.8,
    )
    for whisk in (-1, 1):
        _line(
            hd,
            [
                (cx + 9.5 * scale, cy + 2.2 * scale),
                (cx + 12.5 * scale, cy + 1.0 * whisk + 2.0 * scale),
            ],
            fur_hi,
            0.7,
        )
    if tilt:
        head = head.rotate(tilt, center=_pt((cx, cy)))
    rigdoc.composite_canvas(draw._image, head)


def _render_puppy_slug_v2(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose_puppy_slug_v2(anim, frame_idx, nframes)
    img, _draw = _new_frame()
    hx, hy = HOME
    body = (212, 196, 112, 255)
    body_hi = (234, 220, 150, 255)
    body_lo = (132, 110, 118, 255)
    ridge = (170, 120, 188, 255)
    dead = round(pose["dead"], 3)
    eyes = round(pose["eyes"], 3)
    dorsal_pts: List[Point] = []
    last: Point | None = None
    # The body: a segment piece per segment (its size), and a ribbon piece
    # per length from the segment before, turned to it.
    for i in range(10):
        tt = i / 9.0
        x = 34 + tt * 82 + pose["x"] * 0.8
        y = (
            95
            + math.sin(tt * math.pi * 1.5 + frame_idx * 0.7)
            * (3.0 + pose["stretch"] * 2.0)
            + pose["bob"]
            + tt * pose["dead"] * 9.0
        )
        r = round(10.5 - abs(tt - 0.46) * 7.2 - dead * 2.0, 3)

        def segment(d, r=r) -> None:
            _ellipse(d, hx, hy, r * 1.35, r, OUTLINE, None, 0)
            _ellipse(d, hx, hy, r * 1.2, r * 0.92, body, OUTLINE, 0.8)
            _ellipse(d, hx - 1.5, hy - 1.3, r * 0.75, r * 0.46, body_hi, None, 0)
            _ellipse(d, hx + 2.0, hy + 2.4, r * 0.64, r * 0.36, body_lo, None, 0)

        WORLD.put(img, ("ps2_segment", r), segment, (x, y), f"segment_{i}")
        if last is not None:
            _stroke_piece(
                img,
                WORLD,
                last,
                (x, y),
                lambda d, a, b: _ribbon(d, [a, b], 9.5, body, OUTLINE, body_hi),
                ("ps2_ribbon",),
                f"ribbon_{i}",
            )
        dorsal_pts.append((x - r * 0.15, y - r * 0.85))
        last = (x, y)

    # The dorsal faces: a ridge bead and two eyes, one piece per gaze.
    def bump(d) -> None:
        _circle(d, (hx, hy - 4.2), 2.0, ridge, OUTLINE, 0.6)
        _emotion_eye(d, hx - 3.2, hy - 3.6, 1.5, 1.9, GREEN, pupil_shift=eyes * 1.4)
        _emotion_eye(d, hx + 0.8, hy - 2.8, 1.6, 2.0, MAGENTA, pupil_shift=eyes * 1.2)

    for i, (x, y) in enumerate(dorsal_pts[2:8]):
        WORLD.put(img, ("ps2_bump", eyes), bump, (x, y), f"bump_{i}")

    head_y = 90 + pose["bob"] + pose["coil"] * -3.0 + pose["dead"] * 10.0
    head_x = 110 + pose["x"]
    scale = round(1.15 + pose["coil"] * 0.08, 3)
    eye_pop = round(pose["eyes"] * 5.0, 3)
    WORLD.put(
        img,
        ("ps2_head", scale, eye_pop),
        lambda d: _draw_puppy_head(d, hx, hy, scale, 0.0, eye_pop, (body, body_hi, (238, 226, 182, 255))),
        (head_x, head_y),
        "head",
        -(pose["coil"] * 5.0 - pose["dead"] * 18.0),
    )
    mouth = round(pose["mouth"], 3)
    WORLD.put(
        img,
        ("ps2_mouth", mouth),
        lambda d: _line(d, [(hx, hy), (hx + 3.7, hy + mouth * 8.0)], BLACK, 1.1),
        (head_x + 11.3, head_y + 7.5),
        "mouth",
    )
    for j in range(3):
        WORLD.put(
            img,
            ("ps2_dot",),
            lambda d: _circle(d, (hx, hy), 1.7, ridge, None, 0),
            (58 + j * 18, 104 + pose["bob"] + math.sin(frame_idx * 0.7 + j) * 2),
            f"dot_{j}",
        )
    if anim == "gaze":
        def stars(d) -> None:
            for ox in (-8, 3, 14):
                _star(d, (hx + ox, hy), 3.0 + eyes * 4.0, 1.5, 6, (255, 244, 150, 110), None)

        WORLD.put(img, ("ps2_stars", eyes), stars, (head_x, head_y - 8), "stars")
    if anim == "lunge":
        impact = round(pose["impact"], 3)
        WORLD.put(
            img,
            ("ps2_lunge", impact),
            lambda d: _line(d, [(hx, hy), (hx + 18 + impact * 10, hy - 5)], (255, 236, 180, 180), 2.2),
            (120, 95),
            "lunge",
        )
    if anim == "howl":
        def howl(d) -> None:
            for i in range(3):
                a = 0.2 + i * 0.55
                pts = _bezier(
                    (hx, hy),
                    (hx + 7 + i * 4, hy - 8 - i * 6),
                    (hx + 19 + i * 10, hy - 12 - i * 3),
                    (hx + 29 + i * 10, hy - 6 - i * 2),
                    10,
                )
                _noise_squiggles(d, pts, (218, 186, 255, int(140 - i * 26)), 0.9 + a)

        WORLD.put(img, ("ps2_howl",), howl, (123, 86), "howl")
    return _downsample(img)


# ---------------------------------------------------------------------------
# Hand saint


def _pose_saint(anim: str, frame_idx: int, nframes: int) -> Dict[str, float]:
    t = 0.0 if nframes <= 1 else frame_idx / float(max(1, nframes - 1))
    cyc = math.tau * frame_idx / max(1, nframes)
    s = math.sin(cyc)
    pose = {
        "bob": 0.0,
        "tilt": 0.0,
        "halo": 0.0,
        "grasp": 0.0,
        "bless": 0.0,
        "judge": 0.0,
        "hurt": 0.0,
        "dead": 0.0,
    }
    if anim == "idle":
        pose["bob"] = s * 1.3
        pose["halo"] = s * 4.0
    elif anim == "hover":
        pose["bob"] = math.sin(cyc * 1.1) * 2.6
        pose["tilt"] = s * 2.2
        pose["halo"] = frame_idx * 7.0
    elif anim == "bless":
        tt = _ease(t)
        pose["bless"] = math.sin(tt * math.pi)
        pose["halo"] = tt * 18.0
    elif anim == "grasp":
        tt = _ease(t)
        pose["grasp"] = math.sin(tt * math.pi)
        pose["tilt"] = -8.0 + tt * 10.0
    elif anim == "judgement":
        tt = _ease(t)
        pose["judge"] = math.sin(tt * math.pi)
        pose["halo"] = tt * 36.0
    elif anim == "hurt":
        hit = math.sin(t * math.pi)
        pose["hurt"] = hit
        pose["tilt"] = (1 if frame_idx % 2 == 0 else -1) * 5.0
    elif anim == "death":
        tt = _ease(t)
        pose["dead"] = tt
        pose["tilt"] = tt * 40.0
        pose["bob"] = tt * 8.0
        pose["halo"] = tt * 48.0
    return pose


def _paint_saint_robe(d, cx: float, cy: float) -> None:
    robe_pts = [
        (cx - 18, cy + 12),
        (cx - 28, cy + 40),
        (cx - 18, cy + 56),
        (cx, cy + 62),
        (cx + 18, cy + 56),
        (cx + 30, cy + 38),
        (cx + 18, cy + 12),
        (cx + 6, cy + 4),
        (cx - 6, cy + 4),
    ]
    _poly(d, robe_pts, (118, 94, 154, 255), OUTLINE, 0.9)
    _poly(d, [(cx - 12, cy + 12), (cx - 6, cy + 55), (cx + 4, cy + 58), (cx - 2, cy + 8)], (152, 132, 190, 180), None, 0)


def _paint_saint_palm(d, cx: float, cy: float, dead: float, judge: float) -> None:
    """The palm torso, its fingers, its eye and the yellow mark."""
    palm_c = (cx, cy - 4)
    _circle(d, palm_c, 12, (244, 226, 198, 255), OUTLINE, 0.8)
    for a in (-50, -22, 0, 22, 48):
        root = (
            palm_c[0] + math.cos(math.radians(a - 90)) * 6.0,
            palm_c[1] - 7.0 + math.sin(math.radians(a - 90)) * 3.0,
        )
        tip = (root[0] + math.sin(math.radians(a)) * 3.0, root[1] - 11.0 - abs(a) * 0.05)
        _capsule(d, root, tip, 3.0, (244, 226, 198, 255), OUTLINE, None)
    thumb_root = (palm_c[0] - 8.0, palm_c[1] + 1.0)
    thumb_tip = (thumb_root[0] - 7.0, thumb_root[1] + 5.0)
    _capsule(d, thumb_root, thumb_tip, 3.0, (244, 226, 198, 255), OUTLINE, None)
    _emotion_eye(d, palm_c[0], palm_c[1] + 1.0, 3.4, 4.1, CYAN, blink=dead * 0.95)
    _circle(d, (palm_c[0], palm_c[1] + 8.5), 1.5 + judge * 0.8, YELLOW, OUTLINE, 0.6)


def _render_hand_saint(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose_saint(anim, frame_idx, nframes)
    img, _draw = _new_frame()
    hx, hy = HOME
    cx = 80
    cy = 84 + pose["bob"]
    body = _Frame((cx, cy + 10), -pose["tilt"])
    body.put(img, ("saint_robe",), lambda d: _paint_saint_robe(d, hx, hy), (cx, cy), "robe")
    dead = round(pose["dead"], 3)
    judge = round(pose["judge"], 3)
    body.put(img, ("saint_palm", dead, judge), lambda d: _paint_saint_palm(d, hx, hy, dead, judge), (cx, cy), "palm")

    # Arms/hands: each hand one piece per spread, turned at its wrist.
    def arms(d) -> None:
        _capsule(d, (hx - 8, hy + 10), (hx - 14, hy + 18), 4.0, (208, 188, 166, 255), OUTLINE, None)
        _capsule(d, (hx + 8, hy + 10), (hx + 14, hy + 18), 4.0, (208, 188, 166, 255), OUTLINE, None)

    body.put(img, ("saint_arms",), arms, (cx, cy), "arms")
    spread = round(8 + pose["grasp"] * 10, 3)
    for name, wrist, ang in (
        ("left_hand", (cx - 14, cy + 18), 145 - pose["grasp"] * 45 + pose["bless"] * 10),
        ("right_hand", (cx + 14, cy + 18), 35 + pose["grasp"] * 45 - pose["bless"] * 10),
    ):
        body.put(
            img,
            ("saint_hand", spread),
            lambda d: _draw_hand(d, (hx, hy), 0.0, spread=spread, scale=0.9, palm=(244, 226, 198, 255)),
            wrist,
            name,
            ang,
        )
    # Halo of smaller hands: one piece, placed and turned six times.
    for i in range(6):
        ang = pose["halo"] + i * 60.0
        body.put(
            img,
            ("saint_halo_hand",),
            lambda d: _draw_hand(
                d, (hx, hy), 0.0, spread=3.0, scale=0.42, palm=(230, 214, 186, 255), finger=(244, 226, 198, 255), outline=(150, 132, 164, 255)
            ),
            (cx + math.cos(math.radians(ang)) * 22.0, cy - 24 + math.sin(math.radians(ang)) * 11.0),
            f"halo_hand_{i}",
            ang + 90,
        )
    if pose["judge"] > 0.0:
        def stars(d) -> None:
            for i in range(3):
                _star(d, (hx, hy - i * 6), 3.8 + i * 1.0 + judge * 4.0, 1.6 + i * 0.4, 8, (255, 236, 160, int(140 - i * 20)), None)

        body.put(img, ("saint_stars", judge), stars, (cx, cy - 34), "stars")
    if pose["bless"] > 0.0:
        def bless(d) -> None:
            for side in (-1, 1):
                pts = _bezier(
                    (hx + side * 12, hy + 6),
                    (hx + side * 26, hy + 4),
                    (hx + side * 34, hy + 14),
                    (hx + side * 42, hy + 4),
                    12,
                )
                _ribbon(d, pts, 1.6, (255, 236, 170, 148), None)

        body.put(img, ("saint_bless",), bless, (cx, cy), "bless")
    if pose["hurt"] > 0.0:
        hurt = round(pose["hurt"], 3)
        body.put(
            img,
            ("saint_hurt", hurt),
            lambda d: _alpha_ellipse(d._image, hx, hy, 26, 30, (255, 94, 112, int(80 * hurt))),
            (cx, cy + 10),
            "hurt",
        )
    return _downsample(img)


# ---------------------------------------------------------------------------
# Grid-cut pieces

#: Grid-cut pieces (``_grid_piece``).
_GRID = 8
_GRID_PIECES: Dict[tuple, object] = {}


def _grid_piece(key: tuple, paint: Callable, keep: Tuple[float, float, float, float] | None = None):
    """``_piece`` cut on a grid of ``_GRID`` canvas pixels, so a mirrored or
    turned copy reduces to the exact transform of the reduced piece. ``keep``
    = (x0, y0, x1, y1), logical offsets from ``HOME``, keeps only that region
    of what ``paint`` paints (a half or a quarter of a symmetric thing)."""
    if key not in _GRID_PIECES:
        size = (WORK_FRAME_SIZE[0] * 2, WORK_FRAME_SIZE[1] * 2)
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        paint(blending_draw(canvas))
        if keep is not None:
            mask = Image.new("L", size, 0)
            x0, y0, x1, y1 = (_s(HOME[0] + keep[0]), _s(HOME[1] + keep[1]), _s(HOME[0] + keep[2]), _s(HOME[1] + keep[3]))
            ImageDraw.Draw(mask).rectangle((max(0, x0), max(0, y0), min(size[0], x1) - 1, min(size[1], y1) - 1), fill=255)  # raw-draw-ok: an L crop mask (which region of a piece to keep), not content
            canvas = Image.composite(canvas, Image.new("RGBA", size, (0, 0, 0, 0)), mask)
        box = canvas.getchannel("A").getbbox()
        if box is None:
            _GRID_PIECES[key] = None
        else:
            x0, y0 = box[0] - box[0] % _GRID, box[1] - box[1] % _GRID
            x1, y1 = box[2] + (-box[2]) % _GRID, box[3] + (-box[3]) % _GRID
            _GRID_PIECES[key] = (canvas.crop((x0, y0, x1, y1)), (HOME[0] * SUPER - x0, HOME[1] * SUPER - y0))
    return _GRID_PIECES[key]


# ---------------------------------------------------------------------------
# Discovery integration


def _render_target(
    target: str,
    frame_fn: Callable[[str, int, int], Image.Image],
    out_dir: str | Path,
    *,
    label_width: int = 124,
) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=target,
        rows=TARGET_ROWS[target],
        render_fn=frame_fn,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=label_width,
        auto_crop=True,
        crop_margin=2,
    )
    parts = publish_rig_flipbook(target, TARGET_ROWS[target], frame_fn, outputs, frame_transform, out_dir)
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ] + list(parts.values())


def _entry(
    target: str,
    frame_fn: Callable[[str, int, int], Image.Image],
    label_width: int = 124,
) -> Dict[str, object]:
    return {
        "render": lambda out_dir, **opts: _render_target(
            target, frame_fn, out_dir, label_width=label_width
        ),
        "sheet_files": [
            f"{target}_spritesheet.png",
            f"{target}_spritesheet.yaml",
            f"{target}_spritesheet.ron",
        ],
    }


TARGETS = {
    "puppy_slug_variant2": _entry("puppy_slug_variant2", _render_puppy_slug_v2, 142),
    "hand_saint": _entry("hand_saint", _render_hand_saint, 124),
}

__all__ = ["TARGETS"]

# ---- Local actor-contract metadata -------------------------------------------------
# Keep per-target actor metadata with the multi-renderer so the contract stays
# tied to the drawn entity instead of a central registry table.
LOCAL_ACTOR_METADATA_BY_TARGET = {
    "hand_saint": {
        "actor": {"character_id": "npc_hand_saint", "display_name": "Hand Saint"},
        "body": {
            "body_plan": "PropActor",
            "body_kind": "PropLike",
            "mass_class": "Light",
            "traits": ["floating", "prop_actor", "ai_era"],
            "locomotion_hint": "Float",
        },
        "capabilities": {
            "traversal": {
                "walk": False,
                "jump": None,
                "climb": None,
                "fly": True,
                "swim": None,
                "crawl": None,
                "use_lifts": None,
                "door_access": [],
            },
            "interactions": {
                "talk": None,
                "trade": None,
                "carry": None,
                "open_doors": [],
            },
        },
        "brain": {"default_preset": "skirmisher_ranger"},
        "actions": {"default_preset": "boss_bolt"},
        "visual": {"default_pose": "idle"},
        "tags": ["floating", "prop_actor", "ai_era"],
        "sockets": {
            "center": {
                "source": "explicit.profile.floating_prop",
                "point": {"x": 80.0, "y": 80.0},
            },
            "projectile_origin": {
                "source": "explicit.profile.hand_saint",
                "point": {"x": 80.0, "y": 58.0},
            },
            "speech_bubble": {
                "source": "explicit.profile.floating_prop",
                "point": {"x": 80.0, "y": 24.0},
            },
            "palm": {
                "source": "explicit.profile.hand_saint",
                "point": {"x": 80.0, "y": 78.0},
            },
        },
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.hover": {"animation": "hover", "events": []},
            "action.ranged.primary": {
                "animation": "shoot",
                "events": [
                    {
                        "t": 0.5,
                        "event": "projectile_release",
                        "source": "explicit.profile.floating_prop",
                    }
                ],
            },
            "action.special.bless": {
                "animation": "bless",
                "events": [
                    {
                        "t": 0.45,
                        "event": "blessing_emit",
                        "source": "explicit.profile.hand_saint",
                    }
                ],
            },
        },
    },
    "puppy_slug_variant2": {
        "actor": {
            "character_id": "npc_puppy_slug_variant2",
            "display_name": "Puppy Slug Variant 2",
        },
        "body": {
            "body_plan": "Crawler",
            "body_kind": "LowProfile",
            "mass_class": "Light",
            "traits": ["ai_era", "enemy", "crawler", "no_hands"],
            "locomotion_hint": "Slither",
        },
        "capabilities": {
            "traversal": {
                "walk": True,
                "jump": None,
                "climb": None,
                "fly": None,
                "swim": None,
                "crawl": True,
                "use_lifts": None,
                "door_access": [],
            },
            "interactions": {
                "talk": None,
                "trade": None,
                "carry": None,
                "open_doors": [],
            },
        },
        "brain": {"default_preset": "wanderer_puppy_slug"},
        "actions": {"default_preset": "zombie_bite"},
        "visual": {"default_pose": "idle"},
        "tags": ["ai_era", "enemy", "crawler", "no_hands"],
        "sockets": {
            "mouth": {
                "source": "explicit.profile.ai_era",
                "point": {"x": 104.0, "y": 74.0},
            },
            "center": {
                "source": "explicit.profile.ai_era",
                "point": {"x": 80.0, "y": 80.0},
            },
        },
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.crawl": {"animation": "crawl", "events": []},
            "action.melee.primary": {
                "animation": "lunge",
                "events": [
                    {
                        "t": 0.35,
                        "event": "hitbox_active_start",
                        "source": "explicit.profile.ai_era",
                    },
                    {
                        "t": 0.55,
                        "event": "hitbox_active_end",
                        "source": "explicit.profile.ai_era",
                    },
                ],
            },
        },
    },
}

for _target_name, _actor_metadata in LOCAL_ACTOR_METADATA_BY_TARGET.items():
    if _target_name in TARGETS:
        TARGETS[_target_name].setdefault("actor_metadata", _actor_metadata)
