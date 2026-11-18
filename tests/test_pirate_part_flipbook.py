"""The pirate part flipbook draws the frames the pirates are painted as.

Their sheets are published part-first (`build_sheet(parts=True)`): no page.
Published with ``AMBITION_PART_FIRST_AUDIT``, every frame is painted and the
flipbook's redraw held to the replay guard against it, by D6's bounds (the
game repository's `docs/planning/engine/mary-o-part-realization.md`): at
most 1% of the drawn pixels wrong and no wrong blob over 6 pixels, at the
continuous replay tolerance (`CONTINUOUS_REPLAY_PARITY`, `_BLOB`).

A pirate frame is fitted by its own scale (``sheet_build.downsample``, 4.6x
to 5.4x, never whole), so each shape is resized where the frame's resize
samples it (``part_flipbook._sampled_as_the_frame``). The flipbook of 2026-10-02
transformed parts drawn at one scale and measured 5.5% and a blob of 69.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ambition_sprite2d_renderer.authoring.part_flipbook import CONTINUOUS_REPLAY_BLOB, CONTINUOUS_REPLAY_PARITY
from ambition_sprite2d_renderer.targets.characters._pirate_common import (
    render_target_with_products,
)

#: Faithful costs texels here: a shape resized by its frame's own scale is
#: reused by no other frame. A ceiling on the part pages against the frames
#: they draw (every frame's whole cell), so a flipbook that stops sharing
#: what it can share shows. Measured 2026-11-18: raider 0.041, admiral
#: 0.022, quartermaster 0.062, lookout 0.068, navigator 0.058, Kernel Guide
#: 0.049.
_TEXEL_CEILING = 0.08


# Each of the five: each has its own build and its own headwear, and the
# quartermaster alone did not replay when the poses were made again (a publish
# of the five found it, this test with two of them did not).
@pytest.mark.parametrize("kind", [
    "pirate_raider", "pirate_admiral", "pirate_quartermaster", "pirate_lookout", "pirate_navigator",
    # Not a pirate: the Kernel Guide, on the same rig with its own rows.
    "kernel_guide",
])
def test_the_flipbook_replays_every_painted_frame(kind, tmp_path: Path, monkeypatch, capsys):
    from ambition_sprite2d_renderer.targets.characters import _pirate_common as crew
    from ambition_sprite2d_renderer.targets.characters import kernel_guide  # noqa: F401

    assert (CONTINUOUS_REPLAY_PARITY, CONTINUOUS_REPLAY_BLOB) == (0.01, 6), "D6's bounds are the guard's"
    monkeypatch.setenv("AMBITION_PART_FIRST_AUDIT", "1")
    outputs, products = render_target_with_products(kind, tmp_path)
    flipbook = products["parts"]
    assert Path(outputs["parts"]).read_text() == flipbook.to_ron()
    frames = sum(len(f) for _d, f in flipbook.clips.values())
    # The audit spoke for every frame (it raises on the first that fails).
    assert f"{frames} of {frames} frames replay the paint" in capsys.readouterr().out
    sheet = yaml.safe_load(Path(outputs["yaml"]).read_text())
    assert sheet.get("drawn_from_parts") is True and not outputs.get("spritesheet")
    assert [(row, len(f)) for row, (_d, f) in flipbook.clips.items()] == [
        (row, count) for row, count, _ms in crew.rows_of(kind)
    ]
    cost = flipbook.packed_texels() / (frames * int(sheet["frame_width"]) * int(sheet["frame_height"]))
    print(f"{kind}: part pages cost {cost:.3f} of the frames' texels")
    assert cost <= _TEXEL_CEILING, f"the part atlas costs {cost:.3f} of the frames' texels"
