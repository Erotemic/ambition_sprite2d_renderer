from __future__ import annotations

from ambition_sprite2d_renderer.registry import discover_module_targets
from ambition_sprite2d_renderer.targets.characters import _snakes_on_planes_common as common


def _has_near(image, rgb, tolerance=30):
    for pixel in image.convert("RGBA").get_flattened_data():
        if pixel[3] and all(abs(pixel[i] - rgb[i]) <= tolerance for i in range(3)):
            return True
    return False


def test_plane_variant_names_are_distinct_and_registered():
    report = discover_module_targets()
    assert common.PAPER_SPEC.target_name == "snakes_on_a_paper_plane"
    assert common.CARTESIAN_SPEC.target_name == "snakes_on_a_cartesian_plane"
    assert common.PAPER_SPEC.target_name != common.CARTESIAN_SPEC.target_name
    assert common.PAPER_SPEC.target_name in report.targets
    assert common.CARTESIAN_SPEC.target_name in report.targets


def test_plane_variants_render_every_animation_with_visible_art():
    for spec in (common.PAPER_SPEC, common.CARTESIAN_SPEC):
        for animation, nframes, _duration in common.ROWS:
            for frame_idx in range(nframes):
                frame = common.render_frame(spec, animation, frame_idx, nframes)
                assert frame.size == common.FRAME_SIZE
                assert frame.getchannel("A").getbbox() is not None


def test_paper_and_cartesian_planes_have_different_visual_signatures():
    paper = common.render_frame(common.PAPER_SPEC, "idle", 0, 6)
    cartesian = common.render_frame(common.CARTESIAN_SPEC, "idle", 0, 6)
    assert paper.tobytes() != cartesian.tobytes()
    assert _has_near(paper, common.PAPER[:3])
    assert _has_near(cartesian, common.AXIS_X[:3])
    assert _has_near(cartesian, common.AXIS_Y[:3])
