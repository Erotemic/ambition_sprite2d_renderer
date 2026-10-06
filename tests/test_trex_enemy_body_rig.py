"""The T-rex's body rig states where his jaws hold a body.

The game holds a seized body at the ``jaw`` attachment of this rig and keeps no
pixel of its own for it. So the point must be on his mouth in every frame of
the rows that hold a body: on the length of his drawn lower jaw, on its teeth
side, and near drawn art.
"""

from __future__ import annotations

import pytest

from ambition_sprite2d_renderer.authoring.body_rig import place
from ambition_sprite2d_renderer.targets.characters import trex_enemy
from ambition_sprite2d_renderer.targets.characters._trex_enemy_body_rig import (
    ATTACHMENTS,
    _joint_extent,
    body_rig,
)

#: The rows in which he holds a body in his jaws.
_HOLD_ROWS = ("grab_reach", "grab_shake", "grab_throw")
#: How far the point may sit from the nearest drawn pixel of the frame.
_TOLERANCE_PX = 4


@pytest.fixture(scope="module")
def doc():
    return trex_enemy._doc()


def test_the_jaw_attachment_is_on_the_teeth_side_of_his_drawn_jaw(doc):
    names = {name: (joint, offset) for name, joint, offset in ATTACHMENTS}
    assert "jaw" in names, "the rig states no `jaw` attachment; his grab has nowhere to hold a body"
    joint, (x, y) = names["jaw"]
    assert joint == "jaw"
    parts = {str(part["name"]): part for part in doc.parts}
    x0, y0, x1, y1 = _joint_extent(doc, parts["jaw"])
    assert x0 <= x <= x1, f"the jaw point is at {x} along the jaw; his drawn jaw runs {x0:.1f} to {x1:.1f}"
    assert y < (y0 + y1) / 2.0, f"the jaw point is on the chin side of the jaw's middle line ({y} vs {(y0 + y1) / 2.0:.1f})"


def test_the_jaw_attachment_lands_on_his_drawn_mouth_in_every_hold_frame(doc):
    rows = {name: int(frames) for name, frames, _duration in trex_enemy.ROWS}
    # The rig in the DRAWN frame, feet at the origin: the same solve the
    # frames below are drawn from, with no publish transform between them.
    product = body_rig(doc, trex_enemy.TARGET_NAME, trex_enemy.ROWS, {}, (0.0, 0.0))
    product.validate()
    joints = [name for name, _parent in product.joints]
    (_name, joint, offset), = [a for a in product.attachments if a[0] == "jaw"]
    misses = []
    for row in _HOLD_ROWS:
        _looping, _duration, frames = product.clips[row]
        assert len(frames) == rows[row], f"{row}: rig frames differ from the sheet row"
        for index, frame in enumerate(frames):
            alpha = trex_enemy.render_frame(row, index, rows[row]).getchannel("A")
            px, py = place(dict(zip(joints, frame))[joint], offset)
            near = any(
                0 <= int(round(px)) + dx < alpha.width
                and 0 <= int(round(py)) + dy < alpha.height
                and alpha.getpixel((int(round(px)) + dx, int(round(py)) + dy)) > 0
                for dy in range(-_TOLERANCE_PX, _TOLERANCE_PX + 1)
                for dx in range(-_TOLERANCE_PX, _TOLERANCE_PX + 1)
            )
            if not near:
                misses.append(f"{row}[{index}] jaw at ({px:.1f}, {py:.1f})")
    assert not misses, "the jaw point is in empty air:\n" + "\n".join(misses)
