"""The pirate part flipbook draws the frames the sheet publishes.

Every frame is recomposed from the published part atlas and draw table and
diffed against the same frame of the PUBLISHED sheet, by D6's bounds (the game
repository's `docs/planning/engine/mary-o-part-realization.md`): at most 1% of
the drawn pixels wrong and no wrong blob over 6 pixels, at the continuous
replay tolerance.

A pirate frame is fitted by its own scale (``sheet_build.downsample``, 4.6x
to 5.4x, never whole), so each shape is resized where the frame's resize
samples it (``part_flipbook._sampled_as_the_frame``). The flipbook of 2026-10-02
transformed parts drawn at one scale and measured 5.5% and a blob of 69.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from PIL import Image

from ambition_sprite2d_renderer.authoring.part_flipbook import (
    CONTINUOUS_REPLAY_TOLERANCE,
    largest_wrong_blob,
    parity,
)
from ambition_sprite2d_renderer.authoring.sheet_build import ANIMATIONS
from ambition_sprite2d_renderer.targets.characters._pirate_common import (
    render_target_with_products,
)

_PARITY_BOUND = 0.01
_BLOB_BOUND = 6
#: Faithful costs texels here: a shape resized by its frame's own scale is
#: reused by no other frame. Measured 2026-10-03: 1.004 of the sheet's texels
#: (raider), 1.074 (admiral); the unfaithful flipbook before saved 35%. A ceiling, so a
#: flipbook that stops sharing what it can share shows.
_TEXEL_CEILING = 1.15


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
            candidate = flipbook.recompose(row, index)
            wrong = parity(reference, candidate, **CONTINUOUS_REPLAY_TOLERANCE)
            blob = largest_wrong_blob(reference, candidate, **CONTINUOUS_REPLAY_TOLERANCE)
            if wrong > _PARITY_BOUND or blob > _BLOB_BOUND:
                failures.append(f"{row}[{index}]: {wrong:.4f}, blob {blob}")
    assert not failures, "frames the flipbook does not reproduce:\n" + "\n".join(failures)
    cost = flipbook.packed_texels() / (atlas.width * atlas.height)
    assert cost <= _TEXEL_CEILING, f"the part atlas costs {cost:.3f} of the sheet's texels"
