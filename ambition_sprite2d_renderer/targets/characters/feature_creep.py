"""Feature Creep, a prototype with a remarkably crowded feature backlog.

A rugged unfinished service robot with four plug-in bays, a CRT face, a cup
holder, a useless satellite dish, a receipt printer, a cooling fan and an elaborate articulated hammer. The
modules unfold in successive beats as it over-engineers a simple punch.
Nothing persists or changes the actual game state: the feature pileup is
one attack cycle, using the existing melee action system.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from ._clockwork_enemy_art import (Canvas, INK, add, sub, mul, rot, unit, perp,
                                  polar, mix, track, phase, anchored_death, actor)

TARGET_NAME='feature_creep'
FRAME_SIZE=(352,256)
CX,GROUND=154.,228.
WINDUP_S,ACTIVE_S,RECOVER_S=.85,.30,1.02
ROWS=[('idle',16,100),('walk',16,85),('notice',8,80),('windup',14,65),('attack_side',52,42),('hit',8,75),('death',20,80)]
LOOPS={'idle','walk','windup'}
ACTOR_METADATA=actor(TARGET_NAME,'Feature Creep','unfinished',['machine','prototype'],
    'The software development phenomenon of feature creep made into an unfinished service robot. Its modular tool bays extend unnecessary accessories and a receipt printer, a cooling fan and a large piston hammer. Blueprint blue, raw metal, and construction-yellow accents match the unfinished dimension.',
    'A heavy grounded enemy that unfolds an excessive array of attachments, delivers one over-engineered piston strike, then spends time retracting its features.', 'Heavy')
SHELL='#b6c2bf'; LIGHT='#e1e5d9'; DARK='#64767e'; MID='#819a9d'; STEEL='#78929c'; STEEL_D='#435661'; STEEL_L='#cad7d5'
YELLOW='#d6b25b'; YELLOW_L='#f4d78b'; OCHRE='#96753f'; SCREEN='#233b43'; CYAN='#92ded3'; RED='#c56a56'; BLACK='#394047'; WHITE='#f3edce'


@dataclass(frozen=True)
class Pose:
    lean:float=0.; bob:float=0.; stride:float=0.; phase:float=0.
    dish:float=0.; cup:float=0.; beacon:float=0.; arm:float=0.; strike:float=0.
    fan:float=0.; printer:float=0.
    alarm:float=0.; blink:float=0.; topple:float=0.; recoil:float=0.


def pose(anim,i,n):
    t=phase(i,n,anim in LOOPS); p=math.tau*t
    if anim=='idle':return Pose(bob=1.2*math.sin(p),phase=p,blink=float(i in (9,10)))
    if anim=='walk':return Pose(lean=7,bob=2*abs(math.sin(p)),stride=1,phase=p)
    if anim=='notice':return Pose(lean=-7*math.sin(math.pi*t),bob=-2*math.sin(math.pi*t),beacon=.45,alarm=.6)
    if anim=='windup':return Pose(lean=-9,bob=3+.6*math.sin(p),dish=.82,cup=.88,beacon=1,arm=.7,fan=.35,printer=.40,alarm=.85)
    if anim=='attack_side':
        # The game pins windup until startup ends, then samples the attack
        # row at whole-move progress. Keep the matching anticipation until A.
        a=WINDUP_S/(WINDUP_S+ACTIVE_S+RECOVER_S); b=(WINDUP_S+ACTIVE_S)/(WINDUP_S+ACTIVE_S+RECOVER_S)
        k=lambda keys:track(t,keys)
        return Pose(lean=k([(0,-9),(a,-9),(a+.07,16),(b,12),(.83,-3),(1,0)]),
            bob=k([(0,3),(a,3),(a+.07,5),(b,6),(.85,2),(1,0)]),
            dish=k([(0,.82),(a,.82),(a+.05,1),(.73,1),(.96,0),(1,0)]),
            cup=k([(0,.88),(a,.88),(a+.07,1),(.65,1),(.90,0),(1,0)]),
            beacon=k([(0,1),(.83,1),(.98,0),(1,0)]),
            fan=k([(0,.35),(a,.35),(a+.045,1),(.74,1),(.91,0),(1,0)]),
            printer=k([(0,.40),(a,.40),(a+.08,.85),(.70,1),(.97,0),(1,0)]),
            arm=k([(0,.7),(a,.7),(a+.05,1),(b,1),(.68,.8),(.94,0),(1,0)]),
            strike=k([(0,0),(a,0),(a+.06,1),(b,1),(.70,.37),(.91,0),(1,0)]),
            alarm=k([(0,.85),(a+.06,1),(b,1),(.9,0),(1,0)]))
    if anim=='hit':return Pose(lean=-17*math.sin(math.pi*t),bob=2*math.sin(math.pi*t),recoil=math.sin(math.pi*t),alarm=1,blink=.65)
    if anim=='death':return Pose(lean=-5,topple=track(t,[(0,0),(.18,0),(.67,1),(1,1)]),alarm=1,blink=1,
                                arm=.28*(1-t),dish=.4*(1-t),cup=.45*(1-t),beacon=.8*(1-t),bob=4*t)
    raise ValueError(anim)


def _joint(d,p,r=8):
    d.disk(p,r,STEEL_D);d.disk(p,r*.73,STEEL,INK,1);d.bolt(p,r*.37,STEEL_L)


def _leg(d,P,q,side,far):
    ph=q.phase+(math.pi if far else 0); st=q.stride
    x=side*25+24*st*math.sin(ph); lift=12*st*max(0,math.cos(ph))
    hip=P((side*24,-42)); knee=P((side*22+10*st*math.sin(ph),-23)); ankle=P((x,-10-lift))
    d.tube(hip,knee,9,STEEL_D,STEEL,None);d.tube(knee,ankle,6.5,MID,STEEL_L,STEEL_D)
    _joint(d,hip,9);_joint(d,knee,7)
    foot=[P((x-13,-12-lift)),P((x+16,-12-lift)),P((x+21,-5-lift)),P((x+20,-1-lift)),P((x-16,-1-lift)),P((x-17,-6-lift))]
    d.poly(foot,STEEL_D if far else YELLOW,INK,2);d.line([P((x-14,-5-lift)),P((x+18,-5-lift))],BLACK,3)
    for a in [-8,1,10]:d.line([P((x+a,-4-lift)),P((x+a-1,-1-lift))],MID,1.4)


def _render_frame(anim,i,n):
    q=pose(anim,i,n);d=Canvas(FRAME_SIZE)
    def P(p):return add((CX+54*q.topple-5*q.recoil,GROUND-2-95*q.topple),rot(p,-80*q.topple))
    def B(x,y):return P(add((0,-80+q.bob),rot((x,y+80),q.lean)))
    # Back foot, then the chassis and plug-in rails. Front foot is painted over
    # the far leg's rim but remains behind the body shell.
    _leg(d,P,q,-1,True);_leg(d,P,q,1,False)
    def panel(points,fill,edge=INK,w=1.8):d.poly([B(*p) for p in points],fill,edge,w)
    def line(points,c=INK,w=1.5):d.line([B(*p) for p in points],c,w)
    def oval(x,y,rx,ry,fill,edge=INK,w=1.5):d.oval(B(x,y),rx,ry,fill,edge,w,q.lean-80*q.topple)
    # Rear industrial rack, three rails and plug ports. The modules remain
    # attached to their actual sliding carriages, never floating around it.
    panel([(-53,-137),(-34,-149),(-26,-130),(-28,-53),(-56,-51)],DARK)
    for yy in (-126,-103,-80):
        panel([(-57,yy-6),(-38,yy-6),(-38,yy+6),(-57,yy+6)],STEEL_D);line([(-54,yy-3),(-42,yy-3)],STEEL_L,1.8)
    # Dish mast: screw telescope and swiveling saucer.
    base=B(-39,-137); joint=B(-51-16*q.dish,-144-12*q.dish); tip=B(-52-25*q.dish,-151-29*q.dish)
    d.tube(base,joint,5,STEEL_D,STEEL_L);d.tube(joint,tip,3.4,STEEL,STEEL_L);_joint(d,joint,5.5)
    u=rot((-1,-.3),-13*q.dish-80*q.topple);v=perp(u)
    saucer=[add(tip,add(mul(u,5-12*(k/16-.5)**2),mul(v,(k/16-.5)*32))) for k in range(17)]
    inner=[add(p,mul(u,4)) for p in reversed(saucer)];d.poly(saucer+inner,STEEL_L,INK,1.6)
    d.line([saucer[0],tip,saucer[-1]],DARK,1.0);feed=add(tip,mul(u,15));d.tube(tip,feed,1.6,STEEL_D,STEEL_L);d.disk(feed,3.2,YELLOW)
    # Unnecessary drinks holder, with a lidded takeaway cup. Stays mounted on
    # a secondary linkage even when fully deployed.
    cp=B(-53-27*q.cup,-86+5*q.cup);cs=B(-51,-82)
    d.tube(cs,cp,4.2,STEEL_D,STEEL_L);d.box(cp,11,5,STEEL,angle=q.lean-80*q.topple)
    panel_cup=[(-7,-6),(-6,-22),(6,-22),(8,-6)];ang=q.lean-80*q.topple
    d.poly([add(cp,rot(p,ang)) for p in panel_cup],WHITE,INK,1.2)
    d.box(add(cp,rot((0,-22),ang)),8,2.5,DARK,INK,1.1,2,ang);d.line([add(cp,rot((-5,-13),ang)),add(cp,rot((6,-13),ang))],OCHRE,3)
    # A receipt printer emerges from the bottom of the rack. The paper itself
    # is regenerated along its curl, with printed line items and a perforation.
    pp=B(-52-21*q.printer,-58); pr=B(-47,-62)
    d.tube(pr,pp,4.8,STEEL_D,STEEL_L);d.box(pp,12,9,STEEL,INK,1.5,3,ang)
    d.line([add(pp,rot((-7,3),ang)),add(pp,rot((7,3),ang))],SCREEN,3)
    if q.printer>.08:
        length=18*q.printer
        a0=add(pp,rot((-6,4),ang));a1=add(pp,rot((6,4),ang))
        b0=add(pp,rot((-10,4+length),ang));b1=add(pp,rot((2,4+length),ang))
        d.poly([a0,a1,b1,b0],WHITE,INK,1.1)
        for z in (.28,.48,.68):d.line([mix(a0,b0,z),mix(a1,b1,z)],OCHRE,.9)
        d.line([mix(a0,b0,.88),mix(a1,b1,.88)],DARK,.8)
    # Main body: chamfered cast chassis, darker side and removable service panel.
    panel([(-39,-144),(25,-144),(42,-132),(43,-59),(28,-42),(-39,-42),(-49,-58),(-49,-130)],SHELL,INK,2.4)
    panel([(-49,-130),(-39,-144),(-32,-136),(-32,-53),(-39,-42),(-49,-58)],DARK,None)
    panel([(-39,-144),(25,-144),(42,-132),(-32,-132)],LIGHT,None)
    panel([(-32,-127),(30,-127),(35,-117),(35,-85),(-31,-85)],DARK,INK,1.5)
    panel([(-28,-123),(26,-123),(30,-116),(30,-90),(-28,-90)],SCREEN,INK,1.1)
    line([(-25,-120),(22,-120)],'#537479',1.2)
    # Face drawn as an amber/teal CRT expression with scan lines.
    eye_color=YELLOW_L if q.alarm>.5 else CYAN
    for ex in (-10,14):
        if q.blink>.5:line([(ex-6,-106),(ex+6,-106)],eye_color,2.4)
        else:
            oval(ex+2,-107,4.4,7.1,eye_color,None)
            if q.alarm>.5:line([(ex-5,-116),(ex+7,-110)],SCREEN,3.3)
    if q.topple>.45:line([(-11,-95),(-2,-98),(6,-94),(15,-97)],RED,2.4)
    else:line([(-7,-96),(4,-94 if q.alarm<.5 else -99),(15,-97)],eye_color,1.8)
    for yy in (-118,-114,-110,-106,-102,-98,-94):line([(-26,yy),(27,yy)],'#35525a',.6)
    # Module bus: four sockets, with distinctly coloured connectors and three
    # lit capacity bars. Yellow diagonal warning stripes on the lower rail.
    panel([(-27,-80),(28,-80),(28,-55),(-27,-55)],MID,INK,1.3)
    for x,c in [(-19,CYAN),(-4,YELLOW_L),(11,RED)]:
        oval(x,-69,5,5,SCREEN);oval(x,-69,2.5,2.5,c if q.arm>.35 or x==-19 else DARK,None)
    for yy in [-77,-61]:line([(22,yy),(26,yy)],STEEL_D,1.4)
    panel([(-32,-52),(27,-52),(23,-45),(-30,-45)],YELLOW)
    for x in range(-26,24,12):line([(x,-51),(x+5,-46)],BLACK,3.1)
    for x,y in [(-37,-133),(33,-133),(-37,-56),(35,-63)]:d.bolt(B(x,y),2.7,STEEL_L)
    # Beacon on a retractable threaded mast. Draw the mast before its lamp.
    b0=B(10,-145);b1=B(10,-150-20*q.beacon);d.tube(b0,b1,3.5,STEEL_D,STEEL_L)
    for k in range(1,4):
        h=mix(b0,b1,k/4);d.line([add(h,(-3,0)),add(h,(3,0))],DARK,.9)
    oval(10,-152-20*q.beacon,9,5,STEEL_D);oval(10,-160-20*q.beacon,7,8,RED if q.beacon>.5 else OCHRE)
    oval(8,-163-20*q.beacon,2.8,3.4,YELLOW_L,None)
    # A completely unnecessary cooling fan unfolds above the front corner.
    # Its articulated stand shares a real mounting point on the chassis.
    if q.fan>.01:
        f0=B(33,-139);f1=B(37+14*q.fan,-148-24*q.fan);f2=B(42+16*q.fan,-151-39*q.fan)
        d.tube(f0,f1,4.7,STEEL_D,STEEL_L);d.tube(f1,f2,3.3,STEEL,STEEL_L);_joint(d,f1,5.2)
        radius=7+8*q.fan;d.disk(f2,radius,STEEL_D,INK,1.6);d.disk(f2,radius*.81,SCREEN,STEEL_L,1)
        spin=360*(i/n)*4 if anim in ('windup','attack_side') else 0
        for j in range(4):
            theta=spin+j*90+ang
            pts=[add(f2,polar(radius*r,theta+offset)) for r,offset in [(.18,0),(.72,-14),(.78,25),(.28,48)]]
            d.poly(pts,MID,INK,.7)
        d.disk(f2,radius*.20,YELLOW,INK,.8)
        for j in range(4):d.line([add(f2,polar(radius*.38,ang+j*90)),add(f2,polar(radius*.87,ang+j*90))],STEEL_L,.8)
    # Near arm: a real telescoping piston with the hammer head bolted to its
    # endpoint. Idle = tucked under the shoulder. Strike = long forward reach.
    shoulder=B(39,-103); elbow=B(49+8*q.arm,-77-17*q.arm); end=B(50+25*q.arm+63*q.strike,-56-30*q.arm+13*q.strike)
    d.tube(shoulder,elbow,9,STEEL_D,STEEL_L);_joint(d,shoulder,11);_joint(d,elbow,8)
    d.tube(elbow,end,5.4,STEEL_L,WHITE,STEEL)
    v=unit(sub(end,elbow));sleeve=add(elbow,mul(v,min(24,math.hypot(*sub(end,elbow))*.78)))
    d.tube(elbow,sleeve,9,YELLOW,YELLOW_L,OCHRE);d.tube(add(sleeve,mul(v,-4)),sleeve,10,STEEL_D,STEEL_L)
    angle=math.degrees(math.atan2(v[1],v[0]));
    d.box(end,17,12,YELLOW,INK,2,3,angle);d.box(add(end,mul(v,12)),6,13,STEEL_D,INK,1.5,2,angle)
    for side in (-1,1):d.bolt(add(end,mul(perp(v),side*7)),2.5,STEEL_L)
    # Five redundant little status LEDs on the hammer, activated by deployment.
    for k in range(3):d.disk(add(end,add(mul(v,-10+5*k),mul(perp(v),-5))),1.65,CYAN if q.strike>.5 else OCHRE,None)
    out=d.finish()
    return anchored_death(out,GROUND) if q.topple>0 else out


def _body_metrics(fw,fh):
    from ...core.measure import body_metrics_for_box
    return body_metrics_for_box((106,82,202,229),fw,fh)


def render(out_dir: str|Path, **opts):
    from ...authoring.sheet_build import build_sheet
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,out_dir=Path(out_dir),frame_size=FRAME_SIZE,
        auto_crop=False,actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
