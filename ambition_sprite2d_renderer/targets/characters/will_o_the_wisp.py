"""A lantern flame without a lantern, from the Starless Hollow.

Curved flame lobes curl behind a bright core. A warm amber core signals a
charge; cold turquoise returns during recovery. Not a creature of the Void.
"""
from __future__ import annotations
import math
from ._magic_character_art import Canvas, add, mul, rot, polar, phase, track, star, curve, metadata, publish
TARGET_NAME='will_o_the_wisp'
FRAME_SIZE=(220,192)
ROWS=[('idle',16,95),('walk',16,75),('notice',8,80),('windup',12,65),('attack_side',36,37),('hit',8,70),('death',18,75)]
ACTOR_METADATA=metadata(TARGET_NAME,"Will-o'-the-Wisp",'Small','Floating','Light','Fly',['flame','spirit'], 'A floating blue-green ghost flame with a warm luminous core and a mischievous face. It drifts in the Starless Hollow, flares amber and darts at travellers. Its glowing tails are procedural curves, not void matter.',True)
WINDUP,ACTIVE,RECOVER=.55,.23,.65

def _render_frame(anim,i,n):
    t=phase(i,n,anim in ('idle','walk','windup'));p=math.tau*t
    bob=3*math.sin(p);stretch=0.;tilt=0.;hot=0.;gape=0.;blink=i in (12,13) and anim=='idle';fade=1.;drift=0.
    if anim=='walk':tilt=17;stretch=.15
    if anim=='notice':hot=.3;bob=-5*math.sin(math.pi*t);gape=.2
    if anim=='windup':hot=.8+.1*math.sin(p);tilt=-14;stretch=-.11;gape=.7
    if anim=='attack_side':
        a=WINDUP/(WINDUP+ACTIVE+RECOVER);b=(WINDUP+ACTIVE)/(WINDUP+ACTIVE+RECOVER)
        hot=track(t,[(0,.87),(a,.87),(a+.04,1),(b,1),(.9,0),(1,0)])
        tilt=track(t,[(0,-14),(a,-14),(a+.055,45),(b,38),(.88,-3),(1,0)])
        stretch=track(t,[(0,-.11),(a,-.11),(a+.055,.32),(b,.28),(1,0)]);gape=hot;drift=12*max(0,stretch)
    if anim=='hit':tilt=-28*math.sin(math.pi*t);stretch=-.13;blink=True;gape=.4;drift=-6*math.sin(math.pi*t)
    if anim=='death':fade=track(t,[(0,1),(.25,1),(.99,0)]);stretch=-.4*t;tilt=-30*t;gape=.3;blink=True
    d=Canvas(FRAME_SIZE);center=(110+drift,105+bob)
    def P(x,y):return add(center,rot((x*(1+stretch),y*(1-stretch*.35)),tilt))
    def shape(points,fill,edge=None,w=1.5):curve(d,[P(*q) for q in points],fill,edge,w)
    def mixc(a,b):return tuple(round(x+(y-x)*hot) for x,y in zip(a,b))+(255,)
    deep=mixc((24,66,96),(124,48,40));mid=mixc((27,148,154),(232,108,49));light=mixc((96,239,205),(255,195,84));cream=mixc((228,255,197),(255,246,167))
    sw=5*math.sin(p);sw2=5*math.cos(p)
    # A single curved flame silhouette; asymmetrical swept tongues read as fire, not a blob.
    shape([(3,40),(-26,43),(-43,26),(-39,3),(-36,-20),(-65,-22+sw),(-58,-48+sw),(-44,-33),(-30,-42),(-25,-57),(-22,-71),(-28,-76+sw2),(-12,-82+sw2),(-14,-52), (15,-58),(22,-72+sw),(39,-44),(24,-36),(36,-27),(57,-14),(54,13),(41,28),(31,41),(13,43),(3,40)],deep,'#153040',2.4)
    shape([(4,36),(-23,38),(-36,16),(-32,-5),(-28,-23),(-48,-29),(-46,-38+sw),(-27,-27),(-12,-43),(-11,-60+sw2),(-4,-42),(16,-36),(22,-49+sw),(23,-34),(37,-23),(43,-9),(50,15),(32,36),(4,36)],mid)
    shape([(4,31),(-20,35),(-28,16),(-25,1),(-22,-13),(-8,-24),(-12,-39+sw2),(1,-30),(12,-21),(18,-30),(28,-18),(38,-13),(36,7),(36,21),(23,33),(4,31)],light)
    shape([(6,27),(-12,27),(-19,16),(-16,4),(-14,-8),(-3,-11),(1,-22),(4,-8),(16,-14),(23,-6),(30,7),(23,27),(6,27)],cream)
    d.line([P(-29,13),P(-24,26),P(-10,34)],light,1.8)
    d.line([P(26,-20),P(36,-8),P(38,3)],cream,1.4)
    # Two narrow eyes bend with its flame, but retain contrast at game scale.
    for x,y,r in [(-7,0,5),(15,-1,5.8)]:
        if blink:d.line([P(x-r,y),P(x+r,y)],'#1b3440',2.8)
        else:
            d.oval(P(x,y),r,7*(1-.35*hot),'#16313b',None,angle=tilt+hot*15*(-1 if x<0 else 1));d.disk(P(x+1.5,y-2.1),1.5,'#f5ffeb',None)
    if gape>.35:d.oval(P(10,17),5+4*gape,4+2*gape,'#24434b',None,angle=tilt)
    else:d.line([P(3,14),P(9,18),P(17,13)],'#24434b',2)
    # Sparks are local flame accents, never floor shadows.
    for j in range(3):
        a=p*.8+j*2.094;pt=P(-25-10*math.sin(a),-32-14*j-5*math.cos(a));star(d,pt,3.5+2*hot,light,points=4)
    out=d.finish()
    if fade<1:out.putalpha(out.getchannel('A').point(lambda a:round(a*fade)))
    return out

def render(out_dir,**opts):return publish(TARGET_NAME,ROWS,_render_frame,FRAME_SIZE,ACTOR_METADATA,(75,75,147,147),out_dir)
TARGETS={TARGET_NAME:{'render':render,'actor_metadata':ACTOR_METADATA}}
