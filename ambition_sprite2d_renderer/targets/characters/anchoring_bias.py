"""Anchoring Bias, an original Neural dimension heavy enemy.

A stubborn, one-eyed neural brute, riveted into a diving-weight harness,
hauls a massive iron anchor by its chain. A fixed sight stays trained on
its chosen point. The anchor is one articulated prop, not a succession of
independent drawings: its ring, chain links, grip and flukes share a pose.
The visual attack is a committed swing into a grounded follow-through.
Actual target fixation, damage, and physical item custody are game logic.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
import math
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet
from ...core.draw import resize_transparent_sprite
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'anchoring_bias'
FRAME_SIZE = (480, 368)
SUPER = 3
GROUND = 333.0
CHAIN_LENGTH = 84.0
ORIGIN = (220.0, 242.0)
# The load-bearing body, not the separate anchor, chain, limbs' extension,
# sparks, or the dendrites. This is fixed across animation frames.
BODY_BOX = (157, 106, 280, 334)
ROWS = [
    ('idle', 12, 85), ('walk', 16, 70), ('dash', 10, 65),
    ('notice', 8, 70), ('windup', 12, 70), ('attack_side', 18, 60),
    ('hit', 7, 65), ('death', 16, 80),
]
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Anchoring Bias'},
    'body': {'body_plan': 'Biped', 'body_kind': 'Standard', 'mass_class': 'Heavy',
             'locomotion_hint': 'Walk',
             'traits': ['neural', 'bioengineered', 'armored', 'anchor', 'heavy']},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'tags': ['enemy', 'neural', 'cognitive_bias'],
    'authoring_description': (
        'Original creature based on the cognitive bias of anchoring: initial '
        'information can exert undue influence on subsequent judgment. A '
        'heavy neural brute carries a literal iron anchor, with a fixed '
        'optical sight and a massive harness. Its exaggerated commitment '
        'to a chosen point is a proposed game mechanic, not a psychological '
        'or anatomical illustration. The renderer authors the visual motion '
        'only; the game owns targeting, damage, and the physical anchor.'
    ),
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
}

INK = '#211d2a'
FLESH_DEEP = '#542e43'
FLESH_DARK = '#854459'
FLESH = '#ba6877'
FLESH_LIGHT = '#df9590'
FLESH_HI = '#f5c1a5'
STEEL_DEEP = '#252c37'
STEEL_DARK = '#414c59'
STEEL = '#697e86'
STEEL_LIGHT = '#a0b4ae'
BRASS_DARK = '#76513b'
BRASS = '#b7884f'
BRASS_HI = '#e5be7d'
RUST = '#8c5146'
LEATHER = '#59403e'
CYAN = (80, 220, 225, 255)
CORE = (219, 255, 237, 255)
ORANGE = (247, 175, 91, 255)

def clamp(x):
    return max(0.0, min(1.0, x))


def smooth(x):
    x = clamp(x)
    return x*x*(3-2*x)


def mix(a, b, t):
    return a + (b-a)*t


def opacity(c, a):
    return (*c[:3], round(c[3]*clamp(a)))


def shade(c, f):
    if isinstance(c, str):
        c = tuple(int(c[j:j+2], 16) for j in (1, 3, 5))
    return tuple(round(max(0, min(255, k*f))) for k in c[:3]) + (255,)


def add(a, b):
    return (a[0]+b[0], a[1]+b[1])


def sub(a, b):
    return (a[0]-b[0], a[1]-b[1])


def mul(a, f):
    return (a[0]*f, a[1]*f)


def unit(v):
    return mul(v, 1/max(math.hypot(*v), .0001))


def cross(v):
    return (-v[1], v[0])


def lerp_point(a, b, t):
    return (mix(a[0], b[0], t), mix(a[1], b[1], t))


def spline(points, closed=False, steps=9):
    """Catmull-Rom interpolated authored contours."""
    points = list(points)
    p = [points[-1], *points, points[0], points[1]] if closed else [points[0], *points, points[-1]]
    out = []
    for a,b,c,d in zip(p,p[1:],p[2:],p[3:]):
        for i in range(steps):
            t = i/steps
            out.append(tuple(.5*(2*b[k]+(-a[k]+c[k])*t+(2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+
                                   (-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in (0,1)))
    return out+[points[0] if closed else points[-1]]


class Pen:
    def __init__(self, image, transform=lambda p:p):
        self.image = image
        self.transform = transform
        self.d = ImageDraw.Draw(image)

    def xy(self, p):
        return tuple(round(v*SUPER) for v in self.transform(p))

    def poly(self, points, fill, outline=None, width=1):
        pts = [self.xy(p) for p in points]
        self.d.polygon(pts, fill=fill)
        if outline:
            self.d.line(pts+pts[:1], fill=outline, width=max(1,round(width*SUPER)), joint='curve')

    def shape(self, points, fill, outline=None, width=1):
        self.poly(spline(points, True), fill, outline, width)

    def line(self, points, fill, width=1):
        self.d.line([self.xy(p) for p in points], fill=fill,
                    width=max(1,round(width*SUPER)), joint='curve')

    def curve(self, points, fill, width=1):
        self.line(spline(points), fill, width)

    def ellipse(self, p, r, fill, outline=None, width=1):
        x,y=p; rx,ry=r
        self.poly([(x+rx*math.cos(i*math.tau/48),y+ry*math.sin(i*math.tau/48)) for i in range(48)], fill, outline, width)

    def disk(self, p, r, fill, outline=None, width=1):
        self.ellipse(p, (r,r), fill, outline, width)

    def local(self, origin, axis=(1,0)):
        norm=cross(axis)
        return Pen(self.image, lambda p:self.transform(add(origin,add(mul(axis,p[0]),mul(norm,p[1])))))

    def tube(self, knots, radii, fill, outline=INK, width=1.5, highlight=None):
        """A tapered curved organ, from a centreline and local radii."""
        path=spline(knots,False,8)
        left=[]; right=[]
        for i,p in enumerate(path):
            t=i/max(1,len(path)-1)*(len(radii)-1)
            j=min(int(t),len(radii)-2)
            r=mix(radii[j],radii[j+1],t-j)
            n=cross(unit(sub(path[min(i+1,len(path)-1)],path[max(0,i-1)])))
            left.append(add(p,mul(n,r)))
            right.append(sub(p,mul(n,r)))
        self.poly(left+right[::-1],fill,outline,width)
        if highlight:
            self.curve([lerp_point(p,q,.57) for p,q in zip(path,left)][::4]+[path[-1]],highlight,max(.7,width*.8))



@dataclass(frozen=True)
class Pose:
    x: float = 0
    y: float = 0
    lean: float = .04
    front: float = 26
    back: float = -30
    front_lift: float = 0
    back_lift: float = 0
    grip_x: float = -54
    grip_y: float = -26
    brace_x: float = 55
    brace_y: float = -22
    ring_x: float = 111
    ring_y: float = 240
    anchor_angle: float = -1.30
    grounded: float = 1
    eye: float = 1
    charge: float = .22
    breath: float = 0
    phase: float = 0
    tension: float = 0
    impact: float = 0
    dust: float = 0
    collapse: float = 0
    fade: float = 1


def blend(a, b, t):
    t = smooth(t)
    return Pose(**{f.name:mix(getattr(a,f.name),getattr(b,f.name),t) for f in fields(Pose)})


def keys(t, values):
    for (ta,a),(tb,b) in zip(values,values[1:]):
        if t<=tb:
            return blend(a,b,(t-ta)/(tb-ta))
    return values[-1][1]


# Poses for the committed attack. Windup ends exactly where the attack starts.
REST = Pose()
LOCK = Pose(x=-3,y=-4,lean=-.04,front=30,back=-33,grip_x=-60,grip_y=-35,
            brace_x=63,brace_y=-44,ring_x=111,anchor_angle=-1.30,eye=1,charge=.85,tension=.4)
CROUCH = Pose(x=-12,y=12,lean=-.14,front=35,back=-39,grip_x=-64,grip_y=-28,
              brace_x=53,brace_y=-38,ring_x=104,anchor_angle=-1.12,charge=.96,tension=.8)
COCK = Pose(x=-10,y=2,lean=-.13,front=34,back=-40,grip_x=-48,grip_y=-65,
            brace_x=52,brace_y=-50,ring_x=132,ring_y=104,anchor_angle=.18,grounded=0,
            charge=1,tension=1)
HIGH = Pose(x=2,y=-8,lean=.05,front=40,back=-31,grip_x=0,grip_y=-86,
            brace_x=58,brace_y=-59,ring_x=292,ring_y=125,anchor_angle=1.06,grounded=0,
            charge=1,tension=1)
SWEEP = Pose(x=15,y=-1,lean=.28,front=46,back=-27,grip_x=40,grip_y=-55,
             brace_x=66,brace_y=-33,ring_x=356,ring_y=195,anchor_angle=2.96,grounded=0,
             charge=.95,tension=1)
SLAM = Pose(x=16,y=14,lean=.31,front=47,back=-29,grip_x=38,grip_y=-25,
            brace_x=65,brace_y=0,ring_x=363,ring_y=240,anchor_angle=4.0,grounded=1,
            charge=.9,tension=1,impact=1,dust=1)
DRAG = Pose(x=4,y=6,lean=.10,front=40,back=-24,grip_x=24,grip_y=-19,
            brace_x=43,brace_y=-14,ring_x=327,anchor_angle=4.15,grounded=1,
            charge=.35,tension=.8,dust=.2)
PULL = Pose(x=-5,y=4,lean=-.13,front=28,back=-34,grip_x=-10,grip_y=-16,
            brace_x=38,brace_y=-24,ring_x=280,anchor_angle=4.32,grounded=1,
            charge=.3,tension=.65)
# This return sweeps the object around the outside rather than teleporting it.
RETURN_HIGH = Pose(x=-3,y=2,lean=-.08,front=26,back=-30,grip_x=-10,grip_y=-75,
                   brace_x=45,brace_y=-44,ring_x=166,ring_y=106,anchor_angle=5.9,
                   grounded=0,charge=.3,tension=.6)
RETURN = Pose(ring_x=111,anchor_angle=math.tau-1.30)


def gait(t, dash=False):
    # A stance foot moves back relative to the root and the swing foot
    # returns forward on a raised arc. No translation of the sheet origin.
    stride = 48 if dash else 32
    lift = 21 if dash else 13
    def foot(u):
        u %= 1
        if u<.61:
            return mix(stride,-stride,u/.61),0
        v=(u-.61)/.39
        return mix(-stride,stride,smooth(v)),lift*math.sin(math.pi*v)
    a,al=foot(t); b,bl=foot(t+.5)
    c=math.tau*t
    return Pose(x=2*math.sin(c),y=2*math.cos(2*c),lean=.22 if dash else .10,
                front=a+12,back=b-13,front_lift=al,back_lift=bl,
                grip_x=-57,grip_y=-24+2*math.sin(c),brace_x=53+10*math.sin(c),
                brace_y=-20-7*math.sin(c),ring_x=107-4*math.sin(c),
                anchor_angle=-1.05 if dash else -1.28,charge=.58 if dash else .28,
                breath=math.sin(c),phase=c,tension=.85 if dash else .62,
                dust=.45 if dash else .16)


def pose_for(anim,i,n):
    t=i/(n if anim in ('idle','walk','dash') else max(1,n-1))
    c=math.tau*t
    if anim=='idle':
        return Pose(y=1.8*math.sin(c),breath=math.sin(c),phase=c,
                    grip_y=-26+1.3*math.sin(c),eye=.1 if i in (8,) else 1,
                    charge=.24+.08*math.cos(c),anchor_angle=-1.30)
    if anim in ('walk','dash'):
        return gait(t,anim=='dash')
    if anim=='notice':
        p=blend(REST,LOCK,t)
    elif anim=='windup':
        p=keys(t,[(0,LOCK),(.55,CROUCH),(1,COCK)])
    elif anim=='attack_side':
        p=keys(t,[(0,COCK),(.18,HIGH),(.32,SWEEP),(.43,SLAM),(.53,SLAM),
                  (.69,DRAG),(.80,PULL),(.90,RETURN_HIGH),(1,RETURN)])
    elif anim=='hit':
        recoil=Pose(x=-13,y=5,lean=-.24,grip_x=-63,grip_y=-25,brace_x=39,brace_y=-43,
                    eye=.06,charge=.85,impact=.32,ring_x=111,tension=.8)
        p=keys(t,[(0,REST),(.32,recoil),(1,REST)])
    elif anim=='death':
        stagger=Pose(x=-8,y=9,lean=-.17,grip_x=-64,grip_y=-8,brace_x=38,brace_y=-11,
                     eye=.3,charge=.9,ring_x=111,tension=.7)
        kneel=Pose(x=5,y=32,lean=.37,front=36,back=-36,grip_x=-58,grip_y=-3,
                   brace_x=48,brace_y=10,ring_x=111,eye=.1,charge=.34,collapse=.55,dust=.6)
        fallen=Pose(x=13,y=40,lean=.72,front=40,back=-37,grip_x=-70,grip_y=5,
                    brace_x=34,brace_y=4,ring_x=111,eye=0,charge=0,collapse=1,dust=0)
        p=keys(t,[(0,REST),(.25,stagger),(.58,kneel),(1,fallen)])
    else:
        raise ValueError(anim)
    return Pose(**{**p.__dict__,'phase':c,'breath':.35*math.sin(c)})


def body_transform(pose):
    a=pose.lean; c=math.cos(a); s=math.sin(a)
    return lambda p:(ORIGIN[0]+pose.x+p[0]*c-p[1]*s,ORIGIN[1]+pose.y+p[0]*s+p[1]*c)


def joint(a,b,l1,l2,bend):
    """Two-link IK, clamping unreachable targets rather than stretching limbs."""
    v=sub(b,a); d=math.hypot(*v); u=unit(v)
    d=max(abs(l1-l2)+.1,min(l1+l2-.1,d))
    end=add(a,mul(u,d)); x=(l1*l1+d*d-l2*l2)/(2*d)
    h=math.sqrt(max(0,l1*l1-x*x))
    return add(add(a,mul(u,x)),mul(cross(u),bend*h)),end


def rivet(p,pt,r=2.7):
    p.disk(pt,r,BRASS_DARK,INK,.8)
    p.disk(add(pt,(-.5,-.6)),r*.67,BRASS_HI)
    p.line([add(pt,(-r*.4,.7)),add(pt,(r*.5,.7))],BRASS_DARK,.65)


def plate(p,outline,edge,fill=STEEL):
    p.shape(outline,STEEL_DEEP,INK,2.3)
    p.shape([lerp_point(q,edge,.12) for q in outline],fill,STEEL_DARK,1.2)
    p.curve(outline[:max(3,len(outline)//2)],STEEL_LIGHT,1.6)


def draw_dendrites(p,pose):
    # Sparse, thick nerve roots: the figure is a neural brute, not a diver.
    branches=[([(-42,-104),(-68,-118),(-81,-142),(-80,-158)], [(-81,-142),(-98,-148),(-105,-159)]),
              ([(-23,-126),(-35,-148),(-28,-170),(-36,-180)], [(-28,-170),(-10,-179),(-3,-190)]),
              ([(8,-131),(15,-153),(32,-167),(31,-183)], [(32,-167),(51,-165),(62,-179)]),
              ([(-53,-75),(-76,-81),(-94,-96),(-112,-95)], [(-94,-96),(-102,-115),(-115,-123)])]
    for j,(main,branch) in enumerate(branches):
        root=main[0]
        def move(q):
            k=math.hypot(*sub(q,root))/75
            return (q[0]+k*(3*math.sin(pose.phase+j)-7*pose.tension),q[1]+k*(3*math.cos(pose.phase+j)+15*pose.collapse))
        a=[move(q) for q in main]; b=[move(q) for q in branch]
        p.tube(b,[3.2,2,1.2],FLESH_DARK,INK,1.4,FLESH_LIGHT)
        p.tube(a,[8,5,3,1.6],FLESH,INK,1.7,FLESH_LIGHT)
        for q in (a[-1],b[-1]):
            p.disk(q,2.4,FLESH_LIGHT,FLESH_DEEP,.9)
            if pose.charge>.45:p.disk(q,1.3,opacity(CYAN,pose.charge))


def draw_leg(p,hip,knee,ankle,near,collapse):
    dark=FLESH_DEEP if not near else FLESH_DARK
    # Thick sinewy thigh and a braced shin. Highlights follow the joint axis.
    a=p.local(hip,unit(sub(knee,hip)))
    L=math.hypot(*sub(knee,hip))
    a.shape([(-7,-12),(L*.24,-20),(L*.7,-17),(L+4,-11),(L+5,11),(L*.55,17),(0,15)],dark,INK,2.4)
    for off in (-9,-3,4,10):
        a.curve([(2,off*.7),(L*.42,off*1.2),(L-4,off*.6)],FLESH_LIGHT if near else FLESH,1.6)
    a=p.local(knee,unit(sub(ankle,knee))); L=math.hypot(*sub(ankle,knee))
    a.shape([(-4,-13),(L*.35,-17),(L+5,-10),(L+4,10),(L*.45,16),(-4,11)],STEEL_DARK,INK,2.4)
    a.shape([(5,-9),(L*.5,-12),(L-5,-6),(L-4,6),(L*.43,9)],STEEL if near else STEEL_DARK,INK,1.3)
    a.line([(7,-7),(L-6,-5)],STEEL_LIGHT,1.8)
    a.line([(12,5),(L-8,5)],STEEL_DEEP,3.2)
    p.disk(knee,15 if near else 12,STEEL_DARK,INK,2.4)
    p.disk(knee,10 if near else 8,STEEL,INK,1.5)
    rivet(p,knee,5 if near else 4)
    ax,ay=ankle
    # Flat-soled, lead-weight boots. No baked root translation.
    boot=[(ax-18,ay-7),(ax-6,ay-13),(ax+9,ay-9),(ax+24,ay-2),(ax+28,ay+8),(ax+27,ay+14),(ax-18,ay+14),(ax-22,ay+7)]
    p.poly(boot,STEEL if near else STEEL_DARK,INK,2.4)
    p.poly([(ax-17,ay+5),(ax+25,ay+5),(ax+27,ay+13),(ax-18,ay+13)],STEEL_DEEP,INK,1)
    p.line([(ax-13,ay-5),(ax+4,ay-7),(ax+18,ay)],STEEL_LIGHT,2)
    for x in (-11,0,12):p.line([(ax+x,ay+8),(ax+x,ay+13)],STEEL,1.5)


def draw_arm(p,shoulder,elbow,hand,near,charge):
    color=FLESH if near else FLESH_DARK
    a=p.local(shoulder,unit(sub(elbow,shoulder))); L=math.hypot(*sub(elbow,shoulder))
    a.shape([(-8,-15),(L*.35,-19),(L+5,-12),(L+5,11),(L*.45,18),(-7,13)],color,INK,2.3)
    for j in (-8,0,8):a.curve([(1,j*.7),(L*.45,j*1.15),(L-4,j*.65)],FLESH_LIGHT if near else FLESH,1.5)
    p.disk(elbow,11,STEEL_DARK,INK,2)
    a=p.local(elbow,unit(sub(hand,elbow))); L=math.hypot(*sub(hand,elbow))
    a.shape([(-4,-13),(L*.35,-16),(L-1,-12),(L+3,11),(L*.2,14)],STEEL_DARK,INK,2.1)
    a.shape([(4,-10),(L*.43,-12),(L-4,-9),(L-2,6),(L*.32,9)],STEEL if near else STEEL_DARK,INK,1.1)
    a.line([(5,-8),(L-6,-7)],STEEL_LIGHT,1.9)
    for x in (8,L-5):rivet(a,(x,7),2.3)
    # Broad wrist cuff, the hand itself drawn over the chain at its endpoint.
    a.poly([(L-9,-14),(L+1,-14),(L+4,13),(L-8,13)],BRASS_DARK,INK,1.5)
    a.line([(L-6,-12),(L-5,11)],BRASS_HI,1.6)


def draw_fist(p,hand,direction,grip=True):
    a=p.local(hand,unit(direction))
    a.shape([(-10,-10),(0,-14),(13,-11),(16,-4),(13,9),(3,13),(-11,8)],FLESH_DARK,INK,2.2)
    for j in range(3):
        y=-8+j*7
        a.shape([(0,y-3),(9,y-3.5),(13,y),(9,y+3),(1,y+2.8)],FLESH_LIGHT,INK,1)
    a.shape([(-7,-9),(2,-12),(7,-9),(5,-3),(-4,1)],FLESH,INK,1.3)
    a.line([(-6,-7),(0,-9),(3,-8)],FLESH_HI,1.2)


def draw_body(p,pose):
    # Torso, taut bands of tissue and heavy diver-like weight harness.
    p.shape([(-52,-64),(-39,-92),(-8,-101),(30,-91),(53,-61),(54,-22),(36,9),(-4,18),(-44,5),(-60,-27)],FLESH_DEEP,INK,3)
    p.shape([(-48,-66),(-24,-88),(14,-86),(41,-65),(43,-31),(25,-3),(-14,8),(-41,-8),(-52,-34)],FLESH,INK,1.7)
    for j in range(5):
        y=-72+j*11
        p.curve([(-42,y),(-19,y+6),(2,y+3),(24,y-1)],FLESH_DARK,3)
        p.curve([(-37,y-2),(-18,y+3),(0,y)],FLESH_LIGHT,1.7)
    # Lower plate apron and broad leather belts.
    p.shape([(-45,-16),(-24,-21),(13,-17),(41,-28),(49,0),(33,21),(-10,24),(-43,12)],STEEL_DARK,INK,2.5)
    p.poly([(-42,-25),(-4,-16),(39,-25),(41,-10),(-4,0),(-44,-10)],LEATHER,INK,2)
    p.line([(-39,-22),(-5,-12),(37,-21)],BRASS,1.5)
    p.poly([(-13,-18),(10,-18),(13,-3),(-10,0)],BRASS,INK,2)
    p.poly([(-7,-13),(5,-13),(7,-6),(-5,-4)],STEEL_DEEP,INK,1)
    for x in (-34,29):rivet(p,(x,-13),3)
    # Two wide chest straps and a bronze bearing plate with a lock mark.
    for x in (-26,22):
        p.poly([(x-7,-83),(x+6,-86),(x+13,-22),(x-1,-18)],LEATHER,INK,1.8)
        p.line([(x-4,-81),(x+1,-53),(x+4,-24)],BRASS,1.5)
    p.disk((6,-48),24,STEEL_DEEP,INK,2.5)
    p.disk((6,-48),20,BRASS_DARK,INK,1.5)
    p.disk((6,-48),16,STEEL_DARK,INK,1.4)
    for k in range(12):
        a=k*math.tau/12; u=(math.cos(a),math.sin(a)); p.line([add((6,-48),mul(u,12)),add((6,-48),mul(u,15))],BRASS_HI,1)
    p.poly([(-4,-39),(6,-61),(16,-39),(6,-44)],BRASS_HI,INK,1.2)
    p.disk((6,-48),3.2,STEEL_DEEP,BRASS,1)
    for q in [(-26,-27),(35,-40),(-31,-73),(28,-74)]:rivet(p,q,3)


def draw_shoulder(p,center,near):
    q=p.local(center)
    plate(q,[(-27,-7),(-18,-24),(3,-29),(23,-20),(31,-3),(21,14),(-7,18),(-23,11)],(0,-2),STEEL if near else STEEL_DARK)
    q.shape([(-20,-9),(-7,-20),(7,-21),(23,-13),(24,-5),(9,-9),(-6,-8)],STEEL_LIGHT if near else STEEL,STEEL_DARK,1.2)
    q.curve([(-18,5),(1,9),(22,2)],BRASS,2)
    for a in [(-17,2),(16,-13),(19,6)]:rivet(q,a,3)
    q.line([(-5,-15),(0,-5),(-3,0)],STEEL_DARK,1.5)


def draw_head(p,pose):
    # The folded cortex emerges from a corroded iron head collar.
    cy=-108+pose.breath*1.0
    q=p.local((2,cy))
    contour=[(-54,2),(-59,-13),(-49,-33),(-28,-46),(-10,-43),(6,-49),(31,-40),(43,-24),(50,-8),(46,9),(32,20),(9,25),(-21,21),(-44,17)]
    q.shape(contour,FLESH_DARK,INK,2.8)
    # Sculpted cortical lobes overlap; each groove has a lip and a shadow.
    lobes=[([(-50,-13),(-45,-30),(-27,-37),(-17,-29),(-25,-14),(-38,-7)],FLESH_LIGHT),
           ([(-29,-31),(-14,-41),(4,-40),(11,-28),(1,-17),(-14,-17)],FLESH),
           ([(6,-38),(22,-40),(34,-30),(32,-17),(17,-13),(9,-21)],FLESH_LIGHT),
           ([(-52,-10),(-39,-19),(-22,-11),(-23,3),(-35,12),(-50,6)],FLESH),
           ([(-25,-12),(-9,-21),(4,-11),(1,5),(-13,14),(-24,4)],FLESH_LIGHT),
           ([(-19,11),(-4,3),(12,9),(18,19),(3,22),(-15,21)],FLESH)]
    for outline,col in lobes:
        q.shape(outline,col,FLESH_DEEP,1.8)
        q.curve(outline[:4],FLESH_HI,1.8)
    for j in range(8):
        x=-44+j*9; y=-9+8*math.sin(j*1.6)
        q.curve([(x-3,y-6),(x-4,y),(x+1,y+3),(x+4,y+1)],FLESH_DARK,1.25)
    # Iron band covers the right eye region: a literal fixed sight.
    q.shape([(4,-31),(30,-35),(47,-23),(59,-5),(55,13),(38,25),(9,20),(-1,5)],STEEL_DEEP,INK,2.8)
    q.shape([(7,-29),(30,-30),(46,-19),(54,-6),(50,11),(34,18),(10,16),(2,5)],STEEL,STEEL_DARK,1.6)
    q.curve([(8,-25),(29,-26),(43,-16),(49,-7)],STEEL_LIGHT,2.7)
    # One unmistakably directional eye in a heavy bronze socket.
    q.ellipse((27,-2),(23,17),BRASS_DARK,INK,2.2)
    q.ellipse((27,-2),(19,13),STEEL_DEEP,BRASS_HI,1.5)
    h=10*max(.07,pose.eye)
    eye=[(11,-4),(17,-10*pose.eye),(36,-8*pose.eye),(44,-2),(36,h),(20,h-1)]
    q.shape(eye,'#193843',INK,1.2)
    if pose.eye>.15:
        q.ellipse((33,-1),(7.2,7.7*pose.eye),CYAN,STEEL_DEEP,1)
        q.ellipse((35,-1),(3.4,4.2*pose.eye),CORE)
        q.line([(33,-8*pose.eye),(33,6*pose.eye)],'#176877',.8)
        q.line([(26,-1),(39,-1)],'#176877',.8)
        q.disk((36,-4*pose.eye),1.4,CORE)
    # Inward-pointing iron brow and jaw reinforce stubborn expression.
    q.poly([(8,-18),(27,-20),(49,-14),(44,-9),(22,-14),(7,-11)],STEEL_DARK,INK,1.5)
    q.line([(11,-17),(27,-18),(45,-13)],STEEL_LIGHT,1.3)
    q.shape([(-14,15),(12,17),(32,16),(45,12),(48,25),(28,34),(4,31),(-17,24)],STEEL_DARK,INK,2)
    q.curve([(-11,19),(5,23),(27,24),(43,19)],STEEL_LIGHT,1.7)
    for j in range(4):
        x=7+j*8; q.line([(x,24),(x+1,29)],STEEL_DEEP,2.5)
    for v in [(11,-24),(43,-20),(46,12),(0,6)]:rivet(q,v,2.8)
    # Neural probes, thick ceramic necks and exposed contacts.
    for (x,y) in [(-40,-36),(-8,-43)]:
        q.poly([(x-6,y+4),(x-7,y-7),(x+4,y-9),(x+7,y+2)],STEEL_DARK,INK,1.5)
        q.ellipse((x-1,y-7),(6,3.2),BRASS_HI,INK,1)
        q.disk((x-1,y-8),2.2,CYAN)


# Iron anchor in its own coordinate frame. Local +x runs from crown to ring.
# Both palms and flukes are drawn, including the stock, throat and shank.
ANCHOR_OUTLINE=[(-10,-5),(-2,-19),(13,-32),(27,-43),(43,-44),(37,-51),(59,-43),
                (48,-23),(43,-30),(30,-28),(17,-16),(15,-6),(68,-6),(68,-20),
                (76,-20),(76,-6),(86,-6),(89,-10),(99,-11),(107,-5),(107,5),(99,11),(89,10),
                (86,6),(76,6),(76,20),(68,20),(68,6),(15,6),(17,16),(30,28),(43,30),
                (48,23),(59,43),(37,51),(43,44),(27,43),(13,32),(-2,19),(-10,5)]
RING=(97,0)


def anchor_transform(pose, grip=None):
    a=pose.anchor_angle; axis=(math.cos(a),math.sin(a)); normal=cross(axis)
    def delta(q):return add(mul(axis,q[0]-RING[0]),mul(normal,q[1]))
    bottom=max(delta(q)[1] for q in ANCHOR_OUTLINE)+1.4
    y=min(mix(pose.ring_y,GROUND-bottom,pose.grounded),GROUND-bottom)
    ring=(pose.ring_x,y)
    if grip is not None and math.dist(grip,ring)>CHAIN_LENGTH:
        # On the floor, slide the prop instead of stretching the chain.
        # Airborne: constrain the ring along the authored swing direction.
        if pose.grounded>.999 and abs(y-grip[1])<CHAIN_LENGTH:
            reach=math.sqrt(CHAIN_LENGTH**2-(y-grip[1])**2)
            ring=(max(grip[0]-reach,min(grip[0]+reach,ring[0])),y)
        else:
            ring=add(grip,mul(unit(sub(ring,grip)),CHAIN_LENGTH))
            if ring[1]>GROUND-bottom:
                y=GROUND-bottom
                reach=math.sqrt(max(0,CHAIN_LENGTH**2-(y-grip[1])**2))
                ring=(max(grip[0]-reach,min(grip[0]+reach,ring[0])),y)
    return ring,lambda q:add(ring,delta(q))


def draw_anchor(p,transform):
    a=Pen(p.image,transform)
    a.poly(ANCHOR_OUTLINE,STEEL_DEEP,INK,3)
    # Faceted forged iron, raised bevels and rusty bronze wear on edges.
    for side in (-1,1):
        def f(points):return [(x,y*side) for x,y in points]
        a.poly(f([(-5,1),(2,17),(17,30),(29,40),(48,43),(51,41),(45,33),(29,34),(13,20),(8,3)]),STEEL_DARK,INK,1.3)
        a.poly(f([(1,8),(7,20),(19,32),(31,38),(46,39),(39,35),(27,31),(13,18)]),STEEL,STEEL_DEEP,.9)
        a.poly(f([(38,43),(49,45),(42,49),(56,42),(48,27),(45,34),(31,32)]),STEEL,INK,1.5)
        a.line(f([(3,14),(18,28),(31,36),(47,39)]),STEEL_LIGHT,2.1)
        a.line(f([(41,44),(53,42),(48,30)]),BRASS,1.8)
        a.curve(f([(11,15),(20,21),(22,25),(34,28)]),RUST,1.2)
    a.poly([(11,-4),(85,-4),(86,4),(11,4)],STEEL,STEEL_DARK,1.1)
    a.line([(16,-3),(85,-3)],STEEL_LIGHT,2)
    a.line([(16,3),(85,3)],RUST,1.2)
    a.poly([(66,-22),(76,-22),(79,-16),(79,16),(76,22),(66,22),(63,16),(63,-16)],STEEL_DARK,INK,2)
    a.poly([(66,-19),(71,-19),(74,17),(67,19)],STEEL,STEEL_DEEP,1)
    a.line([(67,-17),(69,17)],STEEL_LIGHT,1.6)
    for x in (27,53,72):
        a.line([(x,-4),(x+2,4)],STEEL_DARK,1.2)
    # Hollow eye: render the opening transparent on the anchor layer.
    a.disk(RING,12,STEEL_DARK,INK,2.5)
    a.disk(RING,9,STEEL,STEEL_DEEP,1)
    a.disk(RING,5.2,(0,0,0,0),INK,1.2)
    a.curve([(91,-7),(95,-9),(101,-8),(104,-4)],STEEL_LIGHT,1.5)
    for q in [(3,0),(71,-16),(71,16)]:rivet(a,q,2.8)
    # Small chips and corrosion are deterministic authored detail.
    rng=random.Random(312)
    for _ in range(14):
        x=rng.uniform(20,61); y=rng.uniform(-2,2)
        a.line([(x,y),(x+rng.uniform(.5,2),y-.7)],BRASS_DARK,.7)


def chain_points(a,b,count=12):
    """Equal arc-length positions on a sagging chain, with fixed endpoints.

    Approximate gravity sag is visual, not a second physical simulation.
    Slack is chosen to keep the chain near its nominal length when possible.
    """
    distance=math.hypot(*sub(a,b)); length=max(CHAIN_LENGTH,distance)
    def path(sag):
        return [(mix(a[0],b[0],i/60),mix(a[1],b[1],i/60)+sag*math.sin(math.pi*i/60)) for i in range(61)]
    def arc(pts):return sum(math.hypot(*sub(y,x)) for x,y in zip(pts,pts[1:]))
    lo,hi=0,55
    for _ in range(12):
        mid=(lo+hi)/2
        if arc(path(mid))<length:lo=mid
        else:hi=mid
    pts=path((lo+hi)/2); cum=[0.0]
    for x,y in zip(pts,pts[1:]):cum.append(cum[-1]+math.hypot(*sub(y,x)))
    out=[]; j=1
    for k in range(count+1):
        t=cum[-1]*k/count
        while j<len(cum)-1 and cum[j]<t:j+=1
        out.append(lerp_point(pts[j-1],pts[j],(t-cum[j-1])/max(.0001,cum[j]-cum[j-1])))
    return out


def draw_chain(p,a,b):
    points=chain_points(a,b)
    # The links alternate edge-on and face-on and overlap at their ends.
    for i,(a,b) in enumerate(zip(points,points[1:])):
        m=lerp_point(a,b,.5); u=unit(sub(b,a)); q=p.local(m,u)
        r=math.hypot(*sub(b,a))*.69; h=3.8 if i%2==0 else 2.3
        ring=[(r*math.cos(j*math.tau/24),h*math.sin(j*math.tau/24)) for j in range(25)]
        q.line(ring,INK,4.2)
        q.line(ring,STEEL,2.7)
        q.line(ring[:13],STEEL_DARK,1.6)
        q.line(ring[12:23],STEEL_LIGHT,1.4)


def draw_fx(img,pose,atr):
    size=img.size; sparks=Image.new('RGBA',size); glow=Image.new('RGBA',size)
    p=Pen(sparks); g=Pen(glow)
    # A locked sight has a restrained glow; the iron does not become magic.
    eye=body_transform(pose)((35,-109)); strength=pose.charge*pose.eye
    g.ellipse(eye,(11,8),opacity(CYAN,.24*strength))
    if pose.charge>.6:
        t=body_transform(pose); rng=random.Random(86)
        for j,(a,b) in enumerate([((-43,-151),(-30,-165)),((-11,-155),(8,-169)),((28,-147),(47,-153))]):
            a,b=t(a),t(b); u=unit(sub(b,a)); points=[a]
            for k in range(1,6):points.append(add(lerp_point(a,b,k/6),mul(cross(u),rng.uniform(-3,3)+2*math.sin(pose.phase+j+k))))
            points.append(b); alpha=(pose.charge-.6)/.4
            g.line(points,opacity(CYAN,.4*alpha),5); p.line(points,opacity(CORE,.85*alpha),1.4)
    if pose.dust>.02:
        contact=max((atr(q) for q in ANCHOR_OUTLINE),key=lambda v:v[1]); k=pose.dust
        for j in range(7):
            dx=(-1 if j%2 else 1)*(7+j*3)*k; y=GROUND-3-((j*7)%11)*k
            p.ellipse((contact[0]+dx,y),(2+j*.45,1+j*.25),(157,132,109,round(100*k)))
    if pose.impact>.04:
        contact=max((atr(q) for q in ANCHOR_OUTLINE),key=lambda v:v[1]); k=pose.impact
        for j in range(9):
            a=-math.pi*(.08+.84*j/8); d=(8+17*k)*(1 if j%2 else .75)
            start=add(contact,(5*math.cos(a),5*math.sin(a)-1)); end=add(start,(d*math.cos(a),d*math.sin(a)))
            p.line([start,end],opacity(ORANGE,.86*k),1.7); g.disk(end,2.6,opacity(ORANGE,.48*k))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(2.3*SUPER)))
    img.alpha_composite(sparks)


def render_frame(anim,i,n):
    pose=pose_for(anim,i,n)
    size=tuple(v*SUPER for v in FRAME_SIZE); img=Image.new('RGBA',size)
    tr=body_transform(pose); world=Pen(img); body=Pen(img,tr)
    draw_dendrites(body,pose)
    # Far leg, far arm and bracing hand are under the torso.
    far_hip=tr((-25,4)); near_hip=tr((24,6))
    fa=(ORIGIN[0]+pose.back,GROUND-14-pose.back_lift); na=(ORIGIN[0]+pose.front,GROUND-14-pose.front_lift)
    fk,fa=joint(far_hip,fa,49,50,-1); nk,na=joint(near_hip,na,49,50,-1)
    draw_leg(world,far_hip,fk,fa,False,pose.collapse)
    far_sh=tr((30,-69)); brace=tr((pose.brace_x,pose.brace_y)); fe,brace=joint(far_sh,brace,38,40,-1)
    draw_arm(world,far_sh,fe,brace,False,pose.charge); draw_fist(world,brace,sub(brace,fe),False)
    draw_body(body,pose)
    draw_leg(world,near_hip,nk,na,True,pose.collapse)
    draw_head(body,pose)
    # The anchor remains on a distinct transparent layer, with a hollow ring.
    # Grip is IK-limited; the chain starts at the actual end of the arm.
    near_sh=tr((-28,-69)); grip=tr((pose.grip_x,pose.grip_y)); ne,grip=joint(near_sh,grip,42,45,1)
    anchor=Image.new('RGBA',size); ring,atr=anchor_transform(pose,grip); draw_anchor(Pen(anchor),atr)
    # The chain passes behind the foreground gauntlet, but in front of the torso.
    img.alpha_composite(anchor)
    draw_chain(world,grip,ring)
    draw_arm(world,near_sh,ne,grip,True,pose.charge)
    draw_shoulder(body,(-27,-65),True)
    draw_fist(world,grip,sub(ring,grip))
    draw_fx(img,pose,atr)
    if pose.fade<1:img.putalpha(img.getchannel('A').point(lambda v:round(v*pose.fade)))
    return resize_transparent_sprite(img,FRAME_SIZE)


def _body_metrics(fw,fh):
    return body_metrics_for_box(BODY_BOX,fw,fh)


def render(out_dir: str | Path, **opts):
    del opts
    Path(out_dir).mkdir(parents=True,exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=render_frame,
                        out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,
                        actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,
                        pose_bodies='authored',animation_key_map={name:name for name,_,_ in ROWS})
    return [Path(outputs[key]) for key in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent') if outputs.get(key)]


TARGETS={TARGET_NAME:{'render':render,'actor_metadata':ACTOR_METADATA}}
