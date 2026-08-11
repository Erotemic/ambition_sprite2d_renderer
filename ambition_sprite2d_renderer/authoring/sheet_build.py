"""Generic spritesheet builder for tack-on targets.

The tack-on render pipeline that most procedural characters and props
use under ``targets/``: builds a labeled spritesheet PNG, a per-row
YAML manifest, and a sidecar RON manifest that the sandbox's
`SheetRegistry` consumes at runtime.

This module is the *generic* piece — math, drawing primitives, the
`build_sheet` entry point, the RON emitters. Character-specific
drawing helpers (palettes, body parts, animation poses) live next to
the characters that use them — see
``targets/characters/_pirate_common.py`` for the pirate-family
helpers.

A target's ``render()`` function typically composes:

    from ...authoring.sheet_build import build_sheet
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda anim, idx, n: _draw_my_frame(anim, idx, n),
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=True,
    )

`build_sheet` returns a dict of paths (``spritesheet`` / ``yaml`` /
``ron`` / ``preview`` / ``canonical`` / ``canonical_transparent``)
which the target's ``render()`` flattens into a `list[Path]` for the
discovery API.
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from functools import lru_cache
from contextvars import ContextVar
from copy import deepcopy
from pathlib import Path
from typing import Any, List, Mapping, MutableMapping, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from ..yaml_io import safe_dump
from .actor_contract import write_actor_contract_for_tackon
from ..profiling import profile, profile_checkpoint
from .frame_source import CallableFrameSource, FrameSource
from ..core.measure import measure_body_metrics
from ..core.manifest_ron import record_to_ron, records_to_ron, ron_tuning
from ..registry.pack_groups import policy_for
import os
import time
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]


def publish_character_notes(
    manifest: MutableMapping[str, Any],
    metadata: Mapping[str, Any] | None,
) -> None:
    """Copy portable, freeform character-writing notes into sheet YAML.

    These fields are intentionally not part of the runtime actor contract. They
    travel with the art so a game, dialogue tool, or future author can opt into
    the suggested characterization without treating it as a normalized identity
    database.
    """
    if not metadata:
        return
    for key in ("authoring_description", "gameplay_description"):
        value = metadata.get(key)
        # These notes are keyed mappings now (prose-era configs are lifted into
        # the same shape by the loader). Publish either form: dropping mappings
        # would silently strip the notes from every structured character.
        if isinstance(value, Mapping) and value:
            manifest[key] = deepcopy(dict(value))
        elif isinstance(value, str) and value.strip():
            manifest[key] = value.strip()
    hints = metadata.get("dialogue_hints")
    if isinstance(hints, Mapping):
        copied = deepcopy(dict(hints))
        barks = copied.get("barks")
        if isinstance(barks, (list, tuple)):
            copied["barks"] = [
                str(bark).strip() for bark in barks if str(bark).strip()
            ]
        if copied:
            manifest["dialogue_hints"] = copied


_CANONICAL_ONLY = ContextVar("ambition_sheet_build_canonical_only", default=False)


@contextmanager
def canonical_render_only():
    """Limit this procedural-sheet family to a freshly drawn canonical.

    The target's normal ``render`` function still runs, preserving its private
    authoring implementation, but :func:`render_sheet` skips frame enumeration,
    packing, and manifests. This is the efficient default-portrait adapter for
    modules built on ``sheet_build``; it is not a universal character model.
    """

    token = _CANONICAL_ONLY.set(True)
    try:
        yield
    finally:
        _CANONICAL_ONLY.reset(token)


def _normalize_frame_padding(frame_padding: Any) -> Tuple[int, int, int, int]:
    """Return ``(left, top, right, bottom)`` publish padding.

    The common shorthand ``N`` means the same transparent border on every side,
    and ``(x, y)`` means horizontal/vertical padding. The result is always
    non-negative integers so callers can safely add it to frame geometry.
    """

    if frame_padding is None:
        return (0, 0, 0, 0)
    if isinstance(frame_padding, (int, float)):
        n = max(0, int(frame_padding))
        return (n, n, n, n)
    values = tuple(int(v) for v in frame_padding)
    if len(values) == 2:
        x, y = values
        return (max(0, x), max(0, y), max(0, x), max(0, y))
    if len(values) == 4:
        left, top, right, bottom = values
        return tuple(max(0, v) for v in (left, top, right, bottom))
    raise ValueError(
        "frame_padding must be None, a single integer, a 2-tuple, or a 4-tuple"
    )


def _shift_xy_payload(payload: Any, dx: float, dy: float) -> Any:
    """Translate common point payloads by ``(dx, dy)``.

    This handles the coordinate containers the sprite pipeline already emits:
    ``{x, y}``, ``[x, y]`` / ``(x, y)``, and nested mappings/lists containing
    those shapes. Non-coordinate payloads pass through unchanged.
    """

    if isinstance(payload, Mapping):
        if "x" in payload and "y" in payload:
            shifted = dict(payload)
            shifted["x"] = round(float(payload["x"]) + dx, 3)
            shifted["y"] = round(float(payload["y"]) + dy, 3)
            return shifted
        return {k: _shift_xy_payload(v, dx, dy) for k, v in payload.items()}
    if isinstance(payload, tuple) and len(payload) == 2 and all(isinstance(v, (int, float)) for v in payload):
        return (round(float(payload[0]) + dx, 3), round(float(payload[1]) + dy, 3))
    if isinstance(payload, list) and len(payload) == 2 and all(isinstance(v, (int, float)) for v in payload):
        return [round(float(payload[0]) + dx, 3), round(float(payload[1]) + dy, 3)]
    if isinstance(payload, list):
        return [_shift_xy_payload(v, dx, dy) for v in payload]
    return payload


def _pad_rgba_frame(frame: Image.Image, frame_padding: Tuple[int, int, int, int]) -> Image.Image:
    left, top, right, bottom = frame_padding
    if left == top == right == bottom == 0:
        return frame
    padded = Image.new(
        "RGBA",
        (frame.width + left + right, frame.height + top + bottom),
        (0, 0, 0, 0),
    )
    padded.alpha_composite(frame, (left, top))
    return padded


def _translate_actor_metadata(actor_metadata: Any, dx: float, dy: float) -> Any:
    if not actor_metadata:
        return actor_metadata
    shifted = deepcopy(actor_metadata)
    sockets = shifted.get("sockets")
    if isinstance(sockets, Mapping):
        for socket in sockets.values():
            if isinstance(socket, MutableMapping) and "point" in socket:
                socket["point"] = _shift_xy_payload(socket["point"], dx, dy)
    return shifted


def _translate_attack_hitboxes(attack_hitboxes: Any, dx: float, dy: float) -> Any:
    if not attack_hitboxes:
        return attack_hitboxes
    return deepcopy(_shift_xy_payload(attack_hitboxes, dx, dy))


@profile
def _render_canonical_only(source: FrameSource, out_dir: Path) -> dict[str, Path]:
    target = source.target
    rows = source.rows
    anim, nframes, _duration = rows[0]
    image = source.render_fn(anim, min(1, nframes - 1), nframes).convert("RGBA")
    image = _pad_rgba_frame(image, _normalize_frame_padding(getattr(source, "frame_padding", None)))
    if source.auto_crop:
        bbox = image.getchannel("A").getbbox()
        if bbox is not None:
            margin = int(source.crop_margin)
            x1 = max(0, bbox[0] - margin)
            y1 = max(0, bbox[1] - margin)
            x2 = min(image.width, bbox[2] + margin)
            y2 = min(image.height, bbox[3] + margin)
            image = image.crop((x1, y1, x2, y2))
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical = out_dir / f"{target}_canonical.png"
    transparent = out_dir / f"{target}_canonical_transparent.png"
    background = Image.new("RGBA", image.size, (43, 33, 40, 255))
    background.alpha_composite(image)
    background.save(canonical)
    image.save(transparent)
    return {
        "canonical": canonical,
        "canonical_transparent": transparent,
        "spritesheet": out_dir / f"{target}_spritesheet.png",
        "yaml": out_dir / f"{target}_spritesheet.yaml",
        "ron": out_dir / f"{target}_spritesheet.ron",
        "actor": out_dir / f"{target}_actor.ron",
        "preview": out_dir / f"{target}_preview_labeled.png",
    }


# Optional semantic frame-publication hook. Capture tooling assigns a
# callable(target, anim, frame_idx, frame_image) here for the duration of a
# capture run; production rendering leaves it None (zero overhead).
FRAME_CAPTURE_HOOK = None

SCALE = 4
BASE_FRAME = (128, 128)
LABEL_WIDTH = 100

ANIMATIONS = [
    ("idle", 6, 120),
    ("walk", 8, 90),
    ("slash", 6, 85),
    ("taunt", 6, 100),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

# Mirror of the Rust `CharacterAnim::from_name` alias table at
# `crates/ambition_sprite_sheet/src/character/anim.rs`.
# Two sets so `is_character_sheet` can detect *any* CharacterAnim row
# while `IDLE_ALIASES` flags the missing-Idle case specifically.
IDLE_ALIASES = frozenset(("idle", "opening", "rest", "front_idle", "side_idle"))
CHARACTER_ANIM_NAMES = frozenset(
    (
        *IDLE_ALIASES,
        "walk",
        "stable",
        "spin",
        "side_walk",
        "run",
        "closing",
        "jump",
        "fall",
        "slash",
        "hit",
        "hurt",
        "death",
        "blink_out",
        "blink_in",
        "dash",
        "fly",
        "hover",
        "taunt",
        "ledge_grab",
        "ledge_climb",
        "ledge_getup",
        "wall_grab",
        "float_glide",
        "land_hard",
        "land_recovery",
        "dash_startup",
        "attack_side",
        "attack_up",
        "attack_down",
        "air_neutral",
        "air_forward",
        "air_back",
        "air_down",
        "air_up",
        "ledge_roll",
        "ledge_getup_attack",
    )
)


def diagnose_idle_coverage(target: str, anim_names: List[str]) -> Optional[str]:
    """Return a publish-time warning string when the sheet's row names
    look like a character sheet (≥1 row maps to `CharacterAnim`) but
    none of them is an Idle alias. Returns `None` if the sheet is
    either non-character (props/gates: zero CharacterAnim hits) or
    already has an Idle row.

    Mirroring the runtime's `try_load_spec_for_character_id` filter:
    a character sheet without an Idle row renders as a placeholder
    in-game. Surfacing this at publish time turns the silent failure
    into a visible warning for the renderer author.
    """
    has_character_row = any(n in CHARACTER_ANIM_NAMES for n in anim_names)
    has_idle = any(n in IDLE_ALIASES for n in anim_names)
    if has_character_row and not has_idle:
        return (
            f"[sheet_build] WARN: {target!r} sheet has character-anim rows "
            f"{[n for n in anim_names if n in CHARACTER_ANIM_NAMES]!r} but no Idle alias "
            f"(any of {sorted(IDLE_ALIASES)}). The runtime will render this character "
            f"as a colored-rectangle placeholder. Add or rename one row to an Idle alias."
        )
    return None


@lru_cache(maxsize=None)
def font(size: int = 14):
    """Return a cached label font.

    Sheet generation draws the same two label sizes for every animation row.
    Loading the TrueType file for each draw dominated labeled-grid layout in
    profiles, so keep one immutable Pillow font object per size.
    """

    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def lerp(a, b, t):
    return a + (b - a) * t


def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))


def oscillate(frame_idx: int, nframes: int, phase: float = 0.0) -> float:
    return math.sin((frame_idx / max(1, nframes)) * math.tau + phase)


def rot(pt, deg):
    rad = math.radians(deg)
    c = math.cos(rad)
    s = math.sin(rad)
    x, y = pt
    return (x * c - y * s, x * s + y * c)


def transform(pt, origin, deg=0.0, scale=1.0):
    x, y = pt
    x *= scale
    y *= scale
    x, y = rot((x, y), deg)
    return (origin[0] + x, origin[1] + y)


def poly(draw: ImageDraw.ImageDraw, points, fill, outline=None, width=1):
    draw.polygon(points, fill=fill)
    if outline is not None:
        draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def rotated_rect_points(center, w, h, deg):
    hw, hh = w / 2.0, h / 2.0
    pts = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    return [transform(p, center, deg=deg) for p in pts]


def rotated_rect(draw, center, w, h, deg, fill, outline=None, width=1):
    pts = rotated_rect_points(center, w, h, deg)
    poly(draw, pts, fill, outline, width)
    return pts


def circle(draw, center, r, fill, outline=None, width=1):
    x, y = center
    draw.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=width)


def ellipse(draw, bbox, fill, outline=None, width=1):
    draw.ellipse(bbox, fill=fill, outline=outline, width=width)


def line(draw, points, fill, width=1):
    draw.line(points, fill=fill, width=width, joint="curve")


def downsample(img: Image.Image, final_size=BASE_FRAME):
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return img.resize(final_size, Image.Resampling.LANCZOS)
    x1, y1, x2, y2 = bbox
    crop = img.crop((x1, y1, x2, y2))
    fw, fh = final_size
    target_w = fw * 0.78
    target_h = fh * 0.88
    scale = min(target_w / max(1, crop.width), target_h / max(1, crop.height))
    new_size = (max(1, int(crop.width * scale)), max(1, int(crop.height * scale)))
    crop = crop.resize(new_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", final_size, (0, 0, 0, 0))
    ox = int((fw - new_size[0]) / 2)
    oy = int(fh - new_size[1] - fh * 0.12)
    canvas.alpha_composite(crop, (ox, oy))
    return canvas


def alpha_bbox_metrics(frame: Image.Image):
    # Canonical "measure by default" (core.measure): inclusive last-opaque-row
    # feet + all-channel bbox, shared with the adapter spine. Preserve this
    # path's output shape — rounded values, no frame_width/height, and a
    # degenerate fallback for a fully transparent frame.
    metrics = measure_body_metrics(frame)
    if metrics is None:
        return {
            "body_pixel_bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
            "feet_pixel": {"x": frame.width / 2.0, "y": frame.height},
            "feet_anchor_norm": {"x": 0.0, "y": -0.5},
        }
    feet, anchor = metrics["feet_pixel"], metrics["feet_anchor_norm"]
    return {
        "body_pixel_bbox": metrics["body_pixel_bbox"],
        "feet_pixel": {"x": round(feet["x"], 3), "y": round(feet["y"], 3)},
        "feet_anchor_norm": {
            "x": round(anchor["x"], 6),
            "y": round(anchor["y"], 6),
        },
    }


@profile
def _fit_text(draw, text, font, max_px):
    """`text` shortened until it MEASURES no wider than `max_px`.

    A label column is a fixed pixel width and these fonts are proportional, so
    "how many characters fit" has no answer — only "how wide is this string"
    does. Returns the longest prefix plus an ellipsis that still fits.
    """
    if max_px <= 0:
        # No column was declared, so there is nothing to clip TO. Returning the
        # text unchanged preserves the existing behaviour exactly; returning ""
        # would erase a label instead of fitting it.
        return text
    if draw.textlength(text, font=font) <= max_px:
        return text
    ellipsis = "…"
    if draw.textlength(ellipsis, font=font) > max_px:
        return ""
    for cut in range(len(text) - 1, 0, -1):
        if draw.textlength(text[:cut] + ellipsis, font=font) <= max_px:
            return text[:cut] + ellipsis
    return ellipsis


def _grid_sheet_rows(target, rendered_rows, fw, fh, label_width, max_dim):
    """Legacy layout: one animation per labeled row, stacked vertically and
    split into page images only when the column would exceed ``max_dim``.
    Byte-identical to the pre-packer output. Returns
    ``(page_sheets, rows_meta, num_pages)``."""
    max_frames = max(n for _, n, _, _ in rendered_rows)
    page_w = label_width + fw * max_frames
    if page_w > max_dim:
        raise ValueError(
            f"spritesheet for {target!r} has a {page_w}px-wide frame row, exceeding the "
            f"{max_dim}px texture limit; reduce the frame size or frame count"
        )
    rows_per_page = max(1, max_dim // fh)
    num_pages = max(1, (len(rendered_rows) + rows_per_page - 1) // rows_per_page)
    page_sheets, page_draws = [], []
    for p in range(num_pages):
        rows_on_page = min(rows_per_page, len(rendered_rows) - p * rows_per_page)
        img = Image.new("RGBA", (page_w, fh * rows_on_page), (0, 0, 0, 0))
        page_sheets.append(img)
        page_draws.append(blending_draw(img))
    rows_meta = []
    title_font = font(14)
    detail_font = font(11)
    for row_idx, (anim, nframes, duration_ms, frames_data) in enumerate(rendered_rows):
        page = row_idx // rows_per_page
        y = (row_idx % rows_per_page) * fh
        draw_sheet, sheet = page_draws[page], page_sheets[page]
        draw_sheet.rectangle(
            (0, y, label_width - 1, y + fh - 1), fill=(18, 22, 30, 235)
        )
        # Clipped to the column, for the reason `creator_lab_props` learned the
        # expensive way: text drawn into a label column is composited UNDER the
        # frames, and prop/character art is mostly transparent, so anything that
        # overflows `label_width` shows THROUGH the sprite in game. There it was a
        # 44-character truncation on a proportional font; here there was no limit
        # at all, so a long animation name is one rename away from the same
        # artifact (2026-07-29).
        #
        # Nothing shipping overflows today (verified: `player_robot_v3` renders
        # byte-identical with and without this). It is the guard, not a repair.
        #
        # ⚠ and a guard must not become the bug it guards against. A sheet that
        # declares NO column (`label_width == 0`) has always drawn its labels
        # straight over frame 0, and clipping to a zero-width column would
        # silently DELETE that text rather than clip it. Deleting a label nobody
        # asked me to delete is a worse change than the overflow — so no column
        # means no clipping, and the caller keeps exactly what it had.
        draw_sheet.text(
            (8, y + 10),
            _fit_text(draw_sheet, anim, title_font, label_width - 16),
            fill=(236, 240, 244, 255),
            font=title_font,
        )
        draw_sheet.text(
            (8, y + 30),
            _fit_text(
                draw_sheet,
                f"{nframes}f @ {duration_ms}ms",
                detail_font,
                label_width - 16,
            ),
            fill=(160, 170, 184, 255),
            font=detail_font,
        )
        rects = []
        for frame_idx, (frame, meta) in enumerate(frames_data):
            x = label_width + frame_idx * fw
            sheet.alpha_composite(frame, (x, y))
            rect = {"x": x, "y": y, "w": fw, "h": fh, "page": page}
            if meta:
                rect.update(meta)
            rects.append(rect)
        rows_meta.append(
            {
                "animation": anim,
                "row_index": row_idx,
                "frame_count": nframes,
                "duration_ms": duration_ms,
                "duration_secs": round(duration_ms / 1000.0, 6),
                "page": page,
                "rects": rects,
            }
        )
    return page_sheets, rows_meta, num_pages


@profile
def _packed_sheet_rows(target, rendered_rows, fw, fh, max_dim, page_size=4096):
    """Professional layout: alpha-trim every frame + MaxRects-pack ALL frames
    freely onto tight square pages (best fill). Frames of one animation may
    span pages, so each frame carries its own `page` (and `off` trim offset);
    the runtime addresses frames per-page. Returns ``(page_sheets, rows_meta,
    num_pages)``."""
    from .packer import FrameInput, pack_frames

    frames = [
        FrameInput(key=(row_idx, fi), image=img, logical_size=(fw, fh))
        for row_idx, (_anim, _n, _d, frames_data) in enumerate(rendered_rows)
        for fi, (img, _meta) in enumerate(frames_data)
    ]
    result = pack_frames(frames, max_dim=max_dim, page_size=page_size, padding=1, trim=True)
    rows_meta = []
    for row_idx, (anim, nframes, duration_ms, frames_data) in enumerate(rendered_rows):
        rects = []
        for frame_idx, (_img, meta) in enumerate(frames_data):
            pl = result.placements[(row_idx, frame_idx)]
            # Per-frame page (frames of a row may differ) + trim offset.
            rect = {"x": pl.x, "y": pl.y, "w": pl.w, "h": pl.h, "fpage": pl.page}
            if pl.off_x or pl.off_y:
                rect["off"] = (pl.off_x, pl.off_y)
            if meta:
                rect.update(meta)
            rects.append(rect)
        # SheetRow.page stays the page of frame 0 (a sensible default); the
        # runtime uses the per-frame `fpage` for trimmed sheets.
        row_page = result.placements[(row_idx, 0)].page if nframes else 0
        rows_meta.append(
            {
                "animation": anim,
                "row_index": row_idx,
                "frame_count": nframes,
                "duration_ms": duration_ms,
                "duration_secs": round(duration_ms / 1000.0, 6),
                "page": row_page,
                "rects": rects,
            }
        )
    return result.pages, rows_meta, len(result.pages)


@profile


@profile
def _trimmed_labeled_preview(rendered_rows, fw: int, fh: int, label_width: int) -> Image.Image:
    """Build the human-only labeled preview without full-canvas blend scratches.

    The preview background is opaque. Preblend the one translucent label-strip
    color once, then use ordinary Pillow drawing so each label touches only its
    own pixels. This matters for full fighter sheets whose preview can be
    hundreds of megapixels.
    """
    max_frames = max(nframes for _anim, nframes, _duration_ms, _frames_data in rendered_rows)
    preview_w = label_width + fw * max_frames
    preview = Image.new("RGBA", (preview_w, fh * len(rendered_rows)), (43, 33, 40, 255))
    draw_prev = ImageDraw.Draw(preview)
    # (18, 22, 30, 235) composited over (43, 33, 40, 255).
    label_fill = (20, 23, 31, 255)
    title_font = font(14)
    detail_font = font(11)
    for row_idx, (anim, nframes, duration_ms, frames_data) in enumerate(rendered_rows):
        y_prev = row_idx * fh
        draw_prev.rectangle(
            (0, y_prev, label_width - 1, y_prev + fh - 1),
            fill=label_fill,
        )
        draw_prev.text(
            (8, y_prev + 10),
            anim,
            fill=(236, 240, 244, 255),
            font=title_font,
        )
        draw_prev.text(
            (8, y_prev + 30),
            f"{nframes}f @ {duration_ms}ms",
            fill=(160, 170, 184, 255),
            font=detail_font,
        )
        for frame_idx, (frame, _meta) in enumerate(frames_data):
            preview.alpha_composite(
                frame,
                (label_width + frame_idx * fw, y_prev),
            )
    return preview


def layout_sheet_rows(
    target,
    rendered_rows,
    fw,
    fh,
    *,
    label_width,
    trim,
    max_dim=16384,
    page_size=4096,
):
    """The ONE sheet-layout seam: turn rendered rows into GPU page images +
    normalized ``rows_meta`` (explicit rects, per-frame ``fpage``/``off``).

    ``rendered_rows`` is ``[(anim, nframes, duration_ms, [(frame_img, meta), …]), …]``.
    ``trim=True`` alpha-trims + MaxRects-packs onto tight pages; ``trim=False``
    keeps the legacy one-animation-per-labeled-row grid. Returns
    ``(page_sheets, rows_meta, num_pages)``. Shared by [`build_sheet`] and the
    bespoke boss generators so there is exactly one packer + grid code path."""
    if trim:
        return _packed_sheet_rows(target, rendered_rows, fw, fh, max_dim, page_size)
    return _grid_sheet_rows(target, rendered_rows, fw, fh, label_width, max_dim)


@profile
def build_sheet(
    target: str,
    rows: List[Tuple[str, int, int]],
    render_fn,
    out_dir: Path,
    frame_size=BASE_FRAME,
    label_width=LABEL_WIDTH,
    frame_meta_fn=None,
    auto_crop: bool = True,
    crop_margin: int = 2,
    frame_padding=None,
    actor_metadata=None,
    body_metrics_fn=None,
    sheet_tuning=None,
    animation_key_map=None,
    attack_hitboxes=None,
    hurtbox_parts=None,
    max_sheet_dimension: int = 16384,
    trim: Optional[bool] = None,
    body_inset=None,
    pose_bodies: str = "art",
):
    """Build one module target's sheet from a frame callable + rows.

    Thin constructor: wraps the recipe in a :class:`CallableFrameSource` and
    hands it to the one :func:`render_sheet` core. Kept as the module-target
    entry point so the ~50 target modules that call it need no change.
    """
    source = CallableFrameSource(
        target=target,
        rows=rows,
        render_fn=render_fn,
        frame_size=frame_size,
        label_width=label_width,
        frame_meta_fn=frame_meta_fn,
        auto_crop=auto_crop,
        crop_margin=crop_margin,
        frame_padding=frame_padding,
        actor_metadata=actor_metadata,
        body_inset=body_inset,
        body_metrics_fn=body_metrics_fn,
        sheet_tuning=sheet_tuning,
        animation_key_map=animation_key_map,
        attack_hitboxes=attack_hitboxes,
        hurtbox_parts=hurtbox_parts,
        max_sheet_dimension=max_sheet_dimension,
        trim=trim,
        pose_bodies=pose_bodies,
    )
    return render_sheet(source, out_dir)


@profile
def render_sheet(source: FrameSource, out_dir: Path):
    """Build a sheet from any frame source with a callable-style recipe.

    The one sheet-assembly core for module-authored targets: render every frame,
    auto-crop, lay out via :func:`layout_sheet_rows`, measure body metrics +
    per-animation hurt/hit geometry, and emit the page PNG(s), YAML, RON, and
    actor sidecar.

    ``frame_meta_fn`` is an optional callable ``(animation, frame_idx,
    nframes) -> dict``. When provided, the returned dict is merged
    into each frame's per-rect metadata, so callers can attach
    anchors, weapon-specific rig data, etc.

    ``auto_crop`` (default ``True``) computes the union alpha bbox
    across EVERY rendered frame and crops every frame (plus the
    canonical) to that bbox + ``crop_margin``. The resulting frame
    size hugs the actual art instead of relying on the caller to
    guess a tight ``frame_size``. Any positional anchors that
    ``frame_meta_fn`` reported under a top-level ``"anchors"`` key
    are automatically translated by the crop offset so the
    coordinates stay correct in the cropped frame.

    ``animation_key_map`` (optional) opts a sheet into publishing
    AUTHORITATIVE per-animation hurtboxes. Bosses look these up by a
    GENERIC gameplay key (``rest`` / ``side_sweep`` / ``floor_slam`` /
    ``spike_halo`` / ``dash_echo`` / ``eye_beam`` / ``hit`` / ``death``),
    NOT the sheet's own row names — so pass ``{row_name: gameplay_key}``.
    Each mapped row emits ``body_metrics.animations[gameplay_key].hurtbox``
    = the row's union alpha bbox (cropped-frame coords), so the player's
    attacks register on the per-pose body instead of the coarse idle bbox.
    Rows with no mapping are skipped. ``attack_hitboxes`` (optional,
    keyed by the same gameplay keys) supplies authored attack-damage
    rects, merged in as ``animations[key].hitbox`` — for boss attacks
    whose damage geometry the sprite author wants to pin.

    ``pose_bodies`` says WHERE this character's per-pose gameplay body comes
    from, and it exists because the two answers were sharing one field:

    ``"art"`` (default)
        each mapped row publishes its union alpha bbox, so the body follows the
        drawing pose by pose. Right for a silhouette that changes SHAPE — the
        snake that withdraws into a cardboard box is a long low serpent in
        ``walk`` and a small cube in ``boxed_idle`` because its art is.
    ``"authored"``
        publish no per-animation hurtbox at all; the one authored
        ``body_pixel_bbox`` is the body in every pose. Right for a rigid
        character whose limbs move but whose BODY does not — which is most of
        them.

    ⛔ **why this is a declaration and not a default.** The runtime's
    ``BodyMetrics::pose_body_bbox`` prefers a per-animation hurtbox and falls
    back to the static box, and its docstring calls that fallback *"the whole
    answer for the common characters whose silhouette barely moves"*. But the
    per-animation boxes are MEASURED — alpha unions, motion smear included —
    while the static one may be AUTHORED, and emitting the measured one
    unconditionally meant the authored box could never win. Player robot v3
    authors a ``57x91`` body and their measured rows include a ``128``-wide
    ``block`` and a ``143``-wide ``dash``; a body driven by those inflates every
    time they flourish. The fallback was unreachable, not unused.
    """
    if _CANONICAL_ONLY.get():
        return _render_canonical_only(source, Path(out_dir))

    target = source.target
    rows = source.rows
    render_fn = source.render_fn
    frame_size = source.frame_size
    label_width = source.label_width
    frame_meta_fn = source.frame_meta_fn
    auto_crop = source.auto_crop
    crop_margin = source.crop_margin
    actor_metadata = source.actor_metadata()
    body_metrics_fn = source.body_metrics_fn
    sheet_tuning = source.sheet_tuning
    animation_key_map = source.animation_key_map
    attack_hitboxes = source.attack_hitboxes(source.frame_size)
    hurtbox_parts = source.hurtbox_parts(source.frame_size)
    frame_padding = _normalize_frame_padding(getattr(source, "frame_padding", None))
    pad_left, pad_top, pad_right, pad_bottom = frame_padding
    max_sheet_dimension = source.max_sheet_dimension
    trim = source.trim
    # `getattr`, because the recipe fields are optional on the FrameSource
    # protocol and a source predating this one means the old behaviour.
    pose_bodies = getattr(source, "pose_bodies", "art")
    if pose_bodies not in ("art", "authored"):
        raise ValueError(
            f"{target}: pose_bodies must be 'art' or 'authored', got {pose_bodies!r}"
        )

    fw, fh = frame_size

    # Packing / trim policy is data-driven (registry/pack_groups.py), keyed by
    # the target. A caller may still force `trim` explicitly (e.g. a rigged doc
    # honouring a per-frame opt-out); `None` ⇒ take the target's policy.
    policy = policy_for(target)
    if trim is None:
        trim = policy.trim

    # ---- Pass 1: render every frame + metadata into memory. -------------
    # We need all frames in hand before we can compute the union alpha
    # bbox for auto-crop.
    rendered_rows: List[Tuple[str, int, int, List[Tuple[Image.Image, dict]]]] = []
    progress_value = os.environ.get("AMBITION_SPRITE_PROGRESS", "0").strip().lower()
    progress_enabled = progress_value not in {"", "0", "false", "no", "off"}
    slow_frame_seconds = float(os.environ.get("AMBITION_SPRITE_SLOW_FRAME_SECONDS", "1.0"))
    total_frames = sum(nframes for _anim, nframes, _duration in rows)
    sheet_started = time.perf_counter()
    row_durations: List[float] = []
    render_seconds = 0.0
    metadata_seconds = 0.0
    frames_completed = 0

    def progress(message: str) -> None:
        if progress_enabled:
            print(f"[sheet:{target}] {message}", flush=True)

    progress(
        f"start | {len(rows)} animations | {total_frames} frames | "
        f"frame={fw}x{fh} | trim={trim}"
    )
    progress("phase render: begin")

    for row_idx, (anim, nframes, duration_ms) in enumerate(rows):
        row_started = time.perf_counter()
        row_render_seconds = 0.0
        row_metadata_seconds = 0.0
        progress(
            f"animation {row_idx + 1}/{len(rows)}: {anim} | "
            f"{nframes} frames @ {duration_ms}ms"
        )
        frames_data: List[Tuple[Image.Image, dict]] = []
        for frame_idx in range(nframes):
            frame_started = time.perf_counter()
            render_started = frame_started
            frame = render_fn(anim, frame_idx, nframes)
            render_elapsed = time.perf_counter() - render_started
            render_seconds += render_elapsed
            row_render_seconds += render_elapsed
            if frame.mode != "RGBA":
                frame = frame.convert("RGBA")
            frame = _pad_rgba_frame(frame, frame_padding)
            meta = {}
            if frame_meta_fn is not None:
                metadata_started = time.perf_counter()
                extra = frame_meta_fn(anim, frame_idx, nframes)
                metadata_elapsed = time.perf_counter() - metadata_started
                metadata_seconds += metadata_elapsed
                row_metadata_seconds += metadata_elapsed
                if extra:
                    meta = dict(extra)
                    if pad_left or pad_top:
                        meta = _shift_xy_payload(meta, pad_left, pad_top)
            frames_data.append((frame, meta))
            frames_completed += 1
            frame_elapsed = time.perf_counter() - frame_started
            if progress_enabled and frame_elapsed >= slow_frame_seconds:
                progress(
                    f"  slow frame {anim} {frame_idx + 1}/{nframes}: "
                    f"{frame_elapsed:.2f}s "
                    f"(render {render_elapsed:.2f}s, meta "
                    f"{(metadata_elapsed if frame_meta_fn is not None else 0.0):.2f}s)"
                )
        rendered_rows.append((anim, nframes, duration_ms, frames_data))
        row_duration = time.perf_counter() - row_started
        row_durations.append(row_duration)
        remaining = len(rows) - row_idx - 1
        rolling = sum(row_durations[-5:]) / len(row_durations[-5:])
        elapsed = time.perf_counter() - sheet_started
        progress(
            f"  done {anim} in {row_duration:.2f}s | "
            f"render={row_render_seconds:.2f}s meta={row_metadata_seconds:.2f}s | "
            f"frames {frames_completed}/{total_frames} | elapsed {elapsed:.1f}s | "
            f"row-eta {rolling * remaining:.1f}s"
        )
        profile_checkpoint(f"{target}:{anim}")

    progress(
        f"phase render: done in {time.perf_counter() - sheet_started:.2f}s | "
        f"render calls={render_seconds:.2f}s | metadata calls={metadata_seconds:.2f}s"
    )
    profile_checkpoint(f"{target}:render-pass", force=True)
    # Canonical pose: reuse the already-rendered first-row frame instead of
    # invoking the target renderer a second time. Most idle cycles start at a
    # neutral pose, so frame 1 has a touch more character; single-frame rows
    # fall back to frame 0. The copy keeps subsequent cropping independent.
    canon_index = min(1, rows[0][1] - 1)
    canonical_raw = rendered_rows[0][3][canon_index][0].copy()
    actor_metadata = _translate_actor_metadata(actor_metadata, pad_left, pad_top)
    attack_hitboxes = _translate_attack_hitboxes(attack_hitboxes, pad_left, pad_top)
    fw += pad_left + pad_right
    fh += pad_top + pad_bottom

    # ---- Auto-crop pass (optional) --------------------------------------
    # Union alpha bbox across every frame in the sheet AND the canonical.
    # Cropping uniformly means each frame retains identical dimensions —
    # required for the spritesheet grid to tile correctly — and the
    # canonical also gets the same crop so still poses and animated
    # frames are visually consistent.
    crop_started = time.perf_counter()
    progress(f"phase crop: begin | enabled={auto_crop}")
    if auto_crop:
        union_bbox: Optional[List[int]] = None
        all_frames_iter = []
        for _, _, _, frames_data in rendered_rows:
            all_frames_iter.extend(f for (f, _) in frames_data)
        all_frames_iter.append(canonical_raw)
        for frame in all_frames_iter:
            alpha = frame.getchannel("A")
            bbox = alpha.getbbox()
            if bbox is None:
                continue
            if union_bbox is None:
                union_bbox = list(bbox)
            else:
                union_bbox[0] = min(union_bbox[0], bbox[0])
                union_bbox[1] = min(union_bbox[1], bbox[1])
                union_bbox[2] = max(union_bbox[2], bbox[2])
                union_bbox[3] = max(union_bbox[3], bbox[3])

        if union_bbox is not None:
            crop_x = max(0, union_bbox[0] - crop_margin)
            crop_y = max(0, union_bbox[1] - crop_margin)
            crop_x1 = min(fw, union_bbox[2] + crop_margin)
            crop_y1 = min(fh, union_bbox[3] + crop_margin)
            new_fw = crop_x1 - crop_x
            new_fh = crop_y1 - crop_y

            cropped_rows: List[
                Tuple[str, int, int, List[Tuple[Image.Image, dict]]]
            ] = []
            for anim, nframes, duration_ms, frames_data in rendered_rows:
                new_data: List[Tuple[Image.Image, dict]] = []
                for frame, meta in frames_data:
                    cropped = frame.crop((crop_x, crop_y, crop_x1, crop_y1))
                    # Translate any positional anchors in `meta.anchors`
                    # by the crop offset so the metadata coordinates
                    # match the cropped frame. Non-anchor fields
                    # (`forward` unit vector, `blade_angle_deg`, …)
                    # pass through unchanged.
                    if meta and "anchors" in meta and isinstance(meta["anchors"], dict):
                        new_anchors = {}
                        for name, pos in meta["anchors"].items():
                            if isinstance(pos, dict) and "x" in pos and "y" in pos:
                                new_anchors[name] = {
                                    "x": round(pos["x"] - crop_x, 2),
                                    "y": round(pos["y"] - crop_y, 2),
                                }
                            else:
                                new_anchors[name] = pos
                        meta = {**meta, "anchors": new_anchors}
                    new_data.append((cropped, meta))
                cropped_rows.append((anim, nframes, duration_ms, new_data))
            rendered_rows = cropped_rows
            canonical_raw = canonical_raw.crop((crop_x, crop_y, crop_x1, crop_y1))
            fw, fh = new_fw, new_fh
    progress(f"phase crop: done in {time.perf_counter() - crop_started:.2f}s | frame={fw}x{fh}")

    # Semantic frame-publication seam: capture tooling (see
    # authoring/auto_capture.py) registers a hook here, AFTER the uniform
    # auto-crop, so a vector recording is associated with the EXACT frame
    # image being published — same coordinate system as the manifest, never
    # inferred from image creation order.
    capture_started = time.perf_counter()
    if FRAME_CAPTURE_HOOK is not None:
        progress("phase capture-hook: begin")
        for anim, nframes, _duration_ms, frames_data in rendered_rows:
            for frame_idx, (frame, _meta) in enumerate(frames_data):
                FRAME_CAPTURE_HOOK(target, anim, frame_idx, frame)
        progress(f"phase capture-hook: done in {time.perf_counter() - capture_started:.2f}s")

    # ---- Pass 2: assemble the spritesheet from the (cropped) frames. ----
    #
    # A combined LABELED PREVIEW (one tall grid image, human-only — never a GPU
    # texture, never installed) is always built so reviewers can see every row.
    # The actual GPU page images come from one of two layouts:
    #   - trim=True : alpha-trim every frame + MaxRects-pack the animations onto
    #     tight pages (the professional packer; reclaims the 84-97% transparent
    #     margins). Each animation stays on one page so the per-row page model
    #     holds; frames carry a trim `off` so the runtime repositions them.
    #   - trim=False: the legacy one-animation-per-row grid, split into page
    #     images only when it would exceed the GPU texture limit. Byte-identical
    #     to the pre-packer output for every existing (non-trimmed) target.
    first = rendered_rows[0][3][0][0].copy()

    layout_started = time.perf_counter()
    progress("phase layout/pack: begin")
    page_sheets, rows_meta, num_pages = layout_sheet_rows(
        target,
        rendered_rows,
        fw,
        fh,
        label_width=label_width,
        trim=trim,
        max_dim=max_sheet_dimension,
        page_size=policy.page_size,
    )
    progress(
        f"phase layout/pack: done in {time.perf_counter() - layout_started:.2f}s | "
        f"pages={num_pages}"
    )
    profile_checkpoint(f"{target}:layout", force=True)

    # The untrimmed runtime pages already contain the complete labeled grid.
    # Build the human preview by flattening and vertically stitching those
    # pages rather than drawing every label and compositing every frame twice.
    # Trimmed pages use packed frame geometry, so they still need the explicit
    # logical-row preview path.
    preview_started = time.perf_counter()
    progress("phase preview: begin")
    if not trim:
        preview_w = max(page.width for page in page_sheets)
        preview_h = sum(page.height for page in page_sheets)
        preview = Image.new("RGBA", (preview_w, preview_h), (43, 33, 40, 255))
        preview_y = 0
        for page in page_sheets:
            preview.alpha_composite(page, (0, preview_y))
            preview_y += page.height
    else:
        preview = _trimmed_labeled_preview(rendered_rows, fw, fh, label_width)
        preview_w, preview_h = preview.size
    progress(
        f"phase preview: done in {time.perf_counter() - preview_started:.2f}s | "
        f"preview={preview_w}x{preview_h}"
    )

    can = canonical_raw
    can_bg = Image.new("RGBA", (fw, fh), (43, 33, 40, 255))
    can_bg.alpha_composite(can, (0, 0))

    canonical_path = out_dir / f"{target}_canonical.png"
    canonical_transparent_path = out_dir / f"{target}_canonical_transparent.png"
    sheet_path = out_dir / f"{target}_spritesheet.png"
    yaml_path = out_dir / f"{target}_spritesheet.yaml"
    ron_path = out_dir / f"{target}_spritesheet.ron"
    preview_path = out_dir / f"{target}_preview_labeled.png"

    # Page 0 → `<target>_spritesheet.png`; extra pages → `.1.png`, `.2.png`, …
    image_write_started = time.perf_counter()
    progress("phase image-write: begin")
    page_image_names = [sheet_path.name]
    for k in range(1, num_pages):
        page_image_names.append(f"{target}_spritesheet.{k}.png")
    can_bg.save(canonical_path, compress_level=1)
    can.save(canonical_transparent_path)
    for img, name in zip(page_sheets, page_image_names):
        img.save(out_dir / name)
    preview.save(preview_path, compress_level=1)
    progress(f"phase image-write: done in {time.perf_counter() - image_write_started:.2f}s")

    metrics_started = time.perf_counter()
    progress("phase metadata: begin")
    body_metrics = alpha_bbox_metrics(first or can)
    if body_metrics_fn is not None:
        # Optional target-authored override for sheets whose visible alpha bbox
        # deliberately includes non-body adornments (for example a hat, halo, or
        # carried prop). The default remains alpha-bbox driven so existing
        # generators keep their current conventions; targets that pass this hook
        # can keep gameplay hurtboxes tight to the true character body while the
        # rendered frame still includes decorations.
        body_metrics = body_metrics_fn(fw, fh)
        # **Say which of the two rectangles this is.** `body_pixel_bbox` means
        # "the alpha extent of the drawn art" by default and "the gameplay body"
        # when a target authors one, and a consumer could not tell them apart —
        # so a runtime that wanted the body had no way to ask for it, and one
        # that scaled by the art got a hat and a pair of outstretched arms. The
        # flag is only ever emitted TRUE; its absence is the measured default.
        body_metrics = {**body_metrics, "authored_body": True}

    # Authoritative per-animation hurtboxes (+ optional authored hitboxes), so a
    # boss can register hits on the per-pose body instead of the coarse idle
    # bbox. Keyed by GENERIC gameplay keys (see `animation_key_map` in the
    # docstring) because the boss combat looks animations up that way, not by the
    # sheet's row names. A row's hurtbox is the union alpha bbox across its
    # frames, in cropped-frame coords (same space as `body_pixel_bbox`).
    if animation_key_map:
        anim_metrics = {}
        for anim, _nframes, _duration_ms, frames_data in rendered_rows:
            key = animation_key_map.get(anim)
            if key is None:
                continue
            union = None
            for frame, _meta in frames_data:
                bbox = frame.getchannel("A").getbbox()
                if bbox is None:
                    continue
                union = (
                    list(bbox)
                    if union is None
                    else [
                        min(union[0], bbox[0]),
                        min(union[1], bbox[1]),
                        max(union[2], bbox[2]),
                        max(union[3], bbox[3]),
                    ]
                )
            entry = anim_metrics.setdefault(key, {})
            # An `authored` body still wants its per-animation HITBOXES — those
            # are declared, not measured, and they are the reason a rigid
            # character maps its rows at all. It is only the measured hurtbox
            # that would outrank the authored body.
            if hurtbox_parts and key in hurtbox_parts:
                entry["hurtbox"] = hurtbox_parts[key]
            elif union is not None and pose_bodies == "art":
                entry["hurtbox"] = {
                    "bbox": {
                        "x": int(union[0]),
                        "y": int(union[1]),
                        "w": int(union[2] - union[0]),
                        "h": int(union[3] - union[1]),
                    }
                }
            if attack_hitboxes and key in attack_hitboxes:
                entry["hitbox"] = attack_hitboxes[key]
        # Drop rows that produced no boxes (fully transparent + no hitbox).
        anim_metrics = {k: v for k, v in anim_metrics.items() if v}
        if anim_metrics:
            body_metrics = {**body_metrics, "animations": anim_metrics}

    progress(f"phase metadata: geometry done in {time.perf_counter() - metrics_started:.2f}s")

    manifest = {
        "target": target,
        "image": sheet_path.name,
        "label_width": label_width,
        "frame_width": fw,
        "frame_height": fh,
        "rows": rows_meta,
        "body_metrics": body_metrics,
    }
    # Multi-page sheets carry the full page list; single-page sheets omit it so
    # their RON stays byte-identical to the pre-paging emitter.
    if num_pages > 1:
        manifest["images"] = page_image_names
    publish_character_notes(manifest, actor_metadata)
    if sheet_tuning:
        # Emitted to the RON `tuning` field (ron_tuning reads `sheet_tuning`);
        # the runtime SheetRegistry uses it for in-game display size /
        # sampling instead of the DEFAULT_TUNING fallback.
        manifest["sheet_tuning"] = dict(sheet_tuning)
    sidecar_started = time.perf_counter()
    progress("phase sidecars: begin")
    yaml_path.write_text(safe_dump(manifest, sort_keys=False, width=120))
    # Sidecar RON manifest consumed at runtime by the sandbox's
    # SheetRegistry. The YAML is the human-readable sidecar; RON is
    # what gameplay code deserializes. Keep both in lockstep — they
    # encode the same data structure.
    ron_path.write_text(_emit_sheet_ron(manifest))
    # Optional future-facing actor contract sidecar. Targets may pass
    # an `actor_metadata` dict to `build_sheet`; absent metadata is fine,
    # and the sidecar will record sparse inferred facts plus explicit gaps.
    actor_path = write_actor_contract_for_tackon(
        target=target,
        image_out=sheet_path,
        sheet_ron_out=ron_path,
        manifest=manifest,
        actor_metadata=actor_metadata,
    )
    # Surface the most common silent-publish-failure mode (character
    # sheets that lack any Idle alias and would render as a
    # colored-rectangle placeholder in-game) as a stderr warning so
    # the renderer author sees it during `regen_sprites.sh`.
    warning = diagnose_idle_coverage(target, [name for name, _, _ in rows])
    if warning:
        import sys as _sys

        print(warning, file=_sys.stderr)
    progress(f"phase sidecars: done in {time.perf_counter() - sidecar_started:.2f}s")
    progress(f"complete in {time.perf_counter() - sheet_started:.2f}s")
    profile_checkpoint(f"{target}:complete", force=True)
    return {
        "canonical": canonical_path,
        "canonical_transparent": canonical_transparent_path,
        "spritesheet": sheet_path,
        "yaml": yaml_path,
        "ron": ron_path,
        "actor": actor_path,
        "preview": preview_path,
    }


# RON manifest emission is unified in core.manifest_ron (one writer for both
# spines). These aliases keep the names callers/tests import.
_ron_sheet_record = record_to_ron
_ron_tuning = ron_tuning


def _emit_sheet_ron(manifest):
    """Serialize a manifest to the `Vec<SheetRecord>` RON the game reads."""
    return records_to_ron(manifest["target"], [manifest])


@profile
def write_canonical(
    target: str,
    rows: List[Tuple[str, int, int]],
    render_fn,
    out_dir: Path,
    *,
    frame_size: Tuple[int, int] = BASE_FRAME,
    crop_margin: int = 4,
    frame_padding=None,
) -> Path:
    """Render ONLY the canonical frame for ``target`` and save it.

    Companion to [`build_sheet`] for callers that want just the
    canonical pose without paying for the full sheet build. Renders
    one frame (first row, frame index 1 — same pose `build_sheet` uses
    for its `*_canonical_transparent.png` side-output), auto-crops to
    the alpha bbox + ``crop_margin``, and saves it as a transparent
    PNG to ``out_dir/{target}_canonical_transparent.png``.

    Returns the saved path. This is the function each tack-on target's
    ``render_canonical(out_dir, **opts)`` hook should call.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"{target}: cannot render canonical with no rows")
    anim, nframes, _duration_ms = rows[0]
    frame_idx = min(1, nframes - 1)
    img = render_fn(anim, frame_idx, nframes)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img = _pad_rgba_frame(img, _normalize_frame_padding(frame_padding))
    bbox = img.getchannel("A").getbbox()
    if bbox is not None:
        x1, y1, x2, y2 = bbox
        x1 = max(0, x1 - crop_margin)
        y1 = max(0, y1 - crop_margin)
        x2 = min(img.width, x2 + crop_margin)
        y2 = min(img.height, y2 + crop_margin)
        img = img.crop((x1, y1, x2, y2))
    # Silence unused-arg warning while keeping the signature future-
    # proof for callers that want to pass through frame_size for a
    # custom pre-crop pipeline.
    del frame_size
    out = out_dir / f"{target}_canonical_transparent.png"
    img.save(out)
    return out
