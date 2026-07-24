"""Literal snakes riding a paper airplane."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from ._snakes_on_planes_common import PAPER_SPEC, actor_metadata, render_target

TARGET_NAME = PAPER_SPEC.target_name
ACTOR_METADATA = actor_metadata(PAPER_SPEC)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return render_target(PAPER_SPEC, out_dir)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render Snakes on a Paper Plane.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME,
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
