"""Sunk Cost Fallacy, a Neural Cathedral enemy.

An old copper diving helmet, lead boots and a chest the diver refuses to
abandon. One continuous chain follows the same grip and chest fitting in every
pose. Its slack and taut silhouettes convey weight without baked floor shadows.
The chest is an authored melee weapon, not a second simulated rigid body.

The held windup is compatible with a globally sampled telegraph row. The full
attack row is timed to the catalog Lunge, including its startup and recovery.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

TARGET_NAME = "sunk_cost_fallacy"
FRAME_SIZE = (376, 278)
TOP_PAD = 24
GROUND = 232.0
CENTER = 177.0
SUPER = 3
WINDUP_S, ACTIVE_S, RECOVER_S = .80, .32, 1.08
TOTAL_S = WINDUP_S + ACTIVE_S + RECOVER_S
ROWS = [
    ("idle", 12, 110), ("walk", 16, 85), ("notice", 8, 75),
    ("windup", 12, 67), ("attack_side", 44, 50),
    ("hit", 8, 75), ("death", 18, 95),
]
LOOPS = {"idle", "walk", "notice", "windup"}
ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Sunk Cost Fallacy"},
    "body": {"body_plan": "Biped", "body_kind": "Standard", "mass_class": "Heavy",
             "locomotion_hint": "WalkHeavy", "traits": ["enemy", "neural", "cognitive_bias", "diver"]},
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["enemy", "neural", "cognitive_bias", TARGET_NAME],
    "authoring_description": (
        "The sunk cost fallacy is the tendency to continue a course of action because of past, "
        "irrecoverable investments rather than its prospective costs and benefits. This fictional "
        "diver in a historical brass diving helmet refuses to let go of a heavy chest full of "
        "worthless ballast. Its chain and laborious swing are visual metaphors for that attachment."
    ),
    "gameplay_description": (
        "A slow grounded melee enemy that drags a heavy chest. It braces, raises the chest "
        "behind itself, slams it forward and laboriously reels it back. The chest and chain are "
        "visual attachments; ordinary Lunge timing and forward hit geometry control combat."
    ),
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
}
INK = "#282436"
BRASS = "#d1984f"
BRASS_D = "#88502e"
BRASS_L = "#f8d68b"
SUIT = "#416f78"
SUIT_D = "#284552"
SUIT_L = "#75a4a0"
IRON = "#536372"
IRON_D = "#35404e"
IRON_L = "#a6b9bb"
WOOD = "#995b39"
WOOD_D = "#5b3d38"
WOOD_L = "#c38452"
GLASS = "#213b54"
GLASS_L = "#8be3df"


def clamp(t):
    return max(0.0, min(1.0, t))


def smooth(t):
    t = clamp(t)
    return t*t*(3-2*t)


def lerp(a,b,t):
    return a + (b-a)*t


def track(t, keys):
    for (a,x),(b,y) in zip(keys, keys[1:]):
        if t <= b:
            return lerp(x,y,smooth((t-a)/(b-a)))
    return keys[-1][1]


def add(a,b):
    return (a[0]+b[0],a[1]+b[1])


def sub(a,b):
    return (a[0]-b[0],a[1]-b[1])


def mul(a,k):
    return (a[0]*k,a[1]*k)


def rot(p, angle):
    a=math.radians(angle); c,s=math.cos(a),math.sin(a)
    return (c*p[0]-s*p[1],s*p[0]+c*p[1])


def bez(p, n=20):
    result=[p[0]]
    for j in range(0,len(p)-1,3):
        a,b,c,d=p[j:j+4]
        for i in range(1,n+1):
            t=i/n; q=1-t
            result.append(tuple(q**3*a[k]+3*q*q*t*b[k]+3*q*t*t*c[k]+t**3*d[k] for k in (0,1)))
    return result


def ellipse(x,y,rx,ry,angle=0,n=56):
    return [add((x,y),rot((rx*math.cos(t),ry*math.sin(t)),angle))
            for t in (math.tau*i/n for i in range(n))]


class Draw:
    """Supersampled outlined vector shapes in authored frame coordinates."""
    def __init__(self):
        self.im=Image.new('RGBA',tuple(v*SUPER for v in FRAME_SIZE))
        self.d=ImageDraw.Draw(self.im)

    def line(self,p,c=INK,w=1.6,closed=False):
        q=[(x*SUPER,(y+TOP_PAD)*SUPER) for x,y in p]
        if closed: q.append(q[0])
        self.d.line(q,fill=c,width=max(1,round(w*SUPER)),joint='curve')
        if not closed:
            r=w*SUPER/2
            for x,y in (q[0],q[-1]):
                self.d.ellipse((x-r,y-r,x+r,y+r),fill=c)

    def poly(self,p,c,edge=INK,w=2):
        self.d.polygon([(x*SUPER,(y+TOP_PAD)*SUPER) for x,y in p],fill=c)
        if edge: self.line(p,edge,w,True)

    def shape(self,p,c,edge=INK,w=2): self.poly(bez(p),c,edge,w)
    def curve(self,p,c=INK,w=1.5): self.line(bez(p),c,w)
    def oval(self,x,y,rx,ry,c,edge=INK,w=1.5,angle=0):
        self.poly(ellipse(x,y,rx,ry,angle),c,edge,w)

    def tube(self,p,c,w):
        self.line(p,INK,w+3); self.line(p,c,w)

    def finish(self,fade):
        if fade<1:
            self.im.putalpha(self.im.getchannel('A').point(lambda a:round(a*fade)))
        return self.im.resize(FRAME_SIZE,Image.Resampling.LANCZOS)


@dataclass(frozen=True)
class Pose:
    hip: tuple[float,float]
    lean: float
    stride: float
    lift: float
    grip: tuple[float,float]
    chest: tuple[float,float]  # chest handle, not its center
    chest_angle: float
    effort: float
    blink: float
    fall: float
    fade: float
    phase: float


def pose(anim,i,n):
    t=i/(n if anim in LOOPS else max(1,n-1)); p=math.tau*t
    hip=(CENTER,181+1.3*math.sin(p)); lean=9.; stride=0.; lift=0.
    grip=(149.,160.+1.4*math.sin(p)); chest=(81.,185.); ca=-2.
    effort=.14; blink=max(0.,math.cos(p-4.8))**36; fall=0.; fade=1.
    if anim=='walk':
        stride=math.sin(p); lift=1.; lean=14+3*math.cos(p)
        hip=(CENTER+1.8*math.sin(p),181+2.5*math.cos(2*p))
        grip=(148+2.5*math.sin(p),158+2*math.cos(p))
        chest=(79+3.2*math.sin(p-.8),185.0-.8*abs(math.sin(p)))
        ca=-2-2.4*math.sin(p-.8); effort=.64+.13*math.cos(p)
    elif anim=='notice':
        hip=(CENTER,179+.8*math.sin(p)); lean=-3.; grip=(148,158)
        effort=.28; blink=0.
    elif anim=='windup':
        # A held, braced pose: the chest is lifted off the floor and cocked
        # back. No large motion that would restart on the global row clock.
        hip=(CENTER-4,188+1.2*math.sin(p)); lean=-15+1.1*math.sin(p)
        stride=.78; grip=(146,137+1.3*math.sin(p))
        chest=add(grip,rot((76.,0),-154+1.7*math.sin(p)))
        ca=25+2*math.sin(p); effort=.88; blink=0.
    elif anim=='attack_side':
        s=t*TOTAL_S
        hip=(CENTER+track(s,[(0,0),(.8,-4),(.99,6),(1.12,5),(1.45,-2),(2.2,0)]),
             181+track(s,[(0,0),(.8,7),(.99,3),(1.12,7),(1.5,2),(2.2,0)]))
        lean=track(s,[(0,9),(.8,-15),(.98,24),(1.12,24),(1.48,-10),(2.2,9)])
        stride=track(s,[(0,0),(.72,.78),(1.16,.78),(1.55,-.4),(2.2,0)])
        gx=track(s,[(0,149),(.80,146),(.94,198),(1.12,216),(1.43,195),(1.76,155),(2.2,149)])
        gy=track(s,[(0,160),(.80,137),(.94,116),(1.12,158),(1.43,167),(1.76,165),(2.2,160)])
        grip=(gx,gy)
        # The windup's held endpoint and release agree. During release the
        # chest sweeps over the helmet; the head and arm follow through.
        if s < .80:
            h=smooth(s/.80); chest=add(grip,(lerp(-68,76*math.cos(math.radians(-154)),h),lerp(25,76*math.sin(math.radians(-154)),h)))
            ca=lerp(-2,25,h)
        elif s < 1.12:
            a=track(s,[(.80,-154),(.91,-91),(1.02,-24),(1.12,20)])
            chest=add(grip,rot((76.,0),a)); ca=track(s,[(.80,25),(.91,130),(1.02,255),(1.12,360)])
            # Keep the chest sole from passing through the floor.
            chest=(chest[0],min(chest[1],185.))
        else:
            # Chest hits the floor ahead, then is dragged back; a continuous
            # path, with slack returning as the grip comes back to its side.
            chest=(track(s,[(1.12,216+76*math.cos(math.radians(20))),(1.30,282),(1.58,231),(1.90,119),(2.2,81)]),185.)
            ca=track(s,[(1.12,0),(1.26,-3),(1.42,0),(2.2,-2)])
        effort=track(s,[(0,.14),(.8,.88),(1.04,1),(1.45,.85),(2.2,.14)])
        blink=0.
    elif anim=='hit':
        k=math.sin(math.pi*t); hip=(CENTER-7*k,181+5*k); lean=9-23*k
        grip=(149-11*k,160+7*k); chest=(81-4*k,185); ca=-2+5*k
        effort=.45+.45*k; blink=k
    elif anim=='death':
        fall=smooth(t/.72); hip=(CENTER+22*fall,181+27*fall); lean=9+62*fall
        grip=(149+39*fall,160+46*fall); chest=(81+32*fall,185); ca=-2
        effort=.14*(1-fall); blink=smooth(t/.38); fade=1-.64*smooth((t-.80)/.20)
    # Resting corners of the wooden chest must not penetrate the floor.
    # Work from the exact rigid chest orientation, including its bottom rim.
    support=max(rot(v,ca)[1] for v in ((-34,47),(23,47),(35,39),(35,13),(-34,17)))+1
    chest=(chest[0],min(chest[1],GROUND-support))
    # Preserve one finite chain length when a pose exceeds its reach: the
    # chest follows the pull along the floor, rather than stretching links.
    dy=chest[1]-grip[1]; max_dx=math.sqrt(max(0.,79.**2-dy*dy))
    chest=(grip[0]+max(-max_dx,min(max_dx,chest[0]-grip[0])),chest[1])
    return Pose(hip,lean,stride,lift,grip,chest,ca,effort,blink,fall,fade,p)


def limb(d,a,b,c,col,width,highlight=True):
    d.tube([a,b,c],col,width)
    if highlight:
        d.line([add(a,(-width*.19,-1)),add(b,(-width*.19,-1)),add(c,(-width*.19,-1))],SUIT_L,2.0)
    # Ribbed elbow/knee fabric, drawn along the inside rather than as plates.
    u=sub(c,b); m=math.hypot(*u) or 1.; v=(u[0]/m,u[1]/m); normal=(-v[1],v[0])
    for along in (1,5,9):
        q=add(b,mul(v,along)); d.line([add(q,mul(normal,-width*.34)),add(q,mul(normal,width*.34))],SUIT_D,1.5)


def boot(d, x,y, angle,far):
    def P(p): return add((x,y),rot(p,angle))
    col=IRON_D if far else IRON
    d.shape([P(q) for q in [(-12,1),(-15,-5),(-12,-17),(-8,-20),(0,-21),(6,-20),(8,-11),(18,-10),(22,-6),(22,0),(17,2),(-7,3),(-12,1)]],col)
    d.poly([P(q) for q in [(-12,-1),(22,-1),(21,3),(-13,3)]],INK)
    d.poly([P(q) for q in [(-11,-14),(7,-14),(8,-8),(-11,-8)]],BRASS_D,INK,1.4)
    d.line([P((-8,-12)),P((5,-12))],BRASS_L,1.4)
    d.line([P((12,-7)),P((18,-6))],IRON_L,1.7)


def chain_path(a,b,desired=79.):
    """Length-aware slack curve. Pick a sag by bisection, then re-sample by
    arc length so links do not bunch up as the diver straightens the chain.
    A straight taut chain is the limiting case.
    """
    dx,dy=sub(b,a); straight=math.hypot(dx,dy)
    def sample(sag):
        return [(a[0]+dx*t,a[1]+dy*t+4*sag*t*(1-t)) for t in (i/80 for i in range(81))]
    def length(points): return sum(math.dist(x,y) for x,y in zip(points,points[1:]))
    # Find the maximum sag whose entire curve stays above the floor; the
    # endpoints need not be at the same height. A slack chain can fold back
    # upon itself when the chest is directly below the hand.
    lo,hi=0.,150.
    for _ in range(16):
        mid=(lo+hi)/2
        if max(y for _,y in sample(mid))>GROUND-4: hi=mid
        else: lo=mid
    lo,hi=0.,lo
    for _ in range(16):
        mid=(lo+hi)/2
        if length(sample(mid))<max(desired,straight): lo=mid
        else: hi=mid
    return sample((lo+hi)/2)


def chain(d,a,b):
    pts=chain_path(a,b); lengths=[0.]
    for x,y in zip(pts,pts[1:]): lengths.append(lengths[-1]+math.dist(x,y))
    total=lengths[-1]
    # 12 interleaved links, with fixed spacing along the slack curve. On
    # edge-on links the aperture is still visible at game scale.
    j=1
    for k in range(12):
        s=total*k/11
        while j<len(lengths)-1 and lengths[j]<s: j+=1
        f=(s-lengths[j-1])/max(.00001,lengths[j]-lengths[j-1]); p=add(pts[j-1],mul(sub(pts[j],pts[j-1]),f))
        dx,dy=sub(pts[j],pts[j-1]); a0=math.degrees(math.atan2(dy,dx))
        outline=ellipse(*p,4.9,2.8 if k%2==0 else 1.65,a0,n=20)
        d.line(outline,INK,3.6,True); d.line(outline,IRON_L if k%2==0 else IRON,1.75,True)


def treasure(d,handle,angle,effort):
    """A banded sea chest, pitched around its real carrying ring. Its solid
    contents are ballast, not a particle effect. At rest the base is flat.
    """
    def P(q): return add(handle,rot(q,angle))
    def poly(q,c,edge=INK,w=2): d.poly([P(x) for x in q],c,edge,w)
    def shape(q,c,edge=INK,w=2): d.shape([P(x) for x in q],c,edge,w)
    def line(q,c=INK,w=1.5): d.line([P(x) for x in q],c,w)
    def oval(x,y,rx,ry,c,edge=INK,w=1.3):
        d.poly([P(v) for v in ellipse(x,y,rx,ry)],c,edge,w)
    # Foreshortened side wall and rounded lid, with distinct silhouettes.
    poly([(-34,16),(-24,9),(-24,41),(-34,47)],WOOD_D)
    poly([(-34,47),(23,47),(35,39),(35,13),(23,19),(-34,17)],WOOD)
    poly([(23,19),(35,13),(35,39),(23,47)],WOOD_D)
    shape([(-34,17),(-34,4),(-24,1),(-15,1),(1,0),(19,0),(27,4),(33,8),(35,11),(35,16),(22,23),(-16,23),(-34,17)],WOOD_L)
    poly([(23,9),(35,12),(35,16),(23,23),(23,17)],WOOD_D,INK,1.3)
    line([(-34,20),(23,25),(35,17)],INK,2.5)
    line([(-31,30),(22,32)],WOOD_D,1.3); line([(-31,40),(22,41)],WOOD_D,1.3)
    line([(-30,27),(-10,28),(5,26)],WOOD_L,1.4); line([(3,37),(14,35),(20,36)],WOOD_L,1.3)
    for x in (-25,13):
        poly([(x,2),(x+7,3),(x+7,47),(x,47)],BRASS_D)
        line([(x+2,5),(x+2,44)],BRASS_L,1.6)
        for y in (9,23,39): oval(x+3.5,y,1.65,1.65,BRASS_L,INK,.8)
    poly([(-8,20),(3,20),(4,33),(-8,33)],BRASS)
    oval(-2,26,2.1,2.6,INK,None); line([(-2,27),(-2,30)],INK,1.5)
    # A tiny sea-star and corrosion spots are attached to the wood/straps.
    star=[]
    for k in range(10):
        th=-math.pi/2+k*math.pi/5; r=6 if k%2==0 else 2.5
        star.append((3+math.cos(th)*r,39+math.sin(th)*r))
    poly(star,'#c57667',INK,.9)
    for x,y in [(-19,7),(-17,8),(-18,34),(28,34),(-11,44)]: oval(x,y,1.3,.9,'#72a19a',None)
    # The ring has a real aperture; chain terminates at its center.
    ring=[P(q) for q in ellipse(0,0,5.0,5.5)]
    d.line(ring,INK,4,True); d.line(ring,BRASS_L,2,True)


def diver(d,q):
    hip=q.hip; lean=q.lean; ph=q.phase
    def B(x,y): return add(hip,rot((x,y),lean))
    head=B(0,-74); shoulder=B(4,-38)
    # Foot motion uses a stance half-cycle and an airborne return half-cycle.
    # Keep the feet anchored in the idle/telegraph poses.
    for side,far in ((-1,True),(1,False)):
        dx=side*(7+13*q.stride)
        up=q.lift*max(0,side*math.cos(ph))*10
        x=CENTER+dx+q.fall*(17 if far else 30)
        angle=-12*side*math.cos(ph)*q.lift if q.lift else 0
        sole=max(rot(v,angle)[1] for v in ((-13,3),(21,3),(22,0),(-15,-5)))+1
        y=GROUND-sole-up
        knee=(lerp(hip[0]+side*7,x,.53)+5*(1-q.fall),lerp(hip[1]+4,y-13,.54))
        limb(d,B(side*8,0),knee,(x,y-13),SUIT_D if far else SUIT,14,not far)
        boot(d,x,y,angle,far)
    # Far arm follows the body's tilt, and braces against the pull.
    fa=B(12,-40); fe=B(23,-21); fh=B(27+7*q.effort,-15)
    limb(d,fa,fe,fh,SUIT_D,13,False)
    d.oval(*fh,8,7,IRON_D,INK,1.8)
    # Twin air bottle and straps behind the torso.
    def poly(pts,col,edge=INK,w=2): d.poly([B(*v) for v in pts],col,edge,w)
    def shape(pts,col,edge=INK,w=2): d.shape([B(*v) for v in pts],col,edge,w)
    def line(pts,col=INK,w=1.5): d.line([B(*v) for v in pts],col,w)
    def oval(x,y,rx,ry,col,edge=INK,w=1.5): d.poly([B(*v) for v in ellipse(x,y,rx,ry)],col,edge,w)
    shape([(-28,-13),(-39,-15),(-39,-47),(-31,-52),(-23,-58),(-16,-52),(-17,-41),(-17,-19),(-19,-11),(-28,-13)],IRON_D)
    line([(-33,-42),(-33,-22)],IRON_L,2.5)
    poly([(-38,-38),(-17,-38),(-17,-32),(-38,-32)],BRASS_D)
    # Canvas torso with padded shoulders, seam, and brass belt.
    shape([(-20,2),(-26,-5),(-26,-29),(-25,-39),(-23,-46),(-12,-49),(0,-49),(15,-49),(24,-41),(25,-31),(25,-12),(20,-2),(17,4),(8,8),(-11,8),(-20,2)],SUIT)
    shape([(-20,2),(-25,-6),(-25,-29),(-24,-38),(-18,-44),(-12,-44),(-10,-40),(-14,-20),(-15,-6),(-12,7),(-17,7),(-18,5),(-20,2)],SUIT_D,None)
    line([(9,-37),(13,-24),(12,-11)],SUIT_L,3)
    line([(-4,-40),(-2,-24),(-3,-11)],SUIT_D,1.8)
    for y in (-29,-21,-13): line([(-6,y),(-3,y)],SUIT_L,1.1)
    poly([(-24,-10),(22,-10),(20,0),(-21,0)],BRASS_D)
    poly([(1,-10),(12,-10),(12,0),(1,0)],BRASS)
    oval(6.5,-5,2,2,INK,None)
    # Chest gauge and regulator hose. Tube follows the body, not the frame.
    d.tube([B(-27,-43),B(-32,-62),B(-25,-70),B(-18,-62)],IRON_D,5)
    oval(15,-28,7,7,BRASS)
    oval(15,-28,4.6,4.6,'#efe5c6',INK,1)
    line([(15,-28),(18,-30)],INK,1.5)
    # helmet flange, brass shell, top cap and darker far side.
    oval(0,-48,26,9,BRASS_D)
    oval(0,-53,28,8,BRASS)
    line([(-24,-53),(-13,-58),(13,-58),(24,-53)],BRASS_L,1.7)
    oval(0,-76,34,35,BRASS)
    shape([(-28,-95),(-41,-80),(-31,-55),(-17,-51),(-5,-45),(8,-45),(18,-49),(0,-49),(-18,-66),(-18,-83),(-18,-97),(-9,-105),(6,-110),(-11,-112),(-20,-105),(-28,-95)],BRASS_D,None)
    d.curve([B(-20,-99),B(-13,-108),B(1,-111),B(12,-106)],BRASS_L,3)
    # Side port and top air-valve.
    oval(-23,-76,8.5,10,BRASS_D)
    oval(-23,-76,5,6.5,GLASS)
    line([(-26,-79),(-23,-82)],GLASS_L,1.4)
    poly([(-11,-110),(-10,-118),(1,-118),(3,-110)],BRASS_D)
    oval(-5,-117,7,3,BRASS_L)
    # Large right-facing glass port; the eye is actually visible behind it.
    oval(11,-77,25.5,25,BRASS_D,INK,2.2)
    oval(12,-77,22.2,21.8,BRASS_L,INK,1.5)
    oval(13,-77,18.4,18.6,GLASS,INK,1.7)
    oval(15,-77,15.2,15.6,'#34586a',None)
    for th in (0,math.pi/2,math.pi,math.pi*1.5,math.pi*.25,math.pi*1.25):
        x=12+22.6*math.cos(th); y=-77+22.2*math.sin(th)
        oval(x,y,1.5,1.5,BRASS_D,INK,.6)
    # A tired pair of eyes (different sizes for the 3/4 view), strained
    # brows, and a small mouth. The window highlight never hides the face.
    for ex,ey,rx in ((9,-79,5.4),(21,-79,4.4)):
        ry=4.8*(1-.92*q.blink)
        oval(ex,ey,rx,max(.6,ry),'#f2ead4',INK,1.0)
        if q.blink<.7:
            oval(ex+1.7,ey+.2,2.0,max(.55,2.9*(1-q.blink)),INK,None)
        if q.effort>.2:
            line([(ex-rx,ey-6-q.effort*1.3),(ex+rx,ey-5+q.effort*2.5)],INK,2.0)
    if q.effort>.72:
        oval(16,-68,5.6,2.7,INK,None)
        line([(12,-69),(20,-69)],'#f2ead4',1.4)
    else:
        line([(12,-67),(16,-68.5),(20,-67)],INK,1.7)
    d.curve([B(-1,-86),B(1,-92),B(7,-94),B(11,-94)],GLASS_L,2.1)
    line([(24,-89),(27,-86)],'#c8f4e9',1.5)
    # Near elbow and hand. All chain attachment endpoints use the same grip.
    a=B(-14,-39); g=q.grip
    # Hand-keyed bend; smooth transition from the rear pull into the overhand
    # throw. This is a pose control, not a private general IK implementation.
    bend=clamp((g[0]-a[0]+8)/50)
    e=(lerp(a[0]-12,a[0]+17,bend),lerp(a[1]+24,a[1]-17,bend))
    limb(d,a,e,g,SUIT,15)
    d.oval(*a,9,10,SUIT_L,INK,1.5)
    d.oval(*g,9,8,IRON,INK,1.8)
    d.line([add(g,(-4,-4)),add(g,(3,-4))],IRON_L,1.7)
    for k in (-3,1,5): d.line([add(g,(k,0)),add(g,(k,4))],IRON_D,1.3)


def _render_frame(anim,i,n):
    q=pose(anim,i,n); d=Draw()
    # Chest and chain behind the body when trailing, ahead of it on impact.
    # The layer changes only on the overhead crossing, or while the chest is
    # already in front of the actor on the ground. Its grip stays occluded by
    # the glove. No cast or contact shadows are baked into the image.
    ahead=(q.chest[0]>CENTER-12 or (anim=='attack_side' and i/(n-1)*TOTAL_S>1.12 and q.chest[0]>CENTER-48))
    if not ahead:
        treasure(d,q.chest,q.chest_angle,q.effort); chain(d,q.grip,q.chest); diver(d,q)
    else:
        diver(d,q); chain(d,q.grip,q.chest); treasure(d,q.chest,q.chest_angle,q.effort)
        # Glove covers the first chain link even when it is drawn in front.
        d.oval(*q.grip,7.6,6.7,IRON,INK,1.5)
        d.line([add(q.grip,(-4,-3)),add(q.grip,(3,-3))],IRON_L,1.5)
    return d.finish(q.fade)


def _body_metrics(fw,fh):
    # The long chest swing is presentation, not a wider physics body. The
    # authored feet anchor is independent of the chest's horizontal extent.
    from ...core.measure import body_metrics_for_box
    return body_metrics_for_box((137,60+TOP_PAD,218,233+TOP_PAD),fw,fh)


def render(out_dir: str | Path, **opts):
    from ...authoring.sheet_build import build_sheet
    outputs=build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
                        out_dir=Path(out_dir), frame_size=FRAME_SIZE,
                        auto_crop=False, actor_metadata=ACTOR_METADATA,
                        body_metrics_fn=_body_metrics,
                        animation_key_map={a:a for a,_,_ in ROWS}, sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
