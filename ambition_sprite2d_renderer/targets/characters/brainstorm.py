"""Brainstorm -- an exposed, bioengineered cortex inside a thunderhead.

A right-facing floating monster. The cortex, cerebellum, stem, eyes, hardware,
nerve processes, cloud banks and lightning are separate procedural parts. The
same anatomy is deformed by every pose; the cortex does not regenerate its
folds every frame. All art is drawn here, without external raster assets.

The electrical attack is visual authoring, not a new gameplay ability. The
consumer must bind the actual damage/projectile to its action definition.
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

TARGET_NAME = "brainstorm"
FRAME_SIZE = (320, 252)
SUPER = 3
CENTER = (139, 105)
# Resting cerebral body, excluding the cloud, sparks and hanging nerves.
BODY_BOX = (73, 55, 205, 145)
# More temporal samples, but the exact same clip durations as v2. Keep the
# frame names and fixed body/anchor geometry unchanged. No gameplay events are
# tied to these authoring keyframes.
ROWS = [
    ("idle", 12, 70), ("walk", 12, 60), ("notice", 8, 55),
    ("windup", 8, 45), ("attack_side", 12, 35), ("hit", 6, 45),
    ("death", 12, 55),
]
ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Brainstorm"},
    "body": {"body_plan": "Amorphous", "body_kind": "Entity",
             "mass_class": "Light", "locomotion_hint": "Float",
             "traits": ["enemy", "neural", "brain", "electric", "floating", "bioengineered"]},
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["enemy", "neural"],
    "authoring_description": (
        "An original Neural dimension monster, literally a brain generating a "
        "thunderstorm. Inspired by the folds of a mammalian cortex, branched "
        "neurons and artificial neural interfaces. The storm, electrodes, "
        "eyes and lightning are fictional anatomy. A floating electrical "
        "predator rather than a brain inside a glass machine."
    ),
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
}

INK = '#241c30'
FLESH_DARK = '#773d59'
FLESH = '#b97689'
FLESH_LIGHT = '#e6a7a5'
FLESH_HI = '#f9c8b6'
GROOVE = '#71394f'
GROOVE_DEEP = '#542c48'
NERVE = '#a96c87'
NERVE_LIGHT = '#f1b6b1'
METAL_DARK = '#273648'
METAL = '#657d8f'
METAL_HI = '#a7c7d1'
ARC = (71, 212, 255, 255)
ARC_HI = (210, 255, 255, 255)
CLOUD_DARK = '#202536'
CLOUD = '#384259'
CLOUD_MID = '#4f5971'
CLOUD_HI = '#728095'


def clamp(t):
    return max(0.0, min(1.0, t))


def smooth(t):
    t = clamp(t)
    return t*t*(3-2*t)


def alpha(c, a):
    return (*c[:3], round(c[3]*clamp(a)))


def spline(points, closed=False, steps=9):
    """Interpolating Catmull-Rom path; stable anatomy from authored knots."""
    points = list(points)
    if closed:
        padded = [points[-1], *points, points[0], points[1]]
    else:
        padded = [points[0], *points, points[-1]]
    result = []
    for a,b,c,d in zip(padded,padded[1:],padded[2:],padded[3:]):
        for j in range(steps):
            t = j/steps
            result.append(tuple(0.5*((2*b[k])+(-a[k]+c[k])*t +
                (2*a[k]-5*b[k]+4*c[k]-d[k])*t*t +
                (-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in (0,1)))
    result.append(points[0] if closed else points[-1])
    return result


class Pen:
    def __init__(self, image, transform=lambda p:p):
        self.image = image
        self.transform = transform
        self.draw = ImageDraw.Draw(image)

    def xy(self, p):
        return tuple(round(v*SUPER) for v in self.transform(p))

    def poly(self, pts, fill, outline=None, width=1):
        pts = [self.xy(p) for p in pts]
        self.draw.polygon(pts, fill=fill)
        if outline:
            self.draw.line(pts+pts[:1], fill=outline, width=max(1,round(width*SUPER)), joint='curve')

    def shape(self, pts, fill, outline=None, width=1):
        self.poly(spline(pts, True), fill, outline, width)

    def line(self, pts, fill, width=1):
        self.draw.line([self.xy(p) for p in pts], fill=fill,
                       width=max(1,round(width*SUPER)), joint='curve')

    def curve(self, pts, fill, width=1):
        self.line(spline(pts), fill, width)

    def ellipse(self, center, radii, fill, outline=None, width=1):
        x,y = center
        rx,ry = radii
        self.poly([(x+rx*math.cos(i*math.tau/40), y+ry*math.sin(i*math.tau/40))
                   for i in range(40)],fill,outline,width)

    def offset(self,x,y):
        return Pen(self.image,lambda p:self.transform((p[0]+x,p[1]+y)))


@dataclass(frozen=True)
class Pose:
    """One shared body pose, plus secondary-motion and expression channels.

    Positions are local visual offsets only, never authoritative locomotion.
    Positive tilt is clockwise on screen. The nerves and cloud are animated
    independently of the cortex, not regenerated or detached at their roots.
    """
    x: float = 0
    y: float = 0
    sx: float = 1
    sy: float = 1
    tilt: float = 0
    charge: float = .28
    glare: float = .35
    blink: float = 0
    eye_light: float = 1
    nerve_sweep: float = 0
    nerve_lift: float = 0
    nerve_wave: float = 1
    wind: float = 0
    cloud_lag: float = 0
    bolt: float = 0
    bolt_reach: float = 0
    collapse: float = 0
    fade: float = 1
    phase: float = 0


REST = Pose()
PRIMED = replace(REST, x=-7, y=-5, sx=.94, sy=1.06, tilt=-.075,
                 charge=.78, glare=.95, nerve_sweep=5, nerve_lift=8,
                 nerve_wave=.7, wind=.62, cloud_lag=3)


def blend_pose(a, b, t):
    """Interpolate the authored channels, with no assumptions about frame count."""
    t = smooth(t)
    return Pose(**{f.name: getattr(a, f.name) + (getattr(b, f.name)-getattr(a, f.name))*t
                   for f in fields(Pose)})


def sample_keys(keys, t):
    for (ta,a),(tb,b) in zip(keys,keys[1:]):
        if t <= tb:
            return blend_pose(a,b,(t-ta)/(tb-ta))
    return keys[-1][1]


# Explicit choreography: preload, quick discharge, follow-through, recoil,
# settle. Reach and brightness are independent: the bolt can burn out without
# visibly retracting back into the monster's eye.
ATTACK_KEYS = [
    (0.00, PRIMED),
    (.09, replace(PRIMED,x=-9,sx=.91,sy=1.08,charge=1.0,nerve_lift=11)),
    (.27, replace(REST,x=9,y=-6,sx=1.09,sy=.94,tilt=.10,charge=1.0,
                  glare=1,nerve_sweep=-15,nerve_lift=13,wind=1,cloud_lag=-9,
                  bolt=1,bolt_reach=1)),
    (.45, replace(REST,x=13,y=-3,sx=1.06,sy=.96,tilt=.105,charge=.68,
                  glare=.9,nerve_sweep=-17,nerve_lift=8,wind=.6,cloud_lag=-11,
                  bolt=.78,bolt_reach=1)),
    (.64, replace(REST,x=-3,y=2,sx=.96,sy=1.035,tilt=-.055,charge=.33,
                  glare=.68,nerve_sweep=11,nerve_lift=0,wind=.18,cloud_lag=5,
                  bolt=.18,bolt_reach=1)),
    (.83, replace(REST,x=1,y=1,nerve_sweep=2,cloud_lag=-2,charge=.21)),
    (1.00, REST),
]

HIT_KEYS = [
    (0.00, replace(REST,x=-5,sy=1.06,sx=.96,tilt=-.075,blink=.72,glare=1,
                   charge=.67,nerve_sweep=8,cloud_lag=3)),
    (.20, replace(REST,x=-9,y=3,sy=1.08,sx=.94,tilt=-.125,blink=1,glare=1,
                   charge=.5,nerve_sweep=13,cloud_lag=6)),
    (.56, replace(REST,x=2,y=-1,sy=.97,sx=1.025,tilt=.045,blink=.3,
                   charge=.19,nerve_sweep=-8,cloud_lag=-4)),
    (1.00, REST),
]

DEATH_KEYS = [
    (0.00, replace(REST,charge=.95,glare=.9,nerve_lift=6)),
    (.18, replace(REST,x=-3,y=-5,sx=.95,sy=1.06,tilt=-.075,charge=1,
                  blink=.35,glare=1,nerve_lift=14,nerve_sweep=8,wind=.6)),
    (.44, replace(REST,x=2,y=4,sx=1.06,sy=.94,tilt=.10,charge=.48,
                  blink=.6,eye_light=.6,collapse=.25,nerve_sweep=-8,
                  nerve_wave=.65,cloud_lag=-4)),
    (.73, replace(REST,x=5,y=19,sx=1.06,sy=.81,tilt=.21,charge=.07,
                  blink=.95,eye_light=.08,collapse=.82,nerve_wave=.15,
                  nerve_lift=-2,cloud_lag=-7,fade=.9)),
    (1.00, replace(REST,x=7,y=23,sx=1.07,sy=.76,tilt=.24,charge=0,
                   blink=1,eye_light=0,collapse=1,nerve_wave=0,
                   nerve_lift=-2,cloud_lag=-9,fade=0)),
]


def pose_for(anim,i,n):
    loop = anim in ('idle','walk','windup')
    t = i / (n if loop else max(1,n-1))
    a = t*math.tau
    if anim == 'idle':
        bob=math.sin(a)
        # A full blink, then open again. All periodic channels close at 2pi.
        blink=max(0,1-abs(t-.667)/.12)**1.3
        pose=replace(REST,y=3.5*bob,sy=1+.025*math.sin(a-.3),
                     sx=1-.018*math.sin(a-.3),tilt=.018*math.sin(a),
                     charge=.28+.09*math.sin(a)**2,blink=blink,
                     nerve_sweep=2.5*math.sin(a-.9),cloud_lag=-1.8*math.sin(a))
    elif anim == 'walk':
        # Runtime walk is flight: a forward lean, elongated wake, no footfall.
        pose=replace(REST,x=2.2*math.sin(a),y=2.8*math.sin(a),tilt=.085+.022*math.sin(a),
                     sx=1.025+.015*math.cos(a),sy=.98-.015*math.cos(a),
                     nerve_sweep=-14+4*math.sin(a-.85),nerve_lift=5+2*math.sin(a-.9),
                     wind=.55,cloud_lag=-5+1.5*math.sin(a-.65),charge=.36)
    elif anim == 'notice':
        # Look up and snap into a charged stance; the eye leads the bulk.
        pose=blend_pose(REST,PRIMED,t)
        pose=replace(pose,y=pose.y-3.5*math.sin(math.pi*t),
                     glare=.35+.6*smooth(t*2.2),nerve_sweep=pose.nerve_sweep-3*math.sin(math.pi*t))
    elif anim == 'windup':
        # A repeatable charge hold; start/end agree with the notice/attack.
        pulse=math.sin(a)**2
        pose=replace(PRIMED,x=PRIMED.x-1.4*pulse,y=PRIMED.y+.65*math.sin(a),
                     sx=PRIMED.sx-.018*pulse,sy=PRIMED.sy+.02*pulse,
                     charge=.78+.22*pulse,nerve_lift=8+3*pulse,
                     nerve_sweep=5+2*math.sin(a),cloud_lag=3+1.5*pulse)
    elif anim == 'attack_side':
        pose=sample_keys(ATTACK_KEYS,t)
    elif anim == 'hit':
        pose=sample_keys(HIT_KEYS,t)
    elif anim == 'death':
        pose=sample_keys(DEATH_KEYS,t)
    else:
        raise ValueError(anim)
    return replace(pose,phase=a)


# Stable, asymmetrical cortex silhouette, with small lobular interruptions.
CORTEX = [(-61,-5),(-66,-17),(-61,-30),(-49,-35),(-41,-44),(-26,-45),
          (-13,-50),(0,-45),(11,-48),(25,-44),(37,-40),(48,-33),(58,-28),
          (63,-15),(61,-5),(66,4),(60,17),(50,25),(37,28),(30,36),
          (17,39),(6,35),(-6,39),(-17,32),(-29,34),(-39,28),(-51,21),(-61,11)]

# Sulci are authored as branches rather than a grid of identical grooves.
# The thick lower/inner ink and thin upper light make raised gyri readable.
FOLDS = [
    [(-57,-22),(-45,-23),(-37,-15),(-46,-8),(-49,0),(-37,7),(-30,17)],
    [(-43,-36),(-31,-29),(-32,-19),(-22,-13),(-12,-19),(-13,-29),(-5,-40)],
    [(-21,-42),(-20,-35),(-25,-29)],
    [(-6,-45),(3,-34),(0,-25),(8,-18),(19,-22),(21,-34),(28,-39)],
    [(13,-47),(13,-38),(9,-31)],
    [(35,-37),(34,-27),(26,-19),(29,-9),(42,-9),(50,-19),(57,-19)],
    [(46,-31),(44,-25),(46,-20)],
    [(-60,-1),(-51,6),(-52,14),(-43,19)],
    [(-38,-12),(-26,-4),(-29,7),(-20,16),(-10,13),(-6,3),(-13,-6)],
    [(-22,-10),(-12,-2),(-1,-6),(4,-12),(0,-20)],
    [(-37,26),(-28,25),(-22,19)],
    [(-16,31),(-15,23),(-4,19),(3,25),(0,34)],
    [(10,-16),(15,-6),(9,4),(17,11),(26,5),(23,-4)],
    [(28,-6),(34,2),(42,1),(50,-6),(59,-3)],
    [(7,12),(7,20),(18,25),(15,35)],
    [(33,28),(25,26),(23,18)],
    [(50,16),(59,10)],
]


def tissue(p, points, base, shadow, light):
    """Opaque volume with a narrow highlight plane and deep lower rim."""
    p.shape(points,shadow,INK,1.9)
    cx=sum(x for x,y in points)/len(points)
    cy=sum(y for x,y in points)/len(points)
    inner=[(cx+(x-cx)*.94-1.2,cy+(y-cy)*.88-2.8) for x,y in points]
    p.shape(inner,base)
    upper=[(cx+(x-cx)*.94-1.2,cy+(y-cy)*.88-2.8) for x,y in points if y<cy-5]
    if len(upper)>2:
        # Individual upper sections, not a closed ring of light.
        p.curve(upper[:len(upper)//2+1],light,1.6)


def draw_cortex(p,pose):
    # Cerebellum and brainstem, clearly distinct from the large cerebrum.
    cb=[(-47,15),(-27,18),(-11,29),(-12,42),(-24,48),(-40,42),(-49,30)]
    tissue(p,cb,'#995973','#63354f','#d79a9f')
    for j in range(5):
        y=24+j*4.2
        p.curve([(-43+j*.7,y),(-33,y+3),(-23,y+1),(-15,y-2)],GROOVE_DEEP,1.5)
        p.curve([(-40+j*.6,y-1),(-32,y+1),(-23,y-1)],'#cf8e99',.85)
    stem=[(-13,30),(6,29),(18,40),(15,51),(8,59),(3,67),(-6,66),(-9,55),(-15,43)]
    tissue(p,stem,'#b3748c','#754761','#e6a9ae')
    p.curve([(6,38),(2,49),(-2,58),(-1,64)],'#f0b3b3',2)
    p.curve([(-8,38),(-8,52),(-4,59)],GROOVE,1.4)
    # Main silhouette and a broad, dimensional lighting plane.
    p.shape(CORTEX,FLESH_DARK,INK,2.2)
    p.shape([(x*.963-1,y*.955-2) for x,y in CORTEX],FLESH)
    light_patch=[(-56,-23),(-43,-32),(-31,-39),(-14,-44),(0,-39),(15,-42),
                 (31,-35),(42,-27),(44,-15),(35,-10),(19,-12),(7,-7),(-5,-8),
                 (-17,1),(-31,-3),(-44,-9),(-53,-11)]
    p.shape(light_patch,'#cf8f98')
    p.curve([(-54,-27),(-43,-33),(-32,-41),(-21,-39)],FLESH_HI,2)
    p.curve([(-9,-44),(0,-41),(11,-44),(20,-41)],FLESH_HI,1.6)
    p.curve([(32,-38),(43,-31),(52,-24)],'#e5aca9',1.5)
    # Lower edge has a cool reflected light, not a pale overall wash.
    p.curve([(-54,13),(-44,22),(-31,27),(-18,27)],'#a989a3',2)
    p.curve([(-5,33),(7,31),(17,35),(30,29)],'#b38ba6',1.7)
    for j,fold in enumerate(FOLDS):
        pts=spline(fold)
        width=3.2 if j in (0,1,3,5,8,9,12,13) else 2.4
        p.line([(x,y+.65) for x,y in pts], '#9a566e',width+2)
        p.line(pts,GROOVE,width)
        p.line([(x,y-.35) for x,y in pts],GROOVE_DEEP,width*.52)
        p.line([(x-1,y-2.1) for x,y in pts[2:-2]],'#e6a5a4' if j<8 else '#d5929c',1.2)
    # Small blood vessels / neural traces on selected gyri.
    for path in [[(-46,-16),(-41,-12),(-42,-6)], [(-7,-34),(-4,-30),(-6,-27)],
                 [(35,-22),(38,-18),(36,-13)], [(-10,25),(-5,27),(-3,30)]]:
        p.curve(path,'#a05c79',.85)
    rng=random.Random('brainstorm-cortex-texture')
    for _ in range(48):
        x=rng.uniform(-47,37); y=rng.uniform(-31,23)
        if (x/49)**2+(y/34)**2<1:
            p.ellipse((x,y),(.5,.37),rng.choice(('#d49ba0','#b67b8a','#ac657a')))


def draw_eye(p,pose):
    # One dominant forward eye, with a recessed brow and fleshy rim.
    # A small far eye peeks around the frontal lobe.
    p.shape([(51,-10),(60,-12),(63,-6),(61,3),(55,4),(50,-1)],'#9b5871',INK,1.1)
    p.shape([(54,-7),(61,-8),(62,-3),(59,1),(54,0)],'#271f36')
    aperture=max(.04,1-pose.blink)
    def eye_color(lit):
        from PIL import ImageColor
        rgb=ImageColor.getrgb(lit)
        dark=(33,30,52)
        return tuple(round(a+(b-a)*pose.eye_light) for a,b in zip(dark,rgb))+(255,)
    p.ellipse((59,-3),(2.5,3.4*aperture),eye_color('#61bfcf'))
    p.ellipse((60,-3),(1.1,2.6*aperture),eye_color('#defaff'))
    if pose.blink>.08:
        p.shape([(52,-8),(60,-10),(63,-5),(61,-3),(55,-4)],FLESH, GROOVE,.8)
        if pose.blink>.75:
            p.curve([(54,-3),(59,-2),(62,-4)],GROOVE_DEEP,1.1)
    k=pose.glare
    p.shape([(19,1-2*k),(24,-7),(37,-10),(48,-7),(56,-1),(54,10),
             (47,18),(34,20),(23,14)],'#91536d',GROOVE_DEEP,1.5)
    # Preserve the fleshy socket, but close the actual aperture and iris
    # together. This avoids a glowing pupil shining through a closed lid.
    ep=Pen(p.image,lambda pt:p.transform((pt[0],6+(pt[1]-6)*aperture)))
    ep.shape([(23,1+3*k),(36,-4+2*k),(47,-2-2*k),(53,2-2*k),
              (50,11),(41,16),(30,13)],'#271b36',INK,1.5)
    ep.ellipse((42,6),(8.8,7.3),eye_color('#238aab'))
    ep.ellipse((44,5.6),(6.3,6.6),eye_color('#76e8eb'))
    ep.ellipse((45,5.2),(2.5,5.3),eye_color('#e4ffff'))
    if aperture>.25:
        ep.ellipse((43,2),(1.8,1.5),eye_color('#ffffff'))
    if pose.blink>.8:
        p.curve([(25,5),(36,7),(46,7),(53,4)],GROOVE_DEEP,1.5)
    # Heavy overhanging neural brow creates an expression, not a robot lens.
    p.shape([(20,0),(24,-8),(34,-11),(45,-8),(54,-5),(54,1+2*k),
             (43,-2+2*k),(33,-4+2*k),(25,1)],FLESH_LIGHT,GROOVE,1.2)
    p.curve([(24,-6),(35,-9),(45,-6)],FLESH_HI,1.3)
    p.curve([(28,14),(38,19),(48,15)],'#d89da6',1.7)


def tapered(p,pts,width,color,light):
    pts=spline(pts,steps=8)
    left=[]; right=[]
    for i,(x,y) in enumerate(pts):
        a=pts[max(i-1,0)]; b=pts[min(i+1,len(pts)-1)]
        dx,dy=b[0]-a[0],b[1]-a[1]
        norm=max(.001,math.hypot(dx,dy))
        w=width*(1-.87*i/max(1,len(pts)-1))/2
        left.append((x-dy/norm*w,y+dx/norm*w))
        right.append((x+dy/norm*w,y-dx/norm*w))
    p.poly(left+right[::-1],color,INK,.8)
    p.line([(x-.65,y-.35) for x,y in pts[:-3]],light,max(.65,width*.18))


def draw_nerves(p,pose):
    # Thick biological nerve roots split into fine dendrites. All attachment
    # points stay fixed on the stem/cerebrum while the hanging ends sway.
    roots=[(-46,22,-38,55,7),(-28,35,-44,77,7.5),(-11,47,-7,94,9),
           (8,52,24,85,8),(24,31,51,63,6.5),(43,21,64,48,5)]
    for j,(x,y,tx,ty,w) in enumerate(roots):
        # Lag increases toward the free end and varies with nerve length.
        # Roots remain on the anatomy. The branches inherit the same motion.
        a=pose.phase+1.1*j
        wave=pose.nerve_wave*(3.0+j*.65)
        drag=pose.nerve_sweep*(.72+.07*j)
        lift=pose.nerve_lift*(.7+.09*j)
        tx+=drag+wave*math.sin(a-1.15)
        ty-=lift+pose.collapse*9
        tx+=(j-2.5)*2.8*pose.collapse
        pts=[(x,y),(x*.9+drag*.22+wave*.25*math.sin(a),y+11-lift*.18),
             (tx-8+wave*.45*math.sin(a-.55),ty-13),(tx,ty)]
        tapered(p,pts,w,NERVE,NERVE_LIGHT)
        side=(-1 if j%2 else 1)
        fork=pts[2]
        for k in (0,1):
            ex=tx+side*(8+5*k)+wave*.36*math.sin(a-1.7-k*.45); ey=ty-6+8*k+wave*.25*math.cos(a-k*.7)
            tapered(p,[fork,(ex-3*side,ey-8),(ex,ey)],max(1.9,w*.35),NERVE,'#d89aa9')
            p.ellipse((ex,ey),(1.8,2.1),'#5dd2e0',INK,.55)
        p.ellipse((tx,ty),(2.6,3.3),'#408dba',INK,.75)
        p.ellipse((tx-.6,ty-.8),(1.1,1.7),'#d7ffff')


def draw_hardware(p,pose):
    # An asymmetrical rear interface, implanted contacts and an exposed cable.
    p.curve([(-56,-8),(-76,-12),(-80,1),(-65,16),(-52,13)],INK,7)
    p.curve([(-56,-8),(-76,-12),(-80,1),(-65,16),(-52,13)],METAL,4.8)
    p.curve([(-56,-9),(-76,-13),(-80,0),(-65,15)],METAL_HI,1.1)
    p.shape([(-61,-20),(-53,-23),(-45,-17),(-46,-5),(-50,3),(-62,1),(-67,-9)],METAL_DARK,INK,1.7)
    p.shape([(-60,-18),(-53,-19),(-49,-15),(-50,-6),(-61,-6),(-64,-11)],METAL)
    p.line([(-61,-17),(-55,-17),(-52,-14)],METAL_HI,1.4)
    for y in (-12,-7,-2):
        p.ellipse((-56,y),(1.5,1.1),'#b5fcff')
    for x,y,lean in [(-35,-37,-1),(3,-43,0),(40,-31,1)]:
        p.ellipse((x,y),(7.8,4.4),'#805167',INK,1.2)
        p.poly([(x-5,y),(x-6+lean*2,y-9),(x+3+lean*2,y-11),(x+6,y-3)],METAL_DARK,INK,1.1)
        p.poly([(x-4+lean*2,y-8),(x+3+lean*2,y-10),(x+4,y-5),(x-3,y-4)],METAL)
        p.line([(x-3+lean*2,y-8),(x+2+lean*2,y-9)],METAL_HI,1.4)
        p.ellipse((x+lean*2,y-10),(3.1,1.9),'#d0ffff',INK,.75)


def cloud_outline(x,y,rx,ry,phase,seed):
    return [(x+rx*(1+.065*math.sin(3*a+seed)+.025*math.cos(6*a-seed+phase))*math.cos(a),
             y+ry*(1+.06*math.sin(3*a+seed)+.025*math.cos(5*a+phase))*math.sin(a))
            for a in (i*math.tau/72 for i in range(72))]


def draw_clouds(p,pose):
    # A thunderhead has overlapping, heavy billows, not a glassy halo. Keep
    # the central brain exposed and reserve the brightest rims for lightning.
    a=pose.phase; w=pose.wind
    banks=[(-64,7,30,29,0),(-67,-22,27,24,1),(-43,-43,28,22,2),
           (-15,-48,31,23,3),(15,-49,25,19,4),(41,-36,26,22,5),
           (-61,35,28,22,6),(-36,52,31,16,7),(1,54,27,15,8),(-85,17,17,12,9)]
    for x,y,rx,ry,j in banks:
        dx=math.sin(a+j*.9)*3-7*w*(1 if x<0 else .35)
        dy=math.cos(a+j)*2.2
        # Rolling banks expand and drift apart when the storm loses power.
        x+=dx+pose.collapse*x*.13; y+=dy+pose.collapse*(y*.12-5)
        rx*=1+.10*w+.035*math.sin(a+j*.8); ry*=1+.05*w+.045*math.cos(a+j*.8)
        p.poly(cloud_outline(x,y,rx,ry,a,j),CLOUD_DARK,INK,1.1)
        p.poly(cloud_outline(x-1.7,y-2.5,rx*.89,ry*.84,a,j),CLOUD)
        p.poly(cloud_outline(x-3,y-4,rx*.72,ry*.67,a,j),CLOUD_MID)
        # crescent highlight on the top/rear, interrupted by other cloud lobes
        rim=cloud_outline(x-3,y-4,rx*.72,ry*.67,a,j)
        p.line(rim[37:54],CLOUD_HI,1.4)
        p.line(rim[42:48],'#9298ab',.7)
    # Trailing vapour curls and a little detached cloudlet. Unlike solid fins,
    # these taper away in a curve and have no hard triangular tip.
    for j in range(2):
        y=14+21*j+math.sin(a+j)*2
        p.shape([(-74,y-5),(-91,y-6),(-102,y-1),(-107,y+5),(-99,y+1),
                 (-87,y+4),(-74,y+7)],CLOUD,INK,.65)
        p.curve([(-102,y+1),(-93,y-3),(-81,y-2)],CLOUD_MID,1.6)
    p.shape([(-95,-20),(-104,-23),(-111,-18),(-109,-11),(-101,-10),(-94,-14)],CLOUD_DARK)
    p.curve([(-109,-17),(-104,-21),(-99,-19)],CLOUD_MID,1.3)


def lightning_points(start,end,seed,amp,segments=9,phase=0):
    rng=random.Random(seed)
    dx=end[0]-start[0]; dy=end[1]-start[1]; length=max(1,math.hypot(dx,dy))
    nx,ny=-dy/length,dx/length
    pts=[start]
    for i in range(1,segments):
        # Same underlying channel across frames, with a periodic jitter.
        # This makes the stroke fork and flicker without teleporting wholesale.
        base=rng.uniform(-.72,.72); angle=rng.uniform(0,math.tau)
        wobble=amp*(base+.28*math.sin(2*phase+angle))
        pts.append((start[0]+dx*i/segments+nx*wobble,
                    start[1]+dy*i/segments+ny*wobble))
    return pts+[end]


def electric(p,glow,points,strength=1,width=1.5,branches=True,seed=0):
    """Hard white core and narrow blue edge; blur is a separate layer."""
    if strength<=0: return
    p.line(points,alpha(ARC,.83*strength),width+2.2)
    p.line(points,alpha(ARC_HI,strength),width)
    glow.line(points,alpha(ARC,.6*strength),width+5)
    if branches and len(points)>4:
        rng=random.Random(seed)
        for i in (2,len(points)//2):
            x,y=points[i]; end=(x+rng.uniform(-12,12),y+rng.choice((-1,1))*rng.uniform(9,16))
            branch=lightning_points((x,y),end,seed+i,2,4)
            p.line(branch,alpha(ARC,.85*strength),1.1)
            p.line(branch,alpha(ARC_HI,.8*strength),.6)
            glow.line(branch,alpha(ARC,.5*strength),3.2)


def render_frame(anim,i,n):
    pose=pose_for(anim,i,n)
    size=tuple(v*SUPER for v in FRAME_SIZE)
    img=Image.new('RGBA',size)
    def transform(pt):
        x,y=pt[0]*pose.sx,pt[1]*pose.sy
        c,s=math.cos(pose.tilt),math.sin(pose.tilt)
        return CENTER[0]+pose.x+x*c-y*s,CENTER[1]+pose.y+x*s+y*c
    p=Pen(img,transform)
    # Lagged cloud follows the cortex without being rigidly glued to it.
    cloud=Image.new('RGBA',size)
    cp=Pen(cloud,lambda pt:transform((pt[0]+pose.cloud_lag,pt[1]-4*pose.collapse)))
    draw_clouds(cp,pose)
    if pose.collapse:
        cloud.putalpha(cloud.getchannel('A').point(lambda v:round(v*(1-.7*pose.collapse))))
    img.alpha_composite(cloud)
    # Rear lightning is behind solid anatomy.
    rear=Image.new('RGBA',size); rg=Image.new('RGBA',size)
    rp,gp=Pen(rear,transform),Pen(rg,transform)
    arcs=[((-83,-8),(-38,-46)),((-55,-56),(5,-60)),((-63,32),(-25,60)),((8,52),(37,54)),((-85,22),(-93,57))]
    for j,(a,b) in enumerate(arcs):
        strength=pose.charge*(.7+.3*math.sin(pose.phase+j)**2)
        electric(rp,gp,lightning_points(a,b,51+j*7,4,9,pose.phase),strength,1.2,True,j+19)
    img.alpha_composite(rg.filter(ImageFilter.GaussianBlur(2.4*SUPER)))
    img.alpha_composite(rear)
    draw_nerves(p,pose)
    draw_cortex(p,pose)
    draw_hardware(p,pose)
    draw_eye(p,pose)
    # Front sparks are selective and leave the brain's local color intact.
    front=Image.new('RGBA',size); fg=Image.new('RGBA',size)
    fp,gp=Pen(front,transform),Pen(fg,transform)
    strength=pose.charge
    if strength>.15:
        for j,(a,b) in enumerate([((-35,-47),(-54,-58)),((3,-53),(26,-62)),((40,-41),(60,-27))]):
            electric(fp,gp,lightning_points(a,b,80+j*3,3,6,pose.phase),strength*(.82+.18*math.sin(pose.phase*2+j)**2),1.1,True,j+23)
        for j in range(8):
            angle=j*2.399+pose.phase
            x=math.cos(angle)*(75+6*math.sin(j)); y=math.sin(angle)*53
            gp.ellipse((x,y),(2.5,2.5),alpha(ARC,.25*strength))
            fp.ellipse((x,y),(.8,1.4),alpha(ARC_HI,.7*strength))
    if pose.bolt>0:
        # A compact, forked lightning stroke, telegraphed by the preceding row.
        # It does not itself create a projectile or hitbox.
        b=pose.bolt
        end=(66+62*pose.bolt_reach,-7+4*math.sin(pose.phase))
        electric(fp,gp,lightning_points((58,3),end,370,6+4*b,12,pose.phase),b,2.1+1.5*b,True,81)
        if b>.22:
            electric(fp,gp,lightning_points((59,6),(end[0]-10,end[1]+19),777,5,8,pose.phase),b*.65,1.4,False)
        gp.ellipse((58,3),(7*b,7*b),alpha(ARC,.6*b))
    if anim=='hit':
        stun=max(0,1-i/max(1,n-1)*2.2)
        electric(fp,gp,lightning_points((-48,-10),(38,19),480,4,10,pose.phase),.9*stun,1.8,True,12)
    if anim=='death' and pose.charge>.1:
        # The last uncontrolled discharges leave through the nerve endings.
        for j,(a,b) in enumerate([((-12,48),(-35,89)),((15,42),(47,79)),((-51,-28),(-90,-45))]):
            electric(fp,gp,lightning_points(a,b,910+j,6,10,pose.phase),pose.charge*.75,1.5,True,19+j)
    img.alpha_composite(fg.filter(ImageFilter.GaussianBlur(2.2*SUPER)))
    img.alpha_composite(front)
    if pose.fade<1:
        img.putalpha(img.getchannel('A').point(lambda v:round(v*pose.fade)))
    return resize_transparent_sprite(img,FRAME_SIZE)


def _body_metrics(fw,fh):
    return body_metrics_for_box(BODY_BOX,fw,fh)


def render(out_dir: str | Path, **opts):
    # Authoring coordinates are fixed; the publisher handles lower tiers.
    del opts
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=render_frame,
                        out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,
                        actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,
                        pose_bodies='authored',animation_key_map={name:name for name,_,_ in ROWS})
    return [Path(outputs[key]) for key in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent') if outputs.get(key)]


TARGETS={TARGET_NAME:{'render':render,'actor_metadata':ACTOR_METADATA}}
