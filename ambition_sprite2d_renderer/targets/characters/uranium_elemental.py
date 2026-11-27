"""Uranium: a dense, fissured metallic creature for the Science Dimension.

The lime emission is a stylized radiation motif, not the literal appearance
of elemental uranium. No clothing, chemical lettering or hazard pictograms.
Only existing melee combat is authored here; the emission is decorative.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from ._clockwork_enemy_art import Canvas, add, mix, rot, phase, track, polar, anchored_death
from ...authoring.skeleton import two_bone_ik_points
from ...authoring.surface_gait import Gait
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'uranium_elemental'
FRAME_SIZE = (384, 300)
CX, FLOOR = 148., 263.
ARM_LENGTHS = (46., 46.)
LEG_LENGTHS = (33., 33.)
WINDUP, ACTIVE, RECOVERY = .78, .20, .92
TOTAL = WINDUP + ACTIVE + RECOVERY
ROWS = [('idle',24,65),('walk',20,70),('run',20,55),('notice',8,65),
        ('windup',26,30),('attack_side',63,30),('hit',8,65),
        ('death',24,60),('death_idle',1,200)]
LOOPS = {'idle','walk','run','death_idle'}
WALK = Gait(stride=34, stance=.69, lift=7)
RUN = Gait(stride=47, stance=.62, lift=11)


@dataclass(frozen=True)
class Pose:
    t: float=0.
    moving: float=0.
    alert: float=0.
    ready: float=0.
    strike: float=0.
    recover: float=0.
    hurt: float=0.
    death: float=0.


def pose(anim,i,n):
    t=phase(i,n,anim in LOOPS)
    if anim in LOOPS: t%=1.
    if anim=='idle':return Pose(t)
    if anim in ('walk','run'):return Pose(t,moving=.65 if anim=='walk' else 1.)
    if anim=='notice':return Pose(t,alert=track(t,[(0,0),(.5,1),(1,1)]))
    if anim=='windup':return Pose(t,ready=track(t,[(0,0),(.85,1),(1,1)]))
    if anim=='attack_side':
        a,b=WINDUP/TOTAL,(WINDUP+ACTIVE)/TOTAL
        return Pose(t,ready=track(t,[(0,0),(.85*a,1),(a,1),(a+.035,0),(1,0)]),
            strike=track(t,[(0,0),(a,0),(a+.035,1),(b,1),(b+.13,.35),(1,0)]),
            recover=track(t,[(0,0),(b,0),(b+.17,1),(1,0)]))
    if anim=='hit':return Pose(t,hurt=math.sin(math.pi*t))
    if anim in ('death','death_idle'):
        return Pose(death=1. if anim=='death_idle' else track(t,[(0,0),(.12,.025),(.87,1),(1,1)]))
    raise ValueError(anim)


def solve(q):
    p=math.tau*q.t; r,h,z=q.ready,q.strike,q.hurt
    neutral=(1-r)*(1-h)*(1-z)
    lean=8+6*q.moving-20*r+35*h-15*z+4*q.recover
    hip=(CX-7*r+8*h-5*z,FLOOR-65+1.5*math.cos(2*p)*q.moving+7*r+21*h+3*q.recover+.8*math.sin(p)*neutral*(1-q.moving))
    def P(x,y):return add(hip,rot((x,y),lean))
    gait=RUN if q.moving>.9 else WALK
    sw=math.sin(p)*q.moving
    def foot(side,offset):
        x,lift=gait.foot_offset(q.t,offset) if q.moving else (0.,0.)
        return CX+side*26+x+side*5*h,FLOOR-11-lift
    def arm(side):
        # Both fists rise and compress the torso's glow, then strike the floor
        # in front. The near fist is larger and has a slightly longer reach.
        if side<0:
            idle=(CX-61+12*sw,FLOOR-62)
            ready=(CX-45,FLOOR-201)
            hit=(CX+71,FLOOR-30)
        else:
            idle=(CX+70-12*sw,FLOOR-59)
            ready=(CX+65,FLOOR-197)
            hit=(CX+106,FLOOR-30)
        return mix(mix(idle,ready,r),hit,h)
    def chain(root,goal,lengths,bend):
        return root,*two_bone_ik_points(root,goal,*lengths,bend,extension_margin=.08)
    return P,lean,{'far_leg':chain(P(-20,0),foot(-1,.5),LEG_LENGTHS,1.),
                   'near_leg':chain(P(20,0),foot(1,0.),LEG_LENGTHS,1.),
                   'far_arm':chain(P(-34,-66),arm(-1),ARM_LENGTHS,-1.),
                   'near_arm':chain(P(36,-65),arm(1),ARM_LENGTHS,-1.)}


# Silvery, oxidized metal with warm olive reflections near the energized seams.
# Larger continuous masses and restrained facet boundaries make the material
# read as dense metal rather than a heap of individually glowing rocks.
EDGE = (24,28,30)
DARK = (36,43,47)
STEEL = (95,110,116)
PLANE = (170,185,187)
PALE = (235,242,234)
GLOW_D = (65,91,34)
GLOW = (164,230,54)
HOT = (243,255,186)


def tint(rgb,f):return tuple(max(0,min(255,round(x*f))) for x in rgb)


def color_mix(a,b,t):return tuple(round(v) for v in mix(a,b,t))


def intensity(q):
    # Steady internal glow, with a readable charge envelope rather than a strobe.
    return min(1.,.49+.085*math.sin(math.tau*q.t)+.48*q.ready+.44*q.strike+.18*q.hurt+.12*q.alert)


def fissure(c,points,charge,width=2.):
    c.line(points,EDGE,width+2.1)
    if charge <= 0.:return
    # A muted reflection on the metal lips, then a narrow emissive interior.
    c.line(points,color_mix((46,54,40),(103,142,52),charge),width+1.0)
    c.line(points,color_mix(GLOW_D,GLOW,charge),width)
    if charge>.20:
        c.line(points,color_mix(GLOW_D,HOT,charge),max(.45,width*.38))


# Clockwise chamfered masses. Three shapes remain useful for falling fragments,
# while the torso and head below have their own anatomy-specific surfaces.
PROFILES=(
    ((-.78,-.87),(-.25,-1.),(.50,-.93),(.95,-.58),(.91,.63),(.49,.94),(-.64,.88),(-1.,.31)),
    ((-.91,-.57),(-.67,-.90),(.19,-1.),(.88,-.71),(1.,.28),(.56,.92),(-.38,1.),(-.96,.54)),
    ((-.93,-.76),(-.16,-1.),(.72,-.86),(1.,-.28),(.88,.62),(.19,1.),(-.67,.85),(-1.,.15)),
)


def metal(c,center,rx,ry,angle,seed,shade,charge,cracked=True):
    def P(x,y):return add(center,rot((x*rx,y*ry),angle))
    pts=[P(*p) for p in PROFILES[seed%len(PROFILES)]]
    a,b,d,e,f,g,h,j=pts
    # A narrow bright bevel, large flat central face, and dark side plane.
    u=P(-.67,-.56); v=P(.50,-.58); w=P(.48,.57); z=P(-.57,.66)
    c.poly(pts,tint(STEEL,shade),EDGE,1.55)
    c.poly([a,b,d,v,u],tint(PLANE,shade),None)
    c.poly([d,e,f,g,w,v],tint(DARK,shade),None)
    c.poly([g,h,j,z,w],tint(DARK,shade*1.30),None)
    c.poly([j,a,u,z],tint(STEEL,shade*.79),None)
    c.poly([u,v,w,z],tint(STEEL,shade*1.07),None)
    if cracked and charge>0:
        c.poly([mix(u,z,.32),mix(u,v,.46),mix(v,w,.58),mix(u,z,.73)],tint(color_mix(STEEL,(130,153,92),.22*charge),shade),None)
    # Long broad reflection interrupted by the facet, not repeated triangles.
    c.poly([mix(u,z,.05),mix(v,w,.05),mix(v,w,.25),mix(u,z,.42)],tint(PLANE,shade*.96),None)
    c.poly([mix(u,z,.42),mix(v,w,.25),mix(v,w,.34),mix(u,z,.49)],tint(DARK,shade*1.52),None)
    c.poly([mix(u,z,.71),mix(v,w,.68),w,z],tint(PLANE,shade*.49),None)
    c.line([a,b,d],tint(PALE,shade*.94),1.2)
    c.line([v,w,g],tint(PLANE,shade*.55),.8)
    if rx>21:
        c.line([mix(a,b,.30),mix(b,d,.65)],tint(PALE,shade*1.08),1.0)
        c.line([P(-.48,.19),P(-.34,.15)],tint(PLANE,shade*.78),.7)
    if cracked:
        if seed%2:
            path=[P(-.56,-.82),P(-.37,-.35),P(-.12,-.23),P(-.25,.04),P(.19,.32),P(.12,.73)]
            branch=[P(-.25,.04),P(-.57,.24),P(-.68,.55)]
        else:
            path=[P(.23,-.90),P(.07,-.44),P(.24,-.16),P(-.17,.06),P(-.05,.38),P(-.35,.73)]
            branch=[P(-.17,.06),P(-.53,-.07),P(-.62,.13)]
        fissure(c,path,charge,1.35 if rx>18 else .8)
        if rx>26:fissure(c,branch,charge*.64,.7)


def _angle(a,b):return math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))-90


def foot(c,e,shade,charge):
    def P(x,y):return add(e,(x,y))
    pts=[P(-22,-4),P(-14,-15),P(6,-15),P(23,-9),P(30,2),P(25,11),P(-20,11),P(-25,3)]
    c.poly(pts,tint(STEEL,shade),EDGE,1.6)
    c.poly([pts[0],pts[1],pts[2],pts[3],P(13,1),P(-17,2)],tint(PLANE,shade),None)
    c.poly([P(-17,2),P(13,1),pts[3],pts[4],pts[5],pts[6]],tint(DARK,shade),None)
    c.poly([P(-15,4),P(12,4),P(23,6),P(20,9),P(-16,9)],tint(STEEL,shade*.72),None)
    c.line([pts[0],pts[1],pts[2],pts[3]],tint(PALE,shade),1.3)
    fissure(c,[P(7,-14),P(3,-6),P(9,-2)],charge*.65,.95)
    c.line([P(16,2),P(23,4),P(23,9)],tint(PLANE,shade*.63),1.0)


def fist(c,center,angle,size,shade,charge):
    # A single continuous cast-metal hand with a thumb and blunt knuckles.
    # Coordinate x is across the hand; y follows its long axis.
    def P(x,y):return add(center,rot((x*size,y*size),angle))
    outline=[P(-.67,-.83),P(.42,-.91),P(.91,-.58),P(1.03,-.16),P(.99,.50),P(.67,.92),P(-.38,1.),P(-.90,.58),P(-1.04,.02),P(-.84,-.42)]
    c.poly(outline,tint(STEEL,shade),EDGE,1.8)
    c.poly([outline[0],outline[1],outline[2],P(.49,-.24),P(-.50,-.22)],tint(PLANE,shade),None)
    c.poly([outline[2],outline[3],outline[4],outline[5],P(.46,.51),P(.49,-.24)],tint(DARK,shade),None)
    c.poly([outline[5],outline[6],outline[7],P(-.52,.51),P(.46,.51)],tint(DARK,shade*1.18),None)
    c.poly([P(-.50,-.22),P(.49,-.24),P(.46,.51),P(-.52,.51)],tint(STEEL,shade*1.03),None)
    # Blunt finger ridges separated by dark narrow grooves; no separate gems.
    for j in range(3):
        x=-.46+j*.35
        c.poly([P(x,-.15),P(x+.27,-.16),P(x+.30,.45),P(x+.21,.69),P(x-.015,.58)],tint(PLANE,shade*(.81-.06*j)),None)
        c.line([P(x+.29,-.12),P(x+.31,.44),P(x+.21,.69)],tint(DARK,shade),1.25)
        c.line([P(x+.03,-.15),P(x+.02,.18)],tint(PALE,shade*.87),1.0)
    thumb=[P(-.71,-.56),P(-.99,-.27),P(-.94,.17),P(-.63,.37),P(-.39,.12),P(-.39,-.22)]
    c.poly(thumb,tint(STEEL,shade*1.1),EDGE,1.1)
    c.poly([thumb[0],thumb[1],P(-.69,-.07),thumb[5]],tint(PLANE,shade),None)
    # Folded finger ends and transverse knuckle crease convey a closed fist.
    c.line([P(-.52,.43),P(-.12,.39),P(.23,.40),P(.49,.35)],tint(DARK,shade),1.25)
    c.line([P(-.48,.47),P(-.17,.46),P(.16,.47),P(.40,.43)],tint(PLANE,shade*.70),.9)
    c.line([outline[0],outline[1],outline[2]],tint(PALE,shade),1.35)
    fissure(c,[P(.15,-.87),P(.06,-.59),P(.19,-.35),P(.08,-.18)],charge,.95)
    if charge>.6:fissure(c,[P(.19,-.35),P(.49,-.44),P(.67,-.32)],charge*.72,.7)


def head(c,P,charge,hurt,ready):
    # A broad, solid brow and a protruding jaw. Eyes are incised in the metal.
    outline=[P(-33,-108),P(-26,-125),P(-7,-132),P(20,-129),P(35,-116),P(39,-97),P(29,-82),P(10,-73),P(-13,-80),P(-29,-90)]
    c.poly(outline,STEEL,EDGE,2.)
    c.poly([outline[0],outline[1],outline[2],outline[3],outline[4],P(21,-111),P(-15,-110)],PLANE,None)
    c.poly([outline[4],outline[5],outline[6],P(21,-93),P(21,-111)],DARK,None)
    c.poly([outline[6],outline[7],outline[8],outline[9],P(-18,-94),P(8,-88),P(21,-93)],color_mix(DARK,STEEL,.22),None)
    c.poly([P(-20,-108),P(-4,-104),P(-11,-94),P(-23,-98)],DARK,None)
    c.poly([P(4,-104),P(24,-110),P(24,-98),P(10,-93)],DARK,None)
    c.poly([P(-16,-94),P(-4,-91),P(3,-84),P(-11,-81),P(-22,-89)],color_mix(STEEL,PLANE,.40),None)
    c.poly([P(-3,-100),P(4,-108),P(12,-97),P(6,-91),P(-1,-94)],PLANE,EDGE,.85)
    c.line([outline[0],outline[1],outline[2],outline[3]],PALE,1.25)
    c.line([P(-25,-121),P(-11,-126),P(12,-125)],color_mix(PLANE,PALE,.65),1.05)
    fissure(c,[P(1,-130),P(-5,-123),P(1,-118),P(-9,-112)],charge*.73,.9)
    eye=color_mix(GLOW,HOT,min(1.,.32+.68*charge)) if charge>0 else DARK
    if hurt>.6:
        c.line([P(-20,-101),P(-7,-100)],eye,1.6)
        c.line([P(9,-100),P(23,-103)],eye,1.6)
    else:
        c.poly([P(-23,-108-2*ready),P(-4,-102),P(-8,-96),P(-22,-99)],EDGE,None)
        c.poly([P(5,-102),P(26,-109-2*ready),P(25,-99),P(9,-95)],EDGE,None)
        c.poly([P(-21,-105-2*ready),P(-7,-102),P(-9,-98),P(-20,-100)],eye,None)
        c.poly([P(8,-102),P(23,-106-2*ready),P(23,-101),P(10,-98)],eye,None)
    c.line([P(-13,-86),P(-4,-88),P(8,-86),P(21,-89)],EDGE,2.3)
    if charge>0:c.line([P(-6,-87),P(8,-86),P(16,-88)],color_mix(GLOW_D,GLOW,charge*.65),.75)
    c.line([P(-10,-83),P(5,-81),P(18,-84)],color_mix(STEEL,PLANE,.6),1.0)


def chest(c,P,charge,ready,strike):
    # One broad chest, with a recessed diagonal split following the metal's
    # irregular contour instead of a luminous badge-shaped hole.
    outline=[P(-37,-78),P(-13,-88),P(21,-84),P(41,-68),P(43,-45),P(30,-21),P(16,-7),P(-19,-9),P(-35,-31),P(-45,-56)]
    c.poly(outline,STEEL,EDGE,1.9)
    c.poly([outline[0],outline[1],outline[2],outline[3],P(24,-59),P(-19,-61)],PLANE,None)
    c.poly([outline[3],outline[4],outline[5],outline[6],P(11,-27),P(24,-59)],DARK,None)
    c.poly([outline[6],outline[7],outline[8],P(-16,-32),P(11,-27)],color_mix(DARK,STEEL,.22),None)
    c.poly([outline[8],outline[9],outline[0],P(-19,-61),P(-16,-32)],color_mix(STEEL,DARK,.32),None)
    c.poly([P(-19,-61),P(24,-59),P(11,-27),P(-16,-32)],STEEL,None)
    if charge>0:
        c.poly([P(-18,-60),P(-4,-72),P(-12,-62),P(1,-53),P(-3,-41),P(-17,-36)],color_mix(STEEL,(149,170,82),.46*charge),None)
        c.poly([P(8,-55),P(20,-54),P(17,-39),P(10,-32),P(-3,-41)],color_mix(STEEL,(142,166,85),.42*charge),None)
    c.poly([P(-19,-61),P(24,-59),P(20,-47),P(-18,-43)],color_mix(STEEL,PLANE,.57),None)
    c.poly([P(-18,-43),P(20,-47),P(18,-43),P(-18,-39)],color_mix(DARK,STEEL,.67),None)
    c.line([outline[0],outline[1],outline[2],outline[3]],PALE,1.4)
    c.line([P(-35,-72),P(-15,-80),P(14,-78)],color_mix(PLANE,PALE,.76),1.1)
    # Width changes through the main break during charging. Negative space
    # and asymmetry are retained in every pose.
    w=2.1+1.5*ready+.9*strike
    crack=[P(-11,-85),P(-4,-72),P(-12,-62),P(1,-53),P(-3,-41),P(10,-32),P(5,-17),P(11,-10)]
    c.poly([P(-11,-85),P(1,-73),P(-4,-63),P(8,-53),P(3,-42),P(14,-32),P(5,-17),P(0,-30),P(-8,-40),P(-5,-53),P(-18,-62),P(-11,-72)],EDGE,None)
    fissure(c,crack,charge,w)
    fissure(c,[P(-12,-62),P(-25,-57),P(-28,-45),P(-37,-41)],charge*.86,1.1)
    fissure(c,[P(-3,-41),P(-20,-32),P(-21,-23)],charge*.75,.95)
    fissure(c,[P(1,-53),P(16,-63),P(28,-60),P(36,-67)],charge*.78,1.05)
    fissure(c,[P(10,-32),P(22,-37),P(31,-31)],charge*.68,.85)
    c.line([P(-15,-69),P(-18,-62),P(-12,-57)],color_mix(PLANE,PALE,.65),1.0)
    c.line([P(9,-50),P(5,-42),P(15,-33)],color_mix(PLANE,PALE,.45),.85)
    if charge>.7:
        c.line([P(-4,-72),P(-12,-62),P(1,-53)],HOT,1.15)
        c.line([P(-3,-41),P(10,-32),P(5,-17)],HOT,1.0)


def paint(c,q):
    d=q.death
    P,lean,limbs=solve(q if d==0 else Pose())
    charge=intensity(q)*(1-d)
    def settled(center,rx,ry,angle,seed):
        if not d:return center,rx,ry,angle
        dx=center[0]-CX
        angle+=d*(38+seed*9)*(1 if dx>=0 else -1)
        rx*=1-.18*d;ry*=1-.24*d
        ext=max(rot((x*rx,y*ry),angle)[1] for x,y in PROFILES[seed%3])
        center=mix(center,(CX+dx*1.30,FLOOR-ext-2-abs(dx)*.05),d)
        return center,rx,ry,angle
    def piece(center,rx,ry,angle,seed,shade=1.,cracked=True):
        center,rx,ry,angle=settled(center,rx,ry,angle,seed)
        metal(c,center,rx,ry,angle,seed,shade,charge,cracked)
    def limb(name,width,seed,far=False,leg=False):
        a,b,e=limbs[name]; shade=.67 if far else 1.
        if not d:
            # Broad overlapping joint volume; don't outline each segment like
            # a robot. Narrow glowing seams only at selected joints.
            c.line([a,b,e],EDGE,width*1.50)
            c.line([a,b,e],tint(DARK,shade*1.3),width*1.31)
            c.disk(b,width*.69,tint(STEEL,shade*.76),None)
            if not leg:fissure(c,[mix(a,b,.78),b,mix(b,e,.23)],charge*.85,1.5)
        for k,(lo,hi) in enumerate(((a,b),(b,e))):
            piece(mix(lo,hi,.48),width*(1.05 if k==0 else 1.13 if not leg else .85),
                  math.dist(lo,hi)*(.52 if leg and k else .60),_angle(lo,hi),seed+k,shade,not leg and k==0)
        if leg:
            if d:piece(add(e,(5,-4)),24,11,0,seed+2,shade,False)
            else:foot(c,e,shade,charge)
        else:
            angle=_angle(b,e)
            size=24 if far else 29
            center,rx,ry,angle=settled(e,size,size,angle,seed+2)
            fist(c,center,angle,(rx+ry)*.5,shade,charge)
    limb('far_leg',16,1,True,True)
    limb('near_leg',18,4,False,True)
    limb('far_arm',19,7,True)
    # Asymmetric shoulders with fewer larger planes. Both belong to the
    # metal body, not to a suit of armor.
    piece(P(-32,-68),31,34,lean-18,0,.83,True)
    piece(P(-47,-80),12,18,lean-38,4,.90,False)
    piece(P(-3,-16),31,22,lean+3,2,.82,False)
    if d:
        center=P(0,-47); dx=center[0]-CX
        target=(CX+dx*1.25,FLOOR-47)
        def falling_chest(x,y):
            local=rot((x,y+47),lean-59*d)
            return add(mix(center,target,d),(local[0]*(1-.18*d),local[1]*(1-.26*d)))
        chest(c,falling_chest,charge,0.,0.)
    else:chest(c,P,charge,q.ready,q.strike)
    piece(P(35,-66),32,33,lean+19,5,1.,True)
    piece(P(49,-78),11,15,lean+37,6,.94,False)
    limb('near_arm',22,9)
    # Preserve facial readability while the fists are raised.
    if d:
        center=P(4,-102); dx=center[0]-CX
        target=(CX+dx*1.28,FLOOR-34)
        def falling_head(x,y):
            local=rot((x-4,y+102),lean+64*d)
            return add(mix(center,target,d),(local[0]*(1-.18*d),local[1]*(1-.26*d)))
        head(c,falling_head,charge,d,0.)
    else:head(c,P,charge,q.hurt,q.ready)
    if d:return
    # Softly fading sizes and two-value emission; no full-body flashes.
    for j in range(15):
        u=(q.t+j/15)%1.; k=math.sin(math.pi*u)**2
        if k<.10:continue
        side=-1 if j%2 else 1
        x=side*(41+(26+10*q.ready)*u)+7*math.sin(math.tau*u+j)
        y=-18-125*u
        point=P(x,y)
        c.disk(point,(.65+1.4*charge)*k,color_mix(GLOW_D,GLOW,charge),None)
        if j%4==0:c.disk(point,.70*k,HOT,None)
    if q.ready>.10:
        # Charge visibly accumulates around both fists. The emissive traces
        # are local to the metal, not a persistent damage field.
        for name in ('far_arm','near_arm'):
            x,y=limbs[name][-1]; k=q.ready
            for j in range(5):
                a=math.tau*(q.t+j/5); rr=29+6*math.sin(2*a)
                p0=(x+rr*math.cos(a),y+rr*math.sin(a))
                p1=(p0[0]+5*math.cos(a),p0[1]+5*math.sin(a))
                c.line([p0,p1],color_mix(GLOW_D,GLOW,k),.7+1.1*k)
    if q.strike>.08:
        # Ground-hugging asymmetric impact: dark silhouettes of a few metal
        # chips and a luminous split. Cosmetic, not a second hitbox.
        k=q.strike; x,y=limbs['near_arm'][-1]; y=min(FLOOR-4,y+25)
        c.line([(x-32,y-1),(x-14,y-5),(x+6,y-1),(x+27,y-5),(x+51,y-2)],color_mix(GLOW_D,GLOW,k),1.5+2*k)
        c.line([(x-26,y-2),(x-11,y-4),(x+7,y-1),(x+23,y-4),(x+40,y-3)],color_mix(GLOW,HOT,k),.7+1.1*k)
        for j in range(6):
            ang=-167+j*27
            a=add((x,y),polar(13+11*(1-k),ang))
            b=add((x,y),polar(29+16*(1-k)+(j%3)*7,ang))
            c.line([a,b],color_mix(GLOW_D,GLOW,k),1.4*k+.45)
            c.line([a,mix(a,b,.54)],color_mix(GLOW,HOT,k),.7*k+.30)
            if j%2==0:
                xx,yy=b
                c.poly([(xx-3,yy+1),(xx+1,yy-4),(xx+4,yy+1),(xx,yy+4)],DARK,EDGE,.8)
                c.line([(xx-3,yy+1),(xx+1,yy-4)],PLANE,.85)
    if q.hurt>.15:
        for j in range(4):
            center=P(-25-j*13,-55-j*16)
            center=add(center,(-12*q.hurt,-12*q.hurt))
            c.disk(center,1.6*q.hurt,HOT,None)


def render_frame(anim,i,n):
    q=pose(anim,i,n); c=Canvas(FRAME_SIZE); paint(c,q); im=c.finish()
    return anchored_death(im,FLOOR) if q.death else im


TRAITS=['enemy','science','elemental','chemical_element','uranium','radioactive','heavy']
ACTOR_METADATA={
    'actor':{'character_id':TARGET_NAME,'display_name':'Uranium Elemental'},
    'body':{'body_plan':'Biped','body_kind':'Standard','mass_class':'Heavy',
            'locomotion_hint':'Walk','traits':TRAITS},
    'capabilities':{'traversal':{'walk':True}},
    'actions':{'default_preset':'uranium_elemental_slam'},
    'visual':{'default_pose':'idle','portrait':{'animation':'idle','frame':0}},
    'tags':TRAITS,
    'authoring_description':'A dense, bare metallic monster with fractured silver-black surfaces and a stylized luminous interior.',
    'gameplay_description':'A heavy, slow creature that gathers charge, raises both fists and strikes the ground in front of itself.',
    'animation_bindings':{'default':{'animation':'idle','events':[]},
        'locomotion.walk':{'animation':'walk','events':[]},'locomotion.run':{'animation':'run','events':[]},
        'combat.hurt':{'animation':'hit','events':[]},'combat.death':{'animation':'death','events':[]},
        'action.melee.primary':{'animation':'attack_side','events':[
            {'t':WINDUP/TOTAL,'event':'hitbox_active_start','source':'uranium_elemental.slam'},
            {'t':(WINDUP+ACTIVE)/TOTAL,'event':'hitbox_active_end','source':'uranium_elemental.slam'}]}}}


def render(out_dir: str|Path,**opts):
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=render_frame,out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,auto_crop=False,actor_metadata=ACTOR_METADATA,
        body_metrics_fn=lambda w,h:body_metrics_for_box((89,68,213,265),w,h),
        animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
