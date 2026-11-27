"""Cockatrice: a ground monster with a bird's head, bat wings and a snake tail.

The legs plant before the body advances. The wings spread to warn of a
bite; the neck extends during the strike. The sprite does not move the root.
"""
from __future__ import annotations

import math
from pathlib import Path

from ._clockwork_enemy_art import (
    Canvas, add, sub, mul, mix, rot, unit, perp, bezier, phase, track,
    anchored_death,
)
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'cockatrice'
DISPLAY_NAME = 'Cockatrice'
FRAME_SIZE = (300, 238)
GROUND = 221.
ROWS = [('idle', 12, 110), ('walk', 12, 100), ('run', 12, 70),
        ('notice', 6, 85), ('windup', 10, 45), ('attack_side', 12, 50),
        ('hit', 6, 75), ('death', 14, 90), ('death_idle', 6, 180)]
LOOPS = {'idle', 'walk', 'run', 'death_idle'}
TRAITS = ['enemy', 'fantasy', 'monster', 'cockatrice', 'beast']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': DISPLAY_NAME},
    'body': {'body_plan': 'AvianBiped', 'body_kind': 'Standard',
             'mass_class': 'Medium', 'locomotion_hint': 'Walk', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'actions': {'default_preset': 'cockatrice_snap'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': 0., 'event': 'hitbox_active_start', 'source': 'cockatrice.snap'},
            {'t': .12 / .60, 'event': 'hitbox_active_end', 'source': 'cockatrice.snap'}]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': 'A green-scaled cockatrice with a rust-red crest, hooked beak, leathery wings, talons and a long serpent tail.',
    'gameplay_description': 'It spreads its wings, draws its neck back, snaps forward, and then recovers.',
}

INK = '#252c2c'
GREEN, LIGHT, DARK, DEEP = '#547959', '#8bad78', '#375644', '#263e36'
BELLY, BELLY_D = '#d1bd79', '#ad9457'
RED, RED_L, RED_D = '#b34d3d', '#e07a51', '#74352e'
WING, WING_L, WING_D = '#a8754e', '#c99863', '#674c40'
BEAK, BEAK_L, BEAK_D = '#d7aa55', '#f5d88b', '#82613e'
CLAW = '#e5d5af'


def tapered(c, pts, widths, fill, edge=INK, line=LIGHT, bands=None):
    """Draw a tapered tube with optional curved scale divisions."""
    left, right = [], []
    for i, (p, width) in enumerate(zip(pts, widths)):
        n = perp(unit(sub(pts[min(i+1, len(pts)-1)], pts[max(0, i-1)])))
        left.append(add(p, mul(n, width)))
        right.append(add(p, mul(n, -width)))
    c.poly(left + right[::-1], fill, edge, 1.5)
    if line:
        c.line([mix(a,b,.24) for a,b in zip(left,right)], line, 1.8)
    if bands:
        for i in range(4,len(pts)-3,bands):
            c.line([mix(left[i],right[i],.10), mix(left[i-2],right[i-2],.50),
                    mix(left[i],right[i],.9)], DARK, 1.15)
    return left,right


def _render_frame(anim, i, n):
    t = phase(i,n,anim in LOOPS)
    cyc = math.tau*t
    bob = 1.1*math.sin(cyc); stride=0.; spread=.08; draw=0.; snap=0.; gape=0.
    tilt=0.; recoil=0.; collapse=0.; blink=1.; tailwave=math.sin(cyc)
    if anim in ('walk','run'):
        stride=1. if anim=='walk' else 1.5
        bob=-2.5*stride*math.cos(2*cyc)
        tilt=5*stride; spread=.13+.12*stride
        snap=.12*math.sin(2*cyc)
    elif anim=='notice':
        draw=.35*math.sin(math.pi*t); spread=.16+.28*math.sin(math.pi*t)
        bob=-3*math.sin(math.pi*t)
    elif anim=='windup':
        draw=track(t,[(0,.10),(.40,1),(1,1)])
        spread=track(t,[(0,.15),(.55,1),(1,1)])
        bob=3*draw; gape=.18*draw; tailwave=-draw
    elif anim=='attack_side':
        # The first 0.12 s is active; the remaining 0.48 s is recovery.
        snap=track(t,[(0,.78),(.08,1),(.20,.91),(.42,.30),(.72,-.10),(1,0)])
        gape=track(t,[(0,.85),(.08,1),(.20,.05),(.32,0),(1,0)])
        spread=track(t,[(0,1),(.18,.95),(.6,.18),(1,.08)])
        tilt=track(t,[(0,8),(.15,13),(.40,7),(1,0)])
        bob=2*math.sin(math.pi*t); tailwave=math.sin(math.pi*t)*-.8
    elif anim=='hit':
        recoil=math.sin(math.pi*t); tilt=-15*recoil; draw=.60*recoil
        spread=.08+.5*recoil; gape=.7*recoil; blink=1-recoil
    elif anim in ('death','death_idle'):
        collapse=track(t,[(0,0),(.18,.10),(.72,1),(1,1)]) if anim=='death' else 1.
        spread=.1+.60*math.sin(math.pi*collapse); blink=1-collapse
        tilt=76*collapse; tailwave=0.; bob=0.
    c=Canvas(FRAME_SIZE)
    cx=140-9*recoil; cy=145+bob+34*collapse
    def B(p): return add((cx,cy),rot(p,tilt))
    def poly(pts,col,edge=INK,w=1.65): c.poly([B(p) for p in pts],col,edge,w)
    def line(pts,col,w=1.4): c.line([B(p) for p in pts],col,w)
    def oval(p,rx,ry,col,edge=INK,w=1.5,ang=0): c.oval(B(p),rx,ry,col,edge,w,tilt+ang)
    # Long serpent tail, curled up at its narrow end.
    a=B((-32,3)); b=B((-70,15+5*tailwave)); z=B((-102,0+8*tailwave)); e=B((-112,-26+8*tailwave))
    pts=bezier(a,b,z,e,32)
    widths=[12*(1-j/32)**.72+1 for j in range(33)]
    tapered(c,pts,widths,DARK,INK,GREEN,4)
    # A terminal barb marks the snake-like silhouette.
    poly([(-108,-21+8*tailwave),(-120,-31+8*tailwave),(-111,-42+8*tailwave),(-106,-33+8*tailwave)],GREEN,INK,1.3)
    # Far wing and near wing use one articulated wing geometry.
    def wing(far):
        pivot=(-7,-18) if far else (0,-17)
        angle=(-48+64*spread if far else -47+50*spread)
        scale=(.70+.22*spread) if far else (.76+.24*spread)
        def W(p): return B(add(pivot,rot(mul(p,scale),angle)))
        def wp(pts,col,edge=INK,w=1.6): c.poly([W(p) for p in pts],col,edge,w)
        def wl(pts,col,w=1.6): c.line([W(p) for p in pts],col,w)
        # Digits form a scalloped membrane, with a hook at the wrist.
        # Curve the concave trailing edge between each wing digit.
        rim = [(0,0),(-10,-26),(-29,-50),(-58,-60)]
        for p0,p1,p2,p3 in [((-58,-60),(-40,-42),(-41,-31),(-58,-23)),
                            ((-58,-23),(-43,-27),(-38,-20),(-47,-6)),
                            ((-47,-6),(-34,-16),(-27,-11),(-31,5)),
                            ((-31,5),(-20,-3),(-11,3),(-6,16))]:
            rim.extend(bezier(p0,p1,p2,p3,8)[1:])
        wp(rim,WING_D if far else WING)
        wp([(-10,-26),(-29,-50),(-58,-60),(-38,-32),(-47,-35),(-58,-23),(-29,-27)],WING if far else WING_L,None)
        for p in [(-58,-60),(-58,-23),(-47,-6),(-31,5)]:
            wl([(0,0),(-10,-26),p],DEEP if far else WING_D,2.4)
        wl([(0,0),(-10,-26),(-29,-50)],GREEN if far else LIGHT,3.5)
        wp([(-12,-26),(-15,-37),(-5,-34),(-8,-25)],CLAW,INK,1.0)
    wing(True)
    # The planted part of the gait moves backwards relative to the body.
    def leg(far,offset):
        q=(t+offset)%1
        span=17*stride
        if q<.60:
            dx=span*(1-2*q/.60); lift=0.
        else:
            u=(q-.60)/.40; dx=span*(-1+2*u); lift=13*stride*math.sin(math.pi*u)
        if collapse: dx=0.; lift=0.
        hip=B((4 if far else 12,13))
        ankle=(cx+(3 if far else 11)+dx+24*collapse,GROUND-10-lift)
        knee=(hip[0]+13*(1-collapse)+dx*.35,hip[1]+22*(1-collapse)+4*collapse)
        hock=(ankle[0]-11*(1-collapse),ankle[1]-12*(1-collapse))
        col=DARK if far else GREEN
        c.tube(hip,knee,9,col,None if far else LIGHT,DEEP,INK)
        c.oval(knee,7.5,7,col,INK,1.3)
        c.tube(knee,hock,5.7,BEAK_D if far else BEAK, None if far else BEAK_L,DARK,INK)
        c.tube(hock,ankle,3.8,BEAK_D if far else BEAK,None if far else BEAK_L,DARK,INK)
        # Three grounded toes and contrasting talons.
        x,y=ankle
        for a,b in [((-1,0),(-10,8)),((0,2),(16,8)),((2,4),(9,10))]:
            p=add(ankle,a); e=add(ankle,b)
            c.tube(p,e,2.6,BEAK_D if far else BEAK,None,None,INK)
            c.poly([add(e,(-2,-1)),add(e,(6 if b[0]>0 else -4,-1)),add(e,(1,2))],CLAW,INK,.9)
        for k in range(2):
            p=mix(hock,ankle,.35+.26*k);c.line([add(p,(-3,0)),add(p,(3,1))],BEAK_D,1)
    leg(True,.5)
    # Torso and armored neck base.
    poly([(-39,-7),(-30,-24),(-9,-31),(13,-30),(31,-19),(35,-2),(23,18),(1,26),(-20,22),(-35,11)],GREEN)
    poly([(-31,-5),(-15,-2),(7,-5),(27,-13),(31,-1),(20,18),(1,25),(-21,20),(-32,10)],BELLY,None)
    for j in range(4):
        line([(-20+j*3,4+j*4),(-4,7+j*4),(13,3+j*4),(23,-3+j*4)],BELLY_D,1.2)
    poly([(-36,-9),(-25,-22),(-8,-26),(13,-27),(20,-19),(4,-13),(-14,-15),(-24,-6)],LIGHT,None)
    for x,y in [(-29,-11),(-19,-20),(-10,-12),(2,-21),(12,-14)]:
        line([(x-4,y),(x,y+3),(x+4,y)],DARK,1.25)
    leg(False,0)
    wing(False)
    # The head is carried on a flexible neck that coils, then extends.
    # Curves are attached to the torso and head in the same local frame.
    base=B((23,-17)); head_local=(38+39*snap-18*draw,-66+29*snap-2*draw)
    head=B(head_local)
    pts=bezier(base,B((36+12*snap,-29)),B((14+38*snap-22*draw,-58)),head,28)
    widths=[14-4*j/28+2*math.sin(math.pi*j/28) for j in range(29)]
    l,r=tapered(c,pts,widths,GREEN,INK,LIGHT,4)
    # Warm throat scales run along the forward edge.
    c.poly([mix(a,b,.04) for a,b in zip(l,r)]+[mix(a,b,.44) for a,b in zip(l,r)][::-1],BELLY,None)
    for k in range(4,26,4):
        c.line([mix(l[k],r[k],.05),mix(l[k-1],r[k-1],.22),mix(l[k],r[k],.43)],BELLY_D,1.0)
    hang=tilt+8*snap-9*draw
    def H(p):return add(head,rot(p,hang))
    def hp(pts,col,edge=INK,w=1.5):c.poly([H(p) for p in pts],col,edge,w)
    def hl(pts,col,w=1.4):c.line([H(p) for p in pts],col,w)
    def ho(p,rx,ry,col,edge=INK,w=1.2):c.oval(H(p),rx,ry,col,edge,w,hang)
    # A spiked comb and cheek wattles distinguish the cockatrice from a drake.
    hp([(-14,-8),(-23,-17),(-23,-26),(-15,-23),(-11,-37),(-4,-27),(3,-38),(8,-25),(16,-30),(16,-15),(21,-10)],RED,INK,1.7)
    hl([(-18,-23),(-12,-27),(-5,-26),(3,-30),(8,-24),(14,-25)],RED_L,2)
    hp([(-16,0),(-12,-14),(1,-21),(15,-16),(23,-6),(21,8),(12,14),(-2,13),(-12,8)],GREEN,INK,1.8)
    hp([(-12,-8),(-4,-16),(10,-13),(16,-7),(4,-4),(-6,2)],LIGHT,None)
    hp([(11,8),(20,10),(20,21),(14,26),(9,19),(6,25),(2,18),(6,10)],RED_D,INK,1.5)
    hp([(10,10),(18,12),(16,20),(11,21)],RED,None)
    # Hooked upper beak and separately articulated lower jaw.
    hp([(17,-8),(29,-7),(39,-1-4*gape),(38,4-4*gape),(32,10-4*gape),(32,4-4*gape),(17,3)],BEAK,INK,1.6)
    hp([(19,-6),(29,-5),(36,-1-4*gape),(26,0)],BEAK_L,None)
    hp([(17,3),(31,5+9*gape),(34,4+9*gape),(28,10+7*gape),(19,9)],BEAK_D,INK,1.3)
    if gape>.30:
        hp([(21,3),(29,4-3*gape),(27,5+7*gape),(20,6)],DEEP,None)
    ho((27,-3),1.5,1.1,BEAK_D,None)
    if blink>.15:
        ho((11,-7),6.0,4.6*blink,'#e7c760',INK,1.3)
        ho((12,-7),1.7,3.4*blink,INK,None)
        ho((10,-8.2),.9,.9,'#fff4cf',None)
    else: hl([(5,-7),(16,-7)],INK,1.8)
    hl([(5,-13),(15,-11),(19,-8)],DEEP,2.4)
    im=c.finish()
    if collapse: im=anchored_death(im,GROUND)
    return im


def _body_metrics(fw,fh):
    # The resting body excludes the tail, wing tips and extended beak.
    return body_metrics_for_box((104,67,188,int(GROUND)+1),fw,fh)


def render(out_dir: str | Path, **opts):
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,
                        out_dir=out_dir,frame_size=FRAME_SIZE,auto_crop=False,
                        actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,
                        animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
