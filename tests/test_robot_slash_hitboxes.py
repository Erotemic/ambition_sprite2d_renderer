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

    # The first visible frame should already span nearly the full runtime quad.
    # Express the requirement as a fraction so it follows descriptor-derived
    # geometry instead of pinning one pixel coordinate.
    width = active.width
    assert x0 <= 4
    assert x1 >= 0.95 * width, f"the sweep stops at {x1} of {width} — under 95% of the quad"
    assert x1 - x0 >= 0.93 * width
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

    rows = {row["animation"]: row for row in manifest["rows"]}

    #  this used to freeze the whole row list, and a FOURTH row broke it.
    # `poke` was added and the durations retimed 24 -> 20; both are content
    # decisions, and neither has anything to do with what this test is named
    # for. A hand-kept list of every row is a list that rots on the next
    # authored animation, and it rotted silently — nobody looks at a suite that
    # is already red.
    #
    #  assert the LIFETIME and the RELEASE, which is the subject: every row
    # lives the same five frames at one shared duration, and the last frame of
    # every row is empty. A new animation joins for free; one that lingers,
    # runs short, or is retimed alone still fails.
    assert {"side", "up", "down"} <= set(rows), f"a cardinal swing is missing: {sorted(rows)}"
    assert {row["frame_count"] for row in rows.values()} == {5}
    assert len({row["duration_ms"] for row in rows.values()}) == 1, (
        "one swing is timed differently from its siblings: "
        f"{ {name: row['duration_ms'] for name, row in rows.items()} }"
    )

    for animation in rows:
        release = robot_slash._draw_frame(animation, 4, 5)
        assert _alpha_bbox(release) is None, f"{animation} still paints on its release frame"



def test_robot_slash_has_no_painted_origin_marker():
    active = robot_slash._draw_frame("side", 0, 5).convert("RGBA")

    # The design-space origin remains metadata only. A painted disk/triangle at
    # the pivot looked like a detached weapon tip in game and must not return.
    for y in range(88, 105):
        for x in range(0, 8):
            assert active.getpixel((x, y))[3] < 160
