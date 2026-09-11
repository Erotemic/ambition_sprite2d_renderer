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


def test_every_effect_shape_honours_inflate():
    """`inflate` is documented on the hitbox field, and reached two of six shapes.

    It began inside `hit_polygon`, so only the SWEPT hull grew. The `poke` arm
    was repaired first and left `reentry`, `muzzle` and `beam` still dropping
    it -- 32 specs in the tree, including every one of the officer's smash
    attacks. A knob an author reads about and does not receive is worse than one
    that does not exist.

    ⚠ This walks the EFFECT NAMES, so a shape added tomorrow cannot be the fifth
    to miss it without failing here.
    """
    from ambition_sprite2d_renderer.authoring import swing_effects as se

    # ⚠ TWO FRAMES, because a SWEPT hull is built from where the blade has BEEN.
    # One axis gives two points and `hit_polygon` needs three, so `trail` and
    # `wind` returned `None` and the assertion below read that as a failure to
    # grow rather than a fixture that never reached them.
    axes = [((0.0, 0.0), (20.0, 0.0)), ((0.0, 0.0), (18.0, 8.0))]
    poke = {"extend": 1.0, "width": 10.0, "waist": 0.5, "inner": 0.0}
    # ⚠ `spread` IS A LIST FOR A MUZZLE AND A FLOAT FOR A RE-ENTRY CONE. One
    # shared fixture crashed the cone rather than measuring it.
    shots = {
        "muzzle": {"reach": 2.0, "flare": 0.55, "spread": [0.0]},
        "beam": {"reach": 4.0, "width": 0.4},
        "reentry": {"spread": 1.15, "extend": 1.12, "trail": 1.05},
    }

    def area(effect, inflate):
        poly = se.volume_polygon(
            axes, 1, effect, 0, {"inflate": inflate, "extend": 1.0}, poke,
            shots.get(effect, {}),
        )
        assert poly, f"the premise: {effect} produced a polygon at all"
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        return (max(xs) - min(xs)) * (max(ys) - min(ys))

    for effect in ("poke", "muzzle", "beam", "reentry", "trail", "wind"):
        bare = area(effect, 0.0)
        grown = area(effect, 6.0)
        assert grown > bare * 1.2, (
            f"{effect} ignored inflate: {bare:.1f} -> {grown:.1f}"
        )
