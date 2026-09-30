"""The pirate transform flipbook draws the frames the sheet publishes.

Every frame is recomposed from the published part atlas and draw table and
diffed against the same frame of the PUBLISHED sheet. The bound is 2.5% of the
drawn pixels (``part_flipbook.parity``: premultiplied RGBA within 64, one pixel
of slack for an edge that a separate resample moves over). Measured on all five
pirates the worst frame is 1.95%. A dropped hat reads 8.5%, a torso two pixels
off 7.9%, a sword turned the wrong way 4.0%.

The texel floor is a regression line, not the plan's 75%. Limbs and neck are
per-frame overlays, which is 92% of the flipbook's texels, and the plan's own
method (one overlay per frame) measures near the same 38%.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from PIL import Image

from ambition_sprite2d_renderer.authoring.part_flipbook import parity
from ambition_sprite2d_renderer.authoring.sheet_build import ANIMATIONS
from ambition_sprite2d_renderer.targets.characters._pirate_common import (
    render_target_with_products,
)

_PARITY_BOUND = 0.025
_SAVING_FLOOR = 0.35


def _published_frame(atlas, row, index, frame_size):
    rect = row["rects"][index]
    frame = Image.new("RGBA", frame_size, (0, 0, 0, 0))
    frame.paste(
        atlas.crop((rect["x"], rect["y"], rect["x"] + rect["w"], rect["y"] + rect["h"])),
        tuple(rect["off"]),
    )
    return frame


@pytest.mark.parametrize("kind", ["pirate_raider", "pirate_admiral"])
def test_the_flipbook_recomposes_every_published_frame(kind, tmp_path: Path):
    outputs, products = render_target_with_products(kind, tmp_path)
    flipbook = products["parts"]
    assert Path(outputs["parts"]).read_text() == flipbook.to_ron()
    sheet = yaml.safe_load(Path(outputs["yaml"]).read_text())
    atlas = Image.open(Path(outputs["yaml"]).parent / sheet["image"]).convert("RGBA")
    rows = {row["animation"]: row for row in sheet["rows"]}
    assert [(row, len(frames)) for row, (_d, frames) in flipbook.clips.items()] == [
        (row, count) for row, count, _ms in ANIMATIONS
    ]
    failures = []
    for row, (_duration, frames) in flipbook.clips.items():
        for index in range(len(frames)):
            reference = _published_frame(atlas, rows[row], index, flipbook.frame_size)
            wrong = parity(reference, flipbook.recompose(row, index))
            if wrong > _PARITY_BOUND:
                failures.append(f"{row}[{index}]: {wrong:.4f}")
    assert not failures, "frames the flipbook does not reproduce:\n" + "\n".join(failures)
    saving = 1.0 - flipbook.packed_texels() / (atlas.width * atlas.height)
    assert saving >= _SAVING_FLOOR, f"the part atlas saves only {saving:.3f} of the sheet's texels"
