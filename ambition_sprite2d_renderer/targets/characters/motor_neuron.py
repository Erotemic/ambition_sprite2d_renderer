"""Motor Neuron -- an original Neural dimension bio-mechanical runner.

The soma of a multipolar neuron is fused to an exposed electric motor. A
myelinated axon feeds the stator; the rotor transmits motion through paired
cranks to muscular, piston-braced legs. Its dendrites are branching organs,
not loose decorative wires. The two legs are posed with a two-link solver;
feet have explicit stance and swing phases. All anatomy is authored here.

The windup, ram and sparks are visual proposals for an enemy action; the
actual locomotion, damage and knockback remain the game's responsibility.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, replace
import math
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet
from ...core.draw import resize_transparent_sprite
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'motor_neuron'
FRAME_SIZE = (384, 344)
SUPER = 3
GROUND = 299
ORIGIN = (164, 213)
# The central mass and weight-bearing legs, not the dendrite crown, sparks,
# forward-reaching toes, or the trailing cable. Stable for every frame.
BODY_BOX = (108, 93, 228, GROUND + 1)
ROWS = [
    ('idle', 10, 90), ('walk', 12, 75), ('dash', 10, 54),
    ('notice', 6, 75), ('windup', 10, 60), ('attack_side', 12, 50),
    ('hit', 6, 50), ('death', 14, 75),
]
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Motor Neuron'},
    'body': {'body_plan': 'Biped', 'body_kind': 'Standard', 'mass_class': 'Heavy',
             'locomotion_hint': 'Walk',
             'traits': ['neural', 'bioengineered', 'mechanical', 'electric', 'runner']},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'tags': ['enemy', 'neural'],
    'authoring_description': (
        'An original Neural dimension monster based on the motor neuron pun. '
        'A multipolar nerve cell with branching dendrites and a myelinated axon '
        'is fused to a copper-wound electric motor, reduction gearing, and '
        'muscular mechanical legs. The exposed rotor, eye, and mechanical '
        'locomotion are fictional; not an anatomical illustration. A heavy '
        'ground pursuer that visibly winds up before a charge.'
    ),
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
}

INK = '#281d30'
DEEP = '#4b2b43'
FLESH_DARK = '#75435c'
FLESH = '#b66f80'
FLESH_LIGHT = '#e4a09e'
FLESH_HI = '#f7c2ad'
MUSCLE = '#ae4e63'
MUSCLE_HI = '#e18b85'
MUSCLE_DARK = '#662e49'
IVORY = '#e5d4b4'
IVORY_DARK = '#96878c'
STEEL_DEEP = '#263444'
STEEL_DARK = '#405367'
STEEL = '#748a99'
STEEL_LIGHT = '#b6c9c9'
COPPER_DARK = '#754331'
COPPER = '#c17b48'
COPPER_HI = '#efb66d'
CYAN = (65, 210, 241, 255)
CORE = (216, 255, 250, 255)
ORANGE = (255, 153, 72, 255)


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
    x: float=0
    y: float=0
    lean: float=.09
    front_x: float=17
    front_lift: float=0
    back_x: float=-18
    back_lift: float=0
    front_toe: float=0
    back_toe: float=0
    flex: float=0
    eye: float=.65
    blink: float=0
    charge: float=.24
    rotor: float=0
    branch: float=0
    branch_sweep: float=0
    heat: float=0
    strike: float=0
    damage: float=0
    collapse: float=0
    fade: float=1


def blend(a,b,t):
    t=smooth(t)
    return Pose(**{f.name:mix(getattr(a,f.name),getattr(b,f.name),t) for f in fields(Pose)})


def keyframes(t, keys):
    for (a,p),(b,q) in zip(keys,keys[1:]):
        if t <= b:
            return blend(p,q,(t-a)/(b-a))
    return keys[-1][1]


def gait(t, stride, lift, stance):
    """A single foot relative to the translating body; no root movement.

    During stance the toe moves linearly backwards. During swing it clears
    the ground, returns forwards, then plants again. The near and far feet
    have the same loop at half-cycle offsets.
    """
    t %= 1
    if t<stance:
        u=t/stance
        return (stride*(.5-u),0,0)
    u=(t-stance)/(1-stance)
    return (stride*(smooth(u)-.5),lift*math.sin(math.pi*u)**1.25,
            .28*math.sin(math.tau*u))


REST=Pose()
NOTICE=replace(REST,y=-3,lean=-.04,eye=1,charge=.48,branch_sweep=-.3)
COILED=replace(REST,y=15,lean=.28,front_x=33,back_x=-38,flex=.7,eye=1,
               charge=1,heat=.82,branch_sweep=-.85)
THRUST=replace(REST,x=5,y=5,lean=.49,front_x=44,back_x=-33,back_lift=17,
               back_toe=.25,flex=1,eye=1,charge=1,heat=1,branch_sweep=-1.1,strike=1)


def pose_for(anim,i,n):
    loop=anim in ('idle','walk','dash','windup')
    t=i/(n if loop else max(1,n-1)); a=t*math.tau
    if anim=='idle':
        return replace(REST,y=1.4*math.cos(a),flex=.18+.13*math.sin(a),
                       blink=math.exp(-((t-.65)/.075)**2),charge=.24+.06*math.sin(a),
                       rotor=a,branch=a)
    if anim in ('walk','dash'):
        fast=anim=='dash'; stride=74 if fast else 49
        f=gait(t,stride,27 if fast else 14,.54 if fast else .63)
        b=gait(t+.5,stride,27 if fast else 14,.54 if fast else .63)
        return replace(REST,y=(4 if fast else 2.5)*math.cos(a*2)+ (6 if fast else 0),
                       lean=.40 if fast else .16,front_x=f[0],front_lift=f[1],front_toe=f[2],
                       back_x=b[0],back_lift=b[1],back_toe=b[2],flex=.55 if fast else .25,
                       charge=.83 if fast else .42,heat=.75 if fast else .15,
                       rotor=a*(3 if fast else 2),branch=a,branch_sweep=-.95 if fast else -.35)
    if anim=='notice':
        p=keyframes(t,[(0,REST),(.40,NOTICE),(1,NOTICE)])
        return replace(p,rotor=t*math.tau,branch=a)
    if anim=='windup':
        # A sustained, repeatable charged pose: no reset to idle if the tell loops.
        return replace(COILED,y=COILED.y+1.6*math.sin(a),flex=.75+.15*math.cos(a),
                       charge=.9+.1*math.sin(a),heat=.8+.12*math.cos(a),rotor=a*3,branch=a)
    if anim=='attack_side':
        recovery=replace(REST,x=1,y=3,lean=.22,front_x=25,back_x=-22,charge=.58,heat=.7,branch_sweep=-.25)
        p=keyframes(t,[(0,COILED),(.17,THRUST),(.42,replace(THRUST,x=9,front_x=37,back_lift=13,strike=.85)),
                       (.63,recovery),(1,REST)])
        return replace(p,rotor=t*math.tau*4,branch=a)
    if anim=='hit':
        p=keyframes(t,[(0,REST),(.25,replace(REST,x=-6,y=6,lean=-.24,eye=.1,blink=.9,
                    flex=.8,charge=.9,damage=1,branch_sweep=.8)),(.60,replace(REST,lean=-.10,damage=.35)),(1,REST)])
        return replace(p,rotor=t*math.tau,branch=a)
    if anim=='death':
        p=keyframes(t,[(0,REST),(.16,replace(REST,lean=-.18,y=8,charge=1,heat=1,damage=1,eye=.2,branch_sweep=.75)),
                    (.48,replace(REST,y=22,lean=.46,front_x=48,back_x=-34,charge=.5,heat=.8,
                                 eye=.08,blink=.55,collapse=.35,branch_sweep=-.65)),
                    (.78,replace(REST,y=27,lean=.95,front_x=65,back_x=-40,charge=.1,heat=.35,
                                 eye=0,blink=1,collapse=.9,branch_sweep=-.9)),
                    (1,replace(REST,y=28,lean=1.04,front_x=65,back_x=-40,charge=0,heat=.1,
                               eye=0,blink=1,collapse=1,branch_sweep=-1,fade=.12))])
        return replace(p,rotor=math.tau*2*(1-(1-t)**3),branch=a)
    raise ValueError(anim)


def local_transform(pose):
    c,s=math.cos(pose.lean),math.sin(pose.lean)
    def tr(p):
        x,y=p
        return ORIGIN[0]+pose.x+x*c-y*s,ORIGIN[1]+pose.y+x*s+y*c
    return tr


# ------------ Neural anatomy ------------
# Each dendrite has authored branch knots and radii. Motion is correlated with
# distance from its root, so the organ stays attached while the tips flex.
DENDRITES = [
    ([(-48,-84),(-69,-94),(-86,-112),(-112,-121)], [8,6,3.4,1.2],
     [(1,[(-77,-128),(-92,-143)],[2.6,1]),(2,[(-99,-96),(-119,-96)],[2.6,1]),(2,[(-90,-132),(-111,-145)],[1.9,.7])]),
    ([(-29,-111),(-39,-136),(-60,-156),(-65,-176)], [7,5,2.8,1.1],
     [(1,[(-16,-148),(-9,-169)],[2.8,.9]),(2,[(-84,-154),(-97,-162)],[2.1,.8]),(1,[(-50,-142),(-70,-139)],[2.0,.8])]),
    ([(7,-117),(9,-144),(24,-158),(26,-178)], [6.5,4.5,2.7,1],
     [(1,[(45,-149),(59,-158)],[2.4,.9]),(2,[(6,-173),(-6,-182)],[2,.8]),(1,[(-8,-150),(-15,-158)],[2,.8])]),
    ([(-48,-62),(-78,-63),(-99,-46),(-125,-44)], [7,5,3,1],
     [(1,[(-100,-77),(-119,-80)],[2.7,.9]),(2,[(-100,-26),(-119,-17)],[2.1,.8]),(1,[(-83,-42),(-88,-27)],[2.1,.7])]),
    ([(38,-107),(55,-126),(80,-130),(94,-146)], [5.5,4,2.5,1],
     [(1,[(54,-150),(68,-162)],[2.1,.8]),(2,[(92,-117),(105,-118)],[1.9,.8])]),
]


def dendrite_motion(p, root, phase, sweep, collapse, index):
    d=math.hypot(*sub(p,root)); w=min(1,d/65)
    return (p[0]+w*(sweep*13+2.1*math.sin(phase+index+d*.045)),
            p[1]+w*(3.5*math.cos(phase+index*.8+d*.03)+12*collapse))


def draw_dendrites(p, g, pose):
    for j,(main,radii,forks) in enumerate(DENDRITES):
        move=lambda pt:dendrite_motion(pt,main[0],pose.branch,pose.branch_sweep,pose.collapse,j)
        # Forks under main trunk, giving clean junctions rather than floating roots.
        for idx,pts,r in forks:
            path=[move(v) for v in [main[idx],*pts]]
            p.tube(path,[r[0]+.6,*r],FLESH_DARK,INK,1.2,FLESH_LIGHT)
            p.disk(path[-1],1.7,FLESH_LIGHT,INK,.8)
        path=[move(v) for v in main]
        p.tube(path,radii,FLESH,INK,1.6,FLESH_LIGHT)
        tip=path[-1]
        p.disk(tip,2.2,FLESH_LIGHT,INK,1)
        if pose.charge>.25:
            g.disk(tip,4.5,opacity(CYAN,pose.charge*.6))
            p.disk(tip,1.1,opacity(CORE,pose.charge))
        # Organic membrane filaments inside the trunk.
        p.curve([lerp_point(v,root,.15) for v,root in zip(path,main)],FLESH_DARK,.9)
        for idx,pt in enumerate(path[1:-1]):
            p.disk(pt,1.25,FLESH_LIGHT)


def draw_soma(p,g,pose):
    # A large asymmetrical nerve-cell soma, rather than another folded brain.
    # Upper rear nucleus and forward ocular organ are separated by membrane ridges.
    outline=[(-63,-81),(-55,-103),(-32,-119),(-9,-122),(14,-117),(37,-111),
             (55,-99),(62,-84),(59,-70),(65,-57),(51,-47),(32,-49),(17,-40),
             (4,-39),(-9,-48),(-27,-47),(-44,-52),(-61,-61)]
    p.shape(outline,FLESH_DARK,INK,2.4)
    p.shape([(-58,-83),(-50,-104),(-28,-115),(-5,-117),(18,-110),(40,-104),
             (53,-91),(55,-78),(45,-70),(35,-72),(21,-63),(0,-59),(-17,-64),
             (-38,-58),(-55,-68)],FLESH,INK,1.2)
    p.shape([(-54,-91),(-41,-106),(-20,-112),(-3,-111),(10,-105),(-12,-101),
             (-28,-93),(-43,-82),(-56,-79)],FLESH_LIGHT)
    p.shape([(-45,-101),(-32,-109),(-15,-110),(-23,-105),(-40,-98)],FLESH_HI)
    # Lower folds have depth, but are cell membrane and organelles, not cortex.
    p.shape([(-54,-67),(-37,-71),(-24,-60),(-7,-58),(11,-52),(5,-43),(-15,-49),(-34,-49)],DEEP)
    p.curve([(-57,-76),(-43,-77),(-29,-68),(-17,-67),(-5,-59)],FLESH_LIGHT,2.1)
    p.curve([(2,-112),(8,-101),(4,-91),(-6,-85)],FLESH_DARK,1.9)
    p.curve([(19,-107),(27,-98),(42,-96),(50,-88)],FLESH_HI,1.8)
    # Nucleus: translucent-looking membrane with an internal nucleolus.
    p.ellipse((-21,-88),(21,20),DEEP,INK,1.7)
    p.ellipse((-22,-90),(18.5,17), '#9a667f',FLESH_LIGHT,1.4)
    p.ellipse((-25,-93),(13.8,12.5),'#c18d9b')
    p.ellipse((-19,-87),(8.6,8.1),'#80526e',DEEP,1.1)
    p.ellipse((-21,-89),(3.6,3.3),'#e0b4b6')
    p.curve([(-35,-88),(-33,-97),(-26,-102),(-18,-102)],FLESH_HI,1.8)
    for x,y,rx,ry in [(-47,-87,2.8,1.3),(-43,-70,2,1.5),(-10,-65,3,1.4),
                      (2,-70,2,1.5),(11,-94,3,1.3),(-4,-107,2,1.1),(23,-55,2,1.3)]:
        p.ellipse((x,y),(rx,ry),FLESH_DARK)
        p.curve([(x-rx*.6,y-.5),(x,y-.8),(x+rx*.6,y-.4)],FLESH_LIGHT,.8)
    # Fine membrane filaments follow the shape instead of changing every frame.
    for pts in [[(-51,-96),(-43,-95),(-40,-91)], [(-46,-60),(-38,-55),(-31,-57)],
                [(-1,-74),(7,-78),(10,-86)],[(15,-103),(19,-98),(24,-98)],
                [(36,-57),(27,-55),(23,-51)]]:
        p.curve(pts,FLESH_DARK,1.15)
        p.disk(pts[-1],1.15,FLESH_LIGHT)
    # Visible implanted sensory organ and brow. The bright pupil reads in a tiny sprite.
    eye_open=max(.06,(1-pose.blink)*(.6+.4*pose.eye))
    p.shape([(12,-87),(26,-99),(43,-96),(55,-86),(58,-75),(45,-65),(25,-68),(14,-75)],DEEP,INK,1.6)
    p.shape([(18,-83),(30,-91),(45,-87),(52,-81),(46,-79+10*eye_open),
             (32,-79+13*eye_open),(22,-77+6*eye_open)],STEEL_DEEP,INK,1.1)
    if pose.eye>.05 and pose.blink<.94:
        p.ellipse((39,-81+4*eye_open),(7.6,7*eye_open), '#288c9b',INK,.9)
        p.ellipse((41,-81+4*eye_open),(3.5,5.5*eye_open),shade(CORE,.55+.45*pose.eye))
        g.ellipse((41,-81+4*eye_open),(10,8),opacity(CYAN,.42*pose.eye))
        p.disk((42,-84+4*eye_open),1.8,'#ffffff')
    p.curve([(15,-86),(30,-91),(43,-88),(54,-83)],FLESH_LIGHT,3.2)
    p.curve([(20,-70),(32,-64),(45,-65),(55,-70)],FLESH,2.4)
    # Front serrated sensory plate, inset into the fleshy head.
    p.shape([(47,-52),(60,-60),(68,-56),(65,-48),(56,-44),(44,-43),(39,-47)],STEEL_DARK,INK,1.8)
    p.line([(49,-51),(60,-53),(64,-51)],STEEL_LIGHT,1.6)
    for x,y in ((49,-47),(55,-47),(61,-49)):
        p.disk((x,y),1.5,STEEL_DEEP)
    # A pair of metallic electrode clamps, each with bolted feet and ceramic cap.
    for pos,angle in [((-42,-112),-.44),((29,-113),.32)]:
        ep=p.local(pos,(math.cos(angle),math.sin(angle)))
        ep.shape([(-7,1),(-5,-7),(5,-7),(8,0),(6,5),(-6,5)],STEEL,INK,1.6)
        ep.ellipse((0,-6),(5.2,2.7),IVORY,INK,1)
        ep.line([(-4,-3),(4,-3)],STEEL_LIGHT,1.2)
        ep.disk((0,-7),1.8,opacity(CORE,.75))
    # Cell membrane routes into the axon; fine veins converge on the axon hillock.
    p.curve([(-31,-53),(-20,-46),(-13,-45),(-7,-37)],FLESH_HI,1.6)
    p.curve([(27,-53),(15,-46),(9,-42),(4,-37)],FLESH_LIGHT,1.6)


def draw_axon(p,g,pose):
    # The soma's output process runs around the *outside* of the gearbox,
    # visibly feeding a terminal on the stator. Nodes between myelin sleeves
    # glow in succession during the windup.
    path=spline([(-24,-51),(-39,-48),(-55,-39),(-63,-24),(-57,-9),(-44,-5)],False,9)
    p.tube([(-24,-51),(-39,-48),(-55,-39),(-63,-24),(-57,-9),(-44,-5)],
           [6.4,6,5.5,5,4.5,3.5],FLESH_DARK,INK,1.7,FLESH_HI)
    for j,t in enumerate((.22,.40,.59,.77)):
        k=round(t*(len(path)-1)); v=path[k]
        axis=unit(sub(path[k+1],path[k-1])); q=p.local(v,axis)
        q.shape([(-5,-5),(-4,-7),(3,-7),(5,-4),(5,4),(3,7),(-4,7),(-5,4)],IVORY_DARK,INK,1.3)
        q.shape([(-4,-4),(-3,-6),(3,-6),(4,-3),(3,3),(-3,4),(-4,1)],IVORY)
        q.line([(-3,-5),(3,-5)],FLESH_HI,1.1)
    for j,t in enumerate((.31,.50,.69,.87)):
        k=round(t*(len(path)-1)); v=path[k]
        strength=pose.charge*(.25+.75*max(0,math.cos(pose.branch*2-j*1.5))**3)
        p.disk(v,2.4,shade(FLESH_HI, .8+.2*strength))
        if strength>.18:
            g.disk(v,4,opacity(CYAN,strength*.7))
    terminal=path[-1]
    p.disk(terminal,5.5,STEEL_DARK,INK,1.4)
    p.disk(terminal,3.3,COPPER_HI,INK,.9)
    p.disk(terminal,1.5,CORE if pose.charge>.5 else STEEL_LIGHT)


# ------------ Motor assembly ------------

def draw_motor(p,g,pose):
    # Structural backplate and integrated gearbox. Different silhouettes from
    # the soft soma, so the biological/mechanical joke reads without text.
    p.shape([(-48,-38),(-43,-50),(-26,-55),(-2,-50),(13,-47),(33,-39),
             (45,-19),(45,0),(35,17),(14,23),(-17,23),(-39,12),(-48,-5)],STEEL_DEEP,INK,2.4)
    p.shape([(-43,-36),(-31,-48),(-8,-46),(18,-42),(36,-25),(39,-9),(29,10),
             (11,16),(-13,18),(-35,7),(-44,-10)],STEEL_DARK,INK,1.2)
    p.shape([(-44,-32),(-35,-43),(-20,-47),(-6,-43),(-26,-38),(-37,-29),(-42,-16)],STEEL_LIGHT)
    # Rear cooling fins, individually shaped and welded to the main housing.
    for j in range(5):
        y=-34+j*7.5
        p.poly([(-43,y),(-55,y+1),(-55,y+5),(-46,y+5),(-39,y+2)],STEEL_DARK,INK,1.2)
        p.line([(-53,y+1),(-43,y+1)],STEEL_LIGHT,1.2)
    # Copper stator, clearly stationary. Rotor and drive eccentric turn inside.
    center=(0,-15); rx,ry=32,29
    p.ellipse(center,(rx+5,ry+5),STEEL_DEEP,INK,2)
    p.ellipse(center,(rx+1,ry+1),STEEL,INK,1.5)
    p.ellipse(center,(rx-3,ry-3),COPPER_DARK,INK,1.5)
    for k in range(12):
        a=k*math.tau/12
        def rad(r, da=0):
            return (center[0]+r*math.cos(a+da),center[1]+r*.89*math.sin(a+da))
        pts=[rad(19,-.23),rad(27,-.23),rad(29,-.11),rad(29,.11),rad(27,.23),rad(19,.23)]
        p.poly(pts,COPPER,INK,1.2)
        for d in (-.12,.015,.14):
            p.line([rad(21,d),rad(27.8,d)],COPPER_HI,.95)
    p.ellipse(center,(20,18.6),STEEL_DEEP,INK,1.7)
    p.ellipse(center,(17.4,16),STEEL_DARK,STEEL_LIGHT,1.2)
    # Radial cooling blades on the spinning rotor; no motion of the stator.
    for k in range(5):
        a=pose.rotor+math.tau*k/5
        def v(r,b):return (r*math.cos(a+b),center[1]+r*.9*math.sin(a+b))
        p.shape([v(5,-.4),v(15,-.37),v(16,.18),v(11,.42),v(5,.35)],STEEL,INK,1.0)
        p.line([v(6,-.32),v(14,-.29)],STEEL_LIGHT,1.3)
        if k==0:
            p.line([v(10,.18),v(14,.17)],COPPER_HI,1.7)
    p.ellipse(center,(7.5,6.7),STEEL_LIGHT,INK,1.5)
    p.ellipse(center,(4,3.6),STEEL_DEEP,INK,1)
    pin=(8.5*math.cos(pose.rotor),center[1]+8*math.sin(pose.rotor))
    p.disk(pin,2.8,COPPER_HI,INK,1)
    for a in (.45,1.95,3.52,5.15):
        v=(36*math.cos(a),center[1]+32*math.sin(a))
        p.disk(v,2.8,STEEL_LIGHT,INK,1)
        p.line([(v[0]-1.2,v[1]),(v[0]+1.2,v[1])],STEEL_DEEP,.9)
    # Bright winding surfaces pulse with the current during a charge.
    if pose.charge>.45:
        for j in range(6):
            a=j*math.tau/6
            v=(25*math.cos(a),center[1]+22*math.sin(a))
            strength=(pose.charge-.45)/.55*(.4+.6*math.cos(pose.branch*2+j)**2)
            g.ellipse(v,(5,4),opacity(ORANGE,.48*strength))
    # Heat and current indicator in the housing, not a giant overlay on the art.
    p.shape([(31,-34),(40,-29),(44,-21),(41,-16),(34,-20)],STEEL_DEEP,INK,1)
    for j in range(3):
        v=(35+j*2.2,-28+j*3.2)
        col=opacity(ORANGE if pose.heat>.6 else CYAN,.45+.55*pose.charge)
        p.line([(v[0]-1,v[1]),(v[0]+2,v[1]+1)],col,1.6)
        g.disk(v,3,opacity(ORANGE if pose.heat>.6 else CYAN,.30*pose.charge))
    # Heavy front bumper and motor mount, leg pins attach at the lower sides.
    p.shape([(22,-2),(42,-6),(50,1),(47,10),(33,18),(16,17),(14,9)],STEEL_DARK,INK,2)
    p.line([(22,2),(39,0),(46,3)],STEEL_LIGHT,2)
    for x,y in [(25,9),(41,5)]:p.disk((x,y),2.2,COPPER,INK,1)


# ------------ Locomotion anatomy ------------

def leg_joints(hip,ankle):
    """Two-link knee, forward-bending. Limit extension to anatomical reach."""
    a,b=49.0,48.0
    v=sub(ankle,hip); d=math.hypot(*v); u=unit(v)
    d_eff=max(abs(a-b)+.1,min(a+b-.2,d))
    ankle=add(hip,mul(u,d_eff))
    along=(a*a-b*b+d_eff*d_eff)/(2*d_eff)
    height=math.sqrt(max(0,a*a-along*along))
    knee=add(hip,add(mul(u,along),mul(cross(u),-height)))
    return knee,ankle


def shaft(p,a,b,width,base,hi):
    p.tube([a,lerp_point(a,b,.5),b],[width*.5,width*.5,width*.5],base,INK,1.5,hi)


def draw_leg(p,hip,knee,ankle,toe,near,flex):
    """Muscle bundles around a real articulated load-bearing linkage."""
    factor=1 if near else .72
    col=lambda c:shade(c,factor)
    # Thigh, bulging muscle on a longitudinal armature.
    q=p.local(hip,unit(sub(knee,hip)))
    L=math.hypot(*sub(knee,hip))
    q.shape([(-7,-7),(1,-15),(14,-19),(29,-14),(L-6,-7),(L+4,1),
             (L-5,11),(25,15),(9,13),(-5,7)],col(MUSCLE_DARK),INK,2)
    q.shape([(-3,-7),(8,-14),(20,-15),(35,-9),(L-6,-5),(L-5,2),
             (23,9),(9,9),(0,4)],col(MUSCLE),INK,1)
    for y in (-10,-5,0,5):
        q.curve([(4,y*.64),(13,y-1),(23,y*.85+2),(L-6,y*.29)],col(MUSCLE_HI),1.6 if near else 1.2)
    q.shape([(0,6),(9,9),(21,10),(33,5),(L-2,1),(L+2,7),(33,13),(14,14),(1,11)],col(STEEL_DARK),INK,1.3)
    q.curve([(7,11),(19,11),(33,8),(L-1,5)],col(STEEL_LIGHT),1.5)
    # Hip socket overlaps the crank, keeping the moving leg rooted.
    p.disk(hip,10.8,col(STEEL_DARK),INK,2)
    p.disk(hip,7.6,col(STEEL),INK,1.3)
    p.disk(hip,3.5,col(COPPER_HI),INK,1)
    # Lower leg: tendon, split piston, and a ribbed muscle belly behind shin.
    v=unit(sub(ankle,knee)); r=p.local(knee,v); L2=math.hypot(*sub(ankle,knee))
    r.shape([(0,-8),(10,-12),(22,-10),(33,-5),(L2-2,-3),(L2+3,4),
             (L2-5,9),(30,11),(13,13),(1,7)],col(MUSCLE_DARK),INK,1.9)
    r.shape([(2,2),(12,5),(21,7),(31,5),(L2-5,3),(L2-5,7),(27,10),(12,10),(3,7)],col(MUSCLE))
    r.curve([(6,6),(16,8),(28,8),(L2-4,5)],col(MUSCLE_HI),1.5)
    r.shape([(0,-9),(8,-10),(15,-7),(15,1),(9,4),(1,3)],col(STEEL),INK,1.5)
    r.poly([(13,-6),(L2-10,-6),(L2-6,-2),(L2-10,2),(13,2)],col(STEEL_LIGHT),INK,1.2)
    r.shape([(L2-21,-8),(L2-9,-8),(L2-4,-4),(L2-4,4),(L2-9,7),(L2-21,6)],col(STEEL_DARK),INK,1.5)
    for k in range(3):r.line([(L2-19+k*4,-6),(L2-19+k*4,4)],col(STEEL),1.2)
    # External cable joins both pivots and flexes at the joint.
    c1=add(knee,mul(cross(v),10)); c2=add(ankle,mul(cross(v),7))
    p.tube([c1,add(lerp_point(c1,c2,.4),mul(cross(v),5+flex*3)),c2],[2.8,2.5,2],col(DEEP),INK,1.0,col(FLESH_LIGHT))
    # Armored knee cap and shaft pin.
    p.disk(knee,12,col(STEEL_DEEP),INK,2)
    p.disk(knee,9.3,col(STEEL),INK,1.2)
    p.shape([add(knee,(-7,-4)),add(knee,(-3,-9)),add(knee,(5,-8)),add(knee,(8,-2)),add(knee,(2,0))],col(STEEL_LIGHT))
    p.disk(knee,4.1,col(COPPER),INK,1.2)
    p.disk(knee,1.8,col(STEEL_DEEP))
    p.disk(ankle,7.0,col(STEEL_DARK),INK,1.4)
    p.disk(ankle,3.5,col(STEEL_LIGHT),INK,1)
    # Grounded foot. Toe pivot affects swing only; stance always stays flat.
    s=p.local(ankle,(math.cos(toe),math.sin(toe)))
    s.shape([(-9,-7),(4,-7),(12,-1),(22,2),(31,6),(32,11),(27,13),
             (-13,13),(-18,9),(-14,3)],col(STEEL_DEEP),INK,2)
    s.shape([(-12,3),(-8,-5),(4,-5),(12,1),(22,4),(27,8),(20,10),(-12,9)],col(STEEL_DARK),INK,1.2)
    s.poly([(-10,-3),(3,-3),(9,2),(-12,4)],col(STEEL_LIGHT))
    s.line([(-13,11),(28,11)],col(STEEL),1.5)
    for x in (-9,0,9,18):s.line([(x,10),(x+2,13)],col(INK),1.3)
    s.line([(22,5),(27,7)],col(COPPER_HI),2)


def draw_linkage(p,pose,hip,tr):
    # The eccentric link actually connects to the visible hip joint.
    pin=tr((8.5*math.cos(pose.rotor),-15+8*math.sin(pose.rotor)))
    anchor=add(hip,(0,-2))
    shaft(p,pin,anchor,6.5,STEEL_DARK,STEEL_LIGHT)
    p.disk(pin,4.4,COPPER,INK,1.3)
    p.disk(pin,1.8,STEEL_LIGHT)


# ------------ Electrical accents ------------

def bolt(p,g,a,b,seed,phase,strength,width=1.5):
    if strength<.025:return
    rng=random.Random(seed)
    axis=unit(sub(b,a)); perp=cross(axis)
    pts=[a]
    for j in range(1,7):
        t=j/7
        v=lerp_point(a,b,t)
        v=add(v,mul(perp,rng.uniform(-1,1)*4.5*math.sin(math.pi*t)+1.7*math.sin(phase+j)))
        pts.append(v)
    pts.append(b)
    g.line(pts,opacity(CYAN,.6*strength),width*3.4)
    p.line(pts,opacity(CYAN,strength),width)
    p.line(pts,opacity(CORE,.92*strength),width*.48)


def render_frame(anim,i,n):
    pose=pose_for(anim,i,n)
    size=tuple(v*SUPER for v in FRAME_SIZE)
    img=Image.new('RGBA',size)
    g_back=Image.new('RGBA',size)
    tr=local_transform(pose)
    p=Pen(img,tr); gb=Pen(g_back,tr)
    # The branches and the far leg go behind the central body.
    draw_dendrites(p,gb,pose)
    world=Pen(img)
    near_hip=tr((14,10)); far_hip=tr((-18,10))
    # At rest and during walking the soles plant on GROUND. The motor/chassis
    # may shift visually, but root movement is never baked into the sheet.
    fa=(ORIGIN[0]+pose.back_x-9,GROUND-14-pose.back_lift)
    na=(ORIGIN[0]+pose.front_x,GROUND-14-pose.front_lift)
    fk,fa=leg_joints(far_hip,fa); nk,na=leg_joints(near_hip,na)
    draw_leg(world,far_hip,fk,fa,pose.back_toe,False,pose.flex)
    draw_motor(p,gb,pose)
    draw_soma(p,gb,pose)
    draw_axon(p,gb,pose)
    draw_leg(world,near_hip,nk,na,pose.front_toe,True,pose.flex)
    draw_linkage(world,pose,near_hip,tr)
    img.alpha_composite(g_back.filter(ImageFilter.GaussianBlur(2.3*SUPER)))
    # Selective electrical activity: stable seeded topology, slowly changing
    # amplitude, and a brighter short release around the bumper during a ram.
    front=Image.new('RGBA',size); glow=Image.new('RGBA',size)
    fp,gp=Pen(front,tr),Pen(glow,tr)
    phase=pose.branch
    for j,(a,b) in enumerate([((-43,-119),(-55,-132)),((30,-120),(43,-137)),((-51,-63),(-76,-72)),
                             ((-15,-39),(-30,-28)),((29,-15),(45,-4))]):
        strength=pose.charge*(.25+.65*math.sin(phase+j*1.3)**2)
        bolt(fp,gp,a,b,90+j,phase,strength,1.3)
    if pose.charge>.5:
        # These discharges follow the actual moving dendrite tips.
        tips=[dendrite_motion(main[-1],main[0],pose.branch,pose.branch_sweep,pose.collapse,j)
              for j,(main,_,_) in enumerate(DENDRITES)]
        for j,k in [(0,1),(1,2),(2,4)]:
            a,b=tips[j],tips[k]
            strength=(pose.charge-.5)*(.55+.45*math.sin(phase+j)**2)
            bolt(fp,gp,a,b,620+j,phase,strength,1.3)
    if pose.heat>.42:
        for j in range(4):
            t=(phase/math.tau+j*.25)%1
            x=-49-15*t; y=-32-13*t+j*3
            gp.ellipse((x,y),(3+3*t,2+2*t),opacity(ORANGE,pose.heat*(1-t)*.28))
            fp.disk((x,y),1.2,opacity(ORANGE,pose.heat*(1-t)))
    if pose.strike>.02:
        k=pose.strike
        bolt(fp,gp,(49,1),(75+17*k,-3),373,phase,k,2.2)
        bolt(fp,gp,(41,-8),(77+12*k,-20),391,phase,k*.85,1.8)
        bolt(fp,gp,(40,10),(70+9*k,19),400,phase,k*.7,1.4)
        gp.ellipse((46,0),(10*k,10*k),opacity(CYAN,.65*k))
        for j in range(5):
            a=math.pi*(j-2)/7; q=(57+23*k*math.cos(a),22*k*math.sin(a))
            fp.line([q,add(q,(6*math.cos(a),6*math.sin(a)))],opacity(CORE,.8*k),1.4)
    if pose.damage>.02:
        bolt(fp,gp,(-50,-95),(51,-54),512,phase,pose.damage,2)
        bolt(fp,gp,(-38,-30),(41,1),614,phase,pose.damage,.95)
    if pose.collapse>.1:
        # Motor sparks dwindle as the heavy assembly settles; no spawned parts.
        for j in range(5):
            k=pose.charge*(1-.15*j)
            q=(26+9*j,2+5*j)
            fp.line([q,add(q,(5,6))],opacity(ORANGE,k),1.4)
            gp.disk(q,3,opacity(ORANGE,k*.4))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(2.1*SUPER)))
    img.alpha_composite(front)
    if pose.fade<1:
        img.putalpha(img.getchannel('A').point(lambda v:round(v*pose.fade)))
    return resize_transparent_sprite(img,FRAME_SIZE)


def _body_metrics(fw,fh):
    return body_metrics_for_box(BODY_BOX,fw,fh)


def render(out_dir: str | Path, **opts):
    # Fixed authoring frame; publication chooses runtime scale/packing.
    del opts
    Path(out_dir).mkdir(parents=True,exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=render_frame,
                        out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,
                        actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,
                        pose_bodies='authored',animation_key_map={name:name for name,_,_ in ROWS})
    return [Path(outputs[key]) for key in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent') if outputs.get(key)]


TARGETS={TARGET_NAME:{'render':render,'actor_metadata':ACTOR_METADATA}}
