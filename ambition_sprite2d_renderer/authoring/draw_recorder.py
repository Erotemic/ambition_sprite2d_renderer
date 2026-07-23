"""Capture procedural PIL drawing as an SVG scene — the PIL->SVG converter.

Non-bone characters (the pirate family, and every other target drawn through
``sheet_build``'s ``poly`` / ``line`` / ``circle`` / ``ellipse`` helpers) paint
themselves with a tiny vocabulary that bottoms out in exactly three Pillow
calls: ``ImageDraw.polygon``, ``ImageDraw.line`` and ``ImageDraw.ellipse``.

``DrawRecorder`` **quacks like** ``PIL.ImageDraw.ImageDraw`` for that subset:
pass it where a character expects its ``draw`` object and every part paints
itself into a growing list of SVG elements instead of pixels. Because each
Pillow primitive maps onto its exact SVG counterpart (``<polygon>``,
``<polyline>``, ``<ellipse>``), the captured scene is geometrically identical
to the raster by construction — so a re-rasterization lands within
antialiasing tolerance of the original (``raster-equivalent`` in the
equivalence harness), and the SVG becomes an editable source going forward.

This is the reusable half of the conversion recipe:
``docs/planning/engine/svg-component-character-migration.md``. It records the
mechanical baseline SVG; a human then makes it pleasant to edit. The recorder
uses only Pillow-free stdlib, so it stays importable anywhere.

``component(name)`` scopes subsequent primitives under a named ``<g>`` so the
exported document already carries semantic parts (hat, coat, head, ...) rather
than one flat soup of shapes.

``part(name, origin, deg)`` goes further: primitives inside a part scope are
authored in the part's LOCAL coordinates, and the recorder registers the local
geometry ONCE (content-deduplicated across frames) and places it with a
``<use transform="translate(..) rotate(..)">``. That turns a procedural
character into the migration's target shape — an editable parts library plus
per-frame placements — instead of N flattened copies of every shape. The
Pillow twin, :class:`PillowPartDraw`, runs the *same* local-coordinate paint
code against a real ``ImageDraw`` by flattening each part transform into the
coordinates, so one paint pass serves raster output, SVG capture, and the
parts library simultaneously.
"""
from __future__ import annotations

import math
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Sequence, Tuple

Number = float
Point = Tuple[Number, Number]


def _color(c: Any) -> Tuple[str, float]:
    """A Pillow colour -> (css-rgb, opacity). Accepts (r,g,b[,a]) or a string."""
    if c is None:
        return "none", 0.0
    if isinstance(c, str):
        return c, 1.0
    if isinstance(c, (tuple, list)):
        if len(c) >= 4:
            r, g, b, a = c[0], c[1], c[2], c[3]
            return f"rgb({r},{g},{b})", round(a / 255.0, 4)
        r, g, b = c[0], c[1], c[2]
        return f"rgb({r},{g},{b})", 1.0
    return str(c), 1.0


def _fmt(n: Number) -> str:
    # Compact numeric formatting; keep sub-pixel precision for supersampled art.
    return f"{float(n):.3f}".rstrip("0").rstrip(".")


def _points(points: Sequence[Any]) -> str:
    # Pillow accepts [(x,y), ...] or a flat [x0,y0,x1,y1,...]; support both.
    if points and isinstance(points[0], (int, float)):
        it = iter(points)
        pairs = list(zip(it, it))
    else:
        pairs = [(p[0], p[1]) for p in points]
    return " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in pairs)


class DrawRecorder:
    """Records a subset of the ``ImageDraw`` API as SVG elements."""

    def __init__(self, size: Tuple[int, int], *, supersample: int = 1) -> None:
        self.width, self.height = size
        self.supersample = supersample
        self._groups: List[Tuple[str, List[str]]] = [("root", [])]
        self.calls = 0
        self.unsupported: set = set()
        # Registered parts: id -> (semantic name, local-geometry SVG body).
        # Content-addressed, so identical local geometry across frames (or
        # across a whole animation set) registers exactly once.
        self.part_defs: Dict[str, Tuple[str, str]] = {}
        self._part_stack: List[Tuple[str, Point, float, List[str]]] = []

    # -- part scoping (local-coordinate, registered geometry) ----------------
    @contextmanager
    def part(self, name: str, origin: Point, deg: float = 0.0):
        """Record subsequent primitives in the part's LOCAL coordinates.

        On exit the local geometry is registered once (content-deduplicated)
        and placed with ``<use transform="translate(origin) rotate(deg)">``.
        """
        assert not self._part_stack, "nested part() scopes are not supported"
        self._part_stack.append((name, origin, deg, []))
        try:
            yield self
        finally:
            name, origin, deg, elems = self._part_stack.pop()
            body = "".join(elems)
            if body:
                import hashlib

                pid = f"part_{name}_{hashlib.sha1(body.encode()).hexdigest()[:8]}"
                self.part_defs.setdefault(pid, (name, body))
                t = f"translate({_fmt(origin[0])} {_fmt(origin[1])})"
                if deg:
                    t += f" rotate({_fmt(deg)})"
                self._emit(f'<use href="#{pid}" xlink:href="#{pid}" transform="{t}"/>')

    # -- component scoping --------------------------------------------------
    def begin_component(self, name: str) -> None:
        self._groups.append((name, []))

    def end_component(self) -> None:
        name, elems = self._groups.pop()
        if elems:
            body = "".join(elems)
            safe = name.replace('"', "'")
            self._emit(f'<g inkscape:label="{safe}" inkscape:groupmode="layer">{body}</g>')

    @contextmanager
    def component(self, name: str):
        self.begin_component(name)
        try:
            yield self
        finally:
            self.end_component()

    def _emit(self, element: str) -> None:
        if self._part_stack:
            self._part_stack[-1][3].append(element)
        else:
            self._groups[-1][1].append(element)

    # -- ImageDraw-compatible primitives ------------------------------------
    def polygon(self, xy: Sequence[Any], fill: Any = None,
                outline: Any = None, width: int = 1) -> None:
        self.calls += 1
        pts = _points(xy)
        attrs = [f'points="{pts}"']
        fc, fo = _color(fill)
        attrs.append(f'fill="{fc}"' if fill is not None else 'fill="none"')
        if fill is not None and fo != 1.0:
            attrs.append(f'fill-opacity="{fo}"')
        if outline is not None:
            oc, oo = _color(outline)
            attrs.append(f'stroke="{oc}" stroke-width="{_fmt(width)}"')
            if oo != 1.0:
                attrs.append(f'stroke-opacity="{oo}"')
        self._emit(f'<polygon {" ".join(attrs)}/>')

    def line(self, xy: Sequence[Any], fill: Any = None, width: int = 1,
             joint: Optional[str] = None) -> None:
        self.calls += 1
        pts = _points(xy)
        sc, so = _color(fill)
        attrs = [f'points="{pts}"', 'fill="none"', f'stroke="{sc}"',
                 f'stroke-width="{_fmt(width)}"']
        if so != 1.0:
            attrs.append(f'stroke-opacity="{so}"')
        # Pillow's joint="curve" rounds inner corners; round line ends match its
        # wide-stroke look far better than the SVG default butt/miter.
        attrs.append('stroke-linejoin="round" stroke-linecap="round"')
        self._emit(f'<polyline {" ".join(attrs)}/>')

    def ellipse(self, xy: Sequence[Number], fill: Any = None,
                outline: Any = None, width: int = 1) -> None:
        self.calls += 1
        x0, y0, x1, y1 = xy
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        rx, ry = abs(x1 - x0) / 2.0, abs(y1 - y0) / 2.0
        attrs = [f'cx="{_fmt(cx)}" cy="{_fmt(cy)}" rx="{_fmt(rx)}" ry="{_fmt(ry)}"']
        fc, fo = _color(fill)
        attrs.append(f'fill="{fc}"' if fill is not None else 'fill="none"')
        if fill is not None and fo != 1.0:
            attrs.append(f'fill-opacity="{fo}"')
        if outline is not None:
            oc, oo = _color(outline)
            attrs.append(f'stroke="{oc}" stroke-width="{_fmt(width)}"')
            if oo != 1.0:
                attrs.append(f'stroke-opacity="{oo}"')
        self._emit(f'<ellipse {" ".join(attrs)}/>')

    # Pillow calls these occasionally; keep the recorder from crashing and note
    # the gap so a caller knows the capture was not fully faithful.
    def rectangle(self, xy: Sequence[Number], fill: Any = None,
                  outline: Any = None, width: int = 1) -> None:
        x0, y0, x1, y1 = xy
        self.polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                     fill=fill, outline=outline, width=width)

    def arc(self, xy: Sequence[Number], start: float, end: float,
            fill: Any = None, width: int = 1) -> None:
        # Pillow draws an elliptical arc, angles in degrees clockwise from the
        # +x axis (y points down). Sample it into a stroked polyline — faithful
        # to a few tenths of a pixel and trivially rasterizable.
        self.calls += 1
        x0, y0, x1, y1 = xy
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        rx, ry = abs(x1 - x0) / 2.0, abs(y1 - y0) / 2.0
        sweep = (end - start) % 360 or 360.0
        steps = max(2, int(sweep / 4))
        pts = []
        for i in range(steps + 1):
            a = math.radians(start + sweep * i / steps)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
        self.line(pts, fill=fill, width=width)

    def pieslice(self, xy: Sequence[Number], start: float, end: float,
                 fill: Any = None, outline: Any = None, width: int = 1) -> None:
        # Wedge: centre + sampled arc, closed as a polygon.
        self.calls += 1
        x0, y0, x1, y1 = xy
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        rx, ry = abs(x1 - x0) / 2.0, abs(y1 - y0) / 2.0
        sweep = (end - start) % 360 or 360.0
        steps = max(2, int(sweep / 4))
        pts = [(cx, cy)]
        for i in range(steps + 1):
            a = math.radians(start + sweep * i / steps)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
        self.polygon(pts, fill=fill, outline=outline, width=width)

    def rounded_rectangle(self, xy: Sequence[Number], radius: float = 0,
                          fill: Any = None, outline: Any = None,
                          width: int = 1, corners: Any = None) -> None:
        self.calls += 1
        x0, y0, x1, y1 = xy
        r = min(radius, abs(x1 - x0) / 2, abs(y1 - y0) / 2)
        if r <= 0:
            self.rectangle(xy, fill=fill, outline=outline, width=width)
            return
        # Quarter-arc-sampled rounded rect (corners arg: treat all rounded).
        pts: List[Point] = []
        centres = [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0),
                   (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]
        for cx, cy, a0 in centres:
            for i in range(7):
                a = math.radians(a0 + 90 * i / 6)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.polygon(pts, fill=fill, outline=outline, width=width)

    def point(self, xy: Sequence[Any], fill: Any = None) -> None:
        # Single pixels: a 1x1 rect each (rare; used by speckle effects).
        if xy and isinstance(xy[0], (int, float)):
            it = iter(xy)
            pairs = list(zip(it, it))
        else:
            pairs = [(p[0], p[1]) for p in xy]
        for x, y in pairs:
            self.rectangle((x, y, x + 1, y + 1), fill=fill)

    def text(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - rare
        self.unsupported.add("text")

    def chord(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        self.unsupported.add("chord")

    # -- export -------------------------------------------------------------
    def defs_svg(self) -> str:
        """The registered parts as a ``<defs>`` block ('' when no parts)."""
        if not self.part_defs:
            return ""
        inner = "".join(
            f'<g id="{pid}" inkscape:label="{name}">{body}</g>'
            for pid, (name, body) in self.part_defs.items()
        )
        return f"<defs>{inner}</defs>"

    def body_svg(self) -> str:
        assert len(self._groups) == 1, "unclosed component() scope"
        assert not self._part_stack, "unclosed part() scope"
        return "".join(self._groups[0][1])

    def snapshot_svg(self) -> str:
        """Serialize current content, virtually closing any open scopes.

        Composite hooks fold a layer's recording mid-paint, while the painter
        may legitimately have component() scopes open; the snapshot closes
        them in the serialization only — recording state is untouched.
        """
        out = "".join(self._groups[0][1])
        tail = ""
        for name, elems in self._groups[1:]:
            safe = name.replace('"', "'")
            out += (f'<g inkscape:label="{safe}" inkscape:groupmode="layer">'
                    + "".join(elems))
            tail += "</g>"
        return out + tail

    def to_svg(self) -> str:
        w, h = self.width, self.height
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" '
            'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
            f'width="{w}px" height="{h}px" viewBox="0 0 {w} {h}">'
            f'{self.defs_svg()}{self.body_svg()}</svg>'
        )


class PillowPartDraw:
    """Run part-scoped local-coordinate paint code against a real ImageDraw.

    The twin of :class:`DrawRecorder`: the same ``paint(draw, ...)`` pass that
    records an SVG parts library also rasterizes, because this wrapper flattens
    each ``part(origin, deg)`` transform into the coordinates before delegating
    to Pillow. The transform math mirrors ``sheet_build.transform`` exactly
    (scale, then rotate, then translate) so converted code stays pixel-faithful
    to what the old world-coordinate drawing produced.
    """

    def __init__(self, draw: Any) -> None:
        self._draw = draw
        self._origin: Point = (0.0, 0.0)
        self._deg: float = 0.0

    # -- scopes --------------------------------------------------------------
    @contextmanager
    def part(self, name: str, origin: Point, deg: float = 0.0):
        del name
        assert self._origin == (0.0, 0.0) and self._deg == 0.0, "nested part()"
        self._origin, self._deg = (float(origin[0]), float(origin[1])), float(deg)
        try:
            yield self
        finally:
            self._origin, self._deg = (0.0, 0.0), 0.0

    def begin_component(self, name: str) -> None:  # grouping is SVG-only
        del name

    def end_component(self) -> None:
        pass

    @contextmanager
    def component(self, name: str):
        del name
        yield self

    # -- coordinate flattening ----------------------------------------------
    def _pt(self, p: Point) -> Point:
        x, y = float(p[0]), float(p[1])
        if self._deg:
            rad = math.radians(self._deg)
            c, s = math.cos(rad), math.sin(rad)
            x, y = (x * c - y * s, x * s + y * c)
        return (self._origin[0] + x, self._origin[1] + y)

    def _pts(self, points: Sequence[Any]) -> List[Point]:
        if points and isinstance(points[0], (int, float)):
            it = iter(points)
            pairs = list(zip(it, it))
        else:
            pairs = [(p[0], p[1]) for p in points]
        return [self._pt(p) for p in pairs]

    def _bbox(self, xy: Sequence[Number]) -> Tuple[float, float, float, float]:
        """Transform an axis-aligned bbox; rotation only allowed for circles."""
        x0, y0, x1, y1 = xy
        if self._deg:
            rx, ry = abs(x1 - x0) / 2.0, abs(y1 - y0) / 2.0
            assert abs(rx - ry) < 1e-9, \
                "only circles may live in a rotated part() scope"
            cx, cy = self._pt(((x0 + x1) / 2.0, (y0 + y1) / 2.0))
            return (cx - rx, cy - ry, cx + rx, cy + ry)
        ox, oy = self._origin
        return (x0 + ox, y0 + oy, x1 + ox, y1 + oy)

    # -- primitives ----------------------------------------------------------
    def polygon(self, xy, fill=None, outline=None, width=1):
        if outline is None:
            self._draw.polygon(self._pts(xy), fill=fill)
        else:
            self._draw.polygon(self._pts(xy), fill=fill, outline=outline, width=width)

    def line(self, xy, fill=None, width=1, joint=None):
        self._draw.line(self._pts(xy), fill=fill, width=width, joint=joint)

    def ellipse(self, xy, fill=None, outline=None, width=1):
        self._draw.ellipse(self._bbox(xy), fill=fill, outline=outline, width=width)

    def arc(self, xy, start, end, fill=None, width=1):
        assert not self._deg, "arc inside a rotated part() scope is unsupported"
        self._draw.arc(self._bbox(xy), start=start, end=end, fill=fill, width=width)

    def rectangle(self, xy, fill=None, outline=None, width=1):
        assert not self._deg, "rectangle in rotated scope: use polygon"
        self._draw.rectangle(self._bbox(xy), fill=fill, outline=outline, width=width)


def rasterize_svg(svg: str, size: Tuple[int, int]):
    """Rasterize an SVG string to an RGBA image at ``size`` pixels."""
    import io

    import resvg_py
    from PIL import Image

    png = resvg_py.svg_to_bytes(svg_string=svg)
    img = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
    if img.size != tuple(size):
        img = img.resize(size, Image.LANCZOS)
    return img
