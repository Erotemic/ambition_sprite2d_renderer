"""Mary-O's transform flipbook is a hybrid: her walk from parts, every other
row left to the baked sheet (rig packet 9).

Her ``RigDocument`` paints every frame from rigid sprite parts, so the
flipbook is recorded from the real render (``build_rig_flipbook``). Each walk
frame is recomposed from the published part atlas and diffed against the same
frame of the PUBLISHED sheet, with the pirates' bound (2.5%,
``part_flipbook.parity``). Measured on the short form before this test was
written: the worst walk frame is 1.74%, where a part sits on a half pixel that
the render rounds.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from PIL import Image

from ambition_sprite2d_renderer.authoring.part_flipbook import parity
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_model import FIRE_FORM, SHORT_FORM, TALL_FORM
from ambition_sprite2d_renderer.targets.characters.mary_o_v2 import PART_ROWS, _render_form_with_products

_PARITY_BOUND = 0.025


def _published_frame(atlas, row, index, frame_size):
    rect = row["rects"][index]
    frame = Image.new("RGBA", frame_size, (0, 0, 0, 0))
    frame.paste(
        atlas.crop((rect["x"], rect["y"], rect["x"] + rect["w"], rect["y"] + rect["h"])),
        tuple(rect["off"]),
    )
    return frame


@pytest.mark.parametrize("form", [SHORT_FORM, TALL_FORM, FIRE_FORM], ids=lambda form: form.target_name)
def test_her_walk_is_drawn_from_parts_and_every_other_row_stays_baked(form, tmp_path: Path):
    paths, products = _render_form_with_products(form, tmp_path)
    flipbook = products["parts"]
    ron = tmp_path / f"{form.target_name}_parts.ron"
    assert ron in paths and ron.read_text() == flipbook.to_ron()
    assert list(flipbook.clips) == list(PART_ROWS)
    assert flipbook.baked_clips == [row for row, _count, _ms in form.rows if row not in PART_ROWS]

    sheet = yaml.safe_load(Path(products["outputs"]["yaml"]).read_text())
    atlas = Image.open(Path(products["outputs"]["yaml"]).parent / sheet["image"]).convert("RGBA")
    rows = {row["animation"]: row for row in sheet["rows"]}
    failures = []
    for row, (_duration, frames) in flipbook.clips.items():
        assert len(frames) == len(rows[row]["rects"]), row
        for index in range(len(frames)):
            reference = _published_frame(atlas, rows[row], index, flipbook.frame_size)
            wrong = parity(reference, flipbook.recompose(row, index))
            if wrong > _PARITY_BOUND:
                failures.append(f"{row}[{index}]: {wrong:.4f}")
    assert not failures, "walk frames the flipbook does not reproduce:\n" + "\n".join(failures)
