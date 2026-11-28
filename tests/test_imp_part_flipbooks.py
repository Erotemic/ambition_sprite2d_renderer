"""The imp family publishes articulated tracks, not flattened yaw images."""
import pytest
from ambition_sprite2d_renderer.authoring.part_flipbook import build_rig_flipbook
from ambition_sprite2d_renderer.targets.characters import imp, greater_imp
from ambition_sprite2d_renderer.targets.characters._imp_parts import TRACK_PARENTS, reflect


@pytest.mark.parametrize('m',[imp,greater_imp])
def test_turnaround_uses_authored_views(m):
    n=next(n for name,n,_ in m.ROWS if name=='turnaround')
    assert n==5
    frames=[m._render_frame('turnaround',i,n) for i in range(n)]
    assert len({f.tobytes() for f in frames})==5
    assert frames[0].tobytes()==reflect(frames[-1],m.BODY_BOX).tobytes()
    assert frames[1].tobytes()==reflect(frames[3],m.BODY_BOX).tobytes()
    assert frames[2].tobytes()==m._view_frame(False).tobytes()
    assert frames[3].tobytes()==m._view_frame(True).tobytes()
    for frame in frames:
        x,y,r,b=frame.getchannel('A').getbbox()
        assert min(x,y,frame.width-r,frame.height-b)>0


@pytest.mark.parametrize('m',[imp,greater_imp])
def test_articulated_tracks_and_depth(m):
    rows=[('fly',4,50),('turnaround',5,44)]
    x0,_,x1,y1=m.BODY_BOX
    book=build_rig_flipbook(m.TARGET_NAME,rows,m._render_frame,None,
                           ((x0+x1-1)/2,y1-1),m.FRAME_SIZE,(),paint=False,
                           track_parents=TRACK_PARENTS)
    assert not book.baked_clips
    assert book.track_parents['near_arm_hand']=='near_arm_lower'
    def index(frame,name):
        return next(i for i,d in enumerate(frame) if name in (d.track or '').split('+'))
    _,fly=book.clips['fly']
    for f in fly:
        assert index(f,'far_wing')<index(f,'far_arm_upper')<index(f,'torso')
        assert index(f,'torso')<index(f,'near_arm_upper')<index(f,'head')
        assert index(f,'head')<index(f,'face')
        assert index(f,'near_arm_hand')<index(f,'near_arm_lower')<index(f,'near_arm_upper')
    assert len({d.rotation for f in fly for d in f if d.track=='near_arm_lower'})>1
    assert len({d.part for f in fly for d in f if d.track=='near_arm_lower'})==1
    _,turn=book.clips['turnaround']
    q=turn[3]
    far_wing=index(q,'quarter_far_wing')
    near_wing=index(q,'quarter_near_wing')
    assert far_wing<near_wing<index(q,'quarter_torso')
    assert q[far_wing].part != q[near_wing].part
    assert index(q,'quarter_far_arm_upper')<index(q,'quarter_torso')<index(q,'quarter_near_arm_upper')
    assert index(q,'quarter_head')<index(q,'quarter_face')
