"""Crag Ibex: a territorial mountain animal with a short, warned charge.

The feet move back during stance and forward during swing. The engine moves
its body during the charge; the sheet changes its posture, not its location.
"""
from __future__ import annotations

import math
from pathlib import Path

from ._clockwork_enemy_art import Canvas, add, bezier, mix, mul, phase, rot, track, unit, perp
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'crag_ibex'
DISPLAY_NAME = 'Crag Ibex'
FRAME_SIZE = (252, 230)
GROUND = 215.
ROWS = [('idle', 10, 150), ('walk', 12, 100), ('run', 12, 70),
        ('notice', 6, 90), ('windup', 10, 65), ('attack_side', 15, 60),
        ('hit', 5, 85), ('death', 12, 100), ('death_idle', 6, 180)]
LOOPS = {'idle', 'walk', 'run', 'windup', 'death_idle'}
TRAITS = ['enemy', 'animal', 'quadruped', 'fantasy', 'mountain']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': DISPLAY_NAME},
    'body': {'body_plan': 'Quadruped', 'body_kind': 'Standard',
             'mass_class': 'Medium', 'locomotion_hint': 'Walk', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'actions': {'default_preset': 'crag_ibex_charge'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': 0.0, 'event': 'hitbox_active_start', 'source': 'crag_ibex.charge'},
            {'t': 0.2 / 0.9, 'event': 'hitbox_active_end', 'source': 'crag_ibex.charge'}]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': 'A stocky brown mountain ibex with a pale saddle, black beard, and long ridged horns.',
    'gameplay_description': 'It paws the ground, lowers its horns, charges a short distance, and recovers.',
}

INK = '#312a28'
COAT, LIGHT, SHADE, DARK = '#94704c', '#c3a27b', '#6c5040', '#4a3933'
BELLY, MUZZLE, HOOF = '#ded0af', '#b6a188', '#363039'
HORN, RIDGE, HORN_D = '#c2b394', '#e2d3ac', '#736654'


def _render_frame(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    c = Canvas(FRAME_SIZE)
    cyc = math.tau*t
    head = -4.; bob = 0.; lean = 0.; fold = 0.; eye = 1.; gait = 0.; speed = 0.; paw = 0.
    if anim == 'idle':
        head = 7*math.sin(cyc)-4
        bob = 1.2*math.sin(cyc)
    elif anim in ('walk', 'run'):
        gait = t; speed = 1. if anim == 'walk' else 1.6
        bob = 2.*speed*math.cos(2*cyc)
        head = -4+3*math.sin(2*cyc)
    elif anim == 'notice':
        head = -4-18*math.sin(math.pi*t)
        lean = -3*math.sin(math.pi*t)
    elif anim == 'windup':
        head = 65+2*math.sin(2*cyc)
        lean = -6
        paw = math.sin(cyc)**2
        bob = -2
    elif anim == 'attack_side':
        # The first 0.20 s is the rush; the remaining 0.70 s is recovery.
        head = track(t, [(0,65),(.18,59),(.33,12),(.55,4),(1,-4)])
        lean = track(t, [(0,-6),(.17,5),(.28,3),(.6,0),(1,0)])
        speed = track(t, [(0,1.7),(.19,1.7),(.32,.5),(.48,0),(1,0)])
        gait = min(t/.33,1)*1.5
        bob = 2*speed*math.cos(gait*math.tau*2)
    elif anim == 'hit':
        recoil = math.sin(math.pi*t)
        head = -4-25*recoil; lean = -5*recoil; eye = 1-recoil
    elif anim in ('death', 'death_idle'):
        fold = track(t, [(0,0),(.35,.25),(.75,1),(1,1)]) if anim == 'death' else 1.
        head = -4+32*fold; eye=1-fold
    # Body-local points. At full collapse the body is near the ground.
    yshift = 40 + 43*fold-bob
    def B(p): return (p[0]+lean,p[1]+yshift)
    def poly(points, col, edge=INK, w=1.6): c.poly([B(p) for p in points],col,edge,w)
    def line(points, col, w=1.5): c.line([B(p) for p in points],col,w)
    def oval(p,rx,ry,col,edge=INK,w=1.5,angle=0): c.oval(B(p),rx,ry,col,edge,w,angle)
    # Tail: short, pointed, held up when charging.
    poly([(63,101),(48,91-speed*4),(42,96),(49,108),(64,112)],DARK)
    # A leg's planted half of the cycle moves backward. Its swing is lifted.
    def leg(x, front, near, offset):
        q=(gait+offset)%1
        travel = 18*speed
        if q < .55:
            swing=travel*(1-2*q/.55); lift=0.
        else:
            u=(q-.55)/.45; swing=travel*(-1+2*u); lift=12*speed*math.sin(math.pi*u)
        if not speed: swing=0.; lift=0.
        if anim=='windup' and front and near: swing=8*paw; lift=13*paw
        hip=B((x,119 if front else 118))
        foot=(x+lean+swing+(5 if front else -4),GROUND-lift)
        if fold:
            foot=(x+lean+(18 if front else -12)*fold,GROUND-1)
        knee=(hip[0]+(9 if front else -13)*(1-fold)+swing*.42,hip[1]+(25*(1-fold)+5*fold))
        ankle=(foot[0]-3,foot[1]-10)
        col=COAT if near else SHADE
        c.tube(hip,knee,9.0*(1-.25*fold),col, LIGHT if near else None, DARK,INK)
        c.tube(knee,ankle,4.8,col,LIGHT if near else None,DARK,INK)
        c.poly([(ankle[0]-5,ankle[1]-2),(ankle[0]+4,ankle[1]),(foot[0]+6,foot[1]-1),(foot[0]-7,foot[1]-1)],HOOF,INK,1.4)
        c.line([(foot[0],foot[1]-7),(foot[0]+1,foot[1]-2)],'#675e59',1)
    leg(75,False,False,.5); leg(143,True,False,0)
    # Compact torso; the pale belly and saddle give readable value contrast.
    poly([(58,95),(74,85),(104,83),(129,85),(146,80),(159,91),(161,115),
          (148,132),(119,138),(93,137),(73,129),(59,116)],COAT)
    poly([(62,103),(76,113),(94,120),(119,119),(142,110),(149,126),(126,135),(99,136),(76,128),(63,117)],BELLY,None)
    poly([(67,97),(82,89),(106,88),(126,91),(143,87),(146,96),(132,103),(107,101),(91,106),(76,102)],LIGHT,None)
    line([(66,96),(81,89),(105,88),(127,91),(146,85)],'#e0c29c',2.2)
    line([(67,120),(76,129),(93,133)],SHADE,2.2)
    for x,y in [(77,101),(90,99),(111,95),(125,98),(70,112),(105,121),(134,106)]:
        line([(x,y),(x-4,y+6),(x+2,y+4)],SHADE,1.2)
    leg(82,False,True,0); leg(151,True,True,.5)
    # Neck with shaggy chest and dark stripe on the shoulder.
    neck=B((148,91))
    def H(p): return add(neck,rot(p,head))
    def hp(points,col,edge=INK,w=1.7): c.poly([H(p) for p in points],col,edge,w)
    def hl(points,col,w=1.4): c.line([H(p) for p in points],col,w)
    def ho(p,rx,ry,col,edge=INK,w=1.3,ang=0): c.oval(H(p),rx,ry,col,edge,w,head+ang)
    hp([(-13,15),(-16,-8),(-7,-32),(8,-43),(23,-36),(24,-13),(12,13),(4,29),(-3,20),(-8,25)],COAT)
    hp([(-7,-23),(5,-34),(10,-19),(5,-2),(-3,16),(-10,12)],LIGHT,None)
    hp([(14,-23),(22,-13),(16,13),(6,24),(4,12),(10,-4)],DARK,None)
    # Long back-swept horns, defined by a taper around a Bezier centreline.
    def horn(base, far):
        pts=bezier(base,add(base,(-2,-30)),add(base,(-16 if far else -24,-58 if far else -62)),add(base,(-31 if far else -50,-64 if far else -65)),32)
        widths=[(8.7 if not far else 7.0)*(1-k/32)**.67+.25 for k in range(33)]
        left=[]; right=[]
        for k,p in enumerate(pts):
            normal=perp(unit((pts[min(k+1,32)][0]-pts[max(k-1,0)][0],pts[min(k+1,32)][1]-pts[max(k-1,0)][1])))
            left.append(add(p,mul(normal,widths[k])));right.append(add(p,mul(normal,-widths[k])))
        hp(left+right[::-1],HORN_D if far else HORN,INK,1.5)
        hl([mix(a,b,.23) for a,b in zip(left,right)],RIDGE if not far else HORN,1.4)
        for k in range(3,25,3):
            hl([mix(left[k],right[k],.06),mix(left[k-1],right[k-1],.48),mix(left[k],right[k],.94)],HORN_D if not far else DARK,1.8)
    horn((16,-39),True)
    # Far ear, head and muzzle.
    hp([(7,-35),(-12,-44),(-19,-39),(-6,-28)],SHADE)
    hp([(5,-40),(23,-41),(36,-30),(43,-17),(39,-9),(29,-6),(19,-12),(8,-20),(2,-32)],COAT)
    hp([(29,-29),(38,-24),(44,-15),(39,-9),(30,-8),(25,-15)],MUZZLE)
    hl([(30,-8),(37,-8),(41,-11)],DARK,1.7)
    ho((39,-17),2.9,2.2,DARK,None)
    hp([(19,-15),(28,-10),(27,3),(21,13),(18,1),(14,7),(13,-10)],DARK)
    hp([(5,-36),(-13,-31),(-21,-34),(-13,-23),(4,-24)],COAT)
    hl([(-15,-32),(-7,-28),(1,-29)],SHADE,2.1)
    horn((6,-39),False)
    if eye>.1:
        ho((25,-28),5.3,3.8*eye,'#f0c977',INK,1.2,-6)
        ho((26,-28),3.6,1.1*eye,INK,None)
        ho((24,-29.5),.9,.9,'#fff1ce',None)
    else: hl([(20,-28),(28,-27)],INK,1.5)
    if anim in ('windup','attack_side'):
        hl([(19,-34),(29,-31)],DARK,2.4)
    return c.finish()


def _body_metrics(fw,fh):
    # Torso, neck and grounded legs, excluding the horns and tail.
    return body_metrics_for_box((59,89,192,GROUND),fw,fh)


def render(out_dir: str | Path, **opts):
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,
                        out_dir=out_dir,frame_size=FRAME_SIZE,auto_crop=False,
                        actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,
                        animation_key_map={a:a for a,_,_ in ROWS})
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
