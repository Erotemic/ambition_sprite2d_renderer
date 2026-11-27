"""A soft-solid alkali-metal creature, with a sodium-yellow reaction burst.

Silver cut surfaces and a dull oxidized skin are material motifs. The amber
emission is a stylized reference to the Na I D doublet (588.995/589.592 nm),
not the ambient color of sodium. No text, symbols, or costume. The engine
owns the lunge and damage; all sparks and smoke here are decorative.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from pathlib import Path

from ._clockwork_enemy_art import (Canvas, add, sub, mul, mix, rot, unit, perp,
    bezier, polar, phase, track, anchored_death)
from ...authoring.skeleton import two_bone_ik_points
from ...authoring.surface_gait import Gait
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'sodium_elemental'
FRAME_SIZE = (352, 268)
CX, FLOOR = 132., 236.
ARMS, LEGS = (31., 31.), (28., 28.)
WINDUP, ACTIVE, RECOVERY = .44, .22, .78
TOTAL = WINDUP+ACTIVE+RECOVERY
A, B = WINDUP/TOTAL, (WINDUP+ACTIVE)/TOTAL
# 30 ms attack samples span the 1.44 second action. The separate windup
# ends at the same pose as the last pre-launch sample of the full action.
ROWS = [('idle',24,65),('walk',24,50),('run',24,38),('notice',10,55),
        ('windup',15,29),('attack_side',48,30),('hit',9,55),
        ('death',24,55),('death_idle',1,200)]
LOOPS = {'idle','walk','run','death_idle'}
WALK = Gait(stride=31, stance=.68, lift=8)
RUN = Gait(stride=42, stance=.60, lift=13)
EDGE = '#252c34'; DULL = '#899497'; SHADE = '#54616b'; DARK = '#35434e'
MID = '#aebbbd'; LIGHT = '#d7e0df'; WHITE = '#f6f7ef'; WARM = '#f3ad39'
YELLOW = '#ffc329'; HOT = '#fff6ab'; AMBER = '#cf702a'; SOOT = '#7a7470'

@dataclass(frozen=True)
class Pose:
    t: float=0.
    move: float=0.
    ready: float=0.
    strike: float=0.
    recover: float=0.
    flash: float=0.
    alert: float=0.
    hurt: float=0.
    death: float=0.


def pose(anim,i,n):
    t=phase(i,n,anim in LOOPS)
    if anim in LOOPS and anim!='death_idle':
        return Pose(t%1.,move={'idle':0.,'walk':.65,'run':1.}[anim])
    if anim=='notice':return Pose(alert=track(t,[(0,0),(.45,1),(1,.5)]))
    if anim=='windup':return Pose(ready=track(t,[(0,0),(.81,1),(1,1)]))
    if anim=='attack_side':
        launch=A-.075/TOTAL
        return Pose(ready=track(t,[(0,0),(.81*launch,1),(launch,1),(A,0),(1,0)]),
            strike=track(t,[(0,0),(launch,0),(A,1),(B,1),(B+.13,.28),(1,0)]),
            recover=track(t,[(0,0),(B,0),(B+.15,1),(1,0)]),
            flash=track(t,[(0,0),(launch,0),(A,1),(B,.86),(B+.24,0),(1,0)]),t=t%1.)
    if anim=='hit':return Pose(hurt=math.sin(math.pi*t))
    if anim in ('death','death_idle'):
        return Pose(death=1. if anim=='death_idle' else t)
    raise ValueError(anim)


def chain(root,goal,lengths,bend):
    return root,*two_bone_ik_points(root,goal,*lengths,bend,extension_margin=.08)


def death_rig(t):
    """Articulated collapse. Only joint goals and body orientation are animated.

    The feet initially stay planted; the knees buckle, the near hand braces,
    then the upper mass falls forwards. The body and limbs keep their geometry
    at impact, with a slight rebound before the final settled posture.
    """
    k=lambda *keys:track(t,keys)
    hip=(CX+k((0,0),(.13,-6),(.30,-9),(.49,-15),(.66,-24),(.76,-23),(.90,-25),(1,-25)),
         FLOOR+k((0,-53),(.13,-54),(.31,-40),(.46,-32),(.63,-59),(.72,-56),(.83,-59),(1,-58)))
    lean=k((0,5),(.13,-13),(.31,18),(.46,49),(.64,88),(.73,82),(.86,91),(1,91))
    def P(x,y):return add(hip,rot((x,y),lean))
    # Track the foot and wrist targets in world coordinates, not on a
    # rotating bitmap. The resting legs trail the torso and the front hand
    # catches the fall, then loses tension.
    ff=(CX+k((0,-22),(.32,-22),(.62,-43),(.84,-55),(1,-55)),
        FLOOR+k((0,-10),(.48,-10),(.66,-33),(1,-33)))
    nf=(CX+k((0,22),(.32,22),(.62,-52),(.86,-76),(1,-76)),
        FLOOR+k((0,-10),(.46,-10),(.60,-30),(.83,-26),(1,-26)))
    fh=(CX+k((0,-65),(.14,-68),(.34,-35),(.58,27),(.85,43),(1,43)),
        FLOOR+k((0,-65),(.16,-83),(.39,-59),(.63,-27),(.82,-25),(1,-25)))
    nh=(CX+k((0,68),(.16,58),(.34,73),(.55,102),(.70,96),(.86,91),(1,91)),
        FLOOR+k((0,-45),(.15,-65),(.34,-39),(.55,-24),(.73,-25),(.9,-24),(1,-24)))
    return P,lean,{'far_leg':chain(P(-17,0),ff,LEGS,1.),
                   'near_leg':chain(P(17,0),nf,LEGS,1.),
                   'far_arm':chain(P(-39,-53),fh,ARMS,1.),
                   'near_arm':chain(P(44,-39),nh,ARMS,1.)}


def solve(q):
    if q.death:return death_rig(q.death)
    p=math.tau*q.t; r,h,z=q.ready,q.strike,q.hurt
    # A compact, springy creature, not a tall rock golem. The hips sink
    # before it throws its body into the engine-driven lunge.
    lean=5+8*q.move-13*r+22*h-17*z+1.5*math.sin(p)*(1-r)*(1-h)*(1-q.move)
    hip=(CX-6*r+9*h-5*z,FLOOR-53+7*r-2*h+3*q.recover+2*math.cos(2*p)*q.move+1.3*math.sin(p)*(1-r)*(1-h)*(1-q.move))
    def P(x,y):return add(hip,rot((x,y),lean))
    gait=RUN if q.move>.9 else WALK
    def foot(side,off):
        x,lift=gait.foot_offset(q.t,off) if q.move else (0.,0.)
        return CX+side*22+x+side*3*h,FLOOR-10-lift
    sw=math.sin(p)*q.move
    def hand(side):
        if side<0:
            idle=(CX-65+10*sw,FLOOR-65)
            ready=(CX-69,FLOOR-55)
            hit=(CX+22,FLOOR-83)
        else:
            idle=(CX+68-10*sw,FLOOR-45)
            ready=(CX+59,FLOOR-45)
            hit=(CX+112,FLOOR-82)
        return mix(mix(idle,ready,r),hit,h)
    return P,lean,{'far_leg':chain(P(-17,0),foot(-1,.5),LEGS,1.),
                   'near_leg':chain(P(17,0),foot(1,0.),LEGS,1.),
                   'far_arm':chain(P(-39,-53),hand(-1),ARMS,1.),
                   'near_arm':chain(P(44,-39),hand(1),ARMS,1.)}


def path(start,*segments):
    """Join the existing cubic Bezier sampler into a closed contour."""
    pts=[start]
    for a,b,e in segments:pts.extend(bezier(pts[-1],a,b,e,n=12)[1:])
    return pts


def shape(c,P,start,*segments,fill,edge=EDGE,width=1.8):
    c.poly([P(*p) for p in path(start,*segments)],fill,edge,width)


def line(c,P,pts,col,width=1.5):c.line([P(*p) for p in pts],col,width)
def poly(c,P,pts,col,edge=None,width=1.5):c.poly([P(*p) for p in pts],col,edge,width)


def limb(c,chain,far=False,leg=False,foot_pitch=0.):
    # Continuous metal contours around the solved links. Extend the upper
    # thigh into the hip and incorporate the foot in the same outline: no
    # ankle rings, detached shoe, or exposed flat joint caps.
    a,b,e=chain
    u=unit(sub(b,a));v=unit(sub(e,b));n=perp(u);m=perp(v)
    mid=unit(add(n,m))
    if leg:
        a=sub(a,mul(u,10.))
        r0,r1,r2=19.,14.5,11.5
        # The foot has its own orientation. Align the ankle cross-section
        # with it so the shin flows into the toe and heel without a seam.
        m=rot((-1.,0.),foot_pitch)
    else:r0,r1,r2=17.,14.,15.
    A0=add(a,mul(n,-r0));A1=add(a,mul(n,r0))
    B0=add(b,mul(mid,-r1));B1=add(b,mul(mid,r1))
    E0=add(e,mul(m,-r2));E1=add(e,mul(m,r2))
    tangent=unit(add(u,v))
    def side_curve(a0,b0,e0):
        return path(a0,(mix(a0,b0,.42),sub(b0,mul(tangent,10 if leg else 7)),b0),
                    (add(b0,mul(tangent,10 if leg else 7)),mix(b0,e0,.74),e0))
    top=side_curve(A0,B0,E0); bottom=side_curve(A1,B1,E1)
    base=SHADE if far else DULL
    light=DULL if far else LIGHT
    if leg:
        def F(x,y):return add(e,rot((x,y),foot_pitch))
        cap=path(E0,(F(14,-1),F(22,-2),F(24,4)),
                 (F(27,10),F(12,10),F(3,10)),
                 (F(-9,10),F(-16,8),F(-14,3)),
                 (F(-14,0),F(-12,-1),E1))
        # Round the root inside the torso. Leave the root stroke off the
        # near thigh: it emerges from the metal of the hip, not a socket.
        root=bezier(A1,sub(A1,mul(u,8)),sub(A0,mul(u,8)),A0,n=12)
        outline=top+cap[1:]+bottom[::-1]+root[1:]
        c.poly(outline,base,None)
        c.line(top+cap[1:]+bottom[::-1],EDGE,1.7)
        def ridge(f):return side_curve(mix(A0,A1,f),mix(B0,B1,f),mix(E0,E1,f))
        # Carry the reflection from the hip through the shin and into the
        # foot. The broad tonal band, rather than a dark line, defines the
        # bend at the ankle.
        lo=path(ridge(.16)[-1],(F(14,1),F(21,1),F(21,4)),
                (F(20,6),F(6,6),F(-8,4)),(F(-10,2),F(-9,1),ridge(.80)[-1]))
        c.poly(ridge(.16)+lo[1:]+ridge(.80)[::-1],light,None)
        c.line(ridge(.22)+[F(12,1),F(18,3)],MID if far else WHITE,1.7)
        line(c,F,[(-10,7),(3,8),(17,7),(22,5)],DARK,1.15)
        c.line(ridge(.86)[6:],DARK if far else '#77848b',1.1)
    else:
        cap=bezier(E0,add(E0,mul(v,7)),add(E1,mul(v,7)),E1,n=10)
        pts=top+cap[1:]+bottom[::-1]
        c.poly(pts,base,EDGE,1.7)
        def ridge(t):return side_curve(mix(A0,A1,t),mix(B0,B1,t),mix(E0,E1,t))
        c.poly(ridge(.22)+ridge(.70)[::-1],light,None)
        c.line(ridge(.25),MID if far else WHITE,1.8)
        c.line(ridge(.85),DARK if far else '#77848b',1.2)
        # Broad fist with bent, malleable knuckles, oriented with the wrist.
        angle=math.degrees(math.atan2(v[1],v[0]))
        def F(x,y):return add(e,rot((x,y),angle))
        shape(c,F,(-12,-14),((-2,-20),(15,-20),(23,-12)),((29,-5),(30,8),(21,15)),
              ((13,20),(-2,20),(-12,14)),((-18,7),(-19,-6),(-12,-14)),fill=SHADE if far else MID)
        shape(c,F,(-7,-13),((1,-17),(16,-17),(22,-9)),((27,-4),(27,3),(21,7)),
              ((8,10),(1,5),(-10,4)),((-14,-2),(-11,-9),(-7,-13)),fill=DULL if far else LIGHT,edge=None)
        line(c,F,[(-5,-10),(3,-12),(12,-11),(17,-7)],MID if far else WHITE,2.1)
        for y in (-5,2,9):line(c,F,[(19,y),(14,y+1),(10,y+1)],SHADE,1.25)
        line(c,F,[(-6,8),(2,10),(8,9)],DARK,1.35)


def body(c,P,q):
    r,h,z=q.ready,q.strike,q.hurt
    # The face is cut into a fresh surface of a single soft metal chunk.
    # A rounded, dull, thicker crust wraps the bright oblique cut face.
    dent=track(q.death,[(0,0),(.56,0),(.65,1),(.75,.32),(.88,.54),(1,.54)])
    def T(x,y):
        f=max(0.,min(1.,-y/118.))
        # At impact the lower metal flank gives slightly. This is local
        # material deformation; the limb rig and entire sprite are intact.
        contact=max(0.,x)/58.
        return P(x*(1+.10*r*f-.045*h*f+.018*math.sin(math.tau*q.t)*f*(1-q.move)*(1-r)*(1-h))
                 -6.0*dent*contact*contact*f,
                 y*(1-.14*r+.035*h+.025*dent*f))
    shape(c,T,(-44,-26),((-57,-43),(-57,-75),(-44,-98)),
          ((-40,-111),(-29,-118),(-15,-120)),((-3,-121),(32,-112),(46,-100)),
          ((58,-89),(57,-71),(53,-57)),((59,-39),(48,-17),(32,-8)),
          ((15,10),(-30,5),(-44,-26)),fill=DULL,width=2.3)
    # Oxidized side and rear bevel: neutral gray, no crystal fragments.
    shape(c,T,(-44,-96),((-55,-81),(-55,-49),(-43,-28)),
          ((-35,-15),(-17,-5),(-4,-5)),((-19,-25),(-20,-50),(-19,-68)),
          ((-23,-83),(-32,-90),(-44,-96)),fill=SHADE,edge=None)
    shape(c,T,(-43,-98),((-28,-115),(-17,-116),(-8,-114)),
          ((9,-116),(35,-109),(44,-100)),((48,-95),(49,-93),(51,-89)),
          ((34,-97),(12,-94),(-8,-92)),((-23,-93),(-34,-94),(-43,-98)),fill=LIGHT,edge=None)
    # Fresh cut is a single silvery plane with an oblique reflection, not
    # a panel or visor. The two planes meet at a chamfer in the soft metal.
    shape(c,T,(-20,-89),((-8,-94),(26,-98),(43,-88)),
          ((50,-83),(50,-68),(47,-57)),((52,-42),(38,-25),(24,-19)),
          ((11,-13),(-6,-14),(-15,-24)),((-25,-36),(-24,-65),(-20,-89)),fill='#bec9ca',edge=None)
    shape(c,T,(-20,-89),((-8,-94),(26,-98),(43,-88)),
          ((45,-84),(47,-81),(46,-77)),((31,-84),(15,-78),(4,-63)),
          ((-8,-47),(-15,-39),(-20,-39)),((-24,-51),(-24,-70),(-20,-89)),fill='#e5ebe8',edge=None)
    shape(c,T,(40,-87),((50,-80),(50,-64),(47,-57)),
          ((52,-42),(38,-25),(24,-19)),((11,-13),(-6,-14),(-15,-24)),
          ((2,-26),(17,-42),(25,-57)),((33,-73),(42,-76),(40,-87)),fill='#85959d',edge=None)
    shape(c,T,(-13,-27),((5,-28),(21,-41),(33,-52)),
          ((39,-58),(44,-67),(47,-73)),((48,-59),(49,-46),(42,-35)),
          ((28,-21),(4,-15),(-13,-27)),fill='#abb9bc',edge=None)
    # Distinct fresh cut edge and small irregular, soft dents.
    line(c,T,[(-18,-85),(-9,-89),(8,-90),(23,-90),(37,-85)],WHITE,2.8)
    line(c,T,[(-20,-61),(-20,-51),(-18,-38),(-12,-29),(0,-23)],'#e6ece7',1.6)
    line(c,T,[(-47,-73),(-46,-55),(-41,-42)],MID,2.0)
    line(c,T,[(-32,-103),(-22,-108),(-8,-110)],WHITE,1.7)
    # Rounded bevel reflections give the freshly cut face a little depth.
    shape(c,T,(-15,-85),((-3,-91),(20,-92),(35,-86)),
          ((22,-88),(7,-86),(-3,-83)),((-9,-82),(-13,-83),(-15,-85)),fill=WHITE,edge=None)
    shape(c,T,(-41,-78),((-44,-61),(-39,-41),(-29,-31)),
          ((-36,-35),(-44,-44),(-47,-58)),((-48,-67),(-45,-75),(-41,-78)),fill='#a8b4b5',edge=None)
    shape(c,T,(-11,-23),((0,-17),(18,-18),(30,-26)),
          ((17,-15),(7,-13),(-4,-17)),((-8,-18),(-11,-20),(-11,-23)),fill=WHITE,edge=None)
    # A face sculpted in the metal. The larger near eye and off-axis mouth
    # convey the side view. Dark sockets, yellow light only inside the eyes.
    f=3.5*r+2.2*h; blink=1-.73*z
    if q.death:
        blink=track(q.death,[(0,1),(.12,.35),(.28,.8),(.46,.18),(.62,.04),(1,.04)])
    if q.move==0 and r+h==0 and q.hurt==0:
        blink*=1-.88*max(0.,1-abs(q.t-.72)/.045)
    for x,y,w,sl in [(-3,-76,10,1),(25,-78,13,-1)]:
        s=(3.7+f)*(1-.54*track(q.death,[(0,0),(.4,0),(.65,1),(1,1)]))
        # Dark dents in the metal, with a curved lip and reflected gold.
        eyeh=4*(1-.69*track(q.death,[(0,0),(.32,0),(.59,1),(1,1)]))
        a=(x-w-2,y-eyeh-sl*s); b=(x+w+1,y-eyeh+sl*s)
        d=(x-w,y+5*blink-sl*s); e=(x+w-1,y+5*blink+sl*s)
        shape(c,T,a,(mix(a,b,.36),mix(a,b,.76),b),
              ((b[0]+1,b[1]+3),(e[0]+1,e[1]-1),e),
              (mix(e,d,.27),mix(e,d,.70),d),((d[0]-2,d[1]-3),(a[0]-2,a[1]+2),a),fill=EDGE,edge=None)
        if blink>.18 and q.death<.46:
            col=HOT if r+h>.3 else YELLOW
            if q.death:
                glow=1-track(q.death,[(0,0),(.13,.34),(.29,.18),(.46,1),(1,1)])
                col=tuple(round(v) for v in mix((37,44,52),(255,195,41),glow))
            poly(c,T,[(x-w+2,y-1-sl*s),(x+w-2,y-1+sl*s),
                      (x+w-3,y+2.5*blink+sl*s),(x-w+2,y+2.5*blink-sl*s)],col)
        line(c,T,[(x-w+1,y+7*blink-sl*s),(x+w-2,y+7*blink+sl*s)],'#dce5df',1.3)
    # A compressed ridge and a crooked smirk change into an open snarl.
    poly(c,T,[(5,-57),(13,-65),(17,-54),(13,-51)],'#c0c9c9')
    if q.death:
        openness=track(q.death,[(0,0),(.13,1),(.28,.62),(.43,.25),(.58,0),(1,0)])
        # Open briefly as balance is lost, then relax into a closed mouth.
        y=-43+2*openness
        if openness>.04:
            shape(c,T,(6,y),((15,y-3),(28,y-5),(35,y-4)),
                  ((34,y+9*openness),(22,y+12*openness),(15,y+9*openness)),
                  ((8,y+5*openness),(6,y+2),(6,y)),fill=EDGE,edge=None)
        else:
            line(c,T,[(6,y),(15,y+1),(26,y-1),(35,y-4)],EDGE,2.)
    elif h>.1 or r>.5:
        shape(c,T,(4,-43),((14,-48),(28,-49),(37,-51)),((37,-39),(29,-32),(16,-32)),
              ((9,-33),(5,-39),(4,-43)),fill=EDGE,edge=None)
        poly(c,T,[(9,-42),(18,-44),(32,-47),(29,-42),(17,-38)],WHITE)
        line(c,T,[(13,-35),(23,-35),(29,-38)],AMBER,1.6)
    else:
        line(c,T,[(5,-43),(13,-41),(25,-44),(35,-48)],EDGE,2.2)
        line(c,T,[(9,-39),(18,-38),(30,-43)],WHITE,1.2)
    # Oxide gathers in the shallow pits of the back bevel. Keep detail
    # sparse and irregular so the fresh surface stays clean and readable.
    for x,y,rx,ry,ang in [(-42,-88,2.5,1.3,-60),(-45,-55,3.2,1.5,-65),(-34,-36,2.6,1.3,32),(-30,-105,3.1,1.0,-27),(-18,-111,1.5,.8,-15)]:
        c.oval(T(x,y),rx,ry,'#64727a',None,angle=ang)
        c.line([T(x-rx*.6,y+ry),T(x+rx*.6,y+ry)],'#bac4c3',.8)
    # Sparse scuffed edges help distinguish soft cut metal from chrome liquid.
    for x,y in [(-39,-85),(-36,-31),(37,-33)]:
        line(c,T,[(x-3,y+2),(x,y),(x+4,y-1)],'#65747b',.9)


def sparks(c,center,q):
    r,h,k=q.ready,q.strike,q.flash
    if r>.03:
        # Gather warm, compact motes around the striking hand. Avoid a
        # full-screen flash or a persistent fire aura.
        for j in range(7):
            a=math.tau*(q.t*2+j/7); rr=22+7*(1-r)+4*math.sin(a*2)
            p=add(center,(rr*math.cos(a),rr*math.sin(a)))
            c.line([p,add(p,polar(3+5*r,math.degrees(a)))],YELLOW,1.1+1.0*r)
            if j%3==0:c.disk(p,1.7*r,HOT,None)
    if r<.03 and k<.03 and not q.move and not q.hurt:
        u=(q.t+.38)%1.
        life=math.sin(math.pi*min(1.,u*2.4))**2 if u<.42 else 0.
        if life>.02:
            p=add(center,(14+15*u,-9-28*u))
            c.disk(p,1.6*life,YELLOW,None)
    if k<=.025:return
    # A short, rolling reaction plume. Gray vapor is behind the yellow
    # flame tongues; the plume grows and dissipates during recovery. Use
    # soft-edged lobes rather than a generic comic star.
    x,y=center; origin=(x+17,y-3)
    travel=max(0.,(q.t-A)/(1-A)); bloom=.65+.35*k
    for j in range(6):
        a=-105+j*27
        p=add(origin,polar((20+j%3*9+18*travel)*bloom,a))
        radius=(8+3*(j%3)+10*travel)*k
        if radius>1:
            def Q(u,v):return add(p,rot((u*radius,v*radius),a))
            shape(c,Q,(-1.,.20),((-1.20,-.4),(-.64,-.90),(-.28,-.74)),
                  ((-.28,-1.26),(.48,-1.28),(.66,-.72)),((1.28,-.68),(1.28,.23),(.8,.48)),
                  ((.69,1.02),(-.26,1.06),(-.50,.68)),((-1.06,.75),(-1.15,.42),(-1.,.20)),
                  fill=(164,167,162,round(100*k)),edge=None)
    # Two intertwined, asymmetrical flame tongues, yellow core rather than
    # a sustained orange fire. Their tips move as the discharge decays.
    def F(u,v):return origin[0]+u*bloom,origin[1]+v*bloom
    flicker=math.sin(37*q.t)*4
    shape(c,F,(-14,5),((-8,-15),(4,-18),(9,-37-flicker)),
          ((18,-26),(16,-16),(19,-11)),((27,-20),(39,-24),(47,-23)),
          ((35,-15),(34,-6),(39,0)),((29,14),(13,18),(-1,13)),
          ((-11,11),(-15,10),(-14,5)),fill=(255,191,27,round(245*k)),edge=None)
    shape(c,F,(-8,4),((-2,-8),(9,-9),(12,-23)),
          ((15,-10),(20,-4),(31,-7)),((24,2),(19,9),(9,11)),
          ((2,12),(-8,10),(-8,4)),fill=(255,249,174,round(255*k)),edge=None)
    for j in range(8):
        ang=-106+j*24+8*math.sin(j*7.1)
        length=(19+13*(j%3)+7*math.sin(j*2.9))*(.65+.35*k)
        a=add(origin,polar(15+8*travel,ang)); b=add(origin,polar(length+17+13*travel,ang))
        n=polar(1.7*k,ang+90)
        c.poly([add(a,n),b,sub(a,n)],(255,194,41,round(230*k)),None)
        c.line([a,mix(a,b,.54)],(255,246,171,round(255*k)),.85+1.0*k)
        if j%2==0:
            p=add(origin,polar(length+24+12*travel,ang));c.disk(p,1.+1.1*k,(255,239,131,round(245*k)),None)


def render_frame(anim,i,n):
    q=pose(anim,i,n); c=Canvas(FRAME_SIZE)
    P,lean,j=solve(q)
    # Both upper thighs extend inside the lower body; paint the body last
    # to keep the hip overlaps clean and avoid obscuring the face.
    def foot_pitch(name):
        if not q.death:return 0.
        _,knee,foot=j[name]
        dx,dy=sub(foot,knee)
        angle=math.degrees(math.atan2(-dx,dy))
        # The toes follow the shin once the foot leaves its support pose.
        return angle*track(q.death,[(0,0),(.34,0),(.59,1),(1,1)])
    fp,np=foot_pitch('far_leg'),foot_pitch('near_leg')
    limb(c,j['far_leg'],True,True,fp);limb(c,j['far_arm'],True)
    limb(c,j['near_leg'],False,True,np)
    limb(c,j['near_arm'])
    body(c,P,q)
    if not q.death:
        sparks(c,j['near_arm'][-1],q)
        if q.hurt>.1:
            for k in range(3):
                c.line([P(-39-5*k,-89+6*k),P(-53-9*k,-100+5*k)],YELLOW,1+q.hurt)
    elif .08<q.death<.57:
        # A few last sparks escape the falling creature. They die away
        # before contact; the resting body is a solid, recognizable corpse.
        u=(q.death-.08)/.49; life=math.sin(math.pi*u)**2
        for k in range(4):
            a=add(P(19,-76),(-8+8*k+9*u,-9-14*u-5*(k%2)))
            b=add(a,(-3+2*k,-3-5*life))
            c.line([a,b],(255,195,41,round(210*life)),.7+life)
    im=c.finish()
    if q.death:
        # Ground contact is a translation of the articulated pose, not a
        # bitmap squash/rotation. Restrict early frames only if they
        # penetrate; after impact keep the corpse in contact.
        box=im.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox()
        if box and (box[3]>FLOOR+1 or q.death>=.64):
            im=anchored_death(im,FLOOR)
    return im

TRAITS=['enemy','science','elemental','chemical_element','sodium','alkali_metal']
ACTOR_METADATA={
    'actor':{'character_id':TARGET_NAME,'display_name':'Sodium Elemental'},
    'body':{'body_plan':'Biped','body_kind':'Standard','mass_class':'Light','locomotion_hint':'Walk','traits':TRAITS},
    'capabilities':{'traversal':{'walk':True}},'actions':{'default_preset':'sodium_elemental_burst'},
    'visual':{'default_pose':'idle','portrait':{'animation':'idle','frame':0}},'tags':TRAITS,
    'authoring_description':'A compact, soft silver-metal creature with a dull outer skin, bright cut face, and stylized sodium-yellow emission.',
    'gameplay_description':'A fast, light melee elemental. It compresses, gathers yellow sparks, and lunges forward in a brief reactive burst. The burst is cosmetic.',
    'animation_bindings':{'default':{'animation':'idle','events':[]},
        'locomotion.walk':{'animation':'walk','events':[]},'locomotion.run':{'animation':'run','events':[]},
        'combat.hurt':{'animation':'hit','events':[]},'combat.death':{'animation':'death','events':[]},
        'action.melee.primary':{'animation':'attack_side','events':[
            {'t':A,'event':'hitbox_active_start','source':'sodium_elemental.burst'},
            {'t':B,'event':'hitbox_active_end','source':'sodium_elemental.burst'}]}}}


def render(out_dir: str|Path,**opts):
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=render_frame,out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,auto_crop=False,actor_metadata=ACTOR_METADATA,
        body_metrics_fn=lambda w,h:body_metrics_for_box((76,62,191,238),w,h),
        animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
