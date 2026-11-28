"""The gargoyle publishes anatomical parts and uses five distinct turn views."""
from PIL import ImageChops

from ambition_sprite2d_renderer.authoring.part_flipbook import build_rig_flipbook
from ambition_sprite2d_renderer.targets.characters import gargoyle


def test_turnaround_views():
    row = next(row for row in gargoyle.ROWS if row[0] == 'turnaround')
    assert row[1:] == (5, 51)
    frames = [gargoyle._render_frame('turnaround', i, 5) for i in range(5)]
    for frame in frames:
        x0, y0, x1, y1 = frame.getchannel('A').getbbox()
        assert 0 < x0 < x1 < frame.width
        assert 0 < y0 < y1 < frame.height
    assert ImageChops.difference(frames[3], gargoyle.quarter_frame()).getbbox() is None
    assert ImageChops.difference(frames[2], gargoyle.front_frame()).getbbox() is None
    assert ImageChops.difference(frames[4], gargoyle.side_frame('idle', 0, 12)).getbbox() is None


def test_part_tracks_and_reuse():
    rows = [row for row in gargoyle.ROWS if row[0] in ('walk', 'turnaround')]
    flipbook = build_rig_flipbook(gargoyle.TARGET_NAME, rows, gargoyle._render_frame,
                                 None, (210., 261.), gargoyle.FRAME_SIZE, (), paint=False)
    flipbook.pack()
    assert not flipbook.baked_clips
    assert flipbook.frame_count() == 21
    assert flipbook.packed_texels() < 21 * gargoyle.FRAME_SIZE[0] * gargoyle.FRAME_SIZE[1]
    _, walk = flipbook.clips['walk']
    # The shoulder and shin each carry independent, rotating tracks. The
    # wing and head stay separate in front-to-back draw order.
    for frame in walk:
        tracks = [draw.track for draw in frame]
        assert 'fore_near_upper' in tracks and 'fore_near_shin' in tracks
        assert tracks.index('wing_far') < tracks.index('torso') < tracks.index('wing_near')
        assert len(frame) < 64
    assert len({draw.part for frame in walk for draw in frame}) < sum(map(len, walk))
    assert any(draw.rotation for frame in walk for draw in frame if draw.track == 'fore_near_shin')


def test_all_frames_fit_canvas():
    for animation, count, _ in gargoyle.ROWS:
        for i in range(count):
            frame = gargoyle._render_frame(animation, i, count)
            x0, y0, x1, y1 = frame.getchannel('A').getbbox()
            assert min(x0, y0, frame.width - x1, frame.height - y1) > 0, (animation, i)
            if animation.startswith('death'):
                assert abs(y1 - gargoyle.GROUND) <= 5, (animation, i)


def test_quarter_view_depth_and_parts():
    rows = [('turnaround', 5, 51)]
    flipbook = build_rig_flipbook(gargoyle.TARGET_NAME, rows, gargoyle._render_frame,
                                 None, (210., 261.), gargoyle.FRAME_SIZE, (), paint=False)
    flipbook.pack()
    assert not flipbook.baked_clips
    _, frames = flipbook.clips['turnaround']
    tracks = [draw.track for draw in frames[3]]
    assert tracks.index('quarter_wing_far') < tracks.index('quarter_torso')
    assert tracks.index('quarter_fore_far_leg') < tracks.index('quarter_torso')
    assert tracks.index('quarter_torso') < tracks.index('quarter_fore_near_leg')
    assert tracks.index('quarter_torso') < tracks.index('quarter_wing_near')
    assert tracks.index('quarter_wing_near') < tracks.index('quarter_wing_root') < tracks.index('quarter_head')
    assert tracks.index('quarter_head') < tracks.index('quarter_eyes_and_nose') < tracks.index('quarter_jaw')
    for name in ('hind_far', 'fore_far', 'hind_near', 'fore_near'):
        assert f'quarter_{name}_leg' in tracks
        assert f'quarter_{name}_paw' in tracks
