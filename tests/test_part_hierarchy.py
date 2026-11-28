"""The offline hierarchy follows the runtime's rigid-transform contract."""
import math
from dataclasses import replace

from PIL import Image
import pytest

from ambition_sprite2d_renderer.authoring.part_flipbook import (
    PartDraw, PartFlipbook, PartRaster, TWEEN_LINEAR, tween_draws,
    _merge_rigid_neighbours, _share_transformed_parts,
)
from ambition_sprite2d_renderer.authoring.part_hierarchy import blend_draws, validate_hierarchy


def _fixture():
    parts = [PartRaster('a', Image.new('RGBA', (2, 2), 'red'), (1, 1)),
             PartRaster('b', Image.new('RGBA', (3, 3), 'blue'), (1, 1))]
    def pose(turn, variant=0):
        c, s = math.cos(turn), math.sin(turn)
        return [PartDraw(variant, (20*c, -20+20*s), turn, track='hand'),
                PartDraw(0, (0, -20), turn, track='root'),
                PartDraw(0, (10*c, -20+10*s), turn, track='elbow')]
    before, after = pose(0), pose(math.pi/2, 1)
    after.append(PartDraw(0, (0, -15), math.pi/2, track='watch'))
    return PartFlipbook('chain', (28, 40), (14, 35), parts,
                        {'idle': (.1, [before, after])}, tweens={'idle': TWEEN_LINEAR},
                        track_parents={'hand': 'elbow', 'elbow': 'root', 'watch': 'root'})


def test_hierarchical_tween_and_blend_keep_attachments_and_draw_order(tmp_path):
    flipbook = _fixture()
    before, after = flipbook.clips['idle'][1]
    def check(draws):
        assert [d.track for d in draws[:3]] == ['hand', 'root', 'elbow']
        assert math.dist(draws[0].at, draws[2].at) == pytest.approx(10)
        assert math.dist(draws[2].at, draws[1].at) == pytest.approx(10)
        assert draws[2].at[0] == pytest.approx(10/math.sqrt(2))
    check(tween_draws(flipbook, 'idle', 0, .5))
    assert tween_draws(flipbook, 'idle', 0, .5)[0].part == 0
    blended = blend_draws(before, after, .5, flipbook.track_parents)
    check(blended)
    assert blended[0].part == 1
    assert math.dist(blended[3].at, blended[1].at) == pytest.approx(5)
    assert tween_draws(flipbook, 'idle', 0, 0) == before
    assert blend_draws(before, after, 1, flipbook.track_parents) == after
    paths = flipbook.write(tmp_path)
    restored = PartFlipbook.from_published(paths['ron'])
    assert restored.track_parents == flipbook.track_parents
    # RON quantizes angles to 4 decimal places; no change to its semantics.
    assert math.dist(tween_draws(restored, 'idle', 0, .5)[0].at, (math.sqrt(200), -20+math.sqrt(200))) < .001


def test_invalid_hierarchy_is_refused():
    f = _fixture()
    for parents in ({'elbow': 'hand', 'hand': 'elbow'}, {'hand': 'absent'}, {'hand': 'watch'}):
        with pytest.raises(ValueError):
            validate_hierarchy(parents, f.clips)


def test_atlas_optimization_preserves_joint_identity_and_basis():
    f = _fixture()
    # Exact symmetric art can otherwise become half a sprite, or be merged
    # with the next rigid draw. These parts are coordinate frames, not just pixels.
    merged = _merge_rigid_neighbours(f)
    assert merged is f
    # A protected part can share only identical local art with the same pivot.
    turned = f.parts[0].image.transpose(Image.Transpose.ROTATE_90)
    f.parts.append(PartRaster('c', turned, (1, 1)))
    f.clips['idle'][1][1][2] = replace(f.clips['idle'][1][1][2], part=2)
    changed = _share_transformed_parts(f)
    assert changed.clips['idle'][1][1][2].at == f.clips['idle'][1][1][2].at
    assert changed.clips['idle'][1][1][2].rotation == f.clips['idle'][1][1][2].rotation
