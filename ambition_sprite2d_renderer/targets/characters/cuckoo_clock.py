"""Cuckoo Clock: an old clockwork chalet that walks on brass feet.

Its clock hands tick, pendulum swings, and wooden doors open to release a
brass mechanical cuckoo on a scissor spring. The bird snaps and retracts;
it is not a separate simulated projectile. All moving parts are attached.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from ._clockwork_enemy_art import (Canvas, INK, add, sub, mul, rot, unit, perp,
                                  polar, mix, track, phase, anchored_death, actor)

TARGET_NAME='cuckoo_clock'
FRAME_SIZE=(368,288)
CX,GROUND=132.,258.
WINDUP_S,ACTIVE_S,RECOVER_S=.65,.22,.76
ROWS=[('idle',16,100),('walk',16,82),('notice',8,75),('windup',12,65),('attack_side',48,35),('hit',8,80),('death',20,85)]
LOOPS={'idle','walk','windup'}
ACTOR_METADATA=actor(TARGET_NAME,'Cuckoo Clock','automaton',['machine','clockwork','bird'],
    'A walking Black Forest-style wooden cuckoo clock with a decorative chalet roof, brass gears, a swinging pendulum, and a mechanical cuckoo riding a scissor linkage. The bird lunge is an invented game attack.',
    'A clockwork melee enemy. It opens its door and holds a coiled mechanical bird inside, then sends it out on a spring for a quick peck before winding the bird back in.')
WOOD='#985b40'; WOOD_D='#603d37'; WOOD_M='#b8754a'; WOOD_L='#daa16b'; WOOD_H='#f2c18a'
ROOF='#785047'; ROOF_D='#4d3940'; ROOF_L='#b27b60'; GOLD='#cda252'; GOLD_D='#89663d'; GOLD_L='#f4d889'; GOLD_H='#fff1be'
STEEL='#74898d'; STEEL_D='#495e68'; STEEL_L='#c3d1cb'; CREAM='#efe1b9'; DARK='#302e38'; RED='#a54a42'; RED_L='#e07b62'; GREEN='#688b7a'; GREEN_L='#9fbd99'; WHITE='#fff5da'


@dataclass(frozen=True)
class Pose:
    lean:float=0.; bob:float=0.; stride:float=0.; phase:float=0.; door:float=0.
    extension:float=0.; peck:float=0.; alarm:float=0.; blink:float=0.; topple:float=0.; recoil:float=0.


def pose(anim,i,n):
    t=phase(i,n,anim in LOOPS); p=math.tau*t
    if anim=='idle':return Pose(bob=.8*math.sin(p),phase=p,blink=float(i in (10,11)))
    if anim=='walk':return Pose(lean=6,bob=1.5*abs(math.sin(p)),stride=1,phase=p)
    if anim=='notice':return Pose(lean=-5*math.sin(math.pi*t),bob=-2*math.sin(math.pi*t),phase=p,alarm=.6,door=0.)
    if anim=='windup':return Pose(lean=-8,bob=2,phase=.18*math.sin(p),door=.88,extension=.10,alarm=1)
    if anim=='attack_side':
        a=WINDUP_S/(WINDUP_S+ACTIVE_S+RECOVER_S);b=(WINDUP_S+ACTIVE_S)/(WINDUP_S+ACTIVE_S+RECOVER_S)
        k=lambda keys:track(t,keys)
        return Pose(lean=k([(0,-8),(a,-8),(a+.06,8),(b,5),(.83,-3),(1,0)]),bob=k([(0,2),(a,2),(b,4),(1,0)]),
            phase=k([(0,0),(a,0),(b,2),(1,math.tau)]),
            door=k([(0,.88),(a,.88),(a+.04,1),(.76,1),(.98,0),(1,0)]),
            extension=k([(0,.10),(a,.10),(a+.06,1),(b,1),(.75,.28),(.91,0),(1,0)]),
            peck=k([(0,0),(a,0),(a+.045,1),(b,.15),(.69,0),(1,0)]),
            alarm=k([(0,1),(b,1),(.85,.4),(1,0)]))
    if anim=='hit':return Pose(lean=-13*math.sin(math.pi*t),bob=3*math.sin(math.pi*t),phase=p,door=0.,alarm=1,blink=1,recoil=math.sin(math.pi*t))
    if anim=='death':return Pose(lean=-3,phase=p,door=track(t,[(0,0),(.25,.75),(1,.58)]),extension=0,alarm=1,blink=1,topple=track(t,[(0,0),(.15,0),(.7,1),(1,1)]))
    raise ValueError(anim)


def _leg(d,P,q,side,far):
    ph=q.phase+(math.pi if far else 0);s=q.stride
    x=side*22+22*s*math.sin(ph);lift=12*s*max(0,math.cos(ph))
    a=P((side*23,-46));b=P((side*23+8*s*math.sin(ph),-25));c=P((x,-10-lift))
    d.tube(a,b,6.5,GOLD_D,GOLD_L);d.disk(a,7.8,WOOD_D);d.disk(a,4.4,GOLD)
    d.tube(b,c,5.1,GOLD,GOLD_L,GOLD_D);d.disk(b,6.8,GOLD_D);d.bolt(b,3.8,GOLD_L)
    d.poly([P((x-14,-11-lift)),P((x+10,-11-lift)),P((x+21,-5-lift)),P((x+21,-1-lift)),P((x-14,-1-lift)),P((x-17,-5-lift))],WOOD_D if far else GOLD,INK,1.8)
    d.line([P((x-12,-5-lift)),P((x+18,-5-lift))],GOLD_D,2.4)


def _bird(d,center,angle,peck):
    """The brass cuckoo, drawn in one local coordinate frame."""
    def P(x,y):return add(center,rot((x,y),angle))
    def poly(points,c,edge=INK,w=1.5):d.poly([P(*p) for p in points],c,edge,w)
    # tail feathers and mechanical wing hinge
    poly([(-11,1),(-28,-12),(-23,1),(-30,10),(-9,10)],GREEN)
    d.oval(P(-1,3),19,12,GOLD,INK,1.7,angle)
    d.oval(P(5,1),12,9,GOLD_L,None,angle=angle)
    poly([(-10,-5),(4,-5),(11,2),(-1,12),(-15,7)],GREEN,INK)
    d.line([P(-9,1),P(5,2),P(-1,8)],GREEN_L,2)
    d.bolt(P(-3,1),2.6,GOLD_L)
    head=P(15,-9-2*peck);d.disk(head,12.5,GREEN,INK,1.7);d.oval(P(18,-8-2*peck),8.1,9,GREEN_L,None,angle=angle)
    d.disk(P(19,-12-2*peck),4.1,WHITE,INK,.9);d.disk(P(20.2,-12-2*peck),1.9,DARK,None)
    # Upper and lower beaks pivot about the face. A sharp snap is the visible hit.
    gape=8*peck
    poly([(24,-12-2*peck),(39+3*peck,-9-gape),(25,-7-2*peck)],GOLD_L,INK,1.1)
    poly([(25,-7-2*peck),(39+3*peck,-9+gape),(23,-4-2*peck)],GOLD,INK,1.1)
    d.line([P(19,-18-2*peck),P(23,-16-2*peck)],DARK,1.5)
    for x in (-7,5):d.tube(P(x,10),P(x,16),1.6,GOLD_D,GOLD_L);d.line([P(x-3,16),P(x+4,16)],GOLD,2)


def _render_frame(anim,i,n):
    q=pose(anim,i,n);d=Canvas(FRAME_SIZE)
    def P(p):return add((CX+110*q.topple-6*q.recoil,GROUND-2-100*q.topple),rot(p,-79*q.topple))
    def B(x,y):return P(add((0,-104+q.bob),rot((x,y+104),q.lean)))
    ang=q.lean-79*q.topple
    def panel(points,c,edge=INK,w=1.8):d.poly([B(*p) for p in points],c,edge,w)
    def line(points,c=INK,w=1.4):d.line([B(*p) for p in points],c,w)
    def oval(x,y,rx,ry,c,edge=INK,w=1.5):d.oval(B(x,y),rx,ry,c,edge,w,ang)
    _leg(d,P,q,-1,True);_leg(d,P,q,1,False)
    # Pendulum below the case, between the two knees. Side chains and weights
    # are mounted to the wooden case and do not extend past the sole row.
    pivot=B(-8,-57); pend=B(-8+12*math.sin(q.phase),-24);d.tube(pivot,pend,2.5,GOLD_D,GOLD_L)
    d.oval(pend,9,11,GOLD,INK,1.5,ang);d.oval(add(pend,rot((-2,-2),ang)),5.6,7.5,GOLD_L,None,angle=ang)
    for x,l in [(-32,21),(22,16)]:
        for k in range(5):oval(x,-47+3.7*k,2.0,3.0,GOLD_D,INK,.7)
        yy=-47+l;oval(x,yy,4.3,8.5,WOOD_D);line([(x-2,yy-5),(x+2,yy-1),(x-2,yy+3),(x+1,yy+6)],WOOD_L,.9)
    # Wooden chalet body, with a visibly darker rear wall and joinery.
    panel([(-58,-153),(-43,-174),(39,-174),(50,-158),(50,-48),(-43,-48),(-58,-63)],WOOD_D,INK,2.2)
    panel([(-44,-167),(45,-167),(45,-52),(-44,-52)],WOOD,INK,2)
    panel([(-44,-167),(-32,-163),(-32,-56),(-44,-52)],WOOD_M,None)
    for x in [-36,-30,36,40]:line([(x,-161),(x,-55)],WOOD_D,.65)
    for x in [-40,40]:
        for yy in [-145,-71]:d.bolt(B(x,yy),2.3,GOLD_D)
    # Carved wood slats follow the case; not screen-space texture.
    for x in [-28,-21,-13,15,26,33]:
        line([(x,-152),(x+1,-142),(x-1,-132)],WOOD_M,.9)
        line([(x,-77),(x-1,-67),(x+1,-56)],WOOD_M,.9)
    # Bottom ledge and carved apron.
    panel([(-50,-57),(50,-57),(54,-49),(47,-43),(-47,-43),(-54,-49)],WOOD_M,INK,2)
    line([(-48,-51),(48,-51)],WOOD_L,1.8)
    # Roof silhouette, layered shingles and carved scallop edge.
    panel([(-68,-165),(-12,-211),(4,-219),(67,-167),(61,-158),(4,-203),(-58,-156)],ROOF_D,INK,2.4)
    panel([(-59,-167),(4,-214),(60,-166),(51,-165),(4,-203),(-50,-162)],ROOF,INK,1.4)
    line([(-59,-167),(4,-214),(60,-166)],WOOD_L,2.2)
    for k in range(1,5):
        t=k/5;line([(-59+63*t,-167-47*t),(-50+54*t,-162-41*t)],ROOF_L,1.0)
        line([(4+56*t,-214+48*t),(4+47*t,-203+38*t)],ROOF_L,1.0)
    panel([(-62,-157),(4,-205),(62,-158),(59,-153),(4,-195),(-59,-151)],WOOD_L,INK,1.6)
    # Decorative leaf motif under gable with a small brass rosette.
    for side in [-1,1]:
        panel([(4,-189),(4+side*18,-185),(4+side*12,-178),(4,-183)],WOOD_M,WOOD_D,1.1)
    oval(4,-188,4,4,GOLD,INK,.9)
    # Clock face: ring, tick marks and Roman-like grouped marks, moving hands.
    oval(0,-97,36,36,WOOD_D,INK,2);oval(0,-97,31.5,31.5,GOLD,INK,1.2);oval(0,-97,27.5,27.5,CREAM,INK,1.2)
    for k in range(12):
        a=k*30-90;r=23.5
        p=add((0,-97),polar(r,a));p2=add((0,-97),polar(r-(4.6 if k%3==0 else 2.5),a));line([p,p2],WOOD_D,1.4 if k%3==0 else .85)
    # Two clock hands, attached to the same hub and rotating continuously.
    minute=-65+math.degrees(q.phase);hour=155+math.degrees(q.phase)/12
    for radius,a,w in [(20,minute,2.4),(13,hour,3.5)]:
        x,y=polar(radius,a);line([(0,-97),(x,-97+y)],DARK,w)
        x2,y2=polar(radius+2,a);line([(x,-97+y),(x2,-97+y2)],GOLD_D,1.2)
    oval(0,-97,3.2,3.2,GOLD_D,INK,.8)
    # Expressive eyes on the face, separated from the clock hand hub.
    for x in (-10,10):
        if q.blink>.5:line([(x-4,-106),(x+4,-106)],WOOD_D,1.9)
        else:
            oval(x,-108,4.2,5.5,WHITE,INK,.7);oval(x+1.7,-108,2,3.0,DARK,None)
            if q.alarm>.5:line([(x-5,-115),(x+5,-110)],WOOD_D,2.1)
    line([(-7,-85),(0,-82 if q.alarm<.5 else -87),(7,-85)],WOOD_D,1.3)
    # Real door aperture. The scissor-link root stays within the dark opening.
    opening=B(8,-151);oval(8,-152,19,21,WOOD_D,INK,1.8);oval(8,-151,15.5,17.5,DARK,INK,1.2)
    # At zero extension the bird is hidden; when the doors open the assembly
    # first peeks out from the opening, then slides forward on linked bars.
    if q.door>.12:
        root=B(13,-151);ext=9+111*q.extension;end=B(13+ext,-151+25*q.peck)
        u=unit(sub(end,root));v=perp(u)
        nlink=5;span=math.hypot(*sub(end,root))/nlink;half=math.sqrt(max(3.5**2,15.5**2-(span/2)**2))
        for k in range(nlink):
            a=add(root,mul(u,span*k));b=add(root,mul(u,span*(k+1)));upper=add(a,mul(v,-half));lower=add(a,mul(v,half));up2=add(b,mul(v,-half));lo2=add(b,mul(v,half))
            d.tube(upper,lo2,2.3,GOLD_D,GOLD_L);d.tube(lower,up2,2.4,GOLD,GOLD_L)
            d.bolt(mix(a,b,.5),2.5,STEEL_L)
        d.box(end,7,8,WOOD_D,INK,1.3,2,ang)
        # In the held windup the bird is tucked close; the door masks the tail.
        bird_at=add(end,rot((8+7*q.extension,0),ang));_bird(d,bird_at,ang+12*q.peck,q.peck)
    # Door leaves are hinged at the aperture sides, not scaled around their
    # centres. A 3/4 side view makes one leaf shorter as it rotates outward.
    # At idle the leaves meet over the dark arch.
    for side in (-1,1):
        hinge=8+side*16;inward=-side
        extent=16*(1-q.door*.86);swing=side*10*q.door
        panel([(hinge,-166),(hinge+inward*extent,-167+swing*.13),(hinge+inward*extent,-134+swing*.35),(hinge,-133)],WOOD_M,INK,1.4)
        line([(hinge+inward*extent*.25,-162),(hinge+inward*extent*.25,-139)],WOOD_L,1.3)
        for yy in [-162,-137]:oval(hinge,yy,2.2,3.2,GOLD_D,INK,.6)
        if q.door<.45:oval(hinge+inward*extent*.80,-150,1.8,1.8,GOLD_L,INK,.6)
    # A clockwork key near the rear, rotating as the machine winds itself.
    key=B(-53,-85);d.tube(B(-43,-85),key,3,GOLD_D,GOLD_L)
    for side in (-1,1):
        c=add(key,polar(7,math.degrees(q.phase)+90*side));d.oval(c,6,4,GOLD,INK,1.0,math.degrees(q.phase));d.disk(c,1.7,WOOD_D,None)
    out=d.finish()
    return anchored_death(out,GROUND) if q.topple>0 else out


def _body_metrics(fw,fh):
    from ...core.measure import body_metrics_for_box
    return body_metrics_for_box((83,45,181,259),fw,fh)


def render(out_dir: str|Path, **opts):
    from ...authoring.sheet_build import build_sheet
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,out_dir=Path(out_dir),frame_size=FRAME_SIZE,
        auto_crop=False,actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
