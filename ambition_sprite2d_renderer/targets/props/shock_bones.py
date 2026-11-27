"""Paint the bone parts for a body that takes electric damage."""

from pathlib import Path

from PIL import Image

from ..characters import _humanoid_bone_art as bones
from ..characters._clockwork_enemy_art import Canvas

TARGET_NAME = "shock_bones"
PUBLICATION_TIERS = ["full"]
SHEET_FILES = ["shock_bones.png"]

CELL = 64
COLUMNS = 4
CENTER = (32, 32)


def render(out_dir, **_opts):
    """Put six bone parts into fixed cells with transparent margins."""
    palette = bones.FLASH
    painters = [
        lambda c: bones.skull(c, CENTER, palette=palette),
        lambda c: bones.trunk(c, (32, 52), (32, 12), palette),
        lambda c: bones.long_bone(c, (12, 32), (52, 32), 3.0, palette),
        lambda c: bones.paired_bones(c, (12, 32), (52, 32), 2.9, palette),
        lambda c: bones.hand(c, CENTER, 0, scale=1.4, palette=palette),
        lambda c: bones.foot(c, CENTER, scale=1.4, palette=palette),
    ]
    atlas = Image.new("RGBA", (COLUMNS * CELL, 2 * CELL))
    for index, paint in enumerate(painters):
        cell = Canvas((CELL, CELL))
        paint(cell)
        atlas.paste(cell.finish(), (index % COLUMNS * CELL, index // COLUMNS * CELL))

    path = Path(out_dir) / SHEET_FILES[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(path)
    return [path]
