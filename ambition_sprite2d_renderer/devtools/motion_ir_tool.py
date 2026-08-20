"""Inspect, validate, and bridge Ambition's editor-neutral motion IR.

This is intentionally a small agent-facing tool.  Normal authoring edits the
SVG rig markers and ``*.pose.json`` / ``*.clip.json`` directly; this module
provides compact inspection, validation, one-time legacy migration, and the
temporary RigDocument projection used by the existing renderer.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from ambition_sprite2d_renderer.authoring.motion_ir import (
    CharacterMotionBinding,
    MotionLibrary,
    bake_legacy_motion_library,
    binding_dict,
    fit_legacy_render_binding,
    load_svg_rig_definition,
    write_json,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument


DEFAULT_CANONICAL_POSES: dict[str, tuple[str, int]] = {
    "humanoid/fighting_polygon/idle": ("idle", 0),
    "humanoid/fighting_polygon/crouch": ("crouch", 0),
    "humanoid/fighting_polygon/jab/anticipation": ("jab", 1),
    "humanoid/fighting_polygon/jab/contact": ("jab", 2),
    "humanoid/fighting_polygon/jab/recovery": ("jab", 3),
    "humanoid/fighting_polygon/ftilt/anticipation": ("attack_side", 1),
    "humanoid/fighting_polygon/ftilt/contact": ("attack_side", 3),
    "humanoid/fighting_polygon/ftilt/recovery": ("attack_side", 4),
    "humanoid/fighting_polygon/grab/anticipation": ("grab", 1),
    "humanoid/fighting_polygon/grab/extension": ("grab", 3),
    "humanoid/fighting_polygon/grab/recovery": ("grab", 5),
    "humanoid/fighting_polygon/grab/hold": ("grab_hold", 0),
    "humanoid/fighting_polygon/pummel/contact": ("pummel", 2),
    "humanoid/fighting_polygon/throw_forward/anticipation": ("throw_forward", 1),
    "humanoid/fighting_polygon/throw_forward/release": ("throw_forward", 4),
    "humanoid/fighting_polygon/throw_forward/recovery": ("throw_forward", 6),
}


def describe(binding_path: Path, *, include_clips: bool = False) -> str:
    binding = CharacterMotionBinding.load(binding_path)
    prepared = binding.load_prepared()
    rig = prepared.rig
    library = prepared.library
    lines = [
        f"character={binding.character}",
        f"binding={binding.path}",
        f"rig={rig.source_svg} view={rig.view_id} profile={rig.profile}",
        f"root={rig.root_anchor[0]:.3f},{rig.root_anchor[1]:.3f} bones={len(rig.bones)} parts={len(rig.parts)}",
        f"library={library.id} poses={len(library.poses)} clips={len(library.clips)}",
        (
            f"frame={binding.render.frame_width_px}x{binding.render.frame_height_px} "
            f"root_px={binding.render.root_anchor_px[0]:.3f},{binding.render.root_anchor_px[1]:.3f} "
            f"px_per_rig_unit={binding.render.frame_px_per_rig_unit:.9f}"
        ),
    ]
    for pose_id in sorted(library.poses):
        pose = library.poses[pose_id]
        lines.append(f"P {pose_id} bones={len(pose.state.bones)}")
    if include_clips:
        for clip_id in sorted(library.clips):
            clip = library.clips[clip_id]
            refs = sum(1 for key in clip.pose_keys if key.pose)
            lines.append(
                f"C {clip_id} frames={clip.frame_count} frame_ms={clip.frame_duration_ms} "
                f"loop={str(clip.loop).lower()} pose_refs={refs} tracks={len(clip.tracks)}"
            )
    return "\n".join(lines)


def validate_binding(binding_path: Path) -> list[str]:
    try:
        binding = CharacterMotionBinding.load(binding_path)
        prepared = binding.load_prepared()
    except Exception as ex:
        return [str(ex)]
    return [*prepared.rig.validate(), *prepared.library.validate(prepared.rig)]


def compare_legacy(binding_path: Path, legacy_path: Path, *, tolerance: float = 2e-4) -> dict:
    """Compare every published sample pose against a legacy RigDocument."""

    binding = CharacterMotionBinding.load(binding_path)
    prepared = binding.load_prepared()
    projected = prepared.to_rig_document()
    legacy = RigDocument.load(legacy_path)
    if set(projected.clips) != set(legacy.clips):
        missing = sorted(set(legacy.clips) - set(projected.clips))
        extra = sorted(set(projected.clips) - set(legacy.clips))
        raise ValueError(f"clip vocabulary differs; missing={missing}, extra={extra}")

    worst = {"error": 0.0, "clip": None, "frame": None, "bone": None, "field": None}
    samples = 0
    for clip_name in legacy.clips:
        clip = legacy.clips[clip_name]
        frames = max(1, int(clip.get("frames", 1)))
        for frame in range(frames):
            t = legacy.frame_time(clip_name, frame, frames)
            old_world, old_params = legacy.solve(clip_name, t)
            new_world, new_params = projected.solve(clip_name, t)
            samples += 1
            for bone_name, old in old_world.items():
                new = new_world[bone_name]
                checks = {
                    "origin_x": abs(old.origin[0] - new.origin[0]),
                    "origin_y": abs(old.origin[1] - new.origin[1]),
                    "angle": abs(old.angle - new.angle),
                    "length": abs(old.length - new.length),
                }
                for field, error in checks.items():
                    if error > worst["error"]:
                        worst = {
                            "error": error,
                            "clip": clip_name,
                            "frame": frame,
                            "bone": bone_name,
                            "field": field,
                        }
            free_names = set(old_params) | set(new_params)
            for name in free_names:
                if name in old_world:
                    continue
                # Solver-control channels intentionally disappear from the new
                # source.  Compare only parameters that survive as painter data.
                if name.startswith(("near_foot_", "far_foot_", "near_hand_", "far_hand_")):
                    continue
                if name.startswith("bone.") or name in {"root_x", "root_y"}:
                    continue
                error = abs(float(old_params.get(name, 0.0)) - float(new_params.get(name, 0.0)))
                if error > worst["error"]:
                    worst = {
                        "error": error,
                        "clip": clip_name,
                        "frame": frame,
                        "bone": None,
                        "field": f"parameter:{name}",
                    }
    if float(worst["error"]) > tolerance:
        raise ValueError(
            f"legacy projection differs by {worst['error']:.6g} > {tolerance}: {worst}"
        )
    return {"samples": samples, "tolerance": tolerance, "worst": worst}



def _write_binding_from_legacy(
    *,
    legacy: RigDocument,
    svg_path: Path,
    view: str,
    library_path: Path,
    binding_path: Path,
) -> Path:
    rig = load_svg_rig_definition(svg_path, view_id=view)
    library = MotionLibrary.load(library_path)
    if rig.profile != library.rig_profile:
        raise ValueError(
            f"rig profile {rig.profile!r} does not match motion library {library.rig_profile!r}"
        )
    render = fit_legacy_render_binding(legacy, rig)
    import os

    write_json(
        binding_path,
        binding_dict(
            character=legacy.name,
            svg_relpath=Path(os.path.relpath(svg_path, binding_path.parent)).as_posix(),
            view=view,
            library_relpath=Path(os.path.relpath(library_path, binding_path.parent)).as_posix(),
            render=render,
            sprite_tuning=legacy.sprite_tuning,
            features=legacy.features,
            natural_pose=str((legacy.data.get("natural_pose") or {}).get("clip", "idle")),
        ),
    )
    return binding_path


def _cmd_bind_library(args: argparse.Namespace) -> int:
    legacy_path = Path(args.legacy).resolve()
    svg_path = Path(args.svg).resolve()
    library_path = Path(args.library).resolve()
    binding_path = Path(args.binding_out).resolve()
    legacy = RigDocument.load(legacy_path)
    print(
        _write_binding_from_legacy(
            legacy=legacy,
            svg_path=svg_path,
            view=args.view,
            library_path=library_path,
            binding_path=binding_path,
        )
    )
    return 0

def _cmd_migrate(args: argparse.Namespace) -> int:
    legacy_path = Path(args.legacy).resolve()
    svg_path = Path(args.svg).resolve()
    out_dir = Path(args.library_out).resolve()
    legacy = RigDocument.load(legacy_path)
    rig = load_svg_rig_definition(svg_path, view_id=args.view)
    canonical = {} if args.no_canonical_poses else DEFAULT_CANONICAL_POSES
    render, library_path = bake_legacy_motion_library(
        legacy,
        rig,
        library_id=args.library_id,
        out_dir=out_dir,
        canonical_poses=canonical,
    )
    binding_path = Path(args.binding_out).resolve()
    svg_rel = Path(
        __import__("os").path.relpath(svg_path, binding_path.parent)
    ).as_posix()
    library_rel = Path(
        __import__("os").path.relpath(library_path, binding_path.parent)
    ).as_posix()
    write_json(
        binding_path,
        binding_dict(
            character=legacy.name,
            svg_relpath=svg_rel,
            view=args.view,
            library_relpath=library_rel,
            render=render,
            sprite_tuning=legacy.sprite_tuning,
            features=legacy.features,
            natural_pose=str((legacy.data.get("natural_pose") or {}).get("clip", "idle")),
        ),
    )
    print(binding_path)
    print(library_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    describe_cmd = sub.add_parser("describe", help="Print a compact semantic summary")
    describe_cmd.add_argument("binding", type=Path)
    describe_cmd.add_argument("--clips", action="store_true", help="Also list every clip")

    validate_cmd = sub.add_parser("validate", help="Validate one motion binding + SVG + library")
    validate_cmd.add_argument("binding", type=Path)

    project_cmd = sub.add_parser("materialize-legacy", help="Write a disposable RigDocument projection")
    project_cmd.add_argument("binding", type=Path)
    project_cmd.add_argument("--out", required=True, type=Path)

    compare_cmd = sub.add_parser("compare-legacy", help="Compare every published frame against an old RigDocument")
    compare_cmd.add_argument("binding", type=Path)
    compare_cmd.add_argument("legacy", type=Path)
    compare_cmd.add_argument("--tolerance", type=float, default=2e-4)

    migrate_cmd = sub.add_parser("migrate-legacy", help="One-time bake of a RigDocument into editor-neutral motion JSON")
    migrate_cmd.add_argument("legacy", type=Path)
    migrate_cmd.add_argument("--svg", required=True, type=Path)
    migrate_cmd.add_argument("--view", required=True)
    migrate_cmd.add_argument("--library-id", required=True)
    migrate_cmd.add_argument("--library-out", required=True, type=Path)
    migrate_cmd.add_argument("--binding-out", required=True, type=Path)
    migrate_cmd.add_argument("--no-canonical-poses", action="store_true")

    bind_cmd = sub.add_parser(
        "bind-library",
        help="Bind another SVG rig to an existing compatible motion library",
    )
    bind_cmd.add_argument("legacy", type=Path, help="Legacy document supplying publication mapping/metadata")
    bind_cmd.add_argument("--svg", required=True, type=Path)
    bind_cmd.add_argument("--view", required=True)
    bind_cmd.add_argument("--library", required=True, type=Path)
    bind_cmd.add_argument("--binding-out", required=True, type=Path)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "describe":
        print(describe(args.binding, include_clips=args.clips))
        return 0
    if args.command == "validate":
        errors = validate_binding(args.binding)
        if errors:
            for error in errors:
                print(f"error: {error}")
            return 1
        print("ok")
        return 0
    if args.command == "materialize-legacy":
        binding = CharacterMotionBinding.load(args.binding)
        out = binding.load_prepared().write_legacy_projection(args.out)
        print(out)
        return 0
    if args.command == "compare-legacy":
        print(json.dumps(compare_legacy(args.binding, args.legacy, tolerance=args.tolerance), indent=2))
        return 0
    if args.command == "migrate-legacy":
        return _cmd_migrate(args)
    if args.command == "bind-library":
        return _cmd_bind_library(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
