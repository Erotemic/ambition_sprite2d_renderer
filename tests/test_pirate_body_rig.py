"""The pirate family's body rig describes the frames the sheet publishes.

Its joints are the skeleton the paint pass draws on, placed through the same
maps the frame pixels go through. So each hand must land on drawn art in every
frame of the PUBLISHED sheet; a wrong fit, a wrong crop offset or a wrong
parent composition puts it in empty air.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from PIL import Image

from ambition_sprite2d_renderer.authoring.body_rig import place
from ambition_sprite2d_renderer.targets.characters._pirate_common import (
    render_target_with_body_rig,
)

_TOLERANCE_PX = 3


def _world(product, frame):
    """Every joint's pose with its parent's chain, in joint order."""
    parents = dict(product.joints)
    out = {}
    for (name, _parent), pose in zip(product.joints, frame):
        out[name] = (pose, out.get(parents[name]))
    return out


def _place(chain, point):
    pose, parent = chain
    point = place(pose, point)
    return point if parent is None else _place(parent, point)


def _near_drawn_pixel(alpha, rect, point) -> bool:
    """``point`` is in published frame pixels; ``rect`` is where the frame's
    trimmed pixels sit in the atlas."""
    x = int(round(point[0])) - rect["off"][0]
    y = int(round(point[1])) - rect["off"][1]
    return any(
        0 <= x + dx < rect["w"]
        and 0 <= y + dy < rect["h"]
        and alpha.getpixel((rect["x"] + x + dx, rect["y"] + y + dy)) > 0
        for dy in range(-_TOLERANCE_PX, _TOLERANCE_PX + 1)
        for dx in range(-_TOLERANCE_PX, _TOLERANCE_PX + 1)
    )


@pytest.mark.parametrize("kind", ["pirate_admiral", "pirate_raider"])
def test_the_rig_hands_land_on_the_published_frame(kind, tmp_path: Path):
    outputs, product = render_target_with_body_rig(kind, tmp_path)
    assert product is not None
    assert Path(outputs["body_rig"]).read_text() == product.to_ron()
    sheet = yaml.safe_load(Path(outputs["yaml"]).read_text())
    feet = sheet["body_metrics"]["feet_pixel"]
    alpha = Image.open(Path(outputs["yaml"]).parent / sheet["image"]).getchannel("A")
    rows = {row["animation"]: row for row in sheet["rows"]}
    misses = []
    checked = 0
    for clip, (_loop, _duration, frames) in product.clips.items():
        for index, frame in enumerate(frames):
            rect = rows[clip]["rects"][index]
            chains = _world(product, frame)
            for name, joint, offset in product.attachments:
                if not name.startswith("hand"):
                    continue
                x, y = _place(chains[joint], offset)
                published = (x + feet["x"], y + feet["y"])
                checked += 1
                if not _near_drawn_pixel(alpha, rect, published):
                    misses.append(f"{clip}[{index}] {name} at {published}")
    assert checked > 40
    assert not misses, "hands in empty air:\n" + "\n".join(misses)
