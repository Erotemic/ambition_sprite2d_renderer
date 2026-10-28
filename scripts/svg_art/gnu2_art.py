#!/usr/bin/env python3
"""Render Armored Gnu2 from the original giant's poses, as editable SVG.

From tools/ambition_sprite2d_renderer:
    python scripts/svg_art/gnu2_art.py /tmp/armored_gnu2.svg
    python scripts/svg_art/gnu2_art.py /tmp/armored_gnu2_reared.svg reared angry
    python scripts/svg_art/gnu2_art.py /tmp/armored_gnu2_walk.svg --animation armed_walk --phase 0.35

The first pass creates standalone SVG previews, not a runtime sprite atlas.
The module `targets/characters/gnu_ton_boss/gnu2_art.py` owns the art.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import giant_art
from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss.gnu2_art import (
    armored_gnu2_svg,
    preview_pose,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("stance", nargs="?", choices=["sloped", "reared"], default="sloped")
    parser.add_argument("expression", nargs="?", default=None)
    parser.add_argument("--no-arms", action="store_true", help="Show giant without whole arms")
    parser.add_argument("--animation", help="Use an original Giant Gnu animation pose instead of a static stance")
    parser.add_argument("--phase", type=float, default=0.0, help="Animation phase between 0 and 1")
    args = parser.parse_args()
    if not 0.0 <= args.phase <= 1.0:
        parser.error("--phase must be in [0, 1]")
    pose = (
        giant_art.pose_for(args.animation, args.phase)
        if args.animation else preview_pose(args.stance, args.expression)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        armored_gnu2_svg(pose, arms=not args.no_arms),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
