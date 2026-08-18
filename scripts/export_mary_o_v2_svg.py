#!/usr/bin/env python3
"""Emit Mary-O's current procedural idle anatomy as an editable SVG seed.

This command is intentionally explicit: the ordinary Mary-O and SVG POC render
targets never rewrite ``assets/mary_o_v2.svg`` after an artist begins moving
parts in Inkscape.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ambition_sprite2d_renderer.targets.characters.mary_o_v2 import export_svg_poc_source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "mary_o_v2.svg",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the existing file differs from a fresh procedural export.",
    )
    args = parser.parse_args()
    if args.check:
        from ambition_sprite2d_renderer.targets.characters._mary_o_v2_svg_poc import svg_source_text

        expected = svg_source_text()
        if not args.output.exists() or args.output.read_text(encoding="utf8") != expected:
            raise SystemExit(f"{args.output} differs from a fresh Mary-O procedural export")
        print(f"Mary-O SVG seed matches procedural export: {args.output}")
        return 0
    path = export_svg_poc_source(args.output)
    print(f"Wrote Mary-O SVG seed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
