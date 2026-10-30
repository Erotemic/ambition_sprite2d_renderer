"""The seams of the giant gnu's cut arms are where the arms are drawn (Jon,
2026-10-24: "We need the capability to know exactly where the end points of
the arms "moving through" the portal are, so we can draw the portal lines
correctly").

A seam is the two ends of a limb's cut at its portal's line, published as
anchors of each frame (`giant_art.limb_seam_anchors`). The game draws the
line from them. Each check measures the RASTER of the frame, not the pose's
numbers: the cut that is drawn is the cut that is published.
"""
from __future__ import annotations

import math

import pytest

from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import _pieces as pc
from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import giant_art as g
from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import sprite_generator as sg

#: How far a published end may be from the drawn edge of the limb, in pixels
#: of the frame (the edge of a raster is soft by about a pixel).
TOLERANCE = 2.0
#: How deep into the kept side of the cut the drawn limb is measured, in
#: pixels of the frame. A limb that goes across its line at a slant has edges
#: that move along the line with the depth: the ends must be in what is drawn
#: over these depths.
DEPTHS = (0.5, 1.0, 1.5)


def _drawn_run(image, a, b, toward):
    """What is drawn on the line from ``a`` to ``b``, ``depth`` into the side
    of ``toward``, for each of `DEPTHS`: the first and last drawn place, in
    pixels along the line from ``a``."""
    alpha = image.getchannel("A")
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    nx, ny = -uy, ux
    mx, my = (a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5
    if (toward[0] - mx) * nx + (toward[1] - my) * ny < 0.0:
        nx, ny = -nx, -ny
    runs = []
    for depth in DEPTHS:
        def drawn(s):
            x, y = a[0] + ux * s + nx * depth, a[1] + uy * s + ny * depth
            inside = 0 <= x < image.width and 0 <= y < image.height
            return inside and alpha.getpixel((int(x), int(y))) >= 128

        middle = length * 0.5
        if not drawn(middle):
            runs.append(None)
            continue
        lo = middle
        while lo > -40.0 and drawn(lo - 0.25):
            lo -= 0.25
        hi = middle
        while hi < length + 40.0 and drawn(hi + 0.25):
            hi += 0.25
        runs.append((lo, hi + 0.25))
    return runs, length


def _assert_seam_is_drawn(image, a, b, toward, what):
    runs, length = _drawn_run(image, a, b, toward)
    runs = [run for run in runs if run]
    assert runs, f"{what}: nothing is drawn at its seam"
    starts, ends = [run[0] for run in runs], [run[1] for run in runs]
    assert min(starts) - TOLERANCE <= 0.0 <= max(starts) + TOLERANCE, f"{what}: drawn {runs}, published 0..{length:.1f}"
    assert min(ends) - TOLERANCE <= length <= max(ends) + TOLERANCE, f"{what}: drawn {runs}, published 0..{length:.1f}"


def _arm_only(pose, slot):
    """The frame of ``pose`` with only the cut arm of ``slot`` drawn."""
    name = {v: k for k, v in g.LIMB_SLOTS.items()}[slot]
    scene = g.scene_for(dict(pose, arms=[spec for spec in pose["arms"] if spec["name"] == name]))
    scene.items = [p for p in scene.items if p.name == g.limb_track(name)]
    return pc.compose(scene, g.CANVAS, g.CANVAS_ORIGIN).resize(g.FRAME)


@pytest.mark.parametrize("anim", ["clamp", "rest", "hit", "walk"])
def test_each_cut_arm_publishes_the_seam_it_is_drawn_with(anim):
    """The two ends of each arm's seam are the drawn arm's two edges at its
    line, on the giant's side of it."""
    count = dict((n, c) for n, c, _ in sg.ANIMATIONS)[anim]
    seen = 0
    for f in range(count):
        pose = g.pose_for(anim, f / count)
        for slot, (a, b) in g.limb_seams(pose).items():
            seen += 1
            _assert_seam_is_drawn(_arm_only(pose, slot), a, b, g.to_frame(g._MIDDLE), f"{anim}[{f}] {slot}")
    if anim == "clamp":
        assert seen, "the arms of the clamp go into their lines"


def test_the_clamped_fore_arm_goes_through_its_line_square():
    """In its line the fore arm is level, so the line is as wide as the arm;
    the elbow and its hair stay out of the line."""
    for spec in g._clamped_arms(1.0):
        shoulder, elbow, wrist = spec["pts"]
        elbow, wrist = g.rigid_joints(shoulder, wrist, g._side_of(shoulder, elbow, wrist))
        assert abs(elbow[1] - wrist[1]) < 0.5, f"{spec['name']}: {elbow} {wrist}"
        assert abs(elbow[0] - spec["cut"][1]) > 60.0, f"{spec['name']}: the elbow is at the line"


@pytest.mark.parametrize("anim", [name for name, _n, _ms in g.FIST_ROWS])
def test_a_lone_fist_publishes_the_seam_it_is_drawn_with(anim):
    """The two ends of a lone fist's seam are the drawn fore arm's two edges
    at its line, on the fist's side of it."""
    count = dict((n, c) for n, c, _ in g.FIST_ROWS)[anim]
    middle = (g.FIST_BBOX[0] + g.FIST_BBOX[2] * 0.5, g.FIST_BBOX[1] + g.FIST_BBOX[3] * 0.5)
    for f in range(count):
        for a, b in g.fist_seams(anim, f, count).values():
            _assert_seam_is_drawn(g.render_fist(anim, f, count), a, b, middle, f"{anim}[{f}]")


def test_the_published_sheets_carry_the_seams():
    rows = [{"animation": "clamp", "frame_count": 2, "rects": [{"x": 0}, {"x": 1}]}]
    out = sg._with_seam_anchors(rows, sg._giant_seams, sg.FRAME_SIZE)
    anchors = out[0]["rects"][1]["anchors"]
    assert set(anchors) == {"seam:hand_left:a", "seam:hand_left:b", "seam:hand_right:a", "seam:hand_right:b"}
    assert all(0.0 <= p["x"] <= 1.0 and 0.0 <= p["y"] <= 1.0 for p in anchors.values())


@pytest.mark.parametrize("anim, frame, count", [("rest", 0, 10), ("hammer_windup", 11, 12), ("jab_strike", 3, 5),
                                                ("left_hammer_strike", 3, 5), ("buck", 4, 8)])
def test_each_shoulder_surface_is_on_the_drawn_epaulet(anim, frame, count):
    """The game stands a body on the surface the sheet publishes
    (`surface:<name>:a` / `:b`): in each frame it is the top of the epaulet
    that is drawn (the band of its trim is just under it), however the torso leans or
    lifts. An arm in front of the epaulet may hide one point."""
    image = g.render_giant(anim, frame, count)

    def trim(px):
        # The gold rail or the crimson band of `giant_art.stand_trim`.
        r, _green, b, a = px
        return a >= 128 and r >= 150 and r > b + 80

    hits = []
    for name, (a, b) in sg._giant_surfaces(anim, frame, count).items():
        for u in (0.3, 0.5, 0.7):
            x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
            hits.append((name, round(x), round(y), trim(image.getpixel((int(round(x)), int(round(y + 6)))))))
    assert sum(hit for *_, hit in hits) >= len(hits) - 1, f"{anim}[{frame}]: no trim under the surface at {hits}"


def test_the_published_giant_sheet_carries_its_shoulder_surfaces():
    rows = [{"animation": "hammer_windup", "frame_count": 2, "rects": [{"x": 0}, {"x": 1}]}]
    out = sg._with_seam_anchors(rows, sg._giant_seams, sg.FRAME_SIZE, sg._giant_surfaces)
    anchors = out[0]["rects"][1]["anchors"]
    surfaces = {key for key in anchors if key.startswith("surface:")}
    assert surfaces == {f"surface:{name}:{end}" for name in ("shoulder_left", "shoulder_right") for end in "ab"}
