"""Wanda, Starlight Square's wand repairer, in her travelling combat clothes.

The crescent is a wrench for the fittings on a wand as well as a focus for
spells. Its rigid shaft and crescent share the wrist transform, and the
cape, hat, hair and scarf follow the body pose. This is an original magical
fighter, not a Mary-O recolour; authored facing right.
"""
from __future__ import annotations
import math
from PIL import Image
from ._magic_character_art import Canvas, INK, add, sub, mul, norm, unit, perp, rot, polar, mix, track, phase, star, curve, metadata, publish, anchored_death
TARGET_NAME='wanda'
CHARACTER_ID='npc_magical_wanda'
FRAME_SIZE=(400,330)
CX,GROUND=192,283
# clip, startup, active, recovery, aim (degrees, positive down), attack type
# The combat data is authored to these same timing boundaries.
STRIKES={
 'jab':(.08,.08,.20,-10,'jab'), 'attack_side':(.15,.12,.30,-5,'sweep'),
 'attack_up':(.14,.12,.30,-90,'sweep'), 'attack_down':(.16,.12,.33,34,'low'),
 'attack_dash':(.13,.18,.35,-4,'dash'), 'attack_air':(.13,.18,.29,-35,'spin'),
 'attack_air_forward':(.17,.13,.34,-5,'sweep'), 'attack_air_back':(.17,.13,.31,180,'sweep'),
 'attack_air_up':(.14,.14,.30,-90,'sweep'), 'attack_air_down':(.20,.16,.38,90,'sweep'),
 'smash_forward':(.30,.17,.43,0,'spell'), 'smash_up':(.28,.16,.40,-90,'spell'),
 'smash_down':(.27,.18,.45,48,'spell'), 'special':(.30,.08,.37,0,'cast'),
 'special_forward':(.22,.20,.42,-8,'dash'), 'special_up':(.19,.18,.45,-90,'spell'),
 'special_down':(.26,.18,.43,54,'spell'), 'special_air_down':(.21,.19,.44,90,'spell'),
 'grab':(.12,.11,.27,0,'grab'), 'grab_dash':(.15,.12,.32,0,'grab'),
 'pummel':(.09,.07,.13,0,'jab'), 'throw_forward':(.13,.10,.22,0,'spell'),
 'throw_back':(.14,.10,.23,180,'spell'), 'throw_up':(.14,.10,.24,-90,'spell'),
 'throw_down':(.16,.11,.24,65,'spell'),
}
BASE_ROWS=[('idle',16,95),('walk',16,76),('run',16,60),('jump',10,65),('fall',10,80),('crouch',8,80),('land',8,55),('notice',8,75),('windup',10,70),('shield',8,80),('dodge',10,55),('hit',10,65),('death',20,75),('taunt',20,75)]
ROWS=BASE_ROWS+[(k, max(10,round(sum(v[:3])*24)),round(1000*sum(v[:3])/max(10,round(sum(v[:3])*24)))) for k,v in STRIKES.items()]
ACTOR_METADATA=metadata(CHARACTER_ID,'Wanda','Standard','Biped','Medium','Walk',['wand','witch','mechanic'], 'The wand repairer of Starlight Square, dressed in a teal travelling coat, violet pointed hat, red scarf and golden moon fittings. Her crescent wrench is both a repair tool and a focus. Her movement, wand strikes and spellcasting poses are custom authored.')
ACTOR_METADATA['gameplay_description']='A midweight magical staff fighter with directional melee, ranged star shot and a rising spell. She is a friendly resident unless placed into combat.'
PURPLE='#574776';P_D='#352a4e';P_L='#8e78b5';P_H='#bba8d9';TEAL='#277c83';T_D='#17464f';T_L='#48adad';T_H='#83d7c9';GOLD='#d3a453';G_D='#87643d';G_L='#ffe0a0';SKIN='#e7b292';S_D='#b87567';S_L='#ffdbc0';HAIR='#65424d';H_D='#413040';H_L='#a76a69';RED='#b44c62';R_D='#762e47';R_L='#eb8792';BOOT='#38334f';WHITE='#ffefd4';DARK='#242939'


def limb(d,a,b,r,fill,hi):
    d.line([a,b],INK,2*r+3);d.line([a,b],fill,2*r);d.line([add(a,(-r*.26,-r*.3)),add(b,(-r*.26,-r*.3))],hi,max(1.1,r*.48))


def _joint(a,b,length,bend):
    # Elbow/knee along the perpendicular bisector, clamped to a reachable chain.
    mid=mix(a,b,.5);direction=unit(sub(b,a));h=math.sqrt(max(0,length**2-(norm(sub(b,a))/2)**2));return add(mid,mul(perp(direction),h*bend))


def _render_frame(anim,i,n):
    t=phase(i,n,anim in ('idle','walk','run','windup','shield','fall'));p=math.tau*t
    stride=0; bob=.8*math.sin(p);lean=0;aim=-62;reach=0;charge=0;alarm=0;air=0;crouch=0;topple=0;blink=anim=='idle' and i in (11,12);cast=False;spin=0;step=0
    if anim in ('walk','run'):stride=1 if anim=='walk' else 1.35;lean=7 if anim=='walk' else 13;bob=2*abs(math.sin(p));aim=-48
    if anim=='jump':air=1;aim=-72;lean=-7;bob=-3;reach=.1*math.sin(math.pi*t)
    if anim=='fall':air=1;aim=-35;lean=5;bob=2
    if anim=='crouch':crouch=24;lean=12;aim=5
    if anim=='land':crouch=25*math.sin(math.pi*t);aim=-30
    if anim=='notice':lean=-6;alarm=.6;aim=-78;bob=-4*math.sin(math.pi*t)
    if anim=='windup':lean=-10;aim=-95;charge=.35;alarm=1
    if anim=='shield':aim=-15;charge=.48;alarm=.6;crouch=7;reach=.3
    if anim=='dodge':crouch=25*math.sin(math.pi*t);lean=-28*math.sin(math.pi*t);aim=-32;step=-14*math.sin(math.pi*t)
    if anim=='hit':lean=-19*math.sin(math.pi*t);aim=-118;alarm=1;blink=True;step=-7*math.sin(math.pi*t)
    if anim=='death':topple=track(t,[(0,0),(.13,0),(.78,1),(1,1)]);lean=-7;aim=-30;blink=True;alarm=1
    if anim=='taunt':aim=track(t,[(0,-62),(.25,-105),(.7,-105),(1,-62)]);charge=math.sin(math.pi*t);reach=.2
    if anim in STRIKES:
        su,ac,re,target,kind=STRIKES[anim];a=su/(su+ac+re);b=(su+ac)/(su+ac+re)
        pulse=track(t,[(0,0),(a*.85,0),(a,1),(b,1),(1,0)])
        tell=target-50 if target<100 else target+40
        if target==-90:tell=-32
        if target==90:tell=15
        if kind=='spin':target=-35+360*max(0,min(1,(t-a)/(b-a)));tell=-35
        aim=track(t,[(0,-62),(a*.72,tell),(a,target),(b,target),(1,-62)]) if kind!='spin' else target
        reach=pulse;alarm=1;lean=track(t,[(0,0),(a*.72,-9),(a,10 if target in (-10,-5,0,-4,-8) else 3),(b,8),(1,0)])
        charge=track(t,[(0,0),(a*.8,.65),(a,1),(b,1),(1,0)]) if kind in ('spell','cast','dash','grab','spin') else .2*pulse
        cast=kind in ('spell','cast','dash','spin');air=float('air' in anim or anim=='special_up');crouch=10*pulse if kind=='low' or anim in ('smash_down','special_down') else 0
        if kind=='dash':step=9*pulse;lean=17*pulse
        if kind=='grab':reach=.75*pulse;aim=-35;charge=.45*pulse
    # Root rig. The hip follows the pose; boots solve to the ground, not the other way around.
    d=Canvas(FRAME_SIZE,2);hip=(CX+step,GROUND-67+crouch+bob-4*air)
    def B(x,y):return add(hip,rot((x,y),lean))
    def draw_shape(points,fill,edge=INK,w=1.8):curve(d,[B(*q) for q in points],fill,edge,w)
    # Cloak behind the body, with layered crescent hem and scarf tails.
    flow=11*stride+12*reach+5*math.sin(p)
    draw_shape([(-17,-65),(-32,-50),(-27-flow,-27),(-43-flow,0),(-31-flow,9),(-21,6),(-11,0),(3,-9),(10,-26),(9,-53),(1,-66),(-8,-69),(-17,-65)],P_D)
    draw_shape([(-14,-60),(-25,-46),(-19-flow,-20),(-36-flow,-1),(-28-flow,4),(-17,-1),(-11,-6),(2,-20),(4,-38),(3,-58),(-4,-65),(-10,-64),(-14,-60)],PURPLE,None)
    d.line([B(-36-flow,0),B(-22-flow,2),B(-13,-5)],GOLD,2.2)
    # Hair behind shoulders, a deliberate asymmetric side curl.
    draw_shape([(-31,-102),(-47,-96),(-47,-62),(-36,-53),(-48,-45),(-22,-41),(-14,-53),(-4,-45),(9,-57),(16,-72),(26,-97),(4,-119),(-31,-102)],HAIR)
    # Legs: near and far, boots fixed to the ground on support phases.
    for far in (True,False):
        side=-1 if far else 1;ph=p+(math.pi if far else 0);sx=side*12+stride*23*math.sin(ph);lift=stride*12*max(0,math.cos(ph));
        if air:
            tuck=(.5+.5*math.sin(math.pi*t)) if anim=='jump' else .55+.35*reach
            sx=side*17+(-10 if far else 14)*tuck;lift=12+17*tuck+(10 if far else 0)
            if anim in ('special_up','attack_air_up'):sx=side*13;lift=14+7*tuck
            if anim in ('attack_air_down','special_air_down'):sx=side*17;lift=8+6*tuck
        foot=(CX+step+sx,GROUND-8-lift);ank=add(foot,(-4,-7));a=B(side*10,-2);knee=_joint(a,ank,29,-1)
        limb(d,a,knee,8,P_D if far else PURPLE,P_L);limb(d,knee,ank,7,BOOT,P_L)
        d.poly([add(foot,(-12,-19)),add(foot,(2,-19)),add(foot,(6,-8)),add(foot,(17,-5)),add(foot,(20,3)),add(foot,(18,7)),add(foot,(-12,7)),add(foot,(-14,1))],BOOT if far else PURPLE,INK,2)
        d.poly([add(foot,(-12,2)),add(foot,(19,2)),add(foot,(18,7)),add(foot,(-12,7))],P_D,INK,1)
        d.line([add(foot,(-10,-14)),add(foot,(3,-14))],GOLD,3);d.box(add(foot,(2,-13)),3,3,G_L,G_D,.9,1)
    # Far sleeve and hand, distinct free hand used for casting and grabbing.
    shoulder=B(-18,-51);free=B(-28-10*reach,-27-12*reach)
    if anim in ('grab','grab_dash'):free=B(9+29*reach,-36-3*reach)
    elif anim=='special_up':free=B(-28-6*reach,-37-10*reach)
    elbow=_joint(shoulder,free,20,1)
    limb(d,shoulder,elbow,8,T_D,T_L);limb(d,elbow,free,6.5,TEAL,T_L);d.disk(free,7.4,SKIN,INK,1.5)
    # Coat (tailored silhouette), short vest, waist belt and crescent clasp.
    draw_shape([(-19,-59),(-9,-66),(11,-66),(20,-54),(24,-43),(15,-29),(14,-20),(20,-8),(27,3),(27,10),(11,13),(-11,12),(-27,9),(-26,-5),(-15,-17),(-17,-24),(-24,-39),(-26,-50),(-19,-59)],TEAL)
    draw_shape([(-19,-56),(-22,-46),(-17,-34),(-13,-25),(-17,-11),(-23,1),(-23,7),(-17,10),(-8,9),(-6,7),(-7,-15),(-7,-39),(-8,-58),(-11,-62),(-15,-60),(-19,-56)],T_D,None)
    d.poly([B(-5,-58),B(8,-58),B(10,-24),B(1,-18),B(-6,-25)],WHITE,INK,1.3)
    d.poly([B(-17,-60),B(-4,-58),B(1,-36),B(-12,-45)],T_H,INK,1.1);d.poly([B(16,-59),B(6,-58),B(1,-36),B(17,-47)],T_L,INK,1.1)
    d.line([B(-19,-18),B(17,-18)],G_D,7);d.box(B(3,-18),7,5,GOLD,INK,1.1,2,lean);star(d,B(3,-18),4,G_L)
    for y in (-31,-23):d.disk(B(7,y),1.8,GOLD,G_D,.6)
    d.line([B(14,-12),B(23,5)],T_H,2);d.line([B(-23,8),B(-12,10),B(4,10),B(22,8)],GOLD,2)
    # Neck and scarf; the tails have a coherent origin at the knot.
    d.oval(B(0,-62),8,12,SKIN,INK,1.4,lean);d.poly([B(-13,-65),B(-30-flow,-63),B(-43-flow,-52+3*math.sin(p)),B(-39-flow,-65),B(-23,-73),B(-11,-73)],RED,INK,1.5)
    d.oval(B(0,-64),20,7,RED,INK,1.6,lean-5);d.oval(B(-12,-64),8,7,R_L,R_D,1.1,lean);d.line([B(-1,-67),B(16,-66)],R_L,2)
    # Head with deliberately large, readable eyes, brows and silhouette.
    head=B(4,-94);ha=lean*.65
    def H(x,y):return add(head,rot((x,y),ha))
    def hshape(points,fill,edge=INK,w=1.8):curve(d,[H(*q) for q in points],fill,edge,w)
    hshape([(-28,-17),(-20,-35),(9,-34),(25,-20),(35,-9),(32,7),(26,17),(21,29),(-6,34),(-20,21),(-32,12),(-34,-5),(-28,-17)],S_D)
    hshape([(-25,-15),(-17,-29),(10,-31),(25,-18),(32,-7),(31,6),(25,15),(19,25),(-4,29),(-16,18),(-27,11),(-29,-3),(-25,-15)],SKIN,None)
    d.oval(H(-26,4),8,10,SKIN,INK,1.6,ha);d.oval(H(-27,5),3.5,5,S_D,None,angle=ha);d.disk(H(-27,12),2.6,G_L,G_D,.8)
    # Three-quarter eye placement; glasses-free, bright amber irises.
    for x,y,rx in [(-6,-1,8),(16,-2,7)]:
        if blink:d.line([H(x-rx,y),H(x+rx,y-1)],H_D,2.3)
        else:
            d.oval(H(x,y),rx,10-2*alarm,WHITE,H_D,1.2,ha);d.oval(H(x+2.3,y+.2),4.4,6.1,G_D,None,angle=ha);d.oval(H(x+2.9,y),2.5,4.2,DARK,None,angle=ha);d.disk(H(x+1.3,y-3),1.7,WHITE,None)
            d.line([H(x-rx,-12),H(x+rx,-11+4*alarm)],H_D,2.1)
    d.line([H(12,4),H(17,8),H(11,10)],S_D,1.3)
    d.line([H(2,17),H(10,19 if not alarm else 15),H(18,15)],H_D,1.8)
    d.oval(H(-17,11),6,2.8,'#d58c83',None,angle=ha)
    # Hair swept under the broad hat; scalloped curls rather than spikes.
    hshape([(-28,-15),(-31,-35),(-12,-44),(9,-36),(30,-38),(38,-25),(32,-14),(26,-17),(23,-22),(22,-27),(13,-14),(3,-11),(-3,-15),(-5,-12),(-14,-9),(-16,-16),(-20,-8),(-25,2),(-28,9),(-35,-1),(-33,-9),(-28,-15)],HAIR)
    d.line([H(-24,-22),H(-15,-29),H(-4,-29)],H_L,2.5);d.line([H(9,-31),H(19,-30),H(26,-23)],H_L,2)
    # Pointed soft hat, asymmetric floppy tip, band and crescent buckle.
    hshape([(-38,-28),(-30,-43),(-20,-66),(-15,-79),(-11,-93),(10,-93),(20,-76),(21,-66),(9,-65),(8,-61),(20,-46),(32,-35),(39,-28),(18,-22),(-15,-21),(-38,-28)],PURPLE)
    hshape([(-27,-33),(-20,-47),(-10,-67),(-13,-80),(-5,-91),(12,-83),(16,-76),(3,-77),(-4,-68),(-2,-58),(3,-49),(12,-38),(15,-30),(-3,-24),(-19,-28),(-27,-33)],P_L,None)
    d.poly([H(-28,-40),H(24,-40),H(30,-30),H(-34,-30)],P_D,INK,1.5)
    d.box(H(10,-35),7,5,GOLD,INK,1.1,2,ha);d.disk(H(10,-35),3.3,P_D,None)
    d.oval(H(0,-28),45,8,P_D,INK,1.9,ha+2);d.line([H(-40,-29),H(-15,-23),H(17,-23),H(40,-29)],P_L,2)
    star(d,H(-11,-57),5,G_L,points=4);star(d,H(1,-72),2.8,G_L,points=4)
    # Near arm, grip and rigid wand shaft. Grip point is reachable from shoulder.
    shoulder=B(18,-50);direction=polar(1,aim);grip=add(shoulder,add(mul(direction,19+22*reach),(8,9*(1-reach))))
    if norm(sub(grip,shoulder))>45:grip=add(shoulder,mul(unit(sub(grip,shoulder)),45))
    elbow=_joint(shoulder,grip,24,1);limb(d,shoulder,elbow,9,TEAL,T_L);limb(d,elbow,grip,7.5,TEAL,T_H);d.oval(grip,9,8,SKIN,INK,1.6,aim);d.line([add(grip,rot((-5,-2),aim)),add(grip,rot((3,-2),aim))],S_D,1.4)
    base=add(grip,mul(direction,-16));tip=add(grip,mul(direction,55));d.tube(base,tip,4.7,P_D,P_H,G_D);d.tube(add(grip,mul(direction,14)),tip,3.6,GOLD,G_L,G_D);d.disk(base,5,GOLD,INK,1.2)
    # Crescent wrench jaws form a genuine open shape. The opening faces the strike.
    def W(x,y):return add(tip,rot((x,y),aim))
    d.poly([W(-5,-7),W(2,-17),W(14,-20),W(20,-15),W(12,-7),W(5,-5),W(5,5),W(12,7),W(20,15),W(14,20),W(2,17),W(-5,7)],GOLD,INK,1.7)
    d.line([W(1,-13),W(11,-16),W(15,-15)],G_L,2);d.line([W(1,13),W(11,16),W(15,15)],G_D,2)
    star(d,W(8,0),4.5,T_H,INK,4)
    # Magical arcs remain attached to the focus. Spell projectile travels in the engine, not in a baked frame.
    if charge>.1:
        r=7+charge*9;star(d,W(21,0),r,G_L,None,4,aim-90)
        if cast and charge>.75:
            for j in range(5):
                a=aim-100+j*42;pt=add(W(21,0),polar(15+5*math.sin(p+j),a));star(d,pt,3.7,T_H if j%2 else G_L,None,4,a)
    # Distinct spell silhouettes: a small radial burst, crescent sweep and
    # rising streamers, with all sparks within the authored pose canvas.
    if cast and charge>.75:
        amt=(charge-.75)/.25
        if anim in ('smash_forward','special_forward','attack_air'):
            center=W(8,0)
            for k in range(2):
                r=24+8*k;arc=[add(center,polar(r,aim-80+j*10)) for j in range(17)]
                d.line(arc,(112,216,206,round(175*amt)),2.1-k*.5)
        elif anim in ('smash_up','special_up'):
            for side in (-1,1):
                for j in range(3):star(d,B(side*(29+8*j),-10-18*j),4+2*amt,(255,222,155,round(210*amt)),points=4)
        elif anim in ('smash_down','special_down','special_air_down'):
            center=W(8,0)
            for j in range(4):star(d,add(center,(-25+j*17,-9-8*math.sin(j*1.5))),4+2*amt,T_H,points=4)
    im=d.finish()
    if topple:
        # Rotate only after the full rig is drawn, around the planted character.
        im=im.rotate(-78*topple,resample=Image.Resampling.BICUBIC,center=(CX,GROUND-63));im=anchored_death(im,GROUND)
    return im


def render(out_dir,**opts):return publish(TARGET_NAME,ROWS,_render_frame,FRAME_SIZE,ACTOR_METADATA,(155,90,230,284),out_dir,True)
TARGETS={TARGET_NAME:{'render':render,'actor_metadata':ACTOR_METADATA}}
