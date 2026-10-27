"""Draw the parallax scenes.

    python -m ambition_sprite2d_renderer.backgrounds draw --out-dir DIR [THEME ...]
    python -m ambition_sprite2d_renderer.backgrounds preview OUT.png [THEME ...]
    python -m ambition_sprite2d_renderer.backgrounds parts --out-dir DIR [--look LOOK]
    python -m ambition_sprite2d_renderer.backgrounds parts-preview OUT.png [--looks A,B]

`draw` publishes `<theme>_<layer>.png` for each layer of each scene, and
`<theme>_flat.png`, the one picture a tier with no parallax draws (`scenes.flat`).
`preview` writes one picture of what a 16:9 view of the game shows of each
scene: the camera at the middle of its room, and then at the top and at the
bottom. It does not run the game.
`parts` publishes the parts of the Mockingbird's space, `<part>.png`
(`sky_parts.py`). `parts-preview` writes one labelled sheet with a row for
each look of them, at three moments of the climb, as the game poses them.

`draw` and `parts` record which callable drew each file (`provenance.py`).
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image

from .. import provenance
if __name__ == "__main__":
    from .. import read_record
    read_record.start(provenance.repo_root(), [provenance.asset_root(), Path(__file__).resolve().parents[2] / ".cache"])
from . import foregrounds, room_look_sky, scenes, sky_parts

# A shared machine: this is the most jobs a publish starts.
MAX_JOBS = 6


def _render(job: tuple[str, str]) -> tuple:
    theme, layer = job
    from .. import read_record
    if read_record.recorded() is None:
        read_record.start(provenance.repo_root(), [provenance.asset_root(), Path(__file__).resolve().parents[2] / ".cache"])
    image = scenes.render(theme, layer)
    return theme, layer, image, read_record.recorded() or [], read_record.directories()


def _render_all(themes: list[str]) -> dict[str, dict[str, Image.Image]]:
    jobs = [(theme, layer) for theme in themes for layer in scenes.LAYERS]
    out: dict[str, dict[str, Image.Image]] = {theme: {} for theme in themes}
    with ProcessPoolExecutor(max_workers=min(MAX_JOBS, len(jobs))) as pool:
        from .. import read_record
        for theme, layer, image, files, directories in pool.map(_render, jobs):
            read_record.merge(files, directories)
            out[theme][layer] = image
    return out


def _drawn_by(theme: str, layer: str):
    """The callable that draws one layer of one scene (`scenes.render`)."""
    if layer == scenes.FOREGROUND:
        return foregrounds.render
    if theme in room_look_sky.THEME_KEYS:
        return room_look_sky.render_look_layer
    return scenes.SCENES[theme]


def plan(dest: Path, themes: list[str]) -> provenance.Book:
    """What `draw` publishes into `dest`, by theme, and what draws each file:
    the record of a publish, and the plan of one that has not run here."""
    book = provenance.Book("parallax_theme", dest, "./scripts/regen/backgrounds.sh  # theme {unit}", "backgrounds")
    for theme in _themes(themes):
        for layer in scenes.LAYERS:
            book.add(theme, dest / f"{theme}_{layer}.png", _drawn_by(theme, layer))
        book.add(theme, dest / f"{theme}_flat.png", scenes.flat)
    return book


def parts_plan(dest: Path) -> provenance.Book:
    """What `parts` publishes into `dest`, one unit for each part."""
    book = provenance.Book("sky_part", dest, "./scripts/regen/backgrounds.sh  # sky part {unit}", "backgrounds")
    for name in sky_parts.PARTS:
        book.add(name, dest / f"{name}.png", sky_parts.PARTS[name])
    return book


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
    parts = sub.add_parser("parts", help="publish the parts of the Mockingbird's space")
    parts.add_argument("--out-dir", type=Path, required=True)
    parts.add_argument("--look", default=sky_parts.PUBLISHED, choices=sorted(sky_parts.LOOKS))
    parts_preview = sub.add_parser("parts-preview", help="a labelled sheet of the looks of the space parts")
    parts_preview.add_argument("out", type=Path)
    parts_preview.add_argument("--looks", default=",".join(sky_parts.LOOKS))
    args = parser.parse_args(argv)

    if args.command == "parts":
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for name in sky_parts.PARTS:
            path = args.out_dir / f"{name}.png"
            sky_parts.render(name, args.look).save(path)
            print(path)
        parts_plan(args.out_dir).write()
        return 0
    if args.command == "parts-preview":
        backdrop = scenes.view(_render_all(["open_sky"])["open_sky"], (1280, 720))
        moments = [("climbing (ascent 0.5)", 0.5, None), ("nearly in space (0.85)", 0.85, None), ("in space, moon on its lane", 1.0, 0.42)]
        sheet = sky_parts.candidate_sheet(args.looks.split(","), backdrop, moments)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(args.out)
        print(args.out)
        return 0
    themes = _themes(args.themes)
    rendered = _render_all(themes)
    if args.command == "draw":
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for theme, layers in rendered.items():
            for layer, image in layers.items():
                path = args.out_dir / f"{theme}_{layer}.png"
                if image is None:
                    # A scene with no foreground. The game asks for each layer
                    # of each theme, so the layer is an empty picture.
                    image = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
                image.save(path)
                print(path)
            path = args.out_dir / f"{theme}_flat.png"
            scenes.flat(layers).save(path)
            print(path)
        plan(args.out_dir, themes).write()
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
