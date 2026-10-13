"""Structural rendering checks for the Shadow Duelist."""

from __future__ import annotations

from test_ninja_heavy import _opaque_component_sizes

from ambition_sprite2d_renderer.targets.characters import ninja_shadow_duelist as duelist


def test_shadow_duelist_body_is_connected_in_every_pose(monkeypatch) -> None:
    """No limb, head, foot, scarf or held sword is a piece that floats by
    itself.

    The line of his cut and the dust of his dash are not parts of him. When
    the sword is out of his hand (the pose key ``held`` is 0) it can be a
    second piece."""
    monkeypatch.setattr(duelist.X, "effects", lambda ctx: [])
    failures = []
    for animation, frame_count, _frame_ms in duelist.ROWS:
        for frame_idx in range(frame_count):
            image = duelist._render_frame(animation, frame_idx, frame_count)
            held = float(duelist.X.full(duelist.X.poses[animation](frame_idx, frame_count))["held"]) >= 0.5
            significant = [size for size in _opaque_component_sizes(image) if size >= 20]
            if len(significant) not in ((1,) if held else (1, 2)):
                failures.append((animation, frame_idx, held, significant))

    assert failures == []


def test_shadow_duelist_shows_no_skin_and_his_eyes_are_red() -> None:
    """He is grey from his head to his feet, and his eyes are red lights in
    the dark slit of his hood (Jon, 2026-10-13: "the same red eyes and dark
    shadows")."""
    def is_skin(pixel) -> bool:
        r, g, b, a = pixel
        # Skin; not the brass of his sword (its green is far over its blue), not
        # its steel, and not the light of his red scarf (it has little green).
        return a > 200 and r > 150 and r > g > b > 90 and g > 120 and g - b < 60 and r - b > 40

    def is_eye(pixel) -> bool:
        r, g, b, a = pixel
        return a > 200 and r > 215 and g < 90 and b < 90

    image = duelist._render_frame("idle", 0, 8).convert("RGBA")
    box = image.getbbox()
    width, height = image.size
    pixels = image.load()
    assert not [(x, y) for y in range(height) for x in range(width) if is_skin(pixels[x, y])]
    # His eyes are in his head: the top fifth of him.
    eye_rows = {y for y in range(int(box[1] + (box[3] - box[1]) * 0.2)) for x in range(width) if is_eye(pixels[x, y])}
    assert eye_rows
