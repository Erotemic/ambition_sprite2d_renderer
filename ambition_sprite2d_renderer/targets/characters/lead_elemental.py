"""Lead, a low-slung, heavy cast-metal elemental for the Science Dimension.

A squat, four-point cast-lead beast with an integral face and heavy support pads.
Lead's toxicity is not simulated here; the attack is an existing melee slam.
No chemical symbols, clothing, emission glow, or bitmap-based death poses.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from ._clockwork_enemy_art import (
    Canvas, add, sub, mul, mix, rot, unit, perp, bezier, phase,
    track, anchored_death,
)
from ...authoring.skeleton import two_bone_ik_points
from ...authoring.surface_gait import Gait
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'lead_elemental'
FRAME_SIZE = (384, 300)
CX, FLOOR = 155., 263.
ARMS, LEGS = (57., 60.), (34., 36.)
WINDUP, ACTIVE, RECOVERY = .86, .20, 1.04
TOTAL = WINDUP + ACTIVE + RECOVERY
A, B = WINDUP / TOTAL, (WINDUP + ACTIVE) / TOTAL
ROWS = [('idle',24,75), ('walk',24,90), ('run',24,70), ('notice',12,55),
        ('windup',29,30), ('attack_side',70,30), ('hit',10,60),
        ('death',32,55), ('death_idle',1,200)]
LOOPS = {'idle', 'walk', 'run', 'death_idle'}
WALK = Gait(stride=25, stance=.78, lift=6.)
RUN = Gait(stride=34, stance=.72, lift=9.)
EDGE = (25,29,38)
SHADOW = (46,52,64)
OXIDE = (74,82,94)
BASE = (91,103,119)
MID = (121,135,150)
LIGHT = (158,172,183)
PALE = (196,208,216)


@dataclass(frozen=True)
class Pose:
    t: float = 0.
    move: float = 0.
    alert: float = 0.
    ready: float = 0.
    strike: float = 0.
    recover: float = 0.
    hurt: float = 0.
    death: float = 0.
    impact: float = 0.


def pose(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    if anim in ('idle','walk','run'):
        return Pose(t % 1., move={'idle':0.,'walk':.65,'run':1.}[anim])
    if anim == 'notice':
        return Pose(alert=track(t,[(0,0),(.43,1),(1,1)]))
    if anim == 'windup':
        return Pose(ready=track(t,[(0,0),(.82,1),(1,1)]))
    if anim == 'attack_side':
        launch = A - .12/TOTAL
        return Pose(t=t%1.,ready=track(t,[(0,0),(.82*launch,1),(launch,1),(A,0),(1,0)]),
                    strike=track(t,[(0,0),(launch,0),(A,1),(B,1),(B+.13,.78),(1,0)]),
                    recover=track(t,[(0,0),(B,0),(B+.17,1),(1,0)]),
                    impact=track(t,[(0,0),(A-.001,0),(A,1),(B,.77),(B+.24,0),(1,0)]))
    if anim == 'hit':
        return Pose(hurt=math.sin(math.pi*t))
    if anim in ('death','death_idle'):
        return Pose(death=1. if anim=='death_idle' else t)
    raise ValueError(anim)


def chain(root, goal, lengths, bend):
    return root, *two_bone_ik_points(root, goal, *lengths, bend, extension_margin=.08)


def solve(q):
    p=math.tau*q.t
    r,h,z=q.ready,q.strike,q.hurt
    if q.death:
        k=lambda *keys:track(q.death,keys)
        center=(CX+k((0,0),(.15,-6),(.36,8),(.67,19),(1,19)),
                FLOOR+k((0,-76),(.15,-77),(.37,-61),(.58,-25),(.73,-31),(.90,-23),(1,-23)))
        lean=k((0,0),(.15,-7),(.37,13),(.58,10),(.73,4),(1,3))
    else:
        center=(CX-6*r+12*h-6*z,
                FLOOR-76+1.2*math.sin(p)*(1-q.move)+1.6*q.move*math.sin(2*p)-12*r+6*h+4*q.recover)
        lean=-27*r+10*h-7*z+2.2*q.move*math.sin(p)-4*q.alert
    def P(x,y): return add(center,rot((x,y),lean))
    gait=RUN if q.move>.9 else WALK
    def contact(x,phase_offset,dy):
        dx,lift=gait.foot_offset(q.t,phase_offset) if q.move else (0.,0.)
        return (CX+x+dx,FLOOR-dy-lift)
    fr,nr=contact(-43,.50,12),contact(-68,0.,12)
    ff,nf=contact(55,0.,15),contact(91,.50,15)
    if q.death:
        k=lambda *keys:track(q.death,keys)
        fr=(CX+k((0,-43),(.37,-43),(.7,-75),(1,-75)),FLOOR-12)
        nr=(CX+k((0,-68),(.37,-68),(.7,-98),(1,-98)),FLOOR-12)
        ff=(CX+k((0,57),(.26,72),(.6,96),(1,96)),FLOOR-15)
        nf=(CX+k((0,88),(.26,111),(.6,135),(1,135)),FLOOR-15)
    else:
        nf=mix(mix(nf,(CX+65,FLOOR-100),r),(CX+119,FLOOR-15),h)
        nf=add(nf,(0,-7*z-4*q.alert))
        ff=mix(mix(ff,(CX+49,FLOOR-93),r),(CX+74,FLOOR-15),h)
    return P,lean,{
        'far_leg':chain(P(-35,8),fr,LEGS,-1.),
        'near_leg':chain(P(-64,12),nr,LEGS,-1.),
        'far_arm':chain(P(45,-25),ff,ARMS,1.),
        'near_arm':chain(P(27,-22),nf,ARMS,1.),
    }


def color(a,b,t):
    return tuple(round(v) for v in mix(a,b,t))


def path(start,*segments):
    points=[start]
    for a,b,end in segments:
        points.extend(bezier(points[-1],a,b,end,n=12)[1:])
    return points


def shape(c,P,start,*segments,fill,edge=EDGE,width=1.8):
    c.poly([P(*p) for p in path(start,*segments)],fill,edge,width)


def poly(c,P,pts,fill,edge=None,width=1.3):
    c.poly([P(*p) for p in pts],fill,edge,width)


def line(c,P,pts,fill,width=1.5):
    c.line([P(*p) for p in pts],fill,width)


def dent(c,P,x,y,w,h):
    # Concave imperfections in the soft cast surface, not painted rivets.
    shape(c,P,(x-w,y),((x-w*.8,y-h),(x+w*.25,y-h),(x+w,y-h*.2)),
          ((x+w*.65,y+h*.6),(x-w*.4,y+h*.85),(x-w,y)),fill=OXIDE,edge=None)
    line(c,P,[(x-w*.70,y+h*.22),(x-w*.10,y+h*.50),(x+w*.55,y+h*.18)],LIGHT,.85)


def support(c,j,far=False,rear=False,pitch=0.):
    # The load-bearing limbs end in broad flattened lead pads rather than
    # humanoid fists or shoes. The root is buried inside the body casting.
    a,b,e=j
    u=unit(sub(b,a)); v=unit(sub(e,b)); nu=perp(u); nv=perp(v)
    tangent=unit(add(u,v)); normal=perp(tangent)
    a=sub(a,mul(u,14.)) if u[1]>0 else a
    r0,r1,r2=(29.,25.,22.) if rear else (36.,33.,29.)
    if far:r0*=.83;r1*=.85;r2*=.86
    def H(x,y):return add(e,rot((x,y),pitch))
    w=25 if rear else 36; bottom=12 if rear else 15
    # Keep the two side curves on opposite sides of the contact pad.
    cap_sign=1 if rot(nv,-pitch)[0]>=0 else -1
    def ridge(f):
        aa=add(a,mul(nu,r0*f));bb=add(b,mul(normal,r1*f))
        # The proximal metal is buried in the cast mass. On collapse it
        # cannot protrude down through the ground even if the knee folds up.
        aa=(aa[0],min(aa[1],FLOOR-5))
        ee=H(cap_sign*w*.72*f,-8)
        return path(aa,(mix(aa,bb,.38),sub(bb,mul(tangent,9)),bb),
                    (add(bb,mul(tangent,9)),mix(bb,ee,.64),ee))
    l,r=ridge(-1),ridge(1)
    # The broad foot is a continuation of the limb, not an attached block.
    # Build the outer cap with rounded casting corners and a flat sole.
    left_first=math.dist(l[-1],H(-w,0))<math.dist(l[-1],H(w,0))
    side=-1 if left_first else 1
    def F(x,y):return H(side*x,y)
    cap=path(l[-1],(F(w-8,-14),F(w+3,-11),F(w+5,-3)),
             (F(w+8,4),F(w+3,bottom),F(w-3,bottom)),
             (F(w*.3,bottom),F(-w*.48,bottom),F(-w+4,bottom)),
             (F(-w-5,bottom),F(-w-7,5),F(-w-2,-3)),
             (F(-w-1,-10),F(-w+7,-15),r[-1]))
    base=OXIDE if far else BASE
    c.poly(l+cap[1:]+r[::-1],base,EDGE,2.0)
    # Material reflection along the entire limb and over the thick pad.
    ll,rr=ridge(-.69),ridge(.30)
    light_cap=path(ll[-1],(F(w-10,-11),F(w+1,-9),F(w+1,-2)),
                   (F(w-3,4),F(w*.4,4),F(0,3)),
                   (F(-w*.4,3),F(-w+6,0),rr[-1]))
    c.poly(ll+light_cap[1:]+rr[::-1],MID if far else LIGHT,None)
    c.poly(ridge(.51)+ridge(.88)[::-1],SHADOW if far else OXIDE,None)
    # Cast-metal lip and broad dark lower plane, with no seam across the
    # wrist/ankle. The contact edge is gently warped at the corners.
    shape(c,H,(-w-1,4),((-w*.6,9),(-w*.22,7),(0,7)),
          ((w*.45,8),(w*.8,6),(w+3,3)),((w+2,10),(w-3,bottom),(w-8,bottom)),
          ((w*.15,bottom),(-w*.45,bottom),(-w+6,bottom)),
          ((-w-2,bottom),(-w-4,8),(-w-1,4)),fill=SHADOW if far else OXIDE,edge=None)
    line(c,H,[(-w+5,bottom-2),(0,bottom-1),(w-6,bottom-2)],SHADOW,1.2)
    line(c,H,[(w*.35,-7),(w*.57,-5),(w*.70,-1)],MID if far else PALE,1.1)
    if not far:dent(c,H,-w*.40,1,5,1.6)


def casting(c,P,q):
    # One sloped, irregular ingot silhouette. The front is the head: no
    # neck, helmet, separate humanoid head, or round torso.
    shape(c,P,(-93,-15),((-99,-27),(-100,-58),(-94,-72)),
          ((-91,-81),(-76,-93),(-62,-96)),((-40,-97),(-14,-97),(8,-94)),
          ((30,-90),(56,-81),(75,-72)),((87,-65),(101,-52),(104,-36)),
          ((108,-22),(104,-7),(92,6)),((70,19),(30,23),(-5,22)),
          ((-37,21),(-71,20),(-85,6)),((-89,-1),(-91,-9),(-93,-15)),fill=BASE,width=2.7)
    # Rear oxide rind and broad slanted dorsal plane.
    shape(c,P,(-93,-15),((-101,-36),(-94,-63),(-83,-74)),
          ((-64,-90),(-44,-96),(-25,-95)),((-36,-84),(-57,-72),(-66,-52)),
          ((-74,-29),(-72,-8),(-63,10)),((-78,6),(-88,0),(-93,-15)),fill=OXIDE,edge=None)
    shape(c,P,(-86,-74),((-72,-94),(-47,-96),(-26,-96)),
          ((7,-98),(46,-84),(75,-69)),((60,-72),(45,-67),(28,-59)),
          ((-5,-53),(-39,-58),(-64,-47)),((-78,-55),(-81,-63),(-86,-74)),fill=LIGHT,edge=None)
    shape(c,P,(-81,-74),((-70,-87),(-48,-94),(-27,-94)),
          ((-8,-97),(16,-90),(27,-86)),((3,-86),(-21,-83),(-42,-74)),
          ((-61,-67),(-72,-67),(-81,-74)),fill=color(LIGHT,PALE,.46),edge=None)
    # Wide side face, interrupted by a sagging lower skirt and broad
    # dented casting surfaces instead of a pattern of armor segments.
    shape(c,P,(-66,-47),((-38,-56),(-8,-53),(29,-59)),
          ((39,-42),(39,-16),(29,7)),((8,14),(-32,14),(-58,6)),
          ((-72,-5),(-74,-31),(-66,-47)),fill=MID,edge=None)
    shape(c,P,(-68,-28),((-51,-21),(-36,-27),(-17,-25)),
          ((-3,-24),(10,-20),(30,-25)),((37,-14),(33,0),(28,8)),
          ((-2,18),(-37,15),(-58,6)),((-68,-3),(-73,-16),(-68,-28)),fill=BASE,edge=None)
    shape(c,P,(-76,-4),((-49,12),(-12,11),(14,13)),
          ((44,15),(64,10),(92,6)),((69,20),(31,23),(-4,22)),
          ((-33,21),(-65,18),(-76,-4)),fill=SHADOW,edge=None)
    line(c,P,[(-83,-72),(-68,-84),(-47,-92),(-27,-95),(-10,-94)],PALE,1.65)
    line(c,P,[(-61,-44),(-40,-49),(-10,-49),(24,-56)],LIGHT,1.35)
    line(c,P,[(-55,8),(-36,13),(-7,14),(18,12)],MID,1.25)
    # Wide chamfer catches a colder reflection; the belly folds are
    # cast-metal flow lines rather than armor joints.
    poly(c,P,[(-87,-73),(-66,-47),(-69,-17),(-88,-4),(-95,-33)],color(OXIDE,BASE,.45))
    line(c,P,[(-87,-73),(-66,-47),(-69,-17)],color(BASE,LIGHT,.44),1.5)
    shape(c,P,(-56,-20),((-37,-14),(-16,-20),(2,-18)),
          ((12,-16),(21,-15),(31,-17)),((23,-11),(13,-8),(2,-10)),
          ((-20,-13),(-38,-6),(-56,-20)),fill=OXIDE,edge=None)
    line(c,P,[(-53,-17),(-36,-13),(-13,-15),(0,-14)],MID,.85)
    for x,y,dx in [(-60,-80,11),(-44,-85,14),(-13,-87,11),(-34,-35,12),(-22,-30,9),(6,-41,10)]:
        line(c,P,[(x,y),(x+dx*.7,y-1),(x+dx,y-2)],color(BASE,LIGHT,.38),.8)
    # Irregular casting ripples and a few broad depressions: not rock cracks.
    dent(c,P,-48,-34,11,4);dent(c,P,-7,-38,8,2.8);dent(c,P,-42,-77,6,2)
    line(c,P,[(-79,-52),(-80,-44),(-76,-39)],SHADOW,1.2)
    line(c,P,[(-22,-80),(-10,-82),(5,-81)],MID,1.4)
    line(c,P,[(-51,-12),(-41,-10),(-32,-12)],OXIDE,1.1)
    # The forequarter is a sloping side facet, not a separate joint disk.
    poly(c,P,[(-11,-9),(10,-19),(35,-16),(40,6),(28,16),(6,15)],color(BASE,MID,.39))
    line(c,P,[(-10,-8),(9,-17),(25,-16)],color(MID,LIGHT,.50),1.1)
    # The face is sculpted into the tapered end of the same casting. The
    # drooping brow and blunt snout cast deep shadows into its sockets.
    shape(c,P,(28,-59),((47,-69),(67,-70),(78,-62)),
          ((95,-54),(104,-42),(101,-28)),((102,-14),(94,-1),(83,5)),
          ((65,10),(45,7),(30,0)),((35,-17),(36,-39),(28,-59)),fill=BASE,edge=None)
    shape(c,P,(34,-55),((50,-65),(65,-67),(76,-60)),
          ((86,-56),(93,-49),(97,-39)),((81,-44),(66,-44),(52,-42)),
          ((44,-43),(38,-47),(34,-55)),fill=LIGHT,edge=None)
    shape(c,P,(43,-42),((60,-46),(81,-45),(96,-38)),
          ((97,-28),(92,-21),(86,-18)),((72,-21),(57,-18),(46,-24)),
          ((41,-29),(40,-35),(43,-42)),fill=SHADOW,edge=None)
    blink=1.-.9*max(0.,1.-abs(q.t-.77)/.048) if not q.move and not q.ready+q.strike else 1.
    if q.death:blink=1-track(q.death,[(0,0),(.18,.15),(.56,1),(1,1)])
    # Eyes are small recessed slits, not a glowing visor.
    for x,y,w in ((53,-32,7),(80,-32,10)):
        sl=(2.5+2.2*q.ready+1.2*q.strike)*(1 if x<65 else -1)
        poly(c,P,[(x-w,y-5-sl),(x+w,y-5+sl),(x+w-1,y+4*blink+sl),(x-w+1,y+4*blink-sl)],EDGE)
        if blink>.12:
            poly(c,P,[(x-w+2,y-2-sl),(x+w-2,y-2+sl),(x+w-3,y+1.9*blink+sl),(x-w+3,y+1.9*blink-sl)],PALE)
        line(c,P,[(x-w,y-7-sl),(x,y-8),(x+w,y-7+sl)],MID,1.2)
    # Broad lower lip of the cast face, continuous with the body. No
    # humanoid nose or separate mouth plate.
    shape(c,P,(43,-24),((58,-22),(76,-22),(96,-23)),
          ((100,-16),(98,-8),(91,-5)),((76,0),(53,-2),(44,-8)),
          ((39,-13),(39,-20),(43,-24)),fill=MID,edge=None)
    line(c,P,[(49,-18),(67,-15),(87,-18)],LIGHT,1.4)
    dent(c,P,89,-12,3.5,1.5)
    opened=(.45*q.ready+.9*q.strike+.55*q.hurt)*(1-q.death)
    if q.death:opened=track(q.death,[(0,0),(.25,.55),(.64,0),(1,0)])
    shape(c,P,(46,-3),((57,-12),(79,-11),(94,-5)),
          ((87,-1+7*opened),(62,-1+5*opened),(46,-3)),fill=EDGE,edge=None)
    if opened>.18:line(c,P,[(54,-5),(70,-7),(87,-5)],PALE,1.1)
    line(c,P,[(50,3+5*opened),(71,5+5*opened),(89,2+4*opened)],LIGHT,1.15)
    dent(c,P,73,-57,4,1.2)


def dust(c,q,hand_pos):
    # World-facing contact chips and small settling dust puffs, only during
    # impact. The engine owns actual range, damage and armored behavior.
    if q.impact<=.01:return
    u=max(0.,(q.t-A)/(1-A)); k=q.impact
    x=hand_pos[0]+6
    for i in range(7):
        side=1 if i%2==0 else -1
        xx=x+side*(16+i*5+35*u)
        yy=FLOOR-9-(7+i%3*7)*math.sin(min(1.,u*2.4)*math.pi)
        rr=(4+i%3*2)*k
        c.oval((xx,yy),rr*1.65,rr,(143,139,129,round(130*k)),None)
        if i%2==0:
            p=(xx+side*5,yy-7)
            c.poly([add(p,(-3,-2)),add(p,(4,0)),add(p,(0,3))],(*MID,round(240*k)),None)
    for side in (-1,1):
        p=(x+side*(20+30*u),FLOOR-2)
        c.line([p,(p[0]+side*(17+26*u),FLOOR-4)],(175,172,163,round(170*k)),1.1+1.5*k)


def render_frame(anim,i,n):
    q=pose(anim,i,n)
    P,lean,j=solve(q)
    c=Canvas(FRAME_SIZE)
    # Back limbs first, then the near limbs and the mass. The body masks the
    # limb roots; the face remains unobscured.
    support(c,j['far_leg'],far=True,rear=True)
    support(c,j['far_arm'],far=True,pitch=-18*q.ready)
    support(c,j['near_leg'],rear=True)
    support(c,j['near_arm'],pitch=-24*q.ready)
    casting(c,P,q)
    if not q.death:dust(c,q,j['near_arm'][-1])
    im=c.finish()
    if q.death and q.death>=.46:
        bb=im.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox()
        if bb and bb[3]>FLOOR+1: im=anchored_death(im,FLOOR)
    return im


TRAITS=['enemy','science','elemental','chemical_element','lead','heavy_metal']
ACTOR_METADATA={
    'actor':{'character_id':TARGET_NAME,'display_name':'Lead Elemental'},
    'body':{'body_plan':'Quadruped','body_kind':'Standard','mass_class':'Heavy','locomotion_hint':'Walk','traits':TRAITS},
    'capabilities':{'traversal':{'walk':True}},'actions':{'default_preset':'lead_elemental_slam'},
    'visual':{'default_pose':'idle','portrait':{'animation':'idle','frame':0}},'tags':TRAITS,
    'authoring_description':'A dense cast-lead beast with an integral head, sloping ingot back and four load-bearing limbs.',
    'gameplay_description':'A slow heavy bruiser. It rears onto its rear supports, drops its front mass, and recovers slowly. Dust is decorative.',
    'animation_bindings':{'default':{'animation':'idle','events':[]},
        'locomotion.walk':{'animation':'walk','events':[]},'locomotion.run':{'animation':'run','events':[]},
        'combat.hurt':{'animation':'hit','events':[]},'combat.death':{'animation':'death','events':[]},
        'action.melee.primary':{'animation':'attack_side','events':[
            {'t':A,'event':'hitbox_active_start','source':'lead_elemental.slam'},
            {'t':B,'event':'hitbox_active_end','source':'lead_elemental.slam'}]}}}


def render(out_dir: str|Path,**opts):
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=render_frame,out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,auto_crop=False,actor_metadata=ACTOR_METADATA,
        body_metrics_fn=lambda w,h:body_metrics_for_box((56,89,256,264),w,h),
        animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
