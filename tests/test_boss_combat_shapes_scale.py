"""The Gradient Sentinel's combat shapes are in the pixels of the frame it bakes.

The sheet renders at ``render_scale`` 2, and the hooks get that frame's size.
They used to return 128-canvas numbers regardless, so the baked hurtbox covered
the upper-rear eighth of the drawn body and swapped sides every time the boss
turned.
"""

from ambition_sprite2d_renderer.targets.characters.boss_side import AISlopZetaGenerator


def _parts(shapes, anim):
    return [(p["x"], p["y"], p["w"], p["h"]) for p in shapes[anim]["parts"]]


def test_the_hurtbox_scales_with_the_frame():
    gen = AISlopZetaGenerator()
    small = gen.hurtbox_parts((128, 128))
    large = gen.hurtbox_parts((256, 256))
    for anim in small:
        doubled = [tuple(2 * v for v in part) for part in _parts(small, anim)]
        assert _parts(large, anim) == doubled, anim


def test_the_rest_hurtbox_is_centred_on_the_frame():
    """Centred, so a turn mirrors it onto itself instead of across the body."""
    parts = _parts(AISlopZetaGenerator().hurtbox_parts((256, 256)), "rest")
    left = min(x for x, _, _, _ in parts)
    right = max(x + w for x, _, w, _ in parts)
    assert abs((left + right) / 2 - 128) <= 4, (left, right)


def test_the_attack_shapes_scale_with_the_frame():
    gen = AISlopZetaGenerator()
    small = gen.attack_hitboxes((128, 128))
    large = gen.attack_hitboxes((256, 256))
    assert large["floor_slam"]["bbox"] == tuple(2 * v for v in small["floor_slam"]["bbox"])
    assert _parts(large, "side_sweep") == [tuple(2 * v for v in p) for p in _parts(small, "side_sweep")]
