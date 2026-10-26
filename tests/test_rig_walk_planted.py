"""A rig document's planted walk keeps a foot on the ground the body stands on.

The game draws every row of a sheet on the standing body, so the walk's feet
must reach the standing soles' line. Regression: FK walks swung the legs lower
than they stand (Shock Warden, 6 px in the floor) or rode the hip higher (Tech
Bro Disruptor, 3 px over it). ``frame.plant`` (``RigDocument.plant_offsets``)
puts each walk frame's lowest drawn row on the idle soles' line.
"""
from __future__ import annotations

import pytest

from ambition_sprite2d_renderer.core.measure import visible_bbox
from ambition_sprite2d_renderer.targets.characters import shock_warden, tech_bro_disruptor


@pytest.mark.parametrize("module", [shock_warden, tech_bro_disruptor], ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_every_walk_frame_stands_on_the_idle_soles(module):
    doc = module._doc()
    counts = {name: frames for name, frames, _ms in doc.rows()}
    floor = max(visible_bbox(doc.render_frame("idle", k, counts["idle"]))[3] for k in range(counts["idle"]))
    walk = [visible_bbox(doc.render_frame("walk", k, counts["walk"]))[3] for k in range(counts["walk"])]
    assert all(abs(floor - bottom) <= 1 for bottom in walk), (floor, walk)
