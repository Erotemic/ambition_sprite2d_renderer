"""Render the gate's dialing glyphs.

    python -m ambition_sprite2d_renderer.glyphs sheet OUT.png
    python -m ambition_sprite2d_renderer.glyphs svgs OUT_DIR
"""

from __future__ import annotations

import argparse

from .legally_distinct import review_sheet, write_svgs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ambition_sprite2d_renderer.glyphs")
    sub = parser.add_subparsers(dest="command", required=True)
    sheet = sub.add_parser("sheet", help="a review sheet of every glyph, the inscription and a dial")
    sheet.add_argument("out")
    svgs = sub.add_parser("svgs", help="one SVG per glyph")
    svgs.add_argument("out_dir")
    svgs.add_argument("--color", default="#000000")
    args = parser.parse_args(argv)
    if args.command == "sheet":
        review_sheet().save(args.out)
        print(args.out)
    else:
        for path in write_svgs(args.out_dir, color=args.color):
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
