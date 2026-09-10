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
