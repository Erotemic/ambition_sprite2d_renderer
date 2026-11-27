"""Barrow archer. Use the revised Barrow Skeleton's anatomy and pose rig.

The bow and its string use the solved wrist positions. The shot row shows
only the release and follow-through; the engine draws the moving arrow.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from pathlib import Path

from PIL import Image

from . import barrow_skeleton as skeleton
from . import _humanoid_bone_art as bones
from ._clockwork_enemy_art import Canvas, add, bezier, mix, mul, phase, rot, sub, track, unit
from ...authoring.sheet_build import build_sheet

TARGET_NAME = 'barrow_skeleton_archer'
DISPLAY_NAME = 'Barrow Skeleton Archer'
FRAME_SIZE = skeleton.FRAME_SIZE
CX, GROUND = skeleton.CX, skeleton.GROUND
# The ranged volley has a 0.60 s warning and a 0.18 s firing pose.
ROWS = [
    ('idle', 8, 150), ('walk', 12, 105), ('run', 12, 85),
    ('notice', 6, 95), ('aim', 10, 60), ('windup', 10, 60),
    ('shoot', 6, 30), ('attack_side', 11, 30), ('hit', 6, 90),
    ('death', 12, 95), ('death_idle', 6, 220),
]
LOOPS = {'idle', 'walk', 'run', 'death_idle'}
TRAITS = ['enemy', 'undead', 'skeleton', 'barrow', 'ranged', 'archer', 'fantasy']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': DISPLAY_NAME},
    'body': {'body_plan': 'Biped', 'body_kind': 'Standard',
             'mass_class': 'Medium', 'locomotion_hint': 'Walk', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'brain': {'default_preset': 'skirmisher'},
    'actions': {'default_preset': 'barrow_skeleton_archer_shot'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'action.ranged.primary': {'animation': 'shoot', 'events': [
            {'t': 0., 'event': 'projectile_release', 'source': 'barrow_skeleton_archer.arrow'}]},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': .25/.33, 'event': 'hitbox_active_start', 'source': 'barrow_skeleton_archer.bow_swat'},
            {'t': 1., 'event': 'hitbox_active_end', 'source': 'barrow_skeleton_archer.bow_swat'}]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': 'The same open-ribbed burial skeleton as the swordsman, with a weathered recurve bow, a leather quiver, and a green corpse-light.',
    'gameplay_description': 'It holds its ground while drawing the bow, fires an arrow, and uses the bow as a close-range weapon.',
}
INK = skeleton.INK
WOOD, WOOD_L, WOOD_D = '#94704a', '#c4a476', '#574332'
LEATHER, LEATHER_L, LEATHER_D = '#6e5846', '#a58b63', '#493d34'
STRING, FEATHER, IRON = '#ded7ba', '#c8c5ad', '#959b9b'


@dataclass(frozen=True)
class ArcherPose:
    body: skeleton.Pose
    angle: float = -38.
    draw: float = 0.
    nocked: bool = False
    contact: bool = False


REST = ArcherPose(replace(skeleton.IDLE, near_hand=(CX+19, GROUND-68),
                          far_hand=(CX-14, GROUND-66)))
AIM_START = ArcherPose(replace(REST.body, hip=(CX-2, GROUND-52), lean=1.,
                              head=-4., near_hand=(CX+38, GROUND-100),
                              far_hand=(CX+15, GROUND-105), jaw=1.4,
                              near_foot=(CX+15,GROUND-4), far_foot=(CX-15,GROUND-4)),
                       angle=0., nocked=True, contact=True)
AIM_FULL = replace(AIM_START, draw=1., body=replace(AIM_START.body, lean=-4., head=-3.,
                           near_hand=(CX+44, GROUND-98)))
RELEASE = replace(AIM_FULL, draw=0., nocked=False, contact=False,
                  body=replace(AIM_FULL.body, far_hand=(CX-6,GROUND-105), jaw=2.))
FOLLOW = replace(RELEASE, angle=5., body=replace(RELEASE.body,
                 near_hand=(CX+34,GROUND-93), far_hand=(CX-10,GROUND-99), head=0.))
SWAT_READY = ArcherPose(replace(REST.body, hip=(CX-3,GROUND-50), lean=-10.,
                        near_hand=(CX-4,GROUND-100), far_hand=(CX+15,GROUND-72), head=-12.), angle=-123.)
SWAT = ArcherPose(replace(REST.body, hip=(CX+6,GROUND-49), lean=18.,
                  near_hand=(CX+41,GROUND-76), far_hand=(CX-13,GROUND-67),
                  near_foot=(CX+21,GROUND-4), far_foot=(CX-15,GROUND-4), head=7., jaw=3.), angle=74.)


def _blend(a, b, t):
    return ArcherPose(skeleton._blend(a.body, b.body, t),
                      a.angle+(b.angle-a.angle)*t, a.draw+(b.draw-a.draw)*t,
                      a.nocked if t<.5 else b.nocked, a.contact if t<.5 else b.contact)


def _keys(t, keys):
    for (lo, a), (hi, b) in zip(keys, keys[1:]):
        if t <= hi:
            return _blend(a, b, track(t, [(lo,0.),(hi,1.)]))
    return keys[-1][1]


def pose(anim, i, n):
    t=phase(i,n,anim in LOOPS)
    s=math.sin(math.tau*t)
    if anim in ('idle','walk','run'):
        # Use the swordsman's ground-contact gait, with a steadier bow arm.
        p=skeleton.pose(anim,i,n)
        return replace(REST, body=replace(p, near_hand=(CX+19-3*s,GROUND-68),
                       far_hand=p.far_hand), angle=-38+5*s)
    if anim == 'notice':
        return _keys(t, [(0.,REST),(.7,replace(REST,angle=-20.,body=replace(REST.body,head=-12.,jaw=2.))),(1.,REST)])
    if anim in ('aim','windup'):
        return _keys(t, [(0.,REST),(.30,AIM_START),(.76,AIM_FULL),(1.,AIM_FULL)])
    if anim == 'shoot':
        # The projectile already exists at the beginning of this row.
        return _keys(t, [(0.,RELEASE),(.35,FOLLOW),(1.,replace(REST,angle=-25.))])
    if anim == 'attack_side':
        return _keys(t, [(0.,REST),(.65,SWAT_READY),(.72,SWAT_READY),(.82,SWAT),(1.,SWAT)])
    if anim == 'hit':
        p=skeleton.pose(anim,i,n)
        return replace(REST,body=p,angle=-38+20*math.sin(math.pi*t))
    if anim in ('death','death_idle'):
        return replace(REST,body=replace(REST.body,eye=False))
    raise ValueError(anim)


def _bow_point(grip, angle, x, y):
    return add(grip,rot((x,y),angle))


def _nock(grip, angle, draw):
    return _bow_point(grip,angle,-13.-24.*draw,-5.)


def solve(p):
    """Supply equipment goals to the common skeletal pose adapter.

    The grip is attached to the actual near wrist, not its requested target.
    The string contact uses the same solver and limb dimensions as every
    other arm pose. No second IK pass or character-local IK implementation.
    """
    def grip_at(wrist):
        return _bow_point(wrist,p.angle,4.,0.)
    def string_goal(wrist):
        nock=_nock(grip_at(wrist),p.angle,p.draw)
        return _bow_point(nock,p.angle,-5.,0.)
    j=skeleton._solve(p.body, far_hand_goal=string_goal if p.contact else None,
                      far_bend=1. if p.contact else -1.)
    grip=grip_at(j['near_arm'][-1])
    return j,grip,_nock(grip,p.angle,p.draw)


def _arrow(c,nock,angle,length=47.):
    def q(x,y): return _bow_point(nock,angle,x,y)
    c.line([q(0,0),q(length,0)],INK,2.5)
    c.line([q(0,0),q(length,0)],WOOD_L,1.25)
    c.poly([q(length-3,-3.2),q(length+4,0),q(length-3,3.2),q(length-1,0)],IRON,INK,.8)
    for side in (-1,1):
        c.poly([q(1,0),q(1,side*3.4),q(9,side*3.),q(12,0)],FEATHER,INK,.55)


def _bow(c,grip,angle,draw,nocked,nock=None):
    def q(x,y): return _bow_point(grip,angle,x,y)
    # Recurve tips move toward the archer as the bow bends.
    end=-13.-5.*draw
    top,bot=q(end,-25+1.8*draw),q(end,25-1.8*draw)
    upper=bezier(q(0,0),q(5,-10),q(-22-5*draw,-16),top,n=16)
    lower=bezier(q(0,0),q(5,10),q(-22-5*draw,16),bot,n=16)
    for pts in (upper,lower):
        c.line(pts,INK,5.1); c.line(pts,WOOD,3.5)
        c.line(pts[2:-2],WOOD_L,1.1)
    nock=_nock(grip,angle,draw) if nock is None else nock
    c.line([top,nock,bot],INK,1.8); c.line([top,nock,bot],STRING,.95)
    c.line([q(0,-5),q(0,5)],INK,6.1); c.line([q(0,-5),q(0,5)],LEATHER,4.2)
    for y in (-3.5,-.5,2.5): c.line([q(-2,y),q(2,y+1)],LEATHER_L,.8)
    for end_y in (-25+1.8*draw,25-1.8*draw):
        c.disk(q(end,end_y),1.8,WOOD_D,INK,.7)
    if nocked: _arrow(c,nock,angle)


def _quiver(c,pelvis,neck):
    # Keep the quiver outside the rib silhouette and attached to the trunk.
    up=unit(sub(neck,pelvis)); right=(-up[1],up[0])
    def q(x,y): return add(pelvis,add(mul(right,x),mul(up,y)))
    # The top is farther back than the base, so the arrows clear the skull.
    c.poly([q(-25,38),q(-14,39),q(-8,10),q(-16,6),q(-21,12)],LEATHER,INK,1.3)
    c.poly([q(-25,38),q(-21,37),q(-16,11),q(-16,6),q(-21,12)],LEATHER_D,None)
    c.line([q(-14,37),q(-9,12)],LEATHER_L,1.2)
    for off in (0.,3.5,7.):
        tail=q(-25+off,51+off*.5); base=q(-21+off,28)
        c.line([tail,base],INK,2.2); c.line([tail,base],WOOD_L,1.2)
        c.poly([q(-25+off,51+off*.5),q(-29+off,53+off*.5),q(-27+off,45),q(-24+off,44)],FEATHER,INK,.65)
    c.line([q(-25,38),q(-14,39)],INK,3.6); c.line([q(-25,38),q(-14,39)],LEATHER_L,2.)
    c.line([q(-21,12),q(-10,13)],INK,2.7); c.line([q(-21,12),q(-10,13)],LEATHER_L,1.5)


def render_pose(p, *, bones_only=False, palette=bones.IVORY, death=None):
    j,grip,nock=solve(p)
    body=p.body
    angle=p.angle
    release=0.
    if death is not None:
        body,j=skeleton._death(body,j,death)
        release=track(death,[(0.,0.),(.3,0.),(.85,1.),(1.,1.)])
        angle=angle+(90.-angle)*release
        grip=mix(_bow_point(j['near_arm'][-1],angle,4.,0.),(CX+49,GROUND-7.),release)
        nock=_nock(grip,angle,0.)
    c=Canvas(FRAME_SIZE)
    if not bones_only: _quiver(c,j['pelvis'],j['neck'])
    bones.leg(c,j['far_leg'],palette,True,foot_angle=body.far_toe)
    # The far hand is painted last while drawing, so it remains visible at the string.
    sh,el,wr=j['far_arm']
    bones.long_bone(c,sh,el,2.6,palette,True)
    bones.paired_bones(c,el,wr,2.35,palette,True)
    if not p.contact:
        bones.hand(c,wr,75. if p.nocked is False else angle,palette=palette,far=True)
    bones.trunk(c,j['pelvis'],j['neck'],palette)
    if not bones_only: skeleton._cloth(c,j['pelvis'],body.lean,body.rag)
    bones.leg(c,j['near_leg'],palette,foot_angle=body.near_toe)
    bones.skull(c,j['head'],body.head,1.,body.jaw,palette,
                skeleton.EYE if body.eye and not bones_only else None)
    sh,el,wr=j['near_arm']
    bones.long_bone(c,sh,el,2.6,palette)
    bones.paired_bones(c,el,wr,2.35,palette)
    if not bones_only: _bow(c,grip,angle,p.draw,p.nocked,nock)
    bones.hand(c,wr,angle,palette=palette,grip=not bones_only and release<.5)
    if p.contact:
        bones.hand(c,j['far_arm'][-1],angle,palette=palette,far=True,grip=not bones_only)
    im=c.finish()
    if death is not None:
        bb=im.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox()
        excess=max(0,bb[3]-int(GROUND+1))
        if excess:
            shifted=Image.new('RGBA',FRAME_SIZE); shifted.paste(im,(0,-excess)); im=shifted
    return im


def _render_frame(anim,i,n):
    p=pose(anim,i,n)
    death=phase(i,n,False) if anim=='death' else 1. if anim=='death_idle' else None
    return render_pose(p,death=death)


def render(out_dir: str | Path, **opts):
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,
                        out_dir=out_dir,frame_size=FRAME_SIZE,auto_crop=False,
                        actor_metadata=ACTOR_METADATA,body_metrics_fn=skeleton._body_metrics,
                        animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
