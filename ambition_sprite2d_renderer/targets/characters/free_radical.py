"""Free Radical: an anthropomorphic hydroxyl radical (OH radical).

Oxygen is red and hydrogen white, as in common molecular models. The bond
length is fixed throughout all poses. Two lone pairs and one unpaired dot
are stylized Lewis electron marks; they are not classical electron orbits.
The electric-looking attack is fictional, not a molecular dynamics model.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from PIL import Image
from ._replicator_radical_art import Canvas, INK, add, mul, rot, polar, phase, track, rgbmix, clamp, floating_actor, publish

TARGET_NAME='free_radical'
FRAME_SIZE=(304,224)
CENTER=(151.,116.)
BOND_LENGTH=82.
WINDUP_S,ACTIVE_S,RECOVER_S=.50,.20,.58
ROWS=[('idle',16,100),('walk',16,80),('notice',8,75),('windup',12,65),('attack_side',44,29),('hit',8,75),('death',22,65)]
LOOPS={'idle','walk','windup'}
ACTOR_METADATA=floating_actor(TARGET_NAME,'Free Radical','science',['molecule','hydroxyl','radical'],
    'A stylized hydroxyl radical, OH radical, with one red oxygen and one white hydrogen at a fixed bond length, two paired electron marks and a single highlighted unpaired electron. Its expressions, hovering and crackling lunge are fictional game art, not an electron trajectory simulation.',
    'An aerial enemy that fixes its attention on a target, builds a violet charge and lunges. The electron motif is a visual tell rather than an electron transfer mechanic.')


@dataclass(frozen=True)
class Pose:
    x:float=0.; y:float=0.; tilt:float=0.; bond:float=-154.
    charge:float=0.; gape:float=0.; alarm:float=0.; blink:float=0.
    fade:float=1.; shock:float=0.; phase:float=0.


def pose(anim,i,n):
    t=phase(i,n,anim in LOOPS);p=math.tau*t
    if anim=='idle':return Pose(y=3*math.sin(p),bond=-154+3*math.sin(p),blink=float(i in (11,12)),phase=p)
    if anim=='walk':return Pose(x=2*math.sin(p),y=3*math.cos(p),tilt=6,bond=-166+3*math.cos(p),charge=.13,phase=p)
    if anim=='notice':return Pose(y=-4*math.sin(math.pi*t),tilt=-5,bond=-147,charge=track(t,[(0,0),(.45,.72),(1,.36)]),alarm=.72,gape=.18,phase=p)
    if anim=='windup':return Pose(x=-7,y=0,tilt=-9,bond=-145,charge=.83+.09*math.sin(p),gape=.63,alarm=1,phase=p)
    if anim=='attack_side':
        a=WINDUP_S/(WINDUP_S+ACTIVE_S+RECOVER_S);b=(WINDUP_S+ACTIVE_S)/(WINDUP_S+ACTIVE_S+RECOVER_S)
        k=lambda keys:track(t,keys)
        return Pose(x=k([(0,-7),(a,-7),(a+.065,15),(b,15),(.88,0),(1,0)]),
            y=k([(0,0),(a,0),(a+.08,4),(b,4),(1,0)]),tilt=k([(0,-9),(a,-9),(a+.07,8),(b,7),(.9,-4),(1,0)]),
            bond=k([(0,-145),(a,-145),(a+.07,-171),(b,-171),(.9,-150),(1,-154)]),
            charge=k([(0,.86),(a,.86),(a+.06,1),(b,1),(.85,.2),(1,0)]),
            gape=k([(0,.63),(a,.63),(a+.05,1),(a+.12,.08),(b,.18),(.85,.05),(1,0)]),
            alarm=k([(0,1),(b,1),(1,0)]),shock=k([(0,0),(a,0),(a+.06,1),(b,.65),(.78,0),(1,0)]),phase=p)
    if anim=='hit':return Pose(x=-9*math.sin(math.pi*t),y=-5*math.sin(math.pi*t),tilt=-18*math.sin(math.pi*t),bond=-148,charge=.3,alarm=1,blink=1,gape=.35,shock=.6*math.sin(math.pi*t),phase=p)
    if anim=='death':return Pose(x=0,y=track(t,[(0,0),(.8,12),(1,12)]),tilt=track(t,[(0,0),(.8,62),(1,62)]),bond=track(t,[(0,-154),(.8,-115),(1,-115)]),
        charge=track(t,[(0,.4),(.45,1),(.7,0),(1,0)]),gape=.35,alarm=.6,blink=1,fade=track(t,[(0,1),(.65,1),(1,0)]),shock=track(t,[(0,0),(.35,.6),(.75,0),(1,0)]),phase=p)
    raise ValueError(anim)


def _sphere(d,center,r,palette):
    """Smooth vector-style spherical shading, with a dark outline and rim.

    Nested colored discs model a broad upper-left highlight. All discs are
    internal to the atom silhouette, independent of the molecule's pose.
    """
    shadow,base,light,spec=palette
    d.disk(center,r,shadow,INK,2.3)
    # Offset the centre less than the shrinking radius to keep paint inside.
    for i in range(1,25):
        t=i/25;rr=r*(.97-.78*t)
        c=add(center,(-r*.29*t,-r*.35*t))
        shade=rgbmix(shadow,base,min(1,t*2.9)) if t<.345 else rgbmix(base,light,(t-.345)/.655)
        d.disk(c,rr,shade,None)
    d.oval(add(center,(-r*.35,-r*.48)),r*.20,r*.10,spec,None,angle=-28)
    # Thin lower-right reflected rim, not an external cast shadow.
    d.line([add(center,polar(r*.91,a)) for a in range(18,101,5)],rgbmix(shadow,base,.48),1.5)


def _electron(d,pt,r,charge,radical=False):
    # Lewis marks remain close to the atom. No orbital paths are drawn.
    if radical:
        d.disk(pt,r+3.4,(122,91,197,210),INK,1.3)
        d.disk(pt,r+1.7,(219,169,255),None)
        d.disk(pt,r,(255,233,171),INK,1.1)
        d.disk(add(pt,(-r*.28,-r*.32)),r*.46,(255,255,242),None)
        if charge>.15:
            for a in (35,130,220,305):
                p=add(pt,polar(r+5,a));q=add(pt,polar(r+8+5*charge,a));d.line([p,q],(229,190,255),1.6)
    else:
        d.disk(pt,r+1.0,'#462c57',INK,.9)
        d.disk(pt,r,'#cfa0e7',None)
        d.disk(add(pt,(-.8,-.7)),r*.40,'#f4e2ff',None)


def _render_frame(anim,i,n):
    q=pose(anim,i,n);d=Canvas(FRAME_SIZE);c=add(CENTER,(q.x,q.y))
    def F(x,y):return add(c,rot((x,y),q.tilt))
    h=add(c,polar(BOND_LENGTH,q.bond))
    # Fixed bond length and an exposed metal/pearl connecting segment.
    d.tube(h,c,7.2,'#a8b0c0','#e4e8ee','#6d7689')
    _sphere(d,h,24,((106,121,149),(204,218,232),(250,250,247),(255,255,255)))
    _sphere(d,c,45,((114,31,55),(211,64,71),(255,137,111),(255,205,162)))
    # Two paired Lewis marks, at the upper and lower left edge of oxygen.
    for x,y in [(-29,-36),(-19,-41),(-35,28),(-26,35)]:_electron(d,F(x,y),3.1,0)
    # Face is an expressive mask on the red oxygen sphere.
    for x,y,rx in [(-7,-13,8.7),(16,-13,10.2)]:
        if q.blink>.5:
            d.line([F(x-rx,y+1),F(x,y+3),F(x+rx,y)],'#5b2637',2.6)
        else:
            d.oval(F(x,y),rx,12 if q.alarm<.5 else 9.8,'#fff1dc',INK,1.6,q.tilt)
            d.oval(F(x+3.4,y+1.0),4.2,7.1,'#3b314b',None,angle=q.tilt)
            d.disk(F(x+4.3,y-1),1.4,'#fffaff',None)
        if q.alarm>.3:
            inward=1 if x<0 else -1
            d.line([F(x-rx,y-13-3*inward*q.alarm),F(x+rx,y-13+3*inward*q.alarm)],'#762b40',3.3)
    # Cheek and forward mouth. It gapes on the tell and snaps during active.
    g=q.gape
    if g>.08:
        d.oval(F(15,15),13+2*g,4+13*g,'#502035',INK,1.8,q.tilt+4)
        d.oval(F(16,18+5*g),7.5,3.5*g+1,'#ed7883',None,angle=q.tilt)
        d.poly([F(5,12-6*g),F(10,12-5*g),F(8,16-4*g)],'#ffedd8',None)
        d.poly([F(18,12-6*g),F(23,12-5*g),F(21,16-4*g)],'#ffedd8',None)
    else:
        d.line([F(3,16),F(14,19 if q.alarm<.3 else 14),F(26,14)],'#65253a',2.8)
        d.line([F(11,22),F(21,21)],'#f08b83',1.3)
    d.oval(F(-18,9),6.5,3.2,'#ee8c86',None,angle=q.tilt-12)
    # One highlighted radical dot. It does not follow a classical orbit;
    # its position is an expressive mark beside the molecule.
    electron=F(55+4*q.charge,0)
    if q.charge>.2:
        # Tight charge arcs around the dot, visually attached to the mark.
        for j in range(3):
            a=28+j*112+math.degrees(q.phase)*.18
            pts=[add(electron,polar(12+q.charge*4,a+v)) for v in range(0,62,10)]
            d.line(pts,'#663d92',3.0);d.line(pts,'#dfb6ff',1.5)
    if q.shock>.08:
        # Readable forward strike accent; generated from the same dot each frame.
        for j in (-1,1):
            a=add(electron,(2,j*4));b=add(electron,(9+10*q.shock,j*(6+8*q.shock)));c1=add(electron,(15+11*q.shock,j*3));e=add(electron,(24+13*q.shock,j*(7+7*q.shock)))
            d.line([a,b,c1,e],'#674895',4);d.line([a,b,c1,e],'#f4dcff',1.9)
    _electron(d,electron,6.1+1.7*q.charge,q.charge,radical=True)
    out=d.finish()
    if q.fade<1:out.putalpha(out.getchannel('A').point(lambda a:round(a*q.fade)))
    return out


def _body_metrics(fw,fh):
    from ...core.measure import body_metrics_for_box
    return body_metrics_for_box((52,55,197,163),fw,fh)


def render(out_dir: str|Path, **opts):
    return publish(TARGET_NAME,ROWS,_render_frame,FRAME_SIZE,ACTOR_METADATA,_body_metrics,out_dir,**opts)
