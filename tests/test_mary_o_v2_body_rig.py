"""Mary-O's body rig describes the frames the sheet draws.

The rig is solved from the same SVG rig and pose table as the sheet, so a
gameplay attachment must land on drawn art in the frame the sheet publishes for
that row and index. A rig that drifts from the art (a wrong origin, a wrong
scale, a wrong sign on a rotation) puts a hand in empty air, and this test
names the row, the frame and the attachment where it happens.

The feet are published too, but no gameplay consumer reads them yet, and a foot
is only as good as its authored toe marker: the Fire side view's ``far_toe``
marker sits 40.7 degrees off its leg, where the art is at about 17. The hands
and the head are what a projectile or a hurt volume reads, so they are what
this test holds to the drawing.
"""

from __future__ import annotations

import pytest

from ambition_sprite2d_renderer.authoring.body_rig import place
from ambition_sprite2d_renderer.targets.characters import mary_o_v2_svg_poc as svg_rig
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_body_rig import body_rig_for_form
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_model import (
    FIRE_FORM,
    SHORT_FORM,
    TALL_FORM,
    form_collision_box,
)
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_svg_poc import build_rig_document

#: How far an attachment may sit from the nearest drawn pixel. A hand tip is
#: the END of the glove, so it sits on the art's edge.
_TOLERANCE_PX = 3
#: The attachments a gameplay consumer reads. See the module docstring.
_GAMEPLAY_ATTACHMENTS = ("hand_near", "hand_far", "head")


@pytest.fixture(scope="module")
def docs():
    out = {}
    for source in (SHORT_FORM, TALL_FORM, FIRE_FORM):
        out[source.target_name] = build_rig_document(svg_rig.ASSET_PATH, source, "side")
        out[f"{source.target_name}:front"] = build_rig_document(svg_rig.ASSET_PATH, source, "front")
    return out


def _near_drawn_pixel(alpha, point) -> bool:
    x, y = int(round(point[0])), int(round(point[1]))
    for dy in range(-_TOLERANCE_PX, _TOLERANCE_PX + 1):
        for dx in range(-_TOLERANCE_PX, _TOLERANCE_PX + 1):
            px, py = x + dx, y + dy
            if 0 <= px < alpha.width and 0 <= py < alpha.height and alpha.getpixel((px, py)) > 0:
                return True
    return False


@pytest.mark.parametrize("form", [SHORT_FORM, TALL_FORM, FIRE_FORM], ids=lambda f: f.target_name)
def test_every_attachment_lands_on_the_drawn_frame(form, docs):
    product = body_rig_for_form(svg_rig.ASSET_PATH, form)
    product.validate()
    rows = {name: int(frames) for name, frames, _duration in form.rows}
    box = form_collision_box(form)
    feet = (box["x"] + box["w"] / 2.0, float(box["y"] + box["h"]))
    names = [name for name, _parent in product.joints]
    assert {"hand_near", "hand_far", "foot_near", "foot_far", "head"} <= {
        name for name, _joint, _offset in product.attachments
    }
    misses = []
    for clip, (_looping, _duration, frames) in product.clips.items():
        assert len(frames) == rows[clip], f"{clip}: rig frames differ from the sheet row"
        for index, frame in enumerate(frames):
            alpha = svg_rig._draw_poc_form(form, docs, clip, index, len(frames)).getchannel("A")
            poses = dict(zip(names, frame))
            for name, joint, offset in product.attachments:
                if name not in _GAMEPLAY_ATTACHMENTS:
                    continue
                x, y = place(poses[joint], offset)
                point = (x + feet[0], y + feet[1])
                if not _near_drawn_pixel(alpha, point):
                    misses.append(f"{clip}[{index}] {name} at {point}")
    assert not misses, "attachments in empty air:\n" + "\n".join(misses)


def test_the_rig_does_not_publish_front_or_transition_rows():
    product = body_rig_for_form(svg_rig.ASSET_PATH, TALL_FORM)
    assert "death" not in product.clips
    assert "grow" not in product.clips
    assert "shrink" not in product.clips
    assert "crouch" in product.clips
