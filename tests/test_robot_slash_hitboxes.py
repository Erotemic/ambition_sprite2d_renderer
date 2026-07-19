from __future__ import annotations

from pathlib import Path

from PIL import Image
from yaml import safe_load

from ambition_sprite2d_renderer.targets.props import robot_slash


def _alpha_bbox(image: Image.Image):
    return image.convert("RGBA").getchannel("A").getbbox()


def _coverage(image: Image.Image, threshold: int = 24) -> int:
    alpha = image.convert("RGBA").getchannel("A")
    return sum(alpha.getpixel((x, y)) > threshold for y in range(alpha.height) for x in range(alpha.width))


def test_robot_slash_first_frame_is_immediately_large_and_centered():
    active = robot_slash._draw_frame("side", 0, 5)
    bbox = _alpha_bbox(active)
    assert bbox is not None
    x0, y0, x1, y1 = bbox

    # The attack should feel responsive on the first visible frame, so the
    # broad white sweep must already span nearly the full runtime quad.
    assert x0 <= 4
    assert x1 >= 156
    assert x1 - x0 >= 150
    assert y1 - y0 >= 90

    alpha = active.getchannel("A")
    central_nonzero = 0
    central_total = 0
    for y in range(40, 121):
        for x in range(40, 121):
            central_total += 1
            central_nonzero += alpha.getpixel((x, y)) > 24
    assert central_nonzero / central_total >= 0.50


def test_robot_slash_shrinks_after_the_first_frame():
    frame0 = robot_slash._draw_frame("side", 0, 5)
    frame1 = robot_slash._draw_frame("side", 1, 5)
    frame2 = robot_slash._draw_frame("side", 2, 5)
    frame3 = robot_slash._draw_frame("side", 3, 5)

    coverage = [_coverage(frame) for frame in (frame0, frame1, frame2, frame3)]
    assert coverage[0] > coverage[1] > coverage[2] > coverage[3]



def test_robot_slash_preserves_lifetime_and_clean_release(tmp_path: Path):
    robot_slash.render(tmp_path)
    manifest = safe_load((tmp_path / "robot_slash_spritesheet.yaml").read_text())

    assert manifest["frame_width"] == 160
    assert manifest["frame_height"] == 160
    assert [(row["animation"], row["frame_count"], row["duration_ms"]) for row in manifest["rows"]] == [
        ("side", 5, 24),
        ("up", 5, 24),
        ("down", 5, 24),
    ]

    for animation in ("side", "up", "down"):
        release = robot_slash._draw_frame(animation, 4, 5)
        assert _alpha_bbox(release) is None



def test_robot_slash_has_no_painted_origin_marker():
    active = robot_slash._draw_frame("side", 0, 5).convert("RGBA")

    # The design-space origin remains metadata only. A painted disk/triangle at
    # the pivot looked like a detached weapon tip in game and must not return.
    for y in range(88, 105):
        for x in range(0, 8):
            assert active.getpixel((x, y))[3] < 160
