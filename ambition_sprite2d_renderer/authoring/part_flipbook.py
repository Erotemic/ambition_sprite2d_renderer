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
#: table (each draw's identity across frames) and the per-clip tween policy. 3
#: added the placement rule, a draw's opacity and a frame's opacity.
PART_FLIPBOOK_SCHEMA_VERSION = 3

#: How a flipbook's draws land (``PartFlipbook.placement``).
PLACEMENT_SNAPPED = "snapped"
PLACEMENT_CONTINUOUS = "continuous"

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
    #: The part's own opacity (its alpha scaled), in [0, 1].
    opacity: float = 1.0


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
    #: way ``rigdoc.blit_rotated`` turns it (a rig flipbook painted at frame
    #: resolution, see ``build_rig_flipbook``). ``"continuous"``: a part lands
    #: at its exact place, between pixels, resampled (a supersampled rig; the
    #: pirates' fitted placements).
    placement: str = PLACEMENT_CONTINUOUS
    #: A snapped flipbook's parts turn bilinear: its rig paints at a working
    #: scale of 3 or more (``rigdoc.rotation_resample``). Bicubic otherwise.
    bilinear: bool = False
    #: row -> each frame's opacity, for a clip whose frames fade AS ONE PICTURE
    #: (``rigdoc.faded_canvas``): the frame's draws are composited, then the
    #: result's alpha is scaled. A clip absent here is opaque.
    frame_opacity: Dict[str, List[float]] = field(default_factory=dict)

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
            f"    placement: {self.placement.capitalize()},",
            *(["    rotation_filter: Bilinear,"] if self.bilinear else []),
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
            faded = self.frame_opacity.get(row)
            fade = (
                ", frame_opacity: [" + ", ".join(num(v) for v in faded) + "]"
                if faded and any(v < 1.0 for v in faded)
                else ""
            )
            lines.append(f'        "{row}": (frame_duration_s: {num(duration)}{tween}{fade}, frames: [')
            for frame in frames:
                lines.append("            [")
                for d in frame:
                    track = f", track: {track_index[d.track]}" if d.track is not None else ""
                    opacity = f", opacity: {num(d.opacity)}" if d.opacity < 1.0 else ""
                    lines.append(
                        f"                (part: {d.part}, at: {pair(d.at)}, "
                        f"rotation: {num(d.rotation)}, scale: {pair(d.scale)}{track}{opacity}),"
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
    def from_published(cls, ron_path: Path, placement: Optional[str] = None) -> "PartFlipbook":
        """Read a published ``<target>_parts.ron`` (as ``to_ron`` writes it, one
        part or draw per line) with its atlas pages, so a frame can be
        recomposed from what shipped. The placement is the file's (schema 3);
        ``placement`` names it for an older file, and is refused when the file
        says otherwise."""
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
            rf"\(part: (\d+), at: \({number}, {number}\), rotation: {number}, scale: \({number}, {number}\)"
            rf"(?:, track: (\d+))?(?:, opacity: {number})?\)"
        )
        published = re.search(r"placement: (Snapped|Continuous),", text)
        if published:
            assert placement in (None, published.group(1).lower()), (
                f"{ron_path} is {published.group(1)}, not {placement}"
            )
            placement = published.group(1).lower()
        assert placement is not None, f"{ron_path} names no placement: pass it"
        bilinear = "rotation_filter: Bilinear," in text
        frame_opacity: Dict[str, List[float]] = {}
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
            head = re.match(
                rf'"([^"]+)": \(frame_duration_s: {number}(, tween: Linear)?(?:, frame_opacity: \[([^\]]*)\])?, frames: \[',
                stripped,
            )
            if head:
                row = head.group(1)
                clips[row] = (float(head.group(2)), [])
                if head.group(3):
                    tweens[row] = TWEEN_LINEAR
                if head.group(4):
                    frame_opacity[row] = [float(v) for v in head.group(4).split(",")]
                continue
            if row is None:
                continue
            if stripped == "[":
                clips[row][1].append([])
            match = draw_line.search(stripped)
            if match:
                part, ax, ay, rotation, sx, sy, track, opacity = match.groups()
                clips[row][1][-1].append(
                    PartDraw(
                        int(part),
                        (float(ax), float(ay)),
                        float(rotation),
                        (float(sx), float(sy)),
                        tracks[int(track)] if track is not None else None,
                        float(opacity) if opacity is not None else 1.0,
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
            bilinear,
            frame_opacity,
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
        ``feet_at`` (canvas pixels), unclipped by the frame. ``flip`` mirrors
        the body about the column ``mirror_x`` (a pixel edge; the feet when
        ``None``), as the runtime mirrors about the root's origin — the feet for
        an NPC, the quad's centre for a centre-anchored player."""
        layer = canvas if not flip else Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        # Mirroring about the column `m` (a pixel EDGE) sends pixel `i` to
        # `2 m - 1 - i`; drawn unflipped at `fx` then transposed, the feet land
        # at `width - fx`, so `fx = width - (2 m - feet)`.
        axis = feet_at[0] if mirror_x is None else mirror_x
        fx = feet_at[0] if not flip else canvas.width - (2.0 * axis - feet_at[0])
        self._paint_draws(
            layer,
            self.clips[row][1][index] if draws is None else draws,
            (fx, feet_at[1]),
            self.opacity_of(row, index),
        )
        if flip:
            canvas.alpha_composite(layer.transpose(Image.FLIP_LEFT_RIGHT))

    def opacity_of(self, row: str, index: int) -> float:
        """Frame ``index`` of ``row``'s opacity (``frame_opacity``)."""
        faded = self.frame_opacity.get(row)
        return 1.0 if not faded else faded[min(index, len(faded) - 1)]

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
        self._paint_draws(canvas, self.clips[row][1][index], self.feet, self.opacity_of(row, index))
        return canvas

    def _paint_draws(self, canvas: Image.Image, draws: Sequence[PartDraw], feet_at, opacity: float = 1.0) -> None:
        """``draws`` painted in order with the feet at ``feet_at``; a frame
        ``opacity`` below 1 fades their composite as one picture, the way
        ``rigdoc.faded_canvas`` does."""
        layer = canvas if opacity >= 1.0 else Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        for d in draws:
            self._paint_draw(layer, d, (d.at[0] + feet_at[0], d.at[1] + feet_at[1]))
        if layer is not canvas:
            layer.putalpha(layer.getchannel("A").point(lambda value: int(value * opacity)))
            canvas.alpha_composite(layer)

    def _paint_draw(self, canvas: Image.Image, d: PartDraw, at: Tuple[float, float]) -> None:
        image = self.part_image(d.part)
        pivot = self.parts[d.part].pivot
        if self.placement == PLACEMENT_SNAPPED:
            assert d.scale == (1.0, 1.0), "a snapped draw is never scaled"
            _snapped_blit(canvas, image, pivot, at, math.degrees(d.rotation), d.opacity, self.bilinear)
            return
        px, py = at
        if d.rotation == 0.0 and d.scale == (1.0, 1.0):
            ox, oy = px - pivot[0], py - pivot[1]
            if abs(ox - round(ox)) < 1e-6 and abs(oy - round(oy)) < 1e-6:
                canvas.alpha_composite(_faded(image, d.opacity), (round(ox), round(oy)))
                return
        # A part pixel p lands at at + R S (p - pivot), R turning clockwise
        # (+y down). PIL asks the inverse, in continuous coordinates:
        # p = pivot + S^-1 R^T (q - at). Resampled premultiplied, so the
        # colour under a transparent texel cannot bleed into the edge.
        c, s = math.cos(d.rotation), math.sin(d.rotation)
        kx, ky = 1.0 / d.scale[0], 1.0 / d.scale[1]
        a, b = kx * c, kx * s
        e, f = -ky * s, ky * c
        # Only the part's own box of the canvas is resampled: the same sample
        # points as a whole-canvas transform (the box is a whole-pixel shift
        # of the output), at a fraction of the cost. Measured against the
        # whole-canvas transform on 56 frames of three characters: 53 the same
        # bytes, 3 with three channel values one level apart (float rounding
        # of the shifted offsets).
        corners = [
            (px + d.scale[0] * (c * (x - pivot[0])) - d.scale[1] * (s * (y - pivot[1])),
             py + d.scale[0] * (s * (x - pivot[0])) + d.scale[1] * (c * (y - pivot[1])))
            for x in (0, image.width) for y in (0, image.height)
        ]
        # The bicubic kernel reaches 2 texels past the raster: 2 x scale pixels.
        reach = 3 + 2 * math.ceil(max(abs(d.scale[0]), abs(d.scale[1])))
        x0 = max(0, math.floor(min(x for x, _ in corners)) - reach)
        y0 = max(0, math.floor(min(y for _, y in corners)) - reach)
        x1 = min(canvas.width, math.ceil(max(x for x, _ in corners)) + reach)
        y1 = min(canvas.height, math.ceil(max(y for _, y in corners)) + reach)
        if x1 <= x0 or y1 <= y0:
            return
        layer = (
            image.convert("RGBa")
            .transform(
                (x1 - x0, y1 - y0),
                Image.Transform.AFFINE,
                (a, b, pivot[0] - a * (px - x0) - b * (py - y0), e, f, pivot[1] - e * (px - x0) - f * (py - y0)),
                resample=Image.Resampling.BICUBIC,
            )
            .convert("RGBA")
        )
        canvas.alpha_composite(_faded(layer, d.opacity), (x0, y0))


def _faded(image: Image.Image, opacity: float) -> Image.Image:
    """``image`` with its alpha scaled by ``opacity``, as ``blit_rotated`` fades."""
    if opacity >= 1.0:
        return image
    faded = image.copy()
    faded.putalpha(image.getchannel("A").point(lambda value: int(value * opacity)))
    return faded


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
#
# ⭐ A SUPERSAMPLED RIG IS CONTINUOUS. It paints at 4x and reduces the frame
# once (``rigdoc.downsampled_canvas``), so its parts land between frame pixels.
# The reduction is a seam: each part is reduced on its own and placed exactly
# (``placement == "continuous"``). The replay then differs from the render by
# resampling alone, a few levels on an edge, and is held to that
# (``CONTINUOUS_REPLAY_TOLERANCE``). A mirrored frame (``rigdoc.mirrored_canvas``)
# and a frame faded as one picture (``rigdoc.faded_canvas``) are seams too.


@dataclass
class PaintedPart:
    sprite: Image.Image
    pivot: Tuple[float, float]
    world: Tuple[float, float]
    degrees: float
    opacity: float
    name: str
    #: -1 when the part is drawn mirrored about its pivot (a mirrored frame).
    scale_x: float = 1.0
    #: Placed by ``blit_rotated``'s whole-pixel rule on the frame it returns.
    #: ``False`` once reduced from a supersampled canvas: its place is exact
    #: and fractional.
    exact: bool = True
    #: The opacity of the frame it is part of (``rigdoc.faded_canvas``).
    group: float = 1.0
    #: The filter it was turned with (``rigdoc.rotation_resample``).
    bilinear: bool = False


@dataclass
class PaintedOverlay:
    image: Image.Image
    dest: Tuple[int, int]
    name: str
    group: float = 1.0
    #: Drawn enlarged this many times (``rigdoc.composite_scaled_layer``).
    scale: int = 1


class PaintRecord:
    """Paint operations per canvas, in paint order. A canvas composited onto
    another brings its operations with it, so the frame a render returns holds
    the whole frame."""

    def __init__(self) -> None:
        self._ops: Dict[int, Tuple[Image.Image, list]] = {}
        #: Reduced part rasters, by the supersampled raster they came from.
        self._reduced: Dict[tuple, Tuple[Image.Image, Image.Image, Tuple[float, float]]] = {}

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

    def reduced(self, sprite: Image.Image, pivot: Tuple[float, float], factor: int, reduce: Callable):
        """``sprite`` reduced by ``factor`` with ``reduce``, the filter the
        frame is reduced with, and its pivot there (fractional)."""
        key = (id(sprite), pivot, factor)
        entry = self._reduced.get(key)
        if entry is None or entry[0] is not sprite:
            entry = (sprite,) + _reduce_part(sprite, pivot, factor, reduce)
            self._reduced[key] = entry
        return entry[1], entry[2]


def _reduce_part(sprite: Image.Image, pivot: Tuple[float, float], factor: int, reduce: Callable):
    """A supersampled part raster reduced by ``factor`` with ``reduce``, as the
    frame it is painted on is reduced: padded by the filter's reach first, so
    its edge is not cut, then trimmed to what it covers plus ``PART_BORDER``.

    ⛔ THE BORDER IS NOT WASTE. A continuous draw lands between pixels and is
    resampled, and a resampler reads past the last texel: PIL repeats the edge,
    the GPU reads the atlas neighbour. Trimmed to its alpha box, a part's
    half-covered edge row was smeared outward — the robot's sole drawn at
    alpha 82 where the render has 10 (a blob of 11, 2026-10-03)."""
    reach = 3 * factor
    w = math.ceil(sprite.width / factor) * factor + 2 * reach
    h = math.ceil(sprite.height / factor) * factor + 2 * reach
    padded = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    padded.alpha_composite(sprite, (reach, reach))
    small = reduce(padded, (w // factor, h // factor))
    x0, y0, x1, y1 = small.getchannel("A").getbbox() or (0, 0, 1, 1)
    trim = (max(0, x0 - PART_BORDER), max(0, y0 - PART_BORDER), min(small.width, x1 + PART_BORDER), min(small.height, y1 + PART_BORDER))
    return small.crop(trim), ((pivot[0] + reach) / factor - trim[0], (pivot[1] + reach) / factor - trim[1])


def _bordered(sprite: Image.Image) -> Image.Image:
    """``sprite`` inside ``PART_BORDER`` transparent texels on every side."""
    out = Image.new("RGBA", (sprite.width + 2 * PART_BORDER, sprite.height + 2 * PART_BORDER), (0, 0, 0, 0))
    out.paste(sprite, (PART_BORDER, PART_BORDER))
    return out


#: Transparent texels kept around a continuously placed part: the reach of the
#: offline bicubic resampler (2) covers the GPU's bilinear (1).
PART_BORDER = 2


@contextmanager
def recorded_paint():
    """Record every paint made through ``rigdoc``'s seams inside the block. The
    calls still paint. Yields a ``PaintRecord``."""
    from dataclasses import replace

    from . import rigdoc

    record = PaintRecord()
    names = (
        "blit_rotated",
        "composite_layer",
        "composite_scaled_layer",
        "composite_canvas",
        "downsampled_canvas",
        "mirrored_canvas",
        "faded_canvas",
    )
    originals = {name: getattr(rigdoc, name) for name in names}

    def recording_blit(canvas, sprite, pivot, world_px, delta_deg, opacity=1.0, **kwargs):
        prepared = kwargs.get("prepared")
        record._list(canvas).append(
            PaintedPart(
                sprite,
                (float(pivot[0]), float(pivot[1])),
                (float(world_px[0]), float(world_px[1])),
                float(delta_deg),
                float(opacity),
                str(kwargs.get("part_name") or "part"),
                bilinear=prepared is not None and rigdoc.rotation_resample(prepared) == Image.Resampling.BILINEAR,
            )
        )
        return originals["blit_rotated"](canvas, sprite, pivot, world_px, delta_deg, opacity, **kwargs)

    def recording_layer(canvas, layer, dest=(0, 0), *, name="overlay"):
        record._list(canvas).append(PaintedOverlay(layer, (int(dest[0]), int(dest[1])), str(name)))
        return originals["composite_layer"](canvas, layer, dest, name=name)

    def recording_scaled_layer(canvas, layer, factor, dest=(0, 0), *, name="overlay"):
        record._list(canvas).append(PaintedOverlay(layer, (int(dest[0]), int(dest[1])), str(name), scale=int(factor)))
        return originals["composite_scaled_layer"](canvas, layer, factor, dest, name=name)

    def recording_canvas(canvas, frame, dest=(0, 0)):
        dx, dy = int(dest[0]), int(dest[1])
        ops = record.ops_for(frame)
        target = record._list(canvas)
        if ops is None:
            # Painted by something this record did not see: it is still a
            # picture of the frame, so it rides as one overlay (unless it is
            # blank: a layer nothing painted this frame).
            if frame.getchannel("A").getbbox() is not None:
                target.append(PaintedOverlay(frame, (dx, dy), "composited"))
        else:
            for op in ops:
                if isinstance(op, PaintedPart):
                    target.append(replace(op, world=(op.world[0] + dx, op.world[1] + dy)))
                else:
                    target.append(replace(op, dest=(op.dest[0] + dx, op.dest[1] + dy)))
        return originals["composite_canvas"](canvas, frame, dest)

    def recording_downsample(frame, size, resample=None):
        out = originals["downsampled_canvas"](frame, size, resample)
        ops = record.ops_for(frame)
        if ops is None:
            return out

        def reduce(image, small):
            return originals["downsampled_canvas"](image, small, resample)

        factor = frame.width // size[0]
        assert frame.width == size[0] * factor and frame.height == size[1] * factor, (
            f"a {frame.size} frame reduced to {size} is not a whole supersample"
        )
        target = record._list(out)
        for op in ops:
            if isinstance(op, PaintedOverlay):
                # An effect layer on the supersampled canvas is reduced as a
                # part placed at its corner.
                assert op.scale == 1, "a scaled layer on a supersampled canvas"
                op = PaintedPart(op.image, (0.0, 0.0), (float(op.dest[0]), float(op.dest[1])), 0.0, 1.0, op.name, group=op.group)
            assert op.scale_x == 1.0 and op.exact, "a supersampled canvas is reduced once, unmirrored"
            # Where `blit_rotated` put it on the supersampled canvas: the
            # whole-pixel pivot on the whole-pixel point. Unrounded, an edge
            # lands up to a quarter of a frame pixel off at 4x (a blob of 7 on
            # robot v3's `dash_attack~mirrored`[1], 2026-10-03).
            snapped = (float(round(op.pivot[0])), float(round(op.pivot[1])))
            sprite, pivot = record.reduced(op.sprite, snapped, factor, reduce)
            target.append(
                replace(
                    op,
                    sprite=sprite,
                    pivot=pivot,
                    world=(round(op.world[0]) / factor, round(op.world[1]) / factor),
                    exact=False,
                )
            )
        return out

    def recording_mirror(frame):
        out = originals["mirrored_canvas"](frame)
        ops = record.ops_for(frame)
        if ops is None:
            return out
        width = frame.width
        target = record._list(out)
        for op in ops:
            if isinstance(op, PaintedPart):
                # Mirrored about the frame's centre: the pivot lands at
                # `width - x` (pixel edges), the part turns the other way,
                # mirrored about its own pivot.
                assert not op.exact, "a whole-pixel part is not mirrored (no rig needs it yet)"
                target.append(
                    replace(op, world=(width - op.world[0], op.world[1]), degrees=-op.degrees, scale_x=-op.scale_x)
                )
            else:
                image = op.image.transpose(Image.FLIP_LEFT_RIGHT)
                target.append(replace(op, image=image, dest=(width - op.dest[0] - image.width * op.scale, op.dest[1])))
        return out

    def recording_fade(frame, opacity):
        out = originals["faded_canvas"](frame, opacity)
        ops = record.ops_for(frame)
        if ops is None:
            return out
        target = record._list(out)
        for op in ops:
            target.append(replace(op, group=op.group * float(opacity)))
        return out

    recorders = {
        "blit_rotated": recording_blit,
        "composite_layer": recording_layer,
        "composite_scaled_layer": recording_scaled_layer,
        "composite_canvas": recording_canvas,
        "downsampled_canvas": recording_downsample,
        "mirrored_canvas": recording_mirror,
        "faded_canvas": recording_fade,
    }
    for name, fn in recorders.items():
        setattr(rigdoc, name, fn)
    try:
        yield record
    finally:
        for name, fn in originals.items():
            setattr(rigdoc, name, fn)


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
    way, its opacity linearly too); any other draw holds still. A clip that
    steps, or ``t == 0``, is the frame itself. The frame's opacity is the
    current frame's.
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
                d.opacity + (target.opacity - d.opacity) * t,
            )
        )
    return out


def _snapped_blit(
    canvas: Image.Image, image: Image.Image, pivot, at_px, degrees: float, opacity: float = 1.0, bilinear: bool = False
) -> None:
    """``blit_rotated`` at a whole-pixel pivot and point: the baked road.

    A published point is already whole. A TWEENED point is not, and is rounded
    half UP here: ``blit_rotated``'s ``round`` rounds halves to even, so two
    parts half-way between the same two places would round apart (12.5 -> 12,
    13.5 -> 14) and open a one-pixel seam between a limb and the body it hangs
    from (measured: an 11-pixel blob at t = 0.5 of Mary-O's walk)."""
    from . import rigdoc

    at_px = (math.floor(at_px[0] + 0.5), math.floor(at_px[1] + 0.5))
    resample = Image.Resampling.BILINEAR if bilinear else None
    rigdoc.blit_rotated(canvas, image, pivot, at_px, degrees, opacity, resample=resample)


#: The rows a character's flipbook tweens when its target does not say:
#: locomotion loops (decision D3 of the game's
#: `docs/planning/engine/mary-o-part-realization.md`). Every other clip steps.
LOCOMOTION_LOOPS = ("walk", "run", "crouch_walk", "climb", "swim")


def publish_rig_flipbook(
    target: str,
    rows: Sequence[Tuple[str, int, int]],
    render: Callable[[str, int, int], Image.Image],
    outputs: Mapping[str, Any],
    frame_transform: Mapping[str, int],
    out_dir: Path,
    tween_rows: Optional[Sequence[str]] = None,
    render_clip: Optional[Callable[[str, int], Sequence[Image.Image]]] = None,
) -> Dict[str, Path]:
    """Build and write the part flipbook of a rig-document target that
    ``build_sheet`` just published, and return its files.

    ``render`` is the target's ``render_fn``; ``outputs`` is what
    ``build_sheet`` returned, and ``frame_transform`` what it filled
    (``frame_transform_out``): the translation from a drawn frame to the
    published one (padding added, auto-crop removed). Each frame is drawn onto
    a canvas of the published frame through ``rigdoc.composite_canvas``, so
    the flipbook's frame, feet and draws are the sheet's. ``tween_rows``
    defaults to the rows of ``LOCOMOTION_LOOPS`` the target has.
    ``render_clip`` is for a target that renders a clip at once (a swing
    trail is drawn from the frames before it): see ``build_rig_flipbook``.
    """
    import yaml

    from . import rigdoc
    from .sheet_build import rendering_canonical_only

    # A canonical-only render (a portrait) publishes no sheet to draw, nor
    # does a build that published no sheet.
    if rendering_canonical_only() or "yaml" not in outputs:
        return {}
    sheet = yaml.safe_load(Path(outputs["yaml"]).read_text())
    size = (int(sheet["frame_width"]), int(sheet["frame_height"]))
    feet = sheet_feet(Path(outputs["yaml"]))
    dx, dy = int(frame_transform.get("dx", 0)), int(frame_transform.get("dy", 0))

    def place(frame: Image.Image) -> Image.Image:
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        rigdoc.composite_canvas(canvas, frame, (dx, dy))
        return canvas

    def published(row: str, index: int, count: int) -> Image.Image:
        return place(render(row, index, count))

    published_clip = None if render_clip is None else (lambda row, count: [place(f) for f in render_clip(row, count)])
    names = {row for row, _count, _ms in rows}
    tweened = [row for row in (LOCOMOTION_LOOPS if tween_rows is None else tween_rows) if row in names]
    flipbook = build_rig_flipbook(target, rows, published, None, feet, size, tweened, render_clip=published_clip)
    return flipbook.write(Path(out_dir))


def sheet_feet(sheet_yaml: Path) -> Tuple[float, float]:
    """The feet pixel a published sheet states (``body_metrics.feet_pixel``):
    the flipbook's origin is the sheet's own, read from what was just written
    rather than worked out a second time."""
    import yaml

    feet = yaml.safe_load(Path(sheet_yaml).read_text())["body_metrics"]["feet_pixel"]
    return (float(feet["x"]), float(feet["y"]))


def build_rig_flipbook(
    target: str,
    rows: Sequence[Tuple[str, int, int]],
    render: Callable[[str, int, int], Image.Image],
    part_rows: Optional[Sequence[str]],
    feet: Tuple[float, float],
    frame_size: Tuple[int, int],
    tween_rows: Sequence[str] = (),
    render_clip: Optional[Callable[[str, int], Sequence[Image.Image]]] = None,
) -> PartFlipbook:
    """The flipbook of a rig-document character: ``part_rows`` from parts (every
    row when ``None``), and any other row of ``rows`` left to the baked sheet.
    ``tween_rows`` are published as tweened clips (``tween_draws``); the rest
    step.

    ``render(row, index, count)`` renders one sheet frame through the
    character's ``RigDocument`` and ``rigdoc``'s seams. The canvas it returns
    must BE the published frame, so a draw's place is a frame pixel; a frame of
    another size is refused. ``feet`` is the sheet's feet pixel.

    ``render_clip(row, count)``, when given, renders a whole clip in one call
    instead, and is recorded as one pass. ⛔ For a target that composes a clip
    at once and CACHES it (a swing trail is drawn from the frames before it):
    a frame handed back from a cache filled outside the recording carries no
    record, and pass the UNCACHED function (``lru_cache``'s ``__wrapped__``).

    A rig painted at frame resolution is SNAPPED (whole-pixel places, see
    ``PartFlipbook.placement``); a supersampled rig, reduced through
    ``rigdoc.downsampled_canvas``, is CONTINUOUS. A flipbook of both is refused.

    ⛔ Each frame is drawn back from what was published and compared with the
    render: exactly for a snapped flipbook (``REPLAY_ROUNDING``), within the
    resampling bounds for a continuous one (``CONTINUOUS_REPLAY_PARITY``,
    ``CONTINUOUS_REPLAY_BLOB``). A frame that differs had something painted
    outside the seams — a post-process over the whole frame, a direct
    ``ImageDraw`` — that no draw carries, and the flipbook is refused rather
    than published without it.
    """
    known = {row for row, _count, _ms in rows}
    selected = known if part_rows is None else set(part_rows)
    unknown = sorted(selected - known)
    assert not unknown, f"part rows {unknown} are not rows of {target}"
    parts: List[PartRaster] = []
    part_index: Dict[tuple, int] = {}
    clips: Dict[str, Tuple[float, List[List[PartDraw]]]] = {}
    frame_opacity: Dict[str, List[float]] = {}
    placements = set()
    filters = set()

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
        opacities: List[float] = []
        if render_clip is not None:
            with recorded_paint() as clip_record:
                clip = list(render_clip(row, int(count)))
            assert len(clip) == int(count), f"{target} {row}: {len(clip)} frames rendered for {count}"
        for index in range(int(count)):
            if render_clip is not None:
                frame, record = clip[index], clip_record
            else:
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
            # An effect layer that paints nothing is no draw.
            ops = [op for op in ops if isinstance(op, PaintedPart) or op.image.getchannel("A").getbbox() is not None]
            # A frame fades as ONE picture or not at all: a frame opacity
            # cannot fade some draws and leave others.
            groups = {round(op.group, 6) for op in ops}
            assert len(groups) <= 1, f"{target} {row}:{index} fades its draws by {sorted(groups)}"
            opacities.append(groups.pop() if groups else 1.0)
            draws: List[PartDraw] = []
            for op in ops:
                if isinstance(op, PaintedPart):
                    sprite = op.sprite
                    if op.exact:
                        placements.add(PLACEMENT_SNAPPED)
                        if op.degrees % 360.0 != 0.0:
                            filters.add(op.bilinear)
                        # A turned part's edge fades a pixel outward. The GPU
                        # draws a part only inside its rect, so the raster
                        # carries the transparent border that fade lands on
                        # (`PART_BORDER`): without it PCA's turned outlines lost
                        # a one-pixel edge in game (blobs of 8). The pivot stays
                        # whole, so the replay is the same picture.
                        sprite = _bordered(sprite)
                        pivot = (float(round(op.pivot[0])) + PART_BORDER, float(round(op.pivot[1])) + PART_BORDER)
                        at = (float(round(op.world[0])), float(round(op.world[1])))
                    else:
                        placements.add(PLACEMENT_CONTINUOUS)
                        pivot, at = op.pivot, op.world
                    draws.append(
                        PartDraw(
                            intern("part", sprite, pivot),
                            (at[0] - feet[0], at[1] - feet[1]),
                            math.radians(op.degrees),
                            (op.scale_x, 1.0),
                            track=op.name,
                            opacity=op.opacity,
                        )
                    )
                else:
                    bbox = op.image.getchannel("A").getbbox()
                    if bbox is None:
                        continue
                    if op.scale != 1:
                        # Enlarged, so resampled: it keeps a transparent border
                        # as a reduced part does (`PART_BORDER`).
                        placements.add(PLACEMENT_CONTINUOUS)
                        bbox = (
                            max(0, bbox[0] - PART_BORDER),
                            max(0, bbox[1] - PART_BORDER),
                            min(op.image.width, bbox[2] + PART_BORDER),
                            min(op.image.height, bbox[3] + PART_BORDER),
                        )
                    left, top = op.dest[0] + bbox[0] * op.scale, op.dest[1] + bbox[1] * op.scale
                    draws.append(
                        PartDraw(
                            intern(f"{op.name}:", op.image.crop(bbox), (0.0, 0.0)),
                            (left - feet[0], top - feet[1]),
                            scale=(float(op.scale), float(op.scale)),
                            track=f"overlay:{op.name}",
                        )
                    )
            tracks = [d.track for d in draws]
            assert len(set(tracks)) == len(tracks), f"{target} {row}:{index} names a track twice: {tracks}"
            frames.append(draws)
        clips[row] = (float(duration_ms) / 1000.0, frames)
        if any(value < 1.0 for value in opacities):
            frame_opacity[row] = opacities
    assert len(placements) <= 1, f"{target} draws some parts at whole pixels and some between them"
    assert len(filters) <= 1, f"{target} turns some parts bilinear and some bicubic"
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
        placement=placements.pop() if placements else PLACEMENT_SNAPPED,
        bilinear=filters.pop() if filters else False,
        frame_opacity=frame_opacity,
    )
    for (row, index), frame in rendered.items():
        replayed = flipbook.recompose(row, index)
        if flipbook.placement == PLACEMENT_SNAPPED:
            worst = _max_channel_difference(replayed, frame)
            if worst > REPLAY_ROUNDING:
                raise AssertionError(
                    f"{target} {row}:{index}: the draws do not reproduce the render (a channel "
                    f"differs by {worst}) — something painted the frame outside rigdoc's seams"
                )
            continue
        wrong = parity(frame, replayed, **CONTINUOUS_REPLAY_TOLERANCE)
        blob = largest_wrong_blob(frame, replayed, **CONTINUOUS_REPLAY_TOLERANCE)
        if wrong > CONTINUOUS_REPLAY_PARITY or blob > CONTINUOUS_REPLAY_BLOB:
            raise AssertionError(
                f"{target} {row}:{index}: the draws do not reproduce the render ({wrong:.2%} of its "
                f"pixels wrong, a blob of {blob}) — something painted the frame outside rigdoc's seams"
            )
    return flipbook


#: How far a replayed frame may differ from its render, per 8-bit channel.
#: ``alpha_composite`` rounds each step, so it is associative only to within a
#: level a step: a body composited onto its own canvas and then over an effect
#: layer lands a level off the same parts composited straight over the layer
#: (measured: 4 pixels by 1 on Mary-O's fire `transform`; ONE pixel by 2 on
#: PCA's `special`[2] and `final_smash`[5], two translucent layers deep,
#: 2026-10-03). Anything a seam did not carry differs by far more.
REPLAY_ROUNDING = 2

#: How far a CONTINUOUS replay may differ from its render. A supersampled rig
#: composites its parts at the supersample and reduces the frame; the replay
#: reduces each part and composites them between pixels. Those differ by
#: resampling alone, a few levels on an edge, so the tolerance is in LEVELS
#: (64) and NOT in place: ``parity``'s usual pixel of slack forgives exactly a
#: part drawn one pixel off (robot v3's head moved a pixel passed it).
#: Measured on robot v3, 2026-10-03: honest frames make blobs of at most 2; a
#: visible part one pixel off makes 15 to 174.
CONTINUOUS_REPLAY_TOLERANCE = {"threshold": 64, "radius": 0}
CONTINUOUS_REPLAY_PARITY = 0.01
CONTINUOUS_REPLAY_BLOB = 6


def _max_channel_difference(a: Image.Image, b: Image.Image) -> int:
    from PIL import ImageChops

    extrema = ImageChops.difference(a.convert("RGBA"), b.convert("RGBA")).getextrema()
    return max(high for _low, high in extrema)
