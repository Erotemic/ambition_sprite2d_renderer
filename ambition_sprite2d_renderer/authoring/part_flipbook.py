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

#: Version of the published ``<target>_parts.ron`` schema. 2 added the track
#: table (each draw's identity across frames) and the per-clip tween policy.
PART_FLIPBOOK_SCHEMA_VERSION = 2

#: A clip's in-between policy. ``step`` shows each frame whole until the next;
#: ``linear`` moves each track from its place in one frame to its place in the
#: next (see ``tween_draws``). Published per clip, never chosen at runtime.
TWEEN_STEP = "step"
TWEEN_LINEAR = "linear"

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
    #: The draw's identity across frames (a rig part's name, or
    #: ``overlay:<layer>``): what an in-between pairs. ``None`` when unknown.
    track: Optional[str] = None


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
    #: row -> ``TWEEN_LINEAR`` for a clip whose frames are tweened; every other
    #: clip steps.
    tweens: Dict[str, str] = field(default_factory=dict)
    #: ``"snapped"``: every pivot and point is a whole pixel and a part turns the
    #: way ``rigdoc.blit_rotated`` turns it (a rig flipbook, see
    #: ``build_rig_flipbook``). ``"continuous"``: fitted placements (pirates).
    placement: str = "continuous"

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

        tracks: List[str] = []
        for _duration, frames in self.clips.values():
            for frame in frames:
                for d in frame:
                    if d.track is not None and d.track not in tracks:
                        tracks.append(d.track)
        track_index = {name: index for index, name in enumerate(tracks)}
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
        lines.append("    ],")
        if tracks:
            lines.append("    tracks: [" + ", ".join(f'"{name}"' for name in tracks) + "],")
        lines.append("    clips: {")
        for row, (duration, frames) in self.clips.items():
            tween = ", tween: Linear" if self.tweens.get(row) == TWEEN_LINEAR else ""
            lines.append(f'        "{row}": (frame_duration_s: {num(duration)}{tween}, frames: [')
            for frame in frames:
                lines.append("            [")
                for d in frame:
                    track = f", track: {track_index[d.track]}" if d.track is not None else ""
                    lines.append(
                        f"                (part: {d.part}, at: {pair(d.at)}, "
                        f"rotation: {num(d.rotation)}, scale: {pair(d.scale)}{track}),"
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

    @classmethod
    def from_published(cls, ron_path: Path, placement: str = "continuous") -> "PartFlipbook":
        """Read a published ``<target>_parts.ron`` (as ``to_ron`` writes it, one
        part or draw per line) with its atlas pages, so a frame can be
        recomposed from what shipped. ``placement`` is not in the file: a rig
        flipbook is ``"snapped"``."""
        import re

        ron_path = Path(ron_path)
        text = ron_path.read_text()
        number = r"(-?[\d.]+)"
        target = re.search(r'target: "([^"]+)"', text).group(1)
        pages = [Image.open(ron_path.parent / name).convert("RGBA") for name in re.findall(r'"([^"]+\.png)"', re.search(r"pages: \[([^\]]*)\]", text).group(1))]
        frame_size = tuple(int(v) for v in re.search(r"frame_size: \((\d+), (\d+)\)", text).groups())
        feet = tuple(float(v) for v in re.search(rf"feet_pixel: \({number}, {number}\)", text).groups())
        parts: List[PartRaster] = []
        rects: List[Tuple[int, int, int, int, int]] = []
        part_line = re.compile(
            rf'\(name: "([^"]*)", page: (\d+), rect: \((\d+), (\d+), (\d+), (\d+)\), pivot: \({number}, {number}\)\)'
        )
        draw_line = re.compile(
            rf"\(part: (\d+), at: \({number}, {number}\), rotation: {number}, scale: \({number}, {number}\)(?:, track: (\d+))?\)"
        )
        listed = re.search(r"tracks: \[([^\]]*)\]", text)
        tracks = re.findall(r'"([^"]+)"', listed.group(1)) if listed else []
        tweens: Dict[str, str] = {}
        clips: Dict[str, Tuple[float, List[List[PartDraw]]]] = {}
        row = None
        for line in text.splitlines():
            stripped = line.strip()
            match = part_line.search(stripped)
            if match and row is None:
                name, page, x, y, w, h, px, py = match.groups()
                rect = (int(page), int(x), int(y), int(w), int(h))
                rects.append(rect)
                parts.append(PartRaster(name, pages[rect[0]].crop((rect[1], rect[2], rect[1] + rect[3], rect[2] + rect[4])), (float(px), float(py))))
                continue
            head = re.match(rf'"([^"]+)": \(frame_duration_s: {number}(, tween: Linear)?, frames: \[', stripped)
            if head:
                row = head.group(1)
                clips[row] = (float(head.group(2)), [])
                if head.group(3):
                    tweens[row] = TWEEN_LINEAR
                continue
            if row is None:
                continue
            if stripped == "[":
                clips[row][1].append([])
            match = draw_line.search(stripped)
            if match:
                part, ax, ay, rotation, sx, sy, track = match.groups()
                clips[row][1][-1].append(
                    PartDraw(
                        int(part),
                        (float(ax), float(ay)),
                        float(rotation),
                        (float(sx), float(sy)),
                        tracks[int(track)] if track is not None else None,
                    )
                )
        baked = re.search(r"baked_clips: \[([^\]]*)\]", text)
        return cls(
            target,
            frame_size,
            feet,
            parts,
            clips,
            re.findall(r'"([^"]+)"', baked.group(1)) if baked else [],
            rects,
            pages,
            tweens,
            placement,
        )

    def draw_frame(
        self,
        canvas: Image.Image,
        row: str,
        index: int,
        feet_at: Tuple[float, float],
        flip: bool = False,
        draws: Optional[Sequence[PartDraw]] = None,
        mirror_x: Optional[float] = None,
    ) -> None:
        """Draw frame ``index`` of ``row`` onto ``canvas`` with the feet at
        ``feet_at`` (canvas pixels), unclipped by the frame. Snapped placement
        only. ``flip`` mirrors the body about the column ``mirror_x`` (a pixel
        edge; the feet when ``None``), as the runtime mirrors about the root's
        origin — the feet for an NPC, the quad's centre for a centre-anchored
        player."""
        assert self.placement == "snapped", "draw_frame draws a rig flipbook"
        layer = canvas if not flip else Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        # Mirroring about the column `m` (a pixel EDGE) sends pixel `i` to
        # `2 m - 1 - i`; drawn unflipped at `fx` then transposed, the feet land
        # at `width - fx`, so `fx = width - (2 m - feet)`.
        axis = feet_at[0] if mirror_x is None else mirror_x
        fx = feet_at[0] if not flip else canvas.width - (2.0 * axis - feet_at[0])
        for d in self.clips[row][1][index] if draws is None else draws:
            _snapped_blit(
                layer,
                self.part_image(d.part),
                self.parts[d.part].pivot,
                (d.at[0] + fx, d.at[1] + feet_at[1]),
                math.degrees(d.rotation),
            )
        if flip:
            canvas.alpha_composite(layer.transpose(Image.FLIP_LEFT_RIGHT))

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
            if self.placement == "snapped":
                _snapped_blit(canvas, image, pivot, (px, py), math.degrees(d.rotation))
                continue
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


def wrong_pixels(
    reference: Image.Image, candidate: Image.Image, threshold: int = 64, radius: int = 1
):
    """Boolean mask of the frame's drawn pixels (drawn in either image) that the
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
    return (unmatched(ref, cand) | unmatched(cand, ref)) & drawn, drawn


def parity(
    reference: Image.Image, candidate: Image.Image, threshold: int = 64, radius: int = 1
) -> float:
    """Fraction of the frame's drawn pixels that are ``wrong_pixels``."""
    wrong, drawn = wrong_pixels(reference, candidate, threshold, radius)
    return float(wrong.sum()) / max(1, int(drawn.sum()))


def largest_wrong_blob(
    reference: Image.Image, candidate: Image.Image, threshold: int = 64, radius: int = 1
) -> int:
    """Pixels in the largest 8-connected run of ``wrong_pixels``.

    ⛔ ``parity`` ALONE PASSES A MISSING EFFECT. Dropping one whole effect layer
    from a Mary-O transition frame moved ``parity`` by 1.43% on the median frame
    (measured 2026-10-02), under the old 2.5% bound and beside the anti-aliasing
    noise it is meant to forgive. Noise is scattered single pixels along edges;
    a missing star, orb or limb is one connected blob. This sees the blob.
    """
    wrong, _drawn = wrong_pixels(reference, candidate, threshold, radius)
    h, w = wrong.shape
    seen = set()
    largest = 0
    for y, x in zip(*wrong.nonzero()):
        if (y, x) in seen:
            continue
        size, stack = 0, [(int(y), int(x))]
        seen.add((int(y), int(x)))
        while stack:
            cy, cx = stack.pop()
            size += 1
            for ny in (cy - 1, cy, cy + 1):
                for nx in (cx - 1, cx, cx + 1):
                    if 0 <= ny < h and 0 <= nx < w and wrong[ny, nx] and (ny, nx) not in seen:
                        seen.add((ny, nx))
                        stack.append((ny, nx))
        largest = max(largest, size)
    return largest


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


# -- rig documents ---------------------------------------------------------------
#
# A character drawn by a ``RigDocument`` (``rigdoc``) already paints its frames
# as rigid parts: every sprite part is ONE raster, placed by ``blit_rotated`` at
# its bone's origin, turned by the bone's angle. So its flipbook is that call,
# recorded during the real render: the same raster, the same pivot, the same
# place, the same angle. Nothing is reconstructed.
#
# What a character composes AROUND its rig (effect layers, a body laid onto
# another canvas) goes through ``rigdoc.composite_layer`` and
# ``rigdoc.composite_canvas``, and is recorded the same way: an effect layer is
# an overlay draw, in paint order with the parts.
#
# ⭐ ONE PLACEMENT RULE. ``blit_rotated`` lands a raster on whole pixels: it
# rounds the pivot inside the raster and the world point it lands on, and turns
# the raster about that whole-pixel pivot. A flipbook published with the
# fractional pivot and point drew every frame up to 2.6% off the baked one
# (measured on Mary-O, 2026-10-02). So a rig flipbook publishes the ROUNDED
# pivot and point (``placement == "snapped"``), and recomposition turns a part
# the way ``blit_rotated`` does. The baked frame and the recomposed frame are
# then the same picture, and ``build_rig_flipbook`` refuses one that is not.


@dataclass
class PaintedPart:
    sprite: Image.Image
    pivot: Tuple[float, float]
    world: Tuple[float, float]
    degrees: float
    opacity: float
    name: str


@dataclass
class PaintedOverlay:
    image: Image.Image
    dest: Tuple[int, int]
    name: str


class PaintRecord:
    """Paint operations per canvas, in paint order. A canvas composited onto
    another brings its operations with it, so the frame a render returns holds
    the whole frame."""

    def __init__(self) -> None:
        self._ops: Dict[int, Tuple[Image.Image, list]] = {}

    def _list(self, canvas: Image.Image) -> list:
        entry = self._ops.get(id(canvas))
        if entry is None or entry[0] is not canvas:
            entry = (canvas, [])
            self._ops[id(canvas)] = entry
        return entry[1]

    def ops_for(self, frame: Image.Image) -> Optional[list]:
        entry = self._ops.get(id(frame))
        if entry is None or entry[0] is not frame:
            return None
        return list(entry[1])


@contextmanager
def recorded_paint():
    """Record every paint made through ``rigdoc``'s seams inside the block. The
    calls still paint. Yields a ``PaintRecord``."""
    from . import rigdoc

    record = PaintRecord()
    originals = (rigdoc.blit_rotated, rigdoc.composite_layer, rigdoc.composite_canvas)
    blit, layer_fn, canvas_fn = originals

    def recording_blit(canvas, sprite, pivot, world_px, delta_deg, opacity=1.0, **kwargs):
        record._list(canvas).append(
            PaintedPart(
                sprite,
                (float(pivot[0]), float(pivot[1])),
                (float(world_px[0]), float(world_px[1])),
                float(delta_deg),
                float(opacity),
                str(kwargs.get("part_name") or "part"),
            )
        )
        return blit(canvas, sprite, pivot, world_px, delta_deg, opacity, **kwargs)

    def recording_layer(canvas, layer, dest=(0, 0), *, name="overlay"):
        record._list(canvas).append(PaintedOverlay(layer, (int(dest[0]), int(dest[1])), str(name)))
        return layer_fn(canvas, layer, dest, name=name)

    def recording_canvas(canvas, frame, dest=(0, 0)):
        dx, dy = int(dest[0]), int(dest[1])
        ops = record.ops_for(frame)
        target = record._list(canvas)
        if ops is None:
            # Painted by something this record did not see: it is still a
            # picture of the frame, so it rides as one overlay.
            target.append(PaintedOverlay(frame, (dx, dy), "composited"))
        else:
            for op in ops:
                if isinstance(op, PaintedPart):
                    target.append(
                        PaintedPart(op.sprite, op.pivot, (op.world[0] + dx, op.world[1] + dy), op.degrees, op.opacity, op.name)
                    )
                else:
                    target.append(PaintedOverlay(op.image, (op.dest[0] + dx, op.dest[1] + dy), op.name))
        return canvas_fn(canvas, frame, dest)

    rigdoc.blit_rotated, rigdoc.composite_layer, rigdoc.composite_canvas = (
        recording_blit,
        recording_layer,
        recording_canvas,
    )
    try:
        yield record
    finally:
        rigdoc.blit_rotated, rigdoc.composite_layer, rigdoc.composite_canvas = originals


@contextmanager
def recorded_blits():
    """Record every ``rigdoc.blit_rotated`` call made inside the block, in
    paint order, as ``(sprite, pivot, world_px, delta_deg, opacity)``, whatever
    canvas it painted. The calls still paint. (The measurement scripts read
    this; a flipbook reads ``recorded_paint``.)"""
    from . import rigdoc

    calls: List[Tuple[Image.Image, Tuple[float, float], Tuple[float, float], float, float]] = []
    original = rigdoc.blit_rotated

    def recording(canvas, sprite, pivot, world_px, delta_deg, opacity=1.0, **kwargs):
        calls.append((sprite, (float(pivot[0]), float(pivot[1])), (float(world_px[0]), float(world_px[1])), float(delta_deg), float(opacity)))
        return original(canvas, sprite, pivot, world_px, delta_deg, opacity, **kwargs)

    rigdoc.blit_rotated = recording
    try:
        yield calls
    finally:
        rigdoc.blit_rotated = original


def tween_draws(flipbook: "PartFlipbook", row: str, index: int, t: float) -> List[PartDraw]:
    """The draws ``t`` (0..1) of the way from frame ``index`` of ``row`` to the
    next frame (the first after the last: a tweened clip loops).

    THE RULE, which the game's runtime implements the same way
    (`ambition_sprite_sheet::character::rigged::RiggedSpriteAsset::tweened`):
    the current frame's draws, in its order; a draw whose track is in the next
    frame WITH THE SAME PART moves linearly to it (its turn by the shorter
    way); any other draw holds still. A clip that steps, or ``t == 0``, is the
    frame itself.
    """
    _duration, frames = flipbook.clips[row]
    current = frames[index]
    if flipbook.tweens.get(row) != TWEEN_LINEAR or t <= 0.0:
        return list(current)
    following = {d.track: d for d in frames[(index + 1) % len(frames)] if d.track is not None}
    out: List[PartDraw] = []
    for d in current:
        target = following.get(d.track)
        if d.track is None or target is None or target.part != d.part:
            out.append(d)
            continue
        turn = (target.rotation - d.rotation + math.pi) % (2.0 * math.pi) - math.pi
        out.append(
            PartDraw(
                d.part,
                (d.at[0] + (target.at[0] - d.at[0]) * t, d.at[1] + (target.at[1] - d.at[1]) * t),
                d.rotation + turn * t,
                (d.scale[0] + (target.scale[0] - d.scale[0]) * t, d.scale[1] + (target.scale[1] - d.scale[1]) * t),
                d.track,
            )
        )
    return out


def _snapped_blit(canvas: Image.Image, image: Image.Image, pivot, at_px, degrees: float) -> None:
    """``blit_rotated`` at a whole-pixel pivot and point: the baked road.

    A published point is already whole. A TWEENED point is not, and is rounded
    half UP here: ``blit_rotated``'s ``round`` rounds halves to even, so two
    parts half-way between the same two places would round apart (12.5 -> 12,
    13.5 -> 14) and open a one-pixel seam between a limb and the body it hangs
    from (measured: an 11-pixel blob at t = 0.5 of Mary-O's walk)."""
    from . import rigdoc

    at_px = (math.floor(at_px[0] + 0.5), math.floor(at_px[1] + 0.5))
    rigdoc.blit_rotated(canvas, image, pivot, at_px, degrees, 1.0)


def build_rig_flipbook(
    target: str,
    rows: Sequence[Tuple[str, int, int]],
    render: Callable[[str, int, int], Image.Image],
    part_rows: Optional[Sequence[str]],
    feet: Tuple[float, float],
    frame_size: Tuple[int, int],
    tween_rows: Sequence[str] = (),
) -> PartFlipbook:
    """The flipbook of a rig-document character: ``part_rows`` from parts (every
    row when ``None``), and any other row of ``rows`` left to the baked sheet.
    ``tween_rows`` are published as tweened clips (``tween_draws``); the rest
    step.

    ``render(row, index, count)`` renders one sheet frame through the
    character's ``RigDocument`` and ``rigdoc``'s compositing seams. The canvas
    it returns must BE the published frame (no supersample, no crop), so a
    draw's place is a frame pixel; a frame of another size is refused. ``feet``
    is the sheet's feet pixel.

    ⛔ Each frame is drawn back from what was published and must equal the
    render exactly. A frame that differs had something painted outside the
    seams — a post-process over the whole frame, a direct ``ImageDraw`` — that
    no draw carries, and the flipbook is refused rather than published without
    it.
    """
    known = {row for row, _count, _ms in rows}
    selected = known if part_rows is None else set(part_rows)
    unknown = sorted(selected - known)
    assert not unknown, f"part rows {unknown} are not rows of {target}"
    parts: List[PartRaster] = []
    part_index: Dict[tuple, int] = {}
    clips: Dict[str, Tuple[float, List[List[PartDraw]]]] = {}

    def intern(name: str, image: Image.Image, pivot: Tuple[float, float]) -> int:
        key = (image.size, pivot, image.tobytes())
        if key not in part_index:
            part_index[key] = len(parts)
            parts.append(PartRaster(f"{name}{len(parts)}", image.copy(), pivot))
        return part_index[key]

    rendered: Dict[Tuple[str, int], Image.Image] = {}
    for row, count, duration_ms in rows:
        if row not in selected:
            continue
        frames: List[List[PartDraw]] = []
        for index in range(int(count)):
            with recorded_paint() as record:
                frame = render(row, index, int(count))
            rendered[(row, index)] = frame
            assert frame.size == tuple(frame_size), (
                f"{target} {row}:{index} renders {frame.size}, not the {tuple(frame_size)} frame"
            )
            ops = record.ops_for(frame)
            assert ops is not None, (
                f"{target} {row}:{index}: the returned frame was not painted through rigdoc's seams"
            )
            draws: List[PartDraw] = []
            for op in ops:
                if isinstance(op, PaintedPart):
                    # A part draw has no opacity of its own: a faded part is not
                    # a rigid part of this clip.
                    assert op.opacity >= 0.999, (
                        f"{target} {row}:{index} draws {op.name} at opacity {op.opacity:.3f}"
                    )
                    pivot = (float(round(op.pivot[0])), float(round(op.pivot[1])))
                    at = (float(round(op.world[0])), float(round(op.world[1])))
                    draws.append(
                        PartDraw(
                            intern("part", op.sprite, pivot),
                            (at[0] - feet[0], at[1] - feet[1]),
                            math.radians(op.degrees),
                            track=op.name,
                        )
                    )
                else:
                    bbox = op.image.getchannel("A").getbbox()
                    if bbox is None:
                        continue
                    left, top = op.dest[0] + bbox[0], op.dest[1] + bbox[1]
                    draws.append(
                        PartDraw(
                            intern(f"{op.name}:", op.image.crop(bbox), (0.0, 0.0)),
                            (left - feet[0], top - feet[1]),
                            track=f"overlay:{op.name}",
                        )
                    )
            tracks = [d.track for d in draws]
            assert len(set(tracks)) == len(tracks), f"{target} {row}:{index} names a track twice: {tracks}"
            frames.append(draws)
        clips[row] = (float(duration_ms) / 1000.0, frames)
    baked = [row for row, _count, _ms in rows if row not in selected]
    untweenable = sorted(set(tween_rows) - set(clips))
    assert not untweenable, f"tween rows {untweenable} are not part clips of {target}"
    flipbook = PartFlipbook(
        target,
        tuple(frame_size),
        tuple(feet),
        parts,
        clips,
        baked,
        tweens={row: TWEEN_LINEAR for row in tween_rows},
        placement="snapped",
    )
    for (row, index), frame in rendered.items():
        worst = _max_channel_difference(flipbook.recompose(row, index), frame)
        if worst > REPLAY_ROUNDING:
            raise AssertionError(
                f"{target} {row}:{index}: the draws do not reproduce the render (a channel "
                f"differs by {worst}) — something painted the frame outside rigdoc's seams"
            )
    return flipbook


#: How far a replayed frame may differ from its render, per 8-bit channel.
#: ``alpha_composite`` rounds each step, so it is associative only to within one
#: level: a body composited onto its own canvas and then over an effect layer
#: lands one level off the same parts composited straight over the layer
#: (measured: 4 pixels by 1 on Mary-O's fire `transform`). Anything a seam did
#: not carry differs by far more.
REPLAY_ROUNDING = 1


def _max_channel_difference(a: Image.Image, b: Image.Image) -> int:
    from PIL import ImageChops

    extrema = ImageChops.difference(a.convert("RGBA"), b.convert("RGBA")).getextrema()
    return max(high for _low, high in extrema)
