"""Rats use reusable parts and explicitly authored yaw projections."""

import pytest

from ambition_sprite2d_renderer.authoring.part_flipbook import build_rig_flipbook
from ambition_sprite2d_renderer.targets.characters import giant_rat, plague_rat


@pytest.mark.parametrize('rat,ms', [(giant_rat,44),(plague_rat,54)])
def test_turnaround_views_and_body_anchor(rat,ms):
    assert next(row for row in rat.ROWS if row[0]=='turnaround') == ('turnaround',5,ms)
    frames=[rat._render_frame('turnaround',i,5) for i in range(5)]
    assert len({im.tobytes() for im in frames})==5
    assert frames[2].tobytes()==rat._front_frame().tobytes()
    assert frames[3].tobytes()==rat._quarter_frame().tobytes()
    assert frames[4].tobytes()==rat._render_side_frame('idle',0,16).tobytes()
    for a,b in ((0,4),(1,3)):
        assert frames[a].tobytes()==rat._reflect(frames[b]).tobytes()
        x0,y0,x1,y1=frames[a].getchannel('A').getbbox()
        u0,v0,u1,v1=frames[b].getchannel('A').getbbox()
        assert x0+u1==x1+u0==rat.BODY_BOX[0]+rat.BODY_BOX[2]
        assert (y0,y1)==(v0,v1)


@pytest.mark.parametrize('rat',[giant_rat,plague_rat])
def test_reusable_bones_and_painter_order(rat):
    rows=[r for r in rat.ROWS if r[0] in ('walk','turnaround')]
    x0,_,x1,y1=rat.BODY_BOX
    flipbook=build_rig_flipbook(rat.TARGET_NAME,rows,rat._render_frame,None,
                               ((x0+x1-1)/2,y1-1),rat.FRAME_SIZE,(),paint=False)
    flipbook.pack()
    assert not flipbook.baked_clips
    assert flipbook.frame_count()==21
    assert flipbook.packed_texels()<21*rat.FRAME_SIZE[0]*rat.FRAME_SIZE[1]
    def index(frame,name):
        return next(i for i,d in enumerate(frame) if name in (d.track or '').split('+'))
    _,walk=flipbook.clips['walk']
    for frame in walk:
        for near in ('far','near'):
            for limb in ('hind','fore'):
                chain=[index(frame,f'{near}_{limb}_{part}') for part in ('paw','wrist','lower','upper')]
                assert chain==sorted(chain)
                if near=='far':
                    assert chain[-1]<index(frame,'torso')
                else:
                    assert index(frame,'torso')<chain[0]<index(frame,'skull')
        assert index(frame,'tail')<index(frame,'torso')
        assert index(frame,'far_ear')<=index(frame,'skull')<=index(frame,'near_ear')<=index(frame,'face')
    lower=[d for frame in walk for d in frame if (d.track or '').endswith('_lower')]
    assert len({d.part for d in lower})<len(lower)/2
    assert len({d.rotation for d in lower if d.track=='near_fore_lower'})>2
    _,turn=flipbook.clips['turnaround']
    quarter=turn[3]
    for side in ('far','near'):
        for limb in ('hind','fore'):
            chain=[index(quarter,f'quarter_{side}_{limb}_{part}') for part in ('paw','wrist','lower','upper')]
            assert chain==sorted(chain)
            if side=='far':
                assert chain[-1]<index(quarter,'quarter_torso')
            else:
                assert index(quarter,'quarter_torso')<chain[0]<index(quarter,'quarter_skull')
    assert index(quarter,'quarter_far_ear')<=index(quarter,'quarter_skull')<=index(quarter,'quarter_near_ear')<=index(quarter,'quarter_face')


@pytest.mark.parametrize('rat',[giant_rat,plague_rat])
def test_all_frames_fit_and_death_is_grounded(rat):
    for animation,count,_ in rat.ROWS:
        for i in range(count):
            frame=rat._render_frame(animation,i,count)
            x0,y0,x1,y1=frame.getchannel('A').getbbox()
            assert min(x0,y0,frame.width-x1,frame.height-y1)>0,(animation,i)
            if animation.startswith('death'):
                assert abs(y1-rat.GROUND)<=5,(animation,i)
