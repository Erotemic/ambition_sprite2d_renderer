"""Custom sprite-sheet generators for AI-culture enemy archetypes.

This module intentionally avoids the repo's human / toon rigs. Each target is a
standalone custom creature or animated prop-creature rendered directly with PIL.

Targets provided:
- puppy_slug_variant2   : psychedelic dog-face slug homage to DeepDream era (puppy_slug variant).
- synthetic_friend      : uncanny social-face cocoon / deepfake portrait mimic.
- hand_saint            : floating palm-idol diffusion-hand horror saint.
- spaghetti_event       : unstable noodle-body-horror creature.
- helpful_liar          : friendly kiosk / assistant UI that lies with cheerful certainty.
- ai_slop               : thumbnail-collage sludge beast; the most detailed of the set.
- agent_swarm           : central planner orb coordinating tool-using drones.

The tack-on registry discovers this module automatically because it exposes a
TARGETS dict. Each entry renders a separate spritesheet.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc, shape_rig
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
    "synthetic_friend": [
        ("idle", 6, 125),
        ("drift", 8, 92),
        ("smile", 6, 100),
        ("glitch", 6, 86),
        ("reveal", 6, 90),
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
    "spaghetti_event": [
        ("idle", 6, 126),
        ("slither", 8, 92),
        ("gulp", 6, 90),
        ("lash", 6, 84),
        ("unravel", 6, 90),
        ("hurt", 4, 90),
        ("death", 8, 112),
    ],
    "helpful_liar": [
        ("idle", 6, 126),
        ("roll", 8, 92),
        ("point", 6, 90),
        ("confirm", 6, 86),
        ("misdirect", 6, 90),
        ("hurt", 4, 90),
        ("death", 8, 112),
    ],
    "ai_slop": [
        ("idle", 6, 126),
        ("shamble", 8, 90),
        ("trend", 6, 86),
        ("replicate", 6, 84),
        ("adblast", 6, 88),
        ("hurt", 4, 90),
        ("death", 8, 112),
    ],
    "agent_swarm": [
        ("idle", 6, 126),
        ("orbit", 8, 90),
        ("scan", 6, 88),
        ("deploy", 6, 84),
        ("converge", 6, 90),
        ("hurt", 4, 90),
        ("death", 8, 112),
    ],
}

FRAME_SIZE = (320, 320)
WORK_FRAME_SIZE = (640, 640)  # logical canvas is 160×160 at SUPER=4.
SUPER = 4
OUTLINE = (28, 22, 28, 255)
SMOKE = (180, 184, 214, 92)
GLOW = (255, 244, 184, 118)
WHITE = (250, 250, 250, 255)
BLACK = (28, 24, 28, 255)
YELLOW = (246, 222, 108, 255)
RED = (220, 92, 108, 255)
CYAN = (106, 222, 242, 255)
MAGENTA = (244, 114, 214, 255)
GREEN = (140, 236, 136, 255)


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(p: Point) -> Tuple[int, int]:
    return (_s(p[0]), _s(p[1]))


def _box(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _rot(x: float, y: float, deg: float) -> Point:
    rad = math.radians(deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return (x * c - y * s, x * s + y * c)


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


def _rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[float, float, float, float],
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
    radius: float = 4.0,
) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(
        (_s(x1), _s(y1), _s(x2), _s(y2)),
        radius=_s(radius),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)) if outline is not None else 0,
    )


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


def _triangle(
    draw: ImageDraw.ImageDraw,
    center: Point,
    size: float,
    fill: RGBA,
    deg: float = 0.0,
    outline: RGBA = OUTLINE,
) -> None:
    pts: List[Point] = []
    for i in range(3):
        ang = math.radians(-90 + i * 120 + deg)
        pts.append((center[0] + math.cos(ang) * size, center[1] + math.sin(ang) * size))
    _poly(draw, pts, fill, outline, 0.9)


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
        if part is None:
            return
        px, py = self.pivot
        dx, dy = at[0] - px, at[1] - py
        c, s = math.cos(math.radians(self.degrees)), math.sin(math.radians(self.degrees))
        x, y = px + dx * c - dy * s, py + dx * s + dy * c
        shape_rig.place(img, part, (x * SUPER, y * SUPER), self.degrees + degrees, name)


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
# Synthetic friend (uncanny deepfake cocoon)


def _pose_synth(anim: str, frame_idx: int, nframes: int) -> Dict[str, float]:
    t = 0.0 if nframes <= 1 else frame_idx / float(max(1, nframes - 1))
    cyc = math.tau * frame_idx / max(1, nframes)
    s = math.sin(cyc)
    pose = {
        "x": 0.0,
        "y": 0.0,
        "tilt": 0.0,
        "glitch": 0.0,
        "smile": 0.0,
        "reveal": 0.0,
        "hurt": 0.0,
        "dead": 0.0,
    }
    if anim == "idle":
        pose["y"] = s * 1.2
        pose["tilt"] = s * 1.5
    elif anim == "drift":
        pose["x"] = s * 3.0
        pose["y"] = math.sin(cyc * 1.3) * 2.4
        pose["tilt"] = s * 3.0
    elif anim == "smile":
        tt = _ease(t)
        pose["smile"] = math.sin(tt * math.pi)
        pose["tilt"] = _lerp(-2.0, 2.0, tt)
    elif anim == "glitch":
        pose["x"] = (1 if frame_idx % 2 == 0 else -1) * 2.0
        pose["glitch"] = 1.0
        pose["tilt"] = s * 5.0
    elif anim == "reveal":
        tt = _ease(t)
        pose["reveal"] = math.sin(tt * math.pi)
        pose["tilt"] = -4.0 + tt * 8.0
    elif anim == "hurt":
        hit = math.sin(t * math.pi)
        pose["hurt"] = hit
        pose["x"] = (1 if frame_idx % 2 == 0 else -1) * 2.5
    elif anim == "death":
        tt = _ease(t)
        pose["dead"] = tt
        pose["tilt"] = tt * 28.0
        pose["y"] = tt * 9.0
    return pose


def _paint_synth_back_card(d, cx: float, cy: float) -> None:
    """One back portrait card, level, centred on ``(cx, cy)``."""
    _rounded_rect(d, (cx - 20, cy - 30, cx + 17, cy + 32), (228, 236, 246, 255), (190, 200, 216, 255), 1.0, 5.0)
    _ellipse(d, cx - 1, cy - 6, 10, 12, (240, 212, 190, 255), OUTLINE, 0.7)
    _emotion_eye(d, cx - 4, cy - 8, 2.4, 3.0, CYAN, 0.0, blink=0.0)
    _emotion_eye(d, cx + 3, cy - 8, 2.4, 3.0, GREEN, 0.2, blink=0.0)
    _line(d, [(cx - 5, cy + 2), (cx + 5, cy + 3)], (160, 104, 110, 255), 0.9)


def _paint_synth_main_card(d, cx: float, cy: float, blink: float, glitch: float, mouth_curve: float) -> None:
    """The main face-card, level, centred on ``(cx, cy)``."""
    _rounded_rect(d, (cx - 22, cy - 33, cx + 22, cy + 37), (244, 246, 252, 255), (208, 214, 226, 255), 1.0, 6.0)
    _ellipse(d, cx, cy - 8, 13, 16, (238, 210, 188, 255), OUTLINE, 0.7)
    _ellipse(d, cx - 4.5, cy - 11.0, 3.0, 2.0, (236, 192, 206, 130), None, 0)
    _ellipse(d, cx + 4.8, cy - 8.0, 2.2, 3.6, (236, 192, 206, 130), None, 0)
    _emotion_eye(d, cx - 4.0, cy - 12.0, 2.8, 3.5, CYAN, pupil_shift=glitch * 1.6, blink=blink)
    _emotion_eye(d, cx + 4.2, cy - 11.4, 2.1, 4.1, GREEN, pupil_shift=-glitch * 1.0, blink=0.0)
    _line(d, [(cx - 2.0, cy - 5.0), (cx + 2.0, cy - 3.0)], (190, 142, 126, 255), 0.8)
    _line(
        d,
        [(cx - 5.0, cy + 3.0), (cx, cy + 4.5 + mouth_curve * 0.4), (cx + 5.5, cy + 3.0 + mouth_curve)],
        (146, 92, 104, 255),
        0.8,
    )
    # Mismatched earring + second ear.
    _circle(d, (cx - 13.0, cy - 8.0), 1.6, (238, 210, 188, 255), OUTLINE, 0.6)
    _circle(d, (cx + 13.2, cy - 8.5), 1.9, (238, 210, 188, 255), OUTLINE, 0.6)
    _circle(d, (cx + 14.2, cy - 2.5), 1.1, YELLOW, OUTLINE, 0.5)
    _triangle(d, (cx + 14.8, cy + 2.0), 1.6, MAGENTA, 180)
    # Shoulder/bust drape.
    _poly(
        d,
        [(cx - 18, cy + 14), (cx - 8, cy + 5), (cx + 5, cy + 7), (cx + 18, cy + 18), (cx + 16, cy + 31), (cx - 14, cy + 30)],
        (164, 188, 224, 255),
        OUTLINE,
        0.8,
    )


def _paint_synth_ghost(d, gx: float, gy: float) -> None:
    """The ghost second face peeking in reveal/glitch."""
    _ellipse(d, gx, gy, 8, 9, (246, 224, 206, 170), (188, 146, 156, 180), 0.6)
    _emotion_eye(d, gx - 2.0, gy - 1.0, 1.5, 2.1, MAGENTA, blink=0.0)
    _emotion_eye(d, gx + 2.0, gy - 0.6, 1.5, 2.1, CYAN, blink=0.0)
    _line(d, [(gx - 2, gy + 4), (gx + 2, gy + 5)], (140, 88, 94, 180), 0.7)


def _render_synthetic_friend(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose_synth(anim, frame_idx, nframes)
    img, _draw = _new_frame()
    hx, hy = HOME
    cx = 82 + pose["x"]
    cy = 82 + pose["y"]

    # Halo ring / beauty light.
    def halo(d) -> None:
        _ellipse(d, hx, hy, 28, 34, (236, 240, 252, 120), (186, 212, 252, 180), 1.2)
        _ellipse(d, hx, hy, 23, 29, (10, 18, 24, 0), (210, 226, 248, 110), 1.2)

    WORLD.put(img, ("synth_halo",), halo, (cx, cy - 2), "halo")
    # Back portrait cards: one piece, turned by each card's tilt.
    for k, (ox, oy, tilt) in enumerate([(-8, -2, -8), (7, 3, 10)]):
        WORLD.put(
            img,
            ("synth_back_card",),
            lambda d: _paint_synth_back_card(d, hx, hy),
            (cx + ox, cy + oy),
            f"back_card_{k}",
            -(tilt + pose["tilt"] * 0.4),
        )
    # Main face-card: its pieces ride the card's turn.
    card = _Frame((cx, cy), -pose["tilt"])
    blink = 0.94 if pose["glitch"] and frame_idx % 2 else 0.0
    glitch = pose["glitch"]
    mouth_curve = round(0.0 + pose["smile"] * 4.2 - pose["hurt"] * 2.5, 3)
    card.put(
        img,
        ("synth_main", blink, glitch, mouth_curve),
        lambda d: _paint_synth_main_card(d, hx, hy, blink, glitch, mouth_curve),
        (cx, cy),
        "main_card",
    )
    if pose["reveal"] > 0.0 or pose["glitch"] > 0.0:
        card.put(img, ("synth_ghost",), lambda d: _paint_synth_ghost(d, hx, hy), (cx + 12 + pose["reveal"] * 8.0, cy + 4), "ghost")
    if pose["glitch"]:
        def bars(d) -> None:
            for ox, col in [(-6, CYAN), (7, MAGENTA)]:
                _rounded_rect(d, (hx - 18 + ox, hy + 20, hx + 8 + ox, hy + 25), (col[0], col[1], col[2], 120), None, 0, 1.4)

        card.put(img, ("synth_bars",), bars, (cx, cy), "glitch_bars")
    # Loose floating accessories.
    for i, (ox, oy) in enumerate([(-22, -18), (25, -12), (-24, 10), (20, 16)]):
        r = 1.5 + (i % 2) * 0.4
        WORLD.put(
            img,
            ("synth_bead", r),
            lambda d, r=r: _circle(d, (hx, hy), r, (255, 255, 255, 150), None, 0),
            (cx + ox, cy + oy + math.sin(frame_idx * 0.7 + i) * 1.2),
            f"bead_{i}",
        )
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
# Spaghetti event


def _pose_spaghetti(anim: str, frame_idx: int, nframes: int) -> Dict[str, float]:
    t = 0.0 if nframes <= 1 else frame_idx / float(max(1, nframes - 1))
    cyc = math.tau * frame_idx / max(1, nframes)
    s = math.sin(cyc)
    pose = {
        "x": 0.0,
        "bob": 0.0,
        "noodle": s,
        "mouth": 0.0,
        "lash": 0.0,
        "unravel": 0.0,
        "hurt": 0.0,
        "dead": 0.0,
    }
    if anim == "idle":
        pose["bob"] = s * 1.0
    elif anim == "slither":
        pose["x"] = s * 2.5
        pose["bob"] = abs(s) * 2.0 - 0.4
    elif anim == "gulp":
        tt = _ease(t)
        pose["mouth"] = math.sin(tt * math.pi)
    elif anim == "lash":
        tt = _ease(t)
        pose["lash"] = math.sin(tt * math.pi)
        pose["x"] = _lerp(-3.0, 5.0, tt)
    elif anim == "unravel":
        tt = _ease(t)
        pose["unravel"] = math.sin(tt * math.pi)
        pose["mouth"] = 0.2
    elif anim == "hurt":
        hit = math.sin(t * math.pi)
        pose["hurt"] = hit
        pose["x"] = (1 if frame_idx % 2 == 0 else -1) * 2.0
    elif anim == "death":
        tt = _ease(t)
        pose["dead"] = tt
        pose["bob"] = tt * 7.0
        pose["unravel"] = tt
    return pose


_NOODLE = (238, 222, 184, 255)
_NOODLE_HI = (250, 238, 210, 255)
_NOODLE_LO = (190, 166, 122, 255)
_SAUCE = (188, 96, 66, 220)


def _paint_spaghetti_body(d, cx: float, cy: float, unravel: float) -> None:
    """The noodle mound and its hanging strands (the top strand lifts with
    ``unravel``)."""
    body_paths = [
        _bezier((cx - 28, cy + 8), (cx - 14, cy - 22 - unravel * 10), (cx + 12, cy - 24), (cx + 28, cy + 2), 18),
        _bezier((cx - 24, cy + 16), (cx - 10, cy - 8), (cx + 10, cy - 6), (cx + 24, cy + 12), 14),
        _bezier((cx - 30, cy + 24), (cx - 6, cy + 8), (cx + 10, cy + 14), (cx + 30, cy + 20), 14),
    ]
    for idx, pts in enumerate(body_paths):
        _ribbon(d, pts, 8.5 - idx * 0.8, _NOODLE, OUTLINE, _NOODLE_HI)
    for i in range(6):
        off = -24 + i * 10
        pts = _bezier(
            (cx + off, cy + 8 + abs(off) * 0.05),
            (cx + off * 0.4, cy - 8 - abs(off) * 0.12),
            (cx + off * 0.2, cy + 22),
            (cx + off * 0.8, cy + 28 + math.sin(i) * 2.0),
            10,
        )
        _ribbon(d, pts, 2.6, _NOODLE, OUTLINE, _NOODLE_HI)


def _paint_meatball_eye(d, cx: float, cy: float, iris: RGBA, dead: float) -> None:
    _ellipse(d, cx, cy, 8.0, 7.5, (132, 88, 62, 255), OUTLINE, 0.8)
    _ellipse(d, cx - 1.0, cy - 1.0, 4.2, 3.0, (164, 114, 84, 255), None, 0)
    _emotion_eye(d, cx, cy - 0.2, 2.0, 2.6, iris, blink=dead * 0.9)


def _paint_spaghetti_mouth(d, cx: float, cy: float, mouth_open: float) -> None:
    _ellipse(d, cx + 2, cy + 10, 10, 4.0 + mouth_open, (84, 44, 44, 255), OUTLINE, 0.7)
    for i in range(5):
        tooth_x = cx - 6 + i * 4.0
        _triangle(d, (tooth_x, cy + 8 - (i % 2) * 0.6), 1.2, WHITE, 180)
        _triangle(d, (tooth_x + 0.6, cy + 12 + mouth_open * 0.45 + (i % 2) * 0.5), 1.0, WHITE, 0)


def _paint_fork_arm(d, cx: float, cy: float, side: int, lash: float) -> None:
    arm = _bezier(
        (cx + side * 18, cy + 10),
        (cx + side * 28, cy + 6 - lash * 6),
        (cx + side * 34, cy - 8 + side * lash * 3),
        (cx + side * (42 + lash * 16), cy - 4 - lash * 10),
        12,
    )
    _ribbon(d, arm, 3.6, _NOODLE_LO, OUTLINE, _NOODLE_HI)
    base = arm[-1]
    for prong in (-4, 0, 4):
        _line(d, [base, (base[0] + side * 4, base[1] - 7 + prong * 0.4)], (196, 210, 230, 255), 1.2)


def _paint_sauce(d, cx: float, cy: float) -> None:
    for xoff in (-14, -2, 9):
        drip_y = cy + 2 + (xoff % 3) * 2
        _ribbon(d, [(cx + xoff, cy - 12), (cx + xoff + math.sin(xoff) * 1.0, drip_y)], 1.9, _SAUCE, (126, 62, 42, 220))


def _render_spaghetti(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose_spaghetti(anim, frame_idx, nframes)
    img, _draw = _new_frame()
    hx, hy = HOME
    cx = 80 + pose["x"]
    cy = 100 + pose["bob"] + pose["dead"] * 6
    unravel = round(pose["unravel"], 3)
    WORLD.put(img, ("spaghetti_body", unravel), lambda d: _paint_spaghetti_body(d, hx, hy, unravel), (cx, cy), "body")
    # Meatball eyes.
    dead = round(pose["dead"], 3)
    for off in (-10, 12):
        iris = CYAN if off < 0 else MAGENTA
        WORLD.put(
            img,
            ("spaghetti_eye", iris, dead),
            lambda d, iris=iris: _paint_meatball_eye(d, hx, hy, iris, dead),
            (cx + off, cy - 4),
            f"eye_{'left' if off < 0 else 'right'}",
        )
    mouth_open = round(pose["mouth"] * 8.0 + pose["unravel"] * 5.0, 3)
    WORLD.put(img, ("spaghetti_mouth", mouth_open), lambda d: _paint_spaghetti_mouth(d, hx, hy, mouth_open), (cx, cy), "mouth")
    # Fork appendages: one piece per lash.
    lash = round(pose["lash"], 3)
    for side in (-1, 1):
        WORLD.put(
            img,
            ("spaghetti_fork", side, lash),
            lambda d, side=side: _paint_fork_arm(d, hx, hy, side, lash),
            (cx, cy),
            f"fork_{'left' if side < 0 else 'right'}",
        )
    WORLD.put(img, ("spaghetti_sauce",), lambda d: _paint_sauce(d, hx, hy), (cx, cy), "sauce")
    if pose["hurt"]:
        hurt = round(pose["hurt"], 3)
        WORLD.put(
            img,
            ("spaghetti_hurt", hurt),
            lambda d: _alpha_ellipse(d._image, hx, hy, 30, 18, (255, 92, 108, int(75 * hurt))),
            (cx, cy + 6),
            "hurt",
        )
    return _downsample(img)


# ---------------------------------------------------------------------------
# Helpful liar


def _pose_liar(anim: str, frame_idx: int, nframes: int) -> Dict[str, float]:
    t = 0.0 if nframes <= 1 else frame_idx / float(max(1, nframes - 1))
    cyc = math.tau * frame_idx / max(1, nframes)
    s = math.sin(cyc)
    pose = {
        "x": 0.0,
        "bob": 0.0,
        "tilt": 0.0,
        "arm": 0.0,
        "confirm": 0.0,
        "misdirect": 0.0,
        "hurt": 0.0,
        "dead": 0.0,
    }
    if anim == "idle":
        pose["bob"] = s * 1.2
        pose["tilt"] = s * 1.2
    elif anim == "roll":
        pose["x"] = s * 2.2
        pose["bob"] = abs(s) * 1.8 - 0.2
        pose["arm"] = s * 12.0
    elif anim == "point":
        tt = _ease(t)
        pose["arm"] = _lerp(-6.0, 28.0, tt)
        pose["tilt"] = -4.0 + tt * 8.0
    elif anim == "confirm":
        tt = _ease(t)
        pose["confirm"] = math.sin(tt * math.pi)
        pose["tilt"] = tt * 3.0
    elif anim == "misdirect":
        tt = _ease(t)
        pose["misdirect"] = math.sin(tt * math.pi)
        pose["arm"] = 18.0 * pose["misdirect"]
    elif anim == "hurt":
        hit = math.sin(t * math.pi)
        pose["hurt"] = hit
        pose["x"] = (1 if frame_idx % 2 == 0 else -1) * 2.0
    elif anim == "death":
        tt = _ease(t)
        pose["dead"] = tt
        pose["tilt"] = tt * 34.0
        pose["bob"] = tt * 10.0
    return pose


def _paint_liar_body(d, cx: float, cy: float, dead: float) -> None:
    """Stand, screen, speech-bubble face, badges and cursor arms."""
    _capsule(d, (cx, cy + 28), (cx, cy + 48), 5.0, (168, 176, 198, 255), OUTLINE, None)
    _capsule(d, (cx - 12, cy + 50), (cx + 12, cy + 50), 4.0, (150, 160, 184, 255), OUTLINE, None)
    for side in (-1, 1):
        _circle(d, (cx + side * 9.5, cy + 54), 4.2, (104, 114, 132, 255), OUTLINE, 0.8)
        _circle(d, (cx + side * 9.5, cy + 54), 1.5, (210, 218, 232, 255), None, 0)
    # Main screen.
    _rounded_rect(d, (cx - 24, cy - 22, cx + 24, cy + 18), (194, 230, 240, 255), (118, 138, 164, 255), 1.0, 5.0)
    _rounded_rect(d, (cx - 19, cy - 17, cx + 19, cy + 13), (74, 128, 164, 255), (64, 92, 120, 255), 0.9, 4.0)
    # Face speech bubble.
    bubble = [
        (cx - 14, cy - 9),
        (cx + 11, cy - 9),
        (cx + 11, cy + 4),
        (cx + 3, cy + 4),
        (cx - 1, cy + 9),
        (cx - 2, cy + 4),
        (cx - 14, cy + 4),
    ]
    _poly(d, bubble, (232, 244, 250, 255), (200, 214, 228, 255), 0.7)
    _emotion_eye(d, cx - 7, cy - 3, 2.1, 2.7, GREEN, blink=dead * 0.9)
    _emotion_eye(d, cx + 2.5, cy - 3.2, 2.1, 2.7, CYAN, blink=dead * 0.9)
    _line(d, [(cx - 8, cy + 2), (cx - 2, cy + 4), (cx + 5, cy + 2)], (80, 116, 124, 255), 0.8)
    # UI badges.
    _circle(d, (cx + 18, cy - 15), 3.0, GREEN, OUTLINE, 0.6)
    _line(d, [(cx + 16.5, cy - 15), (cx + 18, cy - 13.2), (cx + 20.5, cy - 17.3)], WHITE, 0.8)
    _circle(d, (cx - 18, cy - 14), 3.0, CYAN, OUTLINE, 0.6)
    _line(d, [(cx - 19.6, cy - 14), (cx - 16.6, cy - 14)], WHITE, 0.8)
    _line(d, [(cx - 18.1, cy - 15.5), (cx - 18.1, cy - 12.3)], WHITE, 0.8)
    # Arms / cursors.
    left_wrist = (cx - 24, cy + 0)
    right_wrist = (cx + 24, cy - 2)
    _capsule(d, (cx - 20, cy - 2), (left_wrist[0] - 8, left_wrist[1] + 6), 3.2, (214, 224, 236, 255), OUTLINE, None)
    _capsule(d, (cx + 20, cy + 0), (right_wrist[0] + 8, right_wrist[1] + 4), 3.2, (214, 224, 236, 255), OUTLINE, None)
    _triangle(d, (left_wrist[0] - 10, left_wrist[1] + 6), 5.0, WHITE, -20)
    _triangle(d, (right_wrist[0] + 10, right_wrist[1] + 4), 5.0, WHITE, 160)


def _render_helpful_liar(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose_liar(anim, frame_idx, nframes)
    img, _draw = _new_frame()
    hx, hy = HOME
    cx = 80 + pose["x"]
    cy = 88 + pose["bob"]
    body = _Frame((cx, cy + 12), -pose["tilt"])
    dead = round(pose["dead"], 3)
    body.put(img, ("liar_body", dead), lambda d: _paint_liar_body(d, hx, hy, dead), (cx, cy), "body")
    if pose["confirm"] > 0:
        def confirm(d) -> None:
            _rounded_rect(d, (hx - 16, hy - 34, hx + 16, hy - 24), (236, 246, 252, 220), (182, 198, 216, 255), 0.8, 2.0)
            _line(d, [(hx - 12, hy - 29), (hx - 8, hy - 25), (hx - 2, hy - 31)], GREEN, 1.0)
            _line(d, [(hx + 1, hy - 29), (hx + 10, hy - 29)], (120, 160, 176, 255), 0.9)

        body.put(img, ("liar_confirm",), confirm, (cx, cy), "confirm")
    if pose["misdirect"] > 0:
        misdirect = round(pose["misdirect"], 3)

        def arrow(d) -> None:
            arrow_c = (hx + 20 + misdirect * 10, hy - 28)
            _ribbon(d, [(hx + 2, hy - 18), (arrow_c[0] - 6, arrow_c[1]), arrow_c], 2.3, MAGENTA, OUTLINE)
            _triangle(d, arrow_c, 4.0, MAGENTA, 90)

        body.put(img, ("liar_arrow", misdirect), arrow, (cx, cy), "arrow")
    if pose["hurt"] > 0:
        hurt = round(pose["hurt"], 3)
        body.put(
            img,
            ("liar_hurt", hurt),
            lambda d: _alpha_ellipse(d._image, hx, hy, 30, 26, (255, 96, 110, int(70 * hurt))),
            (cx, cy - 2),
            "hurt",
        )
    return _downsample(img)


# ---------------------------------------------------------------------------
# AI slop — the most detailed sheet in the set.


def _pose_slop(anim: str, frame_idx: int, nframes: int) -> Dict[str, float]:
    t = 0.0 if nframes <= 1 else frame_idx / float(max(1, nframes - 1))
    cyc = math.tau * frame_idx / max(1, nframes)
    s = math.sin(cyc)
    pose = {
        "x": 0.0,
        "bob": 0.0,
        "tilt": 0.0,
        "burst": 0.0,
        "rep": 0.0,
        "ad": 0.0,
        "arm": s,
        "hurt": 0.0,
        "dead": 0.0,
    }
    if anim == "idle":
        pose["bob"] = s * 1.2
        pose["tilt"] = s * 1.0
    elif anim == "shamble":
        pose["x"] = s * 3.2
        pose["bob"] = abs(s) * 2.0 - 0.3
        pose["tilt"] = s * 3.0
        pose["arm"] = s * 1.4
    elif anim == "trend":
        tt = _ease(t)
        pose["burst"] = math.sin(tt * math.pi)
        pose["tilt"] = _lerp(-5.0, 4.0, tt)
    elif anim == "replicate":
        tt = _ease(t)
        pose["rep"] = math.sin(tt * math.pi)
        pose["tilt"] = tt * 2.0
    elif anim == "adblast":
        tt = _ease(t)
        pose["ad"] = math.sin(tt * math.pi)
        pose["burst"] = pose["ad"]
        pose["tilt"] = -3.0 + pose["ad"] * 4.0
    elif anim == "hurt":
        hit = math.sin(t * math.pi)
        pose["hurt"] = hit
        pose["x"] = (1 if frame_idx % 2 == 0 else -1) * 2.0
        pose["tilt"] = (1 if frame_idx % 2 == 0 else -1) * 3.0
    elif anim == "death":
        tt = _ease(t)
        pose["dead"] = tt
        pose["tilt"] = tt * 40.0
        pose["bob"] = tt * 11.0
        pose["rep"] = tt
    return pose


def _draw_card(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    w: float,
    h: float,
    tilt: float,
    base: RGBA,
    accent: RGBA,
    *,
    bad_face: bool = False,
    pseudo_text: bool = True,
    play: bool = False,
) -> None:
    layer = Image.new("RGBA", draw._image.size, (0, 0, 0, 0))
    ld = blending_draw(layer)
    _rounded_rect(ld, (x, y, x + w, y + h), base, (210, 214, 226, 230), 0.8, 3.0)
    header_h = max(3.5, h * 0.18)
    media_y = y + header_h + 3
    media_h = max(5.0, h - header_h - 7)
    media_y2 = media_y + media_h
    # headline strip
    _rounded_rect(
        ld,
        (x + 2, y + 2, x + w - 2, y + 2 + header_h),
        (248, 250, 252, 230),
        None,
        0,
        1.6,
    )
    for i in range(2):
        line_y = y + 3.3 + i * 2.2
        _rounded_rect(
            ld,
            (x + 4, line_y, x + w - 4 - i * 2, line_y + 1.1),
            (232, 236, 244, 170),
            None,
            0,
            0.6,
        )
    if play:
        _rounded_rect(ld, (x + 3, media_y, x + w - 3, media_y2), accent, None, 0, 1.8)
        _triangle(
            ld, (x + w * 0.54, media_y + media_h * 0.54), min(w, h) * 0.15, WHITE, 90
        )
    elif bad_face:
        _rounded_rect(ld, (x + 3, media_y, x + w - 3, media_y2), accent, None, 0, 1.8)
        # uncanny face.
        _ellipse(
            ld,
            x + w * 0.52,
            media_y + media_h * 0.55,
            max(2.5, w * 0.18),
            max(2.5, media_h * 0.22),
            (246, 220, 200, 255),
            OUTLINE,
            0.5,
        )
        _emotion_eye(ld, x + w * 0.45, media_y + media_h * 0.50, 1.5, 2.0, CYAN)
        _emotion_eye(ld, x + w * 0.56, media_y + media_h * 0.48, 1.2, 2.4, MAGENTA)
        _line(
            ld,
            [
                (x + w * 0.44, media_y + media_h * 0.64),
                (x + w * 0.58, media_y + media_h * 0.66),
            ],
            RED,
            0.6,
        )
        _circle(ld, (x + w * 0.68, media_y + media_h * 0.68), 0.8, YELLOW, OUTLINE, 0.4)
    else:
        _rounded_rect(ld, (x + 3, media_y, x + w - 3, media_y2), accent, None, 0, 1.8)
        if pseudo_text:
            for i in range(3):
                ly = media_y + 2.0 + i * 3.0
                if ly + 1.1 <= media_y2 - 1.0:
                    _rounded_rect(
                        ld,
                        (x + 5, ly, x + w - 5 - (i % 2) * 4, ly + 1.1),
                        (250, 250, 252, 165),
                        None,
                        0,
                        0.6,
                    )
    if tilt:
        layer = layer.rotate(tilt, center=_pt((x + w / 2.0, y + h / 2.0)))
    rigdoc.composite_canvas(draw._image, layer)


_SLOP_CARDS = [
    # (dx, dy, w, h, base, accent, bad_face, pseudo_text, play): offsets
    # from the body centre; each card's tilt is the pose's (``_slop_card_tilts``).
    (-28, -20, 18, 22, (242, 244, 248, 255), (118, 146, 214, 255), False, False, True),
    (-4, -30, 24, 18, (246, 246, 250, 255), (238, 158, 184, 255), True, False, False),
    (12, -8, 18, 24, (248, 248, 252, 255), (128, 210, 188, 255), False, True, False),
    (-12, 6, 28, 20, (246, 246, 250, 255), (238, 196, 96, 255), False, True, False),
    (8, 18, 20, 16, (248, 248, 252, 255), (156, 120, 220, 255), True, False, False),
]


def _slop_card_tilts(pose: Dict[str, float]) -> List[float]:
    return [
        -12 + pose["tilt"],
        8 - pose["tilt"],
        16 + pose["burst"] * 8,
        -8 + pose["rep"] * 10,
        14 - pose["tilt"],
    ]


def _paint_slop_body(d, cx: float, cy: float) -> None:
    """Ragged collage body silhouette."""
    blob = [
        (cx - 26, cy - 24),
        (cx - 36, cy - 6),
        (cx - 34, cy + 18),
        (cx - 24, cy + 34),
        (cx - 5, cy + 42),
        (cx + 18, cy + 38),
        (cx + 32, cy + 18),
        (cx + 34, cy - 8),
        (cx + 26, cy - 28),
        (cx + 6, cy - 38),
        (cx - 12, cy - 36),
    ]
    _poly(d, blob, (118, 84, 164, 255), OUTLINE, 1.1)
    _poly(
        d,
        [(cx - 18, cy - 20), (cx - 22, cy + 24), (cx - 4, cy + 30), (cx + 6, cy - 24)],
        (154, 112, 198, 190),
        None,
        0,
    )


def _paint_slop_face(d, cx: float, cy: float, hurt: float) -> None:
    """Main face: skin, mismatched eyes, two dots."""
    _ellipse(d, cx - 2, cy + 4, 15, 11, (242, 210, 188, 210), (200, 146, 148, 220), 0.7)
    _emotion_eye(d, cx - 7, cy - 1, 2.6, 3.2, CYAN, pupil_shift=hurt * 1.2)
    _emotion_eye(d, cx + 1.8, cy - 2.0, 2.0, 4.0, MAGENTA, pupil_shift=-hurt * 1.0)
    _circle(d, (cx + 10.5, cy + 0.5), 1.6, YELLOW, OUTLINE, 0.5)
    _circle(d, (cx + 12.8, cy + 9.0), 1.0, RED, OUTLINE, 0.5)


def _paint_slop_grin(d, cx: float, cy: float, ad: float, burst: float) -> None:
    """The clickbait grin (it opens with ``burst``)."""
    grin_w = 15 + ad * 4.0
    _ellipse(d, cx - 1, cy + 11, grin_w, 5.0 + burst * 3.8, (76, 34, 58, 255), OUTLINE, 0.8)
    for i in range(8):
        tx = cx - 12 + i * 3.5
        _triangle(d, (tx, cy + 8.5), 1.2 + (i % 2) * 0.3, WHITE, 180)
        _triangle(d, (tx + 0.4, cy + 13.5 + burst * 1.8), 1.0 + ((i + 1) % 2) * 0.2, WHITE, 0)


def _paint_slop_drips(d, cx: float, cy: float, burst: float) -> None:
    """Slime drips (they grow with ``burst``)."""
    for off in (-18, -9, 3, 14):
        length = 5 + (off % 3) * 2 + burst * 5.0
        _ribbon(
            d,
            [(cx + off, cy + 18), (cx + off + math.sin(off) * 1.1, cy + 18 + length)],
            1.5,
            (112, 234, 122, 220),
            (72, 146, 86, 220),
        )


def _paint_slop_bars_and_badges(d, cx: float, cy: float) -> None:
    """Glitched subtitle bars and the ad badges."""
    for i in range(5):
        y = cy - 35 + i * 2.8
        _rounded_rect(d, (cx + 16, y, cx + 28 + (i % 2) * 5, y + 1.8), (250, 250, 252, 110), None, 0, 0.8)
    badges = [
        (cx - 30, cy - 30, RED, "!"),
        (cx + 26, cy - 24, YELLOW, "$"),
        (cx - 34, cy + 8, MAGENTA, "+"),
    ]
    for bx, by, col, symbol in badges:
        _circle(d, (bx, by), 4.2, col, OUTLINE, 0.7)
        if symbol == "!":
            _line(d, [(bx, by - 2.0), (bx, by + 1.5)], WHITE, 1.0)
            _circle(d, (bx, by + 3.0), 0.7, WHITE, None, 0)
        elif symbol == "$":
            _line(d, [(bx, by - 2.6), (bx, by + 2.8)], WHITE, 0.9)
            _line(d, [(bx - 1.5, by - 1.1), (bx + 1.6, by - 1.1)], WHITE, 0.8)
            _line(d, [(bx - 1.6, by + 1.4), (bx + 1.2, by + 1.4)], WHITE, 0.8)
        else:
            _line(d, [(bx - 1.6, by), (bx + 1.6, by)], WHITE, 0.8)
            _line(d, [(bx, by - 1.6), (bx, by + 1.6)], WHITE, 0.8)


def _slop_arm_points(cx: float, cy: float, arm: float, side: int) -> List[Point]:
    if side < 0:
        return _bezier(
            (cx - 20, cy + 10),
            (cx - 34, cy + 6 + arm * 2),
            (cx - 44, cy + 18 - arm * 4),
            (cx - 50, cy + 8 - arm * 6),
            12,
        )
    return _bezier(
        (cx + 18, cy + 6),
        (cx + 30, cy - 4),
        (cx + 42, cy + 4 + arm * 5),
        (cx + 50, cy - 8 + arm * 7),
        12,
    )


def _render_ai_slop(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose_slop(anim, frame_idx, nframes)
    img, _draw = _new_frame()
    cx = 80 + pose["x"]
    cy = 92 + pose["bob"]
    hx, hy = HOME
    body = _Frame((cx, cy + 8), -pose["tilt"])
    burst = round(pose["burst"], 3)
    rep = round(pose["rep"], 3)
    arm = round(pose["arm"], 3)

    body.put(img, ("slop_body",), lambda d: _paint_slop_body(d, hx, hy), (cx, cy), "body")

    # Sticky cards / thumbnails mounted to the body: each painted level and
    # turned by its tilt.
    for k, ((dx, dy, w, h, base, accent, bad_face, pseudo_text, play), tilt) in enumerate(zip(_SLOP_CARDS, _slop_card_tilts(pose))):
        body.put(
            img,
            ("slop_card", k),
            lambda d, w=w, h=h, base=base, accent=accent, b=bad_face, t=pseudo_text, pl=play: _draw_card(
                d, hx - w / 2.0, hy - h / 2.0, w, h, 0.0, base, accent, bad_face=b, pseudo_text=t, play=pl
            ),
            (cx + dx + w / 2.0, cy + dy + h / 2.0),
            f"card_{k}",
            -tilt,
        )

    hurt = round(pose["hurt"], 3)
    body.put(img, ("slop_face", hurt), lambda d: _paint_slop_face(d, hx, hy, hurt), (cx, cy), "face")
    ad = round(pose["ad"], 3)
    body.put(img, ("slop_grin", ad, burst), lambda d: _paint_slop_grin(d, hx, hy, ad, burst), (cx, cy), "grin")
    body.put(img, ("slop_drips", burst), lambda d: _paint_slop_drips(d, hx, hy, burst), (cx, cy), "drips")
    body.put(img, ("slop_bars",), lambda d: _paint_slop_bars_and_badges(d, hx, hy), (cx, cy), "bars")

    # Deformed duplicate hands: each arm one piece per bend, each hand one
    # piece per spread, turned to its angle at the arm's end.
    spread = round(12 + pose["rep"] * 8, 3)
    for side, name, hand_ang in ((-1, "left", 180 - pose["arm"] * 10), (1, "right", 0 + pose["arm"] * 10)):
        body.put(
            img,
            ("slop_arm", side, arm),
            lambda d, side=side: _ribbon(d, _slop_arm_points(hx, hy, arm, side), 4.0, (240, 222, 198, 255), OUTLINE, None),
            (cx, cy),
            f"{name}_arm",
        )
    for side, name, hand_ang in ((-1, "left", 180 - pose["arm"] * 10), (1, "right", 0 + pose["arm"] * 10)):
        end = _slop_arm_points(cx, cy, pose["arm"], side)[-1]
        body.put(
            img,
            ("slop_hand", spread),
            lambda d: _draw_hand(d, (hx, hy), 0.0, spread=spread, scale=0.75, palm=(244, 226, 200, 255)),
            end,
            f"{name}_hand",
            hand_ang,
        )
    # Extra wrong thumb.
    body.put(
        img,
        ("slop_thumb", rep),
        lambda d: _capsule(d, (hx, hy), (hx + 8, hy + 8 + rep * 6), 3.0, (244, 226, 200, 220), OUTLINE, None),
        (cx + 40, cy + 12),
        "thumb",
    )
    body.put(
        img,
        ("slop_small_hand",),
        lambda d: _draw_hand(d, (hx, hy), 0.0, spread=6, scale=0.45, palm=(244, 226, 200, 220)),
        (cx + 48, cy + 20 + pose["rep"] * 6),
        "small_hand",
        35,
    )

    # Cursor quills.
    def quills(d) -> None:
        for i in range(4):
            ang = -40 + i * 26 + burst * 4
            px = hx - 6 + math.cos(math.radians(ang)) * 36
            py = hy - 6 + math.sin(math.radians(ang)) * 28
            _triangle(d, (px, py), 4.3 - i * 0.4, WHITE, ang + 140)

    body.put(img, ("slop_quills", burst), quills, (cx, cy), "quills")

    # Replication thumbnails.
    if pose["rep"] > 0.0:
        for i in range(3):
            alpha = int(170 - i * 36)
            body.put(
                img,
                ("slop_rep_card", i),
                lambda d, i=i, alpha=alpha: _draw_card(
                    d, hx - 8, hy - 6, 16, 12, 0.0, (248, 248, 252, alpha), (120, 186, 228, alpha),
                    bad_face=(i % 2 == 0), pseudo_text=True, play=(i == 1),
                ),
                (cx + 22 + i * 8 + 8, cy - 22 - i * 4 + 6),
                f"rep_card_{i}",
                -(8 + i * 6),
            )

    # Trend burst / ad blast overlays.
    if pose["burst"] > 0.0:
        def rays(d) -> None:
            for i in range(5):
                ang = i * 72 + frame_idx * 5
                r1 = 12 + i * 2 + burst * 5
                r2 = r1 + 8 + burst * 5
                p1 = (hx + math.cos(math.radians(ang)) * r1, hy - 4 + math.sin(math.radians(ang)) * r1)
                p2 = (hx + math.cos(math.radians(ang)) * r2, hy - 4 + math.sin(math.radians(ang)) * r2)
                _capsule(d, p1, p2, 1.8, (255, 236, 146, 180), None, None)

        body.put(img, ("slop_rays", burst, frame_idx * 5 % 72), rays, (cx, cy), "rays")
    if pose["ad"] > 0.0:
        def banner(d) -> None:
            _rounded_rect(d, (hx - 22, hy - 46, hx + 22, hy - 36), (255, 244, 196, 210), (226, 180, 84, 240), 0.8, 2.0)
            _line(d, [(hx - 14, hy - 41), (hx - 6, hy - 41)], RED, 0.9)
            _line(d, [(hx - 3, hy - 41), (hx + 14, hy - 41)], (166, 120, 74, 255), 0.9)
            _triangle(d, (hx + 17, hy - 41), 2.2, RED, 90)

        body.put(img, ("slop_banner",), banner, (cx, cy), "banner")

    if pose["hurt"] > 0.0:
        body.put(
            img,
            ("slop_hurt", hurt),
            lambda d: _alpha_ellipse(d._image, hx, hy + 2, 20, 16, (255, 92, 110, int(62 * hurt))),
            (cx, cy),
            "hurt",
        )
    return _downsample(img)


# ---------------------------------------------------------------------------
# Agent swarm


def _pose_agent(anim: str, frame_idx: int, nframes: int) -> Dict[str, float]:
    t = 0.0 if nframes <= 1 else frame_idx / float(max(1, nframes - 1))
    cyc = math.tau * frame_idx / max(1, nframes)
    s = math.sin(cyc)
    pose = {
        "bob": 0.0,
        "orbit": frame_idx * (360.0 / max(1, nframes)),
        "scan": 0.0,
        "deploy": 0.0,
        "converge": 0.0,
        "hurt": 0.0,
        "dead": 0.0,
    }
    if anim == "idle":
        pose["bob"] = s * 1.2
    elif anim == "orbit":
        pose["bob"] = math.sin(cyc * 1.1) * 2.0
        pose["orbit"] = frame_idx * 45.0
    elif anim == "scan":
        tt = _ease(t)
        pose["scan"] = math.sin(tt * math.pi)
        pose["orbit"] = tt * 30.0
    elif anim == "deploy":
        tt = _ease(t)
        pose["deploy"] = math.sin(tt * math.pi)
        pose["orbit"] = tt * 24.0
    elif anim == "converge":
        tt = _ease(t)
        pose["converge"] = math.sin(tt * math.pi)
        pose["orbit"] = tt * 18.0
    elif anim == "hurt":
        hit = math.sin(t * math.pi)
        pose["hurt"] = hit
    elif anim == "death":
        tt = _ease(t)
        pose["dead"] = tt
        pose["bob"] = tt * 8.0
        pose["orbit"] = tt * 54.0
    return pose


_AGENT_DRONES = [
    (0, 26, "lens"),
    (72, 24, "grip"),
    (144, 25, "scan"),
    (216, 24, "bolt"),
    (288, 25, "msg"),
]


def _paint_agent_orb(d, cx: float, cy: float, pupil_shift: float, dead: float) -> None:
    """The central planner orb."""
    _ellipse(d, cx, cy, 17, 20, (96, 122, 182, 255), OUTLINE, 0.9)
    _ellipse(d, cx - 3, cy - 4, 10, 12, (126, 154, 218, 255), None, 0)
    _ellipse(d, cx, cy + 1, 8, 10, (222, 236, 250, 255), OUTLINE, 0.7)
    _emotion_eye(d, cx, cy + 1, 4.4, 5.4, CYAN, pupil_shift=pupil_shift, blink=dead * 0.9)
    _line(d, [(cx - 4, cy + 13), (cx + 4, cy + 13)], (180, 206, 240, 255), 0.8)


def _paint_agent_drone(d, dx: float, dy: float, kind: str) -> None:
    """One satellite drone, centred on ``(dx, dy)``."""
    _circle(d, (dx, dy), 6.0, (180, 196, 236, 255), OUTLINE, 0.8)
    _circle(d, (dx - 1.0, dy - 1.0), 3.2, (236, 242, 248, 255), None, 0)
    if kind == "lens":
        _emotion_eye(d, dx, dy, 2.2, 2.8, GREEN)
    elif kind == "grip":
        _capsule(d, (dx - 2.0, dy + 2.0), (dx - 6.0, dy + 8.0), 1.5, (120, 136, 170, 255), OUTLINE, None)
        _capsule(d, (dx + 2.0, dy + 2.0), (dx + 6.0, dy + 8.0), 1.5, (120, 136, 170, 255), OUTLINE, None)
    elif kind == "scan":
        for i in range(3):
            _line(d, [(dx - 6, dy + 4 + i * 2), (dx + 6, dy + 4 + i * 2)], CYAN, 0.6)
    elif kind == "bolt":
        _triangle(d, (dx, dy + 1), 3.3, YELLOW, 180)
    else:
        bubble = [
            (dx - 5, dy - 2),
            (dx + 3, dy - 2),
            (dx + 3, dy + 3),
            (dx, dy + 3),
            (dx - 2, dy + 6),
            (dx - 2, dy + 3),
            (dx - 5, dy + 3),
        ]
        _poly(d, bubble, WHITE, (170, 180, 204, 255), 0.6)


def _render_agent_swarm(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose_agent(anim, frame_idx, nframes)
    img, _draw = _new_frame()
    hx, hy = HOME
    cx = 80
    cy = 86 + pose["bob"]
    pupil = round((pose["scan"] - pose["hurt"]) * 2.0, 3)
    dead = round(pose["dead"], 3)
    WORLD.put(img, ("agent_orb", pupil, dead), lambda d: _paint_agent_orb(d, hx, hy, pupil, dead), (cx, cy), "orb")
    # Satellite drones: a tether (one piece per length, turned) and the drone.
    for base_ang, rad, kind in _AGENT_DRONES:
        ang = base_ang + pose["orbit"]
        rr = rad - pose["converge"] * 8.0
        dx = cx + math.cos(math.radians(ang)) * rr
        dy = cy + math.sin(math.radians(ang)) * (rr * 0.58) - 8
        _stroke_piece(
            img,
            WORLD,
            (cx, cy),
            (dx, dy),
            lambda d, a, b: _line(d, [a, b], (160, 190, 232, 150), 0.7),
            ("agent_tether",),
            f"tether_{kind}",
        )
        WORLD.put(img, ("agent_drone", kind), lambda d, kind=kind: _paint_agent_drone(d, hx, hy, kind), (dx, dy), f"drone_{kind}")
    if pose["scan"] > 0.0:
        scan = round(pose["scan"], 3)

        def rings(d) -> None:
            for i in range(3):
                _ellipse(d, hx, hy, 10 + i * 7 + scan * 6, 8 + i * 4 + scan * 4, (0, 0, 0, 0), (96, 236, 240, int(140 - i * 30)), 0.8)

        WORLD.put(img, ("agent_rings", scan), rings, (cx, cy + 4), "scan_rings")
    if pose["deploy"] > 0.0:
        deploy = round(pose["deploy"], 3)

        def legs(d) -> None:
            for side in (-1, 1):
                _capsule(d, (hx + side * 4, hy + 16), (hx + side * (18 + deploy * 18), hy + 32), 2.0, (160, 188, 236, 190), OUTLINE, None)

        WORLD.put(img, ("agent_deploy", deploy), legs, (cx, cy), "deploy")
    if pose["hurt"] > 0.0:
        hurt = round(pose["hurt"], 3)
        WORLD.put(
            img,
            ("agent_hurt", hurt),
            lambda d: _alpha_ellipse(d._image, hx, hy, 34, 26, (255, 92, 110, int(70 * hurt))),
            (cx, cy + 2),
            "hurt",
        )
    return _downsample(img)


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
    "synthetic_friend": _entry("synthetic_friend", _render_synthetic_friend, 132),
    "hand_saint": _entry("hand_saint", _render_hand_saint, 124),
    "spaghetti_event": _entry("spaghetti_event", _render_spaghetti, 132),
    "helpful_liar": _entry("helpful_liar", _render_helpful_liar, 128),
    "ai_slop": _entry("ai_slop", _render_ai_slop, 124),
    "agent_swarm": _entry("agent_swarm", _render_agent_swarm, 124),
}

__all__ = ["TARGETS"]

# ---- Local actor-contract metadata -------------------------------------------------
# Keep per-target actor metadata with the multi-renderer so the contract stays
# tied to the drawn entity instead of a central registry table.
LOCAL_ACTOR_METADATA_BY_TARGET = {
    "agent_swarm": {
        "actor": {"character_id": "npc_agent_swarm", "display_name": "Agent Swarm"},
        "body": {
            "body_plan": "PropActor",
            "body_kind": "PropLike",
            "mass_class": "Light",
            "traits": ["floating", "prop_actor", "ai_era", "swarm"],
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
        "tags": ["floating", "prop_actor", "ai_era", "swarm"],
        "sockets": {
            "center": {
                "source": "explicit.profile.floating_prop",
                "point": {"x": 80.0, "y": 80.0},
            },
            "projectile_origin": {
                "source": "explicit.profile.floating_prop",
                "point": {"x": 92.0, "y": 72.0},
            },
            "speech_bubble": {
                "source": "explicit.profile.floating_prop",
                "point": {"x": 80.0, "y": 24.0},
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
            "locomotion.orbit": {"animation": "orbit", "events": []},
            "action.special.deploy": {
                "animation": "deploy",
                "events": [
                    {
                        "t": 0.5,
                        "event": "summon_minion",
                        "source": "explicit.profile.ai_era",
                    }
                ],
            },
        },
    },
    "ai_slop": {
        "actor": {"character_id": "npc_ai_slop", "display_name": "AI Slop"},
        "body": {
            "body_plan": "Crawler",
            "body_kind": "Wide",
            "mass_class": "Heavy",
            "traits": ["ai_era", "sludge", "enemy", "no_hands"],
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
            "action.ranged.adblast": {
                "animation": "adblast",
                "events": [
                    {
                        "t": 0.5,
                        "event": "projectile_release",
                        "source": "explicit.profile.ai_slop",
                    }
                ],
            },
        },
    },
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
    "helpful_liar": {
        "actor": {"character_id": "npc_helpful_liar", "display_name": "Helpful Liar"},
        "body": {
            "body_plan": "PropActor",
            "body_kind": "PropLike",
            "mass_class": "Light",
            "traits": ["ai_era", "assistant", "unreliable"],
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
                "talk": True,
                "trade": None,
                "carry": None,
                "open_doors": [],
            },
        },
        "brain": "patrol_peaceful",
        "actions": "peaceful",
        "visual": {"default_pose": "idle"},
        "tags": ["floating", "prop_actor", "ai_era", "social"],
        "sockets": {
            "center": {
                "source": "explicit.profile.floating_prop",
                "point": {"x": 80.0, "y": 80.0},
            },
            "projectile_origin": {
                "source": "explicit.profile.floating_prop",
                "point": {"x": 92.0, "y": 72.0},
            },
            "speech_bubble": {
                "source": "explicit.profile.floating_prop",
                "point": {"x": 80.0, "y": 24.0},
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
    "spaghetti_event": {
        "actor": {
            "character_id": "npc_spaghetti_event",
            "display_name": "Spaghetti Event",
        },
        "body": {
            "body_plan": "Crawler",
            "body_kind": "LowProfile",
            "mass_class": "Light",
            "traits": ["ai_era", "no_hands", "noodle"],
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
            "noodle_tip": {
                "source": "explicit.profile.spaghetti_event",
                "point": {"x": 112.0, "y": 72.0},
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
    "synthetic_friend": {
        "actor": {
            "character_id": "npc_synthetic_friend",
            "display_name": "Synthetic Friend",
        },
        "body": {
            "body_plan": "PropActor",
            "body_kind": "PropLike",
            "mass_class": "Light",
            "traits": ["ai_era", "social", "uncanny", "floating"],
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
                "talk": True,
                "trade": None,
                "carry": None,
                "open_doors": [],
            },
        },
        "brain": "patrol_peaceful",
        "actions": "peaceful",
        "visual": {"default_pose": "idle"},
        "tags": ["floating", "prop_actor", "ai_era", "social"],
        "sockets": {
            "center": {
                "source": "explicit.profile.floating_prop",
                "point": {"x": 80.0, "y": 80.0},
            },
            "projectile_origin": {
                "source": "explicit.profile.floating_prop",
                "point": {"x": 92.0, "y": 72.0},
            },
            "speech_bubble": {
                "source": "explicit.profile.floating_prop",
                "point": {"x": 80.0, "y": 24.0},
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
        },
    },
}

for _target_name, _actor_metadata in LOCAL_ACTOR_METADATA_BY_TARGET.items():
    if _target_name in TARGETS:
        TARGETS[_target_name].setdefault("actor_metadata", _actor_metadata)
