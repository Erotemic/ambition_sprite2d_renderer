"""A review sheet of a Polygon fighter's rows: every frame of each row, side
by side, on a flat ground line, at the published render's own scale.

For the reaction-pose pass (`docs/planning/demos/smash-expressive-fighter-poses.md`):
render the fallback rows before the new keys are written, then the new rows,
and compare the two sheets at the same scale.

    python -m ambition_sprite2d_renderer.devtools.reaction_review pointed_polygon \\
        launch,meteor,hit --out /tmp/old.png [--silhouette]

`--gif DIR` also writes one animated preview per row, facing right and left
side by side, at `--scale` of the render (the gameplay scale is about 0.35).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from .pose_core import load_target
from ..core.measure import visible_bbox


def sheet(fighter: str, rows: list[str], silhouette: bool = False) -> Image.Image:
    target = load_target(fighter)
    clips = target._prepared().library.clips
    images = []
    for row in rows:
        clip = clips[row]
        frames = [target._render_frame(row, i, clip.frame_count) for i in range(clip.frame_count)]
        images.append((row, frames))
    # The floor every grounded row stands on: idle's lowest visible row.
    idle = clips["idle"]
    floor = max(
        (visible_bbox(target._render_frame("idle", i, idle.frame_count)) or (0, 0, 0, 0))[3]
        for i in range(idle.frame_count)
    )
    fw = max(f.width for _, fs in images for f in fs)
    fh = max(f.height for _, fs in images for f in fs)
    cols = max(len(fs) for _, fs in images)
    label = 18
    out = Image.new("RGBA", (cols * fw, len(images) * (fh + label)), (236, 236, 240, 255))
    draw = ImageDraw.Draw(out)
    for r, (row, frames) in enumerate(images):
        y0 = r * (fh + label)
        draw.text((4, y0 + 2), row, fill=(20, 20, 30, 255))
        draw.line([(0, y0 + label + floor), (cols * fw, y0 + label + floor)], fill=(200, 60, 60, 255))
        for c, frame in enumerate(frames):
            if silhouette:
                alpha = frame.getchannel("A")
                frame = Image.new("RGBA", frame.size, (20, 20, 30, 255))
                frame.putalpha(alpha)
            out.alpha_composite(frame, (c * fw, y0 + label))
    return out


def previews(fighter: str, rows: list[str], out_dir: Path, scale: float) -> list[Path]:
    """One looping GIF per row: the row facing right, then mirrored."""
    target = load_target(fighter)
    clips = target._prepared().library.clips
    written = []
    for row in rows:
        clip = clips[row]
        frames = []
        for i in range(clip.frame_count):
            frame = target._render_frame(row, i, clip.frame_count)
            w, h = max(1, round(frame.width * scale)), max(1, round(frame.height * scale))
            frame = frame.resize((w, h), Image.LANCZOS)
            pair = Image.new("RGBA", (2 * w, h), (236, 236, 240, 255))
            pair.alpha_composite(frame, (0, 0))
            pair.alpha_composite(frame.transpose(Image.FLIP_LEFT_RIGHT), (w, 0))
            frames.append(pair.convert("RGB"))
        path = out_dir / f"{fighter}_{row}.gif"
        frames[0].save(path, save_all=True, append_images=frames[1:],
                       duration=clip.frame_duration_ms, loop=0)
        written.append(path)
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("fighter")
    parser.add_argument("rows", help="comma-separated row names")
    parser.add_argument("--out", required=True)
    parser.add_argument("--silhouette", action="store_true", help="flat silhouettes, to judge shape before detail")
    parser.add_argument("--gif", type=Path, help="also write an animated preview of each row here")
    parser.add_argument("--scale", type=float, default=1.0, help="the previews' scale of the render")
    args = parser.parse_args(argv)
    image = sheet(args.fighter, args.rows.split(","), args.silhouette)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    image.save(args.out)
    print(args.out, image.size)
    if args.gif:
        args.gif.mkdir(parents=True, exist_ok=True)
        for path in previews(args.fighter, args.rows.split(","), args.gif, args.scale):
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
