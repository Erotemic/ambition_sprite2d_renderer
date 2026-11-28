"""Giant dungeon rat with a bounding gait and a short lunging bite."""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image

from ._magic_character_art import Canvas, add, sub, mul, mix, unit, perp, rot, bezier, phase, track, anchored_death
from ...authoring.sheet_build import build_sheet
from ...authoring.part_flipbook import publish_rig_flipbook
from ._rat_parts import PartScene, limb_segment, reflect, quarter_frame
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'giant_rat'
# Pad the right edge to contain the old-facing tail reflected around the
# authored body anchor. The original drawings retain their coordinates.
FRAME_SIZE = (320, 184)
GROUND = 153.0
BODY_BOX = (88, 67, 230, 154)
ROWS = [('idle', 16, 75), ('walk', 16, 65), ('run', 16, 40),
        ('turnaround', 5, 44), ('notice', 8, 50), ('windup', 8, 40), ('attack_side', 12, 40),
        ('hit', 8, 50), ('death', 18, 55), ('death_idle', 6, 150)]
LOOPS = {'idle', 'walk', 'run', 'windup', 'death_idle'}
TRAITS = ['enemy', 'fantasy', 'monster', 'rat', 'rodent', 'quadruped']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Giant Rat'},
    'body': {'body_plan': 'Quadruped', 'body_kind': 'Standard',
             'mass_class': 'Light', 'locomotion_hint': 'Walk', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'actions': {'default_preset': 'giant_rat_bite'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'locomotion.turnaround': {'animation': 'turnaround', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': 0.0, 'event': 'hitbox_active_start', 'source': 'giant_rat.bite'},
            {'t': .12/.48, 'event': 'hitbox_active_end', 'source': 'giant_rat.bite'}]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': 'A large rat with coarse brown-grey fur, rounded ears, long incisors, bare paws and a tapered scaly tail.',
    'gameplay_description': 'It sniffs, crouches low, darts forward with its jaws open and retreats after it bites.',
}

INK = '#292327'
FAR_INK = '#3b3031'
FUR = '#756459'
FUR_DARK = '#4a3e3b'
FUR_LIGHT = '#9b8774'
FUR_PALE = '#b9a38a'
FAR = '#544743'
FAR_LIGHT = '#796459'
BELLY = '#a28d78'
SKIN = '#a27c77'
SKIN_LIGHT = '#c09a8e'
SKIN_DARK = '#76585b'
TAIL = '#a68079'
TOOTH = '#ecdcba'
EYE = '#d99545'


def _curve(points):
    out = [points[0]]
    for k in range(1, len(points), 3):
        out.extend(bezier(out[-1], *points[k:k+3], n=16)[1:])
    return out


def _shape(c, points, fill, edge=INK, width=2.0):
    c.poly(_curve(points), fill, edge, width)


def _gait(t, stride, lift, stance):
    """Move a foot back on the ground, then forward in the air."""
    t %= 1.0
    if t < stance:
        return stride*(.5 - t/stance), 0.0
    s = (t-stance)/(1-stance)
    return stride*(-.5 + .5*(1-math.cos(math.pi*s))), -lift*math.sin(math.pi*s)



def _front_frame():
    """A head-on, slightly elevated view of the same rat, planted on all fours.

    The hindquarters, paws, pinnae, and tapered muzzle have their own
    projected landmarks. No part of the side silhouette is rescaled.
    """
    c = PartScene(sys.modules[__name__])
    cx = (BODY_BOX[0] + BODY_BOX[2] - 1) / 2

    def pts(seq, side=1):
        return [(cx + side*x, y) for x, y in seq]

    def shape(seq, fill, edge=INK, width=1.8, side=1):
        _shape(c, pts(seq, side), fill, edge, width)

    def poly(seq, fill, edge=INK, width=1.4, side=1):
        c.poly(pts(seq, side), fill, edge, width)

    def line(seq, color=INK, width=1.2, side=1):
        c.line(pts(seq, side), color, width)

    def oval(x, y, rx, ry, color, edge=INK, width=1.5, angle=0):
        c.oval((cx+x,y),rx,ry,color,edge,width,angle)

    with c.part('front_tail',(cx,153),key=('front_tail',)):
        # The tail recedes from the rump, then curves into view at floor level.
        tail = _curve([(cx-7,120),(cx-20,136),(cx-56,147),(cx-73,135),
                       (cx-85,126),(cx-81,113),(cx-79,112)])
        a,b = [],[]
        for j,p in enumerate(tail):
            f=j/(len(tail)-1)
            n=perp(unit(sub(tail[min(j+1,len(tail)-1)],tail[max(0,j-1)])))
            r=4.4*(1-f)**.85+.7
            a.append(add(p,mul(n,r))); b.append(add(p,mul(n,-r)))
        c.poly(a+b[::-1],TAIL,INK,1.6)
        c.line([mix(u,v,.28) for u,v in zip(a,b)],SKIN_LIGHT,1.2)
        for j in range(2,len(tail)-1,2):
            c.line([mix(a[j],b[j],.09),mix(a[j],b[j],.92)],SKIN_DARK,.85)

    with c.part('front_hind',(cx,153),key=('front_hind',)):
        # Hind legs recede behind the barrel. Their paws are visible outside
        # the forelimbs and at the higher, farther ground row.
        for s in (-1,1):
            shape([(20,104),(29,99),(39,112),(37,125),
                   (37,130),(33,134),(31,136),
                   (27,139),(21,135),(21,129),
                   (19,119),(15,112),(20,104)],FAR,FAR_INK,1.5,s)
            shape([(29,132),(36,132),(41,135),(41,139),
                   (40,142),(30,143),(25,141),
                   (24,138),(25,135),(29,132)],SKIN_DARK,FAR_INK,1.3,s)
            for k in (29,33,37):
                line([(k,138),(k+1,140)],SKIN,0.8,s)
                poly([(k,140),(k+2,140),(k+1,143)],TOOTH,FAR_INK,.65,s)

    with c.part('front_torso',(cx,153),key=('front_torso',)):
        # Arched rump and shoulders; the rounded haunches sit behind the head.
        shape([(0,62),(20,61),(34,75),(35,98),
               (38,116),(29,132),(13,135),
               (5,137),(-5,137),(-13,135),
               (-29,132),(-38,116),(-35,98),
               (-34,75),(-20,61),(0,62)],FUR,INK,2.4)
        shape([(-30,88),(-24,68),(-10,65),(0,66),
               (15,64),(26,74),(30,88),
               (14,81),(-12,81),(-30,88)],FUR_LIGHT,None)
        for s in (-1,1):
            for x,y in [(18,66),(25,73),(30,82),(33,94),(30,106)]:
                poly([(x-5,y+5),(x+1,y-2),(x+2,y+4),(x+6,y+8)],FUR_DARK,None,side=s)
            for x,y in [(23,83),(27,96),(28,109),(23,119)]:
                line([(x-3,y-4),(x+2,y+1)],FUR_DARK,1.1,s)
        shape([(-19,111),(-16,104),(16,104),(19,111),
               (21,123),(12,133),(0,134),
               (-12,133),(-21,123),(-19,111)],BELLY,None)

    with c.part('front_fore',(cx,153),key=('front_fore',)):
        # Forelegs: slender wrists and separate splayed toes, with their upper
        # roots lost in the chest. They are in front of the rear feet.
        for s in (-1,1):
            shape([(17,105),(24,109),(25,119),(22,127),
                   (20,133),(20,138),(21,143),
                   (18,145),(14,145),(13,141),
                   (11,134),(12,120),(12,115),
                   (13,110),(14,107),(17,105)],FUR,INK,1.5,s)
            line([(18,118),(16,128),(17,136)],FUR_LIGHT,1.2,s)
            shape([(15,140),(18,139),(22,140),(23,145),
                   (28,147),(28,151),(23,152),
                   (16,154),(9,152),(10,148),
                   (11,144),(13,142),(15,140)],SKIN,INK,1.3,s)
            for x in (13,17,21,25):
                line([(x,147),(x,150)],SKIN_DARK,.9,s)
                poly([(x-1,150),(x+1.7,150),(x+.4,153)],TOOTH,INK,.65,s)

    with c.part('front_ears',(cx,153),key=('front_ears',)):
        # Pinnae, one on each side of the skull. Both preserve the rat's small
        # ragged rim notch and interior folds. The roots hide behind its cheeks.
        for s in (-1,1):
            shape([(18,83),(11,77),(13,61),(19,54),
                   (27,47),(38,53),(38,62),
                   (34,61),(33,66),(38,67),
                   (38,80),(29,90),(18,83)],FUR,INK,1.8,s)
            shape([(20,80),(15,74),(18,59),(25,56),
                   (31,53),(34,59),(33,66),
                   (31,77),(25,82),(20,80)],SKIN,None,side=s)
            shape([(22,80),(19,74),(19,67),(23,63),
                   (21,70),(25,76),(29,77),
                   (27,81),(25,83),(22,80)],FUR_DARK,None,side=s)
            line([(19,61),(24,57),(29,58)],SKIN_LIGHT,1.1,s)

    with c.part('front_skull',(cx,153),key=('front_skull',)):
        # Head-on skull: broad crown and a long tapering rostrum. The nose is
        # projected low between the whisker pads, rather than a flat side nose.
        shape([(0,71),(13,70),(24,77),(25,88),
               (29,97),(24,106),(16,112),
               (11,116),(9,121),(0,122),
               (-9,121),(-11,116),(-16,112),
               (-24,106),(-29,97),(-25,88),
               (-24,77),(-13,70),(0,71)],FUR,INK,2.3)
        shape([(-20,83),(-14,75),(-7,74),(0,74),
               (7,74),(14,75),(20,83),
               (10,80),(5,83),(0,88),
               (-5,83),(-10,80),(-20,83)],FUR_LIGHT,None)
        for s in (-1,1):
            for x,y in [(23,95),(20,103),(15,110)]:
                poly([(x-4,y-2),(x+3,y+1),(x-1,y+3),(x-3,y+5),(x-5,y+1)],FUR_DARK,None,side=s)
            # Slanted amber eyes tucked under the angular dark brow.
            poly([(9,89),(22,83),(24,89),(20,95),(13,95)],'#36292b',INK,1.2,s)
            oval(s*17,89.5,3.9,3.7,EYE,None,angle=s*-12)
            oval(s*16.5,89.5,1.1,2.8,'#211d21',None)
            oval(s*16,88.2,1,1,'#f8e8c7',None)
            line([(8,87),(16,84),(23,82)],FUR_DARK,2.2,s)
    with c.part('front_muzzle',(cx,153),key=('front_muzzle',)):
        # Lower jaw and paired incisors beneath the tapered upper snout.
        shape([(-11,115),(-11,109),(11,109),(11,115),
               (13,121),(9,126),(0,126),
               (-9,126),(-13,121),(-11,115)],FUR_PALE,INK,1.6)
        for s in (-1,1):
            poly([(0.7,115),(5.4,114.5),(5,124),(1,124.6)],TOOTH,INK,.9,s)
        # Long central nose bridge, distinct bilateral pale whisker pads.
        shape([(0,84),(5,90),(8,99),(11,106),
               (12,111),(6,115),(0,116),
               (-6,115),(-12,111),(-11,106),
               (-8,99),(-5,90),(0,84)],FUR_LIGHT,None)
        for s in (-1,1):
            shape([(2,107),(7,101),(15,102),(18,108),
                   (19,112),(10,117),(4,116),
                   (1,115),(0,111),(2,107)],FUR_PALE,None,side=s)
            for x,y in [(7,108),(11,107),(10,112)]:
                oval(x*s,y,.8,.8,FUR_DARK,None)
            for path in [[(10,107),(25,102),(43,98)],[(12,110),(29,109),(47,111)],
                         [(10,113),(25,119),(42,127)],[(7,114),(18,125),(28,131)]]:
                line(path,'#62534b',1.0,s)
                line(path[:2],'#d0b9a1',.65,s)
        # The rounded, split nose projects over the muzzle and tooth roots.
        shape([(-8,109),(-6,104),(6,104),(8,109),
               (7,113),(2,115),(0,115),
               (-2,115),(-7,113),(-8,109)],SKIN_DARK,INK,1.4)
        oval(0,107,3.4,1.3,SKIN_LIGHT,None)
        line([(0,114),(0,117)],INK,1.0)
    return c.finish()



def _render_side_frame(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    cyc = math.tau*t
    gait = stride = lift = pitch = bob = stretch = crouch = rear = strike = hurt = dead = 0.0
    mouth = sniff = ears = bristle = 0.0
    lash = .32*math.sin(cyc)
    if anim == 'idle':
        bob = .8*math.sin(cyc)
        sniff = math.sin(3*cyc)
    elif anim in ('walk', 'run'):
        gait = 1.0 if anim == 'walk' else 2.0
        stride, lift = (23, 8) if gait == 1 else (36, 18)
        bob = -2*math.sin(cyc)**2 if gait == 1 else -7*math.sin(cyc)**2
        stretch = 2.5*math.sin(cyc) if gait == 1 else 8*math.sin(cyc)
        pitch = 2*math.cos(cyc) if gait == 1 else 5*math.cos(cyc)
        lash = .7*math.sin(cyc-.5)
        ears = -.15 if gait == 1 else -.45
        sniff = .35*math.sin(cyc)
    elif anim == 'notice':
        rear = track(t, [(0,0),(.4,1),(1,.72)])
        ears = rear
        pitch = -9*rear
        bob = -3*rear
        mouth = .13*rear
        sniff = .45*math.sin(cyc*3)
    elif anim == 'windup':
        crouch = .90+.10*math.sin(cyc)
        pitch = 4*crouch
        ears = -.8
        mouth = .48+.10*math.sin(cyc)
        bristle = 1.0
        lash = math.sin(cyc*2)
    elif anim == 'attack_side':
        strike = track(t, [(0,.85),(.12,1),(.25,.82),(.55,.32),(1,0)])
        stretch = 11*strike
        pitch = -5*strike
        bob = -5*strike
        ears = -.85*strike
        mouth = track(t, [(0,1),(.12,.92),(.25,0),(.4,.14),(1,0)])
        bristle = strike
        lash = .95*strike
    elif anim == 'hit':
        hurt = track(t, [(0,.70),(.2,1),(.65,.25),(1,0)])
        pitch = -11*hurt
        bob = -4*hurt
        mouth = .75*hurt
        ears = -hurt
        bristle = hurt
        lash = -hurt
    elif anim in ('death', 'death_idle'):
        dead = track(t, [(0,0),(.12,.18),(.4,.48),(.78,1),(1,1)]) if anim == 'death' else 1
        hurt = .6*math.sin(math.pi*min(1,t*2.2)) if anim == 'death' else 0
        pitch = -8*hurt + 4*dead
        mouth = track(t, [(0,.6),(.25,1),(.65,.58),(1,.38)]) if anim == 'death' else .38
        ears = -dead
        bristle = hurt
        lash = -.6*dead
    else:
        raise ValueError(anim)

    c = PartScene(sys.modules[__name__])
    origin = (139-7*crouch+10*strike-8*hurt-3*dead,
              102+bob+8*crouch+20*dead)

    def B(x,y):
        return add(origin, rot((x*(1+stretch*.009),y*(1-.23*crouch-.18*dead)), pitch))

    def body(pts, col, edge=INK, w=2):
        _shape(c,[B(x,y) for x,y in pts],col,edge,w)

    def bline(pts,col,w=1.2):
        c.line([B(x,y) for x,y in pts],col,w)

    def bpoly(pts,col,edge=INK,w=1.5):
        c.poly([B(x,y) for x,y in pts],col,edge,w)

    # Tail curvature is a small family of reusable authored shapes.
    tail_lash=round(lash*2)/2
    tail_dead=round(dead*2)/2
    tsx,tsy=1.,1.
    def T(x,y):
        return ((x+43)*tsx,(y-9)*tsy)
    with c.part('tail',key=('tail',tail_lash,tail_dead),at=B(-43,9),degrees=pitch):
        root = T(-43,9)
        end = T(-116,15-9*tail_lash+17*tail_dead)
        tail = _curve([root,T(-68,33),T(-102,36),T(-112,23),
                       T(-125,6-8*tail_lash+20*tail_dead),T(-114,2-10*tail_lash+22*tail_dead),end])
        left, right = [], []
        for j,p in enumerate(tail):
            f = j/(len(tail)-1)
            tangent = unit(sub(tail[min(j+1,len(tail)-1)],tail[max(j-1,0)]))
            rad = 4.8*(1-f)**.85 + .7
            normal = perp(tangent)
            left.append(add(p,mul(normal,rad)))
            right.append(add(p,mul(normal,-rad)))
        c.poly(left+right[::-1],TAIL,INK,1.6)
        c.line([mix(a,b,.28) for a,b in zip(left,right)],SKIN_LIGHT,1.2)
        for j in range(2,len(tail)-1,2):
            c.line([mix(left[j],right[j],.09),mix(left[j],right[j],.92)],SKIN_DARK,.85)

    # Each foot has its own projected ground point. The two far legs are
    # painted before the torso. Each near leg is painted as a complete chain.
    def leg(front, near):
        col, shade, edge = (FUR,FUR_LIGHT,INK) if near else (FAR,FAR_LIGHT,FAR_INK)
        skin, skinlight = (SKIN,SKIN_LIGHT) if near else (SKIN_DARK,SKIN)
        top = B(29 if front else -27, 11 if front else 7)
        fx = (171 if front else 112) if near else (189 if front else 92)
        gy = GROUND if near else GROUND-10
        fy = gy-4
        if gait:
            offset = (0 if front else .55) + (0 if near else (.43 if gait==1 else .16))
            gx,dy = _gait(t+offset,stride,lift,.60 if gait==1 else .46)
            fx += gx
            fy += dy
        if rear and front:
            fx += 4*rear if near else 9*rear
            fy -= (15 if near else 22)*rear
        if strike:
            fx += (22 if front else -12)*strike
            fy -= (16 if front else 6)*strike
        if hurt:
            fx -= 8*hurt
            fy -= (7 if front else 3)*hurt
        if dead:
            target = ((203 if front else 137) if near else (185 if front else 107),gy-4)
            fx,fy = mix((fx,fy),target,dead)
            fy = min(fy,gy-4)
        foot = (fx,fy)
        # The hind thigh joins the rump with a broad root. The foreleg
        # has a slimmer shoulder and an elbow that bends behind the wrist.
        if front:
            knee = add(mix(top,foot,.43),(-10+3*strike,0))
            ankle = mix(knee,foot,.84)
            radii=(8.5 if near else 6.2,4.8,2.7)
        else:
            knee = add(mix(top,foot,.47),(13-3*dead,-3))
            ankle = add(mix(knee,foot,.70),(-9,-1))
            radii=(12.5 if near else 10,8.2 if near else 5.4,3.2)
        track_name=('near' if near else 'far')+('_fore' if front else '_hind')
        with c.part(track_name+'_paw',key=('paw',near),at=foot):
            # Broad bare paw, four short toes. Draw claws after the paw.
            x,y = 0.,0.
            paw = [(x-5,y-3),(x+1,y-4),(x+8,y-3),(x+12,y),(x+9,y+3),
                   (x-5,y+3),(x-7,y+1)]
            c.poly(paw,skin,edge,1.4)
            for k in range(3):
                px,py = x+5+k*2.4,y+.3+k*.3
                c.line([(px-2,py-1.3),(px,py+.9)],SKIN_DARK,.8)
                c.poly([(px,py),(px+3.1,py+.9),(px,py+1.5)],TOOTH,edge,.65)
        limb_segment(c,track_name+'_wrist',ankle,foot,2.8,2.1,skin,skinlight,edge)
        limb_segment(c,track_name+'_lower',knee,ankle,radii[1],radii[2],col,shade,edge)
        limb_segment(c,track_name+'_upper',top,knee,radii[0],radii[1],col,shade,edge)

    leg(False,False)
    leg(True,False)

    world_B=B
    torso_sx=1.+round(stretch/4)*4*.009
    torso_sy=1.-round((.23*crouch+.18*dead)*8)/8
    bristle_variant=round(bristle*3)/3
    def B(x,y):
        return (x*torso_sx,y*torso_sy)
    with c.part('torso',key=('torso',torso_sx,torso_sy,bristle_variant),at=origin,degrees=pitch):
        # The arched back and heavy haunches form the main silhouette. The
        # shoulder is lower than the rump; short tufts follow the back contour.
        body([(-48,8),(-60,-9),(-49,-31),(-30,-34),
              (-12,-38),(1,-24),(13,-22),
              (24,-21),(38,-25),(46,-8),
              (55,6),(36,22),(20,27),
              (1,32),(-10,29),(-24,29),
              (-40,29),(-48,24),(-48,8)],FUR,INK,2.5)
        body([(-47,-7),(-46,-26),(-35,-32),(-22,-30),
              (-10,-29),(-1,-21),(11,-17),
              (22,-14),(30,-19),(37,-13),
              (20,-8),(1,-12),(-10,-16),
              (-28,-18),(-37,-13),(-47,-7)],FUR_LIGHT,None)
        body([(-43,12),(-38,23),(-28,27),(-18,27),
              (0,30),(21,26),(31,20),
              (37,16),(43,9),(44,4),
              (28,17),(11,17),(-2,17),
              (-20,20),(-34,14),(-43,12)],BELLY,None)
        # Darker irregular guard hairs along the spine. They follow the body
        # transform. No random geometry changes between frames.
        for j,(x,y) in enumerate([(-44,-22),(-35,-31),(-25,-33),(-15,-32),(-5,-27),(5,-24),(15,-22),(25,-23),(33,-20)]):
            h = (4.0 if j%2 else 3.1)+5.8*bristle_variant
            bpoly([(x-5,y+3),(x-3,y-h),(x+1,y-1),(x+5,y+3)],FUR_DARK,None)
        for x,y,ang in [(-39,-13,25),(-30,-19,35),(-23,-13,25),(-11,-16,30),(1,-13,35),(15,-14,26),
                        (-36,3,30),(-23,5,21),(-9,7,24),(9,2,25),(21,9,31)]:
            end = add((x,y),rot((7,0),ang))
            bline([(x,y),end],FUR_DARK if y<0 else FUR_LIGHT,1.25)
    B=world_B
    leg(False,True)
    leg(True,True)

    # The face has its own pivot at the neck. The long snout and cheek
    # move together. The jaw opens about the cheek instead of scaling.
    headroot = B(34,-12)
    ha = pitch-12*rear+9*crouch-4*strike-8*hurt+23*dead+2*sniff
    def HW(x,y):
        return add(headroot,rot((x*1.0,y*1.0),ha))
    def H(x,y):
        return (x*1.0,y*1.0)
    def hshape(pts,col,edge=INK,w=1.8):
        _shape(c,[H(x,y) for x,y in pts],col,edge,w)
    def hpoly(pts,col,edge=INK,w=1.5):
        c.poly([H(x,y) for x,y in pts],col,edge,w)
    def hline(pts,col,w=1.2):
        c.line([H(x,y) for x,y in pts],col,w)
    def hov(x,y,rx,ry,col,edge=INK,w=1.4,angle=0):
        c.oval(H(x,y),rx,ry,col,edge,w,angle)

    def ear(far):
        # The round ear folds back in the windup. A notch interrupts the rim.
        ctr = (-3,-21) if far else (-15,-14)
        ang = -18-24*ears-54*dead if far else -26-24*ears-60*dead
        def E(x,y):
            return (x*1.0,y*1.0)
        scl = .78 if far else 1.0
        def epts(seq):
            return [E(x*scl,y*scl) for x,y in seq]
        with c.part(('far' if far else 'near')+'_ear',key=('ear',far),at=HW(*ctr),degrees=ha+ang):
            _shape(c,epts([(-8,9),(-16,-5),(-14,-18),(-5,-21),
                           (6,-24),(15,-15),(14,-9),
                           (9,-10),(10,-4),(13,-3),
                           (11,5),(1,12),(-8,9)]),FAR if far else FUR,FAR_INK if far else INK,1.8)
            _shape(c,epts([(-6,6),(-12,-4),(-9,-16),(-2,-17),
                           (6,-19),(10,-10),(8,-4),
                           (7,2),(1,7),(-6,6)]),SKIN_DARK if far else SKIN,None)
            _shape(c,epts([(-4,6),(-7,-1),(-4,-7),(1,-10),
                           (-1,-2),(2,2),(4,4),
                           (1,7),(-1,8),(-4,6)]),FUR_DARK,None)
    ear(True)

    # Rotate the lower jaw and teeth as a rigid anatomical part.
    jaw_hinge=(9,12)
    def J(x,y):
        return ((x-9)*1.0,(y-12)*1.0)
    with c.part('jaw',key=('jaw',mouth>.05),at=HW(*jaw_hinge),degrees=ha+29*mouth):
        _shape(c,[J(x,y) for x,y in [(5,9),(17,7),(33,12),(48,10),
                  (50,14),(46,17),(36,18),(19,23),(10,21),(5,9)]],FUR_PALE,INK,1.8)
        if mouth>.05:
            c.poly([J(38,13),J(43,11),J(46,7),J(47,14),J(44,15)],TOOTH,INK,1.1)
    # A separate mouth interior lies between the jaw and the skull.
    mouth_real=mouth
    mouth=round(mouth*5)/5
    with c.part('mouth_interior',key=('mouth',mouth),at=headroot,degrees=ha):
        if mouth>.05:
            hpoly([(7,10),(27,4),(49,6),(41,12+12*mouth),(16,17+4*mouth)],'#39242a',None)
    mouth=mouth_real
    with c.part('skull',key=('skull',),at=headroot,degrees=ha):
        # Upper skull and pointed muzzle. Its short, broken contour makes the
        # cheek read as coarse fur, not a smooth cartoon mouse.
        hshape([(-18,-14),(-11,-25),(5,-28),(16,-20),
                (27,-15),(30,-7),(43,-3),
                (49,-1),(56,0),(57,6),
                (55,11),(44,10),(35,12),
                (24,14),(14,19),(1,18),
                (-12,15),(-23,3),(-18,-14)],FUR,INK,2.3)
        hshape([(-13,-13),(-5,-22),(9,-23),(17,-17),
                (29,-11),(33,-6),(44,-3),
                (32,-3),(20,-7),(13,-12),
                (4,-16),(-5,-15),(-13,-13)],FUR_LIGHT,None)
        hshape([(6,7),(16,0),(30,0),(42,2),
                (48,3),(52,5),(51,8),
                (41,10),(30,11),(20,14),
                (12,16),(7,12),(6,7)],FUR_PALE,None)
        # Ear and its root sit in front of the skull, behind the eye and muzzle.
    ear(False)
    rear_variant=round(rear*3)/3
    with c.part('face',key=('face',dead>.65,hurt>.3,rear_variant,mouth>.35),at=headroot,degrees=ha):
        for x,y in [(-19,3),(-14,8),(-9,12)]:
            hpoly([(x+3,y-4),(x-4,y),(x+1,y+2),(x-2,y+5),(x+6,y+3)],FUR_DARK,None)

        if dead>.65:
            hline([(9,-10),(14,-7),(19,-10)],INK,2.2)
        elif hurt>.3:
            hline([(8,-12),(14,-8),(20,-12)],INK,2.5)
        else:
            wide = 1.0+1.8*rear_variant
            hpoly([(8,-13-wide),(20,-10-wide),(19,-5+wide),(11,-5+wide)],'#36292b',INK,1.2)
            hov(15,-9,3.6,3.5+wide*.3,EYE,None)
            hov(16,-9,.95,2.7,'#211d21',None)
            hov(14,-10,1.0,1.1,'#f8e8c7',None)
            hline([(6,-15-wide),(12,-15-wide),(21,-11-wide)],FUR_DARK,2.5)
        # Upper incisors lie on the outside edge of the upper jaw. Their base
        # stays fixed when the lower jaw rotates.
        hpoly([(44,8),(49,8),(47,17),(43,16)],TOOTH,INK,1.0)
        hpoly([(49,8),(52,7),(51,15),(47,16)],'#d5be96',INK,.9)
        hov(53,3,5.2,4.0,SKIN_DARK,INK,1.4,-12)
        hov(54,1,2.1,1.1,SKIN_LIGHT,None)
        for x,y in [(35,3),(39,5),(33,7)]:
            hov(x,y,.85,.85,FUR_DARK,None)
        # Whiskers follow the muzzle and stay behind the nose tip.
        for pts in [[(37,3),(51,-5),(66,-9)],[(39,5),(54,2),(68,4)],
                    [(36,7),(50,10),(63,16)],[(33,8),(44,16),(55,22)]]:
            hline(pts,'#62534b',1.0)
            hline(pts[:2],'#d0b9a1',.65)
    return c.finish(ground_lock=anim in ('death','death_idle'))


def _quarter_frame():
    return quarter_frame(sys.modules[__name__])


def _reflect(frame):
    return reflect(sys.modules[__name__],frame)


def _render_frame(anim,i,n):
    if anim=='turnaround':
        assert n==5
        if i==2:
            return _front_frame()
        im=_quarter_frame() if i in (1,3) else _render_side_frame('idle',0,16)
        return _reflect(im) if i<2 else im
    return _render_side_frame(anim,i,n)


def render(out_dir: str | Path, **opts):
    del opts
    out_dir=Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    transform={}
    out=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,
        out_dir=out_dir,frame_size=FRAME_SIZE,auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=lambda w,h:body_metrics_for_box(BODY_BOX,w,h),
        animation_key_map={name:name for name,_,_ in ROWS},
        pose_bodies='authored',sits_on_ground=True,parts=True,frame_transform_out=transform)
    parts=publish_rig_flipbook(TARGET_NAME,ROWS,_render_frame,out,transform,out_dir)
    return [out[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent') if out.get(k)] + list(parts.values())
