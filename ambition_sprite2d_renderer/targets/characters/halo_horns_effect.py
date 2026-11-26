"""Halo and Horns Effect, a single Neural Dimension enemy.

The same two metal arcs form the halo and the horns. Their sampled centerlines
and cross sections interpolate continuously; there is no second crown sprite,
visibility swap, or separate weapon. Art faces right in local actor space.

The pinned windup row must be a held pose (its clock can be global). The
attack row uses progress over the *entire* lunge, not just its active phase.
See Ambition's docs/planning/game/enemy-patterns.md. Keep the durations below
in sync with the halo_horns_charge action set.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

TARGET_NAME = "halo_horns_effect"
FRAME_SIZE = (224, 208)
# Full attack progress: .60 seconds startup, .24 active, .72 recovery.
WINDUP_S, ACTIVE_S, RECOVER_S = 0.60, 0.24, 0.72
TOTAL_S = WINDUP_S + ACTIVE_S + RECOVER_S
ROWS = [
    ("idle", 12, 95), ("walk", 12, 75), ("notice", 8, 70),
    ("windup", 12, 60), ("attack_side", 32, 49),
    ("hit", 8, 60), ("death", 14, 85),
]
LOOPS = {"idle", "walk", "notice", "windup"}
SUPER = 3
INK = "#291a35"

ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Halo and Horns Effect"},
    "body": {"body_plan": "Blob", "body_kind": "Floating", "mass_class": "Light",
             "locomotion_hint": "Float", "traits": ["enemy", "neural", "cognitive_bias", "floating"]},
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["enemy", "neural", "cognitive_bias", TARGET_NAME],
    "authoring_description": (
        "The halo and horns effects are positive and negative spillovers from an overall "
        "impression or individual trait to judgments of other attributes. This fictional "
        "neural cherub wears a gilded crown that splits and curls into red horns. "
        "Its feathers spread into bat wings, and an arrow-tipped tail unfurls. "
        "The same creature returns to its halo form after the charge."
    ),
    "gameplay_description": (
        "A hovering melee enemy. It exposes its fangs and holds a devil pose before "
        "it lunges horns first. The devil form stays visible as it slows down."
    ),
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
}


def clamp(t):
    return max(0., min(1., t))


def smooth(t):
    t = clamp(t)
    return t*t*(3-2*t)


def mix(a, b, t):
    return a+(b-a)*t


def track(t, keys):
    for (a, x), (b, y) in zip(keys, keys[1:]):
        if t <= b:
            return mix(x, y, smooth((t-a)/(b-a)))
    return keys[-1][1]


def bez(points, n=28):
    out = [points[0]]
    for j in range(0, len(points)-1, 3):
        a, b, c, d = points[j:j+4]
        for i in range(1, n+1):
            t = i/n; q = 1-t
            out.append(tuple(q**3*a[k]+3*q*q*t*b[k]+3*q*t*t*c[k]+t**3*d[k] for k in (0, 1)))
    return out


def oval_points(x, y, rx, ry, angle=0, n=64):
    a = math.radians(angle); c, s = math.cos(a), math.sin(a)
    return [(x+rx*math.cos(t)*c-ry*math.sin(t)*s,
             y+rx*math.cos(t)*s+ry*math.sin(t)*c)
            for t in (math.tau*i/n for i in range(n))]


def rgb(h):
    return tuple(int(h[i:i+2], 16) for i in (1,3,5)) if isinstance(h, str) else h[:3]


def tint(a, b, t):
    return tuple(round(mix(x,y,t)) for x,y in zip(rgb(a), rgb(b)))+(255,)


class Painter:
    def __init__(self, x, y, tilt, sx, sy):
        size = tuple(v*SUPER for v in FRAME_SIZE)
        self.img = Image.new("RGBA", size)
        self.glow = Image.new("RGBA", size)
        self.d = ImageDraw.Draw(self.img)
        self.g = ImageDraw.Draw(self.glow)
        self.x, self.y, self.sx, self.sy = x, y, sx, sy
        self.c, self.s = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))

    def pts(self, pts):
        return [((self.x+self.c*x*self.sx-self.s*y*self.sy)*SUPER,
                 (self.y+self.s*x*self.sx+self.c*y*self.sy)*SUPER) for x,y in pts]

    def line(self, pts, color=INK, w=1.6, *, closed=False, glow=False):
        p = self.pts(pts)
        if closed: p += [p[0]]
        d = self.g if glow else self.d
        d.line(p, fill=color, width=max(1, round(w*SUPER)), joint="curve")
        if not closed:
            r = w*SUPER/2
            for x,y in (p[0],p[-1]): d.ellipse((x-r,y-r,x+r,y+r),fill=color)

    def poly(self, pts, color, edge=INK, w=1.8):
        self.d.polygon(self.pts(pts),fill=color)
        if edge: self.line(pts,edge,w,closed=True)

    def shape(self, pts, color, edge=INK, w=1.8):
        self.poly(bez(pts),color,edge,w)

    def curve(self, pts, color=INK, w=1.5):
        self.line(bez(pts),color,w)

    def oval(self,x,y,rx,ry,color,edge=INK,w=1.5,angle=0):
        self.poly(oval_points(x,y,rx,ry,angle),color,edge,w)

    def limb(self, pts, color, w=7):
        self.line(pts, INK, w+3)
        self.line(pts, color, w)

    def finish(self, fade):
        out = self.glow.filter(ImageFilter.GaussianBlur(2.1*SUPER))
        out.alpha_composite(self.img)
        if fade < 1:
            out.putalpha(out.getchannel("A").point(lambda v: round(v*fade)))
        return out.resize(FRAME_SIZE,Image.Resampling.LANCZOS)


def pose(anim, i, n):
    t = i/(n if anim in LOOPS else max(1,n-1))
    p = math.tau*t
    x,y,tilt,sx,sy = 108.,112.+2.7*math.sin(p),-2.,1.,1.
    m,anger,flap,reach,ring_tilt,fade = 0.,0.,7*math.sin(p),0.,-8+3*math.sin(p),1.
    blink = max(0., math.cos(p-4.6))**28
    if anim == "walk":
        y = 112+2.5*math.sin(2*p); tilt=9+2*math.sin(p)
        flap=18*math.sin(p); reach=.25; ring_tilt=-8+4*math.sin(p)
    elif anim == "notice":
        # Held global-clock row: a raised, startled pose, not a repeating ramp.
        y=108+1.2*math.sin(p); tilt=-7; sy=1.04; blink=0
        anger=.12; flap=-7+4*math.sin(p); ring_tilt=-13+4*math.sin(p)
    elif anim == "windup":
        # Hold the threat pose. The windup clock can start on any frame.
        m=.78+.024*math.sin(p); anger=.86; x=103; y=112+1.3*math.sin(p)
        tilt=-11+1.6*math.sin(p); sx=.94; sy=1.06
        flap=-22+4*math.sin(p); reach=-.65; ring_tilt=-8; blink=0
    elif anim == "attack_side":
        # Match the held windup at release. Keep the horns through the first
        # 0.44 seconds of recovery, then close the ring as the body settles.
        s=t*TOTAL_S
        hold_end=WINDUP_S+ACTIVE_S+.44
        m=track(s,[(0,0),(.24,.22),(.46,.75),(WINDUP_S,.78),(.68,1),(hold_end,1),(TOTAL_S,0)])
        anger=track(s,[(0,0),(.29,.32),(WINDUP_S,.86),(.68,1),(.94,1),(hold_end,.83),(TOTAL_S,0)])
        tilt=track(s,[(0,-2),(WINDUP_S,-11),(.71,27),(.86,19),(1.06,0),(1.22,5),(TOTAL_S,-2)])
        x=108+track(s,[(0,0),(WINDUP_S,-5),(.70,12),(.84,10),(1.12,0),(TOTAL_S,0)])
        y=112+track(s,[(0,0),(WINDUP_S,0),(.71,-5),(.88,4),(1.12,1),(TOTAL_S,0)])
        sx=track(s,[(0,1),(WINDUP_S,.94),(.71,1.13),(.91,1.02),(TOTAL_S,1)])
        sy=track(s,[(0,1),(WINDUP_S,1.06),(.71,.89),(.91,.99),(TOTAL_S,1)])
        flap=track(s,[(0,0),(WINDUP_S,-22),(.72,22),(.89,11),(1.10,-13),(hold_end,-7),(TOTAL_S,0)])
        reach=track(s,[(0,0),(WINDUP_S,-.65),(.70,-1),(.86,-.8),(1.09,.24),(hold_end,.12),(TOTAL_S,0)])
        ring_tilt=-8; blink=0
    elif anim == "hit":
        k=math.sin(math.pi*t); x-=8*k; y+=3*k; tilt=-2-18*k
        sx=1+.10*k; sy=1-.12*k; m=.18*k; anger=.3*k
        flap=23*k; reach=.9*k; ring_tilt=-8+19*k; blink=k
    elif anim == "death":
        k=smooth(t); x-=6*k; y+=22*k; tilt=-2+58*k; sx=1+.10*k; sy=1-.25*k
        m=track(t,[(0,0),(.25,.70),(.60,.42),(1,0)]); anger=.3*(1-k)
        flap=-18*k; reach=.6*k; ring_tilt=-8-35*k; blink=smooth(t/.30)
        fade=1-.62*smooth((t-.66)/.34)
    return x,y,tilt,sx,sy,m,anger,flap,reach,ring_tilt,blink,fade


def ring_arc(side, angle, n=57):
    """One half from the front center seam to the back center seam."""
    a=math.radians(angle); c,s=math.cos(a),math.sin(a)
    pts=[]
    for j in range(n):
        theta=math.pi/2-side*math.pi*j/(n-1)
        x,y=34*math.cos(theta),10*math.sin(theta)
        pts.append((3+x*c-y*s,-64+x*s+y*c))
    return pts


def horn_arc(side):
    # Both horns use the same sample count and the same two original arcs.
    # The near horn is larger and rooted on the right brow.
    if side == 1:
        return bez([(19,-35),(35,-33),(51,-42),(57,-55),
                    (66,-70),(59,-83),(46,-86)],28)
    return bez([(-18,-36),(-31,-34),(-42,-44),(-47,-53),
                (-54,-64),(-49,-76),(-39,-80)],28)


def crown_geometry(side, m, angle):
    """Matched centerline samples and smoothly changing cross-section.

    Endpoints of the arc spread in opposite directions from the two seams;
    the root thickens and the other end tapers into a horn tip. No crossfade.
    """
    old, new = ring_arc(side,angle), horn_arc(side)
    pts=[]; radii=[]
    # m itself is eased in the pose tracks; do not ease it a second time.
    for i, (a,b) in enumerate(zip(old,new)):
        u=i/(len(old)-1)
        # A slight sideways flex keeps the two opening arcs visibly separated.
        bow=side*4*math.sin(math.pi*m)*math.sin(math.pi*u)
        pts.append((mix(a[0],b[0],m)+bow,mix(a[1],b[1],m)))
        radii.append(mix(3.0, .22+8.8*(1-u)**.88, m))
    return pts,radii


def normals(pts):
    result=[]
    for i in range(len(pts)):
        ax,ay=pts[max(0,i-1)]; bx,by=pts[min(len(pts)-1,i+1)]
        dx,dy=bx-ax,by-ay; l=math.hypot(dx,dy) or 1
        result.append((-dy/l,dx/l))
    return result


def ribbon(p, points, ns, radii, low, high, color, edge=None, w=1):
    def boundary(f):
        return [(x+nx*r*f,y+ny*r*f) for (x,y),(nx,ny),r in zip(points,ns,radii)]
    p.poly(boundary(low)+boundary(high)[::-1],color,edge,w)


def draw_horn(p, side, m, angle, devil):
    pts,radii=crown_geometry(side,m,angle); ns=normals(pts)
    glow=tint('#ffad40','#ff3635',devil)
    p.line(pts,(*glow[:3],round(mix(mix(90,32,m),100,devil))),8.5,glow=True)
    ribbon(p,pts,ns,radii,-1,1,tint(tint('#e6a542','#a95b38',m),'#b22439',devil),INK,1.4)
    ribbon(p,pts,ns,radii,-.95,-.35,tint(tint('#a66b29','#70334b',m),'#641d37',devil))
    ribbon(p,pts,ns,radii,-.30,.72,tint(tint('#ffe7a1','#e3a85c',m),'#ee413e',devil))
    ribbon(p,pts,ns,radii,.12,.50,tint(tint('#fff7d4','#ffdb90',m),'#ff9172',devil))
    # Ring seam becomes a sculpted horn root, with ridges growing out of the
    # same surface. Fine ridges are only inked once there is enough material.
    if m>.32:
        for j in (7,14,22,30,38):
            x,y=pts[j]; nx,ny=ns[j]; r=radii[j]
            p.line([(x-nx*r*.75,y-ny*r*.75),(x-nx*r*.1,y-ny*r*.1),
                    (x+nx*r*.76,y+ny*r*.76)],tint(tint('#ebc27a','#92553e',m),'#961b35',devil),.55+.35*m)
    if m>.64:
        # The widened root acquires a sculpted, dark bronze collar.
        # Its highlights are on the same material strip, not a second horn.
        k=smooth((m-.64)/.36)
        for j in (2,5):
            x,y=pts[j]; nx,ny=ns[j]; r=radii[j]
            p.line([(x-nx*r*.84,y-ny*r*.84),(x+nx*r*.84,y+ny*r*.84)],
                   tint(tint('#c58a45','#784057',k),'#681b32',devil),.9+k*.55)
        x,y=pts[3]; nx,ny=ns[3]; r=radii[3]
        p.line([(x-nx*r*.7,y-ny*r*.7),(x+nx*r*.7,y+ny*r*.7)],tint('#f6ce7d','#ff8268',devil),.8+k*.55)


def intact_crown(p, angle):
    pts=oval_points(3,-64,34,10,angle,112)
    p.line(pts,(255,194,87,130),10,closed=True,glow=True)
    p.line(pts,'#442942',8,closed=True)
    p.line(pts,'#c58933',6.0,closed=True)
    p.line(pts,'#f4cd76',4.5,closed=True)
    p.line(pts,'#fff3c1',2.3,closed=True)
    # Reflected light occupies only one part of the polished ring.
    p.line(pts[48:82],'#fffdf0',1.8)
    for x,y in (pts[13],pts[67]):
        p.oval(x,y,1.35,1.35,'#ffffff',None)


def feather(p, root, length, angle, dark, bright):
    c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle)); x,y=root
    def q(pt):
        u,v=pt;return (x+u*c-v*s,y+u*s+v*c)
    l=length; w=l*.21
    p.shape([q(k) for k in [(0,0),(l*.22,-w),(l*.72,-w),(l,0),
                              (l*.72,w*.55),(l*.20,w*.78),(0,0)]],bright,w=1.4)
    p.shape([q(k) for k in [(3,0),(l*.28,w*.52),(l*.71,w*.50),(l*.91,0),
                              (l*.62,w*.13),(l*.24,w*.10),(3,0)]],dark,None)
    p.curve([q(k) for k in [(4,0),(l*.36,-1),(l*.64,1),(l*.86,0)]],dark,1.1)


def bat_wing(p, root, flap, devil, near):
    angle = math.radians(-flap * .65 + (0 if near else 14))
    c, s = math.cos(angle), math.sin(angle)
    span = devil * (1 if near else .76)

    def wing(points):
        return [(root[0] + span*(x*c-y*s), root[1] + span*(x*s+y*c)) for x, y in points]

    p.shape(wing([(2,2),(-8,-18),(-30,-34),(-49,-32),
                  (-43,-24),(-47,-15),(-61,-8),(-48,-10),(-39,1),(-49,13),
                  (-40,8),(-29,11),(-32,22),(-24,17),(-11,18),(2,2)]),
            tint('#c691a6' if near else '#9f799c', '#a83848' if near else '#6b2948', devil), w=1.6)
    p.curve(wing([(1,2),(-13,-12),(-37,-27),(-49,-32)]), '#ee7669' if near else '#bc5266', 1.6)
    for tip in [(-60,-8),(-48,12),(-32,21)]:
        p.curve(wing([(1,2),(-12,-10),(-27,tip[1]-7),tip]), '#67213e', 1.25)


def mantle(p, near, flap, anger, devil):
    root=(-27,6) if near else (-27,-2)
    if devil < .97:
        for j in range(4):
            angle=196-12*j+flap*.8-12*anger+(5 if near else -9)
            feather(p,(root[0]+j*2,root[1]+j*2.8),(31+3*j)*(1-.84*devil),angle,
                    tint('#b8a0c2' if near else '#867594', '#852943', devil),
                    tint(tint('#eee4e5','#c6a4b4',anger) if near else '#b9a6c6', '#bd4e57', devil))
    if devil > .08:
        bat_wing(p, root, flap, devil, near)
    p.oval(root[0]+4,root[1]+1,10,9,tint('#e2cddc' if near else '#aa93b3','#ba4954',devil),angle=-20)
    p.curve([(root[0]-1,root[1]-5),(root[0]-7,root[1]),(root[0]-2,root[1]+5),(root[0]+6,root[1]+7)],
            tint('#ac8baa','#78273f',devil),1.2)


def eye(p, x, y, rx, anger, blink, devil, far=False):
    # Large, friendly eyes acquire a sharp upper lid, without swapping faces.
    ry=rx*(.92-.29*anger)*(1-.94*blink)
    if ry<1.3:
        p.curve([(x-rx,y),(x-rx*.3,y+2),(x+rx*.4,y+2),(x+rx,y-.5)],'#573450',1.8)
        return
    lean=3.8*anger*(1 if far else -1)
    top=[(x-rx,y+lean*.5),(x-rx*.48,y-ry-lean),(x+rx*.42,y-ry+lean),(x+rx,y+lean*.2)]
    bottom=[(x+rx,y+lean*.2),(x+rx*.52,y+ry),(x-rx*.54,y+ry),(x-rx,y+lean*.5)]
    p.shape(top+bottom[1:],tint('#fff4e5','#ffcf75',devil),tint('#65415a','#501c32',devil),1.35+devil*.6)
    px=x+rx*.21; py=y+.3
    p.oval(px,py,rx*.43,min(ry*.74,rx*.61),tint(tint('#735879','#9a414a',anger),'#d65b30',devil),None)
    p.oval(px+.3,py,rx*(.23-.10*devil),min(ry*(.55+.22*devil),rx*.48),'#352038',None)
    p.oval(px-rx*.15,py-ry*.23,rx*.13,max(.35,ry*.16),'#ffffff',None)
    if anger>.15:
        p.curve([(x-rx-.5,y-ry*.56-lean*.3),(x-rx*.38,y-ry-lean),(x+rx*.52,y-ry+lean),(x+rx+1,y-ry*.30+lean*.4)],'#704056',1.1+anger*.9)
    # The brow changes continuously from a soft arch to an inward slant.
    p.curve([(x-rx*.78,y-ry-2-lean*.6),(x-rx*.3,y-ry-5-lean),
             (x+rx*.38,y-ry-5+lean),(x+rx*.8,y-ry-2+lean*.6)],
            tint(tint('#cfa99b','#8a4960',anger),'#681c2e',devil),1.2+anger*.45+devil*1.2)


def pointed_tail(p, devil, phase):
    root=(-16,26)
    curl=5*math.sin(phase)
    def tail(points):
        return [(root[0]+x*devil, root[1]+y*devil) for x, y in points]

    shaft=tail([(0,0),(-13,23),(-40,21),(-50,13+curl),
                (-59,6+curl),(-61,-6+curl),(-57,-11+curl)])
    p.curve(shaft,INK,2+4*devil)
    p.curve(shaft,'#c54448',4*devil)
    p.poly(tail([(-57,-10+curl),(-64,-10+curl),(-55,-25+curl),(-49,-9+curl)]),'#e95850',INK,1.2)


def body(p, anger, devil, flap, reach, blink, phase, death):
    if devil > .12:
        pointed_tail(p, devil, phase)
    mantle(p,False,flap,anger,devil)
    # Four short nerve tendrils. They hang from the creature itself, not from
    # a shadow or environment-dependent ground plane.
    for j in range(4):
        x=-18+11*j; wave=3*math.sin(phase+j*.87)*(1-death)
        p.limb([(x,22),(x-3,33),(x+wave,39-2*abs(j-1.5))],'#9b4b78',5.7)
        p.oval(x+wave,39-2*abs(j-1.5),3.5,4.2,'#e69aa9',INK,1.15)
        p.oval(x+wave-1,37-2*abs(j-1.5),1,1.2,'#ffd1c5',None)
    # Compact pear-shaped neural core: dark contour, flesh volume, folds.
    p.shape([(-31,-5),(-42,11),(-34,33),(-12,35),(6,42),(31,30),(34,11),
             (37,-9),(21,-27),(0,-26),(-15,-27),(-27,-18),(-31,-5)],tint('#a9517d','#91223b',devil),w=2.1)
    p.shape([(-28,3),(-31,-10),(-13,-21),(7,-18),(24,-18),(29,4),(23,19),
             (17,33),(-14,33),(-25,24),(-32,17),(-33,10),(-28,3)],tint('#d884a0','#cb373e',devil),None)
    p.shape([(-32,15),(-27,29),(-13,32),(4,32),(19,34),(27,25),(31,18),
             (22,39),(-15,43),(-30,27),(-34,23),(-34,18),(-32,15)],tint('#8b3e71','#7e213a',devil),None)
    for pts in [[(-25,2),(-19,14),(-8,-1),(-4,9)], [(-20,21),(-14,30),(-8,19),(0,24)],
                [(2,8),(5,18),(15,14),(20,20)], [(-5,31),(2,28),(4,23),(10,25)]]:
        p.curve(pts,tint('#964671','#9b2539',devil),2.0)
    mantle(p,True,flap,anger,devil)
    # Gilded shoulder / collar and exposed neck tissue anchor the face.
    p.shape([(-24,-12),(-18,-22),(14,-23),(29,-13),(36,-6),(29,10),(15,15),
             (-4,21),(-25,12),(-28,3),(-29,-3),(-28,-9),(-24,-12)],tint('#a9663f','#8b2940',devil),w=2)
    p.shape([(-23,-12),(-12,-19),(13,-20),(28,-11),(31,-4),(25,6),(14,10),
             (-3,16),(-22,7),(-24,1),(-27,-3),(-26,-9),(-23,-12)],tint('#eac88d','#e46551',devil),None)
    p.curve([(-25,-1),(-11,13),(15,17),(29,-4)],tint('#fff0c7','#f9946e',devil),1.5)
    # A continuous organic/chitin head rather than a removable mask.
    # Horn roots end on the upper brow, behind its brow ridges.
    p.shape([(-25,-22),(-28,-40),(-12,-48),(6,-45),(23,-48),(36,-34),(37,-17),
             (38,-4),(24,8),(8,11),(-7,15),(-25,4),(-29,-8),(-30,-15),(-28,-19),(-25,-22)],
            tint(tint('#f5e6d7','#e5adba',anger*.65),'#ed514b',devil),w=2.2)
    p.shape([(19,-43),(33,-38),(38,-27),(36,-15),(37,-5),(27,6),(12,10),
             (24,1),(27,-10),(25,-19),(26,-28),(24,-37),(19,-43)],
            tint(tint('#d3b8c8','#be748d',anger*.8),'#af3044',devil),None)
    p.shape([(-23,-27),(-24,-37),(-12,-43),(2,-43),(5,-39),(-8,-34),(-14,-27),
             (-18,-24),(-21,-23),(-23,-27)],tint('#fff6e4','#ff8068',devil),None)
    # Tiny gilded diamond and seams that echo the ring's material.
    p.poly([(-3,-37),(2,-43),(7,-37),(2,-31)],tint('#c58a43','#ac3042',devil),tint('#9d6549','#75273b',devil),1.0)
    p.poly([(0,-37),(2,-40),(4,-37),(2,-34)],tint('#ffe6aa','#ffa56e',devil),None)
    p.curve([(-24,-20),(-24,-31),(-17,-36),(-10,-36)],tint('#d1a58a','#d44949',devil),1.3)
    p.curve([(25,-39),(31,-34),(33,-29),(33,-24)],tint('#b8839d','#852b43',devil),1.25)
    # Broad cheekbones, a small nose and eyes that stay legible at game scale.
    eye(p,-7,-21,8.5,anger,blink,devil,True)
    eye(p,17,-20,9.8,anger,blink,devil,False)
    p.oval(-13,-8,5.7,2.6,tint(tint('#edb3ae','#df859a',anger),'#cf3444',devil),None,angle=-12)
    p.oval(28,-7,4.7,2.5,tint(tint('#edb3ae','#d67d92',anger),'#9f2d40',devil),None,angle=-18)
    p.curve([(4,-19),(8,-16),(6,-12),(10,-12)],tint('#bb8798','#a22d3f',devil),1.4)
    # The smile opens continuously, preserving the same mouth corners.
    k=smooth((anger-.06)/.94)
    if k<.035:
        p.curve([(-1,-5),(5,2),(13,2),(20,-5)],'#91596d',2.0)
        p.curve([(5,3),(8,4),(12,4),(15,2)],'#d2a0a6',1)
    else:
        top=mix(2,-8,k); lower=mix(2,12,k)+4*devil
        left=-1-5*devil; right=20+4*devil
        p.shape([(left,-5),(5,top),(14,top),(right,-5),
                 (right+3,lower),(left+2,lower),(left,-5)],tint('#4d284a','#421526',devil),'#693651',1.4)
        if k>.28:
            teeth=smooth((k-.28)/.72)
            for j in range(4):
                x=1+4.6*j; base=mix(-1.1,-5.2,k)
                if j in (0,3):
                    x += (j-1.5)*devil*2
                tooth=4.1*teeth + (5*devil if j in (0,3) else 0)
                p.poly([(x,base),(x+3.6+devil,base),(x+1.8+.4*devil,base+tooth)],'#fff0d4',None)
            if k>.72:
                p.poly([(6,5.2),(8,2.5),(10,6.0)],'#ffe0c8',None)
                p.poly([(14,6.0),(16,2.8),(18,5.0)],'#ffe0c8',None)
        if k>.45:
            p.curve([(3,lower*.57),(7,lower*.82),(14,lower*.82),(18,lower*.57)],'#e17e92',1.1)
    # Two small arms unfold, then tuck under the chin during the charge.
    hx=14+14*max(0,reach)-5*max(0,-reach); hy=17-7*max(0,-reach)
    p.limb([(-14,10),(-8,20),(hx,hy)],tint('#c36f92','#a53346',devil),8)
    p.limb([(-14,9),(-7,17),(hx,hy-1)],tint('#e6a0b1','#dc534e',devil),5.1)
    p.oval(hx,hy,5.4,4.8,tint('#f1b9bc','#f57860',devil),INK,1.4)
    p.line([(hx-1,hy-2),(hx-1,hy+2)],tint('#b66e8b','#a33842',devil),.9)
    p.limb([(29,10),(32+5*max(0,reach),17),(22+6*reach,hy+1)],tint('#d282a1','#b83f4b',devil),6)
    p.oval(22+6*reach,hy+1,4.4,4.0,tint('#efadb9','#e96354',devil),INK,1.25)


def draw_charge_streaks(p, time):
    pulse=track(time,[(WINDUP_S,0),(.69,1),(.78,.8),(.92,0)])
    if not pulse:
        return
    for x,y,length in [(-58,-17,34),(-52,9,43),(-39,28,27)]:
        p.poly([(x-length*pulse,y),(x,y-2.4*pulse),(x+7,y),(x-5,y+1.4*pulse)],
               (252,119,92,round(215*pulse)),None)


def _render_frame(anim, i, n):
    x,y,tilt,sx,sy,m,anger,flap,reach,angle,blink,fade=pose(anim,i,n)
    p=Painter(x,y,tilt,sx,sy)
    phase=math.tau*i/max(1,n)
    death=i/max(1,n-1) if anim=='death' else 0.
    devil=smooth((m-.22)/.56) if anim in {'windup','attack_side'} else 0.
    if anim=='attack_side':
        draw_charge_streaks(p, i/max(1,n-1)*TOTAL_S)
    # Far horn occluded by the head; the near root sits in front of it.
    if m>.002: draw_horn(p,-1,m,angle,devil)
    body(p,anger,devil,flap,reach,blink,phase,death)
    if m>.002: draw_horn(p,1,m,angle,devil)
    else: intact_crown(p,angle)
    # The opening seams emit short, attached glints during the telegraph.
    if .15<m<.65:
        for side in (-1,1):
            pts,_=crown_geometry(side,m,angle)
            for xx,yy in (pts[0],pts[-1]):
                p.line([(xx-1.7,yy),(xx+1.7,yy)],tint('#fff0b1','#ffa486',devil),1.4)
    return p.finish(fade)


def render(out_dir: str | Path, **opts):
    from ._art_cast_kit import render_target
    return render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, Path(out_dir), **opts)
