"""Four material-specific monsters, with shared clip timing and publication.

All contours are authored in sprite pixels; the earth elemental uses the
canonical two-bone IK and surface gait. The other three are deforming flows,
not rigid humanoid limb chains. No simulation of fluids or fire is implied.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from pathlib import Path

from ._clockwork_enemy_art import Canvas, add, sub, mul, mix, rot, polar, phase, track, bezier
from ...authoring.skeleton import two_bone_ik_points
from ...authoring.surface_gait import Gait
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

FRAME_SIZE = (360, 300)
CX, GROUND = 150., 267.
LOOPS = {'idle', 'walk', 'run', 'death_idle'}

@dataclass(frozen=True)
class ElementSpec:
    target: str
    display_name: str
    element: str
    traits: tuple[str, ...]
    description: str
    gameplay: str
    run_speed: float
    move_style: str
    body_kind: str
    mass_class: str
    floating: bool
    attack_preset: str
    standing_height: float
    box: tuple[int, int, int, int]
    timing: tuple[float, float, float]

@dataclass(frozen=True)
class Pose:
    t: float = 0.
    cycle: float = 0.
    lean: float = 0.
    x: float = 0.
    y: float = 0.
    ready: float = 0.
    strike: float = 0.
    recover: float = 0.
    hurt: float = 0.
    death: float = 0.
    gait: float = 0.
    running: bool = False


def rows(spec):
    w,a,r = spec.timing
    locomotion = [('idle',24,53),('walk',24,50),('run',24,37)] if spec.floating else [('idle',16,80),('walk',16,75),('run',16,55)]
    return locomotion + [('notice',8,70),
            ('windup',max(10,round(w*25)),40),
            ('attack_side',max(24,round((w+a+r)*30)),33),
            ('hit',8,65),('death',18,70),('death_idle',6,180)]


def _choreography(spec, anim, i, n):
    t=phase(i,n,anim in LOOPS); p=math.tau*t
    if anim=='idle':return Pose(t,p,y=1.6*math.sin(p) if spec.floating else 0.)
    if anim in ('walk','run'):
        return Pose(t,p,lean=8 if anim=='walk' else 13,
                    y=3*math.sin(p) if spec.floating else 0.,gait=1.,running=anim=='run')
    if anim=='notice':
        u=track(t,[(0,0),(.48,1),(1,1)])
        return Pose(t,0.,lean=-4*u,ready=.32*u)
    if anim=='windup':
        u=track(t,[(0,0),(.78,1),(1,1)])
        return Pose(t,0.,lean=-12*u,x=-7*u,y=-5*u,ready=u)
    if anim=='attack_side':
        w,a,r=spec.timing; A=w/(w+a+r); B=(w+a)/(w+a+r)
        # This row is sampled at whole-move progress in the game's melee path.
        # Match the end of the dedicated windup at the active boundary.
        u=track(t,[(0,0),(A*.78,1),(A,1),(min(B,A+.055),0),(1,0)])
        hit=track(t,[(0,0),(A,0),(A+(B-A)*.23,1),(B,1),(B+(1-B)*.40,.12),(1,0)])
        rest=track(t,[(0,0),(B,0),(B+(1-B)*.24,1),(1,0)])
        return Pose(t,0.,lean=-12*u+14*hit+8*rest,x=-7*u+10*hit,y=-5*u+3*hit,
                    ready=u,strike=hit,recover=rest)
    if anim=='hit':
        u=math.sin(math.pi*t)
        return Pose(t,0.,lean=-17*u,x=-7*u,hurt=u)
    if anim in ('death','death_idle'):
        u=1. if anim=='death_idle' else track(t,[(0,0),(.20,.08),(.85,1),(1,1)])
        return Pose(t,0.,death=u)
    raise ValueError(anim)



def pose(spec, anim, i, n):
    q = _choreography(spec, anim, i, n)
    if not spec.floating:
        return q
    # Independent material clock. Use integral turns on cyclic clips and
    # match the windup endpoint to the whole-move attack row's active boundary.
    # The action envelope is still the existing catalog timing; the flow never
    # determines when a hit occurs. Fire runs faster than wind or water.
    turns = 2 if spec.element == 'fire' else 1
    t = q.t
    if anim == 'attack_side':
        w, a, r = spec.timing
        boundary = w / (w + a + r)
        material_t = t / boundary if t <= boundary else 1 + 2*(t-boundary)/(1-boundary)
    elif anim == 'death_idle':
        material_t = 0.
    else:
        material_t = t
    return replace(q, cycle=math.tau * ((turns * material_t) % 1.))


def path(start, *segments):
    """Sample an authored cubic contour using the existing Bezier utility."""
    points=[start]
    for a,b,end in segments:
        points.extend(bezier(points[-1],a,b,end,n=12)[1:])
    return points


def shape(c, P, start, segments, fill, edge=None, width=1.8):
    c.poly([P(*p) for p in path(start,*segments)],fill,edge,width)


def stroke(c, P, start, segments, fill, width=2.):
    c.line([P(*p) for p in path(start,*segments)],fill,width)


def angular_eye(c,P,x,y,w,h,eye,shadow,anger=0.,direction=1.):
    # No white eyeballs or pupils: small luminous slits inside recessed faces.
    c.poly([P(x-w-3,y-h-4),P(x+w+4,y-2),P(x+w+1,y+h+4),P(x-w,y+h+2)],shadow,None)
    c.poly([P(x-w,y-h-direction*(3+anger*2)),P(x+w,y-h+direction*(3+anger*2)),P(x+w-2,y+h),P(x-w+2,y+h-1)],eye,None)


def fluid_transform(q, *, origin=(CX,154.), material='air'):
    """Small, spatially varying deformation of the entire material.

    Keep the face readable and the collision anchor fixed. This is art-space
    advection, not a simulation or a rigid limb solver. Positive y is down.
    """
    def P(x,y):
        p=q.cycle
        bend=q.lean*(-y/105.)
        if material=='fire':
            # Wave travels up the flame, with a slower sway and independent
            # small flickers near the tips. The cinder mask moves much less.
            envelope=min(1.0,abs(y+32)/79.)
            bend+=envelope*(9*math.sin(p+y*.058)+3.3*math.sin(2*p+y*.10+.9))
            dx=x*(1+.065*math.sin(p+y*.041)*envelope)
            dy=y+envelope*(5*math.sin(p+y*.07+1.5)+2.1*math.sin(2*p+y*.10))
        elif material=='water':
            envelope=min(1.,abs(y+29)/75.)
            bend+=envelope*(8*math.sin(p-y*.052)+2.7*math.sin(2*p-y*.09))
            dx=x*(1+.08*math.sin(p-y*.041)*envelope)
            dy=y+envelope*(4.5*math.sin(p-y*.055+1.2))
        else:
            envelope=min(1.,abs(y+48)/83.)
            bend+=envelope*(8*math.sin(p-y*.067)+2.4*math.sin(2*p+y*.038))
            dx=x*(1+.07*math.sin(p+y*.046)*envelope)
            dy=y+2.6*math.sin(p+y*.058)*envelope
        return (origin[0]+q.x+dx+bend, origin[1]+q.y+dy)
    return P


def _life(f):
    """Zero-sized at both ends of a cyclic particle lifetime."""
    return math.sin(math.pi*f)**.75


def _air(c,q):
    P=fluid_transform(q,material='air')
    edge='#354755'; deep='#526977'; base='#8aa6b5'; pale='#d3e3e7'; rim='#f1f7ec'; shade='#647f90'
    hit=q.strike; ready=q.ready
    # The skirt is one tapered vortex. Thin winding bands wrap around its
    # broad cloud mantle, rather than separate discs resembling a robot.
    shape(c,P,(-54,-32),[((-73,1),(-40,30),(-29,48)),((-14,66),(-34,77),(-12,97)),
          ((2,109),(24,106),(27,101)),((4,98),(9,78),(28,59)),((47,40),(65,16),(57,-19)),
          ((39,-52),(-32,-57),(-54,-32))],shade,edge,2.2)
    # A procession of wind bands spirals down the taper. New bands enter
    # behind the cloud mantle and shrink into the tail; no band teleports.
    bands=sorted((j/6+q.cycle/math.tau/6)%1. for j in range(6))
    for f in bands:
        y=2+99*f
        w=52*(1-f)**.85+4
        shift=7*math.sin(q.cycle-4*f)
        depth=.64+.36*math.cos(q.cycle-5*f)
        thickness=(4+8*depth)*min(1.,f*9,(1-f)*8)
        if thickness<.35:continue
        shape(c,P,(-w+shift,y-thickness),
              [((-w-9+shift,y+1),(-w*.2+shift,y+thickness*1.8),(w*.76+shift,y+thickness*.56)),
               ((w+shift,y+1),(w+shift,y-thickness*.8),(w*.58+shift,y-thickness*1.2)),
               ((w*.24+shift,y+1),(-w*.55+shift,y+thickness*.36),(-w+shift,y-thickness))],
              tuple(round(v) for v in mix((138,166,181),(211,227,231),depth)),shade,1.0)
        stroke(c,P,(-w*.68+shift,y+2),[((-w*.35+shift,y+thickness*.8),(w*.15+shift,y+thickness),(w*.57+shift,y+thickness*.4))],rim,1.5)
    # Rear arm sweeps upward like a curled gust, with a tapering tip.
    armx=-67-18*ready+5*math.sin(q.cycle+.8); army=-35-22*ready+8*math.cos(q.cycle+.8)
    shape(c,P,(-31,-51),[((armx+15,-76),(armx-12,army-17),(armx-10,army+5)),
          ((armx-20,army+18),(armx-2,army+29),(armx+11,army+17)),
          ((armx+1,army+17),(armx-3,army+5),(armx+5,army-1)),
          ((armx+25,army-12),(-41,-31),(-31,-51))],base,edge,1.8)
    # Broad storm-cloud shoulders and a sharp curling crown.
    shape(c,P,(-58,-28),[((-76,-57),(-52,-86),(-26,-76)),
          ((-24,-98),(-2,-110),(18,-95)),((35,-114),(62,-92),(49,-77)),
          ((74,-78),(78,-50),(60,-33)),((53,-12),(34,-9),(16,-18)),
          ((-9,-5),(-42,-10),(-58,-28))],base,edge,2.4)
    shape(c,P,(-59,-45),[((-62,-67),(-42,-79),(-26,-66)),((-19,-94),(1,-99),(18,-85)),
          ((40,-101),(56,-90),(48,-77)),((61,-70),(68,-61),(56,-49)),
          ((29,-66),(-18,-42),(-59,-45))],pale,None)
    stroke(c,P,(-50,-50),[((-34,-58),(-20,-50),(-26,-40)),((-30,-32),(-40,-36),(-39,-42))],rim,2.8)
    v=math.sin(q.cycle+.8)
    stroke(c,P,(25,-82+3*v),[((39,-94-2*v),(53,-85+4*v),(42+3*v,-75))],rim,2.6)
    stroke(c,P,(-20+5*v,-78),[((-9,-88+3*v),(5,-87),(12+3*v,-80))],rim,1.7)
    # Face carved out of a dark storm pocket.
    shape(c,P,(-20,-56),[((-4,-67),(23,-67),(42,-55)),((39,-35),(26,-24),(9,-24)),
          ((-6,-30),(-20,-41),(-20,-56))],deep,None)
    angular_eye(c,P,5,-49,8,3,'#eafffa',edge,ready+hit)
    angular_eye(c,P,28,-48,7,3,'#eafffa',edge,ready+hit,-1.)
    # A hollow, wind-cut face with a wisp instead of a cartoon mouth.
    shape(c,P,(4,-33),[((12,-39),(21,-39),(34,-34)),((27,-30),(25,-25),(14,-27)),((10,-30),(8,-33),(4,-33))],edge,None)
    stroke(c,P,(-9,-56),[((-1,-66),(17,-64),(22,-59))],pale,1.8)
    stroke(c,P,(-55,-25),[((-43,-20),(-28,-23),(-23,-30))],rim,2.0)
    # Front arm is a curved ribbon that unfurls in the direction of attack.
    tip=(84+66*hit-19*ready+5*math.sin(q.cycle+.5)*(1-hit),-33-35*ready+16*hit+8*math.sin(q.cycle-1.1)*(1-hit))
    shape(c,P,(32,-39),[((54,-64),(tip[0]-24,tip[1]-24),tip),
          ((tip[0]+8,tip[1]+14),(tip[0]-12,tip[1]+24),(tip[0]-25,tip[1]+15)),
          ((tip[0]-5,tip[1]+11),(tip[0]-14,tip[1]-1),(tip[0]-26,tip[1]+2)),
          ((52,-18),(29,-15),(32,-39))],pale,edge,2.)
    stroke(c,P,(39,-36),[((60,-48),(tip[0]-20,tip[1]-12),(tip[0]-4,tip[1]-1))],rim,3.0)
    # Dust curls and wind shear follow the same continuous contour.
    if hit>.05:
        for j in range(2):
            y=-8+j*13
            stroke(c,P,(64,y),[((87,y-12),(113+28*hit,y-12),(123+39*hit,y-2))],base,2.7-j*.7)
    # Wind streaks orbit the outside of the funnel. The back half of
    # each orbit is omitted; the visible arc grows and disappears smoothly.
    for j in range(7):
        a=q.cycle+j*math.tau/7
        f=(j/7+q.cycle/math.tau)%1.
        y=-14+112*f
        w=67*(1-f)**.8+9
        visibility=max(0.,math.sin(a))*_life(f)
        if visibility<.08:continue
        x=w*math.cos(a)
        length=(9+19*visibility)*(1-.55*f)
        stroke(c,P,(x-length*.5,y+4),[((x-length*.1,y-2),(x+length*.28,y-3),(x+length*.5,y-1))],rim,.8+1.5*visibility)
    # Flecks of wind-borne dust curve away from the shoulders. Their size
    # carries the lifetime envelope so looping introduces no hard pop.
    for j in range(6):
        f=(q.cycle/math.tau+j/6)%1.
        k=_life(f)
        if k<.08:continue
        side=1 if j%2 else -1
        x=side*(57+27*f)+9*math.sin(math.tau*f+j)
        y=-57+95*f
        c.line([P(x-side*5*k,y+4*k),P(x,y)],pale,1.3*k+.5)


def _fire(c,q):
    P=fluid_transform(q,material='fire')
    edge='#512b32'; coal='#852e35'; red='#ce4832'; orange='#f58b35'; gold='#ffd05e'; hot='#fff2b1'
    r=q.ready; h=q.strike; wave=math.sin(q.cycle); flicker=math.sin(q.cycle+1.9); flicker2=math.sin(2*q.cycle-.7)
    # Rear tongues and shoulder, all attached to the main combustion mass.
    shape(c,P,(-22,70),[((-63,42),(-47,11),(-77,-16)),((-89,-33),(-83,-52),(-72,-67)),
          ((-72,-44),(-49,-41),(-50,-76)),((-46,-104),(-31,-115-7*wave),(-23+5*flicker,-125+4*flicker2)),
          ((-34,-95),(-3,-82),(-9,-54)),((8,-77),(24,-87),(21+4*wave,-105+5*flicker)),
          ((45,-88),(51,-68),(52,-49)),((71,-23),(59,30),(34,56)),
          ((18,80),(-2,98),(-22,70))],coal,edge,2.3)
    # Main flame silhouette: a horned, narrow waist with a flowing base.
    shape(c,P,(-24,78),[((-55,53),(-50,20),(-43,-5)),((-68,-28),(-42,-50),(-38,-70)),
          ((-33,-95),(-11,-98),(-14+5*flicker,-128-5*wave)),((4,-107),(12,-85),(5,-68)),
          ((25,-77),(28,-102),(47+5*flicker2,-111+7*flicker)),((39,-80),(65,-70),(56,-44)),
          ((79,-22),(55,8),(43,21)),((22,45),(37,65),(14,86)),
          ((0,94),(-10,88),(-24,78))],red,edge,2.0)
    shape(c,P,(-20,65),[((-42,40),(-25,15),(-32,-8)),((-43,-35),(-16,-53),(-8+4*flicker,-79-5*wave)),
          ((-4,-91),(0,-88),(1,-77)),((13,-58),(26,-59),(36+3*flicker,-83+6*flicker2)),
          ((40,-52),(57,-33),(39,-9)),((20,19),(37,34),(20,60)),((7,80),(-9,81),(-20,65))],orange,None)
    shape(c,P,(-9,67),[((-24,46),(-6,19),(-13,-3)),((-23,-27),(0,-36),(3,-54)),
          ((10,-37),(29,-36),(26,-13)),((9,10),(26,22),(11,49)),((3,65),(0,72),(-9,67))],gold,None)
    shape(c,P,(-4,55),[((-10,41),(3,27),(0,12)),((16,29),(11,44),(-4,55))],hot,None)
    # Facial expression is formed from a single dark cinder mask.
    shape(c,P,(-22,-42),[((-3,-56),(22,-51),(42,-40)),((37,-17),(19,-2),(5,-8)),
          ((-11,-10),(-24,-25),(-22,-42))],coal,None)
    angular_eye(c,P,0,-36,10,4,hot,edge,r+h)
    angular_eye(c,P,25,-35,8,4,hot,edge,r+h,-1.)
    c.poly([P(-8,-18),P(2,-23),P(15,-18),P(28,-21),P(26,-9-4*h),P(14,-4-6*h),P(4,-8),P(-5,-11)],edge,None)
    c.poly([P(0,-18),P(5,-17),P(3,-10)],gold,None)
    c.poly([P(19,-17),P(24,-18),P(21,-9)],gold,None)
    # Cracks in the mask glow through like molten stone.
    c.line([P(-19,-41),P(-12,-31),P(-17,-24)],orange,1.8)
    c.line([P(31,-47),P(28,-43),P(35,-39)],gold,1.4)
    stroke(c,P,(-34,13),[((-45,35),(-25,51),(-21,59))],orange,3.2)
    stroke(c,P,(39,21),[((25,39),(29,57),(17,72))],gold,2.0)
    # A second, smaller tongue curls back as a shoulder and claw.
    shape(c,P,(-36,-23),[((-56,-25),(-79,-45-14*r),(-75+3*flicker,-65-8*r-6*wave)),((-69,-49),(-52,-55),(-49+3*wave,-72-8*r+5*flicker2)),((-41,-53),(-48,-40),(-26,-27)),((-19,-14),(-24,-9),(-36,-23))],red,edge,1.7)
    stroke(c,P,(-43,-27),[((-56,-35),(-68,-44),(-68,-53-8*r))],gold,2.8)
    # Long forward fire claw. A sweeping tongue during the tell becomes a
    # single directional jet during the active window.
    ex=80+60*h-15*r+5*wave*(1-h); ey=-24-42*r+8*h+7*flicker*(1-h)
    shape(c,P,(31,-30),[((52,-47),(ex-19,ey-20),(ex,ey)),
          ((ex+10,ey-9),(ex+13,ey-15),(ex+22,ey-26)),
          ((ex+15,ey-2),(ex+14,ey+8),(ex+4,ey+13)),
          ((ex-14,ey+23),(51,5),(32,5)),((24,-5),(27,-16),(31,-30))],red,edge,1.7)
    shape(c,P,(36,-23),[((55,-36),(ex-18,ey-10),(ex+3,ey+2)),
          ((ex-4,ey+14),(54,0),(36,-3)),((29,-8),(30,-14),(36,-23))],gold,None)
    stroke(c,P,(47,-20),[((61,-20),(ex-12,ey),(ex+2,ey+2))],hot,3.3)
    # Incandescent curls move upward *inside* the flame, so even a
    # small sprite looks alive without relying on detached sparks.
    for j in range(3):
        f=(q.cycle/math.tau+j/3)%1.
        k=_life(f)
        if k<.08:continue
        y=66-62*f; x=-5+9*math.sin(math.tau*f+j*.9)
        length=13*k
        stroke(c,P,(x,y),[((x-5*k,y-length*.3),(x+5*k,y-length*.65),(x+2*k,y-length))],hot,1.2+2*k)
    # Deterministic embers rise along curved paths with a visible hot head
    # and a cooling short trail. Lifetimes close smoothly at loop edges.
    for j in range(10):
        f=(q.cycle/math.tau+j/10)%1.
        k=_life(f)
        if k<.10:continue
        side=1 if j%2 else -1
        x=side*(37+18*f)+9*math.sin(math.tau*f+j*1.9)
        y=66-171*f
        length=(4+7*f)*k
        c.line([P(x-2*side,y+length),P(x,y)],red if f>.70 else orange,1.1+1.2*k)
        c.oval(P(x,y),1.7*k,3*k,gold if f<.65 else orange,None,angle=side*18)
        if f<.55:c.disk(P(x,y-1),.95*k,hot,None)
    if h>.05:
        # Fork the leading tongue into a flame jet rather than a blunt fist.
        shape(c,P,(ex-28,ey+6),[((ex-9,ey+18),(ex+7,ey+12),(ex+20,ey+24)),((ex+10,ey+8),(ex+15,ey+3),(ex+4,ey-1)),((ex-7,ey+5),(ex-18,ey+5),(ex-28,ey+6))],orange,None)
        for j in range(4):
            x=ex+8+j*5; y=ey+(j-1.5)*9
            c.line([P(x-5,y+3),P(x,y)],hot if j%2 else orange,2.2)


def _water(c,q):
    P=fluid_transform(q,origin=(CX,159.),material='water')
    edge='#203f58'; deep='#235477'; blue='#2d83a2'; teal='#56b5c4'; ice='#ace3dc'; foam='#edf9e9'
    r=q.ready; h=q.strike; f=math.sin(q.cycle); roll=math.sin(q.cycle+1.2)
    # Serpentine wave, not a droplet. Its body coils forward at the bottom,
    # then rises behind the head as a breaking crest.
    shape(c,P,(-64,83),[((-41,84),(-18,66),(-28,43)),((-46,15),(-61,-13),(-44,-41)),
          ((-24,-65),(-9,-83),(20,-89)),((50,-96),(71,-78),(72,-52)),
          ((66,-30),(46,-29),(35,-45)),((43,-58),(34,-66),(21,-55)),
          ((3,-42),(12,-22),(32,4)),((52,32),(70,66),(45,82)),
          ((23,96),(-36,100),(-64,83))],blue,edge,2.2)
    shape(c,P,(-50,82),[((-19,83),(2,61),(-11,40)),((-36,5),(-41,-17),(-24,-42)),
          ((-4,-71),(30,-81),(51,-68)),((63,-60),(61,-47),(53,-43)),
          ((48,-61),(27,-66),(13,-51)),((-9,-32),(6,-6),(22,15)),
          ((46,41),(43,63),(23,75)),((9,88),(-26,92),(-50,82))],teal,None)
    shape(c,P,(-33,73),[((-9,68),(2,46),(-6,28)),((12,40),(26,57),(12,72)),
          ((4,83),(-14,86),(-33,73))],deep,None)
    # Creamy foam rolls along the crest, with dark inner curl and scallops.
    shape(c,P,(-41,-43),[((-34,-65),(-7,-90),(18,-94)),((45,-105),(74,-91),(76+4*roll,-69+6*f)),
          ((88+4*roll,-63+6*f),(76,-52),(73+4*roll,-48+4*f)),((75,-35),(58,-30),(50+4*roll,-40+4*f)),
          ((58,-43),(55,-56),(44,-61)),((38,-68),(27,-66),(18,-60)),
          ((14,-70),(3,-66),(-6,-56)),((-20,-63),(-30,-45),(-41,-43))],foam,edge,1.4)
    # Rolling foam lobes and a small traveling crest highlight.
    k=math.sin(q.cycle-.8)
    stroke(c,P,(-23,-74+2*k),[((-8,-87+2*k),(9,-89),(24,-86+3*k))],ice,2.1)
    stroke(c,P,(37+3*roll,-87+2*k),[((51,-84+4*k),(64+2*roll,-77),(63+3*roll,-65+4*f)),((62,-59),(58,-58),(55,-60))],ice,2.5)
    stroke(c,P,(-38,-25),[((-23,-44),(-12,-44),(-4,-41)),((5,-35),(8,-26),(3,-18))],ice,3.2)
    stroke(c,P,(-28,13),[((-17,32),(-4,37),(-2,53))],ice,2.5)
    stroke(c,P,(28,47),[((40,62),(25,78),(5,80))],ice,3.)
    # A serpentine head and projecting jaw grow out of the current. The
    # single visible eye is under a hard brow, unlike the other elementals.
    shape(c,P,(-8,-34),[((7,-51),(32,-49),(45,-37)),((55,-34),(56,-21),(67,-18)),
          ((60,-10),(48,-10),(42,-11)),((47,2),(38,8),(25,3)),((5,-2),(-10,-19),(-8,-34))],deep,edge,1.6)
    c.poly([P(5,-34),P(17,-44),P(38,-39),P(46,-32),P(23,-34),P(11,-28)],blue,None)
    angular_eye(c,P,29,-30,11,4,foam,edge,r+h)
    c.poly([P(34,-11),P(48,-16),P(63,-17),P(53,-8),P(43,-6)],edge,None)
    for x,y in [(45,-13),(53,-14),(60,-15)]:
        c.poly([P(x-3,y),P(x+2,y),P(x,y+5)],foam,None)
    stroke(c,P,(7,-13),[((15,-7),(24,-3),(33,-6))],ice,1.9)
    # Advect bubbles and short, tapered surface streaks along the
    # existing body contour. The path starts behind the crest, sweeps down
    # the body and curls into its base. It is sampled by the existing Bezier
    # utility rather than introducing a second path/curve implementation.
    current=path((-16,-58),((-40,-36),(-33,-15),(-23,8)),
                 ((-17,28),(9,38),(12,58)),((17,75),(3,81),(-26,86)))
    for j in range(6):
        u=(q.cycle/math.tau+j/6)%1.
        k=_life(u)
        if k<.08:continue
        idx=u*(len(current)-1)
        m=int(idx); a=mix(current[m],current[min(m+1,len(current)-1)],idx-m)
        tail=max(0.,idx-3*k); m=int(tail)
        b=mix(current[m],current[min(m+1,len(current)-1)],tail-m)
        stroke(c,P,b,[(b,mix(b,a,.75),a)],ice,1.1+1.6*k)
        if j%2==0:c.oval(P(a[0]+5,a[1]-2),2.5*k,3.2*k,foam,None)
    stroke(c,P,(-13,3),[((-3,17),(14,20),(17,33))],deep,2.5)
    # Long fin-like arm forms a breaking lateral wave. Its curl is open at
    # the end and its entire mass remains connected to the body.
    ex=75+58*h-15*r+4*f*(1-h); ey=1-42*r+15*h+8*roll*(1-h)
    shape(c,P,(17,7),[((31,-14),(ex-36,ey-29-12*h),(ex-8,ey-22-18*h)),
          ((ex+20,ey-20-18*h),(ex+26,ey-6),(ex+10,ey+8+8*h)),
          ((ex+6,ey-6),(ex-8,ey-8),(ex-12,ey+1)),
          ((ex-17,ey+13),(37,38),(18,32)),((6,26),(8,17),(17,7))],blue,edge,2.)
    shape(c,P,(25,5),[((42,-5),(ex-30,ey-22-10*h),(ex-5,ey-16-14*h)),
          ((ex+13,ey-13-14*h),(ex+18,ey-6),(ex+10,ey+3+6*h)),
          ((ex+3,ey-2),(ex-6,ey-5),(ex-12,ey-1)),((ex-22,ey+4),(40,20),(25,18)),
          ((21,15),(21,10),(25,5))],teal,None)
    stroke(c,P,(37,0),[((ex-34,ey-21-11*h),(ex+4,ey-21-15*h),(ex+12,ey-5))],foam,4.)
    # Foam flows along the base and rolls off the crest. The drops are
    # baked sprites, with a simple stylized parabolic path and no hitboxes.
    stroke(c,P,(-53,84),[((-27,92),(4,91),(22,83))],foam,3.4)
    for j in range(6):
        u=(q.cycle/math.tau+j/6)%1.; k=_life(u)
        if k<.08:continue
        x=-48+79*u; y=86+4*math.sin(math.tau*u)
        c.oval(P(x,y),5*k,2.4*k,ice,None)
    for j in range(6):
        u=(q.cycle/math.tau+j/6)%1.; k=_life(u)
        if k<.08:continue
        side=-1 if j%3==0 else 1
        if side>0:
            x=64+31*u+5*math.sin(j*2.2);y=-65-34*u+77*u*u
        else:
            x=-39-19*u;y=19+45*u*u
        c.oval(P(x,y),2.0*k,4.3*k,ice,edge,.55,angle=-side*(35-49*u))
        c.disk(P(x-.5,y-1.2),.85*k,foam,None)
    if h>.05:
        for j in range(5):
            x=ex+8+j*4; y=ey-17-j*6
            c.oval(P(x,y),2.6,4.2,ice,edge,.7,35)


# Earth is the only rigid-limbed member of the family. All four limbs use
# canonical IK, and the contact goals come from the existing Gait class.
EARTH_GAIT=Gait(stride=37,stance=.66,lift=11)
EARTH_RUN=Gait(stride=44,stance=.60,lift=13)
EARTH_LEG=(29.,30.)
EARTH_ARM=(37.,36.)
STONE_EDGE='#353b3a'
STONE_PALE='#a4a18c'
STONE='#777b70'
STONE_DARK='#4d5650'
STONE_SHADOW='#3d4843'
MOSS='#627c4e'
MOSS_LIGHT='#92a768'


def _rock(c,center,rx,ry,angle=0,seed=0,far=False,moss=False):
    def P(x,y):return add(center,rot((x*rx,y*ry),angle))
    # Fixed angular planes; no procedural frame-to-frame random noise.
    pts=[(-.90,-.47),(-.47,-.97),(.47,-.89),(.94,-.38),(1.,.36),(.54,.91),(-.48,1.),(-1.,.39)]
    if seed%2:pts=[(-1.,-.34),(-.72,-.90),(.27,-1.),(.84,-.60),(1.,.26),(.44,1.),(-.63,.83),(-.90,.40)]
    poly=[P(*p) for p in pts]
    c.poly(poly,STONE_DARK if far else STONE,STONE_EDGE,2.)
    hub=P(-.15,-.24)
    c.poly([poly[0],poly[1],poly[2],hub],STONE if far else STONE_PALE,None)
    c.poly([hub,poly[2],poly[3],poly[4],P(.32,.20)],STONE if far else '#8c8d79',None)
    c.poly([hub,P(.32,.20),poly[4],poly[5],poly[6]],STONE_SHADOW if far else STONE_DARK,None)
    c.line([P(-.72,.40),P(-.32,.07),P(-.02,.22),P(.30,-.03)],STONE_EDGE,1.2)
    c.line([P(-.58,-.53),P(-.27,-.68),P(.18,-.63)],STONE_PALE if far else '#c1bb9f',1.4)
    if moss:
        c.poly([P(-.81,-.37),P(-.48,-.83),P(.07,-.82),P(-.05,-.53),P(-.34,-.44),P(-.39,-.19)],MOSS,None)
        c.line([P(-.64,-.49),P(-.43,-.61),P(-.18,-.60)],MOSS_LIGHT,1.8)


def earth_joints(q):
    hip=(CX+q.x,GROUND-63+3*math.cos(2*q.cycle)*q.gait+7*q.ready+5*q.recover)
    def P(x,y):return add(hip,rot((x,y),q.lean*.65))
    gait=EARTH_RUN if q.running else EARTH_GAIT
    def chain(root,goal,lengths,bend):return (root,*two_bone_ik_points(root,goal,*lengths,bend,extension_margin=.1))
    # The feet use actual solved endpoints, not requested positions.
    def foot(side,offset):
        dx,dy=gait.foot_offset(q.t,offset) if q.gait else (0.,0.)
        return (CX+side*23+dx+side*4*q.strike,GROUND-12-dy)
    far_leg=chain(P(-22,0),foot(-1,.5),EARTH_LEG,1.)
    near_leg=chain(P(22,0),foot(1,0.),EARTH_LEG,1.)
    # Heavy stone arms raise above the face, then slam down and forward.
    sw=10*math.sin(q.cycle)*q.gait
    far_goal=(CX-53-8*q.ready+46*q.strike+sw,GROUND-83-80*q.ready+5*q.strike)
    near_goal=(CX+55+40*q.strike-12*q.ready-sw,GROUND-75-87*q.ready+29*q.strike)
    far_arm=chain(P(-36,-64),far_goal,EARTH_ARM,-1.)
    near_arm=chain(P(31,-61),near_goal,EARTH_ARM,-1.)
    return P,(far_leg,near_leg,far_arm,near_arm)


def _earth(c,q):
    # Same geometric pieces drive living and collapse poses. The painter
    # assigns collapse goals to slabs, without altering the live IK solver.
    if q.death>0.:
        P,(fl,nl,fa,na)=earth_joints(Pose())
    else:
        P,(fl,nl,fa,na)=earth_joints(q)
    u=q.death
    def rock(center,rx,ry,angle=0,seed=0,far=False,moss=False):
        if u:
            # Fall outward with no increase in size. Land on the actual
            # floor, including the rotation-dependent extent of the slab.
            dx=center[0]-CX
            angle0=angle
            angle=angle0+(-1 if dx<0 else 1)*36*u
            height=min(ry,17.)
            rx=rx*(1-.08*u);ry=ry+(height-ry)*u
            extent=max(abs(math.sin(math.radians(angle))*rx),abs(math.cos(math.radians(angle))*ry))
            tx=CX+dx*1.10
            ty=GROUND-extent-4-abs(dx)*.04
            center=mix(center,(tx,ty),u)
        _rock(c,center,rx,ry,angle,seed,far,moss)
    def chain(joints,radii,far):
        a,b,e=joints
        for k,(lo,hi,r) in enumerate(zip((a,b),(b,e),radii)):
            ang=math.degrees(math.atan2(hi[1]-lo[1],hi[0]-lo[0]))-90
            if not u:c.line([lo,hi],STONE_SHADOW,9.)
            rock(mix(lo,hi,.53),r,math.dist(lo,hi)*.60,ang,k,far,k==0 and not far)
    for j,far in [(fl,True),(nl,False)]:
        chain(j,(15,13),far)
        rock(add(j[-1],(7,0)),22,10,0,seed=1,far=far)
    chain(fa,(21,18),True)
    rock(fa[-1],23,22,-12,seed=1,far=True)
    rock(P(-3,-19),40,37,q.lean*.65,seed=1)
    rock(P(-26,-54),35,38,-21+q.lean*.65,seed=0,moss=True)
    rock(P(18,-58),39,43,12+q.lean*.65,seed=1,moss=True)
    rock(P(9,-30),35,25,-7+q.lean*.65,seed=1)
    rock(P(13,-100),33,31,q.lean*.65,seed=1,moss=True)
    if u==0.:
        c.poly([P(-9,-109),P(6,-116),P(35,-109),P(42,-96),P(29,-92),P(3,-95),P(-12,-100)],STONE_SHADOW,STONE_EDGE,1.6)
        angular_eye(c,P,5,-101,8,3,'#e2d18f',STONE_EDGE,q.ready+q.strike)
        angular_eye(c,P,27,-99,8,3,'#e2d18f',STONE_EDGE,q.ready+q.strike,-1.)
        c.poly([P(11,-94),P(19,-102),P(26,-92),P(21,-87),P(11,-89)],STONE_PALE,STONE_EDGE,1.)
        c.line([P(-1,-82),P(9,-86),P(18,-83),P(31,-87)],STONE_EDGE,3.)
        c.line([P(34,-112),P(28,-117),P(26,-123)],STONE_EDGE,1.7)
        c.line([P(-19,-95),P(-9,-88),P(-13,-76)],STONE_EDGE,1.5)
        c.line([P(2,-46),P(7,-51),P(4,-62)],STONE_EDGE,1.5)
        c.line([P(-5,-28),P(-17,-23),P(-19,-15)],STONE_EDGE,1.4)
        c.line([P(5,-78),P(20,-77)],STONE_PALE,1.7)
    chain(na,(24,21),False)
    rock(na[-1],27,24,16+28*q.strike,seed=0,moss=True)
    if q.strike>.12:
        for i in range(5):
            x,y=add(na[-1],(15+i*7,14-(i%3)*13))
            c.poly([(x-3,y),(x+1,y-6),(x+6,y-2),(x+3,y+4)],STONE_PALE,STONE_EDGE,.8)

def render_frame(spec,anim,i,n):
    q=pose(spec,anim,i,n); c=Canvas(FRAME_SIZE)
    painters={'air':_air,'fire':_fire,'water':_water,'earth':_earth}
    painters[spec.element](c,q)
    im=c.finish()
    if spec.floating and q.death:
        # Air disperses; flame extinguishes; water collapses and drains.
        # The rest pose is deliberately transparent, not a toppled humanoid.
        u=q.death
        sx,sy={'air':(1+.32*u,1-.35*u),'fire':(1-.42*u,1-.64*u),'water':(1+.26*u,1-.82*u)}[spec.element]
        # Resample around the same body anchor; preserve transparent canvas.
        from PIL import Image
        center=(CX,154.)
        im=im.transform(FRAME_SIZE,Image.Transform.AFFINE,(1/sx,0,center[0]*(1-1/sx),0,1/sy,center[1]*(1-1/sy)),resample=Image.Resampling.BICUBIC)
        im.putalpha(im.getchannel('A').point(lambda a:round(a*(1-u))))
    return im


def metadata(spec):
    traits=['enemy','fantasy',*spec.traits]
    w,a,r=spec.timing; total=w+a+r
    return {'actor':{'character_id':spec.target,'display_name':spec.display_name},
            'body':{'body_plan':'Floating' if spec.floating else 'Biped','body_kind':spec.body_kind,
                    'mass_class':spec.mass_class,'locomotion_hint':'Fly' if spec.floating else 'Walk','traits':traits},
            'actions':{'default_preset':spec.attack_preset},
            'visual':{'default_pose':'idle','portrait':{'animation':'idle','frame':0}},
            'tags':traits,'authoring_description':spec.description,'gameplay_description':spec.gameplay,
            'animation_bindings':{'default':{'animation':'idle','events':[]},
               'locomotion.walk':{'animation':'walk','events':[]},'locomotion.run':{'animation':'run','events':[]},
               'combat.hurt':{'animation':'hit','events':[]},'combat.death':{'animation':'death','events':[]},
               'action.melee.primary':{'animation':'attack_side','events':[
                   {'t':w/total,'event':'hitbox_active_start','source':spec.target+'.attack'},
                   {'t':(w+a)/total,'event':'hitbox_active_end','source':spec.target+'.attack'}]}}}


def publish_spec(spec,out_dir: str|Path,**opts):
    clips=rows(spec)
    out=build_sheet(target=spec.target,rows=clips,render_fn=lambda a,i,n:render_frame(spec,a,i,n),
                    out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,actor_metadata=metadata(spec),
                    body_metrics_fn=lambda w,h:body_metrics_for_box(spec.box,w,h),
                    animation_key_map={a:a for a,_,_ in clips},sits_on_ground=not spec.floating)
    return [out[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
