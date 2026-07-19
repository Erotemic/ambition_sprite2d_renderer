"""CLI command implementations.

Every ``draw_*`` pipeline function and ``_cmd_*`` argparse handler lives
here. The argparse wiring that dispatches to them is in ``parser.py``;
this module imports nothing from there (one-way: parser -> commands).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

from ..registry.character_generators import GENERATORS, get_generator
from ..profiling import profile
from ..yaml_io import safe_load
from ..authoring.canonical import (
    draw_canonical_of,
    render_canonical,
    write_canonicals,
    write_gallery,
)
from .console import print_canonical_outputs, print_path, print_paths
from rich import print as rich_print
from ..registry import CharacterJob, load_jobs
from ..authoring.faction_lineup import write_faction_lineup
from ..devtools.debug_hitboxes import render_debug_overlay
from ..authoring.sheet import write_spritesheet
from ..authoring.portrait import write_portrait_gallery
from ..registry import (
    CATEGORIES,
    DiscoveryReport,
    Target,
    discover_all_targets,
)
import time


def package_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def repo_root() -> Path:
    # <repo>/tools/ambition_sprite2d_renderer/ambition_sprite2d_renderer/cli/
    # commands.py -> repo root. Only meaningful for a checkout inside the
    # ambition repo (install/publish default destinations); AMBITION_REPO_ROOT
    # overrides for standalone checkouts.
    override = os.environ.get("AMBITION_REPO_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[4]


# Defaults are computed against the package, not the cwd, so the CLI works
# regardless of where the user runs it from.
DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent.parent / "configs"
DEFAULT_REVIEW_CONFIG_DIR = DEFAULT_CONFIG_DIR / "review"
DEFAULT_ASSET_DIR = package_dir() / "generated"
DEFAULT_FACTION_CONFIG = DEFAULT_CONFIG_DIR / "factions" / "music_factions.yaml"


def _render_progress_enabled() -> bool:
    value = os.environ.get("AMBITION_RENDER_PROGRESS")
    return value is not None and value.strip().lower() not in {
        "",
        "0",
        "false",
        "no",
        "off",
    }


def _render_progress(message: str) -> None:
    if _render_progress_enabled():
        print(message, flush=True)


# ---- Target registry ---------------------------------------------------------
#
# Unified discovery across every surface: tack-on Python modules under
# `targets/<category>/` AND YAML adapter configs under `configs/` /
# `configs/review/`. See `target_registry.discover_all_targets`.
#
# Adding a tack-on: drop a `.py` (or package dir) into the right
# category subdir. Adding an adapter target: drop a YAML config under
# `configs/` or `configs/review/`. Either way, no edit to this file
# is required.

_REPORT: DiscoveryReport = discover_all_targets()
_ALL_TARGETS: dict[str, Target] = _REPORT.targets


# Review configs whose generated spritesheets are loaded at runtime via
# the sandbox NPC sprite registry. `draw-all` skips `configs/review/`
# by design (those are art-iteration review jobs), but these specific
# ones produce assets the game needs. `draw-runtime-npcs` renders +
# installs them in one shot so a fresh checkout can boot with full
# NPC art without invoking `draw-character` ten times.
RUNTIME_REVIEW_NPCS: tuple[str, ...] = (
    "absurd_general",
    "architect",
    "erdish",
    "kernel_guide",
    "merchant_prototype",
    "oiler",
    "vault_keeper",
    # Cryptography crew batch 1 — Bob/Alice/Eve/Mallory/Trent/Judy.
    # See `docs/concepts/cryptography-crew.md` for the full canonical
    # roster. Batch 2 (Trudy/Craig/Sybil/Victor/Peggy/Walter/Olivia)
    # landed as toon-target sketches with phenotype variation; each
    # may be promoted to a bespoke template if a story room demands.
    "alice",
    "bob",
    "eve",
    "judy",
    "mallory",
    "trent",
    "trudy",
    "craig",
    "sybil",
    "victor",
    "peggy",
    "walter",
    "olivia",
)


def _get_target(name: str) -> Target:
    """Look up a target from the unified registry.

    If the name isn't registered but a matching file exists under
    ``targets/<category>/<name>.py``, surface the discovery warning for
    it (typically "no `render()` function") so the user knows *why*
    their file isn't registered, instead of just "unknown target."
    """
    if name in _ALL_TARGETS:
        return _ALL_TARGETS[name]
    # Look for a discovery warning matching this name. Warnings are
    # formatted as "<category>/<stem>: <reason>" so an `endswith` /
    # `:` split is enough to find the relevant one.
    for line in _REPORT.warnings:
        head, _, reason = line.partition(":")
        if head.endswith(f"/{name}"):
            raise SystemExit(
                f"error: target {name!r} is not registered.\n"
                f"  reason: {reason.strip()}\n"
                f"  location: {head.strip()}.py\n"
                f"  see `registry/discovery.py` for the Target protocol contract."
            )
    raise SystemExit(
        f"error: unknown target: {name!r}\n  run `list` to see the registered targets."
    )


def sandbox_sprites_dir() -> Path:
    return repo_root() / "crates" / "ambition_actors" / "assets" / "sprites"


def generated_dir(target_name: str) -> Path:
    return DEFAULT_ASSET_DIR / target_name


def _render_job_portraits(
    job: CharacterJob, stem: str, out_dir: str | Path
) -> List[Path]:
    """Render the standard portrait product for one config-backed job."""

    generator = get_generator(job.target)
    spec = generator.sample_spec(job)
    return list(
        generator.render_portraits(
            spec, job, target=stem, out_dir=str(Path(out_dir))
        )
    )


# ---- Adapter (character lab) commands -----------------------------------------


@profile
def draw_all(
    config_dir: str | Path = DEFAULT_CONFIG_DIR,
    out_dir: str | Path = DEFAULT_ASSET_DIR,
    *,
    jobs: list[tuple[Path, CharacterJob]] | None = None,
) -> List[Path]:
    out_dir = Path(out_dir)
    config_dir_path = Path(config_dir)
    runtime_stems = {
        "boss",
        "raid_enforcer",
        "goblin",
        "ninja",
        "ninja_leader",
        "player_robot",
        "robot",
        "sandbag",
    }
    default_runtime_dir = (
        config_dir_path.resolve() == Path(DEFAULT_CONFIG_DIR).resolve()
    )
    job_items = list(load_jobs(config_dir_path) if jobs is None else jobs)
    selected_jobs: list[tuple[Path, CharacterJob, str]] = []
    for path, job in job_items:
        # The default configs/ directory has accumulated a few older review
        # jobs for compatibility. Keep draw-all focused on the runtime sheets
        # so it stays quick and does not unexpectedly publish review variants.
        # Custom config dirs still render every .yaml they contain.
        config_stem = path.stem
        if default_runtime_dir and config_stem not in runtime_stems:
            continue
        selected_jobs.append((path, job, job.output_stem(path)))

    outputs: List[Path] = []
    total = len(selected_jobs)
    for index, (path, job, stem) in enumerate(selected_jobs, start=1):
        _render_progress(f"    [sheet {index}/{total}] {stem}")
        image_out = out_dir / f"{stem}_spritesheet.png"
        manifest_out = out_dir / f"{stem}_spritesheet.yaml"
        outputs.extend(
            write_spritesheet(job, image_out, manifest_out, source_config=path)
        )
        _render_progress(f"    [portrait {index}/{total}] {stem}")
        outputs.extend(_render_job_portraits(job, stem, out_dir))
    return outputs


@profile
def draw_review(
    config_dir: str | Path = DEFAULT_REVIEW_CONFIG_DIR,
    out_dir: str | Path = DEFAULT_ASSET_DIR / "review",
) -> List[Path]:
    # Scoped to `config_dir` — use the adapter-only `write_canonicals`
    # path rather than `draw_canonicals` (which now does the full
    # adapters + tack-ons + review-NPCs gallery and would balloon a
    # review-of-this-dir into a full-roster render).
    job_items = list(load_jobs(Path(config_dir)))
    _render_progress(f"    [draw-review] {len(job_items)} configured character(s)")
    outputs = draw_all(config_dir, out_dir, jobs=job_items)
    _render_progress("    [draw-review] canonical gallery pass")
    outputs += write_canonicals(
        config_dir,
        Path(out_dir) / "canonicals",
        jobs=job_items,
        progress=_render_progress_enabled(),
    )
    return outputs


@profile
def draw_canonicals(
    config_dir: str | Path = DEFAULT_CONFIG_DIR,
    out_dir: str | Path = DEFAULT_ASSET_DIR / "canonicals",
    *,
    adapters_only: bool = False,
) -> List[Path]:
    """Draw the full canonical gallery: adapters + tack-ons + review NPCs.

    Every canonical is drawn fresh by invoking the per-target renderer
    — does NOT read from any cached ``generated/<name>/`` files. Tiles
    are composited onto a consistent gallery backdrop with per-category
    section headers (Adapter targets, Review NPCs, Tack-on
    characters/props/tiles/icons) so it reads as one unified review piece.

    Set ``adapters_only=True`` for the legacy behavior that walks
    ``configs/*.yaml`` only (adapter targets, no tack-ons or review NPCs).
    """
    if adapters_only:
        return write_canonicals(config_dir, out_dir)
    outputs, warnings = write_gallery(out_dir, _ALL_TARGETS.values())
    for line in warnings:
        print(f"warning: {line}", file=sys.stderr)
    return outputs


def resolve_config_path(value: str | Path) -> Path:
    """Resolve a config name or path to a concrete ``Path``.

    Lookup order:

    1. If ``value`` is a path that exists, return it as-is.
    2. ``configs/<value>.yaml`` (main adapter rigs).
    3. ``configs/review/<value>.yaml`` (review NPCs).

    Raises ``FileNotFoundError`` with the search paths if no match.
    Lets callers pass a short name (``boss``,
    ``robot_guardian``, ``architect``) instead of the full
    ``ambition_sprite2d_renderer/configs/boss.yaml`` path.
    """
    candidate = Path(value)
    if candidate.exists():
        return candidate
    # Strip any extension the user typed so `boss.yaml` and `boss`
    # both work.
    stem = candidate.stem if candidate.suffix else candidate.name
    candidates = [
        DEFAULT_CONFIG_DIR / f"{stem}.yaml",
        DEFAULT_REVIEW_CONFIG_DIR / f"{stem}.yaml",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        f"config not found: {value!r}; tried {[str(p) for p in [candidate, *candidates]]}"
    )


@profile
def draw_character(
    config: str | Path, out_dir: str | Path = DEFAULT_ASSET_DIR
) -> List[Path]:
    """Render both review artifacts for one character config.

    This is the one-shot path for art iteration: it writes the canonical still
    frame used for visual review and the runtime spritesheet + YAML manifest
    used by the game.  It deliberately shares the same `CharacterJob` adapter
    path as `single` and `spritesheet`, so the canonical pose and the sheet are
    generated from the exact same spec.

    Canonical PNGs land in ``<out_dir>/canonicals/`` so they don't visually
    mix with the per-character spritesheet PNGs in ``<out_dir>/`` when an
    artist pages through the folder. Spritesheet + manifest stay at the
    top of ``<out_dir>`` because that's where the runtime asset loader
    looks for them.
    """
    config_path = Path(config)
    out_dir = Path(out_dir)
    job = CharacterJob.load(config_path)
    stem = job.output_stem(config_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    canonical_dir = out_dir / "canonicals"
    canonical_dir.mkdir(parents=True, exist_ok=True)
    canonical_out = canonical_dir / f"{stem}_canonical.png"
    render_canonical(job).save(canonical_out)

    sheet_out = out_dir / f"{stem}_spritesheet.png"
    manifest_out = out_dir / f"{stem}_spritesheet.yaml"
    image_out, yaml_out = write_spritesheet(
        job, sheet_out, manifest_out, source_config=config_path
    )
    actor_out = out_dir / f"{stem}_actor.ron"
    outputs = [canonical_out, image_out, yaml_out]
    if actor_out.exists():
        outputs.append(actor_out)
    outputs.extend(_render_job_portraits(job, stem, out_dir))
    return outputs


@profile
def draw_factions(
    config: str | Path = DEFAULT_FACTION_CONFIG,
    out_dir: str | Path = DEFAULT_ASSET_DIR / "factions",
) -> List[Path]:
    return write_faction_lineup(config, out_dir)


def _cmd_draw_all(args: argparse.Namespace) -> int:
    print_paths(draw_all(args.config_dir, args.out_dir))
    return 0


def _cmd_draw_review(args: argparse.Namespace) -> int:
    print_paths(draw_review(args.config_dir, args.out_dir))
    return 0


def _cmd_canonical(args: argparse.Namespace) -> int:
    """`canonical [<name>]` — draw one canonical, or the full gallery."""
    if args.target:
        target = _get_target(args.target)
        out = draw_canonical_of(target, args.out_dir)
        print_paths([out])
        return 0
    print_canonical_outputs(
        draw_canonicals(
            args.config_dir,
            args.out_dir,
            adapters_only=args.adapters_only,
        )
    )
    return 0


def _cmd_draw_character(args: argparse.Namespace) -> int:
    try:
        config_path = resolve_config_path(args.config)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    outputs = draw_character(config_path, args.out_dir)
    print_paths(outputs)
    if getattr(args, "debug_hitboxes", False):
        # Find the YAML sidecar in the outputs to feed to the
        # overlay. `draw_character` returns it as the third path
        # (canonical, sheet PNG, sheet YAML, optional actor RON).
        yaml_out = next((p for p in outputs if p.suffix == ".yaml"), None)
        if yaml_out is None:
            print(
                "warning: --debug-hitboxes set but no YAML manifest in outputs",
                file=sys.stderr,
            )
            return 0
        try:
            written = render_debug_overlay(yaml_out)
        except FileNotFoundError as e:
            print(f"error: debug overlay failed: {e}", file=sys.stderr)
            return 1
        print_path(written, prefix="  debug overlay: ")
    return 0


def _cmd_draw_factions(args: argparse.Namespace) -> int:
    print_paths(draw_factions(args.config, args.out_dir))
    return 0


def _cmd_portrait_gallery(args: argparse.Namespace) -> int:
    """Build a visual contact sheet from installed portrait products."""

    out, warnings = write_portrait_gallery(
        args.source_dir, args.out, columns=args.columns
    )
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print_path(out)
    return 0


def _cmd_ldtk_manifest(args: argparse.Namespace) -> int:
    """Emit the LDtk visual manifest for the published sprite sheets.

    Producer half of the sprite -> LDtk-editor bridge; the manifest is
    consumed by `ambition_ldtk_tools` `visual-manifest apply-manifest`.
    """
    from ..devtools.ldtk_manifest import build_manifest, write_manifest

    sprites_dir = Path(args.sprites_dir) if args.sprites_dir else sandbox_sprites_dir()
    out_path = Path(args.out) if args.out else sprites_dir / "ldtk_sprite_manifest.json"
    manifest = build_manifest(
        sprites_dir,
        repo_root=repo_root(),
        all_sheets=args.all_sheets,
    )
    write_manifest(manifest, out_path)
    if args.format == "json":
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print(
            f"wrote {out_path} "
            f"({len(manifest['tilesets'])} tilesets, "
            f"{len(manifest['entity_icons'])} entity icons)"
        )
    return 0


def _cmd_list_targets(args: argparse.Namespace) -> int:
    print(
        "# procedural generators (driven by configs/*.yaml — renders via draw-character / draw-all):"
    )
    for target in sorted(GENERATORS):
        generator = get_generator(target)
        print(f"  {target}: {', '.join(generator.default_animations())}")
    print("# registered targets (unified — works with render/install/canonical):")
    by_category: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    for name, tgt in _ALL_TARGETS.items():
        by_category.setdefault(tgt.category, []).append(name)
    for category in CATEGORIES:
        names = sorted(by_category.get(category, []))
        if not names:
            continue
        print(f"  [{category}]")
        for name in names:
            marker = (
                "  (runtime)"
                if category == "characters" and name in RUNTIME_REVIEW_NPCS
                else ""
            )
            print(f"    {name}{marker}")
    if _REPORT.warnings:
        print(
            "# warnings (files in targets/ that don't conform to the Target API):",
            file=sys.stderr,
        )
        for line in _REPORT.warnings:
            print(f"  {line}", file=sys.stderr)
    return 0


def _cmd_spritesheet(args: argparse.Namespace) -> int:
    job = CharacterJob.load(args.config)
    print_paths(
        write_spritesheet(
            job, args.output, args.manifest_out, source_config=args.config
        )
    )
    return 0


def _cmd_single(args: argparse.Namespace) -> int:
    job = CharacterJob.load(args.config)
    generator = get_generator(job.target)
    spec = generator.sample_spec(job)
    img = generator.render_single(spec, args.animation, args.frame_index, job)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output)
    print_paths([output])
    return 0


def _manifest_image_path(manifest_path: Path, manifest: dict) -> Path:
    image = (
        manifest.get("image")
        or manifest.get("spritesheet")
        or manifest_path.with_suffix(".png").name
    )
    image_path = Path(str(image))
    if not image_path.is_absolute():
        image_path = manifest_path.parent / image_path
    return image_path


def _manifest_page_images(manifest_path: Path, manifest: dict) -> dict[int, "object"]:
    """Open every page image of a sheet, keyed by page index.

    A multi-page (packed or grid-split) sheet lists its pages in
    ``images`` (0-indexed, ``page``/``fpage`` address into it); a
    single-page sheet only has ``image``. Missing files are skipped so a
    partially-published sheet still yields the pages it has."""
    from PIL import Image

    names = manifest.get("images") or [
        manifest.get("image")
        or manifest.get("spritesheet")
        or manifest_path.with_suffix(".png").name
    ]
    pages: dict[int, object] = {}
    for idx, name in enumerate(names):
        path = Path(str(name))
        if not path.is_absolute():
            path = manifest_path.parent / path
        if path.exists():
            pages[idx] = Image.open(path).convert("RGBA")
    return pages


def _frame_from_rect(rect: dict, pages: dict, fw: int | None, fh: int | None):
    """Reconstruct one logical frame from a sheet rect (packed or unpacked).

    Crops the (possibly alpha-trimmed) rect from its own page — ``fpage``
    for packed sheets, ``page`` for the grid layout, else page 0 — then
    pastes it at the trim offset ``off`` onto a transparent logical
    ``fw×fh`` canvas. So a trimmed rect and a full grid cell both yield a
    consistently-sized, anchored frame (no per-frame jitter in the GIF).
    Returns ``None`` if the rect's page image is unavailable."""
    from PIL import Image

    page_idx = int(rect.get("fpage", rect.get("page", 0)))
    sheet = pages.get(page_idx)
    if sheet is None:
        sheet = pages.get(0)
    if sheet is None:
        return None
    x, y, w, h = int(rect["x"]), int(rect["y"]), int(rect["w"]), int(rect["h"])
    crop = sheet.crop((x, y, x + w, y + h))
    off = rect.get("off") or (0, 0)
    ox, oy = int(off[0]), int(off[1])
    if fw and fh and (ox or oy or w != int(fw) or h != int(fh)):
        canvas = Image.new("RGBA", (int(fw), int(fh)), (0, 0, 0, 0))
        canvas.alpha_composite(crop, (ox, oy))
        return canvas
    return crop


def _animation_rows_from_manifest(
    manifest: dict,
) -> list[tuple[str, list[dict], int | None]]:
    rows: list[tuple[str, list[dict], int | None]] = []
    animations = manifest.get("animations")
    if isinstance(animations, dict):
        for name, data in animations.items():
            if not isinstance(data, dict):
                continue
            frames = data.get("frames")
            if isinstance(frames, list):
                rows.append(
                    (
                        str(name),
                        [dict(frame) for frame in frames if isinstance(frame, dict)],
                        data.get("duration_ms"),
                    )
                )
    raw_rows = manifest.get("rows")
    if isinstance(raw_rows, list):
        for row in raw_rows:
            if not isinstance(row, dict):
                continue
            name = row.get("animation") or row.get("name") or row.get("id")
            rects = row.get("rects") or row.get("frames")
            if name and isinstance(rects, list):
                frames = []
                for rect in rects:
                    if not isinstance(rect, dict):
                        continue
                    data = dict(rect)
                    if "w" not in data and "width" in data:
                        data["w"] = data["width"]
                    if "h" not in data and "height" in data:
                        data["h"] = data["height"]
                    frames.append(data)
                rows.append((str(name), frames, row.get("duration_ms")))
    return rows


def _safe_filename_part(text: str) -> str:
    return (
        "".join(c if c.isalnum() or c in {"-", "_"} else "_" for c in text).strip("_")
        or "animation"
    )


def write_animation_gifs_for_target(
    target_name: str, out_dir: Path | None = None
) -> list[Path]:
    """Write one GIF per animation row for a registered sprite target.

    The command reads the target's generated sheet manifest instead of creating
    one combined review strip.  Output goes under generated/gifs/<target>/ by
    default so quick-review GIFs never clutter the runtime sprite directory.
    """
    from PIL import Image

    target = _get_target(target_name)
    generated = generated_dir(target.name)
    if not generated.exists() or not any(generated.glob("*_spritesheet.yaml")):
        target.render_sheet(generated)
    manifest_paths = sorted(generated.glob("*_spritesheet.yaml"))
    if not manifest_paths:
        raise FileNotFoundError(
            f"no generated spritesheet YAML found for {target_name!r} in {generated}"
        )

    root = (
        Path(out_dir)
        if out_dir is not None
        else DEFAULT_ASSET_DIR / "gifs" / target.name
    )
    written: list[Path] = []
    for manifest_path in manifest_paths:
        manifest = safe_load(manifest_path.read_text(encoding="utf8")) or {}
        if not isinstance(manifest, dict):
            continue
        # Slice from every page (packed sheets span `.1.png`/`.2.png`/…), not
        # just the base image — a frame is addressed by its own `fpage`/`page`.
        pages = _manifest_page_images(manifest_path, manifest)
        if not pages:
            continue
        fw = manifest.get("frame_width")
        fh = manifest.get("frame_height")
        stem = manifest_path.stem
        if stem.endswith("_spritesheet"):
            stem = stem[:-12]
        # Common case: generated/gifs/<target>/<animation>.gif.
        # Multi-sheet targets still get a sheet-stem subfolder.
        target_out = root if stem == target.name else root / stem
        target_out.mkdir(parents=True, exist_ok=True)
        for animation, frames, row_duration in _animation_rows_from_manifest(manifest):
            if not frames:
                continue
            images = []
            durations = []
            for frame in frames:
                try:
                    img = _frame_from_rect(frame, pages, fw, fh)
                except Exception:
                    img = None
                if img is None:
                    continue
                images.append(img)
                durations.append(int(frame.get("duration_ms") or row_duration or 100))
            if not images:
                continue
            out = target_out / f"{_safe_filename_part(animation)}.gif"
            # Flatten onto the studio background (same as the canonical/preview
            # renders) so the transparent logical canvas doesn't index-quantize
            # to a random palette color.
            flattened = []
            for img in images:
                base = Image.new("RGBA", img.size, (43, 33, 40, 255))
                base.alpha_composite(img)
                flattened.append(base.convert("P", palette=Image.Palette.ADAPTIVE))
            flattened[0].save(
                out,
                save_all=True,
                append_images=flattened[1:],
                duration=durations,
                loop=0,
                disposal=2,
            )
            written.append(out)
    return written


def _cmd_gifs(args: argparse.Namespace) -> int:
    written = write_animation_gifs_for_target(
        args.target, Path(args.out_dir) if args.out_dir else None
    )
    if not written:
        rich_print(
            f"[yellow]No animation GIFs were written for {args.target!r}[/yellow]"
        )
        return 1
    rich_print(f"[bold green]Animation GIFs for {args.target}:[/bold green]")
    print_paths(written, prefix="  ")
    return 0


# ---- Target sheet / install / publish commands -------------------------------

# Tack-on categories that bulk operations scope to. The adapter
# surface (`characters` includes both tack-on and main-config targets;
# `review_npcs` is its own thing) has its own bulk paths via
# `draw-all` / `draw-runtime-npcs`.
_TACKON_CATEGORIES = frozenset({"characters", "props", "tiles", "icons"})


def _module_target_names() -> list[str]:
    """Names of every module-authored (non-config) target, sorted."""
    return sorted(
        name for name, t in _ALL_TARGETS.items() if getattr(t, "kind", None) == "module"
    )


def _portrait_target_names() -> list[str]:
    """Every character target that publishes the portrait product."""
    return sorted(
        name
        for name, target in _ALL_TARGETS.items()
        if target.category == "characters" and target.supports_portraits
    )


def _target_render_opts(args: argparse.Namespace) -> dict[str, object]:
    opts: dict[str, object] = {}
    if getattr(args, "quality_scale", None) is not None:
        opts["quality_scale"] = args.quality_scale
    if getattr(args, "downsample", None) is not None:
        opts["downsample"] = args.downsample
    return opts


@profile
def _publish_target(
    target_name: str,
    dest_root: Path,
    *,
    quiet: bool = False,
    **opts,
) -> List[Path]:
    """Render and install one complete target bundle with one registry lookup.

    The older composition routed through three independently user-facing CLI
    helpers, causing repeated lookups and printing generated paths that were
    immediately copied elsewhere. Full regeneration uses this compact seam and
    may suppress per-file output while retaining per-target progress lines.
    """

    target = _get_target(target_name)
    out_dir = generated_dir(target_name)
    target.render_sheet(out_dir, **opts)
    if target.supports_portraits:
        target.render_portraits(out_dir, **opts)
    copied = list(target.install(out_dir, dest_root))
    if not quiet:
        print_paths(copied)
    return copied


@profile
def _render_target(target_name: str, **opts) -> List[Path]:
    target = _get_target(target_name)
    out_dir = generated_dir(target_name)
    paths = list(target.render_sheet(out_dir, **opts))
    print_paths(paths)
    return paths


@profile
def _render_portraits_target(target_name: str, **opts) -> List[Path]:
    target = _get_target(target_name)
    if not target.supports_portraits:
        raise SystemExit(
            f"error: target {target_name!r} does not publish portraits; "
            "portrait products are required for character targets and optional "
            "for other target categories"
        )
    paths = list(target.render_portraits(generated_dir(target_name), **opts))
    print_paths(paths)
    return paths


@profile
def _render_target_bundle(target_name: str, **opts) -> List[Path]:
    paths = _render_target(target_name, **opts)
    target = _get_target(target_name)
    if target.supports_portraits:
        paths.extend(_render_portraits_target(target_name, **opts))
    return paths


@profile
def _install_target(target_name: str, dest_root: Path) -> List[Path]:
    target = _get_target(target_name)
    out_dir = generated_dir(target_name)
    # Every Target implements `install` with a
    # default copy-each-SHEET_FILES; targets that need custom behavior
    # (e.g. mockingbird_boss with its subdirectory of part files)
    # override the method.
    copied = list(target.install(out_dir, dest_root))
    print_paths(copied)
    return copied


@profile
def _bulk_over(
    op_name: str,
    target_names: list[str],
    op: "callable",
) -> int:
    """Run an operation over targets with durable elapsed/ETA reporting."""
    for line in _REPORT.warnings:
        print(f"discovery warning: {line}", file=sys.stderr)

    names = list(target_names)
    total = len(names)
    started = time.perf_counter()
    recent: list[float] = []
    failures: list[str] = []

    def fmt(seconds: float) -> str:
        seconds = max(0, int(round(seconds)))
        hours, rem = divmod(seconds, 3600)
        minutes, secs = divmod(rem, 60)
        return f"{hours:d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:d}:{secs:02d}"

    for index, name in enumerate(names, 1):
        elapsed = time.perf_counter() - started
        if recent:
            rolling = sum(recent[-8:]) / len(recent[-8:])
            eta_text = f" | eta {fmt(rolling * (total - index + 1))}"
        else:
            eta_text = ""
        width = len(str(max(1, total)))
        print(
            f"[{index:>{width}}/{total} {100.0 * (index - 1) / max(1, total):5.1f}%] "
            f"{op_name} {name} | elapsed {fmt(elapsed)}{eta_text}",
            flush=True,
        )
        item_started = time.perf_counter()
        try:
            op(name)
        except KeyboardInterrupt:
            duration = time.perf_counter() - item_started
            print(
                f"interrupted during {name} after {fmt(duration)} "
                f"({index - 1}/{total} completed)",
                file=sys.stderr,
                flush=True,
            )
            raise
        except Exception as ex:  # noqa: BLE001 - bulk operation reports and continues
            duration = time.perf_counter() - item_started
            print(f"error: target {name!r} failed after {fmt(duration)}: {ex}", file=sys.stderr)
            failures.append(name)
        else:
            duration = time.perf_counter() - item_started
            recent.append(duration)
            rolling = sum(recent[-8:]) / len(recent[-8:])
            print(
                f"    done {name} in {fmt(duration)} | {index}/{total} complete | "
                f"eta {fmt(rolling * (total - index))}",
                flush=True,
            )

    elapsed = time.perf_counter() - started
    if failures:
        print(
            f"\n{op_name} finished in {fmt(elapsed)} with {len(failures)} "
            f"failure(s): " + ", ".join(failures),
            file=sys.stderr,
        )
        return 1
    print(f"{op_name} finished: {total} target(s) in {fmt(elapsed)}", flush=True)
    return 0



def _cmd_sheet(args: argparse.Namespace) -> int:
    """`sheet [<name>]` — render one sheet, or every tack-on sheet."""
    opts = _target_render_opts(args)
    if args.target:
        _render_target(args.target, **opts)
        return 0
    return _bulk_over(
        "sheet", _module_target_names(), lambda name: _render_target(name, **opts)
    )


def _cmd_portraits(args: argparse.Namespace) -> int:
    """`portraits [<name>]` — render native portrait products."""
    opts = _target_render_opts(args)
    if args.target:
        _render_portraits_target(args.target, **opts)
        return 0
    return _bulk_over(
        "portraits",
        _portrait_target_names(),
        lambda name: _render_portraits_target(name, **opts),
    )


def _cmd_portrait_files(args: argparse.Namespace) -> int:
    """Print installed-relative portrait products for cache tooling.

    Multiple target names are resolved in one process so regeneration can
    inspect a whole batch without paying registry discovery once per target.
    ``--with-target`` emits tab-separated target/path records suitable for a
    shell cache map; the historical one-target plain-path output remains the
    default.
    """

    targets = list(args.targets)
    include_target = bool(args.with_target or len(targets) > 1)
    for target_name in targets:
        target = _get_target(target_name)
        prefix = Path(target.portrait_install_subdir or "")
        for filename in target.portrait_files:
            rel = (prefix / filename).as_posix()
            if include_target:
                print(f"{target_name}\t{rel}")
            else:
                print(rel)
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    """`install [<name>]` — install one target's files, or every tack-on's."""
    if args.target:
        copied = _install_target(args.target, args.dest_root)
        return 0 if copied else 1
    return _bulk_over(
        "install",
        _module_target_names(),
        lambda name: _install_target(name, args.dest_root),
    )


@profile
def _cmd_publish(args: argparse.Namespace) -> int:
    """Publish gameplay plus supported portraits, then install the bundle."""
    opts = _target_render_opts(args)
    if args.target:
        copied = _publish_target(args.target, args.dest_root, **opts)
        return 0 if copied else 1

    return _bulk_over(
        "publish",
        _module_target_names(),
        lambda name: _publish_target(name, args.dest_root, **opts),
    )


@profile
def _cmd_publish_many(args: argparse.Namespace) -> int:
    """Publish an explicit target batch after one registry discovery pass."""

    opts = _target_render_opts(args)
    return _bulk_over(
        "publish-many",
        list(dict.fromkeys(args.targets)),
        lambda name: _publish_target(
            name,
            args.dest_root,
            quiet=args.quiet,
            **opts,
        ),
    )


@profile
def _cmd_regenerate_all(args: argparse.Namespace) -> int:
    """Single-button regen: render + install every sprite the sandbox
    runtime can consume.

    Composes three existing convenience commands so a fresh checkout
    only needs one invocation to be art-current:

    1. `draw-all --out-dir <sandbox assets>` — the runtime adapter-driven
       sheets (the `runtime_stems` set in `draw_all`).
    2. `publish` (no target) — every module target under `targets/`.
    3. `draw-runtime-npcs` — the RUNTIME_REVIEW_NPCS roster of
       review-config toon NPCs the runtime sprite registry expects.

    Errors in any sub-step are reported but don't abort the others.
    """
    dest = Path(args.dest_root)
    print("# step 1/3: draw-all (adapter sheets) -> sandbox assets")
    failures: list[str] = []
    try:
        outputs = draw_all(DEFAULT_CONFIG_DIR, dest)
        print_paths(outputs)
    except Exception as ex:  # noqa: BLE001
        print(f"error: draw-all failed: {ex}", file=sys.stderr)
        failures.append("draw-all")

    print("\n# step 2/3: publish (every tack-on target)")
    publish_args = argparse.Namespace(target=None, dest_root=dest)
    rc = _cmd_publish(publish_args)
    if rc != 0:
        failures.append("publish")

    print("\n# step 3/3: draw-runtime-npcs (review-config NPCs)")
    npc_args = argparse.Namespace(
        review_dir=str(DEFAULT_REVIEW_CONFIG_DIR), out_dir=str(dest)
    )
    rc = _cmd_draw_runtime_npcs(npc_args)
    if rc != 0:
        failures.append("draw-runtime-npcs")

    if failures:
        print(
            f"\nregenerate-all completed with failure(s): {', '.join(failures)}",
            file=sys.stderr,
        )
        return 1
    print("\nregenerate-all OK")
    return 0


def _cmd_debug_hitboxes(args: argparse.Namespace) -> int:
    """Overlay per-animation hurt + hit boxes on a rendered spritesheet.

    Reads the sheet's YAML manifest, finds the matching PNG, and
    writes a sibling ``*_debug.png`` with cyan hurtbox + red hitbox
    outlines (+ legend) over every frame. Sprite authors run this
    after a render to verify the boxes line up with the visible
    body / strike pose.
    """
    yaml_path = _resolve_sheet_yaml(args.yaml_or_target)
    if yaml_path is None:
        print(
            f"error: {args.yaml_or_target!r} is neither a file nor a known target name "
            f"(searched {sandbox_sprites_dir()})",
            file=sys.stderr,
        )
        return 1
    out_path = args.out
    try:
        written = render_debug_overlay(yaml_path, out_path)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print_path(written, prefix="wrote debug overlay: ")
    return 0


def _resolve_sheet_yaml(value: str | Path) -> Path | None:
    """Resolve a YAML path or a short target name to a sheet manifest.

    Lookup order:

    1. ``value`` as a path that exists.
    2. ``<sandbox_sprites>/<value>_spritesheet.yaml`` (standard
       install location).
    3. ``<sandbox_sprites>/<stem>_spritesheet.yaml`` where
       ``stem`` is ``value`` with any extension stripped (so
       ``boss``, ``boss.yaml``, and ``boss_spritesheet.yaml``
       all resolve to the same file).
    """
    candidate = Path(value)
    if candidate.exists():
        return candidate
    sprites_dir = sandbox_sprites_dir()
    stem = candidate.stem if candidate.suffix else candidate.name
    # Strip a trailing `_spritesheet` so users can pass either
    # `boss` or `boss_spritesheet`.
    if stem.endswith("_spritesheet"):
        stem = stem[: -len("_spritesheet")]
    for path in (
        sprites_dir / f"{stem}_spritesheet.yaml",
        sprites_dir / "review" / f"{stem}_spritesheet.yaml",
    ):
        if path.exists():
            return path
    return None


@profile
def _cmd_draw_runtime_npcs(args: argparse.Namespace) -> int:
    """Render + install every review-config NPC that the runtime sprite
    registry expects at boot. These configs live under `configs/review/`
    so `draw-all` skips them by default; this one walks the
    [`RUNTIME_REVIEW_NPCS`] tuple and runs `draw-character` for each."""
    review_dir = Path(args.review_dir)
    out_dir = Path(args.out_dir)
    failures: list[str] = []
    all_outputs: List[Path] = []
    for stem in RUNTIME_REVIEW_NPCS:
        cfg = review_dir / f"{stem}.yaml"
        if not cfg.exists():
            print(
                f"error: missing review config for runtime NPC {stem!r}: {cfg}",
                file=sys.stderr,
            )
            failures.append(stem)
            continue
        try:
            paths = draw_character(cfg, out_dir)
            all_outputs.extend(paths)
        except Exception as ex:  # noqa: BLE001
            print(
                f"error: rendering runtime NPC {stem!r} failed: {ex}",
                file=sys.stderr,
            )
            failures.append(stem)
    print_paths(all_outputs)
    if failures:
        print(
            f"\ndraw-runtime-npcs completed with {len(failures)} failure(s): "
            + ", ".join(failures),
            file=sys.stderr,
        )
        return 1
    return 0


@profile
def _cmd_ultrapack(args: argparse.Namespace) -> int:
    """Pool every target's frames into shared uniform atlas pages at one quality
    tier. Writes pages + catalog (runtime artifacts) to ``--out``; the labeled
    page overlays + pack report land under ``out/diagnostics/`` only with
    ``--debug-views``, so the published pack stays clean by default."""
    from ..authoring.ultrapack import (
        PackPlan,
        ultrapack,
        ultrapack_rendered,
        write_debug_views,
        write_pack,
    )

    plan = PackPlan.load(args.pack_plan) if args.pack_plan else None
    if args.from_rendered is not None:
        pack = ultrapack_rendered(
            Path(args.from_rendered),
            scale=args.scale,
            min_frame_px=args.min_frame_px,
            page_size=args.page_size,
            plan=plan,
        )
    else:
        pack = ultrapack(
            list(_ALL_TARGETS.values()),
            scale=args.scale,
            min_frame_px=args.min_frame_px,
            page_size=args.page_size,
            plan=plan,
        )

    written = write_pack(pack, args.out, name=args.name)
    if args.debug_views:
        written += write_debug_views(
            pack, args.out, name=args.name, debug_dir=args.debug_dir
        )
    print(
        f"ultrapack '{args.name}' @ scale {args.scale:g}: "
        f"{len(pack.frames)} frames from "
        f"{len({f.target for f in pack.frames})} targets -> "
        f"{len(pack.pages)} pages ({pack.fill_fraction() * 100:.1f}% fill)"
    )
    print_paths(written)
    return 0
