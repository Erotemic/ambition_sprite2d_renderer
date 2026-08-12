"""Small supersampled effect compositor for SVG-rigged fighter targets.

Character anatomy stays in the canonical SVG/rig. This module only supplies
reusable, resolution-independent effect drawing around solved rig poses.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from PIL import Image, ImageFont

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


class FxCanvas:
    """Transparent supersampled canvas with base-frame coordinates.

    ``origin`` lets an effect keep using the rig's logical coordinates while
    being drawn into a larger overscan raster. This is intentionally a canvas
    concern: effect authors should not have to rewrite every hardcoded point
    merely because publication needs more room around a rotating character.
    """

    def __init__(
        self,
        size: tuple[int, int],
        scale: int = 3,
        *,
        origin: Point = (0.0, 0.0),
        unit_scale: float = 1.0,
    ):
        self.size = size
        self.scale = max(1, int(scale))
        self.unit_scale = max(0.001, float(unit_scale))
        self.origin = (float(origin[0]), float(origin[1]))
        self.image = Image.new(
            "RGBA",
            (size[0] * self.scale, size[1] * self.scale),
            (0, 0, 0, 0),
        )
        self.draw = blending_draw(self.image)
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

    def line(self, points: Sequence[Point], fill: Color, width: float = 1.0, joint: str = "curve") -> None:
        self._dirty = True
        self.draw.line(
            [self.p(point) for point in points],
            fill=fill,
            width=max(1, int(round(width * self.draw_scale))),
            joint=joint,
        )

    def polygon(self, points: Sequence[Point], fill: Color, outline: Color | None = None, width: float = 1.0) -> None:
        self._dirty = True
        mapped = [self.p(point) for point in points]
        self.draw.polygon(mapped, fill=fill)
        if outline is not None:
            self.draw.line(
                [*mapped, mapped[0]],
                fill=outline,
                width=max(1, int(round(width * self.draw_scale))),
                joint="curve",
            )

    def ellipse(self, center: Point, rx: float, ry: float, fill: Color | None, outline: Color | None = None, width: float = 1.0) -> None:
        self._dirty = True
        self.draw.ellipse(
            self.box(center, rx, ry),
            fill=fill,
            outline=outline,
            width=max(1, int(round(width * self.draw_scale))) if outline else 1,
        )

    def arc(self, center: Point, rx: float, ry: float, start: float, end: float, fill: Color, width: float = 1.0) -> None:
        self._dirty = True
        self.draw.arc(
            self.box(center, rx, ry),
            start=start,
            end=end,
            fill=fill,
            width=max(1, int(round(width * self.draw_scale))),
        )

    def text(self, center: Point, text: str, fill: Color, size: float = 6.0, *, bold: bool = True, stroke: Color | None = None) -> None:
        self._dirty = True
        font_name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        try:
            font = ImageFont.truetype(font_name, max(5, int(round(size * self.draw_scale))))
        except OSError:
            font = ImageFont.load_default()
        bbox = self.draw.textbbox((0, 0), text, font=font, stroke_width=1 if stroke else 0)
        q = self.draw_scale
        x = (center[0] + self.origin[0]) * q - (bbox[2] - bbox[0]) / 2
        y = (center[1] + self.origin[1]) * q - (bbox[3] - bbox[1]) / 2
        self.draw.text(
            (int(round(x)), int(round(y))),
            text,
            font=font,
            fill=fill,
            stroke_width=max(1, self.scale // 2) if stroke else 0,
            stroke_fill=stroke,
        )

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

    def finish(self) -> Image.Image:
        if self.scale == 1:
            return self.image
        return self.image.resize(self.size, Image.Resampling.LANCZOS)


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

    behind_image = None
    if behind is not None:
        layer = FxCanvas(
            size,
            scale=effect_supersample,
            origin=origin,
            unit_scale=render_scale,
        )
        behind(layer, t, world, params)
        if layer.dirty:
            behind_image = layer.finish()

    # ``render_at`` already returns a fresh RGBA image. Use it as the result
    # directly when there is no behind effect instead of allocating a blank
    # full-frame canvas and compositing the rig onto transparency first.
    rig_image = doc.render_at(
        animation,
        t,
        solved=solved,
        padding=padding,
        supersample=rig_supersample,
    )
    if behind_image is None:
        result = rig_image
    else:
        result = behind_image
        result.alpha_composite(rig_image)

    if front is not None:
        layer = FxCanvas(
            size,
            scale=effect_supersample,
            origin=origin,
            unit_scale=render_scale,
        )
        front(layer, t, world, params)
        if layer.dirty:
            result.alpha_composite(layer.finish())
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
