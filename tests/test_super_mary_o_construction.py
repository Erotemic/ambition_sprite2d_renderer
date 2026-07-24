from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops

from ambition_sprite2d_renderer.registry import discover_all_targets
from ambition_sprite2d_renderer.targets.props import super_mary_o_construction as art


EXPECTED_TARGETS = {
    "super_mary_o_pipe_body",
    "super_mary_o_pipe_top",
    "super_mary_o_flag_pole_body",
    "super_mary_o_flag_pole_top",
    "super_mary_o_flag",
}


def _row(image: Image.Image, y: int) -> Image.Image:
    return image.crop((0, y, image.width, y + 1))


def test_construction_targets_are_discoverable() -> None:
    report = discover_all_targets()
    assert EXPECTED_TARGETS <= set(report.targets)


def test_pipe_body_stacks_and_top_matches_body_seam() -> None:
    body = art._pipe_body_frame("idle", 0, 1)
    top = art._pipe_top_frame("idle", 0, 1)
    assert body.size == top.size == art.PIPE_FRAME
    assert ImageChops.difference(_row(body, 0), _row(body, body.height - 1)).getbbox() is None
    assert ImageChops.difference(_row(top, top.height - 1), _row(body, 0)).getbbox() is None


def test_flag_pole_stacks_and_finial_matches_body_seam() -> None:
    body = art._pole_body_frame("idle", 0, 1)
    top = art._pole_top_frame("idle", 0, 1)
    assert body.size == top.size == art.POLE_FRAME
    assert ImageChops.difference(_row(body, 0), _row(body, body.height - 1)).getbbox() is None
    assert ImageChops.difference(_row(top, top.height - 1), _row(body, 0)).getbbox() is None


def test_flag_animation_keeps_fixed_attachment_points() -> None:
    frames = [art._flag_frame("idle", i, 4) for i in range(4)]
    assert all(frame.size == art.FLAG_FRAME for frame in frames)
    assert any(ImageChops.difference(frames[0], frame).getbbox() is not None for frame in frames[1:])
    anchors = [art._flag_meta("idle", i, 4)["anchors"] for i in range(4)]
    assert all(anchor == anchors[0] for anchor in anchors[1:])


def test_fixed_canvas_metadata_uses_construction_anchors() -> None:
    assert art._pipe_body_meta("idle", 0, 1)["construction"]["repeat_axis"] == "y"
    assert art._pole_body_meta("idle", 0, 1)["construction"]["repeat_axis"] == "y"
    assert art._flag_meta("idle", 0, 4)["construction"]["attach_to"] == "flag_pole_top.flag_mount"


def test_each_target_renders_runtime_outputs(tmp_path: Path) -> None:
    for name, spec in art.SPECS.items():
        out_dir = tmp_path / name
        outputs = art._render_spec(spec, out_dir)
        assert outputs
        assert all(path.exists() and path.stat().st_size > 0 for path in outputs)
        assert (out_dir / f"{name}_spritesheet.png").exists()
        assert (out_dir / f"{name}_spritesheet.ron").exists()
        assert (out_dir / f"{name}_actor.ron").exists()


def test_composition_preview_is_generated(tmp_path: Path) -> None:
    path = art.render_construction_preview(tmp_path / "mary_o_construction_preview.png")
    image = Image.open(path).convert("RGBA")
    assert image.size == (384, 288)
    assert image.getchannel("A").getbbox() == (0, 0, 384, 288)
