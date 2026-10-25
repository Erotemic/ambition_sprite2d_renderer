"""The gate's dialing glyphs: ΛΕΓΑΛΛΥ ΔΙΣΤΙΝΧΤ as fifteen distinct symbols.

The ring's inscription spells LEGALLY DISTINCT in Greek capitals, one glyph
per chevron, Λ at 12 o'clock. Λ, Ι and Τ repeat, and every chevron must be its
own symbol (Jon, 2026-10-24), so a repeat carries a small ring, the gate's own
shape: the second Λ holds the ring in its counter, the third wears it at the
apex where the legs meet (a drafting compass), and the second Ι and Τ wear it
threaded on the stem.

Each glyph is one geometry, in font units (a 1000-unit em, the cap height
``CAP``, y up, the baseline at 0): stroke centrelines with round caps and
joins, and rings. ``contours`` turns it into closed outlines that fill by
the non-zero rule, and the SVG, the PNG and the font are all drawn from those
outlines, so the ring art, the dial wheel and text show the same shapes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

Point = Tuple[float, float]
Contour = List[Point]

#: The height of a capital, in font units of a 1000-unit em.
CAP = 700.0
#: The weight of every stroke.
STROKE = 92.0
#: The band of a decoration ring: thinner than a stroke, so it reads as an
#: ornament on the letter rather than a second letter.
RING_BAND = 56.0
#: The space on each side of a glyph's ink.
SIDE_BEARING = 60.0

_B = STROKE / 2.0  # the centreline of a stroke that sits on the baseline
_T = CAP - STROKE / 2.0  # the centreline of a stroke at the cap height
_M = CAP / 2.0


@dataclass(frozen=True)
class Line:
    """A polyline stroked ``STROKE`` wide with round caps and round joins."""

    points: Tuple[Point, ...]
    closed: bool = False


@dataclass(frozen=True)
class Ring:
    """A circle stroked ``RING_BAND`` wide about its centreline ``radius``."""

    center: Point
    radius: float


Shape = Line | Ring


@dataclass(frozen=True)
class GateGlyph:
    """One chevron's symbol.

    ``id`` names it everywhere (sheet rows, font glyph names, the catalog);
    ``index`` is its chevron, clockwise from 12 o'clock; ``letter`` the Greek
    capital it is drawn from and ``latin`` the letter of LEGALLY DISTINCT it
    stands for; ``repeat`` counts earlier chevrons with the same letter.
    """

    id: str
    index: int
    letter: str
    latin: str
    repeat: int
    width: float
    shapes: Tuple[Shape, ...] = field(repr=False)

    @property
    def advance(self) -> float:
        return self.width + 2.0 * SIDE_BEARING


# --- the letters --------------------------------------------------------------


def _lambda() -> Tuple[float, List[Shape]]:
    return 600.0, [Line(((_B, _B), (300.0, _T), (600.0 - _B, _B)))]


# The counter ring of a decorated Λ: as large as the space under the apex
# allows while leaving open ground between it and both legs.
_LAMBDA_RING = Ring((300.0, 200.0), 72.0)


def _alpha() -> Tuple[float, List[Shape]]:
    width, shapes = _lambda()
    y = 250.0
    x = _B + (y - _B) * (300.0 - _B) / (_T - _B)
    return width, shapes + [Line(((x, y), (width - x, y)))]


def _delta() -> Tuple[float, List[Shape]]:
    return 600.0, [Line(((_B, _B), (300.0, _T), (600.0 - _B, _B)), closed=True)]


def _epsilon() -> Tuple[float, List[Shape]]:
    return 500.0, [
        Line(((500.0 - _B, _T), (_B, _T), (_B, _B), (500.0 - _B, _B))),
        Line(((_B, _M), (420.0, _M))),
    ]


def _gamma() -> Tuple[float, List[Shape]]:
    return 480.0, [Line(((_B, _B), (_B, _T), (480.0 - _B, _T)))]


def _upsilon() -> Tuple[float, List[Shape]]:
    return 560.0, [
        Line(((_B, _T), (280.0, _M), (560.0 - _B, _T))),
        Line(((280.0, _M), (280.0, _B))),
    ]


def _iota() -> Tuple[float, List[Shape]]:
    return 300.0, [
        Line(((_B, _T), (300.0 - _B, _T))),
        Line(((150.0, _T), (150.0, _B))),
        Line(((_B, _B), (300.0 - _B, _B))),
    ]


def _sigma() -> Tuple[float, List[Shape]]:
    return 520.0, [Line(((520.0 - _B, _T), (_B, _T), (270.0, _M), (_B, _B), (520.0 - _B, _B)))]


def _tau() -> Tuple[float, List[Shape]]:
    return 600.0, [Line(((_B, _T), (600.0 - _B, _T))), Line(((300.0, _T), (300.0, _B)))]


def _nu() -> Tuple[float, List[Shape]]:
    return 520.0, [Line(((_B, _B), (_B, _T), (520.0 - _B, _B), (520.0 - _B, _T)))]


def _chi() -> Tuple[float, List[Shape]]:
    return 600.0, [Line(((_B, _T), (600.0 - _B, _B))), Line(((_B, _B), (600.0 - _B, _T)))]


_LETTERS = {
    "Λ": ("lambda", "L", _lambda),
    "Ε": ("epsilon", "E", _epsilon),
    "Γ": ("gamma", "G", _gamma),
    "Α": ("alpha", "A", _alpha),
    "Υ": ("upsilon", "Y", _upsilon),
    "Δ": ("delta", "D", _delta),
    "Ι": ("iota", "I", _iota),
    "Σ": ("sigma", "S", _sigma),
    "Τ": ("tau", "T", _tau),
    "Ν": ("nu", "N", _nu),
    "Χ": ("chi", "C", _chi),
}

#: The ring's inscription, one letter per chevron.
INSCRIPTION = "ΛΕΓΑΛΛΥΔΙΣΤΙΝΧΤ"


# --- the repeats --------------------------------------------------------------


def _hole_gap(radius: float) -> float:
    """How far from a ring's centre a stroke into it ends, so its round cap
    meets the hole's edge and the hole stays open."""
    return radius - RING_BAND / 2.0 + STROKE / 2.0


def _apex_ringed(width: float) -> List[Shape]:
    """A Λ whose legs meet in a ring at the cap height."""
    radius = 74.0
    center = (width / 2.0, CAP - radius - RING_BAND / 2.0)
    legs = []
    for foot in ((_B, _B), (width - _B, _B)):
        dx, dy = center[0] - foot[0], center[1] - foot[1]
        reach = math.hypot(dx, dy) - _hole_gap(radius)
        legs.append(Line((foot, (foot[0] + dx * reach / math.hypot(dx, dy), foot[1] + dy * reach / math.hypot(dx, dy)))))
    return legs + [Ring(center, radius)]


def _threaded(shapes: List[Shape], stem: Line, center: Point, radius: float) -> List[Shape]:
    """``shapes`` with the vertical ``stem`` broken by a ring at ``center``.

    The stem stops where its round cap meets the ring's hole, so the hole stays
    open (the ring is threaded on the stem, not a letter with a bar through an
    O).
    """
    (x, top), (_, bottom) = stem.points
    gap = _hole_gap(radius)
    kept = [shape for shape in shapes if shape != stem]
    return kept + [
        Line(((x, top), (x, center[1] + gap))),
        Line(((x, center[1] - gap), (x, bottom))),
        Ring(center, radius),
    ]


def _decorate(letter: str, repeat: int, width: float, shapes: List[Shape]) -> List[Shape]:
    if repeat == 0:
        return shapes
    if letter == "Λ" and repeat == 1:
        return shapes + [_LAMBDA_RING]
    if letter == "Λ" and repeat == 2:
        return _apex_ringed(width)
    if letter in ("Ι", "Τ") and repeat == 1:
        stem = next(s for s in shapes if isinstance(s, Line) and len(s.points) == 2 and s.points[0][0] == s.points[1][0])
        radius = 92.0 if letter == "Τ" else 84.0
        center = (stem.points[0][0], 300.0 if letter == "Τ" else _M)
        return _threaded(shapes, stem, center, radius)
    raise ValueError(f"no decoration for repeat {repeat} of {letter}")


def _build() -> Tuple[GateGlyph, ...]:
    glyphs = []
    seen: dict = {}
    for index, letter in enumerate(INSCRIPTION):
        name, latin, make = _LETTERS[letter]
        repeat = seen.get(letter, 0)
        seen[letter] = repeat + 1
        width, shapes = make()
        glyph_id = name if repeat == 0 else f"{name}_{repeat + 1}"
        glyphs.append(
            GateGlyph(glyph_id, index, letter, latin, repeat, width, tuple(_decorate(letter, repeat, width, shapes)))
        )
    return tuple(glyphs)


#: The fifteen symbols, in chevron order.
GLYPHS: Tuple[GateGlyph, ...] = _build()
BY_ID = {glyph.id: glyph for glyph in GLYPHS}


# --- outlines -----------------------------------------------------------------


def _circle(center: Point, radius: float, *, clockwise: bool = False) -> Contour:
    steps = max(24, int(math.ceil(radius / 4.0)))
    sign = -1.0 if clockwise else 1.0
    cx, cy = center
    return [
        (cx + radius * math.cos(sign * math.tau * k / steps), cy + radius * math.sin(sign * math.tau * k / steps))
        for k in range(steps)
    ]


def _capsule(a: Point, b: Point, radius: float) -> Contour:
    """A segment with round ends, counter-clockwise (y up)."""
    ax, ay = a
    bx, by = b
    heading = math.atan2(by - ay, bx - ax)
    steps = max(12, int(math.ceil(radius / 4.0)))
    out: Contour = []
    for end, start_angle in ((b, heading - math.pi / 2.0), (a, heading + math.pi / 2.0)):
        for k in range(steps + 1):
            angle = start_angle + math.pi * k / steps
            out.append((end[0] + radius * math.cos(angle), end[1] + radius * math.sin(angle)))
    return out


def shape_contours(shape: Shape) -> List[Contour]:
    """Closed outlines of one shape. Outer outlines run counter-clockwise and
    holes clockwise (y up), so overlapping shapes union under the non-zero
    rule and a ring's hole stays open."""
    if isinstance(shape, Ring):
        return [
            _circle(shape.center, shape.radius + RING_BAND / 2.0),
            _circle(shape.center, shape.radius - RING_BAND / 2.0, clockwise=True),
        ]
    points = list(shape.points) + ([shape.points[0]] if shape.closed else [])
    return [_capsule(a, b, STROKE / 2.0) for a, b in zip(points, points[1:])]


def contours(glyph: GateGlyph) -> List[Contour]:
    """The glyph's outlines, in font units, with its ink starting at x = 0."""
    return [contour for shape in glyph.shapes for contour in shape_contours(shape)]


# --- drawing ------------------------------------------------------------------


def _path_data(glyph: GateGlyph) -> str:
    parts = []
    for contour in contours(glyph):
        head, *rest = contour
        parts.append(f"M{head[0]:.1f} {head[1]:.1f}" + "".join(f"L{x:.1f} {y:.1f}" for x, y in rest) + "Z")
    return "".join(parts)


def glyph_svg(glyph: GateGlyph, *, color: str = "#000000", size_px: int | None = None) -> str:
    """The glyph as a standalone SVG: its advance box wide, the cap height
    plus a stroke of air above and below tall, y down as SVG draws."""
    pad = STROKE
    width = glyph.advance
    height = CAP + 2.0 * pad
    size = ""
    if size_px is not None:
        size = f' width="{size_px * width / height:.0f}" height="{size_px}"'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}"{size}>'
        f'<path fill="{color}" fill-rule="nonzero" '
        f'transform="matrix(1 0 0 -1 {SIDE_BEARING:.0f} {CAP + pad:.0f})" d="{_path_data(glyph)}"/>'
        "</svg>"
    )


def render_glyph(glyph: GateGlyph, height_px: int, color: str = "#000000") -> Image.Image:
    """The glyph's SVG rasterized ``height_px`` tall (the cap height plus a
    stroke of air above and below), on a transparent ground."""
    import io

    import resvg_py

    png = resvg_py.svg_to_bytes(svg_string=glyph_svg(glyph, color=color, size_px=height_px))
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


def _label_font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans.ttf",):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def review_sheet(*, ink: str = "#7ff3ff", ground: Tuple[int, int, int] = (22, 30, 40)) -> Image.Image:
    """Every glyph large with its id, the inscription at three sizes, and the
    glyphs on a dial ring, for judging the set by eye."""
    cell_w, cell_h, big = 190, 210, 128
    cols = 5
    rows = math.ceil(len(GLYPHS) / cols)
    ring_size = 560
    width = cols * cell_w + ring_size + 40
    height = max(rows * cell_h + 360, ring_size + 40)
    sheet = Image.new("RGBA", (width, height), ground + (255,))
    draw = ImageDraw.Draw(sheet)
    label = _label_font(15)
    for glyph in GLYPHS:
        x0 = (glyph.index % cols) * cell_w
        y0 = (glyph.index // cols) * cell_h
        tile = render_glyph(glyph, big, ink)
        sheet.alpha_composite(tile, (x0 + (cell_w - tile.width) // 2, y0 + 12))
        draw.text((x0 + 10, y0 + cell_h - 40), f"{glyph.index:2d} {glyph.id}", fill=(220, 220, 220), font=label)
        draw.text((x0 + 10, y0 + cell_h - 22), f"{glyph.letter} = {glyph.latin}", fill=(150, 160, 170), font=label)

    y = rows * cell_h + 16
    for size in (72, 36, 18):
        x = 16
        for glyph in GLYPHS:
            tile = render_glyph(glyph, size, ink)
            sheet.alpha_composite(tile, (x, y))
            x += tile.width
            if glyph.index == 6:
                x += size // 2
        y += size + 24

    # The glyphs round a dial, upright, Λ at 12 o'clock, clockwise.
    cx, cy = cols * cell_w + 20 + ring_size // 2, 20 + ring_size // 2
    outer, inner = ring_size // 2 - 4, ring_size // 2 - 110
    draw.ellipse((cx - outer, cy - outer, cx + outer, cy + outer), fill=(92, 74, 52, 255))
    draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), fill=ground + (255,))
    mid = (outer + inner) / 2.0
    for glyph in GLYPHS:
        angle = -math.pi / 2.0 + math.tau * glyph.index / len(GLYPHS)
        tile = render_glyph(glyph, 64, ink)
        gx, gy = cx + mid * math.cos(angle), cy + mid * math.sin(angle)
        sheet.alpha_composite(tile, (int(gx - tile.width / 2), int(gy - tile.height / 2)))
    return sheet


def write_svgs(directory, *, color: str = "#000000") -> List[str]:
    """One SVG per glyph, named by id, into ``directory``."""
    from pathlib import Path

    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for glyph in GLYPHS:
        path = out / f"{glyph.index:02d}_{glyph.id}.svg"
        path.write_text(glyph_svg(glyph, color=color) + "\n", encoding="utf-8")
        written.append(str(path))
    return written


def spell(text: str) -> List[GateGlyph]:
    """The glyphs of ``text`` in LEGALLY DISTINCT's own spelling: each Latin
    letter in turn takes the next chevron that stands for it, so "LEGALLY
    DISTINCT" spells the fifteen chevrons in order. Spaces are dropped."""
    taken: dict = {}
    out = []
    for char in text.upper():
        if char.isspace():
            continue
        candidates: Sequence[GateGlyph] = [g for g in GLYPHS if g.latin == char]
        if not candidates:
            raise ValueError(f"'{char}' is not a letter of LEGALLY DISTINCT")
        k = taken.get(char, 0)
        taken[char] = k + 1
        out.append(candidates[k % len(candidates)])
    return out
