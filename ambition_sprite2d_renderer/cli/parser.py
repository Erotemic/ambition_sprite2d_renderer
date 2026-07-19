"""Modal CLI for ambition_sprite2d_renderer.

Two command families:

(1) **Unified Target commands** — work with any registered target
    (tack-ons under ``targets/<category>/``, main configs under
    ``configs/``, review-NPC configs under ``configs/review/``). Each
    takes an optional ``<TARGET>`` name. With a name: act on that
    target. Without: bulk over every tack-on target.

      list                        Show every registered target, grouped by category.
      canonical [<target>]        One canonical pose, or the full gallery.
      sheet [<target>]            One full gameplay sheet, or every tack-on sheet.
      portraits [<target>]        Native portrait sheet(s) for supported characters.
      portrait-gallery           Contact sheet of installed default portraits.
      portrait-files <target>    Installed-relative portrait product paths.
      install [<target>]          Copy one target's files to sandbox assets, or all.
      publish [<target>]          gameplay sheet + portraits + install.
      publish-many <target>...     Explicit batch with one discovery pass.
      gifs [<target>]             Per-animation GIF previews from a rendered sheet.
      debug-hitboxes <target>     Hitbox/hurtbox overlay strips for one target.

(2) **Adapter-pipeline commands** — take config paths instead of
    target names, scoped to the YAML adapter pipeline. Useful for
    one-off art iteration with custom configs and for the curated
    runtime-NPC publishing path.

      draw-all                    Render every config in ``configs/``.
      draw-review                 Render every config in ``configs/review/``.
      draw-character <config>     One config: canonical + spritesheet + YAML.
      draw-factions               Music-faction lineup review render.
      draw-runtime-npcs           Render + install the curated review-NPC subset.
      regenerate-all              draw-all + publish + draw-runtime-npcs.
      spritesheet <config> <out>  One config's sheet to a specific path.
      single <config> <out>       One frame from a config.

Plus two pipeline surfaces with their own semantics:

      ultrapack                   Pool every target's frames into shared
                                  uniform atlas pages at one quality tier
                                  (see ``authoring/ultrapack.py``).
      ldtk-manifest               Emit the LDtk visual manifest consumed by
                                  ambition_ldtk_tools apply-manifest.

See ``registry/discovery.py`` for the Target protocol contract.
"""

from __future__ import annotations
from ..profiling import profile

import argparse
from pathlib import Path

from .commands import (
    DEFAULT_ASSET_DIR,
    DEFAULT_CONFIG_DIR,
    DEFAULT_FACTION_CONFIG,
    DEFAULT_REVIEW_CONFIG_DIR,
    sandbox_sprites_dir,
    _cmd_canonical,
    _cmd_debug_hitboxes,
    _cmd_draw_all,
    _cmd_draw_character,
    _cmd_draw_factions,
    _cmd_draw_review,
    _cmd_draw_runtime_npcs,
    _cmd_gifs,
    _cmd_install,
    _cmd_ldtk_manifest,
    _cmd_list_targets,
    _cmd_publish,
    _cmd_publish_many,
    _cmd_portraits,
    _cmd_portrait_gallery,
    _cmd_portrait_files,
    _cmd_regenerate_all,
    _cmd_sheet,
    _cmd_single,
    _cmd_spritesheet,
    _cmd_ultrapack,
)


def _add_optional_target_arg(p: argparse.ArgumentParser) -> None:
    """Optional TARGET positional — empty means bulk over every tack-on.

    No ``choices=`` constraint here so that ``_get_target`` can surface
    a useful error when the name matches a file under
    ``targets/<category>/`` but the file is missing the tack-on API.
    With ``choices=`` argparse would error before our handler runs
    and we couldn't show the warning.
    """
    p.add_argument(
        "target",
        metavar="TARGET",
        nargs="?",
        default=None,
        help=(
            "target id — name from `list`. Omit to bulk over every "
            "registered tack-on target (characters/props/tiles/icons)."
        ),
    )


def _add_dest_root_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--dest-root",
        type=Path,
        default=sandbox_sprites_dir(),
        help="install destination (default: crates/ambition_actors/assets/sprites)",
    )


def _add_quality_render_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--quality-scale",
        type=float,
        default=None,
        help=(
            "Render source art at this fraction of the target's normal native "
            "texture scale before packing. Adapter/vector targets support "
            "fractional scales such as 0.5, 0.25, and 0.0625; unsupported "
            "tack-on targets should be upgraded at their render seam instead "
            "of post-resizing atlases."
        ),
    )
    p.add_argument(
        "--downsample",
        choices=["lanczos", "nearest", "bicubic"],
        default=None,
        help="Override the renderer's supersample downsample filter for this render.",
    )


def _add_config_dir_args(
    p: argparse.ArgumentParser,
    *,
    config_default: Path,
    out_default: Path,
) -> None:
    p.add_argument("--config-dir", default=str(config_default))
    p.add_argument("--out-dir", default=str(out_default))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ambition_sprite2d_renderer",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ---- Unified Target commands (take an optional <TARGET> name) ----------
    #
    # With a name: act on that target. Without a name: bulk over every
    # tack-on target (characters/props/tiles/icons). The YAML adapter
    # surface is bulk-rendered separately via `draw-all` /
    # `draw-runtime-npcs` because those have surface-specific semantics.

    p = sub.add_parser(
        "canonical",
        help=(
            "Draw a single target's canonical pose, or the full gallery if "
            "no target is given. Sources canonicals from every surface "
            "(tack-ons, main configs, review NPCs)."
        ),
    )
    _add_optional_target_arg(p)
    _add_config_dir_args(
        p,
        config_default=DEFAULT_CONFIG_DIR,
        out_default=DEFAULT_ASSET_DIR / "canonicals",
    )
    p.add_argument(
        "--adapters-only",
        action="store_true",
        help="(bulk mode only) skip tack-on + review NPC targets",
    )
    p.set_defaults(func=_cmd_canonical)

    p = sub.add_parser(
        "sheet",
        help=(
            "Render a single target's full sprite sheet bundle into generated/, "
            "or bulk-render every tack-on target if no name is given."
        ),
    )
    _add_optional_target_arg(p)
    _add_quality_render_args(p)
    p.set_defaults(func=_cmd_sheet)

    p = sub.add_parser(
        "portraits",
        help=(
            "Render a character's independent native portrait sheet into "
            "generated/, or every portrait-capable character if omitted."
        ),
    )
    _add_optional_target_arg(p)
    p.set_defaults(func=_cmd_portraits)

    p = sub.add_parser(
        "portrait-gallery",
        help="Build a labeled contact sheet from installed portrait products.",
    )
    p.add_argument(
        "--source-dir",
        type=Path,
        default=sandbox_sprites_dir(),
        help="Directory recursively containing *_portraits.ron products.",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_ASSET_DIR / "portrait_gallery.png",
        help="Output gallery PNG.",
    )
    p.add_argument("--columns", type=int, default=8)
    p.set_defaults(func=_cmd_portrait_gallery)

    p = sub.add_parser(
        "portrait-files",
        help="Print installed-relative portrait product files for target(s).",
    )
    p.add_argument("targets", metavar="TARGET", nargs="+")
    p.add_argument(
        "--with-target",
        action="store_true",
        help="Prefix each path with TARGET and a tab for batch cache tooling.",
    )
    p.set_defaults(func=_cmd_portrait_files)

    p = sub.add_parser(
        "install",
        help=(
            "Copy a single target's rendered files into the sandbox sprites "
            "dir, or bulk-install every tack-on target if no name is given."
        ),
    )
    _add_optional_target_arg(p)
    _add_dest_root_arg(p)
    p.set_defaults(func=_cmd_install)

    p = sub.add_parser(
        "publish",
        help=(
            "gameplay sheet + native portraits + install for one target, or "
            "bulk for every tack-on target "
            "if no name is given."
        ),
    )
    _add_optional_target_arg(p)
    _add_dest_root_arg(p)
    _add_quality_render_args(p)
    p.set_defaults(func=_cmd_publish)

    p = sub.add_parser(
        "publish-many",
        help=(
            "Render and install an explicit target batch in one process, "
            "amortizing registry discovery across the batch."
        ),
    )
    p.add_argument("targets", metavar="TARGET", nargs="+")
    _add_dest_root_arg(p)
    _add_quality_render_args(p)
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Print target progress but suppress per-file path listings.",
    )
    p.set_defaults(func=_cmd_publish_many)

    p = sub.add_parser(
        "list", help="Show every registered target, grouped by category."
    )
    p.set_defaults(func=_cmd_list_targets)
    sub.add_parser("list-targets", help="alias of `list`").set_defaults(
        func=_cmd_list_targets
    )

    # ---- Adapter-pipeline commands (take config paths, not target names) ----

    p = sub.add_parser("draw-all", help="Render every main adapter config in configs/.")
    _add_config_dir_args(
        p, config_default=DEFAULT_CONFIG_DIR, out_default=DEFAULT_ASSET_DIR
    )
    p.set_defaults(func=_cmd_draw_all)

    p = sub.add_parser(
        "draw-review", help="Render every review config in configs/review/."
    )
    _add_config_dir_args(
        p,
        config_default=DEFAULT_REVIEW_CONFIG_DIR,
        out_default=DEFAULT_ASSET_DIR / "review",
    )
    p.set_defaults(func=_cmd_draw_review)

    p = sub.add_parser(
        "draw-character", help="Render one config's canonical + spritesheet + YAML."
    )
    p.add_argument(
        "config",
        help=(
            "Config to render. Either a path to a `*.yaml` file or a "
            "short name (e.g. `boss`, `robot_guardian`) — the latter "
            "resolves to `configs/<name>.yaml` or `configs/review/<name>.yaml`."
        ),
    )
    p.add_argument("--out-dir", default=str(DEFAULT_ASSET_DIR))
    p.add_argument(
        "--debug-hitboxes",
        action="store_true",
        help=(
            "After rendering, write `<sheet>_debug.png` next to the "
            "sheet PNG with per-animation hurt + hit boxes drawn over "
            "every frame. Equivalent to running `debug-hitboxes "
            "<sheet>.yaml` separately."
        ),
    )
    p.set_defaults(func=_cmd_draw_character)

    p = sub.add_parser(
        "draw-factions", help="Render music-faction leader/NPC review sprites."
    )
    p.add_argument("--config", default=str(DEFAULT_FACTION_CONFIG))
    p.add_argument("--out-dir", default=str(DEFAULT_ASSET_DIR / "factions"))
    p.set_defaults(func=_cmd_draw_factions)

    p = sub.add_parser(
        "ldtk-manifest",
        help="Emit an LDtk-consumable visual manifest (tilesets + entity icons) "
        "for the published sprite sheets. Consumed by ambition_ldtk_tools "
        "`visual-manifest apply-manifest`.",
    )
    p.add_argument(
        "--sprites-dir",
        default=None,
        help="Directory of published sheets (default: the sandbox sprites dir).",
    )
    p.add_argument(
        "--out",
        default=None,
        help="Output JSON path (default: <sprites-dir>/ldtk_sprite_manifest.json).",
    )
    p.add_argument(
        "--all-sheets",
        action="store_true",
        help="Register every discovered sheet as a tileset (the full, "
        "editor-browsable set). Default: only sheets referenced by the "
        "curated entity map, for a minimal .ldtk apply diff.",
    )
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=_cmd_ldtk_manifest)

    p = sub.add_parser(
        "spritesheet", help="Render one config's sheet to a specific path."
    )
    p.add_argument("config")
    p.add_argument("output")
    p.add_argument("--manifest-out", default=None)
    p.set_defaults(func=_cmd_spritesheet)

    p = sub.add_parser("single", help="Render one frame from a config.")
    p.add_argument("config")
    p.add_argument("output")
    p.add_argument("--animation", default="idle")
    p.add_argument("--frame-index", type=int, default=0)
    p.set_defaults(func=_cmd_single)

    p = sub.add_parser(
        "gifs", help="Write one GIF per animation row for a registered target."
    )
    p.add_argument(
        "target", help="Registered target name, e.g. goblin or kernel_guide."
    )
    p.add_argument(
        "--out-dir",
        default=None,
        help="Output root. Default: generated/gifs/<target>/<sheet_stem>/<animation>.gif",
    )
    p.set_defaults(func=_cmd_gifs)

    p = sub.add_parser(
        "draw-runtime-npcs",
        help=(
            "Render + install every review-config NPC the runtime sprite "
            "registry expects at boot — the RUNTIME_REVIEW_NPCS roster in "
            "cli/commands.py (the single authoritative list). These live "
            "under configs/review/ so draw-all skips them by default."
        ),
    )
    p.add_argument(
        "--review-dir",
        default=str(DEFAULT_REVIEW_CONFIG_DIR),
    )
    p.add_argument(
        "--out-dir",
        default=str(sandbox_sprites_dir()),
        help="install destination (default: crates/ambition_actors/assets/sprites)",
    )
    p.set_defaults(func=_cmd_draw_runtime_npcs)

    p = sub.add_parser(
        "regenerate-all",
        help=(
            "One-shot: draw-all + publish + draw-runtime-npcs, all installed "
            "into sandbox assets. Brings a fresh checkout's sprite directory "
            "up to date in one command."
        ),
    )
    p.add_argument(
        "--dest-root",
        type=Path,
        default=sandbox_sprites_dir(),
        help="install destination (default: crates/ambition_actors/assets/sprites)",
    )
    p.set_defaults(func=_cmd_regenerate_all)

    p = sub.add_parser(
        "debug-hitboxes",
        help=(
            "Overlay per-animation hurt + hit boxes on a rendered "
            "spritesheet. Writes a sibling `<sheet>_debug.png`."
        ),
    )
    p.add_argument(
        "yaml_or_target",
        help=(
            "Either: a path to the sheet's YAML manifest "
            "(e.g. `crates/ambition_actors/assets/sprites/boss_spritesheet.yaml`); "
            "OR a short target name (e.g. `boss`) that resolves to the "
            "expected `<sandbox_sprites>/<target>_spritesheet.yaml`."
        ),
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help=(
            "Output PNG path. Default: sibling of the sheet PNG with "
            "`_debug.png` suffix."
        ),
    )
    p.set_defaults(func=_cmd_debug_hitboxes)

    p = sub.add_parser(
        "ultrapack",
        help=(
            "Pool every target's frames into shared, uniformly-sized atlas "
            "pages at one quality tier. Writes pages + a catalog (runtime "
            "artifacts only); diagnostics are opt-in via --debug-views."
        ),
    )
    p.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for the shared pages + catalog.",
    )
    p.add_argument(
        "--from-rendered",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Pool from already-published `*_spritesheet.yaml` sheets in DIR "
            "instead of re-rendering every target (the efficient regen path). "
            "Default: discover + render every registered target."
        ),
    )
    p.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Quality tier scale (1.0 authored, 0.5, 0.25, 0.0625 potato).",
    )
    p.add_argument(
        "--min-frame-px",
        type=int,
        default=1,
        help="Floor for each scaled frame's side (potato uses 8).",
    )
    p.add_argument(
        "--page-size",
        type=int,
        default=2048,
        help="Square atlas page size in pixels (clamped to the GPU max).",
    )
    p.add_argument(
        "--name",
        default="ultrapack",
        help="Basename for the page PNGs + catalog JSON.",
    )
    p.add_argument(
        "--pack-plan",
        type=Path,
        default=None,
        help=(
            "PackPlan YAML (groups: {name: [target stems]}). Each group packs "
            "into its own page sequence (locality); ungrouped targets share "
            "the general pool."
        ),
    )
    p.add_argument(
        "--debug-views",
        action="store_true",
        help="Also write labeled page overlays + a pack report (see --debug-dir).",
    )
    p.add_argument(
        "--debug-dir",
        type=Path,
        default=None,
        help=(
            "Where --debug-views diagnostics land. Default: out/diagnostics/. "
            "Pass a staging dir when --out is a runtime asset root so debug "
            "views never ship."
        ),
    )
    p.set_defaults(func=_cmd_ultrapack)

    return parser


@profile
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)
