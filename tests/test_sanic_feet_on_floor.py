"""Sanic's feet are on the floor the game stands him on, in both forms.

The game stands a body on the bottom of its published body box and draws the
frame on that box; a locomotion row is drawn on the idle body. So the drawn
soles of a grounded row must be on the bottom of the idle body (and of the
row's own body), or he floats. Regression: the super glow was measured as
body (10 px of air under his feet), the resampling fringe of every frame was
measured as body (3 px), and the sprint's feet ran round a figure 8 that hung
up to 14 px above the ground.

The publish is the real one (``_render_form``), cut to the grounded rows.
"""
from __future__ import annotations

import numpy as np
import pytest
import yaml
from PIL import Image

from ambition_sprite2d_renderer.targets.characters import sanic

#: Alpha of paint that is part of the figure: the shoe and its ink, not the
#: glow (at most 0.55 opaque) and not the resampling fringe.
SOLID = 192
#: Rows drawn on the idle body while he stands or runs.
LOCOMOTION = ("idle", "walk", "run", "sprint")
#: Rows with a foot on the ground in every frame (their own body is the floor).
GROUNDED = LOCOMOTION + ("skid", "block", "crouch")


def _publish(monkeypatch, tmp_path, target, skin):
    rows = [row for row in sanic.ROWS if row[0] in GROUNDED]
    monkeypatch.setattr(sanic, "ROWS", rows)
    monkeypatch.setattr(sanic, "ANIMATION_KEY_MAP", {name: name for name, _n, _ms in rows})
    # The part flipbook is a separate product of the same frames.
    monkeypatch.setattr(sanic, "publish_rig_flipbook", lambda *args, **kwargs: {})
    meta = sanic.TARGETS[target]["actor_metadata"]
    sanic._render_form(target, skin, meta, tmp_path)
    return yaml.safe_load((tmp_path / f"{target}_spritesheet.yaml").read_text())


def _lowest_sole(manifest, sheet, row_name):
    """The bottom (one past the last row) of the solid paint of a row, in frame pixels."""
    row = next(row for row in manifest["rows"] if row["animation"] == row_name)
    lowest = 0
    for rect in row["rects"]:
        alpha = sheet[rect["y"]:rect["y"] + rect["h"], rect["x"]:rect["x"] + rect["w"], 3]
        solid = np.where((alpha >= SOLID).any(axis=1))[0]
        lowest = max(lowest, rect["off"][1] + int(solid.max()) + 1)
    return lowest


def _body_bottom(manifest, row_name):
    box = manifest["body_metrics"]["animations"][row_name]["hurtbox"]["bbox"]
    return box["y"] + box["h"]


@pytest.mark.parametrize("target, skin", [("sanic", sanic.NORMAL), ("super_sanic", sanic.SUPER_SKIN)])
def test_a_grounded_pose_stands_its_soles_on_its_body_bottom(monkeypatch, tmp_path, target, skin):
    manifest = _publish(monkeypatch, tmp_path, target, skin)
    sheet = np.array(Image.open(tmp_path / manifest["image"]).convert("RGBA"))
    floor = _body_bottom(manifest, "idle")
    gaps = {}
    for row in GROUNDED:
        sole = _lowest_sole(manifest, sheet, row)
        gaps[row] = {"own body": _body_bottom(manifest, row) - sole}
        if row in LOCOMOTION:
            gaps[row]["idle body"] = floor - sole
    off = {row: gap for row, gap in gaps.items() if any(abs(px) > 1 for px in gap.values())}
    assert not off, f"{target}: px from the lowest drawn sole down to the floor: {off}"
