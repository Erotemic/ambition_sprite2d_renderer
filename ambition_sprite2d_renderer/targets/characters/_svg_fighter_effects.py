"""Small supersampled effect compositor for SVG-rigged fighter targets.

Character anatomy stays in the canonical SVG/rig. This module only supplies
reusable, resolution-independent effect drawing around solved rig poses.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from PIL import Image, ImageFont

from ...authoring import rigdoc, shape_rig
from ...authoring.rigdoc import RigDocument, RenderPadding, normalize_render_padding
from ...core.draw import blending_draw
from ...profiling import profile

Color = tuple[int, int, int, int]
Point = tuple[float, float]
World = Mapping[str, object]
EffectFn = Callable[["FxCanvas", float, World, Mapping[str, float]], None]


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def smooth(value: float) -> float:
    x = clamp01(value)
    return x * x * (3.0 - 2.0 * x)


def pulse(value: float) -> float:
    return math.sin(math.pi * clamp01(value))


def fade(color: Color, alpha: float) -> Color:
    return color[:3] + (int(round(color[3] * clamp01(alpha))),)


def mix(a: Color, b: Color, amount: float) -> Color:
    q = clamp01(amount)
    return tuple(int(round(x + (y - x) * q)) for x, y in zip(a, b))  # type: ignore[return-value]


def bone_origin(world: World, name: str, fallback: Point) -> Point:
    transform = world.get(name)
    origin = getattr(transform, "origin", None)
    if origin is None:
        return fallback
    return float(origin[0]), float(origin[1])


#: A primitive whose box covers fewer frame pixels than this is a SPECK: a
#: piece of its own only while the frame's draw budget lasts, else drawn with
#: its neighbours into one dust raster per run. A star field is dozens of
#: specks a frame; as pieces they cost almost no texels (a few star shapes)
#: but a draw each, and a fighter past `part_flipbook.REALIZE_MAX_DRAWS` is
#: drawn baked.
DUST_FRAME_PIXELS = 100

#: Pieces a frame keeps for sizeable primitives: a speck becomes a piece only
#: while more than this many remain.
SPECK_RESERVE = 8

#: Draws a frame keeps free of effect pieces below the realize limit (a swing
#: trail, a hit flash, and slack: a slot per draw is a sprite per body).
DRAW_MARGIN = 16


class FxCanvas:
    """Transparent supersampled canvas with base-frame coordinates.

    ``origin`` lets an effect keep using the rig's logical coordinates while
    being drawn into a larger overscan raster. This is intentionally a canvas
    concern: effect authors should not have to rewrite every hardcoded point
    merely because publication needs more room around a rotating character.

    ⭐ WITH ``pieces``, EACH PRIMITIVE IS A PIECE. A ring, an ellipse, an arc, a line or
    a polygon is painted ONCE at full alpha in its own raster (cached by what it
    looks like) and placed through ``rigdoc.blit_rotated`` with its alpha as
    the draw's opacity, so a part flipbook stores a ring that pulses as one
    part. Painted as one layer raster a frame, Carl Stargan's orbit ring was a
    new part on every frame, and effect layers were a third of every part
    page's texels (`scripts/measure_part_waste.py`, 2026-10-04). Coordinates
    stay the whole supersampled pixels they always were, so the frame is the
    same picture. Past the frame's draw budget (and specks, before the
    budget's reserve) primitives are drawn into a dust raster, flushed as one
    layer whenever a piece is drawn after them (draw order kept).

    ⚠ OPT-IN, MEASURED PER CHARACTER. A pulsing radius or a moving point is a
    new raster every frame however it is recorded, and dust runs between
    pieces overlap: Carl Stargan's part texels fell 28%, the Perfect Cellular
    Automaton's 6%, and Noether's ROSE 17% (2026-10-04). An effect that recurs
    is cheapest authored as a glyph painted once and placed (``place``).
    Without ``pieces`` the canvas is one layer raster, as before.
    """

    def __init__(
        self,
        size: tuple[int, int],
        scale: int = 3,
        *,
        origin: Point = (0.0, 0.0),
        unit_scale: float = 1.0,
        name: str = "fx",
        budget: list | None = None,
        pieces: bool = False,
    ):
        self.size = size
        self.scale = max(1, int(scale))
        self.unit_scale = max(0.001, float(unit_scale))
        self.origin = (float(origin[0]), float(origin[1]))
        self.name = name
        self.pieces = pieces
        #: Speck pieces this frame may still draw, shared by its layers.
        self.budget = budget if budget is not None else [0]
        self.image = Image.new(
            "RGBA",
            (size[0] * self.scale, size[1] * self.scale),
            (0, 0, 0, 0),
        )
        self.draw = blending_draw(self.image)
        self._dust: Image.Image | None = None
        self._count = 0
        self._dirty = False

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def draw_scale(self) -> float:
        return self.scale * self.unit_scale

    def p(self, point: Point) -> tuple[int, int]:
        q = self.draw_scale
        return (
            int(round((point[0] + self.origin[0]) * q)),
            int(round((point[1] + self.origin[1]) * q)),
        )

    def box(self, center: Point, rx: float, ry: float) -> tuple[int, int, int, int]:
        x = center[0] + self.origin[0]
        y = center[1] + self.origin[1]
        q = self.draw_scale
        return (
            int(round((x - rx) * q)),
            int(round((y - ry) * q)),
            int(round((x + rx) * q)),
            int(round((y + ry) * q)),
        )

    def _stroke(self, width: float) -> int:
        return max(1, int(round(width * self.draw_scale)))

    def _flush_dust(self) -> None:
        if self._dust is not None:
            self._count += 1
            rigdoc.composite_layer(self.image, self._dust, name=f"{self.name}:dust{self._count}")
            self._dust = None

    def _paint(self, kind: str, extent, colors: Sequence[Color | None], paint, key) -> None:
        """Paint one primitive: ``extent`` its (x0, y0, x1, y1) in canvas
        pixels, ``colors`` the colours it inks, ``paint(draw, dx, dy, opaque)``
        paints it shifted by (dx, dy) with each colour made opaque (or as given
        when ``opaque`` is False), ``key`` what it looks like apart from where."""
        self._dirty = True
        inked = [c for c in colors if c is not None]
        if not inked:
            return
        if not self.pieces:
            paint(self.draw, 0, 0, False)
            return
        x0, y0 = int(math.floor(extent[0])) - 2, int(math.floor(extent[1])) - 2
        x1, y1 = int(math.ceil(extent[2])) + 3, int(math.ceil(extent[3])) + 3
        # Over the frame's draw budget, any primitive joins the dust: a lattice
        # of 200 cells as pieces put the Perfect Cellular Automaton at 244
        # draws a frame, drawn baked (2026-10-04).
        speck = (x1 - x0) * (y1 - y0) < DUST_FRAME_PIXELS * self.scale * self.scale
        if self.budget[0] <= 0 or (speck and self.budget[0] <= SPECK_RESERVE):
            if self._dust is None:
                self._dust = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
            paint(blending_draw(self._dust), 0, 0, False)
            return
        alphas = {c[3] for c in inked}
        if len(alphas) > 1:
            raise _MixedAlpha
        alpha = alphas.pop()
        if alpha <= 0:
            return
        self.budget[0] -= 1
        self._flush_dust()
        opaque = tuple(None if c is None else (c[0], c[1], c[2], 255) for c in colors)
        piece = shape_rig.piece(
            ("fx", kind, key, opaque, (x1 - x0, y1 - y0)),
            (x1 - x0, y1 - y0),
            (0.0, 0.0),
            lambda draw: paint(draw, -x0, -y0, True),
        )
        self._count += 1
        # `blit_rotated` truncates the faded alpha: half a level up lands it on
        # the level the primitive was authored at.
        opacity = 1.0 if alpha >= 255 else (alpha + 0.5) / 255.0
        rigdoc.blit_rotated(self.image, piece[0], (0.0, 0.0), (float(x0), float(y0)), 0.0, opacity,
                            part_name=f"{self.name}:{kind}{self._count}")

    def line(self, points: Sequence[Point], fill: Color, width: float = 1.0, joint: str = "curve") -> None:
        mapped = [self.p(point) for point in points]
        w = self._stroke(width)
        xs, ys = [x for x, _ in mapped], [y for _, y in mapped]
        extent = (min(xs) - w, min(ys) - w, max(xs) + w, max(ys) + w)
        local = tuple((x - min(xs), y - min(ys)) for x, y in mapped)

        def paint(draw, dx, dy, opaque):
            color = (fill[0], fill[1], fill[2], 255) if opaque else fill
            draw.line([(x + dx, y + dy) for x, y in mapped], fill=color, width=w, joint=joint)

        self._paint("line", extent, [fill], paint, (local, w, joint, min(xs) - extent[0], min(ys) - extent[1]))

    def polygon(self, points: Sequence[Point], fill: Color, outline: Color | None = None, width: float = 1.0) -> None:
        mapped = [self.p(point) for point in points]
        w = self._stroke(width)
        xs, ys = [x for x, _ in mapped], [y for _, y in mapped]
        extent = (min(xs) - w, min(ys) - w, max(xs) + w, max(ys) + w)
        local = tuple((x - min(xs), y - min(ys)) for x, y in mapped)

        def paint(draw, dx, dy, opaque):
            f = None if fill is None else ((fill[0], fill[1], fill[2], 255) if opaque else fill)
            o = None if outline is None else ((outline[0], outline[1], outline[2], 255) if opaque else outline)
            shifted = [(x + dx, y + dy) for x, y in mapped]
            if f is not None:
                draw.polygon(shifted, fill=f)
            if o is not None:
                draw.line([*shifted, shifted[0]], fill=o, width=w, joint="curve")

        try:
            self._paint("polygon", extent, [fill, outline], paint, (local, w))
        except _MixedAlpha:
            self.polygon(points, fill, None, width)
            self.polygon(points, None, outline, width)

    def ellipse(self, center: Point, rx: float, ry: float, fill: Color | None, outline: Color | None = None, width: float = 1.0) -> None:
        box = self.box(center, rx, ry)
        w = self._stroke(width) if outline else 1
        if box[2] < box[0] or box[3] < box[1]:
            return

        def paint(draw, dx, dy, opaque):
            f = None if fill is None else ((fill[0], fill[1], fill[2], 255) if opaque else fill)
            o = None if outline is None else ((outline[0], outline[1], outline[2], 255) if opaque else outline)
            draw.ellipse((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy), fill=f, outline=o, width=w)

        try:
            self._paint("ellipse", box, [fill, outline], paint, (box[2] - box[0], box[3] - box[1], w))
        except _MixedAlpha:
            self.ellipse(center, rx, ry, fill, None, width)
            self.ellipse(center, rx, ry, None, outline, width)

    def arc(self, center: Point, rx: float, ry: float, start: float, end: float, fill: Color, width: float = 1.0) -> None:
        box = self.box(center, rx, ry)
        w = self._stroke(width)
        if box[2] < box[0] or box[3] < box[1]:
            return

        def paint(draw, dx, dy, opaque):
            color = (fill[0], fill[1], fill[2], 255) if opaque else fill
            draw.arc((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy), start=start, end=end, fill=color, width=w)

        self._paint("arc", box, [fill], paint, (box[2] - box[0], box[3] - box[1], start, end, w))

    def text(self, center: Point, text: str, fill: Color, size: float = 6.0, *, bold: bool = True, stroke: Color | None = None) -> None:
        font_name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        try:
            font = ImageFont.truetype(font_name, max(5, int(round(size * self.draw_scale))))
        except OSError:
            font = ImageFont.load_default()
        measure = blending_draw(Image.new("RGBA", (1, 1)))
        stroke_width = max(1, self.scale // 2) if stroke else 0
        bbox = measure.textbbox((0, 0), text, font=font, stroke_width=1 if stroke else 0)
        q = self.draw_scale
        x = int(round((center[0] + self.origin[0]) * q - (bbox[2] - bbox[0]) / 2))
        y = int(round((center[1] + self.origin[1]) * q - (bbox[3] - bbox[1]) / 2))
        ink = measure.textbbox((x, y), text, font=font, stroke_width=stroke_width)

        def paint(draw, dx, dy, opaque):
            f = (fill[0], fill[1], fill[2], 255) if opaque else fill
            s = None if stroke is None else ((stroke[0], stroke[1], stroke[2], 255) if opaque else stroke)
            draw.text((x + dx, y + dy), text, font=font, fill=f, stroke_width=stroke_width, stroke_fill=s)

        try:
            self._paint("text", ink, [fill, stroke], paint, (text, font_name, font.size, stroke_width, x - ink[0], y - ink[1]))
        except _MixedAlpha:
            # A stroked label with its own alpha: one raster (rare, small).
            self._dirty = True
            if self._dust is None:
                self._dust = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
            paint(blending_draw(self._dust), 0, 0, False)

    def star(self, center: Point, radius: float, fill: Color, *, points: int = 5, inner: float = 0.43, rotation: float = -90.0, outline: Color | None = None) -> None:
        vertices: list[Point] = []
        for index in range(points * 2):
            angle = math.radians(rotation + index * 180.0 / points)
            r = radius if index % 2 == 0 else radius * inner
            vertices.append((center[0] + math.cos(angle) * r, center[1] + math.sin(angle) * r))
        self.polygon(vertices, fill, outline, 0.7)

    def arrow(self, start: Point, end: Point, fill: Color, width: float = 1.2, head: float = 4.0) -> None:
        self.line([start, end], fill, width)
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        for offset in (-0.55, 0.55):
            tip = (
                end[0] - math.cos(angle + offset) * head,
                end[1] - math.sin(angle + offset) * head,
            )
            self.line([end, tip], fill, width)

    def place(self, part, at: Point, degrees: float = 0.0, opacity: float = 1.0, name: str = "glyph") -> None:
        """Place an authored glyph (``shape_rig.piece``, painted at this
        canvas's pixels) with its pivot at the logical point ``at``, turned
        ``degrees`` clockwise and faded by ``opacity``: one raster however
        often it recurs. Only a ``pieces`` canvas records it as a part."""
        self._dirty = True
        self._flush_dust()
        q = self.draw_scale
        self._count += 1
        rigdoc.blit_rotated(
            self.image, part[0], part[1], ((at[0] + self.origin[0]) * q, (at[1] + self.origin[1]) * q),
            degrees, opacity, part_name=f"{self.name}:{name}{self._count}",
        )

    def finish(self) -> Image.Image:
        """The layer at frame resolution. A ``pieces`` canvas is reduced
        through ``rigdoc``'s seam, so a part flipbook reduces each piece the
        same way; otherwise as the one raster it is."""
        self._flush_dust()
        if self.scale == 1:
            return self.image
        if self.pieces:
            return rigdoc.downsampled_canvas(self.image, self.size, Image.Resampling.LANCZOS)
        return self.image.resize(self.size, Image.Resampling.LANCZOS)


class _MixedAlpha(Exception):
    """A primitive whose colours carry different alphas: one opacity cannot
    fade it, so it is painted as one primitive per colour."""


@profile
def compose_rig_frame(
    doc: RigDocument,
    animation: str,
    frame_idx: int,
    frame_count: int,
    *,
    behind: EffectFn | None = None,
    front: EffectFn | None = None,
    padding: RenderPadding | None = None,
    solved=None,
    rig_supersample: int | None = None,
    rig_image: Image.Image | None = None,
    fx_pieces: bool = False,
) -> Image.Image:
    t = doc.frame_time(animation, frame_idx, frame_count)
    if solved is None:
        solved = doc.solve(animation, t)
    world, params = solved
    base_size = (int(doc.frame["width"]), int(doc.frame["height"]))
    pad_left, pad_top, pad_right, pad_bottom = normalize_render_padding(padding)
    render_scale = max(1, int(doc.frame.get("render_scale", 1)))
    logical_size = (
        base_size[0] + pad_left + pad_right,
        base_size[1] + pad_top + pad_bottom,
    )
    size = (logical_size[0] * render_scale, logical_size[1] * render_scale)
    origin = (float(pad_left), float(pad_top))
    # Keep roughly 3x logical-pixel effect sampling. A rig already publishing
    # at 3x does not need another 3x supersample layer (which would create a 9x
    # logical-pixel intermediate for every foreground/background effect).
    effect_supersample = max(1, int(math.ceil(3.0 / render_scale)))

    # The speck budget both layers share: what the realize limit leaves after
    # the rig's own parts.
    from ...authoring.part_flipbook import REALIZE_MAX_DRAWS

    budget = [max(0, REALIZE_MAX_DRAWS - DRAW_MARGIN - len(doc.parts)) if fx_pieces else 0]
    behind_image = None
    if behind is not None:
        layer = FxCanvas(
            size,
            scale=effect_supersample,
            origin=origin,
            unit_scale=render_scale,
            name="fx_behind",
            budget=budget,
            pieces=fx_pieces,
        )
        behind(layer, t, world, params)
        if layer.dirty:
            behind_image = layer.finish()

    # ``render_at`` already returns a fresh RGBA image. Use it as the result
    # directly when there is no behind effect instead of allocating a blank
    # full-frame canvas and compositing the rig onto transparency first.
    if rig_image is None:
        rig_image = doc.render_at(
            animation,
            t,
            solved=solved,
            padding=padding,
            supersample=rig_supersample,
        )
    # Through rigdoc's seams, so a part flipbook knows what the frame is made
    # of (`part_flipbook.build_rig_flipbook`). The same pixels as compositing
    # straight onto the behind layer.
    if behind_image is None:
        result = rig_image
    else:
        result = Image.new("RGBA", behind_image.size, (0, 0, 0, 0))
        if fx_pieces:
            rigdoc.composite_canvas(result, behind_image)
        else:
            rigdoc.composite_layer(result, behind_image, name="fx_behind")
        rigdoc.composite_canvas(result, rig_image)

    if front is not None:
        layer = FxCanvas(
            size,
            scale=effect_supersample,
            origin=origin,
            unit_scale=render_scale,
            name="fx_front",
            budget=budget,
            pieces=fx_pieces,
        )
        front(layer, t, world, params)
        if layer.dirty:
            if fx_pieces:
                rigdoc.composite_canvas(result, layer.finish())
            else:
                rigdoc.composite_layer(result, layer.finish(), name="fx_front")
    return result


def orbit_point(center: Point, rx: float, ry: float, phase: float) -> Point:
    angle = phase * math.tau
    return center[0] + math.cos(angle) * rx, center[1] + math.sin(angle) * ry


def clock(canvas: FxCanvas, center: Point, radius: float, phase: float, color: Color) -> None:
    canvas.ellipse(center, radius, radius, fade((245, 239, 215, 255), color[3] / 255), color, 1.0)
    for i in range(12):
        angle = i * math.tau / 12.0
        a = (center[0] + math.cos(angle) * radius * 0.72, center[1] + math.sin(angle) * radius * 0.72)
        b = (center[0] + math.cos(angle) * radius * 0.88, center[1] + math.sin(angle) * radius * 0.88)
        canvas.line([a, b], color, 0.55)
    minute = phase * math.tau
    hour = phase * math.tau * 0.27
    canvas.line([center, (center[0] + math.sin(hour) * radius * 0.52, center[1] - math.cos(hour) * radius * 0.52)], color, 0.9)
    canvas.line([center, (center[0] + math.sin(minute) * radius * 0.72, center[1] - math.cos(minute) * radius * 0.72)], color, 0.7)
    canvas.ellipse(center, 0.8, 0.8, color)


__all__ = [
    "FxCanvas",
    "bone_origin",
    "clamp01",
    "clock",
    "compose_rig_frame",
    "fade",
    "mix",
    "orbit_point",
    "pulse",
    "smooth",
]
