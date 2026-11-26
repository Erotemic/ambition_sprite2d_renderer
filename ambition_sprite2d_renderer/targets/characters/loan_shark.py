"""Loan Shark: the literal predatory lender of Capital.

A stocky, blue-grey shark in a tailored pinstripe suit. He carries the loan
ledger throughout the fight. His jaws are the weapon: an open-mouthed tell,
short forward rush, snap and leisurely return to the accounts. Tail, limbs,
head, jaw and book are posed independently from one vector-like drawing.
No drop shadows. The engine supplies the rush, hit geometry and damage.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

TARGET_NAME = "loan_shark"
FRAME_SIZE = (284, 234)
GROUND = 214.0
CX = 136.0
SUPER = 3
WINDUP_S, ACTIVE_S, RECOVER_S = 0.60, 0.24, 0.76
TOTAL_S = WINDUP_S + ACTIVE_S + RECOVER_S
ROWS = [
    ("idle", 16, 100), ("walk", 16, 80), ("notice", 8, 75),
    ("windup", 12, 50), ("attack_side", 40, 40),
    ("hit", 8, 75), ("death", 18, 95),
]
LOOPS = {"idle", "walk", "notice", "windup"}
ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Loan Shark"},
    "body": {"body_plan": "Biped", "body_kind": "Standard", "mass_class": "Heavy",
             "locomotion_hint": "Walk", "traits": ["enemy", "business", "shark"]},
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["enemy", "business", "shark", TARGET_NAME],
    "authoring_description": (
        "A literal visual pun on the term loan shark, a predatory lender. A fictional "
        "anthropomorphic shark in a charcoal pinstripe suit, with a burgundy tie, "
        "gold accessories and a leather ledger. The open jaws and short lunge are "
        "invented combat metaphors, not a depiction of ordinary bank workers."
    ),
    "gameplay_description": (
        "A grounded melee enemy. He studies the player, opens his jaws, then rushes "
        "forward and bites. During the recovery he returns to his accounts. The "
        "ledger is an animated prop; it does not change money or health independently."
    ),
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
}
INK = '#202539'
SKIN = '#789cae'
SKIN_D = '#45687e'
SKIN_L = '#abc4ca'
BELLY = '#e1e6db'
BELLY_D = '#a7b7ba'
NAVY = '#38445d'
NAVY_D = '#252d43'
NAVY_L = '#52637b'
STRIPE = '#67788a'
SHIRT = '#f2e7d1'
TIE = '#a64050'
TIE_D = '#722f46'
GOLD = '#d6ae5a'
GOLD_L = '#f6dc9b'
LEATHER = '#794737'
LEATHER_D = '#4a3030'
LEATHER_L = '#b17650'
PAGE = '#e9d6aa'
SHOE = '#292938'
MOUTH = '#4c2939'
GUM = '#a75960'


def clamp(t):
    return max(0.0, min(1.0, t))


def smooth(t):
    t = clamp(t)
    return t*t*(3-2*t)


def lerp(a, b, t):
    return a + (b-a)*t


def track(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (a, x), (b, y) in zip(keys, keys[1:]):
        if t <= b:
            return lerp(x, y, smooth((t-a)/(b-a)))
    return keys[-1][1]


def add(a, b):
    return (a[0]+b[0], a[1]+b[1])


def sub(a, b):
    return (a[0]-b[0], a[1]-b[1])


def mul(a, k):
    return (a[0]*k, a[1]*k)


def rot(p, angle):
    a = math.radians(angle)
    c, s = math.cos(a), math.sin(a)
    return (c*p[0]-s*p[1], s*p[0]+c*p[1])


def bez(points, n=15):
    """Piecewise cubic Bezier path, in frame pixels."""
    assert (len(points)-1) % 3 == 0
    out = [points[0]]
    for j in range(0, len(points)-1, 3):
        a,b,c,d = points[j:j+4]
        for k in range(1, n+1):
            t = k/n
            q = 1-t
            out.append(tuple(q**3*a[i]+3*q*q*t*b[i]+3*q*t*t*c[i]+t**3*d[i]
                             for i in (0, 1)))
    return out


class Draw:
    """Small supersampled vector-style painting surface; coordinates y down."""
    def __init__(self):
        self.im = Image.new('RGBA', tuple(x*SUPER for x in FRAME_SIZE))
        self.d = ImageDraw.Draw(self.im)

    def line(self, p, c=INK, w=1.8, closed=False):
        pts = [(x*SUPER, y*SUPER) for x,y in p]
        if closed:
            pts.append(pts[0])
        self.d.line(pts, fill=c, width=max(1, round(w*SUPER)), joint='curve')
        if not closed:
            r = w*SUPER/2
            for x,y in (pts[0],pts[-1]):
                self.d.ellipse((x-r,y-r,x+r,y+r), fill=c)

    def poly(self, p, c, edge=INK, w=2):
        self.d.polygon([(x*SUPER,y*SUPER) for x,y in p], fill=c)
        if edge:
            self.line(p, edge, w, True)

    def shape(self, p, c, edge=INK, w=2):
        self.poly(bez(p), c, edge, w)

    def curve(self, p, c=INK, w=1.5):
        self.line(bez(p),c,w)

    def oval(self, x,y,rx,ry,c,edge=INK,w=1.5,angle=0):
        pts = [add((x,y),rot((rx*math.cos(t),ry*math.sin(t)),angle))
               for t in (math.tau*i/56 for i in range(56))]
        self.poly(pts,c,edge,w)

    def tube(self, p, c, w):
        self.line(p, INK, w+3.2)
        self.line(p, c, w)

    def finish(self, fade):
        if fade < 1:
            self.im.putalpha(self.im.getchannel('A').point(lambda a: round(a*fade)))
        return self.im.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


@dataclass(frozen=True)
class Pose:
    hip: tuple[float, float]
    lean: float
    neck: float
    jaw: float
    mood: float
    blink: float
    phase: float
    stride: float
    crouch: float
    point: float
    book_open: float
    book_tilt: float
    tail: float
    collapse: float
    fade: float


def pose(anim, i, n):
    t = i/(n if anim in LOOPS else max(1,n-1))
    p = math.tau*t
    lean, neck, jaw, mood = 3., -2., 2., .22
    blink = max(0., math.cos(p-4.6))**40
    stride, crouch, point, opened, tilt = 0., 0., 0., .0, -9.
    tail, collapse, fade = 5.*math.sin(p), 0., 1.
    bob = 1.4*math.sin(p)
    if anim == 'walk':
        stride, lean = 1., 9.+2.*math.sin(2*p)
        bob = 2.5*abs(math.sin(p))
        tail = 9.*math.sin(p+.8)
        tilt = -11.+3.*math.sin(p)
    elif anim == 'notice':
        bob, lean, neck = -2., -5., -8.
        point, mood, blink = .85, .43, 0.
        tail = -5.+2.*math.sin(p)
    elif anim == 'windup':
        # A held pose, not a looping morph: telegraph rows may be sampled
        # from the global sim clock. Small breathing/tail movements are OK.
        lean, neck, jaw, mood = -11., -9., 30., .95
        crouch, point, tilt = 9., .2, -18.
        tail, blink, bob = -4.+2.*math.sin(p), 0., .8*math.sin(p)
    elif anim == 'attack_side':
        s = t*TOTAL_S
        lean = track(s, [(0,-11),(.60,-11),(.70,23),(.84,22),(1.05,6),(1.34,0),(1.60,3)])
        neck = track(s, [(0,-9),(.60,-9),(.68,5),(.77,9),(.84,2),(1.05,-2),(1.34,9),(1.60,-2)])
        jaw = track(s, [(0,30),(.60,30),(.68,36),(.77,1),(.84,0),(1.02,5),(1.60,2)])
        mood = track(s, [(0,.95),(.84,1.),(1.04,.6),(1.35,.12),(1.60,.22)])
        crouch = track(s, [(0,9),(.60,9),(.70,4),(.84,6),(1.05,3),(1.60,0)])
        point = track(s, [(0,.2),(.60,.2),(.72,.8),(.84,.5),(1.04,0),(1.60,0)])
        opened = track(s, [(0,0),(.88,0),(1.12,1),(1.40,1),(1.60,0)])
        tilt = track(s, [(0,-18),(.60,-18),(.84,-26),(1.04,-9),(1.18,-28),(1.60,-9)])
        tail = track(s, [(0,-4),(.60,-4),(.74,14),(.96,4),(1.60,0)])
        bob, blink = 0., 0.
    elif anim == 'hit':
        recoil = math.sin(math.pi*t)
        lean, neck, jaw, mood = 3.-22*recoil, -2.-9*recoil, 2+13*recoil, .4+.4*recoil
        crouch, point, tail = 5*recoil, .15, -5*recoil
        bob, blink = 0., recoil*.8
    elif anim == 'death':
        collapse = smooth(t/.83)
        lean, neck, jaw = lerp(3,-74,collapse), lerp(-2,-12,collapse), lerp(2,12,collapse)
        crouch, mood, blink = 32*collapse, .1, collapse
        tail, tilt = 48*collapse, lerp(-9,16,collapse)
        bob = 0.
        fade = 1.-.68*smooth((t-.78)/.22)
    return Pose((CX,GROUND-62+crouch+bob),lean,neck,jaw,mood,blink,p,stride,crouch,
                point,opened,tilt,tail,collapse,fade)


def B(q, x,y):
    return add(q.hip,rot((x,y),q.lean))


def draw_tail(d,q):
    # The caudal peduncle leaves through a split in the jacket. Both lobes
    # turn about the same attachment, so the fork never detaches from the tail.
    root = B(q,-17,-9)
    a = q.tail + q.lean*.25
    def T(x,y): return add(root,rot((x,y),a))
    def sh(p,c,e=INK,w=2.2): d.shape([T(*v) for v in p],c,e,w)
    def po(p,c,e=INK,w=2): d.poly([T(*v) for v in p],c,e,w)
    sh([(4,-8),(-17,-6),(-36,7),(-53,3),(-65,-1),(-72,-8),(-83,-13),
        (-78,-4),(-75,6),(-67,14),(-69,21),(-77,30),(-80,43),
        (-66,40),(-57,27),(-51,20),(-33,24),(-14,12),(4,10),(12,4),(13,-4),(4,-8)], SKIN)
    sh([(4,3),(-18,11),(-37,20),(-52,15),(-61,15),(-68,26),(-76,36),
        (-66,34),(-56,23),(-51,20),(-34,24),(-15,14),(4,10),(9,8),(9,4),(4,3)], SKIN_D,None)
    d.curve([T(-8,-1),T(-27,4),T(-45,12),T(-60,9)], SKIN_L,2.2)
    d.line([T(-63,9),T(-69,1),T(-76,-8)],SKIN_D,1.5)
    d.line([T(-63,16),T(-69,25),T(-76,36)],SKIN_D,1.5)


def draw_leg(d,q,far):
    # The stance changes with a gait cycle but the planted foot stays on
    # GROUND. Death has folded legs instead of a standing body spun in place.
    phase = q.phase + (math.pi if far else 0)
    stride = q.stride*math.sin(phase)
    lift = q.stride*max(0.,math.cos(phase))*9
    if q.lean>15 and not q.collapse:
        stride = -.7 if far else .65
    root = B(q,-8 if far else 8,-2)
    x = CX+(-10 if far else 10)+22*stride - 10*q.collapse
    y = GROUND-8-lift
    knee = ((root[0]+x)*.5+7+q.crouch*.5, lerp(root[1],y,.53)-q.collapse*5)
    if q.collapse:
        knee = (CX+12+(7 if far else 0),GROUND-26)
        x += 26*q.collapse
    foot = (x,y)
    base = NAVY_D if far else NAVY
    ankle = add(foot,(0,-9))
    d.tube([root,knee,ankle],base,19 if far else 22)
    d.line([add(root,(-5,1)),add(knee,(-4,0)),add(ankle,(-4,0))],STRIPE if not far else NAVY_L,1.2)
    if not far:
        d.line([add(root,(5,1)),add(knee,(6,0)),add(ankle,(5,0))],NAVY_L,1.3)
    # Oxford shoes with toe cap, vamp and sole. No ground shadow.
    fx,fy=foot
    d.shape([(fx-10,fy-7),(fx-7,fy-10),(fx+2,fy-9),(fx+6,fy-5),
             (fx+13,fy-5),(fx+21,fy-1),(fx+20,fy+5),(fx+11,fy+8),(fx-9,fy+8),
             (fx-11,fy+4),(fx-12,fy-1),(fx-11,fy-5),(fx-10,fy-7)],SHOE)
    d.line([(fx-9,fy+5),(fx+7,fy+5),(fx+19,fy+4)],'#767487',1.2)
    d.curve([(fx+4,fy-5),(fx+9,fy-5),(fx+14,fy-2),(fx+14,fy+2)],'#66687a',1.4)
    for k in range(3):
        d.line([(fx-3+k*2.5,fy-6),(fx+k*2.5,fy-3)],'#8b8490',.85)


def draw_torso(d,q):
    def po(p,c,e=INK,w=2): d.poly([B(q,*v) for v in p],c,e,w)
    def sh(p,c,e=INK,w=2): d.shape([B(q,*v) for v in p],c,e,w)
    def li(p,c=INK,w=1.5): d.line([B(q,*v) for v in p],c,w)
    def cv(p,c=INK,w=1.5): d.curve([B(q,*v) for v in p],c,w)
    def ov(x,y,rx,ry,c,e=INK,w=1.5): d.oval(*B(q,x,y),rx,ry,c,e,w,q.lean)
    # Dorsal fin, behind the jacket collar, with visible seam at the vent.
    sh([(-20,-51),(-43,-66),(-47,-89),(-40,-111),(-34,-104),(-26,-86),(-13,-73),
        (-8,-63),(-10,-54),(-20,-51)],SKIN_D)
    cv([(-39,-103),(-39,-90),(-29,-77),(-21,-70)],SKIN_L,1.6)
    # Broad shoulders and a taper to the waist, two skirt panels.
    sh([(-11,-75),(-23,-75),(-34,-69),(-37,-56),(-39,-42),(-34,-24),(-29,-6),
        (-30,5),(-22,13),(-6,12),(-1,8),(6,7),(13,13),(31,11),(34,3),(29,-12),
        (34,-27),(40,-46),(37,-56),(34,-68),(22,-75),(12,-75),(4,-77),(-4,-77),(-11,-75)],NAVY)
    sh([(-33,-59),(-37,-43),(-30,-17),(-29,-6),(-29,6),(-22,11),(-8,10),
        (-15,-8),(-14,-30),(-20,-53),(-25,-58),(-29,-61),(-33,-59)],NAVY_D,None)
    # Restrained pinstripes, curved with the tailoring; no stripes cross the lapel.
    for x in (-29,-22,-15,18,25,32):
        if x<0:
            cv([(x,-57),(x-1,-44),(x+4,-21),(x+2,7)],STRIPE,1.15)
        else:
            cv([(x,-58),(x+2,-43),(x-4,-23),(x-4,7)],STRIPE,1.15)
    po([(-10,-73),(10,-73),(20,-60),(5,-16),(-10,-39),(-18,-58)],SHIRT)
    po([(-5,-67),(5,-67),(9,-58),(4,-53),(-4,-54),(-9,-61)],TIE)
    po([(-4,-54),(5,-53),(10,-30),(3,-22),(-4,-30)],TIE_D)
    li([(2,-50),(5,-33)],'#dc7780',1.35)
    # Separate left and right notched lapels with edges.
    po([(-15,-76),(-30,-66),(-23,-49),(-15,-52),(-20,-43),(2,-11),(-5,-39),(-12,-62)],NAVY_L)
    po([(12,-76),(31,-67),(25,-50),(17,-53),(22,-43),(2,-11),(9,-40),(12,-62)],NAVY_L)
    li([(-26,-64),(-20,-52),(-13,-52)],'#93a1ae',1.25)
    li([(29,-64),(22,-52),(18,-52)],'#93a1ae',1.25)
    li([(2,-11),(5,8)],INK,1.8)
    for y in (-11,1):
        ov(7,y,2.4,2.4,'#1d2230',GOLD,1.)
    # Breast pocket square and waist pockets.
    po([(18,-43),(29,-43),(28,-35),(17,-35)],NAVY_D)
    po([(19,-43),(21,-49),(24,-44),(27,-47),(28,-43)],'#d5b9a8',INK,1)
    po([(-26,-15),(-12,-16),(-11,-11),(-25,-10)],NAVY_D)
    po([(17,-16),(30,-17),(30,-11),(17,-10)],NAVY_D)
    cv([(16,-6),(20,-1),(24,0),(28,-7)],GOLD,1.4)
    ov(16,-6,1.8,1.8,GOLD)
    ov(28,-7,1.8,1.8,GOLD)


def draw_head(d,q):
    center=B(q,6,-84)
    a=q.lean+q.neck
    def H(x,y): return add(center,rot((x,y),a))
    pivot=(-17,8)
    def J(x,y): return H(*add(pivot,rot(sub((x,y),pivot),q.jaw)))
    def sh(p,c,e=INK,w=2.3): d.shape([H(*v) for v in p],c,e,w)
    def po(p,c,e=INK,w=1.5): d.poly([H(*v) for v in p],c,e,w)
    def cv(p,c=INK,w=1.7): d.curve([H(*v) for v in p],c,w)
    def ov(x,y,rx,ry,c,e=INK,w=1.5): d.oval(*H(x,y),rx,ry,c,e,w,a)
    # Thick neck and lower jaw; the throat is one dark cavity, not a black
    # line across the snout. The jaw pivots at the rear of the mouth.
    sh([(-28,-2),(-38,10),(-34,25),(-17,30),(-7,33),(4,29),(7,20),
        (6,9),(-11,-5),(-28,-2)],SKIN_D)
    upper_lip=[(-15,8),(3,14),(26,11),(48,3)]
    lower_lip=[(-15,8),(7,14),(27,12),(47,4)]
    mouth=bez([H(*p) for p in upper_lip])+list(reversed(bez([J(*p) for p in lower_lip])))
    d.poly(mouth,MOUTH,INK,2)
    # Lower jaw's bone/cream skin and a reflected underside band.
    lower=[(-17,8),(-2,12),(30,15),(47,4),(55,10),(47,21),(33,25),
           (17,31),(-4,31),(-18,25),(-24,20),(-23,12),(-17,8)]
    d.shape([J(*p) for p in lower],BELLY,INK,2.2)
    d.shape([J(*p) for p in [(-18,23),(-3,28),(19,28),(33,25),(15,35),(-8,34),(-18,25),(-19,25),(-19,24),(-18,23)]],BELLY_D,None)
    # Lower teeth are attached to the lower jaw; upper teeth stay on the head.
    # Both are visible as the shark opens his mouth; the closed pose retains
    # the characteristic jagged smile without disconnected floating teeth.
    if q.jaw>3:
        for x,y,dy in [(3,11,5),(12,12,6),(22,11,6),(32,9,5),(41,6,4)]:
            d.poly([J(x-3,y+2),J(x+3,y+1),J(x+1,y-dy)],'#fff1d5',INK,.75)
    # Upper head: long rounded wedge of a snout, sloping back and heavy brow.
    sh([(-28,14),(-39,8),(-40,-11),(-31,-26),(-21,-42),(4,-41),(22,-29),
        (38,-22),(49,-14),(57,-6),(63,-1),(57,6),(48,7),
        (30,13),(4,17),(-13,9),(-20,17),(-26,17),(-28,14)],SKIN)
    sh([(-29,14),(-23,6),(-19,3),(-13,7),(3,13),(32,9),(48,4),
        (53,2),(57,2),(57,4),(50,10),(23,17),(2,17),(-13,9),(-20,17),(-29,14)],BELLY,None)
    # Sculpted dorsal highlight and shaded back of head.
    sh([(-31,-25),(-35,-14),(-36,0),(-29,9),(-24,1),(-24,-12),(-18,-24),
        (-13,-34),(-3,-37),(4,-36),(-13,-42),(-24,-35),(-31,-25)],SKIN_D,None)
    cv([(-21,-30),(-6,-40),(12,-33),(22,-27)],SKIN_L,3.)
    cv([(25,-24),(35,-20),(44,-14),(50,-9)],SKIN_L,1.7)
    # Gill slits sit behind the mouth, with three dark tapered cuts.
    for k in range(3):
        x=-29+k*4.5
        cv([(x,-5),(x+2,-1),(x+2,4),(x,8)],SKIN_D,1.8)
    # A small nostril; shark eyes are lateral and expressive.
    ov(46,-6,2.5,1.5,SKIN_D,INK,.7)
    ex,ey=17,-15
    ry=max(1.15,(6.1-2.0*q.mood)*(1-.91*q.blink))
    ov(ex,ey,9.5,ry,SHIRT,INK,1.7)
    if q.blink<.76:
        ov(ex+2,ey+.4,4.0,max(1.,ry*.90), '#c4a259',INK,.9)
        ov(ex+3.1,ey+.5,2.2,max(.7,ry*.72),INK,None)
        ov(ex+.8,ey-1.7,1.25,1.2,'#fff3da',None)
    # Lowered inner brow when he is about to collect.
    cv([(ex-10,ey-6-q.mood*2),(ex-5,ey-8),(ex+4,ey-6+q.mood*4),(ex+10,ey-4+q.mood*3)],INK,2.9)
    if q.jaw>3:
        for x,y,h in [(0,13,5),(9,14,7),(19,13,8),(29,11,7),(39,8,6),(48,5,4)]:
            po([(x-4,y-1),(x+4,y-1),(x+1,y+h)],'#fff2d8',INK,.8)
    else:
        # Small alternating triangles over the lower lip make a closed grin.
        cv([(-13,9),(5,16),(31,12),(50,5)],INK,1.8)
        for x,y in [(4,14),(13,14),(22,13),(31,11),(40,8)]:
            po([(x-3,y-1),(x+3,y-1),(x+1,y+4)],'#fff1d5',INK,.65)
    ov(-14,9,2.3,2.0,SKIN_D,None)


def draw_hand(d, p, angle=0, near=True, pointing=False):
    def H(x,y): return add(p,rot((x,y),angle))
    c=SKIN if near else SKIN_D
    d.oval(*p,9,7.8,c,INK,1.8,angle)
    if pointing:
        d.tube([H(3,-3),H(12,-3),H(20,-1)],c,5.4)
        d.oval(*H(1,3),5.7,4.5,c,INK,1.3,angle)
    else:
        for x in (-2,2,6):
            d.line([H(x,-1),H(x-1,4)],SKIN_D if near else INK,1.1)
        d.oval(*H(-4,-4),5.0,3.3,c,INK,1.1,angle-10)


def draw_arm(d, shoulder, elbow, hand, near, pointing=False):
    base=NAVY if near else NAVY_D
    d.tube([shoulder,elbow,hand],base,18 if near else 16)
    d.line([add(shoulder,(-4,0)),add(elbow,(-4,0)),add(hand,(-3,-4))],STRIPE,1.3)
    d.line([add(shoulder,(4,1)),add(elbow,(4,-1)),add(hand,(3,-5))],NAVY_L,1.2)
    angle=math.degrees(math.atan2(hand[1]-elbow[1], hand[0]-elbow[0]))
    def A(x,y): return add(hand,rot((x,y),angle))
    d.poly([A(-9,-9),A(-3,-9),A(-3,9),A(-9,9)],SHIRT,INK,1.4)
    d.oval(*A(-7,-4),1.6,1.6,GOLD,INK,.7)
    draw_hand(d,hand,angle if not pointing else 0,near,pointing)


def draw_ledger(d, center, tilt, opened):
    """Leather-bound double-entry book, drawn in the same hand space.

    The near cover swings open around the spine. Page block never vanishes.
    """
    def P(x,y): return add(center,rot((x,y),tilt))
    def po(p,c,e=INK,w=1.7): d.poly([P(*v) for v in p],c,e,w)
    def li(p,c=INK,w=1.2): d.line([P(*v) for v in p],c,w)
    # Back cover, page block and spine.
    po([(-22,-18),(17,-18),(22,-13),(22,19),(-20,19),(-24,14)],LEATHER_D)
    po([(-18,-16),(18,-15),(19,15),(-18,15)],PAGE)
    for y in (11,13): li([(-15,y),(18,y)],'#ae906e',.9)
    po([(-25,-18),(-18,-20),(-18,19),(-24,18)],LEATHER)
    li([(-22,-16),(-22,16)],LEATHER_L,1.3)
    if opened>.01:
        # The exposed page is a ledger grid, with neat entries in dark ink.
        po([(-17,-15),(18,-14),(18,14),(-17,14)],'#f1dfb8')
        li([(7,-12),(7,12)],'#c7aa82',.85)
        for y in (-8,-3,2,7,12):
            li([(-13,y),(15,y)],'#bc9f7d',.65)
        for y in (-6,-1,4,9):
            li([(-12,y),(-5,y)],LEATHER_D,1.1)
            li([(10,y),(14,y)],'#85505a',1.15)
    # Flatten toward the edge at half turn, then extend to the other side.
    width=41*math.cos(math.pi*opened)
    if abs(width)>1:
        x=-20+width
        po([(-20,-20),(x,-18),(x,17),(-20,19)],LEATHER)
        # Inner bevel, brass corners, and a stylized embossed currency sign.
        direction=1 if width>0 else -1
        inset=3*direction
        if abs(width)>13:
            li([(-20+inset,-16),(x-inset,-14),(x-inset,13),(-20+inset,15)],LEATHER_L,1.2)
            for y in (-17,15):
                po([(x,y),(x-7*direction,y),(x,y+(6 if y<0 else -6))],GOLD,INK,.7)
            mid=(-20+x)/2
            if opened<.35:
                d.oval(*P(mid,-1),7*abs(math.cos(math.pi*opened)),8,GOLD,LEATHER_D,1.2,tilt)
                li([(mid,-7),(mid,5)],LEATHER_D,1.3)
                li([(mid+3,-5),(mid-3,-5),(mid-3,-1),(mid+3,-1),(mid+3,3),(mid-3,3)],LEATHER_D,1.2)
    else:
        li([(-20,-20),(-20,19)],LEATHER_D,2.)


def _render_frame(anim,i,n):
    q=pose(anim,i,n)
    d=Draw()
    draw_tail(d,q)
    draw_leg(d,q,True)
    # The far hand gestures while the near hand holds the ledger. Its elbow
    # and shoulder remain connected through windup, charge and recovery.
    s=B(q,25,-58)
    e=B(q,36+9*q.point,-35-8*q.point)
    hand=B(q,40+28*q.point,-22-20*q.point)
    grip=B(q,-1+5*q.book_open,-15-3*q.book_open)
    book=add(grip,rot((15,-13),q.lean))
    book_angle=q.lean+q.book_tilt
    # As the ledger opens, the other hand moves onto the page.
    writing=smooth(q.book_open)
    target_hand=add(book,rot((26,-10+2*math.sin(q.phase*4)),book_angle))
    hand=add(mul(hand,1-writing),mul(target_hand,writing))
    draw_arm(d,s,e,hand,False,q.point>.42)
    draw_leg(d,q,False)
    draw_torso(d,q)
    draw_head(d,q)
    # Near arm supports the book from below. Book, wrist and cuff use one
    # pose space, including the open-book recovery.
    shoulder=B(q,-21,-55)
    elbow=B(q,-29,-25)
    draw_arm(d,shoulder,elbow,grip,True)
    draw_ledger(d,book,book_angle,q.book_open)
    # Fingers overlap the bottom/spine so the book is never levitating.
    draw_hand(d,grip,q.lean-14,True)
    if q.book_open>.22:
        # The pencil is gripped in the far hand, its tip resting on the
        # right-hand page during the recovery. Draw the fingers over it.
        tip=add(book,rot((8,-4+2*math.sin(q.phase*4)),book_angle))
        end=add(hand,rot((8,-5),book_angle))
        d.line([tip,end],INK,3.7)
        d.line([tip,end],GOLD,2.4)
        draw_hand(d,hand,book_angle+12,False)
    return d.finish(q.fade)


def _body_metrics(fw,fh):
    # Tail and ledger must not determine the collision box or horizontal
    # foot anchor. Approximate the standing torso/legs/head, not its props.
    from ...core.measure import body_metrics_for_box
    return body_metrics_for_box((99,28,174,216),fw,fh)


def render(out_dir: str | Path, **opts):
    from ...authoring.sheet_build import build_sheet
    outputs=build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
                        out_dir=Path(out_dir), frame_size=FRAME_SIZE,
                        auto_crop=False, actor_metadata=ACTOR_METADATA,
                        body_metrics_fn=_body_metrics,
                        animation_key_map={a:a for a,_,_ in ROWS}, sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
