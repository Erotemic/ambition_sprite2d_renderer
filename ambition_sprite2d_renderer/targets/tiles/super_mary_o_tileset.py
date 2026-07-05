"""Compact SMB1-style tile atlas for the Super Mary-O push.

The emphasis is quick level-blockout value: brick variants, a handful of
solid ground tiles, and pipe segments that match the standalone pipe prop.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import yaml
from PIL import Image, ImageDraw, ImageFont

from ..super_mary_o_common import (
    BRICK,
    BRICK_DARK,
    BRICK_LIGHT,
    GROUND_BROWN,
    GROUND_BROWN_DARK,
    GROUND_BROWN_LIGHT,
    OUTLINE,
    PIPE_GREEN,
    PIPE_GREEN_DARK,
    PIPE_GREEN_LIGHT,
    SKY_BLUE,
    label_font,
)

TARGET_NAME = "super_mary_o_tileset"
TILE = 16
COLS = 4
ROWS = 4
BG = (0, 0, 0, 0)
FONT = label_font(11)


@dataclass(frozen=True)
class TileSpec:
    key: str
    category: str
    collision: str
    layer: str
    description: str


TILES: Sequence[TileSpec] = [
    TileSpec("blank", "utility", "none", "MaryDecor", "transparent spacer"),
    TileSpec("brick_plain", "brick", "solid", "MarySolids", "main brick block"),
    TileSpec("brick_cracked", "brick", "solid", "MarySolids", "breakable-looking brick"),
    TileSpec("brick_shadowed", "brick", "solid", "MarySolids", "brick with lower shadow"),
    TileSpec("block_solid", "block", "solid", "MarySolids", "plain solid bonus block"),
    TileSpec("coin_block", "block", "solid", "MarySolids", "coin-marker block"),
    TileSpec("ground_top", "ground", "solid", "MarySolids", "top edge of dirt ground"),
    TileSpec("ground_fill", "ground", "solid", "MarySolids", "interior dirt fill"),
    TileSpec("pipe_cap_left", "pipe", "solid", "MarySolids", "left cap of pipe"),
    TileSpec("pipe_cap_right", "pipe", "solid", "MarySolids", "right cap of pipe"),
    TileSpec("pipe_body_left", "pipe", "solid", "MarySolids", "left body segment of pipe"),
    TileSpec("pipe_body_right", "pipe", "solid", "MarySolids", "right body segment of pipe"),
    TileSpec("ground_edge_left", "ground", "solid", "MarySolids", "left ledge edge"),
    TileSpec("ground_edge_right", "ground", "solid", "MarySolids", "right ledge edge"),
    TileSpec("brick_alt", "brick", "solid", "MarySolids", "alternate brick palette"),
    TileSpec("ground_mixed", "ground", "solid", "MarySolids", "ground fill with pebble mix"),
]



def _new_tile() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (TILE, TILE), BG)
    return img, ImageDraw.Draw(img, "RGBA")



def _brick_lines(draw: ImageDraw.ImageDraw, *, fill, mortar, variant: str = "plain") -> None:
    draw.rectangle((0, 0, 15, 15), fill=fill, outline=OUTLINE, width=1)
    draw.line((0, 5, 15, 5), fill=mortar, width=1)
    draw.line((0, 10, 15, 10), fill=mortar, width=1)
    draw.line((4, 0, 4, 5), fill=mortar, width=1)
    draw.line((11, 0, 11, 5), fill=mortar, width=1)
    draw.line((7, 5, 7, 10), fill=mortar, width=1)
    draw.line((4, 10, 4, 15), fill=mortar, width=1)
    draw.line((11, 10, 11, 15), fill=mortar, width=1)
    if variant in {"cracked", "alt"}:
        draw.line((12, 2, 9, 6, 11, 8, 8, 12), fill=OUTLINE, width=1)
    if variant in {"shadowed", "alt"}:
        draw.rectangle((0, 12, 15, 15), fill=(88, 48, 23, 255))
    if variant == "alt":
        draw.rectangle((1, 1, 14, 3), fill=BRICK_LIGHT)



def _block_tile(coin: bool = False) -> Image.Image:
    img, draw = _new_tile()
    draw.rectangle((0, 0, 15, 15), fill=(210, 162, 76, 255), outline=OUTLINE, width=1)
    draw.rectangle((2, 2, 13, 13), outline=(244, 217, 142, 255), width=1)
    if coin:
        draw.ellipse((5, 4, 10, 11), fill=(248, 198, 60, 255), outline=OUTLINE, width=1)
        draw.line((7, 5, 7, 10), fill=OUTLINE, width=1)
    else:
        draw.rectangle((6, 5, 9, 10), fill=(248, 198, 60, 255), outline=OUTLINE, width=1)
    return img



def _ground_tile(kind: str) -> Image.Image:
    img, draw = _new_tile()
    draw.rectangle((0, 0, 15, 15), fill=GROUND_BROWN, outline=OUTLINE, width=1)
    if kind == "top":
        draw.rectangle((0, 0, 15, 4), fill=GROUND_BROWN_LIGHT)
        for x in (1, 5, 10, 13):
            draw.rectangle((x, 2, x + 1, 3), fill=(112, 173, 78, 255))
        for x, y in ((3, 8), (9, 11), (12, 7)):
            draw.rectangle((x, y, x + 1, y + 1), fill=GROUND_BROWN_DARK)
    else:
        for x, y in ((2, 3), (5, 8), (9, 4), (12, 10), (7, 12)):
            draw.rectangle((x, y, x + 2, y + 1), fill=GROUND_BROWN_DARK)
        if kind == "mixed":
            for x, y in ((3, 5), (11, 6), (6, 10)):
                draw.rectangle((x, y, x + 1, y + 1), fill=GROUND_BROWN_LIGHT)
    if kind == "edge_left":
        draw.rectangle((0, 0, 2, 15), fill=SKY_BLUE)
        draw.rectangle((2, 0, 3, 15), fill=(121, 187, 247, 255))
    if kind == "edge_right":
        draw.rectangle((13, 0, 15, 15), fill=SKY_BLUE)
        draw.rectangle((12, 0, 13, 15), fill=(121, 187, 247, 255))
    return img



def _pipe_tile(kind: str) -> Image.Image:
    img, draw = _new_tile()
    draw.rectangle((0, 0, 15, 15), fill=PIPE_GREEN, outline=OUTLINE, width=1)
    draw.rectangle((1, 1, 4, 14), fill=PIPE_GREEN_LIGHT)
    draw.rectangle((12, 1, 14, 14), fill=PIPE_GREEN_DARK)
    draw.line((5, 0, 5, 15), fill=(20, 99, 53, 255), width=1)
    draw.line((11, 0, 11, 15), fill=(20, 99, 53, 255), width=1)
    if kind.startswith("cap"):
        draw.rectangle((0, 0, 15, 5), fill=PIPE_GREEN, outline=OUTLINE, width=1)
        draw.rectangle((1, 1, 4, 4), fill=PIPE_GREEN_LIGHT)
        draw.rectangle((12, 1, 14, 4), fill=PIPE_GREEN_DARK)
        draw.rectangle((4, 5, 11, 7), fill=(10, 70, 39, 255))
    if kind.endswith("left"):
        draw.rectangle((8, 0, 15, 15), fill=PIPE_GREEN)
    if kind.endswith("right"):
        draw.rectangle((0, 0, 7, 15), fill=PIPE_GREEN)
    return img



def _tile_image(key: str) -> Image.Image:
    if key == "blank":
        return Image.new("RGBA", (TILE, TILE), BG)
    if key == "brick_plain":
        img, draw = _new_tile()
        _brick_lines(draw, fill=BRICK, mortar=BRICK_DARK)
        return img
    if key == "brick_cracked":
        img, draw = _new_tile()
        _brick_lines(draw, fill=BRICK, mortar=BRICK_DARK, variant="cracked")
        return img
    if key == "brick_shadowed":
        img, draw = _new_tile()
        _brick_lines(draw, fill=BRICK, mortar=BRICK_DARK, variant="shadowed")
        return img
    if key == "brick_alt":
        img, draw = _new_tile()
        _brick_lines(draw, fill=(190, 117, 62, 255), mortar=BRICK_DARK, variant="alt")
        return img
    if key == "block_solid":
        return _block_tile(False)
    if key == "coin_block":
        return _block_tile(True)
    if key == "ground_top":
        return _ground_tile("top")
    if key == "ground_fill":
        return _ground_tile("fill")
    if key == "ground_edge_left":
        return _ground_tile("edge_left")
    if key == "ground_edge_right":
        return _ground_tile("edge_right")
    if key == "ground_mixed":
        return _ground_tile("mixed")
    if key == "pipe_cap_left":
        return _pipe_tile("cap_left")
    if key == "pipe_cap_right":
        return _pipe_tile("cap_right")
    if key == "pipe_body_left":
        return _pipe_tile("body_left")
    if key == "pipe_body_right":
        return _pipe_tile("body_right")
    raise KeyError(key)



def _build_tilesheet() -> tuple[Image.Image, list[dict]]:
    sheet = Image.new("RGBA", (COLS * TILE, ROWS * TILE), BG)
    tile_entries: list[dict] = []
    for idx, spec in enumerate(TILES):
        img = _tile_image(spec.key)
        col = idx % COLS
        row = idx // COLS
        x = col * TILE
        y = row * TILE
        sheet.alpha_composite(img, (x, y))
        tile_entries.append(
            {
                "id": idx,
                "key": spec.key,
                "name": spec.key.replace("_", " "),
                "x": x,
                "y": y,
                "w": TILE,
                "h": TILE,
                "category": spec.category,
                "collision": spec.collision,
                "ldtk_layer": spec.layer,
                "description": spec.description,
            }
        )
    return sheet, tile_entries



def _preview_image(sheet: Image.Image) -> Image.Image:
    pad = 12
    label_h = 18
    cell_w = 96
    cell_h = TILE + label_h + 10
    preview = Image.new("RGBA", (COLS * cell_w + pad * 2, ROWS * cell_h + pad * 2), (24, 30, 44, 255))
    draw = ImageDraw.Draw(preview, "RGBA")
    for idx, spec in enumerate(TILES):
        col = idx % COLS
        row = idx // COLS
        cell_x = pad + col * cell_w
        cell_y = pad + row * cell_h
        x = cell_x + 8
        y = cell_y + 4
        tile = _tile_image(spec.key)
        draw.rounded_rectangle((cell_x, cell_y, cell_x + cell_w - 8, cell_y + cell_h - 6), radius=6, fill=(31, 38, 54, 255), outline=(84, 96, 118, 255), width=1)
        preview.alpha_composite(tile, (x, y))
        draw.rectangle((x - 1, y - 1, x + TILE, y + TILE), outline=(84, 96, 118, 255), width=1)
        draw.text((cell_x + 28, cell_y + 4), spec.key, fill=(232, 236, 244, 255), font=FONT)
        draw.text((cell_x + 28, cell_y + 18), spec.category, fill=(161, 183, 215, 255), font=FONT)
    return preview



def _manifest(entries: Sequence[dict]) -> dict:
    by_category: Dict[str, list[str]] = {}
    by_layer: Dict[str, list[str]] = {}
    for entry in entries:
        by_category.setdefault(entry["category"], []).append(entry["key"])
        by_layer.setdefault(entry["ldtk_layer"], []).append(entry["key"])
    return {
        "target": TARGET_NAME,
        "image": f"{TARGET_NAME}.png",
        "tile_width": TILE,
        "tile_height": TILE,
        "columns": COLS,
        "rows": ROWS,
        "tile_count": len(entries),
        "tiles": list(entries),
        "groups": {"by_category": by_category, "by_ldtk_layer": by_layer},
        "ldtk": {
            "suggested_tileset_name": "SuperMaryOTiles",
            "suggested_layers": ["MarySolids", "MaryDecor"],
        },
    }



def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sheet, entries = _build_tilesheet()
    manifest = _manifest(entries)

    png_path = out_dir / f"{TARGET_NAME}.png"
    yaml_path = out_dir / f"{TARGET_NAME}.yaml"
    preview_path = out_dir / f"{TARGET_NAME}_preview.png"
    sheet.save(png_path)
    preview = _preview_image(sheet)
    preview.save(preview_path)
    yaml_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return [png_path, yaml_path, preview_path]
