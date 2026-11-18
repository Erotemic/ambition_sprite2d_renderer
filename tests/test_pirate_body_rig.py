"""The pirate family's body rig describes the frames the game draws.

Its joints are the skeleton the paint pass draws on, placed through the same
maps the frame pixels go through. So each hand must land on drawn art in every
frame the PUBLISHED part flipbook draws (the sheet is part-first: no page); a
wrong fit, a wrong crop offset or a wrong parent composition puts it in empty
air.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ambition_sprite2d_renderer.authoring.body_rig import place
from ambition_sprite2d_renderer.targets.characters._pirate_common import (
    render_target_with_products,
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


def _near_drawn_pixel(alpha, point) -> bool:
    """``point`` is in published frame pixels; ``alpha`` is the frame's."""
    x, y = int(round(point[0])), int(round(point[1]))
    return any(
        0 <= x + dx < alpha.width
        and 0 <= y + dy < alpha.height
        and alpha.getpixel((x + dx, y + dy)) > 0
        for dy in range(-_TOLERANCE_PX, _TOLERANCE_PX + 1)
        for dx in range(-_TOLERANCE_PX, _TOLERANCE_PX + 1)
    )


@pytest.mark.parametrize("kind", ["pirate_admiral", "pirate_raider"])
def test_the_rig_hands_land_on_the_published_frame(kind, tmp_path: Path):
    outputs, products = render_target_with_products(kind, tmp_path)
    product = products["body_rig"]
    assert Path(outputs["body_rig"]).read_text() == product.to_ron()
    sheet = yaml.safe_load(Path(outputs["yaml"]).read_text())
    feet = sheet["body_metrics"]["feet_pixel"]
    flipbook = products["parts"]
    misses = []
    checked = 0
    for clip, (_loop, _duration, frames) in product.clips.items():
        for index, frame in enumerate(frames):
            alpha = flipbook.recompose(clip, index).getchannel("A")
            chains = _world(product, frame)
            for name, joint, offset in product.attachments:
                if not name.startswith("hand"):
                    continue
                x, y = _place(chains[joint], offset)
                published = (x + feet["x"], y + feet["y"])
                checked += 1
                if not _near_drawn_pixel(alpha, published):
                    misses.append(f"{clip}[{index}] {name} at {published}")
    assert checked > 40
    assert not misses, "hands in empty air:\n" + "\n".join(misses)
