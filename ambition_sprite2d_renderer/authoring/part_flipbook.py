"""The part flipbook: a character's frames as reusable part rasters plus
per-frame ordered draws, recorded while the target paints its sheet.

``recorded_paint`` watches the paint seams every target goes through:
``rigdoc``'s (a turned part, a layer, a canvas composited, reduced, mirrored
or faded) and ``core.draw.blending_draw``'s ink ops (a procedural painter's
shapes). ``build_rig_flipbook`` records each frame the target returns, and
the draws that made it become the frame's draws, in paint order; identical
rasters are one part.

Placement is the frame's own. A rig painted at frame resolution is SNAPPED to
whole pixels as ``blit_rotated`` placed it; a supersampled frame is reduced
part by part where the frame's reduction samples it (on the frame's grid, or
by a fitted scale through PIL's ``box``) and its parts are CONTINUOUS. Where
two rasters reduced apart would stack wrongly, they are merged into one.

Coordinates are the ones the published sheet uses (``publish_rig_flipbook``),
relative to the published ``feet_pixel``.

``recompose`` draws a frame back from the published atlas and draws; the
replay guard diffs every frame against the frame the target painted, and the
build fails beyond D6 (1% of pixels, a blob of 6).

A flipbook can leave rows to the baked sheet (a hybrid): ``baked_clips`` names
them, and the runtime draws them from the sheet. Each row of the sheet must be
a clip or a baked clip; the runtime refuses a flipbook that leaves a row out.
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
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

#: The roads a published character is drawn by (``PartFlipbook.realize``).
REALIZE_PARTS = "parts"
REALIZE_BAKED = "baked"

#: A clip's in-between policy. ``step`` shows each frame whole until the next;
#: ``linear`` moves each track from its place in one frame to its place in the
#: next (see ``tween_draws``). Published per clip, never chosen at runtime.
TWEEN_STEP = "step"
TWEEN_LINEAR = "linear"


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
    #: A multiply on the part's stored colour, per channel (a back limb drawn
    #: as its front limb, darker): the game's sprite colour, free. (1, 1, 1)
    #: draws the part as painted.
    tint: Tuple[float, float, float] = (1.0, 1.0, 1.0)


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
    #: The road the game draws this character by: ``"parts"``, or ``"baked"``
    #: when the parts measured costlier than the sheet
    #: (``realization_by_cost``). The flipbook is published either way.
    realize: str = REALIZE_PARTS

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
            *([f"    realize: {self.realize},"] if self.realize != REALIZE_PARTS else []),
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
                    tint = (
                        f", tint: ({num(d.tint[0])}, {num(d.tint[1])}, {num(d.tint[2])})"
                        if tuple(d.tint) != (1.0, 1.0, 1.0) else ""
                    )
                    lines.append(
                        f"                (part: {d.part}, at: {pair(d.at)}, "
                        f"rotation: {num(d.rotation)}, scale: {pair(d.scale)}{track}{opacity}{tint}),"
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
            rf"(?:, track: (\d+))?(?:, opacity: {number})?(?:, tint: \({number}, {number}, {number}\))?\)"
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
                part, ax, ay, rotation, sx, sy, track, opacity, tr, tg, tb = match.groups()
                clips[row][1][-1].append(
                    PartDraw(
                        int(part),
                        (float(ax), float(ay)),
                        float(rotation),
                        (float(sx), float(sy)),
                        tracks[int(track)] if track is not None else None,
                        float(opacity) if opacity is not None else 1.0,
                        (float(tr), float(tg), float(tb)) if tr is not None else (1.0, 1.0, 1.0),
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
            (re.search(r"realize: (\w+)", text) or [None, REALIZE_PARTS])[1],
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
        image = _tinted(self.part_image(d.part), d.tint)
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


def _tinted(image: Image.Image, tint) -> Image.Image:
    """``image`` with its colour multiplied by ``tint`` per channel, as the
    game's sprite colour multiplies a raw (sRGB) part page."""
    if tuple(tint) == (1.0, 1.0, 1.0):
        return image
    r, g, b, a = image.split()
    channels = [c.point(lambda v, k=k: min(255, int(round(v * k)))) for c, k in zip((r, g, b), tint)]
    return Image.merge("RGBA", (*channels, a))


def _faded(image: Image.Image, opacity: float) -> Image.Image:
    """``image`` with its alpha scaled by ``opacity``, as ``blit_rotated`` fades."""
    if opacity >= 1.0:
        return image
    faded = image.copy()
    faded.putalpha(image.getchannel("A").point(lambda value: int(value * opacity)))
    return faded


def wrong_pixels(
    reference: Image.Image, candidate: Image.Image, threshold: int = 64, radius: int = 1, edge: int = 0
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
    if edge:
        # A band at the frame's border is not measured (`EDGE_BAND`).
        inner = np.zeros(drawn.shape, dtype=bool)
        inner[edge:-edge, edge:-edge] = True
        drawn &= inner
    return (unmatched(ref, cand) | unmatched(cand, ref)) & drawn, drawn


def parity(
    reference: Image.Image, candidate: Image.Image, threshold: int = 64, radius: int = 1, edge: int = 0
) -> float:
    """Fraction of the frame's drawn pixels that are ``wrong_pixels``."""
    wrong, drawn = wrong_pixels(reference, candidate, threshold, radius, edge)
    return float(wrong.sum()) / max(1, int(drawn.sum()))


def largest_wrong_blob(
    reference: Image.Image, candidate: Image.Image, threshold: int = 64, radius: int = 1, edge: int = 0
) -> int:
    """Pixels in the largest 8-connected run of ``wrong_pixels``.

    ⛔ ``parity`` ALONE PASSES A MISSING EFFECT. Dropping one whole effect layer
    from a Mary-O transition frame moved ``parity`` by 1.43% on the median frame
    (measured 2026-10-02), under the old 2.5% bound and beside the anti-aliasing
    noise it is meant to forgive. Noise is scattered single pixels along edges;
    a missing star, orb or limb is one connected blob. This sees the blob.
    """
    wrong, _drawn = wrong_pixels(reference, candidate, threshold, radius, edge)
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
    #: A raster the painter put on the canvas grid as it is (a procedural
    #: shape, an effect layer): never turned, its top left at a whole canvas
    #: pixel. A supersampled canvas reduces it on the frame's own grid.
    grid: bool = False


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
        #: Shapes recorded from a procedural painter, numbering their tracks.
        self.shapes = 0
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


#: The most a premultiplied channel may move where a part's reduced edge is
#: stacked on another's (``_on_frame_grid``): half the replay tolerance.
STACKED_EDGE_LEVELS = 32


def _on_frame_grid(ops: list, factor: int, reduce: Callable) -> list:
    """The ops of a supersampled canvas, each ``grid`` raster padded so its top
    left is a whole frame pixel, and every run of grid rasters whose reduced
    edges would stack wrongly merged into one.

    Aligned, a raster reduces on the frame's own grid and lands on whole frame
    pixels: alone, it is the frame's own reduction, not a resample of one.

    ⛔ TWO EDGES REDUCED APART DO NOT STACK AS ONE. A boot and its sole share
    a bottom edge; each reduced alone is half covered there, and one half over
    another is three quarters: vera_ruin's sole drawn at alpha 200 where the
    render has 65 (a blob of 10, 2026-10-03). So each raster is checked where
    it lands: the canvas reduced with it, against the reduced rasters stacked.
    Where they differ by more than ``STACKED_EDGE_LEVELS``, it is merged with
    the rasters before it, nearest first, one paint-order run at a time, until
    they agree."""
    import numpy as np

    reach = 3 * factor

    def aligned(op):
        if isinstance(op, PaintedOverlay):
            # An effect layer on the supersampled canvas is a raster at its
            # corner: checked and reduced as one.
            assert op.scale == 1, "a scaled layer on a supersampled canvas"
            op = PaintedPart(
                op.image, (0.0, 0.0), (float(op.dest[0]), float(op.dest[1])), 0.0, 1.0, op.name, group=op.group, grid=True
            )
        if not (isinstance(op, PaintedPart) and op.grid):
            return op
        x, y = int(op.world[0]), int(op.world[1])
        ax, ay = x % factor, y % factor
        if not (ax or ay):
            return op
        sprite = Image.new("RGBA", (op.sprite.width + ax, op.sprite.height + ay), (0, 0, 0, 0))
        sprite.paste(op.sprite, (ax, ay))
        return replace(op, sprite=sprite, world=(float(x - ax), float(y - ay)))

    def box(op):
        x, y = int(op.world[0]), int(op.world[1])
        return (x, y, x + op.sprite.width, y + op.sprite.height)

    def meets(a, b):
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

    def premultiplied(image):
        array = np.asarray(image, dtype=np.int32)
        return np.concatenate([array[..., :3] * array[..., 3:4] // 255, array[..., 3:4]], axis=-1)

    reductions: Dict[int, Tuple[Any, Image.Image, Tuple[int, int]]] = {}

    def reduced_alone(op):
        """``op`` reduced on its own on the frame grid, and the frame pixel of
        its top left. Inside the reach a reduction sees only its own texels,
        so a cut of this is the op reduced inside any region."""
        entry = reductions.get(id(op))
        if entry is None or entry[0] is not op:
            x, y = int(op.world[0]), int(op.world[1])
            padded = Image.new(
                "RGBA",
                (-(-op.sprite.width // factor) * factor + 2 * reach, -(-op.sprite.height // factor) * factor + 2 * reach),
                (0, 0, 0, 0),
            )
            padded.alpha_composite(op.sprite, (reach, reach))
            small = reduce(padded, (padded.width // factor, padded.height // factor))
            entry = (op, small, ((x - reach) // factor, (y - reach) // factor))
            reductions[id(op)] = entry
        return entry[1], entry[2]

    def stack(canvas, image, dest):
        """``image`` composited with its top left at ``dest``, cut to ``canvas``."""
        dx, dy = dest
        canvas.alpha_composite(image, (max(0, dx), max(0, dy)), (max(0, -dx), max(0, -dy)))

    def disagreement(run):
        """Most a channel moves, inside the last raster's box, between the
        canvas reduced whole and its rasters reduced apart and stacked."""
        last = box(run[-1])
        x0 = last[0] // factor * factor - reach
        y0 = last[1] // factor * factor - reach
        x1 = -(-last[2] // factor) * factor + reach
        y1 = -(-last[3] // factor) * factor + reach
        region = (x0, y0, x1, y1)
        if not any(meets(box(op), region) for op in run[:-1]):
            # Alone where it lands: it reduces as the frame does there.
            return 0
        small = ((x1 - x0) // factor, (y1 - y0) // factor)
        whole = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        apart = Image.new("RGBA", small, (0, 0, 0, 0))
        for op in run:
            if not meets(box(op), region):
                continue
            stack(whole, op.sprite, (int(op.world[0]) - x0, int(op.world[1]) - y0))
            image, (sx, sy) = reduced_alone(op)
            stack(apart, image, (sx - x0 // factor, sy - y0 // factor))
        inner = (slice(3, small[1] - 3), slice(3, small[0] - 3))
        return int(np.abs(premultiplied(reduce(whole, small))[inner] - premultiplied(apart)[inner]).max(initial=0))

    def merged(run):
        x0 = min(box(op)[0] for op in run)
        y0 = min(box(op)[1] for op in run)
        canvas = Image.new("RGBA", (max(box(op)[2] for op in run) - x0, max(box(op)[3] for op in run) - y0), (0, 0, 0, 0))
        for op in run:
            alone = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            alone.paste(op.sprite, (int(op.world[0]) - x0, int(op.world[1]) - y0))
            canvas.alpha_composite(alone)
        return replace(run[0], sprite=canvas, world=(float(x0), float(y0)))

    out: list = []
    for op in ops:
        op = aligned(op)
        out.append(op)
        if not (isinstance(op, PaintedPart) and op.grid):
            continue
        # The grid rasters painted just before it, back to the first that is not.
        start = len(out) - 1
        while start > 0 and isinstance(out[start - 1], PaintedPart) and out[start - 1].grid:
            start -= 1
        while len(out) - 1 > start and disagreement(out[start:]) > STACKED_EDGE_LEVELS:
            # Within the filter's reach, not only overlapping: abutting strips
            # (a teleport's slices) share an edge too.
            b = box(out[-1])
            here = (b[0] - reach, b[1] - reach, b[2] + reach, b[3] + reach)
            under = [i for i in range(start, len(out) - 1) if meets(box(out[i]), here)]
            if not under:
                break
            out[under[-1] :] = [merged(out[under[-1] :])]
    return out


def _sampled_as_the_frame(ops: list, frame_size: Tuple[int, int], size: Tuple[int, int], resample) -> list:
    """The grid rasters of a canvas resized to ``size`` by a factor that is
    not whole (flying_spaghetti_monster_boss: 3440 to 748, 4.6x; or an
    enlargement).

    No raster can be padded onto a grid the frame repeats, so each is reduced
    over the frame pixels it reaches, sampled where the frame's own reduction
    samples them (PIL's ``box``): alone, it is that region of the frame's
    reduction, and it lands on whole frame pixels. Stacked edges are checked
    and merged as on a whole factor (``_on_frame_grid``)."""
    import numpy as np

    rx, ry = frame_size[0] / size[0], frame_size[1] / size[1]
    # The filter's reach in frame pixels: 3 when reducing; enlarging, 3
    # canvas pixels are 3 / scale frame pixels (stochastic_parrot_v2 fits a
    # reduced frame up to 1.32x).
    reach_x, reach_y = math.ceil(3 / min(1.0, rx)), math.ceil(3 / min(1.0, ry))

    def as_part(op):
        if isinstance(op, PaintedOverlay):
            assert op.scale == 1, "a scaled layer on a supersampled canvas"
            op = PaintedPart(
                op.image, (0.0, 0.0), (float(op.dest[0]), float(op.dest[1])), 0.0, 1.0, op.name, group=op.group, grid=True
            )
        assert op.grid and op.degrees == 0.0, "a turned part on a canvas resized by a factor that is not whole"
        # As an unmirrored raster at its top left: a part reduced or mirrored
        # before (a frame fitted after its reduction) carries a pivot, and a
        # mirrored one is flipped about it.
        sprite = op.sprite if op.scale_x > 0 else op.sprite.transpose(Image.FLIP_LEFT_RIGHT)
        x = op.world[0] - (op.pivot[0] if op.scale_x > 0 else op.sprite.width - op.pivot[0])
        y = op.world[1] - op.pivot[1]
        assert abs(x - round(x)) < 1e-6 and abs(y - round(y)) < 1e-6, f"a grid raster off the grid at {(x, y)}"
        return replace(op, sprite=sprite, pivot=(0.0, 0.0), world=(float(round(x)), float(round(y))), scale_x=1.0)

    def box(op):
        x, y = int(op.world[0]), int(op.world[1])
        return (x, y, x + op.sprite.width, y + op.sprite.height)

    def rect(b):
        return (
            max(0, math.floor(b[0] / rx) - reach_x),
            max(0, math.floor(b[1] / ry) - reach_y),
            min(size[0], math.ceil(b[2] / rx) + reach_x),
            min(size[1], math.ceil(b[3] / ry) + reach_y),
        )

    def sample(image, origin, r):
        """``image`` (its top left at canvas pixel ``origin``) reduced over the
        frame pixels ``r``."""
        bx0, by0 = r[0] * rx - origin[0], r[1] * ry - origin[1]
        bx1, by1 = r[2] * rx - origin[0], r[3] * ry - origin[1]
        left, top = max(0, math.ceil(-bx0)), max(0, math.ceil(-by0))
        right, bottom = max(0, math.ceil(bx1 - image.width)), max(0, math.ceil(by1 - image.height))
        if left or top or right or bottom:
            padded = Image.new("RGBA", (image.width + left + right, image.height + top + bottom), (0, 0, 0, 0))
            padded.paste(image, (left, top))
            image = padded
        return image.resize((r[2] - r[0], r[3] - r[1]), resample, box=(bx0 + left, by0 + top, bx1 + left, by1 + top))

    reductions: Dict[int, Tuple[Any, Image.Image, Tuple[int, int]]] = {}

    def reduced_alone(op):
        entry = reductions.get(id(op))
        if entry is None or entry[0] is not op:
            r = rect(box(op))
            entry = (op, sample(op.sprite, box(op)[:2], r), r[:2])
            reductions[id(op)] = entry
        return entry[1], entry[2]

    def meets(a, b):
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

    def premultiplied(image):
        array = np.asarray(image, dtype=np.int32)
        return np.concatenate([array[..., :3] * array[..., 3:4] // 255, array[..., 3:4]], axis=-1)

    def stack(canvas, image, dest):
        dx, dy = dest
        canvas.alpha_composite(image, (max(0, dx), max(0, dy)), (max(0, -dx), max(0, -dy)))

    def disagreement(run):
        r = rect(box(run[-1]))
        x0, y0 = math.floor(r[0] * rx), math.floor(r[1] * ry)
        region = (x0, y0, math.ceil(r[2] * rx), math.ceil(r[3] * ry))
        if not any(meets(box(op), region) for op in run[:-1]):
            return 0
        whole = Image.new("RGBA", (region[2] - x0, region[3] - y0), (0, 0, 0, 0))
        apart = Image.new("RGBA", (r[2] - r[0], r[3] - r[1]), (0, 0, 0, 0))
        for op in run:
            if not meets(box(op), region):
                continue
            stack(whole, op.sprite, (int(op.world[0]) - x0, int(op.world[1]) - y0))
            image, (sx, sy) = reduced_alone(op)
            stack(apart, image, (sx - r[0], sy - r[1]))
        inner = (slice(reach_y, apart.height - reach_y), slice(reach_x, apart.width - reach_x))
        joint = premultiplied(sample(whole, (x0, y0), r))
        return int(np.abs(joint[inner] - premultiplied(apart)[inner]).max(initial=0))

    def merged(run):
        x0, y0 = min(box(op)[0] for op in run), min(box(op)[1] for op in run)
        canvas = Image.new("RGBA", (max(box(op)[2] for op in run) - x0, max(box(op)[3] for op in run) - y0), (0, 0, 0, 0))
        for op in run:
            stack(canvas, op.sprite, (int(op.world[0]) - x0, int(op.world[1]) - y0))
        return replace(run[0], sprite=canvas, world=(float(x0), float(y0)))

    out: list = []
    for op in ops:
        out.append(as_part(op))
        while len(out) > 1 and disagreement(out) > STACKED_EDGE_LEVELS:
            b = box(out[-1])
            here = (b[0] - math.ceil(reach_x * rx), b[1] - math.ceil(reach_y * ry), b[2] + math.ceil(reach_x * rx), b[3] + math.ceil(reach_y * ry))
            under = [i for i in range(len(out) - 1) if meets(box(out[i]), here)]
            if not under:
                break
            out[under[-1] :] = [merged(out[under[-1] :])]
    parts = []
    for op in out:
        small, (sx, sy) = reduced_alone(op)
        x0, y0, x1, y1 = small.getchannel("A").getbbox() or (0, 0, 1, 1)
        trim = (max(0, x0 - PART_BORDER), max(0, y0 - PART_BORDER), min(small.width, x1 + PART_BORDER), min(small.height, y1 + PART_BORDER))
        parts.append(
            replace(op, sprite=small.crop(trim), pivot=(0.0, 0.0), world=(float(sx + trim[0]), float(sy + trim[1])), exact=False)
        )
    return parts


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

    def unique(target, op):
        """``op`` named apart from every draw already on ``target``: a track
        is named once a frame, so a second "composited" is "composited2"."""
        names = {draw.name for draw in target}
        if op.name not in names:
            return op
        count = 2
        while f"{op.name}{count}" in names:
            count += 1
        return replace(op, name=f"{op.name}{count}")

    def recording_layer(canvas, layer, dest=(0, 0), *, name="overlay"):
        target = record._list(canvas)
        target.append(unique(target, PaintedOverlay(layer, (int(dest[0]), int(dest[1])), str(name))))
        return originals["composite_layer"](canvas, layer, dest, name=name)

    def recording_scaled_layer(canvas, layer, factor, dest=(0, 0), *, name="overlay"):
        target = record._list(canvas)
        target.append(unique(target, PaintedOverlay(layer, (int(dest[0]), int(dest[1])), str(name), scale=int(factor))))
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
                target.append(unique(target, PaintedOverlay(frame, (dx, dy), "composited")))
        else:
            for op in ops:
                if isinstance(op, PaintedPart):
                    target.append(unique(target, replace(op, world=(op.world[0] + dx, op.world[1] + dy))))
                else:
                    target.append(unique(target, replace(op, dest=(op.dest[0] + dx, op.dest[1] + dy))))
        return originals["composite_canvas"](canvas, frame, dest)

    def recording_downsample(frame, size, resample=None):
        out = originals["downsampled_canvas"](frame, size, resample)
        ops = record.ops_for(frame)
        if ops is None:
            return out

        def reduce(image, small):
            return originals["downsampled_canvas"](image, small, resample)

        factor = frame.width // size[0]
        target = record._list(out)
        whole = frame.width == size[0] * factor and frame.height == size[1] * factor
        # A frame resized again (a quality tier of a reduced frame) holds
        # rasters already reduced: they are sampled where this resize samples.
        reduced_before = any(isinstance(op, PaintedPart) and not op.exact for op in ops)
        if not whole or reduced_before:
            assert resample is not None, f"a {frame.size} frame reduced to {size} is not a whole supersample of its parts"
            target.extend(_sampled_as_the_frame(ops, frame.size, size, resample))
            return out
        for op in _on_frame_grid(ops, factor, reduce):
            if isinstance(op, PaintedOverlay):
                # An effect layer on the supersampled canvas is reduced as a
                # part placed at its corner.
                assert op.scale == 1, "a scaled layer on a supersampled canvas"
                op = PaintedPart(
                    op.image, (0.0, 0.0), (float(op.dest[0]), float(op.dest[1])), 0.0, 1.0, op.name, group=op.group, grid=True
                )
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

    from ..core import draw as core_draw

    def cut_out(ops, image, hole):
        """``hole`` (an L mask of ``image``) cut out of every shape on it."""
        cut_ops = []
        for index, op in enumerate(ops):
            if isinstance(op, PaintedOverlay):
                # A layer composited as it is (a turned card) is cut the same way.
                assert op.scale == 1, "an eraser over an enlarged layer"
                raster, (x0, y0) = op.image, (int(op.dest[0]), int(op.dest[1]))
            else:
                raster = op.sprite
                x0, y0 = int(op.world[0] - op.pivot[0]), int(op.world[1] - op.pivot[1])
            cut = hole.crop((x0, y0, x0 + raster.width, y0 + raster.height))
            if cut.getbbox() is None:
                continue
            assert isinstance(op, PaintedOverlay) or (op.exact and op.degrees == 0.0 and op.scale_x == 1.0), (
                "an eraser over a turned part"
            )
            raster = raster.copy()
            raster.putalpha(Image.composite(Image.new("L", raster.size, 0), raster.getchannel("A"), cut))
            ops[index] = replace(op, image=raster) if isinstance(op, PaintedOverlay) else replace(op, sprite=raster)
            cut_ops.append(index)
        if len(cut_ops) > 1:
            # ⛔ The shapes a hole cuts now share its edge. Reduced one by
            # one and stacked, that edge's partial alpha compounds (two
            # 50% edges make 75%): the hole fills in. Measured on
            # hypatia_prime's phone, a 14-pixel blob. They become one
            # shape, every op from the first cut to the last, in order.
            first, last = cut_ops[0], cut_ops[-1]
            run = ops[first : last + 1]
            if any(not isinstance(op, PaintedOverlay) and not (op.exact and op.degrees == 0.0) for op in run):
                # A turned part between them keeps its own place; the conflict
                # check after the reduction still sees their edges.
                return
            merged = Image.new("RGBA", image.size, (0, 0, 0, 0))
            for op in run:
                if isinstance(op, PaintedOverlay):
                    raster, place = op.image, (int(op.dest[0]), int(op.dest[1]))
                else:
                    raster, place = op.sprite, (int(op.world[0] - op.pivot[0]), int(op.world[1] - op.pivot[1]))
                layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
                layer.paste(raster, place)
                merged.alpha_composite(layer)
            box = merged.getbbox()
            assert len({op.group for op in run}) == 1, "merging draws of different frame opacities"
            ops[first : last + 1] = (
                []
                if box is None
                else [
                    PaintedPart(
                        merged.crop(box), (0.0, 0.0), (float(box[0]), float(box[1])), 0.0, 1.0, run[0].name,
                        group=run[0].group, grid=True,
                    )
                ]
            )

    def recording_shape(image, name, args, kwargs, erases, painted=None, before=None):
        """One ink op of a procedural painter (``blending_draw``): the shape it
        painted, as a part at its box on the supersampled canvas. An op that
        ERASES (an alpha-0 ink drawn directly) cuts its coverage out of every
        shape already on the canvas, which is exactly what it did to them.

        An op drawn straight through (``text``) REPLACES what it covers, at
        any alpha: its stroke may be clear, its fill translucent. Given the
        canvas ``before`` it, the pixels it changed are cut out of every shape
        and are the new shape, as they now are."""
        ops = record._list(image)
        core_draw.SHAPE_RECORDER = None
        try:
            if before is not None:
                import numpy as np

                changed = (np.asarray(before) != np.asarray(image)).any(axis=-1)
                hole = Image.fromarray(changed.astype(np.uint8) * 255)
                cut_out(ops, image, hole)
                painted = Image.new("RGBA", image.size, (0, 0, 0, 0))
                painted.paste(image, (0, 0), hole)
            elif erases:
                def clear(ink):
                    return isinstance(ink, (tuple, list)) and len(ink) >= 4 and int(ink[3]) == 0

                def as_mask(ink):
                    return (255, 255, 255, 255) if clear(ink) else (0, 0, 0, 0)

                masked_args = list(args)
                if len(masked_args) > 1 and name in core_draw._BlendingDraw._POS_FILL:
                    masked_args[1] = as_mask(masked_args[1])
                masked_kwargs = {k: (as_mask(v) if k in ("fill", "outline") else v) for k, v in kwargs.items()}
                coverage = Image.new("RGBA", image.size, (0, 0, 0, 0))
                getattr(core_draw._BlendingDraw(coverage), name)(*masked_args, **masked_kwargs)
                cut_out(ops, image, coverage.getchannel("A"))
            if painted is None:
                painted = Image.new("RGBA", image.size, (0, 0, 0, 0))
                getattr(core_draw._BlendingDraw(painted), name)(*args, **kwargs)
        finally:
            core_draw.SHAPE_RECORDER = recording_shape
        box = painted.getbbox()
        if box is not None:
            record.shapes += 1
            ops.append(
                PaintedPart(
                    painted.crop(box), (0.0, 0.0), (float(box[0]), float(box[1])), 0.0, 1.0, f"shape{record.shapes}", grid=True
                )
            )

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
    core_draw.SHAPE_RECORDER = recording_shape
    try:
        yield record
    finally:
        core_draw.SHAPE_RECORDER = None
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
                tuple(a + (b - a) * t for a, b in zip(d.tint, target.tint)),
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
    from .sheet_build import rendering_canonical_only, rendering_quality_tier

    # A canonical-only render (a portrait) publishes no sheet to draw, nor
    # does a build that published no sheet. A quality tier's flipbook is
    # derived from this one (`generate_visual_quality_variants.py`).
    if rendering_canonical_only() or rendering_quality_tier() or "yaml" not in outputs:
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
    return write_with_realization(flipbook, Path(outputs["yaml"]), Path(out_dir))


def write_with_realization(flipbook: "PartFlipbook", sheet_yaml: Path, out_dir: Path) -> Dict[str, Path]:
    """Write ``flipbook`` with its road decided by ``realization_by_cost``."""
    flipbook.pack()
    flipbook.realize, reason = realization_by_cost(flipbook, sheet_yaml)
    print(f"[part flipbook] {flipbook.target}: realize {flipbook.realize} ({reason})", flush=True)
    return flipbook.write(out_dir)


#: The most draws a frame drawn from parts may take: a body's draws are
#: composited every frame it is visible, and the hall shows dozens at once. The
#: rigs measured 16 to 35 (2026-10-03); a procedural painter recorded shape by
#: shape reached 140.
REALIZE_MAX_DRAWS = 64


def realization_by_cost(flipbook: "PartFlipbook", sheet_yaml: Path) -> Tuple[str, str]:
    """``(road, reason)``: parts unless they measure costlier than the baked
    sheet: more texels on their pages than the sheet's pages, or a frame over
    ``REALIZE_MAX_DRAWS`` draws. ``pack`` first."""
    import yaml

    sheet = yaml.safe_load(Path(sheet_yaml).read_text())
    names = sheet.get("images") or [sheet.get("image", Path(sheet_yaml).name.replace(".yaml", ".png"))]
    sheet_texels = 0
    for name in names:
        with Image.open(Path(sheet_yaml).parent / name) as image:
            sheet_texels += image.width * image.height
    part_texels = flipbook.packed_texels()
    most = max((len(draws) for _d, frames in flipbook.clips.values() for draws in frames), default=0)
    if part_texels > sheet_texels:
        return REALIZE_BAKED, f"part pages {part_texels} texels > sheet {sheet_texels}"
    if most > REALIZE_MAX_DRAWS:
        return REALIZE_BAKED, f"{most} draws in a frame > {REALIZE_MAX_DRAWS}"
    return REALIZE_PARTS, f"part pages {part_texels} <= sheet {sheet_texels}, at most {most} draws"


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
    # Lossless sharing FIRST, then the rigid merge, then sharing again (a
    # composite can be another's mirror). Merged first, two mirrored quarters
    # of a slash ring fused into a new half-ring raster and the robot's pages
    # GREW (166k -> 176k texels, 2026-10-04).
    for step, name in ((_share_transformed_parts, "transform sharing"), (_merge_rigid_neighbours, "rigid merge"),
                       (_share_transformed_parts, "transform sharing")):
        changed = step(flipbook)
        if changed is not flipbook:
            failing = _replay_failures(changed, rendered)
            if failing:
                print(f"[part flipbook] {target}: {name} refused, {len(failing)} frame(s) would change ({failing[0]})", flush=True)
            else:
                flipbook = changed
    # Near twins (a texel over, a shade darker), each kept only where every
    # frame still replays (`_share_near_parts`).
    distinct = frozenset(DISTINCT_TRACKS.get(target, ()))
    flipbook = _share_near_parts(flipbook, rendered, distinct)
    # Then each part that is its own mirror, stored as half (`_split_symmetric_parts`).
    flipbook = _split_symmetric_parts(flipbook, rendered, distinct)
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


def _replay_failures(flipbook: "PartFlipbook", rendered: Mapping[Tuple[str, int], Image.Image]) -> List[str]:
    """The frames ``flipbook`` does not redraw within the replay guard's bounds."""
    failing = []
    for (row, index), frame in rendered.items():
        replayed = flipbook.recompose(row, index)
        if flipbook.placement == PLACEMENT_SNAPPED:
            if _max_channel_difference(replayed, frame) > REPLAY_ROUNDING:
                failing.append(f"{row}:{index}")
            continue
        if (
            parity(frame, replayed, **CONTINUOUS_REPLAY_TOLERANCE) > CONTINUOUS_REPLAY_PARITY
            or largest_wrong_blob(frame, replayed, **CONTINUOUS_REPLAY_TOLERANCE) > CONTINUOUS_REPLAY_BLOB
        ):
            failing.append(f"{row}:{index}")
    return failing


def _merge_rigid_neighbours(flipbook: "PartFlipbook") -> "PartFlipbook":
    """``flipbook`` with every always-rigid pair of neighbouring draws made one
    draw of one composited part, or ``flipbook`` itself when there is none.

    A pair is the draw of track A and the draw right after it, of track B, when
    in EVERY frame that draws A: B follows it, nothing else is painted between
    them (they are consecutive), and B sits at the same place in A's frame —
    the same turn, scale and opacity, at the same offset. Carl Stargan's hair
    rides his head like that. Composited once offline, the pair is one draw a
    frame instead of two (Jon, 2026-10-03: "parts that are always rigid don't
    need to be composed").

    Kept exact: the two rasters are composited at a whole texel of each other
    (no resample), and a snapped flipbook merges only pairs that never turn
    (a snapped part is turned on its own at frame resolution). Merging repeats,
    so a chain of rigid pieces becomes one part. The caller replays every
    frame and keeps the unmerged flipbook if any frame changes.
    """
    from dataclasses import replace as _replace

    def relation(a: PartDraw, b: PartDraw):
        c, s_ = math.cos(-a.rotation), math.sin(-a.rotation)
        dx, dy = b.at[0] - a.at[0], b.at[1] - a.at[1]
        return (
            round(b.rotation - a.rotation, 6),
            round(c * dx - s_ * dy, 3),
            round(s_ * dx + c * dy, 3),
            a.scale,
            b.scale,
            round(a.opacity, 4),
            round(b.opacity, 4),
        )

    parts = list(flipbook.parts)
    index = {(p.image.size, p.pivot, p.image.tobytes()): i for i, p in enumerate(parts)}
    composites: Dict[Tuple[int, int, Tuple[float, float]], Optional[int]] = {}

    def composite(a_part: int, b_part: int, offset: Tuple[float, float]) -> Optional[int]:
        """Part ``b`` drawn at ``offset`` (pivot to pivot, in ``a``'s frame,
        unturned) over part ``a``, as one part with ``a``'s pivot; ``None``
        when ``b`` lands between texels."""
        key = (a_part, b_part, offset)
        if key in composites:
            return composites[key]
        a, b = parts[a_part], parts[b_part]
        bx = a.pivot[0] + offset[0] - b.pivot[0]
        by = a.pivot[1] + offset[1] - b.pivot[1]
        if abs(bx - round(bx)) > 1e-3 or abs(by - round(by)) > 1e-3:
            composites[key] = None
            return None
        bx, by = int(round(bx)), int(round(by))
        x0, y0 = min(0, bx), min(0, by)
        x1, y1 = max(a.image.width, bx + b.image.width), max(a.image.height, by + b.image.height)
        image = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        image.alpha_composite(a.image, (-x0, -y0))
        image.alpha_composite(b.image, (bx - x0, by - y0))
        pivot = (a.pivot[0] - x0, a.pivot[1] - y0)
        found = index.get((image.size, pivot, image.tobytes()))
        if found is None:
            found = len(parts)
            parts.append(PartRaster(f"{a.name}+{b.name}", image, pivot))
            index[(image.size, pivot, image.tobytes())] = found
        composites[key] = found
        return found

    def candidates(clips) -> Dict[str, Tuple[str, tuple]]:
        follows: Dict[Optional[str], set] = {}
        for _duration, frames in clips.values():
            for draws in frames:
                for i, d in enumerate(draws):
                    nxt = draws[i + 1] if i + 1 < len(draws) else None
                    follows.setdefault(d.track, set()).add(None if nxt is None else (nxt.track, relation(d, nxt)))
        # ⛔ The SAME turn, not a constant difference: `composite` pastes the
        # second raster unturned, so a pair turned apart (Sanic's quills) would
        # replay wrong and the guard would refuse every merge with it.
        rigid = {
            a: next(iter(after))
            for a, after in follows.items()
            if a is not None
            and len(after) == 1
            and None not in after
            and next(iter(after))[0] not in (None, a)
            and next(iter(after))[1][0] == 0.0
            # ⛔ Unscaled, both: `composite` pastes rasters as stored, so a
            # mirrored draw (lossless sharing) would be pasted unmirrored.
            and next(iter(after))[1][3] == (1.0, 1.0)
            and next(iter(after))[1][4] == (1.0, 1.0)
        }
        if flipbook.placement == PLACEMENT_SNAPPED:
            turning = {d.track for _d, frames in clips.values() for draws in frames for d in draws if d.rotation != 0.0}
            rigid = {a: rb for a, rb in rigid.items() if a not in turning and rb[0] not in turning}
        return rigid

    def merged_pair(clips, a: str, b: str, rel: tuple):
        out_clips = {}
        progress = False
        for row, (duration, frames) in clips.items():
            new_frames = []
            for draws in frames:
                out: List[PartDraw] = []
                i = 0
                while i < len(draws):
                    d = draws[i]
                    if d.track == a and i + 1 < len(draws) and draws[i + 1].track == b:
                        joined = composite(d.part, draws[i + 1].part, (rel[1], rel[2]))
                        if joined is not None:
                            out.append(_replace(d, part=joined, track=f"{a}+{b}"))
                            i += 2
                            progress = True
                            continue
                    out.append(d)
                    i += 1
                new_frames.append(out)
            out_clips[row] = (duration, new_frames)
        return out_clips if progress else None

    def texels(clips) -> int:
        used = {d.part for _d, frames in clips.values() for draws in frames for d in draws}
        return sum(parts[i].image.width * parts[i].image.height for i in used)

    # ⛔ A COMPOSITE DUPLICATES PIXELS when its pieces are still drawn apart
    # elsewhere (Mary-O's part pages grew past their ceiling, 2026-10-03). A
    # pair is merged only when the parts it leaves drawn hold no more texels
    # than before (none: slack compounds over many pairs): fewer draws, never
    # more memory.
    clips = {row: (duration, [list(draws) for draws in frames]) for row, (duration, frames) in flipbook.clips.items()}
    changed = False
    while True:
        progress = False
        for a, (b, rel) in candidates(clips).items():
            trial = merged_pair(clips, a, b, rel)
            if trial is not None and texels(trial) <= texels(clips):
                clips, progress, changed = trial, True, True
        if not progress:
            break
    if not changed:
        return flipbook
    used = sorted({d.part for _d, frames in clips.values() for draws in frames for d in draws})
    remap = {old: new for new, old in enumerate(used)}
    clips = {
        row: (duration, [[_replace(d, part=remap[d.part]) for d in draws] for draws in frames])
        for row, (duration, frames) in clips.items()
    }
    return _replace(flipbook, parts=[parts[i] for i in used], clips=clips, rects=[], pages=[])


#: The lossless transforms of a raster (PIL transpose ops): the linear part
#: ``L`` of the map of a continuous point of the source onto the transposed
#: raster, ``q = L p + t`` (+y down). ``t`` is ``_lossless_map``'s.
_LOSSLESS = {
    Image.Transpose.FLIP_LEFT_RIGHT: (-1, 0, 0, 1),
    Image.Transpose.FLIP_TOP_BOTTOM: (1, 0, 0, -1),
    Image.Transpose.ROTATE_180: (-1, 0, 0, -1),
    Image.Transpose.ROTATE_90: (0, 1, -1, 0),
    Image.Transpose.ROTATE_270: (0, -1, 1, 0),
    Image.Transpose.TRANSPOSE: (0, 1, 1, 0),
    Image.Transpose.TRANSVERSE: (0, -1, -1, 0),
}


def _lossless_map(op, size: Tuple[int, int]):
    """``(L, t)`` of ``op`` on a raster of ``size``: a continuous source point
    ``p`` lands at ``L p + t`` in the transposed raster. ``t`` moves the
    transformed box back onto the origin. ``None`` is the identity (the same
    pixels at another pivot)."""
    if op is None:
        return (1, 0, 0, 1), (0.0, 0.0)
    a, b, c, d = _LOSSLESS[op]
    w, h = size
    corners = [(a * x + b * y, c * x + d * y) for x in (0, w) for y in (0, h)]
    return (a, b, c, d), (-min(x for x, _ in corners), -min(y for _, y in corners))


def _share_transformed_parts(flipbook: "PartFlipbook") -> "PartFlipbook":
    """``flipbook`` with every part whose pixels are another part's mirrored or
    turned a quarter (a lossless transform) drawn as that part with the
    transform on its draw; ``flipbook`` itself when there is none.

    Jon, 2026-10-04: anything a zero-cost flip or quarter turn reproduces with
    no visual loss is ONE source with a transform on top. A raster equal to a
    transpose of an earlier one is dropped; each draw of it draws the earlier
    raster with ``M = R S L`` (its own turn and scale, then the transform),
    split back into a turn and a signed scale. Compared trimmed to the drawn
    extent, so padding and pivot do not hide a match. A snapped flipbook is
    left alone (its draws are never scaled).

    ⛔ In a tweened clip, two frames of a track that drew DIFFERENT parts held
    still between them; sharing could make them one part and start an
    interpolation through a flip (scale -1 to 1 squashes through zero). Such a
    part is not shared.
    """
    if flipbook.placement == PLACEMENT_SNAPPED:
        return flipbook
    parts = list(flipbook.parts)
    seen: Dict[Tuple[Tuple[int, int], bytes], int] = {}
    source_of: Dict[int, tuple] = {}
    for i, part in enumerate(parts):
        crop, _box = _trimmed(part.image)
        key = (crop.size, crop.tobytes())
        if key in seen:
            # The same pixels at another pivot or padding: the recorder keys
            # a part by its pivot too, so these slip past it (18% of the player
            # robot's texels after its effects became pieces, 2026-10-04).
            source_of[i] = (seen[key], None, (0, 0), (1.0, 1.0, 1.0))
            continue
        for op in _LOSSLESS:
            turned = crop.transpose(op)
            match = seen.get((turned.size, turned.tobytes()))
            if match is not None:
                # op(part i) is part match, so part i is the INVERSE of op
                # applied to part match (only the quarter turns differ).
                inverse = {Image.Transpose.ROTATE_90: Image.Transpose.ROTATE_270,
                           Image.Transpose.ROTATE_270: Image.Transpose.ROTATE_90}.get(op, op)
                source_of[i] = (match, inverse, (0, 0), (1.0, 1.0, 1.0))
                break
        else:
            seen[key] = i
    return _drawn_from_sources(flipbook, source_of)


def _trimmed(image: Image.Image):
    """``image`` cut to its drawn extent, and that box."""
    box = image.getchannel("A").getbbox() or (0, 0, 1, 1)
    return image.crop(box), box


def _drawn_from_sources(flipbook: "PartFlipbook", source_of: Dict[int, tuple]) -> "PartFlipbook":
    """``flipbook`` with each part ``r`` in ``source_of`` drawn from its source
    instead: ``source_of[r] = (src, op, (dx, dy), tint)`` says r's drawn extent
    is ``op`` applied to src's (``None``: as is), lying ``(dx, dy)`` texels into
    it, in src's colours multiplied by ``tint``. ``flipbook`` itself when none
    survives the tween guard.

    Each draw of r draws src with ``M = R S L`` (its own turn and scale, then
    the transform), split back into a turn and a signed scale, and its tint
    multiplied by the source's.

    ⛔ In a tweened clip, two frames of a track that drew DIFFERENT parts held
    still between them; sharing could make them one part and start an
    interpolation through a flip (scale -1 to 1 squashes through zero). Such a
    part is not shared.
    """
    from dataclasses import replace as _replace

    parts = list(flipbook.parts)
    source_of = dict(source_of)

    def redraw(d: PartDraw) -> PartDraw:
        src, op, offset, tint = source_of[d.part]
        return _redrawn(d, parts[d.part], parts[src], src, op, offset, tint)

    def shared_clips(sources):
        return {
            row: (duration, [[redraw(d) if d.part in sources else d for d in draws] for draws in frames])
            for row, (duration, frames) in flipbook.clips.items()
        }

    clips = flipbook.clips
    while source_of:
        clips = shared_clips(source_of)
        refused = set()
        for row, (_duration, frames) in flipbook.clips.items():
            if flipbook.tweens.get(row) != TWEEN_LINEAR:
                continue
            new_frames = clips[row][1]
            for index, draws in enumerate(frames):
                nxt = (index + 1) % len(frames)
                before = {d.track: d.part for d in frames[nxt] if d.track is not None}
                after = {d.track: d.part for d in new_frames[nxt] if d.track is not None}
                for old, new in zip(draws, new_frames[index]):
                    if old.track in before and before[old.track] != old.part and after[old.track] == new.part:
                        refused.update(p for p in (old.part, before[old.track]) if p in source_of)
        if not refused:
            break
        for part in refused:
            source_of.pop(part)
    if not source_of:
        return flipbook
    used = sorted({d.part for _d, frames in clips.values() for draws in frames for d in draws})
    remap = {old: new for new, old in enumerate(used)}
    clips = {
        row: (duration, [[_replace(d, part=remap[d.part]) for d in draws] for draws in frames])
        for row, (duration, frames) in clips.items()
    }
    return _replace(flipbook, parts=[parts[i] for i in used], clips=clips, rects=[], pages=[])


def _redrawn(d: PartDraw, r_img: PartRaster, p_img: PartRaster, src: int, op, offset, tint) -> PartDraw:
    """Draw ``d`` (of the part ``r_img``) as the part ``src`` (``p_img``): r's
    drawn extent is ``op`` applied to p's, lying ``offset`` texels into r's, in
    p's colours times ``tint`` (``_drawn_from_sources``)."""
    from dataclasses import replace as _replace

    ox, oy = offset
    p_crop, p_box = _trimmed(p_img.image)
    _r_crop, r_box = _trimmed(r_img.image)
    (la, lb, lc, ld), (tx, ty) = _lossless_map(op, p_crop.size)
    # A point of P (its own pixels) in R's pixels:
    #   q = L (p - p_box0) + t + offset + r_box0.
    # R's pivot r comes from P's point p_r = L^-1 (r - r_box0 - offset - t) + p_box0.
    rx, ry = r_img.pivot[0] - r_box[0] - ox - tx, r_img.pivot[1] - r_box[1] - oy - ty
    det = la * ld - lb * lc
    ix, iy = (ld * rx - lb * ry) / det + p_box[0], (-lc * rx + la * ry) / det + p_box[1]
    c, s = math.cos(d.rotation), math.sin(d.rotation)
    # M = R S L.
    rs = (c * d.scale[0], -s * d.scale[1], s * d.scale[0], c * d.scale[1])
    m = (
        rs[0] * la + rs[1] * lc, rs[0] * lb + rs[1] * ld,
        rs[2] * la + rs[3] * lc, rs[2] * lb + rs[3] * ld,
    )
    # P's own pivot lands where R's draw put the point ix, iy.
    dx, dy = p_img.pivot[0] - ix, p_img.pivot[1] - iy
    at = (d.at[0] + m[0] * dx + m[1] * dy, d.at[1] + m[2] * dx + m[3] * dy)
    tinted = tuple(round(a * b, 4) for a, b in zip(d.tint, tint))
    if op is None:
        # The same pixels at another place: only the draw's place (and
        # colour) moves (recomposed, its turn and scale would come back a
        # float off).
        return _replace(d, part=src, at=at, tint=tinted)
    # Split M = R(theta) diag(sx, sy): the first column is sx times the
    # turn's first column.
    sx = math.hypot(m[0], m[2])
    theta = math.atan2(m[2], m[0])
    ct, st = math.cos(theta), math.sin(theta)
    sy = -st * m[1] + ct * m[3]
    assert abs(ct * m[1] + st * m[3]) < 1e-6, "a lossless transform keeps the axes square"
    # A lossless transform of a draw scaled by +-1 is scaled by exactly +-1
    # (the published table writes what it is given; a 0.9999999 would not
    # read back as written).
    sx, sy = (round(v) if abs(abs(v) - 1.0) < 1e-9 else v for v in (sx, sy))
    return _replace(d, part=src, at=at, rotation=theta, scale=(sx, sy), tint=tinted)


#: A near twin's covered pixels whose alpha may differ by more than 48 levels
#: (an anti-aliased edge one texel over), as a share. These gates only NOMINATE
#: a twin; the replay guard decides (`_withdrawn_until_replayed`). Sybil's limbs,
#: painted a fraction of a pixel off centre, are their own mirrors to 2.3% and
#: an RMS of 6.7 and were never nominated at 2% and 6 (2026-10-04).
NEAR_ALPHA_MISMATCH = 0.04
#: A near twin's colour residual after its tint, RMS over pixels both draw
#: opaque, in levels; and the 99th percentile, so a missing eye or seam (a
#: local difference) is not averaged away.
NEAR_RMS = 10.0
NEAR_P99 = 32.0
#: A tint brighter than this is not a tint: the source is the brighter twin.
NEAR_MAX_TINT = 1.02

#: target -> track names whose parts are never drawn from a near twin: the
#: author's way to keep two parts apart that the tolerance would join (a left
#: glove a shade off on purpose). Art that diverges beyond the tolerance is
#: kept apart without asking. ``keep_distinct`` registers.
DISTINCT_TRACKS: Dict[str, set] = {}


def keep_distinct(target: str, *tracks: str) -> None:
    """Keep the parts of ``tracks`` of ``target`` their own rasters: never drawn
    from a near twin (mirror, quarter turn, shade), however close they come.
    Call at the character module's import."""
    DISTINCT_TRACKS.setdefault(target, set()).update(tracks)


def _near_sources(flipbook: "PartFlipbook", distinct=frozenset()) -> Dict[int, tuple]:
    """Each part that is, within the tolerance, a lossless transform of a
    brighter part shifted at most a texel, in that part's colours times a tint:
    ``{part: (src, op, (dx, dy), tint)}``. Parts drawn by a ``distinct`` track
    are never drawn from another."""
    import numpy as np

    parts = flipbook.parts
    tracks_of: Dict[int, set] = {}
    for _duration, frames in flipbook.clips.values():
        for draws in frames:
            for d in draws:
                tracks_of.setdefault(d.part, set()).add(d.track)
    crops = [_trimmed(p.image)[0] for p in parts]
    arrays = [np.asarray(c, dtype=np.float32) for c in crops]

    def brightness(i):
        a = arrays[i]
        w = a[..., 3]
        return float((a[..., :3].mean(-1) * w).sum() / max(1.0, w.sum()))

    order = sorted(range(len(parts)), key=lambda i: (-brightness(i), i))
    kept: List[int] = []
    by_size: Dict[Tuple[int, int], List[int]] = {}
    found: Dict[int, tuple] = {}

    def compare(src: int, op, target: int):
        """(dx, dy, tint, score) of the best alignment, or None."""
        p = crops[src] if op is None else crops[src].transpose(op)
        pa, ra = np.asarray(p, dtype=np.float32), arrays[target]
        h, w = max(pa.shape[0], ra.shape[0]) + 2, max(pa.shape[1], ra.shape[1]) + 2
        r_canvas = np.zeros((h, w, 4), np.float32)
        r_canvas[1:1 + ra.shape[0], 1:1 + ra.shape[1]] = ra
        best = None
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                p_canvas = np.zeros((h, w, 4), np.float32)
                y0, x0 = 1 - dy, 1 - dx
                if y0 + pa.shape[0] > h or x0 + pa.shape[1] > w:
                    continue
                p_canvas[y0:y0 + pa.shape[0], x0:x0 + pa.shape[1]] = pa
                covered = (p_canvas[..., 3] > 0) | (r_canvas[..., 3] > 0)
                count = int(covered.sum())
                if count < 16:
                    continue
                mismatch = float((np.abs(p_canvas[..., 3] - r_canvas[..., 3]) > 48)[covered].mean())
                if mismatch > NEAR_ALPHA_MISMATCH:
                    continue
                both = (p_canvas[..., 3] > 200) & (r_canvas[..., 3] > 200)
                if both.sum() < 8:
                    continue
                s, t_ = p_canvas[..., :3][both], r_canvas[..., :3][both]
                ident = np.abs(t_ - s)
                if np.sqrt((ident ** 2).mean()) <= NEAR_RMS and np.percentile(ident, 99) <= NEAR_P99:
                    tint = (1.0, 1.0, 1.0)
                    resid = ident
                else:
                    k = (s * t_).sum(0) / np.maximum((s * s).sum(0), 1e-6)
                    if (k > NEAR_MAX_TINT).any():
                        continue
                    tint = tuple(float(min(1.0, round(v, 3))) for v in k)
                    resid = np.abs(t_ - s * np.array(tint, np.float32))
                    if np.sqrt((resid ** 2).mean()) > NEAR_RMS or np.percentile(resid, 99) > NEAR_P99:
                        continue
                score = (mismatch, float(np.sqrt((resid ** 2).mean())))
                if best is None or score < best[3]:
                    # R's crop pixel (u, v) is P's transposed pixel (u + dx, v + dy)
                    # shifted back: P sits (-dx, -dy) into R's crop.
                    best = (-dx, -dy, tint, score)
        return best

    for j in order:
        if tracks_of.get(j, set()) & distinct:
            kept.append(j)
            by_size.setdefault(tuple(sorted(crops[j].size)), []).append(j)
            continue
        size = tuple(sorted(crops[j].size))
        candidates = [i for dw in (-1, 0, 1) for dh in (-1, 0, 1)
                      for i in by_size.get((size[0] + dw, size[1] + dh), ())]
        best = None
        for i in candidates:
            for op in [None, *_LOSSLESS]:
                hit = compare(i, op, j)
                if hit and (best is None or hit[3] < best[1][3]):
                    best = ((i, op), hit)
        if best:
            (i, op), (dx, dy, tint, _score) = best
            found[j] = (i, op, (dx, dy), tint)
        else:
            kept.append(j)
            by_size.setdefault(size, []).append(j)
    return found


#: Draws a frame may reach when symmetric parts are split into halves (each
#: split adds a draw wherever the part is drawn). Below `REALIZE_MAX_DRAWS`:
#: a draw is a sprite per body in the game.
SPLIT_DRAW_BUDGET = 40

#: Texels each half of a split part reaches past its axis. A half drawn
#: turned or between pixels is resampled, and at a bare cut the filter reads
#: the transparent texel beyond it: the two halves met along a faint seam (a
#: blob of 8, 10% of a turned capsule's pixels, 2026-10-04). Overlapping by
#: the filter's reach, each half's edge falls under the other's interior.
SPLIT_OVERLAP = 2


def _split_symmetric_parts(flipbook: "PartFlipbook", rendered, distinct=frozenset()) -> "PartFlipbook":
    """``flipbook`` with each part that is (within the near tolerance) its own
    left-right or top-bottom mirror stored as ONE HALF, drawn twice: as is, and
    mirrored onto the other half. Largest saving first, while every frame stays
    within ``SPLIT_DRAW_BUDGET`` draws; kept only where every frame still
    replays (a split's frames are withdrawn as ``_share_near_parts`` does).

    Jon, 2026-10-04: capsule limbs, bodies, visors and rings are their own
    mirrors (a third of a mite's and Sybil's texels). An odd width shares its
    centre column, drawn by both halves; the replay guard judges what that
    does to its anti-aliased ends. A part drawn by a ``distinct`` track is
    left whole, and art that stops being symmetric stops being split.
    """
    import numpy as np
    from dataclasses import replace as _replace

    if flipbook.placement == PLACEMENT_SNAPPED:
        return flipbook
    parts = list(flipbook.parts)
    uses: Dict[int, List[Tuple[str, int]]] = {}
    tracks_of: Dict[int, set] = {}
    counts: Dict[Tuple[str, int], int] = {}
    for row, (_duration, frames) in flipbook.clips.items():
        for index, draws in enumerate(frames):
            counts[(row, index)] = len(draws)
            for d in draws:
                uses.setdefault(d.part, []).append((row, index))
                tracks_of.setdefault(d.part, set()).add(d.track)
    candidates = []
    for i, part in enumerate(parts):
        if i not in uses or tracks_of.get(i, set()) & distinct:
            continue
        crop, _box = _trimmed(part.image)
        if min(crop.size) < 8:
            continue
        a = np.asarray(crop, dtype=np.float32)
        for op, axis in ((Image.Transpose.FLIP_LEFT_RIGHT, 0), (Image.Transpose.FLIP_TOP_BOTTOM, 1)):
            b = np.asarray(crop.transpose(op), dtype=np.float32)
            covered = (a[..., 3] > 0) | (b[..., 3] > 0)
            if float((np.abs(a[..., 3] - b[..., 3]) > 48)[covered].mean()) > NEAR_ALPHA_MISMATCH:
                continue
            both = (a[..., 3] > 200) & (b[..., 3] > 200)
            diff = np.abs(a[..., :3] - b[..., :3])[both]
            if both.sum() < 8 or np.sqrt((diff ** 2).mean()) > NEAR_RMS or np.percentile(diff, 99) > NEAR_P99:
                continue
            size = crop.size[axis]
            half = min(size, (size + 1) // 2 + SPLIT_OVERLAP)
            saving = (size - half) * crop.size[1 - axis]
            if saving <= 0:
                break
            candidates.append((saving, i, op, axis))
            break
    candidates.sort(key=lambda c: -c[0])
    chosen: Dict[int, tuple] = {}
    for saving, i, op, axis in candidates:
        frames = uses[i]
        added: Dict[Tuple[str, int], int] = {}
        for key in frames:
            added[key] = added.get(key, 0) + 1
        if all(counts[key] + n <= SPLIT_DRAW_BUDGET for key, n in added.items()):
            for key, n in added.items():
                counts[key] += n
            chosen[i] = (op, axis)

    def split(chosen_now):
        new_parts = list(parts)
        halves: Dict[int, int] = {}
        for i, (op, axis) in chosen_now.items():
            crop, box = _trimmed(parts[i].image)
            size = crop.size[axis]
            half = min(size, (size + 1) // 2 + SPLIT_OVERLAP)
            # Cut from the padded raster, so the half keeps the part's border
            # (the resampling filter's falloff) on every side but the axis.
            image = parts[i].image
            cut = image.crop((0, 0, box[0] + half, image.height) if axis == 0 else (0, 0, image.width, box[1] + half))
            halves[i] = len(new_parts)
            new_parts.append(PartRaster(f"{parts[i].name}/half", cut, parts[i].pivot))
        clips = {}
        for row, (duration, frames) in flipbook.clips.items():
            out_frames = []
            for draws in frames:
                out = []
                for d in draws:
                    if d.part not in chosen_now:
                        out.append(d)
                        continue
                    op, axis = chosen_now[d.part]
                    h = halves[d.part]
                    crop, _box = _trimmed(parts[d.part].image)
                    half_raster = new_parts[h]
                    size = crop.size[axis]
                    half = min(size, (size + 1) // 2 + SPLIT_OVERLAP)
                    out.append(_redrawn(d, parts[d.part], half_raster, h, None, (0, 0), (1.0, 1.0, 1.0)))
                    mirror_offset = (size - half, 0) if axis == 0 else (0, size - half)
                    out.append(
                        _replace(
                            _redrawn(d, parts[d.part], half_raster, h, op, mirror_offset, (1.0, 1.0, 1.0)),
                            track=None if d.track is None else f"{d.track}~mirror",
                        )
                    )
                out_frames.append(out)
            clips[row] = (duration, out_frames)
        used = sorted({d.part for _d, fr in clips.values() for draws in fr for d in draws})
        remap = {old: new for new, old in enumerate(used)}
        clips = {
            row: (duration, [[_replace(d, part=remap[d.part]) for d in draws] for draws in fr])
            for row, (duration, fr) in clips.items()
        }
        return _replace(flipbook, parts=[new_parts[k] for k in used], clips=clips, rects=[], pages=[])

    return _withdrawn_until_replayed(flipbook, rendered, chosen, split)


def _withdrawn_until_replayed(flipbook, rendered, chosen: dict, build) -> "PartFlipbook":
    """``build(chosen)`` with the candidates in ``chosen`` (part -> change)
    that keep every frame replaying, or ``flipbook`` when none do.

    A failing frame names its culprits: each candidate drawn in it is tried
    ALONE on the failing frames and withdrawn if it fails there alone; when
    none fails alone (two changes that only fail together), every candidate
    drawn in those frames is withdrawn. Coarse withdrawal (all of a frame's
    candidates at once) dropped every limb split of a character with one bad
    split, since limbs are drawn in every frame.
    """
    chosen = dict(chosen)
    for _attempt in range(8):
        if not chosen:
            return flipbook
        result = build(chosen)
        failing = _replay_failures(result, rendered)
        if not failing:
            return result
        sample = failing[:6]
        subset = {}
        for name in sample:
            row, index = name.rsplit(":", 1)
            subset[(row, int(index))] = rendered[(row, int(index))]
        suspects = {d.part for name in sample for d in flipbook.clips[name.rsplit(":", 1)[0]][1][int(name.rsplit(":", 1)[1])]}
        suspects &= set(chosen)
        culprits = {part for part in suspects if _replay_failures(build({part: chosen[part]}), subset)}
        for part in culprits or suspects:
            chosen.pop(part, None)
    return flipbook


def _share_near_parts(flipbook: "PartFlipbook", rendered, distinct=frozenset()) -> "PartFlipbook":
    """``flipbook`` with every part that is a NEAR twin of another (mirror,
    quarter turn or the same, a texel over, in a tint: ``_near_sources``) drawn
    from that twin, kept only where every frame still replays its render.

    Jon, 2026-10-04: limbs painted separately are the same shape a pixel apart,
    and a back limb is its front limb darker. Exact sharing never sees them; a
    tolerance does, and the replay guard is the arbiter: a frame that no
    longer replays withdraws the near shares drawn in it, and the rest are
    tried again.
    """
    if flipbook.placement == PLACEMENT_SNAPPED:
        return flipbook
    sources = _near_sources(flipbook, distinct)
    return _withdrawn_until_replayed(flipbook, rendered, sources, lambda chosen: _drawn_from_sources(flipbook, chosen))


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
#: ⚠ The band at a frame's border a continuous replay is not measured over (the
#: ``edge`` of ``CONTINUOUS_REPLAY_TOLERANCE``): the reach of the reduction
#: filter. Art that runs past the frame is cut by the supersampled canvas
#: BEFORE the reduction, while a part is reduced whole and drawn unclipped (as
#: the game draws it, past the baked frame, like Mary-O's feet), so in this
#: band the two legitimately differ: paradox_barber's death on the ground
#: made blobs to 121 along the frame's bottom (2026-10-03). Anything missing
#: away from the border is still measured.
EDGE_BAND = 3
CONTINUOUS_REPLAY_TOLERANCE = {"threshold": 64, "radius": 0, "edge": EDGE_BAND}

CONTINUOUS_REPLAY_PARITY = 0.01
CONTINUOUS_REPLAY_BLOB = 6


def _max_channel_difference(a: Image.Image, b: Image.Image) -> int:
    from PIL import ImageChops

    extrema = ImageChops.difference(a.convert("RGBA"), b.convert("RGBA")).getextrema()
    return max(high for _low, high in extrema)
