"""Barrow Skeleton: a light melee undead built from explicit bone parts.

The skeleton uses shared bone painters. The pose, sword, and burial
cloth belong to this character.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from PIL import Image

from ._clockwork_enemy_art import Canvas, add, mix, mul, phase, rot, sub, track, unit, perp
from . import _humanoid_bone_art as bones
from ...authoring.skeleton import two_bone_ik_points
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'barrow_skeleton'
DISPLAY_NAME = 'Barrow Skeleton'
FRAME_SIZE = (240, 180)
GROUND = 154.0
ROWS = [
    ('idle', 8, 150), ('walk', 12, 105), ('run', 12, 85),
    ('notice', 6, 95), ('windup', 8, 48), ('attack_side', 14, 49),
    ('hit', 6, 90), ('death', 12, 95), ('death_idle', 6, 220),
]
LOOPS = {'idle', 'walk', 'run', 'death_idle'}
TRAITS = ['enemy', 'undead', 'skeleton', 'barrow', 'melee', 'fantasy']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': DISPLAY_NAME},
    'body': {'body_plan': 'Biped', 'body_kind': 'Standard',
             'mass_class': 'Medium', 'locomotion_hint': 'Walk', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'brain': {'default_preset': 'melee_brute_striker'},
    'actions': {'default_preset': 'barrow_skeleton_slash'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': 0.0, 'event': 'hitbox_active_start', 'source': 'barrow_skeleton.slash'},
            {'t': 0.16 / (14 * 0.049), 'event': 'hitbox_active_end', 'source': 'barrow_skeleton.slash'},
        ]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': 'A brittle animated skeleton in scraps of burial cloth. It advances with a rusty sword and a green corpse-light in one eye socket.',
    'gameplay_description': 'A light melee undead that shuffles forward, raises its sword for a clear tell, and collapses into a heap when defeated.',
}


CX = 108.
RAG, RAG_L, RAG_D = '#8d7d60', '#b3a17c', '#5e5343'
METAL, METAL_L, METAL_D = '#8b9292', '#d0d3c7', '#53585b'
RUST = '#80513b'
INK = '#39332d'
EYE = '#9ed5a0'


@dataclass(frozen=True)
class Pose:
    hip: tuple = (CX, GROUND-52)
    lean: float = 5.
    head: float = -5.
    jaw: float = 1.
    near_foot: tuple = (CX+10,GROUND-4)
    far_foot: tuple = (CX-11,GROUND-4)
    near_hand: tuple = (CX+16,GROUND-68)
    far_hand: tuple = (CX-13,GROUND-66)
    sword: float = 37.
    near_toe: float = 0.
    far_toe: float = 0.
    rag: float = 0.
    eye: bool = True


IDLE = Pose()
READY = replace(IDLE, hip=(CX-3,GROUND-49), lean=-7, head=-14, jaw=2.,
                near_hand=(CX-9,GROUND-94),far_hand=(CX+11,GROUND-71),sword=-134,
                near_foot=(CX+13,GROUND-4),far_foot=(CX-15,GROUND-4))
STRIKE = replace(IDLE,hip=(CX+7,GROUND-49),lean=19,head=10,jaw=3.,
                 near_hand=(CX+42,GROUND-78),far_hand=(CX-12,GROUND-64),sword=-4,
                 near_foot=(CX+21,GROUND-4),far_foot=(CX-15,GROUND-4))
SPENT = replace(STRIKE,lean=24,head=15,near_hand=(CX+29,GROUND-51),sword=57)


def _blend(a,b,t):
    values={}
    for k in a.__dataclass_fields__:
        x,y=getattr(a,k),getattr(b,k)
        values[k]=mix(x,y,t) if isinstance(x,tuple) else (x if t<.5 else y) if isinstance(x,bool) else x+(y-x)*t
    return Pose(**values)


def _keys(t,keys):
    for (lo,a),(hi,b) in zip(keys,keys[1:]):
        if t<=hi:
            return _blend(a,b,track(t,[(lo,0),(hi,1)]))
    return keys[-1][1]


def _step(t,stride,lift):
    """Move the planted foot back, then return it forward above the floor."""
    t=t%1.
    if t<.57:
        return stride*(1-2*t/.57),0.,0.
    u=(t-.57)/.43
    return stride*(-1+2*u),lift*math.sin(math.pi*u),-15*math.sin(math.pi*u)


def pose(anim,i,n):
    t=phase(i,n,anim in LOOPS); s=math.sin(math.tau*t)
    if anim=='idle':
        return replace(IDLE,hip=(CX,GROUND-52+.6*s),head=-5+2*s,jaw=1+.5*s,rag=s)
    if anim in ('walk','run'):
        stride,lift=(17,10) if anim=='walk' else (21,14)
        nx,ny,nt=_step(t,stride,lift); fx,fy,ft=_step(t+.5,stride,lift)
        return replace(IDLE,hip=(CX,GROUND-51+1.2*math.cos(2*math.tau*t)),
                       lean=8 if anim=='walk' else 15,head=2*s,
                       near_foot=(CX+nx,GROUND-4-ny),far_foot=(CX+fx,GROUND-4-fy),
                       near_toe=nt,far_toe=ft,near_hand=(CX+17-7*s,GROUND-67),
                       far_hand=(CX-9+11*s,GROUND-66),sword=30-15*s,rag=2*s)
    if anim=='notice':
        return _keys(t,[(0,IDLE),(.5,replace(IDLE,head=-14,jaw=2.4,near_hand=(CX+20,GROUND-78),sword=-15)),(1,replace(IDLE,head=-14,jaw=2.4,near_hand=(CX+20,GROUND-78),sword=-15))])
    if anim=='windup':
        return _keys(t,[(0,IDLE),(.72,READY),(1,READY)])
    if anim=='attack_side':
        # The windup row ends at READY. The first 0.16 s is the slash.
        return _keys(t,[(0,READY),(.15,STRIKE),(.23,STRIKE),(.42,SPENT),(.66,SPENT),(1,IDLE)])
    if anim=='hit':
        hit=replace(IDLE,hip=(CX-5,GROUND-51),lean=-18,head=-21,jaw=4.,near_hand=(CX-2,GROUND-77),sword=-26,far_hand=(CX-27,GROUND-69))
        return _keys(t,[(0,IDLE),(.28,hit),(.55,hit),(1,IDLE)])
    if anim in ('death','death_idle'):
        return replace(IDLE,eye=False)
    raise ValueError(anim)


def _solve(p):
    def T(x,y): return add(p.hip,rot((x,y),p.lean))
    neck=T(0,-43); head=add(neck,rot((4,-18),p.head))
    def limb(root,target,l1,l2,bend):
        return (root,*two_bone_ik_points(root,target,l1,l2,bend,extension_margin=.1))
    # Knees bend toward the direction of travel; elbows bend backward.
    return dict(pelvis=p.hip,neck=neck,head=head,
                far_leg=limb(T(-5,0),p.far_foot,27,27,1),
                near_leg=limb(T(5,0),p.near_foot,27,27,1),
                far_arm=limb(T(-8,-37),p.far_hand,21,22,-1),
                near_arm=limb(T(8,-37),p.near_hand,21,22,-1))


def _sword(c,wrist,angle):
    def q(x,y): return add(wrist,rot((x,y),angle))
    c.poly([q(-4,-2.5),q(8,-2.5),q(8,2.5),q(-4,2.5)],RAG_D,INK,1.)
    for x in (-2,1,4):c.line([q(x,-2),q(x+2,2)],RAG_L,.9)
    c.disk(q(-5,0),3.2,RUST,INK,1.)
    c.poly([q(7,-7),q(10,-7),q(12,-2),q(12,2),q(10,7),q(7,7)],RUST,INK,1.)
    c.poly([q(11,-4),q(34,-4),q(38,-1.5),q(40,-4),q(48,0),q(41,4),q(12,4)],METAL,INK,1.3)
    c.poly([q(12,1),q(47,0),q(41,4),q(12,4)],METAL_D,None)
    c.line([q(12,-3),q(34,-3)],METAL_L,1.3)
    for x,y in ((17,2),(23,-1),(32,2),(39,0)):
        c.line([q(x,y),q(x+3,y-1)],RUST,1.5)


def _cloth(c,hip,lean,rag):
    def q(x,y):return add(hip,rot((x,y),lean))
    c.poly([q(-10,0),q(9,1),q(10,7),q(5,15+rag),q(1,10),q(-3,18),q(-7,11-rag),q(-12,8)],RAG,INK,1.2)
    c.poly([q(-10,1),q(-4,4),q(-3,18),q(-7,11-rag),q(-12,8)],RAG_D,None)
    c.line([q(-9,-.5),q(1,1),q(9,0)],RAG_L,2.1)
    c.line([q(4,4),q(6,10+rag)],RAG_L,1.1)


def _drop_group(points,angle,goal,t):
    """Rotate and lower a connected group without changing its lengths."""
    origin=points[0]; dest=mix(origin,goal,t)
    return tuple(add(dest,rot(sub(p,origin),angle*t)) for p in points)


def _death(p,j,t):
    # Each limb drops independently. The final pile is also death_idle.
    u=track(t,[(0,0),(.12,0),(.72,1),(1,1)])
    core=_drop_group((j['pelvis'],j['neck']),87,(CX-18,GROUND-15),u)
    j.update(pelvis=core[0],neck=core[1],head=mix(j['head'],(CX+37,GROUND-17),u))
    for name,angle,goal in (
        ('far_leg',82,(CX-12,GROUND-9)),('near_leg',-70,(CX-24,GROUND-12)),
        ('far_arm',105,(CX+7,GROUND-14)),('near_arm',-66,(CX-2,GROUND-8))):
        j[name]=_drop_group(j[name],angle,goal,u)
    # Move each collapsed group above the floor as needed.
    for name in ('far_leg','near_leg','far_arm','near_arm'):
        pts=j[name]; excess=max(0,max(y for x,y in pts)+5-GROUND)
        j[name]=tuple((x,y-excess) for x,y in pts)
    return replace(p,head=70*u,jaw=1+2*u,lean=5+87*u,sword=37*(1-u),
                   near_toe=-65*u,far_toe=75*u,eye=False),j


def render_pose(p, *, bones_only=False, palette=bones.IVORY, death=None):
    """Render the same solved pose with or without the enemy's equipment."""
    j=_solve(p)
    if death is not None: p,j=_death(p,j,death)
    c=Canvas(FRAME_SIZE)
    bones.leg(c,j['far_leg'],palette,True,foot_angle=p.far_toe)
    bones.arm(c,j['far_arm'],palette,True,hand_angle=85)
    bones.trunk(c,j['pelvis'],j['neck'],palette)
    if not bones_only: _cloth(c,j['pelvis'],p.lean,p.rag)
    bones.leg(c,j['near_leg'],palette,foot_angle=p.near_toe)
    bones.skull(c,j['head'],p.head,1.,p.jaw,palette,EYE if p.eye and not bones_only else None)
    wrist=j['near_arm'][-1]
    release=track(death,[(0,0),(.3,0),(.85,1),(1,1)]) if death is not None else 0.
    if not bones_only:
        _sword(c,mix(wrist,(CX+48,GROUND-6),release),p.sword)
    bones.arm(c,j['near_arm'],palette,hand_angle=p.sword,grip=not bones_only and release<.5)
    im=c.finish()
    if death is not None:
        # Keep the loose bones and sword above the contact row.
        bb=im.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox()
        excess=max(0,bb[3]-int(GROUND+1))
        if excess:
            shifted=Image.new('RGBA',FRAME_SIZE)
            shifted.paste(im,(0,-excess))
            im=shifted
    return im


def _render_frame(anim,i,n):
    p=pose(anim,i,n)
    death=phase(i,n,False) if anim=='death' else 1. if anim=='death_idle' else None
    return render_pose(p,death=death)


def _body_metrics(fw,fh):
    # Exclude the sword, reaching arms, and the attack pose from body size.
    return body_metrics_for_box((CX-17,21,CX+18,GROUND+1),fw,fh)


def render(out_dir: str | Path, **opts):
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,
                        out_dir=out_dir,frame_size=FRAME_SIZE,auto_crop=False,
                        actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,
                        animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
