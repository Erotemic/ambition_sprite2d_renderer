"""Draw the parallax scenes.

    python -m ambition_sprite2d_renderer.backgrounds draw --out-dir DIR [THEME ...]
    python -m ambition_sprite2d_renderer.backgrounds preview OUT.png [THEME ...]

`draw` publishes `<theme>_<layer>.png` for each layer of each scene.
`preview` writes one picture of what a 16:9 view of the game shows of each
scene: the camera at the middle of its room, and then at the top and at the
bottom. It does not run the game.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image

from . import scenes

# A shared machine: this is the most jobs a publish starts.
MAX_JOBS = 6


def _render(job: tuple[str, str]) -> tuple[str, str, Image.Image]:
    theme, layer = job
    return theme, layer, scenes.render(theme, layer)


def _render_all(themes: list[str]) -> dict[str, dict[str, Image.Image]]:
    jobs = [(theme, layer) for theme in themes for layer in scenes.LAYERS]
    out: dict[str, dict[str, Image.Image]] = {theme: {} for theme in themes}
    with ProcessPoolExecutor(max_workers=min(MAX_JOBS, len(jobs))) as pool:
        for theme, layer, image in pool.map(_render, jobs):
            out[theme][layer] = image
    return out


def _themes(names: list[str]) -> list[str]:
    unknown = [name for name in names if name not in scenes.THEMES]
    if unknown:
        raise SystemExit(f"no scene named {unknown}; the scenes are {sorted(scenes.THEMES)}")
    return names or list(scenes.THEMES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ambition_sprite2d_renderer.backgrounds", description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    draw = sub.add_parser("draw", help="publish the layers of each scene")
    draw.add_argument("--out-dir", type=Path, required=True)
    draw.add_argument("themes", nargs="*")
    preview = sub.add_parser("preview", help="one picture of what the game shows of each scene")
    preview.add_argument("out", type=Path)
    preview.add_argument("themes", nargs="*")
    preview.add_argument("--cameras", default="0", help="camera heights to show, of -1 (top), 0, 1 (bottom)")
    args = parser.parse_args(argv)

    themes = _themes(args.themes)
    rendered = _render_all(themes)
    if args.command == "draw":
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for theme, layers in rendered.items():
            for layer, image in layers.items():
                path = args.out_dir / f"{theme}_{layer}.png"
                image.save(path)
                print(path)
        return 0
    cameras = [float(part) for part in args.cameras.split(",")]
    w, h = 1280, 720
    sheet = Image.new("RGB", (w * len(cameras), h * len(themes)))
    for row, theme in enumerate(themes):
        for column, camera in enumerate(cameras):
            sheet.paste(scenes.view(rendered[theme], (w, h), (0.0, camera)).convert("RGB"), (column * w, row * h))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
