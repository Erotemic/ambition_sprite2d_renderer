from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from PIL import Image, ImageColor, ImageDraw

from ..registry.character_generators import get_generator
from ..profiling import profile
from .actor_contract import write_actor_contract_for_adapter
from ..registry import CharacterJob
from ..registry.pack_groups import policy_for
from ..core.measure import measure_body_metrics
from ..core.manifest_ron import records_to_ron, render_adapter, ron_tuning


def _parse_bg(value: str):
    if str(value).lower() == "transparent":
        return (0, 0, 0, 0)
    r, g, b = ImageColor.getrgb(value)
    return (r, g, b, 255)


def _measure_body_extent(frame: Image.Image) -> Dict[str, Any] | None:
    """Body bbox + feet anchor for one frame. Thin shim over the canonical
    measurement in :mod:`ambition_sprite2d_renderer.core.measure` (the one
    home for "measure by default")."""
    return measure_body_metrics(frame)


def _apply_body_inset(bbox: Dict[str, int], inset: Dict[str, float]) -> Dict[str, int]:
    """Shrink a pixel bbox by per-edge fractions of its own size.

    ``inset`` keys (all optional, default 0): ``left``/``right`` as a fraction
    of width, ``top``/``bottom`` as a fraction of height. The origin moves in by
    the left/top trim; the result never has a non-positive dimension. Used to
    derive an authored gameplay body tighter than the measured alpha box — see
    ``CharacterGenerator.body_inset``."""
    left = float(inset.get("left", 0.0))
    right = float(inset.get("right", 0.0))
    top = float(inset.get("top", 0.0))
    bottom = float(inset.get("bottom", 0.0))
    w, h = int(bbox["w"]), int(bbox["h"])
    return {
        "x": int(bbox["x"]) + int(round(w * left)),
        "y": int(bbox["y"]) + int(round(h * top)),
        "w": max(1, int(round(w * (1.0 - left - right)))),
        "h": max(1, int(round(h * (1.0 - top - bottom)))),
    }


# Pixels of safety padding kept around the union bbox before cropping. Anti-
# aliased character edges are only slightly transparent, so without a small
# pad bilinear sampling could clip them. Two pixels is enough at the current
# 128px source frames.
_DEFAULT_CROP_PADDING = 2


@profile
def build_spritesheet(job: CharacterJob) -> Tuple[List[Image.Image], Dict[str, Any]]:
    """Render every frame at the configured canvas size, then crop the entire
    sheet to the *union* of all opaque-pixel bboxes across every frame.

    Uniform per-sheet cropping (rather than per-frame) keeps the character
    anchored consistently across animations: a wide-arm spike_halo pose and a
    compact rest pose share the same pixel-space frame so the runtime can
    place sprites at a single fixed anchor without compensating for shifting
    bbox origins. The downside is that the crop only saves the margin that
    *every* animation can spare; tall jumps and wide attacks pull the union
    out toward the original canvas size.

    The returned manifest carries the cropped frame dimensions in the
    standard `frame_width`/`frame_height` fields, plus a `crop` block that
    records the original canvas size and crop offset for debugging or for
    runtime loaders that need the unpadded dimensions.
    """
    generator = get_generator(job.target)
    spec = generator.sample_spec(job)
    animations = generator.animations()
    selected = [a for a in job.animations if a in animations]
    missing = [a for a in job.animations if a not in animations]
    if missing:
        raise KeyError(
            f"unsupported animations for {job.target}: {missing}; available={sorted(animations)}"
        )
    # Render at `render_scale` x the authored canvas so the published texture
    # has more native pixels (the toon generator scales its 128-base design to
    # the frame width, so a bigger canvas = a bigger-drawn, higher-res
    # character). Display size in game is collision-driven and aspect-only, so
    # this only sharpens — it never changes how big the sprite appears.
    render_scale = max(1.0 / 64.0, float(getattr(job.render, "render_scale", 1.0)))
    src_fw = max(1, round(job.render.frame_width * render_scale))
    src_fh = max(1, round(job.render.frame_height * render_scale))
    label_w = max(0, job.render.label_width)
    border = max(0, job.render.border)

    # Pass 1: render every frame at full canvas size and accumulate the
    # union of opaque-pixel bboxes.
    rendered: List[List[Image.Image]] = []
    union_min_x, union_min_y = src_fw, src_fh
    union_max_x, union_max_y = 0, 0
    any_visible = False
    for animation in selected:
        info = animations[animation]
        row_frames: List[Image.Image] = []
        for frame_index in range(info["frames"]):
            frame = generator.render_frame(
                spec, animation, frame_index, (src_fw, src_fh), job
            )
            row_frames.append(frame)
            bbox = frame.getbbox()
            if bbox is not None:
                any_visible = True
                x_min, y_min, x_max, y_max = bbox
                union_min_x = min(union_min_x, x_min)
                union_min_y = min(union_min_y, y_min)
                union_max_x = max(union_max_x, x_max)
                union_max_y = max(union_max_y, y_max)
        rendered.append(row_frames)

    crop_padding = max(
        0, int(getattr(job.render, "crop_padding", _DEFAULT_CROP_PADDING))
    ) * max(1, round(render_scale))
    if not getattr(job.render, "crop", True):
        crop_min_x, crop_min_y = 0, 0
        crop_max_x, crop_max_y = src_fw, src_fh
    elif any_visible:
        crop_min_x = max(0, union_min_x - crop_padding)
        crop_min_y = max(0, union_min_y - crop_padding)
        crop_max_x = min(src_fw, union_max_x + crop_padding)
        crop_max_y = min(src_fh, union_max_y + crop_padding)
    else:
        # Defensive fallback: completely transparent input keeps the original
        # canvas size so downstream code never sees a zero-sized frame.
        crop_min_x, crop_min_y = 0, 0
        crop_max_x, crop_max_y = src_fw, src_fh
    fw = crop_max_x - crop_min_x
    fh = crop_max_y - crop_min_y

    # Pass 2: crop every frame to the logical box, gather per-animation source
    # alpha bboxes (hurtboxes) + the reference pose, then lay the frames out.
    #   render.trim → alpha-trim + MaxRects-pack every frame onto tight square
    #     pages (the professional packer; frames carry a `page` + trim `off`).
    #   otherwise → the legacy one-animation-per-labeled-row grid, split into
    #     page images only when it would exceed the GPU texture limit. Byte-
    #     identical to the pre-packer output for untrimmed targets.
    # Packing / trim policy is data-driven (see registry/pack_groups.py), keyed
    # by the target. Generator targets all render through the trim-aware
    # CharacterAnimator path, so the default policy packs them.
    policy = policy_for(job.target)
    max_dim = policy.max_dim
    trim = policy.trim
    page_size = policy.page_size
    manifest: Dict[str, Any] = {
        "target": job.target,
        "name": job.name,
        "output_name": getattr(job, "output_name", None),
        "seed": job.seed,
        "archetype": job.archetype,
        "variant": job.variant,
        "held_item": job.held_item,
        "faction": job.faction,
        "role": job.role,
        "music_cue": job.music_cue,
        "tags": list(job.tags),
        "sheet_tuning": dict(job.sheet_tuning)
        if getattr(job, "sheet_tuning", None) is not None
        else None,
        "frame_width": fw,
        "frame_height": fh,
        "label_width": label_w,
        "border": border,
        "spec": generator.spec_dict(spec),
        "crop": {
            "source_frame_width": src_fw,
            "source_frame_height": src_fh,
            "offset": {"x": int(crop_min_x), "y": int(crop_min_y)},
            "enabled": bool(getattr(job.render, "crop", True)),
            "padding_px": crop_padding,
        },
    }
    body_metric_frame: Image.Image | None = None
    # Per-animation union alpha bboxes in **source canvas** coords (before the
    # sheet-wide crop) → per-animation hurtboxes. Layout-independent.
    anim_union_bbox_src: Dict[str, Tuple[int, int, int, int] | None] = {}
    cropped_rows: List[List[Image.Image]] = []
    for row_idx, animation in enumerate(selected):
        anim_bbox: Tuple[int, int, int, int] | None = None
        row_imgs: List[Image.Image] = []
        for src_frame in rendered[row_idx]:
            cropped = src_frame.crop((crop_min_x, crop_min_y, crop_max_x, crop_max_y))
            row_imgs.append(cropped)
            src_bbox = src_frame.getbbox()
            if src_bbox is not None:
                anim_bbox = (
                    src_bbox
                    if anim_bbox is None
                    else (
                        min(anim_bbox[0], src_bbox[0]),
                        min(anim_bbox[1], src_bbox[1]),
                        max(anim_bbox[2], src_bbox[2]),
                        max(anim_bbox[3], src_bbox[3]),
                    )
                )
            if body_metric_frame is None:
                body_metric_frame = cropped
        cropped_rows.append(row_imgs)
        anim_union_bbox_src[animation] = anim_bbox

    # One layout seam for both spines (see sheet_build.layout_sheet_rows): trim
    # → alpha-trim + MaxRects-pack; untrimmed → the legacy labeled grid. Every
    # adapter generator is trim=True, so this packs exactly as the former inline
    # pack_frames did — the RON and page PNGs are byte-identical (the shared
    # emitter ignores the per-rect index/duration the old inline path carried).
    from .sheet_build import layout_sheet_rows

    rendered_rows = [
        (
            animation,
            len(cropped_rows[row_idx]),
            animations[animation]["duration_ms"],
            [(img, {}) for img in cropped_rows[row_idx]],
        )
        for row_idx, animation in enumerate(selected)
    ]
    pages, rows_meta, num_pages = layout_sheet_rows(
        job.target,
        rendered_rows,
        fw,
        fh,
        label_width=label_w,
        trim=trim,
        max_dim=max_dim,
        page_size=page_size,
    )
    manifest["rows"] = rows_meta
    manifest["pages"] = num_pages
    metrics = (
        _measure_body_extent(body_metric_frame)
        if body_metric_frame is not None
        else None
    )
    if metrics is not None:
        # Authored body-box inset (generator-declared): trim the measured alpha
        # box to the intended gameplay body so every character from this generator
        # shares a tighter collision / hurt body than its full silhouette.
        body_inset = generator.body_inset()
        if body_inset:
            metrics["body_pixel_bbox"] = _apply_body_inset(
                metrics["body_pixel_bbox"], body_inset
            )
        # Per-animation hurtbox: each animation's alpha-bbox in
        # cropped-frame coords (subtract the sheet crop offset).
        # Per-animation hitbox: generator-declared rects, also
        # translated to cropped-frame coords. Together they give
        # the gameplay layer a clean per-animation
        # {hurtbox, hitbox} pair for each row in the sheet.
        anim_metrics: Dict[str, Dict[str, Any]] = {}
        for animation, src_bbox in anim_union_bbox_src.items():
            entry: Dict[str, Any] = {}
            if src_bbox is not None:
                x0, y0, x1, y1 = src_bbox
                # Translate from source canvas → cropped frame.
                cx0 = max(0, x0 - crop_min_x)
                cy0 = max(0, y0 - crop_min_y)
                cw = min(fw, x1 - crop_min_x) - cx0
                ch = min(fh, y1 - crop_min_y) - cy0
                if cw > 0 and ch > 0:
                    entry["hurtbox"] = {
                        "bbox": {
                            "x": int(cx0),
                            "y": int(cy0),
                            "w": int(cw),
                            "h": int(ch),
                        }
                    }
                    # Same authored inset as the base body box, so a pose's
                    # hurtbox stays consistent with the tighter gameplay body.
                    if body_inset:
                        entry["hurtbox"]["bbox"] = _apply_body_inset(
                            entry["hurtbox"]["bbox"], body_inset
                        )
            anim_metrics[animation] = entry
        # Generator-declared per-animation hurtbox parts override
        # (head + body split for bosses, etc.). When present, the
        # parts REPLACE the auto-derived bbox above so the player's
        # attack registration only triggers on the central body —
        # not on cosmetic extensions like outstretched arms.
        # A raising hook is a bug in THIS generator: fail the render
        # rather than silently publishing auto-derived combat geometry.
        try:
            hurtboxes_by_anim = generator.hurtbox_parts((src_fw, src_fh))
        except Exception as ex:
            raise RuntimeError(
                f"{type(generator).__name__}.hurtbox_parts raised for "
                f"frame {src_fw}x{src_fh}: {ex!r}"
            ) from ex
        for anim_name, hurtbox in (hurtboxes_by_anim or {}).items():
            if not isinstance(hurtbox, dict):
                continue
            parts_in = hurtbox.get("parts")
            if not isinstance(parts_in, list) or not parts_in:
                continue
            cropped_parts = []
            for part in parts_in:
                if not isinstance(part, dict):
                    continue
                x = int(part.get("x", 0))
                y = int(part.get("y", 0))
                w = int(part.get("w", 0))
                h = int(part.get("h", 0))
                cx0 = max(0, x - crop_min_x)
                cy0 = max(0, y - crop_min_y)
                cw = min(fw, x + w - crop_min_x) - cx0
                ch = min(fh, y + h - crop_min_y) - cy0
                if cw > 0 and ch > 0:
                    cropped_parts.append(
                        {
                            "name": str(part.get("name", "")),
                            "x": int(cx0),
                            "y": int(cy0),
                            "w": int(cw),
                            "h": int(ch),
                        }
                    )
            if not cropped_parts:
                continue
            if anim_name not in anim_metrics:
                anim_metrics[anim_name] = {}
            # Replace the auto-derived single-bbox hurtbox with the
            # generator-declared multi-rect parts. Drop the bbox so
            # consumers (which prefer `parts` over `bbox`) get only
            # the authored shapes.
            anim_metrics[anim_name]["hurtbox"] = {"parts": cropped_parts}

        # Generator-declared per-animation hitboxes (attack damage
        # geometry). Translated source canvas → cropped frame.
        # Same fail-fast rule as hurtbox_parts above: a raising hook must
        # not silently publish a sheet whose attacks fall back to volume
        # math.
        try:
            hitboxes_by_anim = generator.attack_hitboxes((src_fw, src_fh))
        except Exception as ex:
            raise RuntimeError(
                f"{type(generator).__name__}.attack_hitboxes raised for "
                f"frame {src_fw}x{src_fh}: {ex!r}"
            ) from ex
        for anim_name, hitbox in (hitboxes_by_anim or {}).items():
            if anim_name not in anim_metrics:
                anim_metrics[anim_name] = {}
            hitbox_out: Dict[str, Any] = {}
            if isinstance(hitbox, dict):
                if isinstance(hitbox.get("bbox"), tuple):
                    x, y, w, h = hitbox["bbox"]
                    # Attack hitboxes are NOT clamped to the sprite frame.
                    # A melee box (Hollow-Knight nail-style) reaches out in
                    # FRONT of the body, disjoint from it and usually past
                    # the drawn sprite's edge. Translate into cropped-frame
                    # space but keep the authored extent so a forward box
                    # survives. (Hurtboxes ARE the body and stay frame-bound
                    # via the auto alpha-bbox path — different code.)
                    cx0 = int(x) - crop_min_x
                    cy0 = int(y) - crop_min_y
                    cw = int(w)
                    ch = int(h)
                    if cw > 0 and ch > 0:
                        hitbox_out["bbox"] = {
                            "x": int(cx0),
                            "y": int(cy0),
                            "w": int(cw),
                            "h": int(ch),
                        }
                # Optional convex polygon — an effect-conforming hitbox shape
                # (blade arc, cone). Translated source canvas -> cropped frame,
                # NOT clamped (like the attack bbox, it can reach past the body).
                # The runtime reads it as a CombatVolume::Convex.
                poly = hitbox.get("poly")
                if isinstance(poly, list) and len(poly) >= 3:
                    hitbox_out["poly"] = [
                        (float(px) - crop_min_x, float(py) - crop_min_y)
                        for px, py in poly
                    ]
                if isinstance(hitbox.get("parts"), list):
                    cropped_parts = []
                    for part in hitbox["parts"]:
                        if not isinstance(part, dict):
                            continue
                        x = int(part.get("x", 0))
                        y = int(part.get("y", 0))
                        w = int(part.get("w", 0))
                        h = int(part.get("h", 0))
                        cx0 = max(0, x - crop_min_x)
                        cy0 = max(0, y - crop_min_y)
                        cw = min(fw, x + w - crop_min_x) - cx0
                        ch = min(fh, y + h - crop_min_y) - cy0
                        if cw > 0 and ch > 0:
                            cropped_parts.append(
                                {
                                    "name": str(part.get("name", "")),
                                    "x": int(cx0),
                                    "y": int(cy0),
                                    "w": int(cw),
                                    "h": int(ch),
                                }
                            )
                    if cropped_parts:
                        hitbox_out["parts"] = cropped_parts
                # Optional per-frame active window: which frame indices
                # the attack hitbox is actually live on (e.g. [0] for a
                # hit-on-frame-0 swing). Absent = live on every frame
                # (back-compatible). Consumed by the debug-hitbox overlay
                # and available to the runtime for timing agreement.
                active = hitbox.get("active_frames")
                if isinstance(active, (list, tuple)) and active:
                    hitbox_out["active_frames"] = [int(i) for i in active]
            if hitbox_out:
                anim_metrics[anim_name]["hitbox"] = hitbox_out
        # Drop animations with no data (rest, hit, death may end up empty
        # if the adapter declared no hitbox and the alpha bbox was empty).
        anim_metrics = {k: v for k, v in anim_metrics.items() if v}
        if anim_metrics:
            metrics["animations"] = anim_metrics
        manifest["body_metrics"] = metrics
    return pages, manifest


def _page_image_names(image_out: Path, num_pages: int) -> List[str]:
    """Filenames for each page image. Page 0 keeps the canonical
    ``<stem>_spritesheet.png`` name; later pages are siblings
    ``<stem>_spritesheet.1.png``, ``.2.png``, … in the same directory, so the
    runtime loads them by name relative to page 0."""
    base = image_out.name
    if num_pages <= 1:
        return [base]
    stem, _, ext = base.rpartition(".")
    return [base] + [f"{stem}.{k}.{ext}" for k in range(1, num_pages)]


@profile
def write_spritesheet(
    job: CharacterJob,
    image_out: str | Path,
    manifest_out: str | Path | None = None,
    *,
    source_config: str | Path | None = None,
) -> Tuple[Path, Path]:
    image_out = Path(image_out)
    if manifest_out is None:
        manifest_out = image_out.with_suffix(".yaml")
    manifest_out = Path(manifest_out)
    image_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    pages, manifest = build_spritesheet(job)
    # Page 0 → `<stem>_spritesheet.png`; extra pages → `.1.png`, `.2.png`, …
    page_names = _page_image_names(image_out, len(pages))
    for img, name in zip(pages, page_names):
        img.save(image_out.parent / name)
    # Record the full page list so the YAML + RON sidecars carry `images`
    # (only emitted to RON when there's more than one page).
    if len(page_names) > 1:
        manifest["images"] = page_names
    with open(manifest_out, "w", encoding="utf8") as file:
        yaml.safe_dump(manifest, file, sort_keys=False)
    # Sidecar RON: same data, machine-readable shape for the sandbox's
    # SheetRegistry. The adapter pipeline's YAML is `animations:`-keyed,
    # so we translate to the row-ordered SheetRecord shape here. See
    # `sheet_build._emit_sheet_ron` for the tack-on equivalent.
    ron_path = manifest_out.with_suffix(".ron")
    manifest_for_sidecars = dict(manifest)
    manifest_for_sidecars["image"] = image_out.name
    ron_path.write_text(records_to_ron(manifest["target"], [manifest_for_sidecars]))
    # Optional future-facing runtime sidecar. Current sandbox builds ignore
    # this file, but publishing it now lets every adapter config start
    # declaring sparse actor/body/capability/action metadata without changing
    # the existing SheetRegistry contract.
    write_actor_contract_for_adapter(
        image_out=image_out,
        sheet_ron_out=ron_path,
        manifest=manifest_for_sidecars,
        job=job,
        source_config=source_config,
    )
    return image_out, manifest_out


# RON manifest emission is unified in core.manifest_ron (one writer for both
# spines). These aliases keep the names callers/tests import.
_adapter_manifest_to_ron = render_adapter
_adapter_tuning_to_ron = ron_tuning
