"""Giant spider: eight articulated leg chains and genuinely drawn turn views."""
from ambition_sprite2d_renderer.authoring.part_flipbook import build_rig_flipbook
from ambition_sprite2d_renderer.targets.characters import giant_spider as spider


def _bounds(frame):
    return frame.getchannel('A').getbbox()


def test_turnaround_views_and_anchor():
    row = next(row for row in spider.ROWS if row[0] == 'turnaround')
    assert row[1:] == (5, 44)
    frames = [spider._render_frame('turnaround', i, 5) for i in range(5)]
    assert frames[3].tobytes() == spider._quarter_frame().tobytes()
    assert frames[2].tobytes() == spider._front_frame().tobytes()
    assert frames[4].tobytes() == spider._render_side_frame('idle', 0, 12).tobytes()
    for a, b in ((0, 4), (1, 3)):
        assert frames[a].tobytes() == spider._reflect(frames[b]).tobytes()
        x0, y0, x1, y1 = _bounds(frames[a])
        u0, v0, u1, v1 = _bounds(frames[b])
        assert x0 + u1 == x1 + u0 == spider.BODY_BOX[0] + spider.BODY_BOX[2]
        assert (y0, y1) == (v0, v1)
    assert len({frame.tobytes() for frame in frames}) == 5


def test_articulated_parts_and_depth_order():
    rows = [r for r in spider.ROWS if r[0] in ('walk', 'turnaround')]
    flipbook = build_rig_flipbook(spider.TARGET_NAME, rows, spider._render_frame,
                                 None, (149.5, 169.), spider.FRAME_SIZE, (), paint=False)
    flipbook.pack()
    assert not flipbook.baked_clips
    assert flipbook.frame_count() == 21
    assert flipbook.packed_texels() < 21 * spider.FRAME_SIZE[0] * spider.FRAME_SIZE[1]
    _, walk = flipbook.clips['walk']
    for frame in walk:
        tracks = [draw.track for draw in frame]
        for side in ('far', 'near'):
            for k in range(4):
                chain = [tracks.index(f'{side}_{k}_{role}')
                         for role in ('tarsus', 'tibia', 'femur', 'coxa')]
                assert chain == list(range(chain[0], chain[0]+4))
                if side == 'far':
                    assert chain[-1] < tracks.index('abdomen')
                else:
                    assert tracks.index('carapace') < chain[0]
        assert len(frame) <= 64
    leg_draws = [d for frame in walk for d in frame if d.track and d.track.endswith('_tibia')]
    assert len({d.part for d in leg_draws}) < len(leg_draws) / 2
    assert len({d.rotation for d in leg_draws if d.track == 'near_0_tibia'}) > 2
    _, turns = flipbook.clips['turnaround']
    tracks = [d.track for d in turns[3]]
    for k in range(4):
        for role in ('tarsus', 'tibia', 'femur', 'coxa'):
            assert tracks.index(f'quarter_far_{k}_{role}') < tracks.index('quarter_abdomen')
            assert tracks.index('quarter_carapace') < tracks.index(f'quarter_near_{k}_{role}') < tracks.index('quarter_eye_plate')
    assert tracks.index('quarter_eye_plate') < tracks.index('quarter_chelicera_far') < tracks.index('quarter_chelicera_near')
    # The fixed frontal body layers may be merged by the publisher.
    front_tracks = [d.track or '' for d in turns[2]]
    assert any('front_carapace' in track.split('+') for track in front_tracks)
    for side in (-1, 1):
        for k in range(4):
            for role in ('tarsus', 'tibia', 'femur', 'coxa'):
                assert f'front_{side}_{k}_{role}' in front_tracks


def test_all_frames_fit_and_death_stays_grounded():
    for animation, count, _ in spider.ROWS:
        for i in range(count):
            frame = spider._render_frame(animation, i, count)
            x0, y0, x1, y1 = _bounds(frame)
            assert min(x0, y0, frame.width-x1, frame.height-y1) > 0, (animation, i)
            if animation.startswith('death'):
                # Account for the Lanczos antialiasing fringe.
                assert abs(y1-spider.GROUND) <= 5, (animation, i)
