"""Text-first semantic pose and motion review CLI for automation agents.

Invoke without touching the renderer's centralized command parser::

    python -m ambition_sprite2d_renderer.authoring.pose_tools templates
    python -m ambition_sprite2d_renderer.authoring.pose_tools review carl_stargan --clip walk --out /tmp/walk
    python -m ambition_sprite2d_renderer.authoring.pose_tools scaffold carl_stargan --clip jab --frame 2 --out /tmp/jab.yaml
    python -m ambition_sprite2d_renderer.authoring.pose_tools apply carl_stargan --clip jab --frame 2 --goals /tmp/jab.yaml --out /tmp/carl.rig.json
    python -m ambition_sprite2d_renderer.authoring.pose_tools phases carl_stargan --clip walk --template walk --out /tmp/carl.rig.json

The module entrypoint is deliberate: agent-authored tooling can land as an
additive file without competing for edits to the main CLI registry.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .motion_authoring import (
    PHASE_TEMPLATES,
    apply_phase_template,
    apply_pose_goals,
    load_goal_file,
    write_goal_scaffold,
)
from .motion_review import run_motion_review
from .motion_retarget import retarget_clip
from .motion_rig_resolver import find_existing_rig_document
from .rigdoc import RigDocument


def _resolve_doc(target: str, rig: str | None) -> tuple[Path, RigDocument]:
    path = find_existing_rig_document(target, explicit=Path(rig) if rig else None)
    return path, RigDocument.load(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Semantic bone-pose authoring and motion review tools")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("templates", help="List built-in animation phase templates")

    review = sub.add_parser("review", help="Analyze locomotion/fighting motion through time")
    review.add_argument("target")
    review.add_argument("--clip", required=True)
    review.add_argument("--rig")
    review.add_argument("--focus", help="Endpoint for speed/contact review, e.g. near_hand")
    review.add_argument("--travel-px-per-cycle", type=float, help="Optional expected runtime body travel used to compensate planted-foot drift")
    review.add_argument("--art", action="store_true", help="Also render flat silhouettes when sprite rasterization is available")
    review.add_argument("--out", required=True)

    scaffold = sub.add_parser("scaffold", help="Write a semantic pose-goal YAML scaffold")
    scaffold.add_argument("target")
    scaffold.add_argument("--clip", required=True)
    scaffold.add_argument("--frame", type=int, required=True)
    scaffold.add_argument("--rig")
    scaffold.add_argument("--out", required=True)

    apply_cmd = sub.add_parser("apply", help="Apply semantic pose goals to a copy of a rig")
    apply_cmd.add_argument("target")
    apply_cmd.add_argument("--clip", required=True)
    apply_cmd.add_argument("--frame", type=int, required=True)
    apply_cmd.add_argument("--goals", required=True)
    apply_cmd.add_argument("--rig")
    apply_cmd.add_argument("--out", required=True)
    apply_cmd.add_argument("--ease", default="smooth")

    phases = sub.add_parser("phases", help="Add semantic phase bookmarks to a copy of a rig")
    phases.add_argument("target")
    phases.add_argument("--clip", required=True)
    phases.add_argument("--template", required=True, choices=sorted(PHASE_TEMPLATES))
    phases.add_argument("--rig")
    phases.add_argument("--out", required=True)

    retarget = sub.add_parser("retarget", help="Retarget a clip between humanoid rigs using normalized anatomical endpoints")
    retarget.add_argument("source_target")
    retarget.add_argument("target_target")
    retarget.add_argument("--clip", required=True)
    retarget.add_argument("--target-clip")
    retarget.add_argument("--source-rig")
    retarget.add_argument("--target-rig")
    retarget.add_argument("--scale", type=float, help="Override automatic body-scale ratio")
    retarget.add_argument("--out", required=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "templates":
        for name, phases in PHASE_TEMPLATES.items():
            print(name)
            for phase in phases:
                print(f"  {phase.t:>5.3f}  {phase.role:<20} {phase.intent}")
        return 0

    if args.command == "review":
        review = run_motion_review(
            target=args.target,
            clip_name=args.clip,
            out_dir=args.out,
            rig_path=args.rig,
            focus=args.focus,
            travel_px_per_cycle=args.travel_px_per_cycle,
            with_art=args.art,
        )
        print(json.dumps({"metrics": review.metrics, "findings": [finding.code for finding in review.findings], "outputs": {key: str(value) for key, value in review.output_paths.items()}}, indent=2))
        return 0

    if args.command == "retarget":
        source_path, source_doc = _resolve_doc(args.source_target, args.source_rig)
        target_path, target_doc = _resolve_doc(args.target_target, args.target_rig)
        report = retarget_clip(
            source_doc,
            args.clip,
            target_doc,
            target_clip=args.target_clip,
            scale=args.scale,
        )
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        target_doc.save(out)
        print(json.dumps({"source_rig": str(source_path), "target_rig": str(target_path), "output": str(out), **report}, indent=2))
        return 0

    path, doc = _resolve_doc(args.target, getattr(args, "rig", None))
    if args.command == "scaffold":
        out = write_goal_scaffold(doc, args.clip, args.frame, args.out)
        print(out)
        return 0

    if args.command == "apply":
        data = load_goal_file(args.goals)
        goals = data.get("goals", data)
        values = apply_pose_goals(doc, args.clip, args.frame, goals, ease=args.ease)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        doc.save(out)
        print(json.dumps({"source": str(path), "output": str(out), "channels": values}, indent=2))
        return 0

    if args.command == "phases":
        keys = apply_phase_template(doc, args.clip, args.template)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        doc.save(out)
        print(json.dumps({"source": str(path), "output": str(out), "phase_keys": keys}, indent=2))
        return 0

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
