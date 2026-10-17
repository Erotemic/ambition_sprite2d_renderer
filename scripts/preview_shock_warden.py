#!/usr/bin/env python3
"""Render Shock Warden pose review art from the actual SVG rig.

    uv run python scripts/preview_shock_warden.py --output /tmp/shock_warden.png
    uv run python scripts/preview_shock_warden.py --gif-output /tmp/shock_warden.gif

The preview keeps one scale and one camera across frames. Nothing is painted
as a second art source.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument

RIG = (ROOT / "ambition_sprite2d_renderer/targets/characters/rigged"
       / "shock_warden/shock_warden.rig.json")
BG = "#171e2a"
PANEL = "#262f3b"
INK = "#f0efe9"
MUTED = "#aebdcb"
GOLD = "#f0c16c"


def font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def draw_pose(sheet: Image.Image, doc: RigDocument, clip: str,
              frame: int, count: int, rect, *, scale: float = 1.5) -> None:
    """Crop the still pose to its painted bounds for a readable review."""
    x, y, width, height = rect
    image = doc.render_frame(clip, frame, count)
    bbox = image.getbbox()
    if bbox is None:
        raise ValueError(f"empty rig frame: {clip}[{frame}]")
    l, t, r, b = bbox
    image = image.crop((max(0, l - 10), max(0, t - 10),
                        min(image.width, r + 10), min(image.height, b + 10)))
    factor = min(scale, width / image.width, height / image.height)
    w, h = int(round(image.width * factor)), int(round(image.height * factor))
    image = image.resize((w, h), Image.Resampling.LANCZOS)
    sheet.paste(image, (x + (width - w) // 2, y + (height - h) // 2), image)


def review(doc: RigDocument) -> Image.Image:
    sheet = Image.new("RGB", (1860, 1150), BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((50, 28), "SHOCK WARDEN", font=font(43, True), fill=INK)
    draw.text((52, 89), "Programmatic SVG  /  editable skeletal parts  /  Castle Godwin concept", font=font(20), fill=MUTED)
    draw.line((50, 132, 1812, 132), fill=GOLD, width=2)
    draw.rounded_rectangle((45, 160, 584, 1102), radius=20, fill=PANEL)
    draw.text((70, 188), "IDLE / SILHOUETTE", font=font(25, True), fill=GOLD)
    draw_pose(sheet, doc, "idle", 0, 8, (55, 235, 510, 500), scale=1.85)
    draw.text((72, 756), "SHIELD  /  BATON  /  ARMORED BODY", font=font(19, True), fill=INK)
    draw.text((72, 797), "Test at smaller game sizes", font=font(17), fill=MUTED)
    rest = doc.render_frame("idle", 0, 8)
    for i, height in enumerate((125, 95, 65)):
        factor = height / rest.height
        sample = rest.resize((round(rest.width * factor), height), Image.Resampling.LANCZOS)
        x = 70 + i * 158
        sheet.paste(sample, (x, 854), sample)
        draw.text((x + 22, 992), f"{height} px", font=font(17), fill=MUTED)
    poses = [
        ("GUARD", "guard", 4, 8),
        ("BRACE", "brace", 4, 9),
        ("SHIELD BASH", "shield_bash", 6, 12),
        ("BATON WINDUP", "baton_attack", 4, 11),
        ("BATON STRIKE", "baton_attack", 7, 11),
        ("VULNERABLE", "recovery", 3, 8),
    ]
    x0, y0, w, h, gap = 614, 160, 393, 453, 14
    for i, (title, clip, idx, count) in enumerate(poses):
        col = i % 3
        row = i // 3
        x, y = x0 + col * (w + gap), y0 + row * (h + gap)
        draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=PANEL)
        draw.text((x + 19, y + 15), title, font=font(22, True), fill=GOLD)
        draw_pose(sheet, doc, clip, idx, count, (x + 7, y + 58, w - 14, h - 80), scale=1.40)
    draw.text((619, 1087), f"{len(doc.bones)} BONES   /   {len(doc.parts)} PARTS   /   {len(doc.clips)} CLIPS",
              font=font(18, True), fill=MUTED)
    return sheet


def animate(doc: RigDocument, animation: str) -> list[Image.Image]:
    frames = []
    n = doc.clips[animation]["frames"]
    for i in range(n):
        canvas = Image.new("RGBA", (560, 370), "#252d3a")
        pose = doc.render_frame(animation, i, n)
        pose = pose.resize((round(pose.width * 1.2), round(pose.height * 1.2)),
                           Image.Resampling.LANCZOS)
        canvas.alpha_composite(pose, ((canvas.width - pose.width) // 2,
                                      (canvas.height - pose.height) // 2))
        frames.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE))
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("shock_warden_review.png"))
    parser.add_argument("--gif-output", type=Path)
    parser.add_argument("--animation", choices=("shield_bash", "baton_attack", "walk", "brace"),
                        default="shield_bash")
    args = parser.parse_args()
    doc = RigDocument.load(RIG)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    review(doc).save(args.output)
    print(args.output)
    if args.gif_output is not None:
        args.gif_output.parent.mkdir(parents=True, exist_ok=True)
        frames = animate(doc, args.animation)
        ms = doc.clips[args.animation]["duration_ms"]
        frames[0].save(args.gif_output, save_all=True, append_images=frames[1:],
                       duration=ms, loop=0, disposal=2)
        print(args.gif_output)


if __name__ == "__main__":
    main()
