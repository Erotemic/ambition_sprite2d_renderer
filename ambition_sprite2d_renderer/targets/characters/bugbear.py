"""Bugbear: shaggy woodland goblinoid with a heavy knotted club.

Pose goals are authored in sprite pixels. Existing surface_gait and skeleton
solvers handle feet and limbs; gear is attached to the *solved* wrist.
The animation shows an overhead tell, a forward club blow, and recovery.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from pathlib import Path

from PIL import Image
from ._clockwork_enemy_art import Canvas, add, sub, mul, mix, rot, phase, track, unit, perp, bezier
from ...authoring.skeleton import two_bone_ik_points
from ...authoring.surface_gait import Gait
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'bugbear'
DISPLAY_NAME = 'Bugbear'
FRAME_SIZE = (352, 280)
CX, GROUND = 145., 250.
ARM_LENGTHS = (42., 41.)
LEG_LENGTHS = (34., 34.)
WINDUP_S, ACTIVE_S, RECOVER_S = .65, .20, .80
ROWS = [('idle', 8, 140), ('walk', 12, 105), ('run', 12, 85),
        ('notice', 6, 90), ('windup', 13, 50), ('attack_side', 20, 50),
        ('hit', 6, 85), ('death', 14, 85), ('death_idle', 6, 200)]
LOOPS = {'idle', 'walk', 'run', 'death_idle'}
TRAITS = ['enemy', 'fantasy', 'monster', 'goblinoid', 'heavy', 'woodland']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': DISPLAY_NAME},
    'body': {'body_plan': 'Biped', 'body_kind': 'Standard', 'mass_class': 'Heavy',
             'locomotion_hint': 'Walk', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'actions': {'default_preset': 'bugbear_club'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': 0., 'event': 'hitbox_active_start', 'source': 'bugbear.club'},
            {'t': ACTIVE_S/(ACTIVE_S+RECOVER_S), 'event': 'hitbox_active_end', 'source': 'bugbear.club'}]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': 'A broad, shaggy woodland goblinoid, with pointed ears, a blunt black muzzle, tusks, patchwork leather and a knotted wooden club.',
    'gameplay_description': 'A heavy wandering melee monster that lifts its club overhead before a powerful strike. Vulnerable while recovering.',
}

INK = '#302520'
FUR = '#815b40'
FUR_L = '#b58b59'
FUR_D = '#543c30'
FAR = '#49352d'
FAR_L = '#77543d'
MANE = '#44312a'
SKIN = '#ad8c67'
SKIN_L = '#d3b087'
SKIN_D = '#765744'
NOSE = '#31282a'
MOUTH = '#38252a'
IVORY = '#f3e4bd'
EYE = '#f1c35f'
LEATHER = '#514a36'
LEATHER_L = '#82704e'
LEATHER_D = '#37372d'
CLOTH = '#49665e'
CLOTH_L = '#7d9580'
CLOTH_D = '#30463f'
METAL = '#a69b79'
WOOD = '#78503a'
WOOD_L = '#b38659'
WOOD_D = '#4b342a'
WRAP = '#b7a078'


@dataclass(frozen=True)
class Pose:
    hip: tuple = (CX, GROUND-65.)
    lean: float = 15.
    head: float = -5.
    jaw: float = 0.
    near_foot: tuple = (CX+14, GROUND-8)
    far_foot: tuple = (CX-15, GROUND-8)
    near_hand: tuple = (CX+42, GROUND-66)
    far_hand: tuple = (CX-42, GROUND-54)
    club: float = 35.
    rag: float = 0.
    recoil: float = 0.
    eye: float = 1.


IDLE = Pose()
READY = replace(IDLE, hip=(CX-6,GROUND-61), lean=-9, head=-8, jaw=3,
                near_hand=(CX-34,GROUND-158), far_hand=(CX+32,GROUND-93),
                club=-153, near_foot=(CX+17,GROUND-8), far_foot=(CX-19,GROUND-8), rag=-4)
STRIKE = replace(IDLE, hip=(CX+7,GROUND-61), lean=28, head=11, jaw=8,
                 near_hand=(CX+71,GROUND-79), far_hand=(CX-5,GROUND-60),
                 club=12, near_foot=(CX+28,GROUND-8), far_foot=(CX-19,GROUND-8), rag=5)
SPENT = replace(STRIKE, lean=35, head=17, jaw=3, near_hand=(CX+53,GROUND-53), club=22, rag=7)
WALK = Gait(stride=40, stance=.62, lift=9)
RUN = Gait(stride=52, stance=.58, lift=14)


def _keys(t, keys):
    for (lo,a),(hi,b) in zip(keys,keys[1:]):
        if t <= hi:
            u=track(t,[(lo,0),(hi,1)])
            return Pose(**{k: mix(getattr(a,k),getattr(b,k),u) if isinstance(getattr(a,k),tuple)
                           else getattr(a,k)+(getattr(b,k)-getattr(a,k))*u for k in Pose.__dataclass_fields__})
    return keys[-1][1]


def pose(anim,i,n):
    t=phase(i,n,anim in LOOPS)
    s=math.sin(math.tau*t)
    if anim=='idle':
        return replace(IDLE,hip=(CX,GROUND-65+1.2*s),head=-5+1.5*s,rag=s)
    if anim in ('walk','run'):
        gait=WALK if anim=='walk' else RUN
        nx,ny=gait.foot_offset(t,0.); fx,fy=gait.foot_offset(t,.5)
        return replace(IDLE,hip=(CX,GROUND-64+1.6*math.cos(2*math.tau*t)),
                       lean=15 if anim=='walk' else 20,head=-4+3*s,
                       near_foot=(CX+8+nx,GROUND-8-ny),far_foot=(CX-8+fx,GROUND-8-fy),
                       near_hand=(CX+42-11*s,GROUND-67+3*s),far_hand=(CX-38+22*s,GROUND-56+4*s),
                       club=35-9*s,rag=3*s)
    if anim=='notice':
        alert=replace(IDLE,lean=3,head=-14,jaw=4,near_hand=(CX+40,GROUND-91),club=10)
        return _keys(t,[(0,IDLE),(.45,alert),(1,alert)])
    if anim=='windup':
        return _keys(t,[(0,IDLE),(.62,READY),(1,READY)])
    if anim=='attack_side':
        apex=replace(READY,hip=(CX+1,GROUND-62),lean=4,head=-5,
                     near_hand=(CX+37,GROUND-146),club=-67,rag=-2)
        return _keys(t,[(0,READY),(.053,apex),(.105,STRIKE),(.20,STRIKE),
                        (.37,SPENT),(.62,SPENT),(1,IDLE)])
    if anim=='hit':
        h=replace(IDLE,hip=(CX-6,GROUND-62),lean=-11,head=-23,jaw=5,
                  near_hand=(CX+24,GROUND-81),far_hand=(CX-33,GROUND-90),club=60,recoil=1,eye=.5)
        return _keys(t,[(0,IDLE),(.24,h),(.48,h),(1,IDLE)])
    if anim in ('death','death_idle'):
        return replace(IDLE,eye=0,jaw=3)
    raise ValueError(anim)


def solve(p):
    def T(x,y): return add(p.hip,rot((x,y),p.lean))
    def limb(root,goal,lengths,bend):
        return (root,*two_bone_ik_points(root,goal,*lengths,bend,extension_margin=.1))
    return dict(near_leg=limb(T(12,0),p.near_foot,LEG_LENGTHS,1.),
                far_leg=limb(T(-12,0),p.far_foot,LEG_LENGTHS,1.),
                near_arm=limb(T(3,-65),p.near_hand,ARM_LENGTHS,-1.),
                far_arm=limb(T(-19,-64),p.far_hand,ARM_LENGTHS,-1.),
                head=T(31,-81))


def _curve(c, start, segments, fill, edge=INK, width=1.7):
    """Draw a closed art contour from the existing cubic Bezier sampler."""
    pts=[start]
    for a,b,end in segments:
        pts.extend(bezier(pts[-1],a,b,end,n=10)[1:])
    c.poly(pts,fill,edge,width)


def _fur_chain(c, joints, radii, far=False):
    """Paint a continuous limb, without rings at its IK joints."""
    a,b,d=joints
    r0,r1,r2=radii
    u=unit(sub(b,a)); w=unit(sub(d,b)); n=perp(u); m=perp(w)
    # The joint tangent blends the two solved segment directions. This is
    # a drawing contour only; it never changes the solved joint positions.
    j=unit(add(n,m)) if math.hypot(*add(n,m))>.05 else n
    base,light,shade=(FAR,FAR_L,MANE) if far else (FUR,FUR_L,FUR_D)
    def off(p,v,r):return add(p,mul(v,r))
    left0,left1,left2=off(a,n,-r0),off(b,j,-r1),off(d,m,-r2)
    right0,right1,right2=off(a,n,r0),off(b,j,r1),off(d,m,r2)
    # Smooth shoulder and elbow on the lit edge; the other edge has three
    # pointed, downward-facing locks of fur instead of a geometric seam.
    pts=bezier(left0,add(left0,mul(u,13)),add(left1,mul(u,-9)),left1,n=12)
    pts+=bezier(left1,add(left1,mul(w,10)),add(left2,mul(w,-9)),left2,n=12)[1:]
    pts += [off(add(d,mul(w,3)),m,-r2*.6),off(add(d,mul(w,3)),m,r2*.6),right2]
    for lo,hi,normal,rlo,rhi in ((d,b,m,r2,r1),(b,a,n,r1,r0)):
        for t,f in ((.15,1),(.29,1.22),(.38,.98),(.58,1),(.73,1.18),(.82,.99)):
            pts.append(off(mix(lo,hi,t),normal,(rlo+(rhi-rlo)*t)*f))
        pts.append(right1 if lo==d else right0)
    pts+=bezier(right0,add(right0,mul(u,-10)),add(left0,mul(u,-10)),left0,n=10)[1:]
    c.poly(pts,base,INK,1.8)
    # A broad light plane follows the chain, leaving the outline unbroken.
    c.poly([off(a,n,-r0*.68),off(mix(a,b,.42),n,-r0*.75),off(b,j,-r1*.67),
            off(mix(b,d,.65),m,-r2*.77),off(d,m,-r2*.43),off(b,j,-r1*.18),
            off(mix(a,b,.38),n,-r0*.12)],light,None)
    c.poly([off(mix(a,b,.17),n,r0*.48),off(b,j,r1*.64),off(mix(b,d,.8),m,r2*.55),
            right2,right1,right0],shade,None)
    # Short overlapping locks, not circumferential armor stripes.
    for lo,hi,normal,r in ((a,b,n,r0),(b,d,m,r1)):
        for t,side in ((.25,-.25),(.48,.35),(.74,-.4)):
            p=off(mix(lo,hi,t),normal,r*side)
            q=off(mix(lo,hi,min(1,t+.17)),normal,r*(side+.15))
            c.line([p,q,off(mix(lo,hi,min(1,t+.26)),normal,r*(side+.03))],shade,1.25)


def _foot(c,ankle,far):
    col=FAR if far else FUR
    light=FAR_L if far else FUR_L
    def q(x,y):return add(ankle,(x,y))
    c.poly([q(-12,-7),q(-6,-11),q(6,-9),q(13,-5),q(19,-2),q(23,2),
            q(20,6),q(-12,6),q(-16,2)],col,INK,1.7)
    c.poly([q(-10,-6),q(1,-7),q(11,-3),q(8,0),q(-9,-1)],light,None)
    for x in (11,17,22):
        c.poly([q(x-4,0),q(x+1,1),q(x+2,5),q(x-3,5)],IVORY,INK,.8)
    c.line([q(-11,3),q(5,4)],FUR_D,1.3)


def _leg(c,j,far):
    _fur_chain(c,j,(17,12,8.8),far)
    _foot(c,j[-1],far)


def _arm(c,j,far,angle=85,grip=False):
    a,e,w=j
    _fur_chain(c,j,(21,13,9.5),far)
    if not far:
        u=unit(sub(w,e));v=perp(u)
        for t in (.64,.77,.90):
            b=mix(e,w,t)
            c.poly([add(b,mul(v,-10)),add(add(b,mul(u,5)),mul(v,-9)),
                    add(add(b,mul(u,5)),mul(v,9)),add(b,mul(v,10))],WRAP,LEATHER_D,.9)
    col=SKIN_D if far else SKIN
    def q(x,y):return add(w,rot((x,y),angle))
    c.oval(w,11,9,col,INK,1.6,angle)
    if grip:
        for x in (-5,-1,3,7):
            c.line([q(x,-6),q(x,4)],SKIN_D,1.4)
            c.line([q(x-1,-5),q(x-1,0)],SKIN_L,1.)
        c.oval(q(4,-6),5,4,col,INK,1.,angle)
    else:
        for y in (-6,-2,2,6):
            c.line([q(4,y),q(12,y+1)],INK,5.4)
            c.line([q(4,y),q(11,y+1)],col,3.5)
            c.poly([q(10,y-.6),q(16,y+1),q(11,y+2.2)],IVORY,INK,.75)


def _club(c,w,angle):
    def q(x,y):return add(w,rot((x,y),angle))
    def P(pts,color,edge=INK,width=1.4):c.poly([q(*v) for v in pts],color,edge,width)
    def L(pts,color,width=1.6):c.line([q(*v) for v in pts],color,width)
    # Rough rootwood cudgel, a compact handle and an enlarged, gnarled head.
    P([(-11,-5),(18,-6),(34,-10),(43,-17),(56,-14),(66,-18),(81,-12),
       (88,-3),(84,10),(72,17),(58,15),(43,12),(29,8),(16,5),(-11,5)],WOOD,INK,2.2)
    P([(20,1),(36,2),(50,6),(63,8),(79,6),(84,10),(72,17),(58,15),(43,12),(29,8)],WOOD_D,None)
    P([(30,-7),(44,-13),(53,-11),(66,-14),(79,-9),(82,-5),(65,-8),(48,-5)],WOOD_L,None)
    for pts in ([(19,-2),(34,-4),(46,-3),(57,0),(68,-2),(80,-1)],
                [(39,3),(49,6),(61,3),(73,6)],[(53,-11),(57,-7),(65,-5)]):L(pts,WOOD_D,1.7)
    c.oval(q(65,-4),9,5,WOOD_D,INK,1.,angle)
    c.oval(q(65,-4),5,2.7,WOOD_L,None,0,angle)
    for x in (-8,-3,2,7,12):L([(x,-5),(x+5,5)],WRAP,2.1)
    # A weathered iron band reinforces the split head, not a spiked mace.
    P([(36,-10),(41,-15),(47,-15),(43,12),(37,10)],METAL,INK,1.25)
    L([(42,-12),(38,9)],'#d1bf93',1.3)
    c.disk(q(41,-2),2.2,LEATHER_D,INK,.7)


def _head(c,center,angle,jaw,eye):
    def q(x,y):return add(center,rot((x,y),angle))
    def poly(pts,col,edge=INK,w=1.7):c.poly([q(*p) for p in pts],col,edge,w)
    def line(pts,col,w=1.5):c.line([q(*p) for p in pts],col,w)
    def oval(x,y,rx,ry,col,edge=INK,w=1.2):c.oval(q(x,y),rx,ry,col,edge,w,angle)
    def curve(start,segments,col,edge=INK,w=1.7):
        _curve(c,q(*start),[(q(*a),q(*b),q(*end)) for a,b,end in segments],col,edge,w)
    # Broad, low goblinoid head with pointed side ears, heavy brow and
    # a short bear-like muzzle. Avoid a tall domestic-dog profile.
    poly([(-7,-20),(-12,-33),(-27,-39),(-25,-23),(-18,-13)],FUR_D)
    poly([(-17,-28),(-23,-34),(-22,-22),(-17,-19)],SKIN_D,None)
    curve((-28,-13),[((-29,-29),(-10,-34),(5,-31)),((19,-33),(28,-22),(30,-12)),
                     ((30,-7),(35,-4),(36,5)),((37,18),(24,28),(10,28)),
                     ((-3,32),(-24,25),(-28,14)),((-37,5),(-36,-6),(-28,-13))],FUR)
    # A jagged ruff frames the face and overlaps the back of the jaw.
    poly([(-25,-23),(-12,-31),(1,-33),(-1,-27),(11,-29),(6,-22),(-4,-18),
          (-13,-15),(-15,-4),(-11,7),(-2,14),(6,23),(2,35),(-6,29),
          (-13,36),(-17,25),(-26,30),(-25,17),(-36,21),(-32,7),(-40,9),(-34,-5),(-38,-12)],MANE)
    poly([(-27,-22),(-16,-29),(-5,-28),(-12,-22),(-21,-16),(-27,-5),(-29,4),(-34,6),(-32,-10)],FUR_L,None)
    # Near ear: ragged outer rim, inner skin, one nick.
    poly([(-17,-10),(-30,-24),(-45,-26),(-40,-15),(-42,-12),(-32,-4),(-18,2)],FUR)
    poly([(-22,-9),(-37,-22),(-35,-13),(-27,-5)],SKIN_D,None)
    line([(-41,-23),(-31,-17),(-21,-11)],FUR_L,1.9)
    # Forehead, cheek, low brow. Distinct eye whites and pupils read small.
    curve((-6,-23),[((3,-29),(21,-27),(26,-15)),((26,-9),(20,-5),(14,-1)),
                    ((6,5),(-2,2),(-9,-7)),((-10,-15),(-10,-18),(-6,-23))],FUR_L,None)
    poly([(3,-17),(13,-20),(24,-15),(28,-8),(22,-2),(10,0),(1,-7)],SKIN_D,None)
    oval(13,-9,7.2,4.6,NOSE,None)
    oval(28,-9,3.4,3.2,NOSE,None)
    if eye>.05:
        oval(14,-9,4.4,2.4*eye,EYE,None)
        oval(16,-9,1.6,2.2*eye,NOSE,None)
        oval(29,-9,1.7,1.65*eye,EYE,None)
        oval(13,-10,.9,.8,IVORY,None)
    poly([(-1,-14),(8,-21),(19,-20),(27,-14),(24,-9),(15,-12),(6,-9),(0,-7)],MANE)
    # Lower jaw, mouth cavity, muzzle and broad flattened nose.
    poly([(4,9),(17,9),(35,10),(34,21+jaw),(23,29+jaw),(9,28+jaw),(-1,19+jaw)],MOUTH)
    curve((-1,17+jaw),[((4,19+jaw),(7,23+jaw),(16,24+jaw)),
                        ((24,24+jaw),(31,21+jaw),(35,17+jaw)),
                        ((34,27+jaw),(27,34+jaw),(17,34+jaw)),
                        ((6,34+jaw),(-2,28+jaw),(-1,17+jaw))],SKIN_D)
    curve((6,1),[((15,-4),(28,-4),(36,0)),((42,3),(42,9),(37,13)),
                 ((31,17),(22,17),(16,14)),((7,16),(0,11),(6,1))],SKIN)
    curve((9,1),[((18,-2),(30,-2),(36,2)),((34,7),(28,8),(21,7)),
                 ((15,7),(8,9),(9,1))],SKIN_L,None)
    poly([(30,-3),(38,-3),(43,2),(42,8),(37,11),(30,8),(27,3)],NOSE)
    line([(32,0),(38,1)],'#795e51',1.8)
    line([(39,9),(36,12),(26,13)],MOUTH,1.5)
    # Upturned lower canines and a small, broken row of upper teeth.
    for x,h in ((10,12),(28,10)):
        poly([(x-2,24+jaw),(x-3,13+jaw*.35),(x+1,15+jaw*.6),
              (x+4,23+jaw),(x+2,26+jaw)],IVORY,INK,.9)
    for x in (18,23):poly([(x,14),(x+4,14),(x+3,19),(x+1,18)],IVORY,None)
    for pts in ([(-23,-7),(-17,-2),(-16,5)],[(-22,7),(-12,13),(-11,18)],
                [(-12,-24),(-5,-22),(-1,-20)],[(-5,3),(0,7),(2,11)]):line(pts,FUR_L,1.65)
    for x,y in ((20,8),(24,10),(29,8)):oval(x,y,.8,.8,SKIN_D,None)


def _body(c,p):
    def q(x,y):return add(p.hip,rot((x,y),p.lean))
    def poly(pts,col,edge=INK,w=1.7):c.poly([q(*a) for a in pts],col,edge,w)
    def line(pts,col,w=1.5):c.line([q(*a) for a in pts],col,w)
    def curve(start,segments,col,edge=INK,w=1.8):
        _curve(c,q(*start),[(q(*a),q(*b),q(*end)) for a,b,end in segments],col,edge,w)
    # The rounded humped back and belly establish the weight; separate
    # clumps of hair hang off the silhouette, not polygonal muscle plates.
    curve((-40,-46),[((-44,-68),(-27,-90),(-7,-92)),((17,-96),(37,-82),(40,-62)),
                    ((46,-42),(37,-25),(26,-14)),((28,0),(16,10),(0,9)),
                    ((-18,13),(-32,5),(-34,-15)),((-39,-25),(-47,-33),(-40,-46))],FUR)
    poly([(-37,-65),(-29,-80),(-18,-88),(-8,-91),(7,-92),(24,-86),(33,-77),
          (21,-80),(15,-76),(7,-79),(1,-72),(-7,-75),(-14,-66),(-19,-69),(-25,-54),(-34,-57)],FUR_L,None)
    poly([(-42,-48),(-36,-57),(-34,-43),(-30,-39),(-35,-29),(-29,-30),(-26,-18),
          (-20,-19),(-15,-7),(-8,-3),(-16,8),(-25,10),(-27,1),(-36,6),(-34,-8),
          (-42,-11),(-38,-21),(-47,-24),(-43,-36),(-48,-40)],MANE)
    # A warm chest bib, a recessed belly and a few broad locks of fur.
    curve((8,-71),[((23,-75),(40,-60),(37,-46)),((39,-31),(27,-20),(16,-17)),
                   ((0,-16),(-9,-27),(-8,-41)),((-8,-53),(-1,-67),(8,-71))],FUR_L,None)
    poly([(-8,-45),(-4,-36),(6,-31),(10,-33),(18,-27),(27,-31),(26,-20),
          (14,-12),(0,-18),(-7,-29)],FUR,None)
    for x,y in ((-25,-68),(-16,-57),(-24,-43),(-17,-30),(2,-64),(20,-57),(15,-39),(-8,-10)):
        line([(x-4,y-3),(x,y+2),(x+6,y+4)],FUR_D,1.6)
    # Worn cross-body leather harness with a bone toggle and a single
    # shoulder hide flap. Asymmetry distinguishes it from an armored brute.
    poly([(-27,-80),(-15,-82),(27,-9),(17,-4)],LEATHER_D)
    poly([(-25,-79),(-19,-80),(23,-10),(19,-8)],LEATHER_L,None)
    for x,y in ((-17,-66),(-9,-51),(1,-35),(12,-19)):
        line([(x-3,y+2),(x+2,y-1)],WRAP,1.35)
    poly([(-37,-72),(-27,-86),(-15,-85),(-10,-72),(-19,-60),(-25,-65),
          (-29,-56),(-37,-61)],LEATHER,INK,1.8)
    line([(-35,-70),(-27,-81),(-17,-81)],LEATHER_L,2.)
    c.disk(q(-17,-74),3.8,METAL,INK,1.)
    # Layered loincloth and a broad belt. Legs sit behind this garment.
    poly([(-29,-6),(25,-6),(30,17),(20,13),(14,35+p.rag),(4,25),(-4,34),
          (-13,21),(-22,27-p.rag),(-30,15)],CLOTH,INK,1.8)
    poly([(-29,-5),(-17,0),(-13,21),(-22,27-p.rag),(-30,15)],CLOTH_D,None)
    poly([(5,-3),(17,0),(22,9),(14,28+p.rag),(11,14)],CLOTH_L,None)
    line([(-6,3),(-5,14),(-4,28)],CLOTH_D,1.7)
    line([(20,6),(18,13),(15,18)],CLOTH_D,1.5)
    poly([(-29,-12),(27,-13),(28,0),(-29,1)],LEATHER_D)
    line([(-25,-10),(24,-11)],LEATHER_L,1.8)
    poly([(1,-15),(17,-15),(19,2),(-1,2)],METAL)
    poly([(4,-10),(13,-10),(14,-3),(3,-3)],LEATHER_D,None)
    line([(8,-12),(8,-3)],'#e2d2aa',1.4)
    poly([(-32,-6),(-17,-4),(-15,11),(-20,17),(-33,13)],LEATHER)
    line([(-30,-3),(-18,-2),(-21,4),(-30,2)],LEATHER_L,1.8)
    for x in (-29,-24,-19):line([(x,9),(x,12)],WRAP,1.)
    # Two small bone trophies on the belt, outside the main silhouette.
    for x,y,ang in ((-8,4,18),(-3,7,-12)):
        c.line([q(x,y),q(x,y+10)],WRAP,1.2)
        c.oval(q(x,y+13),2.3,4.8,IVORY,INK,.7,p.lean+ang)

def _alive(p):
    j=solve(p); c=Canvas(FRAME_SIZE)
    _leg(c,j['far_leg'],True)
    _arm(c,j['far_arm'],True)
    _leg(c,j['near_leg'],False)
    _body(c,p)
    # Head precedes near arm; weapon stays under the gripping fingers.
    _head(c,j['head'],p.head+p.lean*.35,p.jaw,p.eye)
    _club(c,j['near_arm'][-1],p.club)
    _arm(c,j['near_arm'],False,p.club,True)
    return c.finish()


def _render_frame(anim,i,n):
    p=pose(anim,i,n)
    if anim not in ('death','death_idle'):return _alive(p)
    t=phase(i,n,False) if anim=='death' else 1.
    u=track(t,[(0,0),(.14,.035),(.30,.12),(.70,1),(1,1)])
    # Rotate the intact body and lower it as one, then align its lowest pixel
    # to the contact row. The final death frame and death_idle are identical.
    if not u:
        return _alive(replace(IDLE,jaw=3))
    im=_alive(replace(p,eye=1-u,club=35+55*u,jaw=3+3*(1-u),
                      hip=mix(p.hip,(CX,GROUND-73),u),lean=p.lean*(1-u),
                      near_foot=mix(p.near_foot,(CX+12,GROUND-8),u),
                      far_foot=mix(p.far_foot,(CX-14,GROUND-8),u),
                      near_hand=mix(p.near_hand,(CX+19,GROUND-75),u),
                      far_hand=mix(p.far_hand,(CX-30,GROUND-67),u)))
    # Pad before rotating: the original feet pivot under the falling head.
    pad=160
    padded=Image.new('RGBA',(FRAME_SIZE[0]+2*pad,FRAME_SIZE[1]+2*pad))
    padded.alpha_composite(im,(pad,pad))
    im=padded.rotate(94*u,Image.Resampling.BICUBIC,
                     center=(CX+pad,GROUND-65+pad))
    bb=im.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox()
    if bb is None:return Image.new('RGBA',FRAME_SIZE)
    # Preserve the horizontal pivot, translating the fall only vertically.
    cropped=im.crop(bb); out=Image.new('RGBA',FRAME_SIZE)
    out.alpha_composite(cropped,(bb[0]-pad-round(6*u),round(GROUND+1-cropped.height)))
    return out


def _body_metrics(fw,fh):
    # Hunched trunk, head and legs, excluding club and reach of arms.
    return body_metrics_for_box((CX-37,GROUND-173,CX+62,GROUND+1),fw,fh)


def render(out_dir: str | Path, **opts):
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    out=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,out_dir=out_dir,
                    frame_size=FRAME_SIZE,auto_crop=False,actor_metadata=ACTOR_METADATA,
                    body_metrics_fn=_body_metrics,animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=True)
    return [out[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
