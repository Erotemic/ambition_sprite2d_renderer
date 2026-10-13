"""Structural rendering checks for the swordsmen of the Shadow Dojo: the Duelist and the Oni Leader."""

from __future__ import annotations

from test_ninja_heavy import _opaque_component_sizes

import pytest

from ambition_sprite2d_renderer.targets.characters import ninja_shadow_duelist, ninja_shadow_oni_leader

SWORDSMEN = pytest.mark.parametrize("who", [ninja_shadow_duelist, ninja_shadow_oni_leader], ids=["duelist", "oni_leader"])


@SWORDSMEN
def test_a_swordsman_of_the_dojo_is_connected_in_every_pose(monkeypatch, who) -> None:
    """No limb, head, foot, scarf, horn or held sword is a piece that floats
    by itself.

    The line of a cut and the dust of a dash are not parts of him. When the
    sword is out of his hand (the pose key ``held`` is 0) it can be a second
    piece."""
    monkeypatch.setattr(who.X, "effects", lambda ctx: [])
    failures = []
    for animation, frame_count, _frame_ms in who.ROWS:
        for frame_idx in range(frame_count):
            image = who._render_frame(animation, frame_idx, frame_count)
            held = float(who.X.full(who.X.poses[animation](frame_idx, frame_count))["held"]) >= 0.5
            significant = [size for size in _opaque_component_sizes(image) if size >= 20]
            if len(significant) not in ((1,) if held else (1, 2)):
                failures.append((animation, frame_idx, held, significant))

    assert failures == []


@SWORDSMEN
def test_a_swordsman_of_the_dojo_shows_no_skin_and_his_eyes_are_red(who) -> None:
    """The ninjas of the picture they come from show no skin, and their eyes
    are red (Jon, 2026-10-13: "the same red eyes and dark shadows"): the
    duelist's are in the dark slit of his hood, the leader's in the sockets of
    his mask."""
    def is_skin(pixel) -> bool:
        r, g, b, a = pixel
        # Skin; not the brass of his sword (its green is far over its blue), not
        # its steel, and not the light of his red scarf (it has little green).
        return a > 200 and r > 150 and r > g > b > 90 and g > 120 and g - b < 60 and r - b > 40

    def is_eye(pixel) -> bool:
        r, g, b, a = pixel
        return a > 200 and r > 215 and g < 90 and b < 90

    image = who._render_frame("idle", 0, 8).convert("RGBA")
    box = image.getbbox()
    width, height = image.size
    pixels = image.load()
    # A face or a hand is tens of pixels. A few pixels are where his brass meets a dark edge.
    assert len([(x, y) for y in range(height) for x in range(width) if is_skin(pixels[x, y])]) < 10
    # His eyes are in his head: the top quarter of him (the leader's horns are over his head).
    eye_rows = {y for y in range(int(box[1] + (box[3] - box[1]) * 0.25)) for x in range(width) if is_eye(pixels[x, y])}
    assert eye_rows
