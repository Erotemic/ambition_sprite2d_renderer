"""Hedge Fund, the literal financial shrub of Capital.

A clipped hedge with roots for feet, banknotes for leaves, a few coins growing
on twigs and brass-rimmed spectacles. Its woody branch arm winds up and sweeps
forward; the foliage and banknotes are attached to the articulated geometry.
The swipe is a normal melee action, not a projectile or a currency mechanic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

TARGET_NAME = 'hedge_fund'
FRAME_SIZE = (310, 240)
SUPER = 3
CX, GROUND = 139., 218.
WINDUP_S, ACTIVE_S, RECOVER_S = .68, .28, .72
TOTAL_S = WINDUP_S + ACTIVE_S + RECOVER_S
ROWS = [
    ('idle', 16, 100), ('walk', 16, 85), ('notice', 8, 75),
    ('windup', 12, 60), ('attack_side', 48, 35), ('hit', 8, 75),
    ('death', 18, 90),
]
LOOPS = {'idle', 'walk', 'notice', 'windup'}
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Hedge Fund'},
    'body': {'body_plan': 'Biped', 'body_kind': 'Standard', 'mass_class': 'Heavy',
             'locomotion_hint': 'WalkHeavy', 'traits': ['enemy', 'business', 'plant']},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'tags': ['enemy', 'business', 'plant', TARGET_NAME],
    'authoring_description': (
        'A literal pun on a hedge fund: a manicured living hedge with banknote '
        'leaves, coins growing on twigs, brass spectacles, and articulated roots. '
        'The branch swipe and falling foliage are fictional combat art, not claims '
        'about actual investment funds.'),
    'gameplay_description': (
        'A slow grounded enemy. It recoils and coils its thorny branch, then '
        'swings forward. The recovery is long enough to retaliate. The money '
        'leaves and falling coins are presentation only.'),
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
}
INK = '#203a32'
DEEP = '#254a3b'
SHADE = '#34624b'
GREEN = '#4b8453'
MID = '#67975a'
LIGHT = '#8eb86b'
LIME = '#b7cf88'
GOLD = '#d6ab50'
GOLD_D = '#916238'
GOLD_L = '#ffe2a0'
WOOD = '#806044'
WOOD_D = '#503d36'
WOOD_L = '#b39560'
MINT = '#cce2a3'
NOTE = '#8bb875'
NOTE_D = '#356b50'
CREAM = '#f9edc6'
MOUTH = '#263b31'


def clamp(t):
    return max(0., min(1., t))


def smooth(t):
    t = clamp(t)
    return t*t*(3-2*t)


def lerp(a,b,t):
    return a+(b-a)*t


def track(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if t <= b:
            return lerp(x,y,smooth((t-a)/(b-a)))
    return keys[-1][1]


def add(a,b):
    return a[0]+b[0],a[1]+b[1]


def rot(p,a):
    t=math.radians(a); c,s=math.cos(t),math.sin(t)
    return c*p[0]-s*p[1],s*p[0]+c*p[1]


def v(a,l):
    return rot((l,0),a)


def bez(points, steps=12):
    assert (len(points)-1)%3==0
    out=[points[0]]
    for i in range(0,len(points)-1,3):
        a,b,c,d=points[i:i+4]
        for j in range(1,steps+1):
            t=j/steps;q=1-t
            out.append(tuple(q**3*a[k]+3*q*q*t*b[k]+3*q*t*t*c[k]+t**3*d[k] for k in range(2)))
    return out


class Canvas:
    def __init__(self):
        self.image=Image.new('RGBA',tuple(v*SUPER for v in FRAME_SIZE))
        self.d=ImageDraw.Draw(self.image)

    def line(self,points,col=INK,w=1.4,closed=False):
        p=[(x*SUPER,y*SUPER) for x,y in points]
        if closed:
            p.append(p[0])
        self.d.line(p,fill=col,width=max(1,round(w*SUPER)),joint='curve')
        if not closed:
            r=w*SUPER/2
            for x,y in (p[0],p[-1]):
                self.d.ellipse((x-r,y-r,x+r,y+r),fill=col)

    def poly(self,points,col,edge=INK,w=2):
        self.d.polygon([(x*SUPER,y*SUPER) for x,y in points],fill=col)
        if edge:
            self.line(points,edge,w,True)

    def shape(self,points,col,edge=INK,w=2):
        self.poly(bez(points),col,edge,w)

    def curve(self,points,col=INK,w=1.4):
        self.line(bez(points),col,w)

    def oval(self,c,rx,ry,col,edge=INK,w=1.5,angle=0):
        pts=[add(c,rot((rx*math.cos(t),ry*math.sin(t)),angle))
             for t in (math.tau*i/44 for i in range(44))]
        self.poly(pts,col,edge,w)

    def finish(self,fade):
        if fade<1:
            self.image.putalpha(self.image.getchannel('A').point(lambda a:round(a*fade)))
        return self.image.resize(FRAME_SIZE,Image.Resampling.LANCZOS)


@dataclass(frozen=True)
class Pose:
    center: tuple[float,float]
    tilt: float
    sx: float
    sy: float
    phase: float
    stride: float
    arm1: float
    arm2: float
    far1: float
    far2: float
    mood: float
    blink: float
    dead: float
    fade: float
    shake: float


def pose(anim,i,n):
    t=i/(n if anim in LOOPS else max(1,n-1)); p=math.tau*t
    bob=1.3*math.sin(p); x=CX; tilt=-1.; sx=sy=1.
    stride=0.; arm1,arm2=70.,22.; far1,far2=116.,64.
    mood=.18;blink=max(0.,math.cos(p-4.55))**55
    dead=0.;fade=1.;shake=0.
    if anim=='walk':
        stride=1.;bob=1.7*abs(math.sin(p));tilt=3.+2.2*math.sin(p)
        arm1+=13*math.sin(p);arm2+=11*math.sin(p+.45)
        far1-=9*math.sin(p);far2-=12*math.sin(p)
    elif anim=='notice':
        bob=-3.+.8*math.sin(p);tilt=-5.;mood=.36;blink=0.
        arm1,arm2=10.,-28.;far1,far2=127.,58.
        sx,sy=.96,1.04
    elif anim=='windup':
        # Pinned by the simulation clock: every frame is the same full tell.
        bob=5.+.6*math.sin(p);tilt=-7.;sx,sy=1.05,.95
        arm1,arm2=-78.+2*math.sin(p),-122.+3*math.sin(p)
        far1,far2=145.,57.;mood=.86;blink=0.;shake=.4
    elif anim=='attack_side':
        # Move progress includes startup, even while windup is pinned over it.
        sec=t*TOTAL_S
        start=WINDUP_S; end=start+ACTIVE_S
        arm1=track(sec,[(0,70),(.22,12),(.44,-78),(start,-78),
                        (start+.11,-20),(start+.19,3),(end,22),(end+.18,53),(TOTAL_S,70)])
        arm2=track(sec,[(0,22),(.22,-28),(.44,-122),(start,-122),
                        (start+.11,-5),(start+.19,12),(end,36),(end+.18,65),(TOTAL_S,22)])
        tilt=track(sec,[(0,-1),(.44,-7),(start,-7),(start+.15,8),(end,9),(end+.3,1),(TOTAL_S,-1)])
        bob=track(sec,[(0,0),(start,5),(start+.16,-2),(end,4),(end+.22,6),(TOTAL_S,0)])
        x+=track(sec,[(0,0),(start,-3),(start+.14,8),(end,6),(TOTAL_S,0)])
        sx=track(sec,[(0,1),(start,1.05),(start+.16,.98),(end,1.04),(TOTAL_S,1)])
        sy=track(sec,[(0,1),(start,.95),(start+.16,1.02),(end,.95),(TOTAL_S,1)])
        mood=track(sec,[(0,.18),(start,.86),(start+.12,1),(end,.94),(end+.3,.52),(TOTAL_S,.18)])
        far1=track(sec,[(0,116),(start,145),(start+.16,93),(end,109),(TOTAL_S,116)])
        far2=track(sec,[(0,64),(start,57),(start+.16,150),(end,105),(TOTAL_S,64)])
        blink=0.
    elif anim=='hit':
        f=math.sin(math.pi*t);x-=6*f;tilt=-1-13*f;bob=5*f;sx=1+.09*f;sy=1-.09*f
        arm1,arm2=70-55*f,22-50*f;far1,far2=116+25*f,64-20*f
        mood=.7;blink=f;shake=f
    elif anim=='death':
        dead=smooth(t);tilt=-1-14*dead;bob=65*dead;sx=1+.13*dead;sy=1-.48*dead
        # Clamp the lowest point of the tilted, compressed topiary to the floor.
        bottom=max(rot((u*sx,vv*sy),tilt)[1] for u,vv in OUTLINE)
        bob=min(bob,GROUND-132-bottom-6)
        x-=6*dead;arm1,arm2=70-18*dead,22+6*dead;far1,far2=116+16*dead,64+40*dead
        mood=.12;blink=dead;fade=1-.12*dead;shake=dead
    return Pose((x,132+bob),tilt,sx,sy,p,stride,arm1,arm2,far1,far2,mood,blink,dead,fade,shake)


def B(q,x,y):
    return add(q.center,rot((x*q.sx,y*q.sy),q.tilt))


def leaf(d,c,size,angle,col=LIGHT,edge=None,vein=True):
    def P(x,y):return add(c,rot((x*size,y*size),angle))
    d.shape([P(-.75,0),P(-.25,-.50),P(.25,-.45),P(.77,0),
             P(.25,.45),P(-.25,.50),P(-.75,0)],col,edge,.85)
    if vein:
        d.curve([P(-.54,0),P(-.17,-.04),P(.12,.04),P(.52,0)],NOTE_D if col!=DEEP else WOOD_D,.75)


def dollar(d,c,size,angle,col):
    def P(x,y):return add(c,rot((size*x,size*y),angle))
    d.curve([P(.25,-.32),P(-.18,-.57),P(-.50,-.1),P(-.04,0),
             P(.44,.08),P(.26,.50),P(-.25,.31)],col,max(.9,size*.105))
    d.line([P(0,-.56),P(0,.56)],col,max(.75,size*.08))


def note(d,c,w,angle,twist=0.):
    """Money leaf: a curved banknote with ornamental border and engraved oval."""
    h=w*.54
    def P(x,y):return add(c,rot((x*w,y*h),angle))
    p=[P(-.5,-.48),P(-.18,-.61+twist),P(.16,-.36+twist),P(.5,-.48),
       P(.47,-.12),P(.49,.22),P(.50,.48),P(.14,.60+twist),P(-.16,.37+twist),P(-.5,.48),
       P(-.48,.16),P(-.51,-.12),P(-.5,-.48)]
    d.shape(p,NOTE,INK,1.35)
    d.shape([P(-.40,-.34),P(-.18,-.44+twist),P(.17,-.21+twist),P(.40,-.34),
             P(.39,-.08),P(.39,.15),P(.40,.34),P(.16,.44+twist),P(-.15,.22+twist),P(-.40,.34),
             P(-.39,.10),P(-.39,-.10),P(-.40,-.34)],MINT,NOTE_D,.7)
    d.oval(P(0,0),w*.13,h*.29,NOTE_D,None,angle=angle)
    dollar(d,P(0,0),h*.55,angle,CREAM)
    for x in (-.29,.29):
        d.line([P(x-.04,-.12),P(x+.04,-.12)],NOTE_D,.9)
        d.line([P(x-.04,.12),P(x+.04,.12)],NOTE_D,.9)


def coin(d,c,r,angle=0,edge_on=1.):
    d.oval(c,r*edge_on,r,GOLD_D,INK,1.1,angle)
    cc=add(c,rot((-.7*edge_on,-.5),angle))
    d.oval(cc,r*.84*edge_on,r*.86,GOLD,None,angle=angle)
    d.oval(cc,r*.64*edge_on,r*.66,GOLD_L,GOLD_D,.75,angle)
    if edge_on>.55:
        dollar(d,cc,r*.95,angle,GOLD_D)


def sprig(d,start,end,kind,size,angle):
    d.curve([start,add(start,(3,-6)),add(end,(-3,4)),end],WOOD_D,2.1)
    if kind=='note':
        note(d,end,size,angle,.10)
    else:
        coin(d,end,size,angle)


def draw_root(d,q,far):
    sign=-1 if far else 1
    side=-29 if far else 24
    root=B(q,side,37)
    phase=q.phase+(math.pi if far else 0)
    step=q.stride*math.sin(phase)*11
    lift=q.stride*max(0.,math.cos(phase))*8
    foot=(CX+side+step-sign*12*q.dead,GROUND-2-lift)
    if q.dead:
        foot=(foot[0]+(-12 if far else 19)*q.dead,GROUND-2)
    knee=(lerp(root[0],foot[0],.50)+7*sign*(1-q.dead),lerp(root[1],foot[1],.52)-3*q.dead)
    color=WOOD_D if far else WOOD
    d.curve([root,add(root,(sign*5,7)),add(knee,(-5,0)),knee],INK,18)
    d.curve([root,add(root,(sign*5,7)),add(knee,(-5,0)),knee],color,14)
    d.curve([knee,add(knee,(sign*4,5)),add(foot,(-4,-8)),add(foot,(0,-7))],INK,14)
    d.curve([knee,add(knee,(sign*4,5)),add(foot,(-4,-8)),add(foot,(0,-7))],color,10)
    fx,fy=foot
    d.shape([(fx-8,fy-10),(fx-5,fy-12),(fx+2,fy-10),(fx+5,fy-6),
             (fx+10,fy-5),(fx+17,fy-3),(fx+15,fy),(fx+8,fy+1),(fx-7,fy+1),(fx-11,fy),
             (fx-13,fy-4),(fx-12,fy-7),(fx-8,fy-10)],color,INK,2)
    d.curve([(fx-7,fy-7),(fx-2,fy-7),(fx+2,fy-4),(fx+8,fy-3)],WOOD_L if not far else WOOD,1.5)
    d.curve([add(root,(0,5)),add(root,(1,11)),add(knee,(-2,-3)),knee],WOOD_L if not far else WOOD,2)
    d.line([add(knee,(-4,1)),add(knee,(4,4))],WOOD_D,1.2)


def branch(d,q,far=False):
    # Two main lengths stay fixed in every pose. The distal twig fans follow
    # the endpoint, so the money never floats independently of the weapon.
    start=B(q,-45 if far else 49,5 if far else -2)
    a=(q.far1 if far else q.arm1)+q.tilt
    b=(q.far2 if far else q.arm2)+q.tilt
    elbow=add(start,v(a,28 if far else 31))
    end=add(elbow,v(b,26 if far else 38))
    if q.dead:
        # Lay the ends along the ground without letting the roots penetrate it.
        end=(end[0],min(end[1],GROUND-28));elbow=(elbow[0],min(elbow[1],GROUND-23))
    wood=WOOD_D if far else WOOD
    # Rounded, tapered bark segments with distinct joint and wood grain.
    for aa,bb,width in [(start,elbow,17 if far else 21),(elbow,end,11 if far else 15)]:
        ax,ay=aa;bx,by=bb;ang=math.degrees(math.atan2(by-ay,bx-ax));length=math.hypot(bx-ax,by-ay)
        def P(x,y):return add(aa,rot((x,y),ang))
        d.shape([P(-4,-width*.37),P(length*.23,-width*.66),P(length*.68,-width*.46),P(length+3,-width*.28),
                 P(length+6,0),P(length+4,width*.32),P(length,width*.37),
                 P(length*.55,width*.56),P(length*.16,width*.48),P(-4,width*.4),
                 P(-8,width*.20),P(-8,-width*.16),P(-4,-width*.37)],wood,INK,1.9)
        d.curve([P(2,-width*.22),P(length*.3,-width*.35),P(length*.65,-width*.18),P(length-2,-width*.15)],WOOD_L if not far else WOOD,1.4)
        d.curve([P(length*.23,width*.17),P(length*.43,width*.31),P(length*.58,width*.06),P(length*.8,width*.19)],WOOD_D,1.1)
        # A small thorn built into the branch silhouette.
        d.poly([P(length*.38,-width*.37),P(length*.45,-width*.93),P(length*.58,-width*.41)],wood,INK,1.)
    d.oval(elbow,7,7,wood,INK,1.2)
    d.curve([add(elbow,(-3,0)),add(elbow,(-1,-3)),add(elbow,(4,-1)),add(elbow,(2,2))],WOOD_L,1.1)
    # Leafy cudgel/fingers: a deliberately compact, forward-pointing sprig.
    if far:
        d.oval(end,11,9,SHADE,INK,1.8,angle=b)
        leaf(d,add(end,v(b-55,8)),13,b-55,GREEN,INK)
        leaf(d,add(end,v(b+38,7)),12,b+38,MID,INK)
    else:
        def P(x,y):return add(end,rot((x*1.12,y*1.13),b))
        # Broad cluster with little pointed tips, not a featureless round glove.
        d.shape([P(-9,5),P(-14,-4),P(-9,-12),P(-1,-12),
                 P(2,-21),P(11,-19),P(13,-11),P(25,-12),P(27,-3),P(20,3),
                 P(24,10),P(17,16),P(7,12),P(1,17),P(-10,13),P(-9,5)],GREEN,INK,2.)
        d.shape([P(-7,1),P(-5,-8),P(5,-9),P(12,-8),P(19,-5),P(16,3),P(9,5),
                 P(5,10),P(-3,9),P(-7,1)],LIGHT,None)
        for off,ang in [((0,-5),-35),((12,5),35),((5,8),62)]:
            leaf(d,P(*off),10,b+ang,MID,None)
        # Gold coin and banknote grow out of the weapon, anchored by stems.
        sprig(d,P(3,-5),P(6,-15),'note',20,b-22)
        sprig(d,P(13,4),P(21,7),'coin',5,b+10)


# Overlapping clipped topiary scallops, with a nearly straight top and sides.
# The rim is one silhouette; internal leaf groupings do not have heavy outlines.
OUTLINE=[(-64,39),(-73,37),(-75,30),(-70,23),
         (-78,18),(-78,10),(-72,5),(-79,-2),(-78,-10),(-72,-16),
         (-79,-25),(-77,-35),(-70,-39),(-75,-48),(-70,-58),(-61,-58),
         (-57,-66),(-47,-67),(-42,-61),(-34,-69),(-26,-69),(-20,-63),
         (-12,-70),(-3,-69),(3,-64),(12,-70),(23,-70),(28,-64),
         (35,-70),(44,-69),(49,-63),(56,-67),(66,-64),(69,-57),
         (78,-56),(81,-46),(75,-40),(83,-32),(82,-22),(76,-16),
         (83,-9),(82,2),(76,6),(83,14),(80,24),(74,25),
         (79,36),(73,44),(64,41),(58,48),(47,48),(40,43),
         (30,50),(23,49),(15,44),(7,50),(-3,50),(-9,44),
         (-18,49),(-29,49),(-35,43),(-44,49),(-55,47),(-64,39)]

# Decorative, deterministic clusters. Locations deliberately leave the face
# readable, especially at quarter resolution.
CLUSTERS=[(-52,-31,22,18),(-33,-49,26,17),(-4,-52,25,16),(25,-50,24,18),(51,-38,18,21),
          (-56,-6,20,20),(-36,-16,24,19),(-9,-25,22,21),(20,-24,25,22),(52,-13,23,22),
          (-54,17,20,18),(-32,26,24,18),(-4,29,25,17),(22,25,26,20),(48,21,19,19)]
# (x,y,size,angle) leaf marks. A restrained graphic detail layer.
LEAVES=[(-50,-46,13,-30),(-33,-54,14,8),(-16,-51,11,-36),(3,-56,14,10),(24,-50,14,-24),
        (42,-52,13,12),(58,-39,13,57),(-59,-25,13,-70),(-39,-26,16,-35),(-20,-35,14,18),
        (-49,-6,13,36),(-59,9,11,-52),(-41,13,14,9),(-29,28,13,20),(-49,31,11,-35),
        (-8,35,15,6),(14,36,14,-35),(40,32,14,23),(58,19,14,-50),(59,-8,12,45),
        (36,-27,13,12),(13,-37,14,-43),(-5,-13,11,-10),(-16,5,11,24),(8,16,12,-25),
        (32,9,13,15),(44,39,9,-25),(-26,-1,10,35),(-61,-11,10,-12)]


def draw_hedge(d,q):
    P=lambda x,y:B(q,x,y)
    outline=[P(x,y) for x,y in OUTLINE]
    d.shape(outline,GREEN,INK,2.6)
    # Major light and shadow masses, clipped by construction to the hedge.
    d.shape([P(-59,0),P(-53,-6),P(-41,-14),P(-34,-9),P(-23,0),P(-24,11),P(-10,17),
             P(2,28),P(24,20),P(37,24),P(52,15),P(61,12),P(70,7),P(69,22),P(57,32),P(49,33),
             P(36,41),P(27,35),P(20,42),P(3,43),P(-12,43),P(-23,37),P(-39,40),P(-49,35),P(-48,27),
             P(-59,25),P(-62,13),P(-59,0)],SHADE,None)
    d.shape([P(-61,-31),P(-59,-42),P(-46,-42),P(-40,-50),P(-30,-61),P(-16,-56),P(-8,-56),
             P(3,-63),P(15,-64),P(21,-56),P(32,-60),P(44,-56),P(48,-51),
             P(61,-53),P(66,-39),P(64,-32),P(45,-26),P(28,-31),P(12,-32),
             P(0,-25),P(-18,-34),P(-27,-30),P(-38,-22),P(-54,-22),P(-61,-31)],MID,None)
    for j,(x,y,rx,ry) in enumerate(CLUSTERS):
        # Soft-edged scallops with a small directional cel-shaded crescent.
        c=P(x,y)
        col=(MID,GREEN,SHADE)[0 if y<-24 else (2 if y>16 else 1)]
        d.oval(c,rx*.82*q.sx,ry*.68*q.sy,col,None,angle=q.tilt)
        if j%3!=2:
            a=P(x-rx*.25,y-ry*.25)
            d.oval(a,rx*.46*q.sx,ry*.24*q.sy,LIGHT if y<-26 else MID,None,angle=q.tilt-12)
    for i,(x,y,size,ang) in enumerate(LEAVES):
        a=ang+q.tilt+q.shake*4*math.sin(i*1.9+q.phase)
        c=P(x,y)
        leaf(d,c,size*(.88 if y>20 else 1),a,(LIGHT,MID,LIME,GREEN)[i%4],None,i%3!=2)
    # Wood and financial leaves appear in silhouette, attached to the plant.
    sprig(d,P(-43,-42),P(-48,-62),'note',29,-31+q.tilt+3*math.sin(q.phase))
    sprig(d,P(-13,-52),P(-11,-70),'coin',9,q.tilt-12)
    sprig(d,P(16,-53),P(24,-69),'note',34,17+q.tilt+3*math.sin(q.phase+1.2))
    sprig(d,P(48,-40),P(55,-53),'coin',8,q.tilt+15)
    sprig(d,P(-48,1),P(-55,-9),'note',27,-19+q.tilt)
    sprig(d,P(-38,30),P(-47,26),'coin',8,q.tilt-12)
    sprig(d,P(31,35),P(40,29),'note',27,21+q.tilt)
    # Eyebrows on the same local coordinate system as glasses and pupils.
    # Large right-facing eyes read from the platformer's normal camera.
    mood=q.mood; anger=smooth((mood-.38)/.62)
    openness=max(.08,(1-q.blink*.96)*(1-.43*anger))
    for x,y,rx,ry in [(-5,-13,13,15),(23,-12,15,16)]:
        center=P(x,y)
        d.oval(center,rx*q.sx,ry*q.sy,DEEP,INK,1.4,angle=q.tilt)
        d.oval(center,(rx-2)*q.sx,(ry-2)*q.sy,GOLD,GOLD_D,1.0,angle=q.tilt)
        d.oval(center,(rx-4)*q.sx,(ry-4)*q.sy,DEEP,None,angle=q.tilt)
        if openness>.15:
            d.oval(center,(rx-4.7)*q.sx,(ry-4.5)*q.sy*openness,CREAM,None,angle=q.tilt)
            pp=P(x+3.5,y+.7+2*anger)
            d.oval(pp,3.3*q.sx,5.1*q.sy*openness,INK,None,angle=q.tilt)
            d.oval(P(x+4.5,y-1.4+2*anger),1.2,1.5,CREAM,None)
            if anger>.05:
                # The eyelid and brow angle down into the middle of the face.
                inner=1 if x<0 else -1
                d.line([P(x-inner*(rx-4),y-ry+5),P(x+inner*(rx-4),y-ry+5+9*anger)],DEEP,2.6)
        else:
            d.line([P(x-5,y),P(x+5,y)],GOLD_D,1.9)
        # Leafy brow comes down on the inner corner as the swipe approaches.
        d.curve([P(x-rx+1,y-ry-2+5*mood),P(x-5,y-ry-7),P(x+5,y-ry-7+6*mood),P(x+rx-1,y-ry-1+4*mood)],DEEP,4)
        d.curve([P(x-rx+3,y-ry-3+5*mood),P(x-5,y-ry-7),P(x+3,y-ry-6+5*mood),P(x+rx-3,y-ry-2+4*mood)],LIGHT,1.1)
    d.curve([P(8,-14),P(10,-19),P(12,-19),P(14,-14)],GOLD_D,2.1)
    d.line([P(-18,-12),P(-35,-18)],GOLD_D,2)
    d.line([P(37,-11),P(48,-16)],GOLD_D,2)
    # Slight crooked grin in a recess, not a face pasted on the plant.
    if q.dead>.45:
        d.oval(P(18,15),10,6,MOUTH,INK,1.4,angle=q.tilt)
    elif mood>.48:
        # Clenched, crooked mouth, with the corners drawn down for the attack.
        d.shape([P(-2,15),P(5,5),P(23,5),P(35,12),P(35,18),P(33,23),P(29,24),
                 P(20,18),P(9,19),P(2,24),P(-2,22),P(-4,17),P(-2,15)],MOUTH,INK,1.5)
        d.shape([P(2,15),P(8,9),P(23,9),P(31,14),P(28,17),P(13,15),P(6,18),
                 P(4,19),P(2,17),P(2,15)],CREAM,None)
        for x in (10,19,26):
            d.line([P(x,11),P(x,16)],GOLD_D,.85)
    else:
        gape=3+7*mood
        d.shape([P(-5,12),P(3,9),P(16,16),P(35,7-3*mood),P(36,12+gape),P(24,24+gape*.12),P(12,22),
                 P(4,21),P(-2,17),P(-5,12)],MOUTH,INK,1.6)
        d.shape([P(-1,12),P(8,12),P(20,15),P(32,9-2*mood),P(29,17),P(12,19),P(5,16),
                 P(2,15),P(0,13),P(-1,12)],CREAM,None)
        for x in (9,17,25):
            d.line([P(x,13),P(x,17)],GOLD_D,.85)
    d.curve([P(-6,27),P(1,31),P(12,32),P(18,29)],LIGHT,1.3)


def debris(d,q):
    # A few attached leaves fly free only on recoil/death. No floor shadow.
    if q.dead>.01:
        z=q.dead
        for j,(x,y) in enumerate([(-58,-35),(-17,-53),(53,-36),(64,5),(-48,21)]):
            start=B(q,x,y)
            side=-1 if j<2 else 1
            c=(start[0]+side*(12+3*j)*z,min(GROUND-(12 if j%2 else 9),start[1]-22*math.sin(math.pi*z)+88*z*z))
            if j%2:
                note(d,c,18,side*80*z+j*11)
            else:
                leaf(d,c,12,side*110*z+j*8,LIGHT,INK)
    elif q.shake>.5:
        z=q.shake
        for j,(x,y) in enumerate([(-50,-44),(56,-37),(-52,12)]):
            c=B(q,x+(-1 if j!=1 else 1)*8*z,y-10*z)
            leaf(d,c,9,30*j+45*z,MID,INK)


def _render_frame(anim,i,n):
    q=pose(anim,i,n);d=Canvas()
    draw_root(d,q,True)
    branch(d,q,True)
    draw_root(d,q,False)
    draw_hedge(d,q)
    branch(d,q,False)
    debris(d,q)
    return d.finish(q.fade)


def _body_metrics(fw,fh):
    # Branches, financial leaves and the attack envelope are not hurt geometry.
    # Feet anchor stays in the middle of the hedge instead of following the arm.
    from ...core.measure import body_metrics_for_box
    return body_metrics_for_box((65,66,219,220),fw,fh)


def render(out_dir: str | Path, **opts):
    from ...authoring.sheet_build import build_sheet
    outputs=build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
                        out_dir=Path(out_dir), frame_size=FRAME_SIZE,
                        auto_crop=False, actor_metadata=ACTOR_METADATA,
                        body_metrics_fn=_body_metrics,
                        animation_key_map={a:a for a,_,_ in ROWS}, sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
