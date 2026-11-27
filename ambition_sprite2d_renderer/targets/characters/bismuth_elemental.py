"""Bismuth crystal creature and its suited business variant.

Both targets use the same hopper-crystal painter, skeletal pose, and gait.
The colors suggest the interference colors of oxidized bismuth crystals.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from ._clockwork_enemy_art import Canvas, add, sub, mul, unit, perp, mix, rot, phase, track, anchored_death
from ...authoring.skeleton import two_bone_ik_points
from ...authoring.surface_gait import Gait
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'bismuth_elemental'
FRAME_SIZE = (350, 280)
CX, FLOOR = 139., 251.
EDGE = '#292c43'
INK = '#252a3d'
SUIT = '#353d55'
SUIT_D = '#20273a'
SUIT_L = '#505d79'
SHIRT = '#e9e8df'
TIE = '#ac3c4b'
LEGS = (34., 33.)
ARMS = (41., 39.)
SUIT_LEGS = (36., 35.)
SUIT_ARMS = (32., 31.)
WALK = Gait(stride=39, stance=.66, lift=9)
RUN = Gait(stride=48, stance=.60, lift=13)
LOOPS = {'idle','walk','run','death_idle'}


@dataclass(frozen=True)
class Variant:
    target: str
    name: str
    serious: bool
    timing: tuple[float,float,float]
    description: str
    gameplay: str


NORMAL = Variant(TARGET_NAME, 'Bismuth Elemental', False, (.66,.18,.82),
    'A humanoid cluster of stepped bismuth hopper crystals. Iridescent oxide colors follow its square terraces and recessed faces.',
    'A heavy crystalline enemy that draws back a blocky fist, then drives it forward. It breaks into crystal fragments on defeat.')
SERIOUS = Variant('serious_bismuth', 'Serious Bismuth', True, (.50,.14,.64),
    'An iridescent bismuth crystal in a tailored business suit, with a tie, glasses and a briefcase.',
    'A businesslike crystalline fighter that strikes with its briefcase. It walks more briskly than the larger bismuth elemental.')


def rows(v):
    w,a,r=v.timing
    return [('idle',16,80),('walk',16,75),('run',16,55),('notice',8,70),
            ('windup',round(w*30),33),('attack_side',round((w+a+r)*30),33),
            ('hit',8,65),('death',22,55),('death_idle',1,200)]


def tint(color, factor):
    rgb=tuple(int(color[j:j+2],16) for j in (1,3,5))
    return tuple(max(0,min(255,round(x*factor))) for x in rgb)


# The same oxide film palette is sampled around a crystal. Different planes
# get different hues and light values; narrow highlights belong to edges.
OXIDE = ('#d58c4b', '#efc56e', '#8ebfa0', '#32b6b9', '#3b86bd',
         '#6c52ad', '#bf57a7', '#e67b99')


def oxide(k, shade=1.):
    i = math.floor(k)
    a = tint(OXIDE[i % len(OXIDE)], 1.)
    b = tint(OXIDE[(i+1) % len(OXIDE)], 1.)
    return tuple(max(0, min(255, round(x*shade))) for x in mix(a,b,k-i))


def crystal(c, center, rx, ry, angle=0., seed=0, levels=3, shade=1., face=None):
    """Oblique hopper geometry, with actual offset recesses and broad facets.

    Positive depth is behind the front plane. Each ledge and each riser has
    its own projected quad. Fewer, wider planes survive sprite downsampling.
    A solid small shard uses the same projection with no recessed steps.
    """
    def P(x,y,z=0.):
        return add(center,rot((rx*(x-.10*y-.46*z),ry*(y+.12*x-.40*z)),angle))
    def corners(radius,z=0.,dx=0.,dy=0.):
        return [P(x*radius+dx,y*radius+dy,z) for x,y in ((-1,-1),(1,-1),(1,1),(-1,1))]
    hue = seed*1.27
    def facet(quad,k,light,glint=False):
        # Three broad, gently changing color bands on large faces; no black
        # line between bands. Only the boundaries of the actual planes ink.
        a,b,d,e=quad
        c.poly(quad,oxide(k,shade*light),None)
        if math.dist(a,b)>12 and math.dist(a,e)>3.5:
            for lo,hi,shift in ((0.,.27,-.65),(.27,.70,0.),(.70,1.,.55)):
                c.poly([mix(a,b,lo),mix(a,b,hi),mix(e,d,hi),mix(e,d,lo)],
                       oxide(k+shift,shade*light),None)
        c.line(quad,EDGE,.70,closed=True)
        if glint:
            c.line([mix(a,b,.10),mix(a,b,.76)],oxide(k+.45,shade*1.48),1.0)
    front=corners(1.)
    back=corners(1.,.72 if levels else .58)
    facet([back[0],back[1],front[1],front[0]],hue+.9,1.06,True)
    facet([back[3],back[0],front[0],front[3]],hue+4.4,.51)
    c.poly(front,oxide(hue+2,shade*.76),EDGE,1.25)
    if not levels:
        a,b,d,e=front
        hub=P(-.20,-.23)
        c.poly([a,b,hub],oxide(hue+.8,shade*1.12),None)
        c.poly([b,d,hub],oxide(hue+2.4,shade*.88),None)
        c.poly([d,e,hub],oxide(hue+4.4,shade*.68),None)
        c.poly([e,a,hub],oxide(hue+5.6,shade*.94),None)
        c.line([a,b],oxide(hue+.7,shade*1.45),1.05)
        c.line([b,d],oxide(hue+2.1,shade*1.18),.75)
        return
    # Face crystals are broad at the bottom of their two-step hollow.
    end=.61 if face is not None else .24
    radius=1.; depth=0.; outer=front
    for k in range(levels):
        step=(1.-end)/levels
        # The shelf and wall are separate 3D faces. Deeper levels shift
        # down/right in projection, like a real open crystal hopper.
        ledge=radius-step*.59
        inner=radius-step
        z_next=depth-step*.56
        shelf=corners(ledge,depth)
        bottom=corners(inner,z_next)
        for j in range(4):
            m=(j+1)%4
            color=hue+1.30*k+(0.5,2.8,4.7,6.1)[j]
            facet([outer[j],outer[m],shelf[m],shelf[j]],color,(1.12,.91,.70,.94)[j],j in (0,3))
            facet([shelf[j],shelf[m],bottom[m],bottom[j]],color+1.25,(.52,.70,1.00,.70)[j])
        radius,depth,outer=inner,z_next,bottom
    c.poly(outer,oxide(hue+5.0,shade*.34),EDGE,.9)
    c.line([back[0],back[1],front[1]],oxide(hue+.9,shade*1.42),1.15)
    if face is None:return
    ready,hurt,serious=face
    def F(x,y):return P(x*radius,y*radius,depth)
    # The expressive face is on the deepest plane, not a screen pasted
    # over the terraces. A large asymmetric brow and a chiselled jaw.
    c.poly([F(-1,-1),F(1,-1),F(1,1),F(-1,1)],'#272c43',EDGE,.7)
    c.poly([F(-1,-1),F(1,-1),F(1,-.60),F(.20,-.39),F(-.31,-.55),F(-1,-.40)],oxide(hue+4.7,shade*.66),None)
    c.poly([F(-.92,.56),F(-.26,.80),F(.89,.51),F(1,1),F(-1,1)],oxide(hue+3.8,shade*.52),None)
    if hurt>.6:
        c.line([F(-.79,-.07),F(-.23,.07)],'#ffdd98',1.8)
        c.line([F(.19,.04),F(.80,-.10)],'#ffdd98',1.8)
    else:
        eye='#fff2b2' if not serious else '#f5f7ee'
        slant=.20+.12*ready if not serious else .12+.08*ready
        c.poly([F(-.83,-.32-slant),F(-.16,-.17),F(-.23,.17),F(-.77,.09)],eye,None)
        c.poly([F(.12,-.17),F(.85,-.36-slant),F(.76,.08),F(.18,.17)],eye,None)
        if serious:
            c.poly([F(-.41,-.18),F(-.23,-.17),F(-.29,.13),F(-.45,.08)],'#596275',None)
            c.poly([F(.52,-.19),F(.69,-.23),F(.62,.10),F(.46,.11)],'#596275',None)
    if serious:
        # Glasses sit across the opening, with a thin gold bridge and a
        # small temple; do not cover the eyes with opaque lenses.
        for x in (-.51,.50):
            c.line([F(x-.38,-.40),F(x+.38,-.40),F(x+.32,.26),F(x-.32,.26),F(x-.38,-.40)],'#e3c68a',1.5)
        c.line([F(-.13,-.24),F(.12,-.24)],'#e3c68a',1.5)
        c.line([F(-.87,-.31),F(-1.14,-.45)],'#a58b60',1.4)
        c.line([F(-.34,.60),F(.11,.47),F(.55,.56)],'#b9a49b',1.5)
    else:
        c.poly([F(-.56,.50),F(-.21,.42),F(.10,.61),F(.52,.42),F(.73,.58),F(.45,.72),F(-.48,.70)],'#171e32',None)
        c.line([F(-.46,.54),F(-.17,.51),F(.10,.65),F(.50,.53)],'#edc68a',1.05)


@dataclass(frozen=True)
class Pose:
    t: float=0.
    moving: float=0.
    ready: float=0.
    hit: float=0.
    recovery: float=0.
    hurt: float=0.
    alert: float=0.
    death: float=0.


def pose(v,anim,i,n):
    t=phase(i,n,anim in LOOPS)%1. if anim in LOOPS else phase(i,n,False)
    if anim=='idle': return Pose(t)
    if anim in ('walk','run'):return Pose(t,.7 if anim=='walk' else 1.)
    if anim=='notice':return Pose(t,alert=track(t,[(0,0),(.5,1),(1,1)]))
    if anim=='windup':return Pose(t,ready=track(t,[(0,0),(.8,1),(1,1)]))
    if anim=='attack_side':
        w,a,r=v.timing; A=w/(w+a+r); B=(w+a)/(w+a+r)
        return Pose(t,ready=track(t,[(0,0),(.8*A,1),(A,1),(A+.04,0),(1,0)]),
            hit=track(t,[(0,0),(A,0),(A+.045,1),(B,1),(B+.18,.12),(1,0)]),
            recovery=track(t,[(0,0),(B,0),(B+.15,1),(1,0)]))
    if anim=='hit':return Pose(t,hurt=math.sin(math.pi*t))
    if anim in ('death','death_idle'):
        return Pose(0.,death=1. if anim=='death_idle' else track(t,[(0,0),(.13,.025),(.82,1),(1,1)]))
    raise ValueError(anim)


def solve(v,q):
    r,h,z=q.ready,q.hit,q.hurt
    p=math.tau*q.t; sw=math.sin(p)*q.moving
    if v.serious:
        # A composed upright office worker, not a crouched golem in a suit.
        lean=1+7*q.moving-13*r+17*h-11*z+5*q.recovery-3*q.alert
        hip=(CX-4*r+7*h-5*z,FLOOR-79+5*q.moving+1.2*math.cos(2*p)*q.moving+5*r+3*h+.55*math.sin(p)*(1-q.moving)*(1-r)*(1-h)*(1-z))
        shoulder,leg_len,arm_len=23,SUIT_LEGS,SUIT_ARMS
        stance=15
        far_goal=(CX-31+14*sw+12*r-9*h,FLOOR-77-16*r+7*h)
        near_goal=(CX+36-15*sw+17*r+52*h,FLOOR-79-47*r-23*h+10*q.recovery)
    else:
        lean=9+8*q.moving-15*r+24*h-11*z+7*q.recovery-3*q.alert
        hip=(CX-7*r+8*h-5*z,FLOOR-65+1.5*math.cos(2*p)*q.moving+4*r+3*h+.85*math.sin(p)*(1-q.moving)*(1-r)*(1-h)*(1-z))
        shoulder,leg_len,arm_len=39,LEGS,ARMS
        stance=29
        far_goal=(CX-65+15*sw+13*r-6*h,FLOOR-64-26*r+3*h)
        near_goal=(CX+70-16*sw-1*r+51*h,FLOOR-63-65*r-35*h+13*q.recovery)
    def P(x,y):return add(hip,rot((x,y),lean))
    if v.serious and q.alert:
        # On noticing a target, adjust the left temple of the glasses with
        # the free hand. The briefcase stays in the other hand.
        far_goal=mix(far_goal,P(-23,-103),q.alert)
    gait=RUN if q.moving>.9 else WALK
    def foot(side,offset):
        x,lift=gait.foot_offset(q.t,offset) if q.moving else (0.,0.)
        return CX+side*stance+x+side*6*h,FLOOR-10-lift
    def chain(root,goal,lengths,bend):return (root,*two_bone_ik_points(root,goal,*lengths,bend,extension_margin=.08))
    return P,lean,dict(far_leg=chain(P(-stance*.74,0),foot(-1,.5),leg_len,1.),
        near_leg=chain(P(stance*.74,0),foot(1,0.),leg_len,1.),
        far_arm=chain(P(-shoulder,-66),far_goal,arm_len,-1.),
        near_arm=chain(P(shoulder,-63),near_goal,arm_len,-1.))


def angle_of(a,b):return math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))-90


def _case(c,wrist,angle,shade=1.):
    def P(x,y):return add(wrist,rot((x,y),angle))
    # Handle reaches into the hand; front flap, gusset, brass corners.
    c.line([P(-10,11),P(-10,-2),P(10,-2),P(10,11)],'#392b2d',5.)
    c.line([P(-8,3),P(-8,-1),P(8,-1)],'#ac8057',1.2)
    c.poly([P(-24,7),P(24,7),P(30,14),P(30,39),P(23,46),P(-24,46),P(-29,40),P(-29,13)],'#422d30',EDGE,1.6)
    c.poly([P(-24,9),P(20,9),P(24,14),P(24,39),P(20,43),P(-24,43),P(-26,38),P(-26,14)],'#855541',EDGE,1.15)
    c.poly([P(-24,9),P(20,9),P(24,15),P(21,24),P(-24,24),P(-26,16)],'#a16c4d',EDGE,1.0)
    c.poly([P(24,14),P(30,14),P(30,39),P(24,43)],'#5a3932',None)
    for x in (-14,13):
        c.poly([P(x-3,20),P(x+3,20),P(x+3,29),P(x-3,29)],'#d2af6d',EDGE,.7)
        c.line([P(x-1,22),P(x+1,22)],'#fff0b7',.9)
    c.line([P(-22,39),P(18,39)],'#bd8c62',.85)
    for x,s in ((-23,1),(21,-1)):
        c.poly([P(x,36),P(x+s*5,36),P(x+s*5,41),P(x,41)],'#b69561',None)


def _cloth_chain(c,joints,radii,far=False,leg=False):
    """Continuous suit contour following the existing solved joint chain."""
    a,b,e=joints
    u,w=unit(sub(b,a)),unit(sub(e,b)); n,m=perp(u),perp(w)
    mid=add(n,m); j=unit(mid) if math.hypot(*mid)>.1 else n
    def off(p,v,r):return add(p,mul(v,r))
    r0,r1,r2=radii
    l0,l1,l2=off(a,n,-r0),off(b,j,-r1),off(e,m,-r2)
    r0p,r1p,r2p=off(a,n,r0),off(b,j,r1),off(e,m,r2)
    base=SUIT_D if far else SUIT
    light=SUIT if far else SUIT_L
    shade='#181e2b' if far else SUIT_D
    c.poly([l0,l1,l2,r2p,r1p,r0p],base,EDGE,1.55)
    c.poly([off(a,n,-r0*.77),off(b,j,-r1*.68),off(e,m,-r2*.72),off(e,m,-r2*.18),off(b,j,-r1*.16),off(a,n,-r0*.22)],light,None)
    c.poly([off(a,n,r0*.40),off(b,j,r1*.30),off(e,m,r2*.58),r2p,r1p,r0p],shade,None)
    # Pressed crease for slacks, short fold at the elbow for sleeves.
    if leg:
        c.line([off(a,n,-r0*.20),off(b,j,-r1*.16),off(e,m,-r2*.21)],light,1.0)
        c.line([off(mix(b,e,.81),m,-r2*.64),off(mix(b,e,.90),m,r2*.24)],shade,.95)
    else:
        c.line([off(mix(a,b,.77),n,-r1*.62),off(b,j,-r1*.18),off(mix(b,e,.23),m,r1*.12)],shade,1.1)
        c.line([off(mix(b,e,.70),m,r2*.74),off(mix(b,e,.90),m,r2*.72)],light,.95)


def _shoe(c,e,far):
    def P(x,y):return add(e,(x,y))
    base='#23283a' if far else '#30384c'
    c.poly([P(-12,-8),P(7,-8),P(12,-3),P(25,1),P(28,5),P(26,10),P(-13,10),P(-16,5)],base,EDGE,1.4)
    c.poly([P(-12,6),P(27,6),P(26,10),P(-13,10),P(-16,7)],'#171b28',None)
    c.poly([P(9,-2),P(19,0),P(24,3),P(13,4),P(5,2)],'#525b70' if far else '#788297',None)
    c.line([P(-10,0),P(2,0)],'#657084' if not far else '#41495b',1.15)
    c.line([P(-11,8),P(24,8)],'#4b5260',.9)


def _stone_foot(c,e,seed,shade):
    def P(x,y):return add(e,(x,y))
    # Wide low solid base; the toe's bottom plane is exactly on the IK
    # floor contact row. Put the terraces on top, not through the floor.
    outline=[P(-19,-4),P(-12,-12),P(10,-12),P(25,-7),P(29,1),P(26,10),P(-20,10),P(-24,3)]
    c.poly(outline,oxide(seed+4.6,shade*.61),EDGE,1.5)
    c.poly([P(-19,-4),P(-12,-12),P(10,-12),P(25,-7),P(19,0),P(-17,0)],oxide(seed+1.7,shade*1.12),EDGE,.8)
    c.poly([P(19,0),P(25,-7),P(29,1),P(26,10),P(19,9)],oxide(seed+3.2,shade*.70),None)
    c.poly([P(-18,0),P(19,0),P(19,9),P(-20,10)],oxide(seed+5.8,shade*.90),None)
    c.poly([P(-10,1),P(11,1),P(8,6),P(-13,6)],oxide(seed+2.7,shade*.65),None)
    c.line([P(-16,0),P(18,0)],oxide(seed+1.6,shade*1.40),1.2)
    crystal(c,add(e,(0,-11)),17,10,-2,seed+1,2,shade)


def _paint(c,v,q):
    P,lean,j=solve(v,q if q.death==0 else Pose())
    d=q.death
    def piece(center,rx,ry,ang=0,seed=0,levels=3,shade=1.,face=None):
        if d:
            dx=center[0]-CX
            x=CX+dx*1.22
            ang=ang+(1 if dx>=0 else -1)*(30+seed*9)*d
            rx*=1-.29*d; ry*=1-.33*d
            extent=max(rot((rx*(u-.10*v-.46*z),ry*(v+.12*u-.40*z)),ang)[1]
                       for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)] for z in (0.,.72))
            center=mix(center,(x,FLOOR-extent-3-abs(dx)*.035),d)
            face=None if d>.25 else face
        crystal(c,center,rx,ry,ang,seed,levels,shade,face)
    def limb(name,width,seed,far=False,leg=False):
        a,b,e=j[name]
        shade=.76 if far else 1.
        if v.serious and not d:
            _cloth_chain(c,(a,b,e),(width,width*.76,width*.57 if not leg else width*.70),far,leg)
        else:
            for k,(lo,hi) in enumerate(((a,b),(b,e))):
                if not d:c.line([lo,hi],'#36364b',width*.92)
                # Mostly solid angular facets between larger hopper clusters.
                # Taper the shin into the boot and keep the projected
                # lower slab above the planted sole even in a bent knee.
                low_leg=leg and k==1
                piece(mix(lo,hi,.43 if low_leg else .52),width*(.80 if low_leg else (.93 if k else 1.04)),
                      math.dist(lo,hi)*(.42 if low_leg else .49),angle_of(lo,hi),seed+k,1 if k==0 else 0,shade)
        if leg:
            if v.serious and not d:_shoe(c,e,far)
            elif not d:_stone_foot(c,e,seed+2,shade)
            else:piece(add(e,(6,-4)),24,12,0,seed+2,2,shade)
        elif name=='near_arm' and v.serious and not d:
            c.box(e,9,7,SHIRT,EDGE,1.,1.,angle_of(b,e))
            # Carry vertically, rotate out and forward with the hand. The
            # handle is drawn first and the little crystal fist covers it.
            angle=-160*q.ready-102*q.hit+21*q.recovery+8*math.sin(math.tau*q.t)*q.moving
            _case(c,e,angle)
            piece(e,8,8,angle_of(b,e),seed+2,0,shade)
            c.line([add(e,rot((-3,-5),angle)),add(e,rot((-3,4),angle))],oxide(seed+3,shade*.7),.8)
        elif v.serious:
            if not d:c.box(e,9,7,SHIRT,EDGE,1.,1.,angle_of(b,e))
            piece(e,9,10,angle_of(b,e)*.7,seed+2,1,shade)
        else:
            # Massive single fist, edged by three little angular knuckles.
            ang=angle_of(b,e)*.48
            piece(e,27,23,ang,seed+2,2,shade)
            for k in range(3):
                off=rot((20,(k-1)*13),ang)
                piece(add(e,off),8,6,ang-5,seed+k+5,1,shade)
    limb('far_leg',12 if v.serious else 17,2,True,True)
    limb('near_leg',12 if v.serious else 18,5,False,True)
    limb('far_arm',13 if v.serious else 18,4,True)
    if not v.serious or d:
        # Broader torso, dark connection planes and fewer hollow motifs.
        # Outer shoulders have staggered projecting slabs like a growing
        # cluster of hopper crystals, rather than a set of concentric frames.
        piece(P(-34,-62),26,28,-22+lean,5,2,.78)
        piece(P(-24,-91),15,25,-30+lean,1,2,.90)
        piece(P(-44,-79),13,18,-38+lean,7,0,.82)
        piece(P(1,-13),32,20,lean-3,6,1,.84)
        piece(P(3,-40),42,39,lean-7,0,3)
        piece(P(38,-65),24,24,15+lean,3,2)
        piece(P(47,-84),13,16,29+lean,4,1)
        piece(P(24,-103),15,22,18+lean,6,1)
        # Paint face after the forearm, preserving its readability.
        limb('near_arm',20,1)
        piece(P(5,-107),27,26,lean*.48-2+1.5*math.sin(math.tau*q.t)*(1-q.moving)*(1-q.ready)*(1-q.hit),2,2,1.,(q.ready+q.hit,q.hurt,v.serious))
    else:
        # A clean, fitted jacket with a more human stance. The shirt is a
        # narrow inset, the collar and lapels distinct folded fabric planes.
        c.poly([P(-27,-75),P(-15,-84),P(16,-84),P(29,-70),P(23,-39),P(23,-14),P(27,1),P(8,7),P(-2,-3),P(-11,7),P(-27,1),P(-22,-18),P(-24,-50)],SUIT,EDGE,1.8)
        c.poly([P(-26,-69),P(-18,-49),P(-15,-20),P(-23,-3),P(-27,1),P(-22,-18),P(-24,-50)],SUIT_D,None)
        c.poly([P(-13,-82),P(15,-82),P(11,-59),P(2,-25),P(-9,-60)],SHIRT,EDGE,.85)
        c.poly([P(-4,-76),P(4,-76),P(7,-70),P(3,-65),P(6,-40),P(1,-28),P(-4,-38),P(-1,-65),P(-7,-70)],TIE,EDGE,.7)
        c.poly([P(-3,-64),P(1,-64),P(2,-41),P(-1,-37)],'#d26c6a',None)
        c.poly([P(-13,-83),P(-22,-72),P(-10,-58),P(-15,-51),P(2,-25),P(-8,-61)],SUIT_L,EDGE,.9)
        c.poly([P(15,-83),P(24,-70),P(14,-56),P(19,-49),P(2,-25),P(9,-60)],SUIT_D,EDGE,.9)
        c.line([P(-22,-70),P(-10,-58)],'#8a94a5',.8)
        c.line([P(2,-26),P(4,-8),P(-2,-3)],SUIT_D,1.15)
        for y in (-19,-8):c.disk(P(6,y),1.9,'#c2a46a',EDGE,.55)
        c.poly([P(14,-47),P(22,-49),P(23,-45),P(14,-44)],SHIRT,EDGE,.6)
        c.line([P(-20,-16),P(-10,-17)],SUIT_D,1.6)
        c.line([P(-20,-14),P(-10,-15)],SUIT_L,.8)
        piece(P(-8,-89),12,16,-13+lean,5,1,.8)
        limb('near_arm',13,1)
        piece(P(4,-103),25,26,lean*.40-2+.8*math.sin(math.tau*q.t)*(1-q.moving)*(1-q.ready)*(1-q.hit),2,2,1.,(q.ready+q.hit,q.hurt,True))
        if q.alert>.10:
            # The hand touches the temple in front of the head; the sleeve
            # remains behind it. Same solved wrist, no additional IK pass.
            _,elbow,wrist=j['far_arm']
            piece(wrist,8,9,angle_of(elbow,wrist)*.7,6,0,.92)
    if not v.serious and q.hit>.15 and not d:
        # Small fragments at the fist, following the active envelope. No
        # detached projectile or new hitbox is implied by these accents.
        wrist=j['near_arm'][-1]
        k=q.hit
        for i in range(3):
            point=add(wrist,(22+9*i+6*k,-25-i*7+5*k))
            piece(point,2.6+1.0*k,3.7+1.0*k,24*i+35*k,2+i,0,.9)
    if q.hurt>.2:
        for k in range(4):
            f=q.hurt; x=CX-20-10*k-18*f;y=FLOOR-135+k*13-16*f
            piece((x,y),2.8,4,20*k+40*f,k,0,.9)


def render_frame(v,anim,i,n):
    c=Canvas(FRAME_SIZE)
    q=pose(v,anim,i,n)
    if v.serious and q.death:
        # Serious Bismuth falls in its suit, with the briefcase in hand.
        # Do not replace the clothes with a bare crystal body at death.
        from PIL import Image
        _paint(c,v,Pose(hurt=min(.85,4*q.death)))
        im=c.finish().rotate(-77*q.death,resample=Image.Resampling.BICUBIC,center=(CX,FLOOR-66))
        return anchored_death(im,FLOOR)
    _paint(c,v,q)
    im=c.finish()
    if q.death:return anchored_death(im,FLOOR)
    return im


def metadata(v):
    traits=['enemy','elemental','chemical_element','bismuth','crystal', 'business' if v.serious else 'science']
    w,a,r=v.timing; total=w+a+r
    return {'actor':{'character_id':v.target,'display_name':v.name},
        'body':{'body_plan':'Biped','body_kind':'Standard','mass_class':'Heavy',
                'locomotion_hint':'Walk','traits':traits},
        'capabilities':{'traversal':{'walk':True}},
        'actions':{'default_preset':v.target+'_strike'},
        'visual':{'default_pose':'idle','portrait':{'animation':'idle','frame':0}},
        'tags':traits,'authoring_description':v.description,'gameplay_description':v.gameplay,
        'animation_bindings':{'default':{'animation':'idle','events':[]},
            'locomotion.walk':{'animation':'walk','events':[]},'locomotion.run':{'animation':'run','events':[]},
            'combat.hurt':{'animation':'hit','events':[]},'combat.death':{'animation':'death','events':[]},
            'action.melee.primary':{'animation':'attack_side','events':[
                {'t':w/total,'event':'hitbox_active_start','source':v.target+'.strike'},
                {'t':(w+a)/total,'event':'hitbox_active_end','source':v.target+'.strike'}]}}}


def publish(v,out_dir,**opts):
    Path(out_dir).mkdir(parents=True,exist_ok=True)
    clips=rows(v)
    outputs=build_sheet(target=v.target,rows=clips,render_fn=lambda a,i,n:render_frame(v,a,i,n),
        out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,actor_metadata=metadata(v),
        body_metrics_fn=lambda w,h:body_metrics_for_box((89,42,195,252) if not v.serious else (101,41,181,252),w,h),
        animation_key_map={a:a for a,_,_ in clips},sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]


def render(out_dir: str|Path,**opts):return publish(NORMAL,out_dir,**opts)
