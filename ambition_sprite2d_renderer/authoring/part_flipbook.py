"""The transform flipbook: a character's frames as reusable part rasters plus
per-frame ordered draws.

A character that paints through part scopes (``draw.part(name, origin, deg)``,
see ``draw_recorder``) already says which of its pixels are rigid parts. This
module captures one paint pass per frame as ordered LAYERS:

* a PART layer is a rigid part in its local coordinates, placed at an origin
  and an angle. Identical local geometry is one part, rasterized once;
* an OVERLAY layer is a run of frame-local geometry between two parts (the
  pirates' limbs and neck). Each run is rasterized for its own frame.

The paint order is kept: a frame's draws are its layers in paint order. One
overlay per frame cannot keep that order, because the runs sit between parts
(legs under the boots, the back arm under the torso), so every run is its own
draw.

Coordinates are the ones the published sheet uses. A frame's pixels reach the
sheet through ``downsample``'s per-frame fit and ``build_sheet``'s translation,
so each draw is placed through the same maps, relative to the published
``feet_pixel`` (the body rig's origin, see ``body_rig``). An overlay goes
through its frame's own fit and lands on the sheet's pixel grid. A part is
rasterized at the largest fit any frame uses and is drawn scaled down to its
frame's fit.

``recompose`` draws a frame back from the published atlas and draws; the
parity check diffs it against the baked sheet frame.

A flipbook can leave rows to the baked sheet (a hybrid): ``baked_clips`` names
them, and the runtime draws them from the sheet. Each row of the sheet must be
a clip or a baked clip; the runtime refuses a flipbook that leaves a row out.
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from PIL import Image

#: Version of the published ``<target>_parts.ron`` schema.
PART_FLIPBOOK_SCHEMA_VERSION = 1

Call = Tuple[str, tuple, dict]


@dataclass
class Layer:
    """One paint-order layer of one frame."""

    kind: str  # "part" or "overlay"
    calls: List[Call]
    name: str = "overlay"
    origin: Tuple[float, float] = (0.0, 0.0)
    deg: float = 0.0

    def key(self) -> tuple:
        """Content identity of a part's local geometry."""
        return (self.name, repr(self.calls))


class LayerCapture:
    """Quacks like the part-scoped draw object and records paint order."""

    def __init__(self) -> None:
        self.layers: List[Layer] = []
        self._part: Optional[Layer] = None

    @contextmanager
    def part(self, name: str, origin, deg: float = 0.0):
        assert self._part is None, "nested part() scopes are not supported"
        self._part = Layer("part", [], name, (float(origin[0]), float(origin[1])), float(deg))
        try:
            yield self
        finally:
            layer, self._part = self._part, None
            if layer.calls:
                self.layers.append(layer)

    def begin_component(self, name: str) -> None:
        del name

    def end_component(self) -> None:
        pass

    @contextmanager
    def component(self, name: str):
        del name
        yield self

    def _record(self, method: str, args: tuple, kwargs: dict) -> None:
        if self._part is not None:
            self._part.calls.append((method, args, kwargs))
            return
        if not self.layers or self.layers[-1].kind != "overlay":
            self.layers.append(Layer("overlay", []))
        self.layers[-1].calls.append((method, args, kwargs))

    def polygon(self, *args, **kwargs):
        self._record("polygon", args, kwargs)

    def line(self, *args, **kwargs):
        self._record("line", args, kwargs)

    def ellipse(self, *args, **kwargs):
        self._record("ellipse", args, kwargs)

    def arc(self, *args, **kwargs):
        self._record("arc", args, kwargs)

    def rectangle(self, *args, **kwargs):
        self._record("rectangle", args, kwargs)


def _replay(draw: Any, calls: Sequence[Call]) -> None:
    for method, args, kwargs in calls:
        getattr(draw, method)(*args, **kwargs)


def _paint(size: Tuple[int, int], calls: Sequence[Call], origin=(0.0, 0.0)) -> Image.Image:
    """``calls`` painted as the canonical renderer paints them, placed at
    ``origin``, on a transparent ``size`` canvas."""
    from ..core.draw import blending_draw
    from .draw_recorder import PillowPartDraw

    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = PillowPartDraw(blending_draw(image))
    with draw.part("layer", origin, 0.0):
        _replay(draw, calls)
    return image


@dataclass
class PartRaster:
    name: str
    image: Image.Image
    #: The part's origin inside ``image``, in its pixels.
    pivot: Tuple[float, float]


@dataclass
class PartDraw:
    part: int
    #: Where the part's pivot lands: published pixels from the feet.
    at: Tuple[float, float]
    #: Radians, clockwise positive (+y is down).
    rotation: float = 0.0
    scale: Tuple[float, float] = (1.0, 1.0)


@dataclass
class PartFlipbook:
    target: str
    frame_size: Tuple[int, int]
    feet: Tuple[float, float]
    parts: List[PartRaster]
    #: row -> (frame duration in seconds, frames of ordered draws)
    clips: Dict[str, Tuple[float, List[List[PartDraw]]]]
    #: Rows left to the baked sheet: they have no draws here.
    baked_clips: List[str] = field(default_factory=list)
    #: Filled by ``pack``: per part (page, x, y, w, h).
    rects: List[Tuple[int, int, int, int, int]] = field(default_factory=list)
    pages: List[Image.Image] = field(default_factory=list)

    # -- measurement -----------------------------------------------------------
    def tight_texels(self) -> int:
        return sum(p.image.width * p.image.height for p in self.parts)

    def packed_texels(self) -> int:
        return sum(page.width * page.height for page in self.pages)

    def draw_count(self) -> int:
        return sum(len(frame) for _d, frames in self.clips.values() for frame in frames)

    def frame_count(self) -> int:
        return sum(len(frames) for _d, frames in self.clips.values())

    # -- publishing ------------------------------------------------------------
    def pack(self) -> None:
        from .packer import FrameInput, pack_frames

        result = pack_frames(
            [
                FrameInput(key=index, image=part.image, logical_size=part.image.size)
                for index, part in enumerate(self.parts)
            ],
            trim=False,
        )
        self.pages = result.pages
        self.rects = [
            (p.page, p.x, p.y, p.w, p.h)
            for p in (result.placements[index] for index in range(len(self.parts)))
        ]

    def page_names(self) -> List[str]:
        return [
            f"{self.target}_parts.png" if index == 0 else f"{self.target}_parts_{index}.png"
            for index in range(len(self.pages))
        ]

    def to_ron(self) -> str:
        assert self.rects, "pack() before to_ron()"

        def num(value: float) -> str:
            text = f"{float(value):.4f}".rstrip("0")
            return text + "0" if text.endswith(".") else text

        def pair(values) -> str:
            return f"({num(values[0])}, {num(values[1])})"

        lines = [
            "(",
            f"    schema_version: {PART_FLIPBOOK_SCHEMA_VERSION},",
            f'    target: "{self.target}",',
            "    pages: [" + ", ".join(f'"{name}"' for name in self.page_names()) + "],",
            f"    frame_size: ({self.frame_size[0]}, {self.frame_size[1]}),",
            f"    feet_pixel: {pair(self.feet)},",
            "    parts: [",
        ]
        for part, (page, x, y, w, h) in zip(self.parts, self.rects):
            lines.append(
                f'        (name: "{part.name}", page: {page}, rect: ({x}, {y}, {w}, {h}), '
                f"pivot: {pair(part.pivot)}),"
            )
        lines += ["    ],", "    clips: {"]
        for row, (duration, frames) in self.clips.items():
            lines.append(f'        "{row}": (frame_duration_s: {num(duration)}, frames: [')
            for frame in frames:
                lines.append("            [")
                for d in frame:
                    lines.append(
                        f"                (part: {d.part}, at: {pair(d.at)}, "
                        f"rotation: {num(d.rotation)}, scale: {pair(d.scale)}),"
                    )
                lines.append("            ],")
            lines.append("        ]),")
        lines.append("    },")
        # Only when there are some, so a flipbook of parts alone publishes the
        # same file as before hybrids existed.
        if self.baked_clips:
            lines.append("    baked_clips: [" + ", ".join(f'"{row}"' for row in self.baked_clips) + "],")
        lines += [")", ""]
        return "\n".join(lines)

    def write(self, out_dir: Path) -> Dict[str, Path]:
        """Write the atlas pages and ``<target>_parts.ron``."""
        if not self.pages:
            self.pack()
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        written: Dict[str, Path] = {}
        for page, name in zip(self.pages, self.page_names()):
            path = out_dir / name
            page.save(path)
            written[name] = path
        ron = out_dir / f"{self.target}_parts.ron"
        ron.write_text(self.to_ron())
        written["ron"] = ron
        return written

    # -- recomposition -----------------------------------------------------------
    def part_image(self, index: int) -> Image.Image:
        """Part ``index`` as the published atlas holds it."""
        if not self.rects:
            return self.parts[index].image
        page, x, y, w, h = self.rects[index]
        return self.pages[page].crop((x, y, x + w, y + h))

    def recompose(self, row: str, index: int) -> Image.Image:
        """Frame ``index`` of ``row`` drawn from the published parts, at the
        published frame size."""
        canvas = Image.new("RGBA", self.frame_size, (0, 0, 0, 0))
        for d in self.clips[row][1][index]:
            image = self.part_image(d.part)
            pivot = self.parts[d.part].pivot
            px, py = d.at[0] + self.feet[0], d.at[1] + self.feet[1]
            if d.rotation == 0.0 and d.scale == (1.0, 1.0):
                ox, oy = px - pivot[0], py - pivot[1]
                if abs(ox - round(ox)) < 1e-6 and abs(oy - round(oy)) < 1e-6:
                    layer = Image.new("RGBA", self.frame_size, (0, 0, 0, 0))
                    layer.paste(image, (round(ox), round(oy)))
                    canvas.alpha_composite(layer)
                    continue
            # A part pixel p lands at at + R S (p - pivot), R turning
            # clockwise (+y down). PIL asks the inverse, in continuous
            # coordinates: p = pivot + S^-1 R^T (q - at).
            c, s = math.cos(d.rotation), math.sin(d.rotation)
            kx, ky = 1.0 / d.scale[0], 1.0 / d.scale[1]
            a, b = kx * c, kx * s
            e, f = -ky * s, ky * c
            layer = image.transform(
                self.frame_size,
                Image.Transform.AFFINE,
                (a, b, pivot[0] - a * px - b * py, e, f, pivot[1] - e * px - f * py),
                resample=Image.Resampling.BICUBIC,
            )
            canvas.alpha_composite(layer)
        return canvas


def parity(
    reference: Image.Image, candidate: Image.Image, threshold: int = 64, radius: int = 1
) -> float:
    """Fraction of the frame's drawn pixels (drawn in either image) that the
    other image does not reproduce: no pixel within ``radius`` of it differs by
    ``threshold`` or less in every premultiplied RGBA channel. Both directions
    are counted.

    The radius is there because a part is resampled on its own, not with the
    whole frame, so an anti-aliased edge can fall one pixel over. A misplaced
    or missing part moves more than one pixel and is still counted.
    """
    import numpy as np

    def premultiplied(image: Image.Image):
        array = np.asarray(image.convert("RGBA"), dtype=np.int32)
        alpha = array[..., 3:4]
        return np.concatenate([array[..., :3] * alpha // 255, alpha], axis=-1)

    def unmatched(a, b):
        """Pixels of ``a`` with no close match in ``b`` within the radius."""
        h, w = a.shape[:2]
        pad = np.pad(b, ((radius, radius), (radius, radius), (0, 0)))
        matched = np.zeros((h, w), dtype=bool)
        for oy in range(2 * radius + 1):
            for ox in range(2 * radius + 1):
                window = pad[oy : oy + h, ox : ox + w]
                matched |= np.abs(a - window).max(axis=-1) <= threshold
        return ~matched

    ref, cand = premultiplied(reference), premultiplied(candidate)
    drawn = (ref[..., 3] > 0) | (cand[..., 3] > 0)
    wrong = (unmatched(ref, cand) | unmatched(cand, ref)) & drawn
    return float(wrong.sum()) / max(1, int(drawn.sum()))


def build_flipbook(
    target: str,
    rows: Sequence[Tuple[str, int, int]],
    paint: Callable[[Any, str, int, int], None],
    canvas: Tuple[int, int],
    frame_fits: Mapping[Tuple[str, int], Mapping[str, float]],
    frame_transform: Mapping[str, float],
    feet: Tuple[float, float],
    drawn_size: Tuple[int, int],
    frame_size: Tuple[int, int],
    baked_rows: Sequence[str] = (),
) -> PartFlipbook:
    """Capture every frame of ``rows`` (``(row, frame count, duration ms)``)
    and build its flipbook. A row in ``baked_rows`` is not captured; the
    flipbook names it as a baked clip.

    ``paint(draw, row, index, count)`` is the canonical paint pass on the
    ``canvas`` (supersampled) frame. ``frame_fits`` are ``downsample``'s
    per-frame maps; ``frame_transform`` and ``feet`` are the sheet's (see
    ``body_rig``). ``drawn_size`` is the frame ``downsample`` fits into and
    ``frame_size`` the published frame.
    """
    dx, dy = float(frame_transform["dx"]), float(frame_transform["dy"])
    unknown = sorted(set(baked_rows) - {row for row, _count, _ms in rows})
    assert not unknown, f"baked rows {unknown} are not rows of {target}"
    baked = [row for row, _count, _ms in rows if row in set(baked_rows)]
    rows = [entry for entry in rows if entry[0] not in set(baked_rows)]
    captured: Dict[Tuple[str, int], List[Layer]] = {}
    for row, count, _ms in rows:
        for index in range(int(count)):
            capture = LayerCapture()
            paint(capture, row, index, int(count))
            captured[(row, index)] = capture.layers
    part_scale = max(max(frame_fits[key]["sx"], frame_fits[key]["sy"]) for key in captured)

    def published(fit, point) -> Tuple[float, float]:
        return (
            (point[0] - fit["x0"]) * fit["sx"] + fit["ox"] + dx - feet[0],
            (point[1] - fit["y0"]) * fit["sy"] + fit["oy"] + dy - feet[1],
        )

    parts: List[PartRaster] = []
    part_index: Dict[tuple, int] = {}
    margin = 2 * max(canvas)
    clips: Dict[str, Tuple[float, List[List[PartDraw]]]] = {}
    for row, count, duration_ms in rows:
        frames: List[List[PartDraw]] = []
        for index in range(int(count)):
            fit = frame_fits[(row, index)]
            draws: List[PartDraw] = []
            for layer in captured[(row, index)]:
                if layer.kind == "part":
                    key = layer.key()
                    if key not in part_index:
                        part_index[key] = len(parts)
                        parts.append(_part_raster(layer, margin, part_scale))
                    draws.append(
                        PartDraw(
                            part_index[key],
                            published(fit, layer.origin),
                            math.radians(layer.deg),
                            (fit["sx"] / part_scale, fit["sy"] / part_scale),
                        )
                    )
                    continue
                raster = _overlay_raster(layer, canvas, fit, drawn_size)
                if raster is None:
                    continue
                image, (left, top) = raster
                parts.append(PartRaster(f"{layer.name}:{row}:{index}", image, (0.0, 0.0)))
                draws.append(PartDraw(len(parts) - 1, (left + dx - feet[0], top + dy - feet[1])))
            frames.append(draws)
        clips[row] = (float(duration_ms) / 1000.0, frames)
    return PartFlipbook(target, tuple(frame_size), tuple(feet), parts, clips, baked)


def _part_raster(layer: Layer, margin: int, scale: float) -> PartRaster:
    """A rigid part painted once in its local frame and fitted to ``scale``.

    The crop keeps the resampling kernel's reach around the art before the
    resize: LANCZOS spreads an edge up to three output pixels, and the baked
    frame keeps that fringe, so a tight crop would thin every outline.
    """
    image = _paint((2 * margin, 2 * margin), layer.calls, (margin, margin))
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return PartRaster(layer.name, Image.new("RGBA", (1, 1), (0, 0, 0, 0)), (0.0, 0.0))
    reach = math.ceil(3.0 / scale)
    x0, y0 = max(0, bbox[0] - reach), max(0, bbox[1] - reach)
    x1, y1 = min(image.width, bbox[2] + reach), min(image.height, bbox[3] + reach)
    crop = image.crop((x0, y0, x1, y1))
    size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
    fitted = crop.resize(size, Image.Resampling.LANCZOS)
    kx, ky = size[0] / crop.width, size[1] / crop.height
    trim = fitted.getchannel("A").getbbox() or (0, 0, 1, 1)
    pivot = ((margin - x0) * kx - trim[0], (margin - y0) * ky - trim[1])
    return PartRaster(layer.name, fitted.crop(trim), pivot)


def _overlay_raster(layer: Layer, canvas, fit, drawn_size):
    """A frame-local run through its frame's own fit, tight: ``(image, (left,
    top))`` in the drawn frame's pixels, or ``None`` when it draws nothing."""
    image = _paint(canvas, layer.calls)
    x0, y0 = int(fit["x0"]), int(fit["y0"])
    x1, y1 = int(fit["x1"]), int(fit["y1"])
    fitted = image.crop((x0, y0, x1, y1)).resize(
        (int(fit["nw"]), int(fit["nh"])), Image.Resampling.LANCZOS
    )
    frame = Image.new("RGBA", tuple(drawn_size), (0, 0, 0, 0))
    frame.alpha_composite(fitted, (int(fit["ox"]), int(fit["oy"])))
    bbox = frame.getchannel("A").getbbox()
    if bbox is None:
        return None
    return frame.crop(bbox), (bbox[0], bbox[1])
