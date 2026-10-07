"""Lay out a character's eras side by side: still, date, name, model."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TILE_H = 256
PAD = 12
CAPTION_H = 92
BG = (28, 30, 38, 255)
FG = (230, 232, 240, 255)
DIM = (150, 156, 172, 255)


@dataclasses.dataclass
class Tile:
    image: Path | None
    lines: list[str]


def character_bbox(image: Image.Image):
    """The box around the drawn character. Most stills are transparent; the
    earliest eras are opaque, so the character is whatever differs from the
    corner colour."""
    from PIL import ImageChops

    alpha_box = image.getchannel("A").getbbox()
    if alpha_box and alpha_box != (0, 0, *image.size):
        return alpha_box
    flat = Image.new("RGBA", image.size, image.getpixel((0, 0)))
    return ImageChops.difference(image, flat).convert("L").point(lambda v: 255 if v > 12 else 0).getbbox() or alpha_box


def _font(size: int):
    for name in ("DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw, text: str, font, width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def compose(title: str, tiles: list[Tile], *, per_row: int = 6, tile_w: int = 190) -> Image.Image:
    rows = [tiles[i : i + per_row] for i in range(0, len(tiles), per_row)] or [[]]
    title_h = 44
    width = PAD + per_row * (tile_w + PAD)
    height = title_h + len(rows) * (TILE_H + CAPTION_H + PAD) + PAD
    sheet = Image.new("RGBA", (width, height), BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((PAD, 10), title, font=_font(24), fill=FG)
    body, small = _font(13), _font(11)
    for r, row in enumerate(rows):
        top = title_h + r * (TILE_H + CAPTION_H + PAD)
        for c, tile in enumerate(row):
            left = PAD + c * (tile_w + PAD)
            draw.rectangle([left, top, left + tile_w, top + TILE_H], fill=(40, 43, 54, 255))
            if tile.image and tile.image.exists():
                with Image.open(tile.image) as raw:
                    art = raw.convert("RGBA")
                    art = art.crop(character_bbox(art) or (0, 0, *art.size))
                scale = min((tile_w - 16) / art.width, (TILE_H - 16) / art.height)
                scale = min(scale, 4.0)
                size = (max(1, int(art.width * scale)), max(1, int(art.height * scale)))
                art = art.resize(size, Image.NEAREST if scale >= 2 else Image.LANCZOS)
                sheet.alpha_composite(
                    art, (left + (tile_w - size[0]) // 2, top + TILE_H - 8 - size[1])
                )
            else:
                draw.text((left + 10, top + TILE_H // 2), "no render", font=body, fill=DIM)
            y = top + TILE_H + 6
            for i, line in enumerate(tile.lines):
                font = body if i == 0 else small
                colour = FG if i == 0 else DIM
                for part in _wrap(draw, line, font, tile_w):
                    if y > top + TILE_H + CAPTION_H - 10:
                        break
                    draw.text((left, y), part, font=font, fill=colour)
                    y += 15 if i == 0 else 13
    return sheet


def stack(title: str, sheets: list[Image.Image]) -> Image.Image:
    """Several lineages, one under another, under a shared title."""
    title_h = 44
    width = max(sheet.width for sheet in sheets)
    height = title_h + sum(sheet.height for sheet in sheets)
    out = Image.new("RGBA", (width, height), BG)
    ImageDraw.Draw(out).text((PAD, 10), title, font=_font(26), fill=FG)
    y = title_h
    for sheet in sheets:
        out.alpha_composite(sheet, (0, y))
        y += sheet.height
    return out
