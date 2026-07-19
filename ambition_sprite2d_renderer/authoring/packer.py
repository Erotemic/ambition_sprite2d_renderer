"""Professional sprite-atlas packing: per-frame alpha-trim + MaxRects bin
packing across one or more page images.

Our generated sheets are 84-97% transparent because every frame reserves the
full logical canvas (a tall jump pose dictates the height, a wide attack the
width, and idle/rest frames waste the rest). This module reclaims that space:

  1. **Trim** each frame to its opaque alpha bounding box, recording the offset
     of the trimmed rect within the original (logical) frame.
  2. **Pack** the trimmed rects into pages no larger than ``max_dim`` using the
     ``rectpack`` MaxRects bin packer (the NP-hard heuristic we deliberately do
     NOT reinvent). No rotation — Bevy's ``TextureAtlas`` can't render rotated
     atlas frames without a custom mesh.
  3. **Extrude/gutter**: a transparent ``padding`` border around each frame so
     bilinear filtering at a frame edge never samples a neighbouring frame.

The logical frame size, feet anchor, and gameplay hurt/hit boxes stay in
*untrimmed* coordinates — trimming is purely a storage optimization. Each
placement carries ``trim_offset`` so the runtime can position the trimmed rect
exactly where the full frame would have drawn it.

Cross-target packing falls out for free: pass frames from several targets to one
``pack_frames`` call and they share pages; each frame's ``key`` records which
target/animation/frame it belongs to so callers can emit per-target manifests.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Hashable, List, Sequence, Tuple

from PIL import Image
from ..profiling import profile
from rectpack import newPacker, PackingMode, SORT_AREA
from rectpack.maxrects import MaxRectsBssf


@dataclass
class FrameInput:
    """One frame to pack. ``image`` is rendered at the LOGICAL frame size
    (after any uniform per-sheet crop); ``logical_size`` is that ``(W, H)``."""

    key: Hashable
    image: Image.Image
    logical_size: Tuple[int, int]


@dataclass
class FramePlacement:
    """Where a frame's trimmed pixels landed, plus the trim geometry needed to
    reconstruct its position within the logical frame."""

    page: int
    # Trimmed rect within the page image (excludes the transparent gutter).
    x: int
    y: int
    w: int
    h: int
    # Offset of the trimmed rect's top-left within the logical frame.
    off_x: int
    off_y: int
    # Logical (untrimmed) frame size — the gameplay coordinate space.
    src_w: int
    src_h: int


@dataclass
class PackResult:
    pages: List[Image.Image]
    placements: Dict[Hashable, FramePlacement]


@profile
def _trim(image: Image.Image, logical_size: Tuple[int, int], trim: bool):
    """Return ``(trimmed_image, off_x, off_y)``. A fully transparent frame
    collapses to a 1x1 transparent pixel at the origin (it draws nothing)."""
    lw, lh = logical_size
    if not trim:
        return image, 0, 0
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0
    x0, y0, x1, y1 = bbox
    return image.crop((x0, y0, x1, y1)), x0, y0


@profile
def pack_frames(
    frames: Sequence[FrameInput],
    *,
    max_dim: int = 16384,
    page_size: int = 4096,
    padding: int = 1,
    trim: bool = True,
    background: Tuple[int, int, int, int] = (0, 0, 0, 0),
) -> PackResult:
    """Trim + MaxRects-pack ``frames`` freely into square pages of ``page_size``
    (spilling to more pages as needed). Frames of one logical animation may land
    on different pages — the runtime addresses each frame by its own page, so
    this maximizes fill. ``page_size`` is clamped to ``max_dim`` (the GPU limit).

    Raises ``ValueError`` if a single trimmed frame (plus gutter) exceeds the
    page — it can never fit.
    """
    if not frames:
        return PackResult(pages=[], placements={})

    page_cap = min(max_dim, max(page_size, 64))
    trimmed: List[Tuple[FrameInput, Image.Image, int, int]] = []
    for fr in frames:
        timg, ox, oy = _trim(fr.image, fr.logical_size, trim)
        tw, th = timg.size
        if tw + 2 * padding > page_cap or th + 2 * padding > page_cap:
            raise ValueError(
                f"frame {fr.key!r} is {tw}x{th} (+{padding}px gutter), exceeding the "
                f"{page_cap}px page; raise page_size"
            )
        trimmed.append((fr, timg, ox, oy))

    # Choose and execute the pack in one bounded search. The old implementation
    # binary-searched every pixel between the largest frame and ``page_cap``.
    # Each probe ran a complete MaxRects pack, then the successful result was
    # discarded and packed once more. A review roster could therefore perform
    # hundreds of full NP-hard heuristic packs merely to shave a few pixels off
    # atlas dimensions.
    #
    # Start from an area-derived near-square side with conservative slack, grow
    # geometrically only when that estimate fails, and REUSE the first
    # successful placement. Page images are cropped to their occupied extents
    # below, so this retains compact output without exact pixel-level search.
    sizes = [
        (t.size[0] + 2 * padding, t.size[1] + 2 * padding)
        for (_f, t, _x, _y) in trimmed
    ]
    _bin_dim, rects = _pack_near_square(sizes, page_cap=page_cap)
    if len(rects) != len(trimmed):
        placed = {r[5] for r in rects}
        missing = [trimmed[i][0].key for i in range(len(trimmed)) if i not in placed]
        raise ValueError(f"rectpack failed to place {len(missing)} frame(s): {missing[:5]}")

    # First pass: page extents (tight, not the full max_dim).
    num_pages = max(r[0] for r in rects) + 1
    page_extent = [(0, 0)] * num_pages
    placement_by_idx: Dict[int, Tuple[int, int, int]] = {}  # idx -> (page, bx, by)
    for binid, x, y, w, h, rid in rects:
        placement_by_idx[rid] = (binid, x, y)
        ew, eh = page_extent[binid]
        page_extent[binid] = (max(ew, x + w), max(eh, y + h))

    pages = [Image.new("RGBA", (max(1, w), max(1, h)), background) for (w, h) in page_extent]

    placements: Dict[Hashable, FramePlacement] = {}
    for idx, (fr, timg, ox, oy) in enumerate(trimmed):
        page, bx, by = placement_by_idx[idx]
        # Composite inside the gutter; the runtime rect excludes the gutter.
        px, py = bx + padding, by + padding
        pages[page].alpha_composite(timg, (px, py))
        lw, lh = fr.logical_size
        placements[fr.key] = FramePlacement(
            page=page,
            x=px,
            y=py,
            w=timg.width,
            h=timg.height,
            off_x=ox,
            off_y=oy,
            src_w=lw,
            src_h=lh,
        )

    if trim:
        _assert_lossless(trimmed, placements, pages)
    return PackResult(pages=pages, placements=placements)


@profile
def _pack_rects_once(
    sizes: Sequence[Tuple[int, int]],
    *,
    side: int,
    bin_count: int | float,
) -> List[Tuple[int, int, int, int, int, int]]:
    """Run one deterministic MaxRects pass and return ``rect_list()``.

    Keeping this as a separate seam lets the bin chooser reuse a successful
    trial as the final placement instead of paying for an identical second pack.
    """
    packer = newPacker(
        mode=PackingMode.Offline,
        rotation=False,
        pack_algo=MaxRectsBssf,
        sort_algo=SORT_AREA,
    )
    for idx, (w, h) in enumerate(sizes):
        packer.add_rect(w, h, rid=idx)
    packer.add_bin(side, side, count=bin_count)
    packer.pack()
    return list(packer.rect_list())


def _align_up(value: int, quantum: int) -> int:
    return ((int(value) + quantum - 1) // quantum) * quantum


@profile
def _pack_near_square(
    sizes: Sequence[Tuple[int, int]],
    *,
    page_cap: int,
    target_fill: float = 0.78,
    alignment: int = 64,
) -> Tuple[int, List[Tuple[int, int, int, int, int, int]]]:
    """Pack rectangles with a bounded near-square search.

    The area lower bound estimates a compact one-page square. MaxRects gets
    roughly 22 percent slack by default, which is usually enough for irregular
    sprite rectangles. If the estimate fails, the side grows by 25 percent.
    The first successful trial is returned directly. If one page is impossible
    even at ``page_cap``, one final unbounded-page pass uses that cap.

    This intentionally optimizes for regeneration latency rather than the exact
    mathematically smallest side. Occupied page extents are cropped after
    packing, so a conservative candidate does not force full-size output PNGs.
    """
    if not sizes:
        return max(1, min(page_cap, alignment)), []
    if page_cap <= 0:
        raise ValueError(f"page_cap must be positive, got {page_cap!r}")

    largest = max(max(w, h) for (w, h) in sizes)
    total_area = sum(w * h for (w, h) in sizes)
    if largest > page_cap:
        raise ValueError(
            f"rectangle dimension {largest} exceeds the {page_cap}px page cap"
        )

    # If area alone proves a single page impossible, skip a doomed trial.
    if total_area > page_cap * page_cap:
        rects = _pack_rects_once(sizes, side=page_cap, bin_count=float("inf"))
        return page_cap, rects

    fill = min(0.95, max(0.25, float(target_fill)))
    estimated = max(largest, math.ceil(math.sqrt(total_area / fill)))
    candidate = min(page_cap, _align_up(estimated, max(1, alignment)))

    while True:
        rects = _pack_rects_once(sizes, side=candidate, bin_count=1)
        if len(rects) == len(sizes):
            return candidate, rects
        if candidate >= page_cap:
            break
        grown = max(candidate + alignment, math.ceil(candidate * 1.25))
        candidate = min(page_cap, _align_up(grown, max(1, alignment)))

    rects = _pack_rects_once(sizes, side=page_cap, bin_count=float("inf"))
    return page_cap, rects


@profile
def _maxrects(sizes: List[Tuple[int, int]], bin_w: int, bin_h: int) -> List[Tuple[int, int, int]]:
    """Bin-pack ``sizes`` (w,h) into bins of ``bin_w``×``bin_h``; return one
    ``(bin_index, x, y)`` per input index, in input order. Raises if any rect
    can't be placed (i.e. is larger than a bin)."""
    packer = newPacker(
        mode=PackingMode.Offline,
        rotation=False,
        pack_algo=MaxRectsBssf,
        sort_algo=SORT_AREA,
    )
    for idx, (w, h) in enumerate(sizes):
        packer.add_rect(w, h, rid=idx)
    packer.add_bin(bin_w, bin_h, count=float("inf"))
    packer.pack()
    out: Dict[int, Tuple[int, int, int]] = {}
    for binid, x, y, _w, _h, rid in packer.rect_list():
        out[rid] = (binid, x, y)
    if len(out) != len(sizes):
        raise ValueError(f"maxrects failed to place {len(sizes) - len(out)} rect(s) in {bin_w}x{bin_h}")
    return [out[i] for i in range(len(sizes))]


@profile
def pack_frames_grouped(
    groups: Dict[Hashable, Sequence[FrameInput]],
    *,
    max_dim: int = 16384,
    page_size: int = 4096,
    padding: int = 1,
    trim: bool = True,
    background: Tuple[int, int, int, int] = (0, 0, 0, 0),
) -> Tuple[PackResult, Dict[Hashable, int]]:
    """Like [`pack_frames`] but keeps every frame of a group on ONE page.

    The runtime swaps page images per *animation* (a `SheetRow` has a single
    `page`), so an animation's frames must not be scattered across pages. Each
    group (an animation, keyed e.g. by ``(target, animation)``) is first packed
    into its own tight *block*; the blocks are then bin-packed onto pages. This
    still trims every frame and reclaims inter-animation space, while guaranteeing
    the per-page invariant. Cross-target packing falls out by keying groups with
    the target id.

    Returns ``(PackResult, group_page)`` where ``group_page[group_key]`` is the
    page each group landed on.
    """
    if not groups:
        return PackResult(pages=[], placements={}), {}

    # Square page size keeps pages well-filled (packing into one giant bin and
    # taking the extent yields a tall sliver). Bump if a single block needs more.
    bin_dim = min(max_dim, max(page_size, 64))

    # 1. Trim every frame; lay out each group into its own block coordinate space.
    group_keys = list(groups.keys())
    group_blocks: Dict[Hashable, Dict[Hashable, Tuple[Image.Image, int, int, int, int, int, int]]] = {}
    block_size: Dict[Hashable, Tuple[int, int]] = {}
    for gk in group_keys:
        frames = groups[gk]
        sizes: List[Tuple[int, int]] = []
        trimmed: List[Tuple[FrameInput, Image.Image, int, int]] = []
        for fr in frames:
            timg, ox, oy = _trim(fr.image, fr.logical_size, trim)
            tw, th = timg.size
            if tw + 2 * padding > max_dim or th + 2 * padding > max_dim:
                raise ValueError(f"frame {fr.key!r} is {tw}x{th}, exceeding the {max_dim}px limit")
            sizes.append((tw + 2 * padding, th + 2 * padding))
            trimmed.append((fr, timg, ox, oy))
        intra = _maxrects(sizes, bin_dim, bin_dim)
        if any(b != 0 for b, _, _ in intra):
            raise ValueError(f"animation group {gk!r} does not fit in one {max_dim}px page")
        bw = max((x + sizes[i][0]) for i, (_, x, _y) in enumerate(intra))
        bh = max((y + sizes[i][1]) for i, (_b, _x, y) in enumerate(intra))
        block_size[gk] = (bw, bh)
        per_frame = {}
        for i, (fr, timg, ox, oy) in enumerate(trimmed):
            _b, ix, iy = intra[i]
            per_frame[fr.key] = (timg, ix, iy, ox, oy, fr.logical_size[0], fr.logical_size[1])
        group_blocks[gk] = per_frame

    # 2. Bin-pack the blocks onto pages.
    block_place = _maxrects([block_size[gk] for gk in group_keys], bin_dim, bin_dim)
    group_page: Dict[Hashable, int] = {}
    page_extent: Dict[int, Tuple[int, int]] = {}
    block_origin: Dict[Hashable, Tuple[int, int, int]] = {}
    for gk, (page, bx, by) in zip(group_keys, block_place):
        group_page[gk] = page
        block_origin[gk] = (page, bx, by)
        bw, bh = block_size[gk]
        ew, eh = page_extent.get(page, (0, 0))
        page_extent[page] = (max(ew, bx + bw), max(eh, by + bh))

    num_pages = (max(page_extent) + 1) if page_extent else 0
    pages = [
        Image.new("RGBA", (max(1, page_extent.get(p, (1, 1))[0]), max(1, page_extent.get(p, (1, 1))[1])), background)
        for p in range(num_pages)
    ]

    # 3. Compose + record placements (gutter inside each frame's padded cell).
    placements: Dict[Hashable, FramePlacement] = {}
    for gk in group_keys:
        page, bx, by = block_origin[gk]
        for fkey, (timg, ix, iy, ox, oy, lw, lh) in group_blocks[gk].items():
            px, py = bx + ix + padding, by + iy + padding
            pages[page].alpha_composite(timg, (px, py))
            placements[fkey] = FramePlacement(
                page=page, x=px, y=py, w=timg.width, h=timg.height,
                off_x=ox, off_y=oy, src_w=lw, src_h=lh,
            )

    if trim:
        all_frames = [fr for gk in group_keys for fr in groups[gk]]
        _assert_lossless(all_frames, placements, pages)
    return PackResult(pages=pages, placements=placements), group_page


@profile
def _assert_lossless(
    trimmed: Sequence[Tuple[FrameInput, Image.Image, int, int]],
    placements: Dict[Hashable, FramePlacement],
    pages: List[Image.Image],
) -> None:
    """Assert that every packed trimmed region is visually pixel-identical.

    The former check reconstructed the complete logical canvas for every frame,
    even though alpha trimming has already proven that everything outside the
    trimmed region is transparent. Compare only the occupied region and validate
    its offset bounds; this preserves the same visual invariant with much less
    allocation and compositing.
    """
    for fr, trimmed_image, off_x, off_y in trimmed:
        p = placements[fr.key]
        if (p.off_x, p.off_y) != (off_x, off_y):
            raise AssertionError(
                f"lossless check failed for frame {fr.key!r}: trim offset changed"
            )
        if (
            p.off_x < 0
            or p.off_y < 0
            or p.off_x + p.w > p.src_w
            or p.off_y + p.h > p.src_h
        ):
            raise AssertionError(
                f"lossless check failed for frame {fr.key!r}: trim geometry exceeds logical frame"
            )
        sub = pages[p.page].crop((p.x, p.y, p.x + p.w, p.y + p.h))
        # Compare visually: compositing onto transparent zeroes arbitrary RGB
        # values hidden beneath alpha 0 on both sides.
        src_norm = Image.new("RGBA", trimmed_image.size, (0, 0, 0, 0))
        src_norm.alpha_composite(trimmed_image.convert("RGBA"))
        if sub.tobytes() != src_norm.tobytes():
            raise AssertionError(
                f"lossless check failed for frame {fr.key!r}: packed pixels "
                f"differ from the trimmed source (packing bug)"
            )
