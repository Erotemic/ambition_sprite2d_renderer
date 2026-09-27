"""Contact sheets and timed GIFs of player_robot_v3 rows, for reviewing motion.

    python scripts/preview_player_robot_v3_rows.py grid OUT.png ROW[,ROW...] [--scale 2]
    python scripts/preview_player_robot_v3_rows.py gif OUT.gif ROW [--scale 3] [--hold 400]

``grid`` lays each row out as a strip of its published frames (effects
included, the ground line in red) — the view for judging poses. ``gif`` plays
one row at the sheet's own frame duration, then holds on idle, which is the
view for judging timing: a pose that reads in a strip can still vanish in the
42 ms it is on screen.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.targets.characters import player_robot_v3 as robot  # noqa: E402

CROP = (20, 20, 215, 180)
BG = (60, 64, 80, 255)
GROUND = (255, 90, 90, 255)


def _frames(row: str, scale: int):
    doc = robot.load_doc()
    clip = doc.clips[row]
    n = int(clip["frames"])
    w, h = CROP[2] - CROP[0], CROP[3] - CROP[1]
    out = [
        robot.render_frame(row, i, n).crop(CROP).resize((w * scale, h * scale), Image.NEAREST)
        for i in range(n)
    ]
    return out, int(clip["duration_ms"])


def _ground(draw: ImageDraw.ImageDraw, top: int, width: int, scale: int) -> None:
    y = top + (doc_ground() - CROP[1]) * scale
    draw.line([(0, y), (width, y)], fill=GROUND, width=1)


def doc_ground() -> float:
    return float(robot.load_doc().frame["ground_y"])


def grid(out: Path, rows: list[str], scale: int) -> None:
    strips = [(row, *_frames(row, scale)) for row in rows]
    fw, fh = strips[0][1][0].size
    cols = max(len(frames) for _row, frames, _ms in strips)
    sheet = Image.new("RGBA", (fw * cols, (fh + 14) * len(strips)), BG)
    draw = ImageDraw.Draw(sheet)
    for r, (row, frames, ms) in enumerate(strips):
        top = r * (fh + 14)
        draw.text((4, top + 1), f"{row}  {len(frames)} x {ms} ms", fill="white")
        for i, frame in enumerate(frames):
            sheet.alpha_composite(frame, (i * fw, top + 14))
        _ground(draw, top + 14, sheet.width, scale)
    sheet.save(out)


def gif(out: Path, row: str, scale: int, hold_ms: int) -> None:
    frames, ms = _frames(row, scale)
    idle, _ = _frames("idle", scale)
    step = 20  # GIF delays are centiseconds; 20 ms is the finest browsers honour
    timeline = []
    for t in range(0, len(frames) * ms + hold_ms, step):
        timeline.append(frames[t // ms] if t < len(frames) * ms else idle[0])
    images = []
    for frame in timeline:
        canvas = Image.new("RGBA", frame.size, BG)
        canvas.alpha_composite(frame)
        _ground(ImageDraw.Draw(canvas), 0, canvas.width, scale)
        images.append(canvas.convert("RGB").quantize(64))
    images[0].save(out, save_all=True, append_images=images[1:], duration=step, loop=0)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grid")
    g.add_argument("out", type=Path)
    g.add_argument("rows")
    g.add_argument("--scale", type=int, default=2)
    a = sub.add_parser("gif")
    a.add_argument("out", type=Path)
    a.add_argument("row")
    a.add_argument("--scale", type=int, default=3)
    a.add_argument("--hold", type=int, default=400)
    args = parser.parse_args(argv)
    if args.cmd == "grid":
        grid(args.out, args.rows.split(","), args.scale)
    else:
        gif(args.out, args.row, args.scale, args.hold)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
