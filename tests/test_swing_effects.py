"""A conjured blade has an edge before it has any swept history."""
from PIL import Image

from ambition_sprite2d_renderer.authoring.swing_effects import authored_hit_frames, draw_trail


def test_conjured_blade_and_hit_shape_start_together_and_follow_the_sweep():
    frames = [Image.new('RGBA', (64, 64)) for _ in range(4)]
    axes = [((32, 32), (52, 32)), ((32, 32), (52, 32)),
            ((32, 32), (32, 12)), ((32, 32), (12, 32))]
    spec = {'effect': 'trail', 'hitbox': {'active': [1, 2], 'inflate': 2},
            'trail': {'blade_width': 4, 'inner': 0, 'window': 1}}
    images = draw_trail(frames, axes=axes, active=[1, 2], blade_width=4)
    shapes = authored_hit_frames(frames, spec, axes)
    assert images[0].getbbox() is None
    assert images[1].getpixel((42, 32))[3] > 0
    assert shapes[0]['poly'] == shapes[3]['poly'] == []
    assert len(shapes[1]['poly']) >= 3
    assert min(y for _, y in shapes[1]['poly']) > 20
    assert min(y for _, y in shapes[2]['poly']) <= 12
    assert min(x for x, _ in shapes[2]['poly']) > 20


def test_a_poke_hitbox_honours_inflate():
    """`hitbox.inflate` was a silent no-op for every thrust in the game.

    `volume_polygon` routes a `poke` to `poke_polygon`, which never received the
    value, so a spec asking for a more generous volume than its art got exactly
    its art. MEASURED 2026-09-11: the performer's forward smash drew a 15 px
    beam and carried a hitbox 5.6 px TALL. It asked for `inflate: 3.0`.

    The two performer pokes are the only ones in the tree that set it, so this
    is the arm that says whether the knob is connected at all.
    """
    from ambition_sprite2d_renderer.authoring import swing_effects as se

    axes = [((0.0, 0.0), (20.0, 0.0))]
    poke = {"extend": 1.0, "width": 10.0, "waist": 0.5, "inner": 0.0}

    def span(inflate):
        poly = se.volume_polygon(axes, 0, "poke", 0, {"inflate": inflate}, poke, {})
        assert poly, "the premise: the thrust produced a polygon at all"
        ys = [p[1] for p in poly]
        xs = [p[0] for p in poly]
        return max(xs) - min(xs), max(ys) - min(ys)

    bare_w, bare_h = span(0.0)
    grown_w, grown_h = span(6.0)
    assert grown_h > bare_h + 6.0, (
        f"inflate did not reach the thrust: {bare_h} -> {grown_h}"
    )
    assert grown_w > bare_w, f"inflate grew height but not width: {bare_w} -> {grown_w}"
