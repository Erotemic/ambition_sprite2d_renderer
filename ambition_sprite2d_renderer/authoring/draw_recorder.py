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
"""
from __future__ import annotations

import math
from contextlib import contextmanager
from typing import Any, List, Optional, Sequence, Tuple

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

    def text(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - rare
        self.unsupported.add("text")

    # -- export -------------------------------------------------------------
    def to_svg(self) -> str:
        assert len(self._groups) == 1, "unclosed component() scope"
        body = "".join(self._groups[0][1])
        w, h = self.width, self.height
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
            f'width="{w}px" height="{h}px" viewBox="0 0 {w} {h}">'
            f'{body}</svg>'
        )


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
