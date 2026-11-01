"""``python -m ambition_sprite2d_renderer.handgen``: reference sheets."""

from __future__ import annotations

import argparse
from pathlib import Path

from .draw import STYLES
from .model import SPECS
from .reference import drawn_sheet, model_sheet, solved_sheet


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="handgen", description="Hand generator reference sheets.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, help_ in (("model", "the bare 3D model's turnaround"), ("poses", "every named pose, drawn, palm and back"), ("solved", "grips round rods and pinches, solved by contact")):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--out", type=Path, required=True, help="PNG to write")
        p.add_argument("--spec", choices=sorted(SPECS), default="default")
        p.add_argument("--left", action="store_true", help="a left hand")
        if name in ("poses", "solved"):
            p.add_argument("--style", choices=sorted(STYLES), default="skin")
    args = ap.parse_args(argv)
    spec = SPECS[args.spec].mirrored() if args.left else SPECS[args.spec]
    sheet = {"model": lambda: model_sheet(spec), "poses": lambda: drawn_sheet(spec, STYLES[args.style]), "solved": lambda: solved_sheet(spec, STYLES[args.style])}[args.cmd]()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
