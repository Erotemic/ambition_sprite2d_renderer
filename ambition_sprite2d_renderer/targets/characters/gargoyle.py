"""A winged stone gargoyle with a heavy, grounded claw attack."""
from __future__ import annotations

import math
from dataclasses import dataclass
from contextlib import contextmanager
from pathlib import Path

from PIL import Image
import numpy as np

from ._magic_character_art import (Canvas, add, sub, mul, mix, unit, perp, rot,
                                   bezier, phase, track)
from ...authoring.sheet_build import build_sheet
from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'gargoyle'
FRAME_SIZE = (420, 308)
CX, GROUND = 209.5, 259.
# The solid body, not the wings, horns, tail or attack extension.
BODY_BOX = (102, 108, 318, 261)
WINDUP, ACTIVE, RECOVERY = .66, .18, .84
TOTAL = WINDUP + ACTIVE + RECOVERY
A, B = WINDUP / TOTAL, (WINDUP + ACTIVE) / TOTAL
ROWS = [('idle', 12, 90), ('walk', 16, 75), ('run', 16, 55),
        ('turnaround', 5, 51), ('notice', 8, 65), ('windup', 12, 55),
        ('attack_side', 42, 40), ('hit', 9, 60), ('death', 21, 60),
        ('death_idle', 1, 200)]
LOOPS = {'idle', 'walk', 'run', 'death_idle'}
TRAITS = ['enemy', 'fantasy', 'monster', 'gargoyle', 'stone', 'winged']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Gargoyle'},
    'body': {'body_plan': 'Quadruped', 'body_kind': 'Standard', 'mass_class': 'Heavy',
             'locomotion_hint': 'Walk', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'actions': {'default_preset': 'gargoyle_rake'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'locomotion.turnaround': {'animation': 'turnaround', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': A, 'event': 'hitbox_active_start', 'source': 'gargoyle.rake'},
            {'t': B, 'event': 'hitbox_active_end', 'source': 'gargoyle.rake'}]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': ('A crouched quadrupedal cathedral grotesque with a broad lionlike jaw, '
                              'carved stone ruff, heavy paws, and folded sculptural wings.'),
    'gameplay_description': ('A heavy grounded quadruped. It flares its stone wings, raises a '
                             'forepaw and rakes forward. The wings do not provide flight.'),
}

INK = '#343831'
STONE = '#999b8d'
DARK = '#646a5f'
FAR = '#777b6e'
LIGHT = '#c0c0ac'
MID = '#a9ab9a'
CRACK = '#565b50'
EDGE = '#c2c3b4'
CLAW = '#d3d0b9'
WING = '#646c70'
PANEL = '#838b88'
EYE = '#ddd9c2'


def path(start, *segs):
    out = [start]
    for a, b, end in segs:
        out.extend(bezier(out[-1], a, b, end, 14)[1:])
    return out


class PartScene:
    """Local rasters and the ordered placements the runtime draws."""
    _cache = {}

    def __init__(self):
        self.s = 3
        self.ops = []
        self.local = None
        self.anchor = None
        self.center = (210.,154.)
        self.cached = False

    @contextmanager
    def part(self, name, anchor=(CX, GROUND-90), *, key=None,
             at=None, degrees=0.):
        assert self.anchor is None, name
        self.anchor = anchor
        cached = self._cache.get(key) if key is not None else None
        self.cached = cached is not None
        self.local = None if self.cached else Canvas(FRAME_SIZE,self.s)
        try:
            yield
            if cached is None:
                im=self.local.image
                bbox=im.getbbox()
                if bbox is None:return
                x0,y0,x1,y1=bbox
                assert x0>0 and y0>0 and x1<im.width and y1<im.height, name
                x0=max(0,(x0-6)//self.s*self.s);y0=max(0,(y0-6)//self.s*self.s)
                x1=min(im.width,math.ceil((x1+6)/self.s)*self.s)
                y1=min(im.height,math.ceil((y1+6)/self.s)*self.s)
                pivot=(self.center[0]*self.s-x0,self.center[1]*self.s-y0)
                cached=(im.crop((x0,y0,x1,y1)),pivot)
                if key is not None:self._cache[key]=cached
            # Whole logical-pixel anchors keep a shared texel grid. The
            # orientation is continuous and stored in the part draw.
            dest=tuple(round(v)*self.s for v in (anchor if at is None else at))
            self.ops.append((name,*cached,dest,degrees))
        finally:
            self.local=self.anchor=None
            self.cached=False

    def _pts(self,pts):
        ax,ay=self.anchor;cx,cy=self.center
        return [(round(x-ax+cx,5),round(y-ay+cy,5)) for x,y in pts]

    def poly(self,pts,fill,edge,width):
        if not self.cached:self.local.poly(self._pts(pts),fill,edge,width)

    def line(self,pts,fill,width):
        if not self.cached:self.local.line(self._pts(pts),fill,width)

    def finish(self, ground_lock=False):
        frame=Image.new('RGBA',tuple(v*self.s for v in FRAME_SIZE))
        dy=0
        if ground_lock:
            # Measure the support of the transformed parts, not the frame.
            # The tail, chest and folded limbs can all touch the ground.
            bottom=-math.inf
            for name,im,pivot,at,deg in self.ops:
                yy,xx=np.nonzero(np.asarray(im.getchannel('A'))>=32)
                if not len(yy):continue
                r=math.radians(deg)
                support=(xx-pivot[0])*math.sin(r)+(yy-pivot[1])*math.cos(r)
                bottom=max(bottom,at[1]+float(support.max())+1)
            dy=round((GROUND+1)*self.s-bottom)
        for name,im,pivot,at,deg in self.ops:
            rigdoc.blit_rotated(frame,im,pivot,(at[0],at[1]+dy),deg,part_name=name)
        return rigdoc.downsampled_canvas(frame,FRAME_SIZE,Image.Resampling.LANCZOS)


class Pen:
    def __init__(self, canvas, transform):
        self.c = canvas
        self.P = transform

    def poly(self, pts, fill, edge=INK, w=2.2):
        self.c.poly([self.P(*p) for p in pts], fill, edge, w)

    def line(self, pts, fill=INK, w=1.6):
        self.c.line([self.P(*p) for p in pts], fill, w)

    def shape(self, start, *segs, fill, edge=INK, w=2.2):
        self.poly(path(start, *segs), fill, edge, w)

    def oval(self, x, y, rx, ry, fill, edge=INK, w=1.5):
        self.poly([(x+rx*math.cos(math.tau*k/40), y+ry*math.sin(math.tau*k/40))
                   for k in range(40)], fill, edge, w)

    def crack(self, pts, w=1.3):
        self.line([(x+.8, y+.9) for x,y in pts], '#b5b5a4', w*.85)
        self.line(pts, CRACK, w)

    def limb(self, joints, widths, far=False, fissures=True):
        # The limb is one continuous contour, not separate discs at the joints.
        normals = [perp(unit(sub(joints[min(j+1,len(joints)-1)], joints[max(0,j-1)])))
                   for j in range(len(joints))]
        left = [add(p,mul(v,r)) for p,v,r in zip(joints,normals,widths)]
        right = [add(p,mul(v,-r)) for p,v,r in zip(joints,normals,widths)]
        contour = left+right[::-1]
        rounded = []
        for j,v in enumerate(contour):
            a,b = contour[j-1],contour[(j+1)%len(contour)]
            rounded.extend(bezier(mix(v,a,.22),v,v,mix(v,b,.22),5))
        col = FAR if far else STONE
        self.poly(rounded,col)
        self.poly([add(p,mul(v,r*.25)) for p,v,r in zip(joints,normals,widths)]
                  + [add(p,mul(v,r*.78)) for p,v,r in zip(joints,normals,widths)][::-1],
                  '#878a7d' if far else MID,None)
        # A continuous bevel on the lit side of the stone limb. Avoid a
        # transverse seam at every articulation: this is carved stone, not
        # a set of mechanical shells.
        if fissures and len(joints)>=4:
            k=1 if len(joints)==4 else 2
            p=joints[k]; v=normals[k]; r=widths[k]
            tangent=unit(sub(joints[min(k+1,len(joints)-1)],joints[k-1]))
            self.crack([add(p,mul(v,-r*.75)),add(add(p,mul(v,-r*.32)),mul(tangent,-4)),
                        add(add(p,mul(v,-r*.12)),mul(tangent,2)),
                        add(add(p,mul(v,r*.10)),mul(tangent,5))],1.1)
            if not far:
                self.line([add(a,mul(b,r*.62)) for a,b,r in zip(joints[1:-1],normals[1:-1],widths[1:-1])],LIGHT,1.25)

@dataclass(frozen=True)
class Pose:
    cycle: float = 0.
    gait: float = 0.
    ready: float = 0.
    strike: float = 0.
    recover: float = 0.
    notice: float = 0.
    hurt: float = 0.
    death: float = 0.


def pose(anim,i,n):
    t=phase(i,n,anim in LOOPS); p=math.tau*t
    if anim=='idle': return Pose(p)
    if anim in ('walk','run'):return Pose(p, .70 if anim=='walk' else 1.0)
    if anim=='notice':return Pose(notice=track(t,[(0,0),(.5,1),(1,.7)]))
    if anim=='windup':return Pose(ready=track(t,[(0,0),(.80,1),(1,1)]))
    if anim=='attack_side':
        u=track(t,[(0,0),(.80*A,1),(A,1),(A+.065,0),(1,0)])
        s=track(t,[(0,0),(A,0),(A+.045,1),(B,1),(B+.18,.23),(1,0)])
        r=track(t,[(0,0),(B,0),(B+.17,1),(1,0)])
        return Pose(ready=u,strike=s,recover=r)
    if anim=='hit':return Pose(hurt=math.sin(math.pi*t))
    if anim in ('death','death_idle'):
        return Pose(death=1. if anim=='death_idle' else track(t,[(0,0),(.16,.10),(.72,.94),(1,1)]))
    raise ValueError(anim)


def stone_wing(pen, shoulder, spread, side=1, far=False, frontal=False, collapse=0., quarter=False):
    """Carved, folded wing: a heavy curved spar and overlapping stone vanes.

    The points are attached to the shoulder, not to the silhouette of the head.
    Open the vane fan by changing the individual lengths and their angles.
    """
    sh = shoulder
    if quarter:
        if far:
            axis=(23,-67); tip=(43,-94); tips=[(51,-109),(65,-76),(58,-36),(38,0),(10,16)]
        else:
            axis=(-40,-55); tip=(-77,-85); tips=[(-101,-98),(-120,-57),(-105,-17),(-72,10),(-23,22)]
    elif frontal:
        # Outward-facing paired wing silhouettes; roots behind the shoulders.
        axis = (side*(38+17*spread), -54+22*collapse)
        tip = (side*(82+24*spread), -90+46*collapse)
        tips = [(side*(96+24*spread), -101+49*collapse),
                (side*(106+30*spread), -59+35*collapse),
                (side*(92+29*spread), -21+17*collapse),
                (side*(65+18*spread), 7+7*collapse), (side*23, 16)]
    else:
        depth = .80 if far else 1.
        # Wings point back and up like the wings of a cathedral grotesque.
        # The farther wing is raised above the nearer wing rather than mirrored.
        axis = (-38*depth, -52-18*spread+35*collapse)
        tip = (-77*depth-12*spread, -88-17*spread+55*collapse)
        tips = [(-103*depth-15*spread,-96-21*spread+55*collapse),
                (-123*depth-18*spread,-58-15*spread+40*collapse),
                (-111*depth-16*spread,-14+25*collapse),
                (-76*depth-10*spread,13+15*collapse),(-22*depth,22)]
    if far and not frontal:
        # The farther folded wing stands more upright behind its mate. Its
        # spar and vanes remain a separate chain, with their own silhouette.
        def raised(v):return (.62*v[0]+17, v[1]*1.17-8)
        axis=raised(axis); tip=raised(tip); tips=[raised(v) for v in tips]
    wrist=add(sh,axis); crown=add(sh,tip); points=[add(sh,v) for v in tips]
    base = '#64695f' if far else '#85897c'
    shadow = '#4c554e' if far else '#586157'
    panel = '#7b8174' if far else '#a2a597'
    # Broad folded slab with an ogee outline, not a thin bat membrane.
    outline=[sh,wrist,crown,points[0]]
    for x,y in zip(points,points[1:]):
        outline.extend(bezier(x,mix(x,wrist,.27),mix(y,wrist,.19),y,12)[1:])
    outline.append(sh)
    pen.poly(outline,base,INK,2.8)
    for j,(x,y) in enumerate(zip(points,points[1:])):
        # Each carved vane follows exactly the same scallop as its outer
        # silhouette. The face and ribs therefore cannot spill past the edge.
        scallop=bezier(x,mix(x,wrist,.27),mix(y,wrist,.19),y,12)
        face=[wrist]+scallop+[wrist]
        pen.poly(face,panel if j%2==0 else base,None)
        # Inner beveled face uses the same concavity, shrunk toward the wrist.
        inset=[mix(wrist,v,.77) for v in scallop]
        pen.poly([wrist]+inset+[wrist],base if j%2==0 else shadow,None)
        pen.line([mix(wrist,x,.10),mix(wrist,x,.65),x],shadow,3.0)
        pen.line([mix(wrist,x,.20),mix(wrist,x,.72)],LIGHT if not far else panel,1.3)
        pen.line([mix(wrist,v,.90) for v in scallop[2:-2]],panel if j%2 else LIGHT,1.0)
    pen.line(outline,INK,2.6)
    pen.limb([sh,mix(sh,wrist,.56),wrist,crown],[11,9,6,3],far,False)
    pen.line([mix(sh,wrist,.2),mix(sh,wrist,.73),wrist],LIGHT if not far else base,2.0)
    if not far:
        pen.crack([mix(wrist,points[1],.46),mix(wrist,points[1],.58),add(mix(wrist,points[1],.65),(4,-3)),mix(wrist,points[2],.69)],1.1)


def paw(pen, x, y, far=False, front=False, rake=0.):
    """Broad load-bearing catlike stone paws; the claws are carved into toes."""
    col=FAR if far else STONE
    hi='#898c80' if far else LIGHT
    if front:
        pen.shape((x-19,y-12),((x-22,y-3),(x-24,y+4),(x-18,y+9)),
                  ((x-4,y+12),(x+14,y+12),(x+20,y+7)),
                  ((x+23,y+1),(x+18,y-10),(x+13,y-12)),
                  ((x+1,y-16),(x-13,y-15),(x-19,y-12)),fill=col)
        pen.poly([(x-14,y-10),(x+12,y-10),(x+16,y-5),(x-12,y-3)],hi,None)
        for k in (-1,0,1):
            xx=x+12*k
            pen.shape((xx-4,y+4),((xx-5,y+7),(xx-6,y+12),(xx,y+13)),
                      ((xx+5,y+11),(xx+5,y+7),(xx+4,y+4)),fill=CLAW,w=1.2)
    else:
        pen.shape((x-17,y-10),((x-21,y-3),(x-22,y+5),(x-13,y+8)),
                  ((x+1,y+12),(x+21,y+10),(x+26+7*rake,y+5)),
                  ((x+29+7*rake,y-4),(x+13,y-10),(x+6,y-12)),
                  ((x-1,y-15),(x-13,y-14),(x-17,y-10)),fill=col)
        pen.poly([(x-12,y-10),(x+8,y-10),(x+19,y-3),(x-6,y-4)],hi,None)
        for k in range(3):
            xx=x+10+k*6; yy=y+4-k*3
            pen.line([(xx-6,yy-4),(xx-3,yy-1)],DARK,1.0)
            pen.shape((xx-3,yy-2),((xx+2,yy-3),(xx+8+5*rake,yy),(xx+7+5*rake,yy+4)),
                      ((xx+2,yy+5),(xx-1,yy+2),(xx-3,yy-2)),fill=CLAW,w=1.0)


def stone_segment(scene, name, a, b, widths, far):
    """Paint a shaped stone bone along local +y; rotate it about its root.

    Lengths use small discrete raster families, with overlapping ends.
    The limb's joints and paw targets are independent of the texture.
    """
    dx,dy=sub(b,a)
    length=max(8,4*round(math.hypot(dx,dy)/4))
    angle=math.degrees(math.atan2(-dx,dy))
    r0,rm,r1=widths
    col=FAR if far else STONE
    shade='#656b61' if far else '#767d70'
    hi='#929588' if far else LIGHT
    pen=Pen(scene,lambda x,y:(x,y))
    at=(CX+a[0],GROUND+a[1])
    with scene.part(name,(0,0),key=('segment',length,widths,far),at=at,degrees=angle):
        # Rounded, slightly faceted ends overlap the adjoining bone. No
        # circular hardware or cap plates are drawn at the joints.
        pen.shape((-r0*.82,-5),((-r0,-2),(-rm, length*.24),(-rm,length*.42)),
            ((-rm,length*.66),(-r1*1.06,length*.88),(-r1*.94,length+4)),
            ((-r1*.4,length+8),(r1*.5,length+8),(r1*.93,length+4)),
            ((r1*1.05,length*.86),(rm,length*.64),(rm*.89,length*.36)),
            ((rm*.9,length*.13),(r0*.9,-4),(r0*.66,-7)),
            ((r0*.14,-10),(-r0*.47,-9),(-r0*.82,-5)),fill=col,w=2.1)
        pen.poly([(-rm*.84,length*.15),(-rm*.46,length*.05),(-rm*.24,length*.32),
                  (-r1*.18,length*.84),(-r1*.64,length+1),(-rm*.72,length*.52)],hi,None)
        pen.poly([(rm*.55,length*.10),(rm*.85,length*.35),(r1*.8,length*.85),
                  (r1*.54,length+3),(r1*.12,length*.58)],shade,None)
        pen.crack([(-rm*.70,length*.40),(-rm*.30,length*.49),(-rm*.48,length*.58),(-r1*.14,length*.64)],1.0)
        pen.line([(-rm*.72,length*.13),(-rm*.86,length*.27),(-rm*.73,length*.39)],hi,1.15)


def side_frame(anim,i,n):
    q=pose(anim,i,n); p,d=q.cycle,q.death
    c=PartScene()
    pen=Pen(c,lambda x,y:(CX+x,GROUND+y))
    # The torso moves independently of the foot plants. Its long quadrupedal
    # silhouette and head carried out in front distinguish it from the imps.
    bx=-9*q.ready+15*q.strike-7*q.hurt
    by=4*q.ready+5*q.strike+3*q.recover+4*q.hurt+2*q.gait*math.cos(2*p)+44*d
    def U(x,y):return x+bx,y+by
    def us(pts):return [U(*v) for v in pts]
    def ush(start,*segs,**kw):pen.shape(U(*start),*((U(*a),U(*b),U(*z)) for a,b,z in segs),**kw)
    # A short, hooked architectural tail, unlike the imp's long pointed tail.
    with c.part('tail',(CX-80,GROUND-65),key=('side_tail',),
                at=(CX+bx-80,GROUND+by-65-12*d),degrees=-7*q.ready+4*q.strike+5*d):
        tail=path((-80,-65),((-105,-58),(-140,-45),(-150,-62)),
                  ((-158,-81),(-142,-89),(-133,-82)))
        pen.limb(tail,[11*(1-j/(len(tail)-1))**.75+3 for j in range(len(tail))],False,False)
        for j in (8,18):
            a=tail[j];v=perp(unit(sub(tail[j+1],tail[j-1])));r=11*(1-j/(len(tail)-1))**.75+3
            pen.crack([add(a,mul(v,-r*.8)),a,add(a,mul(v,r*.7))],1.)
    spread=round(4*(.9*q.ready+.45*q.notice+.25*q.strike))/4
    fold=round(4*d)/4
    far_spread=round(3*spread)/4
    with c.part('wing_far',(CX+bx+15,GROUND+by-110),key=('wing',True,far_spread,fold),degrees=-7*q.ready-4*q.strike):
        stone_wing(pen,U(15,-110),far_spread,far=True,collapse=fold)
    def leg(fore,far):
        angle=p+(math.pi if far else 0)+(math.pi if fore else 0)
        step=23*q.gait*math.sin(angle); lift=max(0.,-math.cos(angle))*11*q.gait
        if fore:
            hip=U(40 if far else 28,-88)
            elbow=(hip[0]+5+step*.5, -47+by*.35+8*d)
            x=(62 if far else 35)+step
            y=-13-lift
            if not far:
                # Pull up and then swipe the near front paw out below the jaw.
                # The other three limbs remain weight-bearing.
                elbow=(elbow[0]-22*q.ready+29*q.strike,elbow[1]-14*q.ready-12*q.strike)
                x+=-25*q.ready+85*q.strike+17*q.recover
                y-=31*q.ready+34*q.strike+8*q.recover
            ankle=(x,y)
            name='fore_far' if far else 'fore_near'
            stone_segment(c,name+'_shin',elbow,ankle,(16,17,12),far)
            stone_segment(c,name+'_upper',hip,elbow,(19,22,16),far)
            rake=round(4*q.strike)/4 if not far else 0.
            with c.part(name+'_paw',(CX+ankle[0],GROUND+ankle[1]),key=('side_paw',far,rake)):
                paw(pen,*ankle,far=far,rake=rake)
        else:
            hip=U(-64 if far else -78,-65)
            knee=(hip[0]+27+step*.35,-36+by*.31+5*d)
            ankle=((-55 if far else -82)+step,-13-lift)
            name='hind_far' if far else 'hind_near'
            stone_segment(c,name+'_shin',knee,ankle,(16,15,10),far)
            stone_segment(c,name+'_upper',hip,knee,(22,24,17),far)
            with c.part(name+'_paw',(CX+ankle[0],GROUND+ankle[1]),key=('side_paw',far,0.)):
                paw(pen,*ankle,far=far)
    leg(False,True);leg(True,True)
    # Low heavy haunches, arched spine, thick chest. No humanoid abdomen.
    with c.part('torso',(CX+bx,GROUND+by),key=('side_torso',)):
        ush((-94,-73),((-102,-97),(-80,-116),(-53,-114)),
            ((-29,-122),(-4,-119),(20,-116)),((45,-114),(56,-93),(57,-76)),
            ((65,-52),(39,-40),(12,-43)),((-8,-39),(-23,-49),(-48,-46)),
            ((-75,-35),(-95,-48),(-94,-73)),fill=STONE,w=3.)
        pen.poly(us([(-89,-78),(-77,-103),(-52,-110),(-29,-104),(-12,-112),(9,-108),(28,-99),(11,-84),(-22,-76),(-56,-81),(-80,-69)]),MID,None)
        pen.poly(us([(-81,-91),(-64,-106),(-48,-107),(-28,-101),(-50,-95),(-65,-85)]),LIGHT,None)
        pen.poly(us([(-44,-59),(-17,-51),(9,-48),(32,-52),(42,-61),(16,-65),(-16,-64)]),DARK,None)
        pen.crack(us([(-69,-105),(-64,-93),(-55,-89),(-59,-79)]),1.4)
        pen.crack(us([(-13,-113),(-18,-104),(-9,-97),(-14,-91)]),1.3)
        pen.line(us([(-85,-88),(-77,-101),(-62,-108)]),LIGHT,1.8)
        pen.poly(us([(-87,-66),(-79,-60),(-70,-64),(-77,-69)]),MID,None)
        pen.crack(us([(-83,-71),(-79,-65),(-81,-61)]),1.0)
        pen.poly(us([(-62,-75),(-45,-77),(-35,-73),(-50,-69)]),MID,None)
        pen.line(us([(-37,-102),(-24,-106),(-15,-102)]),LIGHT,1.0)
    # Near haunch and near shoulder are muscular, full continuous limbs.
    leg(False,False);leg(True,False)
    # The near wing is on the visible flank, in front of the torso and
    # upper limb roots. Its base is recessed into the scapular stone.
    # The ruff/head are painted afterward and conceal only the forward edge.
    with c.part('wing_near',(CX+bx+4,GROUND+by-91),key=('wing',False,spread,fold),degrees=6*q.ready-4*q.strike):
        stone_wing(pen,U(4,-91),spread,collapse=fold)
    with c.part('wing_root',(CX+bx,GROUND+by),key=('side_wing_root',)):
        ush((-10,-91),((-10,-98),(1,-100),(9,-96)),
            ((18,-92),(16,-82),(8,-77)),((-1,-76),(-9,-83),(-10,-91)),fill=STONE,w=1.9)
        pen.line(us([(-7,-90),(-1,-95),(7,-94)]),LIGHT,1.8)
        pen.line(us([(8,-78),(13,-83),(14,-89)]),DARK,1.5)
    # Massive head held horizontally like a cathedral lion/bulldog grotesque.
    # The scalloped stone ruff joins the shoulders, hiding their limb roots.
    hx=bx+44+9*q.strike-7*q.ready
    hy=by-4*q.notice+4*q.hurt+3*d
    h=Pen(c,lambda x,y:(CX+x+hx,GROUND+y+hy))
    with c.part('head',(CX+hx,GROUND+hy),key=('side_head',)):
        h.shape((-39,-119),((-32,-133),(-16,-138),(-5,-129)),
                ((1,-131),(11,-126),(14,-121)),((10,-106),(3,-99),(12,-88)),
                ((2,-78),(-3,-70),(-13,-65)),((-15,-76),(-25,-78),(-26,-69)),
                ((-41,-78),(-50,-92),(-45,-106)),((-47,-113),(-44,-119),(-39,-119)),fill=DARK,w=2.6)
        h.poly([(-40,-111),(-28,-127),(-16,-124),(-23,-107),(-13,-95),(-24,-83),(-37,-89)],MID,None)
        # Low ears and a sculpted lionlike mane with three swept, chiselled lobes.
        # No exposed high horns, pointed devil ears, or spherical imp skull.
        h.shape((-10,-126),((-13,-137),(-7,-145),(6,-143)),
                ((14,-143),(20,-135),(13,-127)),((1,-123),(-7,-124),(-10,-126)),fill=FAR)
        h.shape((-38,-126),((-45,-136),(-42,-145),(-30,-145)),
                ((-19,-146),(-12,-138),(-14,-128)),((-21,-123),(-31,-122),(-38,-126)),fill=STONE)
        h.poly([(-38,-137),(-29,-141),(-22,-136),(-27,-129),(-33,-130)],DARK,None)
        h.shape((-37,-126),((-50,-125),(-56,-114),(-54,-105)),
                ((-60,-97),(-55,-90),(-49,-84)),((-51,-77),(-44,-69),(-38,-67)),
                ((-33,-78),(-30,-78),(-24,-70)),((-24,-78),(-10,-75),(-9,-84)),
                ((-7,-105),(-19,-125),(-37,-126)),fill=DARK,w=2.5)
        for k,(a,b,z) in enumerate([((-46,-119),(-52,-111),(-40,-101)),((-52,-104),(-50,-96),(-38,-91)),((-48,-89),(-42,-82),(-37,-75))]):
            h.line([a,b,z],MID,4.2);h.line([a,b],LIGHT,1.3)
        # Broad head with a short, squared-off muzzle and heavy cheeks.
        h.shape((-32,-122),((-22,-136),(0,-139),(17,-128)),
                ((29,-130),(38,-121),(39,-111)),((52,-111),(56,-105),(56,-97)),
                ((56,-78),(49,-69),(34,-69)),((12,-61),(-7,-68),(-21,-81)),
                ((-35,-88),(-42,-103),(-32,-122)),fill=STONE,w=3.)
        h.poly([(-29,-119),(-16,-131),(4,-131),(19,-123),(8,-122),(-7,-119),(-21,-111)],LIGHT,None)
        h.poly([(-28,-106),(-13,-100),(-20,-88),(-31,-93)],DARK,None)
        h.line([(-31,-112),(-29,-103),(-21,-98)],LIGHT,1.5)
        h.poly([(-32,-109),(-19,-103),(-2,-102),(3,-91),(-10,-79),(-25,-87)],MID,None)
        h.poly([(20,-123),(35,-119),(40,-112),(27,-110),(16,-113)],MID,None)
    # Deep-set hooded eyes. The carved brow has a central downward wedge,
    # with small white recessed eyes instead of a yellow imp gaze.
    with c.part('eyes_and_nose',(CX+hx,GROUND+hy),key=('side_eyes',d<.65)):
        h.poly([(-18,-117),(12,-110),(8,-100),(-12,-104)],'#45473f',INK,1.7)
        h.poly([(25,-111),(36,-118),(39,-108),(31,-103)],'#45473f',INK,1.4)
        if d<.65:
            h.poly([(-11,-113),(7,-109),(5,-104),(-8,-107)],EYE,None)
            h.poly([(28,-110),(35,-114),(35,-108),(30,-106)],EYE,None)
        h.poly([(-26,-125),(-9,-126),(16,-113),(12,-106),(1,-111),(-11,-116),(-22,-117)],MID,INK,1.9)
        h.poly([(20,-114),(31,-124),(37,-120),(35,-115),(25,-110)],MID,INK,1.6)
        h.line([(-23,-123),(-9,-124),(7,-115)],LIGHT,1.6)
        # Short broad snub nose with two deep nostrils and carved muzzle folds.
        h.shape((31,-111),((38,-117),(50,-114),(55,-108)),
                ((60,-101),(54,-95),(46,-95)),((35,-96),(30,-101),(31,-111)),fill=DARK)
        h.oval(38,-105,3.7,3,INK,None);h.oval(50,-104,3.5,2.7,INK,None)
        h.poly([(34,-112),(43,-114),(51,-111),(44,-108)],LIGHT,None)
    gape=2*round((3+10*q.ready+12*q.strike+7*q.hurt+7*d)/2)
    with c.part('jaw',(CX+hx,GROUND+hy),key=('side_jaw',gape)):
        # The mouth is a snarl, with downward turned corners and deep jowls.
        h.shape((-2,-87),((10,-99),(30,-96),(53,-96)),
                ((57,-85+gape*.42),(45,-81+gape*.55),(30,-83+gape*.45)),
                ((14,-85+gape*.3),(5,-80),(-2,-87)),fill='#32352f',w=2.)
        for x,y,w,len_ in [(10,-93,5.3,11),(24,-94,3.0,6),(37,-95,3.2,7),(48,-96,4.1,9)]:
            h.poly([(x-w,y),(x+w,y),(x+1,y+len_+gape*.13)],CLAW,INK,1.)
        for x,y,w,len_ in [(10,-85,4.8,10),(40,-83,4.4,12)]:
            h.poly([(x-w,y+3+gape*.38),(x-1,y-len_+gape*.2),(x+w,y+3+gape*.38)],CLAW,INK,1.)
        h.line([(-5,-94),(-8,-86),(-1,-78),(13,-73),(31,-72+gape*.22)],DARK,2.)
        h.line([(2,-79),(14,-73),(31,-72+gape*.2),(47,-77+gape*.3)],LIGHT,1.5)
        h.crack([(-14,-131),(-8,-123),(-11,-118)],1.3)
        h.crack([(-14,-100),(-21,-94),(-17,-87)],1.1)
        h.poly([(-29,-87),(-25,-82),(-20,-81),(-24,-86)],LIGHT,None)
        h.line([(0,-97),(5,-100),(11,-99)],LIGHT,1.0)
        h.line([(32,-74),(43,-75),(49,-81)],MID,1.6)
    return c.finish(ground_lock=d>0)


def front_frame():
    """Independent frontal view of the low quadruped, not a side-view warp."""
    c=PartScene(); pen=Pen(c,lambda x,y:(CX+x,GROUND+y))
    # Tail and hindquarters recessed behind the chest and near forepaws.
    with c.part('front_tail'):
        tail=path((-18,-61),((-45,-42),(-93,-44),(-103,-59)),((-110,-72),(-99,-85),(-89,-81)))
        pen.limb(tail,[9*(1-j/(len(tail)-1))+.5+3 for j in range(len(tail))],False,False)
    for s in (-1,1):
        hip=(s*40,-67);knee=(s*59,-42);ankle=(s*61,-21)
        with c.part(f'front_hind_{s}'):
            pen.limb([hip,mix(hip,knee,.5),knee,ankle],[22,23,15,10],True)
            paw(pen,*ankle,True,True)
    with c.part('front_torso'):
        pen.shape((-45,-111),((-23,-127),(23,-127),(45,-111)),
                  ((68,-90),(59,-62),(38,-45)),((18,-36),(-18,-36),(-38,-45)),
                  ((-59,-62),(-68,-90),(-45,-111)),fill=STONE,w=3.)
    for s in (-1,1):
        with c.part(f'front_wing_{s}'):
            stone_wing(pen,(s*38,-97),.08,s,frontal=True)
    for s in (-1,1):
        with c.part(f'front_fore_{s}'):
            pen.poly([(s*x,y) for x,y in [(14,-111),(37,-114),(51,-98),(44,-79),(19,-67),(9,-84)]],MID,None)
            sh=(s*42,-90);el=(s*51,-49);wr=(s*43,-14)
            pen.limb([sh,mix(sh,el,.5),el,mix(el,wr,.6),wr],[19,23,16,18,12])
            paw(pen,*wr,front=True)
    with c.part('front_head'):
        # Ruff and a full broad frontal lion/grotesque face. Ears are squat stone lobes.
        pen.shape((-40,-129),((-51,-121),(-63,-102),(-54,-89)),
                  ((-55,-80),(-47,-68),(-40,-65)),((-32,-75),(-20,-74),(-14,-63)),
                  ((-4,-66),(4,-66),(14,-63)),((20,-74),(32,-75),(40,-65)),
                  ((47,-68),(55,-80),(54,-89)),((63,-102),(51,-121),(40,-129)),
                  ((22,-141),(-22,-141),(-40,-129)),fill=DARK,w=2.7)
        for s in (-1,1):
            def S(x,y):return s*x,y
            pen.shape(S(26,-124),(S(22,-136),S(30,-144),S(42,-143)),
                      (S(51,-144),S(55,-135),S(49,-127)),(S(40,-122),S(30,-121),S(26,-124)),fill=STONE)
            pen.poly([S(x,y) for x,y in [(34,-132),(40,-139),(48,-136),(44,-129),(38,-128)]],DARK,None)
            for a,b,z in [((46,-124),(53,-113),(43,-102)),((53,-106),(56,-98),(45,-89)),((52,-89),(48,-81),(41,-74))]:
                pen.line([S(*a),S(*b),S(*z)],MID,4.4)
                pen.line([S(*a),S(*b)],LIGHT,1.3)
        pen.shape((-41,-120),((-29,-137),(-9,-137),(0,-131)),
                  ((9,-137),(29,-137),(41,-120)),((49,-107),(45,-88),(33,-77)),
                  ((20,-65),(-20,-65),(-33,-77)),((-45,-88),(-49,-107),(-41,-120)),fill=STONE,w=3.)
        pen.poly([(-35,-120),(-22,-131),(-9,-130),(0,-125),(9,-130),(22,-131),(35,-120),(16,-119),(0,-115),(-16,-119)],LIGHT,None)
        for s in (-1,1):
            def S(x,y):return s*x,y
            pen.poly([S(x,y) for x,y in [(7,-111),(33,-122),(32,-107),(18,-103)]],'#45473f',INK,1.6)
            pen.poly([S(x,y) for x,y in [(13,-109),(28,-117),(27,-110),(18,-107)]],EYE,None)
            pen.poly([S(x,y) for x,y in [(4,-113),(21,-129),(36,-126),(33,-119),(14,-108)]],MID,INK,1.8)
            pen.line([S(x,y) for x,y in [(10,-116),(21,-126),(33,-124)]],LIGHT,1.45)
            pen.poly([S(x,y) for x,y in [(24,-103),(40,-105),(39,-91),(26,-84),(16,-94)]],MID,None)
        pen.shape((-23,-106),((-18,-113),(-7,-114),(0,-111)),
                  ((7,-114),(18,-113),(23,-106)),((29,-96),(17,-91),(0,-92)),
                  ((-17,-91),(-29,-96),(-23,-106)),fill=DARK,w=2.1)
        for s in (-1,1):pen.oval(s*11,-101,5,3.1,INK,None)
        pen.poly([(-16,-108),(0,-110),(16,-108),(9,-104),(-9,-104)],LIGHT,None)
        pen.shape((-34,-85),((-20,-96),(-10,-91),(0,-92)),((10,-91),(20,-96),(34,-85)),
                  ((28,-77),(16,-76),(0,-77)),((-16,-76),(-28,-77),(-34,-85)),fill='#32352f',w=2.)
        for x in (-23,-9,9,23):
            w=4.8 if abs(x)>10 else 3.0
            pen.poly([(x-w,-90),(x+w,-90),(x,-79 if abs(x)>10 else -84)],CLAW,INK,.9)
        for x in (-23,23):pen.poly([(x-5,-78),(x,-87),(x+5,-78)],CLAW,INK,.9)
        pen.line([(-32,-90),(-37,-81),(-27,-74),(-12,-70),(12,-70),(27,-74),(37,-81),(32,-90)],DARK,1.6)
        pen.crack([(-19,-131),(-14,-125),(-17,-119)],1.3)
    return c.finish()


def quarter_frame():
    """Oblique, independently drawn view: the near flank recedes left.

    The muzzle projects along the head's center line; the feet are staggered
    by depth, and the far wing and limbs are occluded by the chest. No
    deformation of the profile raster is involved.
    """
    c=PartScene(); pen=Pen(c,lambda x,y:(CX+x,GROUND+y))
    with c.part('quarter_tail'):
        tail=path((-62,-66),((-89,-54),(-124,-55),(-134,-73)),
                  ((-143,-89),(-129,-101),(-117,-91)))
        pen.limb(tail,[11*(1-j/(len(tail)-1))**.8+3 for j in range(len(tail))],False,False)
        pen.crack([(-110,-61),(-107,-69),(-108,-75)],1.1)

    def leg(name,hip,knee,ankle,far,fore):
        # Each limb has its own oblique contour and separate paw. A longer
        # near-side thigh and a shorter far-side stance communicate depth.
        with c.part(name+'_leg'):
            pen.limb([hip,mix(hip,knee,.48),knee,mix(knee,ankle,.66),ankle],
                     ([19,22,15,16,11] if fore else [22,24,16,12,10])
                     if not far else ([16,18,13,14,10] if fore else [18,19,13,10,8]),far)
        with c.part(name+'_paw'):
            x,y=ankle; col=FAR if far else STONE; hi='#929589' if far else LIGHT
            # Actual toe fan in oblique projection. The toe nearest the
            # viewer is wide; the others recede along the outer edge.
            s=.85 if far else 1.
            def F(a,b):return x+s*a,y+s*b
            def S(start,*segs,**kw):pen.shape(F(*start),*((F(*a),F(*b),F(*z)) for a,b,z in segs),**kw)
            S((-16,-11),((-22,-6),(-21,4),(-15,8)),
              ((-8,13),(9,13),(18,9)),((26,6),(28,-2),(21,-7)),
              ((14,-13),(1,-15),(-8,-13)),((-12,-13),(-15,-12),(-16,-11)),fill=col)
            S((-14,-8),((-9,-12),(3,-13),(10,-10)),
              ((15,-8),(17,-5),(15,-3)),((4,-4),(-7,-2),(-14,-8)),fill=hi,edge=None)
            for a,b,w in [(-5,7,4.6),(6,6,4.1),(15,3,3.4)]:
                S((a-w,b-2),((a-w,b+1),(a-1,b+5),(a+2,b+5)),
                  ((a+w,b+4),(a+w+1,b),(a+w,b-2)),fill=CLAW,w=1.)
                pen.line([F(a-w-1,b-5),F(a-w,b-2)],DARK,1.)

    # Far-side wing is upright and narrower: halfway between the profile's
    # foreshortened silhouette and the fully spread frontal pair.
    with c.part('quarter_wing_far'):
        stone_wing(pen,(27,-111),0.,1,far=True,frontal=True,quarter=True)
    leg('quarter_hind_far',(-31,-80),(-18,-49),(-28,-31),True,False)
    leg('quarter_fore_far',(35,-93),(49,-54),(52,-29),True,True)
    with c.part('quarter_torso'):
        pen.shape((-73,-82),((-83,-103),(-64,-123),(-38,-122)),
            ((-15,-129),(8,-124),(27,-113)),((50,-105),(55,-81),(38,-61)),
            ((23,-45),(8,-42),(-13,-48)),((-35,-54),(-56,-45),(-69,-61)),
            ((-77,-68),(-77,-74),(-73,-82)),fill=STONE,w=3)
        pen.shape((-68,-87),((-61,-112),(-36,-120),(-17,-114)),
            ((1,-117),(19,-112),(30,-99)),((7,-85),(-13,-79),(-34,-83)),
            ((-51,-87),(-61,-76),(-68,-87)),fill=MID,edge=None)
        pen.poly([(-65,-95),(-53,-113),(-34,-117),(-16,-113),(-36,-105),(-48,-95)],LIGHT,None)
        pen.shape((-58,-63),((-43,-70),(-26,-60),(-9,-57)),
            ((7,-53),(23,-54),(36,-64)),((27,-48),(6,-46),(-10,-50)),
            ((-29,-56),(-47,-51),(-58,-63)),fill=DARK,edge=None)
        pen.crack([(-55,-112),(-49,-102),(-53,-96),(-44,-89)])
        pen.line([(-70,-93),(-63,-106),(-54,-110)],LIGHT,1.45)
    leg('quarter_hind_near',(-56,-75),(-42,-39),(-64,-15),False,False)
    leg('quarter_fore_near',(4,-91),(14,-47),(13,-14),False,True)
    # The shoulder is in front of the flank, then the near wing, then the
    # ruff; this keeps the root embedded in the body in every view.
    with c.part('quarter_wing_near'):
        stone_wing(pen,(-14,-94),0.,-1,frontal=True,quarter=True)
    with c.part('quarter_wing_root'):
        pen.shape((-25,-91),((-29,-99),(-21,-103),(-11,-100)),
                  ((0,-96),(1,-87),(-7,-82)),((-16,-79),(-23,-83),(-25,-91)),fill=STONE,w=1.9)
        pen.line([(-23,-92),(-17,-98),(-10,-97)],LIGHT,1.6)
        pen.line([(-7,-83),(-2,-88),(-3,-94)],DARK,1.3)
    with c.part('quarter_head'):
        # The ruff wraps the chest and terminates in carved, overlapping
        # lobes rather than a floating outline around the face.
        pen.shape((-22,-128),((-38,-125),(-44,-113),(-40,-104)),
            ((-49,-93),(-43,-77),(-32,-70)),((-26,-74),(-20,-77),(-13,-68)),
            ((-6,-62),(5,-68),(12,-70)),((25,-64),(39,-74),(46,-83)),
            ((53,-105),(45,-129),(28,-133)),((6,-142),(-12,-136),(-22,-128)),fill=DARK,w=2.7)
        # The far ear is partly hidden by the skull. The near ear has a
        # visible inner concavity and follows the receding cheek plane.
        pen.shape((30,-130),((26,-139),(32,-145),(43,-143)),
            ((54,-144),(59,-134),(53,-128)),((46,-123),(35,-124),(30,-130)),fill=FAR)
        pen.shape((35,-136),((40,-141),(48,-141),(51,-137)),
                  ((51,-132),(45,-129),(40,-131)),fill=DARK,edge=None)
        pen.line([(35,-137),(42,-141),(48,-139)],'#929589',1.1)
        pen.shape((-21,-127),((-29,-136),(-25,-146),(-13,-145)),
            ((-1,-146),(4,-138),(-1,-128)),((-7,-123),(-17,-122),(-21,-127)),fill=STONE)
        pen.shape((-21,-137),((-17,-141),(-9,-142),(-5,-137)),
                  ((-6,-132),(-13,-129),(-17,-131)),fill=DARK,edge=None)
        for pts in [[(-28,-124),(-38,-113),(-29,-104)],
                    [(-38,-105),(-42,-95),(-30,-87)],
                    [(-37,-89),(-31,-80),(-24,-75)]]:
            pen.line(pts,MID,4.4);pen.line(pts[:2],LIGHT,1.4)
        # Cranial mass, not a warped frontal mask. The near cheek has
        # width and depth, and the far cheek disappears behind the snout.
        pen.shape((-19,-122),((-7,-137),(11,-137),(27,-131)),
            ((41,-132),(54,-124),(57,-114)),((63,-107),(68,-100),(67,-90)),
            ((64,-78),(55,-71),(42,-69)),((27,-64),(5,-67),(-8,-77)),
            ((-22,-85),(-30,-99),(-27,-111)),((-26,-115),(-23,-119),(-19,-122)),fill=STONE,w=3)
        pen.shape((-21,-118),((-9,-130),(5,-134),(22,-128)),
            ((14,-126),(2,-123),(-9,-117)),((-15,-114),(-20,-114),(-21,-118)),fill=LIGHT,edge=None)
        pen.shape((-22,-105),((-15,-107),(-8,-102),(1,-101)),
            ((8,-98),(9,-90),(3,-84)),((-2,-80),(-10,-83),(-17,-90)),
            ((-21,-95),(-23,-100),(-22,-105)),fill=MID,edge=None)
        pen.poly([(39,-123),(49,-119),(54,-113),(49,-108),(37,-115)],MID,None)
        pen.line([(-24,-111),(-23,-102),(-17,-97)],LIGHT,1.4)
        pen.line([(-19,-91),(-12,-83),(-5,-80)],LIGHT,1.35)
        pen.crack([(-6,-130),(-1,-124),(-4,-119)],1.2)
        pen.crack([(-12,-100),(-17,-94),(-13,-89)],1.1)
    with c.part('quarter_eyes_and_nose'):
        # A continuous brow ridge with two different projected sockets.
        # The central crease falls on the bridge of the projected nose.
        pen.poly([(-7,-117),(21,-111),(20,-102),(6,-102),(-5,-107)],'#45473f',INK,1.7)
        pen.poly([(35,-111),(49,-120),(53,-112),(47,-105),(39,-104)],'#45473f',INK,1.5)
        pen.poly([(-1,-113),(17,-110),(16,-105),(6,-106)],EYE,None)
        pen.poly([(40,-111),(48,-116),(48,-110),(43,-107)],EYE,None)
        pen.shape((-15,-125),((-7,-130),(4,-129),(15,-121)),
            ((21,-117),(25,-115),(28,-111)),((25,-107),(21,-106),(17,-108)),
            ((5,-114),(-4,-116),(-13,-117)),((-17,-119),(-17,-122),(-15,-125)),fill=MID,w=1.8)
        pen.poly([(32,-114),(41,-126),(51,-124),(53,-119),(47,-115),(38,-109)],MID,INK,1.6)
        pen.line([(-12,-124),(-3,-126),(7,-123),(19,-115)],LIGHT,1.45)
        pen.line([(36,-117),(43,-123),(50,-121)],LIGHT,1.15)
        # Bridge and cheek-to-muzzle planes: a short broad stone snout,
        # with the far nostril receding, rather than a flat oval nose.
        pen.shape((20,-108),((27,-114),(34,-113),(39,-109)),
            ((49,-111),(58,-108),(61,-101)),((64,-95),(57,-91),(48,-91)),
            ((38,-92),(27,-90),(21,-94)),((17,-99),(17,-104),(20,-108)),fill=DARK,w=2.1)
        pen.oval(29,-101,5.0,3.3,INK,None)
        pen.oval(52,-102,3.7,2.6,INK,None)
        pen.poly([(23,-108),(33,-111),(47,-108),(48,-105),(32,-105)],LIGHT,None)
        pen.line([(14,-105),(18,-109),(22,-110)],LIGHT,1.0)
    with c.part('quarter_jaw'):
        # The mouth's near corner sits farther back; its far corner curls
        # around the muzzle. Individual teeth follow the curved gum line.
        pen.shape((5,-88),((13,-98),(26,-96),(38,-95)),
            ((48,-95),(59,-98),(62,-91)),((64,-85),(55,-79),(45,-80)),
            ((35,-79),(21,-76),(11,-81)),((6,-82),(4,-85),(5,-88)),fill='#32352f',w=2.1)
        for x,y,w,h in [(14,-94,4.9,11),(26,-95,3.1,7),(38,-95,3.0,6),(51,-95,3.6,9)]:
            pen.poly([(x-w,y),(x+w,y),(x+1,y+h)],CLAW,INK,.9)
        for x,y,w,h in [(15,-80,4.3,10),(47,-81,3.6,9)]:
            pen.poly([(x-w,y),(x,y-h),(x+w,y)],CLAW,INK,.9)
        pen.line([(4,-96),(0,-89),(4,-81),(13,-76),(27,-72),(44,-73),(57,-79)],DARK,1.7)
        pen.line([(8,-79),(18,-75),(31,-73),(45,-74)],LIGHT,1.4)
    return c.finish()


def _render_frame(anim,i,n):
    if anim=='turnaround':
        assert n==5
        if i==2:return front_frame()
        im=quarter_frame() if i in (1,3) else side_frame('idle',0,ROWS[0][1])
        return rigdoc.mirrored_canvas(im) if i<2 else im
    return side_frame(anim,i,n)


def render(out_dir: str | Path, **opts):
    out_dir=Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    transform={}
    out=build_sheet(parts=True, frame_transform_out=transform, target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,
                    out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,
                    actor_metadata=ACTOR_METADATA,
                    body_metrics_fn=lambda w,h:body_metrics_for_box(BODY_BOX,w,h),
                    animation_key_map={name:name for name,_,_ in ROWS},
                    pose_bodies='authored',sits_on_ground=True)
    parts=publish_rig_flipbook(TARGET_NAME,ROWS,_render_frame,out,transform,Path(out_dir))
    return [out[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent') if out.get(k)] + list(parts.values())
